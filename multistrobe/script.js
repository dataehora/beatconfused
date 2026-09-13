const T = TunerCommon;

const toggleMicBtn = document.getElementById("toggleMicBtn");
const powerSwitchStateEl = document.getElementById("powerSwitchState");
const tuningStatementEl = document.getElementById("tuningStatement");
const freqTableTuningNoteEl = document.getElementById("freqTableTuningNote");
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

const spectrumCanvas = document.getElementById("spectrumCanvas");
const spectrumStyleCheckbox = document.getElementById("spectrumStyleCheckbox");
const spectrumStyleToggleEl = document.getElementById("spectrumStyleToggle");
const spectrumLowLabelEl = document.getElementById("spectrumLowLabel");
const spectrumRefLabelEl = document.getElementById("spectrumRefLabel");
const spectrumHighLabelEl = document.getElementById("spectrumHighLabel");
const octaveFreqTableHead = document.getElementById("octaveFreqTableHead");
const octaveFreqTableBody = document.getElementById("octaveFreqTableBody");

const sharpsContainer = document.getElementById("strobeDiscsSharps");
const naturalsContainer = document.getElementById("strobeDiscsNaturals");

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

// Where each sharp disc sits along the naturals row, expressed as which
// natural-key boundary (of 7) it floats above — e.g. C♯ sits right after C
// (boundary 1), matching a real piano keyboard's black-key spacing (no
// sharp between E-F or B-C, so F♯/G♯/A♯ pick up 2 boundaries further out).
const SHARP_BOUNDARY = { "C♯": 1, "D♯": 2, "F♯": 4, "G♯": 5, "A♯": 6 };
const NATURAL_COLUMN_COUNT = 7;

// Every disc uses the exact shared Octave Strobe Tuner proportions (see
// StrobeDiscEngine.buildStageGeometry) — the same 180° dome, thin bezel,
// tick marks and flat/sharp glyphs /strobetuner/'s single hero disc uses,
// just at this page's compact per-key scale. A future tweak to that shared
// geometry or bezel decoration applies here automatically, with no code
// change on this page.
const DISC_GEOMETRY = StrobeDiscEngine.buildStageGeometry({ caseR: 100 });

const PITCH_CHECK_INTERVAL_MS = 45;

// The test tone's frequency slider spans the full piano keyboard, A0 to C8.
const TEST_FREQ_MIN = 19;
const TEST_FREQ_MAX = 4434;
const FINE_TUNING_MAX_CENTS = 50;

const clamp = T.clamp;
const setMicStatus = T.setMicStatusFactory(micStatus);

const state = {
  a4: T.DEFAULT_A4,
  activeSource: null, // null | "mic" | "test"
};

const DISCS = []; // 12 entries (NOTE_NAMES order): { name, el, rings: [...] }
// Every disc's rings, flattened into one lookup by MIDI note — the same
// shape /strobetuner/'s shadow rings are, so the shared Frequency Table
// helper can drive live cents readings straight from the real, on-screen
// discs here (no separate "shadow" analysis needed: all 12 notes are
// already visible and analyzed every tick).
const ringsByMidi = new Map();

// Wired up first since recomputeRingTargets below needs to read its
// current tuning standard/key — see temperament.pianoNoteFrequency.
const temperament = T.setupTemperament({
  selects: temperamentSelects,
  keyRows: temperamentKeyRows,
  keySelects: temperamentKeySelects,
  onChange: () => {
    recomputeRingTargets();
    buildFreqTable();
    updateTestToneDisplay(testTone.getFrequency());
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

function updateTestToneDisplay(frequency) {
  testTone.updateFreqLabel(frequency);
  const note = T.frequencyToNote(frequency, state.a4, pianoNoteFrequency);
  const roundedCents = Math.round(note.cents);
  const sign = roundedCents > 0 ? "+" : "";
  testToneNoteEl.textContent = `${note.name}${note.octave} ${sign}${roundedCents}¢`;
  T.updateTestToneVariance(
    note,
    { fillEl: varianceFillEl, prevNoteEl: variancePrevNoteEl, currentNoteEl: varianceCurrentNoteEl, nextNoteEl: varianceNextNoteEl },
    { inTuneThresholdCents: StrobeDiscEngine.IN_TUNE_THRESHOLD_CENTS, getTuneMixPercent: StrobeDiscEngine.getTuneMixPercent },
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
    const disc = StrobeDiscEngine.buildDisc(name, midiList, DISC_GEOMETRY);
    StrobeDiscEngine.addBezelDecoration(disc);

    if (isSharp) {
      disc.el.style.left = `${(SHARP_BOUNDARY[name] / NATURAL_COLUMN_COUNT) * 100}%`;
    }

    DISCS.push(disc);
    disc.rings.forEach((ring) => ringsByMidi.set(ring.midi, ring));
    (isSharp ? sharpsContainer : naturalsContainer).appendChild(disc.el);
  });
}

// Recomputes every ring's target frequency (and the analysis window that
// depends on it) from the current A4 and tuning standard — called at load
// and whenever the reference pitch or tuning standard/key changes.
function recomputeRingTargets() {
  const sampleRate = audioContext ? audioContext.sampleRate : 44100;
  DISCS.forEach((disc) => StrobeDiscEngine.recomputeDiscTargets(disc, state.a4, sampleRate));
}

/* ============================================================
   FREQUENCY TABLE — the shared octave-by-note table (see
   T.buildOctaveFrequencyTable in shared/tuner-common.js), driven every
   tick straight from the real discs' own rings via ringsByMidi. There's
   no autocorrelation-identified "predominant" note on this page (every
   note is always on screen at once), so no cell ever gets the fundamental
   highlight.
   ============================================================ */
const freqTableCellsByMidi = new Map();

function buildFreqTable() {
  T.buildOctaveFrequencyTable({
    headRow: octaveFreqTableHead,
    body: octaveFreqTableBody,
    pianoNoteFrequency: (midi) => pianoNoteFrequency(midi, state.a4),
    cellsByMidi: freqTableCellsByMidi,
  });
}

function updateFreqTableLiveCents() {
  T.updateOctaveFrequencyTableRings(freqTableCellsByMidi, ringsByMidi, null, StrobeDiscEngine.IN_TUNE_THRESHOLD_CENTS);
}

function resetFreqTableLiveCents() {
  T.resetOctaveFrequencyTable(freqTableCellsByMidi);
}

function resetVisuals() {
  DISCS.forEach((disc) => StrobeDiscEngine.resetDisc(disc));
  resetFreqTableLiveCents();
  inputMonitor.reset();
  spectrum.clear();
}

/* ============================================================
   AUDIO SOURCE — the microphone; see TEST TONE below for the other one.
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

    // audioContext.currentTime (seconds, audio-clock), not performance.now()
    // — see StrobeDiscEngine.analyzeRing's comment for why this matters.
    const now = audioContext.currentTime;
    const sampleRate = audioContext.sampleRate;

    DISCS.forEach((disc) => StrobeDiscEngine.analyzeDisc(disc, timeDomainBuffer, sampleRate, now));
    updateFreqTableLiveCents();
  }

  DISCS.forEach((disc) => StrobeDiscEngine.renderDisc(disc, dt));
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
   T.createTestTone), tapped into the same analyser a mic signal would use.
   Unlike /tuner/ and /strobetuner/, this page has no single "detected
   note" readout to bypass — all twelve discs already analyze the real
   synthesized audio independently via Goertzel, exactly like a mic
   signal, so the correct disc lights up with no special-casing here.
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
  recomputeRingTargets();
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

/* ============================================================
   CONTROLS
   ============================================================ */
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
    recomputeRingTargets();
    buildFreqTable();
    updateTestToneDisplay(testTone.getFrequency());
    spectrum.updateLabels(getSpectrumRange(), state.a4);
    updateTuningStatement();
  },
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

buildDiscs();
referencePitch.setA4(state.a4);
testTone.updateCentsLabel();
updateTestToneDisplay(testTone.getFrequency());
spectrum.setStyle("vintage");
spectrum.sizeCanvas();
resetVisuals();
