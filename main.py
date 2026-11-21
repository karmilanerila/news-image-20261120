#!/usr/bin/env python3
"""THE WORLD IN ONE PAGE -- Friday 20 November 2026.

A deterministic program that draws a one-page newspaper front page
summing up the world's news of Friday 20 November 2026 and writes it
to /output/entry.png (1024 x 1024 PNG, under 1 MiB).

Every story, date and figure was checked against live reporting on
21 November 2026 (Reuters, AP, BBC, CNN, IMD, UN News, ISW and
others); see SOURCES.md for the source of each fact. No network, no
clock, no randomness: the same run always writes the same bytes.

Run:  python3 main.py                  (writes /output/entry.png)
      OUTPUT_DIR=out python3 main.py   (writes out/entry.png)

Standard library only. The PNG writer (zlib + struct), the drawing
surface and the two bitmap fonts below are all written here, by hand:
a 5x7 text face and a 7x11 display face for the masthead. Nothing is
imported from any font file or package.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024
OUT = os.path.join(
    os.environ.get("OUTPUT_DIR")
    or os.environ.get("MAKEFUN_OUTPUT_DIR")
    or "/output",
    "entry.png",
)

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)
INK = (26, 26, 26)
INK_SOFT = (74, 74, 74)
RULE = (26, 26, 26)
RED = (179, 32, 44)
RED_DARK = (128, 20, 30)
BLUE = (31, 78, 121)
TEAL = (14, 107, 107)
GOLD = (146, 104, 12)
GREY_BG = (232, 228, 218)
GREY_LINE = (190, 184, 170)
MAP_LAND = (206, 214, 200)
MAP_SEA = (226, 235, 240)
WHITE = (255, 255, 255)
CREAM = (255, 252, 244)

# ---------------------------------------------------------------- the news
# 24 stories, 7 regions. Figures checked 21 Nov 2026; see SOURCES.md.
MASTHEAD_TITLE = "THE WORLD IN ONE PAGE"
DATE_LINE = "FRIDAY, 20 NOVEMBER 2026"
COUNT_LINE = "24 STORIES  ·  7 REGIONS"

STATS = [
    ("400+ DRONES", "110+ missiles fired at Ukraine overnight"),
    ("−6.8% TAIEX", "Taiwan leads Asia’s worst week since 2020"),
    ("$3.79BN", "GTA VI day-one sales — the biggest ever"),
    ("300,000+", "people evacuated as Cyclone Akvan lands"),
]

LEADS = [
    {
        "kicker": "UKRAINE · WAR IN EUROPE",
        "art": "kyiv",
        "headline": "Kyiv’s bridges hit in Russia’s biggest barrage of the month",
        "deck": "400+ drones, 110 missiles overnight; nine killed, 28 hurt. Three Dnipro bridges hit.",
        "accent": RED,
    },
    {
        "kicker": "INDIA · WEATHER",
        "art": "cyclone",
        "headline": "Cyclone Akvan comes ashore on India’s east coast",
        "deck": "Landfall near Gopalpur at 8:30am with winds of 70–80 km/h. Heavy rain lashes Odisha and Andhra Pradesh.",
        "accent": TEAL,
    },
    {
        "kicker": "MARKETS · ASIA",
        "art": "markets",
        "headline": "Asia’s AI sell-off deepens into a rout",
        "deck": "Nikkei −4.8%, Kospi −5.2%, Taiex −6.8%. Even Anthropic’s record $81bn IPO cannot stop the slide.",
        "accent": BLUE,
    },
]

CARDS = [
    ("CLIMATE · ANTALYA", "COP31 slips into overtime",
     "Draft drops fossil-fuel words and a $120bn finance target."),
    ("EUROPE · BRUSSELS", "UK and EU seal a reset deal",
     "Food trade eased, 100,000 youth visas a year, carbon link 2028."),
    ("DIPLOMACY · SHENZHEN", "Trump, Xi and Putin meet",
     "First-ever trilateral, 90 minutes at APEC; a nuclear war “cannot be won”."),
    ("JUSTICE · THE HAGUE", "Myanmar guilty of genocide",
     "First state ever held responsible; reparations ordered for Rohingya."),
    ("CULTURE · GAMES", "$3.79bn in a day for GTA VI",
     "32.5m copies pre-sold; Metacritic 99. Biggest launch in history."),
    ("AMERICAS · PERU", "M6.9 quake shakes the Andes",
     "Tremor near Junín at 7:09pm, felt in Lima; no casualties reported."),
    ("MIDDLE EAST · RIYADH", "Houthi missile hits Riyadh tower",
     "Tallest tower struck; defences intercept more missiles."),
    ("MARKETS · NEW YORK", "Wall Street slides with tech",
     "Nasdaq −2.3%; tech ETF in bear market, 20% off October peak."),
    ("AMERICAS · NEW YORK", "Rikers Island to close by 2032",
     "Plan to shut the jail complex — five years past the legal deadline."),
    ("UKRAINE · KRYVYI RIH", "Evening strike kills two",
     "Ballistic strike on city centre kills a child and a paramedic."),
    ("SCIENCE · MATHS", "A proof, with AI’s help",
     "A mathematician says Claude helped prove it; verification to come."),
    ("AFRICA · SOUTH AFRICA", "Mlambo-Ngcuka dies at 71",
     "First woman deputy president and ex-UN Women chief, aged 71."),
]

TIMELINE = [
    ("OVERNIGHT", "Russia’s barrage hits Kyiv’s bridges."),
    ("08:30 IST", "Cyclone Akvan lands near Gopalpur."),
    ("MORNING", "Nikkei −4.8%, Kospi −5.2%, Taiex −6.8%."),
    ("AFTERNOON", "COP31 talks spill into overtime."),
    ("EVENING", "M6.9 quake in Peru; UK–EU deal sealed."),
]

BRIEF = [
    "Egypt–IMF final review agreed on $8bn programme.",
    "Miami jury convicts Sanon over Haiti murder plot.",
    "Denmark approves Arctic pact with Greenland, US.",
    "Knesset elects Matan Kahana speaker, 66–52.",
    "Quad backs US-led AI supply-chain pact.",
    "Cell study: gene variant aids mosquito mating.",
    "Ukraine drones reportedly hit Russian chemical plant.",
    "M4.2 quake wakes Los Angeles; no injuries.",
    "Germany rejects any new ‘Yalta’ deal over Europe.",
]

# Schematic world map: (label, x, y) in panel coordinates 0..1,
# plus rough continent blobs as (cx, cy, rx, ry).
MAP_POINTS = [
    ("1 Kyiv", 0.485, 0.30), ("2 Antalya", 0.52, 0.38),
    ("3 Brussels", 0.425, 0.30), ("4 Shenzhen", 0.79, 0.50),
    ("5 Gopalpur", 0.72, 0.55), ("6 Riyadh", 0.585, 0.47),
    ("7 Lima", 0.20, 0.68), ("8 The Hague", 0.46, 0.235),
    ("9 New York", 0.235, 0.38), ("10 Pretoria", 0.545, 0.72),
    ("11 Cairo", 0.545, 0.44), ("12 Canberra", 0.875, 0.80),
]
MAP_BLOBS = [
    (0.20, 0.33, 0.115, 0.085),   # North America
    (0.26, 0.68, 0.055, 0.085),   # South America
    (0.52, 0.60, 0.075, 0.105),   # Africa
    (0.47, 0.28, 0.045, 0.045),   # Europe
    (0.72, 0.35, 0.155, 0.105),   # Asia
    (0.87, 0.78, 0.045, 0.035),   # Australia
]
MAP_LEGEND = [
    "1 Kyiv  ·  2 Antalya  ·  3 Brussels  ·  4 Shenzhen  ·  5 Gopalpur  ·  6 Riyadh",
    "7 Lima  ·  8 The Hague  ·  9 New York  ·  10 Pretoria  ·  11 Cairo  ·  12 Canberra",
]

# ---------------------------------------------------------------- fonts
# Hand-drawn bitmap faces. Each glyph is (advance, (row0, ..., row6)):
# rows are 5-bit values, bit 4 is the leftmost column, bit 0 the
# rightmost. Row 0 is the top of the cell; the baseline is row 6.
# Capitals and digits use the full cell; lowercase x-height letters
# sit on rows 2..6, ascenders reach row 0, descenders tail to row 6.
# No font file, no package data: every row below was drawn by hand.
FONT_5X7 = {
    32: (3, (0, 0, 0, 0, 0, 0, 0)),
    33: (3, (4, 4, 4, 4, 4, 0, 4)),
    34: (4, (10, 10, 10, 0, 0, 0, 0)),
    35: (5, (10, 10, 31, 10, 10, 31, 10)),
    36: (5, (4, 15, 20, 14, 5, 30, 4)),
    37: (5, (25, 26, 2, 4, 8, 11, 19)),
    38: (5, (12, 18, 20, 8, 21, 18, 13)),
    39: (3, (4, 4, 8, 0, 0, 0, 0)),
    40: (4, (2, 4, 8, 8, 8, 4, 2)),
    41: (4, (8, 4, 2, 2, 2, 4, 8)),
    42: (5, (0, 4, 21, 14, 21, 4, 0)),
    43: (5, (0, 4, 4, 31, 4, 4, 0)),
    44: (3, (0, 0, 0, 0, 0, 12, 8)),
    45: (5, (0, 0, 0, 31, 0, 0, 0)),
    46: (3, (0, 0, 0, 0, 0, 0, 12)),
    47: (5, (1, 1, 2, 2, 4, 8, 16)),
    48: (5, (14, 17, 19, 21, 25, 17, 14)),
    49: (5, (4, 12, 4, 4, 4, 4, 14)),
    50: (5, (14, 17, 1, 2, 4, 8, 31)),
    51: (5, (31, 2, 4, 2, 1, 17, 14)),
    52: (5, (2, 6, 10, 18, 31, 2, 2)),
    53: (5, (31, 16, 30, 1, 1, 17, 14)),
    54: (5, (6, 8, 16, 30, 17, 17, 14)),
    55: (5, (31, 1, 2, 4, 8, 8, 8)),
    56: (5, (14, 17, 17, 14, 17, 17, 14)),
    57: (5, (14, 17, 17, 15, 1, 2, 12)),
    58: (3, (0, 12, 0, 0, 0, 12, 0)),
    59: (3, (0, 12, 0, 0, 0, 12, 8)),
    60: (5, (2, 4, 8, 16, 8, 4, 2)),
    61: (5, (0, 0, 31, 0, 31, 0, 0)),
    62: (5, (8, 4, 2, 1, 2, 4, 8)),
    63: (5, (14, 17, 1, 2, 4, 0, 4)),
    64: (5, (14, 17, 23, 21, 23, 16, 14)),
    65: (5, (14, 17, 17, 31, 17, 17, 17)),
    66: (5, (30, 17, 17, 30, 17, 17, 30)),
    67: (5, (14, 17, 16, 16, 16, 17, 14)),
    68: (5, (30, 17, 17, 17, 17, 17, 30)),
    69: (5, (31, 16, 16, 30, 16, 16, 31)),
    70: (5, (31, 16, 16, 30, 16, 16, 16)),
    71: (5, (14, 17, 16, 23, 17, 17, 15)),
    72: (5, (17, 17, 17, 31, 17, 17, 17)),
    73: (5, (14, 4, 4, 4, 4, 4, 14)),
    74: (5, (7, 2, 2, 2, 2, 18, 12)),
    75: (5, (17, 18, 20, 24, 20, 18, 17)),
    76: (5, (16, 16, 16, 16, 16, 16, 31)),
    77: (5, (17, 27, 21, 21, 17, 17, 17)),
    78: (5, (17, 25, 21, 19, 17, 17, 17)),
    79: (5, (14, 17, 17, 17, 17, 17, 14)),
    80: (5, (30, 17, 17, 30, 16, 16, 16)),
    81: (5, (14, 17, 17, 17, 21, 18, 13)),
    82: (5, (30, 17, 17, 30, 20, 18, 17)),
    83: (5, (15, 16, 16, 14, 1, 1, 30)),
    84: (5, (31, 4, 4, 4, 4, 4, 4)),
    85: (5, (17, 17, 17, 17, 17, 17, 14)),
    86: (5, (17, 17, 17, 17, 17, 10, 4)),
    87: (6, (17, 17, 17, 21, 21, 27, 17)),
    88: (5, (17, 17, 10, 4, 10, 17, 17)),
    89: (5, (17, 17, 10, 4, 4, 4, 4)),
    90: (5, (31, 1, 2, 4, 8, 16, 31)),
    91: (4, (14, 8, 8, 8, 8, 8, 14)),
    92: (5, (16, 8, 8, 4, 4, 2, 1)),
    93: (4, (14, 2, 2, 2, 2, 2, 14)),
    94: (5, (4, 10, 17, 0, 0, 0, 0)),
    95: (5, (0, 0, 0, 0, 0, 0, 31)),
    96: (3, (8, 4, 2, 0, 0, 0, 0)),
    97: (5, (0, 0, 14, 1, 15, 17, 15)),
    98: (5, (16, 16, 30, 17, 17, 17, 30)),
    99: (5, (0, 0, 14, 16, 16, 17, 14)),
    100: (5, (1, 1, 15, 17, 17, 17, 15)),
    101: (5, (0, 0, 14, 17, 31, 16, 14)),
    102: (4, (6, 8, 8, 30, 8, 8, 8)),
    103: (5, (0, 14, 17, 17, 15, 1, 14)),
    104: (5, (16, 16, 30, 17, 17, 17, 17)),
    105: (3, (4, 0, 12, 4, 4, 4, 14)),
    106: (3, (2, 0, 6, 2, 2, 18, 12)),
    107: (5, (16, 16, 18, 20, 24, 20, 18)),
    108: (3, (12, 4, 4, 4, 4, 4, 14)),
    109: (6, (0, 0, 26, 21, 21, 21, 21)),
    110: (5, (0, 0, 30, 17, 17, 17, 17)),
    111: (5, (0, 0, 14, 17, 17, 17, 14)),
    112: (5, (0, 0, 30, 17, 17, 30, 16)),
    113: (5, (0, 0, 15, 17, 17, 15, 1)),
    114: (4, (0, 0, 22, 28, 16, 16, 16)),
    115: (5, (0, 0, 15, 16, 14, 1, 30)),
    116: (3, (4, 4, 31, 4, 4, 4, 6)),
    117: (5, (0, 0, 17, 17, 17, 19, 14)),
    118: (5, (0, 0, 17, 17, 17, 10, 4)),
    119: (6, (0, 0, 17, 21, 21, 21, 10)),
    120: (5, (0, 0, 17, 10, 4, 10, 17)),
    121: (5, (0, 0, 17, 17, 15, 1, 14)),
    122: (5, (0, 0, 31, 2, 4, 8, 31)),
    123: (4, (6, 8, 8, 30, 8, 8, 6)),
    124: (3, (4, 4, 4, 4, 4, 4, 4)),
    125: (4, (12, 2, 2, 15, 2, 2, 12)),
    126: (5, (0, 0, 0, 8, 21, 0, 0)),
    8212: (5, (0, 0, 0, 31, 0, 0, 0)),
    8211: (5, (0, 0, 0, 14, 0, 0, 0)),
    8722: (5, (0, 0, 0, 14, 0, 0, 0)),
    183: (3, (0, 0, 0, 4, 0, 0, 0)),
    9642: (5, (0, 0, 14, 14, 14, 0, 0)),
    8217: (3, (4, 4, 8, 0, 0, 0, 0)),
    8216: (3, (8, 8, 4, 0, 0, 0, 0)),
    8220: (5, (10, 10, 8, 0, 0, 0, 0)),
    8221: (5, (10, 10, 10, 0, 0, 0, 0)),
    233: (5, (2, 0, 14, 17, 31, 16, 14)),
    237: (3, (2, 0, 12, 4, 4, 4, 14)),
    252: (5, (10, 0, 17, 17, 17, 19, 14)),
}

# Masthead display face: 7 columns (bit 6 is the leftmost), 11 rows,
# one line per letter. Only the letters of the masthead title are
# needed, plus a space. Drawn by hand, same grid as the text face.
FONT_DISPLAY = {
    32: (4, (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
    65: (8, (8, 20, 34, 34, 62, 65, 65, 65, 65, 65, 65)),
    68: (8, (124, 66, 65, 65, 65, 65, 65, 65, 65, 66, 124)),
    69: (8, (126, 64, 64, 64, 124, 64, 64, 64, 64, 64, 126)),
    71: (8, (60, 66, 64, 64, 64, 71, 65, 65, 66, 66, 60)),
    72: (8, (65, 65, 65, 65, 65, 127, 65, 65, 65, 65, 65)),
    73: (8, (62, 8, 8, 8, 8, 8, 8, 8, 8, 8, 62)),
    76: (8, (64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 126)),
    78: (8, (65, 97, 81, 73, 69, 67, 65, 65, 65, 65, 65)),
    79: (8, (60, 66, 65, 65, 65, 65, 65, 65, 65, 66, 60)),
    80: (8, (124, 66, 65, 65, 65, 124, 64, 64, 64, 64, 64)),
    82: (8, (124, 66, 65, 65, 65, 124, 66, 68, 72, 80, 96)),
    84: (8, (127, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8)),
    87: (8, (65, 65, 65, 65, 65, 65, 65, 85, 85, 42, 20)),
}


class Face:
    """One bitmap face: a glyph table, a cell size and a scale.

    `bold` thickens every stroke by one pixel to the right, inside the
    glyph cell (bits | bits >> 1), so bold and regular share a table.
    """

    __slots__ = ("table", "rows", "cols", "scale", "bold")

    def __init__(self, table, rows, cols, scale, bold=False):
        self.table = table
        self.rows = rows
        self.cols = cols
        self.scale = scale
        self.bold = bold

    def advance(self, ch):
        g = self.table.get(ord(ch))
        if g is None:
            return 3 * self.scale
        return g[0] * self.scale

    def width(self, s):
        total = 0
        for ch in s:
            total += self.advance(ch)
        return total


_FACES = {}


def face(kind, size):
    """The face for a (kind, size) pair, cached.

    kind is "serif_b", "sans_b" or "sans". The 56pt masthead uses the
    display face; every other size uses the 5x7 face, at scale 2 for
    13pt and up and scale 1 below it.
    """
    key = (kind, size)
    got = _FACES.get(key)
    if got is not None:
        return got
    if kind == "serif_b" and size == 56:
        made = Face(FONT_DISPLAY, 11, 7, 5)
    else:
        scale = 2 if size >= 13 else 1
        made = Face(FONT_5X7, 7, 5, scale, bold=(kind != "sans"))
    _FACES[key] = made
    return made

# ---------------------------------------------------------------- canvas
class Page:
    """An RGB picture kept as one flat bytearray, with primitives."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def px(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = (y * self.w + x) * 3
            self.buf[o] = rgb[0]
            self.buf[o + 1] = rgb[1]
            self.buf[o + 2] = rgb[2]

    def rect(self, x0, y0, x1, y1, rgb):
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, self.w - 1)
        y1 = min(y1, self.h - 1)
        if x1 < x0 or y1 < y0:
            return
        row = bytes(rgb) * (x1 - x0 + 1)
        stride = self.w * 3
        for y in range(y0, y1 + 1):
            o = y * stride + x0 * 3
            self.buf[o:o + len(row)] = row

    def thin(self, x0, y0, x1, y1, rgb):
        """One-pixel line (Bresenham)."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        w, h, buf = self.w, self.h, self.buf
        r, g, b = rgb
        while True:
            if 0 <= x0 < w and 0 <= y0 < h:
                o = (y0 * w + x0) * 3
                buf[o] = r
                buf[o + 1] = g
                buf[o + 2] = b
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def line(self, x0, y0, x1, y1, rgb, width=1):
        if width <= 1:
            self.thin(x0, y0, x1, y1, rgb)
            return
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        if length == 0:
            r = width // 2
            self.rect(x0 - r, y0 - r, x0 + r, y0 + r, rgb)
            return
        # A thick line is a solid band of `width` centred on the
        # segment, drawn as one filled polygon: drawing it as
        # parallel thin lines would leave gaps on diagonals.
        px = -dy / length * (width / 2.0)
        py = dx / length * (width / 2.0)
        self.poly([(x0 + px, y0 + py), (x1 + px, y1 + py),
                   (x1 - px, y1 - py), (x0 - px, y0 - py)], rgb)

    def disc(self, x0, y0, x1, y1, rgb):
        """Filled ellipse inside the box (x0, y0, x1, y1)."""
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        if rx <= 0 or ry <= 0:
            self.rect(x0, y0, x1, y1, rgb)
            return
        for y in range(max(y0, 0), min(y1, self.h - 1) + 1):
            t = (y - cy) / ry
            if abs(t) > 1:
                continue
            dx = rx * math.sqrt(1 - t * t)
            xa = int(math.ceil(cx - dx))
            xb = int(math.floor(cx + dx))
            self.rect(xa, y, xb, y, rgb)

    def ring(self, x0, y0, x1, y1, rgb):
        """One-pixel ellipse outline."""
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        steps = max(int(2 * math.pi * max(rx, ry)), 24)
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            self.px(int(round(cx + rx * math.cos(a))),
                    int(round(cy + ry * math.sin(a))), rgb)

    def arc(self, x0, y0, x1, y1, start, end, rgb, width=1):
        """Arc of an ellipse. Angles in degrees, 0 at 3 o'clock,
        increasing clockwise (y grows downwards)."""
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        sweep = end - start
        steps = max(int(abs(sweep) / 2), 8)
        prev = None
        for i in range(steps + 1):
            a = math.radians(start + sweep * i / steps)
            px = int(round(cx + rx * math.cos(a)))
            py = int(round(cy + ry * math.sin(a)))
            if prev is not None:
                self.line(prev[0], prev[1], px, py, rgb, width)
            prev = (px, py)

    def poly(self, points, rgb):
        """Filled polygon, scanline by scanline."""
        ys = [p[1] for p in points]
        ymin = max(int(math.floor(min(ys))), 0)
        ymax = min(int(math.ceil(max(ys))), self.h - 1)
        n = len(points)
        for y in range(ymin, ymax + 1):
            xs = []
            for i in range(n):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(math.ceil(xs[i])), y,
                          int(math.floor(xs[i + 1])), y, rgb)

    def blit(self, x, y, s, fnt, fill):
        """Draw text; (x, y) is the top-left of the glyph cells."""
        pen = x
        scale = fnt.scale
        for ch in s:
            g = fnt.table.get(ord(ch))
            if g is None:
                pen += 3 * scale
                continue
            adv, rows = g
            for r in range(fnt.rows):
                bits = rows[r]
                if fnt.bold:
                    bits = bits | (bits >> 1)
                if not bits:
                    continue
                yy = y + r * scale
                for c in range(fnt.cols):
                    if bits & (1 << (fnt.cols - 1 - c)):
                        xx = pen + c * scale
                        self.rect(xx, yy, xx + scale - 1,
                                  yy + scale - 1, fill)
            pen += adv * scale


class Pen:
    """A small drawing API over a Page, with PIL-like call shapes."""

    def __init__(self, page):
        self.p = page

    @staticmethod
    def _box(box):
        return int(box[0]), int(box[1]), int(box[2]), int(box[3])

    def rectangle(self, box, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = self._box(box)
        if fill is not None:
            self.p.rect(x0, y0, x1, y1, fill)
        if outline is not None:
            for k in range(width):
                self.p.rect(x0 + k, y0 + k, x1 - k, y0 + k, outline)
                self.p.rect(x0 + k, y1 - k, x1 - k, y1 - k, outline)
                self.p.rect(x0 + k, y0 + k, x0 + k, y1 - k, outline)
                self.p.rect(x1 - k, y0 + k, x1 - k, y1 - k, outline)

    def ellipse(self, box, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = self._box(box)
        if fill is not None:
            self.p.disc(x0, y0, x1, y1, fill)
        if outline is not None:
            self.p.ring(x0, y0, x1, y1, outline)

    def line(self, points, fill=None, width=1):
        if points and isinstance(points[0], (int, float)):
            pts = [(int(points[i]), int(points[i + 1]))
                   for i in range(0, len(points) - 1, 2)]
        else:
            pts = [(int(p[0]), int(p[1])) for p in points]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            self.p.line(x0, y0, x1, y1, fill, width)

    def arc(self, box, start, end, fill=None, width=1):
        x0, y0, x1, y1 = self._box(box)
        self.p.arc(x0, y0, x1, y1, start, end, fill, width)

    def polygon(self, points, fill=None):
        self.p.poly([(int(p[0]), int(p[1])) for p in points], fill)

    def text(self, xy, s, font=None, fill=None):
        self.p.blit(int(xy[0]), int(xy[1]), s, font, fill)

    def textlength(self, s, font=None):
        return font.width(s)

# ---------------------------------------------------------------- PNG encoder
_ABS = bytes(min(b, 256 - b) for b in range(256))


def _chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data +
            struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))


def _filtered(row, prev):
    """The three candidate encodings of one scanline: filter 0 (None),
    filter 1 (Sub) and filter 2 (Up), each as (filter, bytes, score),
    where the score is the sum of the absolute values of the signed
    filtered bytes. The smallest score wins."""
    cands = [(0, row, sum(row.translate(_ABS)))]
    sub = row[:3] + bytes((a - b) & 0xFF for a, b in zip(row[3:], row))
    cands.append((1, sub, sum(sub.translate(_ABS))))
    up = bytes((a - b) & 0xFF for a, b in zip(row, prev))
    cands.append((2, up, sum(up.translate(_ABS))))
    return min(cands, key=lambda c: c[2])


def encode_png(page):
    """RGB PNG, 8-bit, zlib level 9, one filter byte per scanline."""
    w, h = page.w, page.h
    buf = page.buf
    stride = w * 3
    out = bytearray(b"\x89PNG\r\n\x1a\n")
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    raw = bytearray()
    prev = bytes(stride)
    for y in range(h):
        row = bytes(buf[y * stride:(y + 1) * stride])
        f, best, _score = _filtered(row, prev)
        raw.append(f)
        raw += best
        prev = row
    out += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += _chunk(b"IEND", b"")
    return bytes(out)


# ---------------------------------------------------------------- text tools
def wrap(pen, text, fnt, width):
    """Greedy word wrap; returns the lines that fit `width`."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if pen.textlength(trial, font=fnt) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(pen, x, y, text, fnt, width, fill=INK,
                 max_lines=None, line_h=None):
    """Draw wrapped text; returns (lines drawn, height used)."""
    lines = wrap(pen, text, fnt, width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and pen.textlength(lines[-1] + " ...", font=fnt) > width:
            lines[-1] = lines[-1][:-1].rstrip()
        lines[-1] = lines[-1] + " ..."
    lh = line_h or int(fnt.scale * fnt.rows * 1.22)
    for i, ln in enumerate(lines):
        pen.text((x, y + i * lh), ln, font=fnt, fill=fill)
    return len(lines), len(lines) * lh

# ---------------------------------------------------------------- art panels
def art_kyiv(d, x, y, w, h):
    """Night sky over Kyiv: river, bridge silhouette, missile trails."""
    d.rectangle([x, y, x + w, y + h], fill=(24, 30, 46))
    # stars
    for sx, sy in [(0.08, 0.12), (0.22, 0.06), (0.38, 0.15), (0.55, 0.08),
                   (0.70, 0.14), (0.86, 0.07), (0.93, 0.20), (0.47, 0.05),
                   (0.63, 0.22), (0.15, 0.24)]:
        d.ellipse([x + sx * w - 1, y + sy * h - 1, x + sx * w + 1, y + sy * h + 1],
                  fill=(220, 220, 200))
    # moon
    d.ellipse([x + 0.82 * w, y + 0.10 * h, x + 0.90 * w, y + 0.10 * h + 0.08 * w],
              fill=(235, 230, 210))
    # missile trails
    for (x0, y0, x1, y1) in [(0.05, 0.10, 0.30, 0.55), (0.35, 0.05, 0.52, 0.50),
                             (0.62, 0.12, 0.78, 0.55)]:
        d.line([x + x0 * w, y + y0 * h, x + x1 * w, y + y1 * h],
               fill=(255, 170, 60), width=3)
        d.ellipse([x + x1 * w - 5, y + y1 * h - 5, x + x1 * w + 5, y + y1 * h + 5],
                  fill=(255, 120, 40))
    # explosion bursts
    for cx, cy, r in [(0.30, 0.55, 16), (0.52, 0.50, 12), (0.78, 0.55, 14)]:
        for rr, col in [(r, (255, 190, 80)), (int(r * 0.6), (255, 120, 40)),
                        (int(r * 0.3), (255, 220, 130))]:
            d.ellipse([x + cx * w - rr, y + cy * h - rr,
                       x + cx * w + rr, y + cy * h + rr], fill=col)
    # river
    d.rectangle([x, y + 0.78 * h, x + w, y + h], fill=(52, 84, 110))
    for i in range(6):
        yy = y + (0.81 + i * 0.03) * h
        d.line([x + 6, yy, x + w - 6, yy], fill=(120, 160, 190), width=1)
    # bridge silhouette
    by = y + 0.66 * h
    d.rectangle([x, by, x + w, by + 5], fill=(12, 14, 20))
    for px in (0.18, 0.50, 0.82):
        d.line([x + px * w, by, x + px * w, y + 0.42 * h], fill=(12, 14, 20), width=4)
        d.line([x + px * w, y + 0.42 * h, x + (px - 0.14) * w, by],
               fill=(12, 14, 20), width=2)
        d.line([x + px * w, y + 0.42 * h, x + (px + 0.14) * w, by],
               fill=(12, 14, 20), width=2)
    # city skyline
    for bx, bw, bh in [(0.02, 0.06, 0.14), (0.10, 0.05, 0.20), (0.30, 0.07, 0.12),
                       (0.58, 0.06, 0.18), (0.68, 0.05, 0.10), (0.90, 0.07, 0.16)]:
        d.rectangle([x + bx * w, y + 0.78 * h - bh * h, x + (bx + bw) * w,
                     y + 0.78 * h], fill=(12, 14, 20))
    d.rectangle([x, y, x + w, y + h], outline=(26, 26, 26), width=1)


def art_cyclone(d, x, y, w, h):
    """Cyclone spiral over a coastline."""
    d.rectangle([x, y, x + w, y + h], fill=(16, 74, 92))
    cx, cy = x + 0.38 * w, y + 0.52 * h
    # spiral bands
    for k in range(1, 7):
        r = k * 0.055 * w
        d.arc([cx - r, cy - r * 0.85, cx + r, cy + r * 0.85],
              start=200 + k * 28, end=200 + k * 28 + 235,
              fill=(235, 245, 248) if k % 2 else (140, 200, 215), width=7)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(235, 245, 248))
    # rain bands
    for rx in (0.62, 0.72, 0.82, 0.92):
        for i in range(5):
            ry = 0.12 + i * 0.16
            d.line([x + rx * w, y + ry * h, x + (rx - 0.03) * w,
                    y + (ry + 0.08) * h], fill=(180, 220, 230), width=2)
    # coastline + land
    d.polygon([(x + 0.62 * w, y + h), (x + 0.68 * w, y + 0.55 * h),
               (x + 0.78 * w, y + 0.30 * h), (x + w, y + 0.22 * h),
               (x + w, y + h)], fill=(214, 196, 150))
    d.ellipse([x + 0.74 * w, y + 0.42 * h, x + 0.74 * w + 7, y + 0.42 * h + 7],
              fill=RED)
    d.text((x + 0.76 * w, y + 0.40 * h), "GOPALPUR", font=face("sans_b", 10),
           fill=(60, 40, 20))
    d.rectangle([x, y, x + w, y + h], outline=(26, 26, 26), width=1)


def art_markets(d, x, y, w, h):
    """Falling market chart: red bars and a plunging line."""
    d.rectangle([x, y, x + w, y + h], fill=(250, 244, 238))
    # grid
    for gy in (0.25, 0.50, 0.75):
        d.line([x + 8, y + gy * h, x + w - 8, y + gy * h], fill=(225, 215, 200), width=1)
    # bars, falling left to right
    vals = [0.86, 0.80, 0.83, 0.72, 0.66, 0.58, 0.48, 0.40]
    bw = w / len(vals) * 0.62
    for i, v in enumerate(vals):
        bx = x + (i + 0.5) * (w / len(vals)) - bw / 2
        d.rectangle([bx, y + h - 14 - v * (h - 34), bx + bw, y + h - 14],
                    fill=(196, 60, 60) if i >= 5 else (224, 122, 95))
    # plunging line
    pts = []
    for i, v in enumerate(vals):
        pts.append((x + (i + 0.5) * (w / len(vals)), y + h - 14 - v * (h - 34) - 8))
    d.line(pts, fill=RED_DARK, width=3)
    for px, py in pts:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=RED_DARK)
    # labels
    d.text((x + 10, y + 8), "NIKKEI −4.8%", font=face("sans_b", 12), fill=RED_DARK)
    d.text((x + w - 108, y + 8), "TAIEX −6.8%", font=face("sans_b", 12), fill=RED_DARK)
    d.text((x + 10, y + h - 26), "KOSPI −5.2%", font=face("sans_b", 12), fill=RED_DARK)
    d.rectangle([x, y, x + w, y + h], outline=(26, 26, 26), width=1)


ART = {"kyiv": art_kyiv, "cyclone": art_cyclone, "markets": art_markets}

# ---------------------------------------------------------------- sections
def section_rule(d, x, y, w, label):
    f = face("sans_b", 11)
    d.text((x, y), label, font=f, fill=INK)
    tw = d.textlength(label, font=f)
    d.line([x + tw + 8, y + 7, x + w, y + 7], fill=RULE, width=1)


def draw_masthead(d):
    d.rectangle([0, 0, W, H], fill=PAPER)
    # top hairlines
    d.line([24, 12, W - 24, 12], fill=RULE, width=2)
    d.line([24, 16, W - 24, 16], fill=RULE, width=1)
    f_small = face("sans", 11)
    d.text((24, 22), "VOL. I — No. 325", font=f_small, fill=INK_SOFT)
    d.text((W - 24 - d.textlength("ONE DAY · ONE PAGE · THE WHOLE WORLD", font=f_small), 22),
           "ONE DAY · ONE PAGE · THE WHOLE WORLD", font=f_small, fill=INK_SOFT)
    f_title = face("serif_b", 56)
    t = MASTHEAD_TITLE
    d.text(((W - d.textlength(t, font=f_title)) / 2, 40), t, font=f_title, fill=INK)
    # dateline bar
    d.rectangle([24, 102, W - 24, 130], fill=INK)
    f_date = face("sans_b", 15)
    d.text((36, 109), DATE_LINE, font=f_date, fill=WHITE)
    cw = d.textlength(COUNT_LINE, font=f_date)
    d.text((W - 36 - cw, 109), COUNT_LINE, font=f_date, fill=WHITE)


def draw_stats(d):
    y0, y1, x0 = 140, 186, 24
    w = (W - 48 - 3 * 10) / 4
    f_big = face("sans_b", 20)
    f_lab = face("sans", 11)
    for i, (big, lab) in enumerate(STATS):
        x = x0 + i * (w + 10)
        d.rectangle([x, y0, x + w, y1], outline=GREY_LINE, width=1, fill=CREAM)
        d.rectangle([x, y0, x + w, y0 + 3], fill=RED)
        d.text((x + 10, y0 + 10), big, font=f_big, fill=RED_DARK)
        draw_wrapped(d, x + 10, y0 + 31, lab, f_lab, w - 20, fill=INK_SOFT,
                     max_lines=1, line_h=12)


def draw_lead(d, x, y, w, lead):
    art_h = 130
    ART[lead["art"]](d, x, y, w, art_h)
    yy = y + art_h + 8
    f_kick = face("sans_b", 10)
    d.text((x, yy), lead["kicker"], font=f_kick, fill=lead["accent"])
    yy += 15
    d.line([x, yy, x + w, yy], fill=GREY_LINE, width=1)
    yy += 6
    f_head = face("serif_b", 21)
    _, used = draw_wrapped(d, x, yy, lead["headline"], f_head, w, max_lines=2,
                           line_h=25)
    yy += used + 4
    f_deck = face("sans", 12)
    draw_wrapped(d, x, yy, lead["deck"], f_deck, w, max_lines=2, line_h=15)


def draw_card(d, x, y, w, h, kicker, headline, deck, idx):
    d.rectangle([x, y, x + w, y + h], outline=GREY_LINE, width=1, fill=CREAM)
    d.rectangle([x, y, x + 4, y + h], fill=RED if idx % 3 == 0 else
                (BLUE if idx % 3 == 1 else TEAL))
    tx = x + 12
    f_kick = face("sans_b", 9)
    d.text((tx, y + 7), kicker, font=f_kick, fill=INK_SOFT)
    f_head = face("serif_b", 13)
    _, used = draw_wrapped(d, tx, y + 22, headline, f_head, w - 22,
                           max_lines=2, line_h=16)
    f_deck = face("sans", 11)
    draw_wrapped(d, tx, y + 22 + used + 2, deck, f_deck, w - 22,
                 fill=INK_SOFT, max_lines=2, line_h=13)


def draw_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], outline=GREY_LINE, width=1, fill=MAP_SEA)
    section_rule(d, x + 10, y + 8, w - 20, "THE WORLD AT A GLANCE — SCHEMATIC MAP")
    my = y + 30
    mh = h - 30 - 40
    # graticule
    for gx in (0.25, 0.5, 0.75):
        d.line([x + gx * w, my, x + gx * w, my + mh], fill=(200, 212, 220), width=1)
    for gy in (0.33, 0.66):
        d.line([x, my + gy * mh, x + w, my + gy * mh], fill=(200, 212, 220), width=1)
    # continents (schematic blobs)
    for (cx, cy, rx, ry) in MAP_BLOBS:
        d.ellipse([x + (cx - rx) * w, my + (cy - ry) * mh,
                   x + (cx + rx) * w, my + (cy + ry) * mh], fill=MAP_LAND,
                  outline=(160, 170, 150), width=1)
    f_dot = face("sans_b", 9)
    for label, px, py in MAP_POINTS:
        num, name = label.split(" ", 1)
        dx, dy = x + px * w, my + py * mh
        d.ellipse([dx - 8, dy - 8, dx + 8, dy + 8], fill=RED, outline=WHITE, width=1)
        tw = d.textlength(num, font=f_dot)
        d.text((dx - tw / 2, dy - 6), num, font=f_dot, fill=WHITE)
    # legend
    ly = my + mh + 8
    f_leg = face("sans", 10)
    for i, line in enumerate(MAP_LEGEND):
        d.text((x + 10, ly + i * 13), line, font=f_leg, fill=INK_SOFT)


def draw_right(d, x, y, w):
    section_rule(d, x, y, w, "THE DAY IN ORDER")
    yy = y + 24
    f_t = face("sans_b", 11)
    f_b = face("sans", 11)
    for when, what in TIMELINE:
        d.text((x, yy), when, font=f_t, fill=RED_DARK)
        d.text((x + 82, yy), what, font=f_b, fill=INK)
        yy += 22
    return yy


def draw_brief_strip(d, x, y, w):
    section_rule(d, x, y, w, "IN BRIEF")
    yy = y + 20
    f_br = face("sans", 11)
    col_w = (w - 2 * 16) / 3
    for i, item in enumerate(BRIEF):
        cx = x + (i % 3) * (col_w + 16)
        cy = yy + (i // 3) * 15
        d.text((cx, cy), "▪ ", font=f_br, fill=RED)
        d.text((cx + 12, cy), item, font=f_br, fill=INK_SOFT)


def draw_footer(d):
    f = face("sans", 9)
    line = ("All stories reported on Friday 20 November 2026 · Figures as reported by "
            "Reuters, AP, BBC, CNN, IMD, the UN and ISW · THE WORLD IN ONE PAGE")
    d.text(((W - d.textlength(line, font=f)) / 2, H - 12), line, font=f,
           fill=INK_SOFT)


# ---------------------------------------------------------------- assemble
def build():
    page = Page(W, H, PAPER)
    d = Pen(page)
    draw_masthead(d)
    draw_stats(d)
    # leads
    lx, ly, lw, gap = 24, 192, (W - 48 - 2 * 10) / 3, 10
    for i, lead in enumerate(LEADS):
        draw_lead(d, lx + i * (lw + gap), ly, lw, lead)
    # cards
    section_rule(d, 24, 444, W - 48, "INSIDE TODAY")
    cw, ch, cg = (W - 48 - 3 * 8) / 4, 96, 8
    for i, (kick, head, deck) in enumerate(CARDS):
        cx = 24 + (i % 4) * (cw + cg)
        cy = 466 + (i // 4) * (ch + cg)
        draw_card(d, cx, cy, cw, ch, kick, head, deck, i)
    # bottom row: map + timeline
    by = 778
    draw_map(d, 24, by, 624, 162)
    draw_right(d, 660, by, 340)
    # brief strip
    draw_brief_strip(d, 24, 946, W - 48)
    d.line([24, 1010, W - 24, 1010], fill=RULE, width=1)
    draw_footer(d)
    return page


def main():
    page = build()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "wb") as fh:
        fh.write(encode_png(page))


if __name__ == "__main__":
    main()
