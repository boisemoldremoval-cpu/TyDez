#!/usr/bin/env python3
"""
Assemble the final TyGuy film from Veo-generated 3D shots.

Splices: your intro -> shot1..shotN -> your outro, normalizing every clip to a
common size/fps with a blurred-fill background (so 16:9 and 9:16 sources both
fit cleanly), and keeping each clip's native (Veo) audio.

    python3 assemble_3d.py shot1.mp4 shot2.mp4 ...            # 16:9  -> tyguy_3d.mp4
    python3 assemble_3d.py --vertical shot1.mp4 ...           # 9:16  -> tyguy_3d_9x16.mp4
    python3 assemble_3d.py --out movie.mp4 shotA.mp4 shotB.mp4

Notes:
- Assumes each shot has an audio track (Veo 3 clips do). If you generated silent
  "plates" instead, tell me and I'll add the TTS voices + music bed instead.
"""

import sys
import subprocess
import imageio_ffmpeg

INTRO = "/root/.claude/uploads/ff8cfb28-4e13-5a8d-82f5-0d89c1f5c66e/aedae882-gemini_generated_video_0B5B250C.mp4"
OUTRO = "/root/.claude/uploads/ff8cfb28-4e13-5a8d-82f5-0d89c1f5c66e/87539884-gemini_generated_video_7CC21B3D.mp4"


def main():
    args = sys.argv[1:]
    vertical = "--vertical" in args
    bookends = "--bookends" in args          # include intro/outro (off by default)
    args = [a for a in args if a not in ("--vertical", "--bookends")]
    xfade = 0.0
    if "--xfade" in args:                     # crossfade seconds between clips
        i = args.index("--xfade")
        xfade = float(args[i + 1])
        del args[i:i + 2]
    out = "tyguy_3d_9x16.mp4" if vertical else "tyguy_3d.mp4"
    if "--out" in args:
        i = args.index("--out")
        out = args[i + 1]
        del args[i:i + 2]
    shots = args
    if not shots:
        print("usage: assemble_3d.py [--vertical] [--bookends] [--out FILE] shot1.mp4 ...")
        raise SystemExit(1)

    Wt, Ht = (1080, 1920) if vertical else (1280, 720)
    # default: just the shots, no intro/outro
    inputs = ([INTRO] + shots + [OUTRO]) if bookends else list(shots)

    parts, concat = [], ""
    for i in range(len(inputs)):
        parts.append(
            f"[{i}:v]split=2[bg{i}][fg{i}];"
            f"[bg{i}]scale={Wt}:{Ht}:force_original_aspect_ratio=increase,"
            f"crop={Wt}:{Ht},gblur=sigma=24[bgb{i}];"
            f"[fg{i}]scale={Wt}:{Ht}:force_original_aspect_ratio=decrease[fg{i}s];"
            f"[bgb{i}][fg{i}s]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=24[v{i}];"
            f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}];"
        )
        concat += f"[v{i}][a{i}]"
    fc = "".join(parts) + f"{concat}concat=n={len(inputs)}:v=1:a=1[v][a]"

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y"]
    for f in inputs:
        cmd += ["-i", f]
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    print(f"Assembling {len(shots)} shots -> {out} ({Wt}x{Ht})")
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode()[-2000:])
        raise SystemExit("assembly failed")
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
