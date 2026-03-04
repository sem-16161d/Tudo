from Tudo.Tudo import Tudo


t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/PSQL/")
t.connect()
t.getAllColumnsAndTables()

path = "SAMPLES/ACOUSTIC_INSTRUMENTS/STRING/VIOLA/TREMOLO_SUL_PONTICELLO"
idents = (
        "viola",
        "TREMOLO_SUL_PONTICELLO"
)
# for i in range(10000): 
#         t.deleteEntryByID(i,"soundfile_analysis")
t.newEntriesFromFolder(path,
idents)
# t.dumpAllEntries("soundfile_analysis")
t.killAllServerInstances()