---
name: onboard
description: Onboard onto a project workspace — locate the project folder, read context, and ask clarifying questions until intent is clear before doing any work. Triggers on "/onboard [project name or ID]", "onboard [project]", "onboard me to [project]".
---

# Onboard

Get up to speed on a project before touching it. The goal is **clarity of intent before action** — load the workspace, then ask questions until you know exactly what the user wants out of this session.

Companion to the `coordinate` skill. Where `coordinate` creates and tracks the project, `onboard` is the "I'm joining a project mid-flight, catch me up" entry point.

## Trigger

- `/onboard [project name or ID]`
- "onboard [project]"
- "onboard me to [project]"

## Setup

Same root workspace as `coordinate` — projects live at `{WORKSPACE}/{ID}-{short-desc}/`. Replace `{WORKSPACE}` mentally with your actual root path.

## Step 1 — Find the project

**Resolution order:**

1. If the user gave an ID (matches `^[A-Z]-\d{4}$` or whatever convention you use), Glob `{WORKSPACE}/{ID}-*/**` and take the parent folder.
2. Otherwise, list directories in `{WORKSPACE}` and match by keyword (case-insensitive) against folder names.
   - **Use shell, not Glob, to list folders.** Glob returns *files*, so `*keyword*` only matches files whose names contain the keyword — it misses folders whose names contain it but whose files don't. The bare `*` Glob also truncates on busy folders and silently drops folders.
   - Command: `ls -d {WORKSPACE}/*/ 2>/dev/null` (or PowerShell `Get-ChildItem -Directory`). Then filter folder names client-side for each keyword from the user's request.
   - Match logic: split the phrase into significant words (drop stopwords like "project", "on", "the"), require at least one to appear in the folder name. Score by number of matching words.
3. If multiple folders match, list the top candidates with their match scores and ask which.
4. If you have a task list elsewhere, look up the name there to find the ID, then re-check Step 1. If still nothing, say so and offer to invoke coordinate to create the project.

**Sanity check before saying "not found":** if your search returned zero hits but the topic feels like it should exist, re-list the directory directly and eyeball it. A truncated Glob result is a silent failure mode — don't trust an empty result without verifying the dir was actually fully enumerated.

## Step 2 — Read what's there

Read in this order, whichever exist:

1. `context.md` — what we're building, current phase, decisions, open questions
2. `session-log.md` — last few entries (most recent work)
3. Any obvious top-level docs (README.md, posts.md, notes.md)

Do **not** read the whole tree. Just enough to understand state.

## Step 3 — Brief the user (one short message)

In 3-5 bullets:
- What the project is (one line)
- Current phase / status
- Last session: what got done
- What's open or blocked

Keep it tight. The user knows the project — they want to confirm you do too.

## Step 4 — Ask clarifying questions until intent is clear

This is the whole point. Do **not** start work after the brief. Ask questions.

Cover whichever of these are unclear:

- **Scope:** What are we doing today specifically? One thing or several?
- **Output:** What does "done" look like for this session? A draft, a decision, a file shipped, a post?
- **Constraints:** Time pressure? Anything we must avoid? Approval needed before publishing?
- **Inputs:** Is there a doc, link, image, or transcript I should read first?
- **Audience / voice:** If it's content — who's it for, what's the energy?

**Format:** ask 2-4 questions max in one message. Don't interrogate. If most of it is obvious from context, ask only the one or two things you genuinely need.

If everything is obvious, say so and confirm: "Looks like the next move is X — confirm and I'll start." Wait for the green light.

## Step 5 — Hand off to work

Once intent is clear, proceed. If the project has full `coordinate` structure, append a session-log entry when meaningful work happens (per that skill's rules).

## Rules

- Never start the work in the same message as the brief. Brief → questions → wait.
- If the project folder doesn't exist, don't silently create it — surface it and offer `coordinate`.
