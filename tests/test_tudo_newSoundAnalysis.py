from Tudo.Tudo import Tudo
from Tudo.Sound import Sound

t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/PSQL/")
t.connect()
t.getAllColumnsAndTables()

# s = Sound("/Users/sraw/Documents/SAMPLES/TUDO/SAMPLES/ACOUSTIC_INSTRUMENTS/STRING/VIOLIN/ORDINARIO/vln-m154-A4-f-Hhv81.wav")
# s.analyse()
# s.addIntentifiers(("violin", "ordinario"))
# t.newEntry("soundfile_analysis")

# for key in s.analysisDict:
#     t.updateEntry(
#         t.lastID["soundfile_analysis"],
#         key,
#         "soundfile_analysis",
#         s.analysisDict[key])

t.newEntryFromSound(
        "/Users/sraw/Documents/SAMPLES/TUDO/SAMPLES/ACOUSTIC_INSTRUMENTS/STRING/VIOLIN/ORDINARIO/vln-m154-A4-f-Hhv81.wav",
        ("violin", "ordinario"))

t.newEntriesFromFolder("SAMPLES/ACOUSTIC_INSTRUMENTS/STRING/VIOLA/artificial_harmonic",
("violin", "ordinario"))

# t.newEntry("instruments")

# t.updateEntry(
#         t.lastID["instruments"],
#         "commontuningreference",
#         "instruments",
#         [419,440,442,443])


t.dumpAllEntries("soundfile_analysis")
# t.dumpAllEntries("instruments")
t.killAllServerInstances()
