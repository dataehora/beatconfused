"""eTutti Slim (R4SL, stage 2b): 3D scene of the MAIN board with the case, the four rulers, the battery and the two knobs, with sections. CadQuery + PyVista.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/case.py             (first: the case)
    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/cena_principal.py

Realistic models where they exist: RT1062 (SamacSys STEP), USB-C, P2 jack, FFC, TMAG5273 x2, DRV5032, SGTL5000, BQ24075, TPS63001, FNR3015, crystal (EasyEDA STEP by LCSC code,
modelos/baixados/), the 0402/0603/0805 passives (KiCad 3D library), the VARTA 523450 battery (manufacturer STEP, fornecimento/bateria/), the KS-33D (Gateron STEP).  Parts without a STEP
(W25Q64 flash, MKL02, JST SH, small SOT-23 / SOD / QFN) are BOXES from their courtyard and height: listed in the report.  The knobs are simple solids from the Design's numbers.
Placed from pcb/principal/posicao_principal.json: each part's footprint pads are fitted to its placed pads (rotation / mirror exactly KiCad's).
Writes case/renders/{cena_principal_baixo,cena_principal_iso,corte_principal_registros,corte_principal_volume,corte_principal_longitudinal}.png and case/out/cena_principal.json.
"""
import glob
import json
import math
import os
import re
import sys

import cadquery as cq
import numpy as np
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import case as C  # noqa: E402
import cena_regua as CR  # noqa: E402
import layout_slim as L  # noqa: E402

OUT, REN, TMP = CR.OUT, CR.REN, CR.TMP
POS = json.load(open(os.path.join(HW, "pcb", "principal", "posicao_principal.json"), encoding="utf-8"))
ENVP = json.load(open(os.path.join(HERE, "envelope_principal.json"), encoding="utf-8"))
BX = os.path.join(HW, "modelos", "baixados")
KISH = CR.KISH
BOARD_BOT, BOARD_T = C.BOARD_BOT, C.BOARD_T
sys.path.insert(0, os.path.join(HW, "pcb"))
import sexpr as S  # noqa: E402

LCSC = {}
_t = S.parse(open(os.path.join(HW, "pcb", "build", "slim_netlist.net"), encoding="utf-8").read())
for _c in S.find(S.first(_t, "components"), "comp"):
    _f = {S.first(f, "name")[1]: (f[-1] if isinstance(f[-1], str) else "") for f in S.find(S.first(_c, "fields"), "field")}
    LCSC[S.first(_c, "ref")[1]] = _f.get("LCSC", "")
STEP_BY_LCSC = {"C3216699": os.path.join(HW, "modelos", "rt1062", "MIMXRT1062DVJ6B.stp"), "C165948": glob.glob(BX + "/usbc_TYPE-C-31-M-12_C165948.step")[0],
                "C49284723": glob.glob(BX + "/jack_PJ-327A_XUNPU_C49284723.step")[0], "C3250113": glob.glob(BX + "/ffc_8p_05_h1_C3250113.step")[0],
                "C3020565": glob.glob(BX + "/tmag5273A2_C3020565.step")[0], "C41935525": glob.glob(BX + "/tmag5273B2_C41935525.step")[0],
                "C266118": glob.glob(BX + "/drv5032ZE_C266118.step")[0], "C2651833": glob.glob(BX + "/sgtl5000_C2651833.step")[0], "C15464": glob.glob(BX + "/bq24075_C15464.step")[0],
                "C28060": glob.glob(BX + "/tps63001_C28060.step")[0], "C167747": glob.glob(BX + "/ind_FNR3015_C167747.step")[0], "C524739": glob.glob(BX + "/xtal_24M_3225_C524739.step")[0],
                "C273605": glob.glob(BX + "/led_1615_C273605.step")[0], "C318884": glob.glob(BX + "/botao_TS-1187A_C318884.step")[0]}
KICAD_PASSIVE = {"C_0402": "Capacitor_SMD.3dshapes/C_0402_1005Metric.step", "C_0603": "Capacitor_SMD.3dshapes/C_0603_1608Metric.step", "C_0805": "Capacitor_SMD.3dshapes/C_0805_2012Metric.step",
                 "R_0402": "Resistor_SMD.3dshapes/R_0402_1005Metric.step", "R_0603": "Resistor_SMD.3dshapes/R_0603_1608Metric.step"}
CENTER = {"FFC_8P_0.5_KH-H1.0": (0.0, 0.45)}
BOXES = []                                       # parts drawn as boxes (reported)


def fp_file(fpname):
    cands = [os.path.join(HW, "pcb", "kicad", "slim.pretty", fpname + ".kicad_mod")] + glob.glob(KISH + "/footprints/*.pretty/" + fpname + ".kicad_mod")
    for f in cands:
        if os.path.exists(f):
            return f


def step_mesh(path, key):
    return CR.step_mesh(path, key)


def affine_for(ref):
    q = POS["pecas"][ref]
    txt = open(fp_file(q["fp"]), encoding="utf-8").read()
    allp = [(m.group(1), float(m.group(4)), float(m.group(5))) for m in re.finditer(r'\(pad "?([\w]*)"? (\w+) (\w+)\s+\(at ([-\d.]+) ([-\d.]+)', txt)]
    cnt = {}
    for n, _, _ in allp:
        cnt[n] = cnt.get(n, 0) + 1
    lib = {n: (x, y) for n, x, y in allp if cnt[n] == 1 and n not in ("", "MP")}
    dcnt = {}
    for p in POS["pads"]:
        if p["ref"] == ref:
            dcnt[p["n"]] = dcnt.get(p["n"], 0) + 1
    src, dst = [], []
    for p in POS["pads"]:
        if p["ref"] == ref and p["n"] in lib and dcnt[p["n"]] == 1:
            src.append(lib[p["n"]])
            dst.append((p["x"], p["y"]))
    if len(src) >= 3 and np.linalg.matrix_rank(np.array(src) - np.mean(src, axis=0)) >= 2:
        return CR.fit_affine(src, dst)
    if len(src) >= 2:
        s0, s1, d0, d1 = np.array(src[0]), np.array(src[1]), np.array(dst[0]), np.array(dst[1])
        a = np.arctan2(*(d1 - d0)[::-1]) - np.arctan2(*(s1 - s0)[::-1])
        R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        t = (d0 + d1) / 2 - R @ ((s0 + s1) / 2)
        return np.hstack([R, t.reshape(2, 1)])
    return None


def place(mesh, A, center_fp=(0, 0), yflip=False):
    m = mesh.copy()
    pts = np.array(m.points)
    xy = pts[:, :2] - np.array(center_fp)
    if yflip:
        xy[:, 1] = -xy[:, 1]
    uv = (A[:, :2] @ xy.T).T + A[:, 2]
    z = BOARD_BOT - pts[:, 2]
    m.points = np.column_stack([uv[:, 0], uv[:, 1], z])
    m.flip_faces(inplace=True)
    return m


def box_mesh(q):
    x0, y0, x1, y1 = q["patio"]
    h = float(q["altura_mm"] or 0.8)
    b = cq.Workplane("XY").box(x1 - x0 - 0.2, y1 - y0 - 0.2, h, centered=False).translate((x0 + 0.1, y0 + 0.1, BOARD_BOT - h))
    return CR.stl_mesh(b, "box_%s" % q["fp"][:12].replace(":", "_"))


def board_mesh():
    poly = [tuple(p) for p in POS["placa"]["contorno"]]
    wp = cq.Workplane("XY").workplane(offset=BOARD_BOT).polyline(poly).close().extrude(BOARD_T)
    for (x, y) in ENVP["pilares"]["pontos"]:
        wp = wp.cut(cq.Workplane("XY").workplane(offset=BOARD_BOT - 1).center(x, y).circle(1.1).extrude(4))
    return CR.stl_mesh(wp, "placa_principal")


def knobs():
    """Knob solids from the Design's numbers (S2): knob, stem, head, magnets, LED ring."""
    out = []
    for name, (cx, cy), rise, vol in (("registros", C.REG, 1.0, False), ("volume", C.VOL, C.S2_RISE_VOL, True)):
        zc = C.S(cy) + rise
        zf = C.S(cy - C.WELL_D / 2) + rise - 0.1
        top = zc + 4.8
        knob = cq.Workplane("XY").workplane(offset=zf + 0.3).center(cx, cy).circle(8.2).extrude(top - zf - 0.3)
        stem = cq.Workplane("XY").workplane(offset=11.0).center(cx, cy).circle(2.5).extrude(zf + 0.3 - 11.0)
        head = cq.Workplane("XY").workplane(offset=9.0).center(cx, cy).circle(9.5 if vol else 5.0).extrude(2.0)
        mag = cq.Workplane("XY").workplane(offset=8.5).center(cx, cy).circle(3.0).extrude(2.5)
        for i, (w, col) in enumerate(((knob, "#fbf9f3"), (stem, "#d9d9d9"), (head, "#d9d9d9"), (mag, "#c0392b"))):
            out.append((CR.stl_mesh(w, "knob_%s_%d" % (name, i)), col, 1.0, "knob_" + name))
        if vol:
            off = cq.Workplane("XY").workplane(offset=8.5).center(cx - 7.2 * 0.7071, cy - 7.2 * 0.7071).circle(2.0).extrude(2.0)
            out.append((CR.stl_mesh(off, "knob_off"), "#c0392b", 1.0, "knob_volume"))
    return out


def battery():
    m = CR.step_mesh(os.path.join(HW, "fornecimento", "bateria", "VARTA_56457201012_LPP523450S_PCM_W.stp"), "bateria_full")
    m = m.clip_box(bounds=(-20, 20, -32.0, 30, -1, 8), invert=False)        # cell + PCM + a stub of wire (the STEP's wires run 53 mm further to -y)
    pts = np.array(m.points)
    # STEP: wires at -y, body y -26.75..25.25, thickness z -0.06..5.3.  Rotate 180 deg about z (wires exit towards +y), body at y -13.75 .. 38.25, x centred in the bay, bottom at z 1.6
    bx = (C.BAY[0] + C.BAY[2]) / 2
    x = bx - pts[:, 0]
    y = (-13.75 + 25.25) - pts[:, 1] + 13.75 - 13.75 + 0.0
    y = 38.25 - (pts[:, 1] + 26.75) + 0.0 - 0.0
    z = 1.6 + (pts[:, 2] + 0.06)
    m.points = np.column_stack([x, y, z])
    return m


def build():
    meshes = CR.build_scene()                    # case + rulers + grades + switches (R3SL scene)
    meshes = [t for t in meshes if t[3] != "tampo"] + [t for t in meshes if t[3] == "tampo"]
    meshes.append((board_mesh(), "#1f6b4a", 1.0, "placa"))
    cache = {}
    report = {"modelos_reais": [], "caixas": []}
    for ref, q in POS["pecas"].items():
        if ref.startswith("H") and not q["codigo"]:
            continue
        lc = LCSC.get(ref, "")
        fpn = q["fp"]
        A = affine_for(ref)
        mesh = None
        yflip = False
        if lc in STEP_BY_LCSC and A is not None:
            if lc not in cache:
                cache[lc] = step_mesh(STEP_BY_LCSC[lc], "m_" + lc)
            mesh = place(cache[lc], A, CENTER.get(fpn, (0, 0)))
            col = {"C3216699": "#222222", "C165948": "#c9c9c9", "C49284723": "#2b2b2b", "C3250113": "#e8d9a8", "C273605": "#dddddd"}.get(lc, "#262626")
            report["modelos_reais"].append(ref)
        else:
            key = next((k for k in KICAD_PASSIVE if fpn.startswith(k)), None)
            if key and A is not None:
                if key not in cache:
                    cache[key] = step_mesh(KISH + "/3dmodels/" + KICAD_PASSIVE[key], "k_" + key)
                mesh = place(cache[key], A, (0, 0), yflip=True)
                col = "#9b7b4a" if key.startswith("C") else "#333333"
                report["modelos_reais"].append(ref)
            else:
                mesh = box_mesh(q)
                col = "#555555"
                report["caixas"].append("%s (%s)" % (ref, fpn))
        meshes.append((mesh, col, 1.0, ref))
    meshes.append((battery(), "#c7b9a5", 1.0, "bateria"))
    meshes += knobs()
    json.dump({"modelos_reais": len(report["modelos_reais"]), "caixas": report["caixas"]}, open(os.path.join(OUT, "cena_principal.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return meshes


def main():
    meshes = build()
    cx = -62.0
    # bottom view of the board with the parts: base, lid and rulers hidden (the battery stays)
    rn = set(json.load(open(os.path.join(HW, "pcb", "regua", "posicao_regua.json"), encoding="utf-8"))["pecas"].keys()) | {"base", "tampo", "ferragem", "ks33d", "knob_registros", "knob_volume"}
    rn |= {"regua%d" % r for r in range(4)} | {"grade%d" % r for r in range(4)}
    sel = [m for m in meshes if m[3] not in rn]
    CR.shot(sel, "cena_principal_baixo", cam=[(cx, 30, -150), (cx, 30, 6), (0, 1, 0)], size=(1500, 1400), hide=())
    # iso: case base + board + parts + battery + rulers' left ends, lid hidden
    CR.shot(meshes, "cena_principal_iso", cam=[(-170, -120, 120), (-60, 30, 6), (0, 0, 1)], hide=("tampo",), size=(1800, 1100))
    # section through the registers knob and its sensor (y = 0), the back half seen from the front
    CR.shot(meshes, "corte_principal_registros", normal=(0, 1, 0), origin=(0, 0.01, 0), cam=[(-46, -150, 12), (-46, 0, 12), (0, 0, 1)], size=(1800, 800), scale=22)
    CR.shot(meshes, "corte_principal_volume", normal=(0, 1, 0), origin=(0, C.VOL[1], 0), cam=[(-46, -100, 14), (-46, C.VOL[1], 14), (0, 0, 1)], size=(1800, 800), scale=24)
    # longitudinal section through the strip (x = -47): the right half kept, seen from -x
    CR.shot(meshes, "corte_principal_longitudinal", normal=(1, 0, 0), origin=(-47.0, 0, 0), cam=[(-200, 30, 8), (-47, 30, 8), (0, 0, 1)], size=(2000, 760), scale=44)


if __name__ == "__main__":
    main()
