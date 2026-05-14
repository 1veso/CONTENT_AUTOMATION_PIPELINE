# {{CLIENT_NAME}} — Campaign Log

One row per scheduled piece of content. Keep in chronological order by Scheduled Date.

| idx | Pillar | Scheduled | Status | Asset | Airtable | Notes |
|----:|--------|-----------|--------|-------|----------|-------|
| 1 | {{pillar}} | YYYY-MM-DD HH:MM | Pending / Generated / Scheduled / Posted | [link]({{r2 or local}}) | [rec...]({{airtable url}}) | {{any}} |
| 2 |  |  |  |  |  |  |

## Status legend
- **Pending** — record exists, no asset yet
- **Generated** — asset rendered, awaiting human gate
- **Approved** — passed gate, ready to schedule
- **Scheduled** — submitted to Blotato with `scheduledTime`
- **Posted** — confirmed live on platform
- **Held** — paused (per-client posting hold or quality issue)

## Hold state
{{ACTIVE / LIFTED — date and reason}}
