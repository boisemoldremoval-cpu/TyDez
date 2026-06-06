#!/usr/bin/env python3
"""
Splice the uploaded intro + 2D TyGuy cartoon + uploaded outro into the final
film: tyguy_film_2d.mp4 (1280x720, 24fps, stereo).

Run make_tyguy2d.py first to produce cartoon2d.mp4.
"""
import subprocess
import imageio_ffmpeg

INTRO = "/root/.claude/uploads/ff8cfb28-4e13-5a8d-82f5-0d89c1f5c66e/aedae882-gemini_generated_video_0B5B250C.mp4"
OUTRO = "/root/.claude/uploads/ff8cfb28-4e13-5a8d-82f5-0d89c1f5c66e/87539884-gemini_generated_video_7CC21B3D.mp4"
MID = "cartoon2d.mp4"
OUT = "tyguy_film_2d.mp4"

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


def main():
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ff, "-y", "-i", INTRO, "-i", MID, "-i", OUTRO,
        "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT,
    ]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode()[-2000:])
        raise SystemExit("concat failed")
    print(f"Done -> {OUT}")


if __name__ == "__main__":
    main()
