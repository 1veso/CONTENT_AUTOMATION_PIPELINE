# n30 — Product Videography

## What it does
RoboNuggets n30 product video pipeline. Takes a product image / reference and generates cinematic product videography (multi-shot, choreographed camera moves). Sister flow to [[n31_precision_camera]] which focuses on precise camera-move control.

## Tools used
- Image-to-video gen (Sora 2 Pro / Veo / Kling via Fal)
- System prompt encodes shot-list / camera-move discipline (see `System Prompt - Product Videography by RoboNuggets (n30).md`)
- Airtable for project tracking (grid + gallery views provided as CSV)

## Credentials needed
- `FAL_API_KEY`
- `AIRTABLE_API_KEY`

## Status
**Template only.** Files in `n30_product_videography/`:
- `n30 _ Product Videography (by RoboNuggets) (1).json`
- `System Prompt - Product Videography by RoboNuggets (n30).md`
- `n30 _ Cost breakdown.md`
- `n30 airtable - Project-Grid view.csv` + `Project-Gallery.csv`
- `n30 pipeline.png`

## n8n template
`n30_product_videography/n30 _ Product Videography (by RoboNuggets) (1).json`

## Use case for Provinzial
Most useful if Provinzial commissions product-style spots for specific coverage products (e.g., car insurance hero shot, home insurance object stills). Pair with [[../R61_video_pipeline]] for the daily delivery cadence.

## Related
- [[n31_precision_camera]]
- [[../R61_video_pipeline]]
- [[../../frameworks/video_ads_framework]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §I @ canvas Y=[9940, 11140]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/n30` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** googleGemini -> TODO sticky. switch v3.4 capped to v3.2. KIE Veo TODO swap to Fal.

## Telegram launch

Command `/n30` via `lux_bot` → `[Telegram Router]` Switch (canvas `SmtkmTgfCTLZPlN4`) → `[I] Get Project` (id `cd4102fd-38bd-4f92-93f4-2210ff545a88`). Parallel to webhook/schedule trigger; both stay live. See [[../../knowledge/webhook_registry#Telegram bot commands]].
