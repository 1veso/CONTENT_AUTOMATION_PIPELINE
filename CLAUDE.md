# CONTENT_PIPELINE

Three content pipelines for **Provinzial** (Geier & Ayhan campaign). Shared Airtable base, shared Blotato accounts, all gated by the same posting hold.

## Session Startup (ClaudeClaw — Phase 1)

On every new session, complete these steps **before responding to the user**:

1. Read `SOUL.md` (non-negotiable shared rules) and `USER.md` (operator profile).
2. Read `obsidian-brain/_index.md` for current pipeline state — that's the source of truth for what's queued, shipped, and blocked.
3. Read `cron-registry.json` and recreate **every enabled** cron via `CronCreate`. Confirm each one registered.
4. Read `shared/memory/convo_log_primary.md` for the most recent session handoff.
5. Send a single Telegram message confirming you're back online, listing which crons registered, and naming any pending R61 gates from `shared/gates/pending.json`.

## Identity (Primary Agent)

- **Name:** Primary
- **Role:** Coordinator across R55, R57, R61. Triage, planning, status checks, gate notifications. Quick tasks stay here; deep pipeline work happens in the pipeline's own folder.
- **Channel:** Telegram (single bot, allowlisted to chat 1077552316)
- **Posting hold:** ACTIVE. See SOUL.md rule 1.

## Approval Required (Telegram)

Ping the user on Telegram and wait for explicit approval before:
- Calling any paid generation API (Fal, Higgsfield, Vizard, ElevenLabs, Gemini) — surface USD cost first
- Deleting or overwriting any file (everything is version-incremented per SOUL.md rule 2/4)
- Posting anything via Blotato (and even then, only as `scheduledTime` — never immediate)
- Lifting the Blotato posting hold for any client
- Advancing past any R61 human gate

Safe operations (reading, searching, building, testing, dry-runs) — just do them.

## Context Recovery

After meaningful exchanges or completed tasks, append a structured entry to `shared/memory/convo_log_primary.md` (active context, completed, pending, key decisions). Keep last 3 sessions, prepend new above old.

## ClaudeClaw Agent Architecture

**Phase 1:** Single primary agent at repo root. One Telegram bot covers all three pipelines. Per-pipeline alpha/beta/gamma split deferred until Phase 1 has run cleanly for ≥1 week.

**Launch (from `C:\CONTENT_PIPELINE\`):**

```powershell
claude --dangerously-skip-permissions --channels plugin:telegram@claude-plugins-official
```

Prerequisites (done): Bun at `C:\Users\benja\.bun\bin\bun.exe`; Telegram plugin loaded inside Claude Code via `/plugin install telegram@claude-plugins-official`.

**Cron schedule (Europe/Berlin, recreated on every session startup):**

| ID | Cron | Purpose |
|---|---|---|
| `morning-summary` | `0 8 * * *` | Daily digest: obsidian state + Airtable counts + pending gates → Telegram |
| `keepalive` | `0 */6 * * *` | Silent connection check. Never messages the user. |
| `r61-gate-watcher` | `*/15 * * * *` | Polls `shared/gates/pending.json`, surfaces unnotified entries with approve/redo/hold options |

**Gate-notification pattern (R61):**

Pipeline scripts never talk to Telegram directly. They append a JSON entry to `shared/gates/pending.json` via `R61_video_pipeline/tools/_gates.append_gate(...)`. The `r61-gate-watcher` cron picks it up within 15 min.

Wired write points:
- `frame_gen.py` end-of-batch → Gate 0 (frames ready for review)
- `video_gen.py` end-of-batch → Gate 1 (clips ready — CLAUDE.md Gate 1)
- `hf_stitch.py` per record after publish → Gate 4 (final preview — CLAUDE.md Gate 4)

Full schema and rationale in `obsidian-brain/agents/per_pipeline_agents.md`.

## Gate Reply Handler

Triggered when the operator taps a button on a Telegram inline keyboard sent by `r61-gate-watcher`. Each button carries `callback_data = "gate:<option_lower>:<record_id>"` (e.g. `gate:approve:rec4cuKlnZwe0Slag`). See the Telegram-inline-keyboards section in `obsidian-brain/agents/per_pipeline_agents.md` for the keyboard rendering rules.

**Protocol — execute in this order, no shortcuts:**

1. **Parse the callback.** Split `callback_data` on `:` into `["gate", verb, record_id]`. If the prefix isn't `gate` or there are fewer than three parts, ignore — not a gate callback.

2. **Update local state first.** Open `shared/gates/pending.json`, find the gate entry whose `record_id` matches AND `status == "pending"`, then:
   - `approve` → set `status = "approved"`
   - `redo` → set `status = "rejected"`, then send a follow-up Telegram message asking for the reason; on the operator's text reply, merge `{reason: "<text>"}` into `extra`
   - `hold` → leave `status = "pending"` (acknowledge only)
   - Custom verbs (e.g. `use take 1`, `use take 2`) → set `status = "approved"` and merge `{choice: "<verb>"}` into `extra` — these come from per-gate `options[]` overrides
   
   Append `{operator_reply: "<verb>", reply_at: "<iso ts>"}` to the entry. Write atomically (write to `.tmp` then `os.replace` — same pattern `_gates.py` uses). This MUST succeed before proceeding.

3. **Determine target Airtable status by gate number AND verb:**

   | Gate # | approve verb → status | redo verb → status | hold verb |
   |---|---|---|---|
   | 0 (frames batch) | (no Airtable change — frames stay `Frames Generated`; if redo, operator re-runs `frame_gen.py --record-id <id>`) | (no Airtable change) | no-op |
   | 1 (clip batch) | `STATUS_APPROVED` ("Approved") | `STATUS_REJECTED` ("Rejected") | no-op |
   | 4 (stitch final) | `STATUS_APPROVED` ("Approved") — Blotato schedule reads Approved rows | `STATUS_REJECTED` — operator re-runs `hf_stitch.py --record-id <id>` later | no-op |

   For batch-level gates (`record_id == "batch"`), the keyboard sends one button per record id from `extra.batch_record_ids`; the callback then carries the per-record id, so the handler always sees a real record id.
   
   For custom verbs without a defined Airtable mapping, default to `STATUS_APPROVED` and log the verb to convo log — do not invent a status.

4. **Shell out to update Airtable.** Same subprocess-delegation pattern as the morning-summary cron — `airtable_video.py` loads its own `.env` via dotenv inside the Python subprocess, so the deny list does not block it. Run with cwd = `C:\CONTENT_PIPELINE\`:

   ```powershell
   python -c "import sys; sys.path.insert(0, 'R61_video_pipeline'); from tools import airtable_video as av; av.set_status('<RECORD_ID>', av.STATUS_APPROVED); print('ok')"
   ```

   For redo, swap `STATUS_APPROVED` → `STATUS_REJECTED`. The script prints `ok` on success or raises with a traceback on failure (non-zero exit). Capture stderr for the degradation message.

5. **Reply to operator on Telegram based on outcome:**

   - **Both succeeded** (local + Airtable): edit the original gate message to show `✅ Approved — Airtable status: Approved` (or `🔁 Redo queued — Airtable status: Rejected. Reason: <text>`).
   - **GRACEFUL DEGRADATION — local OK, Airtable failed:** reply with the exact phrase `Local approval recorded but Airtable update failed: <reason>. Please update Airtable manually.` Include the record ID and the target status. Do not retry silently — the operator needs to know.
   - **Local update failed:** reply `Could not update local gate state: <reason>. No action taken.` and stop. Never touch Airtable if local state is inconsistent.

6. **Log the exchange** to `shared/memory/convo_log_primary.md` under a "Gate replies" subsection with timestamp, record_id, verb, target status, Airtable outcome (ok / failed-with-reason).

**Why this delegation pattern, not direct HTTP:** the deny list blocks the agent from reading `.env` files (intentional — protects Airtable/Fal/Higgsfield/R2 credentials). The Python subprocess loads `.env` via `dotenv` at import time, which is invisible to Claude's permission system. Same trick as morning-summary. Do not work around the deny list — use the subprocess.

## Repo Structure

```
C:\CONTENT_PIPELINE\
├── R55_clipper_agent\        # Long-form video → YouTube Shorts clipper (Vizard + Telegram)
├── R57_content_engine\       # Daily static images for social (Fal.ai)
├── R61_video_pipeline\       # Daily cinematic ad videos (Fal frames → Higgsfield clip → FFmpeg)
├── obsidian-brain\           # Obsidian vault — pipelines, frameworks, client log, lessons (start here: obsidian-brain/_index.md)
└── robo-skills\              # Shared skills directory
```

| Pipeline | Purpose | Status |
|---|---|---|
| **R55** | Vizard takes long-form video, slices into Shorts, Telegram bot for review, Blotato schedule | **Deployed (Modal), running** |
| **R57** | Fal.ai static image gen → Airtable → Blotato schedule. 30 images generated. | **Complete — all 30 images scheduled in Blotato. Deployed (Modal) 2026-05-14, app `r57-content-engine`.** |
| **R61** | Fal frames → Higgsfield first/last-frame video → ElevenLabs TTS → HyperFrames hybrid stitch | **Complete — all 30 records `Scheduled` in Blotato (8 v2 finals May 15–22; 22 v3 finals June 1–30). Deployed (Modal) 2026-05-14, app `r61-video-pipeline` (functions only; HTTP endpoints parked on free-tier 8-endpoint cap).** |

## Modal Deployment (2026-05-14)

Modal workspace: `hello-58046`. Three apps deployed, all in `State: deployed`.

| App ID | App | Source | Dashboard |
|---|---|---|---|
| `ap-x3Mpc6hbqoXamFzykV6t2I` | `vizard-clipper` (R55) | `R55_clipper_agent/` | https://modal.com/apps/hello-58046/main/deployed/vizard-clipper |
| `ap-7hP62D82XJ6x8LvefI79CD` | `r57-content-engine` | `R57_content_engine/modal_app.py` | https://modal.com/apps/hello-58046/main/deployed/r57-content-engine |
| `ap-SB0c4CNE51ZfMfmR49WYkC` | `r61-video-pipeline` | `R61_video_pipeline/modal_app.py` | https://modal.com/apps/hello-58046/main/deployed/r61-video-pipeline |

**Live R57 HTTP endpoints** (POST; verified 2026-05-14, both respond `HTTP/2 422` to empty body — alive):
- `https://hello-58046--r57-content-engine-generate-images-http.modal.run` — payload `{record_ids?: [string], dry_run?: bool}` → `generate_images.remote(...)`
- `https://hello-58046--r57-content-engine-schedule-blotato-http.modal.run` — payload `{record_ids?: [string], dry_run?: bool}` → `schedule_blotato.remote(...)`

**R61 functions** (HTTP wrappers parked — Modal free-tier 8-endpoint cap, `r57` + `vizard-clipper` consume the budget). All callable via `modal run`:

| Function | Invocation |
|---|---|
| `frame_gen` | `modal run R61_video_pipeline/modal_app.py -- stage=frame record_id=rec...` |
| `video_gen` | `modal run R61_video_pipeline/modal_app.py -- stage=video record_id=rec...` |
| `voiceover_gen` | `modal run R61_video_pipeline/modal_app.py -- stage=vo record_id=rec...` |
| `hf_stitch` | `modal run R61_video_pipeline/modal_app.py -- stage=stitch record_id=rec...` |
| `blotato_schedule` | `modal run R61_video_pipeline/modal_app.py -- stage=blotato record_id=rec...` |
| `sync_r57_to_video` | `modal run R61_video_pipeline/modal_app.py -- stage=sync` |

Six `*_http` wrappers in `R61_video_pipeline/modal_app.py` are commented out; uncomment + redeploy after Modal plan upgrade or after retiring an endpoint elsewhere.

**Modal secrets** (one-time, persisted in Modal workspace — not stored locally): `r57-secrets`, `r61-secrets`, `vizard-clipper-secrets`. Full schema in `obsidian-brain/knowledge/webhook_registry.md#operator-setup-commands`.

**Windows deploy quirk:** prefix `$env:PYTHONIOENCODING="utf-8"` before `modal deploy` — modal CLI emits unicode build logs that crash default cp1252 mid-deploy.

**Not yet wired:** n8n `/webhook/r57` and `/webhook/r61` on `ops.getautomata.ai` still hit the original shims, not Modal. Tunnel/reverse-proxy work is the next deployment phase — see `obsidian-brain/knowledge/webhook_registry.md` Phase 7.

## Shared Resources

**Airtable base:** `appC3HqG42ftswOvw` — used by both R57 and R61
- R57 table: `May2025 - Provinzial_Geier&Ayhan` (`tblnpiwNYF3zJXm9Q`)
- R61 table: `Video` (`tbl1hd8yprLTZia4c`) — consumes R57's `Source Image` field as input

**Blotato:** Connected accounts = TikTok, Meta, Instagram. Used by R55, R57, R61.

**.env locations** (each pipeline has its own; never commit):
- `R55_clipper_agent\` — Modal secret `vizard-clipper-secrets` (see `.env.example`)
- `R57_content_engine\.env` — `FAL_API_KEY`, `AIRTABLE_API_KEY`, `BLOTATO_API_KEY`
- `R61_video_pipeline\.env` — `FAL_KEY`, `HIGGSFIELD_*`, `R2_*`, `AIRTABLE_*`, `BLOTATO_API_KEY`, `GOOGLE_API_KEY`

**Provider conventions (R57 + R61):** Fal.ai is the default for image and video gen. KIE has been ripped out of R57; do not reintroduce it. Models:
- `nano-banana-pro` → `fal-ai/nano-banana/edit` (refs) or `fal-ai/nano-banana` (text-only)
- `kling-3.0` → `fal-ai/kling-video/v2.1/master/image-to-video`
- `sora-2-pro` → `fal-ai/sora-2/image-to-video/pro`

## n8n Canvas — GetAutomata_W01-W05 (Phase 6 — 2026-05-13)

- **Workflow:** `SmtkmTgfCTLZPlN4` at https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Final state:** 460 nodes, ACTIVE. 12 pipelines + 16 webhook chains + R46→R51 auto-clone + cross-pipeline gates.
- **Final export:** `n8n_backups/GetAutomata_W01-W05_FINAL_2026-05-13.json`
- **Telegram credential `lux_bot`:** id `WoB3AsOoB9cIKUrI` (chat 1077552316). Bound to `n8n-nodes-base.telegram` send/edit nodes. **`telegramTrigger` cannot be PUT via public API** (needs UI registration) — TODO stickies preserve original config.
- **Webhook trigger sink:** Airtable table `PipelineRequests` = `tblLtTpXwFOpzDX4K` on `appC3HqG42ftswOvw`. All 16 webhook chains write Pending row + RespondToWebhook immediately, then continue into pipeline body.
- **Webhook URLs:** see `obsidian-brain/knowledge/webhook_registry.md`.

**Section coordinates (slot @ Y range, all X≈[-1200,+1000]; webhook sub-bands at X=-2500):**

| Slot | Pipeline | Y range |
|---|---|---|
| §A | R46 — Extract (Apify×8 + Set/Filter + 8 Airtable sinks) | 0..1140 |
| §B | R51 — Creative Cloner | 1540..2640 |
| §C | R34 — VeoRobo | 2740..3840 |
| §D | n16 — Narrative Chaining | 3940..5140 |
| §E | n16.1 — Auto Subtitles | 5140..6340 |
| §F | R39 — Split AI Images | 6340..7540 |
| §G | n19 — Ultimate Video Ads | 7540..8740 |
| §H | n21 — Ultimate UGC Creator (5 sub-workflows TODO) | 8740..9940 |
| §I | n30 — Product Videography | 9940..11140 |
| §J | n31 — Precision Camera | 11140..12340 |
| §K | n3 — Voice & Subs | 12340..13440 |
| §L1 | n29 — TikTok→Sora | 13540..14540 |
| §L2 | n29 — YT Long→LI/X | 14640..15640 |
| §L3 | n29 — YT Short→Script | 15740..16740 |

**Compatibility caps applied on this n8n instance** (verified by bisect during merge):
- `@n8n/n8n-nodes-langchain.agent` → cap typeVersion at 2 (v3 fails)
- `n8n-nodes-base.googleSheets` → cap at 4.6 (v4.7 fails)
- `n8n-nodes-base.switch` → cap at 3.2 (v3.4 fails)
- `@n8n/n8n-nodes-langchain.googleGemini` → unrecognized (TODO sticky)
- `n8n-nodes-base.telegramTrigger` → public PUT rejects (TODO sticky preserves config; bind to lux_bot in UI)

**Operator-bound credentials still required** (UI binding only, never via API): airtableTokenApi, openAiApi, openRouterApi, googlePalmApi, httpHeaderAuth (Fal/WaveSpeed/Blotato-v2), elevenLabsApi, piAPIApi, s3 (R2), httpCustomAuth (NCA Toolkit/ElevenLabs custom), boxOAuth2Api (until Box→R2 swap).

## CodeGraph

CodeGraph is initialized at the repo root (`.codegraph/`, v0.7.3, 161 files, 1,897 nodes, 3,715 edges as of 2026-05-13). **Follow the rules in `~/.claude/CLAUDE.md`** — in particular, never call `codegraph_explore` or `codegraph_context` directly in the main session; spawn an Explore agent. Lightweight tools (`codegraph_search`, `codegraph_callers`, `codegraph_callees`, `codegraph_impact`, `codegraph_node`) are safe to call directly for targeted lookups.

After significant code changes, run `codegraph sync` from `C:\CONTENT_PIPELINE\` to keep the index current.

## Rules (non-negotiable)

1. **Never create throwaway scripts.** Use the existing tools in `R57_content_engine/tools/` and `R61_video_pipeline/tools/` inline — extend them if needed, don't write one-off `.py` files in the repo root.
2. **Always confirm cost before any generation.** Before running anything that calls Fal, Higgsfield, Vizard, Gemini, or any other paid API, surface the expected USD cost and wait for explicit user approval. Check `R57_content_engine/tools/config.py` (COSTS table) for current Fal pricing — verify at fal.ai/models if quoting to the user.
3. **Blotato is schedule-only.** Scheduling future-dated posts via Blotato is the standing practice. **Immediate posting (anything that publishes "now") is never invoked from these pipelines.** Every Blotato call must include a future `scheduledTime`. See `~/.claude/projects/C--CONTENT-PIPELINE/memory/feedback_blotato_no_post.md`.

## R61 Human-Review Gates

R61 has four mandatory human gates that cannot be auto-skipped:
1. After Higgsfield clip generation
2. After raw R2 footage selection (full manual — no auto-pull)
3. Before each FFmpeg stitch
4. Full final preview before export

## Quick References

- R57 details: `R57_content_engine/R57-README.md`, `.agent/AGENT.md`
- R61 details: `R61_video_pipeline/README.md`, `PIPELINE.md`
- R55 details: `R55_clipper_agent/AGENT.md`, `R55 - README.md`
- Auto-memory index: `C:\Users\benja\.claude\projects\C--CONTENT-PIPELINE\memory\MEMORY.md`
