from Tudo.Tudo import Tudo

t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/DB")
t.connect()
# print(t.dumpAllTables())              # see what's in there

# t.dropTable("soundfile_analysis")
# t.dropTable("instruments")            # leave this out if you want to keep instrument data
# t.setupTables()                       # recreates both tables with all the new columns