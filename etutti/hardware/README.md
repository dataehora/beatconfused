# eTuttino — PCB design

A 34-key chromatic button-accordion controller (C-griff, G3–G5) built from
Cherry MX-compatible switches on a custom PCB, read by a Teensy 4.0 with
the PJRC Audio Adaptor Board Rev D stacked on it. The firmware is in
[`../firmware`](../firmware) and the web page is
[beatconfused.com/etutti](https://beatconfused.com/etutti/).

![PCB preview](build/etuttino_pcb_preview.svg)

All geometry comes from [`generate.py`](generate.py), which you run with plain
Python 3 and no extra packages. Change the layout there and re-run it. It
regenerates everything in `build/`:

| File | What it is |
| --- | --- |
| `build/etuttino_pcb_preview.svg` | top view: outline, keys, matrix cells, Teensy zone, holes |
| `build/etuttino_keys.csv` | each switch: reference, matrix row/col, Teensy pins, note, X/Y (mm) |
| `build/etuttino_plate.dxf` | switch plate for laser cutting / CNC (mm, DXF R12) |
| `build/kicad_place_etuttino.py` | KiCad script: places every footprint and assigns all nets |

## Layout

Chromatic accordion, C-griff:

- Each key along a row is a **minor third (3 semitones)** above the previous one.
- Rows are **staggered by half a key**, so a diagonal step to the next row
  is **one semitone**.
- Row 4 repeats row 1, with F♯3 added in front.

| Row | Keys | Notes |
| --- | --- | --- |
| 1 | 8 | A3 C4 D♯4 F♯4 A4 C5 D♯5 F♯5 |
| 2 | 9 | G3 A♯3 C♯4 E4 G4 A♯4 C♯5 E5 G5 |
| 3 | 8 | G♯3 B3 D4 F4 G♯4 B4 D5 F5 |
| 4 | 9 | F♯3 A3 C4 D♯4 F♯4 A4 C5 D♯5 F♯5 |

Keys sit on the standard MX pitch of 19.05 mm. Rows 2 and 4 start half a
key further left than rows 1 and 3. The key area is 9 × 4 keys
(171.45 × 76.2 mm).

## Electrical

**Key matrix: 4 rows × 9 columns.** Each physical row is one matrix row,
and each half-key position along the rows is one column. Only 34 of the 36
cells are used.

- Each switch has a 1N4148W diode in series. The anode goes to the switch
  and the cathode to the row (QMK calls this "COL2ROW").
- The firmware drives one row LOW at a time and reads the columns through
  pull-ups. The diodes allow any number of keys to be held at once without
  ghost notes.

| Net | Teensy pin |   | Net | Teensy pin |
| --- | --- | --- | --- | --- |
| ROW0 | 0 | | COL0 | 4 |
| ROW1 | 1 | | COL1 | 5 |
| ROW2 | 2 | | COL2 | 6 |
| ROW3 | 3 | | COL3 | 9 |
| | | | COL4 | 14 |
| | | | COL5 | 15 |
| | | | COL6 | 16 |
| | | | COL7 | 17 |
| | | | COL8 | 22 |

Pins the matrix stays clear of:

- **7, 8, 18, 19, 20, 21, 23:** the Audio Board Rev D audio and I²C
  connections.
- **10–13:** the Audio Board's SD card slot, kept free for future sample
  playback.
- **6** (optional memory chip) and **15** (optional volume pot) are both
  unpopulated on a stock Audio Board, so the matrix can use them. If you
  ever fit either part, move that column to another pin.

**Teensy + Audio Board mounting.**

- The Teensy 4.0 sits on top of the Audio Board, joined by **long-pin
  stacking headers**. The headers pass through the Audio Board and plug
  into **two 1×14 female sockets** (2.54 mm pitch, 15.24 mm apart) on the
  eTuttino PCB.
- The stack lies with its long axis horizontal in the strip behind the
  keys, **USB pointing at the right edge**.
- Before ordering the case, hold your real board against the preview and
  check where its headphone jack ends up. Then cut the case openings for
  both the USB and the jack.
- Only the matrix pins and GND go to the PCB. Power reaches the Audio
  Board through the stacking headers.

## Bill of materials

| Qty | Part | Notes |
| --- | --- | --- |
| 34 | MX-compatible switch, 3- or 5-pin | linear or tactile, your choice |
| 34 | Kailh MX hot-swap socket (CPG151101S11) | soldered on the back |
| 34 | 1N4148W diode, SOD-123 | back side, next to each socket |
| 34 | 1u MX keycap | uniform profile (DSA / XDA) suits a staggered grid. **19 light** (naturals) + **15 dark** (sharps), like accordion buttons |
| 1 | Teensy 4.0 | |
| 1 | PJRC Audio Adaptor Board **Rev D** | |
| 2 | 1×14 long-pin stacking header | Teensy → through Audio Board |
| 2 | 1×14 female socket, 2.54 mm | on the eTuttino PCB |
| 1 | switch plate, 1.5 mm | aluminium, FR4 or POM, from `etuttino_plate.dxf` (183.45 × 88.2 mm, 14 mm cutouts) |
| 10 | M2 screw + standoff | through the M2 holes (2.2 mm) |
| 1 | case | 3D-printed or CNC aluminium, tray mount on the M2 holes |

## Building the PCB in KiCad

1. Install [KiCad 8](https://www.kicad.org/). It ships with every footprint
   used here: `SW_Hotswap_Kailh_MX_1.00u`, `D_SOD-123`,
   `PinSocket_1x14_P2.54mm_Vertical` and `MountingHole_2.2mm_M2`.
2. Create a new project and open the **PCB Editor**.
3. Open **Tools › Scripting Console** and run:
   ```python
   exec(open(r"C:\path\to\etutti\hardware\build\kicad_place_etuttino.py").read())
   ```
   All switches, diodes, sockets, holes and the board outline are placed,
   with every connection shown as a ratsnest.
4. Route the board, either by hand or with the Freerouting plugin
   (**Plugin and Content Manager**). Two layers are plenty. A GND pour on
   both sides is a good finish.
5. Run **DRC**, then **File › Fabrication Outputs** (Gerbers + drill files).
6. Order from JLCPCB, PCBWay or similar: 2 layers, 1.6 mm, any colour.
   The board is 183.45 × 132.2 mm.

The placement script **has not been run in this repo's environment** (no
KiCad here). If KiCad reports an error, send the message and it will be
fixed in `generate.py`.

## Assembly

1. Solder the 34 diodes. Watch the polarity: the cathode band faces the row
   net, as marked on the footprint.
2. Solder the 34 hot-swap sockets on the back.
3. Solder the two 1×14 female sockets on the top.
4. Solder the stacking headers through the Audio Board and the Teensy.
   Check the pin-to-pin alignment of both boards first.
5. Mount the plate on standoffs, snap the switches through the plate into
   the sockets, then add the keycaps.
6. Flash `firmware/etutti_synth`. Every key should sound on the Audio
   Board's headphone output and light up on the web page.
