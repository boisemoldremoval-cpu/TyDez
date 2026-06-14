#!/usr/bin/env python3
"""
Tie multiple clips into one continuous video.

    python3 tie_together.py a.mp4 b.mp4 c.mp4 --out final.mp4

Defaults match the request: 0.5s crossfade dissolves between clips, every
clip's original audio preserved and crossfaded, PLUS one continuous
synthesized music bed mixed underneath the whole thing, loudness-normalized.

Options:
    --xdur 0.5        crossfade duration (seconds)
    --transition fade xfade type: fade | fadeblack | fadewhite | dissolve | wipeleft ...
    --music track.mp3 use your own bed instead of the synthesized one
    --no-music        keep only the clips' original audio
    --bed-vol 0.5     music bed level under the ambient audio
    --out final.mp4   output path
    --size 1280x720   force canvas size (default: first clip's size)
    --fps 24          force fps (default: first clip's fps)

Differing resolutions/aspect ratios are letterboxed (scale + pad) to a common
canvas; differing fps are conformed. Clips with no audio get silent fill so
the crossfades stay in sync.
"""

import os
import re
import sys
import subprocess

import imageio_ffmpeg

# reuse the music-bed synth from add_music.py
from add_music import (synth_bed, synth_hardcore, synth_grunge,
                        synth_industrial, write_wav)

FF = imageio_ffmpeg.get_ffmpeg_exe()


def probe(path):
    out = subprocess.run([FF, "-i", path], stderr=subprocess.PIPE).stderr.decode()
    dur = 0.0
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    if m:
        h, mn, s = m.groups()
        dur = int(h) * 3600 + int(mn) * 60 + float(s)
    w, h = 1280, 720
    m = re.search(r", (\d{2,5})x(\d{2,5})", out)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
    fps = 24.0
    m = re.search(r"(\d+(?:\.\d+)?) fps", out)
    if m:
        fps = float(m.group(1))
    has_audio = "Audio:" in out
    return dur, w, h, fps, has_audio


def main():
    args = sys.argv[1:]

    def take(flag, default=None):
        if flag in args:
            i = args.index(flag)
            val = args[i + 1]
            del args[i:i + 2]
            return val
        return default

    out = take("--out", "final.mp4")
    xdur = float(take("--xdur", "0.5"))
    transition = take("--transition", "fade")
    music = take("--music", None)
    bed_vol = float(take("--bed-vol", "0.5"))
    size = take("--size", None)
    fps_override = take("--fps", None)
    intro = take("--intro", None)            # PNG/JPG or MP4 prepended at the start
    intro_dur = float(take("--intro-dur", "3.0"))
    endcard = take("--endcard", None)        # PNG/JPG or MP4 appended at the end
    endcard_dur = float(take("--endcard-dur", "3.5"))
    style = take("--style", "uplifting")     # uplifting | hardcore | grunge (synth bed)
    clip_start = float(take("--clip-start", "0"))   # in-point into each clip
    cl = take("--clip-len", None)                   # trim each clip to N seconds
    clip_len = float(cl) if cl else None
    pass_arg = take("--pass", None)                 # comma-list of pass-through scenes
    pass_set = set(pass_arg.split(",")) if pass_arg else set()
    no_music = "--no-music" in args
    if no_music:
        args.remove("--no-music")
    grade = "--grade" in args
    if grade:
        args.remove("--grade")

    files = args
    if not files:
        print("usage: tie_together.py clip1.mp4 clip2.mp4 ... [--out final.mp4]")
        raise SystemExit(1)

    IMG = (".png", ".jpg", ".jpeg")

    def add_card(path, card_dur, label):
        if not os.path.exists(path):
            raise SystemExit(f"missing {label}: {path}")
        if path.lower().endswith(IMG):
            return {"path": path, "image": True, "dur": card_dur,
                    "has_audio": False, "grade": False, "trim": None}
        m = probe(path)
        return {"path": path, "image": False, "dur": m[0],
                "has_audio": m[4], "grade": False, "trim": None}

    # Build the ordered segment list: [intro] + clips + [endcard].
    # Only real clips get trimmed/graded; intro & end card are passed through.
    segs = []
    if intro:
        segs.append(add_card(intro, intro_dur, "intro"))
    metas = []
    for f in files:
        if not os.path.exists(f):
            raise SystemExit(f"missing input: {f}")
        m = probe(f)
        metas.append(m)
        if f in pass_set:                      # designed scene: no trim/grade
            segs.append({"path": f, "image": f.lower().endswith(IMG),
                         "dur": m[0], "has_audio": m[4], "grade": False,
                         "trim": None})
            continue
        if clip_len:
            length = min(clip_len, max(0.5, m[0] - clip_start))
            trim = (clip_start, length)
        else:
            length, trim = m[0], None
        segs.append({"path": f, "image": False, "dur": length,
                     "has_audio": m[4], "grade": grade, "trim": trim})
    if endcard:
        segs.append(add_card(endcard, endcard_dur, "endcard"))

    n = len(segs)
    durs = [s["dur"] for s in segs]

    if size:
        W, H = (int(x) for x in size.lower().split("x"))
    else:
        W, H = metas[0][1], metas[0][2]
    FPS = float(fps_override) if fps_override else metas[0][3]

    total = durs[0] if n == 1 else sum(durs) - (n - 1) * xdur
    print(f"tying {len(files)} clips"
          f"{' +intro' if intro else ''}{' +endcard' if endcard else ''} -> {out}  "
          f"({W}x{H} @ {FPS}fps, ~{total:.1f}s, {transition} {xdur}s, "
          f"{style} bed{', graded' if grade else ''})")

    cmd = [FF, "-y"]
    for s in segs:  # video inputs occupy indices 0..n-1, in segment order
        if s["image"]:
            cmd += ["-loop", "1", "-t", f"{s['dur']:.3f}", "-i", s["path"]]
        else:
            cmd += ["-i", s["path"]]

    # silent fill for any segment without audio
    next_idx = n
    silent_idx = {}
    for i, s in enumerate(segs):
        if not s["has_audio"]:
            cmd += ["-f", "lavfi", "-t", f"{s['dur']:.3f}",
                    "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
            silent_idx[i] = next_idx
            next_idx += 1

    # music bed input (synth or provided)
    bed_idx = None
    if not no_music:
        bed_path = music
        if bed_path is None:
            bed_path = "/tmp/_tie_bed.wav"
            if style == "hardcore":
                bed = synth_hardcore(total)
            elif style == "grunge":
                bed = synth_grunge(total)
            elif style == "industrial":
                bed = synth_industrial(total)
            else:
                bed = synth_bed(total)
            write_wav(bed_path, bed)
            print(f"synthesized {style} bed -> {bed_path}")
        cmd += ["-i", bed_path]
        bed_idx = next_idx
        next_idx += 1

    fc = []
    # clean, punchy grade for a 'fresh & restored' look
    grade_f = ("eq=contrast=1.10:saturation=1.18:brightness=0.012:gamma=0.98,"
               "unsharp=5:5:0.5:5:5:0.0")
    # normalize video to common canvas/fps (+ optional trim/grade)
    for i, s in enumerate(segs):
        pre = ""
        if s["trim"]:
            cs, clen = s["trim"]
            pre = f"trim=start={cs:.3f}:end={cs + clen:.3f},setpts=PTS-STARTPTS,"
        chain = (f"[{i}:v]{pre}scale={W}:{H}:force_original_aspect_ratio=decrease,"
                 f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS}")
        if s["grade"]:
            chain += "," + grade_f
        fc.append(chain + f",format=yuv420p[v{i}]")
    # normalize audio
    for i, s in enumerate(segs):
        if s["has_audio"]:
            pre = ""
            if s["trim"]:
                cs, clen = s["trim"]
                pre = f"atrim=start={cs:.3f}:end={cs + clen:.3f},asetpts=N/SR/TB,"
            fc.append(f"[{i}:a]{pre}aresample=48000,"
                      f"aformat=channel_layouts=stereo[a{i}]")
        else:
            fc.append(f"[{silent_idx[i]}:a]aresample=48000,"
                      f"aformat=channel_layouts=stereo[a{i}]")

    if n == 1:
        vfinal, afinal = "v0", "a0"
    else:
        # video xfade chain
        prev = "v0"
        run = durs[0]
        for i in range(1, n):
            off = run - xdur
            lab = f"vx{i}"
            fc.append(f"[{prev}][v{i}]xfade=transition={transition}:"
                      f"duration={xdur}:offset={off:.3f}[{lab}]")
            prev = lab
            run += durs[i] - xdur
        vfinal = prev
        # audio crossfade chain
        aprev = "a0"
        for i in range(1, n):
            lab = f"ax{i}"
            fc.append(f"[{aprev}][a{i}]acrossfade=d={xdur}[{lab}]")
            aprev = lab
        afinal = aprev

    if no_music:
        fc.append(f"[{afinal}]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    else:
        fo = max(0, total - 1.0)
        fc.append(f"[{bed_idx}:a]atrim=0:{total},afade=t=out:st={fo:.3f}:d=1,"
                  f"volume={bed_vol},aresample=48000,"
                  f"aformat=channel_layouts=stereo[bed]")
        fc.append(f"[{afinal}][bed]amix=inputs=2:duration=first:normalize=0[mix]")
        fc.append(f"[mix]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

    cmd += ["-filter_complex", ";".join(fc),
            "-map", f"[{vfinal}]", "-map", "[aout]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", out]

    r = subprocess.run(cmd, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode()[-2500:])
        raise SystemExit("tie failed")
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
