#!/usr/bin/env python3
"""
"The New Kid" -- a dramatized TyGuy Biblical-moral story.

TyGuy (your real artwork, animated as a cutout) welcomes Mia, a lonely new
kid (a drawn cel-shaded character), in a hand-drawn schoolyard. Two voices
(Piper TTS), a music bed, captions and speech bubbles. Moral: love your
neighbor / be kind (Ephesians 4:32).

    python3 make_story2d.py        # -> story2d.mp4
Then build_film2d.py (MID=story2d.mp4) splices intro + story + outro.
"""

import math
import wave
import subprocess

import numpy as np
from PIL import ImageDraw
import imageio_ffmpeg

import make_cartoon as M
import make_tyguy2d as A      # reuse cutout + motion/fx helpers
import bg2
import kid
import voices

W, H, FPS = 1280, 720, 24
OUT = "story2d.mp4"

clamp = A.clamp
eo = A.eo
ease_out_back = A.ease_out_back
CUT = A.CUT
KID_FEET = int(H * 0.93)


def lerp(a, b, t):
    return a + (b - a) * t


def blink(t, seed=0.0):
    return 1 if (t * 0.5 + seed) % 1.0 > 0.93 else 0


def kbob(t, seed=0.0, amp=5.0):
    return math.sin(t * 2.0 + seed) * amp


def fade(t, dur, f=0.5):
    return clamp(min(t / f, (dur - t) / f))


# --------------------------------------------------------------------------- #
SCENES = []


def scene(dur):
    def deco(fn):
        SCENES.append((dur, fn))
        return fn
    return deco


@scene(5.0)
def s_establish(t, dur):
    img = bg2.schoolyard(t)
    d = M.D(img)
    bo = kbob(t, 1)
    kid.draw_kid(img, W * 0.30, KID_FEET - bo, 300, kid.MIA,
                 {"mouth": "sad", "brow": "sad", "lean": 4, "blink": blink(t, 1)})
    M.caption(d, "It was Mia's first day. She didn't know anyone...", fade(t, dur))
    return img.convert("RGB")


@scene(4.5)
def s_ignored(t, dur):
    img = bg2.schoolyard(t)
    d = M.D(img)
    bo = kbob(t, 1)
    kid.draw_kid(img, W * 0.30, KID_FEET - bo, 300, kid.MIA,
                 {"mouth": "sad", "brow": "sad", "lean": 5, "blink": blink(t, 1),
                  "look": -1})
    # two kids stroll across, chatting, ignoring her
    p = clamp(t / (dur - 0.3))
    for pal, x0, x1, seed in ((kid.KID1, W * 1.15, W * 0.52, 2),
                              (kid.KID2, W * 1.30, W * 0.66, 5)):
        x = lerp(x0, x1, eo(p))
        sw = math.sin(t * 7 + seed) * 18
        kid.draw_kid(img, x, KID_FEET, 300, pal,
                     {"walk": (t * 1.7 + seed) % 1, "arm_l": 16 + sw / 2,
                      "arm_r": 16 - sw / 2, "mouth": "smile", "lean": 6})
    M.caption(d, "But the other kids just hurried on by...", fade(t, dur))
    return img.convert("RGB")


@scene(4.2)
def s_notice(t, dur):
    img = bg2.schoolyard(t)
    d = M.D(img)
    bo = kbob(t, 1)
    kid.draw_kid(img, W * 0.28, KID_FEET - bo, 300, kid.MIA,
                 {"mouth": "sad", "brow": "sad", "blink": blink(t, 1)})
    # TyGuy hops in from the right
    p = clamp(t / 0.6)
    y_in = (1 - ease_out_back(p)) * 440
    sx, sy = A.land_squash(t / 0.6) if t < 0.62 else (1, 1)
    hy = A.hop_cycle(t - 0.62, 1.0, 26)[0] if t >= 0.62 else 0
    A.draw_cut(img, CUT["full"], W * 0.66, H * 0.99 + y_in + hy, 440,
               alpha=clamp(t / 0.2), sx_mul=sx, sy_mul=sy)
    if t > 0.7:
        M.speech(d, W * 0.66, H * 0.14, "Hey there! Are you new here?",
                 clamp((t - 0.7) / 0.3) * fade(t, dur, 0.4))
    return img.convert("RGB")


@scene(5.0)
def s_welcome(t, dur):
    img = bg2.schoolyard(t)
    d = M.D(img)
    bo = kbob(t, 1)
    kid.draw_kid(img, W * 0.28, KID_FEET - bo, 300, kid.MIA,
                 {"mouth": "neutral", "brow": "normal", "blink": blink(t, 1),
                  "look": -1})
    # TyGuy walks from right toward Mia then gestures (point pose)
    mt = dur * 0.4
    if t < mt:
        x = lerp(W * 0.66, W * 0.50, eo(t / mt))
        hy = A.hop_cycle(t, 1.5, 22)[0]
        pose = "full"
    else:
        x = W * 0.50
        hy = 0
        pose = "point"
    A.draw_cut(img, CUT[pose], x, H * 0.99 + hy, 440, alpha=clamp(t / 0.2))
    if t > mt + 0.2:
        M.speech(d, W * 0.52, H * 0.14, "Hi, I'm Ty! Come hang out with us!",
                 clamp((t - mt - 0.2) / 0.3) * fade(t, dur, 0.4))
    return img.convert("RGB")


@scene(4.4)
def s_happy(t, dur):
    img = bg2.schoolyard(t)
    d = M.D(img)
    # Mia lights up + little hop
    hop = abs(math.sin(t * 3.2)) * 16 if t > 0.3 else 0
    kid.draw_kid(img, W * 0.34, KID_FEET - hop, 310, kid.MIA,
                 {"mouth": "bigsmile", "brow": "happy", "blush": True,
                  "arm_l": 38, "elbow": 14, "blink": blink(t, 1)})
    A.draw_cut(img, CUT["cheer"], W * 0.66, H * 0.99 + A.hop_cycle(t, 1.2, 20)[0],
               420, alpha=1.0)
    for i in range(5):                 # sparkly hearts
        hp = (t * 0.6 + i * 0.2) % 1.0
        hx = W * 0.46 + math.sin(i * 2 + t) * 70
        hy = lerp(H * 0.6, H * 0.18, hp)
        M.heart(d, hx, hy, 16 * (1 - hp * 0.4), a=clamp(1 - hp))
    if t > 0.4:
        M.speech(d, W * 0.30, H * 0.16, "Really? Thank you!",
                 clamp((t - 0.4) / 0.3) * fade(t, dur, 0.4))
    return img.convert("RGB")


@scene(4.5)
def s_together(t, dur):
    img = bg2.schoolyard(t)
    d = M.D(img)
    kid.draw_kid(img, W * 0.36, KID_FEET - kbob(t, 0, 7), 310, kid.MIA,
                 {"mouth": "bigsmile", "brow": "happy", "arm_r": 34,
                  "elbow": 12, "blink": blink(t, 1)})
    A.draw_cut(img, CUT["cheer"], W * 0.62, H * 0.99 + A.hop_cycle(t, 1.0, 18)[0],
               430, alpha=1.0)
    M.caption(d, "One small kindness changed her whole day.", fade(t, dur))
    return img.convert("RGB")


@scene(7.0)
def s_verse(t, dur):
    img = M.starburst(t).convert("RGBA")
    d = M.D(img)
    M._gold_cross(d, W * 0.30, H * 0.20, 40)
    M.ctext(d, "“Be kind to one another,", M.font(M.F_SERIF, 44),
            H * 0.34, (255, 255, 255), clamp((t - 0.2) / 0.5), cx=W * 0.42)
    M.ctext(d, "tender-hearted, forgiving one another.”",
            M.font(M.F_SERIF, 44), H * 0.43, (255, 255, 255),
            clamp((t - 0.7) / 0.5), cx=W * 0.42)
    M.ctext(d, "Ephesians 4:32", M.font(M.F_BOLD, 36),
            H * 0.55, (255, 210, 80), clamp((t - 1.3) / 0.5), cx=W * 0.42)
    M.ctext(d, "“Love your neighbor as yourself.” — Mark 12:31",
            M.font(M.F_REG, 26), H * 0.66, (200, 222, 255),
            clamp((t - 1.8) / 0.5), cx=W * 0.42)
    hy, hsx, hsy = A.hop_cycle(t, 0.8, 22)
    A.draw_cut(img, CUT["cheer"], W * 0.86, H * 0.99 + hy, 420 * eo(clamp(t / 0.5)),
               alpha=fade(t, dur, 0.6), sx_mul=hsx, sy_mul=hsy, shadow=False)
    return img.convert("RGB")


@scene(5.0)
def s_outro(t, dur):
    img = M.starburst(t).convert("RGBA")
    d = M.D(img)
    p = clamp(t / 0.5)
    y_in = (1 - ease_out_back(p)) * 420
    spin = 0.0
    sx, sy = A.land_squash(t / 0.5) if t < 0.52 else (1, 1)
    if 2.4 <= t < 3.0:
        spin = -360 * eo((t - 2.4) / 0.6)
        A.burst(d, W * 0.5, H * 0.5, clamp((t - 2.4) / 0.6), 1.0, col=(255, 255, 255))
        hy = 0
    elif t >= 0.52:
        hy, sx, sy = A.hop_cycle(t - 0.52, 1.0, 26)
    else:
        hy = 0
    A.draw_cut(img, CUT["full"], W * 0.5, H * 0.99 + y_in + hy, 470,
               rot=spin, alpha=clamp(t / 0.2), sx_mul=sx, sy_mul=sy)
    pulse = 1 + 0.05 * math.sin(t * 5)
    M.ctext(d, "Be kind. Have fun. Be you!", M.font(M.F_BOLD, int(58 * pulse)),
            H * 0.12, (255, 255, 255), fade(t, dur))
    return img.convert("RGB")


DURATION = sum(s[0] for s in SCENES)

# (voice, text, delay, pitch) aligned to SCENES
NARRATION = [
    ("ty", "It was Mia's first day at a new school. She didn't know anybody.", 0.4, 1.0),
    ("ty", "But the other kids just hurried on by.", 0.5, 1.0),
    ("ty", "Hey there! Are you new here?", 0.7, 1.0),
    ("ty", "I'm Ty! Come hang out with us!", 0.6, 1.0),
    ("mia", "Really? Thank you so much!", 0.5, 1.14),
    ("ty", "One small kindness changed her whole day.", 0.4, 1.0),
    ("ty", "Be kind to one another, tender hearted, forgiving one another. "
           "Ephesians four, thirty two.", 0.5, 1.0),
    ("ty", "Remember. Be kind, have fun, and be you! See you next time!", 0.4, 1.0),
]


def build_voice_track(path):
    total = int((DURATION + 1.0) * voices.SR)
    buf = np.zeros(total, np.float32)
    acc = 0.0
    for (dur, _fn), (vc, text, delay, pitch) in zip(SCENES, NARRATION):
        clip = voices.synth(vc, text, pitch)
        s = int((acc + delay) * voices.SR)
        e = min(total, s + len(clip))
        buf[s:e] += clip[:e - s]
        print(f"  [{vc}] @{acc + delay:5.1f}s {len(clip)/voices.SR:4.1f}s  {text[:34]}")
        acc += dur
    pcm = (np.clip(buf, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(voices.SR)
        wf.writeframes(pcm.tobytes())


def frame_at(t):
    acc = 0.0
    for dur, fn in SCENES:
        if acc <= t < acc + dur:
            return fn(t - acc, dur)
        acc += dur
    return SCENES[-1][1](SCENES[-1][0] - 1e-3, SCENES[-1][0])


def main():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(DURATION * FPS)
    print(f"story: {DURATION:.1f}s, {n} frames")
    M.generate_music("musicS.wav", DURATION + 0.3)
    print("Synthesizing voices...")
    build_voice_track("voiceS.wav")
    amix = ("[1:a]volume=0.26,aresample=48000,aformat=channel_layouts=stereo[m];"
            "[2:a]volume=1.8,aresample=48000,aformat=channel_layouts=stereo[v];"
            "[m][v]amix=inputs=2:duration=first:normalize=0[a]")
    cmd = [
        ffmpeg, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", "musicS.wav", "-i", "voiceS.wav",
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
