"""
muriel.tools.diagrams.treemap — squarified part-of-whole treemap as SVG.

When to use
-----------
One total that decomposes into **4–8 parts**, where the reader's question
is *"what dominates, and by how much?"* — share of fixation time by page
region, spend by category, bundle bytes by package, time allocation. Area
is the only encoding: each cell's area is its share of the whole, and the
squarified layout keeps cells near-square so two areas can be compared by
eye.

Epistemic precondition: the parts are **disjoint** and **sum to a
meaningful whole**. The figure claims "these are all the pieces, and this
is how big each is"; if either half of that is false the figure lies.

Anti-prescription
-----------------
- **Don't use a treemap when the values are roughly equal.** Uniform area
  carries no signal — the reader compares near-identical rectangles and
  learns nothing a list wouldn't say. Use a list, or a dendrogram if the
  structure is the point. (The generator warns when the largest value is
  within 25% of the smallest.)
- **Don't use a treemap for parts that don't sum to a meaningful whole**
  — overlapping categories, independent measurements, rates. Area-of-whole
  is then a fiction. Use a bar chart.
- **Don't use a treemap when exact values matter more than proportion.**
  Area is compared coarsely; a ranked bar chart reads values precisely.
- **Don't draw more than 8 cells.** Past 8 the tail becomes unlabelable
  slivers. Collapse the tail into a named "Other" (``max_cells=``) and
  say in ``desc=`` what it holds.

What the generator never does: clip a cell, floor a small one to make it
visible, log-scale, rotate a label, resize a cell to fit its label, or
drop a cell. A cell too small to draw raises instead.

Layout: squarified (Bruls, Huizing & van Wijk 2000). Label tiers, the
rank-ordered ink ramp, the single accent cell, ``data-share`` on every
cell and the relative-area-error framing are adapted from the MIT-licensed
diagram-design skill (© 2025 Cathryn Lavery), ``type-treemap.md`` and
``scripts/verify-treemap.py``; the gutter-compensating layout, tokens,
contrast rule and epistemic gate are muriel's own.

Not yet: nesting (one level of grouping). A second level needs its own
border weight and label tier; it is left for the hierarchy family rather
than bolted on here.
"""

from __future__ import annotations

import math
import warnings
from html import escape
from pathlib import Path
from typing import Callable, Optional, Union

from ._a11y import default_desc, figure_slug, legible_on, svg_open
from ._labels import (
    RATIO_MONO,
    RATIO_SANS_BOLD,
    fit_text,
    grow_to_fit,
    text_width,
)

__all__ = ["treemap"]

_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

MIN_CELLS = 4
MAX_CELLS = 8
GUTTER = 4.0
INSET = 16.0          # top-left label inset inside a cell
PAD_END = 12.0        # right / bottom clearance a label must leave
MIN_SIDE = 2.0        # a drawn cell narrower than this cannot carry area honestly
MARKER_R = 4.0        # sliver locator disc
MARKER_MIN = 12.0     # a sliver this big on both axes gets the disc

# Type: name 13px/600 sans, value line 10px mono. Baselines from the cell
# top, derived from muriel.layout's ascent 0.80 / descent 0.22 so the
# read-back verifier sees no collision between lines.
_NAME_PX = 13
_NAME_BASE = INSET + 11.0          # first name baseline (ascent 10.4 → 11)
_NAME_LEAD = 16.0                  # second wrapped name line
_VAL_PX = 10
_VAL_GAP = 16.0                    # last name baseline → value baseline
_SUB_GAP = 14.0                    # value baseline → sublabel baseline
_NAME_DESC = 0.22 * _NAME_PX
_VAL_DESC = 0.22 * _VAL_PX


# ─── Brand → tokens ─────────────────────────────────────────────────

def _resolve(brand) -> dict:
    if brand is None:
        return {
            "bg":        "#0a0a0f",
            "ink":       "#e6e4d2",
            "muted":     "#b0b0c4",
            "accent":    "#7dd4e4",
            "body_font": "ui-sans-serif, -apple-system, system-ui, sans-serif",
            "mono_font": _MONO,
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
        "body_font": brand.typography.body_family or "system-ui, sans-serif",
        "mono_font": brand.typography.mono_family or _MONO,
    }


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha:.3f})"


# ─── Formatting ─────────────────────────────────────────────────────

def _default_fmt(v: float) -> str:
    v = float(v)
    if float(v).is_integer():
        return f"{int(v):,}"
    return f"{v:,.4g}" if abs(v) < 100 else f"{v:,.0f}"


def _fmt_share(pct: float) -> str:
    """Displayed share. Coarse where coarse is honest, finer for small parts."""
    if pct >= 10:
        return f"{pct:.0f}%"
    if pct >= 0.1:
        return f"{pct:.1f}%"
    return "<0.1%"


# ─── Input normalization ────────────────────────────────────────────

def _normalize(cells, max_cells: Optional[int], other_label: str) -> list[dict]:
    out = []
    for i, c in enumerate(cells):
        if not isinstance(c, dict):
            raise TypeError(f"cell {i} must be a dict with 'label' and 'value'")
        try:
            v = float(c["value"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"cell {i} ({c.get('label')!r}) needs a numeric 'value'")
        if not math.isfinite(v) or v <= 0:
            # A zero or negative part has no area. Dropping it silently
            # would misstate the whole; say so instead.
            raise ValueError(
                f"cell {c.get('label')!r} has value {c['value']!r}; treemap "
                f"values must be finite and > 0. Remove the part explicitly "
                f"(and say so in desc=) or use a bar chart")
        out.append({
            "label":    str(c.get("label", "")),
            "short":    c.get("short"),
            "sublabel": c.get("sublabel"),
            "value":    v,
            "focal":    bool(c.get("focal", False)),
            "members":  None,
        })

    if max_cells is not None and not MIN_CELLS <= max_cells <= MAX_CELLS:
        raise ValueError(f"max_cells must be {MIN_CELLS}–{MAX_CELLS}; got {max_cells}")

    if len(out) > MAX_CELLS or (max_cells is not None and len(out) > max_cells):
        if max_cells is None:
            raise ValueError(
                f"treemap supports {MIN_CELLS}–{MAX_CELLS} cells; got {len(out)}. "
                f"Past {MAX_CELLS} the tail becomes unlabelable slivers. Pass "
                f"max_cells={MAX_CELLS} to collapse the smallest parts into one "
                f"named {other_label!r} cell, or merge them yourself")
        ranked = sorted(out, key=lambda c: -c["value"])
        keep, tail = ranked[: max_cells - 1], ranked[max_cells - 1:]
        if any(c["focal"] for c in tail):
            raise ValueError(
                "the focal cell would be collapsed into "
                f"{other_label!r}; raise max_cells or pick another focal cell")
        members = [c["label"] for c in tail]
        keep.append({
            "label":    other_label,
            "short":    None,
            "sublabel": f"{len(members)} smaller parts",
            "value":    sum(c["value"] for c in tail),
            "focal":    False,
            "members":  members,
        })
        out = keep

    if len(out) < MIN_CELLS:
        raise ValueError(
            f"treemap supports {MIN_CELLS}–{MAX_CELLS} cells; got {len(out)}. "
            f"Two or three parts read better as a bar or a sentence")
    if sum(c["focal"] for c in out) > 1:
        raise ValueError("at most one cell may be focal")
    return out


# ─── Squarified layout ──────────────────────────────────────────────

def _worst(row: list[float], side: float) -> float:
    """Worst aspect ratio in ``row`` laid along a side of length ``side``."""
    s = sum(row)
    if s <= 0 or side <= 0:
        return math.inf
    s2, w2 = s * s, side * side
    return max(max(w2 * r / s2, s2 / (w2 * r)) for r in row)


def _squarify(weights: list[float], x: float, y: float,
              w: float, h: float) -> list[tuple[float, float, float, float]]:
    """Bruls/Huizing/van Wijk squarified layout of ``weights`` (in order).

    Weights are scaled so they tile ``w × h`` exactly. Each row is laid
    against the shorter side of the remaining rectangle, and grows while
    adding the next item does not worsen the row's worst aspect ratio.
    """
    total = sum(weights)
    areas = [wt * (w * h) / total for wt in weights]
    rects: list[tuple[float, float, float, float]] = []
    i, n = 0, len(areas)
    while i < n:
        side = min(w, h)
        row = [areas[i]]
        i += 1
        while i < n and _worst(row + [areas[i]], side) <= _worst(row, side):
            row.append(areas[i])
            i += 1
        s = sum(row)
        last = i == n
        if w >= h:           # short side is vertical: a column at the left
            # The last row takes whatever remains, so float drift cannot
            # leave a hairline of unassigned area at the far edge.
            cw = w if last else (s / h if h > 0 else 0.0)
            yy = y
            for a in row:
                rh = a / s * h
                rects.append((x, yy, cw, rh))
                yy += rh
            x += cw
            w -= cw
        else:                # short side is horizontal: a row at the top
            rh = h if last else (s / w if w > 0 else 0.0)
            xx = x
            for a in row:
                cw = a / s * w
                rects.append((xx, y, cw, rh))
                xx += cw
            y += rh
            h -= rh
    return rects


def _layout(values: list[float], px: float, py: float, pw: float, ph: float,
            gutter: float) -> list[tuple[float, float, float, float]]:
    """Squarified cells in the plot rect, gutters included, area-corrected.

    Gutters are made by laying out in the plot rect grown by half a gutter
    on every side and then insetting each cell by half a gutter: outer
    edges land on the plot edge and every shared edge becomes a full
    gutter. But an inset takes a bigger bite out of a small cell than a
    large one (a 30×30 cell loses 25% of its area, a 300×300 one 3%), so
    drawn shares drift from true shares. The weights are corrected
    iteratively — each is scaled by true/drawn share and the layout redone
    — and the best layout seen is kept. Order is fixed by the true values,
    so the correction only moves edges; it never reorders cells.
    """
    total = sum(values)
    target = [v / total for v in values]
    g2 = gutter / 2
    weights = list(target)
    best, best_err = None, math.inf
    for _ in range(60):
        raw = _squarify(weights, px - g2, py - g2, pw + gutter, ph + gutter)
        drawn = [(x + g2, y + g2, w - gutter, h - gutter) for x, y, w, h in raw]
        areas = [max(w, 0.0) * max(h, 0.0) for _, _, w, h in drawn]
        a_tot = sum(areas)
        if a_tot <= 0:
            break
        shares = [a / a_tot for a in areas]
        err = max(abs(s - t) / t for s, t in zip(shares, target))
        if all(w >= MIN_SIDE and h >= MIN_SIDE for _, _, w, h in drawn) \
                and err < best_err:
            best, best_err = drawn, err
        if err < 1e-4:
            break
        weights = [wt * (t / s if s > 0 else 2.0)
                   for wt, t, s in zip(weights, target, shares)]
    if best is None:
        raise ValueError(
            "the smallest part is too small to draw at this size once gutters "
            "are taken out; collapse the tail into a named 'Other' "
            "(max_cells=) or use a bar chart")
    return best


# ─── Label tiers ────────────────────────────────────────────────────

def _fits(lines_w: float, lines_h: float, w: float, h: float) -> bool:
    return INSET + lines_w + PAD_END <= w and lines_h + PAD_END <= h


def _plan_labels(cell: dict, w: float, h: float, value_txt: str,
                 share_txt: str) -> dict:
    """Pick the richest label tier that fits, measured. Never resizes."""
    avail = w - INSET - PAD_END

    def name_lines(text: str) -> Optional[tuple[str, ...]]:
        fit = fit_text(text, _NAME_PX, max(avail, 1.0), max_lines=2,
                       char_width_ratio=RATIO_SANS_BOLD)
        return None if fit.needs_growth else fit.lines

    def vw(s: str) -> float:
        return text_width(s, _VAL_PX, char_width_ratio=RATIO_MONO)

    lines = name_lines(cell["label"])
    if lines:
        name_w = max(text_width(ln, _NAME_PX, char_width_ratio=RATIO_SANS_BOLD)
                     for ln in lines)
        last_name = _NAME_BASE + _NAME_LEAD * (len(lines) - 1)
        val_base = last_name + _VAL_GAP
        full = f"{value_txt} · {share_txt}"
        # large: name + value + share (+ sublabel if it also fits)
        if _fits(max(name_w, vw(full)), val_base + _VAL_DESC, w, h):
            plan = {"tier": "large", "name": lines, "value": full, "sub": None}
            sub = cell["sublabel"]
            if sub and _fits(vw(sub), val_base + _SUB_GAP + _VAL_DESC, w, h):
                plan["sub"] = sub
            return plan
        # medium: name + value
        if _fits(max(name_w, vw(value_txt)), val_base + _VAL_DESC, w, h):
            return {"tier": "medium", "name": lines, "value": value_txt,
                    "sub": None}
    # small: one line — the short name if given, else the full name
    for cand in ([cell["short"]] if cell["short"] else []) + [cell["label"]]:
        cw = text_width(cand, _NAME_PX, char_width_ratio=RATIO_SANS_BOLD)
        if _fits(cw, _NAME_BASE + _NAME_DESC, w, h):
            return {"tier": "small", "name": (cand,), "value": None, "sub": None}
    return {"tier": "sliver", "name": (), "value": None, "sub": None}


def _position_phrase(cx: float, cy: float, px: float, py: float,
                     pw: float, ph: float) -> str:
    col = ("left", "centre", "right")[min(2, int(3 * (cx - px) / pw))]
    row = ("top", "middle", "bottom")[min(2, int(3 * (cy - py) / ph))]
    if row == "middle" and col == "centre":
        return "centre"
    if row == "middle":
        return f"middle {col}"
    if col == "centre":
        return f"{row} centre"
    return f"{row} {col}"


# ─── SVG ────────────────────────────────────────────────────────────

def treemap(
    cells,
    *,
    title: Optional[str] = None,
    brand=None,
    unit: str = "",
    value_format: Optional[Callable[[float], str]] = None,
    max_cells: Optional[int] = None,
    other_label: str = "Other",
    out_path: Union[str, Path] = "treemap.svg",
    width: int = 960,
    plot_height: int = 480,
    desc: Optional[str] = None,
) -> str:
    """Render a 4–8 cell squarified treemap.

    Parameters
    ----------
    cells
        Dicts ``{"label": str, "value": float, "focal": bool,
        "sublabel": str, "short": str}``, any order (they are drawn
        largest first). ``value`` must be finite and > 0. ``short`` is an
        honest abbreviation used when the full name will not fit.
        ``sublabel`` is drawn under the value line only in cells large
        enough to hold it; it always reaches the ``<desc>``. At most one
        cell may be ``focal`` — the editorially focal one, not
        automatically the largest; it takes the accent tint and stroke.
    unit
        Appended to every printed value, e.g. ``" s"`` or ``" ms"``.
    value_format
        ``float -> str`` for printed values. Default: integers with
        thousands separators, else four significant figures.
    max_cells
        ``None`` (default) raises on more than 8 cells. An integer 4–8
        collapses the smallest parts into one cell named ``other_label``
        so that at most ``max_cells`` are drawn; the collapsed names are
        listed in the default ``<desc>`` and in the cell's
        ``data-members``. Collapsing is never silent: it only happens when
        asked for.
    title, brand, out_path, desc
        As for every muriel diagram. ``desc`` should state what the figure
        argues; the default lists the parts, values and shares only.
    width, plot_height
        Canvas width and plot-area height in px. The canvas grows downward
        to hold the legend; cells never resize to fit text.

    Label tiers
    -----------
    Chosen per cell by measured fit, top-left inset 16px:
    **large** — name, then ``value · share``; **medium** — name, value;
    **small** — the name (or ``short``) alone; **sliver** — no text in the
    cell, a locator disc if the cell is at least 12×12px. Every cell whose
    value is not printed in place (small and sliver) gets a legend line
    below the plot with its name, value and share; slivers also give
    their position. Labels are never rotated and a cell is never resized.

    Every cell ``<rect>`` carries ``data-value``, ``data-share`` (percent
    of the whole), ``data-label`` and ``data-tier``.

    Returns
    -------
    str
        The path written.
    """
    norm = _normalize(cells, max_cells, other_label)
    norm.sort(key=lambda c: -c["value"])  # stable: ties keep caller order
    n = len(norm)
    t = _resolve(brand)
    fmt = value_format or _default_fmt

    values = [c["value"] for c in norm]
    total = sum(values)
    if max(values) <= 1.25 * min(values):
        warnings.warn(
            "treemap values are within 25% of each other; uniform area "
            "carries no signal — a list (or a dendrogram, if structure is the "
            "point) says the same thing more honestly",
            stacklevel=2,
        )

    # ── Geometry (4px grid for the frame; cell edges are data) ──────
    margin = 32
    title_h = 72 if title else 0
    px, py = float(margin), float(title_h + 16 if title else margin)
    pw, ph = float(width - 2 * margin), float(plot_height)
    rects = _layout(values, px, py, pw, ph, GUTTER)

    shares = [v / total * 100 for v in values]
    share_txt = [_fmt_share(s) for s in shares]
    value_txt = [f"{fmt(v)}{unit}" for v in values]

    # Tint ramp by rank: strongest on the largest part. Low opacity keeps
    # ink text above 8:1 on every step; legible_on still checks each cell.
    ramp = [0.16 - (0.16 - 0.05) * (i / (n - 1)) for i in range(n)]

    plans = []
    for i, (c, (x, y, w, h)) in enumerate(zip(norm, rects)):
        plans.append(_plan_labels(c, w, h, value_txt[i], share_txt[i]))

    n_sliver = sum(p["tier"] == "sliver" for p in plans)
    if n_sliver >= 3:
        warnings.warn(
            f"{n_sliver} of {n} cells are too small to label in place; when "
            f"several parts are only legible in the legend, the data wants a "
            f"bar chart (or collapse them with max_cells=)",
            stacklevel=2,
        )

    # ── Legend: every part whose value is not printed in its cell ───
    legend_items = []
    sliver_pos: dict[int, str] = {}
    for i, (p, (x, y, w, h)) in enumerate(zip(plans, rects)):
        if p["tier"] == "sliver":
            sliver_pos[i] = _position_phrase(x + w / 2, y + h / 2, px, py, pw, ph)
    # Two slivers in one region need a tiebreak the reader can apply.
    by_pos: dict[str, list[int]] = {}
    for i, pos in sliver_pos.items():
        by_pos.setdefault(pos, []).append(i)
    for pos, idxs in by_pos.items():
        if len(idxs) > 1:
            # reading order: top to bottom, then left to right
            idxs.sort(key=lambda j: (round(rects[j][1]), rects[j][0]))
            for k, j in enumerate(idxs):
                sliver_pos[j] = (f"{pos}, {_ordinal(k + 1)} of {len(idxs)} "
                                 f"in reading order")

    for i, p in enumerate(plans):
        if p["tier"] not in ("small", "sliver"):
            continue
        c = norm[i]
        head = c["label"]
        if p["tier"] == "small" and p["name"][0] != c["label"]:
            head = f'{p["name"][0]} = {c["label"]}'
        txt = f"{head} · {value_txt[i]} · {share_txt[i]}"
        if i in sliver_pos:
            txt += f" · {sliver_pos[i]}"
        legend_items.append((i, txt))

    enc = f"Area is proportional to value. Total {fmt(total)}{unit}."
    shown = [s for s in share_txt if not s.startswith("<")]
    if len(shown) == n:
        disp_sum = sum(float(s.rstrip("%")) for s in shown)
        if abs(disp_sum - 100.0) > 1e-6:
            enc += " Shares rounded; they may not sum to 100%."

    # Legend rows wrap on measured width; the canvas grows to hold them.
    sw = 12.0          # swatch size
    key_gap = 8.0
    item_gap = 28.0
    row_h = 24.0
    enc_y = py + ph + 28
    rows: list[list[tuple[int, str, float]]] = []
    cur: list[tuple[int, str, float]] = []
    cur_w = 0.0
    for i, txt in legend_items:
        iw = sw + key_gap + text_width(txt, 11, char_width_ratio=RATIO_MONO)
        need = iw if not cur else cur_w + item_gap + iw
        if cur and need > pw:
            rows.append(cur)
            cur, cur_w = [], 0.0
            need = iw
        cur.append((i, txt, iw))
        cur_w = need
    if cur:
        rows.append(cur)
    widest_row = max((sum(it[2] for it in r) + item_gap * (len(r) - 1)
                      for r in rows), default=0.0)
    enc_w = text_width(enc, 10, char_width_ratio=RATIO_MONO)
    width = int(grow_to_fit(width, max(widest_row, enc_w) + 2 * margin))
    legend_y0 = enc_y + 28
    last_base = legend_y0 + (len(rows) - 1) * row_h if rows else enc_y
    height = int(grow_to_fit(0, last_base + margin))

    # ── Description ─────────────────────────────────────────────────
    if desc is None:
        parts_txt = []
        for i, c in enumerate(norm):
            extra = [value_txt[i], share_txt[i]]
            if c["sublabel"]:
                extra.append(c["sublabel"])
            if c["members"]:
                extra.append("combines " + ", ".join(c["members"]))
            parts_txt.append(f'{c["label"]} ({"; ".join(extra)})')
        focal_i = next((i for i, c in enumerate(norm) if c["focal"]), None)
        desc = default_desc(
            f"Treemap with {n} parts",
            title,
            [
                "largest to smallest: " + ", ".join(parts_txt),
                f"area proportional to value; total {fmt(total)}{unit}",
                (f"highlighted: {norm[focal_i]['label']}"
                 if focal_i is not None else ""),
            ],
        )

    parts: list[str] = [svg_open(
        width=width, height=height,
        slug=figure_slug(out_path, "treemap"),
        title=title or "Treemap", desc=desc,
        attrs=f'font-family="{escape(t["body_font"])}"',
    )]
    parts.append(f'<rect width="{width}" height="{height}" fill="{t["bg"]}"/>')
    if title:
        parts.append(
            f'<text x="{width / 2:.1f}" y="{title_h - 24:.1f}" fill="{t["ink"]}" '
            f'font-size="20" font-weight="600" text-anchor="middle">'
            f'{escape(title)}</text>')

    mono = escape(t["mono_font"])
    fills = [_rgba(t["accent"], 0.14) if c["focal"] else _rgba(t["ink"], ramp[i])
             for i, c in enumerate(norm)]
    # One text colour per role across every cell, chosen by computed
    # contrast against each composited fill — so the value line does not
    # flip between muted and ink from cell to cell. Only if no single
    # candidate clears 8:1 everywhere does a cell pick its own.
    name_all = _legible_everywhere([t["ink"], t["bg"]], fills, t["bg"])
    val_all = _legible_everywhere([t["muted"], t["ink"], t["bg"]], fills, t["bg"])
    for i, (c, p, (x, y, w, h)) in enumerate(zip(norm, plans, rects)):
        fill = fills[i]
        if c["focal"]:
            stroke, sw_ = t["accent"], 1.5
        else:
            stroke, sw_ = _rgba(t["ink"], 0.28), 1
        members = (f' data-members="{escape("; ".join(c["members"]))}"'
                   if c["members"] else "")
        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'rx="2" fill="{fill}" stroke="{stroke}" stroke-width="{sw_}" '
            f'data-label="{escape(c["label"])}" data-value="{c["value"]:g}" '
            f'data-share="{shares[i]:.4f}" data-tier="{p["tier"]}"{members}/>')

        # Name: ink, or paper for a brand whose ink fails on a tinted cell.
        # Value line: muted, stepping up to ink.
        name_fill = name_all or legible_on([t["ink"], t["bg"]], fill, t["bg"])
        val_fill = val_all or legible_on([t["muted"], t["ink"], t["bg"]],
                                         fill, t["bg"])
        tx = x + INSET
        base = y + _NAME_BASE
        for k, ln in enumerate(p["name"]):
            parts.append(
                f'<text x="{tx:.2f}" y="{base + k * _NAME_LEAD:.2f}" '
                f'fill="{name_fill}" font-size="{_NAME_PX}" font-weight="600">'
                f'{escape(ln)}</text>')
        if p["value"]:
            vy = base + _NAME_LEAD * (len(p["name"]) - 1) + _VAL_GAP
            parts.append(
                f'<text x="{tx:.2f}" y="{vy:.2f}" fill="{val_fill}" '
                f'font-family="{mono}" font-size="{_VAL_PX}">'
                f'{escape(p["value"])}</text>')
            if p["sub"]:
                parts.append(
                    f'<text x="{tx:.2f}" y="{vy + _SUB_GAP:.2f}" fill="{val_fill}" '
                    f'font-family="{mono}" font-size="{_VAL_PX}">'
                    f'{escape(p["sub"])}</text>')
        if p["tier"] == "sliver" and w >= MARKER_MIN and h >= MARKER_MIN:
            parts.append(
                f'<circle cx="{x + w / 2:.2f}" cy="{y + h / 2:.2f}" '
                f'r="{MARKER_R:g}" fill="{name_fill}" data-marker="sliver"/>')

    # ── Encoding line + legend ──────────────────────────────────────
    enc_fill = legible_on([t["muted"], t["ink"]], t["bg"], t["bg"])
    parts.append(
        f'<text x="{px:.1f}" y="{enc_y:.1f}" fill="{enc_fill}" '
        f'font-family="{mono}" font-size="10">{escape(enc)}</text>')
    for r, row in enumerate(rows):
        ly = legend_y0 + r * row_h
        lx = px
        for i, txt, iw in row:
            c = norm[i]
            if c["focal"]:
                fill, stroke, sw_ = (_rgba(t["accent"], 0.14), t["accent"], 1.5)
            else:
                fill, stroke, sw_ = (_rgba(t["ink"], ramp[i]),
                                     _rgba(t["ink"], 0.28), 1)
            parts.append(
                f'<rect x="{lx:.1f}" y="{ly - 10:.1f}" width="{sw:g}" '
                f'height="{sw:g}" rx="2" fill="{fill}" stroke="{stroke}" '
                f'stroke-width="{sw_}" data-key="{escape(c["label"])}"/>')
            if plans[i]["tier"] == "sliver":
                parts.append(
                    f'<circle cx="{lx + sw / 2:.1f}" cy="{ly - 4:.1f}" r="3" '
                    f'fill="{legible_on([t["ink"], t["bg"]], fill, t["bg"])}"/>')
            parts.append(
                f'<text x="{lx + sw + key_gap:.1f}" y="{ly:.1f}" fill="{enc_fill}" '
                f'font-family="{mono}" font-size="11">{escape(txt)}</text>')
            lx += iw + item_gap

    parts.append("</svg>")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return str(out)


def _legible_everywhere(candidates, surfaces, page_bg: str,
                        required: float = 8.0) -> Optional[str]:
    """First candidate that clears ``required`` on every surface, else None."""
    from muriel.contrast import (
        _color_alpha, _composite, contrast_ratio, parse_color,
    )
    base = parse_color(page_bg) or (0, 0, 0)
    behind = []
    for srf in surfaces:
        rgb = parse_color(srf)
        behind.append(_composite(rgb, _color_alpha(srf), base) if rgb else base)
    for c in candidates:
        fg = parse_color(c)
        if fg and all(contrast_ratio(fg, b) >= required for b in behind):
            return c
    return None


def _ordinal(k: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(k, f"{k}th")


def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.treemap spec.json out.svg``.

    Spec format::

        {
          "title": "Share of fixation time by SERP region",
          "unit":  " s",
          "max_cells": 8,
          "cells": [
            {"label": "Organic results", "value": 41.2, "focal": true},
            {"label": "Ads",             "value": 12.6},
            {"label": "Knowledge panel", "value": 9.8}
          ],
          "brand": "examples/muriel-brand.toml"
        }
    """
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.treemap")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    treemap(
        spec["cells"],
        title=spec.get("title"),
        brand=brand,
        unit=spec.get("unit", ""),
        max_cells=spec.get("max_cells"),
        other_label=spec.get("other_label", "Other"),
        out_path=args.output,
        desc=spec.get("desc"),
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
