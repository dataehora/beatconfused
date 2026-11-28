"""eTutti Slim (R1SL): schematic of the R8 ruler (8 keys), ERC, netlist check, BOM.

    python etutti/hardware/slim/pcb/regua/schematic_regua.py

Plain CPython; calls kicad-cli for ERC and the netlist. Reuses the Slim main board's schematic writer (pcb/schematic.py)
through module globals (same symbols, nothing of the main board is written).

The ruler (SPEC 5.1): 8 x TMAG5253BA3 on the bottom face (one per key, 4.3 mm from the key centre), outputs tied together
(OUT), each EN driven by one stage of a 74HC595 in the 14 mm tail, decoupling, one FFC 8-way 0.5 mm connector (bottom contact):
1 GND, 2 +3V3, 3 OUT, 4 DATA, 5 CLOCK, 6 LATCH, 7 GND, 8 GND. 595: SER = DATA, SRCLK = CLOCK, RCLK = LATCH, ~OE = GND,
~SRCLR = +3V3, QA..QH = EN1..EN8 (QH' unused). One ruler per row, no cascade.

Writes under etutti/hardware/slim/pcb/: kicad_regua/ (+ sheet, library), regua/build/{partes_regua.json, regua_erc.json,
regua_netlist.net}, bom_regua.csv. Exits non-zero on an ERC error/warning or a netlist mismatch.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, PCB)
import schematic as M  # noqa: E402  (importing it defines the main board's parts; they are dropped below)

KD = os.path.join(PCB, "kicad_regua")
BUILD = os.path.join(HERE, "build")
os.makedirs(KD, exist_ok=True)
os.makedirs(BUILD, exist_ok=True)

M.PARTS = {"R": []}
M.SHEETS = [("R", "Regua")]
M.CUR = ["R"]
M.PROJECT = "slim_regua"
M.KDIR = KD
M.BUILD = BUILD
M.REV = "Slim R1SL regua R8"
M.NOTES = {"R": [
    "R · Regua R8 (8 teclas, ~15 x 160 mm, 2 camadas, 1,2 mm): 8 TMAG5253BA3 + 74HC595 (DHVQFN-16) + conector FFC de 8 vias, tudo no fundo.",
    "FFC: 1 GND, 2 +3V3, 3 OUT, 4 DADO, 5 CLOCK, 6 LATCH, 7 GND, 8 GND. O 595 liga o EN de cada sensor (QA..QH); OE em GND, SRCLR em +3V3.",
]}
M.ROOT_UUID = M.uid("root-regua")
M.SHEET_UUID = {"R": M.uid("sheet", "regua", "R")}
M.sym("PWR_FLAG", "power")


def tmag_tristate():
    """The TMAG5253 output is high-impedance while EN is low (several share one line): tri_state, not output."""
    return M.box_symbol("TMAG5253BA3", "U", [([("1", "VCC", "power_in"), ("3", "EN", "input")],
                                              [("4", "OUT", "tri_state"), ("2", "GND", "power_in"), ("5", "EP", "passive")])],
                        "TI TMAG5253 linear Hall sensor with enable, X2SON-4 (OUT high-impedance with EN low)")


M.sym("TMAG5253BA3", "custom", tmag_tristate)

FFC_FP = "slim:FFC_8P_0.5_KH-H1.0"
TMAG_FP = "slim:TMAG5253_X2SON4_EE"
DFN_FP = "slim:HC595_DHVQFN16_EE"
NPOS = 8

QPIN = {1: "15", 2: "1", 3: "2", 4: "3", 5: "4", 6: "5", 7: "6", 8: "7"}     # 74HC595 QA..QH
for k in range(1, NPOS + 1):
    M.part("U%d" % k, "TMAG5253BA3", "TMAG5253BA3IQDMRR",
           {"1": "+3V3", "2": "GND", "3": "EN%d" % k, "4": "OUT", "5": "GND"}, "S%d" % k, fp=TMAG_FP, lcsc="C22401868",
           cls="estendida", price=0.60, status="final",
           note="tecla %d: no verso, a 4,3 mm do centro (desenho Gateron 'Layout of PCB'); OUT em comum com os 7 outros; EN = Q%s do 595"
                % (k, "ABCDEFGH"[k - 1]),
           datasheet="https://www.ti.com/lit/ds/symlink/tmag5253.pdf")


def sym595():
    left = [("14", "SER", "input"), ("11", "SRCLK", "input"), ("12", "RCLK", "input"), ("13", "~{OE}", "input"),
            ("10", "~{SRCLR}", "input"), ("16", "VCC", "power_in"), ("8", "GND", "power_in"), ("17", "EP", "power_in")]
    right = [("15", "QA", "output"), ("1", "QB", "output"), ("2", "QC", "output"), ("3", "QD", "output"),
             ("4", "QE", "output"), ("5", "QF", "output"), ("6", "QG", "output"), ("7", "QH", "output"),
             ("9", "QH'", "output")]
    return M.box_symbol("74HC595BQ", "U", [(left, right)], "8-bit shift register with output latch, DHVQFN-16, 17 = exposed pad = GND")


M.sym("74HC595BQ", "custom", sym595)
n595 = {"8": "GND", "9": "NC", "10": "+3V3", "11": "CLK", "12": "LATCH", "13": "GND", "14": "DATA", "16": "+3V3", "17": "GND"}
for st in range(1, 9):
    n595[QPIN[st]] = "EN%d" % st
M.part("U9", "74HC595BQ", "74HC595BQ,115", n595, "S9", fp=DFN_FP, lcsc="C730243", cls="estendida", price=0.176, status="conferir",
       note="registrador de deslocamento 8 bits (DHVQFN-16, 2,5 x 3,5 mm), 137 mil em estoque; QA..QH = EN dos sensores 1..8, QH' sem uso; pad 17 no GND",
       datasheet="https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf")
M.sym("Conn_01x08_MountingPin", "Connector_Generic_MountingPin")
M.part("J1", "Conn_01x08_MountingPin", "FFC 8P 0.5 mm H1.0 (KH-FPC0.5-H1.0SMT-8P-QCHF)",
       {"1": "GND", "2": "+3V3", "3": "OUT", "4": "DATA", "5": "CLK", "6": "LATCH", "7": "GND", "8": "GND", "MP": "GND"}, "S10",
       fp=FFC_FP, lcsc="C3250113", cls="estendida", price=0.10, status="conferir",
       note="na cauda, face de baixo, fora da area das teclas; cabo FFC reto ate a principal (mesmo conector, 1,0 mm de altura, contatos dos dois lados); footprint = placeholder Amphenol")
for k in range(1, NPOS + 1):
    M.C("C%d" % k, "100nF", "+3V3", "GND", "S%d" % k, note="desacoplamento do TMAG5253 %d, junto do pino 1" % k)
M.C("C9", "100nF", "+3V3", "GND", "S9", note="desacoplamento do 595")
M.C("C10", "10uF", "+3V3", "GND", "S10", "0805", note="reservatorio da regua (junto do conector)")


def main():
    import shutil
    M.footprints.write_all()
    shutil.copytree(os.path.join(PCB, "kicad", "slim.pretty"), os.path.join(KD, "slim.pretty"), dirs_exist_ok=True)
    M.check_footprints()
    declared, pages = {}, {}
    for s, title in M.SHEETS:
        nets, paper = M.write_sheet(s, title, M.PARTS[s])
        pages[s] = paper
        for k, v in nets.items():
            declared.setdefault(k, []).extend(v)
    for net, nodes in declared.items():
        if len(nodes) < 2:
            raise SystemExit("net %s has a single pin: %s" % (net, nodes))
    flags = sorted(n for n, nodes in declared.items()
                   if any(t == "power_in" for _, _, t in nodes) and not any(t == "power_out" for _, _, t in nodes))
    M.write_root(flags)
    M.write_library()
    parts = []
    for p in M.PARTS["R"]:
        q = {k: p[k] for k in ("ref", "value", "nets", "code", "fp", "lcsc", "cls", "mount", "note", "dnp", "sheet", "price", "datasheet")}
        q["path"] = "/%s/%s/%s" % (M.ROOT_UUID, M.SHEET_UUID["R"], M.uid("sym", p["ref"], 1))
        parts.append(q)
    json.dump(parts, open(os.path.join(BUILD, "partes_regua.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    counts, bad = M.run_checks(declared)
    os.replace(os.path.join(BUILD, "slim_erc.json"), os.path.join(BUILD, "regua_erc.json"))
    os.replace(os.path.join(BUILD, "slim_netlist.net"), os.path.join(BUILD, "regua_netlist.net"))
    rows = {}
    for p in parts:
        r = rows.setdefault(p["lcsc"], dict(p, refs=[]))
        r["refs"].append(p["ref"])
    with open(os.path.join(PCB, "bom_regua.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["lcsc", "valor", "classe_jlc", "qtd", "referencias", "preco_unit_usd_est"])
        for lc, r in sorted(rows.items(), key=lambda kv: kv[1]["refs"][0]):
            w.writerow([lc, r["value"], "Extended" if r["cls"] == "estendida" else "Basic", len(r["refs"]),
                        " ".join(r["refs"]), "%.3f" % (r["price"] or 0)])
    print("parts %d, nets %d, PWR_FLAG on %s" % (len(parts), len(declared), ", ".join(flags)))
    for sev in ("error", "warning", "exclusion"):
        items = counts.get(sev, [])
        print("ERC %s: %d" % (sev, len(items)))
        for it in items[:25]:
            print("   ", it)
    print("netlist vs declared: %s" % ("OK" if not bad else bad[:10]))
    sys.exit(1 if counts.get("error") or counts.get("warning") or bad else 0)


if __name__ == "__main__":
    main()
