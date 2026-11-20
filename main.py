#!/usr/bin/env python3
"""Draw one poster summing up the world news of Friday 20 November 2026.

Pure Python standard library only. No network, no files read, no
randomness, no clock: the same bytes on every run. Writes a 1024x1024
PNG to $MAKEFUN_OUTPUT_DIR/entry.png (default ./entry.png).

Layout: amber masthead, one hero story (Trump pushes the Iran decision
to 2027), four cards (Cyclone Akvan, the ICJ Myanmar ruling, Europe
ready for Russia talks, Anthropic's Nasdaq debut), and a ticker strip
(GTA VI sales estimates, Hayabusa2). All text is drawn with a
hand-built 5x7 bitmap font, uppercase only.
"""

import os
import struct
import zlib

W, H = 1024, 1024

NAVY = (15, 27, 45)
AMBER = (242, 169, 0)
WHITE = (255, 255, 255)
INK = (15, 27, 45)
SLATE = (51, 65, 85)
TEAL = (13, 148, 136)
CRIMSON = (190, 18, 60)
BLUE = (37, 99, 235)
GREEN = (22, 163, 74)
STRIP = (22, 39, 63)
PALE = (226, 232, 240)

# 5x7 bitmap font, written from scratch for this poster.
# Each glyph is 7 rows of 5 pixels, "#" on, " " off.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    ".": ("     ", "     ", "     ", "     ", "     ", "01100", "01100"),
    ",": ("     ", "     ", "     ", "     ", "01100", "00100", "01000"),
    ":": ("     ", "01100", "01100", "     ", "01100", "01100", "     "),
    ";": ("     ", "01100", "01100", "     ", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "     ", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "     ", "00100"),
    "'": ("00100", "00100", "01000", "     ", "     ", "     ", "     "),
    '"': ("01010", "01010", "     ", "     ", "     ", "     ", "     "),
    "-": ("     ", "     ", "     ", "01110", "     ", "     ", "     "),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("     ", "00100", "00100", "01110", "00100", "00100", "     "),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "*": ("     ", "10101", "01110", "10101", "     ", "     ", "     "),
    "=": ("     ", "     ", "11111", "     ", "11111", "     ", "     "),
    "_": ("     ", "     ", "     ", "     ", "     ", "     ", "11111"),
    "~": ("     ", "     ", "01001", "10110", "     ", "     ", "     "),
}


class Canvas:
    """An RGB pixel buffer with small filled-shape helpers."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def fill_rect(self, x, y, w, h, c):
        x0, x1 = max(x, 0), min(x + w, self.w)
        y0, y1 = max(y, 0), min(y + h, self.h)
        if x0 >= x1 or y0 >= y1:
            return
        b = bytes(c)
        for yy in range(y0, y1):
            base = yy * self.w * 3
            for xx in range(x0, x1):
                i = base + xx * 3
                self.px[i:i + 3] = b

    def rect(self, x, y, w, h, c, t=3):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=2):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=2):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=2):
        """Bresenham line with square thickness."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        half = t // 2
        while True:
            self.fill_rect(x - half, y - half, t, t, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, c, t=2):
        """Midpoint circle outline."""
        x, y, d = r, 0, 1 - r
        while x >= y:
            for px, py in ((cx + x, cy + y), (cx + y, cy + x),
                           (cx - y, cy + x), (cx - x, cy + y),
                           (cx - x, cy - y), (cx - y, cy - x),
                           (cx + y, cy - x), (cx + x, cy - y)):
                self.fill_rect(px - t // 2, py - t // 2, t, t, c)
            y += 1
            if d <= 0:
                d += 2 * y + 1
            else:
                x -= 1
                d += 2 * (y - x) + 1

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5)
            self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, c)

    def triangle(self, pts, c):
        """Filled triangle from three (x, y) points."""
        (x0, y0), (x1, y1), (x2, y2) = pts
        ymin, ymax = min(y0, y1, y2), max(y0, y1, y2)
        for yy in range(ymin, ymax + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= yy <= max(ay, by):
                    xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                self.fill_rect(int(min(xs)), yy, int(max(xs)) - int(min(xs)) + 1, 1, c)


def save_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    data = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        out = struct.pack(">I", len(payload)) + tag + payload
        return out + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", data) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- text

def text_w(s, sc):
    """Pixel width of s at scale sc (6 px per char cell, no trailing gap)."""
    if not s:
        return 0
    return len(s) * 6 * sc - sc


def draw_text(cv, x, y, s, sc, c):
    """Draw uppercase text; unknown chars render as space."""
    s = s.upper()
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    cv.fill_rect(x + col * sc, y + row * sc, sc, sc, c)
        x += 6 * sc


def draw_centered(cv, cx, y, s, sc, c):
    draw_text(cv, cx - text_w(s, sc) // 2, y, s, sc, c)


def wrap(s, sc, maxw):
    """Greedy word wrap; returns a list of lines fitting maxw pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, sc) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- pictograms

def draw_calendar(cv, x, y, w, h, c):
    """A calendar page for January 2027 with the 1st circled."""
    cv.rect(x, y, w, h, c, t=4)
    cv.fill_rect(x, y, w, 34, AMBER)
    draw_centered(cv, x + w // 2, y + 7, "JANUARY 2027", 2, INK)
    # two rows of day cells
    for row in range(2):
        for col in range(7):
            cx = x + 14 + col * 26
            cy = y + 48 + row * 26
            cv.rect(cx, cy, 20, 20, c, t=2)
    # big "1" with a circle around it (radius clears the day cells above)
    draw_text(cv, x + w // 2 - 22, y + 108, "1", 9, c)
    cv.circle(x + w // 2, y + 142, 42, CRIMSON, t=4)


def draw_spiral(cv, cx, cy, c):
    """Concentric rings with a hub: a cyclone seen from above."""
    for r in (42, 30, 18):
        cv.circle(cx, cy, r, c, t=3)
    cv.disc(cx, cy, 5, c)
    cv.line(cx - 52, cy, cx - 42, cy, c, t=3)
    cv.line(cx + 42, cy, cx + 52, cy, c, t=3)
    cv.line(cx, cy - 52, cx, cy - 42, c, t=3)
    cv.line(cx, cy + 42, cx, cy + 52, c, t=3)


def draw_scales(cv, cx, cy, c):
    """The scales of justice: post, beam, two hanging pans."""
    cv.vline(cx, cy - 48, 96, c, t=4)
    cv.hline(cx - 44, cy - 48, 88, c, t=4)
    cv.disc(cx, cy - 52, 5, c)
    for sx in (cx - 44, cx + 44):
        cv.line(sx, cy - 48, sx - 16, cy - 8, c, t=3)
        cv.line(sx, cy - 48, sx + 16, cy - 8, c, t=3)
        cv.line(sx - 16, cy - 8, sx + 16, cy - 8, c, t=3)
        cv.triangle([(sx - 16, cy - 8), (sx + 16, cy - 8), (sx, cy + 8)], c)
    cv.fill_rect(cx - 34, cy + 48, 68, 5, c)


def draw_bubbles(cv, cx, cy, c):
    """Two overlapping speech bubbles, one asking a question."""
    cv.rect(cx - 48, cy - 44, 64, 44, c, t=3)
    cv.triangle([(cx - 32, cy), (cx - 12, cy), (cx - 28, cy + 18)], c)
    cv.rect(cx - 8, cy - 8, 56, 40, AMBER, t=3)
    cv.triangle([(cx + 12, cy + 32), (cx + 30, cy + 32), (cx + 16, cy + 50)], AMBER)
    draw_text(cv, cx + 12, cy + 2, "?", 3, INK)
    draw_text(cv, cx - 34, cy - 34, "TALK", 2, c)


def draw_bars(cv, cx, cy, c):
    """Rising bars: a market debut climbing off the open."""
    base = cy + 52
    cv.hline(cx - 52, base, 108, c, t=4)
    cv.vline(cx - 52, cy - 56, 108, c, t=4)
    heights = (28, 48, 68, 92)
    for i, bh in enumerate(heights):
        bx = cx - 44 + i * 26
        cv.fill_rect(bx, base - bh, 18, bh, GREEN if i == 3 else c)
    cv.line(cx - 52, cy - 56, cx + 56, cy - 60, AMBER, t=3)


# ---------------------------------------------------------------- layout

def draw_masthead(cv):
    cv.fill_rect(24, 24, 976, 104, AMBER)
    draw_centered(cv, 512, 40, "THE WORLD TODAY", 6, INK)
    draw_centered(cv, 512, 94, "FRIDAY / 20 NOVEMBER 2026", 3, INK)


def draw_hero(cv):
    cv.fill_rect(24, 144, 976, 268, WHITE)
    cv.fill_rect(24, 144, 976, 10, AMBER)
    draw_text(cv, 48, 170, "DIPLOMACY", 2, CRIMSON)
    draw_text(cv, 48, 198, "TRUMP PUSHES IRAN", 5, INK)
    draw_text(cv, 48, 238, "DECISION TO 2027", 5, INK)
    draw_text(cv, 48, 292, "NO RUSH ON NEW STRIKES", 3, SLATE)
    draw_text(cv, 48, 320, "'WE'LL SEE WHAT HAPPENS", 3, SLATE)
    draw_text(cv, 48, 348, "AFTER JAN 1' - FOX NEWS", 3, SLATE)
    draw_text(cv, 48, 384, "AXIOS + FOX NEWS - 19 NOV", 2, SLATE)
    draw_calendar(cv, 736, 168, 208, 220, INK)


def draw_card(cv, x, y, accent, tag, lines, details, pict):
    cv.fill_rect(x, y, 476, 210, WHITE)
    cv.fill_rect(x, y, 476, 10, accent)
    draw_text(cv, x + 16, y + 24, tag, 2, accent)
    ly = y + 52
    for ln in lines:
        draw_text(cv, x + 16, ly, ln, 3, INK)
        ly += 28
    dy = y + 122
    for ln in details:
        draw_text(cv, x + 16, dy, ln, 2, SLATE)
        dy += 20
    pict(cv, x + 416, y + 118, accent)


def draw_ticker(cv):
    cv.fill_rect(24, 888, 976, 88, STRIP)
    cv.fill_rect(24, 888, 168, 88, AMBER)
    draw_text(cv, 48, 908, "ALSO", 3, INK)
    draw_text(cv, 48, 936, "TODAY", 3, INK)
    draw_text(cv, 216, 908, "GTA VI ~$1.84BN EST. SALES", 2, WHITE)
    draw_text(cv, 216, 936, "HAYABUSA2 DROPS ASTEROID LANDING", 2, PALE)


def build():
    cv = Canvas(W, H, NAVY)
    draw_masthead(cv)
    draw_hero(cv)
    draw_card(cv, 24, 428, TEAL, "WEATHER",
              ["CYCLONE AKVAN HITS", "ODISHA TODAY"],
              ["LANDFALL ~NOON NEAR", "GOPALPUR - 90-100 KM/H",
               "300,000+ EVACUATED"],
              draw_spiral)
    draw_card(cv, 524, 428, CRIMSON, "JUSTICE",
              ["ICJ: MYANMAR", "COMMITTED GENOCIDE"],
              ["9-6 RULING IN THE HAGUE", "~10,000 KILLED IN 2017",
               "COMPENSATION ORDERED"],
              draw_scales)
    draw_card(cv, 24, 662, BLUE, "DIPLOMACY",
              ["EUROPE READY FOR", "RUSSIA TALKS"],
              ["BERLIN SUMMIT 19 NOV", "TALKS ONLY WITH KYIV",
               "AT THE TABLE"],
              draw_bubbles)
    draw_card(cv, 524, 662, GREEN, "MARKETS",
              ["ANT +17% ON NASDAQ", "DEBUT"],
              ["CLOSES $97.17 VS $83 IPO", "OPENED $111.50 - RECORD",
               "$81.3BN OFFERING"],
              draw_bars)
    draw_ticker(cv)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", ".")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = save_png(build(), path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
