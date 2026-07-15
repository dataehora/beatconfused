# Custom metronome sounds

Drop audio files in this folder to override the built-in synthesised
clicks. Nothing here is required — any tone/beat combination without a
matching file just keeps using the synthesised sound.

Each file is looked up as `.mp3`, then `.ogg`, then `.wav` (only supply
one format per sound unless you want a specific fallback order).

Filename pattern: `{tone}_{beat}.{ext}`

| Tone | Accent (downbeat) | Beat | Subdivision |
| --- | --- | --- | --- |
| Wood | `wood_accent` | `wood_beat` | `wood_subdivision` |
| Cymbal | `cymbal_accent` | `cymbal_beat` | `cymbal_subdivision` |
| Cowbell | `cowbell_accent` | `cowbell_beat` | `cowbell_subdivision` |
| Bossa | `bossa_accent` | `bossa_beat` | `bossa_subdivision` |
| Electronic | `electronic_accent` | `electronic_beat` | `electronic_subdivision` |
| Jazz | `jazz_accent` | `jazz_beat` | `jazz_subdivision` |

- **Accent** plays on beat 1 of the measure.
- **Beat** plays on every other regular beat.
- **Subdivision** plays on the extra pulses when beat subdivision is set above 1.

You can supply as few or as many of the 18 as you like — e.g. just
`wood_accent.mp3` and `wood_beat.mp3` still leaves subdivisions on the
synthesised wood click.
