#!/usr/bin/env python3
"""
2D TyGuy Biblical-moral cartoon using the real artwork cutouts (assets/cut_*.png).

TyGuy hosts a lesson on kindness, animated puppet-style with a lively motion
vocabulary: jump-in entrances with squash & stretch, hops, scale-punch
emphasis, pose-swaps timed to the dialogue, spins, motion lines and confetti.

    python3 make_tyguy2d.py            # -> cartoon2d.mp4
Run build_film2d.py afterwards to splice intro + cartoon2d + outro.
"""

import math
import wave
import subprocess

import numpy as np
from PIL import Image, ImageDraw
import imageio_ffmpeg

import make_cartoon as M     # shared 2D helpers @1280x720

W, H = 1280, 720
FPS = 24
OUT = "cartoon2d.mp4"

CUT = {n: Image.open(f"assets/cut_{n}.png").convert("RGBA")
       for n in ["full", "point", "sun", "think", "cheer"]}


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def eo(t):
    return 1 - (1 - clamp(t)) ** 3


def ei(t):
    return clamp(t) ** 3


def ease_out_back(t):
    t = clamp(t)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


# --------------------------------------------------------------------------- #
# motion primitives
# --------------------------------------------------------------------------- #
def jump_arc(p, height):
    return -math.sin(math.pi * clamp(p)) * height


def land_squash(p, k=0.20):
    """Squash/stretch near takeoff & landing of a 0..1 jump phase."""
    if p < 0 or p > 1:
        return 1.0, 1.0
    e = max(0.0, 1 - min(p, 1 - p) / 0.14)
    return 1 + e * k, 1 - e * k


def hop_cycle(t, rate=1.0, height=42):
    ph = (t * rate) % 1.0
    sx, sy = land_squash(ph)
    return jump_arc(ph, height), sx, sy


def punch(t, t0, mag=0.14, w=0.20):
    dt = t - t0
    return 1 + mag * math.sin(math.pi * dt / w) if 0 <= dt < w else 1.0


def idle(t, seed=0.0, amp=10.0):
    bob = math.sin(t * 2.0 + seed) * amp
    sway = math.sin(t * 1.3 + seed) * 1.6
    br = math.sin(t * 2.0 + seed)
    return bob, sway, 1 - br * 0.012, 1 + br * 0.012


# --------------------------------------------------------------------------- #
# fx
# --------------------------------------------------------------------------- #
def draw_cut(img, cut, cx, baseline, target_h, rot=0.0, alpha=1.0,
             sx_mul=1.0, sy_mul=1.0, shadow=True):
    scale = target_h / cut.height
    w = max(1, int(cut.width * scale * sx_mul))
    h = max(1, int(cut.height * scale * sy_mul))
    c = cut.resize((w, h), Image.LANCZOS)
    if abs(rot) > 0.01:
        c = c.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1.0:
        c.putalpha(c.getchannel("A").point(lambda p: int(p * alpha)))
    if shadow:
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dd = ImageDraw.Draw(ov)
        lift = clamp((baseline - (H * 0.99)) / -120)  # smaller shadow when airborne
        sw = int(w * 0.5 * (0.7 + 0.3 * (1 - lift)))
        sy = H * 0.99
        dd.ellipse([cx - sw, sy - 18, cx + sw, sy + 18],
                   fill=(0, 0, 0, int(60 * alpha * (0.6 + 0.4 * (1 - lift)))))
        img.alpha_composite(ov)
    img.alpha_composite(c, (int(cx - c.width / 2), int(baseline - c.height)))


def spark(d, x, y, r, col, a):
    al = int(clamp(a) * 255)
    d.line([(x - r, y), (x + r, y)], fill=(*col, al), width=max(2, r // 4))
    d.line([(x, y - r), (x, y + r)], fill=(*col, al), width=max(2, r // 4))


def burst(d, cx, cy, p, a, n=12, col=(255, 210, 80)):
    """Expanding star burst, p in 0..1."""
    R = M.lerp(20, 230, eo(p))
    for i in range(n):
        ang = i / n * math.tau + p
        x = cx + math.cos(ang) * R
        y = cy + math.sin(ang) * R
        spark(d, x, y, int(14 * (1 - p) + 4), col, (1 - p) * a)


def motion_lines(d, cx, cy, direction, a, col=(255, 255, 255)):
    al = int(clamp(a) * 110)
    for i in range(4):
        oy = cy - 60 + i * 40
        x0 = cx - direction * 70
        x1 = cx - direction * 200
        d.line([(x0, oy), (x1, oy)], fill=(*col, al), width=5)


def confetti(d, t, a):
    import random
    rng = random.Random(7)
    for _ in range(40):
        x0 = rng.uniform(0, W)
        spd = rng.uniform(120, 260)
        ph = (t * spd / H + rng.random()) % 1.0
        y = ph * H
        x = x0 + math.sin(t * 2 + x0) * 20
        col = rng.choice([(255, 210, 80), (255, 255, 255), (120, 200, 255), (255, 130, 150)])
        s = rng.uniform(5, 11)
        if rng.random() < 0.5:
            M._gold_cross(d, x, y, s, col=col)
        else:
            d.ellipse([x - s, y - s, x + s, y + s], fill=(*col, int(200 * a)))


# --------------------------------------------------------------------------- #
# scenes
# --------------------------------------------------------------------------- #
SCENES = []


def scene(dur):
    def deco(fn):
        SCENES.append((dur, fn))
        return fn
    return deco


def bg(t):
    return M.starburst(t).convert("RGBA")


BASE = H * 0.99
FULL_H = 480


@scene(4.2)
def s_intro(t, dur):
    img = bg(t)
    d = M.D(img)
    # jump up into frame from below, overshoot, land + settle
    p = clamp(t / 0.6)
    y_in = (1 - ease_out_back(p)) * 460
    sx, sy = land_squash(t / 0.6) if t < 0.62 else (1, 1)
    if t >= 0.62:                      # happy hops after landing
        hy, hsx, hsy = hop_cycle(t - 0.62, rate=1.1, height=34)
        sx, sy = hsx, hsy
    else:
        hy = 0
    a = clamp(t / 0.2)
    if t < 0.6:
        motion_lines(d, W * 0.5, H * 0.5, 0.0, 1 - p)
    draw_cut(img, CUT["full"], W * 0.5, BASE + y_in + hy, FULL_H,
             alpha=a, sx_mul=sx, sy_mul=sy)
    if t > 0.7:
        M.speech(d, W * 0.5, H * 0.12, "Hey friends! It's TyGuy!",
                 clamp((t - 0.7) / 0.3) * clamp((dur - t) / 0.4))
    return img.convert("RGB")


@scene(4.6)
def s_topic(t, dur):
    img = bg(t)
    d = M.D(img)
    # slide in from the left
    x = M.lerp(-320, W * 0.6, eo(clamp(t / 0.5)))
    if t < 0.5:
        motion_lines(d, x, H * 0.6, 1.0, 1 - t / 0.5)
    # on "KIND!" -> big hop + punch + star burst, swap to cheer pose
    kick = 1.5
    hop_y = jump_arc(clamp((t - kick) / 0.5), 90) if kick <= t < kick + 0.5 else 0
    pose = "cheer" if kick - 0.05 <= t < kick + 0.6 else "point"
    pu = punch(t, kick, mag=0.16, w=0.4)
    bob, sway, bsx, bsy = idle(t, seed=1, amp=8)
    draw_cut(img, CUT[pose], x, BASE + hop_y, 500 * pu,
             rot=sway, alpha=clamp(t / 0.2), sx_mul=bsx, sy_mul=bsy)
    if kick <= t < kick + 0.7:
        burst(d, x, H * 0.4, clamp((t - kick) / 0.7), 1.0)
    M.caption(d, "Today, let's talk about something important...",
              clamp(min(t / 0.4, (dur - t) / 0.4)))
    if t > 1.0:
        M.speech(d, W * 0.28, H * 0.30, "Being KIND!",
                 clamp((t - 1.0) / 0.3) * clamp((dur - t) / 0.4))
    return img.convert("RGB")


@scene(5.0)
def s_question(t, dur):
    img = bg(t)
    d = M.D(img)
    a = clamp(min(t / 0.3, (dur - t) / 0.4))
    # slow zoom-in + thoughtful sway/tilt
    zoom = M.lerp(520, 600, eo(clamp(t / dur)))
    sway = math.sin(t * 1.1) * 4
    xoff = math.sin(t * 0.9) * 40
    bob = math.sin(t * 1.8) * 6
    draw_cut(img, CUT["think"], W * 0.40 + xoff, BASE - bob, zoom,
             rot=sway, alpha=clamp(t / 0.25))
    for i in range(3):                 # floating question marks
        qp = (t * 0.45 + i * 0.3) % 1.0
        qx = W * 0.58 + i * 64
        qy = M.lerp(H * 0.55, H * 0.18, qp)
        M.ctext(d, "?", M.font(M.F_BOLD, int(76 - i * 12)), qy,
                (255, 210, 80), clamp(1 - qp) * a, cx=qx)
    M.caption(d, "Ever notice someone sitting all alone, feeling left out?", a)
    return img.convert("RGB")


@scene(4.4)
def s_teach(t, dur):
    img = bg(t)
    d = M.D(img)
    # authoritative nod + gentle scale pulse on "love"
    nod = abs(math.sin(t * 2.2)) * 14
    pu = punch(t, 1.4, mag=0.10, w=0.5)
    draw_cut(img, CUT["full"], W * 0.5, BASE - nod * 0.4, FULL_H * pu,
             alpha=clamp(t / 0.25))
    if t > 0.5:
        M.speech(d, W * 0.5, H * 0.12, "The Bible says: love your neighbor!",
                 clamp((t - 0.5) / 0.3) * clamp((dur - t) / 0.4))
    return img.convert("RGB")


@scene(7.0)
def s_verse(t, dur):
    img = bg(t)
    d = M.D(img)
    a = clamp(min(t / 0.7, (dur - t) / 0.7))
    M._gold_cross(d, W * 0.30, H * 0.20, 40)
    # lines slide/fade in one by one
    la = clamp((t - 0.2) / 0.5)
    M.ctext(d, "“Be kind to one another,", M.font(M.F_SERIF, 44),
            H * 0.34, (255, 255, 255), la, cx=W * 0.42)
    M.ctext(d, "tender-hearted, forgiving one another.”",
            M.font(M.F_SERIF, 44), H * 0.43, (255, 255, 255), clamp((t - 0.6) / 0.5), cx=W * 0.42)
    M.ctext(d, "Ephesians 4:32", M.font(M.F_BOLD, 36),
            H * 0.55, (255, 210, 80), clamp((t - 1.1) / 0.5), cx=W * 0.42)
    M.ctext(d, "“Love your neighbor as yourself.” — Mark 12:31",
            M.font(M.F_REG, 26), H * 0.66, (200, 222, 255), clamp((t - 1.5) / 0.5), cx=W * 0.42)
    hy, hsx, hsy = hop_cycle(t, rate=0.8, height=24)
    draw_cut(img, CUT["cheer"], W * 0.86, BASE + hy, 420 * eo(clamp(t / 0.5)),
             alpha=a, sx_mul=hsx, sy_mul=hsy, shadow=False)
    return img.convert("RGB")


@scene(4.6)
def s_apply(t, dur):
    img = bg(t)
    d = M.D(img)
    confetti(d, t, clamp(min(t / 0.4, (dur - t) / 0.4)))
    # hop energetically across from left to right
    x = M.lerp(W * 0.22, W * 0.78, eo(clamp(t / (dur - 0.4))))
    hy, hsx, hsy = hop_cycle(t, rate=1.6, height=70)
    draw_cut(img, CUT["cheer"], x, BASE + hy, 500, sx_mul=hsx, sy_mul=hsy,
             alpha=clamp(t / 0.2))
    M.caption(d, "So go say hi. Share a smile. Invite them in!",
              clamp(min(t / 0.4, (dur - t) / 0.4)))
    return img.convert("RGB")


@scene(4.8)
def s_outro(t, dur):
    img = bg(t)
    d = M.D(img)
    # leap to center, land, then a quick celebratory spin + star burst
    p = clamp(t / 0.5)
    y_in = (1 - ease_out_back(p)) * 420
    spin = 0.0
    sx, sy = land_squash(t / 0.5) if t < 0.52 else (1, 1)
    spin_t0 = 2.4
    if spin_t0 <= t < spin_t0 + 0.6:
        spin = -360 * eo((t - spin_t0) / 0.6)
        burst(d, W * 0.5, H * 0.5, clamp((t - spin_t0) / 0.6), 1.0, col=(255, 255, 255))
    if t >= 0.52 and not (spin_t0 <= t < spin_t0 + 0.6):
        hy, sx, sy = hop_cycle(t - 0.52, rate=1.0, height=26)
    else:
        hy = 0
    draw_cut(img, CUT["full"], W * 0.5, BASE + y_in + hy, FULL_H,
             rot=spin, alpha=clamp(t / 0.2), sx_mul=sx, sy_mul=sy)
    pulse = 1 + 0.05 * math.sin(t * 5)
    M.ctext(d, "Be kind. Have fun. Be you!",
            M.font(M.F_BOLD, int(58 * pulse)),
            H * 0.12, (255, 255, 255), clamp(min(t / 0.4, (dur - t) / 0.4)))
    return img.convert("RGB")


DURATION = sum(s[0] for s in SCENES)

# TyGuy's spoken lines, aligned to SCENES order; (text, delay-after-scene-start)
NARRATION = [
    ("Hey friends! It's TyGuy!", 0.7),
    ("Today, let's talk about something really important. Being kind!", 0.4),
    ("Have you ever seen someone sitting all alone, feeling left out?", 0.4),
    ("Well, the Bible tells us to love our neighbor.", 0.5),
    ("Be kind to one another, tender hearted, forgiving one another. "
     "Ephesians four, verse thirty two.", 0.5),
    ("So go say hi! Share a smile! Invite them in!", 0.4),
    ("Remember. Be kind, have fun, and be you! See you next time!", 0.4),
]
VOICE_SR = 22050


def build_voice_track(path):
    """Synthesize TyGuy's lines with Piper and lay them on one timeline."""
    from piper import PiperVoice
    v = PiperVoice.load("voices/en-us-ryan-high.onnx",
                        config_path="voices/en-us-ryan-high.onnx.json")

    def synth(text):
        frames = []
        for ch in v.synthesize(text):
            b = getattr(ch, "audio_int16_bytes", None)
            if b is None:
                arr = getattr(ch, "audio_int16_array", None)
                b = arr.tobytes() if arr is not None else \
                    (np.clip(ch.audio_float_array, -1, 1) * 32767).astype("<i2").tobytes()
            frames.append(b)
        return np.frombuffer(b"".join(frames), dtype="<i2").astype(np.float32) / 32768.0

    total = int((DURATION + 1.0) * VOICE_SR)
    buf = np.zeros(total, np.float32)
    acc = 0.0
    for (dur, _fn), (text, delay) in zip(SCENES, NARRATION):
        clip = synth(text)
        start = int((acc + delay) * VOICE_SR)
        end = min(total, start + len(clip))
        buf[start:end] += clip[:end - start]
        print(f"  voice @ {acc + delay:5.1f}s  {len(clip)/VOICE_SR:4.1f}s  {text[:38]}...")
        acc += dur
    pcm = (np.clip(buf, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(VOICE_SR)
        wf.writeframes(pcm.tobytes())


def frame_at(t):
    acc = 0.0
    for dur, fn in SCENES:
        if acc <= t < acc + dur:
            return fn(t - acc, dur)
        acc += dur
    return SCENES[-1][1](SCENES[-1][0], SCENES[-1][0])


def main():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(DURATION * FPS)
    print(f"2D cartoon: {DURATION:.1f}s, {n} frames")
    M.generate_music("music2d.wav", DURATION + 0.3)
    print("Synthesizing TyGuy's voice...")
    build_voice_track("voice2d.wav")
    # mix: music ducked under the voiceover
    amix = ("[1:a]volume=0.30,aresample=48000,aformat=channel_layouts=stereo[m];"
            "[2:a]volume=1.7,aresample=48000,aformat=channel_layouts=stereo[v];"
            "[m][v]amix=inputs=2:duration=first:normalize=0[a]")
    cmd = [
        ffmpeg, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", "music2d.wav", "-i", "voice2d.wav",
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
