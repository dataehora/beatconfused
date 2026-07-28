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
const octaveLegendEl = document.getElementById("octaveLegend");

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
// page, in the same half-circle style as /tuner/'s own strobe device. The
// gap between ringOuterR and caseR is deliberately wide (unlike
// /multistrobe/'s discs) to leave room for the reference bezel drawn by
// addScaleTicks() below.
const STAGE_GEOMETRY = {
  cx: 150,
  cy: 150,
  arcSpanDeg: 180,
  viewBox: "0 0 300 165",
  caseR: 145,
  windowR: 122,
  ringOuterR: 118,
  hubR: 7,
  hubDotR: 4.5,
  ringGap: 1,
  // A 180° arc's boundary wedges are big enough that a spinning ring can
  // visibly poke outside the window sector without this — see the
  // comment on clipToWindow in shared/strobe-disc.js.
  clipToWindow: true,
};

const SVG_NS = "http://www.w3.org/2000/svg";

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

const state = {
  a4: DEFAULT_A4,
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
   and sharp ends of the arc (rings rotate clockwise when sharp,
   counter-clockwise when flat — see shared/strobe-disc.js's renderDisc).
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

function addScaleTicks(disc) {
  const svg = disc.el.querySelector("svg");
  const { cx, cy, caseR } = STAGE_GEOMETRY;
  const halfSpan = STAGE_GEOMETRY.arcSpanDeg / 2;
  const majorTickInnerR = caseR - 9;
  const minorTickInnerR = caseR - 5;
  const tickOuterR = caseR - 2;

  const ticksGroup = document.createElementNS(SVG_NS, "g");
  ticksGroup.setAttribute("class", "disc-scale-ticks");

  for (let angle = -halfSpan; angle <= halfSpan; angle += 10) {
    const isMajor = angle % 30 === 0;
    const inner = polarPoint(cx, cy, isMajor ? majorTickInnerR : minorTickInnerR, angle);
    const outer = polarPoint(cx, cy, tickOuterR, angle);

    const tick = document.createElementNS(SVG_NS, "line");
    tick.setAttribute("class", isMajor ? "disc-scale-tick disc-scale-tick-major" : "disc-scale-tick");
    tick.setAttribute("x1", inner.x.toFixed(2));
    tick.setAttribute("y1", inner.y.toFixed(2));
    tick.setAttribute("x2", outer.x.toFixed(2));
    tick.setAttribute("y2", outer.y.toFixed(2));
    ticksGroup.appendChild(tick);
  }

  const flatPoint = polarPoint(cx, cy, majorTickInnerR - 9, -halfSpan);
  const flatLabel = document.createElementNS(SVG_NS, "text");
  flatLabel.setAttribute("class", "disc-scale-label disc-scale-label-flat");
  flatLabel.setAttribute("x", flatPoint.x.toFixed(2));
  flatLabel.setAttribute("y", flatPoint.y.toFixed(2));
  flatLabel.setAttribute("text-anchor", "middle");
  flatLabel.textContent = "♭";
  ticksGroup.appendChild(flatLabel);

  const sharpPoint = polarPoint(cx, cy, majorTickInnerR - 9, halfSpan);
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
   OCTAVE LEGEND — a plain HTML readout beside the disc, one row per ring,
   showing that octave's note name and its live cents error. Mirrors
   shared/strobe-disc.js's ring state (confident/smoothedCents) every
   tick rather than tracking anything of its own — see updateDiscExtras.
   Built once per disc (cached alongside it in discCache) since the ring
   list for a given note never changes.
   ============================================================ */
function buildLegend(disc) {
  const legendEl = document.createElement("div");
  legendEl.className = "octave-legend-disc";
  legendEl.hidden = true;

  disc.rings.forEach((ring) => {
    const row = document.createElement("div");
    row.className = "octave-legend-row";

    const noteEl = document.createElement("span");
    noteEl.className = "octave-legend-note";
    noteEl.textContent = StrobeDiscEngine.noteNameForMidi(ring.midi);

    const centsEl = document.createElement("span");
    centsEl.className = "octave-legend-cents";
    centsEl.textContent = "—";

    row.appendChild(noteEl);
    row.appendChild(centsEl);
    legendEl.appendChild(row);

    // Stashed directly on the ring object: it's already the single source
    // of truth for this octave's live state, so the legend row just reads
    // off it every tick instead of keeping its own parallel lookup.
    ring.legendRowEl = row;
    ring.legendCentsEl = centsEl;
  });

  return legendEl;
}

// Mirrors every ring's confidence/tuning/fundamental state onto its
// legend row and (for the fundamental ring only) onto the wedge itself —
// called every pitch-check tick while a disc is active.
function updateDiscExtras(disc) {
  disc.rings.forEach((ring) => {
    const isFundamental = state.fundamentalMidi === ring.midi;
    const isInTune = ring.confident && Math.abs(ring.smoothedCents) <= StrobeDiscEngine.IN_TUNE_THRESHOLD_CENTS;

    ring.ringGroupEl.classList.toggle("is-fundamental", isFundamental);
    ring.legendRowEl.classList.toggle("is-active", ring.confident);
    ring.legendRowEl.classList.toggle("is-in-tune", isInTune);
    ring.legendRowEl.classList.toggle("is-fundamental", isFundamental);

    if (ring.confident) {
      const rounded = Math.round(ring.smoothedCents);
      const sign = rounded > 0 ? "+" : "";
      ring.legendCentsEl.textContent = `${sign}${rounded}¢`;
    } else {
      ring.legendCentsEl.textContent = "—";
    }
  });
}

function resetDiscExtras(disc) {
  disc.rings.forEach((ring) => {
    ring.ringGroupEl.classList.remove("is-fundamental");
    ring.legendRowEl.classList.remove("is-active", "is-in-tune", "is-fundamental");
    ring.legendCentsEl.textContent = "—";
  });
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
    addScaleTicks(disc);
    disc.legendEl = buildLegend(disc);
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
    activeDisc.legendEl.hidden = true;
  }

  if (!disc.el.isConnected) {
    discContainer.appendChild(disc.el);
  }

  if (!disc.legendEl.isConnected) {
    octaveLegendEl.appendChild(disc.legendEl);
  }

  disc.el.hidden = false;
  disc.legendEl.hidden = false;
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
  state.fundamentalMidi = null;

  if (activeDisc) {
    StrobeDiscEngine.resetDisc(activeDisc);
    resetDiscExtras(activeDisc);
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
    // discs: each ring independently decides whether it's hearing its
    // own exact target frequency, regardless of which note
    // autocorrelation currently thinks is predominant. fundamentalMidi
    // (from autocorrelation) only picks which ring gets the "best guess"
    // highlight in updateDiscExtras.
    if (state.hasSignal && state.currentNoteName) {
      const disc = setActiveDisc(state.currentNoteName, sampleRate);
      StrobeDiscEngine.analyzeDisc(disc, timeDomainBuffer, sampleRate, now);
      updateDiscExtras(disc);
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
