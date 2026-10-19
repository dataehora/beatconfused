# eTutti Viaggio · especificação · v1

**Versão 1 — 19 out 2026 (revista no mesmo dia: base Teensy 4.1).** Primeira SPEC do eTutti Viaggio (antes chamado "Pocket Slim"). Mantida pela gestão (Claude Chat com o J); o Code não edita este arquivo. Mesmo protocolo do eTuttino Pocket (`CLAUDE.md`, seção "como trabalhamos"): cada disciplina responde no seu relatório, terminando com "Perguntas para a gestão".

Medidas em mm. **(conferir)** = estimativa a confirmar com a peça real ou o datasheet.

## 0. O que é o Viaggio

Um eTutti fino e alongado, com **toda a eletrônica numa placa só, montada pela JLCPCB**. Em casa, só se encaixam as teclas, ligam-se a bateria e o alto-falante e grava-se a firmware pela USB.

- **Prioridade desta versão: o detalhamento da placa.** O case é só conceitual e acompanha o que a eletrônica precisar; pode mudar depois.
- As expectativas de altura, chanfros e case do eTuttino e do Pocket **não valem** aqui.
- Base: o teclado e o lado direito do eTuttino Pocket (SPEC v5); o lado esquerdo foi refeito.
- Layout conceitual: `concept/layout_concept.py` → `concept/out/viaggio_concept.json`. É uma primeira impressão para a eletrônica, não um contrato.

## 1. Decisões (todas confirmadas pelo J em 19 out 2026)

| Tema | Decisão |
|---|---|
| Teclado | 28 botões C-griff, G3–E5, grade hexagonal de 18,5, fileiras a 16,02; igual ao Pocket |
| Teclas | Gateron magnéticas KS-20 (perfil confirmado pelo J); encaixam sem solda |
| Sensores | **TMAG5253BA3**, um por tecla, no verso, ligados por grupo (EN); comprados pelo **Global Sourcing da JLCPCB** e montados por ela. Plano B desenhável: DRV5055 (estoque LCSC, ~3 h de autonomia) |
| Processador | **"Teensy 4.1 montado na placa"** (decisão do J): i.MX RT1062 + bootloader PJRC MKL02 + **flash de 64 Mbit** + lugar para **PSRAM** (não montada) + cristal de 24 MHz. Firmware, Teensyduino e biblioteca de áudio sem mudança; compila como Teensy 4.1 |
| Áudio | codec **SGTL5000** (fone); amplificador **MAX98357A** (I2S, digital) para o alto-falante; alto-falante **fino** (~4,5 mm) |
| Som | só acordeom (6 registros de fábrica + 2 presets livres), como no Pocket |
| Conexão | **USB-C** na borda (carga, MIDI, gravação), com 2 × 5,1 kΩ nos CC e ESD |
| Bateria | LiPo 1S **~1000 mAh, ~4 mm de espessura** (formato tipo 405060, conferir), com NTC (3 fios); comprada à parte |
| Liga/desliga | **segurar o clique do seletor por 2 s** (liga e desliga); volume vira potenciômetro comum |
| Placa | 4 camadas (obrigatório pelo BGA), espessura a definir pela eletrônica (o Pocket usa 1,2 pela distância ímã–sensor) |

## 2. Forma da placa

- Contorno = o de dentro da parede do case do Pocket (`pocket.json` → `inner`), ~246,5 × 95.
- **Área do teclado**: as 28 teclas do Pocket, nas mesmas posições.
- **Limite da interface** (pedido do J): é o espelho da borda direita da placa em torno do centro do teclado. O teclado tem a mesma folga dos dois lados (~22,8 da borda da tecla), e a interface ganha os cantos de trás e da frente.
- **Interface, lado de cima**, de trás para a frente: área do logo; volume, seletor e LED numa linha (y ≈ 49); alto-falante na frente.
- **Borda curva da esquerda**: USB-C (y ≈ 22) e fone (y ≈ 35), cada um num trecho reto da borda.
- **Lado de baixo da interface**: processador, flash e bootloader perto do USB-C; codec perto do fone; energia no canto de trás; amplificador e conector da bateria no canto da frente.
- **Botão de gravação** (Program) no lado de baixo, alcançável por um furo no fundo do case.
- Furos de fixação M2: na interface e nos centros de triângulos de teclas.

## 3. Arquitetura elétrica

### Processador ("Teensy 4.1" na placa)

- **i.MX RT1062** (MIMXRT1062DVL6B, LCSC C2847497, MAPBGA-196 10 × 10, passo 0,65). A eletrônica avalia a versão de 12 × 12 com passo 0,8 (vendida pela PJRC) se o passo 0,65 exigir via-in-pad ou regras caras na JLCPCB.
- **Bootloader PJRC MKL02** (US$ 6,25, só na PJRC): comprado e enviado à JLCPCB (consignado).
- **Flash de 64 Mbit (8 MB)** suportada pelo bootloader v1.09 (conferir a lista da PJRC; ex.: W25Q64JV-IQ/-IM, mesmo encapsulamento da de 16 Mbit). A capacidade define o modelo: com 64 Mbit o bootloader se identifica como **Teensy 4.1**.
- **PSRAM opcional** (8 MB, QSPI, tipo APS6404L-3SQR ou ESP-PSRAM64H, como no Teensy 4.1) ligada ao FlexSPI2 como no esquema do Teensy 4.1. **O lugar fica na placa, sem montar**: só entra quando um preset de amostras (ex.: piano, acordeom gravado) precisar. Conferir o consumo dela em repouso para o orçamento.
- **Por que 4.1 e não 4.0**: o processador, a RAM interna e a velocidade são os mesmos (sem ganho de resposta nem de som hoje). A flash maior e a PSRAM são espaço para sons com amostras no futuro, por centavos.
- **Cristal de 24 MHz** com os capacitores e o resistor do guia da NXP. O de 32,768 kHz é opcional (sem relógio, pode sair).
- **Seguir à risca o esquema do Teensy 4.1 e a página do bootloader da PJRC:**
  - o SNVS liga antes dos outros reguladores internos;
  - PMIC_ON_REQ;
  - transição baixo → alto do DCDC_PSWITCH depois de o 3,3 V estabilizar, sem RC;
  - ligações do MKL02, incluindo PTA3 → DCDC_PSWITCH e PTB5 → AD_B0_08.
- **Numeração de pinos igual à do Teensy 4.1** (0–54): cada função vai a um pino que tenha número no Teensy 4.1. A firmware usa `digitalRead(n)` e afins como hoje. Os pinos 48–54 (PSRAM/flash extra) ficam reservados para a PSRAM; o Ethernet e o USB host do Teensy 4.1 não são usados.
- **Nunca ativar o modo seguro** (travamento é irreversível). Registrar no manual.

### Teclas

- 28 TMAG5253BA3 no verso, sob cada switch, mesma orientação do Pocket.
- 2 × CD74HC4067 (TSSOP-24) atrás da fileira 4.
- EN por grupo (S3 escolhe canais 0–7 ou 8–15; SENS_EN geral), com as portas lógicas do Pocket.
- Espera de 45 µs depois de trocar de grupo.
- Rigidez da placa sobre os apoios ≤ 0,05 mm a 3 N (como no Pocket).

### Áudio

- **SGTL5000** (LCSC C511764): saída de fone com terra virtual (HP_VGND) no jack, nunca no GND.
- **Jack 3,5** na borda, com contato de comutação na ponta para detectar o fone. Plugar o fone desliga o alto-falante.
- **MAX98357A** (conferir estoque na LCSC) no mesmo barramento I2S, mono (L+R)/2. O pino SD_MODE desliga o amplificador com o fone plugado, em silêncio e no desligamento.
- **Alto-falante fino**: Ø36 × ~4,6 (tipo PUI AS03608MR) ou módulo com caixa embutida. A eletrônica escolhe pela qualidade, e o design reserva a caixa traseira possível. Ligação por terminais na placa (ou montagem da JLC, se houver modelo com pinos).

### Energia

- **USB-C** (ex.: TYPE-C-31-M-12, LCSC C165948), pernas da carcaça passantes, 2 × 5,1 kΩ nos CC, ESD em D+, D− e VBUS.
- **Carregador BQ24074** (C54313): power-path, USB500, NTC no TS, carga de 500 mA. Luz de carga: o STAT acende o vermelho do LED só com o aparelho desligado.
- **Buck-boost TPS63001** (C28060), 3,3 V.
- **Liga/desliga eletrônico** (decisão do J):
  - segurar o clique do seletor por 2 s liga o conversor (o botão liga o EN por um diodo);
  - a firmware segura o EN pelo KEEP;
  - para desligar, a firmware lê o clique longo e solta o KEEP;
  - o clique curto continua sendo lido normalmente;
  - com USB presente, o conversor fica ligado (para gravar e testar);
  - desligamento automático em dois estágios, como no Pocket.
- **Medida da bateria** por divisor de alta impedância.
- **Bateria** ~1000 mAh, ~4 mm, 3 fios com NTC, em conector JST PH 3 vias na placa. Fica sob o teclado, no case, isolada da placa.

### Interface

- Volume: potenciômetro de 9 mm vertical **sem chave**, eixo para cima (tipo RK09K ou equivalente na LCSC).
- Seletor: encoder EC11E vertical com clique.
- LED bicolor (SMD sob um light pipe, ou 3 mm).
- Botão de gravação (tátil SMD) no verso.

### Orçamento de energia (referência do Pocket, a refazer pela eletrônica)

~6,7 h com fone e ~4,5 h com alto-falante (típicos), com TMAG5253 por grupo e 396 MHz. O MAX98357A e o processador na placa mudam um pouco os números.

## 4. Case conceitual (só para orientar a placa)

- Casca fina em duas partes (tampa e fundo), seguindo o contorno da placa com uma parede de ~2,5.
- Empilhamento de referência, de baixo para cima:
  - fundo;
  - bateria de ~4;
  - placa;
  - switch abaixo do plate (~3,5);
  - plate de 1,6;
  - switch acima do plate e capas.

  A eletrônica informa a altura máxima das peças em cada lado da placa.
- **Interface:** furos para os dois eixos e o LED, grade sobre o alto-falante, logo. Trechos retos na borda curva para o USB-C e o fone.
- **Fundo:** furo para o botão de gravação; acesso à bateria.
- **Nada é detalhado agora.** O design só faz um volume conceitual quando a placa tiver as alturas.

## Tarefas para o Code (v1)

**Foco: a placa.** Um passo, um PR, um merge. A programação (firmware do Viaggio) fica para depois, mas a numeração de pinos já sai compatível com o Teensy 4.1.

### Integração

- Pasta nova `etutti/hardware/viaggio/`. Acrescentar o Viaggio ao `CLAUDE.md` (projeto ativo; o Pocket fica concluído e pausado) e aos arquivos dos agentes (pastas que cada um pode editar no Viaggio, relatórios em `viaggio/`).

### Eletrônica

- **VE1. Esquema completo** (KiCad) da §3, partindo do esquema público do Teensy 4.1 para o bloco do processador (sem Ethernet, sem USB host, sem cartão SD) e da página do bootloader da PJRC.
  - Escolher o encapsulamento do RT1062 pela capacidade da JLCPCB (0,65 ou 0,8).
  - Conferir na LCSC/JLCPCB cada peça (estoque, básica ou estendida) e marcar as consignadas e as de Global Sourcing (MKL02, TMAG5253).
- **VE2. Posicionamento e roteamento** em 4 camadas, partindo do layout conceitual (`concept/`).
  - Áreas: teclado igual ao Pocket; interface até o limite espelhado.
  - USB de alta velocidade curta e com impedância controlada.
  - DRC 0/0/0; conferência placa × firmware 28/28.
  - Rigidez sobre os furos de fixação.
- **VE3. Documentos:**
  - `viaggio/pcb/PINOS.md`, com o mapa de pinos em numeração Teensy 4.1;
  - `viaggio/POWER.md`, com o orçamento refeito;
  - BOM da JLCPCB e BOM do kit (inclui bateria, alto-falante, switches, capas);
  - lista de alturas máximas por lado da placa;
  - relatório `viaggio/ELETRONICA.md`.

### Design

- **VD1. Volume conceitual do case** a partir das alturas da eletrônica: um render simples e as medidas totais (comprimento, largura, espessura). Nada de detalhamento de fabricação.

## 5. Perguntas para o J

Nenhuma em aberto.
