"""Etapa 4: pos-processamento de uma placa saida do Freerouting (fr_<tag>.kicad_pcb).
 1) larguras: o Freerouting afina trilhas na entrada dos pinos (0,10 / 0,25 / 0,6 mm). Cada trecho abaixo do minimo da regra e alargado ate o
    minimo (ou o maximo que cabe) se a geometria deixa (folgas das regras, via com furo a 0,2 do cobre, borda a 0,3). Classe Corrente: 0,8 mm fora
    dos patios de J201, U202, U204, J202, U501 e J101; SCAN_CLK/SCAN_DATA/OUT_Rk: 0,2; demais sinais 0,15.
 2) pontas soltas: vias e trilhas apontadas pelo DRC como dangling saem (um por vez, DRC entre as rodadas), desde que nao abram ligacao.
Uso: python post.py entrada.kicad_pcb saida.kicad_pcb   (python do KiCad)"""
import json, math, sys
from lib import *
import pcbnew
import fanout as F

CORR = F.CORRENTE
PATIOS_CORRENTE = ('J201', 'U202', 'U204', 'J202', 'U501', 'J101')
LINHAS_02 = ('SCAN_CLK', 'SCAN_DATA', 'OUT_R1', 'OUT_R2', 'OUT_R3', 'OUT_R4')
CLK_LIKE = ('SCAN_CLK', 'SCAN_DATA', 'SCAN_CLK_P', 'SCAN_DATA_P', 'I2S_BCLK', 'I2S_LRCLK', 'I2S_TX', 'I2S_RX', 'AUD_MCLK', 'AUD_MCLK_P')
OUTS = ('OUT_R1', 'OUT_R2', 'OUT_R3', 'OUT_R4')

def folga(a, b):
    f = 0.1
    if a in CORR or b in CORR: f = max(f, 0.2)
    if (a in ('USB_DP', 'USB_DN')) != (b in ('USB_DP', 'USB_DN')): f = max(f, 0.25)
    if (a in OUTS and b in CLK_LIKE) or (b in OUTS and a in CLK_LIKE): f = max(f, 0.3)
    return f

def patios(b):
    out = {}
    for r in PATIOS_CORRENTE:
        fp = b.FindFootprintByReference(r)
        bb = fp.GetCourtyard(pcbnew.B_CrtYd if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_CrtYd).BBox()
        out[r] = (F.mmv(bb.GetX()), F.mmv(bb.GetY()), F.mmv(bb.GetRight()), F.mmv(bb.GetBottom()))
    return out

def toca_patio(seg, pat):
    (ax, ay), (bx, by), w = seg
    for (x0, y0, x1, y1) in pat.values():
        poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        if F.seg_poly((ax, ay), (bx, by), poly) <= w/2: return True
    return False

def minimo(net, seg, pat):
    if net in ('USB_DP', 'USB_DN'): return 0.19
    if net in CORR:
        if toca_patio(seg, pat): return 0.15
        if net == 'VSYS' and F.seg_poly(seg[0], seg[1], [(63.0, 6.5), (72.5, 6.5), (72.5, 15.5), (63.0, 15.5)]) <= seg[2]/2: return 0.5
        return 0.8
    if net in LINHAS_02: return 0.2
    return 0.15

def cabe(obs, t, a, c, w, net):
    """O trecho a-c com largura w cabe (folgas)? obs ja tem tudo, inclusive o proprio trecho (mesma rede: ignorado)."""
    lay = 'B' if t.GetLayer() == pcbnew.B_Cu else 'F'
    if not (F.dentro_placa(a[0], a[1], 0.3+w/2) and F.dentro_placa(c[0], c[1], 0.3+w/2)): return False
    for o in obs:
        if o.net == net or lay not in o.camadas: continue
        if o.bb[0]-1 > max(a[0], c[0]) or o.bb[2]+1 < min(a[0], c[0]) or o.bb[1]-1 > max(a[1], c[1]) or o.bb[3]+1 < min(a[1], c[1]): continue
        if o.net == '#keepout':
            if o.dist_seg(a, c) < w/2+0.0: return False
            continue
        if o.kind == 'circ' and o.ref == 'via':
            cx, cy, r = o.g
            if F.pd(cx, cy, *a, *c) < max(r+folga(net, o.net)+w/2, 0.35+w/2)-1e-9: return False
            continue
        if o.dist_seg(a, c) < w/2+folga(net, o.net)-1e-9: return False
    return True

def alarga(b):
    obs, vias, pads = F.carrega(b)
    pat = patios(b)
    n_ok = n_falha = 0; falhas = []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T: continue
        net = t.GetNetname(); w0 = F.mmv(t.GetWidth())
        a = (F.mmv(t.GetStart().x), F.mmv(t.GetStart().y)); c = (F.mmv(t.GetEnd().x), F.mmv(t.GetEnd().y))
        mn = minimo(net, (a, c, w0), pat)
        if w0 >= mn-1e-6: continue
        if math.hypot(c[0]-a[0], c[1]-a[1]) < 1e-4: continue
        ok = False
        for w in sorted({mn, (mn+w0)/2, w0}, reverse=True):
            if w <= w0+1e-6: continue
            if cabe(obs, t, a, c, w, net):
                t.SetWidth(F.mm(w) if hasattr(F, 'mm') else pcbnew.FromMM(w)); ok = True; break
        if ok: n_ok += 1
        else: n_falha += 1; falhas.append((net, round(a[0], 2), round(a[1], 2), round(w0, 3), mn))
    return n_ok, n_falha, falhas

def limpa_pontas(b, rodadas=6):
    """Remove (um conjunto por rodada) vias/trilhas que o DRC aponta como pontas soltas."""
    GRAVE_ = []
    total = 0
    for _ in range(rodadas):
        tmp = os.path.join(BUILD, 'post_tmp.kicad_pcb'); pcbnew.SaveBoard(tmp, b); companions(tmp)
        r, d = drc(tmp, os.path.join(BUILD, 'post_tmp.json'))
        pontos = [v for v in d.get('violations', []) if v['type'] in ('via_dangling', 'track_dangling')]
        if not pontos: break
        n = 0
        for v in pontos:
            for it in v['items']:
                px, py = it['pos']['x'], it['pos']['y']
                for t in list(b.GetTracks()):
                    isv = t.Type() == pcbnew.PCB_VIA_T
                    if ('Via' in it['description']) != isv: continue
                    if it['description'].split('[')[1].split(']')[0] != t.GetNetname(): continue
                    q = t.GetPosition() if isv else t.GetStart()
                    q2 = q if isv else t.GetEnd()
                    if (abs(F.mmv(q.x)-px) < 0.02 and abs(F.mmv(q.y)-py) < 0.02) or (not isv and abs(F.mmv(q2.x)-px) < 0.02 and abs(F.mmv(q2.y)-py) < 0.02):
                        b.Remove(t); GRAVE_.append(t); n += 1; break
        total += n
        if n == 0: break
    return total

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    b = pcbnew.LoadBoard(src)
    ok, falha, falhas = alarga(b)
    log("larguras: %d trechos alargados, %d sem folga" % (ok, falha))
    nd = limpa_pontas(b)
    log("pontas soltas removidas: %d" % nd)
    fill(b); pcbnew.SaveBoard(dst, b); companions(dst)
    r, d = drc(dst, os.path.join(BUILD, 'drc_post.json')); log("DRC post: %s" % r)
    marca('4_post', status='feito', larguras_ok=ok, larguras_falha=falha, pontas=nd, drc=r, falhas_largura=falhas[:40])
