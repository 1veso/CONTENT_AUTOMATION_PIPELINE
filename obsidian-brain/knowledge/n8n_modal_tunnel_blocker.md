# n8n ↔ Modal tunnel — blocker note

**Status:** Wired 2026-05-15 — see "Wiring as built" section at bottom. Historical context below preserved for reference.

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


## Wiring as built — 2026-05-15

Wired in two partial-diff patches against `SmtkmTgfCTLZPlN4`. Operator decisions captured up-front: strict per-endpoint payload mapping, fire-and-forget (HTTP after `WH-Respond`), R61 routed by a Switch on inbound `body.stage` to preserve human gates.

### §T1 R57 — `/webhook/r57`

```
[T1] WH R57 → WH-Set → WH-Log → WH-Respond → [T1] HTTP-Modal R57 gen (POST)
                                                  └─ (error) → [T1] HTTP-Err R57 (Airtable status=Failed)
```

- **HTTP node:** `[T1] HTTP-Modal R57 gen` — POST `https://hello-58046--r57-content-engine-generate-images-http.modal.run`, body `{record_ids: null, dry_run: false}`, `onError: continueErrorOutput`, timeout 300000ms.
- **Error handler:** `[T1] HTTP-Err R57` — Airtable create on `tblLtTpXwFOpzDX4K` carrying `pipeline_id` + `webhook_id` from WH-Set, `status: Failed`, `params: JSON.stringify({error, endpoint, status_code, body})`.

### §T2 R61 — `/webhook/r61`

```
[T2] WH R61 → WH-Set → WH-Log → WH-Respond → [T2] HTTP-Switch R61 ─┬─ stage=voiceover → [T2] HTTP-Modal R61 vo
                                                                    ├─ stage=stitch    → [T2] HTTP-Modal R61 stitch
                                                                    └─ stage=blotato   → [T2] HTTP-Modal R61 blotato
                                                                                                │
                                                                                                └─ (any error) → [T2] HTTP-Err R61
```

- **Switch:** `[T2] HTTP-Switch R61` (typeVersion 3.2, rules mode) — three string-equals rules on `={{ $('[T2] WH R61').item.json.body.stage }}`, outputs labelled `voiceover` / `stitch` / `blotato`. Missing/unmatched `stage` => no Modal call (n8n drops the item).
- **HTTP nodes** (all `onError: continueErrorOutput`, timeout 300000ms):
  - `[T2] HTTP-Modal R61 vo` → `voiceover-gen-http.modal.run`, body `{record_id: {{ body.record_id }}, confirm: "go"}`
  - `[T2] HTTP-Modal R61 stitch` → `hf-stitch-http.modal.run`, body `{all_voiceover_done: true}`
  - `[T2] HTTP-Modal R61 blotato` → `blotato-schedule-http.modal.run`, body `{}`
- **Error handler:** `[T2] HTTP-Err R61` — shared sink for all three; records the originating endpoint via `endpoint: 'r61-' + body.stage`.

### Gates preserved

The Switch routing means the caller chooses which R61 stage runs. R61 human gates (Gate 1 clip review, Gate 3 pre-stitch, Gate 4 final preview) are unaffected — operator still controls which `stage` to POST, exactly as before. Blotato `scheduledTime`-only convention is enforced inside `blotato_schedule.remote(...)` itself, not at the n8n layer.

### Airtable PipelineRequests rows

A successful Modal call produces only the original `status=Pending` row from `WH-Log`. The Modal job is expected to update Airtable on completion (per each pipeline's own write-back). A Modal HTTP error produces a second row with `status=Failed` and `params` carrying error context — match the two rows by `webhook_id`.

### R57 scheduling endpoint

The `r57-content-engine-schedule-blotato-http.modal.run` endpoint is **not** wired to `/webhook/r57`. R57 scheduling is driven by the morning cron / direct `modal run` invocation, not by a webhook trigger. If you later need to expose it, add a sibling Switch on `body.stage = schedule` in T1 mirroring the T2 pattern.
