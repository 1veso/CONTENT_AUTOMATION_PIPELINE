# n30 — Manual UI Patch (2 nodes, ~5 minutes)

**Why this doc exists:** the API-side patch is blocked by 30 pre-existing stale connection refs on canvas `SmtkmTgfCTLZPlN4` (telegramTrigger, googleGemini, n21 sub-workflows). See `MIGRATION_NOTES.md` for the full diagnosis. This is the safe path — direct UI edits, no `cleanStaleConnections` blast radius.

**Canvas:** https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4
**Section:** §I (n30 — Y range 9940..11140)

## Step 1 — Open the canvas and locate the two nodes

In the n8n UI, search the canvas (Cmd/Ctrl+F) for:

- `[I] Start frame 🍌` (node id `81355084-0111-4577-96ae-25fb8b86442b`, position `[-464, 10276]`)
- `[I] End frame 🍌` (node id `1d211c0c-4274-4f6b-b15f-5155e3532091`, position `[-304, 10276]`)

## Step 2 — Edit `[I] Start frame 🍌`

1. Double-click the node.
2. Change **URL** from:
   ```
   https://api.wavespeed.ai/api/v3/google/nano-banana-pro/edit
   ```
   to:
   ```
   https://queue.fal.run/fal-ai/nano-banana-pro/edit
   ```
3. Open the **Body Parameters / JSON** field. Find the key `"images"` and rename it to `"image_urls"`. Leave its value (array of URLs) untouched. Other body fields (`prompt`, `aspect_ratio`, `output_format`, `resolution`) stay as they are.
4. Under **Authentication**, set to **Generic Credential Type → Header Auth**.
5. Pick the Fal credential (re-use the same `httpHeaderAuth` credential id that any other §section's Fal HTTP node uses on this canvas — search the credential list for one named like `Fal Credentials` or with header `Authorization: Key ...`). If none exists yet, create one:
   - Name: `Fal Credentials`
   - Header Name: `Authorization`
   - Header Value: `Key {FAL_KEY}` where `{FAL_KEY}` is the value from `R57_content_engine/.env` or `R61_video_pipeline/.env`.
6. Click **Save**.

## Step 3 — Edit `[I] End frame 🍌`

Repeat Step 2 verbatim on this node. Same URL change, same `images` → `image_urls` rename, same credential binding.

## Step 4 — Test on a single record

1. Pick one Airtable row from the n30 table that has a `Start frame Prompt` and `End frame Prompt` ready.
2. Right-click `[I] Start frame 🍌` → **Execute Node**. Confirm it returns a Fal queue response (HTTP 200 with `request_id`, `status`, etc.).
3. Repeat for `[I] End frame 🍌`.
4. If both pass, the section is migrated.

## Step 5 — Activate the section

Once both nodes work in isolation, the existing downstream wiring (Wait → Get start frame → Log Images → Switch → Create Video → ...) is already in place and unchanged by this patch. No further edits required.

## Rollback

If anything breaks, the old WaveSpeed URL was `https://api.wavespeed.ai/api/v3/google/nano-banana-pro/edit` and the body field was `images` (plural, plain). Re-binding to the old WaveSpeed credential restores the prior behavior.

## Why not API-patch?

The MCP `n8n_update_partial_workflow` operation correctly applies the 4 `patchNodeField` operations, but n8n rejects the save because the canvas has 30 connection references to nodes that public-API workflow saves can't preserve (telegramTrigger, googleGemini, n21 sub-workflows — all documented TODO stickies). Cleaning those connections via `cleanStaleConnections` would wipe wiring that the operator needs to recreate by hand later. UI patch sidesteps all of that.

## Cost note

Fal `nano-banana-pro/edit` is ~$0.04/image (R57 COSTS table). WaveSpeed was ~$0.14/image. Net ~70% cheaper per render. Confirm before doing the n30 batch run.
