# BeatConfused

A small web studio of fast, elegant, install-free music tools. Every tool
is plain HTML, CSS and vanilla JavaScript with the Web Audio API — no build
step, no dependencies, no accounts, works offline after first load.

Live at [beatconfused.com](https://beatconfused.com).

## Tools

| Tool | Path | What it does |
| --- | --- | --- |
| **Metronome** | [`/metronome/`](https://beatconfused.com/metronome/) | Tap tempo, organized time signatures, beat subdivisions, counting modes, sound styles, and pulse / number / pendulum visuals. |
| **Tuner** | [`/tuner/`](https://beatconfused.com/tuner/) | Chromatic instrument tuner with needle, strobe and LED-meter displays, an adjustable A4 reference pitch, historical tuning standards, a test-tone generator, and a spectrum analyser. |
| **Octave Strobe Tuner** | [`/strobetuner/`](https://beatconfused.com/strobetuner/) | Identifies the note being played and shows its tuning across every octave at once on a single strobe disc. |
| **Chromatic Strobe Tuner** | [`/multistrobe/`](https://beatconfused.com/multistrobe/) | One dedicated strobe wheel per note, laid out like a piano keyboard, each with a ring per octave across the 88-key range. |

## Repository layout

```
index.html            Studio landing page (tool cards + JSON-LD)
styles.css             Landing-page styles
metronome/             Metronome — index.html, script.js, styles.css, Assets/
tuner/                 Tuner — index.html, script.js, styles.css
strobetuner/           Octave Strobe Tuner — index.html, script.js, styles.css
multistrobe/           Chromatic Strobe Tuner — index.html, script.js, styles.css
binfacevsfarage/       Standalone browser game (not linked from the studio)
shared/                Assets shared across tools
CNAME, robots.txt, sitemap.xml   Hosting + crawl metadata
```

## Metronome controls

### Tempo
- **Slider** / **input field** — smooth or direct BPM entry (40–240)
- **+/- buttons** — step by 5 BPM
- **Tap tempo** — tap the button or press `T` to detect BPM
- **Arrow keys** — Up / Down to adjust BPM

### Beat settings
- **Time signature** — organized simple, compound and odd meters
- **Beat subdivision** — split each beat into more pulses
- **Tempo counting** — beat count, measure + beat, or hidden
- **Beat visual** — pulse, numbers, or pendulum
- **Sound style** — electronic, bossa, jazz, wood, cymbal, cowbell
- **Sound / vibration toggles** and **volume control**

### Keyboard shortcuts
- **Space** — start / stop
- **Arrow Up / Down** — BPM ±5
- **T** — tap tempo

### Custom sounds
Drop `{style}_{accent|beat|subdivision}` audio files (`.mp3`, then `.ogg`,
then `.wav`) into `metronome/Assets/` and they replace the synthesised click
for that combination. Anything not supplied keeps the built-in sound, so the
metronome always has audio even with no custom assets.

## Tuner controls

- **Start Tuner** — vintage-style slide switch above the display; turns the
  microphone on. A "no signal" sign appears below the display after ~3s of
  silence while running.
- **Display** — needle, strobe or LED meter
- **Input Monitor** — microphone gain boost and a live level meter
- **Reference Pitch** — A4 from 392–466 Hz, with historical presets
  (French Baroque, Baroque, Verdi, Standard, Modern, Italian Renaissance)
- **Tuning Standard** — Equal Temperament plus Vallotti, Young II,
  1/4-comma meantone and Just Intonation, each built from first principles
- **Test Tone** — a pure tone fed straight into the tuner, no mic needed
- **Spectrum Analyser** — vintage or modern style
- **Frequency Table** — every note of an 88-key piano under each standard

## Technical stack

- **HTML5 / CSS3** — semantic structure, gradients and animations
- **Web Audio API** — high-precision timing, autocorrelation pitch
  detection, Goertzel per-octave analysis for the strobe tools
- **Vanilla JavaScript** — no dependencies, no build step
- **Structured data + crawl files** — JSON-LD, `robots.txt`, `sitemap.xml`

## Development

Everything is static — serve the repo root with any static file server:

```bash
git clone https://github.com/dataehora/beatconfused.git
cd beatconfused
python3 -m http.server 8000
# then open http://localhost:8000/
```

## Deployment

Served via GitHub Pages on the `beatconfused.com` domain (`CNAME`). Any
static host with HTTPS works — no server-side code.

## License

MIT License — feel free to use and modify.

## Contributing

Contributions are welcome. Please open a Pull Request.
