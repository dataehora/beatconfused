"""eTutti Student V4 (R4V4): schematic of the universal 4-key sensor ruler, ERC, netlist check, BOM.

    python etutti/hardware/student_v04/pcb/regua/schematic_regua.py

Plain CPython; calls kicad-cli for ERC and the netlist. Reuses the main board's schematic writer (pcb/schematic.py) by
module globals (same symbols, same uuid namespace, nothing of the main board is written).

The ruler (R2V4 E5, R3V4 contract, R4V4): 4 x TMAG5253BA3 (one per key), one 74HC595D that switches their EN lines
(QA..QD), decoupling, two JST SH 6-way connectors (IN and OUT, both on the bottom). All parts on the bottom (JLCPCB
bottom assembly); nothing on the top, where the key sits.

  J1 IN  : 1 +3V3, 2 GND, 3 OUT, 4 CLK, 5 SER (to 595 pin 14), 6 reserved (NC); cable of the first ruler of a row
  LK1/LK2 (R5V4): 5 solder pads each end for the in-row link (+3V3, GND, OUT, CLK, SER / QH' through 100 ohm)
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
KD = os.path.join(HW, "kicad", "regua")
BUILD = os.path.join(HERE, "build")
os.makedirs(KD, exist_ok=True)
os.makedirs(BUILD, exist_ok=True)

M.PARTS = {"R": []}
M.SHEETS = [("R", "Regua")]
M.CUR = ["R"]
M.PROJECT = "student_v04_regua"
M.KDIR = KD
M.BUILD = BUILD
M.REV = "Student V4 R5V4 regua"
M.NOTES = {"R": [
    "R · Regua universal de 4 teclas (74 x 14 x 1,2 mm): 4 TMAG5253BA3 + 74HC595D + 2 conectores SH de 6 vias (J1 entrada, J2 saida: opcao A) + 2 grupos de pads de solda (LK1, LK2: opcao B/D), tudo no fundo.",
    "J1 (entrada, cabo SH-6 de 25 mm da placa principal): 1 +3V3, 2 GND, 3 OUT, 4 CLK, 5 SER, 6 reservado. J2 (saida, so opcao A): igual com o pino 5 = QH'. LK1/LK2: pads do elo soldado, mesma ordem; LK2 pino 5 = QH' (por 100 ohm).",
    "O 595 liga o EN de cada sensor (QA..QD); SRCLK e RCLK juntos (a saida travada atrasa 1 pulso); OE em GND, SRCLR em +3V3.",
]}
M.ROOT_UUID = M.uid("root-regua")
M.SHEET_UUID = {"R": M.uid("sheet", "regua", "R")}
M.sym("PWR_FLAG", "power")

SH_FP = "Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal"
TMAG_FP = "Package_SON:Texas_X2SON-4-1EP_1.1x1.4mm_P0.5mm_EP0.8x0.6mm"
DFN_FP = "Package_DFN_QFN:DHVQFN-16-1EP_2.5x3.5mm_P0.5mm_EP1x2mm"
LINK_FP = "viaggio_micromod:LINK_5x1.00mm"   # footprint do projeto (so pads), escrito abaixo

# ------------------------------------------------------------------ parts
for k in range(1, 5):
    M.part("U%d" % k, "TMAG5253BA3", "TMAG5253BA3IQDMRR",
           {"1": "+3V3", "2": "GND", "3": "EN%d" % k, "4": "OUT", "5": "GND"}, "S%d" % k, fp=TMAG_FP, lcsc="C22401868",
           cls="estendida", price=0.60, status="final",
           note="tecla %d da regua: no verso, no centro da celula (u = %.2f mm); OUT em comum com os 3 outros; EN = QA..QD do 595 (saida em Hi-Z com EN baixo)"
                % (k, 9.25 + 18.5 * (k - 1)),
           datasheet="https://www.ti.com/lit/ds/symlink/tmag5253.pdf")
def sym595():
    left = [("14", "SER", "input"), ("11", "SRCLK", "input"), ("12", "RCLK", "input"), ("13", "~{OE}", "input"),
            ("10", "~{SRCLR}", "input"), ("16", "VCC", "power_in"), ("8", "GND", "power_in"), ("17", "EP", "power_in")]
    right = [("15", "QA", "output"), ("1", "QB", "output"), ("2", "QC", "output"), ("3", "QD", "output"),
             ("4", "QE", "output"), ("5", "QF", "output"), ("6", "QG", "output"), ("7", "QH", "output"),
             ("9", "QH'", "output")]
    return M.box_symbol("74HC595BQ", "U", [(left, right)], "8-bit shift register with output latch, DHVQFN-16 (SOT763-1), 17 = exposed pad = GND")


M.sym("74HC595BQ", "custom", sym595)
M.part("U5", "74HC595BQ", "74HC595BQ,115", {
    "1": "EN2", "2": "EN3", "3": "EN4", "4": "NC", "5": "NC", "6": "NC", "7": "NC", "8": "GND", "9": "QHP",
    "10": "+3V3", "11": "CLK", "12": "CLK", "13": "GND", "14": "SER", "15": "EN1", "16": "+3V3", "17": "GND"},
    "S5", fp=DFN_FP, lcsc="C730243", cls="estendida", price=0.176, status="conferir",
    note="registrador de deslocamento 8 bits em DHVQFN-16 (2,5 x 3,5 mm): o SOIC-16 (C5947, Basic) tem 6,9 mm de pads e nao cabe numa "
         "regua de 14 mm com pinos a 10,16 mm; QA..QD ligam o EN dos sensores 1..4, QE..QH sem uso; QH' = cascata; pad 17 no GND",
    datasheet="https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf")
# R5V4 (ligacao das reguas, opcao D): J1 = entrada por cabo SH-6 sob medida (placa principal -> 1a regua da fileira);
# LK1/LK2 = grupos de 5 pads de solda (1,0 mm) nas duas pontas, para o ELO SOLDADO regua -> regua (sem conector, sem J2).
M.part("J1", "Conn_01x06_MountingPin", "XY-SM06B-SRSS-TB",
       {"1": "+3V3", "2": "GND", "3": "OUT", "4": "CLK", "5": "SER", "6": "NC", "MP": "GND"}, "S6", fp=SH_FP,
       lcsc="C56123098", cls="estendida", price=0.069, status="conferir",
       note="entrada por cabo SH-6 sob medida (25 mm) vindo da placa principal; so e usado na 1a regua de cada fileira (nas outras fica sem cabo); "
            "no fundo, faixa de tras; mesmo conector SH-6 clone XYECONN da placa principal",
       datasheet="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf")
M.part("J2", "Conn_01x06_MountingPin", "XY-SM06B-SRSS-TB",
       {"1": "+3V3", "2": "GND", "3": "OUT", "4": "CLK", "5": "QHP_J", "6": "NC", "MP": "GND"}, "S7", fp=SH_FP,
       lcsc="C56123098", cls="estendida", price=0.069, status="conferir",
       note="saida por cabo SH-6 de 15 mm (opcao A) para a regua seguinte; pino 5 = QH' do 595 por 100 ohm; na recomendada (D) fica sem cabo "
            "(o elo e soldado em LK2): mantido so para a regua aceitar a opcao A sem mexer na placa (US$ 0,07 por regua)",
       datasheet="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf")
M.sym("Conn_01x05", "Connector_Generic")
for ref, what, net5 in (("LK1", "IN", "SER"), ("LK2", "OUT", "QHP_J")):
    M.part(ref, "Conn_01x05", "ELO " + what,
           {"1": "+3V3", "2": "GND", "3": "OUT", "4": "CLK", "5": net5}, "S6", fp=LINK_FP, lcsc="", cls="", price=0.0,
           status="final", mount="em casa (solda)",
           note=("pads do elo soldado, entrada (vem do OUT da regua anterior da fileira)" if what == "IN"
                 else "pads do elo soldado, saida (vai para a entrada da regua seguinte): 5 pads de 1,4 x 0,7 mm a 1,0 mm, no fundo, na ponta da regua; fio 28-30 AWG de 7 mm; sem peca do pedido JLCPCB"))
M.R("R1", "100", "QHP", "QHP_J", "S7", note="serie no QH' (cascata para a proxima regua)")
for k in range(1, 5):
    M.C("C%d" % k, "100nF", "+3V3", "GND", "S%d" % k, note="desacoplamento do TMAG5253 %d, junto do pino 1" % k)
M.C("C5", "100nF", "+3V3", "GND", "S5", note="desacoplamento do 595")
M.C("C6", "10uF", "+3V3", "GND", "S5", "0805", note="reservatorio da regua (junto do conector de entrada)")


def write_link_fp():
    """5 SMD pads 1.4 x 0.7 mm, pitch 1.0 mm along y (pad 1 at y = -2.0), centred; board-only (not in the BOM/CPL)."""
    d = os.path.join(KD, "viaggio_micromod.pretty")
    os.makedirs(d, exist_ok=True)
    nl = chr(10)
    lines = ['(footprint "LINK_5x1.00mm" (version 20240108) (generator "pcbnew") (layer "F.Cu")',
             '  (descr "R5V4: 5 pads de solda do elo da regua, passo 1,0 mm, 1,4 x 0,7 mm")',
             '  (attr smd board_only exclude_from_pos_files exclude_from_bom)',
             '  (fp_rect (start -0.9 -2.45) (end 0.9 2.45) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))']
    for i in range(5):
        lines.append('  (pad "%d" smd rect (at 0 %.2f) (size 1.4 0.7) (layers "F.Cu" "F.Mask" "F.Paste"))' % (i + 1, -2.0 + i))
    lines.append(')')
    open(os.path.join(d, "LINK_5x1.00mm.kicad_mod"), "w", newline=nl).write(nl.join(lines) + nl)




def main():
    write_link_fp()
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
    os.replace(os.path.join(BUILD, "student_v04_regua_erc.json"), os.path.join(BUILD, "regua_erc.json"))
    os.replace(os.path.join(BUILD, "student_v04_regua_netlist.net"), os.path.join(BUILD, "regua_netlist.net"))
    # BOM
    rows = {}
    for p in parts:
        if p["ref"].startswith("LK"):          # pads de solda: nada no pedido da JLCPCB
            continue
        r = rows.setdefault(p["lcsc"], dict(p, refs=[]))
        r["refs"].append(p["ref"])
    with open(os.path.join(HW, "bom_regua.csv"), "w", newline="", encoding="utf-8") as f:
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
