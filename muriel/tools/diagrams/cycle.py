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
"""

from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import List, Optional, Sequence, Union

from ._labels import RATIO_SANS, grow_to_fit, label_bbox, wrap_measured

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
            out.append({"label": s.get("label", ""), "icon": s.get("icon")})
    if not 3 <= len(out) <= 8:
        raise ValueError(f"cycle supports 3–8 steps; got {len(out)}")
    return out


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
) -> str:
    """Render an N-step iterative cycle (3–8 steps).

    Parameters
    ----------
    steps
        List of step labels. Each entry is either a string or a dict
        ``{"label": str, "icon": <SVG inner markup or None>}``. Icons,
        when supplied, are rendered inside a small accent ring above
        each step's label.
    center
        Optional centre-of-cycle text (e.g. "Evolver's improvement
        cycle"). Multi-line allowed via ``\\n``.
    title
        Optional heading above the cycle.
    direction
        ``"clockwise"`` (default) or ``"counterclockwise"`` — controls
        which way the connecting arrows point.
    brand
        Optional ``muriel.styleguide.StyleGuide``.
    out_path
        Where to write the SVG.

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

    # ── Grow the canvas until every radial label lands on it ────────
    #
    # Step labels sit outside the ring, anchored so they read outward, so
    # the thing they overflow is the canvas itself — text rendered past
    # the edge, invisible. Rather than pull the labels in (which would
    # crowd the ring) or shrink them, keep the ring exactly as sized and
    # pad the canvas around it. Growth is symmetric so the cycle stays
    # centred; a diagram whose labels already fit gets no padding.
    _placements = []
    for i, step in enumerate(norm_steps):
        a = base_angle + i * step_angle
        lx, ly = _polar(cx, cy, R + label_offset, a)
        cos_a = math.cos(math.radians(a))
        anchor = "start" if cos_a > 0.2 else ("end" if cos_a < -0.2 else "middle")
        _placements.append((_wrap_label(step["label"]), lx, ly, anchor))

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
            (lines,) + _polar(cx, cy, R + label_offset,
                              base_angle + i * step_angle) + (anchor,)
            for i, (lines, _, _, anchor) in enumerate(_placements)
        ]

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="{escape(t["body_font"])}">'
    )
    # Arrow marker
    parts.append(
        f'<defs>'
        f'<marker id="cycle-arrow" markerWidth="10" markerHeight="10" '
        f'refX="9" refY="5" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{t["accent"]}"/>'
        f'</marker>'
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
            f'marker-end="url(#cycle-arrow)"/>'
        )

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
        # Step number inside
        parts.append(
            f'<text x="{nx:.1f}" y="{ny + 5:.1f}" fill="{t["accent"]}" '
            f'font-size="20" font-weight="600" text-anchor="middle">{i + 1}</text>'
        )
        # Optional icon — caller supplies inner SVG markup; we wrap in <g>
        if step["icon"]:
            parts.append(
                f'<g transform="translate({nx - 12:.1f}, {ny - 26:.1f}) scale(1)" '
                f'fill="none" stroke="{t["accent"]}" stroke-width="1.5">{step["icon"]}</g>'
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
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
