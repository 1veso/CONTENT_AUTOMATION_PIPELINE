# R61 — Video Pipeline

Daily cinematic video ad pipeline for Provinzial. Frames → clip → voiceover → stitch → schedule. Four mandatory human gates.

## What it does
1. **Frames**: Nano Banana Pro / GPT Image 2 via Fal.ai — pillar-aware first/last frame pairs (`tools/frame_gen.py`)
2. **Clip**: Higgsfield ``kling3_0`` first/last frame → 5s 9:16 video (`tools/video_gen.py`)
3. **Voiceover**: Gemini TTS via Fal (temp), German — to be swapped to ElevenLabs (`tools/voiceover_gen.py`)
4. **Stitch**: HyperFrames hybrid — intro (2.75s) + clip (5s) + outro (2.75s) with pre-mixed audio (`tools/hf_stitch.py`)
5. **Upload**: Cloudflare R2 at ``r61/final/v2/{filename}``
6. **Schedule**: Blotato wrapped-shape API (`tools/blotato_schedule.py`)

## Tools used
- Fal.ai (frames + temp voiceover)
- Higgsfield (clip gen; skills copied from R55 into `.claude/skills/higgsfield/`)
- FFmpeg via HyperFrames adapter
- Cloudflare R2 (`trendiva-raw-assets` bucket)
- Airtable (campaign row source-of-truth)
- Blotato (scheduling only — never immediate post)
- ElevenLabs (pending payment unblock)

## Credentials needed
- `FAL_KEY`
- `HIGGSFIELD_API_KEY`, `HIGGSFIELD_SECRET`
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL`
- `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`
- `BLOTATO_API_KEY`
- `GOOGLE_API_KEY` (Gemini TTS)
- `ELEVENLABS_API_KEY` (pending)
- Stored in `R61_video_pipeline/.env`

## Status
**Active build — partially complete.**
- 30 records synced, 30 frame pairs, 30 Higgsfield clips
- 8 voiceovers (Gemini temp), 8 stitched v2 finals, 8 uploaded to R2, 8 Blotato-scheduled (2026-05-15 → 2026-05-22, 18:00 Berlin daily)
- 22 records waiting on ElevenLabs swap
- Captions not yet built into pipeline
- See [[../clients/Provinzial_Geier_Ayhan/generation_notes]] for what worked / failed

## Airtable
- Base: ``appC3HqG42ftswOvw``
- Table: ``Video`` (``tbl1hd8yprLTZia4c``)
- Consumes R57's `Source Image` as input

## Human review gates (cannot be auto-skipped)
1. After Higgsfield clip generation
2. After raw R2 footage selection (full manual — no auto-pull)
3. Before each FFmpeg / HyperFrames stitch
4. Full final preview before R2 upload + Blotato schedule

## Key files
- `tools/frame_gen.py` — pillar-aware first/last frame
- `tools/video_gen.py` — Higgsfield kling3_0
- `tools/voiceover_gen.py` — swap to ElevenLabs when unblocked
- `tools/hf_stitch.py` — canonical stitcher (HyperFrames hybrid)
- `tools/stitch.py` — old FFmpeg path; contains `_patch_botocore_clock` ([[../knowledge/lessons_learned#R2 clock skew]])
- `tools/blotato_schedule.py` — schedule only, refuses to submit without `scheduledTime`
- `references/inputs/intro.mp4`, `references/outputs/outro.mp4`
- `references/docs/provinzial_BRAND.md` → mirrored at [[../clients/Provinzial_Geier_Ayhan/brand_brief]]
- `HANDOVER.md`, `PIPELINE.md`, `README.md`

## n8n template
Not n8n-based — pure Python. n8n equivalents for narrative chaining live in [[integrations/n16_narrative_chaining]] and [[integrations/n29_analyze_video]]; for product/cinematic video in [[integrations/n30_product_videography]] and [[integrations/n31_precision_camera]].

## Rules
- **Never overwrite generated content** — version increment (`v2/`, `_v2`, etc.). See [[../knowledge/lessons_learned#Never delete old content]].
- **Never post via Blotato** — schedule only until hold is explicitly lifted.
- **Confirm cost before any paid generation call.**
- **No throwaway scripts** — extend existing tools inline.

## Resume prompt
> Read R61_video_pipeline/HANDOVER.md and PIPELINE.md. ElevenLabs is now unblocked. Swap voiceover_gen.py to ElevenLabs, run voiceover on all records with status reset to Clip Generated, re-stitch all 30 with hf_stitch.py, add captions via HyperFrames, and schedule all 30 in Blotato at 3–5 posts/day for one week.

## Related
- [[R57_content_engine]]
- [[R55_clipper]]
- [[../clients/Provinzial_Geier_Ayhan/campaign_log]]
- [[../clients/Provinzial_Geier_Ayhan/content_library]]
- [[../clients/Provinzial_Geier_Ayhan/generation_notes]]
- [[../frameworks/video_ads_framework]]
- [[../agents/per_pipeline_agents]]
