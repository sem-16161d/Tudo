from Tudo.Tudo import Tudo

t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/PSQL/")
t.connect()
t.getAllColumnsAndTables()

# for _ in range(20): t.newEntry()


for i in range(70):
    t.deleteEntryByID(i+1, "soundfile_analysis")
# t.newEntry("soundfile_analysis")
# print(t.lastID)

t.dumpAllEntries("soundfile_analysis")
t.killAllServerInstances()
# t.addColumn("soundfile_analysis","timestamp","TIMESTAMP")