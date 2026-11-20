import shutil
import os

from Tudo.Tudo import Tudo
from Tudo.Sound import Sound

t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/DB")

t.connect()


res = t.search(
    tags=["bassoon", "multiphonic"],     # must have all of these
    anyTags=["buzz", "rumbling"],        # at least one
    noTags=["noise"],                    # none of these
    durationSec__gt=2,
    flatnessMedian__between=(0.1, 0.5),
    transposability__in=[0, 1],
    pitchFluctRate__isnull=False,
    pathContains="BASSOON",
    orderBy="-centroidMostCommon",       # "-" = descending
    limit=20,                            # also: offset, random=True, columns=[...]
)

print(res)