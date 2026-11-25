"""eTutti Slim (R4SL item 10): the button (keycap) study: round D5.4 pin with a female cross socket for the KS-33D's male cross. CadQuery + stdlib SVG.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/estudos/botao/botao.py
    -> estudos/botao/botao.{step,stl}, botao_corte.svg/.png, botao.json

Measured on the KS-33D STEP (fornecimento/gateron/KS-33D_FB_POM_Mini.stp, sliced every 0.5 mm, 25 Nov 2026): male cross arms +-2.00 (4.00 long) x 1.10 wide (area 7.6 mm2),
from z 4.5 up to 7.8 on the STEP's frame (stem top 8.0, so the cross tops out 0.2 mm below the stem top and is >= 3.3 mm tall). The drawing (SPEC-KS-33D-001) does not
dimension the cross: the STEP is the source, checked by the section area. The round well D5.67 is the SPEC's reading of the same STEP.
Frame of the cap: z = 0 at the skirt's lower edge, up positive; the cap sits with its skirt at 14.55 and its top at 18.55 on row 1 (SPEC 3; every row has the same cap).
"""
import json
import math
import os
import subprocess

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
SKIRT_D, SKIRT_H, TOP_H = 15.0, 0.75, 4.0           # skirt D15 (SPEC 1), dome rising to +4.0 above the skirt edge (top 18.55 - 14.55)
PIN_D, PIN_L = 5.40, 3.40                          # pin D5.4 (<= 5.5) in the D5.67 well: 0.135 mm radial; 3.4 below the skirt edge
WELL_D = 5.67
CROSS_L, CROSS_W, CROSS_H = 4.00, 1.10, 3.30        # male cross (STEP)
SOCK_L, SOCK_DEPTH = 4.20, 3.00                     # female cross: arms 0.1 longer each end (no retention there), 3.0 engaged (cross top reaches 0.2 below the stem top)
RUN = {"SLA": {"slot_w": 1.04, "tol": 0.10, "nota": "resina SLA (Tough / Durable), +-0.1: interferencia nominal 0.06 mm na largura (0.03 por face), faixa -0.04..+0.16"},
       "MJF": {"slot_w": 1.04, "tol": 0.30, "nota": "MJF PA12: +-0.3 e pó preso em fendas de 1 mm: NAO serve para a cruz (so para um botao com cruz usinada/inserida)"}}


def cap():
    prof = [(0, -PIN_L), (PIN_D / 2, -PIN_L), (PIN_D / 2, 0), (SKIRT_D / 2, 0), (SKIRT_D / 2, SKIRT_H)]
    R = ((SKIRT_D / 2) ** 2 + (TOP_H - SKIRT_H) ** 2) / (2 * (TOP_H - SKIRT_H))      # dome sphere radius
    pts = [(0, -PIN_L), (PIN_D / 2, -PIN_L), (PIN_D / 2, 0.0), (SKIRT_D / 2, 0.0), (SKIRT_D / 2, SKIRT_H)]
    n = 24
    zc = TOP_H - R
    for i in range(1, n + 1):
        a = math.asin((SKIRT_D / 2) / R) * (1 - i / n)
        pts.append((R * math.sin(a), zc + R * math.cos(a)))
    wp = cq.Workplane("XZ").polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0))
    # underside relief: a shallow dish D12.6 up to +1.4 around the pin (the skirt is a ring, the pin a boss D8 -> D5.4)
    dish = cq.Workplane("XY").workplane(offset=-0.01).circle(12.6 / 2).circle(8.0 / 2).extrude(1.4)
    wp = wp.cut(dish)
    # female cross: two slots, 0.3 lead-in chamfer by a flared start
    for ang in (0, 90):
        slot = cq.Workplane("XY").workplane(offset=-PIN_L - 0.01).rect(SOCK_L, RUN["SLA"]["slot_w"]).extrude(SOCK_DEPTH + 0.01)
        wp = wp.cut(slot.rotate((0, 0, 0), (0, 0, 1), ang))
    return wp


def main():
    c = cap()
    cq.exporters.export(c, os.path.join(HERE, "botao.step"))
    cq.exporters.export(c, os.path.join(HERE, "botao.stl"), tolerance=0.03, angularTolerance=0.1)
    vol = c.val().Volume()
    # lid hole numbers (row 1 lid: top 14.0 at the key centre, D16 through, D17 counterbore down to 12.65)
    hole_d, cb_d = 16.0, 17.0
    out = {"revisao": "R4SL", "cruz_macho": {"braco": CROSS_L, "largura": CROSS_W, "altura_min": CROSS_H, "fonte": "STEP KS-33D cortado a cada 0,5 mm (area 7,6 mm2); o desenho nao cota a cruz"},
           "poco_redondo_d": WELL_D, "pino_d": PIN_D, "folga_radial_pino_poco": round((WELL_D - PIN_D) / 2, 3), "pino_comprimento_abaixo_da_saia": PIN_L,
           "cruz_femea": {"braco": SOCK_L, "largura_slot": RUN["SLA"]["slot_w"], "profundidade": SOCK_DEPTH, "entrada_chanfro": 0.3},
           "interferencia_largura_mm": round(CROSS_W - RUN["SLA"]["slot_w"], 3), "interferencia_por_processo": {k: {"slot": v["slot_w"], "tolerancia": v["tol"], "nota": v["nota"]} for k, v in RUN.items()},
           "volume_cm3": round(vol / 1000, 3), "massa_g_resina_1p1": round(vol / 1000 * 1.1, 2)}
    # radial clearance in the lid hole
    skirt_hi = SKIRT_D + 0.15
    hole_lo = hole_d - 0.15
    out["folga_radial_furo_tampo"] = {"nominal_mm": (hole_d - SKIRT_D) / 2, "pior_caso_impressao_mm": round((hole_lo - skirt_hi) / 2, 3),
                                      "deslocamento_haste_estimado_mm": 0.20, "inclinacao_socket_graus": 0.5, "deslocamento_por_inclinacao_mm": round(10.0 * math.tan(math.radians(0.5)), 3),
                                      "margem_pior_caso_mm": round((hole_lo - skirt_hi) / 2 - 0.20 - 10.0 * math.tan(math.radians(0.5)), 3),
                                      "nota": "a folga da haste (+-0,2) e a inclinacao (0,5 graus) sao ESTIMATIVAS: a Gateron nao as publica; o ensaio dos 4 botoes mede"}
    out["alternativa_saia"] = {"saia_d": 14.8, "folga_radial_nominal": 0.6, "margem_pior_caso_mm": round(((hole_d - 0.15) - (14.8 + 0.15)) / 2 - 0.20 - 10.0 * math.tan(math.radians(0.5)), 3)}
    rows = []
    for r, dz in enumerate((0.0, 2.0, 4.0, 7.0)):
        rows.append({"fileira": r + 1, "saia_em_repouso_z": round(14.55 + dz, 2), "topo_em_repouso_z": round(18.55 + dz, 2), "saia_no_fundo_z": round(11.05 + dz, 2),
                     "carcaca_topo_z": round(10.85 + dz, 2), "folga_saia_carcaca_no_fundo": 0.2})
    out["altura_por_fileira"] = rows
    out["processo"] = {"recomendado": "SLA em resina Tough/Durable (ou nylon SLS fino), cor preta e branca; pretos = sustenidos, brancos = naturais, brancos com ponto = C e F (SPEC 1)",
                       "alternativa": "MJF PA12 para a cupula e a cruz em INSERTO (peca de latao/POM usinada) so se o ensaio mostrar que a SLA racha",
                       "acabamento": "lixar a cruz? NAO: so remover suporte; cupula polida a vapor so no MJF",
                       "onde_encomendar": "JLC3DP (SLA 8001 / Tough), PCBWay 3D, Craftcloud (agregador, entrega ao Reino Unido), Protolabs Network/Hubs UK. Nenhuma cotacao pedida."}
    out["ensaio_antes_de_imprimir_32"] = "4 botoes (1 por fileira) com slots 1,00 / 1,04 / 1,08 / 1,12 em SLA: medir a forca de saida (alvo 3-10 N) e o jogo lateral; escolher o slot e so entao imprimir 32."
    json.dump(out, open(os.path.join(HERE, "botao.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    # ---- dimensioned section (x-z), row 1, at rest and at the bottom of travel
    W, H = 150, 70
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Arial,sans-serif">' % (W, H, W * 9, H * 9), '<rect width="%d" height="%d" fill="#fff"/>' % (W, H)]
    S = 3.0

    def poly(pts, fill, stroke="#1d1d1f", w=0.15):
        o.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%.2f"/>' % (" ".join("%.2f,%.2f" % p for p in pts), fill, stroke, w))

    def T(t, x, y, s=1.8, c="#1d1d1f", a="start"):
        o.append('<text x="%.2f" y="%.2f" font-size="%.2f" fill="%s" text-anchor="%s">%s</text>' % (t if False else x, y, s, c, a, t))
    o[-1:] = o[-1:]
    T("eTutti Slim R4SL - botao: corte pelo eixo, fileira 1, em repouso (esq.) e no fundo do curso (dir.); cotas em mm", 4, 6, 2.2)
    for k, (cx, drop, name) in enumerate(((35, 0.0, "repouso"), (105, 3.5, "fundo do curso"))):
        z0 = 12.0 + drop * 0                      # drawing baseline: z = 10 at y = 62
        def P(dx, z):
            return (cx + dx * S * 0.9, 62 - (z - 10.0) * S)
        zs = 14.55 - drop                         # skirt edge
        # lid (row 1): top 14.0, counterbore D17 to 12.65, D16 hole through
        poly([P(-12, 14.0), P(-8.0, 14.0), P(-8.0, 12.65), P(-8.5, 12.65), P(-8.5, 11.15), P(-12, 11.15)], "#efe6d2")
        poly([P(12, 14.0), P(8.0, 14.0), P(8.0, 12.65), P(8.5, 12.65), P(8.5, 11.15), P(12, 11.15)], "#efe6d2")
        # housing top 10.85
        poly([P(-7.3, 10.85), P(7.3, 10.85), P(7.3, 10.0), P(-7.3, 10.0)], "#c9c9c9")
        # stem body (rect 9.4 wide) with the well D5.67 and the male cross
        zt = 14.35 - drop
        poly([P(-4.7, zt), P(-WELL_D / 2, zt), P(-WELL_D / 2, 10.85 + 1.0), P(-4.7, 10.85 + 1.0)], "#9ec5e8")
        poly([P(4.7, zt), P(WELL_D / 2, zt), P(WELL_D / 2, 10.85 + 1.0), P(4.7, 10.85 + 1.0)], "#9ec5e8")
        poly([P(-0.55, zt - 0.2), P(0.55, zt - 0.2), P(0.55, zt - 0.2 - CROSS_H), P(-0.55, zt - 0.2 - CROSS_H)], "#5b8ec2")
        # cap
        pts = [P(-PIN_D / 2, zs - PIN_L), P(PIN_D / 2, zs - PIN_L), P(PIN_D / 2, zs), P(SKIRT_D / 2, zs), P(SKIRT_D / 2, zs + SKIRT_H)]
        R = ((SKIRT_D / 2) ** 2 + (TOP_H - SKIRT_H) ** 2) / (2 * (TOP_H - SKIRT_H))
        zc = zs + TOP_H - R
        for i in range(0, 17):
            a = math.asin((SKIRT_D / 2) / R) * (1 - i / 16 * 2)
            pts.append(P(R * math.sin(a), zc + R * math.cos(a)))
        pts += [P(-SKIRT_D / 2, zs + SKIRT_H), P(-SKIRT_D / 2, zs), P(-PIN_D / 2, zs)]
        poly(pts, "#fbf9f3")
        poly([P(-0.52, zs - PIN_L), P(0.52, zs - PIN_L), P(0.52, zs - PIN_L + SOCK_DEPTH), P(-0.52, zs - PIN_L + SOCK_DEPTH)], "#ffffff", "#b3261e", 0.1)
        T(name, cx, 12, 2.0, "#1d1d1f", "middle")
        T("saia z %.2f / topo %.2f" % (zs, zs + TOP_H), cx, 15.5, 1.5, "#1f5fa8", "middle")
        T("pino D5,4 no poco D5,67 (folga radial 0,135)", cx, 18.5, 1.3, "#1d1d1f", "middle")
        T("furo D16 no tampo: folga radial 0,5 (0,35 no pior caso)", cx, 21.0, 1.3, "#1d1d1f", "middle")
    T("cruz macho 4,0 x 1,1 (STEP) / cruz femea 4,2 x 1,04, 3,0 de fundo; interferencia 0,06 na largura (SLA)", 4, 66, 1.6)
    o.append("</svg>")
    path = os.path.join(HERE, "botao_corte.svg")
    open(path, "w", encoding="utf-8").write("\n".join(o))
    edge = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    if os.path.exists(edge):
        subprocess.run([edge, "--headless", "--screenshot=" + os.path.join(HERE, "botao_corte.png"), "--window-size=1350,630", "file:///" + path.replace("\\", "/")], capture_output=True)
    print(json.dumps({k: out[k] for k in ("interferencia_largura_mm", "folga_radial_furo_tampo", "alternativa_saia", "volume_cm3")}, indent=1))


if __name__ == "__main__":
    main()
