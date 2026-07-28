/* ============================================================
   STROBE TUNER — a hybrid of /tuner/'s live pitch identification and
   /multistrobe/'s per-note, per-octave strobe display: autocorrelation
   picks out which of the 12 notes is predominant (exactly like /tuner/'s
   note readout), then that single note's disc — built from the very same
   shared/strobe-disc.js engine /multistrobe/'s twelve discs are built
   from — is shown, with every one of its real octave-instances lit and
   spinning independently via Goertzel analysis.

   Only one disc is ever mounted at a time; discs are cached per note so
   switching back to a recently-played note doesn't rebuild its SVG.
   ============================================================ */

const noteNameEl = document.getElementById("noteName");
const noSignalHintEl = document.getElementById("noSignalHint");
const strobeSection = document.querySelector(".strobetuner");
const discContainer = document.getElementById("strobeDiscContainer");

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

const MIN_A4 = 392;
const MAX_A4 = 466;
const DEFAULT_A4 = 440;

// Autocorrelation only needs to resolve *which note* is sounding (not a
// precise cents reading — the disc's own Goertzel rings do that), so it
// runs on a short trailing window of the same buffer the Goertzel rings
// read from, matching /tuner/'s own FFT_SIZE rather than the much longer
// window the low-frequency rings need.
const AUTOCORRELATION_WINDOW = 4096;
const MIN_FREQ_HZ = 40;
const MAX_FREQ_HZ = 1600;
const MIN_RMS = 0.012;
const MIN_CLARITY = 0.9;

const PITCH_CHECK_INTERVAL_MS = 45;
const SILENCE_TIMEOUT_MS = 500;
// The floor of the Input Monitor's dB scale — anything quieter reads as
// silence rather than an ever-more-negative number.
const LEVEL_FLOOR_DB = -60;

// A much wider, half-circle geometry than /multistrobe/'s compact 90°
// discs — this page has room for exactly one disc to be the hero of the
// page, in the same half-circle style as /tuner/'s own strobe device.
const STAGE_GEOMETRY = {
  cx: 150,
  cy: 150,
  arcSpanDeg: 180,
  viewBox: "0 0 300 160",
  caseR: 145,
  windowR: 139,
  ringOuterR: 135,
  hubR: 8,
  hubDotR: 5,
  ringGap: 1,
};

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

const state = {
  a4: DEFAULT_A4,
  activeSource: null, // null | "mic"
  hasSignal: false,
  currentNoteName: null,
  lastConfidentAt: 0,
};

const discCache = new Map(); // note name -> disc
let activeDisc = null;

/* ============================================================
   PITCH DETECTION — time-domain autocorrelation (the standard "ACF2+"
   approach), restricted to the plausible instrument frequency range.
   Adapted from /tuner/'s detectPitch — only the note *name* is used here
   (the disc's Goertzel rings supply the actual cents readings), so there
   is no need for /tuner/'s temperament-aware frequency-to-note mapping.
   ============================================================ */
function detectPitch(buffer, sampleRate) {
  const size = buffer.length;
  let sumSquares = 0;

  for (let i = 0; i < size; i += 1) {
    sumSquares += buffer[i] * buffer[i];
  }

  const rms = Math.sqrt(sumSquares / size);

  if (rms < MIN_RMS) {
    return null;
  }

  const minLag = Math.max(2, Math.floor(sampleRate / MAX_FREQ_HZ));
  const maxLag = Math.min(size - 2, Math.floor(sampleRate / MIN_FREQ_HZ));

  if (maxLag <= minLag) {
    return null;
  }

  const correlations = new Float32Array(maxLag - minLag + 1);
  let bestIndex = -1;
  let bestValue = 0;

  for (let lag = minLag; lag <= maxLag; lag += 1) {
    let sum = 0;

    for (let i = 0; i < size - lag; i += 1) {
      sum += buffer[i] * buffer[i + lag];
    }

    const index = lag - minLag;
    correlations[index] = sum;

    if (sum > bestValue) {
      bestValue = sum;
      bestIndex = index;
    }
  }

  if (bestIndex < 0) {
    return null;
  }

  const clarity = bestValue / sumSquares;

  if (clarity < MIN_CLARITY) {
    return null;
  }

  let refinedLag = bestIndex + minLag;

  if (bestIndex > 0 && bestIndex < correlations.length - 1) {
    const c0 = correlations[bestIndex - 1];
    const c1 = correlations[bestIndex];
    const c2 = correlations[bestIndex + 1];
    const denom = c0 - 2 * c1 + c2;

    if (denom !== 0) {
      refinedLag = bestIndex + minLag + (0.5 * (c0 - c2)) / denom;
    }
  }

  if (refinedLag <= 0) {
    return null;
  }

  return { frequency: sampleRate / refinedLag, clarity };
}

function frequencyToPitchClassName(frequency, a4) {
  const equalMidi = 69 + 12 * Math.log2(frequency / a4);
  const rounded = Math.round(equalMidi);
  return NOTE_NAMES[((rounded % 12) + 12) % 12];
}

/* ============================================================
   DISC — a single instance of shared/strobe-disc.js's engine at this
   page's large STAGE_GEOMETRY. Discs are cached per note so switching
   between recently-heard notes doesn't rebuild their SVG each time.
   ============================================================ */
function getOrBuildDisc(name) {
  let disc = discCache.get(name);

  if (!disc) {
    const midiList = StrobeDiscEngine.midiListForPitchClass(NOTE_NAMES.indexOf(name));
    disc = StrobeDiscEngine.buildDisc(name, midiList, STAGE_GEOMETRY);
    discCache.set(name, disc);
  }

  return disc;
}

// Switches which disc is mounted/visible, if `name` isn't already the
// active one — recomputing its ring targets (which discards any
// now-stale in-flight phase tracking) since it's coming back from being
// idle. Called once per detected note change, never per frame.
function setActiveDisc(name, sampleRate) {
  if (activeDisc && activeDisc.name === name) {
    return activeDisc;
  }

  const disc = getOrBuildDisc(name);

  if (activeDisc) {
    activeDisc.el.hidden = true;
  }

  if (!disc.el.isConnected) {
    discContainer.appendChild(disc.el);
  }

  disc.el.hidden = false;
  StrobeDiscEngine.recomputeDiscTargets(disc, state.a4, sampleRate);
  activeDisc = disc;
  return disc;
}

/* ============================================================
   READOUT
   ============================================================ */
function updateReadout() {
  const inTune = !state.hasSignal;
  strobeSection.classList.toggle("in-tune", inTune);

  if (!state.hasSignal || !state.currentNoteName) {
    noteNameEl.textContent = "No Signal";
    noteNameEl.classList.add("is-no-signal");
    noSignalHintEl.textContent = state.activeSource === "mic" ? "Check your microphone" : "Start the Strobe Tuner or play a note";
    noSignalHintEl.hidden = false;
    return;
  }

  noteNameEl.classList.remove("is-no-signal");
  noSignalHintEl.hidden = true;
  noteNameEl.textContent = state.currentNoteName;
}

/* ============================================================
   INPUT MONITOR — a separate readout from the tuning display: how loud
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
  levelMeterFillEl.style.setProperty("--level-mix", String(Math.round(clamp((db + 12) / 12, 0, 1) * 100)));
  levelValueLabelEl.textContent = db <= LEVEL_FLOOR_DB ? "−∞ dB" : `${db.toFixed(1)} dB`;
}

function resetLevelMeter() {
  levelMeterFillEl.style.height = "0%";
  levelMeterFillEl.style.setProperty("--level-mix", "0");
  levelValueLabelEl.textContent = "−∞ dB";
}

function resetVisuals() {
  state.hasSignal = false;
  state.currentNoteName = null;

  if (activeDisc) {
    StrobeDiscEngine.resetDisc(activeDisc);
  }

  updateReadout();
  resetLevelMeter();
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

    const sampleRate = audioContext.sampleRate;
    // audioContext.currentTime (seconds, audio-clock), not
    // performance.now() — see StrobeDiscEngine.analyzeRing's comment for
    // why this matters.
    const now = audioContext.currentTime;

    const pitchWindow = timeDomainBuffer.subarray(timeDomainBuffer.length - AUTOCORRELATION_WINDOW);
    const result = detectPitch(pitchWindow, sampleRate);

    if (result) {
      state.hasSignal = true;
      state.lastConfidentAt = timestamp;
      state.currentNoteName = frequencyToPitchClassName(result.frequency, state.a4);
    } else if (state.hasSignal && timestamp - state.lastConfidentAt > SILENCE_TIMEOUT_MS) {
      state.hasSignal = false;
      state.currentNoteName = null;

      if (activeDisc) {
        StrobeDiscEngine.resetDisc(activeDisc);
      }
    }

    updateReadout();

    // The disc's own Goertzel rings — not the autocorrelation result —
    // drive the actual tuning display, exactly like /multistrobe/'s
    // discs: each ring independently decides whether it's hearing its
    // own exact target frequency, regardless of which note
    // autocorrelation currently thinks is predominant.
    if (state.hasSignal && state.currentNoteName) {
      const disc = setActiveDisc(state.currentNoteName, sampleRate);
      StrobeDiscEngine.analyzeDisc(disc, timeDomainBuffer, sampleRate, now);
    }
  }

  if (activeDisc) {
    StrobeDiscEngine.renderDisc(activeDisc, dt);
  }

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
  updateReadout();
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

  const sampleRate = audioContext ? audioContext.sampleRate : 44100;
  discCache.forEach((disc) => StrobeDiscEngine.recomputeDiscTargets(disc, state.a4, sampleRate));
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

updateReferencePitch(state.a4);
micGainValueLabelEl.textContent = `${Number(micGainRange.value).toFixed(1)}×`;
updateReadout();
resetLevelMeter();
