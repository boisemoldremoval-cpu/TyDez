#!/usr/bin/env python3
"""Hand-drawn retro superhero dog — a static hero illustration.

Vintage-comic look: bold ink outlines, flat cel colors, sunburst + halftone
background. Rendered at 2x then downscaled for smooth 'hand-inked' edges.
Output: retro_dog_hero.png
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = 2                      # supersample factor
W, H = 1280, 720
CW, CH = W * S, H * S
OUT = Path(__file__).parent / "retro_dog_hero.png"

# --- retro palette ---
CREAM   = (245, 236, 214)
MUSTARD = (233, 196, 106)
TEAL    = (54, 128, 124)
TEAL_D  = (38, 98, 96)
RED     = (201, 74, 63)
RED_D   = (168, 56, 48)
FUR     = (236, 210, 166)
FUR_D   = (206, 172, 120)
INK     = (38, 32, 30)
ORANGE  = (222, 132, 66)
CREAMHI = (252, 246, 232)

def s(v): return int(v * S)
def pts(seq): return [(s(x), s(y)) for x, y in seq]
def bb(x0, y0, x1, y1): return [s(x0), s(y0), s(x1), s(y1)]

img = Image.new("RGB", (CW, CH), CREAM)
d = ImageDraw.Draw(img)
LW = s(5)   # ink line width


def sunburst(cx, cy, n=24, rad=1600):
    step = 360 / n
    for i in range(n):
        a0 = math.radians(i * step)
        a1 = math.radians((i + 1) * step)
        col = MUSTARD if i % 2 == 0 else CREAMHI
        poly = [(s(cx), s(cy)),
                (s(cx + rad * math.cos(a0)), s(cy + rad * math.sin(a0))),
                (s(cx + rad * math.cos(a1)), s(cy + rad * math.sin(a1)))]
        d.polygon(poly, fill=col)


def halftone(cx, cy, maxr, dot=9, gap=22, color=ORANGE):
    """Radial halftone: dots shrink toward the edge (retro shading)."""
    r = int(maxr)
    y = -r
    while y <= r:
        x = -r
        while x <= r:
            dist = math.hypot(x, y)
            if dist <= r:
                dd = dot * (1 - dist / r)
                if dd > 1:
                    px, py = cx + x, cy + y
                    d.ellipse(bb(px - dd, py - dd, px + dd, py + dd), fill=color)
            x += gap
        y += gap


def outline_ellipse(box, fill):
    d.ellipse(bb(*box), fill=fill, outline=INK, width=LW)

def outline_poly(seq, fill):
    d.polygon(pts(seq), fill=fill, outline=INK)
    # thicken the polygon edge manually
    p = pts(seq) + [pts(seq)[0]]
    d.line(p, fill=INK, width=LW, joint="curve")

def outline_round(box, r, fill):
    d.rounded_rectangle(bb(*box), radius=s(r), fill=fill, outline=INK, width=LW)


# ---------- background ----------
sunburst(560, 300)
halftone(1080, 600, 260)
halftone(150, 150, 200)

# soft ground shadow under the hero
d.ellipse(bb(330, 650, 780, 705), fill=(210, 190, 150))

# ---------- CAPE (behind body) ----------
outline_poly([(470, 235), (760, 300), (800, 560), (700, 640),
              (660, 560), (600, 650), (540, 540), (500, 470)], RED)
# cape inner shading
d.polygon(pts([(560, 300), (720, 340), (740, 540), (660, 560),
               (620, 470), (580, 420)]), fill=RED_D)

# ---------- LEGS + boots ----------
outline_round((470, 470, 528, 650), 22, TEAL)
outline_round((548, 470, 606, 650), 22, TEAL)
outline_round((452, 620, 540, 678), 20, RED)   # left boot
outline_round((540, 620, 628, 678), 20, RED)   # right boot

# ---------- ARMS (fists on hips) ----------
outline_poly([(410, 300), (470, 320), (470, 430), (420, 440),
              (372, 400), (372, 340)], TEAL)     # left upper arm
outline_poly([(610, 320), (668, 300), (700, 340), (700, 400),
              (652, 440), (610, 430)], TEAL)     # right upper arm
outline_ellipse((376, 400, 452, 470), RED)       # left glove/fist
outline_ellipse((624, 400, 700, 470), RED)       # right glove/fist

# ---------- TORSO ----------
outline_ellipse((406, 250, 672, 500), TEAL)
# belt
outline_round((418, 452, 660, 496), 10, ORANGE)
d.ellipse(bb(524, 456, 556, 492), fill=CREAM, outline=INK, width=LW)  # belt buckle

# chest emblem — cream shield with a bone
d.ellipse(bb(468, 296, 612, 432), fill=CREAMHI, outline=INK, width=LW)
# bone icon
by = 364
d.line([(s(500), s(by)), (s(580), s(by))], fill=INK, width=s(16))
for cx in (500, 580):
    d.ellipse(bb(cx - 16, by - 20, cx + 4, by), fill=INK)
    d.ellipse(bb(cx - 16, by, cx + 4, by + 20), fill=INK)
    d.ellipse(bb(cx - 4, by - 20, cx + 16, by), fill=INK)
    d.ellipse(bb(cx - 4, by, cx + 16, by + 20), fill=INK)

# ---------- HEAD ----------
# ears (behind head)
outline_poly([(360, 150), (430, 120), (452, 210), (400, 260)], FUR_D)
outline_poly([(720, 150), (650, 120), (628, 210), (680, 260)], FUR_D)
# head
outline_ellipse((404, 70, 676, 320), FUR)
# muzzle
outline_ellipse((470, 200, 610, 312), CREAMHI)
# nose
d.ellipse(bb(516, 214, 564, 250), fill=INK)
d.ellipse(bb(524, 220, 540, 232), fill=(90, 78, 72))   # nose highlight
# mouth / grin
d.arc(bb(486, 236, 594, 300), 20, 160, fill=INK, width=LW)
d.line([(s(540), s(250)), (s(540), s(276))], fill=INK, width=LW)
# tongue
d.pieslice(bb(524, 282, 566, 316), 0, 180, fill=RED)
# eyes
for ex in (470, 610):
    d.ellipse(bb(ex - 26, 150, ex + 26, 202), fill=CREAMHI, outline=INK, width=LW)
    d.ellipse(bb(ex - 12, 162, ex + 12, 194), fill=INK)
    d.ellipse(bb(ex - 6, 166, ex + 4, 176), fill=CREAMHI)
# domino mask
outline_poly([(440, 138), (640, 138), (656, 168), (600, 210),
              (540, 188), (480, 210), (424, 168)], TEAL_D)

# ---------- render + downscale ----------
img = img.filter(ImageFilter.GaussianBlur(0.4))
img = img.resize((W, H), Image.LANCZOS)

# ---------- retro title ----------
d2 = ImageDraw.Draw(img)
def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()

def banner_text(txt, cx, cy, fs, fill, outline=INK, ow=4):
    f = font(fs)
    bbx = d2.textbbox((0, 0), txt, font=f)
    tw, th = bbx[2] - bbx[0], bbx[3] - bbx[1]
    x, y = cx - tw / 2, cy - th / 2
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            d2.text((x + dx, y + dy), txt, font=f, fill=outline)
    d2.text((x, y), txt, font=f, fill=fill)

# title on the right side
banner_text("CAPTAIN", 990, 250, 78, MUSTARD)
banner_text("BARK", 990, 335, 104, RED)
banner_text("- super good boy -", 990, 415, 30, TEAL_D, ow=2)

img.save(OUT)
print("wrote", OUT)
