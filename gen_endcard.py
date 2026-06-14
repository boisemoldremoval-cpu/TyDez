#!/usr/bin/env python3
"""
Render the DesilFuel product end-card PNG (call-to-action).

    python3 gen_endcard.py                 # -> endcard.png (1280x720)
    python3 gen_endcard.py out.png --size 1920x1080

Edgy, product-forward card: DesilFuel wordmark, tagline, and phone number.
Edit CONFIG to change the copy.
"""

import sys
from PIL import Image, ImageDraw, ImageFont

CONFIG = {
    "name_a": "Desil",                              # white half of wordmark
    "name_b": "Fuel",                               # accent half
    "tagline": "THE CHEMICAL THAT PUTS MOLD TO SHAME",
    "phone": "(208) 495-5959",
}

FD = "/mnt/skills/examples/canvas-design/canvas-fonts"
F_DISPLAY = f"{FD}/BigShoulders-Bold.ttf"
F_BOLD = f"{FD}/Outfit-Bold.ttf"

C_TOP = (12, 14, 11)        # near-black
C_BOTTOM = (3, 20, 9)       # dark toxic green
C_WHITE = (236, 255, 240)
C_ACID = (126, 240, 70)     # acid green accent
C_DIM = (150, 196, 168)


def font(path, size):
    return ImageFont.truetype(path, size)


def vgrad(w, h, top, bottom):
    base = Image.new("RGBA", (w, h))
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        grad.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t)
                                    for i in range(3)))
    base.alpha_composite(grad.resize((w, h)).convert("RGBA"))
    return base


def fit_font(d, text, path, max_w, start):
    """Largest font size whose text width fits within max_w."""
    size = start
    while size > 10:
        f = font(path, size)
        if d.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(path, 10)


def main():
    args = sys.argv[1:]
    out = "endcard.png"
    W, H = 1280, 720
    if "--size" in args:
        i = args.index("--size"); W, H = (int(x) for x in args[i + 1].lower().split("x"))
        del args[i:i + 2]
    if args:
        out = args[0]

    s = W / 1280.0
    img = vgrad(W, H, C_TOP, C_BOTTOM)
    d = ImageDraw.Draw(img)
    cx = W // 2

    # top accent rule
    rw = int(150 * s)
    d.rounded_rectangle([cx - rw, int(150 * s), cx + rw, int(158 * s)],
                        radius=int(4 * s), fill=C_ACID)

    # DesilFuel wordmark (two-tone), centered
    fw = font(F_DISPLAY, int(168 * s))
    wa = d.textlength(CONFIG["name_a"], font=fw)
    wb = d.textlength(CONFIG["name_b"], font=fw)
    x0 = cx - (wa + wb) / 2
    ymid = int(285 * s)
    d.text((x0, ymid), CONFIG["name_a"], font=fw, fill=C_WHITE, anchor="lm")
    d.text((x0 + wa, ymid), CONFIG["name_b"], font=fw, fill=C_ACID, anchor="lm")

    # tagline (auto-fit to width, letter-spaced feel)
    f_tag = fit_font(d, CONFIG["tagline"], F_BOLD, int(W * 0.86), int(46 * s))
    d.text((cx, int(420 * s)), CONFIG["tagline"], font=f_tag, fill=C_WHITE,
           anchor="mm")

    # phone pill (hero CTA)
    f_phone = font(F_DISPLAY, int(78 * s))
    pad_x, pad_y = int(50 * s), int(22 * s)
    bbox = d.textbbox((0, 0), CONFIG["phone"], font=f_phone)
    pw, ph = bbox[2] - bbox[0], bbox[3] - bbox[1]
    py = int(520 * s)
    box = [cx - pw // 2 - pad_x, py - pad_y,
           cx + pw // 2 + pad_x, py + ph + pad_y]
    d.rounded_rectangle(box, radius=int((ph + 2 * pad_y) / 2), fill=C_ACID)
    d.text((cx, py + ph // 2), CONFIG["phone"], font=f_phone,
           fill=(6, 18, 8), anchor="mm")

    img.convert("RGB").save(out)
    print(f"Done -> {out}  ({W}x{H})")


if __name__ == "__main__":
    main()
