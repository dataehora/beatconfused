"""Resumo de um drc json: ligacoes faltando por rede e violacoes por tipo (com posicao). Python comum."""
import json, sys, collections, re
d = json.load(open(sys.argv[1]))
c = collections.Counter()
for u in d.get('unconnected_items', []):
    m = re.findall(r'\[([^\]]+)\]', u['items'][0]['description'])
    c[m[0] if m else '?'] += 1
print('faltando por rede:', dict(c))
v = collections.defaultdict(list)
for x in d['violations']:
    v[(x['severity'], x['type'])].append(x)
for k, l in v.items():
    print(k, len(l))
    if len(sys.argv) > 2:
        for x in l[:int(sys.argv[2])]:
            print('   ', x['description'][:110], [i['description'][:50] for i in x['items']], round(x['items'][0]['pos']['x'], 2), round(x['items'][0]['pos']['y'], 2))
