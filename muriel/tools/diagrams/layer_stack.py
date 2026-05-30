"""
muriel.tools.diagrams.layer_stack — layered dependency stack as SVG.

When to use
-----------
A set of strata where **higher layers depend on / abstract over lower
ones**, and reading direction itself carries the claim: OSI model, the
CSS cascade, a tech stack, a memory hierarchy, an LLM context window's
nested scopes. The diagram's job is to assert the layering is real —
that you cannot reach an upper layer except *through* the one below.

Anti-prescription
-----------------
- **Don't stack non-hierarchical peers.** If the bands don't depend on
  each other — they're just categories side by side — you want a
  swimlane or an architecture diagram, not a stack. A stack claims
  load-bearing order.
- **Don't skip indices.** ``L1, L2, L4`` invites the reader to hunt for
  the missing layer. Renumber or name honestly.
- **Don't exceed 6 layers.** Past 6 the dependency chain stops being a
  thing a reader can hold; decompose or group.
- **Don't paint every layer a different hue.** Polychrome bands read as
  unrelated categories — the opposite of the "one ladder" claim.

Geometry follows the editorial-diagram discipline: 4px-increment
alignment, 1px hairline dividers, no shadows. Layout reference adapted
from the MIT-licensed diagram-design skill (© 2025 Cathryn Lavery); the
tokens, contrast rule, and epistemic gate are muriel's own.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Optional, Union

__all__ = ["layer_stack"]

# Monospace stack for index tags / notes (the "technical" register).
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


# ─── Layer normalization ────────────────────────────────────────────

def _normalize(layers) -> list[dict]:
    out = []
    for i, l in enumerate(layers):
        if isinstance(l, str):
            out.append({"label": l, "tag": None, "note": None, "focal": False})
        else:
            out.append({
                "label": l.get("label", ""),
                "tag":   l.get("tag") or l.get("index_tag"),
                "note":  l.get("note") or l.get("sublabel"),
                "focal": bool(l.get("focal", False)),
            })
    if not 4 <= len(out) <= 6:
        raise ValueError(f"layer_stack supports 4–6 layers; got {len(out)}")
    return out


# ─── SVG ────────────────────────────────────────────────────────────

def layer_stack(
    layers,
    *,
    title: Optional[str] = None,
    brand=None,
    focal: Optional[int] = None,
    axis_label: Optional[str] = None,
    axis_dir: str = "up",
    out_path: Union[str, Path] = "layer-stack.svg",
    width: int = 1000,
) -> str:
    """Render a 4–6 layer dependency stack.

    Parameters
    ----------
    layers
        4–6 entries in **reading order, top to bottom** (index 0 is the
        top band). Each entry is a string (just the layer name) or a
        dict ``{"label": str, "tag": str, "note": str, "focal": bool}``
        where ``tag`` is the far-left index eyebrow (``"L3"``, ``"07"``,
        ``"APPLICATION"``), ``note`` is the muted far-right annotation,
        and ``focal`` flags the one layer to highlight (bottleneck or
        discussion focus).
    title
        Optional heading above the stack.
    focal
        Index of the single layer to highlight (accent stroke + tint).
        Overrides per-layer ``focal`` flags. Highlight at most one.
    axis_label
        Optional left-margin axis word, e.g. ``"abstraction"`` or
        ``"packets"``. Rendered with a vertical arrow.
    axis_dir
        ``"up"`` (default) or ``"down"`` — which way the axis arrow
        points. ``"up"`` reads "lower layers are foundational; upper
        layers abstract over them."
    brand
        Optional ``muriel.styleguide.StyleGuide``.
    out_path
        Where to write the SVG.

    Returns
    -------
    str
        The path written.
    """
    if axis_dir not in ("up", "down"):
        raise ValueError(f"axis_dir must be 'up' or 'down'; got {axis_dir!r}")

    norm = _normalize(layers)
    n = len(norm)
    t = _resolve(brand)

    # Resolve the single focal layer (explicit arg wins over flags).
    focal_idx = focal
    if focal_idx is None:
        for i, l in enumerate(norm):
            if l["focal"]:
                focal_idx = i
                break
    if focal_idx is not None and not 0 <= focal_idx < n:
        raise ValueError(f"focal index {focal_idx} out of range for {n} layers")

    # ── Geometry (all on a 4px grid) ────────────────────────────────
    band_h   = 64
    band_x   = 180          # leaves a left margin for the axis
    band_w   = 680
    pad_top  = 48
    pad_bot  = 48
    title_h  = 72 if title else 0
    y0       = title_h + pad_top
    stack_h  = n * band_h
    height   = y0 + stack_h + pad_bot
    cx       = width / 2

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="{escape(t["body_font"])}">'
    )
    parts.append(
        f'<defs><marker id="ls-arrow" markerWidth="8" markerHeight="8" '
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

    # ── Layer bands ─────────────────────────────────────────────────
    for i, l in enumerate(norm):
        by = y0 + i * band_h
        mid = by + band_h / 2
        is_focal = (i == focal_idx)
        fill = t["focal_fill"] if is_focal else t["paper"]
        stroke = t["accent"] if is_focal else t["hairline"]
        sw = 1.5 if is_focal else 1
        parts.append(
            f'<rect x="{band_x}" y="{by:.1f}" width="{band_w}" height="{band_h}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )
        # Index tag (mono eyebrow, far left inside band)
        if l["tag"]:
            parts.append(
                f'<text x="{band_x + 20}" y="{mid + 4:.1f}" '
                f'fill="{t["accent"] if is_focal else t["muted"]}" '
                f'font-family="{_MONO}" font-size="10" letter-spacing="1.5" '
                f'text-anchor="start">{escape(str(l["tag"]).upper())}</text>'
            )
        # Layer name (center-left of the band)
        name_x = band_x + (120 if l["tag"] else 24)
        parts.append(
            f'<text x="{name_x}" y="{mid + 5:.1f}" fill="{t["ink"]}" '
            f'font-size="15" font-weight="600" text-anchor="start">'
            f'{escape(l["label"])}</text>'
        )
        # Note (mono muted, far right inside band)
        if l["note"]:
            parts.append(
                f'<text x="{band_x + band_w - 20}" y="{mid + 4:.1f}" '
                f'fill="{t["muted"]}" font-family="{_MONO}" font-size="10" '
                f'text-anchor="end">{escape(l["note"])}</text>'
            )

    # ── Left-margin axis arrow ──────────────────────────────────────
    if axis_label:
        ax = 96
        a_top = y0 + 8
        a_bot = y0 + stack_h - 8
        if axis_dir == "up":
            parts.append(
                f'<line x1="{ax}" y1="{a_bot:.1f}" x2="{ax}" y2="{a_top:.1f}" '
                f'stroke="{t["muted"]}" stroke-width="1" marker-end="url(#ls-arrow)"/>'
            )
        else:
            parts.append(
                f'<line x1="{ax}" y1="{a_top:.1f}" x2="{ax}" y2="{a_bot:.1f}" '
                f'stroke="{t["muted"]}" stroke-width="1" marker-end="url(#ls-arrow)"/>'
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
    """CLI: ``python -m muriel.tools.diagrams.layer_stack spec.json out.svg``.

    Spec format::

        {
          "title":      "The TCP/IP stack",
          "axis_label": "abstraction",
          "axis_dir":   "up",
          "layers": [
            {"tag": "L4", "label": "Application", "note": "HTTP, DNS"},
            {"tag": "L3", "label": "Transport",   "note": "TCP, UDP", "focal": true},
            {"tag": "L2", "label": "Internet",    "note": "IP"},
            {"tag": "L1", "label": "Link",        "note": "Ethernet, Wi-Fi"}
          ],
          "brand": "examples/muriel-brand.toml"
        }
    """
    import argparse, json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.layer_stack")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    layer_stack(
        spec["layers"],
        title=spec.get("title"),
        brand=brand,
        focal=spec.get("focal"),
        axis_label=spec.get("axis_label"),
        axis_dir=spec.get("axis_dir", "up"),
        out_path=args.output,
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
