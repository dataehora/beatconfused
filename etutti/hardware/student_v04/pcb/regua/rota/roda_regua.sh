#!/bin/bash
# Pipeline completo de uma regua: Freerouting + pos-processamento. Uso: roda_regua.sh 8|4
PY="/c/Program Files/KiCad/10.0/bin/python.exe"
cd "$(dirname "$0")"
N=$1
if [ "$N" = "8" ]; then export FRW=150; else export FRW=200; fi
export ESCNETS=OUT,GND
"$PY" -u fr_run.py $N 200 2>&1 | grep -v "dupl\|leak\|stackup"
"$PY" -u post.py $N 2>&1 | grep -v "dupl\|leak\|stackup"
