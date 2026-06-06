#!/usr/bin/env python3
"""
Generate a branded promo MP4 for Boise Mold Removal / TyDez.

Renders animated 1080p frames with Pillow and encodes them to H.264 via the
ffmpeg binary bundled with imageio-ffmpeg (no system ffmpeg required).

Usage:
    python3 make_promo.py            # renders promo.mp4
    python3 make_promo.py out.mp4    # custom output path

Edit the CONFIG block below to re-skin the video (brand, colors, copy,
contact details) and re-render anytime.
"""

import sys
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

# --------------------------------------------------------------------------- #
# CONFIG -- edit these to re-skin the promo
# --------------------------------------------------------------------------- #
CONFIG = {
    "brand": "TyDez",
    "subtitle": "BOISE MOLD REMOVAL",
    "services": [
        "Mold Inspection & Testing",
        "Safe, Certified Removal",
        "Air Quality Restoration",
        "Moisture & Prevention",
    ],
    "badges": ["LICENSED", "FAST", "GUARANTEED"],
    "cta": "Free Inspection · No Obligation",
    "contact_email": "boisemoldremoval@gmail.com",
    "region": "Serving Boise & the Treasure Valley",
}

WIDTH, HEIGHT = 1920, 1080
FPS = 30

FONT_DIR = "/mnt/skills/examples/canvas-design/canvas-fonts"
F_DISPLAY = f"{FONT_DIR}/BigShoulders-Bold.ttf"   # punchy brand wordmark
F_BOLD = f"{FONT_DIR}/Outfit-Bold.ttf"            # headlines
F_REG = f"{FONT_DIR}/Outfit-Regular.ttf"          # body

# Palette -- clean, fresh, "healthy air" teals + a lime accent
C_TOP = (8, 58, 60)       # deep teal
C_BOTTOM = (4, 26, 40)    # near-navy
C_WHITE = (240, 250, 249)
C_MUTE = (150, 196, 196)
C_ACCENT = (86, 214, 165)  # fresh mint/lime
C_ACCENT2 = (120, 224, 232)

# --------------------------------------------------------------------------- #
# Font cache
# --------------------------------------------------------------------------- #
_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


# --------------------------------------------------------------------------- #
# Math helpers
# --------------------------------------------------------------------------- #
def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def ease_out(t):
    """Cubic ease-out."""
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    return 0.5 * (1 - math.cos(math.pi * clamp(t)))


def lerp(a, b, t):
    return a + (b - a) * t


def fade_window(t, start, dur, fade=0.5, hold=None):
    """Opacity 0->1->0 for an element appearing at `start` for `dur` seconds."""
    local = t - start
    if local < 0 or local > dur:
        return 0.0
    if hold is None:
        hold = dur - 2 * fade
    if local < fade:
        return ease_in_out(local / fade)
    if local < fade + hold:
        return 1.0
    return ease_in_out(clamp((dur - local) / fade))


# --------------------------------------------------------------------------- #
# Background: vertical gradient + drifting "fresh air" bubbles
# --------------------------------------------------------------------------- #
def make_gradient():
    top = np.array(C_TOP, dtype=np.float32)
    bot = np.array(C_BOTTOM, dtype=np.float32)
    ramp = np.linspace(0, 1, HEIGHT, dtype=np.float32)[:, None]
    grad = (top[None, :] * (1 - ramp) + bot[None, :] * ramp)
    grad = np.repeat(grad[:, None, :], WIDTH, axis=1)
    # soft radial glow behind center
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    cx, cy = WIDTH * 0.5, HEIGHT * 0.42
    dist = np.sqrt(((xx - cx) / WIDTH) ** 2 + ((yy - cy) / HEIGHT) ** 2)
    glow = np.clip(1 - dist * 1.6, 0, 1)[:, :, None] ** 2
    grad = grad + glow * np.array([18, 40, 38], dtype=np.float32)
    return np.clip(grad, 0, 255).astype(np.uint8)


_GRAD = make_gradient()

# Pre-seed bubbles
rng = np.random.default_rng(7)
_BUBBLES = []
for _ in range(46):
    _BUBBLES.append({
        "x": rng.uniform(0, WIDTH),
        "y": rng.uniform(0, HEIGHT),
        "r": rng.uniform(4, 26),
        "speed": rng.uniform(8, 34),
        "sway": rng.uniform(6, 28),
        "phase": rng.uniform(0, math.tau),
        "alpha": rng.uniform(10, 40),
    })


def background(t):
    img = Image.fromarray(_GRAD.copy(), "RGB").convert("RGBA")
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for b in _BUBBLES:
        y = (b["y"] - b["speed"] * t) % (HEIGHT + 80) - 40
        x = b["x"] + math.sin(t * 0.6 + b["phase"]) * b["sway"]
        r = b["r"]
        a = int(b["alpha"])
        d.ellipse([x - r, y - r, x + r, y + r],
                  outline=(*C_ACCENT2, a + 20), width=2)
        d.ellipse([x - r * 0.5, y - r * 0.5, x + r * 0.5, y + r * 0.5],
                  fill=(*C_ACCENT2, a // 3))
    return Image.alpha_composite(img, layer)


# --------------------------------------------------------------------------- #
# Drawing helpers
# --------------------------------------------------------------------------- #
def with_alpha(color, a):
    return (color[0], color[1], color[2], int(clamp(a) * 255))


def text_size(draw, s, fnt, tracking=0):
    if not s:
        return 0, 0
    if tracking == 0:
        box = draw.textbbox((0, 0), s, font=fnt)
        return box[2] - box[0], box[3] - box[1]
    w = 0
    h = 0
    for ch in s:
        box = draw.textbbox((0, 0), ch, font=fnt)
        w += (box[2] - box[0]) + tracking
        h = max(h, box[3] - box[1])
    return w - tracking, h


def draw_centered(draw, s, fnt, cy, color, alpha, tracking=0, cx=None):
    if alpha <= 0:
        return
    cx = WIDTH / 2 if cx is None else cx
    w, _ = text_size(draw, s, fnt, tracking)
    x = cx - w / 2
    col = with_alpha(color, alpha)
    if tracking == 0:
        draw.text((x, cy), s, font=fnt, fill=col, anchor="lm")
        return
    for ch in s:
        box = draw.textbbox((0, 0), ch, font=fnt)
        cw = box[2] - box[0]
        draw.text((x, cy), ch, font=fnt, fill=col, anchor="lm")
        x += cw + tracking


def draw_shield(draw, cx, cy, scale, alpha):
    """A simple shield + droplet mark drawn from primitives."""
    if alpha <= 0:
        return
    s = scale
    pts = [
        (cx, cy - 1.15 * s),
        (cx + 0.95 * s, cy - 0.75 * s),
        (cx + 0.95 * s, cy + 0.25 * s),
        (cx, cy + 1.2 * s),
        (cx - 0.95 * s, cy + 0.25 * s),
        (cx - 0.95 * s, cy - 0.75 * s),
    ]
    draw.polygon(pts, outline=with_alpha(C_ACCENT, alpha), width=max(2, int(s * 0.07)))
    # inner droplet
    dx, dy = cx, cy - 0.15 * s
    r = 0.42 * s
    draw.ellipse([dx - r, dy - r * 0.7, dx + r, dy + r * 1.1],
                 fill=with_alpha(C_ACCENT2, alpha * 0.9))
    draw.polygon([(dx, dy - 0.95 * s), (dx - r * 0.7, dy - r * 0.2),
                  (dx + r * 0.7, dy - r * 0.2)],
                 fill=with_alpha(C_ACCENT2, alpha * 0.9))
    # check tick
    draw.line([(cx - 0.32 * s, cy + 0.05 * s),
               (cx - 0.05 * s, cy + 0.32 * s),
               (cx + 0.4 * s, cy - 0.2 * s)],
              fill=with_alpha(C_TOP, alpha), width=max(3, int(s * 0.11)))


# --------------------------------------------------------------------------- #
# Scenes
# --------------------------------------------------------------------------- #
# Timeline (seconds)
T_INTRO = 4.2
T_HOOK = 3.6
T_PROMISE = 3.6
T_SERVICES = 6.4
T_BADGES = 3.2
T_CTA = 4.6
DURATION = T_INTRO + T_HOOK + T_PROMISE + T_SERVICES + T_BADGES + T_CTA

S_INTRO = 0.0
S_HOOK = S_INTRO + T_INTRO
S_PROMISE = S_HOOK + T_HOOK
S_SERVICES = S_PROMISE + T_PROMISE
S_BADGES = S_SERVICES + T_SERVICES
S_CTA = S_BADGES + T_BADGES


def render_frame(t):
    img = background(t)
    d = ImageDraw.Draw(img)

    # ---- Scene 1: brand intro ----
    if S_INTRO <= t < S_HOOK:
        a = fade_window(t, S_INTRO, T_INTRO, fade=0.7)
        local = t - S_INTRO
        rise = ease_out(clamp(local / 0.9))
        cy = HEIGHT * 0.34 + (1 - rise) * 40
        draw_shield(d, WIDTH / 2, cy - 40, 90 * (0.6 + 0.4 * rise), a)
        draw_centered(d, CONFIG["brand"], font(F_DISPLAY, 200),
                      HEIGHT * 0.55, C_WHITE, a)
        draw_centered(d, CONFIG["subtitle"], font(F_REG, 50),
                      HEIGHT * 0.67, C_ACCENT, a, tracking=14)

    # ---- Scene 2: hook ----
    elif S_HOOK <= t < S_PROMISE:
        a = fade_window(t, S_HOOK, T_HOOK, fade=0.6)
        local = t - S_HOOK
        rise = ease_out(clamp(local / 0.8))
        off = (1 - rise) * 50
        draw_centered(d, "Worried about", font(F_REG, 66),
                      HEIGHT * 0.40 + off, C_MUTE, a)
        draw_centered(d, "MOLD in your home?", font(F_BOLD, 132),
                      HEIGHT * 0.55 + off, C_WHITE, a)

    # ---- Scene 3: promise ----
    elif S_PROMISE <= t < S_SERVICES:
        a = fade_window(t, S_PROMISE, T_PROMISE, fade=0.6)
        local = t - S_PROMISE
        rise = ease_out(clamp(local / 0.8))
        off = (1 - rise) * 50
        draw_centered(d, "We remove it.", font(F_BOLD, 150),
                      HEIGHT * 0.46 + off, C_WHITE, a)
        draw_centered(d, "For good.", font(F_BOLD, 150),
                      HEIGHT * 0.63 + off, C_ACCENT, a)

    # ---- Scene 4: services ----
    elif S_SERVICES <= t < S_BADGES:
        a_scene = fade_window(t, S_SERVICES, T_SERVICES, fade=0.55)
        local = t - S_SERVICES
        draw_centered(d, "What we do", font(F_REG, 50),
                      HEIGHT * 0.20, C_ACCENT, a_scene, tracking=12)
        items = CONFIG["services"]
        base_y = HEIGHT * 0.36
        gap = HEIGHT * 0.13
        for i, item in enumerate(items):
            appear = 0.5 + i * 0.55
            ia = fade_window(t, S_SERVICES + appear,
                             T_SERVICES - appear, fade=0.4)
            ia = min(ia, a_scene)
            rise = ease_out(clamp((local - appear) / 0.6))
            x_off = (1 - rise) * 60
            y = base_y + i * gap
            # bullet dot
            if ia > 0:
                bx = WIDTH * 0.30 - x_off
                d.ellipse([bx - 11, y - 11, bx + 11, y + 11],
                          fill=with_alpha(C_ACCENT, ia))
                d.text((WIDTH * 0.34 - x_off, y), item,
                       font=font(F_BOLD, 64),
                       fill=with_alpha(C_WHITE, ia), anchor="lm")

    # ---- Scene 5: badges / why us ----
    elif S_BADGES <= t < S_CTA:
        a = fade_window(t, S_BADGES, T_BADGES, fade=0.5)
        local = t - S_BADGES
        draw_centered(d, "Why homeowners choose us", font(F_REG, 48),
                      HEIGHT * 0.34, C_MUTE, a)
        badges = CONFIG["badges"]
        # layout pills in a row
        pill_font = font(F_BOLD, 60)
        gaps = 60
        widths = [text_size(d, b, pill_font)[0] + 90 for b in badges]
        total = sum(widths) + gaps * (len(badges) - 1)
        x = WIDTH / 2 - total / 2
        y = HEIGHT * 0.52
        for i, b in enumerate(badges):
            appear = i * 0.35
            ba = min(a, fade_window(t, S_BADGES + appear,
                                    T_BADGES - appear, fade=0.35))
            pop = ease_out(clamp((local - appear) / 0.4))
            w = widths[i]
            h = 110
            if ba > 0:
                d.rounded_rectangle([x, y - h / 2, x + w, y + h / 2],
                                    radius=h / 2,
                                    outline=with_alpha(C_ACCENT, ba),
                                    width=3)
                d.text((x + w / 2, y), b, font=pill_font,
                       fill=with_alpha(C_WHITE, ba * pop), anchor="mm")
            x += w + gaps

    # ---- Scene 6: CTA ----
    else:
        a = fade_window(t, S_CTA, T_CTA, fade=0.6, hold=T_CTA)
        local = t - S_CTA
        rise = ease_out(clamp(local / 0.8))
        off = (1 - rise) * 40
        draw_shield(d, WIDTH / 2, HEIGHT * 0.24 + off, 70, a)
        draw_centered(d, "Breathe easy again.", font(F_BOLD, 110),
                      HEIGHT * 0.45 + off, C_WHITE, a)
        draw_centered(d, CONFIG["cta"], font(F_REG, 56),
                      HEIGHT * 0.57, C_ACCENT, a)
        draw_centered(d, CONFIG["contact_email"], font(F_BOLD, 64),
                      HEIGHT * 0.70, C_ACCENT2, a)
        draw_centered(d, CONFIG["region"], font(F_REG, 42),
                      HEIGHT * 0.80, C_MUTE, a)

    return img.convert("RGB")


# --------------------------------------------------------------------------- #
# Encode
# --------------------------------------------------------------------------- #
def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "promo.mp4"
    n_frames = int(DURATION * FPS)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS),
        "-i", "-",
        "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "18",
        "-movflags", "+faststart",
        out,
    ]
    print(f"Rendering {n_frames} frames "
          f"({DURATION:.1f}s @ {FPS}fps, {WIDTH}x{HEIGHT}) -> {out}")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    for i in range(n_frames):
        frame = render_frame(i / FPS)
        proc.stdin.write(frame.tobytes())
        if i % 30 == 0:
            print(f"  {i:4d}/{n_frames}  ({i / n_frames * 100:5.1f}%)")
    proc.stdin.close()
    proc.wait()
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
