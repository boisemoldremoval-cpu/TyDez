#!/usr/bin/env python3
"""Clip TyGuy's video animations into aligned, chroma-keyed FRAME SEQUENCES.

Each labelled section of the movement videos becomes an in-place animation:
K frames sampled across the section, magenta chroma-keyed (largest connected
component -> drops the on-screen labels / bullets / detached dust), then all
frames of a clip are placed on ONE common canvas with their FEET aligned, so
blit_char animates them smoothly with no wobble.

Deps: pip install imageio imageio-ffmpeg scipy pillow
"""
import numpy as np
from PIL import Image
from scipy import ndimage
import imageio

VID = {
    "A": "/root/.claude/uploads/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/33d04f87-gemini_generated_video_154FBDD9.mp4",
    "B": "/root/.claude/uploads/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/b4e2d225-gemini_generated_video_47BCC056.mp4",
    "C": "/root/.claude/uploads/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/ea3d7949-gemini_generated_video_083D2E9C.mp4",
}
OUT = "assets"

# state -> (video, first_frame, last_frame, n_frames, crop_left_dust)
ANIMS = {
    "player":              ("A",   6,  30, 4, False),  # IDLE
    "player_walk":         ("A",  34,  62, 6, False),  # WALK
    "player_run":          ("A",  66,  88, 6, False),  # RUN
    "player_dash":         ("A",  94, 118, 5, True),   # DASH/SPRINT (drop dust)
    "player_jump":         ("A", 124, 146, 4, False),  # JUMP (rising)
    "player_peak":         ("A", 150, 176, 4, False),  # JUMP PEAK
    "player_fall":         ("A", 178, 190, 3, False),  # descending
    "player_land":         ("A", 190, 204, 4, False),  # touchdown
    "player_wallslide":    ("A", 208, 236, 4, False),  # WALL SLIDE
    "player_crouch":       ("B",  26,  56, 4, False),  # CROUCH IDLE
    "player_crouch_walk":  ("B",  64,  86, 6, False),  # CROUCH WALK
    "player_roll":         ("B", 146, 166, 5, False),  # ROLL
    "player_aim":          ("B", 176, 236, 4, False),  # AIM (gun)
    "player_shoot":        ("C",   2,  34, 5, False),  # SHOOT (gun + muzzle)
    "player_reload":       ("C",  40,  72, 5, False),  # RELOAD
    "player_use":          ("C",  74, 106, 5, False),  # USE / ACTIVATE
}

_cache = {}
def frames_of(v):
    if v not in _cache:
        _cache[v] = [Image.fromarray(np.asarray(f))
                     for f in imageio.get_reader(VID[v], "ffmpeg")]
    return _cache[v]


def key(fr):
    """Chroma-key magenta, keep largest blob, de-spill. Returns (RGBA, mask)."""
    a = np.asarray(fr.convert("RGB")).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    fg = ~((r > 150) & (g < 105) & (b > 95) & ((r - g) > 95))
    lbl, n = ndimage.label(fg)
    sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
    mask = lbl == int(np.argmax(sizes)) + 1
    src = np.asarray(fr.convert("RGB")).astype(int)
    cr, cg, cb = src[:, :, 0], src[:, :, 1], src[:, :, 2]
    spill = (cr > cg + 20) & (cr > cb - 10) & mask
    cr = np.where(spill, np.minimum(cr, np.maximum(cg, cb)), cr)
    cb = np.where(spill, np.minimum(cb, cg + 24), cb)
    out = np.zeros((*mask.shape, 4), np.uint8)
    out[:, :, 0], out[:, :, 1], out[:, :, 2], out[:, :, 3] = cr, cg, cb, mask * 255
    return out, mask


def foot_x(mask):
    ys, xs = np.where(mask)
    y1 = ys.max()
    band = ys >= y1 - max(3, int((y1 - ys.min()) * 0.12))
    return float(xs[band].mean()), int(y1), int(ys.min()), int(xs.min()), int(xs.max())


def build(name, spec):
    v, a, b, k, crop_dust = spec
    frs = frames_of(v)
    idxs = [int(round(a + (b - a) * i / (k - 1))) for i in range(k)] if k > 1 else [a]
    keyed = []
    for i in idxs:
        rgba, mask = key(frs[i])
        if not mask.any():
            continue
        fx, by, ty, lx, rx = foot_x(mask)
        keyed.append((rgba, fx, by, ty, lx, rx))
    # common canvas with feet aligned at (cx, bottom)
    halfL = max(fx - lx for _, fx, _, _, lx, _ in keyed)
    halfR = max(rx - fx for _, fx, _, _, _, rx in keyed)
    up = max(by - ty for _, fx, by, ty, _, _ in keyed)
    W = int(np.ceil(halfL + halfR)) + 6
    H = int(up) + 6
    cx = int(np.ceil(halfL)) + 3
    for j, (rgba, fx, by, ty, lx, rx) in enumerate(keyed):
        canvas = np.zeros((H, W, 4), np.uint8)
        # source region rows ty..by, cols lx..rx  ->  place foot fx at cx, by at H-3
        sy0, sy1, sx0, sx1 = ty, by + 1, lx, rx + 1
        dst_x = cx - int(round(fx - lx))
        dst_y = (H - 3) - (by - ty)
        sub = rgba[sy0:sy1, sx0:sx1]
        hh, ww = sub.shape[:2]
        x0 = max(0, dst_x); y0 = max(0, dst_y)
        x1 = min(W, dst_x + ww); y1 = min(H, dst_y + hh)
        canvas[y0:y1, x0:x1] = sub[y0 - dst_y:y1 - dst_y, x0 - dst_x:x1 - dst_x]
        im = Image.fromarray(canvas, "RGBA")
        if crop_dust:                       # dash: keep the sprinter, drop left dust
            im = im.crop((max(0, im.width - int(W * 0.62)), 0, im.width, im.height))
        im.save(f"{OUT}/{name}_{j}.png")
    print(f"{name}: {len(keyed)} frames  canvas~{W}x{H}")


def main():
    for name, spec in ANIMS.items():
        build(name, spec)


if __name__ == "__main__":
    main()
