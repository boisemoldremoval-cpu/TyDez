"""Drawn, lightly-animated scene backgrounds for the TyGuy story."""

import math
import numpy as np
from PIL import Image, ImageDraw

W, H = 1280, 720
_yard_base = None


def _vgrad(top, bot, h):
    t = np.array(top, np.float32)
    b = np.array(bot, np.float32)
    r = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    g = t[None, :] * (1 - r) + b[None, :] * r
    return np.repeat(g[:, None, :], W, axis=1).astype(np.uint8)


def _build_yard_base():
    ground_y = int(H * 0.70)
    sky = _vgrad((120, 195, 245), (205, 236, 255), ground_y)
    img = Image.new("RGB", (W, H), (150, 205, 110))
    img.paste(Image.fromarray(sky, "RGB"), (0, 0))
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img)
    # ground
    d.rectangle([0, ground_y, W, H], fill=(150, 205, 110))
    d.rectangle([0, ground_y, W, ground_y + 12], fill=(132, 185, 96))
    # path
    d.polygon([(W * 0.32, H), (W * 0.46, H), (W * 0.56, ground_y), (W * 0.50, ground_y)],
              fill=(206, 196, 170))
    # school building (back-right)
    bx0, by0, bx1, by1 = W * 0.58, H * 0.30, W * 0.96, ground_y + 6
    d.rectangle([bx0, by0, bx1, by1], fill=(226, 198, 156))
    d.polygon([(bx0 - 18, by0), (bx1 + 18, by0), (bx1 - 30, by0 - 70),
               (bx0 + 30, by0 - 70)], fill=(176, 78, 66))  # roof
    # door
    d.rounded_rectangle([W * 0.73, by1 - 130, W * 0.80, by1], radius=8, fill=(120, 80, 55))
    d.ellipse([W * 0.785, by1 - 70, W * 0.792, by1 - 63], fill=(240, 220, 120))
    # windows
    for wx in (0.61, 0.665, 0.84, 0.895):
        for wy in (0.40, 0.53):
            d.rounded_rectangle([W * wx, H * wy, W * wx + 52, H * wy + 60],
                                radius=6, fill=(150, 205, 235),
                                outline=(235, 215, 175), width=5)
    # sign
    d.rounded_rectangle([W * 0.685, H * 0.315, W * 0.86, H * 0.355],
                        radius=8, fill=(60, 90, 150))
    # tree (left)
    d.rectangle([W * 0.13, ground_y - 130, W * 0.155, ground_y], fill=(120, 84, 54))
    for cxr, cyr, rr in [(0.143, 0.52, 95), (0.10, 0.56, 70), (0.185, 0.56, 70),
                         (0.143, 0.60, 80)]:
        d.ellipse([W * cxr - rr, H * cyr - rr, W * cxr + rr, H * cyr + rr],
                  fill=(86, 170, 92))
    # a small bench
    d.rectangle([W * 0.30, ground_y + 40, W * 0.46, ground_y + 54], fill=(150, 110, 70))
    d.rectangle([W * 0.31, ground_y + 54, W * 0.33, ground_y + 96], fill=(120, 86, 54))
    d.rectangle([W * 0.43, ground_y + 54, W * 0.45, ground_y + 96], fill=(120, 86, 54))
    return img


def schoolyard(t):
    global _yard_base
    if _yard_base is None:
        _yard_base = _build_yard_base()
    img = _yard_base.copy()
    d = ImageDraw.Draw(img, "RGBA")
    # sun + slow rotating rays
    sx, sy = W * 0.14, H * 0.16
    for i in range(12):
        a = i / 12 * math.tau + t * 0.15
        x1 = sx + math.cos(a) * 70
        y1 = sy + math.sin(a) * 70
        x2 = sx + math.cos(a) * 120
        y2 = sy + math.sin(a) * 120
        d.line([(x1, y1), (x2, y2)], fill=(255, 226, 120, 200), width=8)
    d.ellipse([sx - 56, sy - 56, sx + 56, sy + 56], fill=(255, 224, 110))
    d.ellipse([sx - 44, sy - 44, sx + 44, sy + 44], fill=(255, 238, 150))
    # drifting clouds
    for base_x, cy, sc, spd in [(0.30, 0.16, 1.0, 14), (0.62, 0.10, 0.8, 9),
                                (0.85, 0.20, 1.1, 18)]:
        cx = (base_x * W + t * spd) % (W + 320) - 160
        _cloud(d, cx, H * cy, sc)
    return img.convert("RGBA")


def _cloud(d, x, y, s):
    col = (255, 255, 255, 235)
    for dx, dy, r in [(-70, 10, 42), (-20, -8, 54), (40, 6, 46), (-15, 22, 50)]:
        d.ellipse([x + dx * s - r * s, y + dy * s - r * s,
                   x + dx * s + r * s, y + dy * s + r * s], fill=col)
