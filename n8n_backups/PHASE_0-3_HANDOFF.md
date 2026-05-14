# GetAutomata_W01-W05 Merge — Phase 0–3 Handoff

**Target workflow:** `SmtkmTgfCTLZPlN4` at `https://ops.getautomata.ai`
**Date:** 2026-05-13
**Status:** Phases 0, 2, 3 complete (offline). Phases 1, 4, 5, 6 BLOCKED on operator action.

---

## 🛑 BLOCKER — Cloudflare Access on ops.getautomata.ai

Every path on the host (`/`, `/api/v1`, `/api/v1/workflows`, `/healthz`) returns 302 to `trendivalux.cloudflareaccess.com/cdn-cgi/access/login/`. The n8n API key is never reached because Cloudflare Access intercepts the request first. The n8n-mcp client has no slot for `CF-Access-Client-Id` / `CF-Access-Client-Secret` headers.

**Verified by curl:**
- `GET /` → 302 → CF Access login
- `GET /api/v1` → 302 → CF Access login
- `GET /api/v1/workflows` with `X-N8N-API-KEY` header → 302 (key never reaches n8n)

**Self-correction attempts:** Patched `N8N_API_URL` in `C:\Users\benja\.claude.json` from `https://ops.getautomata.ai` → `https://ops.getautomata.ai/api/v1`. The running MCP process still has the old value cached; even after restart, CF Access blocks the request regardless of path.

**Operator decision needed — pick ONE:**
1. **CF Access bypass policy** for `/api/v1/*` (fastest — service tokens or no-auth bypass on that path). Recommended.
2. **CF Access Service Token** + fork/patch n8n-mcp to inject `CF-Access-Client-Id` and `CF-Access-Client-Secret` headers.
3. **Alternate non-CF-fronted endpoint** (Cloudflare Tunnel internal hostname, VPN URL, or direct n8n container IP).

Nothing in Phase 1+ moves until this is unblocked.

---

## ✅ PHASE 0 — Environment verification (DONE)

| Step | Status | Notes |
|---|---|---|
| 0.1 MCP connectivity | ❌ Blocked | CF Access. See above. |
| 0.2 Read obsidian-brain | ✅ Done | Digest below. |
| 0.3 JSON catalog | ✅ Done | 14 JSONs across 12 pipeline folders. |
| 0.4 Backup directory | ✅ Done | `C:\CONTENT_PIPELINE\n8n_backups\` exists. |

### 0.3 JSON catalog

| # | Folder | JSON filename | Bytes | Pipeline name | Role |
|---|---|---|---|---|---|
| 1 | R46_ultimate_extract | `R46_airtable.json` | 96199 | R46 Ultimate Extract (Airtable variant) | Main |
| 1b | R46_ultimate_extract | `Ultimate Extract by RoboNuggets (R46) (1).json` | — | R46 original RoboNuggets template | Reference only |
| 2 | R51_creative_cloner | `R51_airtable.json` | 74152 | R51 Creative Cloner | Main (R51_complete.json not present; airtable variant is canonical) |
| 2b | R51_creative_cloner | `R51 _ The Creative Cloner AI Agent (by RoboNuggets).json` | — | R51 original RoboNuggets template | Reference only |
| 3 | R34_veorobo | `R34_airtable.json` | 28545 | R34 VeoRobo | Main |
| 3b | R34_veorobo | `R34___VeoRobo_Template__3_scenes__by_RoboNuggets.json` | — | R34 original RoboNuggets template | Reference only |
| 4 | R39_split_ai_system | `(template) 🥚 Split AI System - by RoboNuggets (R39).json` | 27790 | R39 Nano Banana Split System | Main (template; not yet ported) |
| 5 | n3_voice_and_subs | `n3 - Monetizable Tiktoks AI Machine with voice and subs.json` | 52860 | n3 Voice & Subs | Main |
| 6 | n16_narrative_chaining | `🍳 Veo3 - Narrative Chaining (n16).json` | 37746 | n16 Narrative Chaining | Main (second (1) copy is duplicate) |
| 7 | n16.1_auto_subtitled_videos | `ElevenLabs_to_NCA_Toolkit.json` | 21616 | n16.1 Auto Subtitles | Main |
| 8 | n19_ultimate_video_ads | `🍌 Split AI System extended (by RoboNuggets) _ n19.json` | 57889 | n19 Ultimate Video Ads | Main |
| 9a | n21_infinite_ugcs | `n21 - Ultimate UGC Creator (by RoboNuggets).json` | 54594 | n21 UGC Creator | Orchestrator |
| 9b | n21_infinite_ugcs | `n21 - Bulk Runner for Ultimate UGC Creator.json` | — | n21 Bulk Runner | Sub-workflow |
| 9c | n21_infinite_ugcs | `🍳 Combine Clips (FFMPEG via Fal AI).json` | — | n21 Combine Clips | Sub (Fal — OK) |
| 9d | n21_infinite_ugcs | `🍳 Create Image (GPT-image-1 via Kie AI).json` | — | n21 Create Image GPT-image | Sub (KIE — needs swap) |
| 9e | n21_infinite_ugcs | `🍳 Create Image (Nanobanana via Kie AI).json` | — | n21 Create Image Nano-banana | Sub (KIE — needs swap) |
| 9f | n21_infinite_ugcs | `🍳 Create Image (Seedream 4.0 via Kie AI).json` | — | n21 Create Image Seedream | Sub (KIE — needs swap) |
| 9g | n21_infinite_ugcs | `🍳 Create Video (Veo3-fast via Kie AI).json` | — | n21 Create Video Veo3-fast | Sub (KIE — needs swap) |
| 10 | n29_templates | 3 JSONs (Sora, LI/X, Script) | 14430+ | n29 Quality / Transform Templates | 3 separate Main workflows |
| 11 | n30_product_videography | `n30 _ Product Videography (by RoboNuggets) (1).json` | 46455 | n30 Product Videography | Main |
| 12 | n31_precision_camera | `n31 _ Precision Camera Movements (by RoboNuggets).json` | 76540 | n31 Precision Camera | Main |

**Out of merge scope (Python, not n8n):** R55 (Modal-deployed Vizard clipper), R57 (Fal image engine), R61 (cinematic video). These are tracked in `obsidian-brain/pipelines/` but are not on the canvas. If trigger webhooks for them are wanted (Phase 5.5), they become **new** small n8n workflows that write to the existing Airtable tables `tblnpiwNYF3zJXm9Q` (R57) and `tbl1hd8yprLTZia4c` (R61), then the Python pipelines poll those tables.

### 0.2 Obsidian brain — load-bearing facts for the merge

- **Shared Airtable base:** `appC3HqG42ftswOvw`. R57 = `tblnpiwNYF3zJXm9Q`. R61 = `Video` / `tbl1hd8yprLTZia4c`. All other pipelines (R46/R51/R34/R39/n3/n16/n16.1/n19/n21/n29/n30/n31) **unbound** — need new tables created when activated.
- **Blotato is schedule-only.** Every Blotato call must include a future `scheduledTime`. Wrapped shape `{"post": {...}, "scheduledTime": "..."}`. Accounts endpoint is `/v2/users/me/accounts`, NOT `/v2/accounts`.
- **KIE is dead.** Fal.ai replaces it everywhere. Fal slugs canon:
  - `nano-banana-pro` → `fal-ai/nano-banana/edit` (with refs) or `fal-ai/nano-banana` (text-only)
  - `kling-3.0` → `fal-ai/kling-video/v2.1/master/image-to-video`
  - `sora-2-pro` → `fal-ai/sora-2/image-to-video/pro`
  - `veo3-fast` → `fal-ai/veo3-fast`
- **Doc rot:** R57 and R39 markdown still mentions KIE; this is informational only. Trust the code, not the prose.
- **Frameworks (canvas grouping rationale):**
  - `content_extraction_framework` = R46 + R51
  - `ugc_framework` = n21 + R39 + n19
  - `video_ads_framework` = R61(Python) + n30 + n31
  - `narrative_video_framework` = n16 + n16.1 + R34
- **Never overwrite generated content.** Always version-increment output paths.
- **R2 clock-skew patch** (`botocore.utils.get_current_datetime` + `botocore.auth.get_current_datetime`) — only relevant if an n8n node pushes to R2 directly (no current pipeline does; n16.1 reads R2).
- **n21 KIE landmine:** all 4 image/video sub-workflows are hardcoded to KIE. DO NOT run n21 until Fal swap is done.

---

## ❌ PHASE 1 — Backup & canvas analysis (BLOCKED)

**1.1** Export of `SmtkmTgfCTLZPlN4` to `n8n_backups\GetAutomata_W01-W05_backup_2026-05-13.json` — **cannot execute** without API. Operator should attempt this manually via n8n UI download once CF Access is bypassed, OR allow me to retry once API works.

**1.2** Canvas analysis (node list, bounding box, sticky notes, existing creds) — depends on 1.1 file. Cannot do.

**1.3** Safe starting Y = max_Y + 400 — formula known, max_Y unknown until 1.2.

**Assumption to apply once unblocked:** if max_Y of current canvas is `Y0`, all new sections start at `Y0 + 400` and stack downward in 1200px slots per pipeline.

---

## ✅ PHASE 2 — Pipeline inspection (DONE — brain-corrected)

Pipeline inspection from prior analysis turn refined with brain context. Each row gives: external API surface, in-JSON credential type+id, broken refs flagged for swap, structural gaps.

### A. R46 Ultimate Extract
- **Nodes (key):** Apify (×7), Airtable (×8), Form trigger, Set/Filter
- **Creds in JSON:** `apifyOAuth2Api` (id `ENbIGOecErZBpoLD`, name "Apify account"), `airtableTokenApi` (id placeholder `REPLACE_WITH_PAT_CREDENTIAL_ID`, name "Airtable Personal Access Token")
- **Airtable tables touched on base `appC3HqG42ftswOvw`:** `tblrc4ILrLINc6rVy`, `tbl59JhHWb07isxR8`, `tbl7IJMsbRMy1NwnW`, `tblCHWVm1tqrpHeGJ`, `tblbIkcFGqgKVGsHr`, `tblqgMjGVrY9p5IEi`, `tblgYOJucqBTAwLMm`, `tblWdSTGmlndt6UwR`
- **Broken refs:** none
- **Status:** READY once creds bound

### B. R51 Creative Cloner
- **Nodes (key):** Google Gemini, OpenRouter, Airtable (×8), Schedule triggers (×4), HTTP nodes for WaveSpeed + KIE
- **Creds in JSON:** `googlePalmApi` (`vk56cHrZU444NgZQ`), `openRouterApi` (`hmP48RU4dJfJaaSV`), `airtableTokenApi` (`Gik7e1Ksb0K9anPI`, "Airtable account"), `httpHeaderAuth` WaveSpeed (`IZqnM1MEeUfWcob3`), `httpHeaderAuth` **KIE** (`GY8EwBg1KMzSwh9X`)
- **Airtable tables on `appC3HqG42ftswOvw`:** `tbl6mWeZktOw3Gaoq`, `tbl56RJdZs4rBQXdd`
- **Broken refs:**
  - 🔴 KIE Suno music: `api.kie.ai/api/v1/generate` + `/generate/record-info` → swap to Fal Suno equivalent (verify which Fal slug; ElevenLabs Music or `fal-ai/lyria-2` are candidates)
  - 🟡 Hardcoded callback `https://api.example.com/callback`
- **Status:** NEEDS FIXES

### C. R34 VeoRobo
- **Nodes (key):** Schedule, LangChain agent + OpenRouter, Code, Airtable, Fal HTTP, Blotato HTTP
- **Creds in JSON:** `openRouterApi` (`gpOxOvCHLqdEMcaD`), `airtableTokenApi` (placeholder `AIRTABLE_PAT_PLACEHOLDER`, "Airtable PAT"), `httpHeaderAuth` Fal (`fLJXjcjJjHekzjid`, "Fal AI Credential - r33"), `httpHeaderAuth` Blotato v2 (`PALbCt4SkGzvuqFN`)
- **Airtable:** base `appC3HqG42ftswOvw` (table `tbl0IpDJZw0ud45LO` per sticky note)
- **Broken refs:** none — already KIE-stripped, Sheets-stripped (sticky note in JSON confirms)
- **Status:** READY once creds bound. Per brain: cred should be FAL_KEY-backed, Airtable PAT bound to `appC3HqG42ftswOvw`.

### D. R39 Split AI System (raw template — NOT ported)
- **Nodes (key):** Telegram trigger, Box (×2+), OpenAI agent, Google Sheets (×3), HTTP to Telegram API
- **Creds in JSON:** `boxOAuth2Api` (`g94zYSbBNeR9PtGA`), `telegramApi` (`CrSrYX7BqnvCGioc`), `openAiApi` (`CRXcwVtODws9mTd1`), `googleSheetsOAuth2Api` (`kyZpZ72Pl8dphEXk`)
- **Google Sheet referenced:** `1v2urk2p3OLGwyQU9lasYD9ffbDFQnyp4F1wdUgxPYlc`
- **Broken refs:**
  - 🔴 Box → R2 swap per project rules. **Brain note:** brain describes Box as "asset handoff between nodes" without explicitly mandating swap — but CLAUDE.md rules are explicit. Flag for operator to confirm.
  - 🔴 Google Sheets → Airtable swap
  - 🟡 Telegram bot id hardcoded in expressions
- **Status:** NEEDS HEAVY REWRITE before merge value-adds

### E. n3 Voice & Subs
- **Nodes (key):** Schedule, OpenAI (×4), Google Sheets (×2), Fal HTTP (×8 for ElevenLabs TTS via Fal queue + subs), Wait, Merge, Code
- **Creds in JSON:** `openAiApi` (`NyuhXI96tWK9dR2J`), `googleSheetsOAuth2Api` (`WmDBwEhcrLeG9D67`), `httpHeaderAuth` Fal (`fLJXjcjJjHekzjid`), `httpBasicAuth` Fal (`OLFUcGebSI77ITzJ`) — **two Fal cred entries, consolidate**
- **Endpoints OK:** `queue.fal.run/fal-ai/elevenlabs/tts/turbo-v2.5`
- **Google Sheet:** `1FgwtfdRV3WqRo_nrGOYjmV2zqvb2MY_oAxCDi3HgeZA`
- **Broken refs:** 🔴 Sheets → Airtable
- **Status:** NEEDS FIXES (Sheets swap + Fal cred consolidation)

### F. n16 Narrative Chaining
- **Nodes (key):** Manual trigger, OpenAI agent, ElevenLabs HTTP, Fal HTTP (×6 for Veo + first/last frame), KIE HTTP, Google Sheets (×5), Wait
- **Creds in JSON:** `openAiApi` (`zDZ32auFKuRIohXt`), `httpCustomAuth` ElevenLabs (`6yzgNwUoP2cfT1ov`), `httpHeaderAuth` Fal × 2 (`fLJXjcjJjHekzjid` + `8us2N7EU77ApbiYP` — consolidate), `httpHeaderAuth` **KIE** (`GY8EwBg1KMzSwh9X`), `googleSheetsOAuth2Api` (`WmDBwEhcrLeG9D67`)
- **Google Sheet:** `1x65wzvPcZAahQsegZ8h99Qh3boI5xRNymx-gtlE9QEU`
- **Broken refs:**
  - 🔴 KIE Veo: `api.kie.ai/api/v1/veo/generate`, `/veo/record-info` → swap to `fal-ai/veo3-fast`
  - 🔴 Sheets → Airtable
  - 🟡 Two Fal creds (consolidate)
- **Status:** NEEDS FIXES

### G. n16.1 ElevenLabs → NCA Toolkit
- **Nodes (key):** Webhook trigger, ElevenLabs **community node** (`n8n-nodes-elevenlabs-enhanced.elevenLabs`), PiAPI HTTP, S3/R2, OpenAI agent, NCA HTTP (×4), respondToWebhook
- **Creds in JSON:** `elevenLabsApi` (`iOvpLcJK0VkN7XCL`), `piAPIApi` (`tLdUHTT1TxJrmvCo`), `s3` (`gc6DZPBfhyeGhoyN`, "S3 cLOUDFLARE"), `openAiApi` (`QPZnBdHx3ZTb2QZi`), `httpCustomAuth` NCA (`W64g12bHEW1Ujb9b`)
- **Broken refs:** none structurally
- **Gaps:**
  - ⚠️ Community node `n8n-nodes-elevenlabs-enhanced` must be installed on ops.getautomata.ai before import
  - ⚠️ Verify NCA Toolkit endpoint reachability from the n8n instance
- **Status:** NEEDS PRE-INSTALL (community node) + creds

### H. n19 Ultimate Video Ads
- **Nodes (key):** Telegram trigger, OpenAI agent + LM, Google Sheets (×6), KIE HTTP (×4), Box (×2), Telegram bot send
- **Creds in JSON:** `telegramApi` (`pzInIPWCmzUAL9tS`, "robotutorials_bot"), `openAiApi` (`zDZ32auFKuRIohXt`), `googleSheetsOAuth2Api` (`WmDBwEhcrLeG9D67`), `httpHeaderAuth` **KIE** (`GY8EwBg1KMzSwh9X`), `boxOAuth2Api` (`z1F7fuocI0Mht5WE`)
- **Google Sheet:** `1v2urk2p3OLGwyQU9lasYD9ffbDFQnyp4F1wdUgxPYlc` (same as R39 — repurposed?)
- **Broken refs:**
  - 🔴 KIE Veo + nano-banana-edit endpoints (×4)
  - 🔴 Box → R2
  - 🔴 Sheets → Airtable
  - 🟡 Telegram bot needs fresh credentials
- **Status:** HEAVIEST REWRITE — KIE+Box+Sheets+Telegram all need touching

### I. n21 Infinite UGCs (orchestrator + 5 sub-workflows + bulk runner)
- **Orchestrator/Bulk creds:** `openAiApi` (`zDZ32auFKuRIohXt`), `googleSheetsOAuth2Api` (`WmDBwEhcrLeG9D67`)
- **Google Sheet:** `1mxpTRFrYKQAG6Fbwr1yjwOaHJn5tpxC8U6aA2b3NT8E`
- **Sub-workflow status:**
  - `Combine Clips (FFMPEG via Fal AI)` — OK
  - `Create Image (GPT-image-1 via Kie AI)` — 🔴 KIE swap
  - `Create Image (Nanobanana via Kie AI)` — 🔴 KIE swap → `fal-ai/nano-banana/edit`
  - `Create Image (Seedream 4.0 via Kie AI)` — 🔴 KIE swap → likely `fal-ai/bytedance/seedream` (verify)
  - `Create Video (Veo3-fast via Kie AI)` — 🔴 KIE swap → `fal-ai/veo3-fast`
- **executeWorkflow rewiring required:** orchestrator and bulk-runner reference sub-workflow IDs that don't exist on target n8n. After importing sub-workflows, the new IDs must be patched into the executeWorkflow nodes.
- **Status:** **DO NOT MERGE AS-IS.** 4 sub-workflows must be Fal-swapped first. Brain explicitly flags this.

### J. n29 Templates (3 separate workflows)
- **Common creds:** `googlePalmApi` (`Uf69yXezkjIZP6Ah`), `telegramApi` × 2 (`lQn98mDFXokupopl` "Robo Tutorials Bot" + `rSWai5EUNllXsaLS` "Tutorials Robo Bot"), `blotatoApi` **community node** (`kL3kwivG5ErCmAl8`)
- **Sora variant additionally:** `httpHeaderAuth` **KIE** (`GY8EwBg1KMzSwh9X`)
- **Broken refs (Sora variant only):**
  - 🔴 KIE Sora endpoints `/jobs/createTask` + `/jobs/recordInfo` → swap to `fal-ai/sora-2/image-to-video/pro`
- **Gaps:**
  - ⚠️ Community node `@blotato/n8n-nodes-blotato` must be installed before import
  - ⚠️ Telegram bot creds need fresh tokens
- **Status:** NEEDS COMMUNITY NODE + Sora variant needs Fal swap

### K. n30 Product Videography
- **Nodes (key):** Webhook, Airtable (×3), OpenRouter agent, Google Gemini, WaveSpeed HTTP (nano-banana-pro edit), KIE HTTP (veo)
- **Creds in JSON:** `airtableTokenApi` (`Gik7e1Ksb0K9anPI`), `openRouterApi` (`hmP48RU4dJfJaaSV`), `googlePalmApi` (`Uf69yXezkjIZP6Ah`), `httpHeaderAuth` WaveSpeed (`IZqnM1MEeUfWcob3`), `httpHeaderAuth` **KIE** (`GY8EwBg1KMzSwh9X`)
- **Broken refs:**
  - 🔴 KIE Veo (`/veo/generate`, `/veo/record-info`) → Fal
  - 🟡 WaveSpeed nano-banana-pro — works but consider Fal nano-banana for consistency (not required)
- **Status:** NEEDS FIXES (KIE swap)

### L. n31 Precision Camera
- **Nodes (key):** Airtable (×10+), Schedule triggers (×5), OpenRouter agent, Google Gemini, WaveSpeed HTTP (nano-banana-pro + kling-v2.5-turbo-pro), Wait
- **Creds in JSON:** `airtableTokenApi` (`Gik7e1Ksb0K9anPI`), `openRouterApi` (`hmP48RU4dJfJaaSV`), `googlePalmApi` (`Uf69yXezkjIZP6Ah`), `httpHeaderAuth` WaveSpeed only
- **Broken refs:** **NONE** — cleanest workflow of the batch
- **Status:** READY once creds bound. Recommended first import after R46/R34.

---

## ✅ PHASE 3 — Master credential map (DONE)

### 3.1 Standardized credential names (one cred per service, not per pipeline)

| Service | Cred type in n8n | Standardized name | Used by |
|---|---|---|---|
| Airtable | `airtableTokenApi` | `Airtable PAT (Provinzial)` | R46, R51, R34, R39*, n3*, n16*, n19*, n21*, n30, n31 |
| Apify | `apifyOAuth2Api` | `Apify (Provinzial)` | R46 |
| OpenRouter | `openRouterApi` | `OpenRouter (Provinzial)` | R51, R34, n30, n31 |
| Google AI (Gemini) | `googlePalmApi` | `Google Gemini (Provinzial)` | R51, n29×3, n30, n31 |
| OpenAI | `openAiApi` | `OpenAI (Provinzial)` | n3, n16, n19, n21, n16.1, R39 |
| Fal AI | `httpHeaderAuth` | `Fal AI (Provinzial)` — header `Authorization: Key <FAL_KEY>` | R34, n3, n16, n16.1 (PiAPI separate), R51*, n19*, n21×4 subs*, n29 Sora*, n30* |
| WaveSpeed | `httpHeaderAuth` | `WaveSpeed (Provinzial)` | R51, n30, n31 |
| KIE AI | — | **DO NOT CREATE** | All KIE nodes must be swapped to Fal |
| Blotato (v2 custom) | `httpHeaderAuth` | `Blotato v2 (Provinzial)` | R34 |
| Blotato (community) | `blotatoApi` | `Blotato (Provinzial)` | n29×3 (after community node install) |
| ElevenLabs (custom) | `httpCustomAuth` | `ElevenLabs custom (Provinzial)` | n16 |
| ElevenLabs (native) | `elevenLabsApi` | `ElevenLabs (Provinzial)` | n16.1 |
| PiAPI | `piAPIApi` | `PiAPI (Provinzial)` | n16.1 |
| Cloudflare R2 | `s3` | `R2 (Provinzial — trendiva-raw-assets)` | n16.1 (read); future swaps from Box (R39, n19) |
| NCA Toolkit | `httpCustomAuth` | `NCA Toolkit` | n16.1 |
| Box | — | **DO NOT CREATE** | Swap to R2 per CLAUDE.md rule 3 |
| Google Sheets | — | **DO NOT CREATE** | Swap to Airtable |
| Telegram | `telegramApi` | `Telegram - <bot-name>` (one per bot) | R39, n19, n29×3 — each needs fresh bot token |

`*` = pipeline uses this credential AFTER required swaps land.

### 3.2 Existing-vs-create on live workflow
**UNKNOWN** — depends on Phase 1.2 inspection of `SmtkmTgfCTLZPlN4` current credentials. Once exported, cross-reference the existing cred list against the table above; standardize names; manually create gaps in the n8n UI before merge.

### 3.3 Swap plans (offline, ready to apply post-export)

**KIE → Fal swap matrix** (in-JSON URL change + cred rebind):

| Pipeline | KIE endpoint | Replace with Fal | Auth |
|---|---|---|---|
| R51 | `api.kie.ai/api/v1/generate` (Suno music) | `queue.fal.run/fal-ai/lyria-2` (verify slug) | Fal header |
| R51 | `api.kie.ai/api/v1/generate/record-info` | `queue.fal.run/fal-ai/lyria-2/requests/{id}` | Fal header |
| n16 | `api.kie.ai/api/v1/veo/generate` | `queue.fal.run/fal-ai/veo3-fast` | Fal header |
| n16 | `api.kie.ai/api/v1/veo/record-info` | `queue.fal.run/fal-ai/veo3-fast/requests/{id}` | Fal header |
| n19 | `api.kie.ai/api/v1/veo/generate` | `queue.fal.run/fal-ai/veo3-fast` | Fal header |
| n19 | `api.kie.ai/api/v1/jobs/createTask` (nano-banana-edit) | `queue.fal.run/fal-ai/nano-banana/edit` | Fal header |
| n19 | `api.kie.ai/api/v1/jobs/recordInfo` | `queue.fal.run/fal-ai/nano-banana/edit/requests/{id}` | Fal header |
| n19 | `api.kie.ai/api/v1/veo/record-info` | `queue.fal.run/fal-ai/veo3-fast/requests/{id}` | Fal header |
| n21 sub: Nanobanana | KIE jobs/createTask + recordInfo | `fal-ai/nano-banana/edit` | Fal header |
| n21 sub: Seedream | KIE jobs/createTask + recordInfo | `fal-ai/bytedance/seedream` (verify) | Fal header |
| n21 sub: GPT-image-1 | KIE jobs/createTask + recordInfo | `fal-ai/gpt-image-1` (verify) or keep direct OpenAI Images | Fal header / OpenAI |
| n21 sub: Veo3-fast | KIE veo/generate + record-info | `fal-ai/veo3-fast` | Fal header |
| n29 Sora | KIE jobs/createTask + recordInfo | `fal-ai/sora-2/image-to-video/pro` | Fal header |
| n30 | KIE veo endpoints | `fal-ai/veo3-fast` | Fal header |

**Sheets → Airtable swap matrix** (need to design Airtable table schemas to replace each sheet):

| Pipeline | Google Sheet ID | Replacement Airtable table (TBD design) |
|---|---|---|
| R39 | `1v2urk2p3OLGwyQU9lasYD9ffbDFQnyp4F1wdUgxPYlc` | New `R39_SplitAI` table on `appC3HqG42ftswOvw` |
| n3 | `1FgwtfdRV3WqRo_nrGOYjmV2zqvb2MY_oAxCDi3HgeZA` | New `n3_VoiceSubs` table |
| n16 | `1x65wzvPcZAahQsegZ8h99Qh3boI5xRNymx-gtlE9QEU` | New `n16_NarrativeChaining` table |
| n19 | `1v2urk2p3OLGwyQU9lasYD9ffbDFQnyp4F1wdUgxPYlc` (same as R39) | New `n19_VideoAds` table |
| n21 | `1mxpTRFrYKQAG6Fbwr1yjwOaHJn5tpxC8U6aA2b3NT8E` | New `n21_UGCs` table |

**Box → R2 swap (R39 + n19):** replace Box nodes with HTTP nodes against R2 S3 API at `https://bac1091b224817fd422a89cd335cc4f1.r2.cloudflarestorage.com`, bucket `trendiva-raw-assets`, using existing `s3 cLOUDFLARE` cred pattern from n16.1.

### Community nodes to install on ops.getautomata.ai BEFORE merge
1. `@blotato/n8n-nodes-blotato` — for n29×3
2. `n8n-nodes-elevenlabs-enhanced` — for n16.1
3. `@apify/n8n-nodes-apify` — for R46

If any of these are absent at import time, the affected JSONs will surface "unknown node type" errors.

---

## 📐 PHASE 4 — Staged merge — LAYOUT PLAN (cannot execute)

**Cannot patch live workflow until Phase 1 unblocks.** Layout plan below is ready to apply once exported `SmtkmTgfCTLZPlN4` JSON is available.

### Canvas layout (relative offsets from existing canvas bottom)

Let `Y0` = max_Y of existing canvas after Phase 1.2 inspection. New sections stack at `Y0 + 400 + N×1200`.

| Slot | Y offset from Y0 | Framework group | Pipeline | Section label (sticky) |
|---|---|---|---|---|
| 0 | +400 | content_extraction | R46 | `## §A R46 — Extract` |
| 1 | +1600 | content_extraction | R51 | `## §B R51 — Clone` |
| 2 | +2800 | narrative_video | R34 | `## §C R34 — VeoRobo (3-scene)` |
| 3 | +4000 | narrative_video | n16 | `## §D n16 — Narrative Chaining` |
| 4 | +5200 | narrative_video | n16.1 | `## §E n16.1 — Auto Subtitles` |
| 5 | +6400 | ugc | R39 | `## §F R39 — Split AI Images` |
| 6 | +7600 | ugc | n19 | `## §G n19 — Video Ads` |
| 7 | +8800 | ugc | n21 + 5 subs | `## §H n21 — Infinite UGCs` |
| 8 | +10000 | video_ads | n30 | `## §I n30 — Product Videography` |
| 9 | +11200 | video_ads | n31 | `## §J n31 — Precision Camera` |
| 10 | +12400 | enhancement | n3 | `## §K n3 — Voice & Subs` |
| 11 | +13600 | qa/transform | n29 (×3) | `## §L n29 — Quality / Transform` |
| **Optional (Phase 5.5)** | | | | |
| 12 | +14800 | trigger | Trigger R57 (new) | `## §T1 R57 webhook trigger` |
| 13 | +16000 | trigger | Trigger R61 (new) | `## §T2 R61 webhook trigger` |

Each slot reserves 1200px vertical. Within a slot, nodes flow left-to-right starting at `X=0`. Sub-workflow groups (n21) get a horizontal sub-band of 600px.

### Per-pipeline merge steps (apply in this order)

1. **R46** — clean import, bind creds. Foundation.
2. **R34** — clean import, bind creds. Brain confirms ready.
3. **R51** — import, then patch KIE Suno → Fal Lyria-2 (verify slug), fix placeholder callback URL.
4. **n31** — clean import (no swaps).
5. **n30** — import, patch KIE Veo → Fal Veo3-fast.
6. **n3** — import, patch Sheets → Airtable (requires new table). Consolidate Fal creds.
7. **n16** — import, patch KIE Veo + Sheets→Airtable. Consolidate Fal creds.
8. **n16.1** — import (verify community node present). Bind R2 cred.
9. **n29** (×3) — import after Blotato community node installed. Patch Sora variant KIE → Fal.
10. **R39** — defer if heavy rewrite is risky; otherwise patch Box→R2 + Sheets→Airtable + new Telegram bot.
11. **n19** — defer/last: heaviest rewrite (KIE+Box+Sheets+Telegram).
12. **n21** — DEFER until Fal-swapped sub-workflows verified. After import, rewire executeWorkflow IDs to new sub IDs.

### Node ID remapping protocol (Phase 4.2)
- Every node `id` in incoming JSONs is a UUID. Before patching, regenerate all UUIDs in the incoming JSON (substring-replace with fresh UUIDs while preserving inter-node `connections` mapping).
- Rationale: the operator rule says "UUIDs must be unique across the merged canvas." If a future import collides with an existing UUID, the patch silently rejects.

### Sticky note convention
- Section header sticky: 400×60, color 5 (gray), top-left at slot Y offset, content `## §<letter> <pipeline> — <one-line purpose>`.
- Below section header, place a credential-flag sticky listing required creds (240×120, color 7 = yellow).

---

## 🔀 PHASE 5 — Cross-pipeline wiring — DESIGN (cannot execute)

### 5.1 R46 → R51 (auto-clone winners)
Trigger: when R46's Meta_Ads OR TikTok Airtable table gets a new record with `days_on_air > 7`.
Implementation: add an Airtable trigger node (or a 5-minute schedule + filter) reading the relevant R46 table, filter for `days_on_air > 7 AND clone_status IS NULL`, then `executeWorkflow` into the R51 section.
Tables: R46 writes 8 tables; brain says specifically Meta_Ads + TikTok. Need to confirm which of the 8 table IDs are "Meta_Ads" and "TikTok" once we can read field names in n8n.

### 5.2 R51 → R61 handoff (documentation only)
Sticky note in R51 section pointing to `obsidian-brain/pipelines/R61.md` noting R61 (Python) reads Airtable table `tbl1hd8yprLTZia4c` looking for `Status = Ready for stitch` rows produced by R51.

### 5.3 n3 enhancement gate
After R34, R51, n19 final nodes (just before "Schedule via Blotato" steps), insert a Switch node reading `add_voiceover` flag from the originating Airtable record. If `true`, `executeWorkflow` into n3 then return; else pass through.
**Caveat:** n3 currently reads from Google Sheets. Until n3 is patched to Airtable (Phase 4 step 6), this wiring will not work.

### 5.4 n29 quality gate (post-video-gen)
After R34, n19, n21, n30, n31 generate a video, insert optional `executeWorkflow` into a dedicated `n29 Quality Check` sub-workflow that pulls the generated `video_url`, runs Gemini analysis, writes a `quality_score` field back to the originating Airtable record before Blotato scheduling. Blotato scheduling is conditional on `quality_score >= threshold` (operator decision: what threshold).
**Assumption (flagged):** threshold = 7/10 unless operator specifies.

### 5.5 Webhook triggers (per second user message in this turn)

**Decision applied from prior alignment:**
- Output to `C:\CONTENT_PIPELINE\_triggered\` — BUT since these are now merged into the SINGLE canvas, the equivalent is: each pipeline section on the canvas starts with a `Webhook` trigger node in addition to its existing trigger. Coexist mode.
- Add webhooks NOW (operator confirmed: webhooks first, body rewrites later).
- Coexist with existing triggers.
- One shared `PipelineRequests` Airtable table (operator confirmed).

**Shared `PipelineRequests` table schema (to create in `appC3HqG42ftswOvw`):**

| Field | Type | Notes |
|---|---|---|
| `request_id` | Autonumber / Formula | Primary key |
| `pipeline_id` | Single select | R57, R61, R46, R51, R34, R39, n19, n21, n30, n31, n3, n16, n29 |
| `params` | Long text | JSON payload from webhook |
| `status` | Single select | Pending, In Progress, Done, Failed |
| `webhook_id` | Single line text | n8n execution ID |
| `created_at` | Created time | Auto |
| `updated_at` | Last modified time | Auto |
| `result_url` | URL | Final output (video/image) |
| `error` | Long text | If status=Failed |

**Webhook nodes to add (one per pipeline, including R57/R61 as new tiny workflows):**

| Trigger name | Path | Required JSON params | Pipeline section |
|---|---|---|---|
| Trigger R57 Content Engine | `POST /webhook/r57` | none (or `niche`, `count`) | NEW sub-workflow — writes to `tblnpiwNYF3zJXm9Q` AND `PipelineRequests` |
| Trigger R61 Video Pipeline | `POST /webhook/r61` | `idx`, `pillar` | NEW sub-workflow — writes to `tbl1hd8yprLTZia4c` AND `PipelineRequests` |
| Trigger R46 Extract | `POST /webhook/r46` | `platform`, `keyword` | Added to §A; writes `PipelineRequests` row then enters R46 main flow |
| Trigger R51 Clone | `POST /webhook/r51` | `source_url`, `brand` | Added to §B |
| Trigger R34 VeoRobo | `POST /webhook/r34` | `niche`, `platform` | Added to §C |
| Trigger R39 Bulk Images | `POST /webhook/r39` | `product_image_url`, `ad_count` | Added to §F |
| Trigger n19 Video Ads | `POST /webhook/n19` | `product_image_url`, `platform` | Added to §G |
| Trigger n21 UGCs | `POST /webhook/n21` | `product`, `character` | Added to §H |
| Trigger n30 3D Product | `POST /webhook/n30` | `product_image_url` | Added to §I |
| Trigger n31 Camera Motion | `POST /webhook/n31` | `product_image_url`, `motion_style` | Added to §J |
| Trigger n3 Voiceover | `POST /webhook/n3` | `video_url`, `script`, `language` | Added to §K |
| Trigger n16 Extend Video | `POST /webhook/n16` | `video_url`, `target_length` | Added to §D |
| Trigger n29 Quality Check | `POST /webhook/n29` | `video_url` | Added to §L |

**Each webhook implements:**
1. Webhook trigger (POST, JSON body)
2. Set node — populate `pipeline_id`, generate `webhook_id` from `$execution.id`
3. Airtable "Create record" on `PipelineRequests` with status=Pending
4. RespondToWebhook — `{webhook_id, status: "Pending", message: "Queued"}` (immediate response)
5. Continue to existing pipeline main flow

**Webhook URLs** are not knowable until import. After Phase 1 unblock + Phase 4 merge, n8n will assign URLs of form `https://ops.getautomata.ai/webhook/<path>`. These will be recorded in the scaffold below.

---

## 📋 PHASE 6 — Final verification — PLAN (cannot execute)

6.1 Re-export merged workflow → `n8n_backups\GetAutomata_W01-W05_MERGED_2026-05-13.json`.
6.2 Final report (filled after 4–5 execute).
6.3 Update each `obsidian-brain/pipelines/<P>.md`:
- Add `n8n_workflow_id: SmtkmTgfCTLZPlN4`
- Add `canvas_section: §<letter> @ (X=0, Y=Y0+offset)`
- Add `credentials: [list]`
- Add `webhook_url: <if applicable>`
6.4 Update `C:\CONTENT_PIPELINE\CLAUDE.md` — add Phase-6 state section listing the merged workflow id + section coordinates per pipeline.
6.5 Run `codegraph sync` from `C:\CONTENT_PIPELINE\` to reindex.

---

## 🎯 OPERATOR DECISION POINTS

| # | Decision | Why blocked |
|---|---|---|
| 1 | **Resolve CF Access on ops.getautomata.ai/api/v1/*** | Blocks ALL API calls. See top of doc for 3 options. |
| 2 | **Install community nodes on ops** | `@blotato/n8n-nodes-blotato`, `n8n-nodes-elevenlabs-enhanced`, `@apify/n8n-nodes-apify`. Must be present before n29/n16.1/R46 import. |
| 3 | **Confirm R39 Box→R2 swap is wanted** | CLAUDE.md rule says yes; brain describes Box as "asset handoff" without mandate. Default = swap. |
| 4 | **Approve Fal slug mappings** | R51 Suno → Lyria-2 (or alternative); n21 Seedream slug; n21 GPT-image-1 (Fal vs direct OpenAI). |
| 5 | **Create `PipelineRequests` Airtable table** | Schema spec'd above. Webhook triggers depend on it. |
| 6 | **Quality threshold for n29 gate (5.4)** | Default assumption applied = 7/10. |
| 7 | **R57/R61 trigger webhooks IN-scope?** | Spec says yes. They become 2 new n8n workflows on the same canvas (sections T1, T2). |
| 8 | **Telegram bots — reuse or fresh?** | R39, n19, n29 all reference different bot ids. Fresh bots per pipeline is cleanest. |

---

## Files produced this turn

- `C:\CONTENT_PIPELINE\n8n_backups\` (directory, empty until Phase 1.1)
- `C:\CONTENT_PIPELINE\n8n_backups\PHASE_0-3_HANDOFF.md` (this file)
- `C:\CONTENT_PIPELINE\obsidian-brain\knowledge\webhook_registry.md` (scaffold, URLs blank)

**Nothing on the live workflow was touched.** Imports, patches, and verifications all wait on CF Access resolution.
