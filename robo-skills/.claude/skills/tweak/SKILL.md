---
name: tweak
description: Inject a live tweak panel into any HTML file (slides, websites, mockups). Auto-scans the page, picks reasonable sliders, lets the user dial in changes in browser, then bakes the chosen values back into the source CSS and removes the panel. Two levels — `tweak light` (5 sliders), `tweak max` (10 sliders).
---

# tweak

Drop a live controls panel into any single-file HTML output, let the user dial in changes in the browser, then bake the values back into the source.

## Triggers

- `/tweak [file]` → default level (light, 5 sliders)
- `/tweak light [file]` → 5 universal sliders
- `/tweak max [file]` → 10 sliders with finer-grained targets
- `tweak this` / `add tweak panel to this` (when a file is open or referenced)
- `bake tweak` / `tweak bake` → apply the user's dialed values back to source + remove panel
- `tweak strip` → remove panel without baking (revert)

If no file is given, infer from context (most recently edited HTML, the file the user has open in the IDE, or the active slide deck).

## Two levels

| Level | Slider count | Use when |
|---|---|---|
| **light** | 5 | Quick visual dial-in. Default. |
| **max** | 10 | Granular control — type sizes, spacing, glow, saturation. |

### Light tier (always 5)

1. **Speed** — multiplies `animation-duration` on every animated element
2. **Title size** — scales `h1` / `.display` / hero title font-size
3. **Body size** — scales `body` / `p` / `.body` font-size
4. **Density** — multiplies `padding` / `gap` on layout containers
5. **Visual scale** — `transform: scale()` on `svg`, `canvas` (excluding bg), `.visual`, `.iso-stage`, `.hero-image`

### Max tier (5 light + 5 more)

6. **Accent glow** — `filter: drop-shadow + brightness` on accent / hero areas
7. **Background** — opacity multiplier on bg layers (`#hexBg`, `body::before`, `.bg-layer`)
8. **Letter spacing** — `letter-spacing` on h1/h2/.display
9. **Roundness** — scales `border-radius` everywhere it's > 0
10. **Saturation** — `filter: saturate()` on `body`

The panel auto-skips sliders whose targets don't exist on the page (e.g. no `border-radius` anywhere → skip Roundness, fill the slot with the next candidate).

## Workflow

### Step 1 — Inject

When the user runs `/tweak [file]`:

1. Read `panel.html` from this skill folder.
2. Read the target HTML file.
3. Find `</body>` (last occurrence) and insert the **entire contents** of `panel.html` immediately before it. The bundle is wrapped in `<!-- TWEAK:START -->` ... `<!-- TWEAK:END -->` markers — these are required for `bake` and `strip` to work later.
4. Optionally pass a level hint by replacing `data-tweak-level="light"` with `"max"` on the `#tweak-panel` element if the user asked for max.
5. Save the file.
6. Open in the browser (`start "" "<path>"` on Windows, `open` on macOS, `xdg-open` on Linux).
7. Tell the user: panel is in, hit T to toggle, dial things in, then say "bake" when done.

**Idempotency:** if the file already contains `<!-- TWEAK:START -->`, don't inject again — tell the user it's already there and (re)open the file.

### Step 2 — User tweaks (in browser)

The panel:
- Auto-scans the DOM on load and picks the right sliders.
- For pages with multiple `.slide` elements, runs in **per-slide mode** (sliders target the visible slide).
- Otherwise runs in **page mode** (sliders target the whole document).
- Each slider has a value indicator and a reset.
- Header shows what's being targeted ("Page" or "Slide 03").
- **T** toggles the panel; **R** resets all on the active target; **B** opens the bake modal.

### Step 3 — Bake

When the user clicks **Bake** in the panel (or hits **B**), a modal appears with two options:

**Option A — Patch for the agent (default, recommended):**
A JSON block formatted as:
```
BAKE_TWEAK_v1
{
  "mode": "page" | "slide",
  "values": { "speed": 1.4, "titleSize": 1.1, "density": 0.9, ... },
  "perSlide": { "slide-1": { "speed": 0.8 }, "slide-2": { "scale": 1.15 } }   // only in slide mode
}
```
The user copies this and pastes it back to the agent.

When the agent receives a `BAKE_TWEAK_v1` payload, it:
1. Reads the source HTML file.
2. For each non-1.0 value in `values`, locates the relevant CSS rules and updates them in place, or injects a `<style id="tweak-baked">:root { ... }</style>` block right after `<head>` with custom-property overrides (whichever is cleaner — see "Bake strategy" below).
3. Strips the panel block — see **Stripping the panel** below for the safe procedure.
4. Saves the file.
5. Verifies the strip worked (re-grep for `TWEAK` — must return 0 matches), then confirms in chat: "Baked X changes, panel removed. Reload the file."

**Option B — Download baked HTML:**
The panel clones the document, strips the tweak block, inlines the deltas as a `<style>` near the top, and triggers a download. The user replaces the source manually if they prefer. Good for quick standalone exports.

### Bake strategy

- **Prefer in-place edits** for clarity — e.g. if Title Size = 1.15 and the source has `--title-size: clamp(2.6rem, 8vw, 7rem)`, multiply the values: `clamp(2.99rem, 9.2vw, 8.05rem)`.
- **Fall back to override block** when the source is too dense or uses computed values: insert a single `<style id="tweak-baked">:root { --tweak-mult-title: 1.15; }</style>` block + add a few helper rules. Keep it minimal — one block, scoped, easy to revert.
- For animation Speed bakes: rewrite each `animation` shorthand or `animation-duration` rule with the scaled value. Don't use a global multiplier var (CSS doesn't support computed durations from variables reliably across all browsers).
- For per-slide bakes: scope the CSS via `[data-title="..."]` attribute selectors or `.slide:nth-of-type(N)`.

### Step 4 — Strip

`tweak strip [file]` removes the panel without baking. Use the safe procedure in **Stripping the panel** below.

### Stripping the panel (CRITICAL — read before stripping)

**The trap:** the panel's own `<script>` source contains the literal string `TWEAK:END` and `-->` (inside a JS regex used by the in-browser download path). A naive lazy regex like `<!--\s*TWEAK:START[\s\S]*?TWEAK:END[\s\S]*?-->` will match the start marker, then jump to that JS-internal `TWEAK:END`, then close on the JS regex's own `-->/` — leaving the actual `<!-- TWEAK:END -->` marker plus a chunk of orphaned JS sitting outside any `<script>` tag. The browser then renders that orphaned JS as visible text on the page. This has happened. Don't repeat it.

**Safe procedure — pick one:**

**A. Line-range delete (recommended, most robust):**

```bash
# Find both marker line numbers
grep -n "<!-- TWEAK:START\|<!-- TWEAK:END" path/to/file.html
# Then delete that line range with sed (Windows: use node, see B)
sed -i "${START},${END}d" path/to/file.html
```

**B. Node strip with anchored regex (cross-platform):**

The end marker MUST be anchored as `<!--\s*TWEAK:END\s*-->` (not just `TWEAK:END[\s\S]*?-->`). The leading `<!--` is the discriminator — the JS-internal occurrence has `[\s\S]*?` before its `TWEAK:END`, never `<!--`.

```js
// node -e "..."
const fs=require('fs');
const p='path/to/file.html';
let s=fs.readFileSync(p,'utf8');
s=s.replace(/\n?<!--\s*TWEAK:START[\s\S]*?<!--\s*TWEAK:END\s*-->\n?/, '\n');
fs.writeFileSync(p,s);
```

Note the `<!--\s*TWEAK:END\s*-->` at the end — that's the fix. The JS regex string inside the panel does not contain `<!--` immediately before its `TWEAK:END`, so this pattern only matches the real closing comment.

**C. Edit tool with explicit anchors:**

If the file is small enough, do a single edit where `old_string` starts with `<!-- TWEAK:START · injected by .claude/skills/tweak · safe to remove between markers -->` and ends with `<!-- TWEAK:END -->\n`, and `new_string` is empty. Read the file first to copy the exact opening marker line.

**Always verify after stripping** — run `grep -c "TWEAK\|tweak-panel\|tweak-script\|bakedToCss\|renderRows" path/to/file.html`. Expected: `0`. If non-zero, the strip cut at the wrong spot — find the orphan and finish the job.

## Auto-scan rules

The panel.html script picks sliders in this order, skipping any whose targets don't exist:

| Priority | Slider | Target check (skip if 0 matches) |
|---|---|---|
| 1 | Speed | `*` with `getComputedStyle(el).animationName !== 'none'` |
| 2 | Title size | `h1, h1.display, .hero-title, .title-display` |
| 3 | Body size | `body` (always exists, never skipped) |
| 4 | Density | `.slide-content, section, .container, main, .layout, .grid, .stack` |
| 5 | Visual scale | `svg:not(.icon):not([data-bg]), canvas:not(#hexBg), .hero-image, .visual, .iso-stage, img.hero` |
| 6 | Accent glow | any element with `var(--accent)` resolved color OR `[data-accent]` OR `.accent` class |
| 7 | Background | `#hexBg, .bg-layer, [data-bg]` (or detect a `body::before` with low alpha) |
| 8 | Letter spacing | `h1, h2, .display` |
| 9 | Roundness | any element with `border-radius > 0` (compute style, sample first 50 elements) |
| 10 | Saturation | `body` (always works as a filter target) |

If the user asks `light` and fewer than 5 sliders qualify, show what we have. If they ask `max` and fewer than 10 qualify, fill what we can — the panel reports "8 of 10 sliders active — your page didn't expose roundness or accent areas."

## Mode detection (per-slide vs page)

On panel boot:
- If `document.querySelectorAll('.slide').length >= 2` AND scroll-snap is on the html or body, run **per-slide mode**.
- Otherwise run **page mode**.

Per-slide mode uses an IntersectionObserver to track which slide is visible and routes slider input to that slide's local state (cached per slide).

## What the skill does NOT do

- Click-to-select-element — we infer instead — keeps the v1 simple.
- Color picking (sliders only — saturation/glow are scalar; no hue picker).
- Layout shifts (no rearranging blocks; sliders only multiply existing values).
- Live editing of text content (visual-only).

If the user asks for any of these, tell them this skill is dial-in-only and they can either edit the source manually or use a proper component editor.

## Files in this skill

- **SKILL.md** — this file, the workflow
- **panel.html** — the self-contained CSS + HTML + JS bundle injected into target files. Has all the auto-scan logic, slider rendering, mode detection, and bake export.

## Rules (do not break)

1. The injected bundle MUST be wrapped in `<!-- TWEAK:START -->` ... `<!-- TWEAK:END -->` markers. Bake and strip both rely on these.
2. Never inject twice. Always check for the START marker before adding.
3. When baking via patch JSON, prefer in-place CSS edits over override blocks. Override blocks accumulate and rot.
4. After bake, ALWAYS remove the panel block — never leave it half-installed. Use the **Stripping the panel** procedure; the naive lazy regex will cut at the wrong spot because the panel's own JS contains the literal `TWEAK:END...-->` inside a regex string.
5. ALWAYS verify the strip with a `grep -c "TWEAK\|tweak-panel\|tweak-script\|bakedToCss\|renderRows"` — expect 0. If non-zero, fix it before reporting done.
6. Don't strip the bundle without confirming with the user if there are uncommitted slider changes (no way to detect — just warn that strip discards anything unbaked).
7. The panel itself never modifies the source file from the browser. All source mutations go through the agent (via the patch-back flow) or via the user's manual download replacement.
8. Default level is **light**. Don't surprise the user with 10 sliders unless they ask for `max`.
