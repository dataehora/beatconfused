# eTutti Student V4 — base de trabalho

SPEC: `SPEC.md` (R1V4 + R2V4, do Chat; o Code nunca a edita). Relatórios do Code (português, citam "R2V4"):
`FIT_CHECK.md` (design), `ELETRONICA.md` (eletrônica), `FIRMWARE.md` (programação e som).

Esta pasta nasceu da `student_v03/` (R1V4, tarefa 1): só **scripts e fontes** (esquema, geometria, pcb, case, estudos,
fornecimento), sem `fab/`, renders, STEP/STL nem saídas geradas. A V3, a V2 e a V1 **não são alteradas**.
Fase B (R3V4): `pcb/schematic.py` (esquema V4, ERC), `pcb/posiciona_v4.py` (placa principal sem trilhas), `pcb/vistas_v4.py` (imagens), `bom_v4.py`; arquivos KiCad `kicad/student_v04.*`. Os demais scripts herdados da V3 (`build_sem_rota.py`, `pcb/build_board_v3.py`, `refaz_usb.py`...) não valem para a V4.
Páginas, Blender e passos de manual da V3 não foram copiados (página e manual ficam para depois, decisão 19).

## Ordem de execução (herdada da V3; ajustar à medida que a V4 diverge)

1. `python geometria.py` (stdlib).
2. `python pcb/schematic.py` (esquema + ERC + netlist), `pcb/export_furos.py` e `pcb/export_fp.py` (KiCad python).
3. Placa: `build_sem_rota.py` -> `pcb/build_board_v3.py` -> `pcb/troca_jack.py` -> `pcb/refaz_usb.py` -> `pcb/costura_usb.py` (KiCad python).
   Na V4 o posicionamento (Fase B) e o roteamento (Fase C, agente `roteamento`) são etapas separadas.
4. `fab.py`, `bom_v3.py`, `auditoria_pinos.py`.
5. Case (venv CadQuery): `case/case.py`, `case/fit_check.py`, `case/fit_extra.py`, `case/render.py`, `estudos/acustica.py`;
   `estudos/flexao.py` (KiCad python).

KiCad python: `C:/Program Files/KiCad/10.0/bin/python.exe`. CadQuery: `C:/Users/julia/.venvs/cadquery/Scripts/python.exe`.

## Réguas (R11V4)
Dois desenhos (R8 de 8 posições, R4 de 4), quatro variantes por BOM (R8, R8E, R4, R4E: "E" = com o OUT). Ordem, com `REGUA_N=8` ou `4`:
`python pcb/regua/schematic_regua.py` -> KiCad python `pcb/regua/posiciona_regua.py` -> KiCad python `pcb/regua/pacotes_regua.py` (BOM e CPL em `fab/regua/`) ->
KiCad python `MODO=regua PAINEL_N=2|4|5 pcb/regua/fab_regua.py` (painéis) -> venv CadQuery `pcb/regua/vistas_regua.py`; custo: `pcb/regua/custo_r11.py`.
Entrega ao roteamento: `pcb/regua/ROTEAMENTO_ENTREGA.md`; folha de cotação: `fab/regua/LEIAME_COTACAO.md`. Nunca rodar `posiciona_regua.py` sobre uma placa roteada (use `REGUA_BOARD`).
