---
name: burst
description: Generate N distinct variations of any request. Usage `/burst {N} [request]` — default N=3. Flags long tasks (>5 min) and any cost-incurring work (image/video/audio gen, paid APIs) before starting. Triggers on `/burst` or "burst N [thing]" / "give me N variations".
---

# Burst

Generate N distinct variations of whatever the user asks for.

## Usage

- `/burst {N} [request]` — produce N variations
- `/burst [request]` — defaults to 3
- N is any positive integer

## Always

- **Vary by default — wildly.** Every burst pushes across multiple axes at once. Different design language, different voice/tone, different structure, different angle. If three variations could swap labels without anyone noticing, you failed. Treat each option as a separate person solving the same brief.
  - **Design axis** — colour palette, typography family, layout grid, density, motion, ornament vs minimal.
  - **Voice axis** — formal vs casual, builder vs marketer, plain English vs technical, calm vs urgent, first-person vs third.
  - **Structural axis** — narrative shape (question→answer, list, manifesto, before/after, single image, dense grid).
  - **Angle axis** — emotional appeal, status appeal, curiosity, utility, contrarian take.
  - Aim to move at least 2-3 axes between each pair of variations. Minor word swaps and re-skins don't count.
- **Lock the seed message; vary everything else.** When the user seeds a title/hook/copy, hold the core message constant across variants. Diversify the wrapper (design, voice, angle, structure), not the meaning. Only diversify the message itself when the user asks for "different directions" or "different angles" explicitly.
- **Label every variation.** V1/V2/V3, A/B/C, or 1/2/3 so the user can pick by label.
- **Name your pick at the end.** Recommend one with a one-line reason. Don't pick instead of presenting.
- **Lean into the theme.** When the source has a strong thematic anchor (a noun/concept threaded through it), at least one variation must lean into that theme directly. Don't default to generic alternatives when the theme is sitting right there.
- **Show the preview for phrase-level swaps.** When variations are replacements for a phrase inside a larger title/sentence/post, show the full preview line with the pick so the swap reads in context.

## Self-check before sending

Before posting the burst, scan it:
- Could V1 and V2 swap design styles with no other change? Too close — push further.
- Do all variations sound like the same writer? Too close — change voice on at least one.
- Did every variation use the same structure (all 3 bullets, all 3 single-line)? Too close — change shape on one.

If you can't articulate "V1 is X, V2 is Y, V3 is Z" in three distinct words, regenerate.

## Flag BEFORE starting

### Long tasks (>5 min total work)

Report scope + estimated time, wait for explicit "go" before doing the work.

Trigger:
- `/burst 10 websites` — multi-step per item
- `/burst 5 video scripts` — research + writing per script
- `/burst 8 detailed product pages`
- `/burst 5 storyboards` — multi-shot per board

Don't trigger:
- `/burst 5 hooks` — text only, fast
- `/burst 10 subject lines` — short text
- `/burst 3 image prompts` — prompt text, no generation

Format:
> Heads up: this is N items × ~M min each = ~T min total. Going to wait for go.

### Cost-incurring work

Any paid API call (image gen, video gen, audio gen, paid LLM calls) triggers a cost quote BEFORE spending.

Auto mode does NOT override this.

Format:
> Heads up: this will run [N] generations on [model] at [$X each] = [$total]. Going to wait for go.

Re-quote per batch — cost approval applies per generation batch, not just session start.

## Voice rules

- Match the user's natural voice and spelling preferences
- No em-dashes
- No "isn't X, it's Y" constructions
- No filler hedge words ("honestly", "frankly")
- Builder voice, not corporate

## When request is ambiguous

If `/burst 5 ideas` could mean wildly different things in scope (one might be "5 post titles" = fast text, another might be "5 product launches" = each is a project), ask one quick clarifying question before generating. Otherwise execute.

## Iteration patterns to expect

When the user is in a writing-iteration session (drafting a post, line-rewriting an opener, picking descriptors), expect repeated `/burst` calls in the same conversation — sometimes 4-5 in a row on different lines / single words / phrases. Each one stands alone; don't try to second-guess and pre-generate "more" without being asked. But also: when they run `/burst` four times in a row at N=5, they're likely to keep wanting 5s — match the rhythm rather than dropping back to N=3 default unless told otherwise.

Common rapid-fire patterns:
- Opener variations → descriptor swaps inside the opener → mid-sentence word swaps → closer rewrites
- Hook directions → benefit phrasings → CTA wording
- Title options → subtitle options → tagline options

Treat each as a fresh `/burst` — distinct variations, labelled, with a pick. Don't merge across calls or assume the previous winner constrains the next batch.
