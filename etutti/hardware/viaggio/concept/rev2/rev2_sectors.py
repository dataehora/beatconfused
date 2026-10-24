"""eTutti Viaggio Rev2 -- stage 2 (approved by J, 24 Oct 2026): sectors, part codes and routing corridors.

Writes out/viaggio_rev2.json (the placement contract for the electronics) and out/viaggio_rev2.svg.

Coding (three kinds, three shapes):
  sector  = coloured area, letter + name (P Processador, E Energia, F Fone, I Interface, A Alto-falante, T Teclas)
  part    = circle, sector letter + number (P1 ... T4), circle in the sector colour
  corridor= rounded square, C1 ... C7
"""
import json, sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import rev2_layout as g

g.zones[:] = []          # stage-1 dashed zones replaced by the sectors below
base = g.svg("ambos")
base = re.sub(r'<g class="L-\w+ tag"[^>]*>.*?</g>', "", base, flags=re.S)   # drop stage-1 numbers

COLS = {"P": "#5fa8d3", "E": "#e0a35f", "F": "#b48ae0", "I": "#6fd08c", "A": "#e07fb0", "T": "#e6c25a"}
NAMES = {"P": "Processador", "E": "Energia", "F": "Fone", "I": "Interface", "A": "Alto-falante", "T": "Teclas"}

# stage-1 number -> (code, short name)
CODE = {
    10: ("P1", "Processador i.MX RT1062 (BGA 12 × 12)"),
    11: ("P2", "Bootloader PJRC MKL02"),
    12: ("P3", "Flash 64 Mbit"),
    26: ("P4", "PSRAM (só o lugar)"),
    13: ("P5", "Cristais 24 MHz e 32,768 kHz (relógios do processador)"),
    1:  ("E1", "USB-C (energia e dados)"),
    24: ("E2", "Proteção ESD do USB"),
    15: ("E3", "Carregador BQ24074 + trava liga/desliga"),
    16: ("E4", "Conversor 3,3 V TPS63001 + indutor"),
    17: ("E5", "Regulador do SNVS e partida do processador"),
    19: ("E6", "Conector da bateria"),
    14: ("F1", "Codec SGTL5000"),
    2:  ("F2", "Jack do fone"),
    3:  ("I1", "Volume (encoder com clique)"),
    4:  ("I2", "Seletor (encoder com clique)"),
    5:  ("I3", "LED bicolor"),
    20: ("I4", "Botão Program (por baixo)"),
    18: ("A1", "Amplificador MAX98357A"),
    6:  ("A2", "Alto-falante"),
    21: ("T1", "Mux esquerdo"),
    22: ("T2", "Mux direito"),
    23: ("T3", "Portas do liga/desliga dos sensores"),
}

# sector areas (polygons)
SECT = {
    "P": [(21, 3.5), (53.5, 3.5), (53.5, 31), (21, 31)],
    "E": [(55, 3.5), (80, 3.5), (80, 30), (55, 30)],
    "E2": [(3, 6.5), (19.5, 6.5), (19.5, 19), (3, 19)],
    "F": [(3, 20), (33, 20), (33, 40), (3, 40)],
    "I": [(12, 41.5), (35, 41.5), (35, 32), (58, 32), (58, 57), (12, 57)],
    "A": [(12, 59), (70, 59), (70, 97), (12, 97)],
    "T": [(82, 3.5), (234, 3.5), (234, 95.5), (82, 95.5)],
}
LABEL_AT = {"P": (22.6, 30), "E": (56.4, 28.6), "F": (4.4, 38.8), "I": (53.8, 55.8), "A": (58.2, 64.8), "T": (227, 93.6)}

# corridors: (code, from-to, points)
COR = [
    ("C1", "USB", [(9.5, 13), (22, 14)], "#5fa8d3"),
    ("C2", "VBUS", [(8, 8.5), (30, 4.6), (58, 4.6), (62, 8)], "#e0a35f"),
    ("C3", "teclas", [(196, 13.5), (97, 13.5), (86, 28), (58, 33), (44, 31), (38, 22)], "#e6c25a"),
    ("C4", "fone", [(22, 34), (12, 26)], "#b48ae0"),
    ("C5", "I2S", [(40, 23), (46, 35), (46, 70), (52, 85)], "#e07fb0"),
    ("C6", "SYS", [(76, 21), (72, 45), (66, 76), (58, 86)], "#e0a35f"),
    ("C7", "bateria", [(64.5, 23.5), (62, 11.5)], "#e0a35f"),
]
DASHED = {"C5", "C6"}
CORPOS = {"C1": (18, 18.4), "C2": (40, 4.6), "C3": (130, 13.5), "C4": (17, 30), "C5": (46, 66), "C6": (68, 66), "C7": (58.4, 19)}


def poly(pts):
    return " ".join(f"{x},{y}" for x, y in pts)


ov = ['<g class="ov-sect">']
for k, pts in SECT.items():
    c = COLS[k[0]]
    ov.append(f'<polygon points="{poly(pts)}" fill="{c}" fill-opacity=".18" stroke="{c}" stroke-width=".6" stroke-linejoin="round"/>')
for k, (x, y) in LABEL_AT.items():
    c = COLS[k]
    ov.append(f'<text x="{x}" y="{y}" font-size="6" font-weight="700" fill="{c}" stroke="#0b2418" stroke-width="1" paint-order="stroke" '
              f'font-family="IBM Plex Sans,Arial,sans-serif">{k}</text>')
ov.append('</g><g class="ov-cor">')
for code, lab, pts, c in COR:
    da = ' stroke-dasharray="2 1"' if code in DASHED else ""
    ov.append(f'<polyline points="{poly(pts)}" fill="none" stroke="#0b2418" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" opacity=".7"/>'
              f'<polyline points="{poly(pts)}" fill="none" stroke="{c}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"{da}/>')
ov.append('</g>')
# proposed new spot for E6

# part tags: circle in the sector colour
ov.append('<g class="ov-parts">')
for p in g.parts:
    if p["n"] not in CODE:
        continue
    code, _ = CODE[p["n"]]
    c = COLS[code[0]]
    tx, ty = p["cx"], p["cy"]
    if p["kind"] == "spk":
        ty = p["cy"] - 10
    ov.append(f'<g class="pt" data-c="{code}"><circle cx="{tx:.2f}" cy="{ty:.2f}" r="2.9" fill="{c}" stroke="#111" stroke-width=".3"/>'
              f'<text x="{tx:.2f}" y="{ty+0.95:.2f}" font-size="2.6" text-anchor="middle" fill="#111" font-weight="700" font-family="IBM Plex Mono,monospace">{code}</text></g>')
# T4: the 28 sensors, one sample tag
ov.append('<g class="pt" data-c="T4"><circle cx="113" cy="34.5" r="2.9" fill="#e6c25a" stroke="#111" stroke-width=".3"/>'
          '<text x="113" y="35.45" font-size="2.6" text-anchor="middle" fill="#111" font-weight="700" font-family="IBM Plex Mono,monospace">T4</text></g>')
ov.append('</g><g class="ov-cor">')
for code, lab, pts, c in COR:
    x, y = CORPOS[code]
    ov.append(f'<g><rect x="{x-3.4}" y="{y-2.3}" width="6.8" height="4.6" rx="1" fill="#0b2418" stroke="{c}" stroke-width=".6"/>'
              f'<text x="{x}" y="{y+0.95}" font-size="2.6" text-anchor="middle" fill="{c}" font-weight="700" font-family="IBM Plex Mono,monospace">{code}</text></g>')
ov.append('</g>')

svg = base.replace("</svg>", "\n".join(ov) + "\n</svg>")

os.makedirs("out", exist_ok=True)
open("out/viaggio_rev2.svg", "w", encoding="utf-8").write(svg.replace("var(--bg)", "#ffffff").replace("currentColor", "#222"))

CONTRACT = {
    "version": "Rev2 / SPEC v2, 24 Oct 2026",
    "units": "mm; x right, y towards the player (front), origin top-left of the drawing",
    "board": {"rect": [g.BX0, g.BY0, g.BX1, g.BY1], "corner_radius": g.BR, "layers": 4, "thickness": 1.2},
    "profile_a": [[round(x, 2), round(y, 2)] for x, y in g.P],
    "interface_limit": [[round(x, 2), round(y, 2)] for x, y in g.IFACE],
    "keys": [{"note": k["note"], "x": k["x"], "y": k["y"]} for k in g.keys],
    "holes_m2": [[round(x, 2), round(y, 2)] for x, y in g.holes],
    "sectors": {k: {"name": NAMES[k[0]], "polygon": v} for k, v in SECT.items()},
    "parts": [dict(code=CODE[p["n"]][0], name=CODE[p["n"]][1], side=p["side"], x=round(p["cx"], 2), y=round(p["cy"], 2),
                   w=p["w"], h=p["h"], rot=round(p["rot"], 1)) for p in g.parts if p["n"] in CODE]
             + [{"code": "T4", "name": "28 TMAG5253, one under each key, bottom side", "side": "bot", "at": "keys"}],
    "corridors": [{"code": c, "carries": lab, "path": pts} for c, lab, pts, _ in COR],
}
json.dump(CONTRACT, open("out/viaggio_rev2.json", "w", encoding="utf-8"), ensure_ascii=False)
print("out/viaggio_rev2.json:", len(CONTRACT["parts"]), "parts,", len(CONTRACT["corridors"]), "corridors")
