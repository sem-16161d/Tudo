# =============================================================================
# TUDO — cheatsheet
# Tudo is a PostgreSQL-backed sample library.
# =============================================================================
import shutil
import os

from Tudo.Tudo import Tudo
from Tudo.Sound import Sound

t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/DB")
# t.newDatabase('tudo')
# t.initializeNewDatabase()
t.connect()
# t.setupTables()

# # whole folder
# t.newEntriesFromFolder(
#     "/Users/sraw/Documents/SAMPLES/TUDO/SAMPLES/ACOUSTIC_INSTRUMENTS/WOODWIND/BASSOON/MULTIPHONIC",
#     identifiers=[
#         "bassoon", "multiphonic","conTimbre", 'music instrument','instrument',
#         'double reed',"reed", 'wood','air' , 'standard atmosphere',
#         'buzz','pulse', 'dark', 'noise','rumbling',"pressure","vibration","murky","muddy","split" ,
#         "interference" ,"beating", "partial" ,"overtone", "undertone" ],
#     transposability=0
# )


## 1st MPH call
# rows = t.executeAndReturn("""
#     SELECT path
#     FROM soundfile_analysis
#     WHERE pitchFluctStrength > 0
#       AND durationsec > 2
#       AND spectFluctMean > 0.1
#     ORDER BY centroidmostcommon DESC
# """)

rows = t.executeAndReturn("""
    SELECT path, spectralDensity, roughness, flatnessMedian
    FROM soundfile_analysis
    WHERE flatnessMedian  > 0.00001
    ORDER BY centroidmostcommon ASC
""")

print(len(rows))

if os.path.exists("/private/tmp/mph"):
    shutil.rmtree("/private/tmp/mph")
os.makedirs("/private/tmp/mph")

for r in rows:
    shutil.copy(r[0], "/private/tmp/mph")

print(f"copied {len(rows)} files to /private/tmp/mph")
'''
second lookup
usage permitted only with a contimbre.com license bassoon.m47.v5686-2.Slb32824
usage permitted only with a contimbre.com license bassoon.m47.v5687-2.Slb32829
usage permitted only with a contimbre.com license bassoon.m47.v4920-2.Slb28994
usage permitted only with a contimbre.com license bassoon.m47.v2212-2.Slb15454

very subtle
usage permitted only with a contimbre.com license bassoon.m47.v1622-2.Slb12504
'''
'''
Interesting MPHS
Results:
usage permitted only with a contimbre.com license bassoon.m47.v524-1.Slb7013
usage permitted only with a contimbre.com license bassoon.m47.v627-1.Slb7528
usage permitted only with a contimbre.com license bassoon.m47.v829-1.Slb8538
usage permitted only with a contimbre.com license bassoon.m47.v1328-1.Slb11033
usage permitted only with a contimbre.com license bassoon.m47.v1380-2.Slb11294
usage permitted only with a contimbre.com license bassoon.m47.v1382-1.Slb11303
usage permitted only with a contimbre.com license bassoon.m47.v1459-1.Slb11688
usage permitted only with a contimbre.com license bassoon.m47.v1657-1.Slb12678
usage permitted only with a contimbre.com license bassoon.m47.v1955-2.Slb14169
usage permitted only with a contimbre.com license bassoon.m47.v1960-2.Slb14194
usage permitted only with a contimbre.com license bassoon.m47.v1962-2.Slb14204
usage permitted only with a contimbre.com license bassoon.m47.v2028-1.Slb14533
usage permitted only with a contimbre.com license bassoon.m47.v2080-2.Slb14794
usage permitted only with a contimbre.com license bassoon.m47.v3143-1.Slb20108
usage permitted only with a contimbre.com license bassoon.m47.v3210-1.Slb20443
usage permitted only with a contimbre.com license bassoon.m47.v3214-1.Slb20463
usage permitted only with a contimbre.com license bassoon.m47.v3216-2.Slb20474
usage permitted only with a contimbre.com license bassoon.m47.v2526-1.Slb17023
usage permitted only with a contimbre.com license bassoon.m47.v2893-1.Slb18858
usage permitted only with a contimbre.com license bassoon.m47.v4837-2.Slb28579
usage permitted only with a contimbre.com license bassoon.m47.v5487-1.Slb31828
usage permitted only with a contimbre.com license bassoon.m47.v1636-1.Slb12573
usage permitted only with a contimbre.com license bassoon.m47.v1656-2.Slb12674
usage permitted only with a contimbre.com license bassoon.m47.v1954-2.Slb14164
usage permitted only with a contimbre.com license bassoon.m47.v1948-1.Slb14133
usage permitted only with a contimbre.com license bassoon.m47.v4843-1.Slb28608
usage permitted only with a contimbre.com license bassoon.m47.v2979-1.Slb19288
usage permitted only with a contimbre.com license bassoon.m47.v1382-2.Slb11304
usage permitted only with a contimbre.com license bassoon.m47.v1965-1.Slb14218
usage permitted only with a contimbre.com license bassoon.m47.v1954-1.Slb14163


dafuq
usage permitted only with a contimbre.com license bassoon.m47.v5000-1.Slb29393
usage permitted only with a contimbre.com license bassoon.m47.v5377-3.Slb31280
'''