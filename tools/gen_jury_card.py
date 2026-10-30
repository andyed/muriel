"""
Jury social cards: muriel's six-juror jury, judging muriel's own logo card.

Output (assets/social/):
    jury-1600x900.svg / .png    X in-stream 16:9; also posts to Bluesky and
                                LinkedIn. Content stays inside the 1600x838
                                centre band, so a 1.91:1 crop loses nothing.
    jury-1080x1350.svg / .png   Instagram portrait 4:5
    jury-lens/                  the computed juror views both SVGs reference

Sizes come from plugins/muriel/skills/compose/channels/dimensions.md.

Exhibit A is assets/logo-dark.png. Each juror view is that card pushed
through the lens that juror really uses (references/jury.md, "The roster"),
not a drawing of the lens:

    Squinter   muriel.squint `heavy` level
    Thumbnail  muriel.squint `eighth` and `px16` companions, shown at 1:1
    Stranger   the sharp card; it is the only juror that sees all of it, once
    Forger     the counterfeit the Forger built in case jc-1024-x7
    Pedant     a tally of the card's source strings, nothing else
    Loupe      a 4x nearest-neighbour crop of the bar 3 / bar 4 joint

The jurors themselves are the logo's six bars, at the logo's measured
geometry, with eyes. The card's copy quotes numbers measured here (the
joint offset, the string tally) rather than typing them in.

Usage:
    python3 tools/gen_jury_card.py          # SVG + PNG (needs rsvg-convert)
    python3 tools/gen_jury_card.py --svg    # SVG only
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageFont

ROOT = Path(__file__).resolve().parents[1]
EXHIBIT = ROOT / "assets" / "social" / "jury-lens" / "exhibit-a-jc-1024-x7.png"
OUT = ROOT / "assets" / "social"
LENS = OUT / "jury-lens"

# Palette: the logo's dark pair plus the site's cyan accent. Ratios against
# BG are checked by `python -m muriel.contrast` on the emitted SVGs.
BG = "#1F1A14"      # logo-dark paper
MARK = "#E0D4BC"    # logo-dark bars
INK = "#E8E2D0"     # cream text, 13.3:1
MUTED = "#C8BFAA"   # secondary text, 9.5:1 (logo ink_soft #A89E88 is 6.5:1)
ACCENT = "#7DD4E4"  # site accent cyan, 10.2:1
DIM = "#706655"     # unhighlighted locator bars, 3.1:1 (WCAG 1.4.11 graphic floor)
RULE = "#4A4236"    # view frames (graphic only)

SANS = "'Helvetica Neue', Helvetica, Arial, sans-serif"
LOGO_SANS = "Helvetica, 'Helvetica Neue', Arial, sans-serif"
MONO = "Menlo, 'SF Mono', ui-monospace, monospace"

HN = "/System/Library/Fonts/HelveticaNeue.ttc"
HN_INDEX = {500: 10, 700: 1}  # Medium, Bold


# ── measurement ──────────────────────────────────────────────────────────

_font_cache: dict[tuple[int, int], ImageFont.FreeTypeFont] = {}


def text_w(s: str, px: int, weight: int = 500) -> float:
    """Advance width of s in Helvetica Neue, so wrapping is measured, not guessed."""
    key = (px, weight)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(HN, px, index=HN_INDEX[weight])
    return _font_cache[key].getlength(s)


def wrap(s: str, px: int, max_w: float, weight: int = 500) -> list[str]:
    lines, cur = [], ""
    # Split on plain spaces only: a no-break space (U+00A0) holds "bar 3" together.
    for word in s.split(" "):
        trial = f"{cur} {word}".strip()
        # 4% slack: rsvg's Pango layout runs slightly wider than PIL's advances
        if cur and text_w(trial, px, weight) * 1.04 > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


@dataclass
class Bar:
    x: int
    y: int
    w: int
    h: int

    @property
    def bottom(self) -> int:
        return self.y + self.h - 1

    @property
    def right(self) -> int:
        return self.x + self.w - 1


def measure_bars(img: Image.Image) -> list[Bar]:
    """Find the six logo bars by scanning one row that crosses all of them."""
    rgb = img.convert("RGB")
    W = rgb.width
    bg = rgb.getpixel((5, 5))

    def on(x, y):
        return sum(abs(a - b) for a, b in zip(rgb.getpixel((x, y)), bg)) > 60

    row = 260  # inside every bar of the 1200x630 card
    spans, start = [], None
    for x in range(W):
        if on(x, row) and start is None:
            start = x
        elif not on(x, row) and start is not None:
            spans.append((start, x - 1))
            start = None
    bars = []
    for s, e in spans:
        xc = (s + e) // 2
        ys = [y for y in range(400) if on(xc, y)]
        bars.append(Bar(s, min(ys), e - s + 1, max(ys) - min(ys) + 1))
    if len(bars) != 6:
        raise SystemExit(f"expected 6 bars in {EXHIBIT.name}, found {len(bars)}")
    return bars


# Exhibit A's text, as render_captured_frame.py draws it (examples/logos/).
EXHIBIT_STRINGS = [
    "muriel",
    "scriptable visual production toolkit",
    "for researcher-designer-engineers",
    "after muriel cooper · live constraint system",
]


def tally_strings(strings: list[str]) -> dict[str, int]:
    nums = [m for s in strings for m in re.findall(r"\d+(?:\.\d+)?", s)]
    units = [m for s in strings for m in re.findall(r"\d+(?:\.\d+)?\s*(?:px|ms|%|s|pt)\b", s)]
    return {"strings": len(strings), "numbers": len(nums), "units": len(units)}


# ── lens views ───────────────────────────────────────────────────────────

def run_squint(src: Path, out_dir: Path) -> dict[str, Path]:
    subprocess.run(
        [sys.executable, "-m", "muriel.squint", str(src), "--out-dir", str(out_dir)],
        check=True, cwd=ROOT, capture_output=True,
    )
    stem = src.stem
    return {
        "heavy": out_dir / f"{stem}.squint-heavy.png",
        "eighth": out_dir / f"{stem}.thumb-eighth.png",
        "px16": out_dir / f"{stem}.thumb-16px.png",
    }


def loupe_crop(img: Image.Image, bars: list[Bar], w: int, h: int, path: Path) -> tuple[int, int]:
    """4x nearest-neighbour crop over the bar 3 / bar 4 joint, sized to fill
    a w x h view exactly. Returns the crop origin in ship pixels."""
    cw, ch = w // 4, h // 4
    b3 = bars[2]
    x0 = b3.right - int(cw * 0.5) + 4
    # Bars fill the top ~30% only: a mostly-cream tile outshone the jury
    # box at heavy blur (Squinter, jc-1024-q3 sq-1/sq-2).
    y0 = b3.bottom - int(ch * 0.30)
    crop = img.convert("RGB").crop((x0, y0, x0 + cw, y0 + ch))
    crop.resize((cw * 4, ch * 4), Image.NEAREST).save(path)
    return x0, y0


def fit(src: Path, w: int, h: int, path: Path) -> None:
    Image.open(src).convert("RGB").resize((w, h), Image.LANCZOS).save(path)


# ── seats ────────────────────────────────────────────────────────────────

# The case the card quotes: five jurors on Exhibit A, sealed, each run as its
# own subagent. Ballots are kept verbatim in assets/social/jury-sittings.md.
SITTING = "jc-1024-x7"


@dataclass
class Seat:
    key: str
    name: str
    bar: int        # index of the logo bar this juror stands in
    lens: str
    quote: str      # verbatim from the juror's ballot, or the Loupe's sat-out note
    recused: str    # first entries of the juror's own Recused line, in plain words


def seats(joint_px: int) -> list[Seat]:
    # Logo order, left to right, so each card sits under its juror's bar.
    nb = "\u00a0"
    return [
        Seat("squinter", "Squinter", 0, "sees: a heavy blur",
             "“At mid-distance the mark reads as two blocks, a bowtie.”",
             "Won’t judge: typography"),
        Seat("stranger", "Stranger", 1, "sees: one look, no brief",
             "“I could not work out what ‘live constraint system’ means.”",
             "Won’t judge: craft, hierarchy"),
        Seat("pedant", "Pedant", 2, "sees: the text only",
             "“The only state word on the canvas is ‘live’.”",
             "Won’t judge: composition"),
        Seat("thumbnail", "Thumbnail", 3, "sees: 1/8 scale, 16 px wide",
             "“Mark plus wordmark read as one T-shaped blob.”",
             "Won’t judge: full-size layout"),
        Seat("forger", "Forger", 4, "sees: its own counterfeit",
             "“All distinctiveness sits in one element.”",
             "Won’t judge: hierarchy"),
        Seat("loupe", "Loupe", 5, "sees: 4× crops only",
             f"Sat this case out (five jurors max). Up close, the Thumbnail stands {joint_px}{nb}px below the Pedant.",
             "Won’t judge: empty space"),
    ]


# ── SVG primitives ───────────────────────────────────────────────────────

def t(x, y, s, px, fill, weight=500, family=SANS, anchor="start", ls=None) -> str:
    extra = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{px}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>'
            f"{escape(s)}</text>")


def rect(x, y, w, h, fill, stroke=None, rx=0) -> str:
    st = f' stroke="{stroke}" stroke-width="1"' if stroke else ""
    r = f' rx="{rx}"' if rx else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"{st}{r}/>'


def image(href, x, y, w, h, pixelated=False) -> str:
    style = ' style="image-rendering:pixelated"' if pixelated else ""
    return (f'<image href="{href}" x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" '
            f'preserveAspectRatio="none"{style}/>')


def juror(bar: Bar, i: int, ox: float, oy: float, s: float, origin: tuple[int, int],
          boost: float = 1.0) -> str:
    """One logo bar with a face. Coordinates are logo ship pixels mapped by
    (ox, oy, s); no SVG transforms, so the contrast audit sees real geometry.

    boost enlarges the face, not the bar: the portrait's grid tile shrinks
    the card ~8x, and 1x eyes fall to single grey pixels there."""
    lx, ly = origin
    cx = bar.x + bar.w / 2
    spread = 1 + (boost - 1) * 0.3  # features grow faster than they spread,
                                    # so boosted eyes stay inside narrow bars

    def X(dx):          # face x offset from the bar centre
        return ox + (cx + dx * spread - lx) * s

    def Y(dy):          # face y offset from the bar top
        return oy + (bar.y + dy * spread - ly) * s

    def F(v):           # face feature size
        return v * s * boost

    parts = [rect(ox + (bar.x - lx) * s, oy + (bar.y - ly) * s, bar.w * s, bar.h * s, MARK)]
    eye = BG
    if i == 0:  # Squinter: two narrowed slits under strained brows
        for dx in (-26, 26):
            parts.append(f'<ellipse cx="{X(dx):.1f}" cy="{Y(58):.1f}" '
                         f'rx="{F(15):.1f}" ry="{F(2.6):.1f}" fill="{eye}"/>')
            sx = -1 if dx < 0 else 1
            parts.append(f'<line x1="{X(dx - 16 * sx):.1f}" y1="{Y(40):.1f}" '
                         f'x2="{X(dx + 14 * sx):.1f}" y2="{Y(47):.1f}" '
                         f'stroke="{eye}" stroke-width="{F(5):.1f}" stroke-linecap="round"/>')
    elif i == 1:  # Stranger: eyes on the exit
        for dx in (-17, 17):
            parts.append(f'<circle cx="{X(dx):.1f}" cy="{Y(44):.1f}" r="{F(10):.1f}" '
                         f'fill="none" stroke="{eye}" stroke-width="{F(3):.1f}"/>')
            parts.append(f'<circle cx="{X(dx + 5):.1f}" cy="{Y(44):.1f}" '
                         f'r="{F(4.5):.1f}" fill="{eye}"/>')
    elif i == 2:  # Pedant: reading glasses, eyes down
        for dx in (-15, 15):
            parts.append(f'<circle cx="{X(dx):.1f}" cy="{Y(30):.1f}" r="{F(11):.1f}" '
                         f'fill="none" stroke="{eye}" stroke-width="{F(3.2):.1f}"/>')
            parts.append(f'<circle cx="{X(dx):.1f}" cy="{Y(36):.1f}" '
                         f'r="{F(3.5):.1f}" fill="{eye}"/>')
        parts.append(f'<line x1="{X(-4):.1f}" y1="{Y(28):.1f}" x2="{X(4):.1f}" '
                     f'y2="{Y(28):.1f}" stroke="{eye}" stroke-width="{F(3):.1f}"/>')
    elif i == 3:  # Thumbnail: eyes at 16 px
        for dx in (-6, 6):
            parts.append(f'<circle cx="{X(dx):.1f}" cy="{Y(24):.1f}" '
                         f'r="{F(1.8):.1f}" fill="{eye}"/>')
    elif i == 4:  # Forger: domino mask, eyes sliding sideways
        parts.append(rect(ox + (bar.x + 3 - lx) * s, Y(45) - F(11), (bar.w - 6) * s, F(22),
                          eye, rx=F(10)))
        for dx in (-17, 17):
            parts.append(f'<ellipse cx="{X(dx):.1f}" cy="{Y(45):.1f}" '
                         f'rx="{F(8):.1f}" ry="{F(5):.1f}" fill="{MARK}"/>')
            parts.append(f'<circle cx="{X(dx - 4):.1f}" cy="{Y(45):.1f}" '
                         f'r="{F(3):.1f}" fill="{eye}"/>')
    elif i == 5:  # Loupe: one eye behind a jeweller's loupe
        parts.append(f'<line x1="{X(14):.1f}" y1="{Y(62):.1f}" x2="{X(34):.1f}" '
                     f'y2="{Y(90):.1f}" stroke="{ACCENT}" stroke-width="{F(7):.1f}" '
                     f'stroke-linecap="round"/>')
        parts.append(f'<circle cx="{X(0):.1f}" cy="{Y(46):.1f}" r="{F(21):.1f}" fill="{MARK}" '
                     f'stroke="{ACCENT}" stroke-width="{F(5):.1f}"/>')
        parts.append(f'<circle cx="{X(0):.1f}" cy="{Y(46):.1f}" r="{F(10):.1f}" fill="{eye}"/>')
        parts.append(f'<circle cx="{X(3):.1f}" cy="{Y(43):.1f}" r="{F(3):.1f}" fill="{MARK}"/>')
    return "\n".join(parts)


def jury_box(bars, ox, oy, s, wordmark_px=None, boost=1.0) -> str:
    """The logo with eyes: six jurors on the bench rule, wordmark beneath."""
    lx, ly = min(b.x for b in bars), min(b.y for b in bars)
    out = [juror(b, i, ox, oy, s, (lx, ly), boost) for i, b in enumerate(bars)]
    # The logo's rule (y=410, x 400..800 on the 1200 card) and wordmark (baseline 490).
    out.append(rect(ox + (400 - lx) * s, oy + (409 - ly) * s, 400 * s, 2 * s, MARK))
    if wordmark_px:
        cx = ox + (600 - lx) * s
        out.append(t(cx, oy + (490 - ly) * s, "muriel", wordmark_px, INK, 700, LOGO_SANS, "middle"))
    return "\n".join(out)


def locator(bars, highlight, x, y_base, s) -> str:
    """A tiny logo with this seat's bar lit, so a card maps back to its juror."""
    lx = min(b.x for b in bars)
    base = 313  # the logo baseline every bar but bar 1 stands on
    out = []
    for i, b in enumerate(bars):
        out.append(rect(x + (b.x - lx) * s, y_base - (base - b.y + 1) * s, b.w * s, b.h * s,
                        ACCENT if i == highlight else DIM))
    return "\n".join(out)


# ── views ────────────────────────────────────────────────────────────────

def view(seat: Seat, x, y, w, h, fmt: str, ctx: dict) -> str:
    out = [rect(x, y, w, h, BG)]
    k = seat.key
    if k == "squinter":
        out.append(image(f"jury-lens/squinter-{fmt}.png", x, y, w, h))
    elif k == "stranger":
        out.append(image(f"jury-lens/exhibit-a-{fmt}.png", x, y, w, h))
        # The brief, sent back unread: its tab sits on the card's empty top edge.
        label = "brief: returned unopened"
        lw = text_w(label, 16) * 1.04 + 16
        out.append(rect(x + w - lw - 6, y + 6, lw, 26, BG, ACCENT, rx=3))
        out.append(t(x + w - lw / 2 - 6, y + 24, label, 16, ACCENT, 500, SANS, "middle"))
    elif k == "pedant":
        tally = ctx["tally"]
        rows = [("strings", tally["strings"]), ("numbers", tally["numbers"]), ("units", tally["units"])]
        lh = (h - 20) / 4
        out.append(t(x + 14, y + 10 + lh * 0.8, "# source strings", 16, MUTED, 500, MONO))
        for j, (name, n) in enumerate(rows):
            yy = y + 10 + lh * (j + 1.8)
            out.append(t(x + 14, yy, name, 18, INK, 500, MONO))
            out.append(t(x + w - 18, yy, str(n), 18, ACCENT, 700, MONO, "end"))
    elif k == "thumbnail":
        e = ctx["eighth_size"]
        ex, ey = x + 12, y + (h - e[1] - 24) / 2
        out.append(image("jury-lens/thumbnail-eighth.png", round(ex), round(ey), e[0], e[1], True))
        out.append(t(ex, ey + e[1] + 20, "1/8", 16, MUTED))
        px = round(x + w - 16 - 22)
        py = round(ey + e[1] / 2 - 4)
        out.append(image("jury-lens/thumbnail-16px.png", px, py, 16, 8, True))
        out.append(t(x + w - 12, ey + e[1] + 20, "16 px", 16, MUTED, 500, SANS, "end"))
    elif k == "forger":
        out.append(image(f"jury-lens/forger-{fmt}.png", x, y, w, h))
        # Top-left: the counterfeit, like the original, is empty above its mark.
        label = "its counterfeit"
        lw = text_w(label, 16) * 1.04 + 16
        out.append(rect(x + 6, y + 6, lw, 26, BG, INK, rx=3))
        out.append(t(x + 6 + lw / 2, y + 24, label, 16, INK, 500, SANS, "middle"))
    elif k == "loupe":
        out.append(image(f"jury-lens/loupe-{fmt}.png", x, y, w, h, True))
        ox, oy = ctx["loupe_origin"][fmt]
        b3, b4 = ctx["bars"][2], ctx["bars"][3]
        yb3 = y + (b3.bottom + 1 - oy) * 4
        yb4 = y + (b4.bottom + 1 - oy) * 4
        gx = x + (b4.x - ox) * 4 - 16  # in the gap between the bars
        out.append(f'<line x1="{gx:.1f}" y1="{yb3:.1f}" x2="{gx:.1f}" y2="{yb4:.1f}" '
                   f'stroke="{ACCENT}" stroke-width="2"/>')
        for yy in (yb3, yb4):
            out.append(f'<line x1="{gx - 6:.1f}" y1="{yy:.1f}" x2="{gx + 6:.1f}" y2="{yy:.1f}" '
                       f'stroke="{ACCENT}" stroke-width="2"/>')
        label = f"{ctx['joint_px']} px at 1×"
        lw = text_w(label, 16) * 1.04 + 12
        ly = max(yb4 + 6, y + h - 30)
        out.append(rect(gx - lw / 2, ly, lw, 24, BG, rx=3))
        out.append(t(gx, ly + 17, label, 16, ACCENT, 700, SANS, "middle"))
    out.append(rect(x, y, w, h, "none", RULE))
    return "\n".join(out)


def card_text(seat: Seat, x, y, w, bars, name_px, body_px, small_px,
              quote_lines: int, lens_px: int) -> tuple[str, float]:
    """Landscape card: name with its locator logo, the lens, the quote, the
    recusal. quote_lines reserves the row's tallest quote, so every card's
    recusal sits on one baseline."""
    out = []
    out.append(t(x, y + name_px * 0.8, seat.name, name_px, INK, 700))
    s = 0.105
    out.append(locator(bars, seat.bar, x + w - 509 * s, y + name_px * 0.8, s))
    yy = y + name_px * 0.8 + body_px * 1.45
    out.append(t(x, yy, seat.lens, lens_px, ACCENT, 500))
    yy += body_px * 0.5
    y_q = yy
    for line in wrap(seat.quote, body_px, w):
        yy += body_px * 1.28
        out.append(t(x, yy, line, body_px, INK, 500))
    yy = y_q + quote_lines * body_px * 1.28 + small_px * 1.6
    out.append(t(x, yy, seat.recused, small_px, MUTED, 500))
    return "\n".join(out), yy


def row_text(seat: Seat, x, y, w, bars, name_px, body_px) -> tuple[str, float]:
    """Portrait row: name and lens on one line, the quote under them. No
    recusal: at Instagram feed width the card's type has to stay large."""
    out = []
    base = y + name_px * 0.8
    out.append(t(x, base, seat.name, name_px, INK, 700))
    lx = x + text_w(seat.name, name_px, 700) * 1.04 + 16
    out.append(t(lx, base, seat.lens, body_px - 2, ACCENT, 500))
    s = 0.1
    out.append(locator(bars, seat.bar, x + w - 509 * s, base, s))
    yy = base + 6
    for line in wrap(seat.quote, body_px, w):
        yy += body_px * 1.3
        out.append(t(x, yy, line, body_px, INK, 500))
    return "\n".join(out), yy


def max_lines(seats_: list[Seat], attr: str, px: int, w: float) -> int:
    return max(len(wrap(getattr(s, attr), px, w)) for s in seats_)


# ── copy ─────────────────────────────────────────────────────────────────

DOCKET = f"muriel jury · case {SITTING} · 5 of 6 jurors · ballots sealed"
DOCKET_SHORT = f"muriel jury · case {SITTING}"
HEADLINE = "Every juror is missing something on purpose."
SUBHEAD = ("Six AI jurors, drawn as the six bars of muriel’s logo. Each sees "
           "through one lens and is denied the rest, so their blind spots differ.")
MECHANICS = ("Ballots stay sealed until the last one is in. Each juror sees the options "
             "in its own order, shuffled by shasum(case + juror). The chair doesn’t vote: "
             "it opens every ballot at once and keeps the worst finding.")
ROW_LABEL = "Exhibit A, muriel’s logo card, as each juror saw it. Quotes are from their ballots."
VERDICT = ("Measured before the jury met: Exhibit A’s second tagline is 6.5:1, under "
           "the 8:1 floor. Worst juror finding: the Pedant’s, rated HIGH.")


def svg_open(W, H, title) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f"<title>{escape(title)}</title>",
        f'<desc>{escape(SUBHEAD)} Generated by tools/gen_jury_card.py.</desc>',
        rect(0, 0, W, H, BG),
    ]


def landscape(ctx) -> str:
    W, H, M = 1600, 900, 64
    bars, sts = ctx["bars"], ctx["seats"]
    out = svg_open(W, H, "muriel's jury")
    # Left column: docket line, headline, subhead, mechanics, stipulated fact.
    col = 790
    out.append(t(M, 88, DOCKET, 18, ACCENT, 500, MONO))
    y = 88
    for line in wrap(HEADLINE, 60, col, 700):
        y += 68
        out.append(t(M, y, line, 60, INK, 700))
    y += 18
    for line in wrap(SUBHEAD, 24, col):
        y += 34
        out.append(t(M, y, line, 24, INK, 500))
    y += 10
    for line in wrap(MECHANICS, 18, col):
        y += 26
        out.append(t(M, y, line, 18, MUTED, 500))
    # The stipulated fact comes before the cards, as it comes before seating.
    y += 8
    for line in wrap(VERDICT, 18, col):
        y += 26
        out.append(t(M, y, line, 18, ACCENT, 500))
    ctx["left_column_end"] = y  # must stay above the row label at y 524
    # Right: the jury box, which is also the logo. The loupe handle reaches
    # ~40 px past bar 6, so the box sits that far inside the margin.
    s = 0.82
    out.append(jury_box(bars, W - M - 40 - 509 * s, 70, s, wordmark_px=round(76 * s)))
    # Cards: one row in logo order, each under its juror's position.
    n, gap = 6, 20
    cw = (W - 2 * M - gap * (n - 1)) / n          # 228
    vw, vh = int(cw), 120
    vy = 540
    out.append(t(M, vy - 16, ROW_LABEL, 18, MUTED, 500))
    q_n = max_lines(sts, "quote", 19, cw)
    bottom = 0
    for i, seat in enumerate(sts):
        x = M + i * (cw + gap)
        out.append(view(seat, x, vy, vw, vh, "land", ctx))
        txt, yy = card_text(seat, x, vy + vh + 18, cw, bars, 26, 19, 16, q_n, lens_px=17)
        out.append(txt)
        bottom = max(bottom, yy)
    ctx.setdefault("bottoms", {})["land"] = bottom
    ctx.setdefault("checks", []).extend(one_line_checks(sts, 17, 16, cw, "land"))
    if ctx["left_column_end"] > vy - 40:
        ctx["checks"].append(f"land: left column runs to y {ctx['left_column_end']:.0f}, into the row label")
    out.append("</svg>")
    return "\n".join(out)


def portrait(ctx) -> str:
    W, H, M = 1080, 1350, 56
    bars, sts = ctx["bars"], ctx["seats"]
    out = svg_open(W, H, "muriel's jury")
    out.append(t(M, 84, DOCKET_SHORT, 20, ACCENT, 500, MONO))
    y = 84
    for line in wrap(HEADLINE, 58, 560, 700):
        y += 66
        out.append(t(M, y, line, 58, INK, 700))
    s, oy = 0.72, 62
    out.append(jury_box(bars, W - M - 30 - 509 * s, oy, s, wordmark_px=round(76 * s), boost=1.5))
    y = max(y, oy + (490 - 90) * s) + 24
    for line in wrap(SUBHEAD, 28, W - 2 * M):
        y += 38
        out.append(t(M, y, line, 28, INK, 500))
    # Rows: view left, name + lens + quote right. Type stays >= 26 px so it
    # reads near 10 CSS px in a 390-wide Instagram feed.
    vw, vh = 208, 108
    tx = M + vw + 24
    tw = W - M - tx
    y += 46
    out.append(t(M, y, ROW_LABEL, 22, MUTED, 500))
    y += 18
    for seat in sts:
        out.append(view(seat, M, y, vw, vh, "port", ctx))
        txt, yy = row_text(seat, tx, y - 2, tw, bars, 32, 27)
        out.append(txt)
        y = max(y + vh, yy + 10) + 10
    for line in wrap(VERDICT, 22, W - 2 * M):
        y += 30
        out.append(t(M, y, line, 22, ACCENT, 500))
    ctx.setdefault("bottoms", {})["port"] = y
    for seat in sts:
        if len(wrap(seat.quote, 27, tw)) > 2:
            ctx.setdefault("checks", []).append(f"port: {seat.key} quote runs past 2 lines")
    out.append("</svg>")
    return "\n".join(out)


def one_line_checks(sts, body_px, small_px, w, fmt) -> list[str]:
    """Lens and recusal lines must not wrap, or the card rows fall out of step."""
    bad = []
    for seat in sts:
        if len(wrap(seat.lens, body_px, w)) > 1:
            bad.append(f"{fmt}: {seat.key} lens wraps")
        if len(wrap(seat.recused, small_px, w)) > 1:
            bad.append(f"{fmt}: {seat.key} recusal wraps")
    return bad


# ── main ─────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    LENS.mkdir(parents=True, exist_ok=True)
    img = Image.open(EXHIBIT)
    bars = measure_bars(img)
    joint_px = bars[3].bottom - bars[2].bottom
    tally = tally_strings(EXHIBIT_STRINGS)

    with tempfile.TemporaryDirectory() as tmp:
        sq = run_squint(EXHIBIT, Path(tmp))
        shutil.copy(sq["eighth"], LENS / "thumbnail-eighth.png")
        shutil.copy(sq["px16"], LENS / "thumbnail-16px.png")
        heavy = Path(tmp) / "heavy.png"
        shutil.copy(sq["heavy"], heavy)
        # The Forger seat's own counterfeit from the sitting, kept as an input:
        # it was built once by the seat, so the generator does not rebuild it.
        forged = LENS / f"forger-counterfeit-{SITTING}.png"
        if not forged.exists():
            raise SystemExit(f"missing {forged}: copy it from the Forger's forgery_dir")
        views = {"land": (228, 120), "port": (208, 108)}
        loupe_origin = {}
        for fmt, (w, h) in views.items():
            fit(heavy, w, h, LENS / f"squinter-{fmt}.png")
            fit(EXHIBIT, w, h, LENS / f"exhibit-a-{fmt}.png")
            fit(forged, w, h, LENS / f"forger-{fmt}.png")
            loupe_origin[fmt] = loupe_crop(img, bars, w, h, LENS / f"loupe-{fmt}.png")

    ctx = {
        "bars": bars, "joint_px": joint_px, "tally": tally,
        "seats": seats(joint_px), "loupe_origin": loupe_origin,
        "eighth_size": Image.open(LENS / "thumbnail-eighth.png").size,
    }
    outputs = {"jury-1600x900": landscape(ctx), "jury-1080x1350": portrait(ctx)}
    for stem, svg in outputs.items():
        (OUT / f"{stem}.svg").write_text(svg + "\n")
        print(f"  → {OUT / stem}.svg")
    print(f"  bars: {[(b.x, b.y, b.w, b.h) for b in bars]}  joint offset: {joint_px} px  "
          f"tally: {tally}  text bottoms: {ctx['bottoms']}")
    for c in ctx.get("checks", []):
        print(f"  ! {c}")

    if "--svg" not in argv:
        for stem in outputs:
            subprocess.run(["rsvg-convert", "-o", str(OUT / f"{stem}.png"), str(OUT / f"{stem}.svg")],
                           check=True)
            w, h = Image.open(OUT / f"{stem}.png").size
            print(f"  → {OUT / stem}.png  {w}x{h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
