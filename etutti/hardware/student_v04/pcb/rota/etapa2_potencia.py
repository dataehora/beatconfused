"""Etapa 2: redes de corrente a mao (roteador de grade proprio wide.py): VBUS, e os dois fios do indutor (BB_L1, BB_L2).
Idempotente: parte de build/etapa1.kicad_pcb (so o par USB) e refaz tudo. VSYS e VBAT ficam para o Freerouting (estagio de potencia, etapa 3 com NETS=...).
Trechos finos (0,25) nas pontas dos pinos de 0,5 mm de passo (patio do J101/U202 isenta a regra de 0,8), 0,8 no resto."""
import shutil
from lib import *
import pcbnew, wide
shutil.copy(os.path.join(BUILD, 'etapa1.kicad_pcb'), BOARD)
b = pcbnew.LoadBoard(BOARD)
res = {}
res['VBUS_u202'] = wide.route_net(b, 'VBUS', 0.25, ['U202.13', 'C201.1'], log)
res['VBUS_j101'] = wide.route_net(b, 'VBUS', 0.2, ['J101.9', 'V@17.95,10.75'], log)
res['VBUS_tronco'] = wide.route_net(b, 'VBUS', 0.8, ['J201.A9', 'J201.A4', 'V@13.25,9.2', 'V@17.95,10.75', 'D201.1', 'R214.1', 'R205.1', 'R206.1', 'C201.1'], log,
                                bloqueia=[(19.0, 5.3, 52.0, 100.0)])   # o tronco passa pela faixa de cima (y < 5,3): o miolo fica para os sinais
# indutor: dois fios curtos (um trecho fino dentro do patio do U204 + um largo ate o pad do L201)
add_track(b, 'BB_L1', [(70.88, 9.5), (71.9, 9.5)], 0.35); add_track(b, 'BB_L1', [(71.9, 9.5), (72.5, 10.3)], 0.8)
add_track(b, 'BB_L2', [(70.88, 8.5), (71.9, 8.5)], 0.35); add_track(b, 'BB_L2', [(71.9, 8.5), (72.5, 7.7)], 0.8)
fill(b); pcbnew.SaveBoard(BOARD, b)
r, d = drc(); log("potencia: %s %s" % (res, r))
shutil.copy(BOARD, os.path.join(BUILD, 'etapa2.kicad_pcb'))
marca('2_potencia', status='feito', res={k: [v[0], round(v[1], 1)] for k, v in res.items()}, drc=r)
