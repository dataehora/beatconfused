import os,subprocess,sys
sys.path.insert(0,'.')
import pcbnew, roteia as RT
n=8; novo=RT.paths(n)[1]
b=pcbnew.LoadBoard(novo)
pcbnew.ExportSpecctraDSN(b,'build/R8r.dsn')
t=open('build/R8r.dsn',encoding='utf-8').read().replace('(width 200)','(width 150)'); open('build/R8r.dsn','w',encoding='utf-8').write(t)
r=subprocess.run([r"C:/Users/julia/AppData/Local/freerouting/freerouting.exe",'-de','build/R8r.dsn','-do','build/R8r.ses','-mp','200'],capture_output=True,text=True)
open('build/fr_R8r.log','w').write(r.stdout+r.stderr)
b=pcbnew.LoadBoard(novo); print(pcbnew.ImportSpecctraSES(b,'build/R8r.ses'))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(novo,b)
RT.st_all={}; RT.drc(n,{},tag='_r')
