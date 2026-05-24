"""Link R57 Generated Image 1 -> R61 Source Image for Day 29-31."""
import sys
import re
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "R57_content_engine"))
from tools import airtable as r57_at  # noqa

# Load R61 airtable_video directly by file path to avoid package collision
spec = importlib.util.spec_from_file_location(
    "r61_airtable_video",
    REPO_ROOT / "R61_video_pipeline" / "tools" / "airtable_video.py",
)
r61_at = importlib.util.module_from_spec(spec)
sys.modules["r61_airtable_video"] = r61_at
spec.loader.exec_module(r61_at)


PAIRS = [
    # (R61 Day, R61 record_id, R57 record_id, scenario_label)
    (29, "recc01n1tMzC9aiHv", "recrYjb3Omgp6dCd0", "glas-umgekippt"),
    (30, "recZ5AxNrEnYPHexW", "recvjTUabMn7Tz0Ix", "beim-umzug"),
    (31, "recuu2pTCKRlHM0uR", "recTH01CBrSciCL2c", "schluessel-verloren"),
]


def main():
    print("=== Link Day 29-31 R61 Source Image from R57 Generated Image 1 ===")
    ok = 0
    for day, r61_id, r57_id, slug in PAIRS:
        r57 = r57_at.get_records(f'RECORD_ID() = "{r57_id}"')
        if not r57:
            print(f"  Day {day} FAIL: R57 record {r57_id} not found")
            continue
        gi1 = r57[0].get("fields", {}).get("Generated Image 1") or []
        if not gi1:
            print(f"  Day {day} FAIL: R57 {r57_id} has no Generated Image 1 yet")
            continue
        src_url = gi1[0].get("url")
        src_filename = gi1[0].get("filename") or f"{r57_id}_source.png"
        r61_at.update_record(r61_id, {
            "Source Image": [{"url": src_url, "filename": src_filename}],
        })
        print(f"  Day {day} {r61_id} <- {r57_id} ({slug})")
        ok += 1
    print(f"Linked={ok}/3")


if __name__ == "__main__":
    main()
