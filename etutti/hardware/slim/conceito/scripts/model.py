import bpy, bmesh, math, sys
from mathutils import Vector
sys.path.insert(0,'/home/claude/slim/gen')
from geo import rr_outline, keys, P, D, OFFS
KEYS=keys()
FRONT=-18.5; BACK=70.6; LEFT=-90; RIGHT=149
ROWZ=[10.6,12.6,14.6,17.6]           # switch-top heights = bayan steps 2/2/3 (inputs)
SL=2.0/D; OFS=1.4                     # lid sits 1.4 above switch tops at hole centres
Y0S=35.0; WS=4.0; YC=50.0; LC=12.0
def ss(t):
    t=max(0,min(1,t)); return t*t*t*(t*(6*t-15)+10)
def H(y):
    z=ROWZ[0]+SL*y+1.0*ss((y-Y0S)/WS)
    if y>YC:
        u=min(y-YC,LC); z-=SL*u*u/(2*LC)+(SL*(y-YC-LC) if y>YC+LC else 0)
    return z
def S(y):
    z=H(y)+OFS
    rf,df=4,1.2
    if y<FRONT+rf:
        t=(FRONT+rf-y)/rf; z-=df*(1-math.sqrt(max(0,1-t*t)))
    rb,db=6,2.0
    if y>BACK-rb:
        t=(y-(BACK-rb))/rb; z-=db*(1-math.sqrt(max(0,1-t*t)))
    return z
HOUS=3.0; GRADE=1.2; GAP=2.2; PCB=1.2; CB=17.0; HOLE=16.0
def stack(r):
    zt=ROWZ[r]; gt=zt-HOUS; gb=gt-GRADE; pt=gb-GAP; pb=pt-PCB
    return zt,gt,gb,pt,pb
REG=(-46.0,0.0); VOL=(-46.0,3*D)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
def mat(name,col,rough=0.45,metal=0.0,emit=None):
    m=bpy.data.materials.new(name); m.use_nodes=True
    b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*col,1); b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal
    if emit:
        b.inputs['Emission Color'].default_value=(*emit,1); b.inputs['Emission Strength'].default_value=6.0
    return m
def srgb(h):
    h=h.lstrip('#'); c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(((x+0.055)/1.055)**2.4 if x>0.04045 else x/12.92 for x in c)
M={'case':mat('case',srgb('EFE6D2'),0.55),'base':mat('base',srgb('8F8A80'),0.6),'pcb':mat('pcb',srgb('2F6B3A'),0.4),
   'grade':mat('grade',srgb('3F3F46'),0.5),'sw':mat('sw',srgb('B6BCC6'),0.35),'swl':mat('swl',srgb('9CA3AF'),0.35),
   'white':mat('white',srgb('FBF9F3'),0.3),'black':mat('black',srgb('222428'),0.3),'stem':mat('stem',srgb('6B7280'),0.4),
   'knob':mat('knob',srgb('2B2D31'),0.35),'chrome':mat('chrome',srgb('C9CCD1'),0.2,0.9),'led':mat('led',srgb('BFF5CF'),0.3,0,srgb('22C55E')),
   'bat':mat('bat',srgb('C9D6E8'),0.5),'conn':mat('conn',srgb('1E2124'),0.4),'dot':mat('dot',srgb('8A8578'),0.5),
   'txtd':mat('txtd',srgb('1E2124'),0.5),'txtl':mat('txtl',srgb('F4F1EA'),0.5)}
def obj_from_bm(bm,name,m):
    me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); sc.collection.objects.link(o); o.data.materials.append(m); return o
def prism(poly,z0,z1,name,m):
    bm=bmesh.new()
    vb=[bm.verts.new((x,y,z0)) for x,y in poly]; vt=[bm.verts.new((x,y,z1)) for x,y in poly]
    n=len(poly)
    bm.faces.new(vb[::-1]); bm.faces.new(vt)
    for i in range(n):
        j=(i+1)%n; bm.faces.new([vb[i],vb[j],vt[j],vt[i]])
    return obj_from_bm(bm,name,m)
def box(x0,x1,y0,y1,z0,z1,name,m): return prism([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z0,z1,name,m)
def cyl(cx,cy,r,z0,z1,name,m,seg=48):
    return prism([(cx+r*math.cos(2*math.pi*i/seg),cy+r*math.sin(2*math.pi*i/seg)) for i in range(seg)],z0,z1,name,m)
def profile_solid(fn,x0,x1,name,zbot=-1.0,step=0.4):
    ys=[FRONT-2+i*step for i in range(int((BACK-FRONT+4)/step)+1)]
    poly=[(y,fn(min(max(y,FRONT),BACK))) for y in ys]
    bm=bmesh.new()
    def ring(x): return [bm.verts.new((x,y,z)) for y,z in poly]+[bm.verts.new((x,ys[-1],zbot)),bm.verts.new((x,ys[0],zbot))]
    a=ring(x0); b=ring(x1); n=len(a)
    bm.faces.new(a[::-1]); bm.faces.new(b)
    for i in range(n):
        j=(i+1)%n; bm.faces.new([a[i],a[j],b[j],b[i]])
    return obj_from_bm(bm,name,M['case'])
def boolean(o,cutter,op='DIFFERENCE'):
    md=o.modifiers.new('b','BOOLEAN'); md.operation=op; md.object=cutter; md.solver='EXACT'; md.use_self=True; md.use_hole_tolerant=True
    bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
def join(objs,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join(); objs[0].name=name; return objs[0]
# ---------------- case top shell
outer=prism(rr_outline(LEFT,FRONT,RIGHT,BACK,6),0.0,40.0,'case',M['case'])
boolean(outer,profile_solid(S,LEFT-5,RIGHT+5,'topcut'),'INTERSECT')
inner=prism(rr_outline(LEFT+1.6,FRONT+1.6,RIGHT-1.6,BACK-1.6,4.4),-1.0,40.0,'inner',M['case'])
boolean(inner,profile_solid(lambda y:S(y)-1.6,LEFT-5,RIGHT+5,'innercut'),'INTERSECT')
# collars (keep material around holes down to grade+0.3) and knob bosses
coll=[]
for k in KEYS:
    zt,gt,*_=stack(k['r']); coll.append(cyl(k['x'],k['y'],CB/2+1.6,gt+0.3,40,'c',M['case']))
coll+= [cyl(REG[0],REG[1],11,6.0,40,'kb',M['case']),cyl(VOL[0],VOL[1],11,6.0,40,'kb',M['case'])]
cj=join(coll,'collars')
boolean(inner,cj,'DIFFERENCE')
boolean(outer,inner,'DIFFERENCE')
# holes + counterbores + knob pockets + connector openings
holes=[];cbs=[];misc=[]
for k in KEYS:
    zt,gt,*_=stack(k['r'])
    holes.append(cyl(k['x'],k['y'],HOLE/2,-1,40,'h',M['case']))
    cbs.append(cyl(k['x'],k['y'],CB/2,zt,40,'cb',M['case']))
for (cx,cy) in (REG,VOL):
    cbs.append(cyl(cx,cy,8.8,S(cy)-1.2,40,'kp',M['case']))
    holes.append(cyl(cx,cy,3.5,-1,40,'ks',M['case']))
misc.append(box(-76.5,-67.5,BACK-3,BACK+3,3.2,6.4,'usb',M['case']))
bpy.ops.mesh.primitive_cylinder_add(radius=2.9,depth=8,location=(LEFT,63,4.8),rotation=(0,math.pi/2,0)); misc.append(bpy.context.active_object)
boolean(outer,join(holes,'holes'),'DIFFERENCE')
boolean(outer,join(cbs,'cbs'),'DIFFERENCE')
boolean(outer,join(misc,'misc'),'DIFFERENCE')
CASE=outer
# ---------------- internals
parts={'base':[],'pcb':[],'grade':[],'swl':[],'sw':[],'stem':[],'caps':[],'capdots':[],'misc':[],'labels_cap':[],'labels_sw':[]}
parts['base'].append(prism(rr_outline(LEFT+1.6,FRONT+1.6,RIGHT-1.6,BACK-1.6,4.4),0,1.6,'floor',M['base']))
for r in range(4):
    zt,gt,gb,pt,pb=stack(r); off=OFFS[r]; y=r*D
    parts['base'].append(box(off-21.5,off+138.5,y-7.6,y+7.6,1.6,pb,'step',M['base']))
    parts['pcb'].append(box(off-21.5,off+138.5,y-7.5,y+7.5,pb,pt,'ruler',M['pcb']))
    parts['grade'].append(box(off-9.6,off+138.5,y-7.8,y+7.8,gb,gt,'grade',M['grade']))
for k in KEYS:
    zt,gt,gb,pt,pb=stack(k['r']); x,y=k['x'],k['y']
    parts['swl'].append(box(x-6.9,x+6.9,y-6.9,y+6.9,pt,gb,'swl',M['swl']))
    parts['sw'].append(box(x-7,x+7,y-7,y+7,gt,zt-0.05,'swh',M['sw']))
    parts['stem'].append(box(x-1.5,x+1.5,y-1.5,y+1.5,zt,zt+1.6,'stem',M['stem']))
    # cap: skirt + dome via spin
    bm=bmesh.new(); prof=[(0.0,0.0),(7.5,0.0),(7.5,1.6)]+[(7.5*math.cos(a),1.6+2.4*math.sin(a)) for a in [i*math.pi/2/10 for i in range(1,11)]]
    vs=[bm.verts.new((px,0,pz)) for px,pz in prof]
    for i in range(len(vs)-1): bm.edges.new((vs[i],vs[i+1]))
    bmesh.ops.spin(bm,geom=bm.verts[:]+bm.edges[:],cent=(0,0,0),axis=(0,0,1),angle=2*math.pi,steps=48)
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=0.001)
    c=obj_from_bm(bm,'cap',M['black'] if k['sharp'] else M['white']); c.location=(x,y,zt+1.0)
    bpy.context.view_layer.objects.active=c
    md=c.modifiers.new('s','SUBSURF'); md.levels=1
    parts['caps'].append(c)
    if k['dot']:
        for dx in (-2.6,0,2.6):
            for dy in (-2.6,0,2.6):
                if (dx,dy)!=(0,0) and abs(dx)+abs(dy)<5:
                    rr=math.hypot(dx,dy); zz=zt+1+1.6+2.4*math.sqrt(max(0,1-(rr/7.5)**2))
                    parts['capdots'].append(cyl(x+dx,y+dy,0.45,zz-0.3,zz+0.12,'dot',M['dot'],12))
    for setname,z,mt in (('labels_cap',zt+1+4.02+0.05,M['txtl'] if k['sharp'] else M['txtd']),('labels_sw',zt+0.03,M['txtd'])):
        bpy.ops.object.text_add(location=(x,y-1.2 if setname=='labels_cap' else y,z))
        t=bpy.context.active_object; t.data.body=k['n']; t.data.size=3.0 if setname=='labels_cap' else 3.4; t.data.align_x='CENTER'; t.data.align_y='CENTER'
        t.data.font=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf') if 'djv' not in bpy.data.fonts else bpy.data.fonts['djv']
        t.data.font.name='djv'; t.data.materials.append(mt); t.data.extrude=0.02
        parts[setname].append(t)
# interface
parts['misc'].append(prism([(-58,-16.5),(-34,-16.5),(-34,69),(-89,69),(-89,55),(-58,55)],4.0,5.2,'mainboard',M['pcb']))
parts['misc'].append(box(-88,-60,-14.5,54,2.1,6.6,'battery',M['bat']))
parts['misc'].append(box(-76.5,-67.5,61,BACK-0.2,3.2,6.4,'usbc',M['conn']))
bpy.ops.mesh.primitive_cylinder_add(radius=3.0,depth=12,location=(LEFT+6,63,4.8),rotation=(0,math.pi/2,0)); jo=bpy.context.active_object; jo.data.materials.append(M['conn']); parts['misc'].append(jo)
for (cx,cy),led in ((REG,False),(VOL,True)):
    z0=S(cy)-1.2
    parts['misc'].append(cyl(cx,cy,7.4,z0,z0+0.9,'ring',M['led'] if led else M['chrome']))
    parts['misc'].append(cyl(cx,cy,6.2,z0+0.9,z0+3.8,'knob',M['knob']))
    pt=box(-0.5,0.5,-5.5,-1.5,0,0.06,'ptr',M['txtl']); pt.location=(cx,cy,z0+3.8); pt.rotation_euler=(0,0,math.radians(45 if not led else -45)); parts['misc'].append(pt)
# ---------------- world / render
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(*srgb('F4F1EA'),1); w.node_tree.nodes['Background'].inputs[1].default_value=0.9
sun=bpy.data.lights.new('sun','SUN'); sun.energy=2.6; sun.angle=math.radians(8); so=bpy.data.objects.new('sun',sun); sc.collection.objects.link(so); so.rotation_euler=(math.radians(45),math.radians(-10),math.radians(-35))
fill=bpy.data.lights.new('fill','AREA'); fill.energy=2.5e6; fill.size=400; fo=bpy.data.objects.new('fill',fill); sc.collection.objects.link(fo); fo.location=(150,-250,300); fo.rotation_euler=(math.radians(40),0,math.radians(30))
sc.render.engine='CYCLES'; sc.cycles.samples=40; sc.cycles.use_denoising=True
try: sc.cycles.denoiser='OPENIMAGEDENOISE'
except: pass
sc.render.resolution_x=1600; sc.render.resolution_y=1000; sc.view_settings.view_transform='Standard'
sc.render.film_transparent=False
sc.view_settings.view_transform='AgX'; sc.view_settings.exposure=-0.6
CENTER=Vector(((LEFT+RIGHT)/2,(FRONT+BACK)/2,8))
cam=bpy.data.cameras.new('cam'); cam.type='ORTHO'; co=bpy.data.objects.new('cam',cam); sc.collection.objects.link(co); sc.camera=co
def aim(loc,target,scale):
    co.location=loc; d=(Vector(target)-Vector(loc)); co.rotation_euler=d.to_track_quat('-Z','Y').to_euler(); cam.ortho_scale=scale
def show(name,vis):
    for o in parts[name]: o.hide_render=not vis
def render(path):
    sc.render.filepath=path; bpy.ops.render.render(write_still=True)
