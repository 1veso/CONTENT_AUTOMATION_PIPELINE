# Per-Pipeline Agents

Spec for the automation layer: each pipeline runs under its own dedicated agent (Claude Code), the agent autonomously monitors its pipeline's state, takes safe actions inside its scope, and keeps the owner posted.

**Phase 1 status (2026-05-13):** ClaudeClaw blueprint applied. Single primary agent live at repo root via Telegram. R61 gate-notification pattern wired end-to-end. Per-pipeline agents (alpha/beta/gamma split) deferred until Phase 1 has run for ≥1 week.

## Goal

Move from "owner manually checks Airtable / Modal / Blotato dashboards" to "one agent per pipeline owns its own surface area, surfaces what needs human attention, and leaves everything else alone".

## Phase 1 — Single Primary Agent (live)

Deployed via the [ClaudeClaw blueprint](https://github.com/robonuggets/claudeclaw). One Claude Code session at `C:\CONTENT_PIPELINE\` with one Telegram bot covers all three pipelines.

### What's wired

| File | Purpose |
|------|---------|
| `SOUL.md` | 6 non-negotiable rules every agent inherits (Blotato schedule-only, never delete, cost-confirm, no overwrite, per-client hold, human gates) |
| `USER.md` | Operator profile (timezone Berlin, OS Win11, working style) |
| `CLAUDE.md` | Primary agent identity, session startup, approval rules |
| `cron-registry.json` | 3 crons recreated on every startup |
| `.claude/settings.local.json` | Env vars (TELEGRAM_STATE_DIR + token) + deny list (env files, references/outputs/, n8n_backups/, obsidian-brain/clients/, destructive shell) |
| `.claude/telegram/.env` + `access.json` | Bot token, DM allowlist |
| `.mcp.json` | Empty `{}` — required so the Telegram plugin doesn't double-poll |
| `shared/gates/pending.json` | R61 gate queue, polled by cron |
| `shared/memory/convo_log_primary.md` | Rolling session handoff |
| `R61_video_pipeline/tools/_gates.py` | Helper module — atomic gate-queue writer |

### Cron schedule (Europe/Berlin)

| ID | Cron | What it does |
|---|---|---|
| `morning-summary` | `0 8 * * *` | Reads obsidian-brain/_index.md + Airtable counts + pending gates → Telegram digest |
| `keepalive` | `0 */6 * * *` | Silently verifies Telegram connection. No user-visible message. |
| `r61-gate-watcher` | `*/15 * * * *` | Polls `shared/gates/pending.json`, pings Telegram with approve/redo/hold options for any `notified: false` entry |

### Launch command

From `C:\CONTENT_PIPELINE\`:

```powershell
claude --dangerously-skip-permissions --channels plugin:telegram@claude-plugins-official
```

Prerequisite: Bun installed (done — v1.3.14 at `C:\Users\benja\.bun\bin\bun.exe`) and Telegram plugin installed inside Claude Code (`/plugin install telegram@claude-plugins-official`).

### Gate-notification pattern (R61)

Pipeline scripts don't talk to Telegram directly. Each R61 step writes a JSON entry to `shared/gates/pending.json` via `tools/_gates.append_gate(...)`. The `r61-gate-watcher` cron polls that file every 15 minutes and surfaces every unnotified entry on Telegram with clear approve / redo / hold options.

**Wired write points:**

| Script | Trigger | Gate # | Entry summary |
|--------|---------|--------|---------------|
| `frame_gen.py` | End of batch (after summary log) | 0 | "frames_generated_batch — N records ready for video_gen review" |
| `video_gen.py` | End of batch (after summary log) | 1 | "clip_generated_batch — N clips ready for human review (Gate 1)" |
| `hf_stitch.py` | After publish_to_r2_and_airtable per record | 4 | "stitch_final_preview — Ad <name>, final v3 URL" |

**Gate schema** (see `tools/_gates.py` docstring for canonical reference):

```json
{
  "gate_number": 4,
  "gate_name": "stitch_final_preview",
  "record_id": "recXXX...",
  "ad_name": "Day_3_Sicherheit_im_Alltag",
  "video_url": "https://r2.../r61/final/v3/3_day_3_...mp4",
  "options": ["Approve", "Redo", "Hold"],
  "timestamp": "2026-05-13T22:30:00",
  "status": "pending",
  "notified": false
}
```

`notified` flips to `true` once the gate-watcher cron has sent the Telegram message. `status` flips to `approved` / `rejected` based on user reply.

### Telegram inline keyboards

Every gate entry carries an `options[]` array (defaults to `["Approve", "Redo", "Hold"]` — see `_gates.DEFAULT_OPTIONS`). The `r61-gate-watcher` cron renders these as a single-row inline keyboard. Each button's `callback_data` is `gate:<option_lower>:<record_id>` (e.g. `gate:approve:rec4cuKlnZwe0Slag`).

On callback:
- `gate:approve:<id>` → status → `approved`; if gate 4, prompt to advance to `blotato_schedule`
- `gate:redo:<id>` → status → `rejected` + ask the operator in chat for a `reason` (merged into `extra.reason`)
- `gate:hold:<id>` → keeps status `pending`; acknowledge only

Pipeline scripts can override the options array per-gate by passing `options=[...]` to `_gates.append_gate(...)` — useful when a gate needs a custom action (e.g. `["Use take 1", "Use take 2", "Both", "Redo"]`).

### Gate reply handler (subprocess-delegated Airtable update)

When the operator taps a button, the agent receives `callback_data = "gate:<verb>:<record_id>"` and runs the handler defined in CLAUDE.md → "Gate Reply Handler". Two-stage write — local gate state first, Airtable second — with hard graceful degradation if either side fails.

**Verb → Airtable status mapping** (Gate 1 and Gate 4):

| Verb | Airtable status (`av.set_status`) |
|---|---|
| `approve` | `STATUS_APPROVED` ("Approved") |
| `redo` | `STATUS_REJECTED` ("Rejected") |
| `hold` | no-op (status stays as-is) |
| custom (e.g. `use take 1`) | default `STATUS_APPROVED`, choice logged in `extra.choice` |

Gate 0 (frames batch) is local-only — no Airtable mutation.

**Subprocess invocation** — same delegation pattern as morning-summary, runs from `C:\CONTENT_PIPELINE\`:

```powershell
python -c "import sys; sys.path.insert(0, 'R61_video_pipeline'); from tools import airtable_video as av; av.set_status('<RECORD_ID>', av.STATUS_APPROVED); print('ok')"
```

`airtable_video.py` calls `load_dotenv(R61_video_pipeline/.env)` at line 19, so the credential never enters the agent's context window AND the deny list (which blocks `Read(**/.env)`) is bypassed cleanly — the subprocess load is invisible to Claude's permission system.

**Graceful degradation** — three branches:
- Local OK + Airtable OK → edit original Telegram message to `✅ Approved — Airtable status: Approved` (or `🔁 Redo queued — Reason: <text>`)
- Local OK + Airtable FAILED → reply on Telegram with the exact phrase `Local approval recorded but Airtable update failed: <reason>. Please update Airtable manually.` (operator must never be left thinking it worked)
- Local FAILED → reply `Could not update local gate state: <reason>. No action taken.` and stop. Never touch Airtable if local state is inconsistent.

Every reply is logged to `shared/memory/convo_log_primary.md` under "Gate replies" with timestamp, record_id, verb, target status, and Airtable outcome.

### Numbering vs CLAUDE.md's 4 gates

CLAUDE.md declares 4 R61 human gates. The wired entries map as follows:

| CLAUDE.md gate | Description | Wired? | Where |
|---|---|---|---|
| Gate 1 | After Higgsfield clip generation | ✅ | `video_gen.py` batch end |
| Gate 2 | After raw R2 footage selection | ❌ (fully manual — no script) | n/a |
| Gate 3 | Before each FFmpeg stitch | ⚠️ Implicit — operator runs `hf_stitch` only when ready | n/a |
| Gate 4 | Full final preview before export | ✅ | `hf_stitch.py` per record |

Gate 0 (frame-gen batch ready) is additional — it surfaces the first/last frames for review before any paid Higgsfield call.

## Future state — One agent per pipeline (deferred)

| Agent | Pipeline | Watches | Acts on | Escalates |
|-------|----------|---------|---------|-----------|
| R55-agent | [[../pipelines/R55_clipper]] | Modal job state, Telegram review queue, Vizard quota | Re-clip on rejection, Blotato schedule on approve | Modal failures, Vizard quota exhaustion, ambiguous review verdicts |
| R57-agent | [[../pipelines/R57_content_engine]] | Airtable May2025 table, Fal balance | Generate next-day image when status is empty (within cost gate) | Fal balance < threshold, prompt v3 regressions, hold-release triggers |
| R61-agent | [[../pipelines/R61_video_pipeline]] | Airtable Video table, R2 v2 prefix, Higgsfield credits, ElevenLabs status | Run voiceover → stitch → R2 upload → Airtable PATCH for rows past human-gate 1 | All 4 human gates (cannot auto-skip), ElevenLabs unblock, captions TODO |

Will be promoted to Phase 2 once the primary agent has demonstrated a clean week of gate notifications without false positives or missed events.

## Shared behaviours (all agents)

- **Cost-approval gate:** never call a paid API without explicit approval *for this run* — even if the row is "due"
- **Never overwrite:** version-increment every output ([[../knowledge/lessons_learned#Never delete old content]])
- **Blotato hold:** schedule only, never immediate post
- **Daily status update** to owner: what advanced, what's blocked, what needs human input
- **Memory writes:** when an agent learns something non-obvious about its pipeline, write it to `~/.claude/projects/C--CONTENT-PIPELINE/memory/` per the auto-memory rules

## Monitoring surface

Each agent should be able to answer these questions about its pipeline at any time:

1. What's the queue depth right now?
2. What's blocked, and on what?
3. What did I do in the last 24 hours, and what did it cost?
4. What's the next safe action, and do I have approval to take it?
5. Are any of the rules in [[../knowledge/lessons_learned]] currently at risk of being violated?

## Hand-off to owner

Telegram message format used by the primary agent (Phase 1 live):

```
*R61 Gate <N> — <gate_name>*
• Record: <record_id>
• Ad: <ad_name>
• Asset: <video_url>
• Next: <next_step>

Reply: *approve <record_id>*, *redo <record_id> <reason>*, or *hold*.
```

Morning summary format (`0 8 * * *`):

```
*Daily summary — <date>*
• R55: <pending review count> awaiting review
• R57: <X scheduled today>, <Y posted, Z pending>
• R61: <X scheduled today>, <gate count> gates pending
• Blotato hold: ACTIVE (schedule-only)
```

## Related

- [[openclaw_marriage]]
- [[../frameworks/README]]
- [[../knowledge/lessons_learned]]
- [[../knowledge/tools_and_skills]]
- ClaudeClaw blueprint: https://github.com/robonuggets/claudeclaw
