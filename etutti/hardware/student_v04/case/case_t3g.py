"""eTutti Student V4 (R3V4): the F2 case with the T3-G key fixing (grade-regua), parametric in the number of modules.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/case_t3g.py [modules ...]   (default 0 1 2 3)

modules = 0, 1, 2, 3  ->  28, 44, 60, 76 keys. Built on case_f2.py (R2V4): its functions are reused with the constants below patched
(they read module globals). What R3V4 changes:
  * no foam, no preload: the deck only covers the keys with a 1.0 mm gap (the grade-regua carries the key, not the lid);
  * each regua gets a grade-regua (FR-4, t = GRADE_T, 4 openings 14.00, same outline as the regua, notches at the posts);
  * the two locating pins per regua become two M2 screws (pan head, non magnetic) into inserts in the tray (Pm bosses, D 6);
  * deck 2.5 mm (was 3.0) with 5 / 8 / 11 / 14 interior posts (was 10 / 16 / 22 / 28), stem 0.1 mm shorter (head top ZR + 22.8);
  * the key stand-ins use the measured envelope (estudos/ks20_step.py: PDF of the Orange + STEP KS-20T).
Pieces (out/): t3g_<n>_{tampa,base,reguas,grades,teclas}.stl + t3g_<n>.json. Frame as in case_f2 (z = 0 at the top of row 1's regua).
"""
import json
import os
import sys
import time

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case_f2 as F    # noqa: E402

OUT = F.OUT
GRADE_T = 1.6                     # see FIT_CHECK R3V4 section 2.1: 1.2 leaves 0.16 mm of vertical play, 1.6 is inside the latch window
GAP = 1.0                         # nominal gap between the housing top (11.10) and the deck underside
SCREW_D, SCREW_HEAD, SCREW_BOSS, SCREW_PILOT = 2.2, 3.8, 6.0, 3.2
GRADE_OPEN = 14.0                 # +0.03/-0.02 on the drawing
POSTS = {0: 5, 1: 8, 2: 11, 3: 14}
CAP_TOP = 22.8

# ---- patch the F2 constants (derived ones too: they were computed at import time)
F.FOAM = GAP
F.DECK_T = 2.5
F.DECK_UNDER = F.HOUSING_H + GAP
F.DECK_TOP = F.DECK_UNDER + F.DECK_T
F.IF_ROOF_TOP = F.DECK_TOP
F.PIN_HOLE = SCREW_D
F.PIN_D = SCREW_BOSS
F.PIN_H = 0.05                    # the "pin" becomes a boss that stops at the regua's underside
F.CAP_TOP = CAP_TOP


def pick_posts(mod):
    tri = [t for t in F.triangles(mod) if t[0] > F.X_IF + 8]
    import numpy as np
    idx = np.linspace(0, len(tri) - 1, POSTS[mod]).astype(int)
    return [tri[i] for i in sorted(set(idx))]


F.pick_posts = pick_posts
box, cyl, vol, inter = F.box, F.cyl, F.vol, F.inter


def base(mod):
    b = F.base(mod)
    for r, x0, y in F.rulers(mod):
        z1 = F.ZR[r - 1] - F.RULER_T
        for xx in (x0 + F.PITCH, x0 + 3 * F.PITCH):
            b = b.cut(cyl(xx, y + 5.2, z1, z1 + 0.5, SCREW_BOSS + 0.2)).cut(cyl(xx, y + 5.2, z1 - 6.0, z1 + 0.1, SCREW_PILOT))
    return b


def grades(mod):
    """Grade-regua: same outline as the regua, 4 openings 14.00 at the key centres, notches where a post blade passes."""
    res = None
    posts = pick_posts(mod)
    for r, x0, y in F.rulers(mod):
        z1 = F.ZR[r - 1] + 5.0                       # top of the grade = the housing's 5.00 shoulder
        g = box(x0 + 0.2, x0 + F.RULER_L - 0.2, y - F.RULER_W / 2, y + F.RULER_W / 2, z1 - GRADE_T, z1)
        for i in range(4):
            xc = x0 + F.PITCH / 2 + i * F.PITCH
            g = g.cut(box(xc - GRADE_OPEN / 2, xc + GRADE_OPEN / 2, y - GRADE_OPEN / 2, y + GRADE_OPEN / 2, z1 - 2, z1 + 1))
        for px, py in posts:
            if abs(py - (y - F.ROWP / 3.0)) < 0.05 and x0 - 3 < px < x0 + F.RULER_L + 3:
                g = g.cut(box(px - 1.0, px + 1.0, y - 7.1, y - 2.7, z1 - 2, z1 + 1))
        res = g if res is None else res.union(g)
    return res


def screws(mod):
    """M2 pan heads standing on the regua (only for the interference check): D 3.8 x 1.6."""
    res = None
    for r, x0, y in F.rulers(mod):
        z0 = F.ZR[r - 1]
        for xx in (x0 + F.PITCH, x0 + 3 * F.PITCH):
            s = cyl(xx, y + 5.2, z0 - F.RULER_T - 4, z0 + 1.6, 2.0).union(cyl(xx, y + 5.2, z0, z0 + 1.6, SCREW_HEAD))
            res = s if res is None else res.union(s)
    return res


def key_bodies(mod, dz=0.0, with_cap=True):
    """Envelope from estudos/ks20_step.py. rel z above the seat: body 14.0 to 5.0 (the 14.44 of the barbs is in the grade's hole),
    cover 15.4 x 15.1 from 5.35 (tabs 16.1) to 8.6, tapered to 13.5 x 12.3 at 10.6, collar 11.3 x 10.4 to 11.10, stem (cross) to 13.8."""
    res = None
    for r, x, y in F.key_list(mod):
        z0 = F.ZR[r - 1] + dz
        k = box(x - 7.0, x + 7.0, y - 7.0, y + 7.0, z0, z0 + 5.0)
        k = k.union(box(x - 7.7, x + 7.7, y - 7.55, y + 7.55, z0 + 5.0, z0 + 8.6))
        top = (cq.Workplane("XY").workplane(offset=z0 + 8.6).center(x, y).rect(15.4, 15.1)
               .workplane(offset=2.0).rect(13.5, 12.3).loft(ruled=True))
        k = k.union(top).union(box(x - 5.65, x + 5.65, y - 5.2, y + 5.2, z0 + 10.6, z0 + 11.10))
        k = k.union(box(x - 2.0, x + 2.0, y - 0.65, y + 0.65, z0 + 11.10, z0 + 13.8))
        if with_cap:
            zt = z0 + CAP_TOP - F.CAP_TRAVEL
            cap = cyl(x, y, zt - 3.5, zt - 2.3, 16.5).union(cyl(x, y, zt - 2.3, zt, 15.0)).union(cyl(x, y, z0 + 13.8 - F.CAP_TRAVEL - 1.0, zt - 3.5, 5.6))
            k = k.union(cap)
        res = k if res is None else res.union(k)
    return res


def build(mod):
    t0 = time.time()
    n = 28 + 16 * mod
    L = F.length(mod)
    lid_, base_, ru, gr, sc = F.lid(mod), base(mod), F.rulers_solid(mod), grades(mod), screws(mod)
    info = {"teclas": n, "modulos": mod, "comprimento_mm": L, "largura_mm": F.CASE_W,
            "grade_mm": GRADE_T, "folga_deck_mm": GAP, "deck_mm": F.DECK_T, "haste_cabeca_topo": CAP_TOP,
            "z_topo_tampa": F.ZR[3] + F.DECK_TOP, "altura_atras_mm": round(F.ZR[3] + F.DECK_TOP - F.Z_BOT, 2),
            "altura_frente_mm": round(F.ZR[0] + F.DECK_TOP - F.Z_BOT, 2),
            "reguas": len(F.rulers(mod)), "grades": len(F.rulers(mod)), "postes_internos": len(pick_posts(mod)),
            "bossas_de_parede": len(F.wall_posts(mod)),
            "volume_cm3": {"tampa": round(vol(lid_) / 1000, 1), "base": round(vol(base_) / 1000, 1)}}
    keys0, keys5, keys8 = key_bodies(mod, 0.0), key_bodies(mod, 0.5, False), key_bodies(mod, 0.8, False)
    info["interferencias_mm3"] = {
        "tampa x teclas (nominal)": round(inter(lid_, keys0), 2),
        "tampa x carcacas (+0,5 mm, sem botao)": round(inter(lid_, keys5), 2),
        "tampa x carcacas (+0,8 mm, sem botao)": round(inter(lid_, keys8), 2),
        "tampa x grades": round(inter(lid_, gr), 2), "tampa x reguas": round(inter(lid_, ru), 2),
        "tampa x parafusos": round(inter(lid_, sc), 2), "tampa x base": round(inter(lid_, base_), 2),
        "base x teclas": round(inter(base_, keys0), 2), "base x reguas": round(inter(base_, ru), 2),
        "base x grades": round(inter(base_, gr), 2), "base x parafusos (cabeca)": round(inter(base_, sc), 2),
        "grades x teclas": round(inter(gr, keys0), 2), "grades x reguas": round(inter(gr, ru), 2),
        "grades x parafusos": round(inter(gr, sc), 2), "teclas x parafusos": round(inter(keys0, sc), 2)}
    for name, w in (("tampa", lid_), ("base", base_), ("reguas", ru), ("grades", gr), ("teclas", keys0), ("parafusos", sc)):
        cq.exporters.export(F.mirror(w), os.path.join(OUT, "t3g_%d_%s.stl" % (n, name)), tolerance=0.05, angularTolerance=0.2)
        if name in ("tampa", "base") and mod in (0, 3):
            cq.exporters.export(F.mirror(w), os.path.join(OUT, "t3g_%d_%s.step" % (n, name)))
    info["segundos"] = round(time.time() - t0, 1)
    json.dump(info, open(os.path.join(OUT, "t3g_%d.json" % n), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(info, indent=1, ensure_ascii=False), flush=True)
    return info


if __name__ == "__main__":
    for m in [int(a) for a in sys.argv[1:]] or [0, 1, 2, 3]:
        build(m)
