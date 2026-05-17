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

from typing import Optional, Sequence


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


# ─── Contrast-floor palette generator ──────────────────────────────


def generate_for_floor(
    bg: str,
    *,
    floor: float = 8.0,
    hues: Optional[Sequence[float]] = None,
    n: int = 6,
    direction: str = "auto",
    chroma_max: float = 0.4,
) -> list[str]:
    """Generate a categorical palette where every color clears ``floor`` contrast vs ``bg``.

    The named palettes above (Wong, IBM, Tol) are *audited* against
    muriel's 8:1 floor after the fact — they pass on near-black
    backgrounds because their authors hand-picked saturations that
    happen to work. This function inverts the relationship: pick a
    background + a contrast floor, and the palette is generated *at*
    the floor by construction. Every output color is guaranteed by
    the algorithm (not by audit) to hit ``floor`` vs ``bg``.

    Lineage
    -------
    Adobe Leonardo (https://github.com/adobe/leonardo, Apache-2.0).
    Leonardo's core insight is that brand palettes should be generated
    at a target contrast ratio, not generated freely and audited
    after. This function is a Python port of that idea, scoped to
    muriel's OKLCH pipeline + WCAG 2.1 enforcement.

    Algorithm
    ---------
    For each hue:

    1. Solve the WCAG formula for the target relative luminance
       (``L_fg = (L_bg + 0.05) * floor - 0.05`` for the light direction,
       ``L_bg / floor`` for the dark direction).
    2. Binary-search OKLCH perceptual L for an achromatic color at the
       target relative luminance.
    3. Binary-search the maximum sRGB-gamut chroma at that L and hue.
    4. Verify contrast (gamut clamping can shift luminance off-target);
       nudge L 1% at a time away from the bg if needed.

    Parameters
    ----------
    bg : str
        Background hex (e.g. ``"#0a0a0f"``). Every output color hits
        ``contrast_ratio(color, bg) >= floor``.
    floor : float
        Minimum WCAG 2.1 contrast ratio. Default 8.0 — muriel's
        universal text floor.
    hues : sequence of float, optional
        Explicit hue angles in degrees ``[0, 360)``. If omitted, uses
        ``n`` evenly-spaced hues starting at 0°.
    n : int
        Number of colors when ``hues`` is omitted (default 6).
    direction : {"light", "dark", "auto"}
        Whether outputs should be lighter or darker than ``bg``.
        ``"auto"`` picks whichever has more luminance headroom — light
        for dark backgrounds, dark for light.
    chroma_max : float
        Upper bound on OKLCH chroma considered per hue (default 0.4 —
        the sRGB outer envelope). Lower values produce more muted
        palettes.

    Returns
    -------
    list[str]
        Hex strings, all clearing ``floor`` vs ``bg``.

    Raises
    ------
    ValueError
        If ``floor`` is unreachable in the chosen direction (mid-tone
        bg + very high floor), or if a specific hue can't satisfy the
        floor after gamut clamping.

    Example
    -------

    ::

        >>> from muriel.palettes import generate_for_floor
        >>> from muriel.contrast import contrast_ratio
        >>> p = generate_for_floor("#0a0a0f", floor=8.0, n=6)
        >>> all(contrast_ratio(c, "#0a0a0f") >= 8.0 for c in p)
        True

    See also
    --------
    ``muriel.contrast.contrast_ratio`` — the WCAG 2.1 formula.
    ``muriel.oklch`` — the OKLCH conversion pipeline this function
    binary-searches over.
    """
    # Lazy import so the named-palette path stays import-cheap.
    from muriel.contrast import contrast_ratio, hex_to_rgb, relative_luminance
    from muriel.oklch import Oklch, oklch_to_rgb, in_srgb_gamut

    bg_rgb = hex_to_rgb(bg)
    bg_lum = relative_luminance(bg_rgb)

    # Decide direction if auto.
    if direction == "auto":
        light_target = (bg_lum + 0.05) * floor - 0.05
        dark_target = (bg_lum + 0.05) / floor - 0.05
        light_ok = light_target <= 1.0
        dark_ok = dark_target >= 0.0
        if light_ok and not dark_ok:
            direction = "light"
        elif dark_ok and not light_ok:
            direction = "dark"
        elif light_ok and dark_ok:
            # Both work — pick the side with more breathing room.
            direction = "light" if (1.0 - light_target) > dark_target else "dark"
        else:
            raise ValueError(
                f"floor={floor} unreachable from bg luminance {bg_lum:.3f} "
                f"in either direction; lower the floor or change the bg."
            )
    if direction not in ("light", "dark"):
        raise ValueError(
            f"direction must be 'light' | 'dark' | 'auto'; got {direction!r}"
        )

    if hues is None:
        if n <= 0:
            raise ValueError(f"n must be > 0; got {n}")
        hues = [i * 360.0 / n for i in range(n)]

    out: list[str] = []
    for hue in hues:
        rgb = _hue_color_meeting_floor(
            bg_rgb, bg_lum, float(hue), floor, direction, chroma_max,
        )
        out.append("#{:02x}{:02x}{:02x}".format(*rgb))
    return out


def _hue_color_meeting_floor(
    bg_rgb: tuple[int, int, int],
    bg_lum: float,
    hue: float,
    floor: float,
    direction: str,
    chroma_max: float,
) -> tuple[int, int, int]:
    """Return the (R, G, B) at this hue that meets ``floor`` contrast vs bg."""
    from muriel.contrast import contrast_ratio, relative_luminance
    from muriel.oklch import Oklch, oklch_to_rgb, in_srgb_gamut

    # 1. Target relative luminance per WCAG.
    if direction == "light":
        target_lum = (bg_lum + 0.05) * floor - 0.05
        if target_lum > 1.0:
            raise ValueError(
                f"floor={floor} unreachable in light direction at hue={hue:.1f}° "
                f"(needs luminance {target_lum:.3f} > 1.0)"
            )
    else:
        target_lum = (bg_lum + 0.05) / floor - 0.05
        if target_lum < 0.0:
            raise ValueError(
                f"floor={floor} unreachable in dark direction at hue={hue:.1f}° "
                f"(needs luminance {target_lum:.3f} < 0.0)"
            )

    # 2. Binary-search OKLCH perceptual L for the achromatic color at
    # the target relative luminance. (OKLCH L is perceptual; relative
    # luminance is the WCAG sRGB-EOTF-weighted quantity; the two are
    # related but not equal, so we search.)
    lo_L, hi_L = 0.0, 1.0
    for _ in range(40):
        mid_L = (lo_L + hi_L) / 2.0
        rgb = oklch_to_rgb(Oklch(mid_L, 0.0, hue))
        lum = relative_luminance(rgb)
        if lum < target_lum:
            lo_L = mid_L
        else:
            hi_L = mid_L
    perc_L = (lo_L + hi_L) / 2.0

    # 3. Binary-search max chroma at this L+H staying in sRGB gamut.
    lo_C, hi_C = 0.0, chroma_max
    for _ in range(30):
        mid_C = (lo_C + hi_C) / 2.0
        if in_srgb_gamut(Oklch(perc_L, mid_C, hue)):
            lo_C = mid_C
        else:
            hi_C = mid_C
    max_C = lo_C

    # 4. Verify contrast — gamut clamping can shift luminance off-target;
    # nudge L further from bg in 1% steps until floor is cleared.
    color = Oklch(perc_L, max_C, hue)
    rgb = oklch_to_rgb(color)
    if contrast_ratio(rgb, bg_rgb) < floor:
        step = 0.01 if direction == "light" else -0.01
        for _ in range(40):
            perc_L = max(0.0, min(1.0, perc_L + step))
            color = Oklch(perc_L, max_C, hue)
            rgb = oklch_to_rgb(color)
            if contrast_ratio(rgb, bg_rgb) >= floor:
                return rgb
        raise ValueError(
            f"could not reach floor={floor} at hue={hue:.1f}°; "
            f"highest achievable was {contrast_ratio(rgb, bg_rgb):.2f}:1"
        )
    return rgb


def _selftest() -> int:
    """Run ``generate_for_floor`` invariant checks."""
    # Lazy import — keep the module loadable without contrast.py / oklch.py
    # being requested on every import.
    from muriel.contrast import contrast_ratio

    # Dark bg, auto direction → light foregrounds, all clear 8:1.
    p = generate_for_floor("#0a0a0f", floor=8.0, n=6)
    assert len(p) == 6
    for hex_color in p:
        assert hex_color.startswith("#") and len(hex_color) == 7
        ratio = contrast_ratio(hex_color, "#0a0a0f")
        assert ratio >= 8.0 - 1e-3, (
            f"{hex_color} only achieved {ratio:.2f}:1 vs #0a0a0f"
        )

    # Light bg, auto direction → dark foregrounds, all clear 8:1.
    p = generate_for_floor("#fafafa", floor=8.0, n=6)
    assert len(p) == 6
    for hex_color in p:
        ratio = contrast_ratio(hex_color, "#fafafa")
        assert ratio >= 8.0 - 1e-3

    # Custom floor (WCAG AA: 4.5).
    p = generate_for_floor("#0a0a0f", floor=4.5, n=8)
    assert len(p) == 8
    for hex_color in p:
        assert contrast_ratio(hex_color, "#0a0a0f") >= 4.5 - 1e-3

    # Custom hues (e.g. brand cyan + magenta).
    p = generate_for_floor("#0a0a0f", floor=8.0, hues=[200, 320])
    assert len(p) == 2

    # Determinism — same input, same output.
    p1 = generate_for_floor("#0a0a0f", floor=8.0, n=6)
    p2 = generate_for_floor("#0a0a0f", floor=8.0, n=6)
    assert p1 == p2

    # Mid-tone bg with too-high floor in both directions → ValueError.
    try:
        generate_for_floor("#808080", floor=10.0, n=3)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "expected ValueError for mid-tone bg + floor 10.0"
        )

    # Explicit direction conflict with bg → ValueError.
    try:
        # Very light bg with direction='light' — there's nowhere lighter.
        generate_for_floor("#fafafa", floor=8.0, direction="light", n=3)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "expected ValueError for direction='light' on near-white bg"
        )

    # Invalid direction.
    try:
        generate_for_floor("#0a0a0f", direction="sideways")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for invalid direction")

    return 0


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
    ap.add_argument("--generate", action="store_true",
                    help="generate a contrast-floor palette via "
                         "generate_for_floor() — see --bg, --floor, --n")
    ap.add_argument("--bg", default="#0a0a0f",
                    help="background hex for --generate (default #0a0a0f)")
    ap.add_argument("--floor", type=float, default=8.0,
                    help="target WCAG ratio for --generate (default 8.0)")
    ap.add_argument("--n", type=int, default=6,
                    help="number of colors for --generate (default 6)")
    ap.add_argument("--direction", default="auto",
                    choices=("auto", "light", "dark"),
                    help="--generate direction (default auto)")
    ap.add_argument("--selftest", action="store_true",
                    help="run generate_for_floor() invariant checks")
    args = ap.parse_args(argv)

    if args.selftest:
        _selftest()
        print("muriel.palettes: selftest passed")
        return 0

    if args.generate:
        from muriel.contrast import contrast_ratio
        p = generate_for_floor(
            args.bg, floor=args.floor, n=args.n, direction=args.direction,
        )
        print(
            f"\n  generate_for_floor(bg={args.bg!r}, "
            f"floor={args.floor}, n={args.n}, "
            f"direction={args.direction!r})"
        )
        for hx in p:
            r = contrast_ratio(hx, args.bg)
            print(f"    {hx}   contrast vs {args.bg} = {r:.2f}:1")
        print()
        return 0

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
