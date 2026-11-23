"""Roda o pipeline varias vezes (o Freerouting nao e deterministico entre execucoes) e guarda a melhor placa.
Uso (python comum): python melhor.py N tentativas"""
import json, os, shutil, subprocess, sys, time
HERE=os.path.dirname(os.path.abspath(__file__))
n=int(sys.argv[1]); tries=int(sys.argv[2])
KD=os.path.abspath(os.path.join(HERE,'..','..','..','kicad','regua'))
name={8:'student_v04_regua8_roteada',4:'student_v04_regua_roteada'}[n]
best=None
for k in range(tries):
    subprocess.run(['bash',os.path.join(HERE,'roda_regua.sh'),str(n)],capture_output=True)
    d=json.load(open(os.path.join(HERE,'drc_R%d.json'%n),encoding='utf-8'))
    score=len(d.get('violations',[]))+len(d.get('unconnected_items',[]))+len(d.get('schematic_parity',[]))
    err=sum(1 for v in d.get('violations',[])+d.get('unconnected_items',[]) if v.get('severity')=='error')
    print(time.strftime('%H:%M:%S'),'tentativa',k+1,'itens',score,'erros',err,flush=True)
    if best is None or score<best:
        best=score; shutil.copy(os.path.join(KD,name+'.kicad_pcb'),os.path.join(HERE,'melhor_R%d.kicad_pcb'%n))
        if score==0: break
if best is not None:
    shutil.copy(os.path.join(HERE,'melhor_R%d.kicad_pcb'%n),os.path.join(KD,name+'.kicad_pcb'))
print('melhor',best)
