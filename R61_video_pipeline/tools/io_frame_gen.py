"""
Frame generation for the R61 IO table (intro / outro brand-mark animations).

Different shape from tools/frame_gen.py:
- Reads from the IO table, not Video.
- Two modes:
    * default (text-to-image): nano-banana-pro generates the logo from prompt.
      Risk: model may invent wing shapes; fine for first-pass exploration.
    * --reference-image PATH: nano-banana-pro/edit uses the real logo PNG as
      a composition anchor. Wing shapes/proportions/color are LOCKED to the
      reference — only background and lighting vary between first/last frame.
      This is the right mode when the client-supplied logo must not change.
- Splits the single base Prompt into a "first frame cold" variant (logo not
  visible yet, central area empty/dark per the brief) and a "last frame wings
  fully visible" variant (logo fully rendered).

Usage:
    python -m tools.io_frame_gen --dry-run
    python -m tools.io_frame_gen
    python -m tools.io_frame_gen --record-id recXXXX
    python -m tools.io_frame_gen --record-id recXXXX \\
        --reference-image ../R57_content_engine/references/inputs/_ascii/provinzial_logo_transparent.png
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

if os.getenv("FAL_KEY") is None and os.getenv("FAL_API_KEY"):
    os.environ["FAL_KEY"] = os.environ["FAL_API_KEY"]

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

from tools import airtable_video as av  # noqa: E402

IO_TABLE_NAME = "IO"
IO_TABLE_ID = "tblkRJ2e0eSBxmrYx"
LOG_PATH = PROJECT_ROOT / "references" / "outputs" / "io_frame_gen_run.log"

FAL_T2I_ENDPOINT = "fal-ai/nano-banana-pro"
FAL_T2I_FALLBACK = "fal-ai/nano-banana"
FAL_EDIT_ENDPOINT = "fal-ai/nano-banana-pro/edit"
FAL_EDIT_FALLBACK = "fal-ai/nano-banana/edit"

COST_PER_IMAGE_USD = 0.04
FIRE_WORDS = {"go", "fire", "yes", "run it", "run", "ship"}


def log(msg):
    ts = dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _io_url():
    return f"{av.AIRTABLE_API_URL}/{av.AIRTABLE_BASE_ID}/{quote(IO_TABLE_NAME, safe='')}"


def _io_headers():
    return {
        "Authorization": f"Bearer {av.AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }


def get_io_records(filter_formula=None):
    params = {}
    if filter_formula:
        params["filterByFormula"] = filter_formula
    resp = requests.get(_io_url(), headers=_io_headers(), params=params, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"IO query failed: {resp.text}")
    return resp.json().get("records", [])


def update_io_record(record_id, fields):
    resp = requests.patch(
        f"{_io_url()}/{record_id}",
        headers=_io_headers(),
        json={"fields": fields},
        timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"IO update failed: {resp.text}")
    return resp.json()


def split_prompt(base_prompt, io_type, reference_locked=False):
    """Take the base brand-mark prompt and emit (first, last) variants.

    First = scene cold, wings/logo not yet visible.
    Last  = wings/logo fully visible, brand mark crisp.

    When reference_locked=True, the reference image (the real client logo) is
    passed alongside the prompt via the edit endpoint. The prompts then
    forbid the model from redrawing the wings — only background/lighting
    differ between the two frames.
    """
    base = (base_prompt or "").strip()
    io_type_l = (io_type or "").strip().lower()

    if reference_locked:
        if io_type_l == "intro":
            bg_clause = (
                "Background is solid Provinzial green #005940 filling the full "
                "9:16 frame. Warm cinematic light, subtle volumetric light rays."
            )
            first_state = (
                "The reference logo is present at the SAME centered position, "
                "size, rotation, and orientation as in the reference image, but "
                "is dimmed deep into shadow — barely perceptible, just emerging "
                "from the dark green. Almost black-on-green. No glow yet."
            )
            last_state = (
                "The reference logo is centered, fully visible, crisp, glowing "
                "warmly. Composition, position, scale, and wing shapes are "
                "IDENTICAL to the reference."
            )
        elif io_type_l == "outro":
            bg_clause = (
                "Background is pure flat white #FFFFFF filling the full 9:16 "
                "frame. Clean, minimal, no gradient, no texture."
            )
            first_state = (
                "The reference logo is present at the SAME centered position, "
                "size, rotation, and orientation as in the reference image, but "
                "is faded almost to invisibility against the white — barely a "
                "ghost of the wings, on the edge of imperceptible."
            )
            last_state = (
                "The reference logo is centered, fully visible, crisp, "
                "fully opaque. Composition, position, scale, and wing shapes "
                "are IDENTICAL to the reference."
            )
        else:
            bg_clause = "Background per the base prompt."
            first_state = "The reference logo is faded/dim, not yet fully visible."
            last_state = "The reference logo is fully visible, crisp."

        lock_clause = (
            "CRITICAL LOCK on logo identity: the wing shapes, proportions, "
            "color (#FFD000 yellow), stroke style, and silhouette MUST match "
            "the reference image EXACTLY. Do NOT redraw, restyle, simplify, "
            "redesign, or reinterpret the wings. Treat the reference logo as "
            "the client-supplied final asset that must be preserved pixel-"
            "faithful in shape. Only the BACKGROUND and LIGHTING/VISIBILITY "
            "of the logo change between first and last frame. 9:16 vertical. "
            "No on-image text, no people, no extra elements."
        )

        first = (
            f"FIRST FRAME — {base} {bg_clause} {first_state} {lock_clause}"
        )
        last = (
            f"LAST FRAME — {base} {bg_clause} {last_state} {lock_clause}"
        )
        return first, last

    # Legacy text-to-image branch (no reference) — kept for back-compat.
    first = (
        f"FIRST FRAME (scene cold): {base} "
        f"CRITICAL OVERRIDE for this frame only — the golden wings logo "
        f"is NOT yet visible. The central area where the logo would "
        f"sit is empty (for an intro: in deep shadow against the green; "
        f"for an outro: a perfectly clean blank white area). No logo, "
        f"no glyph, no mark on screen. Same composition, same palette, "
        f"same aspect 9:16 vertical — only the brand mark is held back. "
        f"Cinematic, calm, professional, no on-image text."
    )
    last = (
        f"LAST FRAME (brand mark fully visible): {base} "
        f"The golden wings logo #FFD000 is centered, fully rendered, "
        f"crisp and clearly readable as the Provinzial Goldene Flügel "
        f"mark. Wings are symmetric, two stylized golden wings meeting "
        f"in the center. 9:16 vertical. Cinematic, calm, professional, "
        f"no on-image text."
    )
    return first, last


def submit_text_to_image(prompt, aspect_ratio="9:16"):
    import fal_client
    arguments = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "num_images": 1,
        "output_format": "png",
    }
    try:
        return fal_client.submit(FAL_T2I_ENDPOINT, arguments=arguments)
    except Exception as e:
        log(f"Primary endpoint {FAL_T2I_ENDPOINT} rejected ({e}); falling back to {FAL_T2I_FALLBACK}.")
        return fal_client.submit(FAL_T2I_FALLBACK, arguments=arguments)


def submit_reference_edit(prompt, reference_url, aspect_ratio="9:16"):
    """Reference-anchored nano-banana edit. Logo identity is locked via image_urls."""
    import fal_client
    arguments = {
        "prompt": prompt,
        "image_urls": [reference_url],
        "aspect_ratio": aspect_ratio,
        "num_images": 1,
        "output_format": "png",
    }
    try:
        return fal_client.submit(FAL_EDIT_ENDPOINT, arguments=arguments)
    except Exception as e:
        log(f"Primary edit endpoint {FAL_EDIT_ENDPOINT} rejected ({e}); falling back to {FAL_EDIT_FALLBACK}.")
        return fal_client.submit(FAL_EDIT_FALLBACK, arguments=arguments)


def upload_reference_to_fal(local_path):
    """Upload a local image to Fal storage and return the hosted URL."""
    import fal_client
    return fal_client.upload_file(str(local_path))


def extract_image_url(result):
    images = (result or {}).get("images") or []
    return images[0].get("url") if images else None


def confirm_cost(num_records):
    total_images = num_records * 2
    total_usd = total_images * COST_PER_IMAGE_USD
    print()
    print("=" * 60)
    print("COST ESTIMATE — IO frame generation")
    print("=" * 60)
    print(f"  Records to process : {num_records}")
    print(f"  Images per record  : 2 (first frame + last frame)")
    print(f"  Total images       : {total_images}")
    print(f"  Model              : Nano Banana Pro (Fal text-to-image)")
    print(f"  $ per image        : ${COST_PER_IMAGE_USD:.2f}")
    print(f"  TOTAL              : ${total_usd:.2f}")
    print("=" * 60)
    print(f"Type one of: {sorted(FIRE_WORDS)} to proceed, anything else aborts.")
    return input("> ").strip().lower() in FIRE_WORDS


def process_record(record, reference_fal_url=None):
    rec_id = record["id"]
    fields = record.get("fields", {})
    io_type = fields.get("Type") or "?"
    base_prompt = (fields.get("Prompt") or "").strip()

    log(f"START {rec_id} Type={io_type} "
        f"mode={'reference-locked' if reference_fal_url else 'text-to-image'}")
    if not base_prompt:
        log(f"SKIP {rec_id}: empty Prompt")
        return "skipped"

    reference_locked = reference_fal_url is not None
    first_prompt, last_prompt = split_prompt(
        base_prompt, io_type, reference_locked=reference_locked,
    )

    if reference_locked:
        h_first = submit_reference_edit(first_prompt, reference_fal_url)
        h_last = submit_reference_edit(last_prompt, reference_fal_url)
    else:
        h_first = submit_text_to_image(first_prompt)
        h_last = submit_text_to_image(last_prompt)

    first_url = extract_image_url(h_first.get())
    last_url = extract_image_url(h_last.get())
    if not first_url or not last_url:
        log(f"FAIL {rec_id}: missing result URL")
        return "failed"

    update_io_record(rec_id, {
        "First Frame": [{"url": first_url, "filename": f"{io_type.lower()}_first.png"}],
        "Last Frame": [{"url": last_url, "filename": f"{io_type.lower()}_last.png"}],
        "Status": "Frames Generated",
    })
    log(f"DONE  {rec_id} Type={io_type} first={first_url} last={last_url}")
    return "ok"


def dry_run_report(records):
    print()
    print(f"DRY RUN — IO table ({IO_TABLE_ID})")
    print(f"Records matched: {len(records)}")
    for r in records:
        f = r.get("fields", {})
        first, last = split_prompt(f.get("Prompt", ""), f.get("Type", ""))
        print(f"  - {r['id']}  Type={f.get('Type')!r}  Status={f.get('Status')!r}")
        print(f"      Base prompt ({len(f.get('Prompt') or '')} chars): "
              f"{(f.get('Prompt') or '')[:120]}...")
        print(f"      First-frame prompt ({len(first)} chars): {first[:140]}...")
        print(f"      Last-frame prompt  ({len(last)} chars): {last[:140]}...")
    total = len(records) * 2
    print(f"Would generate {total} images on Fal (~${total * COST_PER_IMAGE_USD:.2f}).")
    print("No API calls were made.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="R61 IO frame generation")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--record-id", default=None,
                        help="Process this single IO record id, bypassing the Pending filter.")
    parser.add_argument("--reference-image", default=None,
                        help="Path to a logo PNG to use as the composition "
                             "anchor. When set, the nano-banana-pro/edit "
                             "endpoint is used and prompts lock logo identity "
                             "to this reference (wings cannot be redrawn).")
    parser.add_argument("--confirm", default=None,
                        help="Pass a fire word to bypass the interactive cost "
                             "prompt (e.g. --confirm go). Needed for "
                             "non-interactive runs on Windows.")
    args = parser.parse_args(argv)

    if av.check_credentials():
        print("Missing AIRTABLE_API_KEY/BASE_ID", file=sys.stderr)
        return 1
    if not args.dry_run and not os.getenv("FAL_KEY"):
        print("FAL_KEY missing — needed for paid run.", file=sys.stderr)
        return 1

    if args.record_id:
        records = [r for r in get_io_records() if r["id"] == args.record_id]
    else:
        records = get_io_records('{Status} = "Pending"')

    if args.dry_run:
        dry_run_report(records)
        return 0

    if not records:
        log("No matching IO records.")
        return 0

    if args.confirm is not None:
        if args.confirm.strip().lower() not in FIRE_WORDS:
            print(f"--confirm value {args.confirm!r} is not a fire word. "
                  f"Allowed: {sorted(FIRE_WORDS)}", file=sys.stderr)
            return 1
        total_usd = len(records) * 2 * COST_PER_IMAGE_USD
        log(f"Cost gate bypassed via --confirm {args.confirm!r}. "
            f"Approved: {len(records)} record(s) x 2 images = "
            f"${total_usd:.2f}.")
    else:
        if not confirm_cost(len(records)):
            log("Aborted at cost gate.")
            return 1

    # Optional: upload the reference logo to Fal storage once so all
    # subsequent edit submits can pass the same hosted URL.
    reference_fal_url = None
    if args.reference_image:
        ref_path = Path(args.reference_image)
        if not ref_path.is_absolute():
            ref_path = (PROJECT_ROOT / ref_path).resolve()
        if not ref_path.exists():
            print(f"Reference image not found: {ref_path}", file=sys.stderr)
            return 1
        log(f"Uploading reference logo to Fal: {ref_path}")
        reference_fal_url = upload_reference_to_fal(ref_path)
        log(f"  -> {reference_fal_url}")

    log(f"Confirmed. Processing {len(records)} IO record(s).")
    summary = {"ok": 0, "failed": 0, "skipped": 0}
    for r in records:
        try:
            summary[process_record(r, reference_fal_url=reference_fal_url)] += 1
        except Exception as e:
            log(f"FAIL {r['id']}: {e}")
            summary["failed"] += 1

    log(f"IO frame gen complete. Summary: {summary}")
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
