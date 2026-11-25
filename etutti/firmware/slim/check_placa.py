"""Checks PINOS.md against the PLACED main board (R4SL, stage 2b): every pin's ball carries the net PINOS.md says, and the distance to its far end.

    python etutti/firmware/slim/check_placa.py

Reads pcb/PINOS.md (the contract) and pcb/principal/posicao_principal.json (positions and nets of every pad, from the placed KiCad board).
Distances are straight (Manhattan) estimates between the ball and the nearest pad of ANOTHER part on the same net: the routing stage measures the real lengths.
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, "..", "..", "hardware", "slim"))
pinos = open(os.path.join(HW, "pcb", "PINOS.md"), encoding="utf-8").read()
rows = [(int(m.group(1)), m.group(2), m.group(3), m.group(4)) for m in re.finditer(r"^\| (\d+) \| (\w+) \| (\w+) \| (\w+) \|", pinos, re.M)]
pos = json.load(open(os.path.join(HW, "pcb", "principal", "posicao_principal.json"), encoding="utf-8"))
pads = pos["pads"]
norm = lambda n: n.lstrip("/")
bga = {p["n"]: p for p in pads if p["ref"] == "U101"}
bad = 0
far = []
for pin, net, pad, ball in rows:
    p = bga.get(ball)
    ok = p is not None and norm(p["net"]) == net
    others = [q for q in pads if q["ref"] != "U101" and norm(q["net"]) == net and not q["ref"].startswith("H")]
    d = min((abs(q["x"] - p["x"]) + abs(q["y"] - p["y"]) for q in others), default=None) if p else None
    print("pino %2d %-13s bola %-3s rede na placa %-13s %s  distancia ao outro lado %s" % (pin, net, ball, norm(p["net"]) if p else "-", "ok" if ok else "ERRO", "%.1f mm" % d if d is not None else "-"))
    bad += not ok
    if d:
        far.append((d, net))
far.sort(reverse=True)
print("pinos: %d conferidos, %d errados; mais longos: %s" % (len(rows), bad, ", ".join("%s %.0f mm" % (n, d) for d, n in far[:4])))


def p_of(ref, n):
    return next(p for p in pads if p["ref"] == ref and p["n"] == n)


# USB pair: USB-C -> ESD (U201) -> RT1062 (balls of USB_DP / USB_DN)
tot = []
for net, usb_pad in (("USB_DP", "A6"), ("USB_DN", "A7")):
    a = p_of("J201", usb_pad)
    esd = [q for q in pads if q["ref"] == "U201" and norm(q["net"]) == net]
    ball = [q for q in pads if q["ref"] == "U101" and norm(q["net"]) == net]
    if esd and ball:
        e = esd[0]
        l = abs(a["x"] - e["x"]) + abs(a["y"] - e["y"]) + abs(e["x"] - ball[0]["x"]) + abs(e["y"] - ball[0]["y"])
        tot.append(l)
        print("par USB %s: J201 -> U201 -> bola %s: %.1f mm (Manhattan)" % (net, ball[0]["n"], l))
sys.exit(1 if bad else 0)
