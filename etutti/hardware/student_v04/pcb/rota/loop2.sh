#!/bin/bash
PY="/c/Program Files/KiCad/10.0/bin/python.exe"; cd "$(dirname "$0")"
cp build/fecha.kicad_pcb build/melhor.kicad_pcb; cp build/fecha.kicad_pro build/melhor.kicad_pro 2>/dev/null
"$PY" -u etapa5_itera.py 1 30
"$PY" -u etapa6_fecha.py
"$PY" -u etapa6_fecha.py
