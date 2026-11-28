"""eTutti Slim (R4SL): the Design's envelope for the MAIN board (what the electronics may use). CadQuery only through case.py's constants.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/envelope_principal.py   -> case/envelope_principal.json

Frame = the instrument's (x right, y BACK, z up from the base's bottom).  The board hangs at z 6.8 (bottom face) .. 8.0, parts on the BOTTOM face only (JLCPCB).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402
import layout_slim as L  # noqa: E402

STRIP_X0, STRIP_X1 = -58.5, float(os.environ.get("SLIM_STRIP_X1", -36.3))          # the strip under the knobs (the bay's right wall ends at -58.8)
Y_FRONT, Y_BACK = -9.0, 68.1               # back: 0.5 mm from the wall's inner face (68.6)
TAB_X1, TAB_HALF = -26.75, 5.5             # tabs for rows 1 and 3: the FFC gap is the same 5.5 mm on the four rows
FOOT_X0, FOOT_Y0 = C.LEFT + 2.0 + 0.2, 47.0    # foot: from the left wall (0.2 gap) to the strip; its front edge 0.3 behind the bay's back wall (46.7)
CORNER_CUT = (3.0, 2.8)                    # chamfer at the back-left corner (the wall's inner corner radius is 4)


def outline():
    r1, r3 = L.ROW_Y[0], L.ROW_Y[2]
    return [(STRIP_X0, Y_FRONT), (STRIP_X1, Y_FRONT), (STRIP_X1, r1 - TAB_HALF), (TAB_X1, r1 - TAB_HALF), (TAB_X1, r1 + TAB_HALF), (STRIP_X1, r1 + TAB_HALF),
            (STRIP_X1, r3 - TAB_HALF), (TAB_X1, r3 - TAB_HALF), (TAB_X1, r3 + TAB_HALF), (STRIP_X1, r3 + TAB_HALF), (STRIP_X1, Y_BACK),
            (FOOT_X0 + CORNER_CUT[0], Y_BACK), (FOOT_X0, Y_BACK - CORNER_CUT[1]), (FOOT_X0, FOOT_Y0), (STRIP_X0, FOOT_Y0)]


def main():
    ffc = []
    for r in range(4):
        x_edge = TAB_X1 if r in (0, 2) else STRIP_X1
        x_ruler = L.ROW_X0[r] - L.U_KEY1
        ffc.append({"fileira": r + 1, "ref": "J60%d" % (r + 1), "y": round(L.ROW_Y[r], 3), "x_borda_placa": x_edge, "boca": "+x", "x_regua_esquerda": round(x_ruler, 3),
                    "folga_horizontal_mm": round(x_ruler - x_edge, 2), "z_regua_baixo": round(L.RULER_BOT[r], 2), "dz_ate_placa_mm": round(L.RULER_BOT[r] - 6.8, 2)})
    env = {"revisao": "R4SL", "quadro": "instrumento: x direita, y TRAS, z de baixo da base; placa com a face de baixo em z 6,8, 1,2 mm, pecas SO na face de baixo",
           "placa": {"z_baixo": C.BOARD_BOT, "espessura": C.BOARD_T, "contorno": [(round(x, 3), round(y, 3)) for x, y in outline()],
                     "faixa": {"x": [STRIP_X0, STRIP_X1], "y": [Y_FRONT, Y_BACK]}, "pe": {"x": [FOOT_X0, STRIP_X0], "y": [FOOT_Y0, Y_BACK]},
                     "abas_ffc": {"x_ate": TAB_X1, "meia_largura": TAB_HALF, "fileiras": [1, 3]}},
           "paredes_internas": {"esquerda_x": C.LEFT + C.WALL, "tras_y": C.BACK - C.WALL, "frente_y": C.FRONT + C.WALL, "raio_canto_interno": 4.0},
           "folga_sob_a_placa_mm": {"geral": round(C.BOARD_BOT - 1.6, 2), "sob_o_P2_bolso": round(C.BOARD_BOT - 1.6 + 0.6, 2), "bolso_x": [C.P2_POCKET[0], C.P2_POCKET[2]], "bolso_y": [C.P2_POCKET[1], C.P2_POCKET[3]]},
           "pilares": {"d": 6.0, "pontos": C.POSTS, "furo_placa_d": 2.2, "parafuso": "M2 por cima, autoatarraxante no pilar (piloto 1,75)", "proibido_sob_pilar": "peca na face de baixo num disco de 6,4 mm"},
           "baia_bateria": {"x": [C.BAY[0], C.BAY[2]], "y": [C.BAY[1], C.BAY[3]], "parede_direita_x": [C.BAY[2], C.BAY[2] + 1.2], "altura_parede_z": 7.0, "bateria": "VARTA 56457 201 016: 34,5 x 52,0 x 5,35 (STEP 5,36)",
                          "saida_dos_fios": {"x": [C.WIRE_SLOT[0], C.WIRE_SLOT[1]], "y": C.BAY[3], "z_de": C.WIRE_SLOT[2], "destino": "J202 (JST SH 3 vias, boca para -y), entre x -80 e -66, y 49-52"}},
           "knobs": {"registros": {"eixo": list(C.REG), "sensor": "U401 TMAG5273A2 no eixo, face de baixo"},
                     "volume": {"eixo": list(C.VOL), "sensor": "U402 TMAG5273B2 no eixo", "chave_off": {"pos": [round(C.VOL[0] - 7.2 * 0.7071, 2), round(C.VOL[1] - 7.2 * 0.7071, 2)], "peca": "U403 DRV5032ZE, ima de OFF Ø4 x 2,0 a 7,2 mm, 225 graus"},
                                "anel_led": {"raio_interno": C.RING_ID / 2, "raio_externo": C.RING_OD / 2, "led": "D401 a 11,0 mm do eixo, a 90 graus (atras)"}},
                     "plataforma_d": 2 * C.PLAT_R, "regra": "nada sob o ima alem do sensor; o ima fica ACIMA da placa (z 8,5-11,0)"},
           "conectores": {"usb_c": {"x": C.USB[0], "parede": "tras", "z_centro": C.USB[1], "abertura": [C.USB[2], C.USB[3]]}, "p2": {"y": C.P2[0], "parede": "esquerda", "z_centro": C.P2[1], "furo_d": C.P2[2]}},
           "ffc": ffc, "cabos_ffc": "4 cabos iguais, retos; a boca da placa olha +x, a da regua olha -x",
           "alturas": {"regra": "(a) peca mais baixa, (b) face de cima soldada em casa, (c) subir o conjunto", "limite_peca_sob_a_placa_mm": round(C.BOARD_BOT - 1.6 - 0.2, 2)},
           "avisos": ["a bateria (z 1,6-6,95) fica FORA da placa: a parede da baia (x -60..-58,8) toca a placa em z 7,0 > 6,8, por isso a faixa comeca em x -58,5",
                      "o LED reverso precisa de janela na placa sob o anel (a definir com a folha do LED)"]}
    saida = os.environ.get("SLIM_ENV_OUT") or os.path.join(HERE, "envelope_principal.json")   # SLIM_STRIP_X1 / SLIM_ENV_OUT: test hooks (a narrower strip, written elsewhere)
    json.dump(env, open(saida, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("envelope_principal.json", len(env["placa"]["contorno"]), "vertices")


if __name__ == "__main__":
    main()
