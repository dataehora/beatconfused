"""Stage 3 of the ruler routing: GND. KiCad python, idempotent (reads the signals board, writes the output; GND copper of an earlier run is dropped first).

    python gnd.py in.kicad_pcb out.kicad_pcb

  1. GND pour on F.Cu (key side, the plane the SPEC asks for; already in the base board) and a GND pour on B.Cu over the free area (so no pad is shut off by the tracks).
  2. Every GND pad on B.Cu gets a tap: the pad is inside the B.Cu pour if it is reachable, else a short track + via to the top plane. Plane stitching vias on a grid
     (STITCH mm) wherever both pours are free (>= 0.3 + 0.2 mm from other nets, 0.25 mm from holes), so the two pours are one plane.
  3. Zones refilled, saved. Island removal is ON in both zones: copper that is not connected to the pads simply does not exist after the fill.
"""
import math, os, sys
import pcbnew
M = pcbnew.FromMM
T = pcbnew.ToMM
STITCH = float(os.environ.get("STITCH", 8.0))
VIA_D, VIA_DR = 0.6, 0.3
CLR = 0.2                 # pour clearance
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))

def other_items(b, gnd):
    """copper shapes (layer-resolved) of every item that is not GND."""
    out = []
    for t in b.GetTracks():
        if t.GetNetCode() != gnd:
            out.append(t)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() != gnd:
                out.append(p)
    return out

def free_spot(b, items, holes, x, y, margin=CLR):
    """via of VIA_D at (x, y) keeps `margin` from every non-GND copper item on both layers and 0.25 from NPTH holes, stays 0.5 inside the outline."""
    if not (20.5 + .3 <= x <= 179.5 - .3 and 22.5 + .75 <= y <= 37.5 - .75):
        return False
    circ = pcbnew.SHAPE_CIRCLE(V(x, y), M(VIA_D / 2))
    for it in items:
        for L in (pcbnew.F_Cu, pcbnew.B_Cu):
            if it.IsOnLayer(L) and it.GetEffectiveShape(L).Collide(circ, M(margin)):
                return False
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias() and z.Outline().Collide(V(x, y), M(VIA_D / 2 + 0.05)):
            return False
    for hx, hy, hr in holes:
        if math.hypot(hx - x, hy - y) < hr + 0.25 + VIA_D / 2 + 0.02:
            return False
    # also keep 0.25 mm hole-to-hole from other vias' drills
    return True

def seg_free(b, items, x0, y0, x1, y1, margin=0.17):
    seg = pcbnew.SHAPE_SEGMENT(V(x0, y0), V(x1, y1), M(0.2))
    for it in items:
        if it.IsOnLayer(pcbnew.B_Cu) and it.GetEffectiveShape(pcbnew.B_Cu).Collide(seg, M(margin)):
            return False
    return True

def main(src, dst):
    b = pcbnew.LoadBoard(src)
    gnd = b.FindNet("GND").GetNetCode()
    # (the GND copper already on the board -- the sensors' vias and stubs drawn by fixa.py -- stays; the input is rebuilt from the base board on every run)
    for z in list(b.Zones()):
        if not z.GetIsRuleArea() and z.GetLayer() == pcbnew.B_Cu:
            b.Remove(z)
    keep = []   # keep python objects alive (pcbnew gotcha)
    # B.Cu pour
    bz = pcbnew.ZONE(b); bz.SetLayer(pcbnew.B_Cu); bz.SetNet(b.FindNet("GND")); bz.SetZoneName("GND baixo")
    bz.SetLocalClearance(M(CLR)); bz.SetMinThickness(M(0.2)); bz.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    bz.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    bz.SetThermalReliefGap(M(0.2)); bz.SetThermalReliefSpokeWidth(M(0.25))
    o = bz.Outline(); o.NewOutline()
    for x, y in ((20.0, 22.5), (180.0, 22.5), (180.0, 37.5), (20.0, 37.5)):
        o.Append(M(x), M(y))
    b.Add(bz); keep.append(bz)
    # outline inset for both pours: copper pulled 0.3 from the edge
    for z in b.Zones():
        if not z.GetIsRuleArea():
            z.SetLocalClearance(M(CLR))
    items = other_items(b, gnd)
    holes = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                holes.append((T(p.GetX()), T(p.GetY()), T(p.GetDrillSize().x) / 2))
    n_pad, n_st, miss = 0, 0, []
    # pad taps: only where the pad is shut off; decided after a first fill -> here every GND pad on B.Cu gets a via within 1.6 mm if one fits (cheap, robust)
    def add_via(x, y):
        v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetNet(b.FindNet("GND")); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(M(VIA_D)); v.SetDrill(M(VIA_DR)); b.Add(v); keep.append(v)
        items.append(v)       # later candidates keep their distance from it (GND vias count as foreign for each other: 0.2 mm min, fine)
    def stub(x0, y0, x1, y1, L=pcbnew.B_Cu):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(x0, y0)); t.SetEnd(V(x1, y1)); t.SetWidth(M(0.2)); t.SetLayer(L); t.SetNet(b.FindNet("GND")); b.Add(t); keep.append(t)
    gpads = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == gnd and p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu):
                gpads.append((fp.GetReference(), p.GetNumber(), T(p.GetX()), T(p.GetY())))
    gtracks = [t for t in b.GetTracks() if t.GetNetCode() == gnd]
    def tapped(px, py):
        P = V(px, py)
        for t in gtracks:
            if t.GetClass() == "PCB_VIA":
                continue
            for q in (t.GetStart(), t.GetEnd()):
                if abs(q.x - P.x) < 1000 and abs(q.y - P.y) < 1000:
                    return True
        return False
    for ref, num, px, py in gpads:
        if tapped(px, py):
            continue
        done = False
        for rad in (0.0, 0.8, 1.1, 1.4, 1.8, 2.3):
            for k in range(16 if rad else 1):
                a = 2 * math.pi * k / 16
                x, y = px + rad * math.cos(a), py + rad * math.sin(a)
                if free_spot(b, items, holes, x, y) and (not rad or seg_free(b, items, px, py, x, y)):
                    add_via(x, y)
                    if rad:
                        stub(px, py, x, y)
                    done = True; n_pad += 1
                    break
            if done:
                break
        if not done:
            miss.append((ref, num, px, py))
    # stitching grid
    x = 24.0
    while x < 178:
        for y in (24.5, 30.0, 35.8):
            if free_spot(b, items, holes, x, y):
                add_via(x, y); n_st += 1
            else:
                for dx, dy in ((0.8, 0), (-0.8, 0), (0, 0.8), (0, -0.8), (1.6, 0), (-1.6, 0)):
                    if free_spot(b, items, holes, x + dx, y + dy):
                        add_via(x + dx, y + dy); n_st += 1; break
        x += STITCH
    # pads that found no via of their own (fine-pitch connector pads whose pour piece must be tied to the top plane): a few vias in the free copper round them
    for ref, num, px, py in miss:
        added = 0
        for rad in (1.2, 1.6, 2.0, 2.5, 3.0, 3.6):
            for k in range(24):
                a = 2 * math.pi * k / 24
                x, y = px + rad * math.cos(a), py + rad * math.sin(a)
                if added < 2 and free_spot(b, items, holes, x, y):
                    add_via(x, y)
                    n_st += 1
                    added += 1
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    pcbnew.SaveBoard(dst, b)
    print("GND: vias de pad %d, de costura %d, sem lugar: %s" % (n_pad, n_st, miss))

if __name__ == "__main__":
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
