# SpectralFeatures.py
"""
Spectral features after

    G. Peeters (2004): "A large set of audio features for sound
    description (similarity and classification) in the CUIDADO project",
    sections 6 (spectral features) and 9.1 (flatness / crest / tonality).

All features are computed frame by frame on the STFT magnitude spectrum
(linear amplitude, linear frequency, DC bin excluded):

    centroid    6.1.1  barycenter of the spectrum                    [Hz]
    spread      6.1.2  standard deviation around the centroid        [Hz]
                       (Peeters defines the variance; we store sigma so it is in Hz)
    skewness    6.1.3  asymmetry (0 = symmetric, >0 = more energy left)
    kurtosis    6.1.4  peakedness (3 = gaussian, <3 flatter, >3 peakier)
    slope       6.1.5  linear regression of amplitude over frequency, / sum(a)
    decrease    6.1.6  perceptually motivated slope
    rolloff     6.1.7  frequency below which 95 % of the energy lies   [Hz]
    variation   6.2.1  1 - normalised cross-correlation of successive frames
    mfcc        6.3.1  MFCCs -> computed in MFCC.py with FluCoMa-style settings
    sfmBands    9.1    spectral flatness in 250-500, 500-1k, 1k-2k, 2k-4k Hz
    scmBands    9.1    spectral crest in the same four bands
    tonality    9.1    min(SFM_dB / -60, 1) over the whole spectrum (1 = tonal)

Each frame track is then summarised like the other Tudo parameters:

    main      most common value: loudness-weighted histogram mode over the
              frames above the noise threshold (10 % of max loudness)
    fluctRate     dominant periodic rate of the track in Hz (autocorrelation)
    fluctDepth    5th-95th percentile range (in cents for Hz-features)
    fluctStrength normalised autocorrelation peak [0, 1]

Only numpy + scipy.
"""

import numpy as np

SFM_BANDS = ((250, 500), (500, 1000), (1000, 2000), (2000, 4000))

# features whose values are frequencies: mode and depth are taken in log2 / cents
FREQUENCY_FEATURES = {"centroid", "spread", "rolloff"}

SCALAR_FEATURES = ("centroid", "spread", "skewness", "kurtosis", "slope",
                   "decrease", "rolloff", "variation", "tonality")
VECTOR_FEATURES = ("mfcc", "sfmBands", "scmBands")

_BARK_EDGES = np.array([
    0, 100, 200, 300, 400, 510, 630, 770, 920, 1080, 1270, 1480, 1720,
    2000, 2320, 2700, 3150, 3700, 4400, 5300, 6400, 7700, 9500, 12000,
    15500, 20500])

_EPS = 1e-12


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def _autocorrPeak(signal, frameRate, minHz=2.0, maxHz=20.0):
    """
    Dominant periodic rate of a frame track: (rate_hz, strength).
    Like Sound._autocorr_peak, but
      - the search is capped at the track's Nyquist (frameRate / 2), and
      - only true local maxima of the autocorrelation count, so a smooth,
        non-periodic track returns (0, 0) instead of the boundary lag.
    """
    signal = np.asarray(signal, dtype=float)
    signal = signal - np.mean(signal)
    if len(signal) < 4 or np.std(signal) < 1e-10:
        return 0.0, 0.0
    maxHz = min(maxHz, frameRate / 2)
    lagMin = max(2, int(np.floor(frameRate / maxHz)))
    lagMax = min(int(np.ceil(frameRate / minHz)), len(signal) - 2)
    if lagMin >= lagMax:
        return 0.0, 0.0
    acf = np.correlate(signal, signal, mode="full")[len(signal) - 1:]
    acf = acf / (acf[0] + _EPS)
    lags = np.arange(lagMin, lagMax + 1)
    isPeak = (acf[lags] > acf[lags - 1]) & (acf[lags] >= acf[lags + 1])
    if not isPeak.any():
        return 0.0, 0.0
    peaks = lags[isPeak]
    best = peaks[int(np.argmax(acf[peaks]))]
    strength = float(np.clip(acf[best], 0, 1))
    if strength <= 0:
        return 0.0, 0.0
    # parabolic interpolation for a finer rate estimate
    y0, y1, y2 = acf[best - 1], acf[best], acf[best + 1]
    d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + _EPS)
    return float(frameRate / (best + d)), strength


def barkLoudness(S, freqs, sr):
    """Total loudness per frame (CUIDADO AudioLoudness): sum_z E(z)^0.23."""
    power = S ** 2
    edges = _BARK_EDGES[_BARK_EDGES < sr / 2]
    edges = np.append(edges, sr / 2)
    idx = np.digitize(freqs, edges) - 1
    loud = np.zeros(S.shape[1])
    for b in range(len(edges) - 1):
        rows = idx == b
        if rows.any():
            loud += power[rows].sum(axis=0) ** 0.23
    return loud


# ----------------------------------------------------------------------
# frame-wise features
# ----------------------------------------------------------------------
def spectralFeatureTracks(S, freqs, sr, rolloffThreshold=0.95):
    """
    S     : magnitude spectrogram (bins x frames), e.g. librosa's |STFT|
    freqs : bin frequencies in Hz
    Returns dict of 1-D tracks (scalar features) and 2-D arrays
    (vector features, shape (n, frames)).
    """
    S = np.asarray(S, dtype=float)
    freqs = np.asarray(freqs, dtype=float)
    a, f = S[1:], freqs[1:]                      # drop DC
    K, nFrames = a.shape
    sumA = a.sum(axis=0) + _EPS
    p = a / sumA                                  # spectrum as distribution

    centroid = (f[:, None] * p).sum(axis=0)
    dev = f[:, None] - centroid
    var = (dev ** 2 * p).sum(axis=0)
    sigma = np.sqrt(var)
    skew = (dev ** 3 * p).sum(axis=0) / (sigma ** 3 + _EPS)
    kurt = (dev ** 4 * p).sum(axis=0) / (var ** 2 + _EPS)

    # 6.1.5 slope (linear regression, normalised by sum of amplitudes)
    N = K
    sf, sff = f.sum(), (f ** 2).sum()
    slope = (N * (f[:, None] * a).sum(axis=0) - sf * a.sum(axis=0)) \
        / (N * sff - sf ** 2) / sumA

    # 6.1.6 decrease
    k = np.arange(1, K)[:, None]                  # k-1 for k = 2..K
    decrease = ((a[1:] - a[0]) / k).sum(axis=0) / (a[1:].sum(axis=0) + _EPS)

    # 6.1.7 roll-off (95 % of the energy)
    energy = np.cumsum(a ** 2, axis=0)
    total = energy[-1] + _EPS
    rolloff = f[np.argmax(energy >= rolloffThreshold * total, axis=0)]

    # 6.2.1 variation between successive frames (first frame: 0)
    num = (a[:, :-1] * a[:, 1:]).sum(axis=0)
    den = np.sqrt((a[:, :-1] ** 2).sum(axis=0)) * np.sqrt((a[:, 1:] ** 2).sum(axis=0))
    variation = np.concatenate([[0.0], 1.0 - num / (den + _EPS)])

    # 6.3.1 MFCC: computed separately in MFCC.py (FluCoMa-style settings)

    # 9.1 flatness / crest per band on the energy spectrum
    power = a ** 2
    sfm, scm = [], []
    for lo, hi in SFM_BANDS:
        rows = (f >= lo) & (f < hi)
        if not rows.any():
            sfm.append(np.zeros(nFrames)); scm.append(np.zeros(nFrames)); continue
        pb = power[rows] + _EPS
        mean = pb.mean(axis=0)
        sfm.append(np.exp(np.log(pb).mean(axis=0)) / mean)
        scm.append(pb.max(axis=0) / mean)

    # tonality from the full-spectrum flatness
    pw = power + _EPS
    sfmAll = np.exp(np.log(pw).mean(axis=0)) / pw.mean(axis=0)
    tonality = np.minimum(10 * np.log10(sfmAll) / -60.0, 1.0)

    return {
        "centroid": centroid, "spread": sigma, "skewness": skew,
        "kurtosis": kurt, "slope": slope, "decrease": decrease,
        "rolloff": rolloff, "variation": variation, "tonality": tonality,
        "sfmBands": np.array(sfm), "scmBands": np.array(scm),
    }


# ----------------------------------------------------------------------
# summary: main value + fluctuation
# ----------------------------------------------------------------------
def mostCommonValue(values, weights=None, bins=30, log=False):
    """Loudness-weighted histogram mode; returns the weighted median of
    the values that fall into the heaviest bin."""
    v = np.asarray(values, dtype=float)
    w = np.ones_like(v) if weights is None else np.asarray(weights, dtype=float)
    ok = np.isfinite(v) & (w > 0)
    if log:
        ok &= v > 0
    v, w = v[ok], w[ok]
    if len(v) == 0:
        return 0.0
    x = np.log2(v) if log else v
    lo, hi = np.percentile(x, [2, 98])
    if hi - lo < 1e-12:
        return float(np.median(v))
    hist, edges = np.histogram(x, bins=bins, range=(lo, hi), weights=w)
    b = int(np.argmax(hist))
    sel = (x >= edges[b]) & (x <= edges[b + 1])
    xs, ws = x[sel], w[sel]
    order = np.argsort(xs)
    cw = np.cumsum(ws[order])
    med = xs[order][np.searchsorted(cw, cw[-1] / 2)]
    return float(2 ** med if log else med)


def summariseTrack(track, weights, frameRate, *, log=False, minHz=2.0, maxHz=20.0):
    track = np.asarray(track, dtype=float)
    main = mostCommonValue(track, weights, log=log)
    t = np.where(np.isfinite(track), track, main)
    if log:
        t = 1200.0 * np.log2(np.maximum(t, _EPS) / (main + _EPS))   # cents
    depth = float(np.percentile(t, 95) - np.percentile(t, 5)) if len(t) else 0.0
    rate, strength = _autocorrPeak(t, frameRate, minHz, maxHz)
    return {"main": main, "fluctRate": round(rate, 3),
            "fluctDepth": depth, "fluctStrength": round(strength, 4)}


def spectralFeatures(S, freqs, sr, hopLength, *, noiseThreshold=0.1,
                     minHz=2.0, maxHz=20.0):
    """
    Compute all tracks and summarise them.
    Only the frames between the first and last frame above
    `noiseThreshold` x max loudness are used (Peeters sec. 10),
    statistics are weighted by the loudness.

    Returns (summary, tracks). summary[name] is a dict for scalar
    features and a dict of lists (one entry per coefficient/band) for
    vector features.
    """
    frameRate = sr / hopLength
    tracks = spectralFeatureTracks(S, freqs, sr)
    loud = barkLoudness(np.asarray(S, dtype=float), np.asarray(freqs, dtype=float), sr)
    active = np.flatnonzero(loud >= noiseThreshold * (loud.max() + _EPS))
    if len(active) == 0:
        active = np.arange(len(loud))
    seg = slice(active[0], active[-1] + 1)
    w = loud[seg]

    summary = {}
    for name in SCALAR_FEATURES:
        tr = tracks[name][seg]
        if name == "variation" and len(tr) > 1:     # first value has no predecessor
            summary[name] = summariseTrack(tr[1:], w[1:], frameRate, minHz=minHz, maxHz=maxHz)
        else:
            summary[name] = summariseTrack(tr, w, frameRate, log=name in FREQUENCY_FEATURES,
                                           minHz=minHz, maxHz=maxHz)
    for name in VECTOR_FEATURES:
        if name not in tracks:          # mfcc is summarised in MFCC.py
            continue
        rows = [summariseTrack(row[seg], w, frameRate, minHz=minHz, maxHz=maxHz)
                for row in tracks[name]]
        summary[name] = {k: [r[k] for r in rows] for k in rows[0]}
    tracks["loudness"] = loud
    tracks["activeFrames"] = (active[0], active[-1])
    return summary, tracks


def databaseColumns():
    """(column, type) pairs for Tudo.setupTables / addMissingColumns."""
    cols = []
    for name in SCALAR_FEATURES + VECTOR_FEATURES:
        typ = "FLOAT" if name in SCALAR_FEATURES else "JSON"
        base = "spec" + name[0].upper() + name[1:]
        for stat in ("Main", "FluctRate", "FluctDepth", "FluctStrength"):
            cols.append((base + stat, typ))
    return cols


def analysisDictEntries(summary):
    """Flatten a summary into {column: value} for the database."""
    out = {}
    for name, stats in summary.items():
        base = "spec" + name[0].upper() + name[1:]
        for stat, val in stats.items():
            col = base + stat[0].upper() + stat[1:]
            out[col] = [float(x) for x in val] if isinstance(val, list) else float(val)
    return out
