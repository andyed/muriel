"""Render a captured frame from the interactive colophon to a static PNG.

Input: JSON blob emitted by the "capture frame" button in
       output/colophon/interactive-colophon.html
Output: a 1200×630 PNG with the bars in the exact captured pose,
        plus wordmark / rule / credit matching the interactive layout.

Usage:
    python3 render_captured_frame.py <capture.json> [<capture.json> ...]
    cat capture.json | python3 render_captured_frame.py -

Output path: output/colophon/still-<palette>-t<time>.png
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent / "output" / "colophon"

# Fonts (match interactive Helvetica stack)
FONT_PATHS = [
    '/System/Library/Fonts/Helvetica.ttc',
    '/Library/Fonts/Arial Bold.ttf',
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
]


def _load_font(size, bold=True):
    for p in FONT_PATHS:
        if os.path.exists(p):
            idx = 1 if (bold and p.endswith('.ttc')) else 0
            try:
                return ImageFont.truetype(p, size, index=idx)
            except OSError:
                continue
    return ImageFont.load_default()


def _measure(font, text, draw):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


# Palette pairs: mode → {paper, mark, ink, ink_soft}. When a capture's
# palette.id matches a known key, rendering in dark mode swaps to the
# inverse-lightness pair in the same hue family.
DARK_PALETTES = {
    "graphite": {
        "paper":    "#1F1A14",
        "mark":     "#E0D4BC",
        "ink":      "#E8E2D0",
        "ink_soft": "#A89E88",
    },
}


def render(capture: dict, label: str | None = None, mode: str = "light") -> Path:
    W = capture.get("canvas", {}).get("w", 1200)
    H = capture.get("canvas", {}).get("h", 630)
    pal_id = capture["palette"]["id"]
    if mode == "dark" and pal_id in DARK_PALETTES:
        dp = DARK_PALETTES[pal_id]
        paper, mark = dp["paper"], dp["mark"]
        ink, ink_soft = dp["ink"], dp["ink_soft"]
    else:
        paper = capture["palette"]["paper"]
        mark  = capture["palette"]["mark"]
        ink, ink_soft = "#121212", "#5C5852"

    img = Image.new("RGB", (W, H), paper)
    draw = ImageDraw.Draw(img, "RGBA")

    for b in capture["bars"]:
        x = round(b["x"])
        y = round(b["y"])
        w = round(b["width"])
        h = round(b["height"])
        draw.rectangle([x, y, x + w, y + h], fill=mark)

    accent = mark

    draw.line([(400, 410), (800, 410)], fill=mark, width=2)

    wf = _load_font(76, bold=True)
    wm = "muriel"
    ww, _ = _measure(wf, wm, draw)
    draw.text(((W - ww) // 2, 490 - 72), wm, fill=ink, font=wf)

    sf1 = _load_font(22, bold=False)
    s1 = "scriptable visual production toolkit"
    sw1, _ = _measure(sf1, s1, draw)
    draw.text(((W - sw1) // 2, 532 - 22), s1, fill=ink, font=sf1)

    sf2 = _load_font(17, bold=False)
    s2 = "for researcher-designer-engineers"
    sw2, _ = _measure(sf2, s2, draw)
    draw.text(((W - sw2) // 2, 558 - 17), s2, fill=ink_soft, font=sf2)

    cf = _load_font(11, bold=False)
    credit = "after muriel cooper · live constraint system"
    draw.text((40, 612 - 11), credit, fill=accent, font=cf)

    t = capture.get("time", 0)
    palette_id = capture["palette"]["id"]
    mode_suffix = "" if mode == "light" else f"-{mode}"
    stem = label or f"still-{palette_id}-t{t:.2f}{mode_suffix}".replace(".", "_")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{stem}.png"
    img.save(out_path, "PNG")
    return out_path


def main() -> int:
    args = sys.argv[1:]
    modes = ["light"]
    if "--both" in args:
        modes = ["light", "dark"]
        args = [a for a in args if a != "--both"]
    elif "--dark" in args:
        modes = ["dark"]
        args = [a for a in args if a != "--dark"]

    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    for i, arg in enumerate(args, start=1):
        if arg == "-":
            raw = sys.stdin.read()
            data = json.loads(raw)
            for mode in modes:
                out = render(data, label=f"still-stdin-{i}" + ("" if mode == "light" else f"-{mode}"), mode=mode)
                print(f"  → {out}")
        else:
            p = Path(arg)
            data = json.loads(p.read_text())
            for mode in modes:
                out = render(data, mode=mode)
                print(f"  → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
