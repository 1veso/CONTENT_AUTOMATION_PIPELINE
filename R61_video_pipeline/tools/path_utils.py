"""
Path + slug helpers shared across R61 tools.

Two responsibilities, deliberately kept in one small module so every tool
imports them the same way:

  1. `check_output_path(path)` — version-increment guard. Returns the input
     path if free; otherwise appends `_v2`, `_v3`, ... until a free name is
     found, preserving the extension. Codifies [[SOUL.md]] rule 2 (never
     overwrite generated content).

  2. `clean_slug(name)` — filesystem- and CDN-safe slug. Strips brackets,
     ampersands, and other punctuation that's tripped us up at the
     FFmpeg/npx/R2 layer. Preserves German umlauts.

Both helpers are pure functions — they don't read or write any state.
"""

from __future__ import annotations

import re
from pathlib import Path


_RE_BRACKETS = re.compile(r"[\[\]\(\)\{\}]")
_RE_WIN_ILLEGAL = re.compile(r"[\\/:*?\"<>|]")
_RE_WHITESPACE = re.compile(r"\s+")
_RE_MULTI_UNDERSCORE = re.compile(r"_+")
_RE_V_SUFFIX = re.compile(r"^(.*)_v(\d+)$")


def clean_slug(name: str, max_len: int = 60) -> str:
    """Filesystem-safe slug.

    Rules:
      • Brackets `[]`, `()`, `{}` → stripped entirely.
      • Ampersand `&` → dropped (no `and` replacement — operator preference).
      • Windows-illegal chars `\\ / : * ? " < > |` → stripped.
      • Whitespace (any run) → single underscore.
      • Multiple consecutive underscores → one underscore.
      • Trailing/leading `._-` → stripped.
      • German umlauts (ä, ö, ü, ß, etc.) → preserved.
      • Truncated to `max_len` characters.

    Example:
      "Day 3 [Sicherheit & Vorsorge]"  →  "Day_3_Sicherheit_Vorsorge"
    """
    s = (name or "video").strip()
    s = _RE_BRACKETS.sub("", s)
    s = s.replace("&", "")
    s = _RE_WIN_ILLEGAL.sub("", s)
    s = _RE_WHITESPACE.sub("_", s)
    s = _RE_MULTI_UNDERSCORE.sub("_", s)
    return s[:max_len].strip("._-")


def check_output_path(path) -> Path:
    """Return a free path, version-incrementing if needed.

    If `path` does not exist on disk, returns it unchanged. Otherwise
    appends `_v2` / `_v3` / ... (or increments an existing `_vN` suffix)
    until a free name is found, preserving the extension.

    This enforces [[SOUL.md]] rule 2 — never overwrite a generated output.
    Source code and config files are NOT routed through this helper; they
    edit in place per rule 4's exception.

    Examples:
      foo.mp4  (free)             → foo.mp4
      foo.mp4  (exists)           → foo_v2.mp4
      foo_v2.mp4  (both exist)    → foo_v3.mp4
      foo_v7.mp4  (exists)        → foo_v8.mp4
    """
    p = Path(path)
    if not p.exists():
        return p
    stem = p.stem
    suffix = p.suffix
    m = _RE_V_SUFFIX.match(stem)
    if m:
        base = m.group(1)
        n = int(m.group(2)) + 1
    else:
        base = stem
        n = 2
    while True:
        candidate = p.with_name(f"{base}_v{n}{suffix}")
        if not candidate.exists():
            return candidate
        n += 1
