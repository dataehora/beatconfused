#!/bin/bash
# usage: krt_seq.sh TAG "net1 net2" "net3" ...   routes the groups one call each, chaining the boards
cd "$(dirname "$0")"
K=/c/Users/julia/OneDrive/Documentos/GitHub/KiCadRoutingTools
T=$1; shift
cp kicad/base/slim_regua.kicad_pcb build/krt/${T}_0.kicad_pcb
i=0
for g in "$@"; do
  p=$i; i=$((i+1))
  python $K/py_router/route.py build/krt/${T}_$p.kicad_pcb build/krt/${T}_$i.kicad_pcb --nets $g --layers F.Cu B.Cu --track-width ${TW:-0.2} --clearance ${CLR:-0.15} --via-size 0.6 --via-drill 0.3 --escalation off --no-fix-drc-settings ${EXTRA} > build/krt/${T}_$i.log 2>&1
  echo "$g: $(grep -E '^JSON_REGRADE' build/krt/${T}_$i.log | grep -o '"failed_single": \[[^]]*\]')"
done
