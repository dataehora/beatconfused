# eTuttino case — Seixo and Madeira (CadQuery)

Parametric model of the case described in [SPEC.md](SPEC.md) — currently
**v9** (shape frozen since v7; v9 changed only the firmware and the page): pitch 18.5 mm on a hexagonal grid, the deck
round the keys at z 17.4, Ø16.5 cap skirts, the ramp's front curve to 75°
then straight. v8 adds:

- the 1.6 mm FR-4 plate: the buttons' tops are at z 26.6;
- two M2 screws from below through thicker pillars, to hold the main
  board under the interface;
- two posts under the interface lid for the controls board.

The reference drawings in [canvas-v5/](canvas-v5/) are v5's (general
shape only); the measurements in SPEC v9 and this model win.
There are two versions:

- **Seixo**: resin or MJF, one colour.
- **Madeira**: white oak, cut on a 3-axis CNC in two setups (top, then the inner pocket from below).

Both have the same outside. Only the wall thickness, the LED (a plain hole
in the Seixo, a hole with a bought 3 mm light pipe in the Madeira) and the
pocket round the connector insert differ.

The electronics check (SPEC item 9) is in **[FIT_CHECK.md](FIT_CHECK.md)**.
It is in Portuguese because it answers the SPEC. It ends with "Perguntas
para o design", the open questions for the next SPEC version.

## Regenerate

CadQuery and PyVista live in a venv, outside the repo:

```bash
python -m venv C:/Users/julia/.venvs/cadquery
C:/Users/julia/.venvs/cadquery/Scripts/python.exe -m pip install cadquery pyvista
```

Then, from this folder:

```bash
C:/Users/julia/.venvs/cadquery/Scripts/python.exe case.py        # case parts -> out/
C:/Users/julia/.venvs/cadquery/Scripts/python.exe keycap.py      # caps + switch stand-ins -> out/
C:/Users/julia/.venvs/cadquery/Scripts/python.exe render.py      # renders/{seixo,madeira}_{iso,top,left}.png
C:/Users/julia/.venvs/cadquery/Scripts/python.exe fit_check.py   # FIT_CHECK.md + renders/fit_*.png (~3 min)
C:/Users/julia/.venvs/cadquery/Scripts/python.exe pcb_envelope.py # out/pcb_envelope.json for the board
C:/Users/julia/.venvs/cadquery/Scripts/python.exe models_render.py  # pictures + numbers for /etutti/models/
python models_page.py                                                # writes etutti/models/index.html (texts live here)
```

Run `case.py` and `keycap.py` before `render.py`, and `render.py` before
`models_render.py` (it crops render.py's PNGs). The assembly manual's
pictures are made in Blender by [`../manual3d/`](../manual3d/) (`build.py`),
from these STLs and the KiCad boards.

## Files

| File | What |
|---|---|
| `out/seixo_tampa.*` / `out/seixo_fundo.*` | Seixo top shell / bottom plate (STEP + STL) |
| `out/madeira_corpo.*` / `out/madeira_fundo.*` | oak body / thin bottom cover |
| `out/pcb_envelope.json` | the room for the main board: outline, boss notches, supports, plate edge, height levels, key centres, stack / controls-board / panel footprints (`pcb_envelope.py`; plan in `renders/pcb_envelope.png`). `etutti/hardware/generate.py` reads it. |
| `out/insert.*` | black connector insert for the left face (USB + headphones) |
| `out/plate.step`, `out/plate.dxf` | 1.6 mm switch plate (FR-4 since v8), MX 14 × 14 holes on the 18.5 mm hex grid (rows 16.02 apart) |
| `out/keycap_{natural,sharp,cf}.stl` | the three caps (C/F has the raised diagonal chequer) |
| `out/keycap_test_4.stl` | four caps on sprues, laid out like four neighbouring buttons, for the fit test on real switches |
| `out/switches.stl` | stand-in switches, used by the renders only |
| `renders/fit_*.png` | the fit check's plans and sections (see FIT_CHECK.md) |
| `renders/models_*.png` | the anatomy call-outs and the keycap picture for /etutti/models/ |

**Coordinates.** The code works in SPEC coordinates: x to the right, y
towards the player, z up. That system is left-handed, so a model built
directly in it comes out mirrored in any CAD program. The exported files
are therefore mirrored back: `y_file = 100 − y_spec`. In the files x points
right, y points away from the player and z points up, which puts the
interface on the player's left. Keycaps are exported centred on their own
axis.

## Parameters (top of `case.py`)

- **Keyboard**
  - `P` (18.5) — button pitch, the same to all six neighbours.
  - `D_BTN` (15) / `D_SKIRT` (16.5) — button and skirt diameters.
  - `O_KEYS` — x of the first key column.
  - `ROW_Y` — y of each row, `ROW_PITCH` = P · cos 30° apart, centred on `KEYS_CY`.
  - `keys()` — puts the 44 notes on rows using the SPEC 2 rules.
- **Opening**
  - `CLR_SIDE` (15) / `CLR_FB` — side and front/back clearances. `CLR_FB` is derived so the deck round the keys stays `BOX_OFF` wide in the 100 mm box (8.17 at P = 18.5).
  - `SIDE_ANGLE` (30°) — angle of the opening's sides.
  - `R_OPEN_CORNER` (6) — corner radius.
  - The lateral fillets are concentric with the end buttons.
  - `CHAMFER_W` (4) / `CHAMFER_DROP` (2) — the rounded edge. A vertical land under it (`LID_T - CHAMFER_DROP`, 2.6) brings the lid down to the plate.
- **Box**
  - `BOX_OFF` (10.3) — the box is the opening grown by this amount.
  - `R_LEFT` (16) — radius of the two left corners.
  - `Z_DECK` (17.4) — deck height; the lid round the keys is `LID_T` = 4.6 thick and rests on the plate's edge.
  - `Z_IF` (33), `IF_CREASE_Y` (55), `IF_SLOPE` (13°), `IF_CREASE_R` (10) — interface top: flat, rounded crease, then down to the front.
  - The ramp: top edge = opening + `RAMP_TOP_OFF` (12.7), foot = opening + `RAMP_FOOT_OFF` (4). In the front half both run straight to `RAMP_STRAIGHT_TO` (86), then curve with `RAMP_FRONT_R` (14) through `RAMP_FRONT_SWEEP` (75°) and run straight into the front face. `RAMP_EDGE_R` (5) rounds both edges.
  - Every ramp and box line is an offset of the keyboard opening, so changing `P` moves them all.
- **Stack-up**
  - These match the current board.
  - `Z_PCB_TOP` = 7.7, plate top `Z_PLATE_TOP` = 12.8 (1.6 mm FR-4 plate), `Z_KEY_TOP` = 26.6.
  - So the lid round the keys is `LID_T` = 4.6 mm thick (deck at 17.4) and rests on the plate's edge.
- **Interface**
  - `SCREEN_ZONE` / `SCREEN_MODE` (`"recess"` for a sticker or engraving, `"window"` for a real screen, `"none"`).
  - `VOLUME_XY`, `SELECT_XY`, `LED_XY`.
  - `GRILLE_RECT` with corners `GRILLE_R` / `GRILLE_R_FR`, holes `GRILLE_D` at `GRILLE_PITCH` measured on the 13° surface.
- **Connectors**
  - `USB_YZ`, `JACK_YZ`, `INSERT`.
  - `USB_PLUG_CUT` / `JACK_HOLE_D` (CHECK against the panel parts bought).
  - `INSERT_WALL` — the Madeira wall is thinned to this round the insert.
- **Versions**: `VERSIONS = {"seixo": {wall 2.5, top 2.5}, "madeira": {wall 4, top 3}}`.
- **Fixings**
  - `screw_points()` — M2.5 bosses from the bottom up into the top, notched out of the plate. `BOSS_TOP` stops two of them short of the lid (one would hit the screen module, one the grille); they hang on the walls.
  - `pillar_points()` — board supports on the bottom plate: one at the centre of every triangle of three neighbouring keys (61, 10.7 mm from each sensor) plus 3 under the interface. The board sags ≤ 0.044 mm under a 3 N press on them (`../mechanics.py`).

`keycap.py` has the switch numbers, from Gateron's KS-20T drawing
(top housing 15.40 × 15.10, 11.10 mm from the board, travel 4.1). The top
face and the stem height aren't dimensioned there: the four-cap print test
checks them. The skirt height is calculated, not
picked: the round skirt must clear the square top housing's corners at full
travel.

Values marked **CHECK** in the code are the SPEC's *conferir* items, plus a
few part dimensions (panel connectors, screen thickness, speaker depth)
that need the real part.
