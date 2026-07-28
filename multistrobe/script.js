const toggleMicBtn = document.getElementById("toggleMicBtn");
const tuningStatementEl = document.getElementById("tuningStatement");
const micStatus = document.getElementById("micStatus");
const decreasePitchBtn = document.getElementById("decreasePitchBtn");
const increasePitchBtn = document.getElementById("increasePitchBtn");
const pitchInput = document.getElementById("pitchInput");
const pitchRange = document.getElementById("pitchRange");
const micGainRange = document.getElementById("micGainRange");
const micGainValueLabelEl = document.getElementById("micGainValueLabel");
const levelMeterFillEl = document.getElementById("levelMeterFill");
const levelValueLabelEl = document.getElementById("levelValueLabel");

const sharpsContainer = document.getElementById("strobeDiscsSharps");
const naturalsContainer = document.getElementById("strobeDiscsNaturals");

const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
let audioContext = null;
let analyserNode = null;
let mediaStream = null;
let mediaStreamSource = null;
let micGainNode = null;
let timeDomainBuffer = null;
let rafId;
let lastFrameAt = 0;
let lastPitchCheckAt = 0;

const NOTE_NAMES = StrobeDiscEngine.NOTE_NAMES;

// Where each sharp disc sits along the naturals row, expressed as which
// natural-key boundary (of 7) it floats above — e.g. C♯ sits right after C
// (boundary 1), matching a real piano keyboard's black-key spacing (no
// sharp between E-F or B-C, so F♯/G♯/A♯ pick up 2 boundaries further out).
const SHARP_BOUNDARY = { "C♯": 1, "D♯": 2, "F♯": 4, "G♯": 5, "A♯": 6 };
const NATURAL_COLUMN_COUNT = 7;

const MIN_A4 = 392;
const MAX_A4 = 466;
const DEFAULT_A4 = 440;

const PITCH_CHECK_INTERVAL_MS = 45;
// The floor of the Input Monitor's dB scale — anything quieter reads as
// silence rather than an ever-more-negative number.
const LEVEL_FLOOR_DB = -60;

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

const state = {
  a4: DEFAULT_A4,
  activeSource: null, // null | "mic"
};

const DISCS = []; // 12 entries (NOTE_NAMES order): { name, el, rings: [...] }

/* ============================================================
   DISCS — every disc is built from shared/strobe-disc.js's engine (the
   same code /strobetuner/'s single, large disc is built from), just at
   this page's compact piano-keyboard geometry. This file only owns what's
   specific to laying out 12 of them at once (piano positioning) and to
   this page's audio/controls plumbing — any improvement to the disc
   itself (ring layout, Goertzel analysis, rendering) lives in the shared
   engine and applies to both pages automatically.
   ============================================================ */
function buildDiscs() {
  NOTE_NAMES.forEach((name) => {
    const isSharp = name.includes("♯");
    const midiList = StrobeDiscEngine.midiListForPitchClass(NOTE_NAMES.indexOf(name));
    const disc = StrobeDiscEngine.buildDisc(name, midiList);

    if (isSharp) {
      disc.el.style.left = `${(SHARP_BOUNDARY[name] / NATURAL_COLUMN_COUNT) * 100}%`;
    }

    DISCS.push(disc);
    (isSharp ? sharpsContainer : naturalsContainer).appendChild(disc.el);
  });
}

// Recomputes every ring's target frequency (and the analysis window that
// depends on it) from the current A4 — called at load and whenever the
// reference pitch changes.
function recomputeRingTargets() {
  const sampleRate = audioContext ? audioContext.sampleRate : 44100;
  DISCS.forEach((disc) => StrobeDiscEngine.recomputeDiscTargets(disc, state.a4, sampleRate));
}

function resetVisuals() {
  DISCS.forEach((disc) => StrobeDiscEngine.resetDisc(disc));
  resetLevelMeter();
}

/* ============================================================
   INPUT MONITOR — a separate readout from the strobe display: how loud
   the (post-gain-boost) microphone signal is. Same as /tuner/'s.
   ============================================================ */
function computeRms(buffer) {
  let sumSquares = 0;

  for (let i = 0; i < buffer.length; i += 1) {
    sumSquares += buffer[i] * buffer[i];
  }

  return Math.sqrt(sumSquares / buffer.length);
}

function rmsToDb(rms) {
  if (rms <= 0) {
    return LEVEL_FLOOR_DB;
  }

  return Math.max(LEVEL_FLOOR_DB, 20 * Math.log10(rms));
}

function updateLevelMeter(rms) {
  const db = rmsToDb(rms);
  const percent = clamp(((db - LEVEL_FLOOR_DB) / -LEVEL_FLOOR_DB) * 100, 0, 100);
  levelMeterFillEl.style.height = `${percent}%`;
  // Gold up to a comfortable working level, warming toward the accent red
  // as the signal approaches 0 dB (clipping) — the last 12 dB of headroom.
  levelMeterFillEl.style.setProperty("--level-mix", String(Math.round(clamp((db + 12) / 12, 0, 1) * 100)));
  levelValueLabelEl.textContent = db <= LEVEL_FLOOR_DB ? "−∞ dB" : `${db.toFixed(1)} dB`;
}

function resetLevelMeter() {
  levelMeterFillEl.style.height = "0%";
  levelMeterFillEl.style.setProperty("--level-mix", "0");
  levelValueLabelEl.textContent = "−∞ dB";
}

/* ============================================================
   AUDIO SOURCE — microphone only (no test tone on this page, unlike
   /tuner/).
   ============================================================ */
function setMicStatus(message, isError) {
  micStatus.textContent = message;
  micStatus.classList.toggle("is-error", Boolean(isError));
}

function ensureAudioContext() {
  if (!AudioContextConstructor) {
    return null;
  }

  if (!audioContext) {
    audioContext = new AudioContextConstructor();
  }

  if (audioContext.state === "suspended") {
    audioContext.resume().catch(() => {});
  }

  return audioContext;
}

function ensureAnalyser() {
  if (!analyserNode) {
    analyserNode = audioContext.createAnalyser();
    analyserNode.fftSize = StrobeDiscEngine.ANALYSER_BUFFER_SIZE;
    timeDomainBuffer = new Float32Array(analyserNode.fftSize);
  }

  return analyserNode;
}

function beginRenderLoop() {
  lastFrameAt = performance.now();
  lastPitchCheckAt = 0;

  if (rafId === undefined) {
    rafId = window.requestAnimationFrame(mainLoop);
  }
}

function endRenderLoop() {
  if (rafId !== undefined) {
    window.cancelAnimationFrame(rafId);
    rafId = undefined;
  }
}

function mainLoop(timestamp) {
  if (!state.activeSource) {
    return;
  }

  const dt = Math.min((timestamp - lastFrameAt) / 1000, 0.1);
  lastFrameAt = timestamp;

  if (timestamp - lastPitchCheckAt >= PITCH_CHECK_INTERVAL_MS) {
    lastPitchCheckAt = timestamp;

    analyserNode.getFloatTimeDomainData(timeDomainBuffer);
    updateLevelMeter(computeRms(timeDomainBuffer));
    // audioContext.currentTime (seconds, audio-clock), not performance.now()
    // — see StrobeDiscEngine.analyzeRing's comment for why this matters.
    const now = audioContext.currentTime;
    const sampleRate = audioContext.sampleRate;

    DISCS.forEach((disc) => StrobeDiscEngine.analyzeDisc(disc, timeDomainBuffer, sampleRate, now));
  }

  DISCS.forEach((disc) => StrobeDiscEngine.renderDisc(disc, dt));
  rafId = window.requestAnimationFrame(mainLoop);
}

async function startMic() {
  if (state.activeSource === "mic") {
    return;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setMicStatus("Microphone access isn't supported in this browser.", true);
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 },
    });
  } catch (error) {
    if (error && error.name === "NotAllowedError") {
      setMicStatus("Microphone access was denied. Allow it in your browser's address bar and try again.", true);
    } else if (error && error.name === "NotFoundError") {
      setMicStatus("No microphone was found on this device.", true);
    } else {
      setMicStatus("Couldn't access the microphone. Please try again.", true);
    }
    return;
  }

  const ctx = ensureAudioContext();

  if (!ctx) {
    setMicStatus("Web Audio isn't supported in this browser.", true);
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
    return;
  }

  ensureAnalyser();
  // The real device sample rate is only known once the context exists —
  // recompute every ring's window length against it now, rather than the
  // 44.1kHz guess recomputeRingTargets() used at load.
  recomputeRingTargets();

  mediaStreamSource = ctx.createMediaStreamSource(mediaStream);
  micGainNode = ctx.createGain();
  micGainNode.gain.value = Number(micGainRange.value);
  mediaStreamSource.connect(micGainNode);
  micGainNode.connect(analyserNode);
  // Deliberately not connected to audioContext.destination — we only
  // analyze the signal, never play it back, so there's no feedback loop.

  state.activeSource = "mic";
  toggleMicBtn.textContent = "Stop Tuner";
  toggleMicBtn.setAttribute("aria-pressed", "true");
  setMicStatus("Listening… play a note.");
  beginRenderLoop();
}

function stopMic() {
  if (state.activeSource !== "mic") {
    return;
  }

  state.activeSource = null;

  if (mediaStreamSource) {
    mediaStreamSource.disconnect();
    mediaStreamSource = null;
  }

  if (micGainNode) {
    micGainNode.disconnect();
    micGainNode = null;
  }

  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }

  toggleMicBtn.textContent = "Start Tuner";
  toggleMicBtn.setAttribute("aria-pressed", "false");
  setMicStatus("Uses your microphone. Nothing is recorded or sent anywhere.");
  endRenderLoop();
  resetVisuals();
}

function toggleMic() {
  if (state.activeSource === "mic") {
    stopMic();
  } else {
    startMic();
  }
}

/* ============================================================
   CONTROLS
   ============================================================ */
function updateTuningStatement() {
  tuningStatementEl.textContent = `Tuning at ${state.a4} Hz`;
}

function updateReferencePitch(value) {
  state.a4 = clamp(Math.round(Number(value) || DEFAULT_A4), MIN_A4, MAX_A4);
  pitchInput.value = String(state.a4);
  pitchRange.value = String(state.a4);
  updateTuningStatement();
  recomputeRingTargets();
}

pitchInput.addEventListener("input", (event) => updateReferencePitch(event.target.value));
pitchRange.addEventListener("input", (event) => updateReferencePitch(event.target.value));
// A double-click anywhere on the reference pitch bar snaps it back to A440.
pitchRange.addEventListener("dblclick", () => updateReferencePitch(DEFAULT_A4));
decreasePitchBtn.addEventListener("click", () => updateReferencePitch(state.a4 - 1));
increasePitchBtn.addEventListener("click", () => updateReferencePitch(state.a4 + 1));

toggleMicBtn.addEventListener("click", toggleMic);

micGainRange.addEventListener("input", (event) => {
  const gain = Number(event.target.value);
  micGainValueLabelEl.textContent = `${gain.toFixed(1)}×`;

  if (micGainNode) {
    micGainNode.gain.setTargetAtTime(gain, audioContext.currentTime, 0.01);
  }
});

// Collapsible frames: each panel-header's toggle hides everything in its
// .control-block except the header (see the .is-collapsed CSS rule).
document.querySelectorAll(".collapse-toggle").forEach((toggle) => {
  toggle.addEventListener("click", () => {
    const panel = toggle.closest(".control-block");
    const collapsed = panel.classList.toggle("is-collapsed");
    toggle.setAttribute("aria-expanded", String(!collapsed));
  });
});

document.addEventListener("keydown", (event) => {
  const focusedTag = document.activeElement?.tagName;
  const isFormElement = focusedTag === "INPUT" || focusedTag === "SELECT" || focusedTag === "TEXTAREA";

  if (event.code === "Space" && !isFormElement) {
    event.preventDefault();
    toggleMic();
  }

  if (event.key === "ArrowUp" && !isFormElement) {
    event.preventDefault();
    updateReferencePitch(state.a4 + 1);
  }

  if (event.key === "ArrowDown" && !isFormElement) {
    event.preventDefault();
    updateReferencePitch(state.a4 - 1);
  }
});

// Release the microphone when the tab is hidden, rather than leaving it
// running in the background.
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopMic();
  }
});

buildDiscs();
updateReferencePitch(state.a4);
micGainValueLabelEl.textContent = `${Number(micGainRange.value).toFixed(1)}×`;
resetVisuals();
