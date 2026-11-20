#!/usr/bin/env python3
"""world-in-one-day-20-nov -- make.fun news-image-20261120 entry.

Draws one 1024x1024 PNG that sums up the world's news of Friday
20 November 2026: a masthead, one hero story, four story cards and a
ticker strip. Pure Python 3.13 standard library, no network, no files
read, no randomness, no clock: every run writes byte-identical output.

Stories (each verified against a reputable source before drawing):
  1. Trump pushes the Iran decision to 2027 -- "no rush" on new strikes.
  2. Cyclone Akvan makes landfall on India's east coast today.
  3. The ICJ rules Myanmar committed genocide against the Rohingya.
  4. European leaders in Berlin say they are ready for talks with Russia.
  5. Anthropic's ANT closes its Nasdaq debut up 17% at $97.17.
Ticker: GTA VI passes $1.84bn; Japan's Hayabusa2 drops its asteroid landing.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   -> out/entry.png
"""

import binascii
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
INK = (15, 27, 45)        # deep navy page background
INK_SOFT = (27, 42, 68)   # ticker strip
AMBER = (245, 184, 29)    # masthead gold
PAPER = (255, 255, 255)   # card background
PAPER_DIM = (238, 240, 243)
DARK = (17, 24, 39)       # main text
MUTED = (88, 98, 112)     # secondary text
HAIR = (203, 209, 217)    # hairline rules
RED = (166, 28, 46)
TEAL = (14, 124, 123)
BLUE = (43, 94, 167)
GREEN = (30, 122, 52)
GOLD_DARK = (146, 104, 8)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
# Written from scratch for this poster (uppercase, digits, punctuation).
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "$": ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    "~": (".....", ".....", ".##.#", "#.#.#", ".....", ".....", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "·": (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
}


def glyph_rows(ch):
    """Rows for a character; unknown characters become a blank cell."""
    return GLYPHS.get(ch, GLYPHS[" "])


def text_width(text, scale):
    """Pixel width of text at a scale (glyph cell is 6*scale wide)."""
    return len(text) * 6 * scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    for raw in text.split("\n"):
        words = raw.split(" ")
        line = ""
        for word in words:
            trial = word if not line else line + " " + word
            if text_width(trial, scale) <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


# ------------------------------------------------------------------ canvas
class Canvas:
    """A plain RGB framebuffer with small drawing primitives."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def fill(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = r
                self.buf[i + 1] = g
                self.buf[i + 2] = b

    def vgrad(self, x, y, w, h, top, bottom):
        """Vertical gradient from top colour to bottom colour."""
        for yy in range(h):
            t = yy / max(1, h - 1)
            c = tuple(round(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
            self.fill(x, y + yy, w, 1, c)

    def hline(self, x, y, w, color):
        self.fill(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill(x, y, 1, h, color)

    def rect(self, x, y, w, h, color, thick=1):
        self.fill(x, y, w, thick, color)
        self.fill(x, y + h - thick, w, thick, color)
        self.fill(x, y, thick, h, color)
        self.fill(x + w - thick, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line, inclusive of both ends."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.px(x, y, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color, filled=False):
        """Midpoint circle; filled draws horizontal spans."""
        if r <= 0:
            return
        if filled:
            for yy in range(-r, r + 1):
                half = int((r * r - yy * yy) ** 0.5)
                self.fill(cx - half, cy + yy, half * 2 + 1, 1, color)
            return
        x = 0
        y = r
        d = 1 - r
        while x <= y:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                self.px(cx + sx, cy + sy, color)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

    def ellipse(self, cx, cy, rx, ry, color, filled=False):
        """Axis-aligned ellipse by scanline (filled) or outline."""
        if rx <= 0 or ry <= 0:
            return
        if filled:
            for yy in range(-ry, ry + 1):
                t = 1.0 - (yy * yy) / float(ry * ry)
                half = int(rx * (t ** 0.5))
                self.fill(cx - half, cy + yy, half * 2 + 1, 1, color)
            return
        steps = max(rx, ry) * 8
        for i in range(steps):
            import math
            a = 2.0 * math.pi * i / steps
            self.px(cx + int(rx * math.cos(a)), cy + int(ry * math.sin(a)), color)

    def poly(self, points, color):
        """Filled polygon by scanline (points: list of (x, y))."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    t = (yy - y0) / float(y1 - y0)
                    xs.append(int(x0 + t * (x1 - x0)))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill(xs[j], yy, xs[j + 1] - xs[j] + 1, 1, color)

    # ------------------------------------------------------------ text
    def text(self, x, y, s, scale, color):
        """Draw text left-aligned at (x, y); returns width drawn."""
        cx = x
        for ch in s:
            rows = glyph_rows(ch)
            for ry in range(7):
                row = rows[ry]
                for rx in range(5):
                    if row[rx] == "#":
                        self.fill(cx + rx * scale, y + ry * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx - x

    def text_center(self, x, y, w, s, scale, color):
        tw = text_width(s, scale)
        self.text(x + (w - tw) // 2, y, s, scale, color)

    def para(self, x, y, s, scale, color, max_width, leading=None):
        """Draw a wrapped paragraph; returns the y below the last line."""
        if leading is None:
            leading = 7 * scale + 5
        for line in wrap_text(s, scale, max_width):
            self.text(x, y, line, scale, color)
            y += leading
        return y


# ---------------------------------------------------------------- PNG out
def _png_chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    """Encode the canvas as a PNG (filter 0, zlib level 9) and write it."""
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _png_chunk(b"IHDR", ihdr)
    png += _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# -------------------------------------------------------------- pictograms
def rrect(cv, x, y, w, h, r, color):
    """Filled rounded rectangle (corner radius r)."""
    cv.fill(x + r, y, w - 2 * r, h, color)
    cv.fill(x, y + r, w, h - 2 * r, color)
    for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r),
                   (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
        cv.circle(cx, cy, r, color, filled=True)


def draw_calendar(cv, x, y, w, h, accent):
    """A calendar page for January 2027, with the 1st circled in red."""
    cv.fill(x, y, w, h, PAPER)
    cv.rect(x, y, w, h, HAIR)
    cv.fill(x, y, w, 30, AMBER)
    cv.text_center(x, y + 8, w, "JANUARY 2027", 2, DARK)
    # binder holes (kept clear of the centred header text)
    for hx in (x + 14, x + w - 14):
        cv.circle(hx, y + 15, 4, DARK, filled=True)
    # day grid: 7 columns x 4 rows of dots, the 1st circled
    gx, gy = x + 16, y + 48
    cell = (w - 32) // 7
    for row in range(4):
        for col in range(7):
            cx = gx + col * cell + cell // 2
            cy = gy + row * 26 + 8
            if row == 0 and col == 0:
                cv.circle(cx, cy, 12, RED)
                cv.circle(cx, cy, 9, RED)
            else:
                cv.circle(cx, cy, 3, MUTED, filled=True)
    cv.text_center(x, y + h - 34, w, "JAN 1", 3, RED)


def draw_spiral(cv, cx, cy, rmax, color):
    """Cyclone spiral: an Archimedean spiral plus a calm eye."""
    import math
    prev = None
    steps = 220
    for i in range(steps + 1):
        t = i / steps
        ang = t * math.pi * 5.0
        r = 6 + t * (rmax - 6)
        px = cx + int(r * math.cos(ang))
        py = cy + int(r * math.sin(ang))
        if prev is not None:
            cv.line(prev[0], prev[1], px, py, color)
        prev = (px, py)
    cv.circle(cx, cy, 7, PAPER, filled=True)
    cv.circle(cx, cy, 7, color)


def draw_scales(cv, x, y, w, h, color):
    """Scales of justice: post, beam, two hanging pans."""
    cx = x + w // 2
    top = y + 8
    cv.fill(cx - 3, top, 6, h - 30, color)          # post
    cv.fill(x + 8, top, w - 16, 5, color)          # beam
    cv.circle(cx, top, 6, color, filled=True)
    for side in (-1, 1):
        px = cx + side * (w // 2 - 16)
        cv.line(cx, top + 2, px, top + 34, color)
        cv.line(px - 2, top + 2, px, top + 34, color)
        cv.line(px + 2, top + 2, px, top + 34, color)
        cv.line(px - 26, top + 34, px + 26, top + 34, color)
        cv.poly([(px - 26, top + 34), (px + 26, top + 34),
                 (px, top + 52)], color)
    cv.fill(x + 18, y + h - 14, w - 36, 6, color)   # base


def draw_bubbles(cv, x, y, w, h, color):
    """Two overlapping speech bubbles: talks under way."""
    rrect(cv, x, y, 96, 56, 10, BLUE)
    rrect(cv, x + 24, y + 48, 96, 56, 10, PAPER)
    cv.rect(x + 24, y + 48, 96, 56, BLUE)
    cv.poly([(x + 16, y + 52), (x + 32, y + 52), (x + 16, y + 72)], BLUE)
    cv.poly([(x + w - 16, y + 100), (x + w - 32, y + 100),
             (x + w - 16, y + 120)], BLUE)
    cv.text(x + 18, y + 19, "TALKS", 2, PAPER)
    cv.text(x + 36, y + 67, "PEACE?", 2, BLUE)


def draw_chart(cv, x, y, w, h, color):
    """Rising bars with an arrow: a market that closed higher."""
    base = y + h - 10
    bars = [34, 58, 46, 82, 104]
    bw = 22
    gap = (w - len(bars) * bw) // (len(bars) + 1)
    for i, bh in enumerate(bars):
        bx = x + gap + i * (bw + gap)
        cv.fill(bx, base - bh, bw, bh, GREEN if i == len(bars) - 1 else BLUE)
    cv.line(x + 8, base - 30, x + w - 34, base - 108, GREEN)
    cv.line(x + w - 34, base - 108, x + w - 52, base - 108, GREEN)
    cv.line(x + w - 34, base - 108, x + w - 34, base - 90, GREEN)
    cv.line(x, base, x + w, base, DARK)


# ------------------------------------------------------------------ layout
def draw_masthead(cv):
    cv.fill(0, 0, W, 112, AMBER)
    cv.text(32, 38, "THE WORLD TODAY", 5, DARK)
    cv.text(1024 - 32 - text_width("FRIDAY", 3), 26, "FRIDAY", 3, DARK)
    cv.text(1024 - 32 - text_width("20 NOVEMBER 2026", 3), 60,
            "20 NOVEMBER 2026", 3, DARK)


def draw_hero(cv):
    x, y, w, h = 24, 128, 976, 272
    cv.fill(x, y, w, h, PAPER)
    cv.text(x + 24, y + 20, "WASHINGTON · MIDDLE EAST", 2, RED)
    cv.text(x + 24, y + 50, "TRUMP PUSHES IRAN", 4, DARK)
    cv.text(x + 24, y + 84, "CALL TO 2027", 4, DARK)
    cv.para(x + 24, y + 130,
            "'WE'LL SEE WHAT HAPPENS AFTER JAN 1,' HE TELLS FOX NEWS -- "
            "NO RUSH ON NEW STRIKES ON IRAN, HE TELLS REUTERS AND AXIOS.",
            2, DARK, 600)
    cv.para(x + 24, y + 130 + 3 * 19 + 8,
            "DECISION ON RENEWED ATTACKS SLIDES INTO NEXT YEAR.",
            2, MUTED, 600)
    cv.hline(x + 24, y + h - 32, 600, HAIR)
    cv.text(x + 24, y + h - 24, "SOURCE: REUTERS, FOX NEWS, AXIOS",
            2, MUTED)
    draw_calendar(cv, x + 672, y + 20, 256, 232, RED)


def draw_card(cv, x, y, accent, kicker, headline, body, source, art):
    w, h = 480, 248
    cv.fill(x, y, w, h, PAPER)
    cv.fill(x, y, w, 10, accent)
    cv.text(x + 20, y + 26, kicker, 2, accent)
    lines = wrap_text(headline, 3, 300)
    yy = y + 56
    for line in lines:
        cv.text(x + 20, yy, line, 3, DARK)
        yy += 27
    cv.para(x + 20, y + 149, body, 2, DARK, 300)
    cv.hline(x + 20, y + h - 34, 300, HAIR)
    cv.text(x + 20, y + h - 26, source, 2, MUTED)
    cv.vline(x + 340, y + 30, h - 60, HAIR)
    art(cv, x + 350, y + 54, 120, 140)


def draw_ticker(cv):
    x, y, w, h = 24, 944, 976, 44
    cv.fill(x, y, w, h, INK_SOFT)
    cv.text(x + 16, y + 5, "ALSO TODAY:", 2, AMBER)
    cv.text(x + 16 + text_width("ALSO TODAY: ", 2), y + 5,
            "GTA VI ~19M COPIES, ~$1.84BN -- BIGGEST LAUNCH EVER",
            2, PAPER)
    cv.text(x + 16, y + 24,
            "JAPAN'S HAYABUSA2 DROPS ASTEROID LANDING AFTER ENGINE TROUBLE",
            2, PAPER)


def draw_footer(cv):
    cv.text_center(0, 998, W,
                   "SOURCES: REUTERS · BBC · IMD · NASDAQ · AP "
                   "-- ALL STORIES REPORTED 20 NOV 2026",
                   2, PAPER)


def build():
    cv = Canvas(W, H, INK)
    draw_masthead(cv)
    draw_hero(cv)
    draw_card(cv, 24, 416, TEAL, "INDIA · WEATHER",
              "CYCLONE AKVAN HITS ODISHA TODAY",
              "LANDFALL ~NOON NEAR GOPALPUR. WINDS 90-100 KM/H. "
              "105,304 EVACUATED.",
              "SOURCE: IMD",
              lambda c, ax, ay, aw, ah: draw_spiral(c, ax + 60, ay + 70, 58, TEAL))
    draw_card(cv, 520, 416, RED, "THE HAGUE · JUSTICE",
              "ICJ: MYANMAR COMMITTED GENOCIDE",
              "9-6 RULING. ~10,000 KILLED IN 2017. "
              "COMPENSATION ORDERED.",
              "SOURCE: BBC / ICJ",
              lambda c, ax, ay, aw, ah: draw_scales(c, ax, ay, 120, 140, RED))
    draw_card(cv, 24, 680, BLUE, "BERLIN · UKRAINE",
              "EUROPE READY FOR RUSSIA TALKS",
              "BERLIN SUMMIT: TALKS ON UKRAINE -- BUT ONLY WITH "
              "KYIV AT THE TABLE.",
              "SOURCE: BBC",
              lambda c, ax, ay, aw, ah: draw_bubbles(c, ax, ay + 10, 120, 130, BLUE))
    draw_card(cv, 520, 680, GREEN, "MARKETS · TECH",
              "ANT +17% ON NASDAQ DEBUT",
              "CLOSES AT $97.17 VS $83 IPO. OPENED $111.50. "
              "RECORD $81.3BN OFFERING.",
              "SOURCE: NASDAQ",
              lambda c, ax, ay, aw, ah: draw_chart(c, ax, ay + 10, 120, 130, GREEN))
    draw_ticker(cv)
    draw_footer(cv)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(build(), path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
