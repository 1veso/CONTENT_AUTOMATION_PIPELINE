# Provinzial Pipeline — Portability Checklist

Tick-box list for migrating R61 + Obsidian to a new machine. Pair with [[secrets_bootstrap]].

## Pre-flight (on old machine)

- [ ] `git status` clean. Every working-tree change committed or stashed.
- [ ] `git log origin/main..HEAD` returns nothing (or you have explicitly chosen to push first).
- [ ] `R61_video_pipeline/.env` opened and every value confirmed legible — especially the Higgsfield secret and R2 secret (these cannot be retrieved if lost).
- [ ] Secrets manager snapshot: paste current `.env` into 1Password / Bitwarden / etc. as a one-time backup before rotating keys on the new machine.
- [ ] `cron-registry.json` reflects current enabled crons. Run a manual `CronList` and compare.

## Repository (already tracked — pulls down via `git clone`)

- [ ] Source code: `R55_clipper_agent/`, `R57_content_engine/`, `R61_video_pipeline/` (tools/, modal_app.py, README.md, etc.).
- [ ] Obsidian brain: `obsidian-brain/_index.md`, `obsidian-brain/clients/Provinzial_Geier_Ayhan/` (briefs, campaign log, content library, generation notes, secrets bootstrap, this checklist).
- [ ] Canonical brand inputs:
  - [ ] `R61_video_pipeline/references/inputs/wings.png`
  - [ ] `R61_video_pipeline/references/inputs/intro.mp4`
  - [ ] `R61_video_pipeline/references/inputs/outro_5s_audio_DEPRECATED.mp4`
- [ ] Canonical outro template: `R61_video_pipeline/references/outputs/outro.mp4`
- [ ] Shared infra: `cron-registry.json`, `shared/memory/convo_log_primary.md`, `SOUL.md`, `USER.md`, `CLAUDE.md`.
- [ ] `.env.example` file in `R61_video_pipeline/`.

## Local-only artifacts (must be recreated or re-fetched)

- [ ] `R61_video_pipeline/.env` — copy from `.env.example` and fill via [[secrets_bootstrap]].
- [ ] `.claude/telegram/.env` — bot token. Recreate via `/telegram:configure` skill.
- [ ] `shared/gates/pending.json` — runtime state. Will be re-populated by pipeline runs; no migration needed.
- [ ] `obsidian-brain/clients/Provinzial_Geier_Ayhan/assets/` — brand asset binaries. Re-download from source.
- [ ] `references/outputs/v3/`, `v4/`, day-N render outputs — pull from R2 (`trendiva-raw-assets` bucket) if you need older renders for reference.
- [ ] Python virtualenv `.venv/` for each pipeline — rebuild via `python -m venv .venv && pip install -r requirements.txt`.
- [ ] FFmpeg binary on PATH — install OS-specific.
- [ ] Bun runtime — install at `~/.bun/bin/bun` (path used by ClaudeClaw startup).

## Modal (cloud — already remote, no migration)

- [ ] `modal token new` on new machine.
- [ ] Confirm workspace = `hello-58046` (`modal profile current`).
- [ ] Confirm three apps still in `State: deployed`: `vizard-clipper`, `r57-content-engine`, `r61-video-pipeline`.
- [ ] Modal secrets `r57-secrets`, `r61-secrets`, `vizard-clipper-secrets` already live in the workspace — verify with `modal secret list`.

## Validation (after new-machine setup)

- [ ] `git log -1` shows the expected HEAD commit.
- [ ] `python -c "from R61_video_pipeline.tools import airtable_video as av; print(len(av.list_records()))"` returns a positive count.
- [ ] R2 list-buckets test passes (see step 5 in [[secrets_bootstrap#Migration steps for a new machine|secrets_bootstrap]]).
- [ ] `voiceover_gen.py --record-id <rec...> --dry-run` runs without crashing.
- [ ] All three crons register on ClaudeClaw startup (`morning-summary`, `keepalive`, `r61-gate-watcher`).
- [ ] Telegram bot reachable from new machine (send a `/start`, receive confirmation message).
- [ ] One manual gate approval round-trip works end-to-end (use a test record).

## Post-migration hygiene

- [ ] Old machine's `.env` shredded (`rm` followed by disk-flush) OR retained intentionally as a cold backup.
- [ ] Update `obsidian-brain/_index.md` to note the migration date and new machine identifier.
- [ ] Append a session entry to `shared/memory/convo_log_primary.md` documenting the migration.
