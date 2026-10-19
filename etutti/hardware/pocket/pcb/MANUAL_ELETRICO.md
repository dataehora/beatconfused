# eTuttino Pocket · conteúdo elétrico do manual de montagem

Dono: eletrônica (SPEC v5, tarefa F4; antes v4/F2). Entrada para o manual de montagem (M1/M2), que o design
escreve em `/etutti/pocket/manual/`. Português. Os passos seguem a ordem da SPEC v4 (M1, itens 1 a 9); aqui
está só o que é elétrico: o que soldar, como, o que medir e o que pode dar errado. As figuras que a
eletrônica precisa estão no fim (F-01 a F-17).

**Mudanças na v5 (para o M2):** não há mais plaquinha do painel. O micro-USB do Teensy vai à parede por um
**extensão micro-B em fita FPC** (fêmea presa na parede por uma presilha impressa, macho de 90° "UP" no Teensy); o 5 V do
carregador sai do **pad VUSB** do Teensy por um **fio de 26 AWG** soldado antes de empilhar (passo 3); o fone
é um **jack de painel** (Cliff FC681375V, porca na parede) ligado por **4 fios** ao J_JACK (passo 6.2). Na
placa principal: J_PNL saiu, entraram J_VBUS (1 pad) e J_JACK (4 pads), o TVS D60 e a chave do VIN (Q23/Q24/D61).

Referências das peças: `pcb/PECAS.json` e `pcb/fab/pocket_kit_bom.csv`. Placas: `pcb/kicad/`.
Medidas em mm. **(conferir)** = valor a confirmar no primeiro protótipo.

## Antes de começar (passo 1)

### Ferramentas

- Ferro de solda com ponta fina (cônica de 0,5–1 mm ou chanfrada de 1,5 mm), 330–350 °C; estanho 0,5–0,8 mm com fluxo.
- Fluxo em pasta ou caneta, malha dessoldadora, pinça, alicate de corte rente (para as pernas).
- Multímetro com medição de tensão contínua, resistência e continuidade (bipe).
- Estilete afiado (corte da ponte VUSB–VIN), lupa ou lente de aumento.
- Fita Kapton, termorretrátil fino, fios 28–30 AWG de silicone.
- Cabo USB com micro-B (ou USB-C → micro-B) e um carregador USB comum.
- Cola epóxi ou cola quente (alívio de tração do fio do VUSB).

### O que já vem montado da JLCPCB

- **Placa principal**: todos os CIs e passivos no verso (carregador, conversor, amplificador,
  multiplexadores, o TVS do VBUS, a chave do VIN, os 28 sensores TMAG5253) e, em cima, o conector
  JST SH J_CTL. Os sensores TMAG5253 não se soldam em casa (encapsulamento X2SON de 1,1 × 1,4 mm).

O que se solda em casa: o fio do VUSB, a pilha Teensy + Audio Board, os dois JST PH da placa principal
(bateria e alto-falante), os fios do fone (Audio Board → J_HP e jack de painel → J_JACK), o
potenciômetro, o encoder, o LED e o cabo dos knobs. A extensão micro-B em FPC só se encaixa e se prende com a presilha.

## Passo 3 · Teensy: cortar a ponte VUSB–VIN e soldar a pilha baixa

1. **Cortar a ponte VUSB–VIN** no verso do Teensy 4.0, antes de tudo (depois de soldado na Audio
   Board o verso fica inacessível). É a pequena trilha entre os dois pads marcados VUSB e VIN, no
   verso, perto do conector micro-B (figura F-01). Passe o estilete 3–4 vezes, firme, até ver a
   fibra da placa entre os dois pads.
   - **Teste:** multímetro em continuidade entre o pino **VIN** (borda, ao lado do GND) e o pad
     **VUSB** (ou a carcaça do micro-B **não**: use o pad VUSB): **sem bipe**. Se bipar, corte de novo.
   - Por quê: no Pocket o Teensy recebe 3,3 V do conversor da placa principal; o 5 V da USB vai só
     ao carregador. Com a ponte inteira, a USB e o conversor brigam no mesmo trilho.
2. **Fio do VUSB** (novo na v5), ainda com o Teensy solto: solde um fio de **26 AWG vermelho, ~50 mm**,
   no pad **VUSB** do verso do Teensy (na ponta do micro-B, ao lado dos pads da ponte que você acabou de
   cortar; figura F-01). Deite o fio para a ponta do USB e prenda-o com uma gota de epóxi ou cola quente
   a 2–3 mm do pad (alívio de tração: o pad é pequeno e arranca com um puxão).
   - **Teste:** ligue um cabo USB no micro-B do Teensy solto: entre a ponta do fio e o **GND** (borda),
     **4,75–5,25 V**, e o Teensy **não** acende o LED dele (ponte cortada, VIN sem nada). Se o LED
     acender, a ponte não foi cortada: volte ao 3.1. Tire o cabo.
   - O fio sai depois pela ponta do USB, entre o Teensy e a Audio Board (as barras de pinos fecham os
     lados compridos): na pilha baixa sobram ~2,5 mm, o fio de ≤ 1,2 mm passa.
3. **Isolar o verso do Teensy** com uma camada de fita Kapton (ele fica de frente para a Audio Board,
   ~2,5 mm acima dela), sem cobrir a solda do fio.
4. **Fios do fone na Audio Board** (antes de empilhar): solde três fios de ~40 mm (28–30 AWG, cores
   diferentes) nos terminais do jack de fone da Audio Board, pelo lado de baixo: **L** (ponta),
   **R** (anel) e **VGND** (manga, o terra virtual). Figura F-02 **(conferir os três terminais no
   esquema da Audio Board Rev D)**. Os fios vão depois aos pads J_HP da placa principal.
   - **Teste:** continuidade entre o fio VGND e qualquer pino GND da Audio Board: **sem bipe**. O
     terra do fone é virtual (~1,6 V); ligado ao GND, queima a saída de fone do codec.
5. **Pilha baixa:** passe as duas barras de pinos extralongas (1 × 14) pela Audio Board de baixo
   para cima, apoie o Teensy em cima (o plástico das barras é o único espaçador) e solde os 28
   pinos no Teensy e depois na Audio Board. As pernas compridas ficam para baixo: elas atravessam a
   placa principal no passo 4.
   - O Teensy fica com o USB do mesmo lado do jack da Audio Board (figura F-03).
   - **Medir:** da face de baixo da Audio Board ao topo do conector USB: **≤ 8,7 (conferir)**. Anote.
     Se der mais, as pernas ficaram altas: o case foi desenhado com 8,7.

## Passo 4 · Placa principal: conferir, soldar a pilha, testar o 3,3 V sem bateria

### 4.1 Conferir a placa montada (sem ferro)

Olhe o verso com lupa (figura F-04):

- os 28 sensores TMAG5253 no lugar, um sob cada switch, sem pontes de solda;
- U60 (carregador), U61 (conversor) com o indutor L10 ao lado, U62 (amplificador), U51/U52
  (multiplexadores), Q20/Q21/Q22, Q30/Q31 (luz de carga), D20/D30;
- D60 (TVS do VBUS, perto do carregador), Q23/Q24/D61 (chave do VIN, sob a ponta USB da pilha);
- em cima: J_CTL (SH 10 vias) soldado; J_VBUS (1 pad) e J_JACK (4 pads) vazios.

Medidas de resistência, **placa sem nada ligado** (ponta preta no GND):

| Onde medir | Esperado | Se der errado |
|---|---|---|
| J_BAT pino 1 (BAT+) × pino 3 (GND) | > 100 kΩ (o divisor da bateria tem 2 MΩ) | < 1 kΩ: curto no carregador ou em C62 |
| Furo do pino **3V3** da pilha (J2, 3º furo da fileira de trás) × furo **GND** | > 1 kΩ (sensores, multiplexadores e conversor desligados) | < 50 Ω: curto no trilho de 3,3 V |
| Pad **J_VBUS** × GND | > 50 kΩ | < 1 kΩ: TVS D60 em curto ou ponte de solda no carregador |
| Pad **J_JACK 3** (HP_VGND) × GND | **aberto** (> 1 MΩ) | bipe = erro grave (terra do fone no GND) |

### 4.2 Soldar a pilha e os conectores de cima

1. **Conectores JST PH** (passantes, por cima): J_BAT (3 vias, bateria) e J_SPK (2 vias,
   alto-falante), com a trava virada como na serigrafia (figura F-05). Solde pelo verso, sem
   encostar o ferro nos componentes vizinhos.
2. **Pilha:** encaixe as 28 pernas da pilha nos furos J1/J2 (USB do Teensy para a esquerda, para o
   lado do painel). A Audio Board fica ~3 mm acima da placa: use um calço de 3 mm (dois pedaços de
   papelão ou uma tira impressa) entre as duas, solde 2 pernas nas pontas, confira o paralelismo e
   solde as outras 26 pelo verso. Corte as pernas rente no verso (≤ 1 mm): **o verso encosta nos
   pilares do fundo** (figura F-06).
3. **Fios do fone** (do passo 3.4) nos pads **J_HP** da placa principal, na frente da Audio Board:
   1 = L, 2 = R, 3 = VGND (serigrafia). Torça os três fios juntos.
4. **Fio do VUSB** (do passo 3.2) no pad **J_VBUS**, no canto de trás-esquerdo da placa (figura F-05):
   leve o fio por fora da borda esquerda da Audio Board, **por baixo** de onde vai ficar o plugue micro-B
   (nada acima de ~6 mm da placa ali), corte no comprimento sem esticar, solde e cole o fio na placa
   com uma gota de cola a ~5 mm do pad.

### 4.3 Primeiro teste com USB, sem bateria e sem firmware do Pocket

Ainda sem bateria e sem plaquinhas: ligue um cabo USB direto no micro-B do Teensy. **Sem a chave do
volume ligada, nada liga** (o 3,3 V depende dela); este teste confere o fio do VUSB e o carregador.

| Onde medir (ponta preta no GND) | Esperado |
|---|---|
| J_VBUS | 4,75–5,25 V |
| Pino **VIN** do Teensy (por cima, ao lado do GND), chave aberta | ~0 V (o VIN só recebe o VBUS com o Pocket ligado) |
| J_BAT pino 1 (BAT+), sem bateria | 0–4,2 V oscilando (o carregador procura a bateria; normal) |
| 3V3 da pilha, chave aberta | 0 V |

A luz de carga pode piscar sem bateria (o BQ24074 alterna "carregando / sem bateria"): normal.

## Passo 5 · Plate e switches

Sem parte elétrica: os Gateron magnéticos não têm pernas elétricas (só pinos plásticos); o ímã
fica com o **norte para baixo** e o sensor está no verso da placa, de propósito. Não inverter nada.

## Passo 6 · Plaquinhas (knobs e volume) e painel, com os fios soldados

### 6.1 Plaquinha do volume (em pé) e plaquinha dos knobs

1. **Potenciômetro com chave** (RK097) na plaquinha do volume: 5 pernas (3 do potenciômetro,
   2 da chave) + as 2 abas da carcaça. Eixo para cima (figura F-07).
2. **Encoder EC11E** na plaquinha dos knobs: 5 pernas + 2 abas grandes (as abas passam pelas
   duas pontas da plaquinha: as "orelhas" na frente e atrás). Eixo para cima.
3. **LED 3 mm** bicolor no espaçador de ~10 mm: perna **comprida do meio = catodo (GND)**, no furo
   do meio; vermelho e verde nos furos marcados R e G (figura F-08). A ponta do LED precisa chegar
   ao furo da tampa: conferir a altura com a tampa antes de soldar.
4. **Junta de 90°:** encoste a plaquinha do volume na borda esquerda da plaquinha dos knobs, por baixo,
   em esquadro, e solde os 6 pads JP de uma na outra (só um é GND; os outros são reforço). Figura F-09.
5. **Cabo dos knobs** (JST SH 10 vias, com conector só na ponta da placa principal): corte os fios a
   ~100 mm, desencape 1,5 mm, estanhe e solde:
   - fios **1–5** nos pads JW1–JW5 da plaquinha do volume (face de trás, no alto): 1 VCC, 2 POT,
     3 GND, 4 PWR_A, 5 PWR_B;
   - fios **6–10** nos pads JW6–JW10 da borda direita da plaquinha dos knobs: 6 ENC_A, 7 ENC_B,
     8 ENC_SW, 9 LED_R, 10 LED_G.
   - O fio 1 é o do lado marcado do conector SH (normalmente o fio de cor diferente ou o da borda do
     conector com o triângulo): **conferir com o multímetro** do pino 1 do J_CTL até o pad JW1.
   - **Teste:** continuidade de cada pad ao pino do J_CTL (tabela no `PINOS.md`); nenhum par vizinho
     em curto.

### 6.2 Painel: jack de fone e micro-B de painel

1. **Jack de fone Cliff FC681375V** (figura F-10): antes de montar, solde 4 fios de 28–30 AWG, ~80 mm
   **(conferir o comprimento com o case)**, nas abas de trás, e isole cada solda com termorretrátil:
   - aba **3 (T, ponta)** → **J_JACK 1 (HP_L)**;
   - aba **2 (R, anel)** → **J_JACK 2 (HP_R)**;
   - aba **1 (S, manga)** → **J_JACK 3 (HP_VGND)**, o terra virtual: **nunca no GND**;
   - aba **4 (comutação da ponta)** → **J_JACK 4 (HP_TIPSW)**.
   Passe a rosca pelo furo da parede **por dentro**, ponha a porca anel por fora e aperte com uma chave
   na fenda da porca (sem forçar: parede de plástico). Torça os 4 fios e solde no J_JACK.
2. **Testes do jack** (sem nada ligado; um plugue de fone à mão):

| Onde medir | Esperado |
|---|---|
| J_JACK 3 (HP_VGND) × GND (J_BAT 3) | **aberto**. Bipe = erro grave: o fone não pode ir ao GND |
| J_JACK 1 (ponta) × J_JACK 4 (comutação), sem plugue | bipe (o contato fecha sem plugue) |
| O mesmo, com um plugue de fone encaixado | aberto |
| J_JACK 1 × J_HP 1, J_JACK 2 × J_HP 2, J_JACK 3 × J_HP 3 | bipe (o jack de painel e o da Audio Board ficam em paralelo) |

3. **Extensão micro-B em fita FPC** (figura F-13): a cabeça da fêmea entra no bolso do ressalto, com a
   boca rente ao furo da parede, e a presilha impressa a prende com **2 parafusos M2 × 5**. O macho de 90°
   ("UP") entra no micro-B do Teensy **até o fim**, com a fita saindo **para cima**; dobre a fita **uma vez,
   rente**, no caminho que o design desenhou (a fita aceita dobra chata, mas não fica sendo dobrada e
   desdobrada), longe do indutor L10. Não puxe o plugue do Teensy pela fita.
4. **Teste:** cabo USB na fêmea do painel: **J_VBUS = 4,75–5,25 V**. Com o Pocket ligado (passo 9) e o
   cabo num computador, o computador vê o Teensy.

## Passo 7 · Bateria e alto-falante

### 7.1 Alto-falante

1. Os dois fios do alto-falante (vermelho +, preto −, 152 mm) passam pelo furo da caixa e são
   vedados ali com cola (a caixa tem de ficar fechada).
2. Na ponta, o plugue JST PH 2 vias (PHR-2): **vermelho no pino 1 (SPK+)**, preto no pino 2. A
   polaridade só muda a fase, não estraga nada.
3. **Teste:** resistência entre os dois fios: **~8 Ω** (7–9). Aberto = fio partido.

### 7.2 Bateria (LiPo) — avisos de segurança

> **Bateria de lítio-polímero: leia antes de mexer.**
> - **Não furar, não dobrar, não amassar, não aquecer.** Nada de ferro de solda perto da célula.
> - **Não carregar sem o NTC ligado** (o fio do meio). Sem ele o carregador não sabe a temperatura:
>   a placa só carrega com o NTC entre 0 e 45–50 °C.
> - **Conferir a polaridade do plugue antes de ligar** (abaixo): a ordem dos fios muda entre
>   vendedores. Polaridade invertida queima o carregador e pode aquecer a bateria.
> - Não deixar os fios + e − se tocarem; isolar as pontas com fita se cortar algum.
> - Bateria estufada, amassada, com cheiro doce ou quente: **não usar**; descartar em ponto de coleta.
> - Carregar sobre superfície não inflamável nas primeiras vezes e não deixar carregando sem ninguém
>   por perto no primeiro protótipo.

1. **Conferir a bateria** com o multímetro, no plugue dela (figura F-11):
   - entre o fio **vermelho (+)** e o **preto (−)**: 3,0–4,2 V (bateria nova costuma vir com 3,7–3,9 V);
   - entre o fio do **NTC** (o terceiro) e o **preto**: **~10 kΩ** a 25 °C (8–12 kΩ).
2. **Conferir o rabicho** (extensão JST PH 3 vias) já ligado ao J_BAT da placa, **sem a bateria**:
   continuidade de cada pino da ponta do rabicho ao pino do J_BAT: 1 = BAT+, 2 = NTC, 3 = GND.
3. **Antes de encaixar a bateria no rabicho:** compare as duas pontas. O vermelho da bateria precisa
   cair no pino que vai ao **J_BAT 1 (BAT+)**, o NTC no **2** e o preto no **3**. Se não, **troque
   os terminais da carcaça do rabicho** (levante a lingueta com uma agulha), nunca os da bateria.
4. Encaixe a bateria. **Medir:** J_BAT 1 × J_BAT 3 = a tensão da bateria (3,0–4,2 V); J_BAT 2 ×
   J_BAT 3 ≈ 0,75 V com USB a 25 °C (0,6–0,9; o carregador injeta 75 µA no NTC de 10 kΩ; sem USB, ~0 V).
5. A célula vai no berço sobre a espuma, sem cola, com o PCM (a plaquinha da bateria) do lado da
   saída dos fios. O plugue fica no bolso.

## Passo 8 · Fechar o case

Elétrico, só conferir antes de fechar:

- nenhum fio preso entre o fundo e os pilares, nem sobre o verso da placa;
- o cabo SH encaixado até o fim no J_CTL (trava audível);
- o plugue micro-B de 90° encaixado até o fim no Teensy, a fêmea na presilha com os 2 parafusos M2, a fita dobrada rente;
- o fio do VUSB colado nas duas pontas, longe do indutor L10 e de bordas cortantes;
- o plugue do alto-falante no J_SPK e o rabicho no J_BAT.

## Passo 9 · Primeiros testes sem a firmware do Pocket

O Teensy ainda tem o programa de fábrica (pisca o LED laranja dele) ou nenhum. Sem a firmware do
Pocket o pino KEEP não sobe; por isso o comportamento sem USB é diferente do final (abaixo).

| # | Teste | Como | Esperado |
|---|---|---|---|
| 1 | Luz de carga com o Pocket **desligado** | volume todo para a esquerda (clique = desligado), bateria encaixada, cabo USB no micro-B do painel e num carregador | **vermelho aceso** enquanto carrega; apaga quando a bateria enche (pode levar ~2,5 h) |
| 2 | Luz de carga com o Pocket **ligado** | com o USB ainda ligado, gire o volume além do clique | a luz de carga **apaga** (ligado, quem mostra a carga é a firmware, com o verde). Com o programa de fábrica do Teensy o vermelho **pisca** junto com o LED laranja dele (o programa pisca o pino 13): normal |
| 3 | 3,3 V presente | ligado e com USB: medir o pino **3V** do Teensy (por cima) × **G** | **3,25–3,35 V** |
| 3b | VIN do Teensy | ligado e com USB: pino **VIN** × **G** | **4,4–5,0 V** (VBUS menos o diodo D61). Desligado: ~0 V |
| 3c | USB | ligado, cabo num computador | o computador vê o Teensy (programa de fábrica: serial "Teensy"; com a firmware: "eTutti" MIDI) |
| 4 | Liga/desliga pelo volume | com USB: girar o volume até o clique (desligar) | 3V do Teensy cai a 0 V em < 1 s |
| 5 | Ligado só com a bateria (sem USB) | girar o volume além do clique | o 3,3 V aparece por **~0,5 s e cai**: é o normal **sem a firmware do Pocket** (ela segura o KEEP). Com a firmware, fica ligado |
| 6 | Tensão da bateria | J_BAT 1 × 3 | 3,0–4,2 V |
| 7 | Fone sem GND | Pocket desligado, multímetro em continuidade entre a manga de um plugue encaixado no jack e o GND (J_BAT 3) | **aberto** |
| 8 | Carga | depois de 10–20 min carregando, encostar o dedo na bateria pelo bolso | morna no máximo. Quente = desligar a USB e conferir o NTC |

Se o teste 3 der 0 V com USB e volume ligado: conferir o cabo dos knobs (fios 4 e 5 = chave) e a
chave do potenciômetro (continuidade entre os pinos 4 e 5 dele ligado). Se der ~4,4 V ou 5 V no 3V:
**desligar já** e conferir o corte da ponte VUSB–VIN (passo 3.1).

**Em breve** (seção marcada assim no manual): gravar a firmware do Pocket pelo micro-USB do painel (com o volume
ligado e o cabo no computador o Pocket fica ligado durante a gravação), calibrar as teclas.

## Pontos de teste: resumo para o manual

| Ponto | Onde fica | Valor |
|---|---|---|
| GND | J_BAT pino 3; pino G do Teensy | referência |
| BAT+ | J_BAT pino 1 | 3,0–4,2 V com bateria |
| NTC | J_BAT pino 2 | ~10 kΩ ao GND sem energia; ~0,75 V com USB (25 °C) |
| VBUS | pad J_VBUS | 4,75–5,25 V com USB |
| VIN do Teensy | pino VIN (por cima) | ~4,4–5 V ligado com USB; 0 V desligado |
| VSYS (saída do carregador) | pad JW4 da plaquinha do volume (PWR_A, por 100 Ω) | ~4,4 V com USB; = bateria sem USB |
| 3,3 V | pino 3V do Teensy (por cima) | 3,25–3,35 V ligado; 0 V desligado |
| Terra do fone | manga do jack / J_JACK 3 | nunca em continuidade com o GND |
| Alto-falante | entre os fios | ~8 Ω |

## Figuras que a eletrônica precisa (para o design desenhar)

Numeradas F-xx; o design escolhe a numeração final do manual. Todas com a peça nova em destaque
(âmbar) e balões numerados.

| Fig. | Peça | Vista | Destacar |
|---|---|---|---|
| F-01 | Teensy 4.0, verso | close-up de cima (verso para cima), perto do micro-B | a ponte VUSB–VIN e a linha do corte (seta + tesoura); **o pad VUSB com o fio de 26 AWG soldado e a gota de cola** |
| F-02 | Audio Board Rev D, verso | close-up do jack de fone | os 3 terminais L, R, VGND com os fios soldados (cores) |
| F-03 | Pilha baixa (Teensy sobre a Audio Board) | lateral, de frente para o USB | as barras extralongas, o plástico como espaçador, a cota ≤ 8,7 |
| F-04 | Placa principal montada, verso | vista inteira | sensores sob os switches, U60/U61/L10/U62, U51/U52, Q31/Q22 (para conferir) |
| F-05 | Placa principal, topo, canto esquerdo | close-up | J_BAT e J_SPK (orientação da trava), **J_VBUS com o fio do VUSB, J_JACK (1–4)**, J_CTL, pads J_HP |
| F-06 | Pilha soldada na placa principal | lateral em corte | calço de 3 mm, pernas cortadas rente no verso |
| F-07 | Plaquinha do volume com o RK097 | iso | eixo para cima, as 5 pernas, porca M7 |
| F-08 | Plaquinha dos knobs com encoder e LED | iso | LED no espaçador (catodo no meio), encoder |
| F-09 | Junta de 90° volume × knobs | close-up por baixo | os 6 pads JP soldados em esquadro |
| F-10 | Jack de painel FC681375V | iso por trás + vista da parede | as 4 abas numeradas (1 S, 2 R, 3 T, 4 comutação) com as cores dos fios; porca anel por fora |
| F-11 | Bateria e rabicho | plano | os 3 fios (+, NTC, −) e a ordem 1-2-3 no J_BAT; multímetro nas pontas |
| F-12 | Cabo dos knobs | esquema plano | fios 1–5 na plaquinha do volume, 6–10 na dos knobs, pino 1 marcado |
| F-13 | Extensão micro-B em FPC | iso, case aberto | fêmea na presilha com 2 M2, plugue "UP" no Teensy com a fita subindo e dobrada rente até a fêmea |
| F-14 | Pocket montado em corte | corte em y ~21 e em y ~49 | pilha, bateria, alto-falante, plaquinhas, cabos (pedido da SPEC M1) |
| F-15 | Pontos de teste | vista de cima, case aberto | GND, BAT+, 3V, VIN, J_VBUS, J_JACK 3 (balões com os valores da tabela) |
| F-16 | LED | duas fotos/renders | vermelho com o Pocket desligado carregando; apagado ligado |
| F-17 | Fio do VUSB na pilha | lateral, ponta do USB | o fio saindo entre o Teensy e a Audio Board, por baixo do plugue de 90°, até o J_VBUS |

Figuras que **saem** na v5: a da plaquinha do painel (antiga F-10) e o esquema TP1–TP8 (antiga F-13).
