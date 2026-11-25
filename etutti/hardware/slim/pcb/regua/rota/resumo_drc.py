import json,collections,sys
d=json.load(open(sys.argv[1]))
c=collections.Counter()
ex={}
for v in d['violations']+d.get('unconnected_items',[]):
    t=v.get('type','unconnected')
    its=tuple(sorted((i['description'].split(',')[0][:40]) for i in v['items']))
    k=(v['severity'],t,v['description'][:75],its)
    c[k]+=1; ex.setdefault(k,v['items'][0]['pos'])
for k,n in c.most_common(25): print(n,k,ex[k])
