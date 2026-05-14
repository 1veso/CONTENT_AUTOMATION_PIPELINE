# Webhook Registry — GetAutomata_W01-W05 Content Pipeline

**Target canvas:** `SmtkmTgfCTLZPlN4` at `https://ops.getautomata.ai`
**Status:** WIRED. 16 webhooks deployed in Phase 5 (2026-05-13). All write to `PipelineRequests` (`tblLtTpXwFOpzDX4K`) on base `appC3HqG42ftswOvw`.

Each webhook chain on the canvas is `[Webhook] -> [Set: pipeline_id, params, status=Pending, webhook_id=$execution.id] -> [Airtable Create on PipelineRequests] -> [RespondToWebhook: {webhook_id, pipeline, status}]`.

The respond is immediate; pipeline body work happens after. Operator wires the body (`Set` or final `Respond` output → existing pipeline entry node) per pipeline.

## Registry

| Pipeline | URL | Section | Body params (JSON) |
|---|---|---|---|
| R46 Extract | https://ops.getautomata.ai/webhook/r46 | §A | `platform`, `keyword` |
| R51 Clone | https://ops.getautomata.ai/webhook/r51 | §B | `source_url`, `brand` |
| R34 VeoRobo | https://ops.getautomata.ai/webhook/r34 | §C | `niche`, `platform` |
| n16 Extend Video | https://ops.getautomata.ai/webhook/n16 | §D | `video_url`, `target_length` |
| n16.1 Auto Subtitles | https://ops.getautomata.ai/webhook/n16-1 | §E | `video_url`, `language` |
| R39 Bulk Images | https://ops.getautomata.ai/webhook/r39 | §F | `product_image_url`, `ad_count` |
| n19 Video Ads | https://ops.getautomata.ai/webhook/n19 | §G | `product_image_url`, `platform` |
| n21 UGCs | https://ops.getautomata.ai/webhook/n21 | §H | `product`, `character` |
| n30 3D Product | https://ops.getautomata.ai/webhook/n30 | §I | `product_image_url` |
| n31 Camera Motion | https://ops.getautomata.ai/webhook/n31 | §J | `product_image_url`, `motion_style` |
| n3 Voiceover | https://ops.getautomata.ai/webhook/n3 | §K | `video_url`, `script`, `language` |
| n29 Sora (TikTok→Sora) | https://ops.getautomata.ai/webhook/n29-sora | §L1 | `tiktok_url` |
| n29 Long (YT Long→LI/X) | https://ops.getautomata.ai/webhook/n29-long | §L2 | `youtube_url` |
| n29 Short (YT Short→Script) | https://ops.getautomata.ai/webhook/n29-short | §L3 | `youtube_short_url` |
| R57 Content Engine | https://ops.getautomata.ai/webhook/r57 | T1 | `niche?`, `count?` (writes to `tblnpiwNYF3zJXm9Q` for R57 Python to poll) |
| R61 Video Pipeline | https://ops.getautomata.ai/webhook/r61 | T2 | `idx`, `pillar` (writes to `tbl1hd8yprLTZia4c` for R61 Python to poll) |

## `PipelineRequests` Airtable table — DEPLOYED

- **Base:** `appC3HqG42ftswOvw`
- **Table ID:** `tblLtTpXwFOpzDX4K`
- **URL:** https://airtable.com/appC3HqG42ftswOvw/tblLtTpXwFOpzDX4K

| Field | Type |
|---|---|
| `pipeline_id` | Single line text (primary) |
| `params` | Long text (JSON) |
| `status` | Single select (Pending, Running, Done, Failed) |
| `webhook_id` | Single line text |
| `result_url` | URL |
| `error` | Long text |

(`created_at` was requested but Airtable Meta API rejects createdTime field creation; add manually in UI if needed, or use Airtable record `createdTime` automatic field.)

## Phase 5 cross-pipeline wiring deployed

- **R46 → R51 auto-clone**: Schedule (5min) + Airtable search (TikTok days_on_air > 7, clone_status empty) + sticky pointing to R51 entry. Operator wires `Find winners` → R51 main flow.
- **n3 voiceover routing gate**: sticky placed at Y=12100 documenting Switch on `add_voiceover` flag after R34/R51/n19.
- **n29 quality gate**: sticky at Y=13200 documenting Gemini-scored quality_score >= 7 threshold before Blotato.
