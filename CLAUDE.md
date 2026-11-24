# BeatConfused.com — project notes for Claude

Static site, no build step: plain HTML/CSS/vanilla JS with the Web Audio
API. Hosted on GitHub Pages (`CNAME` → beatconfused.com). Repo:
`dataehora/beatconfused`. See [README.md](README.md) for the user-facing
tool descriptions and repo layout — this file is developer/agent context
that doesn't belong there.

## Architecture

- `index.html` / `styles.css` — home page (tool cards, decorative SVG
  icons built by inline `<script>`, no shared code).
- `metronome/` — fully independent, no shared code, has its own opt-in
  cache-busting scheme (see Caching section below).
- `tuner/`, `strobetuner/` (Octave Strobe Tuner), `multistrobe/`
  (Chromatic Strobe Tuner) — the three "tuner-family" pages. Each has its
  own `index.html` / `script.js` / `styles.css`, but share:
  - `shared/tuner-common.js` + `shared/tuner-common.css` — Reference
    Pitch, Tuning Standard/temperament math, Spectrum Analyser, Input
    Monitor, **Test Tone** (`createTestTone`, `updateTestToneVariance`,
    `frequencyToNote`), the Octave Frequency Table
    (`buildOctaveFrequencyTable` / `updateOctaveFrequencyTableRings` /
    `resetOctaveFrequencyTable`), collapsible-panel wiring, transport
    shortcuts (Space/arrows).
  - `shared/strobe-disc.js` — the reusable strobe-disc engine used by both
    `/strobetuner/` (one large hero disc) and `/multistrobe/` (twelve
    small ones): `buildStageGeometry` (shared 180°/thin-bezel proportions,
    scale to any case radius), `ringRadiusForOctave` (fixed 9-slot radius
    math — every disc reserves radius space for octaves 0-8 regardless of
    which octaves a given note actually has, so the visual scale never
    changes between notes), `buildDisc`, `addBezelDecoration` (ticks,
    ♭/♯ glyphs, vignette, glass highlight), Goertzel ring analysis
    (`analyzeDisc`/`analyzeRing`), `renderDisc`.
  - A future look/behavior change to either shared file applies to all
    three pages automatically — that's the intended design, lean on it
    rather than re-forking page-local copies.
- `luthier/` (Luthier Tuning) — a live spectrogram: decaying live
  spectrum + peak-hold background curve on a log-frequency axis, a 12 s
  waterfall underneath, full-range/audible toggle, peak-hold mode
  On/Temporary/Off (Temporary = per-bin 2 s hold, then falls at the live
  curve's Decay rate). Loads
  `shared/tuner-common.css` (page chrome, power switch, style-toggle,
  panels) and `shared/tuner-common.js` (only for `setMicStatusFactory`,
  `MIC_MESSAGES`, `wireCollapsibles`, `noteNameForMidi`) — none of the
  pitch/temperament/strobe machinery. Its own `script.js`/`styles.css`
  carry their own `?v=` (independent of the tuner pages' value). No Test
  Tone; for in-browser verification, monkeypatch
  `navigator.mediaDevices.getUserMedia` to return a
  `MediaStreamAudioDestinationNode` stream of synthesized partials.
- `etutti/` (eTutti) — **work in progress, deliberately unlisted**: no
  home-page card, not in `sitemap.xml`, `noindex` meta (the user asked
  for no home button while it's being built). **Since Oct 2026
  `/etutti/` is the family landing page** (`etutti/index.html` +
  `family.css`: four cards, only the eTuttino Pocket opens, the other
  three are disabled "in development"; the top-view SVGs are written
  inline between `BEGIN/END svg:` markers by `etutti/landing_svgs.py`
  from `pocket.json` + `pocket/layout.py`), `/etutti/pocket/` is the
  provisional Pocket page, and **the MIDI app described below lives at
  `/etutti/etuttino/`** (`etutti/etuttino/{index.html,script.js,
  websynth.js,styles.css}`; reachable by direct URL and from the
  manuals/models pages, not from the landing page). Read
  `etutti/script.js` below as `etutti/etuttino/script.js`. Two models: **eTuttino**
  (the one being built — Teensy 4.0 + Audio Board Rev D, 44 **Gateron
  magnetic (Hall-effect) keys with velocity** — see "Hall-effect keys"
  below — in a chromatic-accordion **C-griff** layout (PR #77): row 1
  A3..D#6 (11), row 2 G3..E6 (12, half a key left), row 3 G#3..D6 (11),
  row 4 A3..C6 (10, on row 2's columns: A3 above row 2's A#3, C6 above
  C#6). **Never name the commercial accordion this layout was first
  compared to** — the user asked for that reference to be removed
  everywhere) and **eTutti** (full version, the page only
  shows "in development"). Web MIDI (`navigator.requestMIDIAccess`) to the
  Teensy running `etutti/firmware/etutti_synth/` (8-voice synth, USB name
  "eTutti" via `name.c`, reads the 44 Hall sensors through 3 analog
  multiplexers and plays/sends notes with velocity).
  **Row 1 is nearest the player (bottom), row 4 at the top** — on the
  page and on the PCB. Round on-screen buttons. C-griff / B-griff switch
  (B = mirror: rows 1 and 3 swapped; firmware gets CC 24 so the real keys
  follow). Optional computer-keyboard input (toggle, remembered in
  localStorage), by `KeyboardEvent.code`: row 1 = Z..Period,Slash,IntlRo
  (ABNT2 ; and /), row 2 = A..L,Semicolon,Quote,Backslash (G6 has no
  key), row 3 = W..P,BracketLeft,BracketRight, row 4 = Digit3..Digit8
  (the user is on ABNT2; legends come from navigator.keyboard
  .getLayoutMap() when available, else ABNT2 labels). Arrows =
  octave/velocity, Esc panic. Sound: accordion = additive free-reed synthesis, four reeds per
  note (16' cassotto, 8' M1 open, 8' M2 cassotto, 4' piccolo) switched by a
  round accordion-register widget (CC 26 bit mask) plus named registers;
  "classic" = dry MM (default, what Reset restores), "jazz" = same reeds
  ~6 cents wet (CC 27). Piano/bass/guitar = Teensy Audio Library wavetable
  samples (`piano`, `nylonstrgtr`; the library has NO bass sample — bass
  is the guitar 2 octaves down; a real one would need converting from a
  SoundFont). "Synth" instrument (CC 25 = 4·16) reuses 3 of each voice's
  oscillators: wave (sine/triangle/BANDLIMIT saw/square), level, detune,
  octave + ADSR. Light reverb (CC 91). Tone filter is a **biquad** —
  `AudioFilterStateVariable` near its max frequency went unstable and
  turned piano/guitar into full-scale noise; don't bring the SVF back. The user found the earlier
  saw/square synth "metallic" (aliasing) — don't go back to raw
  WAVEFORM_SAWTOOTH/SQUARE. `PRESETS` in script.js; custom saved presets
  are a planned follow-up. To measure CPU on the real Teensy, build a
  throwaway copy with usb=serialmidi that self-plays chords and prints
  AudioProcessorUsageMax(), read it from the COM port. The note layout lives in THREE places
  that must agree: `FIRST_NOTE`/`ROWS` in `etutti/script.js`,
  `FIRST_NOTE`/`FIRST_COL`/`KEY_INPUT` in the sketch, `ROWS`/`MUXES` in
  `etutti/hardware/generate.py` (geometry + which mux each key uses) —
  since #77 the router picks each sensor's mux **channel** (any free one
  of its mux; per-pad placeholder nets `FREE<m>_<ch>` keep pad
  clearances) and `build_pcb.py` **writes `KEY_INPUT` into the sketch**
  and `build/etuttino_keys.csv`, then checks the board's nets against the
  sketch and fails on a mismatch. Recompile/flash after a board rebuild. The CC map lives in
  both `etutti/script.js` (`CC`) and the sketch — change both together.
  - **Hall-effect keys** (PR #75): DRV5056A3 under each Gateron KS-20
    switch, on the **back** of a 1.2 mm board — the DRV5056 only reads a
    SOUTH pole facing its marked side and Gateron magnets are NORTH-down,
    so a front-mounted sensor would read nothing; don't "fix" it back to
    the front. 3 × CD74HC4067 (S0-S3 = pins 0-3, COM = 14/15/16 with
    INPUT_PULLDOWN so a bare Teensy has no stray notes — verified on the
    real Teensy: 0 keys present, 0 notes), AMS1117-3.3 rail from VIN.
    Firmware: cube-root (1/d³ dipole) travel model between per-key rest
    (measured at boot) and learnt bottom (EEPROM), note on 45 %, off 30 %,
    velocity = log-mapped time 12 %→45 % (1 ms = 127, 80 ms = 1). CC 9
    velocity curve, CC 14 recalibrate, CC 15 key-test stream (Poly AT on
    ch 16, data1 = key index in grid order). Full 34-key scan measured at
    240 µs (44 keys: ~310 µs expected). Page: "eTuttino keys" panel (curve, Calibrate, Key test rings).
    Not yet tested with a real board — tune VEL thresholds/FAST_MS/SLOW_MS
    by feel once one exists.
  - **Browser sound** (`etutti/websynth.js`, PR #76): "Listen in this
    browser" switch, OFF by default every visit (the user asked that it
    must be switched on before anything reaches the speakers). It takes
    the same CCs as the firmware via `sendCC()` and plays the page's own
    notes (on-screen + computer keyboard, not the Teensy's): accordion
    reeds = same PeriodicWave spectra as `buildReedTable`, synth = 3
    band-limited oscillators + ADSR, piano/guitar/bass = decaying-partial
    approximations (labelled as such on the page). Verified by tapping
    the output with an AnalyserNode in the browser pane.
  - **Board shape (PR #78, "ergonomic" layout)**: 267 × 97.2 mm — the
    4 key rows + 6 mm margins + a 15 mm strip at the BACK (`MARGIN_BACK`,
    for U52 and the long lines to the far mux). The user asked for USB and jack on
    the LEFT for ergonomics (cables away from the playing right hand, high
    notes clear, LED in sight): the Teensy + Audio Board stack sits in the
    free back-LEFT corner (`STACK_ZONE`, rows 3-4 start after row 2), the
    USB-up view turned 90° anticlockwise, so the 0-12 row (J1) is the front
    one and VIN-13 (J2) the back one; the jack is beside the 0-12 row at the
    USB end (read off PJRC's pin diagram — unverified on a real board). The
    key grid is mirror-symmetric, so the layout is the #77 one mirrored:
    U51 in the front-left corner (`CORNER_X` = row 2's left edge; row 1 +
    left 5 of row 2, routed nearest-first), LED D1 just in front of the
    Audio Board under J1 pins 4/5 (down the left edge its lines walled U51
    in), U52 sideways (rot 90) in the back strip just right of the stack
    (left 12 keys; behind J2 its traces couldn't squeeze past the stack), U53 rot 0 in the back-right corner (right
    16; COM pin at the top so COM2 runs along the back strip, routed with
    the other COMs, not late), LDO U60 rot 180 between the pin rows, VIN pin towards J2. The
    Audio Board is soldered ~3 mm above the PCB on its stacking-header legs;
    with the Teensy's 2.5 mm male-header spacer the Teensy top is 17.2 mm,
    USB 19.8 mm (keycaps 18.8) — the case's pod covers it. **Power LED** D1 (#77): 3 mm red/green common-cathode
    THT on top in front of the Audio Board, pins 4 (red) / 5 (green) through R1/R2
    330 Ω on the back; firmware: orange while the keys are first read
    (≥ 0.6 s), green playing, red blinking if the codec or any key's
    sensor didn't answer (so a bare Teensy blinks red — no LED there
    anyway). Routing order:
    power buses → mux COM/SEL/power/LED → 44 sensor outputs → the far
    mux U53's COM/SEL (routed earlier they boxed row 4's sensors in); on a
    failure `build_pcb.py` re-runs itself with the failed net first
    (`ETUTTINO_ROUTE_FIRST`), up to 20 attempts (~4-15 min each). A net
    that fails even when first is a physical blockage: export
    `kicad/etuttino_failed.kicad_pcb` to SVG and look.
  - **Manual pictures** (PR #99): `etutti/hardware/manual3d/`, Blender 5.2
    (Steam install: `C:/Program Files (x86)/Steam/steamapps/common/Blender/
    blender.exe`; Cycles on the RTX 3060 via OptiX). `build.py` (CadQuery
    venv) runs: `kicad-cli pcb export glb` of both boards (pads, silkscreen,
    mask only: tracks/zones exported above the mask showed as bare copper;
    controls board with `--component-filter J1`) → `parts.py` (datasheet-
    sized Teensy, Audio Board, 2×14 extra-long headers + solder, Gateron,
    RK09K, EC11E, LED, knobs, PH plugs, panel parts, screws/nuts →
    `build/lib/<part>.<material>.stl` + `build/assembly.json`) →
    `render_blender.py` (SHOTS: `r_*` photo-like with transparent film +
    shadow catcher, `l_*` Freestyle line drawings with the step's new
    groups amber/heavy) → `annotate.py` (balloon numbers + arrows from the
    projected 3D anchors; numbers only so the images serve en/pt/es; the
    manual's "Parts list" table names them; numbering in `STYLE.md`).
    `build/` is gitignored. ~7 min for all shots; `--fast` for previews.
    Gotchas: STL import gives object scale 0.001 with mesh data in mm;
    KiCad's GLB mask material is semi-transparent (forced opaque and
    re-coloured); Blender auto-converts glTF to Z-up (x, -y_spec, z).
    `case/manual_render.py` (PyVista, #95) is gone.
  - **Old case (PR #78, removed in #89)**: a FreeCAD two-piece case. Purchase
    options given to the user then and still in the manual: JLC3DP, PCBWay,
    Craftcloud. The user is in London; manuals stay country-neutral (no
    import/customs talk).
  - **Models page** `/etutti/models/` (PR #94, unlisted/noindex, linked
    from the eTutti page): the SPEC v9 case. Written by
    `etutti/hardware/case/models_page.py` (texts en/pt/es live there);
    pictures + numbers (size, heights, case weight from the STL volume) by
    `case/models_render.py`. Sections: hero (Seixo iso), Seixo/Madeira side
    by side, numbered anatomy (call-outs projected from 3D points, legend
    per language), caps, the family as a table (eTutti = 48 keys, each row
    +1: F♯6/G6/F6/D♯6; eTuttiChorus = eTutti + screen, 28 mm speaker under
    the grille, battery, stack ≤ 10 mm; both "in development"), measures.
    The PR #80 concept generator (`concepts*.py`, 76 mm grip) is gone.
  - **New case, Seixo/Madeira (Oct 2026)**: `etutti/hardware/case/`.
    - Files: `SPEC.md` (the design spec, versioned, Portuguese),
      `canvas-v5/` (Claude Chat's reference drawings), `case.py`
      (CadQuery, all parameters at the top), `keycap.py`, `render.py`
      (PyVista), `fit_check.py` → `FIT_CHECK.md` (Portuguese).
    - Python env: `C:/Users/julia/.venvs/cadquery` (cadquery + pyvista,
      not in the repo).
    - **Workflow with Claude Chat:** Chat owns `SPEC.md` (v5, v6…, each
      with a "Mudanças desde a versão anterior" section). Code regenerates
      the model, runs the check, and updates `FIT_CHECK.md`, ending with
      "Perguntas para o design". Then commit, PR, merge. The user relays a
      one-line note between the two.
    - **SPEC v7 (PR #85) froze the shape.** Changes since v6 are
      listed below. The Madeira's LED is now a bought 3 mm light pipe
      in a Ø3.1 hole.
    - The room left for the main board is exported by
      `pcb_envelope.py` → `out/pcb_envelope.json`, which the PCB scripts
      read. It holds:
      - the outline (Madeira cavity − 0.5);
      - boss notches and fundo supports;
      - the plate edge;
      - height levels;
      - keys, stack, controls board and panel footprints.
    - Exterior finishing changes must not touch that interior.
    - Model state as of v6 (PR #84):
      - pitch **18.5** on the hex grid (rows 16.02 apart, Gateron KS-20
        housings 0.92 mm apart);
      - deck round the keys at z 17.4 (lid 4.7 mm on the plate);
      - cap skirts Ø16.5;
      - the ramp's front curve stops at 75° and runs straight into the
        face (90° is tangent to it, and OCC can't fillet that);
      - Madeira LED: hole + acrylic window (`madeira_led_janela`);
      - stack ~13 mm in the eTuttino, ≤ 10 mm in the Chorus.
    - Coordinates: the SPEC's frame (x right, y towards the player, z up)
      is LEFT-handed. Model in SPEC coordinates, mirror on export
      (`y_file = 100 - y_spec`).
    - OCC gotchas (each one bit in #82–#84):
      - The opening cutter is ONE ruled loft through stacked contours.
        A loft plus a separate prism, fused or cut in turn, left a
        film, came out empty, or split off a slab. The shell keeps only
        its largest solid after that cut.
      - Each ramp edge is one spline through densely, evenly paired
        points, with the same point count on both edges.
        - Sparse points on the straight parts made the spline bulge
          into the opening.
        - Exact lines + arcs made the fillets invalid.
      - The two R 5 ramp fillets are applied one after the other.
      - Check every export: ray-probe the opening and count open mesh
        edges (the render once hid a film over the keys).
    - **SPEC v8 (PR #88), done in PR #89:**
      - **Plate:** 1.6 mm FR-4 (`case.PLATE_T`). The plate's top is at
        12.8 and the key tops at 26.6.
      - **Board fixing:** two M2 screws from below through Ø6 pillars at
        (30; 60) and (12; 70), into board holes H1/H2. The router keeps
        3.5 mm of copper-free ring round them.
      - **Controls board:** `etutti/hardware/controls_pcb.py`, which
        reuses `build_pcb`'s router through module globals. Its geometry
        is `case.CONTROLS`, exported in the envelope. It hangs on two lid
        posts. Parts: RK09K rot 180, EC11E rot 270, LED, and a vertical
        JST on the back facing down, so its cable can't hit the Chorus
        speaker. DRC 0/0/0.
      - **Firmware knobs:** pot on 22 (ignored when no pot is detected
        via pull-up/pull-down at boot, verified on the real Teensy: the
        floating pin reads 400–680), encoder on 17/9 (ISR Gray table,
        `ENC_STEPS_PER_DETENT` 2), switch on 6. It sends CC 7 / CC 25
        back; the page doesn't follow them yet.
    - **Board v0.6 (PR #87) is built for this case** (v0.7 adds the M2 holes). The README of
      `etutti/hardware/` has the details.
      - `generate.py` reads `case/out/pcb_envelope.json`: keys, outline,
        pillars, stack spot. `ROWS`, the notes and the firmware
        semantics are unchanged.
      - The router keeps 0.5 mm from the outline polygon.
      - Placement:
        - U51 front-left of rows 1-2;
        - U52 and U53 rot 90 in the strip behind row 4;
        - the LED moved to the controls board: R1/R2 stay here, and J3
          (JST PH 8) carries VCC, GND, POT (22), ENC A/B/SW (17/9/6) and
          LED R/G.
      - `DEFAULT_ROUTE_FIRST = OUT_U41,OUT_U42,GND,LED_R,LED_G_DRV,OUT_U34`.
      - Result: DRC 0/0/0, firmware 44/44, KEY_INPUT rewritten in the
        sketch (it compiles; not flashed, since no such board exists
        yet).
      - The case's pillars: one per three-key triangle (64), 0.044 mm
        worst sag (`mechanics.py`). `build_pcb.py` fails if a back-side
        part sits on one.
      - Removed: the #78 FreeCAD case (`case.py`, `case_check.py`, its
        `fab/` STLs). `build_pcb.py --renders` only points to
        `manual3d/build.py` now.
    - Electronics in the interface: pot, encoder and LED go on a small
      board under the lid. Use a 90° micro-USB plug.
  - **Stiffness**: `etutti/hardware/mechanics.py` (KiCad python + numpy,
    no scipy) runs a grillage FE (4 mm mesh) per key on the case's pillars
    → `build/etuttino_supports.json`. The user asked that the board "not
    flex much": keep the worst key ≤ 0.05 mm at 3 N (v0.6: 0.044).
  - `etutti/manuais/` — assembly manual (board v0.7, Seixo/Madeira case,
    controls board; PR #95: before you start, route A JLCPCB PCBA bottom
    side, route B soldered at home, then 9 build steps in the brief's
    order) + user manual (PR #96: knobs, LED table, page, C/B-griff, care,
    troubleshooting), one `.lang-block` per language (en/pt/es) shown by
    `html[lang]`; hand-written HTML, noindex, linked from the eTutti page
    only. It says the design is ready to make and that only the firmware
    has run on real hardware. Keep it in step with hardware/firmware
    changes. Stack as written there: Teensy soldered straight on the Audio
    Board with extra-long headers (plastic = the only spacer, ~8–9 mm),
    legs on through the main board, Audio Board ~3 mm up; measure ≤ 16.9
    (Seixo) / 16.4 (Madeira). The headphone jack is wired to the Audio
    Board's own socket pins: its ground is virtual, never GND.
  - **Tooling available on this machine** (use it to verify, don't just
    write code blind): KiCad 10 at `C:/Program Files/KiCad/10.0/bin/`
    (its `python.exe` has `pcbnew`; `kicad-cli.exe` does DRC/Gerbers/
    renders) and the Arduino IDE's bundled
    `C:/Program Files/Arduino IDE/resources/app/lib/backend/resources/arduino-cli.exe`
    with Teensyduino 1.60 installed — compile with
    `arduino-cli compile --fqbn teensy:avr:teensy40:usb=midi etutti/firmware/etutti_synth`.
  - `etutti/hardware/build_pcb.py` (run with KiCad's python, ~2 min)
    places, **routes** (fixed per-key wiring + power buses/trunks, then
    its own A* grid router — 0.254 mm grid aligned to the Teensy pins, two
    layers, vias — for sensor outputs, mux address/COM and supplies; each
    net only ever joins its already-connected copper tree, or the next job
    can hook onto an island), DRCs and exports `fab/` (Gerbers zip,
    plate-as-FR4 Gerbers zip, JLCPCB BOM/CPL for bottom-side assembly,
    renders). It exits non-zero on any DRC error/unconnected or firmware
    mismatch. The switch footprint is our own
    `etuttino.pretty/Gateron_Magnetic_MX_1u` (two peg holes only).
  - The firmware's `#error` on missing `MIDI_INTERFACE` exists because the
    user hit "'usbMIDI' was not declared" with USB Type left on Serial. The
  MIDI monitor already logs what the Teensy sends back (hook for the
  user's planned custom hardware interface). See **eTutti handoff** below
  for the current state, verification recipes and next steps.
- `binfacevsfarage/` — standalone browser game, deliberately **not**
  linked from the studio nav, blocked in `robots.txt`, and absent from
  `sitemap.xml`. Leave it that way unless told otherwise.

- `shared/site-title.css` — the "beatconfused.com" wordmark link back to
  home (`<a class="site-title" href="/">`) that sits first inside
  `<main>` on every page except the home page itself (which has it as its
  own h1). Same colour in every link state by design. Loaded with its own
  `?v=` on all six pages (five tools + `404.html`).

### Hosting headers / 404 / SEO

- `404.html` (root) is served for unknown URLs by both GitHub Pages and
  Cloudflare Pages (without it, Cloudflare Pages falls back to serving
  `index.html` with a 200). It uses absolute paths only, since it can be
  served at any depth.
- `_headers` is Cloudflare Pages syntax (GitHub Pages ignores it).
  **Keep `microphone=(self)`** in its Permissions-Policy — `microphone=()`
  would block `getUserMedia` on all three tuners. Its CSP is
  `Report-Only`; the only third parties are GA4 (gtag.js) and Google
  Fonts. If a new third-party script/API is added, add it there.
- `og-image.png` (1200×630) is a screenshot of the home hero, shared by
  every page's `og:image`/`twitter:image`. Re-render it if the home icons
  change noticeably.
- The home page's `meta.description` i18n key is the short visible
  tagline; the `<meta>` tags use `meta.pageDescription` (140-160 chars).
  Keep `<lastmod>` in `sitemap.xml` current when a page's content changes.

### Section order convention (tuner-family pages)

All three pages follow the same order: Title → Toggle → Display →
"Input Monitor and Test Tone - Setting up your Microphone" (one merged
panel, collapsed by default) → Spectrum Analyser → "Tuning Standard and
Reference Pitch" (one merged panel) → Frequency Table. This is identical
on all three pages now — Test Tone lives inside the Input Monitor panel
everywhere, not as a separate block.

## ⚠️ Caching gotcha — read before editing shared files or any page script

GitHub Pages (behind Cloudflare) serves `.js`/`.css` with
`Cache-Control: public, max-age=14400, must-revalidate` (4 hours) and
**no version in the URL** by default. The HTML documents themselves are
`max-age=0, must-revalidate` (always revalidated), but each `<script>` /
`<link>` tag's own target is cached independently for up to 4 hours.

This caused two real, live production bugs in one session (see
[PR #52](https://github.com/dataehora/beatconfused/pull/52) and
[PR #53](https://github.com/dataehora/beatconfused/pull/53)): a browser
that had `shared/tuner-common.js` (or a page's own `script.js`) cached
from before a deploy kept using the stale copy — even on a "fresh" page
load — because the file's own cache window hadn't expired yet. A
function added in one file but called from a freshly-fetched sibling
file threw `TypeError: ... is not a function` (or silently resolved to
`undefined`), breaking the whole page's `<script>` from that line down.

**The fix in place**: every `<script src>` / `<link href>` for
`shared/tuner-common.js`, `shared/tuner-common.css`, `shared/strobe-disc.js`,
and each tuner page's own `script.js`/`styles.css` carries a
`?v=20260913` query string across `tuner/index.html`,
`strobetuner/index.html`, `multistrobe/index.html`.

**When you touch any of those files again**: bump the `?v=` value (a
`YYYYMMDD` string is fine) on *every* reference to that specific file,
across all pages that load it. Grep for the old value first:

```bash
grep -rn "v=20260913" --include="*.html" .
```

If you forget, the change will still work for brand-new visitors but can
silently break the page for anyone with a stale cached copy of just one
of the files, for up to 4 hours after deploy — exactly what happened
above. This is a manual, easy-to-forget step; a more permanent fix (a
build script that content-hashes filenames, or automating the version
bump) would remove the footgun entirely and is worth doing eventually.

Note `metronome/index.html` already has its own *different*,
**opt-in** versioning scheme (only kicks in if the page URL itself has a
`?__v=` param — see the `loadVersionedAssets` IIFE there). It predates
this session's fix and hasn't been touched or unified with it.

### Local dev server

`.claude/launch.json` runs `.claude/nocache_server.py` (not
`python -m http.server`) on port 5849 — a tiny wrapper that adds
`Cache-Control: no-store` to every response. Plain `http.server` sends no
caching headers at all, which let the *browser* heuristically cache
scripts for a surprisingly long time and made local edits appear not to
apply without a manual hard-refresh — this bit hard during development
this session. If local preview ever again seems to be running stale code
despite the file on disk being correct, suspect the browser's own cache
first (try a brand new tab, or bump the preview port) rather than the
code.

## eTuttino handoff (14 Oct 2026, PRs #81–#97) — start here

**Milestone reached:** the eTuttino is designed end to end and ready to
order, and the site and manuals describe it. Everything is merged on
`main`. Nothing has been built: only the firmware has run on the user's
Teensy + Audio Board.

- **Case** (`etutti/hardware/case/`, CadQuery): SPEC v9 (shape frozen since
  v7; v9 changed only the firmware and the page). Seixo (resin/MJF) and
  Madeira (oak, CNC, two setups), STEP/STL in `case/out/`; caps in three
  files + a 4-cap fit test; renders in `case/renders/`; `FIT_CHECK.md`
  (Portuguese) ends with the open questions.
- **Main board v0.7** (`generate.py` + `build_pcb.py`): 18.5 mm hex grid,
  outline from `case/out/pcb_envelope.json`, 3 muxes + LDO on the back,
  J3 to the controls board, 2 M2 holes. DRC 0/0/0, firmware 44/44.
  Gerbers/BOM/CPL in `fab/`; plate 1.6 mm FR-4.
- **Controls board** (`controls_pcb.py`): RK09K pot, EC11E encoder (15
  pulses / 15 detents), 3 mm R/G LED, vertical JST PH facing down.
- **Firmware:** pot = volume (CC 7 back), encoder = instrument (CC 25
  back), `ENC_STEPS_PER_DETENT = 4` (#93); click after turning = keep
  (EEPROM), click without turning = classic accordion. Flashed on the
  user's Teensy (enumerates as "eTutti"); the click count itself can only
  be checked with a real controls board.
- **Site** (#93–#96): `/etutti/` follows CC 7 / CC 25 without echoing them
  (`followKnob` in `script.js`; a CC 25 equal to the current instrument =
  the firmware's default sound); `/etutti/models/` and `etutti/manuais/`
  rebuilt (see Architecture above).
- **Process:** design iterations run through the protocol under "New
  case, Seixo/Madeira" above (Claude Chat edits `SPEC.md`; Code models,
  checks, answers in `FIT_CHECK.md`, commits, PRs, merges; the user relays
  a one-line note). The site/manuals brief that drove #93–#96 is
  `etutti/BRIEF-site-manuais.md`.

**Open questions for the design (v10), in `case/FIT_CHECK.md` §5:**

1. The Madeira's light pipe: with the LED straight on the controls board
   there is room for a ~4 mm pipe, not `LIGHT_PIPE_L` = 6 (CHECK). The
   manual says ~4 mm.
2. The low stack (Teensy soldered on the Audio Board, ~8–9 mm): confirm
   with the real parts.
3. Order the prototype?

**Verifying the pages:** the in-app browser pane works (preview_start
"static-site"); when the pane is hidden, screenshots come back stale or at
the wrong size, so check with `javascript_tool` instead (each
`.lang-block` via `BC_I18N.setLang`, `scrollWidth` at 375 px, elements
past `innerWidth`, `fetch` every `img`/download link). A fake
`navigator.requestMIDIAccess` whose input's `onmidimessage` you call by
hand tests the knob following.

**Tool gotcha:** in this environment Bash heredocs lose backslashes
(`'\n'` arrives as `'
'`), so Python edit scripts with escapes go
through the Write tool into the scratchpad.

## Sampled accordion reeds (14 Nov 2026)

The accordion can play recorded reeds instead of the synthesised tables. `reed_sampler.h`
(`ReedSampler`, one per voice, four ranks, Catmull-Rom, attack + loop) is in the sketch; the data
(`reed_samples.cpp/.h`, 1.3 MB) is **gitignored**: it is made from J's licensed Concert Accordion
library and must never be committed or published. Without those two files the sketch builds and
uses the old reed tables (`HAVE_REED_SAMPLES`).
- Tools in `etutti/firmware/tools/accordion_samples/` (CadQuery venv python, numpy + scipy):
  `make_capture_midi.py` → `capture_notes.mid` (keys 43..79 every 3 semitones; the library sounds
  its 8' reed an octave above the MIDI key and is silent above key 81); J exports one WAV per rank
  (L, M, M2, H) from Ableton into `capturas/` (gitignored; Ableton names them
  `<rank> 1-Engine Player.wav`, rename to `<rank>.wav`); `analyse.py` measures the notes;
  `build_samples.py` writes the sample data and `capturas/preview/*.wav`.
- Measured on the Teensy 4.0 (8 notes): 12 % CPU in MM, 20 % with all four ranks, 8 audio blocks.
  Flash: 1.44 MB used, 0.59 MB free. Ranks stored at 24 kHz (H at 32 kHz).
- The library's MM is almost dry (beat under 1 Hz); the tremolo is still CC 27 (`wetCents`).
- J judged the sound good (14 Nov). The start of each sample is limited to its held level
  (`START_MAX` in `build_samples.py`): matching the join's level had made the lowest 8' note start
  50 % too loud.
- Page: one "Accordion" instrument (the jazz preset is gone) with seven register buttons in J's
  order and names: L Bassoon, ML Bandoneon, MM Violin, MH Oboe, H Piccolo, LH Organ, M Clarinet.
  The reed dots only display the register; the reed tuning slider (CC 27) is still there.
- Velocity on the accordion = bellows pressure (`accordionLevel`, `accordionBrightness`): 24 dB of
  loudness plus a one-pole low-pass in `ReedSampler` (700 Hz..16 kHz, at least 3x the note).
  Measured 27 dB from velocity 4 to 127 on G3; the brightness change is gentle and J has not yet
  judged it. Before, velocity gave only ~13 dB and under 2 dB between 100 and 127.
- Flashing: after `arduino-cli upload` the Teensy often stays in the bootloader (`PID_0478`) for
  10-20 s; poll `Get-PnpDevice` before retrying the upload.
- Still open: rank balance (`SAMPLED_REED_GAIN`) and loop
  length are first guesses. The browser sound (`websynth.js`) still uses the synthesised reeds.

## eTutti Student V2 (16 Nov 2026) — new design cycle, start here

`etutti/hardware/student_v02/`: Chat's `SPEC.md` v1 (Retro finish; canvas link at its top) answered by
Code. Reports (Portuguese): `FIT_CHECK.md` (gaps, the two studies, 12 "Perguntas para o design"),
`ELETRONICA.md`, `COMPRAS.md`. Nothing ordered or printed; **no V2 firmware yet** (OLED, mic, pins).
- `geometria.py` (stdlib) is shared by board and case: keys, the hull's offsets (well 12.5, grid screws
  18.5, grid edge 21.5), interface positions. Run order: `geometria.py`, `pcb/schematic.py`, KiCad python
  `pcb/build_board.py` (~8 min), KiCad python `pcb/export_fp.py`, `estudos/flexao.py`, `fab.py`, KiCad python `pcb/grade_fab.py`; CadQuery
  venv `case/case.py`, `case/fit_check.py`, `case/render.py`, `estudos/acustica.py`.
- Board = the V1 board changed by script (never by hand): LED out, USB-C/OUT moved, IN jack J302 +
  R305/C309, OLED socket J401 (JST SH, Qwiic order, I2C shared with the codec), encoders EC11E18244AU
  (20 mm shaft, C202365) at the SPEC's knob centres, codec I2S_DOUT -> Teensy pin 8, holes HG1-HG10
  (grid) / H1-H4, H9, H10 (lid) / H5-H8 (base pins). DRC as the V1's, parity 0.
- `build_board.py` lessons: move a group with its copper and only stretch tracks that run along the
  move; let KiCad's DRC say which tracks to rip; **do not prune dangling ends before routing** (the two
  halves of a cut route are what the router mends), and after routing drop a dangling item only if no
  pad group splits; the codec's pin 16 needed a hand-drawn fan-out of pins 16-19. Set `V2_ATTEMPTS` /
  `V2_EXPAND` to shorten a diagnostic run; progress is in `pcb/build/progress.log`.
- Case: lid drops over the sockets (openings open downwards, tongues on the base), grid screws end in
  nuts under the board so the base comes off with 6 screws, hat knob with a hidden sleeve.
- **SPEC v2 done (16 Nov, cycle 2):** sockets 0.3 mm behind the wall's inner face (closed holes, board goes
  into the lid from below; `fit_check.py` tests the insertion path), grid = FR-4 board of its own
  (`pcb/grade_fab.py`, z 11.35-12.95), window 24 x 13, L-shaped acoustic box 10.4 cm3 with ribs, 0.4 mm
  paint recesses. Lettering gotchas in `case.py`: cut the glyphs one by one, before the lid's cavity, from
  polygon outlines (`polygonised`); Bahnschrift's overlapping outlines never finish cutting; one cut with
  all glyphs ate 26 GB. Michroma (OFL) is in `case/fontes/`, downloaded with J's OK; its strokes are thin
  for a recess. **SPEC v3 (17 Nov):** eTUTTI outlines grown 0.1 mm (offset2D by winding direction), STUDENT · V2 is
  paint only (`out/tinta_marrom.stl`, no cut), 0.5 x 45 deg chamfer on the three holes, USB-C hole 12.8, flange 0.15.
  `out/tinta.stl` + `tinta_marrom.stl` are the paint, for the renders only.
- **Presentation page (17 Nov):** `/etutti/studentV2/` (unlisted, noindex, Portuguese only; case-sensitive
  path) = `etutti/studentV2/{index.html,styles.css,img/}`, written by `student_v02/pagina.py` (texts, parts by
  area/supplier, price table: edit there). Its pictures (exploded view with numbered pins from `img/ancoras.json`,
  7 assembly steps, plan, wall, cuts) come from `case/passos.py` (CadQuery venv, ~1 min, after `case.py` +
  `render.py`). Prices are ranges: "preço visto" = shop pages of 15 Nov (V01 sourcing), "estimativa" = not
  quoted (JLCPCB fees, OLED, speaker, print job...); GBP at 1.30 USD is an assumption. Regenerate the page
  after any price or part change.
- Studies: board needs the 4 pins in H5-H8 plus 3 pillars for <= 0.05 mm at 3 N (the SPEC's 3 pin spots
  sit on back-side parts); a printed grid sags onto the switches (FR-4 suggested); the 3.9 cm3 box puts
  the speaker's resonance near 1 kHz (12 cm3 would give 7-9 dB more bass).

## eTutti Student V01 (14 Nov 2026) — the version to be ordered

**Closed on 15 Nov 2026: checked and ready to buy; nothing ordered, printed or built.** J will
present it, then may start a new design concept with Claude Chat from
`etutti/hardware/student_v01/RESUMO-PARA-O-CHAT.md` (state, the fixed dimensions a new case must
respect, the open design questions, what the prototype will answer). Same Chat -> Code protocol
as before: Chat writes a versioned SPEC, Code models, checks and reports. Don't change the
ordered files (`student_v01/fab/`, `kicad/`) without an explicit task.

`etutti/hardware/student_v01/` = the **Viaggio J1** board taken to the order (J's name for it:
"Student_V01"; not the resistive-key `student_viaggio/`). Its `README.md` (Portuguese) holds the
nine-step review J is doing with Code, one step approved at a time: 1 keyboard, 2 concept, 3 board
shape, 4 schematic/parts (all closed 14 Nov, nothing changed), 5 routing/checks (done, awaiting
J), 6 firmware for this board (does not exist yet: 28 keys, 2 muxes, MicroMod pins, battery, soft
power, amplifier, sampled accordion), 7 full 3D model + case with the 6 pillars (J asked to use
the models in `etutti/hardware/student/eTutti_3D.3dshapes/`, untracked), 8 sourcing, 9 shopping
list and order. Update the README's table as steps close. Nothing is ordered until J says so.
- `student_v01/build.py` (KiCad python, ~1 min) copies the J1's tracked KiCad files, renames the
  two silkscreen texts, checks the board differs from the J1's in exactly those 2 lines, runs DRC
  (0 unconnected, parity 0, only the 3 accepted EN_B widths) and writes `fab/` through the J1's
  `m3.py` functions. Board changes go into the J1 (or the script), never by hand in
  `student_v01/kicad/`.
- **Order of the remaining steps (J, 15 Nov): 7, 8, 9, then 6 (firmware) last.** Step 5 approved.
- Step 7 so far: `student_v01/model3d/build.py` (CadQuery venv python, ~1 min) assembles the
  instrument without the case (frame: z = 0 at the board's top, y = -y KiCad) from the board's
  GLB, SparkFun's module STEP and J's VRML models, and writes `img/` + `heights.json`. Gotchas:
  `pv.read()` on KiCad's GLB hangs (own reader in `model3d/glb.py`); this PC's KiCad 3D library
  lacks the EC11E, HRO USB-C, JST PH, QFN, X2SON and TS-1187A models (boxes from `Altura_mm`
  instead). `model3d/fetch_models.py` downloads the parts' own STEP models from EasyEDA by LCSC code
  into `model3d/modelos/` (gitignored); call the API with plain `curl` (Python's client and
  browser-like headers get 403) and not in bursts (a second batch minutes later was refused).
  Fetching them exposed a wrong BOM code: codec U301 was C511764 (QFN-32 variant), now C2651833
  (SGTL5000XNLA3, QFN-20) in `schematic.py`, the J1 board and the BOMs; **step 8 must check every
  LCSC code's package against its footprint**. Encoder shaft: 24.5 mm in EasyEDA's model vs 20 in
  the footprint (unresolved). Module depth below the board measured 4.7 mm (was estimated 6-6.5).
  J said (15 Nov) not to work on the case yet. The case does not
  exist yet: battery spot (503450 under the front-left, under trimmed encoder legs), outer shape
  and process are J's open decisions.
- **Step 8 (15 Nov, awaiting J):** `student_v01/fornecimento/conferir_bom.py` looks every BOM
  code up on LCSC (`wmsc.lcsc.com/ftps/wm/product/detail?productCode=`) and in JLCPCB's parts
  library (POST `.../shoppingCart/smtGood/selectSmtComponentList`, keyword = code or part number:
  stock, base/expand), 2 s apart, plain curl. It found five wrong or dead codes, all fixed in
  `viaggio_micromod/pcb/schematic.py` (re-run: ERC 0/0), the J1 board and the BOMs: codec
  C2651833, **R203 C25871** (was a 200 k 0603: charge current would have been ~4 mA), **R401
  C25099** (was 27 ohm 0603), muxes C179326 (the tube part had 0 stock), TMAG5253 C22401868 and
  standoff C7496631 (both now in JLC's library: no Global Sourcing). ~US$ 34 of parts per board
  (codec is 9.35), ~70 per assembled board. Report + 4 questions for J in
  `fornecimento/FORNECIMENTO.md`. Encoder shaft tip is most likely 24.5 mm above the board (Arrow
  + EasyEDA model), not the footprint's 20: matters for the case and knobs only.
- **Step 9 (15 Nov, awaiting J):** `student_v01/LISTA_DE_COMPRAS.md`. J's decisions: fewest
  boards possible (JLCPCB minimum = 5 PCBs with 2 assembled; ~US$ 220-265), Gateron KS-20
  **Orange**, **3-wire** battery (503450 with NTC), MicroMod module bought later. Only step 6
  (firmware) and the postponed case remain. Nothing ordered.
- **Step 6, firmware (15 Nov, awaiting J):** the same sketch `etutti/firmware/etutti_synth/` now
  builds two instruments, chosen by the board: Teensy 4.0 = eTuttino, **Teensy MicroMod =
  Student V01** (`ETUTTI_STUDENT`; `--fqbn teensy:avr:teensyMM:usb=midi,speed=396`). Student
  part: 28 keys / 2 muxes, TMAG5253 groups switched by S3 (60 us wake), per-key sensor direction
  from the rest reading (readings mirrored about mid-scale), soft power on the volume click
  (2 s; KEEP pin 10, pin 28 low to switch off), volume encoder (digital gain `outAmp`, since
  the MAX98357A shares the I2S), selector = the seven registers (CC 26 back, kept in EEPROM),
  speaker on without headphones, battery and idle switch-off, LED states. **Never run on a
  board.** `student_v01/firmware_check.py` (KiCad python) checks the sketch's pins against
  PINOS.md and J101's nets (27/27) and KEY_INPUT (28/28). Report: `student_v01/FIRMWARE.md`.
  Not done: a Student model on the page, watchdog. Shopping list gained 65 g and 80 g long
  springs (J wants a bayan-like key weight; KS-20 Orange is 38 gf).
  All nine review steps are now done or awaiting J; only the case is postponed.
- **CPL was wrong (found by J in JLCPCB's preview, 15 Nov).** The J1's `m3.bom_cpl` takes
  positions from KiCad's footprint origins and rotations from a per-package table; JLCPCB places
  by the EasyEDA footprint of the LCSC code. `student_v01/fornecimento/cpl_jlc.py` (KiCad python)
  now writes `fab/student_v01_cpl.csv` from the pads: fits each part's EasyEDA pads (in
  `fornecimento/easyeda_pads.json`, tracked) onto the board's pads, by shared pad numbers or by
  place; bottom side = EasyEDA footprint mirrored left-right, rotation counted the other way
  (reproduces the old result for SOT-23/TSSOP on the back). 37 of 140 parts changed: **all 28
  TMAG5253 were 180 deg off** (invisible in a preview: symmetric pads), J101 180 deg, encoders
  90 deg + 7.7 mm, jack 6.6 mm, USB-C 1.5 mm, J202 180 deg, U201/U202/U204 90 deg.
  `student_v01/build.py` runs it after the fab export; the table-based file is kept as
  `fornecimento/cpl_antigo.csv` to compare. **The J1's own `fab/viaggio_j1_cpl.csv` is still the
  wrong one.** EasyEDA's API allows about a dozen requests, then 403 for some minutes.
- **State on 15 Nov, evening:** J checked the new CPL in JLCPCB's preview (connectors, encoders,
  pin 1 of the chips and sensors) and calls the project **ready to buy**; he will present it
  for approval before ordering. He chose to keep the board rectangular (cutting it to profile A
  on the right was offered: only 53 GND stitching vias lie outside the profile there).
- **Prototype case:** `student_v01/case/case.py` (CadQuery; model frame, z = 0 at the board's
  top) writes `out/fundo`, `tampa`, `espacador` (STEP + STL): rectangular, 251.3 x 99.8 x 19.9 mm,
  8 M2 x 16 from below (H1-H4 into lid posts, H5-H8 through spacer and plate into nuts), the 6
  keyboard pillars, battery cradle, one key opening (union of r 10.8 circles) with a rim on the
  plate, speaker grille, USB/jack slots. `case/fit_check.py` tests every part's mesh points
  against the two shells (`compute_implicit_distance`, 0.15 mm margin); `model3d/build.py` adds
  the case to the scene (`case_*` shots). Report: `case/CASE.md`. Not printed.
  **J's change, then approved (15 Nov):** the lid covers the keyboard like an accordion's: a
  1.6 mm deck 0.4 above the switch housings with one 7 mm hole per key (lid top now 13.2, case
  23.3 mm tall), and a new button `out/capa` (5.6 mm stem through the deck onto the MX cross,
  16.5 mm domed head, 0.7 mm above the deck when pressed), which replaces the Pocket's skirted
  cap for this model and goes on from above after the lid.
- The J1's step M3b (LCSC codes, C307 = C162182, SW403 height) had sat unmerged on its branch
  since 28 Oct; merged as PR #138.

## eTutti StudentViaggio (14 Nov 2026) — cheap first prototype, resistive keys

`etutti/hardware/student_viaggio/` = the **Viaggio J1** electronics with the 28 Hall keys swapped
for bare interdigitated electrodes (`FSR_Comb_D12`, pad 1 GND, pad 2 = the J1's `OUT_Kxx`) under a
pressure-sensitive sheet; R601/R602 (10 k to +3V3) on the mux commons; Teensy pin 4 free. Its
`README.md` (Portuguese) is the report: checks, options for the keys and for the MicroMod, open
questions. No fab files and no firmware for these keys yet.
- **v0.2 (compact):** 210 × 95 mm, pointed right end, keys on a 19.05 × 18 grid (rows of
  7/8/7/6), 11 M2 holes, all from `pcb/layout.py` → `layout.json`. The J1's left block (x ≤ 78)
  and the two muxes stay where they are with their routing; the 28 key nets are routed again.
  Flex: 0.122 mm on the holes alone, 0.039 mm with the 6 case pillars in `pcb/flexao.json`.
- Run, in order: `python .../pcb/layout.py`, `python .../pcb/schematic.py` (ERC + netlist
  compared with the J1's), KiCad python `.../pcb/build_board.py` (reads the J1 board, never
  writes it; reuses `viaggio_j1/rota_restante.py` as the router; DRC 0/0, parity 0; **10-15 min,
  run it in the background**; it retries up to 6 times with the failed nets first), KiCad python
  `.../pcb/mechanics.py`, `python .../pcb/pinos.py`.
- Routing gotcha: stubs left by the pruned nets must go **before** routing (`drop_dangling`), or
  they block the mux inputs and the last key nets find no path.
- The footprint library keeps the nickname `viaggio_micromod` and the schematic keeps the J1's
  uuid namespace, so the J1 footprints stay linked. Don't rename either.
- **pcbnew gotcha:** after `board.Remove(footprint)`, keep the Python object alive (the script's
  `rm()` / `GRAVE`). If it is garbage-collected, later pcbnew calls return bare `SwigPyObject`s.
- `etutti/hardware/student/` and `studentBK/` (the v20 draft, untracked) were audited and are not
  manufacturable (no 3.3 V source, mirrored back-side ICs, made-up footprints). Don't build on them.

## Project status (25 Oct 2026) — eTutti Viaggio MicroMod is the active project

**eTutti Viaggio MicroMod** (`etutti/hardware/viaggio_micromod/`, SPEC v2.2) is now the only
active instrument. It is the Viaggio Rev2 with the chip-down RT1062 swapped for a **SparkFun
MicroMod Teensy** module (DEV-16402: RT1062, 16 MB flash, no PSRAM) in an M.2 Key E 4.2 mm
connector held by an M2.5 SMD standoff. JLC fits the connector and standoff; J fits the module
at home. Gone from the board: the RT1062, MKL02, W25Q64, PSRAM spot, crystals, SNVS regulator +
start gate (E5), DCDC parts and the BGA-196 footprint.
- Placement contract: `viaggio_micromod/concept/out/viaggio_micromod.json` (by
  `concept/sectors.py`; same plan as Rev2 with sector P replaced by the module).
- Firmware board: "Teensy MicroMod" in Teensyduino; PINOS.md uses MicroMod Teensy pin numbers,
  I2S 7/20/21/23 and I2C 18/19 unchanged.
- Rules: vias 0.5 / 0.3 drill; In2 is a **signal** layer (GND/3V3 pours after routing).
- Steps (SPEC §7, one PR each, J approves each): **M1** schematic + ERC + pin map + BOM;
  **M2** placed board for routing (no tracks) + DSN; **J routes** in KiCad with Freerouting;
  **M3** checks (DRC, firmware 28/28, flex) + fab.
- **Decision of 25 Oct 2026, still in force: J routes; no Code step routes.**
- `etutti/hardware/viaggio/` (SPEC v2.1, the chip-down RT1062 attempt) is **archived**:
  reference only, don't change it. Its routing never closed (the BGA fan-out) — that is why
  the module exists.

## Project status (19 Oct 2026) — eTutti Viaggio (archived since 25 Oct 2026)

**eTutti Viaggio** (`etutti/hardware/viaggio/`, SPEC v1) is now the only
active instrument: the Pocket's 28-key keyboard and right side, one
4-layer board with ALL electronics assembled by JLCPCB ("Teensy 4.1 on
the board": i.MX RT1062 + PJRC MKL02 bootloader + 64 Mbit flash + unfitted
PSRAM footprint, SGTL5000,
MAX98357A, BQ24074, TPS63001, USB-C, TMAG5253 via JLC Global Sourcing),
soft power (hold the volume click 2 s), thin ~1000 mAh battery, case only
conceptual. Same Chat→Code protocol as the Pocket (below); the Viaggio's
reports live in `viaggio/`. Pin map keeps Teensy 4.1 pin numbers so the
firmware stays compatible (compile with `teensy:avr:teensy41`).
**Current spec: `viaggio/SPEC.md` v2.1 (Rev2).** It specifies:
- a rectangular 246.5 × 95 board, 4 layers, 1.2 mm;
- parts coded by sector (P, E, F, I, A, T → P1…T4), with positions, sectors and corridors in
  `concept/rev2/out/viaggio_rev2.json`.

The board is done in the four steps of SPEC §7, one session = one PR each, and J approves each step
before the next:
- 3.1 schematic + ERC + preliminary BOM + pin map (done, see below);
- 3.2 board outline, rules, placement (done, see below); **routing is J's job** since 25 Oct 2026;
- 3.3 sectors E, F, A, I;
- 3.4 sector T, then DRC/fab/POWER.md.

**Step 3.1 state:**
- `viaggio/pcb/schematic.py` (stdlib Python) writes the KiCad schematic in `viaggio/pcb/kicad/`:
  - one sheet per sector;
  - a `Codigo` field on every part;
  - global labels;
  - the project's own `viaggio.kicad_sym`.
- It then runs ERC (0/0) and checks KiCad's netlist against its own net list. Don't hand-edit the
  `.kicad_sch` files.
- Also in `viaggio/pcb/`: `PINOS.md` (the contract with the firmware) and `bom_preliminar.csv`.
  The report is `viaggio/ELETRONICA.md`.
- The `eletronica` agent owns the Viaggio's `pcb/`, `POWER.md` and `ELETRONICA.md`.

**Step 3.2 state (SPEC v2.1):** power switch on the volume click (I1); flash W25Q64JVSSIM; encoders
EC11E18244A5 (18/36, `ENC_STEPS_PER_DETENT = 2`); jack PJ-327A (the PJ-313D had no tip switch).
Run, in this order (all from the repo root):
1. `python etutti/hardware/viaggio/pcb/schematic.py` — also writes `pcb/kicad/viaggio.pretty/`
   (`footprints.py`: BGA-196, jack, LED 1615, Gateron), ERC + netlist check;
2. `"C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/viaggio/pcb/impedance.py`
   — 2D field solver for the USB pair on JLC04121H-7628 → `build/impedance.json` (only when the
   stack-up changes);
3. `"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio/pcb/build_board.py`:
   - places every part from `viaggio_rev2.json`, then tries to route sector P with its own grid
     router (`pcb/router.py`);
   - after three sessions sector P still had 18 DRC errors and 3 unrouted connections.
4. `"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio/pcb/handoff_freerouting.py`:
   - turns the placed board into the board J routes: no tracks;
   - links every footprint to the schematic (F8 is clean) and fixes 4 courtyard overlaps;
   - In1/In2 become power (plane) layers;
   - fills the zones and writes `build/viaggio.dsn`;
   - result: DRC 0 errors, schematic parity 0, 499 unrouted.
   - The partial sector P routing stays in `kicad/viaggio_rota_P_parcial.kicad_pcb`, for reference
     only.

**Decision of 25 Oct 2026:** J routes the board himself in KiCad with the Freerouting plugin. Code
supplies the placed board, the rules and the DSN. The guide is `viaggio/pcb/ROTEAMENTO.md`. Don't
re-run `build_board.py` over a board J has routed: it rebuilds `kicad/viaggio.kicad_pcb` from
scratch.

The **eTuttino Pocket is finished at SPEC v5
(PR #110) and paused**; its files are reference for the Viaggio.

## Project status (17 Oct 2026)

**eTuttino, eTutti and eTuttiChorus are PAUSED.** Their code, case,
boards, manuals and pages stay as they are. Read and reuse them, but
don't change their behaviour without an explicit task. **The eTuttino
Pocket is the only active instrument project.** The public `/etutti/`
becomes a minimal family landing page (task:
`etutti/TAREFA-pagina-inicial.md`). The Pocket's real page comes only
after the prototype and the engineering detail are done.

## eTuttino Pocket — como trabalhamos (protocol since 17 Oct 2026)

- **Gestão = Claude Chat** (with J). It owns `etutti/hardware/pocket/SPEC.md`
  (versioned v1, v2…, Portuguese, each with "Mudanças desde a versão
  anterior" and a "Tarefas para o Code" section that tags each task
  Design / Eletrônica / Programação e som). Chat never edits the agents'
  files; Code never edits the SPEC.
- **Code = one integrating session + three subagents** in
  `.claude/agents/`: `design`, `eletronica`, `programacao-som`. Each one
  owns its folders and its report and only *reads* the others' (the
  agent files list them). The integrating session (whoever J opens):
  1. reads the SPEC version and its "Tarefas para o Code";
  2. hands each task to its agent, in dependency order (design → shape
     and `pcb_envelope.json`; eletrônica → board and `pcb/PINOS.md`;
     programação e som → firmware/pages; sound and pages don't wait for
     the board);
  3. runs the cross-checks itself (fit check, DRC 0/0/0, board ×
     firmware, firmware compile for both models, pages in the browser);
  4. commits, opens ONE PR per SPEC version or task, and merges it
     (J's standing rule: commit → PR → merge without asking);
  5. tells J the one line to relay to Chat: "SPEC vN atendida — PR #x;
     relatórios atualizados".
- **Contracts, one owner each:** `pocket/build/pocket.json` and
  `pocket/case/out/pcb_envelope.json` (design), `pocket/pcb/PINOS.md`
  and `pocket/POWER.md` (eletrônica), CC/SysEx map in `script.js` + the
  sketch (programação e som). A change needed in someone else's
  contract is asked for in your report, never made directly.
- **Reports** (Portuguese, each ends with "Perguntas para a gestão"):
  `pocket/FIT_CHECK.md` (design), `pocket/ELETRONICA.md` (eletrônica),
  `pocket/FIRMWARE_SOM.md` (programação e som).
- Run on J's Windows PC: KiCad, arduino-cli/Teensyduino, the CadQuery
  venv and the Teensy are there. A cloud session can only do docs and
  the web pages.
- Parallel work: one worktree/branch per agent, merged in the order
  above.
- `pocket/rascunhos/layout_v2.py`: J's first left-side revision (logo,
  knobs + LED, speaker grille, "<"-shaped left end), unfinished (the
  36 mm speaker doesn't fit the front-left corner). Starting point for
  the design agent; see the README there.

## eTuttino Pocket (started 15 Oct 2026)

Compact third model: same C-griff geometry (P 18.5, rows 16.02, 100 mm
deep), **28 keys G3–E5** (row 1 A3..D#5, row 2 G3..E5, row 3 G#3..D5,
row 4 A3..C5), `O = 84`, ~237 × 100 mm, no screen zone, 2 muxes, LiPo
1S ~2000 mAh (4 h with earphones; budget in `pocket/POWER.md`, the 28
Hall sensors are >half the draw), battery bay under the front of the
interface so the keyboard keeps the eTuttino's height. Lives in
`etutti/hardware/pocket/`: `SPEC.md` (same Chat→Code protocol as the
case SPEC, Portuguese, §9 lists the Code deliverables, §10 the open
questions), `layout.py` (stdlib; writes `build/pocket_keys.csv`,
`build/pocket_top.svg`, `build/pocket.json`, `POWER.md`; its eTuttino
reference outline reproduces the case's 331.1 mm, which validates the
hull method). Next: `case.py` gets `MODEL = "pocket"`, then the board
(charger + buck-boost, Teensy fed on 3V3 with VUSB–VIN cut — CHECK),
firmware `ETUTTI_MODEL_POCKET`, page model picker.

## eTutti handoff (session of Oct 2026, PRs #63–#76) — earlier state

**State at hand-off** (everything merged to `main`):
- **Page** `/etutti/` (unlisted, noindex) works with the user's real
  Teensy. It has:
  - model picker (eTuttino / eTutti "in development")
  - round C-griff / B-griff buttons, row 1 at the bottom
  - optional computer keyboard
  - instruments: classic accordion (default, dry MM), jazz accordion
    (~6¢ wet), piano, bass, guitar (nylon), synth (3 oscillators)
  - round accordion register switch with named registers
  - Reset to default, "modified" marker
  - MIDI monitor, en/pt/es strings
- **Firmware** `etutti/firmware/etutti_synth/` compiles clean (teensy40,
  usb=midi) and is flashed on the user's Teensy 4.0 + Audio Board Rev D.
  The user confirmed accordion/bass work and asked for piano/guitar to be
  fixed (done in #74: SVF → biquad, sample gain up) and the synth to come
  back (done in #74).
- **PCB** `etutti/hardware/`: **44-key version with power LED (#77)**,
  stack moved to the back-left + case (#78), 267 × 97.2 mm, routed, DRC 0/0/0, firmware cross-check 44/44 (incl.
  LED pins), manual renders in `etutti/manuais/img/`. Firmware with the
  44-key table, LED and high-note reed tables is
  flashed on the user's Teensy. (The #75 board, 34 keys, was: Ready-to-upload Gerbers in `fab/`
  (PCB 1.2 mm + FR4 plate + JLCPCB BOM/CPL).) The old MX/diode-matrix
  board was never ordered and is gone. As far as we know the new one has
  **not been ordered** yet either. If the layout changes, re-run
  `generate.py`, then `build_pcb.py`, and update `etutti/manuais/`.

**Next steps the user mentioned** (not done):
- Tune the instruments by ear. The user said the other sounds "can be
  improved later". Ask what sounds artificial, instrument by instrument.
- A real acoustic-bass sample, converted from a SoundFont with PJRC's
  SoundFont decoder and dropped in like `piano_samples.*`.
- Saved custom presets. `PRESETS` in `etutti/script.js` is already one
  flat shape per preset; Web storage or a downloadable JSON are the
  obvious routes.
- A custom hardware interface (knobs/buttons) talking back over MIDI.
  The monitor and `handleIncoming` are the hook.
- The full eTutti model (bigger keyboard), only a render for now.
- The user may want round MX keycaps (noted in the hardware BOM).
- Once a real Hall board exists: check the sensor swing (key test /
  a serialmidi build printing raw readings), then tune NOTE_ON_AT,
  VEL_START, FAST_MS/SLOW_MS by feel. A bellows/expression input on the
  free pins 17 or 22 (A3/A8) was suggested for the accordion.

**How to verify, without asking the user to test:**
- Firmware: `arduino-cli compile --fqbn teensy:avr:teensy40:usb=midi
  etutti/firmware/etutti_synth`, then
  `arduino-cli upload -p usb:80001/3/0/3 --fqbn ...` (check
  `arduino-cli board list` for the port). The user has OK'd flashing
  their connected Teensy. After a flash, confirm it enumerates as
  `VID_16C0&PID_0485` (MIDI) and stays stable (PowerShell `Get-PnpDevice`).
- On-device measurements: copy the sketch to the scratchpad, add
  `AudioAnalyzePeak` / `AudioProcessorUsageMax()` prints and a
  self-playing loop that cycles every ~10 s, then build with
  `usb=serialmidi` and read `COM3` with
  `System.IO.Ports.SerialPort` (arduino-cli monitor printed nothing).
  Reflash the production `usb=midi` build afterwards.
- Page: the in-app browser pane worked fine in the #75 session
  (preview_start "static-site", fake `navigator.requestMIDIAccess` via
  javascript_tool, then click Connect). If it hangs again,
  use headless Edge (`msedge --headless --screenshot --timeout=3000
  --window-size=800,700`) on a temp copy of `etutti/index.html` with:
  - `/shared/` → `../shared/` paths
  - the gtag script removed (it blocks `load`)
  - a fake `navigator.requestMIDIAccess` that records sent bytes and
    prints results into a full-screen `<pre>`
  - Retry a few times: headless screenshots fail intermittently, and
    window heights over ~1100 px tend to fail.
- PCB: `"C:/Program Files/KiCad/10.0/bin/python.exe"
  etutti/hardware/build_pcb.py`. It exits non-zero on DRC problems or a
  firmware mismatch. Running it rewrites `fab/`/`kicad/` with new
  timestamps even when nothing changed; `git checkout -- etutti/hardware`
  if the layout didn't change.

**Gotchas learned:**
- Holding the Teensy's button ~15 s restores the factory blink sketch
  (orange LED blinking, enumerates as RawHID `PID_0486`). Just reflash.
- `tone` is an Arduino core function: don't name an audio object `tone`.
- Windows caches the USB device name ("Teensy MIDI" instead of "eTutti").
  Harmless; the page matches both.
- The user writes in Portuguese (pt-BR). Reply in Portuguese.

## Recent history (earlier session: PRs #47–#53, in order)

1. **#47** — reverted the home page's Tuner card icon back to needle-only
   (removed a since-unwanted strobe/meter thumbnail trio).
2. **#48** — redesigned the Chromatic Strobe Tuner home-icon as three
   overlapping "fan" dials (A, B♭, B); changed Octave Strobe's home-icon
   badge "A4" → "A"; **fixed a real pitch-detection bug**: `detectPitch`'s
   clarity score divided by a fixed full-buffer energy figure even though
   the numerator only summed `(size - lag)` samples, systematically
   penalizing low notes — a clean ~110 Hz tone could already fail the
   confidence threshold from lag length alone. Replaced with a proper
   per-lag-normalized autocorrelation (NSDF / McLeod Pitch Method) plus
   first-peak picking (to avoid octave-down misreads on clean tones' exact
   harmonic ties). This is shared logic duplicated in `tuner/script.js`
   and `strobetuner/script.js` — if you ever touch pitch detection, fix
   both (or, better, finally extract it to `shared/`).
3. **#49** — unified section order across all three tuner pages and
   replaced `/tuner/`'s and `/multistrobe/`'s old "one column per
   reference-pitch standard" Frequency Table with the octave-by-note grid
   `/strobetuner/` already had (now the one shared implementation, see
   Architecture above). Removed the per-table duplicate Standard/Key
   selector; added a live text line naming the standard/pitch currently
   shown.
4. **#50** — Octave Strobe Tuner: restored 180° arc (was drifted to 160°
   in earlier work), fixed the "display rescales when a different note
   plays" bug (ring radius now depends on a fixed 9-octave-slot layout,
   not on how many octaves *that specific note* happens to have — see
   `ringRadiusForOctave`), repositioned the octave legend to line up with
   true ring radii (fixed position, note-before-number). Moved the disc's
   full shared appearance/geometry into `shared/` and switched
   Chromatic Strobe's 12 discs to build from it too — they're now
   "adapted copies" of the Octave Strobe disc (180°, thin bezel, ticks,
   monochrome wedges) instead of a separate smaller/colored design.
5. **#51** — merged "Input Monitor" and "Test Tone" into one panel,
   collapsed by default, positioned right after the display on all three
   pages. **Ported Test Tone to `/strobetuner/` and `/multistrobe/`**
   (previously Tuner-only) via a new shared `T.createTestTone` — a real
   oscillator routed to both the speakers and the page's own analyser, so
   it exercises the same detection pipeline a microphone would.
   Octave Strobe bypasses autocorrelation for the *known* test frequency
   (matching Tuner's own approach) purely for note identification; its
   disc's Goertzel rings still analyze the real synthesized audio.
   Chromatic Strobe needs no bypass at all — no single "detected note"
   concept there, so the twelve discs just light up correctly on their
   own. Fixed a genuine bug along the way: a second `.panel-header`
   inside one collapsible block stayed visible while collapsed (the
   collapse-hide CSS rule exempts *every* `.panel-header`) — introduced
   `.panel-subheader` for non-collapsing sub-headings.
6. **#52, #53** — the caching fix described above, found and fixed during
   this session's own final live-site review.
7. **#55** — **fixed a real Goertzel spectral-leakage bug** reported by a
   user: playing a single pure test tone (e.g. A440) on `/multistrobe/`
   lit up several *neighboring semitones'* discs (G♯, A♯, B, G — not
   harmonics, which correctly stayed dark) at close to full strength, and
   the correct A disc's own reading looked jittery. Root cause: each
   ring's Goertzel window (`shared/strobe-disc.js`) was only
   `GOERTZEL_MIN_CYCLES = 6` cycles long with no window function applied —
   a rectangular window's main lobe at that length is ≈±17% of the target
   frequency, several times wider than the ~6% gap between adjacent
   semitones, so a clean tone landed well inside a neighbor's passband.
   Confirmed by simulation (not just the formula) before touching code —
   see the constant's own comment in `shared/strobe-disc.js` for the
   numbers. Fix: apply a Hann window inside `goertzel()` and raise
   `GOERTZEL_MIN_CYCLES` to 36 (verified to push adjacent-semitone leakage
   under ~0.3% almost everywhere on the keyboard); doubled
   `ANALYSER_BUFFER_SIZE` to 32768 (the Web Audio API's own max fftSize)
   so the longer window doesn't get clamped down again for the bottom
   octave; halved `MIN_RING_MAGNITUDE` to compensate for Hann's ~0.5
   coherent-gain factor so mic sensitivity is unchanged. Same fix, no
   separate work needed: `/strobetuner/`'s single hero disc uses the exact
   same shared engine. Also bumped the Test Tone **Fine Tuning** slider
   from 1¢ to 0.1¢ steps (`shared/tuner-common.js` + all three
   `index.html`s) per the same report, to match the Frequency Table's
   hundredths-of-a-Hz display precision.

## Testing notes / caveats

- This environment cannot grant real microphone permission, so "mic"
  functionality was verified structurally (no console errors, correct
  wiring) but never with real live audio input. **Test Tone** (a
  synthesized oscillator, no permission needed) *was* verified
  end-to-end on the live production site for all three pages, including
  confirming the correct disc/ring lights up with ~0¢ deviation.
- The local dev server caching issue (see above) means: if a future
  session's local testing shows unexplained stale behavior, try a brand
  new browser tab or bump the dev server's port before assuming the code
  is wrong.
- The #55 Goertzel leakage fix was verified two ways: a standalone Python
  simulation of the exact windowed-Goertzel math (sweeping every semitone
  offset 0-12 at several candidate cycle counts) before touching the code,
  then structurally on the local dev server — driving Test Tone at 440 Hz
  and reading each disc's `is-active`/`in-tune` classes via
  `javascript_tool` confirmed only the `A` disc lit up, where before the
  fix several neighbors would have too. Not yet re-confirmed on the live
  production site the way #51's Test Tone rollout was.
- A user report that Chromatic Strobe's Frequency Table appeared "empty"
  was investigated thoroughly and could not be reproduced anywhere
  (local dev, then the live site) — the table was correctly populated in
  every check. Almost certainly a stale-cache symptom on the reporter's
  end (see the caching section above — this was *before* the #52/#53
  fixes existed, so it's very plausible). Worth a quick re-check if it's
  ever reported again, but treat it as resolved by the caching fix unless
  a concrete repro shows up.

## Possible follow-ups (not done, not blocking)

- Pitch detection (`detectPitch`) is still duplicated between
  `tuner/script.js` and `strobetuner/script.js`. Low urgency, but if it's
  touched again, consider finally moving it into `shared/`.
- `shared/strobe-disc.js`'s `DEFAULT_GEOMETRY` is now effectively dead —
  both real callers (`tuner-family` pages) always pass explicit geometry
  via `buildStageGeometry`. Harmless to leave, fine to remove if it's
  ever confusing.
- `metronome/`'s opt-in `?__v=` cache-busting scheme predates and is
  inconsistent with the static `?v=` scheme now used on the tuner pages.
  Worth unifying if metronome's own assets ever need a forced-refresh fix
  like #52/#53.
- No automated tests exist anywhere in this repo; all verification is
  manual/in-browser. If a testing setup is ever wanted, there isn't one
  to extend — it'd be new infrastructure.
- Even after #55's fix, the bottom octave (A0/A♯0/B0, and to a lesser
  extent A1-ish) still gets less semitone selectivity than the rest of
  the keyboard, because their rings' desired 36-cycle window would exceed
  `ANALYSER_BUFFER_SIZE` (32768, already the Web Audio API's max fftSize)
  and gets clamped shorter. Not reported as a problem by any user yet —
  flagging it here since it's an inherent, understood limitation rather
  than an oversight, in case very-low-note leakage is ever reported.

### Later sessions (summary)

- **#63–#67** — Luthier Tuning (`/luthier/`): spectrogram, home card,
  og-image re-render, site-title link on every page, peak-hold modes
  (Temporary default).
- **#68–#74** — eTutti / eTuttino (see the handoff above).
- **#75** — eTuttino Hall-effect redesign (velocity) + `etutti/manuais/`.
- **#76** — 41-key layout, slim board with the stack in the
  back-right corner, browser sound (`websynth.js`), manual 3D renders +
  lightbox. Render gotchas: VRML y is flipped, so face winding flips too
  (boxes and cylinders are wound opposite ways in `assembly3d.py`, the
  raytracer shows wrongly-wound faces black); close-ups are crops of
  6000-px transparent renders mapped by the board's alpha bbox, because
  kicad-cli's --pan units aren't mm.
- **#77** — final layout (44 keys: row 2 to E6, row 4 A3..C6 on row 2's
  columns), muxes moved to the front-right corner, power LED, high-note
  reed tables (above C5 the full 20-harmonic tables aliased), commercial
  layout reference removed everywhere.
- **#78** — ergonomic re-layout: Teensy + Audio Board in the back-LEFT
  corner (USB + jack to the left), LED in front of the stack, U52 in a
  15 mm back strip, 267 × 97.2 mm; two-piece 3D-printed case
  (`case.py`/FreeCAD, `case_check.py` collision check), tray pillars from
  `mechanics.py` (board sag 2.6 mm → 0.03 mm at 3 N); renders show all 28
  header legs (`stack_pins`) and the case (`case_*`). Routing took
  U53 rot 0 + COM/address lines early, U51 nearest-first,
  `DEFAULT_ROUTE_FIRST = "OUT_U34"`.

## Workflow conventions observed this session

- User wants autonomous commit → PR → merge after finishing a unit of
  work, without asking first (confirmed repeatedly).
- Commits/PRs end with the Claude Code attribution lines currently in use
  (see any recent commit/PR for the exact wording — it's supplied
  per-session and may change).
- Prefer small, reviewable PRs over one giant one; this session shipped 7
  separate PRs (#47–#53) rather than one mega-PR, and that was well
  received implicitly (no pushback).

## eTutti Student Lite (17 Nov 2026) — cost draft of the V2

`etutti/hardware/student_lite/` + page `/etutti/studentLite/` (unlisted, noindex, Portuguese). Same board and
grid files as the V2; three cuts: JLCPCB assembles the **bottom side only**, no screen, no case. `lite.py`
filters the V2's CPL/BOM to the bottom (125 parts, 32 BOM lines) and lists the 11 top parts soldered at home
(encoders + knobs, USB-C, 2 jacks, U201, D201, 4 passives; J401 is dropped with the screen). `passos_lite.py`
(CadQuery venv) renders the pictures from the V2 scene; `pagina.py` writes the page, reusing `student_v02/pagina.py`
(CSS, price conventions). Total US$ 238-339 vs the V2's 373-556: JLCPCB lines are *derived* estimates (not quoted;
economic one-side assembly not checked). Never re-run after a price change without regenerating the page.
- **Basic swaps and the real JLCPCB quote (18 Nov):** JLCPCB charges US$ 3.09 per Extended part *type* (16 types = US$ 49.44;
  Economic PCBA setup 8.24, stencil 1.55; PCB 39.50 = engineering 25 + board 14.50). `lite.py` swaps R203 1.8k->2.2k
  (ICHG 0.405 A), R501 680k->1M (SD_MODE 0.30 V) and C307 150nF->100nF (SGTL5000 datasheet Figs 19/20: VAG = 0.1 uF)
  in the Lite BOM only (same 0402 footprints, CPL unchanged) -> 13 Extended types. H101 (Wurth SMT standoff) is refused
  by Economic PCBA: removed from the CPL and soldered at home (12 home parts). Not applied: BAT54C->BAV70 (Basic, but
  Vf 0.2 -> 0.5 V on the power-latch lines). No Basic exists for the ICs, connectors, inductor, 1.8 V LDO, 74LVC1G04/08.
  For the V3 board, H101 can become a plain hole + screw + 2.5 mm nylon spacer (no fee, no soldering).

## eTutti Student V3 (18 Nov 2026) — concept board for JLCPCB bottom-only assembly

`etutti/hardware/student_v03/` (README.md, AUDITORIA.md, Portuguese). The V2 board re-placed by script
(`build_sem_rota.py`, KiCad python): tracks removed, dotted case outline / V1 alternatives / sector labels removed,
everything except the 2 encoders (and the speaker's wire pads) flipped to the bottom (connectors keep x at the left
edge), J401's cable passes through a 7 x 2.5 mm slot, H101 became a plain 2.7 mm hole (M2.5 screw + 2.5 mm nylon spacer),
and Basic swaps (R203 2.2k, R501 1M, C307 100nF, BAT54C->BAV70). JLCPCB quote of 18 Nov: PCB 39.50, economic PCBA setup
8.24 + stencil 1.55, US$ 3.09 per Extended type; V3 has 17 Extended types (`bom_v3.py`). `auditoria_pinos.py` compares every
part's EasyEDA symbol pins with the board's nets; real errors found were VALUES (C307 VAG 150 nF vs the datasheet's
0.1 uF), not pin-outs. PJ-327A, TS-1187A and the UMW XC6206 datasheets could not be downloaded (LCSC serves HTML). **No
routing yet: waiting for J's approval**, then routing (reuse the V2 router `rota_restante`), CPL/BOM for JLCPCB, the case's
left wall (connectors now under the board) and the V3 page.
- **V3 routed (18 Nov):** `student_v03/pcb/build_board_v3.py` (derived from the routed V2 board: tracks kept except the USB group's old
  copper, moved parts flipped by `build_sem_rota.py`'s functions, `student_v03/pcb/schematic.py` = V2's with the V3 changes, router =
  `viaggio_j1/rota_restante.py` through `student_v02/pcb/build_board.py`'s functions with `NAME/KDIR/BUILD/BOARD` overridden). DRC with
  parity: only the 3 accepted EN_B widths, 0 unconnected, parity 0. Lessons: no `rr.PROTECT` boxes round the USB-C's 0.5 mm pads (they block each
  other's exits); the router reads only the outer outline, so a slot needs a rule-area keep-out; USB tracks may be on any layer in V3 (the V2 90-ohm
  F.Cu rules are replaced in the .kicad_dru); a dangling USB end must not abort the rip (local `rip_by_drc`). `fab.py` writes the bottom-only CPL
  (135 parts, 0 top). D206 (VBUS_S -> EN_REQ) makes a USB plug switch the 3.3 V on (screen shows charge/battery %, firmware later).
- **Jacks swapped (18 Nov):** JLCPCB flagged the SHOU HAN PJ-327A 5JJ (C668605) "difficult to process" (qty 0 in the BOM sheet). J301/J302 are now the XUNPU PJ-327A (C49284723; pads 2/5 sleeve, 6 ring, 4 tip, 3 tip switch). `student_v03/pcb/troca_jack.py` (KiCad python, after `schematic.py`) renumbers the pads by function without touching tracks, renames the two `unconnected-(J302-...-PadN)` nets, 1.2 mm peg holes, refills zones; `fab.py` regenerates BOM/CPL (jack rotation 270 -> 180, fit error 0.23 mm). The pad *numbers* differing between EasyEDA's footprint and the board's made `cpl_jlc.py` fit by number and turn the part wrongly: keep a swapped part's pad numbers equal to the new part's.
- **USB pair redone (19 Nov):** `student_v03/pcb/refaz_usb.py` (KiCad python, ~4 min; reads and rewrites the board, run after `build_board_v3.py` + `troca_jack.py`) puts D+/D- on B.Cu end to end, no via, 17.209 mm each, hand-computed 45-degree polylines (`dp_path`/`dn_path`/`build_paths`, XV = 19.673 is the vertical run), a length trombone, an In2 keep-out + GND island (`add_in2_zones`), R202 moved north of the pair, the ESD chip's GND pin 2 via in the pocket east of its pad; DRC then rips what the pair displaced and the V3 router re-routes it. `costura_usb.py` re-adds the two In2 zones and stitches GND vias (DRC-filtered). `USB.md` has the numbers (coupled ~6 of 16 mm; 92 ohm is a calculation). **In2 is the +3V3 pour, not GND** (the island is what gives the pair its reference). **pcbnew gotcha:** `SaveBoard` turns a via that overlaps a track of another net into that track's net (a silent short): clear other-net copper near new tracks first (`clear_near`). Rule-area keep-outs on one layer (In2) are honoured by the router. `.kicad_dru`: USB only on B.Cu, 0.25 mm to other nets except zones. `pcb/vista.py dump|draw` renders a window of the board (KiCad python dumps JSON, CadQuery venv plots with matplotlib).
- **V3 power chain trimmed (19 Nov, J chose A: USB wakes, no cut-off with a cable):** D206 (VBUS_S -> EN_REQ) stays; U203, D204, R217, R218, C213 and the nets USB_HOLD / PWR_EN_S / PWR_EN are gone (`student_v03/pcb/tira_cadeia_pwren.py`: removes the footprints and copper, J101 pad 4 = `unconnected-(J101A-3.3V_EN_(28)-Pad4)`, routes again VBUS_S, which ran through U203's pad). 130 parts on the BOM/CPL, still 17 Extended types. The MicroMod Teensy module holds the PJRC power-up sequence inside (SparkFun schematic: PMIC_ON_REQ -> Q2 -> 3.3V_CONTROLLED, SNVS fed from the 3.3 V pads through D2/D4); checked in `AUDITORIA.md`. USBLC6 and SMF5.0A stay (J's decision).
- **Student V3 case, SPEC v4 (19 Nov):** `student_v03/case/` is a copy of the V2's (V2 untouched) driven by `student_v03/geometria.py` (Z_TOP 14.5, no Z_SPLIT, `USB_Z` -2.9, `JACK_Z` -4.0) and `pcb/furos.json` (holes read from the V3 board by `pcb/export_furos.py`; also `export_fp.py` -> `pcb/footprints.json`). Lid z -10.1..14.5 with the lower chamfer; the base is a 2 mm TRAY (`base.step`) with rim, rib grid (`RIB_GRID`), recess for the H101 nut. Run order: `export_furos.py` + `export_fp.py` (KiCad python), `case.py`, `fit_check.py`, `fit_extra.py`, `render.py`, `render_comparacao.py`, `estudos/flexao.py` (KiCad python), `estudos/acustica.py` (CadQuery venv). Findings waiting for the Chat are in `case/FIT_CHECK.md` section 3 (0.5 mm lid over the grid at the front/back chamfer; EC11E18244AU shaft is 24.5 not 20; tray bending in the air; acoustic box 9.75 cm3; screen posts 0.06 mm from the flat ceiling). EasyEDA's STEP of the XUNPU jack and the encoder is in `case/modelos/` (gitignored). The 245-pair fit check takes ~8 min.

- **Student V3 case, SPEC v6 (18 Nov):** chamfer 4.0 x 3.5 on all four sides (lid over the grid 1.4 mm everywhere); no EC11E with a 15 mm shaft exists (all nine are 20 mm, tip ~24.5), so the **10 mm knob** is the built one (`knob_7mm`/`knob_10mm`, `KNOB_CHOSEN`); 9 silicone feet (`pe.stl`, D 8 x 1.5, recesses D 8.4 x 0.5; `case.feet()`); the v5 shelf is **off** (`SHELF_ON = False`): the board enters from below and sits 0.5 mm from the wall, so a 1.5 mm shelf blocks it (613 mm3 at 8 mm travel). Flexion: board alone 0.0492 mm, over soft silicone feet 0.057-0.069 (needs 70A+ feet). `student_v03/pcb/grade_fab.py` (KiCad python) = V3 grid Gerbers with copper pulled back to D 4.4 round the 10 countersunk holes; `case/GRADE_ESCAREADA.md` has the JLCPCB/PCBWay order texts (no home countersinking). Report: `case/FIT_CHECK.md` (cycle 5, then the cycle 4 as an annex).

- **Student V3 page and assembly manual (18 Nov):** `/etutti/studentV3/` (unlisted, noindex, Portuguese; `index.html` = concept, block diagram, KiCad schematic sheets as SVG in `esquema/`, parts by area and supplier, numbered exploded view, budget; `montagem.html` = ten-step manual, each step an exploded picture). Written by `student_v03/pagina.py` (texts and prices live there); pictures by `student_v03/case/passos.py` (CadQuery venv, ~3 min, run after `case.py` + `render.py`; steps 8-9 are drawn view-up = -z, lid face down as on the bench). Schematics: `kicad-cli sch export svg --exclude-drawing-sheet` on `kicad/student_v03.kicad_sch`. The 5 DRC *warnings* (via/track dangling) were analysed on 18 Nov: removing them cascades through whole routes (ends sit off a via's centre, KiCad's check is topological); the board was left as ordered. The lid's printed logo still reads "STUDENT · V2" (SPEC v3, paint only).
- **Student V3 photo-real renders (18 Nov):** Blender 5.2 (Cycles, OptiX) via `student_v03/case/blender_export.py` (CadQuery venv: writes `case/blender/build/` PLYs + manifest + KiCad GLB of the board; shots = the steps' cameras and offsets plus beauty shots) -> `case/render_blender.py` (`blender -b --python ... -- [shots] [--fast]`, ~10 min for all 17) -> `case/blender_finish.py` (lays the transparent PNGs on the paper colour, writes `etutti/studentV3/img/foto_*.jpg`). `pagina.py` uses `foto_<name>` when it exists and links the clay version. Gotchas: PLY import brings custom normals that smear flat plates (the mesh is rebuilt with `from_pydata`); use "Standard" view transform (AgX washes the cream paint); keep the same camera as pyvista and the numbered pins of `ancoras.json` still line up. `case/blender/{build,out}` are gitignored.

## eTutti Student V4 (21 Nov 2026) — SPEC R1V4 + R2V4, Phase A (studies)

`etutti/hardware/student_v04/`: Chat's `SPEC.md` (nomenclature **RnV4** = revision n of the V4 SPEC; reports cite the revision they meet).
Base = the V3's scripts and sources copied (no `fab/`, renders or generated output; V3/V2/V1 untouched); `README.md` has the run order.
Only the keyboard layout is fixed. **F2 chosen (R2V4):** main board only for the interface (Teensy, power, audio, connectors, screen,
encoders), **sensor rulers** (universal 4-key board, 74 x 14 x 1.2 mm, 2 layers, panel of 5 (88 x 84 mm), 4 TMAG5253 + 74HC595 + 2 JST SH 6-pin) on the case's
steps, one cap for all rows; 28 keys = 8 rulers (since R5V4: 32 keys, all rulers full; modules 48/64/80), each +16-key module = +4; **T3** = the lid presses key bodies against the board.
No multiplexers: one OUT line per row (pins 14/15/26/27), SCAN_DATA/SCAN_CLK = 2/3 (`pcb/PINOS.md`, the electronics-to-firmware contract).
- **Agents** (`.claude/agents/`): `design`, `eletronica`, `programacao-som` now list the V4 folders (see each file); new agent
  **`roteamento`** owns only routing (`pcb/rota/`, `ROTEAMENTO.md`): it starts **only after J approves the placement gate P**
  (`POSICIONAMENTO.md`), never moves a part (asks `eletronica` for a placement change instead), picks the method and justifies it, works in
  idempotent resumable stages (`pcb/rota/estado.json`, one commit per finished stage on a work branch, stages < ~10 min, long ones in
  the background) and accepts only DRC 0 errors **and 0 warnings**, 0 unconnected, parity 0, no sub-minimum tracks, no dangling ends, no
  plane islands.
- Reports (Portuguese, end with "Perguntas para o design"): `ELETRONICA.md` (E1 BOM review, E2 scan, E3 cost check, E4 USB pair, E5
  ruler), `FIT_CHECK.md` (design), `FIRMWARE.md` (programacao-som). Numbers regenerate with `student_v04/calculos_eletronica.py` and
  `fornecimento/precos_jlc.py` (JLCPCB parts library via plain curl, 2 s apart).
- **R3V4 (21 Nov, design part):** Gateron files in `student_v04/fornecimento/gateron/`: the **KS-20TO10B050NW-Y64 Orange** drawing (PDF, 2023-10-19:
  shoulder 5.00 +-0.05, grid hole 14.00 +0.03/-0.02 with a 1.50 +0.01/-0.05 plate, top 11.10, pegs 2 x D1.70 at 10.16, 38 gf, 4.10 travel,
  102/905 Gs) and the **KS-20T STEP** (a 2021 revision: it has a centre post and two stem posts, NOT the PDF's two pegs and central cross; use the
  PDF for pegs/stem, the STEP only for the cover/flange envelope; `estudos/ks20_step.py`). Latch window read off the drawing: 1.36 mm nominal
  (up to 1.84), so a **1.2 mm grade leaves 0.16 mm of vertical play, 1.6 mm sits inside the window**. **T3-G** model: `case/case_t3g.py`
  (patches `case_f2.py`: grade-ruler, no foam, no preload, deck 2.5, gap 1.0, M2 screws instead of pins), numbers in `estudos/t3g.py`;
  `FIT_CHECK.md` has the R3V4 section on top. The STEP's face-by-face reading is slow to redo: reuse `estudos/ks20_step.json`.
- **R6V4 (22 nov, design part):** case `CASE_LEN` 244 (+4 mm flat deck; 318/392/466 for 48/64/80; the 32-key lid fits a 250 mm FDM bed with 3 mm
  spare; MJF ~US$ 46). Ruler-to-ruler joint studied in `case/juncao_r6.py` (data: E1, E1c, E2, E2b, F) + `case/juncao_v6.py` (checks and figures
  `juncao_opcoes_r6.png`, `juncao_E2_r6.png`, `juncao_placa_r6.png`). **E1 is dead** (the ruler cannot slide in x: D1.7 pegs in D1.7 holes and M2 with 0.1 mm
  play; the contact row crosses the 1st peg). **E2 recommended** with the electronics' real parts (female SHOU HAN 1x5 H3.4 C55566451 at u 5.9 / 68.1 in the BACK lane
  v -6.9..-1.7 = J1/J2; bridge PCB 1.2 mm with two male C55213903): 6.2 mm under the ruler in a 6.9 mm pocket (0.7 mm spare, to confirm), 0 mm3 at 32/48/64/80 keys,
  tray cradle (`CRADLE_OPT` in `case_r4.py`), 70 % of the back rail left. Board -> 1st ruler: rigid plug impossible (gap 2.45 / 11.7 mm, step 0/2/4/7 mm) -> SH pigtail ending
  in a male 1x5 (about 9 mm rows 2/4, 17 mm rows 1/3). `layout_r4.LINK = "E2"` (D and A still selectable). Report: `student_v04/FIT_CHECK.md` top section.
- Findings worth remembering: the 74HC595D (C5947) is JLCPCB **Basic** (the 164/4094/4017 are all Extended); no Basic connector, jack,
  LDO or ESD part exists; TMAG5253 BA tON is 20 typ / **45 us max** (UA 55 / 130); F2 costs about 12-22 % less than F1 (US$ 292-371 vs 332-477, MJF case print US$ 51) at the minimum order
  (estimates marked in `ELETRONICA.md`); JLCPCB WMSC search endpoints are blocked for curl, the assembly parts-library endpoint works.
- **R4V4 (21 nov, design part):** decisions applied in `student_v04/case/case_r4.py` (built on `case_t3g.py`/`case_f2.py`; positions in
  `case/layout_r4.py`, which also feeds `planta_v4.py` -> `renders/planta_geral_v4.png`, `planta_interface_v4.png` and `corte_v4.py` ->
  `renders/corte_interface_v4.png`): grade-regua 1.6 mm FR-4 own drawing, deck 2.5 mm with 5/8/11/14 posts (never on a ruler's junction), gap 1.0,
  head top ZR + 22.8, non-magnetic M2 into an insert in a real D6 boss of the step (the R3V4 model had only the 2.8 mm rail), ruler hole D2.2,
  KS-20 Orange. Interface modelled for real: USB-C hole at y 10 (module and H101 5.5 mm left), battery 503450 under the board at
  (17.4..51.4; 40..90) long side along y, Dayton CE28MB-8 (D28 x 4.5; box chamber 10.4 cm3, `estudos/acustica.py`), OLED window/slit, lid posts on H1..H4
  (D5.4, M2 insert), the two V3-style wall bosses (7;12)/(7;88) removed (they sat on the USB-C). **Plan corner radius R6, not the V3's R9** (R9 cuts the
  board and the USB-C). **Ruler connectors (task 3):** the SH header cannot sit on the ruler's axis (the key pegs and sensors are there, windows
  of only 6.6 mm); contract = both headers in the BACK lane (y -7.5..-1.35 of the axis), mouth to -y, IN centre x 5.9, OUT x 68.1 along the ruler, plug passes
  under the next (higher) row's ruler through a notch in that row's front rail; M2 positions per row (1: 18.5/55.5, 2: 37/55.5, 3 and 4: 18.5/37)
  so no boss meets a notch; custom SH cables 15 mm (row links) and 25 mm (board to first ruler). Details and open questions in `student_v04/FIT_CHECK.md`.
  `case/out/` stays git-ignored; `estudos/r4v4.json` keeps the numbers.
- **R8V4 (22 nov, design part):** the link **H is approved and applied** in the official model (`case_r4.py`, `LINK = "H"`): SH headers IN u 5.9 / OUT u 47.5, mouth to -y (SM06B-SRSS-TB or clone C56123098, 2.95 high; plug 3.6 x 7.0 x 2.45), pinout P6s, stock jumper A06SR06SR30K51B (free wire 45.8 or 50.8 mm, NOT measured), cable recesses cut from the tray's rails (floor stays 2.0 mm), no bridge/cradle (E2/G gone). **Case 244 x 102 mm**: the back outer face moved to y -2 (`layout_r4.Y_BACK`; board and interface keep their y) so row 4's loop closes with 50.8 mm (0.79 mm margin; +US$ 0.64). **A pair of M2 per row is impossible** (the only gaps between key bodies are u 18.5/37/55.5; plugs of the row in front take the rest): 11 M2 (rows 2 and 4 at u 37, row 3 at 18.5, row 1 at 18.5 + 55.5, R3.1 also 55.5); ruler holes unchanged. 5 interior posts (107.7;68.69) (116.95;52.67) (181.7;36.65) (200.2;68.69) (218.7;36.65), 6 wall posts x 102.5/176.6/234 at y 5 and 93. Ruler stiffness (3 N, grillage with torsion, `estudos/rigidez_regua_r8.py`) 0.028 mm worst; M2 do not matter for it. Fit check 32 keys: 0 mm3 with both cable lengths. A ribbon jumper (instead of loose wires) does not fit the U loop: risk to check at purchase. `ligacao_h.py` is the shared analysis engine (`r8`, `figuras`); `layout_r4.RECESS` is filled lazily from it (`ensure_recess`). **New project rule (J): nothing is bought until the whole prototype is closed, not even samples; doubts only the real part answers stay as risks and the design must be robust to them.**
- **R5V4 (21 nov, design part): 32 keys, full rulers.** Rows (first key x): 1 A3-F#5 (98.45), 2 G3-E5 (89.2), 3 G#3-F5 (98.45), 4 F#3-D#5 (89.2, ruler
  from 79.95, aligned with row 2); modules add 16 keys: **32 / 48 / 64 / 80** (8 / 12 / 16 / 20 rulers). Every key figure now shows the **note name on each
  key** (project rule from J: naturals white, sharps black, C and F diagonal checkerboard; `planta_v4.key_cap`, names from `layout_r4.note_name`).
  `layout_r4.ROWS` overrides `geometria.py`'s 28-key rows for the case (that file is not the design agent's; `pcb/grade_fab.py` still reads 28 keys).
  Case length **252 -> 240 mm** (ruler body end 237.0 + 1.0 + 2.0 wall; modules 314 / 388 / 462); the 32-key lid now fits a 250 mm FDM bed.
  Outer finish proposed: **2.0 x 2.0 mm 45 deg chamfer on the top outer edge** (the right end follows the stepped deck in one ruled loft, corners are
  cones) and 1.0 x 1.0 on the bottom edge; plan corners R6 outside / R4 inside are now in the model (`case_r4.round_and_chamfer_lid`, R4V4 only drew them);
  the USB-C cut was lengthened to 4.5 mm because the R6 corner left a 0.2 mm sliver. M2 of row 4 = row 2's (37 / 55.5). Fit check 32/48/64/80: 0 mm3 in every
  pair (tolerance cases +0.5 mm: 8-21 mm3 on the step-3 ramp as before). Print (MJF PA12): 158.9 / 211.6 / 264.1 / 316.8 cm3, ~US$ 44 / 59 / 73 / 88.
  Ruler link: **D chosen by electronics and design** (4 SH-6 cables of 25 mm board -> J1 of the first ruler + 5-wire soldered link between rulers of a row,
  pads 1.4 x 0.7 at u 2.1 / 71.9; J2 stays on the ruler without a cable): `layout_r4.LINK = "D"`, `link_box`; 0 mm3 vs tray, pegs, sensors, screws, rulers at
  every junction (32-80 keys); the OUT plug windows are gone (`J2_FITTED = False` would also drop the J2 header notch). Option C (FPC 3.9 mm deep) hits the pegs. Report: `student_v04/FIT_CHECK.md`
  R5V4 section; numbers in `estudos/r5v4.json`, `case/out/ligacao_v5.json`. Heredocs in Bash lose backslashes: edit strings with `\n` through the Edit tool.

### Student V4, R7V4 (22 Nov 2026): general rules and the H-link study

- **General rules (J's decision, valid for every later revision; also in `.claude/agents/*.md`):** (1) **only the 32-key version is detailed**
  (model, fit check, figures, cost, assembly, firmware); 48/64/80 keys get only a short "validation of the modular concept" section (the universal
  ruler repeats, the chain and the scan grow without changing the main board, the case grows by the same length rule), with no figures, cost tables
  or per-size fit checks; (2) **only the modular Student V4** is worked on, compiled and checked: Student V01, V2, V3, Lite, Viaggio, Pocket,
  eTuttino, eTutti and eTuttiChorus stay in the repo frozen (not updated, not kept compiling, nothing in the V4 reports depends on them);
  (3) the V4 firmware gets its **own sketch**, `etutti/firmware/student_v4/` (created by `programacao-som`); the shared `etutti/firmware/etutti_synth/`
  is frozen.
- **H link study (design part, nothing applied to the official case):** `student_v04/case/ligacao_h.py` (CadQuery venv python, ~6 s; plain
  numpy raster at 0.1 mm over `layout_r4.py`, does not touch `case_r4.py`) writes `case/out/ligacao_h.json` and `case/renders/ligacao_h_*_r7.png`.
  The JST SH datasheet PDF (`jst-mfg.com/product/pdf/eng/eSH.pdf`) has font-obfuscated text (digits lost): header 4.3, plug 7.6 x 5.0 x 3.9 and the
  4 mm minimum bend radius are still "conferir". Result and open questions in `student_v04/FIT_CHECK.md` (R7V4 section on top).

- **R10V4 (22 nov 2026, design part): 4 x R8, robust base.** The standard rulers are the **R8** (8 positions, 148 mm, one per row; 32 keys = 4 x R8) and the
  **R4** (74 mm, only ends a longer row, always at the right/treble end); both have an SH IN header at u 5.9 and an SH OUT header 26.5 mm from the right end
  (R8 u 121.5, R4 u 47.5), same P6s pinout. The 32-key model has no ruler-to-ruler junction, no junction cable and no junction recess: only the board's 4
  cables (45.8 / 50.8 mm free wire) to each row's R8 IN; the R8's OUT header stays unplugged. Model: `case/layout_r4.py` + `case/case_r4.py` (`RULER_L` =
  148). Base: continuous rails, the 2 mm trench between rows closed by a **riser** up to the lower neighbour's rail top (row 1: a 2 mm thicker front wall),
  end walls, tunnels cut for the 4 board cables (`cable_cutter`, chain of slots: `_flat_prism` self-intersects on tight curves and breaks the cut), notches for
  headers, the IN plug (through the riser) and the 595/C5 that stand over the front rail. **Two M2 per ruler in a heat-set insert (no self-tapping):** R8 has four
  holes u 18.5 / 37 / 111 / 129.5 (v +5.2), rows 1 and 3 use 18.5 + 129.5, rows 2 and 4 use 37 + 111 (`case/fixacao_r10.py`; they stay free in the 48/64/80
  arrangements). Base 84.9 cm3 (was 69.9: +15.0 cm3 = about +US$ 4.2 MJF). Ruler bending 0.015 mm at 3 N (`estudos/rigidez_regua_r10.py`). OLED: glass 26.7 x
  19.26 centred on the module's board, the viewing area (21.74 x 10.86) centred on the window; the 1.9 mm offset between them is the SPEC's assumption, not
  confirmed on a real module. Figures `case/renders/*_r10.png` (`planta_v4.py`, `corte_v4.py`, `corte_base_r10.py`, `iso_base_r10.py`). Older rules still
  hold: only 32 keys detailed, only the Student V4, nothing is bought before the prototype closes. The Sennheiser ME 3 and the 9-10 V boost are out of the
  project (microphones: electret and dynamic through the 3.5 mm jack only).
- **R11V4 (22 nov 2026, design part): real OLED, fasteners by use, R8 without OUT, detailed base drawings.** (1) **OLED = Adafruit 326** (SSD1306, 3.3 V, I2C, two
  STEMMA QT / Qwiic SH-4 connectors on the module's BACK, edges facing outwards): every number read from Adafruit's Eagle board file
  (`Adafruit-128x64-Monochrome-OLED-PCB`, UG-2864HSWEG01 panel: glass 26.7 x 19.26, viewing area 21.744 x 10.864, 2.098 mm off the glass centre; board
  29.21 x 31.75 with two lugs, holes D2.5 at 24.13 x 26.67) in `case/oled_r11.py`. PCB 1.6 / glass+tape 1.5 are ASSUMED (6.2 mm total in the shop). Viewing area
  centred on the 24 x 13 window (margins 1.13 x 1.07); module turned so the header edge faces +y (firmware rotates the image 180 deg); four lid posts D4.2 on the real
  holes, PT M2 x 4; the right-hand plug exits at x 53.6, the Qwiic cable makes an S (R 3) down the existing board slit (J401 is now an SH-4, the electronics'
  change). (2) **The "no self-tapping" rule is GONE: the cheapest joint that is stable.** Study `estudos/parafusos_r11.py`: ruler = **through M2 bolt + nut in a hex
  pocket from the tray's underside** (M2 x 10/12/14/16 by row; the D6 boss is under the 6.4 mm an insert needs; unlimited reuse; ~US$ 0.5), lid posts / wall
  bosses / H1..H4 / OLED = **thread-forming M2** straight into the post (pilot 1.75, 7 mm deep; D5.0 is right for PT, too thin for an insert). Reuse of PT in PA12
  (5-10) and the boss rules are estimates to be tested on the prototype. (3) **Ruler variants R8 / R8E / R4 / R4E (OUT only on a ruler that extends):** 32 keys = 4 x R8
  with no OUT header, plug or notch (`layout_r4.OUT_ON_LAST = False`); frees u 129.5 in rows 2 and 4 (pair 37 + 129.5 = 92.5 mm, was 74). (4) **Base drawings**
  `case/iso_base_r11.py`: OpenCascade HLR edges of the real tray, numbered supports with a legend, notes on the key squares, hidden-line view, PDF.
  Update the same day: the R8's 74HC595 is at u 74, v 0 (rot 90) per `pcb/regua/posicao_regua8.json`, which `ligacao_h.py` now reads; no front-rail cut-out for it; row 4's bolt uses a thin (1.2 mm) M2 nut. The J accepted: 102 mm depth, OLED orientation B, through-bolt + nut on rulers, thread-forming on lid/OLED, mandatory PT reassembly test and OLED measurement before closing; the 80-key middle R8 is an R8E.

## eTutti Slim (24 nov 2026) — start here

`etutti/hardware/slim/`: the newest instrument, **independent of the Student V4** (own folder; the V4 is only a source to learn from, never referenced or changed). Chat owns `SPEC.md` (R1SL, R2SL...; Portuguese) and `conceito/`; Code answers in `ELETRONICA.md`, `FIRMWARE.md`, `FIT_CHECK.md` (each ends with "Perguntas para o design"). Three stages with gates the J approves: **A** components + logic (stage 1), **B** placement (ruler and main board in separate sessions), **C** routing (idem). Nothing is quoted, bought or ordered until the J says so.
- Owners (also in `.claude/agents/*.md`): eletronica = `slim/pcb/`, `slim/ELETRONICA.md`; programacao-som = `etutti/firmware/slim/` (sketch for `teensy:avr:teensy41`), `slim/FIRMWARE.md`; design = `slim/case/`, `slim/estudos/`, `slim/modelos/`, `slim/FIT_CHECK.md`; roteamento = nothing until gate B.
- "Only the V4" (R7V4 rule) applies to the old versions, not to the Slim.
- **GitHub here:** `gh auth status` says the token is invalid but access works; `gh pr` (GraphQL) is blocked. Open and merge PRs through the REST API: `gh api repos/dataehora/beatconfused/pulls ...` and `.../pulls/<n>/merge`.
- **Git gotcha (24 nov):** `git checkout`/`switch`/`merge` that touch the working tree fail with `error: cannot stat 'etutti': Invalid argument`; build commits with plumbing (temporary index + `commit-tree` + `update-ref`) and push the ref.
