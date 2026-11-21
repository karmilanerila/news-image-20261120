#!/usr/bin/env python3
"""THE WORLD IN ONE PAGE -- Friday 20 November 2026.

A deterministic program that draws a one-page newspaper front page
summing up the world's news of Friday 20 November 2026 and writes it
to /output/entry.png (1024x1024, PNG, <= 1 MiB).

Every story, date and figure below was verified against live reporting
on 21 November 2026 (Reuters, AP, BBC, CNN, IMD, UN News, ISW and
others); see SOURCES.md for the source of each fact. No network access,
no clock, no randomness: the same run always writes the same bytes.

Run:  python3 main.py            (writes /output/entry.png)
      OUTPUT_DIR=out python3 main.py   (writes out/entry.png, for local tests)
Requires: Pillow (PIL). Standard library otherwise.
"""

import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = os.path.join(os.environ.get("OUTPUT_DIR", "/output"), "entry.png")

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

# ---------------------------------------------------------------- fonts
_FONT_DIRS = [
    "/usr/share/fonts/truetype/liberation/",
    "/usr/share/fonts/truetype/dejavu/",
    "/usr/share/fonts/truetype/noto/",
]


def _find(names):
    for d in _FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


_SERIF_B = _find(["LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"])
_SERIF = _find(["LiberationSerif-Regular.ttf", "DejaVuSerif.ttf"])
_SERIF_I = _find(["LiberationSerif-Italic.ttf", "DejaVuSerif-Italic.ttf"])
_SANS = _find(["LiberationSans-Regular.ttf", "DejaVuSans.ttf"])
_SANS_B = _find(["LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"])
_SANS_I = _find(["LiberationSans-Italic.ttf", "DejaVuSans-Oblique.ttf"])


def font(kind, size):
    path = {
        "serif_b": _SERIF_B, "serif": _SERIF, "serif_i": _SERIF_I,
        "sans": _SANS, "sans_b": _SANS_B, "sans_i": _SANS_I,
    }.get(kind) or _SANS
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# ---------------------------------------------------------------- text tools
def wrap(draw, text, fnt, width):
    """Greedy word wrap; returns a list of lines that fit `width`."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, width, fill=INK, spacing=2,
                 max_lines=None, line_h=None):
    """Draw wrapped text; returns (lines_drawn, height_used)."""
    lines = wrap(draw, text, fnt, width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        # ellipsize the last line
        while lines and draw.textlength(lines[-1] + " ...", font=fnt) > width:
            lines[-1] = lines[-1][:-1].rstrip()
        lines[-1] = lines[-1] + " ..."
    lh = line_h or int(fnt.size * 1.22)
    for i, ln in enumerate(lines):
        draw.text((x, y + i * lh), ln, font=fnt, fill=fill)
    return len(lines), len(lines) * lh


def text_h(fnt, lines=1, spacing=2):
    return int(fnt.size * 1.22) * lines + spacing * max(0, lines - 1)


# ---------------------------------------------------------------- the news
# 24 stories, 7 regions. Figures verified 21 Nov 2026; see SOURCES.md.
MASTHEAD_TITLE = "THE WORLD IN ONE PAGE"
DATE_LINE = "FRIDAY, 20 NOVEMBER 2026"
COUNT_LINE = "24 STORIES  \u00b7  7 REGIONS"

STATS = [
    ("400+ DRONES", "110+ missiles fired at Ukraine overnight"),
    ("\u22126.8% TAIEX", "Taiwan leads Asia\u2019s worst week since 2020"),
    ("$3.79BN", "GTA VI day-one sales \u2014 the biggest ever"),
    ("300,000+", "people evacuated as Cyclone Akvan lands"),
]

LEADS = [
    {
        "kicker": "UKRAINE \u00b7 WAR IN EUROPE",
        "art": "kyiv",
        "headline": "Kyiv\u2019s bridges hit in Russia\u2019s biggest barrage of the month",
        "deck": "400+ drones, 110 missiles overnight; nine killed, 28 hurt. Three Dnipro bridges hit.",
        "accent": RED,
    },
    {
        "kicker": "INDIA \u00b7 WEATHER",
        "art": "cyclone",
        "headline": "Cyclone Akvan comes ashore on India\u2019s east coast",
        "deck": "Landfall near Gopalpur at 8:30am with winds of 70\u201380 km/h. Heavy rain lashes Odisha and Andhra Pradesh.",
        "accent": TEAL,
    },
    {
        "kicker": "MARKETS \u00b7 ASIA",
        "art": "markets",
        "headline": "Asia\u2019s AI sell-off deepens into a rout",
        "deck": "Nikkei \u22124.8%, Kospi \u22125.2%, Taiex \u22126.8%. Even Anthropic\u2019s record $81bn IPO cannot stop the slide.",
        "accent": BLUE,
    },
]

CARDS = [
    ("CLIMATE \u00b7 ANTALYA", "COP31 slips into overtime",
     "Draft drops fossil-fuel words and a $120bn finance target."),
    ("EUROPE \u00b7 BRUSSELS", "UK and EU seal a reset deal",
     "Food trade eased, 100,000 youth visas a year, carbon link 2028."),
    ("DIPLOMACY \u00b7 SHENZHEN", "Trump, Xi and Putin meet",
     "First-ever trilateral, 90 minutes at APEC; a nuclear war \u201ccannot be won\u201d."),
    ("JUSTICE \u00b7 THE HAGUE", "Myanmar guilty of genocide",
     "First state ever held responsible; reparations ordered for Rohingya."),
    ("CULTURE \u00b7 GAMES", "$3.79bn in a day for GTA VI",
     "32.5m copies pre-sold; Metacritic 99. Biggest launch in history."),
    ("AMERICAS \u00b7 PERU", "M6.9 quake shakes the Andes",
     "Tremor near Jun\u00edn at 7:09pm, felt in Lima; no casualties reported."),
    ("MIDDLE EAST \u00b7 RIYADH", "Houthi missile hits Riyadh tower",
     "Tallest tower struck; defences intercept more missiles."),
    ("MARKETS \u00b7 NEW YORK", "Wall Street slides with tech",
     "Nasdaq \u22122.3%; tech ETF in bear market, 20% off October peak."),
    ("AMERICAS \u00b7 NEW YORK", "Rikers Island to close by 2032",
     "Plan to shut the jail complex \u2014 five years past the legal deadline."),
    ("UKRAINE \u00b7 KRYVYI RIH", "Evening strike kills two",
     "Ballistic strike on city centre kills a child and a paramedic."),
    ("SCIENCE \u00b7 MATHS", "A proof, with AI\u2019s help",
     "A mathematician says Claude helped prove it; verification to come."),
    ("AFRICA \u00b7 SOUTH AFRICA", "Mlambo-Ngcuka dies at 71",
     "First woman deputy president and ex-UN Women chief, aged 71."),
]

TIMELINE = [
    ("OVERNIGHT", "Russia\u2019s barrage hits Kyiv\u2019s bridges."),
    ("08:30 IST", "Cyclone Akvan lands near Gopalpur."),
    ("MORNING", "Nikkei \u22124.8%, Kospi \u22125.2%, Taiex \u22126.8%."),
    ("AFTERNOON", "COP31 talks spill into overtime."),
    ("EVENING", "M6.9 quake in Peru; UK\u2013EU deal sealed."),
]

BRIEF = [
    "Egypt\u2013IMF final review agreed on $8bn programme.",
    "Miami jury convicts Sanon over Haiti murder plot.",
    "Denmark approves Arctic pact with Greenland, US.",
    "Knesset elects Matan Kahana speaker, 66\u201352.",
    "Quad backs US-led AI supply-chain pact.",
    "Cell study: gene variant aids mosquito mating.",
    "Ukraine drones reportedly hit Russian chemical plant.",
    "M4.2 quake wakes Los Angeles; no injuries.",
    "Germany rejects any new \u2018Yalta\u2019 deal over Europe.",
]

# Schematic world map: (label, number, x, y) in panel coordinates 0..1,
# plus rough continent blobs as (cx, cy, rx, ry, tilt_deg).
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
    "1 Kyiv  \u00b7  2 Antalya  \u00b7  3 Brussels  \u00b7  4 Shenzhen  \u00b7  5 Gopalpur  \u00b7  6 Riyadh",
    "7 Lima  \u00b7  8 The Hague  \u00b7  9 New York  \u00b7  10 Pretoria  \u00b7  11 Cairo  \u00b7  12 Canberra",
]

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
    d.text((x + 0.76 * w, y + 0.40 * h), "GOPALPUR", font=font("sans_b", 10),
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
    d.text((x + 10, y + 8), "NIKKEI \u22124.8%", font=font("sans_b", 12), fill=RED_DARK)
    d.text((x + w - 108, y + 8), "TAIEX \u22126.8%", font=font("sans_b", 12), fill=RED_DARK)
    d.text((x + 10, y + h - 26), "KOSPI \u22125.2%", font=font("sans_b", 12), fill=RED_DARK)
    d.rectangle([x, y, x + w, y + h], outline=(26, 26, 26), width=1)


ART = {"kyiv": art_kyiv, "cyclone": art_cyclone, "markets": art_markets}


# ---------------------------------------------------------------- sections
def section_rule(d, x, y, w, label):
    f = font("sans_b", 11)
    d.text((x, y), label, font=f, fill=INK)
    tw = d.textlength(label, font=f)
    d.line([x + tw + 8, y + 7, x + w, y + 7], fill=RULE, width=1)


def draw_masthead(d):
    d.rectangle([0, 0, W, H], fill=PAPER)
    # top hairlines
    d.line([24, 12, W - 24, 12], fill=RULE, width=2)
    d.line([24, 16, W - 24, 16], fill=RULE, width=1)
    f_small = font("sans", 11)
    d.text((24, 22), "VOL. I \u2014 No. 325", font=f_small, fill=INK_SOFT)
    d.text((W - 24 - d.textlength("ONE DAY \u00b7 ONE PAGE \u00b7 THE WHOLE WORLD", font=f_small), 22),
           "ONE DAY \u00b7 ONE PAGE \u00b7 THE WHOLE WORLD", font=f_small, fill=INK_SOFT)
    f_title = font("serif_b", 56)
    t = MASTHEAD_TITLE
    d.text(((W - d.textlength(t, font=f_title)) / 2, 36), t, font=f_title, fill=INK)
    # dateline bar
    d.rectangle([24, 102, W - 24, 130], fill=INK)
    f_date = font("sans_b", 15)
    d.text((36, 109), DATE_LINE, font=f_date, fill=WHITE)
    cw = d.textlength(COUNT_LINE, font=f_date)
    d.text((W - 36 - cw, 109), COUNT_LINE, font=f_date, fill=WHITE)


def draw_stats(d):
    y0, y1, x0 = 140, 186, 24
    w = (W - 48 - 3 * 10) / 4
    f_big = font("sans_b", 20)
    f_lab = font("sans", 11)
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
    f_kick = font("sans_b", 10)
    d.text((x, yy), lead["kicker"], font=f_kick, fill=lead["accent"])
    yy += 15
    d.line([x, yy, x + w, yy], fill=GREY_LINE, width=1)
    yy += 6
    f_head = font("serif_b", 21)
    _, used = draw_wrapped(d, x, yy, lead["headline"], f_head, w, max_lines=2,
                           line_h=25)
    yy += used + 4
    f_deck = font("sans", 12)
    draw_wrapped(d, x, yy, lead["deck"], f_deck, w, max_lines=2, line_h=15)


def draw_card(d, x, y, w, h, kicker, headline, deck, idx):
    d.rectangle([x, y, x + w, y + h], outline=GREY_LINE, width=1, fill=CREAM)
    d.rectangle([x, y, x + 4, y + h], fill=RED if idx % 3 == 0 else
                (BLUE if idx % 3 == 1 else TEAL))
    tx = x + 12
    f_kick = font("sans_b", 9)
    d.text((tx, y + 7), kicker, font=f_kick, fill=INK_SOFT)
    f_head = font("serif_b", 13)
    _, used = draw_wrapped(d, tx, y + 22, headline, f_head, w - 22,
                           max_lines=2, line_h=16)
    f_deck = font("sans", 11)
    draw_wrapped(d, tx, y + 22 + used + 2, deck, f_deck, w - 22,
                 fill=INK_SOFT, max_lines=2, line_h=13)


def draw_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], outline=GREY_LINE, width=1, fill=MAP_SEA)
    section_rule(d, x + 10, y + 8, w - 20, "THE WORLD AT A GLANCE \u2014 SCHEMATIC MAP")
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
    f_dot = font("sans_b", 9)
    for label, px, py in MAP_POINTS:
        num, name = label.split(" ", 1)
        dx, dy = x + px * w, my + py * mh
        d.ellipse([dx - 8, dy - 8, dx + 8, dy + 8], fill=RED, outline=WHITE, width=1)
        tw = d.textlength(num, font=f_dot)
        d.text((dx - tw / 2, dy - 6), num, font=f_dot, fill=WHITE)
    # legend
    ly = my + mh + 8
    f_leg = font("sans", 10)
    for i, line in enumerate(MAP_LEGEND):
        d.text((x + 10, ly + i * 13), line, font=f_leg, fill=INK_SOFT)


def draw_right(d, x, y, w):
    section_rule(d, x, y, w, "THE DAY IN ORDER")
    yy = y + 24
    f_t = font("sans_b", 11)
    f_b = font("sans", 11)
    for when, what in TIMELINE:
        d.text((x, yy), when, font=f_t, fill=RED_DARK)
        d.text((x + 82, yy), what, font=f_b, fill=INK)
        yy += 22
    return yy


def draw_brief_strip(d, x, y, w):
    section_rule(d, x, y, w, "IN BRIEF")
    yy = y + 20
    f_br = font("sans", 11)
    col_w = (w - 2 * 16) / 3
    for i, item in enumerate(BRIEF):
        cx = x + (i % 3) * (col_w + 16)
        cy = yy + (i // 3) * 15
        d.text((cx, cy), "\u25aa ", font=f_br, fill=RED)
        d.text((cx + 12, cy), item, font=f_br, fill=INK_SOFT)


def draw_footer(d):
    f = font("sans", 9)
    line = ("All stories reported on Friday 20 November 2026 \u00b7 Figures as reported by "
            "Reuters, AP, BBC, CNN, IMD, the UN and ISW \u00b7 THE WORLD IN ONE PAGE")
    d.text(((W - d.textlength(line, font=f)) / 2, H - 12), line, font=f,
           fill=INK_SOFT)


# ---------------------------------------------------------------- assemble
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
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
    return img


def main():
    img = build()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)


if __name__ == "__main__":
    main()
