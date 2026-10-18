# eTuttino Pocket · especificação · v4

**Versão 4 — 18 out 2026.** Substitui a v3 (PRs #105 e #106, no histórico do git). Mantida pela gestão (Claude Chat com o J); o Code não edita este arquivo. Cada disciplina responde no seu relatório (`FIT_CHECK.md`, `ELETRONICA.md`, `FIRMWARE_SOM.md`), terminando com "Perguntas para a gestão". Protocolo completo no `CLAUDE.md`, seção "eTuttino Pocket — como trabalhamos".

**Objetivo da v4: fechar toda a parte física do Pocket e escrever o manual de montagem.** A programação e a engenharia de som ficam para depois (§9 e §10 continuam valendo como requisitos, mas nenhuma tarefa de firmware ou de som roda nesta versão).

Medidas em mm. **(conferir)** = estimativa a confirmar com a peça real ou o datasheet.

## Mudanças desde a versão anterior (v3)

Decisões do J sobre os relatórios do passo 1 da v3 (PR #106). Todas as propostas da gestão foram aceitas:

1. **Logo reto (horizontal)**, centrado na zona de trás da interface, como nos desenhos do D1. Ele deixa de acompanhar a curva (que o deixava inclinado ~55°).
2. **USB-C e fone em duas janelas** afundadas na parede curva (sem inserto).
3. **R 1 nas arestas de cima das paredes** (deck e interface) confirmado.
4. **Caixa do alto-falante de 18,5 cm³** mantida.
5. **Casca de cima em resina** (por causa do logo); fundo, tampinha da bateria e fundo da caixa do alto-falante em MJF.
6. **Placa principal de 4 camadas** aceita.
7. **Conversor TPS63001** (LCSC C28060) no lugar do TPS63802.
8. **Cabos soldados** nas plaquinhas (knobs, volume, painel) e **cabo micro-B de 90° cortado e soldado** na plaquinha do painel, aceitos para o protótipo.
9. **Bateria de 3 fios (NTC), 1000 a 1200 mAh**, tipo 603450. Fornecedor fica para depois.
10. **Luz de carga**: o vermelho acende pelo carregador **só com o Pocket desligado** (um transistor). Ligado, quem mostra "carregando" é a firmware (verde pulsando), na etapa de programação.
11. **Potenciômetro com chave** (RK0972S deitado numa plaquinha em pé, preso pela porca M7) e **plaquinha dos knobs com abas** para o encoder, aprovados.
12. **Corrigir as divergências de contrato** listadas no PR #106 e **pôr proteção ESD no USB-C** (Tarefas F1/F2).
13. **Manual de montagem do Pocket**, no modelo do manual do eTuttino (Tarefa M1), só em português.
14. **A programação e o som (P1, P2 da v3) ficam para depois** da parte física. Não iniciar.

## 1. Resumo

| | Pocket v3 |
|---|---|
| Case | só plástico, Seixo, **variante B** (lado esquerdo em curva única), ~251,5 × 100 |
| Botões | 28 · G3–E5 · notas mais altas por fileira (4, 3, 2, 1): C5 · D5 · E5 · D♯5 |
| Passo, switches, sensores | grade hexagonal de 18,5, Gateron magnético, **TMAG5253BA3** por tecla, ligados por grupos |
| Interface | logo gravado, 2 knobs (volume com chave, seletor com clique), LED, grade do alto-falante |
| Som | só acordeom: 6 registros de fábrica + 2 presets livres; alto-falante Ø36 + fone 3,5 (o fone desliga o alto-falante) |
| Energia | LiPo 1S 1000 mAh com NTC; carrega por **USB-C**, toca enquanto carrega; ~6,9 h com fone, ~4,5 h com alto-falante (típicos, estimativa) |
| Teensy | 4.0 + Audio Board Rev D, a 396 MHz (§6, a confirmar na etapa de programação) |

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
| Trás | **logo gravado** (eTuttino Pocket), baixo-relevo de ~0,4, **reto (horizontal)** e centrado na zona |
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
- **USB-C** no case, para carga e MIDI.
  - A eletrônica escolhe como ligar o USB-C ao Teensy 4.0, que tem micro-B. Por exemplo: USB-C de painel ou na placa, com um cabo interno curto até o micro-B do Teensy, tirando o 5 V para o carregador antes do Teensy.
  - O USB-C precisa dos resistores de 5,1 kΩ nos CC, para carregar com cabos C-C.
- **Bateria** LiPo 1S 1000 mAh tipo 603450, com PCM e **NTC (3 fios)** ligado ao TS do carregador.
- **Liga/desliga** pela chave do potenciômetro, com o circuito de partida e o **KEEP** (pino 10). O carregador fica antes da chave e carrega com o aparelho desligado.
- **Luz de carga**: o STAT do carregador acende o vermelho do LED (por diodo e um transistor) **só com o Pocket desligado**, sem pino do Teensy.
- **USB-C com proteção ESD** (diodo TVS de linha de dados e VBUS, o menor que couber).
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

## Tarefas para o Code (v4)

**Só a parte física e o manual de montagem. Não rodar P1 nem P2.**

Um passo só, um PR, um merge. Ordem: F1 e F2 juntos (design e eletrônica fecham os contratos entre eles), depois M1.

**A sessão de integração confere as reservas antes do PR**: cada peça do `pcb/PECAS.json` (medidas do datasheet) contra o espaço do case, e o `PINOS.md` contra o `KEY_INPUT` da placa. Ao final, **nenhuma divergência aberta**: a parte física fica congelada para o protótipo.

### Design

- **F1. Acabamento e fechamento do case.**
  - Logo reto, centrado (Mudança 1).
  - Bolso do conector da bateria para o par JST PH de 3 vias encaixado (≥ 14,5 × 9,0 × 6,0, conferir com a peça), e o rabicho até ele.
  - Espaço para as abas da plaquinha dos knobs (x 27,0–35,2; y 40,0–42,5 e 56,0–57,5), conferindo a parede da caixa do alto-falante.
  - Furo e ressalto do fone para o Same Sky SJ1-3525N.
  - Plaquinha do painel: resolver a perna da carcaça do USB-C e o parafuso M2 sobre o plugue micro-B (com a eletrônica).
  - Lista de materiais por peça (resina em cima, MJF no resto), arquivos finais em `case/out/`, renders finais, fit check sem divergências, `pocket.json`, `pcb_envelope.json` e página de revisão atualizados.

### Eletrônica

- **F2. Fechamento das placas.**
  - Placa principal com o TPS63001, a luz de carga só com o aparelho desligado (transistor), e **ESD no USB-C** (plaquinha do painel ou placa principal, onde couber).
  - Ajustes das divergências 2 a 4 do PR #106, com o design.
  - DRC 0/0/0 nas quatro placas, conferência placa × firmware 28/28, rigidez ≤ 0,05 mm.
  - Gerbers, BOM e CPL finais (TMAG5253 marcado como peça fora do estoque da JLCPCB).
  - **BOM completo do kit**: tudo o que se compra, com quantidades, códigos e links, incluindo a sobra de peças pequenas.
  - Atualizar `PECAS.json`, `PINOS.md`, `POWER.md` e `ELETRONICA.md`.
  - Entregar ao design o conteúdo elétrico do manual (passos de solda, testes com multímetro e as fotos/figuras que precisa).

### Manual de montagem

- **M1. Manual de montagem do eTuttino Pocket** em `/etutti/pocket/manual/`, **só em português**, noindex, no modelo do `etutti/manuais/` do eTuttino (mesmo estilo, lightbox, figuras numeradas com balões e a tabela "Lista de peças"). O manual de uso fica para a etapa de programação.
  - **Dono nesta versão: o agente design** (figuras 3D e páginas do manual), com o conteúdo elétrico da eletrônica. É uma exceção à divisão de pastas: o `programacao-som` não participa desta versão.
  - **Figuras 3D**: adaptar o pipeline `etutti/hardware/manual3d/` (Blender) ao Pocket, numa pasta própria (`etutti/hardware/pocket/manual3d/`), sem mudar o do eTuttino. Uma figura por passo, mais o Pocket montado em corte mostrando a pilha, a bateria, o alto-falante e as plaquinhas.
  - **Rota única**: placa principal montada pela JLCPCB (os TMAG5253 em X2SON não se soldam em casa). O que se solda em casa fica explícito.
  - Ordem sugerida:
    1. **Antes de começar**: o que comprar (BOM do kit, F2), o que imprimir (casca de cima em resina, o resto em MJF, as capas) e as ferramentas.
    2. **Capas de teste**: imprimir 4 capas e conferir nos switches antes das 28.
    3. **Teensy**: cortar a ponte VUSB–VIN e soldar a pilha baixa na Audio Board. Medir a altura.
    4. **Placa principal**: conferir a placa montada, soldar a pilha, testar o 3,3 V com multímetro antes de ligar a bateria.
    5. **Plate e switches**: encaixar o plate e os 28 Gateron.
    6. **Plaquinhas**: knobs (encoder e LED), volume (potenciômetro com chave), painel (USB-C e fone), com os cabos soldados.
    7. **Bateria e alto-falante**: alto-falante na caixa vedada, bateria no berço com o rabicho.
    8. **Fechar o case**: placa nos pilares, parafusos, plaquinhas nos postes, fundo e tampinha da bateria.
    9. **Primeiros testes sem firmware do Pocket**: carga (luz vermelha com o aparelho desligado), liga/desliga pelo volume, 3,3 V presente. A gravação da firmware e a calibração entram quando a firmware existir; deixar a seção marcada como "em breve".
  - Avisos de segurança da bateria LiPo (não furar, não dobrar, não carregar sem o NTC ligado, conferir a polaridade do JST antes de ligar).
  - A página `/etutti/pocket/` provisória ganha um link para o manual.
  - Conferir as páginas no navegador: sem erros no console, sem rolagem lateral em 375 px, todas as figuras carregando.

## 11. Perguntas para o J

Nenhuma em aberto. As próximas virão do fechamento físico e do manual.
