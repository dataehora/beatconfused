"""Utilidades comuns das etapas de roteamento da PRINCIPAL (R12V4). Python do KiCad.
Placa roteada = kicad/student_v04_roteada.kicad_pcb (variavel de ambiente ROTA_BOARD muda o caminho).
NUNCA roda sobre a placa posicionada kicad/student_v04.kicad_pcb."""
import json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))          # student_v04/
KICAD = os.path.join(ROOT, 'kicad')
POS = os.path.join(KICAD, 'student_v04.kicad_pcb')                # posicionada, intacta
BOARD = os.environ.get('ROTA_BOARD', os.path.join(KICAD, 'student_v04_roteada.kicad_pcb'))
BUILD = os.path.join(HERE, 'build')
ESTADO = os.path.join(HERE, 'estado.json')
CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
FR = r"C:/Users/julia/AppData/Local/freerouting/freerouting.exe"
os.makedirs(BUILD, exist_ok=True)
assert os.path.abspath(BOARD) != os.path.abspath(POS), "nao rotear a placa posicionada"

def log(m):
    s = time.strftime("%H:%M:%S") + " " + str(m)
    print(s, flush=True); open(os.path.join(HERE, "build", "log.txt"), "a", encoding="utf-8").write(s + chr(10))
def estado():
    return json.load(open(ESTADO, encoding='utf-8')) if os.path.exists(ESTADO) else {"etapas": {}}
def salva(st):
    json.dump(st, open(ESTADO, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
def marca(nome, **kw):
    st = estado(); e = st['etapas'].setdefault(nome, {}); e.update(kw); e['quando'] = time.strftime("%Y-%m-%d %H:%M"); salva(st)

def drc(board=None, out=None):
    board = board or BOARD
    out = out or os.path.join(BUILD, 'drc.json')
    subprocess.run([CLI, 'pcb', 'drc', '--schematic-parity', '--severity-all', '--format', 'json', '--units', 'mm', '-o', out, board],
                   capture_output=True, text=True)
    d = json.load(open(out, encoding='utf-8'))
    from collections import Counter
    c = Counter(); 
    for v in d.get('violations', []): c[(v['severity'], v['type'])] += 1
    un = len(d.get('unconnected_items', [])); par = len(d.get('schematic_parity', []))
    err = sum(n for (s, t), n in c.items() if s == 'error'); war = sum(n for (s, t), n in c.items() if s == 'warning')
    return dict(erros=err, avisos=war, faltando=un, paridade=par, tipos={f"{s}:{t}": n for (s, t), n in c.items()}), d

import math
def mm(v): import pcbnew; return pcbnew.FromMM(float(v))
def add_track(b, net, pts, w, layer=None):
    """Polilinha de trilhas (lista de (x,y) em mm) na rede `net` (nome)."""
    import pcbnew
    layer = pcbnew.B_Cu if layer is None else layer
    n = b.FindNet(net); L = 0.0; out = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0))); t.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(n); b.Add(t); out.append(t); L += math.hypot(x1-x0, y1-y0)
    return L, out
def add_via(b, net, x, y, dia=0.5, drill=0.3):
    import pcbnew
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and abs(t.GetPosition().x - mm(x)) < mm(0.05) and abs(t.GetPosition().y - mm(y)) < mm(0.05): return t
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(dia)); v.SetDrill(mm(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet(net)); b.Add(v); return v

def fill(b):
    import pcbnew
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

def companions(out):
    """Copia .kicad_pro/.kicad_dru/.kicad_sch (mesmo nome de `out`) e as folhas do esquema, para o DRC com paridade fora de kicad/."""
    import glob, shutil
    for ext in ('.kicad_pro', '.kicad_dru', '.kicad_sch'):
        s = BOARD.replace('.kicad_pcb', ext)
        d = out.replace('.kicad_pcb', ext)
        if os.path.exists(s) and os.path.abspath(s) != os.path.abspath(d): shutil.copy(s, d)
    d = os.path.dirname(out)
    if os.path.abspath(d) != os.path.abspath(KICAD):
        for f in glob.glob(os.path.join(KICAD, 'student_v04_?.kicad_sch')): shutil.copy(f, d)

def chave(t):
    import pcbnew
    if t.Type() == pcbnew.PCB_VIA_T:
        return ('v', t.GetNetname(), t.GetPosition().x, t.GetPosition().y)
    return ('t', t.GetNetname(), t.GetLayer(), t.GetWidth(), tuple(sorted(((t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)))))

def reaplica(b, base):
    """O ImportSpecctraSES apaga/parte as trilhas que ja existiam: devolve a `b` tudo o que `base` tinha e nao esta mais la
    (par USB, fan-out, corredor do USBLC6) e tira os restos de USB que o Freerouting acrescentou."""
    import pcbnew
    kb = {chave(t) for t in base.GetTracks()}
    atual = {chave(t): t for t in b.GetTracks()}
    for k, t in list(atual.items()):
        if t.GetNetname() in ('USB_DP', 'USB_DN') and k not in kb: b.Remove(t); GRAVE.append(t)
    n = 0
    for t in base.GetTracks():
        if chave(t) in atual: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            q = t.GetPosition(); c = pcbnew.PCB_VIA(b); c.SetPosition(q); c.SetWidth(t.GetWidth(pcbnew.F_Cu)); c.SetDrill(t.GetDrillValue())
            c.SetViaType(pcbnew.VIATYPE_THROUGH); c.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        else:
            c = pcbnew.PCB_TRACK(b); c.SetStart(t.GetStart()); c.SetEnd(t.GetEnd()); c.SetWidth(t.GetWidth()); c.SetLayer(t.GetLayer())
        c.SetNet(b.FindNet(t.GetNetname())); b.Add(c); GRAVE.append(c); n += 1
    log("reaplicados %d itens da placa-base" % n)

GRAVE = []   # mantem vivos os objetos python tirados/postos na placa (licao: pcbnew devolve SwigPyObject se forem coletados)
