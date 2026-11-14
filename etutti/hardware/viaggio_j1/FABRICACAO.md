# eTutti Viaggio J1 · passo M3 (conferência e fabricação)

Atende a **SPEC v2.4** (`etutti/hardware/viaggio_micromod/SPEC.md`, "Tarefas para o Code (v2.4)"), sobre a placa `kicad/viaggio_micromod.kicad_pcb` do `main` depois do PR #126 e do commit 93aa0e3. Branch `viaggio-j1-m3`.

Medidas em mm, no referencial do KiCad (x para a direita, y para baixo, isto é, em direção ao músico). **(conferir)** = estimativa a confirmar com a peça real ou o datasheet.

## Estado dos lotes

| Lote | O quê | Estado |
|---|---|---|
| 1 | ajustes pedidos na v2.4 | **feito** (commit f2d50a8) |
| 2 | conferências: DRC final, placa × firmware 28/28, flexão, alturas | **feito** (commit 7d7f39f) |
| 3 | fabricação: Gerbers, furação, BOM/CPL, plate, POWER.md, imagens | **feito** (commit do lote 3) |
| M3b | SPEC v2.5: códigos LCSC, serigrafia, altura do SW403, `fab/` refeito com ENIG | **feito** (branch `viaggio-j1-m3b`, seção M3b no fim) |

Se a sessão cair, a próxima parte do último lote enviado (`git log` da branch) e desta tabela.

## Como rodar

```
python etutti/hardware/viaggio_micromod/pcb/schematic.py          (esquema, ERC, BOM preliminar)
copiar viaggio_micromod/pcb/kicad/viaggio_micromod_E.kicad_sch para viaggio_j1/kicad/
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/m3.py lote1
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/m3.py lote2
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/mechanics.py
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/m3.py lote3
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

## Lote 3 · fabricação (nada foi encomendado)

`"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/m3.py lote3`. Ele lê a placa como o lote 2 a deixou e não muda nada nela.

### Arquivos em `fab/`

| Arquivo | O quê |
|---|---|
| `viaggio_j1_gerbers.zip` | Gerbers das 4 camadas de cobre (F.Cu, In1, In2, B.Cu), pasta, máscara e serigrafia dos dois lados, contorno, mais a furação Excellon em mm (PTH e NPTH separados) e o job file. Gerado pelo `kicad-cli` |
| `viaggio_j1_bom.csv` | BOM no formato da JLCPCB (Comment, Designator, Footprint, LCSC Part #): 42 linhas, 140 peças. Global Sourcing marcado no Comment |
| `viaggio_j1_cpl.csv` | CPL da JLCPCB, os dois lados num arquivo (coluna Layer): 11 peças em cima, 129 embaixo |
| `viaggio_j1_fora_da_montagem.csv` | o que a JLC não monta: 28 Gateron, 8 furos M2, TP101, J501 (fios do alto-falante), o módulo MicroMod, o parafuso do módulo, o plate, o alto-falante e a bateria |
| `viaggio_j1_plate_gerbers.zip` | plate de FR-4 de 1,6 mm (ver abaixo) |
| `viaggio_j1_top.png`, `viaggio_j1_bottom.png` | render 3D da placa final, de cima e de baixo (olhados) |
| `viaggio_j1_plate_top.png` | render do plate (olhado) |

A fonte do plate é `kicad/viaggio_j1_plate.kicad_pcb`.

### Parâmetros do pedido da placa (JLCPCB)

- 4 camadas, **1,2 mm**, empilhamento **JLC04121H-7628** (o mesmo do arquivo, que já tem a espessura 1,2 e 4 camadas de cobre).
- 246,5 × 95 mm, cantos R 5.
- Vias: **1313, todas 0,5 / furo 0,3**. Não há via no pad: a única, a do C304, saiu no lote 1.
- Trilha mínima: **0,12** (só as 3 da EN_B do U711); o resto ≥ 0,15. Folga mínima 0,1.
- Acabamento: **ENIG** (decidido na SPEC v2.5; X2SON de 0,5 de passo, QFN de 0,4 do codec, conector M.2 de 0,5).
- Máscara: vias tampadas (tented), o padrão da JLC.

### BOM e CPL

- **Global Sourcing:** T4 (28 × TMAG5253BA3IQDMRR) e H101 (Würth 9774025151R). Estão no BOM sem código LCSC, com "[GLOBAL SOURCING JLCPCB, sem codigo LCSC]" no Comment.
- **Fora da montagem:** o módulo MicroMod (DEV-16402) e os Gateron (lista em `viaggio_j1_fora_da_montagem.csv`).
- **Códigos LCSC que faltavam no esquema**, achados em páginas públicas da LCSC/JLCPCB em 28 out 2026 e postos só no BOM de fabricação. O esquema ainda não os tem:
  - FB301, ferrite 600 Ω @ 100 MHz 0603: **C1002** (Sunlord GZ1608D601TF, 200 mA, básica);
  - R501, 680 kΩ 0402: **C4131** (UNI-ROYAL 0402WGF6803TCE).
- **Ainda sem código: C307, 150 nF 0402** (o VAG do codec). Sugestão: Samsung CL05B154KO5NNNC, 16 V X7R. Não achei o código LCSC dela **(conferir antes de encomendar)**.
- **Encoders SW401/SW402** são THT: a JLC solda à mão (custo à parte, abaixo).
- **Rotações:** o CPL tem a rotação do KiCad, espelhada no verso (180 − a), mais a correção dos modelos da JLC por encapsulamento, a mesma tabela do plugin kicad-jlcpcb-tools:

  | Encapsulamento | Correção |
  |---|---|
  | SOT-23 (todas as variantes) | 180° |
  | TSSOP, VQFN, QFN, TQFN, DRC0010J, X2SON | 270° |
  | o resto (passivos, conectores, footprints próprios) | 0° |

  No total: 82 + 10 sem correção, 13 + 1 com 180°, 34 com 270°.
- **Conferir as rotações uma a uma na prévia da JLC antes de pagar (conferir).** Não há como ver os modelos da JLC daqui. Atenção especial a:
  - J101 (M.2), H101, J301 (jack), D401 (LED 1615), J202, SW403 e o USB-C: são footprints próprios ou com a origem fora do centro da peça, e a posição também pode precisar de ajuste;
  - TMAG5253 (X2SON): o pino 1 decide a leitura.

### Plate de FR-4 de 1,6 mm

- **Origem:** o plate do Pocket (`pocket/case/out/plate.dxf`, do design), lido linha a linha.
- O DXF tem y espelhado (y = 100 − y_dxf). Desespelhado, os 28 recortes do Pocket caem exatamente nas 28 teclas do J1, como a SPEC diz.
- **Mudanças:**
  - os 7 entalhes de parafuso do Pocket (R 3,5) foram fechados pela corda, porque o Viaggio não tem aqueles parafusos;
  - os 28 recortes de 14 × 14 foram refeitos nas posições das SW1–SW28 da placa;
  - entraram furos de 2,2 mm nos 4 furos M2 da placa que caem dentro do plate: H5, H6, H7 e H8.
- O DRC do plate dá 0 erros e o contorno é fechado.
- **(conferir com o design):** o plate ainda tem o contorno de hexágono do Pocket. A forma final e o que passa pelos furos M2 (parafuso, espaçador) são do case.

### Custo estimado para 5 placas (US$, sem frete e impostos)

| Item | Valor | Fonte e data |
|---|---:|---|
| PCB 4 camadas, 1,2 mm, 246,5 × 95, vias 0,3, 5 unidades | ~34 | cotação do J na JLC (SPEC v2.2, 25 out 2026); ENIG deve somar (estimativa) |
| Montagem Standard (dois lados): taxa de preparação | 50 | página de preços de montagem da JLCPCB (25 US$ por lado), lida em 28 out 2026 |
| Estêncil, 2 lados | ~17 | mesma página (~8,66 por lado) |
| Taxa de carregador por tipo de peça (~44 tipos, inclusive 2 de Global Sourcing) | ~66 | mesma página (1,5 por tipo na Standard; versões mais antigas da página falam em 3 só para as estendidas) **(estimativa)** |
| Juntas SMT: 598 por placa × 5 × 0,0017 | ~5 | FAQ de montagem da JLCPCB (0,0017 por junta) |
| Solda à mão dos 2 encoders (THT) | ~5 | FAQ (3,5 de mão de obra + 0,0173 por junta) |
| Peças, 5 placas (~24,3 por placa; 13,2 delas são os 28 TMAG5253 + o espaçador, de Global Sourcing) | ~122 | preços estimados do `bom_preliminar.csv` (LCSC/JLC, 25 out 2026) **(estimativa)**; a JLC compra quantidades mínimas dos passivos (centavos) |
| Global Sourcing: frete e manuseio até a JLC | ? | **(conferir na cotação)** |
| Plate FR-4 1,6 mm, 2 camadas sem cobre, ~180 × 86, 5 unidades | ~8 | estimativa pelo preço de placa de 2 camadas da JLC **(estimativa)** |
| **Total** | **~305 + frete + Global Sourcing** | ~61 por placa montada |

Fora desse total:
- 5 módulos MicroMod Teensy (~25 cada, ~125);
- 140 Gateron KS-20 (28 por instrumento);
- baterias, alto-falantes, capas e o case.

Fontes dos preços de montagem: [JLCPCB, preço da montagem](https://jlcpcb.com/help/article/pcb-assembly-price), [JLCPCB, FAQ de montagem](https://jlcpcb.com/help/article/pcb-assembly-faqs), [TechOverflow, resumo dos preços](https://techoverflow.net/2024/04/09/jlcpcb-pcba-assembly-price-overview/). Códigos LCSC: [C1002](https://jlcpcb.com/partdetail/Sunlord-GZ1608D601TF/C1002) e [C4131](https://www.lcsc.com/product-detail/C4131.html). O total é uma ordem de grandeza: a cotação da JLC, com o BOM e o CPL enviados, é que vale.

## Peças escolhidas no M3 (datasheets)

- C210, 10 µF 0603 10 V X5R, Samsung CL10A106KP8NNNC, LCSC C19702: [LCSC C19702](https://www.lcsc.com/product-detail/C19702.html).
- FB301, Sunlord GZ1608D601TF, LCSC C1002: [datasheet](https://datasheet.lcsc.com/lcsc/2310301640_Sunlord-GZ1608D601TF_C1002.pdf).
- R501, UNI-ROYAL 0402WGF6803TCE, LCSC C4131: [LCSC C4131](https://www.lcsc.com/product-detail/C4131.html).

O resto das peças é o do M1/M2 (`viaggio_micromod/ELETRONICA.md`).

## Itens (conferir)

1. Rotações e posições do CPL na prévia da JLC, sobretudo J101, H101, J301, D401, J202, SW403, J201 e os TMAG5253.
2. C307 (150 nF 0402) sem código LCSC.
3. Alturas: Gateron 11,6; jack 5,1; J202 6,0; SW403 1,5; módulo montado ~6–6,5 abaixo da placa.
4. Flexão: o modelo ignora o plate. A medida real fica para o protótipo com o case.
5. Consumo (POWER.md): nada medido nesta placa.
6. Plate: forma e furos M2, com o design.
7. Custos de Global Sourcing (frete e manuseio) e de ENIG.

## Perguntas para a gestão

1. **C202/C206:** troquei as duas peças de lugar na placa, sem mexer no esquema. Assim a referência e o `Codigo` batem com o esquema (C202 = E3 no norte do bloco; C206 = E4 na entrada do U204). Serve, ou preferem renumerar no esquema?
2. **C210 no lado de cima:** o capacitor de VSYS dos pinos OUT não coube no verso sem refazer quatro redes em volta do D205. Ficou em cima, logo acima dos pinos, com o GND junto das vias térmicas do U202. Aceito?
3. **C304 andou 0,59 mm** para o espaço do laço de +3V3, porque só assim a via de GND sai do pad. A v2.4 autorizou a trilha, não o movimento. Aceito?
4. **EN_B no U711:** 3 trechos de 0,12 ficam (a JLC faz 0,09). Aceito, ou o J refaz esse trecho por baixo do sensor?
5. **Apoios do case:** só com os 8 furos M2, a pior tecla dobra 1,23 mm. Com os 6 pilares Ø4 propostos (P1–P6), dobra 0,048 mm. O design põe esses pilares no fundo do case, ou preferem mais furos M2 na placa?
6. **Acabamento:** ENIG (recomendado pelos pads de 0,4–0,5) ou HASL?
7. **C307 sem código LCSC:** escolho um 150 nF 0402 com estoque e atualizo o esquema e a placa, junto com o FB301 e o R501, num passo curto antes de encomendar?
8. **Serigrafia:** a placa ainda diz "SPEC v2.3 passo M2" no texto de cima e de baixo. Troco para "J1 · M3" antes de encomendar? É só texto, mas é uma mudança na placa.

## M3b · últimos códigos e serigrafia (SPEC v2.5)

Atende a **SPEC v2.5**, "Tarefas para o Code (v2.5)", passo M3b, sobre a placa do `main` no commit 4b25bb1 (depois do PR #128). Branch `viaggio-j1-m3b`. Nada foi encomendado nem posto em carrinho.

### Como rodar

```
python etutti/hardware/viaggio_micromod/pcb/schematic.py          (esquema, ERC, BOM preliminar)
copiar viaggio_micromod/pcb/kicad/viaggio_micromod_A.kicad_sch e _F.kicad_sch para viaggio_j1/kicad/ (CRLF)
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/m3.py m3b
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/m3.py lote3 --sem-plate
```

O `m3b` sai com erro se a placa não for a do commit 4b25bb1, se um campo já tiver outro valor ou se o DRC piorar.

### O que mudou

**Na placa** (`kicad/viaggio_micromod.kicad_pcb`), 6 linhas em 6 blocos e nada mais:

| Objeto | Campo | Antes | Depois |
|---|---|---|---|
| C307 (150 nF, VAG do codec) | LCSC | vazio | **C162182** |
| FB301 (ferrite do VDDA) | LCSC | vazio | **C1002** |
| R501 (680 kΩ, SD_MODE) | LCSC | vazio | **C4131** |
| SW403 (Program) | Altura_mm | 20 | **1.5** (conferir) |
| texto de cima (F.Silkscreen, em (150; 92)) | texto | "eTutti Viaggio MicroMod - placa principal - SPEC v2.3 passo M2" | **"eTutti Viaggio MicroMod · J1 · SPEC v2.5"** |
| texto de baixo (B.Silkscreen, em (150; 92), espelhado) | texto | "eTutti Viaggio MicroMod - verso: modulo, chips, sensores TMAG5253" | **"eTutti Viaggio MicroMod · J1 · SPEC v2.5"** |

- **O texto de baixo não dizia "SPEC v2.3 passo M2".** Ele trazia "verso: modulo, chips, sensores TMAG5253". Segui a SPEC ao pé da letra: os dois lados passam a ter o mesmo nome da placa. Se quiserem de volta a descrição do verso, é uma linha (pergunta 2).
- O texto novo é mais curto: ocupa x 130,6–169,4 e y 91,0–93,0, centrado no mesmo ponto. A borda da placa fica a ~4,5 mm abaixo. O DRC não acusa nada de serigrafia (sem silk_over_copper, silk_edge_clearance ou silk_overlap). O "·" sai na fonte do KiCad (conferido no render `fab/viaggio_j1_top.png`).

**Método de gravação, o mesmo do M3.** O pcbnew muda só os campos e os textos e salva uma cópia. Do arquivo salvo entram no original só os 6 blocos mudados, e o script confere:
- cada bloco trocado difere do original em **exatamente uma linha**, a do valor novo;
- os outros **4025 blocos** ficaram idênticos ao original, texto a texto;
- **2976 objetos** (todas as trilhas, vias e zonas, e a posição, a camada e os pads de cada footprint) foram comparados por uuid com a placa do commit 4b25bb1: **idênticos**. Nenhuma trilha ou via nova, apagada ou mudada; nenhuma peça movida ou girada; as zonas nem foram repreenchidas (texto e campos não mexem no cobre).

O `git diff` da placa mostra só essas 6 linhas.

**No esquema** (`viaggio_micromod/pcb/schematic.py`):
- C307: LCSC **C162182** (tabela `PASSIVES`, "150nF 0402", status final).
- FB301: LCSC **C1002**, status final.
- R501: LCSC **C4131** (tabela `PASSIVES`, "680k 0402", status final).
- **As folhas que mudaram são a F (C307, FB301) e a A (R501), não a E.** A SPEC falava da folha E, mas nenhuma dessas peças está nela. A folha E regenerada ficou igual à do J1 (só a quebra de linha difere, CRLF no Git). Copiei para `viaggio_j1/kicad/` só a F e a A. Diferença de cada uma: só as linhas `(property "LCSC" ...)` (2 na F, 1 na A). As outras folhas (raiz, P, E, I, T) foram comparadas com as do J1: iguais.
- `bom_preliminar.csv` regenerado: só as 3 linhas dessas peças mudam (código, status final; o preço do C307 passou de 0,003 para 0,013).
- **ERC do esquema do J1: 0 erros, 0 avisos.** O `schematic.py` também: ERC 0/0 e netlist igual à declarada.
- **Paridade:** antes de gravar a placa, a paridade dava 3 (os 3 campos LCSC novos do esquema, que a placa ainda não tinha). Depois: **0**.

**No `viaggio_micromod/pcb/build_board.py`:** na tabela `HEIGHT_MM` (vale o primeiro prefixo que casa), "SW403" passou para antes de "SW40". Antes o SW403 casava "SW40" e ficava com 20 mm. O script não foi rodado (ele recria a placa do zero).

**No `m3.py`:**
- subcomando novo `m3b` (o que está acima);
- `lote3 --sem-plate`: refaz Gerbers, BOM/CPL e renders da placa e deixa o plate como está;
- o BOM agora **para com erro** se alguma peça montada pela JLC estiver sem código LCSC e fora do Global Sourcing. Saiu o remendo do M3 que punha os códigos do FB301 e do R501 só no BOM (`LCSC_FIX` ficou vazio): agora eles vêm da placa;
- os parâmetros do pedido ficam em `ORDER` e vão para o `m3.json` (`m3b_fab.pedido`): 4 camadas, 1,2 mm, JLC04121H-7628, **acabamento ENIG**, vias tampadas, vias 0,5/0,3, trilha mínima 0,12, folga mínima 0,1. O script confere a espessura e o número de camadas da placa contra eles.

### C307: a peça escolhida

| | |
|---|---|
| Peça | **Murata GRM155R71C154KA12D**, 150 nF ±10 %, **16 V, X7R**, 0402 |
| Código LCSC / JLCPCB | **C162182** |
| Classe na JLCPCB | **estendida** (não há 150 nF 0402 entre as básicas) |
| Estoque na LCSC | **31 850** unidades, lido em **28 out 2026** (API de produto da LCSC) |
| Preço LCSC | 0,0135 US$ (50+) a 0,0074 US$ (50 000+) |
| Página | [LCSC C162182](https://www.lcsc.com/product-detail/Multilayer-Ceramic-Capacitors-MLCC-SMD-SMT_Murata-Electronics_C162182.html) · [JLCPCB C162182](https://jlcpcb.com/partdetail/C162182) |
| Datasheet | [LCSC, C162182.pdf](https://www.lcsc.com/datasheet/C162182.pdf) |

- **Básica não há:** procurei 150 nF 0402 X7R nas listas de básicas da JLC e nas alternativas da LCSC. As básicas de 0402 nessa faixa são 100 nF (C1525) e 220 nF (C16772). Trocar o valor mudaria o VAG, que segue a Audio Board (0,15 µF), e a SPEC pede 150 nF.
- A Samsung CL05B154KO5NNNC, sugerida no M3, está **obsoleta** (Digi-Key) e não aparece na LCSC.
- **Alternativas na LCSC (mesma peça, 0402 X7R), estoque lido em 28 out 2026**, para o caso de o estoque do C162182 acabar até o M4:
  - CCTC TCC0402X7R154K160AT, 16 V: **C7393865**, 179 400 unidades (estendida);
  - YAGEO CC0402KRX7R7BB154, 16 V: **C505466**, 26 400 unidades;
  - Murata GCM155R71C154KE02D, 16 V (automotiva): C161164, 5 050 unidades;
  - TDK CGA2B3X7R1E154KT000F, 25 V: C46617467, 8 340 unidades.
- Escolhi a Murata (e não a CCTC, com mais estoque) por ser o fabricante de referência e por ter estoque de sobra para 5 placas. A estendida custa a taxa de carregador de mais um tipo de peça.

Os outros dois códigos, conferidos em 28 out 2026:
- FB301: **C1002**, Sunlord GZ1608D601TF, 600 Ω @ 100 MHz, 200 mA, 0603 ([JLCPCB C1002](https://jlcpcb.com/partdetail/Sunlord-GZ1608D601TF/C1002), [datasheet](https://datasheet.lcsc.com/lcsc/2310301640_Sunlord-GZ1608D601TF_C1002.pdf)).
- R501: **C4131**, UNI-ROYAL 0402WGF6803TCE, 680 kΩ 1 %, 0402; **estendida** na JLC (o M3 não dizia); 78 400 unidades na LCSC ([LCSC C4131](https://www.lcsc.com/product-detail/C4131.html)).

### `fab/` refeito

`m3.py lote3 --sem-plate`:

| Arquivo | O que mudou |
|---|---|
| `viaggio_j1_gerbers.zip` | **só as duas serigrafias** (`F_Silkscreen.gto`, `B_Silkscreen.gbo`). Cobre (4 camadas), máscara, pasta, contorno e furação conferidos arquivo a arquivo com os do M3: iguais, salvo a data de criação |
| `viaggio_j1_bom.csv` | só a linha do C307: agora `150nF, C307, C_0402_1005Metric, C162182`. **Nenhuma peça sem código**, salvo as duas de Global Sourcing (28 × TMAG5253 e H101). 42 linhas, 140 peças |
| `viaggio_j1_cpl.csv` | **igual** ao do M3 (nada se moveu) |
| `viaggio_j1_fora_da_montagem.csv` | igual |
| `viaggio_j1_top.png`, `viaggio_j1_bottom.png` | refeitos, olhados: o texto novo aparece nos dois lados |
| plate (`viaggio_j1_plate_gerbers.zip`, `viaggio_j1_plate_top.png`, `kicad/viaggio_j1_plate.kicad_pcb`) | **não refeitos**: nada no plate mudou |

O `POWER.md` não muda: nenhuma peça ou rede de energia mudou.

### DRC final

`kicad-cli pcb drc --schematic-parity --severity-all` (`build/drc_m3_m3b.json`, fora do Git):

| Tipo | Base (4b25bb1, com o esquema novo) | M3b |
|---|---|---|
| clearance, shorting_items, hole_clearance, hole_to_hole, copper_edge_clearance, furos, anéis, máscara, pátios | 0 | **0** |
| serigrafia (silk_over_copper, silk_edge_clearance, silk_overlap) | 0 | **0** |
| ligações não feitas | 0 | **0** |
| paridade com o esquema | 3 (os 3 campos LCSC) | **0** |
| track_width | 3 | **3**, as mesmas da EN_B no U711 (mesmos uuids do DRC final do M3; aceitas na v2.5) |

ERC do esquema do J1 (`build/erc_m3b.json`): **0**.

### Itens (conferir) para o M4

1. **Rotações e posições do CPL** na prévia da JLC, peça a peça, sobretudo J101, H101, J301, D401, J202, SW403, J201 e os 28 TMAG5253 (pino 1).
2. **Estoque** na hora do pedido: C162182 (C307; alternativas acima), TMAG5253 e H101 (Global Sourcing), e as estendidas em geral.
3. **Custo** do Global Sourcing (frete e manuseio) e do ENIG na cotação.
4. **Alturas:** módulo montado ~6–6,5 abaixo da placa; J202 6,0; espaçador 2,5; Gateron 11,6; jack 5,1; SW403 1,5.
5. **Flexão:** o modelo ignora o plate; os 6 pilares do case (P1–P6) são requisito do design.
6. **Plate:** forma e furos M2 com o design (o plate ainda tem o contorno do Pocket).
7. **Consumo** (`POWER.md`): nada medido nesta placa.

## Perguntas para a gestão (M3b)

1. **C307:** escolhi a Murata GRM155R71C154KA12D (C162182, 16 V X7R, estendida, 31 850 em estoque na LCSC em 28 out 2026). Não há 150 nF 0402 básica. Serve, ou preferem a CCTC C7393865 (179 400 em estoque) por segurança de estoque?
2. **Texto do verso:** ele não dizia "SPEC v2.3 passo M2", e sim "verso: modulo, chips, sensores TMAG5253". Pus o mesmo nome da placa nos dois lados, como a SPEC pede. Fica assim, ou o verso volta a ter a descrição depois do nome?
3. **Folha do esquema:** as três peças estão nas folhas F e A, não na E. Copiei para o J1 só essas duas. Confirmam que a SPEC queria dizer essas?
