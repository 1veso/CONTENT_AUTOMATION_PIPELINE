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
| **R57** | Fal.ai static image gen → Airtable → Blotato schedule. 30 images generated. | **Complete — all 30 images scheduled in Blotato** |
| **R61** | Fal frames → Higgsfield first/last-frame video → ElevenLabs TTS → HyperFrames hybrid stitch | **Complete — all 30 records `Scheduled` in Blotato (8 v2 finals May 15–22; 22 v3 finals June 1–30)** |

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
