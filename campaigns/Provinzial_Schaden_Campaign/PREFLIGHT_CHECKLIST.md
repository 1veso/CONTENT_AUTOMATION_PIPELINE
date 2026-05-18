# Schaden Campaign — Preflight Checklist

**Campaign:** Provinzial Schäden — 120 posts over 30 days
**Total estimated spend:** ~$50 (generation only; doesn't count Modal compute or R2 egress)
**Generated:** 2026-05-14
**Source brief:** `campaigns/Provinzial_Schaden_Campaign/CAMPAIGN_BRIEF.md`

Tick every box on this checklist before firing any webhook. Items in **bold** are non-trivial — they cannot be assumed done from a prior run.

---

## 1. Webhooks to fire

All five inbound n8n webhooks (`https://ops.getautomata.ai/webhook/...`). Each writes a `Pending` row to `PipelineRequests` (`tblLtTpXwFOpzDX4K`) on `appC3HqG42ftswOvw`, returns immediately, then continues into the pipeline body.

| Order | Pipeline | URL | Posts | Body shape |
|---|---|---|---|---|
| 1 | **R57** static images | `https://ops.getautomata.ai/webhook/r57` | 40 | `{"niche":"Schaeden Alltag","count":40,"campaign_id":"Schaden_2026_05"}` |
| 2 | **R61** cinematic videos | `https://ops.getautomata.ai/webhook/r61` | 25 (per-idx loop 1..25) | `{"idx":<n>,"pillar":"Schaden & Service","campaign_id":"Schaden_2026_05"}` |
| 3 | **R34** TikTok 3-scene Veo3 | `https://ops.getautomata.ai/webhook/r34` | 20 (loop) | `{"niche":"Schaeden Stories","platform":"TikTok","campaign_id":"Schaden_2026_05"}` |
| 4 | **n19** product video ads | `https://ops.getautomata.ai/webhook/n19` | 15 (CSV-driven) | `{"product_image_url":"<R2 url>","platform":"TikTok","campaign_id":"Schaden_2026_05"}` |
| 5 | **n21** UGC monologues | `https://ops.getautomata.ai/webhook/n21` | 20 (loop) | `{"product":"Provinzial Hausrat","character":"persona_<n>","campaign_id":"Schaden_2026_05"}` |

Fire order can be parallel-safe. CAMPAIGN_BRIEF.md §"End-to-end kickoff" has the curl loops. The fire commands themselves never invoke paid APIs directly — they enter a chain that does. Each chain must be verified independently before the first real call.

---

## 2. n8n credentials that must be bound (operator UI binding only — never API)

These are pre-existing canvas requirements (Phase 6). The canvas will fail at runtime if any of these are unbound or expired.

| Pipeline | Required credentials |
|---|---|
| **R57** | `airtableTokenApi`, `httpHeaderAuth` (Fal) |
| **R61** | `airtableTokenApi`, `httpHeaderAuth` (Fal), `httpHeaderAuth` (Higgsfield), `elevenLabsApi` (or PiAPI ElevenLabs proxy), `s3` (R2), `httpHeaderAuth` (Blotato v2) |
| **R34** | `httpHeaderAuth` (Fal), `openRouterApi`, `airtableTokenApi`, `httpHeaderAuth` (Blotato v2) |
| **n19** | `openAiApi`, `googlePalmApi`, `httpHeaderAuth` (Fal — replacing KIE), `s3` (R2 — replacing Box), `airtableTokenApi`, `n8n-nodes-base.telegram` bound to **lux_bot** (`WoB3AsOoB9cIKUrI`) |
| **n21** | `openAiApi`, `httpHeaderAuth` (Fal — replacing KIE in 4 sub-workflows), `airtableTokenApi`, `httpHeaderAuth` (Blotato v2) |
| All five WH chains | `airtableTokenApi` (for the `PipelineRequests` Airtable.create node) |

**Pre-existing gaps from Phase 6 still open:**

- ☐ `telegramTrigger` nodes for R39 / n19 / n29×3 require manual UI re-add and lux_bot binding (TODO stickies on canvas preserve original config).
- ~~☐ KIE → Fal swaps still pending in: **n19** (Veo + nano-banana-edit), **n21** (4 sub-workflows: Veo3-fast, nano-banana, Seedream, gpt-image-1).~~ **DONE 2026-05-15** — see `convo_log_primary.md` Session 3 and `_index.md:91` (R51 lyria2, n16/n19 veo3/image-to-video, n19 nano-banana-pro/edit, Seedream v4/edit).
- ☐ Sheets → Airtable swaps pending in: **n19, n21**.
- ☐ Box → R2 swap pending in: **n19**.
- ☐ n21 sub-workflows do not yet exist — 5 separate workflows must be created (Combine Clips, 3× Create Image, Create Video) and their IDs patched into the n21 orchestrator's TODO sticky positions.

**If any of the above is unresolved, n19 and n21 cannot run.** The campaign can still ship 65 of 120 posts (R57 + R61 + R34) with the remaining work paused.

---

## 3. Airtable tables — must exist + be empty/ready

| Table | Base | ID | Status check | Purpose |
|---|---|---|---|---|
| `May2025 - Provinzial_Geier&Ayhan` (R57) | `appC3HqG42ftswOvw` | `tblnpiwNYF3zJXm9Q` | **Verify no leftover Pending rows from prior campaign before kickoff.** R57 polls this table. | R57 image generation queue + output log |
| `Video` (R61) | `appC3HqG42ftswOvw` | `tbl1hd8yprLTZia4c` | **Verify Index field counter — R61 IDs increment from current max.** | R61 video generation queue (consumes R57 Source Image) |
| `PipelineRequests` | `appC3HqG42ftswOvw` | `tblLtTpXwFOpzDX4K` | Reachable; no schema changes needed since Phase 5. | All 16 webhook chains write `Pending` here |
| TikTok / IG / Meta / LinkedIn / Twitter / Reddit / YouTube_Longs / YouTube_Shorts / Meta_Ads (R46 sinks) | `appC3HqG42ftswOvw` | `tblrc4ILrLINc6rVy` / `tblCHWVm1tqrpHeGJ` / `tblWdSTGmlndt6UwR` / `tblbIkcFGqgKVGsHr` / `tblqgMjGVrY9p5IEi` / `tblgYOJucqBTAwLMm` / `tbl59JhHWb07isxR8` / `tbl7IJMsbRMy1NwnW` | Only relevant if R46 fires during campaign — not in v1 plan. | Per-platform R46 destination sinks |

R34, R39, n3, n16, n16.1, n19, n21, n29, n30, n31 — **no bound Airtable table yet**. CLAUDE.md says these need new tables created when activated. For this campaign, R34/n19/n21 will produce outputs into local Sheets fallback unless a new Airtable table is created. **Decision required:** ship to local Sheets for v1, or create the missing tables first.

---

## 4. Modal endpoints — must be warm

Live as of 2026-05-14, all `State: deployed` (`hello-58046` workspace). Cold start adds ~30s for R57, ~2-3min for R61 (large image with ffmpeg + Playwright + HyperFrames). Warm them with a `dry_run: true` POST before campaign kickoff.

| Endpoint | URL | Used by |
|---|---|---|
| R57 generate_images | `https://hello-58046--r57-content-engine-generate-images-http.modal.run` | R57 chain (if wired via tunnel — not yet) |
| R57 schedule_blotato | `https://hello-58046--r57-content-engine-schedule-blotato-http.modal.run` | R57 chain (if wired via tunnel — not yet) |
| R61 voiceover_gen | `https://hello-58046--r61-video-pipeline-voiceover-gen-http.modal.run` | R61 chain (if wired via tunnel — not yet) |
| R61 hf_stitch | `https://hello-58046--r61-video-pipeline-hf-stitch-http.modal.run` | R61 chain (if wired via tunnel — not yet) |
| R61 blotato_schedule | `https://hello-58046--r61-video-pipeline-blotato-schedule-http.modal.run` | R61 chain (if wired via tunnel — not yet) |

**Warm-up commands (run all 5 in parallel before fire):**

```powershell
curl -X POST https://hello-58046--r57-content-engine-generate-images-http.modal.run `
  -H "Content-Type: application/json" -d '{"dry_run": true}'

curl -X POST https://hello-58046--r57-content-engine-schedule-blotato-http.modal.run `
  -H "Content-Type: application/json" -d '{"dry_run": true}'

curl -X POST https://hello-58046--r61-video-pipeline-voiceover-gen-http.modal.run `
  -H "Content-Type: application/json" -d '{"dry_run": true}'

curl -X POST https://hello-58046--r61-video-pipeline-hf-stitch-http.modal.run `
  -H "Content-Type: application/json" -d '{"skip_publish": true}'

curl -X POST https://hello-58046--r61-video-pipeline-blotato-schedule-http.modal.run `
  -H "Content-Type: application/json" -d '{"dry_run": true}'
```

**Important:** ~~n8n is **not yet wired to call Modal** (the `WH-Log → WH-Respond` chain currently terminates without an HTTP Request to Modal). See `obsidian-brain/knowledge/n8n_modal_tunnel_blocker.md`. Until that's done, R57 and R61 work happens via Python poller, not Modal HTTP. The Modal endpoints are warm-tested for when the tunnel lands.~~ **DONE 2026-05-15** — tunnel wired. §T1 R57 fires `generate-images-http` after WH-Respond (fire-and-forget). §T2 R61 routes voiceover/stitch/blotato via Switch on `body.stage`. See `_index.md:90` and `obsidian-brain/knowledge/n8n_modal_tunnel_blocker.md` (wiring-as-built section). Caveat: R57 `schedule_blotato_http` wrapper is broken (missing `tools.blotato_schedule` import) — surfaced by Block 2 dry-runs 2026-05-18, see `convo_log_primary.md` Session 4.

**Modal secrets that must be present** (one-time, persistent in workspace):
- `r57-secrets` — `FAL_KEY`, `AIRTABLE_API_KEY`, `BLOTATO_API_KEY`, `GOOGLE_API_KEY`
- `r61-secrets` — `FAL_KEY`, `HIGGSFIELD_API_KEY`, `HIGGSFIELD_SECRET`, `R2_*` (5 vars), `AIRTABLE_*` (2 vars), `BLOTATO_API_KEY`, `GOOGLE_API_KEY`, `R61_VERSION_TAG=v3`
- `vizard-clipper-secrets` — R55 (already in place)

Verify with `modal secret list` from `C:\CONTENT_PIPELINE\` before kickoff.

---

## 5. Cost breakdown — must be confirmed with operator before any paid call (SOUL.md rule 3)

| Pipeline | Posts | Per-unit cost | Subtotal |
|---|---|---|---|
| R57 (Fal nano-banana / nano-banana-pro) | 40 images | ~$0.04 / image | **~$1.60** |
| R61 (Fal frames + Higgsfield clip + ElevenLabs TTS) | 25 videos | ~$0.40 / video | **~$10.00** |
| R34 (Fal Veo3-fast × 3 scenes) | 20 videos | ~$0.75 / video | **~$15.00** |
| n19 (Fal Veo3-fast + nano-banana-edit) | 15 ads | ~$0.55 / ad | **~$8.25** |
| n21 (Fal multi-model UGC) | 20 monologues | ~$0.75 / UGC | **~$15.00** |
| **Total** | **120 posts** | | **~$49.85** |

**Cost-table source:** `R57_content_engine/tools/config.py` COSTS table. Per-unit numbers above are approximations; verify each at `fal.ai/models` and (for Higgsfield) the Higgsfield dashboard before quoting to the operator.

**R2 storage** is not metered separately for this run — bucket `trendiva-raw-assets` is well within free-tier egress. **Modal compute** is on the workspace plan (free-tier — R61 hf_stitch is the heaviest at ~$0 per minute under current quota; if usage spikes, the 8-endpoint cap is what bites first, not cost).

**Cost-approval gate (SOUL.md rule 3):** the agent must surface this table to the operator on Telegram and wait for explicit "go" before any of the five chain heads fire.

---

## 6. Blotato — schedule-only (SOUL.md rule 1)

- ☐ Every post produced by this campaign carries a future `scheduledTime` in the Blotato call.
- ☐ The agent never invokes Blotato immediate-post endpoints. Verified by the n8n nodes already on canvas (`@blotato/n8n-nodes-blotato.blotato` with `scheduledTime` field present).
- ☐ Connected accounts in Blotato: TikTok, Meta, Instagram (R55/R57/R61 + R34/n19/n21 all use the same accounts).
- ☐ Schedule grid — distribute 120 posts across 30 days @ 4 posts/day. CAMPAIGN_BRIEF.md "Daily cadence" gives the per-day mix.
- ☐ The posting hold remains in force for **Provinzial** until the operator explicitly lifts it for a named client. For Schaden v1: schedule into Blotato draft state, leave posting hold ON.

---

## 7. Quality gates that cannot be skipped

| Gate | Where | Action |
|---|---|---|
| R61 Gate 0 — frame batch | After `frame_gen.py` | Operator approves/redos via Telegram inline keyboard. No Airtable mutation. |
| R61 Gate 1 — clip batch | After `video_gen.py` | Operator approves → `STATUS_APPROVED`; redo → `STATUS_REJECTED`. |
| R61 Gate 2 — raw R2 footage | Manual (no auto-pull per CLAUDE.md) | Operator selects R2 keys for stitch. |
| R61 Gate 3 — pre-stitch review | Before `hf_stitch.py` | Operator confirms voiceover + clip pairing. |
| R61 Gate 4 — final preview | After `hf_stitch.py` publish | Operator approves → Blotato schedule; redo → re-run `hf_stitch.py --record-id`. |
| n29 quality gate | All non-R57 videos (R34, R61, n19, n21 = 80 video posts) | Gemini-scored `quality_score >= 7/10` before Blotato schedule. Sticky at canvas Y=13200. |
| R57 visual check | Per-record in Airtable | Manual yes/no in Airtable Status field. |

**None of these are bypassable by the agent.** Each is wired to either Telegram approve/redo callbacks or an Airtable status field; the agent must wait for the operator's action.

---

## 8. Telegram operator channel

- ☐ Telegram bot active and allowlisted to `chat_id=1077552316`.
- ☐ `r61-gate-watcher` cron registered (`*/15 * * * *`) — polls `shared/gates/pending.json` and surfaces unnotified entries with approve/redo/hold inline keyboards.
- ☐ `morning-summary` cron registered (`0 8 * * *`) — daily digest will surface campaign progress against PipelineRequests counts.
- ☐ `keepalive` cron registered (`0 */6 * * *`) — silent.

---

## 9. Go / No-Go summary

A row can be **GO** only when every box on its row is ticked.

| Pipeline | Creds bound | Sub-workflows ready | Airtable target | Cost approved | Modal warm | Quality gate wired | Verdict |
|---|---|---|---|---|---|---|---|
| R57 | ☐ | n/a | ☐ | ☐ | ☐ (optional) | n/a | ☐ |
| R61 | ☐ | n/a | ☐ | ☐ | ☐ (optional) | ☐ (Gates 0–4 + n29) | ☐ |
| R34 | ☐ | n/a | ☐ (new table?) | ☐ | n/a | ☐ (n29) | ☐ |
| n19 | ☐ | ☐ (KIE→Fal, Box→R2, telegramTrigger) | ☐ | ☐ | n/a | ☐ (n29) | ☐ |
| n21 | ☐ | ☐ (5 sub-workflows missing) | ☐ | ☐ | n/a | ☐ (n29) | ☐ |

**Likely v1 ship state:** R57 + R61 + R34 = 85 posts (out of 120). n19 + n21 (35 posts) deferred until canvas TODOs are cleared.

---

## 10. Operator decisions still open (carry over to kickoff conversation)

1. ~~**n8n ↔ Modal tunnel** — keep using current Python poller (R57/R61 pull from Airtable), or wire HTTP Request nodes downstream of `WH-Log` per `n8n_modal_tunnel_blocker.md`? Tunnel lets Blotato scheduling happen end-to-end inside n8n; poller keeps the existing battle-tested path.~~ **DONE 2026-05-15** — tunnel chosen + wired. Both paths now exist; R57/R61 active path is via Modal HTTP downstream of WH-Respond (see `_index.md:90`).
2. **R34/n19/n21 Airtable tables** — create new tables before kickoff, or accept Sheets fallback for v1?
3. **n21 sub-workflows** — defer entirely (ship 100 posts instead of 120), or block on UI creation?
4. **Posting hold** — confirm Schaden v1 ships into Blotato as scheduled drafts, not live posts. Operator must say "lift hold for Provinzial Schaden" before any post goes live.
5. **Cost cap** — operator approval at the campaign level (~$50) or per-pipeline (split into 5 separate approvals)?
