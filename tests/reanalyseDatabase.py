# =============================================================================
# reanalyseDatabase.py — rerun the analysis for every entry in the database
#
# Updates all analysis columns with the current Tudo code (sine histogram,
# onsets, spectral features, MFCC slots, dynamic profile, fluctuations, ...).
# Identifiers, transposability and paths are kept.
#
# Safe to interrupt: with ONLY_OUTDATED = True a restart continues with the
# entries that don't have the current analysis version yet.
# =============================================================================
import time
from Tudo.Tudo import Tudo
from Tudo.Sound import Sound

# ----------------------------------------------------------------------------
# settings
# ----------------------------------------------------------------------------
DB_PATH = "/Users/sraw/Documents/SAMPLES/TUDO/DB"
TABLE = "soundfile_analysis"

ONLY_OUTDATED = True     # skip entries already analysed with the current version
                         # (False = reanalyse everything)
UPDATE_TAGS = True       # also fix umlaut tags and add missing folder/file-name tags

# sine histogram (defaults shown)
SINE_SETTINGS = {"toleranceCents": 33, "size": 16,
                 "windowSize": 2**14, "hopLength": 2**12}

# onset detection (FluCoMa onsetslice parameters, see Onsets.py)
ONSET_SETTINGS = {"metric": 2, "threshold": 0.3}

# optional: only part of the library, same conditions as t.search(...)
# e.g. CONDITIONS = dict(pathContains="DRUM_MACHINES")
CONDITIONS = {}

# ----------------------------------------------------------------------------
# run
# ----------------------------------------------------------------------------
t = Tudo(DB_PATH)
t.connect()
t.sineSettings = SINE_SETTINGS
t.onsetSettings = ONSET_SETTINGS

# make sure all new columns exist before anything is selected
t.ensureColumns(TABLE)

total = t.count(TABLE, **CONDITIONS)
ids = None
if CONDITIONS:
    ids = [r["id"] for r in t.search(TABLE, columns=["id"], **CONDITIONS)]

if ONLY_OUTDATED:
    todo = t.count(TABLE, analysisVersion__ne=Sound.ANALYSIS_VERSION, **CONDITIONS) \
         + t.count(TABLE, analysisVersion__isnull=True, **CONDITIONS)
else:
    todo = total

print(f"\nTudo: {todo} of {total} entries to reanalyse "
      f"(analysis version {Sound.ANALYSIS_VERSION})\n")

start = time.time()
if todo:
    t.reanalyseEntries(TABLE, ids=ids, onlyOutdated=ONLY_OUTDATED)
elapsed = time.time() - start

if UPDATE_TAGS:
    print("\nTudo: checking tags ...")
    t.fixUmlautTags(tableName=TABLE, **dict(CONDITIONS))
    t.updateAutoIdentifiers(tableName=TABLE, **dict(CONDITIONS))

left = t.count(TABLE, analysisVersion__isnull=True, **CONDITIONS) \
     + t.count(TABLE, analysisVersion__ne=Sound.ANALYSIS_VERSION, **CONDITIONS)
print(f"\nTudo: done in {elapsed / 60:.1f} min")
if left:
    print(f"Tudo: {left} entries could not be analysed (missing or broken files?), "
          f"see the 'skipped' messages above")
