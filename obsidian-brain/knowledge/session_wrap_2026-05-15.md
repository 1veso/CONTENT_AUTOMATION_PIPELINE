# Session wrap — 2026-05-15

Heavy infra day. Five blocks of work landed; canvas + sub-workflows on Fal end-to-end; R61 gained opt-in narrative + B-roll + VFX + cross-platform layers.

## Recovery round (late session)

Sub-workflows lost their content (empty canvases) between the initial import and the later re-fetch — operator-side rollback or n8n save inconsistency, root cause not pinned down. **Re-import + redo of Blocks 2.5 / 2.6 / §H wiring** was needed:

1. **7 sub-workflows re-imported via `update_full_workflow`** with clean names (no "via Kie AI" suffix):
   - `IFbs9tznah16OT3d` → `🍳 Create Image (GPT-image-1)` (8 nodes)
   - `CCBQMbBdFaKG7qtP` → `🍳 Create Image (Nanobanana)` (8 nodes)
   - `xYmf9iyOXAcalnY4` → `🍳 Create Image (Seedream v4)` (8 nodes)
   - `UlfRzmG35nVdpQTO` → `🍳 Create Video (Veo3 I2V)` (8 nodes)
   - `MMppx9O228HCIEyx` → `🍳 Combine Clips (FFMPEG via Fal)` (8 nodes)
   - `cddGpaBUHEtZmX08` → `n21 - Bulk Runner` (6 nodes)
   - `RPnvHKTpdv7q0Z7v` → `n21 - UGC Creator` (29 nodes)
2. **KIE → Fal swap re-applied** on the 4 image/video subs (Create URL + body to Fal schema, Get URL drop `/status`, Switch on `$json.status`, Return reads `data.images[0].url` / `data.video.url`, `XCCrAcucNjypOTqE` credential bound). Veo3 I2V keeps `image_url` in body.
3. **§H executeWorkflow nodes re-added** on main canvas — the Block 3.A/3.B work had also been reverted; redone with fresh clean `cachedResultName` so n8n UI doesn't throw "Could not find property option".
4. **UGC Creator orchestrator (`RPnvHKTpdv7q0Z7v`) executeWorkflow IDs re-patched** — re-import restored the phantom IDs (`DaIbrXSzbXzzNEeT` etc.); patched back to live sub IDs + new `cachedResultName`.

**Test caveat:** `n8n_test_workflow` MCP only supports webhook/form/chat trigger types. Sub-workflows use `executeWorkflowTrigger` — cannot be live-tested via the API. Verified structurally instead: all 7 subs present, named correctly, with non-zero nodes and recent `updatedAt`. Live execution path is parent canvas → §H Switch → executeWorkflow → sub (cascades through real API calls, so untested until first paid run).

## What changed

### Canvas + sub-workflows (n8n)

- **n8n ↔ Modal tunnel wired** on `SmtkmTgfCTLZPlN4`. §T1 R57 webhook → HTTP-Modal R57 gen (fire-and-forget); §T2 R61 webhook → Switch on `body.stage` → voiceover/stitch/blotato endpoints. Shared Airtable-error sinks on both sections.
- **All 16 webhook node params re-armed.** n8n public PUT API had stripped `httpMethod/path/responseMode` from every `webhook` v2.1 node on the canvas. Restored via `updateNode` partial-diff; see [[webhook_registry]] warning callout.
- **§H orchestrator wired.** 5 TODO stickies replaced with real `executeWorkflow` nodes pointing at the 5 imported n21 sub-workflows. Switch[0/1/2] → image branches → Store Image; Filter → Call Create Video → Store Videos; Aggregate → Combine Clips → Final Video.
- **KIE → Fal migration complete** across:
  - R51 [B] Create Songs → `fal-ai/lyria2`
  - n16 [D] Create Video → `fal-ai/veo3/image-to-video`
  - n19 [G] Create Image → `fal-ai/nano-banana-pro/edit`
  - n19 [G] Create Video → `fal-ai/veo3/image-to-video`
  - sub `IFbs9tznah16OT3d` (GPT-image-1) → `fal-ai/nano-banana-pro/edit`
  - sub `CCBQMbBdFaKG7qtP` (Nanobanana) → `fal-ai/nano-banana-pro/edit`
  - sub `xYmf9iyOXAcalnY4` (Seedream) → `fal-ai/bytedance/seedream/v4/edit`
  - sub `UlfRzmG35nVdpQTO` (Veo3-fast → I2V) → `fal-ai/veo3/image-to-video`
  - Ultimate UGC Creator (`RPnvHKTpdv7q0Z7v`) executeWorkflow IDs patched to point at the new subs.
- Bodies rewritten to Fal schema, poll URLs dropped `/status` suffix, Switch/If routing rewritten to read `$json.status === "COMPLETED"`, result extraction reads `data.images[0].url` / `data.video.url` / `data.audio.url`.

### Imported sub-workflows (n21)

| ID | Name |
|---|---|
| `MMppx9O228HCIEyx` | 🍳 Combine Clips (FFMPEG via Fal AI) |
| `IFbs9tznah16OT3d` | 🍳 Create Image (GPT-image-1 via Kie AI) — now Fal nano-banana-pro |
| `CCBQMbBdFaKG7qtP` | 🍳 Create Image (Nanobanana via Kie AI) — now Fal nano-banana-pro |
| `xYmf9iyOXAcalnY4` | 🍳 Create Image (Seedream 4.0 via Kie AI) — now Fal seedream v4 |
| `UlfRzmG35nVdpQTO` | 🍳 Create Video (Veo3-fast via Kie AI) — now Fal veo3 image-to-video |
| `cddGpaBUHEtZmX08` | n21 - Bulk Runner for Ultimate UGC Creator |
| `RPnvHKTpdv7q0Z7v` | n21 - Ultimate UGC Creator (by RoboNuggets) |

### Python (R61 tools)

- `voiceover_gen.py` — `R61_NARRATIVE_MODE` env splits the cleaned + provinzial-rewritten script into Hook (0-3s), Problem (3-7s), Lösung (7-11s), CTA (11-15s) via Gemini Flash; TTSs each segment via ElevenLabs; ffmpeg-concat into a single MP3; writes the segment timing JSON to the new Airtable `Voiceover Segments` field. Single-segment fallback if split fails.
- `frame_gen.py` — `build_prompts()` now reads `Voiceover Segments` and incorporates Hook beat into the first-frame prompt and CTA beat into the last-frame prompt when narrative mode is on. Existing pillar-only path unchanged when flag off.
- `hf_stitch.py` — three new bottom-of-file functions, all opt-in via env flags, all fail-safe (never break the main render):
  - `add_broll_injection()` — `R61_BROLL_ENABLED`. Picks best-matching B-roll clip from `r2://r61/broll/<scenario>/` via OpenAI `text-embedding-3-small` cosine match. Splices a 3-7s overlay scene into `index.html` between Hook and Problem segments.
  - `add_vfx_transitions()` — `R61_VFX_ENABLED`. Injects a 100ms CSS opacity crossfade at every scene boundary.
  - `generate_platform_variants()` — `R61_PLATFORMS=tiktok,instagram_reels,…`. Renders 10 platform-specific crops (instagram_feed/reels, tiktok, facebook_feed/stories, linkedin, youtube/shorts, twitter, pinterest) via ffmpeg, uploads to `r61/final/<tag>/platforms/<platform>/<name>`, writes JSON map of URLs to the new Airtable `Platform Variants` field.

### Airtable schema

Two new Long-text fields on `tbl1hd8yprLTZia4c` (Video table, base `appC3HqG42ftswOvw`):
- `Voiceover Segments` — JSON array `[{name, text, start_s, end_s}, ...]` from narrative split.
- `Platform Variants` — JSON map `{platform: url}` from cross-platform render.

Both added via Airtable Meta API (PAT had `schema.bases:write`).

## Known carry-forward items

- **Sub-workflow downstream consumers** were rewritten by autonomous subagent passes — some Set/Return expressions may need manual verification in n8n UI. The high-confidence rewrites: Switch routing on `$json.status`, result extraction to `data.images[0].url` / `data.video.url`.
- **fal-ai/veo3/fast (text-to-video) → fal-ai/veo3/image-to-video (image-to-video)** swap re-introduced `image_url` in the body wherever a first-frame image is available upstream. If the upstream Get-Image expression resolves to a non-Fal shape, the I2V call will fail — needs a single canvas test.
- **`codegraph sync` failed** at end-of-session (database locked). Re-run when the lock clears.
- **Workflow `SmtkmTgfCTLZPlN4` is currently `active: false`** — operator deactivated to wire 3 §L2/§L3 telegram triggers in UI. Reactivate after that's done.
- **R61 production data is untouched.** All 30 records stay scheduled in Blotato; narrative/B-roll/VFX/platform features are opt-in and default off.

## Open items rolled into [[_index]] Next actions

- Re-deploy remaining 3 R61 HTTP endpoints (post-Modal-plan-upgrade)
- Schaden campaign kickoff (operator approval gates pending)
- Per-pipeline agents — host + system prompts + OpenClaw wiring

## Backups

`.bak.2026-05-15` copies of `voiceover_gen.py`, `frame_gen.py`, `hf_stitch.py` left alongside the live files for quick rollback.
