#!/usr/bin/env python3
"""
Assemble the final TyGuy film:
  intro (uploaded) -> 3D story (PNG seq + caption/speech/heart overlays + music)
  -> Bible verse card -> outro (uploaded).

Reuses the 2D overlay/music helpers from make_cartoon (1280x720) and the
shared story TIMELINE from make_film_3d. Produces tyguy_film.mp4.
"""

import os
import glob
import math
import subprocess

from PIL import Image
import imageio_ffmpeg

import make_cartoon as M          # 2D helpers @1280x720: starburst, caption, speech, heart, fonts, music
import make_film_3d as F          # TIMELINE, beat_at, FPS, DURATION

W, H = 1280, 720
FPS = 24
SEQ_DIR = "/tmp/seq3d"

INTRO = "/root/.claude/uploads/ff8cfb28-4e13-5a8d-82f5-0d89c1f5c66e/aedae882-gemini_generated_video_0B5B250C.mp4"
OUTRO = "/root/.claude/uploads/ff8cfb28-4e13-5a8d-82f5-0d89c1f5c66e/87539884-gemini_generated_video_7CC21B3D.mp4"
VERSE_DUR = 7.0
OUT = "tyguy_film.mp4"


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


# --------------------------------------------------------------------------- #
# overlays on a rendered 3D frame
# --------------------------------------------------------------------------- #
def overlay(img3d, t):
    img = img3d.convert("RGBA").resize((W, H), Image.LANCZOS)
    d = M.D(img)
    name, lt, dur = F.beat_at(t)
    info = F.TIMELINE.get(name, {})
    a = clamp(min(lt / 0.5, (dur - lt) / 0.5))

    # opening title over the first beat
    if name == "establish":
        ta = clamp(min(lt / 0.6, (dur - lt) / 0.6))
        M.ctext(d, "The Kindness Choice", M.font(M.F_TITLE, 78),
                H * 0.13, (255, 255, 255), ta)
        M.ctext(d, "a TyGuy story", M.font(M.F_REG, 30),
                H * 0.20, (255, 220, 120), ta, track=4)

    # speech bubble
    if "speech" in info:
        txt, s, e = info["speech"]
        if s <= lt < e:
            sa = clamp(min((lt - s) / 0.3, (e - lt) / 0.3))
            M.speech(d, W * 0.34, H * 0.40, txt, sa)

    # rising hearts
    if "hearts" in info:
        s, e = info["hearts"]
        if s <= lt < e:
            for i in range(5):
                hp = ((lt - s) * 0.5 + i * 0.23) % 1.0
                hx = W * 0.52 + math.sin(i * 2 + lt) * 70
                hy = M.lerp(H * 0.62, H * 0.28, hp)
                M.heart(d, hx, hy, 18 * (1 - hp * 0.4), a=clamp(1 - hp) * a)

    # caption banner
    if "cap" in info:
        M.caption(d, info["cap"], a)
    return img.convert("RGB")


# --------------------------------------------------------------------------- #
# Bible verse card
# --------------------------------------------------------------------------- #
def verse_frame(t, dur):
    img = M.starburst(t)
    d = M.D(img)
    a = clamp(min(t / 0.8, (dur - t) / 0.8))
    M._gold_cross(d, W / 2, H * 0.16, 42)
    M.ctext(d, "“Be kind to one another, tender-hearted,",
            M.font(M.F_SERIF, 46), H * 0.38, (255, 255, 255), a)
    M.ctext(d, "forgiving one another.”",
            M.font(M.F_SERIF, 46), H * 0.47, (255, 255, 255), a)
    M.ctext(d, "Ephesians 4:32", M.font(M.F_BOLD, 38),
            H * 0.60, (255, 210, 80), a)
    M.ctext(d, "“Love your neighbor as yourself.”  — Mark 12:31",
            M.font(M.F_REG, 30), H * 0.74, (200, 222, 255), a)
    return img.convert("RGB")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    frames = sorted(glob.glob(f"{SEQ_DIR}/*.png"))
    if not frames:
        raise SystemExit(f"No frames in {SEQ_DIR}; run make_film_3d.py all first.")
    n_story = len(frames)
    n_verse = int(VERSE_DUR * FPS)
    total = (n_story + n_verse) / FPS
    print(f"{n_story} story frames + {n_verse} verse frames = {total:.1f}s")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    print("Generating music bed...")
    M.generate_music("music_film.wav", total + 0.3)

    # ---- render the middle (story + verse) to lesson.mp4 with music ----
    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", "music_film.wav",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart", "lesson.mp4",
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i, f in enumerate(frames):
        fr = overlay(Image.open(f), i / FPS)
        proc.stdin.write(fr.tobytes())
        if i % 48 == 0:
            print(f"  overlay {i}/{n_story}")
    for i in range(n_verse):
        proc.stdin.write(verse_frame(i / FPS, VERSE_DUR).tobytes())
    proc.stdin.close()
    proc.wait()
    print("lesson.mp4 done")

    # ---- concat intro + lesson + outro (normalize to 1280x720/24fps/48k stereo) ----
    fc = (
        "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24[v0];"
        "[1:v]scale=1280:720,setsar=1,fps=24[v1];"
        "[2:v]scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24[v2];"
        "[0:a]aresample=48000,aformat=channel_layouts=stereo[a0];"
        "[1:a]aresample=48000,aformat=channel_layouts=stereo[a1];"
        "[2:a]aresample=48000,aformat=channel_layouts=stereo[a2];"
        "[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]"
    )
    cmd2 = [
        ffmpeg, "-y", "-i", INTRO, "-i", "lesson.mp4", "-i", OUTRO,
        "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT,
    ]
    print("Concatenating intro + story + outro...")
    r = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode()[-2000:])
        raise SystemExit("concat failed")
    print(f"Done -> {OUT}")


if __name__ == "__main__":
    main()
