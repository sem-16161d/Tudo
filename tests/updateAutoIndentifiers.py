
from Tudo.Tudo import Tudo

# ----------------------------------------------------------------------------
# settings
# ----------------------------------------------------------------------------
DB_PATH = "/Users/sraw/Documents/SAMPLES/TUDO/DB"

t = Tudo(DB_PATH)
t.connect()
t.updateAutoIdentifiers() 