# Example — On Cloudsurfer Max (Ivory)

A 15-second product-only motion-graphic ad. Built end-to-end with this kit.

- `storyboard.png` — Step 3 output. 6-panel sheet from GPT Image 2, 2560×1792, ~$0.18.
- `ad-15s-480p.mp4` — Step 4 output. Seedance 2.0 Pro animated the storyboard at 480p for a cheap test run, ~$2.70.

## What worked

- **Product-only direction.** No humans → no Seedance likeness rejection. Cleanest path.
- **Dynamic studio backgrounds.** Motion-streak gradients, abstract alpine-horizon color fields, wind-streak particles — gives kinetic energy without needing a runner in frame.
- **Both refs named in the prompt.** Storyboard as `@Image1`, clean product photo as `@Image2`. Without the `@Image2` line, Seedance drifts on colorway and sole architecture even when the storyboard is right.

## Cost

| Step | Cost |
|------|------|
| Storyboard (GPT Image 2 high, 2560×1792) | ~$0.18 |
| Animation (Seedance 2.0 Pro, 15s @ 480p) | ~$2.70 |
| **Total** | **~$2.88** |

For a 720p final, swap `RESOLUTION = '720p'` in `animate.mjs` — that's $4.54 for the 15s clip.
