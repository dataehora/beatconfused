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
  for no home button while it's being built). Two models: **eTuttino**
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
  - **Manual pictures**: `etutti/hardware/case/manual_render.py` (CadQuery
    venv + PyVista). It exports the main and controls boards with
    `kicad-cli pcb export stl` (`--board-only` and `--no-board-body`
    separately, so the board and its parts get their own colours; the GLB
    export of the main board hangs VTK's reader), places them in the case
    STLs, and takes the stack / controls-board bodies / panel parts from
    `fit_check.py`. One figure per assembly step + a capped section
    (`clip_closed_surface`) → `etutti/manuais/img/*.jpg` (+ `-sm`). The
    manual's `lightbox.js` opens the full image on click. (`assembly3d.py`,
    the v0.5 VRML version, is gone.)
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
        `case/manual_render.py` now.
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
