# DynamicProfile.py
"""
Automatic dynamic-profile description after

    G. Peeters & E. Deruty (2008): "Automatic morphological description
    of sounds", Acoustics'08 Paris, section 3.1.

The sound is assumed to be unitary (one event). It is described by
five features and sorted into one of five classes:

    ascending | descending | ascending/descending | stable | impulsive

Pipeline (paper Fig. 2):
    1. instantaneous loudness l(t)
    2. low-pass filter (fc = 1 Hz)
    3. noise threshold at 10 % of l(tM)  ->  ts, te
    4. locate maximum tM
    5. log-scale
    6. second-order (= piecewise-linear) B-spline with knots ts, tM, te,
       fitted by least squares on a normalised time axis [0, 1]
    7. read slopes / relative durations from the spline

Features:
    S1  slope before tM          RD1  relative duration before tM
    S2  slope after tM           RD2  relative duration after tM
    ED  temporal effective duration (time l(t) > 40 % of max, relative)

Only numpy + scipy, so it can be tested without librosa.
"""

import numpy as np
from scipy.signal import butter, sosfiltfilt, stft

PROFILES = ("ascending", "descending", "ascending/descending",
            "stable", "impulsive")

# Bark band edges in Hz (Zwicker), used for the specific loudness
_BARK_EDGES = np.array([
    0, 100, 200, 300, 400, 510, 630, 770, 920, 1080, 1270, 1480, 1720,
    2000, 2320, 2700, 3150, 3700, 4400, 5300, 6400, 7700, 9500, 12000,
    15500, 20500])


# ----------------------------------------------------------------------
# 1. loudness
# ----------------------------------------------------------------------
def instantaneousLoudness(signal, sr, hopSec=0.01, winSec=0.04):
    """
    AudioLoudness as in the CUIDADO feature set (Peeters 2004):
    energy per Bark band E(z), specific loudness N'(z) = E(z)^0.23,
    total loudness N = sum_z N'(z). One value every `hopSec`.

    Returns (loudness, frameRate).
    """
    signal = np.asarray(signal, dtype=float)
    if signal.ndim > 1:                       # mixdown
        signal = signal.mean(axis=0 if signal.shape[0] < signal.shape[1] else 1)
    hop = max(1, int(round(hopSec * sr)))
    nfft = int(2 ** np.ceil(np.log2(max(winSec * sr, 64))))
    freqs, _, Z = stft(signal, fs=sr, window="hann", nperseg=nfft,
                       noverlap=nfft - hop, boundary="even", padded=True)
    power = np.abs(Z) ** 2

    edges = _BARK_EDGES[_BARK_EDGES < sr / 2]
    edges = np.append(edges, sr / 2)
    bandIdx = np.digitize(freqs, edges) - 1
    loud = np.zeros(power.shape[1])
    for b in range(len(edges) - 1):
        rows = bandIdx == b
        if rows.any():
            loud += power[rows].sum(axis=0) ** 0.23
    return loud, sr / hop


# ----------------------------------------------------------------------
# 2.-7. features
# ----------------------------------------------------------------------
def _lowpass(x, frameRate, cutoffHz):
    if cutoffHz is None or cutoffHz >= frameRate / 2:
        return x.copy()
    sos = butter(2, cutoffHz / (frameRate / 2), output="sos")
    padlen = min(len(x) - 1, 3 * (2 * len(sos) + 1) * 4)
    if len(x) < 8:
        return x.copy()
    return np.maximum(sosfiltfilt(sos, x, padlen=padlen), 0.0)


def _linearSpline(t, y, knots):
    """Least-squares fit of a continuous piecewise-linear function
    (2nd-order B-spline) with the given knots. Returns values at knots."""
    knots = np.asarray(knots, dtype=float)
    B = np.zeros((len(t), len(knots)))
    for i, k in enumerate(knots):
        left = knots[i - 1] if i > 0 else None
        right = knots[i + 1] if i < len(knots) - 1 else None
        b = np.zeros(len(t))
        if left is not None:
            m = (t >= left) & (t <= k)
            b[m] = (t[m] - left) / (k - left)
        if right is not None:
            m = (t >= k) & (t <= right)
            b[m] = (right - t[m]) / (right - k)
        b[np.isclose(t, k)] = 1.0
        B[:, i] = b
    coef, *_ = np.linalg.lstsq(B, y, rcond=None)
    return coef


def dynamicProfileFeatures(signal, sr, *, lowpassHz=1.0, noiseThreshold=0.1,
                           effDurThreshold=0.4, hopSec=0.01,
                           timeBase="active", maxTolerance=1.0):
    """
    Compute S1, RD1, S2, RD2, ED.

    timeBase : "active" -> time axis [0, 1] spans ts..te (the part above
               the 10 % noise threshold), so leading/trailing silence in
               a sample file doesn't distort the result.
               "file"   -> time axis spans the whole file.

    maxTolerance : 1.0 = tM is the exact maximum (as in the paper).
               < 1 (e.g. 0.9) = tM is the FIRST frame that reaches
               maxTolerance * max. Makes flat sounds more robust,
               where the exact maximum can land anywhere.

    Returns a dict (also includes intermediate curves for plotting).
    """
    loud, frameRate = instantaneousLoudness(signal, sr, hopSec=hopSec)
    n = len(loud)
    result = dict(slope1=0.0, relDur1=0.0, slope2=0.0, relDur2=0.0,
                  effDur=0.0, loudness=loud, frameRate=frameRate)
    if n < 3 or loud.max() <= 0:
        return result

    smooth = _lowpass(loud, frameRate, lowpassHz)
    iM = int(np.argmax(smooth))
    lM = smooth[iM]
    if maxTolerance < 1.0:
        iM = int(np.flatnonzero(smooth >= maxTolerance * lM)[0])
    if lM <= 0:
        return result

    above = np.flatnonzero(smooth >= noiseThreshold * lM)
    iS, iE = int(above[0]), int(above[-1])

    # normalised time axis
    if timeBase == "file":
        t = np.arange(n) / max(n - 1, 1)
    else:
        t = (np.arange(n) - iS) / max(iE - iS, 1)
    ts, tM, te = t[iS], t[iM], t[iE]
    span = te - ts if te > ts else 1.0

    # log-scale (relative to the maximum, so l(tM) = 0)
    seg = slice(iS, iE + 1)
    logL = np.log(np.maximum(smooth[seg], 1e-12) / lM)
    tt = t[seg]

    knots = [k for k in (ts, tM, te)]
    # degenerate cases: maximum at the very start or end
    if np.isclose(tM, ts) or np.isclose(tM, te):
        knots = [ts, te]
        c = _linearSpline(tt, logL, knots)
        s = (c[1] - c[0]) / span
        if np.isclose(tM, ts):          # only decay
            result.update(slope1=0.0, relDur1=0.0, slope2=s, relDur2=1.0)
        else:                            # only rise
            result.update(slope1=s, relDur1=1.0, slope2=0.0, relDur2=0.0)
    else:
        c = _linearSpline(tt, logL, knots)
        result.update(
            slope1=(c[1] - c[0]) / (tM - ts), relDur1=(tM - ts) / span,
            slope2=(c[2] - c[1]) / (te - tM), relDur2=(te - tM) / span)
        result["splineKnots"] = (np.array(knots), c)

    # temporal effective duration on the unsmoothed loudness
    if timeBase == "file":
        result["effDur"] = float(np.mean(loud >= effDurThreshold * loud.max()))
    else:
        act = loud[seg]
        result["effDur"] = float(np.mean(act >= effDurThreshold * loud.max()))

    result.update(smoothLoudness=smooth, tMaxSec=iM / frameRate,
                  tStartSec=iS / frameRate, tEndSec=iE / frameRate)
    for k in ("slope1", "relDur1", "slope2", "relDur2", "effDur"):
        result[k] = float(result[k])
    return result


# ----------------------------------------------------------------------
# classification (paper Table 1, PART rules, applied in order)
# ----------------------------------------------------------------------
def classifyDynamicProfile(f):
    S1, RD1, S2, ED = f["slope1"], f["relDur1"], f["slope2"], f["effDur"]
    if ED > 0.28 and RD1 <= 0.214286 and S2 <= -0.584657:
        return "descending"
    if ED > 0.28 and -1.287156 < S2 <= 6.022541:
        return "stable"
    if ED <= 0.28:
        return "impulsive"
    if RD1 > 0.73991 and S1 > 0.403746:
        return "ascending"
    if S1 > 0.972048:
        return "ascending/descending"
    return "unclassified"


def dynamicProfile(signal, sr, **kwargs):
    """Features + class in one go. Returns (profile, features)."""
    f = dynamicProfileFeatures(signal, sr, **kwargs)
    return classifyDynamicProfile(f), f
