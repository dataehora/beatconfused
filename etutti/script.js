/* ============================================================
   eTUTTI — browser front-end for a Teensy-based controller/synth.

   Two models share this page:
     - eTuttino (the one being built): 34 round keys in a chromatic
       button-accordion layout (C-griff or B-griff), G3–G6, laid out like
       a Castagnari Magica K2 (41 keys), on magnetic
       (Hall-effect) switches: a Teensy 4.0 reads how far each key is down,
       so the real keys play with velocity.
     - eTutti (the full instrument): only a preview render for now.

   The Teensy runs etutti/firmware/etutti_synth (Teensy Audio Library on
   an SGTL5000 Audio Board) and enumerates over USB as a class-compliant
   MIDI device. This page talks to it with the Web MIDI API:
     - the computer keyboard (optional) and the on-screen keys send notes,
     - the Synth panel sends Control Change messages: instrument presets
       (accordion reed synthesis with a register switch, or recorded
       piano / bass / guitar samples), tone and room ambience,
     - the C/B-griff switch is sent too, so the real keys follow it,
     - notes played on the real keys light up on the on-screen ones, and
       the "eTuttino keys" panel sets their velocity curve, restarts their
       calibration and shows a live key test.
   No sound is made in the browser — the Teensy's audio output is the
   instrument.
   ============================================================ */
(function () {
  "use strict";

  // CC numbers shared with the firmware (keep in sync with etutti_synth.ino).
  const CC = {
    volume: 7,
    layout: 24,
    instrument: 25,
    register: 26,
    reedTuning: 27,
    release: 72,
    attack: 73,
    tone: 74,
    ambience: 91,
    decay: 75,
    sustain: 79,
    synthWave: [20, 21, 22],
    synthOctave: [102, 103, 104],
    keyVelocity: 9,
    calibrate: 14,
    keyTest: 15,
    allSoundOff: 120,
    allNotesOff: 123,
  };

  const NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];

  /* ------------------------------------------------------------
     eTuttino LAYOUT — chromatic button accordion.
     Row 1 is nearest the player (drawn at the bottom), row 4 furthest.
     Laid out like the Castagnari Magica K2: rows 1-3 run A3..D♯6,
     G3..G6 and G♯3..D6; row 4 repeats the start of row 1 (A3..C5).
     Along a row each key is a minor third (3 semitones) above the last;
     rows are staggered half a key, so a diagonal step to the next row is
     one semitone (up in C-griff, down in B-griff — B-griff is C-griff's
     mirror image, rows 1 and 3 swapped).
       x    = horizontal position in key units (19.05 mm on the PCB)
       col  = matrix column on the PCB/firmware (row = matrix row)
       code = computer key (KeyboardEvent.code). The computer's rows are
              staggered too, so the shape under the fingers matches. On
              ABNT2, Slash/IntlRo are the ; and / keys, BracketLeft/Right
              the ´ and [ keys, Backslash the ] key; the last key of row 2
              (G6) has no computer key.
     Keep in sync with FIRST_NOTE/FIRST_COL in etutti_synth.ino and with
     ROWS in etutti/hardware/generate.py.
     ------------------------------------------------------------ */
  const FIRST_NOTE = {
    c: [57, 55, 56, 57], // A3, G3, G♯3, A3
    b: [56, 55, 57, 56], // G♯3, G3, A3, G♯3
  };
  const ROWS = [
    { count: 11, x0: 0, col0: 1, codes: ["KeyZ", "KeyX", "KeyC", "KeyV", "KeyB", "KeyN", "KeyM", "Comma", "Period", "Slash", "IntlRo"] },
    { count: 13, x0: -0.5, col0: 0, codes: ["KeyA", "KeyS", "KeyD", "KeyF", "KeyG", "KeyH", "KeyJ", "KeyK", "KeyL", "Semicolon", "Quote", "Backslash", null] },
    { count: 11, x0: 0, col0: 1, codes: ["KeyW", "KeyE", "KeyR", "KeyT", "KeyY", "KeyU", "KeyI", "KeyO", "KeyP", "BracketLeft", "BracketRight"] },
    { count: 6, x0: 0, col0: 1, codes: ["Digit3", "Digit4", "Digit5", "Digit6", "Digit7", "Digit8"] },
  ];
  const LAYOUT = [];
  ROWS.forEach((row, r) => {
    for (let i = 0; i < row.count; i += 1) {
      LAYOUT.push({ row: r, step: i, col: row.col0 + i, x: row.x0 + i, code: row.codes[i] });
    }
  });
  const CODE_TO_KEY = new Map(LAYOUT.filter((k) => k.code).map((k) => [k.code, k]));
  const GRID_UNITS_X = 13; // x from -0.5 to 11.5, one key wide each
  const GRID_UNITS_Y = 4;
  const MAX_TRANSPOSE = 3; // octaves either way
  const VELOCITY_STEP = 16;
  const MONITOR_LINES = 40;

  /* ------------------------------------------------------------
     ACCORDION REGISTER — one bit per reed set, as in the firmware:
     16' low reed in cassotto, 8' M1 open, 8' M2 in cassotto, 4' piccolo.
     Named combinations follow the usual accordion register names.
     ------------------------------------------------------------ */
  const REED = { low: 1, m1: 2, m2: 4, high: 8 };
  const NAMED_REGISTERS = [
    { mask: 15, key: "master" },
    { mask: 6, key: "violin" },
    { mask: 2, key: "clarinet" },
    { mask: 3, key: "bandoneon" },
    { mask: 10, key: "oboe" },
    { mask: 9, key: "organ" },
    { mask: 8, key: "piccolo" },
    { mask: 1, key: "bassoon" },
  ];
  // Name for any mask: M1 and M2 both count as "M" (8').
  function registerNameKey(mask) {
    const l = mask & REED.low ? 1 : 0;
    const m = (mask & REED.m1 ? 1 : 0) + (mask & REED.m2 ? 1 : 0);
    const h = mask & REED.high ? 1 : 0;
    const code = `${l ? "L" : ""}${"M".repeat(m)}${h ? "H" : ""}`;
    const names = { L: "bassoon", M: "clarinet", H: "piccolo", LM: "bandoneon", MM: "violin", MH: "oboe", LH: "organ", LMH: "harmonium", LMM: "accordion", LMMH: "master" };
    return { code, name: names[code] || null };
  }

  /* ------------------------------------------------------------
     INSTRUMENT PRESETS — raw CC values (see the firmware for units).
     instrument: 0 accordion (reed synthesis), 1 piano, 2 bass, 3 guitar
     (recorded samples). "accordion" is the default and what Reset
     restores: dry tuning, register MM (both 8' reeds — they differ only in
     timbre, open vs cassotto). Jazz is the same reeds tuned slightly wet.
     Custom presets will slot into this same shape later.
     ------------------------------------------------------------ */
  const DEFAULT_PRESET = "accordion";
  const SYNTH_INSTRUMENT = 4;
  const ACCORDION_DEFAULTS = { register: 6, ccReedTuning: 0, ccAttack: 14, ccRelease: 21 };
  // Synth: three oscillators (wave 0 sine, 1 triangle, 2 saw, 3 square —
  // the firmware uses band-limited saw/square), level, detune (64 = in
  // tune), octave (-1 / 0 / +1), plus decay/sustain for the ADSR.
  const SYNTH_DEFAULTS = {
    oscWave1: 2, ccOsc1Level: 100, ccOsc1Detune: 64, oscOct1: 0,
    oscWave2: 2, ccOsc2Level: 80, ccOsc2Detune: 73, oscOct2: 0,
    oscWave3: 3, ccOsc3Level: 50, ccOsc3Detune: 64, oscOct3: -1,
    ccDecay: 49, ccSustain: 89,
  };
  const BASE = { ...ACCORDION_DEFAULTS, ...SYNTH_DEFAULTS };
  const PRESETS = {
    accordion: { ...BASE, instrument: 0, ccVolume: 90, ccTone: 110, ccAmbience: 25 },
    accordionJazz: { ...BASE, instrument: 0, ccReedTuning: 6, ccVolume: 90, ccTone: 100, ccAmbience: 32 },
    piano: { ...BASE, instrument: 1, ccVolume: 100, ccTone: 127, ccAmbience: 30 },
    bass: { ...BASE, instrument: 2, ccVolume: 105, ccTone: 100, ccAmbience: 15 },
    guitar: { ...BASE, instrument: 3, ccVolume: 100, ccTone: 122, ccAmbience: 25 },
    synth: { ...BASE, instrument: SYNTH_INSTRUMENT, ccAttack: 6, ccRelease: 33, ccVolume: 90, ccTone: 88, ccAmbience: 25 },
  };
  // Which settings matter for which engine (for the "modified" marker and
  // for showing the right panels).
  const ACCORDION_ONLY = ["register", "ccReedTuning"];
  const SYNTH_ONLY = Object.keys(SYNTH_DEFAULTS);
  const ENVELOPE = ["ccAttack", "ccRelease"];
  const SYNTH_RADIOS = ["oscWave1", "oscWave2", "oscWave3", "oscOct1", "oscOct2", "oscOct3"];
  function settingMatters(key, inst) {
    if (ACCORDION_ONLY.includes(key)) return inst === 0;
    if (SYNTH_ONLY.includes(key)) return inst === SYNTH_INSTRUMENT;
    if (ENVELOPE.includes(key)) return inst === 0 || inst === SYNTH_INSTRUMENT;
    return true;
  }

  const STORAGE = {
    griff: "etutti.griff",
    keyboard: "etutti.computerKeyboard",
    preset: "etutti.preset",
    keyVelocity: "etutti.keyVelocity",
  };

  function load(key, fallback) {
    try {
      const v = window.localStorage.getItem(key);
      return v === null ? fallback : v;
    } catch (error) {
      return fallback;
    }
  }

  function save(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (error) {
      // private mode etc. — just don't remember
    }
  }

  const els = {
    modelCards: document.querySelectorAll(".model-card"),
    renderEtuttino: document.getElementById("renderEtuttino"),
    renderEtutti: document.getElementById("renderEtutti"),
    wipPanel: document.getElementById("etuttiWip"),
    etuttinoSections: document.getElementById("etuttinoSections"),
    connectBtn: document.getElementById("connectBtn"),
    connLight: document.getElementById("connLight"),
    connStatus: document.getElementById("connStatus"),
    outputSelect: document.getElementById("outputSelect"),
    channelSelect: document.getElementById("channelSelect"),
    grid: document.getElementById("buttonGrid"),
    griffToggle: document.getElementById("griffToggle"),
    griffCheckbox: document.getElementById("griffCheckbox"),
    keyboardToggle: document.getElementById("keyboardToggle"),
    keyboardCheckbox: document.getElementById("keyboardCheckbox"),
    keysHint: document.getElementById("keysHint"),
    octaveDown: document.getElementById("octaveDown"),
    octaveUp: document.getElementById("octaveUp"),
    octaveValue: document.getElementById("octaveValue"),
    velocityDown: document.getElementById("velocityDown"),
    velocityUp: document.getElementById("velocityUp"),
    velocityValue: document.getElementById("velocityValue"),
    panicBtn: document.getElementById("panicBtn"),
    sendAllBtn: document.getElementById("sendAllBtn"),
    resetBtn: document.getElementById("resetSynthBtn"),
    presetInputs: document.querySelectorAll('input[name="preset"]'),
    presetModified: document.getElementById("presetModified"),
    accordionControls: document.getElementById("accordionControls"),
    registerDots: document.querySelectorAll(".register-dot"),
    registerCode: document.getElementById("registerCode"),
    registerName: document.getElementById("registerName"),
    registerPresets: document.getElementById("registerPresets"),
    synthControls: document.getElementById("synthControls"),
    envelopeControls: document.getElementById("envelopeControls"),
    synthEnvelopeOnly: document.querySelectorAll(".synth-envelope-only"),
    sliders: document.querySelectorAll("[data-cc]"),
    monitor: document.getElementById("midiMonitor"),
    clearMonitorBtn: document.getElementById("clearMonitorBtn"),
    keyVelocityInputs: document.querySelectorAll('input[name="keyVelocity"]'),
    calibrateBtn: document.getElementById("calibrateBtn"),
    calibrateStatus: document.getElementById("calibrateStatus"),
    keyTestToggle: document.getElementById("keyTestToggle"),
    keyTestCheckbox: document.getElementById("keyTestCheckbox"),
  };

  function tr(key, fallback, vars) {
    return window.BC_I18N ? window.BC_I18N.t(key, vars) : fallback;
  }

  // ---- state ----
  let midiAccess = null;
  let output = null;
  let input = null;
  let channel = 0; // 0-15 on the wire, shown as 1-16
  let transpose = 0; // in octaves
  let velocity = 100;
  let griff = load(STORAGE.griff, "c") === "b" ? "b" : "c";
  let keyboardOn = load(STORAGE.keyboard, "on") !== "off";
  let activePreset = PRESETS[load(STORAGE.preset, DEFAULT_PRESET)] ? load(STORAGE.preset, DEFAULT_PRESET) : DEFAULT_PRESET;
  const heldByKey = new Map(); // KeyboardEvent.code -> MIDI note actually sent
  const heldByPointer = new Map(); // pointerId -> MIDI note
  const soundingCount = new Map(); // MIDI note -> how many sources hold it
  const remoteNotes = new Set(); // notes the Teensy reports from its own keys
  // The eTuttino's sounds in the browser (websynth.js), off until the user
  // switches "Listen in this browser" on.
  const webSynth = window.EtuttiWebSynth ? window.EtuttiWebSynth.create() : null;
  let keyTestOn = false;
  const keyPress = new Array(LAYOUT.length).fill(0); // key test: 0 .. 1 per real key
  let statusKey = "status.idle";
  let statusVars = null;

  function noteName(midi) {
    return `${NOTE_NAMES[((midi % 12) + 12) % 12]}${Math.floor(midi / 12) - 1}`;
  }

  function isSharp(midi) {
    return [1, 3, 6, 8, 10].includes(((midi % 12) + 12) % 12);
  }

  // Note a key plays, before transposition.
  function baseNote(key, system) {
    return FIRST_NOTE[system || griff][key.row] + 3 * key.step;
  }

  function keyNote(key) {
    return baseNote(key) + 12 * transpose;
  }

  // Row 1 at the bottom.
  function slotOf(row) {
    return GRID_UNITS_Y - 1 - row;
  }

  /* ============================================================
     MODEL PICKER + RENDERS
     ============================================================ */
  const NS = "http://www.w3.org/2000/svg";

  function svgEl(tag, attrs) {
    const el = document.createElementNS(NS, tag);
    Object.keys(attrs).forEach((name) => el.setAttribute(name, String(attrs[name])));
    return el;
  }

  // A small "product shot": rounded case (aluminium or plastic), a
  // recessed plate and round accordion-style buttons.
  function renderModel(container, keys, unitsX, unitsY, finish) {
    const u = 20;
    const pad = 10;
    const w = unitsX * u + pad * 2;
    const h = unitsY * u + pad * 2;
    const svg = svgEl("svg", { viewBox: `0 0 ${w} ${h + 6}`, class: `model-svg model-svg-${finish}`, role: "presentation", focusable: "false" });
    svg.appendChild(svgEl("rect", { x: 2, y: 6, width: w - 4, height: h - 2, rx: 9, class: "model-shadow" }));
    svg.appendChild(svgEl("rect", { x: 0, y: 0, width: w, height: h, rx: 9, class: "model-case" }));
    svg.appendChild(svgEl("rect", { x: pad - 3, y: pad - 3, width: w - 2 * pad + 6, height: h - 2 * pad + 6, rx: 4, class: "model-plate" }));
    keys.forEach((k) => {
      const cx = pad + (k.x - k.xMin + 0.5) * u;
      const cy = pad + (k.slot + 0.5) * u;
      svg.appendChild(svgEl("circle", { cx, cy: cy + 1.2, r: u / 2 - 1.6, class: "model-cap-side" }));
      svg.appendChild(svgEl("circle", { cx, cy, r: u / 2 - 1.6, class: isSharp(k.note) ? "model-cap model-cap-dark" : "model-cap" }));
    });
    container.innerHTML = "";
    container.appendChild(svg);
  }

  function renderModels() {
    renderModel(
      els.renderEtuttino,
      LAYOUT.map((k) => ({ x: k.x, xMin: -0.5, slot: slotOf(k.row), note: baseNote(k) })),
      GRID_UNITS_X,
      GRID_UNITS_Y,
      "aluminium",
    );
    // eTutti preview: a full 5-row C-griff, 12-13 keys per row.
    const full = [];
    const starts = [45, 43, 44, 42, 43];
    starts.forEach((first, r) => {
      const offset = r % 2 === 0 ? 0 : -0.5;
      const count = r % 2 === 0 ? 12 : 13;
      for (let i = 0; i < count; i += 1) full.push({ x: offset + i, xMin: -0.5, slot: 4 - r, note: first + 3 * i });
    });
    renderModel(els.renderEtutti, full, 13, 5, "plastic");
  }

  function selectModel(model) {
    els.modelCards.forEach((card) => {
      const on = card.dataset.model === model;
      card.classList.toggle("is-selected", on);
      card.setAttribute("aria-pressed", String(on));
    });
    const isEtuttino = model === "etuttino";
    els.etuttinoSections.hidden = !isEtuttino;
    els.wipPanel.hidden = isEtuttino;
    if (!isEtuttino) releaseEverything();
  }

  els.modelCards.forEach((card) => {
    card.addEventListener("click", () => selectModel(card.dataset.model));
  });

  /* ============================================================
     STATUS + MONITOR
     ============================================================ */
  const STATUS_FALLBACKS = {
    "status.idle": "Not connected. Plug in the Teensy and press Connect.",
    "status.unsupported": "This browser has no Web MIDI. Use Chrome or Edge on a computer.",
    "status.denied": "MIDI access was refused. Allow it in the address bar and try again.",
    "status.noDevice": "MIDI is on, but no device was found. Is the Teensy plugged in with USB Type set to MIDI?",
    "status.pickDevice": "Choose your Teensy in the list.",
    "status.connected": "Connected to {name}.",
    "status.disconnected": "{name} was unplugged.",
  };

  function renderStatus() {
    els.connStatus.textContent = tr(statusKey, STATUS_FALLBACKS[statusKey], statusVars || undefined);
    els.connStatus.classList.toggle("is-error", statusKey === "status.unsupported" || statusKey === "status.denied");
    els.connLight.classList.toggle("is-on", statusKey === "status.connected");
  }

  function setStatus(key, vars) {
    statusKey = key;
    statusVars = vars || null;
    renderStatus();
  }

  function hex(bytes) {
    return Array.from(bytes, (b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ");
  }

  function describe(bytes) {
    const [status, d1, d2] = bytes;
    const type = status & 0xf0;
    const ch = (status & 0x0f) + 1;
    if (type === 0x90 && d2 > 0) return `ch${ch} Note On  ${noteName(d1)} vel ${d2}`;
    if (type === 0x80 || (type === 0x90 && d2 === 0)) return `ch${ch} Note Off ${noteName(d1)}`;
    if (type === 0xb0) return `ch${ch} CC ${d1} = ${d2}`;
    if (type === 0xa0) return `ch${ch} Poly pressure ${d1} = ${d2}`;
    if (type === 0xe0) return `ch${ch} Pitch bend ${(d2 << 7) | d1}`;
    return "";
  }

  function logMidi(direction, bytes) {
    const line = document.createElement("div");
    line.className = direction === "out" ? "monitor-out" : "monitor-in";
    line.textContent = `${direction === "out" ? "→" : "←"} ${hex(bytes).padEnd(9)}  ${describe(bytes)}`;
    els.monitor.prepend(line);
    while (els.monitor.childElementCount > MONITOR_LINES) {
      els.monitor.lastElementChild.remove();
    }
  }

  // Notes the Teensy plays from its own keys light up here too. In key
  // test mode it also streams every key's position as Polyphonic
  // Aftertouch on channel 16 (data 1 = key index in LAYOUT order); those
  // aren't logged, they'd flood the monitor.
  function handleIncoming(bytes) {
    if (bytes[0] === 0xaf) {
      if (keyTestOn && bytes[1] < keyPress.length) {
        keyPress[bytes[1]] = bytes[2] / 127;
        paintPress(bytes[1]);
      }
      return;
    }
    logMidi("in", bytes);
    const type = bytes[0] & 0xf0;
    if (type === 0x90 && bytes[2] > 0) remoteNotes.add(bytes[1]);
    else if (type === 0x80 || type === 0x90) remoteNotes.delete(bytes[1]);
    else return;
    paintNote(bytes[1]);
  }

  /* ============================================================
     MIDI OUTPUT
     ============================================================ */
  function send(bytes) {
    if (!output || output.state !== "connected") return;
    try {
      output.send(bytes);
      logMidi("out", bytes);
    } catch (error) {
      // A port that vanished between the state check and send() throws;
      // the statechange handler will update the UI.
    }
  }

  function noteOn(note) {
    const count = soundingCount.get(note) || 0;
    soundingCount.set(note, count + 1);
    if (count === 0) {
      send([0x90 | channel, note, velocity]);
      if (webSynth) webSynth.noteOn(note, velocity);
    }
    paintNote(note);
  }

  function noteOff(note) {
    const count = soundingCount.get(note) || 0;
    if (count <= 1) {
      soundingCount.delete(note);
      if (count === 1) {
        send([0x80 | channel, note, 0]);
        if (webSynth) webSynth.noteOff(note);
      }
    } else {
      soundingCount.set(note, count - 1);
    }
    paintNote(note);
  }

  function releaseEverything() {
    heldByKey.clear();
    heldByPointer.clear();
    const notes = Array.from(soundingCount.keys());
    notes.forEach((note) => send([0x80 | channel, note, 0]));
    if (webSynth) webSynth.allOff();
    soundingCount.clear();
    notes.forEach(paintNote);
  }

  function panic() {
    releaseEverything();
    for (let ch = 0; ch < 16; ch += 1) {
      send([0xb0 | ch, CC.allSoundOff, 0]);
      send([0xb0 | ch, CC.allNotesOff, 0]);
    }
  }

  function sendCC(number, value) {
    const v = Math.max(0, Math.min(127, Math.round(value)));
    if (webSynth) webSynth.cc(number, v);
    send([0xb0 | channel, number, v]);
  }

  function radioValue(name) {
    const checked = document.querySelector(`input[name="${name}"]:checked`);
    return checked ? Number(checked.value) : 0;
  }

  const octaveToCC = (o) => (o < 0 ? 0 : o > 0 ? 127 : 64);

  // Synth state that isn't a slider or radio.
  let instrument = 0;
  let registerMask = ACCORDION_DEFAULTS.register;

  // Pushes every setting, so a freshly plugged (or rebooted) Teensy
  // matches what the page shows.
  function sendAllControls() {
    sendCC(CC.layout, griff === "b" ? 127 : 0);
    sendCC(CC.keyVelocity, radioValue("keyVelocity") * 32);
    sendCC(CC.keyTest, keyTestOn ? 127 : 0);
    sendCC(CC.instrument, instrument * 16);
    for (let o = 0; o < 3; o += 1) {
      sendCC(CC.synthWave[o], radioValue(`oscWave${o + 1}`) * 32);
      sendCC(CC.synthOctave[o], octaveToCC(radioValue(`oscOct${o + 1}`)));
    }
    sendCC(CC.register, registerMask);
    els.sliders.forEach((slider) => sendCC(Number(slider.dataset.cc), Number(slider.value)));
  }

  /* ============================================================
     DEVICE LIST
     ============================================================ */
  function looksLikeTeensy(port) {
    return /teensy|etutti/i.test(`${port.name} ${port.manufacturer || ""}`);
  }

  function refreshDevices() {
    if (!midiAccess) return;

    // Some browsers keep an unplugged port in the map, flagged disconnected.
    const outputs = Array.from(midiAccess.outputs.values()).filter((p) => p.state !== "disconnected");
    const previousId = els.outputSelect.value;
    els.outputSelect.innerHTML = "";

    if (outputs.length === 0) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = tr("device.none", "No MIDI devices");
      els.outputSelect.appendChild(opt);
      els.outputSelect.disabled = true;
      selectOutput(null);
      setStatus("status.noDevice");
      return;
    }

    els.outputSelect.disabled = false;
    outputs.forEach((port) => {
      const opt = document.createElement("option");
      opt.value = port.id;
      opt.textContent = port.name || port.id;
      els.outputSelect.appendChild(opt);
    });

    const keep = outputs.find((p) => p.id === previousId);
    const teensy = outputs.find(looksLikeTeensy);
    const chosen = keep || teensy || null;

    if (chosen) {
      els.outputSelect.value = chosen.id;
      selectOutput(chosen);
    } else {
      // Several unknown devices: don't guess, let the user pick.
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = tr("device.choose", "— choose a device —");
      els.outputSelect.prepend(placeholder);
      els.outputSelect.value = "";
      selectOutput(null);
      setStatus("status.pickDevice");
    }
  }

  function selectOutput(port) {
    if (output === port) return;
    releaseEverything();
    output = port;

    if (input) {
      input.onmidimessage = null;
      input = null;
    }
    const lit = Array.from(remoteNotes);
    remoteNotes.clear();
    lit.forEach(paintNote);

    if (!port) return;

    // The matching input (same device name) carries what the Teensy sends
    // back — notes from its own keys now, more controls later.
    input = Array.from(midiAccess.inputs.values()).find((p) => p.name === port.name) || null;
    if (input) {
      input.onmidimessage = (event) => handleIncoming(event.data);
    }

    setStatus("status.connected", { name: port.name || port.id });
    sendAllControls();
  }

  async function connect() {
    if (!navigator.requestMIDIAccess) {
      setStatus("status.unsupported");
      return;
    }

    try {
      midiAccess = await navigator.requestMIDIAccess({ sysex: false });
    } catch (error) {
      setStatus("status.denied");
      return;
    }

    els.connectBtn.hidden = true;
    midiAccess.onstatechange = (event) => {
      const port = event.port;
      if (port && output && port.id === output.id && port.state === "disconnected") {
        const name = output.name || output.id;
        output = null;
        const notes = Array.from(soundingCount.keys());
        soundingCount.clear();
        heldByKey.clear();
        heldByPointer.clear();
        notes.forEach(paintNote);
        refreshDevices();
        if (!output) setStatus("status.disconnected", { name });
        return;
      }
      refreshDevices();
    };
    refreshDevices();
  }

  /* ============================================================
     ON-SCREEN eTuttino
     ============================================================ */
  const keyEls = []; // { el, key } per layout key

  // Key legends: the real labels of the user's keyboard where the browser
  // exposes them (navigator.keyboard.getLayoutMap, Chrome/Edge), else the
  // ABNT2 labels the layout was designed on.
  const ABNT2_LABELS = {
    Comma: ",", Period: ".", Slash: ";", IntlRo: "/", Semicolon: "Ç", Quote: "~",
    Backslash: "]", BracketLeft: "´", BracketRight: "[",
  };
  let layoutMap = null;
  function keyLegend(code) {
    if (!code) return "";
    const label = layoutMap && layoutMap.get(code);
    if (label) return label.toUpperCase();
    return ABNT2_LABELS[code] || code.replace(/^(Key|Digit)/, "");
  }
  if (navigator.keyboard && navigator.keyboard.getLayoutMap) {
    navigator.keyboard.getLayoutMap().then((map) => {
      layoutMap = map;
      renderGrid();
    }).catch(() => {});
  }

  function renderGrid() {
    els.grid.innerHTML = "";
    keyEls.length = 0;
    els.grid.classList.toggle("hide-key-legends", !keyboardOn);

    LAYOUT.forEach((key) => {
      const note = keyNote(key);
      const cap = document.createElement("button");
      cap.type = "button";
      cap.className = isSharp(note) ? "cap cap-dark" : "cap";
      if (((note % 12) + 12) % 12 === 0) cap.classList.add("cap-c");
      cap.dataset.index = String(LAYOUT.indexOf(key));
      cap.tabIndex = -1;
      cap.setAttribute("aria-label", noteName(note));
      cap.style.left = `${((key.x + 0.5) / GRID_UNITS_X) * 100}%`;
      cap.style.top = `${(slotOf(key.row) / GRID_UNITS_Y) * 100}%`;
      cap.style.width = `${100 / GRID_UNITS_X}%`;
      cap.style.height = `${100 / GRID_UNITS_Y}%`;

      const face = document.createElement("span");
      face.className = "cap-face";
      const name = document.createElement("span");
      name.className = "cap-note";
      name.textContent = noteName(note);
      const legend = document.createElement("span");
      legend.className = "cap-key";
      legend.textContent = keyLegend(key.code);
      face.appendChild(name);
      face.appendChild(legend);
      cap.appendChild(face);

      els.grid.appendChild(cap);
      keyEls.push({ el: cap, key });
    });

    keyEls.forEach((_, i) => paintPress(i));
    const notes = LAYOUT.map(keyNote);
    els.octaveValue.textContent = `${noteName(Math.min(...notes))}–${noteName(Math.max(...notes))}`;
    keyEls.forEach(({ key }) => paintNote(keyNote(key)));
  }

  // Every key carrying this note lights up (row 4 duplicates row 1).
  function paintNote(note) {
    const down = soundingCount.has(note) || remoteNotes.has(note);
    keyEls.forEach(({ el, key }) => {
      if (keyNote(key) === note) el.classList.toggle("is-down", down);
    });
  }

  function paintPress(i) {
    const entry = keyEls[i];
    if (!entry) return;
    entry.el.classList.toggle("has-press", keyTestOn);
    entry.el.style.setProperty("--press", keyTestOn ? keyPress[i].toFixed(3) : "0");
  }

  function noteForCap(el) {
    return keyNote(LAYOUT[Number(el.dataset.index)]);
  }

  els.grid.addEventListener("pointerdown", (event) => {
    const cap = event.target.closest(".cap");
    if (!cap) return;
    event.preventDefault();
    els.grid.setPointerCapture(event.pointerId);
    const note = noteForCap(cap);
    heldByPointer.set(event.pointerId, note);
    noteOn(note);
  });

  // Sliding across keys moves the held note with the pointer.
  els.grid.addEventListener("pointermove", (event) => {
    if (!heldByPointer.has(event.pointerId)) return;
    const el = document.elementFromPoint(event.clientX, event.clientY);
    const cap = el && el.closest && el.closest(".cap");
    if (!cap) return;
    const note = noteForCap(cap);
    const previous = heldByPointer.get(event.pointerId);
    if (note === previous) return;
    heldByPointer.set(event.pointerId, note);
    noteOn(note);
    noteOff(previous);
  });

  function endPointer(event) {
    if (!heldByPointer.has(event.pointerId)) return;
    noteOff(heldByPointer.get(event.pointerId));
    heldByPointer.delete(event.pointerId);
  }
  els.grid.addEventListener("pointerup", endPointer);
  els.grid.addEventListener("pointercancel", endPointer);

  /* ============================================================
     C-GRIFF / B-GRIFF
     ============================================================ */
  function syncToggleLabels(toggle, activeStyle) {
    toggle.querySelectorAll(".style-toggle-label").forEach((label) => {
      label.classList.toggle("is-active", label.dataset.style === activeStyle);
    });
  }

  function setGriff(system) {
    releaseEverything();
    griff = system;
    save(STORAGE.griff, system);
    els.griffCheckbox.checked = system === "b";
    syncToggleLabels(els.griffToggle, system);
    sendCC(CC.layout, system === "b" ? 127 : 0);
    renderGrid();
    renderModels();
  }

  function wireStyleToggle(toggle, checkbox, onChange) {
    checkbox.addEventListener("change", () => onChange(checkbox.checked));
    toggle.querySelectorAll(".style-toggle-label").forEach((label) => {
      label.addEventListener("click", (event) => {
        event.preventDefault();
        const wantChecked = label.dataset.checked === "true";
        if (checkbox.checked !== wantChecked) {
          checkbox.checked = wantChecked;
          onChange(wantChecked);
        }
      });
    });
  }

  wireStyleToggle(els.griffToggle, els.griffCheckbox, (checked) => setGriff(checked ? "b" : "c"));

  /* ============================================================
     COMPUTER KEYBOARD
     ============================================================ */
  function setKeyboard(on) {
    if (!on) {
      // Release anything held from the keyboard before ignoring it.
      heldByKey.forEach((note) => noteOff(note));
      heldByKey.clear();
    }
    keyboardOn = on;
    save(STORAGE.keyboard, on ? "on" : "off");
    els.keyboardCheckbox.checked = on;
    syncToggleLabels(els.keyboardToggle, on ? "on" : "off");
    els.keysHint.hidden = !on;
    els.grid.classList.toggle("hide-key-legends", !on);
  }

  wireStyleToggle(els.keyboardToggle, els.keyboardCheckbox, setKeyboard);

  function isTyping() {
    const el = document.activeElement;
    if (!el) return false;
    const tag = el.tagName;
    return (tag === "INPUT" && el.type !== "range" && el.type !== "radio" && el.type !== "checkbox") || tag === "SELECT" || tag === "TEXTAREA";
  }

  function shiftOctave(delta) {
    const next = Math.max(-MAX_TRANSPOSE, Math.min(MAX_TRANSPOSE, transpose + delta));
    if (next === transpose) return;
    transpose = next;
    // Held notes keep sounding and release correctly (heldByKey remembers
    // the note actually sent); only the labels move.
    renderGrid();
  }

  function shiftVelocity(delta) {
    velocity = Math.max(1, Math.min(127, velocity + delta));
    els.velocityValue.textContent = String(velocity);
  }

  function playing() {
    return !els.etuttinoSections.hidden;
  }

  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey || event.metaKey || event.altKey || isTyping() || !playing()) return;

    const key = keyboardOn ? CODE_TO_KEY.get(event.code) : null;
    if (key) {
      event.preventDefault();
      if (event.repeat || heldByKey.has(event.code)) return;
      const note = keyNote(key);
      heldByKey.set(event.code, note);
      noteOn(note);
      return;
    }

    let handled = true;
    if (event.code === "ArrowLeft") shiftOctave(-1);
    else if (event.code === "ArrowRight") shiftOctave(1);
    else if (event.code === "ArrowDown") shiftVelocity(-VELOCITY_STEP);
    else if (event.code === "ArrowUp") shiftVelocity(VELOCITY_STEP);
    else if (event.code === "Escape") panic();
    else handled = false;
    // Arrows would otherwise scroll the page (or move a focused slider).
    if (handled) event.preventDefault();
  });

  document.addEventListener("keyup", (event) => {
    if (!heldByKey.has(event.code)) return;
    noteOff(heldByKey.get(event.code));
    heldByKey.delete(event.code);
  });

  // Switching tabs/windows mid-note would otherwise leave it stuck on, since
  // the keyup never reaches this page.
  window.addEventListener("blur", releaseEverything);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) releaseEverything();
  });

  /* ============================================================
     SYNTH CONTROLS + PRESETS
     ============================================================ */
  // Each slider carries its CC number and a formatter for the value the
  // firmware will actually use, so the label reads in real units.
  const FORMATS = {
    percent: (v) => `${Math.round((v / 127) * 100)}%`,
    attack: (v) => `${Math.round(Math.pow(v / 127, 2) * 2000)} ms`,
    release: (v) => `${Math.round(Math.pow(v / 127, 2) * 3000)} ms`,
    cutoff: (v) => {
      const hz = 40 * Math.pow(2, (v / 127) * 9);
      return hz >= 1000 ? `${(hz / 1000).toFixed(1)} kHz` : `${Math.round(hz)} Hz`;
    },
    wetness: (v) => (v === 0 ? tr("synth.dry", "dry") : `${tr("synth.wet", "wet")} · ${v}¢`),
    decay: (v) => `${Math.round(Math.pow(v / 127, 2) * 2000)} ms`,
    detune: (v) => {
      const cents = ((v - 64) / 64) * 50;
      return `${cents > 0 ? "+" : cents < 0 ? "−" : ""}${Math.abs(cents).toFixed(1)}¢`;
    },
  };
  const sliderLabelUpdaters = new Map();

  els.sliders.forEach((slider) => {
    const out = document.getElementById(`${slider.id}Value`);
    const format = FORMATS[slider.dataset.format] || String;
    const update = () => {
      if (out) out.textContent = format(Number(slider.value));
    };
    sliderLabelUpdaters.set(slider.id, update);
    slider.addEventListener("input", () => {
      update();
      sendCC(Number(slider.dataset.cc), Number(slider.value));
      refreshPresetState();
    });
    update();
  });

  // ---- register switch ----
  function renderRegister() {
    els.registerDots.forEach((dot) => {
      const on = (registerMask & Number(dot.dataset.reed)) !== 0;
      dot.classList.toggle("is-on", on);
      dot.setAttribute("aria-pressed", String(on));
    });
    const { code, name } = registerNameKey(registerMask);
    els.registerCode.textContent = code;
    els.registerName.textContent = name ? tr(`register.${name}`, name) : "";
    els.registerPresets.querySelectorAll("[data-mask]").forEach((btn) => {
      btn.classList.toggle("is-active", Number(btn.dataset.mask) === registerMask);
    });
  }

  function setRegister(mask) {
    if (mask === 0) return; // at least one reed must sound
    registerMask = mask;
    sendCC(CC.register, mask);
    renderRegister();
    refreshPresetState();
  }

  els.registerDots.forEach((dot) => {
    dot.addEventListener("click", () => setRegister(registerMask ^ Number(dot.dataset.reed)));
  });

  NAMED_REGISTERS.forEach(({ mask, key }) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "small-btn register-preset";
    btn.dataset.mask = String(mask);
    btn.dataset.i18n = `register.${key}`;
    btn.textContent = tr(`register.${key}`, key);
    btn.addEventListener("click", () => setRegister(mask));
    els.registerPresets.appendChild(btn);
  });

  // ---- synth oscillators ----
  for (let o = 0; o < 3; o += 1) {
    document.querySelectorAll(`input[name="oscWave${o + 1}"]`).forEach((radio) => {
      radio.addEventListener("change", () => {
        if (!radio.checked) return;
        sendCC(CC.synthWave[o], Number(radio.value) * 32);
        refreshPresetState();
      });
    });
    document.querySelectorAll(`input[name="oscOct${o + 1}"]`).forEach((radio) => {
      radio.addEventListener("change", () => {
        if (!radio.checked) return;
        sendCC(CC.synthOctave[o], octaveToCC(Number(radio.value)));
        refreshPresetState();
      });
    });
  }

  // ---- presets ----
  function currentSettings() {
    const settings = { instrument, register: registerMask };
    SYNTH_RADIOS.forEach((name) => {
      settings[name] = radioValue(name);
    });
    els.sliders.forEach((slider) => {
      settings[slider.id] = Number(slider.value);
    });
    return settings;
  }

  // Shows "modified" once any control that matters for the chosen
  // instrument differs from its preset.
  function refreshPresetState() {
    const preset = PRESETS[activePreset];
    const now = currentSettings();
    const modified = Object.keys(preset).some((k) => settingMatters(k, preset.instrument) && preset[k] !== now[k]);
    els.presetModified.hidden = !modified;
  }

  function applyPreset(id, { send: doSend = true } = {}) {
    const preset = PRESETS[id];
    if (!preset) return;
    if (doSend && preset.instrument !== instrument) releaseEverything();
    activePreset = id;
    save(STORAGE.preset, id);
    instrument = preset.instrument;
    registerMask = preset.register;
    els.presetInputs.forEach((radio) => {
      radio.checked = radio.value === id;
    });
    els.sliders.forEach((slider) => {
      if (slider.id in preset) {
        slider.value = String(preset[slider.id]);
        sliderLabelUpdaters.get(slider.id)();
      }
    });
    SYNTH_RADIOS.forEach((name) => {
      document.querySelectorAll(`input[name="${name}"]`).forEach((radio) => {
        radio.checked = Number(radio.value) === preset[name];
      });
    });
    const isSynth = instrument === SYNTH_INSTRUMENT;
    els.accordionControls.hidden = instrument !== 0;
    els.synthControls.hidden = !isSynth;
    els.envelopeControls.hidden = !(instrument === 0 || isSynth);
    els.synthEnvelopeOnly.forEach((el) => {
      el.hidden = !isSynth;
    });
    renderRegister();
    refreshPresetState();
    if (doSend) sendAllControls();
  }

  els.presetInputs.forEach((radio) => {
    radio.addEventListener("change", () => {
      if (radio.checked) applyPreset(radio.value);
    });
  });
  els.resetBtn.addEventListener("click", () => applyPreset(DEFAULT_PRESET));

  window.addEventListener("bc:langchange", () => {
    renderRegister();
    sliderLabelUpdaters.forEach((update) => update());
  });

  /* ============================================================
     PHYSICAL KEYS (velocity curve, calibration, key test)
     ============================================================ */
  const savedCurve = load(STORAGE.keyVelocity, "2");
  els.keyVelocityInputs.forEach((radio) => {
    radio.checked = radio.value === savedCurve;
    radio.addEventListener("change", () => {
      if (!radio.checked) return;
      save(STORAGE.keyVelocity, radio.value);
      sendCC(CC.keyVelocity, Number(radio.value) * 32);
    });
  });

  els.calibrateBtn.addEventListener("click", () => {
    sendCC(CC.calibrate, 127);
    els.calibrateStatus.dataset.i18n = "keys.calibrateSent";
    els.calibrateStatus.textContent = tr("keys.calibrateSent", "Calibration restarted: now press every key all the way down once.");
  });

  function setKeyTest(on) {
    keyTestOn = on;
    els.keyTestCheckbox.checked = on;
    syncToggleLabels(els.keyTestToggle, on ? "on" : "off");
    keyPress.fill(0);
    keyEls.forEach((_, i) => paintPress(i));
    sendCC(CC.keyTest, on ? 127 : 0);
  }
  wireStyleToggle(els.keyTestToggle, els.keyTestCheckbox, setKeyTest);

  /* ============================================================
     SOUND IN THE BROWSER
     ============================================================ */
  const webSoundToggle = document.getElementById("webSoundToggle");
  const webSoundCheckbox = document.getElementById("webSoundCheckbox");
  async function setWebSound(on) {
    webSoundCheckbox.checked = on;
    syncToggleLabels(webSoundToggle, on ? "on" : "off");
    if (!webSynth) return;
    if (on) {
      await webSynth.enable();
      sendAllControls(); // the web synth starts from the page's settings
    } else {
      webSynth.disable();
    }
  }
  if (webSynth) {
    wireStyleToggle(webSoundToggle, webSoundCheckbox, setWebSound);
  } else {
    webSoundCheckbox.disabled = true;
  }

  /* ============================================================
     OTHER CONTROLS
     ============================================================ */
  els.connectBtn.addEventListener("click", connect);

  els.outputSelect.addEventListener("change", () => {
    const port = midiAccess && midiAccess.outputs.get(els.outputSelect.value);
    selectOutput(port || null);
    if (!port) setStatus("status.pickDevice");
    els.outputSelect.blur();
  });

  for (let ch = 1; ch <= 16; ch += 1) {
    const opt = document.createElement("option");
    opt.value = String(ch - 1);
    opt.textContent = String(ch);
    els.channelSelect.appendChild(opt);
  }
  els.channelSelect.addEventListener("change", () => {
    releaseEverything();
    channel = Number(els.channelSelect.value);
    els.channelSelect.blur();
  });

  els.octaveDown.addEventListener("click", () => shiftOctave(-1));
  els.octaveUp.addEventListener("click", () => shiftOctave(1));
  els.velocityDown.addEventListener("click", () => shiftVelocity(-VELOCITY_STEP));
  els.velocityUp.addEventListener("click", () => shiftVelocity(VELOCITY_STEP));
  els.panicBtn.addEventListener("click", panic);
  els.sendAllBtn.addEventListener("click", sendAllControls);
  els.clearMonitorBtn.addEventListener("click", () => {
    els.monitor.innerHTML = "";
  });

  // Collapsible panels (same markup as the tuner pages).
  document.querySelectorAll(".collapse-toggle").forEach((toggle) => {
    toggle.addEventListener("click", () => {
      const panel = toggle.closest(".control-block");
      const collapsed = panel.classList.toggle("is-collapsed");
      toggle.setAttribute("aria-expanded", String(!collapsed));
    });
  });

  window.addEventListener("bc:langchange", () => {
    renderStatus();
    if (midiAccess) refreshDevices();
  });

  if (!navigator.requestMIDIAccess) {
    setStatus("status.unsupported");
    els.connectBtn.disabled = true;
  } else {
    renderStatus();
  }
  shiftVelocity(0);
  applyPreset(activePreset, { send: false });
  els.griffCheckbox.checked = griff === "b";
  syncToggleLabels(els.griffToggle, griff);
  setKeyboard(keyboardOn);
  renderModels();
  renderGrid();
  selectModel("etuttino");
})();
