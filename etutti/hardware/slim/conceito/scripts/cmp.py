import trimesh,numpy as np
def prof(fn,cx,cy,seat):
    s=trimesh.load(fn,force='mesh'); s.apply_scale(1000)
    sec=s.section(plane_origin=[cx,cy,0],plane_normal=[1,0,0])
    polys=[]
    for e in sec.entities:
        pts=sec.vertices[e.points]
        polys.append([(p[1]-cy,p[2]-seat) for p in pts])
    return polys
A=prof('ks20.glb',0.0,26.5,0.35)
B=prof('ks33d.glb',16.7,4.5,-1.4)
INK='#1E2124'; BLUE='#1F5FA8'
def draw(polys,ox,col):
    out=[]
    for p in polys:
        out.append('<polyline points="'+' '.join(f'{ox+y:.2f},{-z:.2f}' for y,z in p)+f'" fill="none" stroke="{col}" stroke-width="0.12"/>')
    return out
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-14 -19 76 27" width="1140" height="405">']
for ox,lab in ((0,'V4 · Gateron KS‑20 (altura cheia)'),(36,'Slim · Gateron LP Magnetic Jade Pro (KS‑33D)')):
    s.append(f'<rect x="{ox-10}" y="0" width="20" height="1.2" fill="#2F6B3A" opacity="0.5"/>')
    s.append(f'<text x="{ox}" y="5.5" font-family="IBM Plex Sans, Arial" font-size="1.4" font-weight="700" fill="{INK}" text-anchor="middle">{lab}</text>')
s+=draw(A,0,INK); s+=draw(B,36,INK)
def dim(x,z0,z1,t,anchor='start'):
    return (f'<line x1="{x}" y1="{-z0}" x2="{x}" y2="{-z1}" stroke="{BLUE}" stroke-width="0.1"/>'
            f'<line x1="{x-0.6}" y1="{-z0}" x2="{x+0.6}" y2="{-z0}" stroke="{BLUE}" stroke-width="0.1"/><line x1="{x-0.6}" y1="{-z1}" x2="{x+0.6}" y2="{-z1}" stroke="{BLUE}" stroke-width="0.1"/>'
            f'<text x="{x+(0.8 if anchor=="start" else -0.8)}" y="{-(z0+z1)/2+0.4}" font-family="IBM Plex Mono, monospace" font-size="1.0" fill="{BLUE}" text-anchor="{anchor}">{t}</text>')
s.append(dim(9.5,0,11.1,'11,10 topo da carcaça'))
s.append(dim(-9.5,0,5.0,'5,00','end'))
s.append(dim(45.5,0,5.85,'5,85 topo da carcaça'))
s.append(dim(48.8,5.85,9.35,'3,5 curso'))
s.append(dim(26.5,1.3,2.5,'grade 1,2','end'))
s.append(dim(26.5,-1.2,-3.7,'poste 2,5 abaixo da PCB','end'))
s.append(f'<text x="-13" y="7.6" font-family="IBM Plex Sans, Arial" font-size="1.0" fill="#5B6168">Cortes reais dos modelos STEP pelo eixo da haste · faixa verde = PCB de 1,2 mm · cotas do desenho oficial da Gateron</text>')
s.append('</svg>')
open('/home/claude/slim/svg/sw_cmp.svg','w').write('\n'.join(s))
print('ok')
