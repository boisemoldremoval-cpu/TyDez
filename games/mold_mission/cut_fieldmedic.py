#!/usr/bin/env python3
"""Cut the FIELD MEDIC's natural, multi-frame animations from her pink-stage clip.

The Field Medic ("Field Medic - Complete Sprite Sheet": Squad Medic / Support /
Reviver, healing rifle) animates from one magenta-PINK video the user supplied
("...No I want a pink background..."). Unlike the Micro Mold's several magenta
sources, this single clip carries five labelled sections back to back:

  RUN            0- 56   a clean run cycle (moving right)
  SHOOT         64-104   plants + fires the healing rifle (green muzzle blast)
  HEAL BEAM    112-152   channels a green heal beam onto an ally silhouette
  PROTECT      160-200   kneels inside a green hex barrier dome
  HAPPY        208-232   a face-close-up cheer with a green heart (emote)

The stage is PINK (~226, 90, 175) rather than the Micro Mold's magenta, and the
Medic wears green medical accents, so the key targets the pink signature only
(high red AND blue, low green) and leaves her greens — and the green heal/barrier
FX — intact. Each clip is chroma-keyed (largest blob drops the caption band and
the stray pink sparkles), then feet-aligned on one common per-clip canvas exactly
like cut_micromold.build, so the engine cycles them at one constant scale
(see AssetPack.enemy_ref / Enemy.draw).

Deps: pip install imageio imageio-ffmpeg scipy pillow
"""
import numpy as np
from PIL import Image
from scipy import ndimage
import imageio

VID = {
    # V2 — the canonical, richer clip: a superset of the first (RUN/SHOOT/HEAL/
    # BARRIER/HAPPY) plus DASH/SPRINT, SLIDE, RELOAD, HEAL BURST (AREA) and a real
    # LOOPABLE IDLE. Every state is cut from this one so scale + keying stay uniform.
    "V": "/root/.claude/uploads/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/165c6801-Generate_the_next_animation_vi.mp4",
    "V1": "/root/.claude/uploads/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/9009b7d4-No_I_want_a_pick_background.mp4",
}
OUT = "assets"

# state key -> (video, first_frame, last_frame, n_frames[, crop_top, crop_right,
# crop_bot, crop_left]). Ranges sit inside each labelled section, trimmed off the
# caption transitions so cycles loop cleanly.
CLIPS = {
    "fieldmedic":         ("V", 434, 476, 6),   # LOOPABLE IDLE — settle / breathe hold
    "fieldmedic_run":     ("V",   4,  52, 8),   # RUN cycle (a clean single loop)
    "fieldmedic_shoot":   ("V",  66, 104, 5),   # SHOOT — healing-rifle muzzle blast
    "fieldmedic_heal":    ("V", 114, 150, 5),   # HEAL BEAM (ALLY) — green channel beam
    "fieldmedic_channel": ("V", 114, 150, 5, 0, 410),  # HEAL BEAM, beam+ally cropped
    #                          off (crop_right=410, just past the muzzle) so the game
    #                          can aim a live beam at Ty instead of the baked target
    "fieldmedic_barrier": ("V", 164, 198, 4),   # PROTECT BARRIER — green hex dome
    "fieldmedic_happy":   ("V", 210, 232, 4),   # HAPPY — cheer emote (face close-up)
    "fieldmedic_dash":    ("V", 250, 280, 5),   # DASH / SPRINT — speed-line charge
    "fieldmedic_slide":   ("V", 296, 326, 4),   # SLIDE — low sliding kick
    "fieldmedic_reload":  ("V", 340, 374, 5),   # RELOAD — swap the healing-rifle cell
    "fieldmedic_burst":   ("V", 392, 422, 5),   # HEAL BURST (AREA) — radiating aura
}

_cache = {}
def frames_of(v):
    if v not in _cache:
        _cache[v] = [Image.fromarray(np.asarray(f))
                     for f in imageio.get_reader(VID[v], "ffmpeg")]
    return _cache[v]


def key(fr):
    """Chroma-key the PINK stage, keep largest blob, de-spill. Returns (RGBA, mask).

    Pink background signature: high red AND blue with green pulled well below both
    (bg ~226,90,175). The Medic's white armour, skin and — crucially — her green
    medical accents and the green heal/barrier FX all keep green at or above the
    other channels, so none of them trip this test."""
    a = np.asarray(fr.convert("RGB")).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    pink = (r > 175) & (b > 125) & (g < r - 42) & (g < b - 18)
    fg = ~pink
    lbl, n = ndimage.label(fg)
    sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
    mask = lbl == int(np.argmax(sizes)) + 1
    mask = ndimage.binary_erosion(mask, iterations=1)
    mask = ndimage.binary_fill_holes(mask)
    src = np.asarray(fr.convert("RGB")).astype(int)
    cr, cg, cb = src[:, :, 0], src[:, :, 1], src[:, :, 2]
    # de-spill only strongly-pink edge pixels (r and b both well above green) so we
    # scrub the pink halo without desaturating skin (skin is only ~20 red>green).
    spill = ((cr > cg + 40) & (cb > cg + 20)) & mask
    cr = np.where(spill, np.minimum(cr, cg + 20), cr)
    cb = np.where(spill, np.minimum(cb, cg + 12), cb)
    mag = (cr > cg + 42) & (cb > cg + 18)
    mask = mask & ~mag
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
    crop_top = spec[4] if len(spec) > 4 else 0
    crop_right = spec[5] if len(spec) > 5 else 0
    crop_bot = spec[6] if len(spec) > 6 else 0
    crop_left = spec[7] if len(spec) > 7 else 0
    frs = frames_of(v)
    idxs = [int(round(a + (b - a) * i / (k - 1))) for i in range(k)] if k > 1 else [a]
    keyed = []
    for i in idxs:
        fr = frs[i]
        if crop_top or crop_right or crop_bot or crop_left:
            arr = np.array(fr.convert("RGB"))
            if crop_top:
                arr[:crop_top] = (226, 90, 175)
            if crop_right:
                arr[:, crop_right:] = (226, 90, 175)
            if crop_bot:
                arr[crop_bot:, :] = (226, 90, 175)
            if crop_left:
                arr[:, :crop_left] = (226, 90, 175)
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
        kept = [f for f in keyed if 0.72 * med <= (f[2] - f[3]) <= 1.20 * med]
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
