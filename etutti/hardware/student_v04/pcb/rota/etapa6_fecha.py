"""Etapa 6: fecha com o roteador de grade proprio (wide.py) as ligacoes que o Freerouting deixou (pares do DRC: pad-pad ou pad-trilha).
Parte de build/melhor.kicad_pcb, grava build/fecha.kicad_pcb; se a pontuacao melhorar, vira a melhor. Largura 0,2 (sinais).
Uso: python etapa6_fecha.py"""
import re, shutil, sys, json
from lib import *
import pcbnew, wide
import post as P
import fanout as F

def termo(desc, pos, layer_default='B'):
    m = re.match(r'(?:PTH pad|Pad) (\S+) \[([^\]]+)\] of (\S+)', desc)
    if m: return m.group(3) + '.' + m.group(1), m.group(2)
    m = re.match(r'Track \[([^\]]+)\] on (\S+)\.Cu', desc)
    if m: return 'C@%s,%.3f,%.3f' % (m.group(2)[0], pos['x'], pos['y']), m.group(1)
    m = re.match(r'Via \[([^\]]+)\]', desc)
    if m: return 'C@B,%.3f,%.3f' % (pos['x'], pos['y']), m.group(1)
    return None, None

def main():
    melhor = os.path.join(BUILD, 'melhor.kicad_pcb')
    out = os.path.join(BUILD, 'fecha.kicad_pcb')
    shutil.copy(melhor, out); companions(out)
    r0, d0 = drc(out, os.path.join(BUILD, 'drc_fecha0.json'))
    b = pcbnew.LoadBoard(out); KEEP.append(b)
    feitos = []; falhas = []
    for u in d0.get('unconnected_items', []):
        a, c = u['items'][:2]
        ta, na = termo(a['description'], a['pos']); tc, nc = termo(c['description'], c['pos'])
        if not ta or not tc or na != nc: falhas.append((a['description'][:40], c['description'][:40])); continue
        if na in P.CORR: falhas.append((na, 'potencia: nao e do fecha')); continue
        w = 0.2
        ok, L = wide.route_net(b, na, w, [ta, tc], log)
        (feitos if ok else falhas).append((na, ta, tc, round(L, 1)))
    log("fecha: %d ligacoes feitas, %d falhas" % (len(feitos), len(falhas)))
    ok, falha, _ = P.alarga(b); nd = P.limpa_pontas(b)
    fill(b); pcbnew.SaveBoard(out, b)
    r, d = drc(out, os.path.join(BUILD, 'drc_fecha.json')); log("fecha: DRC %s" % r)
    pt = lambda r_: 1000*r_['erros'] + 100*r_['faltando'] + r_['avisos']
    if pt(r) < pt(r0):
        shutil.copy(out, os.path.join(BUILD, 'melhor.kicad_pcb')); companions(os.path.join(BUILD, 'melhor.kicad_pcb')); log('fecha: nova melhor')
    marca('6_fecha', status='feito', feitos=feitos, falhas=[list(map(str, f)) for f in falhas], drc=r)
KEEP = []
if __name__ == '__main__': main()
