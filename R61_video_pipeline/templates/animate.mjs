// animate.mjs — Step 4: animate the storyboard with Seedance 2.0 Pro (via Fal)
//
// Usage:
//   1. Put FAL_KEY=fal_... in a .env file in the working directory
//   2. Edit STORYBOARD path, PRODUCT_REF_URL, and PROMPT below
//   3. Run: node animate.mjs
//
// Output: seedance2p_{slug}_{duration}s_{resolution}_{timestamp}.mp4 in ./out/
//
// IMPORTANT (per SKILL.md):
//   - Always reference BOTH @Image1 (storyboard) AND @Image2 (clean product photo)
//     in the prompt. Skipping @Image2 is the #1 cause of product drift.
//   - Cost: 720p ~$0.30/sec ($4.54 for 15s). 480p ~$0.18/sec for cheap tests.
//   - Default tier is Pro, not Fast.

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

const STORYBOARD = './out/gpt2_your_brand_your_product_TIMESTAMP.png'; // path to Step 3 output
const PRODUCT_REF_URL = 'https://example.com/product-hero.jpg';        // clean product photo (brand CDN URL)

const RESOLUTION = '720p';   // '720p' for finals, '480p' for cheap tests
const DURATION = '15';       // 4-15 seconds, or 'auto'

// Default = simple prompt (1-3 sentences, trust the storyboard).
// ALWAYS reference both @Image1 (storyboard) AND @Image2 (product) explicitly.
const PROMPT = `Turn this storyboard (@Image1) into a cinematic ${DURATION}-second ad. Match the ${BRAND} ${PRODUCT} colorway and silhouette exactly using @Image2 as the clean product reference — pristine in every beat. Music + ambient sound design only, no dialogue.`;

// --- upload storyboard to Fal storage --------------------------------------
async function uploadToFal(filePath, contentType) {
  const buf = fs.readFileSync(filePath);
  const init = await fetch('https://rest.alpha.fal.ai/storage/upload/initiate', {
    method: 'POST',
    headers: { Authorization: `Key ${FAL_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ content_type: contentType, file_name: path.basename(filePath) }),
  });
  const { upload_url, file_url } = await init.json();
  if (!upload_url) throw new Error('Fal storage init failed: ' + JSON.stringify(init));
  await fetch(upload_url, { method: 'PUT', headers: { 'Content-Type': contentType }, body: buf });
  return file_url;
}

console.log(`[${SLUG}] Uploading storyboard to Fal storage...`);
const storyboardUrl = await uploadToFal(STORYBOARD, 'image/png');
console.log(`[${SLUG}] Storyboard hosted at: ${storyboardUrl}`);

// --- run -------------------------------------------------------------------
const OUT = path.resolve('./out');
fs.mkdirSync(OUT, { recursive: true });

const body = {
  prompt: PROMPT,
  image_urls: [
    storyboardUrl,       // @Image1 — storyboard sheet (composition + beats)
    PRODUCT_REF_URL,     // @Image2 — clean product photo (silhouette + colorway lock)
  ],
  resolution: RESOLUTION,
  duration: DURATION,
  aspect_ratio: '16:9',
  generate_audio: true,
};

const cost720 = (parseInt(DURATION) * 0.30).toFixed(2);
const cost480 = (parseInt(DURATION) * 0.18).toFixed(2);
console.log(`[${SLUG}] Submitting to Seedance 2.0 Pro (${DURATION}s, ${RESOLUTION})...`);
console.log(`[${SLUG}] Estimated cost: ~$${RESOLUTION === '720p' ? cost720 : cost480} USD`);

const t0 = Date.now();
const res = await fetch('https://fal.run/bytedance/seedance-2.0/reference-to-video', {
  method: 'POST',
  headers: { Authorization: `Key ${FAL_KEY}`, 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});
const json = await res.json();
console.log(`[${SLUG}] Returned in ${((Date.now() - t0) / 1000).toFixed(1)}s`);

if (!json.video?.url) {
  console.error('NO VIDEO:', JSON.stringify(json, null, 2));
  console.error('\nCommon causes (see SKILL.md content-policy section):');
  console.error('  - content_policy_violation: human likeness in storyboard → re-pitch as product-only or use mannequin face workaround');
  console.error('  - Fal storage URL expired → re-upload');
  process.exit(1);
}

const ts = Date.now();
const fname = `seedance2p_${SLUG}_${DURATION}s_${RESOLUTION}_${ts}.mp4`;
const buf = Buffer.from(await (await fetch(json.video.url)).arrayBuffer());
fs.writeFileSync(path.join(OUT, fname), buf);
console.log(`[${SLUG}] Saved: ${path.join(OUT, fname)}`);
console.log(`[${SLUG}] Seed: ${json.seed}`);
