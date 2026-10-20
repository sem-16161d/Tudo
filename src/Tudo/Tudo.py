#Tudo.py
import os
import subprocess
from Tudo.PSQL import PSQL
from Tudo.Sound import Sound

class Tudo(PSQL):
    def __init__(
        self,
        libraryPath = "/Users/sraw/Documents/SAMPLES/TUDO/DB/"):
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
            
            

    def setupTableInstrumentCharacteristic(self, instrument = "dummy"):
        tableName = instrument+"_characteristics"
        self.addTable(tableName)
        for column in [
            ("playingtechnique", "TEXT"),
            ("roughnessMedian", "FLOAT"),
            ("flatnessMedian", "FLOAT"),
            ("spectraldensity", "FLOAT"),
            ("pitchcentroidratio", "FLOAT"),
        ]:
            self.addColumn(tableName,column[0], column[1])

    def setupTables(self):
        self.killAllServerInstances()
        self.startNewServer()
        self.connectToDatabase(self.dbname)
        self.addTable("soundfile_analysis")
        for column in [
                ("identifiers", "JSON"),
                ("path", "TEXT"),
                ("durationSec", "FLOAT"), 
                ("sampleRate", "INT"),
                ("peakAmplitudedB", "FLOAT"),
                ("mainPitchHz", "FLOAT"),
                ("spectralDensity", "FLOAT"),
                ("roughness", "FLOAT"),
                ("centroidMostCommon", "FLOAT"),
                ("pitchcentroidratio", "FLOAT"),
                ("flatnessMedian", "FLOAT"),
                ("transposability", "INT"),
                # pitch fluctuation
                ("pitchFluctRate", "FLOAT"),
                ("pitchFluctDepth", "FLOAT"),
                ("pitchFluctStrength", "FLOAT"),
                # amplitude fluctuation
                ("ampFluctRate", "FLOAT"),
                ("ampFluctDepth", "FLOAT"),
                ("ampFluctStrength", "FLOAT"),
                # spectral fluctuation
                ("spectFluctMean", "FLOAT"),
                ("spectFluctVariance", "FLOAT"),
                ("spectFluctRate", "FLOAT"),
                ("spectFluctStrength", "FLOAT"),
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
            ("physicalDynamicdBmin", "FLOAT"),
            ("physicalDynamicdBmax", "FLOAT"),
            ("writtenDynMin", "TEXT"),
            ("writtenDynMax", "TEXT"),
            ("numSystems","INT"),
            ("microtones", "BOOL"),
            ("transpositionSemitones", "FLOAT"),
            ("chords", "BOOL"),
            ("multiphonics", "BOOL"),
            ("numSystems", "INT"),
            ("materials", "JSON"),
            ("playingTechniques", "JSON"),
            ("possibleClefs", "JSON"),
            ]:
            self.addColumn("instruments", 
                    column[0], 
                    column[1])


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

    def newEntryFromSound(self, pathToSfile: str, identifiers = [], transposability = 1):
        sound = Sound(pathToSfile, transposability=transposability)
        sound.analyse()
        sound.addIntentifiers(identifiers)
        self.newEntry("soundfile_analysis")
        for key in sound.analysisDict:
            self.updateEntry(
                self.lastID["soundfile_analysis"],
                key,
                "soundfile_analysis",
                sound.analysisDict[key])

    def newEntriesFromFolder(self, pathToFolder: str, identifiers = [],transposability = 1):
        numSounds = len(os.listdir(pathToFolder))
        for i,filename in enumerate(os.listdir(pathToFolder)):
            print(f"Tudo: Analysing File {i}/{numSounds}")
            filePath = os.path.join(pathToFolder, filename)
            if os.path.isfile(filePath) and filename.lower().endswith(('.wav')):
                self.newEntryFromSound(filePath, identifiers,transposability)
            