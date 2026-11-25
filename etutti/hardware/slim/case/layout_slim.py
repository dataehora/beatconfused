"""eTutti Slim (R3SL): the keyboard + ruler/grade envelope, one source of truth for the case and for the ruler board. Stdlib only.

    python etutti/hardware/slim/case/layout_slim.py     -> case/envelope_regua.json   (the Design's contract with the ruler placement)

Instrument frame (SPEC section 1): x to the right (treble), y towards the back, origin = centre of key A3 of row 1, z up from the bottom of the base.
Ruler frame (the electronics): u along the ruler from its LEFT end, v across, +v towards the player, v = 0 on the row's centre line.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- keyboard (SPEC 1, fixed)
P = 18.5
D = math.sqrt(P * P - (P / 2) ** 2)                 # 16.0156 between rows
ROW_X0 = [0.0, -P / 2, 0.0, -P / 2]                 # first key centre of rows 1..4
ROW_Y = [r * D for r in range(4)]
NOTES = [["A3", "C4", "D#4", "F#4", "A4", "C5", "D#5", "F#5"],
         ["G3", "A#3", "C#4", "E4", "G4", "A#4", "C#5", "E5"],
         ["G#3", "B3", "D4", "F4", "G#4", "B4", "D5", "F5"],
         ["F#3", "A3", "C4", "D#4", "F#4", "A4", "C5", "D#5"]]
MIDI = [[57, 60, 63, 66, 69, 72, 75, 78], [55, 58, 61, 64, 67, 70, 73, 76], [56, 59, 62, 65, 68, 71, 74, 77], [54, 57, 60, 63, 66, 69, 72, 75]]
HOUSING_TOP = [10.85, 12.85, 14.85, 17.85]          # top of the KS-33D housing, rows 1..4 (SPEC 3: steps 2, 2, 3)
PCB_TOP = [h - 5.85 for h in HOUSING_TOP]           # top of the ruler (5.0, 7.0, 9.0, 12.0)
RULER_T = 1.2
RULER_BOT = [t - RULER_T for t in PCB_TOP]          # 3.8, 5.8, 7.8, 10.8
GRADE_BOT = [t + 1.3 for t in PCB_TOP]              # 6.3, 8.3, ...
GRADE_T = 1.2

# ---- ruler R8 (SPEC 5.1) and grade
NKEYS = 8
HOUSING = 14.6                                      # KS-33D housing, top part
BODY = 14.0                                         # KS-33D body = grade hole
TAIL = 14.0                                         # beyond the first key's housing edge (SPEC 5.1)
U_KEY1 = TAIL + HOUSING / 2                         # 21.3 -> use 21.25 so that the length is exactly 160
TAIL_G = 1.5                                        # R11SL: the ruler grows only 0.5 mm to the LEFT (keys move +0.5 along it): J1 -> U9/C9/C10 -> M2 -> key 1, see ELETRONICA.md
U_KEY1 = 21.25 + TAIL_G
M2_CLEAR = 9.65                                     # M2 axis to the key's centre: head D3.8 stops 0.45 before the KS-33D flange (edge at key -7.3), nut clear of pegs/post
M2_ENDS = (U_KEY1 - M2_CLEAR, U_KEY1 + 7 * 18.5 + M2_CLEAR)   # R11SL: ONE M2 per end, on the axis (v = 0): 12.1 and 160.9
GUIDE_D = 6.0                                       # centred guide (pedestal) in the base under each M2: hex pocket for the nut (4.6 across corners), 0.7 mm walls
END_PAST = 3.0                                      # ruler end beyond the right M2 axis (the oblong slot's end + the nut's 2.3 + 0.2)
RULER_L = M2_ENDS[1] + END_PAST                     # 163.9 (R9SL 167.5, R10SL 171.3)
RULER_W = 15.0
GRADE_W = 16.0
GRADE_U0 = M2_ENDS[0] - 3.0                        # R11SL: the grade reaches both M2 (it is clamped by both): 9.1 ... RULER_L
GRADE_U1 = RULER_L
GRADE_HOLE = 14.00                                  # R4SL item 4: nominal 14.00 (+0.05 / -0.02) with DOG-BONE relief in the corners (the cutter's +-0.1 is a risk, RESTRICOES R28)
GRADE_DOGBONE = (0.25, 0.60)                        # relief circle: centre 0.25 mm in from the corner along both edges, radius 0.60
GRADE_CSK = None                                    # R9SL: no countersink (the M2 are beyond the keys; a pan head D3.8 x 1.6 fits under the lid)
M2_V = (0.0, 0.0)                                  # R11SL: both on the axis
M2_SLOT = (None, 3.2)                               # R11SL: left round (near the FFC, positions the ruler); right OBLONG 2.2 x 3.2 along the ruler (absorbs the length tolerance)
M2_D = 2.2
PEG_DX, PEG_D, POST_D = 5.08, 1.70, 5.20            # KS-33D PCB holes (Gateron drawing "Layout of PCB")
SENSOR_V = 4.3                                      # TMAG5253 centre, from the key centre, towards the PLAYER (the magnet side of the switch)
SPACER_H = 1.3                                      # ruler top -> grade bottom (SPEC 3: 5.0 -> 6.3)

# ---- base (Design's decisions)
FLOOR_T = 1.6
RAIL_W = 1.5                                        # continuous support rails under the long edges of every ruler (|v| = 6.0 .. 7.5)
POST_POCKET_D, POST_BOTTOM = 5.8, 1.0               # pocket under every post of row 1 (the post reaches z 1.3): floor under the pocket >= 1.0
FFC_H = 1.0                                         # KH-FPC0.5-H1.0SMT-8P (C3250113)
FFC_U = 2.2                                         # connector origin (u): mouth towards -u at the ruler's left edge (stays at the end: the ruler grows to the left)
TAIL_U = {"U9": TAIL_G + 6.2, "C9": (TAIL_G + 6.2, -3.4), "C10": (TAIL_G + 8.6, -4.9)}   # R11SL: head parts (old U9 9.2): J1 ends at u 4.05, U9 6.7 (pátio 4.45..8.95), the left guide (D6.0 at u 12.1) starts at 9.1
SPLIT_Z = 8.0                                       # base walls end here (the main board's top face)


def ruler(r):
    x_left = ROW_X0[r] - U_KEY1
    return {"row": r + 1, "y": ROW_Y[r], "x_left": round(x_left, 3), "x_right": round(x_left + RULER_L, 3),
            "z_bottom": round(RULER_BOT[r], 3), "z_top": round(PCB_TOP[r], 3), "grade_z_bottom": round(GRADE_BOT[r], 3),
            "keys": [{"idx": r * NKEYS + k + 1, "k": k + 1, "note": NOTES[r][k], "midi": MIDI[r][k], "u": U_KEY1 + P * k,
                      "x": round(ROW_X0[r] + P * k, 3), "y": round(ROW_Y[r], 3)} for k in range(NKEYS)],
            "m2_u": list(M2_ENDS), "m2_v": list(M2_V), "m2_slot": list(M2_SLOT)}


def contract():
    rs = [ruler(r) for r in range(4)]
    return {
        "revisao": "R4SL", "quadro": "u ao longo da regua a partir da ponta ESQUERDA, v atravessado, +v para o jogador, v = 0 na linha do centro das teclas",
        "regua": {"comprimento": RULER_L, "largura": RULER_W, "espessura": RULER_T, "cauda_alem_da_carcaca": TAIL, "u_tecla1": U_KEY1, "passo": P,
                  "u_teclas": [U_KEY1 + P * k for k in range(NKEYS)], "furos_switch": {"poste_d": POST_D, "pino_d": PEG_D, "pino_dx": PEG_DX},
                  "sensor_v": SENSOR_V, "cauda_g": TAIL_G, "u9_dx": TAIL_U["U9"] - 9.2, "guia_d": GUIDE_D, "head_u": {"U9": TAIL_U["U9"], "C9": list(TAIL_U["C9"]), "C10": list(TAIL_U["C10"])}, "m2_u": rs[0]["m2_u"], "m2_d": M2_D, "m2_v": rs[0]["m2_v"], "m2_slot": rs[0]["m2_slot"],
                  "ffc": {"u_origem": FFC_U, "v": 0.0, "boca": "-u (esquerda)", "altura": FFC_H, "saida": "-x, cabo FFC horizontal"}},
        "grade": {"u0": GRADE_U0, "u1": GRADE_U1, "largura": GRADE_W, "espessura": GRADE_T, "furo": GRADE_HOLE, "dogbone": {"recuo": GRADE_DOGBONE[0], "raio": GRADE_DOGBONE[1]}, "m2_escareado": None, "m2_v": rs[0]["m2_v"], "m2_slot": rs[0]["m2_slot"],
                  "m2_u": rs[0]["m2_u"], "m2_d": M2_D, "separador_h": SPACER_H},
        "base": {"piso": FLOOR_T, "trilhos_largura": RAIL_W, "trilhos_v": [6.0, 7.5], "bolso_poste": {"d": POST_POCKET_D, "fundo_z": POST_BOTTOM, "so_fileira": 1},
                 "regua_baixo_z": [round(z, 3) for z in RULER_BOT], "regua_topo_z": [round(z, 3) for z in PCB_TOP],
                 "livre_sob_a_regua": [round(z - FLOOR_T, 3) for z in RULER_BOT], "zona_livre_v": [-6.0, 6.0],
                 "porca_m2": {"altura": 1.6, "d": 4.6}, "cabeca_m2_topo_z": [round(z + SPACER_H + GRADE_T + 1.6, 2) for z in PCB_TOP]},
        "fileiras": rs,
        "ordem_indice": "indice = 8*(fileira-1) + posicao (1 = esquerda); teclas_u cresce para os agudos",
    }


if __name__ == "__main__":
    c = contract()
    json.dump(c, open(os.path.join(HERE, "envelope_regua.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for r in c["fileiras"]:
        print("fileira %d: x %.2f..%.2f, y %.2f, z %.1f..%.1f, M2 u %s, %d teclas (%s ... %s)" % (r["row"], r["x_left"], r["x_right"], r["y"], r["z_bottom"],
              r["z_top"], r["m2_u"], len(r["keys"]), r["keys"][0]["note"], r["keys"][-1]["note"]))
    print("envelope_regua.json")
