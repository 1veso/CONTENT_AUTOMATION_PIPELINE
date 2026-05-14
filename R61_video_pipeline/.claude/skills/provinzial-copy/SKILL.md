---
name: provinzial-copy
description: provinzial, provinzial-copy, Geier Ayhan — German copy rules for Provinzial campaign content (R55/R57/R61); overrides generic marketing skills
---

# Provinzial Copy Rules (Geier & Ayhan Campaign)

This skill governs ALL copy, captions, hooks, voiceover scripts, and on-screen text produced for the Provinzial Versicherung "Geier & Ayhan" campaign across R55 (Shorts), R57 (static images), and R61 (cinematic videos).

**Precedence:** When this skill is loaded, it overrides general marketing skills (copywriting, ad-creative, social-content, ogilvy, market-copy, etc.) for any output destined for Provinzial channels. Use the general skills as input; let these rules filter the output.

## 1. Language

- All audience-facing copy is **German**. No English in captions, hooks, or VO unless the campaign explicitly calls for a code-switch.
- Use **Du** (informal) by default — TikTok/Instagram/Meta audience expects it. Only switch to **Sie** if a specific piece is targeted at older demographics or business contexts.
- TTS provider (Fal Gemini) requires the language enum **"German (Germany)"** — never `de-DE`. See [[feedback_fal_gemini_tts_lang_enum]].

## 2. Regulatory guardrails (non-negotiable)

Provinzial is a regulated **Versicherung** (insurance company). Copy must not:

- Promise specific coverage, payouts, or rates without a disclaimer.
- Use absolute claims ("immer", "garantiert", "100%") around insurance outcomes.
- Compare Provinzial against named competitors in a disparaging way.
- Imply free service when fees apply, or hide material terms.

If a hook leans into a coverage promise, add a soft qualifier (e.g., "je nach Tarif", "im Schadenfall*") and flag that legal review may be needed before publish.

## 3. Voice & tone

- **Warm, direct, slightly cheeky** — campaign features personas (Geier & Ayhan); copy should sound like them talking, not corporate Provinzial.
- Active voice. Short sentences. Spoken cadence — written to be read aloud or scanned in 2 seconds.
- Concrete > abstract. "Auto kaputt." beats "Im Falle eines Schadenereignisses."
- One idea per sentence. One sentence per beat.
- No buzzwords: "innovativ", "ganzheitlich", "Synergie", "auf Augenhöhe" — all banned.

## 4. Hooks (first 1–2 seconds)

TikTok / Reels / Shorts all live or die in frame 1. Hook rules:

- **Pattern interrupt** in the first beat — a question, a contradiction, a number, or a relatable pain. Never start with "Hallo, ich bin…".
- ≤ 6 words on screen if there's overlay text.
- Hook must work **sound-off**. The image + caption alone has to make someone stop scrolling.
- TTS lines under 8 words for the opening beat — Gemini TTS handles short German sentences cleanly; long ones drift in pacing.

## 5. Platform formats

| Platform | Aspect | Caption | Hashtags | Length |
|---|---|---|---|---|
| TikTok | 9:16 | DE, casual, 1–2 sentences, no emojis unless campaign-specific | 3–5, mix branded (#Provinzial) + topical | 15–30s sweet spot |
| Instagram Reels | 9:16 | DE, can be slightly longer than TikTok, light emoji ok | 5–10, group at end | 15–60s |
| Meta (Feed) | 1:1 or 4:5 | DE, can extend with story context | 3–5 | up to 60s |

R57 static images go on Meta/Instagram feed; R55/R61 video goes everywhere. R61 cinematic ads can run paid — copy needs to survive Meta's policy review.

## 6. CTAs

- One CTA per asset. Never stack ("Folgen + Kommentieren + Link in Bio").
- Soft CTAs ("Mehr erfahren") for awareness, hard CTAs ("Tarif berechnen") only on lower-funnel R61 pieces.
- Never "Jetzt kaufen" or any urgency claim without a real deadline.

## 7. Geier & Ayhan persona rules

> **Gap — needs user input.** I don't have the campaign brief for Geier & Ayhan in the repo. Until the user provides it, treat them as the on-screen talent and write copy that:
> - lets each speak as a distinct voice (not interchangeable)
> - keeps their interaction central (they're a duo, not solo presenters)
> - leaves room for the bit/joke to land before the brand message

**TODO:** Replace this section with the actual persona brief (speech patterns, recurring bits, what they each represent in the campaign). Ask the user for: tone differences between the two, signature phrases, what's off-limits.

## 8. Output checklist (apply before handing back copy)

- [ ] Language is German
- [ ] Du/Sie matches the audience
- [ ] No banned buzzwords (§3, §4)
- [ ] No unqualified coverage promises (§2)
- [ ] Hook works sound-off
- [ ] One CTA, appropriate to funnel stage
- [ ] Caption + hashtag count matches platform
- [ ] Geier & Ayhan voices are distinct (when both appear)

## 9. Related project memory

- [[project_provinzial_content]] — R57 engine + Airtable + Blotato wiring
- [[project_r61_video_pipeline]] — R61 cinematic ad pipeline, 4 human gates
- [[feedback_blotato_no_post]] — scheduling allowed, immediate posting paused
- [[feedback_fal_gemini_tts_lang_enum]] — TTS language must be "German (Germany)"
