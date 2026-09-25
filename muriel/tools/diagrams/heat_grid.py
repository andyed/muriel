"""
muriel.tools.diagrams.heat_grid — comparison heat-grid as SVG.

When to use
-----------
**Epistemic precondition:** an unsigned quantity measured at every
crossing of two categorical factors — rows × columns — where the claim is
about the *pattern* across the whole table: which crossings run hot,
whether one row or column carries the effect, where a single cell breaks
from the field. Mean fixation dwell by SERP position × query intent; CI
failure rate by service × sprint; ticket volume by team × week.

Fill opacity on a single-hue ramp is the only quantitative channel.
Position says "which row, which column", nothing more, and it is carried
by the labels.

Why this is not :func:`~muriel.tools.diagrams.matrix`
---------------------------------------------------
``matrix`` is a named 2×2 categorical decomposition: four cells, each a
*class* with a label and bullets, no number anywhere. A heat grid is the
opposite contract — 3–7 × 3–8 cells whose content is one measured value
each, encoded by fill and optionally printed. Stretching ``matrix`` to N×M
would give it a quantity channel it has no honest way to scale.

Anti-prescription
-----------------
- **One row or one column is a bar chart.** A 1×N heat grid encodes by
  opacity what a bar would encode by length, the channel readers compare
  most accurately. The generator refuses fewer than 3 rows or columns.
- **If the reader needs exact values more than the pattern, use a
  table.** Printed values help, but a heat grid's job is comparative;
  retrieval of a specific number is what a table is for.
- **No hue per row or column.** Hue says "which series", not "how much".
- **No diverging ramp for unsigned data.** Signed data (deltas,
  correlations) needs a diverging treatment with a meaningful centre; it
  is not in scope here, and negative values raise.
- **No gradient legend.** The legend is stepped swatches with numeric
  bounds, and the cells are quantized to exactly those steps, so the
  legend is the scale rather than an impression of it.
- **No silently dropped rows or columns.** A ragged ``values`` table
  raises; a missing measurement is ``None`` and is drawn as an explicit
  "n/a" cell, never as a blank that reads as zero.

The contrast constraint (why the ramp ceiling moves)
----------------------------------------------------
Printed values must clear 8:1 against the *composited* cell, and each
cell's text is ink or paper, whichever clears it (computed, not an opacity
threshold). But ink and paper are themselves only ~15:1 apart, so over the
middle of any ink-on-paper ramp **neither** clears 8:1: for muriel's OLED
default that band runs from about 0.25 to 0.75 opacity. With
``show_values=True`` the ramp ceiling is therefore solved per brand, as
the highest opacity below which every fill still has a legible text colour.
With ``show_values=False`` no text sits on the fill and the ramp uses the
full 0.07–0.70 range.

Geometry and ramp bounds adapted from the MIT-licensed diagram-design
skill (© 2025 Cathryn Lavery), ``references/type-heatmap.md`` and
``scripts/verify-heatmap.py``; the tokens, contrast solve, quantized
legend and epistemic gate are muriel's own.
"""

from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

from ._a11y import default_desc, figure_slug, legible_on, svg_open
from ._labels import (
    RATIO_MONO,
    RATIO_SANS,
    RATIO_SANS_BOLD,
    grow_to_fit,
    text_width,
    wrap_measured,
)

__all__ = ["heat_grid"]

_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

MIN_ROWS, MAX_ROWS = 3, 7
MIN_COLS, MAX_COLS = 3, 8
RAMP_FLOOR = 0.07      # the smallest cell must still separate from paper
RAMP_CEILING = 0.70    # upstream bound when no text sits on the fill
_REQUIRED = 8.0


# ─── Brand → tokens ─────────────────────────────────────────────────

def _resolve(brand) -> dict:
    """Colors and fonts the heat grid needs, from the brand or muriel's
    OLED defaults. The ramp hue is ink; the accent marks the focal cell
    only, so the two never compete for "how much"."""
    if brand is None:
        return {
            "bg":         "#0a0a0f",
            "ink":        "#e6e4d2",
            "muted":      "#b0b0c4",
            "accent":     "#7dd4e4",
            "hairline":   "rgba(230, 228, 210, 0.14)",
            "body_font":  "ui-sans-serif, -apple-system, system-ui, sans-serif",
            "mono_font":  _MONO,
        }
    c = brand.colors
    viz = brand.viz.categorical if brand.viz.categorical else []
    accent = c.accent or (viz[0] if viz else c.foreground)
    ink = c.foreground
    return {
        "bg":         c.background,
        "ink":        ink,
        "muted":      c.foreground_muted or ink,
        "accent":     accent,
        "hairline":   _rgba(ink, 0.14),
        "body_font":  brand.typography.body_family or "system-ui, sans-serif",
        "mono_font":  brand.typography.mono_family or _MONO,
    }


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = _rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha:g})"


# ─── Ramp ───────────────────────────────────────────────────────────

def _best_text_ratio(hue: str, alpha: float, candidates, bg: str) -> float:
    """Highest contrast any candidate text colour reaches on the cell."""
    from muriel.contrast import _composite, contrast_ratio, parse_color
    behind = _composite(parse_color(hue), alpha, parse_color(bg))
    return max(contrast_ratio(parse_color(c), behind) for c in candidates)


def _solve_ceiling(hue: str, bg: str, candidates, floor: float,
                   want: float) -> float:
    """Highest opacity ≤ ``want`` such that every fill from ``floor`` up
    to it leaves some candidate text colour at 8:1 or better.

    Walks up in 0.005 steps and stops at the first failure, so the
    admitted range is contiguous — a ramp that skipped the dead band and
    resumed above it would exaggerate the step across the gap.
    """
    ceiling = None
    a = floor
    while a <= want + 1e-9:
        if _best_text_ratio(hue, round(a, 3), candidates, bg) < _REQUIRED:
            break
        ceiling = round(a, 3)
        a += 0.005
    if ceiling is None:
        raise ValueError(
            "no fill on this brand's ramp leaves ink or paper text at 8:1 "
            "(ink vs background contrast is too low to print values); "
            "pass show_values=False or use a higher-contrast brand"
        )
    return ceiling


def _nice_step(span: float, steps: int) -> float:
    """A 1/2/2.5/5 × 10^k bin width whose bin count over ``[0, span]`` is
    closest to ``steps`` (ties go to the coarser step)."""
    if span <= 0:
        return 1.0
    mag = 10 ** math.floor(math.log10(span / max(1, steps)))
    best, best_err = None, None
    for k in (mag / 10, mag, mag * 10):
        for m in (1, 2, 2.5, 5):
            s = m * k
            err = abs(math.ceil(span / s - 1e-9) - steps)
            if best_err is None or err < best_err or (err == best_err and s > best):
                best, best_err = s, err
    return best


def _fmt_bound(v: float) -> str:
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,g}"


# ─── Input validation ───────────────────────────────────────────────

def _check_values(rows, cols, values) -> list[list[Optional[float]]]:
    if len(values) != len(rows):
        raise ValueError(
            f"values has {len(values)} rows but {len(rows)} row labels; "
            f"every row must be drawn — a dropped row reads as absent data"
        )
    out: list[list[Optional[float]]] = []
    for r, row in enumerate(values):
        row = list(row)
        if len(row) != len(cols):
            raise ValueError(
                f"row {rows[r]!r} has {len(row)} values but there are "
                f"{len(cols)} columns; use None for a missing measurement "
                f"rather than leaving the row short"
            )
        clean: list[Optional[float]] = []
        for c, v in enumerate(row):
            if v is None:
                clean.append(None)
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise TypeError(
                    f"value at ({rows[r]!r}, {cols[c]!r}) is {v!r}; "
                    f"expected a number or None")
            v = float(v)
            if not math.isfinite(v):
                raise ValueError(
                    f"value at ({rows[r]!r}, {cols[c]!r}) is {v}; use None "
                    f"for a missing measurement")
            if v < 0:
                raise ValueError(
                    f"value at ({rows[r]!r}, {cols[c]!r}) is negative ({v:g}). "
                    f"heat_grid encodes unsigned quantities on a single-hue "
                    f"ramp; signed data (deltas, correlations) needs a "
                    f"diverging treatment with a meaningful centre, which "
                    f"this generator does not draw")
            clean.append(v)
        out.append(clean)
    return out


def _index(key, labels: Sequence[str], axis: str) -> int:
    if isinstance(key, int) and not isinstance(key, bool):
        if not 0 <= key < len(labels):
            raise ValueError(f"focal {axis} index {key} out of range")
        return key
    try:
        return list(labels).index(key)
    except ValueError:
        raise ValueError(f"focal {axis} {key!r} is not a {axis} label") from None


# ─── SVG ────────────────────────────────────────────────────────────

def heat_grid(
    rows: Sequence[str],
    cols: Sequence[str],
    values: Sequence[Sequence[Optional[float]]],
    *,
    focal: Optional[tuple] = None,
    focal_note: Optional[str] = None,
    show_values: bool = True,
    value_format: Union[str, Callable[[float], str], None] = None,
    unit: Optional[str] = None,
    row_title: Optional[str] = None,
    col_title: Optional[str] = None,
    steps: int = 5,
    title: Optional[str] = None,
    brand=None,
    out_path: Union[str, Path] = "heat-grid.svg",
    desc: Optional[str] = None,
) -> str:
    """Render a rows × columns comparison heat grid.

    Parameters
    ----------
    rows, cols
        Category labels: 3–7 rows, 3–8 columns, each unique. Outside that
        range the call raises — see the module's anti-prescription.
    values
        ``values[r][c]``, one number per crossing. Non-negative;
        ``None`` marks a missing measurement, drawn as a hatched "n/a"
        cell. Ragged tables raise.
    focal
        Optional ``(row, col)`` — indices or labels — for the one cell
        the figure is about. It is **excluded from the scale maximum** (an
        outlier would otherwise flatten every other cell), stroked in the
        accent, and its value is stated in the legend and ``<desc>``.
    focal_note
        Optional short gloss for the focal key ("deploy regression").
    show_values
        Print each value in its cell. Text colour is ink or paper,
        whichever clears 8:1 on the composited fill; the ramp ceiling is
        solved so that one always does (see module docstring).
    value_format
        ``str.format`` pattern (``"{:,.0f}"``) or a callable for in-cell
        numbers. Defaults to ``{:,g}``.
    unit
        What the values measure, e.g. ``"mean fixation dwell (ms)"``. Heads
        the legend and the description.
    row_title, col_title
        Optional axis names (the factor each axis enumerates).
    steps
        Target number of legend steps. Bin edges are rounded to 1/2/2.5/5
        × 10^k, so the drawn count can differ by one or two; cells are
        quantized to the drawn bins.
    title
        Optional heading above the grid.
    brand
        Optional ``muriel.styleguide.StyleGuide``.
    out_path
        Where to write the SVG. Its stem also prefixes the accessible
        ``<title>``/``<desc>`` ids and the n/a hatch pattern id.
    desc
        What the figure argues, for the SVG ``<desc>``. Defaults to a
        conservative description that lists every row's values and states
        no claim of its own.

    Returns
    -------
    str
        The path written.

    Every cell rect carries ``data-row``, ``data-col`` and ``data-value``
    (``"n/a"`` for a missing value); the focal cell adds
    ``data-focal="true"``. The values can be recomputed from the file.
    """
    rows = [str(r) for r in rows]
    cols = [str(c) for c in cols]
    for n, lo, hi, axis, other in (
        (len(rows), MIN_ROWS, MAX_ROWS, "rows", "column"),
        (len(cols), MIN_COLS, MAX_COLS, "columns", "row"),
    ):
        if n < lo:
            raise ValueError(
                f"heat_grid needs {lo}–{hi} {axis}; got {n}. A comparison "
                f"along a single {other} is a bar chart, and a table this "
                f"small says it with less ink")
        if n > hi:
            raise ValueError(
                f"heat_grid supports at most {hi} {axis}; got {n}. Cells "
                f"shrink below readability — split the figure or facet it")
    for labels, axis in ((rows, "row"), (cols, "column")):
        dup = sorted({x for x in labels if labels.count(x) > 1})
        if dup:
            raise ValueError(f"duplicate {axis} labels {dup}; each "
                             f"{axis} must be identifiable")
    if steps < 2:
        raise ValueError(f"steps must be >= 2; got {steps}")

    grid = _check_values(rows, cols, values)
    nr, nc = len(rows), len(cols)
    t = _resolve(brand)

    focal_rc: Optional[tuple[int, int]] = None
    if focal is not None:
        fr, fc = focal
        focal_rc = (_index(fr, rows, "row"), _index(fc, cols, "column"))
        if grid[focal_rc[0]][focal_rc[1]] is None:
            raise ValueError("the focal cell has no value; a focal n/a "
                             "cell makes no claim to point at")

    if value_format is None:
        fmt: Callable[[float], str] = lambda v: f"{v:,g}"  # noqa: E731
    elif callable(value_format):
        fmt = value_format
    else:
        fmt = value_format.format

    # ── Scale: focal excluded from the max ──────────────────────────
    scale_vals = [
        v for r, row in enumerate(grid) for c, v in enumerate(row)
        if v is not None and (r, c) != focal_rc
    ]
    vmax = max(scale_vals, default=0.0)
    step = _nice_step(vmax if vmax > 0 else 1.0, steps)
    n_bins = max(1, math.ceil((vmax if vmax > 0 else 1.0) / step - 1e-9))
    edges = [i * step for i in range(n_bins + 1)]

    text_candidates = [t["ink"], t["bg"]]
    ceiling = RAMP_CEILING
    if show_values:
        ceiling = _solve_ceiling(t["ink"], t["bg"], text_candidates,
                                 RAMP_FLOOR, RAMP_CEILING)
    if n_bins == 1:
        bin_alpha = [ceiling]
    else:
        bin_alpha = [round(RAMP_FLOOR + (ceiling - RAMP_FLOOR) * i / (n_bins - 1), 3)
                     for i in range(n_bins)]

    def bin_of(v: float) -> int:
        return max(0, min(n_bins - 1, int(v // step)))

    # ── Measure labels, then size the grid ──────────────────────────
    pad = 40
    gap = 4
    cell_h = 56
    label_fs = 12
    value_fs = 13
    lab_gap = 12       # row label end to grid
    val_pad = 10       # value text inset from the cell's sides

    grid_budget = 800
    cell_w = max(80.0, min(116.0, (grid_budget - gap * (nc - 1)) / nc))

    value_txt = [[fmt(v) if v is not None else "n/a" for v in row]
                 for row in grid]
    widest_val = max(
        text_width(s, value_fs, char_width_ratio=RATIO_MONO)
        for row in value_txt for s in row)
    need = widest_val + 2 * val_pad if show_values else 0
    # A column label may wrap to two lines; a single word never splits.
    for c in cols:
        for w in c.split():
            need = max(need, text_width(w, label_fs,
                                        char_width_ratio=RATIO_SANS_BOLD) + 8)
    cell_w = grow_to_fit(cell_w, need)
    col_lines = [wrap_measured(c, label_fs, cell_w - 8,
                               char_width_ratio=RATIO_SANS_BOLD) for c in cols]
    n_col_lines = max(len(ls) for ls in col_lines)
    if n_col_lines > 2:
        # Too many rows of heading text: widen rather than stack three deep.
        widest_col = max(text_width(c, label_fs,
                                    char_width_ratio=RATIO_SANS_BOLD)
                         for c in cols)
        cell_w = grow_to_fit(cell_w, widest_col / 2 + 24)
        col_lines = [wrap_measured(c, label_fs, cell_w - 8,
                                   char_width_ratio=RATIO_SANS_BOLD)
                     for c in cols]
        n_col_lines = max(len(ls) for ls in col_lines)

    row_w = max(text_width(r, label_fs, char_width_ratio=RATIO_SANS_BOLD)
                for r in rows)
    if row_title:
        # The row axis name sits in the table's top-left corner, end-anchored
        # over the row labels, so it shares their column.
        row_w = max(row_w, text_width(row_title.upper(), 10,
                                      char_width_ratio=RATIO_MONO,
                                      letter_spacing=1.5))
    grid_x = float(4 * math.ceil((pad + row_w + lab_gap) / 4))

    title_h = 48 if title else 0
    col_title_h = 22 if col_title else 0
    col_lab_h = n_col_lines * 16 + 6
    grid_y = pad + title_h + col_title_h + col_lab_h
    grid_w = nc * cell_w + (nc - 1) * gap
    grid_h = nr * cell_h + (nr - 1) * gap

    # ── Legend geometry ─────────────────────────────────────────────
    legend_fs = 11
    bound_fs = 10
    bound_txt = [f"{_fmt_bound(edges[i])}–{_fmt_bound(edges[i + 1])}"
                 for i in range(n_bins)]
    sw_w = max(56.0, max(text_width(b, bound_fs, char_width_ratio=RATIO_MONO)
                         for b in bound_txt) + 10)
    sw_w = float(4 * math.ceil(sw_w / 4))
    sw_h = 16
    sw_gap = 4
    swatches_w = n_bins * sw_w + (n_bins - 1) * sw_gap
    legend_head = unit or "value"
    legend_head_w = text_width(legend_head, legend_fs, char_width_ratio=RATIO_SANS)

    has_na = any(v is None for row in grid for v in row)
    focal_line = None
    if focal_rc is not None:
        fr, fc = focal_rc
        fv = grid[fr][fc]
        focal_line = (f"{rows[fr]} × {cols[fc]} = {fmt(fv)}"
                      + (f" {_unit_short(unit)}" if _unit_short(unit) else "")
                      + " — excluded from the scale"
                      + (f"; {focal_note}" if focal_note else ""))
    na_line = "n/a — no measurement for this crossing"
    key_w = 28   # key swatch width
    key_lines = [s for s in (focal_line, na_line if has_na else None) if s]
    key_text_w = max((text_width(s, legend_fs, char_width_ratio=RATIO_SANS)
                      for s in key_lines), default=0.0)

    content_w = max(grid_w, legend_head_w, swatches_w, key_w + 10 + key_text_w)
    width = int(grow_to_fit(0, grid_x + content_w + pad))

    legend_y = grid_y + grid_h + 32          # legend heading baseline
    sw_y = legend_y + 10
    bound_y = sw_y + sw_h + 14
    key_y0 = bound_y + 28
    key_step = 26
    height = int(grow_to_fit(0, key_y0 + len(key_lines) * key_step + pad - 8))

    # ── Description ─────────────────────────────────────────────────
    if desc is None:
        u = f" of {unit}" if unit else ""
        row_txt = [
            f"{rows[r]}: " + ", ".join(
                f"{cols[c]} {value_txt[r][c]}" for c in range(nc))
            for r in range(nr)]
        desc = default_desc(
            f"Heat grid{u}, {nr} rows by {nc} columns",
            title,
            [f"rows{f' ({row_title})' if row_title else ''}: " + ", ".join(rows),
             f"columns{f' ({col_title})' if col_title else ''}: " + ", ".join(cols),
             "darker fill means a higher value, in "
             f"{n_bins} steps from {_fmt_bound(edges[0])} to "
             f"{_fmt_bound(edges[-1])}",
             (f"focal cell {focal_line}" if focal_line else ""),
             ("n/a marks a missing measurement" if has_na else ""),
             "values by row — " + "; ".join(row_txt)])

    slug = figure_slug(out_path, "heat-grid")
    na_id = f"{slug}-na-hatch"

    parts: list[str] = []
    parts.append(svg_open(
        width=width, height=height, slug=slug,
        title=title or "Heat grid", desc=desc,
        attrs=f'font-family="{escape(t["body_font"])}"',
    ))
    if has_na:
        parts.append(
            f'<defs><pattern id="{na_id}" width="8" height="8" '
            f'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<path d="M0,0 L0,8" stroke="{t["hairline"]}" stroke-width="2"/>'
            f'</pattern></defs>')
    parts.append(f'<rect width="{width}" height="{height}" fill="{t["bg"]}"/>')

    if title:
        parts.append(
            f'<text x="{grid_x:.1f}" y="{pad + 20:.1f}" fill="{t["ink"]}" '
            f'font-size="20" font-weight="600">{escape(title)}</text>')

    if col_title:
        parts.append(
            f'<text x="{grid_x + grid_w / 2:.1f}" y="{pad + title_h + 12:.1f}" '
            f'fill="{t["muted"]}" font-family="{escape(t["mono_font"])}" '
            f'font-size="10" letter-spacing="1.5" text-anchor="middle">'
            f'{escape(col_title.upper())}</text>')

    # Column labels, bottom-aligned just above the grid.
    for c, lines in enumerate(col_lines):
        cx = grid_x + c * (cell_w + gap) + cell_w / 2
        base = grid_y - 10 - (len(lines) - 1) * 16
        for k, line in enumerate(lines):
            parts.append(
                f'<text x="{cx:.1f}" y="{base + k * 16:.1f}" fill="{t["ink"]}" '
                f'font-size="{label_fs}" font-weight="600" '
                f'text-anchor="middle">{escape(line)}</text>')

    if row_title:
        parts.append(
            f'<text x="{grid_x - lab_gap:.1f}" y="{grid_y - 10:.1f}" '
            f'fill="{t["muted"]}" font-family="{escape(t["mono_font"])}" '
            f'font-size="10" letter-spacing="1.5" text-anchor="end">'
            f'{escape(row_title.upper())}</text>')

    # ── Cells ───────────────────────────────────────────────────────
    ink_rgb = _rgb(t["ink"])
    focal_svg: list[str] = []
    for r in range(nr):
        cy = grid_y + r * (cell_h + gap)
        parts.append(
            f'<text x="{grid_x - lab_gap:.1f}" y="{cy + cell_h / 2 + 4:.1f}" '
            f'fill="{t["ink"]}" font-size="{label_fs}" font-weight="600" '
            f'text-anchor="end">{escape(rows[r])}</text>')
        for c in range(nc):
            cx = grid_x + c * (cell_w + gap)
            v = grid[r][c]
            attrs = (f'data-row="{escape(rows[r])}" data-col="{escape(cols[c])}" '
                     f'data-value="{"n/a" if v is None else f"{v:g}"}"')
            geom = (f'x="{cx:.1f}" y="{cy:.1f}" width="{cell_w:.1f}" '
                    f'height="{cell_h}"')
            mid_x = cx + cell_w / 2
            mid_y = cy + cell_h / 2 + 4.5
            if v is None:
                parts.append(
                    f'<rect {attrs} data-missing="true" {geom} '
                    f'fill="url(#{na_id})" stroke="{t["hairline"]}" '
                    f'stroke-width="1" stroke-dasharray="3 3"/>')
                # The hatch is scenery; "n/a" sits on a solid paper plate so
                # its contrast is the plate's, not the hatch's.
                tw = text_width("n/a", value_fs, char_width_ratio=RATIO_MONO)
                pw, ph = tw + 12, 20
                parts.append(
                    f'<rect x="{mid_x - pw / 2:.1f}" y="{cy + (cell_h - ph) / 2:.1f}" '
                    f'width="{pw:.1f}" height="{ph}" fill="{t["bg"]}"/>')
                na_fill = legible_on([t["muted"], t["ink"]], t["bg"], t["bg"])
                parts.append(
                    f'<text x="{mid_x:.1f}" y="{mid_y:.1f}" fill="{na_fill}" '
                    f'font-family="{escape(t["mono_font"])}" '
                    f'font-size="{value_fs}" text-anchor="middle">n/a</text>')
                continue
            is_focal = (r, c) == focal_rc
            alpha = bin_alpha[bin_of(min(v, vmax) if is_focal else v)]
            fill = f"rgba({ink_rgb[0]}, {ink_rgb[1]}, {ink_rgb[2]}, {alpha:g})"
            if is_focal:
                attrs += ' data-focal="true"'
            parts.append(f'<rect {attrs} {geom} fill="{fill}"/>')
            if is_focal:
                # Stroke drawn after every cell so no neighbour paints over it.
                focal_svg.append(
                    f'<rect x="{cx - 1:.1f}" y="{cy - 1:.1f}" '
                    f'width="{cell_w + 2:.1f}" height="{cell_h + 2}" '
                    f'fill="none" stroke="{t["accent"]}" stroke-width="2.5"/>')
            if show_values:
                txt_fill = legible_on(text_candidates, fill, t["bg"])
                weight = ' font-weight="700"' if is_focal else ""
                parts.append(
                    f'<text x="{mid_x:.1f}" y="{mid_y:.1f}" fill="{txt_fill}" '
                    f'font-family="{escape(t["mono_font"])}" '
                    f'font-size="{value_fs}"{weight} text-anchor="middle">'
                    f'{escape(value_txt[r][c])}</text>')
    parts.extend(focal_svg)

    # ── Legend: stepped swatches with numeric bounds ────────────────
    parts.append(
        f'<text x="{grid_x:.1f}" y="{legend_y:.1f}" fill="{t["muted"]}" '
        f'font-size="{legend_fs}">{escape(legend_head)}</text>')
    for i in range(n_bins):
        sx = grid_x + i * (sw_w + sw_gap)
        parts.append(
            f'<rect x="{sx:.1f}" y="{sw_y:.1f}" width="{sw_w:.1f}" '
            f'height="{sw_h}" fill="rgba({ink_rgb[0]}, {ink_rgb[1]}, '
            f'{ink_rgb[2]}, {bin_alpha[i]:g})"/>')
        parts.append(
            f'<text x="{sx + sw_w / 2:.1f}" y="{bound_y:.1f}" '
            f'fill="{t["muted"]}" font-family="{escape(t["mono_font"])}" '
            f'font-size="{bound_fs}" text-anchor="middle">'
            f'{escape(bound_txt[i])}</text>')

    ky = key_y0
    if focal_line:
        parts.append(
            f'<rect x="{grid_x + 1:.1f}" y="{ky - 12:.1f}" width="{key_w - 2}" '
            f'height="14" fill="none" stroke="{t["accent"]}" stroke-width="2.5"/>')
        parts.append(
            f'<text x="{grid_x + key_w + 10:.1f}" y="{ky:.1f}" '
            f'fill="{t["ink"]}" font-size="{legend_fs}">'
            f'{escape(focal_line)}</text>')
        ky += key_step
    if has_na:
        parts.append(
            f'<rect x="{grid_x:.1f}" y="{ky - 13:.1f}" width="{key_w}" '
            f'height="16" fill="url(#{na_id})" stroke="{t["hairline"]}" '
            f'stroke-width="1" stroke-dasharray="3 3"/>')
        parts.append(
            f'<text x="{grid_x + key_w + 10:.1f}" y="{ky:.1f}" '
            f'fill="{t["muted"]}" font-size="{legend_fs}">'
            f'{escape(na_line)}</text>')

    parts.append("</svg>")

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return str(out)


def _unit_short(unit: Optional[str]) -> str:
    """The parenthesised unit from ``"mean dwell (ms)"`` → ``"ms"``."""
    if not unit:
        return ""
    if unit.endswith(")") and "(" in unit:
        return unit[unit.rfind("(") + 1:-1].strip()
    return ""


def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.heat_grid spec.json out.svg``.

    Spec format::

        {
          "title":  "Mean fixation dwell by SERP position",
          "rows":   ["1", "2", "3"],
          "cols":   ["nav", "info", "tx"],
          "values": [[410, 530, 480], [300, null, 350], [220, 260, 240]],
          "unit":   "mean fixation dwell (ms)",
          "focal":  [0, 1],
          "brand":  "examples/muriel-brand.toml"      # optional
        }
    """
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.heat_grid")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    focal = spec.get("focal")
    heat_grid(
        spec["rows"], spec["cols"], spec["values"],
        focal=tuple(focal) if focal else None,
        focal_note=spec.get("focal_note"),
        show_values=spec.get("show_values", True),
        value_format=spec.get("value_format"),
        unit=spec.get("unit"),
        row_title=spec.get("row_title"),
        col_title=spec.get("col_title"),
        steps=spec.get("steps", 5),
        title=spec.get("title"),
        brand=brand,
        out_path=args.output,
        desc=spec.get("desc"),
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
