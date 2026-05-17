# Provinzial Pipeline — Secrets Bootstrap

Use this doc when standing up the pipeline on a new machine. Every required env key, where it lives, where to retrieve it.

> **Sister doc:** [[portability_checklist]] — tick-box list of every artifact that must travel.

---

## R61_video_pipeline/.env — required keys

### Airtable

| Key | Purpose | Source | Regenerate? |
|---|---|---|---|
| `AIRTABLE_API_KEY` | Read/write the `Video` table (`tbl1hd8yprLTZia4c`) and the R57 `May2025 - Provinzial_Geier&Ayhan` table | https://airtable.com/create/tokens — "Personal access tokens" | **Yes** — create a new PAT scoped to base `appC3HqG42ftswOvw` with `data.records:read`, `data.records:write`, `schema.bases:read`. No billing impact. |
| `AIRTABLE_BASE_ID` | Static — `appC3HqG42ftswOvw` (shared with R57) | Hardcoded in `.env.example` | N/A — copy as-is. |

Account: `trendivalux@gmail.com` (also Airtable workspace owner).

### ElevenLabs

| Key | Purpose | Source | Regenerate? |
|---|---|---|---|
| `ELEVENLABS_API_KEY` | TTS voiceover for R61 stitched videos. Pipeline uses the official ElevenLabs SDK (see `voiceover_gen.py`). | https://elevenlabs.io/app/settings/api-keys | **Yes** — rotating the key does not change cloned voices or character quota. No billing impact. |

Pricing: per character. Watch monthly character quota.

### Higgsfield

| Key | Purpose | Source | Regenerate? |
|---|---|---|---|
| `HIGGSFIELD_API_KEY` | First/last-frame video synthesis (Gate 1 input). | https://higgsfield.ai/account/api | **Maybe** — Higgsfield's dashboard may not surface the secret a second time after first generation. **Copy the existing values; do not regenerate unless you've already lost them.** |
| `HIGGSFIELD_SECRET` | HMAC signing key paired with the API key. | Same dashboard. | Same warning — Higgsfield only shows the secret once at creation. |

Cost: per-clip generation fee. Regenerating keys does not bill, but losing access mid-batch forces a re-queue from scratch.

### Google

| Key | Purpose | Source | Regenerate? |
|---|---|---|---|
| `GOOGLE_API_KEY` | Gemini API — caption polish + narrative script generation in `script_gen.py`. | https://aistudio.google.com/app/apikey | **Yes** — free-tier eligible. No billing impact. |

### Fal.ai

| Key | Purpose | Source | Regenerate? |
|---|---|---|---|
| `FAL_KEY` | Frame gen (`fal-ai/nano-banana/edit`), video gen (`fal-ai/kling-video/v2.1/master/image-to-video`, `fal-ai/sora-2/image-to-video/pro`), Gemini TTS (`fal-ai/gemini-tts`). | https://fal.ai/dashboard/keys | **Yes** — keys are independent of billing balance. Pre-paid credits sit at the account level. |

Pricing: per second of output. See `R57_content_engine/tools/config.py` `COSTS` table. Always quote USD before generation per CLAUDE.md rule 2.

### Cloudflare R2

| Key | Purpose | Source | Regenerate? |
|---|---|---|---|
| `R2_ACCOUNT_ID` | Cloudflare tenant ID. Public — visible at the top-right of the R2 dashboard. | https://dash.cloudflare.com/ — R2 | N/A — never changes. |
| `R2_ACCESS_KEY_ID` | S3-compatible access key for `trendiva-raw-assets` bucket. | https://dash.cloudflare.com/ — R2 — "Manage R2 API Tokens" — "Create API token" | **Yes** — issue a new token scoped to the bucket. Old keys remain valid until manually deleted, so safe to rotate. |
| `R2_SECRET_ACCESS_KEY` | Paired secret. | Same dashboard — **shown ONCE at creation, capture immediately.** | Same as above. Cloudflare does not let you retrieve the secret after the create dialog closes. |
| `R2_BUCKET_NAME` | Static — `trendiva-raw-assets` | Hardcoded. | N/A. |
| `R2_PUBLIC_URL` | Public bucket alias `https://pub-596ca4afabd54a3883ded26dc489279d.r2.dev` (Blotato reads from here). | R2 — bucket — Settings — "Public Access" — r2.dev subdomain. | N/A unless the public alias is rotated (rare). |

**Known footgun:** local clock skew. See [[../../knowledge/r2_clock_skew_workaround]] — boto3 to R2 needs a `botocore.utils.get_current_datetime` monkey-patch on this machine. Verify the patch is still in `R61_video_pipeline/tools/r2_upload.py` after migration.

### Blotato

| Key | Purpose | Source | Regenerate? |
|---|---|---|---|
| `BLOTATO_API_KEY` | Schedule social posts (TikTok / Meta / Instagram). Schedule-only — never immediate post. | https://blotato.com/settings — "API keys" | **Yes** — connected social accounts are attached at the workspace level, so rotating the API key does not unlink TikTok/Meta/IG. No billing impact. |

Connected-account IDs are looked up at request time from Blotato's `/v2/accounts` endpoint; no need to copy account IDs into env.

---

## R61_* feature flags

Currently set in `.env`:

| Flag | Current | Gates / controls |
|---|---|---|
| `R61_ADD_CAPTIONS` | `1` | When `1`, `hf_stitch.py` runs the caption-burn pass against the Whisper transcript and overlays kinetic captions on the final render. When `0`, the final render is caption-free (clean for platforms that auto-caption). |
| `R61_BROLL_ENABLED` | `1` | When `1`, the stitch pipeline injects B-roll / VFX inserts at script-defined timestamps. When `0`, single-shot output only. |
| `R61_NARRATIVE_MODE` | `1` | When `1`, `script_gen.py` produces a three-act narrative structure (hook — tension — resolution) and the prompt builder consumes those beats. When `0`, falls back to a single-prompt mode (legacy v1/v2 behaviour). |
| `R61_VERSION_TAG` | `v4` | Output-path version namespace. Per the never-delete-old-content rule: new renders always land under a NEW version path. Never reuse an old tag. |

To toggle a flag, edit `.env` directly and re-run the affected stage; flags are read fresh on each pipeline invocation.

---

## Migration steps for a new machine

1. **Install runtime.** Python 3.11+, Bun (`C:\Users\benja\.bun\bin\bun.exe` on the source machine — install fresh on the new one). Ensure FFmpeg is on `PATH` (`ffmpeg -version` works).
2. **Clone the repo.** `git clone <remote-url> CONTENT_PIPELINE && cd CONTENT_PIPELINE`. The repo will pull all tracked code, the canonical `references/inputs/*.png`, `references/inputs/intro.mp4`, `references/inputs/outro_5s_audio_DEPRECATED.mp4`, and `references/outputs/outro.mp4` — these now travel with the repo (see `.gitignore` notes from the portability pass).
3. **Install Python deps.** `cd R61_video_pipeline && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt` (and likewise for `R57_content_engine` and `R55_clipper_agent`).
4. **Create `.env`.** `cp .env.example .env` then fill each `<YOUR_..._HERE>` placeholder using the tables above. The R2 secret and Higgsfield secret **cannot be re-derived** — if you do not have them, you must regenerate (Cloudflare safe; Higgsfield see warning).
5. **Verify R2 clock-skew patch is active.** `python -c "from R61_video_pipeline.tools import r2_upload; print(r2_upload.r2_client().list_buckets())"` — must succeed. If it 403s, the clock-skew monkey-patch is not applied; see [[../../knowledge/r2_clock_skew_workaround]].
6. **Smoke-test Airtable.** Pull one record: `python -c "import sys; sys.path.insert(0, 'R61_video_pipeline'); from tools import airtable_video as av; print(av.get_record(av.list_records()[0]['id'])['fields'].get('Day'))"` — should print a Day number.
7. **First voiceover_gen run.** Pick a record already at `Scheduled` status and dry-run the voiceover stage: `python R61_video_pipeline/tools/voiceover_gen.py --record-id <rec...> --dry-run` (if the tool exposes `--dry-run`) — otherwise pick a record where re-running TTS is acceptable (cost: ~$0.01 per record at ElevenLabs character rates).
8. **Re-create crons.** On startup of the new ClaudeClaw session, the agent reads `cron-registry.json` and re-registers every enabled cron via `CronCreate`. Confirm the three cron IDs (`morning-summary`, `keepalive`, `r61-gate-watcher`) register successfully.
9. **Telegram allowlist.** The Telegram bot allowlist is keyed to `chat_id 1077552316` — that is per-user, not per-machine. New machine inherits it automatically once the same bot token is in `.claude/telegram/.env`.
10. **Modal CLI.** If the new machine will deploy: `pip install modal && modal token new`. Workspace `hello-58046`. Secrets (`r57-secrets`, `r61-secrets`, `vizard-clipper-secrets`) live in Modal, not locally — they do not need to travel.

---

## Things that do NOT travel with the repo

- `R61_video_pipeline/.env` — must be recreated from `.env.example`.
- Render outputs (`references/outputs/v3/`, `v4/`, day-N final files) — these are large and per-batch; pull from R2 if needed.
- `obsidian-brain/clients/**/assets/**` — heavy binary assets stay local. Re-download brand assets from source on the new machine if needed.
- `shared/gates/pending.json` — runtime state, not source-controlled.
- Modal secrets — already persisted in the Modal workspace; new machine just needs `modal token new`.
- `.claude/telegram/.env` — bot token; recreate on the new machine via `/telegram:configure`.
