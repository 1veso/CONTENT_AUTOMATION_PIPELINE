"""
Phase 3: Generate all 30 Provinzial images using Nano Banana Pro via Google AI Studio.
1 variation per record. Reference images are the 3 brand assets (ASCII copies).
"""
import sys
sys.path.insert(0, ".")

from tools.airtable import get_pending_images
from tools.image_gen import generate_batch

REFERENCE_PATHS = [
    "references/inputs/_ascii/provinzial_logo_transparent.png",
    "references/inputs/_ascii/provinzial_branding_kit.jpg",
    "references/inputs/_ascii/provinzial_design_richtlinien.jpg",
]


def main():
    records = get_pending_images()
    print(f"Pending records: {len(records)}")

    if not records:
        print("Nothing to generate.")
        return

    results = generate_batch(
        records,
        reference_paths=REFERENCE_PATHS,
        model="nano-banana-pro",
        provider="google",
        num_variations=1,
    )

    succeeded = sum(1 for r in results if r)
    print(f"\nDone. {succeeded}/{len(records)} succeeded.")


if __name__ == "__main__":
    main()
