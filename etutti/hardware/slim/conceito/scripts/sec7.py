import sys,math
sys.path.insert(0,'/home/claude/slim/gen')
import trimesh
from wave5 import H as H5, FRONT, BACK, D, INK, BLUE, ACC
CT=[10.85,12.85,14.85,17.85]          # cover tops (bayan steps 2/2/3)
OFF=CT[0]+3.16-10.6
def S(y):
    z=H5(y)+OFF
    if y<FRONT+4: t=(FRONT+4-y)/4; z-=1.2*(1-math.sqrt(max(0,1-t*t)))
    if y>BACK-6: t=(y-(BACK-6))/6; z-=2.0*(1-math.sqrt(max(0,1-t*t)))
    return z
def row_of(y):
    for r in range(4):
        if abs(y-r*D)<=8.01: return r
    return None
def ceil(y):
    r=row_of(y)
    return CT[r]+0.3 if r is not None else S(y)-1.5
# real switch section (KS-33D) through stem axis, seat at 0
s=trimesh.load('/home/claude/slim/step/ks33d.glb',force='mesh'); s.apply_scale(1000)
sec=s.section(plane_origin=[16.7,4.5,0],plane_normal=[1,0,0])
SW=[[(p[1]-4.5,p[2]+1.4) for p in sec.vertices[e.points]] for e in sec.entities]
def section(name,cut_rows,title):
    y0,y1=FRONT,BACK; W=(y1-y0)+30; px=8
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{y0-10:.1f} -32 {W:.1f} 44" width="{W*px:.0f}" height="{44*px:.0f}">']
    Z=lambda z:-z
    yy=[y0+i*(y1-y0)/500 for i in range(501)]
    o.append(f'<rect x="{y0:.2f}" y="{Z(1.6)}" width="{y1-y0:.2f}" height="1.6" fill="#8F8A80"/>')
    for r in range(4):
        ct=CT[r]; pt=ct-5.85; pb=pt-1.2; yc=r*D; cut=r in cut_rows; op=1 if cut else 0.35
        o.append(f'<rect x="{yc-7.6:.2f}" y="{Z(pb):.2f}" width="15.2" height="{pb-1.6:.2f}" fill="#8F8A80" opacity="{op}"/>')
        o.append(f'<rect x="{yc-2.9:.2f}" y="{Z(pb):.2f}" width="5.8" height="2.8" fill="#F4F1EA" opacity="{op}"/>')  # post pocket
        o.append(f'<rect x="{yc-7.5:.2f}" y="{Z(pt):.2f}" width="15" height="1.2" fill="#2F6B3A" opacity="{op}"/>')
        o.append(f'<rect x="{yc+3.0:.2f}" y="{Z(pb):.2f}" width="2.9" height="1.1" fill="{ACC}" opacity="{op}"/>')  # hall sensor bottom side
        o.append(f'<rect x="{yc-7.8:.2f}" y="{Z(pt+2.5):.2f}" width="15.6" height="1.2" fill="#3F3F46" opacity="{op}"/>')
        for p in SW:
            o.append('<polyline points="'+' '.join(f'{yc+a:.2f},{Z(pt+b):.2f}' for a,b in p)+f'" fill="none" stroke="{INK}" stroke-width="0.1" opacity="{op}"/>')
        cb=ct+3.7
        o.append(f'<path d="M{yc-7.5:.2f},{Z(cb):.2f} L{yc-7.5:.2f},{Z(cb+1.6):.2f} Q{yc:.2f},{Z(cb+5.2):.2f} {yc+7.5:.2f},{Z(cb+1.6):.2f} L{yc+7.5:.2f},{Z(cb):.2f} Z" fill="{"#FBF9F3" if cut else "#E5E1D8"}" stroke="{INK}" stroke-width="0.15" opacity="{1 if cut else 0.6}"/>')
    # lid: top S, underside ceil, holes at cut rows (Ø16 through, Ø17 counterbore to CT+1.8)
    def top(y):
        for r in cut_rows:
            d=abs(y-r*D)
            if d<8.5: return CT[r]+1.8 if d>=8.0 else None
        return S(y)
    seg=[];segs=[]
    for y in yy:
        t=top(y)
        if t is None:
            if seg: segs.append(seg); seg=[]
        else: seg.append((y,t))
    if seg: segs.append(seg)
    for sg in segs:
        pts=sg+[(y,min(ceil(y),t-1.2)) for y,t in reversed(sg)]
        o.append('<polygon points="'+' '.join(f'{y:.2f},{Z(z):.2f}' for y,z in pts)+f'" fill="#EFE6D2" stroke="{INK}" stroke-width="0.2"/>')
    o.append(f'<rect x="{y0:.2f}" y="{Z(S(y0+0.5)):.2f}" width="1.6" height="{S(y0+0.5)-1.6:.2f}" fill="#EFE6D2" stroke="{INK}" stroke-width="0.15"/>')
    o.append(f'<rect x="{y1-1.6:.2f}" y="{Z(S(y1-0.5)):.2f}" width="1.6" height="{S(y1-0.5)-1.6:.2f}" fill="#EFE6D2" stroke="{INK}" stroke-width="0.15"/>')
    for r in range(4):
        o.append(f'<text x="{r*D:.2f}" y="{Z(CT[r]+3.7+5.2+1.4):.2f}" font-family="IBM Plex Mono, monospace" font-size="1.7" fill="{BLUE}" text-anchor="middle">{CT[r]:.2f}</text>')
    o.append(f'<text x="{y0:.2f}" y="6.5" font-family="IBM Plex Sans, Arial" font-size="2.1" fill="{INK}">{title}</text>')
    o.append(f'<text x="{y0:.2f}" y="9.3" font-family="IBM Plex Sans, Arial" font-size="1.7" fill="#5B6168">switch = corte real do STEP KS‑33D · azul = topo da carcaça de cada fileira (degraus 2/2/3) · laranja = sensor Hall na face de baixo · bolso claro = poste do switch</text>')
    o.append('</svg>')
    open(f'/home/claude/slim/svg/{name}','w').write('\n'.join(o))
section('L_secA.svg',[0,2],'Corte A · centro das fileiras 1 e 3')
section('L_secB.svg',[1,3],'Corte B · centro das fileiras 2 e 4')
print('max',round(max(S(y) for y in [FRONT+i*0.1 for i in range(890)]),2),'front',round(S(FRONT+0.3),2))
