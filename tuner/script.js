const SVG_NS = "http://www.w3.org/2000/svg";
const T = TunerCommon;

const tunerSection = document.querySelector(".tuner");
const noteNameEl = document.getElementById("noteName");
const centsValueEl = document.getElementById("centsValue");
const freqValueEl = document.getElementById("freqValue");
const noteMetaEl = document.getElementById("noteMeta");
const noteReadoutEl = document.getElementById("noteReadout");

const strobeVisual = document.getElementById("strobeVisual");
const needleVisual = document.getElementById("needleVisual");
const meterVisual = document.getElementById("meterVisual");
const needleSwingEl = document.getElementById("needleSwing");
const ledSegmentsContainer = document.getElementById("ledSegments");
const ledIndicatorEl = document.getElementById("ledIndicator");

const toggleMicBtn = document.getElementById("toggleMicBtn");
const powerSwitchStateEl = document.getElementById("powerSwitchState");
const tuningStatementEl = document.getElementById("tuningStatement");
const freqTableTuningNoteEl = document.getElementById("freqTableTuningNote");
const micStatus = document.getElementById("micStatus");
const decreasePitchBtn = document.getElementById("decreasePitchBtn");
const increasePitchBtn = document.getElementById("increasePitchBtn");
const pitchInput = document.getElementById("pitchInput");
const pitchRange = document.getElementById("pitchRange");
const visualModeInputs = document.querySelectorAll('input[name="tunerVisualMode"]');
const pitchPresetInputs = document.querySelectorAll('input[name="pitchPreset"]');
const temperamentSelects = document.querySelectorAll(".temperament-select");
const temperamentKeyRows = document.querySelectorAll(".temperament-key-row");
const temperamentKeySelects = document.querySelectorAll(".temperament-key-select");

const testToneRange = document.getElementById("testToneRange");
const testToneCentsRange = document.getElementById("testToneCentsRange");
const testToneVolume = document.getElementById("testToneVolume");
const toggleTestToneBtn = document.getElementById("toggleTestToneBtn");
const decreaseTestToneBtn = document.getElementById("decreaseTestToneBtn");
const increaseTestToneBtn = document.getElementById("increaseTestToneBtn");
const decreaseCentsBtn = document.getElementById("decreaseCentsBtn");
const increaseCentsBtn = document.getElementById("increaseCentsBtn");
const testToneNoteEl = document.getElementById("testToneNote");
const testToneFreqLabelEl = document.getElementById("testToneFreqLabel");
const testToneCentsLabelEl = document.getElementById("testToneCentsLabel");
const varianceFillEl = document.getElementById("varianceFill");
const variancePrevNoteEl = document.getElementById("variancePrevNote");
const varianceCurrentNoteEl = document.getElementById("varianceCurrentNote");
const varianceNextNoteEl = document.getElementById("varianceNextNote");

const micGainRange = document.getElementById("micGainRange");
const micGainValueLabelEl = document.getElementById("micGainValueLabel");
const levelMeterFillEl = document.getElementById("levelMeterFill");
const levelValueLabelEl = document.getElementById("levelValueLabel");
const spectrumCanvas = document.getElementById("spectrumCanvas");
const spectrumStyleCheckbox = document.getElementById("spectrumStyleCheckbox");
const spectrumStyleToggleEl = document.getElementById("spectrumStyleToggle");
const spectrumLowLabelEl = document.getElementById("spectrumLowLabel");
const spectrumRefLabelEl = document.getElementById("spectrumRefLabel");
const spectrumHighLabelEl = document.getElementById("spectrumHighLabel");
const freqTableHeadRow = document.getElementById("freqTableHeadRow");
const freqTableBody = document.getElementById("freqTableBody");

const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
let audioContext = null;
let analyserNode = null;
let mediaStream = null;
let mediaStreamSource = null;
let micGainNode = null;
let timeDomainBuffer = null;
let freqDataBuffer = null;
let rafId;
let lastFrameAt = 0;
let lastPitchCheckAt = 0;

const NOTE_NAMES = T.NOTE_NAMES;
const MIN_FREQ_HZ = 40;
const MAX_FREQ_HZ = 1600;
const FFT_SIZE = 4096;
const MIN_RMS = 0.012;
const MIN_CLARITY = 0.9;
const PITCH_CHECK_INTERVAL_MS = 45;
const SILENCE_TIMEOUT_MS = 500;
// How long the running tuner must hear nothing before the "no signal"
// sign below the display appears — a short grace period so brief gaps
// between notes don't flash it.
const NO_SIGNAL_DELAY_MS = 3000;
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

// The test tone's frequency slider spans the full piano keyboard, A0 to C8.
const TEST_FREQ_MIN = 19;
const TEST_FREQ_MAX = 4434;
const FINE_TUNING_MAX_CENTS = 50;

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
  a4: T.DEFAULT_A4,
  activeSource: null, // null | "mic" | "test"
  hasSignal: false,
  smoothedCents: 0,
  needleAngle: 0,
  currentNote: null,
  lastFrequency: 0,
  lastConfidentAt: 0,
};

let ledDotElements = [];

const clamp = T.clamp;
const setMicStatus = T.setMicStatusFactory(micStatus);

// Wired up right away since every other controller below needs to read its
// current tuning standard/key — see temperament.pianoNoteFrequency.
const temperament = T.setupTemperament({
  selects: temperamentSelects,
  keyRows: temperamentKeyRows,
  keySelects: temperamentKeySelects,
  onChange: () => {
    buildFreqTable();
    updateTestToneDisplay(testTone.getFrequency());
    spectrum.updateLabels(getSpectrumRange(), state.a4);
    updateTuningStatement();
  },
});

const spectrum = T.createSpectrumAnalyser({
  canvas: spectrumCanvas,
  lowLabel: spectrumLowLabelEl,
  refLabel: spectrumRefLabelEl,
  highLabel: spectrumHighLabelEl,
  styleCheckbox: spectrumStyleCheckbox,
  styleToggleEl: spectrumStyleToggleEl,
});

const inputMonitor = T.createInputMonitor({
  gainRange: micGainRange,
  gainValueLabel: micGainValueLabelEl,
  levelFill: levelMeterFillEl,
  levelValueLabel: levelValueLabelEl,
  getGainNode: () => micGainNode,
  audioContextRef: () => audioContext,
});

const testTone = T.createTestTone({
  rangeInput: testToneRange,
  centsRangeInput: testToneCentsRange,
  volumeInput: testToneVolume,
  freqLabel: testToneFreqLabelEl,
  centsLabel: testToneCentsLabelEl,
  minFreq: TEST_FREQ_MIN,
  maxFreq: TEST_FREQ_MAX,
  maxFineTuningCents: FINE_TUNING_MAX_CENTS,
});

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
   PITCH DETECTION — time-domain autocorrelation, normalized per-lag as an
   NSDF (Normalized Square Difference Function, the same normalization the
   McLeod Pitch Method uses) rather than against one fixed, full-buffer
   energy figure. That fixed-denominator version is what this function
   used to do, and it systematically penalized low notes: the numerator at
   a lag L only sums (size - L) sample pairs, so as L grows for lower
   frequencies, that shrinking sum was being compared against the *same*
   full-length sumSquares computed once for the whole buffer — a perfectly
   periodic low note could land well under MIN_CLARITY for no reason but
   its own lag length (e.g. a clean ~110 Hz tone in a 4096-sample window
   tops out around clarity ~0.89, already below the 0.9 cutoff, before any
   real noise or inharmonicity — which is why guitar notes around A3 and
   below were being reported as "no signal" despite showing clearly on the
   Spectrum Analyser). Normalizing energy over the same shrinking window
   the numerator itself uses removes that bias, so clarity reflects actual
   periodicity at every frequency alike. Restricted to the plausible
   instrument frequency range so the O(bufferSize * lagRange) cost stays
   cheap enough to run several times a second in plain JS. A normalized
   correlation peak below MIN_CLARITY is treated as "no clear pitch"
   (background noise, breath, pick noise, silence).
   ============================================================ */
function detectPitch(buffer, sampleRate) {
  const size = buffer.length;
  let totalEnergy = 0;

  for (let i = 0; i < size; i += 1) {
    totalEnergy += buffer[i] * buffer[i];
  }

  const rms = Math.sqrt(totalEnergy / size);

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
  let bestValue = -1;
  // A clean tone is exactly as periodic at 2x, 3x… its true period as at
  // the period itself (any multiple of a period is also a period), so the
  // NSDF ties or nearly ties there too — floating-point noise alone can
  // then make one of those octave-below lags edge out the true peak as the
  // single global max, misreading (say) a clean A2 as A1. The first local
  // peak that already clears MIN_CLARITY is taken immediately instead: it
  // is necessarily the shortest — i.e. highest-frequency — lag confident
  // enough to count, which is always the true period, never a subharmonic
  // multiple of it (those only appear later, at longer lags).
  let peakIndex = -1;

  for (let lag = minLag; lag <= maxLag; lag += 1) {
    const limit = size - lag;
    let sum = 0;
    let energy = 0;

    for (let i = 0; i < limit; i += 1) {
      sum += buffer[i] * buffer[i + lag];
      energy += buffer[i] * buffer[i] + buffer[i + lag] * buffer[i + lag];
    }

    // 2r(τ) / m'(τ): 1.0 for a perfectly periodic signal at any lag,
    // instead of decaying toward 0 as the lag grows.
    const normalized = energy > 0 ? (2 * sum) / energy : 0;
    const index = lag - minLag;
    correlations[index] = normalized;

    if (normalized > bestValue) {
      bestValue = normalized;
      bestIndex = index;
    }

    if (
      peakIndex === -1 &&
      index >= 2 &&
      correlations[index - 1] >= MIN_CLARITY &&
      correlations[index - 1] >= correlations[index - 2] &&
      correlations[index - 1] >= normalized
    ) {
      peakIndex = index - 1;
    }
  }

  if (bestIndex < 0) {
    return null;
  }

  if (peakIndex !== -1) {
    bestIndex = peakIndex;
    bestValue = correlations[peakIndex];
  }

  const clarity = bestValue;

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

function pianoNoteFrequency(midi, a4) {
  return temperament.pianoNoteFrequency(midi, a4);
}

function frequencyToNote(frequency, a4) {
  return T.frequencyToNote(frequency, a4, pianoNoteFrequency);
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
  // With no source active, rest the meter at its tuned center (0 cents)
  // rather than switching the indicator off — matches the strobe/needle
  // idling in their in-tune position at the reference A4.
  const hasSignal = state.hasSignal;
  const clamped = hasSignal ? clamp(state.smoothedCents, -LED_MAX_CENTS, LED_MAX_CENTS) : 0;

  ledDotElements.forEach(({ cents, el }) => {
    let lit;

    if (cents === 0) {
      lit = Math.abs(clamped) <= IN_TUNE_THRESHOLD_CENTS;
    } else if (hasSignal && cents > 0) {
      lit = clamped >= cents;
    } else if (hasSignal && cents < 0) {
      lit = clamped <= cents;
    } else {
      lit = false;
    }

    el.classList.toggle("lit", lit);
  });

  // The track runs bottom-to-top (flat at the bottom, sharp at the top), so
  // the indicator's vertical position is driven by `bottom`, not `left`.
  const percent = 50 + (clamped / LED_MAX_CENTS) * 50;
  ledIndicatorEl.style.bottom = `${percent}%`;
  ledIndicatorEl.classList.add("visible");
}

/* ============================================================
   INPUT MONITOR / SPECTRUM — the spectrum's own axis tracks the current
   reference pitch and tuning standard (A0 to C8 at that A4), rather than
   the test tone's fixed 19-4434 Hz slider range, so it always matches the
   Frequency Table's columns and the Input Monitor labels below it.
   ============================================================ */
function getSpectrumRange() {
  return {
    min: pianoNoteFrequency(T.PIANO_MIN_MIDI, state.a4),
    max: pianoNoteFrequency(T.PIANO_MAX_MIDI, state.a4),
  };
}

/* ============================================================
   FREQUENCY TABLE — the shared octave-by-note table (see
   T.buildOctaveFrequencyTable in shared/tuner-common.js). Unlike
   /strobetuner/ and /multistrobe/ (which track every note/octave at once
   via Goertzel rings), this page only ever detects one fundamental at a
   time, so at most a single cell — the one matching state.currentNote's
   exact MIDI note — lights up with a live cents reading.
   ============================================================ */
const freqTableCellsByMidi = new Map();

function buildFreqTable() {
  T.buildOctaveFrequencyTable({
    headRow: freqTableHeadRow,
    body: freqTableBody,
    pianoNoteFrequency: (midi) => pianoNoteFrequency(midi, state.a4),
    cellsByMidi: freqTableCellsByMidi,
  });
}

function resetFreqTableLiveCents() {
  T.resetOctaveFrequencyTable(freqTableCellsByMidi);
}

function updateFreqTableLiveCents() {
  resetFreqTableLiveCents();

  if (!state.hasSignal || !state.currentNote) {
    return;
  }

  const entry = freqTableCellsByMidi.get(state.currentNote.midi);

  if (!entry) {
    return;
  }

  const rounded = Math.round(state.smoothedCents);
  const inTune = Math.abs(state.smoothedCents) <= IN_TUNE_THRESHOLD_CENTS;
  const sign = rounded > 0 ? "+" : "";
  entry.centsEl.textContent = `${sign}${rounded}¢`;
  entry.centsEl.hidden = false;
  entry.cell.classList.add("is-active", "is-fundamental");
  entry.cell.classList.toggle("is-in-tune", inTune);
}

const NO_SIGNAL_MESSAGE = "no signal, check the microphone in the input monitor below";

function updateReadout() {
  const inTune = !state.hasSignal || Math.abs(state.smoothedCents) <= IN_TUNE_THRESHOLD_CENTS;
  tunerSection.classList.toggle("in-tune", inTune);
  tunerSection.style.setProperty("--tune-mix", String(state.hasSignal ? getTuneMixPercent(state.smoothedCents) : 0));

  // The readout only exists while a source is running — stopped, it
  // collapses entirely so the live area stays compact.
  noteReadoutEl.hidden = state.activeSource === null;

  if (!state.hasSignal || !state.currentNote) {
    // Running but nothing heard yet: a bare dash for the first few
    // seconds, then the "no signal" message takes its place in the same
    // spot (mic only — the test tone always has a signal). The grace
    // period runs from state.lastConfidentAt, seeded when the mic starts.
    const silentForMs = performance.now() - state.lastConfidentAt;
    const showNoSignal = state.activeSource === "mic" && silentForMs > NO_SIGNAL_DELAY_MS;
    noteNameEl.textContent = showNoSignal ? NO_SIGNAL_MESSAGE : "–";
    noteNameEl.classList.toggle("is-no-signal", showNoSignal);
    noteMetaEl.classList.add("is-empty");
    return;
  }

  noteNameEl.classList.remove("is-no-signal");
  noteMetaEl.classList.remove("is-empty");
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
  resetFreqTableLiveCents();
  needleSwingEl.setAttribute("transform", `rotate(0 ${NEEDLE_PIVOT.x} ${NEEDLE_PIVOT.y})`);
  renderMeter();
  inputMonitor.reset();
  spectrum.clear();

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
    freqDataBuffer = new Uint8Array(analyserNode.frequencyBinCount);
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

    // Both sources feed the same analyser now (mic through micGainNode,
    // test tone through its own gain node in parallel with the speakers —
    // see T.createTestTone), so the Input Monitor's level meter and
    // Spectrum Analyser read it the same way regardless of which one is
    // active.
    analyserNode.getFloatTimeDomainData(timeDomainBuffer);
    inputMonitor.updateLevelMeter(inputMonitor.computeRms(timeDomainBuffer));
    analyserNode.getByteFrequencyData(freqDataBuffer);
    spectrum.update(freqDataBuffer, audioContext.sampleRate, FFT_SIZE, getSpectrumRange());

    if (state.activeSource === "test") {
      // The test tone's frequency is already known exactly, so the readout
      // is computed directly from it rather than detected — this keeps it
      // immune to gain/volume changes, which briefly disturb the analysed
      // waveform (and therefore the autocorrelation result) if routed
      // through the same detector used for the microphone.
      const testFrequency = testTone.getFrequency();
      const note = frequencyToNote(testFrequency, state.a4);
      state.smoothedCents += (note.cents - state.smoothedCents) * CENTS_SMOOTHING;
      state.hasSignal = true;
      state.lastConfidentAt = timestamp;
      state.currentNote = note;
      state.lastFrequency = testFrequency;
    } else {
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
    updateFreqTableLiveCents();
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
    setMicStatus(T.MIC_MESSAGES.notSupported, true);
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 },
    });
  } catch (error) {
    if (error && error.name === "NotAllowedError") {
      setMicStatus(T.MIC_MESSAGES.denied, true);
    } else if (error && error.name === "NotFoundError") {
      setMicStatus(T.MIC_MESSAGES.notFound, true);
    } else {
      setMicStatus(T.MIC_MESSAGES.genericError, true);
    }
    return;
  }

  const ctx = ensureAudioContext();

  if (!ctx) {
    setMicStatus(T.MIC_MESSAGES.webAudioNotSupported, true);
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
  // Seed the silence clock so the "no signal" sign's grace period starts
  // counting from when the tuner was switched on, not from page load.
  state.lastConfidentAt = performance.now();
  toggleMicBtn.setAttribute("aria-pressed", "true");
  powerSwitchStateEl.textContent = "ON";
  setMicStatus(T.MIC_MESSAGES.listening);
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

  toggleMicBtn.setAttribute("aria-pressed", "false");
  powerSwitchStateEl.textContent = "OFF";
  setMicStatus(T.MIC_MESSAGES.idle);
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
   TEST TONE — an oscillator routed to the speakers so it's audible (see
   T.createTestTone, which owns the oscillator/gain node lifecycle and the
   frequency/cents/volume slider math). Its pitch readout here is still
   computed directly from the known set frequency (see mainLoop) rather
   than detected, so it can't be perturbed by gain/volume changes — but
   it's also tapped into the analyser (in parallel with the speakers) so
   the Input Monitor's level meter and Spectrum Analyser have something to
   show while it plays, same as the mic.
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
    setMicStatus(T.MIC_MESSAGES.webAudioNotSupported, true);
    return;
  }

  ensureAnalyser();
  testTone.start(ctx, analyserNode);

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
  testTone.stop();

  toggleTestToneBtn.textContent = "Test Tone";
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

function updateTestToneDisplay(frequency) {
  testTone.updateFreqLabel(frequency);
  const note = frequencyToNote(frequency, state.a4);
  const roundedCents = Math.round(note.cents);
  const sign = roundedCents > 0 ? "+" : "";
  testToneNoteEl.textContent = `${note.name}${note.octave} ${sign}${roundedCents}¢`;
  T.updateTestToneVariance(
    note,
    { fillEl: varianceFillEl, prevNoteEl: variancePrevNoteEl, currentNoteEl: varianceCurrentNoteEl, nextNoteEl: varianceNextNoteEl },
    { inTuneThresholdCents: IN_TUNE_THRESHOLD_CENTS, getTuneMixPercent },
  );
}

function applyTestToneFrequency() {
  updateTestToneDisplay(testTone.applyFrequency(audioContext));
}

// Changing the base frequency resets Fine Tuning back to 0 — otherwise the
// two controls would fight over what "0" even means as the base moves.
function resetFineTuningCents() {
  updateTestToneDisplay(testTone.resetFineTuning(audioContext));
}

function nudgeTestToneFrequency(deltaHz) {
  updateTestToneDisplay(testTone.nudgeFrequency(deltaHz, audioContext));
}

function nudgeFineTuningCents(deltaCents) {
  updateTestToneDisplay(testTone.nudgeFineTuning(deltaCents, audioContext));
}

/* ============================================================
   CONTROLS
   ============================================================ */
function setVisualMode() {
  const mode = document.querySelector('input[name="tunerVisualMode"]:checked')?.value || "needle";
  tunerSection.dataset.visualMode = mode;
  strobeVisual.hidden = mode !== "strobe";
  needleVisual.hidden = mode !== "needle";
  meterVisual.hidden = mode !== "meter";
}

// A plain-language readout of the current tuning configuration — e.g.
// "Tuning for Vallotti in G · 440 Hz" — kept in sync with every control
// that can change it (Standard, Key, and the A4 reference pitch).
function updateTuningStatement() {
  const selected = temperament.getTemperament();
  const keyPart = selected.needsKey ? ` in ${NOTE_NAMES[temperament.state.temperamentKey]}` : "";
  tuningStatementEl.textContent = `Tuning for ${selected.name}${keyPart} · ${state.a4} Hz`;
  freqTableTuningNoteEl.textContent = `Showing frequencies for ${selected.name}${keyPart} · ${state.a4} Hz — set above under Tuning Standard and Reference Pitch.`;
}

const referencePitch = T.setupReferencePitch({
  pitchInput,
  pitchRange,
  decreaseBtn: decreasePitchBtn,
  increaseBtn: increasePitchBtn,
  presetInputs: pitchPresetInputs,
  onChange: (a4) => {
    state.a4 = a4;
    buildFreqTable();
    updateTestToneDisplay(testTone.getFrequency());
    spectrum.updateLabels(getSpectrumRange(), state.a4);
    updateTuningStatement();
  },
});

visualModeInputs.forEach((input) => {
  input.addEventListener("change", setVisualMode);
});

toggleMicBtn.addEventListener("click", toggleMic);
toggleTestToneBtn.addEventListener("click", toggleTestTone);
decreaseTestToneBtn.addEventListener("click", () => nudgeTestToneFrequency(-1));
increaseTestToneBtn.addEventListener("click", () => nudgeTestToneFrequency(1));
decreaseCentsBtn.addEventListener("click", () => nudgeFineTuningCents(-1));
increaseCentsBtn.addEventListener("click", () => nudgeFineTuningCents(1));

// Dragging the base frequency resets Fine Tuning to 0 (see resetFineTuningCents).
testToneRange.addEventListener("input", resetFineTuningCents);

// A double-click on the Frequency bar snaps the test tone back to the
// current reference pitch (state.a4), not a fixed number, so it always
// matches whatever standard is selected in Reference Pitch.
testToneRange.addEventListener("dblclick", () => {
  testToneRange.value = String(state.a4);
  resetFineTuningCents();
});

testToneCentsRange.addEventListener("input", () => {
  testTone.updateCentsLabel();
  applyTestToneFrequency();
});

// A double-click anywhere on the Fine Tuning bar snaps it back to 0.
testToneCentsRange.addEventListener("dblclick", resetFineTuningCents);

// Re-measuring the spectrum canvas on expand matters because it reports
// zero size while display:none, so sizeCanvas's guard skips it until the
// frame is visible again.
T.wireCollapsibles((panel) => {
  if (panel.contains(spectrumCanvas)) {
    spectrum.sizeCanvas();
  }
});

T.wireTransportShortcuts({
  onToggle: toggleMic,
  onA4Delta: (delta) => referencePitch.setA4(state.a4 + delta),
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
referencePitch.setA4(state.a4);
testTone.updateCentsLabel();
updateTestToneDisplay(testTone.getFrequency());
spectrum.setStyle("vintage");
spectrum.sizeCanvas();
resetVisuals();
