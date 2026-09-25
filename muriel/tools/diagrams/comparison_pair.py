"""
muriel.tools.diagrams.comparison_pair — two states of one item set, side by side.

When to use
-----------
The **same items** measured or traced under **exactly two states** — before
and after, layout A and layout B, policy X and policy Y, condition 1 and
condition 2 — where the argument is *what changed between the states*.
Two forms, chosen by the values:

- **Slopegraph** (``mode="slope"``, numeric values). Two vertical axes on
  **one shared scale**, a line per item joining its A value to its B value.
  The reading is threefold and no other primitive gives all three at once:
  direction (up or down), steepness (how much), and crossings (who overtook
  whom). Every endpoint prints its value, and the B side prints the signed
  change, so increase and decrease read without colour.
- **Trace pair** (``mode="trace"``, status words). The same ordered rules
  evaluated for two subjects — two requests through one approval policy, two
  builds through one gate list. Each rule shows its status in words
  (``PASS`` / ``FAIL`` / ``SKIPPED`` / ``NOT REACHED``) for both traces, and
  the **first divergence** is marked and labeled. This is the "divergent
  policy traces" behaviour row in ``channels/diagrams.md``.

Why a native generator (admission rule)
----------------------------------------
The nearest shipped primitive is ``matrix``: it also puts things side by
side, but its two axes are independent *categories* and it has no value
scale, so it cannot draw a slope, let alone hold two axes to one scale. The
nearest non-native route, a two-series line chart, is honest but spends its
width on an x-axis with two ticks and loses the endpoint labels that make a
slopegraph a table with angles. ``swimlane`` sequences steps under owners
and cannot align two traces rule by rule.

Anti-prescription
-----------------
- **More than two states → a line chart** (or a bump chart for rank).
  A slope between the first and last of five snapshots hides the three in
  between. ``states`` must name exactly two.
- **The story is magnitude on one continuous scale, not change → spectrum.**
  If nothing moved, the lines are flat and the figure argues nothing.
- **Items with no shared scale → a table.** A slope between unlike units
  (ms on the left, % on the right) means nothing; there is one ``scale``
  and both axes use it, always.
- **Don't nudge points apart.** Crowded endpoint labels are data — the
  values are close. This generator moves the *labels* (with a leader tick
  back to the true endpoint) and never the endpoint.
- **Two items identical at both ends cannot be separated** — merge them
  into one labeled line. They raise here rather than draw on top of each
  other.

Geometry follows the editorial-diagram discipline: 4px grid for designed
constants (axis positions, gutters, captions), data-scaled endpoint ``y``
exempt, no gridlines (every endpoint prints its value), no shadows. The
slopegraph conventions — shared-scale rule, run narrower than plot height,
dots at both ends, ink ramp plus one weighted accent, labels bound to their
series with ``data-*`` attributes — are adapted from the MIT-licensed
diagram-design skill (© 2025 Cathryn Lavery), ``references/type-line.md``
(slopegraph variant) and ``scripts/verify-slopegraph.py``. The tokens,
contrast rule, label-nudging policy, and trace form are muriel's own.
"""

from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

from ._a11y import default_desc, figure_slug, legible_on, svg_open
from ._labels import RATIO_MONO, RATIO_SANS_BOLD, grow_to_fit, text_width

__all__ = ["comparison_pair"]

_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
_MINUS = "−"  # typographic minus: same advance as "+", reads as a sign

MAX_ITEMS = 10
MIN_ITEMS = 2
TRACE_MIN, TRACE_MAX = 3, 6


# ─── Brand → tokens ─────────────────────────────────────────────────

def _resolve(brand) -> dict:
    if brand is None:
        return {
            "bg":         "#0a0a0f",
            "ink":        "#e6e4d2",
            "muted":      "#b0b0c4",
            "accent":     "#7dd4e4",
            "line":       "rgba(176, 176, 196, 0.62)",
            "paper":      "rgba(230, 228, 210, 0.04)",
            "focal_fill": "rgba(125, 212, 228, 0.12)",
            "hairline":   "rgba(230, 228, 210, 0.22)",
            "body_font":  "ui-sans-serif, -apple-system, system-ui, sans-serif",
        }
    c = brand.colors
    viz = brand.viz.categorical if brand.viz.categorical else []
    accent = viz[0] if viz else (c.foreground or "#7dd4e4")
    ink = c.foreground
    muted = c.foreground_muted or ink
    return {
        "bg":         c.background,
        "ink":        ink,
        "muted":      muted,
        "accent":     accent,
        "line":       _rgba(muted, 0.62),
        "paper":      _rgba(ink, 0.04),
        "focal_fill": _rgba(accent, 0.12),
        "hairline":   _rgba(ink, 0.22),
        "body_font":  brand.typography.body_family or "system-ui, sans-serif",
    }


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ─── Input normalization ────────────────────────────────────────────

def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _normalize(items, focal) -> tuple[list[dict], Optional[int]]:
    norm = []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            raise TypeError(f"item {i} must be a dict {{label, a, b}}; got {it!r}")
        if "label" not in it or not str(it["label"]).strip():
            raise ValueError(f"item {i} has no label")
        if it.get("a") is None or it.get("b") is None:
            # Never interpolate a missing endpoint: drop the item and say so.
            raise ValueError(
                f"item {it['label']!r} is missing an endpoint; drop it and "
                f"name the omission in desc= rather than inventing a value"
            )
        norm.append({"label": str(it["label"]), "a": it["a"], "b": it["b"],
                     "focal": bool(it.get("focal", False))})

    labels = [n["label"] for n in norm]
    dupes = sorted({x for x in labels if labels.count(x) > 1})
    if dupes:
        raise ValueError(f"duplicate item labels: {dupes}")

    flagged = [i for i, n in enumerate(norm) if n["focal"]]
    if focal is not None:
        if isinstance(focal, (list, tuple)):
            if len(focal) > 1:
                raise ValueError("at most one focal item — two accents is no accent")
            focal = focal[0] if focal else None
    if focal is not None:
        if isinstance(focal, str):
            if focal not in labels:
                raise ValueError(f"focal {focal!r} is not an item label")
            flagged.append(labels.index(focal))
        elif isinstance(focal, int) and not isinstance(focal, bool):
            if focal < 0:
                flagged = []
            elif focal >= len(norm):
                raise ValueError(f"focal index {focal} out of range for {len(norm)} items")
            else:
                flagged.append(focal)
        else:
            raise TypeError(f"focal must be a label, an index, or None; got {focal!r}")
    flagged = sorted(set(flagged))
    if len(flagged) > 1:
        raise ValueError(
            "at most one focal item — two accents is no accent; got "
            + ", ".join(repr(labels[i]) for i in flagged)
        )
    return norm, (flagged[0] if flagged else None)


def _formatter(value_format, values) -> Callable[[float], str]:
    if callable(value_format):
        return value_format
    if isinstance(value_format, str):
        return lambda v: value_format.format(v)
    if value_format is not None:
        raise TypeError("value_format must be a format string, a callable, or None")
    if all(float(v).is_integer() for v in values):
        return lambda v: f"{v:,.0f}"
    return lambda v: f"{v:,.1f}"


def _nice_bounds(lo: float, hi: float) -> tuple[float, float]:
    """Round bounds that contain [lo, hi], on a 1/2/2.5/5 × 10^k step."""
    span = hi - lo
    if span <= 0:
        pad = abs(lo) * 0.1 or 1.0
        lo, hi, span = lo - pad, hi + pad, 2 * pad
    raw = span / 4
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    nlo = math.floor(lo / step) * step
    nhi = math.ceil(hi / step) * step
    # A data set that is all non-negative should not grow a negative bound.
    if lo >= 0 and nlo < 0:
        nlo = 0.0
    return round(nlo, 10), round(nhi, 10)


# ─── Label spreading ────────────────────────────────────────────────

def _spread(desired: Sequence[float], gap: float) -> list[float]:
    """Row centres at least ``gap`` apart, each as close to its target as it can be.

    Classic 1-D cluster relaxation: labels in value order form clusters;
    any two clusters closer than ``gap`` merge, and a cluster is laid out
    at ``gap`` pitch centred on the mean of its members' targets. Order is
    preserved, so labels stay in value order. Deterministic: ties break on
    input index.
    """
    n = len(desired)
    order = sorted(range(n), key=lambda i: (desired[i], i))
    clusters: list[list[int]] = [[i] for i in order]

    def layout(cl: list[int]) -> list[float]:
        mean = sum(desired[i] for i in cl) / len(cl)
        start = mean - gap * (len(cl) - 1) / 2
        return [start + k * gap for k in range(len(cl))]

    changed = True
    while changed:
        changed = False
        merged: list[list[int]] = []
        for cl in clusters:
            if merged:
                prev = merged[-1]
                if layout(cl)[0] - layout(prev)[-1] < gap - 1e-9:
                    merged[-1] = prev + cl
                    changed = True
                    continue
            merged.append(cl)
        clusters = merged

    out = [0.0] * n
    for cl in clusters:
        for i, y in zip(cl, layout(cl)):
            out[i] = y
    return out


# ─── Public entry point ─────────────────────────────────────────────

def comparison_pair(
    items,
    *,
    states: Sequence[str],
    mode: Optional[str] = None,
    focal=None,
    scale: Optional[dict] = None,
    value_format=None,
    title: Optional[str] = None,
    brand=None,
    out_path: Union[str, Path] = "comparison_pair.svg",
    width: int = 0,
    desc: Optional[str] = None,
) -> str:
    """Render one item set under two states: a slopegraph or a trace pair.

    Parameters
    ----------
    items
        ``[{"label": str, "a": value, "b": value, "focal": bool}]`` — the
        same items under state A (``a``) and state B (``b``). Numeric values
        draw a slopegraph (2–10 items); status words draw a trace pair
        (3–6 ordered rules, first to last).
    states
        Exactly two state names, ``(A, B)`` — left axis / left column first.
        More than two is a line chart, not this figure.
    mode
        ``"slope"``, ``"trace"``, or ``None`` to infer from the values.
    focal
        One item to accent, by label or index (or ``"focal": True`` on the
        item). ``-1`` clears an item-level flag. Slope mode only; in trace
        mode the first divergence is the accent, computed from the data.
    scale
        Slope mode: ``{"min": float, "max": float, "unit": str}``. ``min`` /
        ``max`` default to round bounds around the data and must contain
        every value. The same scale is used by both axes — there is no way
        to give the sides different scales. ``unit`` is printed in the
        scale line under the figure.
    value_format
        Slope mode: a format string (``"{:.1f}%"``) or a callable, applied
        to every printed value, delta, and scale bound. Defaults to
        integers with thousands separators, else one decimal.
    title, brand, out_path, desc
        As for every muriel diagram generator. ``desc`` should state what
        the comparison argues; the default lists the values only.
    width
        Minimum canvas width; the canvas grows to fit measured labels.

    Returns
    -------
    str
        The path written.
    """
    states = list(states)
    if len(states) != 2:
        raise ValueError(
            f"comparison_pair takes exactly two states; got {len(states)}. "
            f"More than two states is a line chart (or a bump chart for rank)."
        )
    if not all(str(s).strip() for s in states):
        raise ValueError("both states need a name")
    states = [str(s) for s in states]

    items = list(items)
    values = [v for it in items if isinstance(it, dict)
              for v in (it.get("a"), it.get("b")) if v is not None]
    if mode is None:
        if values and all(_is_number(v) for v in values):
            mode = "slope"
        elif values and all(isinstance(v, str) for v in values):
            mode = "trace"
        else:
            raise ValueError(
                "cannot infer mode: values must be all numbers (slope) or all "
                "status words (trace); pass mode= explicitly"
            )
    if mode == "slope":
        return _slope(items, states, focal, scale, value_format, title,
                      brand, out_path, width, desc)
    if mode == "trace":
        if focal not in (None, -1):
            raise ValueError(
                "trace mode marks the first divergence itself; focal= is not taken"
            )
        return _trace(items, states, title, brand, out_path, width, desc)
    raise ValueError(f"mode must be 'slope', 'trace', or None; got {mode!r}")


# ─── Slopegraph ─────────────────────────────────────────────────────

def _slope(items, states, focal, scale, value_format, title, brand,
           out_path, width, desc) -> str:
    norm, focal_idx = _normalize(items, focal)
    n = len(norm)
    if not MIN_ITEMS <= n <= MAX_ITEMS:
        raise ValueError(
            f"slopegraph supports {MIN_ITEMS}–{MAX_ITEMS} items; got {n}. "
            f"Past {MAX_ITEMS} the endpoint labels crowd into a column; split "
            f"the set or show the top movers."
        )
    for it in norm:
        for end in ("a", "b"):
            v = it[end]
            if not _is_number(v) or not math.isfinite(float(v)):
                raise ValueError(
                    f"item {it['label']!r}: {end}={v!r} is not a finite number"
                )
            it[end] = float(v)
    seen: dict[tuple, str] = {}
    for it in norm:
        key = (it["a"], it["b"])
        if key in seen:
            raise ValueError(
                f"items {seen[key]!r} and {it['label']!r} coincide at both "
                f"ends; merge them into one labeled line"
            )
        seen[key] = it["label"]

    scale = dict(scale or {})
    vals = [it[e] for it in norm for e in ("a", "b")]
    dlo, dhi = min(vals), max(vals)
    nlo, nhi = _nice_bounds(dlo, dhi)
    vmin = float(scale["min"]) if scale.get("min") is not None else nlo
    vmax = float(scale["max"]) if scale.get("max") is not None else nhi
    if not (math.isfinite(vmin) and math.isfinite(vmax)) or vmax <= vmin:
        raise ValueError(f"scale needs finite min < max; got {vmin}..{vmax}")
    if dlo < vmin or dhi > vmax:
        raise ValueError(
            f"scale {vmin:g}..{vmax:g} does not contain the data "
            f"({dlo:g}..{dhi:g}); a clipped endpoint misstates its value"
        )
    unit = scale.get("unit")
    fmt = _formatter(value_format, vals + [vmin, vmax])

    t = _resolve(brand)
    value_ink = legible_on([t["muted"], t["ink"]], t["bg"], t["bg"])

    # ── Type and spacing constants (4px grid) ───────────────────────
    name_fs, val_fs, cap_fs = 13, 11, 13
    row_gap = 16.0        # label pitch: 13px name box is 13.3px tall
    name_gap = 8          # name ↔ value on the left, value ↔ delta ↔ name on the right
    axis_gap = 16         # axis rule ↔ nearest value text (leader ticks live here)
    run = 320             # horizontal run between the axes
    plot_h = 360          # vertical extent of the shared scale
    margin = 32

    def name_w(s: str) -> float:
        return text_width(s, name_fs, char_width_ratio=RATIO_SANS_BOLD)

    def mono_w(s: str) -> float:
        return text_width(s, val_fs, char_width_ratio=RATIO_MONO)

    def delta_text(it) -> str:
        d = it["b"] - it["a"]
        if d == 0:
            return "(0)"
        sign = "+" if d > 0 else _MINUS
        return f"({sign}{fmt(abs(d))})"

    a_txt = [fmt(it["a"]) for it in norm]
    b_txt = [fmt(it["b"]) for it in norm]
    d_txt = [delta_text(it) for it in norm]

    w_name = max(name_w(it["label"]) for it in norm)
    w_a = max(mono_w(s) for s in a_txt)
    w_b = max(mono_w(s) for s in b_txt)
    w_d = max(mono_w(s) for s in d_txt)

    left_block = w_name + name_gap + w_a + axis_gap
    right_block = axis_gap + w_b + name_gap + w_d + name_gap + w_name
    content_w = margin + left_block + run + right_block + margin
    # State captions sit centred over each axis; the canvas must hold them.
    cap_half = max(name_w(s) for s in states) / 2
    content_w = max(content_w,
                    margin + max(left_block, cap_half) + run
                    + max(right_block, cap_half) + margin)
    W = int(grow_to_fit(max(width, 0), content_w))
    x0 = (W - content_w) / 2  # centre the content in a wider canvas
    xa = round(x0 + margin + max(left_block, cap_half))
    xb = xa + run

    # ── Vertical layout ─────────────────────────────────────────────
    title_h = 64 if title else 0
    cap_h = 40               # state captions + breathing room above the plot

    def y_of(v: float, top: float) -> float:
        return top + plot_h * (vmax - v) / (vmax - vmin)

    # Spread labels in plot-relative coordinates first, then find how far
    # the outermost rows reach past the plot so the canvas can hold them.
    ya_rel = [y_of(it["a"], 0.0) for it in norm]
    yb_rel = [y_of(it["b"], 0.0) for it in norm]
    ra_rel = _spread(ya_rel, row_gap)
    rb_rel = _spread(yb_rel, row_gap)
    over_top = max(0.0, -min(ra_rel + rb_rel) + row_gap / 2)
    over_bot = max(0.0, max(ra_rel + rb_rel) - plot_h + row_gap / 2)
    top = title_h + cap_h + math.ceil(over_top / 4) * 4 + 8
    bot = top + plot_h
    foot_y = bot + math.ceil(over_bot / 4) * 4 + 36
    H = int(grow_to_fit(0, foot_y + 20))

    ya = [y + top for y in ya_rel]
    yb = [y + top for y in yb_rel]
    ra = [y + top for y in ra_rel]
    rb = [y + top for y in rb_rel]

    # ── Accessible description ──────────────────────────────────────
    if desc is None:
        unit_txt = f" ({unit})" if unit else ""
        desc = default_desc(
            f"Slopegraph comparing {states[0]} with {states[1]} for {n} items",
            title,
            [f"both axes share one scale, {fmt(vmin)} to {fmt(vmax)}{unit_txt}",
             "; ".join(f"{it['label']}: {a} to {b} {d}"
                       for it, a, b, d in zip(norm, a_txt, b_txt, d_txt))],
        )

    parts: list[str] = [svg_open(
        width=W, height=H, slug=figure_slug(out_path, "comparison-pair"),
        title=title or f"{states[0]} vs {states[1]}", desc=desc,
        attrs=f'font-family="{escape(t["body_font"])}"',
    )]
    parts.append(f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>')
    if title:
        parts.append(
            f'<text x="{W / 2:.1f}" y="40" fill="{t["ink"]}" font-size="20" '
            f'font-weight="600" text-anchor="middle">{escape(title)}</text>')

    # Axes: two rules, one scale — declared on both so a reader (or a gate)
    # can see the scale is shared.
    for end, x, state in (("a", xa, states[0]), ("b", xb, states[1])):
        parts.append(
            f'<line data-axis="{end}" data-state="{escape(state)}" '
            f'data-min="{vmin!r}" data-max="{vmax!r}" data-top="{top:.3f}" '
            f'data-bottom="{bot:.3f}" x1="{x}" y1="{top:.1f}" x2="{x}" '
            f'y2="{bot:.1f}" stroke="{t["hairline"]}" stroke-width="1"/>')
        parts.append(
            f'<text data-axis="{end}" x="{x}" y="{title_h + 24}" '
            f'fill="{t["ink"]}" font-size="{cap_fs}" font-weight="600" '
            f'text-anchor="middle">{escape(state)}</text>')

    # Lines: muted first, the focal item last so it paints on top.
    order = [i for i in range(n) if i != focal_idx]
    if focal_idx is not None:
        order.append(focal_idx)
    for i in order:
        it = norm[i]
        foc = i == focal_idx
        stroke = t["accent"] if foc else t["line"]
        sw = 2.5 if foc else 1.5
        r = 4 if foc else 3
        lab = escape(it["label"])
        parts.append(
            f'<line data-item="{lab}" data-a="{it["a"]!r}" data-b="{it["b"]!r}" '
            f'x1="{xa}" y1="{ya[i]:.3f}" x2="{xb}" y2="{yb[i]:.3f}" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>')
        for end, x, y in (("a", xa, ya[i]), ("b", xb, yb[i])):
            parts.append(
                f'<circle data-item="{lab}" data-end="{end}" cx="{x}" '
                f'cy="{y:.3f}" r="{r}" fill="{stroke}"/>')

    # Labels: each row sits at its spread position; a leader tick joins a
    # displaced row back to the true endpoint, which never moves.
    for i, it in enumerate(norm):
        foc = i == focal_idx
        lab = escape(it["label"])
        weight = "700" if foc else "500"
        for end, x, y_true, y_row in (("a", xa, ya[i], ra[i]),
                                      ("b", xb, yb[i], rb[i])):
            side = -1 if end == "a" else 1
            if abs(y_row - y_true) > 0.5:
                parts.append(
                    f'<line data-item="{lab}" data-end="{end}" data-role="leader" '
                    f'x1="{x + side * 5}" y1="{y_true:.3f}" '
                    f'x2="{x + side * (axis_gap - 3)}" y2="{y_row:.3f}" '
                    f'stroke="{t["hairline"]}" stroke-width="1"/>')
        base_a = ra[i] + 4
        base_b = rb[i] + 4
        vx_a = xa - axis_gap
        nx_a = vx_a - w_a - name_gap
        parts.append(
            f'<text data-item="{lab}" data-end="a" data-role="name" '
            f'x="{nx_a:.1f}" y="{base_a:.1f}" fill="{t["ink"]}" '
            f'font-size="{name_fs}" font-weight="{weight}" '
            f'text-anchor="end">{lab}</text>')
        parts.append(
            f'<text data-item="{lab}" data-end="a" data-role="value" '
            f'x="{vx_a:.1f}" y="{base_a:.1f}" fill="{value_ink}" '
            f'font-family="{_MONO}" font-size="{val_fs}" '
            f'text-anchor="end">{escape(a_txt[i])}</text>')
        vx_b = xb + axis_gap
        dx_b = vx_b + w_b + name_gap
        nx_b = dx_b + w_d + name_gap
        parts.append(
            f'<text data-item="{lab}" data-end="b" data-role="value" '
            f'x="{vx_b:.1f}" y="{base_b:.1f}" fill="{value_ink}" '
            f'font-family="{_MONO}" font-size="{val_fs}" '
            f'text-anchor="start">{escape(b_txt[i])}</text>')
        parts.append(
            f'<text data-item="{lab}" data-end="b" data-role="delta" '
            f'data-delta="{it["b"] - it["a"]!r}" x="{dx_b:.1f}" '
            f'y="{base_b:.1f}" fill="{value_ink}" font-family="{_MONO}" '
            f'font-size="{val_fs}" text-anchor="start">'
            f'{escape(d_txt[i])}</text>')
        parts.append(
            f'<text data-item="{lab}" data-end="b" data-role="name" '
            f'x="{nx_b:.1f}" y="{base_b:.1f}" fill="{t["ink"]}" '
            f'font-size="{name_fs}" font-weight="{weight}" '
            f'text-anchor="start">{lab}</text>')

    # Round bounds print as integers ("0–40", not "0.0–40.0"); the unit
    # travels in parentheses so a format string's own suffix is not doubled.
    bfmt = (_formatter(None, [vmin, vmax])
            if float(vmin).is_integer() and float(vmax).is_integer() else fmt)
    scale_txt = f"both axes: {bfmt(vmin)}–{bfmt(vmax)}"
    if unit:
        scale_txt += f" ({unit})"
    parts.append(
        f'<text data-role="scale" data-min="{vmin!r}" data-max="{vmax!r}" '
        f'x="{(xa + xb) / 2:.1f}" y="{foot_y:.1f}" '
        f'fill="{value_ink}" font-family="{_MONO}" font-size="{val_fs}" '
        f'text-anchor="middle">{escape(scale_txt)}</text>')
    parts.append("</svg>")
    return _write(out_path, parts)


# ─── Trace pair ─────────────────────────────────────────────────────

def _trace(items, states, title, brand, out_path, width, desc) -> str:
    norm, _ = _normalize(items, None)
    n = len(norm)
    if not TRACE_MIN <= n <= TRACE_MAX:
        raise ValueError(
            f"trace pair supports {TRACE_MIN}–{TRACE_MAX} rules; got {n}. "
            f"Fold rules that pass on both traces into one row, or split."
        )
    for it in norm:
        for end in ("a", "b"):
            v = it[end]
            if not isinstance(v, str) or not v.strip():
                raise ValueError(
                    f"rule {it['label']!r}: {end}={v!r} must be a status word "
                    f"(PASS / FAIL / SKIPPED / NOT REACHED)"
                )
            it[end] = v.strip()
    div = next((i for i, it in enumerate(norm) if it["a"] != it["b"]), None)
    if div is None:
        raise ValueError(
            "the two traces never diverge; there is no comparison to draw — "
            "say it in a sentence"
        )

    t = _resolve(brand)
    muted_on_bg = legible_on([t["muted"], t["ink"]], t["bg"], t["bg"])
    ink_on_focal = legible_on([t["ink"]], t["focal_fill"], t["bg"])

    label_fs, status_fs = 13, 12
    row_h, cell_gap, pad = 40, 8, 16
    margin = 32
    rule_w = max(text_width(it["label"], label_fs,
                            char_width_ratio=RATIO_SANS_BOLD) for it in norm)
    status_w = max(text_width(it[e], status_fs, char_width_ratio=RATIO_MONO)
                   for it in norm for e in ("a", "b"))
    head_w = max(text_width(s, label_fs, char_width_ratio=RATIO_SANS_BOLD)
                 for s in states)
    cell_w = grow_to_fit(128, max(status_w, head_w) + 2 * pad)
    note = "first divergence"
    note_w = text_width(note, 11, char_width_ratio=RATIO_MONO)

    content_w = (margin + rule_w + pad + cell_w + cell_gap + cell_w
                 + pad + note_w + margin)
    W = int(grow_to_fit(max(width, 0), content_w))
    x0 = (W - content_w) / 2
    x_rule = x0 + margin + rule_w          # right edge of rule names
    xa = math.ceil((x_rule + pad) / 4) * 4
    xb = xa + cell_w + cell_gap

    title_h = 64 if title else 0
    head_y = title_h + 32
    top = head_y + 16
    H = int(grow_to_fit(0, top + n * row_h + 32))

    if desc is None:
        desc = default_desc(
            f"Two traces, {states[0]} and {states[1]}, through {n} ordered rules",
            title,
            ["; ".join(f"{it['label']}: {it['a']} / {it['b']}" for it in norm),
             f"first divergence at {norm[div]['label']}"],
        )

    parts: list[str] = [svg_open(
        width=W, height=H, slug=figure_slug(out_path, "comparison-pair"),
        title=title or f"{states[0]} vs {states[1]}", desc=desc,
        attrs=f'font-family="{escape(t["body_font"])}"',
    )]
    parts.append(f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>')
    if title:
        parts.append(
            f'<text x="{W / 2:.1f}" y="40" fill="{t["ink"]}" font-size="20" '
            f'font-weight="600" text-anchor="middle">{escape(title)}</text>')
    for end, x, state in (("a", xa, states[0]), ("b", xb, states[1])):
        parts.append(
            f'<text data-axis="{end}" x="{x + cell_w / 2:.1f}" y="{head_y}" '
            f'fill="{t["ink"]}" font-size="{label_fs}" font-weight="600" '
            f'text-anchor="middle">{escape(state)}</text>')

    for i, it in enumerate(norm):
        y = top + i * row_h
        cy = y + row_h / 2
        is_div = i == div
        lab = escape(it["label"])
        parts.append(
            f'<text data-item="{lab}" data-role="name" x="{x_rule:.1f}" '
            f'y="{cy + 4:.1f}" fill="{t["ink"]}" font-size="{label_fs}" '
            f'font-weight="{"700" if is_div else "500"}" '
            f'text-anchor="end">{lab}</text>')
        for end, x in (("a", xa), ("b", xb)):
            fill = t["focal_fill"] if is_div else t["paper"]
            stroke = t["accent"] if is_div else t["hairline"]
            sw = 1.5 if is_div else 1
            parts.append(
                f'<rect data-item="{lab}" data-end="{end}" x="{x}" '
                f'y="{y + 4}" width="{cell_w}" height="{row_h - 8}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
            ink = ink_on_focal if is_div else t["ink"]
            parts.append(
                f'<text data-item="{lab}" data-end="{end}" data-role="status" '
                f'x="{x + cell_w / 2:.1f}" y="{cy + 4:.1f}" fill="{ink}" '
                f'font-family="{_MONO}" font-size="{status_fs}" '
                f'font-weight="{"700" if is_div else "400"}" '
                f'text-anchor="middle">{escape(it[end])}</text>')
        if is_div:
            parts.append(
                f'<text data-role="divergence" data-item="{lab}" '
                f'x="{xb + cell_w + pad:.1f}" y="{cy + 4:.1f}" '
                f'fill="{muted_on_bg}" font-family="{_MONO}" font-size="11" '
                f'text-anchor="start">{note}</text>')
    parts.append("</svg>")
    return _write(out_path, parts)


def _write(out_path, parts) -> str:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return str(out)


def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.comparison_pair spec.json out.svg``.

    Spec format::

        {
          "title":  "Click share by result position",
          "states": ["Ten links", "With answer box"],
          "scale":  {"min": 0, "max": 40, "unit": "% of clicks"},
          "value_format": "{:.1f}",
          "focal":  "Position 1",
          "items": [
            {"label": "Position 1", "a": 38.0, "b": 31.5},
            {"label": "Position 2", "a": 16.5, "b": 17.0}
          ],
          "brand": "examples/muriel-brand.toml"
        }

    Status-word values (``"PASS"``, ``"FAIL"``, …) draw a trace pair.
    """
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.comparison_pair")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    comparison_pair(
        spec["items"],
        states=spec["states"],
        mode=spec.get("mode"),
        focal=spec.get("focal"),
        scale=spec.get("scale"),
        value_format=spec.get("value_format"),
        title=spec.get("title"),
        brand=brand,
        out_path=args.output,
        desc=spec.get("desc"),
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
