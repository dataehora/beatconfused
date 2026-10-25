# eTutti Viaggio MicroMod · relatório da eletrônica

**SPEC v2.3, passo M2 (placa para rotear), 25 out 2026.** Dono: eletrônica. A placa está posicionada
e **sem trilhas e sem vias**: nenhum roteador foi usado (o `router.py` do v2.1 não foi copiado nem
importado). Nada foi encomendado.

## Passo M2: resultado

| Conferência | Resultado |
|---|---|
| ERC do esquema | **0 erros, 0 avisos** |
| Netlist do KiCad × lista do script | igual (99 redes, 141 peças, 6 folhas) |
| DRC da entrega (`kicad-cli pcb drc --schematic-parity --severity-all`) | **0 erros, 0 avisos** |
| Paridade com o esquema | **0** |
| Ligações a rotear | **431** (T 220, E 98, F 31, P 12, A 11, I 7, entre setores 52) |
| `.kicad_dru` | compila no KiCad 10.0.7 sem erro; as 6 regras próprias disparam num teste com violações de propósito |
| Peças sob o cartão do MicroMod | C101 (1,45), C102 (0,55), R301 (0,4), R302 (0,4): **todas ≤ 1,9 mm** |
| Peças fora do perfil A | nenhuma, além de E1 e F2 (permitidas) |
| Sobreposição de pátios | nenhuma; nenhuma peça precisou ser empurrada |

Por setor, as 431 ligações: T 220, E 98, F 31, E-P 14, P 12, A 11, F-P 11, I-P 8, P-T 7, I 7,
A-F 3, E-I 3, E-T 2, e 1 em cada um de A-E, A-I, A-P e F-I.

### O que foi feito

- **M2a, esquema** (`pcb/schematic.py`, `pcb/footprints.py`):
  - **J101 = UMAX 91302-42-067RCE** (LCSC C48985906) no lugar do LOTES. O footprint foi refeito pelo
    desenho da UMAX e se chama `M.2_E_H4.2_UMAX_91302-42-067`. O do M1, com o nome do TE, foi apagado.
  - **H101 continua o Würth 9774025151R** por Global Sourcing (ver abaixo).
  - **E2 no lado de cima** (U201 e o TVS D201). O esquema não guarda lado: ficou na nota das duas
    peças ("lado de cima, junto do USB-C (SPEC v2.3)"), no `bom_preliminar.csv`, e o lado de fato está
    no `build_board.py`.
  - `bom_preliminar.csv` regerado (J101 e notas). **`PINOS.md` não mudou:** nenhum pino mudou.
- **M2b, placa** (`pcb/build_board.py`, um script só, que junta o `build_board.py` e o
  `handoff_freerouting.py` do v2.1, sem a parte de roteamento):
  - contorno 246,5 × 95 com cantos R 5; 8 furos M2 do contrato, com anel livre de cobre de 3,5 (áreas
    de regra) e pátio do tamanho da cabeça do parafuso (Ø 3,8);
  - serigrafia: perfil A pontilhado, E1/F2 do v1 tracejados, área do logo, códigos P1…T4 e o
    contorno do cartão do MicroMod no B.SilkS;
  - todas as peças pelo `concept/out/viaggio_micromod.json`, com os passivos junto dos seus chips;
  - a placa ligada ao esquema (F8 limpo), com redes `unconnected-(...)` nos pinos livres;
  - empilhamento JLC04121H-7628 de 1,2 mm. **In1 = GND**, tipo power, com uma zona de GND inteira.
    **In2 = signal, sem nenhuma área.** F.Cu e B.Cu são signal;
  - classes, regras, `.kicad_dru`, DSN e imagens. O DRC tem de dar 0 erros, senão o script sai com
    erro. Também sai com erro se houver peça alta sob o cartão, trilha ou via na placa, ou falha do DSN.
- **`pcb/ROTEAMENTO.md`** curto: arquivos, camadas, classes, e "não rode o `build_board.py` sobre a
  placa que o J rotear".

Para refazer a entrega (só antes de rotear):

```
python etutti/hardware/viaggio_micromod/pcb/schematic.py
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_micromod/pcb/build_board.py
```

São ~1 min. Saídas em `pcb/build/`:
- `viaggio_micromod.dsn`;
- `viaggio_micromod_top.png` e `_bottom.png`;
- `viaggio_micromod_posicionamento.svg`;
- `viaggio_micromod_handoff.json`, com DRC, posições, desvios e peças sob o cartão.

### O conector J101

| | |
|---|---|
| Peça | **UMAX 91302-42-067RCE**: M.2 Key E, 67 contatos (75 posições), passo 0,5, **altura 4,2**, contatos com 15 µin de ouro, SMD em ângulo reto, fita e carretel |
| Código | **LCSC / JLCPCB C48985906**, peça estendida |
| Estoque | **622 peças na LCSC, lido em 25 out 2026** (todas "envio imediato"; preço US$ 1,26 em 1 peça, 1,04 em 10). A página da JLCPCB (`jlcpcb.com/partdetail/C48985906`) não mostra o estoque a um leitor sem navegador: **não consegui ler o estoque da JLC**. O número é o da LCSC, que abastece a montagem da JLC. Conferir no carrinho da JLC antes de pedir |
| Desenho | [UMAX C-91302-42 rev C (dez 2024), 5 folhas](https://datasheet.lcsc.com/datasheet/pdf/fa57621554b717c54a395d0658cff748.pdf?productCode=C48985906) |
| Por que não o LOTES | o **LOTES APCI0108-P001A (C841659) tem estoque 0** na LCSC (mesmo dia), e a altura dele é 4,05 na página |

Medidas conferidas na folha 2 do desenho ("PCB layout"), iguais ao footprint do TE 2199230-4 usado
no M1:

- pads de **0,30 ± 0,03 × 1,55 ± 0,03**, passo 0,5 em cada fileira;
- fileira ímpar (1…75) de **4,5 a 6,05** da linha dos furos; fileira par (2…74) de **1,5 a 3,05**
  do outro lado (total 9,1);
- pino 1 a **9,25** e pino 2 a **9,0** da linha de centro;
- furos sem cobre: **Ø 1,10 ± 0,05** do lado do pino 1 e **Ø 1,60 ± 0,05** (datum X), a **20,0** um
  do outro;
- pinos de fixação de **1,20 × 2,75**, a **±10,35** do centro, centrados a **4,5** da linha dos furos;
- corpo de 21,85 × 8,35 com as pernas, altura máxima **4,20** (folha 1); pinos-guia de Ø 0,90 e
  Ø 1,45 (folha 1).

O desenho mostra o pino 1 à esquerda e a fileira ímpar em cima. O footprint é esse desenho girado
180° (pino 1 em +x, fileira ímpar em +y): uma rotação, não um espelho. O furo de 1,1 continua do lado
do pino 1, como no desenho e no footprint da SparkFun.

### H101 (espaçador)

- Fica o **Würth 9774025151R** (M2.5 × 2,5) por Global Sourcing, como a SPEC v2.3 aceita.
- Procurei um equivalente com estoque na LCSC e não achei de 2,5 mm:
  - **YIYUAN SMTSOM2.520BTR** (C5301776, M2.5, "L2+1,53"): estoque 0;
  - **YIYUAN SMTSOM2.565BTR** (C5301782): 6,5 mm, alto demais;
  - os PEM SMTSO-M25 têm 3 e 6 mm.
- O footprint não mudou: pad de 6,0 com furo metalizado de 3,7. **O furo atravessa a placa** e aparece
  em cima, na área do logo, em (47,5; 14).

### Onde as peças saíram do JSON, e por quê

| Peça | No JSON | Na placa | Por quê |
|---|---|---|---|
| **P1** (J101 + cartão + H101) | centro (37; 17), 22 × 27, conector ao longo de x | **conector ao longo de y**, na borda esquerda do setor P: pátio x 21,1–30,9, y 6,7–29,3, origem em (27,5; 18), rot 90 no verso. Pino 1 atrás (y pequeno), **cartão para +x**: x 30,2–49,5, y 7–29. Espaçador H101 em **(47,5; 14)** | A SPEC deixa a orientação livre. Assim os pads do USB (3 e 5) ficam de frente para o E2, a ~4 mm (o par E1 → E2 → J101 fica com ~15 mm, em vez de ~25 com o conector deitado). Os pads do I2S (50–58) ficam em y ≈ 21–23, a ~14 mm do F1 (24; 35,5). Ocupa o mesmo setor P |
| **E2** (U201) | (14; 13), lado de baixo | **(18,9; 12,2), lado de cima** | O lado vem da SPEC v2.3. Os 4,9 mm para a direita põem o chip dentro do perfil A (SPEC §2: só E1 e F2 ficam fora). Ele fica na linha do par USB que sai do E1 |
| D201 (TVS do VBUS, E2) | — | em cima, (17; 15,5) | vai junto com o E2 |
| R201/R202 (CC do E1) | — | no verso, sob o E2 | deixam o lado de cima livre para o par USB |
| A2 (J501) | (31; 78), o alto-falante | pads dos fios em (46,5; 84), em cima | o alto-falante fica no case; os fios saem perto do A1, como no v2.1 |
| E4 (U204 + L201) | (72; 9) | lado a lado centrados em (72; 9): U204 em 69,5, L201 em 74,2 | dois corpos no mesmo ponto, como no v2.1 |
| T3 (U603–U605) | (150; 10,5) | lado a lado centrados no ponto | idem |
| TP101 | — | fora do cartão, em (29,8; 5,2) | tem de dar para alcançar com o módulo encaixado |

O resto está no ponto do JSON, com centro no pátio. Os passivos ficam no lugar livre mais perto dos
pads do chip que dividem rede com eles (C101 no pad 74, C102 no pad 2 do J101). Todos ficam dentro do
perfil A, fora do anel dos furos M2, e no lado de cima nunca sob uma tecla.

### Classes, vias e regras

| Classe | Redes | Largura | Folga |
|---|---|---|---|
| Default | sinais | 0,2 (mínimo 0,15) | 0,1 |
| USB | USB_DP, USB_DN | 0,24, vão 0,15 | 0,1 |
| Corrente | VBUS, VSYS, VBAT, BB_L1, BB_L2 | 0,8 | 0,2 |

- **Vias 0,5 / furo 0,3 em todas as classes.**
- A classe Nucleo do v2.1 saiu: as redes dela (DCDC do RT1062) não existem mais. As regras usam "não
  é USB nem Corrente".
- **USB: 0,24 / 0,15 em F.Cu sobre o In1.** O empilhamento é o mesmo; a conta continua a do
  `build/impedance.json`: Zdiff 91,2 Ω (solver 2D) e 93,7 Ω (IPC-2141). Não rodei o `impedance.py` de
  novo.
- **`.kicad_dru`**: todos os números com "mm", e nenhuma regra cita a classe "Default". São 7 regras:
  1. vias ≥ 0,5 / furo ≥ 0,3;
  2. sinais (não USB, não Corrente): mínimo 0,15;
  3. USB: 0,22–0,26, vão 0,14–0,20, fora dos pátios de J201, U201 e J101;
  4. USB só em F.Cu fora do pátio do J101;
  5. Corrente: mínimo 0,8 fora dos pátios de J201 (E1), U202 (E3), U204 (E4), J202 (E6), U501 (A1) e
     J101;
  6. Corrente dentro desses pátios: mínimo 0,15 (a afinação na entrada dos pinos);
  7. sob o cartão: uma asserção sobre o campo `Cabe_sob_cartao` de cada peça. O script o escreve a
     partir da altura (campo `Altura_mm`), porque a asserção do KiCad 10 não compara números (testei:
     `getField('Altura_mm') <= 1.9` passa até com 2,0).
- **Prova de que compila:** numa cópia da placa no scratchpad pus uma violação de cada tipo: trilha
  de sinal de 0,12, VSYS de 0,5 fora dos pátios, USB no B.Cu, via de 0,45/0,2 e o L201 (2,0 mm) sob o
  cartão. O `kicad-cli pcb drc` acusou todas, cada uma com o nome da sua regra própria, e não deu
  nenhum erro de leitura do `.kicad_dru`.
- **Área de regra `cartao_MicroMod`**, no B.Cu, sobre o retângulo do cartão. Ela não proíbe nada; serve
  de condição para a regra 7. Na placa de agora há 4 peças sob o cartão, todas de até 1,45 mm.

## Passo M1 (esquema, SPEC v2.2, PR #117)

### O que foi feito

- **Pasta nova** `viaggio_micromod/pcb/`, copiada de `viaggio/pcb/` com o projeto KiCad renomeado
  para `viaggio_micromod`:
  - arquivos, folhas e bibliotecas: `viaggio_micromod.kicad_sym`, `viaggio_micromod.pretty`, sym/fp-lib-table;
  - caminhos e títulos nos scripts;
  - saídas em `build/viaggio_micromod_*`.
- **Vieram:**
  - `schematic.py` (adaptado);
  - `footprints.py` (reescrito);
  - `sexpr.py`;
  - `snap.py` e `impedance.py`, com `build/impedance.json`. O empilhamento é o mesmo; não rodei de novo.
- **Ficaram de fora** (só serviam ao RT1062 na placa):
  - `rt1062_balls.json`, `router.py`, `viaggio_rota_P_parcial.kicad_pcb`;
  - o footprint BGA-196.
- **Ficaram de fora até o passo M2:**
  - `build_board.py` e `handoff_freerouting.py`: o primeiro importa o `router.py` e roteia o setor P;
    os dois serão copiados e ajustados no M2;
  - `ROTEAMENTO.md`;
  - o `fab/` e qualquer `.kicad_pcb`.
- **Folha P** reescrita:
  - J101, o conector M.2 Key E de 4,2 mm;
  - H101, o espaçador SMD M2.5;
  - TP101, o pad de teste do RESET#;
  - C101/C102, 10 µF + 100 nF no 3,3 V junto do conector;
  - R105, os 100 Ω do MCLK, mantido junto do conector.
- **Saíram:** RT1062, MKL02 e o seu LED, W25Q64, PSRAM, os dois cristais, indutor, ferrite e
  capacitores do DCDC do RT1062, diodos do SNVS, e o **E5** inteiro (LDO XC6206P332 + porta U206).
- **Folha E:** o EN do TPS63001 passa a ser o próprio EN_REQ. O USB_HOLD agora depende do **PWR_EN**
  (pad 3.3V_EN) em vez do +3V3 (ver "Liga/desliga" abaixo). Entraram 3 peças: R217 1 kΩ, R218
  100 kΩ e C213 1 µF.
- **Folhas F, I, A, T:** sem mudança de circuito. Muda só o nome da biblioteca do jack e do LED.
- **Resultado** de `python etutti/hardware/viaggio_micromod/pcb/schematic.py`:
  - **ERC: 0 erros, 0 avisos;**
  - **netlist do KiCad = lista do script** (99 redes, 141 peças no esquema, 6 folhas);
  - PWR_FLAG em BB_VINA, GND, SGTL_VDDA e VBUS.
- **`pcb/PINOS.md`** na numeração do Teensy MicroMod. **`pcb/bom_preliminar.csv`** regerado: 64
  linhas, incluindo o módulo e o parafuso, "em casa".

### O conector, pad por pad

A fonte é o **esquema da SparkFun** (`Hardware/MicroMod-Teensy.sch` em
[github.com/sparkfun/MicroMod_Teensy_Processor](https://github.com/sparkfun/MicroMod_Teensy_Processor)).

- Li as ligações rede por rede: pad do J1 → bola do RT1062 → pino do Teensy.
- Confirmei com o [guia do MicroMod Teensy](https://learn.sparkfun.com/tutorials/micromod-teensy-processor-hookup-guide/all).
- As 67 linhas do `MM_PADS` do `schematic.py` foram comparadas por script com o esquema da SparkFun,
  sem diferença.

| Pad | Nome MicroMod | No Teensy MicroMod | No Viaggio |
|---|---|---|---|
| 1, 7, 33, 36, 39, 45, 75 + 2 pinos de fixação | GND | GND | GND |
| 2, 74 | 3.3V | 3,3 V do módulo (antes da chave interna) | +3V3 de E4 |
| 3, 5 | USB_D+ / USB_D− | USB1 | USB-C pelo U201 |
| 4 | 3.3V_EN | **pino 28 (GPIO_EMC_32)** | PWR_EN |
| 6 | RESET# | **ONOFF do RT1062** | clique do volume (D205) + TP101 |
| 9 | USB_VIN | USB1_VBUS (por ferrite e jumper MEAS) | VBUS |
| 11 | BOOT# | PROGRAM do MKL02 (pull-up no módulo) | botão Program I4 |
| 72 | RTC_3V | VDD_SNVS_IN, por diodo | sem ligação |
| demais | ver `pcb/PINOS.md` | pinos 0–45 | 27 sinais, os mesmos números do v2.1 |

### Liga/desliga: o pad 3.3V_EN e o "desligar de verdade com USB"

**O que o pad 4 (3.3V_EN) faz no MicroMod Teensy.** É só o **pino 28** do Teensy (GPIO_EMC_32), um
GPIO comum. Não é o PMIC_ON_REQ.

- Na regra MicroMod ("Designing with MicroMod"), a placa-mãe põe um pull-up nele e o liga ao EN do
  seu regulador. O processador o baixa para cortar o 3,3 V.
- No Teensy ele é solto na partida, no reset e no bootloader.

**O módulo não expõe o PMIC_ON_REQ.** Ele fica dentro do módulo: liga a chave Q2/Q1, que passa o
3,3 V dos pads 2/74 para o "3.3V_CONTROLLED". Esse trilho alimenta o RT1062 (menos o SNVS) e o MKL02.

- O SNVS é alimentado pelo próprio 3,3 V do conector (diodo D2) ou pelo RTC_3V (pad 72).
- **O ONOFF do RT1062 sai no pad 6**, com o nome "RESET#". No esquema da SparkFun a rede chama
  ON/OFF e vai à bola M6.

**Conclusão pela regra P da SPEC:** o 3.3V_EN não é o pedido de desligar do processador. O EN de E4
**não** pode ser "3.3V_EN E EN_REQ". Também não vale usar o 3.3V_EN como EN direto, que é o costume
MicroMod: a gravação reinicia o RT1062, e o regulador cairia no meio dela.

**O que ficou no esquema** (a opção mais segura, que só depende do que confirmei no esquema da
SparkFun):

- **EN de E4 = EN_REQ** = clique do volume OU KEEP (pino 10) OU USB_HOLD.
- **USB_HOLD = VBUS E PWR_EN_S** (U203). PWR_EN_S é o pino 28 com:
  - pull-up de 100 kΩ (R218), o pull-up que a regra MicroMod pede;
  - 1 kΩ em série (R217);
  - 1 µF para o GND (C213).
- Solto (reset, bootloader, firmware que não sabe do pino), o pino 28 fica alto. Com USB, a placa
  continua ligada, e a gravação funciona como no v2.1.
- **Para desligar de verdade com USB, a firmware baixa o pino 28 e o KEEP.** O EN cai quando o
  clique é solto, e o módulo, o codec e os sensores ficam sem energia. Só o carregador continua, e
  a luz de carga aparece (como a SPEC pede).
- O C213 (τ = 100 ms) segura o PWR_EN_S baixo enquanto o 3,3 V cai (≪ 1 ms). A placa não religa
  sozinha quando o pino 28 fica solto ao apagar.
- A SPEC pede o desligar de verdade com USB: **cumprido, sem SNVS e sem LDO sempre ligado**. Saem o
  E5 e o U206. Desligado sem USB, sobra só o BQ24074 (~6 µA, datasheet), menos que no v2.1
  (~25–35 µA).

**Proteção do botão preso: fica.** O módulo expõe o ON/OFF (pad 6), então o D205 leva o clique do
volume ao ONOFF, como no v2.1.

- A firmware grava `BTN_PRESS_TIME` = 10 s no `SNVS_LPCR`. Com o clique preso 10 s, o SNVS desliga
  o RT1062 pela chave interna do módulo.
- Para travamentos sem clique, a firmware usa também o watchdog.
- **Cuidado:** um clique curto no ONOFF com o módulo ligado gera só uma interrupção do SNVS; não é
  reset. O "RESET#" do MicroMod, no Teensy, não reinicia. O TP101 serve para medir, não para
  reiniciar.

### Peças novas

| Código | Peça | LCSC | Montagem | Datasheet |
|---|---|---|---|---|
| P1 (J101) | ~~LOTES APCI0108-P001A~~ (no M2: **UMAX 91302-42-067RCE**, C48985906, ver acima) | C841659 (estendida) | JLC | [LCSC C841659](https://www.lcsc.com/datasheet/C841659.pdf); referência do footprint: [TE 2199230-4 rev B3](https://cdn.sparkfun.com/assets/9/c/e/b/6/MicroMod_M.2_Connector_Datasheet_TE_2199230-4.pdf) |
| P1 (H101) | **Würth 9774025151R**, espaçador SMD M2.5, 2,5 mm (o da SparkFun) | sem código confirmado | JLC Global Sourcing (conferir) | [Würth WA-SMSI 9774025151R](https://cdn.sparkfun.com/assets/f/d/2/b/e/MicroMod_Reflowable_Standoff.pdf) |
| P1 (MOD1) | SparkFun MicroMod Teensy (DEV-16402) | — | em casa | [produto](https://www.sparkfun.com/sparkfun-micromod-teensy-processor.html), [esquema/Eagle](https://github.com/sparkfun/MicroMod_Teensy_Processor), [guia](https://learn.sparkfun.com/tutorials/micromod-teensy-processor-hookup-guide/all) |
| P1 (SCR1) | parafuso M2.5 × 3, cabeça chata | — | em casa | vem no [KIT-16549](https://www.sparkfun.com/sparkfun-micromod-diy-carrier-kit-5-pack.html) |
| P1 (TP101) | pad de teste Ø1,5 | — | sem peça | — |
| E3 | R217 1 kΩ, R218 100 kΩ, C213 1 µF (0402) | C11702, C25741, C52923 (básicas) | JLC | — |

Os demais (E1–E4, E6, F, I, A, T) seguem os do Viaggio v2.1, com os mesmos códigos LCSC
(`bom_preliminar.csv`).

#### Footprints (`pcb/footprints.py` → `kicad/viaggio_micromod.pretty/`)

- **`M.2_Socket_E_H4.2_MicroMod`** (no M2: `M.2_E_H4.2_UMAX_91302-42-067`, mesmas medidas), tirado do desenho TE 2199230 rev B3, folha 3 ("recommended PCB
  outline"). Confere pad a pad com o footprint "M.2-CONNECTOR-E" da biblioteca SparkFun, usado nos
  carriers Data Logging e ATP.
  - 34 pads ímpares e 33 pares de 0,3 × 1,55, passo de 0,5 em cada fileira, com o pino n em
    x = 9,25 − 0,25 (n − 1);
  - fileira ímpar a 4,5–6,05 da linha dos furos, fileira par a 1,5–3,05;
  - dois pinos de fixação de 1,2 × 2,75 em (±10,35; 4,5);
  - furos sem cobre de Ø1,1 (lado do pino 1) e Ø1,6 em (±10; 0).
  - No F.Fab: o cartão de 22 × 22 e o lugar do espaçador em **(+4,0; −20,0)** do conector, onde a
    SparkFun o põe nos dois carriers (4,06/19,94 e 4,01/19,99).
- **`Standoff_SMD_M2.5_H2.5`**: pad de Ø6,0 e furo de 3,7, como no desenho da Würth. Fiz o pad
  metalizado, como a SparkFun (6,0/3,9), para o DRC não ver furo sem cobre dentro de pad. Rede GND.

### Consumo e autonomia

Não mudou o orçamento do v2.1, salvo:

- o módulo (RT1062 a 600 MHz, ~100 mA ativo, conferir) no lugar do RT1062 na placa;
- desligado: ~6 µA (só o BQ24074), em vez de ~25–35 µA, porque saiu o SNVS sempre alimentado.

O `POWER.md` fica para o M3, com a placa, como a SPEC §7 manda.

### O que a programação precisa ajustar

- **fqbn `teensy:avr:teensyMM`** em vez de `teensy:avr:teensy41`. O PC do J tem o Teensyduino 1.62,
  que já lista "Teensy MicroMod".
- **Pinos:** os mesmos 0–26 do v2.1. Nada muda nos `#define` de teclas, encoders, LED, I2S e I2C.
- **Novo, pino 28 (PWR_EN):**
  - na partida, deixar como entrada (sem pull-down);
  - para desligar com USB, `OUTPUT` + `LOW` e mais o KEEP baixo;
  - com USB, um clique curto já deixa a placa ligada: se o clique for solto antes de 2 s, desligar
    assim.
- **Sai o desligamento do SNVS** (`SNVS_LPCR` TOP/DP_EN) para desligar com USB.
- **Fica o `BTN_PRESS_TIME` = 10 s** no `SNVS_LPCR`. Somar o watchdog.
- **Pino 13** também acende o LED azul do módulo (~1,3 mA). O LED de erro do bootloader agora é o
  amarelo do módulo.
- Detalhes em `pcb/PINOS.md`.

## Consumo e autonomia

Sem mudança desde o M1: o módulo consome ~100 mA a 600 MHz (conferir), e desligado sem USB fica só o
BQ24074 (~6 µA). O `POWER.md` fica para o M3, como a SPEC §7 manda.

## O que a programação precisa ajustar

Nada novo no M2: o `PINOS.md` não mudou. Continua valendo o que o M1 pediu: fqbn
`teensy:avr:teensyMM`, pinos 0–26 do v2.1 e pino 28 = PWR_EN.

## Itens (conferir)

1. **Estoque do J101 na JLCPCB:**
   - lido só o da LCSC: 622 peças em 25 out 2026;
   - a página da JLC não mostra o estoque sem navegador;
   - conferir no carrinho da JLC antes de pedir.
2. **Altura do cartão no UMAX:**
   - a folha 1 do desenho UMAX mostra **2,85 ref.** no esquema de encaixe;
   - o TE 2199230-4 dá 2,48 ref. para o cartão, e a SparkFun usa o espaçador de 2,5 mm;
   - se a altura do contato no UMAX for mesmo 2,85, o cartão fica ~0,35 mm inclinado sobre 20 mm. Isso
     pede um espaçador de ~3 mm, ou o cartão sente a flexão;
   - conferir com a peça na mão, ou com uma pergunta à UMAX.
3. **Posição do espaçador:** (+4,0; −20,0) do conector, que na placa dá (47,5; 14).
   - A especificação MicroMod põe o parafuso 4 mm à direita da linha de centro do cartão, o que
     confirma o +4.
   - O −20 vem de dois carriers da SparkFun.
   - Conferir com o módulo na mão.
4. **Espaçador H101:**
   - o Würth fica por Global Sourcing; não há equivalente LCSC de 2,5 mm com estoque;
   - o furo de 3,7 atravessa a placa: no lado de cima, fica na área do logo;
   - conferir o desenho Würth: furo metalizado ou sem cobre.
5. **Alturas da tabela `HEIGHT_MM`** do `build_board.py` (máximos de datasheet ou modelo 3D): 0805
   1,45; SOT-23 1,45; QFN 1,0; TSSOP 1,2; X2SON 0,4; FNR4020 2,0; TS-1187A 1,5; JST PH SMD 6,0. Sob
   o cartão só estão 0805 e 0402.
6. **Altura do conjunto sob a placa** (espaçador + cartão + peças do módulo): medir o módulo, a SPEC
   estima 6–7 mm.
7. **Pino 28 em reset** e **consumo do módulo**: como no M1, conferir no protótipo.

## Perguntas para a gestão

1. **P1 de pé (conector ao longo de y, cartão para +x):** a SPEC deixa a orientação livre, e assim o
   USB e o I2S ficam mais curtos. O retângulo do P1 fica x 21–49,5, y 6,7–29,3, dentro do setor P.
   Aceitam? O design precisa saber disso para o furo do fundo do case.
2. **E2 4,9 mm à direita do JSON** (18,9 em vez de 14), para ficar dentro do perfil A. Aceitam, ou o
   perfil A deve passar a incluir o E2, como já inclui E1 e F2?
3. **Espaçador:** se o UMAX confirmar o cartão a 2,85 mm (item 2 acima), trocamos para um espaçador de
   3 mm (por exemplo o PEM SMTSO-M25-3ET, por Global Sourcing)? Ou compramos um conector UMAX junto com o
   módulo (pergunta 1 da SPEC §8) e medimos antes do M3?
4. **Estoque do J101:** 622 na LCSC hoje. Reservamos já (US$ 1,26 cada) ou esperamos o fim do
   roteamento?
