"""Etapa 5: melhoria iterativa. Parte da melhor placa (build/melhor.kicad_pcb; se nao houver, de BASE ou da roteada), acha as redes com problema
(ligacao faltando ou violacao no DRC), arranca so essas, trava o resto e roda o Freerouting de novo so para elas; depois o pos-processamento
(post.py). Guarda em build/melhor.kicad_pcb a de menor pontuacao (1000 x erros + 100 x faltando + avisos). Retomavel: o estado fica em estado.json
(etapa 5: rodadas feitas, melhor pontuacao) e o log em build/log.txt.
Protegido (nunca arrancado): par USB, vias e tocos do fan-out de GND/+3V3, vias e tocos do corredor do USBLC6.
Uso: python etapa5_itera.py [rodadas] [passes]"""
import json, re, sys, shutil
from lib import *
import pcbnew
import etapa3_fr as E3
import post as P
import fanout as F

def pontua(r): return 1000*r['erros'] + 100*r['faltando'] + r['avisos']

def protegidos(b):
    st = estado(); itens = st['etapas'].get('3_fanout', {}).get('itens', [])
    ch = set()
    for k in itens:
        if k[0] == 'v': ch.add(('v', k[1], k[2]))
        else: ch.add(('t',) + tuple(k[1:]))
    return ch

def eh_protegido(t, ch):
    net = t.GetNetname()
    if net in ('USB_DP', 'USB_DN'): return True
    p = t.GetPosition() if t.Type() == pcbnew.PCB_VIA_T else t.GetStart()
    x, y = F.mmv(p.x), F.mmv(p.y)
    if net in ('VBUS', 'GND') and 12.9 < x < 14.1 and 8.4 < y < 10.0: return True
    if t.Type() == pcbnew.PCB_VIA_T: return ('v', round(x, 3), round(y, 3)) in ch
    e = t.GetEnd()
    a = (round(x, 3), round(y, 3), round(F.mmv(e.x), 3), round(F.mmv(e.y), 3))
    return ('t',) + a in ch or ('t', a[2], a[3], a[0], a[1]) in ch

def redes_ruins(d):
    rs = set()
    for u in d.get('unconnected_items', []):
        for it in u['items']:
            m = re.findall(r'\[([^\]]+)\]', it['description'])
            if m: rs.add(m[0])
    for v in d.get('violations', []):
        if v['type'] in ('isolated_copper',): continue
        for it in v['items']:
            m = re.findall(r'\[([^\]]+)\]', it['description'])
            if m: rs.add(m[0])
    return rs - {'GND', '+3V3', 'USB_DP', 'USB_DN', 'VBUS', 'VSYS', 'VBAT', 'BB_L1', 'BB_L2'}

def arranca(b, redes):
    ch = protegidos(b); n = 0
    for t in list(b.GetTracks()):
        if t.GetNetname() in redes and not eh_protegido(t, ch):
            b.Remove(t); GR.append(t); n += 1
    return n
GR = []
KEEP = []   # placas carregadas ficam vivas (licao: itens tirados de uma placa liberada viram SwigPyObject)

def main():
    rodadas = int(sys.argv[1]) if len(sys.argv) > 1 else 3; passes = sys.argv[2] if len(sys.argv) > 2 else '30'
    melhor = os.path.join(BUILD, 'melhor.kicad_pcb')
    st = estado(); e5 = st['etapas'].setdefault('5_itera', {'rodadas': 0, 'melhor': None, 'hist': []}); salva(st)
    if not os.path.exists(melhor):
        shutil.copy(os.environ.get('BASE', BOARD), melhor); companions(melhor)
        b = pcbnew.LoadBoard(melhor); KEEP.append(b); ok, falha, _ = P.alarga(b); nd = P.limpa_pontas(b); fill(b); pcbnew.SaveBoard(melhor, b)
        log("base: larguras +%d (-%d), pontas %d" % (ok, falha, nd))
    r0, d0 = drc(melhor, os.path.join(BUILD, 'drc_melhor.json'))
    e5['melhor'] = pontua(r0)
    log("etapa 5: melhor atual %s (pontos %d)" % (r0, pontua(r0)))
    for k in range(rodadas):
        r0, d0 = drc(melhor, os.path.join(BUILD, 'drc_melhor.json'))
        ruins = redes_ruins(d0)
        if not ruins: log("nada a melhorar"); break
        b = pcbnew.LoadBoard(melhor); KEEP.append(b)
        n = arranca(b, ruins)
        log("rodada %d: arrancadas %d trilhas de %d redes: %s" % (k+1, n, len(ruins), sorted(ruins)))
        base = os.path.join(BUILD, 'it_base.kicad_pcb'); fill(b); pcbnew.SaveBoard(base, b); companions(base)
        tag = 'it%d' % (e5['rodadas']+1)
        out = E3.roda(tag, passes, base)
        pp = os.path.join(BUILD, 'it_post.kicad_pcb')
        b = pcbnew.LoadBoard(out); KEEP.append(b)
        ok, falha, falhas = P.alarga(b); nd = P.limpa_pontas(b)
        fill(b); pcbnew.SaveBoard(pp, b); companions(pp)
        r, d = drc(pp, os.path.join(BUILD, 'drc_it_post.json'))
        log("rodada %d: larguras +%d (-%d), pontas %d, DRC %s (pontos %d)" % (k+1, ok, falha, nd, r, pontua(r)))
        e5['rodadas'] += 1; e5['hist'].append(dict(tag=tag, pontos=pontua(r), drc=r))
        if pontua(r) < e5['melhor']:
            shutil.copy(pp, melhor); companions(melhor); e5['melhor'] = pontua(r); log("  nova melhor: %d" % e5['melhor'])
        marca('5_itera', **{k_: v for k_, v in e5.items()})
if __name__ == '__main__': main()
