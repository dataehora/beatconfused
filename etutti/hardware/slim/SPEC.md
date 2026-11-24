# eTutti Slim — SPEC R1SL

Versão nova e **independente do Student V4**. Tudo que o Slim precisa está nesta pasta (`etutti/hardware/slim/`). O V4 serve só como fonte de aprendizado: nenhum arquivo daqui depende de arquivos do V4, e nada do V4 é alterado.

- Revisões deste SPEC: **R1SL, R2SL, R3SL…** Cada revisão começa com "Mudanças desde a anterior".
- Protocolo: Chat mantém o SPEC → Code implementa e responde em `FIT_CHECK.md`, que termina com **"Perguntas para o design"** → J aprova os portões.
- Três agentes do Code: **Design**, **Eletrônica**, **Programação e som**.
- **Fora do escopo até o J avisar:** cotação, compra e pedido de placas. Nada é comprado, nem amostra.

---

## 0. Etapas e portões

O trabalho segue em 3 etapas. Nenhuma começa antes do portão anterior aprovado pelo J. **Posicionamento e roteamento são feitos separadamente para a régua e para a placa principal**, cada um na sua sessão, para economizar contexto.

| Etapa | Sessões | Entrega | Portão |
|---|---|---|---|
| **1. Validação de componentes e lógica** | 1a Eletrônica · 1b Programação e som · 1c Design (envelopes e STEP) | BOM com PN, esquemático KiCad, ERC 0/0, mapa de pinos, lógica de energia, lista de STEP, `ELETRONICA.md`, `FIRMWARE.md` | **A**: J aprova componentes e lógica |
| **2. Posicionamento** | 2a Régua R8 (+ grade) · 2b Placa principal | Planta cotada de cada placa, cena 3D com o case, `POSICIONAMENTO.md` | **B**: J aprova o posicionamento de cada placa |
| **3. Roteamento** | 3a Régua R8 · 3b Placa principal | Placas roteadas, DRC 0 erros / 0 avisos, `ROTEAMENTO.md` | **C**: J aprova |

---

## 1. Teclado (entradas fixas — o case nunca decide alturas)

- C‑griff, 4 fileiras, 32 teclas, malha hexagonal: **passo 18,5 mm** na fileira, **16,02 mm** entre fileiras.
- **Degraus entre fileiras 1→2→3→4: 2,0 · 2,0 · 3,0 mm** (padrão bayan, igual ao V4). Fileira 1 = a mais perto do músico e a mais baixa.
- Origem das coordenadas: centro da tecla A3 da fileira 1. x para a direita (agudos), y para trás.
- Deslocamento por fileira: fileiras 1 e 3 em x = 0; fileiras 2 e 4 em x = −9,25.

| Fileira | Notas (8) |
|---|---|
| 1 | A3 C4 D#4 F#4 A4 C5 D#5 F#5 |
| 2 | G3 A#3 C#4 E4 G4 A#4 C#5 E5 |
| 3 | G#3 B3 D4 F4 G#4 B4 D5 F5 |
| 4 | F#3 A3 C4 D#4 F#4 A4 C5 D#5 |

- **Botões: todos iguais**, domo convexo com saia, Ø15. Pretos (sustenidos), brancos, e brancos com pontos (C e F). Encaixe novo para a cruz da KS‑33D (4,0 × 1,1 em cilindro Ø5,7). Nunca há botões de alturas diferentes.
- Toda visualização de teclado leva o nome das notas.

## 2. Switch

**Gateron LP Magnetic Jade Pro, KS‑33DD10B060NW‑D276** (toda em POM). Desenho e STEP em `fornecimento/gateron/`.

| Item | Valor |
|---|---|
| Carcaça de cima | 14,60 × 14,60 (topo 12,7) |
| Corpo de baixo / furo da grade | 14,00 / 14,00 (+0,05/−0,02) |
| Grade (placa) | 1,20 mm; topo a 2,5 mm da PCB |
| PCB → topo da carcaça | 5,85 |
| Curso total | 3,5 ± 0,2 (haste rente à carcaça no fundo) |
| Força inicial | 40 ± 10 gf |
| Fluxo N | 75 ± 10 Gs (repouso) · 680 ± 70 Gs (fundo) |
| PCB | 2 furos Ø1,70 a 10,15 mm + furo Ø5,20 central (o poste Ø5,0 atravessa) |
| Abaixo da PCB | pinos ≈1,65 e poste 2,5 mm abaixo da face de baixo |
| Sensor Hall | verso da PCB, a 4,3 mm do centro (desenho “Layout of PCB”) |

Montagem como teclado mecânico: o switch prende na **grade** e encaixa na **régua**; régua + grade formam um conjunto sólido (2 espaçadores M2 por régua). **O tampo não prende as teclas**: só encosta ou fica a ≤0,3 mm das carcaças.

Comparação com a KS‑20 do V4: `conceito/img/sw_cmp.svg`.

## 3. Case — conceito aprovado (G v7), a rever após o detalhe eletrônico

- Planta **239 × 89 mm**, x de −90 a 149, y de −18,5 a 70,6. Material MJF PA12, tampo + base, sem autoatarraxante.
- **Tampo derivado das fileiras**: plano inclinado de 7,1° pelas fileiras 1–3 (degraus iguais), degrau suave de +1,0 mm entre y = 35 e 39 (completa os 3 mm da fileira 4), depois curva convexa até a borda de trás. Bordas: frente R4, trás R6. Função de referência: `conceito/scripts/sec7.py` (`S(y)`).
- **Furo Ø16** em cada tecla e **rebaixo Ø17** com fundo plano no nível do topo da carcaça + 1,8 mm. Parede mínima entre rebaixos: 1,5 mm.
- **Nenhum furo no piso.** Todas as réguas usam o mesmo tipo de apoio: berço contínuo sobre o degrau da base, com bolso de ≈2,8 mm sob cada poste e piso de ≥1,0 mm sob o bolso.

Pilha da fileira 1 (fileiras 2, 3, 4: +2, +4, +7):

| Cota (mm, do fundo da base) | |
|---|---|
| 1,6 | piso |
| 3,8 → 5,0 | régua (face de baixo → de cima) |
| 6,3 → 7,5 | grade |
| 10,85 | topo da carcaça |
| 14,35 | haste em repouso |
| 11,15 | face de baixo do tampo sobre as carcaças (folga 0,3) |
| 12,65 | fundo do rebaixo (1,5 mm de material) |
| 14,0 | superfície do tampo no centro da tecla |
| 14,55 / 18,55 | saia / topo do botão em repouso (saia a 0,2 da carcaça no fundo de curso) |

Resultado: borda da frente ≈11 mm, tampo máx. ≈22 mm, topo dos botões 18,6 → 25,6 mm.

Renders de conceito: `conceito/img/v7_iso_esq_com.jpg`, `v7_iso_esq_sem.jpg`. Cortes: `L_secA.svg`, `L_secB.svg`.

**Renders Blender detalhados:** só o isométrico frontal do lado dos knobs, com e sem botões, e **só quando o J pedir**. Sempre com modelos 3D realistas dos componentes; se faltar um STEP, avisar o J.

## 4. Interface e energia

- **Knobs baixos, em poços** (Ø17,6, 1,2 mm de fundo) nas plataformas: **registros** em (−46, 0) na fileira 1, **volume** em (−46, 48,06) na fileira 4.
- **Volume: potenciômetro contínuo, sem passos, com chave.** O clique ao sair de OFF, no sentido horário, liga o instrumento e acende o LED; daí até o fim do curso só sobe o volume. Marcação: arco contínuo que engrossa no sentido horário, com ponto de OFF.
- **Registros: chave rotativa absoluta de 7 posições** (escada de resistores em 1 pino ADC), no sentido horário a partir de baixo‑esquerda, a 45°:

| Pos. | Registro | Pontos (L embaixo, M no meio esq./centro/dir., H em cima) |
|---|---|---|
| 1 | L | L |
| 2 | LM | L + M esquerdo |
| 3 | M | M esquerdo |
| 4 | MM | M esquerdo + M direito (centro vazio) |
| 5 | MH | M esquerdo + H |
| 6 | LH | L + H |
| 7 | H | H |

  Desenho: `conceito/img/knobs7.svg`.
- **LED:** bicolor (verde/vermelho, laranja pela mistura), montagem reversa na face de baixo, aceso num anel translúcido em volta do knob de volume. Estados do V4: verde tocando, verde breve a cada 2 s em repouso, laranja ao ler as teclas na partida e carregando, vermelho lento bateria baixa, vermelho rápido codec ou régua sem resposta.
- **Bateria:** LiPo 1000 mAh com NTC (3 fios), **envelope 4,5 × 28 × 68 mm** (classe LP402764), em baia própria na frente‑esquerda (x −88…−60, y −14,5…54). Modelo final em aberto: Code propõe opções de distribuidor com NTC; o J escolhe e manda o STEP.
- **Conectores (aprovados):**
  - **USB‑C** mid‑mount na **parede de trás**, centro em x = −66 (24 mm da parede esquerda).
  - **P2 3,5 mm OUT** mid‑mount na **parede esquerda**, centro em y = 59,5 (11 mm da parede de trás).
  - Ambos afastados das quinas o quanto o layout permitir; o Code pode afastar mais se couber.
- **Energia:** BQ24075 (carregador + caminho de energia com SYSOFF). A chave do pot controla o SYSOFF, mas uma lógica mantém o SYSOFF baixo sempre que há USB, porque com SYSOFF alto o BQ24075 também para de carregar. Knob em OFF e sem USB: bateria desconectada.
- **Com USB, as mesmas funções do V4:** MIDI USB class‑compliant “eTutti” com velocity; o USB acorda, alimenta e carrega mesmo com o knob em OFF; desligamento suave com cabo; USB Full Speed (12 Mbit/s). Só na bateria: desliga sozinho após 15 min sem uso ou com bateria vazia.
- **Botão PROG:** dentro do case, só acessível abrindo a base.
- Áudio: só saída OUT para fone, sem microfone e sem alto‑falante.

## 5. Placas

### 5.1 Régua R8 (×4, idênticas, montadas uma vez)
- 15 × ≈160 mm, 2 camadas, 1,2 mm. Cauda de 14 mm além da primeira tecla, com o conector por baixo, fora da área das teclas.
- 8 × **TMAG5253** na face de baixo, na posição do desenho Gateron (4,3 mm do centro), saída analógica compartilhada; habilitação por **74HC595** na cauda (esquema do V4). O BA3 (±80 mT lineares) cobre os 68 mT do fundo de curso.
- Footprint KS‑33D: 2 × Ø1,70 + Ø5,20.
- **Grade** FR‑4 1,2 mm com furos 14,00, no mesmo painel da régua se a JLCPCB aceitar.
- Conector **FFC 8 vias 0,5 mm** na cauda (face de baixo): GND, 3V3, OUT, DADO, CLOCK, LATCH, GND, GND. Cabos FFC prontos, retos, um por fileira.

### 5.2 Placa principal
- Faixa vertical de ≈24 × 82 mm junto às caudas das réguas, mais um pé de ≈31 × 14 mm atrás, até a parede esquerda (USB‑C, P2, energia). 4 camadas. Montagem JLCPCB **só na face de baixo**, peças Basic primeiro.
- **Teensy 4.1 chip‑down:** MIMXRT1062DVL6B (BGA196 12 × 12, passo 0,8), flash QSPI 64 Mbit, **MKL02 com bootloader PJRC** (só a PJRC vende; prever peça consignada), cristal 24 MHz, 32,768 kHz opcional, indutor do DCDC, sequência de energia pela referência PJRC (sem atraso RC no DCDC_PSWITCH).
- **O RT1062 é posicionado primeiro**: entre os knobs, na altura da fileira 3. Zona de escape livre de 2,5 mm em volta e corredores reservados: ADC → conectores das réguas; QSPI → flash; XTAL; USB e I2S → pé da placa. A orientação do BGA sai do mapa de esferas.
- SGTL5000 (codec com driver de fone), LDO 3,3 V, ESD USB, PTC, conector da bateria, lógica SYSOFF, LED reverso.
- Plano preliminar: `conceito/img/MB5_detail.svg` e `P1e_layout.svg`.
- Par USB: com a placa vertical, fica com ≈30–35 mm. Funciona em Full Speed, mas passa da regra de ≤10 mm do V4: o Code avalia e diz se é aceitável.

## 6. Ferramentas

- O J instalou no computador dele o KiCad 9/10 e o **KiCadRoutingTools** (drandyhaas/KiCadRoutingTools: plugin e CLI, `bga_fanout.py`, roteador A*).
- **Cabe ao Code decidir** se e quando usar o KiCadRoutingTools, e validar se o resultado é melhor que o fluxo usado antes (Freerouting e scripts). Sempre numa cópia do `.kicad_pcb`. A comparação usa: DRC 0/0, nada sem rota, número de vias, comprimento do par USB e das linhas analógicas. O resultado vai no relatório.
- Se o Code rodar na nuvem, ele repete a instalação no ambiente dele.

## 7. Modelos 3D (STEP)

| Peça | Situação |
|---|---|
| Switch KS‑33D | ✔ recebido (`fornecimento/gateron/`) |
| Pot 9 mm contínuo com chave | ✖ falta: escolher o PN e obter o STEP |
| Chave rotativa de 7 posições | ✖ falta: escolher o PN e obter o STEP |
| USB‑C mid‑mount, P2 mid‑mount | ✖ falta: puxar do LCSC/EasyEDA pelo PN |
| Bateria | ✖ falta: o J manda quando escolher |
| RT1062, MKL02, TMAG5253, FFC etc. | bibliotecas KiCad/JLC |

O que não tiver STEP fiel é listado em `FIT_CHECK.md` para o J fornecer.

## 8. Primeira tarefa (Etapa 1)

1. **[Eletrônica]** BOM completa com PN, LCSC, Basic/Extended e estoque. Esquemático KiCad da principal e da régua, ERC 0/0. Lógica de energia (BQ24075 + SYSOFF + USB). Escada da chave de 7 posições. Escolha do pot com chave e da chave rotativa. Mapa de pinos do RT1062, já pensando no posicionamento do BGA.
2. **[Programação e som]** `FIRMWARE.md` do Slim: varredura das 32 teclas (4 linhas analógicas em paralelo, habilitação pelo 74HC595), 7 registros, volume contínuo, LED, energia e funções USB do V4, CPU e bateria estimadas. Compilar para Teensy 4.1.
3. **[Design]** Conferir os envelopes do case contra os STEP e os PN escolhidos; listar os STEP que faltam.
4. `FIT_CHECK.md` com o resumo e **“Perguntas para o design”**. Parar no **portão A**.
