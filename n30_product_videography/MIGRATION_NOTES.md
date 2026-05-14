# n30 — WaveSpeed → Fal migration

**Date:** 2026-05-14
**Status:** Local JSON migrated. Live canvas patch BLOCKED (see below).

## What changed in `n30 _ Product Videography (by RoboNuggets) (1).json`

The 2 HTTP nodes that called the Nano Banana Pro `edit` endpoint:

| Node | Field | Before | After |
|------|-------|--------|-------|
| `Start frame 🍌` | `parameters.url` | `https://api.wavespeed.ai/api/v3/google/nano-banana-pro/edit` | `https://queue.fal.run/fal-ai/nano-banana-pro/edit` |
| `Start frame 🍌` | `parameters.jsonBody` | `"images": [...]` | `"image_urls": [...]` |
| `End frame 🍌` | `parameters.url` | (same WaveSpeed URL) | (same Fal URL) |
| `End frame 🍌` | `parameters.jsonBody` | `"images": [...]` | `"image_urls": [...]` |
| both | `credentials.httpHeaderAuth.name` | `WaveSpeed Credentials` | `Fal Credentials ... TODO operator: re-bind in UI` |

The Fal `nano-banana-pro/edit` endpoint uses the field name `image_urls` (not `images`); the request body otherwise stays the same shape (`prompt`, `aspect_ratio`, `output_format`, `resolution`).

## Operator next steps

1. **Re-bind the credential** for both `[I] Start frame 🍌` (`81355084-…`) and `[I] End frame 🍌` (`1d211c0c-…`) to a Fal `httpHeaderAuth` credential in the n8n UI:
   - Header name: `Authorization`
   - Header value: `Key {FAL_KEY}` (from `R57_content_engine/.env` or `R61_video_pipeline/.env`)
   - n8n credential id can be the same shape as the existing Fal credentials used by other §sections of the canvas. Per `CLAUDE.md`, operator-bound credentials always live UI-side; never PUT via API.

2. **Verify response shape** — Fal's queue.fal.run sync responses use a slightly different envelope than WaveSpeed (`status`, `output`, etc.). Confirm the downstream `Wait` and image-output extraction still works on a single test run before turning the section back on.

3. **Cost**: Fal `nano-banana-pro/edit` is roughly $0.04/image (per `R57_content_engine/tools/config.py` COSTS table). The previous WaveSpeed pricing was $0.14/image per the cost-breakdown note. Net win: ~70% cheaper per generation.

## Why the live canvas patch is parked

The n8n MCP `n8n_update_partial_workflow` validate-then-save protocol refused to save the migrated nodes. The 4 `patchNodeField` operations themselves are valid (n8n MCP reported `operationsApplied: 4`), but the canvas already has 30 structural errors — connections referencing nodes that don't exist:

- `[B] Analyze video`, `[J] Analyze image`, `[I] Analyze image` (the `googleGemini` LangChain node — n8n's public API rejects this type per CLAUDE.md compatibility caps)
- `[F]/[G]/[L1]/[L2]/[L3] Telegram Trigger` (telegramTrigger can't be PUT via public API)
- `[H] Seedream 🎵`, `[H] Nanobanana 🍌`, `[H] ChatGPT 🌀`, `[H] Combine Clips`, `[H] Call Create Video` (n21 sub-workflows that are documented TODO stickies in the merge log)

These are pre-existing issues from the May 13 merge, not introduced by this migration. Until those connection refs are cleaned (either by deleting the stale connections or re-creating the nodes via the UI), the API-side save will keep refusing.

**Recovery options** the operator can pursue in priority order:

1. **Open the canvas in the UI** and manually update the 2 HTTP nodes with the URL + body changes shown above (15-minute job). Skip the API-side patch entirely.
2. **Apply `cleanStaleConnections` op** via n8n MCP to drop the 30 broken connection refs, then re-run the partial diff. Risk: the canvas's intended wiring would have to be restored later when the affected nodes (telegramTrigger, googleGemini, etc.) are re-created in the UI.
3. **Wait for a full UI pass** that recreates the missing nodes (the documented `telegramTrigger` + LangChain Gemini caps are blockers that need UI binding regardless), then re-attempt the API patch.

Recommended: option 1 for n30 specifically, since it's only 2 nodes. The wider cleanup is a separate task.
