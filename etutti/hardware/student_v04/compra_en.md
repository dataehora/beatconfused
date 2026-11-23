# Student V4 (32 keys) · what to tick and fill in at each shop (English translation of fab/COMPRA.md, R13V4)

23 Nov 2026. **Nothing has been bought, quoted as a purchase or uploaded.** The project rule still holds: nothing is bought before the prototype is closed. This text gets the order ready to copy and check. Conventions: **seen** = price seen on a shop page or in JLCPCB's parts library (date given, no shipping, no tax); **est.** = our own calculation, not quoted; **(check)** = no measurement or page checked now. Currency: US$ (GBP is an assumption of 1.30 US$ per £). The shop pages were not opened in this round (only JLCPCB's library, by curl, and the pages of 15 to 22 Nov): **check stock, price and the UK shop at the time.**

Files that go to JLCPCB (section 10 of this page has them under these names):
- main board: `placa_principal_gerbers.zip`, `placa_principal_bom.csv`, `placa_principal_cpl.csv`
- R8 rulers (panel of 2): `regua_R8_painel2_gerbers.zip`, `regua_R8_painel2_bom.csv`, `regua_R8_painel2_cpl.csv`
- support sheets: `LEIAME_COTACAO_principal.md`, `LEIAME_COTACAO_regua.md`, `MODELOS_3D.md`

## 1. JLCPCB · main board (order 1)

Screens in the order of the order page (Instant Quote). Value = what to choose.

| # | Field | Value | Note |
|---|---|---|---|
| 1 | Upload | `placa_principal_gerbers.zip` | the page should read 75.05 x 95.1 mm, 4 layers |
| 2 | Base Material | FR-4 | |
| 3 | Layers | 4 | |
| 4 | Dimensions | read from the Gerber | check 75.05 x 95.1 |
| 5 | PCB Qty | 5 | minimum; the 3 bare ones are spare |
| 6 | Product Type / Delivery Format | Industrial/Consumer, **Single PCB** | |
| 7 | PCB Thickness | **1.2 mm** | |
| 8 | Specify Stackup | **Yes → JLC04121H-7628** | real thickness 1.12 mm ±10 %, accepted by J |
| 9 | Material Type | FR4 **TG135** | |
| 10 | Surface Finish | **ENIG** | J's decision (fine pitch: M.2, USB-C, 0.4 mm QFN); Au 1 U" is the default |
| 11 | Outer / Inner Copper | **1 oz / 0.5 oz** | |
| 12 | Specify Layer Sequence | No | |
| 13 | Via Covering | **Plugged** | J's decision |
| 14 | Min via hole size/diameter | **0.3 mm / (0.4/0.45 mm)** | the board uses 0.5/0.3 vias: ok |
| 15 | Board Outline Tolerance | ±0.2 mm (Regular) | |
| 16 | Impedance Control | **no** | the USB pair (7.4 mm) is a calculation only |
| 17 | Confirm Production file | No | |
| 18 | Mark on PCB | **Remove Mark** | |
| 19 | Electrical Test | **Flying Probe Fully Test** | |
| 20 | Other advanced options (colour, silkscreen, gold edge, ...) | defaults / No | green colour |
| 21 | **PCB Assembly** | on | |
| 22 | PCBA Type | **Economic** | if refused (75 x 95 mm is within the economic limits), use Standard and note it: the price changes |
| 23 | Assembly Side | **Bottom Side** | all 78 parts are on the bottom, 0 on top |
| 24 | PCBA Qty | **2** | minimum; one for the instrument, one spare (the second costs only parts, ~US$ 21) |
| 25 | Tooling holes | **Added by JLCPCB** | the board has no rail |
| 26 | Confirm Parts Placement | **Yes** on the first order, **if free** | JLCPCB sends the placement for J to approve before soldering; this makes the pin 1 and mouth check final |
| 27 | Stencil / Fixture storage | No | |
| 28 | Parts Selection | **By Customer (Self-Service)** | |
| 29 | BOM / CPL | `placa_principal_bom.csv` / `placa_principal_cpl.csv` | |

**On the BOM screen:** the 32 lines should show **found and in stock** (14 Extended types); C310 is **not** in the BOM (do not assemble). **Lowest stock (check):** M.2 C48985906 (553), SGTL5000 C2651833 (1 150), BQ24074 C54313 (2 837), PJ-327A C49284723 (3 259), SM04B C160404 (4 511). Any line without stock: stop and say so.
**On the placement (preview) screen:** use the checklist further down against the preview pictures. Through-hole parts: **none** in the BOM (the 2 encoders and the speaker are done at home).
**Price seen (R13V4, our estimate; J's quote was ~105 before the SH swap):** ~US$ 112 (113.4-138.4 with the assumed PCB); minimum 5 bare boards, 2 assembled.
The main board table was checked against J's: it matches (4 layers, 1.2 mm, JLC04121H-7628, ENIG, 1 oz/0.5 oz, Plugged 0.3/0.4/0.45, Flying Probe, Economic, Bottom, Qty 2, tooling by JLCPCB). **Nothing to correct.**

## 2. JLCPCB · R8 ruler in a panel of 2 (order 2, a separate order: one variant per order)

Same table as the main board, with these differences:

| Field | Value | Note |
|---|---|---|
| Upload | `regua_R8_painel2_gerbers.zip` | panel 161.6 x 44 mm |
| Layers | **2** | F.Cu and B.Cu only |
| Delivery Format | **Panel by Customer: 1 column x 2 rows**, no V-cut, no extra edge rails | the panel brings 5 mm rails, 3 mm tabs with D0.5 mouse bites and D2.0 tooling holes |
| PCB Thickness | 1.2 mm | |
| Specify Stackup | No | |
| Surface Finish | **HASL lead-free** | ENIG is an option if JLCPCB complains about the flatness of the X2SON and DHVQFN (0.5 mm pads): quote both |
| Copper | 1 oz | |
| Via Covering / vias | defaults; min. 0.3 mm | |
| PCB Qty | **5 panels** | = 10 bare rulers |
| PCBA Qty | **2 panels** | = **4 assembled rulers = 32 sensors** |
| Assembly Side | Bottom | |
| Tooling holes | **Added by Customer** | the panel has them (D2.0 + 3 fiducials); if JLCPCB will not take the panel: Added by JLCPCB |
| Confirm Parts Placement | Yes (if free) | |
| BOM | `regua_R8_painel2_bom.csv` (Complete File) | 5 lines, 3 Extended: TMAG5253BA3 C22401868, 74HC595BQ C730243, SM06B JST C160405 |
| CPL | `regua_R8_painel2_cpl.csv` | designators `U1-1`, `J1-1`... |

**Minimums:** 5 bare panels, **2 assembled**: the 32-key instrument uses exactly the 2 (4 R8); 3 bare panels are left over (6 R8 without parts).
**Main risk:** the panel's 44 mm side is smaller than the 70 mm of the standard assembly: JLCPCB may refuse, add a rail (cost not stated) or ask for the 4-panel (`R8_painel4`, 161.6 x 76 mm, 8 assembled rulers, ~US$ 71-102) or "Panel by JLCPCB" with 1 strip.
**Price (est., `custo_r11.json`, R13V4):** **47.3-64.2** (4 rulers); J's quote was ~70 before the SH swap (now ~73).
**Other variants** (only the lines that change): **R8E** (first ruler of 48/64/80 keys): same Gerber, `R8E_painel2/bom.csv` and `cpl.csv` (with J2 and R1), separate order; **R4 / R4E:** `R4_painel5/` (different Gerbers: panel 87.6 x 92 mm, 5 strips), 5 bare panels, 2 assembled = 10 rulers; outside the 32 keys.

## 3. Items outside JLCPCB

The UK shops named are the ones I take as likely; **none was opened now (check)**. Prices: seen on the date given, or est.

| # | Item | Qty (32 keys) | Shop (UK first, if any) / code | Options to choose | Price |
|---|---|---:|---|---|---|
| 1 | **SparkFun MicroMod Teensy** (DEV-16402; RT1062, 16 MB; **no PSRAM**) | 1 (+0) | DigiKey UK, Mouser UK, Pimoroni/The Pi Hut (check stock), SparkFun | with the **M2.5 x 3 tape/screw** (does it come with the module? check; otherwise buy the M2.5 screw and the 2.5 mm H101 spacer) | £18.69 ex VAT at DigiKey UK (seen 15 Nov) = ~US$ 24 |
| 2 | **Adafruit 326 OLED** (0.96", SSD1306, STEMMA QT) | 1 | Adafruit (US$ 17.50, 1-9); in the UK Pimoroni or The Pi Hut usually resell Adafruit (check) | **address 0x3D from the factory** (the firmware tries 0x3D and 0x3C); do not choose the model without STEMMA QT | US$ 17.50 (seen 22 Nov) |
| 3 | **50 mm Qwiic / STEMMA QT cable** (Adafruit 4210 or SparkFun PRT-14426) | 1 (+1 spare) | Adafruit, SparkFun, Pimoroni | 4-way SH at both ends, **pin to pin**, 50 mm (the shortest); not the one with a loose end | ~US$ 1 (seen 22 Nov) |
| 4 | **6-way SH cables** `A06SR06SR30K51B` (JST, 50.8 mm, pin to pin) | **4 + 2 spare = 6** | DigiKey UK, Mouser UK, Farnell UK (JST code) | **50.8 mm length (not the 300 mm)**; **straight**, not crossed; check **before buying** that the code is the 50 mm one (the design assumes 45.8-50.8 mm of free wire, **not measured**) | US$ 1.2-1.4 each (seen 22 Nov, JLCPCB/LCSC library); 4 = ~5.7 |
| 5 | **LiPo 503450 battery** 3.7 V ~1 000 mAh, **3 wires with NTC**, **3-pin JST PH 2.0 mm** plug | 1 | eBay UK, Amazon UK, Pimoroni | **3 wires** (the third = 10 kΩ NTC); the plug's wire order varies: **measure 10 kΩ** between black and the third and check pin 1 = + (J202) **before connecting** | £5-8 (seen 15 Nov) |
| 6 | **Dayton CE28MB-8 speaker** (Ø28 x 4.5 mm, 8 Ω) | 1 | Parts Express (US); UK: check (Farnell/CPC/Cool Components usually do not stock it) | 8 Ω; ask for fs (resonance) if offered | ~US$ 7-10 (est., check) |
| 7 | **Gateron KS-20 Magnetic Orange keys** (KS-20TO10B050NW-Y64, 38 gf) | **32** (1 pack of 35) | Gateron's shop, Chosfox (UK: check) | **Orange**; pack of 35 | US$ 24.50-26.60 (seen 15 Nov) |
| 8 | Long springs (optional, for more weight) | 1 pack of 65 g and 1 of 80 g | UK mechanical-keyboard shops (Candykeys, Cherry Keebs: check) | 20-22 mm, ~65 g and ~80 g; **not tested** that they fit the KS-20 | a few pounds (seen 15 Nov) |
| 9 | **Key caps** (one design for all rows) | 32 | printed, same service as the case (MJF/resin) | files `case/out/capa*.stl` (colour: white for naturals, black for sharps, dots on C and F) | included in the case (est.) |
| 10 | **Alps EC11E18244AU encoders** (C202365, 20 mm shaft, 18 pulses/36 detents) | 2 (+1) | LCSC (US$ 1.92 in a lot of 10, seen 16 Nov); Mouser/DigiKey UK (Alps Alpine EC11E18244AU) | **20 mm D shaft** (not the 25 mm EC11E18244A5); with click | ~US$ 2 each |
| 11 | **Knobs** (10 mm cap for a 6 mm D shaft) | 2 | printed (file `knob`) or a shop | shaft with flat | included in the case |
| 12 | **M2 through bolts** (rulers): 8, **2 of each length M2 x 10, 12, 14, 16** (rows 1 to 4) | 8 (+4) | UK online hardware (Accu, Bolt Base, eBay) | **A2 stainless**, pan head, **non-magnetic** (Hall sensors); always M2 x 10 / 12 / 14 / 16 | pennies (est. US$ 0.03-0.05) |
| 13 | **M2 nuts** | 6 normal + **2 thin (1.2 mm) for row 4** | same | A2, non-magnetic | US$ 0.015 |
| 14 | **M2 thread-forming screws (PT 2.0)**: **lid, 15 x M2 x 14** (H1..H4, 5 inner posts, 6 wall posts); **OLED, 4 x M2 x 4** | 19 (+10 spare) | same | pan head, stainless or steel; **re-using a thread-forming screw has a limit (5-10 times, estimate)** | US$ 0.04 |
| 15 | **Silicone feet** (Ø8 x 1.0, stuck on directly, no recess) | **6** | Amazon/eBay UK | **hardness 70A or more** (too soft lets the board flex) | ~£3 (est.) |
| 16 | **MicroMod at H101**: **nylon M2.5 x 8** screw + **nylon M2.5 nut** + **2.5 mm nylon spacer** | **2 screws, 2 nuts, 2 spacers** (1 + 1 spare) | hardware (Accu, Bolt Base, eBay UK) | the screw goes through **board 1.2 + spacer 2.5 + module ~1.0 = 4.7 mm** and closes on the nut (~2 mm): 4.7 + 2 = 6.7, so **M2.5 x 8** (x 6 does not close); **check the module's real thickness** and that the tip (1.3 mm past the nut) does not touch the base: request to the design | pennies (est.) |
| 17 | **MJF PA12 case** (lid, base, and the printed items 9 and 11) | 1 set | JLC3DP, PCBWay, Craftcloud (UK: via Craftcloud/Shapeways; check) | **MJF PA12 material**, colour **grey/black** (dyeable, paint later), finish **dyed/smoothed if offered**, **no** vapour smoothing on the threads (check with the service), **minimum walls 0.58 mm** in row 4's hexagonal pockets; STL files from `student_v04/case/out/` (lid, base, caps, knob); **do not send the rulers' STL** | ~US$ 46-51 (design est., MJF; not quoted) |
| 18 | Tools | — | — | soldering iron (speaker wires, encoders), multimeter (NTC), small Phillips screwdriver, **torque driver** if any | — |
| 19 | **1.6 mm FR-4 ruler grid** (the keyboard grid: bare board, no assembly, no parts) | **1 panel** (5 is JLCPCB's minimum, the rest are spares) | **JLCPCB**, same cart as the main board (one shipping) | upload `student_v04_grade_regua_painel_gerbers.zip` (this folder, `fab/`; from `pcb/grade_fab.py`); **2 layers, 1.6 mm, FR-4 TG135, lead-free HASL, matte black mask, 5 panels, no assembly**; **check how many grids fit in a panel** (see `student_v04_grade_contorno32_gerbers.zip` for the whole 32-key grid) | US$ 8-15 (**est.**: small 2-layer board + engineering; not quoted) |

## 4. Totals for the 32-key prototype (US$, no shipping, no tax)

| Group | Range (US$) | Type |
|---|---:|---|
| Main board (PCB + assembly, 2 assembled) | 113.4-138.4 | **est.** (4-layer ENIG PCB is an assumption; J's quote was ~105 before the original SH, +7.0) |
| 4 x R8 rulers (panel of 2) | 47.3-64.2 | **est.** (J's quote was ~70, +3.3) |
| 1.6 mm FR-4 ruler grid (JLCPCB, item 19) | 8-15 | **est.** |
| SH cables (6) + Qwiic cable | 8-10 | seen 22 Nov |
| Adafruit 326 OLED | 17.5 | seen 22 Nov |
| Hardware (M2 through bolts and nuts, PT, nylon M2.5, feet; items 12-16) | 6-12 | **est.** |
| MJF case (includes caps, knobs and acoustic box) | 46-51 | **est.** (not quoted) |
| Keys, module, battery, speaker, encoders, springs, USB-C cable (MicroMod ~24 + KS-20 24.5-26.6 + springs 3-8 + battery 6-10 + speaker 7-10 + encoders 4-6 + USB-C 3-8) | 71.5-92.6 | mixed: seen 15 Nov (module, keys, battery) and **est.** |
| **Total (sum of the lines)** | **318-401** | R13V4; the sum of the lines is the official number |

The low end uses quantity prices and the minimum PCB; the high end, the one-piece price and the assumed US$ 39.50 PCB.

## 5. What J does, in order
1. Upload the main board (section 1) up to the **placement preview**; compare with the preview pictures and the checklist; send the screenshot to Chat/Code. Do not pay yet.
2. Upload the R8 (section 2); see whether JLCPCB takes the 44 mm panel; compare with the R8 preview.
3. Quote the MJF case (STL) at 2 or 3 services.
4. Only after the prototype closes: the items of section 3.
