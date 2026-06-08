#!/usr/bin/env python3
"""
Brand any clip with the "Bible Kids Adventures" bottom banner (+ optional music).

    python3 brand_clip.py input.mp4                       # add bottom banner only
    python3 brand_clip.py input.mp4 --music track.mp3     # add banner + music bed
    python3 brand_clip.py input.mp4 --music track.mp3 --out branded.mp4

Reusable series branding: animated bottom-center "BIBLE KIDS / ADVENTURES" title
that pops in and stays (gentle fade at the end). Matches any resolution/fps/length.
"""

import os
import re
import sys
import math
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FONT = "/mnt/skills/examples/canvas-design/canvas-fonts/EricaOne-Regular.ttf"
FF = imageio_ffmpeg.get_ffmpeg_exe()


def probe(path):
    out = subprocess.run([FF, "-i", path], stderr=subprocess.PIPE).stderr.decode()
    dur = 10.0
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    if m:
        h, mn, s = m.groups()
        dur = int(h) * 3600 + int(mn) * 60 + float(s)
    w, hh = 1280, 720
    m = re.search(r", (\d{2,5})x(\d{2,5})", out)
    if m:
        w, hh = int(m.group(1)), int(m.group(2))
    fps = 24.0
    m = re.search(r"(\d+(?:\.\d+)?) fps", out)
    if m:
        fps = float(m.group(1))
    has_audio = "Audio:" in out
    return dur, w, hh, fps, has_audio


def outlined(d, xy, text, font, fill, ow, outline=(25, 18, 8)):
    x, y = xy
    for dx in range(-ow, ow + 1, 2):
        for dy in range(-ow, ow + 1, 2):
            d.text((x + dx, y + dy), text, font=font, fill=outline, anchor="mm")
    d.text((x, y), text, font=font, fill=fill, anchor="mm")


def build_title(W):
    cw = int(W * 0.37)
    ch = int(cw * 150 / 470)
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = int(ch * 0.15)
    d.rounded_rectangle([6, 6, cw - 6, ch - 6], radius=r, fill=(40, 120, 222, 225),
                        outline=(255, 210, 45, 255), width=max(4, cw // 90))
    f1 = ImageFont.truetype(FONT, int(ch * 0.40))
    f2 = ImageFont.truetype(FONT, int(ch * 0.29))
    ow = max(2, cw // 130)
    outlined(d, (cw // 2, int(ch * 0.38)), "BIBLE KIDS", f1, (255, 214, 45), ow)
    outlined(d, (cw // 2, int(ch * 0.72)), "ADVENTURES", f2, (255, 255, 255), ow)
    return im


def eob(t):
    t = max(0, min(1, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def main():
    args = sys.argv[1:]
    music = None
    if "--music" in args:
        i = args.index("--music"); music = args[i + 1]; del args[i:i + 2]
    out = "branded.mp4"
    if "--out" in args:
        i = args.index("--out"); out = args[i + 1]; del args[i:i + 2]
    if not args:
        print("usage: brand_clip.py input.mp4 [--music track.mp3] [--out file.mp4]")
        raise SystemExit(1)
    src = args[0]
    dur, W, H, fps, has_audio = probe(src)
    n = int(dur * fps)
    print(f"branding {src}  {W}x{H} {fps}fps {dur:.1f}s")

    ovdir = "/tmp/bka_ov"
    shutil.rmtree(ovdir, ignore_errors=True)
    os.makedirs(ovdir)
    title = build_title(W)
    fade_start = max(0.5, dur - 0.7)
    for i in range(n):
        t = i / fps
        fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if t < 0.5:
            s, a = 0.3 + 0.7 * eob(t / 0.5), min(1, t / 0.3)
        elif t < fade_start:
            s, a = 1.0, 1.0
        else:
            s, a = 1.0, max(0, (dur - t) / 0.7)
        tw, th = max(1, int(title.width * s)), max(1, int(title.height * s))
        ti = title.resize((tw, th), Image.LANCZOS)
        if a < 1:
            ti.putalpha(ti.split()[3].point(lambda p: int(p * a)))
        fr.alpha_composite(ti, ((W - tw) // 2, H - th - int(H * 0.035)))
        fr.save(f"{ovdir}/ov_{i:05d}.png")

    cmd = [FF, "-y", "-i", src, "-framerate", str(fps), "-i", f"{ovdir}/ov_%05d.png"]
    if music:
        cmd += ["-i", music]
    cmd += ["-filter_complex"]
    if music and has_audio:
        fc = (f"[0:v][1:v]overlay=0:0:format=auto[v];"
              f"[2:a]atrim=0:{dur},afade=t=out:st={max(0,dur-1)}:d=1,volume=0.4,"
              f"aresample=48000,aformat=channel_layouts=stereo[m];"
              f"[0:a]volume=0.95,aresample=48000,aformat=channel_layouts=stereo[o];"
              f"[o][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.97[a]")
        amap = ["-map", "[v]", "-map", "[a]"]
    elif music:
        fc = (f"[0:v][1:v]overlay=0:0:format=auto[v];"
              f"[2:a]atrim=0:{dur},afade=t=out:st={max(0,dur-1)}:d=1,"
              f"aresample=48000,aformat=channel_layouts=stereo[a]")
        amap = ["-map", "[v]", "-map", "[a]"]
    else:
        fc = "[0:v][1:v]overlay=0:0:format=auto[v]"
        amap = ["-map", "[v]"] + (["-map", "0:a"] if has_audio else [])
    cmd += [fc] + amap + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                          "-c:a", "aac", "-b:a", "192k", "-shortest",
                          "-movflags", "+faststart", out]
    r = subprocess.run(cmd, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode()[-1500:]); raise SystemExit("brand failed")
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
