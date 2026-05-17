#!/usr/bin/env python3
"""muriel.spatial — perspective grids for depth scaffolding.

Why this exists
---------------
Floating text in 3D space without a perspective scaffold reads as
stacked planes — there is no felt depth, just layers. The perspective
grid is the cure: a few well-placed receding lines give the visual
system enough cues (vanishing-point convergence, foreshortened
transversals, horizon anchor) to lock the scene into a single
volumetric space.

Lineage: Alberti's *De pictura* (1435) and the *costruzione
legittima*; Dürer's perspective machine (1525); architect's
blueprint axonometrics; Muriel Cooper's MIT Visible Language Workshop
(receding planes of type as an information environment); the
Robertson / Mackinlay / Card *Information Visualizer* cone trees and
the Dumais / Cockburn / Robertson *Data Mountain* at MSR (using
spatial memory as an indexing primitive); and the Tron / synthwave
horizon-to-VP grid that re-popularised one-point perspective in the
1980s.

This module is the 2D static scaffold (SVG, paper, blog). It is
designed to share its coordinate system with a forthcoming
``spatial.typeset_scene()`` that consumes the same grid as a 3D
anchor space for DOM-text-in-3D via CSS3DRenderer — so the same
``("vp", "left", 3)`` or ``("grid", row, col, depth)`` anchor names
mean the same place in both the printed figure and the interactive
fly-through.

Core ideas
----------
``grid(mode, canvas, ...)`` returns a ``PerspectiveGrid`` carrying
its vanishing points plus a flat list of canvas-clipped grid lines.
The result emits a complete SVG document via ``.svg()``. Supported
modes:

* ``"1pt"`` — single VP on horizon (corridor / Tron horizon).
* ``"2pt"`` — two VPs on horizon (architectural cube corner).
* ``"3pt"`` — two VPs on horizon + one vertical VP (looking up at a
  tower, or down into a pit).
* ``"iso"`` — parallel isometric, three axes at 30° / 150° / 90°,
  no convergence.

``ridgemap(field, canvas, ...)`` is the sibling primitive: where
``grid()`` scaffolds *space*, ``ridgemap()`` scaffolds *scalar
fields*. Each row of a 2D iterable becomes a horizontal polyline,
rows stack top-to-bottom, front ridges occlude back ridges via a
baseline-closed polygon fill — the Joy Division *Unknown Pleasures*
look (Harold Craft's 1970 PSR B1919+21 successive-period plot;
Wilke's *ggridges* in 2016 for the statistical-density version).

Defaults are tuned so ``grid("1pt", BBox(0, 0, 1200, 700)).svg()``
produces a readable Tron-style grid out of the box — horizon at
mid-height, VP at canvas centre, line opacity fading toward the
horizon. Override ``horizon_y`` to raise or lower the eye level;
override ``vp_offsets`` for 2pt / 3pt to widen or narrow the
convergence cone.

Usage
-----
    from muriel.spatial import grid
    from muriel.layout import BBox

    g = grid("1pt", canvas=BBox(0, 0, 1200, 700))
    open("grid.svg", "w").write(g.svg(stroke="#7fdfff", bg="#0a0a14"))

    g2 = grid("2pt", canvas=BBox(0, 0, 1200, 700),
              vp_offsets=(-1.5, 1.5))
    for vp in g2.vanishing_points:
        print(vp.name, vp.x, vp.y)

CLI
---
    python -m muriel.spatial --demo                # 2x2 of all modes
    python -m muriel.spatial --demo --mode 1pt     # one mode, full size
    python -m muriel.spatial --selftest            # assertion suite
"""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

from muriel.layout import BBox

__all__ = [
    "BBox",
    "VanishingPoint",
    "GridLine",
    "PerspectiveGrid",
    "Ridge",
    "RidgeMap",
    "SpatialError",
    "grid",
    "ridgemap",
]


class SpatialError(ValueError):
    """Raised when grid parameters are inconsistent (unknown mode, etc.)."""


# ─── Result primitives ──────────────────────────────────────────────


@dataclass(frozen=True)
class VanishingPoint:
    """A point (in canvas coordinates) where a set of parallel lines converge.

    May lie outside the canvas — typical for 2-point and 3-point.
    """

    x: float
    y: float
    name: str = ""


@dataclass(frozen=True)
class GridLine:
    """A grid line segment, already clipped to the canvas.

    ``role`` is one of: ``horizon``, ``orthogonal-floor``,
    ``orthogonal-ceiling``, ``transversal-floor``,
    ``transversal-ceiling``, ``from-vp-left``, ``from-vp-right``,
    ``from-vp-z``, ``vertical``, ``iso-x``, ``iso-y``, ``iso-z``.
    ``weight`` is opacity ∈ [0, 1] — fades toward the horizon when
    ``fade_to_horizon=True``.
    """

    x0: float
    y0: float
    x1: float
    y1: float
    role: str
    weight: float = 1.0


@dataclass(frozen=True)
class PerspectiveGrid:
    """Result of ``grid(...)`` — vanishing points + clipped lines + SVG emit."""

    mode: str
    canvas: BBox
    horizon_y: Optional[float]
    vanishing_points: Tuple[VanishingPoint, ...]
    lines: Tuple[GridLine, ...]

    def svg(
        self,
        stroke: str = "#7fdfff",
        stroke_width: float = 0.6,
        bg: Optional[str] = "#0a0a14",
        show_vps: bool = False,
        vp_fill: str = "#ff5fa2",
        horizon_stroke: Optional[str] = "#ff5fa2",
        horizon_width: Optional[float] = 1.0,
    ) -> str:
        """Render as a standalone, self-contained SVG document.

        Defaults produce a Tron-style cyan-on-near-black with a magenta
        horizon line; set ``bg=None`` to omit the background rect, and
        ``horizon_stroke=None`` to leave the horizon the same colour as
        the rest of the grid.
        """
        cv = self.canvas
        out: list[str] = [
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="{_fmt(cv.x0)} {_fmt(cv.y0)} '
            f'{_fmt(cv.width)} {_fmt(cv.height)}" '
            'preserveAspectRatio="xMidYMid meet">'
        ]
        if bg:
            out.append(
                f'  <rect x="{_fmt(cv.x0)}" y="{_fmt(cv.y0)}" '
                f'width="{_fmt(cv.width)}" height="{_fmt(cv.height)}" '
                f'fill="{bg}"/>'
            )
        out.append('  <g stroke-linecap="butt" fill="none">')
        for ln in self.lines:
            is_horizon = ln.role == "horizon"
            s = horizon_stroke if (is_horizon and horizon_stroke) else stroke
            w = horizon_width if (is_horizon and horizon_width) else stroke_width
            out.append(
                f'    <line x1="{_fmt(ln.x0)}" y1="{_fmt(ln.y0)}" '
                f'x2="{_fmt(ln.x1)}" y2="{_fmt(ln.y1)}" '
                f'stroke="{s}" stroke-width="{_fmt(w)}" '
                f'opacity="{ln.weight:.3f}" '
                f'data-role="{ln.role}"/>'
            )
        out.append("  </g>")
        if show_vps:
            out.append(f'  <g fill="{vp_fill}" stroke="none">')
            for vp in self.vanishing_points:
                out.append(
                    f'    <circle cx="{_fmt(vp.x)}" cy="{_fmt(vp.y)}" r="3.5">'
                    f'<title>VP: {vp.name}</title></circle>'
                )
            out.append("  </g>")
        out.append("</svg>")
        return "\n".join(out) + "\n"


# ─── Helpers ────────────────────────────────────────────────────────


def _fmt(v: float) -> str:
    """Compact numeric formatter for SVG output."""
    if v == int(v):
        return str(int(v))
    return f"{v:.2f}"


def _clip_line(
    x0: float, y0: float, x1: float, y1: float, bbox: BBox
) -> Optional[Tuple[float, float, float, float]]:
    """Liang-Barsky clip a line segment to ``bbox``.

    Returns the clipped endpoints, or None if the segment is entirely
    outside the bbox.
    """
    dx = x1 - x0
    dy = y1 - y0
    p = (-dx, dx, -dy, dy)
    q = (x0 - bbox.x0, bbox.x1 - x0, y0 - bbox.y0, bbox.y1 - y0)
    u1, u2 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return None
        else:
            t = qi / pi
            if pi < 0:
                if t > u1:
                    u1 = t
            else:
                if t < u2:
                    u2 = t
    if u1 > u2:
        return None
    return (x0 + u1 * dx, y0 + u1 * dy, x0 + u2 * dx, y0 + u2 * dy)


def _depth_weight(distance_to_horizon: float, max_distance: float) -> float:
    """Opacity falloff for lines approaching the horizon.

    Uses a soft sqrt curve so near-horizon lines fade but stay visible
    enough to read as part of the grid (we still want them to suggest
    infinity, not vanish).
    """
    if max_distance <= 0:
        return 1.0
    d = max(0.0, distance_to_horizon) / max_distance
    return max(0.15, math.sqrt(d))


# ─── Public API ─────────────────────────────────────────────────────


def grid(
    mode: str,
    canvas: BBox,
    *,
    horizon_y: Optional[float] = None,
    vp_offsets: Optional[Sequence[float]] = None,
    rows: int = 8,
    cols: int = 12,
    iso_step: float = 40.0,
    show_ceiling: bool = True,
    fade_to_horizon: bool = True,
) -> PerspectiveGrid:
    """Build a perspective grid.

    Parameters
    ----------
    mode : {"1pt", "2pt", "3pt", "iso"}
        Which perspective construction.
    canvas : BBox
        The viewport in SVG user units (y grows downward).
    horizon_y : float, optional
        Y-coordinate of the horizon. Defaults to ``canvas`` vertical
        centre. Ignored for ``"iso"``.
    vp_offsets : sequence of float, optional
        Mode-specific VP placement:

        * **1pt** — ``(dx,)`` shifts the single VP horizontally by
          ``dx * canvas.width`` from centre (default: 0).
        * **2pt** — ``(dx_left, dx_right)`` places the two horizon
          VPs at ``cx + dx * canvas.width`` (default: ``(-1.5, 1.5)``,
          well off canvas).
        * **3pt** — ``(dx_left, dx_right, dy_z)`` adds a vertical VP
          at ``cy + dy_z * canvas.height`` (default:
          ``(-1.5, 1.5, -3.0)`` — high above the canvas, "looking up").
    rows : int
        Number of transversals (1pt) or fan rays per VP (2pt / 3pt).
    cols : int
        Number of orthogonals (1pt) or fan rays per VP (2pt / 3pt).
    iso_step : float
        Spacing in canvas units between isometric grid lines.
    show_ceiling : bool
        For 1pt and 2pt, also draw the mirrored ceiling grid.
    fade_to_horizon : bool
        Opacity tapers as transversals approach the horizon — gives
        the felt-infinite-distance cue without needing extra lines.

    Returns
    -------
    PerspectiveGrid
    """
    if mode == "iso":
        return _grid_iso(canvas, iso_step)
    if horizon_y is None:
        horizon_y = (canvas.y0 + canvas.y1) / 2.0
    if mode == "1pt":
        return _grid_1pt(
            canvas, horizon_y, vp_offsets, rows, cols, show_ceiling, fade_to_horizon
        )
    if mode == "2pt":
        return _grid_2pt(
            canvas, horizon_y, vp_offsets, rows, cols, show_ceiling, fade_to_horizon
        )
    if mode == "3pt":
        return _grid_3pt(
            canvas, horizon_y, vp_offsets, rows, cols, fade_to_horizon
        )
    raise SpatialError(
        f"Unknown grid mode: {mode!r}. Expected 1pt | 2pt | 3pt | iso."
    )


# ─── Per-mode constructors ──────────────────────────────────────────


def _grid_1pt(
    canvas: BBox,
    horizon_y: float,
    vp_offsets: Optional[Sequence[float]],
    rows: int,
    cols: int,
    show_ceiling: bool,
    fade_to_horizon: bool,
) -> PerspectiveGrid:
    cx = (canvas.x0 + canvas.x1) / 2.0
    vp_x = cx
    if vp_offsets and len(vp_offsets) >= 1:
        vp_x = cx + vp_offsets[0] * canvas.width
    vp = VanishingPoint(vp_x, horizon_y, "center")
    lines: list[GridLine] = [
        GridLine(canvas.x0, horizon_y, canvas.x1, horizon_y, "horizon", 0.5)
    ]

    # Floor orthogonals — fan rays from VP through evenly-spaced points
    # along an extended bottom range so rays at the edges leave through
    # the side walls instead of bunching at the bottom corners.
    extended_left = canvas.x0 - canvas.width * 0.5
    extended_right = canvas.x1 + canvas.width * 0.5
    extended_width = extended_right - extended_left
    n_orth = cols * 2 + 1
    for i in range(n_orth):
        bx = extended_left + i * extended_width / (n_orth - 1)
        seg = _clip_line(vp.x, vp.y, bx, canvas.y1, canvas)
        if seg:
            lines.append(GridLine(*seg, "orthogonal-floor", 1.0))

    # Floor transversals — at screen y = horizon_y + K/i, K = floor height.
    # Geometric in 1/distance, matches what a real ground plane projects to.
    floor_h = canvas.y1 - horizon_y
    if floor_h > 0:
        for i in range(1, rows + 1):
            ty = horizon_y + floor_h / i
            if ty < horizon_y + 0.5 or ty > canvas.y1 + 0.5:
                continue
            w = _depth_weight(ty - horizon_y, floor_h) if fade_to_horizon else 1.0
            lines.append(
                GridLine(canvas.x0, ty, canvas.x1, ty, "transversal-floor", w)
            )

    # Ceiling mirror
    ceil_h = horizon_y - canvas.y0
    if show_ceiling and ceil_h > 0:
        for i in range(n_orth):
            tx = extended_left + i * extended_width / (n_orth - 1)
            seg = _clip_line(vp.x, vp.y, tx, canvas.y0, canvas)
            if seg:
                lines.append(GridLine(*seg, "orthogonal-ceiling", 1.0))
        for i in range(1, rows + 1):
            ty = horizon_y - ceil_h / i
            if ty < canvas.y0 - 0.5 or ty > horizon_y - 0.5:
                continue
            w = _depth_weight(horizon_y - ty, ceil_h) if fade_to_horizon else 1.0
            lines.append(
                GridLine(canvas.x0, ty, canvas.x1, ty, "transversal-ceiling", w)
            )

    return PerspectiveGrid(
        mode="1pt",
        canvas=canvas,
        horizon_y=horizon_y,
        vanishing_points=(vp,),
        lines=tuple(lines),
    )


def _grid_2pt(
    canvas: BBox,
    horizon_y: float,
    vp_offsets: Optional[Sequence[float]],
    rows: int,
    cols: int,
    show_ceiling: bool,
    fade_to_horizon: bool,
) -> PerspectiveGrid:
    if vp_offsets is None or len(vp_offsets) < 2:
        vp_offsets = (-1.5, 1.5)
    cx = (canvas.x0 + canvas.x1) / 2.0
    vp_l = VanishingPoint(
        cx + vp_offsets[0] * canvas.width, horizon_y, "left"
    )
    vp_r = VanishingPoint(
        cx + vp_offsets[1] * canvas.width, horizon_y, "right"
    )
    lines: list[GridLine] = [
        GridLine(canvas.x0, horizon_y, canvas.x1, horizon_y, "horizon", 0.5)
    ]

    floor_h = canvas.y1 - horizon_y
    ceil_h = horizon_y - canvas.y0
    max_h = max(floor_h, ceil_h)
    n_rays = cols + 1

    # Fan from VP_L through evenly-spaced y on the RIGHT edge.
    for i in range(n_rays):
        f = i / max(cols, 1)
        ry = canvas.y0 + f * canvas.height
        if abs(ry - horizon_y) < 0.5:
            continue
        is_floor = ry > horizon_y
        if not show_ceiling and not is_floor:
            continue
        seg = _clip_line(vp_l.x, vp_l.y, canvas.x1, ry, canvas)
        if seg:
            w = (
                _depth_weight(abs(ry - horizon_y), max_h)
                if fade_to_horizon
                else 1.0
            )
            role = "from-vp-left"
            lines.append(GridLine(*seg, role, w))

    # Fan from VP_R through evenly-spaced y on the LEFT edge.
    for i in range(n_rays):
        f = i / max(cols, 1)
        ly = canvas.y0 + f * canvas.height
        if abs(ly - horizon_y) < 0.5:
            continue
        is_floor = ly > horizon_y
        if not show_ceiling and not is_floor:
            continue
        seg = _clip_line(vp_r.x, vp_r.y, canvas.x0, ly, canvas)
        if seg:
            w = (
                _depth_weight(abs(ly - horizon_y), max_h)
                if fade_to_horizon
                else 1.0
            )
            role = "from-vp-right"
            lines.append(GridLine(*seg, role, w))

    # Verticals — in 2pt these stay vertical (the third axis is "up").
    n_verts = max(3, rows)
    for i in range(n_verts + 1):
        f = i / n_verts
        vx = canvas.x0 + f * canvas.width
        lines.append(GridLine(vx, canvas.y0, vx, canvas.y1, "vertical", 0.30))

    return PerspectiveGrid(
        mode="2pt",
        canvas=canvas,
        horizon_y=horizon_y,
        vanishing_points=(vp_l, vp_r),
        lines=tuple(lines),
    )


def _grid_3pt(
    canvas: BBox,
    horizon_y: float,
    vp_offsets: Optional[Sequence[float]],
    rows: int,
    cols: int,
    fade_to_horizon: bool,
) -> PerspectiveGrid:
    if vp_offsets is None or len(vp_offsets) < 3:
        vp_offsets = (-1.5, 1.5, -3.0)
    # Borrow the 2pt fans (with ceiling) — drop the verticals and
    # replace them with a fan from VP_Z so all three axes vanish.
    base = _grid_2pt(
        canvas, horizon_y, vp_offsets[:2], rows, cols, True, fade_to_horizon
    )
    cx = (canvas.x0 + canvas.x1) / 2.0
    cy = (canvas.y0 + canvas.y1) / 2.0
    vp_z_y = cy + vp_offsets[2] * canvas.height
    vp_z = VanishingPoint(cx, vp_z_y, "vertical")

    lines: list[GridLine] = [ln for ln in base.lines if ln.role != "vertical"]

    # If VP_Z is above canvas (negative offset), rays target the bottom
    # edge; if below, the top edge. Either way the fan extends through
    # the canvas as the third vanishing direction.
    target_edge_y = canvas.y1 if vp_z_y < cy else canvas.y0
    # Extend the target range so rays fan beyond the canvas edges.
    extended_left = canvas.x0 - canvas.width * 0.25
    extended_right = canvas.x1 + canvas.width * 0.25
    n_rays = max(rows, 6) + 1
    for i in range(n_rays):
        f = i / (n_rays - 1)
        tx = extended_left + f * (extended_right - extended_left)
        seg = _clip_line(vp_z.x, vp_z.y, tx, target_edge_y, canvas)
        if seg:
            lines.append(GridLine(*seg, "from-vp-z", 0.70))

    return PerspectiveGrid(
        mode="3pt",
        canvas=canvas,
        horizon_y=horizon_y,
        vanishing_points=(
            base.vanishing_points[0],
            base.vanishing_points[1],
            vp_z,
        ),
        lines=tuple(lines),
    )


def _grid_iso(canvas: BBox, step: float) -> PerspectiveGrid:
    """Three sets of parallel lines at 30° / 150° / 90° — no convergence."""
    lines: list[GridLine] = []
    lines.extend(_iso_lines(canvas, 30.0, step, "iso-x"))
    lines.extend(_iso_lines(canvas, 150.0, step, "iso-y"))
    lines.extend(_iso_lines(canvas, 90.0, step, "iso-z"))
    return PerspectiveGrid(
        mode="iso",
        canvas=canvas,
        horizon_y=None,
        vanishing_points=(),
        lines=tuple(lines),
    )


def _iso_lines(
    canvas: BBox, angle_deg: float, step: float, role: str
) -> list[GridLine]:
    """Generate the set of parallel lines at ``angle_deg``, spaced ``step``
    apart on the perpendicular, clipped to ``canvas``."""
    if step <= 0:
        return []
    theta = math.radians(angle_deg)
    dx, dy = math.cos(theta), math.sin(theta)
    # Perpendicular unit (rotated 90°)
    px, py = -dy, dx
    # Project canvas corners onto the perpendicular axis to find the
    # range we need to span.
    corners = [
        (canvas.x0, canvas.y0),
        (canvas.x1, canvas.y0),
        (canvas.x0, canvas.y1),
        (canvas.x1, canvas.y1),
    ]
    projs = [x * px + y * py for x, y in corners]
    pmin, pmax = min(projs), max(projs)
    n_start = math.floor(pmin / step)
    n_end = math.ceil(pmax / step)
    diag = math.hypot(canvas.width, canvas.height) * 2.0
    out: list[GridLine] = []
    for n in range(n_start, n_end + 1):
        p = n * step
        # A point on the line lies at perpendicular distance p from the
        # origin along (px, py). Extend along (dx, dy) by a generous diag
        # then clip to canvas.
        cx0 = px * p - dx * diag
        cy0 = py * p - dy * diag
        cx1 = px * p + dx * diag
        cy1 = py * p + dy * diag
        seg = _clip_line(cx0, cy0, cx1, cy1, canvas)
        if seg:
            out.append(GridLine(*seg, role, 0.85))
    return out


# ─── Ridgemap — stacked 1D slices of a 2D scalar field ─────────────
#
# Each row of the input field becomes a horizontal polyline; rows are
# stacked top-to-bottom and emitted in row order so front (lower)
# ridges occlude back (upper) ones — the Joy Division *Unknown
# Pleasures* aesthetic, originally Harold Craft's 1970 successive-
# period plot of pulsar PSR B1919+21 for his Cornell PhD. Wilke's
# *ggridges* (2016) is the same primitive ported to statistical
# density plots. Sibling of `grid()`: where the perspective grid is a
# scaffold for *space*, the ridgemap is a scaffold for *scalar fields*
# — a stack of slices through whatever you've got one value per (x, y)
# of (terrain DEM, gaze density, image luminance, attention map, audio
# spectrogram, …). Pre-flight question: *do the row order and the
# stacking direction carry meaning?* If no, you want a heatmap, not a
# ridgemap.


@dataclass(frozen=True)
class Ridge:
    """One row of the field as a polyline at a fixed baseline.

    ``points`` are (x, y) in canvas user units, y increasing downward
    (SVG convention). ``baseline_y`` is the y the curve sits on when
    the sample value equals ``vmin`` — the polygon close-line for the
    occlusion fill runs along it.
    """

    row_index: int
    baseline_y: float
    points: Tuple[Tuple[float, float], ...]


@dataclass(frozen=True)
class RidgeMap:
    """Result of ``ridgemap(...)`` — a back-to-front stack of ridges
    that renders to a single self-contained SVG document."""

    canvas: BBox
    ridges: Tuple[Ridge, ...]
    field_shape: Tuple[int, int]
    value_range: Tuple[float, float]
    row_spacing: float
    amplitude: float

    def svg(
        self,
        stroke: str = "#e6e4d2",
        stroke_width: float = 1.1,
        bg: Optional[str] = "#0a0a14",
        fill: Optional[str] = "#0a0a14",
    ) -> str:
        """Render as a standalone SVG document.

        Defaults: cream stroke (#e6e4d2, 15.42:1 on #0a0a14, clears
        muriel's 8:1 floor), near-black background, and a fill the
        same colour as the background so each ridge paints over the
        ones behind it — the occlusion that makes the stack read as
        layered rather than transparent. Set ``fill=None`` for pure
        line art (every ridge visible top-to-bottom); set ``bg=None``
        to omit the background rect (composable into a larger SVG).
        """
        cv = self.canvas
        out: list[str] = [
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="{_fmt(cv.x0)} {_fmt(cv.y0)} '
            f'{_fmt(cv.width)} {_fmt(cv.height)}" '
            'preserveAspectRatio="xMidYMid meet">'
        ]
        if bg:
            out.append(
                f'  <rect x="{_fmt(cv.x0)}" y="{_fmt(cv.y0)}" '
                f'width="{_fmt(cv.width)}" height="{_fmt(cv.height)}" '
                f'fill="{bg}"/>'
            )
        out.append('  <g stroke-linejoin="round" stroke-linecap="round">')
        for r in self.ridges:
            poly = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in r.points)
            if fill:
                x0_pt, _ = r.points[0]
                x1_pt, _ = r.points[-1]
                close = (
                    f" {_fmt(x1_pt)},{_fmt(r.baseline_y)}"
                    f" {_fmt(x0_pt)},{_fmt(r.baseline_y)}"
                )
                out.append(
                    f'    <polygon points="{poly}{close}" '
                    f'fill="{fill}" stroke="none" '
                    f'data-row="{r.row_index}"/>'
                )
            out.append(
                f'    <polyline points="{poly}" fill="none" '
                f'stroke="{stroke}" stroke-width="{_fmt(stroke_width)}" '
                f'data-row="{r.row_index}"/>'
            )
        out.append("  </g>")
        out.append("</svg>")
        return "\n".join(out) + "\n"


def ridgemap(
    field: Iterable[Iterable[float]],
    canvas: BBox,
    *,
    amplitude: Optional[float] = None,
    row_spacing: Optional[float] = None,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    margin: float = 0.06,
) -> RidgeMap:
    """Stack 1D slices of a 2D scalar field as ridgeline polylines.

    Parameters
    ----------
    field : 2D iterable of floats (numpy.ndarray works via duck typing)
        Shape ``(n_rows, n_cols)``. All rows must have the same length
        and at least 2 samples.
    canvas : BBox
        Output viewport in SVG user units.
    amplitude : float, optional
        Peak excursion (canvas units) above baseline for a sample at
        ``vmax``. Default: ``1.6 * row_spacing``, which makes the
        tallest peaks rise past the next row's baseline — that overlap
        is what creates the stacked / occluded look.
    row_spacing : float, optional
        Vertical distance between consecutive row baselines. Default:
        usable canvas height divided by ``(n_rows - 1)``.
    vmin, vmax : float, optional
        Value range for normalisation. Default: data min / max.
    margin : float
        Fraction of canvas reserved as padding on every side.

    Returns
    -------
    RidgeMap
        Back-to-front: ``ridges[0]`` is the topmost (drawn first),
        ``ridges[-1]`` the bottommost (drawn last, occludes all).
    """
    row_lists: list[list[float]] = []
    flat: list[float] = []
    for ri, row in enumerate(field):
        try:
            r = [float(v) for v in row]
        except TypeError as exc:
            raise SpatialError(
                f"ridgemap: row {ri} is not iterable — field must be 2D"
            ) from exc
        row_lists.append(r)
        flat.extend(r)

    n_rows = len(row_lists)
    if n_rows == 0:
        raise SpatialError("ridgemap: field has 0 rows")
    cols0 = len(row_lists[0])
    if cols0 < 2:
        raise SpatialError("ridgemap: rows must have at least 2 samples")
    for ri, r in enumerate(row_lists):
        if len(r) != cols0:
            raise SpatialError(
                f"ridgemap: row {ri} has length {len(r)}, expected {cols0}"
            )

    lo = float(min(flat) if vmin is None else vmin)
    hi = float(max(flat) if vmax is None else vmax)
    span = hi - lo
    if span <= 0:
        span = 1.0

    pad = canvas.height * margin
    usable_h = canvas.height - 2 * pad
    if n_rows == 1:
        rs = usable_h
        baselines = [canvas.y0 + canvas.height * 0.5]
    else:
        rs = row_spacing if row_spacing is not None else usable_h / (n_rows - 1)
        top = canvas.y0 + pad
        baselines = [top + i * rs for i in range(n_rows)]

    amp = amplitude
    if amp is None:
        amp = rs * 1.6 if n_rows > 1 else usable_h * 0.4

    x_left = canvas.x0 + pad
    x_right = canvas.x1 - pad
    x_span = x_right - x_left

    ridges: list[Ridge] = []
    for ri, row in enumerate(row_lists):
        baseline = baselines[ri]
        pts: list[Tuple[float, float]] = []
        for ci, v in enumerate(row):
            x = x_left + (ci / (cols0 - 1)) * x_span
            n = (v - lo) / span
            if n < 0:
                n = 0.0
            elif n > 1:
                n = 1.0
            y = baseline - n * amp
            pts.append((x, y))
        ridges.append(
            Ridge(row_index=ri, baseline_y=baseline, points=tuple(pts))
        )

    return RidgeMap(
        canvas=canvas,
        ridges=tuple(ridges),
        field_shape=(n_rows, cols0),
        value_range=(lo, hi),
        row_spacing=rs,
        amplitude=amp,
    )


def _pulsar_field(
    n_rows: int = 80, n_cols: int = 240, seed: int = 1919
) -> list[list[float]]:
    """Synthetic pulsar-pulse field for the ridgemap demo.

    Broadly mimics Harold Craft's 1970 PSR B1919+21 successive-period
    plot: a primary pulse near the centre with per-row lateral jitter,
    a secondary pulse appearing in a subset of rows, low-amplitude
    noise floor. Seeded so the demo is byte-identical run to run.
    """
    rng = random.Random(seed)
    field: list[list[float]] = []
    jitter_amp = 0.025 * n_cols
    pri_sigma = 0.045 * n_cols
    pri_amp_base = 1.6
    sec_sigma = 0.06 * n_cols
    for _ in range(n_rows):
        pri_center = n_cols * 0.5 + (rng.random() - 0.5) * 2 * jitter_amp
        pri_amp = pri_amp_base * (0.85 + rng.random() * 0.35)
        has_sec = rng.random() < 0.55
        sec_amp = (0.45 + rng.random() * 0.45) if has_sec else 0.0
        sec_center = n_cols * (0.66 + (rng.random() - 0.5) * 0.16)
        row: list[float] = []
        for ci in range(n_cols):
            d_pri = (ci - pri_center) / pri_sigma
            v = pri_amp * math.exp(-d_pri * d_pri)
            if sec_amp:
                d_sec = (ci - sec_center) / sec_sigma
                v += sec_amp * math.exp(-d_sec * d_sec)
            v += (rng.random() - 0.5) * 0.05
            row.append(v)
        field.append(row)
    return field


def _ridgemap_demo_svg(
    width: float = 800.0, height: float = 600.0
) -> str:
    """Standalone pulsar-style ridgemap demo, captioned to match the
    perspective-grid demo's chrome."""
    cv = BBox(0, 0, width, height)
    field = _pulsar_field(n_rows=60, n_cols=220, seed=1919)
    # Inset so caption chrome has room without overlapping the stack.
    inner = BBox(24, 78, width - 24, height - 56)
    rm = ridgemap(field, canvas=inner, margin=0.04)
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {_fmt(width)} {_fmt(height)}" '
        f'preserveAspectRatio="xMidYMid meet">',
        f'  <rect x="0" y="0" width="{_fmt(width)}" '
        f'height="{_fmt(height)}" fill="#0a0a14"/>',
        f'  <text x="24" y="40" fill="#e6e4d2" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" '
        f'font-size="22" font-weight="600">'
        f'muriel.spatial — ridgemap</text>',
        f'  <text x="24" y="62" fill="#7fdfff" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" '
        f'font-size="12" opacity="0.75">'
        f'Stacked 1D slices of a 2D scalar field · Harold Craft '
        f'PSR B1919+21 (1970) · Saville / Joy Division (1979) · '
        f'Wilke ggridges (2016)</text>',
    ]
    # Inline the ridgemap SVG group instead of nesting <svg>s.
    for r in rm.ridges:
        poly = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in r.points)
        x0_pt = r.points[0][0]
        x1_pt = r.points[-1][0]
        close = (
            f" {_fmt(x1_pt)},{_fmt(r.baseline_y)}"
            f" {_fmt(x0_pt)},{_fmt(r.baseline_y)}"
        )
        parts.append(
            f'  <polygon points="{poly}{close}" fill="#0a0a14" '
            f'stroke="none"/>'
        )
        parts.append(
            f'  <polyline points="{poly}" fill="none" '
            f'stroke="#e6e4d2" stroke-width="1.1" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
        )
    parts.append(
        f'  <text x="24" y="{_fmt(height - 22)}" fill="#e6e4d2" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" '
        f'font-size="12" opacity="0.92">'
        f'60 rows × 220 cols, synthetic pulsar profile '
        f'(seed=1919)</text>'
    )
    parts.append(
        f'  <text x="24" y="{_fmt(height - 6)}" fill="#7fdfff" '
        f'font-family="ui-monospace,monospace" font-size="11" '
        f'opacity="0.65">'
        f'ridgemap(field, BBox(0, 0, {_fmt(inner.width)}, '
        f'{_fmt(inner.height)}))</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


# ─── Demo / CLI ─────────────────────────────────────────────────────


def _demo_svg() -> str:
    """A 2x2 panel showing all four modes side-by-side."""
    panel_w, panel_h = 620, 380
    gap = 18
    total_w = panel_w * 2 + gap * 3
    total_h = panel_h * 2 + gap * 3 + 96
    panels = [
        ("1pt", "One-point — single VP on horizon (Tron / corridor)"),
        ("2pt", "Two-point — two horizon VPs (architectural cube corner)"),
        ("3pt", "Three-point — adds a vertical VP (looking up at a tower)"),
        ("iso", "Isometric — parallel axes at 30° / 150° / 90°, no convergence"),
    ]
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {total_w} {total_h}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="background:#0a0a14">',
        f'  <text x="{gap}" y="40" fill="#e6e4d2" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" '
        f'font-size="24" font-weight="600">'
        f'muriel.spatial — perspective grids</text>',
        f'  <text x="{gap}" y="64" fill="#7fdfff" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" '
        f'font-size="13" opacity="0.75">'
        f'Alberti · Dürer · Muriel Cooper VLW · Robertson/Dumais Data Mountain '
        f'· Tron horizon. Depth scaffold for layered text.</text>',
    ]
    for idx, (mode, caption) in enumerate(panels):
        col = idx % 2
        row = idx // 2
        x_off = gap + col * (panel_w + gap)
        y_off = 96 + row * (panel_h + gap)
        cv = BBox(0, 0, panel_w, panel_h)
        if mode == "3pt":
            g = grid(mode, cv, horizon_y=panel_h * 0.58,
                     vp_offsets=(-1.4, 1.4, -2.6), rows=7, cols=10)
        elif mode == "iso":
            g = grid(mode, cv, iso_step=42.0)
        elif mode == "1pt":
            g = grid(mode, cv, rows=7, cols=10)
        else:
            g = grid(mode, cv, rows=7, cols=10)
        parts.append(f'  <g transform="translate({x_off} {y_off})">')
        parts.append(
            f'    <rect x="0" y="0" width="{panel_w}" height="{panel_h}" '
            f'fill="#0a0a14" stroke="#3a3a4a" stroke-width="1"/>'
        )
        for ln in g.lines:
            is_horizon = ln.role == "horizon"
            color = "#ff5fa2" if is_horizon else "#7fdfff"
            sw = 1.0 if is_horizon else 0.5
            parts.append(
                f'    <line x1="{_fmt(ln.x0)}" y1="{_fmt(ln.y0)}" '
                f'x2="{_fmt(ln.x1)}" y2="{_fmt(ln.y1)}" '
                f'stroke="{color}" stroke-width="{sw}" '
                f'opacity="{ln.weight:.3f}"/>'
            )
        # Caption + code label
        parts.append(
            f'    <text x="14" y="{panel_h - 38}" fill="#e6e4d2" '
            f'font-family="ui-sans-serif,system-ui,sans-serif" '
            f'font-size="13" opacity="0.92">{caption}</text>'
        )
        parts.append(
            f'    <text x="14" y="{panel_h - 18}" fill="#7fdfff" '
            f'font-family="ui-monospace,monospace" '
            f'font-size="11" opacity="0.65">'
            f'grid("{mode}", BBox(0, 0, {panel_w}, {panel_h}))</text>'
        )
        parts.append("  </g>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _selftest() -> int:
    cv = BBox(0, 0, 1200, 700)

    # 1-point
    g = grid("1pt", cv)
    assert g.mode == "1pt"
    assert len(g.vanishing_points) == 1
    vp = g.vanishing_points[0]
    assert abs(vp.x - 600) < 1e-6 and abs(vp.y - 350) < 1e-6
    assert len(g.lines) > 5
    for ln in g.lines:
        assert cv.x0 - 0.1 <= ln.x0 <= cv.x1 + 0.1
        assert cv.x0 - 0.1 <= ln.x1 <= cv.x1 + 0.1
        assert cv.y0 - 0.1 <= ln.y0 <= cv.y1 + 0.1
        assert cv.y0 - 0.1 <= ln.y1 <= cv.y1 + 0.1
    # Exactly one horizon line.
    horizons = [ln for ln in g.lines if ln.role == "horizon"]
    assert len(horizons) == 1

    # 2-point
    g = grid("2pt", cv)
    assert g.mode == "2pt"
    assert len(g.vanishing_points) == 2
    names = {vp.name for vp in g.vanishing_points}
    assert names == {"left", "right"}

    # 3-point
    g = grid("3pt", cv)
    assert g.mode == "3pt"
    assert len(g.vanishing_points) == 3
    names = {vp.name for vp in g.vanishing_points}
    assert names == {"left", "right", "vertical"}
    assert any(ln.role == "from-vp-z" for ln in g.lines)
    assert not any(ln.role == "vertical" for ln in g.lines)

    # iso
    g = grid("iso", cv, iso_step=80.0)
    assert g.mode == "iso"
    assert len(g.vanishing_points) == 0
    roles = {ln.role for ln in g.lines}
    assert roles == {"iso-x", "iso-y", "iso-z"}

    # Bad mode
    try:
        grid("nope", cv)
    except SpatialError:
        pass
    else:
        raise AssertionError("expected SpatialError for unknown mode")

    # Clipping helper
    assert _clip_line(-10, 50, 100, 50, cv) == (0.0, 50.0, 100.0, 50.0)
    assert _clip_line(-10, -10, -5, -5, cv) is None
    assert _clip_line(100, 100, 200, 200, cv) == (100, 100, 200, 200)
    # Vertical-only line through canvas
    assert _clip_line(500, -100, 500, 1000, cv) == (500, 0, 500, 700)

    # SVG output basics
    svg = grid("1pt", cv).svg()
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert 'data-role="horizon"' in svg

    # Demo renders without crashing
    demo = _demo_svg()
    assert demo.startswith("<svg")
    assert "1pt" in demo and "iso" in demo

    # Ridgemap — basic shape + bounds + ordering
    field = [[math.sin(c * 0.1 + r * 0.3) for c in range(40)] for r in range(12)]
    rm = ridgemap(field, BBox(0, 0, 600, 400))
    assert rm.field_shape == (12, 40)
    assert len(rm.ridges) == 12
    assert all(len(r.points) == 40 for r in rm.ridges)
    # Baselines monotonically descend (row 0 at top).
    bls = [r.baseline_y for r in rm.ridges]
    assert all(b1 < b2 for b1, b2 in zip(bls, bls[1:]))
    # Every plotted point sits at or above its baseline (y grows downward).
    for r in rm.ridges:
        for _, y in r.points:
            assert y <= r.baseline_y + 1e-6
    # vmin/vmax bracket data
    assert rm.value_range[0] <= rm.value_range[1]

    # Ridgemap SVG basics
    svg = rm.svg()
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert "polyline" in svg
    # Occlusion fill on by default
    assert "polygon" in svg
    # fill=None removes the occlusion polygons
    svg_lines = rm.svg(fill=None)
    assert "polygon" not in svg_lines
    assert "polyline" in svg_lines

    # Bad inputs
    try:
        ridgemap([], BBox(0, 0, 100, 100))
    except SpatialError:
        pass
    else:
        raise AssertionError("expected SpatialError for empty field")
    try:
        ridgemap([[1.0, 2.0], [3.0]], BBox(0, 0, 100, 100))
    except SpatialError:
        pass
    else:
        raise AssertionError("expected SpatialError for ragged field")
    try:
        ridgemap([[1.0]], BBox(0, 0, 100, 100))
    except SpatialError:
        pass
    else:
        raise AssertionError("expected SpatialError for cols<2")
    try:
        ridgemap([1.0, 2.0, 3.0], BBox(0, 0, 100, 100))  # 1D
    except SpatialError:
        pass
    else:
        raise AssertionError("expected SpatialError for 1D field")

    # Ridgemap demo renders without crashing
    rdemo = _ridgemap_demo_svg()
    assert rdemo.startswith("<svg")
    assert "ridgemap" in rdemo

    return 0


def _main(argv: Sequence[str]) -> int:
    import argparse

    p = argparse.ArgumentParser(
        prog="python -m muriel.spatial",
        description="Perspective-grid generator for depth scaffolding.",
    )
    p.add_argument("--demo", action="store_true",
                   help="render the 2x2 perspective-grid demo SVG")
    p.add_argument("--ridgemap", action="store_true",
                   help="render the pulsar-style ridgemap demo SVG")
    p.add_argument("--mode", choices=["1pt", "2pt", "3pt", "iso"],
                   help="with --demo: render a single mode at full canvas")
    p.add_argument("--selftest", action="store_true",
                   help="run the assertion suite")
    p.add_argument("--width", type=float, default=1200.0,
                   help="canvas width for --mode / --ridgemap (default 1200)")
    p.add_argument("--height", type=float, default=700.0,
                   help="canvas height for --mode / --ridgemap (default 700)")
    p.add_argument("--show-vps", action="store_true",
                   help="annotate the vanishing points")
    p.add_argument("-o", "--output", default="-",
                   help="output file (default: stdout)")
    args = p.parse_args(argv)

    if args.selftest:
        _selftest()
        print("muriel.spatial: selftest passed", file=sys.stderr)
        return 0

    if args.ridgemap:
        svg = _ridgemap_demo_svg(width=args.width, height=args.height)
        if args.output == "-":
            sys.stdout.write(svg)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"wrote {args.output}", file=sys.stderr)
        return 0

    if args.demo:
        if args.mode:
            cv = BBox(0, 0, args.width, args.height)
            if args.mode == "iso":
                g = grid("iso", cv, iso_step=50.0)
            elif args.mode == "3pt":
                g = grid("3pt", cv, vp_offsets=(-1.4, 1.4, -2.6))
            else:
                g = grid(args.mode, cv)
            svg = g.svg(show_vps=args.show_vps)
        else:
            svg = _demo_svg()
        if args.output == "-":
            sys.stdout.write(svg)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"wrote {args.output}", file=sys.stderr)
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
