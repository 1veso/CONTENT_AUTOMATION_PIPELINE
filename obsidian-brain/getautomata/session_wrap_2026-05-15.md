# Session Wrap — 2026-05-15

**Window:** ~2026-05-12 → 2026-05-15 (≈4 days)
**Operator:** Benja
**Agent:** ClaudeClaw / Primary
**Repo:** `1veso/CONTENT_AUTOMATION_PIPELINE` — `main` and `dev` in sync

---

## 1. Headline

Three content pipelines (R55, R57, R61) are deployed to Modal and complete-through-Blotato for Provinzial's Geier & Ayhan campaign. The GetAutomata n8n canvas (460 nodes, 12 pipelines, 16 webhook chains) is ACTIVE on `ops.getautomata.ai`. ClaudeClaw Phase 1 (single primary agent + Telegram channel) is online with three crons. Infrastructure scaling is the next frontier — see `getautomata_infra_notes.md`.

---

## 2. What was built

### R55 — Vizard clipper
- Long-form video → YouTube Shorts clipper
- Vizard API integration, Telegram review bot, Blotato schedule
- **Status:** Deployed to Modal as `vizard-clipper` (`ap-x3Mpc6hbqoXamFzykV6t2I`); running

### R57 — Content engine (static images)
- Fal.ai image generation (`nano-banana`, `nano-banana/edit`) — KIE removed and forbidden from reintroduction
- 30 images generated for Geier & Ayhan, all scheduled in Blotato
- **Status:** Deployed to Modal as `r57-content-engine` (`ap-7hP62D82XJ6x8LvefI79CD`); HTTP endpoints live at `hello-58046--r57-content-engine-{generate-images,schedule-blotato}-http.modal.run`

### R61 — Video pipeline
- Fal frames → Higgsfield first/last-frame video → ElevenLabs TTS → HyperFrames hybrid stitch
- Four mandatory human gates (clip, R2 footage selection, pre-stitch, final preview)
- All 30 records `Scheduled` in Blotato: 8 v2 finals (May 15–22), 22 v3 finals (June 1–30)
- **Status:** Deployed to Modal as `r61-video-pipeline` (`ap-SB0c4CNE51ZfMfmR49WYkC`); functions deployed, HTTP wrappers parked behind the free-tier 8-endpoint cap (commented out in `modal_app.py`)

### R46 — Extract pipeline (n8n)
- Apify ×8 + Set/Filter + 8 Airtable sinks
- Lives in n8n canvas slot §A (Y 0..1140)

### R51 — Creative Cloner (n8n)
- Auto-clones approved R46 outputs to working tables
- Slot §B (Y 1540..2640)

### R34 — VeoRobo (n8n)
- Slot §C (Y 2740..3840)

### n-series (n8n)
- n16 — Narrative Chaining (§D)
- n16.1 — Auto Subtitles (§E)
- R39 — Split AI Images (§F)
- n19 — Ultimate Video Ads (§G)
- n21 — Ultimate UGC Creator (§H; 5 sub-workflows still TODO)
- n30 — Product Videography (§I)
- n31 — Precision Camera (§J)
- n3 — Voice & Subs (§K)
- n29 — three variants: TikTok→Sora (§L1), YT Long→LI/X (§L2), YT Short→Script (§L3)

### Modal deployment
- Workspace `hello-58046`, three apps deployed (all `State: deployed`)
- Three secrets created in Modal: `r57-secrets`, `r61-secrets`, `vizard-clipper-secrets`
- Windows-deploy quirk documented (`$env:PYTHONIOENCODING="utf-8"` prefix required)

### ClaudeClaw agent (Phase 1)
- Single primary agent at repo root
- Telegram channel: one bot, allowlisted to chat `1077552316`
- Three crons registered: `morning-summary` (08:00), `keepalive` (every 6h), `r61-gate-watcher` (every 15m)
- Gate-notification pattern wired in `frame_gen.py`, `video_gen.py`, `hf_stitch.py` → `R61_video_pipeline/tools/_gates.append_gate(...)` → `shared/gates/pending.json`
- Progress notifications: long-running pipeline steps emit interim Telegram updates via the agent (so the operator sees "frame 4/8 generated" not just final summaries)
- Per-pipeline alpha/beta/gamma split deferred until Phase 1 has run cleanly for ≥1 week

### n8n→Modal tunnel
- Wired for R57 and R61 webhooks (commit `e1f49ee`)
- Tunnel/reverse-proxy from `ops.getautomata.ai/webhook/r57` and `/webhook/r61` still hits the original shims, not Modal — completion is the next deployment phase (see `webhook_registry.md` Phase 7)

### GetAutomata vault re-org
- Established GetAutomata is the **parent dashboard**, not a client (commits `0fdc83f`, `443a031`)
- GetAutomata brand brief moved into `obsidian-brain/getautomata/`
- Tenants live under `obsidian-brain/clients/`

---

## 3. n8n canvas state — `GetAutomata_W01-W05`

- **Workflow ID:** `SmtkmTgfCTLZPlN4`
- **Final state:** 472 nodes, ACTIVE (was 460 at last full export; +12 from this session's webhook + telegram trigger wiring)
- **Final export:** `n8n_backups/GetAutomata_W01-W05_FINAL_2026-05-13.json`
- **Telegram credential `lux_bot`:** id `WoB3AsOoB9cIKUrI`, bound to chat 1077552316 on `n8n-nodes-base.telegram` send/edit nodes
- **`telegramTrigger` API limitation:** cannot be PUT via public API — TODO stickies preserve config until UI registration
- **Webhook trigger sink:** Airtable `PipelineRequests` (`tblLtTpXwFOpzDX4K` on `appC3HqG42ftswOvw`) — all 16 webhook chains write a Pending row + RespondToWebhook immediately, then continue into pipeline body

### Compatibility caps applied
- `@n8n/n8n-nodes-langchain.agent` → typeVersion ≤ 2
- `n8n-nodes-base.googleSheets` → typeVersion ≤ 4.6
- `n8n-nodes-base.switch` → typeVersion ≤ 3.2
- `@n8n/n8n-nodes-langchain.googleGemini` → unrecognized (TODO sticky)
- `n8n-nodes-base.telegramTrigger` → public PUT rejects

### Operator-bound credentials still required (UI only, never via API)
- airtableTokenApi
- openAiApi
- openRouterApi
- googlePalmApi
- httpHeaderAuth (Fal / WaveSpeed / Blotato-v2)
- elevenLabsApi
- piAPIApi
- s3 (R2)
- httpCustomAuth (NCA Toolkit / ElevenLabs custom)
- boxOAuth2Api (until Box→R2 swap completes)

---

## 4. Open items (priority ranked)

| # | Item | Notes |
|---|---|---|
| 1 | 5 telegramTrigger nodes — manual UI registration | R39, n19, n29×3. n8n public API cannot PUT `telegramTrigger`; bind to `lux_bot` cred in UI then save |
| 2 | n16 / n21 Airtable schema split | On hold pending operator answer to Q1/Q2 (one table vs split; which fields move) |
| 3 | Schäden campaign kickoff — **$49.85, 120 posts** | Next active Provinzial campaign; provision vault folder + Airtable base + first R57 batch |
| 4 | KIE → Fal remaining swaps | n19, n21, n16, R51 still reference KIE nodes; rip out per the no-KIE rule and replace with `nano-banana`/`kling`/`sora` Fal endpoints |
| 5 | n21 sub-workflows creation | 5 sub-workflows under slot §H (Ultimate UGC Creator) — currently placeholder |
| 6 | Modal free-tier upgrade — **7/8 endpoints used** | One more HTTP wrapper = capped. Either upgrade plan or retire a wrapper before adding any new endpoint |
| 7 | `codegraph sync` | Run from `C:\CONTENT_PIPELINE\` after this session closes — several commits since last index |
| 8 | Google Sheets OAuth2 — **defer; swap nodes to Airtable instead** | OAuth2 binding is brittle in n8n; cheaper to rewrite the two Sheets nodes against the existing Airtable base |
| 9 | GetAutomata infra scaling | Separate project — see `getautomata_infra_notes.md` (HPA + per-tenant Helm + multi-node) |
| 10 | L3 semantic memory (ChromaDB) | Separate project — see `getautomata_infra_notes.md` §4 (Pensyvee re-eval + per-tenant collections) |

---

## 5. Next session — start here

1. **`codegraph sync`** from `C:\CONTENT_PIPELINE\` — index is from 2026-05-13, several commits since
2. **n16 / n21 Airtable schema split** — resolve once operator answers Q1/Q2, then apply the split to both pipelines
3. **Schäden campaign kickoff** — $49.85, 120 posts; clone `NEW_CLIENT_TEMPLATE/`, provision Airtable base, first batch into R57

Items 4–10 above are fair game once those three are done.

---

## 6. References

- Infra deep-dive + scaling brief: `obsidian-brain/knowledge/getautomata_infra_notes.md`
- Webhook map: `obsidian-brain/knowledge/webhook_registry.md`
- n8n credential checklist: `obsidian-brain/knowledge/n8n_credentials.md`
- Auto-memory: `C:\Users\benja\.claude\projects\C--CONTENT-PIPELINE\memory\MEMORY.md`
- Conversation log: `shared/memory/convo_log_primary.md`
