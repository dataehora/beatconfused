"""Student V4 (R13V4, item 2): own preview "equal to JLCPCB's": every EasyEDA 3D model put where the CPL puts it, over the board; fit and pin 1 checks.

    CadQuery venv python (numpy, scipy, PIL, pyvista, cadquery):
    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v04/pcb/previa_jlc.py fit principal|r8
    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v04/pcb/previa_jlc.py draw principal|r8

Needs, before: KiCad python `pcb/previa_dados.py principal|r8` (board dump), `fornecimento/baixar_modelos.py` (STEP files, outside Git).

How the preview is built (the rules of student_v01/fornecimento/cpl_jlc.py):
  1. model (STEP, own frame)  ->  EasyEDA footprint frame: rotate by the SVGNODE c_rotation, move by (c_origin - footprint origin) * 0.254 mm (y up), lowest point at z = `z` * 0.254;
  2. footprint frame -> board: Top: turn by the CPL rotation, move to (Mid X, Mid Y). Bottom: mirror x first, turn by minus the CPL rotation, move; z goes through the
     board (z -> -T - z). (Mid Y is -y_KiCad: all this is y up.)
  3. Checks, all measured on the preview and not copied from the board:
     - fit error: the shift (mm) that best lays the model's seating slab (the lowest part: leads, terminals, pegs) on the board's copper pads (IoU of the two
       masks, 0.05 mm raster, shift searched within +-4 mm), at the nominal turn and at the other three (a better turn = a model that is turned);
     - pin 1: the EasyEDA pad "1" taken through the CPL rules must land on the board's pad "1" (distance, mm); also every other numbered pad (max);
     - mouth of a connector: from the pads to the body centroid, compared with the nearest board edge.
Writes pcb/build/previa_fit_<board>.json and the figures pcb/img/previa_jlc_<board>_{bottom,top}.png (+ the detail sheets).
"""
import csv
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.signal import fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
FORN = os.path.join(HW, "fornecimento")
BUILD = os.path.join(HERE, "build")
IMG = os.path.join(HERE, "img")
MODELS = os.path.join(FORN, "modelos3d")
UNIT = 0.254
CPLS = {"principal": os.path.join(HW, "fab", "principal", "cpl.csv"), "r8": os.path.join(HW, "fab", "regua", "R8E_painel2", "cpl.csv"),
        "r4": os.path.join(HW, "fab", "regua", "R4E_painel5", "cpl.csv")}
PX = 20.0                                  # raster pixels per mm


# ---------------------------------------------------------------- models
def mesh(code):
    """(V, F) of the STEP of an LCSC code, in the model's own frame (cached as .npz next to the STEP)."""
    npz = os.path.join(MODELS, code + ".npz")
    step = os.path.join(MODELS, code + ".step")
    if os.path.exists(npz) and os.path.getmtime(npz) >= os.path.getmtime(step):
        d = np.load(npz)
        return d["V"], d["F"]
    import cadquery as cq
    import pyvista as pv
    stl = os.path.join(MODELS, code + ".stl")
    cq.exporters.export(cq.importers.importStep(step), stl, tolerance=0.02, angularTolerance=0.25)
    m = pv.read(stl).triangulate()
    V = np.asarray(m.points, dtype=float)
    F = np.asarray(m.faces).reshape(-1, 4)[:, 1:]
    np.savez_compressed(npz, V=V, F=F)
    os.remove(stl)
    return V, F


def rot3(rx, ry, rz):
    cx, sx = math.cos(math.radians(rx)), math.sin(math.radians(rx))
    cy, sy = math.cos(math.radians(ry)), math.sin(math.radians(ry))
    cz, sz = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


MODE = {"xy": "centro"}          # 'origem': the STEP origin goes to c_origin; 'centro': the STEP's xy bounding-box centre goes to c_origin


def to_footprint(V, rec, sign=1):
    """Model frame -> EasyEDA footprint frame (mm, y up, z up from the board surface)."""
    ox, oy = rec["footprint_origin"]
    cx, cy = (float(v) for v in rec["c_origin"].split(","))
    if abs(cx - ox) > 200 or abs(cy - oy) > 200:             # C730243: c_origin 400,300 against a footprint origin 4000,3000 (a 10x unit slip in EasyEDA's data): no offset
        cx, cy = ox, oy
    rx, ry, rz = (float(v) for v in rec["c_rotation"].split(","))
    R = rot3(rx, ry, sign * rz)
    P = V @ R.T
    if MODE["xy"] == "centro":
        P[:, :2] -= (P[:, :2].min(0) + P[:, :2].max(0)) / 2
    # z: EasyEDA's `z` is the height of the model's LOWEST point over the board surface (checked on the 0805/0402 passives, whose STEP is centred in z with z = 0, and on the
    # USB-C and M.2, whose STEP minimum equals `z`): the model is lowered/raised so that its lowest point lands at z
    P[:, 2] += float(rec["z"]) * UNIT - P[:, 2].min()
    return P + np.array([(cx - ox) * UNIT, -(cy - oy) * UNIT, 0.0])


def to_board(P, x, y, rotation, bottom, T):
    """Footprint frame -> board frame by the CPL rules; z measured from the board's top surface (bottom parts go below)."""
    P = P.copy()
    if bottom:
        P[:, 0] = -P[:, 0]
        deg = (-rotation) % 360
    else:
        deg = rotation
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    X = P[:, 0] * c - P[:, 1] * s + x
    Y = P[:, 0] * s + P[:, 1] * c + y
    Z = (-T - P[:, 2]) if bottom else P[:, 2]
    return np.column_stack([X, Y, Z])


def point_to_board(p, x, y, rotation, bottom):
    q = np.array([[p[0], p[1], 0.0]])
    return to_board(q, x, y, rotation, bottom, 0.0)[0, :2]


# ---------------------------------------------------------------- raster
def pad_polys(pads):
    """Rectangles (4 corners) of the copper pads of one footprint (global, y up)."""
    out = []
    for n, x, y, sx, sy, shape, ang, onb, pth, drill in pads:
        if sx <= 0 or sy <= 0 or (drill > 0 and not pth):
            continue
        a = math.radians(-ang)
        c, s = math.cos(a), math.sin(a)
        pts = [(x + (u * c - v * s), y + (u * s + v * c)) for u, v in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2))]
        out.append((n, pts))
    return out


def raster(polys, org, shape):
    img = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(img)
    for pts in polys:
        d.polygon([((px - org[0]) * PX, (shape[0] - 1) - (py - org[1]) * PX) for px, py in pts], fill=1)
    return np.asarray(img, dtype=np.float32)


def slab_polys(P, F, s_lo, s_hi, bottom, T):
    """Triangles of the model whose height above the mounting surface lies in [s_lo, s_hi] (xy only)."""
    s = (-(P[:, 2] + T)) if bottom else P[:, 2]
    tri_s = s[F]
    keep = (tri_s.min(1) >= s_lo - 1e-6) & (tri_s.max(1) <= s_hi + 1e-6)
    return [P[t, :2] for t in F[keep]], float(s.min())


def best_shift(pad_mask, mdl_mask, rad_px):
    """Coverage of the pads by the model's projection for every shift within rad_px. Returns (max coverage, dx, dy of the SMALLEST shift reaching it
    within 0.5 %, coverage at zero shift). The smallest shift is the fit error: a body that already covers the pads is not asked to move."""
    pm, mm = pad_mask, mdl_mask
    corr = fftconvolve(pm, mm[::-1, ::-1], mode="full")
    mh, mw = mm.shape
    ap = max(float(pm.sum()), 1e-9)
    i0, j0 = mh - 1, mw - 1
    ys, xs = np.mgrid[-rad_px:rad_px + 1, -rad_px:rad_px + 1]
    sub = corr[i0 - rad_px:i0 + rad_px + 1, j0 - rad_px:j0 + rad_px + 1] / ap
    sel = (ys ** 2 + xs ** 2) <= rad_px ** 2
    cov = np.where(sel, sub, -1)
    cmax = float(cov.max())
    ok = np.argwhere(cov >= cmax - 0.005)
    dist = [(ys[i, j] ** 2 + xs[i, j] ** 2, i, j) for i, j in ok]
    _, i, j = min(dist)
    return (cmax, int(xs[i, j]), int(ys[i, j])), float(cov[rad_px, rad_px])


# ---------------------------------------------------------------- the fit of one part
def read_cpl(board):
    rows = {}
    for r in csv.DictReader(open(CPLS[board], encoding="utf-8")):
        rows[r["Designator"]] = (float(r["Mid X"][:-2]), float(r["Mid Y"][:-2]), float(r["Rotation"]), r["Layer"] == "Bottom")
    return rows


def ee_pads(code):
    """EasyEDA pads with numbers: [(num, x, y)] mm, y up, from the footprint origin."""
    return [tuple(p) for p in json.load(open(os.path.join(FORN, "easyeda_pads.json"), encoding="utf-8"))[code]]


def fit_part(ref, f, cpl, rec, T, sign):
    """Fit error = the largest distance, over the part's contact pads, from the pad centre to the model's xy projection (0 = every pad centre lies under the
    model). (dx, dy) = the shift of the model that makes that largest distance smallest (the smallest such shift): what a correction of the model's offset would be."""
    from scipy.ndimage import distance_transform_edt
    x, y, rot, bottom = cpl
    V, F = mesh(f["lcsc"])
    P = to_board(to_footprint(V, rec, sign), x, y, rot, bottom, T)
    sv = (-(P[:, 2] + T)) if bottom else P[:, 2]
    cont = [(p[1], p[2]) for p in f["pads"] if p[3] > 0 and p[4] > 0 and not (p[9] > 0 and not p[8])]
    cp = np.array(cont)
    org = np.minimum(cp.min(0), P[:, :2].min(0)) - 6.0
    top = np.maximum(cp.max(0), P[:, :2].max(0)) + 6.0
    shape = (int((top[1] - org[1]) * PX) + 1, int((top[0] - org[0]) * PX) + 1)
    res = {}
    for q in (0, 90, 180, 270):
        c, s_ = math.cos(math.radians(q)), math.sin(math.radians(q))
        XY = P[:, :2] - [x, y]
        XY = np.column_stack([XY[:, 0] * c - XY[:, 1] * s_, XY[:, 0] * s_ + XY[:, 1] * c]) + [x, y]
        tri = XY[F]
        mm = raster([[tuple(a) for a in t] for t in tri], org, shape)
        edt = distance_transform_edt(1 - mm) / PX                 # mm from each cell to the model's projection
        rows = shape[0] - 1 - (cp[:, 1] - org[1]) * PX
        cols = (cp[:, 0] - org[0]) * PX
        rad = int(4.0 * PX)
        best = None
        for dy in range(-rad, rad + 1, 2):
            for dx in range(-rad, rad + 1, 2):
                if dx * dx + dy * dy > rad * rad:
                    continue
                ri = np.clip(np.round(rows - (-dy)).astype(int), 0, shape[0] - 1)       # a model shift (dx, dy mm) = looking the pads up at (p - shift)
                ci = np.clip(np.round(cols - dx).astype(int), 0, shape[1] - 1)
                m = float(edt[ri, ci].max())
                key = (round(m, 2), dx * dx + dy * dy)
                if best is None or key < best[0]:
                    best = (key, dx, dy)
        rows0 = np.clip(np.round(rows).astype(int), 0, shape[0] - 1)
        cols0 = np.clip(np.round(cols).astype(int), 0, shape[1] - 1)
        d0 = edt[rows0, cols0]
        res[q] = (float(d0.max()), best[0][0], best[1] / PX, best[2] / PX, d0)
    d0max, dcorr, dx, dy, dist = res[0]
    others = {q: round(res[q][0], 2) for q in (90, 180, 270)}
    nums = [p[0] for p in f["pads"] if p[3] > 0 and p[4] > 0 and not (p[9] > 0 and not p[8])]
    worst = nums[int(np.argmax(dist))] if len(nums) == len(dist) else None
    return {"erro_ajuste_mm": round(d0max, 2), "pad_pior": worst, "erro_apos_correcao_mm": round(dcorr, 2), "dx": round(dx, 2), "dy": round(dy, 2),
            "s_min": round(float(sv.min()), 2), "s_max": round(float(sv.max()), 2), "erro_se_girado": others,
            "giro_melhor_que_o_nominal": bool(d0max > 0.5 and min(others.values()) < 0.3)}


def pin_check(ref, f, cpl):
    """EasyEDA pads through the CPL rules against the board's pads, by number: (pin 1 distance, max distance over the numbered pads)."""
    x, y, rot, bottom = cpl
    eep = ee_pads(f["lcsc"])
    bp = {}
    for n, px, py, *_ in f["pads"]:
        bp.setdefault(n, []).append((px, py))
    d1, dm, miss = None, 0.0, []
    for n, ex, ey in eep:
        q = point_to_board((ex, ey), x, y, rot, bottom)
        cand = bp.get(n)
        if not cand:
            miss.append(n)
            continue
        d = min(math.hypot(q[0] - c[0], q[1] - c[1]) for c in cand)
        dm = max(dm, d)
        if n == "1":
            d1 = d
    return {"dist_pino1_mm": None if d1 is None else round(d1, 3), "dist_max_pads_mm": round(dm, 3), "pads_sem_par": miss}


def marker_info(code, rec):
    """Pin 1 dimple of an IC model: the biggest small flat cluster below the top face, in the EasyEDA footprint frame, and the two EasyEDA pads nearest to it."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    V, F = mesh(code)
    Pf = to_footprint(V, rec)
    tri = Pf[F]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nz = n[:, 2] / (np.linalg.norm(n, axis=1) + 1e-12)
    ztop = Pf[:, 2].max()
    zs = tri[:, :, 2].mean(1)
    flat = (nz > 0.999) & (tri[:, :, 2].max(1) - tri[:, :, 2].min(1) < 0.002) & (zs < ztop - 0.01) & (zs > ztop - 0.6)
    ids = np.where(flat)[0]
    if len(ids) == 0:
        return None
    keys, rows, cols = {}, [], []
    for a_, i in enumerate(ids):
        for v in F[i]:
            k = tuple(np.round(Pf[v], 3))
            if k in keys:
                rows.append(a_)
                cols.append(keys[k])
            else:
                keys[k] = a_
    g = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(ids), len(ids)))
    nc, lab = connected_components(g, directed=False)
    lo, hi = Pf[:, :2].min(0), Pf[:, :2].max(0)
    best = None
    for c in range(nc):
        sel = ids[lab == c]
        pts = Pf[F[sel]].reshape(-1, 3)
        ext = pts[:, :2].max(0) - pts[:, :2].min(0)
        area = 0.5 * np.linalg.norm(np.cross(Pf[F[sel, 1]] - Pf[F[sel, 0]], Pf[F[sel, 2]] - Pf[F[sel, 0]]), axis=1).sum()
        cen = pts[:, :2].mean(0)
        if ext.max() > 0.5 or area < 0.005 or not (lo < cen).all() or not (cen < hi).all():
            continue
        if best is None or area > best[0]:
            best = (area, cen)
    if best is None:
        return None
    eep = ee_pads(code)
    near = sorted(eep, key=lambda p: math.hypot(p[1] - best[1][0], p[2] - best[1][1]))[:2]
    return {"xy": [round(float(best[1][0]), 2), round(float(best[1][1]), 2)], "area": round(float(best[0]), 3), "pads_proximos": [n[0] for n in near],
            "ok": "1" in [n[0] for n in near]}


def mouth(f, cpl, rec, T, outline):
    """Direction of a connector's mouth in the board frame: from the signal pads to the model's bounding-box centre, rounded to an axis; and the board edge it points to."""
    x, y, rot, bottom = cpl
    V, F = mesh(f["lcsc"])
    P = to_board(to_footprint(V, rec), x, y, rot, bottom, T)
    pads = np.array([[p[1], p[2]] for p in f["pads"] if p[3] > 0 and p[0] not in ("MP", "0", "")])
    if len(pads) == 0:
        pads = np.array([[p[1], p[2]] for p in f["pads"]])
    c_pads = pads.mean(0)
    c_body = (P[:, :2].min(0) + P[:, :2].max(0)) / 2
    v = c_body - c_pads
    ax = 0 if abs(v[0]) > abs(v[1]) else 1
    dirv = [0, 0]
    dirv[ax] = 1 if v[ax] > 0 else -1
    lo, hi = outline
    cen = c_body
    # distance from the part to each edge of the outline's bounding box along the direction pointed to
    edge = {(1, 0): hi[0] - P[:, 0].max(), (-1, 0): P[:, 0].min() - lo[0], (0, 1): hi[1] - P[:, 1].max(), (0, -1): P[:, 1].min() - lo[1]}[tuple(dirv)]
    return {"boca": {(1, 0): "+x (direita)", (-1, 0): "-x (esquerda)", (0, 1): "+y (cima)", (0, -1): "-y (baixo)"}[tuple(dirv)], "vetor": [round(float(v[0]), 2), round(float(v[1]), 2)],
            "folga_ate_borda_mm": round(float(edge), 2), "corpo_x": [round(float(P[:, 0].min()), 2), round(float(P[:, 0].max()), 2)],
            "corpo_y": [round(float(P[:, 1].min()), 2), round(float(P[:, 1].max()), 2)]}


def main_fit(board, sign):
    d = json.load(open(os.path.join(BUILD, "previa_%s.json" % board), encoding="utf-8"))
    idx = json.load(open(os.path.join(FORN, "modelos3d_indice.json"), encoding="utf-8"))
    cpl = read_cpl(board)
    T = d["thickness"]
    out = {}
    only = os.environ.get("REFS", "").split(",") if os.environ.get("REFS") else None
    for ref in sorted(cpl):
        if only and ref not in only:
            continue
        f = d["fps"][ref]
        rec = idx.get(f["lcsc"])
        row = {"lcsc": f["lcsc"], "valor": f["value"], "footprint": f["name"], "lado": "fundo" if cpl[ref][3] else "topo", "giro_cpl": cpl[ref][2]}
        if not rec or not rec.get("modelo") or not os.path.exists(os.path.join(MODELS, f["lcsc"] + ".step")):
            row["modelo"] = False
            out[ref] = row
            continue
        row["modelo"] = True
        row["modelo3d"] = rec["nome3d"]
        row.update(pin_check(ref, f, cpl[ref]))
        ol = np.array([[o[1], o[2]] for o in d["outline"]] + [[o[3], o[4]] for o in d["outline"]])
        if ref[0] in "UQ" and len(f["pads"]) >= 5:
            try:
                row["marcador_pino1"] = marker_info(f["lcsc"], rec)
            except Exception as e:
                row["marcador_pino1"] = {"erro": repr(e)}
        if ref[0] == "J":
            row["boca"] = mouth(f, cpl[ref], rec, T, (ol.min(0), ol.max(0)))
        try:
            row.update(fit_part(ref, f, cpl[ref], rec, T, sign))
        except Exception as e:                                   # keep going: one odd model must not hide the others
            row["erro"] = repr(e)
        out[ref] = row
        print(ref, f["lcsc"], {k: row.get(k) for k in ("erro_ajuste_mm", "pad_pior", "dist_pino1_mm", "s_min", "dx", "dy", "erro_apos_correcao_mm")}, flush=True)
    json.dump(out, open(os.path.join(BUILD, "previa_fit_%s.json" % board), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


# ---------------------------------------------------------------- drawing
COLORS = {"C": (0.80, 0.68, 0.45), "R": (0.10, 0.10, 0.10), "D": (0.12, 0.12, 0.14), "Q": (0.12, 0.12, 0.14), "U": (0.10, 0.10, 0.12), "J": (0.72, 0.72, 0.74),
          "L": (0.25, 0.25, 0.28), "F": (0.25, 0.25, 0.28), "S": (0.60, 0.60, 0.62), "H": (0.6, 0.6, 0.6)}
FONT = "C:/Windows/Fonts/arial.ttf"


def placed_mesh(ref, f, cpl, rec, T, sign, shift=(0.0, 0.0)):
    V, F = mesh(f["lcsc"])
    P = to_board(to_footprint(V, rec, sign), *cpl[:3], cpl[3], T)
    P[:, 0] += shift[0]
    P[:, 1] += shift[1]
    return P, F


def draw(board, side, window=None, refs=None, name=None, size=2400, corrected=False, sign=1, title=None, pin1=True, labels=True):
    import pyvista as pv
    d = json.load(open(os.path.join(BUILD, "previa_%s.json" % board), encoding="utf-8"))
    idx = json.load(open(os.path.join(FORN, "modelos3d_indice.json"), encoding="utf-8"))
    fit = json.load(open(os.path.join(BUILD, "previa_fit_%s.json" % board), encoding="utf-8")) if os.path.exists(os.path.join(BUILD, "previa_fit_%s.json" % board)) else {}
    cpl = read_cpl(board)
    T = d["thickness"]
    bottom = side == "bottom"
    # outline bbox
    ol = np.array([[o[1], o[2]] for o in d["outline"]] + [[o[3], o[4]] for o in d["outline"]])
    x0, y0, x1, y1 = (window if window else (ol[:, 0].min() - 3, ol[:, 1].min() - 3, ol[:, 0].max() + 3, ol[:, 1].max() + 3))
    wmm, hmm = x1 - x0, y1 - y0
    k = size / max(wmm, hmm)
    W, H = int(round(wmm * k)), int(round(hmm * k))
    pl = pv.Plotter(off_screen=True, window_size=(W, H))
    pl.set_background((0.97, 0.96, 0.93))
    # board body: the outline's bbox as a slab (the panel's tabs/slots are not drawn: the preview is about the parts)
    lo = ol.min(0)
    hi = ol.max(0)
    pl.add_mesh(pv.Box(bounds=(lo[0], hi[0], lo[1], hi[1], -T, 0)), color=(0.10, 0.32, 0.20), smooth_shading=False)
    for ref, f in d["fps"].items():
        for n, x, y, sx, sy, shape, ang, onb, pth, drill in f["pads"]:
            if sx <= 0 or sy <= 0 or (drill > 0 and not pth):
                continue
            onbottom = f["bottom"]
            if pth:
                onbottom = bottom
            if onbottom != bottom:
                continue
            zz = (-T - 0.02, -T) if bottom else (0.0, 0.02)
            c = np.array([x, y])
            a = math.radians(-ang)
            hx, hy = (abs(sx * math.cos(a)) + abs(sy * math.sin(a))) / 2, (abs(sx * math.sin(a)) + abs(sy * math.cos(a))) / 2
            pl.add_mesh(pv.Box(bounds=(c[0] - hx, c[0] + hx, c[1] - hy, c[1] + hy, zz[0], zz[1])), color=(0.85, 0.65, 0.20))
    placed = []
    for ref in sorted(cpl):
        if refs and ref not in refs:
            continue
        f = d["fps"][ref]
        rec = idx.get(f["lcsc"])
        if not rec or not rec.get("modelo") or not os.path.exists(os.path.join(MODELS, f["lcsc"] + ".step")):
            continue
        if cpl[ref][3] != bottom:
            continue
        sh = (fit.get(ref, {}).get("dx", 0.0), fit.get(ref, {}).get("dy", 0.0)) if corrected else (0.0, 0.0)
        P, F = placed_mesh(ref, f, cpl[ref], rec, T, sign, sh)
        pm = pv.PolyData(P, np.column_stack([np.full(len(F), 3), F]).ravel())
        pl.add_mesh(pm, color=COLORS.get(ref[0], (0.5, 0.5, 0.5)), smooth_shading=False, specular=0.2)
        placed.append((ref, P))
    if pin1:                                                      # red ring at the board's pad 1 of every part with 3 or more pads
        for ref, P in placed:
            f = d["fps"][ref]
            p1 = [p for p in f["pads"] if p[0] == "1"]
            if p1 and len(f["pads"]) >= 3 and ref[0] in "UQDJ":
                z = (-T - 3.0) if bottom else 6.0
                ring = pv.Disc(center=(p1[0][1], p1[0][2], z), inner=0.28, outer=0.42, normal=(0, 0, 1), c_res=24)
                pl.add_mesh(ring, color=(0.9, 0.05, 0.05), lighting=False)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    zc = -T - 40 if bottom else 40
    pl.camera.parallel_projection = True
    tx, ty = (float(v) for v in os.environ.get("INCLINA", "0,0").split(","))
    pl.camera.position = (cx + tx, cy + ty, zc)
    pl.camera.focal_point = (cx, cy, 0)
    pl.camera.up = (0, 1, 0)
    pl.camera.parallel_scale = hmm / 2
    pl.enable_lightkit() if hasattr(pl, "enable_lightkit") else None
    img = pl.screenshot(return_img=True)
    pl.close()
    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    from PIL import ImageFont
    fs = max(12, int(size / 150))
    font = ImageFont.truetype(FONT, fs)

    def px(x, y):
        u = (x - cx) * (W / wmm) * (1 if not bottom else -1)
        return W / 2 + u, H / 2 - (y - cy) * (H / hmm)
    if labels:
        taken = []
        for ref, P in placed:
            bb0, bb1 = P[:, :2].min(0), P[:, :2].max(0)
            a, b = px(bb0[0], bb0[1]), px(bb1[0], bb1[1])
            L, R_, Tp, B = min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])
            tw = dr.textlength(ref, font=font)
            best = None
            for r_ in (4, 22, 44, 70, 100):
                for ang in (0, 90, 180, 270, 45, 135, 225, 315):
                    cxp = (L + R_) / 2 + math.cos(math.radians(ang)) * ((R_ - L) / 2 + r_ + tw / 2 * abs(math.cos(math.radians(ang))))
                    cyp = (Tp + B) / 2 - math.sin(math.radians(ang)) * ((B - Tp) / 2 + r_ + fs / 2)
                    box = (cxp - tw / 2 - 2, cyp - fs / 2 - 2, cxp + tw / 2 + 2, cyp + fs / 2 + 2)
                    if box[0] < 0 or box[1] < 0 or box[2] > W or box[3] > H:
                        continue
                    if any(not (box[2] < t[0] or box[0] > t[2] or box[3] < t[1] or box[1] > t[3]) for t in taken):
                        continue
                    best = (box, cxp, cyp)
                    break
                if best:
                    break
            if best:
                box, cxp, cyp = best
                taken.append(box)
                dr.line([((L + R_) / 2, (Tp + B) / 2), (cxp, cyp)], fill=(20, 20, 20), width=1)
                dr.rectangle(box, fill=(255, 255, 255))
                dr.text((box[0] + 2, box[1] + 1), ref, fill=(0, 0, 160), font=font)
    if labels:                                    # parts the JLCPCB does not place: pads only, named
        for ref, f in d["fps"].items():
            if ref in cpl or ref.startswith(("PEG", "MB", "FID", "H")) and not ref.startswith("H1"):
                continue
            if ref.startswith("H1") and len(ref) > 3:
                continue
            if any(p_[8] for p_ in f["pads"]) and not ref.startswith(("SW", "J", "H")):
                continue
            if f["bottom"] != bottom and not any(p_[8] for p_ in f["pads"]):
                continue
            u, v = px(f["x"], f["y"])
            txt = ref + (" (em casa)" if ref.startswith(("SW40", "J50")) else " (nao montar)" if ref == "C310" else "")
            dr.rectangle((u - 2, v - fs / 2 - 2, u + dr.textlength(txt, font=font) + 2, v + fs / 2 + 2), fill=(255, 255, 220))
            dr.text((u, v - fs / 2), txt, fill=(150, 40, 0), font=font)
    if title:
        big = ImageFont.truetype(FONT, int(fs * 1.5))
        dr.rectangle((0, 0, W, int(fs * 2.4)), fill=(255, 255, 255))
        dr.text((8, 4), title, fill=(0, 0, 0), font=big)
    out = os.path.join(IMG, name or "previa_jlc_%s_%s.png" % (board, side))
    os.makedirs(IMG, exist_ok=True)
    im.save(out)
    print("figura", out, W, H)


if __name__ == "__main__":
    cmd, board = sys.argv[1], sys.argv[2]
    sign = -1 if "--menos" in sys.argv else 1
    if "--origem" in sys.argv:
        MODE["xy"] = "origem"
    if cmd == "fit":
        main_fit(board, sign)
    elif cmd == "draw":
        side = sys.argv[3]
        win = tuple(float(v) for v in os.environ["JANELA"].split(",")) if os.environ.get("JANELA") else None
        refs = os.environ["REFS"].split(",") if os.environ.get("REFS") else None
        draw(board, side, win, refs, os.environ.get("NOME"), int(os.environ.get("TAM", "2400")), bool(os.environ.get("CORRIGIDA")), sign, os.environ.get("TITULO"))
