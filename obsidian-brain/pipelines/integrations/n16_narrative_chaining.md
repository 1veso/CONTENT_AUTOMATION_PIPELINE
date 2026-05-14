# n16 — Veo3 Narrative Chaining

## What it does
Chains multiple Veo 3 scene gens into one coherent narrative video. Each new scene's prompt references the previous scene's mood / character / location, with a controlled handoff frame so visual continuity holds across cuts.

## Tools used
- Veo 3 (Google) via Gemini API or Fal
- OpenAI / Claude for scene-script generation
- Airtable for scene-by-scene state tracking
- FFmpeg for stitch

## Credentials needed
- `GOOGLE_API_KEY` (Veo via Gemini) or `FAL_API_KEY`
- `OPENAI_API_KEY` / `OPENROUTER_API_KEY`
- `AIRTABLE_API_KEY`

## Status
**Template only.** Files: `🍳 Veo3 - Narrative Chaining (n16).json` (+ duplicate), `Kopija od [Template] Veo3 - Narrative Chaining by RoboNuggets.xlsx`, `n16 _ Cost breakdown.docx`.

## n8n template
`n16_narrative_chaining/🍳 Veo3 - Narrative Chaining (n16).json`

## Use case for Provinzial
Direct alternative to Higgsfield first/last-frame in [[../R61_video_pipeline]] when a spot needs more than 5s of motion. Pillar handoff (e.g., Sicherheit → Schaden → Service) is a natural fit for narrative chaining.

## Related
- [[n16.1_auto_subtitled_videos]] — companion subtitle flow
- [[../R34_veorobo]] — 3-scene Veo variant
- [[../../frameworks/narrative_video_framework]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §D @ canvas Y=[3940, 5140]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/n16` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** KIE Veo TODO swap to fal-ai/veo3-fast. Sheets TODO swap.
