"""
Animated cartoon cat video — pure Pillow frames + bundled ffmpeg.

No system ffmpeg, no external services or API credits: frames are drawn from
primitives (same approach as make_promo.py) and piped to the ffmpeg binary that
ships with imageio-ffmpeg.

    pip install Pillow numpy imageio-ffmpeg
    python3 make_cat_video.py            # -> cat.mp4
    python3 make_cat_video.py out.mp4    # custom output path
"""

import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw
import imageio_ffmpeg


# --------------------------------------------------------------------------- #
# config
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 1280, 720
FPS = 30
DURATION = 6.0

CAT = {
    "fur":      (242, 164, 78),     # orange tabby
    "fur_dark": (214, 132, 52),     # stripes / shading
    "belly":    (252, 232, 206),
    "inner_ear": (240, 170, 175),
    "nose":     (226, 120, 128),
    "eye":      (74, 150, 96),       # green eyes
    "pupil":    (28, 24, 22),
    "mouth":    (120, 70, 60),
    "collar":   (58, 150, 118),      # TyDez green
    "tag":      (245, 205, 80),
    "yarn":     (214, 92, 108),
    "outline":  (60, 42, 30),
}


def _lerp(a, b, t):
    return a + (b - a) * t


def _bezier(p0, p1, p2, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def _thick_curve(d, pts, width, color):
    d.line(pts, fill=color, width=width, joint="curve")
    r = width / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)


# --------------------------------------------------------------------------- #
# the cat
# --------------------------------------------------------------------------- #
def draw_cat(img, cx, feet_y, S, t):
    """Draw an animated sitting cat. S ~ overall scale in px."""
    d = ImageDraw.Draw(img)
    pal = CAT
    ol = pal["outline"]
    olw = max(2, int(S * 0.02))

    bob = math.sin(t * 2.2) * S * 0.03          # gentle breathing bob
    tail_sw = math.sin(t * 2.6) * 0.5           # tail swish phase
    ear_tw = max(0.0, math.sin(t * 3.1)) * S * 0.04
    # blink: quick close roughly every ~2.2s
    bph = (t % 2.3)
    blink = 1.0 if 0.0 <= bph < 0.12 else 0.0

    body_cy = feet_y - S * 0.52 + bob
    head_cy = feet_y - S * 1.02 + bob
    head_r = S * 0.42

    # ---- tail (behind body), swishing ----
    base = (cx + S * 0.55, body_cy + S * 0.35)
    tip = (cx + S * (0.95 + 0.18 * tail_sw), body_cy - S * (0.25 + 0.25 * tail_sw))
    ctrl = (cx + S * 1.15, body_cy + S * 0.05)
    tail = _bezier(base, ctrl, tip)
    _thick_curve(d, tail, int(S * 0.17), pal["fur"])
    # tail stripes
    for frac in (0.45, 0.68, 0.9):
        i = int(frac * (len(tail) - 1))
        x, y = tail[i]
        d.ellipse([x - S * 0.07, y - S * 0.05, x + S * 0.07, y + S * 0.05],
                  fill=pal["fur_dark"])

    # ---- body ----
    d.ellipse([cx - S * 0.55, body_cy - S * 0.45, cx + S * 0.55, feet_y],
              fill=pal["fur"], outline=ol, width=olw)
    # belly
    d.ellipse([cx - S * 0.30, body_cy - S * 0.05, cx + S * 0.30, feet_y - S * 0.02],
              fill=pal["belly"])
    # body stripes
    for sx in (-0.34, 0.0, 0.34):
        d.arc([cx + S * sx - S * 0.12, body_cy - S * 0.42,
               cx + S * sx + S * 0.12, body_cy - S * 0.02],
              start=200, end=340, fill=pal["fur_dark"], width=max(2, int(S * 0.03)))
    # front paws
    for sx in (-0.24, 0.24):
        px = cx + S * sx
        d.ellipse([px - S * 0.16, feet_y - S * 0.14, px + S * 0.16, feet_y + S * 0.04],
                  fill=pal["belly"], outline=ol, width=max(2, olw - 1))
        for k in (-1, 0, 1):
            d.line([(px + k * S * 0.06, feet_y - S * 0.12),
                    (px + k * S * 0.06, feet_y - S * 0.02)],
                   fill=pal["fur_dark"], width=max(1, int(S * 0.014)))

    # ---- collar + tag ----
    cy_col = body_cy - S * 0.30
    d.line([(cx - S * 0.30, cy_col), (cx + S * 0.30, cy_col)],
           fill=pal["collar"], width=max(3, int(S * 0.08)))
    d.ellipse([cx - S * 0.06, cy_col + S * 0.04, cx + S * 0.06, cy_col + S * 0.16],
              fill=pal["tag"], outline=ol, width=max(2, olw - 1))

    # ---- ears (behind head) ----
    for sgn in (-1, 1):
        ex = cx + sgn * head_r * 0.72
        ey = head_cy - head_r * 0.72 - (ear_tw if sgn > 0 else ear_tw * 0.6)
        tip_e = (ex + sgn * head_r * 0.28, ey - head_r * 0.62)
        base_a = (ex - head_r * 0.34, ey + head_r * 0.12)
        base_b = (ex + head_r * 0.40, ey + head_r * 0.06)
        d.polygon([base_a, tip_e, base_b], fill=pal["fur"], outline=ol)
        d.polygon([(_lerp(base_a[0], tip_e[0], 0.35), _lerp(base_a[1], tip_e[1], 0.35)),
                   tip_e,
                   (_lerp(base_b[0], tip_e[0], 0.35), _lerp(base_b[1], tip_e[1], 0.35))],
                  fill=pal["inner_ear"])

    # ---- head ----
    d.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r],
              fill=pal["fur"], outline=ol, width=olw)
    # forehead stripes (classic tabby "M")
    for sx in (-0.18, 0.0, 0.18):
        d.line([(cx + head_r * sx, head_cy - head_r * 0.92),
                (cx + head_r * sx, head_cy - head_r * 0.55)],
               fill=pal["fur_dark"], width=max(2, int(S * 0.025)))
    # cheeks (lighter)
    d.ellipse([cx - head_r * 0.85, head_cy + head_r * 0.05,
               cx + head_r * 0.85, head_cy + head_r * 0.80], fill=pal["belly"])

    # ---- eyes ----
    for sgn in (-1, 1):
        ex = cx + sgn * head_r * 0.42
        ey = head_cy - head_r * 0.08
        er = head_r * 0.24
        if blink:
            d.arc([ex - er, ey - er, ex + er, ey + er],
                  start=20, end=160, fill=ol, width=max(2, int(S * 0.02)))
        else:
            d.ellipse([ex - er, ey - er * 1.1, ex + er, ey + er * 1.1], fill=pal["eye"])
            # vertical slit pupil
            d.ellipse([ex - er * 0.28, ey - er * 0.95, ex + er * 0.28, ey + er * 0.95],
                      fill=pal["pupil"])
            d.ellipse([ex - er * 0.30, ey - er * 0.7, ex, ey - er * 0.2],
                      fill=(255, 255, 255))

    # ---- nose + mouth ----
    nx, ny = cx, head_cy + head_r * 0.30
    d.polygon([(nx - S * 0.05, ny), (nx + S * 0.05, ny), (nx, ny + S * 0.06)],
              fill=pal["nose"])
    d.line([(nx, ny + S * 0.06), (nx, ny + S * 0.12)], fill=ol, width=max(2, olw - 1))
    d.arc([nx - S * 0.14, ny + S * 0.02, nx, ny + S * 0.18], start=20, end=150,
          fill=ol, width=max(2, olw - 1))
    d.arc([nx, ny + S * 0.02, nx + S * 0.14, ny + S * 0.18], start=30, end=160,
          fill=ol, width=max(2, olw - 1))

    # ---- whiskers ----
    for sgn in (-1, 1):
        for dy in (-S * 0.03, S * 0.03, S * 0.09):
            d.line([(nx + sgn * S * 0.10, ny + S * 0.05 + dy * 0.3),
                    (nx + sgn * S * 0.42, ny + dy)],
                   fill=(250, 250, 250), width=max(1, int(S * 0.012)))


# --------------------------------------------------------------------------- #
# scene
# --------------------------------------------------------------------------- #
def _bg(t):
    img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    top = np.array([120, 196, 214])
    bot = np.array([208, 240, 232])
    ramp = np.linspace(0, 1, HEIGHT)[:, None]
    col = (top[None, :] * (1 - ramp) + bot[None, :] * ramp).astype(np.uint8)
    img = Image.fromarray(np.repeat(col[:, None, :], WIDTH, axis=1))
    d = ImageDraw.Draw(img)
    # floor
    fy = int(HEIGHT * 0.80)
    d.rectangle([0, fy, WIDTH, HEIGHT], fill=(206, 230, 220))
    d.ellipse([WIDTH * 0.20, fy - 30, WIDTH * 0.80, HEIGHT - 10], fill=(196, 222, 212))
    # drifting clouds
    for cxb, cyb, s in ((0.18, 0.22, 1.0), (0.62, 0.15, 1.3), (0.85, 0.30, 0.8)):
        px = (cxb * WIDTH + (t * 14 * s)) % (WIDTH + 260) - 130
        py = cyb * HEIGHT
        for ox, oy, r in ((0, 0, 42), (46, 8, 34), (-44, 10, 32), (14, -16, 30)):
            d.ellipse([px + ox * s - r * s, py + oy * s - r * s,
                       px + ox * s + r * s, py + oy * s + r * s],
                      fill=(244, 252, 250))
    return img


def _hearts(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(5):
        ph = (t * 0.35 + k * 0.2) % 1.0
        hx = WIDTH * (0.30 + 0.12 * k) + math.sin((t + k) * 1.6) * 22
        hy = HEIGHT * 0.70 - ph * HEIGHT * 0.55
        a = int(220 * (1 - ph))
        s = 10 + 6 * math.sin(t * 3 + k)
        col = (235, 120, 140, max(0, a))
        d.ellipse([hx - s, hy - s, hx, hy], fill=col)
        d.ellipse([hx, hy - s, hx + s, hy], fill=col)
        d.polygon([(hx - s, hy - s * 0.2), (hx + s, hy - s * 0.2), (hx, hy + s * 1.1)],
                  fill=col)


def _yarn(img, cx, feet_y, S, t):
    d = ImageDraw.Draw(img)
    # bounces next to the cat
    bx = cx - S * 0.95
    by = feet_y - abs(math.sin(t * 3.0)) * S * 0.5 - S * 0.12
    r = S * 0.16
    d.ellipse([bx - r, by - r, bx + r, by + r], fill=CAT["yarn"],
              outline=CAT["outline"], width=3)
    for a in range(-2, 3):
        d.arc([bx - r, by - r, bx + r, by + r], start=20 + a * 36,
              end=160 + a * 36, fill=(170, 60, 76), width=2)
    d.line([(bx + r * 0.2, by), (bx + r * 1.8, by + r * 1.2)],
           fill=CAT["yarn"], width=3)


def render_frame(t):
    img = _bg(t)
    cx, feet_y, S = WIDTH * 0.52, HEIGHT * 0.80, 230
    _yarn(img, cx, feet_y, S, t)
    draw_cat(img, cx, feet_y, S, t)
    _hearts(img, t)
    # title
    d = ImageDraw.Draw(img)
    msg = "Meow!"
    tw = len(msg) * 20
    d.text((cx - tw / 2 + 2, HEIGHT * 0.10 + 2), msg, fill=(40, 60, 70))
    d.text((cx - tw / 2, HEIGHT * 0.10), msg, fill=(255, 255, 255))
    return np.asarray(img, dtype=np.uint8)


def main(out="cat.mp4"):
    n_frames = int(DURATION * FPS)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS),
        "-i", "-", "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "18",
        "-movflags", "+faststart",
        out,
    ]
    print(f"Rendering {n_frames} frames ({DURATION:.1f}s @ {FPS}fps, "
          f"{WIDTH}x{HEIGHT}) -> {out}")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(n_frames):
        proc.stdin.write(render_frame(i / FPS).tobytes())
        if i % 30 == 0:
            print(f"  {i:4d}/{n_frames}")
    proc.stdin.close()
    proc.wait()
    print(f"Done -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "cat.mp4")
