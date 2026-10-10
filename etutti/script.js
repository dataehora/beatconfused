/* ============================================================
   eTUTTI — browser front-end for a Teensy-based controller/synth.

   Two models share this page:
     - eTuttino (the one being built): 34 keys in a chromatic-accordion
       C-griff layout, G3–G5, read by a Teensy 4.0 as a 4 x 9 key matrix.
     - eTutti (the full instrument): only a preview render for now.

   The Teensy runs etutti/firmware/etutti_synth (Teensy Audio Library on
   an SGTL5000 Audio Board) and enumerates over USB as a class-compliant
   MIDI device. This page talks to it with the Web MIDI API:
     - the computer keyboard (and the on-screen keys) send Note On/Off,
     - the Synth panel sends Control Change messages the firmware maps to
       waveform, envelope, filter and volume,
     - anything the Teensy sends back is shown in the MIDI monitor, and
       notes played on the real keys light up on the on-screen ones.
   No sound is made in the browser — the Teensy's audio output is the
   instrument.
   ============================================================ */
(function () {
  "use strict";

  // CC numbers shared with the firmware (keep in sync with etutti_synth.ino).
  const CC = {
    volume: 7,
    waveform: 70,
    resonance: 71,
    release: 72,
    attack: 73,
    cutoff: 74,
    decay: 75,
    sustain: 79,
    allSoundOff: 120,
    allNotesOff: 123,
  };

  const NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];

  /* ------------------------------------------------------------
     eTuttino LAYOUT — chromatic button accordion, C-griff.
     Along a row each key is a minor third (3 semitones) above the last;
     rows are staggered half a key, so each diagonal step to the next row
     is one semitone up. Row 4 repeats row 1 (plus F♯3 in front), as on a
     real 4-row C-griff accordion.
       x   = horizontal position in key units (19.05 mm on the PCB)
       col = matrix column on the PCB/firmware (row = matrix row)
       code = computer key (KeyboardEvent.code) — the computer's own rows
              are staggered too, so the shape under the fingers matches.
     Keep in sync with NOTE_MAP in etutti_synth.ino and with
     etutti/hardware/README.md.
     ------------------------------------------------------------ */
  const ROWS = [
    { first: 57, count: 8, x0: 0, col0: 1, codes: ["Digit3", "Digit4", "Digit5", "Digit6", "Digit7", "Digit8", "Digit9", "Digit0"] },
    { first: 55, count: 9, x0: -0.5, col0: 0, codes: ["KeyW", "KeyE", "KeyR", "KeyT", "KeyY", "KeyU", "KeyI", "KeyO", "KeyP"] },
    { first: 56, count: 8, x0: 0, col0: 1, codes: ["KeyS", "KeyD", "KeyF", "KeyG", "KeyH", "KeyJ", "KeyK", "KeyL"] },
    { first: 54, count: 9, x0: -0.5, col0: 0, codes: ["KeyZ", "KeyX", "KeyC", "KeyV", "KeyB", "KeyN", "KeyM", "Comma", "Period"] },
  ];
  const LAYOUT = [];
  ROWS.forEach((row, r) => {
    for (let i = 0; i < row.count; i += 1) {
      LAYOUT.push({ row: r, col: row.col0 + i, x: row.x0 + i, note: row.first + 3 * i, code: row.codes[i] });
    }
  });
  const CODE_TO_KEY = new Map(LAYOUT.map((k) => [k.code, k]));
  const GRID_UNITS_X = 9; // x from -0.5 to 7.5, one key wide each
  const GRID_UNITS_Y = 4;
  const LOWEST = Math.min(...LAYOUT.map((k) => k.note));
  const HIGHEST = Math.max(...LAYOUT.map((k) => k.note));
  const MAX_TRANSPOSE = 3; // octaves either way
  const VELOCITY_STEP = 16;
  const MONITOR_LINES = 40;

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
    octaveDown: document.getElementById("octaveDown"),
    octaveUp: document.getElementById("octaveUp"),
    octaveValue: document.getElementById("octaveValue"),
    velocityDown: document.getElementById("velocityDown"),
    velocityUp: document.getElementById("velocityUp"),
    velocityValue: document.getElementById("velocityValue"),
    panicBtn: document.getElementById("panicBtn"),
    sendAllBtn: document.getElementById("sendAllBtn"),
    waveInputs: document.querySelectorAll('input[name="waveform"]'),
    sliders: document.querySelectorAll("[data-cc]"),
    monitor: document.getElementById("midiMonitor"),
    clearMonitorBtn: document.getElementById("clearMonitorBtn"),
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
  const heldByKey = new Map(); // KeyboardEvent.code -> MIDI note actually sent
  const heldByPointer = new Map(); // pointerId -> MIDI note
  const soundingCount = new Map(); // MIDI note -> how many sources hold it
  const remoteNotes = new Set(); // notes the Teensy reports from its own keys
  let statusKey = "status.idle";
  let statusVars = null;

  function noteName(midi) {
    return `${NOTE_NAMES[((midi % 12) + 12) % 12]}${Math.floor(midi / 12) - 1}`;
  }

  function isSharp(midi) {
    return [1, 3, 6, 8, 10].includes(((midi % 12) + 12) % 12);
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

  // A small three-quarter-free "product shot": rounded case (aluminium or
  // plastic), a recessed plate, and square keycaps in the given layout.
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
      const kx = pad + (k.x - k.xMin) * u + 1.2;
      const ky = pad + k.row * u + 1.2;
      svg.appendChild(svgEl("rect", { x: kx, y: ky + 1.2, width: u - 2.4, height: u - 2.4, rx: 3, class: "model-cap-side" }));
      svg.appendChild(svgEl("rect", {
        x: kx,
        y: ky,
        width: u - 2.4,
        height: u - 2.4,
        rx: 3,
        class: isSharp(k.note) ? "model-cap model-cap-dark" : "model-cap",
      }));
    });
    container.innerHTML = "";
    container.appendChild(svg);
  }

  function renderModels() {
    renderModel(
      els.renderEtuttino,
      LAYOUT.map((k) => ({ ...k, xMin: -0.5 })),
      GRID_UNITS_X,
      GRID_UNITS_Y,
      "aluminium",
    );
    // eTutti preview: a full 5-row C-griff, 12-13 keys per row, F♯2 up.
    const full = [];
    const starts = [45, 43, 44, 42, 43];
    starts.forEach((first, r) => {
      const offset = r % 2 === 0 ? 0 : -0.5;
      const count = r % 2 === 0 ? 12 : 13;
      for (let i = 0; i < count; i += 1) full.push({ row: r, x: offset + i, note: first + 3 * i, xMin: -0.5 });
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

  // Notes the Teensy plays from its own key matrix light up here too.
  function handleIncoming(bytes) {
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
    if (count === 0) send([0x90 | channel, note, velocity]);
    paintNote(note);
  }

  function noteOff(note) {
    const count = soundingCount.get(note) || 0;
    if (count <= 1) {
      soundingCount.delete(note);
      if (count === 1) send([0x80 | channel, note, 0]);
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
    send([0xb0 | channel, number, Math.max(0, Math.min(127, Math.round(value)))]);
  }

  // Pushes every synth control's current value, so a freshly plugged (or
  // freshly rebooted) Teensy matches what the page shows.
  function sendAllControls() {
    const wave = document.querySelector('input[name="waveform"]:checked');
    if (wave) sendCC(CC.waveform, Number(wave.value) * 32);
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
    remoteNotes.clear();
    LAYOUT.forEach((k) => paintNote(k.note + 12 * transpose));

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

  function renderGrid() {
    els.grid.innerHTML = "";
    keyEls.length = 0;

    LAYOUT.forEach((key) => {
      const note = key.note + 12 * transpose;
      const cap = document.createElement("button");
      cap.type = "button";
      cap.className = isSharp(note) ? "cap cap-dark" : "cap";
      if (((note % 12) + 12) % 12 === 0) cap.classList.add("cap-c");
      cap.dataset.code = key.code;
      cap.tabIndex = -1;
      cap.setAttribute("aria-label", noteName(note));
      cap.style.left = `${((key.x + 0.5) / GRID_UNITS_X) * 100}%`;
      cap.style.top = `${(key.row / GRID_UNITS_Y) * 100}%`;
      cap.style.width = `${100 / GRID_UNITS_X}%`;
      cap.style.height = `${100 / GRID_UNITS_Y}%`;

      const face = document.createElement("span");
      face.className = "cap-face";
      const name = document.createElement("span");
      name.className = "cap-note";
      name.textContent = noteName(note);
      const legend = document.createElement("span");
      legend.className = "cap-key";
      legend.textContent = key.code.replace(/^(Key|Digit)/, "").replace("Comma", ",").replace("Period", ".");
      face.appendChild(name);
      face.appendChild(legend);
      cap.appendChild(face);

      els.grid.appendChild(cap);
      keyEls.push({ el: cap, key });
    });

    els.octaveValue.textContent = `${noteName(LOWEST + 12 * transpose)}–${noteName(HIGHEST + 12 * transpose)}`;
    keyEls.forEach(({ key }) => paintNote(key.note + 12 * transpose));
  }

  // Every key carrying this note lights up (row 4 duplicates row 1).
  function paintNote(note) {
    const down = soundingCount.has(note) || remoteNotes.has(note);
    keyEls.forEach(({ el, key }) => {
      if (key.note + 12 * transpose === note) el.classList.toggle("is-down", down);
    });
  }

  function noteForCap(el) {
    const key = CODE_TO_KEY.get(el.dataset.code);
    return key.note + 12 * transpose;
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
     COMPUTER KEYBOARD
     ============================================================ */
  function isTyping() {
    const el = document.activeElement;
    if (!el) return false;
    const tag = el.tagName;
    return (tag === "INPUT" && el.type !== "range" && el.type !== "radio") || tag === "SELECT" || tag === "TEXTAREA";
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

    const key = CODE_TO_KEY.get(event.code);
    if (key) {
      event.preventDefault();
      if (event.repeat || heldByKey.has(event.code)) return;
      const note = key.note + 12 * transpose;
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
     CONTROLS
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

  els.waveInputs.forEach((radio) => {
    radio.addEventListener("change", () => {
      if (radio.checked) sendCC(CC.waveform, Number(radio.value) * 32);
    });
  });

  // Each slider carries its CC number and a formatter for the value the
  // firmware will actually use, so the label reads in real units.
  const FORMATS = {
    percent: (v) => `${Math.round((v / 127) * 100)}%`,
    attack: (v) => `${Math.round(Math.pow(v / 127, 2) * 2000)} ms`,
    decay: (v) => `${Math.round(Math.pow(v / 127, 2) * 2000)} ms`,
    release: (v) => `${Math.round(Math.pow(v / 127, 2) * 3000)} ms`,
    cutoff: (v) => {
      const hz = 40 * Math.pow(2, (v / 127) * 9);
      return hz >= 1000 ? `${(hz / 1000).toFixed(1)} kHz` : `${Math.round(hz)} Hz`;
    },
    resonance: (v) => (0.7 + (v / 127) * 4.3).toFixed(2),
  };

  els.sliders.forEach((slider) => {
    const out = document.getElementById(`${slider.id}Value`);
    const format = FORMATS[slider.dataset.format] || String;
    const update = () => {
      if (out) out.textContent = format(Number(slider.value));
    };
    slider.addEventListener("input", () => {
      update();
      sendCC(Number(slider.dataset.cc), Number(slider.value));
    });
    update();
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
  renderModels();
  renderGrid();
  selectModel("etuttino");
})();
