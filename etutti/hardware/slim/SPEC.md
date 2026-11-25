# eTutti Slim — SPEC R2SL

## Mudanças desde a R1SL (25 nov 2026)

Resposta do J ao portão A da Etapa 1 (PR #210) e às 7 perguntas do `FIT_CHECK.md`. **O portão A continua aberto**: a R2SL fecha os pontos pendentes e a Etapa 1 é refeita só no que mudou (§8).

1. **RT1062 = MIMXRT1062DVJ6B, BGA196 12 × 12 mm, passo 0,8** (pergunta 1). O "DVL6B" da R1SL era erro de nome. Peça **consignada** (não depender do estoque da JLCPCB). STEP, símbolo e footprint da SamacSys em `modelos/rt1062/` (PR #211): a eletrônica confere o footprint do esquema contra o da biblioteca.
2. **Knobs = opção C, magnéticos, sem eixo** (perguntas 2 e 3). Somem o pot com chave e a chave rotativa SRBV: nada de peça de furo, bucha M9 ou porca no tampo. Detalhe em §4.
3. **USB‑C e P2 = as mesmas peças e o mesmo jeito da V4** (pergunta 5): HRO TYPE‑C‑31‑M‑12 (C165948) e XUNPU PJ‑327A (C49284723), montados pela JLCPCB na face de baixo, na borda da placa. Deixam de ser mid‑mount.
4. **Regra de alturas e o novo `RESTRICOES_CASE.md`** (pergunta 4). Peça que não cabe sob a placa segue a ordem: (a) peça equivalente mais baixa; (b) passa para a face de cima (soldada em casa); (c) **o conjunto sobe** até caber. Todo fator que limita a forma do case vai para o registro novo (§3.1), mantido pelo Design e atualizado a cada etapa.
5. **Bateria** (pergunta 6): o caminho aprovado continua (LP402764 de 2 fios + resistor de 10 k no TS se não houver NTC; baia +1 mm), **mas o Code estuda baterias maiores de fabricante com folha de dados e distribuidor**, e o J aceita **alongar o case para a esquerda**. Detalhe em §4.
6. **FFC de 1,0 mm** (C3250113, pergunta 7), montado pela JLCPCB; o J só encaixa os cabos.
7. **Par USB de 30–35 mm aceito** (pergunta 4 da `ELETRONICA.md`), com o firmware **forçando Full Speed**.
8. **Fluxo do repositório:** cada revisão da SPEC entra no `main` por PR (o Chat faz). O ramo `slim-r1sl` do J é cópia antiga e não entra; o PR #132 (placa de teste de teclas) foi fechado.

---

Versão nova e **independente do Student V4**. Tudo que o Slim precisa está nesta pasta (`etutti/hardware/slim/`). O V4 serve só como fonte de aprendizado: nenhum arquivo daqui depende de arquivos do V4, e nada do V4 é alterado.

- Revisões deste SPEC: **R1SL, R2SL, R3SL…** Cada revisão começa com "Mudanças desde a anterior". Os relatórios citam a revisão que atendem.
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

### 3.1 Registro de restrições do case — `RESTRICOES_CASE.md` (novo na R2SL)

Tudo que limita ou empurra a forma do case fica registrado, para ser gerenciado como risco: altura de peça, folga sob a placa, conector na parede, baia da bateria, curso do knob, raio de cabo, tolerância de impressão etc. Dono: **Design**. Atualizado a cada etapa (e a cada revisão da SPEC); o `FIT_CHECK.md` resume as mudanças.

| Coluna | Conteúdo |
|---|---|
| ID | R01, R02… (não reutilizar números) |
| Fator | o que limita (ex.: "altura do JST da bateria sob a placa") |
| Peça e medida | PN, medida e **fonte** (datasheet, STEP, medida estimada) |
| Onde | zona do case (x, y, z) |
| Efeito no case | mm que o case cresce ou sobe, ou "nenhum" |
| Folga | margem que sobra, mm |
| Alternativas | as opções da regra (a)/(b)/(c) e o custo de cada uma |
| Decisão | quem decidiu e quando, ou "aberto" |
| Estado | aberto · resolvido · aceito como risco |

Regra: **qualquer item que mude o lado de fora do case** (contorno, altura, parede, furo) aparece em destaque no `FIT_CHECK.md` e só vale depois do J aprovar. O que só mexe por dentro é decidido pelo Code e registrado.

**Renders Blender detalhados:** só o isométrico frontal do lado dos knobs, com e sem botões, e **só quando o J pedir**. Sempre com modelos 3D realistas dos componentes; se faltar um STEP, avisar o J.

## 4. Interface e energia

- **Knobs magnéticos, sem eixo (opção C, R2SL)**, em poços (Ø17,6, 1,2 mm de fundo) nas plataformas: **registros** em (−46, 0) na fileira 1, **volume** em (−46, 48,06) na fileira 4. Corte de referência: `conceito/img/knobs_opcoes.png` (coluna C).
  - **Knob:** peça impressa, topo ≈ +4,8 mm sobre o tampo (≈ altura do botão da fileira), **haste** que atravessa um furo‑mancal no fundo do poço e desce até ≈0,5 mm acima da placa principal. Retenção por anel de encaixe (ou arruela de pressão) na haste, por baixo do tampo; o knob não sai puxando.
  - **Ímã diametral** (classe Ø6 × 2,5 NdFeB, a confirmar) na ponta da haste, sobre um **sensor de ângulo** na **face de baixo** da placa (montado pela JLCPCB), lendo através da placa: ímã → sensor ≈ 0,5 + 1,2 + chip. Sensor: TMAG5273 ou equivalente (AS5600, MT6701…), **o Code escolhe e justifica** pelo campo no sensor, resolução, consumo e endereço I²C (dois sensores no mesmo barramento do SGTL5000). Se a placa subir pela regra de alturas, só a haste muda de comprimento.
  - **Cliques:** moldados no poço/haste (esfera com mola ou flexão do PA12, **o Design propõe e justifica**), com batentes. A vida útil do clique em PA12 é risco a registrar.
- **Volume: contínuo, sem passos.** O clique ao sair de OFF, no sentido horário, liga o instrumento e acende o LED; daí até o fim do curso só sobe o volume (volume digital, lido do sensor de ângulo). **OFF em hardware:** um segundo ímã no knob, na posição OFF, sobre uma **chave Hall de microcorrente** (DRV5032 ou equivalente, alimentada direto pela bateria) que comanda o SYSOFF no lugar da chave do pot: knob em OFF e sem USB = bateria desconectada, como na R1SL. Consumo em OFF ≤ alguns µA (o Code calcula a autonomia em prateleira). Marcação: arco contínuo que engrossa no sentido horário, com ponto de OFF.
- **Registros: seletor absoluto de 7 posições** (ângulo lido pelo sensor; o firmware arredonda para a posição e guarda a última), no sentido horário a partir de baixo‑esquerda, a 45°:

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
- **LED:** bicolor (verde/vermelho, laranja pela mistura), montagem reversa na face de baixo, aceso num anel translúcido em volta do knob de volume (o Code confere que a luz passa ao lado da haste e do ímã). Estados do V4: verde tocando, verde breve a cada 2 s em repouso, laranja ao ler as teclas na partida e carregando, vermelho lento bateria baixa, vermelho rápido codec ou régua sem resposta.
- **Bateria (R2SL):** baia própria na frente‑esquerda. Três candidatas a comparar no portão A (o J escolhe e manda o STEP):
  - **B1 (caminho aprovado):** LP402764‑1000, 1000 mAh, máx. 4,5 × 28 × 68 mm, fabricante genérico; **baia +1 mm** (29 × 69,5); sem NTC → **resistor de 10 k no TS** do BQ24075. Não exige mudar o case por fora.
  - **B2:** **VARTA LPP 503562 S**, 1200 mAh típico, com PCM e **NTC 10 k (B 3435)** + pino ID (folha de dados VARTA, vendida pela Farnell). Classe 5 × 35 × 62 (**medidas do pack com PCM a conferir**).
  - **B3:** **LPP 503759 8HH**, 1400 mAh típico, PCM e NTC 10 k (B 3380). Classe 5 × 37 × 59 (**fabricante, distribuidor e medidas a conferir**).
  - B2 e B3 são mais largas e mais grossas: **o J aceita alongar o case para a esquerda**. Para cada uma o Code informa: crescimento do case em x (mm), efeito da espessura (> 4,5) no piso/placa, autonomia, conector, distribuidor e se vende em pequena quantidade. Entra no `RESTRICOES_CASE.md`. Nada é comprado.
- **Conectores (aprovados):**
  - **USB‑C** na **parede de trás**, centro em x = −66 (24 mm da parede esquerda; se o case crescer para a esquerda pela bateria, a distância à quina cresce junto).
  - **P2 3,5 mm OUT** na **parede esquerda**, centro em y = 59,5 (11 mm da parede de trás).
  - **Peças e montagem da V4 (R2SL):** HRO TYPE‑C‑31‑M‑12 (C165948) e XUNPU PJ‑327A (C49284723), na **face de baixo**, na borda da placa, montados pela JLCPCB. A altura deles sob a placa entra na regra de alturas (§5.2).
  - Ambos afastados das quinas o quanto o layout permitir; o Code pode afastar mais se couber.
- **Energia:** BQ24075 (carregador + caminho de energia com SYSOFF). A **chave Hall do OFF do volume** controla o SYSOFF (R2SL; era a chave do pot), mas uma lógica mantém o SYSOFF baixo sempre que há USB, porque com SYSOFF alto o BQ24075 também para de carregar. Knob em OFF e sem USB: bateria desconectada.
- **Com USB, as mesmas funções do V4:** MIDI USB class‑compliant “eTutti” com velocity; o USB acorda, alimenta e carrega mesmo com o knob em OFF; desligamento suave com cabo; USB Full Speed (12 Mbit/s), **forçado no firmware** (o par tem 30–35 mm). Só na bateria: desliga sozinho após 15 min sem uso ou com bateria vazia.
- **Botão PROG:** dentro do case, só acessível abrindo a base.
- Áudio: só saída OUT para fone, sem microfone e sem alto‑falante.

## 5. Placas

### 5.1 Régua R8 (×4, idênticas, montadas uma vez)
- 15 × ≈160 mm, 2 camadas, 1,2 mm. Cauda de 14 mm além da primeira tecla, com o conector por baixo, fora da área das teclas.
- 8 × **TMAG5253** na face de baixo, na posição do desenho Gateron (4,3 mm do centro), saída analógica compartilhada; habilitação por **74HC595** na cauda (esquema do V4). O BA3 (±80 mT lineares) cobre os 68 mT do fundo de curso.
- Footprint KS‑33D: 2 × Ø1,70 + Ø5,20.
- **Grade** FR‑4 1,2 mm com furos 14,00, no mesmo painel da régua se a JLCPCB aceitar.
- Conector **FFC 8 vias 0,5 mm, 1,0 mm de altura** (C3250113, R2SL; conferir se o contato é dos dois lados) na cauda (face de baixo): GND, 3V3, OUT, DADO, CLOCK, LATCH, GND, GND. Cabos FFC prontos, retos, um por fileira.

### 5.2 Placa principal
- Faixa vertical de ≈24 × 82 mm junto às caudas das réguas, mais um pé de ≈31 × 14 mm atrás, até a parede esquerda (USB‑C, P2, energia). 4 camadas. Montagem JLCPCB **só na face de baixo**, peças Basic primeiro.
- **Teensy 4.1 chip‑down:** **MIMXRT1062DVJ6B** (BGA196 12 × 12, passo 0,8; peça consignada; STEP e biblioteca em `modelos/rt1062/`), flash QSPI 64 Mbit, **MKL02 com bootloader PJRC** (só a PJRC vende; prever peça consignada), cristal 24 MHz, 32,768 kHz opcional, indutor do DCDC, sequência de energia pela referência PJRC (sem atraso RC no DCDC_PSWITCH).
- **O RT1062 é posicionado primeiro**: entre os knobs, na altura da fileira 3. Zona de escape livre de 2,5 mm em volta e corredores reservados: ADC → conectores das réguas; QSPI → flash; XTAL; USB e I2S → pé da placa. A orientação do BGA sai do mapa de esferas.
- SGTL5000 (codec com driver de fone), LDO 3,3 V, ESD USB, PTC, conector da bateria, lógica SYSOFF, LED reverso, **2 sensores de ângulo + chave Hall do OFF** (face de baixo, sob os knobs).
- **Regra de alturas (R2SL).** Folga sob a placa = face de baixo da placa − topo do piso (com a placa na régua da fileira 1: 3,8 − 1,6 = 2,2 mm). Peça que não cabe, nesta ordem:
  1. **equivalente mais baixa** (ex.: indutor do TPS63001 ≤ 1,9 mm; conector de bateria baixo ou fios soldados em pads);
  2. **face de cima**, soldada em casa (ex.: conector da bateria; há espaço entre a placa e o tampo);
  3. **subir o conjunto** (placa principal mais alta, em pilares) até caber.
  USB‑C e P2 da V4 ficam por baixo (são montados pela JLCPCB): eles provavelmente definem a altura da placa principal. Cada caso vai para o `RESTRICOES_CASE.md` com a folga resultante. Bolsos no piso são permitidos; furos não.
- Plano preliminar: `conceito/img/MB5_detail.svg` e `P1e_layout.svg`.
- Par USB: ≈30–35 mm, **aceito** (R2SL) com Full Speed forçado no firmware; 90 Ω diferenciais como boa prática.

## 6. Ferramentas

- O J instalou no computador dele o KiCad 9/10 e o **KiCadRoutingTools** (drandyhaas/KiCadRoutingTools: plugin e CLI, `bga_fanout.py`, roteador A*).
- **Cabe ao Code decidir** se e quando usar o KiCadRoutingTools, e validar se o resultado é melhor que o fluxo usado antes (Freerouting e scripts). Sempre numa cópia do `.kicad_pcb`. A comparação usa: DRC 0/0, nada sem rota, número de vias, comprimento do par USB e das linhas analógicas. O resultado vai no relatório.
- Se o Code rodar na nuvem, ele repete a instalação no ambiente dele.

## 7. Modelos 3D (STEP)

Sempre modelos realistas e detalhados. O que faltar vai para o `FIT_CHECK.md` para o J fornecer.

| Peça | Situação (R2SL) |
|---|---|
| Switch KS‑33D | ✔ `fornecimento/gateron/` |
| RT1062 DVJ6B | ✔ `modelos/rt1062/` (SamacSys, fornecido pelo J) |
| USB‑C C165948, P2 C49284723 | ◐ puxar do EasyEDA pelo LCSC (os mesmos da V4) |
| Sensor de ângulo, chave Hall, ímãs | ✖ falta: o Code escolhe o PN e busca o STEP (ímã = cilindro com as medidas do PN) |
| Bateria B1 / B2 / B3 | ✖ falta: o J manda o da escolhida; até lá, caixa com as medidas máximas da folha de dados |
| MKL02 | ✖ sem STEP público: caixa QFN‑16 3 × 3 pelo desenho da NXP |
| Demais peças JLCPCB | ✔ EasyEDA (`modelos/baixados/`, fora do Git) |
| Pot com chave, SRBV | — saíram do projeto na R2SL |

## 8. Tarefa da R2SL: fechar a Etapa 1 (portão A)

Refazer só o que mudou; o resto da Etapa 1 (PR #210) fica valendo.

1. **[Eletrônica]**
   - Esquema: RT1062 **DVJ6B** (conferir o mapa de bolas e o footprint contra `modelos/rt1062/`); sai o pot com chave (SW401) e a escada da SRBV (R401–R408); entram **2 sensores de ângulo + chave Hall do OFF** (escolha justificada, endereços I²C, alimentação, consumo em OFF) e a lógica do SYSOFF com a chave Hall; USB‑C C165948 e P2 C49284723 por baixo; FFC C3250113; indutor ≤ 1,9 mm (ou a alternativa da regra de alturas); conector da bateria conforme B1/B2/B3. ERC 0/0 nas duas placas.
   - BOM conferida de novo (LCSC/JLCPCB, Basic/Extended, estoque), sem cotação.
   - Bateria: tabela B1/B2/B3 (§4) com fabricante, distribuidor, venda em pequena quantidade, medidas do pack, NTC, conector, autonomia.
   - Alturas sob a placa de **todas** as peças da face de baixo e a **altura mínima da placa principal** que resulta (com USB‑C e P2 da V4).
2. **[Programação e som]** No sketch `etutti/firmware/slim/`: leitura dos 2 sensores de ângulo (7 posições com histerese e memória da última; volume contínuo), OFF pela chave Hall, **Full Speed forçado**; atualizar `PINOS.md` × sketch e o `FIRMWARE.md` (consumo em OFF e autonomia em prateleira). Compilar para Teensy 4.1.
3. **[Design]**
   - Criar o **`RESTRICOES_CASE.md`** (§3.1) com tudo o que já se sabe: alturas sob a placa, USB‑C/P2, indutor, conector e baia da bateria (B1/B2/B3, com o crescimento para a esquerda), FFC, hastes dos knobs, poste dos switches sobre o piso.
   - Knob C: corte cotado de cada knob (poço, mancal, haste, retenção, ímã, distância ao sensor, cliques e batentes) e o mecanismo de clique proposto; o anel de LED do volume.
   - Envelopes conferidos contra os STEP das peças novas; lista dos STEP que faltam.
4. **`FIT_CHECK.md`**: resumo da R2SL, itens do `RESTRICOES_CASE.md` que mudam o lado de fora do case, e **"Perguntas para o design"**. Parar no **portão A**. Nada de posicionamento, roteamento, cotação ou compra.
