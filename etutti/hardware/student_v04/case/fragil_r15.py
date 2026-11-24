"""R15V4 item 4.2: remove the thin walls ("hastes") that the cut-outs leave in the tray.

The tray is a stack of vertical prisms (rails, risers, end walls, bosses), so it is cut into BANDS between two consecutive horizontal faces. In each band the plan
section F (rasterised at PIX = 0.05 mm from the tray's own mesh, one image slice per band) is opened with a disc of radius R_OPEN = 0.80 mm (rule 1.5 mm, 0.1 mm of margin for the printer):
open(F) = dilate(erode(F)), done with exact Euclidean distance transforms. F minus open(F) = the parts narrower than 1.5 mm plus the rounded residue of the convex
corners (<= 0.13 mm2). Connected pieces with an area >= MIN_AREA are walls: they are decomposed into rectangles and cut from the tray over the band (each rectangle
grown by GROW mm). Bands lower than MIN_BAND are lips, not walls, and are left alone. The region x < X_FROM (the interface) is checked by hand.
Returns the removed pieces (position, band, area) for the report.
"""
import os
import tempfile

import numpy as np
import pyvista as pv
import vtk
import cadquery as cq
from scipy import ndimage as ndi
from vtk.util.numpy_support import vtk_to_numpy

R_OPEN = 0.80
MIN_AREA = 0.2
MIN_BAND = 0.45
PIX = 0.05
GROW = 0.08


def sections(tray):
    zs = set()
    for f in tray.faces().vals():
        n = f.normalAt()
        if abs(abs(n.z) - 1) < 1e-6:
            zs.add(round(f.Center().z, 3))
    zs = sorted(zs)
    return list(zip(zs[:-1], zs[1:]))


def slice_mask(mesh, zm, org, dims):
    img = vtk.vtkImageData()
    img.SetDimensions(dims[0], dims[1], 1)
    img.SetSpacing(PIX, PIX, 1.0)
    img.SetOrigin(org[0], org[1], zm)
    img.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
    img.GetPointData().GetScalars().Fill(1)
    sten = vtk.vtkPolyDataToImageStencil()
    sten.SetInputData(mesh)
    sten.SetOutputOrigin(org[0], org[1], zm)
    sten.SetOutputSpacing(PIX, PIX, 1.0)
    sten.SetOutputWholeExtent(0, dims[0] - 1, 0, dims[1] - 1, 0, 0)
    sten.Update()
    st = vtk.vtkImageStencil()
    st.SetInputData(img)
    st.SetStencilConnection(sten.GetOutputPort())
    st.ReverseStencilOff()
    st.SetBackgroundValue(0)
    st.Update()
    a = vtk_to_numpy(st.GetOutput().GetPointData().GetScalars()).reshape(dims[1], dims[0])
    return a.astype(bool)                      # [y_file index, x index]


def rects_of(mask):
    """Decompose a boolean mask into rectangles (row runs merged vertically): list of (i0, i1, j0, j1) half open, i = row, j = column."""
    out = []
    active = {}
    for i in range(mask.shape[0] + 1):
        runs = set()
        if i < mask.shape[0]:
            row = mask[i]
            d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
            st, en = np.where(d == 1)[0], np.where(d == -1)[0]
            runs = set(zip(st.tolist(), en.tolist()))
        for r in list(active):
            if r not in runs:
                out.append((active.pop(r), i, r[0], r[1]))
        for r in runs:
            if r not in active:
                active[r] = i
    return out


def levels(mesh, step=0.6):
    """Section levels: every distinct z of the mesh's vertices, each stretch longer than `step` split in equal parts (so a feature that starts at an odd level is seen)."""
    zs = np.unique(np.round(mesh.points[:, 2], 3))
    out = [float(zs[0])]
    for a, b in zip(zs[:-1], zs[1:]):
        n = max(1, int(np.ceil((b - a) / step)))
        out += [float(a + (b - a) * k / n) for k in range(1, n + 1)]
    return list(zip(out[:-1], out[1:]))


def prune(tray, x_from=79.0, persist=0.6):
    """tray: CadQuery Workplane (MODEL frame, y towards the player). Returns (new tray, removed list). A thin piece is removed only if it persists over >= `persist` mm of height
    (clusters of pieces that overlap in plan and touch in z); lower ones are lips, not walls."""
    fd, path = tempfile.mkstemp(suffix=".stl")
    os.close(fd)
    cq.exporters.export(tray.mirror("XZ"), path, tolerance=0.01, angularTolerance=0.1)      # file frame: y_file = -y_model
    mesh = pv.read(path)
    os.remove(path)
    b = mesh.bounds
    org = (b[0] - 0.5, b[2] - 0.5)
    dims = (int((b[1] - b[0] + 1.0) / PIX) + 1, int((b[3] - b[2] + 1.0) / PIX) + 1)
    r_px = R_OPEN / PIX
    pieces = []
    for za, zb in levels(mesh):
        if zb - za < 0.02:
            continue
        zm = (za + zb) / 2.0
        F = slice_mask(mesh, zm, org, dims)
        E = ndi.distance_transform_edt(F) >= r_px
        O = (ndi.distance_transform_edt(~E) <= r_px) if E.any() else np.zeros_like(F)
        T = F & ~O
        T[:, :int((x_from - org[0]) / PIX)] = False
        lab, n = ndi.label(T)
        for k, sl in enumerate(ndi.find_objects(lab), start=1):
            m = lab[sl] == k
            area = m.sum() * PIX * PIX
            if area < MIN_AREA:
                continue
            ys, xs = sl
            pieces.append({"z": (za, zb), "m": m, "xs": xs.start, "ys": ys.start, "area": float(area),
                           "bb": (org[0] + xs.start * PIX, org[0] + xs.stop * PIX, -(org[1] + ys.stop * PIX), -(org[1] + ys.start * PIX))})
    # cluster by plan overlap and z contact
    par = list(range(len(pieces)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i, p in enumerate(pieces):
        for j in range(i + 1, len(pieces)):
            q = pieces[j]
            if abs(p["z"][1] - q["z"][0]) < 1e-3 or abs(q["z"][1] - p["z"][0]) < 1e-3:
                if p["bb"][0] < q["bb"][1] and q["bb"][0] < p["bb"][1] and p["bb"][2] < q["bb"][3] and q["bb"][2] < p["bb"][3]:
                    par[find(i)] = find(j)
    groups = {}
    for i in range(len(pieces)):
        groups.setdefault(find(i), []).append(i)
    removed, cuts = [], None
    for g in groups.values():
        zlo, zhi = min(pieces[i]["z"][0] for i in g), max(pieces[i]["z"][1] for i in g)
        if zhi - zlo < persist:
            continue
        bbs = [pieces[i]["bb"] for i in g]
        removed.append({"z": [round(zlo, 2), round(zhi, 2)], "x": [round(min(v[0] for v in bbs), 2), round(max(v[1] for v in bbs), 2)],
                        "y": [round(min(v[2] for v in bbs), 2), round(max(v[3] for v in bbs), 2)], "area_max_mm2": round(max(pieces[i]["area"] for i in g), 2)})
        for i in g:
            p = pieces[i]
            for (i0, i1, c0, c1) in rects_of(p["m"]):
                x0 = org[0] + (p["xs"] + c0) * PIX - GROW
                x1 = org[0] + (p["xs"] + c1) * PIX + GROW
                y_lo = -(org[1] + (p["ys"] + i1) * PIX) - GROW
                y_hi = -(org[1] + (p["ys"] + i0) * PIX) + GROW
                bx = cq.Workplane("XY").box(x1 - x0, y_hi - y_lo, p["z"][1] - p["z"][0], centered=False).translate((x0, y_lo, p["z"][0]))
                cuts = bx if cuts is None else cuts.union(bx)
    if cuts is not None:
        tray = tray.cut(cuts)
    return tray, removed
