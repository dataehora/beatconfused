"""Write the eTutti Viaggio MicroMod schematic (SPEC v2.2, step M1), run ERC, check it.

    python etutti/hardware/viaggio_micromod/pcb/schematic.py

Plain CPython (stdlib only); it calls KiCad 10's kicad-cli for ERC and for
the netlist that is checked back against the nets declared here.

The circuit is data: one PARTS list per sector sheet (P, E, F, I, A, T).
Every part carries its SPEC section 3 code (P1 ... T4) in the "Codigo"
field, so the board step (M2) can match parts to concept/out/
viaggio_micromod.json. Nothing is placed or routed here.

Copied from the Viaggio v2.1 (etutti/hardware/viaggio/pcb/schematic.py, now
archived). What changed: the chip-down RT1062 block (RT1062, MKL02, flash,
PSRAM, crystals, DCDC parts) and E5 are gone; P1 is an M.2 Key E socket for
the SparkFun MicroMod Teensy (DEV-16402) plus its M2.5 standoff.

Sources:
  P          SparkFun MicroMod Teensy schematic (github.com/sparkfun/
             MicroMod_Teensy_Processor, Hardware/MicroMod-Teensy.sch, read
             net by net: connector J1 pad -> RT1062 ball -> Teensy pin), the
             MicroMod Teensy hookup guide and "Designing with MicroMod"
             (learn.sparkfun.com); M.2 socket = UMAX 91302-42-067RCE, drawing C-91302-42
             rev C (same land as TE 2199230-4 rev B3).
  F          PJRC Audio Adaptor Rev D2 (20-pin SGTL5000), as used by the Pocket.
  E, I, A, T the eTuttino Pocket (pocket/pcb/build_pocket_pcb.py, PINOS.md)
             and the Viaggio v2.1.

Writes (under etutti/hardware/viaggio_micromod/pcb/):
  kicad/viaggio_micromod.kicad_pro, viaggio_micromod.kicad_sch (root)
      + viaggio_micromod_<S>.kicad_sch
  kicad/viaggio_micromod.kicad_sym + sym-lib-table + fp-lib-table
  kicad/viaggio_micromod.pretty/ (footprints.py)
  build/viaggio_micromod_erc.json, build/viaggio_micromod_netlist.net
  bom_preliminar.csv
Exits non-zero on an ERC error or a netlist mismatch.
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
KDIR = os.path.join(HERE, "kicad")
BUILD = os.path.join(HERE, "build")
PROJECT = "viaggio_micromod"
LIB = "viaggio_micromod"
DATE = "2026-10-25"
REV = "SPEC v2.2 - passo M1"

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
    return box_symbol("PJ-327A", "J", [([("1", "S", "passive"), ("2", "S", "passive")],
                                        [("4", "T", "passive"), ("5", "TN", "passive"), ("3", "R", "passive")])],
                      "3.5 mm stereo jack, tip switch (5 NC against 4)")


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
                                            [("4", "OUT", "output"), ("2", "GND", "power_in"),
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
        if m.group(2) != "1" and unit != 0:   # De Morgan alternates
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
    ("C", "150nF", "0402"): ("", "estendida", 0.003, "conferir"),
    ("C", "1uF", "0402"): ("C52923", "basica", 0.002, "final"),
    ("C", "2.2uF", "0402"): ("C12530", "basica", 0.003, "conferir"),
    ("C", "4.7uF", "0603"): ("C19666", "basica", 0.004, "final"),
    ("C", "4.7uF", "0402"): ("C23733", "basica", 0.003, "conferir"),
    ("C", "10uF", "0402"): ("C15525", "basica", 0.004, "conferir"),
    ("C", "10uF", "0603"): ("C19702", "basica", 0.005, "final"),
    ("C", "10uF", "0805"): ("C15850", "basica", 0.008, "final"),
    ("C", "12pF", "0402"): ("C1547", "basica", 0.001, "conferir"),
    ("C", "20pF", "0402"): ("C1554", "basica", 0.001, "conferir"),
    ("R", "100", "0402"): ("C25076", "basica", 0.001, "final"),
    ("R", "270", "0402"): ("C25190", "basica", 0.001, "conferir"),
    ("R", "330", "0402"): ("C25104", "basica", 0.001, "conferir"),
    ("R", "470", "0402"): ("C25117", "basica", 0.001, "conferir"),
    ("R", "1k", "0402"): ("C11702", "basica", 0.001, "final"),
    ("R", "1.5k", "0402"): ("C25867", "basica", 0.001, "conferir"),
    ("R", "1.8k", "0402"): ("C25811", "basica", 0.001, "conferir"),
    ("R", "2.2k", "0402"): ("C25879", "basica", 0.001, "conferir"),
    ("R", "5.1k", "0402"): ("C25905", "basica", 0.001, "final"),
    ("R", "10k", "0402"): ("C25744", "basica", 0.001, "final"),
    ("R", "100k", "0402"): ("C25741", "basica", 0.001, "final"),
    ("R", "680k", "0402"): ("", "estendida", 0.002, "conferir"),
    ("R", "1M", "0402"): ("C26083", "basica", 0.001, "final"),
    ("R", "2.2M", "0402"): ("", "estendida", 0.002, "conferir"),
}

SHEETS = [("P", "Processador"), ("E", "Energia"), ("F", "Fone"), ("I", "Interface"),
          ("A", "Alto-falante"), ("T", "Teclas")]
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
    part(ref, sym("BAT54C", "Diode"), "BAT54C", {"1": a1, "2": a2, "3": k}, code, fp=FP["SOT23"],
         lcsc="C134405", cls="estendida", price=0.02, status="final", note=note,
         datasheet="https://www.diodes.com/assets/Datasheets/ds11005.pdf")


def pmos(ref, g, s, d, code, note=""):
    part(ref, sym("AO3401A", "Transistor_FET"), "AO3401A", {"1": g, "2": s, "3": d}, code, fp=FP["SOT23"],
         lcsc="C15127", cls="basica", price=0.01, status="final", note=note,
         datasheet="https://www.aosmd.com/res/datasheets/AO3401A.pdf")


def nmos(ref, g, s, d, code, note=""):
    part(ref, sym("AO3400A", "Transistor_FET"), "AO3400A", {"1": g, "2": s, "3": d}, code, fp=FP["SOT23"],
         lcsc="C20917", cls="basica", price=0.01, status="final", note=note,
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
    "0": "MUX_S0", "1": "MUX_S1", "2": "MUX_S2", "3": "MUX_S3", "4": "SENS_EN", "5": "LED_G", "6": "SEL_SW",
    "7": "I2S_TX", "9": "SEL_B", "10": "KEEP", "11": "SEL_A", "12": "AMP_SD", "13": "LED_R",
    "14/A0": "MUX_R_COM", "15/A1": "MUX_L_COM", "16/A2": "VBAT_S", "17/A3": "HP_DET", "18/A4": "I2C_SDA",
    "19/A5": "I2C_SCL", "20/A6": "I2S_LRCLK", "21/A7": "I2S_BCLK", "22/A8": "VOL_A", "23/A9": "AUD_MCLK_P",
    "24/A10": "VOL_B", "25/A11": "VOL_SW", "26/A12": "CHG_STAT", "28": "PWR_EN",
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
part("H101", sym("MountingHole_Pad", "Mechanical"), "9774025151R", {"1": "GND"}, "P1",
     fp="%s:Standoff_SMD_M2.5_H2.5" % LIB, lcsc="", cls="-", price=0.60, mount="JLC (Global Sourcing)",
     status="conferir",
     note="espacador SMD M2.5 x 2,5 mm (Wurth WA-SMSI, o da SparkFun; SPEC v2.3); a (+4,0; -20,0) do J101 "
          "nas coordenadas do footprint; sem equivalente LCSC de 2,5 mm com estoque em 25 out 2026 (YIYUAN "
          "SMTSOM2.520BTR C5301776: 2,0 mm, estoque 0); parafuso M2.5 x 3 cabeca chata em casa",
     datasheet="https://www.we-online.com/components/products/datasheet/9774025151R.pdf")
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
R("R203", "1.8k", "CHG_ISET", "GND", "E3", note="ICHG = 890/1800 = 0,49 A")
R("R204", "1.5k", "CHG_ILIM", "GND", "E3", note="so vale com EN2=1 (1,07 A); obrigatorio")
R("R205", "10k", "VBUS", "CHG_EN1", "E3")
pmos("Q201", "CHG_N", "VBUS", "CHGLED", "E3", note="luz de carga (Pocket Q30)")
R("R206", "100k", "VBUS", "CHG_N", "E3")
R("R207", "1k", "CHGLED", "CHGA", "E3")
nmos("Q202", "+3V3", "GND", "CHGA", "E3", note="ligado, a luz de carga apaga (Pocket Q31)")
bat54c("D202", "CHG_STAT", "NC", "CHG_N", "E3", note="leitura do ~CHG pelo pino 26 (so com USB)")
R("R208", "1M", "VBAT", "VBAT_S", "E3", note="medida da bateria: V(pino 16) = VBAT/2")
R("R209", "1M", "VBAT_S", "GND", "E3")
C("C204", "100nF", "VBAT_S", "GND", "E3")
# power latch (SPEC v2.2): click of I1 (volume) -> PWR_KEY, firmware KEEP, USB hold while PWR_EN is high.
# EN of E4 = EN_REQ = click OR KEEP OR (USB AND PWR_EN). PWR_EN = MicroMod 3.3V_EN (pad 4, Teensy pin 28):
# pulled up here (MicroMod rule), so it is high while the module resets or runs its bootloader; the
# firmware pulls it low to switch off with USB. R218 + C213 keep PWR_EN_S low while the 3,3 V collapses.
pmos("Q203", "VOL_SW_N", "VSYS", "PWR_KEY", "E3", note="o clique do volume liga o EN")
R("R210", "100k", "VSYS", "VOL_SW_N", "E3")
R("R211", "100k", "PWR_KEY", "GND", "E3")
bat54c("D203", "PWR_KEY", "KEEP", "EN_REQ", "E3", note="OU do clique e do KEEP")
R("R212", "1M", "EN_REQ", "GND", "E3", note="EN do TPS63001 baixo sem pedido")
R("R213", "100k", "KEEP", "GND", "E3", note="KEEP baixo enquanto o modulo parte")
gate("U203", "08", "VBUS_S", "PWR_EN_S", "USB_HOLD", "+3V3", "E3",
     note="USB_HOLD = USB presente E PWR_EN alto (alimentada pelo 3V3)")
R("R214", "10k", "VBUS", "VBUS_S", "E3")
R("R215", "100k", "VBUS_S", "GND", "E3")
C("C205", "100nF", "+3V3", "GND", "E3")
bat54c("D204", "USB_HOLD", "NC", "EN_REQ", "E3")
R("R217", "1k", "PWR_EN", "PWR_EN_S", "E3", note="pino 28 baixo descarrega o C213 em ~1 ms")
R("R218", "100k", "+3V3", "PWR_EN_S", "E3", note="pull-up do 3.3V_EN (regra MicroMod): alto em reset/bootloader")
C("C213", "1uF", "PWR_EN_S", "GND", "E3",
  note="100 ms: depois do desligamento o PWR_EN_S nao sobe antes de o 3,3 V cair (sem religar)")
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
      "8": "NC", "9": "NC", "10": "NC", "11": "NC", "12": "+3V3", "13": "AUD_MCLK", "14": "I2S_LRCLK",
      "15": "I2S_BCLK", "16": "NC", "17": "I2S_TX", "18": "I2C_SDA", "19": "I2C_SCL", "20": "SGTL_VDDD",
      "21": "GND"}, "F1", fp="Package_DFN_QFN:QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm", lcsc="C511764",
     cls="estendida", price=1.80, status="conferir",
     note="como a Audio Board Rev D2 (endereco I2C fixo 0x0A); sem entrada de linha/microfone",
     datasheet="https://www.pjrc.com/teensy/SGTL5000.pdf")
part("FB301", sym("FerriteBead_Small", "Device"), "600R@100MHz", {"1": "+3V3", "2": "SGTL_VDDA"}, "F1",
     fp=FP["0603L"], lcsc="", cls="basica", price=0.005, note="Audio Board: Ferrite 600 no VDDA", rot=90)
C("C301", "2.2uF", "SGTL_VDDA", "GND", "F1")
C("C302", "100nF", "SGTL_VDDA", "GND", "F1")
C("C303", "2.2uF", "+3V3", "GND", "F1", note="VDDIO")
C("C304", "100nF", "+3V3", "GND", "F1")
C("C305", "100nF", "+3V3", "GND", "F1")
part("U302", sym("XC6206P182MR", "Regulator_Linear", "XC6206PxxxMR"), "XC6206P182MR",
     {"1": "GND", "2": "SGTL_VDDD", "3": "+3V3"}, "F1", fp="Package_TO_SOT_SMD:SOT-23-3", lcsc="C347373",
     cls="estendida", price=0.03, status="conferir", note="1,8 V do VDDD (a Audio Board usa AP7313)")
C("C306", "2.2uF", "SGTL_VDDD", "GND", "F1")
C("C307", "150nF", "SGTL_VAG", "GND", "F1", note="Audio Board: 0,15 uF")
R("R301", "2.2k", "+3V3", "I2C_SDA", "F1")
R("R302", "2.2k", "+3V3", "I2C_SCL", "F1")
# The PJ-313D-6A of step 3.1 (C95463) turned out to have no tip switch (datasheet: 3 contacts, 6 pads).
sym("PJ-327A", "custom", jack_symbol)
part("J301", "PJ-327A", "PJ-327A 5JJ",
     {"1": "HP_VGND", "2": "HP_VGND", "3": "HP_R", "4": "HP_L", "5": "HP_TIPSW"}, "F2",
     fp="%s:Jack_3.5mm_PJ-327A_SMD" % LIB, lcsc="C668605", cls="estendida", price=0.10, status="conferir",
     note="SMD, angulo reto, SHOU HAN; 1/2 manga (HP_VGND, nunca no GND), 3 anel, 4 ponta, 5 contato da ponta (fechado sem plugue)",
     datasheet="https://www.lcsc.com/datasheet/lcsc_datasheet_2006181822_SHOU-HAN-PJ-327A-5JJ_C668605.pdf")
R("R303", "100k", "HP_TIPSW", "HP_DET", "F2")
R("R304", "1M", "HP_DET", "GND", "F2")
C("C308", "100nF", "HP_DET", "GND", "F2")

# ---------------------------------------------------------------- I: interface
CUR[0] = "I"
# SPEC v2.1: the same encoder on both. The 15/15 with switch (EC11E1534408, C278348) has no
# stock at LCSC (24/10/2026): EC11E18244A5 (18 pulses / 36 detents, push switch, C255515, 570 in stock).
for ref, code, a, b, sw, what in (("SW401", "I1", "VOL_A", "VOL_B", "VOL_SW_N", "volume; clique de 2 s liga/desliga"),
                                  ("SW402", "I2", "SEL_A", "SEL_B", "SEL_SW", "seletor; clique = funcoes de som")):
    part(ref, sym("RotaryEncoder_Switch_MP", "Device"), "EC11E18244A5",
         {"A": a, "B": b, "C": "GND", "S1": "GND", "S2": sw, "MP": "GND"}, code,
         fp="Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm", lcsc="C255515", cls="estendida", price=1.20,
         status="final", note=what + "; 18 pulsos / 36 detentes (o 15/15 nao tem estoque): ENC_STEPS_PER_DETENT = 2",
         datasheet="https://www.lcsc.com/datasheet/lcsc_datasheet_1811072201_ALPSALPINE-EC11E18244A5_C255515.pdf")
part("D401", sym("LED_RG_1615", "Device", "LED_Dual_AAKK", fix=led_pins), "TJ-S1615SW6TGLCRG-A5",
     {"1": "LED_R_A", "3": "LED_G_A", "2": "GND", "4": "GND"}, "I3", fp="%s:LED_1615_RG_4pad" % LIB, lcsc="C273605",
     cls="estendida", price=0.02, status="final",
     note="1615 vermelho/verde; pads do datasheet: 1 = anodo vermelho, 2 = catodo vermelho, 3 = anodo verde, 4 = catodo verde",
     datasheet="https://www.lcsc.com/datasheet/lcsc_datasheet_1810191024_TOGIALED-TJ-S1615SW6TGLCRG-A5_C273605.pdf")
R("R401", "270", "LED_R", "LEDR_A", "I3")
bat54c("D402", "CHGA", "LEDR_A", "LED_R_A", "I3", note="OU do vermelho: luz de carga e firmware (Pocket D30)")
R("R402", "330", "LED_G", "LED_G_A", "I3")
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
R("R501", "680k", "AMP_SD", "AMP_SDM", "A1",
  note="com os 100k internos: 0,42 V no SD_MODE = (L+R)/2; pino baixo = desligado")
C("C501", "10uF", "VSYS", "GND", "A1", "0805")
C("C502", "100nF", "VSYS", "GND", "A1")
part("J501", sym("Conn_01x02", "Connector_Generic"), "alto-falante (fios)", {"1": "SPK_P", "2": "SPK_N"}, "A2",
     fp="Connector_Wire:SolderWire-0.127sqmm_1x02_P3.7mm_D0.48mm_OD1mm", lcsc="", cls="-", price=0.0,
     mount="sem peca (pads; fios do A2 soldados em casa)", status="conferir")

# ---------------------------------------------------------------- T: keys
CUR[0] = "T"
KEYS = list(csv.DictReader(open(os.path.join(HERE, "..", "..", "pocket", "pcb", "build", "pocket_keys.csv"))))
MUX_REF = {"U52": ("U601", "T1", "MUX_L_COM"), "U51": ("U602", "T2", "MUX_R_COM")}
for pocket_ref, (ref, code, com) in MUX_REF.items():
    nets = {"1": com, "10": "MUX_S0", "11": "MUX_S1", "14": "MUX_S2", "13": "MUX_S3", "15": "GND", "12": "GND",
            "24": "+3V3"}
    chan_pin = {0: "9", 1: "8", 2: "7", 3: "6", 4: "5", 5: "4", 6: "3", 7: "2", 8: "23", 9: "22", 10: "21",
                11: "20", 12: "19", 13: "18", 14: "17", 15: "16"}
    used = {int(k["mux_channel"]): k for k in KEYS if k["mux"] == pocket_ref}
    for ch, pn in chan_pin.items():
        nets[pn] = "OUT_K%02d" % int(used[ch]["switch"][2:]) if ch in used else "NC"
    part(ref, sym("74HC4067PW", "74xx", "CD74HC4067SM"), "74HC4067PW", nets, code,
         fp="Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm", lcsc="C547038", cls="estendida", price=0.25, status="final",
         note=("esquerdo (metade baixa do teclado), COM no pino 15" if code == "T1" else
               "direito (metade alta), COM no pino 14") + "; canais = Pocket v0.3",
         datasheet="https://assets.nexperia.com/documents/data-sheet/74HC_HCT4067.pdf")
C("C601", "100nF", "+3V3", "GND", "T1")
C("C602", "100nF", "+3V3", "GND", "T2")
gate("U603", "04", "MUX_S3", None, "NS3", "+3V3", "T3")
gate("U604", "08", "NS3", "SENS_EN", "EN_A", "+3V3", "T3", note="EN_A = SENS_EN e S3 baixo (canais 0-7)")
gate("U605", "08", "MUX_S3", "SENS_EN", "EN_B", "+3V3", "T3", note="EN_B = SENS_EN e S3 alto (canais 8-15)")
C("C603", "100nF", "+3V3", "GND", "T3")
for k in sorted(KEYS, key=lambda k: int(k["switch"][2:])):
    n = int(k["switch"][2:])
    part("U7%02d" % n, "TMAG5253BA3", "TMAG5253BA3IQDMRR",
         {"1": "+3V3", "2": "GND", "3": k["en_group"], "4": "OUT_K%02d" % n, "5": "GND"}, "T4",
         fp="Package_SON:Texas_X2SON-4-1EP_1.1x1.4mm_P0.5mm_EP0.8x0.6mm", lcsc="", cls="-", price=0.45,
         mount="Global Sourcing (JLCPCB)", status="conferir",
         note="tecla %s (fileira %s, %s); verso, mesma orientacao do Pocket" % (k["switch"], k["row"], k["note"]),
         datasheet="https://www.ti.com/lit/ds/symlink/tmag5253.pdf")
    C("C7%02d" % n, "100nF", "+3V3", "GND", "T4")


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
          "Sinais nos pinos do Teensy MicroMod (PINOS.md): os mesmos numeros do Viaggio v2.1, mais o 28 (3.3V_EN = PWR_EN)."],
    "E": ["E · Energia: USB-C -> BQ24074 (USB500, 500 mA, NTC) -> VSYS -> TPS63001 (3,3 V).",
          "EN do TPS63001 = EN_REQ = clique do volume OU KEEP (pino 10) OU (USB E PWR_EN, 3.3V_EN do modulo, pino 28).",
          "PWR_EN tem pull-up (R218): alto em reset/bootloader; a firmware o baixa para desligar com USB. Luz de carga so desligado (Q202)."],
    "F": ["F · Fone: SGTL5000 como a Audio Board Rev D2. HP_VGND e terra virtual: NUNCA no GND.",
          "Contato da ponta do jack -> HP_DET (fone plugado = 0 V)."],
    "I": ["I · Interface: dois EC11E com clique (volume, seletor), LED vermelho/verde, botao Program.",
          "O clique do volume (I1) liga/desliga (circuito na folha E); o do seletor (I2) e uma entrada comum (pino 6)."],
    "A": ["A · Alto-falante: MAX98357A no mesmo I2S do codec, mono (L+R)/2; SD_MODE pelo pino 12."],
    "T": ["T · Teclas: 28 TMAG5253BA3 no verso, 2 multiplexadores, grupos EN_A (canais 0-7) e EN_B (8-15).",
          "Espera de 45 us depois de trocar o S3. Canais iguais ao Pocket v0.3 (refazer na placa, M3)."],
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
          '(comment 1 "etutti/hardware/viaggio_micromod/pcb/schematic.py escreve este arquivo; nao editar a mao"))' %
          (S.quote("eTutti Viaggio MicroMod · %s · %s" % (sheet, title)), DATE, S.quote(REV)))
    txt = ('(kicad_sch\n\t(version 20250610)\n\t(generator "viaggio_micromod_schematic")\n\t(generator_version "10.0")\n'
           '\t(uuid "%s")\n\t(paper "%s")\n%s\n' % (SHEET_UUID[sheet], paper, tb))
    txt += lib_symbols_block(used) + notes + "\n" + "\n".join(body_txt) + "\n\t(embedded_fonts no)\n)\n"
    open(os.path.join(KDIR, "%s_%s.kicad_sch" % (PROJECT, sheet)), "w", encoding="utf-8", newline="\n").write(txt)
    return nets, paper


def write_root(flags):
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
    notes = [
        "eTutti Viaggio MicroMod · esquema eletrico (SPEC v2.2, passo M1). Uma folha por setor da SPEC (secao 3).",
        "Campo 'Codigo' = codigo da peca na SPEC (P1...T4), o mesmo de concept/out/viaggio_micromod.json.",
        "Placa: passo M2 (posicionamento, sem trilhas; o J roteia). Ligacoes entre folhas por rotulos globais.",
        "PWR_FLAG abaixo: redes alimentadas por conector, ferrite, indutor ou diodo (o ERC nao ve a fonte).",
    ]
    ntxt = "\n".join('\t(text %s (exclude_from_sim no) (at 25 %s 0) %s (uuid "%s"))' %
                     (S.quote(line), fmt(15 + 6 * i), eff("left", size=2.0), uid("rootnote", i))
                     for i, line in enumerate(notes))
    tb = ('\t(title_block (title "eTutti Viaggio MicroMod · esquema") (date "%s") (rev %s) (company "beatconfused.com") '
          '(comment 1 "etutti/hardware/viaggio_micromod/pcb/schematic.py escreve este arquivo; nao editar a mao"))' %
          (DATE, S.quote(REV)))
    txt = ('(kicad_sch\n\t(version 20250610)\n\t(generator "viaggio_micromod_schematic")\n\t(generator_version "10.0")\n'
           '\t(uuid "%s")\n\t(paper "A4")\n%s\n' % (ROOT_UUID, tb))
    txt += lib_symbols_block({"PWR_FLAG"}) + ntxt + "\n" + "\n".join(sheets + body)
    txt += '\n\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n'
    open(os.path.join(KDIR, PROJECT + ".kicad_sch"), "w", encoding="utf-8", newline="\n").write(txt)


def write_library():
    syms = "\n\t".join(S.dump(SYMBOLS[n], 1) for n in sorted(SYMBOLS))
    open(os.path.join(KDIR, LIB + ".kicad_sym"), "w", encoding="utf-8", newline="\n").write(
        '(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "viaggio_micromod_schematic")\n\t(generator_version "10.0")\n\t'
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
    path = os.path.join(HERE, "bom_preliminar.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "referencias", "qtd", "valor_peca", "encapsulamento", "lcsc", "classe_jlc",
                    "preco_unit_usd_est", "montagem", "status", "nota"])
        for row in BOM_EXTRA:
            w.writerow(row)
        for key in sorted(rows, key=lambda k: ("PEFIAT".index(k[0][0]), int(k[0][1:]) if k[0][1:].isdigit() else 0,
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
    counts, bad = run_checks(declared)
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
    sys.exit(1 if counts.get("error") or bad else 0)


if __name__ == "__main__":
    main()
