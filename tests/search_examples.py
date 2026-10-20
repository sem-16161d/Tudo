# Tudo — conditional search examples
from Tudo.Tudo import Tudo

t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/DB")
t.connect()

# print(t.searchColumns())          # what you can filter on

# long, noisy-ish bassoon multiphonics, darkest first
rows = t.search(
    tags=["bassoon", "multiphonic"],
    noTags=["noise"],
    durationSec__gt=2,
    flatnessMedian__gt=0.0001,
    orderBy="centroidMostCommon",
    limit=30,
)
for r in rows:
    print(r["path"], r["roughness"], r["flatnessmedian"])

# how many have a clear pitch fluctuation between 4 and 8 Hz?
print(t.count(pitchFluctStrength__gt=0, pitchFluctRate__between=(4, 8)))

# 10 random low sounds, copied to a folder for auditioning
paths = t.searchPaths(mainPitchHz__lt=110, random=True, limit=10)
# t.copyResults(paths, "/private/tmp/mph")
