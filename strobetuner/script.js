/* ============================================================
   OCTAVE STROBE TUNER — a hybrid of /tuner/'s live pitch identification
   and /multistrobe/'s per-note, per-octave strobe display: autocorrelation
   picks out which of the 12 notes is predominant (exactly like /tuner/'s
   note readout), then that single note's disc — built from the very same
   shared/strobe-disc.js engine /multistrobe/'s twelve discs are built
   from — is shown, with every one of its real octave-instances lit and
   spinning independently via Goertzel analysis.

   Only one disc is ever mounted at a time for the visual display; discs
   are cached per note so switching back to a recently-played note doesn't
   rebuild its SVG. Separately, 12 lightweight "shadow" ring sets (no SVG,
   just the same engine's ring bookkeeping) are analyzed every tick for
   every note at once, so the Frequency Table below can show a live cents
   reading for whichever notes are actually sounding — not just whichever
   one is the current on-screen hero.
   ============================================================ */

const T = TunerCommon;

const noteNameEl = document.getElementById("noteName");
const noteReadoutEl = document.getElementById("noteReadout");
const strobeSection = document.querySelector(".strobetuner");
const discContainer = document.getElementById("strobeDiscContainer");

const toggleMicBtn = document.getElementById("toggleMicBtn");
const powerSwitchStateEl = document.getElementById("powerSwitchState");
const tuningStatementEl = document.getElementById("tuningStatement");
const micStatus = document.getElementById("micStatus");
const decreasePitchBtn = document.getElementById("decreasePitchBtn");
const increasePitchBtn = document.getElementById("increasePitchBtn");
const pitchInput = document.getElementById("pitchInput");
const pitchRange = document.getElementById("pitchRange");
const pitchPresetInputs = document.querySelectorAll('input[name="pitchPreset"]');
const temperamentSelects = document.querySelectorAll(".temperament-select");
const temperamentKeyRows = document.querySelectorAll(".temperament-key-row");
const temperamentKeySelects = document.querySelectorAll(".temperament-key-select");

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
const octaveFreqTableHead = document.getElementById("octaveFreqTableHead");
const octaveFreqTableBody = document.getElementById("octaveFreqTableBody");
const octaveLegendEl = document.getElementById("octaveLegend");

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

const NOTE_NAMES = StrobeDiscEngine.NOTE_NAMES;

// Autocorrelation only needs to resolve *which note* is sounding (not a
// precise cents reading — the disc's own Goertzel rings do that), so it
// runs on a short trailing window of the same buffer the Goertzel rings
// read from, matching /tuner/'s own FFT_SIZE rather than the much longer
// window the low-frequency rings need.
const AUTOCORRELATION_WINDOW = 4096;
const SPECTRUM_FFT_SIZE = 4096;
const MIN_FREQ_HZ = 40;
const MAX_FREQ_HZ = 1600;
const MIN_RMS = 0.012;
const MIN_CLARITY = 0.9;

const PITCH_CHECK_INTERVAL_MS = 45;
const SILENCE_TIMEOUT_MS = 500;
// How long the running tuner must hear nothing before the "no signal"
// sign takes the note readout's place — a short grace period so brief
// gaps between notes don't flash it, matching /tuner/'s.
const NO_SIGNAL_DELAY_MS = 3000;

// A wide, 160° window rather than a full half-circle — closer to a real
// vintage strobe tuner's small display glass than a half-dial, and with
// room enough left over for the reference bezel around it. cx/viewBox are
// widened to fit the arc's corners at this span (half-span 80° pushes them
// almost as far out as the case radius itself). The bezel between windowR
// and caseR is a thin, ~3.5%-of-caseR band — the same slim proportion
// /tuner/'s Needle and Meter cases use — rather than the thicker ring a
// naive half-circle border would suggest.
const STAGE_GEOMETRY = {
  cx: 147,
  cy: 150,
  arcSpanDeg: 160,
  viewBox: "0 0 294 165",
  caseR: 145,
  windowR: 140,
  ringOuterR: 136,
  hubR: 7,
  hubDotR: 4.5,
  ringGap: 1,
  // A wide arc's boundary wedges are big enough that a spinning ring can
  // visibly poke outside the window sector without this — see the
  // comment on clipToWindow in shared/strobe-disc.js.
  clipToWindow: true,
  // The wedge pattern spans the full 360° (not just the visible arc), so
  // a ring can spin any amount, in either direction, without ever running
  // out of pattern to show — see the comment on continuousWedges in
  // shared/strobe-disc.js.
  continuousWedges: true,
};

const SVG_NS = "http://www.w3.org/2000/svg";

const clamp = T.clamp;
const setMicStatus = T.setMicStatusFactory(micStatus);

const state = {
  a4: T.DEFAULT_A4,
  activeSource: null, // null | "mic"
  hasSignal: false,
  currentNoteName: null,
  lastConfidentAt: 0,
  // The exact MIDI note (name + octave) autocorrelation last detected —
  // distinct from currentNoteName (pitch class only), used purely to
  // highlight the "best guess" fundamental ring. The disc's own per-ring
  // Goertzel confidence (not this) is still what actually lights up each
  // ring — see the comment in mainLoop.
  fundamentalMidi: null,
};

const discCache = new Map(); // note name -> hero disc (large, on-screen SVG)
let activeDisc = null;

// One lightweight { name, rings } per pitch class, analyzed every tick for
// every note at once (no SVG, no rendering) — see the file comment above.
// This is what actually drives the Frequency Table's live cents column,
// independent of which single note currently has the visible hero disc.
const shadowDiscs = [];
const shadowRingsByMidi = new Map();

// Wired up first since several other controllers below need to read its
// current tuning standard/key — see temperament.pianoNoteFrequency.
const temperament = T.setupTemperament({
  selects: temperamentSelects,
  keyRows: temperamentKeyRows,
  keySelects: temperamentKeySelects,
  onChange: () => {
    recomputeAllTargets();
    buildOctaveFreqTable();
    spectrum.updateLabels(getSpectrumRange(), state.a4);
    updateTuningStatement();
  },
});

function pianoNoteFrequency(midi, a4) {
  return temperament.pianoNoteFrequency(midi, a4);
}

function getSpectrumRange() {
  return {
    min: pianoNoteFrequency(T.PIANO_MIN_MIDI, state.a4),
    max: pianoNoteFrequency(T.PIANO_MAX_MIDI, state.a4),
  };
}

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

/* ============================================================
   PITCH DETECTION — time-domain autocorrelation, normalized per-lag as an
   NSDF (Normalized Square Difference Function, the same normalization the
   McLeod Pitch Method uses) rather than against one fixed, full-buffer
   energy figure. That fixed-denominator version is what /tuner/'s original
   detectPitch used to do, and it systematically penalized low notes: the
   numerator at a lag L only sums (size - L) sample pairs, so as L grows
   for lower frequencies, that shrinking sum was being compared against the
   *same* full-length sumSquares computed once for the whole buffer — a
   perfectly periodic low note could land well under MIN_CLARITY for no
   reason but its own lag length (e.g. a clean ~110 Hz tone in a 4096-
   sample window tops out around clarity ~0.89, already below the 0.9 cutoff,
   before any real noise or inharmonicity). Normalizing energy over the
   same shrinking window the numerator itself uses removes that bias, so
   clarity reflects actual periodicity at every frequency alike. Restricted
   to the plausible instrument frequency range. Adapted from /tuner/'s
   detectPitch — only the note *name* is used here (the disc's Goertzel
   rings supply the actual cents readings), so there is no need for
   /tuner/'s temperament-aware frequency-to-note mapping.
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
      refinedLag = bestIndex + minLag + (0.5 * (c0 - c2)) / denom;
    }
  }

  if (refinedLag <= 0) {
    return null;
  }

  return { frequency: sampleRate / refinedLag, clarity };
}

function frequencyToPitchClassName(frequency, a4) {
  return NOTE_NAMES[((frequencyToMidi(frequency, a4) % 12) + 12) % 12];
}

// The exact equal-tempered MIDI note (name + octave) nearest a detected
// frequency — used only to pick which ring is the "best guess" fundamental
// to highlight (see updateDiscExtras). The disc's own rings decide their
// own state independently of this.
function frequencyToMidi(frequency, a4) {
  return Math.round(69 + 12 * Math.log2(frequency / a4));
}

/* ============================================================
   REFERENCE BEZEL — a static ring of calibration ticks around the outer
   rim of each disc (between ringOuterR and caseR), framing it the way a
   physical strobe tuner's bezel does, plus ♭/♯ glyphs marking the flat
   and sharp ends of the arc, an index mark at dead center, and a soft
   vignette + glass highlight layered over the rings themselves — the same
   glass-and-brass language /tuner/'s strobe visual uses, so this reads as
   an old piece of measuring equipment rather than a flat vector graphic.
   Purely decorative/orientational: unlike the needle gauge on /tuner/,
   there's no pointer to read a position off this scale — the ring's
   *rotation*, not its position, is what carries the tuning information.
   Drawn directly into each disc's own <svg> (not a separate overlay) so
   it's guaranteed to stay pixel-aligned with that disc's geometry.
   ============================================================ */
function polarPoint(cx, cy, r, angleDeg) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.sin(rad), y: cy - r * Math.cos(rad) };
}

function sectorPath(cx, cy, r, startDeg, endDeg) {
  const start = polarPoint(cx, cy, r, startDeg);
  const end = polarPoint(cx, cy, r, endDeg);
  const largeArc = endDeg - startDeg > 180 ? 1 : 0;

  return [
    `M ${cx} ${cy}`,
    `L ${start.x.toFixed(2)} ${start.y.toFixed(2)}`,
    `A ${r} ${r} 0 ${largeArc} 1 ${end.x.toFixed(2)} ${end.y.toFixed(2)}`,
    "Z",
  ].join(" ");
}

function addBezelDecoration(disc) {
  const svg = disc.el.querySelector("svg");
  const { cx, cy, caseR, windowR } = STAGE_GEOMETRY;
  const halfSpan = STAGE_GEOMETRY.arcSpanDeg / 2;

  // A soft vignette + glass highlight, layered over the rings but under
  // the hub — inserted into the same clipped group the rings live in
  // (found by its clip-path attribute) so it never spills past the
  // window's own sector.
  const ringsParent = svg.querySelector("[clip-path]");

  if (ringsParent) {
    const vignette = document.createElementNS(SVG_NS, "path");
    vignette.setAttribute("class", "disc-vignette");
    vignette.setAttribute("d", sectorPath(cx, cy, windowR, -halfSpan, halfSpan));
    ringsParent.appendChild(vignette);

    const highlight = document.createElementNS(SVG_NS, "ellipse");
    highlight.setAttribute("class", "disc-glass-highlight");
    highlight.setAttribute("cx", String(cx));
    highlight.setAttribute("cy", String(cy - windowR * 0.42));
    highlight.setAttribute("rx", String(windowR * 0.62));
    highlight.setAttribute("ry", String(windowR * 0.3));
    ringsParent.appendChild(highlight);
  }

  // Ticks live entirely within the thin bezel band between windowR and
  // caseR — the rings themselves get everything inside windowR, since
  // they're the part that actually matters here.
  const majorTickInnerR = caseR - 6;
  const minorTickInnerR = caseR - 3;
  const tickOuterR = caseR - 1;
  const labelR = windowR + 1;

  const ticksGroup = document.createElementNS(SVG_NS, "g");
  ticksGroup.setAttribute("class", "disc-scale-ticks");

  for (let angle = -halfSpan; angle <= halfSpan; angle += 10) {
    const isMajor = angle % 30 === 0;
    const isIndex = angle === 0;
    const inner = polarPoint(cx, cy, isMajor ? majorTickInnerR : minorTickInnerR, angle);
    const outer = polarPoint(cx, cy, tickOuterR, angle);

    const tick = document.createElementNS(SVG_NS, "line");
    let tickClass = "disc-scale-tick";
    if (isMajor) tickClass += " disc-scale-tick-major";
    if (isIndex) tickClass += " disc-scale-tick-index";
    tick.setAttribute("class", tickClass);
    tick.setAttribute("x1", inner.x.toFixed(2));
    tick.setAttribute("y1", inner.y.toFixed(2));
    tick.setAttribute("x2", outer.x.toFixed(2));
    tick.setAttribute("y2", outer.y.toFixed(2));
    ticksGroup.appendChild(tick);
  }

  const flatPoint = polarPoint(cx, cy, labelR, -halfSpan);
  const flatLabel = document.createElementNS(SVG_NS, "text");
  flatLabel.setAttribute("class", "disc-scale-label disc-scale-label-flat");
  flatLabel.setAttribute("x", flatPoint.x.toFixed(2));
  flatLabel.setAttribute("y", flatPoint.y.toFixed(2));
  flatLabel.setAttribute("text-anchor", "middle");
  flatLabel.textContent = "♭";
  ticksGroup.appendChild(flatLabel);

  const sharpPoint = polarPoint(cx, cy, labelR, halfSpan);
  const sharpLabel = document.createElementNS(SVG_NS, "text");
  sharpLabel.setAttribute("class", "disc-scale-label disc-scale-label-sharp");
  sharpLabel.setAttribute("x", sharpPoint.x.toFixed(2));
  sharpLabel.setAttribute("y", sharpPoint.y.toFixed(2));
  sharpLabel.setAttribute("text-anchor", "middle");
  sharpLabel.textContent = "♯";
  ticksGroup.appendChild(sharpLabel);

  svg.appendChild(ticksGroup);
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
    addBezelDecoration(disc);
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

// Mirrors the fundamental-highlight state onto the active disc's rings —
// the disc's own per-ring Goertzel confidence (not this) is what actually
// lights a ring up; this only marks autocorrelation's "best guess" among
// whichever rings are already active.
function updateDiscExtras(disc) {
  disc.rings.forEach((ring) => {
    const isFundamental = state.fundamentalMidi === ring.midi;
    ring.ringGroupEl.classList.toggle("is-fundamental", isFundamental);
  });
}

function resetDiscExtras(disc) {
  disc.rings.forEach((ring) => {
    ring.ringGroupEl.classList.remove("is-fundamental");
  });
}

/* ============================================================
   SHADOW RINGS — 12 lightweight { name, rings } sets (no SVG, no visual
   disc), one per pitch class, covering the exact same octave-instances as
   the on-screen discs above. Built once at load and analyzed every tick
   regardless of which note is currently the hero, so the Frequency Table
   can show a live cents reading for whichever notes are actually sounding
   — including ones other than the single note currently on screen (e.g. a
   chord, or a note's audible overtones landing on another pitch class).
   Reuses StrobeDiscEngine.recomputeDiscTargets/analyzeDisc directly: both
   only ever touch `.rings`, so a plain { rings } object works exactly like
   a real disc as far as they're concerned.
   ============================================================ */
function buildShadowRings() {
  NOTE_NAMES.forEach((name) => {
    const midiList = StrobeDiscEngine.midiListForPitchClass(NOTE_NAMES.indexOf(name));
    const rings = midiList.map((midi) => ({
      midi,
      targetFreq: 0,
      windowSamples: 0,
      previousPhase: 0,
      previousTimestamp: 0,
      hasPhase: false,
      confident: false,
      smoothedCents: 0,
    }));

    const shadow = { name, rings };
    shadowDiscs.push(shadow);
    rings.forEach((ring) => shadowRingsByMidi.set(ring.midi, ring));
  });
}

function recomputeAllTargets() {
  const sampleRate = audioContext ? audioContext.sampleRate : 44100;
  shadowDiscs.forEach((shadow) => StrobeDiscEngine.recomputeDiscTargets(shadow, state.a4, sampleRate));

  if (activeDisc) {
    StrobeDiscEngine.recomputeDiscTargets(activeDisc, state.a4, sampleRate);
  }
}

function analyzeShadowRings(buffer, sampleRate, now) {
  shadowDiscs.forEach((shadow) => StrobeDiscEngine.analyzeDisc(shadow, buffer, sampleRate, now));
}

function resetShadowRings() {
  shadowRingsByMidi.forEach((ring) => {
    ring.hasPhase = false;
    ring.confident = false;
    ring.smoothedCents = 0;
  });
}

/* ============================================================
   FREQUENCY TABLE — columns are the 12 notes, rows are octaves 0-8 (every
   key of an 88-key piano, from A0), preloaded with each cell's frequency
   under the current tuning standard. Each cell also carries a live cents
   readout, driven every tick by the shadow ring at that exact MIDI note —
   the same compact "note + deviation together" idea /tuner/'s readout
   uses, just laid out as a grid instead of one row per key.
   ============================================================ */
const OCTAVE_MIN = Math.floor(T.PIANO_MIN_MIDI / 12) - 1; // 0 (A0)
const OCTAVE_MAX = Math.floor(T.PIANO_MAX_MIDI / 12) - 1; // 8 (C8)

const freqTableCellsByMidi = new Map();

function buildOctaveFreqTableHead() {
  if (octaveFreqTableHead.childElementCount > 1) {
    return;
  }

  NOTE_NAMES.forEach((name) => {
    const th = document.createElement("th");
    th.textContent = name;
    octaveFreqTableHead.appendChild(th);
  });
}

function buildOctaveFreqTable() {
  buildOctaveFreqTableHead();
  octaveFreqTableBody.innerHTML = "";
  freqTableCellsByMidi.clear();

  for (let octave = OCTAVE_MIN; octave <= OCTAVE_MAX; octave += 1) {
    const row = document.createElement("tr");
    const octaveCell = document.createElement("td");
    octaveCell.className = "freq-table-note-col";
    octaveCell.textContent = String(octave);
    row.appendChild(octaveCell);

    NOTE_NAMES.forEach((name, pitchClass) => {
      const midi = (octave + 1) * 12 + pitchClass;
      const cell = document.createElement("td");
      cell.className = "octave-cell";

      if (midi < T.PIANO_MIN_MIDI || midi > T.PIANO_MAX_MIDI) {
        cell.classList.add("is-out-of-range");
      } else {
        const freqEl = document.createElement("span");
        freqEl.className = "octave-cell-freq";
        freqEl.textContent = pianoNoteFrequency(midi, state.a4).toFixed(2);

        const centsEl = document.createElement("span");
        centsEl.className = "octave-cell-cents";
        centsEl.hidden = true;

        cell.appendChild(freqEl);
        cell.appendChild(centsEl);
        freqTableCellsByMidi.set(midi, { cell, centsEl });
      }

      row.appendChild(cell);
    });

    octaveFreqTableBody.appendChild(row);
  }
}

function updateFreqTableLiveCents() {
  freqTableCellsByMidi.forEach(({ cell, centsEl }, midi) => {
    const ring = shadowRingsByMidi.get(midi);
    const isFundamental = state.fundamentalMidi === midi;
    cell.classList.toggle("is-fundamental", isFundamental);

    if (!ring || !ring.confident) {
      cell.classList.remove("is-active", "is-in-tune");
      centsEl.hidden = true;
      return;
    }

    const rounded = Math.round(ring.smoothedCents);
    const inTune = Math.abs(ring.smoothedCents) <= StrobeDiscEngine.IN_TUNE_THRESHOLD_CENTS;
    const sign = rounded > 0 ? "+" : "";
    centsEl.textContent = `${sign}${rounded}¢`;
    centsEl.hidden = false;
    cell.classList.add("is-active");
    cell.classList.toggle("is-in-tune", inTune);
  });
}

function resetFreqTableLiveCents() {
  freqTableCellsByMidi.forEach(({ cell, centsEl }) => {
    cell.classList.remove("is-active", "is-in-tune", "is-fundamental");
    centsEl.hidden = true;
  });
}

/* ============================================================
   OCTAVE LEGEND — a single "0 1 2 3 4 5 6 7 8" row below the disc (see
   .octave-legend), one entry per octave a real 88-key piano spans. Unlike
   the Frequency Table above (which tracks all 12 notes independently via
   shadowRingsByMidi), this only ever reflects the single note currently
   on-screen as the hero disc — "the predominant note" — so octave 0 only
   ever lights up for A/A♯/B (the only pitch classes with an A0-range key)
   and octave 8 only for C, exactly matching that disc's own rings.
   ============================================================ */
const octaveLegendCellsByOctave = new Map();

function buildOctaveLegend() {
  for (let octave = OCTAVE_MIN; octave <= OCTAVE_MAX; octave += 1) {
    const item = document.createElement("span");
    item.className = "octave-legend-item";

    const numEl = document.createElement("span");
    numEl.className = "octave-legend-num";
    numEl.textContent = String(octave);

    const noteEl = document.createElement("span");
    noteEl.className = "octave-legend-note";
    noteEl.hidden = true;

    item.appendChild(numEl);
    item.appendChild(noteEl);
    octaveLegendEl.appendChild(item);
    octaveLegendCellsByOctave.set(octave, { item, noteEl });
  }
}

function updateOctaveLegend() {
  if (!state.hasSignal || !activeDisc) {
    resetOctaveLegend();
    return;
  }

  const confidentOctaves = new Set();

  activeDisc.rings.forEach((ring) => {
    const octave = Math.floor(ring.midi / 12) - 1;
    const cell = octaveLegendCellsByOctave.get(octave);

    if (!cell) {
      return;
    }

    if (!ring.confident) {
      cell.item.classList.remove("is-in-tune");
      cell.noteEl.hidden = true;
      return;
    }

    confidentOctaves.add(octave);
    const inTune = Math.abs(ring.smoothedCents) <= StrobeDiscEngine.IN_TUNE_THRESHOLD_CENTS;
    cell.noteEl.textContent = state.currentNoteName;
    cell.noteEl.hidden = false;
    cell.item.classList.toggle("is-in-tune", inTune);
  });

  octaveLegendCellsByOctave.forEach((cell, octave) => {
    if (!confidentOctaves.has(octave)) {
      cell.item.classList.remove("is-in-tune");
      cell.noteEl.hidden = true;
    }
  });
}

function resetOctaveLegend() {
  octaveLegendCellsByOctave.forEach((cell) => {
    cell.item.classList.remove("is-in-tune");
    cell.noteEl.hidden = true;
  });
}

/* ============================================================
   READOUT
   ============================================================ */
const NO_SIGNAL_MESSAGE = "no signal, check the microphone in the input monitor below";

function updateReadout() {
  const inTune = !state.hasSignal;
  strobeSection.classList.toggle("in-tune", inTune);
  noteReadoutEl.hidden = state.activeSource === null;

  if (!state.hasSignal || !state.currentNoteName) {
    const silentForMs = performance.now() - state.lastConfidentAt;
    const showNoSignal = state.activeSource === "mic" && silentForMs > NO_SIGNAL_DELAY_MS;
    noteNameEl.textContent = showNoSignal ? NO_SIGNAL_MESSAGE : "–";
    noteNameEl.classList.toggle("is-no-signal", showNoSignal);
    return;
  }

  noteNameEl.classList.remove("is-no-signal");
  noteNameEl.textContent = state.currentNoteName;
}

function resetVisuals() {
  state.hasSignal = false;
  state.currentNoteName = null;
  state.fundamentalMidi = null;

  if (activeDisc) {
    StrobeDiscEngine.resetDisc(activeDisc);
    resetDiscExtras(activeDisc);
  }

  resetFreqTableLiveCents();
  resetOctaveLegend();
  updateReadout();
  inputMonitor.reset();
  spectrum.clear();
}

/* ============================================================
   AUDIO SOURCE — microphone only (no test tone on this page, unlike
   /tuner/).
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
    analyserNode.fftSize = StrobeDiscEngine.ANALYSER_BUFFER_SIZE;
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

    analyserNode.getFloatTimeDomainData(timeDomainBuffer);
    inputMonitor.updateLevelMeter(inputMonitor.computeRms(timeDomainBuffer));
    analyserNode.getByteFrequencyData(freqDataBuffer);
    spectrum.update(freqDataBuffer, audioContext.sampleRate, StrobeDiscEngine.ANALYSER_BUFFER_SIZE, getSpectrumRange());

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
      state.fundamentalMidi = frequencyToMidi(result.frequency, state.a4);
    } else if (state.hasSignal && timestamp - state.lastConfidentAt > SILENCE_TIMEOUT_MS) {
      state.hasSignal = false;
      state.currentNoteName = null;
      state.fundamentalMidi = null;

      if (activeDisc) {
        StrobeDiscEngine.resetDisc(activeDisc);
        resetDiscExtras(activeDisc);
      }
    }

    updateReadout();

    // The disc's own Goertzel rings — not the autocorrelation result —
    // drive the actual tuning display, exactly like /multistrobe/'s
    // discs: each ring independently decides whether it's hearing its own
    // exact target frequency. fundamentalMidi (from autocorrelation) only
    // picks which ring gets the "best guess" highlight.
    if (state.hasSignal && state.currentNoteName) {
      const disc = setActiveDisc(state.currentNoteName, sampleRate);
      StrobeDiscEngine.analyzeDisc(disc, timeDomainBuffer, sampleRate, now);
      updateDiscExtras(disc);
    }

    // All 12 notes' octaves, analyzed independently of which one is the
    // current on-screen hero — see the file comment at the top.
    analyzeShadowRings(timeDomainBuffer, sampleRate, now);
    updateFreqTableLiveCents();
    updateOctaveLegend();
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
  recomputeAllTargets();

  mediaStreamSource = ctx.createMediaStreamSource(mediaStream);
  micGainNode = ctx.createGain();
  micGainNode.gain.value = Number(micGainRange.value);
  mediaStreamSource.connect(micGainNode);
  micGainNode.connect(analyserNode);
  // Deliberately not connected to audioContext.destination — we only
  // analyze the signal, never play it back, so there's no feedback loop.

  state.activeSource = "mic";
  state.lastConfidentAt = performance.now();
  toggleMicBtn.setAttribute("aria-pressed", "true");
  powerSwitchStateEl.textContent = "ON";
  setMicStatus(T.MIC_MESSAGES.listening);
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

  toggleMicBtn.setAttribute("aria-pressed", "false");
  powerSwitchStateEl.textContent = "OFF";
  setMicStatus(T.MIC_MESSAGES.idle);
  endRenderLoop();
  resetVisuals();
  resetShadowRings();
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
  const selected = temperament.getTemperament();
  const keyPart = selected.needsKey ? ` in ${NOTE_NAMES[temperament.state.temperamentKey]}` : "";
  tuningStatementEl.textContent = `Tuning for ${selected.name}${keyPart} · ${state.a4} Hz`;
}

const referencePitch = T.setupReferencePitch({
  pitchInput,
  pitchRange,
  decreaseBtn: decreasePitchBtn,
  increaseBtn: increasePitchBtn,
  presetInputs: pitchPresetInputs,
  onChange: (a4) => {
    state.a4 = a4;
    recomputeAllTargets();
    buildOctaveFreqTable();
    spectrum.updateLabels(getSpectrumRange(), state.a4);
    updateTuningStatement();
  },
});

toggleMicBtn.addEventListener("click", toggleMic);

T.wireCollapsibles((panel) => {
  if (panel.contains(spectrumCanvas)) {
    spectrum.sizeCanvas();
  }
});

T.wireTransportShortcuts({
  onToggle: toggleMic,
  onA4Delta: (delta) => referencePitch.setA4(state.a4 + delta),
});

// Release the microphone when the tab is hidden, rather than leaving it
// running in the background.
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopMic();
  }
});

// A freshly built disc's rings start idle by construction (see buildDisc),
// so mounting it here is enough to have something other than blank space
// on the page before the tuner is even started.
const DEFAULT_NOTE_NAME = "A";
setActiveDisc(DEFAULT_NOTE_NAME, 44100);
buildShadowRings();
buildOctaveLegend();

referencePitch.setA4(state.a4);
spectrum.setStyle("vintage");
spectrum.sizeCanvas();
updateReadout();
inputMonitor.reset();
