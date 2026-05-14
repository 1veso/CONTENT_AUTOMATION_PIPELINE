"""One-shot publisher for the already-rendered Day 3 v2 mp4.

This skips re-rendering Day 3 (already done) and just uploads the existing
final mp4 to R2 and updates Airtable. Used because the v2 stitcher tool
re-renders unconditionally; Day 3 was the manual proof-of-concept and is
already at references/outputs/final/v2/.
"""
from pathlib import Path
from tools.hf_stitch import publish_to_r2_and_airtable, FINAL_V2_DIR, log

REC_ID = "rec4cuKlnZwe0Slag"
MP4_NAME = "3_Provinzial_-_Day_3_-_NRW_Kleinstadt_Café_[Regional_&_Gemeins.mp4"

mp4_path = FINAL_V2_DIR / MP4_NAME
assert mp4_path.exists(), f"missing: {mp4_path}"
log(f"PUBLISH-ONLY {REC_ID}  ({mp4_path.stat().st_size/1e6:.1f} MB)")
url = publish_to_r2_and_airtable(REC_ID, mp4_path, MP4_NAME)
log(f"DONE  {REC_ID}  → {url}")
