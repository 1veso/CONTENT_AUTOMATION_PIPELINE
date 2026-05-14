"""
R51 ingest — pull a source video from a social URL into the cloner pipeline.

Strategy:
  1. Detect platform from URL (TikTok, Instagram, YouTube, Facebook/Meta).
  2. Try `yt-dlp` first (handles 90% of cases via direct CDN scraping).
  3. Fall back to camofox REST (http://localhost:9377) when yt-dlp fails —
     usually because the post is geo-walled, login-walled, or behind anti-bot.
  4. Upload the resulting MP4 to Cloudflare R2 under
     `r51/inputs/{timestamp}_{platform}_{id}.mp4`.
  5. Write the R2 URL + platform + source URL into Airtable
     `R51_Creative_Cloner` table, Status = "Create".
  6. Return the R2 URL.

This module is intentionally callable both as a CLI tool and as a library
function. The webhook handler at `webhook_handler.py` imports `ingest_url`
directly.

Usage (CLI):
    python -m tools.ingest --url "https://tiktok.com/..."
    python -m tools.ingest --url "..." --project-name "Q3 ad clone" --brand "Provinzial"
"""

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    # Fall back to the R61 .env which already holds R2 + Airtable creds.
    R61_ENV = PROJECT_ROOT.parent / "R61_video_pipeline" / ".env"
    if R61_ENV.exists():
        load_dotenv(R61_ENV)

CAMOFOX_BASE = os.environ.get("CAMOFOX_BASE", "http://localhost:9377")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_R51_TABLE = os.environ.get("AIRTABLE_R51_TABLE", "R51_Creative_Cloner")


def _ts():
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def detect_platform(url):
    """Map a URL host to a short platform tag."""
    host = (urlparse(url).hostname or "").lower()
    if "tiktok" in host:
        return "tiktok"
    if "instagram" in host:
        return "instagram"
    if "youtube" in host or "youtu.be" in host:
        return "youtube"
    if "facebook" in host or "fb.watch" in host or "fb.com" in host:
        return "facebook"
    if "twitter" in host or "x.com" in host:
        return "x"
    return "unknown"


def _id_from_url(url, platform):
    """Heuristic id extraction for filename hygiene; falls back to timestamp."""
    parts = [p for p in urlparse(url).path.split("/") if p]
    for p in reversed(parts):
        if re.fullmatch(r"[A-Za-z0-9_\-]{6,}", p):
            return p
    return _ts()


def _try_ytdlp(url, out_dir):
    """Run yt-dlp and return the produced mp4 path, or None on failure."""
    if shutil.which("yt-dlp") is None:
        return None
    out_template = str(out_dir / "r51_%(id)s.%(ext)s")
    argv = [
        "yt-dlp",
        "-o", out_template,
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--quiet",
        "--no-warnings",
        url,
    ]
    proc = subprocess.run(argv, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return None
    # Find the produced mp4 (most-recently-modified file in out_dir).
    mp4s = sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime,
                  reverse=True)
    return mp4s[0] if mp4s else None


def _try_camofox(url, out_dir):
    """Fallback ingest via local camofox REST. Returns mp4 path or None."""
    endpoint = f"{CAMOFOX_BASE.rstrip('/')}/ingest"
    try:
        resp = requests.post(endpoint, json={"url": url}, timeout=300)
    except requests.RequestException as e:
        print(f"  camofox unreachable at {endpoint}: {e}", file=sys.stderr)
        return None
    if resp.status_code != 200:
        print(f"  camofox returned {resp.status_code}: {resp.text[:200]}",
              file=sys.stderr)
        return None
    body = resp.json()
    media_url = body.get("media_url") or body.get("url")
    if not media_url:
        return None
    dest = out_dir / f"r51_camofox_{_ts()}.mp4"
    with requests.get(media_url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    return dest


_R2_CLOCK_PATCHED = False


def _patch_botocore_clock(endpoint_url):
    """Same SigV4 clock-skew workaround used in R61/tools/stitch.py."""
    global _R2_CLOCK_PATCHED
    if _R2_CLOCK_PATCHED:
        return
    import datetime as _dt
    from email.utils import parsedate_to_datetime
    import botocore.auth
    import botocore.utils

    try:
        head = requests.head(endpoint_url, timeout=10, allow_redirects=True)
        server_dt = parsedate_to_datetime(head.headers["Date"]).astimezone(
            _dt.timezone.utc
        ).replace(tzinfo=None)
    except Exception:
        _R2_CLOCK_PATCHED = True
        return

    local_dt = _dt.datetime.utcnow()
    offset = server_dt - local_dt
    if abs(offset.total_seconds()) < 60:
        _R2_CLOCK_PATCHED = True
        return

    def _shifted(remove_tzinfo=True):
        d = _dt.datetime.now(_dt.timezone.utc) + offset
        if remove_tzinfo:
            d = d.replace(tzinfo=None)
        return d

    botocore.utils.get_current_datetime = _shifted
    botocore.auth.get_current_datetime = _shifted
    _R2_CLOCK_PATCHED = True


def upload_to_r2(local_path, key, content_type="video/mp4"):
    """Push local mp4 to R2 and return its public URL."""
    import boto3
    from botocore.config import Config

    account_id = os.environ["R2_ACCOUNT_ID"]
    access_key = os.environ["R2_ACCESS_KEY_ID"]
    secret_key = os.environ["R2_SECRET_ACCESS_KEY"]
    bucket = os.environ["R2_BUCKET_NAME"]
    public_base = os.environ["R2_PUBLIC_URL"].rstrip("/")
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    _patch_botocore_clock(endpoint_url)

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )
    client.upload_file(
        str(local_path), bucket, key,
        ExtraArgs={"ContentType": content_type},
    )
    return f"{public_base}/{key}"


def write_airtable_row(r2_url, source_url, platform, project_name=None,
                       brand=None):
    """Create one row in the R51 Airtable table. Returns the new record id."""
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        print("  Airtable env not set — skipping table write", file=sys.stderr)
        return None
    url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/"
        f"{requests.utils.quote(AIRTABLE_R51_TABLE, safe='')}"
    )
    fields = {
        "INPUT_Video": [{"url": r2_url}],
        "Source URL": source_url,
        "Platform": platform,
        "Status": "Create",
    }
    if project_name:
        fields["Project"] = project_name
    if brand:
        fields["Brand"] = brand
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"fields": fields, "typecast": True},
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        print(f"  Airtable write failed ({resp.status_code}): "
              f"{resp.text[:300]}", file=sys.stderr)
        return None
    return resp.json().get("id")


def ingest_url(url, project_name=None, brand=None):
    """End-to-end: download → upload → Airtable. Returns dict with r2_url + id."""
    platform = detect_platform(url)
    vid_id = _id_from_url(url, platform)
    with tempfile.TemporaryDirectory(prefix="r51_ingest_") as tmp:
        out_dir = Path(tmp)
        mp4 = _try_ytdlp(url, out_dir)
        used = "yt-dlp"
        if mp4 is None or not mp4.exists():
            print(f"  yt-dlp failed → falling back to camofox", file=sys.stderr)
            mp4 = _try_camofox(url, out_dir)
            used = "camofox"
        if mp4 is None or not mp4.exists():
            raise RuntimeError(
                f"Both yt-dlp and camofox failed to ingest {url}"
            )
        r2_key = f"r51/inputs/{_ts()}_{platform}_{vid_id}.mp4"
        r2_url = upload_to_r2(mp4, r2_key)
    record_id = write_airtable_row(r2_url, url, platform,
                                   project_name=project_name, brand=brand)
    return {
        "status": "ok",
        "platform": platform,
        "source_url": url,
        "r2_url": r2_url,
        "airtable_record_id": record_id,
        "ingester": used,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="R51 source ingest (URL → R2 + Airtable)")
    p.add_argument("--url", required=True)
    p.add_argument("--project-name", default=None)
    p.add_argument("--brand", default=None)
    args = p.parse_args(argv)
    result = ingest_url(args.url, project_name=args.project_name,
                        brand=args.brand)
    print(result)


if __name__ == "__main__":
    main()
