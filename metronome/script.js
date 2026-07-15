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
const pendulumSwing = pendulum.querySelector(".pendulum-swing");
const beatLabel = document.getElementById("beatLabel");
const beatIndicators = document.getElementById("beatIndicators");
const timeSignatureSelect = document.getElementById("timeSignature");
const subdivisionInputs = document.querySelectorAll('input[name="subdivision"]');
const visualModeInputs = document.querySelectorAll('input[name="visualMode"]');
const countModeInputs = document.querySelectorAll('input[name="countMode"]');
const soundStyleSelect = document.getElementById("soundStyle");
const soundToggle = document.getElementById("soundToggle");
const vibrationToggle = document.getElementById("vibrationToggle");
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
const UPDATE_CHECK_INTERVAL_MS = 10000;
const UPDATE_CHECK_RESOURCES = [window.location.pathname, "styles.css", "script.js"];
const PENDULUM_MIN_AMPLITUDE_DEG = 10;
const PENDULUM_MAX_AMPLITUDE_DEG = 17;
// pivots near the base (like the escapement in a real metronome), rod swings
// above it — offsets below are relative to that, positive = toward the pivot
const PENDULUM_PIVOT_X = 120;
const PENDULUM_PIVOT_Y = 246;
const PENDULUM_WEIGHT_MIN_OFFSET_PX = 56;
const PENDULUM_WEIGHT_MAX_OFFSET_PX = -8;
const PENDULUM_PREVIEW_RETURN_MS = 240;

const deployedVersionTokens = new Map();
let pendingReloadForUpdate = false;
let pendingReloadVersionToken;
let pendulumAnimationFrameId;
let pendulumTweenFrameId;
let pendulumPreviewTimeoutId;
let pendulumTickTimeoutId;
let pendulumPreviewDirection = -1;
let pendulumCurrentAngle = 0;

const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

function getSelectedTimeSignatureOption() {
  return timeSignatureSelect.selectedOptions[0];
}

function getSubdivision() {
  const checked = document.querySelector('input[name="subdivision"]:checked');
  return clamp(Number(checked?.value) || 1, 1, MAX_SUBDIVISION);
}

function getCountMode() {
  return document.querySelector('input[name="countMode"]:checked')?.value || "beat";
}

function isVibrationSupported() {
  return typeof navigator.vibrate === "function";
}

function setTapMessage(message) {
  tapStatus.textContent = message;
}

function buildUpdateCheckUrl(resource) {
  const url = new URL(resource, window.location.href);
  url.searchParams.set("__update_check", String(Date.now()));
  return url.toString();
}

function getVersionToken(response) {
  return response.headers.get("etag") || response.headers.get("last-modified");
}

function getResourceKey(resource) {
  return new URL(resource, window.location.href).pathname;
}

function buildReloadUrl(versionToken) {
  const url = new URL(window.location.href);
  url.searchParams.set("__v", versionToken);
  return url.toString();
}

function reloadWithVersion(versionToken) {
  window.location.replace(buildReloadUrl(versionToken));
}

async function checkResourceForDeployedUpdate(resource) {
  const response = await fetch(buildUpdateCheckUrl(resource), {
    method: "HEAD",
    cache: "reload",
  });

  if (!response.ok) {
    return null;
  }

  const versionToken = getVersionToken(response);

  if (!versionToken) {
    return null;
  }

  const resourceKey = getResourceKey(resource);
  const previousVersionToken = deployedVersionTokens.get(resourceKey);
  deployedVersionTokens.set(resourceKey, versionToken);

  if (!previousVersionToken || previousVersionToken === versionToken) {
    return null;
  }

  return versionToken;
}

async function checkForDeployedUpdate() {
  try {
    for (const resource of UPDATE_CHECK_RESOURCES) {
      const updatedVersionToken = await checkResourceForDeployedUpdate(resource);

      if (!updatedVersionToken) {
        continue;
      }

      if (state.isPlaying) {
        pendingReloadForUpdate = true;
        pendingReloadVersionToken = updatedVersionToken;
        return;
      }

      reloadWithVersion(updatedVersionToken);
      return;
    }
  } catch (error) {
    console.warn("Update check failed:", error);
  }
}

function syncTimeSignature() {
  const selectedOption = getSelectedTimeSignatureOption();
  state.beatsPerMeasure = clamp(Number(selectedOption?.dataset.beats) || 4, 1, 16);
  state.timeSignatureLabel = selectedOption?.value || "4/4";
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
  syncPendulumPhysics();

  if (state.isPlaying) {
    restartTimer();
    startPendulumAnimation();
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
  const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;

  if (!AudioContextConstructor) {
    return false;
  }

  if (!audioContext) {
    try {
      audioContext = new AudioContextConstructor();
    } catch (_) {
      return false;
    }
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

  return true;
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

  if (!ensureAudioContext()) {
    return;
  }

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
    vibrationToggle.title = IOS_DEVICE_REGEX.test(navigator.userAgent)
      ? "Vibration is unavailable on iOS browsers because they do not expose the web vibration API."
      : "Vibration is unavailable in this browser. Audio and visual beat cues still work normally.";
    return;
  }

  vibrationToggle.title = "Vibration is supported on this browser after a touch or click interaction.";
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

function getTempoProgress() {
  return (state.bpm - MIN_BPM) / (MAX_BPM - MIN_BPM);
}

function getPendulumAmplitudeDeg() {
  const amplitudeRange = PENDULUM_MAX_AMPLITUDE_DEG - PENDULUM_MIN_AMPLITUDE_DEG;
  return PENDULUM_MAX_AMPLITUDE_DEG - (getTempoProgress() * amplitudeRange);
}

function getPendulumCarriageOffsetPx() {
  const offsetRange = PENDULUM_WEIGHT_MAX_OFFSET_PX - PENDULUM_WEIGHT_MIN_OFFSET_PX;
  return PENDULUM_WEIGHT_MAX_OFFSET_PX - (getTempoProgress() * offsetRange);
}

function getPendulumHalfCycleMs() {
  return (60 / state.bpm) * MS_PER_SECOND;
}

// Rotating the SVG group via its transform attribute (rather than a CSS
// custom property + transform-origin) sidesteps transform-box, which is
// inconsistently implemented across browsers — most notably mobile Safari,
// where it produced an erratic, off-axis swing.
function applyPendulumAngle(angle) {
  pendulumCurrentAngle = angle;
  pendulumSwing.setAttribute("transform", `rotate(${angle.toFixed(2)} ${PENDULUM_PIVOT_X} ${PENDULUM_PIVOT_Y})`);
}

function syncPendulumPhysics() {
  pendulum.style.setProperty("--pendulum-carriage-offset", `${getPendulumCarriageOffsetPx().toFixed(2)}px`);
}

// Small manual tween (used only for the idle tap-tempo preview swing) so the
// easing doesn't depend on a CSS transition running on the same attribute.
function tweenPendulumAngle(fromAngle, toAngle, durationMs, onDone) {
  if (pendulumTweenFrameId !== undefined) {
    window.cancelAnimationFrame(pendulumTweenFrameId);
  }

  const startedAt = performance.now();

  const step = (now) => {
    const t = Math.min((now - startedAt) / durationMs, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    applyPendulumAngle(fromAngle + (toAngle - fromAngle) * eased);

    if (t < 1) {
      pendulumTweenFrameId = window.requestAnimationFrame(step);
      return;
    }

    pendulumTweenFrameId = undefined;
    onDone?.();
  };

  pendulumTweenFrameId = window.requestAnimationFrame(step);
}

function stopPendulumPreview() {
  if (pendulumPreviewTimeoutId !== undefined) {
    window.clearTimeout(pendulumPreviewTimeoutId);
    pendulumPreviewTimeoutId = undefined;
  }

  if (pendulumTweenFrameId !== undefined) {
    window.cancelAnimationFrame(pendulumTweenFrameId);
    pendulumTweenFrameId = undefined;
  }
}

function flashPendulumTick(pulseType) {
  pendulum.classList.toggle("accent", pulseType === "measure");
  pendulum.classList.remove("tick");

  if (pendulumTickTimeoutId !== undefined) {
    window.clearTimeout(pendulumTickTimeoutId);
  }

  void pendulum.offsetWidth;
  pendulum.classList.add("tick");
  pendulumTickTimeoutId = window.setTimeout(() => {
    pendulum.classList.remove("tick");
    pendulumTickTimeoutId = undefined;
  }, PULSE_ANIMATION_DURATION_MS);
}

function previewPendulumSwing() {
  if (reducedMotionQuery.matches) {
    applyPendulumAngle(0);
    return;
  }

  stopPendulumPreview();
  pendulumPreviewDirection *= -1;
  const targetAngle = pendulumPreviewDirection * getPendulumAmplitudeDeg() * 0.86;

  tweenPendulumAngle(pendulumCurrentAngle, targetAngle, 150, () => {
    pendulumPreviewTimeoutId = window.setTimeout(() => {
      pendulumPreviewTimeoutId = undefined;
      tweenPendulumAngle(pendulumCurrentAngle, 0, PENDULUM_PREVIEW_RETURN_MS);
    }, 90);
  });
}

function stopPendulumAnimation() {
  if (pendulumAnimationFrameId !== undefined) {
    window.cancelAnimationFrame(pendulumAnimationFrameId);
    pendulumAnimationFrameId = undefined;
  }

  stopPendulumPreview();
  applyPendulumAngle(0);
}

function startPendulumAnimation() {
  syncPendulumPhysics();
  stopPendulumPreview();

  if (reducedMotionQuery.matches) {
    applyPendulumAngle(0);
    return;
  }

  if (pendulumAnimationFrameId !== undefined) {
    window.cancelAnimationFrame(pendulumAnimationFrameId);
  }

  const amplitude = getPendulumAmplitudeDeg();
  const halfCycleMs = getPendulumHalfCycleMs();
  const startedAt = performance.now();

  applyPendulumAngle(-amplitude);

  const animatePendulum = (now) => {
    if (!state.isPlaying) {
      pendulumAnimationFrameId = undefined;
      return;
    }

    const phase = (now - startedAt) / halfCycleMs;
    const angle = -Math.cos(phase * Math.PI) * amplitude;
    applyPendulumAngle(angle);
    pendulumAnimationFrameId = window.requestAnimationFrame(animatePendulum);
  };

  pendulumAnimationFrameId = window.requestAnimationFrame(animatePendulum);
}

function pendulumVisual(pulseType) {
  syncPendulumPhysics();
  flashPendulumTick(pulseType);

  if (!state.isPlaying) {
    previewPendulumSwing();
  }
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

  state.isPlaying = true;
  state.currentBeat = 0;
  state.currentSubdivisionStep = 0;
  state.currentMeasure = 1;
  state.totalPulseCount = 0;
  toggleBtn.textContent = "Stop";
  toggleBtn.setAttribute("aria-pressed", "true");
  startPendulumAnimation();
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
  stopPendulumAnimation();
  state.currentBeat = 0;
  state.currentSubdivisionStep = 0;
  state.currentMeasure = 1;
  state.totalPulseCount = 0;
  updateBeatLabel();
  renderBeatIndicators();
  pulse.classList.remove("active", "accent");
  numberDisplay.classList.remove("active", "accent");
  pendulum.classList.remove("accent", "tick");

  if (pendingReloadForUpdate) {
    reloadWithVersion(pendingReloadVersionToken || String(Date.now()));
  }
}

function toggleMetronome() {
  if (state.isPlaying) {
    stopMetronome();
  } else {
    startMetronome();
  }
}

function handleTapTempo() {
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
    setTapMessage("Tap again…");
    return;
  }

  const latestInterval = tapTimes[1] - tapTimes[0];
  const tappedBpm = clamp(Math.round(60000 / latestInterval), MIN_BPM, MAX_BPM);

  updateTempo(tappedBpm);
  setTapMessage(`${tappedBpm} BPM`);
}

function setVisualMode() {
  const mode = document.querySelector('input[name="visualMode"]:checked')?.value || "pendulum";
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

function handleReducedMotionPreferenceChange() {
  syncPendulumPhysics();

  if (state.isPlaying) {
    if (reducedMotionQuery.matches) {
      stopPendulumAnimation();
    } else {
      startPendulumAnimation();
    }
    return;
  }

  applyPendulumAngle(0);
}

bpmInput.addEventListener("input", (event) => updateTempo(event.target.value));
bpmRange.addEventListener("input", (event) => updateTempo(event.target.value));

increaseBtn.addEventListener("click", () => updateTempo(state.bpm + 5));
decreaseBtn.addEventListener("click", () => updateTempo(state.bpm - 5));
tapBtn.addEventListener("click", handleTapTempo);
toggleBtn.addEventListener("click", toggleMetronome);

timeSignatureSelect.addEventListener("change", syncTimeSignature);

subdivisionInputs.forEach((input) => {
  input.addEventListener("change", handleSubdivisionChange);
});

visualModeInputs.forEach((input) => {
  input.addEventListener("change", setVisualMode);
});

countModeInputs.forEach((input) => {
  input.addEventListener("change", handleCountModeChange);
});

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

if (typeof reducedMotionQuery.addEventListener === "function") {
  reducedMotionQuery.addEventListener("change", handleReducedMotionPreferenceChange);
} else if (typeof reducedMotionQuery.addListener === "function") {
  reducedMotionQuery.addListener(handleReducedMotionPreferenceChange);
}

syncTimeSignature();
state.subdivision = getSubdivision();
setVisualMode();
updateVibrationUI();
renderBeatIndicators();
updateBeatLabel();
updateTempo(state.bpm);
syncPendulumPhysics();
checkForDeployedUpdate();
window.setInterval(checkForDeployedUpdate, UPDATE_CHECK_INTERVAL_MS);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) {
    checkForDeployedUpdate();
  }
});
