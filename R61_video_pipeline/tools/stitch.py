"""
R61 Step 5 — FFmpeg stitch.

Reads Airtable Video records where Video Status = "Voiceover Done",
downloads the Video Clip (mp4) and Voiceover Audio (mp3), and stitches a
final 9:16 cinematic ad in this order:

    intro.mp4  →  video_clip.mp4  →  outro.mp4

Voiceover audio is mixed only over the video_clip segment. Intro and outro
keep their own audio. Inside the clip segment, voiceover plays at volume
0.9 and the clip's original audio plays at 0.3 so ambient sound stays
audible underneath the narration.

The real Provinzial Goldene-Flügel logo PNG is overlaid on the intro and
outro segments only (bottom-right, 15% of width, 10 px margin) so the
brand mark is the actual one, not the AI-stylised wings baked into the
intro/outro clips. The overlay never touches the daily clip segment.

Behaviour notes:
  • If references/inputs/intro.mp4 or references/inputs/outro.mp4 is
    missing, the tool logs a warning and skips that segment instead of
    failing.
  • If a clip/outro/intro file has no audio stream, the tool synthesises
    silence (anullsrc) for that segment so the concat filter stays happy.
  • Every record is gated by an interactive human confirmation: the exact
    FFmpeg command is printed and the operator types `go`/`fire`/`yes` to
    run it, or `skip` to skip just this record. Anything else aborts the
    whole run. This satisfies PIPELINE.md Gate #3 (stitch confirmation).
  • On success the final mp4 is written to
    references/outputs/final/{index}_{slugged_ad_name}.mp4, re-hosted on
    Fal storage, attached to Airtable field "Final Video", and Video
    Status is advanced from "Voiceover Done" → "Approved".

Pipeline-doc deviation: PIPELINE.md models the full flow as
"Voiceover Done" → "Stitched" → (Gate #4 preview) → "Approved". This tool
collapses the two transitions and treats the per-record FFmpeg-command
confirmation as the human gate, per the operator's explicit instructions
for this step. The full-preview gate happens in front of the rendered
final file via the operator's video player after run-completion.

Usage:
    python -m tools.stitch --dry-run            # read-only; no downloads, no ffmpeg
    python -m tools.stitch                      # interactive, per-record gate
    python -m tools.stitch --limit 3
    python -m tools.stitch --record-id recXXX
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
from tools.path_utils import check_output_path, clean_slug  # noqa: E402

LOG_PATH = PROJECT_ROOT / "references" / "outputs" / "stitch_run.log"
TMP_DIR = PROJECT_ROOT / "references" / "outputs" / "tmp"
FINAL_DIR = PROJECT_ROOT / "references" / "outputs" / "final"
INTRO_PATH = PROJECT_ROOT / "references" / "inputs" / "intro.mp4"
OUTRO_PATH = PROJECT_ROOT / "references" / "inputs" / "outro.mp4"

# Real Provinzial Goldene-Flügel logo. Overlaid on intro and outro segments
# only (the Higgsfield-generated brand wings in the AI intro/outro are
# stylized, not the actual mark — this overlay swaps the real one back in).
# Not overlaid on the clip segment so daily ad imagery stays untouched.
LOGO_PATH = (PROJECT_ROOT.parent / "R57_content_engine" / "references"
             / "inputs" / "_ascii" / "provinzial_logo_transparent.png")
LOGO_WIDTH_PCT = 0.15   # 15% of target width
LOGO_MARGIN_PX = 10     # bottom-right corner offset

# Target master format — 9:16 vertical, 1080x1920, 30 fps, stereo 48 kHz.
TARGET_W = 1080
TARGET_H = 1920
TARGET_FPS = 30
TARGET_SR = 48000

VO_VOLUME = 0.9
CLIP_AUDIO_VOLUME = 0.3

GO_WORDS = {"go", "fire", "yes", "run it", "run", "ship"}
SKIP_WORDS = {"skip", "s"}


def log(msg):
    ts = dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def slugify(name, max_len=60):
    """Filesystem-safe slug from an Ad Name. Preserves German umlauts.

    Thin alias for tools.path_utils.clean_slug. Kept as a name-stable
    re-export because other tools historically import `slugify` from this
    module. The implementation now strips brackets and ampersands too —
    those tripped up FFmpeg/npx/R2 in mid-May 2026.
    """
    return clean_slug(name, max_len=max_len)


def attachment_url(record, field_name):
    atts = record.get("fields", {}).get(field_name) or []
    if not atts:
        return None
    return atts[0].get("url")


def ext_from_url(url, default=".bin"):
    suffix = Path(urlparse(url).path).suffix
    return suffix if suffix else default


def download_attachment(url, dest_path):
    resp = requests.get(url, stream=True, timeout=180)
    resp.raise_for_status()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return dest_path


_R2_CLOCK_PATCHED = False


def _patch_botocore_clock(endpoint_url):
    """One-shot fix for local-clock skew vs Cloudflare R2.

    SigV4 rejects requests when the signed timestamp drifts >15 min from
    server time. The Windows host we run on is currently ~2h behind UTC
    (system-time misconfig), which makes every PutObject fail with
    `RequestTimeTooSkewed`. Rather than mutate the OS clock, we read the
    R2 server's `Date` header, compute the offset, and rebind
    `botocore.auth.datetime` to a shim whose `datetime.utcnow()` and
    `datetime.now()` return offset-corrected times. SigV4 picks those up
    transparently. Idempotent — subsequent calls re-use the existing patch.
    """
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
    except Exception as e:
        log(f"  WARN could not read R2 server time ({e}); skipping clock patch")
        _R2_CLOCK_PATCHED = True
        return

    local_dt = _dt.datetime.utcnow()
    offset = server_dt - local_dt
    if abs(offset.total_seconds()) < 60:
        log(f"  R2 clock offset {offset.total_seconds():+.1f}s (within tolerance)")
        _R2_CLOCK_PATCHED = True
        return

    # botocore SigV4 reads time exclusively via botocore.utils.get_current_datetime
    # (imported by name into botocore.auth at module-load), so patching the
    # `datetime` module reference is NOT enough — we must replace the function
    # in BOTH modules (utils owns it; auth holds a stale binding).
    def _shifted_get_current_datetime(remove_tzinfo=True):
        dt_now = _dt.datetime.now(_dt.timezone.utc) + offset
        if remove_tzinfo:
            dt_now = dt_now.replace(tzinfo=None)
        return dt_now

    botocore.utils.get_current_datetime = _shifted_get_current_datetime
    botocore.auth.get_current_datetime = _shifted_get_current_datetime
    log(f"  Patched botocore.{{auth,utils}}.get_current_datetime by "
        f"{offset.total_seconds():+.1f}s "
        f"(local={local_dt.isoformat()}Z, server={server_dt.isoformat()}Z)")
    _R2_CLOCK_PATCHED = True


def upload_to_r2(local_path, key, content_type="video/mp4"):
    """Push a local file into the Cloudflare R2 bucket and return its public URL.

    Uses the S3-compatible R2 endpoint via boto3. Credentials and bucket
    are read from R2_* env vars in .env (already used by R2 raw-footage
    pulls in this pipeline).

    We re-host to R2 instead of Fal because the project's FAL_KEY does not
    have permission to obtain fal-cdn-v3 signed-upload tokens for files
    >~1MB (rest.fal.ai returns 403 on /storage/auth/token). R2 sidesteps
    that entirely and gives Airtable a stable, controllable CDN URL.
    """
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


def ffmpeg_available():
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def probe_has_audio(path):
    """True if the media file at `path` has at least one audio stream."""
    if not Path(path).exists():
        return False
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30,
        )
        return "audio" in (proc.stdout or "").lower()
    except (subprocess.SubprocessError, OSError):
        return False


def probe_duration(path):
    """Return container duration in seconds, or None on failure."""
    if not Path(path).exists():
        return None
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30,
        )
        val = (proc.stdout or "").strip()
        return float(val) if val else None
    except (subprocess.SubprocessError, OSError, ValueError):
        return None


def build_segment_plan(intro, clip, vo, outro):
    """Decide which segments make it into the stitch and in what order.

    Each plan entry: {role, path, has_audio, duration}.
    Voiceover (vo) is not a video segment — it's mixed into the clip — so
    it's tracked separately by the caller.
    """
    plan = []
    if intro and Path(intro).exists():
        plan.append({
            "role": "intro",
            "path": intro,
            "has_audio": probe_has_audio(intro),
            "duration": probe_duration(intro),
        })
    else:
        if intro:
            log(f"  WARN intro missing at {intro} — skipping intro segment")
    # Clip is required.
    plan.append({
        "role": "clip",
        "path": clip,
        "has_audio": probe_has_audio(clip),
        "duration": probe_duration(clip),
    })
    if outro and Path(outro).exists():
        plan.append({
            "role": "outro",
            "path": outro,
            "has_audio": probe_has_audio(outro),
            "duration": probe_duration(outro),
        })
    else:
        if outro:
            log(f"  WARN outro missing at {outro} — skipping outro segment")
    return plan


def build_ffmpeg_command(plan, vo_path, output_path):
    """Build the exact ffmpeg argv list for one record.

    Strategy:
      • Each segment video stream is scaled/padded to 1080x1920 @ 30 fps.
      • Each segment audio stream is normalised to stereo / 48 kHz. If the
        source segment has no audio, anullsrc silence is synthesised for the
        full segment duration via an extra lavfi input.
      • The clip segment additionally amix'es the voiceover at VO_VOLUME
        with the clip audio at CLIP_AUDIO_VOLUME.
      • The real Provinzial logo PNG is overlaid on intro AND outro segments
        only (15% of width, bottom-right, 10px margin). NEVER overlaid on
        the clip segment.
      • All segments are concatenated with the concat filter (v=1, a=1).
    """
    inputs = []
    extra_lavfi_inputs = []  # appended after the real inputs

    # Map each segment to its (input index, lavfi index for synth silence).
    for seg in plan:
        seg["input_idx"] = len(inputs)
        inputs.append(seg["path"])
        if not seg["has_audio"]:
            dur = seg["duration"] or 5.0  # fallback; concat will cope
            extra_lavfi_inputs.append({
                "seg": seg,
                "duration": dur,
            })

    # Voiceover is always an input (audio-only consumer of [vo_idx:a]).
    # We'll add the lavfi silence inputs BEFORE the voiceover so the indexes
    # are stable. Rebuild ordering: first real video files, then lavfi
    # silence sources, then voiceover, then (optionally) logo PNG.
    for j, lav in enumerate(extra_lavfi_inputs):
        lav["input_idx"] = len(inputs) + j
        lav["seg"]["silence_idx"] = lav["input_idx"]
    vo_idx = len(inputs) + len(extra_lavfi_inputs)

    # Logo overlay setup — only for intro/outro segments and only if PNG
    # exists. If missing, skip overlay silently (warn at log site).
    overlay_segs = [s for s in plan if s["role"] in ("intro", "outro")]
    include_overlay = bool(overlay_segs) and LOGO_PATH.exists()
    if overlay_segs and not LOGO_PATH.exists():
        log(f"  WARN logo PNG missing at {LOGO_PATH} — overlay skipped")
    logo_idx = vo_idx + 1 if include_overlay else None

    # Build the argv.
    argv = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "info"]
    for path in inputs:
        argv += ["-i", str(path)]
    for lav in extra_lavfi_inputs:
        argv += [
            "-f", "lavfi",
            "-t", f"{lav['duration']:.3f}",
            "-i", f"anullsrc=channel_layout=stereo:sample_rate={TARGET_SR}",
        ]
    argv += ["-i", str(vo_path)]
    if include_overlay:
        # -loop 1 makes the single PNG into an infinite video stream the
        # overlay filter can consume against any segment duration.
        argv += ["-loop", "1", "-i", str(LOGO_PATH)]

    # Build the filter_complex.
    scale_pad = (
        f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET_W}:{TARGET_H}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1,fps={TARGET_FPS}"
    )
    fmt = f"aformat=channel_layouts=stereo:sample_rates={TARGET_SR}"

    parts = []
    concat_pairs = []
    for seg in plan:
        i = seg["input_idx"]
        role = seg["role"]
        # Intro/outro that will get a logo overlay end as `[v_{role}_base]`
        # so the overlay step below can produce `[v_{role}]`. Clip and any
        # non-overlay-eligible role go straight to `[v_{role}]`.
        if include_overlay and role in ("intro", "outro"):
            parts.append(f"[{i}:v]{scale_pad}[v_{role}_base]")
        else:
            parts.append(f"[{i}:v]{scale_pad}[v_{role}]")

        if seg["has_audio"]:
            a_src = f"[{i}:a]"
        else:
            a_src = f"[{seg['silence_idx']}:a]"
        if role == "clip":
            parts.append(f"{a_src}volume={CLIP_AUDIO_VOLUME},{fmt}[a_clip_base]")
            parts.append(f"[{vo_idx}:a]volume={VO_VOLUME},{fmt}[a_vo]")
            parts.append(
                "[a_clip_base][a_vo]amix=inputs=2:duration=first:"
                "dropout_transition=0,dynaudnorm[a_clip]"
            )
            concat_pairs.append(("[v_clip]", "[a_clip]"))
        else:
            parts.append(f"{a_src}{fmt}[a_{role}]")
            concat_pairs.append((f"[v_{role}]", f"[a_{role}]"))

    # Logo overlay branch — scale logo once, split across N overlay segments,
    # composite each into its base.
    if include_overlay:
        logo_w = int(TARGET_W * LOGO_WIDTH_PCT)
        m = LOGO_MARGIN_PX
        overlay_roles = [s["role"] for s in overlay_segs]
        n_ov = len(overlay_roles)
        if n_ov == 1:
            role = overlay_roles[0]
            parts.append(
                f"[{logo_idx}:v]scale={logo_w}:-1,format=rgba[v_logo_{role}]"
            )
        else:
            split_labels = "".join(f"[v_logo_{r}]" for r in overlay_roles)
            parts.append(
                f"[{logo_idx}:v]scale={logo_w}:-1,format=rgba,"
                f"split={n_ov}{split_labels}"
            )
        for role in overlay_roles:
            parts.append(
                f"[v_{role}_base][v_logo_{role}]"
                f"overlay=x=W-w-{m}:y=H-h-{m}:shortest=1[v_{role}]"
            )

    n = len(concat_pairs)
    concat_inputs = "".join(v + a for v, a in concat_pairs)
    parts.append(f"{concat_inputs}concat=n={n}:v=1:a=1[outv][outa]")

    filter_complex = ";".join(parts)

    argv += [
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(TARGET_SR),
        "-movflags", "+faststart",
        str(output_path),
    ]
    return argv


def render_cmd(argv):
    """Pretty-print an argv list as a shell-ish single line for the operator."""
    return subprocess.list2cmdline(argv)


def gate_for_record(argv, ad_name):
    """Print the exact ffmpeg command and gate on operator confirmation.

    Returns one of: 'go', 'skip', 'abort'.
    """
    print()
    print("=" * 70)
    print(f"STITCH GATE — {ad_name}")
    print("=" * 70)
    print("Exact FFmpeg command:")
    print()
    print(render_cmd(argv))
    print()
    print(f"  Type one of {sorted(GO_WORDS)} to RUN this stitch.")
    print(f"  Type one of {sorted(SKIP_WORDS)} to SKIP just this record.")
    print( "  Anything else ABORTS the run.")
    answer = input("> ").strip().lower()
    if answer in GO_WORDS:
        return "go"
    if answer in SKIP_WORDS:
        return "skip"
    return "abort"


def run_ffmpeg(argv):
    """Run ffmpeg streaming stderr to the log. Raises on non-zero exit."""
    log("  $ " + render_cmd(argv))
    proc = subprocess.run(
        argv, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()[-30:]
        raise RuntimeError(
            "ffmpeg failed (exit "
            f"{proc.returncode}). Last stderr lines:\n"
            + "\n".join(tail)
        )
    # Log the last few stderr lines (ffmpeg always writes status to stderr).
    tail = (proc.stderr or "").strip().splitlines()[-3:]
    for line in tail:
        log(f"  ffmpeg: {line}")


def process_record(record, auto_confirm=None):
    rec_id = record["id"]
    fields = record.get("fields", {})
    ad_name = fields.get("Ad Name") or "(no name)"
    index = fields.get("Index")

    clip_url = attachment_url(record, "Video Clip")
    vo_url = attachment_url(record, "Voiceover Audio")
    if not clip_url:
        log(f"SKIP {rec_id} ({ad_name}): missing Video Clip attachment")
        return "skipped_missing_inputs"
    if not vo_url:
        log(f"SKIP {rec_id} ({ad_name}): missing Voiceover Audio attachment")
        return "skipped_missing_inputs"

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    clip_local = TMP_DIR / f"{rec_id}_clip{ext_from_url(clip_url, '.mp4')}"
    vo_local = TMP_DIR / f"{rec_id}_vo{ext_from_url(vo_url, '.mp3')}"
    log(f"START {rec_id} ({ad_name})")
    download_attachment(clip_url, clip_local)
    download_attachment(vo_url, vo_local)
    log(f"  downloaded clip -> {clip_local.name}, vo -> {vo_local.name}")

    intro = INTRO_PATH if INTRO_PATH.exists() else None
    outro = OUTRO_PATH if OUTRO_PATH.exists() else None
    if intro is None:
        log(f"  WARN intro missing at {INTRO_PATH} — skipping intro segment")
    if outro is None:
        log(f"  WARN outro missing at {OUTRO_PATH} — skipping outro segment")

    plan = build_segment_plan(intro, clip_local, vo_local, outro)
    log(f"  segments: {[s['role'] for s in plan]}")

    out_name = f"{index}_{slugify(ad_name)}.mp4" if index is not None \
        else f"{rec_id}_{slugify(ad_name)}.mp4"
    output_path = check_output_path(FINAL_DIR / out_name)
    if output_path.name != out_name:
        log(f"  version-incremented output → {output_path.name} "
            f"(prior render preserved per SOUL.md rule 2)")
        out_name = output_path.name

    argv = build_ffmpeg_command(plan, vo_local, output_path)

    if auto_confirm:
        log(f"  gate bypassed via --confirm {auto_confirm!r}")
        log(f"  $ {render_cmd(argv)}")
        decision = "go"
    else:
        decision = gate_for_record(argv, ad_name)
    if decision == "abort":
        log(f"ABORT at gate on {rec_id} ({ad_name}) — stopping whole run.")
        raise SystemExit(3)
    if decision == "skip":
        log(f"SKIP gate decision on {rec_id} ({ad_name}) — moving on.")
        return "skipped_at_gate"

    run_ffmpeg(argv)
    log(f"  stitched -> {output_path}")

    r2_key = f"r61/final/{out_name}"
    public_url = upload_to_r2(output_path, r2_key, content_type="video/mp4")
    log(f"  uploaded to R2 -> {public_url}")

    av.update_record(
        rec_id,
        {
            "Final Video": [{"url": public_url, "filename": out_name}],
            av.STATUS_FIELD: av.STATUS_APPROVED,
        },
    )
    log(f"DONE  {rec_id} ({ad_name}) status -> {av.STATUS_APPROVED}")
    return "ok"


def dry_run_report(records, filter_label="(see args)"):
    print()
    print(f"DRY RUN — base {av.AIRTABLE_BASE_ID}, table '{av.TABLE_NAME}' "
          f"({av.TABLE_ID})")
    print(f"Filter: {filter_label}")
    print(f"Records matched: {len(records)}")
    print(f"intro.mp4 present: {INTRO_PATH.exists()}  ({INTRO_PATH})")
    print(f"outro.mp4 present: {OUTRO_PATH.exists()}  ({OUTRO_PATH})")
    print(f"logo PNG present : {LOGO_PATH.exists()}  ({LOGO_PATH})")
    print(f"  overlay applied on: intro + outro only (15% width, "
          f"bottom-right, {LOGO_MARGIN_PX}px margin)")
    print(f"ffmpeg/ffprobe on PATH: {ffmpeg_available()}")
    if not records:
        print("  (no rows ready for stitch)")
        return
    intro = INTRO_PATH if INTRO_PATH.exists() else None
    outro = OUTRO_PATH if OUTRO_PATH.exists() else None
    for r in records:
        f = r.get("fields", {})
        rec_id = r["id"]
        index = f.get("Index")
        ad_name = f.get("Ad Name") or "(no name)"
        clip_url = attachment_url(r, "Video Clip") or "<missing>"
        vo_url = attachment_url(r, "Voiceover Audio") or "<missing>"
        print(f"  - {rec_id}  Index={index!r}  Ad Name={ad_name!r}")
        print(f"      Video Clip      : {clip_url[:80]}"
              f"{'...' if len(clip_url) > 80 else ''}")
        print(f"      Voiceover Audio : {vo_url[:80]}"
              f"{'...' if len(vo_url) > 80 else ''}")
        if "<missing>" in (clip_url, vo_url):
            print(f"      [WOULD SKIP — missing attachment(s)]")
            continue
        # Build a representative command using placeholder local paths so
        # the operator can see the exact shape without us downloading files.
        clip_ph = TMP_DIR / f"{rec_id}_clip.mp4"
        vo_ph = TMP_DIR / f"{rec_id}_vo.mp3"
        plan = []
        if intro:
            plan.append({"role": "intro", "path": intro,
                         "has_audio": probe_has_audio(intro),
                         "duration": probe_duration(intro)})
        plan.append({"role": "clip", "path": clip_ph,
                     "has_audio": True, "duration": None})  # assume audio
        if outro:
            plan.append({"role": "outro", "path": outro,
                         "has_audio": probe_has_audio(outro),
                         "duration": probe_duration(outro)})
        out_name = f"{index}_{slugify(ad_name)}.mp4" if index is not None \
            else f"{rec_id}_{slugify(ad_name)}.mp4"
        out_path = FINAL_DIR / out_name
        argv = build_ffmpeg_command(plan, vo_ph, out_path)
        print(f"      Segments order  : {[s['role'] for s in plan]}")
        print(f"      Output file     : {out_path}")
        print(f"      FFmpeg command  :")
        print(f"        {render_cmd(argv)}")
    print()
    print(f"Voiceover mix: vo={VO_VOLUME}, clip_audio={CLIP_AUDIO_VOLUME} "
          f"(clip segment only).")
    print(f"Master format: {TARGET_W}x{TARGET_H} @ {TARGET_FPS}fps, "
          f"stereo {TARGET_SR}Hz, libx264 crf=20, aac 192k.")
    print("No downloads, no ffmpeg invocations, no Airtable writes were made.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="R61 Step 5 — FFmpeg stitch (intro + clip+vo-mix + outro)"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Read Airtable and show what would happen; "
                             "no downloads, no ffmpeg, no writes.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N records this run.")
    parser.add_argument("--record-id", default=None,
                        help="Force-process this single Airtable record id, "
                             "bypassing the Video Status filter.")
    parser.add_argument("--confirm", default=None,
                        help="Pass a fire word (e.g. --confirm go) to bypass "
                             "the per-record FFmpeg-command gate. Use only "
                             "for non-interactive batch runs where you've "
                             "already audited the command shape.")
    parser.add_argument("--include-approved", action="store_true",
                        help="Also re-stitch records that are already in "
                             "Approved state (status stays Approved after; "
                             "Final Video attachment gets overwritten with "
                             "the new render).")
    parser.add_argument("--only-approved", action="store_true",
                        help="Process ONLY records currently in Approved "
                             "state. Use to re-stitch existing finals after "
                             "a recipe change (e.g. new logo overlay).")
    args = parser.parse_args(argv)
    if args.include_approved and args.only_approved:
        print("--include-approved and --only-approved are mutually exclusive.",
              file=sys.stderr)
        return 1

    missing = av.check_credentials()
    if missing:
        print(f"Missing env vars in {ENV_PATH}: {', '.join(missing)}",
              file=sys.stderr)
        return 1
    if not args.dry_run:
        if not ffmpeg_available():
            print("ffmpeg/ffprobe not on PATH — install FFmpeg before a paid run.",
                  file=sys.stderr)
            return 1
        r2_required = ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID",
                       "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME",
                       "R2_PUBLIC_URL"]
        missing_r2 = [v for v in r2_required if not os.getenv(v)]
        if missing_r2:
            print(f"Missing R2 env vars in {ENV_PATH}: {', '.join(missing_r2)} "
                  f"— needed to re-host the final mp4.", file=sys.stderr)
            return 1

    if args.record_id:
        records = [av.get_record(args.record_id)]
    elif args.only_approved:
        records = av.get_records(
            f'{{{av.STATUS_FIELD}}} = "{av.STATUS_APPROVED}"'
        )
    elif args.include_approved:
        records = av.get_records(
            f'OR({{{av.STATUS_FIELD}}} = "{av.STATUS_VOICEOVER_DONE}",'
            f'{{{av.STATUS_FIELD}}} = "{av.STATUS_APPROVED}")'
        )
    else:
        records = av.get_records(
            f'{{{av.STATUS_FIELD}}} = "{av.STATUS_VOICEOVER_DONE}"'
        )
    if args.limit:
        records = records[: args.limit]

    if args.dry_run:
        if args.record_id:
            label = f"--record-id {args.record_id}"
        elif args.only_approved:
            label = f"{{{av.STATUS_FIELD}}} = \"{av.STATUS_APPROVED}\""
        elif args.include_approved:
            label = (f"{{{av.STATUS_FIELD}}} in "
                     f"[\"{av.STATUS_VOICEOVER_DONE}\", "
                     f"\"{av.STATUS_APPROVED}\"]")
        else:
            label = f"{{{av.STATUS_FIELD}}} = \"{av.STATUS_VOICEOVER_DONE}\""
        dry_run_report(records, filter_label=label)
        return 0

    if not records:
        log("No records with Video Status = 'Voiceover Done' — nothing to do.")
        return 0

    bypass = None
    if args.confirm is not None:
        if args.confirm.strip().lower() not in GO_WORDS:
            print(f"--confirm value {args.confirm!r} is not a fire word. "
                  f"Allowed: {sorted(GO_WORDS)}", file=sys.stderr)
            return 1
        bypass = args.confirm.strip().lower()
        log(f"Per-record gate BYPASSED via --confirm {bypass!r}. "
            f"All {len(records)} record(s) will stitch without prompting.")

    log(f"Processing {len(records)} record(s). "
        f"{'Auto-confirm.' if bypass else 'Per-record gate is interactive.'}")
    summary = {"ok": 0, "failed": 0,
               "skipped_missing_inputs": 0, "skipped_at_gate": 0}
    for r in records:
        try:
            result = process_record(r, auto_confirm=bypass)
        except SystemExit:
            raise
        except Exception as e:
            log(f"FAIL {r['id']}: {e}")
            result = "failed"
        summary[result] = summary.get(result, 0) + 1

    log(f"Run complete. Summary: {summary}")
    return 0 if summary.get("failed", 0) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
