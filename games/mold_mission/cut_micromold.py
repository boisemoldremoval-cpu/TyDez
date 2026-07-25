#!/usr/bin/env python3
"""Cut the MICRO MOLD's natural, multi-frame animations from its three videos.

The Micro Mold (the spiky mold-ball common enemy — "Micro Mold, Complete Sprite
Sheet") animates from the same three magenta clips as its sheet:
  V3 (locomotion)   IDLE, WALK, RUN, JUMP, FALL, LAND, TURN, HOP, BASIC ATTACK
  V1 (attacks)      DASH ATTACK, CONTACT SPLAT, SPORE CLOUD, BIG SPORE SHOT,
                    HURT, STUNNED
  V2 (environment)  SPORE TRAIL, GROWING, SPLIT/SPAWN, ENRAGED, CEILING HANG, ...

Unlike a single-pose enemy cut, this produces a FRAME SEQUENCE per state
(micromold_<state>_0..N) so the walk / idle / attack read as flowing motion, not
a two-frame toggle. Every frame of a clip is chroma-keyed (largest blob drops the
on-screen labels / sparkles / motion lines), then feet-aligned on one common
per-clip canvas exactly like cut_tyguy_anim.build, so the engine cycles them
wobble-free at one constant scale (see AssetPack.enemy_ref / Enemy.draw).

Deps: pip install imageio imageio-ffmpeg scipy pillow
"""
import numpy as np
from PIL import Image
from scipy import ndimage
import imageio

VID = {
    "V1": "/root/.claude/uploads/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/026df666-gemini_generated_video_A240F980.mp4",
    "V2": "/root/.claude/uploads/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/3bf597a3-gemini_generated_video_B4188FEB.mp4",
    "V3": "/root/.claude/uploads/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/dd1eca11-gemini_generated_video_554AEEF4.mp4",
}
OUT = "assets"

# state key -> (video, first_frame, last_frame, n_frames). Ranges sit inside each
# labelled section, trimmed off the transitions so the cycle loops cleanly.
CLIPS = {
    "micromold":         ("V3",   8,  40, 5),   # IDLE (settle / breathe)
    "micromold_walk":    ("V3",  44,  58, 8),   # WALK cycle — a clean single loop
    #                                             (44-58 only; 60+ carries a motion
    #                                             streak that flickers on repeat)
    "micromold_run":     ("V3",  64,  80, 6),   # RUN (faster gait, speed lines)
    "micromold_jump":    ("V3",  88,  98, 3, 150),  # JUMP — rising. crop_top=150 cuts
    #                                                the caption band (creature is lower)
    "micromold_fall":    ("V3", 124, 136, 3, 150),  # FALL — descending (same crop)
    "micromold_land":    ("V3", 152, 170, 4),   # LAND — touchdown squash
    "micromold_turn":    ("V3", 174, 190, 3),   # TURN AROUND (reverse facing)
    "micromold_hop":     ("V3", 196, 210, 3),   # HOP — a little skip
    "micromold_attack":  ("V3", 216, 236, 4),   # BASIC ATTACK — spore burst
    "micromold_hurt":    ("V1", 170, 186, 3),   # HURT recoil
    "micromold_stun":    ("V1", 196, 230, 3),   # STUNNED (dizzy stars)
    "micromold_splat":   ("V1",  48,  74, 4),   # CONTACT SPLAT — used as DEATH splat
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
    mask = ndimage.binary_erosion(mask, iterations=1)
    mask = ndimage.binary_fill_holes(mask)
    src = np.asarray(fr.convert("RGB")).astype(int)
    cr, cg, cb = src[:, :, 0], src[:, :, 1], src[:, :, 2]
    spill = ((cr > cg + 12) & (cr > cb - 30)) & mask
    cr = np.where(spill, np.minimum(cr, np.maximum(cg, cb)), cr)
    cb = np.where(spill, np.minimum(cb, cg + 24), cb)
    mag = (cr > cg + 12) & (cb > cg + 3)
    mask = mask & ~mag
    # drop near-WHITE pixels: those are the on-screen caption text ("JUMP" / "FALL")
    # and sparkle FX, never the creature (its brightest bits are yellow eyes / gold
    # spikes, all with a low blue channel), so this strips label bleed cleanly.
    white = (cr > 205) & (cg > 205) & (cb > 205)
    mask = mask & ~white
    lbl2, n2 = ndimage.label(mask)
    if n2 > 1:
        sizes2 = ndimage.sum(np.ones_like(lbl2), lbl2, range(1, n2 + 1))
        mask = lbl2 == int(np.argmax(sizes2)) + 1
    out = np.zeros((*mask.shape, 4), np.uint8)
    out[:, :, 0], out[:, :, 1], out[:, :, 2], out[:, :, 3] = cr, cg, cb, mask * 255
    return out, mask


def foot_x(mask):
    ys, xs = np.where(mask)
    y1 = ys.max()
    band = ys >= y1 - max(3, int((y1 - ys.min()) * 0.12))
    return float(xs[band].mean()), int(y1), int(ys.min()), int(xs.min()), int(xs.max())


def build(name, spec):
    v, a, b, k = spec[:4]
    crop_top = spec[4] if len(spec) > 4 else 0   # blank the caption band up top
    frs = frames_of(v)
    idxs = [int(round(a + (b - a) * i / (k - 1))) for i in range(k)] if k > 1 else [a]
    keyed = []
    for i in idxs:
        fr = frs[i]
        if crop_top:
            arr = np.array(fr.convert("RGB"))
            arr[:crop_top] = (200, 40, 110)      # paint it the magenta stage colour
            fr = Image.fromarray(arr)
        rgba, mask = key(fr)
        if not mask.any():
            continue
        fx, by, ty, lx, rx = foot_x(mask)
        keyed.append((rgba, fx, by, ty, lx, rx))
    # drop outlier frames (a raised apex / stray effect) so the body doesn't pop
    if len(keyed) >= 3:
        bh = sorted(by - ty for _, _, by, ty, _, _ in keyed)
        n = len(bh)
        med = bh[n // 2] if n % 2 else (bh[n // 2 - 1] + bh[n // 2]) / 2
        kept = [f for f in keyed if 0.78 * med <= (f[2] - f[3]) <= 1.16 * med]
        if len(kept) >= 2:
            keyed = kept
    halfL = max(fx - lx for _, fx, _, _, lx, _ in keyed)
    halfR = max(rx - fx for _, fx, _, _, _, rx in keyed)
    up = max(by - ty for _, fx, by, ty, _, _ in keyed)
    W = int(np.ceil(halfL + halfR)) + 6
    H = int(up) + 6
    cx = int(np.ceil(halfL)) + 3
    for j, (rgba, fx, by, ty, lx, rx) in enumerate(keyed):
        canvas = np.zeros((H, W, 4), np.uint8)
        sy0, sy1, sx0, sx1 = ty, by + 1, lx, rx + 1
        dst_x = cx - int(round(fx - lx))
        dst_y = (H - 3) - (by - ty)
        sub = rgba[sy0:sy1, sx0:sx1]
        hh, ww = sub.shape[:2]
        x0 = max(0, dst_x); y0 = max(0, dst_y)
        x1 = min(W, dst_x + ww); y1 = min(H, dst_y + hh)
        canvas[y0:y1, x0:x1] = sub[y0 - dst_y:y1 - dst_y, x0 - dst_x:x1 - dst_x]
        Image.fromarray(canvas, "RGBA").save(f"{OUT}/{name}_{j}.png")
    print(f"{name}: {len(keyed)} frames  canvas~{W}x{H}")


def main():
    for name, spec in CLIPS.items():
        build(name, spec)


if __name__ == "__main__":
    main()
