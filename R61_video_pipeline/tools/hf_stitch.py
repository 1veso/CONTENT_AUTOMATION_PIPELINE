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
# Env-level default for captions burn-in. CLI --add-captions overrides this.
ADD_CAPTIONS_DEFAULT = os.environ.get("R61_ADD_CAPTIONS", "").lower() in ("1", "true", "yes")

LOG_PATH = PROJECT_ROOT / "references" / "outputs" / "hf_stitch_run.log"
TMP_DIR = PROJECT_ROOT / "references" / "outputs" / "tmp"
HF_WORK_DIR = PROJECT_ROOT / "references" / "outputs" / "hf_work"
FINAL_DIR = PROJECT_ROOT / "references" / "outputs" / "final" / VERSION_TAG
CAPTIONS_DIR = FINAL_DIR / "captions"
REFERENCES_INPUT_DIR = PROJECT_ROOT / "references" / "inputs"
INTRO_PATH = REFERENCES_INPUT_DIR / "intro.mp4"
# CANONICAL OUTRO: references/outputs/outro.mp4 (2.75s, 716x1284, silent)
# Do NOT confuse with references/inputs/outro_5s_audio_DEPRECATED.mp4
OUTRO_PATH = PROJECT_ROOT / "references" / "outputs" / "outro.mp4"
WATERMARK_PATH = REFERENCES_INPUT_DIR / "wings.png"

VO_VOLUME = 0.9
CLIP_AUDIO_VOLUME = 0.3

TARGET_W = 1080
TARGET_H = 1920
TARGET_SR = 48000

CAPTION_CHUNK_MAX_CHARS = 42


def log(msg):
    ts = dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def apply_watermark(input_video_path, output_video_path, segment_kind):
    """Overlay golden wings bottom-right on every segment EXCEPT intro/outro.

    Intro and outro carry their own brand-design treatment (center-positioned
    logo, animation reserved for future variants). All other segments — Kling
    clips, raw footage, B-roll, Ken Burns stills — receive the corner watermark
    so brand presence is consistent throughout the content portion. When intro/
    outro are later upgraded with retracting-wings animations, this helper does
    not need to change."""

    if segment_kind in {"intro", "outro"}:
        shutil.copy(input_video_path, output_video_path)
        return

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_video_path),
        "-i", str(WATERMARK_PATH),
        "-filter_complex",
        "[1:v]scale=120:120[wm];[0:v][wm]overlay=W-w-12:H-h-12",
        "-c:a", "copy",
        str(output_video_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)


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
                               advance_status: bool = False,
                               key_prefix: str = ""):
    """Upload mp4 to r61/final/{VERSION_TAG}/{key_prefix}{key_name} and PATCH Airtable.

    `key_prefix` (default "") sits between the version dir and the filename
    in the R2 key — e.g. "captions/" lands the upload at
    r61/final/v3/captions/<key_name>. The Airtable attachment filename stays
    just `key_name` (no slash) so the UI download is clean.

    If advance_status is True, also set Video Status = "Stitched".
    Used by --all-voiceover-done batch (fresh pipeline progression). The
    older --all-approved-or-scheduled batch keeps status untouched because
    those records are re-renders of already-Scheduled finals.
    """
    r2_key = f"r61/final/{VERSION_TAG}/{key_prefix}{key_name}"
    public_url = upload_to_r2(mp4_path, r2_key, content_type="video/mp4")
    log(f"  uploaded → {public_url}")

    patch = {"Final Video": [{"url": public_url, "filename": key_name}]}
    if advance_status:
        patch[av.STATUS_FIELD] = av.STATUS_STITCHED
    av.update_record(record_id, patch)
    status_note = f"+status={av.STATUS_STITCHED}" if advance_status else "status untouched"
    log(f"  Airtable Final Video updated for {record_id} ({status_note})")
    return public_url


def _split_script_for_captions(script: str, max_chars: int = CAPTION_CHUNK_MAX_CHARS):
    """Break the German script into caption-line-sized chunks.

    Splits on sentence-ending punctuation first (. ! ? :), then re-splits any
    chunk longer than max_chars on commas, then on word boundaries. Output is
    plain UTF-8 text per chunk — ASS escaping happens at format time.
    """
    text = " ".join((script or "").split())
    if not text:
        return []
    sentences = re.split(r"(?<=[\.\!\?\:])\s+", text)
    chunks = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) <= max_chars:
            chunks.append(s)
            continue
        for piece in s.split(","):
            piece = piece.strip()
            if not piece:
                continue
            if len(piece) <= max_chars:
                chunks.append(piece)
                continue
            words, cur = piece.split(), ""
            for w in words:
                candidate = (cur + " " + w).strip() if cur else w
                if len(candidate) > max_chars and cur:
                    chunks.append(cur)
                    cur = w
                else:
                    cur = candidate
            if cur:
                chunks.append(cur)
    return chunks


def _ass_time(seconds: float) -> str:
    """ASS uses H:MM:SS.cs (centiseconds)."""
    if seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - h * 3600 - m * 60
    return f"{h}:{m:02d}:{int(s):02d}.{int(round((s - int(s)) * 100)):02d}"


def build_ass_subs(script: str, vo_start: float, vo_dur: float,
                   out_path: Path):
    """Write an ASS file with the German script chunked over [vo_start, vo_start+vo_dur].

    Caption style: white text, black 3px outline, bottom-third margin,
    centre-aligned, sans-serif. Chunks are distributed proportionally to
    their character length over the voiceover window.
    """
    chunks = _split_script_for_captions(script)
    if not chunks:
        log("  no caption chunks (empty script); skipping ASS build")
        return False

    total_chars = sum(max(1, len(c)) for c in chunks)
    events = []
    cursor = 0.0
    for c in chunks:
        share = max(1, len(c)) / total_chars
        chunk_dur = vo_dur * share
        start_s = vo_start + cursor
        end_s = vo_start + cursor + chunk_dur
        cursor += chunk_dur
        # ASS escapes — backslash and braces are special.
        safe = c.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        events.append(
            f"Dialogue: 0,{_ass_time(start_s)},{_ass_time(end_s)},Caption,,0,0,0,,{safe}"
        )

    # MarginV is from the bottom (PlayResY 1920 → bottom-third begins at ~640
    # from the bottom). Outline=3, BorderStyle=1 (outline+drop shadow), Alignment=2
    # (bottom-centre). Fontsize tuned for 1080-wide vertical.
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {TARGET_W}\n"
        f"PlayResY: {TARGET_H}\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Caption,Arial,68,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,"
        "1,0,0,0,100,100,0,0,1,3,0,2,60,60,260,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    log(f"  ASS subs written → {out_path.name} ({len(chunks)} chunks)")
    return True


def burn_captions(input_mp4: Path, ass_file: Path, output_mp4: Path):
    """Run ffmpeg to burn the ASS subs into a copy of the rendered mp4.

    The original input_mp4 is left untouched (SOUL.md rule 2/4 — never
    overwrite existing renders). Re-encodes video; copies audio.
    """
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    # ffmpeg's subtitles/ass filter needs the path in libavfilter syntax —
    # backslashes and colons (Windows drive letters) must be escaped.
    ass_str = str(ass_file).replace("\\", "/").replace(":", "\\:")
    argv = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(input_mp4),
        "-vf", f"ass='{ass_str}'",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "copy",
        str(output_mp4),
    ]
    proc = subprocess.run(argv, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError("burn_captions ffmpeg failed:\n" + (proc.stderr or "")[-2000:])
    log(f"  captions burned → {output_mp4.name}  "
        f"({output_mp4.stat().st_size/1e6:.1f} MB)")


def process_record(record, **kwargs):
    """Block 6 dispatcher. Pure routing — no legacy logic lives here.

    When R61_NARRATIVE_MODE is on AND the record carries a Voiceover Segments
    payload, route to the new 21s narrative pipeline. Otherwise fall through
    to the byte-identical legacy HyperFrames path (process_record_legacy).

    Kwargs are forwarded only to the legacy path (skip_publish, force_premix,
    advance_status, add_captions). stitch_narrative owns its own behavior and
    ignores them — see Block 6 spec.
    """
    fields = record.get("fields", {}) or {}
    if (os.environ.get("R61_NARRATIVE_MODE", "").lower() in ("1", "true", "yes")
            and (fields.get("Voiceover Segments") or "").strip()):
        return stitch_narrative(record)
    return process_record_legacy(record, **kwargs)


def process_record_legacy(record, skip_publish=False, force_premix=False,
                          advance_status=False, add_captions=False):
    """End-to-end v2 build for one Airtable record (HyperFrames path).

    Renamed from `process_record` in Block 6 — body unchanged. The 22 v3
    renders that shipped on 2026-05-15 came out of this exact code path.
    """
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

    # Block 3 opt-in side-features. Both are NO-OPs unless their env flag is
    # set, and they swallow their own exceptions — the v3 render must reach
    # R2/Airtable regardless of side-feature health.
    add_broll_injection(workdir, record)
    add_vfx_transitions(workdir)

    out_name = f"{index}_{clean_slug(ad_name)}.mp4"
    output_path = check_output_path(FINAL_DIR / out_name)
    if output_path.name != out_name:
        log(f"  version-incremented output → {output_path.name} "
            f"(original existed; preserving prior render per SOUL.md rule 2)")
        out_name = output_path.name
    run_hyperframes(workdir, output_path)

    # Optional captions burn-in. The captioned variant goes to a separate
    # path so the unsubtitled render is preserved per SOUL.md rule 2/4.
    publish_path = output_path
    publish_key_prefix = ""
    if add_captions:
        vo_script = fields.get("Voiceover Script") or ""
        ass_path = workdir / "captions.ass"
        captioned_name = output_path.stem + "_captions.mp4"
        captioned_path = check_output_path(CAPTIONS_DIR / captioned_name)
        # vo_start = end of intro = t_intro_end inside the composition; here
        # we recompute it from intro_dur (write_composition uses the same
        # value rounded to ms).
        if build_ass_subs(vo_script, vo_start=intro_dur,
                          vo_dur=audio_dur, out_path=ass_path):
            burn_captions(output_path, ass_path, captioned_path)
            publish_path = captioned_path
            publish_key_prefix = "captions/"
            log(f"  publishing captioned variant: {captioned_path.name}")
        else:
            log(f"  --add-captions set but no Voiceover Script text; "
                f"publishing uncaptioned render")

    if skip_publish:
        log(f"  --skip-publish set; not uploading or touching Airtable")
        return "rendered_only"

    public_url = publish_to_r2_and_airtable(rec_id, publish_path,
                                            publish_path.name,
                                            advance_status=advance_status,
                                            key_prefix=publish_key_prefix)

    # Block 4 — cross-platform variants. NO-OP unless R61_PLATFORMS is set.
    # Variants are rendered from `publish_path` (which is captioned if
    # add_captions was used; uncaptioned otherwise). Failures here NEVER
    # break the main publish.
    try:
        generate_platform_variants(publish_path, rec_id, VERSION_TAG)
    except Exception as e:
        log(f"  WARN generate_platform_variants raised: {e}")

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
    parser.add_argument("--add-captions", action="store_true",
                        default=ADD_CAPTIONS_DEFAULT,
                        help="After HyperFrames render, burn the Airtable "
                             "'Voiceover Script' field into the final mp4 as "
                             "white-on-black-outline ASS subtitles (bottom "
                             "third, DE). Captioned variant goes to "
                             "final/<tag>/captions/ and uploads to "
                             "r61/final/<tag>/captions/. Original render is "
                             "preserved. Default from R61_ADD_CAPTIONS env "
                             "var (1/true to enable).")
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
                                 advance_status=advance_status,
                                 add_captions=args.add_captions)
        except Exception as e:
            log(f"FAIL {r['id']}: {e}")
            res = "failed"
        summary[res] = summary.get(res, 0) + 1
    log(f"Run complete. Summary: {summary}")
    return 0 if summary.get("failed", 0) == 0 else 2


# =============================================================================
# Block 3 — Narrative Structure Layer (opt-in)
# Block 4 — Cross-Platform Format Adaptation (opt-in)
#
# All three functions below are PURE ADDITIONS. They never modify the existing
# stitch path unless their respective env flags are set:
#   R61_BROLL_ENABLED=true     → add_broll_injection() runs after write_composition
#   R61_VFX_ENABLED=true       → add_vfx_transitions() runs after write_composition
#   R61_PLATFORMS=tiktok,...   → generate_platform_variants() runs after publish
#
# Failure inside any of these is logged but NEVER raises into the calling
# pipeline — the v3 render must always reach R2/Airtable even if a side-feature
# misbehaves.
# =============================================================================

BROLL_R2_PREFIX = "r61/broll"
PLATFORM_FORMATS = {
    "instagram_feed":   {"w": 1080, "h": 1350, "crop": "center"},
    "instagram_reels":  {"w": 1080, "h": 1920, "crop": "none"},
    "tiktok":           {"w": 1080, "h": 1920, "crop": "none"},
    "facebook_feed":    {"w": 1080, "h": 1080, "crop": "center"},
    "facebook_stories": {"w": 1080, "h": 1920, "crop": "none"},
    "linkedin":         {"w": 1920, "h": 1080, "crop": "center"},
    "youtube_shorts":   {"w": 1080, "h": 1920, "crop": "none"},
    "youtube":          {"w": 1920, "h": 1080, "crop": "center"},
    "twitter":          {"w": 1920, "h": 1080, "crop": "center"},
    "pinterest":        {"w": 1000, "h": 1500, "crop": "center"},
}


def _r2_client():
    """Build a boto3 R2 client, mirroring tools/stitch.upload_to_r2 wiring."""
    import boto3
    from botocore.config import Config
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )


def _scenario_slug(ad_name):
    """Reduce 'Wohnzimmer Familie [Pillar Name]' → 'wohnzimmer_familie'."""
    base = (ad_name or "").split("[")[0]
    base = re.sub(r"[^\w\s-]", "", base, flags=re.UNICODE).strip().lower()
    base = re.sub(r"\s+", "_", base)
    return base or "default"


def _embed_texts(texts):
    """OpenAI text-embedding-3-small. Returns list of vectors aligned with input.

    Raises on hard API failure; caller catches and falls back.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY missing — needed for B-roll semantic match")
    resp = requests.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
        json={"model": "text-embedding-3-small", "input": texts},
        timeout=20,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI embeddings failed ({resp.status_code}): "
                           f"{resp.text[:200]}")
    return [d["embedding"] for d in resp.json()["data"]]


def _cosine(a, b):
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def add_broll_injection(workdir, record):
    """Pick best-matching B-roll clip from R2 r61/broll/{scenario}/ via embedding
    cosine, download it into workdir, splice it into index.html as a new scene
    between Hook (0-3s) and Problem (3-7s) — see write_composition timing.

    Idempotent: silent no-op if R61_BROLL_ENABLED is unset, if the R2 folder is
    missing/empty, or if no Voiceover Segments are present on the record (B-roll
    only makes sense in narrative mode). Never raises.
    """
    if os.environ.get("R61_BROLL_ENABLED", "").lower() not in ("1", "true", "yes"):
        return
    try:
        fields = record.get("fields", {}) or {}
        ad_name = fields.get("Ad Name") or ""
        segments_raw = fields.get("Voiceover Segments") or ""
        if not segments_raw.strip():
            log("  B-roll: no Voiceover Segments on record; skipping")
            return
        scenario = _scenario_slug(ad_name)
        bucket = os.environ["R2_BUCKET_NAME"]
        prefix = f"{BROLL_R2_PREFIX}/{scenario}/"
        client = _r2_client()
        listing = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        keys = [
            obj["Key"] for obj in listing.get("Contents", [])
            if obj["Key"].lower().endswith((".mp4", ".mov", ".webm"))
        ]
        if not keys:
            log(f"  B-roll: no clips at r2://{bucket}/{prefix}; skipping")
            return
        filenames = [k.rsplit("/", 1)[-1] for k in keys]
        embed_inputs = [ad_name] + filenames
        try:
            vecs = _embed_texts(embed_inputs)
        except Exception as e:
            log(f"  B-roll: embed failed ({e}); falling back to first clip")
            best_idx = 0
        else:
            ad_vec = vecs[0]
            scores = [_cosine(ad_vec, v) for v in vecs[1:]]
            best_idx = max(range(len(scores)), key=lambda i: scores[i])
            log(f"  B-roll: top match {filenames[best_idx]!r} "
                f"(cos={scores[best_idx]:.3f})")
        winner_key = keys[best_idx]
        local_path = workdir / "broll.mp4"
        client.download_file(bucket, winner_key, str(local_path))

        html_path = workdir / "index.html"
        html = html_path.read_text(encoding="utf-8")
        # Splice a new <video> between Scene 1 (intro) and Scene 2 (clip).
        # The HyperFrames composition uses absolute data-start timestamps;
        # we layer the B-roll over the 3-7s window (problem beat). It plays
        # muted (mixed audio carries the VO) and is composited on top.
        broll_tag = (
            '    <!-- B-roll injection (R61_BROLL_ENABLED) -->\n'
            '    <video id="v-broll" data-start="3.000" data-duration="4.000" '
            'data-track-index="2" src="broll.mp4" muted playsinline '
            'style="opacity: 0.92;"></video>\n'
        )
        marker = '    <!-- Scene 2a: Clip'
        if marker in html and broll_tag not in html:
            html = html.replace(marker, broll_tag + marker, 1)
            html_path.write_text(html, encoding="utf-8")
            log(f"  B-roll: injected {winner_key} as 3-7s overlay")
        else:
            log("  B-roll: HTML marker not found or already injected; skipped splice")
    except Exception as e:
        log(f"  WARN add_broll_injection failed: {e}")


def add_vfx_transitions(workdir):
    """Inject a 100ms CSS opacity crossfade at every scene boundary in
    index.html. Pure CSS — no JS, no HyperFrames API dependency. Idempotent.

    Falls back silently if index.html is missing. Never raises.
    """
    if os.environ.get("R61_VFX_ENABLED", "").lower() not in ("1", "true", "yes"):
        return
    try:
        html_path = workdir / "index.html"
        if not html_path.exists():
            return
        html = html_path.read_text(encoding="utf-8")
        if "hf-crossfade" in html:
            return  # already injected on a prior call
        css_inject = (
            "    .hf-crossfade { animation: hf-crossfade 0.1s ease-out; }\n"
            "    @keyframes hf-crossfade { from { opacity: 0; } to { opacity: 1; } }\n"
        )
        if "</style>" in html:
            html = html.replace("</style>", css_inject + "  </style>", 1)
        # Apply class to every <video> tag in the composition.
        html = re.sub(
            r"<video ((?:(?!class=)[^>])*?)>",
            r'<video class="hf-crossfade" \1>',
            html,
        )
        html_path.write_text(html, encoding="utf-8")
        log("  VFX: injected 100ms crossfade on scene videos")
    except Exception as e:
        log(f"  WARN add_vfx_transitions failed: {e}")


def generate_platform_variants(source_mp4, rec_id, version_tag):
    """Block 4 — produce per-platform crops/scales from the master render, upload
    each to R2 at r61/final/{tag}/platforms/{platform}/{name}, write a JSON map
    of {platform: url} to Airtable's `Platform Variants` field.

    Triggered by R61_PLATFORMS env (comma-separated, e.g.
    'tiktok,instagram_reels,linkedin'). Unset/empty → silent no-op. Per-platform
    failure logged; other platforms still proceed. Never raises into caller.
    """
    platforms_env = os.environ.get("R61_PLATFORMS", "")
    if not platforms_env.strip():
        return {}
    targets = [p.strip() for p in platforms_env.split(",") if p.strip()]
    if not targets:
        return {}
    log(f"  platform variants: {targets}")

    from tools.stitch import upload_to_r2  # re-use R2 helper
    out_root = source_mp4.parent / "platforms"
    out_root.mkdir(parents=True, exist_ok=True)
    variants = {}
    base_stem = source_mp4.stem

    for platform in targets:
        spec = PLATFORM_FORMATS.get(platform)
        if not spec:
            log(f"    unknown platform '{platform}'; skipping")
            continue
        try:
            target_w, target_h = spec["w"], spec["h"]
            out_dir = out_root / platform
            out_dir.mkdir(parents=True, exist_ok=True)
            out_name = f"{base_stem}_{platform}.mp4"
            out_path = check_output_path(out_dir / out_name)
            if spec["crop"] == "none":
                # Master is 1080x1920 9:16 — just copy/transcode if dims match.
                vf = f"scale={target_w}:{target_h}"
            else:
                # Center crop to target aspect, then scale to exact dims.
                # Pick the larger of (sw/tw, sh/th) so cropped region covers
                # the target aspect, then scale.
                vf = (
                    f"crop=if(gt(a\\,{target_w}/{target_h})\\,"
                    f"ih*{target_w}/{target_h}\\,iw):"
                    f"if(gt(a\\,{target_w}/{target_h})\\,ih\\,iw*{target_h}/{target_w}),"
                    f"scale={target_w}:{target_h}"
                )
            argv = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(source_mp4),
                "-vf", vf,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-c:a", "copy",
                str(out_path),
            ]
            proc = subprocess.run(argv, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
            if proc.returncode != 0:
                log(f"    {platform}: ffmpeg failed: "
                    f"{(proc.stderr or '')[-300:]}")
                continue
            r2_key = f"r61/final/{version_tag}/platforms/{platform}/{out_path.name}"
            url = upload_to_r2(out_path, r2_key, content_type="video/mp4")
            variants[platform] = url
            log(f"    {platform}: {target_w}x{target_h} -> {url}")
        except Exception as e:
            log(f"    {platform}: failed ({e})")

    if variants:
        try:
            av.update_record(rec_id, {
                "Platform Variants": json.dumps(variants, indent=2),
            })
            log(f"  platform variants: wrote {len(variants)} URLs to Airtable")
        except Exception as e:
            log(f"  WARN Airtable Platform Variants write failed: {e}")
    return variants


# =============================================================================
# Block 6 — Narrative stitcher (R61_NARRATIVE_MODE)
#
# 21s composition built as a direct FFmpeg pipeline (NOT HyperFrames). Visual
# track is 6 segments concatenated via concat filter; audio is voiceover at 0 dB
# throughout + (optional) raw-clip audio at -6 dB during voice-silent sub-windows
# of [10,16]. Captions, if enabled, are burned from forced-alignment word
# timestamps in a separate post-pass.
#
# Architectural change vs the existing pipeline: the `raw_or_kling` segment IS
# the new B-roll mechanism — a first-class composition slot, not a bolt-on. The
# old R61_BROLL_ENABLED / R61_VFX_ENABLED side-features only run in the legacy
# HyperFrames path (process_record_legacy); narrative mode skips them and logs
# a note at start.
# =============================================================================

NARRATIVE_TIMELINE = [
    # Block 11 layout — every content beat is a real generated clip.
    # kind         start  end
    ("kling_hook",   0,   3),
    ("intro",        3,   5),
    ("problem",      5,  10),
    ("lösung",      10,  15),
    ("cta",         15,  19),
    ("outro",       19,  21),
]
NARRATIVE_TOTAL_S = 21
# Block 11: voiced window now ends at 19s (cta beat 15-19 is voiced;
# 19-21 outro is hard-muted). Audio mute windows below MUST stay in sync
# with the skip_windows passed to build_ass_subs_from_alignment from
# stitch_narrative.
NARRATIVE_VOICE_END_S = 19
NARRATIVE_MUTE_WINDOWS = [(3.0, 5.0), (19.0, 21.0)]
NARRATIVE_FPS = 25


def _ff(cmd, label="ffmpeg"):
    """Run ffmpeg, raise RuntimeError with the stderr tail on failure."""
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = (proc.stderr or "")[-2000:]
        raise RuntimeError(f"{label} failed (exit {proc.returncode}):\n{tail}")
    return proc


def apply_ken_burns(image_path: Path, output_path: Path, duration: float,
                    direction: str = "in", zoom_to: float = 1.15):
    """Render a Ken Burns clip from a still image at TARGET_W×TARGET_H.

    Direction:
      "in"    — center zoom 1.0 → zoom_to, no pan
      "right" — center zoom + x pans right by 5% of input width
      "left"  — center zoom + x pans left by 5% of input width

    Input image is upscaled 2× before zoompan to avoid resampling artifacts at
    the maximum zoom. Output is silent (no audio stream).
    """
    if duration <= 0:
        raise ValueError(f"apply_ken_burns: duration must be > 0, got {duration}")
    fps = NARRATIVE_FPS
    total_frames = max(1, int(round(duration * fps)))
    zinc = (zoom_to - 1.0) / max(1, total_frames - 1)
    z_expr = f"min(zoom+{zinc:.5f},{zoom_to})"
    if direction == "in":
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif direction == "right":
        x_expr = f"iw/2-(iw/zoom/2)+iw*0.05*on/{max(1, total_frames - 1)}"
        y_expr = "ih/2-(ih/zoom/2)"
    elif direction == "left":
        x_expr = f"iw/2-(iw/zoom/2)-iw*0.05*on/{max(1, total_frames - 1)}"
        y_expr = "ih/2-(ih/zoom/2)"
    else:
        raise ValueError(f"apply_ken_burns: unknown direction {direction!r}")
    vf = (
        f"scale={TARGET_W * 2}:{TARGET_H * 2}:force_original_aspect_ratio=increase,"
        f"crop={TARGET_W * 2}:{TARGET_H * 2},"
        f"zoompan=z='{z_expr}':d={total_frames}:s={TARGET_W}x{TARGET_H}:fps={fps}:"
        f"x='{x_expr}':y='{y_expr}'"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(image_path),
        "-vf", vf,
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-r", str(fps),
        "-an",
        str(output_path),
    ]
    _ff(cmd, label=f"ken_burns({direction},{duration:.1f}s)")


def _trim_clip(src: Path, start: float, dur: float, out: Path):
    """Trim a video to [start, start+dur], scale-and-crop to TARGET_W×TARGET_H,
    re-encode to libx264/yuv420p/25fps, drop audio."""
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{start:.3f}", "-i", str(src),
        "-t", f"{dur:.3f}",
        "-vf", f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase,"
               f"crop={TARGET_W}:{TARGET_H}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-r", str(NARRATIVE_FPS), "-an",
        str(out),
    ]
    _ff(cmd, label=f"trim_clip(start={start},dur={dur})")


def _trim_static(src: Path, dur: float, out: Path):
    """Trim a video to exactly dur seconds starting at 0; normalize like _trim_clip."""
    _trim_clip(src, 0.0, dur, out)


def _concat_segments_via_filter(segment_paths, out_path):
    """Concatenate using the concat FILTER (decodes + re-encodes) so segments
    don't have to be byte-identical at the codec level — much more reliable
    than the demuxer when segments come from heterogeneous sources."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    inputs = []
    for p in segment_paths:
        inputs.extend(["-i", str(p)])
    n = len(segment_paths)
    filter_str = "".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[outv]"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[outv]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-r", str(NARRATIVE_FPS),
        str(out_path),
    ]
    _ff(cmd, label=f"concat_segments(n={n})")


def _compute_voice_speaking_intervals(alignment_json, merge_gap_s: float = 0.20):
    """Collapse the per-word alignment into contiguous speaking intervals.

    Adjacent words with gaps < merge_gap_s are merged into one interval. Returns
    a list of (start, end) tuples in seconds. Empty list if alignment is missing,
    failed, or contains no non-whitespace words.
    """
    if not alignment_json:
        return []
    try:
        data = (json.loads(alignment_json) if isinstance(alignment_json, str)
                else alignment_json)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(data, dict) or data.get("alignment_failed"):
        return []
    words = data.get("words") or []
    intervals = []
    cur_start = cur_end = None
    for w in words:
        if not (w.get("text") or "").strip():
            continue
        s = float(w.get("start", 0))
        e = float(w.get("end", s))
        if cur_start is None:
            cur_start, cur_end = s, e
            continue
        if s - cur_end < merge_gap_s:
            cur_end = max(cur_end, e)
        else:
            intervals.append((cur_start, cur_end))
            cur_start, cur_end = s, e
    if cur_start is not None:
        intervals.append((cur_start, cur_end))
    return intervals


def build_ass_subs_from_alignment(alignment_json, out_path: Path,
                                  window=(0.0, NARRATIVE_VOICE_END_S),
                                  mode: str = "word_by_word",
                                  skip_windows=None,
                                  beats=None):
    """Word-by-word ASS captions sourced from forced-alignment timestamps.

    Each non-whitespace word displays from its alignment.start until the next
    word's start (or its own end + 100 ms for the final word), clamped to
    `window` (defaults to the voiced 0–19s region in Block 11 mode).

    `skip_windows` is an optional list of (start, end) ranges; any word whose
    `start` falls within a skip window is dropped entirely (used by Block 11
    to keep captions silent during the 3-5s intro and 19-21s outro segments —
    matches the voiceover mute windows in stitch_narrative).

    Highlight heuristic — the longest word inside each narrative beat slot is
    recolored Provinzial Flügelgelb (#F5C518). `beats` is an optional list of
    (start, end) tuples; defaults to Block 11's voiced beats
    [(0,3), (5,10), (10,15), (15,19)].
    ASS uses BGR ordering, so the override tag is &H18C5F5&.

    Caption style: Inter Bold ~52px, white text with a 3px black outline,
    bottom-centered with MarginV=120 to keep captions inside the brand-safe
    bottom-third. Returns True if at least one event was written.
    """
    if mode != "word_by_word":
        raise NotImplementedError(f"build_ass_subs_from_alignment: mode={mode!r}")
    if not alignment_json:
        log("  captions: no alignment payload; skipping")
        return False
    try:
        data = (json.loads(alignment_json) if isinstance(alignment_json, str)
                else alignment_json)
    except json.JSONDecodeError:
        log("  captions: alignment JSON unparseable; skipping")
        return False
    if data.get("alignment_failed"):
        log("  captions: alignment_failed in payload; skipping")
        return False
    words = [w for w in (data.get("words") or [])
             if (w.get("text") or "").strip()]
    if not words:
        log("  captions: no non-whitespace words; skipping")
        return False

    win_start, win_end = window

    if skip_windows is None:
        skip_windows = []

    def _in_skip(t):
        return any(a <= t < b for a, b in skip_windows)

    if beats is None:
        # Block 11 voiced beat layout (0-3 hook, 5-10 problem, 10-15 lösung, 15-19 cta).
        beats = [(0, 3), (5, 10), (10, 15), (15, 19)]
    highlight = set()
    for bs, be in beats:
        in_beat = [(i, w) for i, w in enumerate(words)
                   if bs <= float(w.get("start", 0)) < be
                   and not _in_skip(float(w.get("start", 0)))]
        if in_beat:
            highlight.add(max(in_beat, key=lambda iw: len(iw[1]["text"].strip()))[0])

    events = []
    skipped_count = 0
    for i, w in enumerate(words):
        s = float(w["start"])
        e = float(w["end"])
        if s >= win_end or e <= win_start:
            continue
        if _in_skip(s):
            skipped_count += 1
            continue
        next_s = float(words[i + 1]["start"]) if i + 1 < len(words) else e + 0.1
        disp_start = max(s, win_start)
        disp_end = min(next_s, win_end)
        # Truncate display so a word never bleeds into a skip window
        for a, b in skip_windows:
            if disp_start < a <= disp_end:
                disp_end = a
                break
        if disp_end <= disp_start:
            continue
        raw = (w["text"] or "").strip()
        safe = raw.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        if i in highlight:
            safe = f"{{\\c&H18C5F5&}}{safe}{{\\c&HFFFFFF&}}"
        events.append(
            f"Dialogue: 0,{_ass_time(disp_start)},{_ass_time(disp_end)},"
            f"Caption,,0,0,0,,{safe}"
        )

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {TARGET_W}\n"
        f"PlayResY: {TARGET_H}\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Caption,Inter,52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,"
        "1,0,0,0,100,100,0,0,1,3,0,2,60,60,120,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    log(f"  captions ASS (alignment) → {out_path.name} ({len(events)} words, "
        f"{len(highlight)} highlighted, {skipped_count} skipped via skip_windows)")
    return True


def stitch_narrative(record):
    """R61 Block 11 — 21s narrative composition with four distinct generated clips.

    Timeline (every content beat is real generated motion — no Ken Burns):
      0-3   hook    → Hook Clip[0:3]     (fallback: Video Clip[0:3])
      3-5   intro   → intro.mp4 (2s pass-through)
      5-10  problem → Problem Clip[0:5]  (fallback: Video Clip[0:5])
      10-15 lösung  → Lösung Clip[0:5]   (REQUIRED, full 5s, no hold extension)
      15-19 cta     → CTA Clip[0:4]      (REQUIRED; Kling gens 5s, trimmed)
      19-21 outro   → outro.mp4 (2s pass-through)

    Audio:
      voice  — voiceover padded to 21s, muted in [3,5) (intro) and [19,21] (outro).
               Words at those times are dropped — captions skip them too so the
               viewer never sees a word render against muted audio.
      raw    — DROPPED in Block 11. The raw 6s slot no longer exists.
      music  — still TODO (Fal Lyria as follow-up if Gate 4 review flags).

    Captions (R61_ADD_CAPTIONS=1):
      build_ass_subs_from_alignment with mode="word_by_word" and
      skip_windows=NARRATIVE_MUTE_WINDOWS. Highlight beats sit on
      [(0,3), (5,10), (10,15), (15,19)] — the four voiced segments.

    Side-features NOT run in narrative mode:
      add_broll_injection — superseded by the four-clip composition.
      add_vfx_transitions — HTML/HyperFrames-only; doesn't apply here.
      generate_platform_variants — invoked separately after stitch_narrative.

    Skip conditions (returns "skipped_*" instead of "ok"):
      - Voiceover Segments unparseable / empty
      - Missing Voiceover Audio / First Frame / Last Frame / Video Clip
      - Missing Lösung Clip or CTA Clip (Block 11 hard requirement)

    Output:
      r61/final/{VERSION_TAG}/{scenario_id}_{YYYYMMDD-HHMMSS}.mp4 on R2.
      Airtable "Final Video" attachment filename = {scenario_id}.mp4 (clean).
      Video Status → "Stitched". Gate 4 entry written to shared/gates/pending.json.
    """
    rec_id = record["id"]
    fields = record.get("fields", {}) or {}
    ad_name = fields.get("Ad Name") or "(no name)"
    index = fields.get("Index")
    scenario_id = (fields.get("Scenario ID") or rec_id).strip() or rec_id
    log(f"START narrative {rec_id}  Index={index}  scenario={scenario_id}  "
        f"'{ad_name}'  version={VERSION_TAG}")
    log(f"  R61_BROLL_ENABLED / R61_VFX_ENABLED skipped in narrative mode — "
        f"raw_or_kling segment is the first-class composition slot.")

    seg_raw = fields.get("Voiceover Segments") or ""
    aln_raw = fields.get("Voiceover Alignment JSON") or ""
    try:
        segments_meta = json.loads(seg_raw) if seg_raw.strip() else []
    except json.JSONDecodeError:
        log(f"  SKIP — Voiceover Segments JSON unparseable")
        return "skipped_bad_segments"
    if not segments_meta:
        log(f"  SKIP — Voiceover Segments empty")
        return "skipped_no_segments"
    log(f"  voiceover segments: {[s.get('name') for s in segments_meta]}")

    clip_url = attachment_url(record, "Video Clip")
    vo_url = attachment_url(record, "Voiceover Audio")
    first_url = attachment_url(record, "First Frame Image")
    last_url = attachment_url(record, "Last Frame Image")
    missing_inputs = [n for n, u in [
        ("Video Clip", clip_url), ("Voiceover Audio", vo_url),
        ("First Frame Image", first_url), ("Last Frame Image", last_url),
    ] if not u]
    if missing_inputs:
        log(f"  SKIP — missing attachments: {missing_inputs}")
        return "skipped_missing_inputs"

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    work = TMP_DIR / f"narrative_{rec_id}"
    work.mkdir(parents=True, exist_ok=True)

    clip_local = work / f"clip{ext_from_url(clip_url, '.mp4')}"
    vo_local = work / f"vo{ext_from_url(vo_url, '.mp3')}"
    first_local = work / f"first{ext_from_url(first_url, '.png')}"
    last_local = work / f"last{ext_from_url(last_url, '.png')}"
    for url, dst in [(clip_url, clip_local), (vo_url, vo_local),
                     (first_url, first_local), (last_url, last_local)]:
        if not dst.exists():
            download_attachment(url, dst)
    log(f"  inputs downloaded → {work.name}/")

    # Block 11: raw footage no longer participates in the visual composition —
    # the Lösung Clip occupies the 10-15s slot end-to-end. Kept as False for
    # the gate entry's diagnostic fields.
    raw_available = False
    raw_has_audio = False

    # Block 11: four dedicated beat clips (Hook / Problem / Lösung / CTA).
    # apply_ken_burns is no longer invoked — every content beat needs its own
    # real generated motion. Hook + Problem fall back to Video Clip slices for
    # back-compat on pre-Block-11 records; Lösung and CTA are required.
    hook_clip_url    = attachment_url(record, "Hook Clip")
    problem_clip_url = attachment_url(record, "Problem Clip")
    loesung_clip_url = attachment_url(record, "Lösung Clip")
    cta_clip_url     = attachment_url(record, "CTA Clip")

    def _fetch_beat_clip(url, label):
        if not url:
            return None
        local = work / f"{label}_clip{ext_from_url(url, '.mp4')}"
        if not local.exists():
            download_attachment(url, local)
        log(f"  {label} Clip available → {local.name} "
            f"({local.stat().st_size / 1e6:.1f} MB)")
        return local

    hook_clip_local    = _fetch_beat_clip(hook_clip_url, "hook")
    problem_clip_local = _fetch_beat_clip(problem_clip_url, "problem")
    loesung_clip_local = _fetch_beat_clip(loesung_clip_url, "loesung")
    cta_clip_local     = _fetch_beat_clip(cta_clip_url, "cta")

    if not hook_clip_local:
        log(f"  no Hook Clip attachment — falls back to Video Clip[0:3]")
    if not problem_clip_local:
        log(f"  no Problem Clip attachment — falls back to Video Clip[0:5]")
    if not loesung_clip_local:
        log(f"  SKIP — Block 11 requires Lösung Clip; missing for {rec_id}")
        return "skipped_missing_loesung_clip"
    if not cta_clip_local:
        log(f"  SKIP — Block 11 requires CTA Clip; missing for {rec_id}")
        return "skipped_missing_cta_clip"

    # --- Build visual segments (audio stripped on all) ---
    # Block 11 timeline (21s total, every content beat is a real generated clip):
    #   0-3   hook    → Hook Clip[0:3]    (fallback: Video Clip[0:3])
    #   3-5   intro   → intro.mp4 (2s)
    #   5-10  problem → Problem Clip[0:5] (fallback: Video Clip[0:5])
    #   10-15 lösung  → Lösung Clip[0:5]  (full 5s, no Ken Burns extension)
    #   15-19 cta     → CTA Clip[0:4]     (Kling generated at 5s, trimmed to 4s)
    #   19-21 outro   → outro.mp4 (2s)
    seg_dir = work / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    segment_paths = []  # ordered list fed to concat

    # hook 0-3s
    p_hook_raw = seg_dir / "01_hook_raw.mp4"
    p_hook = seg_dir / "01_hook.mp4"
    if hook_clip_local:
        _trim_clip(hook_clip_local, 0.0, 3.0, p_hook_raw)
        log(f"  hook segment from Hook Clip (3s)")
    else:
        _trim_clip(clip_local, 0.0, 3.0, p_hook_raw)
        log(f"  hook segment from Video Clip[0:3] (fallback)")
    apply_watermark(p_hook_raw, p_hook, "kling_hook")
    segment_paths.append(p_hook)

    # intro 3-5s (pass-through)
    p_intro_raw = seg_dir / "02_intro_raw.mp4"
    p_intro = seg_dir / "02_intro.mp4"
    _trim_static(INTRO_PATH, 2.0, p_intro_raw)
    apply_watermark(p_intro_raw, p_intro, "intro")
    segment_paths.append(p_intro)

    # problem 5-10s
    p_problem_raw = seg_dir / "03_problem_raw.mp4"
    p_problem = seg_dir / "03_problem.mp4"
    if problem_clip_local:
        _trim_clip(problem_clip_local, 0.0, 5.0, p_problem_raw)
        log(f"  problem segment from Problem Clip (5s)")
    else:
        _trim_clip(clip_local, 0.0, 5.0, p_problem_raw)
        log(f"  problem segment from Video Clip[0:5] (fallback)")
    apply_watermark(p_problem_raw, p_problem, "problem")
    segment_paths.append(p_problem)

    # lösung 10-15s — full 5s of real motion (no Ken Burns hold extension)
    p_loesung_raw = seg_dir / "04_loesung_raw.mp4"
    p_loesung = seg_dir / "04_loesung.mp4"
    _trim_clip(loesung_clip_local, 0.0, 5.0, p_loesung_raw)
    apply_watermark(p_loesung_raw, p_loesung, "lösung")
    segment_paths.append(p_loesung)
    log(f"  lösung segment from Lösung Clip (5s, no hold extension)")

    # cta 15-19s — Kling generated at 5s, trim trailing 1s to fit slot
    p_cta_raw = seg_dir / "05_cta_raw.mp4"
    p_cta = seg_dir / "05_cta.mp4"
    _trim_clip(cta_clip_local, 0.0, 4.0, p_cta_raw)
    apply_watermark(p_cta_raw, p_cta, "cta")
    segment_paths.append(p_cta)
    log(f"  cta segment from CTA Clip (4s, trimmed from 5s gen)")

    # outro 19-21s (pass-through)
    p_outro_raw = seg_dir / "06_outro_raw.mp4"
    p_outro = seg_dir / "06_outro.mp4"
    _trim_static(OUTRO_PATH, 2.0, p_outro_raw)
    apply_watermark(p_outro_raw, p_outro, "outro")
    segment_paths.append(p_outro)

    visual_track = work / "video_track.mp4"
    _concat_segments_via_filter(segment_paths, visual_track)
    log(f"  visual track concatenated → {visual_track.name} "
        f"({visual_track.stat().st_size / 1e6:.1f} MB)")

    # --- Audio mix ---
    audio_dir = work / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    voice_intervals = _compute_voice_speaking_intervals(aln_raw)
    voice_end = voice_intervals[-1][1] if voice_intervals else 0.0
    log(f"  voice activity: {len(voice_intervals)} interval(s), ends at "
        f"{voice_end:.3f}s (alignment {'ok' if voice_intervals else 'missing'})")

    # Block 11.3: mute the voiceover in [3,5) (intro slot) and [19,21] (outro slot).
    # Words scheduled at those times in the source vo file are dropped — captions
    # apply the same skip windows (Block 11.4) so the muted regions stay silent
    # but never look broken on screen.
    mute_windows = NARRATIVE_MUTE_WINDOWS
    mute_expr = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in mute_windows)
    mixed_audio = work / "mixed_audio.aac"
    _ff([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(vo_local),
        "-af",
        f"apad=whole_dur={NARRATIVE_TOTAL_S},"
        f"aresample={TARGET_SR},"
        f"volume=enable='{mute_expr}':volume=0:eval=frame",
        "-t", f"{NARRATIVE_TOTAL_S}",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(TARGET_SR),
        str(mixed_audio),
    ], label="audio_mix(voice_with_mute_windows)")
    log(f"  audio mix: voice with mute windows {mute_windows} — "
        f"intro/outro tone deferred to a follow-up (Block 11.3 fallback to silence).")

    # --- Mux video + audio ---
    base_mp4 = work / f"{scenario_id}_base.mp4"
    _ff([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(visual_track),
        "-i", str(mixed_audio),
        "-c:v", "copy", "-c:a", "copy",
        "-shortest",
        str(base_mp4),
    ], label="mux")
    log(f"  muxed → {base_mp4.name} ({base_mp4.stat().st_size / 1e6:.1f} MB)")

    # --- Optional caption burn-in ---
    final_mp4 = base_mp4
    add_captions = os.environ.get("R61_ADD_CAPTIONS", "").lower() in ("1", "true", "yes")
    if add_captions:
        ass_path = work / "captions.ass"
        captioned = work / f"{scenario_id}_captioned.mp4"
        if build_ass_subs_from_alignment(aln_raw, ass_path,
                                         skip_windows=NARRATIVE_MUTE_WINDOWS):
            burn_captions(base_mp4, ass_path, captioned)
            final_mp4 = captioned
        else:
            log(f"  R61_ADD_CAPTIONS=1 but alignment unusable; publishing uncaptioned")

    # --- Upload + Airtable ---
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    r2_key = f"r61/final/{VERSION_TAG}/{scenario_id}_{ts}.mp4"
    public_url = upload_to_r2(final_mp4, r2_key, content_type="video/mp4")
    log(f"  uploaded → {public_url}")

    av.update_record(rec_id, {
        "Final Video": [{"url": public_url, "filename": f"{scenario_id}.mp4"}],
        av.STATUS_FIELD: av.STATUS_STITCHED,
    })
    log(f"  Airtable Final Video updated for {rec_id} (status=Stitched)")

    try:
        _gates.append_gate(
            gate_number=4, gate_name="stitch_final_preview",
            record_id=rec_id, ad_name=ad_name,
            video_url=public_url,
            extra={
                "local_path": str(final_mp4),
                "index": index,
                "scenario_id": scenario_id,
                "mode": "narrative_v5_block11",
                "captions": add_captions,
                "raw_available": raw_available,
                "raw_has_audio": raw_has_audio,
                "voice_end_s": round(voice_end, 3),
                "next_step": "Watch narrative preview. Approve to Blotato-schedule, or request redo.",
            },
        )
        log(f"Gate entry written → shared/gates/pending.json ({rec_id}, Gate 4).")
    except Exception as e:
        log(f"WARN: gate write failed: {e}")

    log(f"DONE narrative {rec_id} → {public_url}")
    return "ok"


if __name__ == "__main__":
    raise SystemExit(main())
