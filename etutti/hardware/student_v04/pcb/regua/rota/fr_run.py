"""Metodo misto: OUT a mao (A* proprio, folga 0,3 de CLK/SER/QHP) + Freerouting para o resto + planos de GND.
Uso: python fr_run.py N [passes]   (python do KiCad). Idempotente: refaz a partir da placa entregue."""
import json, os, subprocess, sys, time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import pcbnew
import roteia as RT, gnd, lib_rota as R
FR=r"C:/Users/julia/AppData/Local/freerouting/freerouting.exe"
def log(m): print(time.strftime("%H:%M:%S"),m,flush=True)
n=int(sys.argv[1]); passes=sys.argv[2] if len(sys.argv)>2 else "40"
RT.st_all=R.load_state(RT.STATE); st=RT.st_all.setdefault("R%d"%n,{})
st.clear(); st['prep']=False
RT.prep(n,st)
orig,novo=RT.paths(n)
pro=novo.replace('.kicad_pcb','.kicad_pro')
p=json.load(open(pro,encoding='utf-8'))
cl=p['net_settings']['classes']
d=dict(cl[0]); d['name']='Alimentacao'; d['track_width']=0.3; d['priority']=1
if not any(c['name']=='Alimentacao' for c in cl): cl.append(d)
p['net_settings']['netclass_patterns']=[{'netclass':'Alimentacao','pattern':'+3V3'}]
json.dump(p,open(pro,'w',encoding='utf-8'),indent=2)
b=pcbnew.LoadBoard(novo); ctx=R.Ctx(b)
# 1) OUT a mao
mode=os.environ.get('PREOUT','esc')
if mode=='1': ok=RT.route_net(ctx,'OUT',0.2,0.2,(1.0,1.35),30.0,st)
elif mode=='esc':
    only=tuple(os.environ.get('ESCNETS','OUT,GND').split(','))
    if 'GND' in only: gnd.local_links(ctx,b); ctx.refresh()
    RT.escapes(ctx,n,st,only=only)
    if os.environ.get('PRE3V3')=='1':
        ok3=RT.route_net(ctx,'+3V3',0.3,0.2,(1.0,4.0),15.0,st); log('3V3 a mao: %s'%ok3); ok='escapes'
else: ok=None
if mode=='esc': ok='escapes'
spec={p[0]:p for p in RT.default_order(n)}
for nm_ in [x for x in os.environ.get('PRENETS','').split(',') if x]:
    p=spec[nm_]; log('%s a mao: %s'%(nm_,RT.route_net(ctx,nm_,p[1],p[2],p[3],p[4],st)))
log("OUT a mao: %s"%ok); st['OUT_mao']=ok
gnd.add_zones(b,ctx); gnd.fill(b)
pcbnew.SaveBoard(novo,b)
# 2) Freerouting
b=pcbnew.LoadBoard(novo)
dsn=os.path.join(HERE,'build','R%d.dsn'%n); ses=os.path.join(HERE,'build','R%d.ses'%n)
pcbnew.ExportSpecctraDSN(b,dsn)
if os.environ.get('FRW'):
    t=open(dsn,encoding='utf-8').read().replace('(width 200)','(width %s)'%os.environ['FRW']); open(dsn,'w',encoding='utf-8').write(t)
t0=time.time()
r=subprocess.run([FR,'-de',dsn,'-do',ses,'-mp',passes],capture_output=True,text=True)
open(os.path.join(HERE,'build','fr_R%d.log'%n),'w',encoding='utf-8').write(r.stdout+r.stderr)
log("freerouting %.0fs"%(time.time()-t0))
b=pcbnew.LoadBoard(novo)
log("import ses: %s"%pcbnew.ImportSpecctraSES(b,ses))
gnd.fill(b)
pcbnew.SaveBoard(novo,b)
st['freerouting_s']=round(time.time()-t0)
R.save_state(RT.STATE,RT.st_all)
RT.drc(n,st); R.save_state(RT.STATE,RT.st_all)
