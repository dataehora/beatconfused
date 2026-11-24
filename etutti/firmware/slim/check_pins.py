"""Checks the sketch's pins against etutti/hardware/slim/pcb/PINOS.md (the contract with the electronics).

    python etutti/firmware/slim/check_pins.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ino = open(os.path.join(HERE, "slim.ino"), encoding="utf-8").read()
pinos = open(os.path.join(HERE, "..", "..", "hardware", "slim", "pcb", "PINOS.md"), encoding="utf-8").read()
table = {m.group(2): int(m.group(1)) for m in re.finditer(r"^\| (\d+) \| (\w+) \|", pinos, re.M)}
want = {"PIN_CHG_STAT": "CHG_STAT", "PIN_PGOOD_N": "PGOOD_N", "PIN_SCAN_DATA": "SCAN_DATA_P", "PIN_SCAN_CLK": "SCAN_CLK_P",
        "PIN_SCAN_LATCH": "SCAN_LATCH_P", "PIN_LED_G": "LED_G", "PIN_KEEP": "KEEP", "PIN_LED_R": "LED_R", "PIN_VBAT_S": "VBAT_S",
        "PIN_VOL_W": "VOL_W", "PIN_REG_ADC": "REG_ADC", "PIN_SW_S": "SW_S"}
bad = 0
for d, net in want.items():
    m = re.search(r"#define %s\s+(\d+)" % d, ino)
    ok = m and table.get(net) == int(m.group(1))
    print("%-16s %-14s sketch %-4s PINOS %-4s %s" % (d, net, m.group(1) if m else "-", table.get(net), "ok" if ok else "ERRO"))
    bad += not ok
m = re.search(r"PIN_OUT\[4\]\s*=\s*\{([^}]*)\}", ino)
outs = [int(x) for x in m.group(1).split(",")]
for i, p in enumerate(outs):
    ok = table.get("OUT_R%d" % (i + 1)) == p
    print("OUT_R%d          sketch %-4d PINOS %-4s %s" % (i + 1, p, table.get("OUT_R%d" % (i + 1)), "ok" if ok else "ERRO"))
    bad += not ok
print("pins: %d checked, %d wrong" % (len(want) + 4, bad))
sys.exit(1 if bad else 0)
