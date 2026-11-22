"""eTutti Student V4 (R4V4): schematic of the universal 4-key sensor ruler, ERC, netlist check, BOM.

    python etutti/hardware/student_v04/pcb/regua/schematic_regua.py

Plain CPython; calls kicad-cli for ERC and the netlist. Reuses the main board's schematic writer (pcb/schematic.py) by
module globals (same symbols, same uuid namespace, nothing of the main board is written).

The ruler (R2V4 E5, R3V4 contract, R4V4): 4 x TMAG5253BA3 (one per key), one 74HC595D that switches their EN lines
(QA..QD), decoupling, two JST SH 6-way connectors (IN and OUT, both on the bottom). All parts on the bottom (JLCPCB
bottom assembly); nothing on the top, where the key sits.

  J1 IN  : R8V4 P6s: 1 +3V3, 2 GND, 3 OUT, 4 GND, 5 CLK, 6 DATA (= SER, 595 pin 14); J2 OUT: same, pin 6 = QH' through 330 ohm
  (LK1/LK2 solder pads of the R5V4 are gone: link H = stock cable, no solder)
  595    : VCC +3V3, GND, ~OE GND, ~SRCLR +3V3, SRCLK + RCLK = CLK, QA..QD -> EN of the sensors 1..4 (QE..QH unused)

Writes under etutti/hardware/student_v04/: kicad/regua/student_v04_regua.kicad_sch (+ sheet, library, tables),
pcb/regua/build/{partes_regua.json, regua_erc.json, regua_netlist.net}, bom_regua.csv.
Exits non-zero on an ERC error/warning or a netlist mismatch.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, PCB)
import schematic as M  # noqa: E402  (importing it defines the main board's parts; they are dropped below)

HW = os.path.normpath(os.path.join(PCB, ".."))
NPOS = int(os.environ.get("REGUA_N", "4"))            # R10V4: 4 = R4 (default, unchanged), 8 = R8
assert NPOS in (4, 8)
SUF = "" if NPOS == 4 else "8"
KD = os.path.join(HW, "kicad", "regua")
BUILD = os.path.join(HERE, "build" + SUF)
os.makedirs(KD, exist_ok=True)
os.makedirs(BUILD, exist_ok=True)

M.PARTS = {"R": []}
M.SHEETS = [("R", "Regua")]
M.CUR = ["R"]
M.PROJECT = "student_v04_regua" + SUF
M.KDIR = KD
M.BUILD = BUILD
M.REV = "Student V4 R8V4 regua" if NPOS == 4 else "Student V4 R10V4 regua R8"
M.NOTES = {"R": [
    ("R · Regua universal de 4 teclas (74 x 14 x 1,2 mm): 4 TMAG5253BA3 + 74HC595 + 2 conectores SH de 6 vias (J1 entrada em u 5,9, J2 saida em u 47,5), tudo no fundo. R8V4: ligacao H (cabo de estoque, sem solda)." if NPOS == 4 else
     "R · Regua R8 de 8 teclas (148 x 14 x 1,2 mm): 8 TMAG5253BA3 + um 74HC595 com os 8 estagios usados + 2 conectores SH de 6 vias (J1 entrada em u 5,9, J2 saida em u 121,5 = 26,5 mm da ponta direita nominal, como na R4), tudo no fundo. R10V4."),
    "Pinagem P6s (J1, J2 e J601-J604 da principal): 1 +3V3, 2 GND, 3 OUT, 4 GND, 5 CLK, 6 DADO (J1: SER; J2: QH' por 330 ohm).",
    "O 595 liga o EN de cada sensor (QA..QD); SRCLK e RCLK juntos (a saida travada atrasa 1 pulso); OE em GND, SRCLR em +3V3.",
]}
M.ROOT_UUID = M.uid("root-regua")
M.SHEET_UUID = {"R": M.uid("sheet", "regua", "R")}
M.sym("PWR_FLAG", "power")

SH_FP = "Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal"
TMAG_FP = "Package_SON:Texas_X2SON-4-1EP_1.1x1.4mm_P0.5mm_EP0.8x0.6mm"
DFN_FP = "Package_DFN_QFN:DHVQFN-16-1EP_2.5x3.5mm_P0.5mm_EP1x2mm"

# ------------------------------------------------------------------ parts
QPIN = {1: "15", 2: "1", 3: "2", 4: "3", 5: "4", 6: "5", 7: "6", 8: "7"}     # 74HC595 QA..QH
for k in range(1, NPOS + 1):
    M.part("U%d" % k, "TMAG5253BA3", "TMAG5253BA3IQDMRR",
           {"1": "+3V3", "2": "GND", "3": "EN%d" % k, "4": "OUT", "5": "GND"}, "S%d" % k, fp=TMAG_FP, lcsc="C22401868",
           cls="estendida", price=0.60, status="final",
           note="tecla %d da regua: no verso, no centro da celula (u = %.2f mm); OUT em comum com os %d outros; EN = %s do 595 (saida em Hi-Z com EN baixo)"
                % (k, 9.25 + 18.5 * (k - 1), NPOS - 1, "QA..QD" if NPOS == 4 else "QA..QH"),
           datasheet="https://www.ti.com/lit/ds/symlink/tmag5253.pdf")
def sym595():
    left = [("14", "SER", "input"), ("11", "SRCLK", "input"), ("12", "RCLK", "input"), ("13", "~{OE}", "input"),
            ("10", "~{SRCLR}", "input"), ("16", "VCC", "power_in"), ("8", "GND", "power_in"), ("17", "EP", "power_in")]
    right = [("15", "QA", "output"), ("1", "QB", "output"), ("2", "QC", "output"), ("3", "QD", "output"),
             ("4", "QE", "output"), ("5", "QF", "output"), ("6", "QG", "output"), ("7", "QH", "output"),
             ("9", "QH'", "output")]
    return M.box_symbol("74HC595BQ", "U", [(left, right)], "8-bit shift register with output latch, DHVQFN-16 (SOT763-1), 17 = exposed pad = GND")


M.sym("74HC595BQ", "custom", sym595)
REF595, REFC5, REFC6 = "U%d" % (NPOS + 1), "C%d" % (NPOS + 1), "C%d" % (NPOS + 2)
n595 = {"8": "GND", "9": "QHP", "10": "+3V3", "11": "CLK", "12": "CLK", "13": "GND", "14": "SER", "16": "+3V3", "17": "GND"}
for st in range(1, 9):
    n595[QPIN[st]] = ("EN%d" % st) if st <= NPOS else "NC"
M.part(REF595, "74HC595BQ", "74HC595BQ,115", n595,
    "S%d" % (NPOS + 1), fp=DFN_FP, lcsc="C730243", cls="estendida", price=0.176, status="conferir",
    note="registrador de deslocamento 8 bits em DHVQFN-16 (2,5 x 3,5 mm): o SOIC-16 (C5947, Basic) tem 6,9 mm de pads e nao cabe numa "
         "regua de 14 mm com pinos a 10,16 mm; QA..QD ligam o EN dos sensores 1..4, QE..QH sem uso; QH' = cascata; pad 17 no GND",
    datasheet="https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf")
# R8V4 (ligacao H, SPEC R8V4): J1 = entrada e J2 = saida, os dois SM06B-SRSS-TB (clone C56123098) no fundo, boca para tras;
# cabo de estoque JST A06SR06SR30K51B (reto, pino k -> pino k). Pinagem P6s: 1 +3V3, 2 GND, 3 OUT, 4 GND, 5 CLK, 6 DADO.
# Os pads de solda LK1/LK2 da R5V4 (elo soldado, opcao D) saem: na H nao ha solda.
M.part("J1", "Conn_01x06_MountingPin", "XY-SM06B-SRSS-TB",
       {"1": "+3V3", "2": "GND", "3": "OUT", "4": "GND", "5": "CLK", "6": "SER", "MP": "GND"}, "S%d" % (NPOS + 2), fp=SH_FP,
       lcsc="C56123098", cls="estendida", price=0.069, status="conferir",
       note="entrada (P6s: 1 +3V3, 2 GND, 3 OUT, 4 GND, 5 CLK, 6 DADO = SER do 595); cabo JST A06SR06SR30K51B vindo da placa principal ou do OUT da regua anterior; "
            "no fundo, faixa de tras, boca para tras; u = 5,9",
       datasheet="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf")
M.part("J2", "Conn_01x06_MountingPin", "XY-SM06B-SRSS-TB",
       {"1": "+3V3", "2": "GND", "3": "OUT", "4": "GND", "5": "CLK", "6": "QHP_J", "MP": "GND"}, "S%d" % (NPOS + 3), fp=SH_FP,
       lcsc="C56123098", cls="estendida", price=0.069, status="conferir",
       note="saida (P6s, igual ao J1; o pino 6 = QH' do 595 por 330 ohm) para a regua seguinte da fileira; no fundo, faixa de tras, boca para tras; "
            "R8V4: u = 47,5 (era 68,1) para o cabo de 45,8-50,8 mm fechar",
       datasheet="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf")
M.R("R1", "330", "QHP", "QHP_J", "S%d" % (NPOS + 3), note="R8V4: 330 ohm (era 100) em serie no QH' (cascata para a proxima regua; limita a 10 mA o pior caso de cabo errado)")
for k in range(1, NPOS + 1):
    M.C("C%d" % k, "100nF", "+3V3", "GND", "S%d" % k, note="desacoplamento do TMAG5253 %d, junto do pino 1" % k)
M.C(REFC5, "100nF", "+3V3", "GND", "S%d" % (NPOS + 1), note="desacoplamento do 595")
M.C(REFC6, "10uF", "+3V3", "GND", "S%d" % (NPOS + 1), "0805", note="reservatorio da regua (junto do conector de entrada)")


def main():
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
    M.write_root(flags, root_notes=[
        "eTutti Student V4 · regua universal de 4 teclas, R4V4. Nada de roteamento aqui: so esquema (Fase B).",
        "Placa: pcb/regua/posiciona_regua.py (posicionamento sem trilhas). Painel: pcb/regua/painel_regua.py.",
        "PWR_FLAG: redes alimentadas por conector (o ERC nao ve a fonte)."])
    M.write_library()
    parts = []
    for p in M.PARTS["R"]:
        q = {k: p[k] for k in ("ref", "value", "nets", "code", "fp", "lcsc", "cls", "mount", "note", "dnp", "sheet", "price", "datasheet")}
        q["path"] = "/%s/%s/%s" % (M.ROOT_UUID, M.SHEET_UUID["R"], M.uid("sym", p["ref"], 1))
        parts.append(q)
    json.dump(parts, open(os.path.join(BUILD, "partes_regua.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    # the board script reads the netlist kicad-cli writes here
    counts, bad = M.run_checks(declared)
    os.replace(os.path.join(BUILD, M.PROJECT + "_erc.json"), os.path.join(BUILD, "regua_erc.json"))
    os.replace(os.path.join(BUILD, M.PROJECT + "_netlist.net"), os.path.join(BUILD, "regua_netlist.net"))
    # BOM
    rows = {}
    for p in parts:
        r = rows.setdefault(p["lcsc"], dict(p, refs=[]))
        r["refs"].append(p["ref"])
    with open(os.path.join(HW, "bom_regua%s.csv" % SUF), "w", newline="", encoding="utf-8") as f:
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
