#Tudo.py
import os
import subprocess
import numpy as np
from Tudo.PSQL import PSQL
from Tudo.Sound import Sound
from Tudo.Search import buildSearchQuery
from Tudo.SpectralFeatures import databaseColumns as spectralColumns, analysisDictEntries
from psycopg2.extras import Json

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
                # dynamic profile
                ("dynProfile", "TEXT"),
                ("dynSlope1", "FLOAT"),
                ("dynRelDur1", "FLOAT"),
                ("dynSlope2", "FLOAT"),
                ("dynRelDur2", "FLOAT"),
                ("dynEffDur", "FLOAT"),
                # Peeters spectral features (see SpectralFeatures.py)
                *spectralColumns(),
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


    # ------------------------------------------------------------------
    # conditional search
    # ------------------------------------------------------------------
    def searchColumns(self, tableName="soundfile_analysis"):
        """Column names available for search (cached per table)."""
        if not hasattr(self, "_searchColumns"):
            self._searchColumns = {}
        if tableName not in self._searchColumns:
            self._searchColumns[tableName] = [c[0] for c in self.dumpAllColumns(tableName)]
        return self._searchColumns[tableName]

    def search(self, tableName="soundfile_analysis", **conditions):
        """
        Conditional search, returns a list of dicts (one per sound).
        See Tudo/Search.py for the full syntax. Example:

            t.search(durationSec__gt=2, flatnessMedian__between=(0.1, 0.5),
                     tags=["bassoon", "multiphonic"], noTags=["noise"],
                     orderBy="-centroidMostCommon", limit=20)
        """
        sql, params = buildSearchQuery(
            tableName, self.searchColumns(tableName), **conditions)
        self.cur.execute(sql, params)
        names = [d[0] for d in self.cur.description]
        rows = [dict(zip(names, r)) for r in self.cur.fetchall()]
        self.conn.commit()
        return rows

    def searchPaths(self, tableName="soundfile_analysis", **conditions):
        """Like search, but returns only the file paths."""
        conditions["columns"] = ["path"]
        return [r["path"] for r in self.search(tableName, **conditions)]

    def count(self, tableName="soundfile_analysis", **conditions):
        """Number of sounds matching the conditions."""
        for k in ("orderBy", "limit", "offset", "random", "columns"):
            conditions.pop(k, None)
        sql, params = buildSearchQuery(
            tableName, self.searchColumns(tableName), **conditions)
        sql = sql.replace("SELECT *", "SELECT COUNT(*)", 1)
        self.cur.execute(sql, params)
        n = self.cur.fetchone()[0]
        self.conn.commit()
        return n

    def copyResults(self, results, destination="/private/tmp/tudo_results", clear=True):
        """Copy the files of a search result (dicts or paths) into a folder."""
        import shutil
        if clear and os.path.exists(destination):
            shutil.rmtree(destination)
        os.makedirs(destination, exist_ok=True)
        paths = [r["path"] if isinstance(r, dict) else r for r in results]
        for p in paths:
            shutil.copy(p, destination)
        print(f"Tudo: copied {len(paths)} files to {destination}")
        return destination


    # ------------------------------------------------------------------
    # migrations / re-analysis of existing entries
    # ------------------------------------------------------------------
    DYNAMIC_PROFILE_COLUMNS = [
        ("dynProfile", "TEXT"),
        ("dynSlope1", "FLOAT"),
        ("dynRelDur1", "FLOAT"),
        ("dynSlope2", "FLOAT"),
        ("dynRelDur2", "FLOAT"),
        ("dynEffDur", "FLOAT"),
    ]

    def addMissingColumns(self, columns, tableName="soundfile_analysis"):
        """Add columns to an existing table (skips the ones that exist)."""
        for name, typ in columns:
            self.executeQuery(
                f"ALTER TABLE {tableName} ADD COLUMN IF NOT EXISTS {name} {typ}")
        if hasattr(self, "_searchColumns"):
            self._searchColumns.pop(tableName, None)

    def updateDynamicProfiles(self, onlyMissing=True, tableName="soundfile_analysis", **kwargs):
        """
        Compute the dynamic profile for entries already in the database.
        onlyMissing=True skips entries that already have one.
        kwargs go to Sound.getDynamicProfile.
        """
        self.addMissingColumns(self.DYNAMIC_PROFILE_COLUMNS, tableName)
        where = " WHERE dynProfile IS NULL" if onlyMissing else ""
        self.cur.execute(f"SELECT id, path FROM {tableName}{where} ORDER BY id")
        rows = self.cur.fetchall()
        self.conn.commit()
        for i, (id, path) in enumerate(rows):
            print(f"Tudo: dynamic profile {i+1}/{len(rows)}  {os.path.basename(path)}")
            try:
                sound = Sound(path)
                profile = sound.getDynamicProfile(**kwargs)
            except Exception as e:
                print(f"Tudo: skipped id {id}: {e}")
                continue
            f = sound.dynamicProfileFeatures
            self.cur.execute(
                f"""UPDATE {tableName} SET dynProfile = %s, dynSlope1 = %s,
                    dynRelDur1 = %s, dynSlope2 = %s, dynRelDur2 = %s,
                    dynEffDur = %s WHERE id = %s""",
                (profile, f["slope1"], f["relDur1"], f["slope2"],
                 f["relDur2"], f["effDur"], id))
            self.conn.commit()

    def updateSpectralFeatures(self, onlyMissing=True, tableName="soundfile_analysis", **kwargs):
        """
        Compute the Peeters spectral features for entries already in the
        database. onlyMissing=True skips entries that already have them.
        kwargs go to Sound.getSpectralFeatures (minHz, maxHz).
        """
        cols = spectralColumns()
        self.addMissingColumns(cols, tableName)
        where = " WHERE specCentroidMain IS NULL" if onlyMissing else ""
        self.cur.execute(f"SELECT id, path FROM {tableName}{where} ORDER BY id")
        rows = self.cur.fetchall()
        self.conn.commit()
        for i, (id, path) in enumerate(rows):
            print(f"Tudo: spectral features {i+1}/{len(rows)}  {os.path.basename(path)}")
            try:
                sound = Sound(path)
                values = analysisDictEntries(sound.getSpectralFeatures(**kwargs))
            except Exception as e:
                print(f"Tudo: skipped id {id}: {e}")
                continue
            names = list(values)
            assignments = ", ".join(f"{n} = %s" for n in names)
            params = [Json(values[n]) if isinstance(values[n], list) else values[n] for n in names]
            self.cur.execute(
                f"UPDATE {tableName} SET {assignments} WHERE id = %s", params + [id])
            self.conn.commit()

    def reanalyseEntries(self, tableName="soundfile_analysis", ids=None):
        """
        Re-run the full Sound.analyse() on entries already in the database
        and overwrite all analysis columns (identifiers and transposability
        are kept). Adds missing columns first. ids=None -> all entries.
        """
        self.addMissingColumns(self.DYNAMIC_PROFILE_COLUMNS, tableName)
        self.addMissingColumns(spectralColumns(), tableName)
        sql = f"SELECT id, path, transposability FROM {tableName}"
        params = None
        if ids is not None:
            sql += " WHERE id = ANY(%s)"
            params = (list(ids),)
        self.cur.execute(sql + " ORDER BY id", params)
        rows = self.cur.fetchall()
        self.conn.commit()
        for i, (id, path, transp) in enumerate(rows):
            print(f"Tudo: reanalysing {i+1}/{len(rows)}  {os.path.basename(path)}")
            try:
                sound = Sound(path, transposability=transp if transp is not None else 1)
                sound.analyse()
            except Exception as e:
                print(f"Tudo: skipped id {id}: {e}")
                continue
            values = {k: v for k, v in sound.analysisDict.items()
                      if k not in ("identifiers", "transposability", "path")}
            names = list(values)
            assignments = ", ".join(f"{n} = %s" for n in names)
            params = [Json(values[n]) if isinstance(values[n], (list, dict)) else
                      (float(values[n]) if isinstance(values[n], np.generic) else values[n])
                      for n in names]
            self.cur.execute(
                f"UPDATE {tableName} SET {assignments} WHERE id = %s", params + [id])
            self.conn.commit()

