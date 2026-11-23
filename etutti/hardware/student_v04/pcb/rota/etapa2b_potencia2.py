"""Etapa 2b: VBAT e VSYS pelo roteador de grade proprio, com largura por zona: 0,25 junto aos pinos finos de U202/U204/U501/J202/J101 (patios isentos),
0,5 na area vsys_estreito (R12V4), 0,8 no resto. Parte de build/etapa2.kicad_pcb e grava build/etapa2b.kicad_pcb (e a roteada)."""
import shutil
from lib import *
import pcbnew, wide
shutil.copy(os.path.join(BUILD, 'etapa2.kicad_pcb'), BOARD)
b = pcbnew.LoadBoard(BOARD)
Z = [(('U202', 'U204', 'U501', 'J202'), 0.25, 0.8), ('rect', 0.5, (63.0, 6.5, 72.5, 15.5))]
ZB = [(('U202', 'J202'), 0.25, 0.8)]
res = {}
res['BB_VINA'] = wide.route_net(b, 'BB_VINA', 0.2, ['U204.8', 'C209.1', 'R216.2'], log)   # antes do VSYS: senao o VSYS corta o caminho
res['VBAT'] = wide.route_net(b, 'VBAT', 0.8, ['U202.2', 'U202.3', 'C203.1', 'R208.1', 'J202.1'], log, zonas=ZB)
res['VSYS'] = wide.route_net(b, 'VSYS', 0.8, ['U202.10', 'U202.11', 'C202.1', 'R216.1', 'C210.1', 'Q203.2', 'R210.1', 'C206.1', 'U204.5', 'U501.7', 'U501.8', 'C501.1', 'C502.1'], log, zonas=Z)
fill(b); pcbnew.SaveBoard(BOARD, b)
r, d = drc(); log("potencia2: %s %s" % (res, r))
shutil.copy(BOARD, os.path.join(BUILD, 'etapa2b.kicad_pcb'))
marca('2b_potencia2', status='feito', res={k: [v[0], round(v[1], 1)] for k, v in res.items()}, drc=r)
