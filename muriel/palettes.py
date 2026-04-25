"""
muriel.palettes — colorblind-safe categorical palettes.

Three name families, all designed and tested for protan, deutan, and
tritan deficiencies:

  - **Wong** (8 colors). Wong, B. (2011). "Color blindness." *Nature
    Methods* 8, 441. The de facto standard for scientific figures since
    publication; deliberately includes a "vermillion" + "bluish green"
    that survive deuteranopia (the most common form).

  - **IBM** (5 colors). IBM Carbon Design System "data-vis colorblind
    palette". Designed for dashboard / chart use; perceptually distinct
    in greyscale and in all three colorblindness modes.
    https://carbondesignsystem.com/data-visualization/color-palettes/

  - **Tol** (5 schemes — Bright, Vibrant, Muted, High-Contrast, plus a
    diverging Sunset). Paul Tol's collection, originally published as
    a SRON technical note. The Bright + Vibrant + Muted qualitatives
    pair well together at different lightness ranges.
    https://personal.sron.nl/~pault/

Why three rather than one
------------------------
Each family makes a different tradeoff:

  - **Wong** maximizes hue separation in deutan space; saturated and
    high-energy. Use when figures will be small or printed.
  - **IBM** is dashboard-tuned: roughly equal lightness, designed to
    avoid any one series visually dominating. Use for ongoing UI.
  - **Tol** gives you matched families at multiple lightnesses
    (Bright/Vibrant/Muted) so multi-panel figures can vary palette
    by panel without breaking visual coherence. Use for paper figures.

When in doubt, use Wong. It's the citation a reviewer expects.

Usage
-----

    from muriel.palettes import WONG, palette, register_matplotlib

    WONG[0]                            # → '#000000' (Wong starts with black)
    palette('tol_bright', n=4)         # → first 4 Tol Bright colors
    register_matplotlib('wong')        # set matplotlib default cycle

CLI:

    python -m muriel.palettes              # print all palettes as a table
    python -m muriel.palettes --swatches   # render an SVG swatch sheet

Cross-references: ``channels/science.md`` (palette section),
``channels/infographics.md`` (named palette use), ``channels/style-guides.md``
(brand viz.categorical population).
"""

from __future__ import annotations

from typing import Optional


# ─── Wong 2011 (Nature Methods) ──────────────────────────────────────

WONG = [
    "#000000",   # black
    "#E69F00",   # orange
    "#56B4E9",   # sky blue
    "#009E73",   # bluish green
    "#F0E442",   # yellow
    "#0072B2",   # blue
    "#D55E00",   # vermillion
    "#CC79A7",   # reddish purple
]

WONG_NAMED = {
    "black":          "#000000",
    "orange":         "#E69F00",
    "sky_blue":       "#56B4E9",
    "bluish_green":   "#009E73",
    "yellow":         "#F0E442",
    "blue":           "#0072B2",
    "vermillion":     "#D55E00",
    "reddish_purple": "#CC79A7",
}


# ─── IBM Carbon Design System (5-color colorblind-safe) ─────────────

IBM = [
    "#648FFF",   # blue
    "#785EF0",   # purple
    "#DC267F",   # magenta / pink
    "#FE6100",   # orange
    "#FFB000",   # yellow / amber
]

IBM_NAMED = {
    "blue":    "#648FFF",
    "purple":  "#785EF0",
    "magenta": "#DC267F",
    "orange":  "#FE6100",
    "yellow":  "#FFB000",
}


# ─── Paul Tol — qualitative schemes ─────────────────────────────────

TOL_BRIGHT = [
    "#4477AA",   # blue
    "#66CCEE",   # cyan
    "#228833",   # green
    "#CCBB44",   # yellow
    "#EE6677",   # red
    "#AA3377",   # purple
    "#BBBBBB",   # grey
]

TOL_VIBRANT = [
    "#EE7733",   # orange
    "#0077BB",   # blue
    "#33BBEE",   # cyan
    "#EE3377",   # magenta
    "#CC3311",   # red
    "#009988",   # teal
    "#BBBBBB",   # grey
]

TOL_MUTED = [
    "#332288",   # indigo
    "#88CCEE",   # cyan
    "#44AA99",   # teal
    "#117733",   # green
    "#999933",   # olive
    "#DDCC77",   # sand
    "#CC6677",   # rose
    "#882255",   # wine
    "#AA4499",   # purple
    "#DDDDDD",   # pale grey
]

TOL_HIGH_CONTRAST = [
    "#DDAA33",   # yellow
    "#BB5566",   # red
    "#004488",   # blue
]

# Tol Sunset — diverging (red ↔ blue, neutral cream midpoint).
# 11-stop sample suitable for direct use as a sequential gradient or as
# a continuous map base. From Paul Tol's "Sunset" diverging scheme.
TOL_SUNSET_DIVERGING = [
    "#364B9A", "#4A7BB7", "#6EA6CD", "#98CAE1", "#C2E4EF",
    "#EAECCC",
    "#FEDA8B", "#FDB366", "#F67E4B", "#DD3D2D", "#A50026",
]


# ─── Unified registry ──────────────────────────────────────────────

PALETTES = {
    "wong":              WONG,
    "ibm":               IBM,
    "tol_bright":        TOL_BRIGHT,
    "tol_vibrant":       TOL_VIBRANT,
    "tol_muted":         TOL_MUTED,
    "tol_hc":            TOL_HIGH_CONTRAST,
    "tol_sunset":        TOL_SUNSET_DIVERGING,
}

CITATIONS = {
    "wong":       "Wong, B. (2011). Color blindness. Nature Methods 8, 441.",
    "ibm":        "IBM Carbon Design System — data-vis colorblind palette.",
    "tol_bright": "Tol, P. (SRON tech note) — Bright qualitative scheme.",
    "tol_vibrant":"Tol, P. (SRON tech note) — Vibrant qualitative scheme.",
    "tol_muted":  "Tol, P. (SRON tech note) — Muted qualitative scheme.",
    "tol_hc":     "Tol, P. (SRON tech note) — High-Contrast scheme.",
    "tol_sunset": "Tol, P. (SRON tech note) — Sunset diverging scheme.",
}


# ─── API ────────────────────────────────────────────────────────────

def palette(name: str, n: Optional[int] = None) -> list[str]:
    """Look up a named palette, optionally sliced to the first ``n`` colors.

    Parameters
    ----------
    name
        Palette key (case-insensitive). One of:
        ``'wong'``, ``'ibm'``, ``'tol_bright'``, ``'tol_vibrant'``,
        ``'tol_muted'``, ``'tol_hc'``, ``'tol_sunset'``.
    n
        Number of colors to return. If larger than the palette,
        wraps around (cycles).

    Returns
    -------
    list[str]
        Hex color strings, suitable for matplotlib, d3, CSS.
    """
    p = PALETTES.get(name.lower())
    if p is None:
        raise ValueError(
            f"unknown palette {name!r}; available: {sorted(PALETTES)}"
        )
    if n is None:
        return list(p)
    if n <= 0:
        return []
    if n <= len(p):
        return list(p[:n])
    # Wrap around for n > len(palette)
    out: list[str] = []
    while len(out) < n:
        out.extend(p)
    return out[:n]


def all_palettes() -> dict[str, list[str]]:
    """Return every named palette as a fresh dict (name → list of hex)."""
    return {k: list(v) for k, v in PALETTES.items()}


def register_matplotlib(name: str = "wong") -> None:
    """Set ``matplotlib.rcParams['axes.prop_cycle']`` to the named palette.

    Raises ImportError if matplotlib isn't installed (kept optional so
    the module imports cleanly without it).
    """
    try:
        import matplotlib as mpl
        from cycler import cycler
    except ImportError as e:
        raise ImportError(
            "matplotlib + cycler required for register_matplotlib(); "
            "pip install matplotlib"
        ) from e
    mpl.rcParams["axes.prop_cycle"] = cycler("color", palette(name))


def citation(name: str) -> str:
    """Return the citation string for a named palette."""
    c = CITATIONS.get(name.lower())
    if c is None:
        raise ValueError(f"unknown palette {name!r}")
    return c


# ─── SVG swatch sheet ──────────────────────────────────────────────

def swatch_sheet_svg(
    *,
    palettes_to_render: Optional[list[str]] = None,
    swatch_w: int = 80,
    swatch_h: int = 60,
    pad: int = 8,
    label_h: int = 24,
    bg: str = "#0a0a0f",
    ink: str = "#e6e4d2",
    body_font: str = "ui-sans-serif, -apple-system, system-ui, sans-serif",
) -> str:
    """Render every palette as a swatch sheet SVG (one row per palette).

    Returns the SVG markup as a string. Useful for ``muriel`` style-guide
    documentation and quick visual audits.
    """
    from html import escape

    if palettes_to_render is None:
        palettes_to_render = list(PALETTES)

    rows = []
    for name in palettes_to_render:
        rows.append((name, PALETTES[name]))

    max_cols = max(len(p) for _, p in rows)
    name_col = 130
    width = name_col + max_cols * (swatch_w + pad) + pad
    row_h = swatch_h + label_h + pad
    height = pad + len(rows) * row_h + pad

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="{escape(body_font)}">',
        f'<rect width="{width}" height="{height}" fill="{bg}"/>',
    ]
    for ri, (name, hexes) in enumerate(rows):
        y_top = pad + ri * row_h
        # Palette name on the left
        parts.append(
            f'<text x="{pad}" y="{y_top + swatch_h/2 + 5:.1f}" fill="{ink}" '
            f'font-size="14" font-weight="600">{escape(name)}</text>'
        )
        for ci, hx in enumerate(hexes):
            x = name_col + ci * (swatch_w + pad)
            parts.append(
                f'<rect x="{x}" y="{y_top}" width="{swatch_w}" height="{swatch_h}" '
                f'fill="{hx}" stroke="rgba(255,255,255,0.10)" stroke-width="1"/>'
            )
            parts.append(
                f'<text x="{x + swatch_w/2}" y="{y_top + swatch_h + 16}" '
                f'fill="{ink}" font-size="10" font-family="ui-monospace, monospace" '
                f'text-anchor="middle">{escape(hx)}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


# ─── CLI ───────────────────────────────────────────────────────────

def _main(argv=None) -> int:
    """``python -m muriel.palettes [--swatches OUT.svg]``.

    Default: prints every palette as a text table with hex codes.
    With ``--swatches PATH``, writes an SVG swatch sheet.
    """
    import argparse
    from pathlib import Path

    ap = argparse.ArgumentParser(prog="python -m muriel.palettes")
    ap.add_argument("--swatches", metavar="OUT.svg", default=None,
                    help="render swatch sheet SVG to OUT.svg")
    args = ap.parse_args(argv)

    if args.swatches:
        out = Path(args.swatches)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(swatch_sheet_svg(), encoding="utf-8")
        print(f"→ {out}")
        return 0

    # Text table
    for name, hexes in PALETTES.items():
        print(f"\n{name}  ({len(hexes)} colors)")
        print(f"  {CITATIONS[name]}")
        print("  " + "  ".join(hexes))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
