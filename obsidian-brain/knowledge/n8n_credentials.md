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

## Operational rules (n8n API — learned 2026-05-19)

Hard-won during the canvas activation incident. Read before writing to `SmtkmTgfCTLZPlN4` (or any large n8n workflow):

1. **MCP `n8n_update_partial_workflow` auto-sanitizes the WHOLE workflow on every call.** Any partial-update op type can strip required fields from nodes you never touched — confirmed: `parameters.path` wiped from all 17 webhook shims and `parameters.operation` from 5 Telegram nodes after a 12-node schedule-trigger disable batch using `updateNode {disabled, parameters}`. Use `disableNode` op or direct REST PUT instead of `updateNode {disabled, parameters}`.

2. **For high-risk writes, bypass MCP entirely — use direct REST PUT/GET.** Python subprocess pattern:
   - Read `N8N_API_KEY` + `N8N_API_URL` from `~/.claude.json` under `mcpServers."n8n-mcp".env`
   - Send `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36` — without it Cloudflare returns Error 1010 (browser-signature ban) before the request reaches n8n. The API key is the actual auth.
   - PUT body: `{name, nodes, connections, settings, staticData?}`. Exclude `id`, `active`, `createdAt`, `updatedAt`, `versionId` — they're read-only.
   - Verified payload 396KB PUT in 2.4s; 680KB GET in 1.8s on the 1Gi pod.

3. **`active` is read-only on `PUT /workflows/{id}`.** Returns HTTP 400 `"request/body/active is read-only"`. Activation requires `POST /workflows/{id}/activate` separately.

4. **RESOLVED — "Too Many Requests" activation block (root cause, permanent fix):**
   The HTTP 400 `"The service is receiving too many requests from you"` had TWO independent causes both surfacing the SAME generic message:

   **CAUSE 1 — Proxy IP-collapse (tenant-wide throttle):**
   - n8n's Express rate-limiter keys on client IP. Behind the Cloudflare tunnel, every request (UI, MCP, API, ClaudeClaw, webhooks) arrived as the SINGLE tunnel IP because n8n wasn't trusting X-Forwarded-For.
   - All traffic shared ONE rate-limit bucket. A burst of activation retries drained it tenant-wide; nothing could activate until the window cleared. Survived pod restarts, hit all access methods, returned HTTP 400 not 429.
   - **PERMANENT FIX:** `N8N_PROXY_HOPS=1` on the n8n deployment → n8n trusts the one proxy hop and rate-limits per REAL client IP.
     `kubectl set env deployment/n8n -n user-40911a6c N8N_PROXY_HOPS=1`
   - NOTE: hop value must equal the real proxy chain length. Cloudflare tunnel only = 1. If an ingress controller also sits in front of n8n = 2. Verify the chain; wrong count = still misreads IP.

   **CAUSE 2 — telegramTrigger activation-registration failure:**
   - 6 `telegramTrigger` nodes fail at activation time (Telegram polling registration errors), and n8n reports that failure via the same generic "too many requests" string.
   - FIX: re-add the 6 triggers in UI with credential `lux_bot` bound (`telegramTrigger` cannot be PUT via public API). If registration fails again, check the bot token / getUpdates conflict, not rate limits.

   The earlier "it aged out after 5+ days idle" was NOT a fix — that was just the throttle window expiring. `N8N_PROXY_HOPS=1` is what prevents recurrence. Validate workflow to `errorCount: 0` BEFORE first activation attempt — every failed activate burns the budget without succeeding.

5. **Workflow versions exist (`n8n_workflow_versions list`) but `rollback` mode requires an admin token not provisioned to the current PAT.** Read-only `list`/`get` work fine — use as forensic/recovery context, not as a write recovery path on this hosting.

## Related

- [[lessons_learned]]
- [[tools_and_skills]]
- [[model_costs]]
