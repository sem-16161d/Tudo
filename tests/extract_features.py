import numpy as np
from GreasyPidgin.Envelope import Envelope
from Tudo.Tudo import Tudo


t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/PSQL/")
t.connect()
t.getAllColumnsAndTables()

r = t.executeAndReturn("""
    SELECT roughness
    FROM soundfile_analysis
    WHERE identifiers::jsonb @> '["viola", "tremolo_sul_ponticello"]'::jsonb;
""")
flattened = [i[0] for i in r]
print(np.mean(flattened))
print(np.median(flattened))

e = Envelope(flattened)
e.display()

t.killAllServerInstances()