"""
muriel.palettes — categorical palettes for data viz + theme registers.

Two tiers — **data-viz** (colorblind-safe, audited) and **theme**
(aesthetic-first, NOT colorblind-tested).

Data-viz palettes — designed and tested for protan, deutan, and
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

Theme palettes — aesthetic-first, brand register, NOT colorblind-
tested and NOT all 8:1 on muriel's universal floor (they're designed
against the theme's own bg, not muriel's). Use them for editorial /
UI register where coherence and recognisability matter more than
colorblind separation:

  - **Catppuccin** (Mocha — dark, 14 accents; Latte — light, 14
    accents). Soothing pastels designed for syntax-highlighting + UI
    theming. MIT. https://github.com/catppuccin/catppuccin

  - **Nord** (Aurora — 5 warm accents; Frost — 4 cool blues). The
    Arctic, north-bluish palette. Aurora reads as muted-editorial;
    Frost as tech-cool. MIT. https://github.com/nordtheme/nord

When you need a guaranteed-8:1 categorical set against a specific
brand background, use ``generate_for_floor()`` below — it generates
the palette at the target contrast ratio by construction.

When in doubt for a scientific figure, use Wong. It's the citation a
reviewer expects.

Usage
-----

    from muriel.palettes import (
        WONG, CATPPUCCIN_MOCHA, NORD_AURORA,
        palette, generate_for_floor, register_matplotlib, validate,
    )

    WONG[0]                            # → '#000000'
    palette('tol_bright', n=4)         # → first 4 Tol Bright colors
    palette('catppuccin_mocha', n=6)   # → first 6 Mocha accents
    register_matplotlib('nord_aurora') # set matplotlib default cycle
    generate_for_floor('#0a0a0f',      # → 6 hues guaranteed 8:1 on bg
                       floor=8.0, n=6)
    validate(WONG, bg='#0a0a0f')       # → PaletteReport(ok=True, …)

Validating your own colors
--------------------------

The named palettes above are safe on authority — Wong is the citation a
reviewer expects. That authority does not transfer to a brand palette, to
``generate_for_floor()`` output, or to any hand-picked set. :func:`validate`
runs the four checks ``muriel.contrast`` cannot: OKLCH lightness band, chroma
floor, CVD separation (via :mod:`muriel.cvd`), and contrast vs the surface.
Contrast measures each color against the *background*; ``validate`` measures
the palette against *itself*, which is where categorical palettes actually
fail.

CLI:

    python -m muriel.palettes              # print all palettes as a table
    python -m muriel.palettes --swatches OUT.svg
                                            # render an SVG swatch sheet
    python -m muriel.palettes --generate --bg "#0a0a0f" --floor 8 --n 6
                                            # contrast-floor palette
    python -m muriel.palettes --validate "#4477AA,#EE6677" --bg "#0a0a0f"
                                            # the four checks
    python -m muriel.palettes --palette wong --pairs adjacent
                                            # validate a named palette

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


# ─── Theme palettes — Catppuccin + Nord ────────────────────────────
#
# Theme palettes (vs the data-viz palettes above): designed for
# editorial / brand / UI register where aesthetic coherence matters
# more than colorblind separation. NOT all 8:1 on muriel's universal
# floor — these are paint-chip palettes, not data-vis ones. When you
# need a guaranteed-8:1 categorical set, use ``generate_for_floor()``
# below; when you want a recognisable brand register, reach here.

# Catppuccin Mocha — the dark flavor, 14 accent colors.
# https://github.com/catppuccin/catppuccin · MIT
# Designed against the Catppuccin Mocha base (#1e1e2e). Reorder favours
# putting warm pastels first (most common reach for highlight + accent
# UI roles); blues/lavenders cluster at the end.
CATPPUCCIN_MOCHA = [
    "#f5c2e7",   # pink
    "#cba6f7",   # mauve
    "#f38ba8",   # red
    "#eba0ac",   # maroon
    "#fab387",   # peach
    "#f9e2af",   # yellow
    "#a6e3a1",   # green
    "#94e2d5",   # teal
    "#89dceb",   # sky
    "#74c7ec",   # sapphire
    "#89b4fa",   # blue
    "#b4befe",   # lavender
    "#f5e0dc",   # rosewater
    "#f2cdcd",   # flamingo
]

# Catppuccin Latte — the light flavor, 14 accent colors at deeper
# saturation suited for paper/white-canvas register.
CATPPUCCIN_LATTE = [
    "#ea76cb",   # pink
    "#8839ef",   # mauve
    "#d20f39",   # red
    "#e64553",   # maroon
    "#fe640b",   # peach
    "#df8e1d",   # yellow
    "#40a02b",   # green
    "#179299",   # teal
    "#04a5e5",   # sky
    "#209fb5",   # sapphire
    "#1e66f5",   # blue
    "#7287fd",   # lavender
    "#dc8a78",   # rosewater
    "#dd7878",   # flamingo
]

# Nord Aurora — the Arctic palette's 5-color categorical "Aurora"
# accent set. https://github.com/nordtheme/nord · MIT
# Designed against Nord's Polar Night (#2e3440); read as muted-warm
# editorial. The five colors map onto the typical {error, warn, info,
# success, ?} semantic roles though the project doesn't bind them.
NORD_AURORA = [
    "#bf616a",   # nord11 — red (aurora 1)
    "#d08770",   # nord12 — orange (aurora 2)
    "#ebcb8b",   # nord13 — yellow (aurora 3)
    "#a3be8c",   # nord14 — green (aurora 4)
    "#b48ead",   # nord15 — purple (aurora 5)
]

# Nord Frost — the four cool blues of Nord, suited for axis chrome,
# decorative rules, or any "tech-cool" UI register.
NORD_FROST = [
    "#8fbcbb",   # nord7 — pale teal
    "#88c0d0",   # nord8 — frost light
    "#81a1c1",   # nord9 — frost medium
    "#5e81ac",   # nord10 — frost deep
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
    "catppuccin_mocha":  CATPPUCCIN_MOCHA,
    "catppuccin_latte":  CATPPUCCIN_LATTE,
    "nord_aurora":       NORD_AURORA,
    "nord_frost":        NORD_FROST,
}

CITATIONS = {
    "wong":              "Wong, B. (2011). Color blindness. Nature Methods 8, 441.",
    "ibm":               "IBM Carbon Design System — data-vis colorblind palette.",
    "tol_bright":        "Tol, P. (SRON tech note) — Bright qualitative scheme.",
    "tol_vibrant":       "Tol, P. (SRON tech note) — Vibrant qualitative scheme.",
    "tol_muted":         "Tol, P. (SRON tech note) — Muted qualitative scheme.",
    "tol_hc":            "Tol, P. (SRON tech note) — High-Contrast scheme.",
    "tol_sunset":        "Tol, P. (SRON tech note) — Sunset diverging scheme.",
    "catppuccin_mocha":  "Catppuccin — Mocha (dark) flavor (MIT). 14/14 clear 8:1 on #0a0a0f; designed for the Catppuccin Mocha base #1e1e2e. https://github.com/catppuccin/catppuccin",
    "catppuccin_latte":  "Catppuccin — Latte (light) flavor (MIT). Saturated mid-tones; 0/14 clear muriel's 8:1 on standard #fafafa — use as fills, markers, or decorative chrome, NOT text. Designed for Latte's own #eff1f5 base. https://github.com/catppuccin/catppuccin",
    "nord_aurora":       "Nord — Aurora accent set (MIT). 2/5 clear 8:1 on #0a0a0f (red + orange); the muted yellow, green, purple are decorative-only. https://github.com/nordtheme/nord",
    "nord_frost":        "Nord — Frost cool-blue set (MIT). 2/4 clear 8:1 on #0a0a0f (the two lighter teals). https://github.com/nordtheme/nord",
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


def uipromax_brand_palettes(meeting_floor: bool = True) -> list[dict]:
    """Brand UI colour *sets* from the ui-ux-pro-max corpus (:mod:`muriel.uipromax`).

    Unlike the viz palettes above (ordered hex lists for charts), these are
    product-type → semantic-role sets (Primary / Background / Foreground / Card
    / Accent / Destructive / …). With ``meeting_floor=True`` (default) only sets
    whose body text clears muriel's 8:1 floor are returned; their interactive
    pairs (``On Primary`` etc.) still need a per-button contrast pass. Lazy-
    imported so palettes.py keeps its zero-dependency import. The corpus is a
    verbatim MIT port — see ``THIRD_PARTY_NOTICES.md``.
    """
    from muriel import uipromax
    return uipromax.palettes(meeting_floor=meeting_floor)


# ─── Palette validation ────────────────────────────────────────────
#
# muriel.contrast measures a color against the *background*. That catches
# illegibility and misses palette collapse: two hues can each clear 8:1 on
# near-black and still be the same color to a deuteranope. These checks
# measure the palette against *itself* (and its surface) — the questions
# contrast.py structurally cannot ask.

# Two checks the sibling validators run are deliberately NOT implemented here.
# Both are real checks — in a design system whose parameters differ from muriel's.
# Ported verbatim they would each reject muriel's own house style, which is the
# signature of a constant that belongs to its original system, not to the method.
#
# **Lightness band** (theirs: OKLCH L 0.48–0.67 on dark). Tuned to a lighter
# surface (#1a1a19) and a permissive 3:1 mark floor. Muriel's OLED register runs
# bright on #0a0a0f, where an 8:1 floor *mathematically forces* L >= ~0.72: every
# color generate_for_floor() emits at the floor lands at L 0.72–0.75, and the
# shipped chart tokens (#ffa07a L=0.794, #bbb L=0.792) sit higher still. The band
# would reject muriel's own generator output wholesale. It is redundant besides:
# its lower bound restates "don't dissolve into the surface" (the contrast check)
# and its upper bound restates "don't blow out to white" (chroma).
#
# **Chroma floor** (theirs: OKLCH C >= 0.10, a gray slot "encodes nothing").
# True where gray is reserved for chrome. Muriel reserves no such thing —
# channels/charts.md rule 10 is *gray-first*: a muted gray default series with one
# accent is the house pattern. The floor also fails Wong's #000000 on the white
# paper Wong was designed for, and Tol Bright's #BBBBBB. A check that rejects the
# canonical colorblind-safe palette on its own surface is measuring the wrong
# thing. The real risk — two neutral slots colliding — is caught by CVD
# separation, which scores muriel's gray-first pair (#bbb ↔ #ffa07a) at ΔE 29.7.
#
# What is left is what was genuinely missing: separation, plus a role-aware
# contrast floor. Composing those two is the whole job.

MARK_CONTRAST_FLOOR = 3.0
"""WCAG 2.1 SC 1.4.11 non-text contrast — the floor for a *fill* against its surface."""

TEXT_CONTRAST_FLOOR = 8.0
"""muriel's universal floor — applies the moment a palette color is used as text."""


class Check:
    """One validation check's outcome.

    ``status`` is ``'pass'``, ``'warn'`` (conditional — legal only with the
    stated mitigation), or ``'fail'`` (the palette is wrong).
    """

    __slots__ = ("name", "status", "detail")

    def __init__(self, name: str, status: str, detail: str):
        self.name = name
        self.status = status
        self.detail = detail

    def __repr__(self) -> str:
        return f"Check({self.name!r}, {self.status!r}, {self.detail!r})"


class PaletteReport:
    """The result of :func:`validate`. Truthy when no check failed."""

    __slots__ = ("checks", "palette", "bg", "mode")

    def __init__(self, checks, palette, bg, mode):
        self.checks = checks
        self.palette = palette
        self.bg = bg
        self.mode = mode

    @property
    def ok(self) -> bool:
        """True when no check has status ``'fail'``. WARNs do not gate."""
        return not any(c.status == "fail" for c in self.checks)

    @property
    def warnings(self) -> list:
        """Checks that passed conditionally — each carries a mandatory mitigation."""
        return [c for c in self.checks if c.status == "warn"]

    def __bool__(self) -> bool:
        return self.ok

    def __repr__(self) -> str:
        return (f"PaletteReport({len(self.palette)} slots, {self.mode}, "
                f"{'ok' if self.ok else 'FAILED'}, "
                f"{len(self.warnings)} warning(s))")


def validate(
    palette_colors: Sequence[str],
    *,
    bg: str = "#0a0a0f",
    pairs: str = "all",
    as_text: bool = False,
) -> PaletteReport:
    """Validate a categorical palette against the checks contrast alone can't make.

    Two checks, computed — never eyeballed:

    1. **CVD separation** — worst protan/deutan pair >= :data:`muriel.cvd.CVD_TARGET`.
       Between TARGET and FLOOR the palette is legal *only* with a second
       encoding channel (direct label, dash, shape, texture). This is the
       check :mod:`muriel.contrast` structurally cannot make: contrast measures
       each color against the *background*, and two hues can each clear 8:1 on
       near-black while being the same color to a deuteranope.
    2. **Contrast vs surface** — see the floor note below.

    Sibling validators also gate a lightness band and a chroma floor. Muriel
    deliberately runs neither — see the comment above this function; ported to
    muriel's surfaces they reject muriel's own generator output and its
    gray-first house pattern.

    The floor depends on what the color *is*, not what it costs to pass
    ---------------------------------------------------------------------
    muriel's 8:1 rule governs **readable text** — anything parsed for meaning.
    A bar fill is not text: it is a mark whose job is to be distinguishable,
    and WCAG 2.1 SC 1.4.11 sets 3:1 for that. So by default this function
    gates marks at :data:`MARK_CONTRAST_FLOOR` (3.0), not at 8.0 — applying
    the text floor to fills would be over-reading muriel's own rule, and would
    reject Wong, IBM, and Tol wholesale.

    Pass ``as_text=True`` when the palette's colors will also be rendered as
    type (data labels, direct series labels, KPI values). Then the floor is
    :data:`TEXT_CONTRAST_FLOOR` (8.0) and it is hard — that is muriel's rule,
    and it does not bend for a chart.

    Parameters
    ----------
    palette_colors
        Hex strings in slot order.
    bg
        The surface the marks render on. Default ``'#0a0a0f'`` (muriel's OLED
        near-black). Contrast and band results are only meaningful against the
        surface the chart actually uses — pass your own.
    pairs
        ``'all'`` (default) — any two marks can meet: scatter, bubble,
        choropleth, small multiples. ``'adjacent'`` — bars, stacks, lines,
        where slot assignment never skips.
    as_text
        Gate contrast at muriel's 8:1 text floor instead of the 3:1 mark floor.

    Returns
    -------
    PaletteReport
        Truthy when nothing failed. Inspect ``.checks`` for detail and
        ``.warnings`` for the conditional passes.

    Example
    -------

    ::

        >>> from muriel.palettes import validate, WONG
        >>> bool(validate(WONG, bg="#0a0a0f"))
        True

    See also
    --------
    :func:`muriel.cvd.worst_separation` — the separation check on its own.
    :func:`generate_for_floor` — build a palette at a contrast floor by construction.
    :func:`muriel.contrast.audit_svg` — legibility of rendered text.
    """
    from muriel.contrast import contrast_ratio, hex_to_rgb, relative_luminance
    from muriel.cvd import CVD_FLOOR, CVD_TARGET, worst_separation

    colors = [c for c in palette_colors]
    if not colors:
        raise ValueError("palette is empty")

    # Mode is reported for context and follows the surface, not the caller's
    # say-so — it is a fact about the background's luminance.
    mode = "dark" if relative_luminance(hex_to_rgb(bg)) < 0.5 else "light"
    checks = []

    # 1. CVD separation — the whole reason this module exists.
    if len(colors) < 2:
        checks.append(Check("CVD separation", "pass", "single slot — nothing to separate"))
    else:
        worst = worst_separation(colors, pairs=pairs)
        status = {"pass": "pass", "floor": "warn", "fail": "fail"}[worst.status]
        detail = (f"worst {pairs} pair ΔE {worst.delta:.1f} ({worst.kind}) — "
                  f"slot {worst.index_a} {worst.color_a} ↔ "
                  f"slot {worst.index_b} {worst.color_b}")
        if status == "warn":
            detail += (f"; in the {CVD_FLOOR}–{CVD_TARGET} floor band — a second "
                       "encoding channel (direct label, dash, shape, texture) is mandatory")
        elif status == "fail":
            detail += f"; below the {CVD_FLOOR} floor — these slots collapse"
        checks.append(Check("CVD separation", status, detail))

    # 2. Contrast vs surface.
    floor = TEXT_CONTRAST_FLOOR if as_text else MARK_CONTRAST_FLOOR
    role = "text" if as_text else "marks"
    low = [(c, round(contrast_ratio(c, bg), 2))
           for c in colors if contrast_ratio(c, bg) < floor]
    if not low:
        status, detail = "pass", f"all {len(colors)} >= {floor}:1 vs {bg} ({role})"
    elif as_text:
        # muriel's floor. It does not have a relief valve.
        status = "fail"
        detail = (f"below muriel's {floor}:1 text floor vs {bg}: {low}. "
                  "These colors cannot carry type — use a text token and let a "
                  "mark beside it carry identity.")
    else:
        # A fill under 3:1 is legal with relief; it is not free.
        status = "warn"
        detail = (f"below {floor}:1 vs {bg}: {low}. Legal for fills only with "
                  "relief — visible direct labels or a companion table.")
    checks.append(Check("Contrast vs surface", status, detail))

    return PaletteReport(checks, colors, bg, mode)


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

    Guarantees what it optimizes, and only that
    -------------------------------------------
    Every output clears ``floor`` **against the background**. It does *not*
    guarantee the colors are distinguishable **from each other** — the hues are
    spaced evenly in degrees, which is not the same as spaced evenly under
    color-vision deficiency. Evenly-spaced hues can still collapse for a
    deuteranope (``n=6`` on ``#0a0a0f`` puts slots 0 and 3 at ΔE 6.4, below the
    separation floor). Pass the result through :func:`validate` — the CVD check
    is exactly the complement this function lacks — and reorder or reduce ``n``
    if it warns. The two functions are designed to be used together.

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

    # ── validate() ──────────────────────────────────────────────────

    # Wong is THE colorblind-safe reference. On the white paper it was designed
    # for, all eight slots (black included) must pass — a validator that rejects
    # Wong on its own surface is measuring the wrong thing.
    assert validate(WONG, bg="#fffff8").ok, "Wong must pass on the paper register"

    # On OLED near-black, Wong's black slot (#000000) is invisible — 1.06:1, a
    # real property of the palette on this surface. As MARKS it warns (relief
    # available); it must not silently pass, and must not hard-fail as if #000000
    # were forbidden everywhere. (Muriel keeps no chroma gate, so a gray/black
    # slot is judged by whether it can be *seen*, not by whether it has a hue.)
    dark = validate(WONG, bg="#0a0a0f")
    dark_contrast = [c for c in dark.checks if c.name == "Contrast vs surface"][0]
    assert dark_contrast.status == "warn"
    assert "#000000" in dark_contrast.detail

    # Mode follows the surface's luminance, not the caller.
    assert validate(WONG, bg="#0a0a0f").mode == "dark"
    assert validate(WONG, bg="#fffff8").mode == "light"

    # The load-bearing invariant: muriel's own generator output must never fail
    # validate()'s *contrast* check on the surface it was generated for. This
    # fires if a foreign lightness band (incompatible with the 8:1 floor, which
    # forces L >= ~0.72 on near-black) ever creeps in. generate_for_floor emits
    # colors AT the floor by construction, so as_text=True must find them clean.
    generated = generate_for_floor("#0a0a0f", floor=8.0, n=6)
    gen_report = validate(generated, bg="#0a0a0f", as_text=True)
    gen_contrast = [c for c in gen_report.checks if c.name == "Contrast vs surface"][0]
    assert gen_contrast.status == "pass", (
        "generate_for_floor() output must clear validate()'s contrast check on "
        "the same bg — any non-pass means an imported band or chroma gate is "
        "fighting muriel's generator"
    )
    # NB: gen_report.ok may still be False — the generator spaces hues evenly and
    # does NOT check CVD separation, so its output can collapse under deuteranopia
    # (n=6 on #0a0a0f: slots 0↔3 at ΔE 6.4). That is a real generator limitation,
    # not a validate() bug: the two are complementary, and validate() is exactly
    # what catches it. See generate_for_floor's own note.

    # Gray-first (charts.md rule 10): a muted gray series + one accent is muriel
    # house style and must validate cleanly — never rejected for "being gray".
    assert validate(["#bbbbbb", "#ffa07a"], bg="#0a0a0f").ok

    # The floor depends on the color's role. Wong's black slot cannot carry
    # type on near-black — as text that must FAIL, as a mark it need not.
    text_report = validate(WONG, bg="#0a0a0f", as_text=True)
    assert not text_report.ok, "8:1 text floor must reject #000000 on #0a0a0f"
    contrast_check = [c for c in text_report.checks if c.name == "Contrast vs surface"][0]
    assert contrast_check.status == "fail", "muriel's text floor has no relief valve"

    # A mark below 3:1 warns (relief available) rather than failing.
    mark_report = validate(["#0a0a10", "#EE6677"], bg="#0a0a0f")
    mark_contrast = [c for c in mark_report.checks if c.name == "Contrast vs surface"][0]
    assert mark_contrast.status == "warn"

    # The check that earns the module: two hues that both clear the 8:1 TEXT
    # floor on near-black yet collapse for a deuteranope (ΔE 6.4). muriel.contrast
    # sees two happy PASSes — this pair is lifted straight from generate_for_floor
    # output, so it also proves the generator can emit CVD-colliding palettes.
    from muriel.contrast import contrast_ratio
    pink, teal = "#ff78af", "#00bfa8"
    for c in (pink, teal):
        assert contrast_ratio(c, "#0a0a0f") >= 8.0, "control: both clear the text floor"
    collapsed = validate([pink, teal], bg="#0a0a0f")
    cvd_check = [c for c in collapsed.checks if c.name == "CVD separation"][0]
    assert cvd_check.status == "fail", (
        f"expected CVD collapse for {pink}/{teal}, got {cvd_check.status}"
    )
    assert not collapsed.ok

    # A gray is judged by separation, not by a chroma gate. muriel's documented
    # gray-first pair passes (asserted above); a gray only fails when it actually
    # collapses into its neighbour — e.g. #888 mid-gray vs Tol red #EE6677 darken
    # together under protanopia (ΔE 6.5). That is the CVD check doing its job, not
    # a "no grays allowed" rule. Pin the distinction so no one re-adds a chroma gate.
    assert validate(["#888888", "#EE6677"], bg="#0a0a0f").checks[0].status == "fail"
    assert validate(["#bbbbbb", "#ffa07a"], bg="#0a0a0f").ok  # separated gray: fine

    # Report truthiness tracks .ok, and warnings never gate.
    assert bool(validate(WONG, bg="#0a0a0f")) is True
    assert all(c.status != "fail" for c in validate(WONG, bg="#0a0a0f").checks)

    # Empty palette is an error, not a silent pass.
    try:
        validate([], bg="#0a0a0f")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for empty palette")

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
    ap.add_argument("--validate", metavar="HEXES", default=None,
                    help="validate a comma-separated palette (or a named "
                         "palette with --palette) against the four checks")
    ap.add_argument("--palette", dest="named", default=None, metavar="NAME",
                    help="named palette to --validate (wong, ibm, tol_bright, …)")
    ap.add_argument("--pairs", choices=("adjacent", "all"), default="all",
                    help="--validate pair scope: all (scatter/maps, default) "
                         "or adjacent (bars/stacks/lines)")
    ap.add_argument("--as-text", action="store_true",
                    help="--validate against muriel's 8:1 text floor instead "
                         "of the 3:1 mark floor (use when slots render as type)")
    ap.add_argument("--selftest", action="store_true",
                    help="run generate_for_floor() + validate() invariant checks")
    args = ap.parse_args(argv)

    if args.selftest:
        _selftest()
        print("muriel.palettes: selftest passed")
        return 0

    if args.validate or args.named:
        if args.named:
            colors, label = palette(args.named), args.named
        else:
            colors = [c.strip() for c in args.validate.split(",") if c.strip()]
            label = "palette"
        report = validate(colors, bg=args.bg, pairs=args.pairs, as_text=args.as_text)
        glyph = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}
        role = "text (8:1)" if args.as_text else "marks (3:1)"
        print(f"\n{label} — {len(colors)} slots, {report.mode} surface "
              f"{args.bg}, {args.pairs} pairs, {role}")
        for c in report.checks:
            print(f"  [{glyph[c.status]:4}] {c.name:22} {c.detail}")
        print(f"\n  → {'ALL CHECKS PASS' if report.ok else 'FAILED — fix the marked checks'}")
        if report.warnings:
            print("  WARNs are conditional passes — each names a mandatory mitigation.")
        print("  scope: the palette against itself + its surface. For legibility "
              "of rendered text run `muriel contrast`.\n")
        return 0 if report.ok else 1

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
