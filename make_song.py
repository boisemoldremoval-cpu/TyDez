#!/usr/bin/env python3
"""
make_song.py — render "The Joy of the Lord" as a full lo-fi chill-pop
instrumental (Forrest-Frank-inspired), section by section, all the way through.

No external music service required. Pure-numpy synthesis:
  warm electric-piano pad, sub bass, boom-bap kit, ukulele skank,
  claps/snaps, whistle lead — plus vinyl warmth and a gentle sidechain.

Usage:
    pip install numpy imageio-ffmpeg
    python3 make_song.py                 # -> joy_of_the_lord.mp3
    python3 make_song.py out.mp3         # custom output
"""
import sys, wave, struct, subprocess
import numpy as np

SR = 44100
BPM = 95.0
SPB = 60.0 / BPM                 # seconds per beat
rng = np.random.default_rng(7)

def b2s(beats):  return int(round(beats * SPB * SR))
def midi_freq(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

# ----------------------------------------------------------------------------
# Chord voicings (midi note numbers) and bass roots
# ----------------------------------------------------------------------------
CHORDS = {
    'C':  [48, 55, 60, 64, 67],   # C3 G3 C4 E4 G4
    'G':  [43, 50, 59, 62, 67],   # G2 D3 B3 D4 G4
    'Am': [45, 52, 60, 64, 69],   # A2 E3 C4 E4 A4
    'F':  [41, 48, 57, 60, 65],   # F2 C3 A3 C4 F4
}
BASS_ROOT = {'C': 36, 'G': 31, 'Am': 33, 'F': 29}

# ----------------------------------------------------------------------------
# Envelopes / oscillators
# ----------------------------------------------------------------------------
def adsr(n, a, d, s, r):
    a, d, r = max(1, int(a)), max(1, int(d)), max(1, int(r))
    env = np.zeros(n)
    if a + d + r >= n:                      # short note: attack + quick decay
        a = max(1, int(n * 0.2)); d = max(1, n - a); r = 0
    env[:a] = np.linspace(0, 1, a)
    env[a:a+d] = np.linspace(1, s, d)
    sus = n - a - d - r
    if sus > 0: env[a+d:a+d+sus] = s
    if r > 0:   env[n-r:] = np.linspace(env[n-r-1] if n-r-1 >= 0 else s, 0, r)
    return env

def epiano(freq, dur):
    """Warm electric-piano / Rhodes-ish tone: a few sine partials, bell attack."""
    n = b2s(dur); t = np.arange(n) / SR
    parts = [(1.0, 1.0), (2.0, 0.35), (3.0, 0.12), (4.0, 0.06)]
    sig = sum(a * np.sin(2*np.pi*freq*h*t) for h, a in parts)
    tine = 0.25 * np.sin(2*np.pi*freq*6*t) * np.exp(-t*18)   # bell transient
    env = adsr(n, 0.012*SR, 0.15*SR, 0.55, 0.30*SR)
    return (sig + tine) * env

def subbass(freq, dur):
    n = b2s(dur); t = np.arange(n) / SR
    sig = np.sin(2*np.pi*freq*t) + 0.25*np.sin(2*np.pi*freq*2*t)
    sig += 0.12*np.tanh(3*np.sin(2*np.pi*freq*t))            # a little grit
    return sig * adsr(n, 0.010*SR, 0.08*SR, 0.85, 0.06*SR)

def whistle(freq, dur):
    n = b2s(dur); t = np.arange(n) / SR
    vib = 1 + 0.006*np.sin(2*np.pi*5.2*t)
    sig = np.sin(2*np.pi*freq*t*vib) + 0.10*np.sin(2*np.pi*freq*2*t)
    breath = 0.03 * rng.standard_normal(n) * np.exp(-t*6)
    env = adsr(n, 0.03*SR, 0.05*SR, 0.8, 0.10*SR)
    return (sig + breath) * env

def pluck(freq, dur, damp=0.994):
    """Karplus-Strong ukulele-ish pluck."""
    n = b2s(dur); N = max(2, int(SR/freq))
    buf = rng.uniform(-1, 1, N); out = np.empty(n)
    b = buf.copy(); idx = 0
    for i in range(n):
        out[i] = b[idx]
        nxt = (idx + 1) % N
        b[idx] = damp * 0.5 * (b[idx] + b[nxt])
        idx = nxt
    t = np.arange(n)/SR
    return out * np.exp(-t*4.5)

# --- drums -----------------------------------------------------------------
def kick(dur=0.32):
    n = int(dur*SR); t = np.arange(n)/SR
    f = 120*np.exp(-t*35) + 42
    sig = np.sin(2*np.pi*np.cumsum(f)/SR)
    sig += 0.6*np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*60)  # click
    return sig * np.exp(-t*7)

def snare(dur=0.20):
    n = int(dur*SR); t = np.arange(n)/SR
    noise = rng.standard_normal(n) * np.exp(-t*22)
    tone = 0.5*np.sin(2*np.pi*185*t) * np.exp(-t*26)
    return 0.9*noise + tone

def hat(dur=0.05, open=False):
    n = int(dur*SR); t = np.arange(n)/SR
    d = 12 if open else 55
    x = rng.standard_normal(n) * np.exp(-t*d)
    x = np.diff(x, prepend=0.0)                # crude high-pass -> brighter
    return x

def clap(dur=0.22):
    n = int(dur*SR); out = np.zeros(n)
    for off in (0, 0.010, 0.020, 0.032):       # a few staggered bursts
        s = int(off*SR); m = n - s
        if m <= 0: continue
        tt = np.arange(m)/SR
        out[s:] += rng.standard_normal(m) * np.exp(-tt*45)
    tt = np.arange(n)/SR
    return out * np.exp(-tt*10)

def snap(dur=0.12):
    n = int(dur*SR); t = np.arange(n)/SR
    x = rng.standard_normal(n) * np.exp(-t*70)
    x = np.diff(x, prepend=0.0)
    return x * 1.2

# ----------------------------------------------------------------------------
# Mixer
# ----------------------------------------------------------------------------
TOTAL_BEATS = 0
EVENTS = []   # (start_beat, samples, gain)
KICKS = []    # kick start samples (for sidechain)

def place(start_beat, sig, gain=1.0):
    EVENTS.append((start_beat, sig.astype(np.float32), float(gain)))

# --- pattern writers -------------------------------------------------------
def write_chord(bar_start_beat, chord, gain=0.16):
    notes = CHORDS[chord]
    for m in notes:
        place(bar_start_beat, epiano(midi_freq(m), 4.0), gain)

def write_bass(bar_start_beat, chord, gain=0.55, bounce=True):
    root = BASS_ROOT[chord]
    place(bar_start_beat + 0.0, subbass(midi_freq(root), 1.5), gain)
    place(bar_start_beat + 2.0, subbass(midi_freq(root), 1.0), gain)
    if bounce:
        place(bar_start_beat + 3.0, subbass(midi_freq(root+12), 0.5), gain*0.8)
        place(bar_start_beat + 3.5, subbass(midi_freq(root), 0.5), gain*0.8)

def write_uke(bar_start_beat, chord, gain=0.14):
    top = CHORDS[chord][2:]                    # upper voices for the skank
    for off in (1.5, 2.5, 3.5, 4.5):           # reggae-ish offbeats
        for m in top:
            place(bar_start_beat + (off-1), pluck(midi_freq(m+12), 0.45), gain)

def write_drums(bar_start_beat, level):
    # level: 0 intro, 1 verse, 2 chorus/full, 3 bridge(soft)
    if level >= 1:
        place(bar_start_beat + 0.0, kick(), 0.95)
        place(bar_start_beat + 2.5, kick(), 0.70)
    if level == 3:
        place(bar_start_beat + 0.0, kick(), 0.7)
    # backbeat
    if level >= 1:
        for beat in (1.0, 3.0):
            place(bar_start_beat + beat, snare(), 0.55)
            place(bar_start_beat + beat, clap(), 0.40)
    if level == 0:                             # intro: just soft claps/snaps
        for beat in (1.0, 3.0):
            place(bar_start_beat + beat, snap(), 0.35)
    # hats (swung 8ths)
    if level != 3:
        for i in range(8):
            beat = i * 0.5
            swing = 0.06 if (i % 2) else 0.0
            g = 0.16 if level >= 1 else 0.09
            place(bar_start_beat + beat + swing, hat(open=(i == 7)), g)
    else:
        for beat in (0.5, 1.5, 2.5, 3.5):
            place(bar_start_beat + beat, hat(), 0.10)

def write_melody(start_beat, melody, gain=0.34):
    """melody: list of (midi or 0-rest, beats)."""
    cur = start_beat
    for note, dur in melody:
        if note:
            place(cur, whistle(midi_freq(note), dur*0.92), gain)
        cur += dur

# ----------------------------------------------------------------------------
# Melodies (pentatonic C-D-E-G-A)
# ----------------------------------------------------------------------------
phraseA = [(72,1),(69,1),(67,2),(69,1),(67,1),(64,2),(67,1),(64,1),(62,2),(64,2),(0,2)]
phraseB = [(72,1),(69,1),(67,2),(69,1),(72,1),(74,2),(72,1),(69,1),(67,2),(69,2),(0,2)]
CHORUS_MEL = phraseA + phraseB                     # 32 beats
INTRO_MEL  = [(0,2),(67,1),(69,1),(72,2),(0,2),(69,1),(67,1),(64,2),(0,4)]      # 16
PREF_MEL   = [(64,1),(67,1),(69,1),(72,1),(74,2),(72,2),(69,2),(72,6)]          # 16
OUTRO_MEL  = phraseA                                # 16

# ----------------------------------------------------------------------------
# Arrangement — each section renders its bars fully
# ----------------------------------------------------------------------------
MAIN   = ['C','G','Am','F']
PRE    = ['F','F','G','G']
BRIDGE = ['Am','F','C','G']

def section(name, bars, chords, drum_level, uke=True, bass=True, mel=None):
    global TOTAL_BEATS
    start = TOTAL_BEATS
    for bar in range(bars):
        bs = TOTAL_BEATS + bar*4
        ch = chords[bar % len(chords)]
        write_chord(bs, ch)
        if bass: write_bass(bs, ch, bounce=(drum_level >= 1))
        if uke:  write_uke(bs, ch, gain=0.14 if drum_level != 3 else 0.09)
        write_drums(bs, drum_level)
    if mel is not None:
        write_melody(start, mel)
    TOTAL_BEATS += bars*4

# ---- the song, start to finish -------------------------------------------
section('Intro',      4, MAIN,   0, uke=True,  bass=True,  mel=INTRO_MEL)
section('Verse 1',    8, MAIN,   1, uke=True,  bass=True,  mel=None)
section('Pre-Chorus', 4, PRE,    1, uke=True,  bass=True,  mel=None)
section('Chorus',     8, MAIN,   2, uke=True,  bass=True,  mel=CHORUS_MEL)
section('Post-Chorus',4, MAIN,   2, uke=True,  bass=True,  mel=INTRO_MEL)
section('Verse 2',    8, MAIN,   1, uke=True,  bass=True,  mel=None)
section('Pre-Chorus', 4, PRE,    1, uke=True,  bass=True,  mel=None)
section('Chorus',     8, MAIN,   2, uke=True,  bass=True,  mel=CHORUS_MEL)
section('Bridge',     8, BRIDGE, 3, uke=True,  bass=True,  mel=None)
section('Pre-Final',  4, PRE,    1, uke=True,  bass=True,  mel=PREF_MEL)
section('Final Chorus',8,MAIN,   2, uke=True,  bass=True,  mel=CHORUS_MEL)
section('Post-Chorus',4, MAIN,   2, uke=True,  bass=True,  mel=INTRO_MEL)
section('Outro',      4, MAIN,   0, uke=True,  bass=True,  mel=OUTRO_MEL)

# ----------------------------------------------------------------------------
# Render mix
# ----------------------------------------------------------------------------
total_samples = b2s(TOTAL_BEATS) + SR   # +1s tail
mix = np.zeros(total_samples, dtype=np.float32)
sc = np.ones(total_samples, dtype=np.float32)   # sidechain envelope

dip = np.linspace(0.55, 1.0, int(0.18*SR))      # pump shape after each kick

for start_beat, sig, gain in EVENTS:
    i = b2s(start_beat); j = i + len(sig)
    if j > total_samples:
        sig = sig[:total_samples - i]; j = total_samples
    mix[i:j] += sig * gain

# sidechain: dip the whole mix slightly on every kick hit
for start_beat, sig, gain in EVENTS:
    pass
# recompute kick positions from the arrangement (beats 0 & 2.5 of every bar, etc.)
for bar_start in range(0, int(TOTAL_BEATS), 4):
    for kb in (0.0, 2.5):
        i = b2s(bar_start + kb)
        j = min(total_samples, i + len(dip))
        if i < total_samples:
            sc[i:j] = np.minimum(sc[i:j], dip[:j-i])
# smooth the sidechain
k = np.ones(int(0.02*SR)) / int(0.02*SR)
sc = np.convolve(sc, k, mode='same')
mix *= sc

# --- lo-fi mastering -------------------------------------------------------
# gentle low-pass (moving average) to soften highs
def lowpass(x, width):
    k = max(1, int(width))
    c = np.cumsum(np.insert(x, 0, 0.0))
    return (c[k:] - c[:-k]) / k
mix = lowpass(mix, 3)

# vinyl warmth: soft noise bed + sparse crackle
noise = 0.004 * rng.standard_normal(len(mix))
crackle = np.zeros(len(mix))
idx = rng.integers(0, len(mix), size=len(mix)//4000)
crackle[idx] = rng.uniform(-0.25, 0.25, size=len(idx))
mix = mix + noise + crackle

# soft-clip / glue
mix = np.tanh(1.25 * mix)

# normalize
peak = np.max(np.abs(mix)) or 1.0
mix = mix / peak * 0.89

# fades
fi = int(0.4*SR); fo = int(3.0*SR)
mix[:fi] *= np.linspace(0, 1, fi)
mix[-fo:] *= np.linspace(1, 0, fo)

# subtle stereo width (Haas)
delay = 9
right = np.concatenate([np.zeros(delay, dtype=mix.dtype), mix[:-delay]]) * 0.97
stereo = np.stack([mix, right], axis=1)
stereo = np.clip(stereo, -1, 1)

# ----------------------------------------------------------------------------
# Write WAV, then encode MP3 via imageio-ffmpeg
# ----------------------------------------------------------------------------
out_mp3 = sys.argv[1] if len(sys.argv) > 1 else 'joy_of_the_lord.mp3'
wav_path = out_mp3.rsplit('.', 1)[0] + '.wav'
pcm = (stereo * 32767).astype('<i2')
with wave.open(wav_path, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())

dur = len(mix) / SR
print(f"wrote {wav_path}  ({dur:.1f}s, {TOTAL_BEATS} beats)")

try:
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, '-y', '-loglevel', 'error', '-i', wav_path,
                    '-codec:a', 'libmp3lame', '-b:a', '256k', out_mp3], check=True)
    print(f"wrote {out_mp3}")
except Exception as e:
    print(f"(mp3 encode skipped: {e}) — WAV is at {wav_path}")
