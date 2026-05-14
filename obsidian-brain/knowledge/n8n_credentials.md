# n8n Credentials Master List

Every credential referenced across the n8n templates in this repo. Live keys for Provinzial are in `R57_content_engine/references/.env` and `R61_video_pipeline/.env` — never commit. Use this page as the canonical list when standing up any new n8n instance or routing the templates to a fresh account.

## API keys

| Service | Env var | Used by |
|---------|---------|---------|
| Telegram Bot | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | [[../pipelines/R55_clipper]] |
| OpenAI | `OPENAI_API_KEY` | R46, R51, R39, n3, n29 (LLM + transcribe) |
| OpenRouter | `OPENROUTER_API_KEY` | R39, R51 (multi-LLM router) |
| Fal.ai | `FAL_API_KEY` (bridged to `FAL_KEY` in R57 `config.py`) | R57, R61, n21 (post KIE migration), n30, n31, n29 (Sora route) |
| Wavespeed | `WAVESPEED_API_KEY` | optional R57 image-gen route (currently unused) |
| KIE AI | **DEPRECATED — replace with Fal** | n21 templates still reference; must migrate before live use |
| Airtable | `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID` | R57, R61, R46, R51, R34, R39, n16, n21, n29, n30, n31 |
| OpenRouter | `OPENROUTER_API_KEY` | duplicates listed for clarity |
| Google AI (Gemini + Veo + TTS) | `GOOGLE_API_KEY` | R61 (Gemini TTS temp), R34 (Veo), n16 (Veo) |
| Apify | `APIFY_TOKEN` | R46, n29 (source video pull) |
| Cloudinary | `CLOUDINARY_URL` | n3, n16.1, n21 (media handoff) |
| Box | `BOX_CLIENT_ID`, `BOX_CLIENT_SECRET`, `BOX_*` | R39 (FYI Box setup), n29, n3 |
| Blotato | `BLOTATO_API_KEY` | R55, R57, R61, n3, n21 (all posting) |
| ElevenLabs | `ELEVENLABS_API_KEY` | R61 (target voice — payment processing), n3, n16.1 |
| Higgsfield | `HIGGSFIELD_API_KEY`, `HIGGSFIELD_SECRET` | R61 |
| Cloudflare R2 | `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL` | R61 |
| NCA Toolkit | `NCA_TOOLKIT_*` | n16.1, n3 |
| Vizard | `VIZARD_API_KEY` | R55 (via Modal secret) |

## Modal secrets

- `vizard-clipper-secrets` — R55 Modal deployment

## Where keys live

- `R55_clipper_agent/` — `.env.example` for shape; live keys in Modal secret
- `R57_content_engine/references/.env` — Provinzial live keys
- `R61_video_pipeline/.env` — Provinzial live keys

## Hold

[[lessons_learned#Blotato hold|Blotato posting is paused]] — schedule only, even though the credential is wired in every template.

## Manual import steps

- R51 import: point Airtable nodes to PAT credential with data.records:read+write on appC3HqG42ftswOvw
- R34 import: point Fal credential to FAL_KEY, point Airtable nodes to PAT credential

## KIE → Fal migration

[[../pipelines/integrations/n21_infinite_ugcs#KIE → Fal migration note|n21]] is the main template still on KIE; do not run it until the swap to Fal slugs is done.

## Related

- [[lessons_learned]]
- [[tools_and_skills]]
- [[model_costs]]
