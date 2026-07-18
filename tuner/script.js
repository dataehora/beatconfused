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

const testToneRange = document.getElementById("testToneRange");
const testToneCentsRange = document.getElementById("testToneCentsRange");
const testToneVolume = document.getElementById("testToneVolume");
const toggleTestToneBtn = document.getElementById("toggleTestToneBtn");
const decreaseTestToneBtn = document.getElementById("decreaseTestToneBtn");
const increaseTestToneBtn = document.getElementById("increaseTestToneBtn");
const testToneNoteEl = document.getElementById("testToneNote");
const testToneFreqLabelEl = document.getElementById("testToneFreqLabel");
const varianceFillEl = document.getElementById("varianceFill");
const variancePrevNoteEl = document.getElementById("variancePrevNote");
const varianceCurrentNoteEl = document.getElementById("varianceCurrentNote");
const varianceNextNoteEl = document.getElementById("varianceNextNote");

const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
let audioContext = null;
let analyserNode = null;
let mediaStream = null;
let mediaStreamSource = null;
let testOscillator = null;
let testGainNode = null;
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
const IN_TUNE_THRESHOLD_CENTS = 1;
const MAX_UNTUNED_CENTS = 50;
const STROBE_DEADZONE_CENTS = 1.5;
const NEEDLE_PIVOT = { x: 120, y: 150 };
const NEEDLE_MAX_CENTS = 50;
const NEEDLE_MAX_DEG = 45;
const LED_MAX_CENTS = 50;
const LED_STEP_CENTS = 5;

// Five rings graduating from a slow outer band to a fast inner one, closer
// to a real optical strobe disc (e.g. the Peterson StroboStomp HD) than a
// simple two- or three-ring toy. Segment counts follow a strict power-of-two
// ratio (128:64:32:16:8, outer to inner) — on a physical strobe disc this is
// what lets rings representing successive octaves of the same note all
// freeze at once under a single rotation speed: a note at 2F needs exactly
// double the segments of one at F to appear stationary at the same speed
// (2F / 2N = F / N).
const STROBE_CENTER = { x: 150, y: 150 };
const STROBE_RINGS = [
  { id: "strobeRing1", innerR: 104, outerR: 120, count: 128, speed: 3.0, direction: 1, angle: 0, el: null },
  { id: "strobeRing2", innerR: 86, outerR: 100, count: 64, speed: 4.6, direction: -1, angle: 0, el: null },
  { id: "strobeRing3", innerR: 68, outerR: 82, count: 32, speed: 6.4, direction: 1, angle: 0, el: null },
  { id: "strobeRing4", innerR: 50, outerR: 64, count: 16, speed: 8.6, direction: -1, angle: 0, el: null },
  { id: "strobeRing5", innerR: 28, outerR: 44, count: 8, speed: 11.2, direction: 1, angle: 0, el: null },
];

const state = {
  a4: DEFAULT_A4,
  activeSource: null, // null | "mic" | "test"
  hasSignal: false,
  smoothedCents: 0,
  needleAngle: 0,
  currentNote: null,
  lastFrequency: 0,
  lastConfidentAt: 0,
};

let ledDotElements = [];

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

// How far a reading sits between "just out of the green zone" (pure brown,
// 0%) and "as untuned as the scale goes" (pure gray, 100%). Consumed by
// CSS color-mix() rules — see .note-name / .strobe-ring / .needle-pointer /
// .variance-fill — so within the green zone itself (|cents| <= threshold)
// this value is irrelevant: a separate, more specific ".in-tune" rule wins
// and snaps the color straight to green, same as before.
function getTuneMixPercent(cents) {
  const abs = Math.abs(cents);

  if (abs <= IN_TUNE_THRESHOLD_CENTS) {
    return 0;
  }

  const t = (abs - IN_TUNE_THRESHOLD_CENTS) / (MAX_UNTUNED_CENTS - IN_TUNE_THRESHOLD_CENTS);
  return Math.round(clamp(t, 0, 1) * 100);
}

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
  return { name, octave, cents, midi: rounded };
}

function noteNameForMidi(midi) {
  const name = NOTE_NAMES[((midi % 12) + 12) % 12];
  const octave = Math.floor(midi / 12) - 1;
  return `${name}${octave}`;
}

function centsToNeedleAngle(cents) {
  const clamped = clamp(cents, -NEEDLE_MAX_CENTS, NEEDLE_MAX_CENTS);
  return (clamped / NEEDLE_MAX_CENTS) * NEEDLE_MAX_DEG;
}

function polarPoint(cx, cy, r, angleDeg) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.sin(rad), y: cy - r * Math.cos(rad) };
}

// One annulus wedge (a "donut slice") spanning startDeg..endDeg between
// innerR and outerR — the building block of the strobe rings below.
function annulusWedgePath(cx, cy, innerR, outerR, startDeg, endDeg) {
  const startOuter = polarPoint(cx, cy, outerR, startDeg);
  const endOuter = polarPoint(cx, cy, outerR, endDeg);
  const startInner = polarPoint(cx, cy, innerR, startDeg);
  const endInner = polarPoint(cx, cy, innerR, endDeg);
  const largeArc = endDeg - startDeg > 180 ? 1 : 0;

  return [
    `M ${startInner.x.toFixed(2)} ${startInner.y.toFixed(2)}`,
    `L ${startOuter.x.toFixed(2)} ${startOuter.y.toFixed(2)}`,
    `A ${outerR} ${outerR} 0 ${largeArc} 1 ${endOuter.x.toFixed(2)} ${endOuter.y.toFixed(2)}`,
    `L ${endInner.x.toFixed(2)} ${endInner.y.toFixed(2)}`,
    `A ${innerR} ${innerR} 0 ${largeArc} 0 ${startInner.x.toFixed(2)} ${startInner.y.toFixed(2)}`,
    "Z",
  ].join(" ");
}

/* ============================================================
   DEVICE GRAPHICS — built once at load. Rotation for both the
   strobe rings and the needle is applied via the SVG transform
   ATTRIBUTE (not CSS transform-origin), matching the metronome
   pendulum's approach: it sidesteps transform-box inconsistencies
   across browsers (notably mobile Safari) and needs no extra setup.

   Each strobe ring is built as true alternating pie-wedge segments —
   a full colored step followed by a full empty step of the same
   angular width — matching a classic optical strobe disc (e.g. the
   Conn Strobotuner), rather than thin tick marks with gaps between.
   `count` filled wedges alternate with `count` equal-width empty
   gaps, so the ring is divided into count * 2 equal slices in total.
   ============================================================ */
function buildStrobeRings() {
  const { x: cx, y: cy } = STROBE_CENTER;

  STROBE_RINGS.forEach((ring) => {
    const gEl = document.getElementById(ring.id);
    ring.el = gEl;
    gEl.innerHTML = "";

    const totalSlices = ring.count * 2;
    const step = 360 / totalSlices;

    for (let i = 0; i < totalSlices; i += 2) {
      const path = document.createElementNS(SVG_NS, "path");
      path.setAttribute("d", annulusWedgePath(cx, cy, ring.innerR, ring.outerR, i * step, (i + 1) * step));
      gEl.appendChild(path);
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
    ring.el.setAttribute("transform", `rotate(${ring.angle.toFixed(2)} ${STROBE_CENTER.x} ${STROBE_CENTER.y})`);
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
  tunerSection.style.setProperty("--tune-mix", String(state.hasSignal ? getTuneMixPercent(state.smoothedCents) : 0));

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

  // With no tone playing, every ring's wedge boundaries should line up
  // along the same radial lines (as in a physical strobe disc at rest),
  // not stay wherever they last drifted to before the tuner was stopped.
  STROBE_RINGS.forEach((ring) => {
    ring.angle = 0;

    if (ring.el) {
      ring.el.setAttribute("transform", `rotate(0 ${STROBE_CENTER.x} ${STROBE_CENTER.y})`);
    }
  });
}

/* ============================================================
   AUDIO SOURCE LIFECYCLE — the microphone and the test-tone generator
   are two interchangeable sources feeding the same analyser and the
   same render loop; only one is ever active at a time (starting one
   stops the other).
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
    analyserNode.fftSize = FFT_SIZE;
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

    if (state.activeSource === "test") {
      // The test tone's frequency is already known exactly, so the readout
      // is computed directly from it rather than detected — this keeps it
      // immune to gain/volume changes, which briefly disturb the analysed
      // waveform (and therefore the autocorrelation result) if routed
      // through the same detector used for the microphone.
      const testFrequency = getTestToneFrequency();
      const note = frequencyToNote(testFrequency, state.a4);
      state.smoothedCents += (note.cents - state.smoothedCents) * CENTS_SMOOTHING;
      state.hasSignal = true;
      state.lastConfidentAt = timestamp;
      state.currentNote = note;
      state.lastFrequency = testFrequency;
    } else {
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
    }

    updateReadout();
    renderMeter();
  }

  renderStrobe(dt);
  renderNeedle();
  rafId = window.requestAnimationFrame(mainLoop);
}

async function startMic() {
  if (state.activeSource === "mic") {
    return;
  }

  if (state.activeSource === "test") {
    stopTestTone();
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

  const ctx = ensureAudioContext();

  if (!ctx) {
    setMicStatus("Web Audio isn't supported in this browser.", true);
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
    return;
  }

  ensureAnalyser();
  mediaStreamSource = ctx.createMediaStreamSource(mediaStream);
  mediaStreamSource.connect(analyserNode);
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
   TEST TONE — an oscillator routed to the speakers so it's audible,
   but NOT into the analyser: its readout is computed directly from
   the known set frequency (see mainLoop) rather than detected, so
   it can't be perturbed by gain/volume changes.
   ============================================================ */
function startTestTone() {
  if (state.activeSource === "test") {
    return;
  }

  if (state.activeSource === "mic") {
    stopMic();
  }

  const ctx = ensureAudioContext();

  if (!ctx) {
    setMicStatus("Web Audio isn't supported in this browser.", true);
    return;
  }

  testOscillator = ctx.createOscillator();
  testOscillator.type = "sine";
  testOscillator.frequency.setValueAtTime(getTestToneFrequency(), ctx.currentTime);

  testGainNode = ctx.createGain();
  testGainNode.gain.setValueAtTime(Number(testToneVolume.value), ctx.currentTime);

  testOscillator.connect(testGainNode);
  testGainNode.connect(ctx.destination);
  testOscillator.start();

  state.activeSource = "test";
  toggleTestToneBtn.textContent = "Stop Test Tone";
  toggleTestToneBtn.setAttribute("aria-pressed", "true");
  beginRenderLoop();
}

function stopTestTone() {
  if (state.activeSource !== "test") {
    return;
  }

  state.activeSource = null;

  if (testOscillator) {
    testOscillator.stop();
    testOscillator.disconnect();
    testOscillator = null;
  }

  if (testGainNode) {
    testGainNode.disconnect();
    testGainNode = null;
  }

  toggleTestToneBtn.textContent = "Play Test Tone";
  toggleTestToneBtn.setAttribute("aria-pressed", "false");
  endRenderLoop();
  resetVisuals();
}

function toggleTestTone() {
  if (state.activeSource === "test") {
    stopTestTone();
  } else {
    startTestTone();
  }
}

function stopActiveSource() {
  if (state.activeSource === "mic") {
    stopMic();
  } else if (state.activeSource === "test") {
    stopTestTone();
  }
}

// The Frequency slider sets a whole-Hz base; the Fine Tuning slider adds a
// continuous 0-1 Hz offset on top of it, covering exactly the gap between
// that base and the next Hz up.
function getTestToneFrequency() {
  return Number(testToneRange.value) + Number(testToneCentsRange.value);
}

function updateTestToneDisplay(frequency) {
  testToneFreqLabelEl.textContent = `${frequency.toFixed(2)} Hz`;
  const note = frequencyToNote(frequency, state.a4);
  const roundedCents = Math.round(note.cents);
  const sign = roundedCents > 0 ? "+" : "";
  testToneNoteEl.textContent = `${note.name}${note.octave} ${sign}${roundedCents}¢`;
  updateVarianceBar(note);
}

// A single lean fill growing outward from a center tick (the nearest note)
// toward whichever neighbor the tone is drifting closer to — how far it's
// come from the current note, and how much room is left before the next.
function updateVarianceBar(note) {
  const clamped = clamp(note.cents, -50, 50);

  if (clamped >= 0) {
    varianceFillEl.style.left = "50%";
    varianceFillEl.style.width = `${clamped}%`;
  } else {
    varianceFillEl.style.left = `${50 + clamped}%`;
    varianceFillEl.style.width = `${-clamped}%`;
  }

  varianceFillEl.classList.toggle("in-tune", Math.abs(note.cents) <= IN_TUNE_THRESHOLD_CENTS);
  varianceFillEl.style.setProperty("--tune-mix", String(getTuneMixPercent(note.cents)));
  variancePrevNoteEl.textContent = noteNameForMidi(note.midi - 1);
  varianceCurrentNoteEl.textContent = `${note.name}${note.octave}`;
  varianceNextNoteEl.textContent = noteNameForMidi(note.midi + 1);
}

function nudgeTestToneFrequency(deltaHz) {
  const next = clamp(Number(testToneRange.value) + deltaHz, Number(testToneRange.min), Number(testToneRange.max));
  testToneRange.value = String(next);
  const combined = getTestToneFrequency();
  updateTestToneDisplay(combined);

  if (state.activeSource === "test" && testOscillator) {
    testOscillator.frequency.setTargetAtTime(combined, audioContext.currentTime, 0.01);
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

  updateTestToneDisplay(getTestToneFrequency());
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

toggleMicBtn.addEventListener("click", toggleMic);
toggleTestToneBtn.addEventListener("click", toggleTestTone);
decreaseTestToneBtn.addEventListener("click", () => nudgeTestToneFrequency(-1));
increaseTestToneBtn.addEventListener("click", () => nudgeTestToneFrequency(1));

function handleTestToneFrequencyInput() {
  const combined = getTestToneFrequency();
  updateTestToneDisplay(combined);

  if (state.activeSource === "test" && testOscillator) {
    testOscillator.frequency.setTargetAtTime(combined, audioContext.currentTime, 0.01);
  }
}

testToneRange.addEventListener("input", handleTestToneFrequencyInput);
testToneCentsRange.addEventListener("input", handleTestToneFrequencyInput);

testToneVolume.addEventListener("input", (event) => {
  if (testGainNode) {
    testGainNode.gain.setTargetAtTime(Number(event.target.value), audioContext.currentTime, 0.01);
  }
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

// Release whichever source is active when the tab is hidden, rather than
// leaving the microphone (or the test tone) running in the background.
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopActiveSource();
  }
});

buildStrobeRings();
buildNeedleScale();
buildLedSegments();
setVisualMode();
updateReferencePitch(state.a4);
updateTestToneDisplay(getTestToneFrequency());
resetVisuals();
