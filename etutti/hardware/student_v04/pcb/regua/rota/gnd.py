"""Etapa GND das reguas: ligacoes locais de GND (pads do TMAG5253 e do 595), planos F.Cu e B.Cu,
costura com vias e limpeza de vias soltas. Idempotente: refaz tudo que e GND.
Uso: python gnd.py N [local|planos|limpa|tudo]"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import pcbnew  # noqa: E402
import lib_rota as R  # noqa: E402
from lib_rota import F, B, mm, nm  # noqa: E402
import roteia as RT  # noqa: E402


def log(m):
    print(time.strftime("%H:%M:%S"), m, flush=True)


def remove_gnd(b, tracks=True, zones=True):
    if tracks:
        for t in list(b.GetTracks()):
            if t.GetNetname() == "GND":
                b.Remove(t)
    if zones:
        for z in list(b.Zones()):
            if not z.GetIsRuleArea():
                b.Remove(z)


def local_links(ctx, b):
    """Liga os pads de GND de cada CI entre si (curto, so em B.Cu)."""
    groups = {}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if not (ref.startswith("U")):
            continue
        ps = [p for p in fp.Pads() if p.GetNetname() == "GND"]
        if len(ps) > 1:
            groups[ref] = ps
    n_ok = n_bad = 0
    for ref, ps in groups.items():
        # EP (maior) primeiro
        ps = sorted(ps, key=lambda p: -p.GetBoundingBox().GetWidth() * p.GetBoundingBox().GetHeight())
        ep = ps[0]
        for p in ps[1:]:
            bb = ep.GetBoundingBox()
            tree = ctx.pad_cells((mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetX() + bb.GetWidth()), mm(bb.GetY() + bb.GetHeight())), (B,))
            tree |= ctx.track_cells("GND")
            bp = p.GetBoundingBox()
            rect = (mm(bp.GetX()), mm(bp.GetY()), mm(bp.GetX() + bp.GetWidth()), mm(bp.GetY() + bp.GetHeight()))
            tcells = ctx.pad_cells(rect, (B,))
            # ja ligado?
            if tcells & tree:
                continue
            path, why = ctx.route("GND", 0.2, tree, tcells, (mm(p.GetX()), mm(p.GetY())), layer_mult=(50.0, 1.0),
                                  via_cost=1e9, via_ok=False, maxexp=300000)
            if path:
                ctx.write_path("GND", 0.2, path)
                ctx.refresh()
                n_ok += 1
            else:
                n_bad += 1
                log("  GND local %s pad %s: %s" % (ref, p.GetNumber(), why))
    log("GND local: %d ligacoes, %d falhas" % (n_ok, n_bad))
    return n_bad


def add_zones(b, ctx):
    for L in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b)
        z.SetLayer(L)
        z.SetNet(b.FindNet("GND"))
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for (x, y) in ctx.pts:
            ch.Append(nm(x), nm(y))
        ch.SetClosed(True)
        z.Outline().AddOutline(ch)
        z.SetLocalClearance(nm(0.2))
        z.SetMinThickness(nm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetZoneName("GND " + ("F.Cu" if L == pcbnew.F_Cu else "B.Cu"))
        b.Add(z)


def fill(b):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())


def stitch(ctx, b, pitch=2.0, rows=(-5.5, -1.7, 1.7, 5.5)):
    """Vias de GND numa treliça, onde cabem nas duas camadas."""
    bl, viab = ctx.masks("GND", 0.2)
    g = ctx.g
    # alem da folga da mascara, deixa 0.1 mm a mais para o preenchimento do plano ter espessura
    xs = np.arange(ctx.pts and min(p[0] for p in ctx.pts) + 1.0, max(p[0] for p in ctx.pts) - 0.9, pitch)
    n = 0
    ymid = 17.0
    for k, x in enumerate(xs):
        for r in rows:
            for dx in (0.0, 0.5, -0.5, 1.0, -1.0):
                for dy in (0.0, 0.5, -0.5, 1.0, -1.0):
                    xx = round((x + dx - g.x0) / R.STEP) * R.STEP + g.x0
                    yy = round((ymid + r + dy - g.y0) / R.STEP) * R.STEP + g.y0
                    i, j = g.ix(xx), g.iy(yy)
                    if not viab[j, i]:
                        # tem de ficar a 0.35 de qualquer outra via de GND ja posta
                        ctx.add_via("GND", xx, yy)
                        n += 1
                        # marca a vizinhanca como bloqueada para as proximas
                        r_i = int(0.9 / R.STEP)
                        viab[max(j - r_i, 0):j + r_i + 1, max(i - r_i, 0):i + r_i + 1] |= True
                        break
                else:
                    continue
                break
    log("costura: %d vias de GND" % n)
    return n


def dangling_vias(n, board_path):
    out = os.path.join(HERE, "drc_gnd_tmp.json")
    subprocess.run([RT.CLI, "pcb", "drc", "--severity-all", "--schematic-parity", "--format", "json", "-o", out, board_path],
                   capture_output=True, text=True)
    d = json.load(open(out, encoding="utf-8"))
    return d


def main(n, etapa):
    orig, novo = RT.paths(n)
    b = pcbnew.LoadBoard(novo)
    ctx = R.Ctx(b)
    if etapa in ("local", "tudo"):
        remove_gnd(b)
        ctx.refresh()
        local_links(ctx, b)
        pcbnew.SaveBoard(novo, b)
    if etapa in ("planos", "tudo"):
        # remove vias e zonas de GND que nao sejam as ligacoes locais (so vias)
        for t in list(b.GetTracks()):
            if t.GetNetname() == "GND" and t.Type() == pcbnew.PCB_VIA_T:
                b.Remove(t)
        for z in list(b.Zones()):
            if not z.GetIsRuleArea():
                b.Remove(z)
        ctx.refresh()
        add_zones(b, ctx)
        stitch(ctx, b)
        fill(b)
        pcbnew.SaveBoard(novo, b)


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else "tudo")
