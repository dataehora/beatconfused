"""Etapa 7: acabamento: alarga fiapos de VSYS junto ao U501 (0,25 -> 0,8) e tenta as ligacoes que sobraram com 0,15 mm (minimo da regra para sinais).
Parte de build/fecha.kicad_pcb, grava build/final.kicad_pcb."""
import re, shutil
from lib import *
import pcbnew, wide
import etapa6_fecha as E6
b = pcbnew.LoadBoard(os.path.join(BUILD, 'fecha.kicad_pcb')); KEEP = [b]
for t in b.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == 'VSYS':
        x, y = t.GetStart().x/1e6, t.GetStart().y/1e6
        if 52.4 < x < 53.0 and 89.6 < y < 90.2 and t.GetWidth() < 0.79e6: t.SetWidth(pcbnew.FromMM(0.8))
out = os.path.join(BUILD, 'final.kicad_pcb'); fill(b); pcbnew.SaveBoard(out, b); companions(out)
r0, d0 = drc(out, os.path.join(BUILD, 'drc_final0.json'))
feitos = []; falhas = []
for u in d0.get('unconnected_items', []):
    a, c = u['items'][:2]
    ta, na = E6.termo(a['description'], a['pos']); tc, nc = E6.termo(c['description'], c['pos'])
    if not ta or na != nc: falhas.append((na, ta, tc)); continue
    ok, L = wide.route_net(b, na, 0.15, [ta, tc], log)
    (feitos if ok else falhas).append((na, ta, tc))
fill(b); pcbnew.SaveBoard(out, b)
r, d = drc(out, os.path.join(BUILD, 'drc_final.json')); log("final: feitos %s falhas %s DRC %s" % (feitos, falhas, r))
marca('7_final', status='feito', drc=r, falhas=[list(map(str, f)) for f in falhas])
