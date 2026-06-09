#!/usr/bin/env python3
"""
Boise Mold Removal — local 2D cartoon ad ("Mold? Gone for good.").

Renders mold_cartoon.mp4 (1280x720, 24fps) with a warm music bed, entirely
offline using the repo's own 2D engine (no Arcads / no API key):

  - characters.py  -> the technician "Ty" and the homeowner
  - make_cartoon.py -> fonts, caption/speech banners, easing, music, encode

Story (4-beat anthropomorphized-problem arc):
  1. Hook       "Moldy" the smug mold patch gloats in a damp crawlspace.
  2. Reveal     Ty the Boise Mold Removal tech shows up, flashlight on.
  3. Mechanism  the chibi Crew HEPA-scrub & seal; Moldy shrinks away.
  4. CTA        clean home, happy homeowner, phone + brand card.

    python3 make_mold_cartoon.py            # -> mold_cartoon.mp4
    python3 make_mold_cartoon.py out.mp4    # custom path
"""

import sys
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw

import make_cartoon as M
import characters as C

W, H = M.WIDTH, M.HEIGHT
FPS = M.FPS
GROUND = M.GROUND
TAU = math.tau

# ── brand palette ──────────────────────────────────────────────────────────
TEAL = (86, 214, 165)      # #56D6A5 brand accent
TEAL_D = (30, 150, 120)    # work-polo teal
TEAL_DK = (16, 92, 78)
CREAM = (245, 247, 240)
INK = (24, 38, 42)
GOLD = (255, 205, 80)

# technician "Ty" — teal Boise Mold Removal polo, light stubble
TECH = {
    "skin": (235, 190, 158), "hair": (44, 34, 30), "beard": (60, 48, 42),
    "shirt": TEAL_D, "shirt_dark": (22, 120, 96),
    "pants": (44, 50, 62), "shoe": (235, 240, 248), "shoe_accent": TEAL_D,
    "cross": False, "beard_on": True,
}

_rng = np.random.default_rng(7)
MOLD_BUMPS = [((i / 24) * TAU, 0.82 + _rng.uniform(-0.16, 0.16)) for i in range(24)]


# ── small drawing helpers ──────────────────────────────────────────────────
def base_rgb(top, bot):
    return Image.fromarray(M._vgrad(top, bot), "RGB").convert("RGBA")


def shield(d, cx, cy, s, fill=CREAM, outline=TEAL_DK):
    """White brand shield with a teal check-drop."""
    pts = [(cx - s, cy - s), (cx + s, cy - s), (cx + s, cy + s * 0.3),
           (cx, cy + s * 1.25), (cx - s, cy + s * 0.3)]
    d.polygon(pts, fill=fill, outline=outline)
    # teal droplet
    dx, dy, r = cx, cy - s * 0.05, s * 0.42
    d.polygon([(dx, dy - r * 1.4), (dx - r, dy + r * 0.4), (dx + r, dy + r * 0.4)], fill=TEAL_D)
    d.ellipse([dx - r, dy - r * 0.2, dx + r, dy + r], fill=TEAL_D)
    d.ellipse([dx - r * 0.4, dy - r * 0.2, dx + r * 0.1, dy + r * 0.4], fill=(225, 255, 245))


def cap(d, head_cx, head_cy, head_r, color=TEAL_D):
    """A ballcap stamped over the character's head."""
    d.chord([head_cx - head_r * 1.05, head_cy - head_r * 1.35,
             head_cx + head_r * 1.05, head_cy + head_r * 0.45],
            start=180, end=360, fill=color)
    d.rounded_rectangle([head_cx - head_r * 0.2, head_cy - head_r * 1.05,
                         head_cx + head_r * 1.5, head_cy - head_r * 0.6],
                        radius=head_r * 0.2, fill=color)  # brim
    d.ellipse([head_cx - head_r * 0.16, head_cy - head_r * 1.32,
               head_cx + head_r * 0.16, head_cy - head_r * 1.0], fill=GOLD)  # button/patch


def brand_chip(d):
    """Persistent small brand chip, top-left."""
    d.rounded_rectangle([24, 22, 360, 74], radius=14, fill=(12, 60, 52, 210))
    sd = ImageDraw.Draw(d._image)
    shield(sd, 52, 46, 18)
    d.text((84, 34), "BOISE MOLD REMOVAL", font=M.font(M.F_BOLD, 26), fill=CREAM)
    d.text((84, 54), "Treasure Valley · 24/7", font=M.font(M.F_REG, 18), fill=TEAL)


def draw_moldy(base, cx, cy, size, t, mood="smug", talking=False):
    """The anthropomorphic mold-patch villain."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # fuzzy body
    pts = []
    for i, (ang, rf) in enumerate(MOLD_BUMPS):
        wob = math.sin(t * 3 + i * 1.3) * 0.05
        r = size * (rf + wob)
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r * 0.82))
    d.polygon(pts, fill=(44, 56, 40))
    # texture specks
    sp = np.random.default_rng(11)
    for _ in range(46):
        ang = sp.uniform(0, TAU)
        rr = sp.uniform(0.12, 0.9) * size
        x = cx + math.cos(ang) * rr
        y = cy + math.sin(ang) * rr * 0.82
        col = [(74, 96, 56), (34, 44, 30), (96, 116, 72)][int(sp.integers(0, 3))]
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=col)
    # eyes
    ex, ey, er = size * 0.34, cy - size * 0.14, size * 0.21
    for sx in (-1, 1):
        X = cx + sx * ex
        d.ellipse([X - er, ey - er, X + er, ey + er], fill=(250, 250, 244))
        pdx = sx * er * 0.15
        d.ellipse([X - er * 0.4 + pdx, ey - er * 0.15, X + er * 0.4 + pdx, ey + er * 0.65],
                  fill=(20, 20, 20))
        if mood == "smug":   # half-lidded lids
            d.chord([X - er, ey - er, X + er, ey + er], start=185, end=355, fill=(44, 56, 40))
        elif mood == "worried":
            d.arc([X - er * 1.2, ey - er * 1.4, X + er * 1.2, ey + er * 0.2],
                  start=200, end=340, fill=(250, 250, 244), width=max(2, int(er * 0.3)))
    # mouth
    mw, my = size * 0.4, cy + size * 0.3
    if talking:
        d.ellipse([cx - mw * 0.5, my - mw * 0.3, cx + mw * 0.5, my + mw * 0.6], fill=(20, 22, 18))
    elif mood == "smug":
        d.arc([cx - mw, my - mw * 0.7, cx + mw, my + mw * 0.7], start=18, end=130,
              fill=(20, 22, 18), width=max(3, int(size * 0.06)))
    else:  # worried small o
        d.ellipse([cx - mw * 0.28, my - mw * 0.1, cx + mw * 0.28, my + mw * 0.5], fill=(20, 22, 18))
    # spore puffs when talking
    if talking:
        for k in range(5):
            ph = (t * 0.9 + k * 0.2) % 1.0
            px = cx + math.sin(k * 2 + t) * size * 0.5
            py = cy - size * 0.8 - ph * size * 0.7
            a = int(120 * (1 - ph))
            rr = 6 + ph * 10
            d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(120, 150, 90, a))
    base.alpha_composite(layer)


def draw_crew(base, x, y, s, t, k=0):
    """A chibi ivory cleanup mascot, scrubbing."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bob = math.sin(t * 6 + k) * s * 0.08
    y = y + bob
    d.ellipse([x - s, y - s * 1.1, x + s, y + s], fill=(244, 244, 236))  # body
    d.ellipse([x - s, y - s * 0.55, x + s, y + s], fill=(232, 232, 222))  # belly shade
    # hard-hat
    d.chord([x - s * 1.05, y - s * 1.7, x + s * 1.05, y - s * 0.4], start=180, end=360, fill=TEAL_D)
    d.rectangle([x - s * 1.05, y - s * 0.75, x + s * 1.05, y - s * 0.6], fill=TEAL_D)
    # eyes
    for sx in (-1, 1):
        d.ellipse([x + sx * s * 0.4 - s * 0.18, y - s * 0.35,
                   x + sx * s * 0.4 + s * 0.18, y + s * 0.05], fill=(20, 20, 20))
    # cheeks
    for sx in (-1, 1):
        d.ellipse([x + sx * s * 0.62 - s * 0.12, y - s * 0.02,
                   x + sx * s * 0.62 + s * 0.12, y + s * 0.18], fill=(255, 190, 190))
    # scrub arm
    swing = math.sin(t * 9 + k) * s * 0.5
    hx, hy = x + s * 0.9, y - s * 0.1 + swing
    d.line([(x + s * 0.5, y - s * 0.1), (hx, hy)], fill=(232, 232, 222), width=max(3, int(s * 0.3)))
    d.rectangle([hx - s * 0.3, hy - s * 0.18, hx + s * 0.3, hy + s * 0.18], fill=GOLD)  # brush
    base.alpha_composite(layer)


# ── backgrounds ────────────────────────────────────────────────────────────
def bg_crawlspace(stain=1.0):
    img = base_rgb((58, 52, 48), (28, 26, 24))
    d = ImageDraw.Draw(img)
    # wood joists (ceiling beams)
    for jx in range(-1, 9):
        x = jx * 170
        d.rectangle([x, 60, x + 46, 240], fill=(96, 74, 52))
        d.rectangle([x, 60, x + 46, 76], fill=(120, 96, 68))
    d.rectangle([0, 60, W, 84], fill=(82, 62, 44))
    # dirt floor
    d.rectangle([0, 560, W, H], fill=(48, 40, 34))
    d.rectangle([0, 560, W, 576], fill=(60, 50, 42))
    # damp water stain bleeding down from the ceiling boards (subtle, brownish)
    if stain > 0:
        sd = ImageDraw.Draw(img, "RGBA")
        st = np.random.default_rng(5)
        for _ in range(14):
            bx = st.uniform(1010, 1180)
            by = st.uniform(86, 230)
            r = st.uniform(26, 64)
            sd.ellipse([bx - r, by - r * 0.7, bx + r, by + r * 0.7],
                       fill=(70, 64, 40, int(46 * stain)))
    # dim light shaft
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(150, 0), (320, 0), (470, H), (40, H)], fill=(255, 240, 200, 16))
    img.alpha_composite(sh)
    return img


def bg_house(bright=1.0):
    sky_top = (150, 200, 240)
    img = base_rgb(sky_top, (214, 236, 250))
    d = ImageDraw.Draw(img)
    # sun
    d.ellipse([90, 70, 190, 170], fill=(255, 238, 170))
    # lawn
    d.rectangle([0, 540, W, H], fill=(120, 195, 110))
    d.rectangle([0, 540, W, 558], fill=(140, 210, 125))
    # house on the right
    hx = 880
    d.rectangle([hx, 250, hx + 360, 560], fill=(238, 232, 220))      # wall
    d.polygon([(hx - 20, 250), (hx + 180, 140), (hx + 380, 250)], fill=(176, 80, 70))  # roof
    d.rectangle([hx + 150, 410, hx + 230, 560], fill=(120, 84, 60))  # door
    d.ellipse([hx + 216, 480, hx + 226, 490], fill=GOLD)             # knob
    for wx in (hx + 40, hx + 270):                                   # windows
        d.rectangle([wx, 300, wx + 70, 370], fill=(150, 205, 235))
        d.line([(wx + 35, 300), (wx + 35, 370)], fill=(238, 232, 220), width=4)
        d.line([(wx, 335), (wx + 70, 335)], fill=(238, 232, 220), width=4)
    return img


def bg_section():
    """Cutaway: house floor on top, dark crawlspace cavity where the crew works."""
    img = base_rgb((196, 214, 230), (176, 198, 218))
    d = ImageDraw.Draw(img)
    # house floor band
    d.rectangle([0, 90, W, 250], fill=(214, 226, 236))
    d.rectangle([0, 232, W, 268], fill=(120, 90, 62))   # floor boards
    for x in range(0, W, 120):
        d.line([(x, 232), (x, 268)], fill=(98, 72, 48), width=3)
    d.text((40, 130), "UNDER THE HOUSE", font=M.font(M.F_BOLD, 30), fill=(70, 92, 110))
    # crawlspace cavity
    d.rectangle([0, 268, W, H], fill=(40, 36, 32))
    for jx in range(0, W, 200):
        d.rectangle([jx + 30, 268, jx + 70, 360], fill=(86, 66, 46))  # posts
    d.rectangle([0, H - 60, W, H], fill=(54, 46, 38))   # dirt
    return img


def card(t, lines):
    """Teal brand card with a radial sheen; `lines` = list of (text, fontpath, size, color, ypos)."""
    img = base_rgb((22, 132, 108), (12, 78, 66))
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = W / 2, H * 0.42
    for i in range(26):
        a = (i / 26) * TAU + t * 0.1
        col = (140, 230, 200, 26) if i % 2 == 0 else (90, 200, 165, 18)
        x2, y2 = cx + math.cos(a) * 1700, cy + math.sin(a) * 1700
        wdt = 60 if i % 2 == 0 else 34
        d.polygon([(cx, cy), (x2 + math.cos(a + .02) * wdt, y2 + math.sin(a + .02) * wdt),
                   (x2 - math.cos(a + .02) * wdt, y2 - math.sin(a + .02) * wdt)], fill=col)
    return img


# ── scenes (each fn(t, dur) -> RGB image) ──────────────────────────────────
def sc_title(t, dur):
    img = card(t, None)
    d = M.D(img)
    a = M.ease(t / 0.7) * M.ease((dur - t) / 0.6)
    pop = M.eo(t / 0.7)
    sd = ImageDraw.Draw(img)
    shield(sd, W / 2, H * 0.24, 46 * pop)
    M.ctext(d, "BOISE MOLD REMOVAL", M.font(M.F_REG, 38), H * 0.46, TEAL, a, track=6)
    M.ctext(d, "MOLD? GONE FOR GOOD.", M.font(M.F_TITLE, 96), H * 0.60, (255, 255, 255), a * pop)
    M.ctext(d, "a Treasure Valley cartoon", M.font(M.F_REG, 28), H * 0.78, (210, 240, 230), a)
    return img.convert("RGB")


def sc_hook(t, dur):
    img = bg_crawlspace(stain=1.0)
    d = M.D(img)
    brand_chip(d)
    pulse = 1.0 + math.sin(t * 2.0) * 0.03
    talking = (t % 1.4) < 0.9 and t > 0.6
    draw_moldy(img, 660, 360, 150 * pulse, t, mood="smug", talking=talking)
    a = M.ease(t / 0.6) * M.ease((dur - t) / 0.6)
    if t > 0.5:
        M.speech(d, 660, 150, "Ahh... I LOVE your damp crawlspace. I'm never leaving!",
                 M.ease((t - 0.5) / 0.5) * a)
    M.caption(d, "Meet Moldy. He moves into damp crawlspaces — and gets comfy.", a)
    return img.convert("RGB")


def sc_reveal(t, dur):
    img = bg_house(bright=1.0)
    d = M.D(img)
    brand_chip(d)
    move_t = dur * 0.5
    if t < move_t:
        x = M.lerp(-160, 470, M.eo(t / move_t))
        pose = {"walk": (t * 1.7) % 1, "arm_l": 14, "arm_r": 14, "mouth": "smile", "brow": "happy"}
    else:
        x = 470
        wave = math.sin((t - move_t) * 7) * 16
        pose = {"arm_r": 92 + wave, "elbow_r": 10, "arm_l": 16, "mouth": "open", "brow": "happy"}
    C.draw_person(img, x, GROUND, 380, TECH, pose)
    # stamp cap + chest shield onto Ty
    sd = ImageDraw.Draw(img)
    head_cx, head_cy, head_r = x, GROUND - 380 * 0.90, 380 * 0.16
    cap(sd, head_cx, head_cy, head_r)
    shield(sd, x, GROUND - 380 * 0.60, 18)
    a = M.ease(t / 0.6) * M.ease((dur - t) / 0.6)
    if t > move_t + 0.2:
        M.speech(d, x, GROUND - 400, "Not on my watch. Boise Mold Removal — on it!",
                 M.ease((t - move_t - 0.2) / 0.4) * a)
    M.caption(d, "Ty rolls up — veteran-owned, 24/7, free pre-inspection.", a)
    return img.convert("RGB")


def sc_mechanism(t, dur):
    img = bg_section()
    d = M.D(img)
    brand_chip(d)
    p = M.clamp(t / (dur - 0.4))
    # Moldy shrinks and gets worried in the cavity corner
    sz = M.lerp(120, 18, M.eo(p))
    draw_moldy(img, 980, 430, sz, t, mood="worried", talking=False)
    # crew advances toward Moldy, scrubbing
    for k in range(3):
        cxk = M.lerp(180 + k * 120, 760 + k * 70, M.eo(p))
        draw_crew(img, cxk, 470, 36, t, k)
    # teal "clean" sweep wiping left->right
    sweep_x = M.lerp(120, 1040, M.eo(p))
    sw = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sw).rectangle([sweep_x - 80, 268, sweep_x + 30, H], fill=(120, 230, 195, 90))
    ImageDraw.Draw(sw).rectangle([0, 268, sweep_x - 80, H], fill=(120, 230, 195, 26))
    img.alpha_composite(sw)
    a = M.ease(t / 0.6) * M.ease((dur - t) / 0.6)
    M.caption(d, "HEPA scrub. Full remediation. Sealed, dried — gone.", a)
    return img.convert("RGB")


def sc_happy(t, dur):
    img = bg_house(bright=1.0)
    d = M.D(img)
    brand_chip(d)
    b1, bl1 = M.idle(t, 1)
    b2, bl2 = M.idle(t, 3)
    # homeowner (left) waves
    C.draw_person(img, 470, GROUND + b1 * 0.4, 360, C.MIA,
                  {"mouth": "smile", "brow": "happy", "blink": bl1, "arm_l": 46, "elbow_l": 10})
    # Ty (center) waves
    wave = math.sin(t * 6) * 16
    C.draw_person(img, 690, GROUND + b2 * 0.4, 380, TECH,
                  {"mouth": "smile", "brow": "happy", "blink": bl2, "arm_r": 72 + wave, "elbow_r": 12})
    sd = ImageDraw.Draw(img)
    head_cx, head_cy, head_r = 690, GROUND - 380 * 0.90 + b2 * 0.4, 380 * 0.16
    cap(sd, head_cx, head_cy, head_r)
    shield(sd, 690, GROUND - 380 * 0.60 + b2 * 0.4, 18)
    # sparkles
    for i in range(5):
        hp = (t * 0.5 + i * 0.22) % 1.0
        hx = 580 + math.sin(i * 2 + t) * 80
        hy = M.lerp(GROUND - 300, GROUND - 520, hp)
        s = 7 * (1 - hp * 0.4)
        sd.ellipse([hx - s, hy - s, hx + s, hy + s], fill=(255, 240, 170))
    a = M.ease(t / 0.6) * M.ease((dur - t) / 0.6)
    M.caption(d, "Healthy home. Happy family. That's the Boise Mold Removal difference.", a)
    return img.convert("RGB")


def sc_cta(t, dur):
    img = card(t, None)
    d = M.D(img)
    a = M.ease(t / 0.7) * M.ease((dur - t) / 0.6)
    pop = M.eo(t / 0.6)
    sd = ImageDraw.Draw(img)
    shield(sd, W / 2, H * 0.20, 40 * pop)
    M.ctext(d, "MOLD GONE FOR GOOD.", M.font(M.F_BOLD, 56), H * 0.40, (255, 255, 255), a)
    M.ctext(d, "(208) 412-0899", M.font(M.F_TITLE, 110), H * 0.57, GOLD, a * pop)
    M.ctext(d, "boise-moldremoval.com", M.font(M.F_BOLD, 40), H * 0.72, TEAL, a)
    M.ctext(d, "Veteran discount · Free pre-inspection · Available 24/7",
            M.font(M.F_REG, 28), H * 0.84, (210, 240, 230), a)
    return img.convert("RGB")


SCENES = [
    (4.5, sc_title),
    (7.5, sc_hook),
    (7.5, sc_reveal),
    (9.0, sc_mechanism),
    (7.0, sc_happy),
    (6.0, sc_cta),
]
DURATION = sum(s[0] for s in SCENES)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "mold_cartoon.mp4"
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    print("Generating music bed...")
    M.generate_music("music.wav", DURATION + 0.2)

    n_frames = int(DURATION * FPS)
    print(f"Rendering {n_frames} frames ({DURATION:.1f}s @ {FPS}fps)...")
    cmd = [
        ffmpeg, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "music.wav",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart", out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    bounds, acc = [], 0.0
    for dur, fn in SCENES:
        bounds.append((acc, acc + dur, dur, fn))
        acc += dur
    for i in range(n_frames):
        t = i / FPS
        for s, e, dur, fn in bounds:
            if s <= t < e:
                frame = fn(t - s, dur)
                break
        else:
            frame = bounds[-1][3](bounds[-1][2], bounds[-1][2])
        proc.stdin.write(frame.tobytes())
        if i % 48 == 0:
            print(f"  {i:4d}/{n_frames} ({i / n_frames * 100:5.1f}%)")
    proc.stdin.close()
    proc.wait()
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
