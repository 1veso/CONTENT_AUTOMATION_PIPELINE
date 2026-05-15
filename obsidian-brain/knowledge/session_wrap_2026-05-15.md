# Session Wrap — 2026-05-15

**Window:** ~2026-05-12 → 2026-05-15 (≈4 days)
**Operator:** Benja
**Agent:** ClaudeClaw / Primary
**Branch:** `main` (will also push to `dev`)

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
- **Final state:** 460 nodes, ACTIVE
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

| Rank | Item | Why |
|---|---|---|
| P0 | Credential fan-out — bind all 10 operator-bound credentials in n8n UI | Blocks every webhook chain from actually executing; UI work only |
| P0 | Schäden campaign kickoff | Next active client campaign after Geier & Ayhan; needs vault folder + Airtable base + pipeline trigger plan |
| P1 | Complete n8n→Modal tunnel for R57/R61 webhooks (Phase 7 in `webhook_registry.md`) | Until done, Modal endpoints are deployed but unreachable from n8n flows |
| P1 | n21 — 5 sub-workflows for Ultimate UGC Creator | Slot §H placeholder only |
| P1 | n8n pod stability (2Gi bump + Service rename) | See `getautomata_infra_notes.md` §1 |
| P2 | k3s scaling architecture decision (horizontal vs per-tenant) | See `getautomata_infra_notes.md` §2 |
| P2 | L3 semantic memory layer (ChromaDB + Pensyvee re-eval) | See `getautomata_infra_notes.md` §4 |
| P2 | `gax tenant new` CLI | Automate the manual Provinzial-style onboarding |
| P3 | Modal HTTP-wrapper revival for R61 (currently parked at 8-endpoint cap) | Either upgrade Modal plan or retire an endpoint elsewhere |
| P3 | Per-pipeline alpha/beta/gamma agent split | Defer until Phase 1 ClaudeClaw has run ≥1 week clean |

---

## 5. Next session — start here

1. **`codegraph sync`** from `C:\CONTENT_PIPELINE\` — index is from 2026-05-13, several commits since
2. **Credential fan-out** — work through the 10 operator-bound creds in `n8n_credentials.md`; bind each in the n8n UI and tick off
3. **Schäden campaign kickoff** — clone `NEW_CLIENT_TEMPLATE/`, provision Airtable base, brief alignment, drop first batch into R57 queue

Anything from §4 below P1 is fair game once those three are done.

---

## 6. References

- Infra deep-dive + scaling brief: `obsidian-brain/knowledge/getautomata_infra_notes.md`
- Webhook map: `obsidian-brain/knowledge/webhook_registry.md`
- n8n credential checklist: `obsidian-brain/knowledge/n8n_credentials.md`
- Auto-memory: `C:\Users\benja\.claude\projects\C--CONTENT-PIPELINE\memory\MEMORY.md`
- Conversation log: `shared/memory/convo_log_primary.md`
