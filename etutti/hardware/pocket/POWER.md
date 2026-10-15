# eTuttino Pocket · orçamento de energia

Gerado por `layout.py` (não editar à mão; mude o `BUDGET` no script).
Trilho único de 3,3 V a partir de uma LiPo 1S por um conversor buck-boost (eficiência 90 %).
Meta: 4,0 h tocando com fone. Capacidade útil = 85 % da nominal (corte, envelhecimento, frio).

| Consumidor | típ. (mA) | máx. (mA) |
|---|---:|---:|
| Teensy 4.0 a 600 MHz (conferir: medir) | 100,0 | 120,0 |
| Audio Board (SGTL5000) com fone 32 ohm, volume normal (conferir) | 20,0 | 40,0 |
| Sensores Hall DRV5056, 28 x 6 mA (máx. 10 mA, datasheet TI) | 168,0 | 280,0 |
| 2 x CD74HC4067 | 0,1 | 0,2 |
| LED bicolor (um lado aceso, 330 ohm) | 4,0 | 8,0 |
| Carregador + conversor, quiescente | 0,1 | 0,5 |
| **Total no trilho de 3,3 V** | **292,2** | **448,7** |

Para 4,0 h: típico 4,3 Wh → **1363 mAh**; pior caso 6,6 Wh → **2093 mAh**.

| Bateria | autonomia típica | pior caso |
|---|---:|---:|
| 1500 mAh | 4,4 h | 2,9 h |
| 2000 mAh | 5,9 h | 3,8 h |
| 2500 mAh | 7,3 h | 4,8 h |

Os 28 sensores Hall são mais da metade do consumo. O datasheet dá 6 mA típicos por sensor; medir a corrente real da placa é o primeiro teste do protótipo.
