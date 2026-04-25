"""
muriel.tools.diagrams.matrix — 2×2 categorical decomposition as SVG.

When to use
-----------
Two **independent** binary axes that together divide a population into
four meaningful classes. The classics: BCG growth/share, Eisenhower
urgent/important, payoff likelihood/impact, sat/opt by LF/HF.

Anti-prescription
-----------------
- **Don't use a 2×2 if your axes are correlated.** Half the cells will
  be empty or near-empty; you've drawn a line, not a matrix. Plot the
  scatter instead and let the correlation show.
- **Don't use a 2×2 to disguise a list.** Four bullet points pretending
  to occupy quadrants is worse than four bullet points.
- **Don't label cells with marketing words** ("Stars / Cash Cows /
  Dogs / Question Marks") if your audience won't recognize them. Use
  the actual short claim each cell carries.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Optional, Sequence, Union

__all__ = ["matrix"]


# ─── Brand → tokens ─────────────────────────────────────────────────

def _resolve(brand) -> dict:
    """Pull the seven colors / two fonts the matrix needs from the brand,
    falling back to muriel's OLED defaults when no brand is supplied."""
    if brand is None:
        return {
            "bg":         "#0a0a0f",
            "ink":        "#e6e4d2",
            "muted":      "#b0b0c4",
            "accent":     "#7dd4e4",
            "decorative": "rgba(125, 212, 228, 0.28)",
            "cell_bg":    "rgba(125, 212, 228, 0.05)",
            "body_font":  "ui-sans-serif, -apple-system, system-ui, sans-serif",
            "mono_font":  "ui-monospace, monospace",
        }
    c = brand.colors
    viz = brand.viz.categorical if brand.viz.categorical else []
    accent = viz[0] if viz else (c.foreground or "#7dd4e4")
    return {
        "bg":         c.background,
        "ink":        c.foreground,
        "muted":      c.foreground_muted or c.foreground,
        "accent":     accent,
        "decorative": _rgba(accent, 0.28),
        "cell_bg":    _rgba(accent, 0.05),
        "body_font":  brand.typography.body_family or "system-ui, sans-serif",
        "mono_font":  brand.typography.mono_family or "ui-monospace, monospace",
    }


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ─── Quadrant normalization ─────────────────────────────────────────

_QUAD_KEYS = ("top_left", "top_right", "bottom_left", "bottom_right")


def _normalize_quadrants(quadrants) -> list[dict]:
    """Accept a list of 4 (TL, TR, BL, BR) or a dict keyed by quadrant
    name. Every quadrant ends up as ``{"label": str, "items": list[str]}``."""
    if isinstance(quadrants, dict):
        try:
            ordered = [quadrants[k] for k in _QUAD_KEYS]
        except KeyError as e:
            raise ValueError(
                f"quadrant dict must have keys {_QUAD_KEYS}; missing {e}"
            ) from None
    else:
        ordered = list(quadrants)
    if len(ordered) != 4:
        raise ValueError(f"matrix needs exactly 4 quadrants; got {len(ordered)}")
    out = []
    for q in ordered:
        if isinstance(q, str):
            out.append({"label": q, "items": []})
        else:
            out.append({"label": q.get("label", ""), "items": list(q.get("items") or [])})
    return out


# ─── SVG ────────────────────────────────────────────────────────────

def matrix(
    quadrants,
    *,
    axes: Sequence[Sequence[str]],
    title: Optional[str] = None,
    brand=None,
    out_path: Union[str, Path] = "matrix.svg",
    width: int = 900,
    height: int = 700,
) -> str:
    """Render a 2×2 categorical decomposition.

    Parameters
    ----------
    quadrants
        Four cells. Either a 4-list in TL/TR/BL/BR order, or a dict with
        keys ``top_left``, ``top_right``, ``bottom_left``, ``bottom_right``.
        Each entry is a string (cell title) or a dict
        ``{"label": str, "items": [str, ...]}``.
    axes
        ``((x_low, x_high), (y_low, y_high))``. The four endpoint labels
        sit at the cardinal positions of the cross.
    title
        Optional heading above the matrix.
    brand
        Optional ``muriel.styleguide.StyleGuide`` for colors + typography.
    out_path
        Where to write the SVG.

    Returns
    -------
    str
        The path written.
    """
    cells = _normalize_quadrants(quadrants)
    (x_low, x_high), (y_low, y_high) = axes
    t = _resolve(brand)

    # Layout: leave room for axis-end labels outside the cells.
    pad   = 80
    title_h = 60 if title else 0
    label_pad = 36   # space reserved for axis labels at each side
    grid_x = pad + label_pad
    grid_y = pad + title_h + label_pad
    grid_w = width  - 2 * pad - 2 * label_pad
    grid_h = height - 2 * pad - 2 * label_pad - title_h
    cell_w = grid_w / 2
    cell_h = grid_h / 2

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="{escape(t["body_font"])}">'
    )
    parts.append(f'<rect width="{width}" height="{height}" fill="{t["bg"]}"/>')

    # Title
    if title:
        parts.append(
            f'<text x="{width/2:.1f}" y="{pad - 10:.1f}" '
            f'fill="{t["ink"]}" font-size="20" font-weight="600" '
            f'text-anchor="middle">{escape(title)}</text>'
        )

    # Cell backgrounds + outlines
    for i, (col, row) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
        cx = grid_x + col * cell_w
        cy = grid_y + row * cell_h
        parts.append(
            f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" '
            f'fill="{t["cell_bg"]}" stroke="{t["decorative"]}" stroke-width="1"/>'
        )

    # Cell content
    for i, (col, row) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
        cx = grid_x + col * cell_w
        cy = grid_y + row * cell_h
        cell = cells[i]
        # Label
        parts.append(
            f'<text x="{cx + 18:.1f}" y="{cy + 30:.1f}" '
            f'fill="{t["accent"]}" font-size="15" font-weight="600" '
            f'letter-spacing="0.06em" text-transform="uppercase">'
            f'{escape(cell["label"])}</text>'
        )
        # Items, one per line, max ~5 visible
        for j, item in enumerate(cell["items"][:6]):
            parts.append(
                f'<text x="{cx + 18:.1f}" y="{cy + 58 + j * 22:.1f}" '
                f'fill="{t["ink"]}" font-size="13">'
                f'• {escape(item)}</text>'
            )

    # Axis cross (over the cells, in muted ink so the dividing lines read clearly)
    cx_mid = grid_x + cell_w
    cy_mid = grid_y + cell_h
    parts.append(
        f'<line x1="{cx_mid:.1f}" y1="{grid_y:.1f}" '
        f'x2="{cx_mid:.1f}" y2="{grid_y + grid_h:.1f}" '
        f'stroke="{t["muted"]}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<line x1="{grid_x:.1f}" y1="{cy_mid:.1f}" '
        f'x2="{grid_x + grid_w:.1f}" y2="{cy_mid:.1f}" '
        f'stroke="{t["muted"]}" stroke-width="1.5"/>'
    )

    # Axis end labels with SVG-path arrows (font-free, render anywhere).
    arrow = t["muted"]
    # ↑ above top of cross
    parts.append(
        f'<path d="M {cx_mid - 5:.1f} {grid_y - 6:.1f} L {cx_mid:.1f} {grid_y - 14:.1f} L {cx_mid + 5:.1f} {grid_y - 6:.1f} Z" '
        f'fill="{arrow}"/>'
    )
    parts.append(
        f'<text x="{cx_mid + 12:.1f}" y="{grid_y - 8:.1f}" fill="{t["muted"]}" '
        f'font-size="13" font-weight="500" text-anchor="start">{escape(y_high)}</text>'
    )
    # ↓ below bottom of cross
    parts.append(
        f'<path d="M {cx_mid - 5:.1f} {grid_y + grid_h + 16:.1f} L {cx_mid:.1f} {grid_y + grid_h + 24:.1f} L {cx_mid + 5:.1f} {grid_y + grid_h + 16:.1f} Z" '
        f'fill="{arrow}"/>'
    )
    parts.append(
        f'<text x="{cx_mid - 12:.1f}" y="{grid_y + grid_h + 24:.1f}" fill="{t["muted"]}" '
        f'font-size="13" font-weight="500" text-anchor="end">{escape(y_low)}</text>'
    )
    # ← left of cross
    parts.append(
        f'<path d="M {grid_x - 16:.1f} {cy_mid:.1f} L {grid_x - 8:.1f} {cy_mid - 5:.1f} L {grid_x - 8:.1f} {cy_mid + 5:.1f} Z" '
        f'fill="{arrow}"/>'
    )
    parts.append(
        f'<text x="{grid_x - 22:.1f}" y="{cy_mid + 5:.1f}" fill="{t["muted"]}" '
        f'font-size="13" font-weight="500" text-anchor="end">{escape(x_low)}</text>'
    )
    # → right of cross
    parts.append(
        f'<path d="M {grid_x + grid_w + 16:.1f} {cy_mid:.1f} L {grid_x + grid_w + 8:.1f} {cy_mid - 5:.1f} L {grid_x + grid_w + 8:.1f} {cy_mid + 5:.1f} Z" '
        f'fill="{arrow}"/>'
    )
    parts.append(
        f'<text x="{grid_x + grid_w + 22:.1f}" y="{cy_mid + 5:.1f}" fill="{t["muted"]}" '
        f'font-size="13" font-weight="500" text-anchor="start">{escape(x_high)}</text>'
    )

    parts.append('</svg>')

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return str(out)


def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.matrix spec.json out.svg``.

    Spec format::

        {
          "title": "Eisenhower",
          "axes":  [["not urgent", "urgent"], ["not important", "important"]],
          "quadrants": {
            "top_left":     {"label": "SCHEDULE",   "items": [...]},
            "top_right":    {"label": "DO",         "items": [...]},
            "bottom_left":  {"label": "DELETE",     "items": [...]},
            "bottom_right": {"label": "DELEGATE",   "items": [...]}
          },
          "brand": "examples/muriel-brand.toml"   # optional
        }
    """
    import argparse, json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.matrix")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    matrix(
        spec["quadrants"],
        axes=spec["axes"],
        title=spec.get("title"),
        brand=brand,
        out_path=args.output,
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
