import sys,json
sys.path.insert(0,'.')
import pcbnew, roteia as RT
n=int(sys.argv[1]); novo=RT.paths(n)[1]
RT.st_all={}; d=RT.drc(n,{},tag='_c')
ids=set()
for v in d['violations']:
    if v['type'] in('clearance','copper_edge_clearance'):
        for i in v['items']:
            if i['description'].startswith('Track'): ids.add(i['uuid'])
b=pcbnew.LoadBoard(novo); K=[]
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in ids: b.Remove(t); K.append(t)
print('removidas',len(K))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(novo,b)
