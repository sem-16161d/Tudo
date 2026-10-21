# =============================================================================
# plotOnsets.py — show the detected onsets of a sound
#
# Top: waveform with numbered onset markers.
# Bottom: onset function (grey), filtered curve (blue) and threshold (red).
# Works for files in the database (by path or id) and for any other file.
# =============================================================================
from Tudo.Tudo import Tudo

DB_PATH = "/Users/sraw/Documents/SAMPLES/TUDO/DB"

TARGET = "/Users/sraw/Documents/SAMPLES/TUDO/SAMPLES/MUSIC_RADAR/female_vocal_samples/operaesque/op 6 4.wav"
# TARGET = 1234          # or a database id

# leave empty for the defaults (metric 2 SpectralFlux, threshold 0.3),
# or try e.g. {"threshold": 0.2, "filterLag": 5} for legato note changes
SETTINGS = {}

SAVE_PNG = None          # e.g. "/private/tmp/onsets.png"

t = Tudo(DB_PATH)
t.connect()
t.plotOnsets(TARGET, savePath=SAVE_PNG, **SETTINGS)
