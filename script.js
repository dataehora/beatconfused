const bpmInput = document.getElementById("bpmInput");
const bpmRange = document.getElementById("bpmRange");
const decreaseBtn = document.getElementById("decreaseBtn");
const increaseBtn = document.getElementById("increaseBtn");
const tapBtn = document.getElementById("tapBtn");
const tapStatus = document.getElementById("tapStatus");
const toggleBtn = document.getElementById("toggleBtn");
const pulse = document.getElementById("pulse");
const numberDisplay = document.getElementById("numberDisplay");
const pendulum = document.getElementById("pendulum");
const beatLabel = document.getElementById("beatLabel");
const beatIndicators = document.getElementById("beatIndicators");
const timeSignatureInputs = document.querySelectorAll('input[name="timeSignature"]');
const subdivisionSelect = document.getElementById("subdivisionSelect");
const visualModeSelect = document.getElementById("visualMode");
const countDisplaySelect = document.getElementById("countDisplay");
const soundStyleSelect = document.getElementById("soundStyle");
const soundToggle = document.getElementById("soundToggle");
const vibrationToggle = document.getElementById("vibrationToggle");
const vibrationStatus = document.getElementById("vibrationStatus");
const volumeInput = document.getElementById("volume");
const metronomeSection = document.querySelector(".metronome");

let audioContext;
let timerId;
let noiseBuffer;
let tapTimes = [];

const state = {
  isPlaying: false,
  bpm: 120,
  beatsPerMeasure: 4,
  timeSignatureLabel: "4/4",
  subdivision: 1,
  currentBeat: 0,
  currentSubdivisionStep: 0,
  currentMeasure: 1,
  totalPulseCount: 0,
};

const CLICK_DURATION_SEC = 0.05;
const MIN_GAIN = 0.001;
const MEASURE_VIBRATION_MS = 35;
const BEAT_VIBRATION_MS = 20;
const PULSE_ANIMATION_DURATION_MS = 120;
const MS_PER_SECOND = 1000;
const MAX_TAP_WINDOW_MS = 2500;
const MAX_STORED_TAPS = 2;
const MAX_SUBDIVISION = 16;
const MIN_BPM = 40;
const MAX_BPM = 240;
const IOS_DEVICE_REGEX = /iPhone|iPad|iPod/i;

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

function getSelectedTimeSignatureInput() {
  return document.querySelector('input[name="timeSignature"]:checked');
}

function getSubdivision() {
  return clamp(Number(subdivisionSelect.value) || 1, 1, MAX_SUBDIVISION);
}

function getCountMode() {
  return countDisplaySelect.value;
}

function isVibrationSupported() {
  return typeof navigator.vibrate === "function";
}

function setTapMessage(message) {
  tapStatus.textContent = message;
}

function syncTimeSignature() {
  const selectedInput = getSelectedTimeSignatureInput();
  state.beatsPerMeasure = clamp(Number(selectedInput?.dataset.beats) || 4, 1, 16);
  state.timeSignatureLabel = selectedInput?.value || "4/4";
  state.currentBeat = 0;
  state.currentSubdivisionStep = 0;
  state.currentMeasure = 1;
  renderBeatIndicators();
  updateBeatLabel();
}

function updateTempo(value) {
  state.bpm = clamp(Number(value) || 120, MIN_BPM, MAX_BPM);
  bpmInput.value = String(state.bpm);
  bpmRange.value = String(state.bpm);

  if (state.isPlaying) {
    restartTimer();
  }
}

function renderBeatIndicators() {
  beatIndicators.innerHTML = "";

  for (let index = 0; index < state.beatsPerMeasure; index += 1) {
    const dot = document.createElement("span");
    dot.className = "beat-dot";

    if (index === 0) {
      dot.classList.add("accent");
    }

    if (index === state.currentBeat) {
      dot.classList.add("active");
    }

    beatIndicators.appendChild(dot);
  }
}

function updateBeatLabel() {
  const countMode = getCountMode();

  if (countMode === "off") {
    beatLabel.classList.add("is-hidden");
    return;
  }

  beatLabel.classList.remove("is-hidden");

  const beatNumber = state.currentBeat + 1;
  const subdivisionNumber = state.currentSubdivisionStep + 1;
  const subdivisionText = state.subdivision > 1
    ? ` · Sub ${subdivisionNumber}/${state.subdivision}`
    : "";

  if (countMode === "measure") {
    beatLabel.textContent = `Measure ${state.currentMeasure} · Beat ${beatNumber}${subdivisionText}`;
    return;
  }

  beatLabel.textContent = `Beat ${beatNumber}${subdivisionText}`;
}

function ensureAudioContext() {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
  }

  if (audioContext.state === "suspended") {
    audioContext.resume().catch(() => {});
  }

  if (!noiseBuffer) {
    const bufferSize = audioContext.sampleRate * 0.1;
    noiseBuffer = audioContext.createBuffer(1, bufferSize, audioContext.sampleRate);
    const channelData = noiseBuffer.getChannelData(0);

    for (let index = 0; index < bufferSize; index += 1) {
      channelData[index] = Math.random() * 2 - 1;
    }
  }
}

function createGainNode(volume, now, duration, decayTarget = MIN_GAIN) {
  const gainNode = audioContext.createGain();
  gainNode.gain.setValueAtTime(volume, now);
  gainNode.gain.exponentialRampToValueAtTime(decayTarget, now + duration);
  gainNode.connect(audioContext.destination);
  return gainNode;
}

function playOscillator({ type, frequency, volume, duration, highPassFrequency }) {
  const now = audioContext.currentTime;
  const oscillator = audioContext.createOscillator();
  const gainNode = createGainNode(volume, now, duration);

  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, now);

  if (highPassFrequency) {
    const filter = audioContext.createBiquadFilter();
    filter.type = "highpass";
    filter.frequency.setValueAtTime(highPassFrequency, now);
    oscillator.connect(filter);
    filter.connect(gainNode);
  } else {
    oscillator.connect(gainNode);
  }

  oscillator.start(now);
  oscillator.stop(now + duration);
}

function playCowbell(volume, isAccent) {
  const now = audioContext.currentTime;
  const gainNode = createGainNode(volume, now, 0.08);

  [540, 845].forEach((frequency) => {
    const oscillator = audioContext.createOscillator();
    oscillator.type = "square";
    oscillator.frequency.setValueAtTime(isAccent ? frequency * 1.08 : frequency, now);
    oscillator.connect(gainNode);
    oscillator.start(now);
    oscillator.stop(now + 0.08);
  });
}

function playCymbal(volume, isAccent) {
  const now = audioContext.currentTime;
  const source = audioContext.createBufferSource();
  const filter = audioContext.createBiquadFilter();
  const gainNode = createGainNode(volume, now, isAccent ? 0.09 : 0.05);

  source.buffer = noiseBuffer;
  filter.type = "bandpass";
  filter.frequency.setValueAtTime(isAccent ? 8800 : 7200, now);
  filter.Q.setValueAtTime(0.9, now);

  source.connect(filter);
  filter.connect(gainNode);
  source.start(now);
  source.stop(now + 0.09);
}

function playSound(pulseType) {
  if (!soundToggle.checked) {
    return;
  }

  ensureAudioContext();

  const volume = Number(volumeInput.value);
  const isAccent = pulseType === "measure";
  const isSubdivision = pulseType === "subdivision";
  const style = soundStyleSelect.value;
  const level = isAccent ? 1 : isSubdivision ? 0.45 : 0.7;
  const adjustedVolume = Math.max(volume * level, MIN_GAIN);

  switch (style) {
    case "wood":
      playOscillator({
        type: "triangle",
        frequency: isAccent ? 980 : isSubdivision ? 520 : 740,
        volume: adjustedVolume,
        duration: CLICK_DURATION_SEC,
      });
      break;
    case "jazz":
      playOscillator({
        type: "sine",
        frequency: isAccent ? 1120 : isSubdivision ? 640 : 860,
        volume: adjustedVolume,
        duration: 0.06,
      });
      break;
    case "bossa":
      playOscillator({
        type: "triangle",
        frequency: isAccent ? 920 : isSubdivision ? 460 : 700,
        volume: adjustedVolume,
        duration: 0.055,
      });
      break;
    case "cymbal":
      playCymbal(adjustedVolume, isAccent);
      break;
    case "cowbell":
      playCowbell(adjustedVolume, isAccent);
      break;
    case "electronic":
    default:
      playOscillator({
        type: "square",
        frequency: isAccent ? 1320 : isSubdivision ? 620 : 920,
        volume: adjustedVolume,
        duration: CLICK_DURATION_SEC,
        highPassFrequency: 240,
      });
      break;
  }
}

function updateVibrationUI() {
  const supported = isVibrationSupported();
  vibrationToggle.disabled = !supported;

  if (!supported) {
    vibrationToggle.checked = false;
    vibrationStatus.textContent = IOS_DEVICE_REGEX.test(navigator.userAgent)
      ? "Vibration is unavailable on iOS browsers because they do not expose the web vibration API."
      : "Vibration is unavailable in this browser. Audio and visual beat cues still work normally.";
    return;
  }

  vibrationStatus.textContent = "Vibration is supported on this browser after a touch or click interaction.";
}

function triggerVibration(pulseType) {
  if (!vibrationToggle.checked || !isVibrationSupported()) {
    return;
  }

  if (pulseType === "measure") {
    navigator.vibrate(MEASURE_VIBRATION_MS);
    return;
  }

  if (pulseType === "beat") {
    navigator.vibrate(BEAT_VIBRATION_MS);
  }
}

function pulseVisual(pulseType) {
  pulse.classList.remove("accent");
  pulse.classList.add("active");

  if (pulseType === "measure") {
    pulse.classList.add("accent");
  }

  window.setTimeout(() => {
    pulse.classList.remove("active", "accent");
  }, PULSE_ANIMATION_DURATION_MS);
}

function numberVisual(pulseType) {
  numberDisplay.classList.remove("active", "accent");
  numberDisplay.textContent = String(state.currentBeat + 1);

  // Force reflow so the number animation restarts on every pulse.
  void numberDisplay.offsetWidth;
  numberDisplay.classList.add("active");

  if (pulseType === "measure") {
    numberDisplay.classList.add("accent");
  }

  window.setTimeout(() => {
    numberDisplay.classList.remove("active", "accent");
  }, PULSE_ANIMATION_DURATION_MS);
}

function pendulumVisual(pulseType) {
  const direction = state.totalPulseCount % 2 === 0 ? -1 : 1;
  const angle = direction * 26;
  const offset = direction * 45;

  pendulum.classList.toggle("accent", pulseType === "measure");
  pendulum.style.setProperty("--swing-angle", `${angle}deg`);
  pendulum.style.setProperty("--swing-offset", `${offset}px`);
}

function runVisuals(pulseType) {
  pulseVisual(pulseType);
  numberVisual(pulseType);
  pendulumVisual(pulseType);
}

function getPulseType() {
  if (state.currentSubdivisionStep > 0) {
    return "subdivision";
  }

  return state.currentBeat === 0 ? "measure" : "beat";
}

function advanceCounters() {
  state.currentSubdivisionStep += 1;

  if (state.currentSubdivisionStep < state.subdivision) {
    return;
  }

  state.currentSubdivisionStep = 0;
  state.currentBeat += 1;

  if (state.currentBeat < state.beatsPerMeasure) {
    return;
  }

  state.currentBeat = 0;
  state.currentMeasure += 1;
}

function tick() {
  const pulseType = getPulseType();
  updateBeatLabel();
  playSound(pulseType);
  triggerVibration(pulseType);
  runVisuals(pulseType);
  renderBeatIndicators();

  state.totalPulseCount += 1;
  advanceCounters();
}

function getIntervalMs() {
  return (60 / (state.bpm * state.subdivision)) * MS_PER_SECOND;
}

function startTimer() {
  tick();
  timerId = window.setInterval(tick, getIntervalMs());
}

function stopTimer() {
  window.clearInterval(timerId);
  timerId = undefined;
}

function restartTimer() {
  stopTimer();
  startTimer();
}

function startMetronome() {
  if (state.isPlaying) {
    return;
  }

  ensureAudioContext();
  state.isPlaying = true;
  state.currentBeat = 0;
  state.currentSubdivisionStep = 0;
  state.currentMeasure = 1;
  state.totalPulseCount = 0;
  toggleBtn.textContent = "Stop";
  toggleBtn.setAttribute("aria-pressed", "true");
  startTimer();
}

function stopMetronome() {
  if (!state.isPlaying) {
    return;
  }

  state.isPlaying = false;
  toggleBtn.textContent = "Start";
  toggleBtn.setAttribute("aria-pressed", "false");
  stopTimer();
  state.currentBeat = 0;
  state.currentSubdivisionStep = 0;
  state.currentMeasure = 1;
  state.totalPulseCount = 0;
  updateBeatLabel();
  renderBeatIndicators();
  pulse.classList.remove("active", "accent");
  numberDisplay.classList.remove("active", "accent");
  pendulum.classList.remove("accent");
}

function toggleMetronome() {
  if (state.isPlaying) {
    stopMetronome();
  } else {
    startMetronome();
  }
}

function handleTapTempo() {
  ensureAudioContext();

  const now = performance.now();
  const previousTap = tapTimes[tapTimes.length - 1];

  if (previousTap && now - previousTap > MAX_TAP_WINDOW_MS) {
    tapTimes = [];
  }

  tapTimes.push(now);

  if (tapTimes.length > MAX_STORED_TAPS) {
    tapTimes.shift();
  }

  pulseVisual("beat");
  numberVisual("beat");
  pendulumVisual("beat");

  if (tapTimes.length < 2) {
    setTapMessage("Tap again to calculate BPM.");
    return;
  }

  const latestInterval = tapTimes[1] - tapTimes[0];
  const tappedBpm = clamp(Math.round(60000 / latestInterval), MIN_BPM, MAX_BPM);

  updateTempo(tappedBpm);
  setTapMessage(`Tap tempo: ${tappedBpm} BPM from last 2 taps.`);
}

function setVisualMode() {
  const mode = visualModeSelect.value;
  const visualElementsByMode = {
    pulse: pulse,
    numbers: numberDisplay,
    pendulum: pendulum,
  };

  metronomeSection.dataset.visualMode = mode;

  Object.entries(visualElementsByMode).forEach(([visualMode, element]) => {
    element.hidden = visualMode !== mode;
  });
}

function handleSubdivisionChange() {
  state.subdivision = getSubdivision();
  state.currentSubdivisionStep = 0;
  updateBeatLabel();

  if (state.isPlaying) {
    restartTimer();
  }
}

function handleCountModeChange() {
  updateBeatLabel();
}

bpmInput.addEventListener("input", (event) => updateTempo(event.target.value));
bpmRange.addEventListener("input", (event) => updateTempo(event.target.value));

increaseBtn.addEventListener("click", () => updateTempo(state.bpm + 5));
decreaseBtn.addEventListener("click", () => updateTempo(state.bpm - 5));
tapBtn.addEventListener("click", handleTapTempo);
toggleBtn.addEventListener("click", toggleMetronome);

timeSignatureInputs.forEach((input) => {
  input.addEventListener("change", syncTimeSignature);
});

subdivisionSelect.addEventListener("change", handleSubdivisionChange);
visualModeSelect.addEventListener("change", setVisualMode);
countDisplaySelect.addEventListener("change", handleCountModeChange);

document.addEventListener("keydown", (event) => {
  const focusedTag = document.activeElement?.tagName;
  const isFormElement = focusedTag === "INPUT" || focusedTag === "SELECT" || focusedTag === "TEXTAREA";

  if (event.code === "Space" && !isFormElement) {
    event.preventDefault();
    toggleMetronome();
  }

  if (event.key === "ArrowUp" && !isFormElement) {
    event.preventDefault();
    updateTempo(state.bpm + 5);
  }

  if (event.key === "ArrowDown" && !isFormElement) {
    event.preventDefault();
    updateTempo(state.bpm - 5);
  }

  if ((event.key === "t" || event.key === "T") && !isFormElement) {
    event.preventDefault();
    handleTapTempo();
  }
});

syncTimeSignature();
state.subdivision = getSubdivision();
setVisualMode();
updateVibrationUI();
renderBeatIndicators();
updateBeatLabel();
updateTempo(state.bpm);
