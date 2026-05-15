# GetAutomata Infrastructure — Agent Handoff

**Status:** active blocker list + scaling research brief
**Last updated:** 2026-05-15
**Audience:** next infrastructure agent (read this fully before touching anything)

---

## 1. Current State

### Cluster

- **Provider:** Hetzner Cloud, single node, region nbg1
- **Instance:** CAX21 (Arm64) — 4 vCPU, 8 GB RAM, 40 GB NVMe
- **Orchestrator:** k3s single-node (server + agent on same box)
- **Ingress:** Traefik (k3s default) behind Cloudflare Tunnel — no public IP exposed
- **Storage:** local-path-provisioner PVs on `/var/lib/rancher/k3s/storage/`
- **Tunnel daemon:** `cloudflared` running locally (not in cluster); config at `/etc/cloudflared/config.yml`

### Workloads currently scheduled

| Pod | Namespace | Limits | Notes |
|---|---|---|---|
| `n8n` | `n8n` | mem 1Gi, cpu 500m | Just bumped from 256Mi after canvas-merge OOMKills. `R2_ENDPOINT` env var added to pod spec this session so workflow nodes can resolve Cloudflare R2 without per-node config — keep it in the pod env, NOT in workflow JSON (so it survives PUT-overwrites). |
| (planned) ChromaDB | `memory` | TBD | not yet deployed |
| (planned) Obsidian sync sidecar | per-tenant | TBD | not yet deployed |

### Cloudflare Tunnel routes (locally managed `config.yml`)

| Hostname | Service | Purpose |
|---|---|---|
| `ssh-k3s.getautomata.ai` | `ssh://localhost:22` | Operator SSH into node |
| `k3s-api.getautomata.ai` | `https://localhost:6443` | kubectl from laptop (cert verify disabled in tunnel) |
| `ops.getautomata.ai` | `http://traefik-ingress` → n8n service | Operator-facing n8n UI + webhooks |

### Known issues (live)

1. **`N8N_PORT` env-var conflict.** k3s injects `N8N_PORT=tcp://<svc-ip>:5678` from the Kubernetes service of the same name into the n8n container, which the n8n process interprets as the *listen* port (it expects an integer). Workaround: explicit `env: [ {name: N8N_PORT, value: "5678"} ]` AFTER the auto-injected one in the pod spec, or rename the service so it stops shadowing. Rename is cleaner — TODO.
2. **OOMKill on large canvas operations.** Bulk n8n canvas writes (the 460-node merge) push the pod past 1Gi. 1Gi limit is a band-aid; underlying issue is n8n loading the entire workflow graph into memory during PUT. Either bump to 2Gi or split big writes into chunks via `n8n_update_partial_workflow`.
3. **`license:activate` CLI command missing.** Self-hosted n8n image we run does not ship the `license:activate` subcommand on the image tag pinned in the deployment. Means we cannot activate a license non-interactively — currently activated via UI. Pin a newer image OR script the activation via the licensing HTTP endpoint instead.
4. **Cloudflare Access blocking API paths.** Cloudflare Access policy on `ops.getautomata.ai` requires SSO for ALL paths including `/webhook/*` and `/api/*`. n8n webhooks are unauthenticated by design, so external callers (Modal → n8n) get bounced to the SSO login. Workaround in place: bypass policy for `path` starts-with `/webhook/`. Need to extend to `/rest/` for API-driven workflow management and audit which paths actually need Access vs. which need to remain open.

---

## 2. Scaling Architecture — Open Questions

**Current shape:** vertical only — one pod, bump limits when it falls over.

**Why this is wrong for SaaS:**
- No redundancy. Single pod restart = downtime for every tenant.
- Heavy workflow execution by one tenant degrades all tenants (noisy-neighbor).
- Limits per pod are coarse — cannot give tenant A 4Gi while tenant B gets 512Mi without separate deployments.

**The choice the next agent must make:**

### Option A — horizontal scale, shared n8n

- One n8n deployment, `replicas: N`, behind a shared service.
- Requires Redis (queue mode) + PostgreSQL (instead of SQLite) for shared state.
- Pros: cheapest, simplest scheduling.
- Cons: tenant isolation is logical only (one bad workflow can still hog Redis). License-per-tenant gets fuzzy.

### Option B — per-tenant pod (preferred default per GetAutomata thesis)

- One Deployment per customer. HPA per Deployment with per-tenant thresholds.
- Pros: full isolation. Crash blast radius = one tenant. Per-tenant resource billing trivial.
- Cons: more YAML to manage (mitigate with Helm chart + per-tenant `values.yaml`). N pods = N license seats.

**Recommendation to verify:** Option B with a Helm chart template. The whole GetAutomata pitch is "each client gets their own isolated stack" — shared n8n contradicts that.

### HPA inputs to research

- **Scale-up trigger:** memory 75% sustained 60s OR cpu 70% sustained 120s.
- **Scale-down cooldown:** 5 min — n8n cold-start is ~15s, too cheap to thrash.
- **Max replicas per tenant:** start at 3, revisit after watching usage.
- **Custom metric for queue depth:** if Option A, need prom-adapter on `n8n_queue_pending` — way better signal than CPU.

### Multi-node — when to add nodes

Add a second Hetzner node when **any one of** these is true:
- Single-node CPU steady-state >70% for >24h
- Total pod memory requests exceed 6Gi (leave headroom on 8Gi node)
- We onboard a third tenant (3 tenant pods + memory layer + control plane = too tight on one box)

### Cost/perf comparison to settle

| Instance | vCPU | RAM | NVMe | €/mo | Notes |
|---|---|---|---|---|---|
| CAX21 (current) | 4 Arm | 8 GB | 40 GB | ~7 | Arm — n8n image OK, ChromaDB image OK, check anything else |
| CX31 | 2 x86 | 8 GB | 80 GB | ~8 | x86 — broader image support, fewer cores |
| CCX13 | 2 dedicated x86 | 8 GB | 80 GB | ~13 | Dedicated CPU — no noisy-neighbor with other Hetzner tenants |

**Open question for next agent:** benchmark all three with a realistic n8n workload (R57 generation cycle) and pick the price/perf winner. Default thesis: CAX21 wins until we need x86-only images.

---

## 3. Customer Isolation Architecture

### Per-customer resources needed

- **n8n pod** — own Deployment, own PVC for `/home/node/.n8n` (workflows + creds DB)
- **Airtable base** — own base ID
- **R2 bucket prefix** — shared bucket, key prefix `{tenant_id}/` (cheaper than one bucket per tenant; R2 has no per-bucket quota benefit)
- **Obsidian vault space** — own folder under `obsidian-brain/clients/{tenant_id}/`
- **Telegram bot** — own bot token + allowlisted chat ID
- **L3 semantic memory** — own Chroma collection (see §4)

### Current state: manual

Provinzial is set up by hand — every resource above was provisioned manually. There is no script.

### Target: one-command onboarding

```
gax tenant new --id provinzial --display "Provinzial Geier & Ayhan" --plan standard
```

…should provision:
1. New Helm release `n8n-{tenant_id}` from the per-tenant chart
2. Airtable base (via Airtable Meta API) seeded from the template base
3. R2 prefix init (just an empty placeholder key, plus IAM policy update)
4. Obsidian folder from `obsidian-brain/templates/NEW_CLIENT_TEMPLATE/`
5. Telegram bot via BotFather *API equivalent* (BotFather has no public API → either pre-mint a bot pool and assign, or ask operator to run /newbot)
6. Chroma collection
7. Write `clients/{tenant_id}/README.md` from template
8. Emit summary card to operator Telegram

**Template starting point:** `obsidian-brain/templates/NEW_CLIENT_TEMPLATE/` already exists — reuse its folder layout.

---

## 4. Memory Layer (L3 Semantic)

### Goal

Before generating any new content (R57 image, R61 video, R55 short, copy), the agent first asks: *"have we done something similar for this client before, and how did it perform?"* — then conditions generation on what worked.

### Architecture (proposed)

- **Vector DB:** ChromaDB, one collection per tenant.
- **Hosting:** single ChromaDB Deployment, multi-collection. Per-tenant collection isolation is enough — full per-tenant DB is overkill at our scale.
- **Storage:** PVC backed by local-path-provisioner; offsite snapshot to R2 nightly.
- **Embedding model:** TBD — `text-embedding-3-large` (OpenAI) for English/German mixed, or `bge-m3` self-hosted if we want to keep generation purely in-cluster.

### What gets embedded

- Every generated asset's description + brand-voice notes (R57 image prompt + final headline; R61 video script + scene notes; R55 short title + hook)
- Every "winning" entry from `obsidian-brain/clients/{tenant}/winners.md`
- Brand voice docs from `obsidian-brain/clients/{tenant}/brand_voice.md`
- Performance metrics keyed by asset (post engagement, save rate, CTR — pulled from Blotato + native platform analytics)

### Integration points

| Pipeline | Hook | Behavior |
|---|---|---|
| R57 | before `generate_images.remote(...)` | Query top-5 similar past prompts for this tenant + their performance; include in system prompt context |
| R61 | before `frame_gen` | Same — find similar past openings/scenes + winner-flag if any |
| R55 | before clip selection | Find which historical clip topics performed; bias selection |

### Plugin choice — Pensyvee

Originally planned to use Pensyvee as the embedding/retrieval orchestration layer. **Re-evaluate in 2026:** Pensyvee was the right call when it was the only Chroma-aware plugin with n8n integration, but the space has moved. Verify before adopting:
- Is Pensyvee still actively maintained (last release date)?
- Does it support per-tenant Chroma collections out of the box, or do we wrap it?
- Alternatives to score: direct n8n `LangChain Vector Store: Chroma` node, raw ChromaDB HTTP, or LlamaIndex orchestration

---

## 5. Agent Prompt for Next Session

> You are the infrastructure architect for GetAutomata, a SaaS platform that provisions AI content automation stacks for marketing clients. Read this document fully (`obsidian-brain/knowledge/getautomata_infra_notes.md`). Your job is to design and implement: (1) horizontal pod autoscaling for n8n on k3s, (2) automated customer onboarding pipeline, (3) L3 semantic memory layer using ChromaDB per customer. Start by auditing the current k3s cluster state (`kubectl get all -A`, `kubectl top nodes`, `kubectl describe pod n8n-*`), then propose a detailed implementation plan with cost estimates before touching anything. Confirm with the operator on Telegram before any change that affects shared infrastructure — see `SOUL.md` for the standing approval rules.

---

## 6. Open TODOs (priority order)

1. **Rename n8n Kubernetes Service** to stop env-var shadowing (`N8N_PORT` issue) — 30 min, no risk
2. **Bump n8n memory to 2Gi** as a safety net while scaling architecture is being decided — 5 min
3. **Audit Cloudflare Access policy** on `ops.getautomata.ai` — list every path-prefix rule, decide which need SSO vs. which need bypass — 1 hr
4. **Helm chart for per-tenant n8n** — extract current Deployment/Service/Ingress/PVC into a chart with `values.yaml`. Test by re-deploying Provinzial through it — 1 day
5. **HPA POC** on Provinzial pod with memory-based scaling, observe over 1 week before adopting cluster-wide — 2 hr setup + 1 week passive
6. **ChromaDB deployment** + one tenant collection seeded from Provinzial's last 30 days of generated assets — 1 day
7. **`gax tenant new` CLI** — Python script wrapping the seven provisioning steps in §3 — 2 days
8. **Pensyvee evaluation note** dropped into this doc once research is done — 2 hr
