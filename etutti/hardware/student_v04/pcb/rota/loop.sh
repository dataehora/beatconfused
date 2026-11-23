#!/bin/bash
# etapas 5 e 6 repetidas, uma rodada por processo (evita o SwigPyObject de varias placas num so processo)
PY="/c/Program Files/KiCad/10.0/bin/python.exe"; cd "$(dirname "$0")"
for i in $(seq 1 ${1:-4}); do "$PY" -u etapa5_itera.py 1 30; done
"$PY" -u etapa6_fecha.py
