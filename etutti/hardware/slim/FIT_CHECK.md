# eTutti Slim · FIT_CHECK (SPEC R4SL, Etapa 2b — portão B da placa principal)

Resposta à **SPEC R4SL §8**. Relatórios: [ELETRONICA.md](ELETRONICA.md) (escolha da bateria, seção 0), [POSICIONAMENTO.md](POSICIONAMENTO.md) (seção A: placa principal), [RESTRICOES_CASE.md](RESTRICOES_CASE.md) (56 itens), [FIRMWARE.md](FIRMWARE.md), `estudos/botao/` (botão). **Parado no portão B da placa principal: sem rotas, nada cotado, comprado ou amostrado.**

## 1. Resumo da R4SL

| Parte | Resultado |
|---|---|
| **Bateria (item 9)** | **VARTA 56457 201 016 (1/LPP 523450 S PCM W)**, 34,5 × 52,0 × 5,35, **1000 mAh** (a folha se contradiz: 1000 × 1400; usei 1000), NTC 10 k B 3380, 3 fios; **CPC UK BT07248, £ 12,50, 2 em estoque (25 nov)**; STEP e folha do fabricante. Case **+8,0 mm** à esquerda (247,0 mm) |
| **Apoio das réguas (item 1)** | **contínuo nas 4 fileiras** (2 trilhos de 1,5 mm por régua, o mesmo tipo, sem furo no piso): `case/corte_apoio.py` provou **0 vãos** de ponta a ponta, cauda incluída; cortes em `case/renders/corte_apoio_4fileiras.png` e `case/out/apoio.json`. Nada precisou mudar |
| **Knobs S1/S2/S3 (item 3)** | cortes dos dois knobs em `case/img/knobs_s123.png`; **S2 aplicada no modelo oficial** (`case/case.py`): plataforma segue o tampo (+1,0), poço horizontal, eixo vertical, ímã horizontal; ímã→sensor 2,5 mm (face do ímã z 8,5, centro do chip z 6,0); S3: erro de ângulo ≤ 0,22° |
| **Grade (itens 4 e 6)** | furo **14,00 com dog‑bone** (R0,6 recuado 0,25) e **M2 escareado** D4,4 × 90° pelo lado das teclas (DRC da grade 0/0) |
| **Botão (item 10)** | pino **Ø5,4** no poço Ø5,67, cruz fêmea 4,2 × 1,04 (macho 4,0 × 1,10, lido do STEP), interferência 0,06 na largura, **SLA**; `estudos/botao/` |
| **Placa principal (2b)** | 69,0 × 77,1 mm, 4 camadas, 120 peças na face de baixo; **DRC sem trilhas 0 erros / 0 avisos; paridade 0**; RT1062 com zona de escape de 2,5 mm; 4 FFC alinhados (cabo ~20 mm sob medida); par USB 36 mm |
| **Programação e som** | NTC (B 3380), carga 0,41 C (0,405 A) e autonomia ~8,1 h da 523450 em `FIRMWARE.md`; `check_placa.py`: **21/21 pinos × placa posicionada**; `check_pins.py` 15/15; `check_teclas.py` 32/32 |
| STEP que faltam | MKL02 (QFN‑16, sem STEP público), JST SH 3 vias, W25Q64 (SOIC‑8 em caixa); o resto da placa tem modelo real |
| Desvios da R4SL | (1) pinagem do FFC **invertida** na principal; (2) **S2 sobe o knob de volume 1,0 mm**; (3) **tubo de retenção** sob o tampo do volume; (4) par USB 36 mm (aceito 30–35) |

## 2. Itens que mudam o lado de fora (precisam do OK do J)

1. **Planta 247,0 × 89,1** (x −98,0…149): **+8,0 mm** à esquerda, **2,5 mm a menos** que os +10,5 aprovados na R3SL, por causa da bateria escolhida (R07/R08).
2. **Plataformas S2** seguem o tampo e o **knob de volume sobe 1,0 mm** (topo do knob a z 26,8) (R09/R55). O de registros mantém +1,0.

Todo o resto é interno (R42…R54, R56).

## 3. Cortes e figuras (onde ver)

| Pedido | Arquivo |
|---|---|
| Apoio contínuo, 1 corte por fileira (trilho e centro) | `case/renders/corte_apoio_4fileiras.png` |
| S1/S2/S3 dos dois knobs | `case/img/knobs_s123.png` (e `.svg`) |
| Botão cotado com a switch e o tampo | `estudos/botao/botao_corte.png`, `botao.step`, `botao.json` |
| Placa principal (planta cotada, blocos) | `pcb/principal/img/planta_principal.png` |
| Cena 3D: placa vista de baixo, base com réguas e knobs, cortes | `case/renders/cena_principal_*.png`, `corte_principal_*.png` |

## 4. Estudo do botão (item 10)

Medidas lidas do **STEP da KS‑33D** (cortes a cada 0,5 mm; o desenho da Gateron não cota a cruz): braços de **4,00**, largura **1,10**, altura ≥ 3,3 (topo 0,2 abaixo do topo da haste); poço Ø5,67 (SPEC).

| Item | Valor |
|---|---|
| Pino | **Ø5,40** (folga radial 0,135 no poço), 3,4 abaixo da saia |
| Cruz fêmea | braços 4,2 (0,1 de sobra em cada ponta), **fenda 1,04** (macho 1,10): **interferência 0,06 total (0,03 por face)** em SLA (±0,1: faixa −0,04…+0,16); 3,0 de fundo; entrada chanfrada 0,3 |
| MJF PA12 | **não serve para a cruz** (±0,3 e pó preso em fenda de 1 mm); só com cruz em inserto usinado |
| Cabeça | saia Ø15 × 0,75, domo até +4,0 (topo z 18,55 / 20,55 / 22,55 / 25,55 nas fileiras 1…4; **o mesmo botão nas quatro**); saia a 0,2 da carcaça no fundo do curso |
| Folga no furo do tampo (Ø16) | **0,5 nominal, 0,35 no pior caso** de impressão (±0,15); a folga da haste (±0,2) e a inclinação do soquete (0,5° → 0,09 mm) são **estimativas** (a Gateron não publica): **margem 0,06 mm**; com a saia **Ø14,8** a margem é 0,16 |
| Processo | **SLA** (resina Tough/Durable), pretos/brancos/branco com ponto; ou nylon SLS fino; onde encomendar (sem cotação): JLC3DP, PCBWay 3D, Craftcloud, Protolabs Network UK |
| Antes de imprimir 32 | **ensaio de 4 botões** com fendas 1,00 / 1,04 / 1,08 / 1,12: medir a força de saída (alvo 3–10 N) e o jogo |

## 5. Placa principal: o que mudou no esquema

**Pinagem dos 4 FFC invertida** (pino n da principal = pino 9−n da régua; ERC 0/0 refeito): as bocas dos dois conectores se olham (a placa gira 180° em relação à régua), então o cabo reto mantém a posição de cada condutor e não a numeração. A régua não mudou.

## 6. Itens para o J fornecer ou confirmar

**STEP:** MKL02, JST SH 3 vias (o fabricante tem), W25Q64 (o da biblioteca do KiCad serve). **Bancada (só o protótipo responde):** campo real nos sensores, folga axial 0,8 com o MJF, cruz fêmea em SLA, estoque da bateria, TMAG5273A2 (60 peças), Full Speed forçado, comprimento do FFC.

## Perguntas para o design

1. **Bateria 523450 e o lado de fora:** aprova a escolha (1000 mAh, ~8,1 h; **2 em estoque no CPC UK**, Farnell com prazo de 28 semanas; a 012 saiu de linha) e a planta **247,0 mm (+8,0)**, 2,5 mm menor que os +10,5 da R3SL? Se a folha estiver certa nos 1400 mAh da tabela, a autonomia sobe a ~11,3 h.
2. **S2 (plataformas que seguem o tampo):** o poço tem **0,1 mm na frente e 2,3 (registros) / 2,9 (volume) atrás**, e o knob fica com um vão em cunha de 2,0 / 2,6 mm atrás; o **knob de volume sobe 1,0 mm** (topo 26,8). Aceita S2, ou prefere S1 (disco plano, 2,6 acima do tampo na frente) ou S3 (eixo perpendicular, erro de ângulo 0,22°)? Se S2: quer uma **saia** no knob para esconder a cunha?
3. **Botão:** aprova **SLA** (não MJF) para o botão, a fenda de 1,04 e o **ensaio dos 4 botões** antes de imprimir 32?
4. **Saia do botão:** Ø15 (margem 0,06 mm no pior caso) ou **Ø14,8** (margem 0,16)? A SPEC fixa Ø15.
5. **Cabo FFC:** os 4 iguais de **20 mm sob medida** (estimado: 5,5 de vão + 6,8 de inserção + folga), ou **30 mm de série** com uma curva em S?
6. **Par USB:** 36 mm em linha reta (aceito 30–35; roteado ~38–42). Aceita, ou subo o RT1062 de y 33 para ~37 (encurta o USB, alonga o OUT das fileiras 1 e 2)?
7. **LED reverso:** o 1615 precisa de uma janela na placa sob o anel e os pads deixam só 0,5 mm entre as fileiras: confirmo na folha do LED, ou passo o LED para a face de cima (soldado em casa)?
8. **Pinagem invertida do FFC** na principal (item 5): aprova mexer no esquema da principal (a régua não muda) em vez de usar cabo com torção?
