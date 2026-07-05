const bpmInput = document.getElementById("bpmInput");
const bpmRange = document.getElementById("bpmRange");
const decreaseBtn = document.getElementById("decreaseBtn");
const increaseBtn = document.getElementById("increaseBtn");
const toggleBtn = document.getElementById("toggleBtn");
const pulse = document.getElementById("pulse");
const beatLabel = document.getElementById("beatLabel");
const beatIndicators = document.getElementById("beatIndicators");
const timeSignature = document.getElementById("timeSignature");
const accentIntervalInput = document.getElementById("accentInterval");
const soundToggle = document.getElementById("soundToggle");
const vibrationToggle = document.getElementById("vibrationToggle");
const volumeInput = document.getElementById("volume");

let audioContext;
let timerId;
let isPlaying = false;
let bpm = 120;
let beatsPerMeasure = 4;
let currentBeat = 0;

const CLICK_DURATION_SEC = 0.05;
const MIN_GAIN = 0.001;
const ACCENT_VIBRATION_MS = 35;
const REGULAR_VIBRATION_MS = 20;
const PULSE_ANIMATION_DURATION_MS = 110;
const MS_PER_SECOND = 1000;

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

function getAccentInterval() {
  return clamp(Number(accentIntervalInput.value) || 1, 1, 12);
}

function updateTempo(value) {
  bpm = clamp(Number(value) || 120, 40, 240);
  bpmInput.value = String(bpm);
  bpmRange.value = String(bpm);

  if (isPlaying) {
    stopTimer();
    startTimer();
  }
}

function renderBeatIndicators() {
  beatIndicators.innerHTML = "";
  const accentEvery = getAccentInterval();

  for (let i = 0; i < beatsPerMeasure; i += 1) {
    const dot = document.createElement("span");
    dot.className = "beat-dot";

    if (i % accentEvery === 0) {
      dot.classList.add("accent");
    }

    if (i === currentBeat) {
      dot.classList.add("active");
    }

    beatIndicators.appendChild(dot);
  }
}

function ensureAudioContext() {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
  }

  if (audioContext.state === "suspended") {
    audioContext.resume().catch(() => {});
  }
}

function playClick(isAccent) {
  if (!soundToggle.checked) {
    return;
  }

  ensureAudioContext();

  const now = audioContext.currentTime;
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();

  oscillator.type = "triangle";
  oscillator.frequency.value = isAccent ? 1250 : 880;

  const volume = Number(volumeInput.value);
  gainNode.gain.setValueAtTime(volume, now);
  gainNode.gain.exponentialRampToValueAtTime(MIN_GAIN, now + CLICK_DURATION_SEC);

  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);

  oscillator.start(now);
  oscillator.stop(now + CLICK_DURATION_SEC);
}

function triggerVibration(isAccent) {
  if (!vibrationToggle.checked || !navigator.vibrate) {
    return;
  }

  navigator.vibrate(isAccent ? ACCENT_VIBRATION_MS : REGULAR_VIBRATION_MS);
}

function pulseVisual(isAccent) {
  pulse.classList.remove("accent");
  pulse.classList.add("active");

  if (isAccent) {
    pulse.classList.add("accent");
  }

  setTimeout(() => {
    pulse.classList.remove("active", "accent");
  }, PULSE_ANIMATION_DURATION_MS);
}

function tick() {
  const accentEvery = getAccentInterval();
  const isAccent = currentBeat % accentEvery === 0;

  beatLabel.textContent = `Beat ${currentBeat + 1}`;
  playClick(isAccent);
  triggerVibration(isAccent);
  pulseVisual(isAccent);
  renderBeatIndicators();

  currentBeat = (currentBeat + 1) % beatsPerMeasure;
}

function startTimer() {
  const intervalMs = (60 / bpm) * MS_PER_SECOND;
  tick();
  timerId = setInterval(tick, intervalMs);
}

function stopTimer() {
  clearInterval(timerId);
  timerId = undefined;
}

function startMetronome() {
  if (isPlaying) {
    return;
  }

  isPlaying = true;
  toggleBtn.textContent = "Stop";
  toggleBtn.setAttribute("aria-pressed", "true");
  currentBeat = 0;
  startTimer();
}

function stopMetronome() {
  if (!isPlaying) {
    return;
  }

  isPlaying = false;
  toggleBtn.textContent = "Start";
  toggleBtn.setAttribute("aria-pressed", "false");
  stopTimer();
  currentBeat = 0;
  beatLabel.textContent = "Beat 1";
  renderBeatIndicators();
}

function toggleMetronome() {
  if (isPlaying) {
    stopMetronome();
  } else {
    startMetronome();
  }
}

bpmInput.addEventListener("input", (event) => updateTempo(event.target.value));
bpmRange.addEventListener("input", (event) => updateTempo(event.target.value));

increaseBtn.addEventListener("click", () => updateTempo(bpm + 5));
decreaseBtn.addEventListener("click", () => updateTempo(bpm - 5));

toggleBtn.addEventListener("click", toggleMetronome);

timeSignature.addEventListener("change", (event) => {
  beatsPerMeasure = clamp(Number(event.target.value) || 4, 1, 12);
  currentBeat = 0;
  renderBeatIndicators();
});

accentIntervalInput.addEventListener("input", () => {
  accentIntervalInput.value = String(getAccentInterval());
  renderBeatIndicators();
});

document.addEventListener("keydown", (event) => {
  const focusedTag = document.activeElement?.tagName;
  if (focusedTag === "INPUT" || focusedTag === "SELECT") {
    return;
  }

  if (event.code === "Space") {
    event.preventDefault();
    toggleMetronome();
  }

  if (event.key === "ArrowUp") {
    event.preventDefault();
    updateTempo(bpm + 5);
  }

  if (event.key === "ArrowDown") {
    event.preventDefault();
    updateTempo(bpm - 5);
  }
});

renderBeatIndicators();
updateTempo(120);
