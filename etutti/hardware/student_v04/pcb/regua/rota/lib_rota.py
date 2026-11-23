"""Biblioteca do roteador das reguas da Student V4 (R11V4).

Roteador de grade proprio (A*, 2 camadas, passo 0,05 mm, 8 direcoes), feito para
a regua (placa de 14 mm de largura): le a placa com pcbnew, monta mascaras de
obstaculo por rede (folga + meia largura), acha o caminho, escreve trilhas e vias.
Nunca move peca. Roda com o python do KiCad.
"""
import heapq
import json
import math
import os
import time

import numpy as np
import pcbnew

STEP = 0.05
MARGIN = 0.012          # folga extra contra a quantizacao da grade
CLR = 0.10              # folga minima de projeto
EDGE = 0.25             # cobre a borda
HOLE_CLR = 0.20         # furo a cobre
VIA_D, VIA_H = 0.50, 0.30
OUT_CLR = 0.30          # OUT x CLK/SER/QHP/QHP_J
OUT_SET = ("CLK", "SER", "QHP", "QHP_J")
F, B = 0, 1
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]


def mm(v):
    return pcbnew.ToMM(v)


def nm(v):
    return pcbnew.FromMM(v)


class Item:
    """Primitiva de cobre: kind 'rect' (x0,y0,x1,y1), 'circ' (x,y,r), 'seg' (x1,y1,x2,y2,r)."""
    __slots__ = ("kind", "g", "net", "layers", "what", "hole")

    def __init__(self, kind, g, net, layers, what, hole=False):
        self.kind, self.g, self.net, self.layers, self.what, self.hole = kind, g, net, layers, what, hole


class Grid:
    def __init__(self, board, x0=None, y0=None):
        bb = board.GetBoardEdgesBoundingBox()
        self.x0 = x0 if x0 is not None else math.floor((mm(bb.GetX()) - 0.5) / STEP) * STEP
        self.y0 = y0 if y0 is not None else math.floor((mm(bb.GetY()) - 0.5) / STEP) * STEP
        self.nx = int((mm(bb.GetWidth()) + 1.0) / STEP) + 2
        self.ny = int((mm(bb.GetHeight()) + 1.0) / STEP) + 2
        self.xs = self.x0 + np.arange(self.nx) * STEP
        self.ys = self.y0 + np.arange(self.ny) * STEP

    def ix(self, x):
        return int(round((x - self.x0) / STEP))

    def iy(self, y):
        return int(round((y - self.y0) / STEP))

    def pt(self, i, j):
        return self.x0 + i * STEP, self.y0 + j * STEP


def dist_prim(it, X, Y):
    k, g = it.kind, it.g
    if k == "rect":
        dx = np.maximum(np.maximum(g[0] - X, X - g[2]), 0.0)
        dy = np.maximum(np.maximum(g[1] - Y, Y - g[3]), 0.0)
        return np.hypot(dx, dy)
    if k == "circ":
        return np.maximum(np.hypot(X - g[0], Y - g[1]) - g[2], 0.0)
    x1, y1, x2, y2, r = g
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        t = 0.0 * X
    else:
        t = np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0.0, 1.0)
    return np.maximum(np.hypot(X - (x1 + t * dx), Y - (y1 + t * dy)) - r, 0.0)


def prim_bbox(it):
    k, g = it.kind, it.g
    if k == "rect":
        return g[0], g[1], g[2], g[3]
    if k == "circ":
        return g[0] - g[2], g[1] - g[2], g[0] + g[2], g[1] + g[2]
    r = g[4]
    return min(g[0], g[2]) - r, min(g[1], g[3]) - r, max(g[0], g[2]) + r, max(g[1], g[3]) + r


def stamp(grid, mask, it, d):
    """Marca em mask as celulas a menos de d do item."""
    x0, y0, x1, y1 = prim_bbox(it)
    i0 = max(grid.ix(x0 - d) - 1, 0)
    i1 = min(grid.ix(x1 + d) + 2, grid.nx)
    j0 = max(grid.iy(y0 - d) - 1, 0)
    j1 = min(grid.iy(y1 + d) + 2, grid.ny)
    if i0 >= i1 or j0 >= j1:
        return
    X, Y = np.meshgrid(grid.xs[i0:i1], grid.ys[j0:j1])
    mask[j0:j1, i0:i1] |= dist_prim(it, X, Y) < d


def read_items(board):
    """Todos os itens de cobre/furo da placa (pads, trilhas, vias, furos NPTH)."""
    items = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetname()
            bb = p.GetBoundingBox()
            rect = (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetX() + bb.GetWidth()), mm(bb.GetY() + bb.GetHeight()))
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                r = mm(p.GetDrillSize().x) / 2
                items.append(Item("circ", (mm(p.GetX()), mm(p.GetY()), r), "", (F, B), "npth", hole=True))
                continue
            if not p.IsOnCopperLayer():
                continue
            ls = tuple(i for i, L in enumerate(LAYERS) if p.IsOnLayer(L))
            it = Item("rect", rect, net, ls, "pad:%s.%s" % (fp.GetReference(), p.GetNumber()))
            items.append(it)
    for t in board.GetTracks():
        net = t.GetNetname()
        if t.Type() == pcbnew.PCB_VIA_T:
            items.append(Item("circ", (mm(t.GetX()), mm(t.GetY()), mm(t.GetWidth(LAYERS[0])) / 2), net, (F, B), "via"))
        else:
            li = F if t.GetLayer() == pcbnew.F_Cu else B
            s, e = t.GetStart(), t.GetEnd()
            items.append(Item("seg", (mm(s.x), mm(s.y), mm(e.x), mm(e.y), mm(t.GetWidth()) / 2), net, (li,), "track"))
    return items


def read_keepouts(board):
    """Areas de proibicao de trilha/via (regra de area): lista de (rect, layers)."""
    ks = []
    for z in board.Zones():
        if not z.GetIsRuleArea():
            continue
        if not (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()):
            continue
        bb = z.GetBoundingBox()
        r = (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetX() + bb.GetWidth()), mm(bb.GetY() + bb.GetHeight()))
        ls = tuple(i for i, L in enumerate(LAYERS) if z.IsOnLayer(L))
        ks.append((r, ls, z.GetDoNotAllowTracks(), z.GetDoNotAllowVias()))
    return ks


def outline_chain(board):
    poly = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(poly, False)
    ch = poly.Outline(0)
    return [(mm(ch.CPoint(i).x), mm(ch.CPoint(i).y)) for i in range(ch.PointCount())]


def outside_mask(grid, pts):
    """Celulas fora do contorno (par-impar por varredura)."""
    inside = np.zeros((grid.ny, grid.nx), bool)
    n = len(pts)
    for j in range(grid.ny):
        y = grid.ys[j] + 1e-7
        xs = []
        for k in range(n):
            (xa, ya), (xb, yb) = pts[k], pts[(k + 1) % n]
            if (ya <= y < yb) or (yb <= y < ya):
                xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for a in range(0, len(xs) - 1, 2):
            i0 = int(math.ceil((xs[a] - grid.x0) / STEP - 1e-9))
            i1 = int(math.floor((xs[a + 1] - grid.x0) / STEP + 1e-9))
            inside[j, max(i0, 0):i1 + 1] = True
    return ~inside


def edge_items(pts):
    n = len(pts)
    return [Item("seg", (pts[k][0], pts[k][1], pts[(k + 1) % n][0], pts[(k + 1) % n][1], 0.0), "", (F, B), "edge")
            for k in range(n)]


class Ctx:
    """Contexto de roteamento: placa + grade + itens estaticos."""

    def __init__(self, board):
        self.b = board
        self.g = Grid(board)
        self.pts = outline_chain(board)
        self.out_mask = outside_mask(self.g, self.pts)
        self.edges = edge_items(self.pts)
        self.keepouts = read_keepouts(board)
        self.bucket = None
        self.esc_ids = set()
        self.esc_pads = set()
        self.refresh()

    def refresh(self):
        self.items = read_items(self.b)

    # ---------------- mascaras ----------------
    def masks(self, net, w):
        """(bloq[F], bloq[B], viabloq) para rotear 'net' com trilha de largura w."""
        g = self.g
        bl = [np.zeros((g.ny, g.nx), bool), np.zeros((g.ny, g.nx), bool)]
        vb = [np.zeros((g.ny, g.nx), bool), np.zeros((g.ny, g.nx), bool)]
        h = w / 2
        rv = VIA_D / 2
        for L in (F, B):
            bl[L] |= self.out_mask
            vb[L] |= self.out_mask
        for e in self.edges:
            for L in (F, B):
                stamp(g, bl[L], e, EDGE + h)
                stamp(g, vb[L], e, EDGE + rv)
        for (r, ls, nt, nv) in self.keepouts:
            it = Item("rect", r, "", ls, "keepout")
            for L in ls:
                if nt:
                    stamp(g, bl[L], it, h + 0.005)
                if nv:
                    stamp(g, vb[L], it, rv + 0.005)
        for it in self.items:
            if it.net == net and not it.hole and it.net != "":
                # cobre da mesma rede nao e obstaculo; mas via nunca sobre pad (qualquer rede)
                if it.what.startswith("pad"):
                    for L in it.layers:
                        stamp(g, vb[L], it, rv - 0.02)
                elif it.what == "via":
                    for L in (F, B):
                        stamp(g, vb[L], it, 0.31)
                continue
            if it.hole:
                dt = it.g[2] + HOLE_CLR + h + MARGIN
                dv = it.g[2] + max(HOLE_CLR + rv, 0.25 + VIA_H / 2) + MARGIN
                for L in (F, B):
                    stamp(g, bl[L], it, dt)
                    stamp(g, vb[L], it, dv)
                continue
            c = CLR
            if (net == "OUT" and it.net in OUT_SET) or (net in OUT_SET and it.net == "OUT" and it.what != "via"):
                c = OUT_CLR
            for L in it.layers:
                stamp(g, bl[L], it, c + h + MARGIN)
                stamp(g, vb[L], it, c + rv + MARGIN)
                if it.what.startswith("pad"):
                    # via nao encosta em pad de outra rede nem em area de pad
                    pass
        viab = vb[F] | vb[B] | bl[F] * False
        return bl, viab

    # ---------------- A* ----------------
    def route(self, net, w, tree, target_cells, target_xy, layer_mult=(1.0, 1.0), via_cost=60.0,
              hw=3.0, maxexp=int(os.environ.get("MAXEXP","1000000")), via_ok=True, extra=None):
        """tree: lista de (L,i,j) de origem. target_cells: set de (L,i,j). Devolve caminho [(L,i,j)] ou None."""
        g = self.g
        bl, viab = self.masks(net, w)
        key = (net, w)
        free = [~bl[F], ~bl[B]]
        free_via = ~viab
        # celulas alvo precisam ser livres (a trilha termina nelas)
        tg = {c for c in target_cells if free[c[0]][c[2], c[1]]}
        if not tg:
            return None, "alvo sem celula livre"
        src = [c for c in tree if free[c[0]][c[2], c[1]]]
        if not src:
            return None, "origem sem celula livre"
        if target_xy is None:
            tix = tiy = 0
            hw = 0.0
        else:
            tix, tiy = g.ix(target_xy[0]), g.iy(target_xy[1])
        DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
        COST = [1.0, 1.41421, 1.0, 1.41421, 1.0, 1.41421, 1.0, 1.41421]
        nx, ny = g.nx, g.ny

        def hfun(i, j):
            dx, dy = abs(i - tix), abs(j - tiy)
            return (max(dx, dy) + 0.41421 * min(dx, dy)) * 0.9

        best = {}
        parent = {}
        heap = []
        cnt = 0
        for (L, i, j) in src:
            k = (L, i, j, 8)
            best[k] = 0.0
            heapq.heappush(heap, (hw * hfun(i, j), 0.0, cnt, k))
            cnt += 1
            parent[k] = None
        exp = 0
        while heap:
            f, gc, _, k = heapq.heappop(heap)
            if best.get(k, 1e18) < gc - 1e-9:
                continue
            L, i, j, d = k
            if (L, i, j) in tg:
                path = []
                kk = k
                while kk is not None:
                    path.append((kk[0], kk[1], kk[2]))
                    kk = parent[kk]
                path.reverse()
                return path, "ok"
            exp += 1
            if exp > maxexp:
                return None, "limite de expansoes"
            lm = layer_mult[L]
            fr = free[L]
            for nd in range(8):
                ni, nj = i + DIRS[nd][0], j + DIRS[nd][1]
                if ni < 0 or nj < 0 or ni >= nx or nj >= ny or not fr[nj, ni]:
                    continue
                if nd % 2 == 1:
                    # diagonal: as duas celulas ortogonais tambem precisam estar livres (evita cortar quina)
                    if not (fr[j, ni] and fr[nj, i]):
                        continue
                turn = 0.0
                if d != 8:
                    a = abs(nd - d)
                    a = min(a, 8 - a)
                    if a == 1:
                        turn = 6.0
                    elif a == 2:
                        turn = 15.0
                    elif a > 2:
                        continue
                ng = gc + COST[nd] * lm + turn
                if extra is not None:
                    ng += extra[L][nj, ni]
                nk = (L, ni, nj, nd)
                if ng < best.get(nk, 1e18) - 1e-9:
                    best[nk] = ng
                    parent[nk] = k
                    heapq.heappush(heap, (ng + hw * hfun(ni, nj), ng, cnt, nk))
                    cnt += 1
            if via_ok and free_via[j, i] and free[1 - L][j, i]:
                nk = (1 - L, i, j, 8)
                ng = gc + via_cost
                if ng < best.get(nk, 1e18) - 1e-9:
                    best[nk] = ng
                    parent[nk] = k
                    heapq.heappush(heap, (ng + hw * hfun(i, j), ng, cnt, nk))
                    cnt += 1
        return None, "sem caminho"

    # ---------------- escrita ----------------
    def write_path(self, net, w, path):
        g = self.g
        b = self.b
        ni = b.FindNet(net)
        # separa em trechos por camada; vias nas trocas
        pts = [(L, i, j) for (L, i, j) in path]
        # remove repeticoes
        runs = []
        cur = [pts[0]]
        for p in pts[1:]:
            if p[0] != cur[-1][0]:
                runs.append(cur)
                cur = [p]
            else:
                cur.append(p)
        runs.append(cur)
        made = []
        for r in runs:
            L = r[0][0]
            # funde pontos colineares
            simp = [r[0]]
            for k in range(1, len(r)):
                if len(simp) >= 2:
                    a, c = simp[-2], simp[-1]
                    d1 = (c[1] - a[1], c[2] - a[2])
                    d2 = (r[k][1] - c[1], r[k][2] - c[2])
                    if d1[0] * d2[1] - d1[1] * d2[0] == 0 and (d1[0] * d2[0] + d1[1] * d2[1]) > 0:
                        simp[-1] = r[k]
                        continue
                if r[k][1:] != simp[-1][1:]:
                    simp.append(r[k])
            for a, c in zip(simp, simp[1:]):
                x1, y1 = g.pt(a[1], a[2])
                x2, y2 = g.pt(c[1], c[2])
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I(nm(x1), nm(y1)))
                t.SetEnd(pcbnew.VECTOR2I(nm(x2), nm(y2)))
                t.SetWidth(nm(w))
                t.SetLayer(LAYERS[L])
                t.SetNet(ni)
                b.Add(t)
                made.append(t)
                if self.bucket is not None:
                    self.bucket.append(t)
        for a, c in zip(pts, pts[1:]):
            if a[0] != c[0]:
                x, y = g.pt(a[1], a[2])
                self.add_via(net, x, y)
        return made

    def add_via(self, net, x, y):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pcbnew.VECTOR2I(nm(x), nm(y)))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        try:
            v.SetWidth(LAYERS[0], nm(VIA_D))
            v.SetWidth(LAYERS[1], nm(VIA_D))
        except TypeError:
            v.SetWidth(nm(VIA_D))
        v.SetDrill(nm(VIA_H))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.b.FindNet(net))
        self.b.Add(v)
        if self.bucket is not None:
            self.bucket.append(v)
        return v

    # ---------------- arvore da rede ----------------
    def net_pads(self, net):
        res = []
        for fp in self.b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() == net and p.IsOnCopperLayer() and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                    bb = p.GetBoundingBox()
                    res.append((fp.GetReference() + "." + p.GetNumber(),
                                (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetX() + bb.GetWidth()), mm(bb.GetY() + bb.GetHeight())),
                                tuple(i for i, L in enumerate(LAYERS) if p.IsOnLayer(L)),
                                (mm(p.GetX()), mm(p.GetY()))))
        return res

    def pad_cells(self, rect, layers):
        g = self.g
        i0, i1 = g.ix(rect[0]), g.ix(rect[2])
        j0, j1 = g.iy(rect[1]), g.iy(rect[3])
        cells = set()
        for L in layers:
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    x, y = g.pt(i, j)
                    if rect[0] - 1e-9 <= x <= rect[2] + 1e-9 and rect[1] - 1e-9 <= y <= rect[3] + 1e-9:
                        cells.add((L, i, j))
        return cells

    def track_cells(self, net):
        g = self.g
        cells = set()
        for t in self.b.GetTracks():
            if t.GetNetname() != net:
                continue
            if t.Type() == pcbnew.PCB_VIA_T:
                i, j = g.ix(mm(t.GetX())), g.iy(mm(t.GetY()))
                cells.add((F, i, j))
                cells.add((B, i, j))
                continue
            L = F if t.GetLayer() == pcbnew.F_Cu else B
            s, e = t.GetStart(), t.GetEnd()
            i0, j0 = g.ix(mm(s.x)), g.iy(mm(s.y))
            i1, j1 = g.ix(mm(e.x)), g.iy(mm(e.y))
            n = max(abs(i1 - i0), abs(j1 - j0), 1)
            for k in range(n + 1):
                cells.add((L, i0 + round((i1 - i0) * k / n), j0 + round((j1 - j0) * k / n)))
        return cells

    def connected_pads(self, net):
        """Quais pads da rede ja tocam a arvore de trilhas (por celulas)."""
        tc = self.track_cells(net)
        done = set()
        for ref, rect, ls, c in self.net_pads(net):
            if self.pad_cells(rect, ls) & tc:
                done.add(ref)
        return done, tc


def load_state(path):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {}


def save_state(path, st):
    json.dump(st, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def components(ctx, net):
    """Componentes conectados do cobre da rede: lista de [cells_todas, refs_de_pad, cells_para_rotear].
    Os escapes (pad -> trilha curta -> via) so oferecem ao A* o lado F.Cu da via."""
    b = ctx.b
    g = ctx.g
    objs = []
    for ref, rect, ls, c in ctx.net_pads(net):
        cells = ctx.pad_cells(rect, ls)
        objs.append((cells, [ref], set() if ref in ctx.esc_pads else cells))
    for t in b.GetTracks():
        if t.GetNetname() != net:
            continue
        esc = t.m_Uuid.AsString() in ctx.esc_ids
        cells = set()
        if t.Type() == pcbnew.PCB_VIA_T:
            i, j = g.ix(mm(t.GetX())), g.iy(mm(t.GetY()))
            cells = {(F, i, j), (B, i, j)}
            objs.append((cells, [], {(F, i, j)} if esc else cells))
            continue
        L = F if t.GetLayer() == pcbnew.F_Cu else B
        s, e = t.GetStart(), t.GetEnd()
        i0, j0 = g.ix(mm(s.x)), g.iy(mm(s.y))
        i1, j1 = g.ix(mm(e.x)), g.iy(mm(e.y))
        n = max(abs(i1 - i0), abs(j1 - j0), 1)
        for k in range(n + 1):
            cells.add((L, i0 + round((i1 - i0) * k / n), j0 + round((j1 - j0) * k / n)))
        objs.append((cells, [], set() if esc else cells))
    parent = list(range(len(objs)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    owner = {}
    for k, o in enumerate(objs):
        for c in o[0]:
            if c in owner:
                parent[find(k)] = find(owner[c])
            else:
                owner[c] = k
    comps = {}
    for k, o in enumerate(objs):
        r = find(k)
        cc = comps.setdefault(r, [set(), [], set()])
        cc[0] |= o[0]
        cc[1] += o[1]
        cc[2] |= o[2]
    return list(comps.values())


def lane_cost(ctx, lane_v, lam=1.0, cap=4.0, yref=17.0):
    """Custo extra por passo, proporcional ao desvio da faixa preferida (v = y - 17)."""
    dev = np.minimum(np.abs(ctx.g.ys - (yref + lane_v)), cap) * lam
    a = np.repeat(dev[:, None], ctx.g.nx, axis=1).astype(np.float32)
    return [a, a]
