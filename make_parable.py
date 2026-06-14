#!/usr/bin/env python3
"""
"Bible Kids Adventures — The Good Samaritan" (2D, polished).
Kid TyGuy frames the parable (Luke 10) -> verse Mark 12:31. -> parable.mp4
Assemble: intro_bka + parable + outro_bka.
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
def blink(t, s=0): return 1 if (t * 0.5 + s) % 1 > 0.93 else 0


SCENES = []
def scene(dur, text=None):
    def deco(fn): SCENES.append((dur, fn, text)); return fn
    return deco


def desert(t): return bg2.desert_road(t).filter(ImageFilter.GaussianBlur(4))
def cinem(img, t, lt, dur):
    O.add_bokeh(img, t)
    return O.cinematic(img, t, lerp(1.05, 1.0, eo(lt / dur)), lerp(-8, 8, lt / dur), 0)


@scene(7.5, lambda d, t, dr: M.speech(d, W * 0.5, H * 0.18,
        "Here's a story Jesus told about loving your neighbor!",
        clamp((t - 0.4) / 0.3) * fade(t, dr, 0.4)))
def s_club_intro(t, dur):
    img = bg2.club_room(t).filter(ImageFilter.GaussianBlur(3))
    kid.draw_kid(img, W * 0.5, GC - bobf(t), 360, kid.KID_TYGUY,
                 {"arm_r": 44, "elbow": 16, "mouth": "bigsmile", "brow": "happy", "blink": blink(t)})
    return cinem(img, t, t, dur)


@scene(7.5, lambda d, t, dr: M.caption(d, "A man walked down a long, lonely road...", fade(t, dr)))
def s_traveler(t, dur):
    img = desert(t)
    x = lerp(W * 0.2, W * 0.6, eo(t / dur))
    F.draw_robed(img, x, GD, 300, F.TRAVELER, {"bob": bobf(t), "arm_l": 14, "arm_r": 14,
                                               "mouth": "smile", "blink": blink(t)})
    return cinem(img, t, t, dur)


@scene(7.5, lambda d, t, dr: M.caption(d, "But robbers hurt him and left him all alone.", fade(t, dr)))
def s_hurt(t, dur):
    img = desert(t)
    F.draw_hurt(img, W * 0.5, GD, 300, F.TRAVELER)
    return cinem(img, t, t, dur)


@scene(8.5, lambda d, t, dr: M.caption(d, "A priest came by, saw him, and walked right past.", fade(t, dr)))
def s_priest(t, dur):
    img = desert(t)
    F.draw_hurt(img, W * 0.34, GD, 290, F.TRAVELER)
    x = lerp(W * 1.15, W * 0.62, eo(clamp(t / (dur - 0.5))))
    F.draw_robed(img, x, GD, 300, F.PRIEST, {"bob": bobf(t, 1), "lean": 8,
                                             "arm_l": 12, "arm_r": 20, "brow": "normal", "blink": blink(t)})
    return cinem(img, t, t, dur)


@scene(8.5, lambda d, t, dr: M.caption(d, "A temple helper came by too... but he passed by as well.", fade(t, dr)))
def s_levite(t, dur):
    img = desert(t)
    F.draw_hurt(img, W * 0.34, GD, 290, F.TRAVELER)
    x = lerp(W * 1.15, W * 0.60, eo(clamp(t / (dur - 0.5))))
    F.draw_robed(img, x, GD, 300, F.LEVITE, {"bob": bobf(t, 2), "lean": 9,
                                             "arm_l": 18, "arm_r": 12, "brow": "normal", "blink": blink(t)})
    return cinem(img, t, t, dur)


@scene(10.5)
def s_samaritan(t, dur):
    img = desert(t)
    d = M.D(img)
    F.draw_hurt(img, W * 0.36, GD, 290, F.TRAVELER)
    # Samaritan walks in then kneels beside, reaching out
    if t < 2.5:
        x = lerp(W * 1.1, W * 0.56, eo(t / 2.5)); reach = 20
    else:
        x = W * 0.56; reach = 70 + math.sin((t - 2.5) * 3) * 8
    F.draw_robed(img, x, GD, 300, F.SAMARITAN, {"bob": bobf(t, 3) if t < 2.5 else 0,
                 "lean": 14 if t >= 2.5 else 0, "arm_l": reach, "elbow": 18,
                 "mouth": "smile", "brow": "kind", "blink": blink(t)})
    if t > 3.0:
        for i in range(4):
            hp = (t * 0.5 + i * 0.25) % 1
            M.heart(d, W * 0.45 + math.sin(i + t) * 50, lerp(H * 0.55, H * 0.2, hp), 13, a=clamp(1 - hp))
    img2 = cinem(img, t, t, dur)
    dd = M.D(img2.convert("RGBA"))
    if t > 2.8:
        M.speech(dd, W * 0.62, H * 0.20, "Don't worry, I've got you.",
                 clamp((t - 2.8) / 0.3) * fade(t, dur, 0.4))
    M.caption(dd, "But a Samaritan stopped to help.", fade(t, dur))
    return dd._image.convert("RGB")


@scene(8.5, lambda d, t, dr: M.caption(d, "He set him on his donkey and took him to an inn.", fade(t, dr)))
def s_to_inn(t, dur):
    img = desert(t)
    x = lerp(W * 0.18, W * 0.62, eo(t / dur))
    F.draw_donkey(img, x + 70, GD, 280)
    # rescued traveler riding (small lump on the donkey)
    d = M.D(img)
    F.draw_robed(img, x - 70, GD, 290, F.SAMARITAN, {"bob": bobf(t, 4), "arm_l": 12, "arm_r": 12,
                                                     "mouth": "smile", "brow": "kind", "blink": blink(t)})
    return cinem(img, t, t, dur)


@scene(9.0)
def s_inn(t, dur):
    img = bg2.inn(t).filter(ImageFilter.GaussianBlur(3))
    d = M.D(img)
    F.draw_robed(img, W * 0.38, GD, 300, F.SAMARITAN, {"bob": bobf(t), "arm_r": 50, "elbow": 16,
                 "mouth": "smile", "brow": "kind", "blink": blink(t)})
    F.draw_robed(img, W * 0.60, GD, 300, F.INNKEEPER, {"bob": bobf(t, 2), "arm_l": 40,
                 "mouth": "smile", "blink": blink(t, 1)})
    for i in range(3):                       # coins
        d.ellipse([W * 0.49 + i * 10, H * 0.55 - i * 6, W * 0.49 + i * 10 + 16, H * 0.55 - i * 6 + 16],
                  fill=(245, 205, 70), outline=(180, 140, 40), width=2)
    img2 = cinem(img, t, t, dur)
    dd = M.D(img2.convert("RGBA"))
    if t > 0.6:
        M.speech(dd, W * 0.38, H * 0.18, "Take care of him. I'll pay whatever it costs.",
                 clamp((t - 0.6) / 0.3) * fade(t, dur, 0.4))
    return dd._image.convert("RGB")


@scene(10.0)
def s_lesson(t, dur):
    img = bg2.club_room(t).filter(ImageFilter.GaussianBlur(3))
    kid.draw_kid(img, W * 0.5, GC - bobf(t), 360, kid.KID_TYGUY,
                 {"arm_l": 36, "elbow": 14, "mouth": "bigsmile", "brow": "happy", "blink": blink(t)})
    img2 = cinem(img, t, t, dur)
    dd = M.D(img2.convert("RGBA"))
    a1 = clamp(t / 0.4) * clamp((dur - t) / 0.4)
    if t < 5.0:
        M.speech(dd, W * 0.5, H * 0.16, "So who was the neighbor? The one who STOPPED to help!", a1)
    else:
        M.speech(dd, W * 0.5, H * 0.16, "Jesus said: go and do the same!", clamp((t - 5) / 0.3) * clamp((dur - t) / 0.4))
    return dd._image.convert("RGB")


@scene(9.0)
def s_verse(t, dur):
    img = M.starburst(t).convert("RGBA")
    d = M.D(img)
    a = fade(t, dur, 0.7)
    M._gold_cross(d, W * 0.5, H * 0.22, 44)
    M.ctext(d, "“Love your neighbor", M.font(M.F_SERIF, 64), H * 0.42, (255, 255, 255), clamp((t - 0.2) / 0.5))
    M.ctext(d, "as yourself.”", M.font(M.F_SERIF, 64), H * 0.54, (255, 255, 255), clamp((t - 0.6) / 0.5))
    M.ctext(d, "Mark 12:31", M.font(M.F_BOLD, 44), H * 0.70, (255, 210, 80), clamp((t - 1.1) / 0.5))
    return img.convert("RGB")


DURATION = sum(s[0] for s in SCENES)

# voices per scene: list of (voice, text, delay, pitch)
NAR = [
    [("ty", "Hey friends! Here's a story Jesus told about loving your neighbor.", 0.4, 1.28)],
    [("ty", "A man was walking down a long, lonely road.", 0.4, 1.0)],
    [("ty", "But robbers hurt him, and left him all alone.", 0.4, 1.0)],
    [("ty", "A priest came by. He saw the hurt man, and walked right past.", 0.4, 1.0)],
    [("ty", "A temple helper came by too, but he passed by as well.", 0.4, 1.0)],
    [("ty", "But then a Samaritan stopped to help.", 0.3, 1.0),
     ("ty", "Don't worry, I've got you.", 3.0, 0.85)],
    [("ty", "He set the man on his donkey, and took him to an inn to rest.", 0.4, 1.0)],
    [("ty", "He gave the innkeeper his own money.", 0.3, 1.0),
     ("ty", "Take care of him. I'll pay whatever it costs.", 3.0, 0.85)],
    [("ty", "So who was the neighbor? The one who stopped to help!", 0.4, 1.28),
     ("ty", "Jesus said: go, and do the same.", 5.2, 1.28)],
    [("ty", "Love your neighbor as yourself. Mark twelve, thirty one.", 0.5, 1.0)],
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
    print(f"parable: {DURATION:.0f}s {n} frames"); M.generate_music("musicP.wav", DURATION + 0.3)
    print("voices..."); build_voice("voiceP.wav")
    amix = ("[1:a]volume=0.24,aresample=48000,aformat=channel_layouts=stereo[m];"
            "[2:a]volume=1.8,aresample=48000,aformat=channel_layouts=stereo[v];"
            "[m][v]amix=inputs=2:duration=first:normalize=0[a]")
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", "musicP.wav", "-i", "voiceP.wav", "-filter_complex", amix,
           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-shortest",
           "-movflags", "+faststart", "parable.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(n):
        p.stdin.write(frame_at(i / FPS).tobytes())
        if i % 48 == 0: print(f"  {i}/{n}")
    p.stdin.close(); p.wait(); print("Done -> parable.mp4")


if __name__ == "__main__":
    main()
