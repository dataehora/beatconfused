"""Turn the placed Viaggio board into a clean starting point for routing by hand.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio/pcb/handoff_freerouting.py

J routes the board himself in KiCad with the Freerouting plugin (decision of
25 Oct 2026). This script starts from kicad/viaggio.kicad_pcb as build_board.py
left it (all parts placed, net classes, rules, stack-up, zones, silkscreen) and:

  1. links every footprint to its schematic symbol (sheet + symbol UUID from
     build/viaggio_netlist.net), copies the Codigo / LCSC / Montagem fields and
     gives unused pins their "unconnected-(...)" nets, so KiCad's "Update PCB
     from Schematic" (F8) and the DRC's schematic parity are clean; the 28
     Gateron switches and the 8 M2 holes are marked "board only";
  2. gives the M2 holes a courtyard the size of the screw head (Ø 3.8): their
     copper-free ring of 3.5 mm is a rule area, not a courtyard, and the old
     4.95 mm courtyard overlapped the switches around them;
  3. moves the few small parts whose courtyards overlap, 0.1 mm at a time away
     from their neighbour, until the DRC finds no overlap;
  4. removes every track and via (the partial sector P routing of build_board.py
     is kept in kicad/viaggio_rota_P_parcial.kicad_pcb, for reference only),
     refills the zones, runs the DRC with schematic parity, and writes
       kicad/viaggio.kicad_pcb           the board to route
       build/viaggio.dsn                 Specctra DSN for the standalone Freerouting
       build/viaggio_handoff.json        DRC counts, moved parts, unrouted per sector
Exits non-zero if the DRC has any error other than unrouted connections.
"""
import json
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pcbnew  # noqa: E402

import sexpr as S  # noqa: E402

KDIR = os.path.join(HERE, "kicad")
BUILD = os.path.join(HERE, "build")
BOARD = os.path.join(KDIR, "viaggio.kicad_pcb")
PARTIAL = os.path.join(KDIR, "viaggio_rota_P_parcial.kicad_pcb")
NETLIST = os.path.join(BUILD, "viaggio_netlist.net")
DRC_OUT = os.path.join(BUILD, "viaggio_handoff_drc.json")
KICAD_CLI = os.path.join(os.path.dirname(sys.executable), "kicad-cli.exe")
HEAD_R = 1.9                 # M2 head Ø 3.8
FIXED = {"U101"}             # never moved
STEP = 0.1


def load_netlist():
    tree = S.parse(open(NETLIST, encoding="utf-8").read())
    comps = {}
    for c in S.find(S.first(tree, "components"), "comp"):
        props = {S.first(p, "name")[1]: (S.first(p, "value") or [None, ""])[1] for p in S.find(c, "property")}
        for f in S.find(S.first(c, "fields"), "field"):
            vals = [x for x in f[1:] if not isinstance(x, list)]
            props[S.first(f, "name")[1]] = vals[0] if vals else ""
        sheet = S.first(S.first(c, "sheetpath"), "tstamps")[1]
        stamp = S.first(c, "tstamps")[1].split()[0]
        comps[S.first(c, "ref")[1]] = dict(path=sheet + stamp, props=props)
    pads = {}
    for n in S.find(S.first(tree, "nets"), "net"):
        name = S.first(n, "name")[1]
        for nd in S.find(n, "node"):
            pads[(S.first(nd, "ref")[1], S.first(nd, "pin")[1])] = name
    return comps, pads


def drc():
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--schematic-parity",
                    "--output", DRC_OUT, BOARD], capture_output=True)
    return json.load(open(DRC_OUT, encoding="utf-8"))


def link(board, comps, pads):
    netinfo = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        c = comps.get(ref)
        if c is None:
            fp.SetBoardOnly(True)            # Gateron switches, M2 holes: mechanical only
            continue
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        fp.SetSheetname(c["props"].get("Sheetname", ""))
        fp.SetSheetfile(c["props"].get("Sheetfile", ""))
        for key in ("Codigo", "LCSC", "Montagem", "Datasheet", "Description"):
            val = c["props"].get(key, "")
            f = fp.GetField(key)
            if f is None:
                f = pcbnew.PCB_FIELD(fp, fp.GetNextFieldOrdinal(), key)
                f.SetVisible(False)
                f.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
                fp.Add(f)
            f.SetText(val)
        for p in fp.Pads():
            n = pads.get((ref, p.GetNumber()))
            if n and n.startswith("unconnected-") and p.GetNetname() == "":
                if n not in netinfo:
                    ni = pcbnew.NETINFO_ITEM(board, n)
                    board.Add(ni)
                    netinfo[n] = ni
                p.SetNet(netinfo[n])


def hole_courtyards(board):
    for fp in board.GetFootprints():
        if not (fp.GetReference().startswith("H") and "MountingHole" in fp.GetFPIDAsString()):
            continue
        pos = fp.GetPosition()
        px, py = pos.x, pos.y
        for g in [g for g in fp.GraphicalItems() if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd)]:
            fp.Delete(g)
        c = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_CIRCLE)
        c.SetCenter(pcbnew.VECTOR2I(px, py))
        c.SetEnd(pcbnew.VECTOR2I(px + pcbnew.FromMM(HEAD_R), py))
        c.SetLayer(pcbnew.F_CrtYd)
        c.SetWidth(pcbnew.FromMM(0.05))
        fp.Add(c)


def area(fp):
    bb = fp.GetBoundingBox(False)
    return pcbnew.ToMM(bb.GetWidth()) * pcbnew.ToMM(bb.GetHeight())


def main():
    if not os.path.exists(PARTIAL):
        shutil.copy(BOARD, PARTIAL)
    comps, pads = load_netlist()
    board = pcbnew.LoadBoard(BOARD)
    link(board, comps, pads)
    hole_courtyards(board)
    # SPEC section 5: In1 = GND whole, In2 = GND + power islands. As "power" (plane) layers the
    # DSN tells Freerouting not to route on them; it reaches their nets through vias.
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)
    tracks = [t for t in board.GetTracks()]
    for t in tracks:
        board.Delete(t)
    pcbnew.SaveBoard(BOARD, board)

    moved = {}
    for _ in range(40):
        d = drc()
        pairs = [[i["description"].split()[-1] for i in v["items"]] for v in d.get("violations", [])
                 if v["type"] == "courtyards_overlap"]
        if not pairs:
            break
        board = pcbnew.LoadBoard(BOARD)
        for a, b in pairs:
            fa, fb = board.FindFootprintByReference(a), board.FindFootprintByReference(b)
            if b in FIXED or (a not in FIXED and area(fa) < area(fb)):
                fa, fb = fb, fa
            if fb.GetReference() in FIXED:
                continue
            pa, pb = fa.GetPosition(), fb.GetPosition()
            dx, dy = pcbnew.ToMM(pb.x - pa.x), pcbnew.ToMM(pb.y - pa.y)
            L = math.hypot(dx, dy) or 1.0
            ux, uy = round(dx / L * STEP, 3), round(dy / L * STEP, 3)
            fb.SetPosition(pcbnew.VECTOR2I(pb.x + pcbnew.FromMM(ux), pb.y + pcbnew.FromMM(uy)))
            r = fb.GetReference()
            ox, oy = moved.get(r, (0.0, 0.0))
            moved[r] = (round(ox + ux, 2), round(oy + uy, 2))
        pcbnew.SaveBoard(BOARD, board)

    board = pcbnew.LoadBoard(BOARD)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    os.makedirs(BUILD, exist_ok=True)
    ok_dsn = pcbnew.ExportSpecctraDSN(board, os.path.join(BUILD, "viaggio.dsn"))

    d = drc()
    vio = d.get("violations", [])
    kinds = {}
    for v in vio + d.get("schematic_parity", []):
        k = "%s/%s" % (v["severity"], v["type"])
        kinds[k] = kinds.get(k, 0) + 1
    code = {r: c["props"].get("Codigo", "") for r, c in comps.items()}
    per = {}
    for u in d.get("unconnected_items", []):
        sec = sorted({(code.get(i["description"].split(" of ")[-1].split()[0], "") or "?")[:1]
                      for i in u.get("items", [])})
        per["-".join(sec)] = per.get("-".join(sec), 0) + 1
    out = {"tracks_removed": len(tracks), "moved_mm": moved, "violations": kinds,
           "unrouted": len(d.get("unconnected_items", [])), "unrouted_by_sector": dict(sorted(per.items())),
           "dsn": bool(ok_dsn)}
    json.dump(out, open(os.path.join(BUILD, "viaggio_handoff.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    bad = [v for v in vio + d.get("schematic_parity", []) if v["severity"] == "error"]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
