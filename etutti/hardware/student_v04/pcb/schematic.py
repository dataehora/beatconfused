"""Write the eTutti Student V4 main-board schematic (interface only, R3V4), run ERC, compare it with the V3.

    python etutti/hardware/student_v04/pcb/schematic.py

Plain CPython (stdlib only); it calls KiCad 10's kicad-cli for ERC and the netlists.

The V3 circuit with the F2 changes (SPEC R2V4/R3V4): no sensors and no multiplexers on the main board (the 4-sensor
rulers carry the TMAG5253 and a 74HC595 each); sheet R = the four row connectors (JST SH 6-way, one per row) with
the OUT_R1..R4 pull-downs and the 330 ohm series resistors (R8V4) of the shared SCAN_CLK / SCAN_DATA; the screen connector
J401 is a 4-way SH (Qwiic order: GND, 3V3, SDA, SCL; R11V4); microphone: C310 on MIC_BIAS (datasheet Fig. 20); Teensy pins as pcb/PINOS.md.
The part references and the symbol uuids are the V3's (same uuid namespace).

Writes (under etutti/hardware/student_v04/): kicad/student_v04.kicad_sch (root) + student_v04_<S>.kicad_sch,
viaggio_micromod.kicad_sym, sym-lib-table, fp-lib-table, viaggio_micromod.pretty/;
pcb/build/student_v04_erc.json, student_v04_netlist.net, v3_netlist.net; pcb/bom_esquema.csv.
Exits non-zero on an ERC error, a netlist mismatch, or a difference from the V3 netlist outside the listed changes.
"""
import csv
import json
import os
import re
import subprocess
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sexpr as S  # noqa: E402
import footprints  # noqa: E402

KICAD = "C:/Program Files/KiCad/10.0"
KICAD_SYM = KICAD + "/share/kicad/symbols"
KICAD_FP = KICAD + "/share/kicad/footprints"
KICAD_CLI = KICAD + "/bin/kicad-cli.exe"
KDIR = os.path.normpath(os.path.join(HERE, "..", "kicad"))
V3_SCH = os.path.normpath(os.path.join(HERE, "..", "..", "student_v03", "kicad", "student_v03.kicad_sch"))
BUILD = os.path.join(HERE, "build")
PROJECT = "student_v04"
LIB = "viaggio_micromod"
DATE = "2026-11-21"
REV = "Student V4 R3V4"

NS = uuid.UUID("3b8e6f0c-2d4a-4f61-8c7e-5a9d1e2f4b22")


def uid(*key):
    return str(uuid.uuid5(NS, "/".join(str(k) for k in key)))


# ====================================================================== symbols
_libs = {}


def _lib(name):
    if name not in _libs:
        root = S.parse(open(os.path.join(KICAD_SYM, name + ".kicad_sym"), encoding="utf-8").read())
        _libs[name] = {s[1]: s for s in S.find(root, "symbol")}
    return _libs[name]


def _rename(sym, new):
    old = sym[1]
    sym[1] = S.Q(new)
    for sub in S.find(sym, "symbol"):
        sub[1] = S.Q(new + sub[1][len(old):])
    return sym


def _copy(n):
    return [_copy(x) for x in n] if isinstance(n, list) else n


def kicad_symbol(lib, name):
    """A KiCad library symbol, with 'extends' flattened."""
    s = _copy(_lib(lib)[name])
    ext = S.first(s, "extends")
    if not ext:
        return s
    parent = _rename(kicad_symbol(lib, ext[1]), name)
    own = {p[1]: p for p in S.find(s, "property")}
    out = ["symbol", S.Q(name)]
    for item in parent[2:]:
        if isinstance(item, list) and item[0] == "property" and item[1] in own:
            out.append(own.pop(item[1]))
        elif isinstance(item, list) and item[0] == "symbol":
            continue
        else:
            out.append(item)
    out += list(own.values())
    out += S.find(parent, "symbol")
    return out


def _pin(num, name, etype, x, y, ang):
    return ["pin", etype, "line", ["at", str(x), str(y), str(ang)], ["length", "2.54"],
            ["name", S.Q(name), ["effects", ["font", ["size", "1.27", "1.27"]]]],
            ["number", S.Q(num), ["effects", ["font", ["size", "1.27", "1.27"]]]]]


def _prop(key, val, x, y, hide=False):
    p = ["property", S.Q(key), S.Q(val), ["at", str(x), str(y), "0"]]
    if hide:
        p.append(["hide", "yes"])
    p.append(["effects", ["font", ["size", "1.27", "1.27"]]])
    return p


def box_symbol(name, ref, units, description=""):
    """A plain box symbol: units = [(left_pins, right_pins)], pin = (num, name, type)."""
    sym = ["symbol", S.Q(name), ["pin_names", ["offset", "1.016"]], ["exclude_from_sim", "no"],
           ["in_bom", "yes"], ["on_board", "yes"]]
    maxlen = max(len(p[1]) for lp, rp in units for p in lp + rp)
    half = max(5.08, round(((maxlen * 1.27 + 2.0) / 2.54) + 0.5) * 2.54)
    tallest = max(max(len(lp), len(rp)) for lp, rp in units)
    top = (tallest + 1) * 2.54 / 2
    sym += [_prop("Reference", ref, 0, round(top + 3.81, 2)), _prop("Value", name, 0, round(-top - 3.81, 2)),
            _prop("Footprint", "", 0, 0, True), _prop("Datasheet", "", 0, 0, True),
            _prop("Description", description, 0, 0, True)]
    for u, (lp, rp) in enumerate(units, 1):
        n = max(len(lp), len(rp))
        y0 = round(((n - 1) // 2) * 2.54, 2)
        body = ["symbol", S.Q("%s_%d_1" % (name, u)),
                ["rectangle", ["start", str(-half), str(round(y0 + 2.54, 2))],
                 ["end", str(half), str(round(y0 - n * 2.54, 2))],
                 ["stroke", ["width", "0.254"], ["type", "default"]], ["fill", ["type", "background"]]]]
        for side, pins in ((-1, lp), (1, rp)):
            for i, p in enumerate(pins):
                if p is None:
                    continue
                x = round(side * (half + 2.54), 2)
                body.append(_pin(p[0], p[1], p[2], x, round(y0 - i * 2.54, 2), 0 if side < 0 else 180))
        sym.append(body)
    return sym


# MicroMod M.2 Key E pads, as the SparkFun MicroMod Teensy wires them
# (Hardware/MicroMod-Teensy.sch, J1 "MICROMOD-2222"): pad -> (MicroMod name, Teensy pin or role).
# Pads 13, 15, 21, 23 are not connected on the Teensy module.
MM_PADS = {
    1: ("GND", "GND"), 2: ("3.3V", "3V3"), 3: ("USB_D+", "USB1 D+"), 4: ("3.3V_EN", "28"),
    5: ("USB_D-", "USB1 D-"), 6: ("RESET#", "ONOFF"), 7: ("GND", "GND"), 8: ("G11", "27/A13"),
    9: ("USB_VIN", "VUSB"), 10: ("D0", "4"), 11: ("BOOT#", "PROGRAM"), 12: ("I2C_SDA", "18/A4"),
    13: ("RTS1", "-"), 14: ("I2C_SCL", "19/A5"), 15: ("CTS1", "-"), 16: ("I2C_INT#", "29"),
    17: ("TX1", "1"), 18: ("D1", "5"), 19: ("RX1", "0"), 20: ("RX2", "16/A2"), 21: ("SWDCK", "-"),
    22: ("TX2", "17/A3"), 23: ("SWDIO", "-"),
    32: ("PWM0", "3"), 33: ("GND", "GND"), 34: ("A0", "14/A0"), 35: ("USBHOST_D+", "USB2 D+"),
    36: ("GND", "GND"), 37: ("USBHOST_D-", "USB2 D-"), 38: ("A1", "15/A1"), 39: ("GND", "GND"),
    40: ("G0", "40"), 41: ("CAN_RX", "30"), 42: ("G1", "41"), 43: ("CAN_TX", "31"), 44: ("G2", "42"),
    45: ("GND", "GND"), 46: ("G3", "43"), 47: ("PWM1", "2"), 48: ("G4", "44"),
    49: ("BATT_VIN/3", "22/A8"), 50: ("AUD_BCLK", "21/A7"), 51: ("I2C_SDA1", "25/A11"),
    52: ("AUD_LRCLK", "20/A6"), 53: ("I2C_SCL1", "24/A10"), 54: ("AUD_IN", "8"), 55: ("SPI_CS#", "10"),
    56: ("AUD_OUT", "7"), 57: ("SPI_SCK", "13"), 58: ("AUD_MCLK", "23/A9"), 59: ("SPI_SDO", "11"),
    60: ("SDIO_SCK", "36"), 61: ("SPI_SDI", "12"), 62: ("SDIO_CMD", "37"), 63: ("G10", "33"),
    64: ("SDIO_DATA0", "35"), 65: ("G9", "32"), 66: ("SDIO_DATA1", "34"), 67: ("G8", "26/A12"),
    68: ("SDIO_DATA2", "39"), 69: ("G7", "9"), 70: ("SDIO_DATA3", "38"), 71: ("G6", "6"),
    72: ("RTC_3V", "VBAT SNVS"), 73: ("G5", "45"), 74: ("3.3V", "3V3"), 75: ("GND", "GND"),
}


def micromod_symbol():
    """M.2 Key E socket with the MicroMod Teensy's pad names: 'MicroMod name / Teensy pin'."""
    def pin(n):
        nm, role = MM_PADS[n]
        if nm == "GND":
            return (str(n), "GND", "power_in")
        if nm == "3.3V":
            return (str(n), "3.3V", "power_in")
        if nm == "USB_VIN":
            return (str(n), "USB_VIN", "input")
        label = nm if role in ("-", "GND", "3V3") or nm == role else "%s (%s)" % (nm, role)
        return (str(n), label, "passive" if role in ("-", "USB1 D+", "USB1 D-", "USB2 D+", "USB2 D-", "VBAT SNVS")
                else "bidirectional")
    power = [1, 7, 33, 36, 39, 45, 75, 2, 74, 9, 4, 6, 11, 72]
    rest = [n for n in sorted(MM_PADS) if n not in power]
    h = (len(rest) + 1) // 2
    unit1 = ([pin(n) for n in power] + [("MP", "MP", "passive")], [])
    unit2 = ([pin(n) for n in rest[:h]], [pin(n) for n in rest[h:]])
    return box_symbol("MicroMod_M.2_E", "J", [unit1, unit2],
                      "M.2 Key E socket (67 pins) for a SparkFun MicroMod processor; pin names = MicroMod name "
                      "(Teensy MicroMod pin)")


def jack_symbol():
    return box_symbol("PJ-327A", "J", [([("2", "S", "passive"), ("5", "S", "passive")],
                                        [("4", "T", "passive"), ("3", "TN", "passive"), ("6", "R", "passive")])],
                      "3.5 mm stereo jack, tip switch (3 NC against 4)")


def led_pins(s):
    """LED_Dual_AAKK renumbered to the 1615 part's pads: A1 = 1 (red), K1 = 2, A2 = 3 (green), K2 = 4."""
    new = {"A1": "1", "K1": "2", "A2": "3", "K2": "4"}

    def walk(n):
        for x in n:
            if isinstance(x, list) and x and x[0] == "pin":
                nm = S.first(x, "name")[1]
                S.first(x, "number")[1] = S.Q(new[nm])
            elif isinstance(x, list):
                walk(x)
    walk(s)


def tmag_symbol():
    return box_symbol("TMAG5253BA3", "U", [([("1", "VCC", "power_in"), ("3", "EN", "input")],
                                            [("4", "OUT", "tri_state"), ("2", "GND", "power_in"),
                                             ("5", "EP", "passive")])],
                      "TI TMAG5253 linear Hall sensor with enable, X2SON-4")


SYMBOLS = {}       # name -> sexpr (top-level name = name)


def sym(name, lib=None, base=None, fix=None):
    """Register a symbol under our library name `name`."""
    if name in SYMBOLS:
        return name
    if lib == "custom":
        s = base()
    else:
        s = _rename(kicad_symbol(lib, base or name), name)
    def walk(n):   # unspecified pins only warn in ERC; ours are all passive in fact
        for x in n:
            if isinstance(x, list) and x and x[0] == "pin" and x[1] == "unspecified":
                x[1] = "passive"
            elif isinstance(x, list):
                walk(x)
    walk(s)
    if fix:
        fix(s)
    SYMBOLS[name] = s
    return name


def pin_table(name):
    """{(unit): [(num, name, type, x, y, ang)]}; unit 0 = shared by all units."""
    out = {}
    for sub in S.find(SYMBOLS[name], "symbol"):
        m = re.match(r".*_(\d+)_(\d+)$", sub[1])
        unit = int(m.group(1))
        if m.group(2) not in ("0", "1") and unit != 0:   # De Morgan alternates
            continue
        for p in S.find(sub, "pin"):
            at = S.first(p, "at")
            out.setdefault(unit, []).append((S.first(p, "number")[1], S.first(p, "name")[1], p[1],
                                             float(at[1]), float(at[2]), int(float(at[3]))))
    return out


# ====================================================================== parts
FP = {
    "0402R": "Resistor_SMD:R_0402_1005Metric", "0402C": "Capacitor_SMD:C_0402_1005Metric",
    "0603C": "Capacitor_SMD:C_0603_1608Metric", "0805C": "Capacitor_SMD:C_0805_2012Metric",
    "0603L": "Inductor_SMD:L_0603_1608Metric", "0805L": "Inductor_SMD:L_0805_2012Metric",
    "SOT23": "Package_TO_SOT_SMD:SOT-23", "SOT235": "Package_TO_SOT_SMD:SOT-23-5",
    "SOT236": "Package_TO_SOT_SMD:SOT-23-6",
}

# (lcsc, class, est. unit price USD, status). Prices are estimates (LCSC/JLCPCB pages
# give no price to a script); class "basica"/"estendida"; status final/conferir.
PASSIVES = {
    ("C", "100nF", "0402"): ("C1525", "basica", 0.001, "final"),
    ("C", "10nF", "0402"): ("C15195", "basica", 0.001, "final"),
    ("C", "220nF", "0402"): ("C16772", "basica", 0.002, "conferir"),
    # M3b (SPEC v2.5): no basic 150 nF 0402 exists; Murata GRM155R71C154KA12D, 16 V X7R (LCSC 31850 in stock, 28 Oct 2026)
    ("C", "150nF", "0402"): ("C162182", "estendida", 0.0135, "final"),
    ("C", "1uF", "0402"): ("C52923", "basica", 0.002, "final"),
    ("C", "2.2uF", "0402"): ("C12530", "basica", 0.003, "conferir"),
    ("C", "4.7uF", "0603"): ("C19666", "basica", 0.004, "final"),
    ("C", "4.7uF", "0402"): ("C23733", "basica", 0.003, "conferir"),
    ("C", "10uF", "0402"): ("C15525", "basica", 0.004, "conferir"),
    ("C", "10uF", "0603"): ("C19702", "basica", 0.005, "final"),
    ("C", "10uF", "0805"): ("C15850", "basica", 0.008, "final"),
    ("C", "12pF", "0402"): ("C1547", "basica", 0.001, "conferir"),
    ("C", "20pF", "0402"): ("C1554", "basica", 0.001, "conferir"),
    ("R", "0", "0402"): ("C17168", "basica", 0.001, "final"),        # R8V4: R305 (0 ohm, bias total de 2 k)
    ("R", "100", "0402"): ("C25076", "basica", 0.001, "final"),
    ("R", "270", "0402"): ("C25099", "estendida", 0.001, "final"),
    ("R", "330", "0402"): ("C25104", "basica", 0.001, "conferir"),
    ("R", "470", "0402"): ("C25117", "basica", 0.001, "conferir"),
    ("R", "1k", "0402"): ("C11702", "basica", 0.001, "final"),
    ("R", "1.5k", "0402"): ("C25867", "basica", 0.001, "conferir"),
    ("R", "1.8k", "0402"): ("C25871", "estendida", 0.001, "final"),
    ("R", "2.2k", "0402"): ("C25879", "basica", 0.001, "conferir"),
    ("R", "5.1k", "0402"): ("C25905", "basica", 0.001, "final"),
    ("R", "10k", "0402"): ("C25744", "basica", 0.001, "final"),
    ("R", "100k", "0402"): ("C25741", "basica", 0.001, "final"),
    ("R", "680k", "0402"): ("C4131", "estendida", 0.002, "final"),   # UNI-ROYAL 0402WGF6803TCE (M3b)
    ("R", "1M", "0402"): ("C26083", "basica", 0.001, "final"),
    ("R", "2.2M", "0402"): ("", "estendida", 0.002, "conferir"),
}

SHEETS = [("P", "Processador"), ("E", "Energia"), ("F", "Fone"), ("I", "Interface"),
          ("A", "Alto-falante"), ("R", "Reguas")]
PARTS = {s: [] for s, _ in SHEETS}
CUR = ["P"]


def part(ref, symbol, value, nets, code, fp="", lcsc="", cls="", price=None, mount="JLC", status="conferir",
         note="", dnp=False, rot=0, nc_rest=False, datasheet=""):
    PARTS[CUR[0]].append(dict(ref=ref, sym=symbol, value=value, nets=nets, code=code, fp=fp, lcsc=lcsc, cls=cls,
                              price=price, mount=mount, status=status, note=note, dnp=dnp, rot=rot,
                              nc_rest=nc_rest, datasheet=datasheet, sheet=CUR[0]))


def RC(kind, ref, value, a, b, code, size="0402", note="", dnp=False):
    lc, cls, price, st = PASSIVES[(kind, value, size)]
    fp = FP[size + kind]
    part(ref, sym("R", "Device") if kind == "R" else sym("C", "Device"), value, {"1": a, "2": b}, code, fp=fp,
         lcsc=lc, cls=cls, price=price, status=st, note=note, dnp=dnp, rot=90,
         mount="nao montar" if dnp else "JLC")


R = lambda *a, **k: RC("R", *a, **k)   # noqa: E731
C = lambda *a, **k: RC("C", *a, **k)   # noqa: E731


def bat54c(ref, a1, a2, k, code, note=""):
    """V3: a BAV70 (Basic, same SOT-23 pins: 1 A1, 2 A2, 3 common cathode); the symbol is the BAT54C's."""
    part(ref, sym("BAT54C", "Diode"), "BAV70", {"1": a1, "2": a2, "3": k}, code, fp=FP["SOT23"],
         lcsc="C68978", cls="basica", price=0.02, status="final", note=note,
         datasheet="https://www.lcsc.com/product-detail/C68978.html")


def pmos(ref, g, s, d, code, note="", dnp=False):
    part(ref, sym("AO3401A", "Transistor_FET"), "AO3401A", {"1": g, "2": s, "3": d}, code, fp=FP["SOT23"],
         lcsc="C15127", cls="basica", price=0.01, status="final", note=note, dnp=dnp,
         mount="nao montar" if dnp else "JLC",
         datasheet="https://www.aosmd.com/res/datasheets/AO3401A.pdf")


def nmos(ref, g, s, d, code, note="", dnp=False):
    part(ref, sym("AO3400A", "Transistor_FET"), "AO3400A", {"1": g, "2": s, "3": d}, code, fp=FP["SOT23"],
         lcsc="C20917", cls="basica", price=0.01, status="final", note=note, dnp=dnp,
         mount="nao montar" if dnp else "JLC",
         datasheet="https://www.aosmd.com/res/datasheets/AO3400A.pdf")


def gate(ref, kind, a, b, y, vcc, code, note=""):
    if kind == "04":
        nets = {"1": "NC", "2": a, "3": "GND", "4": y, "5": vcc}
        lc = "C7827"
    else:
        nets = {"1": a, "2": b, "3": "GND", "4": y, "5": vcc}
        lc = "C7666"
    part(ref, sym("74LVC1G" + kind, "74xGxx"), "74LVC1G" + kind, nets, code, fp=FP["SOT235"], lcsc=lc,
         cls="estendida", price=0.03, status="final", note=note,
         datasheet="https://www.ti.com/lit/ds/symlink/sn74lvc1g%s.pdf" % kind)


# ---------------------------------------------------------------- P: processor (MicroMod Teensy)
sym("MicroMod_M.2_E", "custom", micromod_symbol)
sym("TMAG5253BA3", "custom", tmag_symbol)

# Teensy MicroMod pin -> net. Same Teensy numbers as the Viaggio v2.1 (PINOS.md), plus 28 = 3.3V_EN.
TEENSY_NETS = {
    "0": "CHG_STAT", "4": "VOL_SW", "2": "SCAN_DATA_P", "3": "SCAN_CLK_P", "6": "SEL_SW",
    "7": "I2S_TX", "8": "I2S_RX", "9": "SEL_B", "10": "KEEP", "11": "SEL_A", "12": "AMP_SD",
    "14/A0": "OUT_R1", "15/A1": "OUT_R2", "16/A2": "VBAT_S", "17/A3": "HP_DET", "18/A4": "I2C_SDA",
    "19/A5": "I2C_SCL", "20/A6": "I2S_LRCLK", "21/A7": "I2S_BCLK", "22/A8": "VOL_A", "23/A9": "AUD_MCLK_P",
    "24/A10": "VOL_B", "25/A11": "MIC_DET", "26/A12": "OUT_R3", "27/A13": "OUT_R4", "28": "NC",
}


def p1_nets():
    nets = {"MP": "GND"}
    for n, (nm, role) in MM_PADS.items():
        if nm == "GND":
            nets[str(n)] = "GND"
        elif nm == "3.3V":
            nets[str(n)] = "+3V3"
        elif nm == "USB_VIN":
            nets[str(n)] = "VBUS"
        elif role == "USB1 D+":
            nets[str(n)] = "USB_DP"
        elif role == "USB1 D-":
            nets[str(n)] = "USB_DN"
        elif role == "ONOFF":
            nets[str(n)] = "ONOFF"
        elif role == "PROGRAM":
            nets[str(n)] = "PROG"
        elif role in TEENSY_NETS:
            nets[str(n)] = TEENSY_NETS[role]
        else:
            nets[str(n)] = "NC"
    missing = set(TEENSY_NETS) - {r for _, r in MM_PADS.values()}
    if missing:
        raise SystemExit("Teensy pins not on the MicroMod connector: %s" % sorted(missing))
    return nets


CUR[0] = "P"
part("J101", "MicroMod_M.2_E", "91302-42-067RCE", p1_nets(), "P1", fp="%s:%s" % (LIB, footprints.M2_NAME),
     lcsc="C48985906", cls="estendida", price=1.26, status="conferir",
     note="UMAX M.2 Key E 67 pinos, 0,5 mm, 4,2 mm (estoque LCSC 622 em 25 out 2026; o LOTES C841659 estava "
          "com 0); footprint pelo desenho UMAX C-91302-42 rev C; no verso; modulo SparkFun MicroMod Teensy "
          "DEV-16402 encaixado em casa",
     datasheet="https://datasheet.lcsc.com/datasheet/pdf/fa57621554b717c54a395d0658cff748.pdf?productCode=C48985906")
# H101 (SMT standoff) is a plain 2.7 mm hole in the V3 (board only: M2.5 screw, 2.5 mm nylon spacer, module, nut)
C("C101", "10uF", "+3V3", "GND", "P1", "0805", note="3,3 V junto dos pads 2/74 do J101")
C("C102", "100nF", "+3V3", "GND", "P1")
part("TP101", sym("TestPoint", "Connector"), "RESET#/ONOFF", {"1": "ONOFF"}, "P1",
     fp="TestPoint:TestPoint_Pad_D1.5mm", lcsc="", cls="-", price=0.0, mount="sem peca (pad)", status="final",
     note="pad 6 do MicroMod = ONOFF do RT1062 no modulo Teensy (nao e o POR_B); ver ELETRONICA.md")
R("R105", "100", "AUD_MCLK_P", "AUD_MCLK", "P1", note="MCLK 11,3 MHz: em serie, junto do J101 (SPEC 4, 5o)")

# ---------------------------------------------------------------- E: power
CUR[0] = "E"
part("J201", sym("USB_C_Receptacle_USB2.0_16P", "Connector"), "TYPE-C-31-M-12",
     {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND", "A4": "VBUS", "A9": "VBUS",
      "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN",
      "B7": "USB_DN", "A8": "NC", "B8": "NC"}, "E1", fp="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     lcsc="C165948", cls="estendida", price=0.15, status="final", note="lado de cima, borda esquerda, boca para fora")
R("R201", "5.1k", "CC1", "GND", "E1")
R("R202", "5.1k", "CC2", "GND", "E1")
part("U201", sym("USBLC6-2SC6", "Power_Protection"), "USBLC6-2SC6",
     {"1": "USB_DP", "6": "USB_DP", "3": "USB_DN", "4": "USB_DN", "5": "VBUS", "2": "GND"}, "E2",
     fp=FP["SOT236"], lcsc="C7519", cls="basica", price=0.05, status="conferir",
     note="lado de cima, junto do USB-C (SPEC v2.3)",
     datasheet="https://www.st.com/resource/en/datasheet/usblc6-2.pdf")
part("D201", sym("SMF5.0A", "Diode", "SMAJ5.0A"), "SMF5.0A", {"1": "VBUS", "2": "GND"}, "E2",
     fp="Diode_SMD:D_SOD-123F", lcsc="C151296", cls="estendida", price=0.05, status="final",
     note="TVS do VBUS (Pocket D60); lado de cima, junto do USB-C (SPEC v2.3)", rot=90)
part("U202", sym("BQ24074RGT", "Battery_Management"), "BQ24074RGTR",
     {"1": "BAT_NTC", "2": "VBAT", "3": "VBAT", "4": "GND", "5": "GND", "6": "CHG_EN1", "7": "NC", "8": "GND",
      "9": "CHG_N", "10": "VSYS", "11": "VSYS", "12": "CHG_ILIM", "13": "VBUS", "14": "NC", "15": "NC",
      "16": "CHG_ISET", "17": "GND"}, "E3", fp="Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm",
     lcsc="C54313", cls="estendida", price=1.10, status="final",
     note="USB500 (EN2=0, EN1=1), 500 mA, NTC no TS; TMR e ITERM abertos = padrao; OUT 4,4 V com USB",
     datasheet="https://www.ti.com/lit/ds/symlink/bq24074.pdf")
C("C201", "10uF", "VBUS", "GND", "E3", "0805")
C("C202", "10uF", "VSYS", "GND", "E3", "0805")
C("C203", "10uF", "VBAT", "GND", "E3", "0805")
# M3 (SPEC v2.4): VSYS cap right at the charger's OUT pins (10/11). No room on the back (D205, the VSYS
# vias and the signals round them), so it sits on the top side, its VSYS pad on the VSYS track over the
# pins and its GND pad next to U202's thermal vias. Placed on the J1 board by viaggio_j1/m3.py.
C("C210", "10uF", "VSYS", "GND", "E3", "0603",
  note="VSYS junto dos pinos OUT (10/11) do U202, no lado de cima (M3)")
R("R203", "2.2k", "CHG_ISET", "GND", "E3", note="ICHG = 890/2200 = 0,405 A (K_ISET do datasheet)")
R("R204", "1.5k", "CHG_ILIM", "GND", "E3", note="so vale com EN2=1 (1,07 A); obrigatorio")
R("R205", "10k", "VBUS", "CHG_EN1", "E3")
# V3: Q201 (charge-light driver of the V1) removed
R("R206", "100k", "VBUS", "CHG_N", "E3")
# V3: R207 (charge-light driver of the V1) removed
# V3: Q202 (charge-light driver of the V1) removed
bat54c("D202", "CHG_STAT", "NC", "CHG_N", "E3", note="leitura do ~CHG pelo pino 0 (so com USB; R3V4: saiu do 26, que virou OUT_R3)")
R("R208", "1M", "VBAT", "VBAT_S", "E3", note="medida da bateria: V(pino 16) = VBAT/2")
R("R209", "1M", "VBAT_S", "GND", "E3")
C("C204", "100nF", "VBAT_S", "GND", "E3")
# power latch: click of I1 (volume) -> PWR_KEY, firmware KEEP, and (V3) a USB plug through D206.
# EN of E4 = EN_REQ = click OR KEEP OR USB present (VBUS_S via D206). The V1/V2 "USB AND PWR_EN" hold (U203, D204, R217,
# R218, C213; pin 28 = MicroMod 3.3V_EN) is gone since 19 Nov 2026 (J chose: USB wakes the device; with a cable the firmware
# sleeps, it does not cut the 3.3 V): D206 made it redundant and it could not switch off with USB anymore.
pmos("Q203", "VOL_SW_N", "VSYS", "PWR_KEY", "E3", note="o clique do volume liga o EN")
R("R210", "100k", "VSYS", "VOL_SW_N", "E3")
R("R211", "100k", "PWR_KEY", "GND", "E3")
bat54c("D203", "PWR_KEY", "KEEP", "EN_REQ", "E3", note="OU do clique e do KEEP")
R("R212", "1M", "EN_REQ", "GND", "E3", note="EN do TPS63001 baixo sem pedido")
R("R213", "100k", "KEEP", "GND", "E3", note="KEEP baixo enquanto o modulo parte")
R("R214", "10k", "VBUS", "VBUS_S", "E3")
R("R215", "100k", "VBUS_S", "GND", "E3")
C("C205", "100nF", "+3V3", "GND", "E3")
bat54c("D206", "VBUS_S", "NC", "EN_REQ", "E3", note="V3: o USB ligado liga o 3,3 V (a tela mostra a carga em brilho baixo)")
bat54c("D205", "VOL_SW", "ONOFF", "VOL_SW_N", "E3",
       note="o clique do volume chega ao pino 25 e ao ONOFF do modulo (pad 6) sem levar o VSYS a eles")
part("U204", sym("TPS63001", "Regulator_Switching"), "TPS63001DRCR",
     {"1": "+3V3", "2": "BB_L2", "3": "GND", "4": "BB_L1", "5": "VSYS", "6": "EN_REQ", "7": "GND",
      "8": "BB_VINA", "9": "GND", "10": "+3V3", "11": "GND"}, "E4", fp="Package_SON:Texas_DRC0010J",
     lcsc="C28060", cls="estendida", price=1.40, status="final",
     note="3,3 V fixo; PS/SYNC baixo = economia; EN = EN_REQ (sem a porta U206 da v2.1)",
     datasheet="https://www.ti.com/lit/ds/symlink/tps63001.pdf")
part("L201", sym("L", "Device"), "2.2uH", {"1": "BB_L1", "2": "BB_L2"}, "E4", fp="Inductor_SMD:L_Changjiang_FNR4020S",
     lcsc="C167825", cls="estendida", price=0.08, status="final", note="FNR4020S2R2MT (Pocket L10)", rot=90)
C("C206", "10uF", "VSYS", "GND", "E4", "0805")
C("C207", "10uF", "+3V3", "GND", "E4", "0805")
C("C208", "10uF", "+3V3", "GND", "E4", "0805")
R("R216", "100", "VSYS", "BB_VINA", "E4")
C("C209", "100nF", "BB_VINA", "GND", "E4")
part("J202", sym("Conn_01x03_MountingPin", "Connector_Generic_MountingPin"), "S3B-PH-SM4-TB",
     {"1": "VBAT", "2": "BAT_NTC", "3": "GND", "MP": "GND"}, "E6",
     fp="Connector_JST:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal", lcsc="C265101", cls="estendida",
     price=0.30, status="final", note="bateria 1 = +, 2 = NTC, 3 = - (ordem do Pocket; conferir o cabo)")

# ---------------------------------------------------------------- F: headphone codec
CUR[0] = "F"
part("U301", sym("SGTL5000XNLA3", "Audio"), "SGTL5000XNLA3",
     {"1": "HP_R", "2": "HP_VGND", "3": "SGTL_VDDA", "4": "HP_L", "5": "SGTL_VAG", "6": "NC", "7": "NC",
      "8": "NC", "9": "NC", "10": "MIC_IN", "11": "MIC_BIAS", "12": "+3V3", "13": "AUD_MCLK", "14": "I2S_LRCLK",
      "15": "I2S_BCLK", "16": "I2S_RX", "17": "I2S_TX", "18": "I2C_SDA", "19": "I2C_SCL", "20": "SGTL_VDDD",
      "21": "GND"}, "F1", fp="Package_DFN_QFN:QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm", lcsc="C2651833",
     cls="estendida", price=1.80, status="conferir",
     note="como a Audio Board Rev D2 (endereco I2C fixo 0x0A); V2: entrada de microfone (MIC, MIC_BIAS) e I2S_DOUT ligados",
     datasheet="https://www.pjrc.com/teensy/SGTL5000.pdf")
part("FB301", sym("FerriteBead_Small", "Device"), "600R@100MHz", {"1": "+3V3", "2": "SGTL_VDDA"}, "F1",
     fp=FP["0603L"], lcsc="C1002", cls="basica", price=0.005, status="final",   # Sunlord GZ1608D601TF (M3b)
     note="Audio Board: Ferrite 600 no VDDA", rot=90)
C("C301", "2.2uF", "SGTL_VDDA", "GND", "F1")
C("C302", "100nF", "SGTL_VDDA", "GND", "F1")
C("C303", "2.2uF", "+3V3", "GND", "F1", note="VDDIO")
C("C304", "100nF", "+3V3", "GND", "F1")
C("C305", "100nF", "+3V3", "GND", "F1")
part("U302", sym("XC6206P182MR", "Regulator_Linear", "XC6206PxxxMR"), "XC6206P182MR",
     {"1": "GND", "2": "SGTL_VDDD", "3": "+3V3"}, "F1", fp="Package_TO_SOT_SMD:SOT-23-3", lcsc="C347373",
     cls="estendida", price=0.03, status="conferir", note="1,8 V do VDDD (a Audio Board usa AP7313)")
C("C306", "2.2uF", "SGTL_VDDD", "GND", "F1")
C("C307", "100nF", "SGTL_VAG", "GND", "F1", note="datasheet do SGTL5000 (figuras 19 e 20): VAG = 0,1 uF")
R("R301", "2.2k", "+3V3", "I2C_SDA", "F1")
R("R302", "2.2k", "+3V3", "I2C_SCL", "F1")
# The PJ-313D-6A of step 3.1 (C95463) turned out to have no tip switch (datasheet: 3 contacts, 6 pads).
sym("PJ-327A", "custom", jack_symbol)
part("J301", "PJ-327A", "PJ-327A",
     {"2": "HP_VGND", "5": "HP_VGND", "6": "HP_R", "4": "HP_L", "3": "HP_TIPSW"}, "F2",
     fp="%s:Jack_3.5mm_PJ-327A_SMD" % LIB, lcsc="C49284723", cls="estendida", price=0.10, status="conferir",
     note="SMD, angulo reto, XUNPU (V3; o SHOU HAN 5JJ foi trocado porque a JLCPCB o marca como dificil de montar); 2/5 manga (HP_VGND, nunca no GND), 6 anel, 4 ponta, 3 contato da ponta (fechado sem plugue)",
     datasheet="https://atta.szlcsc.com/upload/public/pdf/source/20250630/AB61CB55FE842E2CCBB937FDB8FB366C.pdf")
R("R303", "100k", "HP_TIPSW", "HP_DET", "F2")
R("R304", "1M", "HP_DET", "GND", "F2")
C("C308", "100nF", "HP_DET", "GND", "F2")
part("J302", "PJ-327A", "PJ-327A",
     {"2": "GND", "5": "GND", "6": "NC", "4": "MIC_J", "3": "NC"}, "F3",
     fp="%s:Jack_3.5mm_PJ-327A_SMD" % LIB, lcsc="C49284723", cls="estendida", price=0.10, status="final",
     note="IN (microfone): manga no GND, ponta = sinal com bias; anel e contato da ponta soltos (XUNPU, V3)",
     datasheet="https://atta.szlcsc.com/upload/public/pdf/source/20250630/AB61CB55FE842E2CCBB937FDB8FB366C.pdf")
R("R305", "0", "MIC_BIAS", "MIC_J", "F3", note="R8V4: 0 ohm (aprovado): bias total = 2 k internos do SGTL5000 (BIAS_RESISTOR 2k); era 2,2 k em serie (4,2 k). Mais tensao para microfones que pedem mais")
C("C309", "1uF", "MIC_J", "MIC_IN", "F3", note="acoplamento do microfone ao pino MIC (o datasheet mostra 0,1 uF; 1 uF baixa o corte da voz)")
R("R306", "100k", "MIC_J", "MIC_DET", "F3", note="R6V4: toma de CC da ponta do IN para o ADC (pino 25): distingue microfone de eletreto de plugue de linha/sem plugue")
C("C311", "100nF", "MIC_DET", "GND", "F3", note="R6V4: filtro da toma MIC_DET (RC 10 ms; o ADC lê devagar)")
C("C310", "100nF", "MIC_BIAS", "GND", "F3", dnp=True, note="R10V4: NAO MONTAR. Datasheet SGTL5000 Fig. 20 poe 0,1 uF no MIC_BIAS (C4) COM o R1 de 2,2 k em serie; com R305 = 0 ohm o C310 fica na ponta do jack e forma um passa-baixas com os 2 k do bias (~800 Hz, -14 dB a 4 kHz). Pad mantido para um 220-470 pF opcional se a bancada mostrar ruido do bias")

# ---------------------------------------------------------------- I: interface
CUR[0] = "I"
# SPEC v2.1: the same encoder on both. The 15/15 with switch (EC11E1534408, C278348) has no
# stock at LCSC (24/10/2026): EC11E18244A5 (18 pulses / 36 detents, push switch, C255515, 570 in stock).
for ref, code, a, b, sw, what in (("SW401", "I1", "VOL_A", "VOL_B", "VOL_SW_N", "volume; clique de 2 s liga/desliga"),
                                  ("SW402", "I2", "SEL_A", "SEL_B", "SEL_SW", "seletor; clique = funcoes de som")):
    part(ref, sym("RotaryEncoder_Switch_MP", "Device"), "EC11E18244AU",
         {"A": a, "B": b, "C": "GND", "S1": "GND", "S2": sw, "MP": "GND"}, code,
         fp="Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm", lcsc="C202365", cls="estendida", price=1.92,
         status="final", mount="sem peca (encoder soldado em casa, topo)", note=what + "; eixo de 20 mm (o knob chapeu tem 7 mm); 18 pulsos / 36 detentes: ENC_STEPS_PER_DETENT = 2",
         datasheet="https://datasheet.lcsc.com/datasheet/pdf/00ace576d31da40a390056171db2037f.pdf?productCode=C202365")
part("J401", sym("Conn_01x04_MountingPin", "Connector_Generic_MountingPin"), "XY-SM04B-SRSS-TB",
     {"1": "GND", "2": "+3V3", "3": "I2C_SDA", "4": "I2C_SCL", "MP": "GND"}, "I3",
     fp="Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal", lcsc="C51940130", cls="estendida",
     price=0.039, status="conferir",
     note="R11V4: tela OLED Adafruit 326 (0,96 pol., SSD1306, 128 x 64, STEMMA QT) por um cabo Qwiic / STEMMA QT de estoque (SH de 4 vias nas duas pontas, pino a pino): "
          "ordem Qwiic 1 GND, 2 +3V3, 3 SDA, 4 SCL. Era um SH de 6 vias (o mesmo das reguas, ordem 1 +3V3) que obrigava a um cabo 6-4 sob medida; "
          "o tipo Extended a mais custa US$ 3,09 por pedido e economiza o cabo sob medida. Clone XY-SM04B-SRSS-TB (C51940130, 17958 em estoque); original JST C160404",
     datasheet="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf")
part("SW403", sym("SW_Push", "Switch"), "Program", {"1": "PROG", "2": "GND"}, "I4",
     fp="Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", lcsc="C318884", cls="basica", price=0.02,
     status="conferir", note="no verso, por um furo no fundo; 5,1 x 5,1 (a SPEC pedia 4 x 4)", rot=0)

# ---------------------------------------------------------------- A: speaker
CUR[0] = "A"
part("U501", sym("MAX98357A", "Audio"), "MAX98357AETE+T",
     {"1": "I2S_TX", "2": "NC", "3": "GND", "4": "AMP_SDM", "5": "NC", "6": "NC", "7": "VSYS", "8": "VSYS",
      "9": "SPK_P", "10": "SPK_N", "11": "GND", "12": "NC", "13": "NC", "14": "I2S_LRCLK", "15": "GND",
      "16": "I2S_BCLK", "17": "GND"}, "A1", fp="Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm",
     lcsc="C910544", cls="estendida", price=1.40, status="final",
     note="GAIN_SLOT aberto = 9 dB; mono (L+R)/2 pelo divisor do SD_MODE",
     datasheet="https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf")
R("R501", "1M", "AMP_SD", "AMP_SDM", "A1",
  note="com os 100k internos: 0,30 V no SD_MODE (janela mono 0,16-0,77 V); pino baixo = desligado")
C("C501", "10uF", "VSYS", "GND", "A1", "0805")
C("C502", "100nF", "VSYS", "GND", "A1")
part("J501", sym("Conn_01x02", "Connector_Generic"), "alto-falante (fios)", {"1": "SPK_P", "2": "SPK_N"}, "A2",
     fp="Connector_Wire:SolderWire-0.127sqmm_1x02_P3.7mm_D0.48mm_OD1mm", lcsc="", cls="-", price=0.0,
     mount="sem peca (pads; fios do A2 soldados em casa)", status="conferir")

def netlist_of(root, out):
    """{ref: {pin: net}} of a schematic, by kicad-cli."""
    os.makedirs(BUILD, exist_ok=True)
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, root],
                   check=True, capture_output=True)
    tree = S.parse(open(out, encoding="utf-8").read())
    got = {}
    for n in S.find(S.first(tree, "nets"), "net"):
        name = S.first(n, "name")[1].lstrip("/")
        for x in S.find(n, "node"):
            got.setdefault(S.first(x, "ref")[1], {})[S.first(x, "pin")[1]] = name
    return got


V3 = netlist_of(V3_SCH, os.path.join(BUILD, "v3_netlist.net"))

# ---------------------------------------------------------------- R: row connectors (rulers hang from them)
CUR[0] = "R"
sym("Conn_01x06_MountingPin", "Connector_Generic_MountingPin")
for k in range(1, 5):
    part("J60%d" % k, "Conn_01x06_MountingPin", "XY-SM06B-SRSS-TB",
         {"1": "+3V3", "2": "GND", "3": "OUT_R%d" % k, "4": "GND", "5": "SCAN_CLK", "6": "SCAN_DATA", "MP": "GND"}, "R%d" % k,
         fp="Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal", lcsc="C56123098", cls="estendida",
         price=0.069, status="conferir",
         note="fileira %d (%s): cabo SH de 6 vias (JST A06SR06SR30K51B, reto) ate a primeira regua; R8V4 pinagem P6s: 1 +3V3, 2 GND, 3 OUT, 4 GND, 5 CLK, 6 DATA (SER da 1a regua)"
              % (k, "a da frente" if k == 1 else "a de tras" if k == 4 else "intermediaria"),
         datasheet="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf")
    R("R60%d" % k, "100k", "OUT_R%d" % k, "GND", "R%d" % k, note="pull-down da linha OUT da fileira (datasheet do TMAG5253)")
R("R605", "330", "SCAN_CLK_P", "SCAN_CLK", "R5", note="R8V4: 330 ohm (era 100; limita a 10 mA o pior caso de cabo errado); serie no CLK comum, junto do J101 (as 4 fileiras em paralelo)")
R("R606", "330", "SCAN_DATA_P", "SCAN_DATA", "R5", note="R8V4: 330 ohm; serie no DATA comum, junto do J101")


# ====================================================================== layout + writer
def fmt(v):
    v = round(v, 3)
    return ("%.3f" % v).rstrip("0").rstrip(".") if v != int(v) else str(int(v))


def rot_vec(a, b, rot):
    for _ in range((rot // 90) % 4):
        a, b = b, -a
    return a, b


DIR_ANGLE = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}
LABEL_H = 2.6


def label_len(name):
    return len(name) * 1.05 + 3.5


def unit_pins(p, unit):
    t = pin_table(p["sym"])
    return t.get(0, []) + t.get(unit, [])


def units_of(p):
    t = pin_table(p["sym"])
    us = sorted(u for u in t if u != 0)
    return us or [1]


def item_geometry(p, unit):
    """Pin endpoints (relative to origin, screen coords), label boxes, bbox."""
    pins = []
    for num, name, etype, x, y, ang in unit_pins(p, unit):
        cx, cy = rot_vec(x, -y, p["rot"])
        lx, ly = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[ang]
        dx, dy = rot_vec(-lx, ly, p["rot"])      # outward, screen
        pins.append((num, name, etype, cx, cy, (round(dx), round(dy))))
    xs = [q[3] for q in pins] or [0]
    ys = [q[4] for q in pins] or [0]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if x1 - x0 < 5:
        x0, x1 = x0 - 2.54, x1 + 2.54
    body = (x0, y0 - 2.54, x1, y1 + 2.54)
    bx0, by0, bx1, by1 = body
    for num, name, etype, cx, cy, (dx, dy) in pins:
        net = p["nets"].get(num, "NC")
        L = 2.54 + (0 if net == "NC" else label_len(net))
        ex, ey = cx + dx * L, cy + dy * L
        bx0, bx1 = min(bx0, ex, cx - LABEL_H / 2 * abs(dy)), max(bx1, ex, cx + LABEL_H / 2 * abs(dy))
        by0, by1 = min(by0, ey, cy - LABEL_H / 2 * abs(dx)), max(by1, ey, cy + LABEL_H / 2 * abs(dx))
    return pins, body, (bx0 - 1.27, by0 - 5.0, bx1 + 1.27, by1 + 3.0)


PAPERS = [("A4", 297, 210), ("A3", 420, 297), ("A2", 594, 420), ("A1", 841, 594), ("A0", 1189, 841)]


def pack(items, top=40.0):
    for paper, W, H in PAPERS:
        x, y, rowh, pos, ok = 15.0, top, 0.0, [], True
        for (bx0, by0, bx1, by1) in items:
            w, h = bx1 - bx0, by1 - by0
            if x + w > W - 15:
                x, y, rowh = 15.0, y + rowh + 2.54, 0.0
            if y + h > H - 40 or w > W - 30:
                ok = False
                break
            pos.append((x - bx0, y - by0))
            x += w + 2.54
            rowh = max(rowh, h)
        if ok:
            return paper, pos
    raise SystemExit("sheet too big")


def snap(v):
    return round(round(v / 2.54) * 2.54, 3)


def eff(justify=None, hide=False, size=1.27):
    e = '(effects (font (size %s %s))%s)' % (fmt(size), fmt(size), ' (justify %s)' % justify if justify else "")
    return ("(hide yes) " if hide else "") + e


def lib_symbols_block(names):
    out = []
    for n in sorted(names):
        s = _copy(SYMBOLS[n])
        s[1] = S.Q(LIB + ":" + n)
        out.append(S.dump(s, 1))
    return "\t(lib_symbols\n\t\t" + "\n\t\t".join(out) + "\n\t)\n"


ROOT_UUID = uid("root")
SHEET_UUID = {s: uid("sheet", s) for s, _ in SHEETS}
NOTES = {
    "P": ["P · Processador: modulo SparkFun MicroMod Teensy (DEV-16402) no conector M.2 Key E J101 + espacador H101.",
          "3,3 V nos pads 2/74; USB_VIN (9) no VBUS; D+/D- (3/5) do USB-C pelo U201; BOOT (11) no Program; RESET# (6) = ONOFF.",
          "Sinais nos pinos do Teensy MicroMod (PINOS.md): os mesmos numeros do Viaggio v2.1, e o pad 4 (3.3V_EN = pino 28) sem ligacao (V3)."],
    "E": ["E · Energia: USB-C -> BQ24074 (USB500, 500 mA, NTC) -> VSYS -> TPS63001 (3,3 V).",
          "EN do TPS63001 = EN_REQ = clique do volume OU KEEP (pino 10) OU USB presente (D206).",
          "Sem a cadeia PWR_EN (V3, 19 nov): com cabo a firmware dorme, nao corta o 3,3 V. A tela mostra a carga."],
    "F": ["F · Fone: SGTL5000 como a Audio Board Rev D2. HP_VGND e terra virtual: NUNCA no GND.",
          "Contato da ponta do jack OUT -> HP_DET (plugue = 0 V). IN (J302): microfone com bias, MIC do codec; I2S_RX no pino 8."],
    "I": ["I · Interface: dois EC11E de eixo curto com clique (volume, registro), conector da tela OLED (J401, I2C), botao Program. Sem LED.",
          "O clique do volume (I1) liga/desliga (circuito na folha E); o do seletor (I2) e uma entrada comum (pino 6)."],
    "A": ["A · Alto-falante: MAX98357A no mesmo I2S do codec, mono (L+R)/2; SD_MODE pelo pino 12."],
    "R": ["R · Reguas: 4 conectores SH de 6 vias (um por fileira) levam +3V3, GND, OUT_Rk, CLK e DATA aos 74HC595 + 4 TMAG5253 de cada regua.",
          "OUT_Rk: pull-down de 100 k na placa principal; CLK e DATA comuns as 4 fileiras, por 330 ohm (R8V4, pinagem P6s). Sem sensores nem multiplexadores aqui."],
}


def write_sheet(sheet, title, parts, extra=None):
    """Write one sector sheet. Returns {net: [(ref, pin)]}, page size."""
    items, geo = [], []
    for p in parts:
        for u in units_of(p):
            pins, body, bbox = item_geometry(p, u)
            items.append(bbox)
            geo.append((p, u, pins, body))
    paper, pos = pack(items)
    body_txt, nets, used = [], {}, set()
    for (p, u, pins, body), (ox, oy) in zip(geo, pos):
        ox, oy = snap(ox), snap(oy)
        used.add(p["sym"])
        path = "/%s/%s" % (ROOT_UUID, SHEET_UUID[sheet])
        su = uid("sym", p["ref"], u)
        fields = [("Reference", p["ref"], ox + body[0], oy + body[1] - 1.27, "left", False),
                  ("Value", p["value"], ox + body[0], oy + body[3] + 1.27, "left", False),
                  ("Footprint", p["fp"], ox, oy, None, True),
                  ("Datasheet", p["datasheet"], ox, oy, None, True),
                  ("Description", p["note"], ox, oy, None, True),
                  ("Codigo", p["code"], ox + body[2], oy + body[1] - 1.27, "right", False),
                  ("LCSC", p["lcsc"], ox, oy, None, True),
                  ("Montagem", p["mount"], ox, oy, None, True)]
        t = ['\t(symbol (lib_id "%s:%s") (at %s %s %d) (unit %d) (exclude_from_sim no) (in_bom %s) (on_board yes) '
             '(dnp %s) (uuid "%s")' % (LIB, p["sym"], fmt(ox), fmt(oy), p["rot"], u,
                                         "no" if p["mount"].startswith("sem peca") else "yes",
                                         "yes" if p["dnp"] else "no", su)]
        for k, v, x, y, just, hide in fields:
            t.append('\t\t(property %s %s (at %s %s 0) %s)' % (S.quote(k), S.quote(v), fmt(x), fmt(y),
                                                               eff(just, hide)))
        for num, name, etype, cx, cy, d in pins:
            t.append('\t\t(pin %s (uuid "%s"))' % (S.quote(num), uid("pin", p["ref"], num)))
        t.append('\t\t(instances (project "%s" (path "%s" (reference "%s") (unit %d))))\n\t)' %
                 (PROJECT, path, p["ref"], u))
        body_txt.append("\n".join(t))
        for num, name, etype, cx, cy, (dx, dy) in pins:
            net = p["nets"].get(num)
            if net is None:
                if not p["nc_rest"]:
                    raise SystemExit("%s pin %s (%s) has no net" % (p["ref"], num, name))
                net = "NC"
            px, py = ox + cx, oy + cy
            if net == "NC":
                body_txt.append('\t(no_connect (at %s %s) (uuid "%s"))' % (fmt(px), fmt(py), uid("nc", p["ref"], num)))
                continue
            nets.setdefault(net, []).append((p["ref"], num, etype))
            ex, ey = px + dx * 2.54, py + dy * 2.54
            body_txt.append('\t(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))' %
                            (fmt(px), fmt(py), fmt(ex), fmt(ey), uid("w", p["ref"], num)))
            ang = DIR_ANGLE[(dx, dy)]
            just = "left" if ang in (0, 90) else "right"
            body_txt.append('\t(global_label %s (shape passive) (at %s %s %d) (fields_autoplaced yes) %s '
                            '(uuid "%s") (property "Intersheetrefs" "${INTERSHEET_REFS}" (at %s %s 0) %s))' %
                            (S.quote(net), fmt(ex), fmt(ey), ang, eff(just), uid("gl", p["ref"], num),
                             fmt(ex), fmt(ey), eff(just, True)))
    notes = "\n".join('\t(text %s (exclude_from_sim no) (at 15 %s 0) %s (uuid "%s"))' %
                      (S.quote(line), fmt(18 + 5 * i), eff("left", size=2.0), uid("note", sheet, i))
                      for i, line in enumerate(NOTES[sheet] + (extra or [])))
    tb = ('\t(title_block (title %s) (date "%s") (rev %s) (company "beatconfused.com") '
          '(comment 1 "etutti/hardware/student_v04/pcb/schematic.py escreve este arquivo; nao editar a mao"))' %
          (S.quote("eTutti Student V4 · %s · %s" % (sheet, title)), DATE, S.quote(REV)))
    txt = ('(kicad_sch\n\t(version 20250610)\n\t(generator "student_v04_schematic")\n\t(generator_version "10.0")\n'
           '\t(uuid "%s")\n\t(paper "%s")\n%s\n' % (SHEET_UUID[sheet], paper, tb))
    txt += lib_symbols_block(used) + notes + "\n" + "\n".join(body_txt) + "\n\t(embedded_fonts no)\n)\n"
    open(os.path.join(KDIR, "%s_%s.kicad_sch" % (PROJECT, sheet)), "w", encoding="utf-8", newline="\n").write(txt)
    return nets, paper


def write_root(flags, root_notes=None):
    sheets = []
    for i, (s, title) in enumerate(SHEETS):
        x, y = 25 + (i % 3) * 85, 45 + (i // 3) * 45
        sheets.append(
            '\t(sheet (at %s %s) (size 70 25) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) '
            '(fields_autoplaced yes) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000)) (uuid "%s")\n'
            '\t\t(property "Sheetname" %s (at %s %s 0) %s)\n'
            '\t\t(property "Sheetfile" "%s_%s.kicad_sch" (at %s %s 0) %s)\n'
            '\t\t(instances (project "%s" (path "/%s" (page "%d"))))\n\t)' %
            (x, y, SHEET_UUID[s], S.quote("%s · %s" % (s, title)), x, fmt(y - 0.7), eff("left bottom"),
             PROJECT, s, x, fmt(y + 25.6), eff("left top"), PROJECT, ROOT_UUID, i + 2))
    body = []
    for i, net in enumerate(flags):
        x, y = snap(25 + (i % 6) * 42), snap(150 + (i // 6) * 15)
        ref = "#FLG%02d" % (i + 1)
        body.append('\t(symbol (lib_id "%s:PWR_FLAG") (at %s %s 0) (unit 1) (exclude_from_sim no) (in_bom yes) '
                    '(on_board yes) (dnp no) (uuid "%s")\n'
                    '\t\t(property "Reference" "%s" (at %s %s 0) %s)\n'
                    '\t\t(property "Value" "PWR_FLAG" (at %s %s 0) %s)\n'
                    '\t\t(property "Footprint" "" (at %s %s 0) %s)\n'
                    '\t\t(property "Datasheet" "" (at %s %s 0) %s)\n'
                    '\t\t(pin "1" (uuid "%s"))\n'
                    '\t\t(instances (project "%s" (path "/%s" (reference "%s") (unit 1))))\n\t)' %
                    (LIB, fmt(x), fmt(y), uid("flag", net), ref, fmt(x), fmt(y - 5), eff(hide=True), fmt(x),
                     fmt(y - 3.5), eff(), fmt(x), fmt(y), eff(hide=True), fmt(x), fmt(y), eff(hide=True),
                     uid("flagpin", net), PROJECT, ROOT_UUID, ref))
        body.append('\t(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))' %
                    (fmt(x), fmt(y), fmt(x), fmt(y + 2.54), uid("flagw", net)))
        body.append('\t(global_label %s (shape passive) (at %s %s 270) (fields_autoplaced yes) %s (uuid "%s") '
                    '(property "Intersheetrefs" "${INTERSHEET_REFS}" (at %s %s 0) %s))' %
                    (S.quote(net), fmt(x), fmt(y + 2.54), eff("right"), uid("flagl", net), fmt(x), fmt(y + 2.54),
                     eff("right", True)))
    notes = root_notes or [
        "eTutti Student V4 · placa principal (so interface), R3V4. E a V3 sem sensores nem multiplexadores.",
        "Folhas P, E, F, I, A: o circuito da V3. Folha R: os 4 conectores de fileira (SH 6 vias), pull-downs e series de CLK/DATA.",
        "Placa: pcb/posiciona_v4.py (posicionamento sem trilhas, portao P). Ligacoes entre folhas por rotulos globais.",
        "PWR_FLAG abaixo: redes alimentadas por conector, ferrite, indutor ou diodo (o ERC nao ve a fonte).",
    ]
    ntxt = "\n".join('\t(text %s (exclude_from_sim no) (at 25 %s 0) %s (uuid "%s"))' %
                     (S.quote(line), fmt(15 + 6 * i), eff("left", size=2.0), uid("rootnote", i))
                     for i, line in enumerate(notes))
    tb = ('\t(title_block (title "eTutti Student V4 · esquema") (date "%s") (rev %s) (company "beatconfused.com") '
          '(comment 1 "etutti/hardware/student_v04/pcb/schematic.py escreve este arquivo; nao editar a mao"))' %
          (DATE, S.quote(REV)))
    txt = ('(kicad_sch\n\t(version 20250610)\n\t(generator "student_v04_schematic")\n\t(generator_version "10.0")\n'
           '\t(uuid "%s")\n\t(paper "A4")\n%s\n' % (ROOT_UUID, tb))
    txt += lib_symbols_block({"PWR_FLAG"}) + ntxt + "\n" + "\n".join(sheets + body)
    txt += '\n\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n'
    open(os.path.join(KDIR, PROJECT + ".kicad_sch"), "w", encoding="utf-8", newline="\n").write(txt)


def write_library():
    syms = "\n\t".join(S.dump(SYMBOLS[n], 1) for n in sorted(SYMBOLS))
    open(os.path.join(KDIR, LIB + ".kicad_sym"), "w", encoding="utf-8", newline="\n").write(
        '(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "student_v04_schematic")\n\t(generator_version "10.0")\n\t'
        + syms + "\n)\n")
    open(os.path.join(KDIR, "sym-lib-table"), "w", newline="\n").write(
        '(sym_lib_table\n\t(version 7)\n\t(lib (name "%s") (type "KiCad") (uri "${KIPRJMOD}/%s.kicad_sym") '
        '(options "") (descr "eTutti Viaggio MicroMod, written by schematic.py"))\n)\n' % (LIB, LIB))
    open(os.path.join(KDIR, "fp-lib-table"), "w", newline="\n").write(
        '(fp_lib_table\n\t(version 7)\n\t(lib (name "%s") (type "KiCad") (uri "${KIPRJMOD}/%s.pretty") '
        '(options "") (descr "eTutti Viaggio MicroMod footprints, written by footprints.py"))\n)\n' % (LIB, LIB))
    pro = os.path.join(KDIR, PROJECT + ".kicad_pro")
    if not os.path.exists(pro):
        json.dump({"meta": {"filename": PROJECT + ".kicad_pro", "version": 3},
                   "sheets": [[ROOT_UUID, "Root"]] + [[SHEET_UUID[s], "%s · %s" % (s, t)] for s, t in SHEETS]},
                  open(pro, "w"), indent=2)


def check_footprints():
    missing = []
    for s in PARTS:
        for p in PARTS[s]:
            if not p["fp"]:
                missing.append((p["ref"], "(sem footprint)"))
            else:
                lib, name = p["fp"].split(":")
                root = os.path.join(KDIR, LIB + ".pretty") if lib == LIB else os.path.join(KICAD_FP, lib + ".pretty")
                if not os.path.exists(os.path.join(root, name + ".kicad_mod")):
                    missing.append((p["ref"], p["fp"]))
    if missing:
        raise SystemExit("footprints not found: %s" % missing)


# Lines with no schematic symbol (bought apart, fitted at home).
BOM_EXTRA = [
    ["I3", "DS1", 1, "Adafruit 326: OLED 0,96 pol. monocromatico 128 x 64, SSD1306, 2 conectores STEMMA QT (SH 4 vias), regulador de bordo AP2112K-3.3", "29,2 x 26,7 mm (+ orelhas, 31,75 de comprimento) (conferir)", "-", "-", "17.500",
     "em casa (preso na tampa; cabo Qwiic ao J401)", "conferir", "R11V4: 4 furos; endereco I2C 0x3D de fabrica (0x3C por jumper); US$ 17,50 (1-9), 15,75 (10-99)"],
    ["I3", "CAB1", 1, "cabo Qwiic / STEMMA QT (SH 1,0 mm, 4 vias, pino a pino), 50 mm (Adafruit 4210 ou SparkFun)", "-", "-", "-", "1.000", "em casa", "final", ""],
    ["P1", "MOD1", 1, "SparkFun MicroMod Teensy Processor (DEV-16402)", "M.2 2222 Key E", "-", "-", "24.950",
     "em casa (encaixar no J101, apertar o parafuso)", "final",
     "i.MX RT1062 600 MHz, 16 MB flash, 1 MB RAM, bootloader MKL02; fqbn teensy:avr:teensyMM"],
    ["P1", "SCR1", 1, "parafuso M2.5 x 3, cabeca chata (Phillips)", "-", "-", "-", "0.050", "em casa", "conferir",
     "prende o modulo no espacador H101 (vem no KIT-16549 da SparkFun)"],
]


def write_bom():
    rows = {}
    for s, _ in SHEETS:
        for p in PARTS[s]:
            key = (p["code"], p["value"], p["fp"], p["lcsc"], p["mount"])
            r = rows.setdefault(key, dict(p, refs=[]))
            r["refs"].append(p["ref"])
    path = os.path.join(HERE, "bom_esquema.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "referencias", "qtd", "valor_peca", "encapsulamento", "lcsc", "classe_jlc",
                    "preco_unit_usd_est", "montagem", "status", "nota"])
        for row in BOM_EXTRA:
            w.writerow(row)
        for key in sorted(rows, key=lambda k: ("PEFIAR".index(k[0][0]), int(k[0][1:]) if k[0][1:].isdigit() else 0,
                                              k[1])):
            r = rows[key]
            fp = r["fp"].split(":")[-1] if r["fp"] else "(a criar)"
            w.writerow([r["code"], " ".join(sorted(r["refs"], key=lambda x: (re.sub(r"\d", "", x),
                                                                              int(re.sub(r"\D", "", x))))),
                        len(r["refs"]), r["value"], fp, r["lcsc"] or "-", r["cls"] or "-",
                        "" if r["price"] is None else "%.3f" % r["price"], r["mount"], r["status"], r["note"]])
    return path


def run_checks(declared):
    os.makedirs(BUILD, exist_ok=True)
    root = os.path.join(KDIR, PROJECT + ".kicad_sch")
    erc = os.path.join(BUILD, PROJECT + "_erc.json")
    subprocess.run([KICAD_CLI, "sch", "erc", "--format", "json", "--severity-all", "-o", erc, root],
                   check=False, capture_output=True)
    rep = json.load(open(erc, encoding="utf-8"))
    counts = {}
    for sh in rep.get("sheets", []):
        for v in sh.get("violations", []):
            counts.setdefault(v["severity"], []).append((sh.get("path"), v["type"], v["description"],
                                                         [i.get("description") for i in v.get("items", [])]))
    net = os.path.join(BUILD, PROJECT + "_netlist.net")
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net, root],
                   check=True, capture_output=True)
    tree = S.parse(open(net, encoding="utf-8").read())
    got = {}
    for n in S.find(S.first(tree, "nets"), "net"):
        name = S.first(n, "name")[1].lstrip("/")
        nodes = {(S.first(x, "ref")[1], S.first(x, "pin")[1]) for x in S.find(n, "node")}
        got[name] = nodes
    bad = []
    for name, nodes in declared.items():
        want = {(r, p) for r, p, _ in nodes}
        have = {x for x in got.get(name, set()) if not x[0].startswith("#")}
        if want != have:
            bad.append((name, sorted(want - have)[:4], sorted(have - want)[:4]))
    for name, nodes in got.items():
        real = {x for x in nodes if not x[0].startswith("#")}
        if name not in declared and len(real) > 1:
            bad.append((name, [], sorted(real)[:4]))
    return counts, bad


def compare_v3():
    """Every part kept from the V3 has the same pins on the same nets; only the listed R3V4 changes differ."""
    mine = netlist_of(os.path.join(KDIR, PROJECT + ".kicad_sch"), os.path.join(BUILD, PROJECT + "_netlist.net"))
    gone = {"U601", "U602", "U603", "U604", "U605", "C601", "C602", "C603"} | {"U7%02d" % n for n in range(1, 29)} |         {"C7%02d" % n for n in range(1, 29)}
    new = {"J601", "J602", "J603", "J604", "R601", "R602", "R603", "R604", "R605", "R606", "C310", "R306", "C311"}
    # Teensy pads 19 (CHG_STAT), 10/18/32/47/34/38/8/67 etc. change by design (PINOS.md); J401 5 and 6 are new pins
    allowed = {("J101", p) for p in ("19", "10", "32", "47", "34", "38", "8", "67", "17", "18", "28", "4", "9", "51")}
    allowed |= {("D202", "1"), ("J401", "1"), ("J401", "2"), ("J401", "3"), ("J401", "4")}

    def nc(n):
        return n is None or n.startswith("unconnected-")

    diff = []
    for ref in sorted(set(V3) | set(mine)):
        if ref.startswith("#"):
            continue
        a, b = V3.get(ref), mine.get(ref)
        if a is None:
            if ref not in new:
                diff.append((ref, "so na V4"))
        elif b is None:
            if ref not in gone:
                diff.append((ref, "so na V3"))
        else:
            for pin in sorted(set(a) | set(b)):
                na, nb = a.get(pin), b.get(pin)
                if na == nb or (nc(na) and nc(nb)) or (ref, pin) in allowed:
                    continue
                diff.append((ref, pin, na, nb))
    return diff


def main():
    os.makedirs(KDIR, exist_ok=True)
    fps, nballs = footprints.write_all()
    print("footprints: %s (M.2 %d pads)" % (", ".join(fps), nballs))
    check_footprints()
    sym("PWR_FLAG", "power")
    declared = {}
    pages = {}
    for s, title in SHEETS:
        nets, paper = write_sheet(s, title, PARTS[s])
        pages[s] = paper
        for k, v in nets.items():
            declared.setdefault(k, []).extend(v)
    for net, nodes in declared.items():
        if len(nodes) < 2:
            raise SystemExit("net %s has a single pin: %s" % (net, nodes))
    flags = sorted(n for n, nodes in declared.items()
                   if any(t == "power_in" for _, _, t in nodes) and not any(t == "power_out" for _, _, t in nodes))
    write_root(flags)
    write_library()
    bom = write_bom()
    dump = []
    for s_, _ in SHEETS:
        for p in PARTS[s_]:
            q = {k: p[k] for k in ("ref", "value", "nets", "code", "fp", "lcsc", "cls", "mount", "note", "dnp", "sheet", "price", "datasheet")}
            q["path"] = "/%s/%s/%s" % (ROOT_UUID, SHEET_UUID[s_], uid("sym", p["ref"], 1))
            dump.append(q)
    json.dump(dump, open(os.path.join(BUILD, "partes_v4.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    counts, bad = run_checks(declared)
    diff = compare_v3()
    nparts = sum(len(v) for v in PARTS.values())
    print("sheets: %s" % ", ".join("%s %s (%d parts)" % (s, pages[s], len(PARTS[s])) for s, _ in SHEETS))
    print("parts %d, nets %d, PWR_FLAG on %s" % (nparts, len(declared), ", ".join(flags)))
    print("BOM -> %s" % os.path.relpath(bom, HERE))
    for sev in ("error", "warning", "exclusion"):
        items = counts.get(sev, [])
        print("ERC %s: %d" % (sev, len(items)))
        for it in items[:25]:
            print("   ", it)
    print("netlist vs declared: %s" % ("OK" if not bad else bad[:10]))
    print("vs Student V3 (fora das mudancas listadas): %s" % ("igual" if not diff else diff[:12]))
    sys.exit(1 if counts.get("error") or bad or diff else 0)


if __name__ == "__main__":
    main()
