---
name: coordinate
description: Cross-session project coordination. Loads or creates a shared project workspace at {WORKSPACE}/projects/{ID}-* so all sessions share context, decisions, and output. Triggers on "/coordinate [ID]", "coordinate [ID]", "load project [ID]", "pick up [ID]".
---

# Coordinate

Cross-session project coordination. When invoked, loads or creates a shared project workspace so all sessions working on the same project share context, decisions, and output.

## Trigger

- `/coordinate [ID]`
- "coordinate [ID]"
- "load project [ID]"
- "pick up [ID]"

## Setup

Pick a root workspace folder on your machine — this is where all coordinated projects will live. Examples: `~/projects/`, `~/.claude/projects/`, or your own convention. Set it once and stick with it.

Throughout this skill, `{WORKSPACE}` refers to that root path. Replace mentally with your real path.

Folder naming inside `{WORKSPACE}`: `{ID}-{short-desc}` — e.g. `proj-046-launch-email`, `proj-101-website-redesign`. Use whatever ID scheme works for you (numeric, ticket, slug — the skill doesn't care).

Short desc: lowercase, hyphen-separated, 2-4 words max. Derived from the project name or what the user tells you.

## Lite mode

If the user says **"lite"**, **"light"**, or **"lite project"** in the invocation (e.g. "make a lite project for X", "lite coord for Y"), use the lighter-weight structure:

- Create **only** `context.md` (no `session-log.md`)
- `context.md` is the single source of truth — goals, candidates, decisions, and short session notes at the bottom
- Skip the separate session log ceremony — append brief "Session Notes" bullets at the bottom of context.md
- Good for: shopping research, gear picks, quick investigations, one-off decisions
- Bad for: multi-day builds, anything with code, anything needing handoffs

Lite `context.md` template:

```markdown
# [ID] — [Name] (lite project)

**Created:** [date]
**Status:** [Research / Deciding / Done]
**Use case:** [one sentence]

## Leaning
[current best option + 1-line why]

## Candidates
[table or short list]

## Decision Criteria
[bulleted]

## Recommendation
[your pick + fallback]

## Open Questions
- [anything unresolved]

## Session Notes
- [date]: [what happened]
```

Full mode (below) is the default when "lite" is not specified.

---

## Step 1 — Parse the project

Extract the ID from the user's message. IDs are an arbitrary convention — use whatever scheme you want (numeric, ticket prefix, slug).

If no ID is given, ask: "Which project? Give me the ID or name."

If you have a backlog or task list, look up the full name there to derive the short desc. Otherwise, ask the user for a 2-4 word name.

---

## Step 2 — Check if folder exists

Check for `{WORKSPACE}` — if the directory doesn't exist yet, create it.

Then check for a folder matching `{ID}-*` inside it.

**If folder exists → Load mode**
**If no folder → Create mode**

---

## Step 3A — Load mode

Read the following files in order:

1. `context.md` — what we're building, current status, decisions made
2. `session-log.md` — last 20 entries (most recent work)

Summarize in 3-5 bullet points:
- What the project is
- Current status / phase
- Last session: what was done
- What's pending or blocked
- Any open decisions

Confirm: "Loaded [ID]. Here's where we are: [summary]. What are we doing today?"

---

## Step 3B — Create mode

1. Create the folder: `{WORKSPACE}/{ID}-{short-desc}/`

2. Create `context.md` with this structure:

```markdown
# [ID] — [Full project name]

**Created:** [date]
**Status:** In Progress

## What We're Building

[Ask the user to describe the project goal in 1-3 sentences, or infer from the request. Fill this in.]

## Current Phase

[e.g. Planning / Scaffolding / Building / Testing / Done]

## Key Decisions

- [date] — [decision made]

## Architecture / Structure

[Fill in as it develops]

## Open Questions

- [anything unresolved]
```

3. Create `session-log.md` with this structure:

```markdown
# Session Log — [ID]

---

## [date] — Session 1

**Goal:** [what the user said we're doing today]
**Done:** 
**Decisions:** 
**Next:**

---
```

4. Confirm: "Created project workspace for [ID] at {WORKSPACE}/[folder-name]/. What are we building?"

---

## Step 4 — Stay in coordination mode

While working on the project:

**Proactive writes — do these automatically, no need to ask:**

- After any meaningful chunk of work, append a new session entry to `session-log.md`
- When a key decision is made, append it to the "Key Decisions" section in `context.md`
- When phase changes, update "Current Phase" in `context.md`
- When new files are created, note them in `context.md` under Architecture/Structure

**Session log entry format:**

```markdown
## [date] — Session [N]

**Goal:** [what we set out to do]
**Done:** [what was actually completed — be specific, include file paths]
**Decisions:** [any choices made, with brief rationale]
**Next:** [what's left, what the next session should pick up]

---
```

**Conflict handling:**
- For session-log.md: always append, never overwrite. No conflict possible.
- For context.md: if you detect it was recently modified by another session (check updated date), read it fresh before writing. If there's a genuine conflict (two sessions changed the same field), surface it to the user and ask which to keep.

---

## Step 5 — Output artifacts

All files built as part of the project go in the project folder or a subfolder:

- `{WORKSPACE}/{ID}-{short-desc}/` — project root
- Subfolders as needed: `scripts/`, `assets/`, `src/`, `output/`

When creating files, always use the project folder as root.

---

## Rules

- Never recreate a folder that already exists — always check first.
- Keep context.md concise. It's a living doc, not a diary. session-log.md is the diary.
- After loading, always confirm before diving into work.

## Itinerary / Trip-Planning Rules

- **Day-bloat check:** When suggesting additions to an itinerary day that already has 8+ stops, proactively flag time pressure and offer to thin existing stops before adding more. Realistic max for a single packed day is 7-8 actually-experienced stops; everything beyond is aspirational.
- **No proactive logistics removal on revision:** When the user revises an itinerary, re-verify ALL transit/logistics for adjacent days before claiming any element is "no longer needed." Don't proactively tell the user a transit option is unnecessary — let them lead removals. If they revise one day, check whether the removed activity was load-bearing for another day's logistics first.
