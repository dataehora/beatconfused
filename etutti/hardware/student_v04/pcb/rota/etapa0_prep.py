"""Etapa 0: copia a placa posicionada para kicad/student_v04_roteada.* (idempotente: so refaz se --force ou nao existir).
Planos: In1 (+3V3) e In2 (GND) passam a camadas de potencia (LT_POWER) para o Freerouting."""
import shutil, sys, os
from lib import *
import pcbnew
force = '--force' in sys.argv
if os.path.exists(BOARD) and not force:
    log("ja existe %s (use --force para refazer)" % BOARD); sys.exit(0)
for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru', '.kicad_sch', '.kicad_prl'):
    s = os.path.join(KICAD, 'student_v04' + ext)
    d = os.path.join(KICAD, 'student_v04_roteada' + ext)
    if os.path.exists(s): shutil.copy(s, d)
b = pcbnew.LoadBoard(BOARD)
n = len(b.GetTracks())
log("trilhas ja na copia: %d" % n)
pcbnew.SaveBoard(BOARD, b)
r, _ = drc(); log(str(r))
marca('0_prep', status='feito', drc=r)
