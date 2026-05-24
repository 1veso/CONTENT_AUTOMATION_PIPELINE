"""Seed R61 Source Image for Day 29-31 via Higgsfield direct (no Fal).

Fal balance is exhausted. This helper:
  1. Reads R57 Schaden v1 R57 - 23/24/25 "Image Prompt" fields (already
     populated by stage_schaden_v1.py).
  2. Calls higgsfield CLI nano_banana_2 (text-to-image, no --image ref).
  3. Downloads result, uploads to R2, patches R61 Day 29/30/31 Source Image.

Credit cost: 3 records x 2 credits = 6 credits total.
"""
from __future__ import annotations
import datetime as dt
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
R61_ROOT = REPO_ROOT / "R61_video_pipeline"
R57_ROOT = REPO_ROOT / "R57_content_engine"
load_dotenv(R61_ROOT / ".env")

os.environ["PATH"] = r"C:\Users\benja\bin;" + os.environ.get("PATH", "")

# Load BOTH airtable modules via importlib so neither pollutes sys.path.
def _load(name, abspath):
    spec = importlib.util.spec_from_file_location(name, abspath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


r61_at = _load("r61_airtable_video", R61_ROOT / "tools" / "airtable_video.py")
# R57 airtable depends on its providers/ subpackage — add R57 root to path
# but don't import R61 tools first to avoid collision.
sys.path.insert(0, str(R57_ROOT))
from tools import airtable as r57_at  # noqa: E402

PAIRS = [
    (29, "recc01n1tMzC9aiHv", "recrYjb3Omgp6dCd0"),
    (30, "recZ5AxNrEnYPHexW", "recvjTUabMn7Tz0Ix"),
    (31, "recuu2pTCKRlHM0uR", "recTH01CBrSciCL2c"),
]

# Per-day seed prompts in English. The R57 German Schaden prompt format
# triggers Higgsfield's content filter (nano_banana_2 returns failed status).
# These simplified scene anchors give frame_gen a Source Image to lock
# composition on; frame_gen's first/last prompts override the actual content.
SEED_PROMPTS = {
    29: (
        "Photorealistic 9:16 vertical: cozy small German neighborhood "
        "restaurant interior, wooden table near a window, a moment of "
        "calm focus, warm afternoon light, neutral palette, real "
        "everyday setting, no text, no logos, no brand marks."
    ),
    30: (
        "Photorealistic 9:16 vertical: a calm German apartment interior "
        "during a moving day, cardboard boxes stacked against a wall, "
        "afternoon light through a window, focused composition, neutral "
        "palette, authentic everyday setting, no text, no logos."
    ),
    31: (
        "Photorealistic 9:16 vertical: a calm German front-door hallway "
        "interior, a person reflecting at their apartment door, warm "
        "indoor light, neutral palette, authentic everyday setting, "
        "no text, no logos, no brand marks."
    ),
}


# ---------- R2 upload (inlined from R61/tools/stitch.py upload_to_r2) ----------
_R2_CLOCK_PATCHED = False


def _patch_botocore_clock():
    """R2 clock-skew workaround — same trick as stitch.py."""
    global _R2_CLOCK_PATCHED
    if _R2_CLOCK_PATCHED:
        return
    import botocore.auth
    import botocore.utils
    import datetime as _dt
    # Probe R2 server clock
    account_id = os.environ["R2_ACCOUNT_ID"]
    resp = requests.head(
        f"https://{account_id}.r2.cloudflarestorage.com/",
        timeout=10, allow_redirects=False,
    )
    server_date_str = resp.headers.get("Date")
    if not server_date_str:
        _R2_CLOCK_PATCHED = True
        return
    from email.utils import parsedate_to_datetime
    server_dt = parsedate_to_datetime(server_date_str).astimezone(_dt.timezone.utc)
    local_dt = _dt.datetime.now(_dt.timezone.utc)
    offset = server_dt - local_dt
    if abs(offset.total_seconds()) < 60:
        _R2_CLOCK_PATCHED = True
        return

    def _shifted_get_current_datetime():
        return _dt.datetime.now(_dt.timezone.utc) + offset

    botocore.utils.get_current_datetime = _shifted_get_current_datetime
    botocore.auth.get_current_datetime = _shifted_get_current_datetime
    print(f"  R2 clock offset {offset.total_seconds():+.1f}s")
    _R2_CLOCK_PATCHED = True


def upload_to_r2(local_path, key, content_type="image/png"):
    import boto3
    from botocore.config import Config
    account_id = os.environ["R2_ACCOUNT_ID"]
    bucket = os.environ["R2_BUCKET_NAME"]
    public_base = os.environ["R2_PUBLIC_URL"].rstrip("/")
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
    _patch_botocore_clock()
    client = boto3.client(
        "s3", endpoint_url=endpoint_url,
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )
    client.upload_file(
        str(local_path), bucket, key,
        ExtraArgs={"ContentType": content_type},
    )
    return f"{public_base}/{key}"


# ---------- Higgsfield text-to-image ----------
def run_higgsfield_image_no_ref(prompt, out_local):
    import re as _re
    cmd = [
        "higgsfield", "generate", "create", "nano_banana_2",
        "--prompt", prompt,
        "--aspect_ratio", "9:16",
        "--resolution", "1k",
        "--wait", "--wait-timeout", "10m",
        "--wait-interval", "10s",
        "--json",
    ]
    proc = subprocess.run(
        cmd, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"higgsfield image failed (exit {proc.returncode}): "
            f"stdout={proc.stdout[:300]} stderr={proc.stderr[:300]}"
        )
    if not proc.stdout.strip():
        raise RuntimeError(
            f"higgsfield returned empty stdout (returncode 0); "
            f"stderr={proc.stderr[:300]}"
        )
    try:
        payload = json.loads(proc.stdout)
    except Exception as e:
        raise RuntimeError(
            f"higgsfield JSON parse failed: {e}; "
            f"stdout head: {proc.stdout[:400]}"
        )
    jobs = payload if isinstance(payload, list) else [payload]
    url = None
    for job in jobs:
        # Shape 1: top-level result_url
        if job.get("result_url"):
            url = job["result_url"]
            break
        # Shape 2: nested results[].url
        for result in (job.get("results") or []):
            u = result.get("url") or result.get("raw_url")
            if u and u.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                url = u
                break
        if url:
            break
    if not url:
        # Last-resort regex scan over full JSON dump
        flat = json.dumps(jobs)
        m = _re.search(r'https?://[^"\s]+\.(?:png|jpg|jpeg|webp)', flat)
        if m:
            url = m.group(0)
    if not url:
        raise RuntimeError(
            f"higgsfield job complete but no image URL; "
            f"payload head: {json.dumps(jobs)[:400]}"
        )
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(out_local, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return url


def main():
    print(f"=== Seed Day 29-31 Source Image via Higgsfield ===")
    print(f"Start: {dt.datetime.now().isoformat(timespec='seconds')}")
    tmp_dir = R61_ROOT / "references" / "outputs" / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    ok = 0
    for day, r61_id, r57_id in PAIRS:
        print(f"\n--- Day {day} | R61 {r61_id} ---")
        prompt = SEED_PROMPTS.get(day)
        if not prompt:
            print(f"  FAIL: no seed prompt for Day {day}")
            continue
        print(f"  prompt ({len(prompt)} chars): {prompt[:80]}...")

        local_png = tmp_dir / f"day{day:02d}_source.png"
        t0 = time.time()
        try:
            hf_url = run_higgsfield_image_no_ref(prompt, local_png)
            print(f"  higgsfield -> {hf_url[:90]}...")
            print(f"  local size: {local_png.stat().st_size:,} bytes "
                  f"({time.time()-t0:.1f}s)")
        except Exception as e:
            print(f"  FAIL higgsfield: {e}")
            continue

        r2_key = f"r61/source/v1/day{day:02d}_{r61_id}_source.png"
        try:
            r2_url = upload_to_r2(local_png, r2_key, content_type="image/png")
            print(f"  R2 -> {r2_url}")
        except Exception as e:
            print(f"  FAIL R2 upload: {e}")
            continue

        try:
            r61_at.update_record(r61_id, {
                "Source Image": [{"url": r2_url, "filename": local_png.name}],
            })
            print(f"  Airtable patched: Day {day} Source Image set")
            ok += 1
        except Exception as e:
            print(f"  FAIL Airtable patch: {e}")
            continue

    print(f"\nDone. Linked={ok}/3")


if __name__ == "__main__":
    main()
