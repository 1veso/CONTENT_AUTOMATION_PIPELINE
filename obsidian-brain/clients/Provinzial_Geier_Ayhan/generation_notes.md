# Provinzial Generation Notes

Captures what actually worked and what didn't across the R57 / R61 production runs. Companion to [[brand_brief]] and [[content_library]].

## Frame-gen prompt evolution

### v1 — too generic
First pass used generic German lifestyle prompts ("German family at home", "couple in NRW") with no pillar steering. Result: visually fine but indistinguishable from any insurance stock library. Brand value zero.

### v2 — pillar-tagged, still flat
Tagged each prompt with its pillar (`Sicherheit im Alltag`, `Vorsorge & Zukunft`, etc.) but the LLM treated pillars as keywords, not as scene constraints. Schaden & Service shots kept looking happy; Regional & Gemeinschaft shots had no actual regional cues.

### v3 — pillar-as-scene-constraint (shipped)
Rewrote the system prompt so each pillar carries:
1. A **scene-type whitelist** ("kitchen morning", "hand on steering wheel", "Kreisliga sidelines")
2. A **mood vector** (calm-grounded vs. quiet-pride vs. matter-of-fact)
3. A **what-NOT-to-show list** (no flashing lights, no destroyed property, no over-styled stock-photo poses)

v3 is the version embedded in `R61_video_pipeline/tools/frame_gen.py`. Pillar-aware first/last frame pairs hit on the first generation for ~26/30 records; the other 4 needed one re-roll each.

## Voice selection rationale

- **Gemini TTS (Fal) — current temp**: German "Provinzial" sounds robotic on Insurance-trust copy. Pronounces brand name `Provinzial` correctly but cadence is wrong for the calm-authority tone in [[brand_brief]]. Useful only for stand-in QA.
- **ElevenLabs (target)**: Two voices chosen by pillar/index parity to avoid same-voice fatigue across the 30-day calendar:
  - `Jones` (`niMwYIP6tIdlsdDEGVdT`) — male, odd indices, used for Schaden & Service / Produktaufklärung (authority pillars)
  - `Clara` (`E13qNLHLLuVPKQvesCoy`) — female, even indices, used for Sicherheit im Alltag / Vorsorge & Zukunft / Regional (warm pillars)
  - Model: `eleven_multilingual_v2` — handles German correctly, including `Selbstbehalt`, `Haftpflicht`, `Schadenmeldung`.
- **Trigger to swap**: ElevenLabs payment is still processing (support ticket open at hello@trendivalux.com). When unblocked, run `R61_video_pipeline/tools/voiceover_gen.py` with `ELEVENLABS_API_KEY`, then re-stitch all 30 via `hf_stitch.py`. Do not overwrite Gemini renders — they go in `references/outputs/final/v1/` (and the new ones into `final/v2/`).

## Intro / outro

- 2.75s each — long enough for the wing logo reveal, short enough to keep the 5s Higgsfield clip dominant.
- Intro: Provinzial green `#005940` with yellow wings `#FFD000`.
- Outro: white with yellow wings + `Sicherheit. Klarheit. Provinzial.` lockup.
- Both produced once and re-used across all 30 records via `hf_stitch.py` (HyperFrames hybrid). Do not re-render per spot.

## What worked

- **Pillar-aware prompts (v3)** — biggest single quality win; ~87 % first-pass hit rate.
- **HyperFrames hybrid stitch** — intro + clip + outro with pre-mixed audio in one render pass; cleaner than chained FFmpeg concat.
- **Gemini TTS language enum hardcode** — `"German (Germany)"` literal, NOT `de-DE`. ISO codes hard-fail Fal validation pre-render (see [[../../knowledge/lessons_learned]]).
- **R2 clock-skew patch** — local clock is ~2h behind UTC; `_patch_botocore_clock` in `tools/stitch.py` reads server time off Cloudflare and rewrites `botocore.utils.get_current_datetime` + `botocore.auth.get_current_datetime`. Without it, every PutObject 403s.
- **Wrapped Blotato schema** — `{post: {...}, scheduledTime}` is the only shape that works; R57's old flat-shape SKILL.md is outdated.

## What failed

- **Auto-pulling raw R2 footage** — never wired up. Manual selection is faster and the human gate is mandatory anyway.
- **Captions** — not yet built. Plan: HyperFrames `references/captions.md` patterns, added to `hf_stitch.py` as an optional pass.
- **R2 filename slugs with brackets** — `[Sicherheit_im_Alltag].mp4` filenames break some downstream URL parsers; cleanup pending.
- **First Gemini TTS run** — `language_code: "de-DE"` failed all 30 records with `literal_error`. Wasted ~5 min before reading the enum.

## TODOs

1. ElevenLabs swap + re-stitch all 30 → v2 finals → R2 v2 → Airtable PATCH
2. Captions via HyperFrames
3. Remaining 22 records: voiceover → stitch → schedule
4. Build 1-week (3-5 posts/day) and 1-month schedule grids
5. R2 filename slug cleanup (strip brackets)
6. Version-increment rule in IO table — never overwrite

## Related

- [[brand_brief]]
- [[campaign_log]]
- [[content_library]]
- [[../../pipelines/R61_video_pipeline]]
- [[../../pipelines/R57_content_engine]]
- [[../../knowledge/lessons_learned]]
- [[../../knowledge/prompt_library]]
