# Content Extraction Framework

Combines [[../pipelines/R46_ultimate_extract]] + [[../pipelines/R51_creative_cloner]] to reverse-engineer existing creative (yours or competitors') into reusable structures, then spin up variants on a new brief.

## When to pick this framework
- You have a **proven creative** (an ad that's working, a long-form video with structure worth keeping) and want to systematise it
- You need to **clone** a winner across many products or brands
- You want to **extract a hook bank** from competitor content for inspiration / variation seeding

## Composition

| Role | Pipeline | Output |
|------|----------|--------|
| Extract structure | [[../pipelines/R46_ultimate_extract]] | Transcript + hook map + shot list + b-roll suggestions |
| Generate variants | [[../pipelines/R51_creative_cloner]] | N adapted variations on a new brand brief |

## Execution order
1. Drop source video / image into R46 input
2. R46 extracts: transcript, scene structure, hook formula, b-roll keywords
3. Output goes into Airtable Extract table
4. Brief + extract → R51
5. R51 generates n branded variants using vision-LLM + image gen
6. Variants land in Airtable Variant table for human review
7. Approved variants enter [[video_ads_framework]] or [[ugc_framework]] for production

## Provider routing
- Extract LLM: OpenAI gpt-4o or Claude (vision-capable)
- Variant copy: OpenRouter / GPT / Claude
- Image gen: Fal (`nano-banana/edit` with refs from the extract)
- Optional Video gen: Fal Sora / Kling

## Provinzial fit
Could be useful for analysing Provinzial's existing campaign assets (historical Geier & Ayhan creative) to extract the working visual / copy formula, then variant-generate for the daily 30-spot calendar via [[video_ads_framework]].

## Related
- [[../pipelines/integrations/n29_analyze_video]] — single-shot "send X get Y" variant of this same idea
- [[narrative_video_framework]]
