#!/usr/bin/env python3
"""Liebling (Batschauer), R3MIC, versao A - D1: contrato de contorno e posicoes (pcb_envelope.json) + SVG de conferencia
+ conferencia de serigrafia (D3 preliminar).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe minimic/design/gerar_envelope.py

Le as posicoes de proto_r3.py (referencia aprovada, nao editada), escreve:
  minimic/design/pcb_envelope.json            (contrato com a eletronica; dono: design)
  minimic/design/img/envelope.svg             (conferencia do contorno e das zonas)
  minimic/design/img/serigrafia_conferencia.svg (textos x pads, com os conflitos em vermelho)
  minimic/design/img/serigrafia_conferencia.json (lista de conflitos)
Quadro: origem no canto superior esquerdo da placa, x para a direita, y para BAIXO (o mesmo sentido do KiCad, sem espelhar);
y = 0 e o lado do plugue; a face de componentes (LEDs, botoes, microfones) e a de cima (F.Cu), vista de cima.
So biblioteca padrao (+ proto_r3, que e so stdlib)."""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import proto_r3 as P  # noqa: E402

W, D, T = 72.0, 22.0, 1.2
CX = W / 2

# ---------------------------------------------------------------- contorno
CH_FRONT, CH_BACK = 3.0, 1.5          # chanfros: frente (longe do celular, y = D), atras (lado do plugue, y = 0)
PLUG_W, PLUG_T = 8.94, 3.26           # envelope do plugue no protótipo (corpo/sobremolde); casca USB-C nominal 8.25 x 2.40
PLUG_OUT = 6.65                       # comprimento do plugue para fora da borda (v < 0)
PLUG_IN = 2.5                         # quanto do corpo entra na placa (entalhe)
NOTCH_CLR = 0.15                      # folga por lado do entalhe
NOTCH_W = PLUG_W + 2 * NOTCH_CLR
NOTCH_D = PLUG_IN + 0.1


def outline(with_notch=True):
    n0, n1 = CX - NOTCH_W / 2, CX + NOTCH_W / 2
    pts = [(CH_BACK, 0.0)]
    if with_notch:
        pts += [(n0, 0.0), (n0, NOTCH_D), (n1, NOTCH_D), (n1, 0.0)]
    pts += [(W - CH_BACK, 0.0), (W, CH_BACK), (W, D - CH_FRONT), (W - CH_FRONT, D), (CH_FRONT, D), (0.0, D - CH_FRONT), (0.0, CH_BACK)]
    return [[round(x, 3), round(y, 3)] for x, y in pts]


def area(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2


# ---------------------------------------------------------------- pecas (centros do proto_r3)
PKG = {"0805": (2.0, 1.2, 2.95, 1.40), "1206": (3.0, 1.6, 4.05, 1.75), "0603r": (0.8, 1.6, 0.95, 2.40)}   # corpo wxh, envelope de pads wxh (estimado)
BTN_BODY = (3.4, 2.6)
BTN_PADS = (4.2, 3.4)                  # corpo + 0,4 por lado (estimado; a eletronica troca pelo footprint real)
MIC_BODY = (4.0, 3.0)
FOAM_D, FOAM_H = 10.0, 3.0
HOLE_D = 1.8                           # do protótipo; E1 confirma no datasheet
RING_R, RING_W = 3.2, 0.3              # anel dourado: o do protótipo (r 2.4) toca os cantos do encapsulamento 4 x 3 (2.5 do centro)


def meter():
    out = []
    for i in range(12):
        x = round(P.FB_X[i], 3)
        if i < 11:
            db, col = P.LEVELS[i]
            out.append({"id": "M%d" % (i + 1), "x": x, "y": P.FB_Y, "pkg": "0805", "color": {P.G: "green", P.Y: "yellow", P.R: "red"}[col],
                        "hex": col, "dbfs": db, "label": str(db), "meaning": P.MEANING[i]})
        else:
            out.append({"id": "M12", "x": x, "y": P.FB_Y, "pkg": "1206", "color": "blue", "hex": P.B, "dbfs": None, "label": "SAT",
                        "meaning": "saturou (blinks with the two reds, ~8 Hz, ~2 s)"})
    return out


def gain():
    return [{"id": "G%d" % (i + 1), "x": round(P.GAIN_X[i], 3), "y": P.GAIN_Y, "pkg": "0603", "rot": 90, "color": "white", "gain_db": 3 * i,
             "label": {0: "0", 4: "+12", 8: "+24", 12: "+36", 14: "+42"}.get(i)} for i in range(15)]


def buttons():
    return [{"id": "SW_DN", "x": 16.0, "y": 15.5, "body": list(BTN_BODY), "pads_est": list(BTN_PADS), "glyph": "-"},
            {"id": "SW_UP", "x": 56.0, "y": 15.5, "body": list(BTN_BODY), "pads_est": list(BTN_PADS), "glyph": "+"}]


def mics():
    out = []
    for mx, lab, ch in zip(P.MIC_X, "LR", ("L", "R")):
        out.append({"id": "MK_" + lab, "channel": ch, "x": mx, "y": P.MIC_Y, "body": list(MIC_BODY), "acoustic_hole_d": HOLE_D,
                    "gold_ring": {"r_center": RING_R, "width": RING_W}, "foam_d": FOAM_D, "foam_h": FOAM_H})
    return out


# ---------------------------------------------------------------- serigrafia (proposta final e as do protótipo)
# (id, texto, x, y_centro, h, ancora, tipo)  -- h = altura da letra (mm); proposta final: 1,0 de altura, 0,8 de largura, traco 0,15 (minimo JLCPCB)
SILK_H, SILK_W, SILK_STROKE = 1.0, 0.8, 0.15
ADV = 1.15 * SILK_W                                     # avanço estimado por caractere do fonte de tracos do KiCad (w = 0,8)


def silk_final():
    t = []
    t.append(("T_LEVEL", "LEVEL dBFS", 14.3, 1.8, 1.0, "left"))
    for m in meter():
        t.append(("T_" + m["id"], m["label"], m["x"], 3.4, 1.2 if m["label"] == "SAT" else 1.0, "center"))
    for g in gain():
        if g["label"]:
            t.append(("T_" + g["id"], g["label"], g["x"], 18.2, 1.0, "center"))
    t.append(("T_GAIN", "GAIN dB", 36.0, 13.0, 1.0, "center"))
    for b in buttons():
        t.append(("T_" + b["id"], b["glyph"], b["x"], 18.6, 1.4, "center"))
    t.append(("T_L", "L", P.MIC_X[0], 19.4, 1.0, "center"))
    t.append(("T_R", "R", P.MIC_X[1], 19.4, 1.0, "center"))
    t.append(("T_BATSCH", "BATSCHAUER", 14.7, 13.0, 0.9, "left"))
    return t


def text_bbox(txt, x, yc, h, anchor, w_param=None):
    w_param = w_param or SILK_W * h / SILK_H
    n = sum(0.55 if c in "-+. " else 1.0 for c in txt)
    wd = n * 1.15 * w_param
    x0 = x - wd / 2 if anchor == "center" else x
    return (x0, yc - h / 2, x0 + wd, yc + h / 2)


# o protótipo (so para dizer o que o J viu): font-size em unidades de mm, largura media 0,6 em, altura da maiuscula 0,72 em
def silk_proto():
    t = []
    t.append(("LEVEL dBFS", 14.3, 2.3, .95, "left", .15))
    for i, m in enumerate(meter()):
        t.append((m["label"], m["x"], 3.9, 1.2 if i == 11 else .95, "center", 0))
    t.append(("Liebling", 14.5, 12.7, 3.0, "left", 0))
    t.append(("BATSCHAUER", 14.7, 13.9, .9, "left", .3))
    for g in gain():
        if g["label"]:
            t.append((g["label"], g["x"], 18.7, .95, "center", 0))
    t.append(("GAIN dB", 36.0, 13.5, .95, "center", .25))
    for b in buttons():
        t.append((b["glyph"], b["x"], 19.3, 1.7, "center", 0))
    t.append(("L", P.MIC_X[0], 19.9, 1.4, "center", 0))
    t.append(("R", P.MIC_X[1], 19.9, 1.4, "center", 0))
    return t


def proto_bbox(txt, x, yb, fs, anchor, ls, serif=False):
    n = len(txt)
    em = 0.5 if serif else 0.6
    wd = n * (fs * em + ls) - ls
    x0 = x - wd / 2 if anchor == "center" else x
    top = yb - fs * 0.72
    bot = yb + (fs * 0.22 if any(c in txt for c in "gjpqy") else 0)
    return (x0, top, x0 + wd, bot)


# ---------------------------------------------------------------- obstaculos (pads estimados)
def pads_rects():
    r = []
    for m in meter():
        w, h = PKG[m["pkg"]][2:]
        r.append((m["id"], m["x"] - w / 2, m["y"] - h / 2, m["x"] + w / 2, m["y"] + h / 2))
    for g in gain():
        w, h = PKG["0603r"][2:]
        r.append((g["id"], g["x"] - w / 2, g["y"] - h / 2, g["x"] + w / 2, g["y"] + h / 2))
    for b in buttons():
        w, h = b["pads_est"]
        r.append((b["id"], b["x"] - w / 2, b["y"] - h / 2, b["x"] + w / 2, b["y"] + h / 2))
    for m in mics():
        w, h = m["body"]
        r.append((m["id"], m["x"] - w / 2, m["y"] - h / 2, m["x"] + w / 2, m["y"] + h / 2))
    r.append(("PLUG_NOTCH", CX - NOTCH_W / 2, 0, CX + NOTCH_W / 2, NOTCH_D))
    return r


def overlap(a, b, margin=0.0):
    return not (a[2] + margin <= b[0] or b[2] + margin <= a[0] or a[3] + margin <= b[1] or b[3] + margin <= a[1])


def silk_check(items, kind):
    """items: lista de (id, bbox). Retorna conflitos texto x pad, texto x texto, texto x contorno dourado, texto x borda."""
    pads = pads_rects()
    gold_y = 0.8
    res = []
    for i, (idt, bb) in enumerate(items):
        for pid, *pr in pads:
            if overlap(bb, tuple(pr), 0.15):
                res.append({"tipo": "texto x pad", "a": idt, "b": pid})
        if bb[1] < gold_y + 0.11 + 0.15:
            res.append({"tipo": "texto x contorno dourado", "a": idt, "b": "linha y=0,8"})
        if bb[0] < 0.3 or bb[2] > W - 0.3 or bb[3] > D - 0.3:
            res.append({"tipo": "texto x borda", "a": idt, "b": "borda"})
        for idu, bu in items[i + 1:]:
            if overlap(bb, bu, 0.1):
                res.append({"tipo": "texto x texto", "a": idt, "b": idu})
    # texto x anel dourado / espuma: circulo
    for idt, bb in items:
        for m in mics():
            cx, cy = m["x"], m["y"]
            nx, ny = min(max(cx, bb[0]), bb[2]), min(max(cy, bb[1]), bb[3])
            if math.hypot(nx - cx, ny - cy) < RING_R + RING_W / 2 + 0.15:
                res.append({"tipo": "texto x anel dourado", "a": idt, "b": m["id"]})
    return res


BRAND = {"text": "Liebling", "x": 14.5, "y_baseline": 11.7, "font": "serif italic", "size": 3.0,
         "bbox_est": [14.5, 9.5, 26.5, 12.4]}      # a marca em cobre dourado (ENIG): ja subida 1,0 mm em relacao ao protótipo


def gold_contour():
    c = CX
    d = D
    return [[c - 5.4, .8], [1.9, .8], [.8, 1.9], [.8, d - 3.4], [3.4, d - .8], [W - 3.4, d - .8], [W - .8, d - 3.4], [W - .8, 1.9], [W - 1.9, .8], [c + 5.4, .8]]


# ---------------------------------------------------------------- JSON
def build_json():
    n0, n1 = CX - NOTCH_W / 2, CX + NOTCH_W / 2
    j = {
        "schema": "minimic_pcb_envelope/1",
        "revision": "R3MIC (versao A)",
        "date": "2026-11-28",
        "owner": "mic-design (a eletronica so le; mudancas sao pedidas no relatorio)",
        "units": "mm",
        "frame": {
            "origin": "canto superior esquerdo da placa, vista de cima (face de componentes = F.Cu)",
            "x": "para a direita, 0..72", "y": "para BAIXO, 0..22 (mesmo sentido do KiCad; nao espelhar)",
            "plug_side": "y = 0 (lado de 72 mm onde sai o plugue); y = 22 e a frente, longe do celular",
            "z": "0 = face de baixo (B.Cu), 1.2 = face de cima; o plugue e centrado em z = 0.6",
            "note": "para pecas na face de baixo, espelhar so em x (x' = 72 - x) ao ver por baixo",
        },
        "board": {
            "size": [W, D], "thickness": T, "layers": 2, "mask": "preta fosca", "finish": "ENIG",
            "outline": outline(True), "outline_no_notch": outline(False),
            "outline_area_mm2": round(area(outline(True)), 2),
            "chamfer_front_mm": CH_FRONT, "chamfer_back_mm": CH_BACK,
            "copper_to_edge_min": 0.3, "thickness_alternative": 1.6,
            "thickness_note": "1.2 e o da SPEC; o estudo de alavanca (FIT_CHECK.md) recomenda 1.6: a eletronica deve poder trocar em 1 parametro",
        },
        "plug": {
            "id": "J1", "type": "USB-C macho, carcaca metalica, pernas soldadas (peca a escolher na E1)",
            "x": CX, "y_axis": "perpendicular ao lado de 72 mm, saindo para y < 0",
            "z_center": T / 2,
            "envelope_wxh": [PLUG_W, PLUG_T], "envelope_note": "8.94 x 3.26 e o do protótipo (conservador); casca USB-C nominal 8.25 x 2.40",
            "exposed_length_from_board_edge": PLUG_OUT, "body_inside_board": PLUG_IN,
            "box": {"x0": round(CX - PLUG_W / 2, 3), "x1": round(CX + PLUG_W / 2, 3), "y0": -PLUG_OUT, "y1": PLUG_IN},
            "notch": {"enabled": True, "x0": round(n0, 3), "x1": round(n1, 3), "y0": 0.0, "y1": NOTCH_D, "clearance_per_side": NOTCH_CLR,
                      "note": "entalhe do meio-montado; se a E1 escolher um plugue so THT na borda, usar board.outline_no_notch"},
            "leg_pad_zone": {"x0": 30.9, "x1": 41.1, "y0": 0.0, "y1": 4.2, "note": "pads das 4 pernas: a eletronica posiciona com o footprint da peca; nada mais nesta zona"},
            "min_exposed_length_requirement": "6.65 (qualquer plugue mais curto reduz a inserção; ver capinha no FIT_CHECK)",
        },
        "mics": mics(),
        "mic_pair": {"spacing": P.MIC_X[1] - P.MIC_X[0], "margin_from_ends": P.MIC_X[0],
                     "port_note": "face do som a confirmar na E1: o protótipo desenha o microfone e a espuma na face de CIMA; se o IM72D128 for de porta inferior, o furo atravessa a placa e a espuma vai do lado do som"},
        "leds_meter": meter(),
        "leds_gain": gain(),
        "buttons": buttons(),
        "foam": {"diameter": FOAM_D, "height": FOAM_H, "count": 2, "side": "face de cima (do protótipo)", "centers": [[m["x"], m["y"]] for m in mics()],
                 "note": "esponja de celula aberta autocolante, 3 pares por embalagem; nenhuma peca alta sob ela alem do microfone"},
        "keepouts": [
            {"id": "KO_FOAM_L", "kind": "no_parts_no_silk_no_tall", "shape": "circle", "cx": P.MIC_X[0], "cy": P.MIC_Y, "r": FOAM_D / 2, "except": "MK_L"},
            {"id": "KO_FOAM_R", "kind": "no_parts_no_silk_no_tall", "shape": "circle", "cx": P.MIC_X[1], "cy": P.MIC_Y, "r": FOAM_D / 2, "except": "MK_R"},
            {"id": "KO_HOLE_L", "kind": "no_copper_no_mask_bridge", "shape": "circle", "cx": P.MIC_X[0], "cy": P.MIC_Y, "r": HOLE_D / 2 + 0.3,
             "note": "furo acustico Ø%.1f (do protótipo; E1 confirma no datasheet): sem cobre de outra rede, sem via" % HOLE_D},
            {"id": "KO_HOLE_R", "kind": "no_copper_no_mask_bridge", "shape": "circle", "cx": P.MIC_X[1], "cy": P.MIC_Y, "r": HOLE_D / 2 + 0.3},
            {"id": "KO_PLUG_TOP", "kind": "no_parts_no_silk", "shape": "rect", "x0": 30.9, "x1": 41.1, "y0": 0.0, "y1": 4.2,
             "note": "o plugue passa 1.03 mm acima e abaixo da placa dentro do entalhe"},
            {"id": "KO_FLEX_NOTCH", "kind": "no_ceramic_caps_no_crystal_no_via_farm", "shape": "rect", "x0": 26.0, "x1": 46.0, "y0": 0.0, "y1": 6.0,
             "note": "zona de flexao em volta do plugue: sem capacitor ceramico, cristal ou peca grande; trilhas largas, cantos do entalhe com raio 0.3"},
            {"id": "KO_EDGE", "kind": "copper_to_edge", "value": 0.3},
        ],
        "gold": {
            "mic_rings": [{"cx": m["x"], "cy": m["y"], "r_center": RING_R, "width": RING_W} for m in mics()],
            "contour": {"width": 0.22, "polyline": gold_contour(), "note": "linha de cobre 0.8 mm para dentro da borda, aberta na mascara (ENIG); aberta junto ao entalhe (±5.4 do centro)"},
            "brand": {"text": "Liebling", "x": BRAND["x"], "y_baseline": BRAND["y_baseline"], "size": BRAND["size"], "bbox": BRAND["bbox_est"],
                      "note": "marca em cobre aberto na mascara; 1.0 mm acima do protótipo (ver D3)"},
            "plug_band": {"x0": 31.5, "x1": 40.5, "y0": 0.0, "y1": 2.5, "note": "faixa dourada do protótipo sobre o entalhe: e a area de solda do plugue, nao arte"},
        },
        "silkscreen_proposal": {"min_height": SILK_H, "width": SILK_W, "stroke": SILK_STROKE, "color": "white",
                                "texts": [{"id": i, "text": t, "x": x, "y_center": y, "height": h, "anchor": a} for i, t, x, y, h, a in silk_final()],
                                "note": "proposta de D3 (o protótipo usa letras de 0.7 mm, abaixo do minimo de silk da JLCPCB); a eletronica ajusta com o KiCad e re-roda a conferencia"},
        "heights": {"board_top_z": T, "meter_led": 0.6, "meter_sat": 0.7, "gain_led": 0.5, "button": 1.6, "mic": 1.0, "foam_above_board": FOAM_H,
                    "max_z_total": round(T + FOAM_H, 2), "plug_z_range": [round(T / 2 - PLUG_T / 2, 3), round(T / 2 + PLUG_T / 2, 3)]},
        "status": "provisorio nas pecas (footprints reais vem da E1/E3); definitivo nas posicoes de LEDs, botoes e microfones (as do protótipo aprovado)",
    }
    return j


# ---------------------------------------------------------------- SVG
def svg_header(vb, w_px):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s" width="%d" font-family="Arial,Helvetica,sans-serif">'
            '<rect x="%s" y="%s" width="%s" height="%s" fill="#fff"/>' % (vb, w_px, *vb.split()))


def poly_svg(pts, **kw):
    a = " ".join('%s="%s"' % (k.replace("_", "-"), v) for k, v in kw.items())
    return '<polygon points="%s" %s/>' % (" ".join("%.3f,%.3f" % tuple(p) for p in pts), a)


def make_envelope_svg(j):
    o = [svg_header("-12 -12 96 52", 1500)]
    o.append('<rect x="-12" y="-12" width="96" height="52" fill="#fafafa"/>')
    # plugue
    b = j["plug"]["box"]
    o.append('<rect x="%s" y="%s" width="%s" height="%s" rx="1.3" fill="#d6dae0" stroke="#6b7078" stroke-width=".18"/>' % (b["x0"], b["y0"], b["x1"] - b["x0"], b["y1"] - b["y0"]))
    o.append(poly_svg(j["board"]["outline"], fill="#2a2a30", stroke="#000", stroke_width=".2"))
    # keepouts
    for k in j["keepouts"]:
        if k.get("shape") == "circle":
            o.append('<circle cx="%s" cy="%s" r="%s" fill="%s" fill-opacity=".18" stroke="%s" stroke-width=".15" stroke-dasharray=".6 .4"/>' % (
                k["cx"], k["cy"], k["r"], "#ff9d2e" if "FOAM" in k["id"] else "#e63946", "#ff9d2e" if "FOAM" in k["id"] else "#e63946"))
        elif k.get("shape") == "rect":
            o.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#e63946" fill-opacity=".12" stroke="#e63946" stroke-width=".15" stroke-dasharray=".6 .4"/>' % (
                k["x0"], k["y0"], k["x1"] - k["x0"], k["y1"] - k["y0"]))
    # notch outline
    n = j["plug"]["notch"]
    o.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none" stroke="#fff" stroke-width=".12"/>' % (n["x0"], n["y0"], n["x1"] - n["x0"], n["y1"] - n["y0"]))
    # gold
    pl = j["gold"]["contour"]["polyline"]
    o.append('<polyline points="%s" fill="none" stroke="#c9a24a" stroke-width=".22"/>' % " ".join("%s,%s" % tuple(p) for p in pl))
    for m in j["mics"]:
        o.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="#c9a24a" stroke-width="%s"/>' % (m["x"], m["y"], m["gold_ring"]["r_center"], m["gold_ring"]["width"]))
        o.append('<rect x="%s" y="%s" width="4" height="3" fill="#cfd2d8" stroke="#6b7078" stroke-width=".12"/>' % (m["x"] - 2, m["y"] - 1.5))
        o.append('<circle cx="%s" cy="%s" r="%s" fill="#000" stroke="#fff" stroke-width=".1"/>' % (m["x"], m["y"], m["acoustic_hole_d"] / 2))
        o.append('<circle cx="%s" cy="%s" r="5" fill="none" stroke="#ff9d2e" stroke-width=".18"/>' % (m["x"], m["y"]))
        o.append('<text x="%s" y="%s" font-size="1.1" fill="#ff9d2e" text-anchor="middle">espuma Ø10</text>' % (m["x"], m["y"] + 7.2))
    for l in j["leds_meter"]:
        w, h = PKG[l["pkg"]][:2]
        o.append('<rect x="%.2f" y="%.2f" width="%s" height="%s" fill="%s"/>' % (l["x"] - w / 2, l["y"] - h / 2, w, h, l["hex"]))
        o.append('<text x="%.2f" y="%.2f" font-size=".9" fill="#ddd" text-anchor="middle">%s</text>' % (l["x"], l["y"] - 2.3, l["id"]))
    for l in j["leds_gain"]:
        o.append('<rect x="%.2f" y="%.2f" width=".8" height="1.6" fill="#f1f1ea"/>' % (l["x"] - .4, l["y"] - .8))
        o.append('<text x="%.2f" y="%.2f" font-size=".75" fill="#ddd" text-anchor="middle">%s</text>' % (l["x"], l["y"] + 2.5, l["id"]))
    for b in j["buttons"]:
        o.append('<rect x="%s" y="%s" width="3.4" height="2.6" rx=".3" fill="#8d929c"/>' % (b["x"] - 1.7, b["y"] - 1.3))
        o.append('<text x="%s" y="%s" font-size=".9" fill="#ddd" text-anchor="middle">%s</text>' % (b["x"], b["y"] + 3.2, b["id"]))
    # cotas
    def dim_h(x0, x1, y, txt, col="#111"):
        o.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width=".13"/>' % (x0, y, x1, y, col))
        o.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width=".13"/><line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width=".13"/>' % (
            x0, y - .6, x0, y + .6, col, x1, y - .6, x1, y + .6, col))
        o.append('<text x="%s" y="%s" font-size="1.1" fill="%s" text-anchor="middle">%s</text>' % ((x0 + x1) / 2, y - .5, col, txt))

    def dim_v(y0, y1, x, txt, col="#111"):
        o.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width=".13"/>' % (x, y0, x, y1, col))
        o.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width=".13"/><line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width=".13"/>' % (
            x - .6, y0, x + .6, y0, col, x - .6, y1, x + .6, y1, col))
        o.append('<text x="%s" y="%s" font-size="1.1" fill="%s" text-anchor="middle" transform="rotate(90 %s %s)">%s</text>' % (x + 1.6, (y0 + y1) / 2, col, x + 1.6, (y0 + y1) / 2, txt))
    dim_h(0, 72, 27.5, "72")
    dim_v(0, 22, 77, "22")
    dim_h(P.MIC_X[0], P.MIC_X[1], 31, "59 entre os microfones")
    dim_h(0, P.MIC_X[0], 24.2, "6.5")
    dim_h(P.MIC_X[1], 72, 24.2, "6.5")
    dim_h(n["x0"], n["x1"], -9.2, "entalhe %.2f x %.1f" % (n["x1"] - n["x0"], n["y1"]))
    o.append('<text x="%s" y="%s" font-size="1.1" fill="#111" text-anchor="middle">plugue %.2f x %.2f (envelope), %.2f para fora, centro x = 36</text>' % (CX, -10.6, PLUG_W, PLUG_T, PLUG_OUT))
    o.append('<text x="2" y="-9" font-size="1.1" fill="#111">y = 0: lado do plugue</text>')
    o.append('<text x="2" y="36.5" font-size="1.1" fill="#111">chanfros: 1.5 mm atras (y=0), 3 mm na frente (y=22). origem no canto superior esquerdo; y para baixo</text>')
    o.append('<text x="-11" y="38.8" font-size="1.0" fill="#555">laranja = espuma Ø10 (sem peca, sem silk); vermelho = zona sem peca / sem cobre de outra rede; dourado = ENIG aberto. Placa 72 x 22 x 1.2 mm, area %.0f mm2.</text>' % j["board"]["outline_area_mm2"])
    o.append("</svg>")
    return "".join(o)


def make_silk_svg(res_final, res_proto, final_items, proto_items, j):
    o = [svg_header("-3 -3 78 28", 1560)]
    o.append('<rect x="-3" y="-3" width="78" height="28" fill="#fafafa"/>')
    o.append(poly_svg(j["board"]["outline"], fill="#1d1d22", stroke="#000", stroke_width=".15"))
    for pid, x0, y0, x1, y1 in pads_rects():
        col = "#c9a24a" if not pid.startswith("PLUG") else "#555"
        o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" fill-opacity=".55" stroke="%s" stroke-width=".07"/>' % (x0, y0, x1 - x0, y1 - y0, col, col))
    for m in j["mics"]:
        o.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="#c9a24a" stroke-width=".3"/>' % (m["x"], m["y"], m["gold_ring"]["r_center"]))
        o.append('<circle cx="%s" cy="%s" r="2.4" fill="none" stroke="#e63946" stroke-width=".12" stroke-dasharray=".4 .3"/>' % (m["x"], m["y"]))
        o.append('<circle cx="%s" cy="%s" r="5" fill="none" stroke="#ff9d2e" stroke-width=".1"/>' % (m["x"], m["y"]))
    bad_f = {c["a"] for c in res_final} | {c["b"] for c in res_final}
    for idt, bb in final_items:
        col = "#ff4d4d" if idt in bad_f else "#ffffff"
        o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="none" stroke="%s" stroke-width=".08"/>' % (bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1], col))
    # proto brand/silk em tracejado cinza para comparar
    bad_p = {c["a"] for c in res_proto}
    for txt, bb in proto_items:
        col = "#ff4d4d" if txt in bad_p else "#6fb5ff"
        o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="none" stroke="%s" stroke-width=".08" stroke-dasharray=".3 .2"/>' % (bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1], col))
        o.append('<text x="%.2f" y="%.2f" font-size=".55" fill="%s">%s</text>' % (bb[0], bb[1] - .1, col, txt))
    bb = BRAND["bbox_est"]
    o.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#c9a24a" fill-opacity=".25" stroke="#c9a24a" stroke-width=".1"/>' % (bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1]))
    o.append('<text x="%s" y="%s" font-size=".7" fill="#c9a24a">marca (cobre, 1.0 mm acima do protótipo)</text>' % (bb[0], bb[1] - .2))
    o.append('<text x="-2.7" y="23.7" font-size=".8" fill="#222">caixas brancas = serigrafia proposta (1.0 mm); azuis tracejadas = a do protótipo (estimadas); vermelho = conflito; dourado = pads estimados; vermelho tracejado = anel do protótipo (r 2.4)</text>')
    o.append("</svg>")
    return "".join(o)


def main():
    j = build_json()
    with open(os.path.join(HERE, "pcb_envelope.json"), "w", encoding="utf-8") as f:
        json.dump(j, f, indent=1, ensure_ascii=False)
    os.makedirs(os.path.join(HERE, "img"), exist_ok=True)
    with open(os.path.join(HERE, "img", "envelope.svg"), "w", encoding="utf-8") as f:
        f.write(make_envelope_svg(j))
    final_items = [(i, text_bbox(t, x, y, h, a)) for i, t, x, y, h, a in silk_final()]
    proto_items = []
    for t, x, yb, fs, a, ls in silk_proto():
        proto_items.append((t, proto_bbox(t, x, yb, fs, a, ls, serif=(t == "Liebling"))))
    # a marca (cobre) conta como texto na conferencia da proposta
    final_items.append(("MARCA", tuple(BRAND["bbox_est"])))
    res_f = silk_check(final_items, "final")
    res_p = silk_check(proto_items, "proto")
    # os pads da MARCA nao existem: remover "texto x pad" dela; o que importa e marca x texto
    with open(os.path.join(HERE, "img", "serigrafia_conferencia.svg"), "w", encoding="utf-8") as f:
        f.write(make_silk_svg(res_f, res_p, final_items, proto_items, j))
    out = {"proposta": res_f, "protótipo_estimado": res_p,
           "anel_dourado": {"r_proto": 2.4, "canto_do_encapsulamento_4x3": round(math.hypot(2.0, 1.5), 3), "r_proposto": RING_R}}
    with open(os.path.join(HERE, "img", "serigrafia_conferencia.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("area", j["board"]["outline_area_mm2"])
    print("conflitos da proposta:", json.dumps(res_f, ensure_ascii=False))
    print("conflitos do prototipo (estimado):")
    for c in res_p:
        print("  ", c)


if __name__ == "__main__":
    main()
