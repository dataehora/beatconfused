"""eTutti Slim (R4SL): sections S1 / S2 / S3 of the two magnetic knobs on the sloped lid (7.1 deg). CadQuery (only for case.S) + stdlib SVG.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/knobs_s123.py   -> case/img/knobs_s123.{svg,png}, case/out/knobs_s123.json

Section plane x = -46 (through both knob axes), y to the right (BACK of the instrument), z up.  Three solutions for the platform on the sloped lid:
  S1  flat disc D26 (R3SL): platform and knob axis vertical, well floor flat and 1.2 deep everywhere; the disc stands proud of the lid in front, sinks behind it;
  S2  (preferred; official model) the platform FOLLOWS the lid (lid + 1.0 registers / + 0 volume), axis VERTICAL, magnet horizontal, knob top flat and horizontal,
      well floor HORIZONTAL (shallow in front, deep behind);
  S3  axis PERPENDICULAR to the lid (magnet tilted 7.1 deg), reference only; the angle error at the sensor is computed below.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402

OUT = os.path.join(HERE, "out")
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
THETA = math.atan((C.ROWZ[1] - C.ROWZ[0]) / C.L.D)          # 7.1 deg
KNOB_D, KNOB_TOP = 16.4, 4.8
STEM_D, HEAD_Z0, HEAD_Z1 = 5.0, 9.0, 11.0
MAG_D, MAG_L, MAG_Z0 = 6.0, 2.5, 8.5
INK, BLUE, RED, GREY, LID, KNOB, PCB, MAG = "#1d1d1f", "#1f5fa8", "#b3261e", "#8b8b8b", "#efe6d2", "#fbf9f3", "#2f6b3a", "#c0392b"


def numbers():
    res = {}
    for name, (cx, cy), rise in (("registros", C.REG, 1.0), ("volume", C.VOL, C.S2_RISE_VOL)):
        zc = C.S(cy) + rise
        zf = C.S(cy - C.WELL_D / 2) + rise - 0.1
        r_in, r_out = C.WELL_D / 2, C.PLAT_R
        f_in, b_in = C.S(cy - r_in) + rise, C.S(cy + r_in) + rise
        f_out, b_out = C.S(cy - r_out) + rise, C.S(cy + r_out) + rise
        s1_top = C.S(cy) + (1.0 if name == "registros" else 0.0)
        d = {"S1": {"topo_plataforma_z": round(s1_top, 2), "acima_do_tampo_frente_mm": round(s1_top - C.S(cy - r_out), 2), "abaixo_do_tampo_tras_mm": round(C.S(cy + r_out) - s1_top, 2),
                    "poco_fundo_z": round(s1_top - 1.2, 2), "profundidade_poco_mm": [1.2, 1.2], "folga_axial_ima_mm": 0.8},
             "S2": {"topo_plataforma_frente_z": round(f_out, 2), "topo_plataforma_tras_z": round(b_out, 2), "poco_fundo_z": round(zf, 2),
                    "profundidade_no_eixo_mm": round(zc - zf, 2), "profundidade_poco_borda_frente_mm": round(f_in - zf, 2), "profundidade_poco_borda_tras_mm": round(b_in - zf, 2),
                    "vao_sob_o_knob_atras_mm": round(b_in - (zf + 0.3), 2), "topo_do_knob_z": round(zc + KNOB_TOP, 2),
                    "knob_acima_do_tampo_frente_mm": round(zc + KNOB_TOP - f_in, 2), "knob_acima_do_tampo_tras_mm": round(zc + KNOB_TOP - b_in, 2), "folga_axial_ima_mm": 0.8},
             "S3": {"inclinacao_graus": round(math.degrees(THETA), 2), "profundidade_poco_mm": [1.2, 1.2],
                    "erro_de_angulo_pico_graus": round(math.degrees(math.atan(1.0 / math.cos(THETA))) - 45.0, 3),
                    "deslocamento_lateral_do_ima_na_haste_mm": round(2.75 * math.sin(THETA), 2)}}
        res[name] = d
    return res


def build():
    N = numbers()
    W, H = 250, 200
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Arial,sans-serif">' % (W, H, W * 6, H * 6), '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H)]

    def T(txt, x, y, s=1.6, c=INK, a="start"):
        o.append('<text x="%.2f" y="%.2f" font-size="%.2f" fill="%s" text-anchor="%s">%s</text>' % (x, y, s, c, a, txt))

    def poly(pts, fill, stroke=INK, w=0.15, op=1):
        o.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%.2f" opacity="%.2f"/>' % (" ".join("%.2f,%.2f" % p for p in pts), fill, stroke, w, op))

    def line(a, b, c=INK, w=0.15, dash=None):
        o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f"%s/>' % (a[0], a[1], b[0], b[1], c, w, ' stroke-dasharray="%s"' % dash if dash else ""))

    T("eTutti Slim R5SL - knobs (S2 com saia D18,4 no poco D19,0) no tampo inclinado (7,1 graus): S1 plano / S2 segue o tampo (oficial) / S3 eixo perpendicular. Corte x = -46, frente (jogador) a esquerda, z em mm.", 4, 6, 2.4)
    for row, (name, (cx, cy), rise) in enumerate((("REGISTROS", C.REG, 1.0), ("VOLUME", C.VOL, 1.0))):
        for col, mode in enumerate(("S1", "S2", "S3")):
            ox = 6 + col * 82            # drawing x of y = cy - 14
            oz0 = 80 + row * 85          # drawing y of z = z0
            rise = 1.0
            zc = C.S(cy) + rise
            zbase = 6.0                  # z drawn at oz0 (the board's level)
            # lid profile
            def X(y):
                return ox + (y - (cy - 14.5)) * 2.6

            def Zd(z):
                return oz0 - (z - zbase) * 2.6

            ys = [cy - 14.5 + i * 0.5 for i in range(0, 59)]
            lid_top = [(X(y), Zd(C.S(y))) for y in ys]
            lid_bot = [(X(y), Zd(C.S(y) - C.SKIN)) for y in reversed(ys)]
            poly(lid_top + lid_bot, LID, INK, 0.12)
            # boss / platform
            if mode == "S1":
                zp = C.S(cy) + (1.0 if row == 0 else 0.0)
                zc = zp
                poly([(X(cy - 13), Zd(zp)), (X(cy + 13), Zd(zp)), (X(cy + 13), Zd(zp - 2.7)), (X(cy - 13), Zd(zp - 2.7))], LID, INK, 0.12)
                zf = zp - 1.2
                tilt = 0.0
            elif mode == "S2":
                top = [(X(y), Zd(C.S(y) + rise)) for y in [cy - 13 + i * 0.5 for i in range(0, 53)]]
                zf = C.S(cy - C.WELL_D / 2) + rise - 0.1
                poly(top + [(X(cy + 13), Zd(zf - 1.5)), (X(cy - 13), Zd(zf - 1.5))], LID, INK, 0.12)
                tilt = 0.0
            else:
                tilt = THETA
                zp = zc
                zf = zp - 1.2
                c, s = math.cos(tilt), math.sin(tilt)
                # platform as a slab perpendicular to the axis through (cy, zp): corners in the tilted frame
                def R(dy, dz):          # tilted frame: rotates (dy, dz) by +tilt about the point (cy, zp)
                    return (X(cy + dy * c - dz * s), Zd(zp + dy * s + dz * c))
                poly([R(-13, 0), R(13, 0), R(13, -2.7), R(-13, -2.7)], LID, INK, 0.12)
            # well (white), knob, stem, head, magnet, board
            if mode == "S3":
                c, s = math.cos(tilt), math.sin(tilt)

                def R(dy, dz):
                    return (X(cy + dy * c - dz * s), Zd(zp + dy * s + dz * c))
                poly([R(-8.8, -1.2), R(8.8, -1.2), R(8.8, 0.1), R(-8.8, 0.1)], "#ffffff", INK, 0.1)
                poly([R(-KNOB_D / 2, -0.9), R(KNOB_D / 2, -0.9), R(KNOB_D / 2, KNOB_TOP), R(-KNOB_D / 2, KNOB_TOP)], KNOB, INK, 0.15)
                poly([R(-STEM_D / 2, -2.7), R(STEM_D / 2, -2.7), R(STEM_D / 2, -1.0), R(-STEM_D / 2, -1.0)], "#d9d9d9", INK, 0.1)
                poly([R(-MAG_D / 2, -7.0), R(MAG_D / 2, -7.0), R(MAG_D / 2, -4.5), R(-MAG_D / 2, -4.5)], MAG, INK, 0.1)
                line(R(0, -8), R(0, KNOB_TOP + 2), RED, 0.12, "1 0.6")
            else:
                knob_top = zc + KNOB_TOP
                poly([(X(cy - C.WELL_D / 2), Zd(zf)), (X(cy + C.WELL_D / 2), Zd(zf)), (X(cy + C.WELL_D / 2), Zd(zc + 3)), (X(cy - C.WELL_D / 2), Zd(zc + 3))], "#ffffff", INK, 0.1)
                if mode == "S2":                  # R5SL: skirt D18.4 down into the D19.0 well, up to 0.5 above the well's rear edge, then the D16.4 body
                    sk, zs_top = C.KNOB_SKIRT_D / 2, C.S(cy + C.WELL_D / 2) + rise + 0.5
                    poly([(X(cy - sk), Zd(zf + 0.3)), (X(cy + sk), Zd(zf + 0.3)), (X(cy + sk), Zd(zs_top)), (X(cy + KNOB_D / 2), Zd(zs_top)), (X(cy + KNOB_D / 2), Zd(knob_top)),
                          (X(cy - KNOB_D / 2), Zd(knob_top)), (X(cy - KNOB_D / 2), Zd(zs_top)), (X(cy - sk), Zd(zs_top))], KNOB, INK, 0.15)
                else:
                    poly([(X(cy - KNOB_D / 2), Zd(zf + 0.3)), (X(cy + KNOB_D / 2), Zd(zf + 0.3)), (X(cy + KNOB_D / 2), Zd(knob_top)), (X(cy - KNOB_D / 2), Zd(knob_top))], KNOB, INK, 0.15)
                poly([(X(cy - STEM_D / 2), Zd(HEAD_Z1)), (X(cy + STEM_D / 2), Zd(HEAD_Z1)), (X(cy + STEM_D / 2), Zd(zf)), (X(cy - STEM_D / 2), Zd(zf))], "#d9d9d9", INK, 0.1)
                poly([(X(cy - MAG_D / 2), Zd(MAG_Z0)), (X(cy + MAG_D / 2), Zd(MAG_Z0)), (X(cy + MAG_D / 2), Zd(MAG_Z0 + MAG_L)), (X(cy - MAG_D / 2), Zd(MAG_Z0 + MAG_L))], MAG, INK, 0.1)
                line((X(cy), Zd(MAG_Z0 - 1)), (X(cy), Zd(knob_top + 2)), RED, 0.12, "1 0.6")
            # main board and sensor (horizontal in every variant)
            poly([(X(cy - 14.5), Zd(6.8)), (X(cy + 14.5), Zd(6.8)), (X(cy + 14.5), Zd(8.0)), (X(cy - 14.5), Zd(8.0))], PCB, INK, 0.1, 0.9)
            poly([(X(cy - 1.45), Zd(6.8)), (X(cy + 1.45), Zd(6.8)), (X(cy + 1.45), Zd(5.15)), (X(cy - 1.45), Zd(5.15))], "#555555", INK, 0.1)
            # labels / numbers
            nn = N["registros" if row == 0 else "volume"][mode]
            T("%s - %s" % (name, mode), ox, oz0 - 60 if row == 0 else oz0 - 58, 2.0)
            if mode == "S1":
                T("disco plano D26: %+.1f mm acima do tampo na frente," % nn["acima_do_tampo_frente_mm"], ox, oz0 + 14, 1.5)
                T("%.1f mm abaixo atras; poco 1,2 uniforme" % nn["abaixo_do_tampo_tras_mm"], ox, oz0 + 16.5, 1.5)
            elif mode == "S2":
                T("poco: %.1f mm na borda da frente, %.1f atras (centro 1,2)" % (nn["profundidade_poco_borda_frente_mm"], nn["profundidade_poco_borda_tras_mm"]), ox, oz0 + 14, 1.5)
                T("vao sob o knob atras %.1f; knob acima do tampo: %.1f frente / %.1f tras" % (nn["vao_sob_o_knob_atras_mm"], nn["knob_acima_do_tampo_frente_mm"], nn["knob_acima_do_tampo_tras_mm"]), ox, oz0 + 16.5, 1.5)
            else:
                T("ima inclinado %.1f graus; erro de angulo no sensor ate %.2f graus" % (nn["inclinacao_graus"], nn["erro_de_angulo_pico_graus"]), ox, oz0 + 14, 1.5)
                T("(sensor em v. da placa horizontal; so referencia)", ox, oz0 + 16.5, 1.5)
    T("Ima Ø6 x 2,5 horizontal em S1/S2; sensor TMAG5273 na face de baixo da placa (z 6,8); folga axial 0,8 mm aceita na R4SL (item 2).", 6, 196, 1.5)
    o.append("</svg>")
    path = os.path.join(IMG, "knobs_s123.svg")
    open(path, "w", encoding="utf-8").write("\n".join(o))
    json.dump(N, open(os.path.join(OUT, "knobs_s123.json"), "w", encoding="utf-8"), indent=1)
    edge = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    if os.path.exists(edge):
        import subprocess
        subprocess.run([edge, "--headless", "--screenshot=" + os.path.join(IMG, "knobs_s123.png"), "--window-size=1500,1200", "file:///" + path.replace("\\", "/")], capture_output=True)
    print(json.dumps(N, indent=1))


if __name__ == "__main__":
    build()
