# **Mastermind Plan — Content Production Engine**

## **1\. Core system idea**

```
Campaign Brief
→ ClaudeClaw Campaign Manager
→ chooses the right pipeline per content type
→ generates assets
→ applies brand rules
→ gates quality
→ schedules only after approval
```

This is the right model:

```
ClaudeClaw = conductor
Pipelines = instruments
Campaign brief = score
Airtable = production board
R2 = asset storage
Blotato = schedule-only distribution
```

The goal today is **not GetAutomata Mission Control**. That comes later.

Today’s goal is:

```
Make the content engine produce beautiful branded campaign assets reliably.
```

---

# **2\. Provinzial campaign spine**

For Provinzial, the overall theme is:

```
Schaden passiert.
Provinzial bleibt ruhig.
Der Mensch wird durch den Moment geführt.
```

Brand rules:

```
- Provinzial green
- golden wings / Flügelgelb accent
- warm German / NRW everyday life
- human, calm, regional
- no fear-mongering
- no hype
- no generic American insurance-ad look
- German voiceover
- captions aligned to voiceover
- CTA as calm invitation, not pressure
```

Canonical short-form structure:

```
hook problem
→ intro / brand stamp
→ solution or explanation
→ natural CTA closing line
→ outro / brand exit
```

For R61 specifically:

```
hook problem → intro → solution/explanation + natural CTA → outro
```

Intro/outro are reusable local assets:

```
R61_video_pipeline/references/inputs/intro.mp4
R61_video_pipeline/references/outputs/outro.mp4
```

---

# **3\. Pipeline roles**

## **R57 — branded rhythm / static / visual seed engine**

Use R57 for:

```
- static image posts
- carousel covers
- daily visual rhythm
- green/yellow branded posts
- simple everyday Schaden moments
- source images that can feed R61
```

Best use:

```
“Schaden passiert / Schaden gemeldet / Schaden gelöst”
```

It gives the campaign volume and rhythm without needing every post to be cinematic.

---

## **R61 — cinematic trust engine**

Use R61 for:

```
- premium cinematic trust videos
- first-frame / last-frame transformation
- “moment something goes wrong → Provinzial handles it”
- German voiceover
- captions
- intro/outro
- polished final MP4
```

R61 should be the beautiful hero-engine.

Best structure:

```
Hook problem:
Something went wrong.

Intro:
Provinzial brand stamp.

Solution:
Calm explanation, help, human reassurance.

CTA:
A natural closing invitation.

Outro:
Brand exit.
```

Example:

```
Wasserrohrbruch um 3 Uhr nachts.
→ Provinzial intro.
→ Ruhig bleiben, Foto machen, Schaden melden.
→ Ein kurzer Check kann reichen, damit du weißt, worauf du dich verlassen kannst.
→ Outro.
```

---

## **R34 — Roboveo narrative story engine**

Use R34 for:

```
- 3-scene story videos
- TikTok / Reels narrative arcs
- 3 × 5s short scenes
- human mini-stories
- story-driven Schaden examples
```

Best structure:

```
Scene 1: The problem
Scene 2: Human reaction / tension
Scene 3: Resolution through Provinzial
```

Example:

```
Scene 1:
Young couple returns from holiday and sees water damage.

Scene 2:
They are overwhelmed, checking the floor and documents.

Scene 3:
They report it, advisor helps, situation becomes calm.
```

This is likely the best “narrative chained coherent short-form video” engine.

---

## **n19 — product / service ad engine**

Use n19 for:

```
- service feature ads
- product explanation
- Schaden-App
- WhatsApp-Schadenmeldung
- 24/7 Hotline
- persönlicher Ansprechpartner
- Unterlagen-Check
```

Best structure:

```
Problem
→ feature
→ benefit
→ CTA
```

Example:

```
Schaden melden in 60 Sekunden.
Foto rein.
Kurz beschreiben.
Provinzial kümmert sich.
```

n19 is **not** the universal narrative stitcher. It is the product/service ad machine.

---

## **n21 — UGC / raw human explanation engine**

Use n21 for:

```
- creator monologues
- raw UGC-style videos
- “Was würde ich machen, wenn…”
- talking-head explanation
- believable human advice
```

Best structure:

```
“Wenn mir das passieren würde, würde ich zuerst…”
```

This gives authenticity.

Example:

```
“Wenn ich einen Parkrempler sehe und keine Nummer dran ist, würde ich nicht erstmal panisch googeln. Ich würde Fotos machen, Uhrzeit notieren und meinen Ansprechpartner kontaktieren.”
```

---

# **4\. The full content mix**

A strong campaign should not be 120 identical videos.

It should be a rhythm:

```
R57 = visual rhythm / static / carousel
R61 = premium cinematic trust piece
R34 = narrative story video
n19 = service/product ad
n21 = UGC human explanation
```

Example weekly campaign flow:

```
Monday:
R57 static + R61 cinematic

Tuesday:
n21 UGC + R57 carousel

Wednesday:
R34 story + n19 service ad

Thursday:
R61 cinematic + R57 static

Friday:
R34 story + n21 UGC

Saturday:
R57 light/community post + R61 cinematic

Sunday:
reflection/static + soft story piece
```

This gives:

```
- authority
- trust
- variety
- human realism
- brand consistency
- platform-native feeling
```

---

# **5\. Potential campaign uses**

## **Insurance / Provinzial**

```
- Schadenfälle
- Hausrat
- Kfz
- Haftpflicht
- Wohngebäude
- Vorsorge
- Lebensversicherung
- Berufsunfähigkeit
- Regional service
- App / digital claims
```

Best pipeline mapping:

```
R57 → static damage moments
R61 → cinematic trust moments
R34 → story cases
n19 → insurance feature ads
n21 → “what I would do if…” UGC
```

---

## **Local business campaigns**

Examples:

```
- dentists
- lawyers
- real estate agents
- car dealerships
- gyms
- restaurants
- tradesmen
- local service providers
```

Mapping:

```
R57 → branded local posts
R61 → premium trust reels
R34 → mini customer stories
n19 → offer/service ads
n21 → founder/UGC-style explanations
```

---

## **Product launches**

```
R57 → product visuals
R61 → cinematic product lifestyle reel
R34 → story-based use case
n19 → direct product ad
n21 → testimonial-style UGC
```

---

## **E-commerce campaigns**

```
R57 → product image posts
R61 → emotional product scene
R34 → problem/solution story
n19 → conversion ad
n21 → UGC review / “I tried this”
```

---

## **Personal brand / creator campaigns**

```
R57 → quote/visual posts
R61 → polished identity reels
R34 → origin-story videos
n19 → offer breakdowns
n21 → direct-to-camera clips
```

---

# **6\. The 15-pipeline thinking exercise**

Current repo inventory confirms the larger n8n canvas contains a wider orchestra: R46, R51, R34, n16, n16.1, R39, n19, n21, n30, n31, n3, n29 variants, plus R55/R57/R61. The repo’s CLAUDE.md lists the n8n sections and confirms 12 pipelines plus 16 webhook chains inside the active canvas.

## **R46 — Extractor**

Purpose:

```
scrape / extract winning content from platforms
```

Use for:

```
- competitor research
- TikTok inspiration
- Meta ad library style extraction
- content pattern mining
```

Role:

```
Market intelligence input.
```

---

## **R51 — Creative Cloner**

Purpose:

```
turn extracted winners into adapted concepts
```

Use for:

```
- cloning structure, not content
- adapting proven hooks
- creating new client-safe versions
```

Role:

```
Pattern translation engine.
```

---

## **R34 — VeoRobo**

Purpose:

```
3-scene AI video storytelling
```

Use for:

```
- narrative arcs
- TikTok stories
- situation → tension → resolution
```

Role:

```
Story video engine.
```

---

## **n16 — Narrative Chaining**

Purpose:

```
connect multiple generated segments into coherent narrative flow
```

Use for:

```
- multi-scene coherence
- longer short-form structure
- story continuity
```

Role:

```
Narrative glue.
```

This may become the bridge between R34/R61/n19 later.

---

## **n16.1 — Auto Subtitles**

Purpose:

```
caption generation / subtitle overlay
```

Use for:

```
- TikTok captions
- Reels captions
- accessibility
- retention
```

Role:

```
Retention layer.
```

---

## **R39 — Split AI Images**

Purpose:

```
image generation / image splitting / creative variations
```

Use for:

```
- carousel frames
- ad image sets
- scene stills
```

Role:

```
Visual expansion engine.
```

---

## **n19 — Ultimate Video Ads**

Purpose:

```
product/service ad generation
```

Use for:

```
- paid ads
- service explainers
- feature-led content
- offer videos
```

Role:

```
Conversion engine.
```

---

## **n21 — Ultimate UGC Creator**

Purpose:

```
UGC-style creator content
```

Use for:

```
- talking-head videos
- testimonial-style content
- raw creator ads
- authentic explanations
```

Role:

```
Human realism engine.
```

---

## **n30 — Product Videography**

Purpose:

```
high-end product shots / product scenes
```

Use for:

```
- e-commerce
- product hero videos
- premium product campaigns
```

Role:

```
Product cinema engine.
```

---

## **n31 — Precision Camera**

Purpose:

```
camera-movement controlled generation
```

Use for:

```
- polished product moves
- cinematic camera passes
- premium agency-quality assets
```

Role:

```
Camera control engine.
```

---

## **n3 — Voice & Subs**

Purpose:

```
voiceover and subtitle processing
```

Use for:

```
- multilingual voice
- subtitle generation
- narration polish
```

Role:

```
Audio/caption utility layer.
```

---

## **n29 — TikTok / YouTube / Script quality gates**

Purpose:

```
quality scoring, repurposing, and platform transformations
```

Use for:

```
- TikTok to Sora
- YouTube long to LinkedIn/X
- YouTube short to script
- quality gate scoring
```

Role:

```
Quality and repurposing gate.
```

---

## **R55 — long-form clipper**

Purpose:

```
long-form video → Shorts
```

Use for:

```
- podcasts
- webinars
- interviews
- client raw videos
```

Role:

```
Long-form extraction engine.
```

---

## **R57 — static / visual seed engine**

Purpose:

```
branded static visuals and source images
```

Role:

```
Campaign rhythm + visual seed engine.
```

---

## **R61 — cinematic finalizer**

Purpose:

```
first/last frame video + voiceover + stitch
```

Role:

```
Premium trust reel engine.
```

---

# **7\. Full seamless system design**

ClaudeClaw Campaign Manager receives:

```
client
brand brief
campaign theme
campaign duration
daily post count
target platforms
content mix
available raw footage
competitor URLs
product/service priorities
posting hold rules
budget cap
```

Then ClaudeClaw creates:

```
campaign calendar
scenario map
pipeline assignment
asset requirements
cost estimate
quality gates
posting schedule
```

Then per content item:

```
1. Choose scenario.
2. Choose content type.
3. Choose pipeline.
4. Generate asset.
5. Apply brand rules.
6. Apply captions/voice/music.
7. Gate quality.
8. Store final in Airtable/R2.
9. Schedule through Blotato only after approval.
```

---

# **8\. The true moat**

The powerful thing is not “AI generates videos.”

The powerful thing is:

```
A campaign brief becomes a multi-platform content calendar,
and every post is routed to the right production pipeline automatically.
```

That means:

```
- one client brief
- many content types
- consistent brand
- varied creative output
- platform-specific formatting
- human quality gates
- scheduled distribution
```

This is the real engine.

---

# **9\. Immediate execution plan**

For tomorrow:

```
1. Finish one R61 sample.
2. Produce one R34 sample.
3. Keep the R57 sample as the branded static proof.
4. Present the system as:
  - R57: branded visual post
  - R61: cinematic trust reel
  - R34: narrative story short
```

Then:

```
5. Batch R57.
6. Batch R61.
7. Verify R34.
8. Defer n19/n21 until their blockers are cleared.
```

After that:

```
9. Bring n19 online for service/product ads.
10. Bring n21 online for UGC monologues.
11. Wire ClaudeClaw campaign manager as the conductor.
```

---

# **10\. Final master sentence**

```
We are building a campaign engine where ClaudeClaw reads the brief, chooses the right production pipeline, generates varied branded assets, gates quality, and schedules the campaign across platforms — with R57 for branded rhythm, R61 for cinematic trust, R34 for narrative stories, n19 for service ads, and n21 for UGC realism.
```

That is the plan.

