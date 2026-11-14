# eTutti StudentViaggio · v0.2 (14 nov 2026)

A **StudentViaggio** tem a eletrônica do **Viaggio J1** (`../viaggio_j1/`) e **teclas resistivas** no lugar das 28 teclas de efeito Hall: um pente de cobre por tecla, sob uma folha sensível à pressão (Velostat). A v0.2 é a placa **compacta**: 210 × 95 mm, ponta à direita, teclas no passo 19,05 × 18 mm.

Ela substitui a v0.1 (a J1 inteira, 246,5 × 95 mm) e o rascunho `student/` / `studentBK/` (v20), que não podia ser fabricado. Do rascunho ficaram a forma, o passo e a ideia dos apoios.

**Estado:** esquema e placa prontos e conferidos. **Não há ainda** arquivos de fabricação (Gerbers, BOM/CPL da JLC) nem firmware para as teclas resistivas. Nada foi construído.

![placa, lado de cima](img/placa_cima.png)

## O que mudou em relação à J1

| | Viaggio J1 | StudentViaggio v0.2 |
|---|---|---|
| Tecla | Gateron magnético + TMAG5253 no verso | pente de cobre no lado de cima (`FSR_Comb_D12`) |
| Peças por tecla | chave, sensor, capacitor | nenhuma (cobre da placa) |
| Grade das teclas | a do Pocket (18,5 mm, hexagonal) | 19,05 × 18 mm, fileiras de 7 / 8 / 7 / 6 |
| Contorno | 246,5 × 95 mm, retangular | 210 × 95 mm, ponta à direita |
| Furos M2 | 8 | 11 (H1–H4 onde a J1 os tem; H5–H8 movidos; H9–H11 novos) |
| Alimentação dos sensores | 3 portas lógicas, grupos `EN_A`/`EN_B`, `SENS_EN` | não existe; o pino 4 do Teensy ficou livre |
| Referência da leitura | — | R601 e R602, 10 k ao 3,3 V no comum de cada mux |
| Footprints na placa | 178 | 123 (51 em cima, 72 no verso) |
| Placa de apoio das chaves (plate) | precisa | não precisa |
| Camadas, espessura, regras | 4 camadas, 1,2 mm | iguais |

- **O bloco esquerdo é o da J1, sem mexer** (x ≤ 78 mm): módulo MicroMod, USB-C, carga, conversor de 3,3 V, codec, amplificador, encoders, LED, com o roteamento dela. Os dois mux também ficaram onde estavam, na faixa de cima.
- Os canais dos multiplexadores são os da J1. A tabela está em `pcb/PINOS.md`.

## Como a tecla funciona

![uma tecla](img/tecla.png)

- **Amarelo = GND**, **laranja = sinal** (entrada do mux). Dedos de 0,3 mm, vão de 0,5 mm, cobre exposto.
- O pente da v0.2 é simétrico: o dedo de sinal passa pelo centro e a via de sinal fica num ressalto do arco direito, fora da área que o dedo aperta. O bloco de sinal da v0.1 saiu.
- Uma folha condutiva sensível à pressão fica sobre o pente. Apertar a folha liga os dedos com uma resistência que cai com a força.
- R601/R602 e a tecla formam um divisor: `V = 3,3 V × Rtecla / (Rtecla + 10 k)`. Solta = 3,3 V.
- **Velocidade:** a firmware mede quão depressa a tensão cai nos primeiros milissegundos do toque. A mesma leitura dá **pressão contínua depois da nota** (aftertouch por tecla), que as teclas Hall não davam.
- O pente comum é o GND, não o 3,3 V: o que fica mais perto do dedo é o terra.

## Como a placa é feita

A partir da raiz do repositório, nesta ordem:

```bash
python etutti/hardware/student_viaggio/pcb/layout.py
```

```bash
python etutti/hardware/student_viaggio/pcb/schematic.py
```

```bash
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_viaggio/pcb/build_board.py
```

```bash
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_viaggio/pcb/mechanics.py
```

```bash
python etutti/hardware/student_viaggio/pcb/pinos.py
```

- `layout.py` escreve o contorno, os centros das teclas e os furos em `pcb/layout.json` (e `img/layout.svg`).
- `schematic.py` escreve o esquema (cópia do gerador do Viaggio MicroMod, folha T refeita), roda o ERC e compara a netlist com a da J1.
- `build_board.py` lê a placa da J1 **sem escrever nela**, tira as teclas e tudo o que ficou fora do contorno novo, põe os pentes e os dois resistores, e roteia de novo as 28 teclas com o roteador da J1 (`viaggio_j1/rota_restante.py`). **Leva de 10 a 15 minutos**: rodar em segundo plano.
- `mechanics.py` calcula a flexão (`pcb/flexao.json`, `img/flexao.png`); `pinos.py` escreve o `pcb/PINOS.md`; `tecla_img.py` desenha `img/tecla.png`.

O projeto KiCad é `pcb/kicad/student_viaggio.kicad_pro`.

## Conferência (14 nov 2026)

| Verificação | Resultado |
|---|---|
| ERC do esquema | 0 erros, 0 avisos |
| Netlist × J1, fora do setor das teclas | igual |
| DRC do KiCad com as regras da J1 (`.kicad_dru`) | 0 violações |
| Ligações abertas | 0 |
| Paridade esquema × placa | 0 diferenças |
| Teclas ligadas a exatamente uma entrada de mux | 28 de 28 |
| Trilhas de outras redes sob os pentes, no lado de cima | nenhuma |
| Vias dentro do círculo de 6,5 mm de cada pente | só a via de sinal da tecla, mais uma de `OUT_K11` na borda do K25 (a 6,46 mm do centro, 0,3 mm fora do arco do pente) |

O que o `build_board.py` fez:

- **Saíram:** 88 peças, as 535 trilhas e vias das teclas e dos sensores da J1, 186 fora do contorno novo, 27 sob os furos movidos e 173 vias de GND/+3V3 que caíam dentro dos pentes, mais os tocos que sobraram.
- **Roteadas de novo:** as 28 redes `OUT_Kxx`, `MUX_S0`, os dois comuns dos mux até R601/R602 e 5 ligações de GND/+3V3. Fechou na sexta tentativa, sem falhas.
- **As rotas das teclas:** 1,58 m de trilha no total, 85 vias, quase tudo no verso (1,33 m; 0,21 m em cima; 0,05 m na camada interna de sinal). A mais longa é a do K01, com 89 mm.
- O pente do K08 está girado 180° (a via de sinal não cabia à direita).
- Nenhuma rede de corrente perdeu cobre: o script para se isso acontecer.

### Flexão, áudio e calor

![flexão](img/flexao.png)

- **Flexão** (grelha de vigas de 4 mm, placa nua de 1,2 mm, 3 N numa tecla por vez; não há plate para ajudar):
  - só com os 11 furos M2: pior tecla **0,122 mm** (K28), média 0,048 mm. Acima do alvo de 0,05 mm.
  - com **6 pilares** de 4 mm no case, em (182,5; 29,5), (144,5; 29,5), (154,5; 83,5), (78,5; 47,5), (97,5; 83,5) e (201,5; 65,5): pior tecla **0,039 mm** (K12), média 0,019 mm.
  - O verso está livre sob as teclas, então quatro desses pilares caem bem embaixo de uma tecla. Há 3779 lugares livres no verso; o case pode pôr mais.
  - O modelo conta os dois cantos cortados da ponta como placa, então é um pouco otimista ali.
- **Áudio:** as rotas novas das teclas ficam em x de 62,5 a 198 mm. A trilha de tecla mais próxima de uma trilha de áudio na mesma camada está a 24,6 mm (`OUT_K08` de `SPK_P`). O codec, a saída de fone e o amplificador não foram tocados.
- **Calor:** carga, conversor e amplificador estão nas posições da J1, com o cobre dela. As teclas não aquecem: cada uma passa no máximo 0,33 mA (3,3 V sobre 10 k), uma por vez.

Não conferido: nenhuma medida com a folha sensível real; alturas e mecânica (não há case nem botões para esta versão).

## Opções para as teclas resistivas

O pente da placa serve para as três primeiras. A escolha é do material que vai por cima.

| Opção | O que é | Custo (28 teclas) | Velocidade | Para quando |
|---|---|---|---|---|
| **A. Folha Velostat / Linqstat** (recomendada agora) | disco de 13 mm de filme condutivo, solto sobre o pente, com um anel adesivo fino como espaçador | uma folha, poucos dólares | pela subida da pressão; repetição entre teclas mediana, pede calibração por tecla | este protótipo |
| **B. Membrana FSR impressa** | uma folha de PET única, com 28 pontos de tinta FSR e espaçador, feita por fabricante de teclados de membrana | ferramental pequeno, depois barato por peça | a mesma medida, bem mais uniforme e estável | segunda rodada, se a A agradar ao toque |
| **C. Manta de silicone com pastilha de carbono** | botões de borracha moldados; com dois contatos em alturas diferentes mede o tempo entre eles, como teclados de sintetizador | molde caro, peça barata | a mais fiel, mas sem pressão contínua | produto final |
| **D. Toque capacitivo** | o mesmo cobre lido como capacitor, sem material nenhum | zero | não mede força | não atende ao objetivo |

Pontos a decidir ou medir com a opção A:

1. **Faixa da resistência.** Os 10 k de R601/R602 são um ponto de partida. Com a folha na mão, meça a resistência de uma tecla solta, tocada de leve e apertada, e ajuste o valor (são só dois resistores 0402).
2. **Espaçador.** Com o anel adesivo a tecla fica aberta sem toque e o limiar é nítido. Sem ele, a folha encosta sempre e a leitura deriva.
3. **O que o dedo toca.** A folha crua não é agradável nem durável. Um botão de silicone ou uma capa impressa por cima distribui a força.
4. **Acabamento.** Pedir **ENIG** (a J1 já pede): estanho (HASL) fica irregular e oxida no cobre exposto.

Antes de encomendar a placa inteira, vale um teste de bancada com um pente só (um recorte de placa ou uma placa de teste de 5 × 5 cm) e a folha escolhida.

## Opções para o uso do MicroMod

A placa hoje: conector M.2 Key E + módulo SparkFun MicroMod Teensy (DEV-16402), o mesmo da J1.

| Opção | O que muda | Ganho | Custo |
|---|---|---|---|
| **1. Como está** | nada | pronto; firmware `teensy:avr:teensyMM`; módulo reaproveitado entre placas | módulo de ~US$ 25 por instrumento |
| **2. Cartão próprio no formato MicroMod** | um cartão de 22 × 22 mm com o RT1062 em BGA, desenhado por nós, encaixado no mesmo M.2 | o passo para o BGA acontece num cartão pequeno e barato de repetir, sem tocar na placa das teclas; foi o roteamento do BGA que travou o Viaggio v2.1 | um projeto novo, de 6 camadas, com o bootloader da PJRC |
| **3. Outro processador MicroMod** | trocar o cartão (RP2040, ESP32, STM32) | cartões de US$ 10–15 para versões de estudo | firmware e áudio refeitos; só os pinos padrão do MicroMod coincidem |
| **4. Placa de 2 camadas para a Student** | sem BGA e sem sensores, o roteamento é simples o bastante para tentar 2 camadas | PCB mais barato | roteamento refeito do zero; perde o plano de GND inteiro sob os pentes |

- **Recomendação:** ficar na opção 1 para este protótipo e tratar a 2 como o caminho para o BGA. O esquema do cartão da SparkFun é aberto e o `MM_PADS` do `schematic.py` já tem a ligação pad a pad.
- O que ajuda a trocar de cartão: os sinais de áudio, I2C e as duas entradas analógicas dos mux já estão nos pads padrão do MicroMod (`AUD_*`, `I2C_*`, `A0`, `A1`). Os demais (endereço dos mux, encoders, LED, liga/desliga) usam pads que mudam de função entre processadores.

## Próximos passos

1. **O J escolhe** a opção das teclas e confirma o MicroMod.
2. Teste de bancada de um pente com a folha.
3. Firmware das teclas resistivas (agente `programacao-som`): varredura, limiar, velocidade pela subida, aftertouch.
4. Arquivos de fabricação (Gerbers, BOM/CPL), com a conferência de alturas sem a plate.

## Perguntas para a gestão

1. A Student entra no protocolo com SPEC própria, ou segue como variante da SPEC do Viaggio MicroMod?
2. A placa nua passa do alvo de flexão (0,122 mm) só com os 11 furos. O case desta versão terá os 6 pilares propostos, ou vale engrossar a placa para 1,6 mm?
3. Haverá botão sobre a folha nesta versão? Disso dependem a altura e o case.
4. As pastas `student/` e `studentBK/` (v20, fora do Git) podem ser apagadas?
