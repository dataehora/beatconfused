const SVG_NS = "http://www.w3.org/2000/svg";

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

const NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];

// Where each sharp disc sits along the naturals row, expressed as which
// natural-key boundary (of 7) it floats above — e.g. C♯ sits right after C
// (boundary 1), matching a real piano keyboard's black-key spacing (no
// sharp between E-F or B-C, so F♯/G♯/A♯ pick up 2 boundaries further out).
const SHARP_BOUNDARY = { "C♯": 1, "D♯": 2, "F♯": 4, "G♯": 5, "A♯": 6 };
const NATURAL_COLUMN_COUNT = 7;

// A standard 88-key grand piano: A0 (MIDI 21) to C8 (MIDI 108) — the same
// range /tuner/'s Frequency Table uses. Every octave-instance of a pitch
// class that falls in this range gets its own ring, so C/A/A♯/B (which
// happen to land on both ends of the range) get 8 rings, everything else
// gets 7 — not a fixed count per disc.
const PIANO_MIN_MIDI = 21;
const PIANO_MAX_MIDI = 108;

const MIN_A4 = 392;
const MAX_A4 = 466;
const DEFAULT_A4 = 440;

// The analyser buffer needs to be long enough that even the lowest ring
// (A0, 27.5 Hz) gets several full cycles to analyze — see
// computeWindowSamples(). 16384 samples is ~371ms at 44.1kHz, enough for
// ~10 cycles of A0 with room to spare, while still being cheap: every ring
// only reads as many of the most recent samples as it actually needs.
const ANALYSER_BUFFER_SIZE = 16384;
// How many cycles of a ring's own target frequency its Goertzel window
// covers — more cycles means a cleaner, more frequency-selective reading
// but a longer window (so a laggier one for that specific ring). Low rings
// end up with long windows and high rings with short ones purely as a
// consequence of this staying constant while frequency varies.
const GOERTZEL_MIN_CYCLES = 6;
const MIN_RING_WINDOW_SAMPLES = 64;

const PITCH_CHECK_INTERVAL_MS = 45;
// The floor of the Input Monitor's dB scale — anything quieter reads as
// silence rather than an ever-more-negative number.
const LEVEL_FLOOR_DB = -60;
const CENTS_SMOOTHING = 0.25;
const IN_TUNE_THRESHOLD_CENTS = 1;
const MAX_UNTUNED_CENTS = 50;
const RING_DEADZONE_CENTS = 1.5;
// Degrees of rotation per cent of error, per second — a single visual-
// sensitivity constant shared by every ring (unlike /tuner/'s multi-ring
// strobe, no ring here needs to match another's rotation to "prove" an
// octave relationship; each ring is independently measured).
const RING_ROTATION_SPEED = 8;
// A Goertzel magnitude, normalized by window length, below which a ring is
// treated as "nothing playing here" rather than noise mistaken for a
// reading — the per-ring equivalent of /tuner/'s MIN_RMS gate.
const MIN_RING_MAGNITUDE = 0.006;

const state = {
  a4: DEFAULT_A4,
  activeSource: null, // null | "mic"
};

const DISCS = []; // 12 entries (NOTE_NAMES order): { name, el, rings: [...] }

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

function getTuneMixPercent(cents) {
  const abs = Math.abs(cents);

  if (abs <= IN_TUNE_THRESHOLD_CENTS) {
    return 0;
  }

  const t = (abs - IN_TUNE_THRESHOLD_CENTS) / (MAX_UNTUNED_CENTS - IN_TUNE_THRESHOLD_CENTS);
  return Math.round(clamp(t, 0, 1) * 100);
}

// Equal temperament only, at whatever A4 is currently set — this page
// doesn't (yet) carry /tuner/'s tuning-standard/key selector.
function pianoNoteFrequency(midi, a4) {
  return a4 * Math.pow(2, (midi - 69) / 12);
}

function midiListForPitchClass(pitchClassIndex) {
  const list = [];

  for (let midi = PIANO_MIN_MIDI; midi <= PIANO_MAX_MIDI; midi += 1) {
    if (((midi % 12) + 12) % 12 === pitchClassIndex) {
      list.push(midi);
    }
  }

  return list;
}

function computeWindowSamples(targetFreq, sampleRate) {
  const raw = Math.round((sampleRate * GOERTZEL_MIN_CYCLES) / targetFreq);
  return clamp(raw, MIN_RING_WINDOW_SAMPLES, ANALYSER_BUFFER_SIZE);
}

/* ============================================================
   GOERTZEL FILTER — a single-bin DFT computed as a small IIR recurrence,
   tuned to one exact target frequency rather than a quantized FFT bin.
   Cheap enough (O(window length)) to run once per ring per tick — 96 of
   these per tick is still only a few hundred thousand multiply-adds,
   trivial for a browser to run every 45ms.
   ============================================================ */
function goertzel(buffer, offset, length, targetFreq, sampleRate) {
  const w = (2 * Math.PI * targetFreq) / sampleRate;
  const coeff = 2 * Math.cos(w);
  let s1 = 0;
  let s2 = 0;

  for (let i = 0; i < length; i += 1) {
    const s0 = buffer[offset + i] + coeff * s1 - s2;
    s2 = s1;
    s1 = s0;
  }

  const real = s1 - s2 * Math.cos(w);
  const imag = s2 * Math.sin(w);
  return { magnitude: Math.hypot(real, imag), phase: Math.atan2(imag, real) };
}

// Turns a ring's Goertzel phase reading into a cents error by comparing it
// against the phase from its *previous* confident reading — the same idea
// a phase vocoder uses: if the real frequency exactly matches the target,
// phase advances by exactly 2π × targetFreq × elapsedSeconds between the
// two readings; any residual beyond that is the frequency error. `now`
// must be audioContext.currentTime (seconds), NOT performance.now() — the
// audio clock is sample-accurate and immune to JS-thread scheduling
// jitter, which otherwise shows up as a small but very real systematic
// bias (confirmed by feeding this an exact 440Hz test tone and watching it
// settle a few cents flat when timestamped with performance.now() instead).
// Mutates `ring` in place (previousPhase/previousTimestamp/hasPhase/
// confident/smoothedCents).
function analyzeRing(ring, buffer, sampleRate, now) {
  const offset = buffer.length - ring.windowSamples;
  const { magnitude, phase } = goertzel(buffer, offset, ring.windowSamples, ring.targetFreq, sampleRate);
  const normalizedMagnitude = magnitude / ring.windowSamples;

  if (normalizedMagnitude < MIN_RING_MAGNITUDE) {
    ring.confident = false;
    ring.hasPhase = false;
    return;
  }

  if (ring.hasPhase) {
    const elapsedSeconds = now - ring.previousTimestamp;

    if (elapsedSeconds > 0) {
      const expectedAdvance = 2 * Math.PI * ring.targetFreq * elapsedSeconds;
      const rawDiff = phase - ring.previousPhase;
      // Unwraps rawDiff (which atan2 only ever gives in a single -π..π
      // turn) to whichever full-turn-adjusted value sits closest to what
      // a perfectly-in-tune signal would have produced.
      const wraps = Math.round((expectedAdvance - rawDiff) / (2 * Math.PI));
      const actualAdvance = rawDiff + wraps * 2 * Math.PI;
      const freqError = (actualAdvance - expectedAdvance) / (2 * Math.PI * elapsedSeconds);
      const cents = 1200 * Math.log2(1 + freqError / ring.targetFreq);
      ring.smoothedCents += (cents - ring.smoothedCents) * CENTS_SMOOTHING;
      ring.confident = true;
    }
  } else {
    // First confident tick after silence — nothing to compare this phase
    // against yet, so this tick only establishes a baseline.
    ring.confident = false;
  }

  ring.previousPhase = phase;
  ring.previousTimestamp = now;
  ring.hasPhase = true;
}

/* ============================================================
   DISC GRAPHICS — each disc shows only the top 90° of its wheel (not a
   full circle, not /tuner/'s half-circle either) — the rest is never
   visible so there's no reason to spend layout space or DOM nodes on it.
   Holds one concentric ring per real octave-instance of that note in the
   88-key range, outermost = lowest octave, innermost = highest — same
   outer-to-inner convention as /tuner/'s original 5-ring strobe. Segment
   count doubles ring by ring outward from the center (2, 4, 8, … up to
   256 on an 8-ring disc) — the same fan pattern a real optical strobe
   disc uses, most visible at the hub where a couple of wide wedges span
   most of the arc, finest at the outer edge.
   ============================================================ */
function polarPoint(cx, cy, r, angleDeg) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.sin(rad), y: cy - r * Math.cos(rad) };
}

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

// A filled pie wedge from the center out to the arc — used for the case
// and window backgrounds (unlike annulusWedgePath, which is a ring
// between two radii).
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

// Segment counts are defined relative to a full 360° wheel (segmentCount
// filled wedges alternating with segmentCount gaps, same convention
// /tuner/'s strobe uses) — this only builds whichever of those wedges
// actually fall inside the visible arcSpanDeg window at the top, clipping
// (not dropping) the ones straddling its edges. Slices are centered on
// multiples of one step from top-center (angle 0), rather than starting a
// step there, so the window stays bilaterally symmetric — most visible
// on the innermost 2-segment ring, where the whole 90° window is exactly
// one centered wedge instead of being split awkwardly across a boundary.
function buildArcRingWedges(groupEl, cx, cy, innerR, outerR, segmentCount, arcSpanDeg) {
  const totalSlices = segmentCount * 2;
  const step = 360 / totalSlices;
  const halfArc = arcSpanDeg / 2;
  const maxJ = Math.ceil(halfArc / step) + 1;

  for (let j = -maxJ; j <= maxJ; j += 1) {
    const isFilled = (((j % 2) + 2) % 2) === 0;

    if (!isFilled) {
      continue;
    }

    const sliceStart = (j - 0.5) * step;
    const sliceEnd = (j + 0.5) * step;
    const clippedStart = Math.max(sliceStart, -halfArc);
    const clippedEnd = Math.min(sliceEnd, halfArc);

    if (clippedEnd <= clippedStart) {
      continue;
    }

    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", annulusWedgePath(cx, cy, innerR, outerR, clippedStart, clippedEnd));
    groupEl.appendChild(path);
  }
}

// The disc's pivot sits near the bottom of its own viewBox (not the
// center of a square one) since only the top 90° arc above it is ever
// drawn — a viewBox this much shorter than it is wide is exactly what
// buys back the vertical space full circles were wasting on their
// invisible bottom three-quarters.
const DISC_CX = 50;
const DISC_CY = 52;
const DISC_ARC_SPAN = 90;
const DISC_VIEWBOX = "0 0 100 56";
const DISC_CASE_R = 48;
const DISC_WINDOW_R = 42;
const DISC_RING_OUTER_R = 39;
const DISC_HUB_R = 5;

function buildDisc(name, isSharp) {
  const midiList = midiListForPitchClass(NOTE_NAMES.indexOf(name));

  const wrapper = document.createElement("div");
  wrapper.className = "strobe-disc";

  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", DISC_VIEWBOX);
  svg.setAttribute("class", "disc-device");
  svg.setAttribute("role", "presentation");
  svg.setAttribute("focusable", "false");

  const halfSpan = DISC_ARC_SPAN / 2;

  const caseShape = document.createElementNS(SVG_NS, "path");
  caseShape.setAttribute("class", "disc-case");
  caseShape.setAttribute("d", sectorPath(DISC_CX, DISC_CY, DISC_CASE_R, -halfSpan, halfSpan));
  svg.appendChild(caseShape);

  const windowShape = document.createElementNS(SVG_NS, "path");
  windowShape.setAttribute("class", "disc-window");
  windowShape.setAttribute("d", sectorPath(DISC_CX, DISC_CY, DISC_WINDOW_R, -halfSpan, halfSpan));
  svg.appendChild(windowShape);

  const totalRings = midiList.length;
  const ringGap = 0.6;
  const availableBand = DISC_RING_OUTER_R - DISC_HUB_R - ringGap * (totalRings - 1);
  const bandWidth = availableBand / totalRings;

  const rings = midiList.map((midi, index) => {
    const outerR = DISC_RING_OUTER_R - index * (bandWidth + ringGap);
    const innerR = outerR - bandWidth;
    // `index` counts inward from the outermost ring (index 0), but segment
    // count needs to count outward from the center: innermost ring = 2
    // segments, doubling ring by ring out to the outermost.
    const positionFromCenter = totalRings - 1 - index;
    const segmentCount = Math.pow(2, positionFromCenter + 1);

    const ringGroup = document.createElementNS(SVG_NS, "g");
    ringGroup.setAttribute("class", "disc-ring");
    buildArcRingWedges(ringGroup, DISC_CX, DISC_CY, innerR, outerR, segmentCount, DISC_ARC_SPAN);
    svg.appendChild(ringGroup);

    return {
      midi,
      targetFreq: 0,
      windowSamples: 0,
      angle: 0,
      previousPhase: 0,
      previousTimestamp: 0,
      hasPhase: false,
      confident: false,
      smoothedCents: 0,
      ringGroupEl: ringGroup,
    };
  });

  const hub = document.createElementNS(SVG_NS, "circle");
  hub.setAttribute("class", "disc-hub");
  hub.setAttribute("cx", String(DISC_CX));
  hub.setAttribute("cy", String(DISC_CY));
  hub.setAttribute("r", "2.5");
  svg.appendChild(hub);

  const label = document.createElement("span");
  label.className = "disc-label";
  label.textContent = name;

  wrapper.appendChild(svg);
  wrapper.appendChild(label);

  if (isSharp) {
    wrapper.style.left = `${(SHARP_BOUNDARY[name] / NATURAL_COLUMN_COUNT) * 100}%`;
  }

  return { name, el: wrapper, rings };
}

function buildDiscs() {
  NOTE_NAMES.forEach((name) => {
    const isSharp = name.includes("♯");
    const disc = buildDisc(name, isSharp);
    DISCS.push(disc);
    (isSharp ? sharpsContainer : naturalsContainer).appendChild(disc.el);
  });
}

// Recomputes every ring's target frequency (and the analysis window that
// depends on it) from the current A4 — called at load and whenever the
// reference pitch changes. Any in-flight phase-tracking history is
// discarded rather than compared against the new target, since it was
// measuring against a now-stale frequency.
function recomputeRingTargets() {
  const sampleRate = audioContext ? audioContext.sampleRate : 44100;

  DISCS.forEach((disc) => {
    disc.rings.forEach((ring) => {
      ring.targetFreq = pianoNoteFrequency(ring.midi, state.a4);
      ring.windowSamples = computeWindowSamples(ring.targetFreq, sampleRate);
      ring.hasPhase = false;
      ring.confident = false;
    });
  });
}

/* ============================================================
   RENDERING — every ring independently decides, every frame, whether it
   has a confident reading: idle rings sit dim and motionless (distinct
   from — never confusable with — the green "in tune" state), active ones
   spin according to their own measured cents error.
   ============================================================ */
function renderDiscs(dt) {
  DISCS.forEach((disc) => {
    let discHasActiveRing = false;
    let discHasInTuneRing = false;

    disc.rings.forEach((ring) => {
      const isActive = ring.confident;
      ring.ringGroupEl.classList.toggle("is-active", isActive);

      if (!isActive) {
        ring.ringGroupEl.classList.remove("in-tune");
        ring.angle = 0;
        ring.ringGroupEl.setAttribute("transform", `rotate(0 ${DISC_CX} ${DISC_CY})`);
        return;
      }

      discHasActiveRing = true;
      const rawCents = ring.smoothedCents;
      const effectiveCents = Math.abs(rawCents) < RING_DEADZONE_CENTS ? 0 : rawCents;
      const inTune = Math.abs(rawCents) <= IN_TUNE_THRESHOLD_CENTS;

      if (inTune) {
        discHasInTuneRing = true;
      }

      ring.ringGroupEl.classList.toggle("in-tune", inTune);
      ring.ringGroupEl.style.setProperty("--tune-mix", String(getTuneMixPercent(rawCents)));
      ring.angle = (ring.angle + effectiveCents * RING_ROTATION_SPEED * dt) % 360;
      ring.ringGroupEl.setAttribute("transform", `rotate(${ring.angle.toFixed(2)} ${DISC_CX} ${DISC_CY})`);
    });

    disc.el.classList.toggle("is-active", discHasActiveRing);
    disc.el.classList.toggle("in-tune", discHasInTuneRing);
  });
}

function resetVisuals() {
  DISCS.forEach((disc) => {
    disc.el.classList.remove("is-active", "in-tune");

    disc.rings.forEach((ring) => {
      ring.angle = 0;
      ring.hasPhase = false;
      ring.confident = false;
      ring.smoothedCents = 0;
      ring.ringGroupEl.classList.remove("is-active", "in-tune");
      ring.ringGroupEl.setAttribute("transform", `rotate(0 ${DISC_CX} ${DISC_CY})`);
    });
  });

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
    analyserNode.fftSize = ANALYSER_BUFFER_SIZE;
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
    // — see analyzeRing's comment for why this matters.
    const now = audioContext.currentTime;
    const sampleRate = audioContext.sampleRate;

    DISCS.forEach((disc) => {
      disc.rings.forEach((ring) => {
        analyzeRing(ring, timeDomainBuffer, sampleRate, now);
      });
    });
  }

  renderDiscs(dt);
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
