# Tarefa · Página inicial do eTutti

**Agente:** programacao-som · **Pedida por:** gestão (Claude Chat), 17 out 2026

## Objetivo

`beatconfused.com/etutti/` vira uma página inicial minimalista da família: quatro botões visuais, um por versão. Só o eTuttino Pocket abre. Os outros três mostram "em desenvolvimento".

## O que fazer

1. **Preservar a página atual.** Mova o app de hoje (`etutti/index.html`, com `script.js`, `websynth.js` e `styles.css`) para `etutti/etuttino/`, sem mudar o funcionamento.
   - Corrija os caminhos relativos: `manuais/`, `models/` e os assets.
   - A página continua acessível pelo endereço direto, mas nenhum botão aponta para ela.
   - Ela é a base da futura página do Pocket.
2. **Nova `etutti/index.html`**, com quatro botões grandes, na ordem:

   | Botão | Descrição curta (en/pt/es) | Ação |
   |---|---|---|
   | eTuttino Pocket | 28 botões · G3–E5 · bateria e alto-falante | abre `etutti/pocket/` |
   | eTuttino | 44 botões · G3–E6 | rótulo "em desenvolvimento", sem link |
   | eTutti | 48 botões · três oitavas | rótulo "em desenvolvimento", sem link |
   | eTuttiChorus | eTutti + tela e alto-falante | rótulo "em desenvolvimento", sem link |

   - Cada botão tem um desenho simples da planta da versão (SVG gerado dos contornos de `pocket.json` e do eTuttino), não uma foto.
   - Os botões "em desenvolvimento" ficam visivelmente desativados, com o rótulo à vista. Nada de links quebrados.
   - Mesmo cabeçalho e mesmo estilo do site (link `site-title`, i18n en/pt/es), sem textos longos.
3. **`etutti/pocket/` provisória**, até a página de verdade (que só vem depois do protótipo e do detalhamento de engenharia):
   - nome, uma frase, a planta do Pocket (`pocket_top.svg` ou um desenho a partir de `pocket.json`) e "protótipo em andamento";
   - sem o app de MIDI ainda.
4. **Manter fora da lista do site:** `noindex` em todas, fora do `sitemap.xml`, sem card na home.
5. **Atualizar os links internos que apontavam para `/etutti/`** (manuais, models) para apontar para `/etutti/etuttino/` quando se referirem ao app.

## Conferir

- Navegador do app: as quatro páginas abrem sem erro no console.
- Nenhuma rolagem lateral em 375 px.
- Os três idiomas.
- Os botões desativados não navegam.
- O app movido ainda conecta (MIDI falso pelo `javascript_tool`, como no `CLAUDE.md`).

## Relatório

No PR e no `etutti/hardware/pocket/FIRMWARE_SOM.md`: o que foi feito e "Perguntas para a gestão".
