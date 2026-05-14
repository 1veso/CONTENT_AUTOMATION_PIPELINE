# Prompt Library

All prompt versions used across the pipelines. Source of truth for the iterations that worked; companion to [[../clients/Provinzial_Geier_Ayhan/generation_notes]].

## R57 — image gen (Fal nano-banana)

**System prompt (current v3):** pillar-aware, embedded in `R57_content_engine/tools/prompts.py` (or the equivalent in `tools/`). Each row's `Image Prompt` is built from: pillar → scene whitelist → mood → what-NOT-to-show, then merged with `Ad Name` and any references from `Reference Images`.

Provinzial defaults baked in:
- 9:16 aspect
- Warm natural lighting, German everyday environments
- Color grading toward `#005940` palette
- Yellow wings watermark bottom-right
- People 25-55, diverse, *never* staged-stock-photo aesthetic

## R61 — frame gen (Nano Banana Pro)

### v1 (deprecated)
Generic "German family at home" lifestyle prompts, no pillar steering.

### v2 (deprecated)
Pillar as keyword only, LLM treated it as filler.

### v3 (shipped — `tools/frame_gen.py`)
Pillar as scene-constraint with three slots:
1. **Scene-type whitelist** per pillar
2. **Mood vector**
3. **NOT-to-show list**

Per-pillar whitelist (abbreviated):

| Pillar | Scene types | Mood | NOT |
|--------|-------------|------|-----|
| Sicherheit im Alltag | kitchen morning, hand on steering wheel, child seat, helmet strap | calm-grounded | flashing lights, dramatic close-ups |
| Vorsorge & Zukunft | daughter moving out, walking in meadow, grandparents-grandchild | quiet-pride | nursing home cliches, money on table |
| Schaden & Service | calm phone call, adjuster handshake, agent portrait | matter-of-fact | destroyed property, sirens |
| Regional & Gemeinschaft | Kreisliga, Bäcker, Wochenmarkt, volunteer firefighter | warm-local | tourism-y "german village" shots |
| Produktaufklärung | over-shoulder explainer, plate text, hands signing | educational-clean | text-heavy infographics, jargon graphics |

## R61 — video gen (Higgsfield kling3_0)

First-frame + last-frame inputs come from the v3 frame-gen output. Camera-move grammar overlay (planned, from [[../pipelines/integrations/n31_precision_camera]]):
- `dolly-in slow` / `dolly-out slow`
- `locked-off`
- `arc 30°`
- `parallax left`

Currently only `locked-off` and `slow push` are used reliably — n31 grammar pending integration.

## R61 — voiceover

### Gemini TTS (temp)
- `language_code: "German (Germany)"` — **NEVER `de-DE`**, ISO codes hard-fail with `literal_error`
- Voice: `Kore` (German neutral) — adequate for QA, wrong tone for brand
- Prompt template: just the German VO script, no SSML

### ElevenLabs (target)
- Model: `eleven_multilingual_v2`
- Voice routing by index parity:
  - Odd index → `Jones` (`niMwYIP6tIdlsdDEGVdT`, male) — Schaden & Service / Produktaufklärung
  - Even index → `Clara` (`E13qNLHLLuVPKQvesCoy`, female) — Sicherheit / Vorsorge / Regional
- Stability 0.5, similarity 0.75, style 0.3 (calm authority baseline; tweak per spot)

## Caption / on-screen text

- German Du-default per Provinzial copy skill
- One reassurance line per spot, never urgency / fear / hype
- CTA always: simple, direct, Link in Bio
- Hashtag cap: 1-2 max (see `brand_brief` caption formula)

## Cross-pipeline rules

- **Cost-approval gate** before any paid gen call
- Output naming: `{idx}_{slug}.mp4`, with `_v2` / `_v3` suffix on iteration (never overwrite)

## Related

- [[../clients/Provinzial_Geier_Ayhan/brand_brief]]
- [[../clients/Provinzial_Geier_Ayhan/generation_notes]]
- [[lessons_learned]]
- [[model_costs]]
