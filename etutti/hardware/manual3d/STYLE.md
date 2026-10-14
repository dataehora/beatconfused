# Assembly manual · visual standard

The pictures in `etutti/manuais/` follow these rules. `build.py` makes all
of them from the design files. Change this file first when the standard
changes, then the code.

## Two kinds of picture

| | Photo-like (`r_*`) | Line drawing (`l_*`) |
|---|---|---|
| Use | overview, finished instrument, close-ups where material and depth help (the stack, the controls board, the section) | every assembly step |
| Renderer | Blender Cycles, PBR materials, three area lights + top light, caught floor shadow | Blender Freestyle on flat fills |
| Camera | perspective, 50–70 mm | orthographic (axonometric), seen from the front-left and above, unless the step happens underneath |
| Background | page colour `#f7f5f0` | white |

## Line drawings

- **New parts** for that step: amber fill `#f6d58f`, black outline 2.4 px.
- **Parts already in place:** white fill, grey outline `#6b6b6b`, 1.3 px.
- Outlines are silhouettes, borders and creases (134°); hidden lines are not drawn.
- **Motion arrows:** `#c44a24`, straight, ending where the part goes.
- An exploded part moves along the axis it is fitted on (screws straight up from below, caps straight down).

## Balloons

- Circle with a dark ring (`#221e1b`) and a bold number, on a leader line with a dot on the part.
- **Numbers only, no words.** Pictures are shared by the three languages; each
  language's parts list in the manual names the numbers.
- Numbers are fixed for the whole manual (parts list below). A part keeps its
  number in every picture.

| # | Part | # | Part |
|---|---|---|---|
| 1 | bottom (case) | 13 | LED + spacer |
| 2 | lid (case) | 14 | knob (×2) |
| 3 | main board | 15 | 8-way JST PH cable |
| 4 | switch plate | 16 | J3 header |
| 5 | Gateron KS-20 switch (×44) | 17 | connector insert |
| 6 | button cap (×44) | 18 | panel micro-USB socket |
| 7 | Teensy 4.0 | 19 | panel 3.5 mm jack |
| 8 | Audio Board Rev D | 20 | 90° micro-USB cable |
| 9 | extra-long 1×14 header (×2) | 21 | M2 × 10 screw (×2) |
| 10 | controls board | 22 | M2 nut (×2) |
| 11 | volume pot RK09K | 23 | M2 × 5 self-tapping screw (×2) |
| 12 | encoder EC11E | 24 | M2.5 × 8 self-tapping screw (×9) |

## Geometry

- Case, plate, caps: `case/out/` (CadQuery). Boards: KiCad, exported with `kicad-cli`.
- Parts without a manufacturer model (Teensy, Audio Board, switches, pot,
  encoder, LED, panel parts, cables, screws): `parts.py`, from datasheet
  sizes. Swap in a manufacturer STEP when one is available.
- Positions come from `case.py`, `case/out/pcb_envelope.json` and the KiCad
  files, never typed into the picture code by hand.
