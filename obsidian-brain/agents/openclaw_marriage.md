# Claude Code + OpenClaw Integration Architecture

Spec for marrying Claude Code (reasoning + tool use + memory) with OpenClaw (autonomous browser / desktop actuation) so a per-pipeline agent ([[per_pipeline_agents]]) can take actions that the Claude Code tool surface alone cannot reach (Blotato dashboard, Modal UI, Higgsfield account, Telegram in cases without a bot, etc.).

## Why marry the two

| Need | Claude Code alone | OpenClaw alone | Both |
|------|-------------------|----------------|------|
| Read codebase / write files | ✅ | ❌ | ✅ |
| Call APIs (REST / SDK) | ✅ | ❌ | ✅ |
| Click through a vendor dashboard | ❌ | ✅ | ✅ |
| Multi-step reasoning, memory, skills | ✅ | ❌ | ✅ |
| Watch a video / read a screenshot for QA | partial (vision) | ✅ | ✅ |
| Comply with [[../knowledge/lessons_learned]] rules | ✅ (instructed) | ❌ (no concept of project rules) | ✅ |

## Architecture sketch

```
   ┌────────────────────────────┐
   │     Per-pipeline agent     │
   │  (Claude Code background)  │
   │                            │
   │   - reads Airtable / R2    │
   │   - calls Fal / Higgsfield │
   │   - writes memory          │
   │   - obeys cost gate        │
   │                            │
   │     ▼  dispatch to OpenClaw when:
   │       - dashboard-only action
   │       - vendor UI required
   │       - screenshot QA needed
   │                            │
   └────────────┬───────────────┘
                │
   ┌────────────▼───────────────┐
   │          OpenClaw          │
   │  (browser / desktop arm)   │
   │                            │
   │   - logs into Blotato      │
   │   - QA-reviews scheduled   │
   │     post on dashboard      │
   │   - reports back to CC     │
   └────────────────────────────┘
```

## Dispatch protocol

1. Claude Code agent decides an action requires actuation → emits a structured "OpenClaw task" (URL, goal, success criterion, screenshots to capture).
2. OpenClaw runs, returns: success bool, screenshots, raw transcript of actions taken.
3. Claude Code interprets the return, decides next step, updates Airtable / memory.

## Boundaries (DO / DON'T)

**OpenClaw DOES:**
- Verify a Blotato scheduled post exists on the dashboard (screenshot the entry)
- Check Higgsfield credit balance from the account page
- QA-watch a finished video on a vendor site
- Confirm a Modal job is green

**OpenClaw NEVER (without explicit owner approval):**
- Click "Post now" on Blotato (hold!)
- Top up Higgsfield / Fal credits
- Delete content
- Touch any account-level settings

These constraints mirror [[../knowledge/lessons_learned]] — OpenClaw inherits all of them.

## Memory bridge

Anything OpenClaw discovers (e.g., "Blotato post #X says Failed in dashboard") gets handed back to Claude Code and Claude Code decides whether to write it to memory per the auto-memory rules.

## Open questions

- Run OpenClaw locally (camofox-style browser) or hosted?
- How does the user approve OpenClaw actions in real time? Telegram one-click? CLI?
- Sandboxing: does OpenClaw run in a separate browser profile per pipeline?
- Audit log: every OpenClaw action recorded where? (Probably `obsidian-brain/agents/audit/` or an Airtable `Agent Actions` table.)

## Related

- [[per_pipeline_agents]]
- [[../knowledge/tools_and_skills]] — camofox is the closest existing tool to what OpenClaw provides
- [[../knowledge/lessons_learned]]
