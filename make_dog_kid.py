#!/usr/bin/env python3
"""
Render a wholesome animated clip: a dog loving a kid.

A golden pup bounds across a sunny park, leaps into a kid's arms and licks
their face while their tail wags and little hearts float up. Pure programmatic
2D animation (Pillow + numpy), encoded to H.264 via the ffmpeg bundled with
imageio-ffmpeg -- no system ffmpeg and no API keys required.

    pip install Pillow numpy imageio-ffmpeg
    python3 make_dog_kid.py                 # -> dog_kid.mp4
    python3 make_dog_kid.py out.mp4         # custom output path

Edit the CONFIG block to tweak length, size, or palette.
"""

import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

import imageio_ffmpeg

# --------------------------------------------------------------------------- #
# CONFIG
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 1920, 1080
FPS = 30
DURATION = 12.0          # seconds
SS = 2                   # supersample factor for smooth, anti-aliased edges

W2, H2 = WIDTH * SS, HEIGHT * SS

# Palette
SKY_TOP = (135, 196, 255)
SKY_HORIZON = (224, 244, 255)
GRASS_FAR = (150, 214, 122)
GRASS_NEAR = (96, 184, 88)
SUN = (255, 241, 186)
SUN_GLOW = (255, 247, 214)
CLOUD = (255, 255, 255)

DOG_BODY = (222, 168, 96)
DOG_DARK = (196, 138, 70)
DOG_EAR = (180, 122, 60)
DOG_BELLY = (245, 214, 168)
DOG_NOSE = (60, 46, 42)

SKIN = (255, 214, 178)
SKIN_SH = (236, 188, 150)
HAIR = (96, 64, 40)
SHIRT = (78, 142, 214)
SHIRT_SH = (60, 116, 184)
PANTS = (74, 88, 112)
MOUTH = (150, 70, 70)

HEART = (255, 110, 130)
HEART_HI = (255, 158, 172)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def smooth(x):
    """smoothstep ease-in-out on [0,1]"""
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def phase(t, a, b):
    """0..1 progress of t through window [a,b]"""
    return clamp01((t - a) / (b - a))


def lerp(a, b, u):
    return a + (b - a) * u


# --------------------------------------------------------------------------- #
# static background (built once)
# --------------------------------------------------------------------------- #
def build_background():
    # vertical sky gradient -> grass
    img = np.zeros((H2, W2, 3), dtype=np.float32)
    horizon = int(H2 * 0.62)

    sky = np.linspace(0, 1, horizon, dtype=np.float32)[:, None]
    sky_col = (np.array(SKY_TOP, np.float32) * (1 - sky)
               + np.array(SKY_HORIZON, np.float32) * sky)
    img[:horizon] = sky_col[:, None, :]

    g = np.linspace(0, 1, H2 - horizon, dtype=np.float32)[:, None]
    grass_col = (np.array(GRASS_FAR, np.float32) * (1 - g)
                 + np.array(GRASS_NEAR, np.float32) * g)
    img[horizon:] = grass_col[:, None, :]

    base = Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(base, "RGBA")

    # sun with soft glow
    sx, sy, sr = W2 * 0.80, H2 * 0.20, H2 * 0.085
    for k in range(7, 0, -1):
        rr = sr * (1 + k * 0.42)
        a = int(16 * (1 - k / 8))
        d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=SUN_GLOW + (a,))
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=SUN + (255,))

    # rolling hill highlight on the grass
    hill = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hill, "RGBA")
    hd.ellipse([-W2 * 0.2, horizon - H2 * 0.06, W2 * 0.7, horizon + H2 * 0.3],
               fill=(168, 222, 130, 120))
    hd.ellipse([W2 * 0.45, horizon - H2 * 0.03, W2 * 1.25, horizon + H2 * 0.35],
               fill=(176, 226, 138, 120))
    base = Image.alpha_composite(base, hill)
    return base


BG = build_background()


def draw_clouds(layer, t):
    d = ImageDraw.Draw(layer, "RGBA")
    clouds = [(0.18, 0.16, 0.060, 0.010),
              (0.52, 0.12, 0.075, 0.014),
              (0.83, 0.26, 0.050, 0.008)]
    for fx, fy, fr, sp in clouds:
        x = ((fx + t * sp) % 1.2 - 0.1) * W2
        y = fy * H2
        r = fr * H2
        for dx, dy, rs in [(-1.1, 0.15, 0.8), (0, 0, 1.1),
                           (1.1, 0.15, 0.85), (0.4, -0.35, 0.7)]:
            d.ellipse([x + dx * r - r * rs, y + dy * r - r * rs,
                       x + dx * r + r * rs, y + dy * r + r * rs],
                      fill=CLOUD + (230,))


# --------------------------------------------------------------------------- #
# characters
# --------------------------------------------------------------------------- #
def draw_kid(d, cx, cy, s, kneel, hug):
    """cx,cy = ground point under the kid. s = scale (px). kneel/hug in 0..1."""
    drop = kneel * s * 0.30              # whole figure sinks when kneeling
    cy = cy - s * 0.72 + drop            # hips reference; feet land on ground_y

    # legs
    leg_w = s * 0.16
    if kneel < 0.5:
        for sgn in (-1, 1):
            lx = cx + sgn * s * 0.18
            d.rounded_rectangle([lx - leg_w / 2, cy, lx + leg_w / 2, cy + s * 0.7],
                                radius=leg_w / 2, fill=PANTS)
    else:
        # kneeling: one shin folded, one knee forward
        d.rounded_rectangle([cx - s * 0.30, cy + s * 0.28,
                             cx + s * 0.05, cy + s * 0.46],
                            radius=leg_w / 2, fill=PANTS)
        d.rounded_rectangle([cx + s * 0.02, cy, cx + s * 0.02 + leg_w,
                             cy + s * 0.5], radius=leg_w / 2, fill=PANTS)

    # torso (shirt)
    th = s * 0.62
    d.rounded_rectangle([cx - s * 0.30, cy - th, cx + s * 0.30, cy + s * 0.06],
                        radius=s * 0.18, fill=SHIRT)
    d.rounded_rectangle([cx - s * 0.30, cy - th * 0.45, cx - s * 0.12, cy + s * 0.06],
                        radius=s * 0.12, fill=SHIRT_SH)

    # head
    hr = s * 0.34
    hx, hy = cx, cy - th - hr * 0.75
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=SKIN)
    d.ellipse([hx - hr, hy - hr, hx + hr * 0.1, hy + hr], fill=SKIN_SH)
    # hair
    d.pieslice([hx - hr * 1.05, hy - hr * 1.15, hx + hr * 1.05, hy + hr * 0.4],
               180, 360, fill=HAIR)
    d.rectangle([hx - hr * 1.05, hy - hr * 0.5, hx + hr * 1.05, hy - hr * 0.2],
                fill=HAIR)
    # face: eyes (happy closed arcs) + big smile
    ey = hy - hr * 0.05
    for sgn in (-1, 1):
        ex = hx + sgn * hr * 0.42
        d.arc([ex - hr * 0.22, ey - hr * 0.18, ex + hr * 0.22, ey + hr * 0.22],
              200, 340, fill=(50, 40, 36), width=max(2, int(s * 0.035)))
    # rosy cheeks
    for sgn in (-1, 1):
        cxx = hx + sgn * hr * 0.62
        d.ellipse([cxx - hr * 0.16, ey + hr * 0.22, cxx + hr * 0.16, ey + hr * 0.5],
                  fill=(255, 170, 160, 150))
    d.arc([hx - hr * 0.45, hy + hr * 0.05, hx + hr * 0.45, hy + hr * 0.6],
          20, 160, fill=MOUTH, width=max(2, int(s * 0.045)))

    # arms — reach forward/up to hug the dog as `hug` rises
    reach = smooth(hug)
    sh_y = cy - th * 0.78
    ax = cx + s * 0.28
    hand_x = cx + lerp(s * 0.34, s * 0.95, reach)
    hand_y = sh_y + lerp(s * 0.30, -s * 0.10, reach)
    aw = s * 0.15
    d.line([(cx - s * 0.28, sh_y), (hand_x - s * 1.1, hand_y)],
           fill=SHIRT_SH, width=int(aw))     # far arm
    d.line([(ax, sh_y), (hand_x, hand_y)], fill=SHIRT, width=int(aw))
    d.ellipse([hand_x - aw * 0.6, hand_y - aw * 0.6,
               hand_x + aw * 0.6, hand_y + aw * 0.6], fill=SKIN)


def draw_dog(d, cx, cy, s, facing, run, tail_t, lift):
    """cx,cy = center of dog body. facing -1 = left. run drives leg cycle.
       lift 0..1 = front of body rears up (jump/lick)."""
    f = facing
    rear = smooth(lift)
    tilt = rear * 0.5                       # body tips up at the front

    bw, bh = s * 1.15, s * 0.66
    # legs (behind body) — trot cycle
    leg_w = s * 0.16
    for i, (lx, base_lift, ph) in enumerate(
            [(-0.42, 0.0, 0.0), (-0.30, 0.0, math.pi),
             (0.34, 0.0, math.pi), (0.46, 0.0, 0.0)]):
        swing = math.sin(run * 2 * math.pi + ph) * s * 0.16 * (1 - rear)
        foot_up = max(0.0, math.sin(run * 2 * math.pi + ph)) * s * 0.10
        # back legs fold up as dog rears
        front = lx > 0
        legx = cx + f * lx * s
        top = cy + bh * 0.2 - (rear * s * 0.5 if not front else 0)
        bot = cy + bh * 0.2 + s * 0.62 - foot_up
        if not front:
            bot -= rear * s * 0.35
        d.line([(legx, top), (legx + swing, bot)],
               fill=DOG_DARK, width=int(leg_w))
        d.ellipse([legx + swing - leg_w * 0.6, bot - leg_w * 0.4,
                   legx + swing + leg_w * 0.6, bot + leg_w * 0.5], fill=DOG_DARK)

    # tail (wags) at the rear (opposite facing)
    tx = cx - f * bw * 0.5
    ty = cy - bh * 0.1
    wag = math.sin(tail_t * 2 * math.pi) * 0.6
    tlen = s * 0.7
    tip = (tx - f * math.cos(0.5 + wag) * tlen,
           ty - abs(math.sin(0.9 + wag)) * tlen - s * 0.1)
    d.line([(tx, ty), tip], fill=DOG_BODY, width=int(s * 0.14))
    d.ellipse([tip[0] - s * 0.09, tip[1] - s * 0.09,
               tip[0] + s * 0.09, tip[1] + s * 0.09], fill=DOG_BODY)

    # body (rotated slightly when rearing — approximate with a tilted ellipse box)
    by = cy - rear * s * 0.18
    d.ellipse([cx - bw * 0.5, by - bh * 0.5 - tilt * s * 0.2,
               cx + bw * 0.5, by + bh * 0.5], fill=DOG_BODY)
    # belly highlight
    d.ellipse([cx - bw * 0.32, by - bh * 0.1, cx + bw * 0.32, by + bh * 0.5],
              fill=DOG_BELLY)

    # neck + head toward `facing`, lifted up when rearing
    hx = cx + f * bw * 0.46
    hy = by - bh * 0.3 - rear * s * 0.62
    d.line([(cx + f * bw * 0.2, by - bh * 0.2), (hx, hy)],
           fill=DOG_BODY, width=int(s * 0.42))

    hr = s * 0.34
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=DOG_BODY)
    # ears (floppy)
    er = s * 0.2
    d.ellipse([hx - f * hr * 0.2 - er, hy - hr * 0.9 - er * 0.4,
               hx - f * hr * 0.2 + er * 0.4, hy - hr * 0.9 + er * 1.6],
              fill=DOG_EAR)
    # snout
    snx = hx + f * hr * 0.95
    sny = hy + hr * 0.12
    d.ellipse([snx - s * 0.2, sny - s * 0.14, snx + s * 0.2, sny + s * 0.16],
              fill=DOG_BELLY)
    d.ellipse([snx + f * s * 0.13 - s * 0.07, sny - s * 0.07,
               snx + f * s * 0.13 + s * 0.07, sny + s * 0.07], fill=DOG_NOSE)
    # eye (happy)
    d.arc([hx + f * hr * 0.1 - hr * 0.3, hy - hr * 0.35,
           hx + f * hr * 0.1 + hr * 0.3, hy + hr * 0.05],
          200, 340, fill=(40, 30, 28), width=max(2, int(s * 0.04)))
    # tongue licking out when rearing/licking
    if rear > 0.2:
        tl = rear
        xa = snx + f * s * 0.16
        xb = snx + f * (s * 0.16 + s * 0.22 * tl)
        d.ellipse([min(xa, xb), sny + s * 0.02, max(xa, xb), sny + s * 0.22],
                  fill=(232, 110, 120))


def draw_heart(layer, x, y, r, a, rot=0.0):
    d = ImageDraw.Draw(layer, "RGBA")
    r2 = r * 0.55
    d.ellipse([x - r, y - r2 * 1.1, x, y + r2 * 0.5], fill=HEART + (a,))
    d.ellipse([x, y - r2 * 1.1, x + r, y + r2 * 0.5], fill=HEART + (a,))
    d.polygon([(x - r * 0.92, y), (x + r * 0.92, y), (x, y + r * 1.15)],
              fill=HEART + (a,))
    d.ellipse([x - r * 0.5, y - r2 * 0.9, x - r * 0.1, y - r2 * 0.3],
              fill=HEART_HI + (int(a * 0.9),))


def hearts_layer(t):
    """Hearts puff up from the dog/kid meeting point during the lick/hug."""
    layer = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    start = 5.0
    if t < start:
        return layer
    meet_x, meet_y = W2 * 0.52, H2 * 0.50
    rng_n = 14
    for i in range(rng_n):
        birth = start + i * 0.42
        if t < birth:
            continue
        age = t - birth
        life = 2.6
        if age > life:
            continue
        u = age / life
        seed = (i * 97 + 13) % 100 / 100.0
        x = meet_x + math.sin(i * 1.7) * W2 * 0.10 + math.sin(age * 2 + i) * 18 * SS
        y = meet_y - u * H2 * 0.34 - seed * H2 * 0.05
        r = (0.5 + seed) * 26 * SS * (0.6 + 0.4 * smooth(min(1, u * 3)))
        a = int(235 * (1 - smooth(max(0, (u - 0.6) / 0.4))))
        draw_heart(layer, x, y, r, max(0, a))
    return layer


# --------------------------------------------------------------------------- #
# frame
# --------------------------------------------------------------------------- #
def render_frame(t):
    frame = BG.copy()
    draw_clouds(frame, t)

    d = ImageDraw.Draw(frame, "RGBA")
    ground_y = H2 * 0.86

    # --- timeline ---
    p_run = phase(t, 0.6, 3.4)        # dog runs in from the right
    p_kneel = phase(t, 3.0, 4.6)      # kid kneels to greet
    p_jump = phase(t, 4.4, 5.4)       # dog leaps up
    p_lick = phase(t, 5.2, 12.0)      # licking / loving
    p_hug = phase(t, 4.6, 6.2)        # kid's arms come up

    # kid stands left-of-center
    kid_x = W2 * 0.40
    draw_kid(d, kid_x, ground_y, s=H2 * 0.26,
             kneel=smooth(p_kneel), hug=p_hug)

    # dog: runs from off-right toward the kid, then rears up to lick
    dog_x = lerp(W2 * 1.15, W2 * 0.60, smooth(p_run))
    bob = abs(math.sin(t * 9)) * H2 * 0.02 * (1 - smooth(p_jump))
    dog_y = ground_y - H2 * 0.16 - bob
    # while jumping/licking, lift body up toward the kneeling kid's face
    lift = max(smooth(p_jump), 0.0)
    if t >= 4.4:
        dog_y = lerp(dog_y, ground_y - H2 * 0.30, smooth(p_jump))
    run_cycle = (t * 1.7) % 1.0
    tail_speed = t * (3.2 if t > 5.0 else 1.6)
    draw_dog(d, dog_x, dog_y, s=H2 * 0.17, facing=-1,
             run=run_cycle * (1 - lift), tail_t=tail_speed, lift=lift)

    frame = Image.alpha_composite(frame, hearts_layer(t))

    # gentle vignette + fade in/out
    out = frame.convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    arr = np.asarray(out).astype(np.float32)
    fade = smooth(phase(t, 0, 0.7)) * smooth(phase(DURATION - t, 0, 0.7))
    arr *= fade
    return np.clip(arr, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- #
# encode
# --------------------------------------------------------------------------- #
def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "dog_kid.mp4"
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
          f"({DURATION:.1f}s @ {FPS}fps, {WIDTH}x{HEIGHT}, SS={SS}) -> {out}")
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
