from psycopg2.extras import Json
# import json
import numpy as np
from GreasyPidgin.Envelope import Envelope
from Tudo.Tudo import Tudo


t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/PSQL/")
t.connect()
t.getAllColumnsAndTables()

r = t.executeAndReturn("""
    SELECT roughness
    FROM soundfile_analysis
    WHERE identifiers::jsonb @> %s::jsonb
""", (Json(["viola", "behind_the_bridge"]),))
# r = t.executeAndReturn("""
#     SELECT roughness
#     FROM soundfile_analysis
#     WHERE identifiers::jsonb @> ["viola", "behind_the_bridge"]::jsonb;
# """)

flattened = [i[0] for i in r]
print(np.mean(flattened))
print(np.median(flattened))

e = Envelope(flattened)
e.display()

t.killAllServerInstances()