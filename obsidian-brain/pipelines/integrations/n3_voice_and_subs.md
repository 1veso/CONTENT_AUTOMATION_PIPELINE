# n3 — Monetizable TikToks AI Machine with voice & subs

## What it does
Takes a script (or auto-generated topic) → ElevenLabs voiceover → auto-subtitle overlay → uploads finished short to TikTok / Reels / Shorts via Blotato. End-to-end "set a topic, get a posted video".

## Tools used (per n8n JSON)
- OpenAI / OpenRouter for script
- ElevenLabs for voice
- NCA Toolkit (or FFmpeg) for subtitle burn-in
- Cloudinary or Box for media handoff
- Blotato for posting

## Credentials needed
- `OPENAI_API_KEY` / `OPENROUTER_API_KEY`
- `ELEVENLABS_API_KEY`
- `CLOUDINARY_URL` / `BOX_*`
- `BLOTATO_API_KEY`

## Status
**Template only.** Files: `n3 - Monetizable Tiktoks AI Machine with voice and subs.json`, `n3 automation.png`.

## n8n template
`n3_voice_and_subs/n3 - Monetizable Tiktoks AI Machine with voice and subs.json`

## Use case for Provinzial
Voice + subs flow is the missing captioning piece for [[../R61_video_pipeline]]. Worth porting the subtitle-burn block into `hf_stitch.py`.

## Posting hold
Blotato leg is paused until hold lifts. See [[../../knowledge/lessons_learned]].

## Related
- [[n16.1_auto_subtitled_videos]]
- [[../../frameworks/narrative_video_framework]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §K @ canvas Y=[12340, 13440]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/n3` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** Sheets -> Airtable swap TODO. Two Fal cred entries still need consolidation.

## Telegram launch

Command `/n3` via `lux_bot` → `[Telegram Router]` Switch (canvas `SmtkmTgfCTLZPlN4`) → `[K] Create New Idea` (id `66985906-2529-42e8-bb38-0586b3666cf1`). Parallel to webhook/schedule trigger; both stay live. See [[../../knowledge/webhook_registry#Telegram bot commands]].
