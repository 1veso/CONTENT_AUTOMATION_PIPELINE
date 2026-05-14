# R39 — Split AI System

## What it does
RoboNuggets "Split AI System" — splits a single complex creative brief into multiple specialised sub-prompts (hook, b-roll, voiceover, on-screen text), runs each through the right model, then re-merges into a finished spot. Designed to beat any single mega-prompt by giving each part its best-fit model.

## Tools used (per n8n template + docs)
- Multiple LLMs in parallel (OpenAI for copy, Claude for structure, Gemini for visuals)
- Nano Banana via KIE (now Fal — see provider migration note in [[R57_content_engine]])
- Box for asset handoff between nodes
- Airtable as orchestration backbone

## Credentials needed
- `OPENAI_API_KEY` / `OPENROUTER_API_KEY`
- `GOOGLE_API_KEY`
- `FAL_API_KEY` (replaces KIE per project convention)
- `BOX_*`
- `AIRTABLE_API_KEY`

## Status
**Template — has documentation but no live instance.** Files:
- `R39 - START.md`
- `R39 - Agent_Prompt_Splitter.md`
- `R39 - FYI Box Set up.md`
- `R39-END_Output Section.md`
- `(template) 🥚 Split AI System - by RoboNuggets (R39).json`
- Reference sheet: `Kopija od (Template) R39 _ Split AI System (by RoboNuggets).xlsx`
- Diagram: `R39_nanobanana_split_system.png`

## n8n template
`R39_split_ai_system/(template) 🥚 Split AI System - by RoboNuggets (R39).json`

## Use case for Provinzial
The Split-AI pattern is the architectural backbone of the [[../frameworks/ugc_framework]] — the same split is being applied (manually so far) inside [[R61_video_pipeline]]. R39 + [[integrations/n19_ultimate_video_ads]] together is the extended version.

## Related
- [[integrations/n19_ultimate_video_ads]] — extended Split AI System
- [[integrations/n21_infinite_ugcs]]
- [[../frameworks/ugc_framework]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §F @ canvas Y=[6340, 7540]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/r39` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** telegramTrigger replaced with TODO sticky pointing to lux_bot. Box+Sheets swaps still TODO.
