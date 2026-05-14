"""
R61 v2 stitcher — hybrid FFmpeg pre-mix + HyperFrames visual composition.

Replaces the v1 FFmpeg-only concat path with a two-step approach:

  1. FFmpeg pre-mix per record:
       amix(voiceover @ 0.9, clip_audio @ 0.3, duration=longest, dynaudnorm)
       → references/outputs/tmp/{index}_mixed_audio.aac
     The voiceover may be longer than the 5.04s clip (it usually is); using
     duration=longest preserves the full narration that v1 used to truncate.
     The clip's last frame is also extracted to a still PNG so scene 2 can
     "hold" on it after the video segment ends.

  2. HyperFrames visual composition per record:
       references/outputs/hf_work/{index}/index.html
     1080x1920 vertical, 30 fps, 4 visual segments + 1 audio segment:
       - intro.mp4    t=0.000          dur=2.750  (muted; intro has no audio)
       - clip.mp4     t=2.750          dur=5.042  (muted; mixed audio carries)
       - lastframe    t=7.792          dur=vo_len - 5.042
       - outro.mp4    t=2.750+vo_len   dur=2.750  (muted; outro has no audio)
       - audio mix    t=2.750          dur=vo_len  (data-volume=1)
     Rendered to references/outputs/final/v2/{index}_{slug}.mp4 via
     `npx hyperframes render`.

  3. Publish: upload the v2 mp4 to R2 under `r61/final/v2/{name}` (never
     overwrites the v1 path) and PATCH Airtable's `Final Video` attachment
     field with the new public URL. Video Status is left untouched per
     operator instruction (records may be Scheduled when v2 is regenerated).

Operator rules:
  * Never delete v1 files. New work always lands in v2 paths. See
    ~/.claude/projects/.../feedback_never_delete_old_content.md.
  * intro.mp4 / outro.mp4 are video-only (no audio stream). HyperFrames
    requires <video muted playsinline>, so even if those sources later
    grow an audio stream it would be ignored — by design.

Usage:
    python -m tools.hf_stitch --record-id rec4cuKlnZwe0Slag
    python -m tools.hf_stitch --record-id rec... --skip-publish   # render only
    python -m tools.hf_stitch --all-approved-or-scheduled         # batch
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

from tools import airtable_video as av  # noqa: E402
from tools import _gates  # noqa: E402
from tools.path_utils import check_output_path, clean_slug  # noqa: E402
from tools.stitch import (  # noqa: E402
    attachment_url,
    ext_from_url,
    download_attachment,
    probe_duration,
    upload_to_r2,
)

# Version tag controls both the local final dir and the R2 key prefix so a
# new render generation can be cut over by changing one env var. Defaults
# to v3 for backwards compatibility with the existing render shelf.
VERSION_TAG = os.environ.get("R61_VERSION_TAG", "v3")

LOG_PATH = PROJECT_ROOT / "references" / "outputs" / "hf_stitch_run.log"
TMP_DIR = PROJECT_ROOT / "references" / "outputs" / "tmp"
HF_WORK_DIR = PROJECT_ROOT / "references" / "outputs" / "hf_work"
FINAL_DIR = PROJECT_ROOT / "references" / "outputs" / "final" / VERSION_TAG
INTRO_PATH = PROJECT_ROOT / "references" / "inputs" / "intro.mp4"
OUTRO_PATH = PROJECT_ROOT / "references" / "outputs" / "outro.mp4"

VO_VOLUME = 0.9
CLIP_AUDIO_VOLUME = 0.3

TARGET_W = 1080
TARGET_H = 1920
TARGET_SR = 48000


def log(msg):
    ts = dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def premix_audio(clip_path: Path, vo_path: Path, out_path: Path):
    """Mix voiceover (0.9) with clip audio (0.3), duration=longest, dynaudnorm."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        log(f"  premix exists, skipping ffmpeg → {out_path.name}")
        return
    argv = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(clip_path),
        "-i", str(vo_path),
        "-filter_complex",
        (
            f"[0:a]volume={CLIP_AUDIO_VOLUME},"
            f"aformat=channel_layouts=stereo:sample_rates={TARGET_SR}[ac];"
            f"[1:a]volume={VO_VOLUME},"
            f"aformat=channel_layouts=stereo:sample_rates={TARGET_SR}[av];"
            f"[ac][av]amix=inputs=2:duration=longest:dropout_transition=0,"
            f"dynaudnorm[outa]"
        ),
        "-map", "[outa]",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(TARGET_SR),
        str(out_path),
    ]
    proc = subprocess.run(argv, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError("premix ffmpeg failed:\n" + (proc.stderr or "")[-2000:])


def extract_last_frame(clip_path: Path, out_path: Path):
    """Pull the final frame of the clip as a high-quality PNG."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        log(f"  lastframe exists, skipping ffmpeg → {out_path.name}")
        return
    argv = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-sseof", "-0.1",
        "-i", str(clip_path),
        "-frames:v", "1", "-q:v", "2",
        str(out_path),
    ]
    proc = subprocess.run(argv, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError("lastframe ffmpeg failed:\n" + (proc.stderr or "")[-2000:])


def stage_workdir(workdir: Path, intro_src: Path, outro_src: Path,
                  clip_src: Path, audio_src: Path, lastframe_src: Path):
    """Copy assets into the per-record workdir alongside index.html."""
    workdir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(intro_src,     workdir / "intro.mp4")
    shutil.copyfile(outro_src,     workdir / "outro.mp4")
    shutil.copyfile(clip_src,      workdir / "clip.mp4")
    shutil.copyfile(audio_src,     workdir / "mixed_audio.aac")
    shutil.copyfile(lastframe_src, workdir / "clip_lastframe.png")


def write_composition(workdir: Path, comp_id: str, ad_label: str,
                      intro_dur: float, clip_dur: float, audio_dur: float,
                      outro_dur: float):
    """Emit index.html. Scene 2 = max(clip, audio) + 1-frame buffer.

    All timestamps are computed in integer milliseconds to avoid float
    drift between data-start and the derived start of the next clip.
    A 50ms buffer (~1.5 frames) is added between scene 2 end and outro
    start; HF's overlap lint treats touching boundaries as overlaps for
    some audio durations because freeze_end and outro_start may resolve
    to slightly different float values when computed independently
    (e.g. 7.792 + 3.114 → 10.905999... while a separately-computed
    outro_start rounds to 10.905). Working entirely in ms makes every
    timestamp a clean derivable sum and the +50ms buffer is
    sub-perceptual (extra hold on the clip's last frame after the VO
    finishes, before the outro cuts in).
    """
    def to_ms(s): return int(round(s * 1000))
    def fmt_ms(ms): return f"{ms / 1000:.3f}"

    intro_ms = to_ms(intro_dur)
    clip_ms = to_ms(clip_dur)
    audio_ms = to_ms(audio_dur)
    outro_ms = to_ms(outro_dur)
    FRAME_BUFFER_MS = 50  # sub-frame safety against float-rounding overlaps

    scene2_ms = max(clip_ms, audio_ms) + FRAME_BUFFER_MS
    freeze_ms = scene2_ms - clip_ms

    t1_ms = intro_ms                      # intro_end == clip_start
    t2_ms = t1_ms + clip_ms               # clip_end == freeze_start
    t3_ms = t1_ms + scene2_ms             # scene2_end == outro_start
    t4_ms = t3_ms + outro_ms              # composition_end

    t_intro_end = t1_ms / 1000.0
    t_clip_end = t2_ms / 1000.0
    t_scene2_end = t3_ms / 1000.0
    t_total = t4_ms / 1000.0
    freeze_start = t_clip_end
    freeze_dur = freeze_ms / 1000.0

    safe_title = (ad_label or comp_id).replace("<", "&lt;").replace(">", "&gt;")
    css_id = comp_id

    parts = []
    parts.append('<!doctype html>')
    parts.append('<html lang="de">')
    parts.append('<head>')
    parts.append('  <meta charset="utf-8" />')
    parts.append(f'  <title>R61 v2 — {safe_title}</title>')
    parts.append('  <style>')
    parts.append('    html, body { margin: 0; padding: 0; background: #000; }')
    parts.append(f'    #{css_id} {{')
    parts.append('      position: relative;')
    parts.append('      background: #000;')
    parts.append('      overflow: hidden;')
    parts.append('    }')
    parts.append(f'    #{css_id} video,')
    parts.append(f'    #{css_id} img {{')
    parts.append('      position: absolute;')
    parts.append('      top: 0;')
    parts.append('      left: 0;')
    parts.append('      width: 100%;')
    parts.append('      height: 100%;')
    parts.append('      object-fit: cover;')
    parts.append('    }')
    parts.append('  </style>')
    parts.append('</head>')
    parts.append('<body>')
    parts.append(f'  <div')
    parts.append(f'    id="{css_id}"')
    parts.append(f'    data-composition-id="{comp_id}"')
    parts.append(f'    data-start="0"')
    parts.append(f'    data-duration="{t_total:.3f}"')
    parts.append(f'    data-width="{TARGET_W}"')
    parts.append(f'    data-height="{TARGET_H}"')
    parts.append(f'  >')
    parts.append(f'    <!-- Scene 1: Intro (0.000 – {t_intro_end:.3f}) -->')
    parts.append(f'    <video id="v-intro" data-start="0" '
                 f'data-duration="{intro_dur:.3f}" data-track-index="0" '
                 f'src="intro.mp4" muted playsinline></video>')
    parts.append(f'    <!-- Scene 2a: Clip ({t_intro_end:.3f} – {t_clip_end:.3f}) -->')
    parts.append(f'    <video id="v-clip" data-start="{t_intro_end:.3f}" '
                 f'data-duration="{clip_dur:.3f}" data-track-index="0" '
                 f'src="clip.mp4" muted playsinline></video>')
    if freeze_dur > 0.01:
        parts.append(f'    <!-- Scene 2b: Frozen last frame '
                     f'({freeze_start:.3f} – {t_scene2_end:.3f}) — '
                     f'holds while VO finishes -->')
        parts.append(f'    <img id="v-freeze" class="clip" '
                     f'data-start="{freeze_start:.3f}" '
                     f'data-duration="{freeze_dur:.3f}" '
                     f'data-track-index="0" '
                     f'src="clip_lastframe.png" alt="" />')
    parts.append(f'    <!-- Scene 3: Outro ({t_scene2_end:.3f} – {t_total:.3f}) -->')
    parts.append(f'    <video id="v-outro" data-start="{t_scene2_end:.3f}" '
                 f'data-duration="{outro_dur:.3f}" data-track-index="0" '
                 f'src="outro.mp4" muted playsinline></video>')
    parts.append(f'    <!-- Pre-mixed audio: vo @ {VO_VOLUME} + clip_audio @ '
                 f'{CLIP_AUDIO_VOLUME} (amix duration=longest, dynaudnorm) -->')
    parts.append(f'    <audio id="a-mix" data-start="{t_intro_end:.3f}" '
                 f'data-duration="{audio_dur:.3f}" data-track-index="1" '
                 f'data-volume="1" src="mixed_audio.aac"></audio>')
    parts.append('    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>')
    parts.append('    <script>')
    parts.append('      window.__timelines = window.__timelines || {};')
    parts.append('      // Hard cuts (matching v1 aesthetic). Timeline registered empty.')
    parts.append('      const tl = gsap.timeline({ paused: true });')
    parts.append(f'      window.__timelines["{comp_id}"] = tl;')
    parts.append('    </script>')
    parts.append('  </div>')
    parts.append('</body>')
    parts.append('</html>')
    parts.append('')

    html = "\n".join(parts)
    (workdir / "index.html").write_text(html, encoding="utf-8")
    return t_total


def run_hyperframes(workdir: Path, output_path: Path):
    """Invoke `npx hyperframes lint` then `npx hyperframes render`.

    npx.cmd shells out through cmd.exe, which parses `&` in arguments as a
    command separator even when subprocess passes the args as a list. Some
    of the Ad Names contain `&` (e.g. "Regional_&_Gemeinschaft"), so we
    render to a safe ASCII-only filename inside the workdir, then move
    the result to the real output path with Python (which is not affected
    by cmd parsing). See:
      https://github.com/python/cpython/issues/89549
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lint = subprocess.run(
        ["npx.cmd", "hyperframes", "lint"],
        cwd=str(workdir),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if lint.returncode != 0:
        raise RuntimeError("hyperframes lint failed:\n" + (lint.stdout or "")
                           + "\n" + (lint.stderr or ""))
    log(f"  lint OK ({workdir.name})")

    safe_out = workdir / "_render_output.mp4"
    if safe_out.exists():
        safe_out.unlink()
    render = subprocess.run(
        ["npx.cmd", "hyperframes", "render", "-o", str(safe_out)],
        cwd=str(workdir),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if render.returncode != 0:
        raise RuntimeError("hyperframes render failed:\n" + (render.stdout or "")
                           + "\n" + (render.stderr or ""))
    if not safe_out.exists():
        raise RuntimeError(
            f"hyperframes render reported success but {safe_out} is missing"
        )
    shutil.move(str(safe_out), str(output_path))
    log(f"  rendered → {output_path}  ({output_path.stat().st_size/1e6:.1f} MB)")


def publish_to_r2_and_airtable(record_id: str, mp4_path: Path, key_name: str,
                               advance_status: bool = False):
    """Upload mp4 to r61/final/{VERSION_TAG}/{key_name} and PATCH the Airtable record.

    If advance_status is True, also set Video Status = "Stitched".
    Used by --all-voiceover-done batch (fresh pipeline progression). The
    older --all-approved-or-scheduled batch keeps status untouched because
    those records are re-renders of already-Scheduled finals.
    """
    r2_key = f"r61/final/{VERSION_TAG}/{key_name}"
    public_url = upload_to_r2(mp4_path, r2_key, content_type="video/mp4")
    log(f"  uploaded → {public_url}")

    patch = {"Final Video": [{"url": public_url, "filename": key_name}]}
    if advance_status:
        patch[av.STATUS_FIELD] = av.STATUS_STITCHED
    av.update_record(record_id, patch)
    status_note = f"+status={av.STATUS_STITCHED}" if advance_status else "status untouched"
    log(f"  Airtable Final Video updated for {record_id} ({status_note})")
    return public_url


def process_record(record, skip_publish=False, force_premix=False,
                   advance_status=False):
    """End-to-end v2 build for one Airtable record."""
    rec_id = record["id"]
    fields = record.get("fields", {})
    ad_name = fields.get("Ad Name") or "(no name)"
    index = fields.get("Index")
    log(f"START {rec_id}  Index={index}  '{ad_name}'")

    clip_url = attachment_url(record, "Video Clip")
    vo_url = attachment_url(record, "Voiceover Audio")
    if not clip_url or not vo_url:
        log(f"  SKIP — missing Video Clip or Voiceover Audio attachment")
        return "skipped_missing_inputs"

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    clip_local = TMP_DIR / f"{rec_id}_clip{ext_from_url(clip_url, '.mp4')}"
    vo_local = TMP_DIR / f"{rec_id}_vo{ext_from_url(vo_url, '.mp3')}"
    if not clip_local.exists():
        download_attachment(clip_url, clip_local)
        log(f"  downloaded clip → {clip_local.name}")
    if not vo_local.exists():
        download_attachment(vo_url, vo_local)
        log(f"  downloaded vo → {vo_local.name}")

    audio_out = TMP_DIR / f"{index}_mixed_audio.aac"
    lastframe_out = TMP_DIR / f"{index}_clip_lastframe.png"
    if force_premix:
        for p in (audio_out, lastframe_out):
            if p.exists():
                p.unlink()
    premix_audio(clip_local, vo_local, audio_out)
    extract_last_frame(clip_local, lastframe_out)
    log(f"  premix → {audio_out.name}, lastframe → {lastframe_out.name}")

    intro_dur = probe_duration(INTRO_PATH) or 2.75
    outro_dur = probe_duration(OUTRO_PATH) or 2.75
    clip_dur = probe_duration(clip_local) or 5.042
    audio_dur = probe_duration(audio_out) or clip_dur
    log(f"  durations: intro={intro_dur:.3f}s clip={clip_dur:.3f}s "
        f"audio={audio_dur:.3f}s outro={outro_dur:.3f}s")

    workdir = HF_WORK_DIR / f"{index}"
    stage_workdir(workdir, INTRO_PATH, OUTRO_PATH, clip_local,
                  audio_out, lastframe_out)
    comp_id = f"r61-day{index}"
    total = write_composition(workdir, comp_id, ad_name,
                              intro_dur, clip_dur, audio_dur, outro_dur)
    log(f"  composition staged: {workdir}  (total {total:.3f}s)")

    out_name = f"{index}_{clean_slug(ad_name)}.mp4"
    output_path = check_output_path(FINAL_DIR / out_name)
    if output_path.name != out_name:
        log(f"  version-incremented output → {output_path.name} "
            f"(original existed; preserving prior render per SOUL.md rule 2)")
        out_name = output_path.name
    run_hyperframes(workdir, output_path)

    if skip_publish:
        log(f"  --skip-publish set; not uploading or touching Airtable")
        return "rendered_only"

    public_url = publish_to_r2_and_airtable(rec_id, output_path, out_name,
                                            advance_status=advance_status)
    log(f"DONE  {rec_id}")

    try:
        _gates.append_gate(
            gate_number=4,
            gate_name="stitch_final_preview",
            record_id=rec_id,
            ad_name=ad_name,
            video_url=public_url or "",
            extra={
                "local_path": str(output_path),
                "index": index,
                "advance_status": advance_status,
                "next_step": "Watch final preview. Approve to Blotato-schedule, or request redo.",
            },
        )
        log(f"Gate entry written → shared/gates/pending.json ({rec_id}, Gate 4).")
    except Exception as e:
        log(f"WARN: gate write failed: {e}")

    return "ok"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="R61 v2 hybrid stitcher (FFmpeg pre-mix + HyperFrames)"
    )
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--record-id", help="Process a single Airtable record id.")
    grp.add_argument("--all-approved-or-scheduled", action="store_true",
                     help="Process every record with Video Status in "
                          "{Approved, Scheduled} that has both Video Clip "
                          "and Voiceover Audio attachments. Status untouched "
                          "(intended for re-renders).")
    grp.add_argument("--all-voiceover-done", action="store_true",
                     help="Process every record with Video Status = "
                          "Voiceover Done that has both Video Clip and "
                          "Voiceover Audio attachments. Advances status to "
                          "Stitched on success (fresh pipeline progression).")
    parser.add_argument("--skip-publish", action="store_true",
                        help="Render but don't upload to R2 or touch Airtable.")
    parser.add_argument("--force-premix", action="store_true",
                        help="Re-run FFmpeg pre-mix and lastframe even if "
                             "the output files already exist.")
    args = parser.parse_args(argv)

    missing = av.check_credentials()
    if missing:
        print(f"Missing env vars in {ENV_PATH}: {', '.join(missing)}",
              file=sys.stderr)
        return 1

    advance_status = False
    if args.record_id:
        records = [av.get_record(args.record_id)]
    elif args.all_voiceover_done:
        records = av.get_records(
            f'{{{av.STATUS_FIELD}}} = "{av.STATUS_VOICEOVER_DONE}"'
        )
        records = [r for r in records
                   if attachment_url(r, "Video Clip")
                   and attachment_url(r, "Voiceover Audio")]
        records.sort(key=lambda r: r.get("fields", {}).get("Index") or 9999)
        advance_status = True
    else:
        records = av.get_records(
            f'OR({{{av.STATUS_FIELD}}} = "{av.STATUS_APPROVED}",'
            f'{{{av.STATUS_FIELD}}} = "{av.STATUS_SCHEDULED}")'
        )
        records = [r for r in records
                   if attachment_url(r, "Video Clip")
                   and attachment_url(r, "Voiceover Audio")]
        records.sort(key=lambda r: r.get("fields", {}).get("Index") or 9999)

    log(f"Processing {len(records)} record(s). advance_status={advance_status}")
    summary = {"ok": 0, "rendered_only": 0,
               "skipped_missing_inputs": 0, "failed": 0}
    for r in records:
        try:
            res = process_record(r, skip_publish=args.skip_publish,
                                 force_premix=args.force_premix,
                                 advance_status=advance_status)
        except Exception as e:
            log(f"FAIL {r['id']}: {e}")
            res = "failed"
        summary[res] = summary.get(res, 0) + 1
    log(f"Run complete. Summary: {summary}")
    return 0 if summary.get("failed", 0) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
