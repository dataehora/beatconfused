import sys
sys.path.insert(0,'.')
import pcbnew, roteia as RT, lib_rota as R
n=int(sys.argv[1]); net=sys.argv[2]; novo=RT.paths(n)[1]
b=pcbnew.LoadBoard(novo); K=[]
for t in list(b.GetTracks()):
    if t.GetNetname()==net: b.Remove(t); K.append(t)
ctx=R.Ctx(b)
RT.escapes(ctx,n,{},only=(net,))
spec={p[0]:p for p in RT.default_order(n)}[net]
print(RT.route_net(ctx,net,spec[1],spec[2],spec[3],spec[4],{}))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(novo,b)
RT.st_all={}; st={}; RT.drc(n,st); RT.limpa_drc(n,st)
b=pcbnew.LoadBoard(novo); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(novo,b); RT.drc(n,st)
