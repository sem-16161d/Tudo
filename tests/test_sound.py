from Tudo.Sound import Sound, process_folder
# from Tudo.PartialTracker import PartialTracker
s = Sound("PYTHON/Tudo/soundfiles/E808_CY-03.wav")
s = Sound("SAMPLES/ACOUSTIC_INSTRUMENTS/STRING/VIOLA/artificial_harmonic/Va-art_harm-A#6-mf-2c-N.wav")
s = Sound("/Users/sraw/Documents/SAMPLES/TUDO/SAMPLES/ACOUSTIC_INSTRUMENTS/STRING/VIOLIN/ORDINARIO/vln-m154-A4-f-Hhv81.wav")
s= Sound((4800, 3.14, "white"), windowSize=2**14)
s= Sound()

s.analyse()

print(s)

# process_folder("/Users/sraw/Documents/SAMPLES/TUDO/SAMPLES/ACOUSTIC_INSTRUMENTS/WOODWIND/BASS_CLARINET/MULTIPHONIC")