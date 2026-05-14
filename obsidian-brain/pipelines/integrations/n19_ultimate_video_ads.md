# n19 — Ultimate Video Ads (Split AI System extended)

## What it does
Extension of [[../R39_split_ai_system]] specifically tuned for video ads. Splits a single ad brief into role-specialised sub-flows (hook copy, on-screen text, product B-roll, environment B-roll, voiceover) and reassembles with FFmpeg.

## Tools used
- Multiple LLMs (Claude / GPT / Gemini in parallel)
- Nano Banana via Fal (was KIE)
- Veo 3 / Kling / Sora for clip gen
- ElevenLabs / Gemini TTS for voice
- FFmpeg via Fal AI for stitching

## Credentials needed
- `OPENAI_API_KEY` / `OPENROUTER_API_KEY`
- `GOOGLE_API_KEY`
- `FAL_API_KEY`
- `ELEVENLABS_API_KEY`
- `AIRTABLE_API_KEY`

## Status
**Template only.** Files: `🍌 Split AI System extended (by RoboNuggets) _ n19.json`, `sample image from system.jfif`.

## n8n template
`n19_ultimate_video_ads/🍌 Split AI System extended (by RoboNuggets) _ n19.json`

## Use case for Provinzial
Architecturally what [[../R61_video_pipeline]] is implementing in Python. Reference for any future n8n port of R61.

## Related
- [[../R39_split_ai_system]]
- [[n21_infinite_ugcs]]
- [[../../frameworks/ugc_framework]]
- [[../../frameworks/video_ads_framework]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §G @ canvas Y=[7540, 8740]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/n19` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** Heaviest rewrite: KIE+Box+Sheets+Telegram (telegramTrigger TODO sticky -> lux_bot).
