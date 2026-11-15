# eTutti Student V01 · etapa 6 · firmware

15 nov 2026. **O firmware compila e os pinos batem com a placa. Ele nunca rodou numa placa Student V01**, porque ela ainda não existe: tudo o que é tempo, limiar ou comportamento de energia abaixo é um primeiro valor, a acertar com a placa na mão.

## Um sketch só, dois instrumentos

O firmware continua sendo `etutti/firmware/etutti_synth/`. A placa para a qual se compila escolhe o instrumento:

| Placa no Teensyduino | Instrumento |
|---|---|
| Teensy 4.0 | eTuttino (44 teclas), como antes |
| **Teensy MicroMod** | **Student V01** (28 teclas) |

Assim o som é um código só: o acordeão amostrado, os registros, a velocity como pressão de fole e os controles MIDI são os mesmos nos dois.

```
arduino-cli compile --fqbn teensy:avr:teensyMM:usb=midi,speed=396 etutti/firmware/etutti_synth
```

`speed=396` é a velocidade usada no orçamento de bateria (`viaggio_j1/POWER.md`). No Arduino IDE: Tools > Board > Teensy MicroMod, USB Type > MIDI, CPU Speed > 396 MHz.

## O que é próprio da Student V01

| Função | Como ficou |
|---|---|
| Teclas | 28, em 2 multiplexadores; a tabela `KEY_INPUT` é a lida da placa roteada |
| Sensores | TMAG5253: ligados pelo pino 4; a linha S3 liga metade deles por vez, e o firmware espera 60 µs a cada troca |
| Direção do sensor | o TMAG5253 lê os dois polos. O firmware descobre, tecla por tecla, se a leitura sobe ou desce, pelo valor em repouso, e trata tudo como "sobe" |
| Ligar | segurar o clique do volume 2 s; soltar antes desliga de novo |
| Desligar | segurar o clique do volume 2 s; o LED apaga quando pode soltar |
| Knob de volume | girar muda o volume (3 passos de 127 por clique do knob) |
| Knob seletor | girar percorre os sete registros: L, ML, MM, MH, H, LH, M. O LED pisca verde até o clique. Clique depois de girar: guarda o registro, que passa a ser o da partida. Clique sem girar: volta para MM |
| Alto-falante | ligado quando não há fone plugado |
| Volume | aplicado antes da saída digital, porque o amplificador do alto-falante recebe o mesmo sinal do codec e não tem volume próprio |
| Bateria | lida a cada 0,5 s. Abaixo de 3,5 V o LED pisca vermelho devagar; 10 s abaixo de 3,3 V desligam o instrumento |
| Descanso | 5 minutos sem tecla, knob ou MIDI: o amplificador do alto-falante desliga. 15 minutos: o instrumento desliga. Nunca com USB ligada |

| LED | Significado |
|---|---|
| laranja piscando rápido | ligando (clique ainda apertado) |
| laranja | partida; depois, carregando com o instrumento ligado |
| verde | ligado |
| verde piscando | um registro escolhido espera o clique |
| verde, um lampejo a cada 2 s | em descanso |
| vermelho piscando devagar | bateria fraca |
| vermelho piscando rápido | o codec ou o sensor de alguma tecla não respondeu |

Os outros instrumentos do firmware (piano, baixo, violão, sintetizador) continuam respondendo pela página, por MIDI. Os knobs só tratam do acordeão.

## Conferências feitas

| Conferência | Resultado |
|---|---|
| Compila para o Teensy MicroMod (600 e 396 MHz), com as amostras do acordeão | sim; 1,44 MB de 16 MB de flash |
| Compila para o Teensy 4.0 | sim, mesmo tamanho de antes |
| Teensy 4.0 do J regravado com esta versão | aparece como MIDI, como antes |
| Pinos do firmware × mapa de pinos × placa (`firmware_check.py`) | **27 de 27** |
| Tabela das teclas × a lida da placa | igual, 28 teclas, 28 entradas diferentes |

```
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v01/firmware_check.py
```

O script lê as constantes do sketch, o `viaggio_micromod/pcb/PINOS.md` e a placa, e confere que cada pino que o firmware usa chega, no conector do módulo, à rede que o nome dele diz. Sai com erro se algo diferir.

## O que só a placa vai dizer

1. **Liga/desliga.** É a parte mais delicada e a que mais depende do circuito. A lógica segue o `PINOS.md`, com uma diferença consciente: com USB ligada, um clique curto liga o instrumento (o `PINOS.md` pede que ele desligue de novo). O firmware não tem como distinguir esse caso de uma partida depois de gravar firmware, e desligar depois de cada gravação seria pior.
2. **Direção e curso dos sensores.** A detecção pelo repouso supõe que o ímã da tecla solta já desloca a leitura uns 0,15 V. Se o deslocamento for menor que 0,04 V, o firmware supõe "sobe" (`DEFAULT_SIGN`), e isso pode estar errado.
3. **Velocity.** Os limiares e tempos são os do eTuttino, que também nunca foram ajustados com teclas de verdade.
4. **Clique dos knobs.** `ENC_STEPS_PER_DETENT = 2` vem da folha do encoder (18 pulsos, 36 cliques por volta).
5. **Detecção de fone, limiares de bateria, luz de carga.**
6. **Vigia contra travamento (watchdog).** O `PINOS.md` pede; não foi posto. A proteção que existe é a do próprio processador: clique do volume preso 10 s corta a alimentação dele.

## Ainda não feito

- A página (`/etutti/etuttino/`) não tem o modelo Student V01: ela desenha as 44 teclas do eTuttino. O instrumento toca sozinho e manda as notas por MIDI; para a página mostrar as 28 teclas falta esse trabalho.
- Presets livres pelo seletor (a especificação fala em 6 registros e 2 presets; ficaram os 7 registros que o J definiu).
