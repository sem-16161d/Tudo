#Tudo.py
import os
import re
import unicodedata
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
        # MFCC settings passed to every Sound (FluCoMa parameter names,
        # see MFCC.py). Example: t.mfccSettings["attack"]["numFrames"] = 96
        self.mfccSettings = {"summary": {}, "attack": {}, "sustain": {}}
        # sine histogram: error band in cents (+/-) and number of pitches
        self.sineSettings = {"toleranceCents": 33, "size": 16,
                             "windowSize": 2**14, "hopLength": 2**12}
    
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
                ("sineHistogram", "JSON"),
                ("sineToleranceCents", "FLOAT"),
                ("analysisVersion", "TEXT"),
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
                # timbre slots: MFCC matrices for training (see MFCC.py)
                *self.TIMBRE_SLOT_COLUMNS,
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

    def _sound(self, path, transposability=1):
        """Sound with this Tudo's MFCC settings."""
        return Sound(path, transposability=transposability,
                     mfccSettings=self.mfccSettings.get("summary"),
                     attackSettings=self.mfccSettings.get("attack"),
                     sustainSettings=self.mfccSettings.get("sustain"),
                     sineToleranceCents=self.sineSettings.get("toleranceCents", 33),
                     sineHistogramSize=self.sineSettings.get("size", 16),
                     sineWindowSize=self.sineSettings.get("windowSize", 2**14),
                     sineHopLength=self.sineSettings.get("hopLength", 2**12))

    def _columnTypes(self, tableName):
        if not hasattr(self, "_colTypes"):
            self._colTypes = {}
        if tableName not in self._colTypes:
            self._colTypes[tableName] = {n: t for n, t in self.dumpAllColumns(tableName)}
        return self._colTypes[tableName]

    def writeAnalysis(self, id, values, tableName="soundfile_analysis"):
        """
        Write a dict {column: value} into one row with a single
        parameterised UPDATE. JSON columns get Json(), array columns
        (REAL[]) get plain (nested) lists, numpy values are converted.
        """
        types = self._columnTypes(tableName)
        names, params = [], []
        for k, v in values.items():
            typ = types.get(k.lower())
            if typ is None:
                print(f"Tudo: no column '{k}' in {tableName}, skipped")
                continue
            if isinstance(v, np.ndarray):
                v = v.tolist()
            elif isinstance(v, np.generic):
                v = v.item()
            if typ in ("json", "jsonb"):
                v = Json(v)
            names.append(k)
            params.append(v)
        if not names:
            return
        assignments = ", ".join(f"{n} = %s" for n in names)
        self.cur.execute(f"UPDATE {tableName} SET {assignments} WHERE id = %s", params + [id])
        self.conn.commit()

    def newEntryFromSound(self, pathToSfile: str, identifiers = [], transposability = 1,
                          *, folderTags=True, filenameTags=True, rootFolder=None):
        """
        Analyse one sound file and add it to the database.
        identifiers are extended by the automatic tags (see autoIdentifiers):
        folder names between rootFolder and the file + words of the file name.
        """
        tags = self._mergeTags(list(identifiers), self.autoIdentifiers(
            pathToSfile, rootFolder, folderTags=folderTags, filenameTags=filenameTags))
        sound = self._sound(pathToSfile, transposability)
        sound.analyse()
        sound.addIntentifiers(tags)
        self.newEntry("soundfile_analysis")
        self.writeAnalysis(self.lastID["soundfile_analysis"], sound.analysisDict)
        return tags

    SAMPLES_ROOT = "/Users/sraw/Documents/SAMPLES/TUDO/SAMPLES"
    SKIP_FOLDER_NAMES = {"none"}          # placeholder folders in the taxonomy

    @staticmethod
    def _normaliseTag(name):
        """MUSIC_RADAR -> 'music radar', Prayer_Bowls -> 'prayer bowls',
        Förderband -> 'foerderband'."""
        return " ".join(Tudo._transliterate(name).replace("_", " ").split()).lower()

    _GERMAN = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
               "ß": "ss", "ẞ": "SS"}

    @staticmethod
    def _transliterate(text):
        """
        ASCII-only tags: ä -> ae, ö -> oe, ü -> ue, ß -> ss, other accents
        are removed (é -> e, ç -> c). macOS stores file names decomposed
        ('o' + combining diaeresis), so the text is NFC-normalised first.
        """
        text = unicodedata.normalize("NFC", str(text))
        text = "".join(Tudo._GERMAN.get(ch, ch) for ch in text)
        text = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in text if not unicodedata.combining(ch))

    def folderIdentifiers(self, filePath, rootFolder=None, normalise=True):
        """
        Names of all folders between rootFolder and the file, top to bottom.
        .../SAMPLES/MUSIC_RADAR/SPIRITUAL/Prayer_Bowls/x.wav
            -> ['music radar', 'spiritual', 'prayer bowls']
        Files outside rootFolder: only their own folder name is used.
        """
        root = os.path.abspath(rootFolder or self.SAMPLES_ROOT)
        folder = os.path.dirname(os.path.abspath(filePath))
        if os.path.commonpath([root, folder]) == root:
            parts = os.path.relpath(folder, root).split(os.sep)
            parts = [] if parts == ["."] else parts
        else:
            parts = [os.path.basename(folder)]
        tags = [self._normaliseTag(p) if normalise else p for p in parts]
        return [t for t in tags if t and t.lower() not in self.SKIP_FOLDER_NAMES]

    # words that carry no meaning as tags (extend as needed)
    FILENAME_STOPWORDS = {"a", "an", "the", "and", "or", "of", "in", "on", "at",
                          "to", "for", "with", "by", "from", "wav", "aif", "aiff"}

    def filenameIdentifiers(self, filePath, keepNumbers=False, minLength=2):
        """
        Individual words of the file name (without extension), lowercase.
        Split at everything that is not a letter or digit.
            Mouth_Fx_01.wav                -> ['mouth', 'fx']
            Cb-behind_bridge-N-N-2c-N.wav  -> ['cb', 'behind', 'bridge', '2c']
            07042047.wav                   -> []
            Untertage_FörderpanzerX.aif    -> ['untertage', 'foerderpanzerx']
        keepNumbers=False drops pure numbers (usually take indices),
        words shorter than minLength and FILENAME_STOPWORDS are dropped.
        """
        stem = self._transliterate(os.path.splitext(os.path.basename(filePath))[0])
        words = [w.lower() for w in re.split(r"[^0-9A-Za-z]+", stem) if w]
        return self._mergeTags([
            w for w in words
            if len(w) >= minLength
            and (keepNumbers or not w.isdigit())
            and w not in self.FILENAME_STOPWORDS])

    def autoIdentifiers(self, filePath, rootFolder=None, *, folderTags=True, filenameTags=True):
        """Automatic tags of a file: folder names, then file-name words."""
        tags = []
        if folderTags:
            tags = self._mergeTags(tags, self.folderIdentifiers(filePath, rootFolder))
        if filenameTags:
            tags = self._mergeTags(tags, self.filenameIdentifiers(filePath))
        return tags

    @staticmethod
    def _mergeTags(*lists):
        out = []
        for lst in lists:
            for tag in lst:
                if tag not in out:
                    out.append(tag)
        return out

    def newEntriesFromFolder(self, pathToFolder: str, identifiers = [], transposability = 1,
                             *, folderTags=True, filenameTags=True, rootFolder=None, recursive=True,
                             skipExisting=True, extensions=(".wav", ".aif", ".aiff", ".flac")):
        """
        Analyse all sound files in a folder and add them to the database.

        identifiers   : tags added to every file
        folderTags    : also add the names of all folders between rootFolder
                        and the file as individual tags (lowercase, '_' -> ' ',
                        'NONE' folders skipped)
        filenameTags  : also add the individual words of the file name
                        (see filenameIdentifiers)
        rootFolder    : where folder tags start (default Tudo.SAMPLES_ROOT)
        recursive     : include all subfolders (default; each file gets its
                        own folder tags). False = only this folder.
        skipExisting  : skip files whose path is already in the database
        """
        if recursive:
            files = sorted(os.path.join(d, f) for d, _, fs in os.walk(pathToFolder) for f in fs)
        else:
            files = sorted(os.path.join(pathToFolder, f) for f in os.listdir(pathToFolder))
        files = [f for f in files if os.path.isfile(f) and f.lower().endswith(tuple(extensions))
                 and not os.path.basename(f).startswith("._")]
        existing = set(self.searchPaths()) if skipExisting else set()

        for i, filePath in enumerate(files):
            name = os.path.relpath(filePath, pathToFolder)
            if filePath in existing:
                print(f"Tudo: {i+1}/{len(files)} already in database: {name}")
                continue
            print(f"Tudo: analysing {i+1}/{len(files)}  {name}")
            try:
                tags = self.newEntryFromSound(
                    filePath, identifiers, transposability, folderTags=folderTags,
                    filenameTags=filenameTags, rootFolder=rootFolder)
                print(f"      tags: {tags}")
            except Exception as e:
                print(f"Tudo: skipped {name}: {e}")

    def updateAutoIdentifiers(self, rootFolder=None, *, folderTags=True, filenameTags=True,
                              dryRun=False, tableName="soundfile_analysis", **conditions):
        """
        Go through the library and make sure every entry has its automatic
        tags (folder names + file-name words). Missing tags are appended,
        existing identifiers are kept. Takes search conditions to limit it,
        e.g. pathContains="CARTOONISH". dryRun=True only reports.
        Returns the number of entries that were (or would be) updated.
        """
        conditions["columns"] = ["id", "path", "identifiers"]
        rows = self.search(tableName, orderBy="id", **conditions)
        changed = 0
        for r in rows:
            current = r["identifiers"] or []
            missing = [tag for tag in self.autoIdentifiers(
                r["path"], rootFolder, folderTags=folderTags, filenameTags=filenameTags)
                if tag not in current]
            if not missing:
                continue
            changed += 1
            print(f"Tudo: [{r['id']}] {os.path.basename(r['path'])}  + {missing}")
            if not dryRun:
                self.writeAnalysis(r["id"], {"identifiers": current + missing}, tableName)
        verb = "would update" if dryRun else "updated"
        print(f"Tudo: checked {len(rows)} entries, {verb} {changed}")
        return changed

    def _legacyAutoIdentifiers(self, filePath, rootFolder=None):
        """Automatic tags exactly as generated before the umlaut fix (for cleanup)."""
        root = os.path.abspath(rootFolder or self.SAMPLES_ROOT)
        folder = os.path.dirname(os.path.abspath(filePath))
        if os.path.commonpath([root, folder]) == root:
            parts = os.path.relpath(folder, root).split(os.sep)
            parts = [] if parts == ["."] else parts
        else:
            parts = [os.path.basename(folder)]
        tags = {" ".join(p.replace("_", " ").split()).lower() for p in parts}
        tags = {t for t in tags if t and t not in self.SKIP_FOLDER_NAMES}
        stem = os.path.splitext(os.path.basename(filePath))[0]
        words = [w.lower() for w in re.split(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ]+", stem) if w]
        tags |= {w for w in words if len(w) >= 2 and not w.isdigit()
                 and w not in self.FILENAME_STOPWORDS}
        return tags

    def fixUmlautTags(self, rootFolder=None, dryRun=False, tableName="soundfile_analysis", **conditions):
        """
        One-off cleanup for entries tagged before the umlaut fix:
        removes broken automatic tags (e.g. 'rderpanzerx', or tags with
        decomposed umlauts) and adds the correct ones ('foerderpanzerx').
        Only tags the old method could have produced are removed, and only
        if the new method doesn't produce them. dryRun=True only reports.
        """
        conditions["columns"] = ["id", "path", "identifiers"]
        rows = self.search(tableName, orderBy="id", **conditions)
        changed = 0
        for r in rows:
            current = r["identifiers"] or []
            new = self.autoIdentifiers(r["path"], rootFolder)
            legacy = self._legacyAutoIdentifiers(r["path"], rootFolder)
            broken = [t for t in current if t in legacy and t not in new]
            fixed = self._mergeTags([t for t in current if t not in broken], new)
            if fixed == current:
                continue
            changed += 1
            print(f"Tudo: [{r['id']}] {os.path.basename(r['path'])}  - {broken}  + {[t for t in fixed if t not in current]}")
            if not dryRun:
                self.writeAnalysis(r["id"], {"identifiers": fixed}, tableName)
        verb = "would fix" if dryRun else "fixed"
        print(f"Tudo: checked {len(rows)} entries, {verb} {changed}")
        return changed

    def updateFolderIdentifiers(self, rootFolder=None, tableName="soundfile_analysis", **conditions):
        """Folder tags only (see updateAutoIdentifiers)."""
        return self.updateAutoIdentifiers(rootFolder, filenameTags=False,
                                          tableName=tableName, **conditions)

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

    def addColumn(self, tableName="tableNo1", columnName="columnNo1", valueType="FLOAT"):
        super().addColumn(tableName, columnName, valueType)
        self._clearColumnCaches(tableName)

    def _clearColumnCaches(self, tableName):
        for cache in ("_searchColumns", "_colTypes"):
            if hasattr(self, cache):
                getattr(self, cache).pop(tableName, None)

    def addMissingColumns(self, columns, tableName="soundfile_analysis"):
        """Add columns to an existing table (skips the ones that exist)."""
        for name, typ in columns:
            self.executeQuery(
                f"ALTER TABLE {tableName} ADD COLUMN IF NOT EXISTS {name} {typ}")
        self._clearColumnCaches(tableName)

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
        Compute the Peeters spectral features (incl. MFCC summary) for
        entries already in the database. onlyMissing=True skips entries
        that already have them. kwargs go to Sound.getSpectralFeatures.
        """
        self.addMissingColumns(spectralColumns(), tableName)
        where = " WHERE specCentroidMain IS NULL" if onlyMissing else ""
        self.cur.execute(f"SELECT id, path FROM {tableName}{where} ORDER BY id")
        rows = self.cur.fetchall()
        self.conn.commit()
        for i, (id, path) in enumerate(rows):
            print(f"Tudo: spectral features {i+1}/{len(rows)}  {os.path.basename(path)}")
            try:
                sound = self._sound(path)
                values = analysisDictEntries(sound.getSpectralFeatures(**kwargs))
            except Exception as e:
                print(f"Tudo: skipped id {id}: {e}")
                continue
            self.writeAnalysis(id, values, tableName)

    def reanalyseEntries(self, tableName="soundfile_analysis", ids=None, onlyOutdated=False):
        """
        Re-run the full Sound.analyse() on entries already in the database
        and overwrite all analysis columns (identifiers and transposability
        are kept). Adds missing columns first. ids=None -> all entries.
        onlyOutdated=True skips entries already analysed with the current
        Sound.ANALYSIS_VERSION, so an interrupted run can simply be restarted.
        """
        self.addMissingColumns(self.DYNAMIC_PROFILE_COLUMNS, tableName)
        self.addMissingColumns(spectralColumns(), tableName)
        self.addMissingColumns(self.TIMBRE_SLOT_COLUMNS, tableName)
        self.addMissingColumns([("sineHistogram", "JSON"), ("sineToleranceCents", "FLOAT"),
                                ("analysisVersion", "TEXT")], tableName)
        sql = f"SELECT id, path, transposability FROM {tableName}"
        where, params = [], []
        if ids is not None:
            where.append("id = ANY(%s)")
            params.append(list(ids))
        if onlyOutdated:
            where.append("analysisVersion IS DISTINCT FROM %s")
            params.append(Sound.ANALYSIS_VERSION)
        if where:
            sql += " WHERE " + " AND ".join(where)
        self.cur.execute(sql + " ORDER BY id", params)
        rows = self.cur.fetchall()
        self.conn.commit()
        for i, (id, path, transp) in enumerate(rows):
            print(f"Tudo: reanalysing {i+1}/{len(rows)}  {os.path.basename(path)}")
            try:
                sound = self._sound(path, transp if transp is not None else 1)
                sound.analyse()
            except Exception as e:
                print(f"Tudo: skipped id {id}: {e}")
                continue
            values = {k: v for k, v in sound.analysisDict.items()
                      if k not in ("identifiers", "transposability", "path")}
            self.writeAnalysis(id, values, tableName)

    TIMBRE_SLOT_COLUMNS = [
        ("mfccAttack", "REAL[]"),
        ("mfccAttackFrames", "INT"),
        ("mfccSustain", "REAL[]"),
        ("mfccSustainFrames", "INT"),
        ("attackStartSec", "FLOAT"),
        ("attackEndSec", "FLOAT"),
        ("logAttackTime", "FLOAT"),
        ("mfccSettings", "JSON"),
    ]

    def loadTimbreSlots(self, tableName="soundfile_analysis", **conditions):
        """
        Training data: returns a dict of numpy arrays for all sounds
        matching the search conditions (same syntax as search):
            attack        (N, numCoeffs, numFrames)  float32
            attackFrames  (N,) valid frames (rest is padding)
            sustain       (N, numCoeffs, numFrames)  float32
            sustainFrames (N,)
            logAttackTime (N,)
            ids, paths, identifiers : lists
        All entries must have been analysed with the same slot settings.
        """
        conditions["columns"] = ["id", "path", "identifiers", "mfccAttack",
                                 "mfccAttackFrames", "mfccSustain",
                                 "mfccSustainFrames", "logAttackTime"]
        conditions["mfccAttack__isnull"] = False
        rows = self.search(tableName, **conditions)
        if not rows:
            return None
        shapes = {np.shape(r["mfccattack"]) for r in rows} | {np.shape(r["mfccsustain"]) for r in rows}
        if len({np.shape(r["mfccattack"]) for r in rows}) > 1 or \
           len({np.shape(r["mfccsustain"]) for r in rows}) > 1:
            raise ValueError(f"Tudo.loadTimbreSlots: mixed slot shapes {shapes}, "
                             "reanalyse with one setting or filter the entries")
        return dict(
            attack=np.array([r["mfccattack"] for r in rows], dtype=np.float32),
            attackFrames=np.array([r["mfccattackframes"] for r in rows]),
            sustain=np.array([r["mfccsustain"] for r in rows], dtype=np.float32),
            sustainFrames=np.array([r["mfccsustainframes"] for r in rows]),
            logAttackTime=np.array([r["logattacktime"] for r in rows], dtype=np.float32),
            ids=[r["id"] for r in rows],
            paths=[r["path"] for r in rows],
            identifiers=[r["identifiers"] for r in rows],
        )
