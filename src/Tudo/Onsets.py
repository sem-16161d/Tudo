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
    relativeFloorDb -25     relative metrics (SpectralFlux, Complex*) are divided
                            by the frame's magnitude sum, but by no less than
                            this level below the loudest frame, so noise
                            before the sound doesn't count as an onset
    filterLag       0       the median baseline ends this many frames before
                            the current frame. 0 = FluCoMa-like; e.g. 5 also
                            catches gradual onsets (legato note changes,
                            ~60-100 ms rises) at the cost of a few extra
                            onsets in fluctuating noise

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
                      normalise=True, minLevelDb=-60, relativeFloorDb=-25, filterLag=0)

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
    # relative metrics are divided by the frame's magnitude sum, but never by
    # less than relativeFloorDb below the loudest frame: otherwise a little
    # noise before the sound counts as "100 % new"
    msum = mag.sum(axis=0)
    floor = msum.max() * 10 ** (s["relativeFloorDb"] / 20) if msum.max() > 0 else _EPS
    norm = np.maximum(msum, floor)
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
        odf = np.maximum(mag - prev(mag, d), 0).sum(axis=0) / norm
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
            odf = diff.sum(axis=0) / (norm + np.maximum(m1.sum(axis=0), floor))
    s["_frameEnergy"] = (mag ** 2).sum(axis=0)
    s["_numSamples"] = len(x)
    return odf, s


def _causalMedian(x, size, lag=0):
    """Median of the `size` frames ending `lag` frames before each frame."""
    if size <= 1:
        return np.zeros_like(x)
    pad = np.concatenate([np.zeros(size - 1 + lag), x])  # silence before the file
    windows = np.lib.stride_tricks.sliding_window_view(pad, size)[:len(x)]
    return np.median(windows, axis=1)


def detectOnsets(signal, sr, settings=None):
    """
    Returns (onsetTimesSec, info). info holds the settings, the raw and the
    filtered onset function and the frame rate.
    """
    odf, s = onsetFunction(signal, sr, settings)
    energy = s.pop("_frameEnergy")
    numSamples = s.pop("_numSamples")
    lag = s["filterSize"] if s["filterLag"] is None else int(s["filterLag"])
    filtered = odf - _causalMedian(odf, s["filterSize"], lag)
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


def plotOnsets(signal, sr, times, info=None, title="", savePath=None, show=True):
    """
    Waveform with onset markers; if `info` from detectOnsets() is given,
    a second panel shows the onset function, its filtered version and the
    threshold. Returns the matplotlib figure.
    """
    import matplotlib.pyplot as plt
    x = np.asarray(signal, dtype=float)
    t = np.arange(len(x)) / sr
    rows = 2 if info is not None else 1
    fig, axes = plt.subplots(rows, 1, figsize=(12, 3.2 * rows), sharex=True, squeeze=False)
    ax = axes[0, 0]
    ax.plot(t, x, color="0.35", linewidth=0.5)
    for i, o in enumerate(times):
        ax.axvline(o, color="crimson", linewidth=1.2)
        ax.text(o, 1.02, str(i + 1), color="crimson", fontsize=8, ha="center",
                transform=ax.get_xaxis_transform())
    ax.set_ylabel("amplitude")
    ax.set_title(f"{title}   {len(times)} onsets" if title else f"{len(times)} onsets", loc="left")
    ax.margins(x=0)
    if info is not None:
        s = info["settings"]
        ft = np.arange(len(info["odf"])) * s["hopSize"] / sr
        ax2 = axes[1, 0]
        ax2.plot(ft, info["odf"], color="0.6", linewidth=0.8, label="onset function")
        ax2.plot(ft, info["filtered"], color="tab:blue", linewidth=1.0, label="filtered (minus median)")
        ax2.axhline(s["threshold"], color="crimson", linestyle="--", linewidth=1.0,
                    label=f"threshold {s['threshold']}")
        for o in times:
            ax2.axvline(o, color="crimson", linewidth=0.6, alpha=0.5)
        ax2.set_ylabel(METRICS[s["metric"]])
        ax2.legend(loc="upper right", fontsize=8)
        ax2.margins(x=0)
    axes[-1, 0].set_xlabel("time (s)")
    fig.tight_layout()
    if savePath:
        fig.savefig(savePath, dpi=130)
    if show:
        plt.show()
    return fig
