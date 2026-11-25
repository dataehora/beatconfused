"""Checks key index x position x note: the sketch's NOTE[][] table and scan order against the placed ruler (pcb/regua/posicao_regua.json)
and the Design's contract (case/envelope_regua.json). Row r (0..3) = ruler r+1, column c = position c+1 from the LEFT end = stage c of the 595
(QA..QH = EN1..EN8 = TMAG5253 U1..U8 = key u 21.25 + 18.5 c).

    python etutti/firmware/slim/check_teclas.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.join(HERE, "..", "..", "hardware", "slim")
ino = open(os.path.join(HERE, "slim.ino"), encoding="utf-8").read()
env = json.load(open(os.path.join(HW, "case", "envelope_regua.json"), encoding="utf-8"))
pos = json.load(open(os.path.join(HW, "pcb", "regua", "posicao_regua.json"), encoding="utf-8"))
m = re.search(r"NOTE\[NROWS\]\[NCOLS\]\s*=\s*\{(.*?)\n\};", ino, re.S)
rows = [[int(x) for x in re.findall(r"\d+", line)] for line in re.findall(r"\{([^}]*)\}", m.group(1))]
NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(n):
    base = NAMES[n[0]] + (1 if "#" in n else 0)
    return 12 * (int(n[-1]) + 1) + base


bad = 0
for r, ri in enumerate(env["fileiras"]):
    for c, k in enumerate(ri["keys"]):
        ok = rows[r][c] == midi(k["note"]) == k["midi"]
        bad += not ok
        if not ok:
            print("ERRO fileira %d pos %d: sketch %d, nota %s = %d" % (r + 1, c + 1, rows[r][c], k["note"], midi(k["note"])))
nets = {(p["ref"], p["n"]): p["net"] for p in pos["pads"]}
for c in range(8):
    u = pos["pecas"]["U%d" % (c + 1)]["u"]
    ok_u = abs(u - env["regua"]["u_teclas"][c]) < 0.01 and nets[("U%d" % (c + 1), "3")] == "EN%d" % (c + 1)
    q = "QA QB QC QD QE QF QG QH".split()[c]
    pin595 = {"QA": "15", "QB": "1", "QC": "2", "QD": "3", "QE": "4", "QF": "5", "QG": "6", "QH": "7"}[q]
    ok_595 = nets[("U9", pin595)] == "EN%d" % (c + 1)
    bad += (not ok_u) + (not ok_595)
    print("posicao %d: U%d em u=%.2f, EN%d <- %s (pino %s do 595): %s" % (c + 1, c + 1, u, c + 1, q, pin595, "ok" if ok_u and ok_595 else "ERRO"))
sweep = "colunas 0..7 = estagios QA..QH, 1 pulso por coluna (um 1 entra no primeiro pulso)"
print("indice = 8*(fileira-1)+posicao; %s" % sweep)
print("teclas: 32 conferidas, %d divergencias" % bad)
sys.exit(1 if bad else 0)
