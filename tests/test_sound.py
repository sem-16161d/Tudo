from Tudo.Sound import Sound
# from Tudo.PartialTracker import PartialTracker
# sound = Sound("PYTHON/Tudo/soundfiles/E808_CY-03.wav")
s = Sound("/Users/sraw/Documents/SAMPLES/TUDO/PYTHON/Tudo/soundfiles/E808_CY-03.wav")
s = Sound("/Users/sraw/Documents/SAMPLES/TUDO/SAMPLES/ACOUSTIC_INSTRUMENTS/STRING/VIOLIN/ORDINARIO/vln-m154-A4-f-Hhv81.wav",windowSize=2**16)
s= Sound((4800, 3.14, "white"), windowSize=2**14)
s= Sound()


s.getPeakAmplitude()
s.getSineFeature(toleranceCENTS =20)
s.getRoughness()
s.getSpectralCentroid()
s.getFlatness()



print(s)