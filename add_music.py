#!/usr/bin/env python3
"""
Add a music bed to any clip, mixed under the existing audio.

    python3 add_music.py input.mp4                      # synth bed -> output
    python3 add_music.py input.mp4 --music track.mp3    # use your own track
    python3 add_music.py input.mp4 --out result.mp4 --bed-vol 0.35

When no --music is given, a clean, uplifting bed is synthesized to match the
clip's exact duration (soft pad + gentle bell arpeggio over a I-V-vi-IV
progression in C major). The original audio is preserved and the bed is
ducked underneath it; both fade out at the end.
"""

import os
import re
import sys
import wave
import struct
import subprocess

import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000


def probe(path):
    out = subprocess.run([FF, "-i", path], stderr=subprocess.PIPE).stderr.decode()
    dur = 10.0
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    if m:
        h, mn, s = m.groups()
        dur = int(h) * 3600 + int(mn) * 60 + float(s)
    has_audio = "Audio:" in out
    return dur, has_audio


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    """Simple ADSR envelope of length n samples."""
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    ns = max(0, n - na - nd - nr)
    env = np.concatenate([
        np.linspace(0, 1, na, endpoint=False),
        np.linspace(1, s, nd, endpoint=False),
        np.full(ns, s),
        np.linspace(s, 0, nr),
    ])
    if len(env) < n:
        env = np.pad(env, (0, n - len(env)), constant_values=0)
    return env[:n]


def note(freq, dur, kind="pad", amp=0.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "pad":
        # warm detuned pad: a few stacked, slightly detuned sines
        w = np.zeros(n)
        for det in (-0.6, 0.0, 0.6):
            w += np.sin(2 * np.pi * (freq + det) * t)
        w += 0.3 * np.sin(2 * np.pi * 2 * freq * t)  # gentle octave shimmer
        w /= 3.3
        env = adsr(n, a=0.18, d=0.2, s=0.85, r=0.5)
    else:  # "bell" pluck
        w = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * 2 * freq * t)
        w += 0.25 * np.sin(2 * np.pi * 3 * freq * t)
        w /= 1.75
        env = np.exp(-t * 4.5)  # quick decay
    return (w * env * amp).astype(np.float32)


# Note frequencies (Hz)
N = {"C3": 130.81, "E3": 164.81, "G3": 196.00, "A3": 220.00, "F3": 174.61,
     "B3": 246.94, "D4": 293.66, "C4": 261.63, "E4": 329.63, "G4": 392.00,
     "A4": 440.00, "F4": 349.23}


def synth_bed(dur):
    """Uplifting C major bed: C - G - Am - F, looped to fill `dur`."""
    total = int(dur * SR)
    left = np.zeros(total, dtype=np.float32)
    right = np.zeros(total, dtype=np.float32)

    chords = [
        (["C3", "E3", "G3", "C4"], ["C4", "E4", "G4", "E4"]),  # C
        (["G3", "B3", "D4", "G4"], ["G4", "D4", "B3", "D4"]),  # G
        (["A3", "C4", "E4", "A4"], ["A4", "E4", "C4", "E4"]),  # Am
        (["F3", "A3", "C4", "F4"], ["F4", "C4", "A3", "C4"]),  # F
    ]
    chord_len = 2.5  # seconds per chord
    arp_step = chord_len / 4.0

    def place(buf, sig, start):
        s = int(start * SR)
        e = min(total, s + len(sig))
        if s < total:
            buf[s:e] += sig[:e - s]

    t = 0.0
    ci = 0
    while t < dur:
        pad_notes, arp_notes = chords[ci % len(chords)]
        # sustained pad chord
        for nm in pad_notes:
            pad = note(N[nm], chord_len, kind="pad", amp=0.16)
            place(left, pad, t)
            place(right, pad, t)
        # gentle bell arpeggio, panned softly
        for j, nm in enumerate(arp_notes):
            bell = note(N[nm], arp_step + 0.4, kind="bell", amp=0.22)
            pan = 0.5 + 0.35 * (1 if j % 2 else -1)
            place(left, bell * (1 - pan), t + j * arp_step)
            place(right, bell * pan, t + j * arp_step)
        t += chord_len
        ci += 1

    stereo = np.stack([left, right], axis=1)
    # global fade in / out
    fi = int(0.5 * SR)
    fo = int(1.5 * SR)
    stereo[:fi] *= np.linspace(0, 1, fi)[:, None]
    stereo[-fo:] *= np.linspace(1, 0, fo)[:, None]
    # normalize to ~ -3 dBFS
    peak = np.max(np.abs(stereo)) or 1.0
    stereo = stereo / peak * 0.7
    return stereo


def write_wav(path, stereo):
    data = np.clip(stereo, -1, 1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    args = sys.argv[1:]
    music = None
    if "--music" in args:
        i = args.index("--music"); music = args[i + 1]; del args[i:i + 2]
    out = "with_music.mp4"
    if "--out" in args:
        i = args.index("--out"); out = args[i + 1]; del args[i:i + 2]
    bed_vol = 0.85
    if "--bed-vol" in args:
        i = args.index("--bed-vol"); bed_vol = float(args[i + 1]); del args[i:i + 2]
    if not args:
        print("usage: add_music.py input.mp4 [--music track] [--out file] [--bed-vol 0.32]")
        raise SystemExit(1)

    src = args[0]
    dur, has_audio = probe(src)
    print(f"adding music to {src}  ({dur:.1f}s, src audio: {has_audio})")

    bed_path = music
    if music is None:
        bed_path = "/tmp/_music_bed.wav"
        write_wav(bed_path, synth_bed(dur))
        print(f"synthesized bed -> {bed_path}")

    cmd = [FF, "-y", "-i", src, "-i", bed_path, "-filter_complex"]
    fo = max(0, dur - 1.0)
    if has_audio:
        fc = (f"[1:a]atrim=0:{dur},afade=t=out:st={fo}:d=1,volume={bed_vol},"
              f"aresample={SR},aformat=channel_layouts=stereo[m];"
              f"[0:a]volume=1.0,aresample={SR},aformat=channel_layouts=stereo[o];"
              f"[o][m]amix=inputs=2:duration=first:normalize=0[mix];"
              f"[mix]loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        fc = (f"[1:a]atrim=0:{dur},afade=t=out:st={fo}:d=1,volume={bed_vol},"
              f"aresample={SR},aformat=channel_layouts=stereo,"
              f"loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    cmd += [fc, "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", out]
    r = subprocess.run(cmd, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode()[-1800:]); raise SystemExit("mux failed")
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
