# n31 — Precision Camera Movements

## What it does
RoboNuggets n31 — sister flow to [[n30_product_videography]], focused on tight control of camera moves (dolly-in, arc, push, parallax, locked-off) in image-to-video gens. Built around a curated prompt grammar that maps clean English moves onto the model's actual capability.

## Tools used
- Image-to-video gen via Fal (Sora 2 Pro / Veo / Kling)
- Airtable project tracker (grid + gallery)

## Credentials needed
- `FAL_API_KEY`
- `AIRTABLE_API_KEY`

## Status
**Template only.** Files in `n31_precision_camera/`:
- `n31 _ Precision Camera Movements (by RoboNuggets).json`
- `n31 - ultra precise camera motion.png`
- `n31_precision camera airtable - Project-Grid view.csv` + `Project-Gallery.csv`

## n8n template
`n31_precision_camera/n31 _ Precision Camera Movements (by RoboNuggets).json`

## Use case for Provinzial
Camera-move grammar from n31 should be folded into [[../R61_video_pipeline]]'s `frame_gen.py` / `video_gen.py` prompt templates. Higgsfield kling3_0 responds to the same vocabulary — could lift first-pass quality further on top of pillar-aware prompts v3.

## Related
- [[n30_product_videography]]
- [[../R61_video_pipeline]]
- [[../../frameworks/video_ads_framework]]
- [[../../knowledge/prompt_library]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §J @ canvas Y=[11140, 12340]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/n31` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** Cleanest pipeline. WaveSpeed nano-banana + kling 2.5 turbo, no swaps required.
- **2026-05-25 (S15) validation fix:** `[J] Bottom Left` (httpRequest `b110e3ad`, WaveSpeed nano-banana-pro/edit) used `authentication:"predefinedCredentialType"` with the Fal.ai `httpHeaderAuth` cred bound but `nodeCredentialType` empty → "Credential Type cannot be empty". Set `parameters.nodeCredentialType:"httpHeaderAuth"` (REST verbatim PUT).
