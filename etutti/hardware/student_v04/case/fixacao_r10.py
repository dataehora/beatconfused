"""R10V4 item 3: the two M2 points of every R8 (and R4): which gaps between key housings are free, and the two farthest apart.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/fixacao_r10.py   -> out/fixacao_r10.json

Candidates: the gaps between housings (u = 18.5 k, k = 1..7 on the R8; k = 1..3 on the R4), v = +5.2 (front half of the ruler: the back half
carries the headers, the interior posts and the entalhes). A candidate is free when its D6 boss (+0.4 mm) touches none of: the SH headers and
plugs of ANY row, the board cables (both free-wire lengths), the interior posts (D5.4 + blade), the wall posts. The 595 and the capacitors are the
electronics' (the R8's layout is theirs): the contract is that every hole has a 6.4 mm clear land under it (u +-3.2) and the 595 stays out of it.
"""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_r4 as L    # noqa: E402
import ligacao_h as H    # noqa: E402

H.configure(L.OUT_X)
zone = H.plugs_and_headers_mask()
for F in H.F_LIST.values():
    for r in (1, 2, 3, 4):
        pts, _a, _b = H.board_cable(r, F)
        zone |= H.sweep(pts, H.BW / 2 + H.CLR)
boss, post, wall = H.solid_masks()
zone |= post | wall


def free(ru, u, d=L.M2_BOSS_D / 2 + 0.4):
    t = H.blank()
    H.stamp_disk(t, ru["x0"] + u, ru["y"] + 5.2, d)
    return not (t & zone).any()


def run():
    res = {}
    for ru in L.rulers(0):
        us = [18.5 * k for k in range(1, 8)]
        ok = [u for u in us if free(ru, u)]
        best = (max(ok) - min(ok), min(ok), max(ok)) if len(ok) >= 2 else None
        res["R%d" % ru["row"]] = {"livres_u": ok, "bloqueados_u": [u for u in us if u not in ok],
                                  "par_mais_afastado_u": list(best[1:]) if best else None, "vao_mm": best[0] if best else None}
    json.dump(res, open(os.path.join(HERE, "out", "fixacao_r10.json"), "w"), indent=1)
    for k, v in res.items():
        print(k, v)


if __name__ == "__main__":
    run()


def r4_study():
    """R10V4 item 3, R4 (validation of the 48-key row R8 + R4; the R4 is always the right-hand end): which of the R4's three holes (u 18.5 / 37 / 55.5) are free of the
    junction loop (R8 OUT plug -> R4 IN plug, both free-wire lengths), the plugs and headers of both rulers, in each row. Raster of 0.1 mm, boss D6 + 0.4."""
    zone = H.blank()
    rows = []
    for r, y, x0r, n in L.ROWS:
        xr8 = x0r - L.PITCH / 2
        xj = xr8 + L.RULER_L                                  # the R4's start
        for F in H.F_LIST.values():
            zone |= H.loop_body(xj, y, H.loop_a(F))
        # headers and plugs: R8 OUT plug + header, R4 IN header + plug, R4 OUT header (no plug)
        for (xa, c, plug) in ((xr8, L.OUT_X, True), (xj, L.IN_X, True), (xj, 47.5, False)):
            H.stamp_rect(zone, xa + c - L.HDR_W / 2, xa + c + L.HDR_W / 2, y + L.LANE_Y0, y + L.LANE_Y0 + L.HDR_D)
            if plug:
                H.stamp_rect(zone, xa + c - L.PLUG_W / 2 - 0.2, xa + c + L.PLUG_W / 2 + 0.2, y + L.LANE_Y0 - L.PLUG_D, y + L.LANE_Y0)
        rows.append((r, y, xj))
    out = {}
    for r, y, xj in rows:
        ok = []
        for u in (18.5, 37.0, 55.5):
            t = H.blank()
            H.stamp_disk(t, xj + u, y + 5.2, L.M2_BOSS_D / 2 + 0.4)
            if not (t & zone).any():
                ok.append(u)
        out["R%d" % r] = ok
    return out


if __name__ == "__main__":
    r = r4_study()
    print("R4 livres:", r)
    d = json.load(open(os.path.join(HERE, "out", "fixacao_r10.json")))
    d["r4_livres_u"] = r
    json.dump(d, open(os.path.join(HERE, "out", "fixacao_r10.json"), "w"), indent=1)


def r8_with_junction():
    """The same check for the FIRST R8 of a longer row (48/64/80 keys): its OUT now has a plug and a cable loop to the next ruler. Which of the four R8 holes stay free."""
    zone = H.blank()
    for r, y, x0r, n in L.ROWS:
        xr8 = x0r - L.PITCH / 2
        xj = xr8 + L.RULER_L
        for F in H.F_LIST.values():
            zone |= H.loop_body(xj, y, H.loop_a(F))
        for (xa, c) in ((xr8, L.IN_X), (xr8, L.OUT_X), (xj, L.IN_X)):
            H.stamp_rect(zone, xa + c - L.HDR_W / 2, xa + c + L.HDR_W / 2, y + L.LANE_Y0, y + L.LANE_Y0 + L.HDR_D)
            H.stamp_rect(zone, xa + c - L.PLUG_W / 2 - 0.2, xa + c + L.PLUG_W / 2 + 0.2, y + L.LANE_Y0 - L.PLUG_D, y + L.LANE_Y0)
        for F in H.F_LIST.values():
            pts, _a, _b = H.board_cable(r, F)
            zone |= H.sweep(pts, H.BW / 2 + H.CLR)
    zone |= post | wall
    out = {}
    for r, y, x0r, n in L.ROWS:
        xr8 = x0r - L.PITCH / 2
        ok = []
        for u in M2_US:
            t = H.blank()
            H.stamp_disk(t, xr8 + u, y + 5.2, L.M2_BOSS_D / 2 + 0.4)
            if not (t & zone).any():
                ok.append(u)
        out["R%d" % r] = ok
    return out


M2_US = L.M2_HOLES_R8
