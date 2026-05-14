// generate.mjs — Step 3: build the storyboard sheet on GPT Image 2 (via Fal)
//
// Usage:
//   1. Put FAL_KEY=fal_... in a .env file in the working directory
//   2. Edit BRAND, PRODUCT, REFS, and PROMPT below
//   3. Run: node generate.mjs
//
// Output: gpt2_{slug}_{timestamp}.png in ./out/
//
// The skill (.claude/skills/cinematic-ads/SKILL.md) covers all the rules:
// 7 storyboard rules, content-policy traps, panel-count cheat sheet, mannequin
// face workaround for human ads, prompt template.

import fs from 'node:fs';
import path from 'node:path';

// --- env -------------------------------------------------------------------
const envText = fs.existsSync('.env') ? fs.readFileSync('.env', 'utf8') : '';
const FAL_KEY = (envText.match(/^FAL_KEY=(.+)$/m) || [])[1]?.trim() || process.env.FAL_KEY;
if (!FAL_KEY) { console.error('FAL_KEY missing — add it to .env or export it'); process.exit(1); }

// --- edit these ------------------------------------------------------------
const BRAND = 'YOUR_BRAND';
const PRODUCT = 'YOUR_PRODUCT';
const SLUG = `${BRAND}_${PRODUCT}`.toLowerCase().replace(/\s+/g, '_');

// 1-4 product reference URLs. Brand CDNs work; Amazon/catbox/litterbox don't.
// For local files, use the Fal storage upload pattern (see animate.mjs).
const REFS = [
  'https://example.com/product-hero.jpg',
  'https://example.com/product-flat.jpg',
  'https://example.com/product-detail.jpg',
];

// Storyboard prompt — see SKILL.md "Storyboard prompt template".
// Replace each {placeholder}. 6 panels for a 15s ad, 12 panels for 30s.
const PROMPT = `A single image: a 6-panel cinematic ad storyboard sheet, 3 columns by 2 rows, on an off-white paper background with a thin black border. Each panel is a cinematic film still in 16:9 landscape orientation. Above the grid, a bold mono header reads:

STORYBOARD: {CONCEPT NAME} — 15s SPOT — BRAND: ${BRAND}     PRODUCT: ${PRODUCT}

Each panel has a small "01"–"06" number top-left AND a clean monospace timestamp badge top-right (e.g. [0:00–0:02.5]). Beneath each panel sits a 3-line monospace caption block:
  SCENE: <label>
  ACTION: <one short camera/motion sentence>
  SOUND: <music or SFX cue>

CRITICAL — PRODUCT FIDELITY: match the silhouette, materials, colorway from @Image refs exactly. Keep small wordmarks as illegible texture if not readable.

CRITICAL — CHARACTER LOCK (humans only — DELETE THIS LINE for product-only ads): {character description, late-twenties woman with light freckles + soft natural skin, no clinical pores/imperfections language}. If you plan to animate humans on Seedance, render the face as MANNEQUIN or SOFT BLUR and let Seedance fill it in.

AESTHETIC: {one paragraph — lens, lighting, mood, palette, location.}

PANELS (timestamped for a 15-second spot @ 2.5s per beat):
01 [0:00–0:02.5] SCENE: ... | ACTION: ... | SOUND: ...
02 [0:02.5–0:05.0] SCENE: ... | ACTION: ... | SOUND: ...
03 [0:05.0–0:07.5] SCENE: ... | ACTION: ... | SOUND: ...
04 [0:07.5–0:10.0] SCENE: ... | ACTION: ... | SOUND: ...
05 [0:10.0–0:12.5] SCENE: ... | ACTION: ... | SOUND: ...
06 [0:12.5–0:15.0] SCENE: END CARD | ACTION: clean plate, wordmark, CTA | SOUND: ...

End-card text (panel 06 only): "${BRAND} — ${PRODUCT}. {TAGLINE}. {DOMAIN}"

Render the full storyboard as ONE single image, 3×2 grid landscape. Captions legible in monospace. No watermarks. No extra text. Same product every panel.`;

// --- run -------------------------------------------------------------------
const OUT = path.resolve('./out');
fs.mkdirSync(OUT, { recursive: true });

const body = {
  prompt: PROMPT,
  image_urls: REFS,
  image_size: { width: 2560, height: 1792 },
  quality: 'high',
  num_images: 1,
  output_format: 'png',
};

console.log(`[${SLUG}] Submitting to GPT Image 2 (high quality, 2560x1792)...`);
const t0 = Date.now();
const res = await fetch('https://fal.run/openai/gpt-image-2/edit', {
  method: 'POST',
  headers: { Authorization: `Key ${FAL_KEY}`, 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});
const json = await res.json();
console.log(`[${SLUG}] Returned in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
if (!json.images?.length) { console.error('NO IMAGES:', JSON.stringify(json)); process.exit(1); }

const ts = Date.now();
const fname = `gpt2_${SLUG}_${ts}.png`;
const buf = Buffer.from(await (await fetch(json.images[0].url)).arrayBuffer());
fs.writeFileSync(path.join(OUT, fname), buf);
console.log(`[${SLUG}] Saved: ${path.join(OUT, fname)}`);
console.log(`[${SLUG}] Cost: ~$0.18`);
