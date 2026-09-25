"""
muriel.tools.diagrams.pyramid — pyramid / funnel as SVG.

When to use
-----------
A set of tiers where **each level rests on the one below**, and the
*width* of a tier is the encoding:

- **Pyramid** (apex up): the narrow top is the rarest / most valuable /
  hardest-won; the broad base is foundational. Maslow, a skills
  hierarchy, "few experts rest on many practitioners."
- **Funnel** (apex down): the wide top is the audience and the narrow
  bottom is what survived — conversion, qualification, retention.

The claim a tier's width makes is quantitative. If you have the counts,
render them honestly (``proportional=True``); if the shape is purely
ordinal, the linear taper says "narrowing" without faking a measurement.

Anti-prescription
-----------------
- **Don't use a pyramid for non-hierarchical data.** If tiers don't
  rest on each other, width encodes nothing — you've drawn a decorative
  triangle. Use a bar chart or a list.
- **Don't fake funnel widths.** If widths aren't proportional to the
  counts, a reader reads a drop-off that isn't there. Either pass real
  values or say (in the caption) that the taper is ordinal.
- **Don't exceed 6 tiers.** 7+ tiers are illegible at any reasonable
  size.
- **Don't highlight the base.** Coral on the broad base dilutes the
  "apex = rare" signal; highlight the apex (pyramid) or the conversion
  tier (funnel), or nothing.

Geometry follows the editorial-diagram discipline: 4px-increment
alignment, 1px hairline dividers, no shadows. Layout reference adapted
from the MIT-licensed diagram-design skill (© 2025 Cathryn Lavery); the
tokens, contrast rule, and epistemic gate are muriel's own.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Optional, Union

from ._a11y import default_desc, figure_slug, legible_on, svg_open
from ._labels import RATIO_MONO, RATIO_SANS_BOLD, grow_to_fit, text_width

__all__ = ["pyramid"]

_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


# ─── Brand → tokens ─────────────────────────────────────────────────

def _resolve(brand) -> dict:
    if brand is None:
        return {
            "bg":         "#0a0a0f",
            "ink":        "#e6e4d2",
            "muted":      "#b0b0c4",
            "accent":     "#7dd4e4",
            "paper":      "rgba(230, 228, 210, 0.04)",
            "focal_fill": "rgba(125, 212, 228, 0.12)",
            "hairline":   "rgba(230, 228, 210, 0.14)",
            "body_font":  "ui-sans-serif, -apple-system, system-ui, sans-serif",
        }
    c = brand.colors
    viz = brand.viz.categorical if brand.viz.categorical else []
    accent = viz[0] if viz else (c.foreground or "#7dd4e4")
    ink = c.foreground
    return {
        "bg":         c.background,
        "ink":        ink,
        "muted":      c.foreground_muted or ink,
        "accent":     accent,
        "paper":      _rgba(ink, 0.04),
        "focal_fill": _rgba(accent, 0.12),
        "hairline":   _rgba(ink, 0.14),
        "body_font":  brand.typography.body_family or "system-ui, sans-serif",
    }


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ─── Tier normalization ─────────────────────────────────────────────

def _data_num(v) -> str:
    """A number as a ``data-*`` attribute value: integral floats lose ``.0``."""
    f = float(v)
    return str(int(f)) if float(f).is_integer() and abs(f) < 1e15 else repr(f)


def _normalize(tiers) -> list[dict]:
    out = []
    for t in tiers:
        if isinstance(t, str):
            out.append({"label": t, "sublabel": None, "annotation": None,
                        "value": None, "focal": False})
        else:
            out.append({
                "label":      t.get("label", ""),
                "sublabel":   t.get("sublabel") or t.get("note"),
                "annotation": t.get("annotation"),
                "value":      t.get("value"),
                "focal":      bool(t.get("focal", False)),
            })
    if not 4 <= len(out) <= 6:
        raise ValueError(f"pyramid supports 4–6 tiers; got {len(out)}")
    return out


# ─── SVG ────────────────────────────────────────────────────────────

def pyramid(
    tiers,
    *,
    orientation: str = "up",
    proportional: bool = False,
    title: Optional[str] = None,
    brand=None,
    focal: Optional[int] = None,
    axis_label: Optional[str] = None,
    out_path: Union[str, Path] = "pyramid.svg",
    width: int = 900,
    desc: Optional[str] = None,
) -> str:
    """Render a 4–6 tier pyramid or funnel.

    Parameters
    ----------
    tiers
        4–6 entries in **reading order, top to bottom** (index 0 is the
        top tier). Each entry is a string or a dict
        ``{"label": str, "sublabel": str, "annotation": str,
        "value": float, "focal": bool}``. ``annotation`` sits to the
        right (e.g. a funnel drop-off ``"−40%"``); ``value`` drives the
        tier width when ``proportional=True``.
    orientation
        ``"up"`` → pyramid (apex at top, narrow = rare/valuable).
        ``"down"`` → funnel (apex at bottom, narrow = converted).
    proportional
        When ``True`` and every tier carries a ``value``, each tier is
        drawn as a centred rectangle whose width is proportional to its
        value (``width = max_w * value / max(values)``) — an honest
        funnel. A tier too narrow to hold its label keeps its true width
        and the label moves outside the bar, to its left; the bar is
        never widened to fit text, because that would misstate the
        count. Otherwise tiers taper linearly (an ordinal narrowing, not
        a measurement).
    title
        Optional heading above the figure.
    focal
        Index of the single tier to highlight. Defaults to the apex
        (tier 0 for a pyramid, last tier for a funnel). Pass ``-1`` to
        highlight nothing.
    axis_label
        Optional left-margin axis word, e.g. ``"rarer"`` (pyramid) or
        ``"drop-off"`` (funnel).
    brand
        Optional ``muriel.styleguide.StyleGuide``.
    out_path
        Where to write the SVG. Its stem also prefixes the accessible
        ``<title>``/``<desc>`` ids.
    desc
        What the figure argues, for the SVG ``<desc>`` a screen reader
        announces. Defaults to a conservative description listing the
        tiers and values from the spec — it states no claim of its own.

    Returns
    -------
    str
        The path written.
    """
    if orientation not in ("up", "down"):
        raise ValueError(f"orientation must be 'up' or 'down'; got {orientation!r}")

    norm = _normalize(tiers)
    n = len(norm)
    t = _resolve(brand)

    # Default focal: apex of the shape (top for pyramid, bottom for funnel).
    if focal is None:
        focal_idx = 0 if orientation == "up" else n - 1
    elif focal < 0:
        focal_idx = None
    else:
        if not 0 <= focal < n:
            raise ValueError(f"focal index {focal} out of range for {n} tiers")
        focal_idx = focal

    # ── Geometry (4px grid) ─────────────────────────────────────────
    tier_h   = 64
    min_w    = 160          # apex flat-top width (keeps labels legible)
    max_w    = 640
    tier_pad = 16           # clear space inside a tier's sloped edges
    ann_gap  = 20           # tier edge to right-hand annotation
    out_gap  = 12           # bar edge to an outside label (proportional mode)
    pad_top  = 48
    pad_bot  = 48
    title_h  = 72 if title else 0
    cx       = width / 2

    use_prop = proportional and all(l["value"] is not None for l in norm)

    def _tier_width(i: int) -> float:
        """Width of tier i in proportional mode: width ∝ value.

        No floor. An earlier version drew ``min_w + (max_w - min_w) * v/vmax``,
        which put a 160px floor under every bar: a funnel of 100000 / 24000 /
        9000 / 2100 drew at 1 / .43 / .32 / .27 when the data say
        1 / .24 / .09 / .02 — a "proportional" funnel that understated the
        drop-off fourfold at the bottom. A label that does not fit a narrow
        bar is placed outside it instead (see below).
        """
        vals = [max(0.0, float(l["value"])) for l in norm]
        vmax = max(vals) or 1.0
        return max_w * (vals[i] / vmax)

    def _boundary_width(j: int) -> float:
        """Width at horizontal boundary j (0..n) for the tapered shape."""
        frac = j / n
        if orientation == "up":      # narrow at top, wide at base
            return min_w + (max_w - min_w) * frac
        return max_w - (max_w - min_w) * frac  # wide at top, narrow at base

    def _span(i: int, top_off: float, bot_off: float) -> float:
        """Narrowest width of tier ``i`` between two offsets into its height.

        A tapered tier is a trapezoid, so "how much room is there" has no
        single answer — it depends where in the tier you ask. Asking at
        the flat edge would over-report the squeeze on one side and
        under-report it on the other, growing figures that render fine.
        Ask across the band the text actually occupies.
        """
        if use_prop:
            return _tier_width(i)  # proportional mode draws rectangles
        top_w = _boundary_width(i)
        bot_w = _boundary_width(i + 1)
        at = lambda off: top_w + (bot_w - top_w) * (off / tier_h)  # noqa: E731
        return min(at(top_off), at(bot_off))

    # ── Fit the labels, then scale the taper up to hold them ────────
    #
    # Widening one tier to fit its label would flatten the taper, and the
    # taper *is* the argument — ordinal narrowing, or a proportional
    # funnel. So when a label doesn't fit, scale min_w and max_w by the
    # same factor: the shape is preserved exactly and the figure just
    # gets bigger. A pyramid whose labels already fit is untouched.
    #
    # The offsets below mirror the baselines the renderer uses further
    # down; ascent/descent come from muriel.layout's text metrics.
    scale = 1.0
    # Proportional mode never scales: its widths are the data. Labels that
    # do not fit move outside their bar instead.
    for i, l in enumerate(norm if not use_prop else []):
        checks = []
        if l["sublabel"]:
            # label baseline at mid, sublabel baseline at mid + 16
            checks.append((text_width(l["label"], 13,
                                      char_width_ratio=RATIO_SANS_BOLD),
                           32 - 10.4, 32 + 2.9))
            checks.append((text_width(l["sublabel"], 10,
                                      char_width_ratio=RATIO_MONO),
                           48 - 8.0, 48 + 2.2))
        else:
            # label baseline at mid + 4
            checks.append((text_width(l["label"], 13,
                                      char_width_ratio=RATIO_SANS_BOLD),
                           36 - 10.4, 36 + 2.9))
        for needed, top_off, bot_off in checks:
            avail = _span(i, top_off, bot_off)
            if avail > 0 and needed > avail - 2 * tier_pad:
                scale = max(scale, (needed + 2 * tier_pad) / avail)
    if scale > 1.0:
        min_w = grow_to_fit(min_w, min_w * scale)
        max_w = grow_to_fit(max_w, max_w * scale)

    # The widest tier has to land on the canvas with room for whatever
    # sits beside it. Growth is symmetric because the stack is centred,
    # so the margin is the worst of the three things that claim the side
    # channel: bare canvas, the left-margin axis, and right-hand
    # annotations.
    widest_ann = max(
        (text_width(l["annotation"], 11, char_width_ratio=RATIO_MONO)
         for l in norm if l["annotation"]),
        default=0.0,
    )
    side = 24.0
    if axis_label:
        side = max(side, 80.0)   # axis line at x=60 plus its rotated caption
    if widest_ann:
        side = max(side, ann_gap + widest_ann + 24)
    # Proportional mode: which tiers are too narrow for their own label?
    # Those labels sit outside the bar, right-anchored just left of it, so
    # the bar keeps its true width. The half-canvas has to hold that label
    # plus the left margin (bare edge, or the axis and its caption).
    outside: set[int] = set()
    half_needed = max_w / 2 + side
    if use_prop:
        left_margin = 80.0 if axis_label else 24.0
        for i, l in enumerate(norm):
            need = text_width(l["label"], 13, char_width_ratio=RATIO_SANS_BOLD)
            if l["sublabel"]:
                need = max(need, text_width(l["sublabel"], 10,
                                            char_width_ratio=RATIO_MONO))
            w_i = _tier_width(i)
            if need > w_i - 2 * tier_pad:
                outside.add(i)
                half_needed = max(half_needed,
                                  w_i / 2 + out_gap + need + left_margin)
    width = int(grow_to_fit(width, 2 * half_needed))
    cx = width / 2

    y0       = title_h + pad_top
    stack_h  = n * tier_h
    height   = y0 + stack_h + pad_bot

    kind = "Funnel" if orientation == "down" else "Pyramid"
    if desc is None:
        def _fmt_v(v) -> str:
            v = float(v)
            return f"{int(v):,}" if float(v).is_integer() else f"{v:,g}"

        tier_txt = []
        for l in norm:
            extra = [x for x in (
                l["sublabel"],
                _fmt_v(l["value"]) if l["value"] is not None else None,
                l["annotation"],
            ) if x]
            tier_txt.append(
                f'{l["label"]} ({"; ".join(extra)})' if extra else l["label"]
            )
        desc = default_desc(
            f"{kind} with {n} tiers",
            title,
            [
                "top to bottom: " + ", ".join(tier_txt),
                ("bar widths proportional to value" if use_prop
                 else "tiers taper linearly; width is ordinal, not measured"),
                (f"axis: {axis_label}" if axis_label else ""),
            ],
        )
    parts: list[str] = []
    slug = figure_slug(out_path, kind.lower())
    parts.append(svg_open(
        width=width, height=height,
        slug=slug,
        title=title or kind, desc=desc,
        attrs=f'font-family="{escape(t["body_font"])}"',
    ))
    parts.append(
        f'<defs><marker id="{slug}-arrow" markerWidth="8" markerHeight="8" '
        f'refX="4" refY="7" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,7 L4,0 L8,7" fill="none" stroke="{t["muted"]}" stroke-width="1"/>'
        f'</marker></defs>'
    )
    parts.append(f'<rect width="{width}" height="{height}" fill="{t["bg"]}"/>')

    if title:
        parts.append(
            f'<text x="{cx:.1f}" y="{title_h - 24:.1f}" fill="{t["ink"]}" '
            f'font-size="20" font-weight="600" text-anchor="middle">'
            f'{escape(title)}</text>'
        )

    # ── Tiers ───────────────────────────────────────────────────────
    for i, l in enumerate(norm):
        ty = y0 + i * tier_h
        by = ty + tier_h
        mid = ty + tier_h / 2
        if use_prop:
            top_w = bot_w = _tier_width(i)
        else:
            top_w = _boundary_width(i)
            bot_w = _boundary_width(i + 1)
        # Proportional bars carry data in their width, and a 0.1px rounding
        # step is a large share of a sliver; write x to 0.001px there.
        xp = 3 if use_prop else 1
        pts = (
            f"{cx - top_w / 2:.{xp}f},{ty:.1f} {cx + top_w / 2:.{xp}f},{ty:.1f} "
            f"{cx + bot_w / 2:.{xp}f},{by:.1f} {cx - bot_w / 2:.{xp}f},{by:.1f}"
        )
        is_focal = (i == focal_idx)
        fill = t["focal_fill"] if is_focal else t["paper"]
        stroke = t["accent"] if is_focal else t["hairline"]
        sw = 1.5 if is_focal else 1
        # data-* carries the spec back out, so a test (or a reader of the
        # file) can recompute the encoding from the drawing alone.
        data = f' data-index="{i}"'
        if l["value"] is not None:
            data += f' data-value="{_data_num(l["value"])}"'
        parts.append(
            f'<polygon points="{pts}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"{data}/>'
        )
        # Primary label: centred in the tier, or — for a proportional bar
        # too narrow to hold it — right-anchored just outside its left edge.
        has_sub = bool(l["sublabel"])
        ly = mid + (0 if not has_sub else -4)
        if i in outside:
            lx = cx - top_w / 2 - out_gap
            anchor = "end"
        else:
            lx = cx
            anchor = "middle"
        parts.append(
            f'<text x="{lx:.1f}" y="{ly + 4:.1f}" fill="{t["ink"]}" '
            f'font-size="13" font-weight="600" text-anchor="{anchor}">'
            f'{escape(l["label"])}</text>'
        )
        if has_sub:
            # Muted on a tinted (focal) tier can fall under 8:1; step up.
            sub_fill = legible_on([t["muted"], t["ink"]],
                                  t["bg"] if i in outside else fill, t["bg"])
            parts.append(
                f'<text x="{lx:.1f}" y="{mid + 16:.1f}" fill="{sub_fill}" '
                f'font-family="{_MONO}" font-size="10" text-anchor="{anchor}">'
                f'{escape(l["sublabel"])}</text>'
            )
        # Right-side annotation (e.g. funnel drop-off)
        if l["annotation"]:
            edge = max(top_w, bot_w) / 2
            parts.append(
                f'<text x="{cx + edge + ann_gap:.1f}" y="{mid + 4:.1f}" '
                f'fill="{t["muted"]}" font-family="{_MONO}" font-size="11" '
                f'text-anchor="start">{escape(l["annotation"])}</text>'
            )

    # ── Left-margin axis arrow ──────────────────────────────────────
    if axis_label:
        ax = 60
        a_top = y0 + 8
        a_bot = y0 + stack_h - 8
        # Pyramid: "rarer" points up. Funnel: "drop-off" points down.
        if orientation == "up":
            parts.append(
                f'<line x1="{ax}" y1="{a_bot:.1f}" x2="{ax}" y2="{a_top:.1f}" '
                f'stroke="{t["muted"]}" stroke-width="1" marker-end="url(#{slug}-arrow)"/>'
            )
        else:
            parts.append(
                f'<line x1="{ax}" y1="{a_top:.1f}" x2="{ax}" y2="{a_bot:.1f}" '
                f'stroke="{t["muted"]}" stroke-width="1" marker-end="url(#{slug}-arrow)"/>'
            )
        # Direction is carried by the line's arrowhead marker; the text
        # stays ASCII so it survives any rasterizer's font fallback.
        ty = (a_top + a_bot) / 2
        parts.append(
            f'<text x="{ax - 16}" y="{ty:.1f}" fill="{t["muted"]}" '
            f'font-family="{_MONO}" font-size="10" letter-spacing="1.5" '
            f'text-anchor="middle" transform="rotate(-90 {ax - 16} {ty:.1f})">'
            f'{escape(axis_label.upper())}</text>'
        )

    parts.append('</svg>')

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return str(out)


def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.pyramid spec.json out.svg``.

    Spec format::

        {
          "title":        "Acquisition funnel — Q2",
          "orientation":  "down",
          "proportional": true,
          "axis_label":   "drop-off",
          "tiers": [
            {"label": "Visitors",  "value": 100000, "sublabel": "all sessions"},
            {"label": "Signups",   "value": 24000,  "annotation": "−76%"},
            {"label": "Activated", "value": 9000,   "annotation": "−62%"},
            {"label": "Paid",      "value": 2100,   "annotation": "−77%"}
          ],
          "brand": "examples/muriel-brand.toml"
        }
    """
    import argparse, json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.pyramid")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    pyramid(
        spec["tiers"],
        orientation=spec.get("orientation", "up"),
        proportional=spec.get("proportional", False),
        title=spec.get("title"),
        brand=brand,
        focal=spec.get("focal"),
        axis_label=spec.get("axis_label"),
        out_path=args.output,
        desc=spec.get("desc"),
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
