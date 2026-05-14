# robo-skills

Seven workflow skills for Claude Code. They run before, during, and after a session — clarify intent, attack drafts, generate variations, coordinate projects, dial in HTML, and tune the agent on the fly.

These aren't industry-specific. They're meta-skills that improve how you work with Claude Code across every task.

## What's inside

```
robo-skills/
├── README.md
├── LICENSE
└── .claude/
    └── skills/
        ├── align/        — pre-work clarifying questions before effort is spent
        ├── burst/        — generate N distinct variations of any request
        ├── calibrate/    — mid-session self-improvement; surfaces 1-7 skill/setup updates
        ├── coordinate/   — cross-session project workspace at a shared projects folder
        ├── devil/        — red-team an artifact, sharp criticism only, no fixes
        ├── onboard/      — load a project, ask clarifying questions before working
        └── tweak/        — live tweak panel injected into any HTML (sliders → bake)
```

## Quick start

Clone the repo:

```bash
git clone https://github.com/robonuggets/robo-skills
```

Copy the skills into your Claude Code skills folder:

```bash
# macOS / Linux
cp -r robo-skills/.claude/skills/* ~/.claude/skills/

# Windows (PowerShell)
Copy-Item -Recurse robo-skills/.claude/skills/* "$env:USERPROFILE/.claude/skills/"
```

Or, if you're using these inside a specific workspace, copy them into that workspace's `.claude/skills/` folder.

Each skill is triggered by its slash command (`/align`, `/burst`, `/calibrate`, `/coordinate`, `/devil`, `/onboard`, `/tweak`) or by natural-language phrases listed in each SKILL.md description.

## The 7 skills — when to use each

### `/align [task]`
Before starting work that could go wrong. Asks 1-5 numbered questions to lock in scope, format, audience, and constraints. One round, then it gets out of the way.

### `/burst {N} [request]`
When you want options, not the first answer. Generates N wildly different variations across design, voice, structure, and angle. Flags long tasks and cost-incurring work before starting.

### `/calibrate` / `/calibrate lite`
End of a session, or after a few corrections. Scans the conversation, surfaces 1-7 specific fixes (skill, CLAUDE.md, memory). You pick which to apply. Lite mode = fast 1-3 suggestions from the last ~15 turns.

### `/coordinate [ID]`
For work that spans sessions. Creates or loads a shared project workspace at `{your-workspace}/{ID}-{name}/` with `context.md` + `session-log.md`. All sessions on the project share context. Has a lite mode for one-off decisions.

### `/devil [artifact]` or `/devil {N}`
Right before you ship. Attacks the artifact — title, draft, plan, decision — with the strongest case against it. No fixes, no padding. Optional `{N}` for exactly that many points.

### `/onboard [project]`
You're starting a session on a project that already exists. Loads context, briefs you in 3-5 bullets, then asks 2-4 clarifying questions before doing any work. Companion to `coordinate`.

### `/tweak [file]` / `tweak light` / `tweak max`
Inject a live controls panel into any single-file HTML. Auto-picks sliders (speed, font size, density, glow, etc.), lets you dial in changes in the browser, then bakes the result back into the source CSS. Two tiers — 5 sliders or 10.

## Example workflow

```
# Before starting a project
/coordinate launch-email
# (loads or creates the workspace, then asks what we're doing today)

# Mid-work, on a tricky task
/align write the launch email
# (5 numbered questions, then writes)

# Need options for the subject line
/burst 5 subject lines

# Got a draft, want to stress-test it before sending
/devil 3
# (3 sharp criticisms, no fixes)

# End of session
/calibrate lite
# (1-3 specific suggestions for improving the skills based on what just happened)
```

## Setup notes

### Workspace path (for `coordinate` and `onboard`) — required one-time setup

The `coordinate` and `onboard` skills need a single root folder on your machine where all coordinated projects live. The skill files refer to it as `{WORKSPACE}` — that's a placeholder you swap **once** before using the skills.

**Do this before invoking `/coordinate` or `/onboard`:**

1. Pick a path. Examples: `~/projects/`, `~/.claude/projects/`, `D:/work/`, anywhere.
2. Open `.claude/skills/coordinate/SKILL.md` and `.claude/skills/onboard/SKILL.md`.
3. Find/replace every `{WORKSPACE}` with your chosen path.
4. Save. Done.

The skills will auto-create the folder on first use if it doesn't exist. If you skip this step, the agent will keep the literal `{WORKSPACE}` token and you'll get confused output.

If you'd rather not edit the files, just tell the agent your root path at the start of the session — it'll honour that instead.

### Skill discovery

Most agents (Claude Code, Claude Desktop with MCP, etc.) auto-pick up new skill folders inside `.claude/skills/`. You may need to restart the session for the new skills to show in the available list.

### No external dependencies

None of these skills require API keys, MCPs, or external services. They're pure workflow logic that runs inside whatever Claude session you're in.

## Credit

Built by Jay from RoboNuggets. These skills were refined over many sessions of real use — they encode patterns that survived contact with actual work. The shape of each one reflects the kind of mistake it stops you from making.

Learn more at [robonuggets.com](https://robonuggets.com).

## License

CC BY 4.0 — free to use, adapt, and share with attribution. See [LICENSE](LICENSE).
