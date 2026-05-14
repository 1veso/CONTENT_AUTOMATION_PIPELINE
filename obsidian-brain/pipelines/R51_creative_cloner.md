# R51 — Creative Cloner AI Agent

## What it does
RoboNuggets "Creative Cloner" — takes a reference creative (image or short video), reverse-engineers its structure / shot list / copy formula, then generates n variations adapted to a new brand or product brief.

## Tools used (per n8n template)
- Vision LLM (OpenAI gpt-4o / Claude / Gemini) for reference analysis
- OpenRouter / OpenAI for variant copy generation
- Fal.ai or KIE for image gen
- Airtable as variant tracker

## Credentials needed
- `OPENAI_API_KEY` / `OPENROUTER_API_KEY`
- `GOOGLE_API_KEY` (Gemini)
- `FAL_API_KEY`
- `AIRTABLE_API_KEY`

## Status
**Template only — not wired up.** JSON lives at `R51_creative_cloner/R51 _ The Creative Cloner AI Agent (by RoboNuggets).json`.

## n8n template
`R51_creative_cloner/R51 _ The Creative Cloner AI Agent (by RoboNuggets).json`

## Use case for Provinzial
Most directly useful for fast variation generation once a winning Provinzial creative is identified. Pair with [[../knowledge/tools_and_skills#ad-creative|ad-creative skill]] and [[../knowledge/tools_and_skills#ogilvy|ogilvy]] to keep variants on-brand.

## Related
- [[R46_ultimate_extract]]
- [[../frameworks/content_extraction_framework]]
- [[../clients/Provinzial_Geier_Ayhan/brand_brief]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §B @ canvas Y=[1540, 2640]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/r51` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** KIE Suno music inline (TODO swap to Fal Lyria-2). Triggered by R46 winners.
