# eTutti Student V2 · FIT_CHECK

16 nov 2026 · Code · responde à `SPEC.md` v1 (conceito de layout, acabamento Retrô).

Nada foi encomendado, impresso ou montado. O firmware da V2 (tela, microfone) não foi escrito neste ciclo.

## 1. Resultado

| Entrega | Estado |
|---|---|
| Placa nova (`kicad/`) | Feita a partir da placa da V1. DRC: 0 erros além das 3 larguras já aceitas na V1, 0 ligações faltando, igual ao esquema. O teclado (teclas, sensores, multiplexadores e trilhas) não mudou. |
| Lista de materiais e notas de compra | `fab/`, `COMPRAS.md` |
| Case em peças (`case/out/`, STEP e STL) | 20 peças: base, tampa, grade, espaçador, 12 botões, knob, caixa acústica, janela. |
| Renders (`case/renders/`) | planta, corte pelas fileiras, corte pelo alto-falante, isométrico, explodido, parede esquerda |
| Fit check | 202 pares de peças testados com sólidos exatos: **nenhuma interferência**. |
| Estudos | flexão (seção 4) e caixa acústica (seção 5) |

O relatório da eletrônica está em `ELETRONICA.md`.

## 2. Folgas medidas no modelo

### Teclado

| Fileira | Topo acima do tampo | Cabeça até a grade, solto | Cabeça até a grade, no fim do curso | SPEC |
|---|---:|---:|---:|---|
| 1 (frente) | 3,7 | 5,2 | **1,1** | 3,7 / 5,2 / 1,1 |
| 2 | 5,7 | 7,2 | 3,1 | 5,7 / 7,2 / 3,1 |
| 3 | 7,7 | 9,2 | 5,1 | 7,7 / 9,2 / 5,1 |
| 4 (fundo) | 10,7 | 12,2 | 8,1 | 10,7 / 12,2 / 8,1 |

| Medida | mm | SPEC |
|---|---:|---|
| Haste (Ø 5,6) no furo da grade (Ø 6,2), por lado | 0,30 | 0,3 |
| Botão da 1ª fileira apertado até a parede do poço | 5,00 | 5 |
| Aba do poço até a grade | 0,20 | 0,2 |
| Grade até o alojamento das teclas | 0,40 | 0,4 |
| Grade até a parede da tampa (menor distância) | 2,47 | — |
| Espaçador da grade até a tecla mais próxima | 6,55 | — |

Comprimento das hastes, do alojamento da tecla até a cabeça: 7,2 / 9,2 / 11,2 / 14,2 mm (fileiras 1 a 4).

### Interface, placa e fundo

| Medida | mm |
|---|---:|
| Placa até a parede da tampa | 0,50 |
| Topo do knob acima do tampo | 7,0 |
| Ponta do eixo do encoder acima do tampo | 1,8 |
| Knob até a tampa (em volta da luva; por baixo da saia são 0,8) | 0,50 |
| Tampa até o corpo dos encoders | 1,6 |
| Caixa acústica até a placa | 1,4 |
| Caixa acústica até a peça mais próxima em cima da placa | 2,3 |
| Caixa acústica até os encoders | 4,3 |
| Módulo da tela até os encoders | 3,5 |
| USB-C até a tampa / até a base | 0,22 / 0,45 |
| Jacks OUT e IN até a tampa / até a base | 0,40 / 0,50 |
| Módulo MicroMod até o piso da base | 2,2 |
| Peças do verso até a base (menor distância, num copo de parafuso da grade) | 0,24 |
| Bateria até as peças do verso | 0,70 |
| Bateria até as pernas dos encoders | 5,1 |

### Zona livre sob o alto-falante

A caixa acústica ocupa um círculo de Ø 31,4 mm em (37; 73,1), com o fundo 1,4 mm acima da placa. Dentro de um raio de 17,5 mm não há peça nenhuma em cima da placa; por baixo passam só trilhas. Os pads dos fios do alto-falante (J501) saíram de (46,5; 84) para (55,5; 79), fora da caixa. No verso, sob essa zona, fica a bateria.

## 3. Como o modelo foi resolvido, e onde ele se afasta do canvas

1. **Aberturas dos conectores.** O USB-C e os dois jacks ficam soldados na placa e atravessam a parede esquerda, então a tampa não desce sobre eles se os furos forem fechados. No modelo, cada abertura da tampa continua para baixo até a divisa com a base, e a base tem um dente que fecha esse rasgo. Fica uma linha de emenda vertical abaixo de cada conector (visível em `renders/parede.png`).
2. **Abertura do USB-C:** 9,6 × 3,9 mm, e não 9,2 × 3,6. Com a medida do canvas o canto do conector ficava a 0,03 mm da tampa.
3. **Borda do poço.** Parede a 12,5 mm dos centros das teclas (5 mm do botão) e raio de 2,5 em cima: a borda no tampo fica a 15,0 mm dos centros. O canvas desenha 15,5. O raio de baixo da aba saiu com 0,95 (a aba tem 2,0 de espessura).
4. **Parafusos da grade.** Nove estão nas posições do canvas. O décimo saiu de (150,77; 7,47) para (160,02; 7,47): na posição original há uma porta lógica dos sensores no verso da placa.
5. **Fixação da grade.** Parafuso M2 × 16 por cima, através da grade, de um espaçador de 11,6 mm e da placa, preso por uma porca sob a placa. A base tem um copo sob cada porca, e a placa apoia na borda do copo. Assim a base sai com 6 parafusos sem desmontar o teclado.
6. **Fixação da tampa.** 6 parafusos M2 × 14 por baixo, na borda: (88; 6,5), (74; 93), (6,5; 48,5), (8; 91,5), (238; 9), (238; 91). Atravessam base e placa e entram em postes da tampa.
7. **Knob.** O encoder escolhido tem eixo de 20 mm, que termina 1,8 mm acima do tampo. O knob tem uma luva escondida que desce 5,4 mm por um furo de Ø 9,2 na tampa e abraça o eixo. A saia fica 0,8 mm acima do tampo para o clique (curso de 0,5 mm); o topo fica a 7,0 mm.
8. **Tela.** O módulo fica preso por baixo da tampa em 4 postes, com o vidro 0,1 mm abaixo de uma janela de acrílico de 1 mm embutida no tampo. Liga-se à placa por um cabo de 4 vias.
9. **Bateria.** No piso da base, em x 13–63, y 56–90 (o canvas mostra y 58–92), sob o alto-falante.
10. **Faixas.** Não fazem parte da geometria; nos renders são uma película pintada.

## 4. Estudo: flexão da placa e da grade

Script `estudos/flexao.py`, resultados em `estudos/flexao.json` e `estudos/flexao.png`. Modelo de grelha de vigas (malha de 4 mm, FR-4 de 1,2 mm, E = 18 GPa), o mesmo usado no eTuttino e na V1. Uma tecla apertada de cada vez com 3 N. Alvo dos outros modelos: 0,05 mm por tecla.

Na V2 não há plate: as teclas apoiam direto na placa, então a placa nua é a estrutura real.

| Apoio da placa | Pior tecla | Média | Teclas acima de 0,05 mm |
|---|---:|---:|---:|
| A. Só a borda (10 parafusos da grade + 6 da tampa) | 0,206 mm | 0,130 | 28 de 28 |
| B. Borda + os 3 pinos da SPEC (fileira 2) | 0,067 mm | 0,038 | 6 |
| C. Borda + 4 pinos nos furos H5–H8 | 0,060 mm | 0,037 | 12 |
| **D. C + 3 pilares** | **0,049 mm** | 0,022 | **0** |

- **Só os pinos da SPEC não bastam** (6 teclas acima do alvo), e as três posições propostas caem sobre peças do verso da placa (sensor e capacitor das teclas vizinhas): um pino de Ø 5 ali invade entre 0,6 e 1,8 mm.
- **Proposta (caso D), já modelada na base:**
  - 4 pinos de Ø 5 com ponta de Ø 2 que entra nos furos que a V1 já tinha entre as teclas: (98,45; 52,67), (153,95; 31,31), (153,95; 63,35), (209,45; 52,67). Eles posicionam e apoiam a placa. Ficam escondidos sob a grade e nenhum parafuso passa por eles.
  - 3 pilares de apoio de Ø 4, sem furo: (127,5; 32,5), (182,5; 62,5), (182,5; 32,5).
- Com um toque forte de 10 N a pior tecla cede 0,16 mm. A pressão de um pino na placa fica em 0,6 MPa: não marca.
- Limite do modelo: um pino só segura a placa por baixo, e o modelo a prende nos dois sentidos. Os números são um pouco otimistas longe da tecla apertada.

### Grade

A grade só é empurrada por um dedo que erre o botão; os botões param na tecla, não na grade. Com 5 N entre dois botões, presa só pelos 10 parafusos da borda:

| Material da grade (1,6 mm) | Cede | |
|---|---:|---|
| Impressa (PETG) | 1,95 mm | encosta nas teclas depois de 0,4 mm |
| FR-4 | 0,22 mm | não encosta |
| Alumínio | 0,06 mm | não encosta |

Uma grade impressa não quebra, porque as teclas a seguram 0,4 mm abaixo, mas afunda de forma perceptível e pode ficar empenada. **Sugestão: grade de FR-4 de 1,6 mm**, pedida junto com a placa (máscara preta ou outra cor), como o plate da V1. Não é preciso reforço nem parafuso no meio.

## 5. Estudo: caixa acústica

Script `estudos/acustica.py`, resultados em `estudos/acustica.json` e `estudos/acustica.png`.

A caixa modelada tem **3,9 cm³** atrás do cone (interior de z 2,6 a 9,9, Ø 26), como a SPEC propôs. Fabricantes de alto-falantes de 28 × 5 mm raramente publicam todos os parâmetros, então o estudo usa um alto-falante nominal (ressonância de 450 Hz, Qts 1,2, Vas 15 cm³) e uma faixa em volta dele. Os números têm de ser refeitos com os dados da peça comprada.

| Caixa | Ressonância na caixa (faixa) | Nível em 262 Hz (Dó 4) | Nível em 523 Hz (Dó 5) |
|---|---:|---:|---:|
| 3,9 cm³ (SPEC, modelada) | 990 Hz (665–1500) | −23 dB | −9 dB |
| a mesma, com manta acústica | 940 Hz | −22 dB | −7 dB |
| 8 cm³ | 760 Hz | −18 dB | −3 dB |
| 12 cm³ | 675 Hz | −15 dB | 0 dB |
| 20 cm³ | 595 Hz | −13 dB | +2 dB |
| Sem caixa (o case inteiro, vazando) | 470 Hz | −9 dB | +3 dB |

- Com 3,9 cm³ a caixa é pequena para este alto-falante: a ressonância sobe de 450 Hz para perto de 1 kHz, com um pico de 8 dB ali. As fundamentais do teclado (196 a 659 Hz) saem fracas, e o som fica "de rádio".
- Triplicar o volume (12 cm³) dá de 7 a 9 dB a mais entre 200 e 520 Hz.
- Há lugar para crescer sem mexer na forma externa: ao lado e atrás do alto-falante, entre a placa e a tampa (z 1,4 a 16), a caixa pode avançar para x 54–66 e para os cantos em volta do círculo. Dá para chegar a cerca de 10 a 12 cm³ numa peça em forma de L.
- Qualquer que seja o volume, a caixa tem de ser estanque (o furo dos fios é fechado com uma gota de silicone) e o firmware deve cortar os graves abaixo de ~300 Hz no alto-falante, para o cone não bater.
- Sob a caixa, na placa: nada em cima; no verso, trilhas e a bateria.

## 6. Perguntas para o design

1. **Emendas na parede esquerda.** A solução dos rasgos com dentes da base (item 3.1) deixa uma linha vertical sob o USB-C, o OUT e o IN. Aceita? A alternativa é dividir tampa e base na altura dos conectores (z ≈ 2), o que muda a faixa cinza da base.
2. **Material da grade.** FR-4 de 1,6 mm (rígida, feita com a placa, cor da máscara) ou impressa (cor livre, mas afunda 0,4 mm sob o dedo)?
3. **Teclas sem plate.** A tecla magnética não tem pinos soldados: só dois pinos de plástico a posicionam na placa, e quem a segura é a grade, 0,4 mm acima. Com essa folga a tecla pode subir 0,4 mm ao puxar um botão e fazer barulho. Posso baixar a grade para 0,1–0,2 mm de folga (o poço passaria de 5,0 para 5,2 mm) ou prever uma espuma fina sob a grade?
4. **Pinos sob o teclado.** As três posições da SPEC caem sobre peças. Proponho os 4 furos que já existem mais 3 pilares (seção 4). De acordo?
5. **Décimo parafuso da grade** em x = 160 em vez de 150,8 (item 3.4): algum problema? Fica escondido sob a tampa.
6. **Borda do poço:** 15,0 mm dos centros (SPEC: 12,5 + raio 2,5) ou 15,5 (canvas)? Para 15,5 o raio de cima teria de ser 3,0.
7. **Janela da tela.** A janela de 30 × 15 é maior que a área acesa (21,7 × 10,9) e mais larga que o vidro do módulo (26,7): com acrílico transparente aparece a placa do módulo nas laterais. Uso acrílico fumê escuro (só os pixels aparecem), uma máscara preta por trás, ou a janela diminui?
8. **Faixa amarela da direita.** Começando em x = 237,5, a amarela fica em x 248,5–250,5, já sobre o chanfro lateral (que começa em x = 246). É intencional?
9. **Caixa acústica.** Mantém os ~4 cm³ redondos da SPEC ou posso crescê-la para 10–12 cm³ em L, por dentro (ganho de 7 a 9 dB nos graves)? Não muda nada por fora.
10. **Carga com o instrumento desligado.** Sem LED não há sinal de carga quando está desligado. Com o USB ligado o firmware pode manter só a tela acesa mostrando a carga. Serve?
11. **Troca da bateria.** Tirando os 6 parafusos de baixo a base sai inteira e a bateria fica à vista. Basta, ou quer uma tampa de acesso na base?
12. **Legendas "OUT" e "IN" e o logo** ainda não estão gravados no modelo (falta decidir entre gravar em baixo-relevo, 0,3 mm, ou pintar).
