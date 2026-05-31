"""
V1 orientation columns — deterministic SVG rendering of cortical
orientation-selectivity topology.

Replaces the AI-generated `v1-orientation-columns.png` from Scrutinizer's
primer with a real generated artifact, in muriel's deterministic-SVG ethos.

Scientific basis:
    Hubel & Wiesel (1962) showed orientation selectivity in V1 simple
    cells. Bonhoeffer & Grinvald (1991, Nature) demonstrated the
    pinwheel topology with optical imaging — orientations vary smoothly
    across cortex around singular points where every orientation meets.
    This figure shows that topology directly: a hex grid of "columns",
    each rendered as an oriented stroke whose angle is set by a
    multi-pinwheel orientation field. Pinwheel centers are marked.

Run:
    python examples/gallery/v1-orientation-columns-demo.py
"""

from __future__ import annotations

import math
from pathlib import Path

# muriel OLED brand tokens (matches examples/muriel-brand.toml)
BG = "#0a0a0f"
BG_2 = "#0f1117"
FG = "#e6e4d2"          # cream, 15.42:1
FG_MUTED = "#b0b0c4"    # 9.27:1
ACCENT = "#50b4c8"      # teal, 8.19:1
ACCENT_INK = "#7dd4e4"  # 11.67:1

# Canvas
W, H = 1600, 900
TITLE_BAND = 110
FOOTER_BAND = 56
PLOT_PAD = 80

# Hex grid geometry
CELL = 32                     # center-to-center spacing
STROKE_LEN = 21               # oriented stroke length (px)
STROKE_W = 2.6
PINWHEEL_DOT_R = 6

# Pinwheel centers (fractional plot-area coords) and signs.
# Sign +1 = orientation increases CCW around the center;
# Sign -1 = decreases. Real V1 has equal numbers of each.
PINWHEELS = [
    (0.18, 0.30, +1),
    (0.42, 0.72, -1),
    (0.66, 0.32, +1),
    (0.85, 0.70, -1),
    (0.50, 0.20, -1),
]


def orientation_at(x: float, y: float, centers) -> float:
    """Smooth multi-pinwheel orientation field.

    Each pinwheel contributes an angle φ_i = sign_i * angle_to_center / 2
    (the /2 enforces V1's 180°-periodic topology). Contributions are
    weighted inversely by distance and combined via vector averaging on
    the doubled-angle representation, so periodicity is preserved.
    """
    sx = sy = 0.0
    for cx, cy, sign in centers:
        dx, dy = x - cx, y - cy
        d2 = dx * dx + dy * dy + 1e-3
        w = 1.0 / d2
        phi = sign * math.atan2(dy, dx)
        sx += w * math.cos(2 * phi)
        sy += w * math.sin(2 * phi)
    angle_doubled = math.atan2(sy, sx)
    return angle_doubled / 2.0  # back to 180°-periodic


def build_svg() -> str:
    plot_x = PLOT_PAD
    plot_y = TITLE_BAND
    plot_w = W - 2 * PLOT_PAD
    plot_h = H - TITLE_BAND - FOOTER_BAND - 20

    centers_px = [
        (plot_x + fx * plot_w, plot_y + fy * plot_h, sign)
        for fx, fy, sign in PINWHEELS
    ]
    centers_norm = [(fx, fy, sign) for fx, fy, sign in PINWHEELS]

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="V1 orientation columns — pinwheel topology, '
        f'a hex grid of oriented strokes whose angles vary smoothly '
        f'around five pinwheel singularities">'
    )

    # Style block — fonts + sizes. No paint-order halo: nothing overlaps
    # the data field. Default body weight is 500 (medium) not 400 — at
    # small sizes the system-sans regular weight reads as thin even at
    # 9:1 contrast. Hitting 8:1 is necessary, not sufficient.
    out.append(
        '<defs><style>'
        '.hero, .body, .muted { '
        'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", '
        'Helvetica, Arial, sans-serif; font-weight: 500; }'
        '.hero { font-weight: 700; }'
        '</style></defs>'
    )

    # Background
    out.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')

    # ── Title band ──────────────────────────────────────────────────
    out.append(
        f'<text x="{PLOT_PAD}" y="58" class="hero" '
        f'font-size="42" fill="{FG}">Orientation columns in V1</text>'
    )
    out.append(
        f'<text x="{PLOT_PAD}" y="92" class="body" '
        f'font-size="20" fill="{FG_MUTED}">'
        f'Each stroke = one column’s preferred orientation. '
        f'Smooth across cortex; singular at the marked centers.</text>'
    )

    # ── Top-right key: chirality of pinwheel singularities ──────────
    # Encoding: filled disk = CCW (+1), open ring = CW (−1). Dimensions
    # match the per-pinwheel glyphs below so the key visually equates.
    key_x = W - PLOT_PAD - 360
    key_y1, key_y2 = 56, 86
    out.append(
        f'<circle cx="{key_x}" cy="{key_y1}" r="{PINWHEEL_DOT_R}" '
        f'fill="{ACCENT_INK}" stroke="{BG}" stroke-width="2"/>'
    )
    out.append(
        f'<text x="{key_x + 16}" y="{key_y1 + 5}" class="body" '
        f'font-size="18" fill="{FG}">pinwheel singularity, CCW (+1)</text>'
    )
    out.append(
        f'<circle cx="{key_x}" cy="{key_y2}" r="{PINWHEEL_DOT_R}" '
        f'fill="none" stroke="{ACCENT_INK}" stroke-width="2.5"/>'
    )
    out.append(
        f'<text x="{key_x + 16}" y="{key_y2 + 5}" class="body" '
        f'font-size="18" fill="{FG}">pinwheel singularity, CW (−1)</text>'
    )

    # ── Hex grid of oriented strokes ────────────────────────────────
    row_step = CELL * math.sqrt(3) / 2
    n_rows = int(plot_h / row_step) - 1
    n_cols = int(plot_w / CELL) - 1
    inset_x = (plot_w - (n_cols - 1) * CELL) / 2
    inset_y = (plot_h - (n_rows - 1) * row_step) / 2

    half_len = STROKE_LEN / 2
    for r in range(n_rows):
        for c in range(n_cols):
            x = plot_x + inset_x + c * CELL + (CELL / 2 if r % 2 else 0)
            y = plot_y + inset_y + r * row_step
            if x > plot_x + plot_w - 8 or x < plot_x + 8:
                continue
            fx = (x - plot_x) / plot_w
            fy = (y - plot_y) / plot_h
            theta = orientation_at(fx, fy, centers_norm)
            dx = half_len * math.cos(theta)
            dy = half_len * math.sin(theta)
            out.append(
                f'<line x1="{x - dx:.1f}" y1="{y - dy:.1f}" '
                f'x2="{x + dx:.1f}" y2="{y + dy:.1f}" '
                f'stroke="{ACCENT}" stroke-width="{STROKE_W}" '
                f'stroke-linecap="round"/>'
            )

    # ── Pinwheel centers (chirality-encoded) ────────────────────────
    # Filled disk = sign +1 (CCW); open ring = sign −1 (CW). Same hue,
    # same radius — only fill/stroke differs, so the eye reads "same
    # kind of thing, opposite rotation" rather than two unrelated
    # marker classes.
    for cx_px, cy_px, sign in centers_px:
        if sign > 0:
            out.append(
                f'<circle cx="{cx_px:.1f}" cy="{cy_px:.1f}" '
                f'r="{PINWHEEL_DOT_R}" fill="{ACCENT_INK}" '
                f'stroke="{BG}" stroke-width="2"/>'
            )
        else:
            out.append(
                f'<circle cx="{cx_px:.1f}" cy="{cy_px:.1f}" '
                f'r="{PINWHEEL_DOT_R}" fill="none" '
                f'stroke="{ACCENT_INK}" stroke-width="2.5"/>'
            )

    # ── Footer ──────────────────────────────────────────────────────
    fy0 = H - FOOTER_BAND + 18
    out.append(
        f'<text x="{PLOT_PAD}" y="{fy0}" class="body" '
        f'font-size="17" fill="{FG}">'
        f'Deterministic SVG — multi-pinwheel orientation field over a hex '
        f'grid. Topology after Bonhoeffer &amp; Grinvald, '
        f'<tspan font-style="italic">Nature</tspan> 1991.</text>'
    )
    out.append(
        f'<text x="{W - PLOT_PAD}" y="{fy0}" text-anchor="end" '
        f'class="body" font-size="17" fill="{FG}">'
        f'muriel · examples/gallery/v1-orientation-columns-demo.py</text>'
    )

    out.append('</svg>')
    return '\n'.join(out)


if __name__ == "__main__":
    here = Path(__file__).resolve()
    out_dir = here.parent.parent.parent / "docs"
    svg_path = out_dir / "v1-orientation-columns.svg"
    svg_path.write_text(build_svg(), encoding="utf-8")
    print(f"wrote {svg_path} ({svg_path.stat().st_size:,} bytes)")
