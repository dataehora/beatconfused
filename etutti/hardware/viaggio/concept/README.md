# Layout conceitual do eTutti Viaggio

## Rev2 (vale a partir da SPEC v2, 24 out 2026)

`rev2/` tem a planta 2D aprovada pelo J nas etapas 1 e 2 da Rev2. Só biblioteca padrão.

- `rev2/rev2_layout.py`: placa retangular, perfil A, limite da interface, teclas (lidas do `pocket.json` do Pocket), posição das peças e furos.
- `rev2/rev2_sectors.py`: importa o anterior e escreve:
  - `rev2/out/viaggio_rev2.json`, o **contrato de posicionamento** para a eletrônica: placa, perfil A, limite da interface, teclas, furos M2, setores, peças com código (P1…T4), lado e posição, e os corredores C1…C7;
  - `rev2/out/viaggio_rev2.svg`, o desenho.

Rode `python rev2/rev2_sectors.py`. Os códigos e as regras estão na `SPEC.md` (§2 e §3).

A eletrônica pode ajustar posições em alguns milímetros para rotear. Mudar uma peça de setor, de lado da placa ou de corredor é pedido à gestão no relatório.

## Rev1 (histórico)

`layout_concept.py` → `out/viaggio_concept.json`: a primeira impressão de 19 out 2026, com o contorno curvo (perfil A). Substituída pela Rev2.
