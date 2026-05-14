# Model Costs

Live cost tracker across all paid APIs. Prices are *approximate* — always verify at the provider before quoting to a user (per the cost-approval rule).

## R57 — Static images (Fal.ai)

| Model | Fal slug | Cost / image | Notes |
|-------|----------|--------------|-------|
| Nano Banana (text-only) | `fal-ai/nano-banana` | ~$0.04 | Default for R57 |
| Nano Banana edit (with refs) | `fal-ai/nano-banana/edit` | ~$0.05 | When R57 row has Reference Images |
| GPT Image 2 | (Fal route) | ~$0.07 | Backup |

**R57 Provinzial total so far (30 images):** ~$2.64

## R61 — Video frames & clips

| Model | Provider | Cost / unit | Used as |
|-------|----------|-------------|---------|
| Nano Banana Pro frame | Fal | ~$0.04 / frame × 2 (first + last) | R61 `frame_gen.py` |
| Higgsfield kling3_0 | Higgsfield direct | 9.5 credits / 5s clip | R61 `video_gen.py` |
| Kling 3.0 via Fal | `fal-ai/kling-video/v2.1/master/image-to-video` | ~$0.40 / clip | Backup |
| Sora 2 Pro | `fal-ai/sora-2/image-to-video/pro` | ~$0.50 / clip | Reserved for cinematic narrative |
| Veo 3 | Gemini API or Fal | ~$0.50-0.75 / clip | Narrative chaining ([[../frameworks/narrative_video_framework]]) |

**Higgsfield credits used to date:** 291.25 (30 clips first/last frame model)

## Voice (TTS)

| Provider | Model | Cost | Status |
|----------|-------|------|--------|
| Fal Gemini TTS | `fal-ai/gemini-tts` | ~$0.005 / spot | Temp, currently in use |
| ElevenLabs | `eleven_multilingual_v2` | Subscription tier (Creator+) | Pending — payment processing |

**R61 Gemini TTS total so far (8 spots):** ~$0.15 — wait, the user said "$0.15 Gemini TTS" in the brief. Logging that value verbatim.

**R61 Fal frames total (60 frames):** ~$0.16 — also from the brief.

## Long-form (R55)

| Service | Cost | Notes |
|---------|------|-------|
| Vizard | Monthly subscription tier | Long-form → Shorts |
| Modal compute | Per-second runtime | Negligible compared to Vizard |

## Stitch / post

| Tool | Cost |
|------|------|
| HyperFrames hybrid | Local CPU/GPU, no API cost |
| FFmpeg local | $0 |
| Fal AI FFmpeg combine | ~$0.01 / merge — only used in n21 / n19 templates |

## Storage

| Service | Cost | Notes |
|---------|------|-------|
| Cloudflare R2 | $0.015 / GB-month | `trendiva-raw-assets` bucket. **Egress is free** — major reason for choosing R2 over S3. |
| Airtable attachments | Free under base limit | Long-lived but bound to record |

## LLM (orchestration / copy)

| Provider | Use | Cost |
|----------|-----|------|
| OpenAI GPT-4o / 4o-mini | Copy, extraction | $5 / $15 per M tokens (4o); $0.15 / $0.60 (4o-mini) |
| Claude (current Opus 4.7 / Sonnet 4.6 / Haiku 4.5) | Orchestration, code | Per Anthropic pricing |
| OpenRouter | Multi-provider router | Pass-through + small margin |
| Gemini | Vision + Veo + TTS | Per Google AI pricing |

## Cost-approval rule

Per repo CLAUDE.md: **always confirm cost before any generation API call.** Check `R57_content_engine/tools/config.py` (COSTS table) for current Fal pricing; verify at fal.ai/models if quoting to user.

## Related

- [[../pipelines/R57_content_engine]]
- [[../pipelines/R61_video_pipeline]]
- [[lessons_learned]]
- [[n8n_credentials]]
