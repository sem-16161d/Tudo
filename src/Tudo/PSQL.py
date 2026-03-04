#Tudo.py
import json
from os import wait
import psycopg2
import subprocess

class PSQL():
    def __init__(
        self,
        libraryPath = "/tmp/dummydatabase",
        *,
        autostart= False):
        self.librayPath = libraryPath
        self.tableNames = []
        self.columnNames = dict()
        self.dbname = None
        self.conn = None
        self.cur = None
        if autostart:
            self.stopServer()
            self.startNewServer()
            if self.dbname is None:
                self.connectToDatabase()
            else:
                print("PSQL: can't connect to database, no data name is chosen!")
        
    def initNewDatabaseCluster(self):
        subprocess.run([f"initdb -D {self.librayPath}"], shell=True)

    def checkServerStatus(self):
        subprocess.run([f"pg_ctl -D {self.librayPath} status"], shell=True)

    def startNewServer(self):
        subprocess.run([f"pg_ctl -D {self.librayPath} start"], shell=True)

    def stopServer(self):
        subprocess.run([f"pg_ctl -D {self.librayPath} stop"], shell=True)

    def killAllServerInstances(self):
        subprocess.run(["pkill -9 postgres"], shell=True)

    def newDatabase(self,dbname = "mydb"):
        self.dbname = dbname
        subprocess.run([f"createdb {dbname}"], shell=True)

    def dumpDatabasesFromServer(self):
        subprocess.run(["pg_dumpall --data-only"], shell=True)


    def connectToDatabase(self, dbname = "mydb"):
        self.conn = psycopg2.connect(
            dbname=dbname,
            host="localhost",
            port="5432")
        self.cur = self.conn.cursor()
        return
    
    def executeQuery(self, query, vars = ()):
        if len(vars) > 0:
            self.cur.execute(query, vars)  # pyright: ignore[reportOptionalMemberAccess]
        else:
            self.cur.execute(query)  # pyright: ignore[reportOptionalMemberAccess]
        self.conn.commit()  # pyright: ignore[reportOptionalMemberAccess]

    def executeAndReturn(self, query, vars = ()):
        self.executeQuery(query, vars)
        return self.cur.fetchall()

    def addTable(self, tableName = "tableNo1"):
        cmd = (f"CREATE TABLE {tableName} (id serial PRIMARY KEY)")
        self.tableNames.append(tableName)
        self.executeQuery(cmd)

    def dropTable(self, tableName = "tableNo1"):
        cmd = (f"DROP TABLE {tableName}")
        self.tableNames.remove(tableName)
        self.executeQuery(cmd)
    
    def dumpAllTables(self, dbname = "mydb"):
        self.executeQuery("""
        SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'
        """)
        return self.cur.fetchall()

    def addColumn(self, tableName = "tableNo1", columnName = "columnNo1", valueType = "FLOAT"):
        cmd = (f"ALTER TABLE {tableName} ADD COLUMN {columnName} {valueType}")
        if tableName not in self.columnNames:
            self.columnNames[tableName] = []
        self.columnNames[tableName].append(columnName)
        self.executeQuery(cmd)

    def dumpAllColumns(self, tableName="tableNo1"):
        cmd = """
            SELECT 
            attname AS column_name,
            format_type(atttypid, atttypmod) AS data_type
            FROM pg_attribute wHERE 
            attrelid = %s::regclass
            AND attnum > 0
            AND NOT attisdropped
            ORDER BY attnum
        """
        self.executeQuery(cmd, (tableName,))
        return [row[:2] for row in self.cur.fetchall()]  # pyright: ignore[reportOptionalMemberAccess]
    
    def getColumnNamesFromTable(self, tableName = "tableNo1"):
        self.columnNames[tableName] = self.dumpAllColumns(tableName)

    def getAllColumnsAndTables(self):
        for table in self.dumpAllTables(self.librayPath):
            tableName = table[0]
            self.columnNames[tableName] = self.dumpAllColumns(tableName)


    def newEntry(self, tableName = "tableNo1"):
        cmd = f"""
            INSERT INTO {tableName} DEFAULT VALUES RETURNING id
        """
        self.executeQuery(cmd, (tableName,))
        return [row[0] for row in self.cur.fetchall()]  # pyright: ignore[reportOptionalMemberAccess]
    
    def updateEntry(self, id, columnName, tableName, value):
        value = formatValue(value)
        cmd = (
            f"UPDATE {tableName} SET {columnName} = {value} where ID = {id}")
        self.executeQuery(cmd)

    def dumpAllEntries(self, tableName = "tableNo1"):
        self.executeQuery(f"SELECT * FROM {tableName}")
        for row in self.cur.fetchall():  # pyright: ignore[reportOptionalMemberAccess]
            print(row)

def formatValue(value):
    if isinstance(value, str):
        return f"'{value}'"
    elif isinstance(value, list):
        return f"'{json.dumps(value)}'"   # JSON string for SQL
    else:
        return str(value)