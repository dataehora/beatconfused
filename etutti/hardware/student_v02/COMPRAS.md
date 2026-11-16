# eTutti Student V2 · notas de compra

16 nov 2026, atualizado para a SPEC v2. Complementa a lista da V1 (`../student_v01/LISTA_DE_COMPRAS.md`): aqui está só o que muda. Nada foi encomendado.

## 1. Montagem pela JLCPCB (o que muda na BOM)

Arquivos: `fab/student_v02_bom.csv` e `fab/student_v02_cpl.csv`.

| Peça | Código LCSC | O que muda | Observação |
|---|---|---|---|
| Encoder Alps EC11E18244AU (SW401, SW402) | C202365 | troca | Eixo de 20 mm (datasheet da Alps). O da V1, EC11E18244A5 (C255515), tem 25 mm e está com estoque 0 na LCSC. Mesmos 18 pulsos / 36 detentes, mesmo footprint, com clique. Estoque na LCSC em 16 nov: 2451; US$ 1,92 (10 un.). |
| Conector JST SH de 4 vias, SM04B-SRSS-TB (J401) | C160404 | novo | Para o cabo da tela. Ordem dos pinos Qwiic: 1 GND, 2 3V3, 3 SDA, 4 SCL. Estoque 60 mil; US$ 0,22. |
| Jack 3,5 mm PJ-327A 5JJ (J302) | C668605 | novo (segundo) | O mesmo do OUT. |
| Resistor 2,2 k 0402 (R305) | C25879 | novo | Bias do microfone. |
| Capacitor 1 µF 0402 (C309) | C52923 | novo | Acoplamento do microfone. |
| LED 1615 (D401), R401, R402, D402 | — | saem | Sem LED na V2. |
| Q201, R207, Q202 | — | não montar | Acionavam a luz de carga da V1. Os footprints ficam na placa, vazios. |

As demais peças e códigos são os da V1, já conferidos um a um (`../student_v01/fornecimento/FORNECIMENTO.md`).

A JLCPCB solda os dois encoders e os conectores à mão (peças com furo), como na V1.

## 2. Peças montadas em casa

| Peça | Qtd | Observação |
|---|---:|---|
| Módulo OLED 0,96″ 128 × 64, SSD1306, I²C, 4 pinos | 1 | Placa de cerca de 27,3 × 27,8 mm com 4 furos de 2 mm nos cantos. **Conferir antes de imprimir a tampa:** a medida da placa, a posição dos furos e a ordem dos pinos (há módulos GND-VCC-SCL-SDA e VCC-GND-SCL-SDA). Tem de aceitar 3,3 V. Endereço 0x3C. |
| Cabo JST SH 1,0 mm de 4 vias, 50 a 100 mm ("Qwiic" ou "STEMMA QT") | 1 | Uma ponta encaixa no J401; a outra é cortada e soldada nos 4 pinos do módulo. Cores usuais: preto GND, vermelho 3V3, azul SDA, amarelo SCL. |
| Alto-falante Ø 28 × 5 mm, 8 Ω, 2 W | 1 | Pedir ao vendedor a frequência de ressonância (fs); quanto mais baixa, melhor. Ver `estudos/ACUSTICA.md`. O da V1 (Ø 36) não cabe. |
| Tela acústica (tecido de alto-falante) 0,3 mm | 1 pedaço de 36 × 28 mm | Colada por baixo das fendas. |
| Junta de espuma de 1 mm, anel Ø 28 / Ø 24 | 1 | Veda a frente do alto-falante contra a tampa. |
| Acrílico fumê escuro de 1 mm, 25,7 × 14,7 mm, cantos R 1 | 1 | Janela da tela (`case/out/janela.step`). |
| Tinta para os rebaixos (esmalte ou acrílica) | — | Logo, filete sob a tela, OUT e IN: rebaixos de 0,4 mm. |
| Silicone | — | Veda o furo dos fios da caixa acústica e a borda do alto-falante no assento. |
| Teclas Gateron KS-20, bateria, módulo MicroMod Teensy | — | Como na V1. |

## 3. Parafusos

| Onde | Parafuso | Qtd |
|---|---|---:|
| Grade do teclado: por cima, atravessa grade, espaçador e placa; porca sob a placa | M2 × 16, cabeça panela, com porca M2 | 10 |
| Tampa: por baixo, atravessa a base e a placa e entra no poste da tampa | M2 × 14, autoatarraxante para plástico | 6 |
| Caixa acústica nas buchas da tampa | M2 × 5 | 2 |
| Módulo da tela nos postes da tampa | M2 × 4 (ou M1,6 × 4, conforme o furo do módulo) | 4 |
| Módulo MicroMod | M2,5 × 3 (vem no kit da SparkFun) | 1 |

## 4. Impressão

Peças em `case/out/` (STEP e STL), no referencial do modelo; cada uma deve ser deitada na mesa pelo serviço de impressão.

| Arquivo | Qtd | Cor (Retrô) | Observação |
|---|---:|---|---|
| `tampa` | 1 | creme | Faixas vermelha, laranja e amarela pintadas ou adesivas. |
| `base` | 1 | cinza | |
| `grade` | — | — | **Não é impressa:** FR-4 de 1,6 mm, pedida com a placa (`fab/student_v02_grade_gerbers.zip`; 2 camadas, máscara preta fosca). O STEP/STL em `case/out/` é a mesma forma, para conferência. |
| `espacador` | 10 | qualquer | Tubo de 5 × 11,35 mm. |
| `botao_branco_f1` … `f4` | 2, 4, 4, 2 | branco | f1 = fileira da frente. |
| `botao_preto_f1` … `f4` | 3, 4, 2, 2 | preto | |
| `botao_pontos_f1`, `f3`, `f4` | 2, 1, 2 | branco | Dó e Fá. Não há Dó nem Fá na fileira 2: `botao_pontos_f2` existe só para completar o jogo. |
| `knob` | 2 | preto | Traço creme pintado no sulco. |
| `caixa_acustica` | 1 | preto | Em L, fechada, 10,4 cm³. Paredes cheias (tem de ser estanque). Resina ou MJF de preferência; em filamento o teto sai em ponte sobre as nervuras. |
| `janela` | — | fumê | Cortada em acrílico (SPEC v2), não impressa. |

Os botões e o knob pedem resina ou MJF (o encaixe em cruz da tecla e o furo em D do eixo não saem bem em filamento).
