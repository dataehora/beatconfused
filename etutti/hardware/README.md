# eTuttino — PCB design (Hall-effect, velocity-sensitive)

A 34-key chromatic button-accordion controller (C-griff, G3–G5).

- **Keys:** Gateron magnetic (Hall-effect) switches, MX-compatible.
- **Sensing:** a TI DRV5056A3 linear Hall sensor under every key, so the
  firmware knows how far down each key is, and from how fast it went
  down, the note's velocity.
- **Brain:** a Teensy 4.0 with the PJRC Audio Adaptor Board Rev D stacked
  on it.

The firmware is in [`../firmware`](../firmware), the web page is
[beatconfused.com/etutti](https://beatconfused.com/etutti/), and
step-by-step **assembly and user manuals** (en/pt/es) are at
[beatconfused.com/etutti/manuais](https://beatconfused.com/etutti/manuais/).

![PCB preview](build/etuttino_pcb_preview.svg)

## Ordering (ready to upload)

Everything a PCB service needs is generated, routed and checked (KiCad DRC:
0 errors, 0 warnings, 0 unconnected; firmware cross-check 34/34):

| File | Upload it as |
| --- | --- |
| [`fab/etuttino_gerbers.zip`](fab/etuttino_gerbers.zip) | **the PCB**: Gerbers + drill files. 2 layers, FR-4, **1.2 mm** |
| [`fab/etuttino_bom.csv`](fab/etuttino_bom.csv) + [`fab/etuttino_cpl_bottom.csv`](fab/etuttino_cpl_bottom.csv) | **assembly** (JLCPCB PCBA, *Bottom Side*): every SMD part is on the back |
| [`fab/etuttino_plate_gerbers.zip`](fab/etuttino_plate_gerbers.zip) | **the switch plate**: a copper-less 1.6 mm FR-4 board with the 14 mm cutouts |

There are two routes, both written up in the manuals:

- **A, factory-soldered:** order the PCB with JLCPCB's assembly service.
  It arrives with all 78 SMD parts soldered. You solder only the two
  Teensy sockets.
- **B, home-soldered:** order the bare PCB (plus an optional bottom-side
  stencil). Buy the parts from LCSC (same numbers as the BOM) and solder
  them yourself.

The BOM carries LCSC numbers for the JLCPCB basic parts. The two TI parts
(`DRV5056A3QDBZR`, `CD74HC4067M96`) are matched by manufacturer part
number in JLCPCB's BOM tool. Check every part's rotation in the placement
preview before paying.

## Why the sensors are on the back

The DRV5056 is unipolar: its output only rises for a **south** pole facing
its marked (top) side. Gateron's magnetic switches have the magnet's
**north** pole facing down. A sensor on the front, facing up, would read
nothing.

Mounted on the back, the sensor faces away from the switch, and the field
reaches it through the board from behind. The sensor reads that as
positive. A 1.2 mm board keeps the sensor as close to the magnet as that
allows.

Gateron rates the switch at about 10 mT at rest and 90 mT bottomed out,
measured on a 1.2 mm board. Through the board it is less, so the A3
variant (30 mV/mT at 3.3 V, about 80 mT before it saturates) leaves
headroom either way. The A4 also works.

With a switch whose magnet has south facing down, the sensors would have
to move to the front.

## Source files and regenerating

| File | What it is |
| --- | --- |
| [`generate.py`](generate.py) | single source of the geometry and of the sensor → multiplexer channel map (plain Python 3). Prints the `KEY_INPUT` table for the firmware |
| [`build_pcb.py`](build_pcb.py) | builds and **routes** the KiCad board, runs DRC, checks it against the firmware, exports everything in `fab/` |
| [`etuttino.pretty/`](etuttino.pretty) | footprint library: `Gateron_Magnetic_MX_1u` (two 1.75 mm peg holes, no centre post, no pins), origin at the switch centre |
| [`kicad/etuttino.kicad_pcb`](kicad/etuttino.kicad_pcb) | the routed board. Open it in KiCad's PCB Editor to look at or tweak it |
| [`kicad/etuttino_plate.kicad_pcb`](kicad/etuttino_plate.kicad_pcb) | the plate |
| `build/etuttino_pcb_preview.svg` | top view: keys (with their multiplexer/channel), sensors, multiplexers, Teensy zone, holes |
| `build/etuttino_keys.csv` | each key: switch, sensor, note-grid row/col, multiplexer, channel and pin, Teensy pin, note, X/Y (mm) |
| `build/etuttino_plate.dxf` | the plate as DXF, for laser cutting aluminium instead of FR4 |

After changing the layout in `generate.py`, rebuild everything (about two
minutes; the router is pure Python):

```bash
python generate.py
"C:/Program Files/KiCad/10.0/bin/python.exe" build_pcb.py
```

`build_pcb.py` exits with an error in three cases:

- DRC finds a problem;
- anything is left unconnected;
- a key's sensor doesn't reach the multiplexer channel and Teensy pin the
  firmware's `KEY_INPUT` / `MUX_COM_PINS` / `MUX_SEL_PINS` say.

If the channel map changed, paste the table `generate.py` prints into the
sketch.

## Layout

Chromatic accordion, C-griff:

- Each key along a row is a **minor third (3 semitones)** above the previous one.
- Rows are **staggered by half a key**, so a diagonal step to the next row
  is **one semitone**.
- Row 4 repeats row 1, with F♯3 added in front.
- **Row 1 is nearest the player**, at the bottom (front edge) of the board,
  and row 4 is at the top, behind it.
- The same switches also play **B-griff** (the mirror image: rows 1 and 3
  swap). The web page's C/B-griff switch tells the firmware which note
  table to use (CC 24). The PCB does not change.

| Row | Keys | Notes |
| --- | --- | --- |
| 1 | 8 | A3 C4 D♯4 F♯4 A4 C5 D♯5 F♯5 |
| 2 | 9 | G3 A♯3 C♯4 E4 G4 A♯4 C♯5 E5 G5 |
| 3 | 8 | G♯3 B3 D4 F4 G♯4 B4 D5 F5 |
| 4 | 9 | F♯3 A3 C4 D♯4 F♯4 A4 C5 D♯5 F♯5 |

Keys sit on the standard MX pitch of 19.05 mm. Rows 2 and 4 start half a
key further left than rows 1 and 3. The key area is 9 × 4 keys
(171.45 × 76.2 mm). The PCB is 183.45 × 132.2 mm.

## Electrical

**Per key (back side):**

- a DRV5056A3 (SOT-23) straight under the switch centre;
- its 100 nF decoupling capacitor just above it;
- a 3.3 V bus above each key row and a GND bus below it (0.4 mm);
- the sensor output drops to a via and is routed to its multiplexer.

**Multiplexers:** three CD74HC4067 (SOIC-24) in the strip behind the keys.

- U41 serves the left third of the keyboard, U42 the middle, U43 the
  right (see `build/etuttino_keys.csv` for each key's channel).
- Their address lines S0–S3 are shared.
- Enable is tied to GND.

| Net | Teensy pin |
| --- | --- |
| SEL0–SEL3 (multiplexer address S0–S3) | 0, 1, 2, 3 |
| COM0 (U41 output) | 14 (A0) |
| COM1 (U42 output) | 15 (A1) |
| COM2 (U43 output) | 16 (A2) |
| VIN (USB 5 V) → regulator | VIN |
| GND | GND (both sockets) |

**Power:** 34 sensors draw about 200 mA, more than the Teensy's own 3.3 V
pin should give. An AMS1117-3.3 (SOT-223, on the back between the Teensy
socket rows) makes a separate 3.3 V rail from VIN for the sensors and
multiplexers. It has 10 µF in and 22 µF out. The sensor outputs never
exceed this rail, and the Teensy's ADC pins tolerate 3.3 V.

**Pins kept clear of:**

- 7, 8, 18–21, 23: the Audio Board Rev D audio and I²C;
- 10–13: its SD card;
- 6: its optional memory chip;
- 15 is the Audio Board's *optional* volume pot, unpopulated on a stock
  board, so COM1 can use it. If you ever fit the pot, move COM1.

Pins 17 and 22 (A3, A8) are still free, for example for a future
expression pedal or bellows sensor.

**Routing:** two layers.

- Per-key wiring, power buses and trunks (3.3 V on the back and GND on the
  front, down the right edge) are laid deterministically.
- Everything else is routed by a small grid router in `build_pcb.py`:
  A* on a 0.254 mm grid aligned to the Teensy pins, both layers, vias,
  keeping KiCad's clearances. Sensor outputs are routed first, furthest
  from their multiplexer first.
- KiCad's DRC then checks the result independently.

## Teensy + Audio Board mounting

- The stack sits in the strip behind the keys, long axis horizontal, **USB
  pointing at the right edge** (silkscreen "USB >").
- It plugs into **two 1×14 female sockets** (2.54 mm pitch, 15.24 mm apart)
  on the front of the board.
- The Teensy (male pins down) plugs into stacking headers on the Audio
  Board, whose long legs plug into the eTuttino sockets.
- Before ordering a case, hold your real stack against the preview and
  check where the headphone jack ends up. Then cut the case openings for
  both the USB and the jack.

## Bill of materials

| Qty | Part | Notes |
| --- | --- | --- |
| 34 | Gateron KS-20 magnetic switch (or another Gateron magnetic switch, north pole down) | plate-mounted, **not soldered**: no pins, two plastic pegs |
| 34 | DRV5056A3QDBZR, SOT-23 | back side, under each switch (A4 also works) |
| 37 | 100 nF 0805 | one per sensor + one per multiplexer |
| 3 | CD74HC4067M96, SOIC-24 | back side |
| 1 | AMS1117-3.3, SOT-223 | back side |
| 1 + 1 | 10 µF, 22 µF 0805 | regulator input / output |
| 34 | 1u MX keycap, **round** | round MX-stem keycaps (sold as "round" or "typewriter" keycaps) give the accordion-button look of the web page. **19 light** (naturals) + **15 dark** (sharps) |
| 1 | Teensy 4.0 (+ 2 × 1×14 male headers) | |
| 1 | PJRC Audio Adaptor Board **Rev D** (+ 2 × 1×14 stacking headers) | |
| 2 | 1×14 female socket, 2.54 mm | on the eTuttino PCB |
| 1 | switch plate | 1.6 mm FR4 from `fab/etuttino_plate_gerbers.zip` (same fab as the PCB), or 1.5 mm aluminium from `build/etuttino_plate.dxf` (183.45 × 88.2 mm, 14 mm cutouts) |
| 8 + 16 | M2 × 3.5 mm standoff + M2 × 4 mm screws | plate ↔ PCB (the standard 3.5 mm MX gap under a 1.5 mm plate); the board must sit right against the switch bottoms |
| 1 | case | 3D-printed or CNC aluminium, tray mount on the M2 holes |

## Assembly

See the manuals at
[beatconfused.com/etutti/manuais](https://beatconfused.com/etutti/manuais/)
(source: [`../manuais/index.html`](../manuais/index.html)). The short
version:

1. Back side SMD: multiplexers (pin 1!), regulator, its two capacitors,
   sensors, 100 nF capacitors. Route A skips this step.
2. Teensy sockets on the front, soldered from the back.
3. Teensy + Audio Board stack in the sockets, USB to the right. Flash
   `firmware/etutti_synth` (USB Type: MIDI).
4. On the web page, turn on **Key test** and sweep a small magnet over each
   key position from the top. Every ring should fill.
5. Switches into the plate. Plate onto the PCB on 3.5 mm standoffs.
   Keycaps.
6. Replug the USB (rest is measured at start-up), click **Calibrate keys**,
   and press every key to the bottom once.
