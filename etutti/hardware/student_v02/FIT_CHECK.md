# eTutti Student V2 · FIT_CHECK

17 nov 2026 · Code · responde à `SPEC.md` **v3** (ciclo 3). Os relatórios dos ciclos 1 e 2 estão nos PRs #150 e #151/#152; aqui está o estado atual do modelo, com o que mudou no ciclo 3 em primeiro lugar.

Nada foi encomendado, impresso ou montado. O firmware da V2 não foi escrito; as notas para ele estão em `ELETRONICA.md`, seção 8.

## 1. Resultado do ciclo 3 (SPEC v3)

| Item da SPEC v3 | Estado |
|---|---|
| 1. Chanfro de 0,5 × 45° na boca externa dos três furos | Feito (`renders/parede_zoom.png`). A boca do USB-C fica com 13,8 × 8,0 e as dos jacks com Ø 7,5. A boca do jack OUT fica a 0,8 mm do começo da legenda "OUT" (a SPEC pede a legenda a 1,3 mm da borda do furo). |
| 2. Furo do USB-C de 12,8 mm | Feito (12,8 × 7,0, cantos R 3,5). Folga de 0,225 mm por lado na largura para um plugue no máximo da norma (antes 0,075). |
| 3. "STUDENT · V2" só pintado | Feito: sem corte na tampa; no modelo é a camada de tinta `out/tinta_marrom.stl` (0,05 mm de espessura, #8A3A22). |
| 4. "eTUTTI" com traço +0,1 mm | Feito: contorno de cada letra alargado em 0,1 mm de cada lado; o rebaixo continua com 0,4 mm de profundidade. Traço de cerca de 0,55 mm (antes 0,35) e letras de 3,6 mm de altura. |
| 5. Furos da grade retos, Ø 6,2 | Feito: o modelo e os Gerbers já eram retos. |
| 6. Aba do poço a 0,15 mm da grade | Feito (medido: 0,15). |
| 7. Cores da tinta | "eTUTTI", "OUT", "IN" e o filete: #2B2925. "STUDENT · V2": #8A3A22. Nos renders e em `out/tinta.stl` e `out/tinta_marrom.stl`. |
| 8. 1,4 mm livres entre as duas linhas do logo | Feito (medido nos sólidos: 1,40 mm). O logo inteiro ocupa 46,95 mm (y 26,5–73,5) dos 84 disponíveis: não foi preciso diminuir o "STUDENT · V2". |
| Placa | **Não mudou.** Nenhum item pedia mudança nela. |
| Fit check | 202 pares, **nenhuma interferência**; a placa entra por baixo na tampa sem contato nas 11 posições testadas, agora com o furo do USB-C de 12,8 mm. |

Nada foi encomendado, impresso ou montado. O firmware da V2 não foi escrito; as notas para ele estão em `ELETRONICA.md`, seção 8. O limite de plugues (seção 3) ainda não foi levado a nenhum manual: não há manual da Student V2.

## 2. Folgas medidas no modelo

### Teclado

| Fileira | Topo acima do tampo | Cabeça até a grade, solto | Cabeça até a grade, no fim do curso | SPEC v2 |
|---|---:|---:|---:|---|
| 1 (frente) | 3,7 | 5,45 | **1,35** | 3,7 / 5,45 / 1,35 |
| 2 | 5,7 | 7,45 | 3,35 | 5,7 / 7,45 / 3,35 |
| 3 | 7,7 | 9,45 | 5,35 | 7,7 / 9,45 / 5,35 |
| 4 (fundo) | 10,7 | 12,45 | 8,35 | 10,7 / 12,45 / 8,35 |

| Medida | mm | SPEC v2 |
|---|---:|---|
| Grade (z) | 11,35–12,95 | 11,35–12,95 |
| Grade até o alojamento das teclas | 0,15 | 0,15 |
| Profundidade do poço (tampo até a grade) | 5,25 | 5,25 |
| Espaçador da grade | 11,35 | 11,35 |
| Haste (Ø 5,6) no furo da grade (Ø 6,2), por lado | 0,30 | 0,3 |
| Botão da 1ª fileira apertado até a parede do poço | 5,00 | 5 |
| Aba do poço até a grade | 0,15 | 0,15 (SPEC v3) |
| Grade até a parede da tampa (menor distância) | 2,47 | — |
| Espaçador da grade até a tecla mais próxima | 6,55 | — |
| Parafuso M2 × 16 da grade: sobra além da porca | 0,25 | — |

As peças dos botões não mudaram: a haste vai do alojamento da tecla até a cabeça (7,2 / 9,2 / 11,2 / 14,2 mm). Com a grade 0,25 mm mais baixa, o trecho de haste à vista acima da grade é que cresceu 0,25 mm; a altura acima do tampo é a mesma.

### Parede esquerda e conectores

| Medida | mm |
|---|---:|
| Frente do USB-C, do OUT e do IN atrás da face interna da parede | 0,30 |
| Abertura do USB-C | 12,8 × 7,0, cantos R 3,5 |
| Chanfro na boca externa dos três furos | 0,5 × 45° |
| Furos dos jacks | Ø 6,5 |
| Material da tampa abaixo do furo do USB-C, até a divisa | 2,2 |
| USB-C até a tampa (menor distância, à borda do furo) | 1,79 |
| Jacks até a tampa | 0,81 |
| Placa (com tudo o que tem em cima) entrando por baixo na tampa | sem contato em nenhuma das 11 posições testadas, de 0,5 a 30 mm |
| Placa até a parede da tampa | 0,50 |

Não há mais rasgo na tampa nem dente na base. A divisa tampa/base continua em z = −4,0.

### Interface, placa e fundo

| Medida | mm |
|---|---:|
| Janela da tela | 24 × 13 (x 25–49, y 15,5–28,5) |
| Acrílico da janela | 25,7 × 14,7 × 1,0 |
| Filete abaixo da janela | 24 × 0,5, em y 30,0–30,5, rebaixo de 0,4 |
| "eTUTTI" | rebaixo de 0,4, letras de 3,6 mm, traço de ~0,55 mm, x 9,3–12,9 |
| "STUDENT · V2" | só tinta: letras de 1,3 mm, x 9,5–12,5, 1,4 mm depois do "eTUTTI" |
| Módulo da tela até os encoders | 3,5 |
| Topo do knob acima do tampo | 7,0 |
| Tampa até o corpo dos encoders | 1,6 |
| Caixa acústica até a placa | 0,8 |
| Caixa acústica até o jack IN | 1,0 |
| Caixa acústica até os encoders | 4,3 |
| Caixa acústica até a grade | 1,7 |
| Caixa acústica até a peça mais próxima em cima da placa | 4,6 |
| Peças do verso até a base (num copo de parafuso da grade) | 0,24 |
| Bateria até as peças do verso | 0,70 |
| Módulo MicroMod até o piso da base | 2,2 |

## 3. Profundidade de encaixe dos plugues

O batente de um plugue é a frente do próprio conector. Com o conector 0,3 mm atrás de uma parede de 2,0 mm, o corpo do plugue tem de entrar 2,3 mm no furo.

| Conector | Furo | Plugue que entra até o fim | Plugue mais grosso que o furo |
|---|---|---|---|
| USB-C | 12,8 × 7,0 | Corpo até 12,35 × 6,5 (o máximo da norma USB-C): folga de 0,225 mm por lado na largura e 0,25 na altura. | Para na parede: dos 6,65 mm da ponta entram 4,35. |
| OUT e IN (P2) | Ø 6,5 | Corpo até Ø 6,4 nos primeiros 2,3 mm. | Para na parede: dos 14 mm da ponta entram 11,7. |

- **O recuo funciona com plugues dentro dessas medidas**, e não foi preciso mexer na divisa.
- O chanfro de 0,5 × 45° na boca externa dos três furos guia o plugue; a folga do USB-C na largura subiu para 0,225 mm por lado com os 12,8 mm.
- **Limite a registrar no manual:** corpo do plugue de até 12,35 × 6,5 mm no USB-C e Ø 6,4 mm no P2.
- Com um plugue que não passa no furo o contato fica incerto: no P2 a ponta não chega à mola do fundo; no USB-C a trava não fecha. Cabos de fone moldados costumam ter Ø 6 ou menos na ponta; plugues de metal de cabos de áudio têm de 7 a 10 mm e não entram.
- São estimativas pelas medidas dos conectores e da norma. Só o protótipo confirma.

Plugues mais grossos continuam fora (decisão da SPEC v3: sem rebaixo externo em volta dos furos).

## 4. Como o modelo foi resolvido, e onde se afasta da SPEC ou do canvas

1. **Logo.** Em Michroma (arquivo e licença em `case/fontes/`), com os tamanhos e espaçamentos da prancha "Área de interface": "eTUTTI" com corpo de 4,4 mm e "STUDENT · V2" com 1,7 mm, de pé, lidos da frente para o fundo, centrados entre y 8 e 92, com 1,4 mm livres entre as duas linhas. Só o "eTUTTI" é rebaixo.
2. **Traços.** "eTUTTI" com o contorno alargado em 0,1 mm de cada lado: traço de cerca de 0,55 mm e letras de 3,6 mm, no limite confortável de um rebaixo impresso em resina ou MJF. "STUDENT · V2" é só tinta: letras de 1,3 mm com traço de cerca de 0,15 mm, o que a tampografia tem de reproduzir (pergunta 1).
3. **OUT e IN.** Letras de 2,0 mm de altura (Arial Bold), começando 1,3 mm à direita de cada furo, de z 1,8 a 3,8, abaixo dos sulcos (o mais baixo fica em z 7,6).
4. **Janela e filete.** Seguem a SPEC (janela em y 15,5–28,5, filete em y 30,0). O texto da prancha "Área de interface" diz "tela 15,5–30,5, filete em 32", mas o desenho da mesma prancha bate com a SPEC.
5. **Furos da grade retos.** A SPEC v1 pedia chanfro de 0,3 mm; em FR-4 o furo é só furado, e a SPEC v3 confirma.
6. **Cobre sob a máscara da grade.** As duas faces da grade têm cobre contínuo sob a máscara (recuado 0,5 mm da borda e dos furos), para o preto ficar uniforme. Sem cobre, a máscara sobre o laminado fica translúcida e mais clara.
7. **Caixa acústica.** Em planta é um retângulo de x 17,5–66 e y 57,5–88,7, entre os dois parafusos. É baixa sob o alto-falante (interior de z 1,8 a 8,7; a borda do alto-falante apoia no teto) e alta ao lado dele, de x 54,5 a 66 (interior até z 14,4): um L visto de frente. Tem 4 nervuras internas com janelas, que sustentam o teto na impressão e evitam que ele vibre. O furo dos fios fica na parede da frente, em x 49,5.
8. **Pads dos fios do alto-falante (J501).** Foram para (48,1; 94,5), na frente da caixa, porque a caixa nova cobria a posição anterior.
9. **Renders.** As faixas e a tinta dos rebaixos são películas pintadas, fora da geometria da tampa. O corte pelo alto-falante passa em x = 40, a 3 mm do eixo, porque no eixo há uma nervura.

## 5. Estudo: caixa acústica em L

Script `estudos/acustica.py`, resultados em `estudos/acustica.json` e `estudos/acustica.png`. O alto-falante continua sendo um nominal de 28 × 5 mm (ressonância 450 Hz, Qts 1,2, Vas 15 cm³); os números têm de ser refeitos com os dados da peça comprada.

| Caixa | Volume | Ressonância na caixa (faixa) | Nível em 262 Hz (Dó 4) | Nível em 523 Hz (Dó 5) |
|---|---:|---:|---:|---:|
| Redonda da SPEC v1 | 3,9 cm³ | 990 Hz (665–1500) | −22,5 dB | −8,6 dB |
| **Em L, como modelada** | **10,4 cm³** | **700 Hz (505–1015)** | **−16,1 dB** | **−0,6 dB** |
| A mesma, com manta acústica | ~12 cm³ | 675 Hz | −15,3 dB | +0,2 dB |

- Ganho da caixa em L sobre a redonda: **+6,4 dB em 262 Hz e +8,0 dB em 523 Hz**. O pico na ressonância cai de 8,4 para 5,5 dB.
- O corte de graves do firmware em ~300 Hz (tomado aqui como de 2ª ordem) tira mais 4,3 dB em 262 Hz e 0,4 dB em 523 Hz.
- A oitava de baixo do teclado (Sol 3 a Fá♯ 4) continua fraca no alto-falante: é o limite de um cone de 28 mm. No fone e na saída OUT nada disso se aplica.
- A peça é fechada, com teto. Em resina ou MJF sai como está (o pó ou a resina saem pela boca de Ø 26). Em filamento, o teto é impresso em ponte sobre as nervuras, com vãos de até 8,5 mm.
- A borda do alto-falante precisa vedar no teto da caixa: a junta de espuma da frente o aperta contra o assento, mas um fio de cola ou de silicone ali garante a estanqueidade.

## 6. Estudo: flexão (sem mudança)

- Placa, caso D (4 pinos Ø 5 + 3 pilares Ø 4, nas posições da SPEC v2): pior tecla **0,049 mm** com 3 N; 0,16 mm com 10 N.
- Grade em FR-4: com um dedo apertando 5 N entre dois botões ela cede até 0,22 mm, mais que a folga de 0,15 mm, e então encosta nos alojamentos das teclas, que a seguram. Não é defeito: só acontece com o dedo fora do botão.

## 7. Perguntas para o design

1. **Tampografia do "STUDENT · V2".** O traço é de cerca de 0,15 mm, e muitos serviços de tampografia pedem 0,2 mm ou mais. Como a letra é só tinta, posso engrossar o traço em 0,05–0,1 mm sem tocar em nada mais (a folga de 1,4 mm ao "eTUTTI" é medida na borda das letras). Engrosso, ou confirma-se antes com o fornecedor?
2. **Legenda "OUT".** O chanfro deixa a boca do furo com Ø 7,5 e a legenda a 0,8 mm dela. Mantém, ou afasto "OUT" e "IN" 0,5 mm para a direita para sobrar mais liso entre o chanfro e a letra?
3. **Manual.** O limite de plugues (12,35 × 6,5 mm no USB-C, Ø 6,4 mm no P2) vai para o manual da Student V2 quando ele existir. Algum dos manuais atuais (eTuttino) também deve citá-lo?
