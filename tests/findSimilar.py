from Tudo.Tudo import Tudo
from Tudo.Sound import Sound
from GreasyPidgin.Pitch import spntof, mtof
from datetime import datetime


ts = datetime.now().strftime("%Y%m%d_%H%M%S")   # 20261120_120800

FOLDER = "/Users/sraw/Documents/PROJEKTE/2026/DER_SCHNEEKÖNIG/SOUNDS/VIV_SOMMER"



t = Tudo("/Users/sraw/Documents/SAMPLES/TUDO/DB")
t.connect()
OUT_PATH =  "/private/tmp/similar.wav"
# OUT_PATH = f"{FOLDER}/{ts}_concatenate.wav"
res = t.findSimilar(
    target = {'roughness': 0, 'mainpitchhz': mtof(31-12, 443), 'durationsec': 1}, 
    k = 20, 
    tagContains = ['string'])
t.renderMix(res, OUT_PATH,align="singleFiles" )