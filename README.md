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

## Developer tools

- **`tools/claude-gemini-bridge/`** — a vendored copy of
  [tkaufmann/claude-gemini-bridge](https://github.com/tkaufmann/claude-gemini-bridge)
  that lets Claude Code delegate large, multi-file analyses to Google Gemini.
  Install it on your own machine with `tools/claude-gemini-bridge/install.sh`
  (requires the Gemini CLI + `GEMINI_API_KEY`). See
  [`tools/claude-gemini-bridge/VENDORED.md`](tools/claude-gemini-bridge/VENDORED.md)
  for details.
