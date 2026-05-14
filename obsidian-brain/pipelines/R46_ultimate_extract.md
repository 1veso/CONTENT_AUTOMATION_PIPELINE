# R46 — Ultimate Extract

## What it does
RoboNuggets "Ultimate Extract" workflow — pulls structured data (transcripts, key moments, hooks, b-roll suggestions) from a long-form video so it can feed downstream pipelines (R51 cloner, R57 image gen, R61 video gen).

## Tools used (per n8n template)
- Apify or similar scraper for source video metadata
- OpenAI / OpenRouter for transcription + extraction LLM passes
- Airtable (output target — extract sheet)
- Cloudinary or Box for media handoff

## Credentials needed
- `OPENAI_API_KEY` (or `OPENROUTER_API_KEY`)
- `APIFY_TOKEN`
- `AIRTABLE_API_KEY`
- `CLOUDINARY_URL` / `BOX_*`

## Status
**Template only — not wired up to a running instance.** JSON workflow lives at `R46_ultimate_extract/Ultimate Extract by RoboNuggets (R46) (1).json`. No `.env`, no Airtable base bound yet.

## Airtable
TBD on activation — likely a new "Extract" table per project.

## n8n template
`R46_ultimate_extract/Ultimate Extract by RoboNuggets (R46) (1).json`

## Use case for Provinzial
Could be paired with [[R55_clipper]] output to extract claim/scene structure from competitor insurance ads or Provinzial's own long-form material — feeds [[R57_content_engine]] / [[R61_video_pipeline]] with creative refs.

## Related
- [[R51_creative_cloner]]
- [[../frameworks/content_extraction_framework]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §A @ canvas Y=[0, 1140]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/r46` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** Apify scrapers + 8 Airtable sinks (TikTok, YT Longs/Shorts, IG, LinkedIn, Twitter, Reddit, Meta_Ads).
