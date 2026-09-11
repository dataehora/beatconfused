/* ============================================================
   TUNER COMMON — the reusable controls shared by every tuner-family page
   (/tuner/, /strobetuner/, /multistrobe/): Reference Pitch (+ tuning
   standards), the Spectrum Analyser, the generic Frequency Table, the
   Input Monitor's level math, collapsible panels, and the space/arrow
   transport shortcuts. Each page still owns its own audio pipeline and
   visualization — this only holds the parts that are identical (or should
   be) across all three, so a fix or a new tuning standard made here
   applies everywhere at once instead of needing to be copied three times.
   ============================================================ */
(function (global) {
  const NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];

  const MIN_A4 = 392;
  const MAX_A4 = 466;
  const DEFAULT_A4 = 440;

  // A standard 88-key grand piano: A0 (MIDI 21) to C8 (MIDI 108).
  const PIANO_MIN_MIDI = 21;
  const PIANO_MAX_MIDI = 108;

  // The six tuning standards offered under Reference Pitch, in ascending
  // order — also reused to build the Frequency Table's columns.
  const REFERENCE_PITCH_PRESETS = [
    { value: 392, primary: "French Baroque", secondary: "\"Tone de Chambre\"" },
    { value: 415, primary: "Baroque" },
    { value: 432, primary: "Verdi", secondary: "\"Scientific\"" },
    { value: 440, primary: "Standard" },
    { value: 444, primary: "Modern", secondary: "\"Symphony\"" },
    { value: 466, primary: "Italian", secondary: "Renaissance" },
  ];

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

  /* ============================================================
     TUNING STANDARDS (temperaments) — Equal Temperament plus four
     historical/alternate systems, each built from first principles rather
     than a hand-typed cents table. See the per-function comments below for
     how each family is derived; ported verbatim from /tuner/'s original
     implementation.
     ============================================================ */
  const PURE_FIFTH_CENTS = 1200 * Math.log2(3 / 2); // ~701.955
  const PYTHAGOREAN_COMMA_CENTS = 1200 * Math.log2(531441 / 524288); // ~23.460
  const SYNTONIC_COMMA_CENTS = 1200 * Math.log2(81 / 80); // ~21.506

  // Position on the circle of fifths (tonic = 0) for each semitone above the
  // tonic. Derived from: 7 * position ≡ semitone (mod 12), position in -5..6.
  const FIFTHS_POSITION_FOR_SEMITONE = [0, -5, 2, -3, 4, -1, 6, 1, -4, 3, -2, 5];

  // Walks the chain of 11 fifths spanning position -5 to +6, given how many
  // cents the fifth connecting `lowerPosition` to `lowerPosition + 1`
  // deviates from a pure 3:2 (0 = pure, negative = narrowed) — then reduces
  // each position against where a 700-cent equal-tempered fifth would have
  // put it, yielding cents-from-equal-temperament per semitone above tonic.
  function buildFifthsChainOffsets(fifthDeviationCents) {
    const cumulative = { 0: 0 };

    for (let position = 1; position <= 6; position += 1) {
      cumulative[position] = cumulative[position - 1] + PURE_FIFTH_CENTS + fifthDeviationCents(position - 1);
    }

    for (let position = -1; position >= -5; position -= 1) {
      cumulative[position] = cumulative[position + 1] - (PURE_FIFTH_CENTS + fifthDeviationCents(position));
    }

    return FIFTHS_POSITION_FOR_SEMITONE.map((position) => cumulative[position] - position * 700);
  }

  function equalTemperamentOffsets() {
    return new Array(12).fill(0);
  }

  // A "well" temperament: a fixed set of fifths (identified by the lower
  // position of each tempered edge) narrowed by a shared fraction of the
  // Pythagorean comma; every other fifth in the chain stays pure.
  function wellTemperamentOffsets(temperedLowerPositions, temperCents) {
    const tempered = new Set(temperedLowerPositions);
    return buildFifthsChainOffsets((lowerPosition) => (tempered.has(lowerPosition) ? -temperCents : 0));
  }

  // A "regular" temperament: every fifth in the chain is narrowed by the
  // same fraction of the syntonic comma (1/4-comma meantone favors pure
  // major thirds at the cost of a "wolf" fifth far from the tonic).
  function meantoneOffsets(commaFraction) {
    const temperCents = SYNTONIC_COMMA_CENTS * commaFraction;
    return buildFifthsChainOffsets(() => -temperCents);
  }

  // 5-limit just intonation, asymmetric 12-tone chromatic scale (the
  // smallest-integer ratio for each degree) — not derived from a fifths
  // chain, so each degree is given directly as cents from the tonic.
  const JUST_MAJOR_RATIO_CENTS = [
    0,
    1200 * Math.log2(16 / 15),
    1200 * Math.log2(9 / 8),
    1200 * Math.log2(6 / 5),
    1200 * Math.log2(5 / 4),
    1200 * Math.log2(4 / 3),
    1200 * Math.log2(45 / 32),
    1200 * Math.log2(3 / 2),
    1200 * Math.log2(8 / 5),
    1200 * Math.log2(5 / 3),
    1200 * Math.log2(9 / 5),
    1200 * Math.log2(15 / 8),
  ];

  function justIntonationMajorOffsets() {
    return JUST_MAJOR_RATIO_CENTS.map((cents, semitone) => cents - semitone * 100);
  }

  const TEMPERAMENTS = [
    { id: "equal", name: "Equal Temperament", needsKey: false, getOffsets: equalTemperamentOffsets },
    { id: "vallotti", name: "Vallotti", needsKey: true, getOffsets: () => wellTemperamentOffsets([-1, 0, 1, 2, 3, 4], PYTHAGOREAN_COMMA_CENTS / 6) },
    { id: "young2", name: "Young II", needsKey: true, getOffsets: () => wellTemperamentOffsets([0, 1, 2, 3, 4, 5], PYTHAGOREAN_COMMA_CENTS / 6) },
    { id: "meantone4", name: "1/4-Comma Meantone", needsKey: true, getOffsets: () => meantoneOffsets(0.25) },
    { id: "justMajor", name: "Just Intonation (Major)", needsKey: true, getOffsets: justIntonationMajorOffsets },
  ];

  function getTemperamentById(id) {
    return TEMPERAMENTS.find((temperament) => temperament.id === id) || TEMPERAMENTS[0];
  }

  function noteNameForMidi(midi) {
    const name = NOTE_NAMES[((midi % 12) + 12) % 12];
    const octave = Math.floor(midi / 12) - 1;
    return `${name}${octave}`;
  }

  /* ============================================================
     REFERENCE PITCH — wires the A4 number input, slider, ± buttons and
     (if present on the page) the preset radio list into one controller.
     Every tuner-family page uses the same MIN_A4..MAX_A4 range and the
     same double-click-to-reset gesture, so this is the entire control,
     not just its math.
     ============================================================ */
  function setupReferencePitch(options) {
    const { pitchInput, pitchRange, decreaseBtn, increaseBtn, presetInputs, onChange } = options;
    const presets = presetInputs || [];
    let a4 = DEFAULT_A4;

    function apply(value) {
      a4 = clamp(Math.round(Number(value) || DEFAULT_A4), MIN_A4, MAX_A4);

      if (pitchInput) pitchInput.value = String(a4);
      if (pitchRange) pitchRange.value = String(a4);

      presets.forEach((input) => {
        input.checked = Number(input.value) === a4;
      });

      if (onChange) onChange(a4);
      return a4;
    }

    if (pitchInput) pitchInput.addEventListener("input", (event) => apply(event.target.value));

    if (pitchRange) {
      pitchRange.addEventListener("input", (event) => apply(event.target.value));
      // A double-click anywhere on the reference pitch bar snaps it back to A440.
      pitchRange.addEventListener("dblclick", () => apply(DEFAULT_A4));
    }

    if (decreaseBtn) decreaseBtn.addEventListener("click", () => apply(a4 - 1));
    if (increaseBtn) increaseBtn.addEventListener("click", () => apply(a4 + 1));

    presets.forEach((input) => {
      input.addEventListener("change", () => apply(input.value));
    });

    return {
      getA4: () => a4,
      setA4: apply,
    };
  }

  /* ============================================================
     TUNING STANDARD — populates and wires the Standard/Key select pair(s).
     A page can have more than one instance of the pair on screen at once
     (e.g. /tuner/'s Tuning Standard panel and the one above its Frequency
     Table) — every instance passed in stays in sync with a single change,
     regardless of which one the user touched.
     ============================================================ */
  function setupTemperament(options) {
    const { selects, keyRows, keySelects, onChange } = options;
    const state = {
      temperamentId: TEMPERAMENTS[0].id,
      temperamentKey: 0,
      temperamentOffsets: TEMPERAMENTS[0].getOffsets(),
    };

    // Options are generated from TEMPERAMENTS / NOTE_NAMES rather than
    // hand-written in the markup, so the dropdowns can never drift out of
    // sync with the tables that actually compute the frequencies.
    selects.forEach((select) => {
      TEMPERAMENTS.forEach((temperament) => {
        const option = document.createElement("option");
        option.value = temperament.id;
        option.textContent = temperament.name;
        select.appendChild(option);
      });
    });

    (keySelects || []).forEach((select) => {
      NOTE_NAMES.forEach((name, pitchClass) => {
        const option = document.createElement("option");
        option.value = String(pitchClass);
        option.textContent = name;
        select.appendChild(option);
      });
    });

    function setTemperament(id) {
      state.temperamentId = id;
      const temperament = getTemperamentById(id);
      state.temperamentOffsets = temperament.getOffsets();

      selects.forEach((select) => {
        select.value = id;
      });

      (keyRows || []).forEach((row) => {
        row.hidden = !temperament.needsKey;
      });

      if (onChange) onChange(state);
    }

    function setKey(pitchClass) {
      state.temperamentKey = clamp(Math.round(Number(pitchClass) || 0), 0, 11);

      (keySelects || []).forEach((select) => {
        select.value = String(state.temperamentKey);
      });

      if (onChange) onChange(state);
    }

    selects.forEach((select) => {
      select.addEventListener("change", (event) => setTemperament(event.target.value));
    });

    (keySelects || []).forEach((select) => {
      select.addEventListener("change", (event) => setKey(event.target.value));
    });

    return {
      state,
      getTemperament: () => getTemperamentById(state.temperamentId),
      setTemperament,
      setKey,
      // Cents-from-equal-temperament for a given MIDI note, rotated to
      // whichever pitch class the Key selector is set to.
      getOffsetCents(midi) {
        const pitchClass = ((midi % 12) + 12) % 12;
        const semitoneAboveTonic = ((pitchClass - state.temperamentKey) % 12 + 12) % 12;
        return state.temperamentOffsets[semitoneAboveTonic];
      },
      pianoNoteFrequency(midi, a4) {
        const equalFrequency = a4 * Math.pow(2, (midi - 69) / 12);
        return equalFrequency * Math.pow(2, this.getOffsetCents(midi) / 1200);
      },
    };
  }

  /* ============================================================
     FREQUENCY TABLE — the generic /tuner/-style table: one column per
     Reference Pitch standard, one row per key of an 88-key piano (A0-C8).
     /strobetuner/ builds its own specialized note-by-octave grid instead
     (its layout is fundamentally different), so that one stays page-local.
     ============================================================ */
  function buildFrequencyTable(options) {
    const { headRow, body, pianoNoteFrequency } = options;

    if (headRow.childElementCount === 0) {
      REFERENCE_PITCH_PRESETS.forEach((preset) => {
        const th = document.createElement("th");
        const freqEl = document.createElement("span");
        freqEl.className = "freq-table-col-freq";
        freqEl.textContent = `${preset.value} Hz`;
        th.appendChild(freqEl);

        if (preset.primary) {
          const primaryEl = document.createElement("span");
          primaryEl.className = "freq-table-col-name-primary";
          primaryEl.textContent = preset.primary;
          th.appendChild(primaryEl);
        }

        if (preset.secondary) {
          const secondaryEl = document.createElement("span");
          secondaryEl.className = "freq-table-col-name-secondary";
          secondaryEl.textContent = preset.secondary;
          th.appendChild(secondaryEl);
        }

        headRow.appendChild(th);
      });
    }

    body.innerHTML = "";

    for (let midi = PIANO_MIN_MIDI; midi <= PIANO_MAX_MIDI; midi += 1) {
      const row = document.createElement("tr");
      const noteCell = document.createElement("td");
      noteCell.textContent = noteNameForMidi(midi);
      row.appendChild(noteCell);

      REFERENCE_PITCH_PRESETS.forEach((preset) => {
        const cell = document.createElement("td");
        cell.textContent = pianoNoteFrequency(midi, preset.value).toFixed(2);
        row.appendChild(cell);
      });

      body.appendChild(row);
    }
  }

  /* ============================================================
     SPECTRUM ANALYSER — log-scaled (so an octave always takes up the same
     width on screen) across the page's current A0-C8 range, in the same
     vintage-LED-ladder or modern-DAW-curve styles. `barWidth` is derived
     from the *exact* bar count rather than floor()'d independently, so the
     bars tile edge to edge — the highest frequency reaches the right edge
     of the display exactly as the lowest one already reaches the left.
     ============================================================ */
  function createSpectrumAnalyser(options) {
    const { canvas, lowLabel, refLabel, highLabel, styleCheckbox, styleToggleEl } = options;
    const ctx = canvas.getContext("2d");
    let style = "vintage"; // "vintage" | "modern"

    function sizeCanvas() {
      const rect = canvas.getBoundingClientRect();

      if (rect.width === 0 || rect.height === 0) {
        return;
      }

      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
    }

    function clear() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }

    function drawVintage(freqData, width, height, barCount, barWidth, logMin, logMax, hzPerBin) {
      const segmentHeight = 6;
      const segmentGap = 2;
      const segmentUnit = segmentHeight + segmentGap;
      const totalSegments = Math.max(1, Math.floor(height / segmentUnit));

      for (let i = 0; i < barCount; i += 1) {
        const t = barCount > 1 ? i / (barCount - 1) : 0;
        const freq = Math.pow(2, logMin + t * (logMax - logMin));
        const binIndex = Math.min(freqData.length - 1, Math.round(freq / hzPerBin));
        const magnitude = freqData[binIndex] / 255;
        const litSegments = Math.round(magnitude * totalSegments);

        for (let s = 0; s < litSegments; s += 1) {
          const ratio = s / totalSegments;

          if (ratio > 0.9) {
            ctx.fillStyle = "#c0453a";
          } else if (ratio > 0.7) {
            ctx.fillStyle = "#d9b23c";
          } else {
            ctx.fillStyle = "#5f9153";
          }

          const y = height - (s + 1) * segmentUnit + segmentGap;
          const x = Math.round(i * barWidth);
          const nextX = Math.round((i + 1) * barWidth);
          ctx.fillRect(x, y, Math.max(1, nextX - x - 1), segmentHeight);
        }
      }
    }

    function drawModern(freqData, width, height, barCount, barWidth, logMin, logMax, hzPerBin) {
      const points = [];

      for (let i = 0; i < barCount; i += 1) {
        const t = barCount > 1 ? i / (barCount - 1) : 0;
        const freq = Math.pow(2, logMin + t * (logMax - logMin));
        const binIndex = Math.min(freqData.length - 1, Math.round(freq / hzPerBin));
        const magnitude = freqData[binIndex] / 255;
        points.push({ x: i * barWidth + barWidth / 2, y: height - magnitude * height });
      }

      if (points.length < 2) {
        return;
      }

      const first = points[0];
      const last = points[points.length - 1];

      ctx.beginPath();
      ctx.moveTo(first.x, height);
      ctx.lineTo(first.x, first.y);

      for (let i = 1; i < points.length - 1; i += 1) {
        const midX = (points[i].x + points[i + 1].x) / 2;
        const midY = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, midX, midY);
      }

      ctx.lineTo(last.x, last.y);
      ctx.lineTo(last.x, height);
      ctx.closePath();

      const fillGradient = ctx.createLinearGradient(0, 0, 0, height);
      fillGradient.addColorStop(0, "rgba(168, 205, 240, 0.55)");
      fillGradient.addColorStop(1, "rgba(63, 110, 160, 0)");
      ctx.fillStyle = fillGradient;
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(first.x, first.y);

      for (let i = 1; i < points.length - 1; i += 1) {
        const midX = (points[i].x + points[i + 1].x) / 2;
        const midY = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, midX, midY);
      }

      ctx.lineTo(last.x, last.y);
      ctx.strokeStyle = "#a8cdf0";
      ctx.lineWidth = 1.5;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.stroke();
    }

    // `range` is {min, max} in Hz (usually A0..C8 at the page's current A4)
    // and `fftSize` must match the live AnalyserNode's own fftSize (pages
    // differ: /tuner/ uses a short one tuned for autocorrelation, /strobetuner/
    // and /multistrobe/ use a much longer one for their Goertzel rings).
    function update(freqData, sampleRate, fftSize, range) {
      const width = canvas.width;
      const height = canvas.height;
      clear();

      const hzPerBin = sampleRate / fftSize;
      const logMin = Math.log2(range.min);
      const logMax = Math.log2(range.max);
      // A fixed bar *count* (not a fixed bar width floor()'d down) means
      // barCount * barWidth always equals the canvas width exactly, so the
      // last bar's right edge lands on the last pixel column instead of
      // leaving an uncovered gap at the high-frequency end.
      const barCount = Math.max(1, Math.round(width / (width / 160)));
      const barWidth = width / barCount;

      if (style === "modern") {
        drawModern(freqData, width, height, barCount, barWidth, logMin, logMax, hzPerBin);
      } else {
        drawVintage(freqData, width, height, barCount, barWidth, logMin, logMax, hzPerBin);
      }
    }

    function updateLabels(range, a4) {
      if (lowLabel) lowLabel.textContent = `A0 · ${range.min.toFixed(1)} Hz`;
      if (refLabel) refLabel.textContent = `A4 · ${a4.toFixed(1)} Hz`;
      if (highLabel) highLabel.textContent = `C8 · ${range.max.toFixed(1)} Hz`;
    }

    function setStyle(name) {
      style = name;

      if (styleCheckbox) styleCheckbox.checked = name === "modern";

      if (styleToggleEl) {
        styleToggleEl.querySelectorAll(".style-toggle-label").forEach((label) => {
          label.classList.toggle("is-active", label.dataset.style === name);
        });
      }
    }

    if (styleCheckbox) {
      styleCheckbox.addEventListener("change", () => {
        setStyle(styleCheckbox.checked ? "modern" : "vintage");
      });
    }

    window.addEventListener("resize", sizeCanvas);

    return { sizeCanvas, clear, update, updateLabels, setStyle, getStyle: () => style };
  }

  /* ============================================================
     INPUT MONITOR — RMS-to-dB level math shared by every page's gain +
     level meter, and the mic-gain slider wiring.
     ============================================================ */
  const LEVEL_FLOOR_DB = -60;

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

  function createInputMonitor(options) {
    const { gainRange, gainValueLabel, levelFill, levelValueLabel, getGainNode, audioContextRef } = options;

    function updateLevelMeter(rms) {
      const db = rmsToDb(rms);
      const percent = clamp(((db - LEVEL_FLOOR_DB) / -LEVEL_FLOOR_DB) * 100, 0, 100);
      levelFill.style.height = `${percent}%`;
      levelFill.style.setProperty("--level-mix", String(Math.round(clamp((db + 12) / 12, 0, 1) * 100)));
      levelValueLabel.textContent = db <= LEVEL_FLOOR_DB ? "−∞ dB" : `${db.toFixed(1)} dB`;
    }

    function reset() {
      levelFill.style.height = "0%";
      levelFill.style.setProperty("--level-mix", "0");
      levelValueLabel.textContent = "−∞ dB";
    }

    if (gainRange && gainValueLabel) {
      gainValueLabel.textContent = `${Number(gainRange.value).toFixed(1)}×`;

      gainRange.addEventListener("input", (event) => {
        const gain = Number(event.target.value);
        gainValueLabel.textContent = `${gain.toFixed(1)}×`;
        const gainNode = getGainNode ? getGainNode() : null;
        const ctx = audioContextRef ? audioContextRef() : null;

        if (gainNode && ctx) {
          gainNode.gain.setTargetAtTime(gain, ctx.currentTime, 0.01);
        }
      });
    }

    return { computeRms, rmsToDb, updateLevelMeter, reset };
  }

  /* ============================================================
     COLLAPSIBLE PANELS — every panel-header's toggle hides everything in
     its .control-block except the header itself.
     ============================================================ */
  function wireCollapsibles(onExpand) {
    document.querySelectorAll(".collapse-toggle").forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const panel = toggle.closest(".control-block");
        const collapsed = panel.classList.toggle("is-collapsed");
        toggle.setAttribute("aria-expanded", String(!collapsed));

        if (!collapsed && onExpand) {
          onExpand(panel);
        }
      });
    });
  }

  /* ============================================================
     TRANSPORT SHORTCUTS — Space toggles the tuner, Up/Down nudges the A4
     reference pitch by a semitone's worth of cents (1 Hz), same on every
     page. Ignored while a form control has focus, so typing into a select
     or number input never fights with the shortcut.
     ============================================================ */
  function wireTransportShortcuts(options) {
    const { onToggle, onA4Delta } = options;

    document.addEventListener("keydown", (event) => {
      const focusedTag = document.activeElement && document.activeElement.tagName;
      const isFormElement = focusedTag === "INPUT" || focusedTag === "SELECT" || focusedTag === "TEXTAREA";

      if (event.code === "Space" && !isFormElement) {
        event.preventDefault();
        if (onToggle) onToggle();
      }

      if (event.key === "ArrowUp" && !isFormElement) {
        event.preventDefault();
        if (onA4Delta) onA4Delta(1);
      }

      if (event.key === "ArrowDown" && !isFormElement) {
        event.preventDefault();
        if (onA4Delta) onA4Delta(-1);
      }
    });
  }

  // The exact wording every page uses for getUserMedia failures and idle/
  // listening status, so the microphone experience reads identically no
  // matter which tuner page you're on.
  const MIC_MESSAGES = {
    idle: "Uses your microphone. Nothing is recorded or sent anywhere.",
    listening: "Listening… play a note.",
    notSupported: "Microphone access isn't supported in this browser.",
    denied: "Microphone access was denied. Allow it in your browser's address bar and try again.",
    notFound: "No microphone was found on this device.",
    genericError: "Couldn't access the microphone. Please try again.",
    webAudioNotSupported: "Web Audio isn't supported in this browser.",
  };

  function setMicStatusFactory(el) {
    return function setMicStatus(message, isError) {
      el.textContent = message;
      el.classList.toggle("is-error", Boolean(isError));
    };
  }

  global.TunerCommon = {
    NOTE_NAMES,
    MIN_A4,
    MAX_A4,
    DEFAULT_A4,
    PIANO_MIN_MIDI,
    PIANO_MAX_MIDI,
    REFERENCE_PITCH_PRESETS,
    TEMPERAMENTS,
    MIC_MESSAGES,
    clamp,
    noteNameForMidi,
    getTemperamentById,
    setupReferencePitch,
    setupTemperament,
    buildFrequencyTable,
    createSpectrumAnalyser,
    computeRms,
    rmsToDb,
    createInputMonitor,
    wireCollapsibles,
    wireTransportShortcuts,
    setMicStatusFactory,
  };
})(window);
