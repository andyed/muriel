#!/usr/bin/env python3
"""muriel.patterns — generative pattern primitives for backgrounds and texture.

Why this exists
---------------
Screenshot designs, hero illustrations, and brand-asset variants need
controlled visual variety — non-uniform but non-distracting backgrounds
that read as "designed" rather than stock. The ad-hoc approach is to
hand-place a gradient or grab a stock noise PNG; both go stale fast.

This module ships four deterministic primitives that cover the
"workhorse background" surface used by the screenshot designer's
``background(mesh|noise|...)`` arg:

* **dots** — Bridson Poisson-disk sampling → dot field with even
  visual density and no obvious tiling. Used for: dot-grid mesh
  backgrounds, scatter texture, particle carriers.
* **flow** — value-noise vector field traced by short polyline
  streamlines. Used for: flow-line backgrounds, contour-suggestion
  texture, anything where the eye should feel directional motion.
* **grain** — value-noise raster sampled at cell granularity →
  small SVG ``<pattern>`` tile (repeats without blowing up file
  size). Used for: film-grain overlays, paper texture, non-flat fill.
* **wavefield** — smooth, layered contour bands from seeded harmonic
  synthesis or caller-supplied normalized series. Used for: section
  boundaries, signal bands, uncertainty fields, and rhythmic structure.

Lineage
-------
* Bridson, R. (2007). "Fast Poisson Disk Sampling in Arbitrary
  Dimensions." SIGGRAPH sketches. ``dots`` is a direct port.
* Perlin, K. (1985); Lewis (1989) value noise. ``flow`` and ``grain``
  sample a hash-driven 2D value-noise function — pure Python,
  smoothstep-interpolated, no numpy.
* Pattern-language ancestry: ``css-doodle`` (rule-based CSS grids),
  ``glisp`` (Lisp DSL), ``curv`` (SDF math), ``nannou`` (Rust
  framework), ``noc-book-2`` (Shiffman, *Nature of Code* 2024).
* Sibling: ``muriel.spatial`` (perspective grids — the depth
  scaffold these patterns can sit on).

Determinism
-----------
Every primitive takes ``seed: int``. Same seed → identical output,
byte-for-byte, across platforms and Python versions — all randomness
routes through ``hashlib.blake2b`` rather than Python's hash
randomization or any RNG with implementation-defined state.

Zero deps
---------
Pure Python; no numpy, scipy, or Pillow. Output is SVG; rasterization
goes through whatever the caller already uses (``cairosvg``,
``rsvg-convert``).

Contrast contract
-----------------
Each primitive takes ``bg`` (base tone — fills the canvas) and ``fg``
(pattern tone — drawn on top). For overlay text to satisfy muriel's
universal 8:1 floor, validate the text colour against ``bg``, not
against the pattern tone — the pattern intentionally has internal
contrast; that's the texture. Use ``muriel.contrast.contrast_ratio``.

Usage
-----

::

    from muriel.layout import BBox
    from muriel.patterns import dots, flow, grain, wavefield

    cv = BBox(0, 0, 1200, 700)

    p = dots(cv, radius=18, seed=42)
    open("dots.svg", "w").write(p.svg(bg="#0a0a14", fg="#e6e4d2"))

    p = flow(cv, density=18, noise_scale=0.004, seed=42)
    open("flow.svg", "w").write(p.svg(bg="#0a0a14", fg="#7fdfff"))

    p = grain(cv, cell=3, seed=42)
    open("grain.svg", "w").write(p.svg(bg="#0a0a14", fg="#e6e4d2"))

    p = wavefield(cv, layers=4, seed=42)
    open("waves.svg", "w").write(p.svg())

CLI
---

::

    python -m muriel.patterns --demo                  # 2x2 panel of all primitives
    python -m muriel.patterns --kind dots             # render a single primitive
    python -m muriel.patterns --selftest              # assertion suite

Cross-references: ``channels/raster.md`` (screenshot designer P0
backgrounds), ``channels/generative.md`` (forthcoming channel doc),
``muriel.spatial`` (perspective scaffolding).
"""

from __future__ import annotations

import hashlib
import math
import sys
from dataclasses import dataclass, field
from typing import Optional, Sequence, Tuple

from muriel.layout import BBox

__all__ = [
    "BBox",
    "DotField",
    "FlowField",
    "Grain",
    "WaveLayer",
    "WaveField",
    "PatternError",
    "dots",
    "flow",
    "grain",
    "wavefield",
]


class PatternError(ValueError):
    """Raised when pattern parameters are inconsistent or out of range."""


# ─── Hash-based deterministic primitives ────────────────────────────


def _hash01(seed: int, *ints: int) -> float:
    """Deterministic hash to ``[0, 1)``.

    Routes through blake2b so output is identical across platforms,
    Python versions, and PYTHONHASHSEED settings.
    """
    h = hashlib.blake2b(digest_size=8)
    h.update(int(seed).to_bytes(8, "little", signed=True))
    for n in ints:
        h.update(int(n).to_bytes(8, "little", signed=True))
    return int.from_bytes(h.digest(), "little") / (1 << 64)


def _smoothstep(t: float) -> float:
    """Hermite smoothstep — cubic ease for value-noise interpolation."""
    return t * t * (3.0 - 2.0 * t)


def _value_noise2(x: float, y: float, seed: int) -> float:
    """Bilinear-interpolated 2D value noise, output ∈ [0, 1].

    Lattice values come from ``_hash01``; interpolation uses smoothstep
    so first-derivative continuity is enough to avoid grid artefacts at
    the cell boundaries.
    """
    x0 = math.floor(x)
    y0 = math.floor(y)
    fx = _smoothstep(x - x0)
    fy = _smoothstep(y - y0)
    n00 = _hash01(seed, x0, y0)
    n10 = _hash01(seed, x0 + 1, y0)
    n01 = _hash01(seed, x0, y0 + 1)
    n11 = _hash01(seed, x0 + 1, y0 + 1)
    return (
        n00 * (1.0 - fx) * (1.0 - fy)
        + n10 * fx * (1.0 - fy)
        + n01 * (1.0 - fx) * fy
        + n11 * fx * fy
    )


def _fmt(v: float) -> str:
    """Compact numeric formatter for SVG output."""
    if v == int(v):
        return str(int(v))
    return f"{v:.2f}"


# ─── Result primitives ──────────────────────────────────────────────


@dataclass(frozen=True)
class DotField:
    """Result of ``dots(...)`` — Poisson-disk points + SVG emit."""

    canvas: BBox
    points: Tuple[Tuple[float, float], ...]
    radius: float
    seed: int

    def svg(
        self,
        bg: Optional[str] = "#0a0a14",
        fg: str = "#e6e4d2",
        dot_r: Optional[float] = None,
        opacity: float = 1.0,
    ) -> str:
        """Render as a standalone SVG document.

        ``dot_r`` defaults to ``radius * 0.25`` — small enough that the
        spacing dominates the felt-density, large enough to read.
        """
        cv = self.canvas
        r = dot_r if dot_r is not None else max(0.5, self.radius * 0.25)
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
        out.append(f'  <g fill="{fg}" opacity="{opacity:.3f}">')
        for x, y in self.points:
            out.append(
                f'    <circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{_fmt(r)}"/>'
            )
        out.append("  </g>")
        out.append("</svg>")
        return "\n".join(out) + "\n"


@dataclass(frozen=True)
class FlowField:
    """Result of ``flow(...)`` — value-noise streamlines + SVG emit."""

    canvas: BBox
    polylines: Tuple[Tuple[Tuple[float, float], ...], ...]
    noise_scale: float
    seed: int

    def svg(
        self,
        bg: Optional[str] = "#0a0a14",
        fg: str = "#7fdfff",
        stroke_width: float = 0.6,
        opacity: float = 0.65,
    ) -> str:
        """Render as a standalone SVG document."""
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
        out.append(
            f'  <g stroke="{fg}" stroke-width="{_fmt(stroke_width)}" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round" '
            f'opacity="{opacity:.3f}">'
        )
        for poly in self.polylines:
            if len(poly) < 2:
                continue
            d = " ".join(
                ("M" if i == 0 else "L") + f"{_fmt(px)} {_fmt(py)}"
                for i, (px, py) in enumerate(poly)
            )
            out.append(f'    <path d="{d}"/>')
        out.append("  </g>")
        out.append("</svg>")
        return "\n".join(out) + "\n"


@dataclass(frozen=True)
class Grain:
    """Result of ``grain(...)`` — small SVG ``<pattern>`` tile that
    repeats across the canvas.

    ``values`` is the unit tile (``tile_cells × tile_cells`` floats in
    [0, 1]); ``cell`` is the rendered side of each tile cell in canvas
    units. The full visual texture is the unit tile repeated via
    ``<pattern>``, so SVG size stays small no matter how large the
    canvas.
    """

    canvas: BBox
    values: Tuple[Tuple[float, ...], ...]
    cell: float
    seed: int

    def svg(
        self,
        bg: Optional[str] = "#0a0a14",
        fg: str = "#e6e4d2",
        opacity_range: Tuple[float, float] = (0.04, 0.30),
    ) -> str:
        """Render as a standalone SVG document.

        Each tile cell is one ``<rect>`` with opacity mapped from its
        noise value into ``opacity_range``. Cells at opacity 0 are
        skipped to keep file size down.
        """
        cv = self.canvas
        n = len(self.values)
        if n == 0:
            raise PatternError("Grain has no tile values.")
        lo, hi = opacity_range
        out: list[str] = [
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="{_fmt(cv.x0)} {_fmt(cv.y0)} '
            f'{_fmt(cv.width)} {_fmt(cv.height)}" '
            'preserveAspectRatio="xMidYMid meet">'
        ]
        out.append("  <defs>")
        pat_id = f"grain-{self.seed}-{n}"
        tile_w = n * self.cell
        out.append(
            f'    <pattern id="{pat_id}" '
            f'width="{_fmt(tile_w)}" height="{_fmt(tile_w)}" '
            f'patternUnits="userSpaceOnUse">'
        )
        for j, row in enumerate(self.values):
            for i, v in enumerate(row):
                op = lo + (hi - lo) * v
                if op <= 0.005:
                    continue
                out.append(
                    f'      <rect x="{_fmt(i * self.cell)}" '
                    f'y="{_fmt(j * self.cell)}" '
                    f'width="{_fmt(self.cell)}" '
                    f'height="{_fmt(self.cell)}" '
                    f'fill="{fg}" opacity="{op:.3f}"/>'
                )
        out.append("    </pattern>")
        out.append("  </defs>")
        if bg:
            out.append(
                f'  <rect x="{_fmt(cv.x0)}" y="{_fmt(cv.y0)}" '
                f'width="{_fmt(cv.width)}" height="{_fmt(cv.height)}" '
                f'fill="{bg}"/>'
            )
        out.append(
            f'  <rect x="{_fmt(cv.x0)}" y="{_fmt(cv.y0)}" '
            f'width="{_fmt(cv.width)}" height="{_fmt(cv.height)}" '
            f'fill="url(#{pat_id})"/>'
        )
        out.append("</svg>")
        return "\n".join(out) + "\n"


@dataclass(frozen=True)
class WaveLayer:
    """One inspectable contour in a :class:`WaveField`.

    ``values`` are normalized to ``[-1, 1]`` with positive values rising
    above ``baseline_y``. ``curve_d`` is the open contour; ``area_d`` closes
    that contour against the canvas bottom for layered fills.
    """

    index: int
    baseline_y: float
    values: Tuple[float, ...]
    points: Tuple[Tuple[float, float], ...]
    curve_d: str
    area_d: str


@dataclass(frozen=True)
class WaveField:
    """Layered wave geometry from ``wavefield(...)`` plus SVG emission."""

    canvas: BBox
    layers: Tuple[WaveLayer, ...]
    source: str
    seed: int
    amplitude: float
    smoothness: float

    def svg(
        self,
        *,
        bg: Optional[str] = "var(--mg-bg, #0a0a14)",
        fill_colors: Optional[Sequence[str]] = None,
        fill_opacity: float = 1.0,
        stroke: str = "var(--mg-wave-stroke, #e6e4d2)",
        stroke_width: float = 1.1,
        title: str = "Layered wave field",
        desc: Optional[str] = None,
    ) -> str:
        """Render a viewBox-first, accessible SVG document.

        Pass ``fill_colors=()`` for line art. Otherwise colors cycle across
        layers; defaults are restrained dark-to-cyan Muriel tokens. Motion is
        intentionally absent: a static export remains the canonical artifact.
        """
        if not 0.0 <= fill_opacity <= 1.0:
            raise PatternError(
                f"fill_opacity must be in [0, 1]; got {fill_opacity}"
            )
        if stroke_width < 0:
            raise PatternError(f"stroke_width must be >= 0; got {stroke_width}")

        colors: Sequence[str] = fill_colors if fill_colors is not None else (
            "var(--mg-wave-0, #12323b)",
            "var(--mg-wave-1, #174c59)",
            "var(--mg-wave-2, #1d6878)",
            "var(--mg-accent, #7fdfff)",
        )
        cv = self.canvas
        description = desc or (
            f"{len(self.layers)} smooth contour layers from {self.source} values; "
            f"seed {self.seed}."
        )
        out: list[str] = [
            '<svg xmlns="http://www.w3.org/2000/svg" role="img" '
            f'viewBox="{_fmt(cv.x0)} {_fmt(cv.y0)} '
            f'{_fmt(cv.width)} {_fmt(cv.height)}" '
            'preserveAspectRatio="xMidYMid meet">',
            f"  <title>{_xml_escape(title)}</title>",
            f"  <desc>{_xml_escape(description)}</desc>",
        ]
        if bg:
            out.append(
                f'  <rect x="{_fmt(cv.x0)}" y="{_fmt(cv.y0)}" '
                f'width="{_fmt(cv.width)}" height="{_fmt(cv.height)}" '
                f'fill="{bg}"/>'
            )
        line_art = len(colors) == 0
        for layer in self.layers:
            if line_art:
                fill = "none"
            elif len(self.layers) == 1:
                fill = colors[-1]
            else:
                color_index = round(
                    layer.index * (len(colors) - 1) / (len(self.layers) - 1)
                )
                fill = colors[color_index]
            path_d = layer.curve_d if line_art else layer.area_d
            out.append(
                f'  <path d="{path_d}" fill="{fill}" '
                f'fill-opacity="{fill_opacity:.3f}" stroke="{stroke}" '
                f'stroke-width="{_fmt(stroke_width)}" '
                f'stroke-linecap="round" stroke-linejoin="round" '
                f'data-layer="{layer.index}" data-source="{self.source}"/>'
            )
        out.append("</svg>")
        return "\n".join(out) + "\n"


# ─── Public constructors ────────────────────────────────────────────


def dots(
    canvas: BBox,
    *,
    radius: float = 18.0,
    k: int = 30,
    seed: int = 0,
) -> DotField:
    """Bridson Poisson-disk dot field — uniform visual density, no tiling.

    Parameters
    ----------
    canvas : BBox
        Bounding box in SVG user units.
    radius : float
        Minimum spacing between any two points, in canvas units.
        Controls felt density: smaller → denser.
    k : int
        Bridson candidate count per active point (paper recommends 30).
        Lower → faster + slightly sparser; higher → tighter packing.
    seed : int
        Determinism handle. Same seed → identical point set.

    Returns
    -------
    DotField

    Raises
    ------
    PatternError
        If ``radius`` is non-positive or larger than the canvas.
    """
    if radius <= 0:
        raise PatternError(f"radius must be > 0; got {radius}")
    if radius >= min(canvas.width, canvas.height):
        raise PatternError(
            f"radius {radius} ≥ canvas min side {min(canvas.width, canvas.height)}; "
            "would produce 0–1 points."
        )
    if k < 1:
        raise PatternError(f"k must be ≥ 1; got {k}")

    pts = _bridson(canvas, radius, k, seed)
    return DotField(
        canvas=canvas, points=tuple(pts), radius=radius, seed=seed
    )


def flow(
    canvas: BBox,
    *,
    density: float = 20.0,
    noise_scale: float = 0.004,
    length: int = 80,
    step: float = 4.0,
    seed: int = 0,
) -> FlowField:
    """Value-noise vector field traced as short streamline polylines.

    Parameters
    ----------
    canvas : BBox
        Bounding box.
    density : float
        Minimum spacing between streamline seed points (Bridson radius
        in canvas units). Smaller → more streamlines.
    noise_scale : float
        Spatial frequency of the underlying noise field, in 1/units.
        Smaller → smoother, large-scale swirls; larger → tighter
        turbulence. ``0.004`` ≈ one full noise period per 250 units.
    length : int
        Maximum integration steps per streamline. Total streamline
        length ≈ ``length * step`` canvas units.
    step : float
        Euler integration step in canvas units.
    seed : int
        Determinism handle.

    Returns
    -------
    FlowField
    """
    if density <= 0:
        raise PatternError(f"density must be > 0; got {density}")
    if noise_scale <= 0:
        raise PatternError(f"noise_scale must be > 0; got {noise_scale}")
    if length < 2:
        raise PatternError(f"length must be ≥ 2; got {length}")
    if step <= 0:
        raise PatternError(f"step must be > 0; got {step}")

    seeds = _bridson(canvas, density, 30, seed)
    polylines: list[Tuple[Tuple[float, float], ...]] = []
    for sx, sy in seeds:
        poly = _trace_streamline(
            sx, sy, canvas, noise_scale, length, step, seed
        )
        if len(poly) >= 2:
            polylines.append(tuple(poly))
    return FlowField(
        canvas=canvas,
        polylines=tuple(polylines),
        noise_scale=noise_scale,
        seed=seed,
    )


def grain(
    canvas: BBox,
    *,
    cell: float = 3.0,
    tile_cells: int = 64,
    noise_scale: float = 0.4,
    seed: int = 0,
) -> Grain:
    """Value-noise raster grain → small repeating SVG pattern tile.

    Parameters
    ----------
    canvas : BBox
        Bounding box (the tile repeats across this).
    cell : float
        Rendered side of each tile cell, in canvas units. ``2–4`` reads
        as film grain; ``6–12`` as paper texture; ``16+`` as coarse mesh.
    tile_cells : int
        Side of the unit tile in cells. ``64`` keeps SVG size O(4096
        rects) regardless of canvas size; the tile then repeats via
        ``<pattern>``.
    noise_scale : float
        Frequency of the underlying noise across the tile. ``0.4`` ≈
        a few peaks across a 64-cell tile, which reads as organic
        grain rather than uniform stipple.
    seed : int
        Determinism handle.

    Returns
    -------
    Grain
    """
    if cell <= 0:
        raise PatternError(f"cell must be > 0; got {cell}")
    if tile_cells < 4:
        raise PatternError(f"tile_cells must be ≥ 4; got {tile_cells}")
    if noise_scale <= 0:
        raise PatternError(f"noise_scale must be > 0; got {noise_scale}")

    rows: list[Tuple[float, ...]] = []
    for j in range(tile_cells):
        row: list[float] = []
        for i in range(tile_cells):
            v = _value_noise2(i * noise_scale, j * noise_scale, seed)
            row.append(v)
        rows.append(tuple(row))
    return Grain(
        canvas=canvas,
        values=tuple(rows),
        cell=cell,
        seed=seed,
    )


def wavefield(
    canvas: BBox,
    *,
    layers: Optional[int] = None,
    samples: int = 16,
    amplitude: Optional[float] = None,
    cycles: float = 1.6,
    roughness: float = 0.35,
    smoothness: float = 0.8,
    margin: float = 0.08,
    seed: int = 0,
    series: Optional[Sequence[Sequence[float]]] = None,
) -> WaveField:
    """Build smooth layered contours from harmonics or normalized data.

    Generated mode (``series=None``) combines three seeded sinusoids. The
    result is organic but byte-stable for a given seed. Semantic mode accepts
    one normalized ``[-1, 1]`` series per layer; positive values rise above the
    layer baseline. Muriel does not silently normalize data because doing so
    would hide the scale that gives a signal its meaning.

    ``layers`` defaults to four in generated mode and is inferred from
    ``series`` in semantic mode. Geometry is returned as frozen dataclasses so
    callers can annotate, compare, or recompose it before SVG emission.
    """
    if canvas.width <= 0 or canvas.height <= 0:
        raise PatternError("wavefield canvas must have positive width and height")
    if not 0.0 <= margin < 0.45:
        raise PatternError(f"margin must be in [0, 0.45); got {margin}")
    if not 0.0 <= roughness <= 1.0:
        raise PatternError(f"roughness must be in [0, 1]; got {roughness}")
    if not 0.0 <= smoothness <= 1.0:
        raise PatternError(f"smoothness must be in [0, 1]; got {smoothness}")

    rows: list[Tuple[float, ...]] = []
    source = "series" if series is not None else "generated"
    if series is not None:
        for row_index, row in enumerate(series):
            vals = tuple(float(v) for v in row)
            if len(vals) < 2:
                raise PatternError(
                    f"series row {row_index} must contain at least 2 values"
                )
            for value in vals:
                if not math.isfinite(value) or not -1.0 <= value <= 1.0:
                    raise PatternError(
                        "series values must be finite and normalized to [-1, 1]; "
                        f"row {row_index} contains {value}"
                    )
            rows.append(vals)
        if not rows:
            raise PatternError("series must contain at least one row")
        if layers is not None and layers != len(rows):
            raise PatternError(
                f"layers={layers} conflicts with {len(rows)} series rows"
            )
        layer_count = len(rows)
    else:
        layer_count = 4 if layers is None else layers
        if layer_count < 1:
            raise PatternError(f"layers must be >= 1; got {layer_count}")
        if samples < 4:
            raise PatternError(f"samples must be >= 4; got {samples}")
        if cycles <= 0:
            raise PatternError(f"cycles must be > 0; got {cycles}")
        for layer_index in range(layer_count):
            phase_a = math.tau * _hash01(seed, 0xD1, layer_index)
            phase_b = math.tau * _hash01(seed, 0xD2, layer_index)
            phase_c = math.tau * _hash01(seed, 0xD3, layer_index)
            layer_cycles = cycles * (1.0 + 0.055 * layer_index)
            values: list[float] = []
            for sample_index in range(samples):
                t = sample_index / (samples - 1)
                primary = math.sin(math.tau * layer_cycles * t + phase_a)
                detail = (
                    0.64
                    * math.sin(math.tau * layer_cycles * 1.85 * t + phase_b)
                    + 0.36
                    * math.sin(math.tau * layer_cycles * 3.10 * t + phase_c)
                )
                values.append((1.0 - roughness) * primary + roughness * detail)
            rows.append(tuple(values))

    inner_top = canvas.y0 + canvas.height * margin
    inner_bottom = canvas.y1 - canvas.height * margin
    available = inner_bottom - inner_top
    amp = amplitude
    if amp is None:
        amp = min(canvas.height * 0.12, available / (layer_count + 1) * 0.55)
    if amp <= 0:
        raise PatternError(f"amplitude must be > 0; got {amp}")
    if amp * 2 >= available:
        raise PatternError(
            f"amplitude {amp} leaves no room inside the {available:.2f}-unit field"
        )

    baseline_top = inner_top + amp
    baseline_bottom = inner_bottom - amp
    if layer_count == 1:
        baselines = [(baseline_top + baseline_bottom) * 0.5]
    else:
        baselines = [
            baseline_top
            + (baseline_bottom - baseline_top) * i / (layer_count - 1)
            for i in range(layer_count)
        ]

    wave_layers: list[WaveLayer] = []
    for layer_index, (baseline, values) in enumerate(zip(baselines, rows)):
        pts = tuple(
            (
                canvas.x0 + canvas.width * i / (len(values) - 1),
                baseline - value * amp,
            )
            for i, value in enumerate(values)
        )
        curve_d, area_d = _wave_paths(pts, canvas.y1, smoothness)
        wave_layers.append(
            WaveLayer(
                index=layer_index,
                baseline_y=baseline,
                values=values,
                points=pts,
                curve_d=curve_d,
                area_d=area_d,
            )
        )

    return WaveField(
        canvas=canvas,
        layers=tuple(wave_layers),
        source=source,
        seed=seed,
        amplitude=amp,
        smoothness=smoothness,
    )


def _wave_paths(
    points: Sequence[Tuple[float, float]],
    bottom_y: float,
    smoothness: float,
) -> Tuple[str, str]:
    """Return open and bottom-closed cubic paths through ``points``.

    Control handles use the local Catmull-Rom tangent at each knot. This is a
    standard interpolation construction, implemented here independently; the
    upstream ``svgwave`` source is not imported, vendored, or translated.
    """
    curve = f"M {_fmt(points[0][0])} {_fmt(points[0][1])}"
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i > 0 else points[i]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        scale = smoothness / 6.0
        c1 = (p1[0] + (p2[0] - p0[0]) * scale,
              p1[1] + (p2[1] - p0[1]) * scale)
        c2 = (p2[0] - (p3[0] - p1[0]) * scale,
              p2[1] - (p3[1] - p1[1]) * scale)
        curve += (
            f" C {_fmt(c1[0])} {_fmt(c1[1])}"
            f" {_fmt(c2[0])} {_fmt(c2[1])}"
            f" {_fmt(p2[0])} {_fmt(p2[1])}"
        )
    area = (
        f"{curve} L {_fmt(points[-1][0])} {_fmt(bottom_y)}"
        f" L {_fmt(points[0][0])} {_fmt(bottom_y)} Z"
    )
    return curve, area


# ─── Internals: Bridson Poisson-disk ────────────────────────────────


def _bridson(
    canvas: BBox, radius: float, k: int, seed: int
) -> list[Tuple[float, float]]:
    """Bridson 2007 fast Poisson-disk sampling.

    O(N) in the number of accepted points. Background grid uses cell
    side ``radius / sqrt(2)`` so any disk-conflict candidate lives in
    one of the 5×5 neighbourhood cells, making the rejection test
    constant-time.
    """
    w = canvas.width
    h = canvas.height
    cell = radius / math.sqrt(2.0)
    gw = max(1, int(math.ceil(w / cell)))
    gh = max(1, int(math.ceil(h / cell)))
    grid: list[list[Optional[Tuple[float, float]]]] = [
        [None] * gw for _ in range(gh)
    ]
    points: list[Tuple[float, float]] = []
    active: list[int] = []  # indices into points

    # Deterministic seed point — centre of canvas drifted by hash.
    p0 = (
        canvas.x0 + (0.25 + 0.5 * _hash01(seed, 0)) * w,
        canvas.y0 + (0.25 + 0.5 * _hash01(seed, 1)) * h,
    )
    points.append(p0)
    active.append(0)
    gi = min(gw - 1, max(0, int((p0[0] - canvas.x0) / cell)))
    gj = min(gh - 1, max(0, int((p0[1] - canvas.y0) / cell)))
    grid[gj][gi] = p0

    step = 0
    r2 = radius * radius
    while active:
        # Deterministically pick an active index.
        pick = int(_hash01(seed, 0xA1, step) * len(active))
        if pick >= len(active):
            pick = len(active) - 1
        step += 1
        anchor_idx = active[pick]
        ax, ay = points[anchor_idx]
        found = False
        for trial in range(k):
            # Annulus: r ∈ [radius, 2*radius), θ ∈ [0, 2π).
            rr = radius * (1.0 + _hash01(seed, 0xB2, step, trial))
            theta = 2.0 * math.pi * _hash01(seed, 0xC3, step, trial)
            px = ax + rr * math.cos(theta)
            py = ay + rr * math.sin(theta)
            if not (canvas.x0 <= px < canvas.x1):
                continue
            if not (canvas.y0 <= py < canvas.y1):
                continue
            gi2 = min(gw - 1, max(0, int((px - canvas.x0) / cell)))
            gj2 = min(gh - 1, max(0, int((py - canvas.y0) / cell)))
            ok = True
            for dj in range(-2, 3):
                nj = gj2 + dj
                if nj < 0 or nj >= gh:
                    continue
                for di in range(-2, 3):
                    ni = gi2 + di
                    if ni < 0 or ni >= gw:
                        continue
                    n = grid[nj][ni]
                    if n is None:
                        continue
                    dx = n[0] - px
                    dy = n[1] - py
                    if dx * dx + dy * dy < r2:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                points.append((px, py))
                active.append(len(points) - 1)
                grid[gj2][gi2] = (px, py)
                found = True
                break
        if not found:
            # Remove the anchor from active; swap-pop preserves O(1)
            # without altering determinism (pick index unchanged
            # because we re-hash on `step`).
            last = active.pop()
            if pick < len(active):
                active[pick] = last
    return points


# ─── Internals: streamline tracing ──────────────────────────────────


def _trace_streamline(
    sx: float,
    sy: float,
    canvas: BBox,
    noise_scale: float,
    length: int,
    step: float,
    seed: int,
) -> list[Tuple[float, float]]:
    """Euler-integrate a streamline from (sx, sy) through the noise field.

    Angle at each point = ``2π * value_noise(x*scale, y*scale)``.
    Traces in both directions from the seed, then concatenates so the
    seed sits roughly mid-streamline (matches Cabral & Leedom 1993
    LIC-style streamline aesthetics).
    """
    forward = _trace_one_direction(
        sx, sy, canvas, noise_scale, length // 2, step, seed, +1
    )
    backward = _trace_one_direction(
        sx, sy, canvas, noise_scale, length // 2, step, seed, -1
    )
    return list(reversed(backward[1:])) + forward


def _trace_one_direction(
    sx: float,
    sy: float,
    canvas: BBox,
    noise_scale: float,
    n_steps: int,
    step: float,
    seed: int,
    sign: int,
) -> list[Tuple[float, float]]:
    pts: list[Tuple[float, float]] = [(sx, sy)]
    x, y = sx, sy
    for _ in range(n_steps):
        v = _value_noise2(x * noise_scale, y * noise_scale, seed)
        theta = 2.0 * math.pi * v
        x += sign * step * math.cos(theta)
        y += sign * step * math.sin(theta)
        if not (canvas.x0 <= x < canvas.x1):
            break
        if not (canvas.y0 <= y < canvas.y1):
            break
        pts.append((x, y))
    return pts


# ─── Demo / CLI ─────────────────────────────────────────────────────


def _demo_svg() -> str:
    """A 2x2 panel showing all four primitives."""
    panel_w, panel_h = 480, 360
    gap = 18
    total_w = panel_w * 2 + gap * 3
    total_h = panel_h * 2 + gap * 3 + 96

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {total_w} {total_h}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="background:#0a0a14">',
        # Header text: #e6e4d2 on #0a0a14 ≈ 15.8:1 contrast — passes 8:1.
        f'  <text x="{gap}" y="40" fill="#e6e4d2" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" '
        f'font-size="24" font-weight="600">'
        f'muriel.patterns — generative backgrounds</text>',
        # Sub text: #7fdfff on #0a0a14 ≈ 13.4:1 contrast — passes 8:1.
        f'  <text x="{gap}" y="64" fill="#7fdfff" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" '
        f'font-size="16" font-weight="500">'
        f'Poisson-disk · value-noise flow and grain · harmonic waves. '
        f'Deterministic; SVG-first.</text>',
    ]

    panels = [
        ("dots", "Bridson Poisson-disk dot field"),
        ("flow", "Value-noise streamlines (LIC-style)"),
        ("grain", "Value-noise grain (SVG pattern tile)"),
        ("wavefield", "Seeded harmonic contour layers"),
    ]

    for idx, (kind, caption) in enumerate(panels):
        x_off = gap + (idx % 2) * (panel_w + gap)
        y_off = 96 + gap + (idx // 2) * (panel_h + gap)
        cv = BBox(0, 0, panel_w, panel_h)
        parts.append(f'  <g transform="translate({x_off} {y_off})">')
        parts.append(
            f'    <rect x="0" y="0" width="{panel_w}" height="{panel_h}" '
            f'fill="#0a0a14" stroke="#3a3a4a" stroke-width="1"/>'
        )
        if kind == "dots":
            p = dots(cv, radius=22, seed=7)
            inner = p.svg(bg=None, fg="#e6e4d2", opacity=0.95)
        elif kind == "flow":
            p = flow(cv, density=18, noise_scale=0.006, length=80, seed=7)
            inner = p.svg(bg=None, fg="#7fdfff", stroke_width=0.7, opacity=0.7)
        elif kind == "grain":
            p = grain(cv, cell=3, tile_cells=64, noise_scale=0.5, seed=7)
            inner = p.svg(bg=None, fg="#e6e4d2", opacity_range=(0.06, 0.36))
        else:
            p = wavefield(cv, layers=4, samples=18, seed=7)
            inner = p.svg(bg=None, title="Seeded harmonic contour layers")
        # Strip the outer <svg> wrapper so the inner content draws in
        # the panel's coordinate space.
        inner_body = _strip_outer_svg(inner)
        parts.append(inner_body)
        # A solid label band keeps contrast independent of generated artwork.
        parts.append(
            f'    <rect x="0" y="{panel_h - 66}" width="{panel_w}" '
            f'height="66" fill="#0a0a14"/>'
        )
        parts.append(
            f'    <text x="14" y="{panel_h - 38}" fill="#e6e4d2" '
            f'font-family="ui-sans-serif,system-ui,sans-serif" '
            f'font-size="16" font-weight="500">{_xml_escape(caption)}</text>'
        )
        parts.append(
            f'    <text x="14" y="{panel_h - 14}" fill="#7fdfff" '
            f'font-family="ui-monospace,monospace" '
            f'font-size="16" font-weight="500">'
            f'{kind}(BBox(0, 0, {panel_w}, {panel_h}), seed=7)</text>'
        )
        parts.append("  </g>")

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _xml_escape(s: str) -> str:
    """Escape ``&``, ``<``, ``>`` for safe SVG text content."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _strip_outer_svg(svg_doc: str) -> str:
    """Remove the outermost <svg ...>...</svg> wrapper, keep contents.

    Used by ``_demo_svg`` to embed standalone-document outputs into the
    panel as drawing groups.
    """
    body = svg_doc
    # Trim opening <svg ...>
    i = body.find("<svg")
    if i >= 0:
        j = body.find(">", i)
        if j >= 0:
            body = body[j + 1 :]
    # Trim closing </svg>
    k = body.rfind("</svg>")
    if k >= 0:
        body = body[:k]
    return body


def _selftest() -> int:
    cv = BBox(0, 0, 1200, 700)

    # Hash determinism.
    assert _hash01(42, 1, 2) == _hash01(42, 1, 2)
    assert _hash01(42, 1, 2) != _hash01(42, 2, 1)
    assert 0.0 <= _hash01(42, 1, 2) < 1.0

    # Value noise in range, deterministic, continuous-ish.
    a = _value_noise2(1.5, 2.5, 7)
    assert 0.0 <= a <= 1.0
    assert _value_noise2(1.5, 2.5, 7) == a
    assert abs(_value_noise2(1.5, 2.5, 7) - _value_noise2(1.51, 2.5, 7)) < 0.1

    # Dots — Bridson invariants.
    p = dots(cv, radius=30, seed=1)
    assert isinstance(p, DotField)
    assert len(p.points) > 50
    for x, y in p.points:
        assert cv.x0 <= x < cv.x1
        assert cv.y0 <= y < cv.y1
    # Pairwise min-distance ≥ radius (sample-check first 200 pairs).
    pts = p.points
    r2 = 30 * 30
    for i in range(min(len(pts), 200)):
        for j in range(i + 1, min(len(pts), 200)):
            dx = pts[i][0] - pts[j][0]
            dy = pts[i][1] - pts[j][1]
            assert dx * dx + dy * dy + 1e-9 >= r2, (
                f"Poisson-disk violation: pts[{i}] & pts[{j}] within radius"
            )

    # Determinism: same seed → identical point set.
    p_again = dots(cv, radius=30, seed=1)
    assert p.points == p_again.points

    # Determinism: different seed → different point set.
    p_other = dots(cv, radius=30, seed=2)
    assert p.points != p_other.points

    # Bad params.
    for bad in (lambda: dots(cv, radius=0),
                lambda: dots(cv, radius=-1),
                lambda: dots(cv, radius=1e6),
                lambda: dots(cv, radius=10, k=0)):
        try:
            bad()
        except PatternError:
            pass
        else:
            raise AssertionError("expected PatternError")

    # Flow — streamline invariants.
    f = flow(cv, density=30, noise_scale=0.005, length=40, step=4, seed=3)
    assert isinstance(f, FlowField)
    assert len(f.polylines) > 10
    for poly in f.polylines:
        assert len(poly) >= 2
        for x, y in poly:
            assert cv.x0 - 1e-6 <= x <= cv.x1 + 1e-6
            assert cv.y0 - 1e-6 <= y <= cv.y1 + 1e-6
    f_again = flow(cv, density=30, noise_scale=0.005, length=40, step=4, seed=3)
    assert f.polylines == f_again.polylines

    # Grain — tile shape + determinism.
    g = grain(cv, cell=3, tile_cells=32, noise_scale=0.5, seed=4)
    assert isinstance(g, Grain)
    assert len(g.values) == 32
    assert all(len(row) == 32 for row in g.values)
    for row in g.values:
        for v in row:
            assert 0.0 <= v <= 1.0
    g_again = grain(cv, cell=3, tile_cells=32, noise_scale=0.5, seed=4)
    assert g.values == g_again.values

    # Wavefield — deterministic generated geometry + truthful series mode.
    w = wavefield(cv, layers=4, samples=18, seed=5)
    assert isinstance(w, WaveField)
    assert w.source == "generated"
    assert len(w.layers) == 4
    assert all(len(layer.points) == 18 for layer in w.layers)
    assert w == wavefield(cv, layers=4, samples=18, seed=5)
    assert w != wavefield(cv, layers=4, samples=18, seed=6)
    semantic = wavefield(
        cv,
        series=((-1.0, -0.25, 0.5, 1.0), (0.2, 0.0, -0.2, 0.0)),
        amplitude=40,
    )
    assert semantic.source == "series"
    assert semantic.layers[0].values == (-1.0, -0.25, 0.5, 1.0)
    assert semantic.layers[0].points[-1][1] < semantic.layers[0].baseline_y
    assert semantic.layers[0].curve_d.startswith("M ")
    assert semantic.layers[0].area_d.endswith(" Z")

    for bad in (
        lambda: wavefield(cv, layers=0),
        lambda: wavefield(cv, samples=3),
        lambda: wavefield(cv, roughness=1.1),
        lambda: wavefield(cv, smoothness=-0.1),
        lambda: wavefield(cv, series=()),
        lambda: wavefield(cv, series=((0.0,),)),
        lambda: wavefield(cv, series=((0.0, 1.2),)),
        lambda: wavefield(cv, layers=2, series=((0.0, 1.0),)),
    ):
        try:
            bad()
        except PatternError:
            pass
        else:
            raise AssertionError("expected PatternError for invalid wavefield")

    # SVG output basics.
    for prim in (p, f, g, w, semantic):
        svg = prim.svg()
        assert svg.startswith("<svg")
        assert svg.rstrip().endswith("</svg>")

    # Grain uses <pattern>.
    g_svg = g.svg()
    assert "<pattern" in g_svg and "url(#grain-" in g_svg

    # bg=None omits the background rect.
    no_bg = dots(cv, radius=60, seed=5).svg(bg=None)
    # Only the dot group should be present; no leading <rect ... fill=...>
    # before the <g>.
    assert no_bg.count("<rect") == 0

    wave_svg = w.svg(title="Signal & field", fill_colors=())
    assert "<title>Signal &amp; field</title>" in wave_svg
    assert 'role="img"' in wave_svg
    assert 'fill="none"' in wave_svg
    assert 'data-source="generated"' in wave_svg

    # Demo renders without crashing.
    demo = _demo_svg()
    assert demo.startswith("<svg")
    assert all(f"{kind}(" in demo for kind in ("dots", "flow", "grain", "wavefield"))

    return 0


def _main(argv: Sequence[str]) -> int:
    import argparse

    p = argparse.ArgumentParser(
        prog="python -m muriel.patterns",
        description="Generative pattern primitives for backgrounds and texture.",
    )
    p.add_argument("--demo", action="store_true",
                   help="render the 1x3 demo SVG (all three primitives)")
    p.add_argument("--kind", choices=["dots", "flow", "grain", "wavefield"],
                   help="render a single primitive at full canvas")
    p.add_argument("--selftest", action="store_true",
                   help="run the assertion suite")
    p.add_argument("--width", type=float, default=1200.0,
                   help="canvas width (default 1200)")
    p.add_argument("--height", type=float, default=700.0,
                   help="canvas height (default 700)")
    p.add_argument("--seed", type=int, default=42,
                   help="determinism seed (default 42)")
    p.add_argument("--bg", default="#0a0a14",
                   help="background fill (default #0a0a14; pass empty for none)")
    p.add_argument("--fg", default=None,
                   help="pattern foreground (default per-kind)")
    p.add_argument("-o", "--output", default="-",
                   help="output file (default: stdout)")
    args = p.parse_args(argv)

    if args.selftest:
        _selftest()
        print("muriel.patterns: selftest passed", file=sys.stderr)
        return 0

    if args.kind:
        cv = BBox(0, 0, args.width, args.height)
        bg = args.bg if args.bg else None
        if args.kind == "dots":
            prim = dots(cv, radius=22, seed=args.seed)
            svg = prim.svg(bg=bg, fg=args.fg or "#e6e4d2")
        elif args.kind == "flow":
            prim = flow(cv, density=18, noise_scale=0.005, length=80,
                        step=4, seed=args.seed)
            svg = prim.svg(bg=bg, fg=args.fg or "#7fdfff")
        elif args.kind == "grain":
            prim = grain(cv, cell=3, tile_cells=64, noise_scale=0.5,
                         seed=args.seed)
            svg = prim.svg(bg=bg, fg=args.fg or "#e6e4d2")
        else:
            prim = wavefield(cv, layers=4, samples=18, seed=args.seed)
            colors = (args.fg,) if args.fg else None
            svg = prim.svg(bg=bg, fill_colors=colors)
    elif args.demo:
        svg = _demo_svg()
    else:
        p.print_help()
        return 0

    if args.output == "-":
        sys.stdout.write(svg)
    else:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
