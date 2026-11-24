import math
INK='#1E2124'; BLUE='#1F5FA8'; G='#22C55E'
DOTS={'L':(0,1.75),'H':(0,-1.75),'M1':(-1.55,0),'M2':(0,0),'M3':(1.55,0)}
REGS=[('L',['L']),('LM',['L','M1']),('M',['M1']),('MM',['M1','M3']),('MH',['M1','H']),('LH',['L','H']),('H',['H'])]
def sym(cx,cy,dots,scale=1.0):
    s=f'<circle cx="{cx}" cy="{cy}" r="{2.6*scale}" fill="#FFFFFF" stroke="{INK}" stroke-width="0.25"/>'
    for dy in (-0.9,0.9): s+=f'<line x1="{cx-2.55*scale}" y1="{cy+dy*scale}" x2="{cx+2.55*scale}" y2="{cy+dy*scale}" stroke="{INK}" stroke-width="0.15"/>'
    for k in ('M1','M2','M3'):
        if k not in dots: s+=f'<circle cx="{cx+DOTS[k][0]*scale}" cy="{cy}" r="{0.42*scale}" fill="none" stroke="#B9B3A6" stroke-width="0.12"/>'
    for d in dots: s+=f'<circle cx="{cx+DOTS[d][0]*scale}" cy="{cy+DOTS[d][1]*scale}" r="{0.5*scale}" fill="{INK}"/>'
    return s
o=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-22 -22 150 46" width="1500" height="460">']
# volume knob
cx,cy=0,0
pts_in=[];pts_out=[]
for i in range(49):
    t=i/48; a=math.radians(210-t*255)
    pts_in.append((cx+9.7*math.cos(a),cy-9.7*math.sin(a))); pts_out.append((cx+(9.9+1.5*t)*math.cos(a),cy-(9.9+1.5*t)*math.sin(a)))
o.append('<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in pts_out+pts_in[::-1])+f'" fill="{INK}"/>')
a=math.radians(228); o.append(f'<circle cx="{cx+10.2*math.cos(a):.2f}" cy="{cy-10.2*math.sin(a):.2f}" r="0.6" fill="{INK}"/>')
o.append(f'<text x="{cx+10.2*math.cos(a)-1:.2f}" y="{cy-10.2*math.sin(a)+3:.2f}" font-family="IBM Plex Mono, monospace" font-size="1.8" fill="{INK}" text-anchor="end">OFF</text>')
o.append(f'<circle cx="{cx}" cy="{cy}" r="8.2" fill="none" stroke="{G}" stroke-width="1.4" opacity="0.6"/>')
o.append(f'<circle cx="{cx}" cy="{cy}" r="6.2" fill="#2B2D31"/><line x1="{cx}" y1="{cy}" x2="{cx-4}" y2="{cy+4}" stroke="#F1E9D6" stroke-width="0.8" stroke-linecap="round"/>')
o.append(f'<text x="0" y="17" font-family="IBM Plex Sans, Arial" font-size="2.2" font-weight="700" fill="{INK}" text-anchor="middle">Volume · contínuo</text>')
o.append(f'<text x="0" y="20.2" font-family="IBM Plex Sans, Arial" font-size="1.8" fill="#5B6168" text-anchor="middle">clique ao sair de OFF (liga + LED), depois sobe sem passos</text>')
# register knob
cx=48
for i,(nm,d) in enumerate(REGS):
    a=math.radians(225-i*45); px=cx+13.6*math.cos(a); py=-13.6*math.sin(a)
    o.append(sym(round(px,2),round(py,2),d))
    o.append(f'<text x="{px+ (4 if math.cos(a)>0.3 else -4 if math.cos(a)<-0.3 else 0):.2f}" y="{py+ (0.6 if abs(math.cos(a))>0.3 else (-3.6 if math.sin(a)>0 else 4.6)):.2f}" font-family="IBM Plex Mono, monospace" font-size="1.7" fill="{BLUE}" text-anchor="{"start" if math.cos(a)>0.3 else "end" if math.cos(a)<-0.3 else "middle"}">{i+1} {nm}</text>')
o.append(f'<circle cx="{cx}" cy="0" r="6.2" fill="#2B2D31"/><line x1="{cx}" y1="0" x2="{cx-4}" y2="4" stroke="#F1E9D6" stroke-width="0.8" stroke-linecap="round"/>')
o.append(f'<text x="{cx}" y="20.2" font-family="IBM Plex Sans, Arial" font-size="2.2" font-weight="700" fill="{INK}" text-anchor="middle">Registros · 7 posições fixas</text>')
# legend of symbols
lx=80
o.append(f'<text x="{lx}" y="-16" font-family="IBM Plex Sans, Arial" font-size="2.0" font-weight="700" fill="{INK}">Símbolos (L embaixo · M no meio · H em cima)</text>')
for i,(nm,d) in enumerate(REGS):
    col=i%4; row=i//4
    x=lx+4+col*12; y=-8+row*13
    o.append(sym(x,y,d,1.25))
    o.append(f'<text x="{x}" y="{y+5.6}" font-family="IBM Plex Mono, monospace" font-size="1.8" fill="{INK}" text-anchor="middle">{i+1} {nm}</text>')
o.append(f'<text x="{lx}" y="20" font-family="IBM Plex Sans, Arial" font-size="1.6" fill="#5B6168">anéis cinza = posições M vazias (só referência; não são impressos)</text>')
o.append('</svg>')
open('/home/claude/slim/svg/knobs7.svg','w').write('\n'.join(o))
