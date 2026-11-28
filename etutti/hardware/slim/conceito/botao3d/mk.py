import bpy, bmesh, math
from mathutils import Vector, Matrix
# ---------- profile (mm): head D15 x 3.8, shank D10 x 5.85, pin D5.4 x 3.0
R=7.5; HS=1.6; HT=3.8
def profile():
    pts=[]
    # pin bottom
    pts.append((0.0,-8.85)); pts.append((2.7,-8.85)); pts.append((2.7,-5.85))
    pts.append((5.0,-5.85)); pts.append((5.0,0.0)); pts.append((R,0.0)); pts.append((R,HS))
    # edge fillet: quarter ellipse to (6.2, 2.75)
    for i in range(1,10):
        t=i/9*math.pi/2
        pts.append((R-1.3+1.3*math.cos(t), HS+1.15*math.sin(t)))
    # dome cap from (6.2,2.75) to (0,3.8)
    r0,z0=R-1.3,HS+1.15
    # circle through (r0,z0) and (0,HT) centred on axis
    zc=(r0**2+z0**2-HT**2)/(2*(z0-HT)); Rs=HT-zc
    a0=math.atan2(z0-zc,r0)
    for i in range(1,25):
        a=a0+(math.pi/2-a0)*i/24
        pts.append((Rs*math.cos(a), zc+Rs*math.sin(a)))
    return pts
def revolve(name, pts, seg=128):
    me=bpy.data.meshes.new(name); bm=bmesh.new()
    rings=[]
    for (r,z) in pts:
        if r<1e-6: rings.append([bm.verts.new((0,0,z))]); continue
        rings.append([bm.verts.new((r*math.cos(2*math.pi*k/seg), r*math.sin(2*math.pi*k/seg), z)) for k in range(seg)])
    for a,b in zip(rings[:-1],rings[1:]):
        if len(a)==1:
            for k in range(seg): bm.faces.new((a[0],b[(k+1)%seg],b[k]))
        elif len(b)==1:
            for k in range(seg): bm.faces.new((a[k],a[(k+1)%seg],b[0]))
        else:
            for k in range(seg): bm.faces.new((a[k],a[(k+1)%seg],b[(k+1)%seg],b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth=True
    return ob
def dome_z(r):
    pts=profile()
    best=None
    for (pr,pz) in pts:
        if pz>=HS and abs(pr-r)<0.35: best=pz if best is None else max(best,pz)
    return best if best is not None else HT
def texture(ob):
    # diagonal grid of square recesses 0.5 mm, pitch 1.1, depth 0.18, inside D11
    bm=bmesh.new()
    pitch=1.1; s=0.5; n=8
    for i in range(-n,n+1):
        for j in range(-n,n+1):
            x=(i-j)*pitch/math.sqrt(2); y=(i+j)*pitch/math.sqrt(2)
            r=math.hypot(x,y)
            if r>5.5: continue
            z=dome_z(r)
            m=Matrix.Translation((x,y,z))@Matrix.Rotation(math.radians(45),4,'Z')
            ret=bmesh.ops.create_cube(bm,size=1.0)
            for v in ret['verts']:
                v.co=Vector((v.co.x*s, v.co.y*s, v.co.z*0.8))
                v.co=m@v.co
    me=bpy.data.meshes.new('dots'); bm.to_mesh(me); bm.free()
    cut=bpy.data.objects.new('dots',me); bpy.context.collection.objects.link(cut)
    # lower cutter so depth = 0.18 below surface
    cut.location.z=0.4-0.18
    mod=ob.modifiers.new('tex','BOOLEAN'); mod.operation='DIFFERENCE'; mod.object=cut; mod.solver='EXACT'
    bpy.context.view_layer.objects.active=ob; bpy.ops.object.modifier_apply(modifier='tex')
    bpy.data.objects.remove(cut)
bpy.ops.wm.read_factory_settings(use_empty=True)
pts=profile()
def mat(name,col,rough,coat=0.0):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*col,1); b.inputs['Roughness'].default_value=rough
    try: b.inputs['Coat Weight'].default_value=coat; b.inputs['Coat Roughness'].default_value=0.05
    except: pass
    try: b.inputs['Subsurface Weight'].default_value=0.15 if col[0]>0.5 else 0
    except: pass
    return m
white=mat('branco',(0.86,0.85,0.80),0.25,0.8); black=mat('preto',(0.015,0.015,0.017),0.22,0.9)
specs=[('branco_liso',white,False,-20),('preto_liso',black,False,0),('branco_CF',white,True,20)]
obs=[]
for name,m,tex,x in specs:
    ob=revolve(name,pts)
    if tex: texture(ob)
    ob.data.materials.append(m); ob.location=(x,0,0); obs.append(ob)
# export STL of the textured and plain
import os
for ob in obs:
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
    loc=ob.location.copy(); ob.location=(0,0,0)
    bpy.ops.wm.stl_export(filepath=f'/home/claude/slim/botao3d/{ob.name}.stl', export_selected_objects=True)
    ob.location=loc
# floor + lighting + camera
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-0.5)); fl=bpy.context.object
fm=mat('fundo',(0.32,0.33,0.34),0.9); fl.data.materials.append(fm)
# hide shanks below floor: move buttons so head underside sits on floor
for ob in obs: ob.location.z=0.0
fl.location.z=-0.01
w=bpy.data.worlds.new('w'); bpy.context.scene.world=w; w.use_nodes=True
w.node_tree.nodes['Background'].inputs[0].default_value=(0.9,0.9,0.92,1); w.node_tree.nodes['Background'].inputs[1].default_value=0.6
for loc,en,sz in [((-40,-40,60),40000,30),((50,-20,40),15000,20),((0,60,50),8000,40)]:
    l=bpy.data.lights.new('L','AREA'); l.energy=en; l.size=sz
    lo=bpy.data.objects.new('L',l); bpy.context.collection.objects.link(lo); lo.location=loc
    d=Vector((0,0,0))-Vector(loc); lo.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
cam=bpy.data.cameras.new('c'); cam.lens=85; co=bpy.data.objects.new('c',cam); bpy.context.collection.objects.link(co)
co.location=(0,-95,70); d=Vector((0,0,1))-co.location; co.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
sc=bpy.context.scene; sc.camera=co; sc.render.engine='CYCLES'; sc.cycles.samples=96; sc.cycles.device='CPU'
sc.render.resolution_x=1600; sc.render.resolution_y=800
sc.view_settings.view_transform='Standard'
sc.render.filepath='/home/claude/slim/botao3d/botoes_render.png'
bpy.ops.render.render(write_still=True)
# close-up of the textured one, top view at angle
co.location=(20,-38,40); d=Vector((20,0,1.5))-co.location; co.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
sc.render.resolution_x=1000; sc.render.resolution_y=800; sc.render.filepath='/home/claude/slim/botao3d/botao_CF_close.png'
bpy.ops.render.render(write_still=True)
print('ok')
