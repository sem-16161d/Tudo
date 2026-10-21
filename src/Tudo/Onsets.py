# Onsets.py
"""
Onset detection modelled on FluCoMa's fluid.onsetslice~ / FluidBufOnsetSlice.

Parameters (FluCoMa names):
    metric          2       0 Energy          sum of squared magnitudes
                            1 HFC             high frequency content (bin-weighted energy)
                            2 SpectralFlux    half-rectified magnitude difference
                            3 MKL             (rectified) log magnitude ratio per bin
                            4 IS              Itakura-Saito divergence
                            5 Cosine          cosine distance between frames
                            6 PhaseDev        phase deviation from steady-state prediction
                            7 WPhaseDev       PhaseDev weighted by magnitude
                            8 ComplexDev      complex-domain deviation
                            9 RComplexDev     ComplexDev, rising bins only
    threshold       0.3     onset when the filtered curve rises above it
    minSliceLength  2       minimum distance between onsets, in hops
    filterSize      5       median filter (frames) subtracted from the curve
                            (adaptive threshold: steady levels are ignored)
    frameDelta      0       samples between compared frames for metrics
                            1, 2, 3, 4, 5 (0 = consecutive frames)
    windowSize      1024
    hopSize         -1      -1 = windowSize / 2
    fftSize         -1      -1 = next power of 2 >= windowSize

Additional:
    normalise       True    peak-normalise the file first, so the threshold
                            means the same for quiet and loud samples
    minLevelDb      -60     ignore frames more than this below the loudest
                            frame (decay tails, noise floor), None = off

Scale: magnitudes are scaled so a full-scale sine has magnitude 1.
SpectralFlux and the complex-domain metrics are divided by the frame's
magnitude sum, so they are level-independent and lie in 0..1 (1 = the
whole frame is new, e.g. a hit after silence). Energy/HFC are relative to
full scale. MKL and IS are unbounded and need much higher thresholds. The
parameters behave like FluCoMa's, but threshold values are not guaranteed to
be numerically identical to FluCoMa's (its internal scaling is not documented).
"""

import numpy as np
from scipy.fft import rfft
from scipy.signal.windows import hann

METRICS = ("Energy", "HFC", "SpectralFlux", "MKL", "IS", "Cosine",
           "PhaseDev", "WPhaseDev", "ComplexDev", "RComplexDev")

ONSET_DEFAULTS = dict(metric=2, threshold=0.3, minSliceLength=2, filterSize=5,
                      frameDelta=0, windowSize=1024, hopSize=-1, fftSize=-1,
                      normalise=True, minLevelDb=-60)

_EPS = 1e-10


def resolveOnsetSettings(settings=None):
    s = dict(ONSET_DEFAULTS)
    s.update(settings or {})
    win = int(s["windowSize"])
    s["hopSize"] = int(s["hopSize"]) if s["hopSize"] and s["hopSize"] > 0 else win // 2
    s["fftSize"] = int(s["fftSize"]) if s["fftSize"] and s["fftSize"] > 0 else int(2 ** np.ceil(np.log2(win)))
    if s["fftSize"] < win or s["fftSize"] & (s["fftSize"] - 1):
        raise ValueError("Onsets: fftSize must be a power of 2 >= windowSize")
    if int(s["metric"]) not in range(10):
        raise ValueError(f"Onsets: metric must be 0-9 ({', '.join(f'{i} {m}' for i, m in enumerate(METRICS))})")
    s["filterSize"] = max(1, int(s["filterSize"]) | 1)          # odd
    s["minSliceLength"] = max(1, int(s["minSliceLength"]))
    s.update(metric=int(s["metric"]), windowSize=win, threshold=float(s["threshold"]))
    return s


def _stft(x, win, hop, nfft):
    pad = win // 2
    x = np.pad(np.asarray(x, dtype=float), (pad, pad))
    if len(x) < win:
        x = np.pad(x, (0, win - len(x)))
    n = 1 + (len(x) - win) // hop
    w = hann(win, sym=False)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    X = rfft(x[idx] * w, n=nfft, axis=1).T * (2.0 / w.sum())   # sine of amp 1 -> |X| = 1
    return X                                                     # (bins, frames), frame i at i*hop


def _princarg(p):
    return (p + np.pi) % (2 * np.pi) - np.pi


def onsetFunction(signal, sr, settings=None):
    """Raw onset detection function, one value per hop. Returns (odf, settings)."""
    s = resolveOnsetSettings(settings)
    x = np.asarray(signal, dtype=float)
    if s["normalise"]:
        peak = np.max(np.abs(x)) if len(x) else 0
        if peak > 0:
            x = x / peak
    X = _stft(x, s["windowSize"], s["hopSize"], s["fftSize"])
    mag = np.abs(X)
    K, n = mag.shape
    metric = s["metric"]
    d = max(1, 1 + int(round(s["frameDelta"] / s["hopSize"]))) if s["frameDelta"] else 1

    def prev(a, lag=1):
        out = np.zeros_like(a)
        out[:, lag:] = a[:, :-lag] if lag < a.shape[1] else 0
        return out

    if metric == 0:                                   # Energy
        odf = (mag ** 2).sum(axis=0)
    elif metric == 1:                                 # HFC
        k = np.arange(K)[:, None] / K
        odf = (k * mag ** 2).sum(axis=0)
    elif metric == 2:                                 # SpectralFlux
        odf = np.maximum(mag - prev(mag, d), 0).sum(axis=0) / (mag.sum(axis=0) + _EPS)
    elif metric == 3:                                 # MKL
        odf = np.maximum(np.log((mag + _EPS) / (prev(mag, d) + _EPS)), 0).mean(axis=0)
    elif metric == 4:                                 # Itakura-Saito
        P, Pp = mag ** 2 + _EPS, prev(mag, d) ** 2 + _EPS
        r = P / Pp
        odf = (r - np.log(r) - 1).mean(axis=0)
    elif metric == 5:                                 # Cosine
        mp = prev(mag, d)
        num = (mag * mp).sum(axis=0)
        den = np.linalg.norm(mag, axis=0) * np.linalg.norm(mp, axis=0)
        odf = np.where(den > _EPS, 1 - num / np.maximum(den, _EPS), 0.0)
        odf[np.linalg.norm(mp, axis=0) <= _EPS] = 0.0
        odf[(np.linalg.norm(mp, axis=0) <= _EPS) & (np.linalg.norm(mag, axis=0) > _EPS)] = 1.0
    else:                                             # phase / complex domain
        ph = np.angle(X)
        ph1, ph2 = prev(ph, 1), prev(ph, 2)
        dev = np.abs(_princarg(ph - 2 * ph1 + ph2))
        if metric == 6:                               # PhaseDev
            odf = dev.mean(axis=0) / np.pi
        elif metric == 7:                             # WPhaseDev
            odf = (mag * dev).sum(axis=0) / (mag.sum(axis=0) + _EPS) / np.pi
        else:
            m1 = prev(mag, 1)
            pred = m1 * np.exp(1j * (2 * ph1 - ph2))
            diff = np.abs(X - pred)
            if metric == 9:                           # RComplexDev: rising bins only
                diff = np.where(mag >= m1, diff, 0.0)
            odf = diff.sum(axis=0) / (mag.sum(axis=0) + m1.sum(axis=0) + _EPS)
    s["_frameEnergy"] = (mag ** 2).sum(axis=0)
    s["_numSamples"] = len(x)
    return odf, s


def _causalMedian(x, size):
    if size <= 1:
        return np.zeros_like(x)
    pad = np.concatenate([np.zeros(size - 1), x])        # silence before the file
    windows = np.lib.stride_tricks.sliding_window_view(pad, size)
    return np.median(windows, axis=1)


def detectOnsets(signal, sr, settings=None):
    """
    Returns (onsetTimesSec, info). info holds the settings, the raw and the
    filtered onset function and the frame rate.
    """
    odf, s = onsetFunction(signal, sr, settings)
    energy = s.pop("_frameEnergy")
    numSamples = s.pop("_numSamples")
    filtered = odf - _causalMedian(odf, s["filterSize"])
    above = filtered > s["threshold"]
    if s["minLevelDb"] is not None and energy.max() > 0:
        above &= 10 * np.log10(energy / energy.max() + 1e-30) >= s["minLevelDb"]
    # frames that reach past the end of the file see the abrupt cut, not an onset
    frameEnd = np.arange(len(above)) * s["hopSize"] + s["windowSize"] // 2
    above &= ~((frameEnd > numSamples) & (np.arange(len(above)) > 0))
    onsets, last = [], -10 ** 9
    for i in range(len(above)):
        rising = above[i] and (i == 0 or not above[i - 1])
        if rising and i - last >= s["minSliceLength"]:
            onsets.append(i)
            last = i
    duration = len(signal) / sr
    times = [min(i * s["hopSize"] / sr, duration) for i in onsets]
    return times, dict(settings=s, odf=odf, filtered=filtered, frameRate=sr / s["hopSize"])


def onsetMetrics(times, durationSec):
    """numOnsets, onsetRate, ioiMeanSec, ioiRegularity (1 = perfectly even)."""
    n = len(times)
    out = dict(numOnsets=n, onsetTimes=[round(float(t), 5) for t in times],
               onsetRate=n / durationSec if durationSec > 0 else 0.0,
               ioiMeanSec=None, ioiRegularity=None)
    if n >= 2:
        ioi = np.diff(times)
        out["ioiMeanSec"] = float(ioi.mean())
    if n >= 3:
        ioi = np.diff(times)
        cv = ioi.std() / ioi.mean() if ioi.mean() > 0 else 1.0
        out["ioiRegularity"] = float(np.clip(1.0 - cv, 0.0, 1.0))
    return out
