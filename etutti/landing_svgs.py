"""Top-view drawings of the eTutti family for the landing pages.

Stdlib only:  python etutti/landing_svgs.py

Rewrites the inline <svg> between the markers
    <!-- BEGIN svg:<model> -->  ...  <!-- END svg:<model> -->
(and the size text between <!-- BEGIN size:<model> --> / <!-- END size:<model> -->)
in etutti/index.html (the family landing page) and etutti/pocket/index.html.

Sources, read only (other agents own them):
  - etutti/hardware/pocket/build/pocket.json   the Pocket: keys, opening,
    case outline and interface positions (design's contract);
  - etutti/hardware/pocket/layout.py           keys_for()/outlines(): the
    same C-griff grid and convex-hull outline method, which reproduces the
    eTuttino case's 331 mm, used here for the eTuttino (44 keys), the
    eTutti (48 keys, one more per row: F#6 / G6 / F6 / D#6) and the
    eTuttiChorus (the eTutti plus the 1.9" screen);
  - interface positions of the eTuttino family (screen zone, volume,
    selector, LED, grille) copied from etutti/hardware/case/case.py.

The outlines are previews (convex hull of the key clearances), not the
exact case: the drawings say "approximate" where they show a size.
Colours come from CSS classes (etutti/family.css), not from the SVG.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
POCKET_DIR = os.path.join(HERE, "hardware", "pocket")
sys.dont_write_bytecode = True  # leave no __pycache__ in the design folder
sys.path.insert(0, POCKET_DIR)
import layout  # noqa: E402  (etutti/hardware/pocket/layout.py, stdlib only)

PAGES = [os.path.join(HERE, "index.html"), os.path.join(HERE, "pocket", "index.html")]

# eTuttino family interface, from etutti/hardware/case/case.py (SPEC v7-v9)
FAMILY_IF = {
    "volume": (20.0, 45.0), "select": (37.0, 45.0), "led": (52.0, 45.0),
    "grille": (8.0, 61.0, 53.0, 94.0), "screen": (8.0, 5.0, 62.0, 35.0),
}
KNOB_R, LED_R = 4.5, 1.75


def pocket():
    with open(os.path.join(POCKET_DIR, "build", "pocket.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    c = d["controls"]
    return {
        "keys": d["keys"], "opening": d["opening"], "box": d["box"],
        "length": d["length"], "volume": c["volume"], "select": c["select"],
        "led": c["led"], "grille": c["grille"], "screen": None,
    }


def family(top, screen=False):
    keys = layout.keys_for(top, layout.O_ETUTTINO)
    opening, box = layout.outlines(keys)
    m = dict(FAMILY_IF)
    if not screen:
        m["screen"] = None
    m.update(keys=keys, opening=opening, box=box, length=max(x for x, _ in box))
    return m


ETUTTINO_TOP = {1: "D#6", 2: "E6", 3: "D6", 4: "C6"}
ETUTTI_TOP = {1: "F#6", 2: "G6", 3: "F6", 4: "D#6"}


def models():
    out = {
        "pocket": pocket(),
        "etuttino": family(ETUTTINO_TOP),
        "etutti": family(ETUTTI_TOP),
        "chorus": family(ETUTTI_TOP, screen=True),
    }
    counts = {k: len(v["keys"]) for k, v in out.items()}
    assert counts == {"pocket": 28, "etuttino": 44, "etutti": 48, "chorus": 48}, counts
    return out


def svg(m, frame_w=None, labels=False):
    """frame_w: shared viewBox width so every card is drawn to one scale."""
    pad = 3.0
    w = m["length"] + 2 * pad
    fw = max(w, frame_w or 0)
    dx = (fw - w) / 2 + pad
    dy = pad
    h = layout.WIDTH + 2 * pad
    f = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")
    pts = lambda poly: " ".join(f"{f(x + dx)},{f(y + dy)}" for x, y in poly)
    s = [f'<svg class="family-svg" viewBox="0 0 {f(fw)} {f(h)}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">',
         f'<polygon class="fs-body" points="{pts(m["box"])}"/>',
         f'<polygon class="fs-well" points="{pts(m["opening"])}"/>']
    x0, y0, x1, y1 = m["grille"]
    s.append(f'<rect class="fs-grille" x="{f(x0 + dx)}" y="{f(y0 + dy)}" width="{f(x1 - x0)}" height="{f(y1 - y0)}" rx="3"/>')
    if m["screen"]:
        x0, y0, x1, y1 = m["screen"]
        s.append(f'<rect class="fs-screen" x="{f(x0 + dx)}" y="{f(y0 + dy)}" width="{f(x1 - x0)}" height="{f(y1 - y0)}" rx="3"/>')
    for key in ("volume", "select"):
        x, y = m[key]
        s.append(f'<circle class="fs-knob" cx="{f(x + dx)}" cy="{f(y + dy)}" r="{f(KNOB_R)}"/>')
    x, y = m["led"]
    s.append(f'<circle class="fs-led" cx="{f(x + dx)}" cy="{f(y + dy)}" r="{f(LED_R)}"/>')
    for k in m["keys"]:
        cls = "fs-key fs-sharp" if k["sharp"] else "fs-key"
        s.append(f'<circle class="{cls}" cx="{f(k["x"] + dx)}" cy="{f(k["y"] + dy)}" r="{f(layout.D_BTN / 2)}"/>')
        if labels:
            tcls = "fs-note fs-note-sharp" if k["sharp"] else "fs-note"
            s.append(f'<text class="{tcls}" x="{f(k["x"] + dx)}" y="{f(k["y"] + dy + 1.3)}">{k["note"]}</text>')
    s.append("</svg>")
    return "\n".join(s)


def replace(text, tag, body):
    pat = re.compile(r"(<!-- BEGIN %s -->)(.*?)(<!-- END %s -->)" % (re.escape(tag), re.escape(tag)), re.S)
    new, n = pat.subn(lambda mm: mm.group(1) + body + mm.group(3), text)
    return new, n


def main():
    ms = models()
    frame = max(m["length"] for m in ms.values()) + 6.0
    for page in PAGES:
        with open(page, encoding="utf-8") as fh:
            text = fh.read()
        total = 0
        for name, m in ms.items():
            text, n = replace(text, f"svg:{name}", "\n" + svg(m, frame) + "\n")
            total += n
            text, n = replace(text, f"svg:{name}-large", "\n" + svg(m, labels=True) + "\n")
            total += n
            size = f"≈ {m['length']:.0f} × {layout.WIDTH:.0f} mm"
            text, n = replace(text, f"size:{name}", size)
            total += n
        with open(page, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"{os.path.relpath(page, HERE)}: {total} block(s) rewritten")
    for name, m in ms.items():
        print(f"  {name}: {len(m['keys'])} keys, ~{m['length']:.1f} x {layout.WIDTH:.0f} mm")


if __name__ == "__main__":
    main()
