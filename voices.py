"""Multi-voice Piper TTS helper. Resamples every clip to a common rate and
supports a pitch tweak (used to make the kid's voice younger)."""

import numpy as np

SR = 22050
_V = {}
_PATHS = {
    "ty": ("voices/en-us-ryan-high.onnx", "voices/en-us-ryan-high.onnx.json"),
    "mia": ("voices/en-us-amy-low.onnx", "voices/en-us-amy-low.onnx.json"),
}


def _load(name):
    from piper import PiperVoice
    if name not in _V:
        p, c = _PATHS[name]
        _V[name] = PiperVoice.load(p, config_path=c)
    return _V[name]


def _resample(a, src, dst):
    if src == dst or len(a) == 0:
        return a
    n = int(len(a) * dst / src)
    return np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)


def synth(voice, text, pitch=1.0):
    """Return float32 mono audio at SR for `text` spoken by `voice`."""
    v = _load(voice)
    sr = getattr(v.config, "sample_rate", SR)
    frames = []
    for ch in v.synthesize(text):
        b = getattr(ch, "audio_int16_bytes", None)
        if b is None:
            arr = getattr(ch, "audio_int16_array", None)
            b = arr.tobytes() if arr is not None else \
                (np.clip(ch.audio_float_array, -1, 1) * 32767).astype("<i2").tobytes()
        frames.append(b)
    a = np.frombuffer(b"".join(frames), dtype="<i2").astype(np.float32) / 32768.0
    a = _resample(a, sr, SR)
    if abs(pitch - 1.0) > 0.01 and len(a):
        idx = np.arange(0, len(a), pitch)
        a = np.interp(idx, np.arange(len(a)), a).astype(np.float32)
    return a
