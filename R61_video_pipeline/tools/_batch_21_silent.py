"""
21-record silent batch runner (private helper, single-purpose).

Runs frame_gen + video_gen on Day 08-28 Schaden v1 R61 records, sequential,
with cost-cap halt at $14 cumulative. Skips hf_stitch entirely; the
deliverable is the Video Clip attachment (5s raw, watermarked).

Writes progress to:
  shared/memory/batch_logs/silent_21_progress.json
  shared/memory/batch_logs/silent_21_stdout.log
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import time
import datetime as dt
from pathlib import Path

REPO_ROOT = Path(r"C:\CONTENT_PIPELINE")
R61_DIR = REPO_ROOT / "R61_video_pipeline"

# Day 20-25 already complete. Day 26 frames done but video failed on HTTP 502.
# Resuming for Day 26 (video only) + Day 27-31 (full).
PRIOR_CREDITS_USED = 86  # Day 20 (10) + Day 21-25 (50) + Day 26 video (6) + Day 27 (10) + Day 28 first-frame attempted (2) + Day 28 stuck frame retry budget (8)
CREDIT_CAP = 200
PER_RECORD_FRAME_CREDITS = 4
PER_RECORD_VIDEO_CREDITS = 6

# Records with "skip_frame": True only run video_gen (frames already produced).
R61_TARGETS = [
    (28, "recOkHcLc6RSqjzed", "hund-beisst-brieftraeger", {}),
    (29, "recc01n1tMzC9aiHv", "glas-umgekippt-restaurant", {}),
    (30, "recZ5AxNrEnYPHexW", "beim-umzug-moebel", {}),
    (31, "recuu2pTCKRlHM0uR", "schluessel-verloren", {}),
]

LOG_DIR = REPO_ROOT / "shared" / "memory" / "batch_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_PATH = LOG_DIR / "silent_resume_progress.json"
STDOUT_LOG = LOG_DIR / "silent_resume_stdout.log"

os.environ["PATH"] = r"C:\Users\benja\bin;" + os.environ.get("PATH", "")
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["R61_NARRATIVE_MODE"] = "false"
# Provider switch (Fal balance exhausted — route through Higgsfield).
os.environ["R61_FRAME_PROVIDER"] = "higgsfield"
os.environ["R61_VIDEO_MODEL"] = "veo3_1_lite"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def log(msg):
    line = f"[{dt.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with open(STDOUT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def write_progress(state):
    PROGRESS_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _run_stage_once(stage_name, argv, timeout_s):
    t0 = time.time()
    try:
        proc = subprocess.run(
            argv, cwd=str(R61_DIR), capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=timeout_s,
        )
        return {
            "stage": stage_name,
            "exit_code": proc.returncode,
            "wall_s": time.time() - t0,
            "stdout_tail": (proc.stdout or "")[-4000:],
            "stderr_tail": (proc.stderr or "")[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {
            "stage": stage_name,
            "exit_code": -1,
            "wall_s": time.time() - t0,
            "error": "timeout",
        }
    except Exception as e:
        return {
            "stage": stage_name,
            "exit_code": -2,
            "wall_s": time.time() - t0,
            "error": str(e)[:400],
        }


# Patterns that indicate a transient Higgsfield infra hiccup — worth retrying.
TRANSIENT_PATTERNS = (
    "Cannot reach https://fnf.higgsfield.ai",
    "HTTP 502",
    "HTTP 503",
    "HTTP 504",
    "Connection reset",
    "Connection aborted",
    "TLS handshake",
)


def _is_transient(result):
    blob = (result.get("stdout_tail", "") + result.get("stderr_tail", "")
            + str(result.get("error", "")))
    return any(pat in blob for pat in TRANSIENT_PATTERNS)


def run_stage(stage_name, argv, timeout_s, max_retries=2, retry_delay_s=45):
    """Run a stage with retry on transient Higgsfield API errors."""
    result = _run_stage_once(stage_name, argv, timeout_s)
    attempt = 0
    while result["exit_code"] != 0 and attempt < max_retries and _is_transient(result):
        attempt += 1
        log(f"  TRANSIENT {stage_name} (attempt {attempt}/{max_retries}); "
            f"sleeping {retry_delay_s}s before retry")
        time.sleep(retry_delay_s)
        result = _run_stage_once(stage_name, argv, timeout_s)
        result["retry_attempt"] = attempt
    return result


def main():
    state = {
        "start_ts": dt.datetime.now().isoformat(timespec="seconds"),
        "prior_credits_used": PRIOR_CREDITS_USED,
        "credit_cap": CREDIT_CAP,
        "targets": len(R61_TARGETS),
        "provider": "higgsfield (nano_banana_2 + veo3_1_lite)",
        "records": [],
        "cumulative_credits_used": PRIOR_CREDITS_USED,
        "status": "running",
        "halt_reason": None,
    }
    write_progress(state)
    log("=== Resume batch: Day 21-31 via Higgsfield (Veo Lite 6s) ===")
    log(f"Prior credits used this session: {PRIOR_CREDITS_USED}")
    log(f"Targets: {len(R61_TARGETS)} records (Day 21-31)")

    for idx, target in enumerate(R61_TARGETS, 1):
        if len(target) == 4:
            day, rid, slug, opts = target
        else:
            day, rid, slug = target
            opts = {}
        skip_frame = opts.get("skip_frame", False)
        log(f"--- [{idx}/{len(R61_TARGETS)}] Day {day:02d} | {rid} | {slug}"
            f"{' (frame skipped)' if skip_frame else ''} ---")
        rec_t0 = time.time()
        rec_entry = {
            "idx": idx, "day": day, "record_id": rid, "slug": slug,
            "start_ts": dt.datetime.now().isoformat(timespec="seconds"),
            "stages": [],
        }

        will_use_frame = 0 if skip_frame else PER_RECORD_FRAME_CREDITS
        projected_after = (
            state["cumulative_credits_used"]
            + will_use_frame + PER_RECORD_VIDEO_CREDITS
        )
        if projected_after > CREDIT_CAP:
            state["status"] = "halted_credit_cap"
            state["halt_reason"] = (
                f"Projected {projected_after} credits > cap {CREDIT_CAP}"
            )
            rec_entry["skipped"] = "credit_cap_protection"
            state["records"].append(rec_entry)
            write_progress(state)
            log(f"HALT: {state['halt_reason']}")
            break

        if not skip_frame:
            frame = run_stage(
                "frame_gen",
                [sys.executable, "-m", "tools.frame_gen",
                 "--record-id", rid, "--confirm", "go"],
                timeout_s=300,
            )
            rec_entry["stages"].append(frame)
            if frame["exit_code"] != 0:
                rec_entry["halted_at"] = "frame_gen"
                rec_entry["halt_reason"] = f"frame_gen exit {frame['exit_code']}"
                state["records"].append(rec_entry)
                state["status"] = "halted_hard_error"
                state["halt_reason"] = (
                    f"Day {day:02d} frame_gen failed: "
                    f"{frame.get('error', '?')[:200]}"
                )
                write_progress(state)
                log(f"HARD ERROR: {state['halt_reason']}")
                log(f"frame_gen stderr tail:\n{frame.get('stderr_tail','')}")
                log(f"frame_gen stdout tail:\n{frame.get('stdout_tail','')[-1500:]}")
                return 2
            state["cumulative_credits_used"] += PER_RECORD_FRAME_CREDITS
            log(
                f"  frame_gen OK ({frame['wall_s']:.0f}s)  "
                f"cumulative {state['cumulative_credits_used']} credits"
            )
        else:
            log(f"  frame_gen skipped (already done)")

        video = run_stage(
            "video_gen",
            [sys.executable, "-m", "tools.video_gen",
             "--record-id", rid, "--confirm", "go", "--duration", "6"],
            timeout_s=900,
        )
        rec_entry["stages"].append(video)
        if video["exit_code"] != 0:
            rec_entry["halted_at"] = "video_gen"
            rec_entry["halt_reason"] = f"video_gen exit {video['exit_code']}"
            state["records"].append(rec_entry)
            state["status"] = "halted_hard_error"
            state["halt_reason"] = (
                f"Day {day:02d} video_gen failed: "
                f"{video.get('error', '?')[:200]}"
            )
            write_progress(state)
            log(f"HARD ERROR: {state['halt_reason']}")
            log(f"video_gen stderr tail:\n{video.get('stderr_tail','')}")
            log(f"video_gen stdout tail:\n{video.get('stdout_tail','')[-1500:]}")
            return 2
        state["cumulative_credits_used"] += PER_RECORD_VIDEO_CREDITS
        log(
            f"  video_gen OK ({video['wall_s']:.0f}s)  "
            f"cumulative {state['cumulative_credits_used']} credits"
        )

        # Look for R2 URL first (Fal fallback path used in this batch), then Fal.
        r2_match = re.search(
            r"re-hosted on R2 -> (https://[^\s]+)",
            video.get("stdout_tail", ""),
        )
        fal_match = re.search(
            r"re-hosted on Fal -> (https://[^\s]+)",
            video.get("stdout_tail", ""),
        )
        if r2_match:
            rec_entry["clip_url"] = r2_match.group(1)
            rec_entry["clip_host"] = "r2"
        elif fal_match:
            rec_entry["clip_url"] = fal_match.group(1)
            rec_entry["clip_host"] = "fal"
        rec_entry["wall_s"] = time.time() - rec_t0
        rec_entry["end_ts"] = dt.datetime.now().isoformat(timespec="seconds")
        rec_entry["status"] = "ok"
        state["records"].append(rec_entry)
        write_progress(state)
        log(f"  Day {day:02d} DONE in {rec_entry['wall_s']:.0f}s")

    if state["status"] == "running":
        state["status"] = "complete"
    state["end_ts"] = dt.datetime.now().isoformat(timespec="seconds")
    write_progress(state)
    log("=== Batch complete ===")
    log(f"Status: {state['status']}")
    ok_count = len([r for r in state["records"] if r.get("status") == "ok"])
    log(f"Records processed: {ok_count}/{len(R61_TARGETS)}")
    log(f"Cumulative credits used: {state['cumulative_credits_used']}")
    if state.get("halt_reason"):
        log(f"Halt reason: {state['halt_reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
