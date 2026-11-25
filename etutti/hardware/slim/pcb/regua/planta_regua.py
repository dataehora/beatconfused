"""eTutti Slim (R3SL, stage 2a): dimensioned plan of the ruler, the grade, the four rows with the NOTE NAME on every key, and the panel. Stdlib only.

    python etutti/hardware/slim/pcb/regua/planta_regua.py     -> pcb/regua/img/planta_regua.svg (+ .png through msedge if present)

Reads pcb/regua/posicao_regua.json (the placement) and case/envelope_regua.json (the Design's contract).
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, "..", ".."))
POS = json.load(open(os.path.join(HERE, "posicao_regua.json"), encoding="utf-8"))
ENV = json.load(open(os.path.join(HW, "case", "envelope_regua.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "img")
os.makedirs(OUT, exist_ok=True)
INK, BLUE, RED, GREEN, GREY = "#1d1d1f", "#1f5fa8", "#b3261e", "#2f6b3a", "#8b8b8b"
FILL = {"U": "#222222", "C": "#9b7b4a", "J": "#c9b777"}
RL, RW = ENV["regua"]["comprimento"], ENV["regua"]["largura"]


def rect(x0, y0, x1, y1, fill="none", stroke=INK, w=0.15, extra=""):
    return '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" stroke="%s" stroke-width="%.2f" %s/>' % (x0, y0, x1 - x0, y1 - y0, fill, stroke, w, extra)


def line(x0, y0, x1, y1, c=INK, w=0.15, dash=None):
    return '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f"%s/>' % (x0, y0, x1, y1, c, w, ' stroke-dasharray="%s"' % dash if dash else "")


def circ(x, y, d, fill="none", stroke=INK, w=0.15):
    return '<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s" stroke-width="%.2f"/>' % (x, y, d / 2, fill, stroke, w)


def txt(x, y, s, size=1.6, c=INK, anchor="middle", extra=""):
    return '<text x="%.2f" y="%.2f" font-size="%.2f" fill="%s" text-anchor="%s" font-family="Arial,sans-serif" %s>%s</text>' % (x, y, size, c, anchor, extra, s)


def hdim(x0, x1, y, label, c=BLUE, up=1):
    return (line(x0, y, x1, y, c, 0.12) + line(x0, y - 0.8, x0, y + 0.8, c, 0.12) + line(x1, y - 0.8, x1, y + 0.8, c, 0.12) + txt((x0 + x1) / 2, y - 0.7 * up, label, 1.5, c))


def vdim(x, y0, y1, label, c=BLUE):
    return (line(x, y0, x, y1, c, 0.12) + line(x - 0.8, y0, x + 0.8, y0, c, 0.12) + line(x - 0.8, y1, x + 0.8, y1, c, 0.12)
            + txt(x + 1.0, (y0 + y1) / 2 + 0.5, label, 1.5, c, "start"))


def ruler_plan(ox, oy, o):
    """Ruler plan at (ox, oy) = (u 0, v = 0 of the ruler's centre line); +v (player) is DOWN on the page."""
    o.append(rect(ox, oy - RW / 2, ox + RL, oy + RW / 2, "#e9f1e6", GREEN, 0.25))
    for u in ENV["regua"]["u_teclas"]:
        o.append(rect(ox + u - 7.0, oy - 7.0, ox + u + 7.0, oy + 7.0, "none", GREY, 0.1, 'stroke-dasharray="1 0.6"'))
        o.append(circ(ox + u, oy, 5.2, "#ffffff", INK, 0.12))
        for sgn in (-1, 1):
            o.append(circ(ox + u + sgn * 5.075, oy, 1.7, "#ffffff", INK, 0.12))
    for u in ENV["regua"]["m2_u"]:
        o.append(circ(ox + u, oy, 2.2, "#ffffff", RED, 0.15))
        o.append(circ(ox + u, oy, 5.4, "none", RED, 0.08))
    for p in POS["pads"]:
        if p["ref"].startswith(("SW", "H")):
            continue
        o.append(rect(ox + p["u"] - p["w"] / 2, oy + p["v"] - p["h"] / 2, ox + p["u"] + p["w"] / 2, oy + p["v"] + p["h"] / 2, "#d4a017", "none", 0))
    for ref, q in POS["pecas"].items():
        if ref.startswith(("SW", "H")):
            continue
        c = q["patio_uv"]
        o.append(rect(ox + c[0], oy + c[1], ox + c[2], oy + c[3], "none", FILL.get(ref[0], INK), 0.1))
        if ref[0] in "UJ":
            o.append(txt(ox + (c[0] + c[2]) / 2, oy + c[3] + 1.5 if ref[0] == "J" or ref == "U9" else oy + c[1] - 0.6, ref, 1.2, INK))
    o.append(line(ox, oy, ox + RL, oy, RED, 0.08, "2 1"))
    return o


def build():
    W, H = 340, 305
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W, H, W * 6, H * 6), '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H)]
    o.append(txt(10, 8, "eTutti Slim - regua R8 e grade (SPEC R3SL, Etapa 2a): planta cotada, mm. Face de baixo vista de cima (as pecas estao no verso, tracejado = verso).", 2.6, INK, "start"))
    # ---- 1. ruler
    ox, oy = 25, 40
    o.append(txt(10, 22, "1. Regua R8: 160,0 x 15,0 x 1,2 mm, 2 camadas. Frente (jogador) EMBAIXO. Eixo: u da ponta esquerda, v = 0 na linha do centro das teclas.", 2.0, INK, "start"))
    ruler_plan(ox, oy, o)
    u = ENV["regua"]["u_teclas"]
    o.append(hdim(ox, ox + 14.0, oy - 12, "cauda 14,0"))
    o.append(hdim(ox + u[0], ox + u[1], oy - 12, "passo 18,5"))
    o.append(hdim(ox, ox + RL, oy - 18, "160,0"))
    o.append(hdim(ox + u[0], ox + u[0] + 0.01, oy + 12, ""))
    o.append(txt(ox + u[0], oy + 11.6, "tecla 1: u = 21,25", 1.4, BLUE))
    o.append(hdim(ox + u[1] + 9.25 - 0.0, ox + ENV["regua"]["m2_u"][1], oy + 12, "M2 u = %.1f e %.1f (nos vaos, v = 0)" % tuple(ENV["regua"]["m2_u"]), BLUE))
    o.append(vdim(ox + RL + 4, oy - RW / 2, oy + RW / 2, "15,0"))
    o.append(vdim(ox + RL + 14, oy, oy + 4.3, "sensor a 4,3 do centro (lado do jogador)"))
    o.append(txt(ox + 3, oy + 11.2, "FFC J1: boca para -u, u = 2,2", 1.3, BLUE, "start"))
    # ---- 2. the four rows with the note names
    oy2 = 118
    o.append(txt(10, oy2 - 12, "2. As 4 fileiras (vista de cima do instrumento; y para tras): regua (verde) e grade (marrom) de cada fileira, a nota em cada tecla. Indice = 8 x (fileira - 1) + posicao.", 2.0, INK, "start"))
    sc_x0 = 100.0                       # instrument x of the page's left edge
    for r in range(4):
        ri = ENV["fileiras"][r]
        yy = oy2 + 54 - ri["y"] * 1.0     # +y (back) goes UP the page
        xl = 20 + (ri["x_left"] - (-30.5)) * 1.0
        o.append(rect(xl, yy - 7.5, xl + RL, yy + 7.5, "#e9f1e6", GREEN, 0.2))
        g0 = ENV["grade"]["u0"]
        o.append(rect(xl + g0, yy - 8.0, xl + RL, yy + 8.0, "none", "#6b5a3a", 0.25, 'stroke-dasharray="2 1"'))
        o.append(txt(xl - 1.5, yy + 0.6, "fileira %d  z %.1f" % (ri["row"], ri["z_bottom"]), 1.4, INK, "end"))
        for k in ri["keys"]:
            kx = 20 + (k["x"] - (-30.5))
            sharp = "#" in k["note"]
            o.append(rect(kx - 7.3, yy - 7.3, kx + 7.3, yy + 7.3, "#222222" if sharp else "#ffffff", INK, 0.2))
            o.append(txt(kx, yy + 1.0, k["note"], 3.2, "#ffffff" if sharp else INK))
            o.append(txt(kx, yy + 5.6, "#%d" % k["idx"], 1.4, "#cccccc" if sharp else GREY))
    # ---- 3. grade
    oy3 = 222
    g = ENV["grade"]
    gl = g["u1"] - g["u0"]
    o.append(txt(10, oy3 - 14, "3. Grade FR-4 1,2 mm: %.1f x %.1f, 8 furos de %.2f (cantos R%.1f), 2 furos M2 de 2,2; sem cobre. Topo da grade a 1,3 mm da regua (separador M2)." % (gl, g["largura"], g["furo"], g["raio_canto"]), 2.0, INK, "start"))
    gx = 25
    o.append(rect(gx, oy3 - g["largura"] / 2, gx + gl, oy3 + g["largura"] / 2, "#efe6d2", "#6b5a3a", 0.25))
    for uu in ENV["regua"]["u_teclas"]:
        h = g["furo"] / 2
        o.append(rect(gx + uu - g["u0"] - h, oy3 - h, gx + uu - g["u0"] + h, oy3 + h, "#ffffff", INK, 0.15))
    for uu in g["m2_u"]:
        o.append(circ(gx + uu - g["u0"], oy3, 2.2, "#ffffff", RED, 0.15))
    o.append(hdim(gx, gx + gl, oy3 - 12, "%.1f" % gl))
    o.append(vdim(gx + gl + 4, oy3 - g["largura"] / 2, oy3 + g["largura"] / 2, "%.1f" % g["largura"]))
    o.append(hdim(gx + 6.5, gx + 6.5 + 18.5, oy3 + 12, "passo 18,5"))
    # ---- 4. panel
    oy4 = 272
    o.append(txt(10, oy4 - 16, "4. Painel proposto (a confirmar com a JLCPCB): regua + grade lado a lado, mesma espessura e acabamento; contorno por fresa/V-cut, 2,0 mm de trilho de separacao.", 2.0, INK, "start"))
    px = 25
    o.append(rect(px - 2, oy4 - 21, px + RL + 2, oy4 + 21, "none", RED, 0.2, 'stroke-dasharray="3 1"'))
    o.append(rect(px, oy4 - 19, px + RL, oy4 - 19 + RW, "#e9f1e6", GREEN, 0.25))
    o.append(rect(px + g["u0"], oy4 + 4, px + RL, oy4 + 4 + g["largura"], "#efe6d2", "#6b5a3a", 0.25))
    o.append(txt(px + RL / 2, oy4 - 11, "regua 160,0 x 15,0", 1.8, GREEN))
    o.append(txt(px + g["u0"] + gl / 2, oy4 + 12.5, "grade %.1f x %.1f" % (gl, g["largura"]), 1.8, "#6b5a3a"))
    o.append(hdim(px - 2, px + RL + 2, oy4 + 24, "painel %.1f x %.1f" % (RL + 4, 42.0)))
    o.append("</svg>")
    path = os.path.join(OUT, "planta_regua.svg")
    open(path, "w", encoding="utf-8").write("\n".join(o))
    print(path)
    edge = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    if os.path.exists(edge):
        subprocess.run([edge, "--headless", "--screenshot=" + os.path.join(OUT, "planta_regua.png"), "--window-size=2040,1800", "file:///" + path.replace("\\", "/")],
                       capture_output=True)


if __name__ == "__main__":
    build()
