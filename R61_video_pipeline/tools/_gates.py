"""
Gate-queue writer for the ClaudeClaw primary agent.

Each R61 step (frame gen, video gen, stitch) calls `append_gate()` at the
point where a human review is needed. Entries land in
`C:\\CONTENT_PIPELINE\\shared\\gates\\pending.json`. The primary agent's
`r61-gate-watcher` cron polls that file every 15 minutes and pings Telegram
for any entry with `notified: false`.

Schema per entry (matches the cron's expected format):
    {
      "gate_number": int,        # 0=frames, 1=clip, 4=stitch-final
      "gate_name": str,          # e.g. "frames_generated", "clip_generated"
      "record_id": str,          # Airtable record id or "batch"
      "ad_name": str,            # display label
      "video_url": str,          # video/asset URL ("" for non-video gates)
      "timestamp": str,          # ISO 8601 local time
      "status": "pending",       # pending | approved | rejected
      "notified": false          # flipped to true by the gate-watcher cron
    }

Concurrency: read-modify-write with os.replace for atomic swap. Safe under
sequential script runs and a 15-min polling cron. Not safe for high-frequency
concurrent writers — none exist in this pipeline.
"""

import datetime as dt
import json
import os
import tempfile
from pathlib import Path

# Repo root is two levels above this file: tools/ -> R61_video_pipeline/ -> root.
GATES_FILE = (
    Path(__file__).resolve().parent.parent.parent
    / "shared" / "gates" / "pending.json"
)


def _load():
    if not GATES_FILE.exists():
        return {
            "description": (
                "R61 human-gate queue. Pipeline stages append entries here; "
                "the primary agent's r61-gate-watcher cron polls this file "
                "every 15 minutes and notifies the user via Telegram."
            ),
            "gates": [],
        }
    with open(GATES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data):
    GATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(GATES_FILE.parent), prefix=".pending_", suffix=".json"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, GATES_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def append_gate(
    gate_number,
    gate_name,
    record_id,
    ad_name,
    video_url="",
    extra=None,
):
    """Append one gate entry. Returns the inserted dict.

    `extra` is an optional dict of additional fields merged into the entry
    (e.g. {"clip_count": 8} for a batch summary).
    """
    entry = {
        "gate_number": gate_number,
        "gate_name": gate_name,
        "record_id": record_id,
        "ad_name": ad_name,
        "video_url": video_url or "",
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "status": "pending",
        "notified": False,
    }
    if extra:
        entry.update(extra)

    data = _load()
    data.setdefault("gates", []).append(entry)
    _save(data)
    return entry
