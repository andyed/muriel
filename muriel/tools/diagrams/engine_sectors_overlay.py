"""
muriel.tools.diagrams.engine_sectors_overlay — Blauch et al. 2026 cobweb.

The "engine truth" companion to ``foveal_overlay``. Where ``foveal_overlay``
mirrors the in-app **UI** (uniform 16-spoke + linear-rings + fovea /
parafovea bullseye, per ``svg-overlay.js``), this primitive draws what
the **engine** actually samples on:

  - Log-spaced cortical rings (CMF parameterisation: ``w = log(r + a)``)
  - Variable spoke count per ring (~equal-area sectors via
    ``floor(2π · r_center / dr)``)
  - Filled-wedge sector polygons
  - Fidelity-graded opacity (clear at the fovea, dense in the periphery)
  - Single cool-blue tone — ``rgba(100, 160, 200, α)``

Verbatim port of ``drawIsoGrid`` from
``scrutinizer2025/tests/reference-pages/grid-comparison.html``. When
``svg-overlay.js`` is eventually upgraded to draw the real engine grid,
this is the reference implementation.

Layout shared with ``foveal_overlay`` via
``foveal_overlay.compute_isotropic_sectors`` — single source of truth
for the Blauch algorithm; this module never re-derives it.

Three verbosity levels
----------------------
- ``verbosity=1`` — **mark.** Tight-radius cobweb + fixation crosshair.
  Favicon, app icon, social avatar.
- ``verbosity=2`` — **wordmark.** Full cobweb + fixation. Site nav, OG
  card, blog hero.
- ``verbosity=3`` — **diagram.** Wordmark + degree-axis labels + footer
  with the algorithmic parameters. Paper figures.

When to use this versus foveal_overlay
--------------------------------------
- Use ``foveal_overlay`` when the artifact represents what the *user*
  sees in Scrutinizer today.
- Use ``engine_sectors_overlay`` when the artifact represents the
  *math underneath*: paper figures explaining cortical magnification,
  brand-mark contexts where the cobweb's "scientific instrument"
  aesthetic is the point, scientific-schematics that need to stay
  honest about the model.

Reference: ``tests/reference-pages/grid-comparison.html`` (lines 92–268).
"""

from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import Optional, Union

from muriel.tools.diagrams.foveal_overlay import compute_isotropic_sectors

__all__ = ["engine_sectors_overlay", "fidelity_alpha"]


# ─── Palette (mirrors grid-comparison.html) ─────────────────────────

_PALETTE_DARK = {
    "bg":        "#0a0a0f",
    "ink":       "#e6e4d2",
    "muted":     "#b0b0c4",
    "fovea":     "rgba(255,255,255,0.30)",
    "fixation":  "rgba(255,255,255,0.85)",
    "sector":    "100, 160, 200",            # cool blue, RGB triple
    "body_font": "ui-sans-serif, -apple-system, system-ui, sans-serif",
}

_PALETTE_LIGHT = {
    "bg":        "#fafaf6",
    "ink":       "#1a1a24",
    "muted":     "#4a4a5a",
    "fovea":     "rgba(26,26,36,0.45)",
    "fixation":  "rgba(26,26,36,0.85)",
    "sector":    "30, 70, 130",              # darker cool-blue for white bg
    "body_font": "ui-sans-serif, -apple-system, system-ui, sans-serif",
}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _resolve(brand, theme: str, accent: Optional[str], tint: float) -> dict:
    base = _PALETTE_LIGHT if theme == "light" else _PALETTE_DARK
    palette = dict(base)

    if brand is not None:
        c = brand.colors
        palette["bg"] = c.background or palette["bg"]
        palette["muted"] = c.foreground_muted or palette["muted"]
        if brand.typography and brand.typography.body_family:
            palette["body_font"] = brand.typography.body_family
        if accent is None:
            accent = getattr(c, "accent", None)
            if not accent:
                viz = brand.viz.categorical if brand.viz and brand.viz.categorical else []
                accent = viz[0] if viz else None

    if accent and tint > 0:
        r1, g1, b1 = (int(x) for x in palette["sector"].split(","))
        r2, g2, b2 = _hex_to_rgb(accent)
        r = int(round(r1 * (1 - tint) + r2 * tint))
        g = int(round(g1 * (1 - tint) + g2 * tint))
        b = int(round(b1 * (1 - tint) + b2 * tint))
        palette["sector"] = f"{r}, {g}, {b}"

    return palette


# ─── Fidelity / opacity ramp (verbatim from grid-comparison.html) ────

def fidelity_alpha(ecc_deg: float, fovea_deg: float = 1.0,
                   ramp_deg: float = 15.0) -> float:
    """Eccentricity → cobweb opacity (matches ``fidelityAlpha`` in
    ``grid-comparison.html``).

    Inside the fovea the overlay is invisible (alpha=0). Beyond the
    fovea, opacity ramps from 0.15 to 0.70 over ``ramp_deg`` degrees.
    """
    if ecc_deg < fovea_deg:
        return 0.0
    t = min((ecc_deg - fovea_deg) / ramp_deg, 1.0)
    return 0.15 + t * 0.55


# ─── Renderer ───────────────────────────────────────────────────────

def engine_sectors_overlay(
    *,
    verbosity: int = 2,
    size: int = 256,
    eccentricity_max: float = 25.0,
    fovea_radius_deg: float = 1.0,
    cmf_a: float = 2.78,
    num_rings: Optional[int] = None,
    theme: str = "dark",
    accent: Optional[str] = None,
    tint: float = 0.0,
    show_fixation: bool = True,
    show_fovea_outline: bool = True,
    show_labels: Optional[bool] = None,
    label_axis_deg: float = 0.0,
    background: Optional[str] = None,
    body_font: Optional[str] = None,
    out_path: Optional[Union[str, Path]] = None,
    brand=None,
) -> str:
    """Render the Blauch isotropic-sectors cobweb as self-contained SVG.

    Parameters mirror ``foveal_overlay`` where they overlap, plus a few
    cobweb-specific options.

    Parameters
    ----------
    verbosity
        1 = mark, 2 = wordmark, 3 = diagram. See module docstring.
    size
        Square SVG viewBox edge in px.
    eccentricity_max
        Degrees from centre to SVG edge. Default 25° matches the
        canonical ``grid-comparison.html`` half-FOV (which uses 30°);
        tighten for small marks, widen for paper figures.
    fovea_radius_deg
        Foveal radius in degrees. Inside this radius the cobweb is
        invisible (``fidelity_alpha = 0``).
    cmf_a
        Cortical magnification constant (default 2.78).
    num_rings
        Number of cortical rings. If ``None``, picks a verbosity-tuned
        default (8 / 24 / 50) so the cobweb stays legible at icon scale
        and rich at paper scale (canonical default = 50).
    theme
        ``'dark'`` (default) or ``'light'``.
    accent
        Override the brand-tint accent (defaults to ``brand.colors.accent``).
    tint
        How strongly to tint the cobweb sector colour toward the brand
        accent. ``0`` (default) = canonical cool-blue;
        ``1`` = fully brand-coloured.
    show_fixation
        Draw the central fixation crosshair (white, 16x2 px scaled).
    show_fovea_outline
        Draw a faint dashed circle at the foveal radius (helps frame
        the empty-centre region).
    show_labels
        Override the verbosity default. ``None`` → labels only at L3.
    label_axis_deg
        Angle (degrees, 0 = right) for the L3 degree labels.
    out_path
        If given, write the SVG to disk and return the markup.
    brand
        Optional ``muriel.styleguide.StyleGuide``.

    Returns
    -------
    str
        The SVG markup.
    """
    if verbosity not in (1, 2, 3):
        raise ValueError(f"verbosity must be 1, 2, or 3; got {verbosity!r}")
    if size < 16:
        raise ValueError(f"size must be ≥ 16; got {size!r}")
    if eccentricity_max <= 0:
        raise ValueError("eccentricity_max must be positive")
    if fovea_radius_deg <= 0:
        raise ValueError("fovea_radius_deg must be positive")
    if theme not in ("dark", "light"):
        raise ValueError(f"theme must be 'dark' or 'light'; got {theme!r}")

    if num_rings is None:
        num_rings = {1: 8, 2: 24, 3: 50}[verbosity]
    if num_rings < 2:
        raise ValueError("num_rings must be ≥ 2")

    t = _resolve(brand, theme=theme, accent=accent, tint=tint)
    if background is not None:
        t["bg"] = background
    if body_font is not None:
        t["body_font"] = body_font
    if show_labels is None:
        show_labels = (verbosity == 3)

    cx = cy = size / 2.0
    R = size / 2.0
    px_per_deg = R / eccentricity_max
    fovea_r_px = fovea_radius_deg * px_per_deg

    sectors = compute_isotropic_sectors(
        num_rings=num_rings,
        cmf_a=cmf_a,
        eccentricity_max_deg=eccentricity_max,
    )

    # Crosshair size — matches grid-comparison.html (16x2 px on a
    # viewport-scaled canvas). We scale linearly with the SVG viewBox.
    scale = size / 512.0
    cross_arm = max(3.0, 8.0 * scale)
    cross_w   = max(1.0, 2.0 * scale)

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" font-family="{escape(t["body_font"])}" '
        f'shape-rendering="geometricPrecision">'
    )
    parts.append(f'<rect width="{size}" height="{size}" fill="{t["bg"]}"/>')

    # ─── Engine cobweb: filled-wedge sectors ─────────────────────────
    sector_rgb = t["sector"]
    for sec in sectors:
        r_inner_px = max(0.0, sec["r_inner_deg"] * px_per_deg)
        r_outer_px = min(R, sec["r_outer_deg"] * px_per_deg)
        if r_inner_px >= R:
            break
        if r_outer_px <= 0:
            continue

        spoke_count = sec["spoke_count"]
        if spoke_count < 1:
            continue
        spoke_width = (2.0 * math.pi) / spoke_count

        alpha = fidelity_alpha(sec["r_center_deg"], fovea_deg=fovea_radius_deg)
        fill_alpha = alpha if alpha > 0 else 0.02
        stroke_alpha = fill_alpha * 0.6

        # Foveal singularity (spoke_count == 1) renders as a full disk.
        if spoke_count == 1:
            parts.append(
                f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r_outer_px:.2f}" '
                f'fill="rgba({sector_rgb}, {fill_alpha:.4f})" '
                f'stroke="rgba({sector_rgb}, {stroke_alpha:.4f})" '
                f'stroke-width="0.5"/>'
            )
            continue

        for s in range(spoke_count):
            a0 = s * spoke_width
            a1 = (s + 1) * spoke_width
            cos0, sin0 = math.cos(a0), math.sin(a0)
            cos1, sin1 = math.cos(a1), math.sin(a1)
            ix0, iy0 = cx + cos0 * r_inner_px, cy + sin0 * r_inner_px
            ix1, iy1 = cx + cos1 * r_inner_px, cy + sin1 * r_inner_px
            ox0, oy0 = cx + cos0 * r_outer_px, cy + sin0 * r_outer_px
            ox1, oy1 = cx + cos1 * r_outer_px, cy + sin1 * r_outer_px
            # SVG path: inner arc CCW from a0→a1, then outer arc CW back.
            d = (
                f"M {ix0:.2f} {iy0:.2f} "
                f"A {r_inner_px:.2f} {r_inner_px:.2f} 0 0 1 {ix1:.2f} {iy1:.2f} "
                f"L {ox1:.2f} {oy1:.2f} "
                f"A {r_outer_px:.2f} {r_outer_px:.2f} 0 0 0 {ox0:.2f} {oy0:.2f} Z"
            )
            parts.append(
                f'<path d="{d}" '
                f'fill="rgba({sector_rgb}, {fill_alpha:.4f})" '
                f'stroke="rgba({sector_rgb}, {stroke_alpha:.4f})" '
                f'stroke-width="0.5"/>'
            )

    # ─── Fovea outline (faint dashed circle, optional) ───────────────
    if show_fovea_outline:
        parts.append(
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{fovea_r_px:.2f}" '
            f'fill="none" stroke="{t["fovea"]}" stroke-width="1" '
            f'stroke-dasharray="4,4" vector-effect="non-scaling-stroke"/>'
        )

    # ─── Fixation crosshair (canonical 16x2-style, scaled) ───────────
    if show_fixation:
        parts.append(
            f'<line x1="{cx:.2f}" y1="{cy - cross_arm:.2f}" '
            f'x2="{cx:.2f}" y2="{cy + cross_arm:.2f}" '
            f'stroke="{t["fixation"]}" stroke-width="{cross_w:.2f}"/>'
        )
        parts.append(
            f'<line x1="{cx - cross_arm:.2f}" y1="{cy:.2f}" '
            f'x2="{cx + cross_arm:.2f}" y2="{cy:.2f}" '
            f'stroke="{t["fixation"]}" stroke-width="{cross_w:.2f}"/>'
        )

    # ─── L3 degree labels + footer caption ───────────────────────────
    if show_labels and verbosity >= 3:
        tick_deg = [d for d in (fovea_radius_deg, 5, 10, 20, 30, 60)
                    if d <= eccentricity_max]
        for d in tick_deg:
            r = d * px_per_deg
            a = math.radians(label_axis_deg - 90.0)
            lx = cx + (r + 12) * math.cos(a)
            ly = cy + (r + 12) * math.sin(a)
            parts.append(
                f'<text x="{lx:.2f}" y="{ly:.2f}" fill="{t["muted"]}" '
                f'font-size="11" font-weight="500" '
                f'text-anchor="middle" dominant-baseline="middle">'
                f'{d:g}°</text>'
            )

        total_sectors = sum(s["spoke_count"] for s in sectors)
        caption = (
            f"fovea {fovea_radius_deg:g}° · {num_rings} cortical rings · "
            f"{total_sectors} isotropic sectors (a={cmf_a:g}, "
            f"Blauch et al. 2026) · ±{eccentricity_max:g}°"
        )
        parts.append(
            f'<text x="{cx:.2f}" y="{size - 8:.2f}" fill="{t["muted"]}" '
            f'font-size="10" text-anchor="middle">{escape(caption)}</text>'
        )

    parts.append("</svg>")
    svg = "\n".join(parts)

    if out_path is not None:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(svg, encoding="utf-8")
    return svg


# ─── CLI ────────────────────────────────────────────────────────────

def _main(argv=None) -> int:
    """``python -m muriel.tools.diagrams.engine_sectors_overlay [opts] OUT.svg``."""
    import argparse
    ap = argparse.ArgumentParser(
        prog="python -m muriel.tools.diagrams.engine_sectors_overlay",
        description="Render the Blauch et al. 2026 isotropic-sectors cobweb "
                    "(verbatim port of grid-comparison.html::drawIsoGrid).",
    )
    ap.add_argument("output", help="output SVG path")
    ap.add_argument("--verbosity", type=int, default=2, choices=(1, 2, 3),
                    help="1=mark, 2=wordmark, 3=diagram (default 2)")
    ap.add_argument("--size", type=int, default=256,
                    help="square viewBox edge in px (default 256)")
    ap.add_argument("--eccentricity-max", type=float, default=25.0,
                    help="degrees from centre to SVG edge (default 25)")
    ap.add_argument("--fovea-deg", type=float, default=1.0,
                    help="foveal radius in degrees (default 1.0)")
    ap.add_argument("--num-rings", type=int, default=None,
                    help="cortical rings (default 8/24/50 by verbosity)")
    ap.add_argument("--cmf-a", type=float, default=2.78,
                    help="cortical magnification constant (default 2.78)")
    ap.add_argument("--theme", default="dark", choices=("dark", "light"),
                    help="palette theme (default dark)")
    ap.add_argument("--accent", default=None, help="brand accent override")
    ap.add_argument("--tint", type=float, default=0.0,
                    help="brand-tint strength, 0=canonical cool-blue (default)")
    ap.add_argument("--no-fixation", action="store_true",
                    help="suppress fixation crosshair")
    ap.add_argument("--no-fovea-outline", action="store_true",
                    help="suppress the dashed fovea outline")
    ap.add_argument("--brand", default=None,
                    help="brand.toml to source colours from")
    args = ap.parse_args(argv)

    brand = None
    if args.brand:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(args.brand)

    engine_sectors_overlay(
        verbosity=args.verbosity,
        size=args.size,
        eccentricity_max=args.eccentricity_max,
        fovea_radius_deg=args.fovea_deg,
        num_rings=args.num_rings,
        cmf_a=args.cmf_a,
        theme=args.theme,
        accent=args.accent,
        tint=args.tint,
        show_fixation=not args.no_fixation,
        show_fovea_outline=not args.no_fovea_outline,
        out_path=args.output,
        brand=brand,
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
