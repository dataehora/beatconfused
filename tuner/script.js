const SVG_NS = "http://www.w3.org/2000/svg";

const tunerSection = document.querySelector(".tuner");
const noteNameEl = document.getElementById("noteName");
const centsValueEl = document.getElementById("centsValue");
const freqValueEl = document.getElementById("freqValue");
const noteMetaEl = document.getElementById("noteMeta");
const noSignalHintEl = document.getElementById("noSignalHint");

const strobeVisual = document.getElementById("strobeVisual");
const needleVisual = document.getElementById("needleVisual");
const meterVisual = document.getElementById("meterVisual");
const needleSwingEl = document.getElementById("needleSwing");
const ledSegmentsContainer = document.getElementById("ledSegments");
const ledIndicatorEl = document.getElementById("ledIndicator");

const toggleMicBtn = document.getElementById("toggleMicBtn");
const tuningStatementEl = document.getElementById("tuningStatement");
const micStatus = document.getElementById("micStatus");
const decreasePitchBtn = document.getElementById("decreasePitchBtn");
const increasePitchBtn = document.getElementById("increasePitchBtn");
const pitchInput = document.getElementById("pitchInput");
const pitchRange = document.getElementById("pitchRange");
const visualModeInputs = document.querySelectorAll('input[name="tunerVisualMode"]');
const pitchPresetInputs = document.querySelectorAll('input[name="pitchPreset"]');
// Two identical Standard/Key control pairs live on the page at once (the
// Tuning Standard panel and the one above the Frequency Table) — queried
// by class rather than id so updateTemperament/updateTemperamentKey can
// keep every instance of both in sync with a single write to state.
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
const spectrumCtx = spectrumCanvas.getContext("2d");
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
let testOscillator = null;
let testGainNode = null;
let timeDomainBuffer = null;
let freqDataBuffer = null;
let rafId;
let lastFrameAt = 0;
let lastPitchCheckAt = 0;

const NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];

const MIN_A4 = 392;
const MAX_A4 = 466;
const DEFAULT_A4 = 440;
const MIN_FREQ_HZ = 40;
const MAX_FREQ_HZ = 1600;
const FFT_SIZE = 4096;
const MIN_RMS = 0.012;
const MIN_CLARITY = 0.9;
// The floor of the Input Monitor's dB scale — anything quieter reads as
// silence rather than an ever-more-negative number.
const LEVEL_FLOOR_DB = -60;
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

// The test tone's frequency slider spans the full piano keyboard, A0 to C8.
const TEST_FREQ_MIN = 19;
const TEST_FREQ_MAX = 4434;
const FINE_TUNING_MAX_CENTS = 50;

// A standard 88-key grand piano: A0 (MIDI 21) to C8 (MIDI 108).
const PIANO_MIN_MIDI = 21;
const PIANO_MAX_MIDI = 108;

// The six tuning standards offered under Reference Pitch, in the same
// ascending order — reused here to build the Frequency Table's columns.
const REFERENCE_PITCH_PRESETS = [
  { value: 392, primary: "French Baroque", secondary: "\"Tone de Chambre\"" },
  { value: 415, primary: "Baroque" },
  { value: 432, primary: "Verdi", secondary: "\"Scientific\"" },
  { value: 440, primary: "Standard" },
  { value: 444, primary: "Modern", secondary: "\"Symphony\"" },
  { value: 466, primary: "Italian", secondary: "Renaissance" },
];

/* ============================================================
   TUNING STANDARDS (temperaments) — Equal Temperament plus four
   historical/alternate systems, each built from first principles
   rather than a hand-typed cents table:

   - Vallotti, Young II and 1/4-comma meantone are all "fifths chain"
     temperaments: every note is reached from the tonic by stacking a
     run of (possibly tempered) fifths. FIFTHS_POSITION_FOR_SEMITONE
     encodes that chain's shape once; each temperament only supplies
     how many cents its fifths deviate from a pure 3:2.
   - Just Intonation (Major) instead fixes each degree directly to a
     5-limit ratio (Wikipedia's "asymmetric" 12-tone scale, chosen for
     using the smallest integers in each ratio).

   Every temperament is expressed as a table of 12 cents offsets from
   equal temperament, indexed by semitone *above the chosen tonic* —
   see getTemperamentOffsetCents, which rotates that table to whatever
   key the Reference Pitch panel's Key selector is set to.
   ============================================================ */
const PURE_FIFTH_CENTS = 1200 * Math.log2(3 / 2); // ~701.955
const PYTHAGOREAN_COMMA_CENTS = 1200 * Math.log2(531441 / 524288); // ~23.460
const SYNTONIC_COMMA_CENTS = 1200 * Math.log2(81 / 80); // ~21.506

// Position on the circle of fifths (tonic = 0) for each semitone above the
// tonic. Derived from: 7 * position ≡ semitone (mod 12), position in -5..6.
const FIFTHS_POSITION_FOR_SEMITONE = [0, -5, 2, -3, 4, -1, 6, 1, -4, 3, -2, 5];

// Walks the chain of 11 fifths spanning position -5 (a major third below
// the tonic's relative minor) to position +6 (the tritone), given how many
// cents the fifth connecting `lowerPosition` to `lowerPosition + 1`
// deviates from a pure 3:2 (0 = pure, negative = narrowed) — then reduces
// each position against where a 700-cent equal-tempered fifth would have
// put it, yielding cents-from-equal-temperament per semitone above tonic.
function buildFifthsChainOffsets(fifthDeviationCents) {
  const cumulative = { 0: 0 };

  for (let position = 1; position <= 6; position += 1) {
    cumulative[position] = cumulative[position - 1] + PURE_FIFTH_CENTS + fifthDeviationCents(position - 1);
  }

  for (let position = -1; position >= -5; position -= 1) {
    cumulative[position] = cumulative[position + 1] - (PURE_FIFTH_CENTS + fifthDeviationCents(position));
  }

  return FIFTHS_POSITION_FOR_SEMITONE.map((position) => cumulative[position] - position * 700);
}

function equalTemperamentOffsets() {
  return new Array(12).fill(0);
}

// A "well" temperament: a fixed set of fifths (identified by the lower
// position of each tempered edge) narrowed by a shared fraction of the
// Pythagorean comma; every other fifth in the chain stays pure.
function wellTemperamentOffsets(temperedLowerPositions, temperCents) {
  const tempered = new Set(temperedLowerPositions);
  return buildFifthsChainOffsets((lowerPosition) => (tempered.has(lowerPosition) ? -temperCents : 0));
}

// A "regular" temperament: every fifth in the chain is narrowed by the
// same fraction of the syntonic comma (1/4-comma meantone favors pure
// major thirds at the cost of a "wolf" fifth far from the tonic).
function meantoneOffsets(commaFraction) {
  const temperCents = SYNTONIC_COMMA_CENTS * commaFraction;
  return buildFifthsChainOffsets(() => -temperCents);
}

// 5-limit just intonation, asymmetric 12-tone chromatic scale (the
// smallest-integer ratio for each degree) — not derived from a fifths
// chain, so each degree is given directly as cents from the tonic.
const JUST_MAJOR_RATIO_CENTS = [
  0, // C    1/1
  1200 * Math.log2(16 / 15), // C♯/D♭
  1200 * Math.log2(9 / 8), // D
  1200 * Math.log2(6 / 5), // D♯/E♭
  1200 * Math.log2(5 / 4), // E
  1200 * Math.log2(4 / 3), // F
  1200 * Math.log2(45 / 32), // F♯/G♭
  1200 * Math.log2(3 / 2), // G
  1200 * Math.log2(8 / 5), // G♯/A♭
  1200 * Math.log2(5 / 3), // A
  1200 * Math.log2(9 / 5), // A♯/B♭
  1200 * Math.log2(15 / 8), // B
];

function justIntonationMajorOffsets() {
  return JUST_MAJOR_RATIO_CENTS.map((cents, semitone) => cents - semitone * 100);
}

// The five tuning standards offered under Reference Pitch. Only the first
// (Equal Temperament) needs no tonic — the rest are anchored to whichever
// key the auxiliary Key selector is set to, so that selector only shows up
// once one of these is chosen (see updateTemperament).
const TEMPERAMENTS = [
  { id: "equal", name: "Equal Temperament", needsKey: false, getOffsets: equalTemperamentOffsets },
  { id: "vallotti", name: "Vallotti", needsKey: true, getOffsets: () => wellTemperamentOffsets([-1, 0, 1, 2, 3, 4], PYTHAGOREAN_COMMA_CENTS / 6) },
  { id: "young2", name: "Young II", needsKey: true, getOffsets: () => wellTemperamentOffsets([0, 1, 2, 3, 4, 5], PYTHAGOREAN_COMMA_CENTS / 6) },
  { id: "meantone4", name: "1/4-Comma Meantone", needsKey: true, getOffsets: () => meantoneOffsets(0.25) },
  { id: "justMajor", name: "Just Intonation (Major)", needsKey: true, getOffsets: justIntonationMajorOffsets },
];

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
  spectrumStyle: "vintage", // "vintage" | "modern"
  temperamentId: TEMPERAMENTS[0].id, // "equal"
  temperamentKey: 0, // tonic as a pitch class (0 = C), only used when the selected temperament needsKey
  temperamentOffsets: TEMPERAMENTS[0].getOffsets(), // 12 cents-from-equal-temperament values, indexed by semitone above the tonic
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

// Rotates the active temperament's offset table (defined relative to its
// own tonic) to whatever pitch class the Key selector is set to, so e.g.
// selecting "Vallotti, key D" shifts Vallotti's usual C-centered pattern
// so D becomes the sweetest key instead.
function getTemperamentOffsetCents(midi) {
  const pitchClass = ((midi % 12) + 12) % 12;
  const semitoneAboveTonic = ((pitchClass - state.temperamentKey) % 12 + 12) % 12;
  return state.temperamentOffsets[semitoneAboveTonic];
}

function frequencyToNote(frequency, a4) {
  const equalMidi = 69 + 12 * Math.log2(frequency / a4);
  const rounded = Math.round(equalMidi);
  const targetFrequency = pianoNoteFrequency(rounded, a4);
  const cents = 1200 * Math.log2(frequency / targetFrequency);
  const name = NOTE_NAMES[((rounded % 12) + 12) % 12];
  const octave = Math.floor(rounded / 12) - 1;
  return { name, octave, cents, midi: rounded };
}

function noteNameForMidi(midi) {
  const name = NOTE_NAMES[((midi % 12) + 12) % 12];
  const octave = Math.floor(midi / 12) - 1;
  return `${name}${octave}`;
}

// The selected tuning standard nudges every note away from equal
// temperament by a few cents (see getTemperamentOffsetCents) — Equal
// Temperament itself has an all-zero offset table, so this collapses back
// to the plain a4 * 2^((midi-69)/12) formula in that case.
function pianoNoteFrequency(midi, a4) {
  const equalFrequency = a4 * Math.pow(2, (midi - 69) / 12);
  return equalFrequency * Math.pow(2, getTemperamentOffsetCents(midi) / 1200);
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

// Builds the table's 6 columns once at load: one per tuning standard from
// Reference Pitch. Unlike the body, these headers don't depend on which
// temperament is selected, so they never need rebuilding.
function buildFrequencyTableHead() {
  REFERENCE_PITCH_PRESETS.forEach((preset) => {
    const th = document.createElement("th");
    const freqEl = document.createElement("span");
    freqEl.className = "freq-table-col-freq";
    freqEl.textContent = `${preset.value} Hz`;
    th.appendChild(freqEl);

    if (preset.primary) {
      const primaryEl = document.createElement("span");
      primaryEl.className = "freq-table-col-name-primary";
      primaryEl.textContent = preset.primary;
      th.appendChild(primaryEl);
    }

    if (preset.secondary) {
      const secondaryEl = document.createElement("span");
      secondaryEl.className = "freq-table-col-name-secondary";
      secondaryEl.textContent = preset.secondary;
      th.appendChild(secondaryEl);
    }

    freqTableHeadRow.appendChild(th);
  });
}

// Builds the table's 88 rows (A0-C8), each cell that key's frequency under
// one of the Reference Pitch standards — under the currently selected
// tuning standard (see pianoNoteFrequency), so this is rebuilt whenever
// the Tuning Standard or Key selector changes, unlike the head above.
function buildFrequencyTableBody() {
  freqTableBody.innerHTML = "";

  for (let midi = PIANO_MIN_MIDI; midi <= PIANO_MAX_MIDI; midi += 1) {
    const row = document.createElement("tr");
    const noteCell = document.createElement("td");
    noteCell.textContent = noteNameForMidi(midi);
    row.appendChild(noteCell);

    REFERENCE_PITCH_PRESETS.forEach((preset) => {
      const cell = document.createElement("td");
      cell.textContent = pianoNoteFrequency(midi, preset.value).toFixed(2);
      row.appendChild(cell);
    });

    freqTableBody.appendChild(row);
  }
}

function buildFrequencyTable() {
  buildFrequencyTableHead();
  buildFrequencyTableBody();
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
   INPUT MONITOR — a separate readout from the tuning display: how loud
   the (post-gain-boost) microphone signal is, and where its energy sits
   across the spectrum. Purely diagnostic, so it only reflects the mic
   path — the test tone bypasses the analyser entirely (see startTestTone)
   and has nothing for this panel to show.
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

function sizeSpectrumCanvas() {
  const rect = spectrumCanvas.getBoundingClientRect();

  if (rect.width === 0 || rect.height === 0) {
    return;
  }

  const dpr = window.devicePixelRatio || 1;
  spectrumCanvas.width = Math.round(rect.width * dpr);
  spectrumCanvas.height = Math.round(rect.height * dpr);
}

function clearSpectrum() {
  spectrumCtx.clearRect(0, 0, spectrumCanvas.width, spectrumCanvas.height);
}

// The spectrum's own axis tracks the current reference pitch — A0 to C8
// at that A4 — rather than the test tone's fixed 19-4434 Hz slider range,
// so it always matches the Frequency Table's columns and the Input
// Monitor labels below it.
function getSpectrumRange() {
  return {
    min: pianoNoteFrequency(PIANO_MIN_MIDI, state.a4),
    max: pianoNoteFrequency(PIANO_MAX_MIDI, state.a4),
  };
}

function updateSpectrumLabels() {
  // The keys themselves (A0 lowest, A4 reference, C8 highest) never
  // change — only their Hz value does, as the reference pitch moves.
  const range = getSpectrumRange();
  spectrumLowLabelEl.textContent = `A0 · ${range.min.toFixed(1)} Hz`;
  spectrumRefLabelEl.textContent = `A4 · ${state.a4.toFixed(1)} Hz`;
  spectrumHighLabelEl.textContent = `C8 · ${range.max.toFixed(1)} Hz`;
}

// ---- Vintage: a classic segmented LED equalizer — blocky steps rather
// than a smooth bar, in the traditional green/yellow/red ladder of an old
// hardware VU meter or graphic EQ.
function drawVintageSpectrum(freqData, width, height, barCount, barWidth, logMin, logMax, hzPerBin) {
  const segmentHeight = 6;
  const segmentGap = 2;
  const segmentUnit = segmentHeight + segmentGap;
  const totalSegments = Math.max(1, Math.floor(height / segmentUnit));

  for (let i = 0; i < barCount; i += 1) {
    const t = barCount > 1 ? i / (barCount - 1) : 0;
    const freq = Math.pow(2, logMin + t * (logMax - logMin));
    const binIndex = Math.min(freqData.length - 1, Math.round(freq / hzPerBin));
    const magnitude = freqData[binIndex] / 255;
    const litSegments = Math.round(magnitude * totalSegments);

    for (let s = 0; s < litSegments; s += 1) {
      const ratio = s / totalSegments;

      if (ratio > 0.9) {
        spectrumCtx.fillStyle = "#c0453a";
      } else if (ratio > 0.7) {
        spectrumCtx.fillStyle = "#d9b23c";
      } else {
        spectrumCtx.fillStyle = "#5f9153";
      }

      const y = height - (s + 1) * segmentUnit + segmentGap;
      spectrumCtx.fillRect(i * barWidth, y, Math.max(1, barWidth - 1), segmentHeight);
    }
  }
}

// ---- Modern: a single smoothed curve over a soft gradient area fill —
// closer to a DAW's analyzer (Ableton Live et al.) than the vintage ladder
// above. Quadratic curves through the midpoint between each pair of points
// (rather than a plain lineTo polyline) round the per-bin steps into one
// continuous line instead of a jagged staircase.
function drawModernSpectrum(freqData, width, height, barCount, barWidth, logMin, logMax, hzPerBin) {
  const points = [];

  for (let i = 0; i < barCount; i += 1) {
    const t = barCount > 1 ? i / (barCount - 1) : 0;
    const freq = Math.pow(2, logMin + t * (logMax - logMin));
    const binIndex = Math.min(freqData.length - 1, Math.round(freq / hzPerBin));
    const magnitude = freqData[binIndex] / 255;
    points.push({ x: i * barWidth + barWidth / 2, y: height - magnitude * height });
  }

  if (points.length < 2) {
    return;
  }

  const first = points[0];
  const last = points[points.length - 1];

  spectrumCtx.beginPath();
  spectrumCtx.moveTo(first.x, height);
  spectrumCtx.lineTo(first.x, first.y);

  for (let i = 1; i < points.length - 1; i += 1) {
    const midX = (points[i].x + points[i + 1].x) / 2;
    const midY = (points[i].y + points[i + 1].y) / 2;
    spectrumCtx.quadraticCurveTo(points[i].x, points[i].y, midX, midY);
  }

  spectrumCtx.lineTo(last.x, last.y);
  spectrumCtx.lineTo(last.x, height);
  spectrumCtx.closePath();

  const fillGradient = spectrumCtx.createLinearGradient(0, 0, 0, height);
  fillGradient.addColorStop(0, "rgba(168, 205, 240, 0.55)");
  fillGradient.addColorStop(1, "rgba(63, 110, 160, 0)");
  spectrumCtx.fillStyle = fillGradient;
  spectrumCtx.fill();

  spectrumCtx.beginPath();
  spectrumCtx.moveTo(first.x, first.y);

  for (let i = 1; i < points.length - 1; i += 1) {
    const midX = (points[i].x + points[i + 1].x) / 2;
    const midY = (points[i].y + points[i + 1].y) / 2;
    spectrumCtx.quadraticCurveTo(points[i].x, points[i].y, midX, midY);
  }

  spectrumCtx.lineTo(last.x, last.y);
  spectrumCtx.strokeStyle = "#a8cdf0";
  spectrumCtx.lineWidth = 1.5;
  spectrumCtx.lineJoin = "round";
  spectrumCtx.lineCap = "round";
  spectrumCtx.stroke();
}

// Log-scaled across the current A0-C8 range (see getSpectrumRange) so an
// octave always takes up the same width on screen, matching how the ear
// actually perceives the spectrum, rather than a linear Hz axis that
// would crush everything below a few hundred Hz into a handful of pixels.
function updateSpectrum(freqData, sampleRate) {
  const width = spectrumCanvas.width;
  const height = spectrumCanvas.height;
  clearSpectrum();

  const hzPerBin = sampleRate / FFT_SIZE;
  const range = getSpectrumRange();
  const logMin = Math.log2(range.min);
  const logMax = Math.log2(range.max);
  const barWidth = Math.max(1, width / 160);
  const barCount = Math.floor(width / barWidth);

  if (state.spectrumStyle === "modern") {
    drawModernSpectrum(freqData, width, height, barCount, barWidth, logMin, logMax, hzPerBin);
  } else {
    drawVintageSpectrum(freqData, width, height, barCount, barWidth, logMin, logMax, hzPerBin);
  }
}

function updateReadout() {
  // With no source active, the tuner rests at its reference A4 rather than
  // going blank — it reads as a device sitting in its tuned position (like
  // a physical strobe disc at standstill), not a device that's off.
  const inTune = !state.hasSignal || Math.abs(state.smoothedCents) <= IN_TUNE_THRESHOLD_CENTS;
  tunerSection.classList.toggle("in-tune", inTune);
  tunerSection.style.setProperty("--tune-mix", String(state.hasSignal ? getTuneMixPercent(state.smoothedCents) : 0));

  if (!state.hasSignal || !state.currentNote) {
    noteNameEl.textContent = "No Signal";
    noteNameEl.classList.add("is-no-signal");
    noteMetaEl.classList.add("is-empty");
    // Two distinct causes read differently: nothing has been started yet
    // (activeSource is still null) versus the mic is listening but hasn't
    // picked up a clear pitch — the fix is different in each case.
    noSignalHintEl.textContent = state.activeSource === "mic" ? "Check your microphone" : "Start the Tuner or the Test Tone";
    noSignalHintEl.hidden = false;
    return;
  }

  noteNameEl.classList.remove("is-no-signal");
  noteMetaEl.classList.remove("is-empty");
  noSignalHintEl.hidden = true;
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
  resetLevelMeter();
  clearSpectrum();

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
    // test tone through testGainNode in parallel with the speakers), so
    // the Input Monitor's level meter and Spectrum Analyser read it the
    // same way regardless of which one is active.
    analyserNode.getFloatTimeDomainData(timeDomainBuffer);
    updateLevelMeter(computeRms(timeDomainBuffer));
    analyserNode.getByteFrequencyData(freqDataBuffer);
    updateSpectrum(freqDataBuffer, audioContext.sampleRate);

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
   TEST TONE — an oscillator routed to the speakers so it's audible. Its
   pitch readout is still computed directly from the known set frequency
   (see mainLoop) rather than detected, so it can't be perturbed by gain/
   volume changes — but it's also tapped into the analyser (in parallel
   with the speakers) so the Input Monitor's level meter and Spectrum
   Analyser have something to show while it plays, same as the mic.
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

  ensureAnalyser();

  testOscillator = ctx.createOscillator();
  testOscillator.type = "sine";
  testOscillator.frequency.setValueAtTime(getTestToneFrequency(), ctx.currentTime);

  testGainNode = ctx.createGain();
  testGainNode.gain.setValueAtTime(Number(testToneVolume.value), ctx.currentTime);

  testOscillator.connect(testGainNode);
  testGainNode.connect(ctx.destination);
  testGainNode.connect(analyserNode);
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

// The Frequency slider picks a whole-Hz base; Fine Tuning bends it by up to
// ±50 cents (a quarter-tone each way) rather than adding raw Hz, so it reads
// the same musically at any point on the keyboard.
function getTestToneFrequency() {
  const base = Number(testToneRange.value);
  const cents = Number(testToneCentsRange.value);
  return base * Math.pow(2, cents / 1200);
}

function updateTestToneDisplay(frequency) {
  testToneFreqLabelEl.textContent = `${frequency.toFixed(2)} Hz`;
  const note = frequencyToNote(frequency, state.a4);
  const roundedCents = Math.round(note.cents);
  const sign = roundedCents > 0 ? "+" : "";
  testToneNoteEl.textContent = `${note.name}${note.octave} ${sign}${roundedCents}¢`;
  updateVarianceBar(note);
}

function updateFineTuningLabel() {
  const cents = Number(testToneCentsRange.value);
  const sign = cents > 0 ? "+" : "";
  testToneCentsLabelEl.textContent = `${sign}${cents}¢`;
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

function applyTestToneFrequency() {
  const combined = getTestToneFrequency();
  updateTestToneDisplay(combined);

  if (state.activeSource === "test" && testOscillator) {
    testOscillator.frequency.setTargetAtTime(combined, audioContext.currentTime, 0.01);
  }
}

// Changing the base frequency resets Fine Tuning back to 0 — otherwise the
// two controls would fight over what "0" even means as the base moves.
function resetFineTuningCents() {
  testToneCentsRange.value = "0";
  updateFineTuningLabel();
  applyTestToneFrequency();
}

function nudgeTestToneFrequency(deltaHz) {
  const next = clamp(Number(testToneRange.value) + deltaHz, TEST_FREQ_MIN, TEST_FREQ_MAX);
  testToneRange.value = String(next);
  resetFineTuningCents();
}

function nudgeFineTuningCents(deltaCents) {
  const next = clamp(Number(testToneCentsRange.value) + deltaCents, -FINE_TUNING_MAX_CENTS, FINE_TUNING_MAX_CENTS);
  testToneCentsRange.value = String(next);
  updateFineTuningLabel();
  applyTestToneFrequency();
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

function updateReferencePitch(value) {
  state.a4 = clamp(Math.round(Number(value) || DEFAULT_A4), MIN_A4, MAX_A4);
  pitchInput.value = String(state.a4);
  pitchRange.value = String(state.a4);

  pitchPresetInputs.forEach((input) => {
    input.checked = Number(input.value) === state.a4;
  });

  updateTestToneDisplay(getTestToneFrequency());
  updateSpectrumLabels();
  updateTuningStatement();
}

pitchInput.addEventListener("input", (event) => updateReferencePitch(event.target.value));
pitchRange.addEventListener("input", (event) => updateReferencePitch(event.target.value));
// A double-click anywhere on the reference pitch bar snaps it back to A440.
pitchRange.addEventListener("dblclick", () => updateReferencePitch(DEFAULT_A4));
decreasePitchBtn.addEventListener("click", () => updateReferencePitch(state.a4 - 1));
increasePitchBtn.addEventListener("click", () => updateReferencePitch(state.a4 + 1));

pitchPresetInputs.forEach((input) => {
  input.addEventListener("change", () => updateReferencePitch(input.value));
});

function getSelectedTemperament() {
  return TEMPERAMENTS.find((temperament) => temperament.id === state.temperamentId) || TEMPERAMENTS[0];
}

// A plain-language readout of the current tuning configuration — e.g.
// "Tuning for Vallotti in G · 440 Hz" — kept in sync with every control
// that can change it (Standard, Key, and the A4 reference pitch).
function updateTuningStatement() {
  const temperament = getSelectedTemperament();
  const keyPart = temperament.needsKey ? ` in ${NOTE_NAMES[state.temperamentKey]}` : "";
  tuningStatementEl.textContent = `Tuning for ${temperament.name}${keyPart} · ${state.a4} Hz`;
}

// Whichever Standard select fired the change, every instance (and both Key
// rows) gets synced to match — so the Tuning Standard panel and the pair
// above the Frequency Table always agree, regardless of which one the user
// touched.
function updateTemperament(id) {
  state.temperamentId = id;
  const temperament = getSelectedTemperament();
  state.temperamentOffsets = temperament.getOffsets();

  temperamentSelects.forEach((select) => {
    select.value = id;
  });

  temperamentKeyRows.forEach((row) => {
    row.hidden = !temperament.needsKey;
  });

  buildFrequencyTableBody();
  updateTestToneDisplay(getTestToneFrequency());
  updateSpectrumLabels();
  updateTuningStatement();
}

function updateTemperamentKey(pitchClass) {
  state.temperamentKey = clamp(Math.round(Number(pitchClass) || 0), 0, 11);

  temperamentKeySelects.forEach((select) => {
    select.value = String(state.temperamentKey);
  });

  buildFrequencyTableBody();
  updateTestToneDisplay(getTestToneFrequency());
  updateSpectrumLabels();
  updateTuningStatement();
}

temperamentSelects.forEach((select) => {
  select.addEventListener("change", (event) => updateTemperament(event.target.value));
});

temperamentKeySelects.forEach((select) => {
  select.addEventListener("change", (event) => updateTemperamentKey(event.target.value));
});

// Options are generated from TEMPERAMENTS / NOTE_NAMES rather than hand-
// written in the markup, so the dropdowns can never drift out of sync with
// the tables that actually compute the frequencies — and every instance of
// each select gets the same option list.
function populateTemperamentControls() {
  temperamentSelects.forEach((select) => {
    TEMPERAMENTS.forEach((temperament) => {
      const option = document.createElement("option");
      option.value = temperament.id;
      option.textContent = temperament.name;
      select.appendChild(option);
    });
  });

  temperamentKeySelects.forEach((select) => {
    NOTE_NAMES.forEach((name, pitchClass) => {
      const option = document.createElement("option");
      option.value = String(pitchClass);
      option.textContent = name;
      select.appendChild(option);
    });
  });
}

visualModeInputs.forEach((input) => {
  input.addEventListener("change", setVisualMode);
});

function setSpectrumStyle(styleName) {
  state.spectrumStyle = styleName;
  spectrumStyleCheckbox.checked = styleName === "modern";
  spectrumStyleToggleEl.querySelectorAll(".style-toggle-label").forEach((label) => {
    label.classList.toggle("is-active", label.dataset.style === styleName);
  });
}

spectrumStyleCheckbox.addEventListener("change", () => {
  setSpectrumStyle(spectrumStyleCheckbox.checked ? "modern" : "vintage");
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
  updateFineTuningLabel();
  applyTestToneFrequency();
});

// A double-click anywhere on the Fine Tuning bar snaps it back to 0.
testToneCentsRange.addEventListener("dblclick", resetFineTuningCents);

testToneVolume.addEventListener("input", (event) => {
  if (testGainNode) {
    testGainNode.gain.setTargetAtTime(Number(event.target.value), audioContext.currentTime, 0.01);
  }
});

micGainRange.addEventListener("input", (event) => {
  const gain = Number(event.target.value);
  micGainValueLabelEl.textContent = `${gain.toFixed(1)}×`;

  if (micGainNode) {
    micGainNode.gain.setTargetAtTime(gain, audioContext.currentTime, 0.01);
  }
});

window.addEventListener("resize", sizeSpectrumCanvas);

// Collapsible frames: each panel-header's toggle hides everything in its
// .control-block except the header (see the .is-collapsed CSS rule).
// Re-measuring the spectrum canvas on expand matters because it reports
// zero size while display:none, so sizeSpectrumCanvas's guard skips it
// until the frame is visible again.
document.querySelectorAll(".collapse-toggle").forEach((toggle) => {
  toggle.addEventListener("click", () => {
    const panel = toggle.closest(".control-block");
    const collapsed = panel.classList.toggle("is-collapsed");
    toggle.setAttribute("aria-expanded", String(!collapsed));

    if (!collapsed && panel.contains(spectrumCanvas)) {
      sizeSpectrumCanvas();
    }
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
populateTemperamentControls();
updateReferencePitch(state.a4);
updateFineTuningLabel();
updateTestToneDisplay(getTestToneFrequency());
micGainValueLabelEl.textContent = `${Number(micGainRange.value).toFixed(1)}×`;
setSpectrumStyle(state.spectrumStyle);
buildFrequencyTable();
sizeSpectrumCanvas();
resetVisuals();
