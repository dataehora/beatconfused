const SVG_NS = "http://www.w3.org/2000/svg";

const tunerSection = document.querySelector(".tuner");
const noteNameEl = document.getElementById("noteName");
const centsValueEl = document.getElementById("centsValue");
const freqValueEl = document.getElementById("freqValue");

const strobeVisual = document.getElementById("strobeVisual");
const needleVisual = document.getElementById("needleVisual");
const meterVisual = document.getElementById("meterVisual");
const needleSwingEl = document.getElementById("needleSwing");
const ledSegmentsContainer = document.getElementById("ledSegments");
const ledIndicatorEl = document.getElementById("ledIndicator");

const toggleMicBtn = document.getElementById("toggleMicBtn");
const micStatus = document.getElementById("micStatus");
const decreasePitchBtn = document.getElementById("decreasePitchBtn");
const increasePitchBtn = document.getElementById("increasePitchBtn");
const pitchInput = document.getElementById("pitchInput");
const pitchRange = document.getElementById("pitchRange");
const visualModeInputs = document.querySelectorAll('input[name="tunerVisualMode"]');
const pitchPresetInputs = document.querySelectorAll('input[name="pitchPreset"]');

const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
let audioContext = null;
let analyserNode = null;
let mediaStream = null;
let mediaStreamSource = null;
let timeDomainBuffer = null;
let rafId;
let lastFrameAt = 0;
let lastPitchCheckAt = 0;

const NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];

const MIN_A4 = 415;
const MAX_A4 = 466;
const DEFAULT_A4 = 440;
const MIN_FREQ_HZ = 40;
const MAX_FREQ_HZ = 1600;
const FFT_SIZE = 4096;
const MIN_RMS = 0.012;
const MIN_CLARITY = 0.9;
const PITCH_CHECK_INTERVAL_MS = 45;
const SILENCE_TIMEOUT_MS = 500;
const CENTS_SMOOTHING = 0.25;
const NEEDLE_DAMPING = 0.18;
const IN_TUNE_THRESHOLD_CENTS = 5;
const STROBE_DEADZONE_CENTS = 1.5;
const NEEDLE_PIVOT = { x: 120, y: 150 };
const NEEDLE_MAX_CENTS = 50;
const NEEDLE_MAX_DEG = 45;
const LED_MAX_CENTS = 50;
const LED_STEP_CENTS = 5;

const STROBE_RINGS = [
  { id: "strobeRingOuter", innerR: 76, outerR: 94, count: 40, speed: 5.4, direction: 1, angle: 0, el: null },
  { id: "strobeRingMiddle", innerR: 50, outerR: 72, count: 28, speed: 8.2, direction: -1, angle: 0, el: null },
  { id: "strobeRingInner", innerR: 22, outerR: 46, count: 16, speed: 12.6, direction: 1, angle: 0, el: null },
];

const state = {
  a4: DEFAULT_A4,
  listening: false,
  hasSignal: false,
  smoothedCents: 0,
  needleAngle: 0,
  currentNote: null,
  lastFrequency: 0,
  lastConfidentAt: 0,
};

let ledDotElements = [];

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

/* ============================================================
   PITCH DETECTION — time-domain autocorrelation (the standard
   "ACF2+" approach), restricted to the plausible instrument
   frequency range so the O(bufferSize * lagRange) cost stays cheap
   enough to run several times a second in plain JS. A normalized
   correlation peak below MIN_CLARITY is treated as "no clear pitch"
   (background noise, breath, pick noise, silence).
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
      refinedLag = bestIndex + minLag + 0.5 * (c0 - c2) / denom;
    }
  }

  if (refinedLag <= 0) {
    return null;
  }

  return { frequency: sampleRate / refinedLag, clarity };
}

function frequencyToNote(frequency, a4) {
  const midi = 69 + 12 * Math.log2(frequency / a4);
  const rounded = Math.round(midi);
  const cents = (midi - rounded) * 100;
  const name = NOTE_NAMES[((rounded % 12) + 12) % 12];
  const octave = Math.floor(rounded / 12) - 1;
  return { name, octave, cents };
}

function centsToNeedleAngle(cents) {
  const clamped = clamp(cents, -NEEDLE_MAX_CENTS, NEEDLE_MAX_CENTS);
  return (clamped / NEEDLE_MAX_CENTS) * NEEDLE_MAX_DEG;
}

function polarPoint(cx, cy, r, angleDeg) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.sin(rad), y: cy - r * Math.cos(rad) };
}

/* ============================================================
   DEVICE GRAPHICS — built once at load. Rotation for both the
   strobe rings and the needle is applied via the SVG transform
   ATTRIBUTE (not CSS transform-origin), matching the metronome
   pendulum's approach: it sidesteps transform-box inconsistencies
   across browsers (notably mobile Safari) and needs no extra setup.
   ============================================================ */
function buildStrobeRings() {
  const cx = 120;
  const cy = 118;

  STROBE_RINGS.forEach((ring) => {
    const gEl = document.getElementById(ring.id);
    ring.el = gEl;
    gEl.innerHTML = "";

    for (let i = 0; i < ring.count; i += 1) {
      const angle = (i / ring.count) * 360;
      const rad = (angle * Math.PI) / 180;
      const x1 = cx + ring.innerR * Math.sin(rad);
      const y1 = cy - ring.innerR * Math.cos(rad);
      const x2 = cx + ring.outerR * Math.sin(rad);
      const y2 = cy - ring.outerR * Math.cos(rad);

      const line = document.createElementNS(SVG_NS, "line");
      line.setAttribute("x1", x1.toFixed(2));
      line.setAttribute("y1", y1.toFixed(2));
      line.setAttribute("x2", x2.toFixed(2));
      line.setAttribute("y2", y2.toFixed(2));
      gEl.appendChild(line);
    }
  });
}

function buildNeedleScale() {
  const ticksGroup = document.getElementById("needleScaleTicks");
  const arcGroup = document.getElementById("needleInTuneArc");
  const majorTicks = [-50, 0, 50];
  const minorTicks = [-40, -30, -20, -10, 10, 20, 30, 40];

  [...majorTicks, ...minorTicks].forEach((cents) => {
    const isMajor = majorTicks.includes(cents);
    const angle = centsToNeedleAngle(cents);
    const outer = polarPoint(NEEDLE_PIVOT.x, NEEDLE_PIVOT.y, 96, angle);
    const inner = polarPoint(NEEDLE_PIVOT.x, NEEDLE_PIVOT.y, isMajor ? 80 : 86, angle);

    const line = document.createElementNS(SVG_NS, "line");
    line.setAttribute("x1", inner.x.toFixed(2));
    line.setAttribute("y1", inner.y.toFixed(2));
    line.setAttribute("x2", outer.x.toFixed(2));
    line.setAttribute("y2", outer.y.toFixed(2));

    if (isMajor) {
      line.classList.add("major");
    }

    ticksGroup.appendChild(line);
  });

  const r = 88;
  const start = polarPoint(NEEDLE_PIVOT.x, NEEDLE_PIVOT.y, r, centsToNeedleAngle(-5));
  const end = polarPoint(NEEDLE_PIVOT.x, NEEDLE_PIVOT.y, r, centsToNeedleAngle(5));
  const path = document.createElementNS(SVG_NS, "path");
  path.setAttribute(
    "d",
    `M ${start.x.toFixed(2)} ${start.y.toFixed(2)} A ${r} ${r} 0 0 1 ${end.x.toFixed(2)} ${end.y.toFixed(2)}`
  );
  arcGroup.appendChild(path);
}

function buildLedSegments() {
  ledSegmentsContainer.innerHTML = "";
  ledDotElements = [];

  for (let cents = -LED_MAX_CENTS; cents <= LED_MAX_CENTS; cents += LED_STEP_CENTS) {
    const dot = document.createElement("span");
    dot.className = "led-dot";

    if (cents === 0) {
      dot.classList.add("center");
    } else if (Math.abs(cents) >= 30) {
      dot.classList.add("edge");
    }

    ledSegmentsContainer.appendChild(dot);
    ledDotElements.push({ cents, el: dot });
  }
}

/* ============================================================
   RENDERING — called every animation frame regardless of which
   visual mode is active (all three stay in sync at once, same as
   the metronome's pulse/numbers/pendulum), so switching modes never
   shows a stale reading.
   ============================================================ */
function renderStrobe(dt) {
  const cents = state.hasSignal ? state.smoothedCents : 0;
  const effectiveCents = Math.abs(cents) < STROBE_DEADZONE_CENTS ? 0 : cents;

  STROBE_RINGS.forEach((ring) => {
    ring.angle = (ring.angle + effectiveCents * ring.speed * ring.direction * dt) % 360;
    ring.el.setAttribute("transform", `rotate(${ring.angle.toFixed(2)} 120 118)`);
  });
}

function renderNeedle() {
  const targetCents = state.hasSignal ? state.smoothedCents : 0;
  const targetAngle = centsToNeedleAngle(targetCents);
  state.needleAngle += (targetAngle - state.needleAngle) * NEEDLE_DAMPING;
  needleSwingEl.setAttribute("transform", `rotate(${state.needleAngle.toFixed(2)} ${NEEDLE_PIVOT.x} ${NEEDLE_PIVOT.y})`);
}

function renderMeter() {
  const hasSignal = state.hasSignal;
  const clamped = clamp(state.smoothedCents, -LED_MAX_CENTS, LED_MAX_CENTS);

  ledDotElements.forEach(({ cents, el }) => {
    let lit = false;

    if (hasSignal) {
      if (cents === 0) {
        lit = Math.abs(clamped) <= IN_TUNE_THRESHOLD_CENTS;
      } else if (cents > 0) {
        lit = clamped >= cents;
      } else {
        lit = clamped <= cents;
      }
    }

    el.classList.toggle("lit", lit);
  });

  if (hasSignal) {
    const percent = 50 + (clamped / LED_MAX_CENTS) * 50;
    ledIndicatorEl.style.left = `${percent}%`;
    ledIndicatorEl.classList.add("visible");
  } else {
    ledIndicatorEl.classList.remove("visible");
  }
}

function updateReadout() {
  const inTune = state.hasSignal && Math.abs(state.smoothedCents) <= IN_TUNE_THRESHOLD_CENTS;
  tunerSection.classList.toggle("in-tune", inTune);

  if (!state.hasSignal || !state.currentNote) {
    noteNameEl.textContent = "–";
    centsValueEl.textContent = "0¢";
    freqValueEl.textContent = "— Hz";
    return;
  }

  const { name, octave } = state.currentNote;
  noteNameEl.textContent = `${name}${octave}`;
  const roundedCents = Math.round(state.smoothedCents);
  const sign = roundedCents > 0 ? "+" : "";
  centsValueEl.textContent = `${sign}${roundedCents}¢`;
  freqValueEl.textContent = `${state.lastFrequency.toFixed(1)} Hz`;
}

function resetVisuals() {
  state.hasSignal = false;
  state.smoothedCents = 0;
  state.currentNote = null;
  state.needleAngle = 0;
  updateReadout();
  needleSwingEl.setAttribute("transform", `rotate(0 ${NEEDLE_PIVOT.x} ${NEEDLE_PIVOT.y})`);
  renderMeter();
}

/* ============================================================
   MIC LIFECYCLE
   ============================================================ */
function setMicStatus(message, isError) {
  micStatus.textContent = message;
  micStatus.classList.toggle("is-error", Boolean(isError));
}

function mainLoop(timestamp) {
  if (!state.listening) {
    return;
  }

  const dt = Math.min((timestamp - lastFrameAt) / 1000, 0.1);
  lastFrameAt = timestamp;

  if (timestamp - lastPitchCheckAt >= PITCH_CHECK_INTERVAL_MS) {
    lastPitchCheckAt = timestamp;
    analyserNode.getFloatTimeDomainData(timeDomainBuffer);
    const result = detectPitch(timeDomainBuffer, audioContext.sampleRate);

    if (result) {
      const note = frequencyToNote(result.frequency, state.a4);
      state.smoothedCents += (note.cents - state.smoothedCents) * CENTS_SMOOTHING;
      state.hasSignal = true;
      state.lastConfidentAt = timestamp;
      state.currentNote = note;
      state.lastFrequency = result.frequency;
    } else if (state.hasSignal && timestamp - state.lastConfidentAt > SILENCE_TIMEOUT_MS) {
      state.hasSignal = false;
      state.smoothedCents = 0;
    }

    updateReadout();
    renderMeter();
  }

  renderStrobe(dt);
  renderNeedle();
  rafId = window.requestAnimationFrame(mainLoop);
}

async function startTuner() {
  if (state.listening) {
    return;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setMicStatus("Microphone access isn't supported in this browser.", true);
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
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

  if (!AudioContextConstructor) {
    setMicStatus("Web Audio isn't supported in this browser.", true);
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
    return;
  }

  if (!audioContext) {
    audioContext = new AudioContextConstructor();
  }

  if (audioContext.state === "suspended") {
    await audioContext.resume().catch(() => {});
  }

  analyserNode = audioContext.createAnalyser();
  analyserNode.fftSize = FFT_SIZE;
  timeDomainBuffer = new Float32Array(analyserNode.fftSize);

  mediaStreamSource = audioContext.createMediaStreamSource(mediaStream);
  mediaStreamSource.connect(analyserNode);
  // Deliberately not connected to audioContext.destination — we only
  // analyze the signal, never play it back, so there's no feedback loop.

  state.listening = true;
  toggleMicBtn.textContent = "Stop Tuner";
  toggleMicBtn.setAttribute("aria-pressed", "true");
  setMicStatus("Listening… play a note.");
  lastFrameAt = performance.now();
  lastPitchCheckAt = 0;
  rafId = window.requestAnimationFrame(mainLoop);
}

function stopTuner() {
  if (!state.listening) {
    return;
  }

  state.listening = false;

  if (rafId !== undefined) {
    window.cancelAnimationFrame(rafId);
    rafId = undefined;
  }

  if (mediaStreamSource) {
    mediaStreamSource.disconnect();
    mediaStreamSource = null;
  }

  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }

  analyserNode = null;
  toggleMicBtn.textContent = "Start Tuner";
  toggleMicBtn.setAttribute("aria-pressed", "false");
  setMicStatus("Uses your microphone. Nothing is recorded or sent anywhere.");
  resetVisuals();
}

function toggleTuner() {
  if (state.listening) {
    stopTuner();
  } else {
    startTuner();
  }
}

/* ============================================================
   CONTROLS
   ============================================================ */
function setVisualMode() {
  const mode = document.querySelector('input[name="tunerVisualMode"]:checked')?.value || "strobe";
  tunerSection.dataset.visualMode = mode;
  strobeVisual.hidden = mode !== "strobe";
  needleVisual.hidden = mode !== "needle";
  meterVisual.hidden = mode !== "meter";
}

function updateReferencePitch(value) {
  state.a4 = clamp(Math.round(Number(value) || DEFAULT_A4), MIN_A4, MAX_A4);
  pitchInput.value = String(state.a4);
  pitchRange.value = String(state.a4);

  pitchPresetInputs.forEach((input) => {
    input.checked = Number(input.value) === state.a4;
  });
}

pitchInput.addEventListener("input", (event) => updateReferencePitch(event.target.value));
pitchRange.addEventListener("input", (event) => updateReferencePitch(event.target.value));
decreasePitchBtn.addEventListener("click", () => updateReferencePitch(state.a4 - 1));
increasePitchBtn.addEventListener("click", () => updateReferencePitch(state.a4 + 1));

pitchPresetInputs.forEach((input) => {
  input.addEventListener("change", () => updateReferencePitch(input.value));
});

visualModeInputs.forEach((input) => {
  input.addEventListener("change", setVisualMode);
});

toggleMicBtn.addEventListener("click", toggleTuner);

document.addEventListener("keydown", (event) => {
  const focusedTag = document.activeElement?.tagName;
  const isFormElement = focusedTag === "INPUT" || focusedTag === "SELECT" || focusedTag === "TEXTAREA";

  if (event.code === "Space" && !isFormElement) {
    event.preventDefault();
    toggleTuner();
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

// Release the microphone when the tab is hidden rather than leaving it
// listening in the background.
document.addEventListener("visibilitychange", () => {
  if (document.hidden && state.listening) {
    stopTuner();
  }
});

buildStrobeRings();
buildNeedleScale();
buildLedSegments();
setVisualMode();
updateReferencePitch(state.a4);
resetVisuals();
