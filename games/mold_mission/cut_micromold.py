#!/usr/bin/env python3
"""Cut the Micro Mold enemy sprites (idle / run / attack / hurt) from its magenta
chroma sheet into assets/. Seed a point inside the figure, flood its connected
silhouette for exact bounds (no clipping), global-remove the magenta, de-spill.
"""
import os
from collections import deque
from PIL import Image

SHEET = "art_reference/pending/micro_mold_sheet.png"
OUT = "assets"

# name -> seed (x, y) inside the frame, or a full (l, t, r, b) box
POSES = {
    "micromold":         (349, 175),            # IDLE frame 1
    "micromold_run":     (655, 175),            # WALK frame (clean, reads as crawl)
    "micromold_attack":  (445, 448),            # BASIC ATTACK — spore burst
    "micromold_hurt":    (324, 570, 395, 645),  # HURT (fixed box — keeps spikes)
}


def is_bg(r, g, b):
    return r > 150 and g < 105 and b > 95 and (r - g) > 95


def _isfig(px, W, H, x, y):
    return 0 <= x < W and 0 <= y < H and not is_bg(*px[x, y])


def _seed_bbox(px, W, H, sx, sy):
    seen = {(sx, sy)}
    q = deque([(sx, sy)])
    a = b = sx
    c = d = sy
    while q:
        x, y = q.popleft()
        a, b, c, d = min(a, x), max(b, x), min(c, y), max(d, y)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if (nx, ny) not in seen and _isfig(px, W, H, nx, ny):
                    seen.add((nx, ny))
                    q.append((nx, ny))
    return (a - 2, c - 2, b + 3, d + 3)


def cut(im, box):
    crop = im.crop(box).convert("RGB")
    w, h = crop.size
    px = crop.load()
    alpha = bytearray(0 if is_bg(*px[x, y]) else 255
                      for y in range(h) for x in range(w))

    def edge(x, y):
        i = y * w + x
        return (x == 0 or y == 0 or x == w - 1 or y == h - 1
                or not alpha[i - 1] or not alpha[i + 1]
                or (y > 0 and not alpha[i - w])
                or (y < h - 1 and not alpha[i + w]))

    out = Image.new("RGBA", (w, h))
    op = out.load()
    for y in range(h):
        for x in range(w):
            if alpha[y * w + x]:
                r, g, b = px[x, y]
                if edge(x, y) and r > g + 14 and r > b - 10:   # de-spill fringe
                    r = min(r, max(g, b))
                    b = min(b, g + 24)
                op[x, y] = (r, g, b, 255)
            else:
                op[x, y] = (0, 0, 0, 0)
    bb = out.getbbox()
    return out.crop(bb) if bb else out


def main():
    im = Image.open(SHEET).convert("RGB")
    W, H = im.size
    px = im.load()
    for name, spec in POSES.items():
        box = _seed_bbox(px, W, H, *spec) if len(spec) == 2 else spec
        img = cut(im, box)
        img.save(os.path.join(OUT, name + ".png"))
        print(f"{name}: {img.size}")


if __name__ == "__main__":
    main()
