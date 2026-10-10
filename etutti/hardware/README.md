# eTuttino — PCB design

A 34-key chromatic button-accordion controller (C-griff, G3–G5) built from
Cherry MX-compatible switches on a custom PCB, read by a Teensy 4.0 with
the PJRC Audio Adaptor Board Rev D stacked on it. The firmware is in
[`../firmware`](../firmware) and the web page is
[beatconfused.com/etutti](https://beatconfused.com/etutti/).

![PCB preview](build/etuttino_pcb_preview.svg)

## Ordering (ready to upload)

Everything a PCB service needs is already generated, routed and checked
(KiCad DRC: 0 errors, 0 warnings, 0 unconnected):

| File | Upload it as |
| --- | --- |
| [`fab/etuttino_gerbers.zip`](fab/etuttino_gerbers.zip) | **the PCB**: Gerbers + drill files |
| [`fab/etuttino_plate_gerbers.zip`](fab/etuttino_plate_gerbers.zip) | **the switch plate**: a copper-less FR4 board with the 14 mm cutouts |
| [`fab/etuttino_bom.csv`](fab/etuttino_bom.csv) + [`fab/etuttino_cpl_bottom.csv`](fab/etuttino_cpl_bottom.csv) | *optional*: have the fab solder the diodes and sockets |

**JLCPCB** (PCBWay and others work the same way):

1. Go to jlcpcb.com, click **Order now** and upload `etuttino_gerbers.zip`.
   The site reads the size (183.45 × 132.2 mm) and shows a preview. Check
   that the keys and the Teensy sockets look right.
2. Settings: **2 layers**, **FR-4**, **1.6 mm**, any colour, **HASL
   lead-free**, quantity 5 (the minimum). Leave the rest at the defaults.
   Under "Remove order number" you can pick "Specify a location"; there is
   no marked spot, so they will put it somewhere unobtrusive.
3. Place a second order with `etuttino_plate_gerbers.zip`, same settings
   (1.6 mm FR-4). The plate has no copper, so "No" for any copper-related
   option. Black or white looks good under keycaps.
4. **Optional assembly.** Enable *PCB Assembly*, choose **Bottom side**,
   and upload the BOM and CPL files. Match the parts in their library:
   Kailh MX hot-swap socket **CPG151101S11** and diode **1N4148W
   (SOD-123)**. Then check the rotation of every part in their placement
   preview before paying. Without assembly you solder 68 small SMD parts
   yourself, which is easy with a fine tip.

The switches, keycaps, Teensy, Audio Board and headers are bought
separately (see the BOM below). They are not on the fab's order.

## Source files and regenerating

| File | What it is |
| --- | --- |
| [`generate.py`](generate.py) | single source of the geometry (plain Python 3, no packages) |
| [`build_pcb.py`](build_pcb.py) | builds and routes the KiCad board, runs DRC, exports everything in `fab/` |
| [`etuttino.pretty/`](etuttino.pretty) | footprint library: Kailh MX hot-swap socket, origin at the switch centre |
| [`kicad/etuttino.kicad_pcb`](kicad/etuttino.kicad_pcb) | the routed board. Open it in KiCad's PCB Editor to look at or tweak it |
| [`kicad/etuttino_plate.kicad_pcb`](kicad/etuttino_plate.kicad_pcb) | the plate |
| `build/etuttino_pcb_preview.svg` | top view: keys, matrix cells, Teensy zone, holes |
| `build/etuttino_keys.csv` | each switch: reference, matrix row/col, Teensy pins, note, X/Y (mm) |
| `build/etuttino_plate.dxf` | the plate as DXF, for laser cutting aluminium instead of FR4 |

After changing the layout in `generate.py`, rebuild everything:

```bash
python generate.py
"C:/Program Files/KiCad/10.0/bin/python.exe" build_pcb.py
```

`build_pcb.py` exits with an error if DRC finds a problem or anything is
left unconnected.

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
| 1 | switch plate | 1.6 mm FR4 from `fab/etuttino_plate_gerbers.zip` (same fab as the PCB), or 1.5 mm aluminium from `build/etuttino_plate.dxf` (183.45 × 88.2 mm, 14 mm cutouts) |
| 10 | M2 screw + standoff | through the M2 holes (2.2 mm) |
| 1 | case | 3D-printed or CNC aluminium, tray mount on the M2 holes |

## Assembly

1. Solder the 34 diodes. Watch the polarity: the cathode band faces the row
   net, as marked on the footprint.
2. Solder the 34 hot-swap sockets on the back.
3. Solder the two 1×14 female sockets on the top.
   The silkscreen marks **GND** and **0** (J1) and **VIN** and **23** (J2):
   the Teensy goes in with its USB towards the "USB >" mark.
4. Solder the stacking headers through the Audio Board and the Teensy.
   Check the pin-to-pin alignment of both boards first.
5. Mount the plate on standoffs, snap the switches through the plate into
   the sockets, then add the keycaps.
6. Flash `firmware/etutti_synth`. Every key should sound on the Audio
   Board's headphone output and light up on the web page.
