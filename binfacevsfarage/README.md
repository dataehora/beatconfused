# Clacton Fighter II

A Street-Fighter-II-style browser brawler. Pure static HTML/CSS/JS — no
build step, no server required. Works on desktop browsers, and on phones
/ iPads via an on-screen touch pad.

## Running it

Just open `index.html` in a browser. For best results (so image loading
isn't blocked by browser file:// restrictions), serve the folder locally:

```
cd sf2-clacton
python3 -m http.server 8000
```

then visit `http://localhost:8000`.

## Title screen & theme

The title screen now uses your `Assets/ClactonFighter.png` logo artwork
directly (if it's ever missing, a plain text title is used automatically
instead). The whole UI palette and fonts were reworked to match it — warm
red/orange/gold accents, a sky-blue menu backdrop, and a bold display font
(Bangers, loaded from Google Fonts with safe local fallbacks if the page
is ever opened offline) for headings and buttons. The stage/fighter
selection cards are also considerably larger now.

## Adding your own artwork

Each fighter is now a full **pose set**, not a single static image. Drop
files into `Assets/` using this naming convention — `<FighterKey>_<pose>.png`:

| File                          | Used for                                             |
|--------------------------------|-------------------------------------------------------|
| `Assets/ClactonFighter.png`     | Title screen logo                                     |
| `Assets/Pier.png`               | Stage background — The Pier                          |
| `Assets/MagicCity.png`          | Stage background — Magic City                         |
| `Assets/ClactonFutureBinface.png` | Result-screen backdrop/photo for a Binface win      |
| `Assets/ClactonFutureFarrage.png` | Result-screen backdrop/photo for a Farrage win      |
| `Assets/<Key>_idle1.png`        | Standing pose, frame 1 (idle breathing loop)          |
| `Assets/<Key>_idle2.png`        | Standing pose, frame 2 — knees slightly bent          |
| `Assets/<Key>_run.png`         | Movement pose, shown while walking left/right          |
| `Assets/<Key>_jump.png`        | Airborne pose                                          |
| `Assets/<Key>_throw.png`       | Throwing pose (during the throw-cooldown window)       |
| `Assets/<Key>_hit.png`         | Reaction pose when struck (also used for K.O.)         |
| `Assets/<Key>_win.png`         | Victory pose, shown as a freeze-frame when a round ends |
| `Assets/<Key>_projectile.png`  | The thrown object sprite                                |

`<Key>` is `Binface` or `Farrage`. **Both fighters now have a full pose
set**, extracted and cleaned up from the reference sheets supplied for
each — backgrounds removed, poses cropped, and both characters scaled
to match each other's height so neither fighter looks bigger or
smaller than the other in-game. Any pose file that's missing for a
fighter falls back automatically to a simple stylised placeholder
silhouette, so the game still runs fine even with an incomplete set.

Farrage's thrown object is now a spinning, weathered bitcoin coin
(cropped from a supplied reference image) rather than a bag — it's 30%
larger than Binface's rubbish bag and spins continuously in flight.

Recommended: transparent-background PNGs, portrait orientation,
roughly 300–400px wide — they're scaled to fit a 130×210 in-game box
while preserving their own aspect ratio and staying anchored to the
ground.

## Sound

The game is Assets-first for audio too: drop any of these filenames into
`Assets/` (as `.mp3`, `.ogg`, or `.wav`) and the game uses your file
instead of the built-in synthesised chiptune sound:

| File (any extension)     | Used for                                  |
|----------------------------|--------------------------------------------|
| `Assets/music`              | Looping battle theme                       |
| `Assets/sfx_throw`          | Throwing the bag / money bags              |
| `Assets/sfx_hit`            | Getting struck by a projectile             |
| `Assets/sfx_jump`           | Jumping                                    |
| `Assets/sfx_countdown`      | Each "3, 2, 1" countdown beep              |
| `Assets/sfx_fight`          | The "FIGHT!" call-out                      |
| `Assets/sfx_ko`             | Knockout                                   |
| `Assets/sfx_win`            | Victory jingle on the result screen        |

Any sound you don't supply just falls back automatically to its
synthesised 8-bit equivalent — the default battle theme is a driving
172bpm minor-key riff with a simple kick/hi-hat pattern layered under
it, and a slightly detuned dual-oscillator lead for a fuller arcade-synth
tone, built entirely with the Web Audio API (no files required to hear
music at all). Hits and knockouts now layer a low thump with a
band-passed noise crunch for a meatier "punch" impact, and throws add a
filtered noise whoosh, aiming for a punchier, more classic-arcade-fighter
feel without reproducing any copyrighted samples.

## Health bar

The HUD health bars are now closer to the genre-standard fighting-game
look: a beveled black-and-white frame, a segmented/ticked yellow-to-orange
fill, and — importantly — each bar depletes *toward the center* of the
screen (P1's bar empties from right to left, P2's from left to right),
matching the classic layout. A bar flashes red once that fighter drops to
25% health or below.

## Gameplay notes

- **Fighters always face each other.** Movement (left/right) is purely
  positional — which way a character is drawn facing is always
  determined by where the opponent currently is, just like the
  classic SF2 rule. There's no "turning your back and running away."
- **Jumping lets you cross over your opponent.** The ground collision
  that normally keeps the two fighters from overlapping is switched
  off while either fighter is airborne, so a well-timed jump carries
  you clean over their head and swaps which side of the arena you're
  each on — exactly like the side-switch jump in the original games.
- **Thrown objects fly at waist height** when thrown from the ground —
  low enough to jump clean over with good timing, but not trivial.
  **Thrown while jumping, they sail high** instead — well above a
  standing opponent's head, so a jump-throw won't hit someone still on
  the ground (it can still connect with another airborne fighter).
  Throw speed has been reduced twice now (30%, then a further 15% on
  top of that) to widen the dodge window. Farrage's bag is 30% bigger
  than Binface's.
- **Opposing thrown objects collide.** If a rubbish bag and a bag of
  slime-money meet in mid-air, they destroy each other in a small burst
  — no damage to either fighter — instead of one continuing through to
  hit its target.
- **A fixable facing switch.** Getting a hand-drawn sprite's default
  left/right orientation right from a flat sheet is genuinely fiddly —
  if a character ever looks like they're facing the wrong way in a
  future art update, there's a one-line override at the top of
  `game.js` (`FACING_OVERRIDE`) that mirrors every pose for that
  character without needing to re-edit any image files.

## The result screen

- The winner holds their victory pose for a few seconds (extended from
  the original quick cut) before the match summary appears.
- The result screen is a newspaper-style front page: a large hero
  portrait of the winner (2.5x the previous size) fills the right side
  in their victory pose, while the left side shows a mocked-up
  newspaper front page — headline, photo, and a short story about
  Clacton's future — that matches the outcome:
  - **Binface wins:** "BINFACE TRIUMPHANT!" — a green, wind-farm-powered
    future for the pier. Backdrop and newspaper photo both use
    `Assets/ClactonFutureBinface.png`.
  - **Farrage wins:** "FARAGE VICTORIOUS!" — the pier sold off, a
    smoke-choked coastline ahead. Backdrop and newspaper photo both use
    `Assets/ClactonFutureFarrage.png`.
  If either photo is missing, a simple hand-drawn illustration in the
  same spirit is used for the backdrop automatically, and the
  newspaper simply runs without a photo — nothing breaks.
- A classic arcade-style **"CONTINUE?" countdown from 9 to 0** gives
  you time to pick Rematch or Main Menu; if it hits 0 with no choice
  made, it automatically returns to the main menu (just like the coin-op
  originals).

## Known rough edge

Determining a hand-drawn character's "default" left/right facing purely
from a flat reference sheet (no metadata, just pixels) is inherently
error-prone — several rounds of this project involved re-checking and
re-flipping specific poses. If Binface (or Farrage) still ever looks
backwards for a specific pose after this update, the fastest fix is the
`FACING_OVERRIDE` switch mentioned above, or just say which pose looks
wrong and it can be corrected directly.

## Controls

**Desktop:** Arrow Left / Right to move, Arrow Up to jump, Space to
throw your projectile (rubbish bag / green slime).

**Mobile/tablet:** an on-screen D-pad and THROW button appear
automatically (detected via touch capability).

## Game structure

- `index.html` — screens: menu (map + fighter select) → game → result
- `style.css` — retro arcade look, CRT scanline overlay, responsive layout, mobile HUD
- `game.js` — state machine (countdown → FIGHT → round), physics, simple
  AI opponent, projectile collision, health bars, timer, and an 8-bit
  music/SFX engine built entirely with the Web Audio API (no audio
  files needed)

## Notes on the AI opponent

The CPU fighter uses a lightweight finite-state approach: it closes
distance when far away, backs off or throws when at close/mid range,
and occasionally jumps — re-rolling its decision a few times per
second so it feels responsive rather than scripted.
