"""
Seed the R61 Video table from R57 generated content.

Reads records from the R57 Content table where Image Status = "Generated"
and inserts a corresponding row into the R61 Video table with Video Status =
"Pending". Skips any Index that already exists in the Video table so reruns
are idempotent.

Both tables live in the same Airtable base (appC3HqG42ftswOvw), so the same
AIRTABLE_API_KEY in R61_video_pipeline/.env covers both reads and writes.

Usage:
    python -m tools.sync_r57_to_video --dry-run   # show plan, no writes
    python -m tools.sync_r57_to_video             # interactive sync
"""

import argparse
import datetime as dt
import os
import sys
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

from tools import airtable_video as av  # noqa: E402

LOG_PATH = PROJECT_ROOT / "references" / "outputs" / "sync_run.log"

R57_TABLE_NAME = "May2025 - Provinzial_Geier&Ayhan"
R57_FILTER = '{Image Status} = "Generated"'

# R57 -> R61 field map. Right side is the R61 Video table field; left side
# is the R57 field name. Source Image needs attachment-shape conversion;
# everything else is a straight copy.
FIELD_MAP = {
    "Index": "Index",
    "Ad Name": "Ad Name",
    "Caption": "Caption",
    "Scheduled Date": "Scheduled Date",
}

FIRE_WORDS = {"go", "fire", "yes", "run it", "run", "ship"}


def log(msg):
    ts = dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _r57_headers():
    return {
        "Authorization": f"Bearer {av.AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }


def _r57_url():
    table = quote(R57_TABLE_NAME, safe="")
    return f"{av.AIRTABLE_API_URL}/{av.AIRTABLE_BASE_ID}/{table}"


def fetch_r57_generated():
    """Pull all R57 Content records with Image Status = Generated."""
    all_records = []
    params = {"filterByFormula": R57_FILTER}
    offset = None
    while True:
        if offset:
            params["offset"] = offset
        resp = requests.get(_r57_url(), headers=_r57_headers(), params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"R57 query failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return all_records


def fetch_existing_video_indices():
    """Indices already present in the R61 Video table, regardless of status."""
    existing = av.get_records()
    indices = set()
    for r in existing:
        idx = r.get("fields", {}).get("Index")
        if idx is not None:
            indices.add(int(idx))
    return indices


def build_video_fields(r57_record):
    """Map a single R57 record to R61 Video table fields. None if invalid."""
    rf = r57_record.get("fields", {})
    out = {}
    for r57_name, r61_name in FIELD_MAP.items():
        if r57_name in rf:
            out[r61_name] = rf[r57_name]

    # Source Image — copy Generated Image 1's first attachment URL.
    gi1 = rf.get("Generated Image 1") or []
    if gi1:
        first = gi1[0]
        url = first.get("url")
        filename = first.get("filename") or "source.png"
        if url:
            out["Source Image"] = [{"url": url, "filename": filename}]

    out[av.STATUS_FIELD] = av.STATUS_PENDING
    return out


def plan(records, existing_indices):
    """Split source records into (to_sync, skipped_duplicate, skipped_no_index)."""
    to_sync = []
    skipped_dup = []
    skipped_no_index = []
    for r in records:
        idx = r.get("fields", {}).get("Index")
        if idx is None:
            skipped_no_index.append(r)
            continue
        if int(idx) in existing_indices:
            skipped_dup.append(r)
            continue
        to_sync.append(r)
    return to_sync, skipped_dup, skipped_no_index


def print_plan(to_sync, skipped_dup, skipped_no_index):
    print()
    print("=" * 60)
    print("SYNC PLAN  (R57 Content -> R61 Video)")
    print("=" * 60)
    print(f"  R57 source filter   : {R57_FILTER}")
    print(f"  Eligible R57 records: {len(to_sync) + len(skipped_dup) + len(skipped_no_index)}")
    print(f"  Already in R61      : {len(skipped_dup)} (skip)")
    print(f"  Missing R57 Index   : {len(skipped_no_index)} (skip)")
    print(f"  TO SYNC             : {len(to_sync)}")
    print("=" * 60)
    if to_sync:
        print("Records that will be inserted:")
        for r in to_sync:
            f = r.get("fields", {})
            has_img = "yes" if (f.get("Generated Image 1") or []) else "NO"
            print(f"  - Index={f.get('Index')!r}  Ad Name={f.get('Ad Name')!r}  source_image={has_img}")
    if skipped_dup:
        print(f"Already-present Indices: {sorted(int(r['fields']['Index']) for r in skipped_dup)}")


def confirm():
    print(f"Type one of {sorted(FIRE_WORDS)} to proceed, anything else aborts.")
    return input("> ").strip().lower() in FIRE_WORDS


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync R57 generated rows into R61 Video table")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show the plan; do not write to the Video table.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N eligible records this run.")
    args = parser.parse_args(argv)

    missing = av.check_credentials()
    if missing:
        print(f"Missing env vars in {ENV_PATH}: {', '.join(missing)}", file=sys.stderr)
        return 1

    log(f"Fetching R57 records where {R57_FILTER}...")
    r57 = fetch_r57_generated()
    log(f"R57 returned {len(r57)} generated record(s).")

    existing = fetch_existing_video_indices()
    log(f"R61 Video table currently holds {len(existing)} indices.")

    to_sync, skipped_dup, skipped_no_index = plan(r57, existing)
    if args.limit:
        to_sync = to_sync[: args.limit]
    print_plan(to_sync, skipped_dup, skipped_no_index)

    if args.dry_run:
        log("Dry run — no rows written.")
        return 0

    if not to_sync:
        log("Nothing to sync.")
        return 0

    if not confirm():
        log("Aborted at confirmation gate — no rows written.")
        return 1

    log(f"Confirmed. Inserting {len(to_sync)} row(s) into Video table.")
    created = 0
    failed = 0
    for r in to_sync:
        idx = r.get("fields", {}).get("Index")
        ad_name = r.get("fields", {}).get("Ad Name") or "(no name)"
        try:
            fields = build_video_fields(r)
            resp = requests.post(
                f"{av.AIRTABLE_API_URL}/{av.AIRTABLE_BASE_ID}/{quote(av.TABLE_NAME, safe='')}",
                headers=_r57_headers(),
                json={"fields": fields},
                timeout=30,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"{resp.status_code}: {resp.text}")
            new_id = resp.json().get("id")
            created += 1
            log(f"INSERT ok  Index={idx} ad='{ad_name}' -> {new_id}")
        except Exception as e:
            failed += 1
            log(f"INSERT FAIL Index={idx} ad='{ad_name}': {e}")

    log(f"Sync complete. Created={created} Failed={failed} "
        f"SkippedDup={len(skipped_dup)} SkippedNoIndex={len(skipped_no_index)}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
