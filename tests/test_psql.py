#test_psql.py
from Tudo.PSQL import PSQL

psql = PSQL()
# psql.initNewDatabaseCluster()
psql.killAllServerInstances()
psql.startNewServer()
# psql.newDatabase()
psql.connectToDatabase()
# psql.addTable("tab2")
# psql.dropTable()
# psql.dumpDatabasesFromServer()
# psql.addColumn(columnName="column2", valueType="TEXT")

# for _ in range(10): psql.newEntry()
psql.getAllColumnsAndTables()
# psql.dumpAllEntries()
print(psql.columnNames)
