"""eTutti Student V3 -- the routed board, made from the routed Student V2 board.

    python etutti/hardware/student_v03/pcb/schematic.py
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/pcb/build_board_v3.py

The V2 board (student_v02/kicad/student_v02.kicad_pcb) is read, never written. Its keyboard routing and
everything that does not touch what moves stays. What changes (the placement is build_sem_rota.py's, approved
by J on 18 Nov 2026; see README.md):

  - every part of the top side but the two encoders goes to the bottom (USB-C, the two jacks, ESD, TVS, 4
    passives, J401 with a slot for the screen's cable); the stubs of their old pads go;
  - H101 is a plain 2.7 mm hole (+ a keep-out like the other M2 holes);
  - the unused charge-light driver (Q201, Q202, R207) is gone;
  - D206 (VBUS_S -> EN_REQ, BAV70): a USB plug switches the 3.3 V on;
  - values and LCSC codes come from the V3 schematic (R203 2.2k, R501 1M, C307 100nF, D202-D205 BAV70);
  - the dotted outlines, the V1 alternatives and the sector labels are off the silkscreen.

Then what KiCad's DRC objects to is ripped up and what is open is routed again with the V2's router
(viaggio_j1/rota_restante.py, through student_v02/pcb/build_board.py's functions). DRC with schematic
parity must come out as the V2's (0 errors but the 3 accepted EN_B widths, 0 unconnected, parity 0).
Set V3_ATTEMPTS / V3_EXPAND to shorten a diagnostic run; progress is in build/progress.log.
Writes kicad/student_v03.kicad_pcb (+ .kicad_pro, .kicad_dru), build/student_v03_drc.json, pcb/board.json.
"""
import collections
import json
import math
import os
import shutil
import sys
import time

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.normpath(os.path.join(HERE, ".."))
HW = os.path.normpath(os.path.join(V3, ".."))
V2 = os.path.join(HW, "student_v02")
sys.path.insert(0, V3)
sys.path.insert(0, os.path.join(V2, "pcb"))
sys.path.insert(0, V2)
sys.path.insert(0, os.path.join(HW, "viaggio_j1"))
import build_sem_rota as SR     # noqa: E402
import build_board as BB        # noqa: E402  (student_v02/pcb/build_board.py)
import rota_restante as rr      # noqa: E402

NAME = "student_v03"
KDIR = os.path.join(V3, "kicad")
BUILD = os.path.join(HERE, "build")
BOARD = os.path.join(KDIR, NAME + ".kicad_pcb")
BB.NAME, BB.KDIR, BB.BUILD, BB.BOARD = NAME, KDIR, BUILD, BOARD
MM, TOMM = pcbnew.FromMM, pcbnew.ToMM
MOVED = list(SR.TO_BOTTOM) + ["J401"]
DEAD_NETS = ("CHGLED", "CHGA")


def xy(p):
    return TOMM(p.x), TOMM(p.y)


def rip_by_drc(b, original, report, keep, when, touched, dangling=True):
    """BB.rip_by_drc with one change: a dangling USB end is not an error (the V3's pair is routed by the router)."""
    total = collections.Counter()
    for _pass in range(25):
        d = BB.save_and_drc(b, original)
        by_uuid = {t.m_Uuid.AsString(): t for t in b.GetTracks()}
        gone = set()
        for x in d.get("violations", []):
            if x["type"] == "hole_to_hole" and dangling:
                v = [by_uuid[i["uuid"]] for i in x["items"] if i.get("uuid") in by_uuid and BB.is_via(by_uuid[i["uuid"]])
                     and by_uuid[i["uuid"]].GetNetname() == "GND"]
                if v and v[0].m_Uuid.AsString() not in gone:
                    gone.add(v[0].m_Uuid.AsString())
                    total["via de GND perto de outro furo"] += 1
                continue
            if x["type"] not in BB.RIP_TYPES or x["severity"] != "error" and x["type"] not in ("via_dangling", "track_dangling"):
                continue
            if not dangling and x["type"] in ("via_dangling", "track_dangling"):
                continue
            cand = [by_uuid[i["uuid"]] for i in x["items"] if i.get("uuid") in by_uuid and i["uuid"] not in keep]
            if not cand:
                continue
            cand.sort(key=lambda t: (rr.klass(t.GetNetname()) == "USB", rr.klass(t.GetNetname()) == "Corrente",
                                     t.GetNetname() in BB.PLANES and not BB.is_via(t)))
            t = cand[0]
            if rr.klass(t.GetNetname()) == "USB" and x["type"] not in ("via_dangling", "track_dangling"):
                raise SystemExit("DRC (%s) on a USB track: %s" % (x["type"], x["description"]))
            if x["type"] in ("via_dangling", "track_dangling"):
                net = t.GetNetname()

                def joined():
                    return sum(1 for g in rr.clusters(b, net) if any(i.GetClass() == "PAD" for i in g["items"]))
                before = joined()
                b.Remove(t)
                if joined() > before:
                    b.Add(t)
                    keep.add(t.m_Uuid.AsString())
                    total["ponta que e ligacao, mantida"] += 1
                    continue
                BB.GRAVE.append(t)
                del by_uuid[t.m_Uuid.AsString()]
                gone.add(None)
                total["%s" % x["type"]] += 1
                continue
            gone.add(t.m_Uuid.AsString())
            total["%s (%s)" % (x["type"], t.GetNetname() if t.GetNetname() in BB.PLANES else "sinal/alimentacao")] += 1
            touched.add(t.GetNetname())
        if not gone:
            break
        for u in gone:
            if u is not None and u in by_uuid:
                BB.rm(b, by_uuid[u])
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    report["tirado pelo DRC (%s)" % when] = dict(total)
    return d


def main():
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(KDIR, exist_ok=True)
    shutil.copyfile(os.path.join(V2, "kicad", "student_v02.kicad_pcb"), BOARD)
    dru = open(os.path.join(V2, "kicad", "student_v02.kicad_dru"), encoding="utf-8").read()
    # V3: the USB-C is on the bottom, 25 mm from the module, all on the bottom side of the board: the V2 rules that kept
    # the pair on F.Cu over the In1 plane (0.24 / 0.15, 90 ohm) go; any layer, 0.15 mm minimum
    i0 = dru.index('(rule "USB 90 ohm')
    i1 = dru.index('(rule "Corrente: minimo 0,8')
    dru = dru[:i0] + """(rule "USB: 0,2 / vao minimo 0,14, qualquer camada de sinal (V3: USB-C no fundo, trilha curta)"
    (condition "A.NetClass == 'USB' && A.Type == 'track'")
    (constraint track_width (min 0.15mm) (opt 0.2mm))
    (constraint diff_pair_gap (min 0.14mm)))
""" + dru[i1:]
    open(os.path.join(KDIR, NAME + ".kicad_dru"), "w", encoding="utf-8").write(dru)
    original = open(BOARD, encoding="utf-8", newline="").read()
    b = pcbnew.LoadBoard(BOARD)
    sch_fields, sch_nets = BB.schematic()
    report, rec = {}, {"moves": {}, "removed": {}}

    def F(ref):
        fp = b.FindFootprintByReference(ref)
        if fp is None:
            raise SystemExit("no %s on the board" % ref)
        return fp

    # ---- sheet files of the V3 schematic
    sheet_of = {}
    for fp in b.GetFootprints():
        path = fp.GetPath().AsString().strip("/").split("/")
        if len(path) == 2:
            fp.SetSheetfile(fp.GetSheetfile().replace("student_v02", NAME))
            sheet_of[fp.GetSheetfile()[-11:-10]] = (path[0], fp.GetSheetname())

    # ---- the USB-C group's old copper (it was routed for a top-side connector): out, the router makes it again
    n = 0
    for t in list(b.GetTracks()):
        pts = [xy(t.GetPosition())] if BB.is_via(t) else [xy(t.GetStart()), xy(t.GetEnd())]
        if all(p[0] < 23.5 and 8.0 < p[1] < 23.0 for p in pts) and t.GetNetname() in ("USB_DP", "USB_DN", "CC1", "CC2", "VBUS"):
            BB.rm(b, t)
            n += 1
    report["cobre antigo da regiao do USB-C"] = n

    # ---- the charge-light driver goes
    for ref in ("Q201", "Q202", "R207"):
        BB.rm(b, F(ref))
    n = 0
    for t in list(b.GetTracks()):
        if t.GetNetname() in DEAD_NETS:
            BB.rm(b, t)
            n += 1
    report["LED de carga"] = {"pecas": 3, "trilhas e vias": n}

    # ---- stubs of the pads that move to the bottom
    n = 0
    for ref in MOVED:
        for pad in F(ref).Pads():
            px, py = xy(pad.GetPosition())
            for t in list(b.GetTracks()):
                ends = [xy(t.GetPosition())] if BB.is_via(t) else [xy(t.GetStart()), xy(t.GetEnd())]
                if any(math.hypot(e[0] - px, e[1] - py) < 0.06 for e in ends):
                    BB.rm(b, t)
                    n += 1
    report["trilhas dos pads que mudam de lado"] = n

    # ---- D206 (new), next to D204
    d204 = F("D204")
    d206 = pcbnew.Cast_to_FOOTPRINT(d204.Duplicate(False))
    b.Add(d206)
    BB.link(d206, "D206", sheet_of["E"][0], "E", sheet_of["E"][1])
    for pad in d206.Pads():
        want = {"1": "VBUS_S", "3": "EN_REQ"}.get(pad.GetNumber())
        pad.SetNet(BB.net_of(b, want or "unconnected-(D206-Pad%s)" % pad.GetNumber()))
    near = xy(d204.GetPosition())
    d206.SetPosition(SR.V(-70, -70))
    w, h = BB.courtyard_size(d204, pcbnew.B_CrtYd)
    x, y, rot = BB.free_spot(BB.obstacles(b, pcbnew.B_Cu), (near[0], near[1] + 3.0), {0: (w, h), 90: (h, w)}, 12.0, margin=0.3)
    d206.SetPosition(SR.V(x, y))
    d206.SetOrientationDegrees(rot)
    report["D206"] = {"x": x, "y": y, "rot": rot}

    # ---- values, codes, fields from the schematic
    for fp in b.GetFootprints():
        f = sch_fields.get(fp.GetReference())
        if f:
            fp.SetValue(f["Value"])
            BB.set_fields(fp, f)

    # ---- placement (J. approved 18 Nov): bottom side, J401 + slot, H101 hole, silkscreen
    SR.clean_silk(b, rec)
    SR.hole_h101(b, rec)
    try:
        F("H101").SetAttributes(F("H1").GetAttributes())
    except Exception as e:
        print("H101 attributes not copied:", e)
    h1 = [z for z in b.Zones() if z.GetZoneName() == "M2 H1"]
    h101 = F("H101")
    if h1:
        try:
            nz = pcbnew.Cast_to_ZONE(h1[0].Duplicate(False))
            c1 = h1[0].GetBoundingBox().GetCenter()
            nz.Move(pcbnew.VECTOR2I(h101.GetX() - c1.x, h101.GetY() - c1.y))
            nz.SetZoneName("M2 H101")
            b.Add(nz)
        except Exception as e:           # a keep-out copy is a courtesy: the router also sees the hole
            print("keep-out of H101 not copied:", e)
    SR.MARGIN = 0.6          # leaves a routing channel between the moved parts
    SR.flip_parts(b, rec)
    SR.MARGIN = 0.3          # J401 + its slot need the tighter fit (0.6 leaves no room)
    SR.place_j401(b, rec)
    # the router reads only the outer outline: the slot gets a keep-out (no tracks, no vias) 0.5 mm round it
    sl = rec["fenda_do_cabo"]["caixa_mm"]
    kz = pcbnew.ZONE(b)
    kz.SetIsRuleArea(True)
    kz.SetDoNotAllowTracks(True)
    kz.SetDoNotAllowVias(True)
    kz.SetDoNotAllowZoneFills(True)
    ls = pcbnew.LSET()
    for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        ls.AddLayer(L)
    kz.SetLayerSet(ls)
    ko = kz.Outline()
    ko.NewOutline()
    for qx, qy in ((sl[0] - 0.5, sl[1] - 0.5), (sl[2] + 0.5, sl[1] - 0.5), (sl[2] + 0.5, sl[3] + 0.5), (sl[0] - 0.5, sl[3] + 0.5)):
        ko.Append(MM(qx), MM(qy))
    kz.SetZoneName("fenda do cabo da tela")
    b.Add(kz)
    report["colocacao"] = rec
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    keep = set()
    rip_by_drc(b, original, report, keep, "antes de rotear", set(), dangling=False)

    # ---- route what is open (the V2's driver)
    _astar = rr.astar
    expand = int(os.environ.get("V3_EXPAND", "10000000"))
    attempts = int(os.environ.get("V3_ATTEMPTS", "6"))
    rr.astar = lambda *a, **kw: _astar(*a, **dict(kw, max_expand=expand))
    prog = open(os.path.join(BUILD, "progress.log"), "w", encoding="utf-8")

    def say(*a):
        prog.write(" ".join(str(x) for x in a) + "\n")
        prog.flush()
    # (no rr.PROTECT boxes: round the 0.5 mm pitch pads of the USB-C they would block each other's exits)
    all_nets = sorted({p_.GetNetname() for p_ in b.GetPads() if p_.GetNetname() and not p_.GetNetname().startswith("unconnected-")})
    made, log, fails, routed = [], [], [], []
    first = None
    for attempt in range(1, attempts + 1):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        ctx = rr.Ctx(b)
        chk = rr.Checker(ctx)
        made, log, fails, routed = [], [], [], []
        opened = [n_ for n_ in all_nets if n_ not in BB.PLANES and len(rr.clusters(b, n_)) > 1]
        if first is None:
            first = sorted(opened, key=lambda n_: (rr.klass(n_) != "Corrente", n_))
        order = [n_ for n_ in first if n_ in opened] + [n_ for n_ in opened if n_ not in first]
        say("tentativa", attempt, "abertas:", order)
        for net in order:
            before, nf, t0 = len(made), len(fails), time.time()
            rr.join_net(ctx, chk, net, None, made, log, fails)
            routed.append({"rede": net, "objetos": len(made) - before})
            say("  %-12s %3d objetos %5.0f s  %s" % (net, len(made) - before, time.time() - t0, fails[nf:]))
        for _round in range(3):
            before = len(made)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
            ctx.refresh()
            chk = rr.Checker(ctx)
            rr.join_net(ctx, chk, "+3V3", None, made, log, fails)
            rr.join_net(ctx, chk, "GND", None, made, log, fails, gnd_mode=True)
            routed.append({"rede": "GND / +3V3 (rodada %d)" % (_round + 1), "objetos": len(made) - before})
            say("  GND/+3V3 rodada", _round + 1, len(made) - before, "objetos")
            if len(made) == before:
                break
        report.setdefault("tentativas", []).append(
            {"tentativa": attempt, "falhas": sorted({f["net"] + " " + str(f["pinos"]) for f in fails})})
        print("tentativa %d: %d objetos, falhas %s" % (attempt, len(made), sorted({f["net"] for f in fails})), flush=True)
        say("falhas:", fails)
        if not fails or attempt == attempts:
            break
        ids = set(made)
        for t in list(b.GetTracks()):
            if t.m_Uuid.AsString() in ids:
                BB.rm(b, t)
        bad = [f["net"] for f in fails]
        first = [n_ for n_ in order if n_ in bad] + [n_ for n_ in order if n_ not in bad]
    report["roteado"] = routed
    report["falhas"] = [dict(f, **{k: [float(v) for v in f[k]] for k in ("de", "ate", "em") if k in f}) for f in fails]
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

    d = rip_by_drc(b, original, report, keep, "depois de rotear", set())
    viol = collections.Counter(x["type"] for x in d.get("violations", []) if x["severity"] == "error")
    warn = collections.Counter(x["type"] for x in d.get("violations", []) if x["severity"] != "error")
    report["drc"] = {"erros": dict(viol), "avisos": dict(warn), "ligacoes_faltando": len(d.get("unconnected_items", [])),
                     "paridade": len(d.get("schematic_parity", []))}
    report["drc_detalhe"] = [(x["type"], x["description"], [(i["description"], i["pos"]) for i in x["items"]])
                             for x in d.get("violations", []) if x["severity"] == "error"][:40]
    report["paridade_detalhe"] = [(x["type"], x["description"], [i["description"] for i in x["items"]])
                                  for x in d.get("schematic_parity", [])][:40]
    report["faltando_detalhe"] = [[(i["description"], i["pos"]) for i in x["items"]] for x in d.get("unconnected_items", [])][:40]
    json.dump(report, open(os.path.join(HERE, "board.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for k in ("LED de carga", "trilhas dos pads que mudam de lado", "D206", "tirado pelo DRC (antes de rotear)",
              "tirado pelo DRC (depois de rotear)", "roteado", "falhas", "drc"):
        print(k, ":", json.dumps(report.get(k), ensure_ascii=False))
    for x in report["drc_detalhe"][:20] + report["paridade_detalhe"][:20] + report["faltando_detalhe"][:20]:
        print("  ", x)
    ok = dict(viol) == BB.ACCEPTED and not d.get("unconnected_items") and not d.get("schematic_parity") and not fails
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
