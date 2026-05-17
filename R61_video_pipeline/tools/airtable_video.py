"""
Airtable helper for the R61 Video table.

Mirrors the R57 tools/airtable.py shape but is hard-pointed at the
`Video` table (id `tbl1hd8yprLTZia4c`) in base `appC3HqG42ftswOvw`.

Credentials are loaded from R61_video_pipeline/.env via python-dotenv.
"""

import os
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appC3HqG42ftswOvw")
AIRTABLE_API_URL = "https://api.airtable.com/v0"

TABLE_NAME = "Video"
TABLE_ID = "tbl1hd8yprLTZia4c"

STATUS_FIELD = "Video Status"
STATUS_PENDING = "Pending"
STATUS_FRAMES_GENERATED = "Frames Generated"
STATUS_CLIP_GENERATED = "Clip Generated"
STATUS_RAW_ATTACHED = "Raw Attached"
STATUS_VOICEOVER_DONE = "Voiceover Done"
STATUS_STITCHED = "Stitched"
STATUS_APPROVED = "Approved"
STATUS_REJECTED = "Rejected"
STATUS_SCHEDULED = "Scheduled"


def check_credentials():
    missing = []
    if not AIRTABLE_API_KEY:
        missing.append("AIRTABLE_API_KEY")
    if not AIRTABLE_BASE_ID:
        missing.append("AIRTABLE_BASE_ID")
    return missing


def _headers():
    return {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }


def _table_url():
    table = quote(TABLE_NAME, safe="")
    return f"{AIRTABLE_API_URL}/{AIRTABLE_BASE_ID}/{table}"


def get_records(filter_formula=None, max_records=None):
    """Return all records matching the filter, with pagination."""
    params = {}
    if filter_formula:
        params["filterByFormula"] = filter_formula
    if max_records is not None:
        params["maxRecords"] = max_records

    all_records = []
    offset = None
    while True:
        if offset:
            params["offset"] = offset
        resp = requests.get(_table_url(), headers=_headers(), params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Airtable query failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return all_records


def get_record(record_id):
    resp = requests.get(f"{_table_url()}/{record_id}", headers=_headers(), timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Airtable get failed ({resp.status_code}): {resp.text}")
    return resp.json()


def update_record(record_id, fields):
    resp = requests.patch(
        f"{_table_url()}/{record_id}",
        headers=_headers(),
        json={"fields": fields},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Airtable update failed ({resp.status_code}): {resp.text}")
    return resp.json()


def get_pending_videos():
    """Records where Video Status = Pending."""
    return get_records(f'{{{STATUS_FIELD}}} = "{STATUS_PENDING}"')


def get_source_image_url(record):
    """First attachment URL on the Source Image field, or None."""
    atts = record.get("fields", {}).get("Source Image") or []
    if not atts:
        return None
    return atts[0].get("url")


def attach_urls_to_field(record_id, field_name, urls, filenames=None):
    """Set an attachment field to one or more hosted URLs."""
    if filenames is None:
        filenames = [None] * len(urls)
    attachments = []
    for url, name in zip(urls, filenames):
        item = {"url": url}
        if name:
            item["filename"] = name
        attachments.append(item)
    return update_record(record_id, {field_name: attachments})


def set_status(record_id, status_value):
    return update_record(record_id, {STATUS_FIELD: status_value})


def create_field(name, field_type, description=None, options=None):
    """Add a new field to the Video table via the metadata API.

    `field_type` must be a valid Airtable field type, e.g.:
      - "multipleAttachments" for attachment fields
      - "multilineText" for long-text fields
      - "singleLineText" for short-text fields

    Requires the personal access token to have `schema.bases:write` scope on
    this base. Idempotent: returns the existing field unchanged (HTTP 422
    "DUPLICATE_OR_EMPTY_FIELD_NAME") if the field already exists.
    """
    url = f"{AIRTABLE_API_URL}/meta/bases/{AIRTABLE_BASE_ID}/tables/{TABLE_ID}/fields"
    body = {"name": name, "type": field_type}
    if description:
        body["description"] = description
    if options:
        body["options"] = options
    resp = requests.post(url, headers=_headers(), json=body, timeout=30)
    if resp.status_code == 422 and "DUPLICATE_OR_EMPTY_FIELD_NAME" in resp.text:
        return {"already_exists": True, "name": name}
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Airtable create_field failed ({resp.status_code}): {resp.text}")
    return resp.json()


if __name__ == "__main__":
    missing = check_credentials()
    if missing:
        print(f"Missing env vars: {', '.join(missing)} (in {ENV_PATH})")
        raise SystemExit(1)
    records = get_records(max_records=5)
    print(f"Connected to base {AIRTABLE_BASE_ID}, table '{TABLE_NAME}' ({TABLE_ID}).")
    print(f"Sample records returned: {len(records)}")
    for r in records:
        f = r.get("fields", {})
        print(f"  - {r['id']}: Index={f.get('Index')} status={f.get(STATUS_FIELD)} ad={f.get('Ad Name')}")
