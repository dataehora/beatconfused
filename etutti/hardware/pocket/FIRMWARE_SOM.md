# eTuttino Pocket · firmware e som (relatório da programação)

Relatório do agente `programacao-som`. Cada tarefa tem uma seção; o fim do
arquivo traz as perguntas abertas para a gestão.

## Página inicial da família eTutti (17 out 2026)

**Pedido:** `etutti/TAREFA-pagina-inicial.md` (gestão, 17 out 2026). SPEC
de referência: v1 (nenhuma tarefa de firmware do Pocket nesta rodada; o
modelo `ETUTTI_MODEL_POCKET` ainda não existe no sketch).

### O que foi feito

- **App do eTuttino movido** para `etutti/etuttino/` com `git mv`
  (`index.html`, `script.js`, `websynth.js`, `styles.css`), sem mudar o
  funcionamento. Ajustes:
  - links `manuais/` e `models/` → `../manuais/` e `../models/`;
  - `?v=` dos três arquivos próprios trocado para `20261025` (os assets
    de `/shared/` e `/i18n/` usam caminho absoluto e não mudaram);
  - nenhum `fetch`/`import` relativo existia no `script.js`/`websynth.js`.
  - O app continua acessível por `/etutti/etuttino/`; nenhum botão da
    página inicial aponta para ele.
- **Nova `etutti/index.html`:** página inicial mínima, quatro cartões
  grandes na ordem pedida, cada um com a planta vista de cima:
  - eTuttino Pocket: um `<a href="pocket/">`;
  - eTuttino, eTutti e eTuttiChorus: `<button disabled>` (sem `href`,
    nem `#`), meio apagados, com o rótulo "Em desenvolvimento".
  - Textos curtos da tabela da tarefa, em en/pt/es pelo `BC_I18N`
    (`window.BC_STRINGS` + `data-i18n`, como as outras páginas).
  - Mesmo cabeçalho do site (`site-title` com o seu `?v=`, eyebrow, h1),
    `noindex,nofollow`.
- **Desenhos (SVG inline), reproduzíveis:** `etutti/landing_svgs.py`
  (stdlib). Ele reescreve o SVG entre os marcadores
  `<!-- BEGIN svg:… -->` / `<!-- END svg:… -->` nas duas páginas.
  - Pocket: teclas, abertura, contorno e interface lidos do
    `pocket/build/pocket.json` (só leitura).
  - eTuttino (44), eTutti (48, uma tecla a mais por fileira:
    F♯6/G6/F6/D♯6) e eTuttiChorus (o eTutti + a tela de 1,9"): mesma
    grade C-griff e mesmo método de contorno do `pocket/layout.py`
    (importado, não alterado), com O = 104. A interface (zona da tela,
    volume, seletor, LED, grade) vem dos valores do `case/case.py`.
  - Os quatro cartões usam a mesma escala, então o Pocket aparece menor.
    Comprimentos: Pocket ≈ 237, eTuttino ≈ 331, eTutti/Chorus ≈ 350 mm.
  - Cores por classes CSS (`etutti/family.css`, novo, `?v=20261017`).
  - Para refazer: `python etutti/landing_svgs.py` depois de mudar o
    `pocket.json`. O script não deixa `__pycache__` na pasta do design.
- **`etutti/pocket/index.html` provisória:** nome, uma frase, a planta do
  Pocket com os nomes das notas, "Protótipo em andamento", o tamanho
  aproximado (≈ 237 × 100 mm, também escrito pelo script) e o link
  "← A família eTutti". Sem app de MIDI. en/pt/es, `noindex`.
- **Links internos:**
  - `etutti/manuais/index.html`: os links "beatconfused.com/etutti"
    (ouvir no navegador, Conectar, Teste das teclas) e os títulos
    "Com a página beatconfused.com/etutti" agora dizem e apontam para
    `/etutti/etuttino/`, nas três línguas.
  - O "← Voltar ao eTutti" dos manuais e da página de modelos virou
    "← Voltar à página do eTuttino" (`../etuttino/`). Motivo: as duas
    páginas são do eTuttino e só são abertas a partir do app; voltar
    para a página inicial deixaria o leitor sem caminho de volta ao app,
    já que a página inicial não liga para ele.
  - `etutti/models/index.html` é gerado: mudei o
    `case/models_page.py` e rodei de novo (saída igual à edição à mão).
  - Comentários "keep in sync with etutti/script.js" no sketch e no
    `firmware/README.md` agora dizem `etutti/etuttino/script.js`. O
    `hardware/generate.py` (do eTuttino pausado, não é meu) ainda diz
    `etutti/script.js` num comentário.
- `sitemap.xml`, `robots.txt` e a home do site não foram tocados: nenhum
  deles cita o eTutti.

### Como foi conferido

- Firmware: `arduino-cli compile --fqbn teensy:avr:teensy40:usb=midi
  etutti/firmware/etutti_synth` compila (FLASH code 85 432, RAM1
  variáveis 61 696, RAM2 22 400). Só mudaram comentários; não regravei o
  Teensy. O modelo Pocket ainda não existe, então só há um modelo para
  compilar.
- Navegador do app, viewport 375 × 812, nas cinco páginas
  (`/etutti/`, `/etutti/pocket/`, `/etutti/etuttino/`, `/etutti/models/`,
  `/etutti/manuais/`):
  - console sem mensagens em todas;
  - `scrollWidth` = 375 = `innerWidth` em en, pt e es, e nenhum
    elemento passa da borda direita (fora de tabelas com rolagem
    própria);
  - os três idiomas trocam textos e, nos manuais e modelos, o
    `.lang-block` certo;
  - todo `img`/`script`/`link`/`a` local responde 200 (7 na inicial, 7 no
    Pocket, 10 no app, 26 em modelos, 61 nos manuais);
  - inicial: clicar os três cartões desativados não muda o endereço;
  - app movido: com um `navigator.requestMIDIAccess` falso, Conectar
    mostra "Connected to eTutti.", envia as 25 mensagens iniciais (CC 24, 9, 15, 25…) e um toque na
    tecla A3 envia `90 39 64` / `80 39 00`.
- Visual (Edge headless, 1000 px): a inicial e a página do Pocket
  conferidas em captura de tela.
- Observação: o servidor do `.claude/launch.json` (`HTTPServer` de uma
  linha só) travou com o painel do navegador oculto; usei uma cópia com
  `ThreadingHTTPServer` no scratchpad, porta 5861.

## Perguntas para a gestão

1. **Alto-falante do Pocket.** A tarefa pede "28 botões · G3–E5 ·
   bateria e alto-falante", e a página diz isso. A SPEC v1 §8 diz que o
   Pocket não tem alto-falante (a grade é só ventilação); o rascunho do J
   (`pocket/rascunhos/layout_v2.py`) põe uma grade de alto-falante. O
   desenho mostra a grade que o `pocket.json` tem, sem dizer para que
   serve. Qual vale? Se não
   houver alto-falante, troco o texto para "bateria" só.
2. **"Voltar" dos manuais e da página de modelos.** Escolhi voltar para
   a página do app (`/etutti/etuttino/`), não para a página inicial.
   Serve?
3. **Título do app movido.** `/etutti/etuttino/` continua com o título
   e o h1 "eTutti" e com o seletor eTuttino/eTutti antigo, porque a
   tarefa pediu para não mudar o funcionamento. Trocar para "eTuttino"
   quando ele virar a base da página do Pocket?
4. **Contornos dos desenhos.** São o casco convexo do `layout.py` (o
   mesmo método que dá os 331 mm do eTuttino), não o case exato; o
   Pocket ainda não tem o "<" do rascunho do J. Quando o design publicar
   o contorno do case do Pocket no `pocket.json`, o script passa a usá-lo
   sem outra mudança, desde que continue nas chaves `box`/`opening`.
