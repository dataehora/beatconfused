"""Pos-processamento: largura minima, alargar +3V3 para 0,3 onde cabe, costura de GND, limpeza, DRC final."""
import json, os, subprocess, sys, time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import pcbnew, roteia as RT, lib_rota as R, costura, gnd
from lib_rota import mm, nm
def log(m): print(time.strftime("%H:%M:%S"),m,flush=True)

def drc_json(n,tag):
    d=RT.drc(n,{},tag=tag); return d

def uuids(d,types):
    out={}
    for v in d.get('violations',[]):
        if v['type'] in types:
            for i in v['items']: out.setdefault(v['type'],[]).append(i['uuid'])
    return out

def by_uuid(b):
    return {t.m_Uuid.AsString():t for t in b.GetTracks()}

def fix_width(b, minw=0.15, to=0.15):
    k=0
    for t in b.GetTracks():
        if t.Type()!=pcbnew.PCB_VIA_T and mm(t.GetWidth())<minw-1e-6:
            t.SetWidth(nm(to)); k+=1
    return k

def widen_power(n,b,novo,w=0.3):
    """Alarga as trilhas de +3V3 para 0,3 mm; as que causarem violacao voltam para a largura anterior."""
    orig={}
    for t in b.GetTracks():
        if t.Type()!=pcbnew.PCB_VIA_T and t.GetNetname()=='+3V3' and mm(t.GetWidth())<w-1e-6:
            orig[t.m_Uuid.AsString()]=t.GetWidth(); t.SetWidth(nm(w))
    for it in range(4):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(novo,b)
        d=RT.drc(n,{},tag='_larg')
        bad=set()
        for v in d.get('violations',[]):
            if v['type'] in ('clearance','hole_clearance','shorting_items','copper_edge_clearance','solder_mask_bridge'):
                for i in v['items']:
                    if i['uuid'] in orig: bad.add(i['uuid'])
        # pads de GND que ficaram sem ligacao: volta as trilhas alargadas num raio de 2 mm
        near=[]
        for v in d.get('unconnected_items',[]):
            for i in v['items']:
                if 'Pad' in i['description'] and '[GND]' in i['description']:
                    near.append((i['pos']['x'],i['pos']['y']))
        tr=by_uuid(b)
        for u,t in tr.items():
            if u in orig and any((t.GetX()/1e6-px)**2+(t.GetY()/1e6-py)**2<4.0 for (px,py) in near):
                bad.add(u)
        if not bad: break
        for u in bad:
            if u in tr: tr[u].SetWidth(orig[u])
            orig.pop(u,None)
    keep=sum(1 for t in b.GetTracks() if t.Type()!=pcbnew.PCB_VIA_T and t.GetNetname()=='+3V3' and mm(t.GetWidth())>=w-1e-6)
    tot=sum(1 for t in b.GetTracks() if t.Type()!=pcbnew.PCB_VIA_T and t.GetNetname()=='+3V3')
    log("+3V3 a 0,3 mm: %d de %d trechos"%(keep,tot)); return keep,tot

if __name__=="__main__":
    n=int(sys.argv[1]); novo=RT.paths(n)[1]
    b=pcbnew.LoadBoard(novo); ctx=R.Ctx(b)
    log("larguras corrigidas: %d"%fix_width(b))
    gnd.stitch(ctx,b,pitch=float(os.environ.get('PITCH','3.0')))
    ok=costura.run(b,ctx); log("costura: %s"%ok)
    pcbnew.SaveBoard(novo,b)
    st={};RT.st_all={}
    RT.limpa_drc(n,st)
    b=pcbnew.LoadBoard(novo)
    if os.environ.get('WIDEN','1')=='1': widen_power(n,b,novo)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(novo,b)
    RT.limpa_drc(n,st)
    b=pcbnew.LoadBoard(novo); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(novo,b)
    RT.drc(n,st)
