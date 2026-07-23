#!/usr/bin/env python3
"""Local 2D animated dog-barking clip with synthesized bark audio.

No accounts / GPU needed: PIL renders frames, numpy synthesizes the barks,
ffmpeg muxes them into an MP4. Output: dog_bark.mp4
"""
import math
import os
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 960, 540
FPS = 24
DUR = 4.0                      # seconds
N = int(FPS * DUR)
OUT = Path(__file__).parent
FRAMES = OUT / "_frames"
FRAMES.mkdir(exist_ok=True)

# Bark timing (seconds). Each bark = mouth open + sound burst.
BARKS = [0.5, 1.4, 2.3, 3.2]
BARK_LEN = 0.22                # how long the mouth stays open per bark


def bark_env(t):
    """0..1 how 'open' the bark is at time t (fast attack, quick decay)."""
    best = 0.0
    for b in BARKS:
        dt = t - b
        if 0 <= dt <= BARK_LEN:
            # rise then fall
            x = dt / BARK_LEN
            best = max(best, math.sin(math.pi * x))
    return best


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_background(d):
    # sky gradient
    top = (135, 206, 250)
    bot = (224, 246, 255)
    for y in range(int(H * 0.72)):
        t = y / (H * 0.72)
        d.line([(0, y), (W, y)], fill=lerp(top, bot, t))
    # grass
    d.rectangle([0, int(H * 0.72), W, H], fill=(126, 200, 96))
    d.rectangle([0, int(H * 0.72), W, int(H * 0.72) + 6], fill=(105, 178, 78))
    # sun
    d.ellipse([W - 150, 40, W - 60, 130], fill=(255, 236, 130))
    d.ellipse([W - 158, 32, W - 52, 138], outline=(255, 236, 130), width=3)
    # a couple of clouds
    for cx, cy in [(160, 90), (420, 60)]:
        for dx, dy, r in [(-30, 0, 26), (0, -8, 32), (30, 0, 26), (0, 8, 24)]:
            d.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r],
                      fill=(255, 255, 255))


def draw_dog(d, frame_t):
    """Draw a cartoon dog. Mouth opens with the bark envelope; ears/tail bounce."""
    open_amt = bark_env(frame_t)                 # 0..1
    bounce = math.sin(frame_t * 2 * math.pi * 2) # idle bob
    cx, cy = W // 2 - 40, int(H * 0.60) + int(bounce * 3)

    body = (196, 148, 96)     # tan
    body_dk = (168, 122, 74)
    belly = (232, 205, 168)

    # tail (wags faster while barking)
    wag = math.sin(frame_t * 2 * math.pi * (5 if open_amt > 0.1 else 2)) * 22
    d.line([(cx - 120, cy - 10), (cx - 175, cy - 40 + wag)],
           fill=body_dk, width=18)

    # back legs
    d.rounded_rectangle([cx - 70, cy + 40, cx - 44, cy + 110], 10, fill=body_dk)
    d.rounded_rectangle([cx + 40, cy + 40, cx + 66, cy + 110], 10, fill=body_dk)
    # body
    d.ellipse([cx - 120, cy - 40, cx + 90, cy + 90], fill=body)
    d.ellipse([cx - 70, cy + 0, cx + 80, cy + 95], fill=belly)
    # front legs
    d.rounded_rectangle([cx - 40, cy + 50, cx - 14, cy + 120], 10, fill=body)
    d.rounded_rectangle([cx + 20, cy + 50, cx + 46, cy + 120], 10, fill=body)
    d.ellipse([cx - 44, cy + 112, cx - 10, cy + 128], fill=body_dk)
    d.ellipse([cx + 16, cy + 112, cx + 50, cy + 128], fill=body_dk)

    # head
    hx, hy = cx + 95, cy - 30
    # ears (flap up with bark)
    ear_lift = open_amt * 16
    d.ellipse([hx - 44, hy - 46 - ear_lift, hx - 8, hy + 18 - ear_lift],
              fill=body_dk)
    d.ellipse([hx + 30, hy - 46 - ear_lift, hx + 66, hy + 18 - ear_lift],
              fill=body_dk)
    # face
    d.ellipse([hx - 42, hy - 40, hx + 58, hy + 60], fill=body)
    # snout
    d.ellipse([hx + 20, hy + 6, hx + 78, hy + 52], fill=belly)
    # eyes
    eye_y = hy - 2
    d.ellipse([hx - 8, eye_y, hx + 6, eye_y + 16], fill=(30, 24, 20))
    d.ellipse([hx + 22, eye_y, hx + 36, eye_y + 16], fill=(30, 24, 20))
    d.ellipse([hx - 4, eye_y + 2, hx + 1, eye_y + 7], fill=(255, 255, 255))
    d.ellipse([hx + 26, eye_y + 2, hx + 31, eye_y + 7], fill=(255, 255, 255))
    # nose
    d.ellipse([hx + 60, hy + 14, hx + 80, hy + 32], fill=(40, 30, 26))

    # mouth: opens downward with bark
    mouth_open = int(open_amt * 30)
    mx, my = hx + 48, hy + 40
    if mouth_open > 3:
        d.pieslice([mx - 26, my - 10, mx + 30, my + 10 + mouth_open],
                   0, 180, fill=(120, 40, 40))
        d.ellipse([mx - 8, my + mouth_open - 6, mx + 14, my + mouth_open + 8],
                  fill=(220, 90, 90))  # tongue
    else:
        d.arc([mx - 20, my - 8, mx + 24, my + 12], 20, 160,
              fill=(60, 40, 30), width=4)

    return open_amt, hx, hy


def draw_woof(d, open_amt, hx, hy):
    if open_amt < 0.35:
        return
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except Exception:
        font = ImageFont.load_default()
    txt = "WOOF!"
    bx, by = hx + 95, hy - 90
    # speech bubble
    d.rounded_rectangle([bx - 10, by - 12, bx + 150, by + 52], 16,
                        fill=(255, 255, 255), outline=(40, 40, 40), width=3)
    d.polygon([(bx + 6, by + 44), (bx - 18, by + 74), (bx + 34, by + 50)],
              fill=(255, 255, 255), outline=(40, 40, 40))
    d.text((bx + 8, by), txt, fill=(220, 60, 40), font=font)


def render_frames():
    for i in range(N):
        t = i / FPS
        img = Image.new("RGB", (W, H), (135, 206, 250))
        d = ImageDraw.Draw(img)
        draw_background(d)
        open_amt, hx, hy = draw_dog(d, t)
        draw_woof(d, open_amt, hx, hy)
        img.save(FRAMES / f"f{i:04d}.png")
    print(f"Rendered {N} frames")


def synth_bark_audio(path, sr=44100):
    total = np.zeros(int(sr * DUR), dtype=np.float32)
    rng = np.random.default_rng(7)
    for b in BARKS:
        dur = 0.20
        n = int(sr * dur)
        tt = np.linspace(0, dur, n, endpoint=False)
        # pitch sweep down (typical bark "wu-of")
        f0 = np.linspace(520, 300, n)
        phase = 2 * np.pi * np.cumsum(f0) / sr
        tone = (np.sin(phase)
                + 0.5 * np.sin(2 * phase)
                + 0.25 * np.sin(3 * phase))
        noise = rng.standard_normal(n) * 0.4          # breathy edge
        # fast attack, quick decay envelope
        env = np.minimum(tt / 0.015, 1.0) * np.exp(-tt * 14)
        burst = (tone * 0.7 + noise) * env
        start = int(b * sr)
        end = min(start + n, total.size)
        total[start:end] += burst[: end - start]
    # normalize
    peak = np.max(np.abs(total)) or 1.0
    total = (total / peak * 0.9 * 32767).astype(np.int16)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(total.tobytes())
    print(f"Wrote audio: {path}")


def mux(out_mp4, wav):
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES / "f%04d.png"),
        "-i", str(wav),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest", str(out_mp4),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"Wrote {out_mp4}")


if __name__ == "__main__":
    render_frames()
    wav = OUT / "_bark.wav"
    synth_bark_audio(wav)
    mux(OUT / "dog_bark.mp4", wav)
