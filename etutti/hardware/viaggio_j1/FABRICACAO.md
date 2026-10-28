# eTutti Viaggio J1 · passo M3 (conferência e fabricação)

Atende a **SPEC v2.4** (`etutti/hardware/viaggio_micromod/SPEC.md`, "Tarefas para o Code (v2.4)"), sobre a placa `kicad/viaggio_micromod.kicad_pcb` do `main` depois do PR #126 e do commit 93aa0e3. Branch `viaggio-j1-m3`.

Medidas em mm, no referencial do KiCad (x para a direita, y para baixo, isto é, em direção ao músico). **(conferir)** = estimativa a confirmar com a peça real ou o datasheet.

## Estado dos lotes

| Lote | O quê | Estado |
|---|---|---|
| 1 | ajustes pedidos na v2.4 | **feito** (commit f2d50a8) |
| 2 | conferências: DRC final, placa × firmware 28/28, flexão, alturas | **feito** (commit do lote 2) |
| 3 | fabricação: Gerbers, furação, BOM/CPL, plate, POWER.md, imagens | a fazer |

Se a sessão cair, a próxima parte do último lote enviado (`git log` da branch) e desta tabela.

## Como rodar

```
python etutti/hardware/viaggio_micromod/pcb/schematic.py          (esquema, ERC, BOM preliminar)
copiar viaggio_micromod/pcb/kicad/viaggio_micromod_E.kicad_sch para viaggio_j1/kicad/
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/m3.py lote1
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/m3.py lote2
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/mechanics.py
```

O `lote2` parte da placa que o `lote1` deixou; ele não roda o `lote1` de novo.

- O `lote1` sempre parte da placa do commit 93aa0e3 (tirada do Git), faz os ajustes e grava pelo **mesmo método dos PRs #120/#123/#126**: o pcbnew salva uma cópia, e só os objetos novos, removidos e mudados, mais as 4 zonas repreenchidas, entram no arquivo original. O script confere bloco a bloco, por uuid, que todo o resto ficou idêntico (4008 blocos).
- `.kicad_pro`, `.kicad_prl` e `.kicad_dru` não mudaram.
- O registro de tudo (peças, trilhas, vias, removidos, DRC) fica em `m3.json`.
- Cada trilha e via nova é conferida com as formas exatas do pcbnew antes de entrar (folga da classe + 0,005), pela classe `Geo` do `energia.py`.

## Lote 1 · ajustes (v2.4)

### 1. C202 / C206: referência e `Codigo` batendo com a função

**Decisão:** trocar as duas peças de lugar na placa, sem mexer no esquema.
- No esquema, o C202 é o capacitor de VSYS do carregador (E3) e o C206 é o capacitor de VSYS do conversor (E4). O PR #126 tinha posto o **C202** na entrada do U204 e o **C206** no norte do bloco, ao contrário da função.
- As duas são a mesma peça (10 µF 0805, C15850), com as mesmas redes (VSYS/GND). Então basta trocá-las de lugar na placa:
  - C206 (E4) vai para (69,60; 12,25; 180), a entrada do U204 (VIN, pino 5);
  - C202 (E3) vai para (64,67; 5,18; 180), o capacitor de VSYS no norte do bloco.
- Assim o esquema continua como o `schematic.py` gera, sem renumerar nada. Na placa mudam só a posição dos dois footprints. Trilhas e vias ficam iguais.
- **Atenção a quem lê o `COBRE.md`:** lá, "C202" é o capacitor de entrada do U204. Agora esse lugar é do C206.

### 2. Capacitor de VSYS junto dos pinos OUT (10/11) do U202: C210, no lado de cima

- **Peça nova no esquema:** C210, 10 µF 0603, VSYS/GND, `Codigo` E3, LCSC **C19702** (Samsung CL10A106KP8NNNC, 10 V, básica). Entra pelo `viaggio_micromod/pcb/schematic.py`, que regenera a folha E. A folha vai copiada para `viaggio_j1/kicad/`. ERC 0/0 no esquema do J1.
- **No verso não coube.** Procurei todas as posições a até 4 mm dos pinos (grade de 0,1, 4 rotações), mesmo sem o D205 e sem as vias de costura. Nenhuma passou. O canto a oeste dos pinos tem as 2 vias de VSYS, o D205 e as trilhas de VOL_SW, CHGLED, CHG_N e CHG_EN1. Mover o D205 obrigaria a refazer essas quatro redes.
- **No lado de cima coube, sem mover nada:** C210 em (60,76; 8,60; 270), em F.Cu, logo acima dos pinos OUT (que estão no verso, em x 60,56).
  - O pad de VSYS, em (60,76; 7,83), fica sobre a ponta da trilha de VSYS de F.Cu que sai das 2 vias dos pinos OUT. O caminho do pino ao capacitor é de ~3 mm, contra ~6 mm do capacitor mais perto antes.
  - O pad de GND, em (60,76; 9,38), vai por 0,85 mm de F.Cu a 0,3 até a via térmica do U202 em (61,60; 9,40). O retorno entra direto no pad térmico do carregador.
- **Montagem:** a placa já é montada dos dois lados (E1, E2, F2 e o LED estão em cima). O C210 é só mais uma peça 0603 no lado de cima, na área do logo. Altura 0,95.

### 3. C207 junto do C208

- O C207 (10 µF de +3V3) foi de (65,40; 13,90) para **(73,25; 5,70; 0)**, a 3,55 mm do C208 (de centro a centro). Distância percorrida: 11,35 mm.
- O pad de +3V3 (72,30; 5,70) liga ao C208.1 por 1,65 mm de B.Cu a 0,6, passando pela via de +3V3 do C208 em (71,40; 6,00).
- Vias novas, fora do corpo da peça: 2 de GND a leste do pad 2, em (75,10; 5,70) e (74,78; 4,83), e 1 de +3V3 a oeste do pad 1, em (71,47; 5,36).
- Saíram as 4 vias e os 4 tocos do lugar antigo, e 2 vias de costura de GND que ficavam sob o lugar novo, em (73,25; 5,75) e (74,75; 5,75).

### 4. C304: via de GND fora do pad

- Saiu a via de GND de dentro do pad 2, em (20,00; 35,00).
- Saíram 4 trilhas de +3V3 do laço do J entre C305.1 e C304.1, todas a 0,2 em B.Cu.
- **Só abrir o laço não bastou.** Uma via de GND colada ao C304, onde ele estava, não cabe em nenhum lado:
  - a leste, a linha **VOL_B** do In2 (x 20,894);
  - a oeste e ao sul, a **I2S_BCLK** em B.Cu (x 19,41 e a diagonal);
  - ao norte, a via e a trilha de F.Cu da **I2S_BCLK**;
  - ao sul, também a **HP_L** em F.Cu.
- **Solução:** o C304 andou **0,59 mm** para o espaço que o laço deixou, para (20,45; 35,89; 180), deitado. Foi a menor distância numa busca a até 2 mm.
  - O pad 2 (GND) tem agora a sua própria via em (19,97; 35,22), a 0,7 mm, ligada por 0,2. A via fica fora do pad.
  - O pad 1 (+3V3) fica na trilha nova de +3V3 do J refeita: C305.1 → C304.1 → junção com o U301 em (21,18; 36,86), toda a 0,2 em B.Cu, reta em x 21,181.
- A mudança está registrada como pergunta para a gestão, porque a v2.4 autorizou a trilha, não o movimento do C304. Ele já tinha andado 1,56 mm no PR #126.

### 5. DRC do lote 1

`kicad-cli pcb drc --schematic-parity --severity-all`, com o `.kicad_dru` da placa:

| | Base (93aa0e3) | Lote 1 |
|---|---|---|
| track_width | 7 (do J: 3 EN_B, 4 MUX_S0) | 7 (as mesmas) |
| clearance, short, furos, pátios, ponte de máscara, borda | 0 | 0 |
| ligações não feitas | 0 | **0** |
| paridade com o esquema | 0 (1 com o esquema novo, que já tem o C210) | **0** |

Nenhuma violação nova.

### Imagens do lote 1

Em `build/`, olhadas:
- `m3_lote1_energia_fcu.png`, `_bcu.png`, `_in2.png`: o bloco de energia, com o C210 em cima e o C207 junto do C208;
- `m3_lote1_c304_fcu.png`, `_bcu.png`, `_in2.png`: o C304 com a via fora do pad.

### Fora da pasta do J1

- O `viaggio_micromod/pcb/schematic.py` ganhou o C210. O `bom_preliminar.csv` e a folha E de `viaggio_micromod/pcb/kicad/` foram regenerados.
- A placa do M2 em `viaggio_micromod/pcb/kicad/` (sem roteamento) não tem o C210. Ela não é mais a placa que segue (SPEC v2.4) e não foi mexida.

## Lote 2 · conferências

### DRC final

`kicad-cli pcb drc --schematic-parity --severity-all`, com o `.kicad_dru` da placa (`build/drc_m3_final.json`, fora do Git):

| Tipo | Quantidade |
|---|---|
| clearance, shorting_items, hole_clearance, hole_to_hole, copper_edge_clearance | **0** |
| courtyards_overlap, solder_mask_bridge, via_diameter, hole_size, annular_width | **0** |
| track_dangling, via_dangling | **0** |
| ligações não feitas | **0** |
| paridade com o esquema | **0** |
| track_width | **3**, todas da EN_B no U711 (justificadas abaixo) |

**As 7 track_width do J:**
- **4 de MUX_S0, no In2, alargadas para 0,15** sem mover nada:
  - 3 em (25,0–25,3; 10,1–10,2), de 0,10–0,12;
  - 1 em (120,5–120,8; 7,9–8,2), de 0,12.

  O pcbnew conferiu cada uma a 0,15 com a folga de cada vizinho. A gravação trocou só esses 4 blocos e repreencheu as zonas; 4023 blocos ficaram idênticos.
- **3 de EN_B, em B.Cu, de 0,12, ficam.** São 0,75 mm em (144,14–144,70; 59,11–59,29), entre o pad 2 (GND) e o pad 3 (EN_B) do sensor U711 (tecla SW11, X2SON de 0,5 de passo). Por que ficam:
  - a 0,15 elas encostam no pad 2 (GND) do U711. Só alargar não cabe;
  - ali a EN_B leva aos sensores do grupo B a leste uma parte dos ~36 mA do grupo (SPEC §4). 0,75 mm de cobre de 35 µm a 0,12 dão ~3 mΩ, o que não pesa;
  - a JLCPCB fabrica trilha de 0,09 mm (3,5 mil) em 4 camadas. A regra de 0,15 é nossa, não da fábrica;
  - corrigir de verdade seria refazer esse trecho do J por baixo do U711, e o lote 2 não autoriza isso.

**Afinações na entrada de pinos.** São as trilhas mais finas que a largura da classe. Todas ficam dentro dos pátios que o `.kicad_dru` permite. A lista completa, rede por rede, está em `m3.json` (`lote2.afinacoes`).

| Classe | Redes | Larguras | Trecho mais comprido |
|---|---|---|---|
| Corrente (mínimo 0,8 fora dos pátios) | VBUS 12 trechos (0,15–0,5; 5,0 mm no total), VSYS 4 (0,24–0,3; 2,4 mm), VBAT 2 (0,24–0,3; 1,4 mm), BB_L1 e BB_L2 1 cada (0,24; 0,9 mm) | 0,15–0,5 | 1,13 mm (VBUS) |
| USB (0,24) | USB_DP 2 trechos e USB_DN 4, junto do J201, do U201 e do J101 | 0,2 | 1,18 mm |
| Sinais (o normal é 0,2, o mínimo 0,15) | 36 redes, de 1 a 19 trechos cada | 0,15 | 3,94 mm (I2C_SCL); na EN_B, 3,7 mm a 0,15, além das 3 de 0,12 |

### Placa × firmware: 28/28

O `m3.py lote2` lê a placa e confere tecla por tecla:
- o sensor U7nn está sob a tecla SWnn: mesmo centro, no verso, girado 180° como no Pocket;
- a saída OUT_Knn chega a um só canal de um só multiplexador;
- o EN do sensor é o do grupo daquele canal: EN_A nos canais 0–7, EN_B nos 8–15;
- a nota da tecla bate com `FIRST_NOTE` e `FIRST_COL`.

Confere também:
- nos pads do J101: o endereço S0–S3 (pads 19, 17, 47 e 32), os COMs (pads 34 e 38) e o SENS_EN (pad 10);
- as portas do T3: EN_A = SENS_EN e não S3; EN_B = SENS_EN e S3.

**Resultado: 28/28, 0 problemas.** O `KEY_INPUT` foi escrito no `viaggio_micromod/pcb/PINOS.md`. É **igual ao do Pocket v0.3**, canal por canal:

```c
const int8_t VIAGGIO_KEY_INPUT[4][8] = {
  { -1,  21,  20,  17,  19,   2,   1,   0},
  { 25,  26,  31,  29,  13,  11,  14,  15},
  { -1,  18,  23,  22,   4,   6,   5,   3},
  { -1,  28,  27,  24,   9,   8,  10,  -1},
};
```

Como no Pocket, o multiplexador 0 é o T2 (U602, COM no pino 14) e o 1 é o T1 (U601, COM no pino 15).

**O que a programação precisa ajustar:** nada nos pinos. O `PINOS.md` só ganhou a tabela de teclas; antes dizia "a do Pocket v0.3, a conferir". A firmware do Viaggio, quando existir, usa essa tabela, que é a mesma do `pocket_keys.h`.

### Flexão: não passa só com os 8 furos M2; passa com 6 pilares do case

`viaggio_j1/mechanics.py` é uma cópia adaptada do `etutti/hardware/mechanics.py`, que não foi mexido.
- **Modelo:** o mesmo do eTuttino e do Pocket. É uma grelha de vigas de 4 mm na placa nua de 1,2 mm (FR-4, E = 18 GPa), sem rigidez à torção e sem o plate de 1,6 mm. A placa real dobra menos.
- **Carga:** 3 N no centro de cada tecla, uma de cada vez.
- **Apoios:** os 8 furos M2 (H1–H8), presos.

| Apoios | Pior tecla | Média |
|---|---|---|
| só os 8 furos M2 | **1,23 mm** (SW28, canto de trás à direita); SW7 0,94; SW6 0,42; SW27 0,40 | 0,18 mm |
| 8 furos + **6 pilares** | **0,048 mm** (SW6) | 0,026 mm |

**Onde faltam apoios do case:** os furos estão na metade esquerda e no meio do teclado (H5–H8), e as pontas da direita (SW7, SW15, SW22, SW28) ficam soltas. O script propõe pilares Ø4 no fundo do case, um por vez, no lugar livre do verso mais perto da pior tecla.
- **Lugar livre:** a borda do pilar fica a ≥ 0,6 mm de pad, via ou corpo de peça (regra do eTuttino), fora do anel dos furos e fora do cartão MicroMod.
- **Os 6 pilares**, em mm, no referencial do KiCad:
  - P1 (197,5; 32,5) e P5 (127,5; 32,5), entre as fileiras 4 e 3;
  - P2 (207,5; 67,5), P3 (112,5; 67,5), P4 (167,5; 67,5) e P6 (132,5; 67,5), entre as fileiras 2 e 1.
- A imagem é `build/m3_flexao.png`. Cada tecla mostra a flexão em centésimos de mm: primeiro só com os furos, depois com os pilares.
- A alternativa seria pôr mais furos M2 na placa. Os pilares não pedem mudança na placa, porque tocam só a máscara.

### Alturas por lado

Vêm do campo `Altura_mm` de cada footprint, que o `build_board.py` do M2 preencheu, com uma correção. O Program (SW403, TS-1187A) estava com 20 mm: a tabela do `build_board.py` casava "SW40" (os encoders) antes de "SW403". A altura real é 1,5 mm **(conferir)**. O campo na placa ficou como estava; aqui vale 1,5.

**Lado de cima.** A peça mais alta são os **encoders I1/I2, com 20 mm**.

| Peça | Altura acima da placa (mm) | Onde (x; y) |
|---|---|---|
| SW401 / SW402, encoders EC11E vertical (I1, I2) | 20 (ponta do eixo) | (17,5; 56,3) / (33,5; 56,3) |
| SW1–SW28, Gateron KS-20 | 11,6 **(conferir)**, sobre o plate | o teclado, x 89–219 |
| J301, jack PJ-327A (F2) | 5,1 **(conferir)** | borda esquerda, y 20–30 |
| J201, USB-C TYPE-C-31-M-12 (E1) | 3,3 | borda esquerda, y 7,7–18,3 |
| U201 (E2), D201 | 1,45 / 1,1 | junto do USB-C |
| C210 (novo), D401 (LED) | 0,95 / 0,6 | (60,8; 8,6) / (50,0; 49,0) |

**Lado de baixo.** A peça mais alta é o **J202, conector da bateria, com 6,0 mm (conferir)**. O módulo vem logo depois.

| Peça | Altura abaixo da placa (mm) | Onde |
|---|---|---|
| J202, JST PH 3 vias SMD horizontal (E6) | 6,0 **(conferir)** | (64,5; 26,5) |
| P1: J101 (M.2 de 4,2) + módulo MicroMod | o cartão fica a 4,2 mm; somando o cartão (0,8) e as peças do módulo, ~6–6,5 **(conferir com o módulo)** | x 20,5–50,5; y 6,7–29,3 |
| H101, espaçador M2.5 | 2,5, mais a cabeça do parafuso (~1,5) sob o cartão | (47,5; 14,0) |
| L201, indutor 4 × 4 | 2,0 | (73,8; 9,0) |
| SW403, Program (I4) | 1,5 **(conferir)** | (52,0; 36,0) |
| chips, capacitores 0805, SOT-23 | ≤ 1,45 | |
| sensores TMAG5253 (X2SON) | 0,4 | sob cada tecla |

- **Sob o cartão MicroMod** só há peças de até 1,45 mm. A regra da SparkFun é 1,9, e o DRC confere pela regra "Sob o cartão MicroMod".
- **No teclado**, o verso só tem os sensores (0,4) e os capacitores 0402 deles (0,55). Os pilares do case passam entre eles.
