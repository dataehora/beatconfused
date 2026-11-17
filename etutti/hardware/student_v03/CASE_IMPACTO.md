# Student V3 — o que a placa V3 muda para o case (19 nov 2026)

Resposta do Code ao "o case será revisto depois" do J. **Não toca no case da V2** (`student_v02/case/`): só mede o que mudou e
lista as perguntas para o Chat escrever a SPEC v4. Referência: z = 0 no topo da placa, a placa tem 1,2 mm (fundo em z = −1,2),
x/y como na SPEC da V2 (as posições x, y dos conectores não mudaram: a placa só virou as peças).

## 1. Conectores da parede esquerda: passaram para o fundo da placa

| | V2 (no topo) | V3 (no fundo) | Faixa vertical do furo na parede |
|---|---|---|---|
| USB-C (y = 16,0) | centro z = **+1,7**, furo 12,8 × 7,0 | centro z = **−2,9** (−1,2 − 1,7) | −6,4 … +0,6 |
| OUT (y = 36,0) | eixo z = **+2,8**, furo Ø6,5 | eixo z = **−4,0** (−1,2 − 2,8) | −7,25 … −0,75 |
| IN (y = 60,0) | idem | eixo z = **−4,0** | −7,25 … −0,75 |

Os valores de V3 são a V2 espelhada em torno da placa (a mesma altura do conector sobre a face em que ele está). Confirmar com a
altura real das peças (HRO TYPE-C-31-M-12 e XUNPU PJ-327A) quando houver amostra.

**O ponto delicado:** o plano de divisão base/tampa da V2 é **z = −4,0** (`Z_SPLIT`). O eixo dos jacks cai exatamente nesse plano e o
furo do USB-C o atravessa (−6,4 … +0,6). Na V2 os três furos eram fechados e ficavam inteiros na tampa; agora cada furo fica **metade
na tampa, metade na base**. Os conectores pendem para baixo da placa (USB-C até z ≈ −4,9, jacks até ≈ −6,3), então entram na região da base.

## 2. Altura útil da base

O piso interno da base fica em z = −8,1 (`Z0` = −10,1, piso 2,0). Peças do fundo da placa: módulo MicroMod até z ≈ −5,9 (4,7 mm abaixo do fundo, medido no modelo), jacks até ≈ −6,3, USB-C até ≈ −4,9. **Cabem com folga de ≥ 1,8 mm.**

## 3. J401 (cabo da tela) e a fenda

J401 (JST SH de 4 vias) está no fundo em (35,5; 36,5) e a placa tem uma **fenda de 7 × 2,5 mm** (x 32,0 … 39,0, y 29,92 … 32,42) para o cabo subir até o módulo OLED na tampa. A janela da tela é (25,0 … 49,0; 15,5 … 28,5): a fenda fica 1,4 mm à frente dela. O cabo passa entre a janela e a fenda, por cima da placa; verificar o raio de curvatura do cabo (JST SH, ~15 mm de comprimento) no modelo.

## 4. Perguntas para o design (Chat)

1. **Divisão dos furos:** deixar o plano de divisão em −4,0 e cortar o mesmo furo nas duas metades (a tampa ganha a metade de cima, a base a de baixo), ou mover o plano para fora da faixa dos conectores (por exemplo z = −7,4, abaixo dos jacks)? A segunda opção deixa os furos inteiros numa peça, mas muda a altura da base e da tampa.
2. **Entrada da placa:** como os conectores pendem da placa, a placa não entra mais "de baixo para dentro da tampa" sem a base: confirmar a ordem de montagem (placa na base, tampa por cima).
3. **"Não ter a base do teclado abaixo do case":** não entendi com certeza. Se for a grade de FR-4 (z 11,35 … 12,95), ela continua sobre os sensores. Se for a parte da base sob o teclado, precisa de definição.
4. **R202** mudou de lugar (12,4; 12,75) na placa (antes 14,4; 19,9): não interfere no case.
