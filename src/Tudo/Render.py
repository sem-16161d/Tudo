# Render.py
"""
Render several sound files into one file, all playing at the same time.
"""

import os
from math import gcd

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def _load(path, sr, channels):
    x, fileSr = sf.read(path, always_2d=True, dtype="float64")   # (frames, ch)
    if fileSr != sr:
        g = gcd(int(fileSr), int(sr))
        x = resample_poly(x, int(sr) // g, int(fileSr) // g, axis=0)
    if x.shape[1] == channels:
        return x
    if channels == 1:
        return x.mean(axis=1, keepdims=True)
    if x.shape[1] == 1:
        return np.repeat(x, channels, axis=1)
    return x[:, :channels] if x.shape[1] > channels else \
        np.concatenate([x, np.repeat(x[:, -1:], channels - x.shape[1], axis=1)], axis=1)


def _firstOnset(x, sr):
    """Time (s) of the first onset, using Tudo's onset detection."""
    from Tudo.Onsets import detectOnsets
    times, _ = detectOnsets(x.mean(axis=1), sr)
    return times[0] if times else 0.0


def mixFiles(paths, outPath, *, sr=48000, channels=2, align="start",
             normaliseEach=True, gains=None, spread=0.0, peakDb=-1.0,
             maxDurationSec=None, fadeOutSec=0.05):
    """
    Mix sound files so they all play at the same time.

    paths         : list of file paths
    outPath       : output file (.wav, .aif, .flac)
    sr, channels  : output format (files are resampled / up- or down-mixed)
    align         : "start" = all files start at 0
                    "onset" = the first onsets coincide (files with a late
                              attack are moved earlier, the others delayed)
    normaliseEach : bring every file to the same peak before mixing, so loud
                    files don't cover the quiet ones
    gains         : optional list of extra gains in dB, one per file
    spread        : 0 = all centred, 1 = files spread from left to right
                    (equal-power panning, stereo output only)
    peakDb        : peak level of the final mix in dBFS (no clipping)
    maxDurationSec: cut the mix after this time (with a short fade-out)

    Returns (outPath, info) with the offsets used per file.
    """
    paths = [p for p in paths if p]
    if not paths:
        raise ValueError("Render.mixFiles: no files")
    layers, onsets = [], []
    for p in paths:
        x = _load(p, sr, channels)
        if normaliseEach:
            peak = np.max(np.abs(x))
            if peak > 0:
                x = x / peak
        layers.append(x)
        onsets.append(_firstOnset(x, sr) if align == "onset" else 0.0)
    if align not in ("start", "onset"):
        raise ValueError("Render.mixFiles: align must be 'start' or 'onset'")

    # offsets so that all first onsets land on the latest one
    ref = max(onsets)
    offsets = [int(round((ref - o) * sr)) for o in onsets]
    length = max(off + len(x) for off, x in zip(offsets, layers))
    if maxDurationSec:
        length = min(length, int(maxDurationSec * sr))
    mix = np.zeros((length, channels))

    n = len(layers)
    for i, (x, off) in enumerate(zip(layers, offsets)):
        g = 10 ** ((gains[i] if gains else 0.0) / 20)
        if channels == 2 and spread and n > 1:
            pos = (i / (n - 1) - 0.5) * spread + 0.5            # 0 = left, 1 = right
            pan = np.array([np.cos(pos * np.pi / 2), np.sin(pos * np.pi / 2)]) * np.sqrt(2)
            x = x * pan
        end = min(length, off + len(x))
        if end > off:
            mix[off:end] += g * x[:end - off]

    if maxDurationSec and fadeOutSec:
        k = min(len(mix), int(fadeOutSec * sr))
        mix[-k:] *= np.linspace(1, 0, k)[:, None]
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix *= 10 ** (peakDb / 20) / peak

    os.makedirs(os.path.dirname(os.path.abspath(outPath)), exist_ok=True)
    fmt = {".aif": "AIFF", ".aiff": "AIFF", ".wav": "WAV", ".flac": "FLAC"}.get(
        os.path.splitext(outPath)[1].lower())
    sf.write(outPath, mix if channels > 1 else mix[:, 0], sr, format=fmt,
             subtype="PCM_24" if fmt in ("AIFF", "WAV", "FLAC") else None)
    info = dict(files=paths, offsetsSec=[o / sr for o in offsets],
                durationSec=length / sr, sampleRate=sr, channels=channels)
    return outPath, info
