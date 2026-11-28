# Liebling (Batschauer) — SPEC R2MIC (conceito)

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
