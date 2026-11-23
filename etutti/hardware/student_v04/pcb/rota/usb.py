"""Par USB a mao (B.Cu, sem via, sobre a In2 = GND inteira) + as duas vias do corredor do USBLC6 (pino 5 VBUS, pino 2 GND).
(o VBUS do pino 5 e do roteador de potencia, etapa 2.) Funcoes idempotentes: refazer_usb(b) remove o que for USB (e os dois stubs/vias do corredor) e desenha de novo; serve para a etapa 1 e
para reaplicar depois de um ImportSpecctraSES (que apaga as trilhas fixas que o pcbnew exportou).
Topologia (explicada no ROTEAMENTO.md): D+ contorna o USBLC6 pelo NORTE, D- pelo SUL; A6/B6 ligados pelo oeste dos pads, A7/B7 por uma ponte
a leste; o corredor entre as fileiras do chip leva os pinos 4/3 (D-) e 6/1 (D+) por tracos verticais; um trombone no D- iguala os comprimentos."""
import math, os
import pcbnew
from lib import add_track, add_via, log

W = float(os.environ.get('USB_W', 0.24))
XA, XB = 9.995, 16.725                    # centros dos pads B6/A7 (USB-C) e 3/5 (J101)

def _len(pts): return sum(math.hypot(a[0]-c[0], a[1]-c[1]) for a, c in zip(pts[:-1], pts[1:]))
def _centro(pts): return _len(pts) - abs(pts[0][0]-XA) + (XB - pts[-1][0])

def caminhos(d=0.0):
    """U201 girado (R12V4): D+ nos pinos 6/1 (y 8,55), D- nos pinos 4/3 (y 10,45): o par passa reto pelo chip."""
    dp = {
     'oeste': [(9.6, 9.25), (8.9, 9.25), (8.9, 10.25), (9.6, 10.25)],        # A6-B6 pelo oeste da ponta do A7
     'reta':  [(9.6, 9.25), (11.0, 9.25), (11.7, 8.55), (15.35, 8.55), (15.75, 9.25), (16.6, 9.25)],
    }
    dn = {
     'ponte': [(9.6, 10.75), (11.2, 10.75), (11.2, 9.75)],                    # A7-B7 a leste da ponta do A6
     'reta':  [(9.6, 9.75), (11.0, 9.75), (11.7, 10.45), (15.35, 10.45), (15.75, 9.75), (16.6, 9.75)],
    }
    return dp, dn

def _na_janela(t):
    p = t.GetStart() if t.Type() == pcbnew.PCB_TRACE_T else t.GetPosition()
    return 12.5 < p.x/1e6 < 14.2 and 8.9 < p.y/1e6 < 10.2

def refazer_usb(b, grave):
    for t in list(b.GetTracks()):
        if t.GetNetname() in ('USB_DP', 'USB_DN') or (t.GetNetname() in ('VBUS', 'GND') and _na_janela(t)):
            b.Remove(t); grave.append(t)
    dp, dn = caminhos(0.0)
    for net, grupo in (('USB_DP', dp), ('USB_DN', dn)):
        for k, pts in grupo.items(): add_track(b, net, pts, W)
    # corredor do meio do chip: pino 5 (VBUS) e pino 2 (GND) saem por vias entre as colunas
    add_via(b, 'VBUS', 13.25, 9.2); add_track(b, 'VBUS', [(12.8, 9.5), (13.25, 9.2)], 0.3)
    add_via(b, 'GND', 13.7, 9.95); add_track(b, 'GND', [(14.0, 9.5), (13.7, 9.95)], 0.3)
    d = 0.0
    return dict(d_plus=round(_centro(dp['reta']), 3), d_minus=round(_centro(dn['reta']), 3), trombone=round(d, 3), largura=W)
