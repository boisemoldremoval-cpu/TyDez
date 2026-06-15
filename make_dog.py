"""
Cartoon dog renderer — same primitive-drawing approach as `characters.py`.

Draws a friendly sitting puppy from ellipses / rounded rectangles onto an RGBA
layer and saves a PNG. No external services or API credits required.

    python3 make_dog.py            # -> dog.png
    python3 make_dog.py pup.png    # custom output path
"""

import sys
from PIL import Image, ImageDraw


# --------------------------------------------------------------------------- #
# palette
# --------------------------------------------------------------------------- #
DOG = {
    "fur":        (214, 158, 96),    # golden-brown
    "fur_dark":   (180, 126, 70),    # ears / patches / shading
    "belly":      (244, 226, 198),   # lighter chest + muzzle
    "nose":       (54, 42, 40),
    "eye":        (40, 32, 30),
    "mouth":      (120, 60, 55),
    "tongue":     (232, 130, 130),
    "collar":     (62, 150, 120),    # TyDez green
    "tag":        (245, 210, 90),
    "outline":    (60, 44, 34),
}


def _ellipse(d, cx, cy, rx, ry, fill, outline=None, w=0):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill,
              outline=outline, width=w)


def draw_dog(base, cx, cy, scale, pal=DOG):
    """Draw a sitting cartoon dog centered horizontally on `cx`.

    `cy` is roughly the vertical center of the body; `scale` sets overall size.
    """
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    S = scale
    ol = pal["outline"]
    olw = max(2, int(S * 0.018))

    # ---- tail ----
    tail_x, tail_y = cx + S * 0.78, cy + S * 0.30
    d.pieslice([tail_x - S * 0.30, tail_y - S * 0.55,
                tail_x + S * 0.42, tail_y + S * 0.30],
               start=300, end=80, fill=pal["fur_dark"], outline=ol, width=olw)

    # ---- haunch / sitting body ----
    body_cy = cy + S * 0.42
    _ellipse(d, cx, body_cy, S * 0.62, S * 0.55, pal["fur"], ol, olw)
    # front legs
    for lx in (cx - S * 0.30, cx + S * 0.30):
        d.rounded_rectangle([lx - S * 0.15, body_cy + S * 0.05,
                             lx + S * 0.15, body_cy + S * 0.62],
                            radius=S * 0.14, fill=pal["fur"],
                            outline=ol, width=olw)
        # paw
        _ellipse(d, lx, body_cy + S * 0.60, S * 0.17, S * 0.11, pal["belly"])
    # chest blaze
    _ellipse(d, cx, body_cy + S * 0.12, S * 0.26, S * 0.40, pal["belly"])

    # ---- head ----
    head_cy = cy - S * 0.45
    # ears (behind head)
    for sgn in (-1, 1):
        ex = cx + sgn * S * 0.52
        d.pieslice([ex - S * 0.26, head_cy - S * 0.22,
                    ex + S * 0.26, head_cy + S * 0.62],
                   start=0, end=360, fill=pal["fur_dark"], outline=ol, width=olw)
    # head dome
    _ellipse(d, cx, head_cy, S * 0.50, S * 0.46, pal["fur"], ol, olw)
    # muzzle
    muzzle_cy = head_cy + S * 0.22
    _ellipse(d, cx, muzzle_cy, S * 0.34, S * 0.26, pal["belly"], ol, olw)

    # ---- face ----
    # eyes
    for sgn in (-1, 1):
        ex = cx + sgn * S * 0.21
        ey = head_cy - S * 0.05
        _ellipse(d, ex, ey, S * 0.11, S * 0.13, (250, 250, 250), ol, max(2, olw - 1))
        _ellipse(d, ex, ey + S * 0.02, S * 0.06, S * 0.07, pal["eye"])
        _ellipse(d, ex - S * 0.02, ey - S * 0.02, S * 0.02, S * 0.02, (255, 255, 255))
    # eyebrows (friendly)
    for sgn in (-1, 1):
        ex = cx + sgn * S * 0.21
        d.arc([ex - S * 0.12, head_cy - S * 0.26, ex + S * 0.12, head_cy - S * 0.02],
              start=200, end=340, fill=ol, width=olw)
    # nose
    nose_cy = muzzle_cy - S * 0.06
    _ellipse(d, cx, nose_cy, S * 0.10, S * 0.08, pal["nose"])
    _ellipse(d, cx - S * 0.03, nose_cy - S * 0.025, S * 0.025, S * 0.02, (120, 110, 108))
    # mouth
    d.line([(cx, nose_cy + S * 0.06), (cx, muzzle_cy + S * 0.10)],
           fill=ol, width=olw)
    d.arc([cx - S * 0.20, muzzle_cy - S * 0.04, cx, muzzle_cy + S * 0.18],
          start=20, end=160, fill=ol, width=olw)
    d.arc([cx, muzzle_cy - S * 0.04, cx + S * 0.20, muzzle_cy + S * 0.18],
          start=20, end=160, fill=ol, width=olw)
    # tongue
    d.rounded_rectangle([cx - S * 0.07, muzzle_cy + S * 0.10,
                         cx + S * 0.07, muzzle_cy + S * 0.26],
                        radius=S * 0.07, fill=pal["tongue"], outline=ol, width=olw)

    # ---- collar + tag ----
    collar_y = cy + S * 0.14
    d.rounded_rectangle([cx - S * 0.42, collar_y - S * 0.07,
                         cx + S * 0.42, collar_y + S * 0.07],
                        radius=S * 0.06, fill=pal["collar"], outline=ol, width=olw)
    _ellipse(d, cx, collar_y + S * 0.12, S * 0.09, S * 0.09, pal["tag"], ol, max(2, olw - 1))

    base.alpha_composite(layer)
    return base


def main(out="dog.png"):
    W, H = 900, 900
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    # soft background
    d.ellipse([W * 0.12, H * 0.74, W * 0.88, H * 0.96], fill=(225, 238, 232))
    draw_dog(img, W * 0.50, H * 0.46, scale=300)
    img.convert("RGB").save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dog.png")
