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


def synth_hardcore(dur, bpm=148):
    """Aggressive driving bed: four-on-the-floor kick, distorted bass,
    power-chord stabs, hats + snare. E-minor riff (Em - C - G - D)."""
    sr = SR
    n = int(dur * sr)
    L = np.zeros(n, dtype=np.float32)
    R = np.zeros(n, dtype=np.float32)
    beat = 60.0 / bpm
    rng = np.random.default_rng(7)

    roots = {"E": 82.41, "G": 98.00, "A": 110.0, "C": 130.81,
             "D": 146.83, "B": 123.47}
    prog = ["E", "C", "G", "D"]

    def place(buf, sig, start):
        s = int(start * sr)
        e = min(n, s + len(sig))
        if s < n:
            buf[s:e] += sig[:e - s]

    def kick(amp=1.0):
        t = np.arange(int(0.20 * sr)) / sr
        f = 120 * np.exp(-t * 30) + 48
        ph = 2 * np.pi * np.cumsum(f) / sr
        env = np.exp(-t * 16)
        click = np.exp(-t * 200) * 0.4
        return ((np.sin(ph) + click) * env * amp).astype(np.float32)

    def snare():
        t = np.arange(int(0.20 * sr)) / sr
        noise = rng.uniform(-1, 1, len(t))
        tone = 0.4 * np.sin(2 * np.pi * 180 * t)
        env = np.exp(-t * 20)
        return ((noise * 0.9 + tone) * env * 0.6).astype(np.float32)

    def hat(opn=False):
        t = np.arange(int((0.09 if opn else 0.03) * sr)) / sr
        noise = np.diff(rng.uniform(-1, 1, len(t) + 1))  # crude high-pass
        env = np.exp(-t * (16 if opn else 45))
        return (noise * env * 0.35).astype(np.float32)

    def bassnote(freq, d):
        t = np.arange(int(d * sr)) / sr
        w = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * 2 * freq * t)
        w = np.tanh(w * 2.2)  # drive
        env = np.minimum(1, t / 0.004) * np.exp(-t * 2.2)
        return (w * env * 0.6).astype(np.float32)

    def powerchord(freq, d):
        t = np.arange(int(d * sr)) / sr
        w = np.zeros(len(t))
        for f in (freq, freq * 1.5, freq * 2.0):     # root, fifth, octave
            for k in range(1, 7):                     # saw-ish
                w += np.sin(2 * np.pi * f * k * t) / k
        w = np.tanh((w / 3.0) * 3.0)                  # distortion
        env = np.minimum(1, t / 0.005) * np.exp(-t * 0.9)
        return (w * env * 0.45).astype(np.float32)

    nbeats = int(dur / beat) + 1
    for b in range(nbeats):
        tb = b * beat
        chord = prog[(b // 4) % len(prog)]
        rf = roots[chord]
        place(L, kick(), tb); place(R, kick(), tb)
        if b % 2 == 1:
            sn = snare(); place(L, sn, tb); place(R, sn, tb)
        h = hat(); place(L, h * 1.1, tb); place(R, h * 0.9, tb)
        h2 = hat(opn=(b % 4 == 3))
        place(L, h2 * 0.9, tb + beat / 2); place(R, h2 * 1.1, tb + beat / 2)
        place(L, bassnote(rf / 2, beat / 2), tb)
        place(R, bassnote(rf / 2, beat / 2), tb)
        place(L, bassnote(rf / 2, beat / 2), tb + beat / 2)
        place(R, bassnote(rf / 2, beat / 2), tb + beat / 2)
        pc = powerchord(rf, beat)
        place(L, pc, tb); place(R, pc, tb)

    stereo = np.stack([L, R], axis=1)
    fi, fo = int(0.04 * sr), int(0.8 * sr)
    stereo[:fi] *= np.linspace(0, 1, fi)[:, None]
    stereo[-fo:] *= np.linspace(1, 0, fo)[:, None]
    peak = np.max(np.abs(stereo)) or 1.0
    return stereo / peak * 0.9


def synth_grunge(dur, bpm=92):
    """Grungy, raw bed: sludgy detuned distorted guitar-ish power chords,
    fuzz bass, loose drums, plus tape hiss / vinyl crackle / bit-crush grit.
    Lower & dirtier than synth_hardcore. E-minor sludge riff."""
    sr = SR
    n = int(dur * sr)
    L = np.zeros(n, dtype=np.float32)
    R = np.zeros(n, dtype=np.float32)
    beat = 60.0 / bpm
    rng = np.random.default_rng(11)

    roots = {"E": 82.41, "G": 98.00, "A": 110.0, "C": 130.81, "D": 146.83}
    prog = ["E", "E", "G", "D", "E", "E", "C", "D"]   # 8-bar sludge loop

    def place(buf, sig, start):
        s = int(start * sr)
        e = min(n, s + len(sig))
        if s < n:
            buf[s:e] += sig[:e - s]

    def kick():
        t = np.arange(int(0.22 * sr)) / sr
        f = 110 * np.exp(-t * 26) + 46
        env = np.exp(-t * 13)
        return (np.sin(2 * np.pi * np.cumsum(f) / sr) * env).astype(np.float32)

    def snare():
        t = np.arange(int(0.26 * sr)) / sr
        noise = rng.uniform(-1, 1, len(t))
        env = np.exp(-t * 15)
        body = 0.3 * np.sin(2 * np.pi * 150 * t)
        return np.tanh((noise * 0.9 + body) * env * 1.4).astype(np.float32) * 0.55

    def fuzzbass(freq, d):
        t = np.arange(int(d * sr)) / sr
        w = np.sin(2 * np.pi * freq * t)
        w = np.tanh(w * 6.0)                 # heavy fuzz
        env = np.minimum(1, t / 0.006) * np.exp(-t * 1.6)
        return (w * env * 0.6).astype(np.float32)

    def guitar(freq, d):
        # detuned, palm-muted-ish distorted power chord (root + fifth + octave)
        t = np.arange(int(d * sr)) / sr
        w = np.zeros(len(t))
        for f, det in ((freq, 1.0), (freq * 1.5, 1.004), (freq * 2.0, 0.997)):
            for k in range(1, 9):
                w += np.sin(2 * np.pi * f * det * k * t) / k
        w /= 3.0
        # slow wobble (tape/pitch drift) + fuzz
        wob = 1.0 + 0.012 * np.sin(2 * np.pi * 5.0 * t)
        w = np.tanh(w * 5.0 * wob)
        env = np.minimum(1, t / 0.004) * (0.5 + 0.5 * np.exp(-t * 1.1))
        return (w * env * 0.42).astype(np.float32)

    nbeats = int(dur / beat) + 1
    for b in range(nbeats):
        tb = b * beat
        rf = roots[prog[b % len(prog)]]
        place(L, kick(), tb); place(R, kick(), tb)
        if b % 2 == 1:
            sn = snare(); place(L, sn, tb); place(R, sn, tb)
        # chugging eighths on guitar + bass
        for off in (0.0, 0.5):
            g = guitar(rf, beat * 0.5)
            place(L, g, tb + off * beat); place(R, g, tb + off * beat)
            bs = fuzzbass(rf / 2, beat * 0.5)
            place(L, bs, tb + off * beat); place(R, bs, tb + off * beat)

    stereo = np.stack([L, R], axis=1)

    # --- grit layer: tape hiss + vinyl crackle ---
    hiss = rng.normal(0, 0.012, (n, 2)).astype(np.float32)
    crackle = np.zeros((n, 2), dtype=np.float32)
    pops = rng.random(n) < 0.0008
    crackle[pops] = rng.uniform(-0.5, 0.5, (pops.sum(), 1))
    stereo += hiss + crackle

    # bit-crush for lo-fi rawness (reduce bit depth + light sample hold)
    levels = 28.0
    stereo = np.round(stereo * levels) / levels
    hold = 3
    stereo[: (n // hold) * hold] = np.repeat(
        stereo[: (n // hold) * hold: hold], hold, axis=0)

    fi, fo = int(0.04 * sr), int(0.9 * sr)
    stereo[:fi] *= np.linspace(0, 1, fi)[:, None]
    stereo[-fo:] *= np.linspace(1, 0, fo)[:, None]
    peak = np.max(np.abs(stereo)) or 1.0
    return stereo / peak * 0.9


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
