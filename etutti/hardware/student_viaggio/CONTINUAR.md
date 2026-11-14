# StudentViaggio v0.2 · notas para continuar o trabalho

Tarefa do J (14 nov 2026): refazer a StudentViaggio com o layout da `studentBK` (compacta, ponta à direita, passo 19,05 × 18), mantendo a eletrônica da Viaggio J1, teclas resistivas com Velostat (velocidade + aftertouch), bloco esquerdo o menor possível, cuidado com áudio, calor e flexão. Trabalhar em etapas salvas (commit + push a cada uma).

Ramo: `student-viaggio-v02`. Ao terminar: PR, merge no `main` (regra do J: sem pedir).

## Decisões já tomadas

- **Eletrônica e bloco esquerdo:** os da J1, nas coordenadas da J1, com o roteamento dela (x ≤ 78 mm, e a faixa de cima com os dois mux em x 118 e 182). Não se reposiciona nada ali: é o que já foi validado (USB, carga, conversor, codec).
- **Teclado:** grade da `studentBK` (19,05 × 18; fileiras de 6/7/8/7), começando em x = 68,5 (fileira de 8), fileiras em y = 28, 46, 64, 82. Placa 210 × 95 mm (a J1 tem 246,5 × 95).
- **Contorno:** cantos esquerdos da J1, ponta à direita. Tudo em `pcb/layout.py` → `pcb/layout.json`.
- **Furos M2:** H1–H4 onde a J1 os tem; H5–H8 movidos para a grade nova; H9–H11 novos.
- **Pente novo, simétrico** (`FSR_Comb_D12`): dedo de sinal no centro, via de sinal num ressalto do arco direito, fora do centro. Sem o bloco de sinal da v0.1.
- **Peças da `studentBK` não entram:** os footprints e a lista de ligações dela estavam errados (auditoria no início desta sessão). Dela ficam a forma, o passo e a ideia dos apoios.

## Etapas

- [x] 1. Levantamento do que a J1 ocupa.
- [x] 2. `pcb/layout.py` + `layout.json` + `img/layout.svg`.
- [x] 3. Pente simétrico em `pcb/footprints.py`; `schematic.py` continua valendo (mesmas ligações).
- [ ] 4. (script escrito; primeira rodada leva mais de 10 min, rodar em segundo plano) `pcb/build_board.py` v0.2: contorno novo, furos, teclas nas posições novas, apagar todas as rotas `OUT_Kxx` da J1 e roteá-las de novo com o roteador da J1; DRC 0 e paridade 0.
- [ ] 5. Flexão: `pcb/mechanics.py` já escrito (importa o da J1), rodar depois da placa; nota sobre áudio e calor.
- [ ] 6. `README.md`, `PINOS.md`, imagens; PR e merge.

## Como rodar (da raiz do repositório)

```bash
python etutti/hardware/student_viaggio/pcb/layout.py
```

```bash
python etutti/hardware/student_viaggio/pcb/schematic.py
```

```bash
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_viaggio/pcb/build_board.py
```

## Armadilhas já encontradas

- No pcbnew, depois de `board.Remove(peça)`, guardar o objeto Python (função `rm()` do `build_board.py`). Se ele for coletado, as chamadas seguintes devolvem `SwigPyObject` cru.
- Scripts com barras invertidas não passam por heredoc do Bash: escrever com a ferramenta Write.
- `pcbnew.SaveBoard` reescreve o `.kicad_pro` e o bloco `(setup …)`: o `build_board.py` repõe os dois a partir da J1.
- O roteador (`viaggio_j1/rota_restante.py`) não põe via dentro de pad SMD da própria rede: a via de sinal de cada tecla é posta pelo `build_board.py` antes dos pentes.
