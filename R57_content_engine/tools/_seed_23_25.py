"""Seed R57 stage-0 for scenarios 23-25 (Day 29-31 prerequisites)."""
import sys
import time
from pathlib import Path

# Ensure we can import tools.* by being in R57_content_engine
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import airtable, image_gen

TARGET_IDS = [
    "recrYjb3Omgp6dCd0",  # 23 glas-umgekippt
    "recvjTUabMn7Tz0Ix",  # 24 beim-umzug
    "recTH01CBrSciCL2c",  # 25 schluessel-verloren
]


def main():
    all_recs = airtable.get_records('FIND("Schaden v1 - R57 - ", {Ad Name})')
    recs_by_id = {r["id"]: r for r in all_recs}
    t0 = time.time()
    print("=== R57 seed scenarios 23-25 (3 records, 1 var each) ===")
    ok = 0
    for i, rid in enumerate(TARGET_IDS, 1):
        rec = recs_by_id.get(rid)
        if not rec:
            print(f"[{i}/3] MISSING {rid}")
            continue
        name = rec.get("fields", {}).get("Ad Name", "?")
        tstart = time.time()
        image_gen.generate_for_record(rec, num_variations=1)
        print(f"[{i}/3] OK {rid} {name[:55]} ({time.time()-tstart:.1f}s)")
        ok += 1
    print(f"Done. OK={ok}/3  Wall={time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
