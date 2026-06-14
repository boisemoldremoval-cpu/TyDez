#!/usr/bin/env python3
"""
Wrap the 16:9 Boise Mold Removal cartoon into a 9:16 vertical social cut
(1080x1920) for Reels / TikTok / Shorts — branded teal frame with a shield
header and a phone-number CTA footer, the cartoon composited in the centre.

    python3 make_mold_vertical.py                       # mold_cartoon.mp4 -> mold_cartoon_vertical.mp4
    python3 make_mold_vertical.py in.mp4 out.mp4

Builds the backdrop with the same palette/fonts as make_mold_cartoon.py, then
composites the source video with ffmpeg (imageio-ffmpeg binary — no system ffmpeg).
"""

import sys
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw

import make_cartoon as M
import make_mold_cartoon as MM

VW, VH = 1080, 1920
VID_Y, VID_H = 656, 608   # 1080-wide source (16:9) lands here


def build_backdrop(path):
    top, bot = (14, 84, 70), (8, 46, 40)
    t = np.array(top, np.float32)
    b = np.array(bot, np.float32)
    r = np.linspace(0, 1, VH, dtype=np.float32)[:, None]
    g = (t[None, :] * (1 - r) + b[None, :] * r)
    img = Image.fromarray(np.repeat(g[:, None, :], VW, axis=1).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    # radial sheen centred on the video band
    cx, cy = VW / 2, 980
    for i in range(30):
        a = (i / 30) * math.tau
        col = (120, 230, 200, 14) if i % 2 == 0 else (80, 190, 160, 10)
        x2, y2 = cx + math.cos(a) * 2200, cy + math.sin(a) * 2200
        w = 70 if i % 2 == 0 else 40
        d.polygon([(cx, cy), (x2 + math.cos(a + .02) * w, y2 + math.sin(a + .02) * w),
                   (x2 - math.cos(a + .02) * w, y2 - math.sin(a + .02) * w)], fill=col)

    def ctext(s, fnt, y, color, track=0):
        M.ctext(M.D(img), s, fnt, y, color, 1.0, track=track, cx=VW / 2)

    # header
    MM.shield(d, VW / 2, 190, 74)
    ctext("BOISE MOLD REMOVAL", M.font(M.F_TITLE, 76), 330, (255, 255, 255))
    ctext("Veteran-owned · Treasure Valley · 24/7", M.font(M.F_REG, 34), 392, MM.TEAL, track=2)

    # video frame border
    d.rounded_rectangle([12, VID_Y - 14, VW - 12, VID_Y + VID_H + 14], radius=26,
                        outline=MM.TEAL, width=5)

    # footer CTA
    ctext("MOLD? GONE FOR GOOD.", M.font(M.F_BOLD, 58), 1430, (255, 255, 255))
    ctext("(208) 412-0899", M.font(M.F_TITLE, 116), 1560, MM.GOLD)
    ctext("boise-moldremoval.com", M.font(M.F_BOLD, 44), 1665, MM.TEAL)
    ctext("Free pre-inspection · Veteran discount", M.font(M.F_REG, 32), 1730, (210, 240, 230))

    img.convert("RGB").save(path)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "mold_cartoon.mp4"
    out = sys.argv[2] if len(sys.argv) > 2 else "mold_cartoon_vertical.mp4"
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    bg = "vertical_bg.png"
    print("Building branded backdrop...")
    build_backdrop(bg)

    print(f"Compositing {src} -> {out} ...")
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-loop", "1", "-i", bg, "-i", src,
        "-filter_complex",
        f"[1:v]scale={VW}:-2[v];[0:v][v]overlay=(W-w)/2:{VID_Y}:shortest=1[out]",
        "-map", "[out]", "-map", "1:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", out,
    ]
    subprocess.run(cmd, check=True)
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
