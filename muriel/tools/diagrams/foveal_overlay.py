"""
muriel.tools.diagrams.foveal_overlay — Scrutinizer's foveal mark.

The Scrutinizer brand mark, generated as deterministic SVG. Combines
two distinct layers:

  **UI layer** — the fovea + parafovea bullseye (`svg-overlay.js`).
  These are user-facing indicators; geometry below mirrors the in-app
  defaults exactly.

  - **Fovea**     — white unfilled circle (`fill='none'`, stroke 1.5,
                    opacity 0.6) + 12 outward white tick marks (every
                    30°, length 15px, opacity 0.8). Halo drop-shadow
                    (``stdDeviation=1.5``, flood ``rgba(0,0,0,0.9)``).
  - **Parafovea** — dashed light-blue ring (``#a0c0ff``, opacity 0.7,
                    ``stroke-dasharray="20, 10"``, ``stroke-linecap=butt``).

  **Engine layer** — the cortical-sector grid the *renderer actually
  uses* (`webgpu-pyramid-compute.js:_computeSectorLayout`, canonical
  reference at `tests/unit/isotropic-sectors.test.js`). Blauch et al.
  2026 isotropic-sector layout:

      a       = cmf_a (default 2.78)
      N       = num_rings
      w_min   = log(a)
      w_step  = log(R_max / a + 1) / (N − 1)

      For each ring n in [0, N):
          r_center  = exp(w_min + n·w_step) − a              # log-spaced
          dr        = (exp(...n+1) − exp(...n−1)) / 2         # half-width
          spokes    = 1 if n==0 else floor(2π · r_center / dr) # ↑ outward

  Rings are log-spaced (tight near fovea, expanding outward); spoke
  count grows with ring index so each sector is approximately isotropic
  (tangential ≈ radial extent). Ring 0 is the foveal singularity
  (1 sector). The outer cobweb gets denser the further out you go —
  the visual signature of cortical magnification.

  This *engine* grid does NOT match `svg-overlay.js`'s debug overlay,
  which draws uniform 16 spokes + linearly-spaced rings. The debug
  overlay is a known simplification; this primitive ships the honest
  Blauch sector layout so the brand mark matches what the engine does.

If `svg-overlay.js` ever upgrades to draw the real sectors, this file
becomes the reference implementation for that change.

Internal cortical magnification (the M(E) curve, log-polar sampling)
governs the *shader's* MIP sampling in ``peripheral.frag`` — it does
not drive the visible overlay. The overlay is a linear, equal-area
grid; the brand mark matches what users actually see in the app.

Three verbosity levels
----------------------
- ``verbosity=1`` — **mark.** Fovea + a few spokes + one hint ring.
  Favicon, app icon, social avatar.
- ``verbosity=2`` — **wordmark.** Full overlay (fovea + parafovea +
  all rings + 16 spokes). Site nav, OG card, blog hero.
- ``verbosity=3`` — **diagram.** Wordmark + degree-axis labels +
  footer with `fovea / parafovea / px-per-deg`. Paper figures.

When to use
-----------
Whenever you need to depict Scrutinizer's POV. The mark is the product's
aesthetic compressed to icon scale. The diagram doubles as the figure
that explains what the overlay is showing.

Anti-prescription
-----------------
- Don't change ``cmf_a`` or ``num_rings`` without updating
  ``svg-overlay.js`` in the same change. The brand mark and the in-app
  overlay must read as the same artifact.
- L1 must stay legible at favicon scale. Skip the parafovea ring at
  L1 — at small sizes, dashed strokes alias and the mark loses its
  silhouette.
- This is a brand mark synched to a live product. If the product's
  overlay changes, this file changes; the SVG outputs are downstream.

Reference: ``scrutinizer2025/renderer/svg-overlay.js`` (``buildGrid``).
"""

from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import Optional, Union

__all__ = ["foveal_overlay", "compute_isotropic_sectors"]


# ─── Isotropic cortical sectors (Blauch et al. 2026) ─────────────────

def compute_isotropic_sectors(
    *,
    num_rings: int,
    cmf_a: float = 2.78,
    eccentricity_max_deg: float = 12.0,
) -> list[dict]:
    """Return per-ring sector layout: ``[{n, r_center_deg, dr_deg, r_inner_deg, r_outer_deg, spoke_count}, …]``.

    Mirrors the algorithm in
    ``scrutinizer2025/renderer/webgpu-pyramid-compute.js::_computeSectorLayout``
    and the canonical test in ``tests/unit/isotropic-sectors.test.js``.
    Ring 0 is the foveal singularity (``spoke_count = 1``); spoke count
    grows with eccentricity so each sector is approximately isotropic.
    """
    if num_rings < 2:
        raise ValueError("num_rings must be ≥ 2")
    if cmf_a <= 0 or eccentricity_max_deg <= 0:
        raise ValueError("cmf_a and eccentricity_max_deg must be positive")

    a = cmf_a
    N = num_rings
    w_min = math.log(a)
    cortical_max = math.log(eccentricity_max_deg / a + 1.0)
    w_step = cortical_max / (N - 1)

    rings: list[dict] = []
    for n in range(N):
        w_i = w_min + n * w_step
        r_center = math.exp(w_i) - a

        if n == 0:
            dr = math.exp(w_min + w_step) - math.exp(w_min)
        elif n == N - 1:
            dr = math.exp(w_min + (N - 1) * w_step) - math.exp(w_min + (N - 2) * w_step)
        else:
            dr = (math.exp(w_min + (n + 1) * w_step) - math.exp(w_min + (n - 1) * w_step)) / 2

        if n == 0:
            spoke_count = 1
        else:
            spoke_count = max(1, int(2.0 * math.pi * r_center / dr))

        rings.append({
            "n":            n,
            "r_center_deg": r_center,
            "dr_deg":       dr,
            "r_inner_deg":  max(0.0, r_center - dr / 2),
            "r_outer_deg":  r_center + dr / 2,
            "spoke_count":  spoke_count,
        })
    return rings


# ─── Brand → tokens ─────────────────────────────────────────────────

_PRODUCT_PALETTE_DARK = {
    # Mirrors scrutinizer2025/renderer/svg-overlay.js exactly.
    # Three segments, three distinct treatments: fovea, parafovea, periphery.
    "bg":              "#0a0a0f",
    "ink":             "#e0e0ec",
    "muted":           "#b0b0c4",
    "fovea":           "#ffffff",     # fovea circle stroke + 12 outward ticks
    "parafovea":       "#a0c0ff",     # parafovea dashed ring
    "ring":            "#00ccff",     # periphery concentric rings (cyan)
    "spoke":           "#80a0ff",     # periphery 16 spokes (blue-violet)
    "halo_flood":      "rgba(0,0,0,0.9)",
    "body_font":       "ui-sans-serif, -apple-system, system-ui, sans-serif",
}

_PRODUCT_PALETTE_LIGHT = {
    # Inverted-luminance variant for white / cream backgrounds. Same
    # role distinctions, darker hue family so the mark is recognisably
    # the same artifact across themes.
    "bg":              "#fafaf6",
    "ink":             "#1a1a24",
    "muted":           "#4a4a5a",
    "fovea":           "#1a1a24",
    "parafovea":       "#2c3e64",
    "ring":            "#0e7490",
    "spoke":           "#4338ca",
    "halo_flood":      "rgba(255,255,255,0.85)",
    "body_font":       "ui-sans-serif, -apple-system, system-ui, sans-serif",
}

_PRODUCT_PALETTE = _PRODUCT_PALETTE_DARK


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha:.4f})"


def _tint_toward(hex_color: str, accent: str, amount: float) -> str:
    """Blend ``hex_color`` toward ``accent`` by ``amount`` ∈ [0, 1].

    Used to brand-tint the product palette: a brand's accent shifts the
    product's cyan/blue grid colours toward the brand identity while
    keeping role distinctions (rings ≠ spokes ≠ parafovea).
    """
    if amount <= 0:
        return hex_color
    if amount >= 1:
        return accent
    r1, g1, b1 = _hex_to_rgb(hex_color)
    r2, g2, b2 = _hex_to_rgb(accent)
    r = int(round(r1 * (1 - amount) + r2 * amount))
    g = int(round(g1 * (1 - amount) + g2 * amount))
    b = int(round(b1 * (1 - amount) + b2 * amount))
    return f"#{r:02x}{g:02x}{b:02x}"


def _resolve(brand, tint: float, theme: str = "dark") -> dict:
    """Map a StyleGuide + theme to overlay-role tokens, optionally brand-tinted.

    ``theme`` selects the dark/light palette; ``tint`` ∈ [0, 1] blends the
    grid colour toward the brand's accent (``tint=0`` → product-accurate).
    """
    base = _PRODUCT_PALETTE_LIGHT if theme == "light" else _PRODUCT_PALETTE_DARK
    palette = dict(base)
    if brand is None:
        return palette

    c = brand.colors
    accent = getattr(c, "accent", None)
    if not accent:
        viz = brand.viz.categorical if brand.viz and brand.viz.categorical else []
        accent = viz[0] if viz else None

    palette["bg"] = c.background or palette["bg"]
    palette["muted"] = c.foreground_muted or palette["muted"]
    if brand.typography and brand.typography.body_family:
        palette["body_font"] = brand.typography.body_family

    if accent and tint > 0:
        # Tint the cobweb sector colour toward the brand.
        r1, g1, b1 = (int(x) for x in palette["sector"].split(","))
        r2, g2, b2 = _hex_to_rgb(accent)
        r = int(round(r1 * (1 - tint) + r2 * tint))
        g = int(round(g1 * (1 - tint) + g2 * tint))
        b = int(round(b1 * (1 - tint) + b2 * tint))
        palette["sector"] = f"{r}, {g}, {b}"

    return palette


# ─── Fidelity / opacity ramp (mirrors grid-comparison.html) ─────────

def _fidelity_alpha(ecc_deg: float, fovea_deg: float = 1.0, ramp_deg: float = 15.0) -> float:
    """Eccentricity → cobweb opacity (matches ``fidelityAlpha`` in grid-comparison.html).

    Inside the fovea the overlay is invisible (alpha=0). Beyond the
    fovea, opacity ramps from 0.15 to 0.70 over ``ramp_deg`` degrees.
    """
    if ecc_deg < fovea_deg:
        return 0.0
    t = min((ecc_deg - fovea_deg) / ramp_deg, 1.0)
    return 0.15 + t * 0.55


# ─── Renderer ───────────────────────────────────────────────────────

def foveal_overlay(
    *,
    verbosity: int = 2,
    size: int = 256,
    eccentricity_max: float = 12.0,
    fovea_radius_deg: float = 1.0,
    parafovea_radius_deg: float = 5.0,
    n_spokes: int = 16,
    theme: str = "dark",
    show_fovea_ticks: bool = True,
    accent: Optional[str] = None,
    background: Optional[str] = None,
    tint: float = 0.0,
    show_labels: Optional[bool] = None,
    label_axis_deg: float = 0.0,
    body_font: Optional[str] = None,
    out_path: Optional[Union[str, Path]] = None,
    brand=None,
) -> str:
    """Render Scrutinizer's foveal overlay grid as self-contained SVG.

    Parameters mirror ``scrutinizer2025/renderer/svg-overlay.js``.

    Parameters
    ----------
    verbosity
        1 = mark, 2 = wordmark, 3 = diagram. See module docstring.
    size
        Square SVG viewBox edge in px. Half of ``size`` corresponds to
        ``eccentricity_max`` degrees of visual angle.
    eccentricity_max
        Degrees from centre to SVG edge. Default 12° keeps the fovea +
        12 ticks reading at brand-mark sizes (in-app proportions assume
        ~90px fovea on a 1080-tall viewport ≈ 17° max). Override to 20°+
        for diagram contexts where the wider field is the point.
    fovea_radius_deg
        Foveal radius in degrees (Scrutinizer default 1.0° → 2° diameter).
    parafovea_radius_deg
        Parafoveal radius in degrees (default 5.0°).
    cmf_a
        Cortical magnification constant (default 2.78). Drives the
        log-spacing of the engine grid; smaller ``a`` → tighter rings
        near fovea.
    num_rings
        Number of cortical rings in the engine grid. If ``None``, picks
        a verbosity-appropriate default (4 for L1, 12 for L2, 24 for L3)
        so the cobweb stays legible at icon scale and rich at paper
        scale. Override for specific renders.
    theme
        ``"dark"`` (default) or ``"light"``. Light theme inverts the
        palette: cream background, dark ink, darker hue family at the
        same role-distinction; halo flips from black drop-shadow to
        soft white glow.
    snap_parafovea_to_ring
        If True (default), shift the dashed parafovea circle to sit on
        the nearest engine-ring ``r_outer`` so it visually anchors to
        the cobweb. Set False to render at the literal degree value.
    sector_mark_fraction
        How much of each ring's annulus the per-ring sector boundary
        marks span, centred on ``r_center`` (default 0.6). Lower values
        (e.g., 0.4) reduce visual collision between adjacent rings of
        different spoke counts at the cost of a more "floating" look.
    show_fovea_ticks
        Cardinal tick marks around the fovea circle (Scrutinizer default).
    accent
        Override the brand-tint accent (defaults to brand.colors.accent).
    background
        Override the background colour (defaults to brand.colors.background
        or ``#0a0a0f``).
    tint
        How strongly to brand-colour the grid. 0 = product-accurate
        cyan/blue (the default — the in-app palette *is* Scrutinizer's
        identity); 1 = fully brand-coloured. Tinting blurs the diagnostic
        role distinctions (rings vs spokes vs parafovea), so use ``tint``
        sparingly and only when the brand colour must dominate (e.g.,
        marketing thumbnails matched to a non-Scrutinizer site palette).
    show_labels
        Override the verbosity default. ``None`` (default) → labels only
        at verbosity 3.
    label_axis_deg
        Angle (degrees, 0 = right) along which to place degree labels at
        L3. Default 0° (rightward).
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
    if fovea_radius_deg <= 0 or parafovea_radius_deg <= fovea_radius_deg:
        raise ValueError("require 0 < fovea_radius_deg < parafovea_radius_deg")
    if n_spokes < 4:
        raise ValueError("n_spokes must be ≥ 4")
    if theme not in ("dark", "light"):
        raise ValueError(f"theme must be 'dark' or 'light'; got {theme!r}")

    t = _resolve(brand, tint=tint, theme=theme)
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
    parafovea_r_px = parafovea_radius_deg * px_per_deg

    # Scale the in-app constants (15-px ticks, 20/10 dash) to the viewBox
    # so the mark looks identical at any size. Reference scale: 512 px.
    scale = size / 512.0
    tick_len_px = max(2.0, 15.0 * scale)
    dash_len    = max(4.0, 20.0 * scale)
    gap_len     = max(2.0, 10.0 * scale)

    # Periphery ring step = foveaRadius (in-app: buildGrid(parafovea, foveaRadius)).
    ring_step_px = fovea_r_px

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" font-family="{escape(t["body_font"])}" '
        f'shape-rendering="geometricPrecision">'
    )

    # ─── halo-shadow filter — verbatim from svg-overlay.js initFilters() ──
    parts.append(
        '<defs>'
        '<filter id="halo-shadow" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feDropShadow dx="0" dy="0" stdDeviation="1.5" '
        f'flood-color="{t["halo_flood"]}"/>'
        '</filter>'
        '</defs>'
    )

    parts.append(f'<rect width="{size}" height="{size}" fill="{t["bg"]}"/>')

    # ═══ SEGMENT 3: Periphery (rings + 16 spokes) ═══════════════════════
    # svg-overlay.js buildGrid(): linear concentric rings, step = fovea
    # radius, starting at parafovea + step. NO halo filter applied.
    # Variable stroke width fades with eccentricity:
    #   width = max(0.3, 1.2 * (1 − normDist*0.8)),  normDist = r/(size*0.8)
    # Drawn first so fovea + parafovea overlay on top.
    if verbosity >= 2:
        edge_radius_for_fade = size * 0.8
        r = parafovea_r_px + ring_step_px
        max_rings = 64  # cap to avoid runaway at extreme eccentricity_max
        ring_count = 0
        while r <= R and ring_count < max_rings:
            norm_dist = min(1.0, r / edge_radius_for_fade)
            stroke_w = max(0.3, 1.2 * (1.0 - norm_dist * 0.8))
            parts.append(
                f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
                f'fill="none" stroke="{t["ring"]}" opacity="0.15" '
                f'stroke-width="{stroke_w:.2f}" '
                f'vector-effect="non-scaling-stroke"/>'
            )
            r += ring_step_px
            ring_count += 1

        # 16 radial spokes from parafovea outward to the SVG edge.
        for i in range(n_spokes):
            ang = (i / n_spokes) * 2.0 * math.pi
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            x0 = cx + cos_a * parafovea_r_px
            y0 = cy + sin_a * parafovea_r_px
            x1 = cx + cos_a * R
            y1 = cy + sin_a * R
            parts.append(
                f'<line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x1:.2f}" y2="{y1:.2f}" '
                f'stroke="{t["spoke"]}" opacity="0.15" stroke-width="1"/>'
            )

    # ═══ SEGMENT 2: Parafovea (dashed ring, halo-shadowed) ══════════════
    # svg-overlay.js: stroke '#a0c0ff' 1.5px opacity 0.7,
    # stroke-dasharray "20, 10", stroke-linecap "butt".
    if verbosity >= 2:
        parts.append('<g filter="url(#halo-shadow)">')
        parts.append(
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{parafovea_r_px:.2f}" '
            f'fill="none" stroke="{t["parafovea"]}" opacity="0.7" '
            f'stroke-width="1.5" stroke-dasharray="{dash_len:.1f},{gap_len:.1f}" '
            f'stroke-linecap="butt" vector-effect="non-scaling-stroke"/>'
        )
        parts.append('</g>')

    # ═══ SEGMENT 1: Fovea (unfilled circle + 12 outward ticks, halo) ════
    # svg-overlay.js: fovea circle fill='none' stroke '#ffffff' 1.5px
    # opacity 0.6. Ticks: 12 (every 30°), tickLen=15, white 1.5px opacity 0.8,
    # going OUTWARD from fovea radius.
    parts.append('<g filter="url(#halo-shadow)">')
    parts.append(
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{fovea_r_px:.2f}" '
        f'fill="none" stroke="{t["fovea"]}" opacity="0.6" '
        f'stroke-width="1.5" vector-effect="non-scaling-stroke"/>'
    )
    if show_fovea_ticks:
        tick_count = 12
        tick_inner = fovea_r_px
        tick_outer = fovea_r_px + tick_len_px
        for i in range(tick_count):
            ang = (i / tick_count) * 2.0 * math.pi
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            x0 = cx + cos_a * tick_inner
            y0 = cy + sin_a * tick_inner
            x1 = cx + cos_a * tick_outer
            y1 = cy + sin_a * tick_outer
            parts.append(
                f'<line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x1:.2f}" y2="{y1:.2f}" '
                f'stroke="{t["fovea"]}" stroke-width="1.5" opacity="0.8"/>'
            )
    parts.append('</g>')

    # ─── Eccentricity labels (L3 only) ───────────────────────────────
    if show_labels and verbosity >= 3:
        # Choose tick degrees: fovea + 5/10/20/30 — keep only those inside max.
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

    # ─── Footer caption (L3 only) ────────────────────────────────────
    if show_labels and verbosity >= 3:
        caption = (
            f"fovea {fovea_radius_deg:g}° · parafovea {parafovea_radius_deg:g}° · "
            f"{n_spokes} spokes · field shown ±{eccentricity_max:g}° "
            f"(port of svg-overlay.js)"
        )
        parts.append(
            f'<text x="{cx:.2f}" y="{size - 8:.2f}" fill="{t["muted"]}" '
            f'font-size="10" text-anchor="middle">{escape(caption)}</text>'
        )

    parts.append('</svg>')
    svg = "\n".join(parts)

    if out_path is not None:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(svg, encoding="utf-8")
    return svg


# ─── CLI ────────────────────────────────────────────────────────────

def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.foveal_overlay [opts] OUT.svg``.

    Examples
    --------
    Mark (favicon-scale)::

        python -m muriel.tools.diagrams.foveal_overlay \\
            --verbosity 1 --size 64 favicon.svg

    Wordmark (OG card) using a brand::

        python -m muriel.tools.diagrams.foveal_overlay \\
            --verbosity 2 --size 1200 --brand examples/scrutinizer-brand.toml \\
            og-card.svg

    Diagram (paper figure)::

        python -m muriel.tools.diagrams.foveal_overlay \\
            --verbosity 3 --size 720 --eccentricity-max 20 diagram.svg
    """
    import argparse
    ap = argparse.ArgumentParser(
        prog="python -m muriel.tools.diagrams.foveal_overlay",
        description="Render Scrutinizer's foveal mark — UI bullseye + Blauch et al. "
                    "2026 isotropic-cortical-sectors engine grid.",
    )
    ap.add_argument("output", help="output SVG path")
    ap.add_argument("--verbosity", type=int, default=2, choices=(1, 2, 3),
                    help="1=mark, 2=wordmark, 3=diagram (default 2)")
    ap.add_argument("--size", type=int, default=256,
                    help="square viewBox edge in px (default 256)")
    ap.add_argument("--eccentricity-max", type=float, default=12.0,
                    help="degrees from centre to SVG edge (default 12)")
    ap.add_argument("--fovea-deg", type=float, default=1.0,
                    help="foveal radius in degrees (default 1.0)")
    ap.add_argument("--parafovea-deg", type=float, default=5.0,
                    help="parafoveal radius in degrees (default 5.0)")
    ap.add_argument("--spokes", type=int, default=16,
                    help="number of radial spokes (default 16, matches svg-overlay.js)")
    ap.add_argument("--theme", default="dark", choices=("dark", "light"),
                    help="palette theme — dark (OLED, default) or light (cream)")
    ap.add_argument("--accent", default=None, help="override brand accent")
    ap.add_argument("--background", default=None, help="override background colour")
    ap.add_argument("--tint", type=float, default=0.0,
                    help="brand tint strength, 0=product-accurate (default), 1=fully brand-coloured")
    ap.add_argument("--no-ticks", action="store_true", help="suppress fovea cardinal ticks")
    ap.add_argument("--brand", default=None,
                    help="brand.toml to source colours from")
    args = ap.parse_args(argv)

    brand = None
    if args.brand:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(args.brand)

    foveal_overlay(
        verbosity=args.verbosity,
        size=args.size,
        eccentricity_max=args.eccentricity_max,
        fovea_radius_deg=args.fovea_deg,
        parafovea_radius_deg=args.parafovea_deg,
        n_spokes=args.spokes,
        theme=args.theme,
        show_fovea_ticks=not args.no_ticks,
        accent=args.accent,
        background=args.background,
        tint=args.tint,
        out_path=args.output,
        brand=brand,
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
