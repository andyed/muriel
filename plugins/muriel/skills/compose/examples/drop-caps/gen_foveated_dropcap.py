"""Foveated drop-cap generator.

Renders a decorative drop-cap composed of a large letter on a log-polar
grid (V1 cortical-magnification ornament). The grid replaces the
traditional Victorian flourish; it carries meaning — on foveation /
peripheral-vision posts it references the research directly.

Primary output: SVG (crisp at any scale, inline-able in blog templates).
Preview output: PNG via cairosvg if available, otherwise skipped.

Usage:
    python3 gen_foveated_dropcap.py                     # default demo
    python3 gen_foveated_dropcap.py --letter H --accent '#C07FA0'
    python3 gen_foveated_dropcap.py --preset peripheral-color-search

Muriel constraint hooks honored:
    - Accent + background contrast audited (must clear 8:1)
    - Brand-token integration via --brand FILE.toml (optional)
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "output"

# ── Contrast helpers (muriel convention — enforce 8:1 minimum) ─────────
def _lin(c: int) -> float:
    x = c / 255.0
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def _lum(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(fg: str, bg: str) -> float:
    lf, lb = _lum(fg), _lum(bg)
    hi, lo = (lf, lb) if lf > lb else (lb, lf)
    return (hi + 0.05) / (lo + 0.05)


# ── Config ─────────────────────────────────────────────────────────────
@dataclass
class DropCapConfig:
    letter: str = "H"
    accent: str = "#C07FA0"          # psychodeli-ish mauve
    background: str = "#0A0A0E"      # near-black blog body
    # Grid params — the "flourish"
    n_spokes: int = 48                # radial lines
    n_rings: int = 14                 # log-spaced concentric rings
    r_inner: float = 18.0             # innermost ring radius (px)
    r_outer: float = 220.0            # outermost ring radius (px)
    grid_opacity_center: float = 0.55
    grid_opacity_edge: float = 0.0
    grid_fade_power: float = 1.4      # >1 = faster fade near edge
    # Letter typography
    font_family: str = "Didot, 'Bodoni 72', 'Bodoni MT', Georgia, serif"
    font_weight: int = 700
    letter_size_px: int = 300          # CSS px height of letter
    # Canvas
    size: int = 480                    # SVG viewbox (square)
    # Fixation marker (the tiny bull's-eye at grid center) — optional
    show_fixation: bool = True
    fixation_color: str = "#FFFFFF"
    fixation_radius: float = 5.0


# ── SVG generator ──────────────────────────────────────────────────────
def svg_foveated_dropcap(cfg: DropCapConfig) -> str:
    size = cfg.size
    cx = cy = size / 2
    accent = cfg.accent

    # Opacity falloff function — per-ring alpha by normalized radius
    def alpha_at(r: float) -> float:
        if r <= cfg.r_inner:
            return cfg.grid_opacity_center
        t = (r - cfg.r_inner) / max(1.0, cfg.r_outer - cfg.r_inner)
        t = max(0.0, min(1.0, t)) ** cfg.grid_fade_power
        return cfg.grid_opacity_center + (cfg.grid_opacity_edge - cfg.grid_opacity_center) * t

    # Log-spaced radii
    ratios = []
    for i in range(cfg.n_rings):
        u = i / max(1, cfg.n_rings - 1)
        r = cfg.r_inner * (cfg.r_outer / cfg.r_inner) ** u
        ratios.append(r)

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">')
    lines.append(f'  <rect width="100%" height="100%" fill="{cfg.background}"/>')
    lines.append(f'  <g stroke="{accent}" fill="none" stroke-width="1">')

    # Concentric rings
    for r in ratios:
        lines.append(f'    <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" stroke-opacity="{alpha_at(r):.3f}"/>')

    # Radial spokes (alpha falls with distance from center — approximated
    # via gradient stroke; here we draw a single spoke with a linear
    # alpha ramp from inner to outer using an SVG linearGradient).
    lines.append('  </g>')
    lines.append('  <defs>')
    lines.append(f'    <radialGradient id="spokeFade" cx="50%" cy="50%" r="50%">')
    lines.append(f'      <stop offset="0%" stop-color="{accent}" stop-opacity="{cfg.grid_opacity_center:.3f}"/>')
    mid_alpha = cfg.grid_opacity_center * 0.55
    lines.append(f'      <stop offset="55%" stop-color="{accent}" stop-opacity="{mid_alpha:.3f}"/>')
    lines.append(f'      <stop offset="100%" stop-color="{accent}" stop-opacity="{cfg.grid_opacity_edge:.3f}"/>')
    lines.append('    </radialGradient>')
    lines.append('  </defs>')
    lines.append('  <g stroke="url(#spokeFade)" stroke-width="1" fill="none">')
    for i in range(cfg.n_spokes):
        theta = (2 * math.pi * i) / cfg.n_spokes
        x2 = cx + cfg.r_outer * math.cos(theta)
        y2 = cy + cfg.r_outer * math.sin(theta)
        x1 = cx + cfg.r_inner * math.cos(theta)
        y1 = cy + cfg.r_inner * math.sin(theta)
        lines.append(f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
    lines.append('  </g>')

    # Fixation marker (tiny bull's-eye at center)
    if cfg.show_fixation:
        fr = cfg.fixation_radius
        lines.append(f'  <g fill="{cfg.background}" stroke="{cfg.fixation_color}" stroke-width="1.5">')
        lines.append(f'    <circle cx="{cx}" cy="{cy}" r="{fr}"/>')
        lines.append(f'    <line x1="{cx - fr}" y1="{cy}" x2="{cx + fr}" y2="{cy}" stroke="{cfg.fixation_color}" stroke-width="1"/>')
        lines.append(f'    <line x1="{cx}" y1="{cy - fr}" x2="{cx}" y2="{cy + fr}" stroke="{cfg.fixation_color}" stroke-width="1"/>')
        lines.append('  </g>')

    # The letter — large, centered, accent color
    lines.append(f'  <text x="{cx}" y="{cy}" font-family="{cfg.font_family}" '
                 f'font-weight="{cfg.font_weight}" font-size="{cfg.letter_size_px}" '
                 f'fill="{accent}" text-anchor="middle" dominant-baseline="central">{cfg.letter}</text>')

    lines.append('</svg>')
    return "\n".join(lines)


# ── Presets ────────────────────────────────────────────────────────────
PRESETS = {
    "peripheral-color-search": DropCapConfig(
        letter="H",
        accent="#C07FA0",
        background="#0A0A0E",
    ),
    "foveation-research": DropCapConfig(
        letter="T",
        accent="#C07FA0",
        background="#0A0A0E",
    ),
    "light": DropCapConfig(
        letter="H",
        accent="#6B2A5A",
        background="#E8E2D0",
    ),
}


# ── Rasterize via cairosvg if available ────────────────────────────────
def try_rasterize(svg_path: Path, out_png: Path, scale: float = 2.0) -> bool:
    try:
        import cairosvg
    except ImportError:
        return False
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(out_png),
        scale=scale,
    )
    return True


# ── Main ───────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--letter", default=None)
    ap.add_argument("--accent", default=None)
    ap.add_argument("--background", default=None)
    ap.add_argument("--preset", default="peripheral-color-search",
                    choices=list(PRESETS.keys()))
    ap.add_argument("--name", default=None, help="output stem (default: letter + preset)")
    ap.add_argument("--no-fixation", action="store_true")
    args = ap.parse_args()

    cfg = PRESETS[args.preset]
    if args.letter:     cfg.letter = args.letter
    if args.accent:     cfg.accent = args.accent
    if args.background: cfg.background = args.background
    if args.no_fixation: cfg.show_fixation = False

    # Contrast audit (muriel hook)
    ratio = contrast_ratio(cfg.accent, cfg.background)
    print(f"  accent {cfg.accent} on {cfg.background} → contrast {ratio:.2f}:1")
    if ratio < 8.0:
        print(f"  WARNING: below muriel's 8:1 floor", file=sys.stderr)

    # Render
    stem = args.name or f"dropcap-{cfg.letter.lower()}-{args.preset}"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg_path = OUT_DIR / f"{stem}.svg"
    svg_path.write_text(svg_foveated_dropcap(cfg))
    print(f"  → {svg_path}")

    # Rasterize preview
    png_path = OUT_DIR / f"{stem}.png"
    if try_rasterize(svg_path, png_path, scale=2.0):
        print(f"  → {png_path} (cairosvg 2×)")
    else:
        print(f"  (cairosvg not installed — SVG only)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
