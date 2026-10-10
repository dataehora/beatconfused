/* ============================================================
   eTUTTI — browser front-end for a Teensy-based controller/synth.

   The Teensy runs etutti/firmware/etutti_synth (Teensy Audio Library on
   an SGTL5000 Audio Board) and enumerates over USB as a class-compliant
   MIDI device. This page talks to it with the Web MIDI API:
     - the computer keyboard (and the on-screen keys) send Note On/Off,
     - the Synth panel sends Control Change messages the firmware maps to
       waveform, envelope, filter and volume,
     - anything the Teensy sends back is shown in the MIDI monitor (the
       hook for the custom hardware interface to come).
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

  // Computer-keyboard layout (by physical key, via KeyboardEvent.code, so
  // it works the same on QWERTY, ABNT2, AZERTY…): the home row plays the
  // white keys, the row above the black keys — the layout most DAWs use.
  const KEY_OFFSETS = {
    KeyA: 0, KeyW: 1, KeyS: 2, KeyE: 3, KeyD: 4, KeyF: 5, KeyT: 6, KeyG: 7,
    KeyY: 8, KeyH: 9, KeyU: 10, KeyJ: 11, KeyK: 12, KeyO: 13, KeyL: 14,
    KeyP: 15, Semicolon: 16, Quote: 17,
  };
  const KEY_LABELS = {};
  Object.keys(KEY_OFFSETS).forEach((code) => {
    KEY_LABELS[KEY_OFFSETS[code]] = code === "Semicolon" ? ";" : code === "Quote" ? "'" : code.slice(3);
  });
  const KEY_COUNT = 18; // C … F of the next octave
  const NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];
  const MIN_BASE = 12; // C0
  const MAX_BASE = 108 - (KEY_COUNT - 1); // keeps the top key ≤ C8
  const VELOCITY_STEP = 16;
  const MONITOR_LINES = 40;

  const els = {
    connectBtn: document.getElementById("connectBtn"),
    connLight: document.getElementById("connLight"),
    connStatus: document.getElementById("connStatus"),
    outputSelect: document.getElementById("outputSelect"),
    channelSelect: document.getElementById("channelSelect"),
    piano: document.getElementById("piano"),
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
  let baseNote = 60; // C4
  let velocity = 100;
  const heldByKey = new Map(); // KeyboardEvent.code -> MIDI note actually sent
  const heldByPointer = new Map(); // pointerId -> MIDI note
  const soundingCount = new Map(); // MIDI note -> how many sources hold it
  let statusKey = "status.idle";
  let statusVars = null;

  function noteName(midi) {
    return `${NOTE_NAMES[midi % 12]}${Math.floor(midi / 12) - 1}`;
  }

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
    paintKey(note);
  }

  function noteOff(note) {
    const count = soundingCount.get(note) || 0;
    if (count <= 1) {
      soundingCount.delete(note);
      if (count === 1) send([0x80 | channel, note, 0]);
    } else {
      soundingCount.set(note, count - 1);
    }
    paintKey(note);
  }

  function releaseEverything() {
    heldByKey.clear();
    heldByPointer.clear();
    soundingCount.forEach((_, note) => send([0x80 | channel, note, 0]));
    soundingCount.clear();
    renderPiano();
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

    if (!port) return;

    // The matching input (same device name) carries whatever the Teensy
    // sends back — knobs, buttons, sensors on the future custom interface.
    input = Array.from(midiAccess.inputs.values()).find((p) => p.name === port.name) || null;
    if (input) {
      input.onmidimessage = (event) => logMidi("in", event.data);
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
        soundingCount.clear();
        heldByKey.clear();
        heldByPointer.clear();
        renderPiano();
        refreshDevices();
        if (!output) setStatus("status.disconnected", { name });
        return;
      }
      refreshDevices();
    };
    refreshDevices();
  }

  /* ============================================================
     ON-SCREEN PIANO
     ============================================================ */
  const keyEls = new Map(); // MIDI note -> element

  function renderPiano() {
    els.piano.innerHTML = "";
    keyEls.clear();

    const whites = document.createElement("div");
    whites.className = "piano-whites";
    const blacks = document.createElement("div");
    blacks.className = "piano-blacks";
    let whiteIndex = 0;

    for (let offset = 0; offset < KEY_COUNT; offset += 1) {
      const note = baseNote + offset;
      const isBlack = [1, 3, 6, 8, 10].includes(note % 12);
      const key = document.createElement("button");
      key.type = "button";
      key.className = isBlack ? "piano-key piano-key-black" : "piano-key piano-key-white";
      key.dataset.note = String(note);
      key.setAttribute("aria-label", noteName(note));
      key.tabIndex = -1;

      const label = document.createElement("span");
      label.className = "piano-key-label";
      label.textContent = KEY_LABELS[offset] || "";
      key.appendChild(label);

      if (!isBlack) {
        const name = document.createElement("span");
        name.className = "piano-key-note";
        name.textContent = note % 12 === 0 ? noteName(note) : "";
        key.appendChild(name);
        whites.appendChild(key);
        whiteIndex += 1;
      } else {
        // Centred on the boundary between the two white keys around it.
        key.style.setProperty("--slot", String(whiteIndex));
        blacks.appendChild(key);
      }
      keyEls.set(note, key);
    }

    els.piano.style.setProperty("--white-count", String(whiteIndex));
    els.piano.appendChild(whites);
    els.piano.appendChild(blacks);
    keyEls.forEach((_, note) => paintKey(note));
    els.octaveValue.textContent = `${noteName(baseNote)}–${noteName(baseNote + KEY_COUNT - 1)}`;
  }

  function paintKey(note) {
    const key = keyEls.get(note);
    if (key) key.classList.toggle("is-down", soundingCount.has(note));
  }

  els.piano.addEventListener("pointerdown", (event) => {
    const key = event.target.closest(".piano-key");
    if (!key) return;
    event.preventDefault();
    els.piano.setPointerCapture(event.pointerId);
    const note = Number(key.dataset.note);
    heldByPointer.set(event.pointerId, note);
    noteOn(note);
  });

  // Glissando: dragging across keys moves the held note with the pointer.
  els.piano.addEventListener("pointermove", (event) => {
    if (!heldByPointer.has(event.pointerId)) return;
    const el = document.elementFromPoint(event.clientX, event.clientY);
    const key = el && el.closest && el.closest(".piano-key");
    if (!key) return;
    const note = Number(key.dataset.note);
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
  els.piano.addEventListener("pointerup", endPointer);
  els.piano.addEventListener("pointercancel", endPointer);

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
    const next = Math.max(MIN_BASE, Math.min(MAX_BASE, baseNote + delta * 12));
    if (next === baseNote) return;
    baseNote = next;
    // Held notes keep sounding (and release correctly, see heldByKey); only
    // the on-screen range moves.
    renderPiano();
  }

  function shiftVelocity(delta) {
    velocity = Math.max(1, Math.min(127, velocity + delta));
    els.velocityValue.textContent = String(velocity);
  }

  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey || event.metaKey || event.altKey || isTyping()) return;

    if (event.code in KEY_OFFSETS) {
      event.preventDefault();
      if (event.repeat || heldByKey.has(event.code)) return;
      const note = baseNote + KEY_OFFSETS[event.code];
      heldByKey.set(event.code, note);
      noteOn(note);
      return;
    }

    if (event.repeat) return;
    if (event.code === "KeyZ") shiftOctave(-1);
    else if (event.code === "KeyX") shiftOctave(1);
    else if (event.code === "KeyC") shiftVelocity(-VELOCITY_STEP);
    else if (event.code === "KeyV") shiftVelocity(VELOCITY_STEP);
    else if (event.code === "Escape") panic();
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
  renderPiano();
})();
