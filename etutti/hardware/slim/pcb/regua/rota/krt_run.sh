#!/bin/bash
# usage: krt_run.sh OUT_NAME [extra args]  -- KiCadRoutingTools route.py, strict sizes, on a copy of the placed ruler
cd "$(dirname "$0")"
K=/c/Users/julia/OneDrive/Documentos/GitHub/KiCadRoutingTools
N=$1; shift
python $K/py_router/route.py kicad/base/slim_regua.kicad_pcb build/krt/$N.kicad_pcb --nets '+3V3' OUT CLK DATA LATCH 'EN*' --layers F.Cu B.Cu --track-width ${TW:-0.2} --clearance ${CLR:-0.15} --via-size 0.6 --via-drill 0.3 --escalation off --no-fix-drc-settings ${KA} "$@" > build/krt/$N.log 2>&1
