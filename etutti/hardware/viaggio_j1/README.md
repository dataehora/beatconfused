# eTutti Viaggio J1 · a placa que o J roteia

Cópia de trabalho da placa do **Viaggio MicroMod** (SPEC v2.3), feita em 27 out 2026 a partir do `main` depois do PR #121.

- **O que já vem:**
  - todas as peças posicionadas;
  - regras (vias 0,5/0,3, `.kicad_dru` válido no KiCad 10);
  - In1 = GND inteiro, In2 = camada de trilhas;
  - **o par USB já roteado e travado** (USB_DP e USB_DN: 46 trilhas e vias, DRC limpo).
- **O que falta:** o resto do roteamento, feito pelo J no KiCad com o Freerouting.
- **Esta pasta é do J.** Nenhum script do Code roda sobre ela (o `build_board.py` e o `route_usb.py` da pasta `viaggio_micromod/pcb/` escrevem só lá). Depois do roteamento, a sessão de conferência (passo M3) parte desta placa.
- O projeto KiCad continua se chamando `viaggio_micromod`, porque o esquema guarda esse nome em cada peça. Abra `kicad/viaggio_micromod.kicad_pro`.
- Arquivos temporários do roteamento (`.dsn`, `.ses`, relatórios `.rpt` e a pasta `copias/`) ficam fora do Git (`.gitignore`).
