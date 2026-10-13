# eTuttino case — Seixo and Madeira (CadQuery)

Parametric model of the case described in [SPEC.md](SPEC.md). There are two versions:

- **Seixo**: resin or MJF, one colour.
- **Madeira**: white oak, cut on a 3-axis CNC.

Both have the same outside. Only the wall thickness, the LED window and the
pocket round the connector insert differ.

The electronics check (SPEC item 9) is in **[FIT_CHECK.md](FIT_CHECK.md)**.
It is in Portuguese because it answers the SPEC.

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
C:/Users/julia/.venvs/cadquery/Scripts/python.exe fit_check.py   # FIT_CHECK.md + renders/fit_*.png (~1 min)
```

Run `case.py` and `keycap.py` before `render.py`.

## Files

| File | What |
|---|---|
| `out/seixo_tampa.*` / `out/seixo_fundo.*` | Seixo top shell / bottom plate (STEP + STL) |
| `out/madeira_corpo.*` / `out/madeira_fundo.*` | oak body / thin bottom cover |
| `out/insert.*` | black connector insert for the left face (USB + headphones) |
| `out/plate.step`, `out/plate.dxf` | 1.5 mm switch plate, MX 14 × 14 holes on the 16.5 mm hex grid |
| `out/keycap_{natural,sharp,cf}.stl` | the three caps (C/F has the raised diagonal chequer) |
| `out/keycap_test_4.stl` | four caps on sprues, laid out like four neighbouring buttons, for the fit test on real switches |
| `out/switches.stl` | stand-in switches, used by the renders only |

**Coordinates.** The code works in SPEC coordinates: x to the right, y
towards the player, z up. That system is left-handed, so a model built
directly in it comes out mirrored in any CAD program. The exported files
are therefore mirrored back: `y_file = 100 − y_spec`. In the files x points
right, y points away from the player and z points up, which puts the
interface on the player's left. Keycaps are exported centred on their own
axis.

## Parameters (top of `case.py`)

- **Keyboard**
  - `P` (19.05) — button pitch.
  - `D_BTN` (15) / `D_SKIRT` (17) — button and skirt diameters.
  - `O_KEYS` — x of the first key column.
  - `ROW_Y` — y of each row.
  - `keys()` — puts the 44 notes on rows using the SPEC 2 rules.
- **Opening**
  - `CLR_SIDE` (15) / `CLR_FB` (7.5) — side and front/back clearances.
  - `SIDE_ANGLE` (30°) — angle of the opening's sides.
  - `R_OPEN_CORNER` (6) — corner radius.
  - The lateral fillets are concentric with the end buttons.
  - `CHAMFER_W` (4) / `CHAMFER_DROP` (2) — the rounded edge. A vertical land under it brings the lid down to the plate.
- **Box**
  - `BOX_OFF` (10.3) — the box is the opening grown by this amount.
  - `R_LEFT` (16) — radius of the two left corners.
  - `TRANS_TOP_OFF` (10.3) — sets the top edge of the slope (see FIT_CHECK §5 on the SPEC's "+20.3").
  - `Z_DECK` (15.7) — deck height.
  - `Z_IF_BACK` / `Z_IF_FRONT` (33 / 28) — interface top height, back and front.
- **Stack-up**
  - These match the current board.
  - `Z_PCB_TOP` = 7.7, plate top `Z_PLATE_TOP` = 12.7 (5 mm, MX), `Z_KEY_TOP` = 26.5.
  - So the lid round the keys is `LID_T` = 3 mm thick and rests on the plate's edge.
- **Interface**
  - `SCREEN_ZONE` / `SCREEN_MODE` (`"recess"` for a sticker or engraving, `"window"` for a real screen, `"none"`).
  - `VOLUME_XY`, `SELECT_XY`, `LED_XY`.
  - `GRILLE` (polygon), `GRILLE_D` / `GRILLE_PITCH`.
  - `GRILLE_KEEP` — drops holes that would land on the slope.
- **Connectors**
  - `USB_YZ`, `JACK_YZ`, `INSERT`.
  - `USB_PLUG_CUT` / `JACK_HOLE_D` (CHECK against the panel parts bought).
  - `INSERT_WALL` — the Madeira wall is thinned to this round the insert.
- **Versions**: `VERSIONS = {"seixo": {wall 2.5, top 2.5}, "madeira": {wall 4, top 3}}`.
- **Fixings**
  - `screw_points()` — M2.5 bosses from the bottom up into the top, notched out of the plate.
  - `pillar_points()` — board supports on the bottom plate, at the centres of key triangles, 11 mm from every sensor.

`keycap.py` has the switch numbers. They are MX nominal values and must be
checked against the Gateron KS-20. The skirt height is calculated, not
picked: the round skirt must clear the square top housing's corners at full
travel.

Values marked **CHECK** in the code are the SPEC's *conferir* items, plus a
few part dimensions (panel connectors, screen thickness, speaker depth)
that need the real part.
