"""
R61 Step 2 — Video clip generation via Higgsfield.

Reads Airtable Video records where Video Status = "Frames Generated",
downloads First Frame Image and Last Frame Image to references/outputs/tmp/,
calls Higgsfield (Kling 3.0 — accepts start_image + end_image) to interpolate
between the two stills, downloads the resulting MP4, re-hosts it on Fal
storage, attaches the URL to the Airtable "Video Clip" field, and advances
Video Status to "Clip Generated".

Model choice: kling3_0. The model catalog lists Kling 3.0 as the natural pick
for single-plane, motion-not-flashy scenes that interpolate between an explicit
first and last frame — exactly the brand brief from references/docs/
provinzial_BRAND.md (warm, grounded, authentic, no flashy effects). Seedance
2.0 is overkill cinema-grade and ~3x cost; reach for it only if Kling 3.0
output drifts on a real run.

Hard cost-approval gate (per .claude/skills/cinematic-ads/SKILL.md Gate 1):
re-quote on every run and wait for an explicit fire word before any paid call.

Usage:
    python -m tools.video_gen --dry-run          # read-only verification
    python -m tools.video_gen                    # interactive paid run
    python -m tools.video_gen --limit 3          # cap records this run
"""

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
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
load_dotenv(ENV_PATH)

if os.getenv("FAL_KEY") is None and os.getenv("FAL_API_KEY"):
    os.environ["FAL_KEY"] = os.environ["FAL_API_KEY"]

from tools import airtable_video as av  # noqa: E402
from tools import _gates  # noqa: E402

LOG_PATH = PROJECT_ROOT / "references" / "outputs" / "video_gen_run.log"
TMP_DIR = PROJECT_ROOT / "references" / "outputs" / "tmp"

# Higgsfield model + settings (brand-aligned: 9:16, short cinematic motion).
HIGGSFIELD_MODEL = "kling3_0"
DEFAULT_DURATION_S = 5    # 4-6s per task spec; 5s sits in the middle.
ASPECT_RATIO = "9:16"
WAIT_TIMEOUT = "20m"      # CLI default is 10m; bump for slow renders.

# Higgsfield bills via subscription credits (no USD/call). Per
# `higgsfield generate cost kling3_0 --prompt test --aspect_ratio 9:16
# --duration N`: 3s=6 credits, 5s=10 credits, scales with duration.
CREDITS_BY_DURATION = {3: 6, 5: 10, 10: 20}
DEFAULT_COST_PER_CLIP_CREDITS = 10

FIRE_WORDS = {"go", "fire", "yes", "run it", "run", "ship"}

# Table-shape config. Lets the same tool drive both the Video table (R61
# main pipeline, prompt built from Ad Name/Caption/pillar) and the IO table
# (intro/outro brand-mark animations, prompt taken from the IO Prompt field).
TABLE_CONFIG = {
    "Video": {
        "table_name": av.TABLE_NAME,
        "status_field": av.STATUS_FIELD,
        "frames_generated": av.STATUS_FRAMES_GENERATED,
        "clip_generated": av.STATUS_CLIP_GENERATED,
        "first_frame_field": "First Frame Image",
        "last_frame_field": "Last Frame Image",
        "clip_field": "Video Clip",
        "name_field": "Ad Name",
    },
    "IO": {
        "table_name": "IO",
        "status_field": "Status",
        "frames_generated": "Frames Generated",
        "clip_generated": "Clip Generated",
        "first_frame_field": "First Frame",
        "last_frame_field": "Last Frame",
        "clip_field": "Video Clip",
        "name_field": "Type",
    },
}

LIFESTYLE_PILLARS = {
    "Sicherheit im Alltag",
    "Vorsorge & Zukunft",
    "Regional & Gemeinschaft",
}
ACTION_PILLARS = {
    "Schaden & Service",
    "Produktaufklärung",
}

BRAND_MOTION_ANCHOR = (
    "Provinzial brand video: warm, authentic German everyday life. Calm "
    "cinematic motion only — soft real-world movement, never flashy, never "
    "snappy zooms, never whip pans, never dramatic VFX. Color stays anchored "
    "on Provinzial green #005940 and Flügelgelb #FFD000, warm natural "
    "lighting. The single beat between the first and last frame plays out "
    "naturally and grounded, like a real moment captured on a 35mm lens. "
    "No on-image text, no logos other than the small yellow wings watermark "
    "bottom-right (which stays static)."
)


def log(msg):
    ts = dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def detect_pillar(ad_name):
    m = re.search(r"\[([^\]]+)\]\s*$", ad_name or "")
    return m.group(1).strip() if m else None


def pillar_kind(pillar):
    if pillar in ACTION_PILLARS:
        return "action"
    return "lifestyle"


def build_io_motion_prompt(record):
    """Motion prompt for IO brand-mark animations. Anchored on the record's
    Prompt field plus a 'wings emerge / fade in' interpolation directive."""
    fields = record.get("fields", {})
    base = (fields.get("Prompt") or "").strip()
    io_type = (fields.get("Type") or "").strip().lower()
    if io_type == "intro":
        emerge = (
            "Animate the golden wings logo #FFD000 emerging slowly from "
            "the dark central area into full visibility, centered, "
            "warm cinematic light deepening on the Provinzial green "
            "#005940 background. Calm, professional, no people, no text, "
            "no flashy motion — a graceful slow reveal."
        )
    elif io_type == "outro":
        emerge = (
            "Animate the golden wings logo #FFD000 fading into full "
            "visibility, centered on the pure white background. Soft, "
            "clean, minimal motion. No people, no text, no flashy "
            "effects — a calm closing brand mark."
        )
    else:
        emerge = (
            "Animate a calm transition from the first frame to the last "
            "frame. No flashy effects."
        )
    return f"{base} {emerge}".strip()


def build_motion_prompt(record):
    """One-paragraph cinematic motion prompt grounded in the brand brief."""
    fields = record.get("fields", {})
    ad_name = (fields.get("Ad Name") or "Provinzial moment").strip()
    caption = (fields.get("Caption") or "").strip()
    pillar = detect_pillar(ad_name)
    kind = pillar_kind(pillar)

    if kind == "lifestyle":
        beat_clause = (
            "The motion is a single warm human beat — a laugh breaking, a "
            "hand reaching, a head turning toward a loved one, or whatever "
            "natural transition fits between the two frames. Gentle, real, "
            "earned. No jump cuts, no sudden camera moves."
        )
    else:
        beat_clause = (
            "The motion is a single resolution beat — a phone reaching the "
            "ear, a signature completing, a handshake closing, a clipboard "
            "being handed across, or whatever calm action fits between the "
            "two frames. Trustworthy and grounded, never theatrical."
        )

    caption_line = f"Caption context: {caption}. " if caption else ""

    return (
        f"Animate from the start frame to the end frame for the Provinzial "
        f"ad '{ad_name}'. {beat_clause} Maintain identical framing, "
        f"composition, subject count, wardrobe, and background across both "
        f"frames — only the single beat changes. {caption_line}"
        f"Pillar: {pillar or 'general'}. {BRAND_MOTION_ANCHOR}"
    ).strip()


def attachment_url(record, field_name):
    atts = record.get("fields", {}).get(field_name) or []
    if not atts:
        return None
    return atts[0].get("url")


def download_attachment(url, dest_path):
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return dest_path


def ext_from_url(url, default=".png"):
    suffix = Path(urlparse(url).path).suffix
    return suffix if suffix else default


def upload_to_fal(local_path):
    import fal_client
    return fal_client.upload_file(str(local_path))


def higgsfield_available():
    return shutil.which("higgsfield") is not None


def run_higgsfield(prompt, start_image_path, end_image_path, duration_s=DEFAULT_DURATION_S):
    """Submit a Kling 3.0 job via the higgsfield CLI and return the video URL.

    Uses `--wait --json` so the call blocks until terminal status and returns
    the final job object. Raises RuntimeError on non-zero exit or missing URL.
    """
    cmd = [
        "higgsfield", "generate", "create", HIGGSFIELD_MODEL,
        "--prompt", prompt,
        "--start-image", str(start_image_path),
        "--end-image", str(end_image_path),
        "--aspect_ratio", ASPECT_RATIO,
        "--duration", str(duration_s),
        "--mode", os.environ.get("HF_MODE", "std"),
        "--wait",
        "--wait-timeout", WAIT_TIMEOUT,
        "--json",
    ]
    log(f"  $ higgsfield generate create {HIGGSFIELD_MODEL} "
        f"--aspect_ratio {ASPECT_RATIO} --duration {duration_s} "
        f"--start-image <first> --end-image <last>")
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"higgsfield CLI failed (exit {proc.returncode}): "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"higgsfield JSON parse failed: {e}; "
                           f"stdout head: {proc.stdout[:400]}")

    # Walk the payload — CLI returns either a job object or a list of jobs.
    jobs = payload if isinstance(payload, list) else [payload]
    for job in jobs:
        for result in (job.get("results") or []):
            url = result.get("url") or result.get("raw_url")
            if url and url.lower().endswith((".mp4", ".mov", ".webm")):
                return url
        # Fallback: scan all string values for the first .mp4
        flat = json.dumps(job)
        m = re.search(r'https?://[^"\s]+\.mp4', flat)
        if m:
            return m.group(0)
    raise RuntimeError("higgsfield job completed but no video URL found in "
                       "result payload")


def get_balance_credits():
    """Best-effort: read Higgsfield credit balance via the CLI. None on error."""
    try:
        proc = subprocess.run(
            ["higgsfield", "account", "status", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=20,
        )
        if proc.returncode != 0:
            return None
        data = json.loads(proc.stdout)
        for key in ("credits", "balance", "available_credits"):
            if key in data:
                return data[key]
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return None
    return None


def confirm_cost(num_records, duration_s=DEFAULT_DURATION_S):
    cost_per_clip = CREDITS_BY_DURATION.get(duration_s, DEFAULT_COST_PER_CLIP_CREDITS)
    total_credits = num_records * cost_per_clip
    balance = get_balance_credits()
    print()
    print("=" * 60)
    print("COST ESTIMATE")
    print("=" * 60)
    print(f"  Records to process : {num_records}")
    print(f"  Model              : Higgsfield {HIGGSFIELD_MODEL}")
    print(f"  Aspect / duration  : {ASPECT_RATIO} / {duration_s}s")
    print(f"  Credits per clip   : {cost_per_clip} "
          f"(from `higgsfield generate cost`)")
    print(f"  TOTAL              : {total_credits} credits")
    if balance is not None:
        print(f"  Account balance    : {balance} credits "
              f"({balance - total_credits} after this run)")
    print("=" * 60)
    print(f"Type one of: {sorted(FIRE_WORDS)} to proceed, anything else aborts.")
    answer = input("> ").strip().lower()
    return answer in FIRE_WORDS


def _airtable_record(table_cfg, record_id):
    """Fetch a record by id from the configured table."""
    from urllib.parse import quote
    url = f"{av.AIRTABLE_API_URL}/{av.AIRTABLE_BASE_ID}/{quote(table_cfg['table_name'], safe='')}/{record_id}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {av.AIRTABLE_API_KEY}"}, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Airtable get failed: {resp.text}")
    return resp.json()


def _airtable_query(table_cfg, filter_formula):
    """Return all matching records from the configured table."""
    from urllib.parse import quote
    url = f"{av.AIRTABLE_API_URL}/{av.AIRTABLE_BASE_ID}/{quote(table_cfg['table_name'], safe='')}"
    params = {"filterByFormula": filter_formula}
    all_records = []
    offset = None
    while True:
        if offset:
            params["offset"] = offset
        resp = requests.get(url, headers={"Authorization": f"Bearer {av.AIRTABLE_API_KEY}"}, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Airtable query failed: {resp.text}")
        data = resp.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return all_records


def _airtable_update(table_cfg, record_id, fields):
    from urllib.parse import quote
    url = f"{av.AIRTABLE_API_URL}/{av.AIRTABLE_BASE_ID}/{quote(table_cfg['table_name'], safe='')}/{record_id}"
    resp = requests.patch(
        url,
        headers={"Authorization": f"Bearer {av.AIRTABLE_API_KEY}", "Content-Type": "application/json"},
        json={"fields": fields},
        timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Airtable update failed: {resp.text}")
    return resp.json()


def process_record(record, table_cfg, output_path=None, duration_s=DEFAULT_DURATION_S):
    rec_id = record["id"]
    fields = record.get("fields", {})
    label = fields.get(table_cfg["name_field"]) or "(no name)"

    first_url = attachment_url(record, table_cfg["first_frame_field"])
    last_url = attachment_url(record, table_cfg["last_frame_field"])
    if not first_url or not last_url:
        log(f"SKIP {rec_id} ({label}): missing first/last frame attachment")
        return "skipped_no_frames"

    if table_cfg["table_name"] == "IO":
        prompt = build_io_motion_prompt(record)
    else:
        prompt = build_motion_prompt(record)

    log(f"START {rec_id} ({label}) table={table_cfg['table_name']}")

    first_local = TMP_DIR / f"{rec_id}_first{ext_from_url(first_url)}"
    last_local = TMP_DIR / f"{rec_id}_last{ext_from_url(last_url)}"
    download_attachment(first_url, first_local)
    download_attachment(last_url, last_local)
    log(f"  downloaded frames -> {first_local.name}, {last_local.name}")

    video_url = run_higgsfield(prompt, first_local, last_local, duration_s=duration_s)
    log(f"  higgsfield returned {video_url}")

    # Re-host on Fal storage so Airtable has a stable CDN.
    clip_local = TMP_DIR / f"{rec_id}_clip.mp4"
    download_attachment(video_url, clip_local)
    fal_url = upload_to_fal(clip_local)
    log(f"  re-hosted on Fal -> {fal_url}")

    # If --output requested, copy the local clip to that path before cleanup.
    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(clip_local, out)
        log(f"  saved local copy -> {out}")

    _airtable_update(
        table_cfg, rec_id,
        {
            table_cfg["clip_field"]: [{"url": fal_url, "filename": f"{rec_id}_clip.mp4"}],
            table_cfg["status_field"]: table_cfg["clip_generated"],
        },
    )
    log(f"DONE  {rec_id} ({label}) status -> {table_cfg['clip_generated']}")

    # Tidy temp artifacts on success.
    for p in (first_local, last_local, clip_local):
        try:
            p.unlink()
        except OSError:
            pass
    return "ok"


def dry_run_report(records, table_cfg):
    print()
    print(f"DRY RUN — base {av.AIRTABLE_BASE_ID}, table '{table_cfg['table_name']}'")
    print(f"Records ready for clip generation: {len(records)}")
    if not records:
        print("  (no rows ready)")
    for r in records:
        f = r.get("fields", {})
        first = attachment_url(r, table_cfg["first_frame_field"]) or "<missing>"
        last = attachment_url(r, table_cfg["last_frame_field"]) or "<missing>"
        if table_cfg["table_name"] == "IO":
            prompt = build_io_motion_prompt(r)
            print(f"  - {r['id']}  Type={f.get('Type')!r}  Index={f.get('Index')!r}")
        else:
            prompt = build_motion_prompt(r)
            pillar = detect_pillar(f.get("Ad Name") or "")
            print(f"  - {r['id']}  Index={f.get('Index')!r}  "
                  f"Ad Name={f.get('Ad Name')!r}")
            print(f"      Pillar: {pillar!r} -> {pillar_kind(pillar)}")
        print(f"      First Frame: {first[:80]}{'...' if len(first) > 80 else ''}")
        print(f"      Last Frame : {last[:80]}{'...' if len(last) > 80 else ''}")
        print(f"      Motion prompt ({len(prompt)} chars): {prompt[:160]}...")
    total_credits = len(records) * DEFAULT_COST_PER_CLIP_CREDITS
    print(f"Would call Higgsfield {HIGGSFIELD_MODEL} for {len(records)} clip(s) "
          f"@ {ASPECT_RATIO} / {DEFAULT_DURATION_S}s "
          f"({total_credits} credits at {DEFAULT_COST_PER_CLIP_CREDITS}/clip — "
          f"override with --duration).")
    print(f"higgsfield CLI on PATH: {higgsfield_available()}")
    print("No API calls were made.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="R61 Step 2 — Higgsfield clip generation")
    parser.add_argument("--dry-run", action="store_true",
                        help="Read Airtable and show what would happen; no calls.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N records this run.")
    parser.add_argument("--record-id", default=None,
                        help="Force-process this single Airtable record id, "
                             "bypassing the Video Status filter.")
    parser.add_argument("--confirm", default=None,
                        help="Pass a fire word (e.g. --confirm go) to bypass "
                             "the interactive cost prompt. Required for "
                             "non-interactive / background runs since stdin "
                             "pipes are unreliable on Windows.")
    parser.add_argument("--table", default="Video", choices=list(TABLE_CONFIG.keys()),
                        help="Which Airtable table to operate on (default Video).")
    parser.add_argument("--output", default=None,
                        help="Optional local path to save the generated MP4 "
                             "(in addition to the Airtable attachment).")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION_S,
                        choices=sorted(CREDITS_BY_DURATION.keys()),
                        help=f"Clip duration in seconds "
                             f"(default {DEFAULT_DURATION_S}s, "
                             f"choices: {sorted(CREDITS_BY_DURATION.keys())}).")
    args = parser.parse_args(argv)

    table_cfg = TABLE_CONFIG[args.table]

    missing = av.check_credentials()
    if missing:
        print(f"Missing env vars in {ENV_PATH}: {', '.join(missing)}", file=sys.stderr)
        return 1
    if not args.dry_run:
        if not os.getenv("FAL_KEY"):
            print(f"FAL_KEY missing in {ENV_PATH} — needed to re-host MP4.",
                  file=sys.stderr)
            return 1
        if not higgsfield_available():
            print("higgsfield CLI not on PATH. Install per "
                  ".claude/skills/higgsfield/higgsfield-generate/SKILL.md "
                  "Step 0, then run `higgsfield auth login`.", file=sys.stderr)
            return 1

    if args.record_id:
        records = [_airtable_record(table_cfg, args.record_id)]
    else:
        records = _airtable_query(
            table_cfg,
            f'{{{table_cfg["status_field"]}}} = "{table_cfg["frames_generated"]}"',
        )
    if args.limit:
        records = records[: args.limit]

    if args.dry_run:
        dry_run_report(records, table_cfg)
        return 0

    if not records:
        log(f"No records with {table_cfg['status_field']} = "
            f"'{table_cfg['frames_generated']}' in {table_cfg['table_name']} — "
            f"nothing to do.")
        return 0
    if args.output is not None and len(records) > 1:
        print(f"--output is single-file; cannot use with {len(records)} records. "
              f"Use --record-id to target one row.", file=sys.stderr)
        return 1

    cost_per_clip = CREDITS_BY_DURATION.get(args.duration, DEFAULT_COST_PER_CLIP_CREDITS)
    if args.confirm is not None:
        if args.confirm.strip().lower() not in FIRE_WORDS:
            print(f"--confirm value {args.confirm!r} is not a fire word. "
                  f"Allowed: {sorted(FIRE_WORDS)}", file=sys.stderr)
            return 1
        # Still print the quote so the log captures what was approved.
        total_credits = len(records) * cost_per_clip
        log(f"Cost gate bypassed via --confirm {args.confirm!r}. "
            f"Approved: {len(records)} clip(s) x {cost_per_clip} = "
            f"{total_credits} credits ({args.duration}s each).")
    else:
        if not confirm_cost(len(records), duration_s=args.duration):
            log("Aborted at cost gate — no API calls made.")
            return 1

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    log(f"Confirmed. Processing {len(records)} record(s) on table "
        f"'{table_cfg['table_name']}'.")
    summary = {"ok": 0, "failed": 0, "skipped_no_frames": 0}
    for r in records:
        try:
            result = process_record(r, table_cfg, output_path=args.output,
                                    duration_s=args.duration)
        except Exception as e:
            log(f"FAIL {r['id']}: {e}")
            result = "failed"
        summary[result] = summary.get(result, 0) + 1

    log(f"Run complete. Summary: {summary}")

    if summary.get("ok", 0) > 0:
        try:
            _gates.append_gate(
                gate_number=1,
                gate_name="clip_generated_batch",
                record_id="batch",
                ad_name=(
                    f"video_gen batch on '{table_cfg['table_name']}' — "
                    f"{summary['ok']} clip(s) ready for human review (Gate 1)"
                ),
                video_url="",
                extra={
                    "table": table_cfg["table_name"],
                    "duration_s": args.duration,
                    "batch_summary": summary,
                    "next_step": "Review Higgsfield clips in Airtable. Approve or redo per record before hf_stitch.",
                },
            )
            log(f"Gate entry written → shared/gates/pending.json (clip batch, Gate 1).")
        except Exception as e:
            log(f"WARN: gate write failed: {e}")

    return 0 if summary.get("failed", 0) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
