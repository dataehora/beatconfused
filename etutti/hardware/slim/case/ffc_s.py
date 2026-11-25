"""eTutti Slim (R5SL item 4): S-curve of the FFC between a ruler and the main board (two equal tangent arcs, mouths 5.5 mm apart, level change dz). Stdlib only.
    python etutti/hardware/slim/case/ffc_s.py -> case/out/ffc_s.json
Cable thickness 0.3 (assumed, FFC 1.0 mm pitch), minimum static bend radius taken as 10 x T = 3.0 mm (conservative; 5 x T = 1.5 is the usual lower limit): both ESTIMATES, no datasheet read.
"""
import json, math, os
H, T, INS = 5.5, 0.3, 3.4
out = {"vao_horizontal": H, "espessura_assumida": T, "raio_minimo_regra_10T": 10 * T, "insercao_por_ponta": INS, "fileiras": []}
for r, dz in enumerate((-3.0, -1.0, 1.0, 4.0), 1):
    a = abs(dz)
    th = 2 * math.atan(a / H)                      # tan(theta/2) = dz/h for two equal arcs
    R = H / (2 * math.sin(th)) if th > 1e-9 else float("inf")
    L = 2 * R * th
    out["fileiras"].append({"fileira": r, "dz": dz, "raio_no_corte_mm": round(R, 2), "comprimento_livre_S_mm": round(L, 2), "cabo_minimo_mm": round(L + 2 * INS, 1),
                            "folga_com_30mm_mm": round(30 - 2 * INS - L, 1), "folga_com_20mm_mm": round(20 - 2 * INS - L, 1)})
out["conclusao"] = "30 mm NAO cabe: sobram 16-17 mm de cabo num vao de 5,5 mm (laco de >= 7 mm fora do plano); 20 mm sob medida (sobra 6-7 mm, absorvida por uma barriga rasa)."
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "ffc_s.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(out["fileiras"]))
