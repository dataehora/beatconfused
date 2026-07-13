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
const JUMP_VELOCITY = -720;
const MAX_DT = 1 / 30;
const MIN_FIGHTER_SEPARATION = 72;
const COUNTDOWN_TOTAL = 3.5;
const COUNTDOWN_ROUND_MARK = 2.7;
const COUNTDOWN_THREE_MARK = 1.95;
const COUNTDOWN_TWO_MARK = 1.2;
const COUNTDOWN_ONE_MARK = 0.45;
const ATTACK_SOUND_MAP = {
  punch: { frequency: 420, type: "square" },
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

const ATTACKS = {
  punch: { startup: 0.08, active: 0.12, recovery: 0.2, range: 68, damage: 8, push: 28, hitstun: 0.18 },
  kick: { startup: 0.12, active: 0.12, recovery: 0.26, range: 88, damage: 12, push: 36, hitstun: 0.23 },
  grab: { startup: 0.1, active: 0.08, recovery: 0.34, range: 48, damage: 16, push: 44, hitstun: 0.28 },
};

const CONTROL_KEYS = new Set([
  "a",
  "d",
  "w",
  "f",
  "g",
  "h",
  "arrowleft",
  "arrowright",
  "arrowup",
  "k",
  "l",
  ";",
]);

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
};

const keysDown = new Set();
const keysPressed = new Set();

let audioContext;

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
    pose: config.pose,
    health: 100,
    velocityY: 0,
    hitstun: 0,
    invulnerable: 0,
    attack: null,
    attackCooldown: 0,
    moveDirection: 0,
    jumpQueued: false,
    isWinner: false,
    controls: config.controls,
  };
}

const fighters = [
  createFighter({
    name: "Count Binfaux",
    title: "Space-bin reformer",
    x: 260,
    facing: 1,
    color: "#d8dce6",
    trim: "#ffb100",
    outline: "#1f2433",
    pose: "bin",
    controls: {
      left: "a",
      right: "d",
      jump: "w",
      punch: "f",
      kick: "g",
      grab: "h",
    },
  }),
  createFighter({
    name: "Far Rage",
    title: "Pier-side blusterer",
    x: 700,
    facing: -1,
    color: "#355996",
    trim: "#54ddff",
    outline: "#101320",
    pose: "bluster",
    controls: {
      left: "arrowleft",
      right: "arrowright",
      jump: "arrowup",
      punch: "k",
      kick: "l",
      grab: ";",
    },
  }),
];

function resetFighters() {
  fighters[0] = createFighter({
    name: "Count Binfaux",
    title: "Space-bin reformer",
    x: 260,
    facing: 1,
    color: "#d8dce6",
    trim: "#ffb100",
    outline: "#1f2433",
    pose: "bin",
    controls: fighters[0].controls,
  });
  fighters[1] = createFighter({
    name: "Far Rage",
    title: "Pier-side blusterer",
    x: 700,
    facing: -1,
    color: "#355996",
    trim: "#54ddff",
    outline: "#101320",
    pose: "bluster",
    controls: fighters[1].controls,
  });
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

function applyResult(winner, mode) {
  state.phase = "result";
  fighters.forEach((fighter) => {
    fighter.attack = null;
    fighter.attackCooldown = 0;
    fighter.hitstun = 0;
    fighter.isWinner = fighter === winner;
  });

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
      ? `${winner.name} controls the promenade today. Hit rematch to reset health, timer, positions, and try again.`
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
  updateHud();
  clearAnnouncement();
  showOverlay({
    kicker: "Tonight only",
    title: "Promenade prizefight",
    body: "Two parody hopefuls have arrived in Clacton for a highly unserious clash. Press start and settle the argument with jumps, jabs, kicks, and grabs.",
    primaryLabel: "Start fight",
    primaryHandler: startCountdown,
  });
}

function startCountdown() {
  resetFighters();
  state.phase = "countdown";
  state.timer = ROUND_TIME;
  state.countdown = COUNTDOWN_TOTAL;
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

  if (!audioContext) {
    audioContext = new window.AudioContext();
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

function tryAttack(attacker, defender) {
  if (state.phase !== "fight") {
    return;
  }

  if (attacker.attack) {
    return;
  }

  if (attacker.attackCooldown > 0) {
    return;
  }

  if (attacker.hitstun > 0) {
    return;
  }

  // Attacks only resolve from grounded neutral so each move has a readable start and cooldown.
  if (!isGrounded(attacker)) {
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
    return;
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
  defender.x = clamp(defender.x + spec.push * attacker.facing, 84, WIDTH - 84);
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

function updateFighter(fighter, opponent, dt) {
  fighter.attackCooldown = Math.max(0, fighter.attackCooldown - dt);
  fighter.hitstun = Math.max(0, fighter.hitstun - dt);
  fighter.invulnerable = Math.max(0, fighter.invulnerable - dt);

  if (fighter.hitstun <= 0 && !fighter.attack && state.phase === "fight") {
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
  } else {
    fighter.moveDirection = 0;
  }

  tryAttack(fighter, opponent);
  updateAttack(fighter, opponent, dt);

  fighter.velocityY += GRAVITY * dt;
  fighter.y += fighter.velocityY * dt;

  if (fighter.y >= FLOOR_Y) {
    fighter.y = FLOOR_Y;
    fighter.velocityY = 0;
  }

  fighter.x = clamp(fighter.x, 58, WIDTH - 58);
}

function updateCountdown(dt) {
  state.countdown -= dt;

  const nextText = getCountdownText();

  if (state.announcementText !== nextText) {
    setAnnouncement(nextText, 0.6);
    const countdownSound = nextText === "FIGHT!"
      ? { frequency: 630, duration: 0.18, type: "sawtooth" }
      : { frequency: 320, duration: 0.09, type: "square" };
    playSound(countdownSound.frequency, countdownSound.duration, countdownSound.type);
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
    if (state.timer === 0) {
      finishOnTimer();
    }
  }

  updateFighter(fighters[0], fighters[1], dt);
  updateFighter(fighters[1], fighters[0], dt);

  if (state.phase !== "result") {
    if (Math.abs(fighters[0].x - fighters[1].x) < MIN_FIGHTER_SEPARATION) {
      const midpoint = (fighters[0].x + fighters[1].x) / 2;
      fighters[0].x = midpoint - MIN_FIGHTER_SEPARATION / 2;
      fighters[1].x = midpoint + MIN_FIGHTER_SEPARATION / 2;
    }
  }

  fighters[0].facing = fighters[0].x <= fighters[1].x ? 1 : -1;
  fighters[1].facing = fighters[1].x >= fighters[0].x ? -1 : 1;

  updateHud();
  keysPressed.clear();
}

function drawBackground() {
  const sky = ctx.createLinearGradient(0, 0, 0, HEIGHT);
  sky.addColorStop(0, "#214f8a");
  sky.addColorStop(0.45, "#6f85b7");
  sky.addColorStop(0.72, "#f08e65");
  sky.addColorStop(1, "#101522");
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  ctx.fillStyle = "rgba(255, 226, 148, 0.75)";
  ctx.beginPath();
  ctx.arc(760, 115, 42, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#2d68a3";
  ctx.fillRect(0, 250, WIDTH, 110);
  ctx.fillStyle = "#367bbd";
  ctx.fillRect(0, 290, WIDTH, 70);

  ctx.fillStyle = "rgba(255, 255, 255, 0.14)";
  for (let index = 0; index < 8; index += 1) {
    ctx.fillRect(index * 140 - 10, 305 + (index % 2) * 8, 120, 4);
  }

  ctx.fillStyle = "#1a202f";
  ctx.fillRect(0, 360, WIDTH, 180);
  ctx.fillStyle = "#4b4c56";
  ctx.fillRect(0, 360, WIDTH, 18);
  ctx.fillStyle = "#292a34";
  ctx.fillRect(0, 378, WIDTH, 22);

  drawPier();
  drawShelters();
  drawCrowd();
}

function drawPier() {
  ctx.fillStyle = "#231b20";
  ctx.fillRect(540, 208, 250, 16);
  for (let x = 560; x <= 760; x += 28) {
    ctx.fillRect(x, 224, 8, 88);
  }

  ctx.fillRect(618, 168, 102, 42);
  ctx.fillStyle = "#ffd164";
  ctx.font = "bold 18px Inter";
  ctx.fillText("CLACTON PIER", 628, 194);

  ctx.fillStyle = "#231b20";
  ctx.fillRect(604, 150, 10, 26);
  ctx.fillRect(726, 150, 10, 26);
  ctx.beginPath();
  ctx.moveTo(609, 150);
  ctx.lineTo(684, 120);
  ctx.lineTo(731, 150);
  ctx.closePath();
  ctx.fill();
}

function drawShelters() {
  for (let i = 0; i < 4; i += 1) {
    const x = 70 + i * 130;
    ctx.fillStyle = "#0e1320";
    ctx.fillRect(x, 302, 76, 64);
    ctx.fillStyle = "#ebd6bf";
    for (let stripe = 0; stripe < 5; stripe += 1) {
      ctx.fillRect(x + stripe * 15, 302, 8, 64);
    }
  }
}

function drawCrowd() {
  for (let i = 0; i < 11; i += 1) {
    const x = 36 + i * 84;
    const h = 18 + (i % 3) * 8;
    ctx.fillStyle = i % 2 === 0 ? "#10131e" : "#1a2232";
    ctx.fillRect(x, 398 - h, 16, h);
    ctx.beginPath();
    ctx.arc(x + 8, 398 - h - 7, 7, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawFloorGlow() {
  const gradient = ctx.createRadialGradient(WIDTH / 2, FLOOR_Y + 40, 10, WIDTH / 2, FLOOR_Y + 40, 340);
  gradient.addColorStop(0, "rgba(255, 177, 0, 0.14)");
  gradient.addColorStop(1, "rgba(255, 177, 0, 0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, FLOOR_Y - 20, WIDTH, 130);
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

  if (fighter.pose === "bin") {
    ctx.fillStyle = "#b9bfcc";
    ctx.fillRect(-22, -120, 44, 32);
    ctx.fillStyle = "#8f97a6";
    ctx.fillRect(-28, -126, 56, 8);
    ctx.fillStyle = "#1d2738";
    ctx.fillRect(-14, -108, 28, 12);
    ctx.fillStyle = "#ffb100";
    ctx.fillRect(-4, -99, 8, 8);
  } else {
    ctx.fillStyle = "#f1c8a1";
    ctx.beginPath();
    ctx.arc(0, -102, 22, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#e6d7b3";
    ctx.fillRect(-22, -118, 44, 7);
    ctx.fillStyle = "#c98b2d";
    ctx.fillRect(-24, -126, 48, 10);
    ctx.fillStyle = "#131722";
    ctx.fillRect(-8, -107, 16, 4);
  }

  ctx.restore();
}

function drawVsBanner() {
  ctx.save();
  ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
  ctx.fillRect(WIDTH / 2 - 30, 26, 60, 44);
  ctx.fillStyle = "#fff1b1";
  ctx.font = "bold 26px Cinzel";
  ctx.textAlign = "center";
  ctx.fillText("VS", WIDTH / 2, 56);
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
  const dt = Math.min(MAX_DT, (timestamp - state.lastFrame) / 1000 || 0);
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
  if (state.soundEnabled) {
    playSound(380, 0.08, "triangle");
  }
});

goToIntro();
requestAnimationFrame(gameLoop);
