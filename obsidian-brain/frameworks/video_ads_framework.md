# Video Ads Framework

Combines [[../pipelines/R61_video_pipeline]] + [[../pipelines/integrations/n30_product_videography]] + [[../pipelines/integrations/n31_precision_camera]] to produce cinematic, brand-controlled video ads on a daily cadence.

## When to pick this framework
- The brief calls for **polished, on-brand** spots (NOT UGC handheld)
- You need **tight camera-move control** (dolly-in, parallax, locked-off) rather than free motion
- A **brand brief exists** with explicit color / typography / tone rules — e.g., Provinzial

## Composition

| Role | Pipeline | Output |
|------|----------|--------|
| End-to-end daily ad | [[../pipelines/R61_video_pipeline]] | Frames → clip → VO → stitched 9:16 ad |
| Product hero shots | [[../pipelines/integrations/n30_product_videography]] | Multi-shot product videography (when needed) |
| Camera-move grammar | [[../pipelines/integrations/n31_precision_camera]] | Prompt grammar that lifts gen quality on Higgsfield / Veo / Sora |

## Execution order (Provinzial reference run)
1. R57 generates static images per day (consumed as `Source Image`)
2. R61 `frame_gen.py` → pillar-aware first/last frame pairs
3. R61 `video_gen.py` → Higgsfield kling3_0 5s clip
4. **Human gate 1** (clip approval)
5. R61 `voiceover_gen.py` → ElevenLabs (or Gemini temp)
6. **Human gate 2** (raw R2 footage select, if used)
7. R61 `hf_stitch.py` → intro+clip+outro stitch with audio
8. **Human gate 3** (pre-stitch sign-off)
9. **Human gate 4** (final preview)
10. R2 upload to `r61/final/v2/{filename}`
11. R61 `blotato_schedule.py` → wrapped-shape schedule (NEVER immediate post)

## Provider routing
- Frames: Fal `nano-banana/edit` (or `nano-banana` text-only)
- Clip: Higgsfield kling3_0
- Voice: ElevenLabs `eleven_multilingual_v2` (target); Gemini TTS via Fal (temp)
- Stitch: HyperFrames hybrid (FFmpeg under the hood)

## Brand controls
For Provinzial, all output flows through:
- [[../clients/Provinzial_Geier_Ayhan/brand_brief]]
- `provinzial-copy` skill (German copy rules) — overrides generic marketing skills

## Cost
- Frames: ~ $0.04 / image × 2 (first + last) = $0.08
- Higgsfield clip: 9.5 credits × 30 ≈ 285 credits (~ daily run)
- Gemini TTS: ~ $0.005 / spot
- See [[../knowledge/model_costs]] for the full table

## Related
- [[narrative_video_framework]] (when one spot needs > 5s)
- [[ugc_framework]] (when brand tolerates UGC tone)
