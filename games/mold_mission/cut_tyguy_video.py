#!/usr/bin/env python3
"""Pull TyGuy's movement poses from the gameplay video into assets/.

The video (art_reference/pending/tyguy_movements.mp4) shows Ty performing each
labelled movement on a magenta background. We read frames with imageio-ffmpeg,
chroma-key the magenta out, and keep the LARGEST connected component so the
on-screen label text / sparkles / detached dust are dropped — leaving just Ty.

Deps: pip install imageio imageio-ffmpeg scipy pillow
"""
import numpy as np
from PIL import Image
from scipy import ndimage
import imageio

VIDEO = "art_reference/pending/tyguy_movements.mp4"
OUT = "assets"

# game asset name -> source frame index (chosen mid-motion, clean pose)
FRAMES = {
    "player":            20,   # IDLE
    "player_run":        82,   # RUN
    "player_jump":       136,  # JUMP (rising)
    "player_fall":       176,  # JUMP DOWN (descending, arms out)
    "player_wallslide":  226,  # WALL SLIDE
}
DASH_FRAME = 110               # DASH/SPRINT — cropped to Ty (drop the dust cloud)


def key_char(fr):
    """Chroma-key the magenta bg, keep the largest blob (Ty), de-spill the fringe."""
    a = np.asarray(fr.convert("RGB")).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    fg = ~((r > 150) & (g < 105) & (b > 95) & ((r - g) > 95))
    lbl, n = ndimage.label(fg)
    sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
    mask = lbl == int(np.argmax(sizes)) + 1
    ys, xs = np.where(mask)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    src = np.asarray(fr.convert("RGB"))[y0:y1 + 1, x0:x1 + 1].astype(int)
    m = mask[y0:y1 + 1, x0:x1 + 1]
    cr, cg, cb = src[:, :, 0], src[:, :, 1], src[:, :, 2]
    spill = (cr > cg + 20) & (cr > cb - 10) & m
    cr = np.where(spill, np.minimum(cr, np.maximum(cg, cb)), cr)
    cb = np.where(spill, np.minimum(cb, cg + 24), cb)
    out = np.zeros((*m.shape, 4), np.uint8)
    out[:, :, 0], out[:, :, 1], out[:, :, 2], out[:, :, 3] = cr, cg, cb, m * 255
    im = Image.fromarray(out, "RGBA")
    return im.crop(im.getbbox())


def main():
    rdr = imageio.get_reader(VIDEO, "ffmpeg")
    frames = [Image.fromarray(np.asarray(f)) for f in rdr]
    for name, idx in FRAMES.items():
        key_char(frames[idx]).save(f"{OUT}/{name}.png")
        print(name, idx)
    # dash: keep the sprinting figure, crop off the left-side dust/flash trail
    d = key_char(frames[DASH_FRAME])
    w, h = d.size
    d = d.crop((max(0, w - 360), 0, w, h))
    d.crop(d.getbbox()).save(f"{OUT}/player_dash.png")
    print("player_dash", DASH_FRAME)


if __name__ == "__main__":
    main()
