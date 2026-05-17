"""Scrutinizer-branded ridgemap composition.

Layers three muriel.spatial primitives into a single SVG, branded
against `examples/scrutinizer-brand.toml`:

1. **3-point perspective grid** (`grid("3pt", …)`) as the deep-space
   scaffold — the "fanciest grid" with three vanishing points.
2. **Foveal overlay** (`foveal_overlay(verbosity=2, …)`) — Scrutinizer's
   eye-pattern mark, the L2 wordmark, at the visual centre with a brand
   tint.
3. **Ridgemap** (`ridgemap(field, …)`) — synthetic gaze-density field
   (56 successive periods × 240 phase bins) rendered in Scrutinizer
   orange. Line-art mode (`fill=None`-equivalent inline emission) so
   the eye reads through the stack rather than being occluded by it.

Runs from a checkout: ``python -m plugins.muriel.skills.compose.examples.scrutinizer-ridgemap.gen``
or directly: ``python plugins/muriel/skills/compose/examples/scrutinizer-ridgemap/gen.py``.
Writes `output/scrutinizer-ridgemap.svg` plus a PNG raster if cairosvg
is importable.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

from muriel.layout import BBox
from muriel.spatial import grid, ridgemap


# ─── Scrutinizer palette ────────────────────────────────────────────
# Excerpts from examples/scrutinizer-brand.toml — contrast values are
# against #0a0a0f. Every text and stroke colour below clears muriel's
# 8:1 floor.
BG = "#0a0a0f"
INK = "#e0e0ec"          # 14.42:1
DIM = "#b0b0c8"          # 8.93:1
ACCENT = "#ff9933"       # brand orange  9.28:1
ACCENT_HI = "#ffb366"    # higher-contrast orange 11.19:1
TEAL = "#7dd4e4"         # gaze teal     11.67:1
BLUE = "#80a0ff"         # 7.62:1 (used as scaffold accent — non-text)


WIDTH = 1600
HEIGHT = 1000
EYE_SIZE = 880


def gaze_density_field(
    n_rows: int = 56, n_cols: int = 240, seed: int = 2026
) -> list[list[float]]:
    """Synthetic gaze-density field for a Scrutinizer-flavoured demo.

    Each row is one time bin; cols are screen-x bins. A primary
    fixation drifts via a damped random walk; a secondary attractor
    fires on ~35% of rows (saccade events). Low-amplitude noise floor.
    Deterministic from ``seed``.
    """
    rng = random.Random(seed)
    field: list[list[float]] = []
    primary = 0.50 * n_cols
    primary_vel = 0.0
    pri_sigma = 0.045 * n_cols
    sec_sigma = 0.055 * n_cols
    for _ in range(n_rows):
        primary_vel += (rng.random() - 0.5) * 0.6
        primary_vel *= 0.85
        primary += primary_vel
        if primary < 0.22 * n_cols:
            primary = 0.22 * n_cols
            primary_vel = abs(primary_vel)
        elif primary > 0.78 * n_cols:
            primary = 0.78 * n_cols
            primary_vel = -abs(primary_vel)
        has_sacc = rng.random() < 0.35
        sec_center = n_cols * (0.28 + 0.46 * rng.random())
        sec_amp = (0.55 + 0.45 * rng.random()) if has_sacc else 0.0
        pri_amp = 2.30 + 0.60 * rng.random()
        row: list[float] = []
        for ci in range(n_cols):
            d_pri = (ci - primary) / pri_sigma
            v = pri_amp * math.exp(-d_pri * d_pri)
            if sec_amp:
                d_sec = (ci - sec_center) / sec_sigma
                v += sec_amp * math.exp(-d_sec * d_sec)
            v += (rng.random() - 0.5) * 0.06
            row.append(v)
        field.append(row)
    return field


def eye_pattern(
    cx: float, cy: float, size: float, *,
    ring_color: str = ACCENT,
    spoke_color: str = TEAL,
    fovea_color: str = INK,
    parafovea_color: str = ACCENT_HI,
    n_rings: int = 9,
    n_spokes: int = 24,
) -> list[str]:
    """Scrutinizer-style eye pattern as inline SVG fragments.

    Echoes `muriel.tools.diagrams.foveal_overlay` (Blauch et al. 2026
    isotropic-sector layout) but with locally controlled opacities so
    the pattern reads at composition scale instead of brand-mark scale.
    Log-spaced concentric rings + 24 radial spokes + dashed parafovea +
    centred fovea with cardinal ticks.
    """
    r_max = size / 2.0
    out: list[str] = []
    # Outer halo to anchor the eye on a busy backdrop.
    out.append(
        f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_max:.1f}" '
        f'fill="none" stroke="{ring_color}" stroke-width="0.6" '
        f'opacity="0.35"/>'
    )
    # Log-spaced engine rings — tight near fovea, expanding outward.
    a = 2.78
    w_min = math.log(a)
    w_step = math.log(r_max / a + 1.0) / max(1, (n_rings - 1))
    for i in range(n_rings):
        r = math.exp(w_min + i * w_step) - a
        if r < 4:
            continue
        op = 0.45 - (i / max(1, n_rings - 1)) * 0.20  # fainter outward
        out.append(
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="none" stroke="{ring_color}" stroke-width="0.7" '
            f'opacity="{op:.3f}"/>'
        )
    # Radial spokes — equally distributed; clipped at outer halo.
    inner_r = r_max * 0.08
    for k in range(n_spokes):
        theta = (k / n_spokes) * 2 * math.pi
        x0 = cx + math.cos(theta) * inner_r
        y0 = cy + math.sin(theta) * inner_r
        x1 = cx + math.cos(theta) * r_max
        y1 = cy + math.sin(theta) * r_max
        out.append(
            f'    <line x1="{x0:.1f}" y1="{y0:.1f}" '
            f'x2="{x1:.1f}" y2="{y1:.1f}" '
            f'stroke="{spoke_color}" stroke-width="0.5" '
            f'opacity="0.30"/>'
        )
    # Dashed parafovea — anchors the eye semantically at ~5/14 of r_max.
    para_r = r_max * (5.0 / 14.0)
    out.append(
        f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{para_r:.1f}" '
        f'fill="none" stroke="{parafovea_color}" stroke-width="1.6" '
        f'stroke-dasharray="14 8" opacity="0.85"/>'
    )
    # Foveal disc — bright unfilled circle + 12 cardinal ticks.
    fov_r = r_max * (1.0 / 14.0)
    out.append(
        f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{fov_r:.1f}" '
        f'fill="none" stroke="{fovea_color}" stroke-width="1.8" '
        f'opacity="0.95"/>'
    )
    tick_inner = fov_r * 1.0
    tick_outer = fov_r * 1.7
    for k in range(12):
        theta = (k / 12) * 2 * math.pi
        ct, st = math.cos(theta), math.sin(theta)
        out.append(
            f'    <line x1="{cx + ct * tick_inner:.1f}" '
            f'y1="{cy + st * tick_inner:.1f}" '
            f'x2="{cx + ct * tick_outer:.1f}" '
            f'y2="{cy + st * tick_outer:.1f}" '
            f'stroke="{fovea_color}" stroke-width="1.6" '
            f'opacity="0.95"/>'
        )
    return out


def compose() -> str:
    # Layer 1 — 3-point perspective scaffold
    grid_cv = BBox(0, 0, WIDTH, HEIGHT)
    g = grid(
        "3pt",
        grid_cv,
        horizon_y=HEIGHT * 0.5,
        vp_offsets=(-1.8, 1.8, -2.6),
        rows=7,
        cols=10,
    )
    grid_lines: list[str] = []
    for ln in g.lines:
        is_horizon = ln.role == "horizon"
        color = BLUE if is_horizon else TEAL
        sw = 0.9 if is_horizon else 0.55
        op = 0.50 if is_horizon else max(0.18, ln.weight * 0.48)
        grid_lines.append(
            f'  <line x1="{ln.x0:.2f}" y1="{ln.y0:.2f}" '
            f'x2="{ln.x1:.2f}" y2="{ln.y1:.2f}" '
            f'stroke="{color}" stroke-width="{sw}" '
            f'opacity="{op:.3f}" data-role="{ln.role}"/>'
        )

    # Layer 2 — Scrutinizer eye pattern (Blauch-style cortical-sector
    # cobweb + fovea + ticks + dashed parafovea, in brand orange/teal).
    eye_fragments = eye_pattern(
        cx=WIDTH / 2, cy=HEIGHT / 2, size=EYE_SIZE,
        ring_color=ACCENT, spoke_color=TEAL,
        fovea_color=INK, parafovea_color=ACCENT_HI,
        n_rings=10, n_spokes=24,
    )

    # Layer 3 — Ridgemap of synthetic gaze density, line-art mode so
    # the eye reads through the ridges (data scrutinising the eye).
    field = gaze_density_field()
    ridge_cv = BBox(72, 132, WIDTH - 72, HEIGHT - 112)
    rm = ridgemap(field, canvas=ridge_cv, margin=0.02)
    ridges: list[str] = []
    for r in rm.ridges:
        poly = " ".join(f"{x:.2f},{y:.2f}" for x, y in r.points)
        ridges.append(
            f'  <polyline points="{poly}" fill="none" '
            f'stroke="{ACCENT}" stroke-width="1.15" '
            f'stroke-linejoin="round" stroke-linecap="round" '
            f'opacity="0.95"/>'
        )

    # Chrome
    title = (
        f'  <text x="48" y="58" fill="{INK}" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" '
        f'font-size="22" font-weight="600" letter-spacing="0.04em">'
        f'SCRUTINIZER &#183; gaze field</text>'
    )
    subtitle = (
        f'  <text x="48" y="84" fill="{ACCENT_HI}" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" '
        f'font-size="13" opacity="0.92">'
        f'56 successive periods &#215; 240 phase bins &#183; '
        f'foveal overlay (L3) on 3-point perspective scaffold</text>'
    )
    footer_l = (
        f'  <text x="48" y="{HEIGHT - 28}" fill="{DIM}" '
        f'font-family="ui-monospace,monospace" font-size="11" '
        f'opacity="0.88">'
        f'muriel.spatial: grid("3pt") + foveal_overlay(L3) + '
        f'ridgemap(gaze_density)</text>'
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
        '  <g id="scaffold-3pt">',
        *grid_lines,
        '  </g>',
        '  <g id="eye-pattern">',
        *eye_fragments,
        '  </g>',
        '  <g id="ridgemap-gaze">',
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
