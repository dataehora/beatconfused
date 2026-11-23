"""Fecha ligacoes abertas apontadas pelo DRC (pares pad/trilha) com A* proprio, sem depender da conectividade por celulas.
Uso: python fecha_par.py N"""
import json, os, sys, time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import pcbnew, roteia as RT, lib_rota as R
from lib_rota import F,B,mm,nm
def log(m): print(time.strftime("%H:%M:%S"),m,flush=True)
SPEC={p[0]:p for p in RT.default_order(8)}
def cells_of(ctx,b,it):
    d=it['description']; u=it['uuid']
    g=ctx.g
    if d.startswith('Pad'):
        num=d.split()[1]; ref=d.split(' of ')[1].split()[0]
        for fp in b.GetFootprints():
            if fp.GetReference()==ref:
                for p in fp.Pads():
                    if p.GetNumber()==num:
                        bb=p.GetBoundingBox()
                        return ctx.pad_cells((mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetX()+bb.GetWidth()),mm(bb.GetY()+bb.GetHeight())),(B,)), (mm(p.GetX()),mm(p.GetY()))
    for t in b.GetTracks():
        if t.m_Uuid.AsString()==u:
            L=F if t.GetLayer()==pcbnew.F_Cu else B
            s,e=t.GetStart(),t.GetEnd()
            i0,j0=g.ix(mm(s.x)),g.iy(mm(s.y)); i1,j1=g.ix(mm(e.x)),g.iy(mm(e.y))
            n=max(abs(i1-i0),abs(j1-j0),1)
            cs={(L,i0+round((i1-i0)*k/n),j0+round((j1-j0)*k/n)) for k in range(n+1)}
            return cs,(mm(e.x),mm(e.y))
    return None,None
def main(n):
    novo=RT.paths(n)[1]
    b=pcbnew.LoadBoard(novo); ctx=R.Ctx(b)
    RT.st_all={}
    d=RT.drc(n,{},tag='_par')
    for v in d['unconnected_items']:
        its=v['items']
        if any('Zone' in i['description'] for i in its): continue
        net=its[0]['description'].split('[')[1].split(']')[0]
        if net not in SPEC: log("rede %s fora do plano"%net); continue
        (_,wp,wm,lm,vc)=SPEC[net]
        A,_=cells_of(ctx,b,its[0]); Bc,bxy=cells_of(ctx,b,its[1])
        if not A or not Bc: log("sem celulas: %s"%[i['description'][:40] for i in its]); continue
        ok=False
        for w in (wp,wm):
            path,why=ctx.route(net,w,A,Bc,bxy,layer_mult=lm,via_cost=vc,maxexp=int(os.environ.get('MAXEXP','600000')))
            log("%s %s -> %s w=%.2f: %s"%(net,its[0]['description'][:30],its[1]['description'][:30],w,why))
            if path:
                ctx.write_path(net,w,path); ctx.refresh(); ok=True; break
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(novo,b)
    st={};RT.drc(n,st,tag='_par')
if __name__=="__main__": main(int(sys.argv[1]))
