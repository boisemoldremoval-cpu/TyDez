#!/usr/bin/env python3
"""
Render synthesized DesilFuel motion-graphic scenes -> mp4 (silent), for use
as extra "scenes" in tie_together.py. All drawn in-container (no network / no
external AI). Matches the grunge look: dark toxic-green palette, film grain,
scanlines, acid-green accent.

    python3 make_scenes.py stinger  out.mp4 --dur 2.0 --text "PUTS MOLD TO SHAME"
    python3 make_scenes.py dissolve out.mp4 --dur 4.0
    python3 make_scenes.py jug      out.mp4 --dur 3.5
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

FPS = 24
C_ACID = (126, 240, 70)
C_GOLD = (214, 176, 72)
C_WHITE = (236, 255, 240)
RNG = np.random.default_rng(17)


def ease_out(t):
    return 1 - (1 - max(0.0, min(1.0, t))) ** 3


def vgrad(W, H, top, bottom):
    g = Image.new("RGB", (1, H))
    for y in range(H):
        f = y / max(1, H - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * f) for i in range(3)))
    return g.resize((W, H)).convert("RGB")


def fit_font(d, text, path, max_w, start):
    sz = start
    while sz > 12:
        f = ImageFont.truetype(path, sz)
        if d.textlength(text, font=f) <= max_w:
            return f
        sz -= 2
    return ImageFont.truetype(path, 12)


def grain_scan(img, amt=13):
    """Apply film grain + scanlines to a PIL RGB image."""
    W, H = img.size
    arr = np.asarray(img).astype(np.int16)
    arr = np.clip(arr + RNG.normal(0, amt, (H, W, 1)).astype(np.int16), 0, 255)
    scan = np.ones((H, W, 1), dtype=np.float32)
    scan[::3] = 0.84
    arr = (arr.astype(np.float32) * scan).astype(np.uint8)
    return Image.fromarray(arr)


# ----------------------------------------------------------------------------
def scene_stinger(W, H, N, text):
    s = W / 1280.0
    cx, cy = W // 2, H // 2
    bg = vgrad(W, H, (10, 14, 10), (3, 22, 9))
    tmp = ImageDraw.Draw(bg.copy())
    f = fit_font(tmp, text, F_DISPLAY, int(W * 0.88), int(150 * s))
    frames = []
    for i in range(N):
        t = i / FPS
        img = bg.copy()
        d = ImageDraw.Draw(img)
        p = t / 0.28
        scale = 1.45 - 0.45 * ease_out(p)
        a = min(1.0, t / 0.12)
        dx = int((1 + 9 * (1 - min(1, p))) * s)
        shake = int((1 - min(1, t / 0.18)) * 8 * s)
        oy = RNG.integers(-shake, shake + 1) if shake else 0
        # layer text on transparent, scale around center
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ld.text((cx - dx, cy + oy), text, font=f, fill=(255, 45, 45, 255), anchor="mm")
        ld.text((cx + dx, cy + oy), text, font=f, fill=(45, 255, 170, 255), anchor="mm")
        ld.text((cx, cy + oy), text, font=f, fill=(*C_WHITE, 255), anchor="mm")
        sw, sh = int(W * scale), int(H * scale)
        lay = lay.resize((sw, sh), Image.LANCZOS)
        if a < 1:
            lay.putalpha(lay.split()[3].point(lambda q: int(q * a)))
        img = img.convert("RGBA")
        img.alpha_composite(lay, ((W - sw) // 2, (H - sh) // 2))
        img = img.convert("RGB")
        d = ImageDraw.Draw(img)
        # acid underline wipes in
        uw = int(W * 0.3 * ease_out(t / 0.5))
        if uw > 4:
            d.rounded_rectangle([cx - uw, cy + int(95 * s), cx + uw, cy + int(104 * s)],
                                radius=int(4 * s), fill=C_ACID)
        # impact flash
        if i < 2:
            fl = Image.new("RGB", (W, H), (255, 255, 255))
            img = Image.blend(img, fl, 0.5 - 0.25 * i)
        frames.append(grain_scan(img))
    return frames


# ----------------------------------------------------------------------------
def _wood(W, H, moldy):
    base = np.empty((H, W, 3), np.float32)
    base[:] = (176, 131, 72)
    pw = W // 7
    for x in range(0, W, pw):
        base[:, x:x + 4] *= 0.55                       # plank gaps
    for _ in range(500):                               # grain streaks
        y = RNG.integers(0, H); x0 = RNG.integers(0, W); ln = RNG.integers(40, 240)
        base[y:y + 2, x0:x0 + ln] *= RNG.uniform(0.8, 1.12)
    base += RNG.normal(0, 6, (H, W, 3))
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    if not moldy:
        return img
    img = Image.eval(img, lambda p: int(p * 0.5))      # darken
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for _ in range(260):                               # mold blotches
        cxb = RNG.integers(0, W); cyb = RNG.integers(0, H)
        r = int(RNG.integers(16, 80))
        col = (int(RNG.integers(18, 55)), int(RNG.integers(45, 80)),
               int(RNG.integers(28, 55)), int(RNG.integers(60, 150)))
        d.ellipse([cxb - r, cyb - r // 2, cxb + r, cyb + r // 2], fill=col)
    img = img.convert("RGBA"); img.alpha_composite(ov)
    return img.convert("RGB")


def scene_dissolve(W, H, N):
    s = W / 1280.0
    clean = _wood(W, H, moldy=False)
    moldy = _wood(W, H, moldy=True)
    f_tag = ImageFont.truetype(F_BOLD, int(34 * s))
    frames = []
    for i in range(N):
        t = i / FPS
        p = ease_out(t / (N / FPS))                    # 0..1 across scene
        bx = int(W * (-0.1 + 1.2 * p))                 # cleaning boundary sweeps L->R
        img = moldy.copy()
        if bx > 0:
            img.paste(clean.crop((0, 0, min(bx, W), H)), (0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        # spray mist band at the boundary
        for _ in range(140):
            mx = int(RNG.normal(bx, 26 * s)); my = RNG.integers(0, H)
            rr = int(RNG.integers(1, 4))
            d.ellipse([mx - rr, my - rr, mx + rr, my + rr],
                      fill=(220, 255, 220, int(RNG.integers(40, 130))))
        d.rectangle([bx - int(6 * s), 0, bx + int(6 * s), H], fill=(235, 255, 235, 60))
        # before / after tags
        d.text((int(W * 0.78), int(H * 0.1)), "BEFORE", font=f_tag,
               fill=(210, 210, 200, 200), anchor="mm")
        if bx > W * 0.2:
            d.text((int(W * 0.12), int(H * 0.1)), "AFTER", font=f_tag,
                   fill=(*C_ACID, 230), anchor="mm")
        frames.append(grain_scan(img, amt=10))
    return frames


# ----------------------------------------------------------------------------
def _jug(s):
    JW, JH = int(300 * s), int(440 * s)
    PADX, PADY = int(40 * s), int(70 * s)
    im = Image.new("RGBA", (JW + 2 * PADX, JH + 2 * PADY), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bx0, by0 = PADX, PADY + int(60 * s)
    body = [bx0, by0, bx0 + JW, by0 + JH]
    d.rounded_rectangle(body, radius=int(38 * s), fill=(238, 241, 236, 255))
    # left highlight + right shade
    d.rounded_rectangle([bx0, by0, bx0 + int(JW * 0.32), by0 + JH],
                        radius=int(38 * s), fill=(255, 255, 252, 90))
    cx = bx0 + JW // 2
    capw = int(120 * s)
    d.rounded_rectangle([cx - capw // 2, PADY + int(8 * s), cx + capw // 2, by0 + int(8 * s)],
                        radius=int(14 * s), fill=(206, 209, 203, 255))
    # label
    lab = [bx0 + int(22 * s), by0 + int(86 * s), bx0 + JW - int(22 * s), by0 + JH - int(54 * s)]
    d.rounded_rectangle(lab, radius=int(10 * s), fill=(12, 13, 12, 255),
                        outline=C_GOLD, width=max(3, int(4 * s)))
    lcx = (lab[0] + lab[2]) // 2
    fg = ImageFont.truetype(F_DISPLAY, int(58 * s))
    fs = ImageFont.truetype(F_BOLD, int(19 * s))
    fs2 = ImageFont.truetype(F_DISPLAY, int(30 * s))
    d.text((lcx, lab[1] + int(46 * s)), "DesilFuel", font=fg, fill=C_GOLD, anchor="mm")
    d.text((lcx, lab[1] + int(96 * s)), "THE CHEMICAL THAT", font=fs, fill=(228, 230, 224), anchor="mm")
    d.text((lcx, lab[1] + int(120 * s)), "PUTS MOLD TO SHAME", font=fs, fill=(228, 230, 224), anchor="mm")
    d.text((lcx, lab[3] - int(34 * s)), "2.5 GAL", font=fs2, fill=C_GOLD, anchor="mm")
    return im


def scene_jug(W, H, N):
    s = W / 1280.0
    cx, cy = W // 2, int(H * 0.52)
    bg = vgrad(W, H, (12, 16, 12), (3, 20, 9))
    # acid radial glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = int(W * 0.28)
    for rr in range(gr, 0, -8):
        al = int(60 * (1 - rr / gr))
        gd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(*C_ACID, al))
    jug = _jug(s)
    # mist particles
    parts = [(RNG.integers(int(W * 0.3), int(W * 0.7)), RNG.integers(0, H),
              RNG.uniform(0.4, 1.0)) for _ in range(60)]
    frames = []
    for i in range(N):
        t = i / FPS
        img = bg.convert("RGBA").copy()
        gp = 0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * t)     # glow pulse
        g2 = glow.copy(); g2.putalpha(glow.split()[3].point(lambda q: int(q * gp)))
        img.alpha_composite(g2)
        # rising mist
        md = ImageDraw.Draw(img)
        for (px, py0, spd) in parts:
            py = int((py0 - t * 60 * spd) % H)
            rr = int(2 + 3 * spd)
            md.ellipse([px - rr, py - rr, px + rr, py + rr],
                       fill=(210, 255, 210, int(28 * spd)))
        # jug scales/fades in then slow push
        a = min(1.0, t / 0.5)
        scale = (0.9 + 0.1 * ease_out(t / 0.6)) + 0.04 * t
        jw, jh = int(jug.width * scale), int(jug.height * scale)
        j = jug.resize((jw, jh), Image.LANCZOS)
        if a < 1:
            j.putalpha(j.split()[3].point(lambda q: int(q * a)))
        img.alpha_composite(j, (cx - jw // 2, cy - jh // 2))
        # specular sweep across the jug
        sx = int(cx - jw / 2 + (jw + 40) * ((t / 1.4) % 1.0))
        spec = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(spec)
        sd.ellipse([sx - 30, cy - jh // 2, sx + 30, cy + jh // 2], fill=(255, 255, 255, 40))
        img.alpha_composite(spec)
        frames.append(grain_scan(img.convert("RGB"), amt=11))
    return frames


# ----------------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    if not args:
        print("usage: make_scenes.py {stinger|dissolve|jug} out.mp4 [--dur S] [--text T] [--size WxH]")
        raise SystemExit(1)
    scene = args[0]
    out = args[1] if len(args) > 1 and not args[1].startswith("--") else f"{scene}.mp4"

    def opt(flag, dflt):
        return args[args.index(flag) + 1] if flag in args else dflt

    dur = float(opt("--dur", "3.0"))
    text = opt("--text", "PUTS MOLD TO SHAME")
    W, H = (int(x) for x in opt("--size", "1280x720").lower().split("x"))
    N = int(dur * FPS)

    if scene == "stinger":
        frames = scene_stinger(W, H, N, text)
    elif scene == "dissolve":
        frames = scene_dissolve(W, H, N)
    elif scene == "jug":
        frames = scene_jug(W, H, N)
    else:
        raise SystemExit(f"unknown scene: {scene}")

    frdir = f"/tmp/_scene_{scene}"
    shutil.rmtree(frdir, ignore_errors=True)
    os.makedirs(frdir)
    for i, fr in enumerate(frames):
        fr.save(f"{frdir}/f_{i:04d}.png")

    cmd = [FF, "-y", "-framerate", str(FPS), "-i", f"{frdir}/f_%04d.png",
           "-t", f"{dur}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "18", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode()[-1500:]); raise SystemExit("encode failed")
    print(f"Done -> {out}  ({scene}, {W}x{H}, {dur}s)")


if __name__ == "__main__":
    main()
