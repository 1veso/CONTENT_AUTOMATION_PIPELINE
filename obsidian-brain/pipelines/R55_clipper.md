# R55 — Clipper Agent

## What it does
Long-form video → YouTube Shorts / TikTok / Reels. User drops a long video into a watched folder (or sends via Telegram); pipeline calls Vizard to slice into vertical Shorts, surfaces each clip for human review via a Telegram bot, and pushes approved clips to Blotato for scheduling.

## Tools used
- **Vizard AI** — clip extraction + auto-reframing to 9:16
- **Telegram Bot** — review UI (approve / reject / re-clip per Short)
- **Blotato** — schedule approved clips across TikTok / Meta / Instagram
- **Modal** — deployed runtime (`vizard-clipper-secrets` secret bundle)

## Credentials needed
- `VIZARD_API_KEY`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `BLOTATO_API_KEY`
- See `R55_clipper_agent/.env.example` for full list; live secrets are in the Modal `vizard-clipper-secrets` bundle.

## Status
**Deployed and running on Modal.** Only pipeline currently in steady-state production.

## Airtable
None — R55 runs off Telegram bot state, not Airtable.

## n8n template
Not n8n-based. Modal-deployed Python service. See `R55_clipper_agent/AGENT.md` and `R55 - README.md` for the runtime spec.

## Posting hold
Blotato hold ([[../knowledge/lessons_learned]]) applies — schedule only, never immediate publish.

## Related
- [[R57_content_engine]]
- [[R61_video_pipeline]]
- [[../frameworks/narrative_video_framework]]
- [[../agents/per_pipeline_agents]]
