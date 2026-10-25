# eTutti Viaggio MicroMod · especificação · v2.3

**Versão 2.3, 25 out 2026** (v2.2 do mesmo dia + respostas ao relatório do passo M1). SPEC do **eTutti Viaggio MicroMod**. É o Viaggio Rev2 (`etutti/hardware/viaggio/`, SPEC v2.1) com o processador soldado na placa trocado por um módulo **SparkFun MicroMod Teensy** encaixado num conector M.2.

Mantida pela gestão (Claude Chat com o J); o Code não edita este arquivo. Mesmo protocolo do eTuttino Pocket (`CLAUDE.md`, "como trabalhamos"): cada disciplina responde no seu relatório, terminando com "Perguntas para a gestão".

Medidas em mm. **(conferir)** = estimativa a confirmar com a peça real ou o datasheet.

## Mudanças desde a versão anterior

### v2.3 (respostas ao `ELETRONICA.md` do passo M1, PR #117)

- **Liga/desliga aceito como o M1 fez** (pergunta 3):
  - EN de E4 = clique do volume OU KEEP (pino 10) OU USB_HOLD;
  - USB_HOLD = VBUS E PWR_EN (pino 28, pad 3.3V_EN, com pull-up);
  - para desligar com USB, a firmware baixa o pino 28 e o KEEP;
  - saem o SNVS sempre ligado, o E5 e a porta U206;
  - desligado sem USB, só o BQ24074 consome (~6 µA).
- **Proteção do botão preso fica:** o pad 6 do módulo é o ONOFF do RT1062, ligado ao clique do volume; `BTN_PRESS_TIME` = 10 s, mais o watchdog.
- **TP101 fica só como pad de teste** (pergunta 4). Não há reset de verdade no conector; para recuperar, usa-se o botão Program.
- **Espaçador:** o Würth 9774025151R (M2.5 × 2,5 mm) por Global Sourcing, que já usamos para os sensores (pergunta 1). Se a eletrônica achar um equivalente com estoque na LCSC no M2, pode trocar e registrar.
- **USB fica em cima** (pergunta 2):
  - **E2 (ESD) passa para o lado de cima**, junto do USB-C;
  - o par D+/D− corre em F.Cu sobre o GND do In1 até junto do J101;
  - desce com um par de vias colado ao conector.

  Assim o In2 fica livre para trilhas e o USB tem GND contínuo por baixo.
- **Conector J101:** a eletrônica escolhe no M2 o M.2 Key E 4,2 mm **com estoque na JLCPCB** (LOTES C841659, UMAX C48985906 ou outro) e faz o footprint pelo desenho da peça escolhida.
- **Firmware:** `teensy:avr:teensyMM`, pinos 0–26 iguais ao v2.1, mais o pino 28 (PWR_EN).

### v2.2 (Viaggio v2.1 → Viaggio MicroMod)

- **Por quê.** A saída das bolas do RT1062 (BGA 12 × 12) não fechou em nenhuma tentativa:
  - três sessões do Code, com o roteador próprio;
  - três ensaios do Freerouting feitos pelo J, com In2 liberada e com fanout.

  O melhor resultado deixou 75 ligações, quase todas no processador. O módulo tira o BGA da placa.
- **Processador: módulo MicroMod Teensy** (SparkFun DEV-16402, ~US$ 25). É o mesmo i.MX RT1062 a 600 MHz, com **16 MB de flash** e 1 MB de RAM. Ele encaixa num **conector M.2 Key E de 4,2 mm** e fica preso por um **parafuso M2.5** num espaçador SMD.
- **Saem da placa:**
  - o RT1062;
  - o bootloader MKL02;
  - a flash W25Q64JV;
  - o lugar da PSRAM;
  - os dois cristais;
  - o regulador do SNVS e a porta de partida (E5);
  - o indutor e os capacitores do conversor interno do RT1062;
  - o footprint BGA-196.
- **Sem PSRAM.** Os 16 MB de flash do módulo já cobrem os sons com amostras do futuro.
- **Montagem:** a JLC monta o conector M.2 e o espaçador. O J encaixa o módulo e aperta o parafuso em casa.
- **Firmware:** placa "Teensy MicroMod" no Teensyduino (conferir o `fqbn`). Os pinos do I2S (7, 20, 21, 23) e do I2C (18, 19) são os mesmos do Teensy 4.1. O resto é mapeado nos pinos que o MicroMod expõe.
- **Vias 0,5 / furo 0,3.** A cotação do J: furo de 0,2 sobe o preço de US$ 34 para 78 em 5 placas.
- **Camada In2 vira camada de trilhas** (tipo signal), com as áreas de 3,3 V e GND preenchidas depois do roteamento. Lição do ensaio 1: com In1 e In2 como planos, só sobravam duas camadas para as trilhas.
- **Roteamento pelo J** no KiCad com o Freerouting, seguindo o guia que ele já usa. O Code entrega a placa posicionada e depois confere e gera a fabricação (§7).
- **Pastas novas:** `etutti/hardware/viaggio_micromod/`. O Viaggio v2.1 (`viaggio/`) fica arquivado como referência e não muda mais.
- Contrato de posicionamento: `viaggio_micromod/concept/out/viaggio_micromod.json` (gerado por `concept/sectors.py`). É o mesmo plano da Rev2, com o setor P trocado pelo módulo.

## 0. O que é o Viaggio MicroMod

Um eTutti fino e alongado, com **toda a eletrônica numa placa só, montada pela JLCPCB**, menos o módulo do processador, que encaixa. Em casa: encaixar as teclas e o módulo, ligar a bateria e o alto-falante e gravar a firmware pela USB.

- **Prioridade: o detalhamento da placa.** O case vem depois e segue a placa.
- Base: o teclado e o lado direito do eTuttino Pocket (SPEC v5); o lado esquerdo é o do Viaggio Rev2.
- **Nada é encomendado** até o J decidir passar para essa fase.

## 1. Decisões (confirmadas pelo J)

| Tema | Decisão |
|---|---|
| Teclado | 28 botões C-griff, G3–E5, grade hexagonal de 18,5, fileiras a 16,02; igual ao Pocket |
| Teclas | Gateron magnéticas KS-20; encaixam sem solda; plate de FR-4 de 1,6 |
| Sensores | **TMAG5253BA3**, um por tecla, no verso, ligados por grupo; **Global Sourcing da JLCPCB**. Plano B desenhável: DRV5055 (LCSC C266131, mais consumo) |
| Processador | **módulo SparkFun MicroMod Teensy** (RT1062, 600 MHz, 16 MB de flash) num conector M.2 Key E de 4,2 mm, preso por parafuso M2.5 |
| Áudio | codec **SGTL5000** (fone); amplificador **MAX98357A** (I2S) junto do alto-falante; alto-falante fino Ø36 |
| Som | só acordeom (6 registros de fábrica + 2 presets livres), como no Pocket |
| Conexão | **USB-C** (carga, MIDI, gravação), 2 × 5,1 kΩ nos CC, ESD |
| Liga/desliga | **segurar o clique do volume (I1) por 2 s** liga e desliga, também com USB ligada; LED mostra cada operação; desligamento automático em dois estágios |
| Knobs | volume e seletor: o mesmo encoder EC11E vertical com clique (EC11E18244A5, 18/36, do passo 3.2). Clique do volume = liga/desliga; clique do seletor = funções de som |
| Bateria | LiPo 1S ~1000 mAh com NTC (3 fios), comprada à parte; **posição decidida no case** |
| Placa | **retângulo 246,5 × 95, cantos R 5, 4 camadas, 1,2 mm**; vias 0,5 / 0,3 |

## 2. Forma da placa e planta

Igual ao Viaggio v2.1, com o módulo no lugar do setor P antigo.

- **Retângulo** de x 2,5 a 249 e y 2,5 a 97,5 (y cresce em direção ao músico), cantos R 5.
- **Perfil A** pontilhado na serigrafia. **Todas as peças ficam dentro dele**, menos o USB-C (E1) e o fone (F2), que ficam na borda esquerda, no alto. A posição antiga de E1 e F2 fica tracejada.
- **Teclado**: as 28 teclas do Pocket, nas mesmas posições. **Limite da interface**: o espelho da borda direita do perfil A em torno do centro do teclado.
- **Furos M2**: os 8 do contrato, com anel livre de cobre de 3,5. A eletrônica pode pedir mais para cumprir a flexão.
- **Flexão no teclado** ≤ 0,05 mm a 3 N por tecla. A bateria não entra nessa conta.
- **Lado de cima**: E1 e F2 na borda esquerda; área do logo atrás; I1, I2 e I3 numa linha (y ≈ 49); alto-falante A2 na frente.
- **Lado de baixo**: todos os chips e o **módulo P1**, no canto de trás à esquerda (área x ≈ 26–48, y ≈ 3,5–30,5). A orientação do conector fica a critério da eletrônica, pela rota mais curta do USB e do I2S.
  - **Altura do módulo** abaixo da placa: ~6–7 mm (conector de 4,2 + módulo, conferir).
  - **Sob o módulo** só peças com até 1,9 mm de altura (regra da SparkFun para o conector de 4,2).
- I4 (Program) é alcançado por um furo no fundo do case.

## 3. Setores e peças

Três tipos de código, que não se misturam: **setor** = letra (P, E, F, I, A, T); **peça** = letra do setor + número; **corredor** = C1…C7. Posições em `concept/out/viaggio_micromod.json`.

| Setor | Peça | O quê | Código / origem | Encapsulamento | Lado |
|---|---|---|---|---|---|
| **P · Processador** | P1 | Conector M.2 Key E 4,2 mm + espaçador SMD M2.5 + parafuso; **módulo MicroMod Teensy** encaixado em casa | conector TE 2199230-4 ou equivalente na LCSC (conferir); módulo SparkFun DEV-16402 | M.2 SMD | baixo |
| **E · Energia** | E1 | USB-C 16 vias + 2 × 5,1 kΩ | C165948 (TYPE-C-31-M-12) | SMD + carcaça passante | cima |
| | E2 | ESD do USB | C7519 (USBLC6-2SC6) | SOT-23-6 | **cima** (v2.3) |
| | E3 | Carregador BQ24074 + trava liga/desliga | C54313 | QFN-16, 3 × 3 | baixo |
| | E4 | Conversor 3,3 V TPS63001 + indutor 2,2 µH | C28060 | VSON-10, 3 × 3 | baixo |
| | E6 | Conector da bateria JST PH 3 vias (+, −, NTC) | LCSC | SMD, ângulo reto | baixo |
| **F · Fone** | F1 | Codec SGTL5000 | C511764 | QFN-20, 3 × 3 | baixo |
| | F2 | Jack 3,5 com contato na ponta (PJ-327A, do passo 3.2) | LCSC | SMD, ângulo reto | cima |
| **I · Interface** | I1 | Volume: encoder EC11E com clique; **o clique liga/desliga** | LCSC | THT | cima |
| | I2 | Seletor: o mesmo encoder | LCSC | THT | cima |
| | I3 | LED bicolor sob light pipe | LCSC | 1615 | cima |
| | I4 | Botão Program (no BOOT do módulo) | C318884 (TS-1187A) | tátil SMD 5,1 × 5,1 | baixo |
| **A · Alto-falante** | A1 | Amplificador MAX98357A | C910544 | QFN-16, 3 × 3 | baixo |
| | A2 | Alto-falante fino Ø36 (~4,6) | a escolher (ex.: PUI AS03608MR) | fios soldados | (case) |
| **T · Teclas** | T1, T2 | Mux 74HC4067PW, esquerdo e direito | C547038 | TSSOP-24 | baixo |
| | T3 | Portas do liga/desliga dos sensores (74LVC1G04 + 2 × 1G08) | LCSC | SOT-23-5 | baixo |
| | T4 | 28 × TMAG5253BA3, um sob cada tecla | Global Sourcing | X2SON | baixo |

O código E5 deixa de existir. Fora da placa: módulo MicroMod Teensy, 28 Gateron KS-20, plate de FR-4, bateria, alto-falante, capas e case.

### Regras por bloco

- **P (módulo):**
  - **Alimentação:** o módulo recebe 3,3 V nos pads 2 e 74, vindos de E4. O USB_VIN (pad 9) vai no VBUS, para o módulo ver a USB. D+/D− (pads 3 e 5) vêm do E1 pelo E2.
  - **Gravação:** o BOOT (pad 11) vai ao botão I4.
  - **ONOFF:** o pad 6 ("RESET#") é o ONOFF do RT1062. Vai ao clique do volume por diodo e ao pad de teste TP101.
  - **Liga/desliga (v2.3):**
    - EN de E4 = clique do volume OU KEEP OU USB_HOLD;
    - USB_HOLD = VBUS E PWR_EN (pino 28 = pad 4, pull-up de 100 kΩ, 1 kΩ + 1 µF);
    - desligar com USB = firmware baixa o pino 28 e o KEEP.
  - **Botão preso 10 s** desliga o RT1062 pelo ONOFF (`BTN_PRESS_TIME`), mais o watchdog.
  - Seguir o guia "Designing with MicroMod" da SparkFun: comprimentos de D+/D− iguais e peças de até 1,9 mm sob o módulo.
- **E**:
  - BQ24074 com power-path, USB500, NTC no TS e carga de 500 mA. O STAT acende o vermelho do LED só com o aparelho desligado.
  - Liga/desliga pelo clique de **I1**: a firmware segura o EN (KEEP) e o solta no clique longo. USB presente mantém ligado, salvo pelo desligamento de verdade da regra P.
  - Medida da bateria por divisor de alta impedância.
- **F**: fone com terra virtual (HP_VGND), **nunca no GND**. O contato da ponta de F2 detecta o fone.
- **A**: A1 no mesmo I2S do F1, mono (L+R)/2. SD_MODE desliga A1 com fone plugado, em silêncio e no desligamento.
- **T**:
  - S3 escolhe os canais 0–7 ou 8–15; SENS_EN liga tudo; T3 faz as portas, como no Pocket.
  - Espera de 45 µs depois de trocar de grupo.
  - Mesma orientação dos sensores do Pocket.

## 4. Ligações, em ordem de prioridade

| Ordem | Tipo | Entre | Corredor | Requisito |
|---|---|---|---|---|
| 1º | USB de alta velocidade | E1 → E2 → P1 | C1 | D+ e D− com comprimentos até 2 mm diferentes, ≤ 40 mm, ≤ 2 vias em cada, GND contínuo por baixo |
| 2º | Fontes chaveadas | E3, E4 | — | indutor e capacitores colados ao chip, na mesma camada, várias vias ao GND; nada analógico por perto |
| 3º | Corrente | E1 → E3 → E4; E6 → E3; E3 → A1; E4 → P1 | C2, C6, C7 | até ~1,5 A: ≥ 0,8 mm, salvo a entrada dos pinos (afinamento de até 1,5 mm de comprimento) |
| 4º | Áudio analógico | F1 → F2; A1 → A2 | C4 | curtas; fone longe das fontes chaveadas; a saída de A1 é chaveada: par curto, longe do fone |
| 5º | Áudio digital | P1 → F1, A1 (I2S); P1 → F1 (I2C) | C5 | MCLK com resistor em série junto de P1; sempre sobre GND |
| 6º | Analógico das teclas | T4 → T1, T2 → P1 | C3 | as 2 saídas dos mux com GND dos dois lados, ≥ 10 mm do indutor de E4 |
| 7º | Digital das teclas | P1 → T1, T2, T3; T3 → T4 | C3 | lentos; cada grupo de 14 sensores puxa ~36 mA: ≥ 0,3 mm |
| 8º | Digital lento | I1–I4, estado de E3, bateria, detecção do fone → P1 | — | qualquer rota livre, 0,2 mm (0,15 na entrada de pinos finos) |

## 5. Corredores e camadas

| Corredor | Leva | De → para | Linhas | Camada | Comprimento |
|---|---|---|---|---|---|
| C1 | USB D+ / D− | E1 → E2 → P1 | 2 | cima (F.Cu sobre o In1); par de vias colado ao J101 | ~25 |
| C2 | 5 V do USB, pela borda de trás | E1 → E3 | 1 larga | 3 | ~60 |
| C3 | 2 saídas analógicas, S0–S3, SENS_EN | T1, T2, T3 → P1 | 7 + GND | baixo | ~160 |
| C4 | esquerdo, direito, terra virtual, detecção | F1 → F2 | 4 | baixo | ~15 |
| C5 | I2S e SD_MODE | P1 → A1 | 4 | baixo | ~70 |
| C6 | alimentação de A1 | E3 → A1 | 1 larga | 3 | ~70 |
| C7 | bateria e NTC | E6 → E3 | 2 | baixo | ~5 |

- **C3** passa atrás da fileira 4 e por baixo do setor E, a **≥ 10 mm do indutor de E4**.
- **Camadas** (empilhamento JLC04121H-7628, 1,2 mm):
  - 1 = cima (knobs, conectores);
  - 2 = GND inteiro, **sem cortes** (tipo power no KiCad);
  - 3 = **trilhas** (tipo signal no KiCad); depois do roteamento, áreas de GND e 3,3 V no espaço livre;
  - 4 = baixo (chips, módulo, rota principal).
- **Vias 0,5 / furo 0,3** em todas as classes.

## 6. Case (etapa 4, depois da placa)

- Segue a placa. A forma externa pode seguir o perfil A ou o retângulo; decide-se na etapa 4.
- Furos para I1, I2, I3; grade sobre A2; E1 e F2 na parede esquerda; furo para I4 no fundo.
- **Módulo P1** embaixo, com ~6–7 mm: o fundo do case tem de abrir espaço para ele, e para tirá-lo se precisar trocar.
- **Bateria**: posição decidida aqui (embaixo, em cima ou à esquerda da placa).
- Apoios do teclado para a flexão de 0,05 mm.

## 7. Plano (um passo = uma sessão curta do Code = um PR)

O J manda um prompt por passo e aprova o resultado antes do seguinte. **Nenhum passo do Code roteia.**

- **M1 · Esquema** (feito, PR #117): pasta nova, esquema adaptado ao módulo, ERC, mapa de pinos, BOM preliminar.
- **M2 · Placa para rotear** (agora): contorno, serigrafia, regras corrigidas, empilhamento, posicionamento pelo `viaggio_micromod.json`, In2 como signal, DSN. Sem trilhas.
- **Roteamento pelo J**, no KiCad com o Freerouting, pelo guia "Viaggio: roteamento no KiCad, passo a passo".
- **M3 · Conferência e fabricação:**
  - áreas de GND e 3,3 V no In2;
  - DRC 0/0/0 e conferência placa × firmware 28/28;
  - flexão;
  - Gerbers, BOM e CPL da JLCPCB;
  - `POWER.md`, alturas por lado e relatório.

## Tarefas para o Code (v2.3): só o passo M2

O M1 foi feito no PR #117. **Agora: a placa posicionada para o J rotear.** Sem trilhas, sem vias e sem roteador. Pare ao fim do M2, faça um PR e informe o J.

### Eletrônica: M2a, ajustes do esquema (v2.3)

- E2 no lado de cima.
- J101: o M.2 Key E 4,2 mm com estoque na JLCPCB (conferir na página da peça), com o footprint pelo desenho dela.
- H101: Würth 9774025151R por Global Sourcing, ou equivalente LCSC registrado.
- ERC 0/0, conferência da netlist, `bom_preliminar.csv` e `PINOS.md` atualizados se algo mudar.

### Eletrônica: M2b, a placa

- **Scripts:** `build_board.py` e `handoff_freerouting.py` adaptados de `viaggio/pcb/`, **sem `router.py` e sem nenhum roteamento**.
- **Contorno, furos M2 e serigrafia** como no Viaggio v2.1:
  - perfil A pontilhado;
  - posição antiga de E1/F2 tracejada;
  - área do logo;
  - códigos P1…T4.
- **Posicionamento de todas as peças** por `concept/out/viaggio_micromod.json`, com os passivos junto dos seus chips.
  - J101 e o cartão de 22 × 22 no verso, na área do setor P, com a orientação que der o USB e o I2S mais curtos.
  - Área de regra sobre o retângulo do cartão: **peças de até 1,9 mm** embaixo dele.
  - Ajustes de alguns milímetros são livres; mudança de setor, lado ou corredor é pedida no relatório.
- **Empilhamento e camadas** (§5):
  - JLC04121H-7628;
  - In1 = GND, tipo power, área de GND inteira;
  - **In2 = tipo signal, sem nenhuma área** (as áreas do In2 entram no M3);
  - F.Cu e B.Cu como no v2.1.
- **Classes e vias:** **0,5 / 0,3 em todas as classes**. USB 0,24 / vão 0,15 em F.Cu sobre o In1 (registrar a conta se mudar).
- **Regras do `.kicad_dru`**, que o KiCad 10 tem de compilar sem erro:
  - números **com unidade (mm)**;
  - nada de nome de classe "Default" (usar "não é USB, Corrente nem Nucleo");
  - sinais com mínimo de 0,15 mm, para as afinações na entrada de pinos finos;
  - Corrente com mínimo de 0,8 mm, exceto dentro do pátio dos chips de energia e dos conectores (E1, E3, E4, E6, A1, J101), onde as afinações na entrada dos pinos são normais.
- **Saídas:**
  - `build/viaggio_micromod.dsn`;
  - imagens do lado de cima e do lado de baixo;
  - DRC da entrega: 0 erros, paridade com o esquema 0, número de ligações a rotear.
- **`pcb/ROTEAMENTO.md` curto:** os arquivos, as camadas, as classes e "não rode o `build_board.py` sobre a placa que o J rotear". O passo a passo fica no guia do J.

### Relatório

`viaggio_micromod/ELETRONICA.md`: o que foi feito, o conector escolhido (código, estoque, desenho), onde as peças saíram do JSON e por quê, itens (conferir) e "Perguntas para a gestão".

## 8. Perguntas para o J

1. **Comprar um módulo MicroMod Teensy agora** (~US$ 25, mais o kit de parafusos da SparkFun)? Não é o protótipo. Serve para medir a altura real e a posição do espaçador antes de mandar fazer a placa (itens 3 e 4 do relatório do M1). O M2 não depende disso.
