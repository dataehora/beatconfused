import math,sys,re
sys.path.insert(0,'/home/claude/slim/gen')
import geo
from geo import P,D,RB,OFFS,INK,ACC,BLUE,CREAM_TOP,CREAM_L,CREAM_F,iso,poly,hull,cylinder,circle_pts,rr_outline,keys,prism
import cases as C0
from board import T,R,Cc,BOT,TOP,PCB,svg
KEYS=keys()
FRONT=-18.5; BACK=70.6; RIGHT=149; LEFT=-90
RAD=500.0; YA=60.0; ZA=13.6
REG=(-46,0); VOL=(-46,3*D)
# ROW HEIGHTS ARE INPUTS (bayan / Student V4): steps 2, 2, 3 mm; pitch 18.5; rows 16.02
ROWZ=[10.6,12.6,14.6,17.6]
SL=(ROWZ[1]-ROWZ[0])/D          # plane through rows 1-3 (equal steps => straight, 7.1 deg)
DSTEP=ROWZ[3]-(ROWZ[0]+SL*3*D)   # extra rise before row 4 = 1.0
Y0S=38.3; WS=3.6; YC=50.0; LC=12.0
def ss(t):
    t=max(0,min(1,t)); return t*t*t*(t*(6*t-15)+10)
def H(y):
    z=ROWZ[0]+SL*y+DSTEP*ss((y-Y0S)/WS)
    if y>YC:
        u=min(y-YC,LC); z-=SL*u*u/(2*LC)+(SL*(y-YC-LC) if y>YC+LC else 0)
    return z
def wave(y):
    z=H(y)
    rf,df=4,1.2
    if y<FRONT+rf:
        t=(FRONT+rf-y)/rf; z-=df*(1-math.sqrt(max(0,1-t*t)))
    rb,db=6,2.0
    if y>BACK-rb:
        t=(y-(BACK-rb))/rb; z-=db*(1-math.sqrt(max(0,1-t*t)))
    return z
TANS=[]
def trough(r): return wave(r*D)
OUT=rr_outline(LEFT,FRONT,RIGHT,BACK,6)
def xext(y):
    xs=[]
    o=OUT
    for i in range(len(o)):
        a=o[i];b=o[(i+1)%len(o)]
        if (a[1]-y)*(b[1]-y)<=0 and a[1]!=b[1]:
            xs.append(a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]))
    return min(xs),max(xs)
def mix(c1,c2,t):
    a=[int(c1[i:i+2],16) for i in (1,3,5)];b=[int(c2[i:i+2],16) for i in (1,3,5)]
    return '#'+''.join(f'{int(a[i]+(b[i]-a[i])*t):02x}' for i in range(3))
def dens(o,m=1.5):
    out=[]
    for i in range(len(o)):
        a=o[i];b=o[(i+1)%len(o)];L=math.hypot(b[0]-a[0],b[1]-a[1]);k=max(1,int(L/m))
        for j in range(k): out.append((a[0]+(b[0]-a[0])*j/k,a[1]+(b[1]-a[1])*j/k))
    return out
# ---------- ISO
parts=prism(dens(OUT),0,lambda x,y:wave(y))
ys=[FRONT+0.05+i*0.8 for i in range(int((BACK-FRONT-0.1)/0.8)+1)]
strips=[]
for i in range(len(ys)-1):
    y0,y1=ys[i],ys[i+1]
    xa0,xb0=xext(y0); xa1,xb1=xext(y1)
    slope=(wave(y1)-wave(y0))/(y1-y0)
    t=max(0,min(1,0.05+slope*6.0))
    col=mix('#D9CCAE','#FAF4E6',t)
    q=[iso(xa0,y0,wave(y0)),iso(xb0,y0,wave(y0)),iso(xb1,y1,wave(y1)),iso(xa1,y1,wave(y1))]
    strips.append(poly(q,col,stroke=col,sw=0.12))
strips.reverse()
parts=parts[:-1]+strips  # replace flat top with shaded strips
JUN=[Y0S,Y0S+WS]
for yj in JUN:
    xa,xb=xext(yj); p1=iso(xa,yj,wave(yj)); p2=iso(xb,yj,wave(yj))
    parts.append(f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" stroke="#FFFFFF" stroke-width="0.5" stroke-opacity="0.9"/>')
# outline on top
parts.append('<polygon points="'+' '.join(f'{a:.2f},{b:.2f}' for a,b in [iso(x,y,wave(y)) for x,y in dens(OUT)])+f'" fill="none" stroke="{INK}" stroke-width="0.35"/>')
items=[]
for k in KEYS:
    z0=wave(k['y'])
    top='#2A2C30' if k['sharp'] else '#FCFAF4'; side='#111214' if k['sharp'] else '#CFC8B8'
    g=cylinder(k['x'],k['y'],RB*0.95,z0-0.5,z0+4.0,top,side,dome=True,sw=0.25)
    tx,ty=iso(k['x'],k['y'],z0+4.0)
    if k['dot']:
        for dx in (-2.6,0,2.6):
            for dy in (-2.6,0,2.6):
                if (dx,dy)!=(0,0) and abs(dx)+abs(dy)<5:
                    a,b=iso(k['x']+dx,k['y']+dy,z0+4.0); g.append(f'<circle cx="{a:.2f}" cy="{b:.2f}" r="0.4" fill="#8A8578"/>')
    g.append(f'<text x="{tx:.2f}" y="{ty+0.9:.2f}" font-family="IBM Plex Sans, Arial" font-size="2.6" font-weight="600" text-anchor="middle" fill="{"#F1EEE6" if k["sharp"] else INK}">{k["n"]}</text>')
    items.append((k['x']+k['y'],g))
for (cx,cy),led in ((VOL,True),(REG,False)):
    z0=wave(cy)
    g=[]
    if led:
        ring=[iso(cx+8.2*math.cos(a),cy+8.2*math.sin(a),z0+0.2) for a in [2*math.pi*i/30 for i in range(30)]]
        g.append(poly(ring,'#22C55E',stroke='#22C55E',sw=1.6,extra='opacity="0.35"'))
        g.append(poly(ring,'none',stroke='#22C55E',sw=0.5))
    g.insert(0,poly([iso(cx+8.8*math.cos(2*math.pi*i/30),cy+8.8*math.sin(2*math.pi*i/30),z0) for i in range(30)],'#CDBF9F',stroke='#B9AD92',sw=0.3))
    g+=cylinder(cx,cy,7.4,z0-1.2,z0+0.2,'#E9F6EC' if led else '#C9CCD1','#B8C7BC' if led else '#9EA3AA',sw=0.25)
    g+=cylinder(cx,cy,6.2,z0+0.2,z0+2.6,'#3A3C41','#1D1E21',sw=0.3)
    a,b=iso(cx,cy,z0+2.6); c,d=iso(cx-3.8,cy-3.8,z0+2.6)
    g.append(f'<line x1="{a:.2f}" y1="{b:.2f}" x2="{c:.2f}" y2="{d:.2f}" stroke="#F1E9D6" stroke-width="0.8" stroke-linecap="round"/>')
    items.append((cx+cy,g))
items.sort(key=lambda t:-t[0])
for _,g in items: parts+=g
z=4.8
parts.append(poly([iso(-63+2.6*math.cos(2*math.pi*i/20),BACK+0.1,z+0) for i in range(1)],'none',sw=0))
q=[iso(-72-4.5,BACK+0.1,z-1.6),iso(-72+4.5,BACK+0.1,z-1.6),iso(-72+4.5,BACK+0.1,z+1.6),iso(-72-4.5,BACK+0.1,z+1.6)]
parts.append(poly(q,'#1E2124',sw=0.2))
parts.append(poly([iso(LEFT-0.1,63+2.6*math.cos(2*math.pi*i/20),z+2.6*math.sin(2*math.pi*i/20)) for i in range(20)],'#1E2124',sw=0.2))
nums=[]
for part in parts:
    for m in re.finditer(r'points="([^"]+)"',part):
        for pr in m.group(1).split():
            a,b=pr.split(','); nums.append((float(a),float(b)))
xs=[a for a,b in nums]; yss=[b for a,b in nums]
mx,Mx,my,My=min(xs)-6,max(xs)+6,min(yss)-6,max(yss)+6
open('/home/claude/slim/svg/K_iso.svg','w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{mx:.1f} {my:.1f} {Mx-mx:.1f} {My-my:.1f}" width="{(Mx-mx)*2.3:.0f}" height="{(My-my)*2.3:.0f}">'+'\n'.join(parts)+'</svg>')
# ---------- PLAN
minx=LEFT-8; maxx=RIGHT+8; miny=-BACK-8; maxy=-FRONT+14
s=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx:.1f} {miny:.1f} {maxx-minx:.1f} {maxy-miny:.1f}" width="{(maxx-minx)*2.4:.0f}" height="{(maxy-miny)*2.4:.0f}">']
s.append('<polygon points="'+' '.join(f'{x:.2f},{-y:.2f}' for x,y in OUT)+f'" fill="{CREAM_TOP}" stroke="{INK}" stroke-width="0.5"/>')
xa,xb=xext(40); s.append(f'<rect x="{xa:.1f}" y="{-(Y0S+WS):.2f}" width="{xb-xa:.1f}" height="{WS}" fill="#F59E0B" fill-opacity="0.35"/>')
s.append(f'<rect x="-88.5" y="-54.5" width="29" height="69" rx="2" fill="none" stroke="{BLUE}" stroke-width="0.35" stroke-dasharray="2 1.2"/>')
s.append(f'<text x="-74" y="-20" font-family="IBM Plex Sans, Arial" font-size="2.8" fill="{BLUE}" text-anchor="middle" transform="rotate(-90 -74 -20)">bateria 1000 mAh (frente)</text>')
for k in KEYS: s.append(C0.plan_key(k))
s.append(f'<circle cx="{REG[0]}" cy="{-REG[1]:.2f}" r="8.8" fill="#DDD2B8" stroke="#B9AD92" stroke-width="0.3"/><circle cx="{VOL[0]}" cy="{-VOL[1]:.2f}" r="8.8" fill="#DDD2B8" stroke="#B9AD92" stroke-width="0.3"/><circle cx="{VOL[0]}" cy="{-VOL[1]:.2f}" r="8.0" fill="none" stroke="#22C55E" stroke-width="1.1"/>')
s.append(C0.knob_plan(*VOL,'VOL',power=True)); s.append(C0.knob_plan(*REG,'REG',regs=True))
s.append(f'<rect x="-76.5" y="{-BACK-1.2:.2f}" width="9" height="2.4" rx="1.2" fill="{INK}"/><text x="-72" y="{-BACK+4:.2f}" font-family="IBM Plex Mono, monospace" font-size="2.6" fill="{INK}" text-anchor="middle">USB-C</text>')
s.append(f'<circle cx="{LEFT}" cy="-63" r="2.6" fill="{INK}"/><text x="{LEFT+3.5}" y="-62" font-family="IBM Plex Mono, monospace" font-size="2.6" fill="{INK}">OUT</text>')
yb=-FRONT+8
s.append(f'<line x1="{LEFT}" y1="{yb}" x2="{RIGHT}" y2="{yb}" stroke="{BLUE}" stroke-width="0.3"/><text x="{(LEFT+RIGHT)/2:.1f}" y="{yb-1.2}" font-family="IBM Plex Mono, monospace" font-size="3.2" fill="{BLUE}" text-anchor="middle">{RIGHT-LEFT:.0f} mm</text>')
xr=RIGHT+4
s.append(f'<line x1="{xr}" y1="{-BACK:.2f}" x2="{xr}" y2="{-FRONT:.2f}" stroke="{BLUE}" stroke-width="0.3"/><text x="{xr+1.5}" y="{(-BACK-FRONT)/2:.1f}" font-family="IBM Plex Mono, monospace" font-size="3.2" fill="{BLUE}" transform="rotate(90 {xr+1.5} {(-BACK-FRONT)/2:.1f})" text-anchor="middle">{BACK-FRONT:.0f} mm</text>')
s.append('</svg>'); open('/home/claude/slim/svg/K_plan.svg','w').write('\n'.join(s))
print('rows',[round(H(r*D),2) for r in range(4)],'max',round(max(wave(FRONT+i*0.1) for i in range(890)),2),'h@-14',round(wave(-14),2))
