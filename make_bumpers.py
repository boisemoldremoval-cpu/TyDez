#!/usr/bin/env python3
"""
Reusable "TyGuy's Bible Club" series intro & outro bumpers (2D, branded).

Built from TyGuy's art + branded starburst, with a voiced tag and music sting.
Drop these on the front/back of every episode:
    intro_series.mp4   (~5s)
    outro_series.mp4   (~6s)

    python3 make_bumpers.py
"""

import math
import wave
import subprocess

import numpy as np
from PIL import Image
import imageio_ffmpeg

import make_cartoon as M
import make_tyguy2d as A
import voices

W, H, FPS = 1280, 720, 24
CUT = A.CUT
clamp, eo, ease_out_back = A.clamp, A.eo, A.ease_out_back


def render(name, dur, frame_fn, vc_text):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(dur * FPS)
    M.generate_music(f"{name}_m.wav", dur + 0.2)
    # voice
    clip = voices.synth("ty", vc_text, 1.0)
    total = int((dur + 0.3) * voices.SR)
    buf = np.zeros(total, np.float32)
    s = int(0.4 * voices.SR)
    e = min(total, s + len(clip))
    buf[s:e] += clip[:e - s]
    pcm = (np.clip(buf, -1, 1) * 32767).astype("<i2")
    with wave.open(f"{name}_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(voices.SR)
        wf.writeframes(pcm.tobytes())
    amix = ("[1:a]volume=0.5,aresample=48000,aformat=channel_layouts=stereo[m];"
            "[2:a]volume=1.8,aresample=48000,aformat=channel_layouts=stereo[v];"
            "[m][v]amix=inputs=2:duration=first:normalize=0[a]")
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", f"{name}_m.wav", "-i", f"{name}_v.wav",
           "-filter_complex", amix, "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
           "-shortest", "-movflags", "+faststart", f"{name}.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(n):
        p.stdin.write(frame_fn(i / FPS, dur).tobytes())
    p.stdin.close(); p.wait()
    print(f"  -> {name}.mp4")


def intro_frame(t, dur):
    img = M.starburst(t).convert("RGBA")
    d = M.D(img)
    # TyGuy leaps in + settles, thumbs up
    p = clamp(t / 0.5)
    y_in = (1 - ease_out_back(p)) * 460
    sx, sy = A.land_squash(t / 0.5) if t < 0.52 else (1, 1)
    hy = A.hop_cycle(t - 0.52, 1.1, 26)[0] if t >= 0.52 else 0
    A.draw_cut(img, CUT["full"], W * 0.30, H * 0.99 + y_in + hy, 470,
               alpha=clamp(t / 0.15), sx_mul=sx, sy_mul=sy)
    # title pops in
    pop = ease_out_back(clamp((t - 0.5) / 0.5))
    a = clamp((t - 0.5) / 0.3) * clamp((dur - t) / 0.4)
    M.ctext(d, "TyGuy's", M.font(M.F_TITLE, int(110 * (0.6 + 0.4 * pop))),
            H * 0.34, (255, 255, 255), a, cx=W * 0.66)
    M.ctext(d, "BIBLE CLUB", M.font(M.F_TITLE, int(120 * (0.6 + 0.4 * pop))),
            H * 0.55, (255, 210, 80), a, cx=W * 0.66)
    if 0.6 < t < 1.4:
        A.burst(d, W * 0.66, H * 0.45, clamp((t - 0.6) / 0.8), 1.0)
    return img.convert("RGB")


def outro_frame(t, dur):
    img = M.starburst(t).convert("RGBA")
    d = M.D(img)
    bob, sway, bsx, bsy = A.idle(t, amp=10)
    A.draw_cut(img, CUT["cheer"], W * 0.5, H * 0.99 + A.hop_cycle(t, 1.0, 22)[0],
               460, alpha=clamp(t / 0.2), sx_mul=bsx, sy_mul=bsy)
    a = clamp(min(t / 0.4, (dur - t) / 0.4))
    M.ctext(d, "Thanks for watching!", M.font(M.F_BOLD, 60), H * 0.16,
            (255, 255, 255), a)
    M.ctext(d, "Be kind. Have fun. Be you!", M.font(M.F_REG, 40), H * 0.27,
            (255, 210, 80), a)
    return img.convert("RGB")


def main():
    print("Rendering series intro...")
    render("intro_series", 5.0, intro_frame, "TyGuy's Bible Club!")
    print("Rendering series outro...")
    render("outro_series", 6.0, outro_frame,
           "Thanks for watching! Remember to love your neighbor. See you next time at Bible Club!")
    print("Done.")


if __name__ == "__main__":
    main()
