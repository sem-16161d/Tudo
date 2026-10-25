# =============================================================================
# tudoServer.py — Tudo as an OSC server for Max / Max for Live / SuperCollider
#
# Start it in a terminal next to Live:   python tests/tudoServer.py
# Stop with Ctrl+C.
#
# Max:  [udpsend localhost 7400]  ->  Tudo  ->  [udpreceive 7401]
# Messages and replies: see src/Tudo/TudoOSC.py (and max/TudoOSC_example.maxpat)
# =============================================================================
from Tudo.Tudo import Tudo
from Tudo.TudoOSC import TudoOSC

DB_PATH = "/Users/sraw/Documents/SAMPLES/TUDO/DB"
IN_PORT = 7400      # Tudo listens here   (Max: udpsend localhost 7400)
OUT_PORT = 7401     # Tudo answers here   (Max: udpreceive 7401)

t = Tudo(DB_PATH)
t.connect()          # uses the running Postgres server, doesn't restart it

server = TudoOSC(t, inPort=IN_PORT, outPort=OUT_PORT)
server.start()       # blocking until Ctrl+C
