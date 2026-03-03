#Tudo.py
from os import wait
import subprocess
from Tudo.PSQL import PSQL

class Tudo(PSQL):
    def __init__(
        self,
        libraryPath = "/Users/sraw/Documents/SAMPLES/TUDO/PSQL/"):
        super().__init__(libraryPath)
        self.dbname = "tudo"
        self.lastID = {"soundfile_analysis": 0,"instruments":0}
    
    def initializeNewDatabase(self):
        newTudo = input("do you really want to create a new Tudo? (y/n)")
        if newTudo == "y":
            subprocess.run([f"dropdb tudo"], shell=True)
            self.killAllServerInstances()
            self.initNewDatabaseCluster()
            
            self.startNewServer()
            self.newDatabase(self.dbname)
            self.connectToDatabase(self.dbname)
            

    def setupTables(self):
        self.killAllServerInstances()
        self.startNewServer()
        self.connectToDatabase(self.dbname)
        self.addTable("soundfile_analysis")
        print(self.dumpAllTables(self.dbname))
        for column in [
                ("instrument", "TEXT"),
                ("path", "TEXT"),
                ("durationSec", "FLOAT"), 
                ("sampleRate", "INT"),
                ("peakAmplitudedB", "FLOAT"),
                ("mainPitchHz", "FLOAT"),
                ("spectralDensity", "FLOAT"),
                ("roughness", "FLOAT"),
                ("centroidMostCommon", "FLOAT"),
                ("flatnessMedian", "FLOAT"),
                ("created_at","TIMESTAMP DEFAULT CURRENT_TIMESTAMP")]:
                self.addColumn(
                    "soundfile_analysis", 
                    column[0], 
                    column[1])

        self.addTable("instruments")
        for column in [
            ("lowestNoteMidi","FLOAT"),
            ("highestNoteMidi","FLOAT"),
            ("commonTuningReference","JSON"),
            ("lowestFreqHz","FLOAT"),
            ("highestFreqHz","FLOAT"),
            ("numSystems","INT"),
            ("microtones", "BOOL"),
            ("transpositionSemitones", "FLOAT"),
            ("chords", "BOOL"),
            ("multiphonics", "BOOL"),
            ("numSystems", "INT"),
            ("materials", "JSON"),
            ("playingTechniques", "JSON")
            ]:
            self.addColumn("instruments", 
                    column[0], 
                    column[1])

    # def newEntry(self, tableName="soundfile_analysis"):
    #     self.lastID[tableName] = super().newEntry(tableName)

    def connect(self):
        self.killAllServerInstances()
        self.startNewServer()
        self.connectToDatabase(self.dbname)

    def newEntry(self, tableName="tableNo1"):
        id =  super().newEntry(tableName)
        self.lastID[tableName] = id[0]

    def deleteEntryByID(self, id, tableName):
        cmd = f"""
        DELETE FROM {tableName} WHERE id = {id};
        """
        self.executeQuery(cmd)

    def newEntryFromSound(self, pathToSfile: str):
        return