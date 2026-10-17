# eTuttino Pocket · especificação · v1

**Versão 1 — primeira proposta.** O eTuttino Pocket é a versão compacta do eTuttino: o mesmo teclado C-griff com 28 botões (G3–E5), bateria para tocar ~4 h com fone, e a mesma área de interface (volume, seletor de instrumento, LED), sem a zona da tela. A pouca quantidade de botões é compensada pelo que se programa pela página do beatconfused.com.

Mesmo protocolo do case do eTuttino (`../case/SPEC.md`): o Claude Chat mantém este arquivo, com a seção "Mudanças desde a versão anterior" a cada versão; o Claude Code implementa, confere e responde em `FIT_CHECK.md`, terminando com "Perguntas para o design".

Medidas em mm. **(conferir)** = estimativa que precisa ser confirmada com a peça real ou o datasheet.

Gerado/verificado por `layout.py` (só biblioteca padrão do Python): `build/pocket_keys.csv`, `build/pocket_top.svg`, `build/pocket.json` e `POWER.md`.

## 1. O que muda e o que fica igual ao eTuttino

| | eTuttino | Pocket |
|---|---|---|
| Botões | 44, G3–E6 | **28, G3–E5** |
| Planta | ~331 × 100 | **~237 × 100** (−28 %) |
| Passo, fileiras, botões, switches, sensores | P 18,5; fileiras 16,02; Gateron KS-20; DRV5056A3 | **igual** |
| Multiplexadores | 3 × CD74HC4067 | **2** (32 canais, 4 livres) |
| Interface | tela/gravação, volume, seletor, LED, grade a 13° | **sem zona da tela**; volume, seletor, LED, grade a 13° |
| Energia | só USB | **LiPo 1S ~2000 mAh**, carrega pelo USB, toca enquanto carrega |
| Conexões (face esquerda) | Micro-B + fone 3,5 | **igual** + chave liga/desliga (ver §6) |
| Versões | Seixo e Madeira | as duas, mesma geometria |

O sistema de coordenadas, as alturas (deck em z 17,4, interface em z 33 com a descida de 13°), o chanfro, a rampa arredondada e os botões (domo baixo com saia; xadrez diagonal nos Dós e Fás) seguem a `../case/SPEC.md` v9.

## 2. Teclado C-griff (28 botões, G3–E5)

Mesma regra da SPEC do case, com os limites do Pocket. `n` = semitons a partir de G3; centro do botão em `x = O + xp · P`, com **`O = 84`** (no eTuttino, 104).

| Fileira | Notas | Condição | `xp` | Botões |
|---|---|---|---|---|
| 1 (mais perto de quem toca, y 74,03) | A3 … **D#5** | `n % 3 == 2`, `n ≤ 20` | `(n − 2) / 3` | 7 |
| 2 (y 58,01) | G3 … **E5** | `n % 3 == 0`, `n ≤ 21` | `n / 3 − 0,5` | 8 |
| 3 (y 41,99) | G#3 … **D5** | `n % 3 == 1`, `n ≤ 19` | `(n − 1) / 3` | 7 |
| 4 (y 25,97) | A3 … **C5** | `n = 2, 5, …, 17` | `(n − 2) / 3 + 0,5` | 6 |

- Faixa cromática completa de G3 a E5; a fileira 4 duplica a 1, como no eTuttino.
- Dós e Fás com xadrez: C4 (fileiras 1 e 4), F4, C5 (fileiras 1 e 4).
- Botões das pontas da fileira 2: (74,75; 58,01) e (204,25; 58,01).
- Tabela da firmware e da página, na convenção de `generate.py` (primeira nota MIDI, quantidade, deslocamento, primeira coluna): `[[57, 7, 0, 1], [55, 8, -0.5, 0], [56, 7, 0, 1], [57, 6, 0.5, 1]]`, `GRID_COLS = 8`.

## 3. Caixa

- Abertura, chanfro, folgas e contorno: as mesmas regras da SPEC do case (folga lateral de 1 botão seguindo "<" e ">", caixa = abertura + 10,3, R 22,5 / R 32,8 concêntricos aos botões das pontas da fileira 2).
- Comprimento total ~237,1 (a borda direita fica em `O + 6,5 P + 32,8`). Largura 100 constante.
- Alturas iguais ao eTuttino (verificar no modelo; a bateria não entra embaixo do teclado, ver §5).

## 4. Área de interface

Mesma ordem do eTuttino, mais estreita porque não há zona da tela:

| Item | Posição / medidas |
|---|---|
| Volume | potenciômetro contínuo, eixo em (12; 45), knob Ø 9 |
| Seletor de instrumento | encoder com clique e giro infinito, eixo em (28; 45), knob Ø 9 (7 mm entre os knobs; no eTuttino, 8) |
| LED | Ø 3,5 em (40; 45); 5,3 mm até a borda de cima da rampa |
| Grade | furos Ø 1,9 a passo de 4, retângulo x 8–32, y 61–88, cantos R 3, no plano a 13°. Com O = 84 a curva da frente da rampa chega à face da frente em x ≈ 27,4 (borda de cima), 20 mm mais à esquerda que no eTuttino: conferir no modelo a folga de 6 mm entre a grade e a rampa |
| Atrás dos knobs (y 0–35) | plano liso, sem rebaixo; pode levar o nome gravado |

## 5. Energia

### Orçamento (detalhe em `POWER.md`)

- Trilho único de 3,3 V: ~292 mA típicos, ~449 mA no pior caso. Os 28 sensores Hall (6 mA típicos cada, 10 mA máx., datasheet TI) são mais da metade.
- 4 h exigem ~1360 mAh no típico e ~2090 mAh no pior caso (eficiência 90 %, 85 % da capacidade útil).
- **Proposta: LiPo 1S de ~2000 mAh** → ~5,9 h típicas, ~3,8 h no pior caso. Com 2500 mAh: 7,3 h / 4,8 h, mas a bateria cresce.

### Arquitetura

- **Carregador com power-path** (toca enquanto carrega), 5 V do USB, ~1 A (~2,5 h para carregar). Ex.: TI BQ24074 (conferir).
- **Buck-boost 3,3 V** da bateria (3,0–4,2 V) para todo o circuito. Ex.: TI TPS63020 (conferir). O AMS1117 da placa do eTuttino sai.
- **Teensy alimentado pelo pino 3V3**, com a ligação VUSB–VIN cortada: o 5 V do USB vai só para o carregador e para a detecção de USB do Teensy; o regulador interno do Teensy fica sem uso (conferir com a PJRC).
- **Medição da bateria**: divisor 100 k / 100 k no pino 16 (A2), livre porque agora são 2 multiplexadores. Corte a 3,3 V por célula na firmware; o carregador/conversor protegem abaixo disso.
- Bateria com proteção própria (PCM), conector JST PH 2 pinos.

### Onde fica

- **Embaixo da frente da interface**, sob a grade: baia de ~44 × 50 × 9 (x 3–47, y 48–98, do fundo até z ~11). Bateria de referência 804050 (8 × 40 × 50, ~2000 mAh, conferir).
- A placa principal **não passa** por essa baia (o contorno da PCB recua ali). Assim a área do teclado continua com a altura do eTuttino e os pilares de apoio não mudam.
- A pilha Teensy + Audio Board continua no canto de trás à esquerda.
- Fixação da bateria: berço impresso no fundo + fita dupla face de espuma; nada de parafuso encostando na célula.

## 6. Ligar, desligar e o LED

- **Liga/desliga**: proposta = potenciômetro de volume **com chave** (como os rádios: girar além do clique liga). Alternativa: chave deslizante na face esquerda, ao lado do USB e do fone. A chave corta o EN do conversor 3,3 V; o carregador continua carregando com o aparelho desligado.
- **LED** (o mesmo bicolor do eTuttino), com novos estados:

  | Estado | LED |
  |---|---|
  | lendo as teclas ao ligar | laranja |
  | tocando, bateria > 20 % | verde |
  | bateria ≤ 20 % | laranja fixo |
  | bateria ≤ 5 % ou erro de sensor/codec | vermelho piscando |
  | carregando, ligado | verde pulsando devagar |
  | carregando, desligado | o sinal STAT do carregador acende o vermelho por um diodo (conferir) |

## 7. Programável pelo beatconfused.com

Com só duas oitavas, o que não cabe nos botões vai para a página `/etutti/` (Web MIDI, cabo USB). Tudo é gravado na EEPROM do Teensy e funciona depois sem computador.

1. **Oitava e transposição**: oitava −2 … +2, transposição ±12 semitons. No instrumento: segurar o clique do seletor (≥ 1 s) e girar = oitava (proposta).
2. **Presets do usuário**: até 8 (instrumento, registros do acordeom, reverb, transposição, oitava, curva de velocidade). A página escolhe se o seletor percorre os instrumentos ou os presets.
3. **C-griff / B-griff** (CC 24, já existe), **curva de velocidade** (CC 9) e **recalibração** (CC 14).
4. **Desligamento automático**: após N minutos sem tocar (padrão 15), silencia e reduz o consumo; a página mostra e muda N.
5. **Bateria na página**: nível e estado de carga, lidos do Teensy.
6. Os presets e as configurações vão por **SysEx** (ID 0x7D, uso não comercial); os controles do dia a dia continuam por CC.

## 8. Fabricação

- Seixo e Madeira como no eTuttino; Madeira em bloco bruto menor (~255 × 110 × 40).
- Fundo com acesso à bateria por 4 parafusos (trocar a bateria sem abrir a tampa).
- A grade sobre a bateria é só ventilação (o Pocket não tem alto-falante).

## 9. Entregáveis pedidos ao Claude Code (v1)

1. ~~`layout.py`, teclas, planta e orçamento~~ — feito nesta versão.
2. `case.py` com `MODEL = "etuttino" | "pocket"`: chaves, `O_KEYS`, interface sem zona da tela, baia da bateria; `fit_check.py` para o Pocket → `FIT_CHECK.md` desta pasta.
3. `pcb_envelope.py` para o Pocket → placa principal com 2 multiplexadores, carregador, buck-boost, divisor da bateria e conector da bateria; DRC 0/0/0 e conferência com a firmware 28/28.
4. Firmware: modelo escolhido na compilação (`ETUTTI_MODEL_POCKET`), nome USB "eTuttino Pocket", bateria e LED (§6), oitava/transposição, presets por SysEx, desligamento automático.
5. Página `/etutti/`: "eTuttino Pocket" no seletor de modelo, com os 28 botões e o painel de bateria e presets.

## 10. Perguntas para o J

1. Interface: está bom tirar a zona da tela e aproximar os knobs (7 mm entre eles) para ganhar comprimento? Mantendo tudo como no eTuttino, o Pocket teria ~257 mm.
2. Liga/desliga no volume (estilo rádio) ou chave deslizante na face esquerda?
3. Bateria de 2000 mAh (~5,9 h típicas) ou 2500 mAh (mais folga, baia maior)?
4. Os 28 botões em 18,5 mm de passo (mesmo toque do eTuttino) ou um passo menor para encolher mais? Um passo menor muda switch, placa e capas.
