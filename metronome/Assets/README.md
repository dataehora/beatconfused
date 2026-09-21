# Metronome sounds

The three sound tones (Wood, Cymbal, Agogô) ship with the `.wav` files
in this folder by default — they're picked up automatically and used
instead of the built-in single-oscillator synth. Each is an original,
royalty-free recording, rendered offline via physically-modeled synthesis
(damped-formant partials + filtered noise, the technique classic drum
machines and bell instruments use) rather than downloaded, so there is no
licensing ambiguity. Deleting a file just falls back to the synthesised
click for that tone/beat combination — nothing here is required.

Each file is looked up as `.mp3`, then `.ogg`, then `.wav` (only supply
one format per sound unless you want a specific fallback order).

Filename pattern: `{tone}_{beat}.{ext}` — the "Agogô" tone keeps the
`cowbell` filename prefix internally (it's the same UI slot, just
retuned), so its files are still `cowbell_*`.

| Tone | Accent (downbeat) | Beat | Subdivision |
| --- | --- | --- | --- |
| Wood | `wood_accent` | `wood_beat` | `wood_subdivision` |
| Cymbal | `cymbal_accent` | `cymbal_beat` | `cymbal_subdivision` |
| Agogô | `cowbell_accent` | `cowbell_beat` | `cowbell_subdivision` |

- **Accent** plays on beat 1 of the measure. For Agogô this is tuned to
  the high bell (~1180 Hz) of a real two-bell agogô.
- **Beat** plays on every other regular beat. For Agogô this is the low
  bell (~760 Hz) — real agogô playing alternates the two bells rather
  than just playing one bell louder.
- **Subdivision** plays on the extra pulses when beat subdivision is set above 1.

You can supply as few or as many of the 9 as you like — e.g. replacing
just `wood_accent.mp3` and `wood_beat.mp3` still leaves subdivisions on
the bundled `wood_subdivision.wav`.
