# n8n ↔ Modal tunnel — blocker note

**Status:** Not wired. Documented 2026-05-14. Operator decision required before any change.

## What was requested

Update n8n webhook nodes on canvas `SmtkmTgfCTLZPlN4` so `/webhook/r57` and `/webhook/r61` call the Modal endpoints:
- `https://hello-58046--r57-content-engine-generate-images-http.modal.run`
- `https://hello-58046--r57-content-engine-schedule-blotato-http.modal.run`
- `https://hello-58046--r61-video-pipeline-hf-stitch-http.modal.run`
- `https://hello-58046--r61-video-pipeline-voiceover-gen-http.modal.run`
- `https://hello-58046--r61-video-pipeline-blotato-schedule-http.modal.run`

## Why it can't be a URL patch

The current T1/T2 chains on the canvas (Phase 5 wiring, 2026-05-13) are:

```
[T1] WH R57       (n8n-nodes-base.webhook, inbound POST)
  → [T1] WH-Set R57       (set pipeline_id, params, status=Pending, webhook_id=$execution.id)
  → [T1] WH-Log R57       (Airtable create on tblLtTpXwFOpzDX4K)
  → [T1] WH-Respond R57   (responds {webhook_id, pipeline, status})
```

T2 (R61) has the identical shape. The webhook nodes are **receivers** — their "URL" is the path n8n exposes to the outside world (`ops.getautomata.ai/webhook/r57`). They do not carry an outbound URL that could be repointed at Modal.

The original design (CLAUDE.md): "writes PipelineRequests; R57 Python polls" — n8n only logs the request to Airtable, and the R57/R61 pipeline poller picks it up and runs locally. Now that R57 + R61 are Modal-deployed, the poller half can be replaced by a direct call.

## Correct fix — add HTTP Request nodes (production change)

Add one `n8n-nodes-base.httpRequest` node downstream of each `WH-Log` node, between `WH-Log` and `WH-Respond`:

| Chain | New node | Method | URL | Body |
|---|---|---|---|---|
| T1 (R57) generate | `[T1] HTTP-Modal R57 gen` | POST | `https://hello-58046--r57-content-engine-generate-images-http.modal.run` | `{ "record_ids": null, "dry_run": false }` |
| T1 (R57) schedule | (second branch off WH-Log if needed) | POST | `https://hello-58046--r57-content-engine-schedule-blotato-http.modal.run` | `{ "record_ids": null, "dry_run": false }` |
| T2 (R61) stitch | `[T2] HTTP-Modal R61 stitch` | POST | `https://hello-58046--r61-video-pipeline-hf-stitch-http.modal.run` | `{ "all_voiceover_done": true }` |
| T2 (R61) voiceover | (branch) | POST | `https://hello-58046--r61-video-pipeline-voiceover-gen-http.modal.run` | `{ "record_id": "{{$json.record_id}}", "confirm": "go" }` |
| T2 (R61) blotato | (branch) | POST | `https://hello-58046--r61-video-pipeline-blotato-schedule-http.modal.run` | `{ }` |

R57 endpoints take 1-2 minutes; R61 hf_stitch can take 30+ minutes. Either:
- Use `responseMode: "lastNode"` and let n8n hold the connection (works for R57; risky for R61)
- Use the current `RespondToWebhook` pattern + fire-and-forget the HTTP call asynchronously (preferred — R57/R61 Modal jobs already write completion back to Airtable, so n8n doesn't need to wait)

## Why this needs operator approval, not autonomous patching

- The canvas is **production-active** (460 nodes, ACTIVE, serving 16 webhook chains).
- The request shape — which Modal endpoint to fire for each inbound webhook payload — is a routing decision the operator owns.
- The body params need to come from somewhere — the inbound webhook payload, a fixed config, or via Airtable lookup. Each option has different failure modes.
- The R57 inbound webhook today carries `niche?` and `count?` per the registry; the Modal endpoint takes `record_ids` and `dry_run`. There is no defined mapping yet.
- Long-running R61 jobs (stitch) interact with the existing R61 human gates — direct HTTP firing may bypass gates that the operator wants to preserve.

## Recommendation

1. Operator confirms the payload-mapping contract (inbound webhook body → Modal endpoint body).
2. Operator confirms async (fire-and-forget) vs sync (wait) per endpoint.
3. Once agreed, partial-diff patch via `n8n_update_partial_workflow` operations: `addNode` (HTTP Request) + `removeConnection` (WH-Log → WH-Respond) + `addConnection` (WH-Log → HTTP Request → WH-Respond), executed atomically.

## Live Modal endpoints (for reference)

Verified responsive 2026-05-14:

```
POST https://hello-58046--r57-content-engine-generate-images-http.modal.run
POST https://hello-58046--r57-content-engine-schedule-blotato-http.modal.run
POST https://hello-58046--r61-video-pipeline-voiceover-gen-http.modal.run
POST https://hello-58046--r61-video-pipeline-hf-stitch-http.modal.run
POST https://hello-58046--r61-video-pipeline-blotato-schedule-http.modal.run
```
