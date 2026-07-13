#!/usr/bin/env python3
"""Cut Ty's crouch poses from the Batch-4 chroma-green animation sheet.

Recipe (matches the one used throughout the project):
  crop the pose from the sheet -> flood-fill the solid green background from
  the edges -> keep the largest connected shape (protects enclosed lime armor
  accents / eyes) -> light green de-spill -> autocrop.

NOTE: this sheet is OFF-MODEL. The official art bible (CHR_001 / PLR_001) and
every shipped player sprite draw Ty as the blue-and-white armored kid; this
sheet is a darker, older tactical design. So the cuts are written to
art_reference/ (preserved, one rename from use) and are NOT dropped into
assets/ -- shipping them would make Ty change character whenever he crouches.
See ty_tactical_crouch_cuts/README.md.
"""
import os
from collections import deque
from PIL import Image

SHEET = "art_reference/pending/upload_new_8ea6eccc.png"
OUT = "art_reference/ty_tactical_crouch_cuts"

# (dest_key, (left, top, right, bottom)) on the 1536x1024 sheet.
POSES = {
    "player_crouch": (18, 150, 285, 345),          # 1. CROUCH IDLE (gun ready)
    "player_crouch_shoot": (1230, 150, 1520, 345),  # 5. CROUCH FIRE (muzzle flash)
}


def is_bg(r, g, b):
    """Absolute chroma-green background test. The sheet's background is a
    solid medium green (~58,121,8): green-dominant with near-zero blue. The
    figure's lime armor accents also read green, but they are enclosed by dark
    armor, so the border-connected flood never reaches them."""
    return b < 45 and g > 40 and (g - r) > 20 and (g - b) > 35


def flood_bg(px, w, h):
    """Mark background-green pixels reachable from any border. Returns a
    bytearray mask (1 = background)."""
    bg = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            i = y * w + x
            if not bg[i] and is_bg(*px[i]):
                bg[i] = 1; q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            i = y * w + x
            if not bg[i] and is_bg(*px[i]):
                bg[i] = 1; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                j = ny * w + nx
                if not bg[j] and is_bg(*px[j]):
                    bg[j] = 1
                    q.append((nx, ny))
    return bg


def is_greenish(r, g, b):
    return g > r + 25 and g > b + 25


def keep_largest(alpha, w, h):
    """Keep only the largest connected component of opaque pixels."""
    seen = bytearray(w * h)
    best = []
    best_n = 0
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
            if len(comp) > best_n:
                best_n = len(comp)
                best = comp
    keep = set(best)
    out = bytearray(w * h)
    for idx in keep:
        out[idx] = 255
    return out


def cut(sheet, box):
    crop = sheet.crop(box).convert("RGB")
    w, h = crop.size
    px = list(crop.getdata())
    bg = flood_bg(px, w, h)

    # alpha: opaque where NOT background
    alpha = bytearray(w * h)
    for i in range(w * h):
        alpha[i] = 0 if bg[i] else 255
    # drop specks / bg islands: keep largest connected opaque shape
    alpha = keep_largest(alpha, w, h)

    out = Image.new("RGBA", (w, h))
    op = out.load()
    src = crop.load()
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if alpha[i]:
                r, g, b = src[x, y]
                # light de-spill: tame green fringe on edge pixels
                edge = (x == 0 or y == 0 or x == w - 1 or y == h - 1 or
                        alpha[i - 1] == 0 or alpha[i + 1 if i + 1 < w * h else i] == 0 or
                        (y > 0 and alpha[i - w] == 0) or
                        (y < h - 1 and alpha[i + w] == 0))
                if edge and is_greenish(r, g, b):
                    g = int((r + b) / 2 + g) // 2
                op[x, y] = (r, g, b, 255)
            else:
                op[x, y] = (0, 0, 0, 0)

    # autocrop to content
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    return out


def main():
    sheet = Image.open(SHEET).convert("RGB")
    for key, box in POSES.items():
        img = cut(sheet, box)
        dest = os.path.join(OUT, key + ".png")
        img.save(dest)
        print(f"{key}: {img.size} -> {dest}")


if __name__ == "__main__":
    main()
