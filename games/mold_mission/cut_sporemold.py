#!/usr/bin/env python3
"""Cut the SPORE MOLD elite enemy's poses from its three animation videos.

The creature ships as three 10s / 24fps clips on a magenta stage:
  V1 (attacks)      DASH ATTACK, CONTACT SPLAT, SPORE CLOUD, BIG SPORE SHOT,
                    HURT, STUNNED
  V2 (environment)  SPORE TRAIL, GROWING, SPLIT/SPAWN, ENRAGED, CEILING HANG,
                    SPORE ON IMPACT, CORRODE SURFACE
  V3 (locomotion)   IDLE, WALK, RUN, JUMP, FALL, LAND, TURN, HOP, BASIC ATTACK

Enemies in the game draw ONE frame per state (base / _run / _hurt / _attack /
_charge / _enraged / ...), auto-picked by Enemy.draw. So we chroma-key a single
clean, centred frame out of the middle of each labelled section (magenta stage
-> largest connected blob drops the on-screen label text + sparkles + motion
lines) and save it under the matching asset key.

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

# asset key -> (video, frame). Frames sit in the calm middle of each labelled
# section so the pose is settled and the chroma stage is clean.
POSES = {
    "sporemold":          ("V3",  16),   # IDLE
    "sporemold_run":      ("V3",  50),   # WALK (clean stride; RUN adds speed lines)
    "sporemold_jump":     ("V3", 100),   # JUMP (airborne, legs tucked)
    "sporemold_attack":   ("V3", 228),   # BASIC ATTACK — spore burst from the mouth
    "sporemold_dash":     ("V1",  16),   # DASH ATTACK (leaning into a charge)
    "sporemold_charge":   ("V2",  56),   # GROWING — swells just before it acts
    "sporemold_hurt":     ("V1", 178),   # HURT
    "sporemold_stun":     ("V1", 205),   # STUNNED (dizzy stars)
    "sporemold_enraged":  ("V2", 120),   # ENRAGED (rare) — spiny, red-eyed
    "sporemold_split":    ("V2",  92),   # SPLIT / SPAWN (pinching in two)
    "sporemold_ceiling":  ("V2", 165),   # CEILING HANG (clinging upside-down)
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
    lbl2, n2 = ndimage.label(mask)
    if n2 > 1:
        sizes2 = ndimage.sum(np.ones_like(lbl2), lbl2, range(1, n2 + 1))
        mask = lbl2 == int(np.argmax(sizes2)) + 1
    out = np.zeros((*mask.shape, 4), np.uint8)
    out[:, :, 0], out[:, :, 1], out[:, :, 2], out[:, :, 3] = cr, cg, cb, mask * 255
    return out, mask


def crop_to_content(rgba, pad=4):
    m = rgba[:, :, 3] > 8
    ys, xs = np.where(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    y0 = max(0, y0 - pad); x0 = max(0, x0 - pad)
    y1 = min(rgba.shape[0] - 1, y1 + pad); x1 = min(rgba.shape[1] - 1, x1 + pad)
    return rgba[y0:y1 + 1, x0:x1 + 1]


def main():
    for name, (v, f) in POSES.items():
        frs = frames_of(v)
        rgba, mask = key(frs[f])
        if not mask.any():
            print(f"!! {name}: empty mask at {v}:{f}")
            continue
        sub = crop_to_content(rgba)
        Image.fromarray(sub, "RGBA").save(f"{OUT}/{name}.png")
        print(f"{name}: {v}:{f}  {sub.shape[1]}x{sub.shape[0]}")


if __name__ == "__main__":
    main()
