# {{CLIENT_NAME}} — Onboarding Checklist

Step-by-step from "new client" to "first campaign live in Blotato". Tick boxes as you go.

## 0. Pre-flight
- [ ] Signed engagement / scope confirmed
- [ ] Client folder created at `obsidian-brain/clients/{{CLIENT_SLUG}}/` (this template duplicated into it)
- [ ] Brand brief filled (`brand_brief.md`) — colors, pillars, voice, NEVER-list
- [ ] Posting hold state recorded in `campaign_log.md` (`ACTIVE` by default)

## 1. Brand-aware copy skill (optional)
- [ ] Decide whether this client needs a dedicated `{{client}}-copy` skill in `robo-skills/` or whether the generic `ogilvy` + `copywriting` skills are sufficient
- [ ] If dedicated: clone `robo-skills/.claude/skills/provinzial-copy/` as a starting point, swap brand rules

## 2. Airtable setup
- [ ] Create new table in base `appC3HqG42ftswOvw` named `{{Month}}{{Year}} - {{CLIENT_NAME}}` (R57-style schema)
- [ ] If video planned: create `{{CLIENT}}_Video` table (R61-style schema — see existing `Video` table `tbl1hd8yprLTZia4c` as reference)
- [ ] Note table IDs in `brand_brief.md`

## 3. R57 — Static image batch
- [ ] Caption sheet drafted (1 row per planned image, pillar tagged)
- [ ] Source prompts written (`generation_notes.md` v1)
- [ ] Cost quote calculated: `records × $/image` (see `R57_content_engine/tools/config.py` COSTS) → Telegram approval
- [ ] `python -m tools.image_gen --dry-run` clean
- [ ] Paid run — record outputs in `content_library.md`
- [ ] Human gate: review every image

## 4. R61 — Cinematic video batch (if applicable)
- [ ] `python -m tools.sync_r57_to_video --dry-run` clean
- [ ] Frame gen → Gate 0 (Telegram)
- [ ] Video gen (Higgsfield) → Gate 1 (Telegram)
- [ ] R2 raw-footage selection → Gate 2 (manual)
- [ ] Voiceover gen (ElevenLabs / Gemini TTS) → cost-approval gate
- [ ] Stitch → Gate 4 (final preview)
- [ ] Update `content_library.md` with every final R2 URL

## 5. Blotato scheduling
- [ ] Confirm posting hold is to be LIFTED for this client (explicit user OK, not implied)
- [ ] `python -m tools.blotato_schedule --dry-run` clean — verify every entry has a future `scheduledTime`
- [ ] Schedule grid filled in `campaign_log.md` (1-week or 1-month)
- [ ] Interactive paid run with per-record gate
- [ ] All records now `Scheduled`

## 6. Hand-off / ongoing
- [ ] Note any pillar-specific learnings in `generation_notes.md`
- [ ] Update `obsidian-brain/_index.md` so the client appears in the Active list
- [ ] Schedule the recurring tasks (cron entries, if any)
