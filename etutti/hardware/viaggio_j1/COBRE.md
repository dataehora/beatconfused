# eTutti Viaggio J1 · cobre de GND e +3V3

27 out 2026, agente eletrônica, branch `viaggio-j1-cobre`. Esta é uma exceção autorizada pelo J sobre a placa que ele roteia à mão: entra **só cobre de GND e +3V3**, sem roteador e sem busca de caminho. Nenhuma trilha ou via do J foi apagada ou movida, exceto as 6 vias soltas pedidas.

Script: `cobre.py` (python do KiCad 10). Ele pode rodar de novo sem duplicar nada. Tudo o que cria fica registrado em `cobre_uuids.json`, e as zonas novas têm nome começando por `COBRE `. Cada execução apaga o que a anterior criou e refaz.

```
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/cobre.py
```

O arquivo é gravado pela técnica do PR #120. O pcbnew salva num temporário e o script encaixa no `.kicad_pcb` original só estas mudanças:
- as 3 zonas novas;
- a zona `L2 GND` do In1, que foi apenas repreenchida;
- as vias e trilhas novas;
- a remoção das 6 vias.

Conferência bloco a bloco contra o `HEAD`:
- cabeçalho, setup, empilhamento, footprints e as 1314 trilhas/213 vias do J estão idênticos;
- `.kicad_pro`, `.kicad_prl` e `.kicad_dru` não mudaram;
- saíram as 6 vias e o bloco antigo da `L2 GND`;
- entraram 987 vias, 46 trilhas (tocos) e 4 zonas (a `L2 GND` repreenchida mais as 3 novas).

## O que foi feito

1. **6 vias soltas apagadas**, cada uma conferida por rede e coordenada:

   | Rede | Posição (mm) |
   |---|---|
   | OUT_K03 | (118,65; 8,77) |
   | MUX_S2 | (184,33; 12,25) |
   | PROG | (23,36; 11,25) |
   | EN_A | (98,20; 43,40) |
   | HP_L | (11,94; 30,27) |
   | HP_R | (8,85; 23,30) |

2. **Áreas de cobre**, todas sobre o contorno inteiro da placa, com folga 0,25 e largura mínima 0,2:
   - `COBRE GND F.Cu` e `COBRE GND B.Cu`;
   - `COBRE +3V3 In2.Cu`, no espaço livre entre as trilhas do In2.

   Regras de preenchimento:
   - alívio térmico 0,25/0,25 só em pinos de furo passante;
   - pinos SMD ligados cheios (veja as Perguntas);
   - ilhas isoladas removidas;
   - os anéis livres dos furos M2 (áreas de regra H1–H8) ficam sem cobre;
   - o In1 continua a zona `L2 GND` de antes, só repreenchida.
3. **Vias de costura de GND 0,5/0,3: 941 no total.**
   - 936 estão numa grade de 5 mm. Quando o centro da célula não servia, o script procurou até ±2 mm em volta.
   - 5 ficam em ilhas de GND em F.Cu/B.Cu que não tinham nenhuma via nem pino passante.

   Cada via só entrou depois deste teste de folga, feito nas quatro camadas:
   - 0,25 contra qualquer cobre, de qualquer rede, inclusive trilhas do In2 e pads de GND (para não ter via no pad);
   - 0,25 de furo a furo;
   - borda a 1 mm;
   - fora das áreas de regra M2 e fora do pátio (B.CrtYd) do J101.

   A área do `cartao_MicroMod` não proíbe vias e as vias são tampadas, então ali pode haver costura. Depois de preencher, o script confere que cada via pega o In1 e também F.Cu ou B.Cu. Nenhuma precisou sair.

   Sobraram 37 ilhas pequenas, entre 0,1 e 6 mm², quase todas entre o J101 e o carregador (x 20–72, y 4–36), sem lugar para uma via. Elas foram removidas no preenchimento final.
4. **Vias por pino: 46**, cada uma com um toco reto até o pino.

   | Rede | Vias |
   |---|---|
   | GND | 3 (U204.11, U201.2, U602.15) |
   | +3V3 | 43 (sensores U7xx, seus capacitores C7xx, R301/R302/R218, C101/C102, J101.74, U204.1, U602.24, U604/U605…) |

   - Largura do toco: 0,2, ou 0,15 em pinos finos (< 0,45 mm de lado). O toco tem até 2,75 mm.
   - Folga: 0,2 contra outras redes.
   - Toda via de +3V3 cai num pedaço do In2 +3V3. Primeiro o script tenta o derramamento principal. Se não der, usa um bolsão fechado pelas trilhas do In2, que então fica e junta os pinos dali.
   - Uma via por pino (J101.74, em (30,02; 27,60)) ficou dentro do pátio do J101, colada ao pino. As vias de costura ficaram todas fora do pátio.

## DRC (kicad-cli, `--schematic-parity --severity-all`, com o `.kicad_dru` da placa)

| | antes | depois |
|---|---|---|
| track_width (do J) | 13 | 13 (as mesmas) |
| via_dangling | 6 | 0 |
| track_dangling | 0 | **1**: toco do J em OUT_K03, B.Cu, 0,46 mm em (118,97; 8,45), que terminava na via de OUT_K03 apagada |
| clearance, short, hole, starved_thermal… | 0 | 0 |
| paridade com o esquema | 0 | 0 |
| ligações não feitas | 237 | **51** |

Ligações não feitas por rede:

| Rede | Antes | Depois |
|---|---|---|
| GND | 162 | 9 |
| +3V3 | 51 | 18 |
| VBUS | 10 | 10 |
| VSYS | 6 | 6 |
| VBAT | 3 | 3 |
| I2C_SDA, I2C_SCL, BB_L1, BB_L2, OUT_K03 | 1 cada | 1 cada |

A redes que não são GND nem +3V3 não foram tocadas.

Tentativas: o script rodou 6 vezes enquanto era ajustado, sempre a partir do mesmo estado de partida e sem duplicar nada. Nenhuma rodada criou erro de folga ou curto. Duas coisas mudaram no caminho:
- **Primeira rodada:** alívio térmico em todos os pinos deu 15 `starved_thermal`, em pinos SMD finos (J201 A1/A12/B1/B12, J101.7/36, U501.3/11/15, C202, C602, R203, R209, R211, Q202). A solução foi alívio só nos pinos de furo e pinos SMD ligados cheios.
- **Bolsões do In2:** o +3V3 ganhou a etapa dos bolsões, que levou de 29 para 18 ligações.

## O que sobrou (para o J rotear)

**GND, 9.** Ilhas de B.Cu presas a um só pino SMD, sem lugar para via com toco reto até 3 mm:

| Pino | Posição (mm) |
|---|---|
| C304.2 | (21,18; 36,05) |
| U301.21 | (24,00; 35,50) |
| R211.2 | (63,95; 19,34) |
| R209.2 | (66,24; 19,43) |
| U202.8 | (61,25; 10,44) |
| U204.7 | (68,08; 9,50) |
| U204.3 | (70,88; 9,00) |
| U204.9 | (68,08; 8,50) |
| C208.2 | (70,69; 5,41) |

É a região densa do carregador e do conversor, e no U301 é o pad central do codec.

**+3V3, 18.** Quase todas ligam grupos que as trilhas do In2 fecharam em bolsões separados, com as trilhas de +3V3 do J em B.Cu. Pares da DRC:

| Ponta A (mm) | Ponta B (mm) |
|---|---|
| (21,18; 34,95) | (26,15; 31,23) |
| (29,77; 9,00) | (31,57; 9,48) |
| (29,77; 27,00) | (31,69; 23,29) |
| (68,08; 8,00) | (70,88; 8,00) |
| via (107,21; 55,16) | (98,70; 38,99) |
| (107,95; 22,97) | (115,72; 15,18) |
| (107,95; 55,01) | (117,20; 41,22) |
| (107,95; 23,53) | (126,45; 25,20) |
| (126,45; 57,23) | via (125,58; 55,59) |
| (135,70; 71,03) | via (127,30; 57,23) |
| (144,95; 57,23) | via (136,35; 41,22) |
| via (153,15; 8,23) | (148,86; 9,55) |
| via (163,92; 23,68) | U726.1 (163,45; 25,20) |
| (172,70; 73,25) | via (164,10; 57,23) |
| (178,43; 13,36) | (182,59; 15,18) |
| via (181,21; 23,12) | (181,95; 25,20) |
| via (184,55; 25,71) | (200,45; 22,97) |
| (218,95; 57,23) | (209,70; 41,22) |

U726.1 é o único pino de +3V3 sem lugar para via.

**Outras redes, intocadas:**

| Rede | Ligações | Pinos ou ponto |
|---|---|---|
| VBUS | 10 | J201 B4/B9, D201.1, U201.5, J101.9, R214/R205/R206, Q201.2, C201.1, U202.13 |
| VSYS | 6 | U501.7/8, R210.1, U204.5, trechos em (58–64; 9–17) |
| VBAT | 3 | J202.1, R208.1, C203.1 |
| I2C_SDA | 1 | R301.2 – J101.12 |
| I2C_SCL | 1 | R302.2 – J101.14 |
| BB_L1 | 1 | U204.4 – L201.1 |
| BB_L2 | 1 | U204.2 – L201.2 |
| OUT_K03 | 1 | toco em (118,97; 8,45) – U703.4 (135,20; 73,25) |

## As 13 track_width do J (não corrigidas)

| Rede | Camada | Largura medida | Mínimo da regra | Onde (mm) |
|---|---|---|---|---|
| EN_B | B.Cu | 0,12 | 0,15 | (144,68; 59,11), (144,14; 59,11), (144,70; 59,14) |
| VSYS | B.Cu | 0,60 | 0,80, classe Corrente | (66,75; 9,48), (66,84; 8,66), (65,64; 6,53), (64,71; 5,59), (66,75; 8,74), (66,30; 9,48) |
| MUX_S0 | In2.Cu | 0,10 / 0,10 / 0,12 | 0,15 | (25,15; 10,08), (25,08; 10,15), (25,00; 10,23) |
| MUX_S0 | In2.Cu | 0,12 | 0,15 | (120,78; 8,16) |

## Imagens

Em `build/`, olhadas uma a uma:
- `cobre_top.png`, F.Cu;
- `cobre_bottom.png`, B.Cu visto de cima, sem espelhar;
- `cobre_in2.png`, +3V3;
- `cobre_in1.png`, GND.

Legenda das cores:
- azul: GND;
- laranja: +3V3;
- verde: via de costura;
- vermelho: via e toco por pino;
- magenta: anel livre M2.

No In2 aparecem grandes bolsões sem +3V3 nos setores dos sensores (x 115–175, y 10–75) e à esquerda (x 20–60), fechados pelas trilhas do J no In2.

Os relatórios DRC brutos estão em `build/drc_antes.json` e `build/drc_cobre_r2.json`. O resumo está em `build/cobre_resumo.json`.

## Perguntas para a gestão

1. **Pinos SMD ligados cheios** às áreas de GND de F.Cu/B.Cu: o alívio térmico em pinos de 0,5 mm não fechava os 2 raios mínimos. Para montagem por refusão na JLC isso costuma ser aceitável. Mantemos, ou o J prefere outra saída (regra `min_resolved_spokes 1` no `.kicad_dru`)?
2. **Malha de 5 mm deu 941 vias de costura.** Não há erro de DRC, mas cada via fura o +3V3 do In2. Quer uma malha mais larga (7–10 mm), ou só costura junto das bordas e do áudio?
3. **O In2 +3V3 ficou repartido** pelas trilhas que o J passou no In2: 18 ligações de +3V3 continuam abertas. O J prefere ligar os bolsões com trilhas, ou tirar trilhas do In2 para o plano fechar?
4. **Toco solto de OUT_K03** em (118,97; 8,45): ficou depois que a via foi apagada (`track_dangling`, aviso). Apagamos, ou o J o usa ao rotear OUT_K03?
5. **9 pinos de GND da região do carregador e do codec** (U204, U202, U301, C208, C304, R209, R211) não aceitaram via com toco reto. O J liga esses à mão, por exemplo ao pad central do U204?

# Rota restante (27 out 2026)

Agente eletrônica, branch `viaggio-j1-rota-restante`, tarefa autorizada pelo J: rotear as 51 ligações que o cobre deixou abertas. Nenhuma trilha, via, zona ou peça existente foi apagada ou movida. A única exceção é o toco solto de OUT_K03 em (118,97; 8,45), apagado no lote 5.

Script: `rota_restante.py` (python do KiCad 10). Ele roda por lote e registra tudo o que cria em `rota_restante.json`. Rodar o lote N de novo apaga antes o que o lote N tinha feito.

```
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/rota_restante.py <1..5>
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/rota_restante.py fotos
```

Como funciona:
- **Roteador:** A* em grade (0,05 mm; 0,1 mm em janelas grandes) em F.Cu, In2.Cu e B.Cu, com vias passantes 0,5/0,3. O In1 (GND inteiro) não recebe trilha. O `router.py` arquivado não foi usado: ele só tem duas camadas e só pinos alinhados aos eixos.
- **O que liga:** os grupos de cada rede, como a conectividade do pcbnew os vê (zonas incluídas). Um pedaço solto de GND termina numa via que pega o plano do In1, ou numa ilha do derramamento que já está ligada.
- **Larguras:**
  - Corrente: 0,8. Afina até 0,15 dentro dos pátios que o `.kicad_dru` nomeia (J201, U202, U204, J202, U501, J101) e até 0,3 a menos de 0,6 mm de um pino ligado.
  - GND e +3V3: 0,3 ou 0,2.
  - Sinais: 0,2.
  - 0,15 só a menos de 1 mm dos pinos ligados.
  - Uma célula estreita custa 4× no A*, então o roteador só afina onde precisa.
- **Folgas:**
  - 0,1 ou 0,2 pela classe, mais 0,03 de margem na 1ª tentativa e nenhuma na 2ª;
  - furo 0,2; furo a furo 0,25; borda 0,3; as áreas M2 são respeitadas;
  - cada trilha e via nova é conferida de novo com as formas exatas do pcbnew antes de entrar.
- **Ilhas:** depois de cada lote as zonas são repreenchidas. Um pedaço de GND ou +3V3 que uma trilha nova soltou é religado no mesmo lote. Se não der, o lote é refeito do zero com o cobre em volta desse pino protegido. Isso aconteceu uma vez, no lote 3, com o J101.36.
- **Gravação:** como no PR #120/#123. O script encaixa no arquivo original só as trilhas e vias novas e as 4 zonas repreenchidas. Depois confere, bloco a bloco e por uuid, que todo o resto ficou idêntico (3956 blocos no fim). `.kicad_pro`, `.kicad_prl` e `.kicad_dru` não mudaram.

## Por lote

As ligações não feitas são as que o DRC conta (`kicad-cli pcb drc --schematic-parity --severity-all`). Em todos os lotes, o DRC deu 0 clearance, 0 short, 0 hole_clearance, 0 hole_to_hole e paridade 0.

| Lote | Commit | Fechadas | Trilhas novas | Vias novas | Não roteadas |
|---|---|---|---|---|---|
| 1: VSYS, VBAT, GND do carregador | f9ea016 | VSYS 3, VBAT 2, GND 5 (+1 ilha nova religada) | 107,6 mm | 9 | 51 → 41 |
| 2: VBUS | 317b7a6 | VBUS 9 (+1 ilha nova de GND religada) | 79,8 mm | 9 | 41 → 32 |
| 3: I2C, +3V3 à esquerda | d0d1b8e | I2C_SDA, I2C_SCL, +3V3 4 | 24,9 mm | 6 | 32 → 26 |
| 4: +3V3 no teclado | edb8d4e | +3V3 14 | 10,3 mm | 11 | 26 → 12 |
| 5: OUT_K03 | 4348321 | OUT_K03 | 71,4 mm | 2 | 12 → 11 |

As mensagens dos commits 1 a 4 trazem contagens de não roteadas erradas, somadas à mão. As certas são as da tabela, tiradas dos relatórios do DRC.

Ligações que valem citar:
- **VSYS do carregador ao amplificador** (C202/Q203 → C501/U501): 76,2 mm a 0,8, em F.Cu e B.Cu, 3 vias.
- **VBUS** do J201 ao J101, ao U201, ao D201 e à entrada do carregador, a 0,8. Um trecho de 35,2 mm corre pela F.Cu ao longo da borda de cima.
- **VBAT:**
  - do J202 ao R208: 4,6 mm a 0,8, pelo In2;
  - do U202.2/3 ao J202: 22,9 mm a 0,8, com 0,2 só dentro do pátio do U202.
- **I2C_SDA:** 12,6 mm em B.Cu, a 0,2, com 0,15 na entrada do J101.
- **I2C_SCL:** 9,8 mm a 0,2, 2 vias.
- **+3V3:** 14 das 18 ligações saíram com uma via só, da trilha de +3V3 do J em B.Cu para o bolsão do In2 logo embaixo. As outras usam trilhas de 0,3 de até 2,7 mm.
- **OUT_K03** do U601.8 ao U703.4: 71,4 mm a 0,2, em B.Cu e F.Cu, 2 vias.
- **GND do U204:** os pinos 3, 7 e 9 vão ao pad central (pino 11) por tocos de 0,2 em B.Cu. O C208.2 vai por 1,8 mm em B.Cu.

## DRC final

| Tipo | Quantidade |
|---|---|
| track_width | 18: as mesmas 13 do J + 5 afinamentos de VBUS a 0,5 na entrada de pinos fora dos pátios do `.kicad_dru` |
| track_dangling | 0 (o toco de OUT_K03 saiu) |
| clearance, short, hole_clearance, hole_to_hole, via_dangling | 0 |
| paridade com o esquema | 0 |
| ligações não feitas | **11** |

Os 5 afinamentos, todos de VBUS com largura 0,5:

| Camada | Posição (mm) | Pino ao lado |
|---|---|---|
| F.Cu | (17,08; 12,25) | U201.5 |
| B.Cu | (52,60; 6,90) | Q201.2 |
| B.Cu | (53,41; 6,20) | R214.1 |
| B.Cu | (53,71; 6,20) | R214.1 / R205.1 |
| B.Cu | (53,96; 6,05) | R205.1 |

## O que ficou de fora (11)

| Rede | Pinos | Posição (mm) | Motivo |
|---|---|---|---|
| BB_L1 | U204.4 – L201.1 | (70,88; 9,50) – (75,67; 9,00) | A trilha de +3V3 do J em B.Cu, que vai de U204.1 até (70,64; 11,05), passa em x 71,67–71,76, entre os pinos 2–5 do U204 e o L201. Não sobra lugar para trilha nem para via. |
| BB_L2 | U204.2 – L201.2 | (70,88; 8,50) – (72,67; 9,00) | A mesma trilha de +3V3. |
| VSYS | U204.5 – trecho do J | (70,88; 10,00) – (66,75; 9,48) | A mesma trilha de +3V3. |
| VSYS | R210.1 – trilha F.Cu do J | (56,29; 12,96) – (58,69; 15,51) | R210.1 está cercado em B.Cu, e não há lugar para via (F.Cu e In2 ocupados por cima). |
| VSYS | trecho B.Cu (60,56; 9,25) – trecho F.Cu (65,68; 12,66) | | U202.10/11 sem saída a 0,8 e sem lugar para via. |
| VBAT | C203.1 – via VBAT nova | (64,11; 13,88) – (66,25; 17,70) | C203.1 está numa ilha fechada por trilhas em B.Cu. Por cima passam a VSYS larga do J em F.Cu e trilhas do In2: não há ponto de via. |
| VBUS | R206.1 – trilha VBUS | (54,22; 9,39) – (52,65; 9,00) | R206.1 está cercado, sem lugar para via. |
| GND | R209.2 | (66,24; 19,43) | Ilha de B.Cu fechada por trilhas, sem ponto de via livre nas quatro camadas. |
| GND | R211.2 | (63,95; 19,34) | O mesmo caso do R209.2. |
| GND | U301.21 (pad central do codec) | (24,00; 35,50) | Trilhas do J no In2 passam bem embaixo do pad. A via no pad foi liberada para GND, mas não há ponto livre. |
| GND | C304.2 | (21,18; 36,05) | Cercado pelo laço de +3V3 C305.1–C304.1 em B.Cu, com trilhas do In2 por cima. |

Cada uma teve 2 tentativas: margem 0,03 com janela de 6 mm, depois margem 0 com janela de 16 mm. Todas fecham se o J mexer em alguma trilha dele. Só a trilha de +3V3 junto do U204 já resolve 3.

## Imagens

Em `build/`, olhadas uma a uma. Vermelho = trilhas e vias novas; cinza = do J; azul claro = GND; laranja claro = +3V3.
- `rota_cima.png`: F.Cu.
- `rota_baixo.png`: B.Cu visto de cima, sem espelhar.
- `rota_in2.png`: In2.Cu. O +3V3 agora é praticamente um pedaço só.

Os relatórios brutos do DRC ficam em `build/drc_rota_lote*.json`, fora do Git, como os do cobre.

## Perguntas para a gestão

1. **Afinamentos de Corrente fora dos pátios:** são 5 trechos de VBUS a 0,5 na entrada de R214, R205, Q201 e U201, que o DRC acusa como track_width. Ampliamos a regra "Corrente: afinacao na entrada dos pinos" do `.kicad_dru` para os pátios de R205, R206, R214, Q201, U201 e C201, ou o J prefere outra saída?
2. **Trilha de +3V3 do J em x 71,7, junto do U204:** ela prende BB_L1, BB_L2 e VSYS (U204.5). O J a desvia (por exemplo, descendo o +3V3 do U204.1 por uma via ao lado do pino) ou faz essas três ligações à mão?
3. **GND do codec (U301.21, C304.2):** as trilhas do In2 embaixo do pad central impedem as vias, e um pad central de codec sem via para o GND é ruim para o áudio. Vale tirar uma ou duas trilhas do In2 dali?
4. **R209.2, R211.2, C203.1, R206.1 e R210.1 ficaram em bolsões fechados.** Ligamos depois que o J abrir espaço, ou ele mesmo as fecha no KiCad?
5. **OUT_K03** foi refeito inteiro: 71 mm em B.Cu e F.Cu, atravessando o teclado. Serve assim? Se o J preferir outro caminho, basta apagar as trilhas listadas no lote 5 de `rota_restante.json`.

# Fechamento (27 out 2026)

Agente eletrônica, branch `viaggio-j1-fechamento`. Responde às 5 perguntas da "Rota restante" com as respostas da gestão. Antes: 18 track_width e 11 ligações não feitas. Depois: 13 track_width (só as do J) e 4 ligações não feitas.

## O que mudou no `.kicad_dru`

Só a regra "Corrente: afinacao na entrada dos pinos (patios)". Ela agora também vale nos pátios de R205, R206, R214, Q201, U201 e C201, na mesma forma `!(!A.intersectsCourtyard(...) && ...)`. O DRC roda sem erro de regra. As 5 track_width dos afinamentos de VBUS somem: 18 → 13. O `rota_restante.py` usa a mesma lista de pátios (`THIN_REFS`).

## Como foi feito

O `rota_restante.py` ganhou o lote 6, em três sublotes: `6a`, `6b` e `6c`.

```
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/rota_restante.py 6a|6b|6c
```

- **Arrancar e refazer.** Uma ligação que falha duas vezes da forma normal passa por uma busca A* nova:
  - as trilhas autorizadas podem ser atravessadas, mas cada célula atravessada custa 25 vezes mais e cada via 40 vezes mais;
  - quando o caminho achado cruza uma trilha autorizada, o segmento é cortado só onde atrapalha: na passagem e mais a folga dela, acrescida de 0,4 mm;
  - as duas pontas que sobram ficam como segmentos novos, na mesma linha, camada, largura e rede do original;
  - a ligação é roteada. Depois, um desvio de mesma rede e mesma largura liga de novo os dois pontos de corte. O desvio só pode usar a largura menor do original (0,15) a menos de 1 mm desses pontos;
  - se o corte encosta na ponta do segmento, o segmento sai inteiro. Dois cortes que se encontram num ponto sem cobre viram um desvio só;
  - se a ligação ou algum desvio não fecha, tudo volta como estava (*undo*). São 2 tentativas: margem 0,03 com janela de 6 mm, depois margem 0 com janela de 16 mm.
- **Corrente.** No lote 6, uma trilha de Corrente fica a 0,8 em toda parte, menos dentro dos pátios do `.kicad_dru`. O afinamento a 0,3 junto do pino saiu, e nenhum afinamento novo apareceu no DRC.
- **Trilhas autorizadas:**
  - a trilha de +3V3 do J junto do U204: 6 segmentos fixos por uuid, de (71,67; 8,08) a (70,64; 11,05). O resto dela até o C207.1 ficou;
  - as trilhas finas, fora da classe Corrente, a até 3 mm do pino de cada bolsão: R210.1, U202.10/11, C203.1, R206.1, R209.2 e R211.2;
  - no 6c, junto do U202.10/11, também as trilhas de Corrente a até 5 mm;
  - só as do In2 junto do C304.2 e sob o U301.21.
- **Gravação:** o mesmo método dos lotes 1 a 5. O script encaixa no arquivo só os segmentos e vias novos e as 4 zonas repreenchidas, e tira só os segmentos arrancados. Depois confere bloco a bloco, por uuid, que todo o resto ficou idêntico: 4085 blocos no fim. `.kicad_pro` e `.kicad_prl` ficaram idênticos aos do main, e os footprints também (nenhuma peça foi movida).
- **Conferência por sublote:**
  - DRC sem violação nova de folga, curto, furo ou ponta solta;
  - paridade 0;
  - nenhuma rede com mais ligações faltando do que antes. O script sai com erro se algo disso falhar.

## Por sublote

Contagens tiradas dos relatórios do DRC (`build/drc_rota_lote6*.json`, fora do Git).

| Sublote | Commit | Fechou | Não roteadas antes → depois |
|---|---|---|---|
| 6a: U204 e carregador | 00002d0 | BB_L2, VSYS R210.1, VBAT C203.1, VBUS R206.1, GND R209.2*, GND R211.2 | 11 (GND 4, VSYS 3, VBUS 1, VBAT 1, BB_L1 1, BB_L2 1) → 6 (GND 3, VSYS 2, BB_L1 1) |
| 6b: codec | a23a4b8 | GND U301.21 (2 vias no pad) | 6 → 5 (GND 2, VSYS 2, BB_L1 1) |
| 6c: o que restou | d5f7967 | GND R209.2, de novo | 5 → 4 (GND 1, VSYS 2, BB_L1 1) |

\* No 6a, o R209.2 foi ligado por 0,78 mm de trilha a uma ilha do cobre GND de B.Cu. Um desvio feito depois, no mesmo sublote, soltou essa ilha do plano, e no repreenchimento final o R209.2 voltou a ficar solto. Por isso o 6a fecha 6 ligações e o DRC conta 5 a menos. No 6c, o R209.2 desce ao In1 por uma via própria em (67,63; 18,53).

Ligações novas:
- **BB_L2** (U204.2 → L201.2): 3,1 mm em B.Cu. A trilha vai a 0,8 e só afina, até 0,15, dentro do pátio do U204.
- **VSYS** (R210.1 → via VSYS em (58,69; 15,51)): 3,4 mm a 0,8, em B.Cu e F.Cu, 1 via.
- **VBAT** (C203.1 → via VBAT em (66,25; 17,70)): 4,5 mm a 0,8, em B.Cu e In2, 1 via.
- **VBUS** (R206.1 → trilha VBUS em F.Cu): 3,4 mm, 0,5 dentro do pátio do R206 e 0,8 fora, 1 via.
- **GND R209.2:** 0,78 mm a 0,3, mais a via do 6c.
- **GND R211.2:** 0,44 mm a 0,2, 1 via.
- **GND U301.21:** 2 vias de 0,5/0,3 dentro do pad central. Uma fica no centro, em (24,00; 35,50), entre as 4 janelas de pasta. A outra fica em (23,45; 34,95). Num pad de 1,65 mm, com as trilhas do In2 que estavam lá, não coube uma terceira com a distância de furo a furo.

## Trilhas apagadas e refeitas

27 segmentos apagados, todos refeitos com a mesma rede e largura, ligando os mesmos pontos. "Restos" são as pontas do segmento original que voltaram como segmentos novos.

| Sublote | Rede | Camada | Largura | De – até (mm) | Compr. | uuid |
|---|---|---|---|---|---|---|
| 6a | +3V3 | B.Cu | 0,15 | (71,67; 8,08) – (70,95; 8,08) | 0,72 | aec31083-1f7b-4dc5-8cb3-358c01c0e2db |
| 6a | +3V3 | B.Cu | 0,20 | (71,67; 8,49) – (71,67; 8,08) | 0,41 | c40a17e3-3c5d-466d-ab19-d537afde617b |
| 6a | +3V3 | B.Cu | 0,15 | (71,76; 8,58) – (71,67; 8,49) | 0,12 | 2a252c93-d6cb-4677-aef6-5241a5231d1a |
| 6a | +3V3 | B.Cu | 0,15 | (71,76; 8,79) – (71,76; 8,58) | 0,21 | a4c0fa06-0fe6-4cf7-b05e-f5c8077415d7 |
| 6a | +3V3 | B.Cu | 0,20 | (71,76; 9,93) – (71,76; 8,79) | 1,14 | 8c10bf73-8c0d-467d-8760-620d9198f542 |
| 6a | +3V3 | B.Cu | 0,20 | (70,64; 11,04) – (71,76; 9,93) | 1,58 | ac807682-fab9-4950-a4e4-5ece2d947b93 |
| 6a | PWR_EN_S | B.Cu | 0,20 | (55,67; 13,54) – (55,06; 14,15) | 0,86 | 9643d65c-3685-46d9-82d0-beb999db2b77 |
| 6a | PWR_EN_S | B.Cu | 0,15 | (55,60; 12,80) – (55,67; 12,87) | 0,10 | ffe6c304-1a27-446b-b013-0033945e5d61 |
| 6a | PWR_EN_S | B.Cu | 0,15 | (55,67; 12,87) – (55,67; 13,54) | 0,68 | 9ab55575-c2c0-487d-b13b-cb5ae4343ffa |
| 6a | PWR_EN_S | B.Cu | 0,20 | (55,60; 12,41) – (55,60; 12,80) | 0,38 | cc9e2b12-531e-44e3-aa4a-8e35a48cac0c |
| 6a | VOL_SW_N | B.Cu | 0,15 | (57,03; 12,76) – (56,88; 12,62) | 0,20 | ffc5c778-d9ca-4ba6-a829-8f7cb73e95c5 |
| 6a | VOL_SW_N | B.Cu | 0,20 | (57,03; 12,89) – (57,03; 12,76) | 0,13 | f63fa47e-03b5-4a57-8788-3cb54d7674e8 |
| 6a | VOL_SW_N | B.Cu | 0,20 | (57,33; 13,19) – (57,03; 12,89) | 0,42 | a750ee13-fae4-47b7-bf45-2903caa81d2f |
| 6a | VOL_SW_N | B.Cu | 0,15 | (56,88; 12,62) – (56,88; 12,54) | 0,08 | 842de9bc-4722-4c5d-87d2-dfc55a3cb25f |
| 6a | VOL_SW_N | B.Cu | 0,20 | (56,88; 12,54) – (56,29; 11,94) | 0,84 | 15787104-d74d-48de-a3cb-fa5f3593db58 |
| 6a | USB_HOLD | In2.Cu | 0,20 | (63,37; 14,88) – (57,48; 14,88) | 5,88 | 38aa3656-4cb0-4c83-82bf-1b5b27632884 |
| 6a | CHG_STAT | F.Cu | 0,20 | (57,98; 13,71) – (53,88; 13,71) | 4,10 | 4ee38af3-caaa-4fd5-8997-a4bf48481553 |
| 6a | CHGLED | In2.Cu | 0,20 | (62,60; 11,59) – (62,60; 13,60) | 2,01 | 9350a0bb-bd7e-47bc-a24d-1bf4fe07ebd7 |
| 6a | BAT_NTC | In2.Cu | 0,20 | (63,99; 11,97) – (63,99; 21,56) | 9,59 | 3aa8a0d5-a272-41b3-aa2f-b7457235e809 |
| 6a | VBUS_S | B.Cu | 0,20 | (51,91; 5,91) – (51,91; 15,96) | 10,05 | 93275340-7819-4692-b86a-f235dd562596 |
| 6a | PWR_KEY | B.Cu | 0,20 | (66,90; 19,99) – (68,37; 18,53) | 2,07 | 4313f05a-43db-4b07-b92d-52ffe8d98d35 |
| 6a | PWR_KEY | B.Cu | 0,20 | (63,59; 19,99) – (66,90; 19,99) | 3,32 | 73a4ef74-ddd9-45e0-85d8-600e45684928 |
| 6a | PWR_KEY | B.Cu | 0,20 | (61,03; 17,44) – (62,93; 19,34) | 2,68 | 2856ad09-9bf9-4ec8-8ed7-66677bceb2e6 |
| 6a | VBAT_S | B.Cu | 0,20 | (62,72; 18,61) – (64,40; 18,61) | 1,68 | 6b67b6b7-474c-44b1-9d02-b2106ed6c481 |
| 6a | VBAT_S | B.Cu | 0,20 | (61,70; 17,60) – (62,72; 18,61) | 1,43 | fbe138ee-5e4c-4987-b2a0-ccbcc6f3b24e |
| 6b | I2S_BCLK | In2.Cu | 0,20 | (22,51; 34,24) – (32,17; 43,91) | 13,67 | ac4c2a51-b7d9-404d-9630-bbe049e7d7aa |

Para que serviu cada grupo:
- **+3V3:** a trilha junto do U204;
- **PWR_EN_S, VOL_SW_N, USB_HOLD e CHG_STAT:** o bolsão do R210.1;
- **CHGLED e BAT_NTC:** o C203.1;
- **VBUS_S:** o R206.1;
- **PWR_KEY 4313f05a e 73a4ef74, VBAT_S:** o R209.2 e o R211.2;
- **PWR_KEY 2856ad09:** o R211.2;
- **I2S_BCLK:** as vias do U301.21.

Os caminhos novos (desvios):

| Rede | Largura | Liga (mm) | Comprimento | Camadas | Vias | Restos |
|---|---|---|---|---|---|---|
| +3V3 | 0,15 | (71,67; 8,08) – (70,95; 8,08) | 0,87 | B.Cu | 0 | 0 |
| +3V3 | 0,2 (0,15 junto das pontas) | (71,67; 8,08) – (70,64; 11,05) | **20,85** | B.Cu, In2 | 2 | 0 |
| PWR_EN_S | 0,2 (0,15 junto das pontas) | (55,06; 14,15) – (55,60; 12,41) | 1,96 | B.Cu | 0 | 0 |
| VOL_SW_N | 0,2 (0,15 junto das pontas) | (57,33; 13,19) – (56,29; 11,94) | **15,07** | B.Cu, In2 | 2 | 0 |
| USB_HOLD | 0,2 | (60,69; 14,88) – (58,49; 14,88) | 2,22 | In2 | 0 | 2 |
| CHG_STAT | 0,2 | (57,44; 13,71) – (55,54; 13,71) | 3,06 | F.Cu | 0 | 2 |
| CHGLED | 0,2 | (62,60; 11,59) – (62,60; 13,60) | 2,04 | In2 | 0 | 0 |
| BAT_NTC | 0,2 | (63,99; 11,97) – (63,99; 14,03) | 2,45 | In2 | 0 | 1 |
| VBUS_S | 0,2 | (51,91; 7,80) – (51,91; 10,00) | 4,45 | B.Cu | 0 | 2 |
| PWR_KEY | 0,2 | (67,69; 19,20) – (66,15; 19,99) | 2,94 | B.Cu | 0 | 2 |
| VBAT_S | 0,2 | (64,40; 18,61) – (62,07; 17,97) | 7,07 | B.Cu, In2 | 2 | 1 |
| PWR_KEY | 0,2 | (61,82; 18,23) – (62,93; 19,34) | 6,19 | B.Cu, In2 | 2 | 1 |
| I2S_BCLK | 0,2 | (22,51; 34,24) – (32,18; 43,91) | **21,13** | F.Cu, In2, B.Cu | 2 | 0 |

Os uuids de cada desvio e de cada resto estão em `rota_restante.json` (lotes `6a`, `6b` e `6c`: `desvios`, `apagadas` e `arrancadas_por_ligacao`). O DRC confirma que nenhuma das redes refeitas ficou com ligação faltando.

Três desvios saíram longos:
- **+3V3 do U204:** 20,85 mm, contornando o L201 em B.Cu. O U204.1 e o C207.1 já estão ligados ao +3V3 do In2 pelas vias do J em (71,625; 8,00) e (69,20; 12,29), então este desvio só repete o que o plano já faz.
- **VOL_SW_N:** 15,07 mm no lugar de 1,7 mm.
- **I2S_BCLK:** 21,1 mm no lugar de 13,7 mm. Um corte curto, só em volta das vias, deixava a ponta presa entre SEL_A e I2S_LRCLK, então o segmento saiu inteiro.

## DRC final

`kicad-cli pcb drc --schematic-parity --severity-all`, no commit d5f7967:

| Tipo | Quantidade |
|---|---|
| track_width | 13, as mesmas do J (3 EN_B, 6 VSYS em B.Cu, 4 MUX_S0 em In2) |
| clearance, short, hole_clearance, hole_to_hole, track_dangling, via_dangling e demais | 0 |
| paridade com o esquema | 0 |
| ligações não feitas | **4**: GND 1, VSYS 2, BB_L1 1 |

## O que ficou de fora (4)

Cada ligação teve 2 tentativas normais e mais 2 com as trilhas autorizadas arrancadas.

| Rede | Pinos | Posição (mm) | Motivo |
|---|---|---|---|
| BB_L1 | U204.4 – L201.1 | (70,88; 9,50) – (75,67; 9,00) | Mesmo sem a trilha de +3V3, não há saída. Ao norte do L201.2 passa o BB_VINA (x 71,47). Ao sul e entre os dois pads do L201 está o VBAT do lote 1: a via em (73,84; 10,20) e o trecho de 0,8 em B.Cu em x 74,14, de y 10,5 a 12,1. Em F.Cu passa por cima o VBAT de 0,8 em y 9,3 (64,4–72,8), também do lote 1, e ele tira o lugar de uma via junto do pino. Agora o desvio de +3V3 também contorna o L201 em B.Cu. |
| VSYS | U204.5 – C202.1 | (70,88; 10,00) – (66,75; 9,48) | O pino 5 está do lado leste do U204 e o C202 do lado oeste. Por baixo do chip fica o pad central; ao sul ficam o EN_REQ e o +3V3 que vai ao C207. Em F.Cu passam o VBAT do lote 1 (y 9,3) e o SENS_EN (y 10,49). Essas trilhas não estão na lista autorizada. |
| VSYS | U202.10/11 – resto do VSYS | (60,56; 9,25) – (64,40; 11,38) | É a saída OUT do carregador. Os pinos 10/11 dão para o C205 e o C213, a 0,66 mm. Não cabe via, a 0,5 com folga de 0,2, nem trilha de 0,8 fora do pátio do U202. Pads não se arrancam. No 6c, nem arrancando também as trilhas de Corrente a até 5 mm houve caminho. **Sem esta ligação, o VSYS do carregador não chega ao resto da placa.** |
| GND | C304.2 | (21,18; 36,05) | Em B.Cu, o pad está fechado pelo +3V3: o laço C305.1–C304.1 e a trilha U301.12–C304.1. Em F.Cu passa por cima o HP_L (y 36,135). Mesmo sem as trilhas do In2 (AMP_SD e VOL_B), não há ponto de via a menos de 0,34 mm do pad. As trilhas de +3V3 do B.Cu não estavam autorizadas. |

## Imagens

Em `build/`, regeradas com `rota_restante.py fotos` e olhadas, com zoom no carregador e no codec. Vermelho = trilhas e vias novas, dos lotes 1 a 6; cinza = do J.
- `rota_cima.png`: F.Cu.
- `rota_baixo.png`: B.Cu visto de cima. Nela aparece o laço de +3V3 em volta do L201.
- `rota_in2.png`: In2.Cu.

## Perguntas para a gestão

1. **VSYS do carregador (U202.10/11)** é a ligação mais importante que falta: sem ela, a saída do BQ24074 não alimenta nada. Os pinos dão para o C205 e o C213, sem lugar para via nem para 0,8. Saídas possíveis:
   - mover o C205 ou o C213 cerca de 0,5 mm;
   - aceitar uma via no pad do U202.10/11;
   - aceitar VSYS a 0,3 por 1–2 mm até uma via, com uma regra no `.kicad_dru`.

   Qual o J prefere?
2. **BB_L1 e VSYS do U204.5** estão presos pelo VBAT que o lote 1 passou entre os pads do L201 (via em (73,84; 10,20), B.Cu em x 74,14 e F.Cu em y 9,3), e agora também pelo desvio de +3V3. Autoriza arrancar e refazer esse VBAT e o desvio de +3V3?
3. **Desvio de +3V3 de 20,85 mm em volta do L201:** ele repete o caminho que o plano do In2 já faz, pelas vias do J em (71,625; 8,00) e (69,20; 12,29), e fecha o L201.1 em B.Cu. Pode ser apagado sem refazer, deixando o +3V3 do U204.1 ao C207.1 só pelo plano?
4. **C304.2 (GND):** autoriza uma via no pad do C304.2, ou arrancar o laço de +3V3 C305.1–C304.1 em B.Cu?
5. **Desvios longos de sinal:** VOL_SW_N (15 mm, 2 vias) e I2S_BCLK (21 mm, 2 vias, em 3 camadas). Servem assim, ou o J prefere refazê-los à mão?
