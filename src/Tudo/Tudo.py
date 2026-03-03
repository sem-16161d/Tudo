#Tudo.py
from os import wait
import psycopg2
import subprocess

class Tudo():
    def __init__(
        self,
        libraryPath = "/Users/sraw/Documents/SAMPLES/TUDO/"):
        self.librayPath = libraryPath
        self.stopServer()
        self.startNewServer()
        self.dbnames = []
        self.conn = None
        self.cur = None

    def initNewDatabaseCluster(self):
        subprocess.run([f"initdb -D {self.librayPath}"], shell=True)

    def checkServerStatus(self):
        subprocess.run([f"pg_ctl -D {self.librayPath} status"], shell=True)

    def startNewServer(self):
        subprocess.run([f"pg_ctl -D {self.librayPath} start"], shell=True)

    def stopServer(self):
        subprocess.run([f"pg_ctl -D {self.librayPath} stop"], shell=True)

    def newDatabase(self,dbname = "mydb"):
        self.dbnames.append(dbname)
        subprocess.run([f"createdb {dbname}"], shell=True)

    def connectToServer(self, dbname = "mydb"):
        self.conn = psycopg2.connect(dbname= dbname)
        self.cur = self.conn.cursor()
        return

    def executeQuery(self, query, vars):
        if vars:
            self.cur.execute(query, vars)
        else:
            self.cur.execute(query)
        self.conn.commit()