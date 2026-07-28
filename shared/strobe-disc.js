/* ============================================================
   STROBE DISC ENGINE — the reusable "one strobe wheel" building block:
   an SVG wedge-disc for a single pitch class, with one concentric ring per
   real octave-instance of that note (each ring independently Goertzel-
   analyzed against a live time-domain buffer).

   This is the base code for BOTH:
   - /strobetuner/  — a single, large instance whose note is chosen live by
     pitch detection, covering every octave of whichever note is sounding.
   - /multistrobe/  — twelve small instances, one per fixed note, laid out
     like a piano keyboard.

   Geometry (size, arc span, viewBox) is passed in per page, since the two
   pages want very different scales — but the disc-building algorithm and
   the Goertzel ring analysis are identical, so an improvement made here
   automatically applies to both pages at once.
   ============================================================ */
(function (global) {
  const SVG_NS = "http://www.w3.org/2000/svg";

  const NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];

  // A standard 88-key grand piano: A0 (MIDI 21) to C8 (MIDI 108). Every
  // octave-instance of a pitch class that falls in this range gets its own
  // ring, so C/A/A♯/B (which land on both ends of the range) get 8 rings,
  // everything else gets 7 — not a fixed count per disc.
  const PIANO_MIN_MIDI = 21;
  const PIANO_MAX_MIDI = 108;

  // The analyser buffer needs to be long enough that even the lowest ring
  // (A0, 27.5 Hz) gets several full cycles to analyze — see
  // computeWindowSamples(). 16384 samples is ~371ms at 44.1kHz, enough for
  // ~10 cycles of A0 with room to spare, while still being cheap: every
  // ring only reads as many of the most recent samples as it actually needs.
  const ANALYSER_BUFFER_SIZE = 16384;
  // How many cycles of a ring's own target frequency its Goertzel window
  // covers — more cycles means a cleaner, more frequency-selective reading
  // but a longer (laggier) window for that specific ring.
  const GOERTZEL_MIN_CYCLES = 6;
  const MIN_RING_WINDOW_SAMPLES = 64;

  const CENTS_SMOOTHING = 0.25;
  const IN_TUNE_THRESHOLD_CENTS = 1;
  const MAX_UNTUNED_CENTS = 50;
  const RING_DEADZONE_CENTS = 1.5;
  // Degrees of rotation per cent of error, per second.
  const RING_ROTATION_SPEED = 8;
  // A Goertzel magnitude, normalized by window length, below which a ring
  // is treated as "nothing playing here" rather than noise mistaken for a
  // reading.
  const MIN_RING_MAGNITUDE = 0.006;

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

  function getTuneMixPercent(cents) {
    const abs = Math.abs(cents);

    if (abs <= IN_TUNE_THRESHOLD_CENTS) {
      return 0;
    }

    const t = (abs - IN_TUNE_THRESHOLD_CENTS) / (MAX_UNTUNED_CENTS - IN_TUNE_THRESHOLD_CENTS);
    return Math.round(clamp(t, 0, 1) * 100);
  }

  // Equal temperament only, at whatever A4 is currently set.
  function pianoNoteFrequency(midi, a4) {
    return a4 * Math.pow(2, (midi - 69) / 12);
  }

  // Standard MIDI-to-scientific-pitch-notation octave numbering (midi 69 =
  // A4), matching /tuner/'s noteNameForMidi — e.g. midi 57 -> "A3".
  function noteNameForMidi(midi) {
    const name = NOTE_NAMES[((midi % 12) + 12) % 12];
    const octave = Math.floor(midi / 12) - 1;
    return `${name}${octave}`;
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
  // jitter. Mutates `ring` in place.
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

  function analyzeDisc(disc, buffer, sampleRate, now) {
    disc.rings.forEach((ring) => analyzeRing(ring, buffer, sampleRate, now));
  }

  /* ============================================================
     DISC GRAPHICS
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
  // filled wedges alternating with segmentCount gaps) — this only builds
  // whichever of those wedges actually fall inside the visible arcSpanDeg
  // window, clipping (not dropping) the ones straddling its edges. Slices
  // are centered on multiples of one step from top-center (angle 0),
  // rather than starting a step there, so the window stays bilaterally
  // symmetric.
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

  // Default geometry matches /multistrobe/'s compact piano-keyboard discs —
  // a wide-short viewBox holding only the top 90° of the wheel. Pages that
  // want a bigger, more prominent single disc (e.g. /strobetuner/) pass
  // their own geometry object to buildDisc().
  const DEFAULT_GEOMETRY = {
    cx: 50,
    cy: 52,
    arcSpanDeg: 90,
    viewBox: "0 0 100 56",
    caseR: 48,
    windowR: 42,
    ringOuterR: 39,
    hubR: 5,
    hubDotR: 2.5,
    ringGap: 0.6,
  };

  // Builds one disc's DOM (a wrapper <div> holding an <svg> and a text
  // label) for `name`, with one ring per entry in `midiList` (outermost =
  // lowest octave, innermost = highest — same outer-to-inner convention as
  // /tuner/'s original strobe). Segment count doubles ring by ring outward
  // from the center (2, 4, 8, … ) — the same fan pattern a real optical
  // strobe disc uses.
  function buildDisc(name, midiList, geometryOverrides) {
    const geo = Object.assign({}, DEFAULT_GEOMETRY, geometryOverrides);
    const { cx, cy, arcSpanDeg, viewBox, caseR, windowR, ringOuterR, hubR, hubDotR, ringGap } = geo;
    const halfSpan = arcSpanDeg / 2;

    const wrapper = document.createElement("div");
    wrapper.className = "strobe-disc";

    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", viewBox);
    svg.setAttribute("class", "disc-device");
    svg.setAttribute("role", "presentation");
    svg.setAttribute("focusable", "false");

    const caseShape = document.createElementNS(SVG_NS, "path");
    caseShape.setAttribute("class", "disc-case");
    caseShape.setAttribute("d", sectorPath(cx, cy, caseR, -halfSpan, halfSpan));
    svg.appendChild(caseShape);

    const windowShape = document.createElementNS(SVG_NS, "path");
    windowShape.setAttribute("class", "disc-window");
    windowShape.setAttribute("d", sectorPath(cx, cy, windowR, -halfSpan, halfSpan));
    svg.appendChild(windowShape);

    // A ring rotates a live wedge boundary right up to (and briefly past)
    // the edge of its own segment as it spins, which can carry it outside
    // the window sector altogether — most visible on wide arcs with big,
    // fast-rotating wedges (e.g. /strobetuner/'s single large disc; far
    // less noticeable on /multistrobe/'s small 90°-arc ones, which is why
    // this stayed opt-in rather than always-on). When geo.clipToWindow is
    // set, every ring is confined to the window sector's own shape, same
    // as /tuner/'s original strobe (see #strobeHalfClip). geo.continuousWedges
    // (below) always implies this too, since an unclipped full-circle
    // pattern would show its "back half" outside the intended window.
    let ringsParent = svg;

    if (geo.clipToWindow || geo.continuousWedges) {
      const clipId = `discClip-${Math.random().toString(36).slice(2, 9)}`;
      const clipPath = document.createElementNS(SVG_NS, "clipPath");
      clipPath.setAttribute("id", clipId);
      const clipShape = document.createElementNS(SVG_NS, "path");
      clipShape.setAttribute("d", sectorPath(cx, cy, windowR, -halfSpan, halfSpan));
      clipPath.appendChild(clipShape);
      svg.appendChild(clipPath);

      ringsParent = document.createElementNS(SVG_NS, "g");
      ringsParent.setAttribute("clip-path", `url(#${clipId})`);
      svg.appendChild(ringsParent);
    }

    // A ring built only across the visible arc (plus a small buffer) runs
    // out of wedges to show once it's rotated far enough — the pattern
    // has a beginning and an end, so a sustained sharp/flat note visibly
    // spins the wheel "off the edge" into a blank gap. Building the full
    // 360° pattern instead (still only ever *shown* through the window
    // sector, via the clip above) makes it a genuinely continuous wheel
    // that can spin any amount, in either direction, forever — exactly
    // like the physical disc this is modeled on, which is a full wheel
    // viewed through a narrow window, not a wheel-shaped window itself.
    const wedgeArcSpanDeg = geo.continuousWedges ? 360 : arcSpanDeg;

    const totalRings = midiList.length;
    const availableBand = ringOuterR - hubR - ringGap * (totalRings - 1);
    const bandWidth = availableBand / totalRings;

    const rings = midiList.map((midi, index) => {
      const outerR = ringOuterR - index * (bandWidth + ringGap);
      const innerR = outerR - bandWidth;
      // `index` counts inward from the outermost ring (index 0), but
      // segment count needs to count outward from the center: innermost
      // ring = 2 segments, doubling ring by ring out to the outermost.
      const positionFromCenter = totalRings - 1 - index;
      const segmentCount = Math.pow(2, positionFromCenter + 1);

      const ringGroup = document.createElementNS(SVG_NS, "g");
      ringGroup.setAttribute("class", "disc-ring");
      buildArcRingWedges(ringGroup, cx, cy, innerR, outerR, segmentCount, wedgeArcSpanDeg);
      ringsParent.appendChild(ringGroup);

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
    hub.setAttribute("cx", String(cx));
    hub.setAttribute("cy", String(cy));
    hub.setAttribute("r", String(hubDotR));
    svg.appendChild(hub);

    const label = document.createElement("span");
    label.className = "disc-label";
    label.textContent = name;

    wrapper.appendChild(svg);
    wrapper.appendChild(label);

    return { name, el: wrapper, rings, cx, cy, continuousWedges: Boolean(geo.continuousWedges) };
  }

  // Recomputes every ring's target frequency (and the analysis window that
  // depends on it) from the current A4 — call at load and whenever the
  // reference pitch changes. Any in-flight phase-tracking history is
  // discarded rather than compared against the new target, since it was
  // measuring against a now-stale frequency.
  function recomputeDiscTargets(disc, a4, sampleRate) {
    disc.rings.forEach((ring) => {
      ring.targetFreq = pianoNoteFrequency(ring.midi, a4);
      ring.windowSamples = computeWindowSamples(ring.targetFreq, sampleRate);
      ring.hasPhase = false;
      ring.confident = false;
    });
  }

  /* ============================================================
     RENDERING — every ring independently decides, every frame, whether it
     has a confident reading: idle rings sit dim and motionless (distinct
     from — never confusable with — the green "in tune" state), active
     ones spin according to their own measured cents error.
     ============================================================ */
  function renderDisc(disc, dt) {
    let hasActiveRing = false;
    let hasInTuneRing = false;

    disc.rings.forEach((ring) => {
      const isActive = ring.confident;
      ring.ringGroupEl.classList.toggle("is-active", isActive);

      if (!isActive) {
        ring.ringGroupEl.classList.remove("in-tune");

        // Snapping back to a fixed "0" position the instant a ring loses
        // confidence (then jumping again once it regains it) is what
        // produced the reported stutter — the ring would freeze at
        // whatever angle it was mid-spin at, not at the position this
        // reset forces it to. Continuous-wedge discs (see buildDisc) have
        // no "canonical" rest angle to return to — the pattern repeats
        // perfectly at every angle — so for them it's safe (and far
        // smoother) to just leave the ring exactly where it stopped and
        // resume from there whenever it goes active again. Discs without
        // the full 360° pattern still need this reset: their wedges only
        // exist near angle 0, so idling anywhere else would show gaps.
        if (!disc.continuousWedges) {
          ring.angle = 0;
          ring.ringGroupEl.setAttribute("transform", `rotate(0 ${disc.cx} ${disc.cy})`);
        }

        return;
      }

      hasActiveRing = true;
      const rawCents = ring.smoothedCents;
      const effectiveCents = Math.abs(rawCents) < RING_DEADZONE_CENTS ? 0 : rawCents;
      const inTune = Math.abs(rawCents) <= IN_TUNE_THRESHOLD_CENTS;

      if (inTune) {
        hasInTuneRing = true;
      }

      ring.ringGroupEl.classList.toggle("in-tune", inTune);
      ring.ringGroupEl.style.setProperty("--tune-mix", String(getTuneMixPercent(rawCents)));
      ring.angle = (ring.angle + effectiveCents * RING_ROTATION_SPEED * dt) % 360;
      ring.ringGroupEl.setAttribute("transform", `rotate(${ring.angle.toFixed(2)} ${disc.cx} ${disc.cy})`);
    });

    disc.el.classList.toggle("is-active", hasActiveRing);
    disc.el.classList.toggle("in-tune", hasInTuneRing);

    return { hasActiveRing, hasInTuneRing };
  }

  function resetDisc(disc) {
    disc.el.classList.remove("is-active", "in-tune");

    disc.rings.forEach((ring) => {
      ring.angle = 0;
      ring.hasPhase = false;
      ring.confident = false;
      ring.smoothedCents = 0;
      ring.ringGroupEl.classList.remove("is-active", "in-tune");
      ring.ringGroupEl.setAttribute("transform", `rotate(0 ${disc.cx} ${disc.cy})`);
    });
  }

  global.StrobeDiscEngine = {
    NOTE_NAMES,
    PIANO_MIN_MIDI,
    PIANO_MAX_MIDI,
    ANALYSER_BUFFER_SIZE,
    IN_TUNE_THRESHOLD_CENTS,
    pianoNoteFrequency,
    noteNameForMidi,
    midiListForPitchClass,
    getTuneMixPercent,
    buildDisc,
    recomputeDiscTargets,
    analyzeRing,
    analyzeDisc,
    renderDisc,
    resetDisc,
  };
})(window);
