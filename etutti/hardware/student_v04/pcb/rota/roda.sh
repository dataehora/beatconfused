#!/bin/bash
# Pipeline completo da placa principal (R12V4): roda.sh [de_etapa]  (1..6); cada etapa e idempotente; log em build/log.txt.
# 1 USB a mao | 2 VBUS + indutor a mao, VBAT/VSYS (grade propria) | 3 fan-out dos planos | 4 Freerouting (resto) | 5 iteracao | 6 fecha
PY="/c/Program Files/KiCad/10.0/bin/python.exe"
cd "$(dirname "$0")"
K=../../kicad
DE=${1:-1}
if [ "$DE" -le 1 ]; then
  cp $K/student_v04.kicad_pcb $K/student_v04_roteada.kicad_pcb
  "$PY" -u etapa1_usb.py; cp $K/student_v04_roteada.kicad_pcb build/etapa1.kicad_pcb
fi
if [ "$DE" -le 2 ]; then
  "$PY" -u etapa2_potencia.py
  "$PY" -u etapa2b_potencia2.py
  "$PY" -u post.py build/etapa2b.kicad_pcb build/post_2b.kicad_pcb
  cp build/post_2b.kicad_pcb $K/student_v04_roteada.kicad_pcb
fi
if [ "$DE" -le 3 ]; then
  [ "$DE" -eq 3 ] && cp build/post_2b.kicad_pcb $K/student_v04_roteada.kicad_pcb
  "$PY" -u fanout.py && cp $K/student_v04_roteada.kicad_pcb build/etapa3.kicad_pcb
fi
if [ "$DE" -le 4 ]; then
  BASE=build/etapa3.kicad_pcb "$PY" -u etapa3_fr.py r1 40
fi
if [ "$DE" -le 5 ]; then
  rm -f build/melhor.*
  export BASE=build/fr_r1.kicad_pcb
  for i in 1 2; do "$PY" -u etapa5_itera.py 1 30; done
fi

