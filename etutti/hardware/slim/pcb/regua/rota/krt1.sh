#!/bin/bash
# krt1.sh IN OUT "nets" [extra]   one route.py call with the ruler's strict settings
K=/c/Users/julia/OneDrive/Documentos/GitHub/KiCadRoutingTools
IN=$1; OUT=$2; G=$3; shift 3
timeout 300 python $K/py_router/route.py $IN $OUT --nets $G --layers F.Cu B.Cu --track-width 0.2 --clearance 0.15 --via-size 0.6 --via-drill 0.3 --escalation off --no-fix-drc-settings --board-edge-clearance 0.45 --keep-input-copper --layer-costs 1.5 1.0 --keep-away OUT:CLK,LATCH,DATA:1.0 --keep-away-cost 5 "$@" > ${OUT%.kicad_pcb}.log 2>&1
echo "$G: $(grep -E '^JSON_REGRADE' ${OUT%.kicad_pcb}.log | grep -o '"failed_single": \[[^]]*\]')"
