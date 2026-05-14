# Cinematic Ads Agent Kit

Auto-build cinematic product ads from a single product input — drop in your product, the agent picks the best angle, builds a storyboard, and ships a full 15-second ad with music + sound design.

> Give it a product. It analyses the best angle, proposes 3 storyboard directions, generates a timestamped storyboard sheet (GPT Image 2), then animates it into a 15s ad with native music + SFX (Seedance 2.0 Pro). Plus optional b-roll and product macro clips.

**Four steps. One command. Any product.** Runs in Claude Code, OpenClaw, or any other agentic platform — only the harness changes, the skill is portable.

## What's Inside

```
.claude/skills/cinematic-ads/SKILL.md   ← The skill that builds the ads
templates/                              ← Runnable .mjs scripts (Step 3 + Step 4)
examples/cloudsurfer-max-ivory/         ← Working example output (storyboard + 15s ad)
```

## What It Does

1. **Send Product** — Drop in a product link, image, or brief. Agent extracts brand, colorway, and reference images.
2. **Approve Direction** — Agent proposes 3 distinct storyboard directions (concept, vibe, hero moment, model-vs-product-only). You pick.
3. **Generate Storyboard** — GPT Image 2 renders a 6-panel timestamped sheet with SCENE/ACTION/SOUND captions. ~$0.18.
4. **Generate Ad** — Seedance 2.0 Pro animates the storyboard into a 15s ad with native music + SFX. ~$4.54 at 720p. Plus optional b-roll panels and product macro clips.

The agent always quotes the cost and waits for explicit approval before any paid run.

## Quick Start

**Step 1:** Clone this repo

```bash
git clone https://github.com/robonuggets/cinematic-ads-agent-kit.git
```

**Step 2:** Add to Claude Code

```bash
claude --add-dir ./cinematic-ads-agent-kit
```

**Step 3:** Use it

Tell Claude Code to make an ad:

```
Make a cinematic ad for these On Cloudsurfer Max sneakers: https://on.com/cloudsurfer-max
```

Or paste a product image directly:

```
Build a 15-second ad for this lip tint [attach product photo]
```

Or describe the product:

```
Cinematic 15s ad for a matte-black mechanical keyboard called Threshold, target gamers
```

The agent runs the 4 steps, pausing at each one for your input.

## Setup — API Keys

This kit uses **Fal AI** for both image generation (GPT Image 2) and video (Seedance 2.0 Pro). One vendor, one key.

### Fal AI

1. Sign up at https://fal.ai
2. Top up credits at https://fal.ai/dashboard/billing
3. Get your key at https://fal.ai/dashboard/keys
4. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
5. Open `.env` and paste your key:
   ```
   FAL_KEY=fal_your_key_here
   ```

The skill never hardcodes the key into source — `.env` only.

## Costs

| Step | What | Cost |
|------|------|------|
| 1 | Send product | Free |
| 2 | Approve direction | Free |
| 3 | Storyboard sheet (GPT Image 2 high, 2560×1792) | ~$0.18 |
| 4a | Main ad (Seedance 2.0 Pro, 15s @ 720p) | ~$4.54 |
| 4b | B-roll panel (Seedance 2.0 Pro, 5s @ 720p, optional) | ~$1.51 each |
| 4c | Product macro (Seedance 2.0 Pro, 5s @ 720p, optional) | ~$1.51 |

**Typical full run:** ~$5–8 for storyboard + 15s ad. Cheap test run at 480p: ~$3.

The agent confirms the cost before making any paid API call. Approval for run #1 does not authorise run #2.

## Example Output

Open `examples/cloudsurfer-max-ivory/` for a working ad.

**On Cloudsurfer Max (Ivory)** — a 15-second product-only motion-graphic ad:

- 6-panel storyboard with timestamped panels and SCENE/ACTION/SOUND captions
- Studio motion-graphic suspended-in-space treatment with sweeping motion-streak gradients and wind-streak particles
- Animated by Seedance with native cinematic synth score and shoe-whoosh SFX
- No humans, no likeness rejection — cleanest possible Seedance path

This is the quality bar. See `examples/cloudsurfer-max-ivory/README.md` for the cost breakdown and what worked.

## How It Works

The skill encodes hard-won learnings from 13+ production runs across footwear, beauty, audio, drink, and apparel brands. It includes:

- **Hard cost-approval gate** — quotes cost and waits for explicit "go"/"fire"/"ship" before any paid call. Auto mode does not override.
- **Content-policy traps** — Fal's moderation layer rejects certain phrasings (clinical skin language in beauty ads, brand-destruction verbs, human likeness on Seedance ref-to-video). The skill encodes safe wording up front.
- **Mannequin face workaround** — confirmed pattern for animating human characters on Seedance: render storyboard faces as mannequin/blur, let Seedance fill in the natural face from the prompt.
- **Two-reference rule** — always pass the storyboard sheet as `@Image1` AND a clean product photo as `@Image2` to Seedance. Skipping `@Image2` is the #1 cause of product drift.
- **Storyboard discipline** — 7 rules (brand never destroyed, real-looking people, distinct camera shots, landscape 16:9 only, model-vs-product-only decided up-front, CTA on end card, no on-product text where avoidable).
- **Simple-prompt default** — A/B-tested simple 1–3 sentence Seedance prompts against verbose time-coded "Yankees" templates. Simple won. Yankees template kept as advanced fallback.

## Templates

Two runnable scripts in `templates/` if you want to skip the agent and run the API calls directly:

- `templates/generate.mjs` — Step 3 GPT Image 2 call. Edit BRAND, PRODUCT, REFS, PROMPT, run with `node templates/generate.mjs`.
- `templates/animate.mjs` — Step 4 Seedance 2.0 Pro call. Uploads the storyboard to Fal storage, references both `@Image1` and `@Image2`, downloads the MP4.

Both scripts read `FAL_KEY` from `.env`. Outputs land in `./out/`.

## Attribution

Created by Jay from RoboLabs. Learn more at [RoboNuggets](https://robonuggets.com)
