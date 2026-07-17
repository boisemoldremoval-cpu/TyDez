#!/usr/bin/env python3
"""Cut TyGuy's sprites from the bright MAGENTA "TYGUY — Complete Animation Guide"
sheet into assets/, so the whole player character is the tactical TyGuy.

The magenta chroma shares no colour with Ty (dark armour, lime accents, tan
skin), so background is removed GLOBALLY (every magenta pixel, including regions
enclosed by the ladder in the climb pose) rather than by an edge flood. Then
keep the largest blob (drops the cell's label text), de-spill the pink fringe,
and autocrop.
"""
import os
from collections import deque
from PIL import Image

SHEET = "art_reference/pending/tyguy_full_animation_guide_magenta.png"
OUT = "assets"

# (key, (l, t, r, b), keep_largest). Boxes are each figure's exact connected
# silhouette bounds + a 2px margin, so no limb/gun/foot is ever clipped.
POSES = [
    ("player",         (49, 124, 102, 224), True),    # IDLE
    ("player_run",     (424, 132, 513, 222), True),   # RUN
    ("player_dash",    (665, 133, 818, 223), True),   # DASH / SPRINT
    ("player_jump",    (850, 125, 925, 221), True),   # JUMP UP
    ("player_fall",    (1179, 132, 1257, 222), True),  # JUMP DOWN
    ("player_aim",     (25, 496, 101, 583), True),    # AIM (IDLE)
    ("player_shoot",   (197, 497, 281, 582), True),   # SHOOT
    ("player_hurt",    (1010, 499, 1062, 580), True),  # TAKE DAMAGE (LIGHT)
    ("player_reload",  (446, 499, 518, 582), True),   # RELOAD
    ("player_victory", (35, 768, 89, 843), True),     # VICTORY
    ("player_climb",   (996, 222, 1045, 336), True),  # CLIMB LADDER (front)
]


def is_bg(r, g, b):
    return r > 140 and g < 125 and b > 62 and (r - g) > 45


def is_pinkish(r, g, b):
    # a magenta-fringe blend pixel (leftover halo on the figure's edge)
    return r > g + 16 and r > b - 12 and b > 42 and g < 155


def keep_largest(alpha, w, h):
    seen = bytearray(w * h)
    best, bn = [], 0
    for sy in range(h):
        for sx in range(w):
            i = sy * w + sx
            if alpha[i] == 0 or seen[i]:
                continue
            comp = []
            q = deque([(sx, sy)])
            seen[i] = 1
            while q:
                x, y = q.popleft()
                comp.append(y * w + x)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        j = ny * w + nx
                        if alpha[j] and not seen[j]:
                            seen[j] = 1
                            q.append((nx, ny))
            if len(comp) > bn:
                bn, best = len(comp), comp
    out = bytearray(w * h)
    for idx in best:
        out[idx] = 255
    return out


def cut(sheet, box, klargest):
    crop = sheet.crop(box).convert("RGB")
    w, h = crop.size
    px = crop.load()
    # global background removal (Ty has no magenta pixels)
    alpha = bytearray(0 if is_bg(*px[x, y]) else 255
                      for y in range(h) for x in range(w))
    if klargest:
        alpha = keep_largest(alpha, w, h)

    def is_edge(x, y):
        i = y * w + x
        return (x == 0 or y == 0 or x == w - 1 or y == h - 1
                or not alpha[i - 1] or not alpha[i + 1]
                or (y > 0 and not alpha[i - w])
                or (y < h - 1 and not alpha[i + w]))

    # peel the magenta halo: erode edge pixels that are still pink-tinted
    for _ in range(2):
        clear = [y * w + x for y in range(h) for x in range(w)
                 if alpha[y * w + x] and is_edge(x, y) and is_pinkish(*px[x, y])]
        for i in clear:
            alpha[i] = 0

    out = Image.new("RGBA", (w, h))
    op = out.load()
    for y in range(h):
        for x in range(w):
            if alpha[y * w + x]:
                r, g, b = px[x, y]
                if is_edge(x, y) and r > g + 14 and r > b - 10:  # de-spill fringe
                    r = min(r, max(g, b))
                    b = min(b, g + 24)
                op[x, y] = (r, g, b, 255)
            else:
                op[x, y] = (0, 0, 0, 0)
    bb = out.getbbox()
    return out.crop(bb) if bb else out


def main():
    sheet = Image.open(SHEET).convert("RGB")
    for key, box, kl in POSES:
        img = cut(sheet, box, kl)
        dest = os.path.join(OUT, key + ".png")
        img.save(dest)
        print(f"{key}: {img.size} -> {dest}")


if __name__ == "__main__":
    main()
