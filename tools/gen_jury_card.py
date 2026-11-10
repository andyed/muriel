"""
Jury social cards: an agent's first-draft dashboard, the same panel after
every juror's fix, and what each of muriel's six jurors caught.

Output (assets/social/):
    jury-1600x900.svg / .png    X in-stream 16:9; also Bluesky and LinkedIn.
                                Content stays inside the centre 1600x838, so
                                a 1.91:1 crop loses nothing.
    jury-1080x1350.svg / .png   Instagram portrait 4:5
    jury-exhibit/               both panels (HTML source and 1200 px renders)

Sizes come from plugins/muriel/skills/compose/channels/dimensions.md.

The draft panel was written the way a coding agent writes a first pass. Six
juror agents reviewed it (case jx-1024-p2), every fix they asked for went into
panel-after.html, and the same six reviewed that (case jx-1024-p3). Each catch
on the card restates a finding from a ballot, and each pin sits where the
ballot locates the problem, in the draft's own pixels. The ballots are in
assets/social/jury-case.md.

Usage:
    python3 tools/gen_jury_card.py          # SVG + PNG (needs rsvg-convert)
    python3 tools/gen_jury_card.py --svg    # SVG only

Re-render a panel PNG after editing its HTML:
    python3 -m muriel.capture file://$PWD/assets/social/jury-exhibit/panel-after.html \\
        --tiers desktop --selector '#panel' --scale 1 \\
        --dir assets/social/jury-exhibit --slug panel-after
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "social"
BEFORE = OUT / "jury-exhibit" / "panel-desktop-1200x662.png"
AFTER = OUT / "jury-exhibit" / "panel-after-desktop-1200x747.png"

# muriel's dark pair plus the site's cyan accent. Ratios on BG are checked
# by `python -m muriel.contrast` on the emitted SVGs.
BG = "#1F1A14"      # logo-dark paper
MARK = "#E0D4BC"    # logo bars
INK = "#E8E2D0"     # 13.3:1
MUTED = "#C8BFAA"   # 9.5:1
ACCENT = "#7DD4E4"  # 10.2:1; pins carry BG digits on it, also 10.2:1
FRAME = "#4A4236"   # graphic only

SANS = "'Helvetica Neue', Helvetica, Arial, sans-serif"
LOGO_SANS = "Helvetica, 'Helvetica Neue', Arial, sans-serif"
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
HN_INDEX = {500: 10, 700: 1}  # Medium, Bold

# muriel's logo bars on the 1200x630 card: (x, y, w, h).
LOGO_BARS = [(346, 159, 133, 212), (488, 159, 96, 155), (594, 199, 80, 83),
             (682, 199, 32, 86), (724, 159, 77, 155), (810, 90, 45, 224)]


@dataclass
class Finding:
    n: int
    juror: str
    catch: str      # a one-line restatement of the juror's finding
    pin: tuple      # (x, y) on the 1200x662 draft


# One catch per juror, in roster order; ids are in assets/social/jury-case.md.
FINDINGS: list[Finding] = [
    Finding(1, "Squinter", "numbers vanish when blurred", (505, 168)),        # F1
    Finding(2, "Thumbnail", "labels unreadable at preview size", (148, 128)), # t1
    Finding(3, "Stranger", "no clear main button", (1025, 22)),              # Q3 answer
    Finding(4, "Forger", "21 of 23 choices are stock", (1150, 282)),  # fg-1
    Finding(5, "Pedant", "two numbers with no unit", (716, 150)),             # P2, P3
    Finding(6, "Loupe", "26 notches at the axis", (508, 556)),                # F2
]

# "Ship (this seat's loss only)" votes, out of six, from the two cases.
SHIP_BEFORE = 1
SHIP_AFTER = 6      # case jx-1024-p4 (Squinter: jx-1024-p4s, reading order stated)

HEADLINE = "Better visual work from your coding agent."
PITCH = ("muriel gives it six AI jurors for visual and interaction work. Each sees the "
         "work differently (blurred, shrunk, one glance, text only, 4× close-ups, "
         "rebuilt from stock parts), so together they catch what one reviewer misses.")
PITCH_SHORT = ("muriel gives it six AI jurors for visual and interaction work. Each sees "
               "it differently, so together they catch what one reviewer misses.")
WHERE = "A design skill for coding agents · muriel.mindbendingpixels.com"
AFTER_LABEL = "After two rounds of fixes"


def label_before() -> str:
    return f"Before: an agent’s first draft · {SHIP_BEFORE} of 6 jurors would ship it"


def label_after() -> str:
    tail = f" · {SHIP_AFTER} of 6 would ship it" if SHIP_AFTER is not None else ""
    return f"After: every juror’s fix applied{tail}"


# ── measurement ──────────────────────────────────────────────────────────

_fonts: dict[tuple[int, int], ImageFont.FreeTypeFont] = {}


def text_w(s: str, px: int, weight: int = 500) -> float:
    if (px, weight) not in _fonts:
        _fonts[(px, weight)] = ImageFont.truetype(HN, px, index=HN_INDEX[weight])
    return _fonts[(px, weight)].getlength(s)


def wrap(s: str, px: int, max_w: float, weight: int = 500) -> list[str]:
    # Plain spaces only, so a no-break space keeps "21 of 23" together.
    lines, cur = [], ""
    for word in s.split(" "):
        trial = f"{cur} {word}".strip()
        # 4% slack: Pango sets slightly wider than PIL measures
        if cur and text_w(trial, px, weight) * 1.04 > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# ── SVG primitives ───────────────────────────────────────────────────────

def t(x, y, s, px, fill, weight=500, family=SANS, anchor="start") -> str:
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{px}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>')


def rect(x, y, w, h, fill, stroke=None, sw=1) -> str:
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"{st}/>'


def pin(cx, cy, n, r) -> str:
    """Numbered marker: BG digit on cyan, ringed in BG so it holds on the
    light panel and on the dark card alike."""
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r + 3:.1f}" fill="{BG}"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{ACCENT}"/>'
            + t(cx, cy + r * 0.42, str(n), round(r * 1.2), BG, 700, SANS, "middle"))


def brand(x, y, h) -> str:
    """The logo bars at height h, then the wordmark beside them."""
    s = h / 281
    out = [rect(x + (bx - 346) * s, y + (by - 90) * s, bw * s, bh * s, MARK)
           for bx, by, bw, bh in LOGO_BARS]
    out.append(t(x + 509 * s + 14, y + h * 0.78, "muriel", round(h * 0.82), INK, 700, LOGO_SANS))
    return "\n".join(out)


def panel(png: Path, x, y, w, pins_r=None, frame=FRAME) -> tuple[str, float]:
    """A panel render at width w; with pins_r, the six findings pinned on it."""
    iw, ih = Image.open(png).size
    scale = w / iw
    h = ih * scale
    out = [(f'<image href="jury-exhibit/{png.name}" x="{x:.1f}" y="{y:.1f}" '
            f'width="{w:.1f}" height="{h:.1f}" preserveAspectRatio="none"/>'),
           rect(x, y, w, h, "none", frame, 2 if frame == ACCENT else 1)]
    if pins_r:
        for f in FINDINGS:
            out.append(pin(x + f.pin[0] * scale, y + f.pin[1] * scale, f.n, pins_r))
    return "\n".join(out), h


def catch(f: Finding, x, y, px) -> str:
    """One legend line: pin, juror name, what it caught."""
    r = px * 0.62
    out = [pin(x + r, y - px * 0.35, f.n, r)]
    tx = x + 2 * r + 10
    out.append(t(tx, y, f.juror, px, INK, 700))
    out.append(t(tx + text_w(f.juror, px, 700) * 1.04 + 10, y, f.catch, px, INK, 500))
    return "\n".join(out)


def arrow(x0, x1, y) -> str:
    return (f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1 - 12:.1f}" y2="{y:.1f}" '
            f'stroke="{ACCENT}" stroke-width="4" stroke-linecap="round"/>'
            f'<path d="M{x1 - 18:.1f},{y - 12:.1f} L{x1:.1f},{y:.1f} L{x1 - 18:.1f},{y + 12:.1f}" '
            f'fill="none" stroke="{ACCENT}" stroke-width="4" stroke-linecap="round" '
            f'stroke-linejoin="round"/>')


def svg_open(W, H) -> list[str]:
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            "<title>muriel jury</title>",
            f"<desc>{escape(HEADLINE + ' ' + PITCH)}</desc>",
            rect(0, 0, W, H, BG)]


# ── layouts ──────────────────────────────────────────────────────────────
# Built for a phone feed: X shows the landscape near 600 px wide and Instagram
# the portrait near 390, so nothing that must be read is set under ~34 px.
# The six catches live in the reply text, numbered to match the pins.

def outcome(x, y, px, anchor="start") -> str:
    """'1 of 6 → N of 6 jurors would ship it', the card's one number."""
    after = SHIP_AFTER if SHIP_AFTER is not None else "?"
    return t(x, y, f"Jurors who would ship it: {SHIP_BEFORE} of 6 → {after} of 6",
             px, ACCENT, 700, SANS, anchor)


def landscape(ctx) -> str:
    W, H, M = 1600, 900, 64
    out = svg_open(W, H)
    out.append(brand(M, 52, 44))
    out.append(t(M, 186, HEADLINE, 62, INK, 700))
    ctx["checks"].append(("land headline width", M + text_w(HEADLINE, 62, 700) * 1.04, W - M))
    pw = 690
    gap = W - 2 * M - 2 * pw
    top = 286
    out.append(t(M, top - 18, "Before", 36, MUTED, 700))
    img, bh = panel(BEFORE, M, top, pw, pins_r=13)
    out.append(img)
    ax = M + pw
    out.append(t(ax + gap, top - 18, AFTER_LABEL, 36, ACCENT, 700))
    img, ah = panel(AFTER, ax + gap, top, pw, frame=ACCENT)
    out.append(img)
    out.append(arrow(ax + 22, ax + gap - 22, top + bh / 2))
    ly = top + max(bh, ah) + 72
    out.append(outcome(M, ly, 40))
    ctx["checks"].append(("land bottom", ly + 10, 860))
    out.append("</svg>")
    return "\n".join(out)


def portrait(ctx) -> str:
    W, H, M = 1080, 1350, 56
    out = svg_open(W, H)
    out.append(brand(M, 50, 44))
    y = 96
    for line in wrap(HEADLINE, 70, W - 2 * M, 700):
        y += 78
        out.append(t(M, y, line, 70, INK, 700))
    y += 70
    out.append(t(M, y, AFTER_LABEL, 40, ACCENT, 700))
    y += 22
    img, ah = panel(AFTER, M, y, W - 2 * M, frame=ACCENT)
    out.append(img)
    y += ah + 62
    out.append(t(M, y, "Before", 36, MUTED, 700))
    y += 20
    bw = 480
    img, bh = panel(BEFORE, M, y, bw, pins_r=10)
    out.append(img)
    # Beside the draft: what happened between the panels, and the result.
    tx = M + bw + 36
    out.append(t(tx, y + 40, "Six AI jurors.", 40, INK, 700))
    out.append(t(tx, y + 90, "Every fix applied.", 40, INK, 700))
    after = SHIP_AFTER if SHIP_AFTER is not None else "?"
    out.append(t(tx, y + 168, "Would ship it:", 36, ACCENT, 700))
    out.append(t(tx, y + 214, f"{SHIP_BEFORE} of 6 → {after} of 6", 36, ACCENT, 700))
    ctx["checks"].append(("port bottom", max(y + bh, y + 222) + 8, 1310))
    ctx["checks"].append(("port side text", tx + text_w("Every fix applied.", 40, 700) * 1.04, W - M))
    out.append("</svg>")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ctx = {"checks": []}
    outputs = {"jury-1600x900": landscape(ctx), "jury-1080x1350": portrait(ctx)}
    for stem, svg in outputs.items():
        (OUT / f"{stem}.svg").write_text(svg + "\n")
    for name, value, limit in ctx["checks"]:
        flag = "!" if value > limit else " "
        print(f" {flag} {name}: {value:.0f} (limit {limit})")
    if "--svg" not in argv:
        for stem in outputs:
            subprocess.run(["rsvg-convert", "-o", str(OUT / f"{stem}.png"),
                            str(OUT / f"{stem}.svg")], check=True)
            w, h = Image.open(OUT / f"{stem}.png").size
            print(f"  → {OUT / stem}.png  {w}x{h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
