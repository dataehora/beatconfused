"""eTutti Student V4 (R13V4): the 32-key instrument for the photo-real renders (Blender) and the 11 assembly figures.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/cena_r13.py

Writes case/blender/build/:
  <group>__<colour>.ply   meshes in millimetres, FILE frame (x right, y = -SPEC y, z up, z = 0 at the main board's top), the same frame as out/r4_32_*.stl
  principal_full.glb, r8_full.glb   the two KiCad boards with the electronics' STEP models linked (kicad-cli, written beforehand; see render_r13.py header)
  manifest.json           files, glb instances (with their placement), the 32 keys (note names), the shots (groups shown, offsets, camera, anchors)
Faithful models used (STEP): EC11E18244AU (EasyEDA C202365), Gateron KS-20T (2021 STEP; pegs and stem cross redrawn from the 2023 Orange drawing),
SparkFun MicroMod Teensy, the 34 JLCPCB parts through the KiCad boards, the Adafruit 326 OLED (case_r4 mesh, read from Adafruit's board file).
Still primitives: Dayton CE28MB-8 and the 503450 cell (real dimensions), keycaps, SH cables, screws, nuts, feet, M2.5 nylon hardware.
"""
import json
import math
import os
import sys

import numpy as np
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_r4 as L          # noqa: E402
import oled_r11 as OL          # noqa: E402
import case as C3              # noqa: E402
import geometria as G          # noqa: E402
from stepcolor import read_step    # noqa: E402

BUILD = os.path.join(HERE, "blender", "build")
OUT = os.path.join(HERE, "out")
FORN = os.path.normpath(os.path.join(HERE, "..", "fornecimento"))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
ENC_STEP = os.path.join(FORN, "modelos3d", "C202365.step")
KS_STEP = os.path.join(FORN, "gateron", "KS-20T_20210922.stp")
MM_STEP = os.path.join(REPO, "etutti", "hardware", "student", "eTutti_3D.3dshapes", "SparkFun MicroMod Teensy Processor.step")
N = 32
ZR = L.ZR
CAP_TOP = 22.8            # cap head top above the seat, key up (case_t3g.CAP_TOP)
BOLT_LEN = {1: 10.0, 2: 12.0, 3: 14.0, 4: 16.0}
NUT_T = {1: 1.6, 2: 1.6, 3: 1.6, 4: 1.2}
PARTS = {}                # (group, "RRGGBB") -> [pv.PolyData]


def hexc(c):
    return "%02X%02X%02X" % tuple(int(round(max(0, min(1, v)) * 255)) for v in c)


def add(group, colour, mesh):
    if mesh is None or mesh.n_points == 0:
        return
    PARTS.setdefault((group, colour.lstrip("#").upper()), []).append(mesh.triangulate().clean())


def FY(y):
    return -y


def cyl(x, y, z0, z1, r, col, grp, res=40, cap=True):
    m = pv.Cylinder(center=(x, FY(y), (z0 + z1) / 2), direction=(0, 0, 1), radius=r, height=z1 - z0, resolution=res, capping=cap)
    add(grp, col, m)


def box(x0, y0, x1, y1, z0, z1, col, grp):
    add(grp, col, pv.Box(bounds=(min(x0, x1), max(x0, x1), FY(max(y0, y1)), FY(min(y0, y1)), z0, z1)))


def hexprism(x, y, z0, z1, af, col, grp, hole=1.0):
    r = af / math.sqrt(3.0)
    ring = pv.Polygon(center=(x, FY(y), z0), radius=r, normal=(0, 0, 1), n_sides=6)
    m = ring.extrude((0, 0, z1 - z0), capping=True)
    add(grp, col, m)


def tube(pts, r, col, grp, sides=10):
    pts = np.array(pts, float)
    if len(pts) < 2:
        return
    sp = pv.Spline(pts, max(30, len(pts) * 2)) if len(pts) > 2 else pv.Line(pts[0], pts[-1])
    add(grp, col, sp.tube(radius=r, n_sides=sides, capping=True))


def stl(name):
    return pv.read(os.path.join(OUT, "r4_32_%s.stl" % name))


# ------------------------------------------------------------------ STEP helpers
def step_mesh(parts, xf, group, flt=None, recol=None, ret=False):
    """parts from stepcolor.read_step; xf(V)->V in the file frame; flt(centroid_local)->bool keep; recol(local centroid, rgb)->hex. One mesh per colour.
    ret=True returns {colour: (V, T)} instead of adding to the scene."""
    acc = {}
    for V, T, c in parts:
        cen_l = V[T].mean(1)
        keep = np.ones(len(T), bool) if flt is None else np.array([flt(l) for l in cen_l])
        if not keep.any():
            continue
        Tk, ck = T[keep], cen_l[keep]
        cols = [hexc(c)] * len(Tk) if recol is None else [recol(l, c) for l in ck]
        for col in set(cols):
            sel = np.array([cc == col for cc in cols])
            acc.setdefault(col, []).append((V, Tk[sel]))
    res = {}
    for col, lst in acc.items():
        Vs, Ts, off = [], [], 0
        for V, T in lst:
            used, inv = np.unique(T, return_inverse=True)
            Vs.append(V[used])
            Ts.append(inv.reshape(-1, 3) + off)
            off += len(used)
        res[col] = (np.vstack(Vs), np.vstack(Ts))
    if ret:
        return res
    for col, (V, T) in res.items():
        faces = np.hstack([np.full((len(T), 1), 3), T]).ravel()
        add(group, col, pv.PolyData(xf(V), faces))


def rotz(V, deg):
    a = math.radians(deg)
    R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    return V @ R.T


# ------------------------------------------------------------------ keys and caps
CHECK = 3.0


def cap_mesh(kind):
    """Keycap, key up, at the origin, z relative to the seat: stem D5.6 into the cross, skirt D16.5, low dome D15.0 (rise 2.0). kind: white | black | cf."""
    zt = CAP_TOP
    r_dome, h_dome = 7.5, 2.0
    Rs = (r_dome ** 2 + h_dome ** 2) / (2 * h_dome)
    z_sk0, z_sk1, z_head = zt - 3.5, zt - 2.3, zt - h_dome
    prof = [(0.0, 11.8), (2.8, 11.8), (2.8, z_sk0), (7.9, z_sk0), (8.25, z_sk0 + 0.35), (8.25, z_sk1 - 0.3), (7.95, z_sk1), (r_dome, z_sk1 + 0.15), (r_dome, z_head)]
    for k in range(1, 25):
        t = k / 24.0
        rr = r_dome * (1 - t)
        prof.append((rr, z_head + math.sqrt(max(Rs ** 2 - rr ** 2, 0)) - (Rs - h_dome)))
    # revolve with many rings on the dome so the checker has smooth edges
    nseg = 96
    pts, faces = [], []
    for i, (r, z) in enumerate(prof):
        for j in range(nseg):
            a = 2 * math.pi * j / nseg
            pts.append((r * math.cos(a), r * math.sin(a), z))
    P = len(prof)
    for i in range(P - 1):
        for j in range(nseg):
            a, b = i * nseg + j, i * nseg + (j + 1) % nseg
            c, d = (i + 1) * nseg + (j + 1) % nseg, (i + 1) * nseg + j
            faces += [3, a, b, c, 3, a, c, d]
    m = pv.PolyData(np.array(pts), np.array(faces)).clean()
    m = m.compute_normals(auto_orient_normals=True, consistent_normals=True)
    m.clear_data()
    return m


def cap_groups(m, kind):
    """-> [(colour, mesh)]: for 'cf' the dome is split in diagonal checker cells (45 deg, 3 mm)."""
    if kind == "white":
        return [("F1ECE1", m)]
    if kind == "black":
        return [("1E1C1B", m)]
    t = m.triangulate()
    t = t.extract_cells(np.where(np.diff(t.GetPolys().GetOffsetsArray()) == 3)[0] if False else np.where(t.faces.reshape(-1, 4)[:, 0] == 3)[0]).extract_surface()
    sub = t
    cen = sub.cell_centers().points
    u = (cen[:, 0] + cen[:, 1]) / math.sqrt(2.0)
    v = (cen[:, 0] - cen[:, 1]) / math.sqrt(2.0)
    dome = cen[:, 2] > CAP_TOP - 2.0 - 0.05
    dark = dome & (((np.floor(u / CHECK) + np.floor(v / CHECK)) % 2) == 0)
    a = sub.extract_cells(np.where(~dark)[0]).extract_surface()
    b = sub.extract_cells(np.where(dark)[0]).extract_surface()
    return [("F1ECE1", a), ("1E1C1B", b)]


def keys_info():
    out = []
    for r, y, x0, n in L.ROWS:
        for i in range(n):
            nm = L.note_name(r, i)
            kind = "black" if "#" in nm else ("cf" if L.is_cf(nm) else "white")
            out.append({"row": r, "i": i, "x": x0 + i * L.PITCH, "y": y, "nome": nm, "tipo": kind})
    return out


def build_keys(KI):
    ks = read_step(KS_STEP)
    seat, cy = 0.85, 26.5
    caps = {k: cap_groups(cap_mesh(k), k) for k in ("white", "black", "cf")}

    def lower(l):
        return (l[2] - seat) > -0.6 and (l[2] - seat) < 11.12

    def recol(l, c):
        z = l[2] - seat
        if z < 5.1:
            return "2E2E30"
        return "C9C6BC"
    local = step_mesh(ks, None, None, flt=lower, recol=recol, ret=True)
    for k in KI:
        r, x, y = k["row"], k["x"], k["y"]
        z0 = ZR[r - 1]
        g = "tec_r%d" % r
        for col, (V, T) in local.items():
            W = V.copy()
            W[:, 0] += x
            W[:, 1] = -y + (V[:, 1] - cy)
            W[:, 2] += z0 - seat
            faces = np.hstack([np.full((len(T), 1), 3), T]).ravel()
            add(g, col, pv.PolyData(W, faces))
        # pegs (2 x D1.7 at +-5.08, through the ruler: 1.2 + 1.5 below the seat) and the stem cross (4.0 x 1.3 / 1.3 x 4.0, 2.7 above the collar)
        for dx in (-L.PEG_DX, L.PEG_DX):
            cyl(x + dx, y, z0 - 1.2 - L.PEG_BELOW, z0 + 0.1, L.PEG_D / 2, "2E2E30", g, res=16)
        box(x - 2.0, y - 0.65, x + 2.0, y + 0.65, z0 + 11.1, z0 + 13.8, "E8742A", g)
        box(x - 0.65, y - 2.0, x + 0.65, y + 2.0, z0 + 11.1, z0 + 13.8, "E8742A", g)
        for col, mesh in caps[k["tipo"]]:
            add("capa_r%d" % r, col, mesh.translate((x, -y, z0), inplace=False))


# ------------------------------------------------------------------ the rulers' bolts, nuts, grades
def build_bolts():
    for ru in L.rulers(0):
        r = ru["row"]
        z0 = ZR[r - 1]
        tip = z0 - BOLT_LEN[r]
        top = max(tip + NUT_T[r], L.Z_BOT + NUT_T[r] + 0.2)
        for mx, my in L.m2_points(ru):
            cyl(mx, my, tip, z0, 1.0, "B9BBBD", "par_r%d" % r, res=16)
            cyl(mx, my, z0, z0 + 1.6, 1.9, "B9BBBD", "par_r%d" % r, res=24)
            hexprism(mx, my, top - NUT_T[r], top, 4.0, "9A9C9E", "por_r%d" % r)


# ------------------------------------------------------------------ cables
WIRE_COLS = ["1B1B1B", "C8402A", "E3B23C", "3F7FD1", "2E8B57", "EDEDED"]


def build_cables():
    mouth = float(L.POS["metricas"]["mouth_x_fileiras"]["1"])
    for c in L.cables(0, L.CABLE_FREE_MM[1]):
        r = c["row"]
        pts = np.array(c["pts"])
        seg = np.hypot(*np.diff(pts, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        tot = s[-1]
        z_b = -L.T_PCB - 2.95 / 2
        z_r = ZR[r - 1] + L.AXIS_Z
        zf = L.Z_FLOOR + 0.9

        def sm(t):
            t = min(max(t, 0), 1)
            return t * t * (3 - 2 * t)
        zs = []
        for si in s:
            a = sm(1 - si / 9.0)
            b = sm(1 - (tot - si) / 9.0)
            z = zf + (z_b - zf) * a + (z_r - zf) * b
            zs.append(z)
        tan = np.gradient(pts, axis=0)
        tan /= np.linalg.norm(tan, axis=1)[:, None] + 1e-9
        nor = np.stack([-tan[:, 1], tan[:, 0]], 1)
        for i, col in enumerate(WIRE_COLS):
            off = (i - 2.5) * 0.9
            P = [(p[0] + nor[k, 0] * off, FY(p[1] + nor[k, 1] * off), zs[k]) for k, p in enumerate(pts)]
            tube(P[::2] + [P[-1]], 0.42, col, "cab_r%d" % r)
        # plug at the board's header (J60r, mouth to +x) and at the ruler's IN header (mouth to -y)
        x_back, y_row = pts[0]
        box(x_back - L.PLUG_D, y_row - L.PLUG_W / 2, x_back, y_row + L.PLUG_W / 2, z_b - L.PLUG_H / 2, z_b + L.PLUG_H / 2, "E9E4D6", "cab_r%d" % r)
        pin = L.plug_back_points([q for q in L.rulers(0) if q["row"] == r][0])["IN"]
        box(pin[0] - L.PLUG_W / 2, pin[1], pin[0] + L.PLUG_W / 2, pin[1] + L.PLUG_D, z_r - L.PLUG_H / 2, z_r + L.PLUG_H / 2, "E9E4D6", "cab_r%d" % r)
        # the end of the cable at the board, for the figure where the board is not yet over the tray (step 9): a short stub with the plug
        P0 = [(x_back + 0.0 + t, FY(y_row), z_b) for t in np.linspace(0, 22, 12)]
        for i, col in enumerate(WIRE_COLS):
            off = (i - 2.5) * 0.9
            tube([(p[0], p[1] - off * -1, p[2] - 0.0) for p in P0], 0.42, col, "pta_r%d" % r)
        box(x_back - L.PLUG_D, y_row - L.PLUG_W / 2, x_back, y_row + L.PLUG_W / 2, z_b - L.PLUG_H / 2, z_b + L.PLUG_H / 2, "E9E4D6", "pta_r%d" % r)


def build_qwiic():
    """OLED right-hand connector (the module's back, 4-pin plug) -> J401 (SH-4 on the board's underside) through the board's slit: an S of four wires."""
    lv = OL.levels(L.CEILING)
    pl = [b for b in OL.conn_boxes_b() if b[0] == "plugue right"][0]
    (xa, ya), (xb, yb) = OL.world(pl[1], pl[3]), OL.world(pl[2], pl[4])
    px, py = (xa + xb) / 2, (ya + yb) / 2
    z_p = lv["pcb_bottom"] + (pl[5] + pl[6]) / 2
    box(min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb), lv["pcb_bottom"] + pl[5], lv["pcb_bottom"] + pl[6], "E9E4D6", "qwiic")
    j = L.P["J401"]
    jx, jy = j["x"], j["y"] + 5.0
    z_j = -L.T_PCB - 1.45
    sx0, sy0, sx1, sy1 = L.SLIT
    mid = ((sx0 + sx1) / 2, (sy0 + sy1) / 2)
    box(jx - 2.5, jy - 0.0, jx + 2.5, jy + 2.4, z_j - 1.8, z_j + 1.8, "E9E4D6", "qwiic")
    cols = ["1B1B1B", "C8402A", "3F7FD1", "E3B23C"]
    for i, col in enumerate(cols):
        o = (i - 1.5) * 1.0
        path = [(px + o, py, z_p), (px + o, py + 4.0, z_p - 2.0), (mid[0] + o, mid[1] + 2.0, 3.0), (mid[0] + o, mid[1], -2.0),
                (jx + o * 0.9, jy + 0.0, z_j + 0.0)]
        tube([(p[0], FY(p[1]), p[2]) for p in path], 0.4, col, "qwiic")


# ------------------------------------------------------------------ interface parts
def build_interface(KI):
    # encoders: EC11E18244AU (EasyEDA STEP): shaft centre = footprint origin + (7.5, 2.5); legs rotated -90 deg to the footprint's pads
    enc = read_step(ENC_STEP)
    for x, y in L.KNOBS:
        def xf(V, x=x, y=y):
            W = rotz(V, -90.0)
            W[:, 0] += x
            W[:, 1] += FY(y)
            return W
        step_mesh(enc, xf, "encoders")
    # MicroMod Teensy: fingers to the M.2 (x 20), notch on H101, chips down (see FIT_CHECK R13V4), PCB 2.5 mm under the board
    mm = read_step(MM_STEP)
    hx, hy = L.H101
    z0 = -L.T_PCB - 2.5

    def xm(V):
        W = np.empty_like(V)
        W[:, 0] = 20.0 + V[:, 1]
        W[:, 1] = V[:, 0] - 29.0
        W[:, 2] = z0 - V[:, 2]
        return W

    def mrecol(l, c):
        return hexc(c) if tuple(round(v, 2) for v in c) != (0.6, 0.6, 0.6) else "A9ABAD"
    step_mesh(mm, xm, "modulo", recol=mrecol)
    # M2.5 nylon: screw from above, spacer 2.5 between the board and the module, nut under the module
    cyl(hx, hy, 0.0, 1.4, 2.3, "EAE4D2", "m25_parafuso", res=32)
    cyl(hx, hy, z0 - 1.6, 0.0, 1.25, "EAE4D2", "m25_parafuso", res=24)
    cyl(hx, hy, z0 + 0.0, -L.T_PCB, 2.5, "EAE4D2", "m25_espacador", res=32)
    hexprism(hx, hy, z0 - 3.2, z0 - 3.2 + 2.0, 5.0, "EAE4D2", "m25_porca")
    # lid screws (thread-forming M2 from below: H1..H4, the 5 interior posts and the 6 wall posts); the posts' lower ends are probed on the lid mesh
    lid = stl("tampa")
    info = {}
    for tag, lst in (("H", L.LID_POSTS), ("P", L.pick_posts(0)), ("W", L.wall_posts(0))):
        for x, y in lst:
            pt, _ = lid.ray_trace((x, FY(y), L.Z_FLOOR), (x, FY(y), 30))
            ztop = float(pt[:, 2].min()) if len(pt) else 6.0
            tip = (6.0 if tag == "H" else ztop + 6.0)
            head = L.Z_BOT + (2.2 if tag == "H" else 1.0)
            cyl(x, y, head, tip, 1.0, "B9BBBD", "parafusos_base", res=16)
            cyl(x, y, head - 1.4, head, 1.9, "B9BBBD", "parafusos_base", res=24)
            info["%s(%.1f;%.1f)" % (tag, x, y)] = round(tip - (head - 1.4), 1)
    # battery 503450 (5 x 34 x 50), wires towards J202
    bx0, by0 = L.BATTERY_XY
    bw, bl, bt = L.BATTERY_CELL
    z0b = L.Z_FLOOR
    box(bx0, by0, bx0 + bw, by0 + bl, z0b, z0b + bt, "6B8DB3", "bateria")
    box(bx0 + 3, by0 + 8, bx0 + bw - 3, by0 + bl - 8, z0b + bt, z0b + bt + 0.05, "E9E4D6", "bateria")        # the label
    box(bx0 + 7, by0 - 3.0, bx0 + 12, by0, z0b + 1.0, z0b + 4.0, "D9D5CC", "bateria")                     # the protection board
    j2 = L.P["J202"]
    jx, jy = j2["x"], j2["y"]
    zj = -L.T_PCB - 3.0
    for i, col in enumerate(["C8402A", "E3B23C", "1B1B1B"]):
        o = (i - 1) * 2.0
        tube([(bx0 + 9.5 + (i - 1) * 1.2, FY(by0 - 3.0), z0b + 2.5), (bx0 + 9.5 + (i - 1) * 1.2, FY(by0 - 9), z0b + 2.5), (jx + o * 0.6, FY(jy + 3), zj - 0.5), (jx + o * 0.6, FY(jy + 0.5), zj)], 0.45, col, "bateria")
    # speaker Dayton CE28MB-8: D28 x 4.5, black frame, grey cone, dust cap; wires to J501 (top of the board)
    sx, sy = L.SPEAKER
    lv = C3.box_levels()
    zb, zf = lv["back"], lv["front"]
    speaker_parts(sx, sy, zb, zf)
    j5 = L.P["J501"]
    for i, (col, dx) in enumerate((("C8402A", -1.4), ("1B1B1B", 1.4))):
        tube([(j5["x"] + dx, FY(j5["y"]), 0.6), (j5["x"] + dx, FY(j5["y"] - 4), 4.0), (sx + 11 + dx * 0.3, FY(sy + 8 + dx), zb + 1.0), (sx + 11, FY(sy + 8 + dx), zb)], 0.35, col, "fios")
    for i, (col, dx) in enumerate((("C8402A", -1.4), ("1B1B1B", 1.4))):          # step 2: the speaker is 50 mm above its place; the wires follow it
        tube([(j5["x"] + dx, FY(j5["y"]), 0.6), (j5["x"] + dx, FY(j5["y"] - 6), 14.0), (sx + 11 + dx * 0.3, FY(sy + 8 + dx), zb + 50 + 3.0), (sx + 11, FY(sy + 8 + dx), zb + 50)], 0.35, col, "fios2")
    return info


def speaker_parts(x, y, zb, zf):
    def rev(prof, col, grp, off=(0, 0, 0)):
        pts = []
        faces = []
        ns = 64
        for r, z in prof:
            for j in range(ns):
                a = 2 * math.pi * j / ns
                pts.append((x + r * math.cos(a), FY(y) + r * math.sin(a), z))
        for i in range(len(prof) - 1):
            for j in range(ns):
                a, b = i * ns + j, i * ns + (j + 1) % ns
                c, d = (i + 1) * ns + (j + 1) % ns, (i + 1) * ns + j
                faces += [3, a, b, c, 3, a, c, d]
        m = pv.PolyData(np.array(pts), np.array(faces)).clean()
        add(grp, col, m)
    H = zf - zb
    rev([(14.0, zb), (14.0, zf), (12.0, zf), (12.0, zf - 0.4)], "1D1D1F", "alto_falante")                 # frame ring
    rev([(12.0, zf - 0.4), (9.5, zf - 1.0), (5.0, zf - 1.8), (4.8, zf - 1.8), (0.0, zf - 1.8)], "3A3835", "alto_falante")   # cone
    rev([(4.8, zf - 1.8), (4.8, zf - 1.2), (3.0, zf - 0.9), (0.0, zf - 0.8)], "55524D", "alto_falante")       # dust cap
    rev([(14.0, zb), (0.0, zb)], "1D1D1F", "alto_falante")
    rev([(10.0, zb), (10.0, zb - 0.3), (0.0, zb - 0.3)], "9A9C9E", "alto_falante")                            # magnet cup, back


def build_feet():
    """R15V4: the 8 feet 3M Bumpon SJ5302 (D 7.94 x 2.2, hemispherical: a cylinder with a rounded top here) at the positions of case/pes_r15.py."""
    chosen = [tuple(p) for p in json.load(open(os.path.join(OUT, "pes_r15.json")))["pos_xy"]]
    for x, y in chosen:
        cyl(x, y, L.Z_BOT - 2.2, L.Z_BOT - 0.8, 3.97, "1E1E1E", "pes", res=40)
        cyl(x, y, L.Z_BOT - 0.8, L.Z_BOT, 3.97, "1E1E1E", "pes", res=40)
    return chosen


def build_misc():
    # smoked pane in the window's ledge
    wx0, wy0, wx1, wy1 = C3.WINDOW
    ld, t = C3.WINDOW_LEDGE, C3.WINDOW_PANE_T
    box(wx0 - ld + 0.1, wy0 - ld + 0.1, wx1 + ld - 0.1, wy1 + ld - 0.1, L.CEILING + 0.02, L.CEILING + t, "141312", "janela")
    # panel tabs (step 1): three mouse-bite tabs between the two rulers of a panel (drawn in render_r13 at the panel's position)


def build_oled():
    m = stl("OLED")
    lv = OL.levels(L.CEILING)
    cen = m.cell_centers().points
    top = cen[:, 2] > lv["pcb_top"] + 0.05
    add("oled", "0B0B0A", m.extract_cells(np.where(top)[0]).extract_surface())
    add("oled", "1B4F8A", m.extract_cells(np.where(~top)[0]).extract_surface())
    # viewing area (what lights up)
    wx0, wy0, wx1, wy1 = C3.WINDOW
    cx, cy = (wx0 + wx1) / 2, (wy0 + wy1) / 2
    ax, ay = OL.ACT_X[1] - OL.ACT_X[0], OL.ACT_Y[1] - OL.ACT_Y[0]
    box(cx - ax / 2, cy - ay / 2, cx + ax / 2, cy + ay / 2, lv["glass_top"] - 0.05, lv["glass_top"] + 0.01, "101010", "oled")


def main():
    os.makedirs(BUILD, exist_ok=True)
    KI = keys_info()
    for g, f in (("tampa", "tampa"), ("base", "base"), ("grades", "grades"), ("caixa", "caixa_acustica"), ("knobs", "knob_1")):
        pass
    add("tampa", "E8DEC6", stl("tampa"))
    add("base", "9C9B96", stl("base"))
    for ru in L.rulers(0):
        pass
    g = stl("grades")
    for ru in L.rulers(0):          # one grade strip per row: split the merged mesh by row (y band)
        y0, y1 = FY(ru["y"] + 8.2), FY(ru["y"] - 8.2)
        cen = g.cell_centers().points
        sel = (cen[:, 1] > y0) & (cen[:, 1] < y1)
        add("gra_r%d" % ru["row"], "1C1B1A", g.extract_cells(np.where(sel)[0]).extract_surface())
    add("caixa", "7A746A", stl("caixa_acustica"))
    for i, (x, y) in enumerate(L.KNOBS):
        add("knobs", "1E1C1B", stl("knob_%d" % (i + 1)))
    build_oled()
    build_keys(KI)
    build_bolts()
    build_cables()
    build_qwiic()
    info = build_interface(KI)
    feet = build_feet()
    build_misc()
    files = []
    for (grp, col), meshes in sorted(PARTS.items()):
        mm = meshes[0] if len(meshes) == 1 else pv.merge(meshes, merge_points=False)
        mm = mm.triangulate()
        mm.clear_data()
        name = "%s__%s.ply" % (grp, col)
        mm.save(os.path.join(BUILD, name), binary=True)
        files.append({"file": name, "group": grp, "colour": col})
    wx0, wy0, wx1, wy1 = C3.WINDOW
    lvo = OL.levels(L.CEILING)
    tela = {"cx": (wx0 + wx1) / 2, "cy_file": -(wy0 + wy1) / 2, "z": lvo["glass_top"] + 0.03, "w": OL.ACT_X[1] - OL.ACT_X[0], "h": OL.ACT_Y[1] - OL.ACT_Y[0]}
    man = {"files": files, "keys": KI, "feet": feet, "lid_screws_mm": info, "tela": tela,
           "rulers": [{"row": r["row"], "x0": r["x0"], "y": r["y"]} for r in L.rulers(0)]}
    json.dump(man, open(os.path.join(BUILD, "manifest_parts.json"), "w"), indent=1)
    print(len(files), "mesh files;", "lid screws:", info, "feet:", feet)


if __name__ == "__main__":
    main()
