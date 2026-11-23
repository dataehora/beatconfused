#!/bin/bash
# 4a execucao completa: roda.sh 1 e depois fecha + final
bash roda.sh 1
PY="/c/Program Files/KiCad/10.0/bin/python.exe"
"$PY" -u etapa6_fecha.py; "$PY" -u etapa6_fecha.py; "$PY" -u etapa7_final.py
