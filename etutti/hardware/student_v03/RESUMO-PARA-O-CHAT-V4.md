# eTutti Student V3 → V4: resumo para o Claude Chat

Cole o texto abaixo no Chat para começar a V4. Ele é autossuficiente. O Chat deve ter à mão, se puder:
`etutti/hardware/student_v03/SPEC.md` (v8, com os anexos v7…v4), `case/FIT_CHECK.md` e `README.md`.

Protocolo (o mesmo da V3): o **Chat escreve a SPEC versionada** (v1 da V4, v2…, cada uma com "Mudanças desde a versão anterior" e "Tarefas para o Code");
o **Code** modela, verifica e responde no `FIT_CHECK.md` (que termina com "Perguntas para o design"), depois commit → PR → merge. O Code nunca edita a SPEC.
O J relata ao Chat uma linha do tipo "SPEC vN atendida — PR #x; relatórios atualizados".

---

Olá. Vamos começar a **V4 do eTutti Student**. A V3 está **fechada para o protótipo**: placa, case, página e manual prontos, nada encomendado,
impresso ou montado. Preciso que você escreva a **SPEC v1 da V4**. Abaixo, o estado da V3, as medidas fixas que um case novo precisa respeitar,
o que é decisão minha e o que a primeira amostra ainda vai responder.

## O que é o instrumento

Acordeão de teclado para estudar, C-griff: **28 teclas** Gateron KS-20 Magnetic (sensor Hall TMAG5253 sob cada uma, velocity), de G3 a E5, em 4 fileiras de **7, 8, 7 e 6**
(a fileira 1 é a da frente), passo 18,5 mm em arranjo hexagonal (fileiras a 16,02 mm). Tela OLED 0,96″, 2 knobs com clique (volume, registro),
alto-falante de 28 mm, USB-C (carga e MIDI), saída de fone OUT e entrada de microfone IN (3,5 mm), bateria LiPo 503450 (~1000 mAh), módulo SparkFun MicroMod Teensy (i.MX RT1062).
Acabamento Retrô: tampa creme, bandeja cinza, faixas vermelha/laranja/amarela, logo em rebaixo.

## Estado da V3 (21 nov 2026)

- **Placa** (`student_v03/kicad/student_v03.kicad_pcb`, 246,5 × 95 mm, 4 camadas, 1,2 mm): roteada; DRC do KiCad com paridade do esquema = **0 ligações faltando, paridade 0**;
  3 larguras de 0,12 mm na rede EN_B (aceitas desde a V1) e 5 avisos de ponta solta (analisados: são pontas fora do centro de via e um toco curto; removê-los desfaz rotas inteiras, então ficaram).
  **Montagem econômica da JLCPCB só pelo fundo:** 130 peças, 17 tipos Extended; no topo só os 2 encoders (soldados em casa) e os pads dos fios do alto-falante.
  Estimativa da JLCPCB (5 placas, 2 montadas): ~US$ 172–183.
- **Grade** de FR-4 de 1,6 mm (placa separada), cobre recuado até Ø 4,4 em volta de 10 furos escareados a 90°. O escareado é **só de fábrica** (nunca em casa); texto pronto para JLCPCB e PCBWay em `case/GRADE_ESCAREADA.md`.
- **Case** (SPEC v8, desenho fechado): tampa creme sem emenda (z −10,1…14,5, 252 × 100 × 24,6 mm), bandeja de 2 mm que entra por baixo, 10 pés de PU/silicone ≥ 80 Shore A,
  chanfro 4,0 × 3,5, knob alto de 10 mm. **245 pares testados, 0 interferências.**
- **Eletrônica:** o USB acorda o instrumento (D206); sem cadeia PWR_EN. Par USB D+/D− inteiro em B.Cu (17,209 mm cada linha, 90 Ω **não garantido**).
- **Página e manual:** `/etutti/studentV3/` e `/etutti/studentV3/montagem.html` (10 passos, vista explodida por passo, renders fotorrealistas do Blender).
- **Firmware da V3: não existe.** O do Student V01 (`etutti/firmware/etutti_synth/`, `teensy:avr:teensyMM:usb=midi,speed=396`) compila e tem o acordeão amostrado, 7 registros e os knobs,
  mas não tem tela, microfone nem o acordar por USB, e **nunca rodou numa placa**.
- **Nada foi encomendado, impresso ou montado.**

## Medidas fixas (um case novo precisa respeitá-las, ou a placa muda)

| | |
|---|---|
| Placa | 246,5 × 95 mm, de x 2,5 a 249 e y 2,5 a 97,5 (origem no canto de trás à esquerda do case; y cresce para quem toca) |
| Case | 252 × 100 × 24,6 mm; parede de 2,0; placa a 0,5 mm da parede por todos os lados |
| Alturas (z = 0 no topo da placa) | tampa −10,1 … 14,5; grade 11,35 … 12,95; tampa sobre a grade 1,4 mm; topo dos botões 21,9 / 23,9 / 25,9 / 28,9 (fileiras 1 a 4); topo do knob 25,8 |
| Conectores | no **fundo** da placa; USB-C a z −2,9 e jacks a z −4,0 (valores espelhados da V2, **a confirmar na amostra**); frente dos conectores 0,3 mm atrás da face interna da parede esquerda |
| Fixação | 6 parafusos M2 × 14 da bandeja (H1–H4, H9, H10, nos postes da tampa); 10 parafusos M2 × 16 escareados na grade, com porca sob a placa em copos da bandeja; 4 pinos Ø 5 da bandeja nos furos H5–H8; H101 do módulo = furo de 2,7 mm (M2,5 × 8 de náilon + espaçador 2,5 + porca) |
| Apoio | 4 pinos + **4 pilares** (um extra em (112,5; 67,5)) sobre 10 pés Ø 8 × 1,5 de ≥ 80A. Pior tecla: 0,036 mm (0,047 no pior caso); meta ≤ 0,05 mm a 3 N |
| Tela | módulo OLED 0,96″ girado 180°, janela de 24 × 13 mm centrada em x = 37, cabo JST SH de 50 mm subindo pela fenda de 7 × 2,5 mm |
| Som | alto-falante Ø 28 × 5 mm em (37; 73,1); caixa acústica fechada em L de 9,75 cm³ |
| Bateria | 503450, no berço da bandeja em x 19,5–69,5, y 56–90 |
| Encoders | EC11E18244AU em (28; 44,5) e (46; 44,5); eixo de 20 mm, **ponta a ~24,5 mm da placa** |

## O que já foi decidido e não deve voltar (a menos que eu peça)

- Montagem **só pelo fundo** na JLCPCB (economia); encoders e módulo em casa.
- **Sem prateleira** na tampa (a placa entra por baixo e chega a 0,5 mm da parede), **sem corte de eixo**, **sem escarear em casa**.
- Knob de 10 mm sobre o eixo inteiro (não existe EC11E de eixo de 15 mm); pele de 0,8 mm sobre o furo em D.
- Pés de PU/silicone **≥ 80A** (o macio de 40–60A faz a tecla pior passar de 0,05 mm).
- USBLC6 (ESD) e SMF5.0A (TVS) ficam. O USB acorda; sem o trinco de energia.
- Parafusos e porcas **não magnéticos** (latão, inox A4 ou náilon) perto das teclas.
- Nunca citar o acordeão comercial com que o layout foi comparado originalmente.

## O que a primeira amostra vai responder (lista em `FIT_CHECK.md` e no manual)

1. Altura real do USB-C e dos jacks no fundo (`USB_Z`, `JACK_Z`) e o recuo da frente das tomadas, pelo cupom da parede.
2. Pilha real do módulo no H101 (porca e parafuso) e se o rebaixo de 1,0 do piso é preciso.
3. Para que lado abre a boca do J401.
4. Comprimento real do eixo e do chato dos encoders.
5. Compressão real do pé sob 3 N (acima de 0,02 mm, trocar por PU de 90A).
6. OLED, bateria e plugues reais.
7. Par USB: conexão e velocidade, já que a impedância de 90 Ω não está garantida.
8. Se a JLCPCB aceita o escareado cônico NPTH no pedido da grade (senão, PCBWay).

## Pontas soltas da V3 que a V4 pode herdar

- **Firmware:** tela (girada 180°, `setRotation(2)`), microfone, acordar por USB, percentual de bateria, HP_DET, KEEP pela atividade do usuário. É a maior lacuna.
- **O logo da tampa ainda diz "STUDENT · V2"** (SPEC v3, só tinta); a placa e o resto são V3.
- Alto-falante ainda não escolhido (o estudo acústico usa um nominal; o volume de 9,75 cm³ é 6% menor que o da V2).
- Encoder de eixo curto de outro fabricante: tarefa de eletrônica **só para uma série**, fora do protótipo.
- Os modelos 3D reais de várias peças (EC11E, USB-C HRO, JST, QFN) não existem na biblioteca desta máquina; as imagens usam caixas.
- Tempo de espera: a grade escareada e os arquivos de `fab/` ainda **não foram enviados** à JLCPCB.

## O que eu quero decidir com você para a V4

(Preencha ou apague conforme o que eu tiver em mente; sugiro que você me pergunte o que faltar.)

- **Objetivo da V4:** por exemplo, depois da amostra da V3 (correções de medidas), uma versão com mudança de conceito (teclado, tamanho, tela, bateria, custo), ou só ajustes?
- **Do que depende:** a V4 espera a primeira amostra da V3 ou parte já do desenho atual?
- **Restrições de custo e de montagem:** manter montagem só pelo fundo e os 17 tipos Extended, ou aceitar mais?
- **O que muda no case:** forma, acabamento, material (resina/MJF) ou processo.

## O que peço

Escreva `SPEC.md` da V4 (v1) com "Mudanças desde a V3" e uma lista de **Tarefas para o Code**, cada uma marcada Design / Eletrônica / Programação e som.
Se alguma decisão depender de medir uma peça real, diga qual e como medir. Se faltar informação para decidir algo, **me pergunte antes de escrever**.

## Onde está tudo (para o Code, depois)

`etutti/hardware/student_v03/`: `SPEC.md`, `README.md`, `AUDITORIA.md`, `USB.md`, `case/` (`case.py`, `FIT_CHECK.md`, `GRADE_ESCAREADA.md`, `passos.py`, `render_blender.py`),
`pcb/` (scripts da placa), `fab/` (Gerbers, BOM, CPL), `kicad/`, `pagina.py`; páginas em `etutti/studentV3/`.
A V3 é a V2 (`student_v02/`) com a placa refeita para montagem pelo fundo; a V2 e a V1 (`student_v01/`) continuam como referência e **não** são alteradas sem tarefa explícita.
