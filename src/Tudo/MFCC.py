# MFCC.py
"""
MFCC analysis with the same parameters as FluCoMa's fluid.mfcc~ /
FluidMFCC / FluidBufMFCC:

    numCoeffs   (13)     number of coefficients returned
    numBands    (40)     mel bands between minFreq and maxFreq
    startCoeff  (0)      lowest coefficient returned (1 = drop c0 / energy)
    minFreq     (20)     Hz
    maxFreq     (20000)  Hz (clipped to Nyquist)
    windowSize  (1024)   samples
    hopSize     (-1)     samples, -1 = windowSize / 2
    fftSize     (-1)     samples, -1 = next power of 2 >= windowSize;
                         larger values oversample the spectrum
    padding     (1)      0 = none, 1 = windowSize/2 on each end,
                         2 = windowSize - hopSize on each end

Additional (not in FluCoMa):
    analysisSampleRate (None)  resample before analysis, so that sizes in
                               samples mean the same time for 44.1k and 48k
    normalizeBands     (True)  area-normalise the mel filters (like
                               FluidMelBands' normalize, the default there)

With startCoeff = 1 the coefficients are c1 ... c(numCoeffs), i.e. FluCoMa
semantics: numCoeffs is the number returned, startCoeff only shifts them.

Pipeline: Hann window -> |FFT| -> mel bands -> dB -> DCT-II (orthonormal).
The parameters behave like FluCoMa's, but the absolute scale of the values
is not guaranteed to be identical to FluCoMa's output.

This module also holds the attack / sustain "slots": fixed-size MFCC
matrices meant as neural-network training data.
"""

import numpy as np
from math import gcd
from scipy.fft import dct, rfft
from scipy.signal import resample_poly
from scipy.signal.windows import hann

from Tudo.SpectralFeatures import barkLoudness, summariseTrack
from Tudo.DynamicProfile import instantaneousLoudness

_EPS = 1e-12

FLUCOMA_DEFAULTS = dict(
    numCoeffs=13, numBands=40, startCoeff=0, minFreq=20.0, maxFreq=20000.0,
    windowSize=1024, hopSize=-1, fftSize=-1, padding=1,
    analysisSampleRate=None, normalizeBands=True)

# summary columns (specMfccMain / FluctRate / ...): 40 coeffs without c0
SUMMARY_DEFAULTS = dict(FLUCOMA_DEFAULTS, numCoeffs=40, startCoeff=1,
                        numBands=128, windowSize=2048, hopSize=1024,
                        fftSize=4096)

# attack slot: ~256 ms from the onset at 4 ms resolution
ATTACK_DEFAULTS = dict(FLUCOMA_DEFAULTS, numCoeffs=40, startCoeff=1,
                       numBands=128, windowSize=1024, hopSize=192,
                       fftSize=4096, analysisSampleRate=48000,
                       numFrames=64, prerollSec=0.015)

# sustain slot: ~2.56 s after the attack at 10 ms resolution
SUSTAIN_DEFAULTS = dict(FLUCOMA_DEFAULTS, numCoeffs=40, startCoeff=1,
                        numBands=128, windowSize=2048, hopSize=480,
                        fftSize=4096, analysisSampleRate=48000,
                        numFrames=256)


# ----------------------------------------------------------------------
# settings
# ----------------------------------------------------------------------
def resolveSettings(settings, sr):
    """Fill in defaults, resolve -1 values, check FluCoMa's constraints.
    `sr` is the sample rate the analysis runs at."""
    s = dict(FLUCOMA_DEFAULTS)
    s.update(settings or {})
    win = int(s["windowSize"])
    hop = int(s["hopSize"]) if s["hopSize"] and s["hopSize"] > 0 else win // 2
    fft = int(s["fftSize"]) if s["fftSize"] and s["fftSize"] > 0 else int(2 ** np.ceil(np.log2(win)))
    if fft & (fft - 1) or fft < 4 or fft < win:
        raise ValueError(f"MFCC: fftSize must be a power of 2, >= 4 and >= windowSize ({win}), got {fft}")
    nb, nc, st = int(s["numBands"]), int(s["numCoeffs"]), int(s["startCoeff"])
    if nc < 2:
        raise ValueError("MFCC: numCoeffs must be >= 2")
    if st not in (0, 1):
        raise ValueError("MFCC: startCoeff must be 0 or 1")
    if nb < max(nc + st, 2):
        raise ValueError(f"MFCC: numBands ({nb}) must be >= numCoeffs + startCoeff ({nc + st})")
    if nb > fft // 2 + 1:
        raise ValueError(f"MFCC: numBands ({nb}) must be <= fftSize/2 + 1 ({fft // 2 + 1})")
    if int(s["padding"]) not in (0, 1, 2):
        raise ValueError("MFCC: padding must be 0, 1 or 2")
    maxF = min(float(s["maxFreq"]), sr / 2)
    minF = max(0.0, float(s["minFreq"]))
    if minF >= maxF:
        raise ValueError(f"MFCC: minFreq ({minF}) must be below maxFreq ({maxF})")
    s.update(windowSize=win, hopSize=hop, fftSize=fft, numBands=nb,
             numCoeffs=nc, startCoeff=st, minFreq=minF, maxFreq=maxF,
             padding=int(s["padding"]))
    return s


def _resample(signal, sr, targetSr):
    if not targetSr or int(targetSr) == int(sr):
        return np.asarray(signal, dtype=float), sr
    g = gcd(int(sr), int(targetSr))
    return resample_poly(signal, int(targetSr) // g, int(sr) // g), int(targetSr)


# ----------------------------------------------------------------------
# core
# ----------------------------------------------------------------------
def melFilterbank(fftSize, sr, numBands, minFreq, maxFreq, normalize=True):
    freqs = np.arange(fftSize // 2 + 1) * sr / fftSize
    mel = lambda f: 2595.0 * np.log10(1.0 + f / 700.0)
    imel = lambda m: 700.0 * (10 ** (m / 2595.0) - 1.0)
    pts = imel(np.linspace(mel(minFreq), mel(maxFreq), numBands + 2))
    fb = np.zeros((numBands, len(freqs)))
    for i in range(numBands):
        lo, c, hi = pts[i], pts[i + 1], pts[i + 2]
        up = (freqs - lo) / (c - lo + _EPS)
        down = (hi - freqs) / (hi - c + _EPS)
        fb[i] = np.maximum(0.0, np.minimum(up, down))
        if fb[i].sum() == 0:                       # band narrower than a bin
            fb[i, int(np.argmin(np.abs(freqs - c)))] = 1.0
        if normalize:
            fb[i] /= fb[i].sum()
    return fb, freqs


def stftMagnitude(signal, sr, windowSize, hopSize, fftSize, padding):
    """Hann-windowed magnitude STFT, frames as columns. FluCoMa padding."""
    x = np.asarray(signal, dtype=float)
    pad = {0: 0, 1: windowSize // 2, 2: windowSize - hopSize}[padding]
    x = np.pad(x, (pad, pad))
    if len(x) < windowSize:
        x = np.pad(x, (0, windowSize - len(x)))
    n = 1 + (len(x) - windowSize) // hopSize
    idx = np.arange(windowSize)[None, :] + hopSize * np.arange(n)[:, None]
    frames = x[idx] * hann(windowSize, sym=False)
    mag = np.abs(rfft(frames, n=fftSize, axis=1)).T
    times = (np.arange(n) * hopSize + windowSize / 2 - pad) / sr
    return mag, times


def mfcc(signal, sr, **settings):
    """
    Returns (coeffs, info)
        coeffs : array (numCoeffs, frames)
        info   : dict(settings, frameRate, times, mag, freqs, sr)
    """
    targetSr = settings.get("analysisSampleRate")
    x, sr = _resample(signal, sr, targetSr)
    s = resolveSettings(settings, sr)
    mag, times = stftMagnitude(x, sr, s["windowSize"], s["hopSize"],
                               s["fftSize"], s["padding"])
    fb, freqs = melFilterbank(s["fftSize"], sr, s["numBands"], s["minFreq"],
                              s["maxFreq"], s["normalizeBands"])
    melDb = 20.0 * np.log10(np.maximum(fb @ mag, 1e-6))   # floor at -120 dB
    cep = dct(melDb, type=2, axis=0, norm="ortho")
    coeffs = cep[s["startCoeff"]:s["startCoeff"] + s["numCoeffs"]]
    return coeffs, dict(settings=s, frameRate=sr / s["hopSize"], times=times,
                        mag=mag, freqs=freqs, sr=sr)


# ----------------------------------------------------------------------
# summary for the database (main value + fluctuation per coefficient)
# ----------------------------------------------------------------------
def summariseMfcc(signal, sr, settings=None, noiseThreshold=0.1, minHz=2.0, maxHz=20.0):
    coeffs, info = mfcc(signal, sr, **(settings or SUMMARY_DEFAULTS))
    loud = barkLoudness(info["mag"], info["freqs"], info["sr"])
    active = np.flatnonzero(loud >= noiseThreshold * (loud.max() + _EPS))
    if len(active) == 0:
        active = np.arange(len(loud))
    seg = slice(active[0], active[-1] + 1)
    rows = [summariseTrack(row[seg], loud[seg], info["frameRate"], minHz=minHz, maxHz=maxHz)
            for row in coeffs]
    return {k: [r[k] for r in rows] for k in rows[0]}


# ----------------------------------------------------------------------
# attack detection + slots
# ----------------------------------------------------------------------
def detectAttack(signal, sr, startThreshold=0.1, endThreshold=0.9, hopSec=0.002):
    """
    Attack start = first time the loudness reaches startThreshold x max,
    attack end = first time after that it reaches endThreshold x max
    (fixed thresholds as in Peeters 2004, 3.1.2.1).
    Returns (startSec, endSec).
    """
    loud, frameRate = instantaneousLoudness(signal, sr, hopSec=hopSec, winSec=0.01)
    if len(loud) == 0 or loud.max() <= 0:
        return 0.0, 0.0
    nfft = int(2 ** np.ceil(np.log2(max(0.01 * sr, 64))))
    offset = nfft / 2 / sr                               # frame centre time
    k = max(1, int(round(0.005 * frameRate)))           # 5 ms smoothing
    loud = np.convolve(loud, np.ones(k) / k, mode="same")
    m = loud.max()
    iS = int(np.argmax(loud >= startThreshold * m))
    iE = iS + int(np.argmax(loud[iS:] >= endThreshold * m))
    return iS / frameRate + offset, max(iE, iS + 1) / frameRate + offset


def mfccSlot(signal, sr, startSec, slotSettings, floorVector=None):
    """
    Fixed-size MFCC matrix starting at startSec.
    Returns (matrix (numCoeffs, numFrames), validFrames).
    Missing frames at the end are filled with floorVector (the
    coefficients of the file's quietest frame) instead of zeros.
    """
    s = dict(slotSettings)
    numFrames = int(s.pop("numFrames"))
    s.pop("prerollSec", None)
    x, sr2 = _resample(signal, sr, s.get("analysisSampleRate"))
    r = resolveSettings(s, sr2)
    start = max(0, int(round(startSec * sr2)))
    need = (numFrames - 1) * r["hopSize"] + r["windowSize"]
    seg = x[start:start + need]
    coeffs, _ = mfcc(seg, sr2, **dict(s, analysisSampleRate=None))
    coeffs = coeffs[:, :numFrames]
    # frames that are really inside the sound (not just padding)
    valid = int(min(coeffs.shape[1], max(1, int(np.ceil(len(seg) / r["hopSize"])))))
    out = np.empty((r["numCoeffs"], numFrames), dtype=np.float32)
    out[:, :valid] = coeffs[:, :valid]
    if valid < numFrames:
        fill = floorVector if floorVector is not None else coeffs[:, valid - 1]
        out[:, valid:] = np.asarray(fill, dtype=np.float32)[:, None]
    return out, valid


def quietestFrame(signal, sr, slotSettings):
    """
    MFCC vector of the file's quietest analysis frame (used as padding).
    Finds the frame by its energy first (cheap, cumulative sum) and only
    computes the MFCC of that one frame, so long files need no full
    analysis at slot resolution.
    """
    s = {k: v for k, v in slotSettings.items() if k not in ("numFrames", "prerollSec")}
    x, sr2 = _resample(signal, sr, s.get("analysisSampleRate"))
    r = resolveSettings(s, sr2)
    win, hop = r["windowSize"], r["hopSize"]
    pad = {0: 0, 1: win // 2, 2: win - hop}[r["padding"]]
    x = np.pad(np.asarray(x, dtype=float), (pad, pad))
    if len(x) < win:
        x = np.pad(x, (0, win - len(x)))
    n = 1 + (len(x) - win) // hop
    cs = np.concatenate([[0.0], np.cumsum(x ** 2)])
    starts = np.arange(n) * hop
    i = int(np.argmin(cs[starts + win] - cs[starts]))
    coeffs, _ = mfcc(x[i * hop:i * hop + win], sr2,
                     **dict(s, padding=0, analysisSampleRate=None))
    return coeffs[:, 0]


def timbreSlots(signal, sr, attackSettings=None, sustainSettings=None):
    """
    Attack and sustain MFCC matrices + attack timing.
    Returns dict with
        mfccAttack, mfccAttackFrames, mfccSustain, mfccSustainFrames,
        attackStartSec, attackEndSec, logAttackTime
    """
    a = dict(ATTACK_DEFAULTS, **(attackSettings or {}))
    su = dict(SUSTAIN_DEFAULTS, **(sustainSettings or {}))
    tS, tE = detectAttack(signal, sr)
    attack, aValid = mfccSlot(signal, sr, tS - a.get("prerollSec", 0.0), a,
                              quietestFrame(signal, sr, a))
    sustain, sValid = mfccSlot(signal, sr, tE, su, quietestFrame(signal, sr, su))
    return dict(
        mfccAttack=attack, mfccAttackFrames=aValid,
        mfccSustain=sustain, mfccSustainFrames=sValid,
        attackStartSec=float(tS), attackEndSec=float(tE),
        logAttackTime=float(np.log10(max(tE - tS, 1e-3))))


def slotSettingsRecord(summary=None, attack=None, sustain=None):
    """JSON-able record of the settings used, stored with each entry."""
    return dict(summary=dict(SUMMARY_DEFAULTS, **(summary or {})),
                attack=dict(ATTACK_DEFAULTS, **(attack or {})),
                sustain=dict(SUSTAIN_DEFAULTS, **(sustain or {})))
