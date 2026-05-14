# Phase 4-6 Final Report — 2026-05-13

**Target workflow:** `SmtkmTgfCTLZPlN4` at `https://ops.getautomata.ai`
**Final state:** **460 nodes, ACTIVE.** All 12 source pipelines + 16 webhook chains + cross-pipeline wiring imported.
**Final snapshot:** `n8n_backups/GetAutomata_W01-W05_FINAL_2026-05-13.json` (632 KB)
**Trajectory:** 35 → 202 (Phase 4 first batch) → 347 (5 failing pipelines) → 383 (n29×3) → 391 (R46 sinks) → 460 (Phase 5 wiring).

---

## What landed this turn

### Task 1 — Imported 5 previously failing pipelines (n16, R39, n19, n21, n30)

Each was bisected against the live canvas; `_bisect.py` inserts one node at a time and reports which one triggers the public-PUT validation error.

| Slot | Pipeline | Error found | Fix applied |
|---|---|---|---|
| §D | n16 | `googleSheets` v4.7 → "Cannot read properties of undefined (reading 'execute')" | Cap `googleSheets` at v4.6 in `TYPE_VERSION_CAPS` |
| §F | R39 | `telegramTrigger` fails even with valid creds (public API does not register the bot webhook) | Replace with TODO sticky preserving original params; bind `n8n-nodes-base.telegram` send/edit nodes to lux_bot |
| §G | n19 | Same as R39 + transient 502 outage during retry | Same telegramTrigger handling; retried after n8n upstream recovered |
| §H | n21 | 5 `executeWorkflow` nodes reference sub-workflow IDs that don't exist on this instance | Replace with TODO stickies preserving original sub-id strings |
| §I | n30 | `switch` v3.4 → same execute-undefined error | Cap `switch` at v3.2 |

Live canvas after this task: **347 nodes.**

### Task 2 — Imported n29 × 3 (Sora / Long / Short)

Created the `lux_bot` Telegram credential via MCP (id `WoB3AsOoB9cIKUrI`, bot token + chat 1077552316 supplied by operator). Bound `n8n-nodes-base.telegram` send/edit nodes to lux_bot; `telegramTrigger` instances are TODO stickies awaiting UI registration. **Live canvas: 383 nodes.**

### Task 3 — R46 Airtable sinks

Extracted the 8 Airtable destination nodes from `R46_airtable.json` and wired each to its existing `Edit Fields N` source on the live canvas:

| Source `Edit Fields…` | New sink | Table |
|---|---|---|
| Edit Fields | `[A] Append row in sheet (TikTok)` | `tblrc4ILrLINc6rVy` |
| Edit Fields1 | `[A] Append row in sheet1 (YouTube_Longs)` | `tbl59JhHWb07isxR8` |
| Edit Fields2 | `[A] Append row in sheet2 (YouTube_Shorts)` | `tbl7IJMsbRMy1NwnW` |
| Edit Fields4 | `[A] Append row in sheet3 (Instagram)` | `tblCHWVm1tqrpHeGJ` |
| Edit Fields5 | `[A] Append row in sheet4 (LinkedIn)` | `tblbIkcFGqgKVGsHr` |
| Edit Fields6 | `[A] Append row in sheet5 (Twitter)` | `tblqgMjGVrY9p5IEi` |
| Edit Fields7 | `[A] Append row in sheet6 (Reddit)` | `tblgYOJucqBTAwLMm` |
| Edit Fields3 | `[A] Append row in sheet7 (Meta_Ads)` | `tblWdSTGmlndt6UwR` |

Credentials stripped (operator binds Airtable PAT in UI). **Live canvas: 391 nodes.**

### Task 4 — Phase 5 cross-pipeline wiring

1. **`PipelineRequests` Airtable table created** via Meta API on `appC3HqG42ftswOvw` → `tblLtTpXwFOpzDX4K`. Fields: `pipeline_id` (text, primary), `params` (long text), `status` (single select Pending/Running/Done/Failed), `webhook_id` (text), `result_url` (URL), `error` (long text). (Note: Airtable Meta API rejects `createdTime` and `autoNumber` field creation → these are not in the table; use Airtable's automatic `Created time` if needed.)

2. **16 webhook chains** added at X=−2500, one per pipeline. Each chain = `Webhook(POST, responseMode=responseNode)` → `Set(pipeline_id, params, status=Pending, webhook_id=$execution.id)` → `Airtable.create on PipelineRequests` → `RespondToWebhook({webhook_id, pipeline, status})`. URLs:

| Pipeline | URL |
|---|---|
| R46 | https://ops.getautomata.ai/webhook/r46 |
| R51 | https://ops.getautomata.ai/webhook/r51 |
| R34 | https://ops.getautomata.ai/webhook/r34 |
| n16 | https://ops.getautomata.ai/webhook/n16 |
| n16.1 | https://ops.getautomata.ai/webhook/n16-1 |
| R39 | https://ops.getautomata.ai/webhook/r39 |
| n19 | https://ops.getautomata.ai/webhook/n19 |
| n21 | https://ops.getautomata.ai/webhook/n21 |
| n30 | https://ops.getautomata.ai/webhook/n30 |
| n31 | https://ops.getautomata.ai/webhook/n31 |
| n3 | https://ops.getautomata.ai/webhook/n3 |
| n29 Sora | https://ops.getautomata.ai/webhook/n29-sora |
| n29 Long | https://ops.getautomata.ai/webhook/n29-long |
| n29 Short | https://ops.getautomata.ai/webhook/n29-short |
| R57 | https://ops.getautomata.ai/webhook/r57 (writes PipelineRequests; R57 Python polls) |
| R61 | https://ops.getautomata.ai/webhook/r61 (writes PipelineRequests; R61 Python polls) |

3. **R46 → R51 auto-clone trigger:** Schedule (5 min) + Airtable.search on TikTok with `AND({days_on_air} > 7, {clone_status} = '')` + sticky pointing to R51 entry. Operator wires the Airtable output → R51 main flow.

4. **n3 voiceover routing gate** (sticky at Y=12100): documents Switch on `add_voiceover` flag after R34/R51/n19 final video output.

5. **n29 quality gate** (sticky at Y=13200): documents Gemini-scored `quality_score >= 7` threshold before Blotato schedule.

**Live canvas after Phase 5: 460 nodes** (+69 nodes, +49 connections from this batch).

### Task 5 — Phase 6 finalization

- Final workflow exported → `n8n_backups/GetAutomata_W01-W05_FINAL_2026-05-13.json` (460 nodes, 632 KB).
- Updated all 12 `obsidian-brain/pipelines/*.md` files with `## Phase 6 final state` footer (workflow id, canvas section coords, webhook URL, notes).
- Updated `obsidian-brain/knowledge/webhook_registry.md` with deployed URLs and PipelineRequests table id.
- Updated `CLAUDE.md` with Phase 6 canvas table (slot/pipeline/Y range), compatibility caps, lux_bot id, operator-bind cred list.
- `codegraph sync` deferred → DB locked by running MCP server. Operator should run from `C:\CONTENT_PIPELINE\` after closing the MCP session.

---

## Compatibility findings added this turn

| Type / version | Behaviour on this n8n instance | Workaround |
|---|---|---|
| `n8n-nodes-base.googleSheets` v4.7 | "Cannot read properties of undefined (reading 'execute')" | Cap to v4.6 |
| `n8n-nodes-base.switch` v3.4 | Same | Cap to v3.2 |
| `n8n-nodes-base.telegramTrigger` | "Bad request - please check your parameters" with valid cred id; bot webhook registration is missing on PUT path | TODO sticky (preserves params); operator adds in UI and binds to lux_bot |
| Public API GET `/credentials` | 405 Method Not Allowed | Cannot enumerate creds via API; create with `n8n_manage_credentials` MCP if needed |

---

## Operator follow-ups still required

1. Bind credentials in n8n UI for: `airtableTokenApi`, `openAiApi`, `openRouterApi`, `googlePalmApi`, `httpHeaderAuth` (Fal AI / WaveSpeed / Blotato v2), `elevenLabsApi`, `piAPIApi`, `s3` (R2), `httpCustomAuth` (NCA Toolkit / ElevenLabs custom). Standardised names: see `PHASE_0-3_HANDOFF.md` section 3.1.
2. Add `telegramTrigger` nodes manually in UI for R39, n19, n29 × 3 → bind to **lux_bot** (id `WoB3AsOoB9cIKUrI`). The TODO stickies on the canvas preserve the original params.
3. KIE → Fal swaps still pending in: R51 (Suno music → Lyria-2 verify), n16 (Veo), n19 (Veo + nano-banana-edit), n21 sub-workflows (Veo3-fast, nano-banana, Seedream, gpt-image-1), n29 Sora variant, n30 (Veo).
4. Sheets → Airtable swaps still pending in: R39, n3, n16, n19, n21.
5. Box → R2 swaps still pending in: R39, n19.
6. n21 sub-workflows: create 5 separate workflows (Combine Clips, 3× Create Image variants, Create Video) and patch new ids back into the n21 orchestrator's TODO sticky positions.
7. Run `codegraph sync` from `C:\CONTENT_PIPELINE\` after closing this MCP session.

---

## Files produced this turn

- `n8n_backups/GetAutomata_W01-W05_FINAL_2026-05-13.json` — final 460-node merged snapshot
- `n8n_backups/_import_remaining.py` — single-pipeline importer with TypeVersion caps + lux_bot binding + telegramTrigger TODO + executeWorkflow TODO + snapshot/rollback
- `n8n_backups/_bisect.py` — node-by-node import bisector (used to find googleSheets/switch caps)
- `n8n_backups/PHASE_6_FINAL_REPORT.md` — this file
- `obsidian-brain/knowledge/webhook_registry.md` — updated with live URLs + PipelineRequests table id
- 12 `obsidian-brain/pipelines/*.md` files — appended Phase 6 footer
- `CLAUDE.md` — new "n8n Canvas — GetAutomata_W01-W05 (Phase 6)" section
