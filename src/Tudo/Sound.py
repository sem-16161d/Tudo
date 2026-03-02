import math
from GreasyPidgin.Envelope import Envelope
from random import random
from librosa import load
from librosa.feature import spectral_centroid, spectral_flatness, spectral_rolloff
import librosa
import scipy.io.wavfile as wavfile
import numpy as np
from scipy.signal import find_peaks
from itertools import combinations

def _get_sample_rate(path):
    """
    Get the sample rate of a sound file before loading it with librosa.
    """
    wav = wavfile.read(path)
    return int(wav[0])

class Sound:
    def __init__(
        self, path = (48000, 3.14, "sine", 440),
        #self, path = (48000, 3.14, "white"),
        *,
        windowSize = 2**10, hopLength= 2**9):
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
        
        self.absSig = []
        self.peakAmplitude = 0
        self.peakdB = '-inf'
        self.D,self.S, self.phase, self.fftFrequencies = None, None, None,None
        self.freq_list, self.mag_list, self.allpairs,self.sineHistogram = None,None,None,None
        self.mainPitchHz=None


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
        self.absSig = [abs(f) for f in self.soundfile]

    def _amp2dB(self,amplitude):
        if amplitude == 0:
            return float('-inf')
        else:
            return 20 * math.log10(amplitude)

    def getPeakAmplitude(self):
        if len(self.absSig)== 0:
            self._genAbsSig()
        self.peakAmplitude = max(self.absSig)
        self.peakdB = self._amp2dB(self.peakAmplitude)
        return    

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
            self.spectralDensity = np.clip(((self.sineHistogram[maxPeaks-1][1])/(self.sineHistogram[0][1]+1e-06)/0.58)**0.5, 0,1)
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

        

    def __repr__(self):
        """
        call via print(Sound)
        """
        return (
            f"\n{self.__class__.__name__}:\n"
            f"   path           : {self.path}\n"
            f"   durationSec    : {self.durationSec:.3f}\n"#dyn={self.dynamicdB:.1f} dB, "
            f"   numSamples     : {self.numSamples}\n"
            f"   peakdB         : {self.peakdB}\n"
            f"   mainPitchHz    : {self.mainPitchHz}\n"
            f"   spectralDensity: {self.spectralDensity}\n"
            f"   roughness      : {self.roughness}\n"
            f"   centroid(occ)  : {self.spectralCentroid}\n"
            f"   flatness(mdn)  : {self.flatnessMedian}\n"
            
        )


def cents_distance(f1, f2):
    return 1200 * np.log2(f1 / f2)



def cluster_by_cents(pairs, tolerance_cents=20):

    clusters = []

    for f, mag_db in pairs:

        placed = False

        for cluster in clusters:
            center = cluster["center"]

            if abs(cents_distance(f, center)) <= tolerance_cents:
                cluster["freqs"].append(f)
                cluster["mags"].append(mag_db)
                placed = True
                break

        if not placed:
            clusters.append({
                "center": f,
                "freqs": [f],
                "mags": [mag_db]
            })

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