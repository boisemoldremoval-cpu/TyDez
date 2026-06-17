# TyDez — Boise Mold Removal Promo

A self-contained generator for a branded promo video (`promo.mp4`).

![brand](https://img.shields.io/badge/TyDez-Boise%20Mold%20Removal-56d6a5)

## What's here

- **`make_promo.py`** — renders a 1080p / 30fps H.264 promo video with
  animated motion graphics. No system `ffmpeg` required; it uses the binary
  bundled with `imageio-ffmpeg`.
- **`promo.mp4`** — the rendered video (~26s):
  brand intro → hook → promise → services → why-us badges → call-to-action.

## Render it

```bash
pip install Pillow numpy imageio-ffmpeg
python3 make_promo.py            # -> promo.mp4
python3 make_promo.py out.mp4    # custom output path
```

## Customize

Edit the `CONFIG` block at the top of `make_promo.py` to change the brand,
copy, services, badges, contact details, and colors, then re-render.
The scene timeline and palette live just below `CONFIG`.

## Open Generative AI (bundled web app)

The [`open-generative-ai/`](./open-generative-ai) directory contains a ported
copy of [Open-Generative-AI](https://github.com/Anil-matcha/Open-Generative-AI)
— an open-source, Next.js/Electron creative studio that wraps 200+ image,
video, and audio models through the MuAPI gateway (Image, Video, Cinema,
Lip Sync, Workflow, and Agent studios). It is self-contained with its own
`package.json`, build scripts, and docs. See
[`open-generative-ai/README.md`](./open-generative-ai/README.md) for setup and
usage.

```bash
cd open-generative-ai
npm install
npm run build      # build all workspace packages
npm run dev        # run the Next.js dev server
```
