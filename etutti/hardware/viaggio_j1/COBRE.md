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
