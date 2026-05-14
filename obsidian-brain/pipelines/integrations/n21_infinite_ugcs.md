# n21 — Infinite UGCs (Ultimate UGC Creator)

## What it does
End-to-end UGC ad factory. From a single product input it produces unlimited UGC-style spots: image gen for actor scenes, Veo3-fast for motion, FFmpeg combine via Fal AI, output to Airtable for review and Blotato for scheduling. Includes a bulk runner workflow for batch operations.

## Tools used (per n8n JSON)
- KIE AI for image gen (Nanobanana, Seedream 4.0, GPT-image-1) — **replace with Fal per project rule**
- KIE AI for Veo3-fast video — also moves to Fal
- Fal AI for FFmpeg combine
- Airtable for variant tracking
- Blotato for posting

## Credentials needed
- `KIE_API_KEY` → migrated to `FAL_API_KEY`
- `AIRTABLE_API_KEY`
- `BLOTATO_API_KEY`

## Status
**Template only — has KIE legacy that must be migrated to Fal before live use.** Files: `n21 - Ultimate UGC Creator (by RoboNuggets).json`, `n21 - Bulk Runner for Ultimate UGC Creator.json`, plus sub-flows for each gen step and `🍳 Combine Clips (FFMPEG via Fal AI).json`.

## n8n templates
- Main: `n21_infinite_ugcs/n21 - Ultimate UGC Creator (by RoboNuggets).json`
- Bulk runner: `n21_infinite_ugcs/n21 - Bulk Runner for Ultimate UGC Creator.json`
- Sub-flows: `🍳 Create Image (...)` × 3 + `🍳 Create Video (Veo3-fast via Kie AI).json` + `🍳 Combine Clips (FFMPEG via Fal AI).json`

## Use case for Provinzial
UGC angle is currently unused for Provinzial (brand voice is calm-authority, not UGC). But the bulk-runner pattern is reusable for the 30-day [[../R61_video_pipeline]] batches.

## KIE → Fal migration note
Per project convention KIE is ripped out. When activating n21, swap each KIE sub-flow for the Fal equivalents: `fal-ai/nano-banana(/edit)`, `fal-ai/kling-video/v2.1/master/image-to-video`, `fal-ai/sora-2/image-to-video/pro`.

## Related
- [[../R39_split_ai_system]]
- [[n19_ultimate_video_ads]]
- [[../../frameworks/ugc_framework]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §H @ canvas Y=[8740, 9940]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/n21` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** 5 executeWorkflow calls TODO stickies (sub-workflow ids missing). KIE swaps required in subs.
