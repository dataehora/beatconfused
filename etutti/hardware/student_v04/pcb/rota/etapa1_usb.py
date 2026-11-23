"""Etapa 1: par USB a mao (usb.py). Idempotente. Salva a placa roteada e roda o DRC."""
from lib import *
import pcbnew, usb
b = pcbnew.LoadBoard(BOARD); GRAVE = []
info = usb.refazer_usb(b, GRAVE)
fill(b); pcbnew.SaveBoard(BOARD, b)
log("USB %s" % info)
r, d = drc(); log(str(r)); marca('1_usb', status='feito', usb=info, drc=r)
