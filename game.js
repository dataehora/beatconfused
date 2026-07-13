"use strict";

// ── Constants ──────────────────────────────────────────────────────────────────
const CANVAS_W       = 800;
const CANVAS_H       = 450;
const GROUND_Y       = 365;   // y-coord of the stage floor surface
const GRAVITY        = 0.55;
const JUMP_VEL       = -13.5;
const MOVE_SPEED     = 4.5;
const PROJ_SPEED     = 9;
const MAX_HP         = 100;
const PROJ_DAMAGE    = 25;
const ATTACK_COOLDOWN = 72;   // frames between allowed attacks (~1.2 s at 60 fps)
const HURT_FRAMES    = 22;
const ROUND_SECONDS  = 99;
const AI_INTERVAL    = 48;    // frames between AI decisions

// ── DOM refs ───────────────────────────────────────────────────────────────────
const canvas        = document.getElementById("game-canvas");
const ctx           = canvas.getContext("2d");
const p1Fill        = document.getElementById("p1-health-fill");
const p2Fill        = document.getElementById("p2-health-fill");
const timerEl       = document.getElementById("round-timer");
const overlayEl     = document.getElementById("game-overlay");
const overlayTitle  = document.getElementById("overlay-title");
const overlaySub    = document.getElementById("overlay-subtitle");
const restartBtn    = document.getElementById("restart-btn");

// ── Game state ─────────────────────────────────────────────────────────────────
let keys          = {};
let fighters      = [];
let projectiles   = [];
let particles     = [];
let timerSecs     = ROUND_SECONDS;
let timerInterval = null;
let rafId         = null;
let gamePhase     = "idle";   // idle | intro | fight | end
let introTimer    = 0;
let bgCache       = null;
let frameCount    = 0;

// ── Fighter ────────────────────────────────────────────────────────────────────
class Fighter {
  constructor(x, isPlayer) {
    this.x          = x;
    this.y          = GROUND_Y;
    this.vx         = 0;
    this.vy         = 0;
    this.hp         = MAX_HP;
    this.facing     = isPlayer ? 1 : -1;
    this.isPlayer   = isPlayer;
    this.state      = "idle"; // idle | run | jump | attack | hurt | ko
    this.stateTimer = 0;
    this.cooldown   = 0;
    this.af         = 0;      // animation frame index
    this.aTimer     = 0;
    this.aiTimer    = 0;
    this.width      = 52;
    this.height     = 112;
  }

  get grounded() { return this.y >= GROUND_Y; }

  update() {
    // animation tick
    if (++this.aTimer >= 8) { this.aTimer = 0; this.af = (this.af + 1) % 4; }

    if (this.cooldown   > 0) this.cooldown--;
    if (this.stateTimer > 0) this.stateTimer--;

    if (this.state === "ko") { this.applyPhysics(); return; }

    if (this.isPlayer) {
      this.handlePlayer();
    } else {
      this.handleAI();
    }

    this.applyPhysics();

    // face opponent
    const opp = fighters.find(f => f !== this);
    if (opp && this.state === "idle") {
      this.facing = opp.x > this.x ? 1 : -1;
    }
  }

  applyPhysics() {
    if (!this.grounded) this.vy += GRAVITY;
    this.x += this.vx;
    this.y += this.vy;
    if (this.y > GROUND_Y) {
      this.y  = GROUND_Y;
      this.vy = 0;
      if (this.state === "jump") this.state = "idle";
    }
    this.x  = Math.max(30, Math.min(CANVAS_W - 30, this.x));
    if (this.grounded && this.state !== "run") this.vx *= 0.65;
  }

  handlePlayer() {
    if (this.state === "hurt" && this.stateTimer > 0) return;

    const ml = keys["ArrowLeft"];
    const mr = keys["ArrowRight"];
    const mj = keys["ArrowUp"];
    const ma = keys[" "] || keys["Space"];

    if (ml) {
      this.vx = -MOVE_SPEED;
      this.facing = -1;
      if (this.grounded && this.state !== "attack") this.state = "run";
    } else if (mr) {
      this.vx = MOVE_SPEED;
      this.facing = 1;
      if (this.grounded && this.state !== "attack") this.state = "run";
    } else {
      this.vx *= 0.65;
      if (this.grounded && this.state === "run") this.state = "idle";
    }

    if (mj && this.grounded) {
      this.vy    = JUMP_VEL;
      this.state = "jump";
      keys["ArrowUp"] = false;
    }

    if (ma && this.cooldown === 0) {
      this.fire();
      this.state      = "attack";
      this.stateTimer = 28;
      this.cooldown   = ATTACK_COOLDOWN;
      keys[" "]     = false;
      keys["Space"] = false;
    }
  }

  handleAI() {
    this.aiTimer++;
    const opp = fighters.find(f => f !== this);
    if (!opp) return;

    const dx   = opp.x - this.x;
    const dist = Math.abs(dx);
    this.facing = dx > 0 ? 1 : -1;

    if (this.state === "hurt" && this.stateTimer > 0) return;

    if (this.aiTimer % AI_INTERVAL === 0) {
      const r = Math.random();
      if (r < 0.25 && dist > 260 && this.grounded) {
        this.vx    = this.facing * MOVE_SPEED * 0.85;
        this.state = "run";
      } else if (r < 0.40 && dist < 130 && this.grounded) {
        this.vx    = -this.facing * MOVE_SPEED * 0.65;
        this.state = "run";
      } else if (r < 0.54 && this.grounded) {
        this.vy    = JUMP_VEL * 0.88;
        this.state = "jump";
      } else if (r < 0.84 && this.cooldown === 0) {
        this.fire();
        this.state      = "attack";
        this.stateTimer = 28;
        this.cooldown   = ATTACK_COOLDOWN;
      } else {
        this.vx *= 0.5;
        if (this.grounded) this.state = "idle";
      }
    }

    if (this.grounded && this.state === "run") {
      this.vx += this.facing * 0.25;
      this.vx  = Math.max(-MOVE_SPEED, Math.min(MOVE_SPEED, this.vx));
    }
  }

  fire() {
    const px = this.x + this.facing * 32;
    const py = this.y - 68;
    projectiles.push(new Projectile(px, py, this.facing * PROJ_SPEED, this.isPlayer));
    spawnFireParticles(px, py, this.isPlayer);
  }

  takeDamage(amount) {
    if ((this.state === "hurt" && this.stateTimer > 0) || this.state === "ko") return;
    this.hp = Math.max(0, this.hp - amount);
    this.state      = "hurt";
    this.stateTimer = HURT_FRAMES;
    this.vx = -this.facing * 3;
    if (this.hp <= 0) {
      this.state = "ko";
      this.vy   = -4;
    }
  }

  hitbox() {
    return { x: this.x - this.width / 2, y: this.y - this.height, w: this.width, h: this.height };
  }
}

// ── Projectile ─────────────────────────────────────────────────────────────────
class Projectile {
  constructor(x, y, vx, fromPlayer) {
    this.x          = x;
    this.y          = y;
    this.vx         = vx;
    this.fromPlayer = fromPlayer;
    this.active     = true;
    this.af         = 0;
    this.aTimer     = 0;
    this.r          = 20;
  }

  update() {
    this.x += this.vx;
    if (++this.aTimer >= 5) { this.aTimer = 0; this.af = (this.af + 1) % 6; }
    if (this.x < -80 || this.x > CANVAS_W + 80) this.active = false;
  }

  hitbox() {
    return { x: this.x - this.r, y: this.y - this.r, w: this.r * 2, h: this.r * 2 };
  }
}

// ── Particle ───────────────────────────────────────────────────────────────────
class Particle {
  constructor(x, y, vx, vy, color, size, life) {
    Object.assign(this, { x, y, vx, vy, color, size, life, maxLife: life });
  }
  update() {
    this.x  += this.vx;
    this.y  += this.vy;
    this.vy += 0.3;
    this.life--;
  }
  draw() {
    const a = this.life / this.maxLife;
    ctx.globalAlpha = a;
    ctx.fillStyle   = this.color;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size * a, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  }
}

function spawnFireParticles(x, y, isPlayer) {
  const color = isPlayer ? "#88cc20" : "#888888";
  for (let i = 0; i < 8; i++) {
    const a = Math.random() * Math.PI * 2;
    const s = 1.5 + Math.random() * 3.5;
    particles.push(new Particle(x, y, Math.cos(a)*s, Math.sin(a)*s, color, 2+Math.random()*4, 18+Math.random()*12));
  }
}

function spawnHitParticles(x, y) {
  for (let i = 0; i < 14; i++) {
    const a = Math.random() * Math.PI * 2;
    const s = 2 + Math.random() * 5;
    const c = Math.random() > 0.5 ? "#ff5500" : "#ffcc00";
    particles.push(new Particle(x, y, Math.cos(a)*s, Math.sin(a)*s - 2, c, 2+Math.random()*5, 22+Math.random()*18));
  }
}

// ── Collision helper ───────────────────────────────────────────────────────────
function rectsOverlap(a, b) {
  return a.x < b.x+b.w && a.x+a.w > b.x && a.y < b.y+b.h && a.y+a.h > b.y;
}

// ── Background (offscreen cached) ─────────────────────────────────────────────
function prerenderBg() {
  const oc = document.createElement("canvas");
  oc.width  = CANVAS_W;
  oc.height = CANVAS_H;
  const ox = oc.getContext("2d");
  renderBg(ox);
  bgCache = oc;
}

function renderBg(ox) {
  // Dark board backing
  ox.fillStyle = "#180e08";
  ox.fillRect(0, 0, CANVAS_W, CANVAS_H);

  // Patchwork photo panels – five snapshots of Clacton Pier
  const panels = [
    { x: 8,   y: 8,   w: 386, h: 216, rot: -1.3, fn: panelSky      },
    { x: 406, y: 10,  w: 388, h: 213, rot:  1.1, fn: panelPavilion },
    { x: 6,   y: 232, w: 258, h: 148, rot: -0.8, fn: panelSea      },
    { x: 272, y: 236, w: 258, h: 143, rot:  0.7, fn: panelArcade   },
    { x: 538, y: 230, w: 254, h: 150, rot: -1.0, fn: panelCrowd    },
  ];

  panels.forEach((p) => {
    const cx = p.x + p.w / 2;
    const cy = p.y + p.h / 2;
    ox.save();
    ox.translate(cx, cy);
    ox.rotate((p.rot * Math.PI) / 180);

    // Drop shadow
    ox.shadowColor   = "rgba(0,0,0,0.75)";
    ox.shadowBlur    = 10;
    ox.shadowOffsetX = 4;
    ox.shadowOffsetY = 4;

    // Cream photo border
    ox.fillStyle = "#f2ecda";
    ox.fillRect(-p.w/2-9, -p.h/2-9, p.w+18, p.h+18);

    ox.shadowColor = "transparent";

    // Clip and draw panel content
    ox.save();
    ox.beginPath();
    ox.rect(-p.w/2, -p.h/2, p.w, p.h);
    ox.clip();
    p.fn(ox, -p.w/2, -p.h/2, p.w, p.h);
    ox.restore();

    ox.restore();
  });

  // Radial vignette
  const vig = ox.createRadialGradient(CANVAS_W/2, CANVAS_H/2, 180, CANVAS_W/2, CANVAS_H/2, 520);
  vig.addColorStop(0, "rgba(0,0,0,0)");
  vig.addColorStop(1, "rgba(0,0,0,0.55)");
  ox.fillStyle = vig;
  ox.fillRect(0, 0, CANVAS_W, CANVAS_H);
}

// Panel 1 – blue sky, pier silhouette, seagulls, Union Jack bunting
function panelSky(ox, x, y, w, h) {
  const sky = ox.createLinearGradient(x, y, x, y+h);
  sky.addColorStop(0,   "#5599d4");
  sky.addColorStop(0.55,"#8ec4e0");
  sky.addColorStop(1,   "#bfddf2");
  ox.fillStyle = sky;
  ox.fillRect(x, y, w, h);

  drawCloud(ox, x+55,  y+36, 92, 32);
  drawCloud(ox, x+240, y+18, 72, 26);
  drawCloud(ox, x+318, y+55, 54, 20);

  // distant sea
  ox.fillStyle = "#3a7898";
  ox.fillRect(x, y+h*0.72, w, h*0.28);

  // pier horizon line
  ox.fillStyle = "#988060";
  ox.fillRect(x+10, y+h*0.70, w-20, 7);

  // small pavilion silhouette
  ox.fillStyle = "#786858";
  ox.fillRect(x+w-112, y+h*0.52, 82, h*0.20);
  ox.beginPath();
  ox.moveTo(x+w-116, y+h*0.52);
  ox.lineTo(x+w-71,  y+h*0.39);
  ox.lineTo(x+w-26,  y+h*0.52);
  ox.closePath();
  ox.fill();

  // seagulls
  ox.strokeStyle = "#1a2030";
  ox.lineWidth   = 2;
  [[x+88,y+82],[x+168,y+62],[x+225,y+96],[x+145,y+110]].forEach(([sx,sy]) => {
    ox.beginPath();
    ox.moveTo(sx-12,sy);
    ox.quadraticCurveTo(sx, sy-8, sx+12, sy);
    ox.stroke();
  });

  drawBunting(ox, x+12, y+28, x+w-12, y+52, 12);

  ox.fillStyle = "rgba(255,200,80,0.07)";
  ox.fillRect(x, y, w, h);
}

// Panel 2 – Victorian pier pavilion building
function panelPavilion(ox, x, y, w, h) {
  const sky = ox.createLinearGradient(x, y, x, y+h*0.55);
  sky.addColorStop(0, "#6aaade");
  sky.addColorStop(1, "#9ec8e8");
  ox.fillStyle = sky;
  ox.fillRect(x, y, w, h*0.55);

  const by = y + h*0.18;

  // façade
  ox.fillStyle = "#f2ead8";
  ox.fillRect(x+15, by, w-30, h);

  // gable roof
  ox.fillStyle = "#c44028";
  ox.beginPath();
  ox.moveTo(x+8,    by+5);
  ox.lineTo(x+w/2,  by-44);
  ox.lineTo(x+w-8,  by+5);
  ox.closePath();
  ox.fill();

  // cornice
  ox.fillStyle = "#8a1818";
  ox.fillRect(x+8, by+4, w-16, 9);

  // scalloped top trim
  for (let i = 0; i < 7; i++) {
    ox.fillStyle = "#c44028";
    ox.beginPath();
    ox.arc(x+25 + i*((w-50)/6), by+3, 6, Math.PI, 0);
    ox.fill();
  }

  // arched windows
  const ww=44, wh=65;
  const wy = by+24;
  [x+40, x+w/2-ww/2, x+w-40-ww].forEach(wx => {
    ox.fillStyle = "#4880b8";
    ox.beginPath();
    ox.arc(wx+ww/2, wy, ww/2, Math.PI, 0);
    ox.fill();
    ox.fillRect(wx, wy, ww, wh-ww/2);
    ox.strokeStyle = "#d8c8a0";
    ox.lineWidth   = 3;
    ox.beginPath();
    ox.arc(wx+ww/2, wy, ww/2, Math.PI, 0);
    ox.moveTo(wx,    wy);
    ox.lineTo(wx,    wy+wh-ww/2);
    ox.moveTo(wx+ww, wy);
    ox.lineTo(wx+ww, wy+wh-ww/2);
    ox.stroke();
    ox.strokeStyle = "rgba(255,255,255,0.4)";
    ox.lineWidth   = 1.5;
    ox.beginPath();
    ox.moveTo(wx+ww/2, wy-ww/2);
    ox.lineTo(wx+ww/2, wy+wh-ww/2);
    ox.stroke();
  });

  // AMUSEMENTS sign
  const sy = by+104;
  ox.fillStyle   = "#cc3300";
  ox.fillRect(x+20, sy, w-40, 37);
  ox.strokeStyle = "#ff6600";
  ox.lineWidth   = 2;
  ox.strokeRect(x+20, sy, w-40, 37);
  ox.fillStyle   = "#ffee00";
  ox.font        = "bold 17px Arial,sans-serif";
  ox.textAlign   = "center";
  ox.fillText("AMUSEMENTS", x+w/2, sy+26);

  // building title
  ox.fillStyle = "#2a1a0a";
  ox.font      = "bold 14px Arial,sans-serif";
  ox.textAlign = "center";
  ox.fillText("CLACTON PIER", x+w/2, by-12);

  // entry door
  ox.fillStyle = "#4a3015";
  ox.fillRect(x+w/2-22, by+104, 44, 66);
  ox.fillStyle = "#8a5020";
  ox.fillRect(x+w/2-18, by+106, 17, 62);
  ox.fillRect(x+w/2+2,  by+106, 16, 62);

  ox.fillStyle = "rgba(20,40,120,0.06)";
  ox.fillRect(x, y, w, h);
}

// Panel 3 – sea with pier support legs
function panelSea(ox, x, y, w, h) {
  ox.fillStyle = "#7a5c1e";
  ox.fillRect(x, y, w, 22);
  ox.fillStyle = "#5a4010";
  ox.fillRect(x, y+22, w, 4);

  const seaG = ox.createLinearGradient(x, y+26, x, y+h);
  seaG.addColorStop(0,   "#2a7898");
  seaG.addColorStop(0.5, "#1a5878");
  seaG.addColorStop(1,   "#0f3858");
  ox.fillStyle = seaG;
  ox.fillRect(x, y+26, w, h-26);

  const cols = 5;
  for (let i = 0; i < cols; i++) {
    const cx = x + 22 + i*((w-44)/(cols-1));
    ox.fillStyle = "#4a3818";
    ox.fillRect(cx-7, y+22, 14, h-22);
    if (i < cols-1) {
      const nx = x + 22 + (i+1)*((w-44)/(cols-1));
      ox.strokeStyle = "#3a2810";
      ox.lineWidth   = 3;
      ox.beginPath();
      ox.moveTo(cx+7, y+30); ox.lineTo(nx-7, y+h*0.7); ox.stroke();
      ox.beginPath();
      ox.moveTo(nx-7, y+30); ox.lineTo(cx+7, y+h*0.7); ox.stroke();
    }
  }

  ox.strokeStyle = "rgba(255,255,255,0.32)";
  ox.lineWidth   = 2;
  for (let w2=0; w2<5; w2++) {
    const wy = y+50 + w2*28;
    ox.beginPath();
    for (let wx=x; wx<=x+w; wx+=4) {
      const yo = Math.sin((wx-x)*0.12+w2*0.8)*4;
      wx===x ? ox.moveTo(wx,wy+yo) : ox.lineTo(wx,wy+yo);
    }
    ox.stroke();
  }

  ox.fillStyle = "rgba(0,40,110,0.13)";
  ox.fillRect(x, y, w, h);
}

// Panel 4 – amusement arcade neon signs
function panelArcade(ox, x, y, w, h) {
  ox.fillStyle = "#100808";
  ox.fillRect(x, y, w, h);

  const signs = [
    { text:"2p SLOTS",    fg:"#ff5500", bg:"#220a00" },
    { text:"PRIZE BINGO", fg:"#00ff88", bg:"#001a0e" },
    { text:"FISH & CHIPS",fg:"#ffdd00", bg:"#191200" },
    { text:"DODGEMS",     fg:"#cc66ff", bg:"#150020" },
  ];

  const sh = (h-16) / 4;
  signs.forEach((s, i) => {
    const sx = x+8, sy = y+5+i*(sh+2), sw = w-16;
    ox.fillStyle = s.bg;
    ox.fillRect(sx, sy, sw, sh);
    ox.shadowColor = s.fg;
    ox.shadowBlur  = 6;
    ox.strokeStyle = s.fg;
    ox.lineWidth   = 2;
    ox.strokeRect(sx, sy, sw, sh);
    ox.shadowBlur  = 0;
    const fs = Math.max(11, Math.min(18, sh*0.54));
    ox.fillStyle = s.fg;
    ox.font      = `bold ${fs}px Arial,sans-serif`;
    ox.textAlign = "center";
    ox.fillText(s.text, sx+sw/2, sy+sh*0.72);
  });

  ox.fillStyle = "rgba(200,80,0,0.06)";
  ox.fillRect(x, y, w, h);
}

// Panel 5 – crowd silhouettes, bunting, distant sea
function panelCrowd(ox, x, y, w, h) {
  const sky = ox.createLinearGradient(x, y, x, y+h*0.55);
  sky.addColorStop(0, "#5090c8");
  sky.addColorStop(1, "#88b8d8");
  ox.fillStyle = sky;
  ox.fillRect(x, y, w, h*0.55);

  ox.fillStyle = "#2a6880";
  ox.fillRect(x, y+h*0.52, w, h*0.12);

  drawBunting(ox, x+5, y+26, x+w-5, y+42, 9);

  // crowd silhouettes
  const cy0 = y+h*0.76;
  ox.fillStyle = "#1a1820";
  for (let i=0; i<8; i++) {
    const cx = x+(i+0.5)*(w/8);
    const dv = (i%3)*8;
    ox.fillRect(cx-9, cy0-42+dv, 18, 34);
    ox.beginPath();
    ox.arc(cx, cy0-50+dv, 10, 0, Math.PI*2);
    ox.fill();
    ox.strokeStyle = "#1a1820";
    ox.lineWidth   = 3;
    ox.beginPath(); ox.moveTo(cx-4,cy0-40+dv); ox.lineTo(cx-18,cy0-66+dv); ox.stroke();
    ox.beginPath(); ox.moveTo(cx+4,cy0-40+dv); ox.lineTo(cx+15,cy0-64+dv); ox.stroke();
  }

  const fg = ox.createLinearGradient(x, cy0, x, y+h);
  fg.addColorStop(0, "#7a6030");
  fg.addColorStop(1, "#5a4020");
  ox.fillStyle = fg;
  ox.fillRect(x, cy0, w, h-(cy0-y));
}

// ── Background helpers ─────────────────────────────────────────────────────────
function drawCloud(ox, x, y, w, h) {
  ox.fillStyle = "rgba(255,255,255,0.91)";
  ox.beginPath();
  ox.arc(x+w*0.30, y+h*0.50, h*0.55, 0, Math.PI*2);
  ox.arc(x+w*0.55, y+h*0.35, h*0.65, 0, Math.PI*2);
  ox.arc(x+w*0.78, y+h*0.50, h*0.50, 0, Math.PI*2);
  ox.arc(x+w*0.50, y+h*0.65, h*0.45, 0, Math.PI*2);
  ox.fill();
}

function drawBunting(ox, x1, y1, x2, y2, count) {
  const cols = ["#cc0000","#ffffff","#0033cc"];
  ox.strokeStyle = "#888";
  ox.lineWidth   = 1;
  ox.beginPath();
  for (let i=0; i<=count; i++) {
    const t  = i/count;
    const bx = x1+t*(x2-x1);
    const by = y1+t*(y2-y1) + Math.sin(t*Math.PI)*14;
    i===0 ? ox.moveTo(bx,by) : ox.lineTo(bx,by);
  }
  ox.stroke();
  for (let i=0; i<count; i++) {
    const t  = (i+0.5)/count;
    const bx = x1+t*(x2-x1);
    const by = y1+t*(y2-y1) + Math.sin(t*Math.PI)*14;
    ox.fillStyle = cols[i%cols.length];
    ox.beginPath();
    ox.moveTo(bx-7, by);
    ox.lineTo(bx+7, by);
    ox.lineTo(bx,   by+10);
    ox.closePath();
    ox.fill();
  }
}

// ── Stage floor (pier deck) ────────────────────────────────────────────────────
function drawFloor() {
  const fy = GROUND_Y;
  const fh = CANVAS_H - fy;

  const pg = ctx.createLinearGradient(0, fy, 0, CANVAS_H);
  pg.addColorStop(0, "#6a4c18");
  pg.addColorStop(1, "#3a2808");
  ctx.fillStyle = pg;
  ctx.fillRect(0, fy, CANVAS_W, fh);

  // plank grooves
  ctx.strokeStyle = "#3a2808";
  ctx.lineWidth   = 2;
  for (let i=1; i<7; i++) {
    ctx.beginPath();
    ctx.moveTo(0, fy+i*(fh/7));
    ctx.lineTo(CANVAS_W, fy+i*(fh/7));
    ctx.stroke();
  }

  // railing beam
  ctx.fillStyle = "#4a3010";
  ctx.fillRect(0, fy-12, CANVAS_W, 10);

  // railing posts
  ctx.fillStyle = "#3a2008";
  for (let px=10; px<CANVAS_W; px+=55) {
    ctx.fillRect(px-3, fy-28, 6, 28);
  }

  // edge shadow
  ctx.fillStyle = "rgba(0,0,0,0.35)";
  ctx.fillRect(0, fy, CANVAS_W, 14);

  // stage name plate
  const nw=264, nh=28;
  const nx=(CANVAS_W-nw)/2, ny=CANVAS_H-nh-4;
  ctx.fillStyle   = "#100800";
  ctx.fillRect(nx, ny, nw, nh);
  ctx.strokeStyle = "#c8a020";
  ctx.lineWidth   = 2;
  ctx.strokeRect(nx, ny, nw, nh);
  ctx.fillStyle   = "#c8a020";
  ctx.font        = 'bold 13px "Courier New",monospace';
  ctx.textAlign   = "center";
  ctx.fillText("✦  CLACTON PIER  ✧  ESSEX  ✦", CANVAS_W/2, ny+19);
}

// ── Character drawing ──────────────────────────────────────────────────────────

function drawFarage(f) {
  const { x, y, facing: fc, state, af } = f;
  ctx.save();
  ctx.translate(x, y);
  if (fc === -1) ctx.scale(-1, 1);

  const walk  = state==="run"    ? Math.sin(af*1.6)*5 : 0;
  const lean  = state==="attack" ? 9 : 0;
  const shake = state==="hurt"   ? (Math.random()-0.5)*6 : 0;
  const bx    = lean + shake;

  // ── Legs ──
  ctx.fillStyle = "#1a2a4a";
  const ll = state==="run" ? Math.sin(af*1.6)*12 : 0;
  // left leg
  ctx.save(); ctx.translate(-9,-14); ctx.rotate(ll*Math.PI/180);
  ctx.fillRect(-7,0,14,32); ctx.restore();
  // right leg
  ctx.save(); ctx.translate(9,-14); ctx.rotate(-ll*Math.PI/180);
  ctx.fillRect(-7,0,14,32); ctx.restore();

  // shoes
  ctx.fillStyle = "#080808";
  ctx.fillRect(-20,-2,18,9);
  ctx.fillRect(2,-2,18,9);

  // ── Body / suit ──
  ctx.save(); ctx.translate(bx, 0);

  ctx.fillStyle = "#1a2a4a";
  ctx.fillRect(-22,-92,44,58);

  // shirt
  ctx.fillStyle = "#f0ead8";
  ctx.fillRect(-8,-90,16,53);

  // UKIP-purple tie
  ctx.fillStyle = "#6b2a8a";
  ctx.fillRect(-4,-90,8,48);

  // jacket lapels
  ctx.fillStyle = "#142038";
  ctx.beginPath();
  ctx.moveTo(-8,-90); ctx.lineTo(-22,-78); ctx.lineTo(-22,-58); ctx.lineTo(-8,-66);
  ctx.closePath(); ctx.fill();
  ctx.beginPath();
  ctx.moveTo(8,-90); ctx.lineTo(22,-78); ctx.lineTo(22,-58); ctx.lineTo(8,-66);
  ctx.closePath(); ctx.fill();

  // ── Neck ──
  ctx.fillStyle = "#c8756a";
  ctx.fillRect(-7,-102,14,14);

  // ── Head ──
  const hdy = state==="hurt" ? -3 : state==="attack" ? -10 : walk*0.3;
  ctx.save(); ctx.translate(0, hdy);

  ctx.fillStyle = state==="hurt" ? "#dd4040" : "#c87568";
  ctx.beginPath();
  ctx.ellipse(0,-118,23,20,0,0,Math.PI*2);
  ctx.fill();

  // hair (receding, parted)
  ctx.fillStyle = "#8a7050";
  ctx.beginPath();
  ctx.ellipse(0,-127,23,11,0,Math.PI,0);
  ctx.fill();

  // eyes
  ctx.fillStyle = "#1a1a1a";
  ctx.fillRect(-13,-123,7,5);
  ctx.fillRect(6,-123,7,5);

  // eyebrows (slightly raised – smug)
  ctx.strokeStyle = "#5a4030";
  ctx.lineWidth   = 2.5;
  ctx.beginPath(); ctx.moveTo(-15,-129); ctx.lineTo(-6,-131); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(15,-129); ctx.lineTo(6,-131);  ctx.stroke();

  // mouth
  if (state==="attack") {
    // wide-open – mid-vomit
    ctx.fillStyle = "#3a0808";
    ctx.beginPath();
    ctx.ellipse(0,-110,11,9,0,0,Math.PI*2);
    ctx.fill();
    ctx.fillStyle = "#e0d8c0";
    ctx.fillRect(-9,-113,18,6);
  } else {
    ctx.strokeStyle = "#4a2010";
    ctx.lineWidth   = 2;
    ctx.beginPath();
    ctx.arc(2,-111,8,0.25,Math.PI-0.25);
    ctx.stroke();
  }

  // KO eyes
  if (state==="ko") {
    ctx.strokeStyle = "#ff0000";
    ctx.lineWidth   = 3;
    [[-13,-123],[ 6,-123]].forEach(([ex,ey]) => {
      ctx.beginPath(); ctx.moveTo(ex,ey);   ctx.lineTo(ex+6,ey+5); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(ex+6,ey); ctx.lineTo(ex,ey+5);   ctx.stroke();
    });
  }

  ctx.restore(); // head

  // ── Arms ──
  ctx.fillStyle = "#1a2a4a";
  // back arm
  ctx.fillRect(-32,-86,11,32);
  // front arm (gestures when attacking)
  const armExt = state==="attack" ? 18 : 0;
  ctx.fillRect(22,-86,12+armExt,30);
  ctx.fillStyle = "#c87568";
  ctx.beginPath();
  ctx.ellipse(35+armExt,-58,11,8,0.3,0,Math.PI*2);
  ctx.fill();

  ctx.restore(); // body translate

  // hurt flash overlay
  if (state==="hurt") {
    ctx.fillStyle = "rgba(255,50,50,0.35)";
    ctx.fillRect(-30,-145,60,150);
  }

  ctx.restore(); // global translate/scale
}

function drawBinface(f) {
  const { x, y, facing: fc, state, af } = f;
  ctx.save();
  ctx.translate(x, y);
  if (fc === -1) ctx.scale(-1, 1);

  const walk  = state==="run"    ? Math.sin(af*1.6)*5 : 0;
  const shake = state==="hurt"   ? (Math.random()-0.5)*6 : 0;
  const bx    = shake;

  // ── Legs ──
  ctx.fillStyle = "#1a1a1a";
  const ll = state==="run" ? Math.sin(af*1.6)*12 : 0;
  ctx.save(); ctx.translate(-9,-14); ctx.rotate(ll*Math.PI/180);
  ctx.fillRect(-7,0,14,32); ctx.restore();
  ctx.save(); ctx.translate(9,-14); ctx.rotate(-ll*Math.PI/180);
  ctx.fillRect(-7,0,14,32); ctx.restore();

  ctx.fillStyle = "#080808";
  ctx.fillRect(-20,-2,18,9);
  ctx.fillRect(2,-2,18,9);

  // ── Body ──
  ctx.save(); ctx.translate(bx, 0);

  ctx.fillStyle = "#1a1a1a";
  ctx.fillRect(-22,-92,44,58);

  // suit details
  ctx.fillStyle = "#282828";
  ctx.fillRect(-8,-90,16,52);
  ctx.fillStyle = "#888";
  ctx.fillRect(-3,-90,6,48);

  // lapels
  ctx.fillStyle = "#101010";
  ctx.beginPath();
  ctx.moveTo(-8,-90); ctx.lineTo(-22,-78); ctx.lineTo(-22,-58); ctx.lineTo(-8,-66);
  ctx.closePath(); ctx.fill();
  ctx.beginPath();
  ctx.moveTo(8,-90); ctx.lineTo(22,-78); ctx.lineTo(22,-58); ctx.lineTo(8,-66);
  ctx.closePath(); ctx.fill();

  // ── Neck ──
  ctx.fillStyle = "#555";
  ctx.fillRect(-7,-102,14,14);

  // ── HEAD = dustbin ──
  const hdy = state==="attack" ? -4 : walk*0.3;
  ctx.save(); ctx.translate(0, hdy);

  // bin body
  ctx.fillStyle = state==="hurt" ? "#aa8888" : "#888";
  ctx.fillRect(-21,-140,42,52);

  // bin lid
  ctx.fillStyle = "#aaa";
  ctx.fillRect(-25,-142,50,8);

  // lid rim
  ctx.fillStyle = "#999";
  ctx.fillRect(-23,-134,46,5);

  // horizontal bands
  ctx.fillStyle = "#777";
  ctx.fillRect(-21,-123,42,3);
  ctx.fillRect(-21,-112,42,3);

  // painted face – eyes (slots)
  const eyeFill = state==="attack" ? "#ff2200" : "#1a1a1a";
  ctx.fillStyle = eyeFill;
  ctx.fillRect(-17,-128,10,9);
  ctx.fillRect(7,-128,10,9);

  // pupils
  ctx.fillStyle = state==="attack" ? "#ff8800" : "#44cc44";
  ctx.fillRect(-14,-127,4,7);
  ctx.fillRect(9,-127,4,7);

  // mouth slot
  ctx.fillStyle = "#1a1a1a";
  ctx.fillRect(-12,-108,24,5);

  // KO
  if (state==="ko") {
    ctx.strokeStyle = "#ff0000";
    ctx.lineWidth   = 3;
    ctx.beginPath(); ctx.moveTo(-16,-132); ctx.lineTo(16,-100); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(16,-132);  ctx.lineTo(-16,-100); ctx.stroke();
  }

  ctx.restore(); // head

  // ── Arms ──
  ctx.fillStyle = "#1a1a1a";
  ctx.fillRect(-32,-86,11,32);
  const armExt = state==="attack" ? 20 : 0;
  ctx.fillRect(22,-86,12+armExt,30);

  ctx.restore(); // body

  if (state==="hurt") {
    ctx.fillStyle = "rgba(255,50,50,0.35)";
    ctx.fillRect(-30,-148,60,152);
  }

  ctx.restore();
}

// ── Projectile drawing ─────────────────────────────────────────────────────────

function drawVomit(p) {
  const wobble = Math.sin(p.af*0.9)*4;
  ctx.save();
  ctx.translate(p.x, p.y+wobble);

  // main blob
  const g = ctx.createRadialGradient(0,0,2, 0,0,22);
  g.addColorStop(0,   "#d0f030");
  g.addColorStop(0.55,"#88b020");
  g.addColorStop(1,   "rgba(70,110,5,0)");
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.ellipse(0, 0, 24, 14, wobble*0.08, 0, Math.PI*2);
  ctx.fill();

  // trailing droplets
  ctx.fillStyle = "rgba(130,170,20,0.75)";
  ctx.beginPath(); ctx.arc(-20, wobble*0.5, 7, 0, Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.arc(-32,-wobble*0.4, 4, 0, Math.PI*2); ctx.fill();

  // label
  ctx.fillStyle = "rgba(90,130,10,0.9)";
  ctx.font      = "bold 9px Arial,sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("BLEURGH!", 0, -24);

  ctx.restore();
}

function drawGarbage(p) {
  const spin = p.af * 0.6;
  ctx.save();
  ctx.translate(p.x, p.y);
  ctx.rotate(spin);

  // bag
  ctx.fillStyle = "#1a1a1a";
  ctx.beginPath();
  ctx.ellipse(0, 2, 18, 22, 0, 0, Math.PI*2);
  ctx.fill();

  // tie knot at top
  ctx.fillStyle = "#333";
  ctx.beginPath();
  ctx.arc(0,-18,6,0,Math.PI*2);
  ctx.fill();

  // white label
  ctx.fillStyle = "#e0e0e0";
  ctx.fillRect(-10,-9,20,14);
  ctx.fillStyle = "#1a1a1a";
  ctx.font      = "bold 7px Arial,sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("RUBBISH",0,0);

  ctx.restore();

  // smell squiggles (not rotated)
  ctx.save();
  ctx.translate(p.x, p.y);
  ctx.strokeStyle = "rgba(100,150,50,0.55)";
  ctx.lineWidth   = 1.5;
  [-14,0,14].forEach(sx => {
    ctx.beginPath();
    ctx.moveTo(sx,-28);
    ctx.quadraticCurveTo(sx+6,-36,sx,-44);
    ctx.stroke();
  });
  ctx.restore();
}

// ── HUD update ─────────────────────────────────────────────────────────────────
function updateHUD() {
  const p1hp = fighters[0] ? fighters[0].hp : 0;
  const p2hp = fighters[1] ? fighters[1].hp : 0;

  const setBar = (el, hp) => {
    const pct = (hp/MAX_HP)*100;
    el.style.width = pct+"%";
    el.classList.remove("low","danger");
    if (pct <= 25)      el.classList.add("danger");
    else if (pct <= 50) el.classList.add("low");
  };

  setBar(p1Fill, p1hp);
  setBar(p2Fill, p2hp);
  timerEl.textContent = String(timerSecs);
}

// ── Overlay helpers ────────────────────────────────────────────────────────────
function showOverlay(title, sub, showBtn) {
  overlayTitle.textContent  = title;
  overlaySub.textContent    = sub;
  restartBtn.classList.toggle("hidden", !showBtn);
  overlayEl.classList.remove("hidden");
}

function hideOverlay() {
  overlayEl.classList.add("hidden");
}

// ── Timer ──────────────────────────────────────────────────────────────────────
function startRoundTimer() {
  timerInterval = setInterval(() => {
    if (gamePhase !== "fight") return;
    timerSecs = Math.max(0, timerSecs-1);
    if (timerSecs === 0) timeOut();
  }, 1000);
}

function stopRoundTimer() {
  clearInterval(timerInterval);
  timerInterval = null;
}

function timeOut() {
  if (gamePhase === "end") return;
  gamePhase = "end";
  stopRoundTimer();
  const p1hp = fighters[0].hp;
  const p2hp = fighters[1].hp;
  if (p1hp > p2hp)       endGame("YOU WIN!", "Farage prevails!");
  else if (p2hp > p1hp)  endGame("YOU LOSE", "Binface wins on points");
  else                   endGame("DRAW!", "Both candidates dishonoured");
}

function endGame(title, sub) {
  gamePhase = "end";
  stopRoundTimer();
  setTimeout(() => showOverlay(title, sub, true), 900);
}

// ── Game loop ──────────────────────────────────────────────────────────────────
function update() {
  frameCount++;

  if (gamePhase === "intro") {
    introTimer++;
    if (introTimer >= 90) {
      gamePhase = "fight";
      hideOverlay();
      startRoundTimer();
    }
    return;
  }

  if (gamePhase !== "fight") return;

  // update fighters
  fighters.forEach(f => f.update());

  // update projectiles
  projectiles = projectiles.filter(p => p.active);
  projectiles.forEach(p => p.update());

  // collision: projectile vs fighter
  projectiles.forEach(proj => {
    if (!proj.active) return;
    fighters.forEach(f => {
      if (f.isPlayer === proj.fromPlayer) return; // don't self-hit
      if (rectsOverlap(proj.hitbox(), f.hitbox())) {
        proj.active = false;
        f.takeDamage(PROJ_DAMAGE);
        spawnHitParticles(f.x, f.y-60);

        // check KO
        if (f.state === "ko") {
          const winner = f.isPlayer ? "BINFACE WINS" : "YOU WIN!";
          const sub    = f.isPlayer ? "K.O. — Binface does bin duty" : "K.O. — Farage vomits to victory";
          endGame(winner, sub);
        }
      }
    });
  });

  // update particles
  particles = particles.filter(p => p.life > 0);
  particles.forEach(p => p.update());
}

function render() {
  // background from cache
  if (bgCache) ctx.drawImage(bgCache, 0, 0);

  drawFloor();

  // fighters
  fighters.forEach(f => {
    if (f.isPlayer) drawFarage(f);
    else            drawBinface(f);
  });

  // projectiles
  projectiles.forEach(p => {
    if (p.fromPlayer) drawVomit(p);
    else              drawGarbage(p);
  });

  // particles
  particles.forEach(p => p.draw());

  // intro countdown text
  if (gamePhase === "intro") {
    ctx.fillStyle   = "rgba(0,0,0,0.38)";
    ctx.fillRect(0,0,CANVAS_W,CANVAS_H);
  }

  updateHUD();
}

function loop() {
  update();
  render();
  rafId = requestAnimationFrame(loop);
}

// ── Init / restart ─────────────────────────────────────────────────────────────
function startGame() {
  cancelAnimationFrame(rafId);
  stopRoundTimer();
  hideOverlay();

  fighters    = [new Fighter(160, true), new Fighter(640, false)];
  projectiles = [];
  particles   = [];
  timerSecs   = ROUND_SECONDS;
  frameCount  = 0;
  gamePhase   = "intro";
  introTimer  = 0;
  keys        = {};

  updateHUD();
  showOverlay("FIGHT!", "", false);
  loop();
}

// ── Input ──────────────────────────────────────────────────────────────────────
document.addEventListener("keydown", e => {
  // Only intercept game keys; let the browser handle others
  if (["ArrowLeft","ArrowRight","ArrowUp","ArrowDown"," ","Space"].includes(e.key) ||
      e.code === "Space") {
    e.preventDefault();
  }
  keys[e.key] = true;
});

document.addEventListener("keyup", e => {
  keys[e.key] = false;
});

restartBtn.addEventListener("click", startGame);

// ── Boot ───────────────────────────────────────────────────────────────────────
prerenderBg();
startGame();
