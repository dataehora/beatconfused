"""Student V4 (R13V4, item 2.3): STEP models in each footprint's own (top-side, y up) frame, for KiCad. CadQuery venv python.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v04/pcb/modelos_kicad.py principal|r8

One file per footprint name + LCSC code in fornecimento/modelos3d/kicad/ (outside Git), the model already turned/moved so that KiCad's model offset/rotation stay 0:
EasyEDA frame (previa_jlc.to_footprint: c_rotation, bbox-centre rule, lowest point at z) -> the footprint's local frame by laying the EasyEDA pads on the footprint's own pads
(same fit as cpl_jlc.py, no mirror: KiCad mirrors a bottom footprint and its model itself). `ajustar` moves the 4 codes whose EasyEDA offset is wrong (fit error > 0.3 mm)
by the shift found in previa_fit_<board>.json, so KiCad shows them on their pads. Writes pcb/build/modelos_kicad_<board>.json (ref -> model file).
"""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import previa_jlc as P
import cadquery as cq

OUT = os.path.join(P.MODELS, "kicad")


def fit_local(local, ee):
    ln = [n for n, _, _ in local]
    en = [n for n, _, _ in ee]
    common = {n for n in ln if ln.count(n) == 1 and en.count(n) == 1}
    best = None
    for deg in (0, 90, 180, 270):
        c, s = round(math.cos(math.radians(deg))), round(math.sin(math.radians(deg)))
        e = [(n, x * c - y * s, x * s + y * c) for n, x, y in ee]
        if len(common) >= max(2, 0.6 * min(len(ln), len(en))):
            eb = {n: (x, y) for n, x, y in e}
            pairs = [((x, y), eb[n]) for n, x, y in local if n in common]
        else:
            cb = np.mean([[x, y] for _, x, y in local], axis=0)
            ce = np.mean([[x, y] for _, x, y in e], axis=0)
            pairs = []
            for _, x, y in local:
                q = min(e, key=lambda t: (t[1] - ce[0] - x + cb[0]) ** 2 + (t[2] - ce[1] - y + cb[1]) ** 2)
                pairs.append(((x, y), (q[1], q[2])))
        tx = sum(b[0] - q[0] for b, q in pairs) / len(pairs)
        ty = sum(b[1] - q[1] for b, q in pairs) / len(pairs)
        cost = max(math.hypot(b[0] - q[0] - tx, b[1] - q[1] - ty) for b, q in pairs)
        if best is None or cost < best[0]:
            best = (cost, deg, tx, ty)
    return best


def main(board):
    d = json.load(open(os.path.join(P.BUILD, "previa_%s.json" % board), encoding="utf-8"))
    idx = json.load(open(os.path.join(P.FORN, "modelos3d_indice.json"), encoding="utf-8"))
    fitj = json.load(open(os.path.join(P.BUILD, "previa_fit_%s.json" % board), encoding="utf-8"))
    cpl = P.read_cpl(board)
    os.makedirs(OUT, exist_ok=True)
    mapping, done = {}, {}
    for ref in sorted(cpl):
        f = d["fps"][ref]
        code = f["lcsc"]
        key = "%s_%s" % (f["name"][:60], code)
        mapping[ref] = key + ".step"
        if key in done:
            continue
        done[key] = True
        rec = idx[code]
        V, F = P.mesh(code)
        # EasyEDA frame steps, repeated on the CadQuery shape
        ox, oy = rec["footprint_origin"]
        cx, cy = (float(v) for v in rec["c_origin"].split(","))
        if abs(cx - ox) > 200 or abs(cy - oy) > 200:
            cx, cy = ox, oy
        rx, ry, rz = (float(v) for v in rec["c_rotation"].split(","))
        R = P.rot3(rx, ry, rz)
        Q = V @ R.T
        c_xy = (Q[:, :2].min(0) + Q[:, :2].max(0)) / 2
        dz = float(rec["z"]) * P.UNIT - Q[:, 2].min()
        t_ee = np.array([-c_xy[0] + (cx - ox) * P.UNIT, -c_xy[1] - (cy - oy) * P.UNIT, dz])
        lp = [(n, -x if f["bottom"] else x, y) for n, x, y in f["local_pads"] if n != ""]     # a bottom footprint stores its pads mirrored: back to the library's top-side frame
        cost, deg, tx, ty = fit_local(lp, P.ee_pads(code))
        corr = np.zeros(2)
        fr = fitj.get(ref, {})
        if fr.get("erro_ajuste_mm", 0) > 0.3 and fr.get("erro_apos_correcao_mm", 9) < 0.3:   # undo the library's wrong offset
            x, y, rot, bottom = cpl[ref]
            cb = np.array([fr["dx"], fr["dy"]])
            dg = (-rot) % 360 if bottom else rot
            c, s = math.cos(math.radians(-dg)), math.sin(math.radians(-dg))
            v = np.array([cb[0] * c - cb[1] * s, cb[0] * s + cb[1] * c])
            if bottom:
                v[0] = -v[0]
            corr = v
        sh = cq.importers.importStep(os.path.join(P.MODELS, code + ".step"))
        for ax, a in (((1, 0, 0), rx), ((0, 1, 0), ry), ((0, 0, 1), rz)):
            if a:
                sh = sh.rotate((0, 0, 0), ax, a)
        sh = sh.translate((float(t_ee[0] + corr[0]), float(t_ee[1] + corr[1]), float(t_ee[2])))
        sh = sh.rotate((0, 0, 0), (0, 0, 1), deg).translate((tx, ty, 0))
        cq.exporters.export(sh, os.path.join(OUT, key + ".step"))
        print(key, "ajuste local %.3f mm, giro %d" % (cost, deg), "correcao" if corr.any() else "", flush=True)
    json.dump(mapping, open(os.path.join(P.BUILD, "modelos_kicad_%s.json" % board), "w"), indent=0)


if __name__ == "__main__":
    main(sys.argv[1])
