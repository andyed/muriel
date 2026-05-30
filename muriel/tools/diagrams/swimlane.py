"""
muriel.tools.diagrams.swimlane — cross-functional process as SVG.

When to use
-----------
A process whose **point is the handoffs**: which actor owns each step and
where work crosses between them. RACI-style flows, vendor handoffs,
multi-team shipping pipelines, request → review → approve chains. The
lane assignment is the argument — if ownership didn't matter, you'd draw
a plain sequence.

Not the exclusive provider
--------------------------
This is the static, brand-locked, print-ready option. For a single-actor
step-by-step flow (no lanes), the infographics "Process" template
(``channels/infographics.md``) is lighter. For an interactive or
runtime-rendered flow, Mermaid (``flowchart`` with ``subgraph`` lanes,
via ``mmdc`` — see ``channels/svg.md``) is faster to author. Reach for
this generator when the deliverable is a paper figure or editorial SVG
that must match brand tokens and clear the 8:1 contrast floor.

Anti-prescription
-----------------
- **Don't draw lanes you can't label.** An unlabeled lane is a row with
  no actor — collapse it.
- **Don't let a step span two lanes.** Every step has one owner; shared
  ownership is a process smell, not a diagram feature.
- **Don't snake the flow.** If arrows backtrack to read in order,
  re-sequence the steps so progression runs forward.

Geometry follows the editorial-diagram discipline: 4px-increment
alignment, 1px hairline lane dividers, no shadows. Layout reference
adapted from the MIT-licensed diagram-design skill (© 2025 Cathryn
Lavery); the tokens, contrast rule, and epistemic gate are muriel's own.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Optional, Union

__all__ = ["swimlane"]

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
            "flow":       "rgba(176, 176, 196, 0.55)",
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
        "paper":      _rgba(ink, 0.04),
        "focal_fill": _rgba(accent, 0.12),
        "hairline":   _rgba(ink, 0.14),
        "flow":       _rgba(muted, 0.55),
        "body_font":  brand.typography.body_family or "system-ui, sans-serif",
    }


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ─── Normalization ──────────────────────────────────────────────────

def _lane_index(lane, lane_labels: list[str]) -> int:
    if isinstance(lane, int):
        if not 0 <= lane < len(lane_labels):
            raise ValueError(f"lane index {lane} out of range")
        return lane
    try:
        return lane_labels.index(lane)
    except ValueError:
        raise ValueError(f"step references unknown lane {lane!r}; "
                         f"lanes are {lane_labels}")


def _normalize(lanes, steps):
    lane_labels = [l if isinstance(l, str) else l.get("label", "") for l in lanes]
    if not 2 <= len(lane_labels) <= 6:
        raise ValueError(f"swimlane supports 2–6 lanes; got {len(lane_labels)}")
    norm = []
    next_col = 0
    for s in steps:
        if isinstance(s, str):
            raise ValueError("each step needs a lane; pass a dict "
                             "{'label':..., 'lane':...}")
        li = _lane_index(s["lane"], lane_labels)
        col = s.get("col")
        if col is None:
            col = next_col
            next_col += 1
        else:
            next_col = max(next_col, col + 1)
        norm.append({
            "label": s.get("label", ""),
            "lane":  li,
            "col":   col,
            "focal": bool(s.get("focal", False)),
        })
    if not norm:
        raise ValueError("swimlane needs at least one step")
    return lane_labels, norm


# ─── SVG ────────────────────────────────────────────────────────────

def swimlane(
    lanes,
    steps,
    *,
    title: Optional[str] = None,
    brand=None,
    out_path: Union[str, Path] = "swimlane.svg",
) -> str:
    """Render a cross-functional swimlane (2–6 lanes).

    Parameters
    ----------
    lanes
        2–6 actor/team labels, top to bottom. Each is a string or a
        dict ``{"label": str}``.
    steps
        Process steps **in flow order**. Each is a dict
        ``{"label": str, "lane": str|int, "col": int, "focal": bool}``.
        ``lane`` names the owning lane (label or row index). ``col`` is
        an optional explicit column; omit it to auto-place each step in
        the next column (strict left-to-right flow). Consecutive steps
        are joined by a flow arrow; a step that changes lane draws an
        emphasised **handoff** arrow (accent).
    title
        Optional heading.
    brand
        Optional ``muriel.styleguide.StyleGuide``.
    out_path
        Where to write the SVG.

    Returns
    -------
    str
        The path written.
    """
    lane_labels, norm = _normalize(lanes, steps)
    n_lanes = len(lane_labels)
    n_cols = max(s["col"] for s in norm) + 1
    t = _resolve(brand)

    # ── Geometry (4px grid) ─────────────────────────────────────────
    lane_h     = 96
    lane_label = 168           # left margin for lane eyebrow
    col_w      = 184
    box_w      = 144
    box_h      = 56
    pad_top    = 48
    pad_bot    = 48
    pad_right  = 48
    title_h    = 72 if title else 0
    y0         = title_h + pad_top
    grid_h     = n_lanes * lane_h
    width      = lane_label + n_cols * col_w + pad_right
    height     = y0 + grid_h + pad_bot

    def cell_cx(col: int) -> float:
        return lane_label + col * col_w + col_w / 2

    def lane_cy(li: int) -> float:
        return y0 + li * lane_h + lane_h / 2

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="{escape(t["body_font"])}">'
    )
    parts.append(
        f'<defs>'
        f'<marker id="sl-flow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" '
        f'orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L9,4.5 L0,9 z" fill="{t["flow"]}"/></marker>'
        f'<marker id="sl-handoff" markerWidth="9" markerHeight="9" refX="8" refY="4.5" '
        f'orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L9,4.5 L0,9 z" fill="{t["accent"]}"/></marker>'
        f'</defs>'
    )
    parts.append(f'<rect width="{width}" height="{height}" fill="{t["bg"]}"/>')

    if title:
        parts.append(
            f'<text x="{lane_label}" y="{title_h - 24:.1f}" fill="{t["ink"]}" '
            f'font-size="20" font-weight="600" text-anchor="start">'
            f'{escape(title)}</text>'
        )

    # ── Lane bands + labels + dividers ──────────────────────────────
    for li, label in enumerate(lane_labels):
        ly = y0 + li * lane_h
        cy = lane_cy(li)
        # subtle alternating wash to separate lanes without boxing them
        if li % 2 == 1:
            parts.append(
                f'<rect x="{lane_label}" y="{ly:.1f}" width="{n_cols * col_w}" '
                f'height="{lane_h}" fill="{t["paper"]}"/>'
            )
        # hairline divider above each lane after the first
        if li > 0:
            parts.append(
                f'<line x1="{lane_label}" y1="{ly:.1f}" x2="{width - pad_right}" '
                f'y2="{ly:.1f}" stroke="{t["hairline"]}" stroke-width="1"/>'
            )
        # lane label (mono eyebrow, left margin)
        parts.append(
            f'<text x="{lane_label - 20}" y="{cy + 4:.1f}" fill="{t["muted"]}" '
            f'font-family="{_MONO}" font-size="11" letter-spacing="1.5" '
            f'text-anchor="end">{escape(label.upper())}</text>'
        )

    # ── Flow arrows (drawn under boxes) ─────────────────────────────
    for a, b in zip(norm, norm[1:]):
        ax = cell_cx(a["col"]) + box_w / 2
        ay = lane_cy(a["lane"])
        bx = cell_cx(b["col"]) - box_w / 2
        by = lane_cy(b["lane"])
        handoff = a["lane"] != b["lane"]
        stroke = t["accent"] if handoff else t["flow"]
        sw = 1.5 if handoff else 1
        marker = "sl-handoff" if handoff else "sl-flow"
        if not handoff:
            d = f'M {ax:.1f} {ay:.1f} L {bx:.1f} {by:.1f}'
        else:
            midx = (ax + bx) / 2
            d = (f'M {ax:.1f} {ay:.1f} L {midx:.1f} {ay:.1f} '
                 f'L {midx:.1f} {by:.1f} L {bx:.1f} {by:.1f}')
        parts.append(
            f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}" '
            f'marker-end="url(#{marker})"/>'
        )

    # ── Step boxes ──────────────────────────────────────────────────
    for s in norm:
        cx = cell_cx(s["col"])
        cy = lane_cy(s["lane"])
        bx = cx - box_w / 2
        by = cy - box_h / 2
        fill = t["focal_fill"] if s["focal"] else t["paper"]
        stroke = t["accent"] if s["focal"] else t["hairline"]
        sw = 1.5 if s["focal"] else 1
        parts.append(
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="{box_w}" height="{box_h}" '
            f'rx="4" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )
        # label (wrap to two lines if long)
        words = s["label"].split()
        line1, line2 = s["label"], ""
        if len(s["label"]) > 16 and len(words) > 1:
            mid = len(words) // 2
            line1, line2 = " ".join(words[:mid]), " ".join(words[mid:])
        if line2:
            parts.append(
                f'<text x="{cx:.1f}" y="{cy - 2:.1f}" fill="{t["ink"]}" '
                f'font-size="13" font-weight="600" text-anchor="middle">'
                f'{escape(line1)}</text>'
            )
            parts.append(
                f'<text x="{cx:.1f}" y="{cy + 14:.1f}" fill="{t["ink"]}" '
                f'font-size="13" font-weight="600" text-anchor="middle">'
                f'{escape(line2)}</text>'
            )
        else:
            parts.append(
                f'<text x="{cx:.1f}" y="{cy + 5:.1f}" fill="{t["ink"]}" '
                f'font-size="13" font-weight="600" text-anchor="middle">'
                f'{escape(line1)}</text>'
            )

    parts.append('</svg>')

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return str(out)


def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.swimlane spec.json out.svg``.

    Spec format::

        {
          "title": "Release pipeline",
          "lanes": ["PM", "Engineering", "QA", "Release"],
          "steps": [
            {"label": "Write spec",   "lane": "PM"},
            {"label": "Implement",    "lane": "Engineering"},
            {"label": "Review PR",    "lane": "Engineering"},
            {"label": "Test build",   "lane": "QA", "focal": true},
            {"label": "Sign off",     "lane": "PM"},
            {"label": "Ship",         "lane": "Release"}
          ],
          "brand": "examples/muriel-brand.toml"
        }
    """
    import argparse, json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.swimlane")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    swimlane(
        spec["lanes"],
        spec["steps"],
        title=spec.get("title"),
        brand=brand,
        out_path=args.output,
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
