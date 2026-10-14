# eTuttino — PCB design (Hall-effect, velocity-sensitive)

A 44-key chromatic button-accordion controller (C-griff, G3–E6).

- **Keys:** Gateron magnetic (Hall-effect) switches, MX-compatible.
- **Sensing:** a TI DRV5056A3 linear Hall sensor under every key, so the
  firmware knows how far down each key is, and from how fast it went
  down, the note's velocity.
- **Brain:** a Teensy 4.0 with the PJRC Audio Adaptor Board Rev D stacked
  on it.

The firmware is in [`../firmware`](../firmware), the web page is
[beatconfused.com/etutti](https://beatconfused.com/etutti/), and the case
(Seixo / Madeira, SPEC v9; shape frozen since v7) is in [`case/`](case/).

> **Board v0.7 (this one) is made for the SPEC v7–v9 case.** The keys sit
> on the case's hexagonal grid (18.5 mm pitch), and the board takes the
> case's inner outline. The assembly and user manuals in
> [`../manuais`](../manuais/) describe this board, the case and the
> controls board; their pictures come from
> [`manual3d/`](manual3d/) (Blender). Nothing has been built
> yet: only the firmware has run on a real Teensy + Audio Board.

![PCB preview](build/etuttino_pcb_preview.svg)

## Ordering (ready to upload)

Generated, routed and checked: KiCad DRC 0 errors, 0 warnings,
0 unconnected; firmware cross-check 44/44.

| File | Upload it as |
| --- | --- |
| [`fab/etuttino_gerbers.zip`](fab/etuttino_gerbers.zip) | **the PCB**: Gerbers + drill files. 2 layers, FR-4, **1.2 mm**, shaped outline (328 × 97 mm bounding box) |
| [`fab/etuttino_bom.csv`](fab/etuttino_bom.csv) + [`fab/etuttino_cpl_bottom.csv`](fab/etuttino_cpl_bottom.csv) | **assembly** (JLCPCB PCBA, *Bottom Side*): every SMD part is on the back |
| [`fab/etuttino_plate_gerbers.zip`](fab/etuttino_plate_gerbers.zip) | **the switch plate**: a copper-less **1.6 mm** FR-4 board with the 14 mm cutouts, cut to the case's plate outline (the case is drawn for 1.6 since SPEC v8) |
| [`fab/etuttino_controls_gerbers.zip`](fab/etuttino_controls_gerbers.zip) | **the controls board**: 2 layers, FR-4 1.6 mm, 41.5 × 25.5 mm, all through-hole (see below) |
| [`case/out/`](case/out/) | **the case** (STEP + STL) and the button caps; see [`case/README.md`](case/README.md) |

The BOM has LCSC numbers for the JLCPCB basic parts. Match the two TI parts
(`DRV5056A3QDBZR`, `CD74HC4067M96`) by manufacturer part number in
JLCPCB's BOM tool. Check every part's rotation in the placement preview
before paying.

## Why the sensors are on the back

The DRV5056 is unipolar: its output only rises when a **south** pole faces
its marked (top) side. Gateron's magnetic switches have the magnet's
**north** pole facing down, so a sensor on the front, facing up, would read
nothing.

On the back, the sensor faces away from the switch. The field reaches it
through the board from behind, and the sensor reads that as positive. A
1.2 mm board keeps the sensor as close to the magnet as that allows.

The A3 variant (30 mV/mT at 3.3 V, about 80 mT before saturation) leaves
headroom against Gateron's ~10 mT at rest and ~90 mT bottomed out. The A4
also works.

## Source files and regenerating

| File | What it is |
| --- | --- |
| [`case/pcb_envelope.py`](case/pcb_envelope.py) → `case/out/pcb_envelope.json` | the room the case leaves for the board: outline (notched round the case's screw bosses), plate outline, bottom-plate pillars, height levels, key centres, the stack's and J3's places. Run with the CadQuery venv (see `case/README.md`) |
| [`generate.py`](generate.py) | reads that envelope. Single source of the key layout and of the sensor → multiplexer map (plain Python 3). Prints the `KEY_INPUT` table for the firmware |
| [`build_pcb.py`](build_pcb.py) | builds and **routes** the KiCad board inside that outline, runs DRC, checks it against the firmware, exports everything in `fab/` |
| [`controls_pcb.py`](controls_pcb.py) | the controls board: places, routes (the same router), DRCs and exports it |
| [`mechanics.py`](mechanics.py) | how far the board bends under a key press on the case's pillars (KiCad's Python, numpy) |
| [`manual3d/`](manual3d/) | the assembly manual's pictures: photo-like renders and numbered line drawings of every step, made in Blender from the case STLs, both KiCad boards (`kicad-cli` GLB) and a library of datasheet-sized parts (`parts.py`). `build.py` runs it all; the visual standard and the balloon numbers are in [`manual3d/STYLE.md`](manual3d/STYLE.md) |
| [`etuttino.pretty/`](etuttino.pretty) | footprint library: `Gateron_Magnetic_MX_1u` (two 1.75 mm peg holes, no centre post, no pins), origin at the switch centre |
| [`kicad/etuttino.kicad_pcb`](kicad/etuttino.kicad_pcb), [`kicad/etuttino_plate.kicad_pcb`](kicad/etuttino_plate.kicad_pcb) | the routed board and the plate |
| `build/etuttino_pcb_preview.svg`, `build/etuttino_keys.csv`, `build/etuttino_plate.dxf` | preview; each key's switch, sensor, multiplexer channel, Teensy pin, note and X/Y; the plate as DXF (for aluminium) |

After a case change, rebuild in this order:

```bash
C:/Users/julia/.venvs/cadquery/Scripts/python.exe case/case.py
C:/Users/julia/.venvs/cadquery/Scripts/python.exe case/pcb_envelope.py
python generate.py
"C:/Program Files/KiCad/10.0/bin/python.exe" build_pcb.py
"C:/Program Files/KiCad/10.0/bin/python.exe" mechanics.py
```

Each routing attempt takes about four minutes. The router is greedy: if
a net can't be routed, the script starts again with that net first, up to
20 times. `DEFAULT_ROUTE_FIRST` keeps the order that worked
(`OUT_U41,OUT_U42,GND,LED_R,LED_G_DRV,OUT_U34` for v0.6 and v0.7).

`build_pcb.py` exits with an error if any of these happens:

- DRC finds a problem.
- Anything is left unconnected.
- A part on the back sits over one of the bottom plate's pillars.
- A key doesn't reach the multiplexer channel and Teensy pin that the
  firmware's tables give.

It writes the routed channels into the sketch's `KEY_INPUT`.

## Layout

Chromatic accordion, C-griff, on a **hexagonal grid**: every button is
**18.5 mm** from its six neighbours, and the rows are 18.5 × cos 30° =
**16.02 mm** apart.

- Each key along a row is a **minor third (3 semitones)** above the
  previous one. A diagonal step to the next row is **one semitone**.
- Row 4 repeats row 1's notes from A3 to C6, on row 2's columns.
- **Row 1 is nearest the player.** It is at the front edge, which is the
  bottom of KiCad's top view.
- The same switches also play **B-griff**: the web page's C/B-griff
  switch sends CC 24, and the firmware swaps rows 1 and 3. The PCB does
  not change.

| Row | Keys | Notes | y (mm) |
| --- | --- | --- | --- |
| 1 | 11 | A3 C4 D♯4 F♯4 A4 C5 D♯5 F♯5 A5 C6 D♯6 | 74.03 |
| 2 | 12 | G3 A♯3 C♯4 E4 G4 A♯4 C♯5 E5 G5 A♯5 C♯6 E6 | 58.01 |
| 3 | 11 | G♯3 B3 D4 F4 G♯4 B4 D5 F5 G♯5 B5 D6 | 41.99 |
| 4 | 10 | A3 C4 D♯4 F♯4 A4 C5 D♯5 F♯5 A5 C6 | 25.97 |

**Coordinates** are the case SPEC's. x is measured from the case's left
face, y towards the player. That is KiCad's top view as it stands.

**The board** is the case's inner cavity less 0.5 mm, notched round the
nine screw columns. It fits both the Seixo (2.5 mm walls) and the Madeira
(4 mm). On the left it runs under the interface area, where the Teensy +
Audio Board stack sits in the back corner:

- USB faces the case's left face, where a short cable goes to the panel
  socket.
- The VIN row is at the back.
- The stack is ~13 mm tall in the eTuttino and 10 mm or less in the
  eTuttiChorus.
- The Audio Board sits ~3 mm above the PCB on its header legs.
- These positions come from `case/fit_check.py`.

**Held by the case:**

- Under the keys, the lid presses the plate's edge, the plate presses
  the switches, and the switches' bottom housings press the board.
- Under the interface, two M2 screws come up from below. They go through
  the bottom plate's pillars at (30; 60) and (12; 70) and through the
  board's holes H1 and H2, with a nut on top. These two pillars are
  Ø6, with a counterbore for the head. The router keeps copper 3.5 mm
  away from both holes.
- The board rests on **64 pillars** of the bottom plate, one at the
  centre of every triangle of three neighbouring keys (10.7 mm from each
  sensor). The case has 3 more pillars under the interface.
- Under a firm 3 N press the board sags **0.044 mm** at worst (E6, row 2)
  and 0.009 mm on average. Check with `mechanics.py`.
- No part on the back may sit over a pillar. `build_pcb.py` checks this.

## Electrical

**Per key (back side):**

- A DRV5056A3 (SOT-23) straight under the switch centre.
- Its 100 nF capacitor just behind it.
- A 3.3 V bus behind each key row and a GND bus in front of it (0.4 mm).
- The sensor output drops to a via and is routed to its multiplexer.

**Multiplexers:** three CD74HC4067 (SOIC-24), all on the back.

- U51 sits in front of the interface, left of rows 1 and 2. It serves row 1
  and the left end of row 2.
- U52 and U53 lie sideways in the strip behind row 4 and serve the rest,
  split left and right.
- The router picks each key's channel; see `build/etuttino_keys.csv`.
- The address lines are shared, and Enable is tied to GND.

| Net | Teensy pin |
| --- | --- |
| SEL0–SEL3 (multiplexer address S0–S3) | 0, 1, 2, 3 |
| COM0 / COM1 / COM2 (U51 / U52 / U53 output) | 14 (A0) / 15 (A1) / 16 (A2) |
| VIN (USB 5 V) → regulator | VIN |
| GND | GND (both rows) |
| LED_R_DRV / LED_G_DRV → 330 Ω (R1 / R2) → J3 | 4 (red), 5 (green) |
| POT → J3 | 22 (A8) |
| ENC_A / ENC_B / ENC_SW → J3 | 17 / 9 / 6 |

**J3, the controls board.** A JST PH 2.0 mm 8-pin vertical header, in front
of the Audio Board, under the interface lid. A short 1:1 cable goes up
to the controls board.

| Pin | Net |
| --- | --- |
| 1 | VCC 3.3 V |
| 2 | GND |
| 3 | POT |
| 4 | ENC_A |
| 5 | ENC_B |
| 6 | ENC_SW |
| 7 | LED_R |
| 8 | LED_G |

The firmware reads the pot as the volume and the encoder as the
instrument selector (see `../firmware/README.md`). With no controls board
plugged in, the pot input is ignored. Pin 6 is the Audio Board's optional
memory-chip select, so leave that chip unfitted.

## Controls board

`controls_pcb.py` → `kicad/etuttino_controls.kicad_pcb` and
`fab/etuttino_controls_gerbers.zip`. KiCad DRC 0 / 0 / 0. In case
coordinates it spans x 14.5–56, y 35.5–61. It hangs under the interface lid
on two posts of the case, with M2 screws through H1 and H2 from below. Its
top faces the lid:

| Ref | Part | Where |
| --- | --- | --- |
| RV1 | Alps RK09K vertical pot, 10 k linear, 6 mm shaft L = 15 | shaft at (20; 45): volume |
| SW1 | Alps EC11E encoder with push switch, L = 15 | shaft at (37; 45): instrument |
| D1 | 3 mm red/green LED, common cathode | (52; 45), on a spacer up to the lid's hole (Seixo) or just under the light pipe (Madeira); `case/FIT_CHECK.md` gives the spacer length |
| J1 | JST PH B8B-PH-K vertical, on the back, facing down | the cable drops straight to the main board's J3, pin for pin |

The encoder's common and one switch leg go to GND. The Teensy's pull-ups
do the rest. The LED's 330 Ω resistors are on the main board.

**Power LED.** A 3 mm red/green bicolour LED (common cathode) on the
controls board, under the lid's LED hole, or the Madeira's light pipe:

- orange while the keys are read at power-up;
- green while playing;
- blinking red on an error.

**Power.** 44 sensors draw about 260 mA, more than the Teensy's own 3.3 V
pin should give. An AMS1117-3.3 (U60, SOT-223) makes a separate 3.3 V rail
from VIN for the sensors and the multiplexers:

- it sits on the back between the Teensy pin rows;
- it has 10 µF in and 22 µF out.

**Pins kept clear of:**

- 7, 8, 18–21, 23: the Audio Board's audio and I²C;
- 10–13: its SD card;
- 15 is its *optional* volume pot, which is not fitted on a stock board, so
  COM1 can use it.

**Routing:** two layers.

- Per-key wiring and the row buses are laid deterministically.
- Everything else goes through a small A* grid router in `build_pcb.py`:
  0.254 mm grid aligned to the Teensy pins, both layers, vias, KiCad's
  clearances, 0.5 mm from the board's outline.
- KiCad's DRC then checks the result independently.

## Teensy + Audio Board mounting

- Two rows of 14 holes (2.54 mm pitch, 15.24 mm apart), with the 0–12 row
  at the front and the VIN–13 row at the back. The silkscreen marks
  "GND"/"0", "VIN"/"23" and "< USB".
- Two 1×14 extra-long male headers (≈ 20–25 mm pins) join all three
  boards: the Teensy is soldered straight onto the Audio Board, the
  header's plastic as the only spacer, and the long legs go on down
  through these holes with the Audio Board ~3 mm above the PCB, soldered
  and trimmed on the back.
- Stack height, from under the Audio Board to the top of the Teensy's
  USB: the case was checked with 13 mm and has room for 16.9 mm (Seixo) /
  16.4 mm (Madeira); the eTuttiChorus needs 10 mm or less, to clear the
  screen.
- USB goes to the panel socket through a short cable with a 90° micro-USB
  plug. The panel headphone jack is wired to the Audio Board's headphone
  pads.

## Bill of materials (main board)

| Qty | Part | Notes |
| --- | --- | --- |
| 44 | Gateron KS-20 magnetic switch (north pole down) | plate-mounted, **not soldered**: no pins, two plastic pegs |
| 44 | DRV5056A3QDBZR, SOT-23 | back, under each switch |
| 47 | 100 nF 0805 | one per sensor + one per multiplexer |
| 3 | CD74HC4067M96, SOIC-24 | back |
| 1 | AMS1117-3.3, SOT-223 | back |
| 1 + 1 | 10 µF, 22 µF 0805 | regulator input / output |
| 2 | 330 Ω 0805 | LED resistors R1, R2 (back) |
| 1 | JST PH 8-pin vertical header (B8B-PH-K-S) + a 1:1 PH cable, ~60 mm | J3, to the controls board |
| 2 + 2 | M2 × 10 mm screw + M2 nut | through the bottom plate's two thick pillars and H1 / H2 |
| 1 | Teensy 4.0 + PJRC Audio Adaptor Board **Rev D** | + 2 × 1×14 extra-long male headers |
| 1 | switch plate | 1.6 mm FR-4 from `fab/etuttino_plate_gerbers.zip`, or 1.5 mm aluminium from `build/etuttino_plate.dxf` |
| 44 | button caps | 3D-printed from `case/out/keycap_*.stl` (26 natural / C-F, 18 sharp) |

**Controls board:**

| Qty | Part |
| --- | --- |
| 1 | Alps RK09K1130 (or equivalent) vertical pot, 10 k linear, 15 mm shaft |
| 1 | Alps EC11E with push switch, **15 pulses / 15 detents**, 15 mm shaft (`ENC_STEPS_PER_DETENT` = 4 in the firmware; 2 for a 30-detent one) |
| 1 | 3 mm LED, red/green, common cathode, + a ≈ 4 mm LED spacer (Seixo); the Madeira has a 3 mm light pipe in the lid instead |
| 1 | JST PH B8B-PH-K-S |
| 2 | M2 × 5 mm self-tapping screws, into the lid's posts |
| 2 | knobs, Ø9, for 6 mm shafts |

The case is listed in [`case/README.md`](case/README.md).
