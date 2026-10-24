"""eTutti Viaggio Rev2 -- 2D plan approved by J (stage 1, 24 Oct 2026). Concept placement, not routed.

Stdlib only. Imported by rev2_sectors.py, which writes the contract out/viaggio_rev2.json.
"""
import json, math, html

import os
HERE = os.path.dirname(os.path.abspath(__file__))
POCKET = os.path.join(HERE, "..", "..", "..", "pocket", "build", "pocket.json")
d = json.load(open(POCKET))
P = d["inner"]                      # option A profile (reference line, dotted on the silkscreen)
BX0, BY0, BX1, BY1, BR = 2.5, 2.5, 249.0, 97.5, 5.0   # Rev2 board: rectangle, R 5 corners (free at JLCPCB)
def _rr():
    import math as _m
    pts = []
    for cx, cy, a0 in ((BX1 - BR, BY0 + BR, -90), (BX1 - BR, BY1 - BR, 0), (BX0 + BR, BY1 - BR, 90), (BX0 + BR, BY0 + BR, 180)):
        for i in range(10):
            a = _m.radians(a0 + 90 * i / 9); pts.append((cx + BR * _m.cos(a), cy + BR * _m.sin(a)))
    return pts
BOARD = _rr()
keys = d["keys"]


def left_x(y):
    xs = []
    for i in range(len(P)):
        (x0, y0), (x1, y1) = P[i], P[(i + 1) % len(P)]
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return min(xs)


XC = (min(k["x"] for k in keys) + max(k["x"] for k in keys)) / 2   # keyboard is mirror-symmetric about x = XC


def right_x(y):
    xs = []
    for i in range(len(P)):
        (x0, y0), (x1, y1) = P[i], P[(i + 1) % len(P)]
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return max(xs)


def iface_x(y):
    """Interface/keyboard boundary: the right edge mirrored, so the keyboard keeps the same buffer on both sides."""
    return 2 * XC - right_x(y)


IFACE = [(iface_x(2.5 + 95 * i / 190), 2.5 + 95 * i / 190) for i in range(191)]


def edge_angle(y):
    """Angle (deg) of the outward normal of the left edge at height y."""
    dy = 1.0
    x0, x1 = left_x(y - dy), left_x(y + dy)
    tx, ty = x1 - x0, 2 * dy                      # tangent going +y
    nx, ny = -ty, tx                              # rotate to point outwards (-x)
    return math.degrees(math.atan2(ny, nx))


# ---------------- parts ----------------
# side: "top" or "bot"; asm: "JLC" (montada pela JLCPCB), "casa" (encaixada/soldada em casa), "consig" (JLC, peça enviada)
parts = []
def part(n, name, side, cx, cy, w, h, asm, kind, label=None, rot=0, shape="rect"):
    parts.append(dict(n=n, name=name, side=side, cx=cx, cy=cy, w=w, h=h, asm=asm, kind=kind,
                      label=label or name, rot=rot, shape=shape))

usb_y, jack_y = 22.0, 35.0
ux, jx = left_x(usb_y), left_x(jack_y)
ua, ja = edge_angle(usb_y), edge_angle(jack_y)

# top side
GHOST = [(ux + 3.6, usb_y, 8.9, 7.35, ua + 180), (jx + 6.6, jack_y, 12.0, 6.0, ja + 180)]   # rev1 positions, kept as a dashed outline
part(1, "USB-C (receptáculo USB 2.0, 16 vias) + 2 × 5,1 kΩ nos CC", "top", 2.5 + 7.35 / 2, 13.0, 7.35, 8.94, "JLC", "con", "USB-C")
part(2, "Jack de fone 3,5 com contato na ponta (SMD)", "top", 2.5 + 6.0, 25.0, 12.0, 6.0, "JLC", "con", "fone")
part(3, "Volume (encoder EC11E vertical, com clique · o mesmo do seletor)", "top", 20.0, 49.0, 12.4, 13.2, "JLC", "knob", "vol")
part(4, "Seletor (encoder EC11E vertical, com clique · segurar 2 s liga/desliga)", "top", 36.0, 49.0, 12.4, 13.2, "JLC", "knob", "sel")
part(5, "LED bicolor (SMD sob light pipe)", "top", 50.0, 49.0, 3.5, 3.5, "JLC", "led", "LED", shape="circle")
part(6, "Alto-falante fino Ø36 (~4,6 mm, fios na placa)", "top", 31.0, 78.0, 36.0, 36.0, "casa", "spk", "alto-falante", shape="circle")
part(7, "Área do logo (serigrafia / case)", "top", 52.0, 15.0, 40.0, 14.0, "—", "logo", "logo")

# bottom side (seen from the top, X-ray)
part(10, "i.MX RT1062 (LFBGA-196, 12 × 12, passo 0,8) — o processador do Teensy 4.1", "bot", 34.0, 15.5, 12.0, 12.0, "JLC", "mcu", "RT1062")
part(11, "Bootloader PJRC MKL02 (QFN-16)", "bot", 46.0, 9.0, 3.0, 3.0, "consig", "mcu", "MKL02")
part(12, "Flash 64 Mbit W25Q64JV (SOIC-8)", "bot", 47.5, 18.0, 5.3, 5.3, "JLC", "mcu", "flash")
part(26, "PSRAM 8 MB APS6404L (SOIC-8) · lugar, sem montar", "bot", 47.5, 26.5, 5.3, 5.3, "—", "mcu", "PSRAM")
part(13, "Cristal 24 MHz", "bot", 26.0, 23.0, 3.2, 2.5, "JLC", "mcu", "24M")
part(14, "Codec de áudio SGTL5000 (QFN-20)", "bot", 24.0, 35.5, 3.0, 3.0, "JLC", "audio", "SGTL5000")
part(15, "Carregador BQ24074 (power-path, NTC) + trava de liga/desliga", "bot", 62.0, 9.0, 3.0, 3.0, "JLC", "pwr", "BQ24074")
part(16, "Buck-boost TPS63001 + indutor 2,2 µH", "bot", 72.0, 9.0, 7.5, 4.0, "JLC", "pwr", "3V3")
part(17, "LDO 1,1 V do SNVS e controle de partida do RT1062", "bot", 66.0, 17.0, 5.0, 4.0, "JLC", "pwr", "SNVS")
part(18, "Amplificador I2S MAX98357A (QFN-16)", "bot", 54.0, 88.0, 3.0, 3.0, "JLC", "audio", "amp")
part(19, "Conector da bateria JST PH 3 vias (NTC)", "bot", 64.5, 26.5, 8.0, 6.0, "JLC", "con", "BAT")
part(20, "Botão de gravação (Program), acessível por baixo", "bot", 52.0, 36.0, 4.5, 4.5, "JLC", "btn", "PROG")
part(21, "Multiplexador CD74HC4067 (TSSOP-24) · metade esquerda", "bot", 118.0, 10.5, 7.8, 4.4, "JLC", "mux", "MUX1")
part(22, "Multiplexador CD74HC4067 (TSSOP-24) · metade direita", "bot", 182.0, 10.5, 7.8, 4.4, "JLC", "mux", "MUX2")
part(23, "Portas do EN por grupo (74LVC1G04 + 2× 74LVC1G08)", "bot", 150.0, 10.5, 9.0, 3.0, "JLC", "mux", "EN")
part(24, "ESD do USB-C (D+, D−, VBUS)", "bot", 14.0, 13.0, 3.0, 2.0, "JLC", "pwr", "ESD")

# mounting holes (M2) between keys + interface corners
holes = [(88.0, 6.5), (74.0, 93.0), (6.0, 60.0), (55.0, 63.0)]
for (x0, y0), (x1, y1) in [((135.6, 58.0), (0, 0))]:
    pass
# put holes at centres of some 3-key triangles of the hex grid
kxy = [(k["x"], k["y"]) for k in keys]
def tri_centres():
    out = []
    for a in kxy:
        for b in kxy:
            for c in kxy:
                if a < b < c and all(abs(math.dist(p, q) - 18.5) < 0.2 for p, q in ((a, b), (b, c), (a, c))):
                    out.append(((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3))
    return out
tc = tri_centres()
for target in ((100, 50), (150, 34), (150, 66), (205, 50)):
    best = min(tc, key=lambda p: math.dist(p, target))
    holes.append(best)

COL = {"con": "#c8a24a", "knob": "#9aa3ad", "led": "#6fd08c", "spk": "#b9b2a4", "logo": "none", "mcu": "#2b2f36",
       "audio": "#3a2f4a", "pwr": "#40342a", "btn": "#d6d6d6", "mux": "#2b2f36", "bat": "#c9c3b6"}

def poly(pts):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)

def rect_svg(p, cls):
    x, y, w, h = p["cx"] - p["w"] / 2, p["cy"] - p["h"] / 2, p["w"], p["h"]
    col = COL[p["kind"]]
    tr = f' transform="rotate({p["rot"]:.1f} {p["cx"]:.2f} {p["cy"]:.2f})"' if p["rot"] else ""
    if p["shape"] == "circle":
        body = f'<circle cx="{p["cx"]}" cy="{p["cy"]}" r="{p["w"]/2}" class="{cls}" fill="{col}" />'
        if p["kind"] == "spk":
            body = (f'<circle cx="{p["cx"]}" cy="{p["cy"]}" r="{p["w"]/2}" class="{cls}" fill="{col}" fill-opacity=".55" stroke="#ece6d6" stroke-width=".4"/>'
                    f'<circle cx="{p["cx"]}" cy="{p["cy"]}" r="{p["w"]/2-5}" class="{cls}" fill="none" stroke="#ece6d6" stroke-width=".3" stroke-dasharray="1 1"/>')
        return body
    if p["kind"] == "logo":
        return (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w}" height="{h}" rx="2" fill="none" stroke="#f2f0e8" stroke-width=".35" stroke-dasharray="1.2 1" class="{cls}"/>'
                f'<text x="{p["cx"]}" y="{p["cy"]+1.6}" font-size="5.2" text-anchor="middle" fill="#f2f0e8" font-family="Georgia,serif" font-weight="700" class="{cls}">eTutti</text>'
                f'<text x="{p["cx"]}" y="{p["cy"]+5.2}" font-size="2.4" text-anchor="middle" fill="#f2f0e8" letter-spacing=".5" font-family="Arial,sans-serif" font-weight="700" class="{cls}">VIAGGIO</text>')
    if p["kind"] == "bat":
        return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w}" height="{h}" rx="2.5" fill="{col}" fill-opacity=".22" stroke="{col}" stroke-width=".5" stroke-dasharray="2 1.2" class="{cls}"/>'
    extra = ""
    if p["kind"] == "knob":
        extra = f'<circle cx="{p["cx"]}" cy="{p["cy"]}" r="3" fill="#d8dde2" stroke="#5c646c" stroke-width=".3" class="{cls}"/>'
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w}" height="{h}" rx=".6" fill="{col}" stroke="#ffffff" stroke-opacity=".35" stroke-width=".25"{tr} class="{cls}"/>' + extra

zones = [  # (label, side, x, y, w, h, colour)
    ("processador (equivale ao Teensy 4.1)", "bot", 22.0, 4.0, 30.0, 23.0, "#5fa8d3"),
    ("áudio", "bot", 18.0, 30.0, 12.0, 11.0, "#b48ae0"),
    ("energia", "bot", 56.0, 4.0, 22.0, 18.0, "#e0a35f"),
    ("amplificador e conector da bateria", "bot", 50.0, 84.0, 18.5, 11.5, "#b48ae0"),
]

def svg(view):
    W, H = 252, 101
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-6 -8 {W+12} {H+18}" class="board" role="img" aria-label="Layout da placa, vista {view}">',
         '<defs><pattern id="hatch" width="2" height="2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="1" height="2" fill="#ffffff" fill-opacity=".05"/></pattern></defs>',
         f'<polygon points="{poly(BOARD)}" fill="#1f5a3c"/>',
         f'<polygon points="{poly(BOARD)}" fill="url(#hatch)" stroke="#d9c88a" stroke-width=".6"/>',
         f'<polygon points="{poly(P)}" fill="none" stroke="#f2f0e8" stroke-width=".5" stroke-dasharray=".6 1.2" stroke-linecap="round"/>']
    # keyboard switch cutouts & sensors
    for k in keys:
        x, y = k["x"], k["y"]
        s.append(f'<rect x="{x-7}" y="{y-7}" width="14" height="14" rx=".8" fill="#163f2b" stroke="#f2f0e8" stroke-opacity=".7" stroke-width=".3" class="L-top"/>')
        s.append(f'<circle cx="{x}" cy="{y}" r="7.5" fill="{"#111" if k["sharp"] else "#f7f6f1"}" fill-opacity=".85" class="L-top"/>')
        s.append(f'<text x="{x}" y="{y+1.1}" font-size="3.1" text-anchor="middle" fill="{"#eee" if k["sharp"] else "#222"}" class="L-top" font-family="IBM Plex Mono,monospace">{k["note"].replace("#","♯")}</text>')
        s.append(f'<rect x="{x-.7}" y="{y-.55}" width="1.4" height="1.1" fill="#e6c25a" class="L-bot"/>')
        s.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="none" stroke="#e6c25a" stroke-width=".25" stroke-dasharray=".6 .6" class="L-bot"/>')
    for x, y in holes:
        s.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.3" fill="#d9c88a"/><circle cx="{x:.2f}" cy="{y:.2f}" r="1.1" fill="var(--bg)"/>')
    for (lab, side, x, y, w, h, c) in zones:
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="1.5" fill="{c}" fill-opacity=".14" stroke="{c}" stroke-width=".4" stroke-dasharray="1.5 1" class="L-{side}"/>')
    for gx, gy, gw, gh, gr in GHOST:
        s.append(f'<rect x="{gx-gw/2:.2f}" y="{gy-gh/2:.2f}" width="{gw}" height="{gh}" rx=".6" fill="none" stroke="#c8a24a" stroke-width=".4" stroke-dasharray="1.2 .9" transform="rotate({gr:.1f} {gx:.2f} {gy:.2f})" class="L-top"/>')
    s.append('<text x="4.5" y="42.5" font-size="2.3" fill="#e8d9a6" font-family="IBM Plex Mono,monospace" class="L-top">posição rev1</text>')
    for p in parts:
        s.append(rect_svg(p, "L-" + p["side"]))
    # number tags
    for p in parts:
        if p["kind"] == "logo":
            continue
        tx, ty = p["cx"], p["cy"]
        if p["kind"] in ("spk", "bat"):
            ty = p["cy"] - p["h"] / 2 + 4 if p["kind"] == "bat" else p["cy"] - 10
        s.append(f'<g class="L-{p["side"]} tag" data-n="{p["n"]}"><circle cx="{tx:.2f}" cy="{ty:.2f}" r="2.4" fill="{"#ffffff" if p["side"]=="top" else "#ffd166"}" stroke="#111" stroke-width=".25"/>'
                 f'<text x="{tx:.2f}" y="{ty+1.0:.2f}" font-size="2.7" text-anchor="middle" fill="#111" font-weight="700" font-family="IBM Plex Mono,monospace">{p["n"]}</text></g>')
    # dimensions
    s.append(f'<line x1="2.5" y1="-4" x2="249" y2="-4" stroke="currentColor" stroke-width=".3"/>'
             f'<text x="125.75" y="-5.2" font-size="3.2" text-anchor="middle" fill="currentColor" font-family="IBM Plex Mono,monospace">246,5 × 95 mm · cantos R 5 · pontilhado = perfil A (referência) · USB-C e fone na borda</text>')
    s.append(f'<line x1="-3" y1="2.5" x2="-3" y2="97.5" stroke="currentColor" stroke-width=".3"/>'
             f'<text x="-4.2" y="50" font-size="3.2" text-anchor="middle" fill="currentColor" transform="rotate(-90 -4.2 50)" font-family="IBM Plex Mono,monospace">95 mm</text>')
    s.append(f'<text x="40" y="105.5" font-size="3" fill="currentColor" font-family="IBM Plex Mono,monospace">tracejado: limite teclado × interface   ·   pontilhado: perfil A, onde as peças devem ficar</text>'
             f'<polyline points="{poly(IFACE)}" fill="none" stroke="#f2f0e8" stroke-opacity=".75" stroke-width=".45" stroke-dasharray="1.6 1.2"/>')
    s.append("</svg>")
    return "\n".join(s)

print(len(parts), "parts;", "usb edge", round(ux, 1), round(ua), "jack", round(jx, 1), round(ja), "holes", [(round(a, 1), round(b, 1)) for a, b in holes])
