# Frameworks

A **framework** is a *named combination* of pipelines that, when composed, produce a specific class of output. Pipelines are atomic — frameworks compose them.

## How they work right now (manual selection)
Today you pick a framework by hand: a client brief comes in, you read the framework's spec, and run the underlying pipelines in the order it documents. The pipelines themselves don't know they're being composed; the framework is metadata + a checklist.

## How they should work later (auto selection)
A per-pipeline agent ([[../agents/per_pipeline_agents]]) watches each pipeline's Airtable / state. A top-level orchestrator agent reads the client brief, picks the framework based on output class (UGC vs cinematic ad vs extraction vs narrative), and routes work to the right pipelines without human dispatch. Cost-approval and the four R61 human gates stay in place.

## Available frameworks

- [[ugc_framework]] — Infinite UGC variations (n21 + R39 + n19)
- [[video_ads_framework]] — Cinematic daily video ads (R61 + n30 + n31)
- [[content_extraction_framework]] — Reverse-engineer / extract from existing creative (R46 + R51)
- [[narrative_video_framework]] — Multi-scene story arc (n16 + n16.1 + R34)

## Cross-framework rules
- **Cost-approval gate** before any paid generation call.
- **Never delete or overwrite generated content** — version increment always (see [[../knowledge/lessons_learned]]).
- **Blotato hold** — schedule only, never immediate post.
- **R2 clock-skew patch** — required for any framework that lands assets in `trendiva-raw-assets`.
- **Default to Fal.ai** — KIE is ripped out across the repo.

## Related
- [[../pipelines/R55_clipper]] — clipper is upstream of multiple frameworks (it produces inputs)
- [[../agents/per_pipeline_agents]]
- [[../agents/openclaw_marriage]]
