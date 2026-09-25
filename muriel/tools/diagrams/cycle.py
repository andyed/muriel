"""
muriel.tools.diagrams.cycle — N-step iterative process as SVG.

When to use
-----------
A process with **no exit condition** that feeds itself: PDCA, OODA,
hypothesis → test → evaluate → revise, agent improvement loops. The
diagram's job is to claim the iteration is real.

Anti-prescription
-----------------
- **Don't use a cycle if there's a real exit.** A funnel, sequence, or
  flowchart is the honest shape — cycles imply you intend to repeat.
- **Don't cycle a list of unrelated steps.** If step N+1 doesn't
  depend on step N's output, you've drawn a clock face, not a process.
- **Don't exceed 8 steps.** Past 8, no reader can hold the loop in
  working memory; decompose into nested cycles or sequential phases.

Hub (``hub=``)
--------------
An optional central node for **state the steps share**: a memory, a
record, a standard, an evidence base — something each pass writes back
to and the next pass reads. Dashed spokes run from the steps to the hub,
so the figure carries two motions at once: work advancing around the
ring, and state accumulating in the middle.

- **Precondition:** there is one durable thing that every step (or the
  named subset) genuinely reads or writes. Name it; if you can't, there
  is no hub.
- **Don't add a hub for a theme or a slogan.** "Customer focus" in the
  middle of a loop is a caption; use ``center=`` for that. A hub claims
  data flows into it.
- **Don't draw a hub as an extra step.** It is state, not an action — a
  step that "happens" in the middle belongs on the ring.
- **Don't spoke every step by reflex.** If only two stages write the
  record, pass ``hub={"steps": [...]}``; a spoke from a step that doesn't
  write is a false claim.
- **One hub.** Two shared stores are two systems; draw two diagrams.

Icons
-----
A step's ``icon`` is a slot name from the curated Lucide set
(``muriel.tools.diagrams.icons.GLYPHS`` — "observe", "measure",
"refresh", "database", …, plus aliases such as "eye" or "iterate") or
raw SVG inner markup on a 24×24 grid. An icon reinforces the label and
never replaces it: the label is what a reader and a screen reader parse.
"""

from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import List, Optional, Sequence, Union

from ._a11y import default_desc, figure_slug, legible_on, svg_open
from ._labels import (
    RATIO_SANS,
    RATIO_SANS_BOLD,
    grow_to_fit,
    label_bbox,
    text_width,
    wrap_measured,
)
from .icons import resolve_icon

__all__ = ["cycle"]


# ─── Brand → tokens ─────────────────────────────────────────────────

def _resolve(brand) -> dict:
    if brand is None:
        return {
            "bg":         "#0a0a0f",
            "ink":        "#e6e4d2",
            "muted":      "#b0b0c4",
            "accent":     "#7dd4e4",
            "node_fill":  "rgba(125, 212, 228, 0.12)",
            "decorative": "rgba(125, 212, 228, 0.45)",
            "body_font":  "ui-sans-serif, -apple-system, system-ui, sans-serif",
        }
    c = brand.colors
    viz = brand.viz.categorical if brand.viz.categorical else []
    accent = viz[0] if viz else (c.foreground or "#7dd4e4")
    return {
        "bg":         c.background,
        "ink":        c.foreground,
        "muted":      c.foreground_muted or c.foreground,
        "accent":     accent,
        "node_fill":  _rgba(accent, 0.12),
        "decorative": _rgba(accent, 0.45),
        "body_font":  brand.typography.body_family or "system-ui, sans-serif",
    }


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ─── Step normalization ─────────────────────────────────────────────

def _normalize_steps(steps) -> list[dict]:
    out = []
    for s in steps:
        if isinstance(s, str):
            out.append({"label": s, "icon": None})
        else:
            # A slot name resolves to curated Lucide markup; raw markup
            # passes through; an unknown name raises here, before any
            # drawing, with close-match suggestions.
            out.append({"label": s.get("label", ""),
                        "icon": resolve_icon(s.get("icon"))})
    if not 3 <= len(out) <= 8:
        raise ValueError(f"cycle supports 3–8 steps; got {len(out)}")
    return out


def _normalize_hub(hub, steps: list[dict]) -> Optional[dict]:
    """``hub`` as ``{"label", "sublabel", "steps": [indices]}`` or None.

    ``hub["steps"]`` selects which steps write back to it, by 0-based
    index or by step label; omitted means every step.
    """
    if hub is None:
        return None
    if isinstance(hub, str):
        hub = {"label": hub}
    if not isinstance(hub, dict):
        raise TypeError(f"hub must be a str or dict; got {type(hub).__name__}")
    label = " ".join(str(hub.get("label", "")).split())
    if not label:
        raise ValueError("hub needs a non-empty 'label' naming the shared state")
    sel = hub.get("steps")
    if sel is None:
        idx = list(range(len(steps)))
    else:
        labels = [s["label"] for s in steps]
        idx = []
        for item in sel:
            if isinstance(item, bool) or not isinstance(item, (int, str)):
                raise TypeError(
                    f"hub steps entries are indices or labels; got {item!r}")
            if isinstance(item, int):
                if not 0 <= item < len(steps):
                    raise ValueError(
                        f"hub step index {item} out of range 0–{len(steps) - 1}")
                idx.append(item)
            elif item in labels:
                idx.append(labels.index(item))
            else:
                raise ValueError(
                    f"hub step {item!r} is not a step label; labels are {labels}")
        idx = sorted(set(idx))
        if not idx:
            raise ValueError("hub steps is empty; omit hub if no step writes to it")
    sub = " ".join(str(hub.get("sublabel") or "").split())
    return {"label": label, "sublabel": sub or None, "steps": idx}


def _hub_desc(hub: Optional[dict], steps: list[dict]) -> str:
    """Description clause for the hub, or "" when there is none."""
    if not hub:
        return ""
    name = hub["label"] + (f" ({hub['sublabel']})" if hub["sublabel"] else "")
    if len(hub["steps"]) == len(steps):
        who = "every step"
    else:
        who = ", ".join(steps[k]["label"] for k in hub["steps"])
    return f"shared hub: {name}, written back by {who}"


def _icon_style(brand) -> tuple[float, float]:
    """(scale from Lucide's 24-unit grid, stroke width in rendered px).

    A brand's ``[iconography] default_size`` sets the rendered size and
    ``stroke_px`` the rendered stroke; without them icons draw at 24 px
    with a 1.5 px stroke.
    """
    size, stroke = 24.0, 1.5
    ic = getattr(brand, "iconography", None) if brand is not None else None
    if ic is not None:
        if ic.default_size:
            size = float(ic.default_size)
        if ic.stroke_px:
            stroke = float(ic.stroke_px)
    return size / 24.0, stroke


def _box_distance(ux: float, uy: float, half_w: float, half_h: float) -> float:
    """Distance from a box's centre to its edge along unit vector (ux, uy)."""
    terms = []
    if abs(ux) > 1e-9:
        terms.append(half_w / abs(ux))
    if abs(uy) > 1e-9:
        terms.append(half_h / abs(uy))
    return min(terms)


# Hub typography and padding, in SVG user units.
_HUB_FS, _HUB_LH = 16, 20        # name: 16 px semibold, 20 px leading
_HUB_SUB_FS, _HUB_SUB_LH = 13, 17
_HUB_PAD_X, _HUB_PAD_Y = 18, 14
_HUB_TEXT_MAX_W = 184.0
_SPOKE_GAP = 6                   # arrow tip stops this far off the hub edge
_SPOKE_MIN = 18                  # shortest spoke that still reads as a line


def _hub_layout(hub: dict) -> dict:
    """Measured hub box: wrapped lines and the box that holds them."""
    name = wrap_measured(hub["label"], _HUB_FS, _HUB_TEXT_MAX_W,
                         char_width_ratio=RATIO_SANS_BOLD) or [hub["label"]]
    sub = (wrap_measured(hub["sublabel"], _HUB_SUB_FS, _HUB_TEXT_MAX_W,
                         char_width_ratio=RATIO_SANS)
           if hub["sublabel"] else [])
    widths = ([text_width(ln, _HUB_FS, char_width_ratio=RATIO_SANS_BOLD) for ln in name]
              + [text_width(ln, _HUB_SUB_FS, char_width_ratio=RATIO_SANS) for ln in sub])
    # Text block height from line boxes: the last line contributes its
    # glyph box (1.02 em), not its full leading.
    text_h = (len(name) - 1) * _HUB_LH + 1.02 * _HUB_FS
    if sub:
        text_h += 6 + (len(sub) - 1) * _HUB_SUB_LH + 1.02 * _HUB_SUB_FS
    w = grow_to_fit(112, max(widths) + 2 * _HUB_PAD_X)
    h = grow_to_fit(56, text_h + 2 * _HUB_PAD_Y)
    return {"name": name, "sub": sub, "w": w, "h": h, "text_h": text_h}


# ─── Geometry helpers ───────────────────────────────────────────────

def _polar(cx: float, cy: float, r: float, angle_deg: float) -> tuple[float, float]:
    a = math.radians(angle_deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


# Target width for a wrapped step label, in SVG user units. The old rule
# wrapped at 14 characters, which is a proxy for width and a poor one:
# "Illuminate" and "WWWWWWWWWW" are the same length and nowhere near the
# same size. This is the width that rule was reaching for.
_LABEL_MAX_W = 126.0


def _wrap_label(text: str, max_width: float = _LABEL_MAX_W) -> list[str]:
    """Greedy wrap on measured width for short cycle labels."""
    lines = wrap_measured(text, 15, max_width, char_width_ratio=RATIO_SANS)
    return lines or [""]


# ─── SVG ────────────────────────────────────────────────────────────

def cycle(
    steps,
    *,
    center: Optional[str] = None,
    title: Optional[str] = None,
    brand=None,
    direction: str = "clockwise",
    out_path: Union[str, Path] = "cycle.svg",
    width: int = 900,
    height: int = 700,
    desc: Optional[str] = None,
    hub=None,
) -> str:
    """Render an N-step iterative cycle (3–8 steps).

    Parameters
    ----------
    steps
        List of step labels. Each entry is either a string or a dict
        ``{"label": str, "icon": <slot name | SVG inner markup | None>}``.
        A slot name ("measure", "refresh", "database", or an alias like
        "eye") draws the curated Lucide glyph; an unknown name raises
        ``ValueError`` with close matches. Raw markup (anything containing
        ``<``) is drawn as given on a 24×24 grid. The icon sits inside the
        step's node, above its number, sized from the brand's
        ``[iconography] default_size`` (24 px without one).
    center
        Optional centre-of-cycle text (e.g. "Evolver's improvement
        cycle"). Multi-line allowed via ``\\n``. Exclusive with ``hub``.
    hub
        Optional shared state the steps write back to — see the module
        docstring for when it is honest. A string (the hub's name) or a
        dict ``{"label": str, "sublabel": str, "steps": [index | label]}``;
        ``steps`` picks which steps get a dashed write-back spoke
        (default: all). The hub is drawn inverted (ink fill, background
        text) so it reads as state, not as another step.
    title
        Optional heading above the cycle.
    direction
        ``"clockwise"`` (default) or ``"counterclockwise"`` — controls
        which way the connecting arrows point.
    brand
        Optional ``muriel.styleguide.StyleGuide``.
    out_path
        Where to write the SVG. Its stem also prefixes the accessible
        ``<title>``/``<desc>`` ids.
    desc
        What the figure argues, for the SVG ``<desc>`` a screen reader
        announces. Defaults to a conservative description built from the
        title and the element labels — it states no claim of its own.

    Returns
    -------
    str
        The path written.
    """
    if direction not in ("clockwise", "counterclockwise"):
        raise ValueError(f"direction must be 'clockwise' or 'counterclockwise'; got {direction!r}")

    norm_steps = _normalize_steps(steps)
    n = len(norm_steps)
    t = _resolve(brand)
    norm_hub = _normalize_hub(hub, norm_steps)
    if norm_hub and center:
        raise ValueError(
            "center= and hub= both occupy the middle of the ring; use hub "
            "for shared state the steps write to, center for a caption")

    title_h = 60 if title else 0
    cx = width / 2
    cy = (height - title_h) / 2 + title_h
    # Outer radius for step nodes; leave generous outside room for labels.
    R = min(width, height - title_h) * 0.32
    node_r = max(34, min(48, R * 0.18))
    label_offset = node_r + 22  # how far the text sits beyond the node edge

    # angle 0 = right; we want first step at the top
    base_angle = -90.0
    sweep = 360.0 if direction == "clockwise" else -360.0
    step_angle = sweep / n

    # ── Hub: measure it, then make the ring big enough to hold it ───
    #
    # The hub box is sized from its measured text. Two things must stay
    # true inside the ring: every spoke keeps a visible length between
    # its node and the hub, and no ring arc passes over the hub's
    # corners. If either fails, the ring grows (the node size stays), and
    # the canvas growth below then makes room for the pushed-out labels.
    hub_box = _hub_layout(norm_hub) if norm_hub else None
    if hub_box:
        A, B = hub_box["w"] / 2, hub_box["h"] / 2
        need = math.hypot(A, B) + node_r + 12   # arcs clear the corners
        for k in norm_hub["steps"]:
            a = math.radians(base_angle + k * step_angle)
            d_hub = _box_distance(math.cos(a), math.sin(a), A, B)
            need = max(need, d_hub + _SPOKE_GAP + _SPOKE_MIN + node_r + 3)
        if R < need:
            R = float(math.ceil(need))

    # ── Grow the canvas until every radial label lands on it ────────
    #
    # Step labels sit outside the ring, anchored so they read outward, so
    # the thing they overflow is the canvas itself — text rendered past
    # the edge, invisible. Rather than pull the labels in (which would
    # crowd the ring) or shrink them, keep the ring exactly as sized and
    # pad the canvas around it. Growth is symmetric so the cycle stays
    # centred; a diagram whose labels already fit gets no padding.
    def _place(i: int, lines: list[str]) -> tuple[float, float]:
        # Lines stack downward from the anchor point. A centred label
        # above the ring must grow *up*, away from its node, or a wrapped
        # second line lands on the node circle. Single-line labels get a
        # zero shift, so existing figures render unchanged.
        a = base_angle + i * step_angle
        lx, ly = _polar(cx, cy, R + label_offset, a)
        cos_a = math.cos(math.radians(a))
        if -0.2 <= cos_a <= 0.2 and math.sin(math.radians(a)) < 0:
            ly -= (len(lines) - 1) * 18
        return lx, ly

    _placements = []
    for i, step in enumerate(norm_steps):
        a = base_angle + i * step_angle
        lines = _wrap_label(step["label"])
        cos_a = math.cos(math.radians(a))
        anchor = "start" if cos_a > 0.2 else ("end" if cos_a < -0.2 else "middle")
        _placements.append((lines,) + _place(i, lines) + (anchor,))

    _spill_x = _spill_y = 0.0
    for lines, lx, ly, anchor in _placements:
        for j, line in enumerate(lines):
            box = label_bbox(line, 15, lx, ly + j * 18 + 5,
                             text_anchor=anchor, char_width_ratio=RATIO_SANS)
            _spill_x = max(_spill_x, -box.x0, box.x1 - width)
            _spill_y = max(_spill_y, title_h - box.y0, box.y1 - height)
    if _spill_x > 0:
        pad = grow_to_fit(0, _spill_x + 16)
        width = int(width + 2 * pad)
        cx += pad
    if _spill_y > 0:
        pad = grow_to_fit(0, _spill_y + 16)
        height = int(height + 2 * pad)
        cy += pad
    if _spill_x > 0 or _spill_y > 0:
        # Positions are derived from the centre, so re-derive them once
        # against the shifted centre rather than trying to patch offsets.
        _placements = [
            (lines,) + _place(i, lines) + (anchor,)
            for i, (lines, _, _, anchor) in enumerate(_placements)
        ]

    parts: list[str] = []
    if desc is None:
        desc = default_desc(
            f"{direction.capitalize()} cycle with {n} steps", title,
            [f"steps in order: " + ", ".join(s["label"] for s in norm_steps),
             (f"centre: " + " ".join(center.split()) if center else ""),
             _hub_desc(norm_hub, norm_steps)])
    slug = figure_slug(out_path, "cycle")
    parts.append(svg_open(
        width=width, height=height,
        slug=slug,
        title=title or "Cycle", desc=desc,
        attrs=f'font-family="{escape(t["body_font"])}"',
    ))
    # Arrow marker(s). The spoke marker only exists when there is a hub,
    # so a hub-less cycle renders byte-identical to before hubs existed.
    spoke_marker = (
        f'<marker id="{slug}-spoke-arrow" markerWidth="8" markerHeight="8" '
        f'refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M0,0 L8,4 L0,8 z" fill="{t["muted"]}"/>'
        f'</marker>'
    ) if norm_hub else ""
    parts.append(
        f'<defs>'
        f'<marker id="{slug}-arrow" markerWidth="10" markerHeight="10" '
        f'refX="9" refY="5" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{t["accent"]}"/>'
        f'</marker>'
        f'{spoke_marker}'
        f'</defs>'
    )
    parts.append(f'<rect width="{width}" height="{height}" fill="{t["bg"]}"/>')

    if title:
        parts.append(
            f'<text x="{cx:.1f}" y="{title_h - 22:.1f}" '
            f'fill="{t["ink"]}" font-size="20" font-weight="600" '
            f'text-anchor="middle">{escape(title)}</text>'
        )

    # Connecting arcs between consecutive nodes
    arc_r = R
    sweep_flag = "1" if direction == "clockwise" else "0"
    for i in range(n):
        a0 = base_angle + i * step_angle
        a1 = base_angle + (i + 1) * step_angle
        # Trim each end by node_r along the arc so the arrow doesn't pierce the node.
        # Approximate by shifting the angle by the chord-equivalent.
        trim_deg = math.degrees(node_r / arc_r) * 1.05
        a0t = a0 + (trim_deg if direction == "clockwise" else -trim_deg)
        a1t = a1 - (trim_deg if direction == "clockwise" else -trim_deg)
        x0, y0 = _polar(cx, cy, arc_r, a0t)
        x1, y1 = _polar(cx, cy, arc_r, a1t)
        parts.append(
            f'<path d="M {x0:.1f} {y0:.1f} A {arc_r:.1f} {arc_r:.1f} 0 0 {sweep_flag} {x1:.1f} {y1:.1f}" '
            f'fill="none" stroke="{t["decorative"]}" stroke-width="1.5" '
            f'marker-end="url(#{slug}-arrow)"/>'
        )

    # Hub: dashed write-back spokes first (beneath everything), then the
    # hub box and its text.
    if norm_hub:
        A, B = hub_box["w"] / 2, hub_box["h"] / 2
        for k in norm_hub["steps"]:
            a = math.radians(base_angle + k * step_angle)
            ux, uy = math.cos(a), math.sin(a)
            nx, ny = _polar(cx, cy, R, base_angle + k * step_angle)
            d_hub = _box_distance(ux, uy, A, B) + _SPOKE_GAP
            sx, sy = nx - (node_r + 3) * ux, ny - (node_r + 3) * uy
            ex, ey = cx + d_hub * ux, cy + d_hub * uy
            parts.append(
                f'<path d="M {sx:.1f} {sy:.1f} L {ex:.1f} {ey:.1f}" '
                f'fill="none" stroke="{t["muted"]}" stroke-width="1.2" '
                f'stroke-dasharray="5 4" stroke-opacity="0.8" '
                f'marker-end="url(#{slug}-spoke-arrow)"/>'
            )
        hx, hy = cx - A, cy - B
        parts.append(
            f'<rect x="{hx:.1f}" y="{hy:.1f}" width="{hub_box["w"]:.1f}" '
            f'height="{hub_box["h"]:.1f}" rx="10" fill="{t["ink"]}"/>'
        )
        # Hub text is background-on-ink: the brand's primary pair,
        # inverted, so it carries the same ratio as body text.
        hub_ink = legible_on([t["bg"], t["muted"]], t["ink"], t["bg"])
        y = cy - hub_box["text_h"] / 2
        for ln in hub_box["name"]:
            parts.append(
                f'<text x="{cx:.1f}" y="{y + 0.8 * _HUB_FS:.1f}" '
                f'fill="{hub_ink}" font-size="{_HUB_FS}" font-weight="600" '
                f'text-anchor="middle">{escape(ln)}</text>'
            )
            y += _HUB_LH
        if hub_box["sub"]:
            # Back off the last name line's unused leading, then the gap.
            y += 6 - (_HUB_LH - 1.02 * _HUB_FS)
            for ln in hub_box["sub"]:
                parts.append(
                    f'<text x="{cx:.1f}" y="{y + 0.8 * _HUB_SUB_FS:.1f}" '
                    f'fill="{hub_ink}" font-size="{_HUB_SUB_FS}" '
                    f'text-anchor="middle">{escape(ln)}</text>'
                )
                y += _HUB_SUB_LH

    # Centre text
    if center:
        lines = center.split("\n")
        line_h = 22
        total_h = line_h * len(lines)
        y0 = cy - total_h / 2 + line_h * 0.75
        for i, line in enumerate(lines):
            parts.append(
                f'<text x="{cx:.1f}" y="{y0 + i * line_h:.1f}" '
                f'fill="{t["ink"]}" font-size="16" font-weight="500" '
                f'text-anchor="middle" opacity="0.85">{escape(line)}</text>'
            )

    # Step nodes + labels
    for i, step in enumerate(norm_steps):
        a = base_angle + i * step_angle
        nx, ny = _polar(cx, cy, R, a)
        # Node circle
        parts.append(
            f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{node_r:.1f}" '
            f'fill="{t["node_fill"]}" stroke="{t["accent"]}" stroke-width="1.5"/>'
        )
        if not step["icon"]:
            # Step number, centred in the node.
            parts.append(
                f'<text x="{nx:.1f}" y="{ny + 5:.1f}" fill="{t["accent"]}" '
                f'font-size="20" font-weight="600" text-anchor="middle">{i + 1}</text>'
            )
        else:
            # Icon above a smaller number, the pair centred as one block.
            # The <g> supplies every presentation attribute (glyphs carry
            # none); stroke-width is divided by the scale so the rendered
            # stroke equals the brand's stroke_px at any icon size.
            scale, stroke_px = _icon_style(brand)
            size = 24.0 * scale
            num_fs, gap = 16, 4
            block_h = size + gap + 0.72 * num_fs   # 0.72 em ≈ digit height
            top = ny - block_h / 2
            parts.append(
                f'<g transform="translate({nx - size / 2:.1f}, {top:.1f}) '
                f'scale({scale:.4g})" fill="none" stroke="{t["accent"]}" '
                f'stroke-width="{stroke_px / scale:.4g}" stroke-linecap="round" '
                f'stroke-linejoin="round" aria-hidden="true">{step["icon"]}</g>'
            )
            parts.append(
                f'<text x="{nx:.1f}" y="{top + block_h:.1f}" fill="{t["accent"]}" '
                f'font-size="{num_fs}" font-weight="600" '
                f'text-anchor="middle">{i + 1}</text>'
            )
        # Label outside the node, in the radial direction — pre-wrapped
        # and pre-anchored above, so the canvas could be sized for it.
        lines, lx, ly, anchor = _placements[i]
        for j, line in enumerate(lines):
            parts.append(
                f'<text x="{lx:.1f}" y="{ly + j * 18 + 5:.1f}" fill="{t["ink"]}" '
                f'font-size="15" font-weight="500" text-anchor="{anchor}">'
                f'{escape(line)}</text>'
            )

    parts.append('</svg>')

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return str(out)


def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.cycle spec.json out.svg``.

    Spec format::

        {
          "title":     "PDCA",
          "center":    "Plan-Do-Check-Act",
          "steps":     ["Plan", "Do", "Check", "Act"],
          "direction": "clockwise",
          "brand":     "examples/muriel-brand.toml"
        }
    """
    import argparse, json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.cycle")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    cycle(
        spec["steps"],
        center=spec.get("center"),
        title=spec.get("title"),
        brand=brand,
        direction=spec.get("direction", "clockwise"),
        out_path=args.output,
        desc=spec.get("desc"),
        hub=spec.get("hub"),
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
