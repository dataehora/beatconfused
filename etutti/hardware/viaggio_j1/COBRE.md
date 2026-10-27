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
