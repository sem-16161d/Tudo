# =============================================================================
# purgeByTag.py — remove database entries by tag
#
# Deletes rows from the Tudo database. The sound files on disk are NOT touched.
# Shows what will be deleted and asks for confirmation first.
# =============================================================================
from Tudo.Tudo import Tudo

# ----------------------------------------------------------------------------
# settings
# ----------------------------------------------------------------------------
DB_PATH = "/Users/sraw/Documents/SAMPLES/TUDO/DB"
TABLE = "soundfile_analysis"

# Tags to purge. Folder tags are stored normalised (RAW_MATERIALS -> "raw materials"),
# so both spellings are listed here.
TAGS = ["viola"]

# "exact"    -> entries that have one of TAGS exactly (case-sensitive)
# "contains" -> entries with a tag CONTAINING one of TAGS (case-insensitive),
#               e.g. "raw" would also match "raw materials" and "straw"
MODE = "exact"

PREVIEW = 30          # number of paths to print before asking
ASK_FIRST = True      # False = delete without asking (careful)

# ----------------------------------------------------------------------------
# run
# ----------------------------------------------------------------------------
t = Tudo(DB_PATH)
t.connect()

if MODE == "exact":
    conditions = dict(anyTags=TAGS)
elif MODE == "contains":
    conditions = dict(anyTagContains=TAGS)
else:
    raise ValueError(f"MODE must be 'exact' or 'contains', not {MODE!r}")

rows = t.search(TABLE, columns=["id", "path", "identifiers"], orderBy="path", **conditions)
total = t.count(TABLE)

print(f"\n{len(rows)} of {total} entries match {MODE} {TAGS}\n")
if not rows:
    raise SystemExit("nothing to purge")

for r in rows[:PREVIEW]:
    print(f"  [{r['id']:>6}] {r['path']}")
if len(rows) > PREVIEW:
    print(f"  ... and {len(rows) - PREVIEW} more")

if ASK_FIRST:
    answer = input(f"\nDelete these {len(rows)} entries from the database? (type 'yes'): ")
    if answer.strip().lower() != "yes":
        raise SystemExit("cancelled, nothing deleted")

ids = [r["id"] for r in rows]
t.cur.execute(f"DELETE FROM {TABLE} WHERE id = ANY(%s)", (ids,))
deleted = t.cur.rowcount
t.conn.commit()

print(f"\ndeleted {deleted} entries, {t.count(TABLE)} left")
print(f"still matching: {t.count(TABLE, **conditions)}")
