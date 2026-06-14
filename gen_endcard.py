#!/usr/bin/env python3
"""
Render a branded Boise Mold Removal end-card PNG (call-to-action).

    python3 gen_endcard.py                 # -> endcard.png (1280x720)
    python3 gen_endcard.py out.png --size 1920x1080

Brand colors/fonts mirror make_promo.py. Edit CONFIG to change the copy.
"""

import sys
from PIL import Image, ImageDraw, ImageFont

CONFIG = {
    "brand": "TyDez",
    "subtitle": "BOISE MOLD REMOVAL",
    "headline": "Breathe Easy Again",
    "phone": "(208) 495-5959",
    "email": "boisemoldremoval@gmail.com",
    "region": "Serving Boise & the Treasure Valley",
    "cta": "Call today for a free inspection",
}

FD = "/mnt/skills/examples/canvas-design/canvas-fonts"
F_DISPLAY = f"{FD}/BigShoulders-Bold.ttf"
F_BOLD = f"{FD}/Outfit-Bold.ttf"
F_REG = f"{FD}/Outfit-Regular.ttf"

C_TOP = (8, 58, 60)
C_BOTTOM = (4, 26, 40)
C_WHITE = (240, 250, 249)
C_MUTE = (150, 196, 196)
C_ACCENT = (86, 214, 165)
C_ACCENT2 = (120, 224, 232)


def font(path, size):
    return ImageFont.truetype(path, size)


def vgrad(w, h, top, bottom):
    base = Image.new("RGB", (w, h), top)
    top = bytes(top); bottom = bytes(bottom)
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        grad.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t)
                                    for i in range(3)))
    return Image.alpha_composite(base.convert("RGBA"),
                                 grad.resize((w, h)).convert("RGBA"))


def main():
    args = sys.argv[1:]
    out = "endcard.png"
    W, H = 1280, 720
    if "--size" in args:
        i = args.index("--size"); W, H = (int(x) for x in args[i + 1].lower().split("x"))
        del args[i:i + 2]
    if args:
        out = args[0]

    s = W / 1280.0  # scale relative to 720p design
    img = vgrad(W, H, C_TOP, C_BOTTOM)
    d = ImageDraw.Draw(img)

    cx = W // 2

    # accent rule above the wordmark
    rw = int(120 * s)
    d.rounded_rectangle([cx - rw, int(118 * s), cx + rw, int(126 * s)],
                        radius=int(4 * s), fill=C_ACCENT)

    # brand wordmark
    f_word = font(F_DISPLAY, int(150 * s))
    d.text((cx, int(210 * s)), CONFIG["brand"], font=f_word, fill=C_WHITE,
           anchor="mm")
    # subtitle (letter-spaced look via spacing)
    f_sub = font(F_BOLD, int(40 * s))
    d.text((cx, int(300 * s)), CONFIG["subtitle"], font=f_sub, fill=C_ACCENT2,
           anchor="mm")

    # headline
    f_head = font(F_BOLD, int(56 * s))
    d.text((cx, int(380 * s)), CONFIG["headline"], font=f_head, fill=C_WHITE,
           anchor="mm")

    # phone pill (the call-to-action hero)
    f_phone = font(F_DISPLAY, int(72 * s))
    pad_x, pad_y = int(46 * s), int(20 * s)
    bbox = d.textbbox((0, 0), CONFIG["phone"], font=f_phone)
    pw, ph = bbox[2] - bbox[0], bbox[3] - bbox[1]
    py = int(470 * s)
    box = [cx - pw // 2 - pad_x, py - pad_y,
           cx + pw // 2 + pad_x, py + ph + pad_y]
    d.rounded_rectangle(box, radius=int((ph + 2 * pad_y) / 2), fill=C_ACCENT)
    d.text((cx, py + ph // 2), CONFIG["phone"], font=f_phone,
           fill=C_BOTTOM, anchor="mm")

    # cta line
    f_cta = font(F_BOLD, int(30 * s))
    d.text((cx, int(588 * s)), CONFIG["cta"], font=f_cta, fill=C_WHITE,
           anchor="mm")

    # contact footer
    f_foot = font(F_REG, int(26 * s))
    foot = f"{CONFIG['email']}   •   {CONFIG['region']}"
    d.text((cx, int(648 * s)), foot, font=f_foot, fill=C_MUTE, anchor="mm")

    img.convert("RGB").save(out)
    print(f"Done -> {out}  ({W}x{H})")


if __name__ == "__main__":
    main()
