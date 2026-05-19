# SOLUTION + CTA — Schaden v1 Campaign Brief (R61 voiceover scripts)

**Client:** Provinzial Geier & Ayhan (NRW Geschäftsstelle)
**Scope:** 30 spoken-German voiceover scripts — solution narration (~9–10s) + CTA closer (~5s) — for the Schaden v1 R61 cinematic series
**Format:** ElevenLabs `eleven_multilingual_v2`, Jones/Clara voice rotation per `generation_notes.md`; HyperFrames hybrid stitch consumes the script via `R61_video_pipeline/tools/voiceover_gen.py`
**Created:** 2026-05-19
**Status:** Draft for operator review (Track C of shovel-execution plan)

---

## 1. Purpose

Define the 30 spoken solution+CTA scripts that pair with the Schaden v1 hook-problem cards already produced in Track A (`HOOK_PROBLEM_brief.md`, `hook_problems_30_days.csv`). These scripts are the **resolution layer** — the part where Provinzial picks up the thread the hook dropped and walks the viewer calmly to the close.

This brief does **not** redesign the campaign — it narrows scope to the spoken solution+CTA production track. Strategic frame, pillars, voice rotation, and pipeline assignments stay anchored in:

- `obsidian-brain/strategy/Mastermind_Plan_Content_Production_Engine.md` — campaign spine + R61 4-beat structure
- `campaigns/Provinzial_Schaden_Campaign/CAMPAIGN_BRIEF.md` — Schaden v1 scope, 50-scenario backlog, R61 pattern
- `campaigns/Provinzial_Schaden_Campaign/HOOK_PROBLEM_brief.md` — Track A anchor (Du, payoff rotation, theme distribution)
- `campaigns/Provinzial_Schaden_Campaign/hook_problems_30_days.csv` — canonical source for Day/theme/scenario/voice_tone (this brief inherits all four columns verbatim)
- `obsidian-brain/clients/Provinzial_Geier_Ayhan/brand_brief.md` — voice, colour, NEVER-list
- `obsidian-brain/clients/Provinzial_Geier_Ayhan/content_library.md` — existing R61 voiceover state (8 Gemini TTS placeholders, 22 pending ElevenLabs)
- `obsidian-brain/clients/Provinzial_Geier_Ayhan/generation_notes.md` — voice rotation rationale (Jones / Clara per index parity)
- `R61_video_pipeline/.claude/skills/provinzial-copy/SKILL.md` — German copy rules (loaded for this brief)

---

## 2. Format spec — audio timing

| Element | Spec | Source |
|---|---|---|
| Solution VO target length | 9–10s spoken German | shovel-plan anchor |
| Solution VO word count | ~22–28 German words (≈2.5 wps) | derived from ElevenLabs `eleven_multilingual_v2` pacing on 30-record v1 batch |
| CTA VO target length | 5s spoken German | shovel-plan anchor |
| CTA VO word count | ~10–13 German words | same derivation |
| Voice provider | ElevenLabs `eleven_multilingual_v2` (Jones odd / Clara even, when payment unblocks); Gemini TTS placeholder otherwise | generation_notes.md §Voice selection rationale |
| Voice tone | inherited from `hook_problems_30_days.csv.voice_tone` (same Day = same tone) | Track A |
| Same speaker | one voice carries the full clip — solution AND CTA from the same ElevenLabs voice ID, no mid-clip swaps | derived from R61 4-beat unity rule |
| Caption layer | yellow `#FFD000` active-word highlight, white base, green stroke; word-by-word reveal driven by HyperFrames hf-seek | HyperFrames captions reference |

---

## 3. Golden building blocks (the levers that matter 10x more than voice choice)

These five rules govern every solution_voiceover and cta_voiceover row in the CSV. They are the difference between a script that converts and one that scrolls past.

### A. Hook quality is paramount — justify within 2–3 seconds

The solution must redeem the hook's promise inside the first sentence. No preamble. No "first let me explain how Provinzial works…". Drop the viewer **straight into the resolution**.

- ❌ `Hi, ich bin von Provinzial und möchte dir erklären, wie wir bei Leitungswasserschäden vorgehen…`
- ✅ `Atme durch. Du machst ein Foto, meldest in der App — wir übernehmen ab Minute eins.`

The hook said "Dein Rohr platzt um 3 Uhr morgens. Provinzial nimmt's auf." — the solution's first three words ("Atme durch.") *are* Provinzial taking it on.

### B. Caption quality — punchy in 3–5 word chunks

Every solution_voiceover is captioned word-by-word. Script must break naturally into 3–5 word caption chunks. Avoid stacking compound-noun mouthfuls back-to-back (one or two per script is fine; three in a row breaks rhythm).

- ❌ `Die Wohngebäudeversicherung übernimmt die Dachziegelreparatur durch Sturmschadenbearbeitung.` — three compound monsters in a row, captions die
- ✅ `Wohngebäude zahlt für Dachziegel, Hausrat für Schäden innen.` — same information, captions breathe

### C. Visual quality match — VO narrates what's on screen

The solution VO must match the visible action at that exact moment. If the visual shows a Provinzial advisor on the phone, the VO talks about being helped. Don't describe abstract product features when a concrete scene is playing.

- Visual: advisor at desk, customer on phone → VO: "Wir kümmern uns ab Minute eins."
- Visual: app screen, photo upload → VO: "Foto rein, Schaden gemeldet, fertig."
- Visual: damaged car at roadside → VO: "Werkstatt rein, Ersatzwagen raus."

Concrete scene → concrete narration. The viewer's eyes and ears must point at the same thing.

### D. First 0.5s of audio is loaded

TikTok's algorithm uses early audio energy as a retention signal. The first spoken syllable must carry weight — strong consonant, emotive word, or a number. Never start with `äh`, filler, soft `und`, or a passive abstraction.

**Approved openers (use freely, rotate):**

- `Atme durch.` / `Atme tief durch.`
- `Schnell.` / `Schnell handeln.`
- `Sofort.` / `Sofort melden — wirklich.`
- `Ruhig.` / `Ruhig bleiben.` / `Ruhig handeln.` / `Ruhig reingehen.` / `Ruhe bewahren.`
- `Klar.` / `Klar erklärt.` / `Klar denken.` / `Klare Schritte.`
- `Erst sortieren.` / `Erstmal hinsetzen.` / `Erstmal weiteratmen.` / `Erstmal anhalten.` / `Erst Abstand halten.` / `Erstmal ruhig.` / `Erstmal entschuldigen.`
- `Drei Schritte.` / `Ein Schritt nach dem anderen.`
- `Kein Drama.` / `Kein Streit.` / `Kein Streit nötig.`
- `Foto.` / `Foto machen, weiterpacken.`
- `Warnblinker an.`
- `Pech gehabt.` (only on `leicht` tone)
- `Ja, wirklich.` (acknowledgement opener — Day 28)
- `Sicher bleiben.` / `Sicher reingehen.`
- `Kleine Sache.` (only on `leicht` tone)

**Banned openers:**

- `Hallo`, `Hi`, `Liebe Zuschauer`, `Heute geht es um…`
- `Und`, `Also`, `Tja`, `Naja`, any filler particle
- `Wenn dir das passiert…` (passive, abstract — viewer has already had it happen, that's why the hook landed)
- `Im Schadenfall…` (legalese cold-open)

### E. CTA = calm invitation, never a command

End on a high-note that leaves the viewer feeling good, not pressured. Soft-sell. Local-advisor energy, not call-centre.

- ✅ `Lass uns gemeinsam schauen, was bei dir wirklich passt.`
- ✅ `Komm bei uns vorbei — wir nehmen uns Zeit für dich.`
- ❌ `Klicke jetzt!` / `Jetzt anrufen!` / `Heute noch abschließen!` / `Bevor es zu spät ist!`

Banned per `CAMPAIGN_BRIEF.md §Copywriting standards` and `provinzial-copy SKILL.md §7 Off-limits`.

---

## 4. CTA rotation pool

Eight base variants, no single CTA used more than 5 times across 30 rows. All hit ~10–13 words and follow rule E.

| # | CTA | Word count |
|---|---|---|
| 1 | `Lass uns gemeinsam schauen, was bei dir wirklich passt.` | 10 |
| 2 | `Komm bei uns vorbei — wir nehmen uns Zeit für dich.` | 11 |
| 3 | `Schauen wir deinen Schutz in einem ruhigen Gespräch an.` | 9 |
| 4 | `Komm vorbei — wir gehen deine Optionen einmal gemeinsam durch.` | 10 |
| 5 | `Schreib uns einfach — wir antworten, wenn du Zeit hast.` | 10 |
| 6 | `Bei uns im Büro: kurze Frage, klare Antwort, kein Druck.` | 10 |
| 7 | `Komm vorbei — wir kennen deine Region und deine Fragen.` | 10 |
| 8 | `Lass uns deinen Vertrag in Ruhe einmal gemeinsam durchgehen.` | 9 |

Plus scenario-specific variants (Familie-Schutz framing for kid/family scenarios; Vor-dem-Urlaub framing for travel scenarios; Wetter-Region framing for Sturm Day 28). All listed inline in the CSV.

---

## 5. POV — Du (inherited from Track A)

Following `HOOK_PROBLEM_brief.md §4`: all 30 scripts use **Du**, matching the hook cards. This is a deliberate override of `provinzial-copy SKILL.md §7` (which defaults to Sie for the advisor persona) — anchored by:

1. Track A precedent ("Dein Rohr platzt um 3 Uhr morgens.")
2. provinzial-copy §7 explicitly permits Du "on TikTok pieces aimed at younger families/first-time-buyers" when energy is casual — R61 cinematic + audio narration on broad social fits
3. Same-asset Du/Sie mixing is forbidden (provinzial-copy §7); hook is Du, so solution+CTA must be Du

If operator prefers Sie, mechanical swap: `du → Sie`, `dir → Ihnen`, `dein → Ihr`, `deine → Ihre`, `dich → Sie`, `bei dir → bei Ihnen`. CSV regenerates in <1 min.

---

## 6. Voice-tone field — inherited verbatim

The `voice_tone` column copies row-for-row from `hook_problems_30_days.csv` — same Day = same tone. This guarantees that the spoken solution carries the same emotional register the hook card set up.

Expected distribution (verified against Track A CSV):

| Tone | Days | Count |
|---|---|---|
| `familie` | 1, 2, 4, 14, 17, 21, 29 | 7 |
| `ernst` | 6, 7, 8, 9, 10, 11, 12, 27 | 8 |
| `leicht` | 5, 18, 19, 22, 23, 25 | 6 |
| `reif` | 3, 13, 15, 16, 20, 24, 26, 28, 30 | 9 |
| **Total** | | **30** |

Voice-tone shapes vocabulary register, not the building blocks:

- `ernst` — fewer light touches, more measured cadence ("Polizei rufen, dann uns — wir kümmern uns um alles andere.")
- `familie` — warm reassurance, family-scoped resolution ("Kinder bleiben Kinder, das wissen wir.")
- `leicht` — conversational, light irony OK ("Bahnfahren musst du trotzdem, leider.")
- `reif` — mature homeowner, resolution-detail-oriented ("Wir prüfen Vertrag und Verantwortung.")

---

## 7. Regulatory guardrails (provinzial-copy §2)

All 30 scripts are **care-promises**, not **coverage-promises**. Where a specific coverage statement appears, it carries a soft qualifier (`je nach Tarif`, `sofern abgedeckt`, `sofern dein Tarif passt`). Examples in the CSV:

- Day 9: `Schmuck mitversichert, sofern dein Tarif passt.`
- Day 20: `Privathaftpflicht zahlt, sofern abgedeckt.`
- Day 24: `E-Bike-Zusatzschutz greift, sofern du ihn hast.`
- Day 25: `Hausrat zahlt auch im Ausland, je nach Tarif.`

If a future edit introduces an unqualified payout/rate claim, legal review flag triggers.

---

## 8. Pillar

All 30 rows: **`Schaden & Service`** — single-pillar campaign, inherited from Track A. Matches `brand_brief.md §Content Pillars #3`.

---

## 9. Banned vocabulary (provinzial-copy §3 + CAMPAIGN_BRIEF §Copywriting)

The CSV is filtered against these:

- Buzzwords: `innovativ`, `ganzheitlich`, `auf Augenhöhe`, `Synergie`
- Urgency tricks: `Jetzt sichern!`, `Bevor es zu spät ist!`, `Heute noch abschließen!`, `Nur diese Woche!`
- Absolute claims: `immer`, `garantiert`, `100%` (around insurance outcomes)
- National-chain framing: `deutschlandweit`, `in jeder Region`, `Wir versichern Deutschland`
- Call-centre cadence: `Unsere Hotline ist 24/7 für Sie da`

---

## 10. What this brief does NOT touch

- R57 / R34 / n19 / n21 pipelines — out of scope for R61 voiceover scripts
- Airtable record creation — that's Track D (future scope, flagged in §12)
- Paid API calls — Track C is doc + CSV only, no ElevenLabs/Fal/Higgsfield invocations
- Blotato scheduling — voiceover scripts are produced for R61 stitch, not posted from this CSV
- Visual prompts / frame regeneration — visual layer is locked from the May 13 v3 batch (`content_library.md`)

---

## 11. Output

- `campaigns/Provinzial_Schaden_Campaign/solution_30_days.csv` — 30 rows, UTF-8, comma-delimited, header included, German umlauts preserved verbatim, fields with commas wrapped in double quotes per RFC 4180

---

## 12. Open items for operator review

1. **Compound-noun density** — confirm the moderate use of `Wohngebäudeversicherung`, `Privathaftpflicht`, `Wildunfallbescheinigung`, `Hundehalterhaftpflicht`, `Hausrattarif` is acceptable (these are insurance-domain terms the audience expects), or request a "plain-language" pass that swaps them for descriptive phrases.
2. **CTA pool size** — 8 base variants + scenario-specific variants gives ~3–4 reuses per CTA. Confirm acceptable, or request larger pool.
3. **Du vs Sie** — confirmation inherited from Track A; same swap mechanics apply if operator wants to revisit.
4. **Voice-tone derivation** — if Track A's voice-tone is later re-mapped (e.g. operator stands up `voice_library.md`), Track C CSV must be re-mapped in lockstep.
5. **Care-promise vs coverage-promise** — confirm the four soft-qualifier lines (Days 9, 20, 24, 25) are legally acceptable, or remove the coverage statement entirely.
6. **ElevenLabs payment** — solution VOs are written for production via ElevenLabs `eleven_multilingual_v2`; until payment unblocks (ticket at hello@trendivalux.com), Gemini TTS stand-in renders will be inferior. Confirm we hold the v2 batch until ElevenLabs is live (per `generation_notes.md` TODO #1).

---

## 13. Future scope (NOT this track)

- **Track D — Airtable CTA records:** create 30 new Day-prefixed CTA records in the R61 Airtable Video table (`tbl1hd8yprLTZia4c`) that point to May 13 visual sources and the new CTA voiceover scripts. Separate task; depends on this CSV landing.
- **Track E — HyperFrames stitch integration:** wire `solution_voiceover` + `cta_voiceover` into `hf_stitch.py --composition-mode schaden-v1` so the 4-beat assembly (hook → intro → solution → outro) renders end-to-end.
- **Track F — Caption pass:** word-by-word yellow-highlight caption rendering on top of the solution VO, driven by HyperFrames hf-seek. Already on `generation_notes.md` TODO #2.
