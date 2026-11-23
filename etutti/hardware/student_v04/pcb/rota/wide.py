"""Roteador de grade proprio para as redes de corrente e para o que o Freerouting nao fecha (python do KiCad: pcbnew + numpy).
Grade de 0,1 mm, 2 camadas (F.Cu, B.Cu), 8 direcoes, vias 0,5 / 0,3. Mascaras de obstaculo por camada, com a folga de cada par de redes
(post.folga), meia largura da trilha, furo da via a 0,2 do cobre, borda a 0,3, areas de proibicao. So le a placa e escreve trilhas e vias:
nunca move peca. Uso como biblioteca (route_net) ou:  python wide.py REDE largura [pads 'U1.2,C3.1' ...]
"""
import heapq, math, sys, os
import numpy as np
from lib import *
import pcbnew
import fanout as F
import post as P

RES = 0.05
X0, Y0, X1, Y1 = 0.0, 0.0, 80.0, 100.0
NX, NY = int((X1-X0)/RES)+1, int((Y1-Y0)/RES)+1
GX = X0 + np.arange(NX)*RES
GY = Y0 + np.arange(NY)*RES
MARG = 0.03

def _dist_poly(xs, ys, poly):
    """distancia (0 dentro) de uma grade de pontos a um poligono; xs (1,n), ys (m,1)"""
    d = np.full((ys.shape[0], xs.shape[1]), 1e9)
    n = len(poly)
    inside = np.zeros(d.shape, bool)
    for i in range(n):
        ax, ay = poly[i]; bx, by = poly[(i+1) % n]
        dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
        if L2 > 0:
            t = np.clip(((xs-ax)*dx+(ys-ay)*dy)/L2, 0, 1)
        else:
            t = np.zeros(d.shape)
        d = np.minimum(d, np.hypot(xs-ax-t*dx, ys-ay-t*dy))
        cond = ((ay > ys) != (by > ys)) & (xs < (bx-ax)*(ys-ay)/((by-ay) if by != ay else 1e-12)+ax)
        inside ^= cond
    d[inside] = 0.0
    return d

def _dist_seg(xs, ys, a, b):
    ax, ay = a; bx, by = b; dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
    t = np.clip(((xs-ax)*dx+(ys-ay)*dy)/L2, 0, 1) if L2 > 0 else np.zeros((ys.shape[0], xs.shape[1]))
    return np.hypot(xs-ax-t*dx, ys-ay-t*dy)

def stamp(mask, o, margem):
    """marca em mask as celulas a menos de `margem` do cobre/obstaculo o"""
    x0, y0, x1, y1 = o.bb
    i0 = max(0, int((x0-margem-X0)/RES)-1); i1 = min(NX, int((x1+margem-X0)/RES)+2)
    j0 = max(0, int((y0-margem-Y0)/RES)-1); j1 = min(NY, int((y1+margem-Y0)/RES)+2)
    if i0 >= i1 or j0 >= j1: return
    xs = GX[i0:i1][None, :]; ys = GY[j0:j1][:, None]
    if o.kind == 'poly': d = _dist_poly(xs, ys, o.g)
    elif o.kind == 'seg':
        (a, b, w) = o.g; d = _dist_seg(xs, ys, a, b) - w/2
    else:
        cx, cy, r = o.g; d = np.hypot(xs-cx, ys-cy) - r
    mask[j0:j1, i0:i1] |= d < margem

def borda(m):
    """True onde o ponto esta a menos de m da borda (contorno 2,45..77,5 x 2,45..97,55 com cantos R3)"""
    xs = GX[None, :]; ys = GY[:, None]
    x0, y0, x1, y1 = F.EDGE[0]+m, F.EDGE[1]+m, F.EDGE[2]-m, F.EDGE[3]-m
    ruim = (xs < x0) | (xs > x1) | (ys < y0) | (ys > y1)
    r = max(F.RCANTO-m, 0.0)
    for cx, cy, sx, sy in ((x0+r, y0+r, -1, -1), (x1-r, y0+r, 1, -1), (x0+r, y1-r, -1, 1), (x1-r, y1-r, 1, 1)):
        ruim |= ((xs-cx)*sx > 0) & ((ys-cy)*sy > 0) & (np.hypot(xs-cx, ys-cy) > r)
    return ruim

class Roteador:
    def __init__(self, b):
        self.b = b
        self.obs, self.vias, self.pads_pl = F.carrega(b)     # obs: pads, vias, trilhas, buracos, areas de proibicao
        # recortes em Edge.Cuts (fenda do cabo da tela): ja como area de proibicao nos rule areas
    def masks(self, net, w):
        """(mascara de trilha F, B; mascara de via)  True = proibido"""
        mt = {'F': np.zeros((NY, NX), bool), 'B': np.zeros((NY, NX), bool)}
        mv = np.zeros((NY, NX), bool)
        for o in self.obs:
            if o.net == net: continue
            if o.net == '#keepout':
                for k in ('F', 'B'): stamp(mt[k], o, w/2+MARG+0.3)
                stamp(mv, o, VIA_R+MARG+0.3); continue
            f = P.folga(net, o.net) if o.net else 0.1
            if o.kind == 'circ' and o.ref == 'via':
                cx, cy, r = o.g
                rr = max(r+f, 0.35)
                big = F.Obs('circ', o.net, (cx, cy, rr), 0.0, o.camadas, 'via')
                for k in ('F', 'B'): stamp(mt[k], big, w/2+MARG)
                stamp(mv, F.Obs('circ', o.net, (cx, cy, 0.45), 0.0, o.camadas, 'via'), VIA_R+MARG)     # via x via: centros a >= 0,7
                continue
            for k in ('F', 'B'):
                if k in o.camadas: stamp(mt[k], o, w/2+f+MARG)
            # via contra cobre de outra rede (furo a 0,2 do cobre)
            if 'B' in o.camadas or 'F' in o.camadas:
                stamp(mv, o, max(VIA_R+f, 0.35)+MARG)
        bd = borda(0.3+w/2);
        for k in ('F', 'B'): mt[k] |= bd
        mv |= borda(0.3+VIA_R)
        return mt, mv

VIA_R = 0.25

def pad_poly(b, ref, num):
    fp = b.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == num:
            lay = pcbnew.B_Cu if p.GetLayerSet().Contains(pcbnew.B_Cu) else pcbnew.F_Cu
            o = p.GetEffectivePolygon(lay).Outline(0)
            return [(F.mmv(o.CPoint(i).x), F.mmv(o.CPoint(i).y)) for i in range(o.PointCount())], ('B' if lay == pcbnew.B_Cu else 'F')
    raise KeyError((ref, num))

def celulas_poly(poly, layer, mt, shrink=0.05):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    i0 = int(math.ceil((min(xs)-X0)/RES)); i1 = int((max(xs)-X0)/RES)
    j0 = int(math.ceil((min(ys)-Y0)/RES)); j1 = int((max(ys)-Y0)/RES)
    out = []
    for i in range(i0, i1+1):
        for j in range(j0, j1+1):
            if F.pt_poly(GX[i], GY[j], poly) == 0.0 and F.pt_poly(GX[i], GY[j], poly) == 0.0:
                # ponto realmente dentro (nao so na borda): exige distancia ao contorno >= shrink se o pad for largo
                out.append((layer, i, j))
    return out

NB = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
VIA_CUSTO = 4.0

def astar(mt, mv, origens, alvos, alvo_xy, camada_custo=(1.0, 1.0), limite=4000000, zi=None, MT=None):
    """origens/alvos: conjuntos de (camada 'F'|'B', i, j). Retorna lista de nos."""
    lid = {'F': 0, 'B': 1}
    g = {}; pai = {}; h = []
    ax, ay = alvo_xy
    def hh(i, j): return math.hypot(GX[i]-ax, GY[j]-ay)
    for (l, i, j) in origens:
        g[(l, i, j)] = 0.0; heapq.heappush(h, (hh(i, j), 0.0, (l, i, j)))
    n = 0
    while h:
        f, gc, nodo = heapq.heappop(h)
        if gc > g.get(nodo, 1e18): continue
        if nodo in alvos:
            path = [nodo]
            while nodo in pai: nodo = pai[nodo]; path.append(nodo)
            return path[::-1]
        n += 1
        if n > limite: return None
        l, i, j = nodo
        for di, dj, c in NB:
            ni, nj = i+di, j+dj
            if not (0 <= ni < NX and 0 <= nj < NY): continue
            m = MT[zi[nj, ni]][l] if MT is not None else mt[l]
            if m[nj, ni] and (l, ni, nj) not in alvos: continue
            if di and dj and (m[j, ni] or m[nj, i]): continue
            ng = gc + c*RES*camada_custo[lid[l]]
            nn = (l, ni, nj)
            if ng < g.get(nn, 1e18):
                g[nn] = ng; pai[nn] = nodo; heapq.heappush(h, (ng+hh(ni, nj), ng, nn))
        # via
        if not mv[j, i]:
            o2 = 'B' if l == 'F' else 'F'
            if not (MT[zi[j, i]][o2][j, i] if MT is not None else mt[o2][j, i]):
                ng = gc + VIA_CUSTO
                nn = (o2, i, j)
                if ng < g.get(nn, 1e18):
                    g[nn] = ng; pai[nn] = nodo; heapq.heappush(h, (ng+hh(i, j), ng, nn))
    return None

def escreve(b, net, path, w, zi=None, W=None):
    """path -> trilhas (colineares de mesma camada e largura unidas) e vias"""
    nvias = 0; L = 0.0
    def lw(n1, n2):
        if zi is None: return w
        return max(W[zi[n1[2], n1[1]]], W[zi[n2[2], n2[1]]])
    segs = []   # (camada, largura, [pontos])
    for a, c in zip(path[:-1], path[1:]):
        if a[0] != c[0]:
            add_via(b, net, GX[a[1]], GY[a[2]]); nvias += 1; continue
        ww = lw(a, c)
        if segs and segs[-1][0] == a[0] and segs[-1][1] == ww and segs[-1][3] == a:
            segs[-1][2].append((GX[c[1]], GY[c[2]])); segs[-1][3] = c
        else:
            segs.append([a[0], ww, [(GX[a[1]], GY[a[2]]), (GX[c[1]], GY[c[2]])], c])
    for lay_, ww, pts, _ in segs:
        simp = [pts[0]]
        for k in range(1, len(pts)-1):
            a, c, d = simp[-1], pts[k], pts[k+1]
            if abs((c[0]-a[0])*(d[1]-c[1])-(c[1]-a[1])*(d[0]-c[0])) > 1e-9: simp.append(c)
        simp.append(pts[-1])
        if len(simp) >= 2 and math.hypot(simp[-1][0]-simp[0][0], simp[-1][1]-simp[0][1]) > 1e-6:
            l, _ = add_track(b, net, simp, ww, pcbnew.F_Cu if lay_ == 'F' else pcbnew.B_Cu); L += l
    return L, nvias

def route_net(b, net, w, pads, log_=print, rot=None, bloqueia=(), zonas=()):
    """Liga os pads (lista 'REF.NUM') da rede `net` com trilhas de largura w. Idempotente nao (acrescenta); use depois de arrancar."""
    R = Roteador(b)
    mt, mv = R.masks(net, w)
    for (bx0, by0, bx1, by1) in bloqueia:      # retangulos (mm) proibidos para esta rede (reserva de canais para os sinais)
        i0 = max(0, int((bx0-X0)/RES)); i1 = min(NX, int((bx1-X0)/RES)+1); j0 = max(0, int((by0-Y0)/RES)); j1 = min(NY, int((by1-Y0)/RES)+1)
        mt['F'][j0:j1, i0:i1] = True; mt['B'][j0:j1, i0:i1] = True; mv[j0:j1, i0:i1] = True
    # zonas de largura menor: (refs, largura, raio) em volta dos pads das pecas, ou ('rect', (x0,y0,x1,y1), largura)
    zi = None; MT = None; W = None
    if zonas:
        zi = np.zeros((NY, NX), np.int8); W = [w]; MT = [mt]
        for k, z in enumerate(zonas, 1):
            W.append(z[1]); m2, _ = R.masks(net, z[1]); 
            for (bx0, by0, bx1, by1) in bloqueia:
                i0 = max(0, int((bx0-X0)/RES)); i1 = min(NX, int((bx1-X0)/RES)+1); j0 = max(0, int((by0-Y0)/RES)); j1 = min(NY, int((by1-Y0)/RES)+1)
                m2['F'][j0:j1, i0:i1] = True; m2['B'][j0:j1, i0:i1] = True
            MT.append(m2)
            if z[0] == 'rect':
                x0_, y0_, x1_, y1_ = z[2]; i0 = int((x0_-X0)/RES); i1 = int((x1_-X0)/RES)+1; j0 = int((y0_-Y0)/RES); j1 = int((y1_-Y0)/RES)+1
                sel = zi[j0:j1, i0:i1]; sel[sel == 0] = k
            else:
                for ref in z[0]:
                    for p in b.FindFootprintByReference(ref).Pads():
                        q = p.GetPosition(); cx, cy = F.mmv(q.x), F.mmv(q.y); r = z[2]
                        i0 = int((cx-r-X0)/RES); i1 = int((cx+r-X0)/RES)+1; j0 = int((cy-r-Y0)/RES); j1 = int((cy+r-Y0)/RES)+1
                        sub = zi[max(j0, 0):j1, max(i0, 0):i1]
                        yy, xx = np.mgrid[max(j0, 0):j1, max(i0, 0):i1]
                        near = np.hypot(GX[xx]-cx, GY[yy]-cy) < r
                        sub[near & (sub == 0)] = k
    terms = []
    for s in pads:
        if s.startswith('V@'):          # terminal = via (criada se nao existir) em x,y
            vx, vy = map(float, s[2:].split(','))
            if not any(abs(v[0]-vx) < 0.05 and abs(v[1]-vy) < 0.05 and v[2] == net for v in R.vias):
                add_via(b, net, vx, vy); R.vias.append([vx, vy, net])
            i = int(round((vx-X0)/RES)); j = int(round((vy-Y0)/RES))
            terms.append((s, [('F', i, j), ('B', i, j)], (vx, vy), [(vx-.2, vy-.2), (vx+.2, vy-.2), (vx+.2, vy+.2), (vx-.2, vy+.2)], 'B'))
            continue
        if s.startswith('C@'):          # terminal = ponto de cobre existente (trilha/via da mesma rede): C@F|B,x,y
            lay_, vx, vy = s[2:].split(','); vx = float(vx); vy = float(vy)
            i = int(round((vx-X0)/RES)); j = int(round((vy-Y0)/RES))
            cs = [(lay_, i+di, j+dj) for di in (-1, 0, 1) for dj in (-1, 0, 1)]
            terms.append((s, cs, (vx, vy), [(vx-.2, vy-.2), (vx+.2, vy-.2), (vx+.2, vy+.2), (vx-.2, vy+.2)], lay_))
            continue
        ref, num = s.split('.', 1)
        poly, lay = pad_poly(b, ref, num)
        cs = [c for c in celulas_poly(poly, lay, mt) if not mt[c[0]][c[2], c[1]]]
        if not cs:   # pad sem celula livre (pad pequeno / vizinhos): relaxa a mascara dentro do pad
            cs = celulas_poly(poly, lay, mt)
        terms.append((s, cs, (sum(p[0] for p in poly)/len(poly), sum(p[1] for p in poly)/len(poly)), poly, lay))
    arvore = set(terms[0][1]); resto = terms[1:]
    total = 0.0; ok = True
    while resto:
        # o mais proximo da arvore
        def dmin(t):
            return min(math.hypot(GX[i]-t[2][0], GY[j]-t[2][1]) for (_, i, j) in list(arvore)[::max(1, len(arvore)//200)])
        resto.sort(key=dmin); t = resto.pop(0)
        alvos = set(t[1])
        # libera as celulas dos pads da arvore/alvo na mascara (cobre da mesma rede nao bloqueia)
        for (l, i, j) in list(arvore)+list(alvos):
            for mm_ in (MT if MT is not None else [mt]): mm_[l][j, i] = False
        p = astar(mt, mv, arvore, alvos, t[2], zi=zi, MT=MT)
        if not p: log_("  %s: sem caminho ate %s" % (net, t[0])); ok = False; continue
        L, nv = escreve(b, net, p, w, zi, W); total += L
        log_("  %s -> %s: %.1f mm, %d vias" % (net, t[0], L, nv))
        for nodo in p: arvore.add(nodo)
        for c in t[1]: arvore.add(c)
        # o novo cobre vira obstaculo para as proximas redes, nao para esta
    return ok, total

if __name__ == '__main__':
    b = pcbnew.LoadBoard(BOARD)
    ok, tot = route_net(b, sys.argv[1], float(sys.argv[2]), sys.argv[3].split(','), log)
    log("%s: %s %.1f mm" % (sys.argv[1], ok, tot))
    fill(b); pcbnew.SaveBoard(BOARD, b)
