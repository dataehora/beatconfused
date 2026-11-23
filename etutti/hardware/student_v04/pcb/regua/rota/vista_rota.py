"""Vista (topo e fundo) das reguas roteadas: PNG por camada, com trechos ampliados.
Uso (python do KiCad): python vista_rota.py placa.kicad_pcb prefixo [x0 x1] [escala]
Cores: trilhas por rede; pads cinza-azulado; vias com furo; furos e entalhes pretos."""
import os
import sys
import pcbnew
from PIL import Image, ImageDraw, ImageFont

COL = {"OUT": (220, 40, 40), "+3V3": (230, 140, 0), "GND": (60, 120, 220), "CLK": (40, 160, 60), "SER": (150, 60, 190),
       "QHP": (0, 160, 170), "QHP_J": (0, 120, 130)}
for k in range(1, 9):
    COL["EN%d" % k] = [(180, 80, 20), (200, 30, 120), (90, 90, 30), (30, 90, 160), (160, 110, 190), (20, 130, 90), (120, 60, 60), (70, 70, 70)][k - 1]


def mm(v):
    return pcbnew.ToMM(v)


def render(path, out, xa=None, xb=None, sc=16, layer="B"):
    b = pcbnew.LoadBoard(path)
    bb = b.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = mm(bb.GetX()) - 0.5, mm(bb.GetY()) - 0.5, mm(bb.GetX() + bb.GetWidth()) + 0.5, mm(bb.GetY() + bb.GetHeight()) + 0.5
    if xa is not None:
        x0, x1 = xa + 10, xb + 10
    W, H = int((x1 - x0) * sc), int((y1 - y0) * sc)
    L = pcbnew.B_Cu if layer == "B" else pcbnew.F_Cu
    img = Image.new("RGB", (W, H), (250, 250, 245))
    d = ImageDraw.Draw(img, "RGBA")

    def P(x, y):
        # fundo: espelha em x (vista de baixo)
        px = (x - x0) * sc
        if layer == "B" and os.environ.get("ESPELHA") == "1":
            px = W - px
        return px, (y - y0) * sc

    # zonas preenchidas
    for z in b.Zones():
        if z.GetIsRuleArea():
            bbz = z.GetBoundingBox()
            if z.IsOnLayer(L):
                a, c = P(mm(bbz.GetX()), mm(bbz.GetY())), P(mm(bbz.GetX() + bbz.GetWidth()), mm(bbz.GetY() + bbz.GetHeight()))
                d.rectangle([min(a[0], c[0]), min(a[1], c[1]), max(a[0], c[0]), max(a[1], c[1])], outline=(200, 0, 200, 200))
            continue
        if not z.IsOnLayer(L):
            continue
        fs = z.GetFilledPolysList(L)
        for k in range(fs.OutlineCount()):
            o = fs.Outline(k)
            pts = [P(mm(o.CPoint(i).x), mm(o.CPoint(i).y)) for i in range(o.PointCount())]
            d.polygon(pts, fill=(60, 120, 220, 70))
            for h in range(fs.HoleCount(k)):
                hh = fs.Hole(k, h)
                d.polygon([P(mm(hh.CPoint(i).x), mm(hh.CPoint(i).y)) for i in range(hh.PointCount())], fill=(250, 250, 245, 255))
    # contorno
    for dr in b.GetDrawings():
        if dr.GetLayerName() == "Edge.Cuts":
            s, e = dr.GetStart(), dr.GetEnd()
            d.line([P(mm(s.x), mm(s.y)), P(mm(e.x), mm(e.y))], fill=(0, 0, 0), width=2)
    # pads
    for fp in b.GetFootprints():
        for p in fp.Pads():
            c = P(mm(p.GetX()), mm(p.GetY()))
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                r = mm(p.GetDrillSize().x) / 2 * sc
                d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=(0, 0, 0), width=2)
                continue
            if not p.IsOnLayer(L) or not p.IsOnCopperLayer():
                continue
            bp = p.GetBoundingBox()
            a, e = P(mm(bp.GetX()), mm(bp.GetY())), P(mm(bp.GetX() + bp.GetWidth()), mm(bp.GetY() + bp.GetHeight()))
            d.rectangle([min(a[0], e[0]), min(a[1], e[1]), max(a[0], e[0]), max(a[1], e[1])], fill=(150, 160, 175, 255),
                        outline=(60, 70, 90))
    # trilhas
    for t in b.GetTracks():
        n = t.GetNetname()
        col = COL.get(n, (0, 0, 0))
        if t.Type() == pcbnew.PCB_VIA_T:
            c = P(mm(t.GetX()), mm(t.GetY()))
            r = mm(t.GetWidth(pcbnew.F_Cu)) / 2 * sc
            d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=col + (255,), outline=(0, 0, 0))
            r2 = mm(t.GetDrill()) / 2 * sc
            d.ellipse([c[0] - r2, c[1] - r2, c[0] + r2, c[1] + r2], fill=(250, 250, 245))
        elif t.GetLayer() == L:
            s, e = t.GetStart(), t.GetEnd()
            d.line([P(mm(s.x), mm(s.y)), P(mm(e.x), mm(e.y))], fill=col + (235,), width=max(int(mm(t.GetWidth()) * sc), 1))
    img.save(out)


if __name__ == "__main__":
    path, pref = sys.argv[1], sys.argv[2]
    xa = float(sys.argv[3]) if len(sys.argv) > 4 else None
    xb = float(sys.argv[4]) if len(sys.argv) > 4 else None
    sc = float(sys.argv[5]) if len(sys.argv) > 5 else 16
    render(path, pref + "_fundo.png", xa, xb, sc, "B")
    render(path, pref + "_topo.png", xa, xb, sc, "F")
