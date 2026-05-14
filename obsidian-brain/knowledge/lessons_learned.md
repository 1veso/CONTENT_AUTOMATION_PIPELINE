# Lessons Learned

Cumulative non-obvious learnings from R55 / R57 / R61 build work. Each entry mirrors a memory note in `~/.claude/projects/C--CONTENT-PIPELINE/memory/`.

## Provinzial — R57 content engine

- KIE provider was ripped out and replaced with Fal.ai. Default to Fal for any image / video gen unless the user explicitly asks for Google or WaveSpeed.
- Fal model mappings:
  - `nano-banana-pro` → `fal-ai/nano-banana/edit` (refs) or `fal-ai/nano-banana` (text-only)
  - `kling-3.0` → `fal-ai/kling-video/v2.1/master/image-to-video`
  - `sora-2-pro` → `fal-ai/sora-2/image-to-video/pro`
- `FAL_API_KEY` env is bridged to `FAL_KEY` in `config.py` for the SDK.
- Doc files in R57 (`R57-README.md`, `.agent/AGENT.md`, etc.) still mention KIE in prose — informational only, not load-bearing.
- Airtable table: `May2025 - Provinzial_Geier&Ayhan` (`tblnpiwNYF3zJXm9Q`). `airtable.py::_table_url()` URL-encodes the name — `&` and spaces work, but update `config.AIRTABLE_TABLE_NAME` on any rename.

## Blotato hold (active)

- User verbatim, 2026-05-12: **"WE WAIT WITH POSTING!! WE CAN SCHEDULE IT BUT NOT YET POST!!"**
- Scheduled future-dated posts via Blotato are fine. Immediate posting is NOT — pause and confirm if any workflow considers a "now" endpoint.
- Hold stays in force until the user explicitly lifts it.

## Blotato API shape (current)

- Endpoint: `POST https://backend.blotato.com/v2/posts`, header `blotato-api-key: <key>`
- **Wrapped** shape (R57 docs reference the OLD flat shape which now returns 400):
  ```json
  {"post": {"accountId": "...", "target": {"targetType": "...", "mediaType": "..."}, "content": {...}}, "scheduledTime": "..."}
  ```
- Accounts: `GET /v2/users/me/accounts` — NOT `/v2/accounts` (that 401s)
- Max schedule window: **9 months**, beyond → `422 code 20011`
- No DELETE — bad scheduled posts can only be removed via dashboard UI
- `scheduledTime` is the safety pin; omitting it = immediate publish

## R2 clock skew (active workaround)

- Local Windows clock runs ~2h behind UTC (observed 2026-05-12: local 20:50:38Z vs Cloudflare 22:50:38Z).
- SigV4 rejects requests where signed timestamp drifts > 15 min. Every PutObject 403s without the workaround.
- Fix: monkey-patch **both** `botocore.utils.get_current_datetime` AND `botocore.auth.get_current_datetime` with a server-time-shifted version. Patching only `utils` is not enough — `auth` imports the function by name at module-load.
- Offset source: HEAD `https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com`, parse `Date` header.
- Working implementation: `R61_video_pipeline/tools/stitch.py::_patch_botocore_clock`.
- Don't bother with `Config(retries={...})` or replacing `datetime.datetime` — both fail.

## Fal Gemini TTS language enum

- Field `language_code` wants the full enum DISPLAY string, NOT an ISO code.
- ❌ `"de-DE"` → `literal_error`, no audio, no Fal billing
- ✅ `"German (Germany)"`
- Same shape for others: `"English (US)"`, `"French (France)"`, etc.
- R61 fix: `R61_video_pipeline/tools/voiceover_gen.py::TTS_LANGUAGE = "German (Germany)"`

## Never delete old content (golden rule)

- **Never delete, overwrite, or modify previously generated content** (renders, audio mixes, frames, exports, R2 uploads, intermediate tmp files).
- Always write new outputs to a new path: `final/v2/`, `r61/final/v2/`, `_v2`, `_new`, etc.
- Airtable attachment replacement is OK (old R2 file still exists), but the R2 path itself must be different.
- Tmp files in `references/outputs/tmp/` are not exempt — if `{rec_id}_clip.mp4` exists, don't `ffmpeg -y` over it.
- Never use `rm`, `Remove-Item`, or `-y` flags that silently clobber prior outputs.
- Only exception: strictly internal working files the user has not asked to preserve — when in doubt, suffix.

## Skill listing budget mechanics

- There is **no `hidden: true` frontmatter field**. It does not exist; I invented it once and `/doctor` still showed every "hidden" skill among 247 dropped.
- Only levers that actually reduce skill listing count:
  1. Move the skill directory **out of the discovery path** (e.g. `~/.claude/skills/<name>/` → `~/.claude/skills-disabled/<name>/`)
  2. Disable the source plugin via `enabledPlugins` in `settings.json` (global) or `.claude/settings.local.json` (per-repo) — requires Claude Code restart
  3. Raise `skillListingBudgetFraction` — palliative, not a fix
- Sources of bulk on this machine (2026-05-13): `everything-claude-code` plugin = 147 skills; `~/.claude/skills/` = 67; medusa/ecommerce/frontend-design = ~8.

## Marketing skills setup (2026-05-13)

- Installed globally to support all Provinzial work across R55/R57/R61:
  - `coreyhaines31/marketingskills` — 41 marketing skills (copywriting, ad-creative, social-content, page-cro, seo-audit, etc.)
  - `zubair-trabzada/ai-marketing-claude` — `market` orchestrator + 14 `market-*` sub-skills + 5 `market-*` agents + scripts + templates
  - `boraoztunc/skills/ogilvy` — David Ogilvy copy principles
  - `JuliusBrussee/caveman` — token-compression mode
- Project skill at `R61_video_pipeline/.claude/skills/provinzial-copy/` — German copy rules, overrides generic marketing skills. **Geier & Ayhan persona TODO** — awaits campaign brief from user.
- Trim pass + budget bump 2026-05-13: trimmed 41 marketingskills SKILL.md descriptions to <130 chars with triggers front-loaded; raised `skillListingBudgetFraction` from default 1% to **5%**.

## Operational rules (CLAUDE.md)

1. No throwaway scripts — extend `R57_content_engine/tools/` and `R61_video_pipeline/tools/` inline
2. Always confirm cost before any paid generation
3. Blotato posting is paused (schedule only)
4. R61 has four mandatory human gates (clip / raw select / pre-stitch / final preview)

## Related

- [[../clients/Provinzial_Geier_Ayhan/generation_notes]]
- [[../pipelines/R57_content_engine]]
- [[../pipelines/R61_video_pipeline]]
- [[tools_and_skills]]
- [[prompt_library]]
- [[n8n_credentials]]
