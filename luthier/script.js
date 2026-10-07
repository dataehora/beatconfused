/* ============================================================
   LUTHIER TUNING — a live spectrogram for studying how an instrument
   holds its frequencies: which harmonics it produces, how strong each is,
   and how long each one sustains.

   Two layers share one log-frequency axis on the main display:
     1. LIVE — the current spectrum, but each bin falls back down at a
        limited rate (the Decay slider, in dB/s) instead of snapping to
        the next frame, so a plucked note visibly rings out.
     2. PEAK HOLD — drawn behind the live curve: the loudest level ever
        reached in each bin since the last Reset. Every new peak raises it.
   Below it, a waterfall (time scrolling downward) keeps several seconds
   of history, so each harmonic's sustain reads as a vertical streak.

   Uses shared/tuner-common.js only for the mic status messages,
   collapsible panels and note-name helpers — none of the tuner-specific
   pitch/temperament machinery applies here.
   ============================================================ */
(function () {
  "use strict";

  const T = window.TunerCommon;

  // 16384 gives ~2.9 Hz per bin at 48 kHz — fine enough to separate the
  // low harmonics of a bass string, while the frame rate stays smooth.
  const FFT_SIZE = 16384;
  const DB_MIN = -120;
  const DB_MAX = -10;
  const AUDIBLE_MIN_HZ = 20;
  const AUDIBLE_MAX_HZ = 20000;
  // Lowest frequency drawn in "Full range" mode. Below this a 16384-point
  // FFT has only one or two bins, so there's nothing meaningful to show.
  const FULL_MIN_HZ = 5;
  const WATERFALL_SECONDS = 12;
  const READOUT_INTERVAL_MS = 120;
  const HARMONIC_GUIDES = 12;

  const els = {
    toggleMicBtn: document.getElementById("toggleMicBtn"),
    powerState: document.getElementById("powerSwitchState"),
    micStatus: document.getElementById("micStatus"),
    rangeToggle: document.getElementById("rangeToggle"),
    rangeCheckbox: document.getElementById("rangeCheckbox"),
    spectrumCanvas: document.getElementById("luthierSpectrum"),
    waterfallCanvas: document.getElementById("luthierWaterfall"),
    rangeLowLabel: document.getElementById("rangeLowLabel"),
    rangeHighLabel: document.getElementById("rangeHighLabel"),
    cursorReadout: document.getElementById("cursorReadout"),
    peakReadout: document.getElementById("peakReadout"),
    decayRange: document.getElementById("decayRange"),
    decayValue: document.getElementById("decayValue"),
    gainRange: document.getElementById("gainRange"),
    gainValue: document.getElementById("gainValue"),
    resetPeaksBtn: document.getElementById("resetPeaksBtn"),
  };

  const setMicStatus = T.setMicStatusFactory(els.micStatus);

  function tr(key, fallback, vars) {
    return window.BC_I18N ? window.BC_I18N.t(key, vars) : fallback;
  }

  // ---- audio state ----
  let audioContext = null;
  let mediaStream = null;
  let sourceNode = null;
  let gainNode = null;
  let analyser = null;
  let isRunning = false;
  let rafId = null;

  // ---- spectrum state (all in dB, one entry per FFT bin) ----
  let sampleRate = 48000;
  let frameDb = null;
  let liveDb = null;
  let peakDb = null;
  let waterfallAccum = null;

  // ---- display state ----
  let fullRange = true;
  let decayDbPerSecond = Number(els.decayRange.value);
  let cursorHz = null;
  let lastFrameTime = 0;
  let lastReadoutTime = 0;
  let waterfallCarryMs = 0;

  // Per-pixel-column mapping onto FFT bins, rebuilt whenever the canvas
  // size, sample rate or frequency range changes.
  let columns = null;

  function binCount() {
    return FFT_SIZE / 2;
  }

  function hzPerBin() {
    return sampleRate / FFT_SIZE;
  }

  function nyquist() {
    return sampleRate / 2;
  }

  function currentRange() {
    if (fullRange) {
      return { min: Math.max(FULL_MIN_HZ, hzPerBin() * 2), max: nyquist() };
    }
    return { min: AUDIBLE_MIN_HZ, max: Math.min(AUDIBLE_MAX_HZ, nyquist()) };
  }

  function allocateBuffers() {
    const count = binCount();
    frameDb = new Float32Array(count).fill(DB_MIN);
    liveDb = new Float32Array(count).fill(DB_MIN);
    peakDb = new Float32Array(count).fill(DB_MIN);
    waterfallAccum = new Float32Array(count).fill(DB_MIN);
  }

  allocateBuffers();

  /* ============================================================
     CANVAS SIZING + COLUMN MAPPING
     ============================================================ */
  const spectrumCtx = els.spectrumCanvas.getContext("2d");
  const waterfallCtx = els.waterfallCanvas.getContext("2d");
  const plot = { width: 0, height: 0, dpr: 1 };
  const fall = { width: 0, height: 0, rowImage: null };

  function sizeCanvases() {
    const dpr = window.devicePixelRatio || 1;
    const spectrumRect = els.spectrumCanvas.getBoundingClientRect();
    const waterfallRect = els.waterfallCanvas.getBoundingClientRect();

    plot.dpr = dpr;
    plot.width = Math.max(1, Math.round(spectrumRect.width * dpr));
    plot.height = Math.max(1, Math.round(spectrumRect.height * dpr));
    els.spectrumCanvas.width = plot.width;
    els.spectrumCanvas.height = plot.height;

    // The waterfall keeps its own pixels as history, so only reallocate
    // (and clear) it when its size actually changed.
    const fallWidth = Math.max(1, Math.round(waterfallRect.width * dpr));
    const fallHeight = Math.max(1, Math.round(waterfallRect.height * dpr));

    if (fallWidth !== fall.width || fallHeight !== fall.height) {
      fall.width = fallWidth;
      fall.height = fallHeight;
      els.waterfallCanvas.width = fallWidth;
      els.waterfallCanvas.height = fallHeight;
      fall.rowImage = waterfallCtx.createImageData(fallWidth, 1);
      clearWaterfall();
    }

    rebuildColumns();
    drawSpectrum();
  }

  function rebuildColumns() {
    // Both canvases share the same CSS width, so one mapping (in device
    // pixels of the spectrum canvas) serves both; the waterfall resamples
    // it if its pixel width ever differs.
    const width = plot.width;
    const { min, max } = currentRange();
    const logMin = Math.log(min);
    const logMax = Math.log(max);
    const step = hzPerBin();
    const lastBin = binCount() - 1;

    const lo = new Int32Array(width);
    const hi = new Int32Array(width);
    const interp = new Float32Array(width);

    for (let x = 0; x < width; x += 1) {
      const fa = Math.exp(logMin + ((logMax - logMin) * x) / width);
      const fb = Math.exp(logMin + ((logMax - logMin) * (x + 1)) / width);
      const ba = fa / step;
      const bb = fb / step;

      if (bb - ba < 1) {
        // Narrower than one bin (the low end of a log axis): interpolate
        // between the two nearest bins at the column's centre frequency.
        const center = Math.sqrt(fa * fb) / step;
        const base = Math.min(lastBin - 1, Math.max(0, Math.floor(center)));
        lo[x] = base;
        hi[x] = -1;
        interp[x] = Math.min(1, Math.max(0, center - base));
      } else {
        // Wider than one bin (the high end): take the loudest bin inside
        // the column so narrow peaks never disappear between pixels.
        lo[x] = Math.min(lastBin, Math.max(0, Math.floor(ba)));
        hi[x] = Math.min(lastBin, Math.max(lo[x], Math.ceil(bb)));
        interp[x] = 0;
      }
    }

    columns = { lo, hi, interp, width, logMin, logMax };
  }

  function columnValue(data, x) {
    const lo = columns.lo[x];
    const hi = columns.hi[x];

    if (hi < 0) {
      const t = columns.interp[x];
      return data[lo] * (1 - t) + data[lo + 1] * t;
    }

    let value = DB_MIN;
    for (let b = lo; b <= hi; b += 1) {
      if (data[b] > value) value = data[b];
    }
    return value;
  }

  function freqToX(hz) {
    return ((Math.log(hz) - columns.logMin) / (columns.logMax - columns.logMin)) * plot.width;
  }

  function xToFreq(x) {
    return Math.exp(columns.logMin + ((columns.logMax - columns.logMin) * x) / plot.width);
  }

  function dbToY(db) {
    const t = (db - DB_MIN) / (DB_MAX - DB_MIN);
    return plot.height - Math.min(1, Math.max(0, t)) * plot.height;
  }

  /* ============================================================
     DRAWING — main spectrum (grid, inaudible bands, peak hold, live)
     ============================================================ */
  const GRID_FREQS = [5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000];
  const MINOR_FREQS = [];
  [1, 10, 100, 1000, 10000].forEach((decade) => {
    for (let m = 2; m <= 9; m += 1) MINOR_FREQS.push(decade * m);
  });

  function formatHz(hz) {
    if (hz >= 1000) {
      const k = hz / 1000;
      return `${Number.isInteger(k) ? k : k.toFixed(1)}k`;
    }
    return String(Math.round(hz));
  }

  function formatHzPrecise(hz) {
    if (hz >= 1000) return `${(hz / 1000).toFixed(hz >= 10000 ? 2 : 3)} kHz`;
    return `${hz.toFixed(1)} Hz`;
  }

  function drawGrid(ctx) {
    const { width, height, dpr } = plot;
    const { min, max } = currentRange();

    // Inaudible bands (only visible in Full range mode): shaded, so it's
    // obvious which part of the picture a human ear can't hear.
    ctx.fillStyle = "rgba(120, 140, 170, 0.08)";
    if (min < AUDIBLE_MIN_HZ) {
      ctx.fillRect(0, 0, freqToX(AUDIBLE_MIN_HZ), height);
    }
    if (max > AUDIBLE_MAX_HZ) {
      const x = freqToX(AUDIBLE_MAX_HZ);
      ctx.fillRect(x, 0, width - x, height);
    }

    ctx.lineWidth = 1;

    ctx.strokeStyle = "rgba(246, 241, 232, 0.04)";
    ctx.beginPath();
    MINOR_FREQS.forEach((hz) => {
      if (hz <= min || hz >= max) return;
      const x = Math.round(freqToX(hz)) + 0.5;
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
    });
    ctx.stroke();

    ctx.strokeStyle = "rgba(246, 241, 232, 0.1)";
    ctx.beginPath();
    GRID_FREQS.forEach((hz) => {
      if (hz <= min || hz >= max) return;
      const x = Math.round(freqToX(hz)) + 0.5;
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
    });
    for (let db = DB_MAX - 10; db > DB_MIN; db -= 20) {
      const y = Math.round(dbToY(db)) + 0.5;
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
    }
    ctx.stroke();

    ctx.font = `${10 * dpr}px Inter, "Segoe UI", system-ui, sans-serif`;
    ctx.fillStyle = "rgba(246, 241, 232, 0.42)";
    ctx.textBaseline = "bottom";
    ctx.textAlign = "center";
    // Kept inside the canvas edges, and skipped when they'd overprint the
    // previous label (narrow phone screens squeeze the low decades).
    let lastLabelRight = -Infinity;
    GRID_FREQS.forEach((hz) => {
      if (hz <= min || hz >= max) return;
      const text = formatHz(hz);
      const half = ctx.measureText(text).width / 2;
      const x = Math.min(width - half - 4 * dpr, Math.max(half + 4 * dpr, freqToX(hz)));
      if (x - half < lastLabelRight + 6 * dpr) return;
      ctx.fillText(text, x, height - 4 * dpr);
      lastLabelRight = x + half;
    });

    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    for (let db = DB_MAX - 10; db > DB_MIN; db -= 20) {
      ctx.fillText(`${db} dB`, 6 * dpr, dbToY(db) - 7 * dpr);
    }

    if (min < AUDIBLE_MIN_HZ || max > AUDIBLE_MAX_HZ) {
      // Just above the frequency labels, clear of the dB labels and the
      // legend in the top corners.
      const labelY = height - 18 * dpr;
      ctx.fillStyle = "rgba(170, 190, 220, 0.5)";
      ctx.textBaseline = "bottom";
      if (min < AUDIBLE_MIN_HZ) {
        ctx.textAlign = "left";
        ctx.fillText(tr("luthier.infrasound", "infrasound"), 4 * dpr, labelY);
      }
      if (max > AUDIBLE_MAX_HZ) {
        ctx.textAlign = "right";
        ctx.fillText(tr("luthier.ultrasound", "ultrasound"), width - 4 * dpr, labelY);
      }
    }
  }

  function traceCurve(ctx, data) {
    ctx.beginPath();
    ctx.moveTo(0, plot.height);
    for (let x = 0; x < columns.width; x += 1) {
      ctx.lineTo(x + 0.5, dbToY(columnValue(data, x)));
    }
    ctx.lineTo(plot.width, plot.height);
    ctx.closePath();
  }

  function strokeCurve(ctx, data) {
    ctx.beginPath();
    for (let x = 0; x < columns.width; x += 1) {
      const y = dbToY(columnValue(data, x));
      if (x === 0) ctx.moveTo(0.5, y);
      else ctx.lineTo(x + 0.5, y);
    }
  }

  function drawSpectrum() {
    if (!columns || columns.width !== plot.width) return;

    const ctx = spectrumCtx;
    const { width, height, dpr } = plot;
    ctx.clearRect(0, 0, width, height);
    drawGrid(ctx);

    // Peak hold — the "background" graph: a soft filled silhouette plus a
    // thin pale-blue outline, so the live curve always reads in front.
    traceCurve(ctx, peakDb);
    ctx.fillStyle = "rgba(143, 179, 217, 0.12)";
    ctx.fill();
    strokeCurve(ctx, peakDb);
    ctx.strokeStyle = "rgba(160, 196, 236, 0.75)";
    ctx.lineWidth = 1.2 * dpr;
    ctx.stroke();

    // Live (decaying) spectrum.
    const fill = ctx.createLinearGradient(0, 0, 0, height);
    fill.addColorStop(0, "rgba(248, 196, 92, 0.75)");
    fill.addColorStop(0.55, "rgba(198, 112, 44, 0.45)");
    fill.addColorStop(1, "rgba(140, 59, 47, 0.08)");
    traceCurve(ctx, liveDb);
    ctx.fillStyle = fill;
    ctx.fill();
    strokeCurve(ctx, liveDb);
    ctx.strokeStyle = "#ffd88a";
    ctx.lineWidth = 1.5 * dpr;
    ctx.stroke();

    if (cursorHz !== null) {
      drawCursor(ctx);
    }
  }

  // Hover/tap cursor: a solid line at the chosen frequency plus dashed
  // guides at its integer multiples — lining them up with real peaks shows
  // at a glance how harmonic (or inharmonic) the instrument's overtones are.
  function drawCursor(ctx) {
    const { width, height, dpr } = plot;
    const { max } = currentRange();

    ctx.save();
    ctx.lineWidth = 1 * dpr;
    ctx.setLineDash([3 * dpr, 4 * dpr]);
    ctx.strokeStyle = "rgba(246, 241, 232, 0.28)";
    ctx.fillStyle = "rgba(246, 241, 232, 0.5)";
    ctx.font = `${9 * dpr}px Inter, "Segoe UI", system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    // Labels sit below the legend. On a log axis the guides bunch up as k
    // grows; only label the ones with room to spare so the numbers never
    // overprint each other.
    let lastLabelX = -Infinity;
    for (let k = 2; k <= HARMONIC_GUIDES; k += 1) {
      const hz = cursorHz * k;
      if (hz >= max) break;
      const x = Math.round(freqToX(hz)) + 0.5;
      if (x > width) break;
      ctx.beginPath();
      ctx.moveTo(x, 44 * dpr);
      ctx.lineTo(x, height);
      ctx.stroke();
      if (x - lastLabelX >= 22 * dpr) {
        ctx.fillText(`${k}×`, x, 32 * dpr);
        lastLabelX = x;
      }
    }

    ctx.setLineDash([]);
    ctx.strokeStyle = "rgba(255, 244, 214, 0.85)";
    const x0 = Math.round(freqToX(cursorHz)) + 0.5;
    ctx.beginPath();
    ctx.moveTo(x0, 0);
    ctx.lineTo(x0, height);
    ctx.stroke();
    ctx.restore();
  }

  /* ============================================================
     WATERFALL — one new row at the top every (WATERFALL_SECONDS / height)
     seconds; older rows scroll down. Each row is the loudest level each
     column reached during that interval, so short transients still show.
     ============================================================ */
  // Dark window → oxblood → copper → brass → cream: the site's own palette
  // stretched into a perceptually increasing heat map.
  const COLOR_STOPS = [
    [0, [23, 19, 16]],
    [0.25, [74, 26, 20]],
    [0.5, [140, 59, 47]],
    [0.7, [198, 112, 44]],
    [0.86, [232, 176, 74]],
    [1, [255, 244, 214]],
  ];
  const COLOR_LUT = new Uint8ClampedArray(256 * 3);

  (function buildLut() {
    for (let i = 0; i < 256; i += 1) {
      const t = i / 255;
      let s = 0;
      while (s < COLOR_STOPS.length - 2 && t > COLOR_STOPS[s + 1][0]) s += 1;
      const [t0, c0] = COLOR_STOPS[s];
      const [t1, c1] = COLOR_STOPS[s + 1];
      const f = (t - t0) / (t1 - t0);
      for (let c = 0; c < 3; c += 1) {
        COLOR_LUT[i * 3 + c] = Math.round(c0[c] + (c1[c] - c0[c]) * f);
      }
    }
  })();

  // The waterfall's colour scale starts higher than the plot's dB floor:
  // a mic's noise floor would otherwise paint the whole history dull red.
  const FALL_DB_MIN = -100;
  const FALL_DB_MAX = -20;

  function clearWaterfall() {
    waterfallCtx.fillStyle = "rgb(23, 19, 16)";
    waterfallCtx.fillRect(0, 0, fall.width, fall.height);
  }

  // `count` > 1 when a slow frame owes several rows at once: they all get
  // the same accumulated data, rather than one real row plus blank ones.
  function pushWaterfallRows(count) {
    if (!fall.rowImage || !columns || count < 1) return;

    const { width, height } = fall;
    const pixels = fall.rowImage.data;
    const scale = columns.width / width;

    for (let x = 0; x < width; x += 1) {
      const col = Math.min(columns.width - 1, Math.floor(x * scale));
      const db = columnValue(waterfallAccum, col);
      const t = Math.min(1, Math.max(0, (db - FALL_DB_MIN) / (FALL_DB_MAX - FALL_DB_MIN)));
      const idx = Math.round(t * 255) * 3;
      const p = x * 4;
      pixels[p] = COLOR_LUT[idx];
      pixels[p + 1] = COLOR_LUT[idx + 1];
      pixels[p + 2] = COLOR_LUT[idx + 2];
      pixels[p + 3] = 255;
    }

    const shift = Math.min(count, height);
    if (shift < height) {
      waterfallCtx.drawImage(els.waterfallCanvas, 0, 0, width, height - shift, 0, shift, width, height - shift);
    }
    for (let y = 0; y < shift; y += 1) {
      waterfallCtx.putImageData(fall.rowImage, 0, y);
    }
    waterfallAccum.fill(DB_MIN);
  }

  /* ============================================================
     READOUTS — cursor (hover/tap) and strongest live peak
     ============================================================ */
  function noteLabel(hz) {
    if (!(hz > 0)) return "";
    const midi = 69 + 12 * Math.log2(hz / 440);
    const rounded = Math.round(midi);
    const cents = Math.round((midi - rounded) * 100);
    const sign = cents < 0 ? "−" : "+";
    return `${T.noteNameForMidi(rounded)} ${sign}${Math.abs(cents)}¢`;
  }

  function binDb(data, hz) {
    const bin = Math.round(hz / hzPerBin());
    if (bin < 0 || bin >= data.length) return DB_MIN;
    return data[bin];
  }

  function formatDb(db) {
    return db <= DB_MIN + 0.5 ? "—" : `${db.toFixed(1)} dB`;
  }

  function updateCursorReadout() {
    if (cursorHz === null) {
      els.cursorReadout.textContent = tr("luthier.cursorHint", "Hover or tap the display to read a frequency and see its harmonics.");
      return;
    }

    els.cursorReadout.textContent = tr("luthier.cursorReadout", "{freq} · {note} · live {live} · peak {peak}", {
      freq: formatHzPrecise(cursorHz),
      note: noteLabel(cursorHz),
      live: formatDb(binDb(liveDb, cursorHz)),
      peak: formatDb(binDb(peakDb, cursorHz)),
    });
  }

  function updatePeakReadout() {
    const { min, max } = currentRange();
    const step = hzPerBin();
    const start = Math.max(1, Math.ceil(min / step));
    const end = Math.min(liveDb.length - 2, Math.floor(max / step));
    let best = -1;
    // Anything quieter is treated as the mic's own noise floor.
    let bestDb = -95;

    for (let b = start; b <= end; b += 1) {
      if (liveDb[b] > bestDb) {
        bestDb = liveDb[b];
        best = b;
      }
    }

    if (best < 0) {
      els.peakReadout.textContent = tr("luthier.peakNone", "Strongest peak: —");
      return;
    }

    // Parabolic interpolation over the three bins around the maximum
    // refines the frequency well below one bin's width.
    const a = liveDb[best - 1];
    const b = liveDb[best];
    const c = liveDb[best + 1];
    const denom = a - 2 * b + c;
    const offset = denom !== 0 ? (0.5 * (a - c)) / denom : 0;
    const hz = (best + Math.max(-0.5, Math.min(0.5, offset))) * step;

    els.peakReadout.textContent = tr("luthier.peakReadout", "Strongest peak: {freq} · {note} · {db}", {
      freq: formatHzPrecise(hz),
      note: noteLabel(hz),
      db: formatDb(bestDb),
    });
  }

  function updateRangeLabels() {
    const { min, max } = currentRange();
    els.rangeLowLabel.textContent = formatHzPrecise(min);
    els.rangeHighLabel.textContent = formatHzPrecise(max);
  }

  /* ============================================================
     MAIN LOOP
     ============================================================ */
  function tick(now) {
    rafId = requestAnimationFrame(tick);

    const dt = lastFrameTime ? Math.min(0.1, (now - lastFrameTime) / 1000) : 0;
    lastFrameTime = now;

    analyser.getFloatFrequencyData(frameDb);

    const fallStep = decayDbPerSecond * dt;
    for (let i = 0; i < frameDb.length; i += 1) {
      let v = frameDb[i];
      if (!(v > DB_MIN)) v = DB_MIN; // also catches -Infinity / NaN

      const decayed = liveDb[i] - fallStep;
      liveDb[i] = v > decayed ? v : decayed;
      if (liveDb[i] < DB_MIN) liveDb[i] = DB_MIN;
      if (v > peakDb[i]) peakDb[i] = v;
      if (v > waterfallAccum[i]) waterfallAccum[i] = v;
    }

    drawSpectrum();

    const rowMs = (WATERFALL_SECONDS * 1000) / Math.max(1, fall.height);
    waterfallCarryMs += dt * 1000;
    const rowsDue = Math.floor(waterfallCarryMs / rowMs);
    if (rowsDue > 0) {
      pushWaterfallRows(rowsDue);
      waterfallCarryMs -= rowsDue * rowMs;
    }

    if (now - lastReadoutTime > READOUT_INTERVAL_MS) {
      lastReadoutTime = now;
      updatePeakReadout();
      updateCursorReadout();
    }
  }

  /* ============================================================
     MICROPHONE START / STOP
     ============================================================ */
  function setPowerUi(on) {
    els.toggleMicBtn.setAttribute("aria-pressed", String(on));
    els.powerState.textContent = on ? tr("power.on", "ON") : tr("power.off", "OFF");
  }

  async function start() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setMicStatus(T.MIC_MESSAGES.notSupported, true);
      return;
    }

    try {
      // Every browser "voice" processing stage off: echo cancellation,
      // noise suppression and AGC would all reshape the very spectrum and
      // decay this tool exists to measure.
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

    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) {
      setMicStatus(T.MIC_MESSAGES.webAudioNotSupported, true);
      mediaStream.getTracks().forEach((track) => track.stop());
      mediaStream = null;
      return;
    }

    if (!audioContext) {
      audioContext = new AudioCtx();
    }
    if (audioContext.state === "suspended") {
      await audioContext.resume();
    }

    if (audioContext.sampleRate !== sampleRate || !analyser) {
      sampleRate = audioContext.sampleRate;
      analyser = audioContext.createAnalyser();
      analyser.fftSize = FFT_SIZE;
      // Smoothing off: the page applies its own, visible decay instead.
      analyser.smoothingTimeConstant = 0;
      analyser.minDecibels = DB_MIN;
      analyser.maxDecibels = DB_MAX;
      gainNode = audioContext.createGain();
      gainNode.connect(analyser);
      allocateBuffers();
      rebuildColumns();
      updateRangeLabels();
    }

    gainNode.gain.value = Number(els.gainRange.value);
    sourceNode = audioContext.createMediaStreamSource(mediaStream);
    sourceNode.connect(gainNode);

    isRunning = true;
    lastFrameTime = 0;
    waterfallCarryMs = 0;
    setPowerUi(true);
    setMicStatus(T.MIC_MESSAGES.listening, false);
    rafId = requestAnimationFrame(tick);
  }

  function stop() {
    isRunning = false;
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;

    if (sourceNode) {
      sourceNode.disconnect();
      sourceNode = null;
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop());
      mediaStream = null;
    }

    // The last picture (and the peak hold) stays on screen for study.
    setPowerUi(false);
    setMicStatus(T.MIC_MESSAGES.idle, false);
  }

  function toggle() {
    if (isRunning) stop();
    else start();
  }

  /* ============================================================
     CONTROLS
     ============================================================ */
  els.toggleMicBtn.addEventListener("click", toggle);

  document.addEventListener("keydown", (event) => {
    const tag = document.activeElement && document.activeElement.tagName;
    if (event.code === "Space" && tag !== "INPUT" && tag !== "SELECT" && tag !== "TEXTAREA" && tag !== "BUTTON") {
      event.preventDefault();
      toggle();
    }
  });

  function syncRangeToggle() {
    fullRange = !els.rangeCheckbox.checked;
    els.rangeToggle.querySelectorAll(".style-toggle-label").forEach((label) => {
      label.classList.toggle("is-active", label.dataset.style === (fullRange ? "full" : "audible"));
    });
    rebuildColumns();
    updateRangeLabels();
    // Old waterfall rows were drawn on the other axis — they'd no longer
    // line up with the spectrum above, so start the history fresh.
    clearWaterfall();
    drawSpectrum();
  }

  els.rangeCheckbox.addEventListener("change", syncRangeToggle);
  els.rangeToggle.querySelectorAll(".style-toggle-label").forEach((label) => {
    label.addEventListener("click", (event) => {
      event.preventDefault();
      const wantAudible = label.dataset.style === "audible";
      if (els.rangeCheckbox.checked !== wantAudible) {
        els.rangeCheckbox.checked = wantAudible;
        syncRangeToggle();
      }
    });
  });

  function syncDecay() {
    decayDbPerSecond = Number(els.decayRange.value);
    els.decayValue.textContent = `${decayDbPerSecond} dB/s`;
  }
  els.decayRange.addEventListener("input", syncDecay);

  function syncGain() {
    const gain = Number(els.gainRange.value);
    els.gainValue.textContent = `${gain.toFixed(1)}×`;
    if (gainNode && audioContext) {
      gainNode.gain.setTargetAtTime(gain, audioContext.currentTime, 0.01);
    }
  }
  els.gainRange.addEventListener("input", syncGain);

  els.resetPeaksBtn.addEventListener("click", () => {
    peakDb.fill(DB_MIN);
    liveDb.fill(DB_MIN);
    clearWaterfall();
    drawSpectrum();
    updatePeakReadout();
    updateCursorReadout();
  });

  // Cursor: follows a mouse, sticks where a finger last tapped.
  function setCursorFromEvent(event) {
    const rect = els.spectrumCanvas.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * plot.width;
    cursorHz = xToFreq(Math.min(plot.width, Math.max(0, x)));
    if (!isRunning) drawSpectrum();
    updateCursorReadout();
  }

  els.spectrumCanvas.addEventListener("pointermove", (event) => {
    if (event.pointerType === "mouse" || event.buttons) setCursorFromEvent(event);
  });
  els.spectrumCanvas.addEventListener("pointerdown", setCursorFromEvent);
  els.spectrumCanvas.addEventListener("pointerleave", (event) => {
    if (event.pointerType !== "mouse") return;
    cursorHz = null;
    if (!isRunning) drawSpectrum();
    updateCursorReadout();
  });

  window.addEventListener("bc:langchange", () => {
    setPowerUi(isRunning);
    updateCursorReadout();
    updatePeakReadout();
    drawSpectrum();
  });

  T.wireCollapsibles(() => sizeCanvases());

  if (window.ResizeObserver) {
    new ResizeObserver(() => sizeCanvases()).observe(els.spectrumCanvas);
  } else {
    window.addEventListener("resize", sizeCanvases);
  }

  syncDecay();
  syncGain();
  syncRangeToggle();
  sizeCanvases();
  updateRangeLabels();
  updateCursorReadout();
  updatePeakReadout();
})();
