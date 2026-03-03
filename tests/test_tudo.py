from Tudo.Tudo import Tudo

t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/PSQL/")

# t.initializeNewDatabase()
# t.setupTables()
t.connect()
t.getAllColumnsAndTables()
for c in t.columnNames:
    print(c)
    for p in t.columnNames[c]:
        print("   ",p)