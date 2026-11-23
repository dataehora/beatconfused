"""Etapa 3: fan-out dos planos. Cada pad SMD das redes dos planos (GND na In2, +3V3 na In1) ganha uma via (0,5 / 0,3) e um toco de trilha curto
em B.Cu; os pads grandes (QFN com almofada termica) ganham uma grade de vias dentro do pad. O Freerouting 2.5.0 nao ligou nenhum desses pads
ao plano (so 1 via de GND em 127 pads), por isso este passo e proprio.
Geometria propria, sem dependencias: pads = poligonos efetivos do pcbnew, trilhas = segmentos, vias = circulos; as folgas vem das regras:
 folga 0,1 (0,2 nas redes da classe Corrente, 0,25 do par USB), furo a 0,2 do cobre de outra rede (centro da via a >= 0,35 do cobre), furo a furo 0,25,
 cobre a 0,3 da borda. Idempotente: remove antes as vias/tocos de GND e +3V3 criados por esta etapa (marcados no estado) e refaz.
Uso: python fanout.py   (python do KiCad)"""
import json, math, sys, os, time, shutil
from lib import *
import pcbnew

VIA_D, VIA_H = 0.5, 0.3
GRID = 0.1
RAIO = 2.6
PLANOS = ('GND', '+3V3')
CORRENTE = ('VBUS', 'VSYS', 'VBAT', 'BB_L1', 'BB_L2')
EDGE = (2.45, 2.45, 77.5, 97.55)          # contorno (x0, y0, x1, y1); cantos R 3
RCANTO = 3.0

# ---------- geometria ----------
def pd(px, py, ax, ay, bx, by):
    dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
    if L2 == 0: return math.hypot(px-ax, py-ay)
    t = max(0.0, min(1.0, ((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-ax-t*dx, py-ay-t*dy)
def inside(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]; x1, y1 = poly[(i+1) % n]
        if (y0 > y) != (y1 > y) and x < (x1-x0)*(y-y0)/(y1-y0)+x0: c = not c
    return c
def pt_poly(x, y, poly):
    if inside(poly, x, y): return 0.0
    return min(pd(x, y, *poly[i], *poly[(i+1) % len(poly)]) for i in range(len(poly)))
def segseg(a, b, c, d):
    def cr(o, p, q): return (p[0]-o[0])*(q[1]-o[1])-(p[1]-o[1])*(q[0]-o[0])
    if cr(a, b, c)*cr(a, b, d) < 0 and cr(c, d, a)*cr(c, d, b) < 0: return 0.0
    return min(pd(*a, *c, *d), pd(*b, *c, *d), pd(*c, *a, *b), pd(*d, *a, *b))
def seg_poly(a, b, poly):
    if inside(poly, *a) or inside(poly, *b): return 0.0
    return min(segseg(a, b, poly[i], poly[(i+1) % len(poly)]) for i in range(len(poly)))
def dentro_placa(x, y, m):
    x0, y0, x1, y1 = EDGE[0]+m, EDGE[1]+m, EDGE[2]-m, EDGE[3]-m
    if not (x0 <= x <= x1 and y0 <= y <= y1): return False
    r = max(RCANTO-m, 0.0)
    for cx, cy, sx, sy in ((x0+r, y0+r, -1, -1), (x1-r, y0+r, 1, -1), (x0+r, y1-r, -1, 1), (x1-r, y1-r, 1, 1)):
        if (x-cx)*sx > 0 and (y-cy)*sy > 0 and math.hypot(x-cx, y-cy) > r: return False
    return True

class Obs:
    __slots__ = ('kind', 'net', 'g', 'clr', 'bb', 'camadas', 'ref')
    def __init__(s, kind, net, g, clr, camadas, ref=''):
        s.kind, s.net, s.g, s.clr, s.camadas, s.ref = kind, net, g, clr, camadas, ref
        if kind == 'poly': xs = [p[0] for p in g]; ys = [p[1] for p in g]; s.bb = (min(xs), min(ys), max(xs), max(ys))
        elif kind == 'seg': (ax, ay), (bx, by), w = g; s.bb = (min(ax, bx)-w/2, min(ay, by)-w/2, max(ax, bx)+w/2, max(ay, by)+w/2)
        else: x, y, r = g; s.bb = (x-r, y-r, x+r, y+r)
    def dist_pt(s, x, y):          # distancia do ponto a borda do cobre
        if s.kind == 'poly': return pt_poly(x, y, s.g)
        if s.kind == 'seg': (a, b, w) = s.g; return max(0.0, pd(x, y, *a, *b)-w/2)
        cx, cy, r = s.g; return max(0.0, math.hypot(x-cx, y-cy)-r)
    def dist_seg(s, a, b):
        if s.kind == 'poly': return seg_poly(a, b, s.g)
        if s.kind == 'seg': (c, d, w) = s.g; return max(0.0, segseg(a, b, c, d)-w/2)
        cx, cy, r = s.g; return max(0.0, pd(cx, cy, *a, *b)-r)

def mmv(v): return v/1e6
def carrega(b):
    obs = []; vias = []; pads = []
    for f in b.GetFootprints():
        for p in f.Pads():
            net = p.GetNetname(); ls = p.GetLayerSet()
            cam = set()
            if ls.Contains(pcbnew.B_Cu): cam.add('B')
            if ls.Contains(pcbnew.F_Cu): cam.add('F')
            dr = p.GetDrillSize()
            fur = dr.x > 0
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                pos = p.GetPosition()
                obs.append(Obs('circ', '', (mmv(pos.x), mmv(pos.y), max(mmv(dr.x), mmv(dr.y))/2+0.25), 0.0, {'F', 'B'}, f.GetReference()))
                continue
            if cam:
                lay = pcbnew.B_Cu if 'B' in cam else pcbnew.F_Cu
                o = p.GetEffectivePolygon(lay).Outline(0)
                poly = [(mmv(o.CPoint(i).x), mmv(o.CPoint(i).y)) for i in range(o.PointCount())]
                clr = 0.2 if net in CORRENTE else 0.1
                obs.append(Obs('poly', net, poly, clr, cam, f.GetReference()+'.'+p.GetNumber()))
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and 'B' in cam and net in PLANOS:
                    pads.append(dict(ref=f.GetReference(), num=p.GetNumber(), net=net, poly=poly, p=p))
            if fur and not cam:      # NPTH: buraco
                pos = p.GetPosition()
                obs.append(Obs('circ', '', (mmv(pos.x), mmv(pos.y), max(mmv(dr.x), mmv(dr.y))/2+0.25), 0.0, {'F', 'B'}, f.GetReference()))
            elif fur and cam:
                pass                 # PTH: ja e um poligono com cobre em todas as camadas
    for z in b.Zones():
        if z.GetIsRuleArea() and (z.GetDoNotAllowVias() or z.GetDoNotAllowTracks()):
            o = z.Outline().COutline(0)
            poly = [(mmv(o.CPoint(i).x), mmv(o.CPoint(i).y)) for i in range(o.PointCount())]
            obs.append(Obs('poly', '#keepout', poly, 0.05, {'F', 'B'}, 'keepout'))
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            q = t.GetPosition(); vias.append([mmv(q.x), mmv(q.y), t.GetNetname()])
            obs.append(Obs('circ', t.GetNetname(), (mmv(q.x), mmv(q.y), mmv(t.GetWidth(pcbnew.F_Cu))/2), 0.1, {'F', 'B'}, 'via'))
        else:
            if b.GetLayerName(t.GetLayer()) != 'B.Cu' and b.GetLayerName(t.GetLayer()) != 'F.Cu': continue
            a = (mmv(t.GetStart().x), mmv(t.GetStart().y)); c = (mmv(t.GetEnd().x), mmv(t.GetEnd().y))
            n = t.GetNetname(); clr = 0.25 if n in ('USB_DP', 'USB_DN') else (0.2 if n in CORRENTE else 0.1)
            obs.append(Obs('seg', n, (a, c, mmv(t.GetWidth())), clr, {'B' if t.GetLayer() == pcbnew.B_Cu else 'F'}, 'trk'))
    return obs, vias, pads

# ---------- verificacoes ----------
def via_ok(obs, vias, x, y, net, extra=()):
    if not dentro_placa(x, y, 0.6): return False
    for o in obs:
        if o.net == net: continue
        if not (o.bb[0]-1 < x < o.bb[2]+1 and o.bb[1]-1 < y < o.bb[3]+1): continue
        need = max(VIA_D/2+max(o.clr, 0.1), VIA_H/2+0.2)
        if o.net == '#keepout': need = VIA_D/2+0.05
        if o.dist_pt(x, y) < need-1e-9: return False
    for vx, vy, vn in vias:
        if abs(vx-x) < 0.8 and abs(vy-y) < 0.8 and math.hypot(vx-x, vy-y) < (0.6 if vn == net else 0.7)-1e-9: return False
    return True
def stub_ok(obs, a, b, ws, net, ref_pad, extra=()):
    for o in obs:
        if o.net == net or 'B' not in o.camadas: continue
        if o.bb[0]-1 > max(a[0], b[0]) or o.bb[2]+1 < min(a[0], b[0]) or o.bb[1]-1 > max(a[1], b[1]) or o.bb[3]+1 < min(a[1], b[1]): continue
        need = ws/2+max(o.clr, 0.1)
        if o.net == '#keepout': need = ws/2+0.02
        if o.kind == 'circ' and o.ref == 'via':
            cx, cy, r = o.g
            if pd(cx, cy, *a, *b) < max(r+need, 0.35+ws/2)-1e-9: return False
            continue
        if o.dist_seg(a, b) < need-1e-9: return False
    return True

def proj_poly(poly, x, y):
    best = None
    for i in range(len(poly)):
        ax, ay = poly[i]; bx, by = poly[(i+1) % len(poly)]
        dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
        t = 0 if L2 == 0 else max(0.0, min(1.0, ((x-ax)*dx+(y-ay)*dy)/L2))
        qx, qy = ax+t*dx, ay+t*dy; d = math.hypot(x-qx, y-qy)
        if best is None or d < best[0]: best = (d, qx, qy)
    return best

def local(obs, vias, xs, ys, m):
    x0, y0, x1, y1 = min(xs)-m, min(ys)-m, max(xs)+m, max(ys)+m
    return ([o for o in obs if o.bb[2] >= x0 and o.bb[0] <= x1 and o.bb[3] >= y0 and o.bb[1] <= y1],
            [v for v in vias if x0 <= v[0] <= x1 and y0 <= v[1] <= y1])

def candidatos(obs, vias, pad, extra=()):
    poly = pad['poly']; net = pad['net']
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    obs, vias = local(obs, vias, xs, ys, RAIO+1.5)
    cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)
    larg = min(max(xs)-min(xs), max(ys)-min(ys)); ws = 0.2 if larg < 0.7 else 0.25
    out = []
    gx0 = math.floor((min(xs)-RAIO)/GRID)*GRID; gy0 = math.floor((min(ys)-RAIO)/GRID)*GRID
    nx = int((max(xs)-min(xs)+2*RAIO)/GRID)+1; ny = int((max(ys)-min(ys)+2*RAIO)/GRID)+1
    for i in range(nx):
        x = gx0+i*GRID
        for j in range(ny):
            y = gy0+j*GRID
            d, qx, qy = proj_poly(poly, x, y)
            if inside(poly, x, y): continue
            if d > RAIO: continue
            if not via_ok(obs, vias, x, y, net, extra): continue
            # ponto de partida do toco: dentro do pad, 0,08 mm alem da borda em direcao ao centroide
            vx, vy = cx-qx, cy-qy; L = math.hypot(vx, vy) or 1.0
            ent = min(0.1, larg/2-0.02)
            a = (qx+vx/L*ent, qy+vy/L*ent)
            if not stub_ok(obs, a, (x, y), ws, net, pad, extra): continue
            out.append((math.hypot(x-a[0], y-a[1]), x, y, a, ws))
    out.sort(key=lambda c: c[0])
    return out

def main():
    t0 = time.time()
    b = pcbnew.LoadBoard(BOARD)
    GRAVE = []
    st = estado(); marcados = st['etapas'].get('3_fanout', {}).get('itens', [])
    # idempotencia: apaga vias e tocos de GND/+3V3 criados por esta etapa (e so eles)
    for t in list(b.GetTracks()):
        if t.GetNetname() in PLANOS:
            if t.Type() == pcbnew.PCB_VIA_T: k = ('v', round(mmv(t.GetPosition().x), 3), round(mmv(t.GetPosition().y), 3))
            else: k = ('t', round(mmv(t.GetStart().x), 3), round(mmv(t.GetStart().y), 3), round(mmv(t.GetEnd().x), 3), round(mmv(t.GetEnd().y), 3))
            if list(k) in marcados:
                b.Remove(t); GRAVE.append(t)
    obs, vias, pads = carrega(b)
    # pads grandes: almofada termica -> grade de vias no pad; os demais: via + toco
    feitos = []; falhas = []
    def novo_via(x, y, net):
        v = add_via(b, net, x, y); vias.append([x, y, net])
        obs.append(Obs('circ', net, (x, y, VIA_D/2), 0.1, {'F', 'B'}, 'via'))
        feitos.append(['v', round(x, 3), round(y, 3)])
    def novo_toco(a, c, ws, net):
        add_track(b, net, [a, c], ws)
        obs.append(Obs('seg', net, (a, c, ws), 0.1, {'B'}, 'trk'))
        feitos.append(['t', round(a[0], 3), round(a[1], 3), round(c[0], 3), round(c[1], 3)])
    # pads com via ja ligada (corredor do USBLC6: U201.2)
    ja = {('U201', '2')}
    termicos = []
    resto = []
    for pd_ in pads:
        if (pd_['ref'], pd_['num']) in ja: continue
        xs = [p[0] for p in pd_['poly']]; ys = [p[1] for p in pd_['poly']]
        w, h = max(xs)-min(xs), max(ys)-min(ys)
        (termicos if pd_['ref'] in ('U301', 'U202', 'U204', 'U501') and min(w, h) >= 1.5 else resto).append(pd_)
    for pd_ in termicos:
        xs = [p[0] for p in pd_['poly']]; ys = [p[1] for p in pd_['poly']]
        w, h = max(xs)-min(xs), max(ys)-min(ys); cx, cy = (max(xs)+min(xs))/2, (max(ys)+min(ys))/2
        nxv = max(1, int((w-0.5)//0.8)+1); nyv = max(1, int((h-0.5)//0.8)+1)
        px = 0.8 if nxv > 1 else 0; py = 0.8 if nyv > 1 else 0
        for i in range(nxv):
            for j in range(nyv):
                x = cx+(i-(nxv-1)/2)*px; y = cy+(j-(nyv-1)/2)*py
                if via_ok(obs, vias, x, y, pd_['net']): novo_via(x, y, pd_['net'])
        log("termico %s.%s: %d vias na almofada" % (pd_['ref'], pd_['num'], sum(1 for f in feitos if f[0] == 'v')))
    # demais pads: candidatos e atribuicao gulosa, os mais apertados primeiro
    cands = {}
    for pd_ in resto:
        cands[(pd_['ref'], pd_['num'], tuple(pd_['poly'][0]))] = candidatos(obs, vias, pd_)
    ordem = sorted(resto, key=lambda p: len(cands[(p['ref'], p['num'], tuple(p['poly'][0]))]))
    log("pads a ligar: %d; sem candidato: %s" % (len(resto), [(p['ref'], p['num']) for p in ordem if not cands[(p['ref'], p['num'], tuple(p['poly'][0]))]]))
    for p in ordem:
        key = (p['ref'], p['num'], tuple(p['poly'][0])); net = p['net']
        lst = cands[key]; escolhido = None
        # preferencia: via do mesmo net ja existente, ao alcance do toco
        xs = [q[0] for q in p['poly']]; ys = [q[1] for q in p['poly']]
        lo, lv = local(obs, vias, xs, ys, RAIO+1.5)
        for (L, x, y, a, ws) in lst:
            if via_ok(lo, lv, x, y, net) and stub_ok(lo, a, (x, y), ws, net, p):
                escolhido = (x, y, a, ws); break
        if not escolhido:
            lst = candidatos(obs, vias, p)
            if lst: L, x, y, a, ws = lst[0]; escolhido = (x, y, a, ws)
        if not escolhido: falhas.append((p['ref'], p['num'], net)); continue
        x, y, a, ws = escolhido
        novo_via(x, y, net); novo_toco(a, (x, y), ws, net)
    fill(b); pcbnew.SaveBoard(BOARD, b)
    log("fan-out: %d itens, %d falhas %s, %.0f s" % (len(feitos), len(falhas), falhas, time.time()-t0))
    r, d = drc(); log(str(r))
    shutil.copy(BOARD, os.path.join(BUILD, 'etapa3.kicad_pcb'))
    marca('3_fanout', status='feito', itens=feitos, falhas=[list(f) for f in falhas], drc=r)
if __name__ == '__main__': main()
