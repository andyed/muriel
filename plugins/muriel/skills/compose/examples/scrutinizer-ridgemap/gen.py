"""Scrutinizer-branded ridgemap composition.

The eye is the data. Each row of the ridgemap is a horizontal slice
through a 2D scalar field whose isovalue contour traces an almond
(*vesica piscis*) — so the stacked ridges, read top to bottom, sweep
out the eye outline themselves. A pupil bump at centre adds the
characteristic spike on the middle rows; a faint iris ring adds a
secondary shoulder.

Backdrop is the concentric circle grid alone (Blauch-style log-spaced
cortical-sector rings), brand-tinted but stripped of fovea / parafovea
/ tick decoration — the rings are scaffold, the ridges are figure.

Runs from a checkout::

    PYTHONPATH=. python plugins/muriel/skills/compose/examples/scrutinizer-ridgemap/gen.py

Writes ``output/scrutinizer-ridgemap.svg`` plus a PNG raster if
cairosvg is importable.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from muriel.layout import BBox
from muriel.spatial import ridgemap


# ─── Scrutinizer palette ────────────────────────────────────────────
# Excerpts from examples/scrutinizer-brand.toml — contrast values are
# against #0a0a0f. Every text/stroke clears muriel's 8:1 floor.
BG = "#0a0a0f"
INK = "#e0e0ec"          # 14.42:1
DIM = "#b0b0c8"          # 8.93:1
ACCENT = "#ff9933"       # brand orange  9.28:1
ACCENT_HI = "#ffb366"    # 11.19:1


WIDTH = 1600
HEIGHT = 1000
EYE_W_FRAC = 0.86        # eye width as fraction of column count
EYE_H_FRAC = 0.82        # eye height as fraction of row count


def eye_field(n_rows: int = 100, n_cols: int = 320) -> list[list[float]]:
    """2D scalar field whose top-down ridges trace an eye outline.

    A *vesica piscis* — the intersection of two circles whose centres
    sit above and below the canvas vertical centre. Inside the lens
    the field rises smoothly toward the centre; outside it is zero.
    The row-wise peaks span wider in the middle rows than at the top
    and bottom rows, so the stacked-ridge envelope **is** the eye.

    Geometry: two arcs of radius ``R`` centred at ``(cx, cy ± d)``.
    At ``y = cy`` the lens has half-width ``sqrt(R**2 - d**2) =
    eye_w/2``; at ``y = cy ± eye_h/2`` the lens closes (width = 0),
    which requires ``R = d + eye_h/2``. Solving gives
    ``d = ((eye_w/2)**2 - (eye_h/2)**2) / eye_h``.

    Per-row profile is shaped to crown at the lens centre and taper
    to zero at the lens edges, which keeps each ridge polyline
    smooth (no flat plateau, no sharp shoulders).
    """
    cx = n_cols / 2.0
    cy = n_rows / 2.0
    eye_w = EYE_W_FRAC * n_cols
    eye_h = EYE_H_FRAC * n_rows
    half_w = eye_w / 2.0
    half_h = eye_h / 2.0
    d = (half_w * half_w - half_h * half_h) / eye_h
    R = d + half_h

    # Pupil / iris — sized off lens dimensions. Amplitudes are kept
    # well below the lens-peak post-normalisation (~0.16 at mid-row
    # centre) so they read as wrinkles on the central rows rather
    # than swamping the lens outline.
    iris_r = min(eye_w, eye_h) * 0.18
    iris_sigma = iris_r * 0.45
    pupil_sigma = min(eye_w, eye_h) * 0.06
    iris_amp = 0.025
    pupil_amp = 0.080

    field: list[list[float]] = []
    for ri in range(n_rows):
        y = ri
        row: list[float] = []
        for ci in range(n_cols):
            x = ci
            d_up = math.hypot(x - cx, y - (cy + d))
            d_dn = math.hypot(x - cx, y - (cy - d))
            depth = R - max(d_up, d_dn)
            if depth <= 0:
                row.append(0.0)
                continue
            row_depth_center = R - math.hypot(0.0, y - (cy + d))
            row_depth_center = max(row_depth_center, 1e-6)
            t = depth / row_depth_center           # 0 at edge, 1 at row centre
            # Flat-top crown so each lens row bulges by ~full amplitude
            # across most of its width and tapers only at the lens
            # boundary. The eye outline then comes from the horizontal
            # extent of each row's bulge — narrow at top/bottom rows,
            # wide at mid rows — tracing a real almond.
            v = math.exp(-((1.0 - t) * 0.9) ** 4)
            r_polar = math.hypot(x - cx, y - cy)
            v += iris_amp * math.exp(
                -((r_polar - iris_r) / iris_sigma) ** 2
            )
            v += pupil_amp * math.exp(
                -(r_polar / pupil_sigma) ** 2
            )
            row.append(v)
        field.append(row)
    return field


def circle_grid(
    cx: float, cy: float, r_max: float, *,
    color: str = ACCENT,
    n_rings: int = 12,
    cmf_a: float = 2.78,
) -> list[str]:
    """Blauch-style log-spaced concentric rings — the cortical-sector
    grid alone, no fovea / parafovea / spokes / ticks. Pure scaffold.

    Spacing follows ``muriel.tools.diagrams.foveal_overlay``'s engine
    layout: ``r_center = exp(w_min + n·w_step) − a``, with
    ``w_min = log(a)`` and ``w_step = log(r_max/a + 1) / (n_rings − 1)``.
    Tight near centre, expanding outward — the visual signature of
    cortical magnification.
    """
    a = cmf_a
    w_min = math.log(a)
    w_step = math.log(r_max / a + 1.0) / max(1, n_rings - 1)
    out: list[str] = []
    for i in range(n_rings):
        r = math.exp(w_min + i * w_step) - a
        if r < 3.0 or r > r_max + 0.5:
            continue
        # Slight outward fade so the inner rings carry more weight.
        op = 0.20 - (i / max(1, n_rings - 1)) * 0.10
        out.append(
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}" '
            f'fill="none" stroke="{color}" stroke-width="0.5" '
            f'opacity="{op:.3f}"/>'
        )
    return out


def compose() -> str:
    # Layer 1 — circle grid scaffold (centred, full-height).
    cx = WIDTH / 2.0
    cy = HEIGHT / 2.0
    r_max = min(WIDTH, HEIGHT) * 0.46
    rings = circle_grid(cx, cy, r_max, color=ACCENT, n_rings=12)

    # Layer 2 — ridgemap of the eye field, with a mirror twist: every
    # row's bulge points TOWARD the canvas vertical midline (rows
    # above mid bulge down, rows below mid bulge up). The bulges
    # cross over each other near the middle and the lens fills as a
    # closed almond — no horizontal slit where opposing halves meet.
    # The pupil/iris bumps ride along and contribute a faint inner
    # figure (the eyeball) near the centre.
    field = eye_field(n_rows=110, n_cols=360)
    ridge_cv = BBox(72, 132, WIDTH - 72, HEIGHT - 112)
    rm = ridgemap(field, canvas=ridge_cv, margin=0.02, amplitude=14.0)
    mid_y = (ridge_cv.y0 + ridge_cv.y1) / 2.0
    ridges: list[str] = []
    for r in rm.ridges:
        sign = +1.0 if r.baseline_y < mid_y else -1.0
        pts: list[str] = []
        for x, y in r.points:
            disp = r.baseline_y - y          # ≥ 0 (upward by construction)
            new_y = r.baseline_y + sign * disp
            pts.append(f"{x:.2f},{new_y:.2f}")
        ridges.append(
            f'  <polyline points="{" ".join(pts)}" fill="none" '
            f'stroke="{ACCENT}" stroke-width="0.95" '
            f'stroke-linejoin="round" stroke-linecap="round" '
            f'opacity="0.96"/>'
        )

    # Chrome
    title = (
        f'  <text x="48" y="58" fill="{INK}" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" '
        f'font-size="22" font-weight="600" letter-spacing="0.04em">'
        f'SCRUTINIZER &#183; the eye is the data</text>'
    )
    subtitle = (
        f'  <text x="48" y="84" fill="{ACCENT_HI}" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" '
        f'font-size="13" opacity="0.92">'
        f'110 rows &#215; 360 cols &#183; vesica-piscis lens with '
        f'pupil + iris core &#183; bottom half mirrored to close '
        f'the almond</text>'
    )
    footer_l = (
        f'  <text x="48" y="{HEIGHT - 28}" fill="{DIM}" '
        f'font-family="ui-monospace,monospace" font-size="11" '
        f'opacity="0.88">'
        f'muriel.spatial.ridgemap(eye_field) on Blauch '
        f'log-spaced ring scaffold</text>'
    )
    footer_r = (
        f'  <text x="{WIDTH - 48}" y="{HEIGHT - 28}" fill="{DIM}" '
        f'font-family="ui-monospace,monospace" font-size="11" '
        f'opacity="0.88" text-anchor="end">'
        f'brand: examples/scrutinizer-brand.toml</text>'
    )

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" '
        'preserveAspectRatio="xMidYMid meet">',
        f'  <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" '
        f'fill="{BG}"/>',
        '  <g id="circle-grid">',
        *rings,
        '  </g>',
        '  <g id="ridgemap-eye">',
        *ridges,
        '  </g>',
        title,
        subtitle,
        footer_l,
        footer_r,
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def main() -> int:
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    svg = compose()
    svg_path = out_dir / "scrutinizer-ridgemap.svg"
    svg_path.write_text(svg, encoding="utf-8")
    print(f"wrote {svg_path}", file=sys.stderr)
    try:
        import cairosvg  # type: ignore
    except ImportError:
        print("cairosvg not installed — skipping PNG", file=sys.stderr)
        return 0
    png_path = out_dir / "scrutinizer-ridgemap.png"
    cairosvg.svg2png(
        url=str(svg_path), write_to=str(png_path), output_width=2400
    )
    print(f"wrote {png_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
