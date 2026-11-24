import os,time
exec(open('/home/claude/slim/blender/model2.py').read())
sc.render.resolution_percentage=int(os.environ.get('RES','100'))
OUT='/home/claude/slim/renders/'
for btn in (True,False):
    show('caps',btn); show('capdots',btn); show('labels_cap',btn); show('labels_sw',not btn)
    aim((CENTER.x-300,CENTER.y-300,CENTER.z+250),CENTER,300)
    t=time.time(); render(OUT+f'v7_iso_esq_{"com" if btn else "sem"}.png'); print('v7',btn,round(time.time()-t,1),flush=True)
