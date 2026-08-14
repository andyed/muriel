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
        value — an honest funnel. Otherwise tiers taper linearly
        (an ordinal narrowing, not a measurement).
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
        Where to write the SVG.

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
    pad_top  = 48
    pad_bot  = 48
    title_h  = 72 if title else 0
    cx       = width / 2

    use_prop = proportional and all(l["value"] is not None for l in norm)

    def _tier_width(i: int) -> float:
        """Representative width of tier i (used in proportional mode)."""
        vals = [l["value"] for l in norm]
        vmax = max(vals) or 1.0
        return min_w + (max_w - min_w) * (norm[i]["value"] / vmax)

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
    for i, l in enumerate(norm):
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
    width = int(grow_to_fit(width, max_w + 2 * side))
    cx = width / 2

    y0       = title_h + pad_top
    stack_h  = n * tier_h
    height   = y0 + stack_h + pad_bot

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="{escape(t["body_font"])}">'
    )
    parts.append(
        f'<defs><marker id="py-arrow" markerWidth="8" markerHeight="8" '
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
        pts = (
            f"{cx - top_w / 2:.1f},{ty:.1f} {cx + top_w / 2:.1f},{ty:.1f} "
            f"{cx + bot_w / 2:.1f},{by:.1f} {cx - bot_w / 2:.1f},{by:.1f}"
        )
        is_focal = (i == focal_idx)
        fill = t["focal_fill"] if is_focal else t["paper"]
        stroke = t["accent"] if is_focal else t["hairline"]
        sw = 1.5 if is_focal else 1
        parts.append(
            f'<polygon points="{pts}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>'
        )
        # Primary label (centred)
        has_sub = bool(l["sublabel"])
        ly = mid + (0 if not has_sub else -4)
        parts.append(
            f'<text x="{cx:.1f}" y="{ly + 4:.1f}" fill="{t["ink"]}" '
            f'font-size="13" font-weight="600" text-anchor="middle">'
            f'{escape(l["label"])}</text>'
        )
        if has_sub:
            parts.append(
                f'<text x="{cx:.1f}" y="{mid + 16:.1f}" fill="{t["muted"]}" '
                f'font-family="{_MONO}" font-size="10" text-anchor="middle">'
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
                f'stroke="{t["muted"]}" stroke-width="1" marker-end="url(#py-arrow)"/>'
            )
        else:
            parts.append(
                f'<line x1="{ax}" y1="{a_top:.1f}" x2="{ax}" y2="{a_bot:.1f}" '
                f'stroke="{t["muted"]}" stroke-width="1" marker-end="url(#py-arrow)"/>'
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
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
