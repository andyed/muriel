"""
muriel.cvd — color-vision-deficiency simulation and perceptual separation.

Standard-library-only. Answers the question ``muriel.contrast`` cannot:
*two colors both clear the contrast floor against the background — but can
a red-green colorblind reader tell them apart from each other?*

``muriel.contrast`` measures each color against the **background** (WCAG
relative luminance). That is a legibility check, and it is blind to
palette collapse: ``#009E73`` and ``#D55E00`` both clear 8:1 on near-black
and are indistinguishable to nobody — but swap in two hues that happen to
converge under deuteranopia and contrast.py still reports two happy PASSes
while a deuteranope sees one color twice. This module measures colors
against **each other**, under simulated CVD.

Muriel previously delegated this to authority — "use Wong, it's
colorblind-safe, a reviewer expects the citation." That is true and it is
still the default (see :mod:`muriel.palettes`), but it does not extend to
brand palettes, ``generate_for_floor()`` output, or any hand-picked set. An
audit you cannot run on your own colors is a claim, not a check.

Simulation
----------

Machado, G. M., Oliveira, M. M., & Fernandes, L. A. F. (2009). "A
Physiologically-based Model for Simulation of Color Vision Deficiency."
*IEEE Transactions on Visualization and Computer Graphics* 15(6), 1291–1298.
https://doi.org/10.1109/TVCG.2009.113

The matrices below are the paper's severity-1.0 (dichromacy) transforms,
applied in **linear** RGB. Machado parameterises severity 0.0–1.0; muriel
implements the endpoint only — dichromacy is the conservative case, and a
palette that survives it survives the anomalous trichromacies above it.

Separation
----------

ΔE is CIE76 (Euclidean distance in CIELAB, D65). CIEDE2000 is the more
accurate metric for *near-threshold* judgements, but the thresholds here
(8 / 12) live well above threshold, where CIE76 is adequate and cheap —
and CIE76 is what the sibling validators report, so the numbers compare
directly across tools.

Thresholds
----------

- ``CVD_TARGET = 12.0`` — adjacent slots are comfortably distinct.
- ``CVD_FLOOR = 8.0`` — legal **only** with a second encoding channel
  (direct label, dash pattern, shape, texture, or a gap between marks).
  Color alone is not carrying identity at this separation.
- Below the floor — the palette collapses. Reorder or replace slots.

These match the bands used by Claude Code's bundled ``dataviz`` skill, so a
palette validated here reports the same ΔE there. Muriel's divergence is
about *floors*, not metrics — see :func:`muriel.palettes.validate`.

Usage
-----

.. code-block:: python

    from muriel.cvd import simulate, delta_e, min_separation

    simulate("#D55E00", "deutan")            # → (166, 137, 0)
    delta_e("#009E73", "#56B4E9", "deutan")  # → 48.9
    min_separation(["#4477AA", "#EE6677"], kind="deutan")

CLI:

    python -m muriel.cvd "#4477AA,#EE6677,#228833"     # separation matrix
    python -m muriel.cvd --palette wong                 # a named muriel palette
    python -m muriel.cvd "#a,#b" --pairs adjacent       # stacks / bars / lines

Cross-references: :mod:`muriel.palettes` (``validate()`` composes this with
the contrast + OKLCH checks), ``channels/charts.md`` (categorical palette
rules), ``channels/science.md`` (figure palettes).
"""

from __future__ import annotations

import math
from typing import Iterable, Optional, Sequence

__all__ = [
    "CVD_KINDS",
    "CVD_TARGET",
    "CVD_FLOOR",
    "simulate",
    "delta_e",
    "separation_matrix",
    "min_separation",
    "worst_separation",
    "Separation",
]


# ─── Thresholds ─────────────────────────────────────────────────────

CVD_TARGET = 12.0
"""ΔE at or above which two slots are comfortably distinct under CVD."""

CVD_FLOOR = 8.0
"""ΔE floor. Between FLOOR and TARGET a second encoding channel is mandatory."""

CVD_KINDS = ("protan", "deutan", "tritan")
"""The three dichromacies. ``protan`` ≈ 1% of males, ``deutan`` ≈ 6%, ``tritan`` < 0.01%."""


# ─── Machado et al. (2009) severity-1.0 transforms, linear RGB ──────

_MACHADO = {
    "protan": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deutan": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "tritan": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
}

# sRGB (D65) → CIEXYZ. IEC 61966-2-1.
_RGB_TO_XYZ = (
    (0.4124564, 0.3575761, 0.1804375),
    (0.2126729, 0.7151522, 0.0721750),
    (0.0193339, 0.1191920, 0.9503041),
)

# D65 reference white.
_WHITE_D65 = (0.95047, 1.00000, 1.08883)


# ─── Color conversion ───────────────────────────────────────────────


def _srgb_to_linear(c: float) -> float:
    """sRGB EOTF. ``c`` in [0, 1]."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    """Inverse sRGB EOTF, clamped to [0, 1]."""
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _to_linear_rgb(color) -> tuple[float, float, float]:
    """Parse any muriel color input to linear-RGB floats in [0, 1]."""
    from muriel.contrast import parse_color

    rgb = parse_color(color) if isinstance(color, str) else tuple(color)
    if rgb is None:
        raise ValueError(f"could not parse color {color!r}")
    return tuple(_srgb_to_linear(c / 255.0) for c in rgb)


def _mat3(m, v) -> tuple[float, float, float]:
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def _linear_rgb_to_lab(rgb_lin: Sequence[float]) -> tuple[float, float, float]:
    """Linear sRGB → CIELAB (D65)."""
    xyz = _mat3(_RGB_TO_XYZ, rgb_lin)

    def f(t: float) -> float:
        # CIE standard: cube root above the linear-segment break, affine below.
        return t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29

    fx, fy, fz = (f(xyz[i] / _WHITE_D65[i]) for i in range(3))
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


# ─── Public API ─────────────────────────────────────────────────────


def simulate(color, kind: str) -> tuple[int, int, int]:
    """Simulate ``color`` as seen with the ``kind`` dichromacy.

    Parameters
    ----------
    color
        Any input :func:`muriel.contrast.parse_color` accepts — hex string,
        ``rgb()`` string, named color, or an (R, G, B) 0–255 triple.
    kind
        One of :data:`CVD_KINDS` — ``'protan'``, ``'deutan'``, ``'tritan'``.

    Returns
    -------
    tuple[int, int, int]
        The simulated color as sRGB 0–255. Out-of-gamut results from the
        transform are clamped per channel.

    Example
    -------

    ::

        >>> from muriel.cvd import simulate
        >>> simulate("#D55E00", "deutan")   # vermillion, as a deuteranope sees it
        (166, 137, 0)
    """
    if kind not in _MACHADO:
        raise ValueError(f"kind must be one of {CVD_KINDS}; got {kind!r}")
    out_lin = _mat3(_MACHADO[kind], _to_linear_rgb(color))
    return tuple(round(_linear_to_srgb(c) * 255) for c in out_lin)


def delta_e(color_a, color_b, kind: Optional[str] = None) -> float:
    """CIE76 ΔE between two colors, optionally under simulated CVD.

    Parameters
    ----------
    color_a, color_b
        Any input :func:`muriel.contrast.parse_color` accepts.
    kind
        A member of :data:`CVD_KINDS` to compare *as simulated*, or
        ``None`` (default) for normal trichromatic vision.

    Returns
    -------
    float
        Euclidean distance in CIELAB. Compare against :data:`CVD_TARGET`
        (12.0) and :data:`CVD_FLOOR` (8.0).
    """
    if kind is not None:
        color_a, color_b = simulate(color_a, kind), simulate(color_b, kind)
    lab_a = _linear_rgb_to_lab(_to_linear_rgb(color_a))
    lab_b = _linear_rgb_to_lab(_to_linear_rgb(color_b))
    return math.dist(lab_a, lab_b)


class Separation:
    """The worst-separated pair in a palette under one vision kind.

    Attributes
    ----------
    delta : float
        The ΔE of the worst pair.
    kind : str or None
        Vision kind the worst pair was found under (``None`` = normal).
    color_a, color_b : str
        The two colors that collapse.
    index_a, index_b : int
        Their slot positions in the input palette.
    """

    __slots__ = ("delta", "kind", "color_a", "color_b", "index_a", "index_b")

    def __init__(self, delta, kind, color_a, color_b, index_a, index_b):
        self.delta = delta
        self.kind = kind
        self.color_a = color_a
        self.color_b = color_b
        self.index_a = index_a
        self.index_b = index_b

    @property
    def status(self) -> str:
        """``'pass'`` (≥ target), ``'floor'`` (≥ floor, needs 2nd channel), or ``'fail'``."""
        if self.delta >= CVD_TARGET:
            return "pass"
        return "floor" if self.delta >= CVD_FLOOR else "fail"

    def __repr__(self) -> str:
        kind = self.kind or "normal"
        return (
            f"Separation(ΔE={self.delta:.1f}, {kind}, "
            f"slot {self.index_a} {self.color_a} ↔ slot {self.index_b} {self.color_b}, "
            f"{self.status})"
        )


def _pair_indices(n: int, pairs: str) -> list[tuple[int, int]]:
    if pairs == "adjacent":
        return [(i, i + 1) for i in range(n - 1)]
    if pairs == "all":
        return [(i, j) for i in range(n) for j in range(i + 1, n)]
    raise ValueError(f"pairs must be 'adjacent' | 'all'; got {pairs!r}")


def separation_matrix(
    palette: Sequence[str],
    kind: Optional[str] = None,
    *,
    pairs: str = "all",
) -> list[tuple[int, int, float]]:
    """Every pair's ΔE as ``(index_a, index_b, delta)``, ascending by delta.

    ``pairs='adjacent'`` restricts to neighbouring slots — correct for bars,
    stacked segments, and lines, where slot assignment never skips. Use the
    ``'all'`` default for scatter, bubble, choropleth, and small multiples,
    where any two marks can land side by side.
    """
    out = [
        (i, j, delta_e(palette[i], palette[j], kind))
        for i, j in _pair_indices(len(palette), pairs)
    ]
    return sorted(out, key=lambda t: t[2])


def min_separation(
    palette: Sequence[str],
    kind: Optional[str] = None,
    *,
    pairs: str = "all",
) -> Optional[Separation]:
    """The worst-separated pair in ``palette`` under a single vision kind.

    ``kind=None`` (default) measures **normal trichromatic vision**, exactly
    as in :func:`delta_e`. To scan the deficiencies, pass a member of
    :data:`CVD_KINDS` — or use :func:`worst_separation`, which searches
    several kinds and returns the worst across all of them.

    Returns ``None`` for a palette of fewer than two colors.

    Example
    -------

    ::

        >>> from muriel.cvd import min_separation
        >>> min_separation(["#ff0000", "#00b400"], "deutan").status
        'fail'
    """
    if len(palette) < 2:
        return None
    # separation_matrix sorts ascending, so slot 0 is this kind's worst pair.
    i, j, d = separation_matrix(palette, kind, pairs=pairs)[0]
    return Separation(d, kind, palette[i], palette[j], i, j)


def worst_separation(
    palette: Sequence[str],
    kinds: Sequence[str] = ("protan", "deutan"),
    *,
    pairs: str = "all",
) -> Optional[Separation]:
    """The worst-separated pair across several vision kinds.

    Defaults to ``protan`` + ``deutan`` — the two red-green deficiencies that
    account for essentially all CVD in the population. ``tritan`` is rare
    (< 0.01%) and routinely drags the worst-pair number down without
    reflecting a real readership, so it is reported but not gated by default;
    pass it explicitly when the audience warrants it.

    This is the function to gate a palette on. Returns ``None`` for a palette
    of fewer than two colors.

    Example
    -------

    ::

        >>> from muriel.cvd import worst_separation
        >>> from muriel.palettes import WONG
        >>> worst_separation(WONG).status
        'pass'
    """
    if len(palette) < 2:
        return None
    worst: Optional[Separation] = None
    for k in kinds:
        found = min_separation(palette, k, pairs=pairs)
        if worst is None or found.delta < worst.delta:
            worst = found
    return worst


# ─── CLI ────────────────────────────────────────────────────────────


def _main(argv=None) -> int:
    """``python -m muriel.cvd "#hex,#hex,…" [--pairs adjacent] [--palette NAME]``."""
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m muriel.cvd",
        description="CVD separation report — can a colorblind reader tell "
                    "these colors apart from each other?",
    )
    ap.add_argument("palette", nargs="?", default=None,
                    help="comma-separated hex values, in slot order")
    ap.add_argument("--palette", dest="named", default=None, metavar="NAME",
                    help="a named muriel palette instead (wong, ibm, tol_bright, …)")
    ap.add_argument("--pairs", choices=("adjacent", "all"), default="all",
                    help="all: scatter/bubble/maps, any two marks can meet "
                         "(default). adjacent: bars/stacks/lines.")
    ap.add_argument("--selftest", action="store_true", help="run invariant checks")
    args = ap.parse_args(argv)

    if args.selftest:
        _selftest()
        print("muriel.cvd: selftest passed")
        return 0

    if args.named:
        from muriel.palettes import palette as named_palette
        colors = named_palette(args.named)
        label = args.named
    elif args.palette:
        colors = [c.strip() for c in args.palette.split(",") if c.strip()]
        label = "palette"
    else:
        ap.error("give a comma-separated hex list or --palette NAME")

    if len(colors) < 2:
        print("need at least 2 colors to measure separation")
        return 1

    print(f"\n{label} — {len(colors)} slots, {args.pairs} pairs")
    print(f"  target ΔE >= {CVD_TARGET}  ·  floor {CVD_FLOOR} "
          f"(2nd encoding channel mandatory below target)\n")

    glyph = {"pass": "PASS", "floor": "WARN", "fail": "FAIL"}
    overall_ok = True
    for kind in (None,) + CVD_KINDS:
        worst = min_separation(colors, kind, pairs=args.pairs)
        name = kind or "normal"
        # Normal vision and tritan are reported for context; protan + deutan gate.
        gates = kind in ("protan", "deutan")
        if gates and worst.status == "fail":
            overall_ok = False
        mark = glyph[worst.status] if gates else ""
        print(f"  [{mark:4}] {name:8} worst ΔE {worst.delta:5.1f}  "
              f"slot {worst.index_a} {worst.color_a} ↔ "
              f"slot {worst.index_b} {worst.color_b}")

    print(f"\n  → {'PASS' if overall_ok else 'FAILED — slots collapse under CVD'}"
          "   (protan + deutan gate; normal + tritan are context)")
    print("  scope: separation between colors. For legibility against the "
          "background run `muriel contrast`.\n")
    return 0 if overall_ok else 1


def _selftest() -> int:
    """Invariant checks for the CVD transforms and ΔE."""
    # Identity: a color is zero distance from itself, under any vision kind.
    for kind in (None,) + CVD_KINDS:
        assert delta_e("#D55E00", "#D55E00", kind) < 1e-9

    # Symmetry.
    assert abs(delta_e("#000000", "#ffffff") - delta_e("#ffffff", "#000000")) < 1e-9

    # Black and white are unmoved by any CVD transform (achromatic anchors).
    for kind in CVD_KINDS:
        assert simulate("#000000", kind) == (0, 0, 0)
        r, g, b = simulate("#ffffff", kind)
        assert all(c >= 253 for c in (r, g, b)), f"white shifted under {kind}"

    # CIE76 sanity: black↔white ΔE is L* range = 100.
    assert abs(delta_e("#000000", "#ffffff") - 100.0) < 0.5

    # The check earns its keep: a red-green pair that reads fine to a
    # trichromat must collapse under deuteranopia. This is the exact failure
    # muriel.contrast cannot see — both clear 8:1 on near-black.
    red, green = "#ff0000", "#00b400"
    assert delta_e(red, green) > 60, "control: distinct to normal vision"
    assert delta_e(red, green, "deutan") < 30, "should collapse for a deuteranope"

    # kind=None means normal vision in BOTH delta_e and min_separation. Guard the
    # overload that once made the CLI print deutan's number under "normal".
    normal = min_separation(["#56B4E9", "#009E73"])
    assert normal.kind is None
    assert abs(normal.delta - delta_e("#56B4E9", "#009E73")) < 1e-9
    assert normal.delta > min_separation(["#56B4E9", "#009E73"], "deutan").delta

    # Wong is the reference colorblind-safe palette — it must clear the floor.
    from muriel.palettes import WONG
    worst = worst_separation(WONG)
    assert worst is not None and worst.status != "fail", f"Wong regressed: {worst}"
    assert worst.kind in ("protan", "deutan")

    # Parse-equivalence: hex string and RGB triple agree.
    assert abs(delta_e("#4477AA", (238, 102, 119))
               - delta_e((68, 119, 170), "#EE6677")) < 1e-9

    # Degenerate palettes.
    assert min_separation(["#ffffff"]) is None
    assert min_separation([]) is None

    # Adjacent vs all: adjacent is a subset, so its worst is never worse.
    p = ["#4477AA", "#EE6677", "#228833", "#CCBB44"]
    assert (min_separation(p, "deutan", pairs="adjacent").delta
            >= min_separation(p, "deutan", pairs="all").delta - 1e-9)

    # worst_separation never reports better than any kind it searched.
    w = worst_separation(p)
    for k in ("protan", "deutan"):
        assert w.delta <= min_separation(p, k).delta + 1e-9

    # Degenerate palettes, multi-kind path.
    assert worst_separation(["#ffffff"]) is None

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
