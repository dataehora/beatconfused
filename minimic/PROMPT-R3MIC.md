# Prompt para o Code — Liebling (Batschauer), SPEC R3MIC, só a versão A

Você é a **sessão integradora** do projeto Liebling (microfone USB-C estéreo da Batschauer), repo `dataehora/beatconfused`, pasta `minimic/`. Responda ao J em português. Escreva direto na `main` (autorizado: commit, PR e merge sem perguntar), um PR por entrega.

## Leia primeiro
1. `CLAUDE.md` da raiz (seção "Liebling / Minimic" e as regras gerais).
2. `minimic/SPEC.md`: o bloco **R3MIC** no topo manda sobre o resto; depois o bloco R2MIC e as seções 1 a 13. A SPEC é do Chat: **ninguém do Code a edita**; pedidos de mudança vão nos relatórios.
3. O protótipo visual aprovado: `minimic/design/liebling_r3.html` (gerado por `proto_r3.py`). É a referência de forma, posições, cores e textos. A comparação A/B/C (`liebling_r3_comparacao.html`) é histórico.

## Escopo
- **Só a versão A**: 2 × Infineon IM72D128 (PDM, uma linha de dados, L/R por pino SELECT) + RP2040 + USB-C, placa **72 × 22 × 1,2 mm**, plugue no centro do lado maior, **sem case**, máscara preta fosca, ENIG.
- **Congeladas, não detalhar:** versões B (eletreto) e C (diafragma grande), e todo o resto do repositório (eTutti, Student, Viaggio, Pocket etc.). Podem ser lidas como referência.
- **Fase 1: nada é comprado nem encomendado**, nem amostras. Só projeto, simulação e orçamento. O portão de compra é do J, depois de validar a versão final e o orçamento.

## O produto, em números (resumo da SPEC; em dúvida, vale a SPEC)
- USB de classe de áudio, 2 canais, 24 bits, 48 kHz, alimentado pelo barramento, ≤ 100 mA. Sem processamento além do ganho e de um bloqueio de DC (~3 Hz). Meta: −3 dB em ≤ 15 Hz na cadeia inteira.
- **Ganho:** 0 a +42 dB, passos de 1,5 dB, dois botões − e +, barra de 15 LEDs brancos fracos (aceso = posição; meio passo = dois vizinhos acesos), repetição ao segurar, padrão +12 dB, último valor guardado em flash (3 s depois da última mudança, com rodízio).
- **Medidor:** 11 LEDs (verde −42, −36, −30, −24, −20, −16; amarelo −12, −9, −6; vermelho −3, 0) + **SAT azul** logo depois do último vermelho. SAT = saída chegou a 0 dBFS (cortou) **ou** sensor acima de ~128 dB SPL; pisca ~8 Hz por ~2 s e **faz os dois vermelhos piscarem junto**. Mostra o máximo entre L e R. Serigrafia: números em dBFS, "SAT", "−", "+", "L", "R", "GAIN dB", marca. **Sem frase de aviso.**
- Acabamento da PCB é o produto: marca "Liebling" em cobre dourado (ENIG), contorno dourado, anéis dourados nos furos dos microfones, chanfros de 3 mm (frente) e 1,5 mm (atrás), espuma Ø10 sobre cada furo (3 pares por embalagem).

## Tarefas, por agente (cada um dono da sua pasta e do seu relatório)
Ordem: **E1 e F1 em paralelo → D1 → E3 → E4 (portão P, o J aprova) → roteamento → fechamento.**

**`mic-eletronica`** (`minimic/pcb/`, `ELETRONICA.md`, `POWER.md`, `pcb/PINOS.md`)
- **E1 — peças, conferidas na fonte** (datasheet, LCSC, biblioteca da JLCPCB): IM72D128 (variante VV01 se existir; estoque, preço a 10 e 100, se a JLCPCB monta ou se vem por Global Sourcing/compra à parte; fallback IM69D130), RP2040 + flash + cristal, LDO 3,3 V com filtro, plugue USB-C macho (carcaça metálica, pernas soldadas, o mais **firme** que a JLCPCB monte), botões táteis SMD baixos, LEDs 0603 branco, 0805 R/Y/G, 1206 azul. Para cada código LCSC, conferir o encapsulamento contra o footprint.
- **E2 — custo e energia:** BOM e custo por placa (10 e 100 un.), montagem Economic, o máximo de peças Basic; `POWER.md` fecha ≤ 100 mA com o pior caso de LEDs.
- **E3 — esquema** (KiCad 10, por script, ERC 0/0): 2 mics na mesma linha PDM, medidor 12 LEDs diretos (GPIOs), barra de ganho de 15 LEDs por **charlieplexing** (5 pinos) — confirmar contra 2 × 74HC595 Basic e justificar —, 2 botões, pontos de teste SWD/BOOT. Cerca de 21 GPIOs; `PINOS.md` é o contrato com o firmware.
- **E4 — posicionamento** no contorno do `design/` (arquivo JSON do design), com **portão P: pare e peça o "aprovado" do J antes de rotear**. Depois roteamento (o agente `roteamento` da eTutti pode ser reaproveitado, com as regras dele), DRC 0 erros e 0 avisos, 0 ligações faltando, paridade 0, Gerbers/BOM/CPL para a JLCPCB (Economic, preto fosco, ENIG).

**`mic-firmware`** (`minimic/firmware/`, `FIRMWARE.md`)
- **F1 — simulação no PC (sem hardware):** fluxo PDM sintético (modulador delta-sigma) → decimação (CIC + FIR) → bloqueio de DC → ganho → medidor, 2 canais, com os parâmetros do IM72D128. Medir resposta de 15 Hz a 16 kHz, ruído, distorção, tons de 41 Hz, acordes, saturação de sensor simulada, e a **carga de CPU estimada no RP2040** para 2 canais.
- **F2 — firmware** (pico-sdk ou arduino-pico, **compilando**): PIO para o PDM, decimação, ganho em passos de 1,5 dB com meio LED, botões com repetição, flash com rodízio, medidor, SAT com vermelhos piscando, UAC 2 canais 24 bits (UAC1 × UAC2 fica como decisão de teste em celular na Fase 2; documente os dois caminhos), consumo estimado.
- Verificação com hardware (celulares, ruído medido) é **Fase 2**: não tente, não compre nada.

**`mic-design`** (`minimic/design/`, `FIT_CHECK.md`)
- **D1 — forma e mecânica:** contorno 72 × 22 mm em JSON (`design/pcb_envelope.json`: contorno, plugue, microfones, LEDs, botões, furos), estudo da **alavanca do plugue no centro** (peso ~6-8 g, selfie stick, celular em pé), folga para capinha fina, e para celulares de 70 a 77 mm de largura.
- **D3 — arte da PCB:** serigrafia e cobre dourado conforme o protótipo, regras de serigrafia da Student V4 (nada sobre pad, nem texto sobre texto), conferir cor × número × significado dos LEDs.
- **D2 — espuma** Ø10 para 2 furos (se afeta altura ou posição, dizer no relatório).

## Contratos e regras de trabalho
- Um dono por contrato: `design/pcb_envelope.json` (design), `pcb/PINOS.md` (eletrônica), o mapa de pinos no firmware (firmware). Mudança no contrato do outro vai pedida no seu relatório, nunca por edição direta.
- Relatórios em português, cada um termina com "Perguntas para o design" e cita "R3MIC".
- Scripts por geração (nada à mão): esquema, placa, renders, Gerbers.
- Ferramentas na máquina do J: KiCad 10 (`C:/Program Files/KiCad/10.0/bin/`), CadQuery venv (`C:/Users/julia/.venvs/cadquery`), arduino-cli. Heredocs do Bash perdem barras invertidas: escreva scripts com `\n` pela ferramenta Write.
- Cheque cruzado antes de cada PR: pinos × firmware, contorno × estudo mecânico, BOM × custo, cor × número dos LEDs.

## Entrega
Um PR por etapa (E1+E2+F1+D1 juntos; E3+F2+D3; E4 até o portão P; roteamento e fechamento). Ao fim de cada um, diga ao J a linha para o Chat: **"SPEC R3MIC (etapa X) atendida — PR #n; relatórios atualizados"**, com o que ficou de fora e as perguntas abertas. **No portão P, não roteie sem o "aprovado" do J.**

## O que não fazer
Não comprar nem encomendar nada. Não editar a SPEC. Não detalhar B nem C. Não tocar nos outros projetos do repositório. Não mudar o texto do medidor (sem frase de saturação), a cor da máscara (preta fosca) nem pôr case.
