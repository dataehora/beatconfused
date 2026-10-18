# eTuttino Pocket · especificação · v5

**Versão 5 — 18 out 2026.** Substitui a v4 (PRs #107 e #108, no histórico do git). Mantida pela gestão (Claude Chat com o J); o Code não edita este arquivo. Cada disciplina responde no seu relatório (`FIT_CHECK.md`, `ELETRONICA.md`, `FIRMWARE_SOM.md`), terminando com "Perguntas para a gestão". Protocolo completo no `CLAUDE.md`, seção "eTuttino Pocket — como trabalhamos".

**Objetivo da v5: simplificar a conexão USB (volta ao micro-USB), acertar o acabamento dos knobs e fechar a versão física.** A encomenda do protótipo só acontece quando o J decidir. A programação e a engenharia de som continuam para depois.

Medidas em mm. **(conferir)** = estimativa a confirmar com a peça real ou o datasheet.

## Mudanças desde a versão anterior (v4)

Decisões do J sobre o PR #108:

1. **Placa principal de 4 camadas confirmada**: é o padrão para sensores Hall analógicos e eletrônica chaveada (conversor, classe D) na mesma placa; os planos de GND e 3,3 V reduzem ruído no áudio e nas leituras.
2. **Transistor Q22 aprovado** (a chave do volume segura o 3,3 V com USB presente, para gravar a firmware e para os testes do manual).
3. **USB-C abandonado. Volta ao micro-USB, a solução mais simples** (§6):
   - sai a plaquinha do painel (e o segundo pedido de montagem);
   - o micro-USB do Teensy é estendido até a parede do case por um **cabo de extensão micro-B de painel** (fêmea na parede, macho de 90° no Teensy);
   - o carregador recebe o 5 V por um **fio do pad VUSB** do Teensy, com a ponte VUSB–VIN cortada;
   - o fone vira um **jack de painel ligado por fios**, como no eTuttino, com o contato de comutação da ponta para a detecção.
4. **Segurança da bateria igual à da v4**: as proteções estão na placa principal e na bateria, não no conector (§6, "Segurança da carga").
5. **Porca do potenciômetro escondida** (§4): acabamento a definir pelo J (§11).
6. **Botão de gravação do Teensy**: o design confere se dá para alcançá-lo com o case fechado (§3).

## 1. Resumo

| | Pocket v3 |
|---|---|
| Case | só plástico, Seixo, **variante B** (lado esquerdo em curva única), ~251,5 × 100 |
| Botões | 28 · G3–E5 · notas mais altas por fileira (4, 3, 2, 1): C5 · D5 · E5 · D♯5 |
| Passo, switches, sensores | grade hexagonal de 18,5, Gateron magnético, **TMAG5253BA3** por tecla, ligados por grupos |
| Interface | logo gravado, 2 knobs (volume com chave, seletor com clique), LED, grade do alto-falante |
| Som | só acordeom: 6 registros de fábrica + 2 presets livres; alto-falante Ø36 + fone 3,5 (o fone desliga o alto-falante) |
| Energia | LiPo 1S 1000 mAh com NTC; carrega pelo **micro-USB** (o mesmo do MIDI e da gravação), toca enquanto carrega; ~6,7 h com fone, ~4,5 h com alto-falante (típicos, estimativa) |
| Teensy | 4.0 + Audio Board Rev D, a 396 MHz (§6, a confirmar na etapa de programação) |

## 2. Teclado

Igual à v1 §2: 28 botões, regra C-griff, fileira 1 mais perto de quem toca, Dós e Fás com xadrez diagonal, botões convexos (domo baixo com saia). Na variante B a origem é `O = 98,45` (`pocket.json`); a grade de notas da firmware não muda.

## 3. Case (Seixo, variante B)

- Geometria em planta: `shape.py`, variante B, como no `pocket.json`. Largura de 100 constante, paredes externas verticais, área do teclado aberta com o chanfro e a folga lateral de 1 botão do eTuttino, rampa arredondada sem quinas vivas.
- O lado esquerdo é uma curva só, concêntrica com a ponta da rampa, com quinas de R 24 nas faces de trás e da frente.
- **Conectores na parede curva**: ressalto plano por dentro, com janelas para o **micro-USB de painel** (cabo de extensão) e o **jack de fone de painel**, na face de trás-esquerda. A fixação do micro-USB de painel segue a peça escolhida pela eletrônica (orelhas de parafuso ou porca).
- **Botão de gravação do Teensy**: conferir se é alcançável com o case fechado (por exemplo, um furo pequeno no fundo para um clipe). Se não der, o manual explica como abrir.
- **Placa principal de 4 camadas**, 1,2 mm.
- **Bateria**: berço para **7 × 36 × 58** (célula com PCM, NTC e dobra dos fios), +8 % para inchaço, saída de ~60 mm de fio com JST, acesso pelo fundo sem abrir a tampa, fora de baixo da placa principal. O comprimento pode crescer um pouco para caber.
- **Potenciômetro com chave**: resolver com a eletrônica, **sem mudar a altura da tampa**. Opções:
  1. 9 mm com chave montado deitado (eixo paralelo à placa) numa plaquinha perpendicular à tampa;
  2. 16 mm com chave, mais baixo e mais largo;
  3. outra peça de altura ≤ 13 que a eletrônica achar.
  A plaquinha dos knobs pode mudar de forma; a linha dos knobs fica em y = 49.
- **Alto-falante**: CLS0361-L152, Ø36 × 6,0 (o D1 reservou 5,5: conferir), com 8–12 cm³ de volume traseiro fechado e vedado. A caixa pode crescer para os lados se precisar.
- Fundo parafusado. Detalhar para fabricação: espessuras de parede, bosses, pilares de apoio da placa (rigidez como no eTuttino: ≤ 0,05 mm a 3 N), berço da bateria, caixa do alto-falante, folgas de impressão (resina e MJF), peso estimado.

## 4. Área de interface (de trás para a frente)

| Zona | O que tem |
|---|---|
| Trás | **logo gravado** (eTuttino Pocket), baixo-relevo de ~0,4, **reto (horizontal)** e centrado na zona |
| Knobs | a **porca M7 do potenciômetro não fica à mostra**; os dois knobs têm o mesmo acabamento (solução na §11) |
| Meio | **knob esquerdo = volume com chave**, **knob direito = seletor** (encoder com clique), **LED** à direita; linha em y = 49 |
| Frente | **grade do alto-falante**, no plano a 13° voltado para quem toca, só sobre o cone |

Folga mínima de 5 entre knobs/LED e as bordas da área, e de 6 entre a grade e a rampa.

## 5. Som

- Alto-falante **Same Sky CLS0361-L152** (Ø36 × 6,0, 2 W, 8 Ω), compra direta, ligado por fio. Grade com área aberta ≥ ~30 % do cone, a ≤ 1–2 mm da membrana, junta entre o aro e a parede.
- Amplificador **PAM8302A** mono, na bateria, ganho reduzido por resistor (ajuste de ouvido). Desligado com o fone plugado, ~2 s depois da última voz e no desligamento automático.
- Fone 3,5 pela Audio Board, com contato de comutação na ponta para a detecção (HP_DET). Manga sempre no terra virtual (HP_VGND), nunca no GND.
- O volume vale para fone e alto-falante. A programação aplica uma equalização só para o alto-falante, quando não há fone: corte abaixo de ~400 Hz e limitador.

## 6. Energia e resposta

- **Arquitetura** (detalhe no `ELETRONICA.md`): carregador BQ24074 com power-path, buck-boost **TPS63001** de 3,3 V, Teensy alimentado pelo 3,3 V com a ponte VUSB–VIN cortada, divisor da bateria no pino 16.
- **Micro-USB** no case, para carga, MIDI e gravação da firmware: cabo de extensão micro-B de painel (fêmea na parede, macho de 90° no Teensy), curto.
  - O 5 V para o carregador sai do **pad VUSB** do Teensy por um fio (≥ 26 AWG, com alívio de tração: cola ou abraçadeira), com a **ponte VUSB–VIN cortada**: o Teensy é alimentado pelo 3,3 V do conversor e nada volta para a USB.
  - Carrega com qualquer carregador ou porta USB, incluindo carregadores USB-C com cabo C → micro-B (o próprio cabo tem o resistor que o carregador precisa).
  - Conferir com a PJRC a corrente admissível no pad e no conector micro-B do Teensy 4.0 (o carregador limita a entrada a 500 mA).
- **Bateria** LiPo 1S 1000 mAh tipo 603450, com PCM e **NTC (3 fios)** ligado ao TS do carregador.
- **Liga/desliga** pela chave do potenciômetro, com o circuito de partida e o **KEEP** (pino 10). O carregador fica antes da chave e carrega com o aparelho desligado.
- **Luz de carga**: o STAT do carregador acende o vermelho do LED (por diodo e um transistor) **só com o Pocket desligado**, sem pino do Teensy.
- **Segurança da carga** (mesma da v4, independente do conector):
  - BQ24074 com limite de entrada de 500 mA (modo USB500), proteção de sobretensão na entrada (até 10,5 V), carga de 500 mA, regulação térmica e timer de carga;
  - NTC da bateria no TS do carregador: a carga para se a bateria esquentar ou estiver fria demais;
  - proteção própria da bateria (PCM): sobrecarga, descarga profunda, curto;
  - corte da ponte VUSB–VIN: a USB nunca alimenta o Teensy direto nem recebe tensão de volta;
  - luz de carga (Q31) e partida com USB (Q22) como na v4.
- **ESD**: sem a plaquinha, pôr um **diodo TVS no VBUS** na placa principal, junto da entrada do carregador. As linhas de dados ficam com a proteção do próprio Teensy (risco aceito no protótipo).
- **Sensores** TMAG5253BA3 ligados por grupo (S3 escolhe canais 0–7 ou 8–15; SENS_EN desliga todos). Espera de 45 µs depois de trocar de grupo.
- **Teensy a 396 MHz**, mantido só se as condições abaixo forem atendidas no motor do Pocket (Musette com 3 palhetas de 8', 8 vozes, reverb, equalização do alto-falante), **medidas no Teensy do J**:
  - CPU do áudio ≤ 40 % no pior caso;
  - leitura completa das 28 teclas por grupos ≤ ~400 µs (≥ 2,5 kHz por tecla);
  - nenhuma diferença audível de som em relação a 600 MHz. A taxa de amostragem (44,1 kHz) e a resolução não dependem do clock; só a folga de CPU muda.

  Se qualquer condição falhar, voltar a 600 MHz (custa ~1,4 h de autonomia, estimativa). 240 MHz só se sobrar folga, como opção.
- **Autonomia estimada** (`POWER.md`, sem medição de corrente ainda): ~6,9 h com fone e ~4,5 h com alto-falante (típicos), com fone ~4,2 h no pior caso. Medir no protótipo.

## 7. Knobs

- **Esquerdo**: volume contínuo, com chave liga/desliga no início do curso (girar além do clique, como rádio).
- **Direito**: encoder com clique.
  - Girar troca o preset (1 → 8, só os presets ocupados).
  - Clique depois de girar grava o preset atual como o de ligar.
  - Segurar o clique e girar muda a **oitava** (−2 … +2). A transposição de ±12 semitons fica só na página.
  - O LED confirma cada mudança (piscada curta).

## 8. Presets

- **Até 8**: os 6 de fábrica (que o usuário pode sobrescrever) e mais 2 livres.
- **De fábrica**, registros clássicos de acordeom, fixos na firmware e restauráveis pela página ("Voltar aos 6 originais"):

  | Preset | Palhetas (registro de acordeom) |
  |---|---|
  | Bassoon | 16' (L) |
  | Bandoneon | 16' + 8' (L M) |
  | Organ | 16' + 4' (L H) |
  | Violin | 8' + 8' afinadas com batimento (M M) |
  | Musette | 8' + 8' + 8' (M− M M+) |
  | Piccolo | 4' (H) |

  O motor de palhetas tem hoje 4 palhetas (16' cassotto, 8' M1, 8' M2, 4'). O Musette precisa de uma 3ª palheta de 8'.
- **Parâmetros editáveis na página**, por preset: combinação de palhetas, desafinação (cents), ataque, decay, sustain, release, filtro de tom, reverb, nível, e outros usuais de sintetizador que caibam no motor.
- **Memória**: medir quantos presets cabem na EEPROM emulada do Teensy 4.0 (e na flash, se precisar) e informar se dá para passar de 8. O seletor percorre no máximo 8; presets extras ficariam só na página, para carregar nos 8 lugares.
- Presets e configurações por SysEx; volume e preset também por CC, como no eTuttino.
- **Só acordeom**: sem as amostras de piano e violão. Um preset de piano pode vir depois, fora do núcleo do Pocket.

## 9. Programado pelo beatconfused.com

- Oitava (−2 … +2) e transposição (±12).
- Presets (§8), incluindo voltar aos 6 originais.
- Conversão C-griff ↔ B-griff (CC 24).
- Calibração das teclas: propor uma calibração guiada (apertar cada tecla até o fundo), além da automática de repouso ao ligar. A gestão decide.
- **Desligamento automático em dois estágios**: espera leve depois de N minutos sem tocar (padrão 15; Teensy em clock baixo, codec e amplificador desligados, sensores lidos devagar, acorda numa tecla), e desliga de verdade (KEEP baixo) depois de mais M minutos (padrão 30). N e M configuráveis.
- Bateria: nível e "carregando" na página.

## 10. Línguas e publicação

- Até a versão final, as páginas do Pocket e a página inicial da família são publicadas **só em português**. As outras línguas, os manuais e os textos para o usuário final vêm na versão final.
- As páginas pausadas (`/etutti/etuttino/`, `manuais/`, `models/`) ficam como estão.

## Tarefas para o Code (v5)

**Só a parte física. Não rodar P1 nem P2. Não encomendar nada.**

Um passo só, um PR, um merge. F3 e F4 juntos (design e eletrônica fecham os contratos entre eles), depois M2.

**A sessão de integração confere as reservas antes do PR** (cada peça do `PECAS.json` contra o case, `PINOS.md` contra o `KEY_INPUT`). Ao final, **nenhuma divergência aberta**.

### Design

- **F3. Case para o micro-USB, knobs e botão do Teensy.**
  - Tirar o ressalto da plaquinha do painel; janelas e fixação para o micro-USB de painel e o jack de fone de painel escolhidos pela eletrônica.
  - Passagem do cabo de extensão até o micro-B do Teensy (raio de curvatura, sem forçar o plugue de 90°).
  - Acabamento dos knobs conforme a decisão do J (§11, pergunta 1), igual nos dois.
  - Acesso ao botão de gravação do Teensy com o case fechado, se possível.
  - Fit check sem divergências, renders, `pocket.json`, `pcb_envelope.json` e página de revisão atualizados.

### Eletrônica

- **F4. Fechamento para o micro-USB.**
  - Escolher o cabo de extensão micro-B de painel (fêmea de painel com fixação, macho de 90°, curto) e o jack de fone de painel com contato de comutação na ponta.
  - Placa principal: entrada do VBUS por fio vindo do pad VUSB do Teensy, com TVS no VBUS; fios do jack para HP_L, HP_R, HP_VGND e HP_DET.
  - Remover a plaquinha do painel do projeto (manter os arquivos no histórico).
  - Conferir com a PJRC a corrente no pad VUSB e no micro-B do Teensy 4.0.
  - DRC 0/0/0 nas três placas (principal, knobs, volume), placa × firmware 28/28, rigidez ≤ 0,05 mm.
  - Gerbers, BOM, CPL e BOM do kit atualizados; `PECAS.json`, `PINOS.md`, `POWER.md`, `ELETRONICA.md` e `pcb/MANUAL_ELETRICO.md`.

### Manual de montagem

- **M2. Atualizar `/etutti/pocket/manual/`** (dono: design, com o conteúdo elétrico da eletrônica): micro-USB de painel e fio do VUSB no passo do Teensy, jack de painel com fios, sem a plaquinha do painel, acabamento dos knobs, acesso ao botão do Teensy. Figuras refeitas onde mudou. Conferir no navegador.

## 11. Perguntas para o J

1. **Porca do potenciômetro (knob da esquerda):** como esconder?
   - (a) **rebaixo na tampa** onde a porca assenta rente, coberto pelo knob, com o mesmo rebaixo no knob da direita (recomendado);
   - (b) knobs com saia que desce e cobre a porca;
   - (c) encoder também com rosca e porca (os dois fixos do mesmo jeito), com o rebaixo de (a).
