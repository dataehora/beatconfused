"""Etapa 8: desbloqueio local. Arranca as redes de sinal com trilha na caixa (x0,y0,x1,y1) em torno do pad que falta, liga primeiro a rede que falta
(roteador de grade, 0,15 mm) e refaz as arrancadas com o mesmo roteador (largura 0,2; 0,15 se nao couber). Uso: python etapa8_local.py x0 y0 x1 y1
Parte de build/final.kicad_pcb, grava build/local.kicad_pcb."""
import sys, re
from lib import *
import pcbnew, wide
import etapa5_itera as E5
import etapa6_fecha as E6
import fanout as F
x0, y0, x1, y1 = map(float, sys.argv[1:5])
b = pcbnew.LoadBoard(os.path.join(BUILD, 'final.kicad_pcb')); KEEP = [b]; ch = E5.protegidos(b)
prot = {'GND', '+3V3', 'USB_DP', 'USB_DN', 'VBUS', 'VSYS', 'VBAT', 'BB_L1', 'BB_L2', 'BB_VINA'}
r0, d0 = drc(os.path.join(BUILD, 'final.kicad_pcb'), os.path.join(BUILD, 'x.json'))
faltam = []
for u in d0.get('unconnected_items', []):
    a, c = u['items'][:2]; ta, na = E6.termo(a['description'], a['pos']); tc, nc = E6.termo(c['description'], c['pos'])
    if ta and na == nc: faltam.append((na, ta, tc))
alvo = set()
for t in b.GetTracks():
    n = t.GetNetname()
    if n in prot or E5.eh_protegido(t, ch): continue
    p = t.GetPosition() if t.Type() == pcbnew.PCB_VIA_T else t.GetStart(); e = t.GetEnd() if t.Type() != pcbnew.PCB_VIA_T else p
    if (x0 <= F.mmv(p.x) <= x1 and y0 <= F.mmv(p.y) <= y1) or (x0 <= F.mmv(e.x) <= x1 and y0 <= F.mmv(e.y) <= y1): alvo.add(n)
log("local: redes a arrancar %s; faltam %s" % (sorted(alvo), faltam))
E5.arranca(b, alvo)
for (n, ta, tc) in faltam:
    ok, L = wide.route_net(b, n, 0.15, [ta, tc], log); log("local %s: %s" % (n, ok))
fill(b); out = os.path.join(BUILD, 'local.kicad_pcb'); pcbnew.SaveBoard(out, b); companions(out)
r1, d1 = drc(out, os.path.join(BUILD, 'drc_local1.json'))
b = pcbnew.LoadBoard(out); KEEP.append(b)
for u in d1.get('unconnected_items', []):
    a, c = u['items'][:2]; ta, na = E6.termo(a['description'], a['pos']); tc, nc = E6.termo(c['description'], c['pos'])
    if ta and na == nc and na not in wide.P.CORR:
        for w in (0.2, 0.15):
            ok, L = wide.route_net(b, na, w, [ta, tc], log)
            if ok: break
fill(b); pcbnew.SaveBoard(out, b)
r, d = drc(out, os.path.join(BUILD, 'drc_local.json')); log("local: DRC %s" % r)
marca('8_local', status='feito', drc=r, redes=sorted(alvo))
