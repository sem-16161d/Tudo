# Render.py
"""
Render several sound files into one file, all playing at the same time.
"""

import os
from fractions import Fraction
from math import gcd, log2

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


def _transpose(x, ratio):
    """Varispeed by `ratio` (2 = one octave up, half as long). Returns (x, semitones)."""
    # shortcut: ratio rounded to a fraction with denominator <= 1000 (< 1 cent error)
    frac = Fraction(1 / ratio).limit_denominator(1000)
    if frac == 1:
        return x, 0.0
    y = resample_poly(x, frac.numerator, frac.denominator, axis=0)
    return y, 12 * log2(frac.denominator / frac.numerator)


def _pan(x, i, n, spread, channels):
    """Equal-power position of file i of n (stereo only)."""
    if channels != 2 or not spread or n < 2:
        return x
    pos = (i / (n - 1) - 0.5) * spread + 0.5            # 0 = left, 1 = right
    return x * (np.array([np.cos(pos * np.pi / 2), np.sin(pos * np.pi / 2)]) * np.sqrt(2))


def _fadeOut(x, sr, fadeOutSec):
    k = min(len(x), int(fadeOutSec * sr))
    if k > 0:
        x[-k:] *= np.linspace(1, 0, k)[:, None]


def _toPeak(x, peakDb):
    peak = np.max(np.abs(x)) if len(x) else 0
    return x * (10 ** (peakDb / 20) / peak) if peak > 0 else x


def _write(path, x, sr, channels):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fmt = {".aif": "AIFF", ".aiff": "AIFF", ".wav": "WAV", ".flac": "FLAC"}.get(
        os.path.splitext(path)[1].lower())
    sf.write(path, x if channels > 1 else x[:, 0], sr, format=fmt,
             subtype="PCM_24" if fmt in ("AIFF", "WAV", "FLAC") else None)


def _renderSingleFiles(paths, layers, outPath, sr, channels, gains, spread,
                       peakDb, maxDurationSec, fadeOutSec):
    folder = os.path.join(os.path.dirname(os.path.abspath(outPath)), "SINGLE_FILES")
    written, n = [], len(layers)
    for i, (p, x) in enumerate(zip(paths, layers)):
        x = _pan(x * 10 ** ((gains[i] if gains else 0.0) / 20), i, n, spread, channels)
        if maxDurationSec:
            x = x[:int(maxDurationSec * sr)].copy()
            if fadeOutSec:
                _fadeOut(x, sr, fadeOutSec)
        stem = os.path.splitext(os.path.basename(p))[0] + "_rendered"
        out = os.path.join(folder, stem + ".wav")
        k = 2
        while out in written:                      # same name from different folders
            out = os.path.join(folder, f"{stem}_{k}.wav")
            k += 1
        _write(out, _toPeak(x, peakDb), sr, channels)
        written.append(out)
    durations = [len(x) / sr for x in layers]
    if maxDurationSec:
        durations = [min(d, maxDurationSec) for d in durations]
    info = dict(files=paths, outputs=written, offsetsSec=[0.0] * n,
                durationSec=max(durations), sampleRate=sr, channels=channels)
    return folder, info


def mixFiles(paths, outPath, *, sr=48000, channels=2, align="start",
             normaliseEach=True, gains=None, spread=0.0, peakDb=-1.0,
             maxDurationSec=None, fadeOutSec=0.05, forceMainPitch=False,
             mainPitches=None):
    """
    Mix sound files so they all play at the same time.

    paths         : list of file paths
    outPath       : output file (.wav, .aif, .flac)
    sr, channels  : output format (files are resampled / up- or down-mixed)
    align         : "start" = all files start at 0
                    "onset" = the first onsets coincide (files with a late
                              attack are moved earlier, the others delayed)
                    "singleFiles" = no mix: every file is rendered on its own
                              (same format, gains, spread, peakDb,
                              maxDurationSec) into a SINGLE_FILES folder next
                              to outPath as <originalname>_rendered.wav
    normaliseEach : bring every file to the same peak before mixing, so loud
                    files don't cover the quiet ones
    gains         : optional list of extra gains in dB, one per file
    spread        : 0 = all centred, 1 = files spread from left to right
                    (equal-power panning, stereo output only)
    peakDb        : peak level of the final mix in dBFS (no clipping)
    maxDurationSec: cut the mix after this time (with a short fade-out)
    forceMainPitch: False, or a frequency in Hz: every file is transposed
                    (varispeed, like a sampler: higher = shorter) so that its
                    main pitch lands on this frequency
    mainPitches   : main pitch in Hz per file (needed for forceMainPitch;
                    None entries are left untransposed)

    Returns (outPath, info) with the offsets used per file
    (singleFiles: (SINGLE_FILES folder, info with the written files)).
    """
    paths = [p for p in paths if p]
    if not paths:
        raise ValueError("Render.mixFiles: no files")
    if forceMainPitch and mainPitches is None:
        raise ValueError("Render.mixFiles: forceMainPitch needs mainPitches (one per file)")
    layers, onsets, semitones = [], [], []
    for i, p in enumerate(paths):
        x = _load(p, sr, channels)
        st = 0.0
        if forceMainPitch and mainPitches[i]:
            x, st = _transpose(x, float(forceMainPitch) / float(mainPitches[i]))
        semitones.append(st)
        if normaliseEach:
            peak = np.max(np.abs(x))
            if peak > 0:
                x = x / peak
        layers.append(x)
        onsets.append(_firstOnset(x, sr) if align == "onset" else 0.0)
    if align not in ("start", "onset", "singleFiles"):
        raise ValueError("Render.mixFiles: align must be 'start', 'onset' or 'singleFiles'")
    if align == "singleFiles":
        folder, info = _renderSingleFiles(paths, layers, outPath, sr, channels, gains,
                                          spread, peakDb, maxDurationSec, fadeOutSec)
        info["transposeSemitones"] = semitones
        return folder, info

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
        x = _pan(x, i, n, spread, channels)
        end = min(length, off + len(x))
        if end > off:
            mix[off:end] += g * x[:end - off]

    if maxDurationSec and fadeOutSec:
        _fadeOut(mix, sr, fadeOutSec)
    _write(outPath, _toPeak(mix, peakDb), sr, channels)
    info = dict(files=paths, transposeSemitones=semitones, offsetsSec=[o / sr for o in offsets],
                durationSec=length / sr, sampleRate=sr, channels=channels)
    return outPath, info
