# R57 — Content Engine

## What it does
Daily static-image ad generator. Reads a row from Airtable, builds a pillar-aware prompt, calls Fal.ai for nano-banana / GPT-Image-2 generation, writes the result back to Airtable, then queues for Blotato scheduling.

## Tools used
- **Fal.ai** — image gen (`fal-ai/nano-banana/edit` with refs, `fal-ai/nano-banana` text-only). KIE provider was ripped out — do not reintroduce.
- **Airtable** — row-per-day campaign sheet
- **Blotato** — scheduled posting (paused per hold)

## Credentials needed
- `FAL_API_KEY` (bridged to `FAL_KEY` for the SDK inside `config.py`)
- `AIRTABLE_API_KEY`
- `BLOTATO_API_KEY`
- Stored in `R57_content_engine/.env` (never committed)

## Status
**Phase 4 (Blotato scheduling) ON HOLD pending [[R61_video_pipeline]] completion.** Generation is complete — 30 images shipped for Provinzial campaign.

## Airtable
- Base: ``appC3HqG42ftswOvw``
- Table: ``May2025 - Provinzial_Geier&Ayhan`` (``tblnpiwNYF3zJXm9Q``)
- ``config.AIRTABLE_TABLE_NAME`` is URL-encoded; if user renames the table, update config.

## n8n template
None — pure Python via `tools/` (no n8n workflow JSON). Sibling templates in [[integrations/n21_infinite_ugcs]] cover the n8n-style equivalent for UGC.

## Provider conventions
- Default: **Fal.ai** for all image / video gen
- Model mappings: `nano-banana-pro` → `fal-ai/nano-banana/edit`; `kling-3.0` → `fal-ai/kling-video/v2.1/master/image-to-video`; `sora-2-pro` → `fal-ai/sora-2/image-to-video/pro`
- Prices in `config.py` COSTS table are approximate — verify at fal.ai/models

## Doc rot warning
`R57-README.md`, `.agent/AGENT.md`, `.agent/workflows/*.md`, `references/docs/kie-ai-api.md`, `references/docs/fabric_BRAND.md` still reference KIE in prose. They are informational only, NOT load-bearing for the runtime. Worth cleaning up before this template gets handed to someone else.

## Posting hold
[[../knowledge/lessons_learned|Blotato hold]] in effect.

## Related
- [[R55_clipper]]
- [[R61_video_pipeline]] — consumes R57's `Source Image` field as input
- [[../clients/Provinzial_Geier_Ayhan/content_library]]
- [[../frameworks/video_ads_framework]]
- [[../agents/per_pipeline_agents]]
