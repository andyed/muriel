"""Drop-cap generator with a pluggable texture registry.

A drop cap is a large letter in an accent color + a decorative texture
behind it that fades radially from center. Different textures carry
different semantic payloads — log-polar for foveation posts, crosshatch
for type-history, stipple for noise/entropy essays, etc.

Textures are plugins. Each is a function:

    def render(cx, cy, r_outer, cfg) -> list[str]   # returns SVG snippets

New textures: drop into TEXTURES dict. The outer fade is the texture's
own responsibility (some fades linearly, some don't at all, some gate
on density). The main generator handles: background, fixation marker
(optional), letter composition, contrast audit.

Usage:
    python3 gen_dropcap.py --letter H --texture log-polar
    python3 gen_dropcap.py --letter T --texture crosshatch --accent '#DDA6B6'
    python3 gen_dropcap.py --preset peripheral-color-search

Muriel hooks honored: accent/background contrast ratio ≥ 8:1 (warns if not).
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

OUT_DIR = Path(__file__).resolve().parent / "output"


# ── Contrast (muriel) ──────────────────────────────────────────────────
def _lin(c):
    x = c / 255.0
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def _lum(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(fg, bg):
    lf, lb = _lum(fg), _lum(bg)
    hi, lo = (lf, lb) if lf > lb else (lb, lf)
    return (hi + 0.05) / (lo + 0.05)


# ── Shared fade helper ─────────────────────────────────────────────────
def radial_alpha(r, r_inner, r_outer, center_alpha, edge_alpha, power):
    if r <= r_inner:
        return center_alpha
    t = (r - r_inner) / max(1.0, r_outer - r_inner)
    t = max(0.0, min(1.0, t)) ** power
    return center_alpha + (edge_alpha - center_alpha) * t


# ── Texture plugins ────────────────────────────────────────────────────
#
# Each returns a list of SVG element strings. Texture functions receive
# (center_x, center_y, outer_radius, cfg_dict). `cfg` is the texture's
# parameters merged from the global config.

def texture_log_polar(cx, cy, r_outer, cfg):
    """Log-polar V1 cortical map — log-spaced concentric rings PLUS
    per-ring angular-offset spoke SEGMENTS (cells staggered half-a-cell
    between adjacent rings, like cortical receptive-field layout).
    Without the offset it'd be just a polar grid; with it the cells
    form a brick-like tessellation that reads as V1.

    `offset_mode`: 'alternate' (default) | 'progressive' | 'none'
    """
    accent = cfg["accent"]
    n_rings = cfg.get("n_rings", 16)
    n_spokes = cfg.get("n_spokes", 36)
    r_inner = cfg.get("r_inner", 16.0)
    a_center = cfg.get("alpha_center", 0.80)
    a_edge = cfg.get("alpha_edge", 0.35)
    fade_power = cfg.get("fade_power", 1.2)
    offset_mode = cfg.get("offset_mode", "alternate")

    cell_angle = 2 * math.pi / n_spokes

    # Log-spaced ring radii
    ring_radii = []
    for i in range(n_rings):
        u = i / max(1, n_rings - 1)
        ring_radii.append(r_inner * (r_outer / r_inner) ** u)

    out = []
    # Concentric rings
    out.append(f'<g stroke="{accent}" fill="none" stroke-width="1">')
    for r in ring_radii:
        a = radial_alpha(r, r_inner, r_outer, a_center, a_edge, fade_power)
        out.append(f'  <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" stroke-opacity="{a:.3f}"/>')
    out.append('</g>')

    # Per-band spoke segments, staggered between bands
    out.append(f'<g stroke="{accent}" fill="none" stroke-width="1">')
    for i in range(len(ring_radii) - 1):
        r_i, r_o = ring_radii[i], ring_radii[i + 1]
        if offset_mode == "alternate":
            offset = (i % 2) * (cell_angle / 2)
        elif offset_mode == "progressive":
            offset = (i / max(1, n_rings - 1)) * cell_angle
        else:
            offset = 0.0
        a = radial_alpha((r_i + r_o) / 2, r_inner, r_outer, a_center, a_edge, fade_power)
        for k in range(n_spokes):
            theta = k * cell_angle + offset
            x1 = cx + r_i * math.cos(theta); y1 = cy + r_i * math.sin(theta)
            x2 = cx + r_o * math.cos(theta); y2 = cy + r_o * math.sin(theta)
            out.append(f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke-opacity="{a:.3f}"/>')
    out.append('</g>')
    return out


def texture_crosshatch(cx, cy, r_outer, cfg):
    """45° crosshatched lines — woodblock / intaglio / Victorian engraving.
    Best for type-history, printmaking, letterpress essays."""
    accent = cfg["accent"]
    spacing = cfg.get("spacing", 8.0)
    a_center = cfg.get("alpha_center", 0.50)
    a_edge = cfg.get("alpha_edge", 0.0)
    fade_power = cfg.get("fade_power", 1.6)
    angles_deg = cfg.get("angles", [45, -45])

    gid = "hatchFade"
    out = []
    out.append('<defs>')
    out.append(f'  <radialGradient id="{gid}" cx="50%" cy="50%" r="50%">')
    out.append(f'    <stop offset="0%" stop-color="{accent}" stop-opacity="{a_center:.3f}"/>')
    out.append(f'    <stop offset="70%" stop-color="{accent}" stop-opacity="{a_center * 0.35:.3f}"/>')
    out.append(f'    <stop offset="100%" stop-color="{accent}" stop-opacity="{a_edge:.3f}"/>')
    out.append('  </radialGradient>')
    out.append('</defs>')
    out.append(f'<g stroke="url(#{gid})" stroke-width="1" fill="none">')
    # For each direction, draw parallel lines across the bounding box
    bbox_r = r_outer * 1.05
    for ang_deg in angles_deg:
        theta = math.radians(ang_deg)
        # Perpendicular direction to step along
        ex, ey = math.cos(theta), math.sin(theta)       # line direction
        px, py = -ey, ex                                 # perpendicular
        # Range of perpendicular offsets to cover the outer radius
        n_steps = int(bbox_r * 2 / spacing) + 1
        for k in range(-n_steps // 2, n_steps // 2 + 1):
            d = k * spacing
            mx = cx + px * d
            my = cy + py * d
            # Clip line to circle of radius bbox_r around (cx,cy)
            # solve |(mx,my) + t*(ex,ey) - (cx,cy)|² = bbox_r²
            dx, dy = mx - cx, my - cy
            A = 1.0
            B = 2 * (dx * ex + dy * ey)
            C = dx * dx + dy * dy - bbox_r * bbox_r
            disc = B * B - 4 * A * C
            if disc <= 0: continue
            sq = math.sqrt(disc)
            t1 = (-B - sq) / 2
            t2 = (-B + sq) / 2
            x1, y1 = mx + t1 * ex, my + t1 * ey
            x2, y2 = mx + t2 * ex, my + t2 * ey
            out.append(f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
    out.append('</g>')
    return out


def texture_stipple(cx, cy, r_outer, cfg):
    """Poisson-disk-ish stipple — dense points thinning outward.
    Best for noise/entropy, sampling, uncertainty posts."""
    import random
    accent = cfg["accent"]
    n_points = cfg.get("n_points", 1800)
    r_min_dot = cfg.get("dot_radius_min", 0.9)
    r_max_dot = cfg.get("dot_radius_max", 2.1)
    r_inner = cfg.get("r_inner", 12.0)
    a_center = cfg.get("alpha_center", 0.85)
    a_edge = cfg.get("alpha_edge", 0.0)
    fade_power = cfg.get("fade_power", 1.5)
    density_power = cfg.get("density_power", 0.7)   # <1 = more at center
    seed = cfg.get("seed", 7)

    rng = random.Random(seed)
    out = [f'<g fill="{accent}">']
    for _ in range(n_points):
        # Density that favors the center — sample radius via inverse-CDF
        # of power distribution
        u = rng.random() ** density_power
        r = r_inner + u * (r_outer - r_inner)
        theta = rng.uniform(0, math.tau)
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)
        a = radial_alpha(r, r_inner, r_outer, a_center, a_edge, fade_power)
        if a <= 0.02: continue
        dot_r = rng.uniform(r_min_dot, r_max_dot)
        out.append(f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{dot_r:.2f}" fill-opacity="{a:.3f}"/>')
    out.append('</g>')
    return out


def texture_illuminated(cx, cy, r_outer, cfg):
    """Traditional manuscript illuminated drop cap — bordered block with
    a dense rosette ornament. Draws (a) an outer frame rectangle, (b)
    optional inner frame, (c) concentric scalloped rings, (d)
    alternating-length radial spokes, (e) center medallion.

    Expects to be composed at near-square aspect ratio; works best when
    r_outer ≈ canvas half-width so the ornament fills the frame.

    Best for general editorial drop caps where the log-polar V1 map
    would be too subject-specific."""
    accent = cfg["accent"]
    n_rings = cfg.get("n_rings", 4)
    n_spokes = cfg.get("n_spokes", 32)
    spoke_pairs = cfg.get("spoke_pairs", True)
    r_inner = cfg.get("r_inner", 30.0)
    a_center = cfg.get("alpha_center", 0.90)
    a_edge = cfg.get("alpha_edge", 0.55)
    fade_power = cfg.get("fade_power", 1.0)
    scallop_depth = cfg.get("scallop_depth", 8.0)
    scallop_freq = cfg.get("scallop_freq", 24)
    frame_padding = cfg.get("frame_padding", 14.0)     # px inside canvas bounds
    frame_thickness = cfg.get("frame_thickness", 3.0)
    inner_frame_gap = cfg.get("inner_frame_gap", 8.0)   # px; 0 disables inner frame

    out = []

    # Outer bordered block — defines the "illuminated" frame
    pad = frame_padding
    out.append(f'<rect x="{cx - r_outer - pad:.2f}" y="{cy - r_outer - pad:.2f}" '
               f'width="{(r_outer + pad) * 2:.2f}" height="{(r_outer + pad) * 2:.2f}" '
               f'fill="none" stroke="{accent}" stroke-width="{frame_thickness}" '
               f'stroke-opacity="{a_center:.3f}"/>')
    # Inner frame (thin parallel border — classic manuscript "double rule")
    if inner_frame_gap > 0:
        inner_pad = pad - inner_frame_gap
        out.append(f'<rect x="{cx - r_outer - inner_pad:.2f}" y="{cy - r_outer - inner_pad:.2f}" '
                   f'width="{(r_outer + inner_pad) * 2:.2f}" height="{(r_outer + inner_pad) * 2:.2f}" '
                   f'fill="none" stroke="{accent}" stroke-width="1" '
                   f'stroke-opacity="{a_center * 0.6:.3f}"/>')
    # Scalloped concentric rings — sinusoidal radius
    out.append(f'<g stroke="{accent}" fill="none" stroke-width="1.2">')
    for i in range(n_rings):
        u = (i + 1) / n_rings
        r_base = r_inner + u * (r_outer - r_inner)
        a = radial_alpha(r_base, r_inner, r_outer, a_center, a_edge, fade_power)
        # Sample points around the circle, modulating r by a sin wave
        pts = []
        n_pts = scallop_freq * 6
        for k in range(n_pts + 1):
            theta = 2 * math.pi * k / n_pts
            r = r_base + scallop_depth * math.sin(theta * scallop_freq + i * math.pi / 2)
            pts.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))
        d = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"
        out.append(f'  <path d="{d}" stroke-opacity="{a:.3f}"/>')
    out.append('</g>')

    # Radial spokes — alternating long / short for a rosette rhythm
    out.append(f'<g stroke="{accent}" fill="none" stroke-width="1">')
    for k in range(n_spokes):
        theta = 2 * math.pi * k / n_spokes
        r_spoke = r_outer * (1.0 if (not spoke_pairs or k % 2 == 0) else 0.72)
        a = radial_alpha(r_spoke * 0.6, r_inner, r_outer, a_center, a_edge, fade_power)
        x1 = cx + r_inner * math.cos(theta); y1 = cy + r_inner * math.sin(theta)
        x2 = cx + r_spoke * math.cos(theta); y2 = cy + r_spoke * math.sin(theta)
        out.append(f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke-opacity="{a:.3f}"/>')
    out.append('</g>')

    # Small inner circle — center medallion
    inner_med = r_inner * 0.55
    out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{inner_med:.2f}" '
               f'fill="none" stroke="{accent}" stroke-width="1.2" stroke-opacity="{a_center:.3f}"/>')
    return out


TEXTURES: dict[str, Callable] = {
    "log-polar":   texture_log_polar,
    "illuminated": texture_illuminated,
    "crosshatch":  texture_crosshatch,
    "stipple":     texture_stipple,
}


# ── Config ─────────────────────────────────────────────────────────────
@dataclass
class DropCapConfig:
    letter: str = "H"
    accent: str = "#C07FA0"
    background: str = "#0A0A0E"
    # Portrait canvas — the decoration extends DOWN into the descender
    # region, like a traditional fancy drop cap's ornamental tail.
    width: int = 520
    height: int = 660
    # Fixation anchored to letter's "eye" — for most caps, this sits in
    # the lower counter. Expressed as fraction of canvas (0,0) = top-left.
    fixation_x_frac: float = 0.50
    fixation_y_frac: float = 0.58
    # Ornament radius — large enough to reach the canvas corners (spills).
    r_outer: float = 420.0
    texture: str = "log-polar"
    texture_params: dict = field(default_factory=dict)
    font_family: str = "Didot, 'Bodoni 72', 'Bodoni MT', Georgia, serif"
    font_weight: int = 700
    # Letter sized to fill the height; cap-top aligned to canvas top so
    # the drop cap flushes to the paragraph's first text line. Ornament
    # extends DOWN into the descender region below the letter.
    letter_size_px: int = 520
    letter_top_px: int = 8            # px from canvas top to letter cap top
    show_fixation: bool = False        # noise in typographic use — off by default
    fixation_color: str = "#FFFFFF"
    fixation_radius: float = 7.0


def build_grid_only_svg(cfg: "DropCapConfig") -> str:
    """Letterless grid asset — reusable across all posts/letters.
    Designed for use as a CSS background behind a real text letter.
    Background is transparent so the asset works on any surface.
    """
    W, H = cfg.width, cfg.height
    cx = W * cfg.fixation_x_frac
    cy = H * cfg.fixation_y_frac
    tex_fn = TEXTURES[cfg.texture]
    tex_cfg = {"accent": cfg.accent, **cfg.texture_params}
    elements = tex_fn(cx, cy, cfg.r_outer, tex_cfg)
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">']
    lines.extend('  ' + el for el in elements)
    lines.append('</svg>')
    return "\n".join(lines)


def build_svg(cfg: DropCapConfig) -> str:
    W, H = cfg.width, cfg.height
    # Ornament is anchored to the fixation point (which is noise-off by
    # default but still serves as the radial anchor for the texture).
    cx = W * cfg.fixation_x_frac
    cy = H * cfg.fixation_y_frac

    tex_fn = TEXTURES[cfg.texture]
    tex_cfg = {"accent": cfg.accent, **cfg.texture_params}
    texture_elements = tex_fn(cx, cy, cfg.r_outer, tex_cfg)

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    lines.append(f'  <rect width="100%" height="100%" fill="{cfg.background}"/>')
    lines.extend('  ' + el for el in texture_elements)

    if cfg.show_fixation:
        fr = cfg.fixation_radius
        lines.append(f'  <g fill="{cfg.background}" stroke="{cfg.fixation_color}" stroke-width="1.5">')
        lines.append(f'    <circle cx="{cx}" cy="{cy}" r="{fr}"/>')
        lines.append(f'    <line x1="{cx - fr}" y1="{cy}" x2="{cx + fr}" y2="{cy}" stroke="{cfg.fixation_color}" stroke-width="1"/>')
        lines.append(f'    <line x1="{cx}" y1="{cy - fr}" x2="{cx}" y2="{cy + fr}" stroke="{cfg.fixation_color}" stroke-width="1"/>')
        lines.append('  </g>')

    # Letter anchored to canvas TOP (cap-height aligned to y=0) so the
    # drop cap sits flush with the paragraph's first text line. The
    # ornament below extends into the descender region.
    letter_top_y = cfg.letter_top_px   # absolute px from canvas top
    lines.append(f'  <text x="{W / 2}" y="{letter_top_y}" font-family="{cfg.font_family}" '
                 f'font-weight="{cfg.font_weight}" font-size="{cfg.letter_size_px}" '
                 f'fill="{cfg.accent}" text-anchor="middle" '
                 f'dominant-baseline="text-before-edge">{cfg.letter}</text>')
    lines.append('</svg>')
    return "\n".join(lines)


# ── Presets ────────────────────────────────────────────────────────────
PRESETS = {
    "peripheral-color-search": DropCapConfig(
        letter="H", accent="#C07FA0", background="#0A0A0E", texture="log-polar",
    ),
    "typography-history": DropCapConfig(
        letter="T", accent="#D4A670", background="#0A0A0E", texture="crosshatch",
        show_fixation=False,
    ),
    "noise-entropy": DropCapConfig(
        letter="N", accent="#9AB8D4", background="#0A0A0E", texture="stipple",
        show_fixation=False,
    ),
    "demo-grid": DropCapConfig(
        letter="D", accent="#C07FA0", background="#0A0A0E", texture="log-polar",
    ),
}


def try_rasterize(svg_path: Path, out_png: Path, scale: float = 2.0) -> bool:
    # Try cairosvg, then ImageMagick, then rsvg-convert
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(out_png), scale=scale)
        return True
    except ImportError:
        pass
    import subprocess
    for cmd in [
        ["magick", str(svg_path), "-background", "none", "-density", str(int(96 * scale)), str(out_png)],
        ["rsvg-convert", "-o", str(out_png), "-z", str(scale), str(svg_path)],
    ]:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--letter", default=None)
    ap.add_argument("--accent", default=None)
    ap.add_argument("--background", default=None)
    ap.add_argument("--texture", choices=list(TEXTURES.keys()), default=None)
    ap.add_argument("--preset", default="peripheral-color-search",
                    choices=list(PRESETS.keys()))
    ap.add_argument("--name", default=None)
    ap.add_argument("--no-fixation", action="store_true")
    ap.add_argument("--all-textures", action="store_true",
                    help="Render the same letter in every texture for comparison")
    args = ap.parse_args()

    cfg = PRESETS[args.preset]
    if args.letter:      cfg.letter = args.letter
    if args.accent:      cfg.accent = args.accent
    if args.background:  cfg.background = args.background
    if args.texture:     cfg.texture = args.texture
    if args.no_fixation: cfg.show_fixation = False

    ratio = contrast_ratio(cfg.accent, cfg.background)
    print(f"  accent {cfg.accent} on {cfg.background} → contrast {ratio:.2f}:1"
          + ("" if ratio >= 8 else "  ⚠ below 8:1 floor"))

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def _render_one(cfg):
        stem = args.name or f"dropcap-{cfg.letter.lower()}-{cfg.texture}"
        svg_path = OUT_DIR / f"{stem}.svg"
        svg_path.write_text(build_svg(cfg))
        print(f"  → {svg_path}")
        png_path = OUT_DIR / f"{stem}.png"
        if try_rasterize(svg_path, png_path, scale=2.0):
            print(f"  → {png_path} (rasterized 2×)")

    if args.all_textures:
        for tex in TEXTURES:
            c = DropCapConfig(**{**cfg.__dict__, "texture": tex})
            _render_one(c)
    else:
        _render_one(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
