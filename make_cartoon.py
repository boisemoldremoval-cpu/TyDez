#!/usr/bin/env python3
"""
Render the TyGuy Biblical-moral cartoon: "The Kindness Choice".

Produces cartoon.mp4 (1280x720, 24fps) with a soft instrumental music bed.
This is the middle segment spliced between the provided intro and outro by
build_film.py.

Moral: Love your neighbor / be kind to one another  (Ephesians 4:32).
"""

import sys
import math
import wave
import struct
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import characters as C

WIDTH, HEIGHT = 1280, 720
FPS = 24
GROUND = 660  # feet baseline

FONT_DIR = "/mnt/skills/examples/canvas-design/canvas-fonts"
F_TITLE = f"{FONT_DIR}/BigShoulders-Bold.ttf"
F_BOLD = f"{FONT_DIR}/Outfit-Bold.ttf"
F_REG = f"{FONT_DIR}/Outfit-Regular.ttf"
F_SERIF = f"{FONT_DIR}/Lora-BoldItalic.ttf"

_fc = {}


def font(p, s):
    k = (p, s)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(p, s)
    return _fc[k]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    return 0.5 * (1 - math.cos(math.pi * clamp(t)))


def eo(t):
    return 1 - (1 - clamp(t)) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


# --------------------------------------------------------------------------- #
# backgrounds
# --------------------------------------------------------------------------- #
def _vgrad(top, bot):
    t = np.array(top, np.float32)
    b = np.array(bot, np.float32)
    r = np.linspace(0, 1, HEIGHT, dtype=np.float32)[:, None]
    g = t[None, :] * (1 - r) + b[None, :] * r
    return np.repeat(g[:, None, :], WIDTH, axis=1).astype(np.uint8)


_HALL = None
_STAR = None


def hallway():
    """A bright school hallway with lockers and a tiled floor."""
    global _HALL
    if _HALL is not None:
        return _HALL.copy()
    img = Image.fromarray(_vgrad((226, 234, 244), (210, 220, 234)), "RGB").convert("RGBA")
    d = ImageDraw.Draw(img)
    floor_y = 540
    d.rectangle([0, floor_y, WIDTH, HEIGHT], fill=(196, 178, 158))
    d.rectangle([0, floor_y, WIDTH, floor_y + 10], fill=(176, 158, 140))
    # perspective floor lines
    for i in range(-6, 14):
        x = i * 130
        d.line([(x, HEIGHT), (WIDTH * 0.5 + (x - WIDTH * 0.5) * 0.18, floor_y)],
               fill=(182, 165, 146), width=2)
    for j in range(1, 5):
        y = floor_y + (HEIGHT - floor_y) * (j / 5) ** 1.4
        d.line([(0, y), (WIDTH, y)], fill=(184, 167, 148), width=2)
    # lockers
    cols = [(70, 130, 190), (60, 150, 150), (70, 130, 190), (60, 150, 150)]
    lw, lh, ly = 150, 300, 150
    x = 40
    k = 0
    while x < WIDTH - 40:
        col = cols[k % len(cols)]
        d.rounded_rectangle([x, ly, x + lw, ly + lh], radius=10, fill=col)
        d.rounded_rectangle([x + 8, ly + 8, x + lw - 8, ly + lh - 8],
                            radius=8, outline=(255, 255, 255, 120), width=3)
        # vents + handle
        for vy in (ly + 24, ly + 40, ly + 56):
            d.line([(x + 30, vy), (x + lw - 30, vy)], fill=(255, 255, 255, 90), width=3)
        d.rectangle([x + lw - 34, ly + lh * 0.5, x + lw - 24, ly + lh * 0.5 + 36],
                    fill=(235, 235, 240))
        x += lw + 18
        k += 1
    _HALL = img
    return _HALL.copy()


def starburst(t, with_crosses=True):
    """Brand-style blue radial burst with golden crosses (title/verse cards)."""
    img = Image.fromarray(_vgrad((20, 70, 150), (8, 30, 80)), "RGB").convert("RGBA")
    d = ImageDraw.Draw(img)
    cx, cy = WIDTH / 2, HEIGHT * 0.46
    n = 28
    for i in range(n):
        a = (i / n) * math.tau + t * 0.12
        col = (130, 180, 240, 60) if i % 2 == 0 else (90, 150, 220, 45)
        x2 = cx + math.cos(a) * 1700
        y2 = cy + math.sin(a) * 1700
        w = 60 if i % 2 == 0 else 34
        d.polygon([(cx, cy),
                   (x2 + math.cos(a + 0.02) * w, y2 + math.sin(a + 0.02) * w),
                   (x2 - math.cos(a + 0.02) * w, y2 - math.sin(a + 0.02) * w)],
                  fill=col)
    # golden crosses scattered
    if with_crosses:
        rng = np.random.default_rng(3)
        for _ in range(16):
            gx = rng.uniform(60, WIDTH - 60)
            gy = rng.uniform(40, HEIGHT - 40)
            s = rng.uniform(10, 22)
            bob = math.sin(t * 1.3 + gx) * 4
            _gold_cross(d, gx, gy + bob, s)
    return img


def _gold_cross(d, x, y, s, col=(255, 205, 70)):
    w = s * 0.32
    d.rounded_rectangle([x - w, y - s, x + w, y + s], radius=w, fill=col)
    d.rounded_rectangle([x - s * 0.8, y - s * 0.25, x + s * 0.8, y + s * 0.25],
                        radius=w, fill=col)


# --------------------------------------------------------------------------- #
# text helpers
# --------------------------------------------------------------------------- #
def wrap(d, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def ctext(d, s, fnt, cy, color, a=1.0, track=0, cx=None):
    if a <= 0:
        return
    cx = WIDTH / 2 if cx is None else cx
    col = (*color, int(clamp(a) * 255))
    if track == 0:
        d.text((cx, cy), s, font=fnt, fill=col, anchor="mm")
        return
    total = sum(d.textlength(ch, font=fnt) + track for ch in s) - track
    x = cx - total / 2
    for ch in s:
        cw = d.textlength(ch, font=fnt)
        d.text((x, cy), ch, font=fnt, fill=col, anchor="lm")
        x += cw + track


def caption(d, text, a=1.0):
    """Lower-third storybook caption banner."""
    if a <= 0:
        return
    fnt = font(F_BOLD, 34)
    lines = wrap(d, text, fnt, WIDTH - 220)
    pad = 22
    lh = 44
    bh = pad * 2 + lh * len(lines)
    by = HEIGHT - bh - 26
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([90, by, WIDTH - 90, by + bh], radius=18,
                         fill=(15, 30, 60, int(190 * a)))
    od.rounded_rectangle([90, by, WIDTH - 90, by + bh], radius=18,
                         outline=(120, 180, 240, int(220 * a)), width=3)
    for i, ln in enumerate(lines):
        od.text((WIDTH / 2, by + pad + lh * i + lh / 2), ln, font=fnt,
                fill=(245, 250, 255, int(255 * a)), anchor="mm")
    d._image.alpha_composite(overlay)


def speech(d, x, y, text, a=1.0):
    """Speech bubble with tail pointing down toward (x, y+tail)."""
    if a <= 0:
        return
    fnt = font(F_BOLD, 30)
    lines = wrap(d, text, fnt, 360)
    lh = 38
    w = max(d.textlength(ln, font=fnt) for ln in lines) + 50
    h = lh * len(lines) + 36
    bx0, by0 = x - w / 2, y - h
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([bx0, by0, bx0 + w, by0 + h], radius=20,
                         fill=(255, 255, 255, int(245 * a)),
                         outline=(60, 110, 190, int(255 * a)), width=3)
    od.polygon([(x - 16, by0 + h - 2), (x + 16, by0 + h - 2), (x, by0 + h + 26)],
               fill=(255, 255, 255, int(245 * a)))
    for i, ln in enumerate(lines):
        od.text((x, by0 + 18 + lh * i + lh / 2), ln, font=fnt,
                fill=(30, 50, 90, int(255 * a)), anchor="mm")
    d._image.alpha_composite(overlay)


# small wrapper so caption()/speech() can composite onto the working image
class D:
    def __init__(self, img):
        self._image = img
        self.d = ImageDraw.Draw(img)

    def __getattr__(self, n):
        return getattr(self.d, n)


def heart(d, x, y, s, a=1.0):
    col = (240, 90, 120, int(255 * a))
    d.ellipse([x - s, y - s, x, y], fill=col)
    d.ellipse([x, y - s, x + s, y], fill=col)
    d.polygon([(x - s, y - s * 0.2), (x + s, y - s * 0.2), (x, y + s * 1.3)], fill=col)


def idle(t, seed=0):
    """Returns (bob_px, blink) for ambient life."""
    bob = math.sin(t * 2.2 + seed) * 5
    ph = (t * 0.5 + seed) % 1.0
    blink = 1 if ph > 0.94 else 0
    return bob, blink


# --------------------------------------------------------------------------- #
# scenes  -- each fn(t, dur) returns an RGB PIL image
# --------------------------------------------------------------------------- #
def sc_title(t, dur):
    img = starburst(t)
    d = D(img)
    a = ease(t / 0.8) * ease((dur - t) / 0.6)
    pop = eo(t / 0.7)
    ctext(d, "TyGuy presents", font(F_REG, 40), HEIGHT * 0.22,
          (200, 220, 255), a, track=6)
    ctext(d, "THE KINDNESS", font(F_TITLE, 130), HEIGHT * 0.45,
          (255, 255, 255), a * pop)
    ctext(d, "CHOICE", font(F_TITLE, 130), HEIGHT * 0.62,
          (255, 210, 80), a * pop)
    ctext(d, "a Biblical moral story", font(F_REG, 30), HEIGHT * 0.80,
          (200, 220, 255), a)
    return img.convert("RGB")


def sc_alone(t, dur):
    img = hallway()
    d = D(img)
    bob, blink = idle(t, 1)
    C.draw_person(img, 720, GROUND + bob * 0.4, 360, C.MIA,
                  {"mouth": "sad", "brow": "sad", "blink": blink,
                   "arm_l": 6, "arm_r": 6, "lean": 4})
    a = ease(t / 0.6) * ease((dur - t) / 0.6)
    caption(d, "It was Mia's first day. She didn't know anyone... and felt all alone.", a)
    return img.convert("RGB")


def sc_passby(t, dur):
    img = hallway()
    d = D(img)
    bob, blink = idle(t, 1)
    C.draw_person(img, 760, GROUND, 360, C.MIA,
                  {"mouth": "sad", "brow": "sad", "blink": blink, "lean": 5})
    # two kids walk across, ignoring her
    p = clamp(t / (dur - 0.5))
    x1 = lerp(-120, WIDTH + 120, p)
    x2 = lerp(-360, WIDTH - 140, p)
    sw = math.sin(t * 6) * 22
    for x, seed in ((x1, 2), (x2, 5)):
        pal = C.KID_A if seed == 2 else C.KID_B
        C.draw_person(img, x, GROUND, 350, pal,
                      {"walk": (t * 1.6 + seed) % 1, "arm_l": 8 + sw / 3,
                       "arm_r": 8 - sw / 3, "mouth": "neutral",
                       "lean": 6})
    a = ease(t / 0.6) * ease((dur - t) / 0.6)
    caption(d, "Some kids hurried right past her, looking away.", a)
    return img.convert("RGB")


def sc_notice(t, dur):
    img = hallway()
    d = D(img)
    bob, blink = idle(t, 1)
    C.draw_person(img, 820, GROUND, 360, C.MIA,
                  {"mouth": "sad", "brow": "sad", "blink": blink, "lean": 5})
    # TyGuy walks in from left, stops at ~x=380, then looks toward Mia
    stop_t = dur * 0.55
    if t < stop_t:
        x = lerp(-140, 380, eo(t / stop_t))
        pose = {"walk": (t * 1.7) % 1, "arm_l": 14, "arm_r": 14, "mouth": "smile"}
    else:
        x = 380
        b2, bl2 = idle(t, 0)
        pose = {"arm_l": 12, "arm_r": 12, "mouth": "open", "brow": "happy",
                "blink": bl2}
        # a thought: notices her  -> draw a small "!" above head later via heart? keep simple
    C.draw_person(img, x, GROUND, 380, C.TYGUY, pose)
    a = ease(t / 0.6) * ease((dur - t) / 0.6)
    caption(d, "But TyGuy noticed. “Nobody should feel left out,” he thought.", a)
    return img.convert("RGB")


def sc_help(t, dur):
    img = hallway()
    d = D(img)
    bob, blink = idle(t, 1)
    miax = 820
    C.draw_person(img, miax, GROUND, 360, C.MIA,
                  {"mouth": "neutral", "brow": "normal", "blink": blink})
    # TyGuy walks from 380 to beside Mia (640), then waves
    move_t = dur * 0.45
    if t < move_t:
        x = lerp(380, 600, eo(t / move_t))
        pose = {"walk": (t * 1.7) % 1, "arm_l": 14, "arm_r": 14, "mouth": "smile"}
    else:
        x = 600
        wave = math.sin((t - move_t) * 7) * 18
        pose = {"arm_r": 95 + wave, "elbow_r": 10, "arm_l": 12,
                "mouth": "open", "brow": "happy"}
    C.draw_person(img, x, GROUND, 380, C.TYGUY, pose)
    a = ease(t / 0.6) * ease((dur - t) / 0.6)
    if t > move_t + 0.3:
        sa = ease((t - move_t - 0.3) / 0.4)
        speech(d, x, GROUND - 400, "Hi! I'm Ty. Want to sit with us?", sa * a)
    caption(d, "He walked over and offered a friendly welcome.", a)
    return img.convert("RGB")


def sc_happy(t, dur):
    img = hallway()
    d = D(img)
    b1, bl1 = idle(t, 1)
    b2, bl2 = idle(t, 3)
    C.draw_person(img, 760, GROUND + b1 * 0.4, 360, C.MIA,
                  {"mouth": "smile", "brow": "happy", "blink": bl1,
                   "arm_l": 40, "elbow_l": 10})
    wave = math.sin(t * 6) * 16
    C.draw_person(img, 520, GROUND + b2 * 0.4, 380, C.TYGUY,
                  {"mouth": "smile", "brow": "happy", "blink": bl2,
                   "arm_r": 70 + wave, "elbow_r": 12})
    # floating hearts
    for i in range(4):
        hp = (t * 0.5 + i * 0.27) % 1.0
        hx = 640 + math.sin(i * 2 + t) * 60
        hy = lerp(GROUND - 320, GROUND - 520, hp)
        heart(d, hx, hy, 16 * (1 - hp * 0.4), a=clamp(1 - hp))
    a = ease(t / 0.6) * ease((dur - t) / 0.6)
    caption(d, "Mia smiled. One small kindness made her whole day brighter!", a)
    return img.convert("RGB")


def sc_verse(t, dur):
    img = starburst(t)
    d = D(img)
    a = ease(t / 0.8) * ease((dur - t) / 0.7)
    _gold_cross(d, WIDTH / 2, HEIGHT * 0.20, 40)
    lines = ["“Be kind to one another,",
             "tender-hearted, forgiving one another.”"]
    for i, ln in enumerate(lines):
        ctext(d, ln, font(F_SERIF, 50), HEIGHT * 0.42 + i * 70,
              (255, 255, 255), a)
    ctext(d, "Ephesians 4:32", font(F_BOLD, 40), HEIGHT * 0.72,
          (255, 210, 80), a)
    return img.convert("RGB")


def sc_moral(t, dur):
    img = starburst(t, with_crosses=True)
    d = D(img)
    a = ease(t / 0.7) * ease((dur - t) / 0.7)
    ctext(d, "Kindness is always a choice.", font(F_BOLD, 60),
          HEIGHT * 0.40, (255, 255, 255), a)
    ctext(d, "Choose kindness today.", font(F_BOLD, 60),
          HEIGHT * 0.54, (255, 210, 80), a)
    ctext(d, "Be kind. Have fun. Be you!", font(F_REG, 38),
          HEIGHT * 0.72, (200, 220, 255), a)
    return img.convert("RGB")


SCENES = [
    (4.5, sc_title),
    (7.5, sc_alone),
    (7.0, sc_passby),
    (7.5, sc_notice),
    (9.0, sc_help),
    (7.0, sc_happy),
    (8.0, sc_verse),
    (5.5, sc_moral),
]
DURATION = sum(s[0] for s in SCENES)


# --------------------------------------------------------------------------- #
# music bed
# --------------------------------------------------------------------------- #
def generate_music(path, duration):
    sr = 44100
    n = int(duration * sr)
    tt = np.linspace(0, duration, n, endpoint=False)
    out = np.zeros(n, np.float32)

    def note(freq, start, length, amp=0.2, wave="sine"):
        i0 = int(start * sr)
        i1 = min(n, int((start + length) * sr))
        if i1 <= i0:
            return
        seg = tt[i0:i1] - start
        env = np.minimum(seg / 0.05, 1.0) * np.clip((length - seg) / 0.4, 0, 1)
        if wave == "sine":
            s = np.sin(2 * math.pi * freq * seg)
        else:
            s = 2 * np.abs(2 * (freq * seg - np.floor(freq * seg + 0.5))) - 1
        out[i0:i1] += (amp * env * s).astype(np.float32)

    def f(semi):  # semitones from A4=440
        return 440 * 2 ** (semi / 12)

    # C major progression: C  G  Am  F  (warm pad + gentle arpeggio)
    chords = [[-9, -5, -2], [-2, 2, 5], [0, 3, 7], [-4, 0, 3]]
    bar = 3.0
    i = 0
    t0 = 0.0
    while t0 < duration:
        ch = chords[i % len(chords)]
        for semi in ch:
            note(f(semi), t0, bar, amp=0.10, wave="sine")
            note(f(semi) / 2, t0, bar, amp=0.05, wave="sine")  # lower octave
        # soft arpeggio bells on top
        for k, semi in enumerate([ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12]):
            note(f(semi), t0 + k * (bar / 4), bar / 4 + 0.2, amp=0.06, wave="sine")
        t0 += bar
        i += 1

    # gentle fade in/out
    fade = int(1.0 * sr)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = np.tanh(out * 1.2) * 0.7
    pcm = (out * 32767).astype(np.int16)
    stereo = np.repeat(pcm[:, None], 2, axis=1).tobytes()
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(stereo)


# --------------------------------------------------------------------------- #
# render + encode
# --------------------------------------------------------------------------- #
def main():
    import imageio_ffmpeg
    out = sys.argv[1] if len(sys.argv) > 1 else "cartoon.mp4"
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    print("Generating music bed...")
    generate_music("music.wav", DURATION + 0.2)

    n_frames = int(DURATION * FPS)
    print(f"Rendering {n_frames} frames ({DURATION:.1f}s @ {FPS}fps)...")
    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-",
        "-i", "music.wav",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart", out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # build per-frame scene lookup
    bounds = []
    acc = 0.0
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
            print(f"  {i:4d}/{n_frames} ({i/n_frames*100:5.1f}%)")
    proc.stdin.close()
    proc.wait()
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
