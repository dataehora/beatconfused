## Peças montadas em casa: modelo na cena do instrumento (`student_v04/case`)
| Peça | Modelo na cena | Fiel? |
|---|---|---|
| OLED Adafruit 326 | placa com orelhas, furos, vidro, área ativa, corpos dos 2 SH4 | **fiel** (medidas lidas do arquivo de placa da Adafruit) |
| Encoders EC11E18244AU (C202365) | caixa 12 x 13,4 x 4,5 + eixo D com chato | **só caixa/cilindro** (STEP da EasyEDA já baixado em `student_v03/case/modelos/`, não ligado) |
| MicroMod Teensy | cartão 22 x 22 mais uma caixa | **só caixa** |
| Alto-falante Dayton CE28MB-8 | cilindro Ø28 x 4,5 | **só cilindro** |
| Bateria 503450 | caixa 34 x 50 x 5 | **só caixa** |
| Teclas KS-20 Orange | corpo, aba cônica e haste | **aproximado** (desenho da Gateron; o STEP KS-20T existe em `fornecimento/gateron/`) |
| Parafusos, porcas, pés | cilindros e hexágonos | só formas |
Pendência de fidelidade, sem efeito na compra: ligar os STEP do EC11E, do MicroMod e da KS-20 à cena (pedido ao design).

## Riscos
1. A regra de colocação da EasyEDA foi deduzida dos dados dos 34 modelos, não de documentação: a figura da JLCPCB pode diferir nos 4 códigos acima.
2. O marcador do pino 1 foi achado na geometria; um marcador só pintado (sem relevo) não aparece.
3. A pré-visualização real da JLCPCB é a conferência final (lista na folha de cotação de cada placa).
