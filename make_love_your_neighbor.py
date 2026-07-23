#!/usr/bin/env python3
"""
make_love_your_neighbor.py — render "Love Your Neighbor" as a full lo-fi
chill-pop instrumental (Forrest-Frank-inspired), section by section.

Distinct from track 1: key of G major, ~100 BPM, slightly brighter/bouncier.
Pure-numpy synthesis, no external music service.

Usage:
    pip install numpy imageio-ffmpeg
    python3 make_love_your_neighbor.py            # -> love_your_neighbor.mp3
    python3 make_love_your_neighbor.py out.mp3
"""
import sys, wave, subprocess
import numpy as np

SR = 44100
BPM = 100.0
SPB = 60.0 / BPM
rng = np.random.default_rng(19)

def b2s(beats):  return int(round(beats * SPB * SR))
def midi_freq(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

# --- G major: I V vi IV = G D Em C -----------------------------------------
CHORDS = {
    'G':  [43, 50, 59, 62, 67],   # G2 D3 B3 D4 G4
    'D':  [38, 45, 54, 57, 62],   # D2 A2 F#3 A3 D4
    'Em': [40, 47, 55, 59, 64],   # E2 B2 G3 B3 E4
    'C':  [36, 43, 52, 55, 60],   # C2 G2 E3 G3 C4
}
BASS_ROOT = {'G': 43, 'D': 38, 'Em': 40, 'C': 36}

def adsr(n, a, d, s, r):
    a, d, r = max(1, int(a)), max(1, int(d)), max(1, int(r))
    env = np.zeros(n)
    if a + d + r >= n:
        a = max(1, int(n * 0.2)); d = max(1, n - a); r = 0
    env[:a] = np.linspace(0, 1, a)
    env[a:a+d] = np.linspace(1, s, d)
    sus = n - a - d - r
    if sus > 0: env[a+d:a+d+sus] = s
    if r > 0:   env[n-r:] = np.linspace(env[n-r-1] if n-r-1 >= 0 else s, 0, r)
    return env

def epiano(freq, dur):
    n = b2s(dur); t = np.arange(n) / SR
    parts = [(1.0, 1.0), (2.0, 0.35), (3.0, 0.12), (4.0, 0.06)]
    sig = sum(a * np.sin(2*np.pi*freq*h*t) for h, a in parts)
    tine = 0.25 * np.sin(2*np.pi*freq*6*t) * np.exp(-t*18)
    env = adsr(n, 0.012*SR, 0.15*SR, 0.55, 0.30*SR)
    return (sig + tine) * env

def subbass(freq, dur):
    n = b2s(dur); t = np.arange(n) / SR
    sig = np.sin(2*np.pi*freq*t) + 0.25*np.sin(2*np.pi*freq*2*t)
    sig += 0.12*np.tanh(3*np.sin(2*np.pi*freq*t))
    return sig * adsr(n, 0.010*SR, 0.08*SR, 0.85, 0.06*SR)

def whistle(freq, dur):
    n = b2s(dur); t = np.arange(n) / SR
    vib = 1 + 0.006*np.sin(2*np.pi*5.4*t)
    sig = np.sin(2*np.pi*freq*t*vib) + 0.10*np.sin(2*np.pi*freq*2*t)
    breath = 0.03 * rng.standard_normal(n) * np.exp(-t*6)
    return (sig + breath) * adsr(n, 0.03*SR, 0.05*SR, 0.8, 0.10*SR)

def pluck(freq, dur, damp=0.994):
    n = b2s(dur); N = max(2, int(SR/freq))
    b = rng.uniform(-1, 1, N); out = np.empty(n); idx = 0
    for i in range(n):
        out[i] = b[idx]; nxt = (idx + 1) % N
        b[idx] = damp * 0.5 * (b[idx] + b[nxt]); idx = nxt
    return out * np.exp(-np.arange(n)/SR*4.5)

def kick(dur=0.32):
    n = int(dur*SR); t = np.arange(n)/SR
    f = 120*np.exp(-t*35) + 42
    sig = np.sin(2*np.pi*np.cumsum(f)/SR)
    sig += 0.6*np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*60)
    return sig * np.exp(-t*7)

def snare(dur=0.20):
    n = int(dur*SR); t = np.arange(n)/SR
    return 0.9*(rng.standard_normal(n)*np.exp(-t*22)) + 0.5*np.sin(2*np.pi*185*t)*np.exp(-t*26)

def hat(dur=0.05, open=False):
    n = int(dur*SR); t = np.arange(n)/SR
    x = rng.standard_normal(n) * np.exp(-t*(12 if open else 55))
    return np.diff(x, prepend=0.0)

def clap(dur=0.22):
    n = int(dur*SR); out = np.zeros(n)
    for off in (0, 0.010, 0.020, 0.032):
        s = int(off*SR); m = n - s
        if m <= 0: continue
        out[s:] += rng.standard_normal(m) * np.exp(-np.arange(m)/SR*45)
    return out * np.exp(-np.arange(n)/SR*10)

def snap(dur=0.12):
    n = int(dur*SR); t = np.arange(n)/SR
    return np.diff(rng.standard_normal(n)*np.exp(-t*70), prepend=0.0) * 1.2

TOTAL_BEATS = 0
EVENTS = []
def place(start_beat, sig, gain=1.0):
    EVENTS.append((start_beat, sig.astype(np.float32), float(gain)))

def write_chord(bs, ch, gain=0.16):
    for m in CHORDS[ch]:
        place(bs, epiano(midi_freq(m), 4.0), gain)

def write_bass(bs, ch, gain=0.55, bounce=True):
    root = BASS_ROOT[ch]
    place(bs + 0.0, subbass(midi_freq(root), 1.5), gain)
    place(bs + 2.0, subbass(midi_freq(root), 1.0), gain)
    if bounce:
        place(bs + 3.0, subbass(midi_freq(root+12), 0.5), gain*0.8)
        place(bs + 3.5, subbass(midi_freq(root), 0.5), gain*0.8)

def write_uke(bs, ch, gain=0.14):
    for off in (1.5, 2.5, 3.5, 4.5):
        for m in CHORDS[ch][2:]:
            place(bs + (off-1), pluck(midi_freq(m+12), 0.45), gain)

def write_drums(bs, level):
    if level >= 1:
        place(bs + 0.0, kick(), 0.95); place(bs + 2.5, kick(), 0.70)
    if level == 3:
        place(bs + 0.0, kick(), 0.7)
    if level >= 1:
        for beat in (1.0, 3.0):
            place(bs + beat, snare(), 0.55); place(bs + beat, clap(), 0.40)
    if level == 0:
        for beat in (1.0, 3.0):
            place(bs + beat, snap(), 0.35)
    if level != 3:
        for i in range(8):
            place(bs + i*0.5 + (0.06 if i % 2 else 0.0), hat(open=(i == 7)),
                  0.16 if level >= 1 else 0.09)
    else:
        for beat in (0.5, 1.5, 2.5, 3.5):
            place(bs + beat, hat(), 0.10)

def write_melody(start_beat, melody, gain=0.34):
    cur = start_beat
    for note, dur in melody:
        if note: place(cur, whistle(midi_freq(note), dur*0.92), gain)
        cur += dur

# --- G-pentatonic melodies (G A B D E) -------------------------------------
phraseA = [(79,1),(76,1),(74,2),(76,1),(74,1),(71,2),(74,1),(71,1),(69,2),(71,2),(0,2)]
phraseB = [(79,1),(76,1),(74,2),(76,1),(79,1),(81,2),(79,1),(76,1),(74,2),(76,2),(0,2)]
CHORUS_MEL = phraseA + phraseB
INTRO_MEL  = [(0,2),(74,1),(76,1),(79,2),(0,2),(76,1),(74,1),(71,2),(0,4)]
PREF_MEL   = [(71,1),(74,1),(76,1),(79,1),(81,2),(79,2),(76,2),(79,6)]
OUTRO_MEL  = phraseA

MAIN   = ['G','D','Em','C']
PRE    = ['C','C','D','D']
BRIDGE = ['Em','C','G','D']

def section(name, bars, chords, level, uke=True, bass=True, mel=None):
    global TOTAL_BEATS
    start = TOTAL_BEATS
    for bar in range(bars):
        bs = TOTAL_BEATS + bar*4
        ch = chords[bar % len(chords)]
        write_chord(bs, ch)
        if bass: write_bass(bs, ch, bounce=(level >= 1))
        if uke:  write_uke(bs, ch, gain=0.14 if level != 3 else 0.09)
        write_drums(bs, level)
    if mel is not None: write_melody(start, mel)
    TOTAL_BEATS += bars*4

section('Intro',       4, MAIN,   0, mel=INTRO_MEL)
section('Verse 1',     8, MAIN,   1)
section('Pre-Chorus',  4, PRE,    1)
section('Chorus',      8, MAIN,   2, mel=CHORUS_MEL)
section('Post-Chorus', 4, MAIN,   2, mel=INTRO_MEL)
section('Verse 2',     8, MAIN,   1)
section('Pre-Chorus',  4, PRE,    1)
section('Chorus',      8, MAIN,   2, mel=CHORUS_MEL)
section('Bridge',      8, BRIDGE, 3)
section('Pre-Final',   4, PRE,    1, mel=PREF_MEL)
section('Final Chorus',8, MAIN,   2, mel=CHORUS_MEL)
section('Post-Chorus', 4, MAIN,   2, mel=INTRO_MEL)
section('Outro',       4, MAIN,   0, mel=OUTRO_MEL)

total_samples = b2s(TOTAL_BEATS) + SR
mix = np.zeros(total_samples, dtype=np.float32)
sc = np.ones(total_samples, dtype=np.float32)
dip = np.linspace(0.55, 1.0, int(0.18*SR))

for start_beat, sig, gain in EVENTS:
    i = b2s(start_beat); j = i + len(sig)
    if j > total_samples: sig = sig[:total_samples - i]; j = total_samples
    mix[i:j] += sig * gain

for bar_start in range(0, int(TOTAL_BEATS), 4):
    for kb in (0.0, 2.5):
        i = b2s(bar_start + kb); j = min(total_samples, i + len(dip))
        if i < total_samples: sc[i:j] = np.minimum(sc[i:j], dip[:j-i])
k = np.ones(int(0.02*SR)) / int(0.02*SR)
sc = np.convolve(sc, k, mode='same')
mix *= sc

def lowpass(x, width):
    k = max(1, int(width)); c = np.cumsum(np.insert(x, 0, 0.0))
    return (c[k:] - c[:-k]) / k
mix = lowpass(mix, 3)

mix = mix + 0.004*rng.standard_normal(len(mix))
crackle = np.zeros(len(mix)); idx = rng.integers(0, len(mix), size=len(mix)//4000)
crackle[idx] = rng.uniform(-0.25, 0.25, size=len(idx)); mix += crackle
mix = np.tanh(1.25 * mix)
mix = mix / (np.max(np.abs(mix)) or 1.0) * 0.89

fi = int(0.4*SR); fo = int(3.0*SR)
mix[:fi] *= np.linspace(0, 1, fi); mix[-fo:] *= np.linspace(1, 0, fo)

delay = 9
right = np.concatenate([np.zeros(delay, dtype=mix.dtype), mix[:-delay]]) * 0.97
stereo = np.clip(np.stack([mix, right], axis=1), -1, 1)

out_mp3 = sys.argv[1] if len(sys.argv) > 1 else 'love_your_neighbor.mp3'
wav_path = out_mp3.rsplit('.', 1)[0] + '.wav'
with wave.open(wav_path, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((stereo * 32767).astype('<i2').tobytes())
print(f"wrote {wav_path}  ({len(mix)/SR:.1f}s, {TOTAL_BEATS} beats)")

try:
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, '-y', '-loglevel', 'error', '-i', wav_path,
                    '-codec:a', 'libmp3lame', '-b:a', '256k', out_mp3], check=True)
    print(f"wrote {out_mp3}")
except Exception as e:
    print(f"(mp3 encode skipped: {e}) — WAV is at {wav_path}")
