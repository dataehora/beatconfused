"""R15V4 item 5: detailed line drawings of the BASE (tray) alone: front-left isometric, back-right isometric, top view and a hidden-lines view, with the numbered
supports, the position of every key (with the note name) on its rails, and a legend that says what each number carries.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/iso_base_r15.py [--fast]
      -> case/renders/iso_base_r15_frente_esq.png, iso_base_r15_tras_dir.png, iso_base_r15_topo.png, iso_base_r15_ocultas.png (large PNGs, 300 dpi)
         and iso_base_r15.pdf (vector, one page per view; the legend is in the same page)

The edges are exact: OpenCascade's hidden-line removal (HLRBRep) over the real tray solid of case_r4.py, written as polylines. The solid is mirrored in y
(y_plot = -y_model: the SPEC frame is left-handed, y towards the player) so the pictures are not mirrored. Badges: a solid circle = the support is visible from that viewpoint;
a dashed circle = it is behind another wall (a ray from the camera hits the tray first).
"""
import json
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Circle, Polygon        # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case_r4 as R      # noqa: E402
import layout_r4 as L    # noqa: E402

from OCP.BRepAdaptor import BRepAdaptor_Curve                 # noqa: E402
from OCP.GCPnts import GCPnts_QuasiUniformDeflection          # noqa: E402
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir                      # noqa: E402
from OCP.HLRAlgo import HLRAlgo_Projector                      # noqa: E402
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape       # noqa: E402
from OCP.TopAbs import TopAbs_EDGE                             # noqa: E402
from OCP.TopExp import TopExp_Explorer                         # noqa: E402
from OCP.TopoDS import TopoDS                                  # noqa: E402

REN = os.path.join(HERE, "renders")
FAST = "--fast" in sys.argv
ROWCOL = {1: "#C2410C", 2: "#1D4ED8", 3: "#15803D", 4: "#7E22CE"}
GROUPCOL = {"berço": "#1D4ED8", "riser": "#B91C1C", "ponta": "#A16207", "bossa": "#15803D",
            "poste": "#7C2D12", "parede": "#9A3412", "tunel": "#BE185D", "interface": "#374151"}


# ------------------------------------------------------------------ the supports (3D anchors in the MODEL frame, then y -> -y)
def key_cover(row, x0, x1):
    """Names of the keys of `row` whose 14 mm housing overlaps the x interval [x0, x1]."""
    r, y, xs, n = [q for q in L.ROWS if q[0] == row][0]
    idx = [i for i in range(n) if xs + i * L.PITCH + 7.0 > x0 and xs + i * L.PITCH - 7.0 < x1]
    if not idx:
        return "(nenhuma)"
    return "%s ... %s" % (L.note_name(row, idx[0]), L.note_name(row, idx[-1])) if len(idx) > 1 else L.note_name(row, idx[0])


def supports():
    """List of dicts: n (number), grupo, nome, apoia (text), anchor (x, y, z model frame), outlines (list of 3D polygons to highlight)."""
    S = []
    rails = L.rail_rects(0)
    rul = {q["row"]: q for q in L.rulers(0)}

    def add(grupo, nome, apoia, anchor, polys=()):
        S.append({"n": len(S) + 1, "grupo": grupo, "nome": nome, "apoia": apoia, "anchor": anchor, "polys": list(polys)})

    def rect(x0, x1, y0, y1, z):
        return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    for r in (1, 2, 3, 4):                                                    # R15V4: ONE continuous cradle per ruler (full width, pockets only for the parts under it)
        y = rul[r]["y"]
        zt = L.ZR[r - 1] - L.RULER_T
        xa, xb = rul[r]["x0"] + 0.2, rul[r]["x0"] + L.RULER_L - 0.2
        add("berço", "berço contínuo da fileira %d" % r, "face de baixo da régua R%d (14 mm de largura, 147,6 de comprimento), z %.1f; apoio em ~86 %% da área, bolsos de 0,3 mm de folga para sensores, 595, capacitores e J1; teclas %s" % (r, zt, key_cover(r, xa, xb)),
            ((xa + xb) / 2 - 10.0, y + 2.0, zt), [rect(xa, xb, y - L.RULER_W / 2, y + L.RULER_W / 2, zt)])
    for r in (1, 2, 3, 4):
        q = rul[r]
        xa, xb, y = q["x0"] + 0.2, q["x0"] + L.RULER_L - 0.2, q["y"]
        if r > 1:
            yn = L.ROWS[r - 2][1]
            zt = L.ZR[r - 2] - L.RULER_T
            add("riser", "riser (parede cheia) da fileira %d" % r, "fecha o degrau entre o trilho da frente da fileira %d e o trilho de trás da fileira %d, até z %.1f; trava os dois trilhos e a frente da régua R%d" % (r, r - 1, zt, r),
                ((xa + xb) / 2 + 20, (y + L.RAIL_OUT + yn - L.RAIL_OUT) / 2, zt), [rect(xa, xb, y + L.RAIL_OUT, yn - L.RAIL_OUT, zt)])
        else:
            zt = L.ZR[0] - L.RULER_T
            add("riser", "parede da frente (2 mm mais grossa) da fileira 1", "fecha a frente do degrau da fileira 1 até z %.1f; trava o trilho da frente da R1" % zt,
                ((xa + xb) / 2 + 20, y + L.RAIL_OUT + 1.0, zt), [rect(xa, xb, y + L.RAIL_OUT, y + L.RAIL_OUT + 2.0, zt)])
    for r in (1, 2, 3, 4):
        q = rul[r]
        xa, xb, y = q["x0"] + 0.2, q["x0"] + L.RULER_L - 0.2, q["y"]
        zt = L.ZR[r - 1] - L.RULER_T
        add("ponta", "parede de ponta esquerda, fileira %d" % r, "fecha a ponta esquerda do degrau (x %.1f..%.1f) da R%d; segura as pontas dos trilhos, com recorte para o cabeçalho IN" % (xa, xa + 2, r), (xa + 1.0, y, zt),
            [rect(xa, xa + 2.0, y - L.RAIL_OUT, y + L.RAIL_OUT, zt)])
        add("ponta", "parede de ponta direita, fileira %d" % r, "fecha a ponta direita (x %.1f..%.1f) da R%d (sem OUT na R8)" % (xb - 2, xb, r), (xb - 1.0, y, zt),
            [rect(xb - 2.0, xb, y - L.RAIL_OUT, y + L.RAIL_OUT, zt)])
    for r in (1, 2, 3, 4):
        q = rul[r]
        for mx, my in L.m2_points(q):
            zt = L.ZR[r - 1] - L.RULER_T
            add("bossa", "bossa M2 da régua R%d, u %.1f" % (r, mx - q["x0"]), "parafuso passante M2 x %g + porca (bolso sextavado por baixo, 3 costelas de pressão); prende a R%d (D6, furo D2,4)" % (R.BOLT_LEN[r], r), (mx, my, zt),
                [[(mx + 3.0 * math.cos(a / 12 * 2 * math.pi), my + 3.0 * math.sin(a / 12 * 2 * math.pi), zt) for a in range(12)]])
    for px, py in L.pick_posts(0):
        r = [k for k in (1, 2, 3) if abs(py - (L.ROWS[k - 1][1] - L.ROWP / 3.0)) < 0.05][0]
        add("poste", "poste interno (%.1f; %.1f)" % (px, py), "a ponta de baixo do poste da tampa pousa aqui (entre as fileiras %d e %d); parafuso PT M2 x 8 por baixo, furo D2,4 no piso" % (r, r + 1), (px, py, L.Z_FLOOR),
            [[(px + 2.7 * math.cos(a / 12 * 2 * math.pi), py + 2.7 * math.sin(a / 12 * 2 * math.pi), L.Z_FLOOR) for a in range(12)]])
    for px, py in L.wall_posts(0):
        add("parede", "poste de parede (%.1f; %.1f)" % (px, py), "bossa D6 da tampa pousa aqui, junto da parede %s; parafuso PT M2 x 8" % ("de trás" if py < 50 else "da frente"), (px, py, L.Z_FLOOR),
            [[(px + 3.0 * math.cos(a / 12 * 2 * math.pi), py + 3.0 * math.sin(a / 12 * 2 * math.pi), L.Z_FLOOR) for a in range(12)]])
    for k in ("H1", "H2", "H3", "H4"):
        hx, hy = L.HOLES[k]
        add("bossa", "bossa D6 da placa principal, %s (%.1f; %.1f)" % (k, hx, hy), "sobe até a face de baixo da placa (z %.1f); parafuso PT M2 x 16 do fundo, atravessa a placa e entra no poste da tampa" % (-L.T_PCB), (hx, hy, -L.T_PCB),
            [[(hx + 3.0 * math.cos(a / 12 * 2 * math.pi), hy + 3.0 * math.sin(a / 12 * 2 * math.pi), -L.T_PCB) for a in range(12)]])
    for r in (1, 2, 3, 4):
        mouth = float(L.POS["metricas"]["mouth_x_fileiras"][str(r)])
        q = rul[r]
        add("tunel", "túnel do cabo da placa, fileira %d" % r, "passa o cabo J60%d -> IN da R%d (feixe 5,6 + 0,8 mm) por baixo da régua, do piso até o eixo do plugue; recorta riser, ponta e trilhos" % (r, r),
            ((mouth + q["x0"] + L.IN_X) / 2 - 2.0, q["y"] - 10.0, L.Z_FLOOR))
    bx0, by0 = L.BATTERY_XY
    add("interface", "berço da bateria", "nervuras de 2,0 mm: atrás e nas duas pontas da bateria 503450 (34 x 50 x 5); a frente fica aberta para o fio", (bx0 + 17.0, by0 + 50.8, L.Z_FLOOR + 2.0))
    add("interface", "furo do botão PROG", "Ø3 mm no piso, para apertar o SW403 por baixo", (L.PROG[0], L.PROG[1], L.Z_FLOOR))
    add("interface", "rebaixo do parafuso do módulo (H101)", "Ø8 mm no piso sob o M.2 (cabeça do M2,5 e espaçador)", (L.H101[0], L.H101[1], L.Z_FLOOR))
    import json as _j
    for i, (fx, fy) in enumerate(_j.load(open(os.path.join(HERE, "out", "pes_r15.json")))["pos_xy"], start=1):
        add("interface", "pé adesivo %d (%d; %d)" % (i, fx, fy), "pé 3M Bumpon SJ5302 (Ø7,94 x 2,2) colado na face de baixo; a 9 mm ou mais de qualquer furo ou bolso", (fx, fy, L.Z_BOT))
    return S


# ------------------------------------------------------------------ geometry helpers
def mirror_pt(p):
    return (p[0], -p[1], p[2])


def basis(elev, azim):
    if elev >= 89.9:
        return np.array([0, 0, 1.0]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0])
    E, A = math.radians(elev), math.radians(azim)
    d = np.array([-math.cos(E) * math.sin(A), -math.cos(E) * math.cos(A), math.sin(E)])
    right = np.array([-d[1], d[0], 0.0])
    right /= np.linalg.norm(right)
    up = np.cross(d, right)
    return d, right, up


def hlr_edges(shape, d, right, up, defl=0.05):
    ax2 = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*d), gp_Dir(*right))
    algo = HLRBRep_Algo()
    algo.Add(shape)
    algo.Projector(HLRAlgo_Projector(ax2))
    algo.Update()
    algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    out = {"visivel": [], "oculto": []}
    for key, getters in (("visivel", (h.VCompound, h.Rg1LineVCompound, h.OutLineVCompound)), ("oculto", (h.HCompound, h.Rg1LineHCompound, h.OutLineHCompound))):
        for g in getters:
            try:
                comp = g()
            except Exception:
                continue
            if comp is None or comp.IsNull():
                continue
            ex = TopExp_Explorer(comp, TopAbs_EDGE)
            while ex.More():
                e = TopoDS.Edge_s(ex.Current())
                try:
                    c = BRepAdaptor_Curve(e)
                    q = GCPnts_QuasiUniformDeflection(c, defl)
                    pts = [(c.Value(q.Parameter(i + 1)).X(), c.Value(q.Parameter(i + 1)).Y()) for i in range(q.NbPoints())] if q.IsDone() else []
                except Exception:
                    pts = []
                if len(pts) >= 2:
                    out[key].append(pts)
                ex.Next()
    return out


def proj2(p, right, up):
    p = np.array(p, float)
    return float(p @ right), float(p @ up)


def hlr_check(d, right, up):
    """The HLR output frame must equal (x = p . right, y = p . up): checked on a unit cube's corner."""
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
    box = BRepPrimAPI_MakeBox(1, 2, 3).Shape()
    e = hlr_edges(box, d, right, up)["visivel"]
    xs = [p[0] for l in e for p in l]
    ys = [p[1] for l in e for p in l]
    corners = [(a, b, c) for a in (0, 1) for b in (0, 2) for c in (0, 3)]
    px = [proj2(c, right, up) for c in corners]
    return abs(max(xs) - max(p[0] for p in px)) < 1e-6 and abs(max(ys) - max(p[1] for p in px)) < 1e-6 and abs(min(xs) - min(p[0] for p in px)) < 1e-6 and abs(min(ys) - min(p[1] for p in px)) < 1e-6


# ------------------------------------------------------------------ visibility by ray casting
def make_mesh(solid):
    import pyvista as pv
    vs, tris = solid.val().tessellate(0.1, 0.4)
    pts = np.array([(p.x, p.y, p.z) for p in vs])
    faces = np.hstack([np.full((len(tris), 1), 3), np.array(tris)]).astype(np.int64).ravel()
    return pv.PolyData(pts, faces)


def visible(mesh, p, d, far=600.0):
    p = np.array(p, float)
    start = p + d * 0.15
    try:
        pts, _ = mesh.ray_trace(start, p + d * far)
    except Exception:
        return True
    return len(pts) == 0


# ------------------------------------------------------------------ drawing
def draw_view(ax, name, elev, azim, shape_m, mesh_m, sup, hidden_view=False):
    d, right, up = basis(elev, azim)
    ed = hlr_edges(shape_m, d, right, up)
    if not hidden_view:
        for l in ed["visivel"]:
            xs, ys = zip(*l)
            ax.plot(xs, ys, color="#111111", lw=0.45, solid_capstyle="round", zorder=5)
    else:
        for l in ed["oculto"]:
            xs, ys = zip(*l)
            ax.plot(xs, ys, color="#6B7280", lw=0.35, ls=(0, (3, 2)), zorder=4)
        for l in ed["visivel"]:
            xs, ys = zip(*l)
            ax.plot(xs, ys, color="#111111", lw=0.5, zorder=5)
    # the keys: 14 x 14 housings on the rail plane, with the note's name
    for r, y, x0, n in L.ROWS:
        zt = L.ZR[r - 1] - L.RULER_T + 0.02
        for i in range(n):
            x = x0 + i * L.PITCH
            nm = L.note_name(r, i)
            cf = L.is_cf(nm)
            corners = [mirror_pt((x + dx, y + dy, zt)) for dx, dy in ((-7, -7), (7, -7), (7, 7), (-7, 7))]
            cen = mirror_pt((x, y, zt))
            if not visible(mesh_m, cen, d):
                continue
            ax.add_patch(Polygon([proj2(c, right, up) for c in corners], closed=True, fc="#FDE047" if cf else "none", ec="#374151", lw=0.35, alpha=0.55 if cf else 1.0, zorder=6, ls=":"))
            cx, cy = proj2(cen, right, up)
            ax.text(cx, cy, nm, fontsize=5.0 if elev < 89 else 6.0, ha="center", va="center", color="#111111", fontweight="bold" if cf else "normal", zorder=9)
    # highlights and badges
    for s in sup:
        col = GROUPCOL[s["grupo"]]
        a = mirror_pt(s["anchor"])
        vis = visible(mesh_m, a, d)
        if vis:
            for poly in s["polys"]:
                pts = [proj2(mirror_pt(p), right, up) for p in poly]
                ax.add_patch(Polygon(pts, closed=True, fc=col, ec=col, lw=0.4, alpha=0.38, zorder=3))
        bx, by = proj2(a, right, up)
        ax.add_patch(Circle((bx, by), 1.5 if elev >= 89 else 1.7, fc=col if vis else "white", ec=col, lw=0.9, ls="-" if vis else (0, (2, 1)), zorder=10))
        ax.text(bx, by, str(s["n"]), fontsize=4.2, color="white" if vis else col, ha="center", va="center", fontweight="bold", zorder=11)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.autoscale_view()


def legend_text(sup):
    lines = []
    for g in ("trilho de trás", "trilho da frente", "riser", "ponta", "bossa", "poste", "parede", "tunel", "interface"):
        pass
    for s in sup:
        lines.append((s["n"], s["grupo"], s["nome"], s["apoia"]))
    return lines


def page(title, elev, azim, shape_m, mesh_m, sup, hidden_view=False, figsize=(26, 21)):
    fig = plt.figure(figsize=figsize)
    top = 0.40 if elev < 89 else 0.30
    ax = fig.add_axes([0.0, top, 1.0, 1.0 - top - 0.03])
    draw_view(ax, title, elev, azim, shape_m, mesh_m, sup, hidden_view)
    fig.suptitle(title, x=0.5, y=0.995, fontsize=13)
    n = len(sup)
    half = (n + 1) // 2
    for col in range(2):
        tx = fig.add_axes([0.01 + 0.5 * col, 0.0, 0.48, top - 0.01])
        tx.axis("off")
        if col == 0:
            tx.text(0.0, 1.0, "Legenda: o que cada número apoia (SPEC R15V4 item 5)", fontsize=9, fontweight="bold", va="top", transform=tx.transAxes)
        y = 0.97
        dy = 0.94 / (half + 3)
        for s in sup[col * half:(col + 1) * half]:
            y -= dy
            c = GROUPCOL[s["grupo"]]
            tx.add_patch(Circle((0.008, y), 0.0065, fc=c, ec=c, transform=tx.transAxes, clip_on=False))
            tx.text(0.008, y, str(s["n"]), fontsize=5.6, color="white", ha="center", va="center", fontweight="bold", transform=tx.transAxes)
            txt = s["nome"] + " - " + s["apoia"]
            if len(txt) > 150:
                txt = txt[:148] + "..."
            tx.text(0.02, y, txt, fontsize=5.6, va="center", transform=tx.transAxes)
        if col == 1:
            tx.text(0.0, 0.0, "Chave: círculo cheio = apoio visível neste ponto de vista; tracejado = atrás de outra parede. Quadrados pontilhados = carcaça de cada tecla (14 x 14) sobre o trilho,"
                    "com o nome da nota (C e F em amarelo). Linhas pretas = arestas visíveis exatas (HLR do OpenCascade); cinza tracejado = ocultas (só na vista de linhas ocultas).",
                    fontsize=6.2, va="bottom", transform=tx.transAxes)
    return fig


def main():
    import cadquery as cq
    tray_m = cq.Workplane("XY").add(cq.importers.importStep(os.path.join(R.OUT, "r4_32_base.step")).val())      # the STEP written by case_r4.py is already mirrored in y (file frame)
    shape_m = tray_m.val().wrapped
    mesh_m = make_mesh(tray_m)
    sup = supports()
    json.dump([{k: v for k, v in s.items() if k != "polys"} for s in sup], open(os.path.join(R.OUT, "iso_base_r15_apoios.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    d, right, up = basis(35.0, 45.0)
    print("HLR frame check:", hlr_check(d, right, up), flush=True)
    views = [("iso_base_r15_frente_esq", "Base (bandeja) sozinha, isométrico frente-esquerda (R15V4): arestas, apoios numerados e teclas com o nome da nota", 35.0, 45.0, False),
             ("iso_base_r15_tras_dir", "Base sozinha, isométrico trás-direita (R15V4)", 35.0, 225.0, False),
             ("iso_base_r15_topo", "Base sozinha, vista de cima (R15V4): o jogador está embaixo", 90.0, 0.0, False),
             ("iso_base_r15_ocultas", "Base sozinha, isométrico frente-esquerda com as arestas OCULTAS tracejadas (R15V4)", 35.0, 45.0, True)]
    if FAST:
        views = views[:1]
    pdf = PdfPages(os.path.join(REN, "iso_base_r15.pdf"))
    for fn, title, e, a, hid in views:
        fig = page(title, e, a, shape_m, mesh_m, sup, hid)
        fig.savefig(os.path.join(REN, fn + ".png"), dpi=200 if FAST else 300)
        pdf.savefig(fig)
        plt.close(fig)
        print(fn, "ok", flush=True)
    pdf.close()


if __name__ == "__main__":
    main()
