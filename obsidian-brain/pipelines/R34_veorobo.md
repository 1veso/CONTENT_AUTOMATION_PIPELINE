# R34 — VeoRobo (3-scene Veo template)

## What it does
RoboNuggets 3-scene Veo template — chains three Veo 3 generations into a single narrative spot. Scene 1 sets up, Scene 2 escalates, Scene 3 resolves; each scene's last frame seeds the next scene's first frame for visual continuity.

## Tools used (per n8n template)
- Google Veo 3 (via Vertex AI or Gemini API)
- Fal.ai (alternative Veo access)
- Airtable for scene-prompt tracking
- ElevenLabs (optional voiceover overlay)

## Credentials needed
- `GOOGLE_API_KEY` (Veo via Gemini)
- `FAL_API_KEY` (Veo via Fal)
- `AIRTABLE_API_KEY`
- `ELEVENLABS_API_KEY`

## Status
**Template only — not wired up.** JSON lives at `R34_veorobo/R34___VeoRobo_Template__3_scenes__by_RoboNuggets.json` with a pipeline diagram at `R34.png`.

## n8n template
`R34_veorobo/R34___VeoRobo_Template__3_scenes__by_RoboNuggets.json`

## Use case for Provinzial
3-scene structure maps cleanly onto Provinzial pillars (e.g., Sicherheit → Schaden → Service narrative arc). Could replace Higgsfield in [[R61_video_pipeline]] for spots that need longer-than-5s coverage without a manual stitch.

## Related
- [[../pipelines/integrations/n16_narrative_chaining]]
- [[R61_video_pipeline]]
- [[../frameworks/narrative_video_framework]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §C @ canvas Y=[2740, 3840]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/r34` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** KIE-stripped, Sheets-stripped per source. Ready once Fal+Airtable+Blotato creds bound.

## Telegram launch

Command `/r34` via `lux_bot` → `[Telegram Router]` Switch (canvas `SmtkmTgfCTLZPlN4`) → `[C] Elements AI Agent` (id `5463cc23-a3c6-4f16-a1dd-2176cb42ceb6`). Parallel to webhook/schedule trigger; both stay live. See [[../knowledge/webhook_registry#Telegram bot commands]].
