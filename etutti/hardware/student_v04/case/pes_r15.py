"""R15V4 item 3: positions of the adhesive feet on the tray's underside (3M Bumpon SJ5302, D 7.94 x 2.2): >= 9 mm from every hole, pocket and recess, >= 7 mm from the tray's edge,
as far apart as possible (greedy farthest-point choice on a 1 mm grid). Writes out/pes_r15.json."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("ETUTTI_CRADLE", "1")
import layout_r4 as L
N, KEEP, EDGE = 8, 9.0, 7.0
def keepouts():
    k = []                                         # (x, y, r): the bottom face's holes and pockets
    for x, y in L.LID_POSTS: k.append((x, y, 2.2))
    for x, y in L.pick_posts(0) + L.wall_posts(0): k.append((x, y, 2.1))
    for ru in L.rulers(0):
        for mx, my in L.m2_points(ru): k.append((mx, my, 2.43))
    k.append((L.PROG[0], L.PROG[1], 1.5)); k.append((L.H101[0], L.H101[1], 4.0))
    return k
def main():
    Lx = L.length(0)
    x0, x1, y0, y1 = 2.15 + EDGE, Lx - 2.15 - EDGE, L.Y_BACK + 2.15 + EDGE, L.Y_FRONT - 2.15 - EDGE
    ko = keepouts()
    cand = [(x, y) for x in range(int(x0), int(x1) + 1) for y in range(int(y0), int(y1) + 1)
            if all(math.hypot(x - a, y - b) - r >= KEEP for a, b, r in ko)]
    pts = [min(cand, key=lambda p: (p[0] - x0) + (p[1] - y0))]
    while len(pts) < N:
        pts.append(max(cand, key=lambda c: min(math.hypot(c[0] - p[0], c[1] - p[1]) for p in pts)))
    res = {"n": N, "pos_xy": pts, "candidatos": len(cand),
           "menor_distancia_a_furo_mm": round(min(math.hypot(x - a, y - b) - r for x, y in pts for a, b, r in ko), 1),
           "menor_distancia_entre_pes_mm": round(min(math.hypot(p[0] - q[0], p[1] - q[1]) for i, p in enumerate(pts) for q in pts[i + 1:]), 1),
           "borda_mm": EDGE}
    json.dump(res, open(os.path.join(HERE, "out", "pes_r15.json"), "w"), indent=1)
    print(res)
main()
