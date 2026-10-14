# Brief · site e manuais do eTuttino (depois da SPEC v9)

Para a próxima sessão do Claude Code. O hardware está fechado (SPEC v9 em `hardware/case/SPEC.md`, placa v0.7, plate de 1,6 mm, plaquinha de controles, firmware com os knobs). O protótipo **ainda não foi montado nem encomendado**. Os textos devem tratar o eTuttino como um projeto pronto para fabricar, sem dizer que já foi testado montado, exceto o que de fato foi: firmware gravado e testado num Teensy com Audio Board.

Regras que continuam valendo (ver `CLAUDE.md`):

- `/etutti/` e as páginas abaixo dele continuam fora da home, fora do `sitemap.xml` e com `noindex`.
- Três idiomas (en/pt/es) em todas as páginas.
- Manuais neutros quanto ao país (sem falar de importação ou alfândega).
- Nunca citar o acordeom comercial com o qual o layout foi comparado no início.

## 1. Página `/etutti/`

- **Seguir os knobs**: ao receber CC 7 (volume) e CC 25 (instrumento) do Teensy, atualizar o controle de volume e o seletor de instrumento na tela, e o marcador "modificado", sem mandar o CC de volta. O "Listen in this browser" segue o mesmo valor.
- **Texto da seção "Setting up the Teensy"**: acrescentar os knobs: volume, seletor (girar troca, clique grava como instrumento ao ligar, clique parado volta ao acordeom clássico) e o LED.
- **Link para os modelos e os manuais**: manter, com os textos atualizados para o case novo.

## 2. Página `/etutti/models/`

Hoje mostra os conceitos antigos (pega à esquerda de 76 mm). Refazer em torno do case novo:

1. **Abertura**: o eTuttino no case novo, com o render isométrico do Seixo (`hardware/case/renders/seixo_iso.png`) em destaque. Uma frase: teclado C-griff de 44 botões, grade hexagonal de 18,5 mm, área de interface à esquerda.
2. **Dois acabamentos, mesma forma**: Seixo (plástico, resina ou MJF) e Madeira (carvalho branco, CNC em duas fixações), lado a lado, com os renders de cima e da face esquerda de cada um.
3. **Anatomia** numa figura com legendas: área do teclado (folga de 1 botão nas diagonais, chanfro), área de interface (tela ou gravação no topo, volume, seletor, LED, grade a 13°), conexões na face esquerda (micro-USB e fone), rampa arredondada entre as áreas.
4. **Botões**: domo baixo com saia, branco nas naturais, preto nos sustenidos, xadrez em relevo nos Dós e Fás. Usar um render das capas (gerar a partir de `keycap_*.stl` se ainda não existir).
5. **A família**: eTuttino (44 botões), eTutti (48, uma tecla a mais por fileira) e eTuttiChorus (com tela, alto-falante e bateria, pilha ≤ 10 mm), agora como variações do case novo. Se o eTutti e o Chorus ainda não tiverem modelo, mostrar só uma tabela com as diferenças e marcar "em desenvolvimento".
6. **Tabela de medidas**: ~331 × 100 mm, altura 33 mm na interface e 26,6 mm no topo dos botões, materiais, peso estimado se o `case.py` puder calcular.
7. Retirar o texto e as figuras do conceito antigo (pega de 76 mm, rampa até as teclas).

Visual: manter o estilo atual das páginas do eTutti (fundo escuro, mesma tipografia). Figuras clicáveis em tamanho grande, como nos manuais (`lightbox.js`).

## 3. Manual de montagem (`/etutti/manuais/`)

Refazer para a placa v0.7, o case novo e a plaquinha de controles. Manter as duas rotas (A: placa montada pela JLCPCB; B: tudo soldado em casa). Ordem sugerida:

1. **Antes de começar**: lista do que comprar (BOM atualizado: placa principal, plate FR-4 de 1,6 mm, plaquinha de controles, 44 Gateron KS-20, Teensy 4.0, Audio Board Rev D, EC11E de 15 pulsos / 15 cliques, potenciômetro RK09K, LED 3 mm vermelho/verde, conectores de painel micro-USB e jack, cabo micro-USB de 90°, cabo JST PH de 8 vias, parafusos M2), o que imprimir ou fresar (case Seixo ou Madeira, inserto, capas) e ferramentas.
2. **Capas de teste**: imprimir o `keycap_test_4.stl` e conferir em quatro switches antes de imprimir as 44 capas.
3. **Placa principal**: sensores Hall no lado de baixo (explicar por quê, com a figura do polo), multiplexadores, LDO.
4. **Pilha baixa**: Teensy soldado direto na Audio Board, ~13 mm no eTuttino. Medir a altura antes de seguir.
5. **Plate e switches**: encaixar o plate, soldar ou encaixar os 44 switches.
6. **Plaquinha de controles**: potenciômetro, encoder, LED no espaçador, conector; cabo até o J3.
7. **Conexões de painel**: micro-USB e jack no inserto, cabos até o Teensy e a Audio Board.
8. **Fechar o case**: placa nos pilares, os dois parafusos M2 por baixo, plaquinha nos postes sob a tampa, tampa e fundo. Na Madeira, o light pipe do LED.
9. **Primeiro uso**: gravar o firmware, calibrar as teclas, teste de teclas na página.

Figuras: refazer as figuras 3D do `assembly3d.py` com a placa v0.7, o case novo e a plaquinha (o CLAUDE.md marca que hoje elas mostram a v0.5). Uma figura por passo, e o caso montado em corte mostrando a pilha, a plaquinha e os parafusos.

## 4. Manual de uso

- Os knobs: volume; seletor (girar troca o instrumento na hora, clique grava como instrumento ao ligar, clique parado volta ao acordeom clássico).
- O LED: laranja ao ler as teclas, verde tocando, vermelho piscando com problema (e o que conferir).
- A página: conectar, instrumentos, registros, calibrar, teste de teclas, e que ela acompanha os knobs.
- C-griff e B-griff, e o xadrez nos Dós e Fás para achar a posição no tato.
- Cuidados: limpeza do case (resina ou óleo na Madeira), não puxar o cabo USB de lado.

## 5. Revisar o resto da documentação

- `etutti/hardware/README.md` e o `README.md` da raiz: estado atual (placa v0.7, case v9), sem referências ao case FreeCAD removido.
- `CLAUDE.md`: atualizar o handoff do eTutti ao fim.
- `hardware/case/canvas-v5/README.md`: deixar claro que são desenhos de referência da v5 e que a forma final é a da SPEC v9.

## 6. Entrega

PRs pequenos, na ordem: página `/etutti/` (knobs), `/etutti/models/`, manual de montagem, manual de uso, revisão da documentação. Conferir cada página no navegador nos três idiomas e numa largura de celular antes do merge.
