"""Stage 4 of the ruler routing: the acceptance check of gate C-regua. KiCad python.

    python verifica.py rota/kicad/slim_regua_rota.kicad_pcb   -> rota/build/verifica.json (+ prints; exit 1 when anything is not zero)

  - kicad-cli DRC with schematic parity (metricas.drc): errors, warnings, unconnected items, parity items
  - widths: no track below the rule minimum 0.15 mm (smallest present)
  - dangling ends: DRC warnings track_dangling / via_dangling (0 wanted) + our own count of copper ends touching nothing
  - GND pour islands: every filled outline of both GND zones must hold a GND pad, a GND via or a GND track end (else it is an island)
  - OUT keep-away: smallest edge-to-edge distance between OUT copper and DATA/CLK/LATCH copper outside the FFC zone (>= 1.0 wanted)
"""
import json, math, os, sys
import pcbnew
import metricas
HERE = os.path.dirname(os.path.abspath(__file__))
mm = pcbnew.ToMM


def own_dangling(b):
    """copper ends that touch nothing: a track end must lie on a pad, a via, or another track of the same net on the same layer (end or body: a tee counts)."""
    pcb = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    out = []
    pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
    vias = [v for v in b.GetTracks() if v.GetClass() == "PCB_VIA"]
    for t in pcb:
        for end in (t.GetStart(), t.GetEnd()):
            pt = pcbnew.SHAPE_CIRCLE(end, 1500)
            ok = False
            for p in pads:
                if p.GetNetCode() == t.GetNetCode() and p.IsOnLayer(t.GetLayer()) and p.GetEffectiveShape(t.GetLayer()).Collide(pt, 0):
                    ok = True
                    break
            if not ok:
                for v in vias:
                    if v.GetNetCode() == t.GetNetCode() and v.GetEffectiveShape(t.GetLayer()).Collide(pt, 0):
                        ok = True
                        break
            if not ok:
                for u in pcb:
                    if u is not t and u.GetNetCode() == t.GetNetCode() and u.GetLayer() == t.GetLayer() and u.GetEffectiveShape(u.GetLayer()).Collide(pt, 0):
                        ok = True
                        break
            if not ok:
                out.append((mm(end.x), mm(end.y), t.GetNetname()))
    return out


def islands(b):
    gnd = b.FindNet("GND").GetNetCode()
    res = []
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() != gnd:
            continue
        L = z.GetLayer()
        ps = z.GetFilledPolysList(L)
        for i in range(ps.OutlineCount()):
            single = pcbnew.SHAPE_POLY_SET()
            single.AddOutline(ps.COutline(i))
            has = False
            for fp in b.GetFootprints():
                for p in fp.Pads():
                    if p.GetNetCode() == gnd and p.IsOnLayer(L) and single.Collide(p.GetPosition(), 10):
                        has = True
            for t in b.GetTracks():
                if t.GetNetCode() == gnd and t.GetClass() == "PCB_VIA" and single.Collide(t.GetPosition(), 10):
                    has = True
            if not has:
                bb = single.BBox()
                res.append((z.GetZoneName(), round(mm(bb.GetX()), 2), round(mm(bb.GetY()), 2), round(mm(bb.GetWidth()), 2), round(mm(bb.GetHeight()), 2)))
    return res


def out_keepaway(b):
    """min edge-to-edge distance OUT <-> DATA/CLK/LATCH copper outside x < 25.6 (FFC zone), per layer (pads included)."""
    items = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        if n in ("OUT", "DATA", "CLK", "LATCH"):
            items.setdefault(n, []).append(t)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            n = p.GetNetname()
            if n in ("OUT", "DATA", "CLK", "LATCH"):
                items.setdefault(n, []).append(p)
    best = 1e9
    where = None
    for a in items.get("OUT", []):
        for n in ("DATA", "CLK", "LATCH"):
            for c in items.get(n, []):
                for L in (pcbnew.F_Cu, pcbnew.B_Cu):
                    if not (a.IsOnLayer(L) and c.IsOnLayer(L)):
                        continue
                    pa, pc = a.GetBoundingBox().GetCenter(), c.GetBoundingBox().GetCenter()
                    if mm(pa.x) < 25.6 and mm(pc.x) < 25.6:
                        continue
                    sa, sc = a.GetEffectiveShape(L), c.GetEffectiveShape(L)
                    d = sa.Collide(sc, 0)  # touching test only; get distance by bisection
                    lo, hi = 0.0, 3.0
                    if sa.Collide(sc, int(hi * 1e6)) is False:
                        continue
                    for _ in range(14):
                        mid = (lo + hi) / 2
                        if sa.Collide(sc, int(mid * 1e6)):
                            hi = mid
                        else:
                            lo = mid
                    if hi < best:
                        best, where = hi, (round(mm(pa.x), 1), round(mm(pa.y), 1), n)
    return round(best, 3) if best < 1e8 else None, where


def main(path):
    b = pcbnew.LoadBoard(path)
    g = metricas.geom(path)
    d = metricas.drc(path, os.path.splitext(os.path.basename(path))[0])
    dang = own_dangling(b)
    isl = islands(b)
    ka = out_keepaway(b)
    res = {"placa": os.path.relpath(path, HERE), "drc": d, "trilhas": g["trilhas"], "vias": g["vias"], "comprimento_mm": g["comprimento_mm"], "comprimento_por_rede": g["por_rede"],
           "largura_min_mm": g["larg_min_mm"], "pontas_soltas_proprio": dang, "ilhas_de_plano": isl, "OUT_afastamento_min_mm": ka[0], "OUT_afastamento_onde": ka[1]}
    ok = (d["erros"] == 0 and d["avisos"] == 0 and d["nao_ligados"] == 0 and d["paridade"] == 0 and g["larg_min_mm"] >= 0.15 and not dang and not isl)
    res["aceito"] = bool(ok)
    json.dump(res, open(os.path.join(HERE, "build", "verifica.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(os.path.abspath(sys.argv[1]))
