# eTutti Viaggio · especificação · v2.1 (Rev2)

**Versão 2.1, 24 out 2026** (v2 do mesmo dia + respostas do J ao relatório do passo 3.1). Mantida pela gestão (Claude Chat com o J); o Code não edita este arquivo. Mesmo protocolo do eTuttino Pocket (`CLAUDE.md`, seção "como trabalhamos"). Cada disciplina responde no seu relatório, terminando com "Perguntas para a gestão".

A v1 levou a sessões longas demais. A **Rev2** recomeça a placa em passos curtos, com aprovação do J entre eles:

1. planta 2D e requisitos das peças (feita);
2. setores, tipos de ligação e corredores (feita);
3. roteamento pelo Code, em quatro passos de uma sessão cada (§7);
4. case.

Medidas em mm. **(conferir)** = estimativa a confirmar com a peça real ou o datasheet.

## Mudanças desde a versão anterior

### v2.1 (respostas ao `ELETRONICA.md` do passo 3.1)

- **O liga/desliga passa para o clique do volume (I1).** Segurar 2 s liga; com o aparelho ligado, segurar 2 s desliga. O LED mostra cada operação; um aviso sonoro para os dois vem depois, na programação. O clique do seletor (I2) fica só para as funções de som.
- **Desligar com USB ligada desliga de verdade** (pergunta 1): a firmware pede o desligamento do SNVS, que baixa o PMIC_ON_REQ. O clique de 2 s religa pelo ONOFF. Sem isso, a luz de carga (só com o aparelho desligado) nunca apareceria com USB.
- **ONOFF preso desliga tudo depois de 10 s** (pergunta 2), não 5 s: a firmware grava `BTN_PRESS_TIME` = 10 s no `SNVS_LPCR` na partida. É a proteção contra firmware travada.
- **Cristal de 32,768 kHz em 3215 e botão Program de 5,1 × 5,1** (pergunta 3): aceitos.
- **Encoders** (pergunta 4): o mesmo modelo nos dois, de preferência o EC11E 15 pulsos / 15 detentes do Pocket. Se ele não estiver no estoque da JLCPCB, usar o EC11E com clique que estiver (ex.: 18/36, C255515), igual nos dois; a firmware se ajusta.
- **Flash "-M"** (pergunta 5): W25Q64JVSSIM, que a página da PJRC aceita em qualquer versão do bootloader. Precisamos de ~5.
- **Recuperação de firmware ruim** (para o manual): com USB ligada, segurar o clique do volume (liga o 3,3 V) e apertar o Program; ao soltar o clique, a USB mantém a placa ligada no bootloader.

### v2 (Rev2)

- **Placa retangular** de 246,5 × 95 com cantos R 5. A JLCPCB não cobra pelo formato do contorno numa placa desse tamanho. O contorno curvo da v1 (perfil A) fica pontilhado na serigrafia, como referência: as peças ficam dentro dele.
- **USB-C e fone na borda esquerda do retângulo, no alto**, com a boca para fora, para o case usar direto. A posição da v1 fica tracejada na serigrafia.
- **Processador: RT1062 em BGA 12 × 12 de passo 0,8** (MIMXRT1062DVJ6B), comprado na PJRC ou na DigiKey e consignado junto com o MKL02. O passo 0,65 da v1 pediria furos de 0,15 mm, que a JLCPCB cobra à parte.
- **PSRAM: só o lugar**, para modelos futuros. Encapsulamento USON-8, o que a LCSC tem (C3040877). Quando entrar, a JLC monta; não é peça para solda em casa.
- **Volume: encoder EC11E com clique**, o mesmo do seletor. Sai o potenciômetro.
- **Bateria fora da placa e sem lugar definido.** A posição dela (embaixo, em cima ou à esquerda da placa) é decidida por último, no case. Na placa só ficam o conector, ao lado do carregador, e o limite de flexão do teclado.
- **Peças codificadas por setor** (§3), com a ordem de roteamento (§4) e os corredores (§5).
- O contrato de posicionamento passa a ser `concept/rev2/out/viaggio_rev2.json`.

## 0. O que é o Viaggio

Um eTutti fino e alongado, com **toda a eletrônica numa placa só, montada pela JLCPCB**. Em casa, só se encaixam as teclas, ligam-se a bateria e o alto-falante e grava-se a firmware pela USB.

- **Prioridade: o detalhamento da placa.** O case vem depois e segue a placa.
- Base: o teclado e o lado direito do eTuttino Pocket (SPEC v5); o lado esquerdo foi refeito.
- **Nada é encomendado** até o J decidir passar para essa fase.

## 1. Decisões (confirmadas pelo J)

| Tema | Decisão |
|---|---|
| Teclado | 28 botões C-griff, G3–E5, grade hexagonal de 18,5, fileiras a 16,02; igual ao Pocket |
| Teclas | Gateron magnéticas KS-20; encaixam sem solda; plate de FR-4 de 1,6 |
| Sensores | **TMAG5253BA3**, um por tecla, no verso, ligados por grupo; **Global Sourcing da JLCPCB**. Plano B desenhável: DRV5055 (LCSC C266131, mais consumo) |
| Processador | **"Teensy 4.1 na placa"**: RT1062 DVJ6B (BGA 12 × 12, passo 0,8) + bootloader PJRC MKL02 + flash de 64 Mbit + lugar para PSRAM (sem montar) + cristais. Compila como `teensy:avr:teensy41` |
| Áudio | codec **SGTL5000** (fone); amplificador **MAX98357A** (I2S) junto do alto-falante; alto-falante fino Ø36 |
| Som | só acordeom (6 registros de fábrica + 2 presets livres), como no Pocket |
| Conexão | **USB-C** (carga, MIDI, gravação), 2 × 5,1 kΩ nos CC, ESD |
| Liga/desliga | **segurar o clique do volume (I1) por 2 s** liga e desliga, também com USB ligada (desligamento do SNVS); LED mostra cada operação; ONOFF preso 10 s desliga tudo; desligamento automático em dois estágios |
| Knobs | **volume e seletor: o mesmo encoder EC11E vertical com clique**. Clique do volume = liga/desliga (2 s); clique do seletor = funções de som |
| Bateria | LiPo 1S ~1000 mAh com NTC (3 fios), comprada à parte; **posição decidida no case** |
| Placa | **retângulo 246,5 × 95, cantos R 5, 4 camadas, 1,2 mm** |

## 2. Forma da placa e planta

- **Retângulo** de x 2,5 a 249 e y 2,5 a 97,5 (y cresce em direção ao músico), cantos R 5.
- **Perfil A**: o contorno da v1 (`pocket.json` → `inner`), pontilhado na serigrafia. **Todas as peças ficam dentro dele**, menos o USB-C (E1) e o fone (F2).
- **Posição antiga de E1 e F2** (v1): tracejada na serigrafia, como referência.
- **Teclado**: as 28 teclas do Pocket, nas mesmas posições.
- **Limite da interface**: o espelho da borda direita do perfil A em torno do centro do teclado.
- **Furos M2**: 4 na interface e 4 em centros de triângulos de teclas (`viaggio_rev2.json` → `holes_m2`). Anel livre de cobre de 3,5. A eletrônica pode pedir mais para cumprir a flexão.
- **Flexão no teclado**: ≤ 0,05 mm a 3 N por tecla, sobre os apoios do case, como no Pocket. A bateria não entra nessa conta.
- **Lado de cima** (interface): E1 e F2 na borda esquerda; área do logo atrás; I1, I2 e I3 numa linha (y ≈ 49); alto-falante A2 na frente.
- **Lado de baixo**: todos os chips. I4 (Program) é alcançado por um furo no fundo do case.

## 3. Setores e peças

Três tipos de código, que não se misturam: **setor** = letra (P, E, F, I, A, T); **peça** = letra do setor + número; **corredor** = C1…C7. Posições em `concept/rev2/out/viaggio_rev2.json`.

| Setor | Peça | O quê | Código / origem | Encapsulamento | Lado |
|---|---|---|---|---|---|
| **P · Processador** | P1 | i.MX RT1062 MIMXRT1062DVJ6B | PJRC ou DigiKey, consignado | LFBGA-196, 12 × 12, passo 0,8 | baixo |
| | P2 | Bootloader PJRC MKL02 | PJRC, consignado | QFN-16 | baixo |
| | P3 | Flash 64 Mbit **W25Q64JVSSIM** ("-M") | LCSC (conferir código) | SOIC-8 208 mil | baixo |
| | P4 | PSRAM APS6404L, **sem montar** | C3040877 (futuro) | USON-8, 2 × 3 | baixo |
| | P5 | Cristais 24 MHz e 32,768 kHz | C431156 / C32346 | 3225 / 3215 | baixo |
| **E · Energia** | E1 | USB-C 16 vias + 2 × 5,1 kΩ | C165948 (TYPE-C-31-M-12) | SMD + carcaça passante | cima |
| | E2 | ESD do USB | C7519 (USBLC6-2SC6) | SOT-23-6 | baixo |
| | E3 | Carregador BQ24074 + trava liga/desliga | C54313 | QFN-16, 3 × 3 | baixo |
| | E4 | Conversor 3,3 V TPS63001 + indutor 2,2 µH | C28060 | VSON-10, 3 × 3 | baixo |
| | E5 | Regulador do SNVS e partida do P1 | LCSC | SOT-23 / SC-70 | baixo |
| | E6 | Conector da bateria JST PH 3 vias (+, −, NTC) | LCSC | SMD, ângulo reto | baixo |
| **F · Fone** | F1 | Codec SGTL5000 | C511764 | QFN-20, 3 × 3 | baixo |
| | F2 | Jack 3,5 com contato na ponta | LCSC (conferir) | SMD, ângulo reto | cima |
| **I · Interface** | I1 | Volume: encoder EC11E vertical com clique; **o clique liga/desliga** | LCSC (conferir) | THT | cima |
| | I2 | Seletor: o mesmo encoder | LCSC (conferir) | THT | cima |
| | I3 | LED bicolor sob light pipe | LCSC | 1615 ou 2020 | cima |
| | I4 | Botão Program | C318884 (TS-1187A) | tátil SMD 5,1 × 5,1 | baixo |
| **A · Alto-falante** | A1 | Amplificador MAX98357A | LCSC (conferir) | QFN-16, 3 × 3 | baixo |
| | A2 | Alto-falante fino Ø36 (~4,6) | a escolher (ex.: PUI AS03608MR) | fios soldados | (case) |
| **T · Teclas** | T1, T2 | Mux CD74HC4067, esquerdo e direito | LCSC | TSSOP-24 | baixo |
| | T3 | Portas do liga/desliga dos sensores (74LVC1G04 + 2 × 1G08) | LCSC | SOT-23-5 | baixo |
| | T4 | 28 × TMAG5253BA3, um sob cada tecla | Global Sourcing | X2SON | baixo |

Fora da placa: 28 Gateron KS-20, plate de FR-4, bateria, alto-falante, capas e case.

### Regras por bloco (como na v1, ainda valem)

- **P**: seguir à risca o esquema do Teensy 4.1 (sem Ethernet, USB host nem cartão SD) e a página do bootloader da PJRC:
  - o SNVS liga antes dos outros reguladores;
  - PMIC_ON_REQ;
  - DCDC_PSWITCH sobe depois de o 3,3 V estabilizar, sem RC;
  - PTA3 → DCDC_PSWITCH e PTB5 → AD_B0_08.

  **Nunca ativar o modo seguro.** Numeração de pinos do Teensy 4.1. Os pinos 48–54 ficam para a PSRAM.
- **E**:
  - BQ24074 com power-path, USB500, NTC no TS e carga de 500 mA. O STAT acende o vermelho do LED só com o aparelho desligado.
  - Liga/desliga: o clique de **I1** liga o EN de E4 por um diodo e vai ao ONOFF do SNVS. A firmware segura o EN (KEEP) e o solta no clique longo. USB presente mantém ligado; para desligar com USB, a firmware desliga o SNVS. ONOFF preso 10 s desliga tudo.
  - Medida da bateria por divisor de alta impedância.
- **F**: fone com terra virtual (HP_VGND), **nunca no GND**. O contato da ponta de F2 detecta o fone.
- **A**: A1 no mesmo I2S do F1, mono (L+R)/2. SD_MODE desliga A1 com fone plugado, em silêncio e no desligamento.
- **T**:
  - S3 escolhe os canais 0–7 ou 8–15; SENS_EN liga tudo; T3 faz as portas, como no Pocket.
  - Espera de 45 µs depois de trocar de grupo.
  - Mesma orientação dos sensores do Pocket.

## 4. Ligações, na ordem em que o Code roteia

| Ordem | Tipo | Entre | Corredor | Requisito |
|---|---|---|---|---|
| 1º | Relógios | P5 → P1 | — | ≤ 5 mm, GND em volta, nada passando por baixo em nenhuma camada |
| 2º | Saída do processador | 196 bolas de P1 + capacitores | — | primeiro a rotear depois dos relógios; capacitores no lado de cima, logo acima do BGA |
| 3º | USB de alta velocidade | E1 → E2 → P1 | C1 | par diferencial de 90 Ω, ≤ 40 mm, no máximo um par de vias, GND contínuo por baixo |
| 4º | Memórias | P1 → P3, P4 | — | até 133 MHz: ≤ 15 mm, comprimentos parecidos (± 2 mm), sem vias se der |
| 5º | Fontes chaveadas | E3, E4, conversor interno de P1 | — | indutor e capacitores colados ao chip, na mesma camada, várias vias ao GND; nada analógico por perto |
| 6º | Corrente | E1 → E3 → E4; E6 → E3; E3 → A1 | C2, C6, C7 | até ~1,5 A: ≥ 0,8 mm ou áreas de cobre na camada 3 |
| 7º | Áudio analógico | F1 → F2; A1 → A2 | C4 | curtas; fone longe das fontes chaveadas; a saída de A1 é chaveada: par curto, longe do fone |
| 8º | Áudio digital | P1 → F1, A1 (I2S); P1 → F1 (I2C) | C5 | MCLK (11,3 MHz) com resistor em série junto de P1; sempre sobre GND |
| 9º | Analógico das teclas | T4 → T1, T2 → P1 | C3 | as 2 saídas dos mux com GND dos dois lados, ≥ 10 mm do indutor de E4 |
| 10º | Digital das teclas | P1 → T1, T2, T3; T3 → T4 | C3 | lentos; cada grupo de 14 sensores puxa ~36 mA: ≥ 0,3 mm |
| 11º | Digital lento | I1–I4, estado de E3, bateria, detecção do fone → P1 | — | qualquer rota livre, 0,2 mm |

## 5. Corredores e camadas

| Corredor | Leva | De → para | Linhas | Camada | Comprimento |
|---|---|---|---|---|---|
| C1 | USB D+ / D− | E1 → P1 | 2 | cima, desce perto do BGA | ~15 |
| C2 | 5 V do USB, pela borda de trás | E1 → E3 | 1 larga | 3 | ~60 |
| C3 | 2 saídas analógicas, S0–S3, SENS_EN | T1, T2, T3 → P1 | 7 + GND | baixo | ~160 |
| C4 | esquerdo, direito, terra virtual, detecção | F1 → F2 | 4 | baixo | ~15 |
| C5 | I2S e SD_MODE | P1 → A1 | 4 | baixo | ~70 |
| C6 | alimentação de A1 | E3 → A1 | 1 larga | 3 | ~70 |
| C7 | bateria e NTC | E6 → E3 | 2 | baixo | ~5 |

- **C3** passa atrás da fileira 4 e por baixo do setor E, a **≥ 10 mm do indutor de E4**.
- **Camadas**:
  - 1 = cima (knobs, conectores, capacitores de P1);
  - 2 = GND inteiro, **sem cortes**;
  - 3 = GND com ilhas de energia (VBUS, SYS, 3V3);
  - 4 = baixo (quase todos os chips, rota principal).
- **Empilhamento padrão de 4 camadas e 1,2 mm da JLCPCB** (conferir o nome); os 90 Ω do C1 são calculados nele.

## 6. Case (etapa 4, depois da placa)

- Segue a placa. A forma externa pode seguir o perfil A ou o retângulo; decide-se na etapa 4.
- Furos para I1, I2, I3; grade sobre A2; E1 e F2 na parede esquerda; furo para I4 no fundo.
- **Bateria**: posição decidida aqui (embaixo, em cima ou à esquerda da placa).
- Apoios do teclado para a flexão de 0,05 mm.

## 7. Plano da etapa 3 (um passo = uma sessão do Code = um PR)

O J manda um prompt por passo e aprova o resultado antes do seguinte.

- **3.1 Esquema** (feito, PR #113): esquema elétrico completo, ERC, BOM preliminar, mapa de pinos. Sem placa.
- **3.2 Placa e setor P** (agora):
  - contorno, furos, serigrafia (perfil A, posições antigas de E1/F2);
  - empilhamento e regras (classes de ligação da §4);
  - posicionamento de todas as peças pelo `viaggio_rev2.json`;
  - roteamento do setor P: relógios, saída do BGA, C1, memórias.
- **3.3 Setores E, F, A, I**: fontes, corrente (C2, C6, C7), áudio (C4, C5), interface.
- **3.4 Setor T e fechamento**:
  - sensores e C3;
  - DRC 0/0/0, conferência placa × firmware 28/28, flexão;
  - Gerbers, BOM e CPL da JLCPCB, `POWER.md`, alturas por lado, relatório.

## Tarefas para o Code (v2.1): só o passo 3.2

O passo 3.1 foi feito no PR #113. **Agora: placa, regras, posicionamento e roteamento só do setor P.** Não rotear os setores E, F, A, I e T (ficam no ratsnest). Pare ao fim do passo 3.2, faça um PR e informe o J.

### Eletrônica: VE2a, ajustes do esquema (v2.1)

- Liga/desliga no clique de **I1** (VOL_SW): Q203, o diodo do EN e o diodo do ONOFF passam do clique do seletor para o do volume. O pino 6 (SEL_SW) fica uma entrada comum.
- `PINOS.md`: atualizar os pinos 6 e 25 e a seção "Como cada sinal novo se comporta" (liga/desliga no volume, desligamento do SNVS com USB, `BTN_PRESS_TIME` = 10 s, recuperação com Program).
- P3 = W25Q64JVSSIM; P5 32 kHz em 3215; I4 TS-1187A; encoders conforme a v2.1. Atualizar o `bom_preliminar.csv`.
- ERC 0/0 e a conferência da netlist de novo.

### Eletrônica: VE2b, footprints que faltam

- **P1**: LFBGA-196 12 × 12, passo 0,8, a partir do desenho da NXP (figura 54 do datasheet), bolas conferidas com `rt1062_balls.json`.
- **F2** (PJ-313D-6A) e **I3** (LED 1615 de 4 pads), com a pinagem conferida no datasheet.
- Footprints próprios numa biblioteca do Viaggio (`pcb/kicad/viaggio.pretty/`). O switch Gateron vem do Pocket/eTuttino.

### Eletrônica: VE2c, placa e regras

- **Contorno**: retângulo da §2 com cantos R 5; furos M2 de `viaggio_rev2.json` com anel livre de 3,5.
- **Serigrafia**: perfil A pontilhado; posição antiga de E1 e F2 tracejada; área do logo; códigos P1…T4 ao lado das peças (lado de baixo espelhado).
- **Empilhamento**: o padrão de 4 camadas e 1,2 mm da JLCPCB (registrar o nome). Camadas como na §5.
- **Regras** (classes de ligação da §4):
  - USB 90 Ω diferencial, largura e espaçamento calculados no empilhamento escolhido (registrar a conta);
  - corrente ≥ 0,8 mm; sinais 0,2 mm; GND/energia por áreas;
  - vias só nos tamanhos que a JLCPCB faz sem custo extra (registrar o mínimo usado); a saída do BGA de 0,8 com via entre bolas (dog-bone), sem via no pad.
- **Posicionamento de todas as peças** pelo `viaggio_rev2.json`, com os passivos junto dos seus chips; T4 sob as teclas, na orientação do Pocket. Ajustes de alguns milímetros são livres; mudança de setor, lado ou corredor é pedida no relatório.

### Eletrônica: VE2d, roteamento do setor P

- Na ordem da §4: relógios (1º), saída do BGA e capacitores (2º), USB C1 (3º), memórias P3/P4 (4º), conversor interno de P1 (parte do 5º), MCLK com o resistor junto de P1.
- GND contínuo sob o USB e sob as memórias.
- **Conferência**: DRC sem nenhum erro de folga, curto ou regra; só podem sobrar ligações não roteadas fora do setor P (listar a contagem por setor).
- **Imagens para revisão**: PNG ou SVG do lado de cima, do lado de baixo e do setor P ampliado (camadas 1 e 4 e as áreas internas), em `pcb/build/`.

### Relatório

`viaggio/ELETRONICA.md`: o que foi feito, empilhamento e conta dos 90 Ω, tamanhos de via, onde as peças saíram do `viaggio_rev2.json` e por quê, itens (conferir) e "Perguntas para a gestão".

## 8. Perguntas para o J

Nenhuma em aberto.
