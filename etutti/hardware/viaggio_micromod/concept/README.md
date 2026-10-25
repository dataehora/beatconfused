# Planta conceitual do eTutti Viaggio MicroMod

Só biblioteca padrão. Rode `python etutti/hardware/viaggio_micromod/concept/sectors.py`.

- `layout.py`: placa retangular, perfil A, limite da interface, teclas (lidas do `pocket.json` do Pocket), posição das peças e furos. É a planta do Viaggio Rev2 com o setor P trocado pelo conector M.2 e o módulo MicroMod Teensy.
- `sectors.py`: importa o anterior e escreve:
  - `out/viaggio_micromod.json`, o **contrato de posicionamento** para a eletrônica: placa, perfil A, limite da interface, teclas, furos M2, setores, peças com código (P1…T4), lado e posição, corredores C1…C7;
  - `out/viaggio_micromod.svg`, o desenho.

A eletrônica pode ajustar posições em alguns milímetros. Mudar uma peça de setor, de lado ou de corredor é pedido à gestão no relatório.
