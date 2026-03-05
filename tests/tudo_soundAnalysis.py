from GreasyPidgin.Pitch import mtof
from Tudo.Tudo import Tudo
from GreasyPidgin.Instruments import STANDARD_INSTRUMENTS

t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/PSQL/")
t.connect()
t.getAllColumnsAndTables()

path = "SAMPLES/ACOUSTIC_INSTRUMENTS/STRING/VIOLA/artificial_harmonic_tremolo"
idents = (
        "viola",
        "artificial_harmonic_tremolo"
)
transpo = 1
t.newEntriesFromFolder(path,
idents,transpo)



# # t.newEntry("instruments")
# # for c, v in [
# #             ("lowestNoteMidi",48),
# #             ("highestNoteMidi",89),
# #             ("commonTuningReference",[415, 440, 442, 443]),
# #             ("lowestFreqHz", mtof(48)),
# #             ("highestFreqHz",mtof(89)),
# #             ("physicalDynamicdBmin", 40),
# #             ("physicalDynamicdBmax", 105),
# #             ("writtenDynMin", "ppppp"),
# #             ("writtenDynMax", "fffff"),
# #             ("numSystems",1),
# #             ("microtones", True),
# #             ("transpositionSemitones", 0),
# #             ("chords", True),
# #             ("multiphonics", True),
# #             ("numSystems", 1),
# #             ("materials", ["wood", "metal", "keratin", "rubber", "lead"]),
# #             ("playingTechniques", [
# #                 "artificial_harmonic", "artificial_harmonic_tremolo",
# #                 "bartok_pizzicato", "behind_the_bridge","behind_the_fingerboard",
# #                 "col_legno_battuto","col_legno_tratto","half_col_legno_tratto",
# #                 "muted_col_legno_saltando","natural_harmonic","natural_harmonic_pizzicato",
# #                 "ordinario","overpressure","paperclip","pizzicato","pizzicato_fingernail",
# #                 "pizzicato_secco","practice_mute","ricochet","ricochet_sul_ponticello",
# #                 "rubber_mute","rubber_mute_pizzicato","rubber_mute_sul_ponticello",
# #                 "sul_tasto_tremolo","tremolo","tremolo_sul_ponticello"
# #                 ]),
# #             ("possibleClefs", ["alto", "treble"]),
# #                 ]:
# #         t.updateEntry(
# #                 t.lastID["instruments"],
# #                 c,
# #                 "instruments",
# #                 v)


# # t.dumpAllEntries("instruments")
