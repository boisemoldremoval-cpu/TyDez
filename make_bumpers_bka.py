#!/usr/bin/env python3
"""
"Bible Kids Adventures" series bumpers with 7-year-old TyGuy (2D).
    intro_bka.mp4 (~4.5s)  /  outro_bka.mp4 (~5s)
"""
import math, wave, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import make_cartoon as M
import kid, voices

W, H, FPS = 1280, 720, 24
FONT = "/mnt/skills/examples/canvas-design/canvas-fonts/EricaOne-Regular.ttf"
GROUND = int(H * 0.96)


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eob(t):
    t = clamp(t); c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def jump(p, h): return -math.sin(math.pi * clamp(p)) * h


def outlined(d, xy, text, font, fill, ow=6, outline=(25, 18, 8)):
    x, y = xy
    for dx in range(-ow, ow + 1, 2):
        for dy in range(-ow, ow + 1, 2):
            d.text((x + dx, y + dy), text, font=font, fill=outline, anchor="mm")
    d.text((x, y), text, font=font, fill=fill, anchor="mm")


def title_card(big=True):
    cw, ch = (900, 300) if big else (620, 210)
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, cw - 10, ch - 10], radius=36,
                        fill=(40, 120, 222, 235), outline=(255, 210, 45, 255), width=10)
    f1 = ImageFont.truetype(FONT, int(ch * 0.42)); f2 = ImageFont.truetype(FONT, int(ch * 0.30))
    outlined(d, (cw // 2, int(ch * 0.37)), "BIBLE KIDS", f1, (255, 214, 45), 7)
    outlined(d, (cw // 2, int(ch * 0.72)), "ADVENTURES", f2, (255, 255, 255), 7)
    return im


def render(name, dur, frame_fn, vc_text, pitch=1.25):
    ff = imageio_ffmpeg.get_ffmpeg_exe(); n = int(dur * FPS)
    M.generate_music(f"{name}_m.wav", dur + 0.2)
    clip = voices.synth("ty", vc_text, pitch)
    tot = int((dur + 0.3) * voices.SR); buf = np.zeros(tot, np.float32)
    s = int(0.5 * voices.SR); e = min(tot, s + len(clip)); buf[s:e] += clip[:e - s]
    pcm = (np.clip(buf, -1, 1) * 32767).astype("<i2")
    with wave.open(f"{name}_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(voices.SR); wf.writeframes(pcm.tobytes())
    amix = ("[1:a]volume=0.5,aresample=48000,aformat=channel_layouts=stereo[m];"
            "[2:a]volume=1.8,aresample=48000,aformat=channel_layouts=stereo[v];"
            "[m][v]amix=inputs=2:duration=first:normalize=0[a]")
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", f"{name}_m.wav", "-i", f"{name}_v.wav", "-filter_complex", amix,
           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-shortest",
           "-movflags", "+faststart", f"{name}.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(n):
        p.stdin.write(frame_fn(i / FPS, dur).tobytes())
    p.stdin.close(); p.wait(); print(f"  -> {name}.mp4")


def intro_frame(t, dur):
    img = M.starburst(t).convert("RGBA")
    p = clamp(t / 0.6); y_in = (1 - eob(p)) * 420
    hy = jump((t - 0.62) * 1.1 % 1, 30) if t >= 0.62 else 0
    wave_a = 40 + math.sin(t * 8) * 25
    kid.draw_kid(img, W * 0.5, GROUND + y_in + hy, 360, kid.KID_TYGUY,
                 {"arm_l": wave_a, "elbow": 14, "mouth": "bigsmile", "brow": "happy",
                  "blink": 1 if (t * 0.5) % 1 > 0.93 else 0})
    pop = eob(clamp((t - 0.5) / 0.5)); a = clamp((t - 0.5) / 0.3) * clamp((dur - t) / 0.4)
    card = title_card(True); s = 0.6 + 0.4 * pop
    cw, ch = int(card.width * s), int(card.height * s)
    c = card.resize((cw, ch), Image.LANCZOS)
    if a < 1: c.putalpha(c.split()[3].point(lambda q: int(q * a)))
    img.alpha_composite(c, ((W - cw) // 2, int(H * 0.06)))
    return img.convert("RGB")


def outro_frame(t, dur):
    img = M.starburst(t).convert("RGBA")
    hy = jump((t * 1.0) % 1, 22)
    kid.draw_kid(img, W * 0.5, GROUND + hy, 360, kid.KID_TYGUY,
                 {"arm_l": 70, "arm_r": 70, "elbow": 16, "mouth": "bigsmile",
                  "brow": "happy", "blink": 1 if (t * 0.5) % 1 > 0.93 else 0})
    a = clamp(min(t / 0.4, (dur - t) / 0.4))
    d = M.D(img)
    M.ctext(d, "Thanks for watching!", M.font(M.F_BOLD, 58), H * 0.14, (255, 255, 255), a)
    M.ctext(d, "Be kind. Have fun. Be you!", M.font(M.F_REG, 38), H * 0.24, (255, 210, 80), a)
    card = title_card(False); a2 = clamp((t - 0.4) / 0.4)
    img.alpha_composite(card, ((W - card.width) // 2, int(H * 0.74)))
    return img.convert("RGB")


def main():
    print("intro..."); render("intro_bka", 4.5, intro_frame, "Welcome to Bible Kids Adventures!")
    print("outro..."); render("outro_bka", 5.0, outro_frame,
                              "Thanks for watching! Be kind, have fun, and be you!")
    print("done")


if __name__ == "__main__":
    main()
