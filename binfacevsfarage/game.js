/* =========================================================================
   CLACTON FIGHTER II — a Street-Fighter-II-style browser brawler
   Pure HTML/CSS/JS, no build step. Character/stage art is loaded from
   ./Assets/<Name>.png — if an image is missing, a stylised placeholder
   is drawn instead so the game is fully playable without any art files.
   ========================================================================= */

(() => {
  "use strict";

  /* ----------------------------- CONFIG ----------------------------- */
  const CANVAS_W = 960, CANVAS_H = 540;
  let GROUND_Y = CANVAS_H - 46; // overridden per-map in beginMatch()
  const GRAVITY = 1400;
  const JUMP_VELOCITY = -620;
  const MOVE_SPEED = 260;
  const FIGHTER_W = 130, FIGHTER_H = 210;
  const MAX_HEALTH = 100;
  const ROUND_TIME = 30; // seconds
  const THROW_COOLDOWN = 0.7;
  const HIT_STUN = 0.35;
  const ARENA_MARGIN = 40;

  // If a character's art ever looks like it's facing the wrong way in-game,
  // fix it here instead of re-editing image files: -1 mirrors every pose for
  // that character, 1 leaves them as authored.
  const FACING_OVERRIDE = { Binface: 1, Farrage: 1 };
  // Per-pose exceptions: sometimes only one specific pose in a character's
  // set is mirrored relative to the rest (e.g. an arm-reach pose drawn
  // facing the opposite way to the character's walk/idle art). Each entry
  // flips just that one pose for that one character, independent of the
  // character-wide FACING_OVERRIDE above.
  const POSE_FACING_OVERRIDE = {
    Binface: { throw: -1 },
  };

  const FIGHTERS = {
    Binface: {
      label: "COUNT BINFACE",
      color: "#2ecC71",
      capColor: "#1a8f4a",
      projectileLabel: "rubbish bag",
      projectileColor: "#7a5230",
      projectileScale: 1.3, // 30% bigger bag
      projectileSpinRate: 8, // 20% slower spin
    },
    Farrage: {
      label: "FARAGE",
      color: "#3b6ea5",
      capColor: "#22456b",
      projectileLabel: "spinning dirty bitcoin",
      projectileColor: "#c9971f",
      projectileScale: 1.3, // 30% bigger bag
      projectileSpinRate: 5, // 50% slower spin than the rubbish bag
    },
  };

  const MAPS = {
    Pier: { label: "THE PIER", tint: "#274b6b", groundOffset: 46 },
    MagicCity: { label: "MAGIC CITY", tint: "#5a2a6b", groundOffset: 26 },
  };

  /* ----------------------------- DOM REFS ----------------------------- */
  const $ = (sel) => document.querySelector(sel);
  const screenMenu = $("#screen-menu");
  const screenGame = $("#screen-game");
  const screenResult = $("#screen-result");
  const canvas = $("#game-canvas");
  const ctx = canvas.getContext("2d");
  const overlayText = $("#overlay-text");
  const p1HealthEl = $("#p1-health");
  const p2HealthEl = $("#p2-health");
  const p1NameEl = $("#p1-name");
  const p2NameEl = $("#p2-name");
  const timerEl = $("#timer");
  const roundLabelEl = $("#round-label");
  const startBtn = $("#start-btn");
  const resultTitle = $("#result-title");
  const resultSub = $("#result-sub");
  const resultBg = $("#result-bg");
  const resultBgPhoto = $("#result-bg-photo");
  const winnerPortrait = $("#winner-portrait");
  const paperHeadline = $("#paper-headline");
  const paperSubhead = $("#paper-subhead");
  const paperPhoto = $("#paper-photo");
  const paperDate = $("#paper-date");
  const continueNumEl = $("#continue-num");

  let selectedMap = null;
  let selectedFighter = null;

  /* ----------------------------- TOUCH DETECTION ----------------------------- */
  if (matchMedia("(pointer: coarse)").matches) {
    document.body.classList.add("show-touch");
  }

  /* ============================================================
     MENU INTERACTIONS
     ============================================================ */
  document.querySelectorAll("#map-row .option-card").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#map-row .option-card").forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedMap = btn.dataset.map;
      checkReady();
    });
  });

  document.querySelectorAll("#fighter-row .option-card").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#fighter-row .option-card").forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedFighter = btn.dataset.fighter;
      checkReady();
    });
  });

  function checkReady() {
    startBtn.disabled = !(selectedMap && selectedFighter);
  }

  startBtn.addEventListener("click", () => {
    AudioEngine.sfxSelected();
    screenMenu.classList.add("hidden");
    screenGame.classList.remove("hidden");
    beginMatch(selectedFighter, selectedMap);
  });

  let continueInterval = null;
  function stopContinueCountdown() {
    if (continueInterval) clearInterval(continueInterval);
    continueInterval = null;
  }

  $("#menu-btn").addEventListener("click", () => {
    stopContinueCountdown();
    screenResult.classList.add("hidden");
    screenMenu.classList.remove("hidden");
    AudioEngine.startMenuMusic();
  });

  $("#rematch-btn").addEventListener("click", () => {
    stopContinueCountdown();
    screenResult.classList.add("hidden");
    screenGame.classList.remove("hidden");
    beginMatch(selectedFighter, selectedMap);
  });

  /* ============================================================
     ASSET LOADING (with graceful placeholder fallback)
     ============================================================ */
  function loadImage(path) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => resolve(null); // null => use placeholder
      img.src = path;
    });
  }

  // Pose sprite set a fighter can have. Any pose file that's missing simply
  // stays null and the generic silhouette placeholder is drawn for that
  // fighter/state combo instead — nothing breaks if only some art exists.
  const POSE_NAMES = ["idle1", "idle2", "run", "hit", "jump", "throw", "win"];

  async function loadPoseSet(key) {
    const entries = await Promise.all(
      POSE_NAMES.map((p) => loadImage(`Assets/${key}_${p}.png`))
    );
    const set = {};
    POSE_NAMES.forEach((p, i) => (set[p] = entries[i]));
    set.projectile = await loadImage(`Assets/${key}_projectile.png`);
    return set;
  }

  let ASSETS = { bg: null, poses: {} };

  async function loadAssetsFor(fighterKey, mapKey) {
    const otherKey = fighterKey === "Binface" ? "Farrage" : "Binface";
    const [bg, poses1, poses2] = await Promise.all([
      loadImage(`Assets/${mapKey}.png`),
      loadPoseSet(fighterKey),
      loadPoseSet(otherKey),
    ]);
    ASSETS.bg = bg;
    ASSETS.poses[fighterKey] = poses1;
    ASSETS.poses[otherKey] = poses2;
  }

  // Picks the right sprite image for a fighter's current animation state.
  // Falls back to null (placeholder silhouette) if that pose wasn't supplied.
  function poseFor(f) {
    const set = ASSETS.poses[f.key];
    if (!set) return null;
    switch (f.state) {
      case "idle":
        // gentle 2-frame breathing loop between the two "stopped" poses
        return (Math.floor(f.animT / 0.5) % 2 === 0 ? set.idle1 : set.idle2) || set.idle1;
      case "walk":
        return set.run || set.idle2 || set.idle1;
      case "jump":
        return set.jump;
      case "throw":
        return set.throw;
      case "hit":
        return set.hit;
      case "ko":
        return set.hit;
      case "win":
        return set.win;
      default:
        return set.idle1;
    }
  }

  /* ============================================================
     AUDIO — Assets-first sound system.
     For every sound below, if a matching file exists in Assets/ it is
     used as-is (looked up as .mp3, then .ogg, then .wav). If nothing is
     found, a synthesised fallback (Web Audio API) plays instead — the
     battle theme is a distorted power-chord rock riff, not a chiptune
     arpeggio — so the game always has sound even with zero audio assets.

     Drop any of these filenames into Assets/ to override the built-in
     sounds:
       Assets/music.mp3         — looping battle theme
       Assets/sfx_select.mp3    — looping ambient track for the menu screen
       Assets/sfx_selected.mp3  — pressing "LET'S HAVE IT!" to confirm
       Assets/sfx_throw.mp3     — throwing the rubbish bag / money bags
       Assets/sfx_hit.mp3       — getting struck by a projectile
       Assets/sfx_jump.mp3      — jumping
       Assets/sfx_countdown.mp3 — each "3, 2, 1" countdown beep
       Assets/sfx_fight.mp3     — the "FIGHT!" call-out
       Assets/sfx_ko.mp3        — knockout
       Assets/sfx_win.mp3       — victory jingle on the result screen
     (.ogg / .wav also work — just match the same base filename.)
     ============================================================ */
  const SOUND_FILES = {
    music: "music",
    select: "sfx_select",
    selected: "sfx_selected",
    throw: "sfx_throw",
    hit: "sfx_hit",
    jump: "sfx_jump",
    countdown: "sfx_countdown",
    fight: "sfx_fight",
    ko: "sfx_ko",
    win: "sfx_win",
  };
  const AUDIO_EXTS = ["mp3", "ogg", "wav"];

  function loadCustomAudio(baseName) {
    return new Promise((resolve) => {
      let i = 0;
      const tryNext = () => {
        if (i >= AUDIO_EXTS.length) return resolve(null);
        const audio = new Audio();
        const path = `Assets/${baseName}.${AUDIO_EXTS[i]}`;
        i++;
        let settled = false;
        const finish = (ok) => {
          if (settled) return;
          settled = true;
          ok ? resolve(audio) : tryNext();
        };
        audio.addEventListener("canplaythrough", () => finish(true), { once: true });
        audio.addEventListener("error", () => finish(false), { once: true });
        audio.src = path;
        audio.load();
        setTimeout(() => finish(false), 3000); // don't hang forever on a stalled request
      };
      tryNext();
    });
  }

  const CUSTOM_AUDIO = {};
  const customAudioReady = Promise.all(
    Object.entries(SOUND_FILES).map(async ([key, base]) => {
      CUSTOM_AUDIO[key] = await loadCustomAudio(base);
    })
  );

  const AudioEngine = (() => {
    let actx = null;
    let musicTimer = null;
    let musicUsingCustom = false;
    let step = 0;
    const BPM = 150; // driving rock stomp, not a chiptune arpeggio
    const STEP_TIME = 60 / BPM / 2; // eighth notes, 16 steps = two bars of 4/4

    // two-bar power-chord progression (i - i - VI - VII in E minor) — the
    // kind of chugging rhythm-guitar riff a Guile/Ryu-style stage theme runs
    // underneath its melody. Guitar and bass lock to the chord roots, drums
    // lay down a rock backbeat, and a sparse synth-lead hook answers in bar 2.
    const CHORD_ROOT = [
      164.81,164.81,164.81,164.81, 164.81,164.81,164.81,164.81, // E3 (bar 1)
      130.81,130.81,130.81,130.81, 146.83,146.83,146.83,146.83, // C3, D3 (bar 2)
    ];
    const GTR   = [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1]; // rhythm-guitar chug, every 8th
    const BASS  = [1,0,1,1, 0,1,0,1, 1,0,1,1, 0,1,0,1]; // syncopated bass under the chug
    const HAT   = [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1]; // driving closed hats
    const KICK  = [1,0,0,0, 1,0,0,1, 1,0,0,0, 1,0,0,1]; // kick on 1, 3, and a pickup
    const SNARE = [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0]; // backbeat on 2 & 4
    const LEAD  = [0,0,0,0, 0,0,0,0, 0,0,659,0, 784,880,0,987]; // rising hook, bar 2 only

    let noiseBuffer = null;
    let distortionCurve = null;
    let musicBus = null;

    let iosAudioUnlocked = false;

    // iOS Safari mutes <audio>/<video> and Web Audio output when the phone's
    // physical silent switch is on, UNLESS a <video> element with a live
    // audio track is played — that flips the page's audio session into the
    // "video playback" category, which iOS exempts from the mute switch, and
    // it stays exempt for the rest of the session (including plain Web Audio
    // output afterwards). Built entirely from an in-memory MediaStream (a
    // blank canvas track + a near-silent oscillator) so no audio/video asset
    // file is needed. Runs once, on the first real audio trigger (always
    // inside a user gesture, which iOS requires for this to take effect).
    function unlockIOSAudioSession(ac) {
      if (iosAudioUnlocked || typeof HTMLCanvasElement === "undefined" || !HTMLCanvasElement.prototype.captureStream) {
        return;
      }
      iosAudioUnlocked = true;

      try {
        const canvas = document.createElement("canvas");
        canvas.width = 1;
        canvas.height = 1;
        const videoStream = canvas.captureStream(0);

        const dest = ac.createMediaStreamDestination();
        const osc = ac.createOscillator();
        const gain = ac.createGain();
        gain.gain.value = 0.00001; // inaudible, but a live (non-silent) track
        osc.connect(gain).connect(dest);
        osc.start();

        const combined = new MediaStream([...videoStream.getVideoTracks(), ...dest.stream.getAudioTracks()]);
        const video = document.createElement("video");
        video.muted = false;
        video.setAttribute("playsinline", "");
        video.setAttribute("webkit-playsinline", "");
        video.style.display = "none";
        video.srcObject = combined;
        document.body.appendChild(video);
        video.play().catch(() => {});
      } catch (_) {
        // best-effort — if any of this isn't supported, sound still plays,
        // it just may stay silenced by the mute switch on affected devices
      }
    }

    function ensureCtx() {
      if (!actx) actx = new (window.AudioContext || window.webkitAudioContext)();
      if (actx.state === "suspended") actx.resume();
      unlockIOSAudioSession(actx);
      return actx;
    }

    function getNoiseBuffer(ac) {
      if (noiseBuffer) return noiseBuffer;
      const len = ac.sampleRate * 0.2;
      noiseBuffer = ac.createBuffer(1, len, ac.sampleRate);
      const data = noiseBuffer.getChannelData(0);
      for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;
      return noiseBuffer;
    }

    // classic waveshaper soft-clip curve — turns a plain oscillator into a
    // crunchy, amp-like distortion for the rhythm guitar and bass
    function getDistortionCurve() {
      if (distortionCurve) return distortionCurve;
      const amount = 34;
      const n = 44100;
      const curve = new Float32Array(n);
      const deg = Math.PI / 180;
      for (let i = 0; i < n; i++) {
        const x = (i * 2) / n - 1;
        curve[i] = ((3 + amount) * x * 20 * deg) / (Math.PI + amount * Math.abs(x));
      }
      distortionCurve = curve;
      return curve;
    }

    // shared bus for the synth-music instruments only — sfx stay wired
    // straight to the destination so they're never ducked by this. Glues the
    // guitar/bass/drum layers together and keeps them from clipping when
    // several land on the same eighth note.
    function getMusicBus(ac) {
      if (musicBus) return musicBus;
      const comp = ac.createDynamicsCompressor();
      comp.threshold.value = -20;
      comp.knee.value = 14;
      comp.ratio.value = 4;
      comp.attack.value = 0.004;
      comp.release.value = 0.18;
      comp.connect(ac.destination);
      musicBus = comp;
      return musicBus;
    }

    function blip(freq, duration, type, gainVal, when) {
      const ac = ensureCtx();
      const osc = ac.createOscillator();
      const gain = ac.createGain();
      osc.type = type;
      osc.frequency.value = freq;
      gain.gain.value = gainVal;
      gain.gain.setValueAtTime(gainVal, when);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
      osc.connect(gain).connect(ac.destination);
      osc.start(when);
      osc.stop(when + duration);
    }

    function hat(when, gainVal) {
      const ac = ensureCtx();
      const src = ac.createBufferSource();
      src.buffer = getNoiseBuffer(ac);
      const hp = ac.createBiquadFilter();
      hp.type = "highpass";
      hp.frequency.value = 6000;
      const gain = ac.createGain();
      gain.gain.setValueAtTime(gainVal, when);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + 0.05);
      src.connect(hp).connect(gain).connect(getMusicBus(ac));
      src.start(when);
      src.stop(when + 0.06);
    }

    function kick(when, gainVal) {
      const ac = ensureCtx();
      const osc = ac.createOscillator();
      const gain = ac.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(150, when);
      osc.frequency.exponentialRampToValueAtTime(45, when + 0.12);
      gain.gain.setValueAtTime(gainVal, when);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + 0.16);
      osc.connect(gain).connect(getMusicBus(ac));
      osc.start(when);
      osc.stop(when + 0.18);
    }

    // acoustic-style snare — bandpassed noise crack plus a tonal thump for body
    function snare(when, gainVal) {
      const ac = ensureCtx();
      const src = ac.createBufferSource();
      src.buffer = getNoiseBuffer(ac);
      const bp = ac.createBiquadFilter();
      bp.type = "bandpass";
      bp.frequency.value = 1800;
      bp.Q.value = 0.7;
      const nGain = ac.createGain();
      nGain.gain.setValueAtTime(gainVal, when);
      nGain.gain.exponentialRampToValueAtTime(0.0001, when + 0.12);
      src.connect(bp).connect(nGain).connect(getMusicBus(ac));
      src.start(when);
      src.stop(when + 0.13);

      const osc = ac.createOscillator();
      const oGain = ac.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(200, when);
      osc.frequency.exponentialRampToValueAtTime(120, when + 0.08);
      oGain.gain.setValueAtTime(gainVal * 0.6, when);
      oGain.gain.exponentialRampToValueAtTime(0.0001, when + 0.09);
      osc.connect(oGain).connect(getMusicBus(ac));
      osc.start(when);
      osc.stop(when + 0.1);
    }

    // distorted power chord (root + fifth + octave) — the rhythm-guitar chug
    function powerChord(rootFreq, duration, gainVal, when) {
      const ac = ensureCtx();
      const shaper = ac.createWaveShaper();
      shaper.curve = getDistortionCurve();
      shaper.oversample = "2x";
      const tone = ac.createBiquadFilter();
      tone.type = "lowpass";
      tone.frequency.value = 3200;
      const gain = ac.createGain();
      gain.gain.setValueAtTime(gainVal, when);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
      shaper.connect(tone).connect(gain).connect(getMusicBus(ac));
      [1, 1.5, 2].forEach((mult, idx) => {
        const osc = ac.createOscillator();
        osc.type = "sawtooth";
        osc.frequency.value = rootFreq * mult;
        osc.detune.value = idx === 0 ? -5 : idx === 2 ? 5 : 0;
        osc.connect(shaper);
        osc.start(when);
        osc.stop(when + duration);
      });
    }

    // driven bass guitar, an octave under the chord root
    function rockBass(freq, duration, gainVal, when) {
      const ac = ensureCtx();
      const shaper = ac.createWaveShaper();
      shaper.curve = getDistortionCurve();
      const tone = ac.createBiquadFilter();
      tone.type = "lowpass";
      tone.frequency.value = 950;
      const gain = ac.createGain();
      gain.gain.setValueAtTime(gainVal, when);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
      shaper.connect(tone).connect(gain).connect(getMusicBus(ac));
      const osc = ac.createOscillator();
      osc.type = "sawtooth";
      osc.frequency.value = freq;
      osc.connect(shaper);
      osc.start(when);
      osc.stop(when + duration);
    }

    // a meatier "impact" for hits/KOs — low thump + band-passed noise
    // crunch layered together, closer to a classic arcade-fighter punch hit
    function punch(when, gainVal) {
      const ac = ensureCtx();
      const osc = ac.createOscillator();
      const oGain = ac.createGain();
      osc.type = "square";
      osc.frequency.setValueAtTime(190, when);
      osc.frequency.exponentialRampToValueAtTime(55, when + 0.09);
      oGain.gain.setValueAtTime(gainVal, when);
      oGain.gain.exponentialRampToValueAtTime(0.0001, when + 0.13);
      osc.connect(oGain).connect(ac.destination);
      osc.start(when);
      osc.stop(when + 0.14);

      const src = ac.createBufferSource();
      src.buffer = getNoiseBuffer(ac);
      const bp = ac.createBiquadFilter();
      bp.type = "bandpass";
      bp.frequency.value = 1400;
      bp.Q.value = 0.6;
      const nGain = ac.createGain();
      nGain.gain.setValueAtTime(gainVal * 0.85, when);
      nGain.gain.exponentialRampToValueAtTime(0.0001, when + 0.08);
      src.connect(bp).connect(nGain).connect(ac.destination);
      src.start(when);
      src.stop(when + 0.09);
    }

    // rising filtered-noise sweep for throws/whooshes
    function whoosh(when, gainVal) {
      const ac = ensureCtx();
      const src = ac.createBufferSource();
      src.buffer = getNoiseBuffer(ac);
      const bp = ac.createBiquadFilter();
      bp.type = "bandpass";
      bp.Q.value = 0.9;
      bp.frequency.setValueAtTime(500, when);
      bp.frequency.exponentialRampToValueAtTime(2200, when + 0.15);
      const gain = ac.createGain();
      gain.gain.setValueAtTime(gainVal, when);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + 0.18);
      src.connect(bp).connect(gain).connect(ac.destination);
      src.start(when);
      src.stop(when + 0.2);
    }

    // dual detuned oscillators for a fuller, less thin lead-synth tone
    function leadBlip(freq, duration, gainVal, when) {
      const ac = ensureCtx();
      const gain = ac.createGain();
      gain.gain.setValueAtTime(gainVal, when);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
      gain.connect(getMusicBus(ac));
      [-6, 6].forEach((detune) => {
        const osc = ac.createOscillator();
        osc.type = "square";
        osc.frequency.value = freq;
        osc.detune.value = detune;
        osc.connect(gain);
        osc.start(when);
        osc.stop(when + duration);
      });
    }

    function startSynthMusic() {
      const ac = ensureCtx();
      step = 0;
      musicTimer = setInterval(() => {
        const t = ac.currentTime + 0.02;
        const i = step % CHORD_ROOT.length;
        const chugDur = STEP_TIME * 0.72;
        if (GTR[i]) powerChord(CHORD_ROOT[i], chugDur, 0.05, t);
        if (BASS[i]) rockBass(CHORD_ROOT[i] / 2, chugDur, 0.09, t);
        if (LEAD[i]) leadBlip(LEAD[i], STEP_TIME * 0.9, 0.05, t);
        if (HAT[i]) hat(t, 0.022);
        if (KICK[i]) kick(t, 0.13);
        if (SNARE[i]) snare(t, 0.1);
        step++;
      }, STEP_TIME * 1000);
    }

    function startMusic() {
      stopMusic();
      const custom = CUSTOM_AUDIO.music;
      if (custom) {
        musicUsingCustom = true;
        custom.loop = true;
        custom.currentTime = 0;
        custom.volume = 0.7;
        custom.play().catch(() => {});
      } else {
        musicUsingCustom = false;
        startSynthMusic();
      }
    }

    function stopMusic() {
      if (musicTimer) clearInterval(musicTimer);
      musicTimer = null;
      if (CUSTOM_AUDIO.music) {
        CUSTOM_AUDIO.music.pause();
        CUSTOM_AUDIO.music.currentTime = 0;
      }
      musicUsingCustom = false;
    }

    // Menu-screen ambient loop (Assets/sfx_select.*). Plays from the moment
    // the menu is shown until the player presses "LET'S HAVE IT!". Browsers
    // block audio autoplay before any user gesture, so if the initial play()
    // is rejected, it's retried on the first click/key/touch anywhere on the
    // page. Silent (no synth fallback) if no custom clip was supplied.
    let menuMusicWanted = false;
    let menuMusicUnlockArmed = false;

    function armMenuMusicUnlock() {
      if (menuMusicUnlockArmed) return;
      menuMusicUnlockArmed = true;
      const retry = () => {
        menuMusicUnlockArmed = false;
        if (menuMusicWanted) startMenuMusic();
      };
      ["pointerdown", "keydown", "touchstart"].forEach((evt) =>
        document.addEventListener(evt, retry, { once: true })
      );
    }

    function startMenuMusic() {
      menuMusicWanted = true;
      const custom = CUSTOM_AUDIO.select;
      if (!custom) return;
      custom.loop = true;
      custom.volume = 0.6;
      custom.play().catch(() => armMenuMusicUnlock());
    }

    function stopMenuMusic() {
      menuMusicWanted = false;
      const custom = CUSTOM_AUDIO.select;
      if (custom) {
        custom.pause();
        custom.currentTime = 0;
      }
    }

    // <audio>.volume is capped at 1, so boosting a clip past its natural
    // level needs an actual Web Audio gain stage instead.
    function playWithGainBoost(node, gainValue) {
      try {
        const ac = ensureCtx();
        const source = ac.createMediaElementSource(node);
        const gain = ac.createGain();
        gain.gain.value = gainValue;
        source.connect(gain).connect(ac.destination);
      } catch (_) {
        // best effort — if routing isn't available, it just plays at 1x
      }
      node.play().catch(() => {});
    }

    // plays a custom clip if one was supplied, otherwise runs the synth
    // fallback. By default each trigger is cloned so overlapping triggers
    // (e.g. rapid hits) don't cut each other off; pass singleVoice for UI
    // sounds where a new trigger should interrupt any still-playing one
    // instead of layering on top of it. volume is a multiplier on the
    // clip's natural level (1 = unchanged); values above 1 use a gain
    // boost since native playback volume can't exceed 1.
    function play(key, synthFallback, { singleVoice = false, volume = 1 } = {}) {
      const custom = CUSTOM_AUDIO[key];
      if (custom) {
        if (singleVoice) {
          custom.pause();
          custom.currentTime = 0;
          custom.volume = Math.min(1, volume);
          custom.play().catch(() => {});
        } else {
          const node = custom.cloneNode(true);
          if (volume > 1) {
            playWithGainBoost(node, volume);
          } else {
            node.volume = volume;
            node.play().catch(() => {});
          }
        }
      } else {
        synthFallback();
      }
    }

    const sfxSelected = () => {
      stopMenuMusic();
      play("selected", () => {
        const ac = ensureCtx();
        [660, 880].forEach((f, i) => blip(f, 0.12, "square", 0.08, ac.currentTime + i * 0.07));
      }, { singleVoice: true });
    };

    const sfxThrow = () => play("throw", () => {
      const ac = ensureCtx();
      whoosh(ac.currentTime, 0.11);
      blip(300, 0.1, "sawtooth", 0.08, ac.currentTime);
      blip(180, 0.13, "sawtooth", 0.06, ac.currentTime + 0.06);
    });

    const sfxHit = () => play("hit", () => {
      const ac = ensureCtx();
      punch(ac.currentTime, 0.16);
    });

    const sfxJump = () => play("jump", () => {
      const ac = ensureCtx();
      const osc = ac.createOscillator();
      const gain = ac.createGain();
      osc.type = "square";
      osc.frequency.setValueAtTime(300, ac.currentTime);
      osc.frequency.exponentialRampToValueAtTime(500, ac.currentTime + 0.12);
      gain.gain.setValueAtTime(0.06, ac.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + 0.14);
      osc.connect(gain).connect(ac.destination);
      osc.start(ac.currentTime);
      osc.stop(ac.currentTime + 0.15);
    });

    const sfxCountBeep = () => play("countdown", () => {
      const ac = ensureCtx();
      blip(440, 0.15, "square", 0.08 * 0.7, ac.currentTime);
    }, { volume: 0.7 });

    const sfxFight = () => play("fight", () => {
      const ac = ensureCtx();
      [523, 659, 784, 1046].forEach((f, i) => blip(f, 0.18, "square", 0.09 * 1.5, ac.currentTime + i * 0.08));
    }, { volume: 1.5 });

    const sfxKO = () => play("ko", () => {
      const ac = ensureCtx();
      punch(ac.currentTime, 0.2);
      [392, 349, 294, 196].forEach((f, i) => blip(f, 0.35, "sawtooth", 0.1, ac.currentTime + 0.1 + i * 0.18));
    });

    const sfxWin = () => play("win", () => {
      const ac = ensureCtx();
      [523, 659, 784, 1046, 1318].forEach((f, i) => blip(f, 0.22, "square", 0.09, ac.currentTime + i * 0.11));
    });

    return { startMusic, stopMusic, startMenuMusic, stopMenuMusic, sfxSelected, sfxThrow, sfxHit, sfxJump, sfxCountBeep, sfxFight, sfxKO, sfxWin, ensureCtx };
  })();

  // Kick off the menu's ambient loop as soon as its custom clip (if any) is
  // ready — it plays until "LET'S HAVE IT!" is pressed.
  customAudioReady.then(() => AudioEngine.startMenuMusic());

  /* ============================================================
     INPUT
     ============================================================ */
  const keys = { ArrowLeft: false, ArrowRight: false, ArrowUp: false, Space: false };

  window.addEventListener("keydown", (e) => {
    const k = e.code === "Space" ? "Space" : e.key;
    if (k in keys) { keys[k] = true; e.preventDefault(); }
  });
  window.addEventListener("keyup", (e) => {
    const k = e.code === "Space" ? "Space" : e.key;
    if (k in keys) { keys[k] = false; e.preventDefault(); }
  });

  document.querySelectorAll(".pad-btn").forEach((btn) => {
    const k = btn.dataset.key;
    const set = (v) => (e) => { keys[k] = v; if (e) e.preventDefault(); };
    btn.addEventListener("pointerdown", set(true));
    btn.addEventListener("pointerup", set(false));
    btn.addEventListener("pointercancel", set(false));
    btn.addEventListener("pointerleave", set(false));
  });

  /* ---- arcade joystick: drag the stick to move/jump ---- */
  const joystickBase = document.getElementById("joystick-base");
  const joystickStick = document.getElementById("joystick-stick");
  if (joystickBase && joystickStick) {
    const JOY_RADIUS = 34; // max visual travel, px
    const DEAD_ZONE = 14; // px before a direction registers
    let joyActive = false;

    function moveStick(clientX, clientY) {
      const rect = joystickBase.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = clientX - cx;
      const dy = clientY - cy;
      const dist = Math.min(Math.hypot(dx, dy), JOY_RADIUS);
      const angle = Math.atan2(dy, dx);
      joystickStick.style.transition = "none";
      joystickStick.style.transform = `translate(-50%,-50%) translate(${Math.cos(angle) * dist}px, ${Math.sin(angle) * dist}px)`;

      keys.ArrowLeft = dx < -DEAD_ZONE;
      keys.ArrowRight = dx > DEAD_ZONE;
      keys.ArrowUp = dy < -DEAD_ZONE;
    }

    function resetStick() {
      keys.ArrowLeft = false;
      keys.ArrowRight = false;
      keys.ArrowUp = false;
      joystickStick.style.transition = "transform 0.12s ease";
      joystickStick.style.transform = "translate(-50%,-50%)";
    }

    // Pointer Events give one unified, robust code path for touch/mouse/pen,
    // and setPointerCapture keeps the drag tracking correctly even if the
    // finger slides off the joystick's visual bounds mid-drag.
    joystickBase.addEventListener("pointerdown", (e) => {
      joyActive = true;
      try { joystickBase.setPointerCapture(e.pointerId); } catch (err) {}
      moveStick(e.clientX, e.clientY);
      e.preventDefault();
    });
    joystickBase.addEventListener("pointermove", (e) => {
      if (!joyActive) return;
      moveStick(e.clientX, e.clientY);
      e.preventDefault();
    });
    const endJoystick = (e) => {
      if (!joyActive) return;
      joyActive = false;
      resetStick();
      if (e) e.preventDefault();
    };
    joystickBase.addEventListener("pointerup", endJoystick);
    joystickBase.addEventListener("pointercancel", endJoystick);
    joystickBase.addEventListener("lostpointercapture", endJoystick);
  }

  /* ============================================================
     ENTITIES
     ============================================================ */
  class Fighter {
    constructor(key, x, facing, isPlayer) {
      this.key = key;
      this.def = FIGHTERS[key];
      this.x = x;
      this.y = GROUND_Y - FIGHTER_H;
      this.vx = 0;
      this.vy = 0;
      this.facing = facing; // 1 = right, -1 = left
      this.health = MAX_HEALTH;
      this.onGround = true;
      this.isPlayer = isPlayer;
      this.throwCooldown = 0;
      this.hitStun = 0;
      this.state = "idle"; // idle | walk | jump | throw | hit | ko
      this.animT = 0;
      this.aiTimer = 0;
      this.aiThrowChance = 0;
    }

    get w() { return FIGHTER_W; }
    get h() { return FIGHTER_H; }

    rect() { return { x: this.x - this.w / 2, y: this.y, w: this.w, h: this.h }; }

    takeHit(dmg) {
      if (this.state === "ko") return;
      this.health = Math.max(0, this.health - dmg);
      this.hitStun = HIT_STUN;
      this.state = "hit";
      AudioEngine.sfxHit();
      if (this.health <= 0) { this.state = "ko"; this.koFlashStart = performance.now(); }
    }
  }

  class Projectile {
    constructor(owner, x, y, dir) {
      this.owner = owner;
      this.x = x;
      this.y = y;
      this.vx = dir * 274; // 322 * 0.85 — an additional 15% slower
      const scale = (owner.def && owner.def.projectileScale) || 1;
      this.w = 34 * scale;
      this.h = 28 * scale;
      this.dead = false;
      this.spin = 0;
      this.spinRate = (owner.def && owner.def.projectileSpinRate) || 10;
      this.exploding = false;
      this.explodeT = 0;
    }
  }

  /* ============================================================
     GAME STATE
     ============================================================ */
  let player, cpu, projectiles;
  let matchState = "idle"; // idle | countdown | fight | roundover | matchover
  let countdownVal = 3;
  let countdownTimer = 0;
  let timeLeft = ROUND_TIME;
  let lastTs = 0;
  let rafId = null;

  async function beginMatch(fighterKey, mapKey) {
    await loadAssetsFor(fighterKey, mapKey);

    GROUND_Y = CANVAS_H - (MAPS[mapKey].groundOffset ?? 46);

    const otherKey = fighterKey === "Binface" ? "Farrage" : "Binface";
    player = new Fighter(fighterKey, CANVAS_W * 0.28, 1, true);
    cpu = new Fighter(otherKey, CANVAS_W * 0.72, -1, false);
    projectiles = [];
    timeLeft = ROUND_TIME;
    timerEl.textContent = ROUND_TIME; // otherwise the HUD still shows the "99" placeholder during the countdown

    p1NameEl.textContent = FIGHTERS[fighterKey].label;
    p2NameEl.textContent = FIGHTERS[otherKey].label;
    roundLabelEl.textContent = MAPS[mapKey].label.toUpperCase();
    updateHealthBars();

    matchState = "countdown";
    countdownVal = 3;
    countdownTimer = 0;
    overlayText.textContent = "3";
    AudioEngine.sfxCountBeep();

    if (rafId) cancelAnimationFrame(rafId);
    lastTs = performance.now();
    rafId = requestAnimationFrame(loop);
  }

  function updateHealthBars() {
    const p1pct = (player.health / MAX_HEALTH) * 100;
    const p2pct = (cpu.health / MAX_HEALTH) * 100;
    p1HealthEl.style.width = `${p1pct}%`;
    p2HealthEl.style.width = `${p2pct}%`;
    p1HealthEl.classList.toggle("low", p1pct <= 25 && p1pct > 0);
    p2HealthEl.classList.toggle("low", p2pct <= 25 && p2pct > 0);
  }

  /* ----------------------------- MAIN LOOP ----------------------------- */
  function loop(ts) {
    const dt = Math.min(0.033, (ts - lastTs) / 1000);
    lastTs = ts;

    if (matchState === "countdown") updateCountdown(dt);
    else if (matchState === "fight") updateFight(dt);

    render();
    rafId = requestAnimationFrame(loop);
  }

  function updateCountdown(dt) {
    countdownTimer += dt;
    if (countdownTimer >= 1) {
      countdownTimer = 0;
      countdownVal--;
      if (countdownVal > 0) {
        overlayText.textContent = String(countdownVal);
        AudioEngine.sfxCountBeep();
      } else {
        overlayText.textContent = "FIGHT!";
        AudioEngine.sfxFight();
        AudioEngine.startMusic();
        matchState = "fight";
        setTimeout(() => { if (matchState === "fight") overlayText.textContent = ""; }, 700);
      }
    }
  }

  function updateFight(dt) {
    timeLeft -= dt;
    timerEl.textContent = Math.max(0, Math.ceil(timeLeft));

    handlePlayer(dt);
    handleAI(dt);
    handlePhysics(player, dt);
    handlePhysics(cpu, dt);
    handleProjectiles(dt);
    handleFighterCollision();
    updateHealthBars();

    if (player.health <= 0 || cpu.health <= 0 || timeLeft <= 0) {
      endRound();
    }
  }

  function handlePlayer(dt) {
    const f = player;
    if (f.hitStun > 0) { f.hitStun -= dt; return; }
    let moving = false;

    if (keys.ArrowLeft) { f.vx = -MOVE_SPEED; moving = true; }
    else if (keys.ArrowRight) { f.vx = MOVE_SPEED; moving = true; }
    else { f.vx = 0; }

    if (keys.ArrowUp && f.onGround) {
      f.vy = JUMP_VELOCITY;
      f.onGround = false;
      AudioEngine.sfxJump();
    }

    if (keys.Space && f.throwCooldown <= 0) {
      throwProjectile(f);
    }

    // fighters always face each other — no "turning your back" like classic SF2
    f.facing = cpu.x >= f.x ? 1 : -1;

    f.state = !f.onGround ? "jump" : moving ? "walk" : "idle";
    if (f.throwCooldown > THROW_COOLDOWN - 0.18) f.state = "throw";
  }

  function handleAI(dt) {
    const f = cpu;
    if (f.hitStun > 0) { f.hitStun -= dt; return; }
    f.aiTimer -= dt;

    const dist = Math.abs(player.x - f.x);
    f.facing = player.x >= f.x ? 1 : -1;

    if (f.aiTimer <= 0) {
      f.aiTimer = 0.25 + Math.random() * 0.35;
      const roll = Math.random();
      if (dist > 260) {
        f.vx = f.facing * MOVE_SPEED * 0.85; // approach
      } else if (dist < 120) {
        // too close: sometimes back off, sometimes throw
        f.vx = roll < 0.5 ? -f.facing * MOVE_SPEED * 0.6 : 0;
      } else {
        f.vx = 0;
        if (roll < 0.55 && f.throwCooldown <= 0) throwProjectile(f);
        else if (roll < 0.7 && f.onGround) { f.vy = JUMP_VELOCITY; f.onGround = false; AudioEngine.sfxJump(); }
      }
    }

    f.state = !f.onGround ? "jump" : Math.abs(f.vx) > 5 ? "walk" : "idle";
    if (f.throwCooldown > THROW_COOLDOWN - 0.18) f.state = "throw";
  }

  const WAIST_HEIGHT_ABOVE_GROUND = FIGHTER_H * 0.34; // dodgeable by a normal jump
  const HIGH_THROW_HEIGHT_ABOVE_GROUND = FIGHTER_H * 1.1; // clears a standing opponent's head entirely

  function throwProjectile(f) {
    f.throwCooldown = THROW_COOLDOWN;
    const px = f.x + f.facing * (f.w / 2 + 10);
    // thrown while grounded: waist height, jump clean over it.
    // thrown while airborne (jumping): sails high — doesn't hit anyone still on the ground.
    const py = f.onGround
      ? GROUND_Y - WAIST_HEIGHT_ABOVE_GROUND
      : GROUND_Y - HIGH_THROW_HEIGHT_ABOVE_GROUND;
    projectiles.push(new Projectile(f, px, py, f.facing));
    AudioEngine.sfxThrow();
  }

  function handlePhysics(f, dt) {
    f.throwCooldown = Math.max(0, f.throwCooldown - dt);
    f.x += f.vx * dt;
    f.x = Math.max(ARENA_MARGIN + f.w / 2, Math.min(CANVAS_W - ARENA_MARGIN - f.w / 2, f.x));

    if (!f.onGround) {
      f.vy += GRAVITY * dt;
      f.y += f.vy * dt;
      if (f.y >= GROUND_Y - f.h) {
        f.y = GROUND_Y - f.h;
        f.vy = 0;
        f.onGround = true;
      }
    }
    f.animT += dt;
  }

  function handleProjectiles(dt) {
    for (const p of projectiles) {
      if (p.exploding) {
        p.explodeT += dt;
        if (p.explodeT > 0.25) p.dead = true;
        continue; // frozen in place during the explosion burst
      }
      p.x += p.vx * dt;
      p.spin += dt * p.spinRate;
      const target = p.owner === player ? cpu : player;
      const tr = target.rect();
      if (p.x > tr.x && p.x < tr.x + tr.w && p.y > tr.y && p.y < tr.y + tr.h) {
        target.takeHit(8 + Math.random() * 4);
        p.dead = true;
      }
      if (p.x < -50 || p.x > CANVAS_W + 50) p.dead = true;
    }

    // bag-vs-bag: opposing thrown objects that meet in mid-air destroy each
    // other harmlessly instead of continuing on to hit a fighter
    for (let i = 0; i < projectiles.length; i++) {
      const a = projectiles[i];
      if (a.dead || a.exploding) continue;
      for (let j = i + 1; j < projectiles.length; j++) {
        const b = projectiles[j];
        if (b.dead || b.exploding || b.owner === a.owner) continue;
        const dx = Math.abs(a.x - b.x);
        const dy = Math.abs(a.y - b.y);
        if (dx < (a.w + b.w) / 2.4 && dy < (a.h + b.h) / 2.4) {
          a.exploding = true; a.explodeT = 0; a.vx = 0;
          b.exploding = true; b.explodeT = 0; b.vx = 0;
          AudioEngine.sfxHit();
          break;
        }
      }
    }

    projectiles = projectiles.filter((p) => !p.dead);
  }

  function handleFighterCollision() {
    // while either fighter is airborne, allow free horizontal pass-through
    // so a jump can carry you clean over your opponent's head and switch
    // sides — only resolve the "solid body" push-apart when both are grounded
    if (!player.onGround || !cpu.onGround) return;

    const minGap = FIGHTER_W * 0.55;
    const gap = cpu.x - player.x;
    if (Math.abs(gap) < minGap) {
      const push = (minGap - Math.abs(gap)) / 2;
      const dir = gap > 0 ? 1 : -1;
      player.x -= push * dir;
      cpu.x += push * dir;
    }
  }

  function endRound() {
    matchState = "matchover";
    AudioEngine.stopMusic();
    let title, sub, winner = null, loser = null;
    if (player.health <= 0 && cpu.health <= 0) { title = "DOUBLE K.O."; sub = "DRAW"; }
    else if (player.health <= 0) { title = "K.O."; sub = `${FIGHTERS[cpu.key].label} WINS`; AudioEngine.sfxKO(); winner = cpu; loser = player; }
    else if (cpu.health <= 0) { title = "K.O."; sub = `${FIGHTERS[player.key].label} WINS`; AudioEngine.sfxKO(); winner = player; loser = cpu; }
    else {
      title = "TIME UP";
      const playerWon = player.health >= cpu.health;
      sub = playerWon ? `${FIGHTERS[player.key].label} WINS` : `${FIGHTERS[cpu.key].label} WINS`;
      winner = playerWon ? player : cpu;
      loser = playerWon ? cpu : player;
    }

    // freeze-frame: victor strikes a win pose, the other stays on their
    // current (hit/ko) pose — render() keeps drawing this every frame
    // even though matchState is no longer "fight". Held for a few seconds
    // (classic SF2 lingers on the win pose) before cutting to the result screen.
    if (winner) { winner.state = "win"; winner.animT = 0; }
    if (loser && loser.state !== "ko") { loser.state = "hit"; }
    if (winner) setTimeout(() => AudioEngine.sfxWin(), 500);

    const FREEZE_MS = 2800;

    setTimeout(() => {
      resultTitle.textContent = title;
      resultSub.textContent = sub;

      resultBg.classList.remove("winner-binface", "winner-farrage", "show-deco");
      resultBgPhoto.style.display = "none";
      paperPhoto.style.display = "none";

      if (winner) {
        winnerPortrait.src = `Assets/${winner.key}_win.png`;
        resultBg.classList.add(winner.key === "Binface" ? "winner-binface" : "winner-farrage");
        resultBg.classList.add("show-deco");

        // real photo backdrop if supplied, else the SVG illustration underneath shows through
        resultBgPhoto.onload = () => { resultBgPhoto.style.display = "block"; resultBg.classList.remove("show-deco"); };
        resultBgPhoto.onerror = () => { resultBgPhoto.style.display = "none"; };
        resultBgPhoto.src = `Assets/ClactonFuture${winner.key}.png`;

        // newspaper front page — headline + the same future photo, so the
        // paper visually matches the backdrop behind it
        paperDate.textContent = "SPECIAL EDITION · CLACTON-ON-SEA";
        paperPhoto.onload = () => { paperPhoto.style.display = "block"; };
        paperPhoto.onerror = () => { paperPhoto.style.display = "none"; };
        paperPhoto.src = `Assets/ClactonFuture${winner.key}.png`;
        if (winner.key === "Binface") {
          paperHeadline.textContent = "BINFACE TRIUMPHANT!";
          paperSubhead.textContent = "Count Binface defeated Nigel Farage and saved the day, residents confirm.";
        } else {
          paperHeadline.textContent = "FARAGE VICTORIOUS!";
          paperSubhead.textContent = "Pier sold to oil interests overnight — campaigners warn of a smoke-choked coastline ahead for Clacton.";
        }
      } else {
        // double K.O. / draw — no clear winner, no themed backdrop or photo
        winnerPortrait.src = `Assets/${player.key}_hit.png`;
        paperDate.textContent = "SPECIAL EDITION · CLACTON-ON-SEA";
        paperHeadline.textContent = "CLACTON STUNNED!";
        paperSubhead.textContent = "Neither candidate prevails — the town's future hangs in the balance as both camps claim victory.";
      }

      screenGame.classList.add("hidden");
      screenResult.classList.remove("hidden");

      // SF2 arcade-style "continue?" countdown — auto-returns to the main
      // menu if the player doesn't pick Rematch / Main Menu in time
      stopContinueCountdown();
      let n = 9;
      continueNumEl.textContent = n;
      continueInterval = setInterval(() => {
        n--;
        continueNumEl.textContent = Math.max(0, n);
        if (n <= 0) {
          stopContinueCountdown();
          $("#menu-btn").click();
        }
      }, 1000);
    }, FREEZE_MS);
  }

  /* ============================================================
     RENDERING
     ============================================================ */
  function render() {
    // resize canvas element pixel size to CSS size for crispness on hi-DPI
    ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);
    drawBackground();
    if (player) {
      drawFighter(player);
      drawFighter(cpu);
      projectiles.forEach(drawProjectile);
    }
  }

  function drawBackground() {
    if (ASSETS.bg) {
      ctx.drawImage(ASSETS.bg, 0, 0, CANVAS_W, CANVAS_H);
    } else {
      const mapKey = selectedMap || "Pier";
      const tint = MAPS[mapKey].tint;
      const grad = ctx.createLinearGradient(0, 0, 0, CANVAS_H);
      grad.addColorStop(0, tint);
      grad.addColorStop(1, "#0b0c1a");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);
      ctx.fillStyle = "rgba(255,255,255,0.06)";
      for (let i = 0; i < 6; i++) {
        ctx.fillRect((i * 180 + 40) % CANVAS_W, 40 + (i % 3) * 30, 40, 200);
      }
      ctx.fillStyle = "#000";
      ctx.font = "bold 20px monospace";
      ctx.textAlign = "center";
      ctx.fillText(`(add Assets/${mapKey}.png for the real backdrop)`, CANVAS_W / 2, 30);
    }
    // subtle ground contact line (no more big flat dark band)
    ctx.strokeStyle = "rgba(255,255,255,0.15)";
    ctx.beginPath();
    ctx.moveTo(0, GROUND_Y);
    ctx.lineTo(CANVAS_W, GROUND_Y);
    ctx.stroke();
  }

  function drawFighter(f) {
    const bob = f.state === "walk" ? Math.sin(f.animT * 10) * 6 : 0;
    const lean = f.state === "throw" ? f.facing * 10 : 0;
    const drawX = f.x - f.w / 2;
    const drawY = f.y + bob;

    ctx.save();
    ctx.translate(drawX + f.w / 2 + lean, drawY + f.h / 2);
    const charOverride = FACING_OVERRIDE[f.key] || 1;
    const poseOverride = (POSE_FACING_OVERRIDE[f.key] && POSE_FACING_OVERRIDE[f.key][f.state]) || 1;
    const shouldFlip = (f.facing * charOverride * poseOverride) < 0;
    if (shouldFlip) ctx.scale(-1, 1);
    ctx.translate(-f.w / 2, -f.h / 2);

    if (f.state === "hit") {
      ctx.filter = "brightness(1.6) saturate(0)";
    }

    const img = poseFor(f);
    if (img) {
      // preserve the sprite's own aspect ratio inside the fighter's box,
      // anchored to the ground so different poses don't jump around
      const scale = Math.min(f.w / img.width, f.h / img.height);
      const dw = img.width * scale;
      const dh = img.height * scale;
      ctx.drawImage(img, (f.w - dw) / 2, f.h - dh, dw, dh);
    } else {
      drawPlaceholder(f);
    }
    ctx.restore();

    // KO flash — tightly bounded to this fighter's own box only (no padding,
    // so it can't visually bleed onto a nearby winner) and fades out over
    // about a second instead of sitting there as a static tint indefinitely
    if (f.state === "ko") {
      const elapsed = (performance.now() - (f.koFlashStart || performance.now())) / 1000;
      const a = Math.max(0, 0.22 - elapsed * 0.18);
      if (a > 0) {
        ctx.fillStyle = `rgba(255,60,60,${a.toFixed(3)})`;
        ctx.fillRect(drawX, drawY, f.w, f.h);
      }
    }
  }

  // Generic stylised placeholder so the game is playable without art assets.
  function drawPlaceholder(f) {
    const w = f.w, h = f.h;
    const body = f.def.color;
    ctx.fillStyle = "rgba(0,0,0,0.25)";
    ctx.beginPath();
    ctx.ellipse(w / 2, h + 6, w * 0.4, 10, 0, 0, Math.PI * 2);
    ctx.fill();

    // legs
    ctx.fillStyle = "#222";
    ctx.fillRect(w * 0.28, h * 0.62, w * 0.18, h * 0.36);
    ctx.fillRect(w * 0.54, h * 0.62, w * 0.18, h * 0.36);

    // torso
    ctx.fillStyle = body;
    ctx.fillRect(w * 0.22, h * 0.28, w * 0.56, h * 0.4);

    // arms
    ctx.fillStyle = body;
    ctx.fillRect(w * 0.05, h * 0.32, w * 0.16, h * 0.3);
    ctx.fillRect(w * 0.79, h * 0.32, w * 0.16, h * 0.3);

    // head
    ctx.fillStyle = "#e7c9a3";
    ctx.beginPath();
    ctx.arc(w / 2, h * 0.18, w * 0.16, 0, Math.PI * 2);
    ctx.fill();

    if (f.key === "Binface") {
      // bin-lid "cap" + bin body motif
      ctx.fillStyle = f.def.capColor;
      ctx.beginPath();
      ctx.arc(w / 2, h * 0.1, w * 0.19, Math.PI, 0);
      ctx.fill();
      ctx.fillStyle = "#0e5c33";
      ctx.fillRect(w * 0.3, h * 0.05, w * 0.4, h * 0.06);
      ctx.strokeStyle = "#0e5c33";
      ctx.lineWidth = 4;
      ctx.strokeRect(w * 0.24, h * 0.29, w * 0.52, h * 0.38);
    } else {
      // generic suit + tie silhouette (not a likeness — placeholder only)
      ctx.fillStyle = "#c94a4a";
      ctx.beginPath();
      ctx.moveTo(w / 2 - 5, h * 0.3);
      ctx.lineTo(w / 2 + 5, h * 0.3);
      ctx.lineTo(w / 2, h * 0.55);
      ctx.fill();
      ctx.strokeStyle = "#1c2f45";
      ctx.lineWidth = 3;
      ctx.strokeRect(w * 0.24, h * 0.29, w * 0.52, h * 0.38);
    }

    // throw pose accent
    if (f.state === "throw") {
      ctx.fillStyle = f.def.projectileColor;
      ctx.beginPath();
      ctx.arc(w * 0.95, h * 0.42, 10, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawProjectile(p) {
    if (p.exploding) {
      const t = p.explodeT / 0.25; // 0..1
      const r = 6 + t * 34;
      const alpha = 1 - t;
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = "#ffe066";
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.arc(0, 0, r, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillStyle = "#ff9d1e";
      const spikes = 8;
      for (let i = 0; i < spikes; i++) {
        const a = (i / spikes) * Math.PI * 2;
        const len = r * 0.7;
        ctx.beginPath();
        ctx.arc(Math.cos(a) * len, Math.sin(a) * len, 4 * (1 - t), 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
      return;
    }

    const set = ASSETS.poses[p.owner.key];
    const img = set && set.projectile;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.spin);
    if (img) {
      const scale = Math.min(p.w * 1.8 / img.width, p.h * 1.8 / img.height);
      ctx.drawImage(img, -(img.width * scale) / 2, -(img.height * scale) / 2, img.width * scale, img.height * scale);
    } else {
      ctx.fillStyle = p.owner.def.projectileColor;
      ctx.beginPath();
      ctx.ellipse(0, 0, p.w / 2, p.h / 2, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "rgba(0,0,0,0.4)";
      ctx.stroke();
    }
    ctx.restore();
  }

  /* Kick off first paint on menu (draws nothing but avoids blank canvas flash) */
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);
})();
