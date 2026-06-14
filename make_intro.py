#!/usr/bin/env python3
"""
Render a grungy DesilFuel intro scene -> intro.mp4 (silent, for tie_together).

    python3 make_intro.py                 # -> intro.mp4 (1280x720, 3s)
    python3 make_intro.py out.mp4 --size 1920x1080 --dur 3

Look: dark toxic-green gradient, animated film grain, scanlines, and a
chromatic-split (RGB glitch) "DesilFuel" reveal with the tagline fading in.
"""

import os
import sys
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
FD = "/mnt/skills/examples/canvas-design/canvas-fonts"
F_DISPLAY = f"{FD}/BigShoulders-Bold.ttf"
F_BOLD = f"{FD}/Outfit-Bold.ttf"

WORD = "DESILFUEL"
TAG = "THE CHEMICAL THAT PUTS MOLD TO SHAME"
C_ACID = (126, 240, 70)


def ease_out(t):
    return 1 - (1 - max(0, min(1, t))) ** 3


def vgrad(W, H, top, bottom):
    g = Image.new("RGB", (1, H))
    for y in range(H):
        f = y / max(1, H - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * f)
                                 for i in range(3)))
    return g.resize((W, H))


def word_layer(W, H, text, font, cx, cy, dx):
    """White core with red/cyan chromatic-split copies (RGBA)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((cx - dx, cy), text, font=font, fill=(255, 45, 45, 255), anchor="mm")
    d.text((cx + dx, cy), text, font=font, fill=(45, 255, 170, 255), anchor="mm")
    d.text((cx, cy), text, font=font, fill=(238, 255, 240, 255), anchor="mm")
    return im


def main():
    args = sys.argv[1:]
    out = "intro.mp4"
    W, H, DUR = 1280, 720, 3.0
    FPS = 24
    if "--size" in args:
        i = args.index("--size"); W, H = (int(x) for x in args[i + 1].lower().split("x")); del args[i:i + 2]
    if "--dur" in args:
        i = args.index("--dur"); DUR = float(args[i + 1]); del args[i:i + 2]
    if args:
        out = args[0]

    s = W / 1280.0
    N = int(DUR * FPS)
    cx, cy = W // 2, int(H * 0.44)
    bg = vgrad(W, H, (10, 14, 10), (3, 22, 9))

    f_word = ImageFont.truetype(F_DISPLAY, int(150 * s))
    f_tag = ImageFont.truetype(F_BOLD, int(40 * s))

    # scanline darkening mask
    scan = np.ones((H, W, 1), dtype=np.float32)
    scan[::3] = 0.82

    rng = np.random.default_rng(3)
    frdir = "/tmp/_intro_frames"
    shutil.rmtree(frdir, ignore_errors=True)
    os.makedirs(frdir)

    for i in range(N):
        t = i / FPS
        img = bg.copy()
        d = ImageDraw.Draw(img)

        # top accent rule grows in
        rprog = ease_out(t / 0.5)
        rw = int(160 * s * rprog)
        if rw > 2:
            d.rounded_rectangle([cx - rw, int(150 * s), cx + rw, int(158 * s)],
                                radius=int(4 * s), fill=C_ACID)

        # wordmark reveal: scale-in + fade + settling chromatic split + flicker
        wp = t / 0.8
        a = max(0, min(1, wp))
        scale = 1.14 - 0.14 * ease_out(wp)
        dx = int((2 + 12 * (1 - min(1, wp))) * s) + (rng.integers(-1, 2) if t < 1.0 else 0)
        flick = 1.0 if t > 0.85 else (0.6 + 0.4 * rng.random())
        wl = word_layer(W, H, WORD, f_word, cx, cy, max(1, dx))
        sw, sh = max(1, int(W * scale)), max(1, int(H * scale))
        wl = wl.resize((sw, sh), Image.LANCZOS)
        al = a * flick
        if al < 1:
            wl.putalpha(wl.split()[3].point(lambda p: int(p * al)))
        img = img.convert("RGBA")
        img.alpha_composite(wl, ((W - sw) // 2, (H - sh) // 2))
        img = img.convert("RGB")
        d = ImageDraw.Draw(img)

        # tagline fades in
        if t > 1.1:
            ta = min(1, (t - 1.1) / 0.6)
            col = tuple(int(c * ta) for c in (235, 255, 240))
            d.text((cx, int(420 * s)), TAG, font=f_tag, fill=col, anchor="mm")

        # grain + scanlines
        arr = np.asarray(img).astype(np.int16)
        grain = rng.normal(0, 13, (H, W, 1)).astype(np.int16)
        arr = np.clip(arr + grain, 0, 255)
        arr = (arr.astype(np.float32) * scan).astype(np.uint8)
        Image.fromarray(arr).save(f"{frdir}/f_{i:04d}.png")

    cmd = [FF, "-y", "-framerate", str(FPS), "-i", f"{frdir}/f_%04d.png",
           "-t", f"{DUR}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "18", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode()[-1500:]); raise SystemExit("intro encode failed")
    print(f"Done -> {out}  ({W}x{H}, {DUR}s)")


if __name__ == "__main__":
    main()
