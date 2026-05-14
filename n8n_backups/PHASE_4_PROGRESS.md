# Phase 4 Progress Report — 2026-05-13

**Target workflow:** `SmtkmTgfCTLZPlN4` at `https://ops.getautomata.ai`
**Final state:** **202 nodes, ACTIVE, idempotent PUT verified**
**Backup:** `n8n_backups/GetAutomata_W01-W05_backup_2026-05-13.json` (35-node clean state)
**Final snapshot:** `n8n_backups/GetAutomata_W01-W05_MERGED_2026-05-13.json` (state after Phase 4)

---

## ✅ Pipelines successfully imported (6 of 12 sections)

| Slot | Pipeline | Y offset | Nodes added | Notes |
|---|---|---|---|---|
| §A | R46 Ultimate Extract (existing) | 0–1140 | — | Already on canvas; not duplicated. 8 Apify scrapers + Set + Filter chains. Apify cred type is `apifyApi` (not `apifyOAuth2Api` like the R46 JSON file). The Airtable destination nodes from the R46 JSON were NOT added — operator must wire those manually (or import only the airtable sinks). |
| §B | R51 Creative Cloner | 1540 | +38 | KIE Suno music endpoint still inline — needs Fal Lyria-2 swap. Callback URL `api.example.com/callback` is placeholder. |
| §C | R34 VeoRobo | 2740 | +27 | Clean — KIE-stripped per source, ready once creds bind. `langchain.agent` typeV auto-downgraded 1.9→1.9 (no change needed). |
| §E | n16.1 Auto Subtitles | 5140 | +19 | Community node `n8n-nodes-elevenlabs-enhanced` IS installed (verified). Webhook trigger; NCA toolkit reachability unverified. |
| §J | n31 Precision Camera | 11140 | +40 | 1 `googleGemini` node replaced with TODO sticky (node type unrecognized on this n8n). All other nodes intact. |
| §K | n3 Voice & Subs | 12340 | +43 | Sheets→Airtable swap still pending. Two Fal cred entries (header + basic) for consolidation. |

---

## ❌ Pipelines that failed to import (6 of 12)

### "Cannot read properties of undefined (reading 'execute')" — unrecognized node type somewhere

| Slot | Pipeline | Likely cause |
|---|---|---|
| §D | n16 Narrative Chaining | Unknown — has standard core + langchain nodes; needs node-by-node bisect |
| §F | R39 Split AI Images | `telegramTrigger` likely needs valid `telegramApi` cred (same as n29 issue) |
| §G | n19 Ultimate Video Ads | Same — has `telegramTrigger` |
| §H | n21 Ultimate UGC Creator | `executeWorkflow` nodes reference sub-workflow IDs that don't exist on this instance |
| §I | n30 Product Videography | Has `googleGemini` (would be replaced) + webhook trigger — needs deeper investigation |

### "Node does not have any credentials set" / "Credential ID does not exist"

| Slot | Pipeline | Cause |
|---|---|---|
| §L1 | n29 TikTok→Sora | `telegramTrigger` requires `telegramApi` cred; stripping creds → "no creds set"; keeping creds with placeholder ID → "ID does not exist" |
| §L2 | n29 YT Long→LI/X | Same |
| §L3 | n29 YT Short→Script | Same |

---

## 🔑 Compatibility findings on this n8n instance

**Verified WORKING (via individual node insertion tests):**
- `@apify/n8n-nodes-apify.apify` ✓
- `@blotato/n8n-nodes-blotato.blotato` ✓
- `n8n-nodes-elevenlabs-enhanced.elevenLabs` ✓
- `n8n-nodes-piapi.fileUpload` ✓
- `n8n-nodes-base.box` ✓
- `n8n-nodes-base.googleSheets` typeV=4 ✓
- `n8n-nodes-base.telegram` typeV=1.2 ✓
- `n8n-nodes-base.s3` ✓
- `@n8n/n8n-nodes-langchain.openAi` typeV=1.7 ✓
- `@n8n/n8n-nodes-langchain.lmChatOpenAi` ✓
- `@n8n/n8n-nodes-langchain.lmChatOpenRouter` ✓
- `@n8n/n8n-nodes-langchain.outputParserStructured` typeV=1.3 ✓
- `@n8n/n8n-nodes-langchain.toolThink` typeV=1.1 ✓
- `@n8n/n8n-nodes-langchain.agent` typeV=2 ✓ (typeV=3 FAILS)

**Confirmed UNRECOGNIZED:**
- `@n8n/n8n-nodes-langchain.googleGemini` ✘ (used by n31, n30, R51, n29)

**TypeVersion caps applied:**
- `@n8n/n8n-nodes-langchain.agent`: capped at 2 (auto-downgrades 3→2 during merge)

---

## 🧪 The state-pollution gotcha

n8n's public API PUT can return **HTTP 400** while still **storing the state**. Specifically:
- When a workflow PUT introduces a node type/version that fails compilation, n8n persists the data and returns 400 with `"Cannot read properties of undefined (reading 'execute')"`.
- Subsequent GETs return the broken state.
- Subsequent PUTs (including idempotent re-PUTs of the broken state) also return 400 — even though nothing new was added.
- The only recovery is to roll back to a known-good snapshot.

**This required adding rollback-on-failure logic to the merge script.** The `_batch_merge.py` and follow-up scripts in `n8n_backups/` now snapshot before each pipeline and roll back if either the PUT returns non-200 OR the idempotent re-PUT fails.

---

## 📐 Final canvas layout

```
Y=0    .. 1140  §A  R46 Ultimate Extract (existing — Apify scrapers x8)
Y=1440 .. 2640  §B  R51 Creative Cloner
Y=2640 .. 3840  §C  R34 VeoRobo
                §D  n16 Narrative Chaining          [NOT IMPORTED]
Y=5040 .. 6240  §E  n16.1 Auto Subtitles
                §F  R39 Split AI Images             [NOT IMPORTED]
                §G  n19 Ultimate Video Ads          [NOT IMPORTED]
                §H  n21 Ultimate UGC Creator        [NOT IMPORTED]
                §I  n30 Product Videography         [NOT IMPORTED]
Y=11040.. 12240 §J  n31 Precision Camera Movements
Y=12240.. 13440 §K  n3  Voice & Subs
                §L1 n29 TikTok→Sora                 [NOT IMPORTED]
                §L2 n29 YT Long→LI/X                [NOT IMPORTED]
                §L3 n29 YT Short→Script             [NOT IMPORTED]
```

Bounding box of merged canvas: roughly X=[-1200, +700], Y=[0, ~13000].

---

## 🛠️ What the operator needs to do BEFORE the remaining 6 imports

1. **Create stub credentials in n8n UI** so that pipelines with trigger nodes that require auth can be imported:
   - `Telegram (Robo)` (telegramApi) — temp token can be a fresh test bot; required for n29×3, n19, R39
   - `Box (R39 placeholder)` (boxOAuth2Api) — for R39, n19 if Box→R2 swap deferred
2. **Bind the imported credentials** for the 6 sections already on canvas:
   - apifyApi (already present)
   - airtableTokenApi (Airtable PAT with `data.records:read+write` on `appC3HqG42ftswOvw`)
   - openAiApi
   - openRouterApi
   - googlePalmApi (for Gemini calls)
   - httpHeaderAuth: Fal AI, WaveSpeed, Blotato v2
   - elevenLabsApi (n16.1)
   - piAPIApi (n16.1)
   - s3 — Cloudflare R2 bucket `trendiva-raw-assets`
   - httpCustomAuth NCA (n16.1)
3. **Reapply settings** dropped by the n8n public API:
   - `callerPolicy: workflowsFromSameOwner`
   - `errorWorkflow: SmtkmTgfCTLZPlN4` (was self-referencing — likely placeholder)
4. **Investigate the §D/§F/§G/§H/§I failures** node-by-node when time permits. Likely culprits per pipeline:
   - n16: `n8n-nodes-base.merge` (not pre-tested), or an HTTP node parameter shape
   - R39/n19/n29: `telegramTrigger` needs a real cred ID
   - n21: `executeWorkflow` references missing sub-workflow IDs

---

## 📋 What still has to happen (Phase 4 follow-up + Phase 5/6)

1. **6 remaining pipeline imports** — n16, R39, n19, n21, n30, n29×3
2. **n21 sub-workflows** — Combine Clips, 3× Create Image variants, Create Video — each as a **separate** n8n workflow (via `n8n_create_workflow`), then patch their new IDs back into the n21 orchestrator's `executeWorkflow` nodes.
3. **R46 Airtable destinations** — the live R46 has scrapers + Set/Filter but no Airtable sinks. Add 8 Airtable destination nodes (one per platform) to complete the chain.
4. **KIE → Fal swaps** for R51, n16, n19, n21 subs, n29 Sora, n30 (see Phase 3 swap matrix in PHASE_0-3_HANDOFF.md).
5. **Sheets → Airtable swaps** for n3, n16, n19, n21, R39.
6. **Box → R2 swaps** for R39, n19.
7. **Phase 5 wiring** — R46→R51 trigger, R51→R61 handoff sticky, n3 enhancement gate, n29 quality gate.
8. **Phase 5.5 webhook triggers** — 14 trigger sub-workflows (one per pipeline + R57 + R61).
9. **Phase 6** — re-export, update obsidian pipeline markdowns with workflow id + section coords, update CLAUDE.md, codegraph sync.

---

## 🚀 Quick wins available in the next iteration

In rough order of effort:
1. **Re-import n29×3** by creating a stub `Telegram` cred first → 30 minutes total.
2. **Re-import n30** by bisecting the unrecognized node → 30 minutes.
3. **Bisect n16, R39, n19** to find each's blocker → 1–2 hours.
4. **n21 sub-workflow plumbing** → 1–2 hours (create 5 separate workflows + rewire executeWorkflow refs).
5. **Webhook triggers (Phase 5.5)** → 2–4 hours once `PipelineRequests` Airtable table exists.

---

## 📂 Files produced this turn

- `C:\CONTENT_PIPELINE\n8n_backups\GetAutomata_W01-W05_backup_2026-05-13.json` — pre-merge 35-node backup
- `C:\CONTENT_PIPELINE\n8n_backups\GetAutomata_W01-W05_MERGED_2026-05-13.json` — final 202-node merged snapshot
- `C:\CONTENT_PIPELINE\n8n_backups\PHASE_0-3_HANDOFF.md` — Phase 0–3 prep
- `C:\CONTENT_PIPELINE\n8n_backups\PHASE_4_PROGRESS.md` — this file
- `C:\CONTENT_PIPELINE\n8n_backups\_merge_pipeline.py` — single-pipeline merger (kept)
- `C:\CONTENT_PIPELINE\n8n_backups\_batch_merge.py` — batch merger with rollback (kept)
- `C:\CONTENT_PIPELINE\obsidian-brain\knowledge\webhook_registry.md` — webhook URL scaffold
