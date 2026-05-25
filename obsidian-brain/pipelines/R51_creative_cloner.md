# R51 — Creative Cloner AI Agent

## What it does
RoboNuggets "Creative Cloner" — takes a reference creative (image or short video), reverse-engineers its structure / shot list / copy formula, then generates n variations adapted to a new brand or product brief.

## Tools used (per n8n template)
- Vision LLM (OpenAI gpt-4o / Claude / Gemini) for reference analysis
- OpenRouter / OpenAI for variant copy generation
- Fal.ai or KIE for image gen
- Airtable as variant tracker

## Credentials needed
- `OPENAI_API_KEY` / `OPENROUTER_API_KEY`
- `GOOGLE_API_KEY` (Gemini)
- `FAL_API_KEY`
- `AIRTABLE_API_KEY`

## Status
**Template only — not wired up.** JSON lives at `R51_creative_cloner/R51 _ The Creative Cloner AI Agent (by RoboNuggets).json`.

## n8n template
`R51_creative_cloner/R51 _ The Creative Cloner AI Agent (by RoboNuggets).json`

## Use case for Provinzial
Most directly useful for fast variation generation once a winning Provinzial creative is identified. Pair with [[../knowledge/tools_and_skills#ad-creative|ad-creative skill]] and [[../knowledge/tools_and_skills#ogilvy|ogilvy]] to keep variants on-brand.

## Related
- [[R46_ultimate_extract]]
- [[../frameworks/content_extraction_framework]]
- [[../clients/Provinzial_Geier_Ayhan/brand_brief]]


---

## Phase 6 final state (2026-05-13)

- **n8n workflow id:** `SmtkmTgfCTLZPlN4`
- **Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
- **Section:** §B @ canvas Y=[1540, 2640]
- **Webhook trigger:** `https://ops.getautomata.ai/webhook/r51` (writes to `PipelineRequests` table `tblLtTpXwFOpzDX4K`)
- **Notes:** KIE Suno music inline (TODO swap to Fal Lyria-2). Triggered by R46 winners.

---

## 2026-05-25 — `clone_status` Airtable error fixed (auto-clone branch parked)

**Symptom:** n8n logs throwing `INVALID_FILTER_BY_FORMULA: Unknown field names: clone_status` every ~5 min.

**Root cause:** The R46→R51 auto-clone branch was **parked-but-live**. It consists of:
- `[X] R46->R51 Schedule (5m)` (scheduleTrigger, id `d5733f86-...`) — fired every ~5 min.
- `[X] R46->R51 Find winners` (Airtable *search*, id `743deb09-...`) — formula `AND({days_on_air} > 7, {clone_status} = '')` against the **TikTok** table `tblrc4ILrLINc6rVy` (base `appC3HqG42ftswOvw`).

`clone_status` **does not exist** on the TikTok table — nor on any of the 8 R46 platform tables (Meta_Ads / TikTok / Instagram / YouTube_Longs / YouTube_Shorts / LinkedIn / Twitter / Reddit), which all share one schema: `keyword, …, days_on_air, page_name, followers, fb_page_likes, collation_count, is_active`. No rename candidate exists (`is_active` = ad still running, a different concept). So the field is **missing entirely** — it was a planned dedup marker that was never created.

The branch is also a **dead-end** (no downstream connection) and tagged `[X]` (operator's "parked / not-yet-wired" convention) — the sticky reads *"Wire output to R51 entry node OR call /webhook/r51. TODO."* So it was firing a doomed query whose results went nowhere.

**Fix applied:** Set `disabled:true` on both `[X]` executable nodes (schedule + Airtable). The `clone_status` formula is **preserved** (parked, not deleted) for when the branch is built out. Mechanism: direct REST verbatim round-trip (GET → flip 2 flags → PUT `name/nodes/connections/settings` byte-identical otherwise) — deliberately **not** the n8n-mcp partial diff, which re-sanitizes all 475 nodes and is the documented webhook/Telegram strip-bug path. Backup: `n8n_backups/SmtkmTgfCTLZPlN4_PRE-clone_status-fix_2026-05-25.json`.

**Verified:** workflow still `active=True`; node count 475 unchanged; strip-detection baseline intact (19 webhook/2 with path, 7 telegram/1 with operation); both nodes `disabled=True`; last error execution was id 723 @ 09:20:03Z (before the 09:22:45Z edit) — the 09:25 tick did not fire.

**To actually enable R46→R51 auto-clone later, the operator must:**
1. Add a `clone_status` field (single-select or text) to the R46 platform table(s) being watched — tracks whether a winning ad has already been cloned (blank = not yet cloned; the filter `{clone_status} = ''` picks unprocessed winners).
2. Wire `[X] R46->R51 Find winners` output → R51 entry node (or have it `POST /webhook/r51`).
3. Confirm the `Airtable PAT` credential binding.
4. Re-enable both `[X]` nodes (set `disabled:false`).
5. Have the clone path **write back** `clone_status` on processed rows, or the filter will re-select the same winners every tick.
