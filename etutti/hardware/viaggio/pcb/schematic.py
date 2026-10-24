"""Write the eTutti Viaggio schematic (SPEC v2, step 3.1), run ERC, check it.

    python etutti/hardware/viaggio/pcb/schematic.py

Plain CPython (stdlib only); it calls KiCad 10's kicad-cli for ERC and for
the netlist that is checked back against the nets declared here.

The circuit is data: one PARTS list per sector sheet (P, E, F, I, A, T).
Every part carries its SPEC section 3 code (P1 ... T4) in the "Codigo"
field, so the board step (3.2) can match parts to concept/rev2/out/
viaggio_rev2.json. Nothing is placed or routed here.

Sources:
  P, E5      PJRC Teensy 4.1 schematic (pjrc.com/teensy/schematic.html) and the
             MKL02 bootloader page (pjrc.com/store/ic_mkl02_t4.html); RT1062 balls
             from NXP IMXRT1060CEC rev 4, table 87 (rt1062_balls.json, checked
             against all 133 balls the Teensy 4.1 schematic names).
  F          PJRC Audio Adaptor Rev D2 (20-pin SGTL5000), as used by the Pocket.
  E, I, A, T the eTuttino Pocket (pocket/pcb/build_pocket_pcb.py, PINOS.md).

Writes (under etutti/hardware/viaggio/pcb/):
  kicad/viaggio.kicad_pro, viaggio.kicad_sch (root) + viaggio_<S>.kicad_sch
  kicad/viaggio.kicad_sym + sym-lib-table   the project's own symbols
  build/viaggio_erc.json, build/viaggio_netlist.net
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

KICAD = "C:/Program Files/KiCad/10.0"
KICAD_SYM = KICAD + "/share/kicad/symbols"
KICAD_FP = KICAD + "/share/kicad/footprints"
KICAD_CLI = KICAD + "/bin/kicad-cli.exe"
KDIR = os.path.join(HERE, "kicad")
BUILD = os.path.join(HERE, "build")
PROJECT = "viaggio"
LIB = "viaggio"
DATE = "2026-10-24"
REV = "SPEC v2 - passo 3.1"

NS = uuid.UUID("6f1d3a52-6b0e-4c55-9a51-7a1c0e2b9a11")


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


# ---------------------------------------------------------------- P: processor
sym("MIMXRT1062DVJ6B", "custom", rt1062_symbol)
sym("TMAG5253BA3", "custom", tmag_symbol)

P1_NETS = {
    # Teensy 4.1 pins 0-26 (PINOS.md)
    "GPIO_AD_B0_03": "MUX_S0", "GPIO_AD_B0_02": "MUX_S1", "GPIO_EMC_04": "MUX_S2", "GPIO_EMC_05": "MUX_S3",
    "GPIO_EMC_06": "SENS_EN", "GPIO_EMC_08": "LED_G", "GPIO_B0_10": "SEL_SW", "GPIO_B1_01": "I2S_TX",
    "GPIO_B0_11": "SEL_B", "GPIO_B0_00": "KEEP", "GPIO_B0_02": "SEL_A", "GPIO_B0_01": "AMP_SD",
    "GPIO_B0_03": "LED_R", "GPIO_AD_B1_02": "MUX_R_COM", "GPIO_AD_B1_03": "MUX_L_COM",
    "GPIO_AD_B1_07": "VBAT_S", "GPIO_AD_B1_06": "HP_DET", "GPIO_AD_B1_01": "I2C_SDA",
    "GPIO_AD_B1_00": "I2C_SCL", "GPIO_AD_B1_10": "I2S_LRCLK", "GPIO_AD_B1_11": "I2S_BCLK",
    "GPIO_AD_B1_08": "VOL_A", "GPIO_AD_B1_09": "AUD_MCLK_P", "GPIO_AD_B0_12": "VOL_B",
    "GPIO_AD_B0_13": "VOL_SW", "GPIO_AD_B1_14": "CHG_STAT",
    # bootloader (MKL02) and boot mode
    "GPIO_AD_B0_04": "BL_BOOT0", "GPIO_AD_B0_05": "GND", "GPIO_AD_B0_06": "BL_TMS", "GPIO_AD_B0_07": "BL_TCK",
    "GPIO_AD_B0_08": "BL_MOD", "GPIO_AD_B0_09": "BL_TDI", "GPIO_AD_B0_10": "BL_TDO",
    "GPIO_AD_B0_11": "PSWITCH", "GPIO_EMC_01": "BL_EMC01", "GPIO_B0_13": "BL_B013",
    # QSPI flash (FlexSPI A) and PSRAM (FlexSPI2, Teensy 4.1 pins 48-54)
    "GPIO_SD_B1_06": "FLASH_CS", "GPIO_SD_B1_07": "FLASH_CLK", "GPIO_SD_B1_08": "FLASH_D0",
    "GPIO_SD_B1_09": "FLASH_D1", "GPIO_SD_B1_10": "FLASH_D2", "GPIO_SD_B1_11": "FLASH_D3",
    "GPIO_EMC_24": "PSRAM_CS", "GPIO_EMC_25": "PSRAM_CLK", "GPIO_EMC_26": "PSRAM_D0", "GPIO_EMC_27": "PSRAM_D1",
    "GPIO_EMC_28": "PSRAM_D2", "GPIO_EMC_29": "PSRAM_D3",
    # supplies
    "DCDC_IN": "DCDC_IN", "DCDC_IN_Q": "+3V3", "DCDC_GND": "GND", "DCDC_LP": "DCDC_LP", "DCDC_PSWITCH": "PSWITCH",
    "DCDC_SENSE": "VDD_SOC", "NGND_KEL0": "GND", "NVCC_EMC": "+3V3", "NVCC_GPIO": "+3V3", "NVCC_SD0": "+3V3",
    "NVCC_SD1": "+3V3", "NVCC_PLL": "NVCC_PLL", "VDDA_ADC_3P3": "+3V3", "VDD_HIGH_CAP": "VDD_HIGH_CAP",
    "VDD_HIGH_IN": "+3V3", "VDD_SNVS_CAP": "VDD_SNVS_CAP", "VDD_SNVS_IN": "VDD_SNVS_IN", "VDD_SOC_IN": "VDD_SOC",
    "VDD_USB_CAP": "VDD_USB_CAP", "VSS": "GND", "USB_OTG1_VBUS": "VBUS", "USB_OTG2_VBUS": "VBUS",
    "USB_OTG1_DN": "USB_DN", "USB_OTG1_DP": "USB_DP", "PMIC_ON_REQ": "PMIC_ON_REQ", "POR_B": "POR_B",
    "ONOFF": "ONOFF", "XTALI": "XTALI", "XTALO": "XTALO", "RTC_XTALI": "RTC_XTALI", "RTC_XTALO": "RTC_XTALO",
}


def p1_nets():
    balls = json.load(open(os.path.join(HERE, "rt1062_balls.json")))
    return {b: P1_NETS[n] for b, n in balls.items() if n in P1_NETS}


CUR[0] = "P"
part("U101", "MIMXRT1062DVJ6B", "MIMXRT1062DVJ6B", p1_nets(), "P1", lcsc="", cls="-", price=11.0,
     mount="consignada (PJRC ou DigiKey)", status="conferir", nc_rest=True,
     note="footprint BGA-196 12x12 P0.8 a criar no passo 3.2; bolas livres sem ligacao (SD_B1_05/N3 e EMC_23/G2 de proposito)",
     datasheet="https://www.pjrc.com/teensy/IMXRT1060CEC_rev4.pdf")
part("L101", sym("FerriteBead_Small", "Device"), "120R@100MHz", {"1": "+3V3", "2": "DCDC_IN"}, "P1",
     fp=FP["0603L"], lcsc="", cls="basica", price=0.005, note="Teensy L3; >=1 A", rot=90)
C("C101", "10uF", "DCDC_IN", "GND", "P1", "0603", note="Teensy C32")
C("C102", "4.7uF", "DCDC_IN", "GND", "P1", "0603", note="Teensy C24")
C("C103", "220nF", "DCDC_IN", "GND", "P1", note="Teensy C19")
part("L102", sym("L", "Device"), "4.7uH", {"1": "DCDC_LP", "2": "VDD_SOC"}, "P1", fp=FP["0805L"], lcsc="",
     cls="estendida", price=0.05, note="Teensy L1; corrente do nucleo (conferir >= 0,5 A)", rot=90)
C("C104", "10uF", "VDD_SOC", "GND", "P1", "0603", note="Teensy C30")
C("C105", "4.7uF", "VDD_SOC", "GND", "P1", "0603", note="Teensy C22")
C("C106", "220nF", "VDD_SOC", "GND", "P1", note="Teensy C12")
C("C107", "10nF", "VDD_SOC", "GND", "P1", note="Teensy C5")
C("C108", "2.2uF", "+3V3", "GND", "P1", note="Teensy C28 (NVCC)")
C("C109", "4.7uF", "+3V3", "GND", "P1", "0603", note="Teensy C23")
C("C110", "220nF", "+3V3", "GND", "P1", note="Teensy C11")
C("C111", "10nF", "+3V3", "GND", "P1", note="Teensy C6")
C("C112", "4.7uF", "VDD_HIGH_CAP", "GND", "P1", "0603", note="Teensy C25")
C("C113", "220nF", "VDD_HIGH_CAP", "GND", "P1", note="Teensy C16")
C("C114", "4.7uF", "NVCC_PLL", "GND", "P1", "0603", note="Teensy C26")
C("C115", "220nF", "NVCC_PLL", "GND", "P1", note="Teensy C14")
C("C116", "220nF", "VDD_SNVS_CAP", "GND", "P1", note="Teensy C13")
C("C117", "10uF", "VDD_USB_CAP", "GND", "P1", "0603", note="Teensy C31")
C("C118", "220nF", "VDD_USB_CAP", "GND", "P1", note="Teensy C17")
C("C119", "220nF", "VDD_SNVS_IN", "GND", "P1", note="Teensy C18")
bat54c("D101", "SNVS_3V3", "+3V3", "VDD_SNVS_IN", "P1",
       note="Teensy D2: o anodo da pilha (VBAT) vai no SNVS_3V3 de E5")
bat54c("D102", "VDD_USB_CAP", "NC", "VDD_SNVS_IN", "P1", note="Teensy D1")
R("R101", "100k", "PMIC_ON_REQ", "GND", "P1", note="Teensy R7")
part("Y101", sym("Crystal_GND24", "Device"), "24MHz", {"1": "XTALI", "2": "GND", "3": "XTALO", "4": "GND"}, "P5",
     fp="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", lcsc="C431156", cls="estendida", price=0.10,
     note="Teensy Y1; 8 pF de carga com 12 pF + ~3 pF de placa (conferir)")
C("C120", "12pF", "XTALO", "GND", "P5", note="Teensy C1")
C("C121", "12pF", "XTALI", "GND", "P5", note="Teensy C2")
R("R102", "2.2M", "XTALI", "GND", "P5", note="Teensy R5 (em paralelo com C2, como no esquema da PJRC)")
part("Y102", sym("Crystal", "Device"), "32.768kHz", {"1": "RTC_XTALI", "2": "RTC_XTALO"}, "P5",
     fp="Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", lcsc="C32346", cls="basica", price=0.08,
     note="Teensy Y2; FC-135 12,5 pF, 3215 (a SPEC pedia 2012: conferir)", rot=90)
C("C122", "20pF", "RTC_XTALO", "GND", "P5", note="Teensy C3")
C("C123", "20pF", "RTC_XTALI", "GND", "P5", note="Teensy C4")
part("U102", sym("MKL02Z32VFG4", "MCU_NXP_Kinetis"), "PJRC MKL02 bootloader (Teensy 4.1)",
     {"1": "+3V3", "2": "GND", "3": "PSWITCH", "4": "BL_BOOT0", "5": "BL_TMS", "6": "BL_TDO", "7": "BL_TDI",
      "8": "BL_TCK", "9": "POR_B", "10": "PROG", "11": "BL_LED_N", "12": "BL_B013", "13": "BL_MOD",
      "14": "NC", "15": "BL_EMC01", "16": "NC", "17": "GND"}, "P2",
     fp="Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.9x1.9mm", lcsc="", cls="-", price=6.0,
     mount="consignada (PJRC)", status="conferir", note="PTA3 -> DCDC_PSWITCH, PTB5 -> AD_B0_08 (pagina da PJRC)",
     datasheet="https://www.pjrc.com/store/ic_mkl02_t4.html")
C("C124", "220nF", "+3V3", "GND", "P2", note="Teensy C8")
part("D103", sym("LED", "Device"), "vermelho", {"1": "BL_LED_K", "2": "+3V3"}, "P2",
     fp="LED_SMD:LED_0603_1608Metric", lcsc="C2286", cls="basica", price=0.01, status="conferir",
     note="Teensy D4: LED de erro do bootloader (piscadas da pagina da PJRC), no verso", rot=90)
R("R103", "470", "BL_LED_K", "BL_LED_N", "P2", note="Teensy R2")
R("R104", "100k", "PSWITCH", "GND", "P2", note="Teensy R6")
part("U103", sym("W25Q64JVSS", "Memory_Flash", "W25Q32JVSS"), "W25Q64JVSSIQ",
     {"1": "FLASH_CS", "2": "FLASH_D1", "3": "FLASH_D2", "4": "GND", "5": "FLASH_D0", "6": "FLASH_CLK",
      "7": "FLASH_D3", "8": "+3V3"}, "P3", fp="Package_SO:SOIC-8_5.3x5.3mm_P1.27mm", lcsc="C179171",
     cls="estendida", price=0.80, status="conferir",
     note="64 Mbit = modelo Teensy 4.1; '-Q' exige bootloader >= 1.09 (lista da PJRC), '-M' serve em todos",
     datasheet="https://www.winbond.com/hq/product/code-storage-flash-memory/serial-nor-flash/?__locale=en&partNo=W25Q64JV")
C("C125", "220nF", "+3V3", "GND", "P3", note="desacoplamento (o esquema da PJRC nao mostra o do U3)")
part("U104", sym("APS6404L-3SQR-ZR", "Memory_RAM", "APS6404L-3SQRx-ZR"), "APS6404L-3SQR-ZR",
     {"1": "PSRAM_CS", "2": "PSRAM_D1", "3": "PSRAM_D2", "4": "GND", "5": "PSRAM_D0", "6": "PSRAM_CLK",
      "7": "PSRAM_D3", "8": "+3V3", "9": "NC"}, "P4",
     fp="Package_SON:Winbond_USON-8-1EP_3x2mm_P0.5mm_EP0.2x1.6mm", lcsc="C3040877", cls="estendida", price=1.9,
     mount="nao montar", status="conferir", dnp=True, note="so o lugar (modelos futuros); sem estoque na LCSC em out/2026",
     datasheet="https://www.lcsc.com/product-detail/C3040877.html")
C("C126", "220nF", "+3V3", "GND", "P4", note="Teensy C21; nao montar", dnp=True)
R("R105", "100", "AUD_MCLK_P", "AUD_MCLK", "P1", note="MCLK 11,3 MHz: em serie, junto do P1 (SPEC 4, 8o)")

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
     datasheet="https://www.st.com/resource/en/datasheet/usblc6-2.pdf")
part("D201", sym("SMF5.0A", "Diode", "SMAJ5.0A"), "SMF5.0A", {"1": "VBUS", "2": "GND"}, "E2",
     fp="Diode_SMD:D_SOD-123F", lcsc="C151296", cls="estendida", price=0.05, status="final",
     note="TVS do VBUS (Pocket D60)", rot=90)
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
# power latch: click of I2 -> PWR_KEY, firmware KEEP, USB hold (only while on)
pmos("Q203", "SEL_SW_N", "VSYS", "PWR_KEY", "E3", note="o clique do seletor liga o EN")
R("R210", "100k", "VSYS", "SEL_SW_N", "E3")
R("R211", "100k", "PWR_KEY", "GND", "E3")
bat54c("D203", "PWR_KEY", "KEEP", "EN_REQ", "E3", note="OU do clique e do KEEP")
R("R212", "1M", "EN_REQ", "GND", "E3")
R("R213", "100k", "KEEP", "GND", "E3", note="KEEP baixo enquanto o P1 parte")
gate("U203", "08", "VBUS_S", "+3V3", "USB_HOLD", "+3V3", "E3",
     note="USB_HOLD = USB presente E aparelho ligado (alimentado pelo 3V3)")
R("R214", "10k", "VBUS", "VBUS_S", "E3")
R("R215", "100k", "VBUS_S", "GND", "E3")
C("C205", "100nF", "+3V3", "GND", "E3")
bat54c("D204", "USB_HOLD", "NC", "EN_REQ", "E3")
bat54c("D205", "SEL_SW", "ONOFF", "SEL_SW_N", "E3",
       note="o clique chega ao pino 6 e ao ONOFF do SNVS sem levar o VSYS a eles")
part("U204", sym("TPS63001", "Regulator_Switching"), "TPS63001DRCR",
     {"1": "+3V3", "2": "BB_L2", "3": "GND", "4": "BB_L1", "5": "VSYS", "6": "EN_E4", "7": "GND",
      "8": "BB_VINA", "9": "GND", "10": "+3V3", "11": "GND"}, "E4", fp="Package_SON:Texas_DRC0010J",
     lcsc="C28060", cls="estendida", price=1.40, status="final", note="3,3 V fixo; PS/SYNC baixo = economia",
     datasheet="https://www.ti.com/lit/ds/symlink/tps63001.pdf")
part("L201", sym("L", "Device"), "2.2uH", {"1": "BB_L1", "2": "BB_L2"}, "E4", fp="Inductor_SMD:L_Changjiang_FNR4020S",
     lcsc="C167825", cls="estendida", price=0.08, status="final", note="FNR4020S2R2MT (Pocket L10)", rot=90)
C("C206", "10uF", "VSYS", "GND", "E4", "0805")
C("C207", "10uF", "+3V3", "GND", "E4", "0805")
C("C208", "10uF", "+3V3", "GND", "E4", "0805")
R("R216", "100", "VSYS", "BB_VINA", "E4")
C("C209", "100nF", "BB_VINA", "GND", "E4")
part("U205", sym("XC6206P332MR", "Regulator_Linear", "XC6206PxxxMR"), "XC6206P332MR",
     {"1": "GND", "2": "SNVS_3V3", "3": "VSYS"}, "E5", fp="Package_TO_SOT_SMD:SOT-23-3", lcsc="C5446",
     cls="basica", price=0.02, status="conferir",
     note="sempre ligado (1 uA): alimenta o SNVS antes de tudo e a porta U206")
C("C210", "1uF", "VSYS", "GND", "E5")
C("C211", "1uF", "SNVS_3V3", "GND", "E5")
gate("U206", "08", "PMIC_ON_REQ", "EN_REQ", "EN_E4", "SNVS_3V3", "E5",
     note="EN de E4 = PMIC_ON_REQ E (clique OU KEEP OU USB_HOLD): 3,3 V so depois do SNVS")
C("C212", "100nF", "SNVS_3V3", "GND", "E5")
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
part("J301", sym("AudioJack3_SwitchT", "Connector_Audio"), "PJ-313D-6A",
     {"T": "HP_L", "R": "HP_R", "S": "HP_VGND", "TN": "HP_TIPSW"}, "F2", fp="", lcsc="C95463",
     cls="estendida", price=0.10, status="conferir",
     note="SMD, angulo reto; contato da ponta = deteccao; manga no HP_VGND, nunca no GND; footprint a criar no 3.3")
R("R303", "100k", "HP_TIPSW", "HP_DET", "F2")
R("R304", "1M", "HP_DET", "GND", "F2")
C("C308", "100nF", "HP_DET", "GND", "F2")

# ---------------------------------------------------------------- I: interface
CUR[0] = "I"
for ref, code, a, b, sw, what in (("SW401", "I1", "VOL_A", "VOL_B", "VOL_SW", "volume"),
                                  ("SW402", "I2", "SEL_A", "SEL_B", "SEL_SW_N", "seletor; clique de 2 s liga/desliga")):
    part(ref, sym("RotaryEncoder_Switch_MP", "Device"), "EC11E 15/15 com chave",
         {"A": a, "B": b, "C": "GND", "S1": "GND", "S2": sw, "MP": "GND"}, code,
         fp="Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm", lcsc="", cls="estendida", price=1.20,
         status="conferir", note=what + "; codigo LCSC da versao 15/15 a achar (C255515 e a 18/36)",
         datasheet="https://tech.alpsalpine.com/e/products/detail/EC11E15244G1/")
part("D401", sym("LED_Dual_AAKK", "Device"), "TJ-S1615SW6TGLCRG-A5", {"1": "LED_R_A", "2": "LED_G_A", "3": "GND",
     "4": "GND"}, "I3", fp="", lcsc="C273605", cls="estendida", price=0.02, status="conferir",
     note="1615 vermelho/verde, 4 pads; pinagem e footprint a conferir")
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
    "P": ["P · Processador: 'Teensy 4.1 na placa' (esquema da PJRC, sem Ethernet, USB host nem cartao SD).",
          "SNVS antes de tudo (E5); PMIC_ON_REQ habilita o 3,3 V (U206); PSWITCH sobe pelo MKL02 (PTA3) depois do 3,3 V, sem RC.",
          "Nunca ativar o modo seguro. Pinos 48-54 (EMC_22..29) ficam para a PSRAM; EMC_23 (G2) e SD_B1_05 (N3) sem ligacao."],
    "E": ["E · Energia: USB-C -> BQ24074 (USB500, 500 mA, NTC) -> VSYS -> TPS63001 (3,3 V).",
          "EN do TPS63001 = PMIC_ON_REQ E (clique do seletor OU KEEP OU USB com o aparelho ligado).",
          "E5: LDO sempre ligado para o SNVS. Luz de carga so com o aparelho desligado (Q202)."],
    "F": ["F · Fone: SGTL5000 como a Audio Board Rev D2. HP_VGND e terra virtual: NUNCA no GND.",
          "Contato da ponta do jack -> HP_DET (fone plugado = 0 V)."],
    "I": ["I · Interface: dois EC11E com clique (volume, seletor), LED vermelho/verde, botao Program.",
          "O clique do seletor vai ao GND; o liga/desliga esta na folha E."],
    "A": ["A · Alto-falante: MAX98357A no mesmo I2S do codec, mono (L+R)/2; SD_MODE pelo pino 12."],
    "T": ["T · Teclas: 28 TMAG5253BA3 no verso, 2 multiplexadores, grupos EN_A (canais 0-7) e EN_B (8-15).",
          "Espera de 45 us depois de trocar o S3. Canais iguais ao Pocket v0.3 (refazer no passo 3.4)."],
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
          '(comment 1 "etutti/hardware/viaggio/pcb/schematic.py escreve este arquivo; nao editar a mao"))' %
          (S.quote("eTutti Viaggio · %s · %s" % (sheet, title)), DATE, S.quote(REV)))
    txt = ('(kicad_sch\n\t(version 20250610)\n\t(generator "viaggio_schematic")\n\t(generator_version "10.0")\n'
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
        "eTutti Viaggio · esquema eletrico (SPEC v2, passo 3.1). Uma folha por setor da SPEC (secao 3).",
        "Campo 'Codigo' = codigo da peca na SPEC (P1...T4), o mesmo de concept/rev2/out/viaggio_rev2.json.",
        "Sem placa: nada posicionado nem roteado neste passo. Ligacoes entre folhas por rotulos globais.",
        "PWR_FLAG abaixo: redes alimentadas por conector, ferrite, indutor ou diodo (o ERC nao ve a fonte).",
    ]
    ntxt = "\n".join('\t(text %s (exclude_from_sim no) (at 25 %s 0) %s (uuid "%s"))' %
                     (S.quote(line), fmt(15 + 6 * i), eff("left", size=2.0), uid("rootnote", i))
                     for i, line in enumerate(notes))
    tb = ('\t(title_block (title "eTutti Viaggio · esquema") (date "%s") (rev %s) (company "beatconfused.com") '
          '(comment 1 "etutti/hardware/viaggio/pcb/schematic.py escreve este arquivo; nao editar a mao"))' %
          (DATE, S.quote(REV)))
    txt = ('(kicad_sch\n\t(version 20250610)\n\t(generator "viaggio_schematic")\n\t(generator_version "10.0")\n'
           '\t(uuid "%s")\n\t(paper "A4")\n%s\n' % (ROOT_UUID, tb))
    txt += lib_symbols_block({"PWR_FLAG"}) + ntxt + "\n" + "\n".join(sheets + body)
    txt += '\n\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n'
    open(os.path.join(KDIR, PROJECT + ".kicad_sch"), "w", encoding="utf-8", newline="\n").write(txt)


def write_library():
    syms = "\n\t".join(S.dump(SYMBOLS[n], 1) for n in sorted(SYMBOLS))
    open(os.path.join(KDIR, LIB + ".kicad_sym"), "w", encoding="utf-8", newline="\n").write(
        '(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "viaggio_schematic")\n\t(generator_version "10.0")\n\t'
        + syms + "\n)\n")
    open(os.path.join(KDIR, "sym-lib-table"), "w", newline="\n").write(
        '(sym_lib_table\n\t(version 7)\n\t(lib (name "%s") (type "KiCad") (uri "${KIPRJMOD}/%s.kicad_sym") '
        '(options "") (descr "eTutti Viaggio, written by schematic.py"))\n)\n' % (LIB, LIB))
    pro = os.path.join(KDIR, PROJECT + ".kicad_pro")
    if not os.path.exists(pro):
        json.dump({"meta": {"filename": PROJECT + ".kicad_pro", "version": 3},
                   "sheets": [[ROOT_UUID, "Root"]] + [[SHEET_UUID[s], "%s · %s" % (s, t)] for s, t in SHEETS]},
                  open(pro, "w"), indent=2)


def check_footprints():
    missing = []
    for s in PARTS:
        for p in PARTS[s]:
            if p["fp"]:
                lib, name = p["fp"].split(":")
                if not os.path.exists(os.path.join(KICAD_FP, lib + ".pretty", name + ".kicad_mod")):
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
    path = os.path.join(HERE, "bom_preliminar.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "referencias", "qtd", "valor_peca", "encapsulamento", "lcsc", "classe_jlc",
                    "preco_unit_usd_est", "montagem", "status", "nota"])
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
    erc = os.path.join(BUILD, "viaggio_erc.json")
    subprocess.run([KICAD_CLI, "sch", "erc", "--format", "json", "--severity-all", "-o", erc, root],
                   check=False, capture_output=True)
    rep = json.load(open(erc, encoding="utf-8"))
    counts = {}
    for sh in rep.get("sheets", []):
        for v in sh.get("violations", []):
            counts.setdefault(v["severity"], []).append((sh.get("path"), v["type"], v["description"],
                                                         [i.get("description") for i in v.get("items", [])]))
    net = os.path.join(BUILD, "viaggio_netlist.net")
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
