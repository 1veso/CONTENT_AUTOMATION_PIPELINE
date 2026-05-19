# HOOK_PROBLEM — Schaden v1 Campaign Brief (Canva Bulk Create)

**Client:** Provinzial Geier & Ayhan (NRW Geschäftsstelle)
**Scope:** 30 static hook-problem cards for Canva Bulk Create — Schaden v1 campaign
**Format:** Yellow Montserrat Bold hook text on green sweep background, golden wings bottom-right
**Created:** 2026-05-19
**Status:** Draft for operator review (Track A of shovel-execution plan)

---

## 1. Purpose

Define the 30 hook problems that drive the Schaden v1 Canva static-card series. These cards are the **hook layer only** — Canva Bulk Create ingests the CSV (`hook_problems_30_days.csv`) and stamps each row onto the locked Trendiva Lux × Provinzial template.

This brief does **not** redesign the campaign — it narrows scope to the hook-card production track. Strategic frame, pillars, and pipeline assignments stay anchored in:

- `obsidian-brain/strategy/Mastermind_Plan_Content_Production_Engine.md` — campaign spine ("Schaden passiert. Provinzial bleibt ruhig.")
- `campaigns/Provinzial_Schaden_Campaign/CAMPAIGN_BRIEF.md` — overall Schaden v1 scope, 50-scenario backlog, pipeline mix
- `obsidian-brain/clients/Provinzial_Geier_Ayhan/brand_brief.md` — voice, colour, NEVER-list
- `obsidian-brain/clients/Provinzial_Geier_Ayhan/campaign_log.md` — 30-record campaign state + Schaden v1 sample (rec3QiBpC3N3cMZHN)
- `obsidian-brain/clients/Provinzial_Geier_Ayhan/content_library.md` — existing 30 R57 statics + 30 R61 clips
- `obsidian-brain/clients/Provinzial_Geier_Ayhan/generation_notes.md` — pillar-aware prompt patterns + voice rotation rationale
- `R57_content_engine/references/inputs/provinzial_BRAND.md` — visual identity + caption formula
- `R61_video_pipeline/.claude/skills/provinzial-copy/SKILL.md` — German copy rules (loaded for this brief)

**Note on missing source:** `obsidian-brain/clients/Provinzial_Geier_Ayhan/voice_library.md` was listed in the shovel plan but **does not exist in the repo**. Voice-tone field values in the CSV are derived from `generation_notes.md` voice rotation (Jones / Clara per pillar) and the CAMPAIGN_BRIEF tone rules — not from a dedicated voice library. Flagging here so the operator can either accept the derivation or stand up the missing file.

---

## 2. Format spec — locked template

| Element | Spec | Source |
|---|---|---|
| Aspect | 9:16 (Reels/Stories) | brand_brief §Image Prompt Defaults |
| Background | Provinzial green sweep `#005940` | brand_brief §Visual Identity (Logo-Grün / Hauptfarbe) |
| Hook text | Yellow `#FFD000`, Montserrat Bold | brand_brief §Visual Identity (CTA / Flügelgelb) + §Typography Feel |
| Watermark | Golden wings (Flügelgelb), bottom-right corner | brand_brief §Logo |
| Hook structure | 2 lines: setup (line 1) + payoff (line 2) | shovel-plan anchor + provinzial-copy §4 |
| Setup max chars | 50 | shovel-plan |
| Payoff max chars | 40 | shovel-plan |

**Brand-colour reconciliation:** The shovel-plan prompt referenced yellow `#FFDD00`. The authoritative source (`brand_brief.md` line 41, `provinzial_BRAND.md` line 41 — "Design-Richtlinien für Social-Media-Kanäle im Provinzial Konzern, Februar 2025") specifies `#FFD000`. **Using `#FFD000`.** Flag if operator wants to override.

---

## 3. Tone & voice

Anchored on `brand_brief.md` §Tone & Voice and `R61_video_pipeline/.claude/skills/provinzial-copy/SKILL.md`:

- Human, calm, NRW everyday realism
- No fear-mongering, no hype, no generic American insurance-ad look
- No buzzwords (`innovativ`, `ganzheitlich`, `auf Augenhöhe` — banned per provinzial-copy §3)
- No urgency tricks (`Jetzt sichern!`, `Bevor es zu spät ist!` — banned per CAMPAIGN_BRIEF §Copywriting standards)
- Spoken cadence — written to be scanned in 2 seconds (provinzial-copy §3)
- Concrete > abstract: "Dein Rohr platzt." beats "Im Falle eines Schadenereignisses."

**Regulatory guardrail (provinzial-copy §2):** Payoffs are **care-promises** ("Wir kümmern uns trotzdem."), not **coverage-promises** (no `je nach Tarif` needed because no specific payout / coverage / rate is stated). If a future edit introduces a specific coverage claim, legal review flag triggers.

---

## 4. POV — Du vs Sie

**Deviation logged from provinzial-copy §7:**

- provinzial-copy §7 defaults to **Sie** for the Geier & Ayhan agency persona (advisor speaking to customer).
- The shovel-plan anchor example uses **Du** ("Dein Rohr platzt um 3 Uhr morgens.").

**Resolution:** Using **Du** for this hook-card series because (a) the anchor example explicitly uses Du, and (b) provinzial-copy §7 itself permits Du "on TikTok pieces aimed at younger families/first-time-buyers, but only when the asset's overall energy is casual" — hook cards on broad social with conversational Trendiva-style cadence fit that exception. The advisor voice (Sie) belongs to spoken R61 dialogue, not 2-line hook captions.

If operator prefers Sie, the swap is mechanical: `Dein → Ihr`, `deine → Ihre`, `dich → Sie`, `dir → Ihnen`. CSV regenerates in <1 min.

---

## 5. Hook structure

Two-beat anchor (from shovel-plan + provinzial-copy §4):

```
Line 1 (setup):   The Schadenfall moment — concrete, observed, ≤50 chars
Line 2 (payoff):  Provinzial brand-care response — ≤40 chars
```

Reference examples (shovel-plan anchors, verbatim):

```
Dein Rohr platzt um 3 Uhr morgens.
Provinzial nimmt's auf.

Der Einbrecher war schneller weg als die Polizei da.
Wir kümmern uns trotzdem.
```

**Note:** The second example is 52 chars (over the 50-char setup limit). The CSV rows trim to comply with the stated limit while preserving the cadence.

**Payoff rotation pool (5 variants, no single payoff used more than 7 times across 30 rows):**

1. `Provinzial nimmt's auf.` (23)
2. `Wir kümmern uns trotzdem.` (25)
3. `Provinzial bleibt ruhig.` (24) — direct echo of the campaign spine
4. `Wir machen das.` (15)
5. `Wir sind schon dran.` / `Wir sind schon da.` (20 / 18) — variant
Plus minor case-specific variants: `Wir klären das.`, `Wir kümmern uns sofort.`, `Wir kümmern uns.`, `Provinzial weiß es.`, `Provinzial führt dich durch.`, `Wir nehmen's auf.`, `Sofort. Wir sind da.`

---

## 6. Theme distribution — 7 Schaden topics × 30 days

User-specified themes (from shovel-plan): **Leitungswasser, Einbruch, Wildunfall, Hagelschaden, Haftpflicht, Fahrraddiebstahl, Sturm**.

All 7 themes are pre-existing in the repo:

| Theme | Scenarios in CAMPAIGN_BRIEF.md backlog | Day count in CSV |
|---|---|---|
| Leitungswasser | #1 (Wasserrohrbruch), #2 (Nachbar), #8 (Schimmel), #36 (Wasserschaden 28), #39 (Hochzeitsreise) | 5 |
| Einbruch | #3 (Einbruch im Urlaub) + variations | 4 |
| Wildunfall | #18 (Wildunfall im Dunkeln) + variations | 4 |
| Hagelschaden | #15 (Hagelschaden) + variations | 3 |
| Haftpflicht | #21–#30 (10 scenarios available) | 5 |
| Fahrraddiebstahl | #6 (Fahrrad geklaut Bahnhof) + variations | 4 |
| Sturm | #4 (Sturm reißt Dachziegel), #40 (Sturmschaden Feb 2026) + variations | 5 |
| **Total** | | **30** |

Distribution rationale:
- **5 days** for Leitungswasser, Haftpflicht, Sturm — broadest scenario pool per CAMPAIGN_BRIEF (10 Wohnen, 10 Haftpflicht, multiple Sturm angles)
- **4 days** for Einbruch, Wildunfall, Fahrraddiebstahl — narrower but distinct scenario angles
- **3 days** for Hagelschaden — fewest documented angles in repo; padding would require invented content

**No invented themes.** All 7 themes appear in `CAMPAIGN_BRIEF.md §Schäden scenarios — content backlog (50 angles)`.

**Within-theme variation logic** (allowed per shovel-plan: "distribute with variations rather than invent"):
- Each theme uses 1–2 base scenarios from the CAMPAIGN_BRIEF backlog
- Variations rotate POV angle (timing — "3 Uhr morgens" vs "über Nacht"; setting — "Bahnhof" vs "Urlaub"; severity cue — "Schloss noch dran" vs "spurlos")
- No new Schaden type introduced

---

## 7. Voice-tone field — derivation

`voice_library.md` does not exist in the repo (flagged in §1). The CSV `voice_tone` column uses 4 values derived from:

- `generation_notes.md` voice-rotation pattern (Jones male / Clara female by pillar parity)
- `CAMPAIGN_BRIEF.md` §Strategic angle (calm, human, never fear-mongering)

| voice_tone | Use case | Mapped scenarios |
|---|---|---|
| `ernst` | high-stakes, violation, shock moments | Einbruch (all 4), Wildunfall (3 of 4), one Sturm (Baum auf Carport) |
| `familie` | home, kids, partner, everyday family situations | Leitungswasser (3), Hagel-Familienauto, Kind-mit-Ball Haftpflicht, Umzug Möbel, Markise |
| `leicht` | smaller annoyances, conversational, lighter Schäden | Fahrraddiebstahl (3 of 4), Hund/Glas/Restaurant Haftpflicht, "erster Wasserschaden mit 28" |
| `reif` | mature homeowner, resolution-focused, complex Schäden | Schimmel, Wildunfall reflection, Hagelsturm wann melden, Schließanlage, E-Bike, Sturm (3 of 5) |

If operator stands up `voice_library.md` later, the CSV `voice_tone` column can be re-mapped via a 30-row sed pass.

---

## 8. Pillar

All 30 rows: **`Schaden & Service`** — single-pillar campaign per shovel-plan and CAMPAIGN_BRIEF §Pipeline-by-pipeline assignment. Matches `brand_brief.md` §Content Pillars #3 verbatim ("Schaden & Service — What happens when things go wrong — fast, human, reliable").

This is narrower than the existing 30-record R61 calendar (`campaign_log.md`), which spans 5 pillars. Hook-card series is Schaden-only.

---

## 9. What this brief does NOT touch

- R57 / R61 / R34 / n19 / n21 pipelines — out of scope for static Canva cards
- Airtable records — CSV is for Canva Bulk Create, not Airtable
- Paid API calls — Track A is doc + CSV only
- Blotato scheduling — hook cards are produced in Canva, not posted from this CSV

---

## 10. Output

- `campaigns/Provinzial_Schaden_Campaign/hook_problems_30_days.csv` — 30 rows, UTF-8, comma-delimited, header included, German umlauts preserved verbatim

---

## 11. Open items for operator review

1. **`#FFDD00` vs `#FFD000`** — confirm brand-brief value (`#FFD000`) is the intended yellow.
2. **Du vs Sie** — confirm Du is acceptable for hook-card series, or request Sie variant.
3. **`voice_library.md` missing** — confirm the derived 4-value voice-tone mapping (`ernst / familie / leicht / reif`) is acceptable, or stand up the missing file.
4. **Hagelschaden = 3 days** — confirm low day-count is acceptable, or accept invented variations to balance to 4.
5. **Payoff rotation** — confirm the 5-variant pool is final, or request alternate phrasings.
