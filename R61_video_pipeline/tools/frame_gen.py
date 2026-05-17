"""
R61 Step 1 — Frame generation.

Reads pending records from the Airtable Video table, generates a first frame
and a last frame for each via Fal.ai (Nano Banana Pro reference-guided edit)
using the Source Image as the visual anchor, uploads results back to Airtable,
and advances Video Status from "Pending" to "Frames Generated".

Prompts are grounded in references/docs/provinzial_BRAND.md (Provinzial green
palette, warm authentic German lifestyle, never staged).

Hard cost-approval gate (per .claude/skills/cinematic-ads/SKILL.md Gate 1):
the tool quotes records × 2 × $/image and waits for an explicit fire word
("go", "fire", "yes", "run it", "ship") before any paid API call. Re-quote
on every run; approval does not carry forward.

Usage:
    python -m tools.frame_gen --dry-run          # read-only verification
    python -m tools.frame_gen                    # interactive paid run
    python -m tools.frame_gen --limit 3          # cap records this run
"""

import argparse
import datetime as dt
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

# Force UTF-8 stdout so Airtable strings with em-dashes etc. don't crash
# the Windows cp1252 console.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

# Bridge FAL_KEY for fal_client (it reads FAL_KEY, our env may use either).
if os.getenv("FAL_KEY") is None and os.getenv("FAL_API_KEY"):
    os.environ["FAL_KEY"] = os.environ["FAL_API_KEY"]

# Local imports after dotenv so env vars are populated.
from tools import airtable_video as av  # noqa: E402
from tools import _gates  # noqa: E402

LOG_PATH = PROJECT_ROOT / "references" / "outputs" / "frame_gen_run.log"
BRAND_DOC = PROJECT_ROOT / "references" / "docs" / "provinzial_BRAND.md"

# Fal endpoint for reference-guided edits with Nano Banana Pro.
# Confirmed callable on Fal: fal-ai/nano-banana-pro/edit accepts image_urls
# for reference-anchored generation. If unavailable in this account, swap to
# fal-ai/nano-banana/edit (used by R57) — same call shape.
FAL_IMAGE_ENDPOINT = "fal-ai/nano-banana-pro/edit"
FAL_IMAGE_ENDPOINT_FALLBACK = "fal-ai/nano-banana/edit"

# Approximate Fal cost per Nano Banana Pro image, used for the cost quote.
# Source: R57 tools/config.py COSTS table. Verify at fal.ai/models before
# treating as authoritative for billing.
COST_PER_IMAGE_USD = 0.04

FIRE_WORDS = {"go", "fire", "yes", "run it", "run", "ship"}

# Narrative-structure mode (Block 3). When R61_NARRATIVE_MODE=true AND the
# record has a populated `Voiceover Segments` JSON field, the first-frame
# prompt incorporates the Hook beat text and the last-frame prompt
# incorporates the CTA beat text. Falls back to pillar-only prompts otherwise.
NARRATIVE_MODE = os.environ.get("R61_NARRATIVE_MODE", "").lower() in ("1", "true", "yes")

# Content-pillar tags appear in the Ad Name like `... [Regional & Gemeinschaft]`.
# Different pillars need different last-frame beats so Higgsfield has real
# motion to interpolate.
LIFESTYLE_PILLARS = {
    "Sicherheit im Alltag",
    "Vorsorge & Zukunft",
    "Regional & Gemeinschaft",
}
ACTION_PILLARS = {
    "Schaden & Service",
    "Produktaufklärung",
}

BRAND_ANCHOR = (
    "Brand: Provinzial (German regional insurance). Palette anchored on "
    "Provinzial green #005940 and Flügelgelb #FFD000, with secondary "
    "Türkisgrün #1D724A and Opalgrün #006646; never the restricted Lachs "
    "#EC672F. Aesthetic: warm, natural light, authentic German everyday "
    "life — real homes, families, communities in NRW. Trustworthy, "
    "grounded, clean. Never staged stock-photo, never flashy, never "
    "fear-mongering. Bottom-right yellow wings watermark (Goldene Flügel)."
)


def log(msg):
    """Append a timestamped line to the run log and echo to stdout."""
    ts = dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def detect_pillar(ad_name):
    """Extract the [Pillar Name] tag from the end of the Ad Name string."""
    m = re.search(r"\[([^\]]+)\]\s*$", ad_name or "")
    return m.group(1).strip() if m else None


def pillar_kind(pillar):
    """Map a pillar name to 'lifestyle' or 'action'. Unknown -> lifestyle."""
    if pillar in ACTION_PILLARS:
        return "action"
    return "lifestyle"


def _narrative_beats(record):
    """Return (hook_text, cta_text) from the record's Voiceover Segments JSON.

    Returns ("", "") if NARRATIVE_MODE is off, the field is missing/empty, or
    parsing fails. Caller treats empty strings as "no narrative override".
    """
    if not NARRATIVE_MODE:
        return "", ""
    raw = (record.get("fields", {}) or {}).get("Voiceover Segments") or ""
    if not raw.strip():
        return "", ""
    try:
        import json as _json
        parsed = _json.loads(raw)
    except (ValueError, TypeError):
        return "", ""
    hook_text = ""
    cta_text = ""
    if isinstance(parsed, list):
        for seg in parsed:
            if isinstance(seg, dict):
                if seg.get("name") == "hook":
                    hook_text = (seg.get("text") or "").strip()
                elif seg.get("name") == "cta":
                    cta_text = (seg.get("text") or "").strip()
    elif isinstance(parsed, dict):
        hook_text = (parsed.get("hook") or "").strip()
        cta_text = (parsed.get("cta") or "").strip()
    return hook_text, cta_text


def build_prompts(record):
    """Return (first_frame_prompt, last_frame_prompt, pillar) for one record.

    Both prompts inherit the Source Image as the visual anchor and lean on
    Ad Name + Caption for variation. First frame is composition-locked and
    static. Last frame is composition-locked but introduces ONE clear beat,
    where the beat shape depends on the detected content pillar so Higgsfield
    has real motion to interpolate.

    When NARRATIVE_MODE is on AND the record has Voiceover Segments populated,
    the first-frame prompt incorporates the Hook beat (real human moment) and
    the last-frame prompt incorporates the CTA beat (resolution/invitation).
    """
    fields = record.get("fields", {})
    ad_name = (fields.get("Ad Name") or "Provinzial moment").strip()
    caption = (fields.get("Caption") or "").strip()
    pillar = detect_pillar(ad_name)
    kind = pillar_kind(pillar)
    hook_text, cta_text = _narrative_beats(record)

    caption_line = f"Caption context: {caption}" if caption else ""
    hook_clause = (
        f"NARRATIVE HOOK BEAT (0-3s): '{hook_text}' — the first frame depicts "
        f"this real human moment, no product visible, no brand reference. "
        if hook_text else ""
    )
    cta_clause = (
        f"NARRATIVE CTA BEAT (11-15s): '{cta_text}' — the last frame depicts "
        f"the resolution/invitation moment matching this voiceover line. "
        if cta_text else ""
    )

    first = (
        f"FIRST FRAME for the ad '{ad_name}'. STRICT COMPOSITION LOCK: "
        f"match the exact framing, subject count, subject positions, and "
        f"overall composition of the reference image. Do NOT recompose. "
        f"Do NOT add or remove subjects. Do NOT change camera angle, "
        f"distance, or crop. Same people in the same places, same "
        f"wardrobe, same props, same background elements in the same "
        f"locations within the frame. The scene is cold and static — no "
        f"motion yet, no expression change yet, no parallax. This is "
        f"frame zero of the clip. {hook_clause}"
        f"{caption_line} {BRAND_ANCHOR} "
        f"Cinematic 9:16 vertical, warm natural color grading toward the "
        f"green palette, no on-image text, no logos other than the small "
        f"yellow wings bottom-right."
    ).strip()

    if kind == "lifestyle":
        beat_clause = (
            "ONE clear emotional beat happens — pick the single most natural "
            "option for this scene from: a real laugh breaking, a hand "
            "reaching to touch another, a nod of recognition, a child "
            "running into the existing frame from the side, a door swinging "
            "open, a head turning toward a loved one, a glance up from the "
            "activity. Exactly one beat, warm and earned, that a human "
            "viewer feels. The beat must be visually distinct enough that "
            "a video model interpolating between first and last frame has "
            "real motion to render — not just a light shift. Choose the "
            "beat that fits the scene; do not stack multiple beats."
        )
    else:
        beat_clause = (
            "ONE clear action beat happens — pick the single most natural "
            "option for this scene from: a phone being picked up to the "
            "ear, a document being signed with a pen meeting paper, a "
            "handshake completing with hands clasped, an agent arriving at "
            "a doorway, a hand pointing decisively at a key clause, a "
            "clipboard or tablet being handed across. Exactly one action "
            "beat that signals resolution and trust. The beat must be "
            "visually distinct enough that a video model interpolating "
            "between first and last frame has real motion to render — "
            "not just a light shift. Choose the beat that fits the scene; "
            "do not stack multiple beats."
        )

    last = (
        f"LAST FRAME for the ad '{ad_name}'. STRICT COMPOSITION LOCK: "
        f"identical composition to the first frame and the reference "
        f"image — same framing, same camera angle and distance, same "
        f"crop, same background, same subject count, same wardrobe, "
        f"same subjects in the same starting positions. {beat_clause} "
        f"Outside that one beat, nothing else moves. No recomposing, "
        f"no zoom, no pan, no added/removed subjects beyond the beat "
        f"itself. The Provinzial product/context remains visible. "
        f"Pillar: {pillar or 'general'}. {cta_clause}"
        f"{caption_line} {BRAND_ANCHOR} "
        f"Cinematic 9:16 vertical, same warm grading, no on-image text, "
        f"yellow wings bottom-right."
    ).strip()

    return first, last, pillar


def download_to_temp(url, suffix=".png"):
    """Pull an Airtable attachment URL down to a temp file for re-upload."""
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return Path(tmp_path)


def upload_to_fal(local_path):
    """Push a local file into Fal storage. Returns the hosted v3 URL."""
    import fal_client  # imported lazily so dry-run never needs the SDK
    return fal_client.upload_file(str(local_path))


def submit_frame(prompt, reference_url, aspect_ratio="9:16"):
    """Submit one Nano Banana Pro edit job. Returns the fal_client handler."""
    import fal_client
    arguments = {
        "prompt": prompt,
        "image_urls": [reference_url],
        "aspect_ratio": aspect_ratio,
        "num_images": 1,
        "output_format": "png",
    }
    try:
        return fal_client.submit(FAL_IMAGE_ENDPOINT, arguments=arguments)
    except Exception as e:
        log(f"Primary endpoint {FAL_IMAGE_ENDPOINT} failed ({e}); "
            f"falling back to {FAL_IMAGE_ENDPOINT_FALLBACK}.")
        return fal_client.submit(FAL_IMAGE_ENDPOINT_FALLBACK, arguments=arguments)


def extract_image_url(result):
    images = (result or {}).get("images") or []
    if not images:
        return None
    return images[0].get("url")


def confirm_cost(num_records):
    total_images = num_records * 2
    total_usd = total_images * COST_PER_IMAGE_USD
    print()
    print("=" * 60)
    print("COST ESTIMATE")
    print("=" * 60)
    print(f"  Records to process : {num_records}")
    print(f"  Images per record  : 2 (first frame + last frame)")
    print(f"  Total images       : {total_images}")
    print(f"  Model              : Nano Banana Pro (Fal — reference edit)")
    print(f"  $ per image        : ${COST_PER_IMAGE_USD:.2f} (approx; verify on fal.ai)")
    print(f"  TOTAL              : ${total_usd:.2f}")
    print("=" * 60)
    print(f"Type one of: {sorted(FIRE_WORDS)} to proceed, anything else aborts.")
    answer = input("> ").strip().lower()
    return answer in FIRE_WORDS


def process_record(record):
    """Run frame gen for one Airtable record. Returns status string."""
    rec_id = record["id"]
    fields = record.get("fields", {})
    ad_name = fields.get("Ad Name") or "(no name)"

    source_url = av.get_source_image_url(record)
    if not source_url:
        log(f"SKIP {rec_id} ({ad_name}): no Source Image attachment")
        return "skipped_no_source"

    first_prompt, last_prompt, pillar = build_prompts(record)

    log(f"START {rec_id} ({ad_name}) pillar='{pillar}' kind={pillar_kind(pillar)}")

    # Mirror the Airtable-hosted source image into Fal storage so the edit
    # endpoint sees a stable, allowed CDN host.
    tmp = download_to_temp(source_url, suffix=Path(urlparse(source_url).path).suffix or ".png")
    try:
        fal_ref_url = upload_to_fal(tmp)
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass

    h_first = submit_frame(first_prompt, fal_ref_url)
    h_last = submit_frame(last_prompt, fal_ref_url)

    first_url = extract_image_url(h_first.get())
    last_url = extract_image_url(h_last.get())
    if not first_url or not last_url:
        log(f"FAIL {rec_id} ({ad_name}): missing result URL")
        return "failed"

    av.update_record(
        rec_id,
        {
            "First Frame Prompt": first_prompt,
            "Last Frame Prompt": last_prompt,
            "First Frame Image": [{"url": first_url, "filename": f"{rec_id}_first.png"}],
            "Last Frame Image": [{"url": last_url, "filename": f"{rec_id}_last.png"}],
            av.STATUS_FIELD: av.STATUS_FRAMES_GENERATED,
        },
    )
    log(f"DONE  {rec_id} ({ad_name}) first={first_url} last={last_url}")
    return "ok"


def dry_run_report(records):
    print()
    print(f"DRY RUN — base {av.AIRTABLE_BASE_ID}, table '{av.TABLE_NAME}' ({av.TABLE_ID})")
    print(f"Pending records matching {{{av.STATUS_FIELD}}} = \"{av.STATUS_PENDING}\": {len(records)}")
    if not records:
        print("  (no rows to process)")
    for r in records:
        f = r.get("fields", {})
        src = av.get_source_image_url(r) or "<missing>"
        first, last, pillar = build_prompts(r)
        kind = pillar_kind(pillar)
        print(f"  - {r['id']}  Index={f.get('Index')!r}  Ad Name={f.get('Ad Name')!r}")
        print(f"      Pillar: {pillar!r} -> {kind}")
        print(f"      Source Image: {src[:80]}{'...' if len(src) > 80 else ''}")
        print(f"      First-frame prompt ({len(first)} chars): {first[:140]}...")
        print(f"      Last-frame prompt  ({len(last)} chars): {last[:140]}...")
    total_images = len(records) * 2
    total_usd = total_images * COST_PER_IMAGE_USD
    print(f"Would generate {total_images} images via Nano Banana Pro on Fal "
          f"(~${total_usd:.2f} at ${COST_PER_IMAGE_USD:.2f}/image, approx).")
    print("No API calls were made.")


def _beat_texts(record):
    """Return {'hook': str, 'lösung': str, 'cta': str} from Voiceover Segments.

    Used by Block 9 (hook/lösung) and Block 11 (cta). Returns empty strings
    for missing/unparseable/absent beats — the caller decides whether that's
    fatal for the specific beat being processed.
    """
    out = {"hook": "", "lösung": "", "cta": ""}
    raw = (record.get("fields", {}) or {}).get("Voiceover Segments") or ""
    if not raw.strip():
        return out
    try:
        import json as _json
        parsed = _json.loads(raw)
    except (ValueError, TypeError):
        return out
    if isinstance(parsed, list):
        for seg in parsed:
            if isinstance(seg, dict):
                n = seg.get("name")
                txt = (seg.get("text") or "").strip()
                if n == "hook":
                    out["hook"] = txt
                elif n in ("lösung", "loesung"):
                    out["lösung"] = txt
                elif n == "cta":
                    out["cta"] = txt
    elif isinstance(parsed, dict):
        out["hook"] = (parsed.get("hook") or "").strip()
        out["lösung"] = (parsed.get("lösung") or parsed.get("loesung") or "").strip()
        out["cta"] = (parsed.get("cta") or "").strip()
    return out


def _hook_lösung_beats(record):
    """Back-compat shim: returns (hook, lösung) tuple. New code should call
    `_beat_texts` directly."""
    b = _beat_texts(record)
    return b["hook"], b["lösung"]


def build_hook_prompt(record):
    """Image prompt for the dedicated Hook frame (Block 9 beat 0-3s)."""
    fields = record.get("fields", {}) or {}
    ad_name = (fields.get("Ad Name") or "Provinzial moment").strip()
    pillar = detect_pillar(ad_name) or "lifestyle"
    scenario = re.sub(r"\s*\[.*\]\s*$", "", ad_name).strip()
    hook_text, _ = _hook_lösung_beats(record)
    if not hook_text:
        raise RuntimeError(f"build_hook_prompt: no hook text in Voiceover Segments")
    return (
        f"Attention-grabbing opening moment for: {scenario}. "
        f"Single visual hook. The first thing the viewer sees — must stop the scroll. "
        f"Scene anchored on: \"{hook_text}\". "
        f"Documentary style, natural lighting, German lifestyle aesthetic "
        f"(NRW everyday — real homes, real people, never staged). "
        f"Composition: 9:16 vertical, subject prominent in upper-mid frame, "
        f"clean bottom-third for caption. {BRAND_ANCHOR} "
        f"NO text, NO logos, NO graphic overlays in the image — those are "
        f"composited in post."
    )


def build_lösung_prompt(record):
    """Image prompt for the dedicated Lösung frame (Block 9 beat 10-16s)."""
    fields = record.get("fields", {}) or {}
    ad_name = (fields.get("Ad Name") or "Provinzial moment").strip()
    scenario = re.sub(r"\s*\[.*\]\s*$", "", ad_name).strip()
    lösung_text = _beat_texts(record).get("lösung", "")
    if not lösung_text:
        raise RuntimeError(f"build_lösung_prompt: no lösung text in Voiceover Segments")
    return (
        f"Resolution moment for: {scenario}. People being helped, relieved, "
        f"secure — the emotional payoff after the problem beat. "
        f"Scene anchored on: \"{lösung_text}\". "
        f"Documentary style, warm lighting (golden-hour bias), German "
        f"lifestyle (NRW everyday). "
        f"Composition: 9:16 vertical, faces or hands visible, "
        f"warmth and trust in the body language, clean bottom-third for caption. "
        f"{BRAND_ANCHOR} "
        f"NO text, NO logos, NO graphic overlays — those are composited in post."
    )


def build_cta_prompt(record):
    """Image prompt for the dedicated CTA frame (Block 11 beat 15-19s).

    Per Block 11 spec: a warm conclusion close-up. Different from the Lösung
    payoff — this is the explicit invitation/resolution at the end of the ad,
    typically a smile, a Provinzial agent, or a family-at-peace frame.
    """
    fields = record.get("fields", {}) or {}
    ad_name = (fields.get("Ad Name") or "Provinzial moment").strip()
    scenario = re.sub(r"\s*\[.*\]\s*$", "", ad_name).strip()
    cta_text = _beat_texts(record).get("cta", "")
    cta_anchor = (
        f"Voiceover anchor: \"{cta_text}\". " if cta_text else ""
    )
    return (
        f"Resolution close-up moment for: {scenario}. Warm conclusion. "
        f"Person looking content, or Provinzial agent smiling warmly, or "
        f"family at peace. {cta_anchor}"
        f"Documentary style, natural lighting (warm golden-hour bias), "
        f"German lifestyle (NRW everyday). "
        f"Composition: 9:16 vertical, face or upper-body close-up, gentle eye "
        f"contact or settled gaze, clean bottom-third for caption. "
        f"{BRAND_ANCHOR} "
        f"NO text, NO logos, NO graphic overlays — those are composited in post."
    )


# Block 9 + 11 beat dispatch table for process_beat_frame.
BEAT_FRAME_CONFIG = {
    "hook":   {"frame_field": "Hook Frame",   "prompt_field": "Hook Prompt",   "fname": "hook.png",     "build_prompt": build_hook_prompt},
    "lösung": {"frame_field": "Lösung Frame", "prompt_field": "Lösung Prompt", "fname": "loesung.png",  "build_prompt": build_lösung_prompt},
    "cta":    {"frame_field": "CTA Frame",    "prompt_field": "CTA Prompt",    "fname": "cta.png",      "build_prompt": build_cta_prompt},
}


def process_beat_frame(record, beat: str):
    """Generate a single new beat frame (hook | lösung | cta) and patch Airtable.

    Reads Voiceover Segments for the beat text, builds the prompt, submits to
    Fal Nano Banana Pro using the record's Source Image as the anchor, writes
    the result to the matching Airtable attachment field, and stores the prompt
    for traceability.

    Does NOT touch Video Status — these are additive Block 9/11 fields, not
    part of the original Pending → Frames Generated → Clip Generated → ... ladder.
    """
    cfg = BEAT_FRAME_CONFIG.get(beat)
    if cfg is None:
        raise ValueError(f"process_beat_frame: bad beat {beat!r}")
    rec_id = record["id"]
    fields = record.get("fields", {})
    ad_name = fields.get("Ad Name") or "(no name)"
    source_url = av.get_source_image_url(record)
    if not source_url:
        log(f"SKIP {rec_id} ({ad_name}) [{beat}]: no Source Image attachment")
        return "skipped_no_source"

    prompt = cfg["build_prompt"](record)
    frame_field = cfg["frame_field"]
    prompt_field = cfg["prompt_field"]
    fname = f"{rec_id}_{cfg['fname']}"

    log(f"START {rec_id} ({ad_name}) [{beat}]")
    tmp = download_to_temp(source_url,
                           suffix=Path(urlparse(source_url).path).suffix or ".png")
    try:
        fal_ref_url = upload_to_fal(tmp)
    finally:
        try: tmp.unlink()
        except OSError: pass

    handler = submit_frame(prompt, fal_ref_url)
    result_url = extract_image_url(handler.get())
    if not result_url:
        log(f"FAIL {rec_id} ({ad_name}) [{beat}]: no result URL")
        return "failed"

    av.update_record(rec_id, {
        prompt_field: prompt,
        frame_field: [{"url": result_url, "filename": fname}],
    })
    log(f"DONE  {rec_id} ({ad_name}) [{beat}] -> {result_url}")
    return "ok"


def main(argv=None):
    parser = argparse.ArgumentParser(description="R61 Step 1 — frame generation")
    parser.add_argument("--dry-run", action="store_true",
                        help="Read Airtable and show what would happen; no Fal calls.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N pending records this run.")
    parser.add_argument("--record-id", default=None,
                        help="Force-process this single Airtable record id, "
                             "bypassing the Video Status = Pending filter. "
                             "Useful for re-running a specific record after "
                             "prompt changes.")
    parser.add_argument("--generate-hook", action="store_true",
                        help="Block 9: generate the Hook Frame for the targeted "
                             "record(s) using the hook text from Voiceover Segments. "
                             "Writes to the Hook Frame / Hook Prompt fields. Does "
                             "not touch the original first/last frames or Video Status.")
    parser.add_argument("--generate-lösung", "--generate-loesung",
                        dest="generate_lösung", action="store_true",
                        help="Block 9: generate the Lösung Frame for the targeted "
                             "record(s) using the lösung text from Voiceover Segments. "
                             "Writes to the Lösung Frame / Lösung Prompt fields. Does "
                             "not touch the original first/last frames or Video Status.")
    parser.add_argument("--generate-cta", dest="generate_cta", action="store_true",
                        help="Block 11: generate the CTA Frame for the targeted "
                             "record(s). Anchors on the cta text from Voiceover "
                             "Segments if present, otherwise a generic warm-conclusion "
                             "prompt. Writes to the CTA Frame / CTA Prompt fields. "
                             "Does not touch Video Status.")
    parser.add_argument("--confirm", default=None,
                        help="Pass a fire word (e.g. --confirm go) to bypass the "
                             "interactive cost prompt.")
    args = parser.parse_args(argv)

    missing = av.check_credentials()
    if missing:
        print(f"Missing env vars in {ENV_PATH}: {', '.join(missing)}", file=sys.stderr)
        return 1
    if not args.dry_run and not os.getenv("FAL_KEY"):
        print(f"FAL_KEY missing in {ENV_PATH} — needed for paid run.", file=sys.stderr)
        return 1

    if not BRAND_DOC.exists():
        print(f"Brand reference not found at {BRAND_DOC}", file=sys.stderr)
        return 1

    if args.record_id:
        records = [av.get_record(args.record_id)]
    else:
        records = av.get_pending_videos()
    if args.limit:
        records = records[: args.limit]

    # ---- Block 9/11: dedicated hook / lösung / cta beat generation path ----
    beats = []
    if args.generate_hook:
        beats.append("hook")
    if args.generate_lösung:
        beats.append("lösung")
    if args.generate_cta:
        beats.append("cta")
    if beats:
        if not records:
            log("--generate-hook/--generate-lösung/--generate-cta set but no records selected.")
            return 0
        if args.dry_run:
            print()
            print(f"DRY RUN — beat frame generation")
            print(f"Beats: {beats}")
            print(f"Records: {len(records)}")
            total_images = len(records) * len(beats)
            print(f"Would generate {total_images} images "
                  f"(~${total_images * COST_PER_IMAGE_USD:.2f} on "
                  f"{FAL_IMAGE_ENDPOINT}). No API calls were made.")
            for r in records:
                f = r.get("fields", {})
                texts = _beat_texts(r)
                print(f"  - {r['id']}  Index={f.get('Index')!r}")
                for b in beats:
                    t = texts.get(b, "")
                    print(f"      {b:7s} text ({len(t)} chars): {t[:120]}{'...' if len(t) > 120 else ''}")
            return 0
        total_images = len(records) * len(beats)
        total_usd = total_images * COST_PER_IMAGE_USD
        if args.confirm and args.confirm.strip().lower() in FIRE_WORDS:
            log(f"Beat-gen cost gate bypassed via --confirm {args.confirm!r}. "
                f"{len(records)} record(s) × {len(beats)} beat(s) = "
                f"{total_images} images, ~${total_usd:.2f}.")
        else:
            print()
            print("=" * 60)
            print(f"BEAT FRAME GENERATION — COST ESTIMATE")
            print("=" * 60)
            print(f"  Records            : {len(records)}")
            print(f"  Beats per record   : {len(beats)} ({', '.join(beats)})")
            print(f"  Total images       : {total_images}")
            print(f"  $ per image        : ${COST_PER_IMAGE_USD:.2f}")
            print(f"  TOTAL              : ${total_usd:.2f}")
            print("=" * 60)
            print(f"Type one of: {sorted(FIRE_WORDS)} to proceed, anything else aborts.")
            ans = input("> ").strip().lower()
            if ans not in FIRE_WORDS:
                log("Aborted at beat-gen cost gate — no API calls made.")
                return 1
        log(f"Beat-gen confirmed. {len(records)} record(s) × beats={beats}.")
        summary = {"ok": 0, "failed": 0, "skipped_no_source": 0}
        for r in records:
            for beat in beats:
                try:
                    result = process_beat_frame(r, beat)
                except Exception as e:
                    log(f"FAIL {r['id']} [{beat}]: {e}")
                    result = "failed"
                summary[result] = summary.get(result, 0) + 1
        log(f"Beat-gen complete. Summary: {summary}")
        return 0 if summary.get("failed", 0) == 0 else 2

    if args.dry_run:
        dry_run_report(records)
        return 0

    if not records:
        log("No pending records — nothing to do.")
        return 0

    if args.confirm and args.confirm.strip().lower() in FIRE_WORDS:
        log(f"Cost gate bypassed via --confirm {args.confirm!r}.")
    elif not confirm_cost(len(records)):
        log("Aborted at cost gate — no API calls made.")
        return 1

    log(f"Confirmed. Processing {len(records)} record(s).")
    summary = {"ok": 0, "failed": 0, "skipped_no_source": 0}
    for r in records:
        try:
            result = process_record(r)
        except Exception as e:
            log(f"FAIL {r['id']}: {e}")
            result = "failed"
        summary[result] = summary.get(result, 0) + 1

    log(f"Run complete. Summary: {summary}")

    if summary.get("ok", 0) > 0:
        try:
            _gates.append_gate(
                gate_number=0,
                gate_name="frames_generated_batch",
                record_id="batch",
                ad_name=f"frame_gen batch — {summary['ok']} record(s) ready for video_gen review",
                video_url="",
                extra={
                    "batch_summary": summary,
                    "next_step": "Review first/last frames in Airtable, then run video_gen.py",
                },
            )
            log(f"Gate entry written → shared/gates/pending.json (frames batch).")
        except Exception as e:
            log(f"WARN: gate write failed: {e}")

    return 0 if summary.get("failed", 0) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
