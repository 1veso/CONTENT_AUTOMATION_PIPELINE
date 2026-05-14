---
name: calibrate
description: In-session self-improvement. Reviews the current conversation for corrections, preferences, and patterns, then suggests specific skill/setup updates. Triggers on "calibrate", "what can you improve", "update your skills", "what did we learn", "tune up". Lite mode: "calibrate lite" or "/calibrate lite" — fast 1-3 suggestion sweep for shorter sessions.
---

# Calibrate: In-Session Self-Improvement

## What This Does

Reviews the current conversation and suggests specific updates to skills, CLAUDE.md rules, memory, or workflows based on what just happened. The user picks which suggestions to apply.

## Two modes

- **Full (default)** — deep scan of the whole conversation, max 7 suggestions, includes the auto project-log suggestion. Use at end of long sessions or after multiple corrections.
- **Lite** — triggered by `calibrate lite` or `/calibrate lite`. Fast 1-3 suggestion sweep for shorter sessions. Skips the project-log auto-include. Skips deep pattern matching. Just surfaces the loudest 1-3 things from the most recent 10-20 turns. ~80% fewer tokens.

If a lite sweep returns "nothing to calibrate", that's a valid output — say so in one line and stop.

## When to Use

- End of a work session
- After a task with multiple corrections
- When the user says "calibrate", "what can you improve", "tune up", "update your skills"

## Lite mode shortcut

If trigger is `calibrate lite` / `/calibrate lite`:

1. Scan only the last 10-20 turns (not the whole session)
2. Look for at most 3 things — corrections that happened, preferences revealed, repeated patterns
3. Skip auto project-log suggestion (lite is for in-session quick tuning, not project handoff)
4. Output max 3 numbered suggestions in the same `[TARGET: file] — [what]` format
5. If nothing meaningful surfaced: respond `Clean — nothing to calibrate` in one line. Don't pad.

Lite is the right call when:
- Session was short (under ~20 turns)
- Most of the work was unmemorable (routine queries, lookups)
- You just want a quick "anything I should fix?" without a deep audit

## Process

### Step 1: Scan the Conversation

Review everything in the current session. Look for:

- **Corrections** — where the user said "no", "wrong", "not that", "I meant X"
- **Preferences revealed** — format choices, tone adjustments, workflow preferences
- **Process gaps** — steps you missed that a skill should encode
- **Repeated patterns** — same type of correction more than once = systemic issue
- **Things that worked** — approaches the user confirmed or accepted without pushback

### Step 2: Match to Updateable Targets

For each finding, identify WHERE the fix belongs:

- **Skill file** — if the issue is about how a specific task is executed
- **CLAUDE.md** — if the issue is about general agent behavior or rules
- **Memory** — if it's a preference or context that should persist across sessions
- **Workflow/cron** — if it's about when or how automated tasks run
- **Style guide** — if it's about tone or writing style

### Step 3: Present Suggestions

**Output format — use this exact structure (Markdown, not plain text):**

Open with a bolded header: **Session calibration — N suggestions:**

Then for each suggestion, use this template:

```
**[number]. [TARGET CATEGORY]: [filename] — [bolded short summary of the change]**
[One full sentence explaining the specific change to make.]
*Why:* [Brief reason — the pattern that triggered this.]
```

Example output:

```
**Session calibration — 3 suggestions:**

**1. SKILL: title-writing — Add upfront signal on thumbnail generations**
State which style you're pulling from at the top of every thumbnail gen response.
*Why:* I freelanced thumb gens without naming the style. You caught me with "what skill did u use?"

**2. MEMORY — Save "Interactive Review HTML pattern"**
Add a reference note documenting the comments-textarea + tri-state checkbox + clipboard export pattern.
*Why:* Pattern emerged twice this session and worked both times. Worth lifting from one-off to reusable.

**3. CLAUDE.md — Add a rule under Red Lines**
Append a one-line rule about not suggesting handoffs to other agents.
*Why:* You corrected me when I suggested handing work off.
```

**Format rules:**
- Each suggestion's summary line (after the target) must be **bolded** — that's the scannable headline
- Use horizontal rule `---` after the last suggestion, then the "Which to apply?" prompt
- Close with: `Which to apply? \`all\` / \`do 1, 3\` / \`skip 2\` etc.`

**Language rule (MANDATORY — default for every calibrate output):**

Write every suggestion in **plain 3rd-grade English**. Short sentences. Simple words. One idea per sentence. Talk like a normal person, not a tech essay.

- ✅ "The skill says use Tool X. That is wrong. Change it to Tool Y."
- ❌ "Update Step 7 to point to Tool Y as the canonical provider, replacing the deprecated Tool X reference."

- ✅ "User asked for this today. They want to type and delete freely. Worth saving so the next session does it from the start."
- ❌ "Encode this preference as a reference memory so future sessions inherit the editable-textarea behavior by default."

This rule applies to the `[bolded short summary]`, the `[one full sentence]` explanation, AND the `*Why:*` line. No jargon. No "encode", "canonical", "deprecated", "leverage", "surface", "propagate". Use "save", "right", "old", "use", "show", "spread" instead. If a 3rd-grader couldn't read the suggestion out loud and roughly get it, rewrite it.

**Why this rule exists:** Calibrate is a fast-scan tool — the user reads the list, picks `do 1, 3`, moves on. Dense tech-writing forces them to translate before they can decide. Plain English makes the call instant.

Rules for suggestions:
- **Max 7 suggestions.** If you find more, prioritize by impact (repeated corrections > one-offs).
- **Be specific.** Not "improve writing quality" but "add rule: no sentences over 20 words in posts."
- **Only suggest changes the data supports.** Don't pad with generic improvements.
- **If nothing meaningful to update, say so.** "Clean session — nothing to calibrate" is a valid output.
- **Project context capture (auto-included).** If the session has a project attached via `coordinate` or `onboard` — i.e. you've read or written to a `context.md` or `session-log.md` this session — automatically include a final suggestion:
  ```
  N. PROJECT: {ID} — Append a session-log entry to {project-folder}/session-log.md
  capturing the important bits of this session (key decisions, files created/edited,
  open questions, what's next).
  Brief why: Project has coordination structure; this session's work should land in
  the project log so the next session picks up cleanly.
  ```
  This applies whether the project was loaded via `/onboard` at session start, or `coordinate` was invoked mid-session, or any session-log/context edits happened. If multiple projects were touched, suggest one entry per project. Skip only if no project files were read or written this session.

### Step 4: Apply

Wait for the user to respond with which numbers to apply (e.g. "do 1 and 3", "all", "skip 2").

Then:
1. Make the changes to the target files
2. Confirm each change with the file path and a one-line summary
3. If updating a skill, re-read it after editing to verify it's coherent
4. If updating memory, follow your memory system rules (write file + update index)

### Step 5: Done

No follow-up needed. Changes are live for the next time the skill/rule is invoked.

## What NOT to Suggest

- Changes that are already in the relevant skill or CLAUDE.md (check first)
- Generic "best practices" not grounded in this session's data
- Temporary fixes for one-off situations
- Changes to other agents' files unless this agent has write access
