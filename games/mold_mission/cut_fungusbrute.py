#!/usr/bin/env python3
"""Cut the Fungus Brute enemy sprites from its magenta chroma sheet into assets/
(this replaces the old vector Fungus Brute with real art). Largest-connected-blob
in a per-pose region box, then global magenta removal + pink de-spill — every
leg and claw captured with no clip. Same technique as cut_toxicslime.py.
"""
import os
from collections import deque
from PIL import Image

SHEET = "art_reference/pending/fungus_brute_sheet.png"
OUT = "assets"

# name -> region box (l, t, r, b) around a single crawler. The TOP is set just
# below the row's label text so we can take the bbox of EVERY non-bg pixel in
# the region (the crawler's thin legs are separated from its body by the magenta,
# so a connected-blob cut would drop them — we must keep all pixels).
REGIONS = {
    "fungusbrute":         (300, 112, 376, 230),   # IDLE (row 1, frame 1)
    "fungusbrute_run":     (940, 112, 1055, 230),  # RUN (frame 1)
    "fungusbrute_attack":  (300, 402, 389, 512),   # CLUB SWING
    "fungusbrute_hurt":    (298, 572, 418, 662),   # HURT
    "fungusbrute_enraged": (298, 724, 452, 804),   # RAGE MODE (glowing)
}


def is_bg(r, g, b):
    return r > 150 and g < 105 and b > 95 and (r - g) > 95


def _body_bbox(px, box):
    """Bbox of the largest connected non-bg blob in the region (the crawler
    body — one frame, never a neighbour)."""
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
            comp = 1
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
                            comp += 1
            if comp > best_n:
                best_n, best = comp, (a, c, e, f)
    return best


def crawler_bbox(px, region):
    """Find the body blob, then take the bbox of every non-bg pixel in a small
    expansion around it — captures the thin detached legs (which spread down and
    out) without reaching the neighbouring frame or the row label above."""
    a, c, e, f = _body_bbox(px, region)
    # legs reach down and sideways, so expand out/down generously, up barely
    l = max(region[0], a - 20)
    t = max(region[1], e - 3)
    r = min(region[2], c + 20)
    b = min(region[3], f + 16)
    ba = ca = ea = fa = None
    for y in range(t, b):
        for x in range(l, r):
            if not is_bg(*px[x, y]):
                if ba is None:
                    ba, ca, ea, fa = x, x, y, y
                else:
                    ba, ca, ea, fa = min(ba, x), max(ca, x), min(ea, y), max(fa, y)
    return (ba - 2, ea - 2, ca + 3, fa + 3)


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
        # RUN frames are packed tightly, so the all-pixel cut catches a
        # neighbour; use the connected body silhouette there instead (its
        # mid-stride legs are attached). Every other pose is an isolated frame.
        if name == "fungusbrute_run":
            a, c, e, f = _body_bbox(px, region)
            box = (a - 2, e - 2, c + 3, f + 3)
        else:
            box = crawler_bbox(px, region)
        img = cut(im, box)
        img.save(os.path.join(OUT, name + ".png"))
        print(f"{name}: box={box} size={img.size}")


if __name__ == "__main__":
    main()
