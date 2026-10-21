# Similarity.py
"""
K-nearest-neighbour search over Tudo feature columns.

Pure numpy, no database access: Tudo.findSimilar() does the conditional
SQL search first and hands the remaining rows to knn() here.

Steps
    1. build a feature matrix from the rows (scalar columns and JSON lists,
       lists are flattened)
    2. frequency features (Hz) are taken as log2, so distances are in octaves
    3. every column is standardised over the candidates + target
       ("zscore": mean / std, "robust": median / IQR) so that features with
       large numbers (Hz, kurtosis) don't dominate
    4. weights per feature; with balanceVectors=True a list feature (e.g. 40
       MFCCs) counts as much as ONE scalar feature (elements / sqrt(n))
    5. optional PCA on the standardised matrix
    6. distance (euclidean, manhattan, cosine), k smallest
"""

import numpy as np

# feature presets (column names as in the database, case-insensitive)
FEATURE_SETS = {
    "timbre": [
        "specCentroidMain", "specSpreadMain", "specSkewnessMain",
        "specKurtosisMain", "specSlopeMain", "specDecreaseMain",
        "specRolloffMain", "specTonalityMain", "flatnessMedian",
        "roughness", "specMfccMain",
    ],
    "pitch": ["mainPitchHz", "pitchcentroidratio"],
    "dynamics": ["dynSlope1", "dynRelDur1", "dynSlope2", "dynRelDur2",
                 "dynEffDur", "logAttackTime", "peakAmplitudedB"],
    "fluctuation": [
        "pitchFluctRate", "pitchFluctDepth", "pitchFluctStrength",
        "ampFluctRate", "ampFluctDepth", "ampFluctStrength",
        "spectFluctMean", "spectFluctRate", "spectFluctStrength",
    ],
    "mfcc": ["specMfccMain"],
}
FEATURE_SETS["all"] = (FEATURE_SETS["timbre"] + FEATURE_SETS["pitch"]
                       + FEATURE_SETS["dynamics"] + FEATURE_SETS["fluctuation"])

# features in Hz -> compared as log2 (octaves)
HZ_FEATURES = {"mainpitchhz", "speccentroidmain", "specspreadmain",
               "specrolloffmain", "centroidmostcommon"}


def resolveFeatures(features):
    """Preset name, list of names/presets -> flat list of lowercase names."""
    if isinstance(features, str):
        features = [features]
    out = []
    for f in features:
        names = FEATURE_SETS.get(f, [f])
        for n in names:
            n = n.lower()
            if n not in out:
                out.append(n)
    return out


def _flatten(v):
    if v is None:
        return None
    if isinstance(v, (list, tuple, np.ndarray)):
        return np.asarray(v, dtype=float).ravel()
    try:
        return np.array([float(v)])
    except (TypeError, ValueError):
        return None


def featureMatrix(rows, features, logHz=True):
    """
    rows : list of dicts (lowercase keys)
    Returns (X, keep, columnGroups)
        X            (n_kept, d) float matrix
        keep         indices of the rows that had all features
        columnGroups [(feature, start, stop)] column ranges per feature
    """
    if not rows:
        return np.zeros((0, 0)), [], []
    # widths from the first row that has the feature
    widths = {}
    for f in features:
        for r in rows:
            v = _flatten(r.get(f))
            if v is not None:
                widths[f] = len(v)
                break
        else:
            raise ValueError(f"Similarity: no values for feature '{f}'")
    groups, start = [], 0
    for f in features:
        groups.append((f, start, start + widths[f]))
        start += widths[f]

    X, keep = [], []
    for i, r in enumerate(rows):
        vec = []
        for f in features:
            v = _flatten(r.get(f))
            if v is None or len(v) != widths[f]:
                break
            if logHz and f in HZ_FEATURES:
                v = np.log2(np.where(v > 0, v, np.nan))
            vec.append(v)
        else:
            vec = np.concatenate(vec)
            if np.all(np.isfinite(vec)):
                X.append(vec)
                keep.append(i)
    return (np.array(X) if X else np.zeros((0, start))), keep, groups


def standardise(X, method="zscore"):
    if method is None or len(X) == 0:
        return X
    if method == "zscore":
        center, scale = X.mean(axis=0), X.std(axis=0)
    elif method == "robust":
        q1, med, q3 = np.percentile(X, [25, 50, 75], axis=0)
        center, scale = med, (q3 - q1) / 1.349      # IQR -> sigma for normal data
    else:
        raise ValueError(f"Similarity: unknown normalisation '{method}'")
    scale = np.where(scale > 1e-12, scale, 1.0)     # constant columns -> 0
    return (X - center) / scale


def featureWeights(groups, weights=None, balanceVectors=True):
    weights = {k.lower(): v for k, v in (weights or {}).items()}
    w = np.ones(groups[-1][2]) if groups else np.ones(0)
    for f, a, b in groups:
        g = float(weights.get(f, 1.0))
        if balanceVectors and b - a > 1:
            g /= np.sqrt(b - a)
        w[a:b] = g
    return w


def pcaReduce(X, nComponents):
    Xc = X - X.mean(axis=0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    n = min(nComponents, Vt.shape[0])
    explained = (S[:n] ** 2).sum() / max((S ** 2).sum(), 1e-30)
    return Xc @ Vt[:n].T, float(explained)


def distances(X, q, metric="euclidean"):
    if metric == "euclidean":
        return np.sqrt(((X - q) ** 2).sum(axis=1))
    if metric == "manhattan":
        return np.abs(X - q).sum(axis=1)
    if metric == "cosine":
        nx = np.linalg.norm(X, axis=1) * np.linalg.norm(q)
        return 1.0 - (X @ q) / np.where(nx > 0, nx, 1.0)
    raise ValueError(f"Similarity: unknown metric '{metric}'")


def knn(targetRow, rows, features, k=10, *, weights=None, normalise="zscore",
        balanceVectors=True, metric="euclidean", pca=None, logHz=True):
    """
    targetRow : dict with the target's features (lowercase keys)
    rows      : candidate dicts (lowercase keys)
    Returns (results, info)
        results : list of (rowIndex, distance), nearest first
        info    : dict(features, candidates, used, dims, pcaExplained)
    """
    features = resolveFeatures(features)
    X, keep, groups = featureMatrix([targetRow] + list(rows), features, logHz)
    if not keep or keep[0] != 0:
        missing = [f for f in features if _flatten(targetRow.get(f)) is None]
        raise ValueError(f"Similarity: target has no value for {missing or 'some features'}")
    Z = standardise(X, normalise) * featureWeights(groups, weights, balanceVectors)
    explained = None
    if pca:
        Z, explained = pcaReduce(Z, int(pca))
    q, C = Z[0], Z[1:]
    d = distances(C, q, metric)
    order = np.argsort(d, kind="stable")[:k]
    rowIdx = np.array(keep[1:]) - 1                 # back to indices into rows
    results = [(int(rowIdx[i]), float(d[i])) for i in order]
    info = dict(features=features, candidates=len(rows), used=len(C),
                dims=Z.shape[1], pcaExplained=explained)
    return results, info
