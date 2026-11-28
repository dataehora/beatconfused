# Liebling (Batschauer) — SPEC R3MIC (conceito)

## R3MIC — decisões do J (28 nov, tarde): o que vale sobre o resto do texto

O bloco R2MIC e as seções 1 a 13 abaixo continuam valendo **exceto** onde este bloco manda diferente (forma, ganho, medidor, estéreo, sem case).

**Fase 1 (projeto, sem comprar) continua.** Protótipo visual: `minimic/design/liebling_r3.html` (gerado por `proto_r3.py`; o `liebling_r2.html` fica como histórico).

### 1. Forma: a placa é a continuação do corpo do celular
- Placa **72 × 22 × 1,2 mm**, o **plugue USB-C macho no centro do lado maior** (largura 72 mm ≈ a de um celular comum), saindo do lado de 72 mm. Plugada, a placa vira o "queixo" do celular, em linha com o corpo, em vez de uma haste que se projeta para fora. Cabe no celular em pé numa estante ou num pau de selfie; sem cabo de extensão.
- **Firme e integrado:** plugue de carcaça metálica com as quatro pernas soldadas na placa (THT, ou meio-montado em entalhe), e a placa de 1,2 mm encostada no corpo do celular. A `mic-design` estuda a alavanca lateral (peso ~6-8 g centrado no plugue) e a folga para capinha fina; a `mic-eletronica` escolhe o plugue pela resistência mecânica (o mais robusto que a JLCPCB monte, ou soldado à mão se for o caso).
- A placa tem 72 mm de largura: celulares mais largos (até ~77 mm) deixam a placa um pouco mais estreita que o corpo, sem problema.

### 2. Ganho: duas barras de LED, sem potenciômetro
- **Barra de ganho** (embaixo, a mais distante do celular): **15 LEDs brancos 0603, fracos** (cor e brilho diferentes do medidor, de propósito), posições de **0 a +42 dB em passos de 3 dB**.
- **Dois botões, − e +**, nas pontas da barra. Cada toque muda **1,5 dB** (o LED aceso anda meio passo: **dois LEDs vizinhos acesos** = meia posição); segurar repete. Resolução real **1,5 dB**, melhor que um slider de 15 mm.
- O **último ganho fica guardado** (RP2040 sem EEPROM: um setor de flash, gravado só 3 s depois da última mudança, com rodízio). Padrão de fábrica: **+12 dB**.
- Sem potenciômetro, sem ADC, sem cursor móvel: **menos uma peça mecânica**, e a barra branca vira parte do desenho. Os 15 LEDs acendem por **charlieplexing** (5 pinos + 5 resistores; brilho fraco é o que se quer), proposta que a eletrônica confirma contra 2 × 74HC595 (Basic).

### 3. Medidor de nível (barra de cima, perto do plugue): colorido e brilhante
- **12 LEDs 0805 (SAT em 1206)**, da esquerda para a direita:

| LED | cor | dBFS (pico, depois do ganho) | significa |
|---|---|---|---|
| 1-6 | verde | −42, −36, −30, −24, −20, −16 | baixo → bom |
| 7-9 | amarelo | −12, −9, −6 | forte: **alvo dos picos do bayan** |
| 10 | vermelho | −3 | limite |
| 11 | vermelho | 0 | no teto |
| 12 | **azul, "SAT"** | — | **saturou** |

- **SAT é o degrau logo depois do último vermelho.** Acende (azul, piscando a ~8 Hz) quando **(a)** a saída chegou a 0 dBFS e **cortou**, ou **(b)** o próprio sensor passou de ~128 dB SPL (o ganho não resolve isso). Dura ~2 s depois do evento. **Enquanto SAT pisca, os dois vermelhos piscam juntos**: o corte fica inconfundível mesmo de longe.
- **Texto na serigrafia:** só "SAT" sob o LED (o azul já é claro; **sem** frase adicional). Cada LED tem o número em dBFS impresso (o protótipo confere cor × número).
- O medidor mostra o **máximo entre L e R** (qualquer canal que sature acende o SAT).

### 4. Par estéreo
- **Dois IM72D128** (PDM, **uma só linha de dados**, selecionados por L/R), nas **duas pontas da placa, a 59 mm um do outro**, cada um com furo acústico e **espuma Ø10**. USB **2 canais, 24 bits, 48 kHz**, ganho ligado nos dois, o mesmo caminho de sinal.
- Par espaçado (AB) de omnis: imagem estéreo moderada (diferença de tempo máxima de 59 mm / 343 m/s ≈ 0,17 ms), **bem compatível com mono** (soma sem filtro de pente forte), natural para um instrumento largo como o acordeon (lado dos graves × lado dos agudos).
- **Custo:** um sensor a mais (+US$ a conferir), a decimação de dois canais no RP2040 (a simulação F1 mede a carga) e o dobro de banda USB (288 kB/s, longe do limite do Full Speed). Consumo continua ≤ 100 mA (conta em `POWER.md`).

### 5. Sem case, mas com cara de produto
- **Nenhum case.** O acabamento é a PCB: máscara **preta fosca**, **ouro (ENIG)** exposto em marca "Liebling" em cobre, contorno dourado interno, anéis dourados nos furos dos microfones, chanfros de 3 mm nos cantos da frente e 1,5 mm nos de trás, serigrafia branca mínima (número em dBFS, +, −, L, R, SAT, "LEVEL dBFS", "GAIN dB", "BATSCHAUER" e a marca; só a frase explicando a saturação fica fora). Tudo isso já está no protótipo.
- Case mínimo só se o J pedir depois (faixa de silicone fina no fundo, sem tampa). Em aberto na §6.
- A espuma cola sobre cada furo (**3 pares por embalagem**).

### 6. Graves e onde ainda perdemos para um estúdio grande
**Graves:** o sensor **não limita** (IM72D128VV01: queda em 11 Hz, a E1 do bayan é 41 Hz). Meta R3MIC: **−3 dB em ≤ 15 Hz** na cadeia inteira (sensor → decimação → bloqueio de DC em ~3 Hz → USB), medida na simulação F1. Perdas possíveis ficam **fora do sensor**: (a) o filtro passa-altas que o sistema/app do celular aplica (Android: fonte UNPROCESSED; iOS: modo de medição; **depende do app de gravação**, a página futura deve dizer isso); (b) vibração e manuseio pelo pau de selfie (graves de manuseio que o estúdio isola com suporte elástico).

Onde ainda estamos **abaixo de um estúdio grande** (conta honesta):

| Item | Liebling | Estúdio grande | Perda real? |
|---|---|---|---|
| Ruído próprio | ≈ 22 dB(A) por canal | 7-15 dB(A) (condensador grande) | **pequena**: o ruído da sala (30-40 dB(A)) é maior que os dois |
| Padrão polar | omni fixo | cardioide, figura 8 etc. | **sim**: mais vazamento de outros instrumentos e da sala; só a posição resolve |
| Estéreo | AB fixo de 59 mm | escolhe XY / ORTF / spaced, a qualquer distância | **parcial**: um par só, mas bom para um instrumento só |
| Isolamento mecânico | rígido no celular | suporte elástico | **sim** (graves de manuseio), a medir; mitigação por filtro < 15 Hz opcional no firmware |
| Pré-amplificador e conversor | digitais dentro do sensor, 24 bits | pré de alta classe + conversor | **pequena** |
| Tamanho da cápsula | ~4 mm | 25 mm | **fora de eixo** nos agudos e comprimento de onda dos graves: sem perda de graves para omni |
| Processamento do celular | depende do app | nenhum | **fora do nosso controle** (ver acima) |
| Distância e posição | presa ao celular | livre | **sim**, é a natureza do produto |

Conclusão: com o IM72D128 e o ganho de 0 a +42 dB, o que fica abaixo do estúdio é **polar, isolamento e posição**, não graves nem ruído. Isso é dito na página do produto.

### 7. Ajustes nas tarefas (§12)
- **Eletrônica:** E1 inclui o IM72D128 duas vezes na tabela (preço × 2, estoque), plugue USB-C pela resistência mecânica, botões táteis SMD baixos (Basic), LEDs 0603 branco, 0805 R/Y/G, 1206 azul; **sem potenciômetro**. E3: 12 + 15 LEDs, 2 botões, 2 microfones numa linha PDM, GPIOs ≈ 21 (PDM 2, medidor 12, charlieplex 5, botões 2). E4: posicionamento no contorno 72 × 22.
- **Firmware:** F1 simula **dois** canais; F2 faz a rampa de ganho em passos de 1,5 dB com meio LED, ganho guardado em flash, SAT com os vermelhos piscando, UAC 2 canais.
- **Design:** D1 = estudo de alavanca do plugue no centro, folga para capinha e para o celular em pé; D3 = a arte da PCB (ENIG, marca, contorno); D2 (espuma) vale para 2 furos.

### 8. Decisões finais do J (28 nov) — R3MIC fechada para detalhar
1. **Layout fixo**, também em paisagem (sem acelerômetro, sem inverter a barra).
2. Máscara **preta fosca**, só ela.
3. **Nenhum case**, nem faixa de silicone.
4. Sem o texto "SATUROU: BAIXE O GANHO": o "SAT" azul basta.

**Decisão do J (28 nov): seguimos apenas com a A.** B e C ficam registradas e congeladas. O prompt para o Code está em `minimic/PROMPT-R3MIC.md`.

### 10. Decisões do J na Fase 1 (28 nov, depois da etapa 1) — valem sobre o resto
1. Placa de **1,6 mm** (era 1,2). O **plugue é soldado pela JLCPCB**; só se for impossível, à mão na Fase 2. Isso pode levar a montagem de Economic para **Standard**.
2. **Sem cola e sem epóxi em lugar nenhum** (nem na junção do plugue). Pendente: como a espuma fica presa (ver relatório de eletrônica).
3. **Calço macio de 0,5 mm entre a placa e o celular: aceito.** A JLCPCB não monta calço; como fazê-lo sem cola é pendente.
4. **IM72D128VV01 no projeto, independentemente de estoque.** Como comprá-lo (Global Sourcing, consignação, outra origem) é estudo da eletrônica.
5. **Serigrafia:** valem os textos do protótipo ("LEVEL dBFS", "GAIN dB", "BATSCHAUER", marca, números); só a frase de saturação sai.
6. **Clock do RP2040 a 153,6 MHz autorizado** (fallback documentado: 120 MHz com PDM a 2,4 MHz).
7. **Mudo de 50 ms no arranque aprovado** (por causa do DC do canal com SELECT em VDD).
8. Pendentes de decisão do J: pico por amostra × verdadeiro; toolchain (pico-sdk × arduino-pico); UAC1 × UAC2 primeiro; tensão dos LEDs (3,3 V × 5 V com ULN2003A).

### 9. Versões B e C (variantes, só para comparar)
Página única com A, B e C: `minimic/design/liebling_r3_comparacao.html` (gerada por `proto_comp.py`, que usa `proto_r3.py` e `proto_b.py`).

**Versão C (cápsulas de diafragma grande, Ø16 mm, placa 84 × 24 mm, ~12 mm de altura):** não encontrei componente de diafragma grande comprável **com ficha aberta**; só catálogos de fabricante de cápsula (14 a 25,4 mm, omni/cardioide, JFET, Mylar de 3 ou 6 µm, resposta "20-20000 Hz" e "130 dB SPL" genéricos, sensibilidade "sob medida", sem SNR, sem preço). Outro fabricante anuncia 14 e 16 mm com 50 Hz a 20 kHz e SNR > 58 dB (pior que o MEMS). O condensador verdadeiro de 1" exige 60 a 80 V de polarização (phantom de 48 V no estúdio): não cabe no microfone alimentado só pelo USB. Conclusão: **para graves só a A tem prova em ficha**; a C é hipótese.
**PUI Audio AOM-6738P-R (avaliada e descartada para a C):** é uma cápsula de 9,7 × 6,9 mm, de diafragma pequeno (classe da B, não da C), omni, −38 dBV/Pa ±3 dB, SNR 60 dB (ruído ≈ 34 dB(A)), sobrecarga 110 dB SPL, 30 Hz a 15 kHz (DigiKey) ou 20 Hz a 20 kHz (Farnell, os dois divergem), pinos para furo passante. Pior que o IM72D128 em ruído (≈ 12 dB), em AOP (18 dB) e sem graves confirmados; pior que a Primo EM272 da B em tudo. Só serviria como cápsula barata de teste do caminho analógico na Fase 2.
Tarefa da Fase 1 para a C (pedir ficha não é comprar): a `mic-eletronica` pede a 2 ou 3 fabricantes, por escrito: curva de resposta medida de 20 a 200 Hz; ruído próprio (A) com o JFET; AOP a 1% de distorção com 3,3 e com 5 V; sensibilidade e tolerância, com pareamento L/R de ± 1 dB; capacitância; diafragma de 3 ou 6 µm; desenho da ventilação traseira (cardioide); altura, pinos e preço por 10 e 100. **Critério para a C virar segunda versão na Fase 2:** ruído ≤ 12 dB(A), −3 dB em ≤ 20 Hz, AOP ≥ 120 dB SPL e pareamento de ± 1 dB.

**Versão B:** cápsulas de eletreto Ø9,7 mm (classe Primo EM272: 80 dB SNR, 119 a 122 dB SPL de máximo, sensibilidade −28 dBV/Pa ±3 dB) + ADC estéreo (candidato: TI PCM1863, 110 dB SNR, 2,1 Vrms de fundo de escala) + RP2040. Resultado das contas: ruído 2,5 a 7 dB menor, mas **6 a 9 dB menos margem de sobrecarga** (a cápsula satura antes do sensor MEMS) e graves **não confirmados** (60 Hz a 20 kHz na ficha de loja). O J decide se segue só a A ou também a B; **a A é a base de todas as tarefas acima**.

---

# R2MIC (histórico) — SPEC R2MIC (conceito)

Data: 28 nov 2026 · Autor: Claude (sessão de conceito, com o J) · Destino: Claude Code + agentes `mic-*`
Nome do produto: **Liebling**, da marca **Batschauer** ("mic Liebling"). A pasta continua `minimic/` (nome de trabalho; renomear é só um `git mv` mais os três arquivos de agente). Nomenclatura das revisões: **RnMIC**; os relatórios citam a revisão que atendem.

## R2MIC — o que mudou desde a R1MIC (este bloco vale sobre o resto do texto)

**Uso real:** captar **acordeon bayan** (graves poderosos, de ~41 Hz para cima, picos de 105-115 dB SPL de perto), de um músico ou banda, em live ou em estúdio pequeno em casa. O foco é plug and play o mais perto possível de um estúdio grande.

### Captação (a pergunta do J)

O que o bayan exige do sensor, em ordem: (1) **ponto de sobrecarga (AOP) ≥ 128 dB SPL**, porque de perto os picos passam de 110 dB e a distorção do sensor não se corrige depois; (2) **extensão de graves até ≤ 30 Hz sem queda**, para a fundamental de 41 Hz e os graves de fole; (3) ruído próprio baixo; (4) resposta plana, sem realce nem AGC. Um microfone de **pressão omnidirecional** (todo MEMS) não tem efeito de proximidade, que é bom para o grave do bayan e ruim para vazamento de outros instrumentos.

Conferido em fonte (Infineon, 28 nov 2026; o resto desta seção segue **de memória**, a E1 confere):
- **IM72D128** (PDM): SNR **71,5 a 72 dB(A)**, AOP **128 dB SPL**, queda de graves em **11 Hz** (variante VV01) ou 20 Hz (V01). Ruído próprio ≈ 22 dB SPL(A), faixa dinâmica ≈ 106 dB.
- **IM69D130** (PDM): SNR 69 dB(A), AOP 130 dB SPL, tabela de resposta começando em 25 Hz (−2/−5 dB nesse ponto).
- O ICS-43434 e os MEMS de ~65 dB / 120 dB SPL com queda de graves em torno de 60 Hz **ficam fora**: cortam a fundamental do bayan e saturam cedo.

**Decisão R2MIC:** **IM72D128 (preferir a variante VV01, 11 Hz)** em PDM, omnidirecional, com **espuma acústica** na porta. Fallback: IM69D130. Os limites que escrevi na R1MIC ("MEMS não passa de ~69 dB") estavam desatualizados; o IM72D128 muda a conta.

Por que **não** dois sensores somados (+3 dB de SNR, ruído ≈ 19,5 dB(A)): numa sala de casa o ruído do ambiente é de 30-40 dB(A), então 22 ou 19,5 dB(A) de ruído próprio não se ouvem; o que decide a qualidade é AOP, graves, planicidade e a posição do microfone. Fica como opção de estudo (dois PDM na mesma linha, selecionados por L/R) se a medição real mostrar ruído audível. **Cardioide por dois sensores** também fica de fora do R2: a subtração diferencial amplifica o ruído justo nos graves do bayan.

Riscos da escolha, para a `mic-eletronica` fechar na E1: (a) **estoque e preço** do IM72D128 na LCSC/JLCPCB (Infineon costuma vir por distribuidor, talvez *Global Sourcing* ou compra à parte e solda em casa); (b) encapsulamento e se a JLCPCB monta; (c) PDM de 2,4-3,1 MHz exige **decimação no RP2040** (PIO + CIC + FIR) com banda e fase boas até os 40 Hz, sem queda do próprio filtro.

### Ganho

**0 a +42 dB**, curva em dB com mais resolução no começo: de perto, o bayan quer 0 a +20 dB; uma banda a 2 m (picos de ~80 dB SPL) precisa de ~+39 dB. Faixa justificada pela escala de fundo do sensor (≈ 128 dB SPL ≈ 0 dBFS). Slider (preferência do J): ver as opções no protótipo; a R2 desenha o **S1 (slider mecânico, 15 mm)** e deixa **S2 (capacitivo, 30 mm, sem peça)** como estudo.

### Medidor

**12 LEDs** (L3): 11 na escala e **1 azul "MIC"** que acende quando o próprio sensor satura (o ganho não resolve isso). Passo de 3 a 4 dB perto do topo. As opções de 8 e 10 LEDs ficam registradas no protótipo.

### Espuma (quebra-vento) — vai junto, faz parte do produto

Espuma acústica de célula aberta, Ø10 × 3 mm, colada sobre a porta do microfone: segura as rajadas de ar do fole e as plosivas da voz, e protege o sensor. Entram **3 por embalagem**. Perda de agudos esperada < 1 dB acima de 10 kHz (a verificar na medição).

### Fases e compra

- **Fase 1 — projeto, sem comprar nada:** conceito, esquema, posicionamento (portão P), roteamento, orçamento, firmware que compila e é testado em simulação no PC (decimação PDM, ganho, medidor com sinais sintéticos).
- **Portão de compra:** o J valida a **versão final e o orçamento**. Só então começa a **Fase 2 — compras**: placas de teste, módulo de bancada, testes em celulares e medições.
- Por isso o antigo F1 (protótipo em bancada) passa para a Fase 2; na Fase 1 o F1 é a simulação no PC.

### Protótipo visual

`minimic/design/liebling_r2.html` (gerado por `minimic/design/proto_r2.py`): planta com cotas, dois isométricos (produto e em uso no celular), 3 opções de slider e 3 de medidor. Conceito, não é desenho de fabricação.

---

**Regras herdadas da eTutti** (o J confirma ou muda):
- o J manda; nada é comprado nem encomendado sem o "aprovado" dele;
- depois de aprovar o posicionamento (portão P), a placa é roteada;
- DRC 0 erros e 0 avisos, 0 ligações faltando, paridade 0;
- relatórios em português, terminando com "Perguntas para o design / a gestão".

---

## 1. O produto em uma frase

Um microfone USB-C **do tamanho de uma placa**: espeta direto no celular, o celular o reconhece sozinho (sem app, sem driver), um único controle ajusta o ganho e uma fileira de LEDs verde → amarelo → vermelho mostra o nível captado para o usuário acertar o ganho **vendo**.

## 2. Princípios (em ordem de prioridade)

1. **Plug and play de verdade:** classe de áudio USB padrão, sem app. Funciona em Android, iPhone com USB-C, iPad, Windows, macOS, Linux.
2. **Menor custo possível:** uma placa só, de 2 camadas, tudo SMD montado pela JLCPCB (montagem Economic, o máximo de peças *Basic*), nenhuma caixa obrigatória.
3. **Qualidade de estúdio dentro do que o sensor permite** (ver §3): digital de ponta a ponta, 24 bits, sem etapa analógica ruidosa entre o microfone e o USB.
4. **Interface mínima:** exatamente dois elementos, o ganho e os LEDs. Sem chaves, sem modos, sem menus.
5. **Leve e estável sem apoio:** a própria placa fica pendurada no conector USB-C do celular.

## 3. O que "qualidade de estúdio" significa aqui (metas mensuráveis)

Um microfone de membrana grande de estúdio tem relação sinal-ruído de ~75-80 dB(A); um MEMS de topo chega a ~69. Prometer "igual a um condensador de estúdio" seria falso. A meta honesta e verificável:

| Item | Meta R1MIC |
|---|---|
| Formato | **24 bits, 48 kHz**, mono (96 kHz só se for de graça no firmware) |
| Relação sinal-ruído do sensor | **≥ 65 dB(A)** (ruído próprio ≤ ~29 dB SPL(A)) |
| Ponto de sobrecarga acústica (AOP) | **≥ 120 dB SPL** (voz gritada e instrumento de perto sem distorcer) |
| Resposta em frequência | **±3 dB de 50 Hz a 16 kHz**, sem realce de presença fabricado |
| Processamento | **nenhum** além do ganho e de um bloqueio de DC (~20 Hz). Sem compressor, sem EQ, sem redução de ruído: o usuário/DAW decide |
| Latência | só a do USB (sem retorno de monitoramento) |

Onde isso supera o microfone embutido do celular: está num ponto fixo e escolhido, perto da fonte, com ganho controlável e medidor, sem o processamento automático (AGC, redução de ruído) que o sistema do celular aplica ao microfone interno. Honestidade para a página futura: o ruído próprio é de MEMS de topo, não de estúdio caro.

## 4. Arquitetura recomendada (A) e alternativas

```
 MEMS digital ──I²S──▶ RP2040 ──USB-C (classe de áudio)──▶ celular
 (24 bits)            │  ├─ ganho digital (potenciômetro → ADC)
                      │  ├─ medidor (pico/RMS → 10 LEDs)
                      │  └─ bloqueio de DC
         LDO 3,3 V ◀── VBUS (5 V)
```

| Opção | Resumo | Custo de peças (estim.) | Veredito |
|---|---|---|---|
| **A. MEMS I²S + RP2040** | microfone digital, USB e medidor no mesmo chip | ~US$ 5-7 | **recomendada**: sem etapa analógica, medidor e ganho em firmware, tudo programável |
| B. Cápsula de eletreto + pré + codec USB (PCM2902 / CM108) | sem firmware; ganho analógico | ~US$ 4-6 | codecs de 16 bits, ruído do pré-amplificador, e o medidor LED precisaria de um segundo chip: reprovada para "estúdio" |
| C. MEMS + MCU STM32/CH32 com USB sem cristal | mesma ideia da A | ~US$ 5-8 | só se o RP2040 falhar (suporte a áudio USB em TinyUSB é bem melhor no RP2040) |

> Todos os números de preço e de datasheet nesta SPEC são de memória e **ainda não conferidos**: a primeira tarefa da `mic-eletronica` é conferi-los (LCSC, biblioteca de peças da JLCPCB, datasheet).

## 5. O microfone (sensor)

Candidatos a comparar (a eletrônica confere SNR, AOP, resposta, consumo, estoque, Basic/Extended, preço, porta superior ou inferior, encapsulamento e se a JLCPCB monta):
- **InvenSense ICS-43434** (I²S, ~65 dB(A), AOP ~120 dB SPL, resposta plana);
- **Infineon IM69D130** (PDM, ~69 dB(A), AOP ~130 dB SPL: o melhor, se couber no custo e houver estoque);
- **ST MP34DT06J** (PDM, ~64 dB(A), bem barato);
- **Knowles SPH0645 / TDK** equivalentes.

Critério de escolha: **primeiro SNR e AOP, depois preço**. PDM exige filtro de decimação no RP2040 (PIO + CIC/FIR), possível mas é trabalho de firmware; I²S é direto. Se o PDM de topo ganhar em qualidade, o custo de firmware é aceito.

Porta acústica: o desenho da placa (§8) decide se é de porta inferior (furo na placa) ou superior. O furo e o entorno (sem LED, sem cobre alto perto) fazem parte do desenho.

## 6. Controle de ganho (item 1 da interface)

- **Um potenciômetro SMD contínuo**, lido por ADC de 12 bits do RP2040: *knob* de lado (tipo roda de polegar), ou deslizante. Não é chave de três posições. A eletrônica escolhe a peça que a JLCPCB monta e que cabe na placa fina; o design propõe onde fica para ser alcançado com o polegar com o celular na mão.
- **Faixa de ganho digital: 0 a +36 dB**, curva logarítmica (cada posição vale um número de dB parecido), resolução prática ≤ 0,25 dB. Suavização (sem "estalos" quando o botão gira), histerese e filtro de mediana contra ruído do ADC.
- O ganho é aplicado no sinal de 24 bits **antes** do USB, e o medidor mostra o sinal **depois do ganho**: é exatamente o que chega ao celular.
- Limite físico que o usuário precisa saber (vai para a página e para o manual): o ganho digital não impede a **saturação do próprio sensor** (AOP ~120 dB SPL). Por isso o LED vermelho também acende se a amostra *crua* do sensor chegar perto do fundo de escala, mesmo com ganho baixo.
- Opcional a estudar (não obrigatório): expor um controle de volume na classe de áudio para quem o sistema deixar usar; o potenciômetro físico continua mandando.

## 7. Medidor de LEDs (item 2 da interface)

Dez LEDs SMD em fila, **acionados direto pelos GPIOs do RP2040** (um resistor por LED, nenhum chip de LED, nenhum multiplexador). LEDs de alta eficiência em 0603 (peças *Basic* da JLCPCB), ~0,5-1 mA cada, brilho por PWM.

| LED | cor | nível (dBFS, *pico* do sinal depois do ganho) |
|---|---|---|
| 1-6 | verde | −42, −36, −30, −24, −18, −12 |
| 7-8 | amarelo | −9, −6 |
| 9 | vermelho | −3 |
| 10 | vermelho | 0 (**clip**; fica aceso ~1 s, "preso") |

Alvo para o usuário: voz passando pelo verde-alto, tocando o amarelo de vez em quando, **nunca vermelho**. Os degraus são proposta; o design/firmware afina.

Comportamento:
- barra (todos os LEDs até o nível aceso), ataque instantâneo no pico, queda ~20 dB/s, ponto de pico segurado ~1 s (um LED a mais, só se não gastar corrente);
- ao ligar, uma varredura rápida acende a fila uma vez (mostra que está vivo);
- sem o celular pedindo áudio (enumerado mas parado), o medidor continua funcionando;
- a cor da escala é a ordem física: o design define o sentido (ver §8).

## 8. Mecânica e forma

- **Uma placa de circuito é todo o produto.** O conector USB-C é um **plugue macho SMD** soldado na ponta da placa (o plugue de pesos e travas de uma placa comum, não só os dedos de cobre da borda). A placa sai do celular em linha, como um pendrive.
- Tamanho-alvo: **≤ 60 × 16 mm, 1,0 mm de espessura, ≤ ~5 g**. Máscara fosca preta, serigrafia branca, ENIG ou HASL sem chumbo (o que mantiver a montagem Economic).
- Posição: LEDs na face voltada para o usuário em uso normal (celular em pé, microfone para baixo); **o microfone na ponta livre**, longe do corpo do celular (menos vibração de manuseio), e o potenciômetro ao alcance do polegar. O design propõe o sentido da fila (vermelho perto do celular, ou o contrário) e mostra em figura.
- Riscos mecânicos a estudar (desenho, não depende de comprar): o plugue encaixa em celulares **com capinha grossa**? A alavanca de uma placa de 60 mm no plugue aguenta o uso? (retenção do conector, trava, e a opção de duas hastes com furo/pinos). Quanto à capinha, o plugue precisa ser comprido o bastante; o design lista a profundidade mínima do rebaixo que ele exige.
- Acessório opcional (pergunta ao J, §11): um **quebra-vento** de espuma acústica recortada em adesivo, para o furo do microfone.
- Sem caixa na versão R1. Uma capa impressa só entra se o J pedir.

## 9. USB e energia

- **Classe de áudio USB, mono, 24 bits, 48 kHz**, dispositivo alimentado pelo barramento. Nome de produto: provisoriamente "Minimic".
- **UAC1 ou UAC2?** Decisão do firmware depois de testar em celulares reais: UAC1 é a mais universal em Android e iOS; UAC2 tem melhor suporte de 24 bits. O TinyUSB tem UAC2 pronto; UAC1 pode exigir descritores próprios.
- **Orçamento de corrente: ≤ 100 mA** (o celular não deve se assustar e a bateria dele não pode ser castigada). Estimativa: RP2040 reduzido a 48-125 MHz ~15-25 mA, sensor ~1 mA, LEDs (média) ~5-8 mA. A eletrônica fecha a conta em `POWER.md`.
- Resistores CC de 5,1 kΩ (dispositivo), proteção ESD só se couber no custo, LDO de 3,3 V com filtro RC no pino de alimentação do sensor (o ruído da alimentação entra direto no sinal).
- Sem bateria, sem botão de energia, sem entrada/saída de áudio de fone.

## 10. Fora do escopo da R1MIC

Saída de fone/monitoramento (adicionaria latência e custo), estéreo, padrões polares, filtro passa-altas selecionável, modos de ganho, bateria, Bluetooth, app, aplicativo de configuração, caixa, suporte de mesa.

## 11. Decisões do J (R2MIC) e perguntas abertas

Respondidas: (1) nome **Liebling**, marca **Batschauer**; (2) faixa de ganho pelo uso com bayan: 0 a +42 dB; (3) slider, com opções; (4) LEDs com opções (R2 desenha 12); (5) espuma vem junto, se importar para a qualidade (importa: entra); (6) nada é comprado antes de validar a versão final e o orçamento.

Abertas para o J olhar no protótipo visual:
1. **Slider:** S1 mecânico (15 mm) ou S2 capacitivo (30 mm, sem peça)?
2. **Medidor:** L1 (8), L2 (10) ou L3 (12, com o LED azul de sobrecarga do sensor)?
3. **Sentido do medidor** com o celular deitado (live em paisagem): o vermelho fica perto do plugue (nível sobe em direção ao celular, certo com o celular em pé) ou do outro lado? Dá para um acelerômetro invertê-lo sozinho, ao custo de uma peça.
4. O **cabo de extensão USB-C** (microfone num pedestal, celular no suporte) faz parte do kit ou é do músico?

## 12. Tarefas para o Code

Cada tarefa tem dono (agente) e a ordem é eletrônica/firmware em paralelo depois do estudo de peças:

**Eletrônica (`mic-eletronica`)** — `minimic/pcb/`, `minimic/ELETRONICA.md`, `minimic/POWER.md`
1. **E1 — estudo de peças**: tabela de sensores (§5), plugue USB-C macho SMD (montável pela JLCPCB, com travas), microcontrolador, flash, cristal, LDO, LED 0603, potenciômetro SMD (§6). Para cada peça: estoque, preço a 10 e 100 unidades, *Basic/Extended*, encapsulamento, risco. Recomendação final de sensor e de potenciômetro.
2. **E2 — custo e energia**: BOM de custo de peças + placa + montagem Economic; orçamento de corrente em `POWER.md` (§9).
3. **E3 — esquema** (KiCad 10, gerado por script como nos outros projetos): sensor, MCU, USB, LDO, 10 LEDs, potenciômetro, pontos de teste (SWD/BOOT). ERC 0/0, `pcb/PINOS.md` (contrato com o firmware).
4. **E4 — posicionamento** (portão P): contorno ≤ 60 × 16 mm, plugue na ponta, sensor na outra, LEDs em fila, potenciômetro; renders; **o J aprova antes de rotear**. Depois roteamento (o agente de roteamento da eTutti pode ser reaproveitado), DRC 0/0, Gerbers, BOM e CPL (Economic, o maior número de peças Basic).

**Programação e som (`mic-firmware`)** — `minimic/firmware/`, `minimic/FIRMWARE.md`
1. **F1 — simulação no PC (Fase 1, sem comprar):** fluxo de bits PDM sintético (modulador delta-sigma) → decimação (CIC + FIR, parâmetros do IM72D128) → ganho → medidor; medir resposta em 30 Hz-16 kHz, ruído e distorção do filtro, com tons de 41 Hz e acordes. *(O protótipo em bancada com celulares reais é da Fase 2, depois do portão de compra.)*
2. **F2 — firmware**: I²S por PIO, classe de áudio USB (UAC1/UAC2, §9), bloqueio de DC, ganho digital com suavização (§6), medidor e LEDs (§7), partida com varredura. Sketch próprio, só do Minimic.
3. **F3 — verificação:** ruído próprio medido com o sensor tapado (dBFS → dB SPL(A)), resposta contra um microfone de referência, lista de aparelhos testados (modelo, sistema, resultado).

**Design (`mic-design`)** — `minimic/design/`, `minimic/FIT_CHECK.md`
1. **D1 — forma e mecânica**: contorno, posição do sensor e do furo acústico, posição do botão e dos LEDs (e o sentido da escala, §8), estudo de alavanca/retenção e de capinhas, renders (vista de uso: placa no celular).
2. **D2 — acessório de espuma** (se o J disser sim) e desenho de embalagem mínima.
3. **D3 — arte da placa**: serigrafia limpa (nome, escala em dB, marcas de ganho) com as regras de serigrafia aprendidas na Student V4 (sem texto sobre pad).

**Integração (sessão que o J abrir)**: confere as três pontas entre si (pinos × firmware, contorno × estudo mecânico, BOM × custo), e só então abre **um PR por revisão** da SPEC.

## 13. Como saberemos que deu certo

- reconhecido sem driver em pelo menos um Android e um iPhone com USB-C, e em Windows e macOS;
- ruído próprio medido ≤ ~29 dB SPL(A) com o ganho no máximo da faixa;
- gravação de voz a 30 cm sem distorção mesmo gritando (nada de vermelho preso com o ganho certo);
- custo total montado ≤ US$ 10 por placa em lote de 100 (estimativa a ser cotada, ver E2);
- o medidor acompanha o nível sem atraso perceptível.
