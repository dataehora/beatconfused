import math
P=18.5; D=math.sqrt(P*P-(P/2)**2); RB=7.5
OFFS=[0,-P/2,0,-P/2]
NOTES=[["A3","C4","D#4","F#4","A4","C5","D#5","F#5"],
       ["G3","A#3","C#4","E4","G4","A#4","C#5","E5"],
       ["G#3","B3","D4","F4","G#4","B4","D5","F5"],
       ["F#3","A3","C4","D#4","F#4","A4","C5","D#5"]]
def keys():
    out=[]
    for r in range(4):
        for c in range(8):
            n=NOTES[r][c]
            out.append(dict(r=r,c=c,x=OFFS[r]+c*P,y=r*D,n=n,sharp='#' in n,dot=n[0] in 'CF' and '#' not in n))
    return out
FRONT=-18.5; BACK=4*D-D+RB+11  # ~66.6
RIGHT=137+12
CASE_LEFT={'P1':-90,'P2':-70}
INK='#1E2124'; ACC='#C2410C'; BLUE='#1F5FA8'
CREAM_TOP='#F1E9D6'; CREAM_L='#D8CBAE'; CREAM_F='#E4D9BF'
def rr_outline(x0,y0,x1,y1,r,rl=None,n=6):
    """rounded rect CCW (y up). rl = radius on left corners"""
    rl=r if rl is None else rl
    pts=[]
    def arc(cx,cy,rad,a0,a1):
        for i in range(n+1):
            a=math.radians(a0+(a1-a0)*i/n); pts.append((cx+rad*math.cos(a),cy+rad*math.sin(a)))
    arc(x1-r,y0+r,r,-90,0); arc(x1-r,y1-r,r,0,90); arc(x0+rl,y1-rl,rl,90,180); arc(x0+rl,y0+rl,rl,180,270)
    return pts
# iso: X=(x-y)*c30, Ydown=-(x+y)*0.5 - z  (viewer front-left)
C30=math.cos(math.radians(30))
def iso(x,y,z): return ((x-y)*C30, -(x+y)*0.5 - z)
def poly(pts,fill,stroke=INK,sw=0.35,extra=''):
    s=' '.join(f'{a:.2f},{b:.2f}' for a,b in pts)
    return f'<polygon points="{s}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" {extra}/>'
def hull(points):
    pts=sorted(set((round(a,3),round(b,3)) for a,b in points))
    if len(pts)<3: return pts
    def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];up=[]
    for p in pts:
        while len(lo)>=2 and cr(lo[-2],lo[-1],p)<=0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up)>=2 and cr(up[-2],up[-1],p)<=0: up.pop()
        up.append(p)
    return lo[:-1]+up[:-1]
def prism(outline, zbot, ztop_fn, top=CREAM_TOP, left=CREAM_L, front=CREAM_F, sw=0.35):
    """outline CCW in plan; ztop_fn(x,y)->z"""
    out=[]
    n=len(outline); faces=[]
    for i in range(n):
        a=outline[i]; b=outline[(i+1)%n]
        dx=b[0]-a[0]; dy=b[1]-a[1]
        nx,ny=dy,-dx
        vis=-nx-ny
        if vis>1e-6:
            q=[iso(a[0],a[1],zbot),iso(b[0],b[1],zbot),iso(b[0],b[1],ztop_fn(*b)),iso(a[0],a[1],ztop_fn(*a))]
            # shade: mostly-left normal -> left color else front
            col=left if abs(nx)>abs(ny) else front
            faces.append((-(a[0]+b[0]+a[1]+b[1]),q,col))
    faces.sort(key=lambda f:-f[0])
    for _,q,col in faces: out.append(poly(q,col,stroke=col,sw=0.15))
    # outer silhouette stroke later; top
    out.append(poly([iso(x,y,ztop_fn(x,y)) for x,y in outline],top,sw=sw))
    return out
def circle_pts(cx,cy,r,n=28):
    return [(cx+r*math.cos(2*math.pi*i/n),cy+r*math.sin(2*math.pi*i/n)) for i in range(n)]
def cylinder(cx,cy,r,z0,z1,top,side,sw=0.3,dome=False,stroke=INK):
    c=circle_pts(cx,cy,r)
    b=[iso(x,y,z0) for x,y in c]; t=[iso(x,y,z1) for x,y in c]
    s=[poly(hull(b+t),side,stroke=stroke,sw=sw), poly(t,top,stroke=stroke,sw=sw)]
    if dome:
        c2=circle_pts(cx-r*0.25,cy-r*0.25,r*0.45,18)
        s.append(poly([iso(x,y,z1) for x,y in c2],'#ffffff',stroke='none',sw=0,extra='opacity="0.35"'))
    return s
