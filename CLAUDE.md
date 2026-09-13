# BeatConfused.com — project notes for Claude

Static site, no build step: plain HTML/CSS/vanilla JS with the Web Audio
API. Hosted on GitHub Pages (`CNAME` → beatconfused.com). Repo:
`dataehora/beatconfused`. See [README.md](README.md) for the user-facing
tool descriptions and repo layout — this file is developer/agent context
that doesn't belong there.

## Architecture

- `index.html` / `styles.css` — home page (tool cards, decorative SVG
  icons built by inline `<script>`, no shared code).
- `metronome/` — fully independent, no shared code, has its own opt-in
  cache-busting scheme (see Caching section below).
- `tuner/`, `strobetuner/` (Octave Strobe Tuner), `multistrobe/`
  (Chromatic Strobe Tuner) — the three "tuner-family" pages. Each has its
  own `index.html` / `script.js` / `styles.css`, but share:
  - `shared/tuner-common.js` + `shared/tuner-common.css` — Reference
    Pitch, Tuning Standard/temperament math, Spectrum Analyser, Input
    Monitor, **Test Tone** (`createTestTone`, `updateTestToneVariance`,
    `frequencyToNote`), the Octave Frequency Table
    (`buildOctaveFrequencyTable` / `updateOctaveFrequencyTableRings` /
    `resetOctaveFrequencyTable`), collapsible-panel wiring, transport
    shortcuts (Space/arrows).
  - `shared/strobe-disc.js` — the reusable strobe-disc engine used by both
    `/strobetuner/` (one large hero disc) and `/multistrobe/` (twelve
    small ones): `buildStageGeometry` (shared 180°/thin-bezel proportions,
    scale to any case radius), `ringRadiusForOctave` (fixed 9-slot radius
    math — every disc reserves radius space for octaves 0-8 regardless of
    which octaves a given note actually has, so the visual scale never
    changes between notes), `buildDisc`, `addBezelDecoration` (ticks,
    ♭/♯ glyphs, vignette, glass highlight), Goertzel ring analysis
    (`analyzeDisc`/`analyzeRing`), `renderDisc`.
  - A future look/behavior change to either shared file applies to all
    three pages automatically — that's the intended design, lean on it
    rather than re-forking page-local copies.
- `binfacevsfarage/` — standalone browser game, deliberately **not**
  linked from the studio nav, blocked in `robots.txt`, and absent from
  `sitemap.xml`. Leave it that way unless told otherwise.

### Section order convention (tuner-family pages)

All three pages follow the same order: Title → Toggle → Display →
"Input Monitor and Test Tone - Setting up your Microphone" (one merged
panel, collapsed by default) → Spectrum Analyser → "Tuning Standard and
Reference Pitch" (one merged panel) → Frequency Table. This is identical
on all three pages now — Test Tone lives inside the Input Monitor panel
everywhere, not as a separate block.

## ⚠️ Caching gotcha — read before editing shared files or any page script

GitHub Pages (behind Cloudflare) serves `.js`/`.css` with
`Cache-Control: public, max-age=14400, must-revalidate` (4 hours) and
**no version in the URL** by default. The HTML documents themselves are
`max-age=0, must-revalidate` (always revalidated), but each `<script>` /
`<link>` tag's own target is cached independently for up to 4 hours.

This caused two real, live production bugs in one session (see
[PR #52](https://github.com/dataehora/beatconfused/pull/52) and
[PR #53](https://github.com/dataehora/beatconfused/pull/53)): a browser
that had `shared/tuner-common.js` (or a page's own `script.js`) cached
from before a deploy kept using the stale copy — even on a "fresh" page
load — because the file's own cache window hadn't expired yet. A
function added in one file but called from a freshly-fetched sibling
file threw `TypeError: ... is not a function` (or silently resolved to
`undefined`), breaking the whole page's `<script>` from that line down.

**The fix in place**: every `<script src>` / `<link href>` for
`shared/tuner-common.js`, `shared/tuner-common.css`, `shared/strobe-disc.js`,
and each tuner page's own `script.js`/`styles.css` carries a
`?v=20260913` query string across `tuner/index.html`,
`strobetuner/index.html`, `multistrobe/index.html`.

**When you touch any of those files again**: bump the `?v=` value (a
`YYYYMMDD` string is fine) on *every* reference to that specific file,
across all pages that load it. Grep for the old value first:

```bash
grep -rn "v=20260913" --include="*.html" .
```

If you forget, the change will still work for brand-new visitors but can
silently break the page for anyone with a stale cached copy of just one
of the files, for up to 4 hours after deploy — exactly what happened
above. This is a manual, easy-to-forget step; a more permanent fix (a
build script that content-hashes filenames, or automating the version
bump) would remove the footgun entirely and is worth doing eventually.

Note `metronome/index.html` already has its own *different*,
**opt-in** versioning scheme (only kicks in if the page URL itself has a
`?__v=` param — see the `loadVersionedAssets` IIFE there). It predates
this session's fix and hasn't been touched or unified with it.

### Local dev server

`.claude/launch.json` runs `.claude/nocache_server.py` (not
`python -m http.server`) on port 5849 — a tiny wrapper that adds
`Cache-Control: no-store` to every response. Plain `http.server` sends no
caching headers at all, which let the *browser* heuristically cache
scripts for a surprisingly long time and made local edits appear not to
apply without a manual hard-refresh — this bit hard during development
this session. If local preview ever again seems to be running stale code
despite the file on disk being correct, suspect the browser's own cache
first (try a brand new tab, or bump the preview port) rather than the
code.

## Recent history (this session: PRs #47–#53, in order)

1. **#47** — reverted the home page's Tuner card icon back to needle-only
   (removed a since-unwanted strobe/meter thumbnail trio).
2. **#48** — redesigned the Chromatic Strobe Tuner home-icon as three
   overlapping "fan" dials (A, B♭, B); changed Octave Strobe's home-icon
   badge "A4" → "A"; **fixed a real pitch-detection bug**: `detectPitch`'s
   clarity score divided by a fixed full-buffer energy figure even though
   the numerator only summed `(size - lag)` samples, systematically
   penalizing low notes — a clean ~110 Hz tone could already fail the
   confidence threshold from lag length alone. Replaced with a proper
   per-lag-normalized autocorrelation (NSDF / McLeod Pitch Method) plus
   first-peak picking (to avoid octave-down misreads on clean tones' exact
   harmonic ties). This is shared logic duplicated in `tuner/script.js`
   and `strobetuner/script.js` — if you ever touch pitch detection, fix
   both (or, better, finally extract it to `shared/`).
3. **#49** — unified section order across all three tuner pages and
   replaced `/tuner/`'s and `/multistrobe/`'s old "one column per
   reference-pitch standard" Frequency Table with the octave-by-note grid
   `/strobetuner/` already had (now the one shared implementation, see
   Architecture above). Removed the per-table duplicate Standard/Key
   selector; added a live text line naming the standard/pitch currently
   shown.
4. **#50** — Octave Strobe Tuner: restored 180° arc (was drifted to 160°
   in earlier work), fixed the "display rescales when a different note
   plays" bug (ring radius now depends on a fixed 9-octave-slot layout,
   not on how many octaves *that specific note* happens to have — see
   `ringRadiusForOctave`), repositioned the octave legend to line up with
   true ring radii (fixed position, note-before-number). Moved the disc's
   full shared appearance/geometry into `shared/` and switched
   Chromatic Strobe's 12 discs to build from it too — they're now
   "adapted copies" of the Octave Strobe disc (180°, thin bezel, ticks,
   monochrome wedges) instead of a separate smaller/colored design.
5. **#51** — merged "Input Monitor" and "Test Tone" into one panel,
   collapsed by default, positioned right after the display on all three
   pages. **Ported Test Tone to `/strobetuner/` and `/multistrobe/`**
   (previously Tuner-only) via a new shared `T.createTestTone` — a real
   oscillator routed to both the speakers and the page's own analyser, so
   it exercises the same detection pipeline a microphone would.
   Octave Strobe bypasses autocorrelation for the *known* test frequency
   (matching Tuner's own approach) purely for note identification; its
   disc's Goertzel rings still analyze the real synthesized audio.
   Chromatic Strobe needs no bypass at all — no single "detected note"
   concept there, so the twelve discs just light up correctly on their
   own. Fixed a genuine bug along the way: a second `.panel-header`
   inside one collapsible block stayed visible while collapsed (the
   collapse-hide CSS rule exempts *every* `.panel-header`) — introduced
   `.panel-subheader` for non-collapsing sub-headings.
6. **#52, #53** — the caching fix described above, found and fixed during
   this session's own final live-site review.
7. **#55** — **fixed a real Goertzel spectral-leakage bug** reported by a
   user: playing a single pure test tone (e.g. A440) on `/multistrobe/`
   lit up several *neighboring semitones'* discs (G♯, A♯, B, G — not
   harmonics, which correctly stayed dark) at close to full strength, and
   the correct A disc's own reading looked jittery. Root cause: each
   ring's Goertzel window (`shared/strobe-disc.js`) was only
   `GOERTZEL_MIN_CYCLES = 6` cycles long with no window function applied —
   a rectangular window's main lobe at that length is ≈±17% of the target
   frequency, several times wider than the ~6% gap between adjacent
   semitones, so a clean tone landed well inside a neighbor's passband.
   Confirmed by simulation (not just the formula) before touching code —
   see the constant's own comment in `shared/strobe-disc.js` for the
   numbers. Fix: apply a Hann window inside `goertzel()` and raise
   `GOERTZEL_MIN_CYCLES` to 36 (verified to push adjacent-semitone leakage
   under ~0.3% almost everywhere on the keyboard); doubled
   `ANALYSER_BUFFER_SIZE` to 32768 (the Web Audio API's own max fftSize)
   so the longer window doesn't get clamped down again for the bottom
   octave; halved `MIN_RING_MAGNITUDE` to compensate for Hann's ~0.5
   coherent-gain factor so mic sensitivity is unchanged. Same fix, no
   separate work needed: `/strobetuner/`'s single hero disc uses the exact
   same shared engine. Also bumped the Test Tone **Fine Tuning** slider
   from 1¢ to 0.1¢ steps (`shared/tuner-common.js` + all three
   `index.html`s) per the same report, to match the Frequency Table's
   hundredths-of-a-Hz display precision.

## Testing notes / caveats

- This environment cannot grant real microphone permission, so "mic"
  functionality was verified structurally (no console errors, correct
  wiring) but never with real live audio input. **Test Tone** (a
  synthesized oscillator, no permission needed) *was* verified
  end-to-end on the live production site for all three pages, including
  confirming the correct disc/ring lights up with ~0¢ deviation.
- The local dev server caching issue (see above) means: if a future
  session's local testing shows unexplained stale behavior, try a brand
  new browser tab or bump the dev server's port before assuming the code
  is wrong.
- The #55 Goertzel leakage fix was verified two ways: a standalone Python
  simulation of the exact windowed-Goertzel math (sweeping every semitone
  offset 0-12 at several candidate cycle counts) before touching the code,
  then structurally on the local dev server — driving Test Tone at 440 Hz
  and reading each disc's `is-active`/`in-tune` classes via
  `javascript_tool` confirmed only the `A` disc lit up, where before the
  fix several neighbors would have too. Not yet re-confirmed on the live
  production site the way #51's Test Tone rollout was.
- A user report that Chromatic Strobe's Frequency Table appeared "empty"
  was investigated thoroughly and could not be reproduced anywhere
  (local dev, then the live site) — the table was correctly populated in
  every check. Almost certainly a stale-cache symptom on the reporter's
  end (see the caching section above — this was *before* the #52/#53
  fixes existed, so it's very plausible). Worth a quick re-check if it's
  ever reported again, but treat it as resolved by the caching fix unless
  a concrete repro shows up.

## Possible follow-ups (not done, not blocking)

- Pitch detection (`detectPitch`) is still duplicated between
  `tuner/script.js` and `strobetuner/script.js`. Low urgency, but if it's
  touched again, consider finally moving it into `shared/`.
- `shared/strobe-disc.js`'s `DEFAULT_GEOMETRY` is now effectively dead —
  both real callers (`tuner-family` pages) always pass explicit geometry
  via `buildStageGeometry`. Harmless to leave, fine to remove if it's
  ever confusing.
- `metronome/`'s opt-in `?__v=` cache-busting scheme predates and is
  inconsistent with the static `?v=` scheme now used on the tuner pages.
  Worth unifying if metronome's own assets ever need a forced-refresh fix
  like #52/#53.
- No automated tests exist anywhere in this repo; all verification is
  manual/in-browser. If a testing setup is ever wanted, there isn't one
  to extend — it'd be new infrastructure.
- Even after #55's fix, the bottom octave (A0/A♯0/B0, and to a lesser
  extent A1-ish) still gets less semitone selectivity than the rest of
  the keyboard, because their rings' desired 36-cycle window would exceed
  `ANALYSER_BUFFER_SIZE` (32768, already the Web Audio API's max fftSize)
  and gets clamped shorter. Not reported as a problem by any user yet —
  flagging it here since it's an inherent, understood limitation rather
  than an oversight, in case very-low-note leakage is ever reported.

## Workflow conventions observed this session

- User wants autonomous commit → PR → merge after finishing a unit of
  work, without asking first (confirmed repeatedly).
- Commits/PRs end with the Claude Code attribution lines currently in use
  (see any recent commit/PR for the exact wording — it's supplied
  per-session and may change).
- Prefer small, reviewable PRs over one giant one; this session shipped 7
  separate PRs (#47–#53) rather than one mega-PR, and that was well
  received implicitly (no pushback).
