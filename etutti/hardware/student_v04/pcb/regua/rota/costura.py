"""Costura dos planos de GND: liga todos os fragmentos do plano de F.Cu e B.Cu com vias de GND,
em rodadas (preenche, acha fragmentos fora do conjunto principal, poe via onde ha cobre dos dois lados)."""
import os, sys, time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import numpy as np, pcbnew
import lib_rota as R
from lib_rota import F,B,mm,nm
KEEP=[]
def log(m): print(time.strftime("%H:%M:%S"),m,flush=True)

def polys(b, L):
    out=[]
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname()!='GND' or not z.IsOnLayer(L): continue
        fs=z.GetFilledPolysList(L)
        for k in range(fs.OutlineCount()):
            o=fs.Outline(k)
            pts=np.array([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())])
            holes=[]
            for h in range(fs.HoleCount(k)):
                hh=fs.Hole(k,h); holes.append(np.array([(mm(hh.CPoint(i).x),mm(hh.CPoint(i).y)) for i in range(hh.PointCount())]))
            out.append((pts,holes))
    return out

def pip(x,y,pts):
    xs,ys=pts[:,0],pts[:,1]; x2,y2=np.roll(xs,-1),np.roll(ys,-1)
    c=((ys<=y)&(y2>y))|((y2<=y)&(ys>y))
    with np.errstate(divide='ignore',invalid='ignore'):
        xi=xs+(y-ys)*(x2-xs)/(y2-ys)
    return bool(np.count_nonzero(c&(xi>x))%2)

_BB={}
def inside(x,y,poly):
    pts,holes=poly
    k=id(pts)
    if k not in _BB: _BB[k]=(pts[:,0].min(),pts[:,1].min(),pts[:,0].max(),pts[:,1].max())
    b=_BB[k]
    if x<b[0] or x>b[2] or y<b[1] or y>b[3]: return False
    return pip(x,y,pts) and not any(pip(x,y,h) for h in holes)

def edge_dist(x,y,poly):
    d=1e9
    for pts in [poly[0]]+poly[1]:
        a=pts; c=np.roll(pts,-1,axis=0); ab=c-a; L2=(ab**2).sum(1); L2[L2==0]=1
        t=np.clip(((x-a[:,0])*ab[:,0]+(y-a[:,1])*ab[:,1])/L2,0,1)
        dd=np.hypot(x-(a[:,0]+t*ab[:,0]),y-(a[:,1]+t*ab[:,1])).min()
        d=min(d,dd)
    return d

def components(b):
    PB,PF=polys(b,pcbnew.B_Cu),polys(b,pcbnew.F_Cu)
    nodes=[('B',i) for i in range(len(PB))]+[('F',i) for i in range(len(PF))]
    idx={n:k for k,n in enumerate(nodes)}; par=list(range(len(nodes)))
    def find(a):
        while par[a]!=a: par[a]=par[par[a]]; a=par[a]
        return a
    for t in b.GetTracks():
        if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=='GND':
            x,y=mm(t.GetX()),mm(t.GetY())
            ib=[i for i,p in enumerate(PB) if inside(x,y,p)]; jf=[i for i,p in enumerate(PF) if inside(x,y,p)]
            if ib and jf: par[find(idx[('B',ib[0])])]=find(idx[('F',jf[0])])
    return PB,PF,nodes,idx,find

def run(b, ctx, rounds=8):
    for r in range(rounds):
        R.Ctx  # noqa
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        PB,PF,nodes,idx,find=components(b)
        # componente principal = o de maior area do plano de topo
        big=max(range(len(PF)),key=lambda i:(np.ptp(PF[i][0][:,0])*np.ptp(PF[i][0][:,1]))) if PF else None
        mainroot=find(idx[('F',big)])
        bad=[n for n in nodes if find(idx[n])!=mainroot]
        log("rodada %d: %d fragmentos B, %d F, fora do principal: %d"%(r,len(PB),len(PF),len(bad)))
        if not bad: return True
        ctx.refresh(); bl,viab=ctx.masks('GND',0.2); g=ctx.g
        placed=0
        for (L,i) in bad:
            poly=(PB if L=='B' else PF)[i]; other=(PF if L=='B' else PB); oL='F' if L=='B' else 'B'
            x0,y0=poly[0].min(0); x1,y1=poly[0].max(0)
            best=None
            for yy in np.arange(y0,y1+0.01,0.1):
                for xx in np.arange(x0,x1+0.01,0.1):
                    ci,cj=g.ix(xx),g.iy(yy); xx2,yy2=g.pt(ci,cj)
                    if ci<0 or cj<0 or ci>=g.nx or cj>=g.ny: continue
                    if viab[cj,ci]: continue
                    if not inside(xx2,yy2,poly): continue
                    if not any(inside(xx2,yy2,o) and find(idx[(oL,k)])==mainroot for k,o in enumerate(other)): continue
                    d=edge_dist(xx2,yy2,poly)
                    if d<0.0: continue
                    if best is None or d>best[0]: best=(d,xx2,yy2)
            if best:
                ctx.add_via('GND',best[1],best[2]); placed+=1; ctx.refresh(); bl,viab=ctx.masks('GND',0.2)
        log("  vias postas: %d"%placed)
        if not placed:
            # fragmento estreito: liga por trilha curta de GND ate o plano principal (pode usar via)
            done=0
            for (L,i) in bad:
                poly=(PB if L=='B' else PF)[i]
                x0,y0=poly[0].min(0); x1,y1=poly[0].max(0)
                bl,viab=ctx.masks('GND',0.2); free=[~bl[0],~bl[1]]
                src=set(); tgt=set()
                for yy in np.arange(y0-4,y1+4,0.1):
                    for xx in np.arange(x0-4,x1+4,0.1):
                        ci,cj=g.ix(xx),g.iy(yy); x2,y2=g.pt(ci,cj)
                        if ci<0 or cj<0 or ci>=g.nx or cj>=g.ny: continue
                        if x0<=x2<=x1 and y0<=y2<=y1 and inside(x2,y2,poly) and free[1 if L=='B' else 0][cj,ci]:
                            src.add((1 if L=='B' else 0,ci,cj))
                        else:
                            for lay,PP,fl in ((1,PB,'B'),(0,PF,'F')):
                                if free[lay][cj,ci] and any(inside(x2,y2,o) and find(idx[(fl,k)])==mainroot for k,o in enumerate(PP)):
                                    tgt.add((lay,ci,cj)); break
                if not src or not tgt: continue
                cx,cy=(x0+x1)/2,(y0+y1)/2
                tb=min(tgt,key=lambda c:(g.pt(c[1],c[2])[0]-cx)**2+(g.pt(c[1],c[2])[1]-cy)**2); cx,cy=g.pt(tb[1],tb[2])
                path,why=ctx.route('GND',0.2,src,tgt,(cx,cy),layer_mult=(1.0,1.0),via_cost=12.0,maxexp=int(os.environ.get("GMAX","3000000")))
                log('  trilha de GND para fragmento %s: %s'%(L,why))
                if path:
                    ctx.write_path('GND',0.2,path); ctx.refresh(); done+=1
            if done: continue
            # sem como ligar: tira as vias de costura soltas dentro dos fragmentos ruins (o cobre sem ligacao some no preenchimento)
            badpolys=[((PB if L=='B' else PF)[i]) for (L,i) in bad]
            tr=[t for t in b.GetTracks() if t.Type()!=pcbnew.PCB_VIA_T and t.GetNetname()=='GND']
            rem=[]
            for t in b.GetTracks():
                if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=='GND':
                    x,y=mm(t.GetX()),mm(t.GetY())
                    if any(inside(x,y,p) for p in badpolys) and not any(abs(e.x-t.GetX())<3000 and abs(e.y-t.GetY())<3000 for o in tr for e in (o.GetStart(),o.GetEnd())):
                        rem.append(t)
            for t in rem: b.Remove(t); KEEP.append(t)
            log('  vias de costura soltas removidas: %d'%len(rem))
            if rem: continue
            for (L,i) in bad:
                p=(PB if L=='B' else PF)[i][0]; log('  fragmento sem via: %s bbox u=%.2f..%.2f v=%.2f..%.2f'%(L,p[:,0].min()-10,p[:,0].max()-10,p[:,1].min()-17,p[:,1].max()-17))
            return False
    return False
