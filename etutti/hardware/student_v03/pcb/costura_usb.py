"""Student V3 -- the GND island under the USB pair, stitched to the In1 plane.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/pcb/costura_usb.py

refaz_usb.py put the pair on B.Cu and a GND island (+ a keep-out for tracks and vias) on In2 under it. An island joined to
the In1 plane by one via is a poor reference at 480 Mbit/s: this script rebuilds the two In2 zones from the final paths
(refaz_usb.build_paths) and drops GND vias round the pair, ~2.4 mm apart, 1.0 mm to the side of the nearest line (outside
the keep-out, 0.35 mm clear of the copper). A via that DRC objects to is taken out again; nothing else is touched.
"""
import json
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import refaz_usb as R           # noqa: E402

BB, MM, TOMM = R.BB, R.MM, R.TOMM
OFFSET = 1.0                    # via centre to the nearest line's centre
STEP = 1.7


def candidates(dp, dn):
    lines = [dp, dn]
    segs = [(a, z) for pl in lines for a, z in zip(pl, pl[1:])]
    out = []
    for pl in lines:
        for a, z in zip(pl, pl[1:]):
            L = math.hypot(z[0] - a[0], z[1] - a[1])
            if L < 0.9 or max(a[0], z[0]) < 11.8 or min(a[0], z[0]) > 21.0:
                continue
            ux, uy = (z[0] - a[0]) / L, (z[1] - a[1]) / L
            n = max(1, int(L // STEP))
            for k in range(n):
                t = (k + 0.5) * L / n
                for side in (+1, -1):
                    px, py = a[0] + ux * t - uy * OFFSET * side, a[1] + uy * t + ux * OFFSET * side
                    d = min(R.seg_dist((px, py), s0, s1) for s0, s1 in segs)
                    if 0.9 <= d <= 1.9 and 11.8 < px < 21.0:
                        out.append((round(px, 3), round(py, 3)))
    keep = []
    for c in out:
        if all(math.hypot(c[0] - q[0], c[1] - q[1]) >= 1.3 for q in keep):
            keep.append(c)
    return keep


def main():
    original = open(R.BOARD, encoding="utf-8", newline="").read()
    b = pcbnew.LoadBoard(R.BOARD)
    dp, dn, lens = R.build_paths()
    for z in list(b.Zones()):
        if z.GetZoneName().startswith("USB:"):
            BB.rm(b, z)
    R.add_in2_zones(b, dp, dn)
    # earlier stitching vias of this script (same net, in the island) go too: marked by their position list in the json
    jpath = os.path.join(HERE, "costura_usb.json")
    if os.path.exists(jpath):
        old = json.load(open(jpath))["vias"]
        for t in list(b.GetTracks()):
            if t.GetClass() == "PCB_VIA" and [round(TOMM(t.GetPosition().x), 3), round(TOMM(t.GetPosition().y), 3)] in old:
                BB.rm(b, t)
    cand = candidates(dp, dn)
    vias = {}
    for (x, y) in cand:
        vias[(x, y)] = R.add_via(b, x, y, "GND")
    removed = []
    for _pass in range(4):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        d = BB.save_and_drc(b, original)
        by_uuid = {v.m_Uuid.AsString(): k for k, v in vias.items()}
        bad = set()
        for x in d.get("violations", []):
            if x["severity"] != "error" and x["type"] != "hole_to_hole":
                continue
            for i in x["items"]:
                if i.get("uuid") in by_uuid:
                    bad.add(by_uuid[i["uuid"]])
        if not bad:
            break
        for k in bad:
            BB.rm(b, vias.pop(k))
            removed.append(k)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    d = BB.save_and_drc(b, original)
    import collections
    viol = collections.Counter(x["type"] for x in d.get("violations", []) if x["severity"] == "error")
    warn = collections.Counter(x["type"] for x in d.get("violations", []) if x["severity"] != "error")
    res = {"vias": [list(k) for k in vias], "tiradas_pelo_DRC": [list(k) for k in removed], "drc_erros": dict(viol),
           "avisos": dict(warn), "ligacoes_faltando": len(d.get("unconnected_items", [])),
           "paridade": len(d.get("schematic_parity", []))}
    json.dump(res, open(jpath, "w"), indent=1)
    print(json.dumps({k: (len(v) if k in ("vias", "tiradas_pelo_DRC") else v) for k, v in res.items()}))
    for x in d.get("violations", []):
        if x["severity"] != "error" and "isolated" in x["type"]:
            print("  ", x["type"], [(i["description"], i["pos"]) for i in x["items"]])
    ok = dict(viol) == BB.ACCEPTED and not d.get("unconnected_items") and not d.get("schematic_parity")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
