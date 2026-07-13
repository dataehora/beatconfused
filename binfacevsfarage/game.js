const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const healthLeft = document.getElementById("healthLeft");
const healthRight = document.getElementById("healthRight");
const timerEl = document.getElementById("timer");
const overlay = document.getElementById("overlay");
const overlayKicker = document.getElementById("overlayKicker");
const overlayTitle = document.getElementById("overlayTitle");
const overlayBody = document.getElementById("overlayBody");
const primaryAction = document.getElementById("primaryAction");
const secondaryAction = document.getElementById("secondaryAction");
const announcement = document.getElementById("announcement");
const soundToggle = document.getElementById("soundToggle");

const WIDTH = canvas.width;
const HEIGHT = canvas.height;
const FLOOR_Y = 430;
const ROUND_TIME = 60;
const GRAVITY = 1800;
const MOVE_SPEED = 245;
const CPU_MOVE_SPEED = 212;
const JUMP_VELOCITY = -720;
const MAX_DT = 1 / 30;
const MIN_FIGHTER_SEPARATION = 72;
const FIGHTER_MIN_X = 58;
const FIGHTER_MAX_X = WIDTH - 58;
const COUNTDOWN_TOTAL = 3.5;
const COUNTDOWN_ROUND_MARK = 2.7;
const COUNTDOWN_THREE_MARK = 1.95;
const COUNTDOWN_TWO_MARK = 1.2;
const COUNTDOWN_ONE_MARK = 0.45;
const MUSIC_STEP_DURATION = 0.18;
const PORTRAIT_SOURCES = {
  binface: "https://commons.wikimedia.org/wiki/Special:Redirect/file/Count_Binface_(cropped)_(cropped).jpg",
  farage: "https://upload.wikimedia.org/wikipedia/commons/9/92/Official_portrait_of_Nigel_Farage_MP_%283x4_close_cropped%29.jpg",
};
const ATTACK_SOUND_MAP = {
  punch: { frequency: 430, type: "square" },
  kick: { frequency: 290, type: "square" },
  grab: { frequency: 180, type: "triangle" },
};
const ARM_REACH_BY_ATTACK = {
  punch: 28,
  kick: 14,
  grab: 34,
};
const LEG_REACH_BY_ATTACK = {
  kick: 24,
};
const MUSIC_PATTERN = [
  { bass: 131, lead: 392 },
  { bass: null, lead: 440 },
  { bass: 147, lead: 466 },
  { bass: null, lead: 440 },
  { bass: 165, lead: 523 },
  { bass: null, lead: 466 },
  { bass: 147, lead: 440 },
  { bass: null, lead: 392 },
  { bass: 131, lead: 349 },
  { bass: null, lead: 392 },
  { bass: 147, lead: 440 },
  { bass: null, lead: 392 },
  { bass: 165, lead: 523 },
  { bass: null, lead: 466 },
  { bass: 147, lead: 440 },
  { bass: null, lead: 392 },
];

const ATTACKS = {
  punch: { startup: 0.08, active: 0.12, recovery: 0.2, range: 68, damage: 8, push: 28, hitstun: 0.18 },
  kick: { startup: 0.12, active: 0.12, recovery: 0.26, range: 88, damage: 12, push: 36, hitstun: 0.23 },
  grab: { startup: 0.1, active: 0.08, recovery: 0.34, range: 48, damage: 16, push: 44, hitstun: 0.28 },
};

const CONTROL_KEYS = new Set(["arrowleft", "arrowright", "arrowup", "arrowdown", "q", "w", "e"]);

const portraits = new Map();
const state = {
  phase: "intro",
  timer: ROUND_TIME,
  countdown: 0,
  resultText: "",
  resultKicker: "",
  announcementText: "",
  announcementTimeout: 0,
  soundEnabled: true,
  lastFrame: 0,
  musicClock: 0,
  musicStep: 0,
  spokenCountdown: "",
};

const keysDown = new Set();
const keysPressed = new Set();

let audioContext;

function createPortrait(url) {
  const image = new Image();
  image.crossOrigin = "anonymous";
  image.decoding = "async";
  image.src = url;
  return image;
}

function preloadPortraits() {
  Object.entries(PORTRAIT_SOURCES).forEach(([key, url]) => {
    portraits.set(key, createPortrait(url));
  });
}

function createFighter(config) {
  return {
    name: config.name,
    title: config.title,
    x: config.x,
    y: FLOOR_Y,
    width: 68,
    height: 144,
    facing: config.facing,
    color: config.color,
    trim: config.trim,
    outline: config.outline,
    health: 100,
    velocityY: 0,
    hitstun: 0,
    invulnerable: 0,
    attack: null,
    attackCooldown: 0,
    moveDirection: 0,
    isWinner: false,
    isCpu: config.isCpu,
    portraitKey: config.portraitKey,
    portraitShape: config.portraitShape,
    portraitFocusY: config.portraitFocusY,
    controls: config.controls,
    aiAttackTimer: 0,
    aiJumpTimer: 0,
  };
}

function createBinface() {
  return createFighter({
    name: "Count Binfaux",
    title: "Player one hero",
    x: 260,
    facing: 1,
    color: "#dadfe8",
    trim: "#ffbf3c",
    outline: "#1f2433",
    isCpu: false,
    portraitKey: "binface",
    portraitShape: "rect",
    portraitFocusY: 0.16,
    controls: {
      left: "arrowleft",
      right: "arrowright",
      jump: "arrowup",
      punch: "q",
      kick: "w",
      grab: "e",
    },
  });
}

function createFarage() {
  return createFighter({
    name: "Far Rage",
    title: "CPU opponent",
    x: 700,
    facing: -1,
    color: "#314a87",
    trim: "#79d8ff",
    outline: "#101320",
    isCpu: true,
    portraitKey: "farage",
    portraitShape: "circle",
    portraitFocusY: 0.2,
    controls: null,
  });
}

const fighters = [createBinface(), createFarage()];

function resetFighters() {
  fighters[0] = createBinface();
  fighters[1] = createFarage();
}

function setAnnouncement(text, duration = 0.75) {
  state.announcementText = text;
  state.announcementTimeout = duration;
  announcement.textContent = text;
  announcement.classList.remove("is-flash");
  void announcement.offsetWidth;
  announcement.classList.add("is-flash");
}

function clearAnnouncement() {
  state.announcementText = "";
  state.announcementTimeout = 0;
  announcement.textContent = "";
  announcement.classList.remove("is-flash");
}

function updateHud() {
  healthLeft.style.width = `${fighters[0].health}%`;
  healthRight.style.width = `${fighters[1].health}%`;
  timerEl.textContent = String(Math.max(0, Math.ceil(state.timer)));
}

function showOverlay({ kicker, title, body, primaryLabel, primaryHandler, secondaryLabel, secondaryHandler }) {
  overlay.hidden = false;
  overlayKicker.textContent = kicker;
  overlayTitle.textContent = title;
  overlayBody.textContent = body;
  primaryAction.textContent = primaryLabel;
  primaryAction.onclick = primaryHandler;

  if (secondaryLabel && secondaryHandler) {
    secondaryAction.hidden = false;
    secondaryAction.textContent = secondaryLabel;
    secondaryAction.onclick = secondaryHandler;
  } else {
    secondaryAction.hidden = true;
    secondaryAction.onclick = null;
  }
}

function hideOverlay() {
  overlay.hidden = true;
}

function cancelSpeech() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

function applyResult(winner, mode) {
  state.phase = "result";
  fighters.forEach((fighter) => {
    fighter.attack = null;
    fighter.attackCooldown = 0;
    fighter.hitstun = 0;
    fighter.isWinner = fighter === winner;
  });

  cancelSpeech();
  state.spokenCountdown = "";

  const winnerLabel = winner ? winner.name : "No one";
  const resultLabel = mode === "ko" ? `${winnerLabel} wins!` : winner ? `${winnerLabel} on points!` : "Draw declared!";
  state.resultText = resultLabel;
  state.resultKicker = mode === "ko" ? "Knockout" : "Time up";
  setAnnouncement(mode === "ko" ? "KO!" : "Decision!", 1.4);
  playSound(mode === "ko" ? 140 : 260, 0.22, "sawtooth");

  showOverlay({
    kicker: state.resultKicker,
    title: resultLabel,
    body: winner
      ? `${winner.name} owns the promenade for now. Hit rematch to reset health, timer, portraits, and tempers.`
      : "The judges could not split them. Hit rematch to restart the bout from a clean slate.",
    primaryLabel: "Rematch",
    primaryHandler: startCountdown,
    secondaryLabel: "Back to intro",
    secondaryHandler: goToIntro,
  });
}

function goToIntro() {
  resetFighters();
  state.phase = "intro";
  state.timer = ROUND_TIME;
  state.musicClock = 0;
  state.musicStep = 0;
  state.spokenCountdown = "";
  updateHud();
  clearAnnouncement();
  cancelSpeech();
  showOverlay({
    kicker: "Tonight only",
    title: "Promenade prizefight",
    body: "Count Binfaux has the controls, Far Rage has the complaints, and the announcer is warming up. Press start for a very unserious cabinet clash.",
    primaryLabel: "Start fight",
    primaryHandler: startCountdown,
  });
}

function startCountdown() {
  resetFighters();
  state.phase = "countdown";
  state.timer = ROUND_TIME;
  state.countdown = COUNTDOWN_TOTAL;
  state.musicClock = 0;
  state.musicStep = 0;
  state.spokenCountdown = "";
  clearAnnouncement();
  hideOverlay();
  updateHud();
  keysDown.clear();
  keysPressed.clear();
  ensureAudioContext();
}

function ensureAudioContext() {
  if (!state.soundEnabled) {
    return null;
  }

  const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
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

function playSound(frequency, duration, type = "square", volume = 0.025) {
  if (!state.soundEnabled) {
    return;
  }

  const context = ensureAudioContext();
  if (!context) {
    return;
  }

  const oscillator = context.createOscillator();
  const gain = context.createGain();
  const now = context.currentTime;

  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, now);
  gain.gain.setValueAtTime(volume, now);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

  oscillator.connect(gain);
  gain.connect(context.destination);

  oscillator.start(now);
  oscillator.stop(now + duration);
}

function updateMusic(dt) {
  const isMusicPhase = state.phase === "countdown" || state.phase === "fight";
  if (!state.soundEnabled || !isMusicPhase) {
    state.musicClock = 0;
    state.musicStep = 0;
    return;
  }

  state.musicClock += dt;
  while (state.musicClock >= MUSIC_STEP_DURATION) {
    state.musicClock -= MUSIC_STEP_DURATION;
    const step = MUSIC_PATTERN[state.musicStep % MUSIC_PATTERN.length];

    if (step.bass) {
      playSound(step.bass, 0.24, "triangle", 0.017);
    }

    if (step.lead) {
      playSound(step.lead, 0.11, "square", 0.013);
    }

    state.musicStep += 1;
  }
}

function speakCountdown(text) {
  if (!state.soundEnabled || !("speechSynthesis" in window) || state.spokenCountdown === text) {
    return;
  }

  cancelSpeech();

  const utterance = new SpeechSynthesisUtterance(text === "FIGHT!" ? "Fight" : text);
  utterance.rate = text === "FIGHT!" ? 0.9 : 0.82;
  utterance.pitch = text === "FIGHT!" ? 0.58 : 0.5;
  utterance.volume = 0.95;
  state.spokenCountdown = text;
  window.speechSynthesis.speak(utterance);
}

function normalizeKey(event) {
  return event.key.toLowerCase();
}

function isPressed(key) {
  return keysDown.has(key);
}

function wasPressed(key) {
  return keysPressed.has(key);
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function isGrounded(fighter) {
  return fighter.y >= FLOOR_Y;
}

function startAttack(fighter, type) {
  fighter.attack = {
    type,
    elapsed: 0,
    connected: false,
  };
  fighter.attackCooldown = ATTACKS[type].startup + ATTACKS[type].active + ATTACKS[type].recovery;
  const sound = ATTACK_SOUND_MAP[type];
  playSound(sound.frequency, 0.08, sound.type);
}

function tryHumanAttack(attacker) {
  if (state.phase !== "fight" || attacker.attack || attacker.attackCooldown > 0 || attacker.hitstun > 0 || !isGrounded(attacker)) {
    return;
  }

  if (wasPressed(attacker.controls.punch)) {
    startAttack(attacker, "punch");
    return;
  }

  if (wasPressed(attacker.controls.kick)) {
    startAttack(attacker, "kick");
    return;
  }

  if (wasPressed(attacker.controls.grab)) {
    startAttack(attacker, "grab");
  }
}

function attackCanHit(attacker, defender, spec) {
  if (defender.invulnerable > 0) {
    return false;
  }

  const forwardDistance = (defender.x - attacker.x) * attacker.facing;
  const verticalGap = Math.abs(defender.y - attacker.y);
  return forwardDistance > 8 && forwardDistance < spec.range + defender.width * 0.5 && verticalGap < 52;
}

function registerHit(attacker, defender, spec) {
  defender.health = clamp(defender.health - spec.damage, 0, 100);
  defender.hitstun = spec.hitstun;
  defender.invulnerable = 0.16;
  defender.x = clamp(defender.x + spec.push * attacker.facing, FIGHTER_MIN_X, FIGHTER_MAX_X);
  defender.velocityY = spec === ATTACKS.grab ? -120 : defender.velocityY;
  playSound(spec === ATTACKS.grab ? 110 : 170, 0.12, spec === ATTACKS.kick ? "sawtooth" : "square", 0.035);
  updateHud();

  if (defender.health <= 0) {
    applyResult(attacker, "ko");
  }
}

function updateAttack(attacker, defender, dt) {
  if (!attacker.attack) {
    return;
  }

  const spec = ATTACKS[attacker.attack.type];
  attacker.attack.elapsed += dt;

  const activeStart = spec.startup;
  const activeEnd = spec.startup + spec.active;

  if (!attacker.attack.connected && attacker.attack.elapsed >= activeStart && attacker.attack.elapsed <= activeEnd) {
    if (attackCanHit(attacker, defender, spec)) {
      attacker.attack.connected = true;
      registerHit(attacker, defender, spec);
    }
  }

  if (attacker.attack.elapsed >= activeEnd + spec.recovery) {
    attacker.attack = null;
  }
}

function updateHumanMovement(fighter, dt) {
  const moveDirection = (isPressed(fighter.controls.right) ? 1 : 0) - (isPressed(fighter.controls.left) ? 1 : 0);
  fighter.moveDirection = moveDirection;

  if (moveDirection !== 0) {
    fighter.facing = moveDirection > 0 ? 1 : -1;
    fighter.x += moveDirection * MOVE_SPEED * dt;
  }

  if (wasPressed(fighter.controls.jump) && isGrounded(fighter)) {
    fighter.velocityY = JUMP_VELOCITY;
    playSound(520, 0.08, "triangle");
  }
}

function updateCpuBehavior(fighter, opponent, dt) {
  fighter.aiAttackTimer = Math.max(0, fighter.aiAttackTimer - dt);
  fighter.aiJumpTimer = Math.max(0, fighter.aiJumpTimer - dt);

  const gap = opponent.x - fighter.x;
  const distance = Math.abs(gap);
  fighter.facing = gap >= 0 ? 1 : -1;

  if (distance > 118) {
    fighter.moveDirection = fighter.facing;
  } else if (distance < 78) {
    fighter.moveDirection = -fighter.facing;
  } else {
    fighter.moveDirection = 0;
  }

  fighter.x += fighter.moveDirection * CPU_MOVE_SPEED * dt;

  if (distance > 180 && isGrounded(fighter) && fighter.aiJumpTimer === 0) {
    fighter.velocityY = JUMP_VELOCITY;
    fighter.aiJumpTimer = 1.35;
    playSound(470, 0.07, "triangle", 0.02);
  }

  if (!isGrounded(fighter) || fighter.attack || fighter.attackCooldown > 0 || fighter.hitstun > 0 || fighter.aiAttackTimer > 0) {
    return;
  }

  if (distance < 56) {
    startAttack(fighter, "grab");
    fighter.aiAttackTimer = 0.4;
    return;
  }

  if (distance < 82) {
    startAttack(fighter, Math.random() > 0.35 ? "punch" : "grab");
    fighter.aiAttackTimer = 0.32;
    return;
  }

  if (distance < 106) {
    startAttack(fighter, Math.random() > 0.45 ? "kick" : "punch");
    fighter.aiAttackTimer = 0.36;
  }
}

function updateFighter(fighter, opponent, dt) {
  fighter.attackCooldown = Math.max(0, fighter.attackCooldown - dt);
  fighter.hitstun = Math.max(0, fighter.hitstun - dt);
  fighter.invulnerable = Math.max(0, fighter.invulnerable - dt);

  if (fighter.hitstun <= 0 && !fighter.attack && state.phase === "fight") {
    if (fighter.isCpu) {
      updateCpuBehavior(fighter, opponent, dt);
    } else {
      updateHumanMovement(fighter, dt);
      tryHumanAttack(fighter);
    }
  } else {
    fighter.moveDirection = 0;
  }

  updateAttack(fighter, opponent, dt);

  fighter.velocityY += GRAVITY * dt;
  fighter.y += fighter.velocityY * dt;

  if (fighter.y >= FLOOR_Y) {
    fighter.y = FLOOR_Y;
    fighter.velocityY = 0;
  }

  fighter.x = clamp(fighter.x, FIGHTER_MIN_X, FIGHTER_MAX_X);
}

function updateCountdown(dt) {
  state.countdown -= dt;

  const nextText = getCountdownText();

  if (state.announcementText !== nextText) {
    setAnnouncement(nextText, 0.6);
    speakCountdown(nextText);
    const countdownSound = nextText === "FIGHT!"
      ? { frequency: 630, duration: 0.18, type: "sawtooth", volume: 0.034 }
      : { frequency: 320, duration: 0.09, type: "square", volume: 0.026 };
    playSound(countdownSound.frequency, countdownSound.duration, countdownSound.type, countdownSound.volume);
  }

  if (state.countdown <= 0) {
    state.phase = "fight";
    clearAnnouncement();
  }
}

function finishOnTimer() {
  if (fighters[0].health === fighters[1].health) {
    applyResult(null, "time");
    return;
  }

  applyResult(fighters[0].health > fighters[1].health ? fighters[0] : fighters[1], "time");
}

function update(dt) {
  updateMusic(dt);

  if (state.announcementTimeout > 0) {
    state.announcementTimeout = Math.max(0, state.announcementTimeout - dt);
    if (state.announcementTimeout === 0 && state.phase !== "countdown") {
      clearAnnouncement();
    }
  }

  if (state.phase === "countdown") {
    updateCountdown(dt);
  } else if (state.phase === "fight") {
    state.timer = Math.max(0, state.timer - dt);
    if (state.timer <= 0) {
      finishOnTimer();
    }
  }

  updateFighter(fighters[0], fighters[1], dt);
  updateFighter(fighters[1], fighters[0], dt);

  if (state.phase !== "result" && Math.abs(fighters[0].x - fighters[1].x) < MIN_FIGHTER_SEPARATION) {
    const midpoint = (fighters[0].x + fighters[1].x) / 2;
    fighters[0].x = midpoint - MIN_FIGHTER_SEPARATION / 2;
    fighters[1].x = midpoint + MIN_FIGHTER_SEPARATION / 2;
  }

  fighters[0].facing = fighters[0].x <= fighters[1].x ? 1 : -1;
  fighters[1].facing = fighters[1].x >= fighters[0].x ? -1 : 1;

  updateHud();
  keysPressed.clear();
}

function drawBackground() {
  const sky = ctx.createLinearGradient(0, 0, 0, HEIGHT);
  sky.addColorStop(0, "#18061f");
  sky.addColorStop(0.34, "#5d1d4d");
  sky.addColorStop(0.66, "#e85d3d");
  sky.addColorStop(1, "#08080f");
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  ctx.fillStyle = "rgba(255, 224, 117, 0.78)";
  ctx.beginPath();
  ctx.arc(770, 112, 44, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "rgba(255, 204, 96, 0.12)";
  for (let index = 0; index < 7; index += 1) {
    ctx.fillRect(index * 160, 92 + (index % 2) * 14, 130, 3);
  }

  ctx.fillStyle = "#33226d";
  ctx.fillRect(0, 250, WIDTH, 110);
  ctx.fillStyle = "#212c7c";
  ctx.fillRect(0, 292, WIDTH, 68);

  ctx.fillStyle = "rgba(255, 255, 255, 0.14)";
  for (let index = 0; index < 8; index += 1) {
    ctx.fillRect(index * 140 - 10, 306 + (index % 2) * 8, 120, 4);
  }

  ctx.fillStyle = "#180d18";
  ctx.fillRect(0, 360, WIDTH, 180);
  ctx.fillStyle = "#483722";
  ctx.fillRect(0, 360, WIDTH, 18);
  ctx.fillStyle = "#241821";
  ctx.fillRect(0, 378, WIDTH, 22);

  drawPier();
  drawShelters();
  drawCrowd();
}

function drawPier() {
  ctx.fillStyle = "#23131d";
  ctx.fillRect(540, 208, 250, 16);
  for (let x = 560; x <= 760; x += 28) {
    ctx.fillRect(x, 224, 8, 88);
  }

  ctx.fillRect(612, 166, 114, 44);
  ctx.fillStyle = "#ffd164";
  ctx.font = "bold 17px Inter";
  ctx.fillText("CABINET CLASH", 622, 193);

  ctx.fillStyle = "#23131d";
  ctx.fillRect(604, 150, 10, 26);
  ctx.fillRect(726, 150, 10, 26);
  ctx.beginPath();
  ctx.moveTo(609, 150);
  ctx.lineTo(684, 118);
  ctx.lineTo(731, 150);
  ctx.closePath();
  ctx.fill();
}

function drawShelters() {
  for (let i = 0; i < 4; i += 1) {
    const x = 70 + i * 130;
    ctx.fillStyle = "#130c18";
    ctx.fillRect(x, 302, 76, 64);
    ctx.fillStyle = i % 2 === 0 ? "#ebd6bf" : "#f3b53f";
    for (let stripe = 0; stripe < 5; stripe += 1) {
      ctx.fillRect(x + stripe * 15, 302, 8, 64);
    }
  }
}

function drawCrowd() {
  for (let i = 0; i < 11; i += 1) {
    const x = 36 + i * 84;
    const h = 18 + (i % 3) * 8;
    ctx.fillStyle = i % 2 === 0 ? "#100a12" : "#26162a";
    ctx.fillRect(x, 398 - h, 16, h);
    ctx.beginPath();
    ctx.arc(x + 8, 398 - h - 7, 7, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawFloorGlow() {
  const gradient = ctx.createRadialGradient(WIDTH / 2, FLOOR_Y + 40, 10, WIDTH / 2, FLOOR_Y + 40, 340);
  gradient.addColorStop(0, "rgba(255, 177, 0, 0.16)");
  gradient.addColorStop(1, "rgba(255, 177, 0, 0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, FLOOR_Y - 20, WIDTH, 130);
}

function drawImageCover(image, dx, dy, dw, dh, focusY = 0.5) {
  if (!image || !image.complete || !image.naturalWidth || !image.naturalHeight) {
    return false;
  }

  const sourceAspect = image.naturalWidth / image.naturalHeight;
  const destinationAspect = dw / dh;
  let sx = 0;
  let sy = 0;
  let sw = image.naturalWidth;
  let sh = image.naturalHeight;

  if (sourceAspect > destinationAspect) {
    sw = sh * destinationAspect;
    sx = (image.naturalWidth - sw) * 0.5;
  } else {
    sh = sw / destinationAspect;
    sy = (image.naturalHeight - sh) * focusY;
  }

  sx = clamp(sx, 0, image.naturalWidth - sw);
  sy = clamp(sy, 0, image.naturalHeight - sh);
  ctx.drawImage(image, sx, sy, sw, sh, dx, dy, dw, dh);
  return true;
}

function drawPortrait(fighter) {
  const portrait = portraits.get(fighter.portraitKey);
  const frameX = -26;
  const frameY = -126;
  const frameSize = 52;

  ctx.save();
  ctx.lineWidth = 4;
  ctx.strokeStyle = fighter.trim;
  ctx.fillStyle = "rgba(18, 14, 30, 0.95)";

  if (fighter.portraitShape === "circle") {
    ctx.beginPath();
    ctx.arc(0, -100, 26, 0, Math.PI * 2);
    ctx.fill();
    ctx.clip();
    if (!drawImageCover(portrait, -28, -128, 56, 56, fighter.portraitFocusY)) {
      ctx.fillStyle = "#f1c8a1";
      ctx.beginPath();
      ctx.arc(0, -102, 22, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#c98b2d";
      ctx.fillRect(-24, -126, 48, 10);
      ctx.fillStyle = "#131722";
      ctx.fillRect(-8, -107, 16, 4);
    }
    ctx.restore();
    ctx.beginPath();
    ctx.arc(0, -100, 26, 0, Math.PI * 2);
    ctx.strokeStyle = fighter.trim;
    ctx.lineWidth = 4;
    ctx.stroke();
    return;
  }

  ctx.beginPath();
  ctx.roundRect(frameX, frameY, frameSize, frameSize, 10);
  ctx.fill();
  ctx.clip();
  if (!drawImageCover(portrait, frameX, frameY, frameSize, frameSize, fighter.portraitFocusY)) {
    ctx.fillStyle = "#b9bfcc";
    ctx.fillRect(-22, -120, 44, 32);
    ctx.fillStyle = "#8f97a6";
    ctx.fillRect(-28, -126, 56, 8);
    ctx.fillStyle = "#1d2738";
    ctx.fillRect(-14, -108, 28, 12);
    ctx.fillStyle = "#ffb100";
    ctx.fillRect(-4, -99, 8, 8);
  }
  ctx.restore();
  ctx.beginPath();
  ctx.roundRect(frameX, frameY, frameSize, frameSize, 10);
  ctx.strokeStyle = fighter.trim;
  ctx.lineWidth = 4;
  ctx.stroke();
}

function drawFighter(fighter) {
  const bob = fighter.attack ? -4 : fighter.moveDirection !== 0 ? Math.sin(performance.now() / 90) * 3 : 0;
  const baseX = fighter.x;
  const baseY = fighter.y + bob;
  const hitTint = fighter.invulnerable > 0 ? 28 : 0;

  ctx.save();
  ctx.translate(baseX, baseY);
  ctx.scale(fighter.facing, 1);

  ctx.fillStyle = "rgba(0, 0, 0, 0.28)";
  ctx.beginPath();
  ctx.ellipse(0, 10, 36, 12, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.lineCap = "round";
  ctx.strokeStyle = fighter.outline;
  ctx.lineWidth = 8;

  const armReach = fighter.attack ? ARM_REACH_BY_ATTACK[fighter.attack.type] || 0 : 0;
  const legReach = fighter.attack ? LEG_REACH_BY_ATTACK[fighter.attack.type] || 0 : 0;

  ctx.strokeStyle = fighter.outline;
  ctx.beginPath();
  ctx.moveTo(0, -78);
  ctx.lineTo(0, -10);
  ctx.stroke();

  ctx.strokeStyle = `rgb(${32 + hitTint}, ${46 + hitTint}, ${58 + hitTint})`;
  ctx.beginPath();
  ctx.moveTo(0, -58);
  ctx.lineTo(28 + armReach, -34);
  ctx.moveTo(0, -54);
  ctx.lineTo(-26, -26 + (fighter.attack?.type === "grab" ? -8 : 0));
  ctx.moveTo(0, -10);
  ctx.lineTo(24 + legReach, 34);
  ctx.moveTo(0, -10);
  ctx.lineTo(-20, 34);
  ctx.stroke();

  ctx.fillStyle = fighter.color;
  ctx.fillRect(-18, -86, 36, 62);

  ctx.fillStyle = fighter.trim;
  ctx.fillRect(-18, -70, 36, 10);
  ctx.fillRect(-12, -26, 24, 8);

  drawPortrait(fighter);

  ctx.restore();
}

function drawVsBanner() {
  ctx.save();
  ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
  ctx.fillRect(WIDTH / 2 - 48, 24, 96, 48);
  ctx.fillStyle = "#fff1b1";
  ctx.font = '28px "Metal Mania"';
  ctx.textAlign = "center";
  ctx.fillText("VS", WIDTH / 2, 58);
  ctx.restore();
}

function draw() {
  ctx.clearRect(0, 0, WIDTH, HEIGHT);
  drawBackground();
  drawFloorGlow();
  drawVsBanner();
  drawFighter(fighters[0]);
  drawFighter(fighters[1]);
}

function getCountdownText() {
  if (state.countdown > COUNTDOWN_ROUND_MARK) {
    return "ROUND 1";
  }

  if (state.countdown > COUNTDOWN_THREE_MARK) {
    return "3";
  }

  if (state.countdown > COUNTDOWN_TWO_MARK) {
    return "2";
  }

  if (state.countdown > COUNTDOWN_ONE_MARK) {
    return "1";
  }

  return "FIGHT!";
}

function gameLoop(timestamp) {
  if (!state.lastFrame) {
    state.lastFrame = timestamp;
  }

  const dt = Math.min(MAX_DT, (timestamp - state.lastFrame) / 1000);
  state.lastFrame = timestamp;
  update(dt);
  draw();
  requestAnimationFrame(gameLoop);
}

document.addEventListener("keydown", (event) => {
  const key = normalizeKey(event);
  if (CONTROL_KEYS.has(key)) {
    event.preventDefault();
  }

  if (!keysDown.has(key)) {
    keysPressed.add(key);
  }

  keysDown.add(key);
});

document.addEventListener("keyup", (event) => {
  keysDown.delete(normalizeKey(event));
});

soundToggle.addEventListener("click", () => {
  state.soundEnabled = !state.soundEnabled;
  soundToggle.textContent = `Sound: ${state.soundEnabled ? "On" : "Off"}`;
  soundToggle.setAttribute("aria-pressed", String(state.soundEnabled));
  state.musicClock = 0;
  state.musicStep = 0;
  if (!state.soundEnabled) {
    cancelSpeech();
  } else {
    ensureAudioContext();
    playSound(380, 0.08, "triangle");
  }
});

preloadPortraits();
goToIntro();
requestAnimationFrame(gameLoop);
