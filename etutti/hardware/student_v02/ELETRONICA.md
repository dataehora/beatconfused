# eTutti Student V2 · eletrônica

16 nov 2026 · Code · responde à `SPEC.md` v1, entrega 1, e à **v2** (seção 0).

A placa da V2 é a da Student V1 (`../student_v01/`) com a interface refeita. Ela é escrita por script a partir da placa da V1, que não é alterada. Nada foi encomendado.

## 0. O que mudou no ciclo 2 (SPEC v2)

- **Conectores recuados.** O USB-C andou 1,25 mm e os dois jacks 2,15 mm para dentro da placa: a frente de cada um fica em x = 2,3, 0,3 mm atrás da face interna da parede. Só os conectores andaram; as peças de proteção ficaram onde estavam. O par USB foi encurtado num trecho reto, sem ser cortado.
- **Pads dos fios do alto-falante (J501):** em (48,1; 94,5), na frente da caixa acústica nova.
- **Grade do teclado em FR-4:** placa própria, sem circuito, feita por `pcb/grade_fab.py` (`kicad/student_v02_grade.kicad_pcb`, `fab/student_v02_grade_gerbers.zip`). 2 camadas, 1,6 mm, 172,6 × 91,2 mm, 28 furos de 6,2 mm e 10 de 2,3 mm, cobre contínuo sob a máscara nas duas faces. Pedir com máscara **preta fosca**. DRC sem erros.
- **Resultado da placa principal:** roteou na primeira tentativa (29 redes religadas, mais terra e 3,3 V; 190 trilhas e vias novas). DRC: as 3 larguras aceitas, 0 ligações faltando, paridade 0, os mesmos 4 avisos de ponta solta.
- BOM sem mudança de peças (39 linhas); CPL refeito com as posições novas (137 peças).
- As coordenadas do USB-C, do OUT, do IN e do J501 nas tabelas abaixo são as do ciclo 1; valem as desta seção.

## 1. O que mudou em relação à V1

| | V1 | V2 |
|---|---|---|
| Teclado | 28 teclas, sensores, 2 multiplexadores | **igual, trilha por trilha** |
| Contorno | 246,5 × 95 mm, cantos R 5 | o mesmo retângulo, cantos **R 6,5** (o canto interno do case é R 7) |
| LED | bicolor no tampo | **removido** (D401, D402, R401, R402) |
| Tela | — | conector J401 para um módulo OLED 0,96″ por **I²C** |
| Encoders | (20; 49) e (36; 49), eixo de 25 mm | **(28; 44,5) e (46; 44,5)**, eixo de **20 mm** |
| USB-C | y = 13 | **y = 16** |
| OUT (fone) | y = 25 | **y = 36** |
| IN (microfone) | — | **y = 60**, segundo jack, com bias |
| Fios do alto-falante (J501) | (46,5; 84) | (55,5; 79), fora da caixa acústica |
| Furos | 8 furos M2, 4 entre as teclas com parafuso | 6 da tampa na borda, 10 da grade na borda, 4 entre as teclas **só para os pinos da base** |

O referencial é o da SPEC: origem no canto de trás à esquerda do case. A placa vai de x 2,5 a 249 e de y 2,5 a 97,5 (0,5 mm da parede à esquerda, atrás e na frente; 1,0 mm à direita).

## 2. Tela: I²C

Escolhi **I²C**, pelo barramento que o codec já usa (pinos 18 e 19 do Teensy).

- Não gasta pino novo. O SPI pediria 4 ou 5 (relógio, dados, seleção, D/C, reset).
- O módulo de 4 pinos (GND, VCC, SCL, SDA) é o mais comum e mais barato; o conector na placa é um JST SH de 4 vias na ordem Qwiic, o padrão da família MicroMod.
- Não há conflito de endereço: o codec é 0x0A e a tela, 0x3C. Os resistores de pull-up (2,2 k) já existem.
- O que o I²C custa é velocidade: uma tela inteira leva cerca de 25 ms a 400 kHz. A tela só mostra estado (registro, volume, carga), então o firmware deve mandá-la em pedaços pequenos (16 bytes, menos de 0,5 ms cada), para não atrasar a leitura das teclas, que define a velocity.

Se um dia a tela precisar de animação rápida, os pinos de SPI do módulo (10 a 13) estão livres no conector, mas não foram levados a lugar nenhum nesta placa.

## 3. Microfone (IN)

- Jack J302, igual ao do OUT. Manga no GND; ponta = sinal.
- R305 (2,2 k) do MIC_BIAS do codec à ponta, para microfone de eletreto; C309 (1 µF) em série até o pino MIC.
- O anel e o contato de detecção do jack ficam soltos.
- O codec passa a devolver áudio ao processador: I2S_DOUT (pino 16 do SGTL5000) → pino 8 do Teensy (rede I2S_RX). Sem essa ligação o microfone não chegaria ao firmware.
- A conferir com a placa real: o nível do bias (o SGTL5000 também tem um resistor interno programável) e o ganho do microfone.

## 4. Encoders de eixo curto

EC11E18244AU, da Alps: eixo de 20 mm com chanfro, clique, 18 pulsos e 36 detentes. O datasheet dá "actuator length 20 mm". É a mesma peça da V1 com o eixo 5 mm mais curto (a EC11E18244A5 da V1 tem 25 mm e está com estoque 0 na LCSC). Footprint e firmware não mudam (`ENC_STEPS_PER_DETENT = 2`).

O eixo termina 1,8 mm acima do tampo; o knob tem uma luva que desce pelo furo da tampa (ver `FIT_CHECK.md`).

Os dois encoders estão girados (pinos à esquerda e à direita, abas na frente e atrás) para não cair sobre o codec, que fica logo atrás do primeiro. O capacitor C307 andou 2,8 mm para sair de baixo de uma aba.

## 5. Pinos do Teensy MicroMod

Iguais aos da V1, com três diferenças:

| Pino | V1 | V2 |
|---|---|---|
| 5 | LED verde | livre |
| 13 | LED vermelho | livre |
| 8 | livre | I2S_RX (áudio do codec para o processador) |

I²C (18/19) agora serve o codec e a tela.

## 6. Como a placa é feita

```
python etutti/hardware/student_v02/geometria.py
python etutti/hardware/student_v02/pcb/schematic.py
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v02/pcb/build_board.py     (~8 min)
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v02/fab.py
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v02/pcb/grade_fab.py
```

- `pcb/schematic.py` escreve o esquema (cópia do gerador da V1 com as mudanças acima), roda o ERC (0 erros, 0 avisos) e confere que tudo o que não foi mudado está igual à V1, pino por pino.
- `pcb/build_board.py` lê a placa da V1 e:
  1. tira o LED;
  2. move o USB-C com a sua proteção (o par USB só é esticado 3 mm num trecho reto), o jack OUT e os encoders;
  3. põe as peças novas (J302, R305, C309, J401) e os furos;
  4. tira o cobre que ficou sobre peça, furo ou zona proibida (36 trilhas e vias);
  5. redesenha o leque dos quatro pinos de cima do codec, porque o pino 16 (novo) não tinha saída;
  6. liga de novo o que ficou aberto com o roteador da J1 (26 redes, mais terra e 3,3 V; 194 trilhas e vias novas, nenhuma falha);
  7. roda o DRC do KiCad com paridade do esquema.
- Resultado do DRC: as 3 larguras de 0,12 mm da rede EN_B já aceitas na V1, **0 ligações faltando, paridade 0**. Sobram 4 avisos de "ponta solta" em trilhas que são ligações de fato (o KiCad chama assim uma trilha que termina fora do centro de um pad).
- Trilhas do teclado: não mexidas, a não ser onde um furo novo da borda cortou uma linha, que foi religada.

## 7. Fabricação

Em `fab/`: Gerbers e furação (`student_v02_gerbers.zip`), BOM, CPL (137 peças montadas: 12 em cima, 125 embaixo), lista do que fica fora da montagem e duas imagens.

- O CPL foi calculado a partir dos pads, pelo método que corrigiu a V1 (`fornecimento/`). **A prévia da JLCPCB precisa ser conferida de novo**, sobretudo os dois encoders (peça e orientação novas), os dois jacks e o J401.
- Q201, R207 e Q202 ficam na placa sem peça: acionavam a luz de carga da V1. Não foram removidos para não mexer nas trilhas de alimentação em volta deles.
- Não há plate nesta versão.

## 8. O que falta e o que só a placa real vai dizer

- **Notas da SPEC v2 para o firmware (a escrever):**
  - com o USB ligado e o instrumento desligado, a tela acende só com a carga, em brilho baixo (comando de contraste do SSD1306), e apaga ao tirar o cabo;
  - corte de graves abaixo de ~300 Hz no caminho do alto-falante (filtro passa-altas antes do amplificador; o fone e a saída OUT ficam sem corte).
- **Firmware:** tela, microfone, pinos 5 e 13 sem LED. O firmware atual da Student não foi adaptado: ainda aciona o LED nos pinos 5 e 13 e não usa a tela nem o microfone.
- A tela e o microfone nunca foram ligados a este circuito.
- Com o LED removido, não há indicação de carga com o instrumento desligado (pergunta no `FIT_CHECK.md`).
- O roteamento novo foi feito por programa e conferido pelo DRC; vale um olhar no KiCad antes do pedido, em especial no trecho do USB junto ao conector e no leque do codec.
