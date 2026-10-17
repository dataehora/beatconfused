# eTuttino Pocket · especificação · v2

**Versão 2 — 17 out 2026.** Substitui a v1 (PR #101, no histórico do git). Mantida pela gestão (Claude Chat com o J); o Code não edita este arquivo. Cada disciplina responde no seu relatório (`FIT_CHECK.md`, `ELETRONICA.md`, `FIRMWARE_SOM.md`), terminando com "Perguntas para a gestão". Protocolo completo no `CLAUDE.md`, seção "eTuttino Pocket — como trabalhamos".

Medidas em mm. **(conferir)** = estimativa a confirmar com a peça real ou o datasheet.

## Mudanças desde a versão anterior (v1)

1. **Só plástico.** O Pocket é só **Seixo** (plástico, resina ou MJF, uma cor). A versão Madeira sai.
2. **Alto-falante e bateria vêm no kit.** O Pocket tem alto-falante de qualidade razoável sob a grade (a grade deixa de ser só ventilação). Responde à pergunta 1 do `FIRMWARE_SOM.md`: o texto "bateria e alto-falante" da página inicial está certo.
3. **Bateria de 1000 mAh, confirmada pelo J** (era ~2000). A autonomia é a que ela der depois das reduções de consumo da §6; não há mais meta fixa de 4 h.
4. **Lado esquerdo redesenhado** (pedido do J em 15 out):
   - os cantos retos da esquerda dão lugar a uma forma moderna e elegante, alinhada ao "<" do teclado;
   - de trás para a frente, a área de interface tem o logo gravado, os knobs com o LED e a grade do alto-falante.

   O rascunho `rascunhos/layout_v2.py` é o ponto de partida. Ali não coube um alto-falante de 36 mm no canto da frente-esquerda.
5. **Seletor = presets.** O knob da direita escolhe entre até 8 presets de som. Os 6 de fábrica são registros de acordeom: Bassoon, Bandoneon, Organ, Violin, Musette, Piccolo (§8).
6. **Só acordeom.** Piano e violão ficam fora do Pocket. Um preset de piano pode vir depois, fora do núcleo do Pocket. A firmware do Pocket não leva as amostras de piano e violão.
7. **Só português** nas páginas do Pocket e da família enquanto durarem o design e o protótipo. As outras línguas e os textos para o usuário final vêm na versão final (§10).
8. **Respostas do J às perguntas da v2:** segurar o clique e girar muda a **oitava**; o liga/desliga fica **no knob de volume** (girar além do clique, como rádio).
9. **Ordem do trabalho:** a programação e o som ficam para um **segundo passo**, depois do design (D1) e da eletrônica (E1).
10. Respostas às outras perguntas do `FIRMWARE_SOM.md` (PR #102):
   - 2: "voltar" dos manuais para `/etutti/etuttino/` está bom;
   - 3: o título de `/etutti/etuttino/` fica como está e muda quando essa página virar a base da página do Pocket;
   - 4: o contorno dos desenhos passa a vir do case do Pocket, nas mesmas chaves `box`/`opening` do `pocket.json`.

## 1. Resumo

| | Pocket v2 |
|---|---|
| Case | só plástico, Seixo |
| Botões | 28 · G3–E5 |
| Nota mais alta por fileira (4, 3, 2, 1) | C5 · D5 · E5 · D♯5 |
| Passo, switches, sensores | grade hexagonal de 18,5, Gateron magnético, sensor Hall por tecla |
| Interface | logo gravado, 2 knobs, LED, grade do alto-falante |
| Som | só acordeom (6 registros de fábrica + 2 presets livres); alto-falante interno + saída de fone 3,5 (o fone desliga o alto-falante) |
| Energia | LiPo 1S **1000 mAh**, carrega pelo USB, toca enquanto carrega; liga/desliga no knob de volume |
| Conexões | USB Micro-B e fone do lado esquerdo |

## 2. Teclado

Igual à v1 §2: 28 botões, regra C-griff, fileira 1 mais perto de quem toca, Dós e Fás com xadrez diagonal, botões convexos (domo baixo com saia). A origem `O` pode mudar com o lado esquerdo novo. Quem define é o design, no `pocket.json`.

## 3. Case (Seixo)

- Largura (profundidade) de 100, constante. Paredes externas verticais. Área do teclado aberta, com o mesmo chanfro e a mesma folga lateral de 1 botão do eTuttino.
- **Lado direito**: segue o ">" do teclado, como na v1.
- **Lado esquerdo, novo**: segue o "<" do teclado, a distância constante, com raios generosos nas três quinas: a ponta do "<" e as duas quinas onde a face esquerda encontra a de trás e a da frente.
  - Nada de canto reto.
  - O J pediu uma forma "moderna e elegante". O design propõe 2 ou 3 variantes em planta (por exemplo, "<" com ponta bem arredondada, curva contínua tipo seixo, "<" com faces levemente curvas) e recomenda uma.
- Transição do teclado para a interface: rampa arredondada, sem quinas vivas onde a mão encosta (como no eTuttino).
- Fundo parafusado, com acesso à bateria sem abrir a tampa.
- Detalhar o Seixo para fabricação: espessuras de parede, bosses, pilares de apoio da placa, encaixe do alto-falante, berço da bateria, folgas de impressão (resina e MJF), e peso estimado.

## 4. Área de interface (de trás para a frente)

| Zona | O que tem |
|---|---|
| Trás | **logo gravado** (eTuttino Pocket), em baixo-relevo de ~0,4 (conferir), numa área que acompanha a forma do lado esquerdo |
| Meio | **knob esquerdo = volume**, **knob direito = seletor** (encoder com clique), **LED** à direita dos knobs |
| Frente | **grade do alto-falante**, no plano a 13° voltado para quem toca, com a forma acompanhando o lado esquerdo |

Folga mínima de 5 entre knobs/LED e as bordas da área, e de 6 entre a grade e a rampa. O knob esquerdo é um **potenciômetro com chave** (liga/desliga ao girar além do clique, como rádio): o design reserva a altura dele (maior que a do RK09K do eTuttino, conferir).

## 5. Som

- **Alto-falante de qualidade razoável**: o maior que couber sob a grade, com volume traseiro fechado. A eletrônica escolhe o modelo; o design faz o encaixe. Faixa sugerida: Ø 28–36 redondo, ou retangular tipo 20 × 30 (conferir).
- **Amplificador classe D** mono, ligado à bateria, desligado quando o fone está plugado e no desligamento automático.
- Fone 3,5 pela Audio Board, como no eTuttino (terra virtual, nunca GND).
- A programação ajusta uma equalização para o alto-falante (corte de graves que ele não reproduz, limitador) separada da do fone.

## 6. Energia

- **LiPo 1S de 1000 mAh** (formato tipo 603450, ~6 × 34 × 50, conferir), com proteção própria (PCM).
- Carregador com power-path (toca enquanto carrega), buck-boost de 3,3 V, divisor para medir a bateria. A arquitetura da v1 §5 continua como referência; a eletrônica pode mudar.
- **Liga/desliga** pela chave do potenciômetro de volume: a chave corta o EN do conversor de 3,3 V e do amplificador; o carregador continua carregando com o aparelho desligado.
- **Autonomia com o orçamento de hoje** (`POWER.md`, gerado pela v1):

  | | típico | pior caso |
  |---|---|---|
  | com fone | ~2,9 h | ~1,9 h |
  | com alto-falante (~0,4 W médios) | ~2,0 h | ~1,5 h |

  A bateria fica em 1000 mAh. Os 28 sensores Hall gastam ~168 mA dos ~292 mA. Referência: 4 h com fone exigiriam ≤ 214 mA no trilho de 3,3 V.
- A eletrônica estuda e mede as reduções abaixo e informa a autonomia resultante, sem comprometer a resposta das teclas:
  1. sensor Hall de menor consumo;
  2. alimentar os sensores só durante a leitura do seu multiplexador (o DRV5056 leva 150–300 µs para ligar: conferir o efeito na velocidade);
  3. Teensy em clock menor (coordenar com a programação: CPU do áudio);
  4. desligar o amplificador do alto-falante em silêncio.

## 7. Knobs

- **Esquerdo**: volume contínuo, com chave liga/desliga no início do curso.
- **Direito**: encoder com clique.
  - Girar troca o preset (1 → 8, só os presets ocupados).
  - Clique depois de girar grava o preset atual como o de ligar.
  - Segurar o clique e girar muda a oitava (−2 … +2), confirmado pelo J. A transposição de ±12 semitons fica só na página.
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

  O motor de palhetas do eTuttino tem hoje 4 palhetas (16' cassotto, 8' M1, 8' M2, 4'). O Musette precisa de uma 3ª palheta de 8'. A programação verifica vozes e CPU.
- **Parâmetros editáveis na página**, por preset: combinação de palhetas, desafinação (cents), ataque, decay, sustain, release, filtro de tom, reverb, nível. Pode incluir outros parâmetros usuais de sintetizador que caibam no motor, desde que não afetem as notas.
- **Memória**: cada preset ocupa poucos bytes. A programação mede quantos cabem na EEPROM emulada do Teensy 4.0 (e na flash, se precisar) sem comprometer o resto, e informa se dá para passar de 8. O seletor continua percorrendo no máximo 8. Presets extras ficariam só na página, para carregar nos 8 lugares.
- Os presets e as configurações vão por SysEx; volume e preset continuam também por CC, como no eTuttino.
- **Só acordeom**: os presets usam só o motor de palhetas (com envelope, filtro e reverb). As amostras de piano e violão do eTuttino não entram no Pocket. Um preset de piano poderá ser adicionado depois, fora do núcleo do Pocket.

## 9. Programado pelo beatconfused.com

- Oitava (−2 … +2) e transposição (±12).
- Presets (§8), incluindo voltar aos 6 originais.
- Conversão C-griff ↔ B-griff (já existe, CC 24).
- Calibração das teclas: considerar uma página de calibração guiada (apertar cada tecla até o fundo). Hoje a calibração é automática ao ligar (repouso) mais a aprendida (fundo). A programação propõe; a gestão decide.
- Desligamento automático: silencia e baixa o consumo depois de N minutos sem tocar (padrão 15). N é configurável.
- Bateria: nível e "carregando" na página.

## 10. Línguas e publicação

- Até a versão final, as páginas do Pocket e a página inicial da família são publicadas **só em português**.
- As outras línguas (en/es), os manuais e os textos para o usuário final só vêm na versão final.
- As páginas pausadas (`/etutti/etuttino/`, `manuais/`, `models/`) ficam como estão.
- Publicar só o necessário para acompanhar o design e o protótipo.

## Tarefas para o Code (v2)

O trabalho vai em **dois passos**. Cada passo tem o seu prompt, o seu PR e o seu merge.

- **Passo 1, design e eletrônica:** D1 primeiro (forma e contratos). E1 pode começar em paralelo e usa o espaço de D1 quando sair.
- **Passo 2, programação e som:** P1 e P2, só depois do merge do passo 1. Lê o `PINOS.md` provisório e o `POWER.md` de E1.
- **Depois da escolha do J entre as variantes de D1:** D2 (modelo do Seixo) e, em seguida, a placa.

### Passo 1 · Design

- **D1. Lado esquerdo e interface.**
  - Partir de `rascunhos/layout_v2.py` e propor 2–3 variantes do lado esquerdo (§3) com a interface da §4; recomendar uma.
  - Para cada variante: planta em escala com o eTuttino atrás, comprimento total, maior alto-falante que cabe sob a grade (com volume traseiro), e onde ficam a bateria de 1000 mAh, a pilha Teensy + Audio Board e o potenciômetro com chave.
  - Preferir a bateria fora de baixo da placa, para o teclado manter a altura do eTuttino. Se não der, dizer quanto o teclado sobe.
  - Publicar as plantas numa página de revisão em português (`/etutti/pocket/revisao/`, noindex) para o J escolher.
  - Atualizar `pocket.json` com a variante recomendada (marcada como provisória) e o `FIT_CHECK.md`.

### Passo 1 · Eletrônica

- **E1. Energia e som.**
  - Escolher bateria de 1000 mAh, carregador, buck-boost, amplificador classe D, alto-falante, detecção do fone e potenciômetro de volume com chave, com códigos LCSC.
  - Estudar e, se possível, medir as reduções de consumo da §6, e dizer quantas horas o Pocket faz com fone e com alto-falante.
  - Mover o orçamento de energia para um script seu e atualizar o `POWER.md`.
  - Rascunho do `pcb/PINOS.md` (2 multiplexadores, bateria, amplificador, detecção do fone, knobs, LED) e `ELETRONICA.md`.
  - Placa e Gerbers só depois de D2.

### Passo 2 · Programação e som (depois do merge do passo 1)

- **P1. Presets e registros de acordeom.**
  - No sketch (`ETUTTI_MODEL_POCKET`) e no `websynth.js`: os 6 registros de fábrica da §8, incluindo a 3ª palheta de 8' do Musette, e a estrutura de preset com os parâmetros editáveis.
  - Só acordeom: o modelo Pocket compila sem as amostras de piano e violão; o eTuttino continua compilando como está.
  - Seguir o `PINOS.md` provisório de E1 (bateria, detecção do fone, amplificador, chave).
  - Medir CPU e vozes no Teensy do J, e medir a memória: quantos presets cabem.
  - Propor o formato SysEx e a calibração guiada.
  - Relatório no `FIRMWARE_SOM.md`.
- **P2. Só português.**
  - A página inicial `/etutti/` e a `/etutti/pocket/` (incluindo a de revisão de D1) passam a sair só em português (sem seletor de língua nessas páginas), conforme a §10.
  - Acrescentar a regra ao agente `programacao-som` e ao `CLAUDE.md`.

## 11. Perguntas para o J

Nenhuma em aberto: as quatro perguntas da v2 foram respondidas (Mudanças 3, 6 e 8). As próximas virão dos relatórios do passo 1, sobretudo a escolha da variante do lado esquerdo.
