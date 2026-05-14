# UGC Framework

Combines [[../pipelines/integrations/n21_infinite_ugcs]] + [[../pipelines/R39_split_ai_system]] + [[../pipelines/integrations/n19_ultimate_video_ads]] to produce unlimited UGC-style variants from a single product input.

## When to pick this framework
- The brief calls for *creator-style* video (handheld feel, talking-to-camera, "as if a real customer made it")
- You need **many variants of one idea**, not one polished spot
- The brand voice tolerates casual / energetic delivery — e.g., **NOT Provinzial** (calm-authority brand brief)

## Composition

| Role | Pipeline | Output |
|------|----------|--------|
| Strategy split | [[../pipelines/R39_split_ai_system]] | Hook / B-roll / VO / on-screen text routed to specialised models |
| Variant factory | [[../pipelines/integrations/n21_infinite_ugcs]] | Bulk-runner over product + script combos |
| Ads polish | [[../pipelines/integrations/n19_ultimate_video_ads]] | Extended split-AI for video-ad specifics |

## Execution order
1. Brief in → R39 splits it into role-prompts
2. n19 routes each role-prompt to the right model
3. n21 bulk-runs n distinct variants
4. Human review → [[../pipelines/R55_clipper]] -style approval loop
5. Schedule via Blotato ([[../knowledge/lessons_learned|hold applies]])

## Provider routing
- Image: Fal `nano-banana(/edit)` (NOT KIE — see [[../pipelines/integrations/n21_infinite_ugcs#KIE → Fal migration note]])
- Video: Fal `kling-video/v2.1/master/image-to-video` or `sora-2/image-to-video/pro`
- Voice: ElevenLabs (`eleven_multilingual_v2` for German)
- Stitch: Fal AI FFmpeg

## Provinzial fit
**Low.** Provinzial brand voice is calm-authority, not creator-energy. Save this framework for future non-Provinzial clients.

## Related
- [[video_ads_framework]] (for cinematic, non-UGC variant)
- [[../agents/per_pipeline_agents]]
