# Primary Agent — Conversation Log

Rolling handoff log for the primary agent. New sessions prepend above older ones. Keep last 3 sessions.

---

## Session 3 — 2026-05-15 (credential fan-out round 2 + Sheets→Airtable swap)

### Active Context
- Operator instructed credential fan-out round 2 (Blotato v2, Blotato account, ElevenLabs, S3 R2) and Sheets→Airtable swap across `SmtkmTgfCTLZPlN4`. Pod restarted with 1Gi mid-session — paused, then resumed under ≤20-node batch cap + 10s pacing.

### Completed This Session
- **Round 2 cred fan-out (1 partial diff, 6 ops):**
  - 4 §C HTTP nodes (`[C] YOUTUBE/INSTAGRAM/TIKTOK/Load Video`) rebound from Fal.ai httpHeaderAuth (`XCCrAcucNjypOTqE`, wrong) → Blotato v2 `pKZs4xekk1thYf2N`
  - `[E] ElevenLabs` ← elevenLabsApi `3LrGYbduS5r1Hdqb`
  - `[E] S3` ← s3 `LQgDrXwa1oYXUdEY`
  - Blotato account `blotatoApi z8JcQJjCeMMw6XU5` already on 6 native Blotato nodes — no-op
- **Created 5 Airtable tables in base `appC3HqG42ftswOvw`** via inline Python subprocess (R57's dotenv loader):
  - n16_Data → `tblROM3P4XlOYhIcn`
  - R39_Data → `tblloJFLska1pClZd`
  - n19_Data → `tbl7MdXu4l1J1NifF`
  - n21_Data → `tblAyWJsWVz17CtOx`
  - n3_Data  → `tblXHrLHWOM86fh1a`
- **Swapped 23 Google Sheets nodes → Airtable** (2 partial diffs, batch 1 = 12 ops, batch 2 = 11 ops; 10s gap between).
  - Pipeline assignment: §D→n16_Data, §F→R39_Data, §G→n19_Data, §H→n21_Data, §K→n3_Data
  - Credential `airtableTokenApi H9KNuMkfQ5Tl0Muu` ("Airtable PAT")
- **Box→R2 swap** (1 partial diff, 3 ops): replaced `[F] Upload a file`, `[G] Upload Image`, `[G] Upload Video` with HTTP Request PUT nodes using s3 credential `LQgDrXwa1oYXUdEY` against bucket `trendiva-raw-assets`. URL pattern `={{ $env.R2_ENDPOINT }}/trendiva-raw-assets/<filename_expression>` — operator must set `R2_ENDPOINT` env on the n8n pod (`https://<accountId>.r2.cloudflarestorage.com`). typeVersion 4.2, `nodeCredentialType: "s3"` for sigv4.
- **Added 5 operator-readable instruction stickies** (1 partial diff, 5 addNode ops) next to telegramTrigger TODO stickies in §F, §G, §L1, §L2, §L3. Each names the lux_bot credential id, the exact target node to connect, and tells the operator to delete the orange TODO sticky when done. Color 5 (green) to distinguish from the orange TODOs.
- **Exported workflow** to `n8n_backups/GetAutomata_W01-W05_CREDENTIALS_2026-05-15.json` (586KB, 465 nodes — was 460 + 5 new stickies, gitignored)

### Key Decisions / Findings
- **First swap batch failed** with `Cannot read properties of undefined (reading 'execute')` — root cause: I used typeVersion 2.2 / mode "id" / explicit `resource`+`authentication`. Running instance's airtable nodes use typeVersion **2.1**, base/table as `{__rl: true, mode: "list", cachedResultName}`, no `resource` key, no `authentication` key. Rollback was clean. Rebuilt against the production dialect by reading an existing live airtable node — succeeded.
- **Operator's section→pipeline label map was scrambled** vs CLAUDE.md canon (e.g. §D R39 vs canonical §D n16). Resolved by using pipeline names from CLAUDE.md, not section letters.
- **38-node figure mismatch**: operator anticipated 38 nodes for fan-out; actual discovery found only 10 candidates (6 to bind). Defaulted to option 2 (bind 6 + rebind 4 mis-bound §C nodes) after 5min Telegram timeout.

### Lossy Translations (operator follow-up needed)
- `[D] Clear scenes`: Sheets `clear` op has no Airtable equivalent. Node now `search` — operator needs a delete-loop if clearing scenes between runs is required.
- `[H] Store Videos / Final Video / Store Image`: matchingColumns changed from `row_number` → `id` (Airtable native record id). Any upstream Code/Set node referencing `$json.row_number` from these reads needs to switch to `$json.id`.
- `[K] Log the Idea` previously wrote `id: =ROW()-1` (a Sheets formula). The `id` field was dropped on swap — Airtable auto-generates record IDs.
- `[D] Get scenes` no longer projects to column C only; returns all fields.
- `[H] Get Prompts / Get Images / Get Videos`: Sheets multi-filter translated to `filterByFormula AND(...)` strings. Verify field-name matches in production.

### Pending / Next Steps
- Operator review of swapped nodes in n8n UI (cachedResultName may need to be re-populated by clicking the table picker once).
- Operator inserts a delete-loop downstream of `[D] Clear scenes` if needed.
- Operator audits upstream `row_number`→`id` references in §H Code/Set nodes.
- Operator sets `R2_ENDPOINT` env var on the n8n pod (`https://<accountId>.r2.cloudflarestorage.com`) so the 3 ex-Box nodes can resolve their URL.
- Operator follows the 5 HOW-TO stickies to register telegramTrigger nodes in the UI (API can't do this), then deletes both the HOW-TO sticky and the orange TODO sticky for each section.
- `codegraph sync` (deferred — no Python changes this session).

### Gate replies
- None this session.

---

## Session 2 — 2026-05-14 (n8n canvas re-spacing)

### Active Context
- Continued from prior context-window run. Full Step 1 (re-space) applied across two sessions.

### Completed This Session
- Applied `cleanStaleConnections` + 4x `addConnection` (fix ops) in a prior session to unblock saves — 30 ghost connection refs removed, 4 disconnected nodes rewired.
- Moved all 460 nodes across 17 sections (§A through §T2 + [X] cross-section nodes) to 2500px minimum vertical gap via `mcp__n8n-mcp__n8n_update_partial_workflow` partial diffs.
  - §A: anchor (no shift)
  - §B+[X] R46→R51: +2240 (applied prior session)
  - §C: +4592 | §D: +6852 | §E: +9764 | §J: +11504 | §F: +18804
  - §K+[X] n3 gate: +21436 | §G: +28736 | §H: +31120 | §I: +33696
  - §L1+[X] n29 gate: +33456 | §L2: +35412 | §L3: +37416
  - §T1: +39016 | §T2: +40416
- Exported final workflow to `n8n_backups/GetAutomata_W01-W05_SPACED_2026-05-14.json` (631 KB). Not git-tracked per .gitignore rule (intentional — large JSON blobs excluded).

### Key Decisions / Findings
- Node naming inconsistencies discovered live: `[D] §D HEADER` → actual name `[D] HEADER`; `[D] Wait ` has trailing space; `[D] If ` has trailing space. Corrected on first failed validate.
- §E node `Map Voice to Voice ID` has full long name (not `Map Voice`).
- §H TODO nodes carry full suffix: `(TODO sub-workflow)` not `(TODO)`.
- One transient NO_RESPONSE on §G batch 1 validate — retry immediate, succeeded.
- n8n_backups/*.json is gitignored by design; export is on disk only.

### Pending / Next Steps
- Task 7: Modal deploy R57 + R61 (gated — awaiting operator go-ahead)
- Task 8: Credential fan-out (gated — operator needs to seed 11 nodes first)

---

## Session 1 — 2026-05-14 (Gate flow end-to-end test)

### Active Context
- Operator launched primary, asked for Status, then asked to test the gate flow.
- 3 crons re-registered (session-only, 7d expiry): morning-summary `6b993f49`, keepalive `6dbafa45`, r61-gate-watcher `b474a490`.

### Completed This Session
- Wrote test gate entry via `_gates.append_gate()`: record `recTEST123456789`, gate 1.
- Sent notification message manually (Telegram MCP reply tool has no inline-keyboard parameter — operator uses verb+record_id reply protocol instead).
- Verified gate-watcher silent path (entries with `notified=true` are skipped).
- Verified gate-reply handler end-to-end on approve: local-state update OK → Airtable subprocess shelled out → 404 for test record → graceful-degradation message sent per protocol.

### Key Decisions / Findings
- Telegram inline keyboards are NOT supported by current `claude-plugins-official/telegram` MCP. The watcher prompt in `cron-registry.json` references inline keyboards but the tool can only send text. Fallback: send action verbs in the message body and parse `<verb> <record_id>` from operator replies. CLAUDE.md gate-reply protocol already accommodates this — no fix needed.
- Test gate left in pending.json with `status=approved`. Safe to leave or clear on operator request.

### Pending / Next Steps
- Clear test gate entry (when operator says so) — currently `recTEST123456789`, status=approved.
- If/when inline-keyboard support lands in the Telegram MCP, revisit the watcher prompt to use callback_data path.

### Gate replies
- 2026-05-14T20:39 — record `recTEST123456789`, verb `approve` → local: approved · Airtable: failed (404 NOT_FOUND, expected for test record).

---

## Session 0b — 2026-05-13 (Phase 1.5: gates wired)

### Active Context
- ClaudeClaw Phase 1 setup completed earlier today. Gate-notification pattern now live.
- Bun v1.3.14 installed at `C:\Users\benja\.bun\bin\bun.exe` (restart shell before launch).

### Completed This Session
- Created `R61_video_pipeline/tools/_gates.py` — atomic gate-queue writer with explicit schema docstring.
- Wired `frame_gen.py` → writes Gate 0 entry at end of batch (if any record succeeded).
- Wired `video_gen.py` → writes Gate 1 entry at end of batch (table-aware: works for both Video and IO).
- Wired `hf_stitch.py` → writes Gate 4 entry per record after R2 publish (skipped if `--skip-publish`).
- Captured `publish_to_r2_and_airtable` return value (URL) in stitch so gate carries the asset link.
- Updated `cron-registry.json` r61-gate-watcher prompt to match the actual JSON field names (gate_number, gate_name, ad_name, video_url, next_step).
- Updated `CLAUDE.md` with full ClaudeClaw Agent Architecture section (launch cmd, cron table, gate pattern).
- Rewrote `obsidian-brain/agents/per_pipeline_agents.md` with Phase 1 state, wired write points, gate schema, and CLAUDE.md-gate mapping.

### Pending / Next Steps
- **CodeGraph sync failed** with "database is locked" — re-run `codegraph sync` from repo root after closing this Claude session.
- **First launch**: from `C:\CONTENT_PIPELINE\`, run `claude --dangerously-skip-permissions --channels plugin:telegram@claude-plugins-official`. Verify Telegram round-trip.
- **Telegram plugin install** still needed inside the new session: `/plugin marketplace add anthropics/claude-plugins-official`, `/plugin install telegram@claude-plugins-official`, `/reload-plugins`.
- Gate 2 (R2 footage selection) and Gate 3 (pre-stitch) remain manual — no script to hook. Operator triggers `hf_stitch.py` only when ready.
- Test the gate path end-to-end: run `frame_gen.py --dry-run` won't trigger (dry-run skips processing); needs a real (paid) run to write a Gate 0 entry. First real opportunity = next R57/R61 cycle.

### Key Decisions
- Gate writes are best-effort: wrapped in try/except so a JSON write failure never breaks the pipeline.
- Frame and video gates are batch-level (one entry per run); stitch gate is per-record (one entry per stitched video). Matches the natural human-review cadence: review-frames-as-set vs review-each-final.
- `_gates.py` lives in `R61_video_pipeline/tools/` (alongside the scripts that use it), not at repo root, so it inherits the package import path the existing scripts already use.

---

## Session 0 — 2026-05-13 (ClaudeClaw Phase 1 setup)

### Active Context
- Initial ClaudeClaw setup completed at C:\CONTENT_PIPELINE\
- Single primary agent on Telegram (bot 8937217698, chat 1077552316)
- 3 crons registered: morning-summary (08:00 Berlin), keepalive (every 6h), r61-gate-watcher (every 15m)

### Completed This Session
- Created SOUL.md with 6 non-negotiable pipeline rules
- Created USER.md with operator profile
- Wrote .claude/settings.local.json with deny list (env files, references/outputs/, n8n_backups/, obsidian-brain/clients/, destructive bash/PS commands)
- Wired Telegram bot via .claude/telegram/{.env, access.json}
- Stubbed shared/gates/pending.json for R61 gate notifications

### Pending / Next Steps
- Bun install (user runs: `irm bun.sh/install.ps1 | iex` in PowerShell)
- First launch and Telegram round-trip test
- R61 pipeline to write gate triggers to shared/gates/pending.json (separate task — not done yet)

### Key Decisions
- Phase 1 = single agent only. No alpha/beta/gamma multi-agent split until Phase 1 sticks.
- Used existing CLAUDE.md, appended Session Startup + Identity sections rather than replacing.
- Bot token + state dir injected via settings.local.json env block (NOT shell env — README warns shell env doesn't propagate to MCP subprocess).
