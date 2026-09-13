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

const PITCH_CHECK_INTERVAL_MS = 45;

const clamp = T.clamp;
const setMicStatus = T.setMicStatusFactory(micStatus);

const state = {
  a4: T.DEFAULT_A4,
  activeSource: null, // null | "mic"
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

buildDiscs();
referencePitch.setA4(state.a4);
spectrum.setStyle("vintage");
spectrum.sizeCanvas();
resetVisuals();
