# n29 — Analyze Video (Send X, Get Y)

## What it does
Trio of RoboNuggets analyse-and-transform workflows that take a single input video and emit a different output asset:
- Send a TikTok → get a Sora video
- Send a YouTube long → get a LinkedIn or X post
- Send a YouTube Short → get a Script

## Tools used (per n8n JSONs)
- Apify or yt-dlp for source video pull
- Vision/transcription LLM (Gemini, GPT-4o, Whisper)
- Sora (via Fal) for video re-gen
- OpenAI / Claude for copy generation
- Airtable as input/output store

## Credentials needed
- `APIFY_TOKEN`
- `OPENAI_API_KEY` / `OPENROUTER_API_KEY`
- `GOOGLE_API_KEY`
- `FAL_API_KEY` (Sora)
- `AIRTABLE_API_KEY`

## Status
**Template only.** Files in `n29_templates/`:
- `🔺Send a Tiktok, 🔻get a Sora Vid _ n29 by RoboNuggets.json`
- `🔺Send a YT Long, 🔻get a LI or X post _ n29 by RoboNuggets.json`
- `🔺Send a YT Short, 🔻get a Script _ n29 by RoboNuggets.json`

(Note: vault path is `n29_analyze_video.md` though source folder is `n29_templates`.)

## n8n templates
See `C:/CONTENT_PIPELINE/n29_templates/` for the three JSON files.

## Use case for Provinzial
Send-YT-Long → LI/X is the most useful: pair with Provinzial brand brief to take long-form thought-leadership content and reformat for LinkedIn (Sparkassen-Finanzgruppe positioning per [[../../clients/Provinzial_Geier_Ayhan/brand_brief]]).

## Related
- [[../R46_ultimate_extract]]
- [[../R51_creative_cloner]]
- [[../../frameworks/content_extraction_framework]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §L1/L2/L3 @ canvas Y=[13540, 16240]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/n29-sora /webhook/n29-long /webhook/n29-short` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** Three variants: Sora (KIE TODO -> Fal Sora-2), Long (LI/X), Short (script). All telegramTriggers replaced with TODO stickies bound to lux_bot.
