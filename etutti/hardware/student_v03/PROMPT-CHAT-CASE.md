# Prompt para o Claude Chat — SPEC v4 do case do eTutti Student V3

Cole isto no Chat. (O Code já gerou `CASE_IMPACTO.md` com as medidas; o resumo está abaixo.)

---

Oi. Preciso da **SPEC v4 do case do eTutti Student**, agora para a **placa V3**. O Code (que modela, confere e responde em `FIT_CHECK.md`) vai regenerar o case a partir da sua SPEC. Peço, como nas versões anteriores: uma SPEC versionada com "Mudanças desde a versão anterior" e "Tarefas para o Code" (marcadas Design). Responda em português.

## O que mudou da V2 para a V3 (a placa está pronta para encomendar)

A V3 é a V2 com **tudo o que podia ir para baixo da placa** montado pela JLCPCB (só o fundo). **Contorno, 10 furos de fixação, teclado (28 Gateron KS-20 magnéticas, passo 18,5), grade de FR-4 e as posições x, y dos conectores não mudam.** O que muda:

1. **Conectores da parede esquerda foram para o FUNDO da placa:** USB-C, OUT (jack 3,5 mm) e IN (jack 3,5 mm). Posições y iguais às da V2 (USB y = 16,0; OUT y = 36,0; IN y = 60,0, no eixo da SPEC, y para o músico), mas em z diferente. Referência: z = 0 no topo da placa, placa de 1,2 mm (fundo em z = −1,2).

   | | V2 (topo) | V3 (fundo) | faixa do furo na parede |
   |---|---|---|---|
   | USB-C | centro z = +1,7, furo 12,8 × 7,0 | centro z ≈ **−2,9** | −6,4 … +0,6 |
   | OUT / IN | eixo z = +2,8, furo Ø6,5 | eixo z ≈ **−4,0** | −7,25 … −0,75 |

   (V3 = V2 espelhada em torno da placa; confirmar com a altura real das peças quando houver amostra.)

2. **Divisão base/tampa:** na V2 ela é em **z = −4,0**. Na V3 esse plano passa **exatamente pelo eixo dos jacks** e atravessa o furo do USB-C. Na V2 os furos eram fechados e ficavam inteiros na tampa (a tampa caía sobre as tomadas); agora cada furo ficaria metade na tampa e metade na base.
3. **Altura da base:** o piso interno da V2 está em z = −8,1 (base de −10,1; parede 2,0; piso 2,0; tampa 2,0; topo em 18,2). As peças do fundo da placa: módulo MicroMod até z ≈ −5,9 (4,7 mm abaixo do fundo), jacks até ≈ −6,3, USB-C até ≈ −4,9. Cabem com folga de ≥ 1,8 mm.
4. **Tela OLED:** o conector do cabo (JST SH de 4 vias, J401) está agora **no fundo**, em (x 35,5; y 36,5), e a placa tem uma **fenda de 7 × 2,5 mm** (x 32,0 … 39,0; y 29,92 … 32,42) para o cabo subir até o módulo OLED preso na tampa. A janela da tela da V2 é (25,0 … 49,0; 15,5 … 28,5): a fenda fica 1,4 mm à frente dela.
5. **Fixação do módulo MicroMod (H101):** furo liso de 2,7 mm; o parafuso M2,5 entra **pelo topo**, com um espaçador de nylon de 2,5 mm, o módulo e uma porca por baixo. A base precisa de espaço para a porca e para tirar o módulo.
6. **Resto:** os 2 encoders (volume e registro) continuam em cima, soldados pelo usuário (eixo de 20 mm, como na V2). Uma peça pequena (R202) mudou de lugar, sem efeito no case. Continuam valendo os parafusos não ferrosos perto dos sensores Hall e os pilares do case (flexão ≤ 0,05 mm a 3 N).

## Decisões que preciso de você (com a sua recomendação)

1. **Furos de USB-C e jacks:** (a) manter o plano de divisão em −4,0 e cortar o mesmo furo nas duas metades, ou (b) **mover o plano de divisão** para fora da faixa dos conectores (por exemplo z ≈ −7,4, abaixo dos jacks), deixando os furos inteiros numa peça? Qual a melhor para impressão, acabamento Retro e montagem? E os furos continuam "fechados" (a tomada fica 0,3 mm atrás da parede) ou passam a ser abertos?
2. **Ordem de montagem:** como as tomadas pendem da placa, a placa não entra mais "de baixo para dentro da tampa". Confirme a ordem (por exemplo: placa na base, depois a tampa por cima) e como a grade de FR-4, a tela e a caixa acústica entram.
3. **"Não ter a base do teclado abaixo do case":** o J disse que o case será revisto "incluindo alteração para não ter a base do teclado abaixo do case". O Code não entendeu com certeza. Se for a grade de FR-4 (z 11,35 … 12,95), ela continua sobre os sensores. Se for a parte da base sob o teclado, precisa de definição. Explique o que o J quer ou pergunte a ele.
4. **Cabo da tela:** o caminho entre a fenda e o módulo OLED, o suporte do cabo e o raio de curvatura (JST SH, ~15 mm de cabo).
5. **Base:** espaço para o módulo MicroMod removível e para a porca do H101; posição da bateria (503450, 3 fios com NTC) e do alto-falante (28 × 5 mm) agora que o fundo da placa tem peças.
6. Qualquer coisa que a V3 permita simplificar no case.

Peço também: a lista de **perguntas para o Code** (medidas que ele deve conferir no modelo) e o que depende de **amostra física** (alturas reais do USB-C e dos jacks).

Material de apoio no repositório: `etutti/hardware/student_v03/CASE_IMPACTO.md`, `README.md`, `kicad/student_v03.kicad_pcb`, e o case da V2 em `etutti/hardware/student_v02/case/` (`case.py`, `FIT_CHECK.md`, SPEC v3).
