"""
muriel.tools.diagrams.spectrum — items on one shared scale between two poles.

When to use
-----------
The claim is **where things sit** on one continuous dimension whose two
ends mean something: cooler ↔ warmer, exploratory ↔ confirmatory,
satisficer ↔ optimizer, fully manual ↔ fully automated. Position is the
encoding, so the scale has to be one real, continuous quantity with a unit
(or a documented index) and every item has to be measured on it.

Two row kinds, one per figure:

- **Point** ``{"label", "value"}`` — one dot per item at its value.
- **Range** ``{"label", "start", "end"}`` — a dumbbell. With
  ``range_kind="change"`` (default) it is a before → after pair: the start
  dot is hollow, the end dot is filled, and an arrowhead on the connector
  points at the end, so the direction of change reads in greyscale and
  without the legend's colour. With ``range_kind="extent"`` it is a
  min–max span: both ends are filled and nothing points anywhere, because
  a range has no direction.

Anti-prescription
-----------------
- **Don't use a spectrum for categories without a continuous order.**
  If the items only differ by *how much* of an unordered thing they have,
  that is a bar chart (``muriel.chart``); poles would promise a dimension
  the data does not have.
- **Don't use it when the story is the rank change.** Two states per item
  where what matters is who overtook whom is a slopegraph —
  ``comparison_pair`` — not a dumbbell; a dumbbell shows each item's gap,
  and rank reversals between rows are hard to read off it.
- **Don't use it for many items.** More than 10 rows is a distribution or
  a dot plot; use the chart channel's dot plot, which carries an axis
  designed for density.
- **Don't truncate the scale to make gaps look big.** The axis runs over
  exactly the ``min``/``max`` given, and on a ratio scale that stops short
  of zero the generator refuses to draw until you say so (``zero=False``
  for an interval scale such as a 1–7 Likert, or ``zero=True`` to extend
  the axis to zero). Narrowing the domain draws every gap wider against
  the frame, and the gap is the entire claim.
- **The connector is a gap, not a trajectory.** It says nothing about
  what happened between the two measurements.

Admission record
----------------
Nearest shipped primitive: ``pyramid(proportional=True)``, which already
draws a magnitude honestly — but as the *width of a centred bar*, so it has
no positional axis, cannot place an item left or right of another, cannot
show a negative or interval scale, has no poles, and has no way to draw a
start/end pair. ``matrix`` places things by position but on two *binary*
axes, which is a categorical claim. Neither can say "this item sits here on
one continuous scale, between these two named ends," which is this
generator's whole grammar.

Geometry: dumbbell conventions (hollow reference end, solid focal end,
connector drawn first so the dots cap it, value labels outside the pair,
the floor exception, the never-truncate and never-clamp rules) adapted
from the MIT-licensed diagram-design skill (© 2025 Cathryn Lavery),
``references/type-bar.md`` dumbbell variant. The poles, the zero guard,
the tokens and the 8:1 contrast rule are muriel's own.
"""

from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import Optional, Sequence, Union

from ._a11y import default_desc, figure_slug, legible_on, svg_open
from ._labels import (
    RATIO_MONO,
    RATIO_SANS,
    RATIO_SANS_BOLD,
    fit_text,
    grow_to_fit,
    text_width,
)

__all__ = ["spectrum", "MAX_ROWS"]

MAX_ROWS = 10
_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
_SORTS = ("input", "value", "delta")
_RANGE_KINDS = ("change", "extent")


# ─── Brand → tokens ─────────────────────────────────────────────────

def _resolve(brand) -> dict:
    if brand is None:
        return {
            "bg":        "#0a0a0f",
            "ink":       "#e6e4d2",
            "muted":     "#b0b0c4",
            "accent":    "#7dd4e4",
            "grid":      "rgba(230, 228, 210, 0.10)",
            "axis":      "rgba(230, 228, 210, 0.45)",
            "connector": "rgba(230, 228, 210, 0.55)",
            "body_font": "ui-sans-serif, -apple-system, system-ui, sans-serif",
        }
    c = brand.colors
    viz = brand.viz.categorical if brand.viz.categorical else []
    accent = viz[0] if viz else (c.foreground or "#7dd4e4")
    ink = c.foreground
    return {
        "bg":        c.background,
        "ink":       ink,
        "muted":     c.foreground_muted or ink,
        "accent":    accent,
        "grid":      _rgba(ink, 0.10),
        "axis":      _rgba(ink, 0.45),
        "connector": _rgba(ink, 0.55),
        "body_font": brand.typography.body_family or "system-ui, sans-serif",
    }


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ─── Numbers ────────────────────────────────────────────────────────

def _num(v, what: str) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        raise ValueError(f"{what} must be a number; got {v!r}") from None
    if not math.isfinite(f):
        raise ValueError(f"{what} must be finite; got {v!r}")
    return f


def _decimals(v: float) -> int:
    """Decimals needed to print ``v`` as given, capped at 2."""
    if float(v).is_integer():
        return 0
    s = repr(float(v))
    if "e" in s:
        return 2
    return min(2, len(s.split(".", 1)[1].rstrip("0")))


def _fmt(v: float, decimals: int) -> str:
    """Typographic minus, fixed decimals, thousands separators."""
    s = f"{abs(v):,.{decimals}f}"
    if v < 0 and float(s.replace(",", "")) != 0:
        return "−" + s
    return s


def _nice_step(span: float, target: int = 5) -> float:
    raw = span / target
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= raw:
            return m * mag
    return 10 * mag


def _auto_ticks(lo: float, hi: float) -> list[float]:
    """Round ticks inside the domain, always including both ends.

    An interior tick closer than 40% of a step to either end is dropped so
    its label cannot land on the end label.
    """
    step = _nice_step(hi - lo)
    first = math.ceil(lo / step) * step
    inner = []
    k = 0
    while True:
        t = first + k * step
        if t > hi - 0.4 * step:
            break
        if t >= lo + 0.4 * step:
            inner.append(round(t, 10))
        k += 1
        if k > 100:  # pragma: no cover - defensive
            break
    return [lo] + inner + [hi]


# ─── Spec normalization ─────────────────────────────────────────────

def _normalize_scale(scale: dict, zero: Optional[bool]) -> dict:
    if not isinstance(scale, dict):
        raise ValueError("scale must be a dict with min, max, left_pole, right_pole")
    for k in ("min", "max", "left_pole", "right_pole"):
        if k not in scale:
            raise ValueError(f"scale is missing {k!r}")
    lo = _num(scale["min"], "scale.min")
    hi = _num(scale["max"], "scale.max")
    if not hi > lo:
        raise ValueError(f"scale.max ({hi:g}) must be greater than scale.min ({lo:g})")
    left, right = str(scale["left_pole"]).strip(), str(scale["right_pole"]).strip()
    if not left or not right:
        raise ValueError("both poles need a name — an unnamed end is not a spectrum")

    if zero is None:
        zero = scale.get("zero")
    if zero is None and (lo > 0 or hi < 0):
        raise ValueError(
            f"scale {lo:g}–{hi:g} does not include zero. On a ratio scale that "
            f"truncates the axis and draws every gap wider than the data "
            f"warrant. Pass zero=True to extend the axis to 0, or zero=False "
            f"to confirm this is an interval scale (e.g. a 1–7 rating) whose "
            f"zero means nothing."
        )
    if zero:
        lo, hi = min(lo, 0.0), max(hi, 0.0)

    ticks = scale.get("ticks")
    if ticks is None:
        ticks = _auto_ticks(lo, hi)
    else:
        ticks = [_num(t, "scale.ticks[]") for t in ticks]
        bad = [t for t in ticks if not lo <= t <= hi]
        if bad:
            raise ValueError(
                f"ticks {bad} fall outside the scale {lo:g}–{hi:g}")
        # The domain ends are always ticked: a reader must see where the
        # axis stops, or a truncation is invisible.
        ticks = sorted(set(ticks) | {lo, hi})
    return {"min": lo, "max": hi, "left": left, "right": right,
            "unit": str(scale.get("unit") or ""), "ticks": ticks,
            "label": str(scale.get("label") or "").strip(),
            "zero": bool(zero)}


def _normalize_items(items, sc: dict, focal: Optional[int]) -> tuple[list[dict], str]:
    items = list(items)
    if not items:
        raise ValueError("spectrum needs at least one item")
    if len(items) > MAX_ROWS:
        raise ValueError(
            f"spectrum supports at most {MAX_ROWS} rows; got {len(items)}. "
            f"Past that the rows are a distribution — use the chart channel's "
            f"dot plot, or split the figure."
        )
    out = []
    kinds = set()
    for i, it in enumerate(items):
        if not isinstance(it, dict) or not str(it.get("label", "")).strip():
            raise ValueError(f"item {i} needs a non-empty 'label'")
        has_v = "value" in it
        has_r = "start" in it or "end" in it
        if has_v == has_r:
            raise ValueError(
                f"item {i} ({it['label']!r}) must have either 'value' or both "
                f"'start' and 'end'")
        row = {"label": str(it["label"]), "note": it.get("note"),
               "focal": bool(it.get("focal", False)), "index": i}
        if has_v:
            kinds.add("point")
            row["value"] = _num(it["value"], f"item {i} value")
            vals = [row["value"]]
        else:
            if "start" not in it or "end" not in it:
                raise ValueError(
                    f"item {i} ({it['label']!r}) needs both 'start' and 'end'")
            kinds.add("range")
            row["start"] = _num(it["start"], f"item {i} start")
            row["end"] = _num(it["end"], f"item {i} end")
            vals = [row["start"], row["end"]]
        for v in vals:
            if not sc["min"] <= v <= sc["max"]:
                raise ValueError(
                    f"item {i} ({it['label']!r}) value {v:g} is outside the "
                    f"scale {sc['min']:g}–{sc['max']:g}. Widen the scale; a "
                    f"clamped point would sit where the data is not.")
        out.append(row)
    if len(kinds) > 1:
        raise ValueError(
            "mix of point items and start/end items; one figure carries one "
            "row kind so the legend means one thing")

    if focal is not None:
        if not 0 <= focal < len(out):
            raise ValueError(f"focal index {focal} out of range for {len(out)} items")
        for r in out:
            r["focal"] = r["index"] == focal
    if sum(r["focal"] for r in out) > 1:
        raise ValueError("at most one focal item — one accent per figure")
    return out, kinds.pop()


def _sort(rows: list[dict], kind: str, sort: str) -> list[dict]:
    if sort not in _SORTS:
        raise ValueError(f"sort must be one of {_SORTS}; got {sort!r}")
    if sort == "input":
        return rows
    if sort == "value":
        key = (lambda r: r["value"]) if kind == "point" else (lambda r: r["end"])
        return sorted(rows, key=key, reverse=True)
    if kind == "point":
        raise ValueError("sort='delta' needs start/end items; points have no change")
    return sorted(rows, key=lambda r: r["end"] - r["start"], reverse=True)


# ─── SVG ────────────────────────────────────────────────────────────

def spectrum(
    items: Sequence[dict],
    *,
    scale: dict,
    focal: Optional[int] = None,
    sort: str = "input",
    range_kind: str = "change",
    series: Sequence[str] = ("start", "end"),
    show_values: bool = True,
    show_delta: bool = False,
    zero: Optional[bool] = None,
    title: Optional[str] = None,
    brand=None,
    out_path: Union[str, Path] = "spectrum.svg",
    width: int = 900,
    desc: Optional[str] = None,
) -> str:
    """Render items on one shared continuous scale between two named poles.

    Parameters
    ----------
    items
        1–10 dicts, all of one kind: ``{"label", "value"}`` (points) or
        ``{"label", "start", "end"}`` (dumbbells). Optional ``"note"``
        prints in the right-hand column (overriding the computed delta);
        optional ``"focal": True`` marks the one accented row.
    scale
        ``{"min", "max", "left_pole", "right_pole", "unit"?, "ticks"?,
        "zero"?}``. The axis spans exactly ``min``–``max``; both ends are
        always ticked. ``"%"`` is appended to every printed value, and a
        change in ``%`` is printed in points (``pts``), which is what it
        is. Any other ``unit`` is printed once, in the axis caption under
        the ticks, rather than repeated on every number. ``label`` names
        the measured quantity in that caption (e.g. ``"mean CIELAB b*"``).
    focal
        Index (into ``items`` as given) of the single accented row.
    sort
        ``"input"`` (as given), ``"value"`` (by value, or by end for
        ranges, high to low), or ``"delta"`` (ranges only: by signed change
        ``end − start``, largest increase first). The order used is printed
        under the axis — an unstated order reads as arbitrary.
    range_kind
        ``"change"`` — start → end, hollow start, filled end, arrowhead at
        the end. ``"extent"`` — a min–max span, both ends filled, no
        direction.
    series
        Legend names for the two ends of a range, e.g. ``("before",
        "after")``.
    show_values
        Print each dot's value beside it.
    show_delta
        For ranges, print the signed change (or span, for ``"extent"``)
        in the right-hand column.
    zero
        Required when the scale excludes zero. ``True`` extends the axis
        to zero; ``False`` confirms an interval scale where zero means
        nothing. Left as ``None`` on such a scale, the call raises.
    title, desc, brand, out_path, width
        As for every diagram generator. ``desc`` should state the claim;
        the default only lists the items and their values.

    Returns
    -------
    str
        The path written.
    """
    if range_kind not in _RANGE_KINDS:
        raise ValueError(f"range_kind must be one of {_RANGE_KINDS}; got {range_kind!r}")
    series = tuple(str(s) for s in series)
    if len(series) != 2:
        raise ValueError("series must name exactly two ends, e.g. ('before', 'after')")

    sc = _normalize_scale(scale, zero)
    rows, kind = _normalize_items(items, sc, focal)
    rows = _sort(rows, kind, sort)
    t = _resolve(brand)
    change = kind == "range" and range_kind == "change"

    lo, hi = sc["min"], sc["max"]
    dec = max([_decimals(v) for v in (lo, hi)]
              + [_decimals(r[k]) for r in rows
                 for k in ("value", "start", "end") if k in r])
    unit = sc["unit"]

    def fmt_v(v: float) -> str:
        s = _fmt(v, dec)
        return s + "%" if unit == "%" else s

    def fmt_d(d: float) -> str:
        s = _fmt(abs(d), dec)
        sign = "+" if d > 0 else ("−" if d < 0 else "±")
        u = " pts" if unit == "%" else ""
        return f"{sign}{s}{u}"

    def right_note(r: dict) -> Optional[str]:
        if r["note"]:
            return str(r["note"])
        if show_delta and kind == "range":
            d = r["end"] - r["start"]
            # A span has no sign; the column header already says "span".
            return fmt_d(d) if change else fmt_d(abs(d)).lstrip("+±")
        return None

    # ── Horizontal geometry: measured, grown on the 4px grid ────────
    pad_l, pad_r = 24, 24
    label_gap = 16           # row label end → plot start
    val_gap = 10             # dot centre → value label
    dot_r = 5
    label_fs, val_fs, pole_fs, tick_fs = 13, 10, 12, 10
    label_max = 240          # a row label wraps past this, up to 2 lines

    fitted = []
    for r in rows:
        fit = fit_text(r["label"], label_fs, label_max, max_lines=2,
                       char_width_ratio=RATIO_SANS_BOLD)
        if fit.reason == "line-count":
            raise ValueError(
                f"row label {r['label']!r} needs more than 2 lines at "
                f"{label_max}px; shorten it")
        fitted.append(fit)
    label_w = max(f.width for f in fitted)
    x0 = grow_to_fit(0, pad_l + label_w + label_gap)

    val_w = 0.0
    if show_values:
        val_w = max(text_width(fmt_v(v), val_fs, char_width_ratio=RATIO_MONO)
                    for r in rows for v in
                    ([r["value"]] if kind == "point" else [r["start"], r["end"]]))
    notes = [right_note(r) for r in rows]
    note_w = max((text_width(n, val_fs + 1, char_width_ratio=RATIO_MONO)
                  for n in notes if n), default=0.0)
    if show_delta and kind == "range":
        note_w = max(note_w, text_width("change", 11, char_width_ratio=RATIO_SANS))
    # Ticks carry their own precision: data at 0.1 does not make a tick
    # at 20 read "20.0".
    tick_dec = max(_decimals(v) for v in sc["ticks"])
    tick_labels = [_fmt(v, tick_dec) + ("%" if unit == "%" else "")
                   for v in sc["ticks"]]
    caption = sc["label"]
    if unit and unit != "%":
        caption = (f"{caption} ({unit})" if caption and unit not in caption
                   else (caption or unit))
    tick_half = max(text_width(s, tick_fs, char_width_ratio=RATIO_MONO)
                    for s in tick_labels) / 2

    right_margin = max(tick_half, (val_gap + val_w) if show_values else dot_r)
    note_x_off = right_margin + 20
    if note_w:
        right_margin = note_x_off + note_w
    right_margin = right_margin + pad_r

    # The two poles share a row; they must clear each other with an
    # arrowed rule of at least 48px between them.
    pole_l_w = text_width(sc["left"], pole_fs, char_width_ratio=RATIO_SANS_BOLD)
    pole_r_w = text_width(sc["right"], pole_fs, char_width_ratio=RATIO_SANS_BOLD)
    min_plot = max(360.0, pole_l_w + pole_r_w + 2 * 12 + 48)
    width = int(grow_to_fit(width, x0 + min_plot + right_margin))
    x1 = width - right_margin
    plot_w = x1 - x0

    def X(v: float) -> float:
        """Data → x. Exact and unsnapped: data coordinates are exempt from
        the 4px grid, and rounding here would move the data."""
        return x0 + (v - lo) / (hi - lo) * plot_w

    # ── Vertical geometry ───────────────────────────────────────────
    pitch = 40
    title_h = 64 if title else 0
    pole_y = title_h + (28 if title else 40)                 # pole-row baseline
    rows_top = pole_y + 44                 # first row's centre line
    rows_bot = rows_top + (len(rows) - 1) * pitch
    axis_y = rows_bot + 28
    tick_y = axis_y + 18
    unit_y = tick_y + 16
    foot_y = (unit_y if caption else tick_y) + 32
    order_y = foot_y + (20 if kind == "range" else 0)
    height = int(grow_to_fit(0, order_y + 24))

    # ── Description ─────────────────────────────────────────────────
    order_txt = {
        "input": "rows in the order given",
        "value": ("rows sorted by value, high to low" if kind == "point"
                  else f"rows sorted by {series[1]} value, high to low"),
        "delta": f"rows sorted by change ({series[1]} − {series[0]}), "
                 f"largest increase first",
    }[sort]
    scale_txt = f"{tick_labels[0]} to {tick_labels[-1]}"
    if desc is None:
        if kind == "point":
            row_txt = [f"{r['label']} {fmt_v(r['value'])}" for r in rows]
        else:
            row_txt = [f"{r['label']} {fmt_v(r['start'])} to {fmt_v(r['end'])}"
                       for r in rows]
        desc = default_desc(
            f"Spectrum with {len(rows)} "
            + ("items" if kind == "point" else
               ("before/after pairs" if change else "ranges")),
            title,
            [
                f"scale from {sc['left']} ({fmt_v(lo)}) to {sc['right']} "
                f"({fmt_v(hi)})" + (f", measured as {caption}" if caption else ""),
                ", ".join(row_txt),
                order_txt,
            ],
        )

    slug = figure_slug(out_path, "spectrum")
    parts: list[str] = [svg_open(
        width=width, height=height, slug=slug, title=title or "Spectrum",
        desc=desc, attrs=f'font-family="{escape(t["body_font"])}"',
    )]
    muted_txt = legible_on([t["muted"], t["ink"]], t["bg"], t["bg"])
    accent_txt = legible_on([t["accent"], t["ink"]], t["bg"], t["bg"])

    # Arrowheads: pole rule (muted, both ends) and change connectors.
    parts.append(
        f'<defs>'
        f'<marker id="{slug}-pole" markerWidth="8" markerHeight="8" refX="7" '
        f'refY="4" orient="auto-start-reverse" markerUnits="userSpaceOnUse">'
        f'<path d="M0,0 L8,4 L0,8" fill="none" stroke="{t["axis"]}" '
        f'stroke-width="1.2"/></marker>'
        f'<marker id="{slug}-chg" markerWidth="8" markerHeight="8" refX="7" '
        f'refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M0,0 L8,4 L0,8 Z" fill="{t["connector"]}"/></marker>'
        f'<marker id="{slug}-chg-focal" markerWidth="8" markerHeight="8" '
        f'refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M0,0 L8,4 L0,8 Z" fill="{t["accent"]}"/></marker>'
        f'</defs>'
    )
    parts.append(f'<rect width="{width}" height="{height}" fill="{t["bg"]}"/>')

    if title:
        parts.append(
            f'<text x="{pad_l}" y="{title_h - 24}" fill="{t["ink"]}" '
            f'font-size="20" font-weight="600">{escape(title)}</text>'
        )

    # ── Poles ───────────────────────────────────────────────────────
    parts.append(
        f'<text x="{x0:.1f}" y="{pole_y}" fill="{t["ink"]}" '
        f'font-size="{pole_fs}" font-weight="600" text-anchor="start" '
        f'data-pole="left">{escape(sc["left"])}</text>'
    )
    parts.append(
        f'<text x="{x1:.1f}" y="{pole_y}" fill="{t["ink"]}" '
        f'font-size="{pole_fs}" font-weight="600" text-anchor="end" '
        f'data-pole="right">{escape(sc["right"])}</text>'
    )
    rule_y = pole_y - 4
    parts.append(
        f'<line x1="{x0 + pole_l_w + 12:.1f}" y1="{rule_y}" '
        f'x2="{x1 - pole_r_w - 12:.1f}" y2="{rule_y}" stroke="{t["axis"]}" '
        f'stroke-width="1" marker-start="url(#{slug}-pole)" '
        f'marker-end="url(#{slug}-pole)"/>'
    )

    # ── Grid, zero line, axis, ticks ────────────────────────────────
    grid_top = rows_top - 20
    parts.append(
        f'<g class="spectrum-plot" data-min="{lo!r}" data-max="{hi!r}" '
        f'data-x0="{x0:.3f}" data-x1="{x1:.3f}">'
    )
    for tv in sc["ticks"]:
        tx = X(tv)
        parts.append(
            f'<line x1="{tx:.3f}" y1="{grid_top}" x2="{tx:.3f}" y2="{axis_y}" '
            f'stroke="{t["grid"]}" stroke-width="1"/>'
        )
    if lo < 0 < hi:
        zx = X(0.0)
        parts.append(
            f'<line x1="{zx:.3f}" y1="{grid_top}" x2="{zx:.3f}" y2="{axis_y}" '
            f'stroke="{t["axis"]}" stroke-width="1" data-zero="true"/>'
        )
    parts.append(
        f'<line x1="{x0:.3f}" y1="{axis_y}" x2="{x1:.3f}" y2="{axis_y}" '
        f'stroke="{t["axis"]}" stroke-width="1"/>'
    )
    for tv, tl in zip(sc["ticks"], tick_labels):
        tx = X(tv)
        parts.append(
            f'<line x1="{tx:.3f}" y1="{axis_y}" x2="{tx:.3f}" y2="{axis_y + 4}" '
            f'stroke="{t["axis"]}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{tx:.2f}" y="{tick_y}" fill="{muted_txt}" '
            f'font-family="{_MONO}" font-size="{tick_fs}" text-anchor="middle">'
            f'{escape(tl)}</text>'
        )
    if caption:
        parts.append(
            f'<text x="{(x0 + x1) / 2:.1f}" y="{unit_y}" fill="{muted_txt}" '
            f'font-size="11" text-anchor="middle">{escape(caption)}</text>'
        )
    if show_delta and kind == "range":
        # Header for the computed column, on the pole row, so the signed
        # numbers at the right edge say what they are.
        parts.append(
            f'<text x="{x1 + note_x_off:.1f}" y="{pole_y}" fill="{muted_txt}" '
            f'font-size="11" text-anchor="start">'
            f'{"change" if change else "span"}</text>'
        )

    # ── Rows ────────────────────────────────────────────────────────
    for i, (r, fit) in enumerate(zip(rows, fitted)):
        y = rows_top + i * pitch
        foc = r["focal"]
        lab_fill = accent_txt if foc else t["ink"]
        mark = t["accent"] if foc else t["ink"]
        attrs = [f'data-label="{escape(r["label"])}"']
        if kind == "point":
            attrs.append(f'data-value="{r["value"]!r}"')
        else:
            attrs.append(f'data-start="{r["start"]!r}" data-end="{r["end"]!r}"')
            d = r["end"] - r["start"]
            direction = ("none" if not change or d == 0
                         else ("increase" if d > 0 else "decrease"))
            attrs.append(f'data-direction="{direction}"')
        if foc:
            attrs.append('data-focal="true"')
        parts.append(f'<g class="spectrum-row" {" ".join(attrs)}>')

        # Row label, end-anchored in the measured left margin.
        lines = fit.lines
        base = y + 4 - (len(lines) - 1) * 8
        for k, ln in enumerate(lines):
            parts.append(
                f'<text x="{x0 - label_gap:.1f}" y="{base + 16 * k:.1f}" '
                f'fill="{lab_fill}" font-size="{label_fs}" font-weight="600" '
                f'text-anchor="end">{escape(ln)}</text>'
            )

        if kind == "point":
            vx = X(r["value"])
            parts.append(
                f'<circle cx="{vx:.3f}" cy="{y}" r="{dot_r}" fill="{mark}" '
                f'data-role="point"/>'
            )
            if show_values:
                parts.append(
                    f'<text x="{vx + val_gap:.2f}" y="{y + 4}" fill="{muted_txt}" '
                    f'font-family="{_MONO}" font-size="{val_fs}" '
                    f'text-anchor="start">{escape(fmt_v(r["value"]))}</text>'
                )
        else:
            sx, ex = X(r["start"]), X(r["end"])
            gap = abs(ex - sx)
            conn = t["accent"] if foc else t["connector"]
            # Connector first so the dots cap it. On a change row long
            # enough to hold it, an arrowhead stops just short of the end
            # dot: direction survives greyscale and a missing legend.
            if gap > 2 * dot_r + 1:
                sgn = 1 if ex > sx else -1
                ax1 = sx + sgn * dot_r
                arrow = change and gap >= 2 * dot_r + 14
                ax2 = ex - sgn * (dot_r + (2 if arrow else 0))
                marker = (f' marker-end="url(#{slug}-chg{"-focal" if foc else ""})"'
                          if arrow else "")
                parts.append(
                    f'<line x1="{ax1:.3f}" y1="{y}" x2="{ax2:.3f}" y2="{y}" '
                    f'stroke="{conn}" stroke-width="1.5"{marker}/>'
                )
            if change:
                parts.append(
                    f'<circle cx="{sx:.3f}" cy="{y}" r="{dot_r}" fill="{t["bg"]}" '
                    f'stroke="{mark}" stroke-width="1.5" data-role="start"/>'
                )
            else:
                parts.append(
                    f'<circle cx="{sx:.3f}" cy="{y}" r="{dot_r}" fill="{mark}" '
                    f'data-role="start"/>'
                )
            parts.append(
                f'<circle cx="{ex:.3f}" cy="{y}" r="{dot_r}" fill="{mark}" '
                f'data-role="end"/>'
            )
            if show_values:
                # Labels sit outside the pair by geometry, not by series,
                # so a decreasing row does not put both labels inside it.
                (lv, lx), (rv, rx) = sorted(
                    [(r["start"], sx), (r["end"], ex)], key=lambda p: p[1])
                l_txt, r_txt = fmt_v(lv), fmt_v(rv)
                if lv == rv:
                    l_txt = None  # coincident ends print one value
                if l_txt is not None:
                    lw = text_width(l_txt, val_fs, char_width_ratio=RATIO_MONO)
                    if lx - val_gap - lw < x0 - label_gap + 4:
                        # Floor exception: the label would reach the row
                        # label; lift it above its own dot instead.
                        parts.append(
                            f'<text x="{lx:.2f}" y="{y - 10}" fill="{muted_txt}" '
                            f'font-family="{_MONO}" font-size="{val_fs}" '
                            f'text-anchor="middle">{escape(l_txt)}</text>'
                        )
                    else:
                        parts.append(
                            f'<text x="{lx - val_gap:.2f}" y="{y + 4}" '
                            f'fill="{muted_txt}" font-family="{_MONO}" '
                            f'font-size="{val_fs}" text-anchor="end">'
                            f'{escape(l_txt)}</text>'
                        )
                parts.append(
                    f'<text x="{rx + val_gap:.2f}" y="{y + 4}" fill="{muted_txt}" '
                    f'font-family="{_MONO}" font-size="{val_fs}" '
                    f'text-anchor="start">{escape(r_txt)}</text>'
                )

        note = right_note(r)
        if note:
            parts.append(
                f'<text x="{x1 + note_x_off:.1f}" y="{y + 4}" '
                f'fill="{t["ink"] if foc else muted_txt}" font-family="{_MONO}" '
                f'font-size="{val_fs + 1}" text-anchor="start">'
                f'{escape(note)}</text>'
            )
        parts.append('</g>')
    parts.append('</g>')

    # ── Legend and stated order ─────────────────────────────────────
    if kind == "range":
        lx = x0
        ly = foot_y
        if change:
            parts.append(
                f'<circle cx="{lx + dot_r:.1f}" cy="{ly - 4}" r="{dot_r}" '
                f'fill="{t["bg"]}" stroke="{t["ink"]}" stroke-width="1.5"/>'
            )
            parts.append(
                f'<text x="{lx + 2 * dot_r + 6:.1f}" y="{ly}" fill="{muted_txt}" '
                f'font-size="11">{escape(series[0])}</text>'
            )
            lx += 2 * dot_r + 6 + text_width(series[0], 11,
                                             char_width_ratio=RATIO_SANS) + 20
            parts.append(
                f'<circle cx="{lx + dot_r:.1f}" cy="{ly - 4}" r="{dot_r}" '
                f'fill="{t["ink"]}"/>'
            )
            parts.append(
                f'<text x="{lx + 2 * dot_r + 6:.1f}" y="{ly}" fill="{muted_txt}" '
                f'font-size="11">{escape(series[1])}</text>'
            )
        else:
            parts.append(
                f'<line x1="{lx + dot_r:.1f}" y1="{ly - 4}" x2="{lx + 28:.1f}" '
                f'y2="{ly - 4}" stroke="{t["connector"]}" stroke-width="1.5"/>'
            )
            for cx_ in (lx + dot_r, lx + 28):
                parts.append(
                    f'<circle cx="{cx_:.1f}" cy="{ly - 4}" r="{dot_r}" '
                    f'fill="{t["ink"]}"/>'
                )
            parts.append(
                f'<text x="{lx + 28 + dot_r + 8:.1f}" y="{ly}" fill="{muted_txt}" '
                f'font-size="11">{escape(series[0])} to {escape(series[1])} '
                f'(range)</text>'
            )
    parts.append(
        f'<text x="{x0:.1f}" y="{order_y}" fill="{muted_txt}" font-size="11">'
        f'{escape(order_txt[0].upper() + order_txt[1:])}; axis {escape(scale_txt)}'
        f'{"" if lo <= 0 <= hi else " (does not start at zero)"}.</text>'
    )

    parts.append('</svg>')
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return str(out)


def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.spectrum spec.json out.svg``.

    Spec format::

        {
          "title": "Warmth after a tritan simulation",
          "scale": {"min": -20, "max": 20, "left_pole": "cooler (blue)",
                    "right_pole": "warmer (yellow)", "unit": "b*"},
          "items": [
            {"label": "Wong", "start": 17.4, "end": 5.3},
            {"label": "Nord Frost", "start": -16.2, "end": -7.5}
          ],
          "series": ["as designed", "tritan simulation"],
          "sort": "delta",
          "show_delta": true,
          "brand": "examples/muriel-brand.toml"
        }
    """
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.spectrum")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    spectrum(
        spec["items"],
        scale=spec["scale"],
        focal=spec.get("focal"),
        sort=spec.get("sort", "input"),
        range_kind=spec.get("range_kind", "change"),
        series=tuple(spec.get("series", ("start", "end"))),
        show_values=spec.get("show_values", True),
        show_delta=spec.get("show_delta", False),
        zero=spec.get("zero"),
        title=spec.get("title"),
        brand=brand,
        out_path=args.output,
        desc=spec.get("desc"),
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
