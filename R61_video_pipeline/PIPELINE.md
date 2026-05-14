# R61 Video Pipeline

Cinematic ad video pipeline for Provinzial. One row per daily video in the Airtable `Video` table (base `appC3HqG42ftswOvw`).

The pipeline is **human-gated** — Blotato never auto-posts, and four stitch/preview gates require explicit human confirmation before the next step runs.

---

## Workflow

### 1. First/Last frame generation
- **Model:** Nano Banana Pro or GPT Image 2 via Fal.ai.
- **Input:** the R57-generated image for this day, attached as `Source Image` on the Airtable row.
- **Output:** two stills written to `First Frame Image` and `Last Frame Image`. Prompts logged in `First Frame Prompt` / `Last Frame Prompt`.
- **Status transitions:** `Pending` → `Frames Generated`.

### 2. Video clip generation
- **Model:** Higgsfield (first/last frame → video clip). Skills live in `.claude/skills/higgsfield/`.
- **Output:** `Video Clip` attachment.
- **Status:** `Frames Generated` → `Clip Generated`.
- 🛑 **Human review gate #1** — operator inspects the clip in Airtable before continuing.

### 3. Raw footage pull from R2 bucket — MANUAL GATE
- **Source:** Cloudflare R2 bucket `trendiva-raw-assets`, manually edited raw footage.
- 🛑 **Human review gate #2** — operator confirms the exact file path (`Raw Footage URL`) before the pipeline proceeds. No automated pull.
- **Status:** `Clip Generated` → `Raw Attached`.

### 4. AI voiceover
- **Model:** Gemini TTS via Fal.ai.
- **Language:** German.
- **Script:** written per brand brief (`references/docs/provinzial_BRAND.md`) and saved to `Voiceover Script`. Audio saved to `Voiceover Audio`.
- **Status:** `Raw Attached` → `Voiceover Done`.

### 5. FFmpeg stitch
- **Explicit order:** intro → hook clip → raw footage → voiceover mixed with real voice segments → B-roll → outro.
- 🛑 **Human review gate #3** — every stitch point human-confirmed before execution. No auto-stitch.
- **Output:** stitched video (pre-final).
- **Status:** `Voiceover Done` → `Stitched`.

### 6. VFX overlay (optional)
- Manual subpipeline. Skip unless the day's brief calls for it.

### 7. Human review gate — full preview before export
- 🛑 **Human review gate #4** — operator watches full preview and either approves or rejects.
- **Status:** `Stitched` → `Approved` or `Rejected`. Rejected rows loop back to whichever step caused the defect.

### 8. Final export
- Export approved video to `Final Video` attachment.

### 9. Blotato schedule
- Schedule only — **do not post immediately** while the current hold is in effect.
- **Status:** `Approved` → `Scheduled`. `Scheduled Date` populated.

---

## Human review gates summary

| Gate | After step | What the operator confirms |
|------|------------|----------------------------|
| #1 | Step 2 — Clip Generated | Higgsfield clip quality, motion, frame coherence |
| #2 | Step 3 — Raw Attached | Correct R2 file selected for the day's ad |
| #3 | Step 5 — Stitched | Each stitch point in the FFmpeg ordering |
| #4 | Step 7 — Approved/Rejected | Full final preview before export |

## Folder layout

```
R61_video_pipeline/
├── .claude/skills/
│   ├── higgsfield/                       # higgsfield-generate, -marketplace-cards, -product-photoshoot, -soul-id
│   └── cinematic-ads/                    # SKILL.md
├── references/
│   ├── docs/provinzial_BRAND.md
│   ├── inputs/                           # daily source images, raw footage descriptors
│   └── outputs/                          # generated frames, clips, voiceovers, finals
├── tools/
│   └── requirements.txt
├── .env.example
├── .env                                  # never commit
└── PIPELINE.md
```

## External resources

- **Airtable base:** `appC3HqG42ftswOvw`, table `Video` (`tbl1hd8yprLTZia4c`)
- **R2 bucket:** `trendiva-raw-assets` (raw footage)
- **Fal.ai:** Nano Banana Pro / GPT Image 2 (frames), Gemini TTS (voiceover)
- **Higgsfield:** frame-to-video
- **Blotato:** scheduling only (posting paused)
