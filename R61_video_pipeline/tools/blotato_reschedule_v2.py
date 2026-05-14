"""
R61 v2 re-scheduler — cancel existing Blotato posts, reschedule with v2 media.

When v2 final mp4s replace v1, Blotato's existing submissions still reference
the v1 R2 URL (their `mediaUrls[0]` was captured at original schedule time).
Re-attaching the v2 video to Airtable does NOT propagate to Blotato. To make
Blotato deliver the v2 video, the existing submission must be cancelled and
a new one created against the v2 URL.

This tool:
  1. Cancels each known Blotato submission via DELETE /v2/posts/{id}.
  2. Computes a new schedule — consecutive days starting from a base date,
     one post per day at the specified Europe/Berlin local time.
  3. Updates each Airtable record's `Scheduled Date` to the new local time
     (stored with the CEST offset so the human-readable Berlin value lands
     unchanged in the table).
  4. Resubmits to Blotato using the v2 R2 URL — reconstructed as
     `{R2_PUBLIC_URL}/r61/final/v2/{filename}` from the Airtable attachment
     filename, NOT the Airtable-proxy URL (which is short-lived).
  5. Logs the new submission IDs.

Scheduling-only contract is enforced exactly as in blotato_schedule.py:
every submission carries `scheduledTime`; the helper that POSTs refuses to
run if it's missing. This is the [[feedback_blotato_no_post]] safeguard.

This tool is intentionally non-interactive — the operator (you) said to fire
immediately. No per-record gate. There is also no `--confirm` toggle for the
opposite case; if you want a gated flow, run blotato_schedule.py.

Usage:
    python -m tools.blotato_reschedule_v2 --dry-run
    python -m tools.blotato_reschedule_v2
    python -m tools.blotato_reschedule_v2 --start-date 2026-05-15
    python -m tools.blotato_reschedule_v2 --berlin-hour 18
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

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
from tools.blotato_schedule import (  # noqa: E402
    BLOTATO_BASE,
    POSTS_ENDPOINT,
    PLATFORM,
    MEDIA_TYPE,
    _blotato_headers,
    resolve_account_id,
    submit_post,
)

LOG_PATH = PROJECT_ROOT / "references" / "outputs" / "blotato_reschedule_v2_run.log"
BERLIN_TZ = ZoneInfo("Europe/Berlin")

# Existing submissions to cancel, sourced from
# references/outputs/blotato_schedule_run.log (2026-05-13 run).
# Keyed by Airtable record id.
EXISTING_SUBMISSIONS = {
    "rec4cuKlnZwe0Slag": "6112164d-0287-4bf6-ba12-d97c178fb0cc",  # Day 3
    "rec7FO4Yw2JOes9UQ": "5bdc96f4-f2a5-4779-b2c1-c96c60f3e323",  # Day 13
    "rec7rlJaPz1iVNTzw": "bed72c47-4328-4de7-8fba-ac8a0b6f0401",  # Day 14
    "recEG1hfayCdXU7Qu": "0efcf307-ce95-4512-8637-c54c2a14b1e6",  # Day 15
    "recEmXiRyXHZPbsKN": "0b10b418-3fa7-416f-a39f-84dc8eb4ce69",  # Day 17
    "rec5g78UeoYm5ntca": "d61d9b66-b9a3-46b9-9698-2d1f61b1ab80",  # Day 18
    "rec5iPo35NwtZNZoK": "737cf283-390d-41a1-8eaa-41dfa918e2b0",  # Day 21
    "rec6dGknAQZTqJiYM": "193c33a4-de5a-46ab-9d3c-19a3c838f4f9",  # Day 29
}


def log(msg):
    ts = dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def cancel_submission(submission_id: str) -> tuple[bool, str]:
    """Cancel a scheduled Blotato post by submission id.

    DELETE /v2/posts/{id}. Blotato's request handler enforces a
    non-empty JSON body whenever the Content-Type is application/json
    (observed: "Body cannot be empty when content-type is set to
    'application/json'"), so we send `{}` as the body. A 404 is treated
    as already-cancelled (idempotent).
    """
    url = f"{POSTS_ENDPOINT}/{submission_id}"
    try:
        resp = requests.delete(url, headers=_blotato_headers(),
                               json={}, timeout=30)
    except requests.RequestException as e:
        return False, f"network error: {e}"
    body = (resp.text or "")[:400]
    if resp.status_code in (200, 202, 204):
        return True, f"deleted ({resp.status_code})"
    if resp.status_code == 404:
        return True, "already gone (404)"
    return False, f"HTTP {resp.status_code}: {body}"


def reconstruct_v2_url(attachment) -> str | None:
    """Build the v2 public R2 URL from an Airtable Final Video attachment.

    The Airtable-proxy URL is unsuitable for Blotato — it's signed and
    short-lived. The R2 key for v2 finals is `r61/final/v2/{filename}`,
    matching the upload path in tools/hf_stitch.upload_to_r2().
    """
    filename = (attachment or {}).get("filename")
    public_base = os.environ.get("R2_PUBLIC_URL", "").rstrip("/")
    if not filename or not public_base:
        return None
    return f"{public_base}/r61/final/v2/{filename}"


def compute_schedule(records, start_date_iso: str, berlin_hour: int):
    """Return [(record, berlin_dt, utc_iso), ...] sorted by Index ascending.

    Day N maps to start_date + (N-th-record-after-sort) days at the
    requested Berlin local hour. Times are emitted with the live Berlin
    UTC offset (+02:00 in CEST, +01:00 in CET) so the human-readable
    `Scheduled Date` in Airtable shows the actual posting time.
    """
    start = dt.datetime.fromisoformat(start_date_iso).date()
    ordered = sorted(records, key=lambda r: r.get("fields", {}).get("Index") or 9999)
    out = []
    for i, r in enumerate(ordered):
        d = start + dt.timedelta(days=i)
        local = dt.datetime(d.year, d.month, d.day, berlin_hour, 0, 0,
                            tzinfo=BERLIN_TZ)
        utc = local.astimezone(dt.timezone.utc)
        out.append((r, local, utc.strftime("%Y-%m-%dT%H:%M:%SZ")))
    return out


def build_payload(record, account_id, scheduled_utc):
    """Wrap post body — same shape as blotato_schedule.build_payload, but
    forced to v2 R2 URL reconstruction. Caption taken from Airtable.
    """
    fields = record.get("fields", {})
    finals = fields.get("Final Video") or []
    if not finals:
        return None, "missing Final Video attachment"
    media_url = reconstruct_v2_url(finals[0])
    if not media_url:
        return None, "could not reconstruct v2 R2 URL (filename or R2_PUBLIC_URL missing)"
    caption = (fields.get("Caption") or "").strip()
    if not caption:
        return None, "Caption is empty"
    return {
        "post": {
            "accountId": account_id,
            "target": {"targetType": PLATFORM, "mediaType": MEDIA_TYPE},
            "content": {
                "text": caption,
                "platform": PLATFORM,
                "mediaUrls": [media_url],
            },
        },
        "scheduledTime": scheduled_utc,
    }, None


def fmt_airtable_scheduled(local_berlin_dt: dt.datetime) -> str:
    """ISO with offset, e.g. `2026-05-15T18:00:00+02:00`."""
    return local_berlin_dt.isoformat(timespec="seconds")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="R61 v2 — cancel + reschedule the 8 known Blotato Instagram posts"
    )
    parser.add_argument("--start-date", default="2026-05-15",
                        help="First posting date (YYYY-MM-DD). Default 2026-05-15.")
    parser.add_argument("--berlin-hour", type=int, default=18,
                        help="Posting hour in Europe/Berlin local time (0-23). Default 18.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the cancel/reschedule plan; no API calls, no writes.")
    parser.add_argument("--skip-cancel", action="store_true",
                        help="Don't call DELETE on the existing submissions. "
                             "Use only if you've already cancelled them by hand.")
    args = parser.parse_args(argv)

    if av.check_credentials():
        print("Missing Airtable creds — see .env", file=sys.stderr)
        return 1
    if not os.getenv("BLOTATO_API_KEY"):
        print("BLOTATO_API_KEY missing in .env", file=sys.stderr)
        return 1
    if not os.getenv("R2_PUBLIC_URL"):
        print("R2_PUBLIC_URL missing in .env — required to build v2 media URL",
              file=sys.stderr)
        return 1

    account_id = resolve_account_id(PLATFORM)
    log(f"Resolved Instagram account_id={account_id}")

    # Load each record once.
    records = []
    for rec_id in EXISTING_SUBMISSIONS:
        try:
            records.append(av.get_record(rec_id))
        except Exception as e:
            log(f"  ERROR fetching {rec_id}: {e}")
    if len(records) != len(EXISTING_SUBMISSIONS):
        log(f"  WARN: only fetched {len(records)}/{len(EXISTING_SUBMISSIONS)} records")

    schedule = compute_schedule(records, args.start_date, args.berlin_hour)
    log(f"Computed schedule for {len(schedule)} record(s); base "
        f"{args.start_date} @ {args.berlin_hour:02d}:00 Europe/Berlin")

    print()
    print(f"{'Idx':>4}  {'RecordId':<19}  {'Submission ID':<38}  Berlin local         → UTC scheduledTime")
    for r, local, utc in schedule:
        idx = r.get("fields", {}).get("Index")
        sub_id = EXISTING_SUBMISSIONS.get(r["id"], "<none>")
        print(f"  {idx:>2}  {r['id']:<19}  {sub_id:<38}  "
              f"{local.strftime('%Y-%m-%d %H:%M %Z')}  → {utc}")
    print()

    if args.dry_run:
        log("DRY RUN — no Blotato calls, no Airtable writes.")
        return 0

    summary = {"cancelled": 0, "cancel_failed": 0,
               "resubmitted": 0, "resubmit_failed": 0}

    # --- Phase 1: cancel existing submissions.
    if args.skip_cancel:
        log("--skip-cancel set; not calling DELETE")
    else:
        log("Phase 1: cancelling existing submissions")
        for r, _local, _utc in schedule:
            rec_id = r["id"]
            sub_id = EXISTING_SUBMISSIONS[rec_id]
            ok, note = cancel_submission(sub_id)
            if ok:
                summary["cancelled"] += 1
                log(f"  CANCEL ok    {rec_id}  sub={sub_id}  ({note})")
            else:
                summary["cancel_failed"] += 1
                log(f"  CANCEL FAIL  {rec_id}  sub={sub_id}  ({note})")

    # --- Phase 2: update Airtable Scheduled Date + resubmit.
    log("Phase 2: updating Airtable Scheduled Date and resubmitting to Blotato")
    new_submissions = {}
    for r, local, utc in schedule:
        rec_id = r["id"]
        idx = r.get("fields", {}).get("Index")
        ad_name = r.get("fields", {}).get("Ad Name") or "(no name)"
        log(f"  RESUB {rec_id} (Day {idx} '{ad_name}')")

        # 1. Update Scheduled Date to new local Berlin time.
        airtable_scheduled = fmt_airtable_scheduled(local)
        try:
            av.update_record(rec_id, {"Scheduled Date": airtable_scheduled})
            log(f"    Scheduled Date → {airtable_scheduled}")
        except Exception as e:
            log(f"    Airtable update FAILED: {e}")
            summary["resubmit_failed"] += 1
            continue

        # 2. Re-fetch to get the latest snapshot (Caption could have been edited).
        rec = av.get_record(rec_id)

        # 3. Build + submit.
        payload, err = build_payload(rec, account_id, utc)
        if err:
            log(f"    PAYLOAD BUILD failed: {err}")
            summary["resubmit_failed"] += 1
            continue
        log(f"    media_url = {payload['post']['content']['mediaUrls'][0]}")
        log(f"    scheduledTime = {payload['scheduledTime']}")
        try:
            body = submit_post(payload)
        except Exception as e:
            log(f"    POST FAILED: {e}")
            summary["resubmit_failed"] += 1
            continue
        sub_id = (body.get("postSubmissionId") or body.get("id")
                  or body.get("submissionId"))
        new_submissions[rec_id] = sub_id
        log(f"    new submissionId = {sub_id}")

        # Ensure status stays Scheduled.
        try:
            av.update_record(rec_id, {av.STATUS_FIELD: av.STATUS_SCHEDULED})
        except Exception as e:
            log(f"    (status patch failed — non-fatal) {e}")
        summary["resubmitted"] += 1

    log(f"Run complete. Summary: {summary}")
    log(f"New submission IDs:")
    for rec_id, sub_id in new_submissions.items():
        log(f"  {rec_id} → {sub_id}")
    return 0 if summary["resubmit_failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
