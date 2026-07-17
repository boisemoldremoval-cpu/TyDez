#!/usr/bin/env python3
"""Cut TyGuy's standing / movement / combat sprites from the bright chroma-green
"TYGUY — Complete Animation Guide" sheet and drop them into assets/, replacing
the earlier placeholder player art so the WHOLE character is the tactical TyGuy
(matching the crouch move-set already cut from the crouch sheet).

Recipe: crop one frame -> flood-fill the solid green background from the edges
-> keep the largest connected shape (drops the cell's label text) -> autocrop.
`victory` skips keep-largest (its pose splits into two blobs) and instead uses a
tight box that already excludes the label / panel.
"""
import os
from collections import deque
from PIL import Image

SHEET = "art_reference/pending/tyguy_full_animation_guide_green.png"
OUT = "assets"

# (key, (l, t, r, b), keep_largest)
POSES = [
    ("player",         (44, 112, 108, 252), True),   # IDLE
    ("player_run",     (449, 112, 520, 252), True),  # RUN
    ("player_dash",    (650, 112, 752, 252), True),  # DASH / SPRINT
    ("player_jump",    (789, 108, 851, 252), True),  # JUMP UP
    ("player_fall",    (1170, 108, 1245, 254), True),  # JUMP DOWN
    ("player_aim",     (31, 484, 108, 604), True),   # AIM (IDLE)
    ("player_shoot",   (183, 484, 322, 604), True),  # SHOOT
    ("player_hurt",    (983, 484, 1048, 604), True),  # TAKE DAMAGE (LIGHT)
    ("player_victory", (22, 768, 108, 858), False),  # VICTORY
]


def is_bg(r, g, b):
    return b < 48 and g > 60 and (g - r) > 28 and (g - b) > 45


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
    bg = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            i = y * w + x
            if not bg[i] and is_bg(*px[x, y]):
                bg[i] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            i = y * w + x
            if not bg[i] and is_bg(*px[x, y]):
                bg[i] = 1
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                j = ny * w + nx
                if not bg[j] and is_bg(*px[nx, ny]):
                    bg[j] = 1
                    q.append((nx, ny))
    alpha = bytearray(0 if bg[i] else 255 for i in range(w * h))
    if klargest:
        alpha = keep_largest(alpha, w, h)
    out = Image.new("RGBA", (w, h))
    op = out.load()
    for y in range(h):
        for x in range(w):
            op[x, y] = ((*px[x, y], 255) if alpha[y * w + x] else (0, 0, 0, 0))
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
