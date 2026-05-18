"""
R61 Step 4 — Voiceover generation via ElevenLabs Multilingual v2.

Reads Airtable Video records where Video Status = "Clip Generated", strips
the Caption of social/CTA noise, optionally rewrites it for spoken cadence
through the provinzial-copy skill rules (Gemini Flash), then calls the
ElevenLabs TTS endpoint with one of two pre-selected native-German voices:

  Index odd  → Jones  (niMwYIP6tIdlsdDEGVdT, male, "Deep & Warm")
  Index even → Clara  (E13qNLHLLuVPKQvesCoy, female, "Warm, clear & Calm")

Both voices were added to the workspace library on first set-up and verified
to support eleven_multilingual_v2. Voice settings (stability 0.55,
similarity_boost 0.75, style 0.3, use_speaker_boost true) tuned for warm
professional German narration that matches the Provinzial brand voice
(calm authority, grounded, trustworthy — see references/docs/provinzial_BRAND.md).

Output MP3 is uploaded to Cloudflare R2 (re-using the upload + clock-patch
pattern from tools/stitch.py — same boto3/SigV4 + local-clock-skew quirk),
the public URL is attached to Airtable field "Voiceover Audio", and Video
Status advances to "Voiceover Done".

Pipeline-ordering note: per PIPELINE.md, voiceover is Step 4
("Raw Attached" → "Voiceover Done"). This tool runs one step earlier
("Clip Generated" → "Voiceover Done") because voiceovers can be produced
from the caption without waiting for the manual R2 raw-footage gate
(Step 3). The FFmpeg stitch step (Gate #3) is where ordering is enforced
anyway.

Hard cost-approval gate: re-quote on every run and wait for an explicit
fire word before any paid call. Quote shows character count, ElevenLabs
credit usage (1 credit/char on eleven_multilingual_v2), and Creator-tier
USD figure ($22/100k chars = $0.00022/char).

Usage:
    python -m tools.voiceover_gen --dry-run          # read-only verification
    python -m tools.voiceover_gen                    # interactive paid run
    python -m tools.voiceover_gen --limit 3
    python -m tools.voiceover_gen --confirm go       # non-interactive
    python -m tools.voiceover_gen --no-rewrite       # skip Gemini rewrite,
                                                     # use strip-only output
    python -m tools.voiceover_gen --record-id recXXX
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

from tools import airtable_video as av  # noqa: E402

LOG_PATH = PROJECT_ROOT / "references" / "outputs" / "voiceover_run.log"

# ---------------------------------------------------------------- ElevenLabs

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
ELEVEN_MODEL_ID = "eleven_multilingual_v2"

# Pre-selected native-German voices, added to the workspace library on
# 2026-05-13. Both verified to support eleven_multilingual_v2 in German.
VOICE_MALE = {
    "id": "niMwYIP6tIdlsdDEGVdT",
    "name": "Jones (DE, Deep & Warm)",
    "gender": "male",
}
VOICE_FEMALE = {
    "id": "E13qNLHLLuVPKQvesCoy",
    "name": "Clara (DE, Warm, clear & Calm)",
    "gender": "female",
}

# Tone-mapped voices (shared library, accent=standard DE). Per-record Airtable
# fields "Voice Tone" / "Voice Override" pick from these; falls back to the
# Jones/Clara odd/even Index routing when neither field is set.
VOICE_BY_TONE = {
    "ernst":   "hUiEHybCSPbXi2EbtGC1",  # Crizz – Conversational & Deep
    "familie": "0o46iPcQNHBZFpnxxQz5",  # Marion Mitte – Friendly, Warm & Fresh
    "leicht":  "LB5G0Z4EP98YaEgL654m",  # Laura – Upbeat & Energetic
    "reif":    "oBVK5gDykyUkoVXUPyCU",  # Altáriel – Storyteller of the Light
}
VOICE_META_BY_TONE = {
    "ernst":   {"name": "Crizz (DE, Conversational & Deep)",         "gender": "male"},
    "familie": {"name": "Marion Mitte (DE, Friendly, Warm & Fresh)", "gender": "female"},
    "leicht":  {"name": "Laura (DE, Upbeat & Energetic)",            "gender": "female"},
    "reif":    {"name": "Altáriel (DE, Storyteller of the Light)",   "gender": "female"},
}

VOICE_SETTINGS = {
    "stability": 0.55,
    "similarity_boost": 0.75,
    "style": 0.3,
    "use_speaker_boost": True,
}

# Creator tier: 100k included chars for $22/mo => $0.00022/char.
# eleven_multilingual_v2 charges 1 credit per character.
CREATOR_USD_PER_CHAR = 22.0 / 100_000.0

ELEVENLABS_TIMEOUT_S = 90

FIRE_WORDS = {"go", "fire", "yes", "run it", "run", "ship"}

# Narrative-structure mode (Block 3). When R61_NARRATIVE_MODE=true the cleaned
# script is split into Hook / Problem / Lösung / CTA segments (Gemini Flash),
# each TTS'd separately, then concatenated. Segment timing JSON lands in
# Airtable's `Voiceover Segments` field; the existing `Voiceover Script`
# behavior is unchanged when the flag is off (default).
NARRATIVE_MODE = os.environ.get("R61_NARRATIVE_MODE", "").lower() in ("1", "true", "yes")

NARRATIVE_SEGMENTS = [
    ("hook",   0.0,  3.0,  "Aufmerksamkeitsmoment — echter menschlicher Moment, KEINE Markenerwähnung."),
    ("problem",3.0,  7.0,  "Das alltägliche Risiko klar und einfach gezeigt."),
    ("lösung", 7.0, 11.0,  "Die Rolle von Provinzial — wie sie helfen, NICHT was sie verkaufen."),
    ("cta",   11.0, 15.0,  "Warme Einladung, niemals ein Befehl."),
]

# ----------------------------------------------------------- Caption cleaning

# Phrases that are clearly social-call-to-action only. Matched case-insensitive.
SOCIAL_PHRASES = [
    r"link\s+in\s+bio",
    r"link\s+in\s+the\s+bio",
    r"link\s+im\s+profil",
    r"link\s+in\s+der\s+bio",
    r"swipe\s+up",
    r"jetzt\s+kaufen",
    r"jetzt\s+klicken",
    r"klick(e)?\s+hier",
    r"mehr\s+(dazu|infos|erfahren)\s+im\s+profil",
]

# Whole lines that are nothing but a CTA imperative pointing at Link-in-Bio.
# We drop the entire line: "Jetzt informieren → Link in Bio", "Mehr erfahren",
# "Tarif berechnen", "Service-Hotline", "Altersvorsorge gestalten", etc.
# A CTA line is one whose stripped content starts/ends with one of these
# imperative phrases and is short (≤ 6 words). Keeps real content like
# "Mehr Sicherheit für dich und deine Familie" untouched.
CTA_IMPERATIVES = [
    r"jetzt\s+informieren",
    r"jetzt\s+klicken",
    r"mehr\s+erfahren",
    r"tarif\s+berechnen",
    r"tarif\s+vergleichen",
    r"service[-\s]?hotline",
    r"altersvorsorge\s+gestalten",
    r"jetzt\s+anfragen",
    r"jetzt\s+kaufen",
    r"jetzt\s+beraten\s+lassen",
]
CTA_LINE_RE = re.compile(
    r"^\s*(?:[→➔➜➡⬅⮕\->]+\s*)?"
    r"(?:" + "|".join(CTA_IMPERATIVES) + r")"
    r"\s*[→➔➜➡⬅⮕\->]*\s*$",
    re.IGNORECASE,
)

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U0000FE00-\U0000FE0F"
    "\U0001F018-\U0001F0FF"
    "]+",
    flags=re.UNICODE,
)
HASHTAG_RE = re.compile(r"#\w+", flags=re.UNICODE)
MENTION_RE = re.compile(r"@\w+", flags=re.UNICODE)
URL_RE = re.compile(r"https?://\S+", flags=re.UNICODE)
ARROW_RE = re.compile(r"[←-⇿➔➡⬅-⮕]")


def log(msg):
    ts = dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def clean_caption(caption):
    """Return a spoken-only version of the caption.

    Strips hashtags, @mentions, URLs, emojis, arrows, social-CTA phrases,
    and whole imperative-only CTA lines ("Jetzt informieren", "Mehr
    erfahren", ...). Collapses leftover whitespace.
    """
    if not caption:
        return ""
    text = caption
    text = URL_RE.sub(" ", text)
    text = HASHTAG_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = EMOJI_RE.sub(" ", text)
    text = ARROW_RE.sub(" ", text)
    for pat in SOCIAL_PHRASES:
        text = re.sub(pat, " ", text, flags=re.IGNORECASE)
    # Collapse line breaks + multispaces before CTA-line filter so the
    # filter can match a clean stripped line.
    text = re.sub(r"\s*\n\s*", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    lines_in = [ln.strip(" \t-—–•") for ln in text.splitlines()]
    lines_out = []
    for ln in lines_in:
        if not ln:
            continue
        if not re.search(r"\w", ln, flags=re.UNICODE):
            continue
        if CTA_LINE_RE.match(ln):
            continue
        lines_out.append(ln)
    return "\n".join(lines_out).strip()


# ------------------------------------------------------ Provinzial-copy rewrite
# Optional second pass: hand the stripped caption to Gemini Flash with the
# provinzial-copy skill rules as the prompt and ask for a spoken-cadence
# rewrite. Gemini Flash is essentially free at this volume (~$0.0001/record).
# Disabled with --no-rewrite for deterministic strip-only output.

REWRITE_SYSTEM_PROMPT = """Du bist Voiceover-Redakteur für die Provinzial Versicherung
(Geier & Ayhan Kampagne). Du bekommst eine bereinigte Caption und schreibst
sie in einen kurzen, gesprochenen Voiceover-Text um.

REGELN (provinzial-copy):
- Sprache: Deutsch, Du-Form.
- Ton: warm, ruhig, professionell, geerdet, vertrauenswürdig. Nicht steif,
  nicht reißerisch, nicht ironisch.
- Kein Hype, keine Dringlichkeit, keine Kaufaufforderungen ohne Frist.
- Kein Versicherungs-Jargon. Konkret statt abstrakt.
- Kurze Sätze. Eine Idee pro Satz. Ein Satz pro Beat.
- Meta-Sprache entfernen ("Wir erklären, warum X wichtig ist." → durch
  eine direkte Aussage über X ersetzen.)
- Verbotene Buzzwords: innovativ, ganzheitlich, Synergie, auf Augenhöhe.
- Niemals absolute Versprechen ("immer", "garantiert", "100%") rund um
  Versicherungsleistungen.
- Markenschluss-Phrasen ("Sicherheit. Klarheit. Provinzial.",
  "Für das, was wirklich zählt.") nur behalten, wenn sie als Pointe sitzen.
- Output: NUR der gesprochene Text. Keine Anführungszeichen, keine
  Erklärung, keine Hashtags, keine Emojis. 2–4 kurze Sätze.
- Wenn die Caption schon ideal gesprochen klingt, gib sie unverändert zurück.
- Wenn nichts übrig bleibt, gib einen leeren String zurück.
"""


def rewrite_for_vo(cleaned_text):
    """Pass the cleaned caption through Gemini Flash with provinzial-copy rules.

    Returns the rewritten string (may equal input if Gemini deems it already
    good). Raises on API errors so caller can decide to fall back.
    """
    if not cleaned_text:
        return ""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY missing — needed for VO rewrite "
                           "(or pass --no-rewrite).")
    # gemini-2.5-flash-lite chosen because (a) 2.5-flash has thinking-mode on
    # by default which eats maxOutputTokens before the visible response
    # (observed 2026-05-13: rewrites cut mid-word at 73-77 chars), and
    # (b) 2.0-flash is no longer available to new API keys. Flash-lite has
    # no thinking mode and is the right tier for this rule-bound task.
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash-lite:generateContent?key={api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": REWRITE_SYSTEM_PROMPT}]},
        "contents": [{
            "role": "user",
            "parts": [{"text": f"Caption:\n{cleaned_text}\n\nVoiceover-Text:"}],
        }],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1024,
            "responseMimeType": "text/plain",
        },
    }
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini rewrite failed ({resp.status_code}): "
                           f"{resp.text[:300]}")
    data = resp.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Gemini response shape unexpected: "
                           f"{json.dumps(data)[:300]}")
    # Strip stray quotes / trailing whitespace; Gemini sometimes wraps output.
    text = text.strip().strip('"').strip("'").strip()
    return text


# ----------------------------------------------------- Narrative-segment split
# Block 3 — Hook / Problem / Lösung / CTA. When NARRATIVE_MODE is on, the
# cleaned + provinzial-copy-rewritten script is passed to Gemini once more to
# be split into 4 timed segments. Each segment carries (text, start_s, end_s).
# This function returns a list of dicts; raises on hard API failure so caller
# decides whether to abort the record or fall back to single-segment TTS.

SPLIT_SYSTEM_PROMPT = """Du bist Drehbuch-Editor für die Provinzial Versicherung
(Geier & Ayhan Kampagne). Du bekommst einen kurzen gesprochenen Voiceover-Text
und teilst ihn in genau VIER aufeinanderfolgende Segmente:

  1. hook    (0–3s):  Aufmerksamkeitsmoment — echter menschlicher Moment.
                       KEINE Markenerwähnung, KEINE Produktnennung.
  2. problem (3–7s):  Das alltägliche Risiko klar und einfach gezeigt.
  3. lösung  (7–11s): Provinzials Rolle — wie sie helfen, NICHT was sie
                       verkaufen. Konkret, geerdet.
  4. cta     (11–15s): Warme Einladung, niemals ein Befehl. Keine
                       Dringlichkeit.

REGELN:
- Sprache: Deutsch, Du-Form, warm, ruhig, professionell, geerdet.
- Buzzwords verboten: innovativ, ganzheitlich, Synergie, auf Augenhöhe.
- Niemals absolute Versprechen ("immer", "garantiert", "100%").
- Falls der Input zu kurz ist, paraphrasiere/dehne sinnvoll auf die Beats;
  erfinde keine Fakten.
- Jedes Segment ist 1-2 kurze Sätze. Eine Idee pro Beat.

Output: NUR ein JSON-Objekt mit den Schlüsseln "hook", "problem", "lösung",
"cta", jeweils ein String. Kein Markdown, keine Erklärung."""


def split_into_segments(script):
    """Return [{name, text, start_s, end_s}, ...] for the 4 narrative beats.

    Used only when NARRATIVE_MODE is True. Caller is responsible for branching
    on the flag — this function unconditionally hits Gemini.
    """
    if not script:
        return []
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY missing — needed for narrative split.")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash-lite:generateContent?key={api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": SPLIT_SYSTEM_PROMPT}]},
        "contents": [{
            "role": "user",
            "parts": [{"text": f"Voiceover-Text:\n{script}\n\nSegmente (JSON):"}],
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini split failed ({resp.status_code}): "
                           f"{resp.text[:300]}")
    data = resp.json()
    try:
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Gemini split response shape unexpected: "
                           f"{json.dumps(data)[:300]}")
    parsed = json.loads(raw)
    out = []
    for name, start_s, end_s, _ in NARRATIVE_SEGMENTS:
        text = (parsed.get(name) or "").strip()
        out.append({
            "name": name,
            "text": text,
            "start_s": start_s,
            "end_s": end_s,
        })
    return out


def concat_mp3_via_ffmpeg(mp3_paths, out_path):
    """Concatenate sequential MP3 chunks losslessly via ffmpeg concat demuxer.

    Used to assemble the 4 narrative-segment TTS outputs into a single file.
    """
    import subprocess
    out_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = out_path.parent / f"{out_path.stem}_concat.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in mp3_paths:
            # ffmpeg concat demuxer requires single-quote escaping.
            safe = str(p).replace("'", r"'\''")
            f.write(f"file '{safe}'\n")
    argv = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(out_path),
    ]
    proc = subprocess.run(argv, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    try:
        list_file.unlink()
    except OSError:
        pass
    if proc.returncode != 0:
        raise RuntimeError("MP3 concat ffmpeg failed:\n" + (proc.stderr or "")[-2000:])


# --------------------------------------------------------------- Voice pick

def pick_voice(index):
    """Odd Index → male (Jones), even Index → female (Clara).

    None/missing Index defaults to male so the pipeline never blocks on a
    bad record; operator will see the assignment in the dry-run report.
    """
    if index is None:
        return VOICE_MALE
    try:
        i = int(index)
    except (TypeError, ValueError):
        return VOICE_MALE
    return VOICE_MALE if i % 2 == 1 else VOICE_FEMALE


def select_voice_id(record):
    """Tone-aware voice selection with override + Jones/Clara fallback.

    Resolution order:
      1. "Voice Override" set and recognized → VOICE_BY_TONE[override]  (path="override")
      2. "Voice Tone" set and recognized     → VOICE_BY_TONE[tone]       (path="tone")
      3. Fallback                            → odd/even Index → pick_voice  (path="fallback")

    Returns (voice_dict, path_str). voice_dict has the same id/name/gender shape
    that the existing pick_voice consumers expect.
    """
    fields = record.get("fields", {}) or {}
    override = (fields.get("Voice Override") or "").strip().lower()
    tone     = (fields.get("Voice Tone")     or "").strip().lower()

    if override and override in VOICE_BY_TONE:
        meta = VOICE_META_BY_TONE[override]
        return (
            {"id": VOICE_BY_TONE[override], "name": meta["name"], "gender": meta["gender"]},
            "override",
        )
    if tone and tone in VOICE_BY_TONE:
        meta = VOICE_META_BY_TONE[tone]
        return (
            {"id": VOICE_BY_TONE[tone], "name": meta["name"], "gender": meta["gender"]},
            "tone",
        )
    return pick_voice(fields.get("Index")), "fallback"


# -------------------------------------------------------------- ElevenLabs TTS

def eleven_tts(script, voice_id):
    """Call ElevenLabs TTS and return MP3 bytes.

    Raises RuntimeError on non-200 response.
    """
    api_key = os.environ["ELEVENLABS_API_KEY"]
    url = f"{ELEVENLABS_API_BASE}/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": script,
        "model_id": ELEVEN_MODEL_ID,
        "voice_settings": VOICE_SETTINGS,
    }
    resp = requests.post(url, headers=headers, json=payload,
                         timeout=ELEVENLABS_TIMEOUT_S)
    if resp.status_code != 200:
        raise RuntimeError(
            f"ElevenLabs TTS failed ({resp.status_code}): {resp.text[:300]}"
        )
    return resp.content


# --------------------------------------------------- ElevenLabs forced alignment

def get_forced_alignment(audio_path, transcript_text):
    """Return per-word alignment for a rendered MP3 against its transcript.

    Uses the ElevenLabs SDK (client.forced_alignment.create). Returns the
    response dict on success; None on permanent failure (caller writes
    {"alignment_failed": true} so downstream caption rendering can fall back
    to char-proportional timing without halting the run).

    Retries twice with 3s backoff on transient/5xx errors; 4xx fail-fast.
    """
    import time as _time
    from elevenlabs.client import ElevenLabs

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        log("  WARN alignment skipped — ELEVENLABS_API_KEY not set")
        return None
    if not transcript_text or not transcript_text.strip():
        log("  WARN alignment skipped — empty transcript")
        return None

    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
    except OSError as e:
        log(f"  WARN alignment skipped — cannot read audio ({e})")
        return None

    client = ElevenLabs(api_key=api_key)
    last_err = None
    for attempt in (1, 2, 3):
        try:
            result = client.forced_alignment.create(
                file=audio_bytes, text=transcript_text
            )
            try:
                payload = result.model_dump()
            except AttributeError:
                payload = result.dict()  # type: ignore[attr-defined]
            words = payload.get("words") or []
            log(f"  alignment ok (attempt {attempt}) — {len(words)} word(s) returned")
            return payload
        except Exception as e:  # noqa: BLE001 — SDK raises ApiError; treat broad
            msg = str(e)
            last_err = e
            status = getattr(e, "status_code", None)
            if status and 400 <= int(status) < 500:
                log(f"  alignment FAILED (4xx, no retry) attempt {attempt}: {msg[:240]}")
                return None
            if attempt == 3:
                log(f"  alignment FAILED (final) attempt {attempt}: {msg[:240]}")
                return None
            log(f"  alignment transient error attempt {attempt}: {msg[:240]} — retrying in 3s")
            _time.sleep(3)
    log(f"  alignment FAILED — exhausted retries: {last_err}")
    return None


# ----------------------------------------------------------------- R2 upload
# Duplicated from tools/stitch.py — same boto3 + SigV4 + local-clock-skew
# workaround. Kept inline rather than extracted to a shared module to keep
# this change focused; if a third tool needs R2 upload, extract then.

_R2_CLOCK_PATCHED = False


def _patch_botocore_clock(endpoint_url):
    """Compensate Windows host clock drift vs Cloudflare R2 (>15min skew
    breaks SigV4). See feedback_r2_clock_skew memory."""
    global _R2_CLOCK_PATCHED
    if _R2_CLOCK_PATCHED:
        return
    import datetime as _dt
    from email.utils import parsedate_to_datetime
    import botocore.auth
    import botocore.utils

    try:
        head = requests.head(endpoint_url, timeout=10, allow_redirects=True)
        server_dt = parsedate_to_datetime(head.headers["Date"]).astimezone(
            _dt.timezone.utc
        ).replace(tzinfo=None)
    except Exception as e:
        log(f"  WARN could not read R2 server time ({e}); skipping clock patch")
        _R2_CLOCK_PATCHED = True
        return

    local_dt = _dt.datetime.utcnow()
    offset = server_dt - local_dt
    if abs(offset.total_seconds()) < 60:
        log(f"  R2 clock offset {offset.total_seconds():+.1f}s (within tolerance)")
        _R2_CLOCK_PATCHED = True
        return

    def _shifted_get_current_datetime(remove_tzinfo=True):
        dt_now = _dt.datetime.now(_dt.timezone.utc) + offset
        if remove_tzinfo:
            dt_now = dt_now.replace(tzinfo=None)
        return dt_now

    botocore.utils.get_current_datetime = _shifted_get_current_datetime
    botocore.auth.get_current_datetime = _shifted_get_current_datetime
    log(f"  Patched botocore.{{auth,utils}}.get_current_datetime by "
        f"{offset.total_seconds():+.1f}s")
    _R2_CLOCK_PATCHED = True


def upload_to_r2(local_path, key, content_type="audio/mpeg"):
    import boto3
    from botocore.config import Config

    account_id = os.environ["R2_ACCOUNT_ID"]
    access_key = os.environ["R2_ACCESS_KEY_ID"]
    secret_key = os.environ["R2_SECRET_ACCESS_KEY"]
    bucket = os.environ["R2_BUCKET_NAME"]
    public_base = os.environ["R2_PUBLIC_URL"].rstrip("/")
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    _patch_botocore_clock(endpoint_url)

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )
    client.upload_file(
        str(local_path), bucket, key,
        ExtraArgs={"ContentType": content_type},
    )
    return f"{public_base}/{key}"


# ----------------------------------------------------------- Per-record runner

def build_script(record, no_rewrite):
    """Return (raw_caption, stripped, final_script, rewrite_used)."""
    caption = record.get("fields", {}).get("Caption") or ""
    stripped = clean_caption(caption)
    if not stripped or no_rewrite:
        return caption, stripped, stripped, False
    try:
        rewritten = rewrite_for_vo(stripped)
    except Exception as e:
        log(f"  WARN rewrite failed ({e}); falling back to strip-only")
        return caption, stripped, stripped, False
    if not rewritten:
        return caption, stripped, stripped, False
    return caption, stripped, rewritten, True


def _process_record_narrative(record, no_rewrite, voice, script):
    """Block 3 narrative path: split → TTS per segment → concat → upload + JSON."""
    rec_id = record["id"]
    fields = record.get("fields", {})
    ad_name = fields.get("Ad Name") or "(no name)"
    index = fields.get("Index")

    try:
        segments = split_into_segments(script)
    except Exception as e:
        log(f"  WARN narrative split failed ({e}); falling back to single-segment TTS")
        segments = []

    if not segments or not any(s.get("text") for s in segments):
        log(f"  narrative split yielded no segments; using single-segment fallback")
        audio_bytes = eleven_tts(script, voice["id"])
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        idx_str = f"{int(index):02d}" if isinstance(index, (int, float)) else "xx"
        key = f"r61/voiceover/{idx_str}_{rec_id}_{ts}.mp3"
        fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
        alignment_payload = None
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(audio_bytes)
            r2_url = upload_to_r2(tmp_path, key, content_type="audio/mpeg")
            alignment_payload = get_forced_alignment(tmp_path, script)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        alignment_json = (
            json.dumps(alignment_payload, ensure_ascii=False)
            if alignment_payload is not None
            else json.dumps({"alignment_failed": True}, ensure_ascii=False)
        )
        av.update_record(rec_id, {
            "Voiceover Audio": [{"url": r2_url, "filename": f"{rec_id}_vo.mp3"}],
            "Voiceover Alignment JSON": alignment_json,
            av.STATUS_FIELD: av.STATUS_VOICEOVER_DONE,
        })
        return "ok"

    # Per-segment TTS to temp files.
    seg_paths = []
    populated = []
    for seg in segments:
        if not seg["text"]:
            continue
        log(f"  segment '{seg['name']}' ({seg['start_s']:.1f}-{seg['end_s']:.1f}s, "
            f"{len(seg['text'])} chars): {seg['text'][:80]}...")
        seg_bytes = eleven_tts(seg["text"], voice["id"])
        fd, tmp = tempfile.mkstemp(suffix=f"_{seg['name']}.mp3")
        with os.fdopen(fd, "wb") as f:
            f.write(seg_bytes)
        seg_paths.append(Path(tmp))
        populated.append(seg)

    if not seg_paths:
        log(f"SKIP {rec_id} ({ad_name}): all segments empty after split")
        return "skipped_no_script"

    # Concat → R2 → forced alignment (runs on the local concatenated MP3
    # before cleanup; cheaper than round-tripping through R2). Transcript =
    # beats joined by single spaces in spoken order.
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    idx_str = f"{int(index):02d}" if isinstance(index, (int, float)) else "xx"
    combined = Path(tempfile.gettempdir()) / f"r61_vo_{rec_id}_{ts}.mp3"
    alignment_payload = None
    try:
        if len(seg_paths) == 1:
            import shutil as _shutil
            _shutil.copyfile(str(seg_paths[0]), str(combined))
        else:
            concat_mp3_via_ffmpeg(seg_paths, combined)
        key = f"r61/voiceover/{idx_str}_{rec_id}_{ts}.mp3"
        r2_url = upload_to_r2(str(combined), key, content_type="audio/mpeg")
        concat_transcript = " ".join(s["text"].strip() for s in populated if s.get("text"))
        alignment_payload = get_forced_alignment(combined, concat_transcript)
    finally:
        for p in seg_paths:
            try: p.unlink()
            except OSError: pass
        try: combined.unlink()
        except OSError: pass

    alignment_json = (
        json.dumps(alignment_payload, ensure_ascii=False)
        if alignment_payload is not None
        else json.dumps({"alignment_failed": True}, ensure_ascii=False)
    )
    av.update_record(rec_id, {
        "Voiceover Audio": [{"url": r2_url, "filename": f"{rec_id}_vo.mp3"}],
        "Voiceover Segments": json.dumps(populated, ensure_ascii=False, indent=2),
        "Voiceover Alignment JSON": alignment_json,
        av.STATUS_FIELD: av.STATUS_VOICEOVER_DONE,
    })
    aln_note = (
        f"alignment_words={len(alignment_payload.get('words') or [])}"
        if alignment_payload else "alignment_failed=True"
    )
    log(f"DONE  {rec_id} ({ad_name}) [narrative, {len(populated)} segs, {aln_note}] -> {r2_url}")
    return "ok"


def process_record(record, no_rewrite):
    rec_id = record["id"]
    fields = record.get("fields", {})
    ad_name = fields.get("Ad Name") or "(no name)"
    index = fields.get("Index")
    voice, voice_path = select_voice_id(record)

    _, stripped, script, rewrote = build_script(record, no_rewrite)
    if not script:
        log(f"SKIP {rec_id} ({ad_name}): caption empty after cleaning")
        return "skipped_no_script"

    log(f"START {rec_id} Index={index} ({ad_name}) "
        f"voice={voice['name']} [{voice_path}] chars={len(script)} rewrote={rewrote} "
        f"narrative={NARRATIVE_MODE}")
    log(f"  script: {script[:160]}{'...' if len(script) > 160 else ''}")

    if NARRATIVE_MODE:
        return _process_record_narrative(record, no_rewrite, voice, script)

    audio_bytes = eleven_tts(script, voice["id"])

    # New path per "never delete old generated content" rule — timestamped key.
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    idx_str = f"{int(index):02d}" if isinstance(index, (int, float)) else "xx"
    key = f"r61/voiceover/{idx_str}_{rec_id}_{ts}.mp3"

    fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
    alignment_payload = None
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(audio_bytes)
        r2_url = upload_to_r2(tmp_path, key, content_type="audio/mpeg")
        alignment_payload = get_forced_alignment(tmp_path, script)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    alignment_json = (
        json.dumps(alignment_payload, ensure_ascii=False)
        if alignment_payload is not None
        else json.dumps({"alignment_failed": True}, ensure_ascii=False)
    )
    av.update_record(
        rec_id,
        {
            "Voiceover Audio": [{"url": r2_url, "filename": f"{rec_id}_vo.mp3"}],
            "Voiceover Alignment JSON": alignment_json,
            av.STATUS_FIELD: av.STATUS_VOICEOVER_DONE,
        },
    )
    aln_note = (
        f"alignment_words={len(alignment_payload.get('words') or [])}"
        if alignment_payload else "alignment_failed=True"
    )
    log(f"DONE  {rec_id} ({ad_name}) [{aln_note}] -> {r2_url}")
    return "ok"


# -------------------------------------------------------------------- Dry-run

def dry_run_report(records, no_rewrite):
    print()
    print(f"DRY RUN — base {av.AIRTABLE_BASE_ID}, table '{av.TABLE_NAME}' "
          f"({av.TABLE_ID})")
    print(f"Filter: {{{av.STATUS_FIELD}}} = \"{av.STATUS_CLIP_GENERATED}\" "
          f"-> {len(records)} record(s)")
    if not records:
        print("  (no rows ready for voiceover)")
        return 0

    total_chars = 0
    skipped = 0
    rewrote = 0
    rows = []
    for r in records:
        f = r.get("fields", {})
        index = f.get("Index")
        ad_name = f.get("Ad Name") or "(no name)"
        voice = pick_voice(index)
        raw, stripped, script, did_rewrite = build_script(r, no_rewrite)
        rows.append({
            "id": r["id"], "index": index, "ad_name": ad_name,
            "voice": voice, "raw": raw, "stripped": stripped,
            "script": script, "rewrote": did_rewrite,
        })
        if did_rewrite:
            rewrote += 1
        if not script:
            skipped += 1
        else:
            total_chars += len(script)

    for row in rows:
        print()
        print(f"  - {row['id']}  Index={row['index']!r}  "
              f"Ad Name={row['ad_name']!r}")
        print(f"      Voice            : {row['voice']['name']} "
              f"[{row['voice']['gender']}]")
        print(f"      Caption raw      ({len(row['raw'])} chars): "
              f"{row['raw'][:140]!r}{'...' if len(row['raw']) > 140 else ''}")
        print(f"      After strip      ({len(row['stripped'])} chars): "
              f"{row['stripped'][:160]!r}"
              f"{'...' if len(row['stripped']) > 160 else ''}")
        if row['rewrote']:
            print(f"      After rewrite    ({len(row['script'])} chars): "
                  f"{row['script'][:200]!r}"
                  f"{'...' if len(row['script']) > 200 else ''}")
        elif not no_rewrite and row['stripped']:
            print(f"      [rewrite kept input unchanged]")
        if not row['script']:
            print(f"      [WOULD SKIP — empty after cleaning]")

    total_usd = total_chars * CREATOR_USD_PER_CHAR
    payable = len(records) - skipped
    print()
    print("=" * 60)
    print(f"  Records ready for TTS : {payable} (skipped: {skipped})")
    print(f"  Rewrites applied      : {rewrote}/{payable}")
    print(f"  Total characters      : {total_chars}")
    print(f"  ElevenLabs credits    : {total_chars} (1 credit/char on "
          f"{ELEVEN_MODEL_ID})")
    print(f"  Creator-tier USD est. : ${total_usd:.4f} "
          f"(at ${CREATOR_USD_PER_CHAR*1000:.4f}/1k chars)")
    print("=" * 60)
    print("No API calls were made to ElevenLabs or R2.")
    return 0


# -------------------------------------------------------------- Cost gate

def confirm_cost(records, no_rewrite):
    """Re-compute scripts (and Gemini-rewrites if enabled) so the operator
    sees the same numbers the paid run will actually charge."""
    total_chars = 0
    skipped = 0
    for r in records:
        _, _, script, _ = build_script(r, no_rewrite)
        if script:
            total_chars += len(script)
        else:
            skipped += 1
    total_usd = total_chars * CREATOR_USD_PER_CHAR
    print()
    print("=" * 60)
    print("COST ESTIMATE")
    print("=" * 60)
    print(f"  Records to process    : {len(records) - skipped} "
          f"(skipped: {skipped})")
    print(f"  Total characters      : {total_chars}")
    print(f"  ElevenLabs credits    : {total_chars}")
    print(f"  Creator-tier USD est. : ${total_usd:.4f}")
    print(f"  Model                 : {ELEVEN_MODEL_ID}")
    print(f"  Voices                : {VOICE_MALE['name']} (odd Index) | "
          f"{VOICE_FEMALE['name']} (even Index)")
    print("=" * 60)
    print(f"Type one of: {sorted(FIRE_WORDS)} to proceed, anything else aborts.")
    answer = input("> ").strip().lower()
    return answer in FIRE_WORDS, total_chars, total_usd


# ------------------------------------------------------------------- main

def check_required_env(dry_run, no_rewrite):
    missing = av.check_credentials()
    if missing:
        return missing
    if not dry_run:
        for v in ("ELEVENLABS_API_KEY", "R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID",
                  "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME", "R2_PUBLIC_URL"):
            if not os.getenv(v):
                missing.append(v)
    if not no_rewrite and not os.getenv("GOOGLE_API_KEY"):
        missing.append("GOOGLE_API_KEY (needed for rewrite, or pass --no-rewrite)")
    return missing


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="R61 Step 4 — ElevenLabs voiceover generation"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Read Airtable + run rewrites; no ElevenLabs/R2 calls.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N records this run.")
    parser.add_argument("--record-id", default=None,
                        help="Force-process this single Airtable record id, "
                             "bypassing the Video Status filter.")
    parser.add_argument("--no-rewrite", action="store_true",
                        help="Skip the Gemini-Flash provinzial-copy rewrite "
                             "pass — feed the strip-only output to TTS.")
    parser.add_argument("--confirm", default=None,
                        help="Pass a fire word (e.g. --confirm go) to bypass "
                             "the interactive cost prompt.")
    args = parser.parse_args(argv)

    missing = check_required_env(args.dry_run, args.no_rewrite)
    if missing:
        print(f"Missing env vars in {ENV_PATH}: {', '.join(missing)}",
              file=sys.stderr)
        return 1

    if args.record_id:
        records = [av.get_record(args.record_id)]
    else:
        records = av.get_records(
            f'{{{av.STATUS_FIELD}}} = "{av.STATUS_CLIP_GENERATED}"'
        )
    if args.limit:
        records = records[: args.limit]

    if args.dry_run:
        return dry_run_report(records, args.no_rewrite)

    if not records:
        log("No records with Video Status = 'Clip Generated' — nothing to do.")
        return 0

    if args.confirm is not None:
        if args.confirm.strip().lower() not in FIRE_WORDS:
            print(f"--confirm value {args.confirm!r} is not a fire word. "
                  f"Allowed: {sorted(FIRE_WORDS)}", file=sys.stderr)
            return 1
        # still compute totals for the log
        total_chars = sum(
            len(build_script(r, args.no_rewrite)[2]) for r in records
        )
        total_usd = total_chars * CREATOR_USD_PER_CHAR
        log(f"Cost gate bypassed via --confirm {args.confirm!r}. "
            f"Approved: {len(records)} record(s), {total_chars} chars, "
            f"~${total_usd:.4f}.")
    else:
        ok, total_chars, total_usd = confirm_cost(records, args.no_rewrite)
        if not ok:
            log("Aborted at cost gate — no API calls made.")
            return 1
        log(f"Confirmed. {len(records)} record(s), {total_chars} chars, "
            f"~${total_usd:.4f}.")

    summary = {"ok": 0, "failed": 0, "skipped_no_script": 0}
    for r in records:
        try:
            result = process_record(r, args.no_rewrite)
        except Exception as e:
            log(f"FAIL {r['id']}: {e}")
            result = "failed"
        summary[result] = summary.get(result, 0) + 1

    log(f"Run complete. Summary: {summary}")
    return 0 if summary.get("failed", 0) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
