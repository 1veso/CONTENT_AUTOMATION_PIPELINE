# Obsidian Brain — Master Index

Vault root for the CONTENT_PIPELINE knowledge base. Every file in the vault is linked from this page.

**Last updated:** 2026-05-14
**Repo:** `C:\CONTENT_PIPELINE\` — checked into GitHub at `1veso/CONTENT_AUTOMATION_PIPELINE` (private) on `main` and `dev`
**Active client:** Provinzial / Geier & Ayhan

## Pipeline status at a glance

| Pipeline | Purpose | Status | Output to date |
|----------|---------|--------|----------------|
| [[pipelines/R55_clipper]] | Long-form → Shorts (Vizard + Telegram) | 🟢 **Deployed on Modal, running** | Live in steady-state |
| [[pipelines/R57_content_engine]] | Daily static images (Fal.ai) | 🟢 **Deployed on Modal (2026-05-14), 30 images scheduled** | 30 images shipped |
| [[pipelines/R61_video_pipeline]] | Daily cinematic ad videos | 🟢 **Deployed on Modal (2026-05-14, functions-only), all 30 final v3 scheduled** | 30 clips, 30 final v3 videos, 30 scheduled in Blotato |
| [[pipelines/R46_ultimate_extract]] | Reverse-engineer source video | ⚪ Template only |  |
| [[pipelines/R51_creative_cloner]] | Clone proven creative N times | ⚪ Template only |  |
| [[pipelines/R34_veorobo]] | 3-scene Veo template | ⚪ Template only |  |
| [[pipelines/R39_split_ai_system]] | Split-AI prompt architecture | ⚪ Template only |  |

**Posting hold:** active. Schedule freely, never immediate-post via Blotato. See [[knowledge/lessons_learned#Blotato hold]].

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

1. **Re-deploy R61 HTTP endpoints** once Modal plan is upgraded past the 8-endpoint cap (the 6 `*_http` wrappers in `R61_video_pipeline/modal_app.py` are commented but ready)
2. **n8n ↔ Modal tunnel/reverse-proxy** — wire `ops.getautomata.ai`'s `/webhook/r57` and `/webhook/r61` to the Modal endpoints (see [[knowledge/webhook_registry#Phase 7]])
3. **n30 live canvas patch** — manually update 2 nodes in UI per [[../n30_product_videography/MIGRATION_NOTES]], or `cleanStaleConnections` then re-attempt API patch
4. **Captions** — port [[pipelines/integrations/n16.1_auto_subtitled_videos]] flow into `hf_stitch.py`
5. **Geier & Ayhan persona** for `provinzial-copy` skill — awaits user brief
6. **Per-pipeline agents** — choose host, write system prompts, wire OpenClaw
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
