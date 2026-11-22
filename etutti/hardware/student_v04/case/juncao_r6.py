"""eTutti Student V4 (R6V4, item 1, design part): the fixed-connector joints between two rulers of a row, as plain data (no CadQuery).

Frame of a joint (all in mm):
  u = along the row, 0 at the junction line (the right ruler's start; + = right ruler, - = left ruler);
  v = across, 0 at the row's axis, + towards the player (the key pegs and sensors are on v = 0, the rails at |v| 4.2..7.0);
  d = depth BELOW THE RULER'S UNDERSIDE (parts are only on the underside: the top carries the keys' housings).
Absolute: x = xj + u, y = y_row + v, z = ZR - 1.2 - d.

Every dimension marked EST is an ESTIMATE from catalogue descriptions (Chat's spec_img/juncao_r6.py, plus my own reading); the electronics agent
brings the real parts with manufacturer drawings (ELETRONICA.md R6V4): change the numbers in OPTIONS and re-run juncao_v6.py. "a confirmar" until then.

Real geometry the options are tested against (FIT_CHECK R4V4/R5V4): ruler body 73.6 x 14.0 x 1.2 (pitch 74.0, 0.4 gap); key pegs D1.7 at u = +-4.17 from the
junction on the right/left (first/last key centre 9.25 from the ruler's end, pegs +-5.08 from it), the sensors' pockets +-1.1 in v at the key centres;
rails |v| 4.2..7.0; pocket under the ruler: floor at z -8.1, i.e. d_floor = ZR + 6.9 (6.9 mm under row 1's ruler, 8.9 / 10.9 / 13.9 under rows 2 / 3 / 4).
"""
import json
import os

import layout_r4 as L

HERE = os.path.dirname(os.path.abspath(__file__))
T = L.RULER_T
D_FLOOR = {r: L.ZR[r - 1] - T - L.Z_FLOOR for r in (1, 2, 3, 4)}                     # 6.9, 8.9, 10.9, 13.9

# ---------------------------------------------------------------- the electronics' ruler parts (posicao_regua.json), to test the joint's footprint against
RULER_JSON = os.path.join(HERE, "..", "pcb", "regua", "posicao_regua.json")


def ruler_parts():
    """Parts of the ruler's underside as (ref, u0, u1, v0, v1, height) in the ruler's own u (0 = its start at the nominal pitch line), v."""
    d = json.load(open(RULER_JSON, encoding="utf-8"))
    out = []
    for ref, p in d["pecas"].items():
        if p["lado"] != "B":
            continue
        h = float(p["altura_mm"] or 0.0)
        a, b, c, e = p["patio_uv"]
        out.append((ref, a, c, b, e, h))
    return out


# ---------------------------------------------------------------- the options
# part = (name, role, u0, u1, v0, v1, d0, d1)
def _E1(female_depth, male_depth):
    """J's idea taken literally: right-angle male at the END of ruler A (pins towards +u) into a right-angle female at the START of ruler B; the row of
    5 contacts lies along v (across the ruler), crossing the axis; 1.27 pitch. EST: housing + pads of the female 5.6 deep (Chat), male 3.1 + pins 2.9."""
    return [
        ("macho (corpo + pads)", "macho", -0.2 - male_depth, -0.2, -3.4, 3.4, 0.0, 3.4),
        ("pinos do macho", "pino", -0.2, 2.7, -2.7, 2.7, 1.5, 1.9),
        ("fêmea (corpo + pads)", "femea", 0.2, 0.2 + female_depth, -3.4, 3.4, 0.0, 3.4),
    ]


E2_SOCK_U = (0.5, 7.4)                 # (E2b / F estimates only) a socket's footprint along u from the ruler's end
E2_V = (1.25, 3.8)                     # (E2b / F estimates) the front lane
E2_H_SOCK, E2_H_HOUS, E2_H_PCB = 3.4, 1.0, 0.8
# E2 with the REAL parts of ELETRONICA.md R6V4 (conferir): female SHOU HAN PM1.27-1x5PLT-H3.4-R C55566451 (footprint 6.76 x 5.2, insulator 3.4) at u = 5.9 / 68.1
# in the BACK lane (v -6.9..-1.7: the front lane has only 3.1 mm), male SHOU HAN PZ1.27-1x5PLT-L7.2-R C55213903 (1.0 plastic, 4 mm pin: 0.6 mm of plastic stays
# out of the 3.4 socket), bridge PCB 1.2 mm (same panel as the rulers; 0.8 mm would give 5.8).
E2_SOCK = (6.76, (-6.9, -1.7), 3.4)
E2_GAP, E2_MALE, E2_BRIDGE = 0.6, 1.0, 1.2


def _bridge_male():
    w, (v0, v1), hs = E2_SOCK
    out = []
    for s in (-1, 1):
        c = s * L.IN_X
        u0, u1 = c - w / 2, c + w / 2
        nm = "A" if s < 0 else "B"
        out.append(("fêmea 1x5 H3.4 (régua %s)" % nm, "femea", u0, u1, v0, v1, 0.0, hs))
        out.append(("macho 1x5 da ponte (régua %s)" % nm, "macho", c - 3.2, c + 3.2, v0 + 0.8, v1 - 0.8, hs + E2_GAP, hs + E2_GAP + E2_MALE))
    top = hs + E2_GAP + E2_MALE
    out.append(("ponte (PCB %.1f)" % E2_BRIDGE, "ponte", -L.IN_X - w / 2 - 0.5, L.IN_X + w / 2 + 0.5, v0 - 0.05, v1 + 0.05, top, top + E2_BRIDGE))
    return out


def _bridge_female():
    """E2b: male 1x5 SMD headers on the rulers (pins down) + a bridge with two female sockets on top."""
    a, b = E2_SOCK_U
    hm, hf = 1.5, 3.4
    out = []
    for s in (-1, 1):
        u0, u1 = (-b, -a) if s < 0 else (a, b)
        out.append(("macho 1x5 (régua %s)" % ("A" if s < 0 else "B"), "macho", u0, u1, E2_V[0], E2_V[1], 0.0, hm))
        out.append(("fêmea 1x5 da ponte", "femea", u0, u1, E2_V[0], E2_V[1], hm, hm + hf))
    out.append(("ponte (PCB 16,4 x 3,0 x 0,8)", "ponte", -8.2, 8.2, 0.95, 3.95, hm + hf, hm + hf + E2_H_PCB))
    return out


def _spring():
    """F: spring contacts (SMD pogo, 2.0 pitch, 3.6 free / 3.0 mounted) on a bridge PCB pressing onto 5 + 5 gold pads of the rulers (no part on the ruler)."""
    out = []
    pos = [1.4 + 2.0 * i for i in range(5)]
    for s in (-1, 1):
        for i, p in enumerate(pos):
            uc = s * p
            out.append(("mola %d (régua %s)" % (i + 1, "A" if s < 0 else "B"), "mola", uc - 0.75, uc + 0.75, 1.75, 3.25, 0.0, 3.0))
    out.append(("ponte (PCB 20,8 x 3,0 x 0,8)", "ponte", -10.4, 10.4, 0.95, 3.95, 3.0, 3.8))
    return out


OPTIONS = {
    "E1": {"titulo": "E1 · macho em ângulo (A) × fêmea em ângulo (B), pinos ao longo de x", "parts": _E1(5.6, 3.1), "ponte": False,
           "montagem": "deslizar a régua B ~3 mm em x contra a A (fileira montada da direita para a esquerda)",
           "est": "fêmea 4,2 + pads 1,4 = 5,6 de fundo, macho 1,7 + 1,4, pinos 2,9 (esboço do Chat)"},
    "E1c": {"titulo": "E1c · o mesmo com fêmea e macho de <= 3,3 mm de fundo, pads incluídos (peça hipotética)", "parts": _E1(3.1, 3.1), "ponte": False,
            "montagem": "idem E1", "est": "peça hipotética: ninguém vende 5 vias a 1,27 em ângulo com 3,3 mm"},
    "E2": {"titulo": "E2 · 2 fêmeas iguais (boca para baixo) + ponte com 2 machos 1x5, por baixo", "parts": _bridge_male(), "ponte": True,
           "montagem": "a ponte descansa no berço da bandeja; as duas réguas descem na vertical sobre os machos e são aparafusadas",
           "est": "peças reais da eletrônica (C55566451, C55213903), faixa de trás; medidas do footprint H4.3 (conferir)"},
    "E2b": {"titulo": "E2b · 2 machos nas réguas (pinos para baixo) + ponte com 2 fêmeas", "parts": _bridge_female(), "ponte": True,
            "montagem": "idem E2, mas com pinos expostos sob a régua enquanto ela não está ligada", "est": "macho SMD 1,5 + fêmea 3,4 (EST)"},
    "F": {"titulo": "F · contatos de mola (pogo SMD) na ponte contra pads dourados da régua", "parts": _spring(), "ponte": True,
          "montagem": "a ponte descansa no berço; as réguas descem e comprimem as molas 0,6 mm; o parafuso M2 dá a pré-carga",
          "est": "mola 3,6 livre / 3,0 montada, passo 2,0, ponte 20,8 (EST)"},
}


def bridge_bottom(opt):
    return max(p[7] for p in OPTIONS[opt]["parts"])


def cradle(opt, row):
    """The tray's cradle for the bridge of a row: a block under the bridge (0.2 mm from it, to the floor) and two end lips (0.3 mm from the bridge's ends).
    Returns [(name, u0, u1, v0, v1, d0, d1)] (d from the ruler's underside down to the floor)."""
    parts = OPTIONS[opt]["parts"]
    if not OPTIONS[opt]["ponte"]:
        return []
    br = [p for p in parts if p[1] == "ponte"][0]
    dfl = D_FLOOR[row]
    out = [("bloco do berço", br[2] + 1.0, br[3] - 1.0, br[4] + 0.5, br[5] - 0.5, br[7] + 0.2, dfl)]
    for s in (-1, 1):
        u0, u1 = (br[3] + 0.3, br[3] + 1.5) if s > 0 else (br[2] - 1.5, br[2] - 0.3)
        out.append(("aba do berço", u0, u1, br[4], br[5], br[6], dfl))
    return out


def height_total(opt):
    return bridge_bottom(opt)


def to_box(part, xj, y, z0):
    """Absolute (x0, x1, y0, y1, z0, z1) of a part (name, role, u0, u1, v0, v1, d0, d1) at a junction (xj, y) of a row whose ruler top is at z0."""
    _n, _r, u0, u1, v0, v1, d0, d1 = part[:8]
    zu = z0 - T
    return (xj + u0, xj + u1, y + v0, y + v1, zu - d1, zu - d0)


def to_box_cradle(c, xj, y, z0):
    _n, u0, u1, v0, v1, d0, d1 = c
    zu = z0 - T
    return (xj + u0, xj + u1, y + v0, y + v1, zu - d1, zu - d0)


def bridges(mod):
    """The joints of every row: (row, xj, y, z0)."""
    out = []
    rs = L.rulers(mod)
    for r, y, x0, n in L.ROWS:
        row = [q for q in rs if q["row"] == r]
        for a, b in zip(row[:-1], row[1:]):
            out.append((r, b["x0"], y, L.ZR[r - 1]))
    return out


def ruler_part_boxes(xj, y, z0, skip=("J1", "J2", "LK1", "LK2")):
    """The electronics' parts of the two rulers next to a joint, in absolute coordinates (the underside, d 0..height)."""
    zu = z0 - T
    out = []
    for side, x_start in (("A", xj - L.RULER_L), ("B", xj)):
        for ref, u0, u1, v0, v1, h in ruler_parts():
            if ref.startswith(("PEG", "H")) or h <= 0 or ref in skip:
                continue
            out.append(("%s.%s" % (ref, side), (x_start + u0, x_start + u1, y + v0, y + v1, zu - h, zu)))
    return out
