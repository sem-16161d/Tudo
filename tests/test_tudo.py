from Tudo.Tudo import Tudo

t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/PSQL/")
# t.checkServerStatus()
# t.stopServer()
# # t.initNewDatabaseCluster()
# t.startNewServer()
t.connectToServer()

t.executeQuery("INSERT INTO test (num, data) VALUES (%s, %s)",(100, "abc'def"))

t.cur.execute("SELECT id, num FROM test order by num")

for record in t.cur:
    print(record)

t.cur.execute("SELECT * FROM test")
print(t.cur.fetchmany(-1))