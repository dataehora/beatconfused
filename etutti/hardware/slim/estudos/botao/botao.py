"""eTutti Slim (R5SL item 3): the accordion-style button. CadQuery + stdlib SVG.  Replaces the R4SL study (skirt D15 x 0.75 cap).

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/estudos/botao/botao.py
    -> estudos/botao/botao.{step,stl} (plain: naturals white / sharps black), botao_textura.{step,stl} (C and F), botao.json, botao_cortes_4fileiras.{svg,png}

Shape (SPEC R5SL 3, reference conceito/img/botao_acordeon.png): head D15 x 7.5 (cylinder + domed top, sagitta 1.0, edge R1), shank D10, pin D5.4 x 3.0 with the
female cross (4.2 x 1.04 x 3.0, 0.3 lead-in) over the KS-33D's male cross (4.0 x 1.10, read off the STEP in R4SL).  Heights come from the REAL lid of each row
(case.S): at the bottom of the stroke the head's base is 2.0 mm above the highest edge of the D11 hole (the rear one: the lid slopes 7.1 deg).  One piece for all four
rows: its shank length is the largest one any row needs, so a row that needs less simply has more than 2.0 mm of clearance.
Cap frame: z = 0 at the head's base, up positive.
"""
import json
import math
import os
import subprocess
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
SLIM = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(SLIM, "case"))
import case as C  # noqa: E402
import layout_slim as L  # noqa: E402

HEAD_D, HEAD_H = 15.0, 3.8                              # R6SL: head D15 x 3.8 (R5SL had 7.5)
WALL_H, EDGE_RX, EDGE_RZ = 1.6, 1.3, 1.15               # straight wall 1.6, quarter-ellipse edge 1.3 radial x 1.15 vertical, spherical dome up to the top
SHANK_D, PIN_D, PIN_L = 10.0, 5.4, 3.0
WELL_D = 5.67
CROSS_L, CROSS_W, CROSS_H = 4.00, 1.10, 3.30
SOCK_L, SOCK_W, SOCK_DEPTH, LEAD = 4.20, 1.04, 3.0, 0.3
HOLE_D = C.KEY_HOLE_D
TRAVEL, GAP, STEM_ABOVE = 3.5, 2.0, 3.5                # stroke, clear space above the hole's high edge at the bottom of the stroke, stem top above the housing top at rest
DOT_S, DOT_DEPTH, DOT_PITCH, DOT_AREA_D = 0.5, 0.18, 1.1, 11.0   # R6SL: C and F = diagonal dotted pattern as on the V4 (0.5 mm square recesses, 0.18 deep, 45 deg grid, pitch 1.1, inside D11)


def row_numbers():
    rows = []
    for r in range(4):
        y = L.ROW_Y[r]
        ys = [y - HOLE_D / 2 + HOLE_D * i / 220 for i in range(221)]
        rim_hi = max(C.S(v) for v in ys)
        rim_lo = min(C.S(v) for v in ys)
        rows.append({"fileira": r + 1, "y": round(y, 3), "topo_carcaca": L.HOUSING_TOP[r], "tampo_no_centro": round(C.S(y), 3), "borda_alta_do_furo": round(rim_hi, 3),
                     "borda_baixa_do_furo": round(rim_lo, 3), "haste_precisa": rim_hi + GAP - L.HOUSING_TOP[r]})
    return rows


ROWS = row_numbers()
SHANK_L = math.ceil(max(r["haste_precisa"] for r in ROWS) * 20) / 20       # one shank for the four rows (to 0.05)


ELL = [(HEAD_D / 2 - EDGE_RX + EDGE_RX * math.cos(math.pi / 2 * i / 8), WALL_H + EDGE_RZ * math.sin(math.pi / 2 * i / 8)) for i in range(0, 9)]
ELL = [(HEAD_D / 2, WALL_H)] + ELL[1:]
R0, Z0 = ELL[-1]
DZC = (R0 ** 2 + Z0 ** 2 - HEAD_H ** 2) / (2 * (Z0 - HEAD_H))          # dome sphere centre on the axis, through the edge's end and the top
DRS = HEAD_H - DZC
_a0 = math.atan2(Z0 - DZC, R0)
DOME_MID = (DRS * math.cos((_a0 + math.pi / 2) / 2), DZC + DRS * math.sin((_a0 + math.pi / 2) / 2))


def dome_z(r):
    return HEAD_H if r < 1e-9 else (DZC + math.sqrt(DRS ** 2 - r * r) if r <= R0 else None)


def head_pts(n=16):
    """(r, z) of the head's outline from the wall top to the axis: wall, ellipse, dome (for the drawings)."""
    pts = [(HEAD_D / 2, WALL_H)] + ELL[1:]
    for i in range(1, n + 1):
        a = _a0 + (math.pi / 2 - _a0) * i / n
        pts.append((DRS * math.cos(a), DZC + DRS * math.sin(a)))
    return pts


def dots():
    """The C/F pattern: square recesses (0.5 mm, rotated 45 deg, pitch 1.1 along the rotated axes) inside D11, flat bottom 0.18 below the dome at the square's centre."""
    cut = None
    n = 9
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = (i - j) * DOT_PITCH / math.sqrt(2), (i + j) * DOT_PITCH / math.sqrt(2)
            if math.hypot(x, y) + DOT_S * 0.71 > DOT_AREA_D / 2:
                continue
            zs = dome_z(math.hypot(x, y)) - DOT_DEPTH
            b = cq.Workplane("XY").workplane(offset=zs).center(x, y).rect(DOT_S, DOT_S).extrude(1.5).rotate((x, y, 0), (x, y, 1), 45)
            cut = b if cut is None else cut.union(b)
    return cut


def cap(texture=False):
    """Revolved profile: pin tip -> pin -> shank -> head, then the dome (arc), the R1 edge as a fillet, the female cross."""
    hr = HEAD_D / 2
    z_pin = -SHANK_L - PIN_L
    wp = (cq.Workplane("XZ").moveTo(0, z_pin).lineTo(PIN_D / 2, z_pin).lineTo(PIN_D / 2, -SHANK_L).lineTo(SHANK_D / 2, -SHANK_L).lineTo(SHANK_D / 2, 0).lineTo(hr, 0)
          .lineTo(hr, WALL_H).spline(ELL[1:], includeCurrent=True).threePointArc(DOME_MID, (0, HEAD_H)).close().revolve(360, (0, 0, 0), (0, 1, 0)))
    z0 = -SHANK_L - PIN_L
    for ang in (0, 90):
        slot = cq.Workplane("XY").workplane(offset=z0 - 0.01).rect(SOCK_L, SOCK_W).extrude(SOCK_DEPTH + 0.01)
        lead = (cq.Workplane("XY").workplane(offset=z0 - 0.01).rect(SOCK_L, SOCK_W + 2 * LEAD).workplane(offset=LEAD + 0.01).rect(SOCK_L, SOCK_W).loft())
        wp = wp.cut(slot.rotate((0, 0, 0), (0, 0, 1), ang)).cut(lead.rotate((0, 0, 0), (0, 0, 1), ang))
    if texture:
        wp = wp.cut(dots())
    return wp


def main():
    plain, tex = cap(False), cap(True)
    for name, w in (("botao", plain), ("botao_textura", tex)):
        cq.exporters.export(w, os.path.join(HERE, name + ".step"))
        cq.exporters.export(w, os.path.join(HERE, name + ".stl"), tolerance=0.03, angularTolerance=0.1)
    vol = plain.val().Volume()
    out = {"revisao": "R6SL",
           "cabeca": {"d": HEAD_D, "altura": HEAD_H, "lateral_reta": WALL_H, "borda_elipse_radial": EDGE_RX, "borda_elipse_vertical": EDGE_RZ, "raio_da_esfera_do_domo": round(DRS, 2)}, "haste_d": SHANK_D, "haste_comprimento": SHANK_L,
           "pino": {"d": PIN_D, "comprimento": PIN_L, "folga_radial_no_poco": round((WELL_D - PIN_D) / 2, 3)},
           "cruz_femea": {"braco": SOCK_L, "largura": SOCK_W, "profundidade": SOCK_DEPTH, "entrada_chanfro": LEAD},
           "cruz_macho_STEP": {"braco": CROSS_L, "largura": CROSS_W, "altura_min": CROSS_H}, "interferencia_largura_mm": round(CROSS_W - SOCK_W, 3),
           "furo_do_tampo_d": HOLE_D, "folga_radial_haste_furo": (HOLE_D - SHANK_D) / 2,
           "textura_C_F": {"tipo": "pontilhado diagonal (V4)", "quadrado": DOT_S, "fundo": DOT_DEPTH, "passo": DOT_PITCH, "grade_graus": 45, "area_d": DOT_AREA_D, "arquivo": "botao_textura.step"},
           "volume_cm3": round(vol / 1000, 3), "massa_g_resina_1p1": round(vol / 1000 * 1.1, 2)}
    tilt = 0.5
    out["folga_haste_furo"] = {"nominal_mm": (HOLE_D - SHANK_D) / 2, "jogo_da_haste_estimado_mm": 0.20, "inclinacao_graus_estimada": tilt,
                               "deslocamento_na_borda_mm": round(SHANK_L * math.tan(math.radians(tilt)), 3),
                               "margem_pior_caso_mm": round((HOLE_D - 0.15 - (SHANK_D + 0.15)) / 2 - 0.20 - SHANK_L * math.tan(math.radians(tilt)), 3),
                               "nota": "jogo da haste e inclinacao sao estimativas (a Gateron nao publica); o ensaio dos 4 botoes mede; impressao SLA +-0,15 no pior caso"}
    per = []
    for r in ROWS:
        stem_rest = r["topo_carcaca"] + STEM_ABOVE
        und_rest = stem_rest + SHANK_L
        und_pr = und_rest - TRAVEL
        per.append({"fileira": r["fileira"], "topo_carcaca_z": r["topo_carcaca"], "borda_alta_do_furo_z": r["borda_alta_do_furo"], "borda_baixa_do_furo_z": r["borda_baixa_do_furo"],
                    "haste_switch_topo_repouso_z": round(stem_rest, 2), "base_da_cabeca_repouso_z": round(und_rest, 2), "base_da_cabeca_apertado_z": round(und_pr, 2),
                    "topo_repouso_z": round(und_rest + HEAD_H, 2), "topo_apertado_z": round(und_pr + HEAD_H, 2),
                    "folga_fim_do_curso_mm": round(und_pr - r["borda_alta_do_furo"], 3), "haste_necessaria_mm": round(r["haste_precisa"], 3)})
    out["por_fileira"] = per
    out["altura_total_botoes_z"] = max(p["topo_repouso_z"] for p in per)
    out["processo"] = {"material": "resina SLA tough (peca unica)", "cores": "naturais brancas, sustenidos pretos, C e F brancos com a covinha (botao_textura)",
                       "acabamento": "so na fase de cotacao (lixa, verniz, brilho)", "ensaio": "4 botoes (1 por fileira) com fendas 1,00 / 1,04 / 1,08 / 1,12 antes de imprimir os 32"}
    json.dump(out, open(os.path.join(HERE, "botao.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    cortes(per)
    print(json.dumps({"haste": SHANK_L, "linhas": per, "vol": out["volume_cm3"]}, indent=1))


def cortes(per):
    """Dimensioned sections, rows 1-4, at rest and at the bottom of the stroke, with the real lid of each row (section through the hole axis, front on the left)."""
    S = 6.0
    PW = 44 * S
    STRIDE = 30 * S + 60
    W, H = int(4 * PW + 60), int(2 * STRIDE + 110)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Arial,sans-serif"><rect width="100%%" height="100%%" fill="#fbfaf6"/>' % (W, H, W, H)]

    def T(x, y, t, sz=12, a="middle", c="#222", wgt="normal"):
        o.append('<text x="%.1f" y="%.1f" font-size="%d" text-anchor="%s" fill="%s" font-weight="%s">%s</text>' % (x, y, sz, a, c, wgt, t))

    def poly(pts, fill, stroke="#222", w=1.0):
        o.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%.1f"/>' % (" ".join("%.1f,%.1f" % p for p in pts), fill, stroke, w))

    def ln(a, b, c="#1f5fa8", w=0.8, d="4,3"):
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f" stroke-dasharray="%s"/>' % (a[0], a[1], b[0], b[1], c, w, d))
    T(W / 2, 26, "eTutti Slim R6SL - botao baixo (cabeca D15 x 3,8): cortes pelo eixo, fileiras 1 a 4, em repouso e apertado (fim do curso); tampo real de cada fileira; z em mm a partir do fundo do case", 15, wgt="bold")
    T(W / 2, 46, "mesma peca nas 4 fileiras: cabeca D15 x 3,8, haste D10 x %.2f, pino D5,4 x 3,0; furo do tampo D11 sem rebaixo; frente (jogador) a esquerda" % SHANK_L, 12, c="#555")
    for col, p in enumerate(per):
        r = p["fileira"] - 1
        y0 = L.ROW_Y[r]
        for rowi, state in enumerate(("repouso", "apertado")):
            drop = TRAVEL if state == "apertado" else 0.0
            ox = 30 + col * PW + 16 * S
            zmax = per[3]["topo_repouso_z"] + 2
            ztop_panel = p["topo_repouso_z"] + 3
            base = 90 + rowi * STRIDE
            zref = p["topo_repouso_z"] + 2.0          # panel top
            Z = lambda z: base + (zref - z) * S + 14
            X = lambda dy: ox + dy * S

            T(ox + 4 * S, base - 6, "fileira %d - %s" % (p["fileira"], state), 13, wgt="bold")
            ht = L.HOUSING_TOP[r]
            zb = ht - 3.0
            # lid (real S): left = front
            ds = [i * 0.5 - 15.0 for i in range(0, 61)]
            top = [(X(d), Z(C.S(y0 + d))) for d in ds if abs(d) >= HOLE_D / 2 or False]
            left = [(X(d), Z(C.S(y0 + d))) for d in ds if d <= -HOLE_D / 2] + [(X(-HOLE_D / 2), Z(C.S(y0 - HOLE_D / 2)))]
            right = [(X(HOLE_D / 2), Z(C.S(y0 + HOLE_D / 2)))] + [(X(d), Z(C.S(y0 + d))) for d in ds if d >= HOLE_D / 2]
            lidb = ht + 0.3
            poly(left + [(X(-HOLE_D / 2), Z(lidb)), (X(-15), Z(lidb))], "#ede4cf", "#776")
            poly(right + [(X(15), Z(lidb)), (X(HOLE_D / 2), Z(lidb))], "#ede4cf", "#776")
            # housing + stem
            poly([(X(-7.0), Z(ht)), (X(7.0), Z(ht)), (X(7.0), Z(zb)), (X(-7.0), Z(zb))], "#e5e5e5", "#666")
            st = ht + STEM_ABOVE - drop
            poly([(X(-4.7), Z(st)), (X(4.7), Z(st)), (X(4.7), Z(ht - 0.5)), (X(-4.7), Z(ht - 0.5))], "#d8d0e8", "#665")
            und = st + SHANK_L
            # cap
            hr = HEAD_D / 2
            pts = [(X(-SHANK_D / 2), Z(und)), (X(-SHANK_D / 2), Z(st)), (X(-PIN_D / 2), Z(st)), (X(-PIN_D / 2), Z(st - PIN_L)), (X(PIN_D / 2), Z(st - PIN_L)), (X(PIN_D / 2), Z(st)),
                   (X(SHANK_D / 2), Z(st)), (X(SHANK_D / 2), Z(und)), (X(hr), Z(und))]
            hp = head_pts()
            pts += [(X(r_), Z(und + z_)) for r_, z_ in hp] + [(X(-r_), Z(und + z_)) for r_, z_ in reversed(hp)] + [(X(-hr), Z(und))]
            poly(pts, "#f6f1e4", "#222", 1.3)
            poly([(X(-0.52), Z(st - PIN_L)), (X(0.52), Z(st - PIN_L)), (X(0.52), Z(st - PIN_L + SOCK_DEPTH)), (X(-0.52), Z(st - PIN_L + SOCK_DEPTH))], "#fbfaf6", "#b3261e", 0.8)
            xr = X(9.0)
            hi = p["borda_alta_do_furo_z"]
            for z, t, c in ((und + HEAD_H, "topo %.2f" % (und + HEAD_H), "#1f5fa8"), (und, "base da cabeca %.2f" % und, "#1f5fa8"), (hi, "borda alta do furo %.2f" % hi, "#8a6d1f"), (st, "topo da haste %.2f" % st, "#6a4e9a")):
                dy = 9 if c == "#6a4e9a" else 0
                ln((xr - 4, Z(z)), (xr + 6, Z(z)), c)
                T(xr + 8, Z(z) + 4 + dy, t.replace(".", ","), 10, "start", c)
            if state == "apertado":
                o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#c0392b" stroke-width="2"/>' % (X(-9), Z(und), X(-9), Z(hi)))
                T(X(-9.4), Z((und + hi) / 2) + 4, ("%.2f livre" % (und - hi)).replace(".", ","), 11, "end", "#c0392b", "bold")
            else:
                o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#555" stroke-width="1.5"/>' % (X(-9), Z(und), X(-9), Z(und - TRAVEL)))
                T(X(-9.4), Z(und - TRAVEL / 2) + 4, "curso 3,5", 10, "end", "#555")
    o.append("</svg>")
    path = os.path.join(HERE, "botao_cortes_4fileiras.svg")
    open(path, "w", encoding="utf-8").write("\n".join(o))
    edge = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    if os.path.exists(edge):
        subprocess.run([edge, "--headless", "--screenshot=" + os.path.join(HERE, "botao_cortes_4fileiras.png"), "--window-size=%d,%d" % (W, H), "file:///" + path.replace("\\", "/")], capture_output=True)


if __name__ == "__main__":
    main()
