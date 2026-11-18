"""eTutti Student V3: fit check of the case against the board, the switches and the bought parts (SPEC v4).

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/pcb/export_fp.py
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/pcb/export_furos.py
    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v03/case/case.py
    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v03/case/fit_check.py

Every pair below is tested with exact solids (OpenCascade): the volume two pieces share (an
interference when over 0.5 mm3) and, for the gaps the SPEC names, the smallest distance.
The parts on the board are boxes over their courtyards, as tall as their height field; the
switches, encoders, sockets, speaker, screen module, battery and MicroMod card have their own shapes.

Writes out/fit_check.json. Exits non-zero when two pieces interfere.
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

FP = json.load(open(os.path.join(HERE, "..", "pcb", "footprints.json"), encoding="utf-8"))["footprints"]
INFO = json.load(open(os.path.join(K.OUT, "case.json"), encoding="utf-8"))
DEFAULT_H = {"J401": 2.95, "J201": 3.26, "J301": 5.0, "J302": 5.0, "J202": 5.5, "SW403": 2.0, "J501": 1.5}
LIMIT = 0.5      # mm3
FRONT = {}        # x of each socket's front face


def step(name):
    return cq.importers.importStep(os.path.join(K.OUT, name + ".step"))


def vol(a, b):
    try:
        r = a.intersect(b)
        return sum(s.Volume() for s in r.solids().vals())
    except Exception:
        return -1.0


def dist(a, b):
    return a.val().distance(b.val())


def at(w, x, y, dz=0.0):
    return w.translate((x, -y, dz))


def board():
    x0, y0, x1, y1 = G.BOARD
    w = K.box(x0, y0, x1, y1, -K.T_PCB, 0, G.BOARD_R)
    for f in FP:
        if f["lib"].startswith("MountingHole"):
            w = w.cut(K.cyl(f["x"], f["y"], -2, 1, 2.7 if f["ref"] == "H101" else 2.2))
    return w


def components():
    """{name: solid} of what stands on the board."""
    out = {}
    top, bottom = [], []
    for f in FP:
        ref = f["ref"]
        if f["lib"].startswith(("MountingHole", "Gateron", "TestPoint")) or ref in ("SW401", "SW402", "J101", "H101") or f.get("dnp"):
            continue
        h = f["height"] or DEFAULT_H.get(ref) or (1.0 if f["bottom"] else 1.0)
        x0, y0, x1, y1 = f["box"]
        if ref in ("J301", "J302"):          # PJ-327A (bottom side): body 12.2 x 6 x 5.1 from the footprint's origin, collar 2 mm in front
            yc = f["y"]
            s = K.box(f["x"], yc - 3.0, f["x"] + 12.2, yc + 3.0, -K.T_PCB - h, -K.T_PCB).union(
                cq.Workplane("YZ").workplane(offset=f["x"] - 2.0).center(-yc, G.JACK_Z).circle(2.5).extrude(2.01))
            out[ref] = s
            FRONT[ref] = f["x"] - 2.0
            continue
        if ref == "J201":                    # HRO TYPE-C-31-M-12: shell 8.94 x 3.16, 7.3 long, centred on the origin
            yc = f["y"]
            out[ref] = (cq.Workplane("YZ").workplane(offset=f["x"] - 3.65).center(-yc, -K.T_PCB - 0.1 - 1.58).rect(8.94, 3.16)
                        .extrude(7.3).edges("|X").fillet(1.2))
            FRONT[ref] = f["x"] - 3.65
            continue
        s = K.box(x0 + 0.25, y0 + 0.25, x1 - 0.25, y1 - 0.25, -K.T_PCB - h, -K.T_PCB) if f["bottom"] else \
            K.box(x0 + 0.25, y0 + 0.25, x1 - 0.25, y1 - 0.25, 0, h)
        (bottom if f["bottom"] else top).append(s)
    out["pecas de cima (SMD)"] = K.union(top)
    out["pecas do verso (SMD)"] = K.union(bottom)
    # encoders (see below), legs 3.5 mm below
    enc = []
    for f in FP:
        if f["ref"] in ("SW401", "SW402"):
            cx, cy = G.KNOBS[int(f["ref"][-1]) - 1]
            # EasyEDA's model of the EC11E18244AU (C202365, case/modelos): body 11.7 x 12.4 to z 4.5, collar 8.0, bushing 7.0 to 11.5,
            # shaft 6.0 from 12.5 to 24.5. The shaft is taken cut to 20.0 (SPEC v4 item 12 / C10): the knob ends at z 21.5.
            enc.append(K.box(cx - 5.85, cy - 6.2, cx + 5.85, cy + 6.2, 0, 4.5).union(K.cyl(cx, cy, 4.5, 11.5, 7.0))
                       .union(K.cyl(cx, cy, 11.5, 20.0, 6.0)))
            for px, py, _n, _th in f["pads"]:
                enc.append(K.cyl(px, py, -K.T_PCB - 2.3, -K.T_PCB, 1.6))
    out["encoders"] = K.union(enc)
    # MicroMod socket and card under the board (4.7 mm below it), with its standoff
    j = next(f for f in FP if f["ref"] == "J101")
    x0, y0, x1, y1 = j["box"]
    out["modulo MicroMod"] = K.box(x0, y0, x1, y1, -K.T_PCB - 4.7, -K.T_PCB)
    hx, hy = K.H101
    out["parafuso do H101"] = K.cyl(hx, hy, 0, 1.5, 4.6).union(K.cyl(hx, hy, -8.0, 0, 2.5))      # M2.5 x 8 nylon, head on the board's top
    out["porca do H101"] = K.cyl(hx, hy, -6.7, -4.7, 5.5).cut(K.cyl(hx, hy, -7, -4, 2.5))         # M2.5 nylon nut, 2 thick
    # switches: housing 14 x 14 to 11.2, stem to 14.8
    sw = [K.box(x - 7, y - 7, x + 7, y + 7, 0, K.HOUSING_TOP) for _r, x, y in G.KEYS]
    out["teclas (alojamentos)"] = K.union(sw)
    # speaker, its mesh and foam are soft; the screen module; the battery
    lv = K.box_levels()
    out["alto-falante"] = K.cyl(K.SPK[0], K.SPK[1], lv["back"], lv["front"], K.SPK_D)
    ol = K.oled_levels()
    cx, cy = K.oled_centre()
    w, h, _t = K.OLED_PCB
    out["modulo da tela"] = K.box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, ol["pcb_bottom"], ol["pcb_top"]).union(
        K.box(cx - 13.35, cy - 10.1, cx + 13.35, cy + 9.2, ol["pcb_top"], ol["glass_top"]))
    for px, py in K.oled_posts():
        out["modulo da tela"] = out["modulo da tela"].cut(K.cyl(px, py, ol["pcb_bottom"] - 1, ol["pcb_top"] + 0.01, 2.2))
    bx0, by0, bx1, by1, bt = K.BATTERY
    zf = K.Z0 + K.FLOOR
    out["bateria"] = K.box(bx0, by0, bx1, by1, zf, zf + bt, 1.0)
    return out


def main():
    P = {n: step(n) for n in ("tampa", "base", "grade", "espacador", "knob", "caixa_acustica", "janela")}
    P["placa"] = board()
    C = components()
    spacers = K.union([at(P["espacador"], x, y) for x, y in K.GRID_SCREWS])
    knobs = K.union([at(P["knob"], x, y) for x, y in G.KNOBS])
    keys = INFO["teclas"]
    btn = {}
    for k in keys:
        name = "botao_%s_f%d" % (k["tipo"], k["fileira"])
        if name not in btn:
            btn[name] = step(name)
    rest = K.union([at(btn["botao_%s_f%d" % (k["tipo"], k["fileira"])], k["x"], k["y"]) for k in keys])
    down = K.union([at(btn["botao_%s_f%d" % (k["tipo"], k["fileira"])], k["x"], k["y"], -K.TRAVEL) for k in keys])
    S = dict(P, **C)
    S.update({"espacadores": spacers, "knobs": knobs, "botoes (soltos)": rest, "botoes (apertados)": down})
    del S["espacador"], S["knob"]

    # the switch's own stem channel takes the button's stem: test the buttons against the grid and the lid only
    pairs = []
    names = list(S)
    skip = {frozenset(p) for p in (
        ("botoes (soltos)", "botoes (apertados)"), ("botoes (soltos)", "teclas (alojamentos)"),
        ("botoes (apertados)", "teclas (alojamentos)"), ("knobs", "encoders"),
        ("pecas de cima (SMD)", "placa"), ("pecas do verso (SMD)", "placa"), ("encoders", "placa"),
        ("alto-falante", "caixa_acustica"))}
    res = {"interferencias": [], "pares_testados": 0}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if frozenset((a, b)) in skip:
                continue
            v = vol(S[a], S[b])
            res["pares_testados"] += 1
            if v > LIMIT or v < 0:
                res["interferencias"].append({"a": a, "b": b, "volume_mm3": round(v, 2)})
                print("INTERFERE", a, "x", b, round(v, 2), flush=True)
    # the speaker must enter its seat: only its rim may touch the box's ledge
    res["falante_na_caixa_mm3"] = round(vol(S["alto-falante"], S["caixa_acustica"]), 2)

    # gaps
    g = {}
    one = {r: next(k for k in keys if k["fileira"] == r) for r in (1, 2, 3, 4)}
    for r, k in one.items():
        b0 = at(btn["botao_%s_f%d" % (k["tipo"], r)], k["x"], k["y"])
        b1 = at(btn["botao_%s_f%d" % (k["tipo"], r)], k["x"], k["y"], -K.TRAVEL)
        head_under = INFO["pecas"]["botao_%s_f%d" % (k["tipo"], r)]["cabeca_por_baixo"]
        g["fileira %d" % r] = {
            "topo_acima_do_tampo": round(K.ROW_TOP[r] - K.ZT, 2),
            "cabeca_ate_a_grade_solto": round(head_under - K.GRID_Z1, 2),
            "cabeca_ate_a_grade_apertado": round(head_under - K.TRAVEL - K.GRID_Z1, 2),
            "haste_no_furo_da_grade": round(dist(b0, S["grade"]), 3),
            "botao_ate_a_tampa": round(dist(b0, S["tampa"]), 3),
            "botao_apertado_ate_a_tampa": round(dist(b1, S["tampa"]), 3),
        }
    edge_keys = [k for k in keys if (k["x"], k["y"]) in G.HULL]
    g["botao_ate_a_parede_do_poco_min"] = round(min(
        dist(at(btn["botao_%s_f%d" % (k["tipo"], k["fileira"])], k["x"], k["y"]), S["tampa"]) for k in edge_keys), 3)
    g["aba_do_poco_ate_a_grade"] = round(dist(S["tampa"], S["grade"]), 3)
    g["grade_ate_as_teclas"] = round(K.GRID_Z0 - K.HOUSING_TOP, 3)
    g["grade_ate_a_parede_da_tampa"] = round(min(dist(S["grade"], K.outer(K.Z0, K.ZT).cut(K.outer(K.Z0 - 1, K.ZT + 1, K.WALL))), 99), 3)
    g["placa_ate_a_parede"] = round(dist(S["placa"], K.outer(K.Z0, K.ZT).cut(K.outer(K.Z0 - 1, K.ZT + 1, K.WALL))), 3)
    g["placa_ate_a_tampa"] = round(dist(S["placa"], S["tampa"]), 3)
    g["knob_ate_a_tampa"] = round(dist(S["knobs"], S["tampa"]), 3)
    g["knob_acima_do_tampo"] = round(K.KNOB["top"] - K.ZT, 2)
    g["eixo_do_encoder_acima_do_tampo"] = round(K.KNOB["shaft_top"] - K.ZT, 2)
    g["caixa_acustica_ate_a_placa"] = round(dist(S["caixa_acustica"], S["placa"]), 3)
    g["caixa_acustica_ate_pecas_de_cima"] = round(dist(S["caixa_acustica"], S["pecas de cima (SMD)"]), 3)
    g["caixa_acustica_ate_encoders"] = round(dist(S["caixa_acustica"], S["encoders"]), 3)
    g["caixa_acustica_ate_a_grade"] = round(dist(S["caixa_acustica"], S["grade"]), 3)
    g["modulo_da_tela_ate_pecas_de_cima"] = round(dist(S["modulo da tela"], S["pecas de cima (SMD)"]), 3)
    g["modulo_da_tela_ate_encoders"] = round(dist(S["modulo da tela"], S["encoders"]), 3)
    g["bateria_ate_pecas_do_verso"] = round(dist(S["bateria"], S["pecas do verso (SMD)"]), 3)
    g["bateria_ate_encoders (pernas)"] = round(dist(S["bateria"], S["encoders"]), 3)
    g["bateria_ate_o_modulo"] = round(dist(S["bateria"], S["modulo MicroMod"]), 3)
    g["modulo_ate_o_piso"] = round(dist(S["modulo MicroMod"], S["base"]), 3)
    g["pecas_do_verso_ate_a_base"] = round(dist(S["pecas do verso (SMD)"], S["base"]), 3)
    g["encoders (pernas)_ate_a_base"] = round(dist(S["encoders"], S["base"]), 3)
    g["espacadores_ate_as_teclas"] = round(dist(S["espacadores"], S["teclas (alojamentos)"]), 3)
    g["espacadores_ate_pecas_de_cima"] = round(dist(S["espacadores"], S["pecas de cima (SMD)"]), 3)
    g["postes_da_tampa_ate_a_grade"] = round(dist(S["tampa"], S["grade"]), 3)
    g["tampa_ate_pecas_de_cima"] = round(dist(S["tampa"], S["pecas de cima (SMD)"]), 3)
    g["tampa_ate_encoders"] = round(dist(S["tampa"], S["encoders"]), 3)
    for ref in ("J201", "J301", "J302"):
        g["%s_ate_a_tampa" % ref] = round(dist(S[ref], S["tampa"]), 3)
        g["%s_ate_a_base" % ref] = round(dist(S[ref], S["base"]), 3)
        g["%s_frente_atras_da_parede" % ref] = round(FRONT[ref] - K.WALL, 3)
    # SPEC v2: the board, with all that stands on it, goes into the lid from below (lid upside down).
    # Moved down step by step, nothing of it may cross the lid.
    going_in = K.union([S[n] for n in ("placa", "J201", "J301", "J302", "pecas de cima (SMD)", "pecas do verso (SMD)", "encoders",
                                       "teclas (alojamentos)", "espacadores", "modulo MicroMod", "parafuso do H101", "porca do H101")])
    res["placa_entra_por_baixo_mm3"] = {str(dz): round(vol(S["tampa"], going_in.translate((0, 0, -dz))), 2)
                                        for dz in (0.5, 1, 2, 3, 4, 6, 8, 12, 16, 22, 30)}
    if any(v > LIMIT or v < 0 for v in res["placa_entra_por_baixo_mm3"].values()):
        res["interferencias"].append({"a": "tampa", "b": "placa ao entrar por baixo", "volume_mm3": res["placa_entra_por_baixo_mm3"]})
    # the tray goes into the lid from below, and comes out the same way (SPEC v4: 0.15 mm a side)
    res["bandeja_entra_por_baixo_mm3"] = {str(dz): round(vol(S["tampa"], S["base"].translate((0, 0, -dz))), 2)
                                          for dz in (2, 5, 10, 20)}
    if any(v > LIMIT or v < 0 for v in res["bandeja_entra_por_baixo_mm3"].values()):
        res["interferencias"].append({"a": "tampa", "b": "bandeja ao entrar por baixo", "volume_mm3": res["bandeja_entra_por_baixo_mm3"]})
    # how far a plug goes in. The socket's own front face is the plug's stop: a plug whose body passes
    # the hole seats fully; a thicker one stops on the wall's outside, short by the wall + the recess.
    uw, uh, _ur = G.USB_OPENING
    res["plugues"] = {
        "USB-C": {"furo_mm": [uw, uh], "corpo_maximo_pela_norma_mm": [12.35, 6.5], "folga_por_lado_mm": [round((uw - 12.35) / 2, 3), round((uh - 6.5) / 2, 3)],
                  "ponta_do_plugue_mm": 6.65, "falta_entrar_se_o_corpo_nao_passa_mm": round(FRONT["J201"], 2),
                  "encaixe_se_o_corpo_nao_passa_mm": round(6.65 - FRONT["J201"], 2)},
        "P2 3,5 mm": {"furo_mm": G.JACK_OPENING_D, "ponta_do_plugue_mm": 14.0, "falta_entrar_se_o_corpo_nao_passa_mm": round(FRONT["J301"], 2),
                      "encaixe_se_o_corpo_nao_passa_mm": round(14.0 - FRONT["J301"], 2)}}
    g["caixa_acustica_ate_J302"] = round(dist(S["caixa_acustica"], S["J302"]), 3)
    g["caixa_acustica_ate_a_tampa"] = round(dist(S["caixa_acustica"], S["tampa"]), 3)
    g["caixa_acustica_ate_espacadores"] = round(dist(S["caixa_acustica"], S["espacadores"]), 3)
    g["parafuso_da_grade_M2x16_passa_da_porca_mm"] = round(16.0 - (K.GRID_T + K.GRID_Z0 + K.T_PCB + 1.6), 2)
    res["folgas_mm"] = g
    json.dump(res, open(os.path.join(K.OUT, "fit_check.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(g, indent=1, ensure_ascii=False))
    print("pares testados:", res["pares_testados"], "interferencias:", len(res["interferencias"]))
    sys.exit(1 if res["interferencias"] else 0)


if __name__ == "__main__":
    main()
