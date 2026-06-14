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


# ---- parable backgrounds ----
_DESERT = _CLUB = _INN = None


def desert_road(t):
    global _DESERT
    if _DESERT is None:
        sky = _vgrad((250, 225, 175), (245, 240, 220), int(H * 0.66))
        img = Image.new("RGB", (W, H), (224, 196, 150))
        img.paste(Image.fromarray(sky, "RGB"), (0, 0)); img = img.convert("RGBA")
        d = ImageDraw.Draw(img)
        gy = int(H * 0.66)
        # distant hills
        for hx, hr, c in [(220, 150, (214, 188, 150)), (640, 200, (206, 178, 138)),
                          (1050, 170, (214, 188, 150))]:
            d.ellipse([hx - hr, gy - hr * 0.7, hx + hr, gy + hr], fill=c)
        d.rectangle([0, gy, W, H], fill=(224, 196, 150))      # sand
        # winding road
        d.polygon([(W * 0.30, gy), (W * 0.70, gy), (W * 1.05, H), (W * -0.05, H)], fill=(210, 182, 138))
        d.polygon([(W * 0.40, gy), (W * 0.60, gy), (W * 0.78, H), (W * 0.22, H)], fill=(202, 174, 130))
        # rocks + bushes
        rng = np.random.default_rng(8)
        for _ in range(16):
            rx, ry = rng.uniform(0, W), rng.uniform(gy + 20, H - 30)
            r = rng.uniform(12, 30)
            d.ellipse([rx - r, ry - r * 0.6, rx + r, ry + r * 0.6], fill=(168, 150, 120))
        for _ in range(12):
            bx, by = rng.uniform(0, W), rng.uniform(gy + 10, H - 40)
            d.ellipse([bx - 22, by - 14, bx + 22, by + 10], fill=(120, 150, 80))
        _DESERT = img
    img = _DESERT.copy(); d = ImageDraw.Draw(img, "RGBA")
    sx, sy = W * 0.82, H * 0.16
    d.ellipse([sx - 50, sy - 50, sx + 50, sy + 50], fill=(255, 238, 170))
    return img.convert("RGBA")


def club_room(t):
    global _CLUB
    if _CLUB is None:
        img = Image.fromarray(_vgrad((236, 214, 186), (222, 198, 168), H), "RGB").convert("RGBA")
        d = ImageDraw.Draw(img)
        fy = int(H * 0.70)
        d.rectangle([0, fy, W, H], fill=(178, 138, 96))               # wood floor
        for i in range(0, W, 90):
            d.line([(i, fy), (i + 40, H)], fill=(160, 122, 84), width=2)
        d.ellipse([W * 0.28, H * 0.80, W * 0.72, H * 1.02], fill=(200, 90, 90))   # rug
        d.ellipse([W * 0.33, H * 0.83, W * 0.67, H * 0.99], fill=(220, 170, 90))
        # bookshelf
        d.rectangle([W * 0.04, fy - 180, W * 0.20, fy], fill=(140, 100, 66))
        for r in range(3):
            yy = fy - 170 + r * 56
            for bx in range(int(W * 0.05), int(W * 0.19), 18):
                d.rectangle([bx, yy, bx + 14, yy + 46],
                            fill=tuple(int(c) for c in np.random.default_rng(bx + r).integers(60, 220, 3)))
        # window
        d.rectangle([W * 0.74, fy - 200, W * 0.94, fy - 40], fill=(150, 205, 235), outline=(150, 110, 70), width=8)
        d.line([(W * 0.84, fy - 200), (W * 0.84, fy - 40)], fill=(150, 110, 70), width=6)
        d.line([(W * 0.74, fy - 120), (W * 0.94, fy - 120)], fill=(150, 110, 70), width=6)
        # bunting banner
        for i in range(8):
            x = W * 0.30 + i * 60
            col = [(230, 80, 80), (240, 200, 70), (80, 160, 220)][i % 3]
            d.polygon([(x, 40), (x + 50, 40), (x + 25, 95)], fill=col)
        _CLUB = img
    return _CLUB.copy()


def inn(t):
    global _INN
    if _INN is None:
        img = Image.fromarray(_vgrad((250, 180, 120), (120, 90, 140), int(H * 0.7)), "RGB").convert("RGBA")
        d = ImageDraw.Draw(img)
        gy = int(H * 0.74)
        d.rectangle([0, gy, W, H], fill=(120, 100, 80))
        # inn building
        bx0, by0 = W * 0.30, H * 0.26
        d.rectangle([bx0, by0, W * 0.80, gy], fill=(206, 184, 150))
        d.polygon([(bx0 - 24, by0), (W * 0.80 + 24, by0), (W * 0.80 - 40, by0 - 70),
                   (bx0 + 40, by0 - 70)], fill=(150, 100, 80))
        d.rounded_rectangle([W * 0.50, gy - 150, W * 0.60, gy], radius=10, fill=(110, 74, 50))  # door
        for wx in (0.35, 0.68):
            d.rectangle([W * wx, by0 + 50, W * wx + 60, by0 + 120], fill=(255, 220, 120),
                        outline=(150, 100, 70), width=5)                # glowing windows
        # lantern
        d.ellipse([W * 0.62, gy - 150, W * 0.66, gy - 130], fill=(255, 220, 120))
        _INN = img
    return _INN.copy()
