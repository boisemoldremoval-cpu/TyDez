#!/usr/bin/env python3
"""
2D clip: 7-year-old TyGuy helps an elderly neighbor carry groceries.
Polished (DoF, light, vignette, bokeh, camera), voiced. -> grocery_clip.mp4
Then brand_clip.py adds the music + Bible Kids Adventures banner.
"""
import math, wave, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import imageio_ffmpeg
import make_own2d as O      # cinematic() + add_bokeh()
import kid, voices

W, H, FPS, DUR = 1280, 720, 24, 9.0
GROUND = int(H * 0.95)


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(t): return 1 - (1 - clamp(t)) ** 3
def lerp(a, b, t): return a + (b - a) * t


# ---- suburb background ----
_BG = None
def suburb():
    global _BG
    if _BG: return _BG.copy()
    sky = np.zeros((H, W, 3), np.float32)
    top = np.array([135, 200, 245]); bot = np.array([205, 235, 250])
    for y in range(H):
        sky[y] = top + (bot - top) * (y / H)
    img = Image.fromarray(sky.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    gy = int(H * 0.62)
    d.rectangle([0, gy, W, H], fill=(150, 205, 110))          # grass
    # houses row
    cols = [(226, 198, 156), (210, 170, 150), (200, 215, 230), (225, 205, 150)]
    x = -40
    i = 0
    while x < W + 40:
        bw, bh = 260, 150
        by = gy - bh
        d.rectangle([x, by, x + bw, gy], fill=cols[i % 4])
        d.polygon([(x - 14, by), (x + bw + 14, by), (x + bw - 40, by - 60),
                   (x + 40, by - 60)], fill=(150, 80, 70))
        d.rectangle([x + bw * 0.42, gy - 70, x + bw * 0.58, gy], fill=(110, 75, 55))
        for wx in (0.16, 0.72):
            d.rectangle([x + bw * wx, by + 40, x + bw * wx + 44, by + 90],
                        fill=(150, 205, 235), outline=(245, 235, 210), width=4)
        x += bw + 36; i += 1
    # sidewalk
    d.rectangle([0, GROUND - 30, W, GROUND + 40], fill=(206, 200, 188))
    d.rectangle([0, GROUND - 30, W, GROUND - 24], fill=(188, 182, 170))
    # flowers
    rng = np.random.default_rng(4)
    for _ in range(60):
        fx = rng.uniform(0, W); fy = rng.uniform(gy + 6, GROUND - 36)
        c = tuple(int(v) for v in rng.choice([(240, 90, 110), (250, 210, 70),
                                              (240, 140, 200), (255, 255, 255)]))
        d.ellipse([fx - 5, fy - 5, fx + 5, fy + 5], fill=c)
        d.ellipse([fx - 2, fy - 2, fx + 2, fy + 2], fill=(255, 240, 120))
    _BG = img
    return _BG.copy()


def _cap(d, p0, p1, w, c):
    d.line([p0, p1], fill=c, width=w); r = w / 2
    for x, y in (p0, p1): d.ellipse([x - r, y - r, x + r, y + r], fill=c)


def draw_granny(base, cx, feet_y, Hh, t):
    sz = base.size; body = Image.new("RGBA", sz, (0, 0, 0, 0)); d = ImageDraw.Draw(body)
    skin = (238, 206, 180); dress = (170, 140, 200); dress_sh = (140, 112, 170)
    hair = (228, 228, 233)
    hr = Hh * 0.15; hcy = feet_y - Hh * 0.86; shy = feet_y - Hh * 0.70; hpy = feet_y - Hh * 0.50
    bob = math.sin(t * 3) * 3; feet_y += bob; hcy += bob; shy += bob; hpy += bob
    # shoes
    for s in (-1, 1):
        d.ellipse([cx + s * Hh * 0.07 - Hh * 0.06, feet_y - Hh * 0.05,
                   cx + s * Hh * 0.07 + Hh * 0.06, feet_y], fill=(70, 60, 65))
    # dress
    d.polygon([(cx - Hh * 0.11, shy), (cx + Hh * 0.11, shy),
               (cx + Hh * 0.2, feet_y - Hh * 0.04), (cx - Hh * 0.2, feet_y - Hh * 0.04)], fill=dress)
    d.polygon([(cx - Hh * 0.155, (shy + feet_y) / 2), (cx + Hh * 0.155, (shy + feet_y) / 2),
               (cx + Hh * 0.2, feet_y - Hh * 0.04), (cx - Hh * 0.2, feet_y - Hh * 0.04)], fill=dress_sh)
    # arms
    shl = (cx - Hh * 0.1, shy + Hh * 0.02); shr = (cx + Hh * 0.1, shy + Hh * 0.02)
    hl = (cx - Hh * 0.17, hpy + Hh * 0.08); hr2 = (cx + Hh * 0.17, hpy + Hh * 0.06)
    for sh, hd in ((shl, hl), (shr, hr2)):
        mid = ((sh[0] + hd[0]) / 2, (sh[1] + hd[1]) / 2)
        _cap(d, sh, mid, int(Hh * 0.07), dress); _cap(d, mid, hd, int(Hh * 0.06), skin)
        d.ellipse([hd[0] - Hh * 0.04, hd[1] - Hh * 0.04, hd[0] + Hh * 0.04, hd[1] + Hh * 0.04], fill=skin)
    # cane
    d.line([(hr2[0], hr2[1]), (hr2[0] + Hh * 0.05, feet_y)], fill=(120, 82, 50), width=max(3, int(Hh * 0.022)))
    d.line([(hr2[0] - Hh * 0.03, hr2[1] - Hh * 0.005), (hr2[0] + Hh * 0.04, hr2[1] - Hh * 0.005)],
           fill=(120, 82, 50), width=max(3, int(Hh * 0.022)))
    # neck + head
    _cap(d, (cx, shy - Hh * 0.02), (cx, shy + Hh * 0.03), int(Hh * 0.06), skin)
    d.ellipse([cx - hr * 0.55, hcy - hr * 1.35, cx + hr * 0.55, hcy - hr * 0.35], fill=hair)  # bun
    d.ellipse([cx - hr, hcy - hr, cx + hr, hcy + hr], fill=skin)
    d.chord([cx - hr * 1.05, hcy - hr * 1.2, cx + hr * 1.05, hcy + hr * 0.5], 180, 360, fill=hair)
    # outline
    ow = max(3, int(Hh * 0.018))
    sil = Image.new("RGBA", sz, (30, 24, 30, 0)); sil.putalpha(body.split()[3].filter(ImageFilter.MaxFilter(ow * 2 + 1)))
    base.alpha_composite(sil); base.alpha_composite(body)
    # face
    fd = ImageDraw.Draw(base); ey = hcy - hr * 0.05
    for s in (-1, 1):
        ex = cx + s * hr * 0.4
        fd.ellipse([ex - hr * 0.22, ey - hr * 0.22, ex + hr * 0.22, ey + hr * 0.22],
                   outline=(90, 80, 80), width=3, fill=(255, 255, 255))   # glasses
        fd.ellipse([ex - hr * 0.07, ey - hr * 0.07, ex + hr * 0.07, ey + hr * 0.07], fill=(60, 50, 48))
    fd.line([(cx - hr * 0.18, ey), (cx + hr * 0.18, ey)], fill=(90, 80, 80), width=3)
    fd.arc([cx - hr * 0.4, hcy + hr * 0.1, cx + hr * 0.4, hcy + hr * 0.7], 15, 165,
           fill=(150, 90, 90), width=max(2, int(hr * 0.12)))
    for s in (-1, 1):                                                    # rosy cheeks
        fd.ellipse([cx + s * hr * 0.5 - hr * 0.12, hcy + hr * 0.25, cx + s * hr * 0.5 + hr * 0.12,
                    hcy + hr * 0.45], fill=(255, 170, 170, 120))


def draw_bag(d, cx, cy, s):
    d.rectangle([cx - s, cy - s, cx + s, cy + s * 0.9], fill=(190, 150, 100),
                outline=(120, 90, 55), width=3)
    d.line([(cx - s * 0.5, cy - s), (cx - s * 0.5, cy - s * 1.4)], fill=(150, 110, 70), width=4)
    d.line([(cx + s * 0.5, cy - s), (cx + s * 0.5, cy - s * 1.4)], fill=(150, 110, 70), width=4)
    # groceries poking out
    d.ellipse([cx - s * 0.6, cy - s * 1.3, cx - s * 0.1, cy - s * 0.7], fill=(220, 70, 70))
    d.ellipse([cx + s * 0.1, cy - s * 1.25, cx + s * 0.6, cy - s * 0.75], fill=(120, 190, 90))
    d.rectangle([cx - s * 0.15, cy - s * 1.5, cx + s * 0.2, cy - s * 0.9], fill=(240, 220, 150))


def frame_at(t):
    bg = suburb().filter(ImageFilter.GaussianBlur(5))
    d = ImageDraw.Draw(bg, "RGBA")
    # walk slowly together left -> right
    x = lerp(W * 0.34, W * 0.56, eo(clamp(t / DUR)))
    # granny on the right, kid TyGuy on the left
    draw_granny(bg, x + 150, GROUND, 330, t)
    kid.draw_kid(bg, x - 60, GROUND, 230, kid.KID_TYGUY,
                 {"walk": (t * 1.4) % 1, "arm_l": 10, "arm_r": 36, "elbow": 14,
                  "mouth": "smile", "brow": "happy",
                  "blink": 1 if (t * 0.5) % 1 > 0.93 else 0})
    draw_bag(d, x + 30, GROUND - 150, 34)      # bag carried between them
    O.add_bokeh(bg, t)
    zoom = lerp(1.05, 1.0, eo(t / DUR))
    return O.cinematic(bg, t, zoom, lerp(-10, 10, t / DUR), 0)


def build_voice(path):
    total = int((DUR + 0.5) * voices.SR); buf = np.zeros(total, np.float32)
    for vc, txt, delay, pitch in [("ty", "Here, let me help you carry that!", 0.6, 1.28),
                                  ("mia", "Oh, thank you so much, dear!", 4.6, 0.92)]:
        clip = voices.synth(vc, txt, pitch)
        s = int(delay * voices.SR); e = min(total, s + len(clip)); buf[s:e] += clip[:e - s]
    pcm = (np.clip(buf, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(voices.SR); wf.writeframes(pcm.tobytes())


def main():
    ff = imageio_ffmpeg.get_ffmpeg_exe(); n = int(DUR * FPS)
    print(f"grocery clip: {DUR}s {n} frames"); build_voice("voiceG.wav")
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", "voiceG.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "18", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
           "-shortest", "-movflags", "+faststart", "grocery_clip.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(n):
        p.stdin.write(frame_at(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print("Done -> grocery_clip.mp4")


if __name__ == "__main__":
    main()
