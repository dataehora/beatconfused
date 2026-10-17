# eTuttino Pocket · eletrônica (relatório)

Relatório do agente `eletronica`. Cada tarefa tem uma seção; o fim do arquivo traz as perguntas
para a gestão. Medidas em mm. **(conferir)** = número de datasheet de distribuidor, estimativa,
ou peça ainda sem medida conferida.

## E1 · Energia e som (SPEC v2, 17 out 2026)

**SPEC atendida:** v2, tarefa E1 ("Passo 1 · Eletrônica"). Sem placa nem Gerbers (esperam D2).

### Resumo

- **Autonomia com 1000 mAh, tocando sem parar** (recomendado: sensor TMAG5253, sensores ligados
  por grupo, Teensy a 396 MHz):

  | | típico | pior caso |
  |---|---:|---:|
  | com fone | **6,9 h** (hoje 3,0 h) | **4,2 h** (hoje 1,9 h) |
  | com alto-falante (0,2 W médios; pior 0,5 W) | **4,5 h** (hoje 2,5 h) | **2,4 h** (hoje 1,4 h) |

  Com o Teensy a 240 MHz (se a programação confirmar a CPU): 7,9 h com fone, 5,0 h com
  alto-falante (típicos).
- **A maior economia é o sensor:** o TMAG5253 (TI, 2023) gasta 2,4–2,6 mA contra 6 mA do DRV5056,
  tem pino EN (desliga em 8 nA, saída em alta impedância) e liga em ≤ 45 µs (BA3) contra até
  300 µs. Os 28 sensores passam de 168 mA para 36 mA médios.
- **Medido no Teensy do J:** a CPU do áudio e o tempo de leitura das teclas em 8 frequências de
  clock (tabela no `POWER.md`). O motor de palhetas de hoje usa só 8,5 % da CPU a 600 MHz e 34 %
  a 150 MHz. A corrente não foi medida (não há medidor no PC do J): a do Teensy por clock é um modelo.
- **Orçamento movido** para `pcb/power_budget.py` (stdlib), que escreve o `POWER.md`.
- **`pcb/PINOS.md` provisório:** os 24 pinos da borda do Teensy ficam todos ocupados; muda
  o LED vermelho (4 → 13), o encoder A (17 → 11) e o COM 3 sai.

### Arquitetura de energia

```
 USB micro-B do Teensy ── VUSB (pad de baixo do Teensy; corte VUSB–VIN feito) ── fio ──┐
                                                                                         │
                                         ┌──────────── BQ24074 (carregador, power-path) ◄┘
              LiPo 1S 1000 mAh + PCM ◄── BAT          OUT = 4,4 V com USB / = bateria sem USB
              (JST PH 2,0)                              │
                     divisor 1M/1M ─ pino 16            ├── PAM8302A VDD (SD = pino 12, 100k p/ GND) ── alto-falante
                                                        │
                                                        └── chave do volume (SPST) ── SW_ON ──┐
                                                                                               │
                                     KEEP (pino 10) ── circuito de partida/retenção ── EN ─────┘
                                                                                               │
                                                     TPS63802 (buck-boost) ◄── OUT do BQ24074 ─┘
                                                        │ 3,3 V
                                                        ├── pino 3.3V do Teensy (e VIN ligado ao 3,3 V)
                                                        │      └── Audio Board (pelos headers)
                                                        └── 28 sensores, 2 multiplexadores, LED
```

- **Teensy alimentado pelo 3,3 V.** Corta-se a ponte VUSB–VIN no verso do Teensy (o corte que a
  PJRC documenta) e o 3,3 V do conversor entra pelo pino 3.3V; o pino VIN vai ao mesmo 3,3 V
  (o regulador do Teensy fica com entrada = saída e não puxa corrente reversa, conferir). O 5 V
  da USB chega ao carregador por **um fio curto** do pad VUSB (verso do Teensy) até a placa
  principal, soldado antes de montar o Teensy na Audio Board. É a única modificação no Teensy.
- **Carregador BQ24074:** modo USB500 (EN2 = 0, EN1 = 1, fixo por resistor): no máximo 500 mA
  da porta USB, seguro em qualquer computador. Corrente de carga 500 mA (R_ISET = 1,78 kΩ;
  K_ISET = 890 AΩ). Tocando enquanto carrega, o power-path dá prioridade ao aparelho e carrega
  com o resto. Carga completa ~2,5 h desligado (conferir). TS com 10 kΩ fixo se a bateria não
  tiver NTC.
- **Conversor TPS63802** em vez do TPS63020 da v1: mesmo papel, menor (2 × 3 mm contra 3 × 4),
  11 µA de repouso, 2 A, aceita 1,3–5,5 V na entrada (cobre 4,4 V da USB e a bateria até o fim).
  O TPS63020 continua como segunda opção (mesmo esquema, outro layout).
- **Liga/desliga (SPEC §6):** a chave do potenciômetro liga a saída do carregador ao nó SW_ON.
  - Ao fechar a chave, um pulso RC (1 µF / 1 MΩ, ~0,5 s, conferir) liga o EN do conversor; o
    Teensy acorda e sobe o **KEEP** (pino 10) em poucos ms, que mantém o EN ligado por um
    transistor alimentado pelo próprio SW_ON. Um diodo impede que o Teensy desligado anule o pulso.
  - Chave aberta: SW_ON = 0, o EN cai, tudo desliga, mesmo com o KEEP alto.
  - O amplificador desliga junto: o SD dele tem 100 kΩ para o GND e o Teensy sem energia não o liga.
  - O carregador continua carregando com a chave aberta (ele fica antes da chave).
  - **Desligamento automático de verdade:** a firmware baixa o KEEP e o aparelho desliga
    (~10 µA). Para religar, o usuário gira o volume até o clique e volta. Sem o KEEP, o
    "desligamento automático" só pode baixar o consumo para ~23 mA, e um Pocket esquecido ligado
    esvazia a bateria em ~1,5 dia. Pergunta 2 para a gestão.
- **Medida da bateria:** divisor 1 MΩ / 1 MΩ com 100 nF, direto na bateria (2 µA sempre), pino 16.
- **Desligado:** ~10 µA (carregador sem entrada, conversor desligado, divisor, amplificador em
  shutdown): a bateria dura anos; fica a autodescarga dela.

### Peças escolhidas

| Função | Peça | LCSC | Medidas | Datasheet | Notas |
|---|---|---|---|---|---|
| Bateria | LiPo 1S 1000 mAh tipo 603450, com PCM, 2 fios + JST PH 2,0 | — (comprar pronta) | célula 6,3 × 34,5 × 52 máx. (EEMB LP603450); **com PCM e dobra dos fios, reservar 7 × 36 × 58** + ~60 mm de fio (conferir) | [EEMB LP603450](https://www.eemb.com/product-252) | "603450" é só tamanho: cada fabricante tem 1000–1200 mAh e PCM de 2–4 mm. A polaridade do JST varia entre vendedores: conferir antes de ligar. Prever ~8 % de inchaço no berço. |
| Carregador com power-path | TI **BQ24074RGTR**, QFN-16 3 × 3 | [C54313](https://www.lcsc.com/product-detail/C54313.html) | 3 × 3 × 1 | [bq24074](https://www.ti.com/lit/ds/symlink/bq24074.pdf) | OUT 4,4 V com USB; OVP 10,5 V. |
| Buck-boost 3,3 V | TI **TPS63802DLAR**, VSON-10 2 × 3 | [C2845237](https://lcsc.com/product-detail/C2845237.html) | 2 × 3 × 1 + indutor 0,47 µH (~4 × 4) | [tps63802](https://www.ti.com/lit/ds/symlink/tps63802.pdf) | 2ª opção TPS63020DSJR [C15483](https://www.lcsc.com/product-detail/C15483.html), [datasheet](https://www.ti.com/lit/ds/symlink/tps63020.pdf). |
| Amplificador classe D mono | Diodes **PAM8302AASCR**, MSOP-8 | [C113367](https://lcsc.com/product-detail/C113367.html) | 3 × 3 × 1 | [PAM8302A](https://www.diodes.com/assets/Datasheets/PAM8302A.pdf) | 2,0–5,5 V, na bateria; 0,65 W em 8 Ω a 3,6 V (1 % THD); repouso 4 mA, shutdown < 1 µA; ganho máx. 23,5 dB, reduzido com R de entrada (~33 kΩ → ~11 dB, conferir de ouvido). |
| Sensor Hall (28×) | TI **TMAG5253BA3** (padrão) ou **TMAG5253UA5**, X2SON-4 | não achado na LCSC/JLCPCB (conferir); TI/DigiKey/Mouser, consignado à JLCPCB | 1,4 × 1,1 × 0,4 | [tmag5253](https://www.ti.com/lit/ds/symlink/tmag5253.pdf) | Mesmo lado (verso) e mesma orientação do DRV5056: lê o sul na face marcada, que é o que o ímã norte-para-baixo do Gateron dá através da placa. Ver "Reduções". |
| Sensor, alternativa SOT-23 | TI DRV5053OAQDBZR(Q1) | [C165150](https://www.lcsc.com/product-image/C165150.html) (sem estoque) / Q1 C2654961 | SOT-23 | [drv5053](https://www.ti.com/lit/ds/symlink/drv5053.pdf) | 2,7 mA, liga em 35 µs, sem EN, saída 0,2–1,8 V invertida (o sul baixa a tensão), satura em 73 mT. Só se o TMAG5253 não puder ser comprado. |
| Multiplexador (2×) | CD74HC4067M96, SOIC-24 | (como no eTuttino) | — | [CD74HC4067](https://www.ti.com/lit/ds/symlink/cd74hc4067.pdf) | Igual ao eTuttino. |
| Porta para o EN dos grupos | SN74LVC2G08 + SN74LVC1G04 (ou equivalente) | escolher na placa (D2) | SOT-23/SC-70 | — | EN_A = SENS_EN · /S3, EN_B = SENS_EN · S3. |
| Potenciômetro de volume com chave | 9 mm, 10 kΩ log (A), chave SPST que fecha no início do curso, tipo **RK0972S / RV097NS** | não achado na LCSC (conferir) | ver abaixo | [desenho RK0972S](https://kyohritsu.com/eclib/OTHER/DATASHEET/rk0972s.pdf) | A chave abre nos primeiros ~30° (sentido anti-horário, até o clique). |
| Jack de fone | jack estéreo 3,5 de painel **com contato de comutação na ponta** (5 terminais), ≤ 10 de profundidade | — (conferir modelo) | como o do eTuttino + 1 terminal | — | 4 fios: L, R, terra virtual (manga) e o contato da ponta. |

#### Alto-falante (o maior que couber; 8 Ω)

| Candidato | Contorno | Profundidade | Potência | Sensibilidade | Ressonância | Volume traseiro recomendado | Datasheet |
|---|---|---:|---|---|---:|---:|---|
| **Same Sky CLS0361-L152** (recomendado) | Ø36 redondo | 6,0 | 2 W (3 W máx.) | 88 dB a 1 W / 0,5 m | 450 Hz | **8–12 cm³** fechado (conferir) | [CLS0361-L152](https://www.sameskydevices.com/product/resource/cls0361-l152.pdf) |
| PUI Audio AS03608MR-LW100-R | Ø36 redondo | 4,6 | 1 W (1,5 W máx.) | 91 dB (condição não informada, conferir) | 500 Hz | 6–10 cm³ (conferir) | [AS03608MR-LW100-R](https://api.puiaudio.com/filename/AS03608MR-LW100-R.pdf) |
| Same Sky CMS-30204-18L250 | 30 × 20 retangular | 4,0 | 1 W (1,2 W máx.) | 94 dB a 1 W / 0,1 m (≈ 80 dB a 1 m) | 700 Hz | 3–5 cm³ (conferir) | [CMS-30204-18L250](https://www.sameskydevices.com/product/audio/speakers/miniature-(10-mm~40-mm)/cms-30204-18l250) |
| Same Sky CLS0281-L152 (se só couber 28) | Ø28 redondo | 5,8 | 1 W | 82 dB | 440–660 Hz | 3–5 cm³ (conferir) | [TME CLS0281-L152](https://www.tme.com/ca/en/details/cls0281-l152/speakers/same-sky-r/) |

- Volume traseiro **fechado e vedado** (junta de espuma ou cola em volta do aro), atrás do cone,
  sem comunicar com o resto do case. Um volume menor que o recomendado sobe a ressonância e corta
  mais grave; maior não faz mal. Com Ø36 e 10 cm³, o grave útil começa em ~550–650 Hz
  (estimativa): o Pocket vai de G3 (196 Hz) a E5 (659 Hz), então o alto-falante reproduz os
  harmônicos e o ouvido completa a fundamental. Por isso a equalização da programação corta
  abaixo de ~400 Hz e limita o pico (SPEC §5).
- Frente: a grade precisa de área aberta ≥ ~30 % da área do cone, a ≤ 1–2 mm da membrana, com
  uma junta entre o aro e a parede.
- Não há códigos LCSC úteis para alto-falantes desses fabricantes: compra direta
  (Mouser/DigiKey/TME); vai ligado por fio, fora da montagem da JLCPCB.
- Alternativa sem volume traseiro: alto-falante "com caixa" 20 × 30 × 6,8 (tipo 2030 cavity,
  2 W): encaixa mais fácil, soa como um celular. Só se não couber o Ø36 com volume.

#### Potenciômetro com chave: medidas para o design

Do desenho RK0972S (9 mm, com chave; o RV097NS é o mesmo formato, conferir no modelo comprado):

- corpo 9,5 de largura × 15,8 de comprimento (ao longo do eixo, **incluindo a chave**) × ~10 de altura;
- rosca M7 × 0,75, eixo Ø6 serrilhado, comprimento L = 15 ou 20 a partir do corpo;
- 8 terminais Ø1 (3 do potenciômetro, 2 da chave, apoios), passo 5 / 2,5.
- **Montado com o eixo para cima** (versão vertical, terminais na face de trás): **15,8 + 0,8 de
  corpo acima da placa, mais o eixo: 31–36 do topo da placa à ponta do eixo** (L = 15 ou 20,
  conferir). É ~10 mais alto que o RK09K do eTuttino.
- O desenho mostrado é da versão horizontal (eixo paralelo à placa, eixo a 6,5 da placa). Se a
  vertical não existir no fornecedor, a horizontal serve montada numa plaquinha perpendicular à
  tampa. Quem decide é o design (altura disponível sob a tampa).

#### Detecção do fone

O jack tem um contato que encosta na ponta (canal esquerdo) quando não há plugue e se afasta
quando o plugue entra. Esse contato vai ao pino 17 (ADC) por 100 kΩ, com 1 MΩ e 100 nF para o GND.

- Sem fone: o pino vê a tensão de repouso da saída de fone do SGTL5000 (~1,6 V, que é também a
  do terra virtual), filtrada do áudio: ~1,4 V.
- Com fone: o contato abre e o pino vai a 0 V.
- O contato nunca toca o GND nem o terra virtual: a manga do jack continua só no **HP_VGND** da
  Audio Board. A carga extra na saída esquerda é de 1,1 MΩ (desprezível).
- Codec desligado ou na partida: 0 V = "fone", o amplificador fica desligado (lado seguro).
- O amplificador pega o som das mesmas saídas de fone (L + R somados por resistores, contra o
  HP_VGND, entradas diferenciais com 1 µF): o potenciômetro de volume vale para fone e
  alto-falante, e a programação aplica a equalização do alto-falante quando HP_DET diz "sem fone".

### Reduções de consumo (SPEC §6)

1. **Sensor de menor consumo: TMAG5253.** Analógico ratiométrico, 15 kHz de banda (DRV5056: 20 kHz;
   a batida mais rápida dura ~1 ms, então sobra), EN com saída em alta impedância, sente o sul na
   face marcada como o DRV5056 (vai no verso, mesma orientação).
   - **BA3** (bipolar, ±80 mT, 15 mV/mT, repouso 1,65 V, 2,6 mA típ./5 mA máx., liga em 20/45 µs):
     a mesma faixa do DRV5056A3, padrão seguro.
   - **UA5** (unipolar, 0–52 mT, 48 mV/mT, repouso 0,2 V, 2,4/4 mA, liga em 55/130 µs): o triplo
     de resolução, se o campo no fim do curso ficar abaixo de ~50 mT.
   - Mesma pegada X2SON: a escolha entre os dois fica para a medição do campo no protótipo.
   - Ponto fraco: não achei na LCSC/JLCPCB; compra na TI/DigiKey e consigna, ou "global sourcing"
     da JLCPCB (conferir prazo e custo). X2SON 1,4 × 1,1 é só montagem de fábrica (rota A do manual).
2. **Sensores ligados por grupo.** O bit S3 do endereço (que já existe) escolhe o grupo de canais
   0–7 ou 8–15 dos dois multiplexadores; uma porta lógica liga o EN só do grupo que está sendo lido.
   Metade dos sensores desligada o tempo todo: 73 → 36 mA. Com o BA3 a leitura cai de 4,6 kHz
   para ~3 kHz (medido + calculado); o erro de velocidade fica em ±2 de 127 na batida mais rápida.
   **Com o DRV5056 não vale:** o tON de até 300 µs derruba a leitura para ~1,2 kHz (tabela no
   `POWER.md`). O SENS_EN geral (pino 4) também desliga todos no repouso e no desligamento leve.
3. **Teensy em clock menor (medido a CPU, estimada a corrente).** O motor atual usa 8,5 % a
   600 MHz, 12,9 % a 396 MHz, 21 % a 240 MHz. Proposta: começar em 396 MHz (~31 mA a menos,
   estimativa) e a programação mede com o motor do Pocket (Musette com 3 palhetas de 8', presets)
   se 240 MHz fica abaixo de ~40 %. A leitura das teclas a 240 MHz leva 266 µs (medido), sem efeito
   na velocidade. Coordenar com a programação (P1).
4. **Amplificador desligado em silêncio:** o SD (pino 12) desliga o PAM8302A com fone plugado,
   ~2 s depois da última voz, e no desligamento automático: −4 mA (até −8) de repouso. Pouco
   tocando; importa parado.

### Consumo e autonomia

Detalhes e todos os cenários no `POWER.md`. Bateria 1000 mAh, 85 % úteis (3,15 Wh).

| Cenário | fone típ. | fone pior | alto-falante típ. | alto-falante pior |
|---|---:|---:|---:|---:|
| antes (v1): DRV5056, 600 MHz | 3,0 h | 1,9 h | 2,5 h | 1,4 h |
| TMAG5253BA3 sempre ligado, 600 MHz | 4,5 h | 2,7 h | 3,4 h | 1,9 h |
| TMAG5253BA3 por grupo, 600 MHz | 5,5 h | 3,5 h | 3,9 h | 2,2 h |
| **TMAG5253BA3 por grupo, 396 MHz (recomendado)** | **6,9 h** | **4,2 h** | **4,5 h** | **2,4 h** |
| TMAG5253BA3 por grupo, 240 MHz | 7,9 h | 4,6 h | 5,0 h | 2,6 h |

- Trilho de 3,3 V no recomendado: ~128 mA típicos com fone (Teensy ~69, sensores 36, Audio
  Board 20). Antes: ~290 mA.
- Alto-falante: 0,2 W médios típicos, 0,5 W no pior caso (estimativa, conferir de ouvido).
- Ligado sem tocar: ~93 mA (~9 h). Desligamento leve: ~23 mA (~1,5 dia). Com KEEP ou chave: ~10 µA.
- Medido em hardware: só CPU e tempo de leitura. Correntes: datasheets e modelo (conferir no protótipo).

### Para o design conferir o encaixe

- Bateria: reservar **7 × 36 × 58** + saída de ~60 mm de fio com JST PH 2,0; acesso pelo fundo.
- Alto-falante Ø36 × 6,0 (CLS0361-L152) com **8–12 cm³** de volume traseiro fechado; ou Ø36 × 4,6
  (AS03608MR) com 6–10 cm³; ou 30 × 20 × 4,0 com 3–5 cm³.
- Potenciômetro com chave: corpo ~9,5 × 10 em planta (versão vertical), **31–36 de altura do
  topo da placa à ponta do eixo**; rosca M7.
- Novo na placa principal (D2): BQ24074, TPS63802 + indutor ~4 × 4, PAM8302A, portas do EN,
  JST PH 2 vias da bateria, 2 vias do alto-falante, 4 fios do jack, 1 fio do VUSB.

### O que a programação precisa ajustar (`pcb/PINOS.md`, provisório)

1. `MUX_COUNT = 2`, COMs em 14 e 15. O pino 16 vira **VBAT** (A2, bateria/2).
2. LED vermelho **4 → 13** (verde continua no 5). O pino 4 vira **SENS_EN**.
3. Encoder A **17 → 11** (B no 9, clique no 6, iguais). O pino 17 vira **HP_DET** (A3).
4. Novos: **KEEP** = 10 (subir na partida, em `startup_early_hook`), **AMP_SD** = 12.
5. Leitura por grupos (S3) com espera de 45 µs (BA3) depois de trocar de grupo.
6. `SENSOR_ZERO` / `PRESENT_MIN` do TMAG5253 (BA3: repouso 1,65 V).
7. `set_arm_clock(396000000)`; medir a CPU do Pocket e, se der, 240 MHz.
8. "Carregando" deduzido de VBUS + VBAT (sem pino do carregador); cortar em VBAT < 3,3 V.

## Perguntas para a gestão

1. **Sensor TMAG5253 no lugar do DRV5056?** Dá o maior ganho (168 → 36 mA, a autonomia com fone
   passa de 3,0 h para 6,9 h), mas não achei estoque na LCSC/JLCPCB: a montagem na JLCPCB fica
   com peça consignada ou "global sourcing" (mais prazo e custo), e o X2SON não se solda em casa.
   Alternativa em SOT-23 com estoque parcial: DRV5053 (2,7 mA, sem EN: ~5,3 h com fone a
   396 MHz, típico, estimativa).
2. **Desligamento automático de verdade (KEEP)?** Com o KEEP, depois de N minutos o Pocket
   desliga de verdade e religa girando o volume até o clique e de volta. Sem ele, o desligamento
   automático só baixa para ~23 mA e um Pocket esquecido ligado esvazia em ~1,5 dia. Recomendo
   o KEEP; a firmware pode ter os dois (leve depois de 15 min, de verdade depois de mais 30).
3. **Um fio no Teensy:** o carregador recebe o 5 V da USB por um fio do pad VUSB (verso do
   Teensy), depois de cortar a ponte VUSB–VIN. É aceitável para o kit/manual, ou prefere um
   conector USB próprio na placa (só carga) além do micro-USB do Teensy?
4. **LED de carga?** Não sobrou pino para o status do carregador; a página mostra "carregando"
   deduzindo pela tensão. Com o aparelho desligado e carregando, nada acende. Quer um LED
   pequeno de carga ligado direto no carregador (sem pino do Teensy, visível com o Pocket
   desligado)?
5. **Potenciômetro com chave:** os 9 mm com chave (tipo RK0972S/RV097NS) são ~10 mm mais altos
   que o RK09K e não achei um com estoque na LCSC. Aceita essa altura (31–36 da placa à ponta do
   eixo), ou o design prefere outro formato (16 mm com chave, mais baixo e mais largo)?
6. **Alto-falante:** recomendo o Ø36 × 6 (CLS0361-L152, 2 W) com 8–12 cm³ fechados. Se o D1 não
   der esse volume sob a grade, prefere o Ø36 fino (4,6) com menos grave, ou o 30 × 20?
7. **Bateria com NTC?** Pacotes de 3 fios (com termistor) deixam o carregador parar a carga se a
   bateria esquentar. São menos comuns no tamanho 603450. Exigir, ou aceitar 2 fios com o TS fixo?
