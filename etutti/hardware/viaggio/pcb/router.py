"""Grid router for the Viaggio board (two routing layers, F.Cu and B.Cu).

The eTuttino's router (etutti/hardware/build_pcb.py) adapted, not imported:
that one keeps one global track width (its HW_MAX); the Viaggio needs 0.1 mm
tracks between the BGA's balls and 0.2 mm elsewhere in the same search. Here
the grid keeps, per layer, cell and track half-width class, which net's halo
(copper + clearance + that half-width) covers it, computed with exact distances
when the copper is marked, so a route can be thin inside a region (the BGA)
and normal outside it, and a via finds its spot the same way.

Pure Python + numpy (KiCad 10's python has both); no pcbnew in here.
"""
import heapq
import math

import numpy as np

FREE, HARD = -1, -2
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
TURN_COST = {0: 0.0, 1: 0.10, 2: 0.40}


class Grid:
    def __init__(self, x0, y0, x1, y1, pitch, clear, via_d, via_clear, slack=0.02, classes=(0.05, 0.1)):
        self.p = pitch
        self.ox, self.oy = x0, y0
        self.W = int(round((x1 - x0) / pitch)) + 1
        self.H = int(round((y1 - y0) / pitch)) + 1
        self.clear = clear
        self.via_r = via_d / 2
        self.via_clear = via_clear
        self.slack = slack
        self.owner = np.full((2, self.H, self.W), FREE, np.int32)
        self.copper = np.full((2, self.H, self.W), FREE, np.int32)
        self.novia = np.zeros((self.H, self.W), bool)
        self.viacell = np.full((self.H, self.W), FREE, np.int32)   # net id of the via centred on a cell
        self.res = np.full((2, self.H, self.W), FREE, np.int32)   # temporary reservations (net id)
        # halo per track half-width (and "via"): a centre-line / via centre in a foreign cell breaks clearance
        self.reach = {hw: clear + hw + slack for hw in classes}
        self.reach["via"] = via_clear + via_d / 2 + slack
        self.cls = {k: np.full((2, self.H, self.W), FREE, np.int32) for k in self.reach}
        self.attach = {}          # (layer, iy, ix) -> (x, y) where a route may end on that copper
        self.items = {}           # item key -> set of (layer, iy, ix)
        self.net_ids, self.net_names = {}, []
        xs = x0 + np.arange(self.W) * pitch
        ys = y0 + np.arange(self.H) * pitch
        self.X, self.Y = np.meshgrid(xs, ys)

    def nid(self, name):
        if name not in self.net_ids:
            self.net_ids[name] = len(self.net_names)
            self.net_names.append(name)
        return self.net_ids[name]

    def x(self, ix):
        return self.ox + ix * self.p

    def y(self, iy):
        return self.oy + iy * self.p

    def cell(self, x, y):
        return int(round((y - self.oy) / self.p)), int(round((x - self.ox) / self.p))

    def _win(self, x0, y0, x1, y1, reach):
        ix0 = max(0, int(math.floor((x0 - reach - self.ox) / self.p)))
        iy0 = max(0, int(math.floor((y0 - reach - self.oy) / self.p)))
        ix1 = min(self.W - 1, int(math.ceil((x1 + reach - self.ox) / self.p)))
        iy1 = min(self.H - 1, int(math.ceil((y1 + reach - self.oy) / self.p)))
        return iy0, iy1 + 1, ix0, ix1 + 1

    @staticmethod
    def _claim_arr(arr, layers, sl, mask, nid):
        for li in layers:
            o = arr[li][sl]
            if nid == HARD:
                o[mask] = HARD
            else:
                o[mask & (o == FREE)] = nid
                o[mask & (o != nid) & (o != FREE)] = HARD

    def _claim(self, layers, sl, mask, nid):
        self._claim_arr(self.owner, layers, sl, mask, nid)

    def _claim_d(self, layers, sl, dd, nid, clear):
        """dd = distance from each cell centre to the copper's surface (< 0 inside)."""
        self._claim_arr(self.owner, layers, sl, dd < clear, nid)
        for k, r in self.reach.items():
            rr = r - self.clear + clear
            self._claim_arr(self.cls[k], layers, sl, dd < rr, nid)

    def _copper(self, layers, sl, mask, nid, item, attach_fn):
        iy0, ix0 = sl[0].start, sl[1].start
        cys, cxs = np.nonzero(mask)
        for li in layers:
            self.copper[li][sl][mask] = nid
            for cy, cx in zip(cys.tolist(), cxs.tolist()):
                key = (li, iy0 + cy, ix0 + cx)
                self.attach[key] = attach_fn(self.x(ix0 + cx), self.y(iy0 + cy))
                if item is not None:
                    self.items.setdefault(item, set()).add(key)

    def mark_segment(self, layers, a, b, half, net, item=None, clear=None):
        clear = self.clear if clear is None else clear
        nid = HARD if net is None else self.nid(net)
        reach = half + clear + max(self.reach.values())
        iy0, iy1, ix0, ix1 = self._win(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]), reach)
        if iy0 >= iy1 or ix0 >= ix1:
            return
        sl = (slice(iy0, iy1), slice(ix0, ix1))
        X, Y = self.X[sl], self.Y[sl]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = np.zeros_like(X) if L2 == 0 else np.clip(((X - a[0]) * dx + (Y - a[1]) * dy) / L2, 0, 1)
        px, py = a[0] + t * dx, a[1] + t * dy
        d = np.hypot(X - px, Y - py)
        self._claim_d(layers, sl, d - half, nid, clear)
        if nid != HARD:
            def att(x, y):
                tt = 0.0 if L2 == 0 else min(1.0, max(0.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
                return (round(a[0] + tt * dx, 4), round(a[1] + tt * dy, 4))
            self._copper(layers, sl, d <= max(half - 0.02, 0.0), nid, item, att)

    def mark_pad(self, layers, cx, cy, hw, hh, net, item=None, circle=False, smd=True, center=None):
        """Axis-aligned rectangle (or circle of radius hw) of copper; a route ends at its centre."""
        nid = HARD if net is None else self.nid(net)
        reach = max(self.reach.values()) + 0.1
        sl = self._win(cx - hw, cy - hh, cx + hw, cy + hh, reach)
        sl = (slice(sl[0], sl[1]), slice(sl[2], sl[3]))
        X, Y = self.X[sl], self.Y[sl]
        if circle:
            d = np.hypot(X - cx, Y - cy) - hw
        else:
            ddx = np.maximum(np.abs(X - cx) - hw, 0)
            ddy = np.maximum(np.abs(Y - cy) - hh, 0)
            d = np.hypot(ddx, ddy)
            inside = np.maximum(np.abs(X - cx) - hw, np.abs(Y - cy) - hh)
            d = np.where(inside < 0, inside, d)
        self._claim_d(layers, sl, d, nid, self.clear)
        if smd:
            self.novia[sl][d < self.via_r + self.clear] = True
        if nid != HARD:
            c = center or (round(cx, 4), round(cy, 4))
            self._copper(layers, sl, d <= -0.03, nid, item, lambda x, y: c)

    def mark_hole(self, x, y, r):
        sl = self._win(x, y, x, y, r + max(self.reach.values()))
        sl = (slice(sl[0], sl[1]), slice(sl[2], sl[3]))
        d = np.hypot(self.X[sl] - x, self.Y[sl] - y)
        self._claim_d((0, 1), sl, d - r + self.clear, HARD, self.clear)
        self.novia[sl][d < r + self.via_r] = True

    def block_rect(self, layers, x0, y0, x1, y1, novia=True):
        sl = self._win(x0, y0, x1, y1, 0)
        sl = (slice(sl[0], sl[1]), slice(sl[2], sl[3]))
        m = (self.X[sl] >= x0) & (self.X[sl] <= x1) & (self.Y[sl] >= y0) & (self.Y[sl] <= y1)
        self._claim(layers, sl, m, HARD)
        for k in self.cls:
            self._claim_arr(self.cls[k], layers, sl, m, HARD)
        if novia:
            self.novia[sl][m] = True

    def reserve(self, layers, x0, y0, x1, y1, net):
        """Keep a box for one net (others may not route there) until release()."""
        sl = self._win(x0, y0, x1, y1, 0)
        sl = (slice(sl[0], sl[1]), slice(sl[2], sl[3]))
        m = (self.X[sl] >= x0) & (self.X[sl] <= x1) & (self.Y[sl] >= y0) & (self.Y[sl] <= y1)
        for li in layers:
            self.res[li][sl][m] = self.nid(net)

    def release(self, net=None):
        if net is None:
            self.res[...] = FREE
        else:
            self.res[self.res == self.nid(net)] = FREE

    def _klass(self, hw):
        ks = [k for k in self.reach if k != "via" and k >= hw - 1e-9]
        if not ks:
            raise ValueError("no halo class for half-width %s" % hw)
        return min(ks)

    # ------------------------------------------------------------------ search
    def _dilate(self, m, r_cells_f):
        r = int(math.ceil(r_cells_f))
        out = m.copy()
        H, W = m.shape
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if (dx or dy) and math.hypot(dx, dy) <= r_cells_f:
                    ys0, ys1 = max(0, -dy), min(H, H - dy)
                    xs0, xs1 = max(0, -dx), min(W, W - dx)
                    out[ys0:ys1, xs0:xs1] |= m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
        return out

    def search(self, net, sources, targets, hw, thin_hw=None, thin_fn=None, window=None, via_cost=2.0,
               allow_via=True, layers_ok=(0, 1), max_expand=3_000_000, extra_ok=()):
        """sources / targets: sets of (layer, iy, ix). Returns the state path or None."""
        nid = self.nid(net)
        allc = list(sources) + list(targets)
        if window is None:
            ys = [c[1] for c in allc]
            xs = [c[2] for c in allc]
            m = int(6.0 / self.p)
            window = (max(0, min(ys) - m), min(self.H, max(ys) + m + 1), max(0, min(xs) - m), min(self.W, max(xs) + m + 1))
        wy0, wy1, wx0, wx1 = window
        sl = (slice(wy0, wy1), slice(wx0, wx1))
        Hh, Ww = wy1 - wy0, wx1 - wx0
        ok_ids = list({FREE, nid} | {self.nid(n) for n in extra_ok})

        def free_in(arr, li):
            o = arr[li][sl]
            m = np.isin(o, ok_ids)
            rs = self.res[li][sl]
            return m & ((rs == FREE) | (rs == nid))
        usable = []
        for li in (0, 1):
            u = free_in(self.cls[self._klass(hw)], li)
            if thin_hw is not None and thin_fn is not None:
                thin = thin_fn(self.X[sl], self.Y[sl])
                u = np.where(thin, free_in(self.cls[self._klass(thin_hw)], li), u)
            if li not in layers_ok:
                u[:] = False
            usable.append(u)
        if allow_via:
            vo = free_in(self.cls["via"], 0) & free_in(self.cls["via"], 1) & ~self.novia[sl]
        else:
            vo = np.zeros((Hh, Ww), bool)
        vo |= self.viacell[sl] == nid          # through one of its own vias, always
        U0 = usable[0].ravel().tolist()
        U1 = usable[1].ravel().tolist()
        U = (U0, U1)
        VO = vo.ravel().tolist()
        tset = {(l, (iy - wy0) * Ww + (ix - wx0)) for l, iy, ix in targets
                if wy0 <= iy < wy1 and wx0 <= ix < wx1}
        if not tset:
            return None
        tys = [i // Ww for _, i in tset]
        txs = [i % Ww for _, i in tset]
        bx0, bx1, by0, by1 = min(txs), max(txs), min(tys), max(tys)
        P = self.p

        def h(ix, iy):
            dx = max(bx0 - ix, 0, ix - bx1)
            dy = max(by0 - iy, 0, iy - by1)
            return (max(dx, dy) + 0.4142 * min(dx, dy)) * P

        g, parent, heap = {}, {}, []
        for l, iy, ix in sources:
            if not (wy0 <= iy < wy1 and wx0 <= ix < wx1):
                continue
            i = (iy - wy0) * Ww + (ix - wx0)
            s = (l, i, 8)
            g[s] = 0.0
            parent[s] = None
            heapq.heappush(heap, (h(i % Ww, i // Ww), 0.0, s))
        n = 0
        while heap:
            f, gc, s = heapq.heappop(heap)
            if gc > g.get(s, 1e18):
                continue
            l, i, d = s
            if (l, i) in tset:
                path = []
                while s is not None:
                    path.append(s)
                    s = parent[s]
                return [(l2, wy0 + i2 // Ww, wx0 + i2 % Ww) for l2, i2, _ in path[::-1]]
            n += 1
            if n > max_expand:
                return None
            ix, iy = i % Ww, i // Ww
            Ul = U[l]
            for nd, (dx, dy) in enumerate(DIRS):
                if d != 8:
                    turn = min((nd - d) % 8, (d - nd) % 8)
                    if turn > 2:
                        continue
                    tc = TURN_COST[turn]
                else:
                    tc = 0.0
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < Ww and 0 <= jy < Hh):
                    continue
                j = jy * Ww + jx
                if not Ul[j] and (l, j) not in tset:
                    continue
                if dx and dy and not (Ul[iy * Ww + jx] and Ul[jy * Ww + ix]):
                    continue
                ng = gc + (1.41421 if dx and dy else 1.0) * P + tc
                ns = (l, j, nd)
                if ng < g.get(ns, 1e18):
                    g[ns] = ng
                    parent[ns] = s
                    heapq.heappush(heap, (ng + h(jx, jy), ng, ns))
            if VO[i]:
                ns = (1 - l, i, 8)
                if U[1 - l][i] or (1 - l, i) in tset:
                    ng = gc + via_cost
                    if ng < g.get(ns, 1e18):
                        g[ns] = ng
                        parent[ns] = s
                        heapq.heappush(heap, (ng + h(ix, iy), ng, ns))
        return None
