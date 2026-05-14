# Narrative Video Framework

Combines [[../pipelines/integrations/n16_narrative_chaining]] + [[../pipelines/integrations/n16.1_auto_subtitled_videos]] + [[../pipelines/R34_veorobo]] to produce multi-scene story-arc video — when one 5s clip is not enough.

## When to pick this framework
- The brief needs **a beginning / middle / end** within one spot
- You want **continuity** across cuts (same character, same location handoff)
- Captions / subtitles matter (insurance, financial, regulatory copy — see Provinzial brand brief)

## Composition

| Role | Pipeline | Output |
|------|----------|--------|
| Scene chaining | [[../pipelines/integrations/n16_narrative_chaining]] | N Veo3 scenes with last-frame → first-frame handoff |
| 3-scene template | [[../pipelines/R34_veorobo]] | Setup / escalate / resolve scaffold |
| Auto subtitles | [[../pipelines/integrations/n16.1_auto_subtitled_videos]] | ElevenLabs + NCA toolkit synchronized caption burn |

## Execution order
1. Brief → R34 scaffolds 3 scene prompts (or n16 for arbitrary n scenes)
2. Veo3 generates each scene; last-frame of scene k seeds scene k+1
3. FFmpeg or HyperFrames stitch the scenes
4. n16.1 transcribes the voiceover and burns subtitles
5. Human review
6. Schedule via Blotato (hold applies)

## Provider routing
- Video: Veo 3 (via Gemini API or Fal)
- Voice: ElevenLabs `eleven_multilingual_v2`
- Caption alignment: NCA Toolkit (whisper-style)
- Stitch: HyperFrames / FFmpeg

## Provinzial fit
**High** — three-act structure maps onto Provinzial pillars (e.g., normal life → claim event → calm Provinzial service), and captions are practically required for German financial content. Strong candidate to layer **on top of** [[video_ads_framework]] for select higher-stakes spots.

## Open question
Veo 3 vs Higgsfield kling3_0 (which [[../pipelines/R61_video_pipeline]] uses today) — Veo 3 handles longer continuous shots better but is more expensive and slower. Switching costs ~30-50% more per spot ([[../knowledge/model_costs]]).

## Related
- [[../pipelines/R61_video_pipeline]]
- [[video_ads_framework]]
- [[../clients/Provinzial_Geier_Ayhan/generation_notes]]
