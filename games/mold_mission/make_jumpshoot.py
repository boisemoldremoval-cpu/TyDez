#!/usr/bin/env python3
"""Build TyGuy's AIR-SHOOT sprites by compositing two animations.

Classic run-and-gun trick (Contra / Metal Slug): the LEGS come from an airborne
pose (jump / fall / peak) while the UPPER BODY comes from the standing AIM pose
(rifle levelled forward). Waist-stitched so Ty keeps his jump silhouette below
and aims his gun above — a real jump-and-shoot frame where the muzzle lines up.

Reads the already-cut, clean clip frames in assets/ (so no video/keying needed),
composites each airborne frame with a fixed aim torso, then feet-aligns the whole
clip on one common canvas exactly like cut_tyguy_anim.build so blit_char animates
it wobble-free at the same constant scale as every other clip.
"""
import glob
import os
import re

import numpy as np
from PIL import Image

OUT = "assets"
TORSO = "player_aim_2"          # rifle levelled forward (upper-body source)


def kill_pink(canvas):
    """Neutralise any magenta/pink fringe (e.g. from rotating the torso) so the
    composite has no pink edge, matching the cleaned source frames."""
    a = canvas.astype(int)
    r, g, b, al = a[:, :, 0], a[:, :, 1], a[:, :, 2], a[:, :, 3]
    # magenta signature: green is the minimum channel (red AND blue above green)
    mag = (r > g + 20) & (b > g + 6) & (al > 30)
    r = np.where(mag, np.minimum(r, g + 10), r)
    b = np.where(mag, np.minimum(b, g + 10), b)
    out = canvas.copy()
    out[:, :, 0], out[:, :, 2] = r.astype(np.uint8), b.astype(np.uint8)
    return out
# leg-pose clip -> (output shoot clip, cut_leg, cut_torso). cut_leg keeps the
# lower (1-cut_leg) of the legs; cut_torso keeps the top cut_torso of the aim
# torso; they meet + overlap at the waist. The crouch variant uses a deeper
# overlap so Ty stays low (ducked) while the rifle still points forward.
CLIPS = {
    "player_jump":   ("player_jumpfire",   0.50, 0.60),
    "player_fall":   ("player_fallfire",   0.50, 0.60),
    "player_peak":   ("player_peakfire",   0.50, 0.60),
    "player_crouch": ("player_crouchfire", 0.66, 0.52),
    "player_run":    ("player_runfire",    0.50, 0.60),
    "player_walk":   ("player_walkfire",   0.50, 0.60),
}
# down-aim: the aim torso rotated so the rifle points diagonally down-forward.
# Composited with the run legs so Ty can shoot DOWN while running.
DOWN_CLIPS = {
    "player_run":  ("player_rundownfire", 0.50, 0.60),
    "player_walk": ("player_walkdownfire", 0.50, 0.60),
}
DOWN_ANGLE = 24                 # degrees the rifle tilts below horizontal


def load(name):
    return np.asarray(Image.open(os.path.join(OUT, name + ".png")).convert("RGBA"))


def bbox(a):
    m = a[:, :, 3] > 8
    ys, xs = np.where(m)
    return ys.min(), ys.max(), xs.min(), xs.max()


def cx_band(a, y0, y1):
    m = a[y0:y1, :, 3] > 8
    ys, xs = np.where(m)
    return xs.mean() if len(xs) else a.shape[1] / 2


def composite(legs, torso, cut_leg, cut_torso):
    """Waist-stitch: lower body from `legs`, upper body from `torso`, aligned on
    their waist-band centroids (the torso is drawn on top so it hides the seam)."""
    t, b, l, r = bbox(legs); L = legs[t:b + 1, l:r + 1]
    t, b, l, r = bbox(torso); T = torso[t:b + 1, l:r + 1]
    Lh = L.shape[0]; Th = T.shape[0]
    yL = int(cut_leg * Lh); yT = int(cut_torso * Th)
    cxL = cx_band(L, max(0, yL - 6), yL + 6)
    cxT = cx_band(T, max(0, yT - 6), yT + 6)
    upH = yT; loH = Lh - yL
    H = upH + loH + 8
    W = L.shape[1] + T.shape[1] + 120
    cxc = W // 2
    waistY = upH + 3
    canvas = np.zeros((H, W, 4), np.uint8)
    # legs (lower) first
    seg = L[yL:Lh]; hh, ww = seg.shape[:2]
    x0 = int(cxc - cxL); y0 = waistY
    reg = canvas[y0:y0 + hh, x0:x0 + ww]
    canvas[y0:y0 + hh, x0:x0 + ww] = np.where(seg[:, :, 3:4] > 8, seg, reg)
    # torso (upper) on top, waist aligned
    seg2 = T[0:yT]; hh2, ww2 = seg2.shape[:2]
    x0 = int(cxc - cxT); y0 = waistY - yT
    reg = canvas[y0:y0 + hh2, x0:x0 + ww2]
    canvas[y0:y0 + hh2, x0:x0 + ww2] = np.where(seg2[:, :, 3:4] > 8, seg2, reg)
    return canvas


def rotate_torso(torso, angle):
    """Rotate the aim torso about the shoulder so the rifle tilts down-forward
    (for the shoot-while-running-down poses)."""
    t, b, l, r = bbox(torso)
    T = torso[t:b + 1, l:r + 1]
    im = Image.fromarray(T)
    H, W = T.shape[:2]
    piv = (int(W * 0.40), int(H * 0.50))       # mid-torso pivot: swings the rifle
    #                                            down while keeping the head level
    im = im.rotate(-angle, resample=Image.BICUBIC, center=piv, expand=True)
    return np.asarray(im)


def foot_x(a):
    m = a[:, :, 3] > 8
    ys, xs = np.where(m)
    y1 = ys.max()
    band = ys >= y1 - max(3, int((y1 - ys.min()) * 0.12))
    return float(xs[band].mean()), int(y1), int(ys.min()), int(xs.min()), int(xs.max())


def frames_of(clip):
    out = []
    for p in sorted(glob.glob(os.path.join(OUT, clip + "_*.png"))):
        if re.match(rf"{clip}_\d+$", os.path.basename(p)[:-4]):
            out.append(load(os.path.basename(p)[:-4]))
    return out


def build(clip, outname, torso, cut_leg, cut_torso):
    comps = [composite(l, torso, cut_leg, cut_torso) for l in frames_of(clip)]
    keyed = [(c, *foot_x(c)) for c in comps]
    halfL = max(fx - lx for _, fx, _, _, lx, _ in keyed)
    halfR = max(rx - fx for _, fx, _, _, _, rx in keyed)
    up = max(by - ty for _, fx, by, ty, _, _ in keyed)
    W = int(np.ceil(halfL + halfR)) + 6
    H = int(up) + 6
    cx = int(np.ceil(halfL)) + 3
    for j, (c, fx, by, ty, lx, rx) in enumerate(keyed):
        canvas = np.zeros((H, W, 4), np.uint8)
        sub = c[ty:by + 1, lx:rx + 1]
        dst_x = cx - int(round(fx - lx))
        dst_y = (H - 3) - (by - ty)
        hh, ww = sub.shape[:2]
        x0 = max(0, dst_x); y0 = max(0, dst_y)
        x1 = min(W, dst_x + ww); y1 = min(H, dst_y + hh)
        canvas[y0:y1, x0:x1] = sub[y0 - dst_y:y1 - dst_y, x0 - dst_x:x1 - dst_x]
        Image.fromarray(kill_pink(canvas), "RGBA").save(
            os.path.join(OUT, f"{outname}_{j}.png"))
    print(f"{outname}: {len(keyed)} frames  canvas~{W}x{H}")


def main():
    torso = load(TORSO)
    for clip, (outname, cut_leg, cut_torso) in CLIPS.items():
        build(clip, outname, torso, cut_leg, cut_torso)
    down_torso = rotate_torso(torso, DOWN_ANGLE)
    for clip, (outname, cut_leg, cut_torso) in DOWN_CLIPS.items():
        build(clip, outname, down_torso, cut_leg, cut_torso)


if __name__ == "__main__":
    main()
