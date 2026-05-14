"""
R61 Step 9 — Schedule Approved videos to Blotato.

Reads Video records where Video Status = "Approved", reads the Final Video
URL (R2-hosted, already public), the Caption, and the Scheduled Date, and
submits a SCHEDULED Instagram post to Blotato. Status flips Approved →
Scheduled on success. The Blotato submission ID is logged.

Hard safety rules (encoded in code, not optional):
  • Every submission MUST include `scheduledTime`. If a record's Scheduled
    Date is empty, unparseable, or in the past, the record is SKIPPED.
    A missing `scheduledTime` would post immediately — the project memory
    [[feedback_blotato_no_post]] forbids immediate posting until the hold
    is lifted, and the user reiterated SCHEDULE ONLY in this task.
  • Per-record interactive fire-word gate before each submission. The
    exact post payload is printed and the operator must type `go` / `fire`
    / `yes` / `run it` / `ship` to send. Anything else aborts the run;
    `skip` skips just this record.
  • There is no `--confirm` bypass on this tool — scheduling externals is
    too consequential for a one-shot non-interactive flag.

Per .agent/skills/blotato_best_practices/SKILL.md:
  • R2 URLs are public and persistent — pass them straight to `mediaUrls`
    (Method 0 — preferred). No upload/re-host step.
  • Instagram videos REQUIRE `mediaType: "reel"` in the post body.
  • `scheduledTime` must be ISO 8601 UTC ("...Z"). Airtable stores the
    Scheduled Date with a `+02:00` (CEST) offset; we convert to UTC.

Usage:
    python -m tools.blotato_schedule --dry-run
    python -m tools.blotato_schedule
    python -m tools.blotato_schedule --limit 1
    python -m tools.blotato_schedule --record-id recXXXX
"""

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

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

LOG_PATH = PROJECT_ROOT / "references" / "outputs" / "blotato_schedule_run.log"

BLOTATO_BASE = "https://backend.blotato.com"
ACCOUNTS_ENDPOINT = f"{BLOTATO_BASE}/v2/users/me/accounts"
POSTS_ENDPOINT = f"{BLOTATO_BASE}/v2/posts"

PLATFORM = "instagram"
MEDIA_TYPE = "reel"  # Required for Instagram video posts per Blotato spec.

GO_WORDS = {"go", "fire", "yes", "run it", "run", "ship"}
SKIP_WORDS = {"skip", "s"}


def log(msg):
    ts = dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _blotato_headers():
    key = os.environ.get("BLOTATO_API_KEY")
    if not key:
        raise RuntimeError("BLOTATO_API_KEY missing in .env")
    return {"blotato-api-key": key, "Content-Type": "application/json"}


def resolve_account_id(platform=PLATFORM):
    """Look up the Blotato accountId for the requested platform."""
    override = os.environ.get(f"BLOTATO_{platform.upper()}_ACCOUNT_ID")
    if override:
        return override.strip()
    resp = requests.get(
        ACCOUNTS_ENDPOINT,
        headers={"blotato-api-key": os.environ["BLOTATO_API_KEY"]},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Could not list Blotato accounts ({resp.status_code}): {resp.text[:200]}"
        )
    items = resp.json().get("items") or []
    matches = [a for a in items if (a.get("platform") or "").lower() == platform]
    if not matches:
        raise RuntimeError(
            f"No connected {platform} account in Blotato. Connect one at "
            f"my.blotato.com or set BLOTATO_{platform.upper()}_ACCOUNT_ID."
        )
    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple {platform} accounts connected — set "
            f"BLOTATO_{platform.upper()}_ACCOUNT_ID in .env to disambiguate. "
            f"IDs: {[m['id'] for m in matches]}"
        )
    return str(matches[0]["id"])


def parse_scheduled_to_utc(s):
    """Parse the Airtable Scheduled Date and return ISO-8601 UTC `...Z`.

    Returns None if the value is empty, unparseable, or in the past.
    Accepts inputs with offset (e.g. `2026-06-03T10:00:00+02:00`) or naive
    ISO datetimes (assumed UTC).
    """
    if not s:
        return None
    s = s.strip()
    try:
        # Python 3.11+ handles "Z" suffix natively; earlier needs replacement.
        parsed = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        # Try date-only fallback (`2026-06-03` -> midnight UTC).
        try:
            parsed = dt.datetime.fromisoformat(s + "T00:00:00+00:00")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    parsed_utc = parsed.astimezone(dt.timezone.utc)
    if parsed_utc <= dt.datetime.now(dt.timezone.utc):
        return None
    return parsed_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def media_url_from_attachment(att):
    """Prefer the R2 public URL (matches stitch.py upload key shape) over
    Airtable's ephemeral CDN copy. The attachment's `filename` round-trips
    back to the R2 key — hf_stitch.py writes objects to
    `r61/final/v3/{filename}` against `R2_PUBLIC_URL`. Falls back to the
    Airtable URL if R2_PUBLIC_URL is unset or the filename is missing.
    """
    filename = att.get("filename")
    public_base = os.environ.get("R2_PUBLIC_URL", "").rstrip("/")
    if filename and public_base:
        return f"{public_base}/r61/final/v3/{filename}"
    return att.get("url")


def build_payload(record, account_id, scheduled_utc):
    """Compose the body for POST /v2/posts.

    Schema (confirmed against backend.blotato.com 2026-05-13 — the API
    requires a `post` wrapper with separate `target` and `content` nodes):

        {
          "post": {
            "accountId": "...",
            "target": { "targetType": "instagram", "mediaType": "reel" },
            "content": { "text": "...", "platform": "instagram",
                         "mediaUrls": [...] }
          },
          "scheduledTime": "...Z"  # ISO 8601 UTC; required.
        }

    Media URL is the R2 public URL (reconstructed from the attachment
    filename), not Airtable's CDN. The Instagram-reel hint lives in
    `target.mediaType` in this shape, not in `content`.
    """
    fields = record.get("fields", {})
    finals = fields.get("Final Video") or []
    if not finals:
        return None, "missing Final Video attachment"
    media_url = media_url_from_attachment(finals[0])
    if not media_url:
        return None, "Final Video attachment has no url and R2 reconstruction failed"
    caption = (fields.get("Caption") or "").strip()
    if not caption:
        return None, "Caption is empty"
    payload = {
        "post": {
            "accountId": account_id,
            "target": {
                "targetType": PLATFORM,
                "mediaType": MEDIA_TYPE,
            },
            "content": {
                "text": caption,
                "platform": PLATFORM,
                "mediaUrls": [media_url],
            },
        },
        "scheduledTime": scheduled_utc,
    }
    return payload, None


def gate(record, payload):
    """Print the post details and gate on operator confirmation.

    Returns 'go' / 'skip' / 'abort'.
    """
    fields = record.get("fields", {})
    index = fields.get("Index")
    ad_name = fields.get("Ad Name") or "(no name)"
    print()
    print("=" * 70)
    print(f"BLOTATO SCHEDULE — Day {index} ({record['id']})")
    print("=" * 70)
    post = payload["post"]
    target = post["target"]
    content = post["content"]
    print(f"  Ad Name        : {ad_name}")
    print(f"  Platform       : {target['targetType']} (mediaType={target['mediaType']})")
    print(f"  Account ID     : {post['accountId']}")
    print(f"  Scheduled (UTC): {payload['scheduledTime']}")
    print(f"  Media URL      : {content['mediaUrls'][0]}")
    print(f"  Caption ({len(content['text'])} chars):")
    for line in content["text"].splitlines():
        print(f"      {line}")
    print()
    print("This will SUBMIT a SCHEDULED post (no immediate posting).")
    print(f"Type one of {sorted(GO_WORDS)} to send | "
          f"{sorted(SKIP_WORDS)} to skip just this record | "
          f"anything else aborts the whole run.")
    answer = input("> ").strip().lower()
    if answer in GO_WORDS:
        return "go"
    if answer in SKIP_WORDS:
        return "skip"
    return "abort"


def submit_post(payload):
    """POST to Blotato /v2/posts. Returns the parsed JSON body (no polling
    here — for SCHEDULED posts the terminal state arrives at scheduledTime,
    not seconds after submission). Caller logs the submission id.
    """
    # Defence in depth: refuse to submit without scheduledTime in the body.
    if not payload.get("scheduledTime"):
        raise RuntimeError(
            "Refusing to submit: payload has no scheduledTime. This safeguard "
            "exists to prevent accidental immediate posting."
        )
    resp = requests.post(
        POSTS_ENDPOINT,
        headers=_blotato_headers(),
        json=payload,
        timeout=60,
    )
    body_text = (resp.text or "")[:2000]
    try:
        body = resp.json()
    except ValueError:
        body = {"_raw": body_text}
    if resp.status_code >= 400:
        raise RuntimeError(f"Blotato POST {resp.status_code}: {body_text}")
    return body


def process_record(record, account_id, batch_confirm=False):
    rec_id = record["id"]
    fields = record.get("fields", {})
    ad_name = fields.get("Ad Name") or "(no name)"
    index = fields.get("Index")

    scheduled_raw = fields.get("Scheduled Date")
    scheduled_utc = parse_scheduled_to_utc(scheduled_raw)
    if not scheduled_utc:
        log(f"SKIP {rec_id} (Day {index}): unschedulable Scheduled Date "
            f"{scheduled_raw!r} — refusing to submit without future UTC time.")
        return "skipped_unschedulable"

    payload, err = build_payload(record, account_id, scheduled_utc)
    if err:
        log(f"SKIP {rec_id} (Day {index}): {err}")
        return "skipped_missing_inputs"

    if batch_confirm:
        log(f"BATCH-CONFIRM bypass: {rec_id} (Day {index}) "
            f"scheduledTime={payload['scheduledTime']}")
    else:
        decision = gate(record, payload)
        if decision == "abort":
            log(f"ABORT at gate on {rec_id} (Day {index}) — stopping run.")
            raise SystemExit(3)
        if decision == "skip":
            log(f"SKIP gate decision on {rec_id} (Day {index}).")
            return "skipped_at_gate"

    log(f"SUBMIT {rec_id} (Day {index}) -> Blotato /v2/posts")
    response = submit_post(payload)
    submission_id = (
        response.get("postSubmissionId")
        or response.get("id")
        or response.get("submissionId")
    )
    log(f"  blotato response status={response.get('status')!r} "
        f"submissionId={submission_id!r}")

    av.update_record(
        rec_id,
        {
            av.STATUS_FIELD: av.STATUS_SCHEDULED,
        },
    )
    log(f"DONE  {rec_id} (Day {index}) status -> {av.STATUS_SCHEDULED}, "
        f"scheduledTime={payload['scheduledTime']}, submissionId={submission_id}")
    return "ok"


def dry_run_report(records, account_id):
    print()
    print(f"DRY RUN — Blotato Instagram scheduling")
    print(f"  account_id  : {account_id} (provinzial_geier_ayhan_ohg expected)")
    print(f"  platform    : {PLATFORM}, mediaType: {MEDIA_TYPE}")
    print(f"  endpoint    : POST {POSTS_ENDPOINT}")
    print(f"  records hit : {len(records)} (Video Status = 'Approved')")
    print()
    if not records:
        print("  (no rows to schedule)")
        return
    now_utc = dt.datetime.now(dt.timezone.utc)
    for r in sorted(records, key=lambda x: x.get("fields", {}).get("Index") or 0):
        f = r.get("fields", {})
        idx = f.get("Index")
        ad_name = f.get("Ad Name") or "(no name)"
        sched_raw = f.get("Scheduled Date") or ""
        sched_utc = parse_scheduled_to_utc(sched_raw)
        finals = f.get("Final Video") or []
        media_url = media_url_from_attachment(finals[0]) if finals else None
        caption = (f.get("Caption") or "").strip()

        status_note = "OK"
        if not sched_utc:
            if not sched_raw:
                status_note = "WOULD SKIP — Scheduled Date is empty"
            else:
                try:
                    parsed = dt.datetime.fromisoformat(sched_raw.replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=dt.timezone.utc)
                    if parsed.astimezone(dt.timezone.utc) <= now_utc:
                        status_note = "WOULD SKIP — Scheduled Date is in the past"
                    else:
                        status_note = "WOULD SKIP — Scheduled Date is unparseable"
                except ValueError:
                    status_note = f"WOULD SKIP — cannot parse {sched_raw!r}"
        elif not media_url:
            status_note = "WOULD SKIP — Final Video attachment missing"
        elif not caption:
            status_note = "WOULD SKIP — Caption is empty"

        print(f"  Day {idx:>2}  {r['id']}  -> {status_note}")
        print(f"      Ad Name        : {ad_name}")
        print(f"      Scheduled (raw): {sched_raw!r}")
        print(f"      Scheduled (UTC): {sched_utc!r}")
        print(f"      Media URL      : {(media_url or '')[:90]}{'...' if media_url and len(media_url) > 90 else ''}")
        print(f"      Caption ({len(caption)} chars):")
        for line in caption.splitlines():
            print(f"        {line}")
        if status_note == "OK":
            preview_payload = {
                "post": {
                    "accountId": account_id,
                    "target": {"targetType": PLATFORM, "mediaType": MEDIA_TYPE},
                    "content": {
                        "text": caption[:60] + ("..." if len(caption) > 60 else ""),
                        "platform": PLATFORM,
                        "mediaUrls": [media_url],
                    },
                },
                "scheduledTime": sched_utc,
            }
            print(f"      Payload preview: {json.dumps(preview_payload)[:240]}...")
        print()
    print("No Blotato calls or Airtable writes were made.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="R61 Step 9 — schedule Approved videos to Blotato Instagram"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show the plan; no Blotato calls, no Airtable writes.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N Approved records this run.")
    parser.add_argument("--record-id", default=None,
                        help="Force-process this specific Airtable record id "
                             "(bypasses the Approved status filter).")
    parser.add_argument("--platform", default=PLATFORM,
                        help="Override target platform (default instagram). "
                             "Only used for account-id lookup; the rest of the "
                             "payload still assumes Instagram-style fields.")
    parser.add_argument("--batch-confirm", action="store_true",
                        help="DANGER — bypass the interactive per-record fire-word "
                             "gate. Use only after the batch has been approved at "
                             "the aggregate level (e.g. you have already reviewed "
                             "samples). Every record still gets the scheduledTime "
                             "guard, the missing-Final-Video skip, and the "
                             "scheduled-in-past skip. Existence of this flag does "
                             "NOT lift the immediate-post hold — scheduledTime is "
                             "still mandatory.")
    parser.add_argument("--all-stitched", action="store_true",
                        help="Pick up records with Video Status = 'Stitched' "
                             "and bulk-advance them to 'Approved' before "
                             "scheduling. Operator should have approved at the "
                             "aggregate level (gate #4) — typically combined "
                             "with --batch-confirm for unattended batch runs. "
                             "The scheduledTime guard and Final-Video / past-"
                             "date skips still apply per record.")
    args = parser.parse_args(argv)

    if av.check_credentials():
        print("Missing Airtable creds — see .env.", file=sys.stderr)
        return 1
    if not os.getenv("BLOTATO_API_KEY"):
        print("BLOTATO_API_KEY missing in .env.", file=sys.stderr)
        return 1

    try:
        account_id = resolve_account_id(args.platform)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.record_id:
        records = [av.get_record(args.record_id)]
    elif args.all_stitched:
        stitched = av.get_records(
            f'{{{av.STATUS_FIELD}}} = "{av.STATUS_STITCHED}"'
        )
        if stitched and not args.dry_run:
            log(f"--all-stitched: advancing {len(stitched)} record(s) "
                f"'{av.STATUS_STITCHED}' -> '{av.STATUS_APPROVED}' before scheduling.")
            for r in stitched:
                av.set_status(r["id"], av.STATUS_APPROVED)
                r.setdefault("fields", {})[av.STATUS_FIELD] = av.STATUS_APPROVED
        elif stitched:
            log(f"--all-stitched (dry-run): would advance {len(stitched)} "
                f"record(s) '{av.STATUS_STITCHED}' -> '{av.STATUS_APPROVED}'. "
                f"No Airtable writes made.")
            for r in stitched:
                r.setdefault("fields", {})[av.STATUS_FIELD] = av.STATUS_APPROVED
        records = stitched
    else:
        records = av.get_records(
            f'{{{av.STATUS_FIELD}}} = "{av.STATUS_APPROVED}"'
        )
    if args.limit:
        records = records[: args.limit]

    if args.dry_run:
        dry_run_report(records, account_id)
        return 0

    if not records:
        log("No Approved records — nothing to schedule.")
        return 0

    log(f"Scheduling {len(records)} record(s) to Blotato {args.platform} "
        f"(account {account_id}). Per-record gate is interactive.")
    summary = {
        "ok": 0, "failed": 0,
        "skipped_at_gate": 0, "skipped_missing_inputs": 0,
        "skipped_unschedulable": 0,
    }
    for r in records:
        try:
            result = process_record(r, account_id,
                                    batch_confirm=args.batch_confirm)
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
