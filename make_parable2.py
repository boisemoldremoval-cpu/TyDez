#!/usr/bin/env python3
"""
"Bible Kids Adventures — The Lost Sheep" (2D, polished).
Kid TyGuy frames the parable (Luke 15) -> verse Luke 15:6. -> parable2.mp4
Assemble: intro_bka + parable2 + outro_bka.
"""
import math, wave, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import imageio_ffmpeg
import make_cartoon as M
import make_own2d as O
import bg2, kid, figures as F, voices

W, H, FPS = 1280, 720, 24
GD, GC = int(H * 0.93), int(H * 0.94)


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(t): return 1 - (1 - clamp(t)) ** 3
def lerp(a, b, t): return a + (b - a) * t
def fade(t, dur, f=0.5): return clamp(min(t / f, (dur - t) / f))
def bobf(t, s=0, a=4): return math.sin(t * 2.4 + s) * a
def sbob(t, s=0): return math.sin(t * 3.0 + s) * 4


SCENES = []
def scene(dur, text=None):
    def deco(fn): SCENES.append((dur, fn, text)); return fn
    return deco


def mead(t): return bg2.meadow(t).filter(ImageFilter.GaussianBlur(4))
def club(t): return bg2.club_room(t).filter(ImageFilter.GaussianBlur(3))
def cinem(img, t, dur):
    O.add_bokeh(img, t)
    return O.cinematic(img, t, lerp(1.05, 1.0, eo(t / dur)), lerp(-8, 8, t / dur), 0)


def staff(d, hx, top_y, ground_y):
    d.line([(hx, top_y), (hx, ground_y)], fill=(120, 84, 52), width=8)
    d.arc([hx - 26, top_y - 28, hx + 26, top_y + 8], start=170, end=20, fill=(120, 84, 52), width=8)


@scene(7.5, lambda d, t, dr: M.speech(d, W * 0.5, H * 0.16,
        "Here's a story about a shepherd who never gave up on one little sheep!",
        clamp((t - 0.3) / 0.3) * fade(t, dr, 0.4)))
def s_club_intro(t, dur):
    img = club(t)
    kid.draw_kid(img, W * 0.5, GC - bobf(t), 360, kid.KID_TYGUY,
                 {"arm_l": 40, "elbow": 14, "mouth": "bigsmile", "brow": "happy",
                  "blink": 1 if (t * 0.5) % 1 > 0.93 else 0})
    return cinem(img, t, dur)


@scene(8.0, lambda d, t, dr: M.caption(d, "A shepherd had a hundred sheep, and loved every one.", fade(t, dr)))
def s_flock(t, dur):
    img = mead(t)
    d = ImageDraw.Draw(img, "RGBA")
    staff(d, W * 0.20, GD - 300, GD)
    F.draw_robed(img, W * 0.24, GD, 300, F.SHEPHERD, {"bob": bobf(t), "arm_l": 12, "arm_r": 12})
    for i, x in enumerate((0.46, 0.58, 0.68, 0.80, 0.90)):
        F.draw_sheep(img, W * x, GD - 6, 120, look=1, bob=sbob(t, i))
    return cinem(img, t, dur)


@scene(8.0, lambda d, t, dr: M.caption(d, "But one little lamb wandered far away... and got lost.", fade(t, dr)))
def s_wander(t, dur):
    img = mead(t)
    d = ImageDraw.Draw(img, "RGBA")
    staff(d, W * 0.18, GD - 300, GD)
    F.draw_robed(img, W * 0.22, GD, 300, F.SHEPHERD, {"bob": bobf(t)})
    for i, x in enumerate((0.40, 0.50, 0.60)):
        F.draw_sheep(img, W * x, GD - 6, 120, look=-1, bob=sbob(t, i))
    wx = lerp(W * 0.72, W * 0.95, eo(clamp(t / dur)))   # the straggler drifts off
    F.draw_sheep(img, wx, GD - 6, 116, look=1, bob=sbob(t, 9))
    return cinem(img, t, dur)


@scene(8.0, lambda d, t, dr: M.caption(d, "He counted them — ninety-eight, ninety-nine... one was missing!", fade(t, dr)))
def s_count(t, dur):
    img = mead(t)
    d = ImageDraw.Draw(img, "RGBA")
    staff(d, W * 0.30, GD - 300, GD)
    F.draw_robed(img, W * 0.34, GD, 300, F.SHEPHERD,
                 {"bob": bobf(t), "arm_r": 70, "elbow": 18})   # hand raised, counting
    for i, x in enumerate((0.56, 0.66, 0.78, 0.88)):
        F.draw_sheep(img, W * x, GD - 6, 120, look=-1, bob=sbob(t, i))
    M.ctext(M.D(img), "?", M.font(M.F_BOLD, 90), H * 0.30, (240, 90, 90),
            fade(t, dur), cx=W * 0.5)
    return cinem(img, t, dur)


@scene(9.0, lambda d, t, dr: M.caption(d, "He left the ninety-nine and searched everywhere for the one.", fade(t, dr)))
def s_search(t, dur):
    img = mead(t)
    d = ImageDraw.Draw(img, "RGBA")
    x = lerp(W * 0.12, W * 0.60, eo(clamp(t / dur)))
    staff(d, x - 40, GD - 290, GD)
    F.draw_robed(img, x, GD, 300, F.SHEPHERD,
                 {"bob": bobf(t), "arm_r": 60, "elbow": 16, "lean": 6})
    return cinem(img, t, dur)


@scene(9.0)
def s_found(t, dur):
    img = mead(t)
    d = ImageDraw.Draw(img, "RGBA")
    # a bush the lamb is stuck near
    d.ellipse([W * 0.74, GD - 60, W * 0.92, GD + 10], fill=(96, 140, 78, 255))
    F.draw_sheep(img, W * 0.80, GD - 4, 116, look=-1, bob=sbob(t))
    x = lerp(W * 0.30, W * 0.58, eo(clamp(t / 1.6)))
    staff(d, x - 38, GD - 250, GD)
    F.draw_robed(img, x, GD, 300, F.SHEPHERD,
                 {"bob": bobf(t) if t < 1.6 else 0, "arm_r": 80, "elbow": 20, "lean": 10})
    for i in range(5):                       # joy sparkles
        hp = (t * 0.6 + i * 0.2) % 1.0
        M._gold_cross(d, W * 0.72 + math.sin(i + t) * 40, lerp(GD - 200, H * 0.2, hp), 10)
    return cinem(img, t, dur)


@scene(8.0, lambda d, t, dr: M.caption(d, "He lifted it onto his shoulders and carried it home — so happy!", fade(t, dr)))
def s_carry(t, dur):
    img = mead(t)
    d = ImageDraw.Draw(img, "RGBA")
    x = lerp(W * 0.30, W * 0.55, eo(clamp(t / dur)))
    F.draw_robed(img, x, GD, 300, F.SHEPHERD, {"bob": bobf(t), "arm_l": 30, "arm_r": 30, "elbow": 20})
    F.draw_sheep(img, x, GD - 300 + bobf(t), 96, look=1, bob=0)   # lamb on shoulders
    for i, sx in enumerate((0.16, 0.74, 0.86)):
        F.draw_sheep(img, W * sx, GD - 6, 118, look=1, bob=sbob(t, i))
    return cinem(img, t, dur)


@scene(9.0, lambda d, t, dr: M.speech(d, W * 0.5, H * 0.15,
        "God is like that shepherd. He loves YOU so much, He'd never give up on you!",
        clamp((t - 0.3) / 0.3) * fade(t, dr, 0.4)))
def s_lesson(t, dur):
    img = club(t)
    kid.draw_kid(img, W * 0.5, GC - bobf(t), 360, kid.KID_TYGUY,
                 {"arm_l": 36, "elbow": 14, "mouth": "bigsmile", "brow": "happy",
                  "blink": 1 if (t * 0.5) % 1 > 0.93 else 0})
    return cinem(img, t, dur)


@scene(8.0)
def s_verse(t, dur):
    img = M.starburst(t).convert("RGBA")
    d = M.D(img)
    M._gold_cross(d, W * 0.5, H * 0.20, 42)
    a = clamp((t - 0.2) / 0.5)
    M.ctext(d, "“Rejoice with me; I have", M.font(M.F_SERIF, 48), H * 0.40, (255, 255, 255), a)
    M.ctext(d, "found my lost sheep!”", M.font(M.F_SERIF, 48), H * 0.50, (255, 255, 255), clamp((t - 0.6) / 0.5))
    M.ctext(d, "Luke 15:6", M.font(M.F_BOLD, 38), H * 0.63, (255, 210, 80), clamp((t - 1.1) / 0.5))
    M.ctext(d, "You matter to God!", M.font(M.F_REG, 34), H * 0.74, (200, 222, 255), clamp((t - 1.6) / 0.5))
    return img.convert("RGB")


DURATION = sum(s[0] for s in SCENES)

NAR = [
    [("ty", "Hey friends! Here's a story about a shepherd who never gave up on one little sheep.", 0.4, 1.28)],
    [("ty", "A shepherd had a hundred sheep, and he loved every single one.", 0.4, 1.0)],
    [("ty", "But one little lamb wandered far away, and got lost.", 0.4, 1.0)],
    [("ty", "The shepherd counted them. Ninety eight, ninety nine... one was missing!", 0.4, 1.0)],
    [("ty", "So he left the ninety nine, and searched everywhere for the one.", 0.4, 1.0)],
    [("ty", "Until at last, he found it!", 0.3, 1.0), ("ty", "There you are! I found you!", 2.7, 0.9)],
    [("ty", "He lifted it onto his shoulders, and carried it home, so happy.", 0.4, 1.0)],
    [("ty", "God is just like that shepherd. He loves you so much, he would never give up on you!", 0.4, 1.28)],
    [("ty", "Rejoice with me, I have found my lost sheep! Luke fifteen, verse six.", 0.5, 1.0)],
]


def build_voice(path):
    tot = int((DURATION + 1.0) * voices.SR); buf = np.zeros(tot, np.float32); acc = 0.0
    for (dur, _f, _t), lines in zip(SCENES, NAR):
        for vc, txt, delay, pitch in lines:
            clip = voices.synth(vc, txt, pitch)
            s = int((acc + delay) * voices.SR); e = min(tot, s + len(clip)); buf[s:e] += clip[:e - s]
        acc += dur
    pcm = (np.clip(buf, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(voices.SR); wf.writeframes(pcm.tobytes())


def frame_at(t):
    acc = 0.0
    for dur, fn, text in SCENES:
        if acc <= t < acc + dur:
            lt = t - acc
            rgb = fn(lt, dur)
            if text:
                wrap = M.D(rgb.convert("RGBA")); text(wrap, lt, dur); return wrap._image.convert("RGB")
            return rgb
        acc += dur
    return frame_at(DURATION - 1e-3)


def main():
    ff = imageio_ffmpeg.get_ffmpeg_exe(); n = int(DURATION * FPS)
    print(f"parable2: {DURATION:.0f}s {n} frames"); M.generate_music("musicP2.wav", DURATION + 0.3)
    print("voices..."); build_voice("voiceP2.wav")
    amix = ("[1:a]volume=0.24,aresample=48000,aformat=channel_layouts=stereo[m];"
            "[2:a]volume=1.8,aresample=48000,aformat=channel_layouts=stereo[v];"
            "[m][v]amix=inputs=2:duration=first:normalize=0[a]")
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", "musicP2.wav", "-i", "voiceP2.wav", "-filter_complex", amix,
           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-shortest",
           "-movflags", "+faststart", "parable2.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(n):
        p.stdin.write(frame_at(i / FPS).tobytes())
        if i % 48 == 0: print(f"  {i}/{n}")
    p.stdin.close(); p.wait(); print("Done -> parable2.mp4")


if __name__ == "__main__":
    main()
