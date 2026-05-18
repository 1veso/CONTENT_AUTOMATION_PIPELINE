# Obsidian Brain — Master Index

## Strategic Source of Truth

**Mastermind Plan — Content Production Engine** is the authoritative doc for pipeline roles, composition patterns, and the campaign engine architecture.

Path: obsidian-brain/strategy/Mastermind_Plan_Content_Production_Engine.md

Read this BEFORE making any pipeline architecture, wiring, or composition decisions. If repo state conflicts with the Mastermind Plan, the Mastermind Plan wins.

---

Vault root for the CONTENT_PIPELINE knowledge base. Every file in the vault is linked from this page.

**Last updated:** 2026-05-15
**Repo:** `C:\CONTENT_PIPELINE\` — checked into GitHub at `1veso/CONTENT_AUTOMATION_PIPELINE` (private) on `main` and `dev`
**Active client:** Provinzial / Geier & Ayhan

## Pipeline status at a glance

| Pipeline | Purpose | Status | Output to date |
|----------|---------|--------|----------------|
| [[pipelines/R55_clipper]] | Long-form → Shorts (Vizard + Telegram) | 🟢 **Deployed on Modal, running** | Live in steady-state |
| [[pipelines/R57_content_engine]] | Daily static images (Fal.ai) | 🟢 **Deployed on Modal (2026-05-14), 30 images scheduled** | 30 images shipped |
| [[pipelines/R61_video_pipeline]] | Daily cinematic ad videos | 🟢 **Deployed on Modal (2026-05-14, +3 HTTP endpoints), captions flag added, all 30 final v3 scheduled** | 30 clips, 30 final v3 videos, 30 scheduled in Blotato |
| [[pipelines/R46_ultimate_extract]] | Reverse-engineer source video | ⚪ Template only |  |
| [[pipelines/R51_creative_cloner]] | Clone proven creative N times | ⚪ Template only |  |
| [[pipelines/R34_veorobo]] | 3-scene Veo template | ⚪ Template only |  |
| [[pipelines/R39_split_ai_system]] | Split-AI prompt architecture | ⚪ Template only |  |

**Posting hold:** active. Schedule freely, never immediate-post via Blotato. See [[knowledge/lessons_learned#Blotato hold]].

## Tomorrow Morning — Blockers (2026-05-19 EOD diagnostic)

Two perceived blockers reported during 2026-05-18 evening session on `[C]` chain. **Both operator hypotheses were diagnosed against Airtable Meta API and found NOT confirmed.** Read this before acting.

### Blocker 1 — `[C] Log Video` Base dropdown can't select "Provinzial — Geier & Ayhan"

- **Operator hypothesis:** PAT bound to credential `H9KNuMkfQ5Tl0Muu` ("Airtable PAT") lacks scope for `appC3HqG42ftswOvw`.
- **Diagnosis:** PAT in `R61_video_pipeline/.env` (`patkw6fr...`, 82 chars) DOES have access to `appC3HqG42ftswOvw` with `create` permission. Returns 1 base when hitting `GET /v0/meta/bases`. Scope is sufficient *if* the n8n credential is bound to the same PAT.
- **Likely real cause:** Either (a) the n8n credential `H9KNuMkfQ5Tl0Muu` holds a DIFFERENT token than the one in `R61_video_pipeline/.env`, or (b) n8n's dropdown cache is stale, or (c) the base was renamed in Airtable from "Provinzial — Geier & Ayhan" to **"R57 Content Engine"** (its current Airtable name) — so the dropdown would now list it under the new name, not the cached one.
- **Where to click (in order, stop at first success):**
  1. n8n → Credentials → "Airtable PAT" (id `H9KNuMkfQ5Tl0Muu`) → reveal token → compare against `R61_video_pipeline/.env::AIRTABLE_API_KEY`. If different, paste the working one in and Save.
  2. Re-open `[C] Log Video` → click Base dropdown → look for **"R57 Content Engine"** (NOT "Provinzial — Geier & Ayhan"). Same ID, just renamed in Airtable. n8n's `cachedResultName` is stale.
  3. If dropdown still empty, click the refresh icon next to it, or click out + back in to force re-fetch.

### Blocker 2 — `[C] Update Video Status` "Done" option missing

- **Operator hypothesis:** R34_VeoRobo Status singleSelect field doesn't have a "Done" option, or has different casing/names.
- **Diagnosis:** **DEBUNKED.** Table `tbl0IpDJZw0ud45LO` (R34_VeoRobo) Status field has exactly: `['Pending', 'Generating', 'Done', 'Failed']` — exact case match. Both expressions used by `[C]` nodes ("Done" in Update Video Status, "Generating" in Log Video) match Airtable reality perfectly. No Airtable schema change needed.
- **Likely real cause if operator saw a "Done invalid" error:** Probably (a) operator was looking at a different table (e.g. R61 `Video` `tbl1hd8yprLTZia4c` which has a different Status enum), or (b) n8n's `schema` cache on the node is stale and showing old options — clicking "Refresh" on the columns mapping section would resync.

### Other open items carried over

- **Canvas activation:** rate-limited 5× via API end-of-session 2026-05-18. Flip the toggle from the n8n UI at `https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4`. Validation is clean (0 errors, `valid: true`).
- **n8n pod env vars** (operator-only, kubectl from admin machine): verify `R2_ENDPOINT=https://<accountId>.r2.cloudflarestorage.com` and `WEBHOOK_URL=https://ops.getautomata.ai`. Workstation kubectl is installed but has no cluster context.

## Client

- [[clients/Provinzial_Geier_Ayhan/brand_brief]] — voice / colours / pillars / NEVER-do list
- [[clients/Provinzial_Geier_Ayhan/campaign_log]] — 30-record table (idx / pillar / scheduled / status / R2 v2 / Airtable links)
- [[clients/Provinzial_Geier_Ayhan/content_library]] — every R57 image + R61 clip / VO / final URL
- [[clients/Provinzial_Geier_Ayhan/generation_notes]] — prompt v1/v2/v3 evolution, voice rationale, what worked / failed
- `clients/Provinzial_Geier_Ayhan/assets/` — local asset folder (configured as Obsidian attachment dir)

## Pipelines

### Core (in-repo Python)
- [[pipelines/R55_clipper]]
- [[pipelines/R57_content_engine]]
- [[pipelines/R61_video_pipeline]]

### RoboNuggets templates (n8n JSONs in repo)
- [[pipelines/R46_ultimate_extract]]
- [[pipelines/R51_creative_cloner]]
- [[pipelines/R34_veorobo]]
- [[pipelines/R39_split_ai_system]]

### n8n integrations
- [[pipelines/integrations/n3_voice_and_subs]]
- [[pipelines/integrations/n16_narrative_chaining]]
- [[pipelines/integrations/n16.1_auto_subtitled_videos]]
- [[pipelines/integrations/n19_ultimate_video_ads]]
- [[pipelines/integrations/n21_infinite_ugcs]]
- [[pipelines/integrations/n29_analyze_video]]
- [[pipelines/integrations/n30_product_videography]]
- [[pipelines/integrations/n31_precision_camera]]

## Frameworks

Composition layer on top of pipelines. Pick a framework by output class.

- [[frameworks/README]] — how frameworks work; manual now, auto later
- [[frameworks/ugc_framework]] — n21 + R39 + n19
- [[frameworks/video_ads_framework]] — R61 + n30 + n31
- [[frameworks/content_extraction_framework]] — R46 + R51
- [[frameworks/narrative_video_framework]] — n16 + n16.1 + R34

## Knowledge

- [[knowledge/lessons_learned]] — every non-obvious learning from this build (R2 clock skew, Gemini TTS enum, Blotato shape, golden never-delete rule, skill listing budget mechanics, etc.)
- [[knowledge/prompt_library]] — all prompt versions across pipelines (v1 → v3)
- [[knowledge/model_costs]] — Fal / Higgsfield / Gemini TTS / ElevenLabs / R2 / Vizard / Modal cost table
- [[knowledge/tools_and_skills]] — installed skills, MCPs, CLIs (HyperFrames, claude-ads, firecrawl, camofox, optillm, caveman, ogilvy, provinzial-copy, …)
- [[knowledge/n8n_credentials]] — master credential list across every n8n template

## Agents

- [[agents/per_pipeline_agents]] — one Claude Code agent per pipeline, autonomous monitoring
- [[agents/openclaw_marriage]] — Claude Code + OpenClaw integration architecture

## Next actions

1. **Re-deploy remaining R61 HTTP endpoints** (3/6 now live: voiceover_gen_http, hf_stitch_http, blotato_schedule_http). The other 3 (frame_gen_http, video_gen_http, sync_r57_to_video_http) stay parked until Modal plan upgrade past the 8-endpoint cap.
2. ✅ ~~n8n ↔ Modal tunnel~~ wired 2026-05-15. §T1 R57 fires generate-images-http after WH-Respond (fire-and-forget). §T2 R61 routes voiceover/stitch/blotato via Switch on body.stage. See [[knowledge/n8n_modal_tunnel_blocker]] (wiring-as-built section).
3. ✅ ~~KIE → Fal swap across canvas + 4 sub-workflows + UGC orchestrator~~ done 2026-05-15. R51 lyria2, n16/n19 veo3/image-to-video, n19 nano-banana-pro/edit, Seedream v4/edit. Bodies, poll URLs (drop /status), Switch routing, response keys all migrated. Block 2.5+2.6.
4. **R61 narrative-structure layer (opt-in)** — `R61_NARRATIVE_MODE=true` splits voiceover into Hook/Problem/Lösung/CTA via Gemini Flash; `R61_BROLL_ENABLED` injects R2 b-roll between 3-7s via OpenAI embedding cosine match; `R61_VFX_ENABLED` adds 100ms crossfades; `R61_PLATFORMS=...` renders 10 platform variants. Off by default; existing pipeline unchanged.
5. **Voiceover Segments + Platform Variants Airtable fields** added 2026-05-15 to `tbl1hd8yprLTZia4c` via Meta API. JSON Long-text shape.
3. **n30 live canvas patch** — manual UI path documented in [[../n30_product_videography/MANUAL_PATCH_INSTRUCTIONS]] (~5 min). API path stays parked because `cleanStaleConnections` would wipe 30 documented TODO-sticky connection refs.
4. ✅ ~~Captions in `hf_stitch.py`~~ done — `--add-captions` flag, ASS burn-in, captioned variant goes to `final/<tag>/captions/` (commit `2facccc`).
5. ✅ ~~Geier & Ayhan persona for `provinzial-copy` skill~~ done — NRW Geschäftsstelle brief landed in §7 (commit `d369498`).
6. **Schaden campaign kickoff** — preflight checklist at [[../campaigns/Provinzial_Schaden_Campaign/PREFLIGHT_CHECKLIST]]. ~$50 cost, 120 posts, 30 days. Operator approval gates listed in checklist §5 and §10.
7. **Per-pipeline agents** — choose host, write system prompts, wire OpenClaw
7. ✅ ~~ElevenLabs unblock~~ done (v3 renders shipped)
8. ✅ ~~Schedule grids~~ done (30 records scheduled in Blotato)
9. ✅ ~~R2 filename slug cleanup~~ done — see [[knowledge/r2_filename_cleanup]]
10. ✅ ~~Version-increment rule~~ done — `check_output_path` wired across tools, `R61_VERSION_TAG` env var

## Rules (non-negotiable)

1. Never throwaway scripts — extend existing tools inline
2. Always confirm cost before any paid generation call
3. Blotato hold — schedule only, never immediate-post
4. R61 has four mandatory human gates (clip / raw select / pre-stitch / final preview)
5. Never delete / overwrite generated content — version-increment everywhere
6. Default to Fal.ai for image / video gen (KIE is ripped out)

## Conventions

- Files in this vault use Obsidian wiki-links: `[[file_name]]` or `[[file_name#heading]]`
- All dates are absolute YYYY-MM-DD (no "yesterday" / "Thursday")
- All money quotes are USD unless tagged otherwise
- Vault is checked into the repo at `C:\CONTENT_PIPELINE\obsidian-brain\`
