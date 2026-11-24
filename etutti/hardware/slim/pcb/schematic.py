"""Write the eTutti Slim main-board schematic (SPEC R1SL, stage 1), run ERC, check the netlist.

    python etutti/hardware/slim/pcb/schematic.py

Plain CPython (stdlib only); it calls KiCad 10's kicad-cli for ERC and for the netlist that is checked back against the nets
declared here. Independent of the Student V4 (the writer machinery was copied, not imported). The circuit is data: one PARTS
list per sheet (P processor chip-down, E power, F headphone codec, I interface, R ruler connectors). Nothing is placed or routed.

Writes (under etutti/hardware/slim/pcb/): kicad/slim.kicad_pro, slim.kicad_sch (root) + slim_<S>.kicad_sch, slim.kicad_sym,
sym-lib-table, fp-lib-table, slim.pretty/; build/slim_erc.json, slim_netlist.net; bom_esquema.csv.
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
PROJECT = "slim"
LIB = "slim"
DATE = "2026-11-24"
REV = "Slim R1SL etapa 1"

NS = uuid.UUID("a4c1e7d2-5b93-4f08-8d6a-31b7c9e0f5d4")


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


def rt1062_symbol():
    balls = json.load(open(os.path.join(HERE, "rt1062_balls.json")))
    groups = {u: [] for u in range(1, 7)}
    power_out = {"DCDC_LP", "VDD_HIGH_CAP", "NVCC_PLL", "VDD_SNVS_CAP", "VDD_USB_CAP"}
    power_in = {"DCDC_IN", "DCDC_IN_Q", "DCDC_GND", "NGND_KEL0", "NVCC_EMC", "NVCC_GPIO", "NVCC_SD0",
                "NVCC_SD1", "VDDA_ADC_3P3", "VDD_HIGH_IN", "VDD_SNVS_IN", "VDD_SOC_IN", "VSS",
                "USB_OTG1_VBUS", "USB_OTG2_VBUS"}
    seen = set()
    for ball, nm in sorted(balls.items(), key=lambda kv: (kv[1], kv[0])):
        if nm in power_out or nm in power_in or nm == "DCDC_SENSE":
            u = 1
            t = "power_out" if nm in power_out else ("input" if nm == "DCDC_SENSE" else "power_in")
            if nm in seen and t == "power_out":
                t = "passive"
        elif nm == "GPIO_AD_B0_05":   # BOOT_MODE1, tied to GND as on the Teensy 4.1
            u, t = 3, "passive"
        elif nm.startswith("GPIO_AD"):
            u, t = 3, "bidirectional"
        elif nm.startswith("GPIO_B"):
            u, t = 4, "bidirectional"
        elif nm.startswith("GPIO_EMC"):
            u, t = 5, "bidirectional"
        elif nm.startswith("GPIO_SD"):
            u, t = 6, "bidirectional"
        else:
            u = 2
            t = {"PMIC_ON_REQ": "output", "PMIC_STBY_REQ": "output", "XTALI": "passive", "XTALO": "passive",
                 "RTC_XTALI": "passive", "RTC_XTALO": "passive", "CCM_CLK1_N": "passive",
                 "CCM_CLK1_P": "passive", "GPANAIO": "passive", "USB_OTG1_DN": "bidirectional",
                 "USB_OTG1_DP": "bidirectional", "USB_OTG2_DN": "bidirectional",
                 "USB_OTG2_DP": "bidirectional", "WAKEUP": "bidirectional",
                 "USB_OTG1_CHD_B": "open_collector"}.get(nm, "input")
        seen.add(nm)
        groups[u].append((ball, nm, t))
    units = []
    for u in range(1, 7):
        pins = groups[u]
        if u == 1:   # inputs left, ground + regulator outputs right
            lp = [p for p in pins if p[2] in ("power_in", "input") and p[1] not in ("VSS", "DCDC_GND", "NGND_KEL0")]
            rp = [p for p in pins if p not in lp]
        else:
            h = (len(pins) + 1) // 2
            lp, rp = pins[:h], pins[h:]
        units.append((lp, rp))
    return box_symbol("MIMXRT1062DVJ6B", "U", units, "i.MX RT1062, 12 x 12 mm 196-ball BGA, 0.8 mm (Teensy 4.1)")


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


PASSIVES.update({
    ("R", "4.7k", "0402"): ("C25900", "basica", 0.001, "final"),
    ("R", "22k", "0402"): ("C25768", "basica", 0.001, "final"),
    ("R", "47k", "0402"): ("C25792", "basica", 0.001, "final"),
    ("R", "2.2M", "0402"): ("C11490", "estendida", 0.002, "final"),
    ("R", "1.5k", "0402"): ("C25867", "basica", 0.001, "conferir"),
    ("R", "1.8k", "0402"): ("C25871", "estendida", 0.001, "conferir"),
    ("C", "150nF", "0402"): ("C162182", "estendida", 0.0135, "final"),
})
SHEETS[:] = [("P", "Processador"), ("E", "Energia"), ("F", "Fone"), ("I", "Interface"), ("R", "Reguas")]
PARTS.clear()
PARTS.update({s: [] for s, _ in SHEETS})


def bav70(ref, a1, a2, k, code, note=""):
    """Basic common-cathode pair (SOT-23: 1 A1, 2 A2, 3 K); the symbol is the BAT54C's."""
    part(ref, sym("BAT54C", "Diode"), "BAV70", {"1": a1, "2": a2, "3": k}, code, fp=FP["SOT23"],
         lcsc="C68978", cls="basica", price=0.015, status="final", note=note,
         datasheet="https://www.lcsc.com/product-detail/C68978.html")


def pot_sw_symbol():
    return box_symbol("POT_SW_9mm", "RV", [([("1", "CCW", "passive"), ("2", "W", "passive"), ("3", "CW", "passive"),
                                             ("4", "SW1", "passive"), ("5", "SW2", "passive")], [])],
                      "9 mm rotary potentiometer with on/off rotary switch (SW1-SW2 closed when ON)")


def srbv_symbol():
    left = [("1", "C", "passive"), ("10", "C2", "passive")]
    right = [(str(n), "P%d" % (n - 1), "passive") for n in range(2, 9)] + [("9", "DUM", "passive")]
    return box_symbol("SRBV_7pos", "SW", [(left, right)], "Alps SRBV 7-position rotary switch, 1 pole, non-shorting; 1 and 10 common, 2..8 positions, 9 dummy")


# ---------------------------------------------------------------- P: processor (chip-down RT1062)
CUR[0] = "P"
sym("MIMXRT1062DVJ6B", "custom", rt1062_symbol)

# Teensy 4.1 pin numbers on the balls (names as in Teensy 4.1); pin map in pcb/PINOS.md
P1_NETS = {
    "GPIO_AD_B0_03": "CHG_STAT",        # 0
    "GPIO_AD_B0_02": "PGOOD_N",         # 1
    "GPIO_EMC_04": "SCAN_DATA_P",       # 2
    "GPIO_EMC_05": "SCAN_CLK_P",        # 3
    "GPIO_EMC_06": "SCAN_LATCH_P",      # 4
    "GPIO_EMC_08": "LED_G",             # 5
    "GPIO_B1_01": "I2S_TX",             # 7
    "GPIO_B0_00": "KEEP",               # 10
    "GPIO_B0_03": "LED_R",              # 13
    "GPIO_AD_B1_02": "OUT_R1",          # 14 / A0
    "GPIO_AD_B1_03": "OUT_R2",          # 15 / A1
    "GPIO_AD_B1_07": "VBAT_S",          # 16 / A2
    "GPIO_AD_B1_01": "I2C_SDA",         # 18
    "GPIO_AD_B1_00": "I2C_SCL",         # 19
    "GPIO_AD_B1_10": "I2S_LRCLK",       # 20
    "GPIO_AD_B1_11": "I2S_BCLK",        # 21
    "GPIO_AD_B1_08": "VOL_W",           # 22 / A8
    "GPIO_AD_B1_09": "AUD_MCLK_P",      # 23
    "GPIO_AD_B0_12": "REG_ADC",         # 24 / A10
    "GPIO_AD_B0_13": "SW_S",            # 25 / A11
    "GPIO_AD_B1_14": "OUT_R3",          # 26 / A12
    "GPIO_AD_B1_15": "OUT_R4",          # 27 / A13
    # bootloader (MKL02) and boot mode
    "GPIO_AD_B0_04": "BL_BOOT0", "GPIO_AD_B0_05": "GND", "GPIO_AD_B0_06": "BL_TMS", "GPIO_AD_B0_07": "BL_TCK",
    "GPIO_AD_B0_08": "BL_MOD", "GPIO_AD_B0_09": "BL_TDI", "GPIO_AD_B0_10": "BL_TDO",
    "GPIO_AD_B0_11": "PSWITCH", "GPIO_EMC_01": "BL_EMC01", "GPIO_B0_13": "BL_B013",
    # QSPI flash (FlexSPI A)
    "GPIO_SD_B1_06": "FLASH_CS", "GPIO_SD_B1_07": "FLASH_CLK", "GPIO_SD_B1_08": "FLASH_D0",
    "GPIO_SD_B1_09": "FLASH_D1", "GPIO_SD_B1_10": "FLASH_D2", "GPIO_SD_B1_11": "FLASH_D3",
    # supplies
    "DCDC_IN": "DCDC_IN", "DCDC_IN_Q": "+3V3", "DCDC_GND": "GND", "DCDC_LP": "DCDC_LP", "DCDC_PSWITCH": "PSWITCH",
    "DCDC_SENSE": "VDD_SOC", "NGND_KEL0": "GND", "NVCC_EMC": "+3V3", "NVCC_GPIO": "+3V3", "NVCC_SD0": "+3V3",
    "NVCC_SD1": "+3V3", "NVCC_PLL": "NVCC_PLL", "VDDA_ADC_3P3": "+3V3", "VDD_HIGH_CAP": "VDD_HIGH_CAP",
    "VDD_HIGH_IN": "+3V3", "VDD_SNVS_CAP": "VDD_SNVS_CAP", "VDD_SNVS_IN": "VDD_SNVS_IN", "VDD_SOC_IN": "VDD_SOC",
    "VDD_USB_CAP": "VDD_USB_CAP", "VSS": "GND", "USB_OTG1_VBUS": "VBUS", "USB_OTG2_VBUS": "VBUS",
    "USB_OTG1_DN": "USB_DN", "USB_OTG1_DP": "USB_DP", "PMIC_ON_REQ": "PMIC_ON_REQ", "POR_B": "POR_B",
    "XTALI": "XTALI", "XTALO": "XTALO", "RTC_XTALI": "RTC_XTALI", "RTC_XTALO": "RTC_XTALO",
}


def p1_nets():
    balls = json.load(open(os.path.join(HERE, "rt1062_balls.json")))
    return {b: P1_NETS[n] for b, n in balls.items() if n in P1_NETS}


part("U101", "MIMXRT1062DVJ6B", "MIMXRT1062DVJ6B", p1_nets(), "P1", fp="slim:BGA-196_12x12mm_P0.8mm_RT1062",
     lcsc="C3216699", cls="estendida", price=14.0, mount="consignada (so 1 em estoque na LCSC)", status="conferir", nc_rest=True,
     note="12x12 mm, 0,8 mm, 196 bolas (DVJ6B). ATENCAO: a SPEC cita DVL6B, que e o 10x10 mm de 0,65 mm (LCSC C2847497, 64 em estoque); "
          "os nomes das bolas sao os mesmos, so o footprint muda. ONOFF sem ligacao (como a Teensy 4.1 sem botao).",
     datasheet="https://www.pjrc.com/teensy/IMXRT1060CEC_rev4.pdf")
part("L101", sym("FerriteBead_Small", "Device"), "120R@100MHz 2A", {"1": "+3V3", "2": "DCDC_IN"}, "P1",
     fp=FP["0603L"], lcsc="C14709", cls="basica", price=0.005, status="final", note="Teensy L3", rot=90)
C("C101", "10uF", "DCDC_IN", "GND", "P1", "0603", note="Teensy C32")
C("C102", "4.7uF", "DCDC_IN", "GND", "P1", "0603", note="Teensy C24")
C("C103", "220nF", "DCDC_IN", "GND", "P1", note="Teensy C19")
part("L102", sym("L", "Device"), "4.7uH 800mA", {"1": "DCDC_LP", "2": "VDD_SOC"}, "P1", fp=FP["0805L"], lcsc="C63166",
     cls="estendida", price=0.05, status="conferir", note="Teensy L1; MPL2012S4R7MHT (TDK, 800 mA, 250 mohm)", rot=90)
C("C104", "10uF", "VDD_SOC", "GND", "P1", "0603", note="Teensy C30")
C("C105", "4.7uF", "VDD_SOC", "GND", "P1", "0603", note="Teensy C22")
C("C106", "220nF", "VDD_SOC", "GND", "P1", note="Teensy C12")
C("C107", "10nF", "VDD_SOC", "GND", "P1", note="Teensy C5")
C("C108", "2.2uF", "+3V3", "GND", "P1", note="Teensy C28 (NVCC)")
C("C109", "4.7uF", "+3V3", "GND", "P1", note="Teensy C23")
C("C110", "220nF", "+3V3", "GND", "P1", note="Teensy C11")
C("C111", "10nF", "+3V3", "GND", "P1", note="Teensy C6")
C("C112", "4.7uF", "VDD_HIGH_CAP", "GND", "P1", note="Teensy C25")
C("C113", "220nF", "VDD_HIGH_CAP", "GND", "P1", note="Teensy C16")
C("C114", "4.7uF", "NVCC_PLL", "GND", "P1", note="Teensy C26")
C("C115", "220nF", "NVCC_PLL", "GND", "P1", note="Teensy C14")
C("C116", "220nF", "VDD_SNVS_CAP", "GND", "P1", note="Teensy C13")
C("C117", "10uF", "VDD_USB_CAP", "GND", "P1", note="Teensy C31")
C("C118", "220nF", "VDD_USB_CAP", "GND", "P1", note="Teensy C17")
C("C119", "220nF", "VDD_SNVS_IN", "GND", "P1", note="Teensy C18")
bav70("D101", "+3V3", "+3V3", "VDD_SNVS_IN", "P1", note="Teensy D2: o SNVS vem do 3V3 (sem pilha); os dois anodos no 3V3")
bav70("D102", "VDD_USB_CAP", "NC", "VDD_SNVS_IN", "P1", note="Teensy D1")
R("R101", "100k", "PMIC_ON_REQ", "GND", "P1", note="Teensy R7 (sem sequenciamento por PMIC: o 3V3 sobe sozinho com o OUT do BQ24075)")
part("Y101", sym("Crystal_GND24", "Device"), "24MHz 8pF", {"1": "XTALI", "2": "GND", "3": "XTALO", "4": "GND"}, "P5",
     fp="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", lcsc="C524739", cls="estendida", price=0.12, status="conferir",
     note="7U24000E08UCG (3410 em estoque); o C431156 do Viaggio ficou sem estoque; 8 pF de carga com 12 pF + ~3 pF de placa (conferir ESR)")
C("C120", "12pF", "XTALO", "GND", "P5", note="Teensy C1")
C("C121", "12pF", "XTALI", "GND", "P5", note="Teensy C2")
R("R102", "2.2M", "XTALI", "GND", "P5", note="Teensy R5")
part("Y102", sym("Crystal", "Device"), "32.768kHz", {"1": "RTC_XTALI", "2": "RTC_XTALO"}, "P5",
     fp="Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", lcsc="C32346", cls="basica", price=0.15, status="conferir",
     note="Teensy Y2, opcional (o RTC so serve com o SNVS; aqui sem pilha, ele reinicia a cada partida)", rot=90)
C("C122", "20pF", "RTC_XTALO", "GND", "P5", note="Teensy C3")
C("C123", "20pF", "RTC_XTALI", "GND", "P5", note="Teensy C4")
part("U102", sym("MKL02Z32VFG4", "MCU_NXP_Kinetis"), "PJRC MKL02 bootloader (Teensy 4.1)",
     {"1": "+3V3", "2": "GND", "3": "PSWITCH", "4": "BL_BOOT0", "5": "BL_TMS", "6": "BL_TDO", "7": "BL_TDI",
      "8": "BL_TCK", "9": "POR_B", "10": "PROG", "11": "NC", "12": "BL_B013", "13": "BL_MOD",
      "14": "NC", "15": "BL_EMC01", "16": "NC", "17": "GND"}, "P2",
     fp="Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.9x1.9mm", lcsc="", cls="-", price=6.0,
     mount="consignada (so a PJRC vende)", status="conferir", note="PTA3 -> DCDC_PSWITCH, PTB5 -> AD_B0_08 (pagina da PJRC); LED de erro do bootloader nao montado",
     datasheet="https://www.pjrc.com/store/ic_mkl02_t4.html")
C("C124", "220nF", "+3V3", "GND", "P2", note="Teensy C8")
R("R104", "100k", "PSWITCH", "GND", "P2", note="Teensy R6")
part("U103", sym("W25Q64JVSS", "Memory_Flash", "W25Q32JVSS"), "W25Q64JVSSIM",
     {"1": "FLASH_CS", "2": "FLASH_D1", "3": "FLASH_D2", "4": "GND", "5": "FLASH_D0", "6": "FLASH_CLK",
      "7": "FLASH_D3", "8": "+3V3"}, "P3", fp="Package_SO:SOIC-8_5.3x5.3mm_P1.27mm", lcsc="C5362615",
     cls="estendida", price=2.97, status="final", note="64 Mbit como a Teensy 4.1; 3944 em estoque",
     datasheet="https://www.winbond.com/hq/product/code-storage-flash-memory/serial-nor-flash/?__locale=en&partNo=W25Q64JV")
C("C125", "220nF", "+3V3", "GND", "P3", note="desacoplamento da flash")
R("R105", "100", "AUD_MCLK_P", "AUD_MCLK", "P1", note="MCLK 11,3 MHz: serie, junto do processador")
R("R106", "100k", "CHG_STAT", "+3V3", "P1", note="pull-up do ~CHG do BQ24075 (dreno aberto)")
R("R107", "100k", "PGOOD_N", "+3V3", "P1", note="pull-up do ~PGOOD do BQ24075 (USB presente = 0)")

# ---------------------------------------------------------------- E: power
CUR[0] = "E"
part("J201", sym("USB_C_Receptacle_USB2.0_16P", "Connector"), "TYPE-C-31-M-14 (mid-mount)",
     {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND", "A4": "VBUS", "A9": "VBUS",
      "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN",
      "B7": "USB_DN", "A8": "NC", "B8": "NC"}, "E1", fp="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     lcsc="C223907", cls="estendida", price=0.15, status="conferir",
     note="HRO, 16 pinos, 'laminated board' = encaixado na borda da placa (mid-mount), 2218 em estoque. Pinagem do M-14 e footprint a conferir "
          "(o footprint aqui e o do M-12, so para o esquema); a JLCPCB pode nao montar peca mid-mount pela face de baixo")
R("R201", "5.1k", "CC1", "GND", "E1")
R("R202", "5.1k", "CC2", "GND", "E1")
part("F201", sym("Polyfuse", "Device"), "500mA 6V PTC", {"1": "VBUS", "2": "VBUS_F"}, "E2",
     fp="Resistor_SMD:R_0603_1608Metric", lcsc="C69679", cls="estendida", price=0.03, status="conferir",
     note="PTC do VBUS (SPEC 5.2); mais um tipo Extended (+US$ 3,09 na JLCPCB): pode sair, o BQ24075 ja limita a corrente", rot=90)
part("U201", sym("USBLC6-2SC6", "Power_Protection"), "USBLC6-2SC6",
     {"1": "USB_DP", "6": "USB_DP", "3": "USB_DN", "4": "USB_DN", "5": "VBUS", "2": "GND"}, "E2",
     fp=FP["SOT236"], lcsc="C7519", cls="estendida", price=0.05, status="conferir",
     datasheet="https://www.st.com/resource/en/datasheet/usblc6-2.pdf")
part("D201", sym("SMF5.0A", "Diode", "SMAJ5.0A"), "SMF5.0A", {"1": "VBUS", "2": "GND"}, "E2",
     fp="Diode_SMD:D_SOD-123F", lcsc="C151296", cls="estendida", price=0.05, status="final", note="TVS do VBUS", rot=90)
part("U202", sym("BQ24075RGT", "Battery_Management"), "BQ24075RGTR",
     {"1": "BAT_NTC", "2": "VBAT", "3": "VBAT", "4": "GND", "5": "GND", "6": "CHG_EN1", "7": "PGOOD_N", "8": "GND",
      "9": "CHG_STAT", "10": "VSYS", "11": "VSYS", "12": "CHG_ILIM", "13": "VBUS_F", "14": "NC", "15": "SYSOFF",
      "16": "CHG_ISET", "17": "GND"}, "E3", fp="Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm",
     lcsc="C15464", cls="estendida", price=0.9, status="final",
     note="USB500 (EN2=0, EN1=1), ICHG 0,4 A, TS = NTC da bateria, TMR aberto (timers de fabrica 0,5 h / 5 h); OUT regulado a 5,5 V com USB; "
          "SYSOFF tem pull-up interno de ~5 Mohm no VBAT: sem acionamento externo a bateria fica DESLIGADA do OUT (e nao carrega com adaptador)",
     datasheet="https://www.ti.com/lit/ds/symlink/bq24075.pdf")
C("C201", "10uF", "VBUS_F", "GND", "E3", "0805")
C("C202", "10uF", "VSYS", "GND", "E3", "0805")
C("C203", "10uF", "VBAT", "GND", "E3", "0805")
R("R203", "2.2k", "CHG_ISET", "GND", "E3", note="ICHG = 890/2200 = 0,405 A (0,4 C da bateria de 1000 mAh)")
R("R204", "1.5k", "CHG_ILIM", "GND", "E3", note="obrigatorio (teste de curto no start-up); so vale com EN2=1")
R("R205", "10k", "VBUS_F", "CHG_EN1", "E3", note="EN1 = 1 quando ha USB (USB500)")
R("R208", "1M", "VBAT", "VBAT_S", "E3", note="medida da bateria: V(pino 16) = VBAT/2")
R("R209", "1M", "VBAT_S", "GND", "E3")
C("C204", "100nF", "VBAT_S", "GND", "E3")
# --- energy logic (SPEC 4): knob switch (SW1 = VBAT, SW2 = SWV) -> pulse -> SYSOFF low; firmware KEEP holds; USB holds
nmos("Q201", "ONG", "GND", "SYSOFF", "E4", note="liga o OUT: puxa o SYSOFF a GND (a bateria passa a alimentar o sistema)")
C("C205", "4.7uF", "SWV", "ONG", "E4", "0603", note="borda do knob: o fechamento da chave empurra ~VBAT no ONG e ele decai (tau ~3 s com a perda de capacitancia): tempo para o firmware ligar o KEEP")
R("R210", "1M", "ONG", "GND", "E4", note="descarga do ONG")
pmos("Q202", "HOLDG", "SWV", "ONG", "E4", note="mantem o ONG em SWV enquanto o KEEP estiver alto E a chave do knob fechada (abrir o knob desliga em hardware)")
R("R211", "100k", "HOLDG", "SWV", "E4")
nmos("Q203", "KEEP", "GND", "HOLDG", "E4", note="o firmware (KEEP, pino 10) segura o sistema ligado; solta no desligamento automatico")
R("R212", "100k", "KEEP", "GND", "E4", note="KEEP baixo enquanto o processador parte")
nmos("Q204", "VBUS_G", "GND", "SYSOFF", "E4", note="com USB o SYSOFF fica baixo sempre (senao o BQ24075 nao carrega)")
R("R213", "100k", "VBUS_F", "VBUS_G", "E4")
R("R214", "100k", "VBUS_G", "GND", "E4")
R("R215", "1M", "SWV", "SW_S", "E4", note="leitura do estado do knob: V(pino 25) = SWV/2 (SWV so existe com o knob ligado; sem bateria nem USB nada)")
R("R216", "1M", "SW_S", "GND", "E4")
C("C206", "100nF", "SW_S", "GND", "E4")
part("U204", sym("TPS63001", "Regulator_Switching"), "TPS63001DRCR",
     {"1": "+3V3", "2": "BB_L2", "3": "GND", "4": "BB_L1", "5": "VSYS", "6": "VSYS", "7": "GND",
      "8": "BB_VINA", "9": "GND", "10": "+3V3", "11": "GND"}, "E5", fp="Package_SON:Texas_DRC0010J",
     lcsc="C28060", cls="estendida", price=1.40, status="final", note="3,3 V fixo; EN em VSYS (sempre ligado com OUT); PS/SYNC baixo = economia",
     datasheet="https://www.ti.com/lit/ds/symlink/tps63001.pdf")
part("L201", sym("L", "Device"), "2.2uH", {"1": "BB_L1", "2": "BB_L2"}, "E5", fp="Inductor_SMD:L_Changjiang_FNR4020S",
     lcsc="C167825", cls="estendida", price=0.08, status="final", note="FNR4020S2R2MT, 2 mm de altura (folga abaixo da placa: SPEC 3)", rot=90)
C("C207", "10uF", "VSYS", "GND", "E5", "0805")
C("C208", "10uF", "+3V3", "GND", "E5", "0805")
C("C209", "10uF", "+3V3", "GND", "E5", "0805")
R("R217", "100", "VSYS", "BB_VINA", "E5")
C("C210", "100nF", "BB_VINA", "GND", "E5")
C("C211", "100nF", "+3V3", "GND", "E5")
part("J202", sym("Conn_01x03_MountingPin", "Connector_Generic_MountingPin"), "S3B-PH-SM4-TB",
     {"1": "VBAT", "2": "BAT_NTC", "3": "GND", "MP": "GND"}, "E6",
     fp="Connector_JST:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal", lcsc="C265101", cls="estendida",
     price=0.27, status="final", note="bateria: 1 +, 2 NTC, 3 - (conferir a ordem do cabo da bateria escolhida)")

# ---------------------------------------------------------------- F: headphone codec
CUR[0] = "F"
part("U301", sym("SGTL5000XNLA3", "Audio"), "SGTL5000XNLA3R2",
     {"1": "HP_R", "2": "HP_VGND", "3": "SGTL_VDDA", "4": "HP_L", "5": "SGTL_VAG", "6": "NC", "7": "NC",
      "8": "NC", "9": "NC", "10": "NC", "11": "NC", "12": "+3V3", "13": "AUD_MCLK", "14": "I2S_LRCLK",
      "15": "I2S_BCLK", "16": "NC", "17": "I2S_TX", "18": "I2C_SDA", "19": "I2C_SCL", "20": "SGTL_VDDD",
      "21": "GND"}, "F1", fp="Package_DFN_QFN:QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm", lcsc="C2651833",
     cls="estendida", price=9.35, status="final",
     note="QFN-20 (C2651833, 952 em estoque; o C511764 do Viaggio era a variante QFN-32); sem microfone nem entrada de linha; I2C fixo 0x0A",
     datasheet="https://www.pjrc.com/teensy/SGTL5000.pdf")
part("FB301", sym("FerriteBead_Small", "Device"), "600R@100MHz", {"1": "+3V3", "2": "SGTL_VDDA"}, "F1",
     fp=FP["0603L"], lcsc="C19330", cls="estendida", price=0.02, status="conferir", note="Audio Board: ferrite 600 no VDDA", rot=90)
C("C301", "2.2uF", "SGTL_VDDA", "GND", "F1")
C("C302", "100nF", "SGTL_VDDA", "GND", "F1")
C("C303", "2.2uF", "+3V3", "GND", "F1", note="VDDIO")
C("C304", "100nF", "+3V3", "GND", "F1")
C("C305", "100nF", "+3V3", "GND", "F1")
part("U302", sym("XC6206P182MR", "Regulator_Linear", "XC6206PxxxMR"), "XC6206P182MR",
     {"1": "GND", "2": "SGTL_VDDD", "3": "+3V3"}, "F1", fp="Package_TO_SOT_SMD:SOT-23-3", lcsc="C347373",
     cls="estendida", price=0.03, status="conferir", note="1,8 V do VDDD (a Audio Board usa AP7313)")
C("C306", "2.2uF", "SGTL_VDDD", "GND", "F1")
C("C307", "100nF", "SGTL_VAG", "GND", "F1", note="datasheet do SGTL5000: VAG = 0,1 uF (o Viaggio tinha 0,15)")
R("R301", "2.2k", "+3V3", "I2C_SDA", "F1")
R("R302", "2.2k", "+3V3", "I2C_SCL", "F1")
sym("PJ-327A", "custom", jack_symbol)
part("J301", "PJ-327A", "jack 3,5 mm mid-mount (a definir)",
     {"1": "HP_VGND", "2": "HP_VGND", "3": "HP_R", "4": "HP_L", "5": "NC"}, "F2",
     fp="slim:Jack_3.5mm_PJ-327A_SMD", lcsc="", cls="-", price=0.15, mount="sem LCSC em estoque (mid-mount nao achado): montar em casa ou consignar",
     status="conferir",
     note="P2 mid-mount na parede esquerda; o footprint e o do PJ-327A de topo, so para o esquema; 1/2 manga (HP_VGND, nunca no GND), 3 anel, 4 ponta; "
          "contato da ponta nao usado (sem alto-falante)")

# ---------------------------------------------------------------- I: interface
CUR[0] = "I"
sym("POT_SW_9mm", "custom", pot_sw_symbol)
sym("SRBV_7pos", "custom", srbv_symbol)
part("SW401", "POT_SW_9mm", "pot 9 mm 50k B c/ chave (a definir)",
     {"1": "GND", "2": "VOL_W", "3": "+3V3", "4": "VBAT", "5": "SWV"}, "I1",
     fp="Potentiometer_THT:Potentiometer_Alps_RK097_Single_Horizontal_Switch", lcsc="", cls="-", price=1.5,
     mount="sem LCSC (nenhum pot de 9 mm com chave rotativa no catalogo da JLCPCB): montar em casa", status="conferir",
     note="volume continuo; a chave fecha SW1-SW2 ao sair de OFF no sentido horario. O footprint e o do RK097 horizontal com chave, so para o esquema. "
          "O RK097 da LCSC com 5 pinos (RK0971114Z1N) tem chave de EMPURRAR, nao rotativa")
C("C401", "100nF", "VOL_W", "GND", "I1", note="filtro do cursor do pot")
part("SW402", "SRBV_7pos", "Alps SRBV170501",
     {"1": "REG_ADC", "10": "REG_ADC", "2": "REG_P1", "3": "REG_P2", "4": "REG_P3", "5": "REG_P4", "6": "REG_P5",
      "7": "REG_P6", "8": "REG_P7", "9": "NC"}, "I2", fp="slim:Rotary_Alps_SRBV_7p5_Vertical",
     lcsc="C470375", cls="estendida", price=3.62, status="conferir", mount="THT: montar em casa",
     note="7 posicoes, 1 polo, sem curto entre posicoes, corpo de 7,5 mm; L = 15 ou 20 mm de eixo (o 170501 e o 170701 de L diferente: conferir qual); 325 em estoque; footprint aproximado",
     datasheet="https://datasheet.lcsc.com/datasheet/pdf/190b925bc48073e99305ed7b719b3b35.pdf?productCode=C470375")
R("R401", "10k", "+3V3", "REG_ADC", "I2", note="topo da escada: aberto entre posicoes = 3,3 V")
for k, rv in enumerate(("1k", "2.2k", "4.7k", "10k", "22k", "47k", "100k"), 1):
    R("R40%d" % (k + 1), rv, "REG_P%d" % k, "GND", "I2",
      note="posicao %d: V = 3,3 x R/(10k+R) = %.2f V" % (k, 3.3 * float(rv.replace("k", "")) / (10 + float(rv.replace("k", "")))))
C("C402", "100nF", "REG_ADC", "GND", "I2")
part("D401", sym("LED_RG_1615", "Device", "LED_Dual_AAKK", fix=led_pins), "TJ-S1615SW6TGLCRG-A5",
     {"1": "LED_R_A", "3": "LED_G_A", "2": "GND", "4": "GND"}, "I3", fp="slim:LED_1615_RG_4pad", lcsc="C273605",
     cls="estendida", price=0.08, status="final",
     note="1615 vermelho/verde (laranja = os dois); face de baixo, montagem reversa, acende o anel do knob de volume",
     datasheet="https://www.lcsc.com/datasheet/lcsc_datasheet_1810191024_TOGIALED-TJ-S1615SW6TGLCRG-A5_C273605.pdf")
R("R409", "330", "LED_R", "LED_R_A", "I3")
R("R410", "100", "LED_G", "LED_G_A", "I3")
part("SW403", sym("SW_Push", "Switch"), "Program", {"1": "PROG", "2": "GND"}, "I4",
     fp="Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", lcsc="C318884", cls="basica", price=0.02,
     status="conferir", note="PROG: dentro do case, so abrindo a base (SPEC 4)", rot=0)

# ---------------------------------------------------------------- R: ruler connectors
CUR[0] = "R"
sym("Conn_01x08_MountingPin", "Connector_Generic_MountingPin")
for k in range(1, 5):
    part("J60%d" % k, "Conn_01x08_MountingPin", "FFC 8P 0.5 mm, contato por baixo",
         {"1": "GND", "2": "+3V3", "3": "OUT_R%d" % k, "4": "SCAN_DATA", "5": "SCAN_CLK", "6": "SCAN_LATCH", "7": "GND",
          "8": "GND", "MP": "GND"}, "R%d" % k,
         fp="Connector_FFC-FPC:Amphenol_F32Q-1A7x1-11008_1x08-1MP_P0.5mm_Horizontal", lcsc="C66953", cls="estendida",
         price=0.10, status="conferir",
         note="fileira %d: cabo FFC reto de 8 vias ate a regua R8 (SPEC 5.1: GND 3V3 OUT DADO CLOCK LATCH GND GND); LCSC 0.5-8P clamshell, h = 2 mm, 5028 em estoque; "
              "footprint do esquema = Amphenol (so placeholder; pads reais no passo 2)" % k)
    R("R60%d" % k, "100k", "OUT_R%d" % k, "GND", "R%d" % k, note="pull-down da linha OUT da fileira (saidas dos TMAG5253 ficam em alta impedancia sem EN)")
R("R605", "100", "SCAN_DATA_P", "SCAN_DATA", "R5", note="serie junto do processador (as 4 fileiras em paralelo)")
R("R606", "100", "SCAN_CLK_P", "SCAN_CLK", "R5", note="serie junto do processador")
R("R607", "100", "SCAN_LATCH_P", "SCAN_LATCH", "R5", note="serie junto do processador")
C("C601", "10uF", "+3V3", "GND", "R5", "0805", note="reservatorio do +3V3 das reguas (um TMAG5253 por vez, ~2 mA)")



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
    "P": ["P · Processador: RT1062 chip-down como a Teensy 4.1 (sem Ethernet, host USB, SD nem PSRAM); MKL02 com bootloader PJRC (consignado).",
          "3,3 V sobe sozinho quando o OUT do BQ24075 existe; SNVS pelo 3V3 (sem pilha). Nunca ativar o modo seguro.",
          "Pinos do Teensy 4.1 nas bolas: ver pcb/PINOS.md."],
    "E": ["E · Energia: USB-C -> PTC -> BQ24075 (USB500, 0,4 A, NTC) -> VSYS -> TPS63001 (3,3 V).",
          "SYSOFF (pull-up interno ~5 Mohm no VBAT) fica ALTO = bateria desligada. Puxado a GND por: borda do knob (C205), KEEP do firmware (Q202/Q203) ou USB (Q204).",
          "Abrir o knob desfaz o KEEP em hardware (Q202 so conduz com a chave fechada)."],
    "F": ["F · Fone: SGTL5000 como a Audio Board Rev D2, so saida de fone. HP_VGND e terra virtual: NUNCA no GND."],
    "I": ["I · Interface: pot 9 mm com chave (volume continuo + liga), chave rotativa de 7 posicoes (escada de resistores em REG_ADC), LED bicolor, PROG."],
    "R": ["R · Reguas: 4 conectores FFC de 8 vias (GND 3V3 OUT DADO CLOCK LATCH GND GND); DADO, CLOCK e LATCH comuns com 100 ohm de serie."],
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
          '(comment 1 "etutti/hardware/slim/pcb/schematic.py escreve este arquivo; nao editar a mao"))' %
          (S.quote("eTutti Slim · %s · %s" % (sheet, title)), DATE, S.quote(REV)))
    txt = ('(kicad_sch\n\t(version 20250610)\n\t(generator "slim_schematic")\n\t(generator_version "10.0")\n'
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
        "eTutti Slim · esquema eletrico (SPEC R1SL, etapa 1).",
        "Campo 'Codigo' = grupo da peca (P1... R5) para o posicionamento da etapa 2.",
        "Etapa 1 (portao A): so esquema. Ligacoes entre folhas por rotulos globais.",
        "PWR_FLAG abaixo: redes alimentadas por conector, ferrite, indutor ou diodo (o ERC nao ve a fonte).",
    ]
    ntxt = "\n".join('\t(text %s (exclude_from_sim no) (at 25 %s 0) %s (uuid "%s"))' %
                     (S.quote(line), fmt(15 + 6 * i), eff("left", size=2.0), uid("rootnote", i))
                     for i, line in enumerate(notes))
    tb = ('\t(title_block (title "eTutti Slim · esquema") (date "%s") (rev %s) (company "beatconfused.com") '
          '(comment 1 "etutti/hardware/slim/pcb/schematic.py escreve este arquivo; nao editar a mao"))' %
          (DATE, S.quote(REV)))
    txt = ('(kicad_sch\n\t(version 20250610)\n\t(generator "slim_schematic")\n\t(generator_version "10.0")\n'
           '\t(uuid "%s")\n\t(paper "A4")\n%s\n' % (ROOT_UUID, tb))
    txt += lib_symbols_block({"PWR_FLAG"}) + ntxt + "\n" + "\n".join(sheets + body)
    txt += '\n\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n'
    open(os.path.join(KDIR, PROJECT + ".kicad_sch"), "w", encoding="utf-8", newline="\n").write(txt)


def write_library():
    syms = "\n\t".join(S.dump(SYMBOLS[n], 1) for n in sorted(SYMBOLS))
    open(os.path.join(KDIR, LIB + ".kicad_sym"), "w", encoding="utf-8", newline="\n").write(
        '(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "slim_schematic")\n\t(generator_version "10.0")\n\t'
        + syms + "\n)\n")
    open(os.path.join(KDIR, "sym-lib-table"), "w", newline="\n").write(
        '(sym_lib_table\n\t(version 7)\n\t(lib (name "%s") (type "KiCad") (uri "${KIPRJMOD}/%s.kicad_sym") '
        '(options "") (descr "eTutti Slim, written by schematic.py"))\n)\n' % (LIB, LIB))
    open(os.path.join(KDIR, "fp-lib-table"), "w", newline="\n").write(
        '(fp_lib_table\n\t(version 7)\n\t(lib (name "%s") (type "KiCad") (uri "${KIPRJMOD}/%s.pretty") '
        '(options "") (descr "eTutti Slim footprints, written by footprints.py"))\n)\n' % (LIB, LIB))
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
        for key in sorted(rows, key=lambda k: ("PEFIR".index(k[0][0]), int(k[0][1:]) if k[0][1:].isdigit() else 0,
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
    erc = os.path.join(BUILD, "slim_erc.json")
    subprocess.run([KICAD_CLI, "sch", "erc", "--format", "json", "--severity-all", "-o", erc, root],
                   check=False, capture_output=True)
    rep = json.load(open(erc, encoding="utf-8"))
    counts = {}
    for sh in rep.get("sheets", []):
        for v in sh.get("violations", []):
            counts.setdefault(v["severity"], []).append((sh.get("path"), v["type"], v["description"],
                                                         [i.get("description") for i in v.get("items", [])]))
    net = os.path.join(BUILD, "slim_netlist.net")
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
    print("footprints: %s (BGA %d pads = rt1062_balls.json)" % (", ".join(fps), nballs))
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
