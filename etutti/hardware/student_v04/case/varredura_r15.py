"""R15V4 item 4.1: automatic scan of the base (tray) and the lid for fragile parts.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/varredura_r15.py [tag]     tag: "" (current out/r4_32_*.stl) or "antes"

Method (numpy + scipy; the STL of case_r4.py voxelised at VOX = 0.25 mm):
  A. thin walls and necks: morphological opening of the solid by a ball of radius 0.75 mm (= the 1.5 mm rule); every voxel of the solid that no 1.5 mm ball
     inscribed in the solid covers is "thin" (wall or blade < 1.5 mm, or a neck of an island). Connected groups of thin voxels (26-neighbourhood) are listed with
     position, volume and the smallest thickness found (local thickness = 2 x the biggest inscribed radius, from the distance transform). Groups under 3 mm3 are the
     rounded sharp edges of the opening and are not listed (counted only).
  B. slender pins / blades: opening by a ball of radius 2.0 mm removes every thin or small part; the rest of A's survivors (solid parts thicker than 1.5 that are removed by
     the r 2.0 opening) are kept as candidates, and each is measured: height along z over its smallest horizontal width (the bounding box of the group's cross-section
     at its base); listed when height > 3 x smallest width.
  C. islands: the part count of the solid after the opening of A (pieces joined only through thin necks become separate pieces).
Output: out/varredura_r15_<tag>.json and the list printed. Figures are drawn by varredura_fig_r15.py from the JSON.
"""
import json
import os
import sys

import numpy as np
import pyvista as pv
import vtk
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
VOX = 0.25


def voxelise(path, vox=VOX):
    m = pv.read(path)
    b = m.bounds
    pad = 1.0
    org = (b[0] - pad, b[2] - pad, b[4] - pad)
    dims = tuple(int((b[2 * i + 1] - b[2 * i] + 2 * pad) / vox) + 1 for i in range(3))
    img = vtk.vtkImageData()
    img.SetDimensions(*dims)
    img.SetSpacing(vox, vox, vox)
    img.SetOrigin(*org)
    img.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
    img.GetPointData().GetScalars().Fill(1)
    pdsten = vtk.vtkPolyDataToImageStencil()
    pdsten.SetInputData(m)
    pdsten.SetOutputOrigin(*org)
    pdsten.SetOutputSpacing(vox, vox, vox)
    pdsten.SetOutputWholeExtent(img.GetExtent())
    pdsten.Update()
    st = vtk.vtkImageStencil()
    st.SetInputData(img)
    st.SetStencilConnection(pdsten.GetOutputPort())
    st.ReverseStencilOff()
    st.SetBackgroundValue(0)
    st.Update()
    out = st.GetOutput()
    from vtk.util.numpy_support import vtk_to_numpy
    a = vtk_to_numpy(out.GetPointData().GetScalars()).reshape(dims[2], dims[1], dims[0])   # z, y, x
    return np.transpose(a, (2, 1, 0)).astype(bool), org                                    # x, y, z


def ball(r_vox):
    n = int(np.ceil(r_vox))
    g = np.mgrid[-n:n + 1, -n:n + 1, -n:n + 1]
    return (g[0] ** 2 + g[1] ** 2 + g[2] ** 2) <= r_vox ** 2 + 1e-9


def disc(r_vox):
    n = int(np.ceil(r_vox))
    g = np.mgrid[-n:n + 1, -n:n + 1]
    return ((g[0] ** 2 + g[1] ** 2) <= r_vox ** 2 + 1e-9)[:, :, None]


def opening(a, r_mm, kind="ball"):
    """ball: 3D ball; disc: horizontal disc (walls in plan: every z layer on its own, so the flat faces give no false skins); line: vertical line of 2r (thin plates)."""
    if kind == "ball":
        s = ball(r_mm / VOX)
    elif kind == "disc":
        s = disc(r_mm / VOX)
    else:
        s = np.ones((1, 1, int(round(2 * r_mm / VOX))), bool)
    return ndi.binary_dilation(ndi.binary_erosion(a, s, border_value=0), s)


def to_world(idx, org):
    """voxel index -> (x, y_model, z) in the MODEL frame (the STL is mirrored in y: y_file = -y_model)."""
    x = org[0] + (idx[0] + 0.5) * VOX
    y = -(org[1] + (idx[1] + 0.5) * VOX)
    z = org[2] + (idx[2] + 0.5) * VOX
    return x, y, z


def scan(path, name, r_thin=0.75, r_big=2.0, min_vol=3.0):
    a, org = voxelise(path)
    vol = a.sum() * VOX ** 3
    op = opening(a, r_thin, "disc")
    thin = a & ~op
    edt = np.zeros(a.shape, np.float32)
    for k in range(a.shape[2]):
        edt[:, :, k] = ndi.distance_transform_edt(a[:, :, k]) * VOX
    lab, n = ndi.label(thin, structure=np.ones((3, 3, 3)))
    res = {"peca": name, "volume_mm3": round(float(vol), 1), "voxel_mm": VOX, "finas": [], "descartadas_menores_que_3mm3": 0}
    objs = ndi.find_objects(lab)
    for i, sl in enumerate(objs, start=1):
        m = lab[sl] == i
        v = m.sum() * VOX ** 3
        if v < min_vol:
            res["descartadas_menores_que_3mm3"] += 1
            continue
        idx = np.argwhere(m) + np.array([s.start for s in sl])
        if m.any(axis=2).sum() * VOX ** 2 < 0.6:          # footprint under 0.6 mm2: the rounded residue of a convex corner of the opening (area 0.13 + voxel noise), not a wall
            res["descartadas_menores_que_3mm3"] += 1
            continue
        c = idx.mean(axis=0)
        lo, hi = idx.min(axis=0), idx.max(axis=0)
        w0, w1 = to_world(lo, org), to_world(hi, org)
        sub = edt[sl][m]
        res["finas"].append({"n": len(res["finas"]) + 1, "centro": [round(float(t), 2) for t in to_world(c, org)],
                             "x": [round(float(min(w0[0], w1[0])), 1), round(float(max(w0[0], w1[0])), 1)], "y": [round(float(min(w0[1], w1[1])), 1), round(float(max(w0[1], w1[1])), 1)],
                             "z": [round(float(min(w0[2], w1[2])), 1), round(float(max(w0[2], w1[2])), 1)],
                             "volume_mm3": round(float(v), 1), "espessura_min_mm": round(float(2 * sub.max()), 2)})
    # B: slender pins: solid parts that survive the 1.5 opening but vanish in the r_big one; each group's height / width
    big = opening(op, r_big, "ball")
    cand = op & ~big
    lab2, n2 = ndi.label(cand, structure=np.ones((3, 3, 3)))
    res["esbeltas"] = []
    for i, sl in enumerate(ndi.find_objects(lab2), start=1):
        m = lab2[sl] == i
        v = m.sum() * VOX ** 3
        if v < 6.0:
            continue
        idx = np.argwhere(m) + np.array([s.start for s in sl])
        lo, hi = idx.min(axis=0), idx.max(axis=0)
        ext = (hi - lo + 1) * VOX
        h = float(ext[2])
        w = float(min(ext[0], ext[1]))
        # width = the smallest horizontal extent of the group's footprint (the mean cross-section over the height)
        foot = m.any(axis=2)
        area = foot.sum() * VOX ** 2
        wmean = float(2 * np.sqrt(area / np.pi)) if area > 0 else 0.0
        if h > 3.0 * min(w, wmean) and h > 3.0:
            w0, w1 = to_world(lo, org), to_world(hi, org)
            res["esbeltas"].append({"centro": [round(float(t), 2) for t in to_world(idx.mean(axis=0), org)], "altura_mm": round(h, 1), "largura_min_mm": round(min(w, wmean), 2),
                                    "x": [round(min(w0[0], w1[0]), 1), round(max(w0[0], w1[0]), 1)], "y": [round(min(w0[1], w1[1]), 1), round(max(w0[1], w1[1]), 1)],
                                    "z": [round(min(w0[2], w1[2]), 1), round(max(w0[2], w1[2]), 1)], "volume_mm3": round(float(v), 1)})
    # C: islands joined by thin necks
    labc, nc = ndi.label(op, structure=np.ones((3, 3, 3)))
    sizes = ndi.sum(op, labc, range(1, nc + 1)) * VOX ** 3
    res["pecas_apos_abertura"] = [round(float(s), 1) for s in sorted(sizes, reverse=True)[:8]]
    res["pecas_n"] = int(nc)
    return res


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else ""
    res = []
    for nm in ("base", "tampa"):
        p = os.path.join(OUT, "r4_32_%s.stl" % nm)
        if tag:
            p = os.path.join(OUT, "r4_32_%s_%s.stl" % (nm, tag))
        r = scan(p, nm)
        res.append(r)
        print(nm, "volume", r["volume_mm3"], "finas", len(r["finas"]), "esbeltas", len(r["esbeltas"]), "pecas", r["pecas_n"], r["pecas_apos_abertura"][:4])
        for f in r["finas"]:
            print("  fina #%d  x %s y %s z %s  v %.1f mm3  e_min %.2f" % (f["n"], f["x"], f["y"], f["z"], f["volume_mm3"], f["espessura_min_mm"]))
        for f in r["esbeltas"]:
            print("  esbelta  x %s y %s z %s  h %.1f  w %.2f" % (f["x"], f["y"], f["z"], f["altura_mm"], f["largura_min_mm"]))
    json.dump(res, open(os.path.join(OUT, "varredura_r15%s.json" % ("_" + tag if tag else ""), ), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
