"""Verify all 8 Airtable records reflect the v2 re-schedule:
   - Scheduled Date == new May 15-22 dates
   - Final Video attachment present (v2 filename)
   - Video Status == Scheduled
"""
from tools import airtable_video as av

IDS = [
    ("Day 3",  "rec4cuKlnZwe0Slag"),
    ("Day 13", "rec7FO4Yw2JOes9UQ"),
    ("Day 14", "rec7rlJaPz1iVNTzw"),
    ("Day 15", "recEG1hfayCdXU7Qu"),
    ("Day 17", "recEmXiRyXHZPbsKN"),
    ("Day 18", "rec5g78UeoYm5ntca"),
    ("Day 21", "rec5iPo35NwtZNZoK"),
    ("Day 29", "rec6dGknAQZTqJiYM"),
]
for label, rec_id in IDS:
    r = av.get_record(rec_id)
    f = r.get("fields", {})
    fv = (f.get("Final Video") or [{}])[0]
    fname = fv.get("filename", "<NONE>")[:55]
    sched = f.get("Scheduled Date", "<NONE>")
    status = f.get(av.STATUS_FIELD, "?")
    print(f"  {label:7s} {rec_id} [{status:>10}] sched={sched}  file={fname}")
