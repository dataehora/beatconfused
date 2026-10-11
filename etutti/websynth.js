/* ============================================================
   eTUTTI WEB SYNTH — the eTuttino's sounds in the browser (Web Audio),
   so anyone can try them before building one.

   It takes the same Control Change messages as the Teensy firmware
   (etutti/firmware/etutti_synth), so the page drives both with one call:
     - accordion: the same additive free-reed waveforms (harmonic counts,
       roll-off, ripple and phases as buildReedTable in the sketch), four
       reeds per note switched by the register bit mask, M2 detuned by the
       reed tuning, bellows attack/release;
     - synth: three oscillators (the browser's are band-limited, like the
       firmware's BANDLIMIT waves), level, detune, octave, full ADSR;
     - piano / guitar / bass: the Teensy plays recorded samples; here they
       are approximated by decaying, slightly inharmonic partials (bass =
       the guitar two octaves down, as on the Teensy);
     - tone low-pass, room reverb, volume, as CC 74 / 91 / 7.
   Nothing makes a sound until enable() is called from a user gesture
   (the page's "Listen in this browser" switch).
   ============================================================ */
(function () {
  "use strict";

  const INST = { ACCORDION: 0, PIANO: 1, BASS: 2, GUITAR: 3, SYNTH: 4 };
  const REED_GAIN = [0.42, 0.42, 0.42, 0.3]; // 16', 8' M1, 8' M2, 4'
  const SYNTH_WAVES = ["sine", "triangle", "sawtooth", "square"];
  const MAX_VOICES = 16;
  const VOICE_SCALE = 0.13; // keeps a full chord under the limiter

  const midiToFreq = (n) => 440 * Math.pow(2, (n - 69) / 12);
  const quadraticMs = (v, max) => Math.pow(v / 127, 2) * max;

  // One period of a free reed, as the firmware's buildReedTable: every
  // harmonic, falling off as 1/n^k with a formant ripple and spread phases.
  function reedWave(ctx, harmonics, rolloff, ripple) {
    const real = new Float32Array(harmonics + 1);
    const imag = new Float32Array(harmonics + 1);
    for (let n = 1; n <= harmonics; n += 1) {
      const amp = Math.pow(n, -rolloff) * (1 + ripple * Math.cos(n * 1.3));
      const phase = 0.7 * n * n;
      // a·sin(nωt + φ) = a·sinφ·cos(nωt) + a·cosφ·sin(nωt)
      real[n] = amp * Math.sin(phase);
      imag[n] = amp * Math.cos(phase);
    }
    return ctx.createPeriodicWave(real, imag);
  }

  function roomImpulse(ctx, seconds, decay) {
    const len = Math.floor(ctx.sampleRate * seconds);
    const buf = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let ch = 0; ch < 2; ch += 1) {
      const data = buf.getChannelData(ch);
      let lp = 0;
      for (let i = 0; i < len; i += 1) {
        const t = i / ctx.sampleRate;
        lp += 0.35 * (Math.random() * 2 - 1 - lp); // a little damping
        data[i] = lp * Math.exp(-t * decay);
      }
    }
    return buf;
  }

  function create() {
    const cc = {
      7: 90, 9: 64, 20: 64, 21: 64, 22: 96, 25: 0, 26: 6, 27: 0, 28: 100, 29: 80, 30: 50,
      72: 21, 73: 14, 74: 110, 75: 49, 79: 89, 85: 64, 86: 73, 87: 64, 91: 25, 102: 64, 103: 64, 104: 0,
    };
    let ctx = null;
    let nodes = null;
    let waves = null;
    let on = false;
    const voices = new Map(); // note -> voice
    let age = 0;

    function build() {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      const bus = ctx.createGain();
      const tone = ctx.createBiquadFilter();
      tone.type = "lowpass";
      tone.Q.value = 0.707;
      const dry = ctx.createGain();
      const verb = ctx.createConvolver();
      verb.buffer = roomImpulse(ctx, 2.2, 3.2);
      const wet = ctx.createGain();
      const volume = ctx.createGain();
      const limiter = ctx.createDynamicsCompressor();
      limiter.threshold.value = -10;
      limiter.ratio.value = 12;
      limiter.attack.value = 0.003;
      limiter.release.value = 0.15;
      bus.connect(tone);
      tone.connect(dry).connect(volume);
      tone.connect(verb).connect(wet).connect(volume);
      volume.connect(limiter).connect(ctx.destination);
      nodes = { bus, tone, dry, wet, volume };
      waves = {
        open: reedWave(ctx, 20, 1.05, 0.25),
        cassotto: reedWave(ctx, 14, 1.85, 0.2),
        piccolo: reedWave(ctx, 10, 1.2, 0.2),
      };
      applyMix();
    }

    function applyMix() {
      if (!nodes) return;
      const t = ctx.currentTime;
      const hz = Math.min(40 * Math.pow(2, (9 * cc[74]) / 127), 16000);
      nodes.tone.frequency.setTargetAtTime(hz, t, 0.02);
      const w = cc[91] / 127;
      nodes.dry.gain.setTargetAtTime(1 - 0.35 * w, t, 0.02);
      nodes.wet.gain.setTargetAtTime(0.6 * w, t, 0.02);
      nodes.volume.gain.setTargetAtTime(1.6 * Math.pow(cc[7] / 127, 1.5), t, 0.02);
    }

    const instrument = () => Math.min(Math.floor(cc[25] / 16), 4);
    const reedCents = () => Math.min(cc[27], 30);

    // ---------------------------------------------------------- voices
    function envelopeGain(peak, attackMs, decayMs, sustain) {
      const g = ctx.createGain();
      const t = ctx.currentTime;
      g.gain.setValueAtTime(0, t);
      const a = Math.max(attackMs, 4) / 1000;
      g.gain.linearRampToValueAtTime(peak, t + a);
      if (decayMs !== null) g.gain.setTargetAtTime(peak * sustain, t + a, Math.max(decayMs, 5) / 3000);
      return g;
    }

    function release(g, ms) {
      const t = ctx.currentTime;
      g.gain.cancelScheduledValues(t);
      g.gain.setValueAtTime(g.gain.value, t);
      g.gain.setTargetAtTime(0, t, Math.max(ms, 8) / 3000);
      return t + Math.max(ms, 8) / 1000 + 0.05;
    }

    function accordionVoice(note, vel) {
      const amp = (0.2 + 0.8 * (vel / 127)) * VOICE_SCALE;
      const env = envelopeGain(amp, quadraticMs(cc[73], 2000), null, 1);
      env.connect(nodes.bus);
      const reeds = [
        { bit: 1, wave: waves.cassotto, note: note - 12, cents: 0 },
        { bit: 2, wave: waves.open, note, cents: 0 },
        { bit: 4, wave: waves.cassotto, note, cents: reedCents() },
        { bit: 8, wave: waves.piccolo, note: note + 12, cents: 0 },
      ];
      const oscs = [];
      reeds.forEach((r, i) => {
        if (!(cc[26] & r.bit)) return;
        const osc = ctx.createOscillator();
        osc.setPeriodicWave(r.wave);
        osc.frequency.value = midiToFreq(r.note);
        osc.detune.value = r.cents;
        const g = ctx.createGain();
        g.gain.value = REED_GAIN[i];
        osc.connect(g).connect(env);
        osc.start();
        oscs.push(osc);
      });
      return {
        stop() {
          const end = release(env, quadraticMs(cc[72], 3000));
          oscs.forEach((o) => o.stop(end));
        },
        kill() { oscs.forEach((o) => o.stop()); env.disconnect(); },
      };
    }

    function synthVoice(note, vel) {
      const amp = (0.2 + 0.8 * (vel / 127)) * VOICE_SCALE * 2.4; // three plain waves sit lower than four reeds
      const env = envelopeGain(amp, quadraticMs(cc[73], 2000), quadraticMs(cc[75], 2000), cc[79] / 127);
      env.connect(nodes.bus);
      const oscs = [0, 1, 2].map((o) => {
        const osc = ctx.createOscillator();
        osc.type = SYNTH_WAVES[Math.min(Math.floor(cc[20 + o] / 32), 3)];
        const oct = cc[102 + o] < 43 ? -1 : cc[102 + o] < 85 ? 0 : 1;
        osc.frequency.value = midiToFreq(note + 12 * oct);
        osc.detune.value = ((cc[85 + o] - 64) / 64) * 50;
        const g = ctx.createGain();
        g.gain.value = 0.45 * (cc[28 + o] / 127);
        osc.connect(g).connect(env);
        osc.start();
        return osc;
      });
      return {
        stop() {
          const end = release(env, quadraticMs(cc[72], 3000));
          oscs.forEach((o) => o.stop(end));
        },
        kill() { oscs.forEach((o) => o.stop()); env.disconnect(); },
      };
    }

    // Struck / plucked strings: decaying partials. Piano partials are
    // stretched (string stiffness) and brighten with velocity; the guitar's
    // follow its pluck point and fade faster in the treble.
    function stringVoice(note, vel, kind) {
      const f0 = midiToFreq(note);
      const v = vel / 127;
      const out = ctx.createGain();
      out.gain.value = VOICE_SCALE * (kind === "piano" ? 1.05 : 1.6) * (0.15 + 0.85 * Math.pow(v, 1.4));
      out.connect(nodes.bus);
      const t = ctx.currentTime;
      const ring = kind === "piano" ? 7 * Math.pow(0.5, (note - 48) / 18) : 3.2 * Math.pow(0.5, (note - 40) / 24);
      const oscs = [];
      const count = 12;
      for (let n = 1; n <= count; n += 1) {
        const f = kind === "piano" ? n * f0 * Math.sqrt(1 + 0.0004 * n * n) : n * f0;
        if (f > 15000) break;
        let a = kind === "piano"
          ? Math.pow(n, -1.1 - 0.9 * (1 - v))
          : Math.abs(Math.sin(n * Math.PI * 0.18)) / Math.pow(n, 1.3);
        if (a < 0.002) continue;
        const osc = ctx.createOscillator();
        osc.frequency.value = f;
        const g = ctx.createGain();
        const tau = Math.max(0.08, ring / (1 + (kind === "piano" ? 0.35 : 0.6) * (n - 1)));
        g.gain.setValueAtTime(0, t);
        g.gain.linearRampToValueAtTime(a, t + (kind === "piano" ? 0.003 : 0.002));
        g.gain.setTargetAtTime(0, t + 0.004, tau / 3);
        osc.connect(g).connect(out);
        osc.start(t);
        osc.stop(t + tau * 2.5 + 0.1);
        oscs.push(osc);
      }
      return {
        stop() {
          const end = release(out, kind === "piano" ? 260 : 180);
          oscs.forEach((o) => { try { o.stop(end); } catch (e) { /* already stopped */ } });
        },
        kill() { oscs.forEach((o) => { try { o.stop(); } catch (e) { /* already stopped */ } }); out.disconnect(); },
      };
    }

    function startVoice(note, vel) {
      switch (instrument()) {
        case INST.PIANO: return stringVoice(note, vel, "piano");
        case INST.GUITAR: return stringVoice(note, vel, "guitar");
        case INST.BASS: return stringVoice(note - 24, vel, "guitar");
        case INST.SYNTH: return synthVoice(note, vel);
        default: return accordionVoice(note, vel);
      }
    }

    // ---------------------------------------------------------- public
    return {
      async enable() {
        if (!ctx) build();
        await ctx.resume();
        on = true;
      },
      disable() {
        on = false;
        this.allOff();
        if (ctx) ctx.suspend();
      },
      isOn: () => on,
      cc(number, value) {
        cc[number] = value;
        if (number === 7 || number === 74 || number === 91) applyMix();
        if (number === 25 || number === 120) this.allOff();
        if (number === 123) voices.forEach((v) => v.stop());
      },
      noteOn(note, velocity) {
        if (!on || !ctx) return;
        if (voices.has(note)) voices.get(note).kill();
        if (voices.size >= MAX_VOICES) {
          let oldest = null;
          voices.forEach((v, n) => { if (!oldest || v.age < voices.get(oldest).age) oldest = n; });
          voices.get(oldest).kill();
          voices.delete(oldest);
        }
        const v = startVoice(note, velocity);
        v.age = ++age;
        voices.set(note, v);
      },
      noteOff(note) {
        const v = voices.get(note);
        if (!v) return;
        v.stop();
        voices.delete(note);
      },
      allOff() {
        voices.forEach((v) => v.kill());
        voices.clear();
      },
    };
  }

  window.EtuttiWebSynth = { create };
})();
