import os
import math
from GreasyPidgin.Envelope import Envelope
from random import random
from librosa import load
from librosa.feature import spectral_centroid, spectral_flatness
import librosa
import soundfile
import numpy as np
from scipy.signal import find_peaks
from itertools import combinations
from Tudo.DynamicProfile import dynamicProfile
from Tudo.SpectralFeatures import spectralFeatures, analysisDictEntries, _autocorrPeak
from Tudo.MFCC import (summariseMfcc, timbreSlots, slotSettingsRecord,
                       SUMMARY_DEFAULTS, ATTACK_DEFAULTS, SUSTAIN_DEFAULTS)

def _get_sample_rate(path):
    """
    Sample rate of a sound file, read from the header only (libsndfile:
    WAV, AIFF, FLAC, OGG, ...).
    """
    return int(soundfile.info(path).samplerate)


# --------------------------
# Fluctuation helpers
# --------------------------

def _autocorr_peak(signal, sr, min_hz=2.0, max_hz=20.0):
    """
    Find the dominant periodic rate in a frame-rate signal via autocorrelation.

    Delegates to SpectralFeatures._autocorrPeak, which caps the search at
    the track's Nyquist (sr / 2) and only accepts true local maxima of the
    autocorrelation (non-periodic tracks return 0, 0).

    Parameters
    ----------
    signal   : 1D numpy array (one value per hop frame)
    sr       : frame rate in Hz  (samplerate / hopLength)
    min_hz   : lower bound for oscillation search (default 2 Hz)
    max_hz   : upper bound for oscillation search (default 20 Hz)

    Returns
    -------
    rate_hz  : dominant oscillation frequency (Hz), or 0 if none found
    strength : normalised autocorrelation peak value [0, 1]
    """
    return _autocorrPeak(signal, sr, min_hz, max_hz)


class Sound:
    def __init__(
        self, path = (48000, 3.14, "sine", 440),
        #self, path = (48000, 3.14, "white"),
        *,
        transposability = 1,# 0 = chromatic, -1 = false, 1 = freely
        windowSize = 2**12, hopLength= 2**11,
        mfccSettings=None, attackSettings=None, sustainSettings=None):
        """
        Load and analyze a sound file.
        """
        if isinstance(path, tuple):
            self.path = None
            self.samplerate = int(path[0])
            self.durationSec = float(path[1])
            self.numSamples = int(self.durationSec*self.samplerate)
            if path[2] == "white":
                self.soundfile = np.array([random()*2-1 for _ in range(self.numSamples)])
            elif path[2] == "sine":
                freq = path[3]
                t = np.arange(self.numSamples) / self.samplerate
                self.soundfile = np.sin(2 * np.pi * freq * t)
        else:
            self.path = path
            self.samplerate = _get_sample_rate(self.path)
            self.soundfile, _ = load(path, sr=self.samplerate)
            
            self.numSamples = len(self.soundfile)
            self.durationSec = self.numSamples/self.samplerate
        
        self.windowSize = int(windowSize)
        self.hopLength = int(hopLength)

        # files shorter than one analysis window (e.g. 0.05 s hits) are
        # zero-padded so every frame-based analysis gets at least one frame;
        # durationSec keeps the real length
        if len(self.soundfile) < self.windowSize:
            self.soundfile = np.pad(self.soundfile, (0, self.windowSize - len(self.soundfile)))
            self.numSamples = len(self.soundfile)
        
        self.absSig = []
        self.peakAmplitude = 0
        self.dynamicEnv = None
        self.peakdB = '-inf'
        self.D,self.S, self.phase, self.fftFrequencies = None, None, None,None
        self.freq_list, self.mag_list, self.allpairs,self.sineHistogram = None,None,None,None
        self.mainPitchHz, self.spectralDensity, self.roughness, self.spectralCentroid=None, None, None, None
        self.flatnessMedian = None

        # fluctuation results (populated by getFluctuations)
        self.pitchFluctuation     = None
        self.amplitudeFluctuation = None
        self.spectralFluctuation  = None

        # dynamic profile (populated by getDynamicProfile)
        self.dynamicProfile = None
        self.dynamicProfileFeatures = None

        # Peeters spectral features (populated by getSpectralFeatures)
        self.spectralFeatures = None
        self.spectralFeatureTracks = None

        # MFCC settings (FluCoMa-style, see MFCC.py); dicts override the defaults
        self.mfccSettings    = dict(SUMMARY_DEFAULTS, **(mfccSettings or {}))
        self.attackSettings  = dict(ATTACK_DEFAULTS,  **(attackSettings or {}))
        self.sustainSettings = dict(SUSTAIN_DEFAULTS, **(sustainSettings or {}))
        self.timbreSlots = None

        self.analysisDict = {"identifiers":[], "transposability": transposability}


    def sine_features_frame(self, frame, detectionThreshold=-60, sortBy="magnitude", maxPeaks=None):
        """
        Extract sinusoidal peak features from ONE complex STFT frame.

        Parameters
        ----------
        frame : complex numpy array (fft bins)
        detectionThreshold : dB threshold
        sortBy : "magnitude" | "frequency" | None
        maxPeaks : limit number of returned peaks

        Returns
        -------
        freqs : np.array (Hz)
        mags  : np.array (dB)
        """

        bins = self.windowSize // 2 + 1
        fftSize = 2 * (bins - 1)

        scale = 1.0 / (self.windowSize / 4.0)

        mag = np.abs(frame) * scale
        log_mag = 20 * np.log10(np.maximum(mag, 1e-12))

        # Peak detection (local maxima above threshold)
        peaks, props = find_peaks(log_mag, height=detectionThreshold)

        freqs = peaks * (self.samplerate / fftSize)
        mags = log_mag[peaks]

        # Optional sorting
        if sortBy == "magnitude":
            order = np.argsort(mags)[::-1]
        elif sortBy == "frequency":
            order = np.argsort(freqs)
        else:
            order = np.arange(len(freqs))

        freqs = freqs[order]
        mags = mags[order]

        if maxPeaks is not None:
            freqs = freqs[:maxPeaks]
            mags = mags[:maxPeaks]

        return freqs, mags

    def sine_features(self, detectionThreshold=-60, sortBy="magnitude", maxPeaks=None):
        """
        python implementation of 
        https://github.com/flucoma/flucoma-core/blob/e3cadeb8382e9e473f3b5f94a2f3a0c93fa082a7/include/flucoma/algorithms/public/SineFeature.hpp
        """
        all_freqs = []
        all_mags = []
        if self.D is None:
            self.stft()
        for frame in self.D.T:  # pyright: ignore[reportOptionalMemberAccess]
            f, m = self.sine_features_frame(
                frame,
                detectionThreshold=detectionThreshold,
                sortBy=sortBy,
                maxPeaks=maxPeaks
            )
            all_freqs.append(f)
            all_mags.append(m)

        return all_freqs, all_mags

    def _genAbsSig(self):
        self.absSig = np.abs(self.soundfile)

    def _amp2dB(self,amplitude):
        if amplitude == 0:
            return float('-inf')
        else:
            return 20 * math.log10(amplitude)

    def getPeakAmplitude(self):
        if len(self.absSig)== 0:
            self._genAbsSig()
        self.peakAmplitude = float(np.max(self.absSig))
        self.peakdB = self._amp2dB(self.peakAmplitude)
        return    

    def calculateDynamicEnv(self,numMinima=3, numMaxima=3, resolution = 10):
        if len(self.absSig) == 0:
            self._genAbsSig()
        rawEnv = Envelope(list(self.absSig))
        rawEnv.reduceEnvPoints(numMinima=numMinima, numMaxima=numMaxima, resolution=resolution)
        self.simpleDynamicEnvNorm = rawEnv.reducedEnv

    def stft(self):
        self.D = librosa.stft(
            self.soundfile,
            n_fft=self.windowSize,
            hop_length=self.hopLength,)
        self.S, self.phase = librosa.magphase(self.D)
        self.fftFrequencies = librosa.fft_frequencies(
            sr=self.samplerate,
            n_fft=self.windowSize)

    def getSineFeature(self,detectionThresholddB=-144,maxPeaks=16, toleranceCENTS = 30):
        self.freq_list, self.mag_list = self.sine_features(detectionThreshold=detectionThresholddB,maxPeaks=maxPeaks)
        self.allpairs =[
            (f,m) 
            for fl,ml in zip(self.freq_list, self.mag_list) 
            for f, m in zip(fl, ml) ]
        clusters = cluster_by_cents(self.allpairs,tolerance_cents=toleranceCENTS)
        
        clusters_sorted = sorted(
            clusters,key=lambda c: c["dominance"],reverse=True)
        self.sineHistogram = [(c["center"], c["relative"]) for c in clusters_sorted[:16]]
        self.mainPitchHz = self.sineHistogram[0][0]
        # white noise has a max value of ideally 0.58, so to normalize this became the factor
        if len(self.sineHistogram) > 1:
            # weakest of the (up to) maxPeaks strongest clusters vs. the strongest;
            # very short files can have fewer than maxPeaks clusters
            weakest = self.sineHistogram[min(maxPeaks, len(self.sineHistogram)) - 1][1]
            self.spectralDensity = np.clip((weakest/(self.sineHistogram[0][1]+1e-06)/0.58)**0.5, 0,1)
        else:
            self.spectralDensity = 0

    def getRoughness(self):
        if self.sineHistogram is None:
            self.getSineFeature()
        self.roughness = roughness_from_histo(self.sineHistogram)

    def getSpectralCentroid(self, toleranceCENTS = 400):
        if self.S is None:
            self.stft()
        self.spectralCentroids = spectral_centroid(S=self.S)[0]
        pairs = [(f,1) for f in self.spectralCentroids]
        cluster = cluster_by_cents(pairs, toleranceCENTS)
        self.spectralCentroidHistogram = sorted([
            (sc["center"], sc["relative"]) for sc in cluster],
            key=lambda c: c[1],reverse=True)
        self.spectralCentroidEnv = Envelope([float(val) for val in self.spectralCentroids])
        self.spectralCentroid = self.spectralCentroidHistogram[0][0]
        
    def getFlatness(self):
        if self.S is None:
            self.stft()
        self.flatnesses = spectral_flatness(S=self.S)[0]
        self.flatnessEnv = Envelope([float(val) for val in self.flatnesses])
        self.flatnessMedian = self.flatnessEnv.median_y()
        self.flatnessMean = self.flatnessEnv.mean_y()

    # --------------------------
    # Dynamic profile (Peeters & Deruty 2008, sec. 3.1)
    # --------------------------

    def getDynamicProfile(self, **kwargs):
        """
        Classify the loudness shape as ascending, descending,
        ascending/descending, stable or impulsive.
        kwargs go to DynamicProfile.dynamicProfileFeatures
        (lowpassHz, noiseThreshold, effDurThreshold, timeBase, maxTolerance).
        """
        self.dynamicProfile, self.dynamicProfileFeatures = dynamicProfile(
            self.soundfile, self.samplerate, **kwargs)
        return self.dynamicProfile

    # --------------------------
    # Spectral features (Peeters 2004, sec. 6 + 9.1)
    # --------------------------

    def getSpectralFeatures(self, minHz=2.0, maxHz=20.0):
        """
        centroid, spread, skewness, kurtosis, slope, decrease, rolloff,
        variation, tonality, 12 MFCCs, band flatness and crest.
        Each summarised as main (most common) value + fluctuation
        rate / depth / strength. See Tudo/SpectralFeatures.py.

        self.spectralFeatures      : summary dict
        self.spectralFeatureTracks : frame-wise curves (for plotting)
        """
        if self.S is None:
            self.stft()
        self.spectralFeatures, self.spectralFeatureTracks = spectralFeatures(
            self.S, self.fftFrequencies, self.samplerate, self.hopLength,
            minHz=minHz, maxHz=maxHz)
        self.spectralFeatures["mfcc"] = summariseMfcc(
            self.soundfile, self.samplerate, self.mfccSettings,
            minHz=minHz, maxHz=maxHz)
        return self.spectralFeatures

    def getTimbreSlots(self):
        """
        Fixed-size MFCC matrices for neural-network training:
            mfccAttack  (numCoeffs x numFrames) from the attack onset
            mfccSustain (numCoeffs x numFrames) from the end of the attack
        + attackStartSec, attackEndSec, logAttackTime.
        Settings: self.attackSettings / self.sustainSettings (see MFCC.py).
        """
        self.timbreSlots = timbreSlots(
            self.soundfile, self.samplerate,
            self.attackSettings, self.sustainSettings)
        return self.timbreSlots

    # --------------------------
    # Fluctuation detectors
    # --------------------------

    def getPitchFluctuation(self, minHz=2.0, maxHz=20.0):
        """
        Measure periodic pitch fluctuation (vibrato, trills, flutter).

        Tracks the dominant-magnitude sinusoidal peak per STFT frame in cents
        relative to the median pitch, then runs autocorrelation to find the
        oscillation rate and depth.

        Requires getSineFeature() to have been called first (falls back to
        spectral centroid track if not available).

        Stores
        ------
        self.pitchFluctuation : dict
            rate_hz   — dominant oscillation rate in Hz (0 if none found)
            depth_cents — peak-to-peak fluctuation depth in cents
            strength  — normalised autocorrelation peak [0, 1]; higher = more
                        periodic. Use this as the primary "vibrato" indicator.
        """
        frame_rate = self.samplerate / self.hopLength

        # --- build per-frame dominant-frequency track ---
        if self.freq_list is not None and len(self.freq_list) > 0:
            pitch_track = []
            for freqs, mags in zip(self.freq_list, self.mag_list):
                if len(freqs) > 0:
                    pitch_track.append(float(freqs[0]))   # already sorted by magnitude
                else:
                    pitch_track.append(np.nan)
            pitch_track = np.array(pitch_track, dtype=float)
        elif hasattr(self, 'spectralCentroids'):
            pitch_track = np.array(self.spectralCentroids, dtype=float)
        else:
            if self.S is None:
                self.stft()
            self.spectralCentroids = spectral_centroid(S=self.S)[0]
            pitch_track = np.array(self.spectralCentroids, dtype=float)

        # Replace NaN / zero with median so they don't poison the autocorr
        median_pitch = np.nanmedian(pitch_track[pitch_track > 0])
        pitch_track = np.where(
            (np.isnan(pitch_track)) | (pitch_track <= 0),
            median_pitch,
            pitch_track
        )

        # Convert to cents relative to median — makes depth perceptually meaningful
        cents_track = 1200.0 * np.log2(pitch_track / (median_pitch + 1e-12))

        depth_cents = float(np.percentile(cents_track, 95) - np.percentile(cents_track, 5))
        rate_hz, strength = _autocorr_peak(cents_track, frame_rate, minHz, maxHz)

        self.pitchFluctuation = {
            "rate_hz":     round(rate_hz, 3),
            "depth_cents": round(depth_cents, 3),
            "strength":    round(strength, 4),
        }
        return self.pitchFluctuation

    def getAmplitudeFluctuation(self, minHz=2.0, maxHz=20.0):
        """
        Measure periodic amplitude fluctuation (tremolo, breath pulses).

        Computes RMS per hop frame in dB, then runs autocorrelation to find the
        oscillation rate and depth.

        Stores
        ------
        self.amplitudeFluctuation : dict
            rate_hz  — dominant oscillation rate in Hz (0 if none found)
            depth_dB — peak-to-peak RMS fluctuation depth in dB
            strength — normalised autocorrelation peak [0, 1]
        """
        frame_rate = self.samplerate / self.hopLength

        # RMS per hop frame
        frames = librosa.util.frame(
            self.soundfile,
            frame_length=self.windowSize,
            hop_length=self.hopLength)
        rms = np.sqrt(np.mean(frames ** 2, axis=0))
        rms_db = 20.0 * np.log10(np.maximum(rms, 1e-12))

        depth_dB = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 5))
        rate_hz, strength = _autocorr_peak(rms_db, frame_rate, minHz, maxHz)

        self.amplitudeFluctuation = {
            "rate_hz":  round(rate_hz, 3),
            "depth_dB": round(depth_dB, 3),
            "strength": round(strength, 4),
        }
        return self.amplitudeFluctuation

    def getSpectralFluctuation(self, minHz=2.0, maxHz=20.0):
        """
        Measure frame-to-frame spectral change (timbral flutter, multiphonic
        instability).

        Computes cosine distance between adjacent normalised magnitude frames,
        giving a spectral flux curve. Summary statistics and autocorrelation
        capture both the overall amount of change and whether it is periodic.

        Stores
        ------
        self.spectralFluctuation : dict
            mean     — mean spectral flux [0, 1]; 0 = static, 1 = maximally
                       different every frame
            variance — variance of the flux curve; high = irregular change
            rate_hz  — dominant periodic rate in the flux signal (Hz)
            strength — normalised autocorrelation peak [0, 1]
        """
        frame_rate = self.samplerate / self.hopLength

        if self.S is None:
            self.stft()

        # Normalise each frame to unit L2 norm (so energy differences don't
        # dominate — we care about spectral *shape* change)
        mag = np.abs(self.S).T                            # (frames, bins)
        norms = np.linalg.norm(mag, axis=1, keepdims=True)
        mag_norm = mag / (norms + 1e-12)

        # Cosine distance between adjacent frames  =  1 − cosine_similarity
        dot = np.sum(mag_norm[:-1] * mag_norm[1:], axis=1)
        flux = 1.0 - np.clip(dot, -1.0, 1.0)             # [0, 2], typically [0, 1]

        mean_flux     = float(np.mean(flux))
        variance_flux = float(np.var(flux))
        rate_hz, strength = _autocorr_peak(flux, frame_rate, minHz, maxHz)

        self.spectralFluctuation = {
            "mean":     round(mean_flux, 4),
            "variance": round(variance_flux, 6),
            "rate_hz":  round(rate_hz, 3),
            "strength": round(strength, 4),
        }
        return self.spectralFluctuation

    def getFluctuations(self, minHz=2.0, maxHz=20.0):
        """
        Run all three fluctuation detectors in one call.
        Ensures STFT and sine features are computed first.

        Returns
        -------
        dict with keys 'pitch', 'amplitude', 'spectral'
        """
        if self.D is None:
            self.stft()
        if self.freq_list is None:
            self.getSineFeature()

        self.getPitchFluctuation(minHz, maxHz)
        self.getAmplitudeFluctuation(minHz, maxHz)
        self.getSpectralFluctuation(minHz, maxHz)

        return {
            "pitch":     self.pitchFluctuation,
            "amplitude": self.amplitudeFluctuation,
            "spectral":  self.spectralFluctuation,
        }

    def analyse(self):
        self.getPeakAmplitude()
        if self.peakAmplitude == 0:
            raise ValueError("Sound.analyse: file is silent")
        self.getRoughness()
        self.getSpectralCentroid()
        self.pitchcentroidratio =  self.spectralCentroid/self.mainPitchHz
        self.getFlatness()
        # calculateDynamicEnv() is not stored in the database and takes most of
        # the analysis time on long files (it runs on every single sample), so
        # analyse() skips it. Call sound.calculateDynamicEnv() when needed.
        self.getFluctuations()
        self.getDynamicProfile()
        self.getSpectralFeatures()
        dp = self.dynamicProfileFeatures
        self.analysisDict = {
            "identifiers": self.analysisDict["identifiers"],
            "transposability": self.analysisDict["transposability"],
            "path": self.path,
            "durationSec": self.durationSec,
            "sampleRate": self.samplerate,
            "peakAmplitudedB": self.peakdB,
            "mainPitchHz": self.mainPitchHz,
            "centroidMostCommon": self.spectralCentroid,
            "pitchcentroidratio":self.pitchcentroidratio,
            "spectralDensity": self.spectralDensity,
            "roughness": self.roughness,
            "flatnessMedian": self.flatnessMedian,
            # fluctuations
            "pitchFluctRate":      self.pitchFluctuation["rate_hz"],
            "pitchFluctDepth":     self.pitchFluctuation["depth_cents"],
            "pitchFluctStrength":  self.pitchFluctuation["strength"],
            "ampFluctRate":        self.amplitudeFluctuation["rate_hz"],
            "ampFluctDepth":       self.amplitudeFluctuation["depth_dB"],
            "ampFluctStrength":    self.amplitudeFluctuation["strength"],
            "spectFluctMean":      self.spectralFluctuation["mean"],
            "spectFluctVariance":  self.spectralFluctuation["variance"],
            "spectFluctRate":      self.spectralFluctuation["rate_hz"],
            "spectFluctStrength":  self.spectralFluctuation["strength"],
            # dynamic profile
            "dynProfile":  self.dynamicProfile,
            "dynSlope1":   dp["slope1"],
            "dynRelDur1":  dp["relDur1"],
            "dynSlope2":   dp["slope2"],
            "dynRelDur2":  dp["relDur2"],
            "dynEffDur":   dp["effDur"],
        }
        # spectral features: spec<Feature>Main / FluctRate / FluctDepth / FluctStrength
        self.analysisDict.update(analysisDictEntries(self.spectralFeatures))
        # timbre slots (MFCC matrices for training)
        self.getTimbreSlots()
        for k, v in self.timbreSlots.items():
            self.analysisDict[k] = v.tolist() if isinstance(v, np.ndarray) else v
        self.analysisDict["mfccSettings"] = slotSettingsRecord(
            self.mfccSettings, self.attackSettings, self.sustainSettings)
        print("Sound.analyse: done!")

    def addIdentifier (self, identifier):
        self.analysisDict["identifiers"].append(identifier)

    def addIntentifiers(self, iterable):
        for i in iterable:
            self.addIdentifier(i)

    def __repr__(self):
        """
        call via print(Sound)
        """
        pitch_f  = self.pitchFluctuation
        amp_f    = self.amplitudeFluctuation
        spec_f   = self.spectralFluctuation
        pf = (f"rate={pitch_f['rate_hz']} Hz  depth={pitch_f['depth_cents']} ¢  str={pitch_f['strength']}"
              if pitch_f else "not computed")
        af = (f"rate={amp_f['rate_hz']} Hz  depth={amp_f['depth_dB']} dB  str={amp_f['strength']}"
              if amp_f else "not computed")
        sf = (f"mean={spec_f['mean']}  var={spec_f['variance']}  rate={spec_f['rate_hz']} Hz  str={spec_f['strength']}"
              if spec_f else "not computed")

        return (
            f"\n{self.__class__.__name__}:\n"
            f"   path              : {self.path}\n"
            f"   durationSec       : {self.durationSec:.3f}\n"
            f"   numSamples        : {self.numSamples}\n"
            f"   peakdB            : {self.peakdB}\n"
            f"   mainPitchHz       : {self.mainPitchHz}\n"
            f"   spectralDensity   : {self.spectralDensity}\n"
            f"   roughness         : {self.roughness}\n"
            f"   centroid(occ)     : {self.spectralCentroid}\n"
            f"   pitchcentroidratio: {self.pitchcentroidratio}\n"
            f"   flatness(mdn)     : {self.flatnessMedian}\n"
            f"   pitchFluct        : {pf}\n"
            f"   ampFluct          : {af}\n"
            f"   spectralFluct     : {sf}\n"
        )


def cents_distance(f1, f2):
    return 1200 * np.log2(f1 / f2+0.00001)



def cluster_by_cents(pairs, tolerance_cents=20):
    """
    Greedy clustering of (frequency, magnitude_dB) pairs: each pair joins the
    first cluster (in creation order) whose centre is within tolerance_cents,
    otherwise it starts a new cluster. Same result as the original loop, but
    the distance to all centres is computed at once with numpy.
    """
    clusters = []
    centers = np.empty(64)
    n = 0
    with np.errstate(divide="ignore", invalid="ignore"):
        for f, mag_db in pairs:
            if n:
                d = np.abs(1200 * np.log2(f / centers[:n] + 0.00001))   # = cents_distance
                hit = np.flatnonzero(d <= tolerance_cents)
                if hit.size:
                    c = clusters[hit[0]]
                    c["freqs"].append(f)
                    c["mags"].append(mag_db)
                    continue
            if n == len(centers):
                centers = np.resize(centers, 2 * n)
            centers[n] = f
            n += 1
            clusters.append({"center": f, "freqs": [f], "mags": [mag_db]})

    # compute dominance per cluster
    for cluster in clusters:
        linear_energy = np.sum(10 ** (np.array(cluster["mags"]) / 20))
        cluster["dominance"] = linear_energy
    
    total_energy = sum(c["dominance"] for c in clusters)

    for c in clusters:
        c["relative"] = c["dominance"] / total_energy

    return clusters



def roughness_from_pair(f1, f2, a1, a2):
    """
    Vassilakis roughness between two sinusoids.
    Frequencies in Hz
    Amplitudes dB)
    """

    # sort
    fMin, fMax = min(f1, f2), max(f1, f2)
    aMin, aMax = min(a1, a2), max(a1, a2)
    aMin, aMax = 10 ** (np.array(aMin) / 20), 10 ** (np.array(aMax) / 20)

    # constants (Vassilakis)
    b1 = 3.5
    b2 = 5.75
    s1 = 0.0207
    s2 = 18.96

    x = aMin * aMax
    y = 2 * aMin / (aMin + aMax)
    s0 = 0.24 / (s1 * fMin + s2)

    z = np.exp(-b1 * s0 * (fMax - fMin)) - np.exp(-b2 * s0 * (fMax - fMin))

    roughness = (x ** 0.1) * 0.5 * (y ** 3.11) * z

    return roughness

def roughness_from_chord(freqs, amps):
    """
    freqs : list of Hz
    amps  : list of linear amplitudes (same length)

    returns total roughness
    """

    total = 0.0

    for (i, j) in combinations(range(len(freqs)), 2):
        total += roughness_from_pair(
            freqs[i], freqs[j],
            amps[i], amps[j]
        )
    # max val for white noise at about 1.2
    return np.clip(total/1.2, 0, 1)


def roughness_from_histo(histo):
    freqs, amps = [],[]
    for f,a in histo:
        freqs.append(f)
        amps.append(a)
    return roughness_from_chord(freqs, amps)




def process_folder(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path) and filename.lower().endswith(('.wav')):
            # print(file_path)
            sound = Sound(file_path)
            sound.analyse()
            print(sound)