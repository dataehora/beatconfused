"""eTutti Slim (R4SL, stage 2b): dimensioned plan of the MAIN board (placement, no tracks). Stdlib only.

    python etutti/hardware/slim/pcb/principal/planta_principal.py   -> pcb/principal/img/planta_principal.{svg,png}

Reads pcb/principal/posicao_principal.json (the placement) and case/envelope_principal.json. The view is from ABOVE (the instrument's frame: x right, y BACK up the page);
the parts are on the bottom face (dashed outlines).  Colours = function blocks.
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, "..", ".."))
POS = json.load(open(os.path.join(HERE, "posicao_principal.json"), encoding="utf-8"))
ENV = json.load(open(os.path.join(HW, "case", "envelope_principal.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "img")
os.makedirs(OUT, exist_ok=True)
INK, BLUE, RED, GREY = "#1d1d1f", "#1f5fa8", "#b3261e", "#8b8b8b"
BLOCK = {"P": ("#cfe3f7", "Processador (RT1062, flash, boot, cristais)"), "E": ("#f7d9c4", "Energia e USB (BQ24075, TPS63001, latch, USB-C)"), "F": ("#d9f0d2", "Audio (SGTL5000, P2)"),
         "I": ("#f3e3a7", "Knobs (sensores de angulo, chave Hall, LED, PROG)"), "R": ("#e3d1f0", "Reguas (4 FFC, series do scan)")}
SC = 11.0
X0, Y1 = -100.0, 72.0                       # the page's left edge (x) and top (y)


def px(x):
    return 20 + (x - X0) * SC


def py(y):
    return 40 + (Y1 - y) * SC


def build():
    W = int(20 + 78 * SC + 360)
    H = int(40 + 90 * SC + 60)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Arial,sans-serif">' % (W, H, W, H), '<rect width="%d" height="%d" fill="#fff"/>' % (W, H)]

    def T(t, x, y, s=11, c=INK, a="start", extra=""):
        o.append('<text x="%.1f" y="%.1f" font-size="%d" fill="%s" text-anchor="%s" %s>%s</text>' % (x, y, s, c, a, extra, t))

    def R(x0, y0, x1, y1, fill="none", stroke=INK, w=1.0, dash=None):
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="%s" stroke-width="%.1f"%s/>' % (px(x0), py(y1), (x1 - x0) * SC, (y1 - y0) * SC, fill, stroke, w, ' stroke-dasharray="%s"' % dash if dash else ""))

    def L(a, b, c=INK, w=1.0, dash=None):
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f"%s/>' % (px(a[0]), py(a[1]), px(b[0]), py(b[1]), c, w, ' stroke-dasharray="%s"' % dash if dash else ""))

    def C(x, y, d, fill="none", stroke=INK, w=1.0, dash=None):
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="%.1f"%s/>' % (px(x), py(y), d / 2 * SC, fill, stroke, w, ' stroke-dasharray="%s"' % dash if dash else ""))

    T("eTutti Slim - placa principal (SPEC R4SL, Etapa 2b): posicionamento SEM rotas. Vista de CIMA (frente/jogador embaixo, y para tras); pecas na face de baixo; mm.", 20, 20, 14)
    # context: case walls, bay, rulers' left ends
    c = ENV["paredes_internas"]
    R(c["esquerda_x"], c["frente_y"], -20.0, c["tras_y"], "none", "#bbbbbb", 1.0, "6 3")
    b = ENV["baia_bateria"]
    R(b["x"][0], b["y"][0], b["x"][1], b["y"][1], "#f2f2f2", GREY, 1.0, "4 3")
    T("baia da bateria VARTA 56457 201 016 (34,5 x 52,0 x 5,35): %.1f x %.1f" % (b["x"][1] - b["x"][0], b["y"][1] - b["y"][0]), px(b["x"][0]) + 6, py(b["y"][0] + 28), 11, GREY)
    for r in ENV["ffc"]:
        R(r["x_regua_esquerda"], r["y"] - 7.5, r["x_regua_esquerda"] + 9, r["y"] + 7.5, "#eaf3e6", "#2f6b3a", 1.0)
        T("regua %d" % r["fileira"], px(r["x_regua_esquerda"]) + 2, py(r["y"]) + 4, 10, "#2f6b3a")
    # board outline
    poly = POS["placa"]["contorno"]
    o.append('<polygon points="%s" fill="#f1f7ec" stroke="#2f6b3a" stroke-width="2"/>' % " ".join("%.1f,%.1f" % (px(x), py(y)) for x, y in poly))
    # escape zone
    e = POS["escape_bga"]["retangulo"]
    R(e[0], e[1], e[2], e[3], "none", RED, 1.2, "5 3")
    T("zona de escape do BGA (2,5 mm)", px(e[0]) + 3, py(e[3]) - 4, 10, RED)
    # posts
    for (x, y) in ENV["pilares"]["pontos"]:
        C(x, y, 6.0, "none", "#7a5a2a", 1.0, "3 2")
        C(x, y, 2.2, "#fff", "#7a5a2a", 1.2)
    # knobs
    for nm, k in (("REGISTROS", ENV["knobs"]["registros"]["eixo"]), ("VOLUME", ENV["knobs"]["volume"]["eixo"])):
        C(k[0], k[1], 26.0, "none", "#999", 0.8, "2 4")
        C(k[0], k[1], 6.0, "none", RED, 1.0)
        L((k[0] - 8, k[1]), (k[0] + 8, k[1]), RED, 0.6, "2 2")
        L((k[0], k[1] - 8), (k[0], k[1] + 8), RED, 0.6, "2 2")
        T("knob " + nm, px(k[0]), py(k[1]) - 14 * SC / 1.0 + 40, 10, RED, "middle")
    C(ENV["knobs"]["volume"]["eixo"][0], ENV["knobs"]["volume"]["eixo"][1], 23.2, "none", "#d4a017", 1.0)
    # parts
    for ref, q in POS["pecas"].items():
        if ref.startswith("H") and q["codigo"] == "":
            continue
        x0, y0, x1, y1 = q["patio"]
        col = BLOCK.get(q["codigo"][:1], ("#eeeeee", ""))[0]
        R(x0, y0, x1, y1, col, "#444", 0.7, "3 1")
    for p in POS["pads"]:
        if p["ref"].startswith("H"):
            continue
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#d4a017" opacity="0.9"/>' % (px(p["x"] - p["w"] / 2), py(p["y"] + p["h"] / 2), p["w"] * SC, p["h"] * SC))
    big = ("U", "J", "Y", "D", "L", "SW", "FB")
    for ref, q in POS["pecas"].items():
        if ref.startswith(big) and q["codigo"]:
            x0, y0, x1, y1 = q["patio"]
            T(ref, px((x0 + x1) / 2), py((y0 + y1) / 2) + 3, 9, "#000", "middle", 'font-weight="bold"')
    # dimensions
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    s = ENV["placa"]["faixa"]
    L((s["x"][0], s["y"][0] - 3), (s["x"][1], s["y"][0] - 3), BLUE, 1)
    T("faixa %.1f" % (s["x"][1] - s["x"][0]), px((s["x"][0] + s["x"][1]) / 2), py(s["y"][0] - 3) + 14, 10, BLUE, "middle")
    L((min(xs), s["y"][1] + 2.2), (max(xs), s["y"][1] + 2.2), BLUE, 1)
    T("comprimento %.1f (x %.1f ... %.1f)" % (max(xs) - min(xs), min(xs), max(xs)), px((min(xs) + max(xs)) / 2), py(s["y"][1] + 2.2) - 5, 10, BLUE, "middle")
    L((max(xs) + 3, min(ys)), (max(xs) + 3, max(ys)), BLUE, 1)
    T("altura %.1f (y %.1f ... %.1f)" % (max(ys) - min(ys), min(ys), max(ys)), px(max(xs) + 3) + 6, py((min(ys) + max(ys)) / 2), 10, BLUE, "start")
    for r in ENV["ffc"]:
        T("FFC %d: folga %.1f" % (r["fileira"], r["folga_horizontal_mm"]), px(r["x_borda_placa"]) + 4, py(r["y"] + 4.2), 9, BLUE)
    # legend
    lx = 20 + 78 * SC + 20
    ly = 60
    for k, (col, name) in BLOCK.items():
        o.append('<rect x="%.1f" y="%.1f" width="14" height="14" fill="%s" stroke="#444"/>' % (lx, ly, col))
        T(name, lx + 20, ly + 12, 11)
        ly += 22
    T("Notas:", lx, ly + 14, 12, INK, "start", 'font-weight="bold"')
    for i, t in enumerate(["Todas as pecas na face de baixo (JLCPCB). Placa em z 6,8, 1,2 mm.", "Tracejado vermelho = zona de escape do RT1062; castanho = pilares D6 (M2).",
                           "Verde claro = pontas esquerdas das 4 reguas; FFC reto, boca da placa para +x.", "Circulo cinza D26 = plataforma do knob; D23,2 = anel de LED.",
                           "Placa fora da baia da bateria (a parede da baia toca z 7,0 > 6,8)."]):
        T(t, lx, ly + 34 + i * 16, 10)
    o.append("</svg>")
    path = os.path.join(OUT, "planta_principal.svg")
    open(path, "w", encoding="utf-8").write("\n".join(o))
    edge = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    if os.path.exists(edge):
        subprocess.run([edge, "--headless", "--screenshot=" + os.path.join(OUT, "planta_principal.png"), "--window-size=%d,%d" % (W, H), "file:///" + path.replace("\\", "/")], capture_output=True)
    print(path)


if __name__ == "__main__":
    build()
