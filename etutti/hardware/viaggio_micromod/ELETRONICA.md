# eTutti Viaggio MicroMod · relatório da eletrônica

**SPEC v2.2, passo M1 (esquema), 25 out 2026.** Dono: eletrônica. Nada foi posicionado, roteado
nem encomendado.

## O que foi feito

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

## O conector, pad por pad

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

## Liga/desliga: o pad 3.3V_EN e o "desligar de verdade com USB"

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

## Peças novas

| Código | Peça | LCSC | Montagem | Datasheet |
|---|---|---|---|---|
| P1 (J101) | **LOTES APCI0108-P001A**, M.2 Key E, 67 pinos, 0,5 mm, H 4,2 | C841659 (estendida) | JLC | [LCSC C841659](https://www.lcsc.com/datasheet/C841659.pdf); referência do footprint: [TE 2199230-4 rev B3](https://cdn.sparkfun.com/assets/9/c/e/b/6/MicroMod_M.2_Connector_Datasheet_TE_2199230-4.pdf) |
| P1 (H101) | **Würth 9774025151R**, espaçador SMD M2.5, 2,5 mm (o da SparkFun) | sem código confirmado | JLC Global Sourcing (conferir) | [Würth WA-SMSI 9774025151R](https://cdn.sparkfun.com/assets/f/d/2/b/e/MicroMod_Reflowable_Standoff.pdf) |
| P1 (MOD1) | SparkFun MicroMod Teensy (DEV-16402) | — | em casa | [produto](https://www.sparkfun.com/sparkfun-micromod-teensy-processor.html), [esquema/Eagle](https://github.com/sparkfun/MicroMod_Teensy_Processor), [guia](https://learn.sparkfun.com/tutorials/micromod-teensy-processor-hookup-guide/all) |
| P1 (SCR1) | parafuso M2.5 × 3, cabeça chata | — | em casa | vem no [KIT-16549](https://www.sparkfun.com/sparkfun-micromod-diy-carrier-kit-5-pack.html) |
| P1 (TP101) | pad de teste Ø1,5 | — | sem peça | — |
| E3 | R217 1 kΩ, R218 100 kΩ, C213 1 µF (0402) | C11702, C25741, C52923 (básicas) | JLC | — |

Os demais (E1–E4, E6, F, I, A, T) seguem os do Viaggio v2.1, com os mesmos códigos LCSC
(`bom_preliminar.csv`).

### Footprints (`pcb/footprints.py` → `kicad/viaggio_micromod.pretty/`)

- **`M.2_Socket_E_H4.2_MicroMod`**, tirado do desenho TE 2199230 rev B3, folha 3 ("recommended PCB
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

## Consumo e autonomia

Não mudou o orçamento do v2.1, salvo:

- o módulo (RT1062 a 600 MHz, ~100 mA ativo, conferir) no lugar do RT1062 na placa;
- desligado: ~6 µA (só o BQ24074), em vez de ~25–35 µA, porque saiu o SNVS sempre alimentado.

O `POWER.md` fica para o M3, com a placa, como a SPEC §7 manda.

## O que a programação precisa ajustar

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

## Itens (conferir)

1. **Conector J101:**
   - o LOTES APCI0108-P001A (C841659) está na LCSC como "M.2 E key, H4.2", mas a página dá 4,05 mm
     de altura e não mostra estoque nem preço a um script;
   - conferir o estoque e o desenho do LOTES contra o footprint (feito pelo TE 2199230-4);
   - alternativa na JLC: UMAX 91302-42-067RCE (C48985906, E key, 4,2 mm, estendida, estoque não
     visto); o TE 2199230-4 só por Global Sourcing.
2. **Espaçador H101:**
   - sem código LCSC confirmado para M2.5 × 2,5 mm;
   - os SMTSOM da YIYUAN na LCSC têm 2,0 mm (C5301776, M2.5) e 2,5 mm só em M2 (C5301773);
   - **a altura certa é a do cartão encaixado:** o desenho TE dá 2,48 mm ref., e a SparkFun usa o de
     2,5 mm. Fica o Würth 9774025151R por Global Sourcing até achar um equivalente.
3. **Posição do espaçador:** (+4,0; −20,0) do conector, tirada de dois carriers da SparkFun.
   Conferir com o módulo na mão antes do M2. O entalhe do cartão parece fora do centro.
4. **Altura do conjunto sob a placa:** espaçador 2,5 + cartão do módulo (~0,8, conferir) + peças do
   verso do módulo. Medir o módulo; a SPEC estima 6–7 mm.
5. **Peças sob o cartão: até 1,9 mm** (SparkFun). A placa M2 precisa de uma área de exclusão de
   altura sobre o retângulo de 22 × 22.
6. **Pino 28 em reset:** conferir no protótipo que fica alto com o R218. A trava "keeper" do pad pode
   segurar o último nível; só importa se a firmware o baixar e travar, e aí ela queria desligar.
7. **Par USB:** a SPEC põe D+/D− em cima e descendo perto do P1, que está no verso. No verso, a
   referência é a In2, que virou camada de trilhas. Ver a pergunta 2.
8. **Consumo do módulo** (~100 mA a 600 MHz) e dos LEDs do módulo: medir no protótipo.

## Perguntas para a gestão

1. **Espaçador:** aceitam o Würth 9774025151R por Global Sourcing (único com 2,5 mm confirmado), ou
   preferem que eu procure um equivalente LCSC e meça um módulo antes do M2?
2. **USB no verso:** o J101 fica embaixo e a In2 virou trilha. Pode o par D+/D− descer cedo para o
   verso com uma área de GND contínua na In2 sob ele (corredor C1)? Ou fica em cima até o J101,
   com as 2 vias junto do conector?
3. **Pino 28 = PWR_EN (pad 3.3V_EN):** a placa obedece à regra MicroMod (pull-up, baixo = desliga),
   com a trava pela USB no lugar do PMIC_ON_REQ do v2.1. Aceitam esse esquema de liga/desliga?
4. **TP101 (RESET#):** no Teensy MicroMod esse pad é o ONOFF, não um reset. Fica só o pad de teste
   (como a SPEC pede), ou querem um botão de reset de verdade? Não há POR_B no conector; o "reset"
   seria pelo Program.
