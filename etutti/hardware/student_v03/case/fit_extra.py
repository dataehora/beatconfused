"""eTutti Student V3: the extra measurements the SPEC v4 asked for (questions C1-C13), beyond fit_check.py.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v03/case/fit_extra.py

Run after case.py and fit_check.py. Writes out/fit_extra.json.
"""
import json
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import case as K           # noqa: E402
import geometria as G      # noqa: E402
import fit_check as F      # noqa: E402

res = {}
tray = F.step("base")
lid = F.step("tampa")
C = F.components()
FP = F.FP
INFO = F.INFO


def d(a, b):
    return round(F.dist(a, b), 3)


# ---- C2: the tray against every part on the bottom of the board, the smallest gaps and where
rows = []
for f in FP:
    if not f["bottom"] or f["lib"].startswith(("MountingHole", "TestPoint")) or f.get("dnp"):
        continue
    ref = f["ref"]
    h = f["height"] or F.DEFAULT_H.get(ref) or 1.0
    x0, y0, x1, y1 = f["box"]
    s = K.box(x0 + 0.25, y0 + 0.25, x1 - 0.25, y1 - 0.25, -K.T_PCB - h, -K.T_PCB)
    rows.append((ref, f["value"], h, round(((x0 + x1) / 2), 1), round(((y0 + y1) / 2), 1), d(s, tray)))
rows.sort(key=lambda r: r[-1])
res["C2_bandeja_ate_pecas_do_verso"] = [dict(zip(("ref", "valor", "altura_mm", "x", "y", "folga_mm"), r)) for r in rows[:10]]
res["C2_H101"] = {"porca_ate_a_bandeja_mm": d(C["porca do H101"], tray), "parafuso_ate_a_bandeja_mm": d(C["parafuso do H101"], tray),
                  "ponta_do_parafuso_z": -8.0, "piso_no_recesso_z": [K.Z0 + K.FLOOR - K.H101_RECESS[1]]}
res["C2_modulo_ate_o_piso_mm"] = d(C["modulo MicroMod"], tray)
res["C2_jacks_e_USB_ate_a_borda_da_bandeja_mm"] = {r: d(C[r], tray) for r in ("J201", "J301", "J302")}
res["C2_copos_da_grade"] = {"topo_do_copo_z": -K.T_PCB, "folga_do_parafuso_e_porca_ate_o_piso_mm": round(K.Z0 + K.FLOOR + K.NUT_POCKET_H - 0, 2)}

# ---- C3: wall under the sockets' holes
ch = G.HOLE_CHAMFER
res["C3_parede_abaixo_dos_furos"] = {
    "USB-C": {"boca_inferior_z": round(K.USB["z"] - K.USB["h"] / 2 - ch, 2), "face_reta_ate_o_chanfro_mm": round(K.USB["z"] - K.USB["h"] / 2 - ch - (K.Z0 + K.BASE_CHAMFER), 2)},
    "OUT/IN": {"boca_inferior_z": round(G.JACK_Z - K.JACK_D / 2 - ch, 2), "face_reta_ate_o_chanfro_mm": round(G.JACK_Z - K.JACK_D / 2 - ch - (K.Z0 + K.BASE_CHAMFER), 2)},
    "chanfro_inferior_comeca_em_z": K.Z0 + K.BASE_CHAMFER, "parede_na_borda_de_baixo_mm": K.WALL - K.BASE_CHAMFER}

# ---- C4: the battery in its new place
bat = C["bateria"]
b4 = {}
for ref in ("J302", "J301", "U501", "C502", "R501", "C501", "J202", "J101"):
    f = next((x for x in FP if x["ref"] == ref), None)
    if not f:
        continue
    if ref in C:
        s = C[ref]
    else:
        h = f["height"] or F.DEFAULT_H.get(ref) or 1.0
        x0, y0, x1, y1 = f["box"]
        s = K.box(x0 + 0.25, y0 + 0.25, x1 - 0.25, y1 - 0.25, -K.T_PCB - h, -K.T_PCB) if f["bottom"] else K.box(x0 + 0.25, y0 + 0.25, x1 - 0.25, y1 - 0.25, 0, h)
    b4[ref] = d(bat, s)
res["C4_bateria_ate"] = b4
res["C4_bateria"] = {"x": [K.BATTERY[0], K.BATTERY[2]], "y": [K.BATTERY[1], K.BATTERY[3]], "z": [K.Z0 + K.FLOOR, K.Z0 + K.FLOOR + K.BATTERY[4]]}

# ---- C5: the screen module turned round
mod = C["modulo da tela"]
res["C5_modulo_da_tela"] = {"ate_a_tampa_mm": d(mod, lid), "ate_os_encoders_mm": d(mod, C["encoders"]), "ate_a_cabeca_do_parafuso_H101_mm": d(mod, C["parafuso do H101"]),
                            "centro": list(K.oled_centre()), "postes": K.oled_posts(), "fundo_do_modulo_z": INFO["niveis"]["oled"]["pcb_bottom"],
                            "teto_plano_comeca_em_y": K.WALL + K.chamfer_inner()[0], "borda_de_tras_y": K.oled_centre()[1] - K.OLED_PCB[1] / 2}
# the flat part of the ceiling starts at y = 2.0 + 4.54; a post of D 3.2 at y = 8.2
ys = [p[1] for p in K.oled_posts()]
res["C5_postes_na_parte_plana_do_teto"] = {"y_do_poste_mais_proximo_da_parede": min(ys), "raio": 1.6,
                                           "folga_ate_o_inicio_da_parte_plana_mm": round(min(ys) - 1.6 - (K.WALL + K.chamfer_inner()[0]), 2)}

# ---- C6: J401 and the cable
j401 = next(f for f in FP if f["ref"] == "J401")
sl = (32.0, 29.92, 39.0, 32.42)
pin_y = K.oled_centre()[1] + K.OLED_PCB[1] / 2 - 1.5
vert = INFO["niveis"]["oled"]["pcb_bottom"] - (-K.T_PCB - 1.5)
res["C6_J401"] = {"posicao": [j401["x"], j401["y"]], "rotacao_graus": j401["rot"], "caixa": j401["box"],
                  "fenda": sl, "pinos_do_modulo_y": round(pin_y, 2), "subida_z_mm": round(vert, 2),
                  "percurso_minimo_mm": round(math.hypot(j401["y"] - (sl[1] + sl[3]) / 2, 0) + vert + abs(pin_y - (sl[1] + sl[3]) / 2) + 2.0, 1)}

# ---- C10: encoders against the new ceiling (the V1's EC11E model: body, bushing, shaft)
enc_model = os.path.join(HERE, "..", "..", "student_v01", "model3d", "modelos", "encoder_EC11E_C255515.step")
if os.path.exists(enc_model):
    bb = cq.importers.importStep(enc_model).val().BoundingBox()
    res["C10_modelo_EC11E_V1"] = {"z": [round(bb.zmin, 2), round(bb.zmax, 2)], "x": [round(bb.xmin, 2), round(bb.xmax, 2)], "y": [round(bb.ymin, 2), round(bb.ymax, 2)]}
enc2 = os.path.join(HERE, "modelos", "encoder_EC11E18244AU_C202365.step")
if os.path.exists(enc2):
    bb2 = cq.importers.importStep(enc2).val().BoundingBox()
    res["C10_modelo_EC11E18244AU_C202365"] = {"z": [round(bb2.zmin, 2), round(bb2.zmax, 2)], "corpo_ate_z": 4.5, "colar_d8_z": [4.5, 5.0],
                                              "bucha_d7_z": [5.0, 11.5], "eixo_d6_z": [12.5, 24.5], "pernas_abaixo_da_placa_mm": 3.5,
                                              "eixo_acima_do_tampo_mm": round(bb2.zmax - K.ZT, 2), "sobra_do_eixo_acima_do_knob_mm": round(bb2.zmax - K.KNOB["top"], 2),
                                              "folga_da_bucha_ate_o_teto_mm": round(K.ZT - K.LID_T - 11.5, 2)}
res["C10_encoders"] = {"corpo_ate_z": 4.5, "bucha_ate_z": 11.5, "eixo_ate_z": K.KNOB["shaft_top"], "teto_interno_z": K.ZT - K.LID_T,
                       "bucha_dentro_do_furo_da_tampa": "sim (7 mm no furo de 9,2)", "tampa_ate_encoders_mm": d(lid, C["encoders"]),
                       "knob_encaixe_mm": round(K.KNOB["shaft_top"] - (K.ZT + K.KNOB["gap"]), 2)}

# ---- C12/C13: the thin lid over the grid and the buttons' gap to the well's rounded edge
res["C12_tampa_sobre_a_grade"] = {"espessura_mm": round(K.ZT - K.GRID_ROOF, 2), "aresta_R_mm": K.WELL_R_TOP,
                                  "parede_reta_na_boca_do_poco_mm": round(K.ZT - K.GRID_ROOF - K.WELL_R_TOP, 2),
                                  "folga_da_tampa_ate_a_cabeca_escareada_mm": round(K.GRID_ROOF - K.GRID_Z1, 2)}
# the lid's thickness above the grid where the chamfer cuts the corner (front and back edges)
ang = math.atan2(K.CHAMFER[1], K.CHAMFER[0])
slope = K.CHAMFER[1] / K.CHAMFER[0]
dmin = 100.0 - (G.ROWS[0][1] + G.GRID_EDGE)            # grid's front edge to the outer wall
res["C12_tampa_sobre_a_grade"]["distancia_da_borda_da_grade_a_parede_externa_mm"] = round(dmin, 2)
res["C12_tampa_sobre_a_grade"]["espessura_minima_no_chanfro_frente_e_fundo_mm"] = round((K.ZT - K.CHAMFER[1] + dmin * slope) - K.GRID_ROOF, 2)
res["C13_botao_ate_a_aresta_do_poco_mm"] = {"lateral_do_botao_da_1a_fileira": round(G.WELL_WALL - K.BUTTON_D / 2, 2)}

# ---- C9: volumes
v2 = json.load(open(os.path.join(HERE, "..", "..", "student_v02", "case", "out", "case.json"), encoding="utf-8"))["pecas"]
res["C9_volumes_cm3"] = {"tampa_v2": v2["tampa"]["volume_cm3"], "base_v2": v2["base"]["volume_cm3"], "tampa_v3": INFO["pecas"]["tampa"]["volume_cm3"],
                         "bandeja_v3": INFO["pecas"]["base"]["volume_cm3"], "caixa_acustica_v2": v2["caixa_acustica"]["camara_cm3"],
                         "caixa_acustica_v3": INFO["pecas"]["caixa_acustica"]["camara_cm3"]}
json.dump(res, open(os.path.join(K.OUT, "fit_extra.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
