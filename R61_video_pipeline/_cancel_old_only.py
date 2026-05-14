"""One-shot: cancel ONLY the original 8 v1 Blotato submissions.

The resubmit phase already succeeded (8 new submissions are scheduled with v2
URLs). The cancel phase had failed because Blotato's DELETE rejected empty
JSON bodies. This script retries the cancel-only step with the corrected
body, leaving the new v2 submissions intact.
"""
from tools.blotato_reschedule_v2 import cancel_submission, EXISTING_SUBMISSIONS, log

log("CANCEL-ONLY retry for original v1 submissions")
ok = 0
fail = 0
for rec_id, sub_id in EXISTING_SUBMISSIONS.items():
    success, note = cancel_submission(sub_id)
    if success:
        log(f"  CANCEL ok    {rec_id}  sub={sub_id}  ({note})")
        ok += 1
    else:
        log(f"  CANCEL FAIL  {rec_id}  sub={sub_id}  ({note})")
        fail += 1
log(f"Summary: cancelled={ok} failed={fail}")
