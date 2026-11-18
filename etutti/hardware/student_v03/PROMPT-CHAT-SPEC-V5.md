# Prompt para o Claude Chat — SPEC v5 do case da Student V3

Cole o texto abaixo no Chat (o mesmo chat da SPEC v4). Ele é autossuficiente, mas o Chat deve ter à mão
`etutti/hardware/student_v03/SPEC.md` (v4) e `etutti/hardware/student_v03/case/FIT_CHECK.md`.

---

Olá. O Code atendeu a SPEC v4 do case da Student V3 (PR #166, no `main`). O modelo foi gerado e o fit check
(245 pares) deu **0 interferências**. Nada foi impresso e a V2 não foi alterada. O relatório completo está em
`etutti/hardware/student_v03/case/FIT_CHECK.md` (seção 3 e "Perguntas para o design"). Preciso que você escreva a
**SPEC v5**, decidindo os cinco achados abaixo (mais duas pendências menores). Para cada um, dou o número medido e a
minha recomendação; decida, ou proponha outra saída.

## Estado atual (resumo)

- Tampa de z −10,1 a 14,5 (case de 24,6 mm), sem emenda na parede, chanfro inferior de 6 × 3,5 mm na própria tampa.
- Fundo = bandeja de 2 mm dentro da tampa (borda, nervuras em grade de 12 mm, copos para porcas, rebaixo do H101,
  bateria em x 19,5–69,5). Entra por baixo com folga de 0,15 mm.
- USB-C e jacks na parte de baixo da placa (`USB_Z` −2,9, `JACK_Z` −4,0), furos inteiros na tampa.
- OLED girado 180°, knobs sem luva, parafusos da grade escareados (M2 × 16), H101 com M2,5 nylon.

## Achados que precisam de decisão

**A. Tampa fina sobre a grade na frente e no fundo — 0,51 mm.**
O chanfro de 6 × 3,5 ainda está subindo onde a grade chega (a 4,47 mm da parede externa), então a tampa sobre a
grade fica com 0,51 mm nessas duas faixas. Não é imprimível em MJF nem em resina. Recomendo chanfro de **4,0 × 3,5**
só nas faixas da frente e do fundo (o resto fica 6 × 3,5), ou subir o teto 0,5 mm. Qual?

**B. Eixo do encoder EC11E18244AU: 24,5 mm, não 20 mm.**
É o que mostram o modelo EasyEDA e o datasheet do fornecedor. Ele sobra ~3 mm acima do topo do knob (SPEC v4 supõe
20). Opções: (1) cortar o eixo em 20 mm (4,5 mm de serra por encoder, serviço do J); (2) knob 3 mm mais alto;
(3) trocar por um encoder de eixo 20 mm. Recomendo (1) para o protótipo e (3) se a V3 for para série.

**C. Flexão da placa com a bandeja no ar.**
Com apoios rígidos a placa chega a 0,049 mm sob 3 N (meta ≤ 0,05). Mas a bandeja de 2 mm presa só pelos 6 parafusos
cede 0,26 mm a 2 mm sob 3 N; só vale com apoio no contorno (0,04–0,06 mm). Recomendo uma **prateleira interna na
parede da tampa** (ressalto de ~1,5 × 2 mm onde a bandeja se apoia) em vez de engrossar a bandeja.

**D. Caixa acústica: 9,75 cm³** (V2: 10,4 cm³; perda estimada de 0,3–0,4 dB nos graves).
Sem um bloco alto à esquerda do alto-falante seriam 7,9 cm³. Aceita como está, ou quer reservar mais volume (por
exemplo, mover a bateria ou o OLED)?

**E. Postes da tela a 0,06 mm do chanfro do teto.**
Está no limite da tolerância de impressão. Recomendo recuar os postes 0,5 mm ou usar um chanfro menor ali.

## Pendências menores

1. **Parafusos escareados da grade.** Não confirmei se o pedido de placa da JLCPCB aceita furo escareado para a
   placa da grade (desenho em `case/GRADE_ESCAREADA.md`). Alternativa: escarear em casa. Qual vale para a SPEC?
2. **Boca do conector J401** (cabo da tela): não consegui confirmar para que lado ela abre; fica para conferir na
   amostra física. Basta registrar na SPEC como "a confirmar".

## O que peço

Escreva `SPEC.md` v5 com "Mudanças desde a versão anterior" e uma lista de tarefas para o Code. Se alguma decisão
depender de medir uma peça real (encoder, XUNPU, HRO, J401), diga qual e como o J deve medir.
