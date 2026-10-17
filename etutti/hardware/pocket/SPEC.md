# eTuttino Pocket · especificação · v3

**Versão 3 — 17 out 2026.** Substitui a v2 (PRs #103 e #104, no histórico do git). Mantida pela gestão (Claude Chat com o J); o Code não edita este arquivo. Cada disciplina responde no seu relatório (`FIT_CHECK.md`, `ELETRONICA.md`, `FIRMWARE_SOM.md`), terminando com "Perguntas para a gestão". Protocolo completo no `CLAUDE.md`, seção "eTuttino Pocket — como trabalhamos".

Medidas em mm. **(conferir)** = estimativa a confirmar com a peça real ou o datasheet.

## Mudanças desde a versão anterior (v2)

Decisões do J sobre os relatórios do passo 1 da v2 (PR #104):

1. **Variante B · Seixo aprovada** (~251,5 de comprimento). Pequenas variações de tamanho não são problema. A e C saem.
2. **Sensor TMAG5253BA3** no lugar do DRV5056, ligado por grupos. O J aceita esperar estoque. A placa do Pocket passa a ser montada só na fábrica (X2SON não se solda em casa). Reserva, se a compra falhar: DRV5053 (SOT-23, sem EN).
3. **Desligamento automático em dois estágios, com o KEEP**: espera leve depois de 15 min sem tocar, desliga de verdade depois de mais 30. Religa girando o volume até o clique e de volta.
4. **Bateria com termistor (NTC, 3 fios) exigida.** Se não houver estoque, o J resolve depois com outros fornecedores; o TS fixo fica só como alternativa de montagem.
5. **Conector USB-C no case.** O Pocket fica preparado para o futuro: o conector externo, que carrega e passa o MIDI, é **USB-C**. O fio do VUSB (ou a solução equivalente da eletrônica) continua aceito por dentro.
6. **Luz de carga sem LED novo**: o STAT do carregador acende o vermelho do LED que já existe, por um diodo, inclusive com o Pocket desligado.
7. **Alto-falante Same Sky CLS0361-L152** (Ø36 × 6,0, 2 W, 8 Ω) com 8–12 cm³ fechados atrás.
8. **Pilha mais baixa**: a eletrônica avalia, mas não é crítico; alguns milímetros a mais não importam.
9. **Linha dos knobs em y = 49** aprovada. A página inicial passa a desenhar a grade de verdade (`controls.grille_outline`).
10. **Teensy a 396 MHz**, com a condição da §6: medir no motor do Pocket e voltar a 600 MHz se houver qualquer perda de resposta ou de som.
11. **Dois conflitos de contrato do passo 1**, que o D2 e o E2 resolvem juntos (§3):
    - **bateria**: o berço reservado (54 × 35) é menor que o pedido pela eletrônica (58 × 36 × 7 com PCM e fios);
    - **potenciômetro com chave**: o reservado (13 de corpo) é menor que o de 9 mm com chave (~16,6).
12. O passo 2 da v2 (P1 e P2) **não foi feito** e entra aqui, atualizado com os pinos e as decisões acima.

## 1. Resumo

| | Pocket v3 |
|---|---|
| Case | só plástico, Seixo, **variante B** (lado esquerdo em curva única), ~251,5 × 100 |
| Botões | 28 · G3–E5 · notas mais altas por fileira (4, 3, 2, 1): C5 · D5 · E5 · D♯5 |
| Passo, switches, sensores | grade hexagonal de 18,5, Gateron magnético, **TMAG5253BA3** por tecla, ligados por grupos |
| Interface | logo gravado, 2 knobs (volume com chave, seletor com clique), LED, grade do alto-falante |
| Som | só acordeom: 6 registros de fábrica + 2 presets livres; alto-falante Ø36 + fone 3,5 (o fone desliga o alto-falante) |
| Energia | LiPo 1S 1000 mAh com NTC; carrega por **USB-C**, toca enquanto carrega; ~6,9 h com fone, ~4,5 h com alto-falante (típicos, estimativa) |
| Teensy | 4.0 + Audio Board Rev D, a 396 MHz (§6) |

## 2. Teclado

Igual à v1 §2: 28 botões, regra C-griff, fileira 1 mais perto de quem toca, Dós e Fás com xadrez diagonal, botões convexos (domo baixo com saia). Na variante B a origem é `O = 98,45` (`pocket.json`); a grade de notas da firmware não muda.

## 3. Case (Seixo, variante B)

- Geometria em planta: `shape.py`, variante B, como no `pocket.json`. Largura de 100 constante, paredes externas verticais, área do teclado aberta com o chanfro e a folga lateral de 1 botão do eTuttino, rampa arredondada sem quinas vivas.
- O lado esquerdo é uma curva só, concêntrica com a ponta da rampa, com quinas de R 24 nas faces de trás e da frente.
- **Conectores na parede curva**: ressalto plano por dentro (ou inserto) para o **USB-C** e o fone de painel, na face de trás-esquerda.
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
| Trás | **logo gravado** (eTuttino Pocket), baixo-relevo de ~0,4 (conferir), acompanhando a curva |
| Meio | **knob esquerdo = volume com chave**, **knob direito = seletor** (encoder com clique), **LED** à direita; linha em y = 49 |
| Frente | **grade do alto-falante**, no plano a 13° voltado para quem toca, só sobre o cone |

Folga mínima de 5 entre knobs/LED e as bordas da área, e de 6 entre a grade e a rampa.

## 5. Som

- Alto-falante **Same Sky CLS0361-L152** (Ø36 × 6,0, 2 W, 8 Ω), compra direta, ligado por fio. Grade com área aberta ≥ ~30 % do cone, a ≤ 1–2 mm da membrana, junta entre o aro e a parede.
- Amplificador **PAM8302A** mono, na bateria, ganho reduzido por resistor (ajuste de ouvido). Desligado com o fone plugado, ~2 s depois da última voz e no desligamento automático.
- Fone 3,5 pela Audio Board, com contato de comutação na ponta para a detecção (HP_DET). Manga sempre no terra virtual (HP_VGND), nunca no GND.
- O volume vale para fone e alto-falante. A programação aplica uma equalização só para o alto-falante, quando não há fone: corte abaixo de ~400 Hz e limitador.

## 6. Energia e resposta

- **Arquitetura** (detalhe no `ELETRONICA.md`): carregador BQ24074 com power-path, buck-boost TPS63802 de 3,3 V, Teensy alimentado pelo 3,3 V com a ponte VUSB–VIN cortada, divisor da bateria no pino 16.
- **USB-C** no case, para carga e MIDI.
  - A eletrônica escolhe como ligar o USB-C ao Teensy 4.0, que tem micro-B. Por exemplo: USB-C de painel ou na placa, com um cabo interno curto até o micro-B do Teensy, tirando o 5 V para o carregador antes do Teensy.
  - O USB-C precisa dos resistores de 5,1 kΩ nos CC, para carregar com cabos C-C.
- **Bateria** LiPo 1S 1000 mAh tipo 603450, com PCM e **NTC (3 fios)** ligado ao TS do carregador.
- **Liga/desliga** pela chave do potenciômetro, com o circuito de partida e o **KEEP** (pino 10). O carregador fica antes da chave e carrega com o aparelho desligado.
- **Luz de carga**: o STAT do carregador acende o vermelho do LED por um diodo, sem pino do Teensy.
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

## Tarefas para o Code (v3)

Dois passos, cada um com o seu prompt, o seu PR e o seu merge.

- **Passo 1, design e eletrônica:** D2 e E2 juntos (os dois conflitos da §3 se resolvem entre eles), depois a placa (E2b).
- **Passo 2, programação e som:** P1 e P2, depois do merge do passo 1.

**A sessão de integração confere as reservas de cada contrato antes do PR**: cada peça escolhida pela eletrônica (medidas do datasheet) contra o espaço reservado pelo design, e cada pino do `PINOS.md` contra o sketch. Divergências vão no PR, como lista.

### Passo 1 · Design

- **D2. Modelo do Seixo, variante B.**
  - `case.py` do Pocket (CadQuery, só Seixo), a partir de `shape.py`, com fit check, renders e o `pcb_envelope.json` do Pocket.
  - Resolver com a eletrônica o berço da bateria e o potenciômetro com chave (§3), o ressalto do USB-C e do fone, e a caixa do alto-falante para o CLS0361-L152.
  - Detalhamento de fabricação da §3, peso estimado e rigidez da placa sobre os pilares.
  - Atualizar `pocket.json` (sem `provisional`), a página de revisão com a versão final da B, e o `FIT_CHECK.md`.

### Passo 1 · Eletrônica

- **E2. Fechar as peças.**
  - USB-C (§6) e a ligação ao Teensy.
  - Bateria com NTC (modelo e fornecedor).
  - Potenciômetro com chave que caiba (com o design).
  - Luz de carga pelo STAT.
  - Avaliar a pilha mais baixa (não crítico).
  - Atualizar `PINOS.md` (deixa de ser provisório), `POWER.md` e `ELETRONICA.md`.
- **E2b. Placa principal** (depois do `pcb_envelope.json` do D2).
  - Placa do Pocket com 2 multiplexadores, 28 TMAG5253BA3 no verso, portas do EN por grupo, carregador, conversor, amplificador, JSTs da bateria e do alto-falante, fios do jack e do USB.
  - Plaquinha dos knobs.
  - DRC 0/0/0, conferência placa × firmware (`KEY_INPUT`), rigidez (`mechanics.py`), Gerbers e BOM/CPL da JLCPCB com o TMAG5253 marcado como peça consignada ou de "global sourcing".

### Passo 2 · Programação e som (depois do merge do passo 1)

- **P1. Firmware e som do Pocket.**
  - Sketch com `ETUTTI_MODEL_POCKET` seguindo o `PINOS.md` final (2 multiplexadores, leitura por grupos com 45 µs, `SENSOR_ZERO`/`PRESENT_MIN` do TMAG5253BA3, VBAT, HP_DET, AMP_SD, KEEP em `startup_early_hook`, LED vermelho no 13).
  - Os 6 registros de fábrica da §8 com a 3ª palheta de 8' do Musette, a estrutura de preset e os parâmetros editáveis, também no `websynth.js`.
  - Só acordeom: o Pocket compila sem as amostras de piano e violão; o eTuttino continua compilando igual.
  - Equalização do alto-falante, desligamento em dois estágios, bateria e "carregando" na página.
  - **Medir no Teensy do J, a 396 e a 600 MHz**: CPU no pior caso, tempo de leitura por grupos, memória e quantos presets cabem. Ouvir e comparar os dois clocks. Decidir o clock pelas condições da §6.
  - Propor o formato SysEx e a calibração guiada.
  - Relatório no `FIRMWARE_SOM.md`.
- **P2. Páginas.**
  - `/etutti/` e `/etutti/pocket/` (com a revisão) só em português, sem seletor de língua.
  - A página inicial desenha a grade de verdade (`controls.grille_outline`).
  - Regra "só português" no agente `programacao-som` e no `CLAUDE.md`.

## 11. Perguntas para o J

Nenhuma em aberto. As próximas virão dos relatórios do passo 1 (sobretudo a solução do potenciômetro com chave e o USB-C).
