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
        column =("instrument", "TEXT")
        for column in [
                ("instrument", "TEXT"),
                ("path", "TEXT"),
                ("durationSec", "FLOAT"), ("sampleRate", "INT"),
                ("peakAmplitudedB", "FLOAT"),
                ("mainPitchHz", "FLOAT"),
                ("spectralDensity", "FLOAT"),
                ("roughness", "FLOAT"),
                ("centroidMostCommon", "FLOAT"),
                ("flatnessMedian", "FLOAT")]:
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
            ("transpositionSemitines", "FLOAT"),
            ("chords", "BOOL"),
            ("multiphonices", "BOOL"),
            ("numSystems", "INT"),
            ("materials", "JSON"),
            ("playingTechniques", "JSON")
            ]:
            self.addColumn("instruments", 
                    column[0], 
                    column[1])


    def connect(self):
        self.killAllServerInstances()
        self.startNewServer()
        self.connectToDatabase(self.dbname)
