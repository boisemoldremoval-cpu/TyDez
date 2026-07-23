#!/usr/bin/env python3
"""Cut the Spore Drifter enemy sprites (idle / drift / attack / hurt) from its
magenta chroma sheet into assets/. For each pose we take a generous region box
that frames exactly one creature (and no label text), keep the largest connected
non-background blob inside it (body + dangling tentacles), then global-remove the
magenta and de-spill the pink fringe — so every limb is captured with no clip.
"""
import os
from collections import deque
from PIL import Image

SHEET = "art_reference/pending/spore_drifter_sheet.png"
OUT = "assets"

# name -> region box (l, t, r, b) around a single creature, clear of neighbours
# and label text. The largest blob inside becomes the sprite.
REGIONS = {
    "sporedrifter":        (300, 128, 432, 276),   # IDLE (row 1, frame 1)
    "sporedrifter_run":    (612, 128, 730, 250),   # DRIFT FORWARD (frame 1)
    "sporedrifter_attack": (300, 392, 398, 500),   # SPORE SHOT (body only; the
                                                    # engine draws the actual spores)
    "sporedrifter_hurt":   (292, 548, 404, 668),   # HURT (body; drop the spray)
    "sporedrifter_charge": (300, 700, 440, 812),   # CHARGING ATTACK (wind-up)
    "sporedrifter_enraged": (500, 692, 732, 818),  # ENRAGED (rare, low-HP state)
}


def is_bg(r, g, b):
    return r > 150 and g < 105 and b > 95 and (r - g) > 95


def largest_blob_bbox(px, box):
    l, t, r, b = box
    seen = set()
    best = None
    best_n = 0
    for sy in range(t, b):
        for sx in range(l, r):
            if (sx, sy) in seen or is_bg(*px[sx, sy]):
                continue
            q = deque([(sx, sy)])
            seen.add((sx, sy))
            comp = [(sx, sy)]
            a = c = sx
            e = f = sy
            while q:
                x, y = q.popleft()
                a, c, e, f = min(a, x), max(c, x), min(e, y), max(f, y)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if (l <= nx < r and t <= ny < b
                                and (nx, ny) not in seen
                                and not is_bg(*px[nx, ny])):
                            seen.add((nx, ny))
                            q.append((nx, ny))
                            comp.append((nx, ny))
            if len(comp) > best_n:
                best_n = len(comp)
                best = (a, c, e, f)
    a, c, e, f = best
    return (a - 2, e - 2, c + 3, f + 3)


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
    px = im.load()
    for name, region in REGIONS.items():
        box = largest_blob_bbox(px, region)
        img = cut(im, box)
        img.save(os.path.join(OUT, name + ".png"))
        print(f"{name}: box={box} size={img.size}")


if __name__ == "__main__":
    main()
