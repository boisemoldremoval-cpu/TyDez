#!/usr/bin/env python3
"""
make_bigger_than_the_storm.py — "Bigger Than the Storm", contemporary worship folk.

Opens with the old hymn "How Great Thou Art" (the melody is the public-domain
Swedish folk tune "O Store Gud"), rendered reverent on fingerpicked acoustic +
warm strings, then flows into the laid-back Jack-Johnson brushed-drum groove of
the song, lifts full at the chorus, builds through the bridge, and closes by
reprising the "How Great Thou Art" refrain — reverent and sparse again.
Same instrument set throughout; every transition is a gradual gain automation.
Pure-numpy synthesis; no external music service.

Note: only the *melody* of How Great Thou Art (public-domain tune) is used here.
The modern English lyrics (Stuart K. Hine, 1949) are under copyright and are
NOT reproduced — the sung words remain the project's own paraphrase.

Usage:
    pip install numpy imageio-ffmpeg
    python3 make_bigger_than_the_storm.py           # -> bigger_than_the_storm.mp3
    python3 make_bigger_than_the_storm.py out.mp3
"""
import sys, wave, subprocess
from functools import lru_cache
import numpy as np

SR = 44100
BPM = 74.0
SPB = 60.0 / BPM
rng = np.random.default_rng(41)

def b2s(beats):   return int(round(beats * SPB * SR))
def midi_freq(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

# --- D major: I V vi IV = D A Bm G -----------------------------------------
CHORDS = {
    'D':  [38, 45, 54, 57, 62],   # D2 A2 F#3 A3 D4
    'A':  [45, 52, 57, 61, 64],   # A2 E3 A3 C#4 E4
    'Bm': [47, 54, 59, 62, 66],   # B2 F#3 B3 D4 F#4
    'G':  [43, 50, 55, 59, 62],   # G2 D3 G3 B3 D4
}
BASS_ROOT = {'D': 38, 'A': 45, 'Bm': 47, 'G': 43}

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

# --- instruments -----------------------------------------------------------
def gtr_pluck(freq, dur, damp=0.9965):
    """Fingerpicked steel-string via Karplus-Strong (long, bright ring)."""
    n = b2s(dur); N = max(2, int(SR/freq))
    b = rng.uniform(-1, 1, N); out = np.empty(n); idx = 0
    for i in range(n):
        out[i] = b[idx]; nxt = (idx + 1) % N
        b[idx] = damp * 0.5 * (b[idx] + b[nxt]); idx = nxt
    return out * np.exp(-np.arange(n)/SR*2.6)

def strings(freq, dur):
    """Warm string-ensemble pad: detuned partials, slow swell, long release."""
    n = b2s(dur); t = np.arange(n) / SR
    sig = np.zeros(n)
    for det in (0.997, 1.0, 1.003):                       # small ensemble
        f = freq * det
        for h, a in ((1, 1.0), (2, 0.5), (3, 0.28), (4, 0.14), (5, 0.07)):
            sig += a * np.sin(2*np.pi*f*h*t)
    sig *= (1 + 0.004*np.sin(2*np.pi*4.8*t))              # gentle vibrato
    env = adsr(n, 0.40*SR, 0.30*SR, 0.85, 0.55*SR)
    return sig * env / 6.0

def upright(freq, dur):
    n = b2s(dur); t = np.arange(n) / SR
    sig = np.sin(2*np.pi*freq*t) + 0.3*np.sin(2*np.pi*freq*2*t)
    thump = 0.4*np.sin(2*np.pi*freq*t) * np.exp(-t*40)    # finger attack
    return (sig + thump) * adsr(n, 0.012*SR, 0.12*SR, 0.7, 0.20*SR)

def lead_voice(freq, dur):
    """Warm topline carrying the vocal melody — soft, conversational."""
    n = b2s(dur); t = np.arange(n) / SR
    vib = 1 + 0.005*np.sin(2*np.pi*5.0*t)
    sig = np.sin(2*np.pi*freq*t*vib) + 0.30*np.sin(2*np.pi*freq*2*t) + 0.12*np.sin(2*np.pi*freq*3*t)
    breath = 0.02 * rng.standard_normal(n) * np.exp(-t*5)
    return (sig + breath) * adsr(n, 0.06*SR, 0.10*SR, 0.8, 0.18*SR)

def brush_kick(dur=0.34):
    n = int(dur*SR); t = np.arange(n)/SR
    f = 100*np.exp(-t*30) + 44
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*8) * 0.9

def brush_snare(dur=0.26):
    """Brushed backbeat — soft noise swell, no sharp crack."""
    n = int(dur*SR); t = np.arange(n)/SR
    noise = rng.standard_normal(n)
    swell = np.minimum(1.0, t/0.010) * np.exp(-t*14)      # soft attack, gentle decay
    x = noise * swell
    return np.convolve(x, np.ones(60)/60, mode='same')    # smooth -> "shh"

def shaker(dur=0.09):
    n = int(dur*SR); t = np.arange(n)/SR
    x = rng.standard_normal(n) * np.exp(-t*40)
    return np.diff(x, prepend=0.0) * 0.6

# --- memoized note synthesis (only ~20 distinct pitches recur) -------------
def _k(dur): return int(round(dur * 1000))
@lru_cache(maxsize=None)
def c_gtr(midi, k):  return gtr_pluck(midi_freq(midi), k/1000.0)
@lru_cache(maxsize=None)
def c_str(midi, k):  return strings(midi_freq(midi), k/1000.0)
@lru_cache(maxsize=None)
def c_upr(midi, k):  return upright(midi_freq(midi), k/1000.0)
@lru_cache(maxsize=None)
def c_lead(midi, k): return lead_voice(midi_freq(midi), k/1000.0)

# --- mixer with per-instrument buses ---------------------------------------
BUSES = {k: None for k in ('gtr', 'str', 'bass', 'drm', 'lead')}
EVENTS = {k: [] for k in BUSES}
def place(bus, start_beat, sig, gain=1.0):
    EVENTS[bus].append((start_beat, sig.astype(np.float32), float(gain)))

FULL_PICK = [(0.0,0),(0.5,4),(1.0,2),(1.5,3),(2.0,1),(2.5,4),(3.0,2),(3.5,3)]
SPARSE_PICK = [(0.0,0),(1.0,2),(2.0,4),(3.0,3)]

def fingerpick(bs, ch, sparse=False):
    v = CHORDS[ch]
    pat = SPARSE_PICK if sparse else FULL_PICK
    dur = 1.7 if sparse else 0.95
    for off, idx in pat:
        place('gtr', bs + off, c_gtr(v[idx], _k(dur)), 0.5)

def pad_strings(bs, ch):
    for m in CHORDS[ch]:
        place('str', bs, c_str(m, _k(4.0)), 0.10)

def bassline(bs, ch):
    root = BASS_ROOT[ch]
    place('bass', bs + 0.0, c_upr(root, _k(2.0)), 0.5)
    place('bass', bs + 2.0, c_upr(root+7, _k(1.5)), 0.42)            # to the fifth
    place('bass', bs + 3.5, c_upr(root, _k(0.5)), 0.35)

def brushes(bs):
    place('drm', bs + 0.0, brush_kick(), 0.8)
    place('drm', bs + 2.0, brush_kick(), 0.7)
    for beat in (1.0, 3.0):
        place('drm', bs + beat, brush_snare(), 0.5)
    for i in range(8):
        place('drm', bs + i*0.5 + (0.05 if i % 2 else 0.0), shaker(), 0.14)

def write_melody(start_beat, melody, gain=0.32):
    cur = start_beat
    for note, dur in melody:
        if note: place('lead', cur, c_lead(note, _k(dur*0.94)), gain)
        cur += dur

# --- melodies (D major) ----------------------------------------------------
# "How Great Thou Art" — public-domain Swedish folk tune "O Store Gud",
# transcribed to D major. Verse (narrow do-re-mi-fa range) for the intro,
# the soaring refrain ("...how great Thou art") for the outro reprise.
HYMN_INTRO = [  # verse: "O Lord my God, when I in awesome wonder / Consider all the worlds..."
    (62,1),(62,1),(64,1),(62,1),(66,1),(66,1),(67,1),(66,1),(64,1),(62,3),(0,4),
    (66,1),(66,1),(67,1),(66,1),(64,1),(62,1),(64,1),(66,1),(64,1),(62,3),(0,4)]
HYMN_OUTRO = [  # refrain: "Then sings my soul... how great Thou art, how great Thou art"
    (69,1),(69,1),(74,2),(78,2),(76,1),(74,1),(73,1),(74,1),(71,1),(69,3),(0,2),
    (74,1),(74,1),(73,2),(76,2),(78,2),(76,1),(74,1),(74,4),(0,2)]

CHORUS_MEL = [(69,1),(69,1),(71,2),(69,1),(66,1),(67,2),(69,1),(71,1),(74,2),(73,1),(71,1),(69,2),
              (71,1),(71,1),(73,2),(71,1),(69,1),(66,2),(67,1),(69,1),(71,2),(69,2),(0,2)]
BRIDGE_MEL = [(66,1),(67,1),(69,2),(69,1),(71,1),(73,2),(74,1),(73,1),(71,2),(69,2),(0,2),
              (71,1),(73,1),(74,2),(73,1),(71,1),(69,2),(74,2),(0,2),(76,4)]

MAIN   = ['D','A','Bm','G']
BRIDGE = ['Bm','G','D','A']
HYMN_IN_CH  = ['D','G','D','A','D','G','A','D']   # hymnal harmony under the verse
HYMN_OUT_CH = ['D','D','G','D','A','D','A','D']   # under the refrain, plagal "amen" close

# name, bars, per-bus level at section start, sparse-pick, melody, chord override
SECTIONS = [
    ('How Great Thou Art (intro)', 8, dict(drm=0.0, bass=0.0, strg=0.58, gtr=0.72, lead=0.62), True,  HYMN_INTRO, HYMN_IN_CH),
    ('Verse 1',  8, dict(drm=0.30,bass=0.7, strg=0.60, gtr=0.90, lead=0.0), False, None,       None),
    ('Verse 2',  8, dict(drm=0.52,bass=0.8, strg=0.70, gtr=0.95, lead=0.0), False, None,       None),
    ('Chorus',   8, dict(drm=1.0, bass=0.9, strg=0.95, gtr=1.00, lead=0.85),False, CHORUS_MEL, None),
    ('Interlude',4, dict(drm=0.9, bass=0.85,strg=0.85, gtr=1.00, lead=0.4), False, None,       None),
    ('Bridge',   8, dict(drm=0.7, bass=0.85,strg=0.90, gtr=0.95, lead=0.8), False, BRIDGE_MEL, None),
    ('Chorus 2', 8, dict(drm=1.0, bass=0.95,strg=1.00, gtr=1.00, lead=0.9), False, CHORUS_MEL, None),
    ('How Great Thou Art (outro)', 8, dict(drm=0.0, bass=0.0, strg=0.60, gtr=0.72, lead=0.66), True,  HYMN_OUTRO, HYMN_OUT_CH),
]

TOTAL_BEATS = 0
CTRL = {k: [] for k in ('drm', 'bass', 'strg', 'gtr', 'lead')}   # (beat, level)
for name, bars, lv, sparse, mel, chords in SECTIONS:
    start = TOTAL_BEATS
    for k in CTRL: CTRL[k].append((start, lv[k]))
    for bar in range(bars):
        bs = start + bar*4
        if chords is not None:      ch = chords[bar % len(chords)]
        elif name == 'Bridge':      ch = BRIDGE[bar % 4]
        else:                       ch = MAIN[bar % 4]
        fingerpick(bs, ch, sparse=sparse)
        pad_strings(bs, ch)
        bassline(bs, ch)
        brushes(bs)
    if mel is not None:
        write_melody(start, mel)
    TOTAL_BEATS += bars*4
for k in CTRL: CTRL[k].append((TOTAL_BEATS, CTRL[k][-1][1]))       # hold last

# --- render buses ----------------------------------------------------------
total_samples = b2s(TOTAL_BEATS) + int(SR*2.0)
def render_bus(name):
    buf = np.zeros(total_samples, dtype=np.float32)
    for start_beat, sig, gain in EVENTS[name]:
        i = b2s(start_beat); j = i + len(sig)
        if j > total_samples: sig = sig[:total_samples-i]; j = total_samples
        buf[i:j] += sig * gain
    return buf

# --- smooth automation curve for a bus -------------------------------------
BUS2CTRL = {'gtr':'gtr', 'str':'strg', 'bass':'bass', 'drm':'drm', 'lead':'lead'}
def automation(ctrl_key):
    pts = CTRL[ctrl_key]
    xs = np.array([b2s(b) for b, _ in pts], dtype=float)
    ys = np.array([v for _, v in pts], dtype=float)
    curve = np.interp(np.arange(total_samples), xs, ys)
    return movavg(curve, int(0.4*SR))                      # smooth ~0.4s (fast)

def movavg(x, width):
    """O(N) moving average via cumsum (fast box smoothing)."""
    k = max(1, int(width))
    c = np.cumsum(np.insert(x.astype(np.float64), 0, 0.0))
    out = np.empty_like(x, dtype=np.float64)
    half = k // 2
    padded = np.concatenate([np.full(half, x[0]), x, np.full(k - half, x[-1])])
    c = np.cumsum(np.insert(padded.astype(np.float64), 0, 0.0))
    return ((c[k:] - c[:-k]) / k)[:len(x)].astype(np.float32)

mix = np.zeros(total_samples, dtype=np.float32)
for bus in BUSES:
    mix += render_bus(bus) * automation(BUS2CTRL[bus])

# --- warm multi-tap reverb (hymnal space) ----------------------------------
def reverb(x):
    taps = [(0.011,0.55),(0.023,0.48),(0.037,0.40),(0.053,0.34),(0.079,0.27),
            (0.107,0.22),(0.149,0.17),(0.211,0.12),(0.290,0.09),(0.380,0.06)]
    wet = np.zeros_like(x)
    for d, g in taps:
        s = int(d*SR)
        wet[s:] += x[:len(x)-s] * g
    return movavg(wet, int(0.006*SR))                      # diffuse/soften (fast)
mix = mix + 0.32 * reverb(mix)

# --- gentle master ---------------------------------------------------------
def lowpass(x, width):
    k = max(1, int(width)); c = np.cumsum(np.insert(x, 0, 0.0))
    return (c[k:] - c[:-k]) / k
mix = lowpass(mix, 2)
mix = mix + 0.0025*rng.standard_normal(len(mix))           # subtle air
mix = np.tanh(1.1 * mix)
mix = mix / (np.max(np.abs(mix)) or 1.0) * 0.89

fi = int(1.2*SR); fo = int(4.0*SR)                         # slow hymnal fades
mix[:fi] *= np.linspace(0, 1, fi); mix[-fo:] *= np.linspace(1, 0, fo)

delay = 11
right = np.concatenate([np.zeros(delay, dtype=mix.dtype), mix[:-delay]]) * 0.97
stereo = np.clip(np.stack([mix, right], axis=1), -1, 1)

# --- write -----------------------------------------------------------------
out_mp3 = sys.argv[1] if len(sys.argv) > 1 else 'bigger_than_the_storm.mp3'
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
