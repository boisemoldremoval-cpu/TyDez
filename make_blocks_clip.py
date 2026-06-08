#!/usr/bin/env python3
"""
"The Block Tower" -- a cel-shaded 2D Bible Kid Adventures short (10s / 720p / 24fps).

Recreates the look of the reference Veo clip with the repo's own offline pipeline:
TyGuy joyfully builds a colorful toy-block castle in a sunny, flower-filled
meadow; another boy storms over and kicks it down; TyGuy is hurt while the other
stands cross and grumpy. Polished with DoF, warm key light, vignette, drifting
bokeh and a gentle camera push-in, plus a soft music bed and the series logo.

    pip install Pillow numpy imageio-ffmpeg
    python3 make_blocks_clip.py            # -> blocks_clip.mp4
    python3 make_blocks_clip.py out.mp4    # custom output path
"""
import sys
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import imageio_ffmpeg
import make_own2d as O          # cinematic() + add_bokeh()
import make_cartoon as M        # generate_music()
import kid

W, H, FPS, DUR = 1280, 720, 24, 10.0
GROUND = int(H * 0.94)
OUT = sys.argv[1] if len(sys.argv) > 1 else "blocks_clip.mp4"

FONT = "/mnt/skills/examples/canvas-design/canvas-fonts/EricaOne-Regular.ttf"

# antagonist: auburn hair, green tee, grey shorts (matches the reference kid)
BULLY = {
    "skin": (236, 190, 152), "skin_sh": (212, 166, 128),
    "hair": (170, 86, 44), "hair_sh": (138, 66, 32),       # auburn
    "shirt": (96, 178, 110), "shirt_sh": (74, 146, 88),    # green tee
    "pants": (120, 124, 132), "pants_sh": (96, 100, 108),  # grey shorts
    "shoe": (60, 62, 70), "ponytail": False,
}


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(t): return 1 - (1 - clamp(t)) ** 3
def ease(t): return 0.5 * (1 - math.cos(math.pi * clamp(t)))
def lerp(a, b, t): return a + (b - a) * t
def blink(t, s=0.0): return 1 if (t * 0.5 + s) % 1.0 > 0.93 else 0


# --------------------------------------------------------------------------- #
# meadow background (sunny park: sky, hills, trees, grass, many flowers)
# --------------------------------------------------------------------------- #
_BG = None


def meadow():
    global _BG
    if _BG:
        return _BG.copy()
    sky = np.zeros((H, W, 3), np.float32)
    top = np.array([120, 190, 240]); bot = np.array([198, 232, 250])
    for y in range(H):
        sky[y] = top + (bot - top) * (y / H)
    img = Image.fromarray(sky.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    gy = int(H * 0.52)
    # soft clouds
    for cx, cy, s in ((W * 0.22, H * 0.16, 70), (W * 0.62, H * 0.10, 90),
                      (W * 0.85, H * 0.22, 60)):
        for ox, oy, r in ((0, 0, s), (-s * 0.7, s * 0.2, s * 0.7),
                          (s * 0.7, s * 0.2, s * 0.75), (0, s * 0.3, s * 0.9)):
            d.ellipse([cx + ox - r, cy + oy - r * 0.7,
                       cx + ox + r, cy + oy + r * 0.7], fill=(255, 255, 255, 230))
    # rolling back hills
    d.ellipse([-W * 0.2, gy - 120, W * 0.6, gy + 260], fill=(150, 205, 120))
    d.ellipse([W * 0.45, gy - 90, W * 1.25, gy + 280], fill=(138, 198, 112))
    # grass
    d.rectangle([0, gy, W, H], fill=(150, 206, 104))
    d.rectangle([0, gy, W, gy + 4], fill=(120, 180, 90))

    # background trees
    def tree(tx, ty, s, c1, c2):
        d.rectangle([tx - s * 0.10, ty, tx + s * 0.10, ty + s * 0.5],
                    fill=(120, 84, 54))
        for ox, oy, r in ((0, -s * 0.55, s * 0.62), (-s * 0.5, -s * 0.25, s * 0.5),
                          (s * 0.5, -s * 0.25, s * 0.5), (0, -s * 0.05, s * 0.55)):
            d.ellipse([tx + ox - r, ty + oy - r, tx + ox + r, ty + oy + r], fill=c1)
        for ox, oy, r in ((-s * 0.2, -s * 0.5, s * 0.34), (s * 0.25, -s * 0.3, s * 0.3)):
            d.ellipse([tx + ox - r, ty + oy - r, tx + ox + r, ty + oy + r], fill=c2)

    for tx, frac, s in ((W * 0.10, 0.0, 150), (W * 0.30, 0.0, 120),
                        (W * 0.74, 0.0, 165), (W * 0.92, 0.0, 130),
                        (W * 0.52, 0.0, 110)):
        ty = gy - s * 0.05
        tree(tx, ty, s, (78, 158, 78), (104, 188, 100))

    # tons of little flowers across the grass
    rng = np.random.default_rng(7)
    palette = [(240, 90, 110), (250, 210, 70), (240, 140, 200),
               (255, 255, 255), (150, 120, 235), (255, 150, 70)]
    for _ in range(220):
        fx = rng.uniform(0, W)
        depth = rng.uniform(0, 1)
        fy = lerp(gy + 12, H - 6, depth)
        r = lerp(3, 8, depth)
        c = tuple(int(v) for v in palette[rng.integers(len(palette))])
        for a in range(0, 360, 72):
            px = fx + math.cos(math.radians(a)) * r
            py = fy + math.sin(math.radians(a)) * r
            d.ellipse([px - r * 0.7, py - r * 0.7, px + r * 0.7, py + r * 0.7], fill=c)
        d.ellipse([fx - r * 0.5, fy - r * 0.5, fx + r * 0.5, fy + r * 0.5],
                  fill=(255, 235, 120))
    _BG = img
    return _BG.copy()


# --------------------------------------------------------------------------- #
# toy blocks
# --------------------------------------------------------------------------- #
BLOCK_COLS = [(225, 78, 78), (70, 135, 215), (245, 205, 70),
              (96, 188, 120), (245, 150, 64), (168, 116, 205)]
_CUBE_CACHE = {}


def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def cube_img(s, col, emblem=True):
    key = (s, col, emblem)
    if key in _CUBE_CACHE:
        return _CUBE_CACHE[key]
    dep = int(s * 0.30)
    sz = s + dep + 6
    im = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = 3, 3 + dep
    fr = [(ox, oy), (ox + s, oy + s)]
    top = [(ox, oy), (ox + dep, oy - dep), (ox + s + dep, oy - dep), (ox + s, oy)]
    rt = [(ox + s, oy), (ox + s + dep, oy - dep),
          (ox + s + dep, oy + s - dep), (ox + s, oy + s)]
    ol = (34, 26, 30)
    d.polygon(top, fill=_shade(col, 1.20), outline=ol)
    d.polygon(rt, fill=_shade(col, 0.74), outline=ol)
    d.rounded_rectangle(fr, radius=int(s * 0.10), fill=col, outline=ol,
                        width=max(2, s // 22))
    # face highlight
    d.line([(ox + s * 0.18, oy + s * 0.18), (ox + s * 0.18, oy + s * 0.5)],
           fill=_shade(col, 1.35), width=max(2, s // 18))
    if emblem:
        m = s * 0.22
        d.rounded_rectangle([ox + m, oy + m, ox + s - m, oy + s - m],
                            radius=int(s * 0.06), outline=(255, 250, 240),
                            width=max(2, s // 20))
    _CUBE_CACHE[key] = im
    return im


def roof_img(s, col):
    key = ("roof", s, col)
    if key in _CUBE_CACHE:
        return _CUBE_CACHE[key]
    dep = int(s * 0.30)
    sz = s + dep + 6
    im = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = 3, 3 + dep
    ol = (34, 26, 30)
    # right (back) gable face
    d.polygon([(ox + s, oy + s), (ox + s + dep, oy + s - dep),
               (ox + s * 0.5 + dep, oy - dep), (ox + s * 0.5, oy)],
              fill=_shade(col, 0.74), outline=ol)
    # front gable triangle
    d.polygon([(ox, oy + s), (ox + s, oy + s), (ox + s * 0.5, oy)],
              fill=col, outline=ol, width=max(2, s // 22))
    _CUBE_CACHE[key] = im
    return im


def paste_block(base, im, cx, cy, rot=0.0, scale=1.0):
    g = im
    if scale != 1.0:
        nw = max(1, int(im.width * scale))
        g = im.resize((nw, nw), Image.LANCZOS)
    if abs(rot) > 0.5:
        g = g.rotate(rot, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(g, (int(cx - g.width / 2), int(cy - g.height / 2)))


# castle layout: (col_index, grid_x, grid_y, is_roof)   grid origin = top of base
CS = 50
TX = W * 0.52
BASE_Y = GROUND - 8
TOWER = [
    (0, -1, 0, False), (1, 0, 0, False), (2, 1, 0, False),   # base row
    (3, -1, 1, False), (4, 1, 1, False),                     # gate sides
    (1, -0.5, 2, False), (2, 0.5, 2, False),                 # mid row
    (3, 0, 3, False),                                        # tip cube
    (0, 0, 4, True),                                         # red roof
]


def _stacked_pos(gx, gy):
    return (TX + gx * CS, BASE_Y - gy * CS - CS * 0.5)


# deterministic scatter targets after the kick
_SC = np.random.default_rng(3)
_SCATTER = []
for i, (_c, gx, gy, _r) in enumerate(TOWER):
    side = 1 if i % 2 else -1
    rx = TX + side * _SC.uniform(0.5, 3.4) * CS + gx * 6
    ry = GROUND - _SC.uniform(2, 16)
    spin = _SC.uniform(140, 520) * side
    arc = _SC.uniform(70, 150)
    _SCATTER.append((rx, ry, spin, arc))

KICK = 5.05          # moment of impact
SETTLE = 1.25        # time for blocks to land & settle


def draw_tower(base, t):
    """Build the tower (0..3.3s), hold, then scatter it after the kick."""
    for i, (ci, gx, gy, is_roof) in enumerate(TOWER):
        s = CS
        col = BLOCK_COLS[ci]
        im = roof_img(s, BLOCK_COLS[0]) if is_roof else cube_img(s, col)
        sx, sy = _stacked_pos(gx, gy)

        if t < KICK:
            # build: each block drops into place in order
            appear = 0.35 + i * 0.33
            p = clamp((t - appear) / 0.42)
            if p <= 0:
                continue
            y = lerp(sy - 230, sy, ease(p))
            sc = lerp(0.6, 1.0, ease(p))
            paste_block(base, im, sx, y, 0, sc)
        else:
            rx, ry, spin, arc = _SCATTER[i]
            kp = clamp((t - KICK) / SETTLE)
            if kp <= 0:
                paste_block(base, im, sx, sy)
                continue
            ek = ease(kp)
            x = lerp(sx, rx, ek)
            y = lerp(sy, ry, ek) - math.sin(math.pi * kp) * arc
            rot = spin * kp
            paste_block(base, im, x, y, rot)


def dust(d, t):
    """A small dust puff at the impact point right after the kick."""
    p = clamp((t - KICK) / 0.55)
    if p <= 0 or p >= 1:
        return
    cx, cy = TX - CS * 0.6, GROUND - CS * 0.4
    for k in range(7):
        a = k / 7 * math.tau
        rr = lerp(6, 60, p)
        px = cx + math.cos(a) * rr
        py = cy - abs(math.sin(a)) * rr * 0.7
        r = lerp(6, 22, p)
        al = int(160 * (1 - p))
        d.ellipse([px - r, py - r, px + r, py + r], fill=(225, 215, 195, al))


def tear(d, cx, cy, s, a=1.0):
    al = int(235 * a)
    d.ellipse([cx - s * 0.6, cy - s * 0.4, cx + s * 0.6, cy + s], fill=(150, 205, 245, al))
    d.polygon([(cx, cy - s), (cx - s * 0.45, cy - s * 0.1),
               (cx + s * 0.45, cy - s * 0.1)], fill=(150, 205, 245, al))
    d.ellipse([cx - s * 0.3, cy - s * 0.1, cx + s * 0.05, cy + s * 0.3],
              fill=(225, 245, 255, al))


# --------------------------------------------------------------------------- #
# characters
# --------------------------------------------------------------------------- #
def draw_tyguy(base, t):
    """TyGuy: kneeling & building, then hurt after the tower falls."""
    if t < KICK - 0.2:
        # kneeling, reaching toward the tower, happy
        b = math.sin(t * 4) * 4
        kid.draw_kid(base, W * 0.30, GROUND + 26, 250, kid.KID_TYGUY,
                     {"arm_l": 8, "arm_r": 64, "elbow": 18, "lean": 12,
                      "mouth": "open" if (t * 2) % 1 > 0.5 else "smile",
                      "brow": "happy", "look": 1, "blink": blink(t)})
    else:
        # stands, shocked then sad
        p = clamp((t - KICK) / 0.9)
        mouth = "open" if p < 0.55 else "sad"
        brow = "sad"
        kid.draw_kid(base, W * 0.30, GROUND, 285, kid.KID_TYGUY,
                     {"arm_l": 26, "arm_r": 22, "elbow": 10,
                      "mouth": mouth, "brow": brow, "look": 1,
                      "blink": blink(t)})
        if t > KICK + 1.4:
            d = ImageDraw.Draw(base, "RGBA")
            tt = (t - (KICK + 1.4)) % 2.2
            fall = clamp(tt / 1.6)
            ty = lerp(GROUND - 285 * 0.66, GROUND - 285 * 0.52, fall)
            tear(d, W * 0.30 + 285 * 0.085, ty, 7, a=clamp(1 - fall))


def draw_bully(base, t):
    """Antagonist runs in from the right, kicks, then stands cross-armed."""
    if t < 3.6:
        return
    d = ImageDraw.Draw(base, "RGBA")
    if t < KICK:
        # run in toward the tower
        p = eo(clamp((t - 3.6) / (KICK - 3.6)))
        x = lerp(W * 1.12, W * 0.66, p)
        lean = lerp(2, 16, p)
        kid.draw_kid(base, x, GROUND, 300, BULLY,
                     {"walk": (t * 2.4) % 1, "arm_l": 26, "arm_r": -18,
                      "lean": lean, "mouth": "neutral", "brow": "sad",
                      "look": -1, "blink": blink(t, 1)})
    else:
        # planted by the rubble, arms low, grumpy & defiant
        sway = math.sin(t * 1.5) * 2
        kid.draw_kid(base, W * 0.74, GROUND, 300, BULLY,
                     {"arm_l": 40, "arm_r": 40, "elbow": -30, "lean": sway,
                      "mouth": "sad", "brow": "sad", "look": -1,
                      "blink": blink(t, 1)})


# --------------------------------------------------------------------------- #
# series logo: "Bible Kid Adventures"
# --------------------------------------------------------------------------- #
_LOGO = None
LOGO_COLS = [(64, 150, 232), (255, 200, 48), (228, 82, 82), (96, 190, 120),
             (245, 150, 56), (170, 112, 206)]


def _outline_letter(d, x, y, ch, font, fill, ow):
    for dx in range(-ow, ow + 1, 2):
        for dy in range(-ow, ow + 1, 2):
            if dx * dx + dy * dy <= ow * ow:
                d.text((x + dx, y + dy), ch, font=font, fill=(255, 255, 255), anchor="lm")
    for dx in (-ow - 2, ow + 2):
        d.text((x + dx, y), ch, font=font, fill=(28, 30, 60), anchor="lm")
    d.text((x, y), ch, font=font, fill=fill, anchor="lm")


def build_logo():
    global _LOGO
    if _LOGO:
        return _LOGO
    f1 = ImageFont.truetype(FONT, 96)
    f2 = ImageFont.truetype(FONT, 56)
    pad = 60
    top = "Bible Kid"
    bot = "Adventures"
    tmp = Image.new("RGBA", (10, 10))
    td = ImageDraw.Draw(tmp)
    w1 = sum(td.textlength(c, font=f1) for c in top)
    w2 = td.textlength(bot, font=f2)
    cw = int(max(w1, w2) + pad * 2)
    ch = int(96 + 56 + 80)
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # top word, per-letter colors
    x = (cw - w1) / 2
    yc = 60
    ci = 0
    for c in top:
        if c == " ":
            x += td.textlength(" ", font=f1)
            continue
        _outline_letter(d, x, yc, c, f1, LOGO_COLS[ci % len(LOGO_COLS)], 6)
        x += td.textlength(c, font=f1)
        ci += 1
    # bottom word in blue
    bx = (cw - w2) / 2
    by = 60 + 70
    for dx in range(-5, 6, 2):
        for dy in range(-5, 6, 2):
            d.text((bx + dx, by + dy), bot, font=f2, fill=(255, 255, 255), anchor="lm")
    d.text((bx, by), bot, font=f2, fill=(58, 130, 226), anchor="lm")
    _LOGO = im
    return im


def overlay_logo(rgb, t):
    """Logo pops in during the happy build, fades as the conflict starts."""
    if t > 5.4:
        return rgb
    a = clamp(t / 0.5)
    if t > 4.7:
        a = clamp((5.4 - t) / 0.7)
    pop = O.eo(clamp(t / 0.6)) if t < 0.6 else 1.0
    logo = build_logo()
    sc = lerp(0.86, 1.0, pop) * 0.92
    lw, lh = int(logo.width * sc), int(logo.height * sc)
    g = logo.resize((lw, lh), Image.LANCZOS)
    if a < 1:
        g.putalpha(g.split()[3].point(lambda p: int(p * a)))
    out = rgb.convert("RGBA")
    out.alpha_composite(g, ((W - lw) // 2, int(H * 0.66) - lh // 2))
    return out.convert("RGB")


# --------------------------------------------------------------------------- #
def frame_at(t):
    base = meadow().filter(ImageFilter.GaussianBlur(5))
    draw_tower(base, t)
    draw_tyguy(base, t)
    draw_bully(base, t)
    d = ImageDraw.Draw(base, "RGBA")
    dust(d, t)
    O.add_bokeh(base, t)
    zoom = lerp(1.07, 1.0, eo(t / DUR))
    dx = lerp(-14, 14, t / DUR)
    out = O.cinematic(base, t, zoom, dx, 0)     # -> RGB
    out = overlay_logo(out, t)
    return np.asarray(out, dtype=np.uint8)


def main():
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(DUR * FPS)
    print(f"blocks clip: {DUR:.0f}s, {n} frames -> {OUT}")
    M.generate_music("musicB.wav", DUR + 0.3)
    amix = ("[1:a]volume=0.5,afade=t=out:st=" + f"{DUR-1:.2f}" + ":d=1,"
            "aresample=48000,aformat=channel_layouts=stereo[a]")
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", "musicB.wav",
           "-filter_complex", amix, "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
           "-crf", "18", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
           "-ac", "2", "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(n):
        p.stdin.write(frame_at(i / FPS).tobytes())
        if i % 48 == 0:
            print(f"  {i}/{n}")
    p.stdin.close()
    p.wait()
    print(f"Done -> {OUT}")


if __name__ == "__main__":
    main()
