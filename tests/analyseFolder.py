from Tudo.Tudo import Tudo
from Tudo.Sound import Sound

t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/DB")

t.connect()

# SAMPLES/MUSIC_RADAR/tunefultoy
# # whole folder
t.newEntriesFromFolder(
    "/Users/sraw/Documents/SAMPLES/TUDO/SAMPLES/ACOUSTIC_INSTRUMENTS/BRASS/HORN_IN_F",
    identifiers=[
        "metal", "instrument" , "blown", ],
    transposability=1
)

# checkup

# from collections import Counter

# rows = t.search(tags=["prayer", "bowl"], orderBy="mainPitchHz")
# print(len(rows), "entries")

# # overview: one line per sound
# for r in rows:
#     print(f"{r['path'].split('/')[-1][:40]:40s} "
#           f"{r['durationsec']:6.2f}s  "
#           f"pitch {r['mainpitchhz']:7.1f} Hz  "
#           f"{r['dynprofile']:22s} "
#           f"tonality {r['spectonalitymain']:.2f}  "
#           f"centroid {r['speccentroidmain']:7.0f} Hz")

# # how the dynamic profiles came out
# print(Counter(r["dynprofile"] for r in rows))

# # everything stored for one sound
# for k, v in rows[0].items():
#     print(f"{k:28s} {v}")