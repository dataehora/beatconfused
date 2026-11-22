"""Builds etutti/firmware/student_v4/oled_font.h: the 5 x 10 font of the Student V4's OLED (SPEC R6V4 item 7).

Why a font of our own: the old 5 x 7 table had capitals, digits and a few signs only. The menu now speaks
Portuguese and English in lower case with accents, and the table is meant to grow to other languages.

Cell: 5 columns x 10 rows (bit r of a column byte = row r, row 0 at the top).
  rows 0-1   accents of the capitals (and of the capitals only)
  rows 2-8   capitals, digits, ascenders (b d f h k l t), the dot of i/j; baseline = row 8
  rows 4-8   x-height of the lower case (5 rows); accents of the lower case sit on rows 1-2
  row 9      the single descender row (g j p q y) and the cedilla
Everything is built from ASCII art below, so a new letter is a few lines. Run with any python 3 (stdlib only):
    python make_font.py            writes ../../student_v4/oled_font.h
    python make_font.py --png X    also writes a preview sheet to X (needs Pillow)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "student_v4", "oled_font.h")

# The classic 5 x 7 table (ASCII 32..90), columns with bit 0 at the top; the old FONT5X7 of the sketch.
OLD = [
    (0x00, 0x00, 0x00, 0x00, 0x00), (0x00, 0x00, 0x5F, 0x00, 0x00), (0x00, 0x07, 0x00, 0x07, 0x00), (0x14, 0x7F, 0x14, 0x7F, 0x14),
    (0x24, 0x2A, 0x7F, 0x2A, 0x12), (0x23, 0x13, 0x08, 0x64, 0x62), (0x36, 0x49, 0x55, 0x22, 0x50), (0x00, 0x05, 0x03, 0x00, 0x00),
    (0x00, 0x1C, 0x22, 0x41, 0x00), (0x00, 0x41, 0x22, 0x1C, 0x00), (0x14, 0x08, 0x3E, 0x08, 0x14), (0x08, 0x08, 0x3E, 0x08, 0x08),
    (0x00, 0x50, 0x30, 0x00, 0x00), (0x08, 0x08, 0x08, 0x08, 0x08), (0x00, 0x60, 0x60, 0x00, 0x00), (0x20, 0x10, 0x08, 0x04, 0x02),
    (0x3E, 0x51, 0x49, 0x45, 0x3E), (0x00, 0x42, 0x7F, 0x40, 0x00), (0x42, 0x61, 0x51, 0x49, 0x46), (0x21, 0x41, 0x45, 0x4B, 0x31),
    (0x18, 0x14, 0x12, 0x7F, 0x10), (0x27, 0x45, 0x45, 0x45, 0x39), (0x3C, 0x4A, 0x49, 0x49, 0x30), (0x01, 0x71, 0x09, 0x05, 0x03),
    (0x36, 0x49, 0x49, 0x49, 0x36), (0x06, 0x49, 0x49, 0x29, 0x1E), (0x00, 0x36, 0x36, 0x00, 0x00), (0x00, 0x56, 0x36, 0x00, 0x00),
    (0x08, 0x14, 0x22, 0x41, 0x00), (0x14, 0x14, 0x14, 0x14, 0x14), (0x00, 0x41, 0x22, 0x14, 0x08), (0x02, 0x01, 0x51, 0x09, 0x06),
    (0x32, 0x49, 0x79, 0x41, 0x3E), (0x7E, 0x11, 0x11, 0x11, 0x7E), (0x7F, 0x49, 0x49, 0x49, 0x36), (0x3E, 0x41, 0x41, 0x41, 0x22),
    (0x7F, 0x41, 0x41, 0x22, 0x1C), (0x7F, 0x49, 0x49, 0x49, 0x41), (0x7F, 0x09, 0x09, 0x09, 0x01), (0x3E, 0x41, 0x49, 0x49, 0x7A),
    (0x7F, 0x08, 0x08, 0x08, 0x7F), (0x00, 0x41, 0x7F, 0x41, 0x00), (0x20, 0x40, 0x41, 0x3F, 0x01), (0x7F, 0x08, 0x14, 0x22, 0x41),
    (0x7F, 0x40, 0x40, 0x40, 0x40), (0x7F, 0x02, 0x0C, 0x02, 0x7F), (0x7F, 0x04, 0x08, 0x10, 0x7F), (0x3E, 0x41, 0x41, 0x41, 0x3E),
    (0x7F, 0x09, 0x09, 0x09, 0x06), (0x3E, 0x41, 0x51, 0x21, 0x5E), (0x7F, 0x09, 0x19, 0x29, 0x46), (0x46, 0x49, 0x49, 0x49, 0x31),
    (0x01, 0x01, 0x7F, 0x01, 0x01), (0x3F, 0x40, 0x40, 0x40, 0x3F), (0x1F, 0x20, 0x40, 0x20, 0x1F), (0x3F, 0x40, 0x38, 0x40, 0x3F),
    (0x63, 0x14, 0x08, 0x14, 0x63), (0x07, 0x08, 0x70, 0x08, 0x07), (0x61, 0x51, 0x49, 0x45, 0x43),
]

# Lower case: rows 2..9 (8 strings of 5 characters). '#' = lit.
LOWER = {
    "a": [".....", ".....", ".###.", "....#", ".####", "#...#", ".####", "....."],
    "b": ["#....", "#....", "####.", "#...#", "#...#", "#...#", "####.", "....."],
    "c": [".....", ".....", ".###.", "#...#", "#....", "#...#", ".###.", "....."],
    "d": ["....#", "....#", ".####", "#...#", "#...#", "#...#", ".####", "....."],
    "e": [".....", ".....", ".###.", "#...#", "#####", "#....", ".###.", "....."],
    "f": ["..##.", ".#...", "####.", ".#...", ".#...", ".#...", ".#...", "....."],
    "g": [".....", ".....", ".###.", "#...#", "#...#", ".####", "....#", ".###."],
    "h": ["#....", "#....", "#.##.", "##..#", "#...#", "#...#", "#...#", "....."],
    "i": ["..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###.", "....."],
    "j": ["...#.", ".....", "..##.", "...#.", "...#.", "...#.", "...#.", "##..."],
    "k": ["#....", "#....", "#...#", "#..#.", "###..", "#..#.", "#...#", "....."],
    "l": [".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###.", "....."],
    "m": [".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#", "....."],
    "n": [".....", ".....", "#.##.", "##..#", "#...#", "#...#", "#...#", "....."],
    "o": [".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###.", "....."],
    "p": [".....", ".....", "####.", "#...#", "#...#", "####.", "#....", "#...."],
    "q": [".....", ".....", ".####", "#...#", "#...#", ".####", "....#", "....#"],
    "r": [".....", ".....", "#.##.", "##..#", "#....", "#....", "#....", "....."],
    "s": [".....", ".....", ".####", "#....", ".###.", "....#", "####.", "....."],
    "t": [".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##.", "....."],
    "u": [".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#", "....."],
    "v": [".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#..", "....."],
    "w": [".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#.", "....."],
    "x": [".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "....."],
    "y": [".....", ".....", "#...#", "#...#", "#...#", ".####", "....#", ".###."],
    "z": [".....", ".....", "#####", "...#.", "..#..", ".#...", "#####", "....."],
}
DOTLESS_I = [".....", ".....", ".##..", "..#..", "..#..", "..#..", ".###.", "....."]

# A few more signs (rows 2..9)
SIGNS = {
    "[": ["###..", "#....", "#....", "#....", "#....", "#....", "###..", "....."],
    "]": ["..###", "....#", "....#", "....#", "....#", "....#", "..###", "....."],
    "_": [".....", ".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    "|": ["..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "¡": ["..#..", ".....", "..#..", "..#..", "..#..", "..#..", "..#..", "....."],      # inverted !
    "¿": ["..#..", ".....", "..#..", "..#..", ".#...", "#...#", ".###.", "....."],      # inverted ?
}

# Accents: two rows (upper, lower); placed on rows 0-1 over capitals and on rows 1-2 over lower case.
ACCENT = {
    "acute": ["...#.", "..#.."],
    "grave": [".#...", "..#.."],
    "circ": ["..#..", ".#.#."],
    "tilde": [".##.#", "#..#."],
    "diae": [".....", ".#.#."],
}


def col_bits(rows_by_index):
    """rows_by_index: {row: 5-char string} -> 5 column ints (bit r = row r)."""
    cols = [0] * 5
    for r, s in rows_by_index.items():
        for c, ch in enumerate(s):
            if ch == "#":
                cols[c] |= 1 << r
    return cols


def from_art(art, first_row=2):
    return col_bits({first_row + i: s for i, s in enumerate(art)})


def from_old(old, shift=2):
    return [b << shift for b in old]


def add(cols, rows_by_index):
    out = list(cols)
    for c, v in enumerate(col_bits(rows_by_index)):
        out[c] |= v
    return out


def accent_on(cols, name, upper):
    r0 = 0 if upper else 1
    a = ACCENT[name]
    return add(cols, {r0: a[0], r0 + 1: a[1]})


def cedilla(cols):
    return add(cols, {9: "..#.."})


def build():
    ascii_cols = {}
    for i, old in enumerate(OLD):                      # 32..90
        ascii_cols[32 + i] = from_old(old)
    for ch, art in LOWER.items():
        ascii_cols[ord(ch)] = from_art(art)
    for ch, art in SIGNS.items():
        if ord(ch) < 128:
            ascii_cols[ord(ch)] = from_art(art)
    qmark = ascii_cols[ord("?")]
    for cp in range(32, 127):
        ascii_cols.setdefault(cp, list(qmark))

    ext = {}
    for ch, art in SIGNS.items():
        if ord(ch) >= 128:
            ext[ord(ch)] = from_art(art)
    vowel_accents = {
        "a": ["à", "á", "â", "ã", "ä"], "e": ["è", "é", "ê", None, "ë"],
        "i": ["ì", "í", "î", None, "ï"], "o": ["ò", "ó", "ô", "õ", "ö"],
        "u": ["ù", "ú", "û", None, "ü"],
    }
    names = ["grave", "acute", "circ", "tilde", "diae"]
    for v, lst in vowel_accents.items():
        base_low = from_art(DOTLESS_I) if v == "i" else ascii_cols[ord(v)]
        base_up = ascii_cols[ord(v.upper())]
        for ch, name in zip(lst, names):
            if ch is None:
                continue
            ext[ord(ch)] = accent_on(base_low, name, upper=False)
            ext[ord(ch.upper())] = accent_on(base_up, name, upper=True)
    ext[0xE7] = cedilla(ascii_cols[ord("c")])
    ext[0xC7] = cedilla(ascii_cols[ord("C")])
    ext[0xF1] = accent_on(ascii_cols[ord("n")], "tilde", upper=False)
    ext[0xD1] = accent_on(ascii_cols[ord("N")], "tilde", upper=True)
    return ascii_cols, ext


def main():
    ascii_cols, ext = build()
    lines = []
    lines.append("// GENERATED by etutti/firmware/tools/oled_font/make_font.py: do not edit by hand.")
    lines.append("// 5 x 10 font of the Student V4 OLED (SPEC R6V4 item 7): ASCII 32..126 and Latin-1 letters with accents.")
    lines.append("// One uint16_t per column, bit r = row r (row 0 at the top); see the generator for the cell layout.")
    lines.append("#pragma once")
    lines.append("#include <stdint.h>")
    lines.append("")
    lines.append("const uint16_t OLED_FONT_ASCII[95][5] = {          // 32 (space) .. 126")
    for cp in range(32, 127):
        c = ascii_cols[cp]
        shown = chr(cp) if chr(cp) not in "\\" else "backslash"
        lines.append("  {0x%04X,0x%04X,0x%04X,0x%04X,0x%04X},   // %s" % (c[0], c[1], c[2], c[3], c[4], shown))
    lines.append("};")
    lines.append("")
    lines.append("struct OledGlyph { uint16_t cp; uint16_t col[5]; };   // cp = Unicode code point, sorted")
    lines.append("const OledGlyph OLED_FONT_EXT[] = {")
    for cp in sorted(ext):
        c = ext[cp]
        lines.append("  {0x%04X,{0x%04X,0x%04X,0x%04X,0x%04X,0x%04X}},   // %s" % (cp, c[0], c[1], c[2], c[3], c[4], chr(cp)))
    lines.append("};")
    lines.append("const int OLED_FONT_EXT_COUNT = %d;" % len(ext))
    lines.append("")
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print("wrote", os.path.normpath(OUT), "ascii 95 glyphs + ext", len(ext), "= ~%d bytes" % ((95 * 10) + len(ext) * 12))
    if "--png" in sys.argv:
        path = sys.argv[sys.argv.index("--png") + 1]
        preview(ascii_cols, ext, path)


def preview(ascii_cols, ext, path):
    from PIL import Image
    allg = [(cp, ascii_cols[cp]) for cp in range(32, 127)] + sorted(ext.items())
    per_row = 24
    scale = 4
    rows = (len(allg) + per_row - 1) // per_row
    img = Image.new("RGB", (per_row * 7 * scale + 8, rows * 12 * scale + 8), (0, 0, 0))
    px = img.load()
    for n, (cp, cols) in enumerate(allg):
        gx = 4 + (n % per_row) * 7 * scale
        gy = 4 + (n // per_row) * 12 * scale
        for c in range(5):
            for r in range(10):
                if cols[c] >> r & 1:
                    for dy in range(scale):
                        for dx in range(scale):
                            px[gx + c * scale + dx, gy + r * scale + dy] = (255, 255, 255)
    img.save(path)


if __name__ == "__main__":
    main()
