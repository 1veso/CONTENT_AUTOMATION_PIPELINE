---
name: provinzial-copy
description: provinzial, provinzial-copy, Geier Ayhan, Geier & Ayhan, Geschäftsstelle Geier Ayhan — German copy rules for Provinzial campaign content (R55/R57/R61); voice = NRW neighbourhood advisor, not national brand; overrides generic marketing skills
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

**Who they are:** Geier & Ayhan OHG is a Provinzial Geschäftsstelle (insurance agency) operating in the **NRW region** — real local agents, named on the door. All campaign copy is published under their voice, not as a national-brand spot. Treat the on-screen duo as the same Geier & Ayhan who actually sit across the desk from a customer in NRW.

**Target audience (catchment-area first):**
- Local business owners (Handwerk, Gastronomie, kleine Mittelständler)
- Families with kids, dual-income households
- Homeowners (Eigenheimbesitzer) and aspirational first-time buyers

**Tone — neighbourhood advisor, not national chain:**
- Slightly warmer and more personal than corporate Provinzial copy
- "Wir kennen Sie und Ihre Straße" energy — not "Wir bieten 24/7-Hotlines"
- Local references are welcome: NRW geography, Vereinsleben, Schützenfeste, Kirmes, "bei uns im Viertel". Specificity > generic regional flavour.
- Humour is dry and grounded. Never quippy or callcenter-cheerful.

**Signature phrases (use sparingly — overuse turns them into slogans nobody hears):**
- "Wir kennen Ihre Region."
- "Persönlich. Lokal. Verlässlich."

These belong at the **end** of an asset (signature/sign-off slot), not in the hook. Hooks still follow §4 rules — pattern interrupt, ≤6 words on screen.

**Du vs Sie:**
- Default to **Sie** for this persona — local advisor speaking to a real customer (business owners, homeowners) leans formal-warm, not chummy.
- **Du** is acceptable on TikTok pieces aimed at younger families/first-time-buyers, but only when the asset's overall energy is casual. Don't mix Du/Sie inside a single asset.
- This is a deliberate override of §1's "Du by default" — Geier & Ayhan are advisors, not influencers.

**Off-limits (anything that breaks the neighbourhood-advisor frame):**
- Anything that sounds like a call-centre: "Unsere Hotline ist 24/7 für Sie da", "Verfügbar in Sekunden", recorded-voice cadence.
- National-brand abstraction: "Wir versichern Deutschland", "in jeder Region", "deutschlandweit". Stay in NRW or stay generic — never claim national reach.
- Anonymous corporate voice: no "Provinzial bietet…" passive constructions when the same line can be Geier or Ayhan saying it directly.
- Aggressive sales pushes ("Heute noch abschließen!"), urgency tricks ("Nur diese Woche!"), or any urgency claim without a real local deadline.
- Stock-photo-style scenarios (smiling family in glass office). The agents work out of a real NRW Geschäftsstelle — keep the setting credible.

**When Geier and Ayhan both appear in the same asset:**
- Let them sound like two different people. One can be the warmer relationship-builder, the other the practical numbers-and-coverage voice — pick a split and keep it consistent across the campaign.
- Their interaction is the appeal. Don't make either a feed line for the other.
- Leave room for the bit/joke to land before the brand message arrives.

**When only one is on camera:**
- Reference the agency, not the brand: "Hier in unserer Geschäftsstelle…" beats "Bei Provinzial…".
- Sign-off still carries both names if it's a campaign-branded piece.

## 8. Output checklist (apply before handing back copy)

- [ ] Language is German
- [ ] Du/Sie matches the audience
- [ ] No banned buzzwords (§3, §4)
- [ ] No unqualified coverage promises (§2)
- [ ] Hook works sound-off
- [ ] One CTA, appropriate to funnel stage
- [ ] Caption + hashtag count matches platform
- [ ] Geier & Ayhan voices are distinct (when both appear)
- [ ] Voice is neighbourhood-advisor, not national-chain (§7 off-limits)
- [ ] If signature phrase used, it's in sign-off slot, not hook
- [ ] No national-reach or callcentre framing

## 9. Related project memory

- [[project_provinzial_content]] — R57 engine + Airtable + Blotato wiring
- [[project_r61_video_pipeline]] — R61 cinematic ad pipeline, 4 human gates
- [[feedback_blotato_no_post]] — scheduling allowed, immediate posting paused
- [[feedback_fal_gemini_tts_lang_enum]] — TTS language must be "German (Germany)"
