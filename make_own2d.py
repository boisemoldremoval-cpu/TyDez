#!/usr/bin/env python3
"""
"A Helping Hand" -- an original, cinematic 2D Biblical-moral short.

Original characters (Sam & Mia), drawn cel-shaded with bold outlines, staged in
a hand-drawn park with real production polish: depth-of-field background blur,
warm key light + vignette, drifting bokeh, drop shadows, a gentle camera
push-in, two TTS voices and a music bed. Moral: the Golden Rule (Luke 6:31).

    python3 make_own2d.py        # -> own2d.mp4   (no intro/outro)
"""

import math
import wave
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import imageio_ffmpeg

import make_cartoon as M
import bg2
import kid
import voices

W, H, FPS = 1280, 720, 24
OUT = "own2d.mp4"
GROUND = int(H * 0.93)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def eo(t):
    return 1 - (1 - clamp(t)) ** 3


def ease(t):
    return 0.5 * (1 - math.cos(math.pi * clamp(t)))


def lerp(a, b, t):
    return a + (b - a) * t


def blink(t, s=0.0):
    return 1 if (t * 0.5 + s) % 1.0 > 0.93 else 0


def bob(t, s=0.0, a=6.0):
    return math.sin(t * 2.0 + s) * a


def fade(t, dur, f=0.5):
    return clamp(min(t / f, (dur - t) / f))


# --------------------------------------------------------------------------- #
# cinematic overlays (precomputed)
# --------------------------------------------------------------------------- #
def _vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H * 0.46
    d = np.sqrt(((xx - cx) / (W * 0.62)) ** 2 + ((yy - cy) / (H * 0.62)) ** 2)
    v = np.clip(1.0 - (d - 0.55) * 0.85, 0.35, 1.0)   # darken corners
    arr = (np.dstack([v, v, v]) * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def _keylight():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sx, sy = W * 0.18, H * 0.14
    d = np.sqrt(((xx - sx) / W) ** 2 + ((yy - sy) / H) ** 2)
    g = np.clip(1.0 - d * 1.7, 0, 1) ** 2
    warm = np.dstack([g * 90, g * 74, g * 40]).astype(np.uint8)  # warm add
    return Image.fromarray(warm, "RGB")


_VIG = _vignette()
_LIGHT = _keylight()
_rng = np.random.default_rng(11)
_BOKEH = [{"x": _rng.uniform(0, W), "y": _rng.uniform(0, H),
           "r": _rng.uniform(10, 40), "spd": _rng.uniform(8, 22),
           "ph": _rng.uniform(0, 7), "a": _rng.uniform(18, 46)} for _ in range(16)]


def add_bokeh(img, t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for b in _BOKEH:
        y = (b["y"] - b["spd"] * t) % (H + 80) - 40
        x = b["x"] + math.sin(t * 0.5 + b["ph"]) * 24
        r = b["r"]
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 248, 225, int(b["a"])))
    layer = layer.filter(ImageFilter.GaussianBlur(7))
    img.alpha_composite(layer)


def cinematic(img, t, zoom=1.04, dx=0.0, dy=0.0):
    """Apply key light, vignette, and a subtle camera move; returns RGB image."""
    rgb = img.convert("RGB")
    rgb = ImageChops.screen(rgb, _LIGHT)
    rgb = ImageChops.multiply(rgb, _VIG)
    # camera: crop a window of size (W/zoom,H/zoom) and scale back up
    cw, ch = W / zoom, H / zoom
    cx = W / 2 + dx
    cy = H / 2 + dy
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    rgb = rgb.crop(tuple(map(int, box))).resize((W, H), Image.LANCZOS)
    return rgb


def stage(t):
    """Blurred park background (depth of field)."""
    bgimg = bg2.schoolyard(t)
    return bgimg.filter(ImageFilter.GaussianBlur(6))


def books(d, x, y, lift=0.0, alpha=1.0):
    cols = [(210, 80, 80), (80, 150, 210), (240, 190, 70)]
    for i, c in enumerate(cols):
        bx = x + (i - 1) * 34
        by = y - lift * (40 + i * 8)
        a = int(255 * alpha)
        d.rounded_rectangle([bx - 22, by - 14, bx + 22, by + 14], radius=4,
                            fill=(*c, a), outline=(30, 24, 28, a), width=3)
        d.line([(bx, by - 12), (bx, by + 12)], fill=(255, 255, 255, a), width=2)


# --------------------------------------------------------------------------- #
# scenes:  (dur, chars_fn, text_fn, camera_fn)
# --------------------------------------------------------------------------- #
SCENES = []


def scene(dur):
    def deco(fn):
        SCENES.append([dur, fn, None, None])
        return SceneRef(len(SCENES) - 1)
    return deco


class SceneRef:
    def __init__(self, i):
        self.i = i

    def text(self, fn):
        SCENES[self.i][2] = fn
        return self

    def cam(self, fn):
        SCENES[self.i][3] = fn
        return self


@scene(4.5)
def s_walk(img, t, dur):
    d = ImageDraw.Draw(img, "RGBA")
    x = lerp(W * 0.12, W * 0.42, eo(clamp(t / (dur - 0.5))))
    kid.draw_kid(img, x, GROUND, 300, kid.SAM,
                 {"walk": (t * 1.5) % 1, "arm_l": 22, "arm_r": -6,
                  "mouth": "smile", "brow": "happy", "blink": blink(t)})


s_walk.text(lambda d, t, dur: M.caption(d, "Sam was having a wonderful day at the park.",
                                        fade(t, dur)))


@scene(4.5)
def s_see(img, t, dur):
    d = ImageDraw.Draw(img, "RGBA")
    books(d, W * 0.66, GROUND - 6)
    kid.draw_kid(img, W * 0.70, GROUND, 290, kid.MIA,
                 {"mouth": "sad", "brow": "sad", "blink": blink(t, 1), "lean": 4})
    kid.draw_kid(img, W * 0.40 - bob(t) * 0.2, GROUND, 300, kid.SAM,
                 {"mouth": "neutral", "brow": "normal", "look": 1, "blink": blink(t)})


s_see.text(lambda d, t, dur: M.caption(d, "Then he saw someone who'd dropped all her things.",
                                       fade(t, dur)))


@scene(4.0)
def s_ignore(img, t, dur):
    d = ImageDraw.Draw(img, "RGBA")
    books(d, W * 0.66, GROUND - 6)
    kid.draw_kid(img, W * 0.70, GROUND, 290, kid.MIA,
                 {"mouth": "sad", "brow": "sad", "blink": blink(t, 1), "look": -1})
    p = clamp(t / (dur - 0.3))
    for pal, x0, x1, sd in ((kid.KID1, -W * 0.1, W * 0.5, 2), (kid.KID2, -W * 0.25, W * 0.34, 5)):
        x = lerp(x0, x1, eo(p))
        sw = math.sin(t * 8 + sd) * 22
        kid.draw_kid(img, x, GROUND, 300, pal,
                     {"walk": (t * 2.0 + sd) % 1, "arm_l": 20 + sw / 2,
                      "arm_r": 20 - sw / 2, "mouth": "smile", "lean": 8})


s_ignore.text(lambda d, t, dur: M.caption(d, "But the other kids just ran right past...",
                                          fade(t, dur)))


@scene(5.0)
def s_help(img, t, dur):
    d = ImageDraw.Draw(img, "RGBA")
    lift = eo(clamp((t - 1.5) / 2.0))               # books get picked up
    books(d, W * 0.66, GROUND - 6, lift=lift, alpha=clamp(1 - lift * 0.6))
    kid.draw_kid(img, W * 0.70, GROUND, 290, kid.MIA,
                 {"mouth": "neutral", "brow": "normal", "blink": blink(t, 1), "look": -1})
    # Sam steps over and reaches out
    x = lerp(W * 0.40, W * 0.55, eo(clamp(t / 1.2)))
    kid.draw_kid(img, x, GROUND, 300, kid.SAM,
                 {"walk": (t * 1.6) % 1 if t < 1.2 else 0, "arm_r": 60,
                  "elbow": 16, "mouth": "smile", "brow": "happy", "blink": blink(t)})


s_help.text(lambda d, t, dur: M.speech(d, W * 0.55, H * 0.20, "Here, let me help you!",
                                       clamp((t - 0.4) / 0.3) * fade(t, dur, 0.4)))


@scene(4.5)
def s_thanks(img, t, dur):
    d = ImageDraw.Draw(img, "RGBA")
    hop = abs(math.sin(t * 3)) * 12 if t > 0.3 else 0
    kid.draw_kid(img, W * 0.62 - hop * 0, GROUND - hop, 300, kid.MIA,
                 {"mouth": "bigsmile", "brow": "happy", "blush": True,
                  "arm_l": 34, "elbow": 12, "blink": blink(t, 1)})
    kid.draw_kid(img, W * 0.38, GROUND - bob(t, 0, 5), 300, kid.SAM,
                 {"mouth": "smile", "brow": "happy", "arm_r": 30, "blink": blink(t)})
    for i in range(5):
        hp = (t * 0.6 + i * 0.2) % 1.0
        hx = W * 0.5 + math.sin(i * 2 + t) * 70
        hy = lerp(H * 0.6, H * 0.2, hp)
        M.heart(d, hx, hy, 15 * (1 - hp * 0.4), a=clamp(1 - hp))


s_thanks.text(lambda d, t, dur: M.speech(d, W * 0.64, H * 0.18, "Oh, thank you so much!",
                                         clamp((t - 0.4) / 0.3) * fade(t, dur, 0.4)))


@scene(4.5)
def s_together(img, t, dur):
    d = ImageDraw.Draw(img, "RGBA")
    x = lerp(W * 0.30, W * 0.52, eo(clamp(t / dur)))
    kid.draw_kid(img, x - 70, GROUND, 300, kid.SAM,
                 {"walk": (t * 1.4) % 1, "arm_l": 18, "arm_r": -4,
                  "mouth": "smile", "brow": "happy", "blink": blink(t)})
    kid.draw_kid(img, x + 90, GROUND, 290, kid.MIA,
                 {"walk": (t * 1.4 + 0.5) % 1, "arm_l": 16, "arm_r": -2,
                  "mouth": "bigsmile", "brow": "happy", "blink": blink(t, 1)})


s_together.text(lambda d, t, dur: M.caption(d, "A little kindness made her whole day.",
                                            fade(t, dur)))


@scene(5.5)
def s_verse(img, t, dur):
    # replace the staged bg entirely with the branded starburst
    img.paste(M.starburst(t).convert("RGBA"), (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    M._gold_cross(d, W * 0.5, H * 0.22, 42)
    M.ctext(d, "“Do to others as you would have", M.font(M.F_SERIF, 46),
            H * 0.42, (255, 255, 255), clamp((t - 0.2) / 0.5))
    M.ctext(d, "them do to you.”", M.font(M.F_SERIF, 46),
            H * 0.52, (255, 255, 255), clamp((t - 0.7) / 0.5))
    M.ctext(d, "Luke 6:31", M.font(M.F_BOLD, 38),
            H * 0.66, (255, 210, 80), clamp((t - 1.2) / 0.5))


s_verse.cam(lambda t, dur: (1.0, 0, 0))   # no DoF/camera move on the card


# --------------------------------------------------------------------------- #
NARRATION = [
    ("ty", "Sam was having a wonderful day at the park.", 0.4, 1.0),
    ("ty", "Then he saw someone who had dropped all her things.", 0.4, 1.0),
    ("ty", "But the other kids just ran right past.", 0.4, 1.0),
    ("ty", "Here, let me help you!", 0.6, 1.18),          # Sam (kid pitch)
    ("mia", "Oh, thank you so much!", 0.5, 1.12),         # Mia
    ("ty", "A little kindness made her whole day.", 0.4, 1.0),
    ("ty", "Do to others as you would have them do to you. Luke six, thirty one.", 0.5, 1.0),
]
DURATION = sum(s[0] for s in SCENES)


def build_voice(path):
    total = int((DURATION + 1.0) * voices.SR)
    buf = np.zeros(total, np.float32)
    acc = 0.0
    for (dur, *_), (vc, text, delay, pitch) in zip(SCENES, NARRATION):
        clip = voices.synth(vc, text, pitch)
        s = int((acc + delay) * voices.SR)
        e = min(total, s + len(clip))
        buf[s:e] += clip[:e - s]
        acc += dur
    pcm = (np.clip(buf, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(voices.SR)
        wf.writeframes(pcm.tobytes())


def frame_at(t):
    acc = 0.0
    for dur, chars_fn, text_fn, cam_fn in SCENES:
        if acc <= t < acc + dur:
            lt = t - acc
            base = stage(t)
            chars_fn(base, lt, dur)
            add_bokeh(base, t)
            if cam_fn:
                zoom, dx, dy = cam_fn(lt, dur)
            else:
                zoom, dx, dy = lerp(1.05, 1.0, eo(lt / dur)), lerp(-12, 12, lt / dur), 0
            out = cinematic(base, t, zoom, dx, dy)
            if text_fn:
                wrap = M.D(out.convert("RGBA"))
                text_fn(wrap, lt, dur)
                return wrap._image.convert("RGB")
            return out
        acc += dur
    return frame_at(DURATION - 1e-3)


def main():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(DURATION * FPS)
    print(f"own2d: {DURATION:.1f}s, {n} frames")
    M.generate_music("musicO.wav", DURATION + 0.3)
    print("Synthesizing voices...")
    build_voice("voiceO.wav")
    amix = ("[1:a]volume=0.26,aresample=48000,aformat=channel_layouts=stereo[m];"
            "[2:a]volume=1.8,aresample=48000,aformat=channel_layouts=stereo[v];"
            "[m][v]amix=inputs=2:duration=first:normalize=0[a]")
    cmd = [
        ffmpeg, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", "musicO.wav", "-i", "voiceO.wav",
        "-filter_complex", amix, "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart", OUT,
    ]
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
