---
name: devil
description: Red-team a specific artifact before it ships — sharp, blunt criticism only, no fixes, no padding. Triggers on "/devil", "devil", "/devil [artifact]", "red-team this".
---

# Devil: Red-Team A Specific Artifact

## What This Does

Attack a draft, decision, plan, title, script, design, or any artifact. Surface its weakest points. No fixes, no counters, no "but on the other hand" — just the strongest case against shipping it as-is. Built for the moment right before commit, when you need to hear what's wrong before it goes out.

## When To Use

- `/devil` → red-team the most recent artifact in the conversation
- `/devil [artifact]` or `devil [artifact]` → red-team that specific thing
- `/devil {N}` or `/devil {N} [artifact]` → give exactly N points, no more, no less
- "red-team this" → same

Do NOT invoke on your own. Only when asked.

## Process

### Step 1: Identify The Target

What's being devil'd?
- If `/devil [thing]` — that's the target
- If `/devil` alone — the most recent artifact (draft, title list, plan, decision)
- If `/devil {N}` — N is the number of points to give, target is still the most recent artifact (or the thing named after N)
- If unclear — ask "devil what?" and stop

### Step 2: Attack

Rules:

- **Number control.** If a number is given (`/devil 3`, `/devil 7`), give exactly that many points — no more, no less. If no number, cap at 5 and pick the strongest. If asked for more after, expand.
- **Plain English by default.** Write at a 3rd-grade reading level. Short words. Short sentences. Talk like a normal person, not a magazine. No jargon unless the artifact itself is technical and the word is the right one.
- **Bolded title phrase.** Each point starts with a short bolded title (2-5 words) that names the weakness, then a dash, then the explanation. Example: `1. **Buried verb.** The action word shows up too late, so people scroll past before they get it.`
- **Pure attack.** No fixes, no "you could solve this by…", no counter-offers, no silver lining. Just the weakness.
- **Sharp and blunt.** Direct language. Don't soften with "this might be a slight concern" — say "this is wrong" / "this won't land" / "this is the weakest line."
- **Real points only.** Never pad to hit the number. If asked for 5 and there are only 3 real weaknesses, give 3 and say "only 3 real ones here." Same for 1, 2, 7, whatever.
- **Each point stands alone.** One sentence to name the weakness, optionally one more to make the case. Don't ramble.
- **Attack the artifact, not the person.** "This title is weak because X." Never "you got this wrong."

Format:

```
Red-teaming [one-line restatement of the artifact].

1. **[Title phrase.]** [Weakness in plain English.]
2. **[Title phrase.]** [Weakness in plain English.]
3. **[Title phrase.]** [Weakness in plain English.]
```

If there are zero real weaknesses (rare): say so. "Nothing to attack — this is solid." Don't manufacture problems.

### Step 3: Stop

No follow-up. No "want me to fix these?" No restatement. The user decides what to do with the criticism.

If they then ask for fixes, switch out of devil mode and help fix. Don't blend modes.

## What NOT To Do

- Don't soften ("this might be" / "potentially" / "one could argue") — be blunt
- Don't suggest fixes unless asked after
- Don't pad to hit 5 points
- Don't attack the person, only the artifact
- Don't blend devil + helpful — pick one, devil first
- Don't apologise for being harsh — the skill is invoked specifically for harshness

## Examples

**Example A: `/devil` (no number, after a list of 3 video titles)**

```
Red-teaming the 3-title list.

1. **One-note feed.** All three start with the same tool — your whole channel reads like one product, and people notice.
2. **Dead hook.** Title 2 puts the action word too late, so phone viewers scroll past before they get it.
3. **Tired number.** "10x" is the most worn-out word on YouTube right now — it tells people to skip.
4. **Missing second tool.** Combo videos need two tool names in the title. None of these have that.
5. **Hype word.** "INSANE" in title 1 is the kind of AI-smell word that's worth avoiding.
```

**Example B: `/devil 3` (asked for exactly 3)**

Give 3 points. Not 5. Not 4. Just 3, the strongest ones.

**Example C: `/devil 5` but only 2 real weaknesses exist**

```
Red-teaming the plan. Only 2 real weaknesses here, not 5.

1. **Wrong tool.** A CLI can't catch webhooks — you'd still need a server.
2. **Untested repo.** The pick has near-zero stars and one maintainer.
```

No fixes. No "want suggestions?" Stop.
