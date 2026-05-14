# Tools & Skills

All installed skills, MCPs and tools relevant to the CONTENT_PIPELINE work. Companion to [[lessons_learned#Skill listing budget mechanics]] for managing the loading budget.

## Skills — globally installed (`~/.claude/skills/`)

### Marketing
- **coreyhaines31/marketingskills** — 41 marketing skills: `copywriting`, `ad-creative`, `social-content`, `page-cro`, `seo-audit`, etc. Descriptions trimmed to < 130 chars on 2026-05-13.
- **zubair-trabzada/ai-marketing-claude** — `market` orchestrator + 14 `market-*` sub-skills + 5 agents in `~/.claude/agents/` + 4 Python scripts + 6 templates. Commands: `/market audit <url>`, `/market copy <url>`, `/market emails <topic>`, etc.
- **boraoztunc/skills/ogilvy** — Ogilvy copy principles (1972 book + Ogilvy on Advertising)
- **claude-ads** — multi-platform paid ads audit & optimisation (Google / Meta / YouTube / LinkedIn / TikTok / Microsoft / Apple). 250+ checks, scoring, parallel agents, industry templates, AI creative gen

### Style / output control
- **caveman** (`JuliusBrussee/caveman`) — ultra-compressed token mode (`lite` / `full` / `ultra`)
- **ogilvy** — see above
- **devil** — sharp red-team criticism, no fixes / padding
- **burst** — N variations of a request
- **align** — pre-work alignment check

### Video production
- **hyperframes** — HTML-based video composition (intro/outro, captions, transitions, audio-reactive). Used directly by [[../pipelines/R61_video_pipeline]] `hf_stitch.py`.
- **hyperframes-cli** — `npx hyperframes` dev loop (init, lint, inspect, preview, render, doctor)
- **hyperframes-media** — asset preprocessing: Kokoro TTS, Whisper transcribe, u2net background removal
- **hyperframes-registry** — install + wire registry blocks/components
- **cinematic-ads** — auto-build cinematic product ads from a single product input (GPT Image 2 + Seedance 2.0 Pro). Encodes cost-approval gate, content-policy traps, Fal storage upload, character lock, time-coded prompts. Lives at `R61_video_pipeline/.claude/skills/cinematic-ads/SKILL.md`.

### Animation adapters (for HyperFrames)
- **anime.js**, **css-animations**, **gsap**, **lottie**, **three**, **typegpu**, **waapi**

### Scraping / data
- **firecrawl** — scrape / crawl / map / search. Reads `FIRECRAWL_API_KEY` from `.env`.

### Brand / project-scoped
- **provinzial-copy** (project skill at `R61_video_pipeline/.claude/skills/provinzial-copy/`) — German copy rules for Provinzial campaign content. Overrides generic marketing skills. **Geier & Ayhan persona section is a TODO**, awaiting brief.

### Misc relevant
- **image** — Flux / Midjourney / DALL-E / Ideogram routing
- **video** — Remotion / HeyGen / Veo / Runway / Kling / Pika routing
- **ad-creative** — ad copy / RSA / Facebook+Google+LinkedIn ad text
- **ralph-loop** — looped agent runs
- **schedule** / **loop** — cron / dynamic recurring agents

### Stealth / research tooling
- **camofox** — stealth browser (Firefox-based, anti-detection) for content / competitor research
- **optillm** — multi-model optimisation router

## MCP servers (configured in `~/.claude.json`)

- **codegraph** — semantic code graph at `.codegraph/` (v0.7.3, 358 nodes, 636 edges in this repo)
- **claude.ai Figma** — Figma file read + Code Connect mapping + FigJam diagrams (not actively used here)
- **pencil** — `.pen` design editor (not actively used)
- **vault** — generic filesystem MCP (use sparingly — direct Read/Write is faster)
- **claude.ai Gmail / Google Calendar / Google Drive** — OAuth-gated, available but unused for Provinzial
- **medusa-dev** — Medusa ecommerce dev tools (unused in CONTENT_PIPELINE)

## CLI tools / pipelines

- `codegraph sync` — re-index the codebase after significant changes
- `python -m tools.frame_gen` / `video_gen` / `voiceover_gen` / `hf_stitch` / `blotato_schedule` (R61)
- HyperFrames CLI: `npx hyperframes init|lint|inspect|preview|render|doctor`

## Settings hot-spots

- `skillListingBudgetFraction` = **0.05 (5%)** in `~/.claude/settings.json` — raised from 1% on 2026-05-13 to load all marketing skills
- For per-repo plugin disables: `<repo>/.claude/settings.local.json` → `enabledPlugins: { ... : false }` (requires CC restart)

## What we deliberately did NOT install

- New MCPs beyond what's listed — the existing set covers everything currently needed
- Fictional skills / non-existent frontmatter fields ([[lessons_learned#Skill listing budget mechanics]])

## Related

- [[lessons_learned]]
- [[prompt_library]]
- [[n8n_credentials]]
- [[../agents/openclaw_marriage]]
