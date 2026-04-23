"""
muriel.oklch — OKLCH / OKLab color-space helpers.

Standard-library-only module for converting between sRGB and OKLCH
(Ottosson 2020, CSS Color Module Level 4), parsing CSS ``oklch()``
syntax, checking whether an OKLCH color falls inside the sRGB gamut,
and clamping out-of-gamut colors by reducing chroma while preserving
lightness and hue.

Scope covers (a) parse, (b) convert, (c) gamut — palette generation and
OKLCH-based contrast are separate follow-ups.

Math reference: Björn Ottosson, "A perceptual color space for image
processing" (2020). Matrix constants match the reference implementation
and the CSS Color 4 spec.

Usage
-----

Programmatic:

.. code-block:: python

    from muriel.oklch import (
        rgb_to_oklch, oklch_to_rgb, parse_oklch, format_oklch,
        in_srgb_gamut, clamp_to_srgb, Oklch,
    )

    rgb_to_oklch((230, 228, 210))             # → Oklch(L=0.906, C=0.020, h=95.8)
    parse_oklch("oklch(62% 0.15 258)")        # → Oklch(L=0.62, C=0.15, h=258.0)
    oklch_to_rgb(Oklch(0.62, 0.15, 258))      # → (86, 139, 202)
    in_srgb_gamut(Oklch(0.7, 0.3, 30))        # → False (too saturated for sRGB)
    clamp_to_srgb(Oklch(0.7, 0.3, 30))        # → Oklch(L=0.7, C=0.185…, h=30.0)

CLI:

.. code-block:: bash

    python -m muriel.oklch "#e6e4d2"
    python -m muriel.oklch "oklch(70% 0.18 30)"
    python -m muriel.oklch "oklch(70% 0.30 30)" --clamp

Any input form accepted by ``muriel.contrast.parse_color`` works as a
CLI argument — hex, ``rgb()``, named color, or ``oklch()``.

Integration
-----------

``muriel.contrast.parse_color`` transparently accepts ``oklch(...)``
syntax (lazy-imports this module), so every existing contrast helper
— ``contrast_ratio``, ``check_text_pair``, ``audit_svg`` — handles
OKLCH fills without changes. Contrast itself is still computed via
WCAG relative luminance in sRGB; OKLCH is only used for the parse
path.

Limitations
-----------

- sRGB gamut only. Display-P3 / Rec.2020 gamut checks are not
  implemented.
- Chroma clamp uses bisection (simple, preserves L and h). This is the
  naïve approach, not the CSS Color 4 "MINDE" gamut-mapping algorithm.
  For most brand palettes the visual difference is negligible.
- CSS ``none`` keyword and ``alpha`` channel are accepted by the parser
  but discarded (alpha ignored, ``none`` treated as 0).
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass
from typing import Optional, Sequence

__all__ = [
    "Oklch",
    "rgb_to_oklch",
    "oklch_to_rgb",
    "oklch_to_rgb_float",
    "parse_oklch",
    "format_oklch",
    "in_srgb_gamut",
    "clamp_to_srgb",
]


# ─── Matrix constants (Ottosson 2020 / CSS Color 4) ───────────────────

# linear sRGB → LMS
_M1 = (
    (0.4122214708, 0.5363325363, 0.0514459929),
    (0.2119034982, 0.6806995451, 0.1073969566),
    (0.0883024619, 0.2817188376, 0.6299787005),
)

# LMS' (cube-rooted) → OKLab
_M2 = (
    (0.2104542553,  0.7936177850, -0.0040720468),
    (1.9779984951, -2.4285922050,  0.4505937099),
    (0.0259040371,  0.7827717662, -0.8086757660),
)

# LMS → linear sRGB
_M1_INV = (
    ( 4.0767416621, -3.3077115913,  0.2309699292),
    (-1.2684380046,  2.6097574011, -0.3413193965),
    (-0.0041960863, -0.7034186147,  1.7076147010),
)

# OKLab → LMS' (cube-rooted)
_M2_INV = (
    (1.0,  0.3963377774,  0.2158037573),
    (1.0, -0.1055613458, -0.0638541728),
    (1.0, -0.0894841775, -1.2914855480),
)

# Float slop around gamut boundaries. A linear-RGB channel within this
# of [0, 1] is treated as in-gamut; the subsequent int rounding absorbs
# the difference.
_GAMUT_EPS = 1e-4


# ─── Internal linear algebra helpers ──────────────────────────────────

def _mat3_mul(
    m: tuple[tuple[float, float, float], ...],
    v: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


def _srgb_to_linear(c: float) -> float:
    # sRGB gamma decode. IEC 61966-2-1 transfer function.
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1 / 2.4)) - 0.055


def _cbrt_signed(x: float) -> float:
    # Real cube root that works for negatives — the sign of LMS can go
    # negative for colors well outside sRGB, and Python's ** operator
    # raises on fractional powers of negatives.
    return math.copysign(abs(x) ** (1.0 / 3.0), x)


# ─── Public dataclass ────────────────────────────────────────────────

@dataclass(frozen=True)
class Oklch:
    """
    OKLCH coordinate. ``L`` in [0, 1] (0 = black, 1 = white). ``C`` in
    [0, ~0.4] (saturation). ``h`` in degrees [0, 360).
    """
    L: float
    C: float
    h: float

    def __iter__(self):
        return iter((self.L, self.C, self.h))

    def replace(self, *, L: Optional[float] = None,
                C: Optional[float] = None,
                h: Optional[float] = None) -> "Oklch":
        return Oklch(
            L if L is not None else self.L,
            C if C is not None else self.C,
            h if h is not None else self.h,
        )


# ─── Core conversion ─────────────────────────────────────────────────

def rgb_to_oklch(rgb: Sequence[int]) -> Oklch:
    """
    Convert an sRGB color (0–255 per channel) to OKLCH.
    """
    r_lin = _srgb_to_linear(rgb[0] / 255.0)
    g_lin = _srgb_to_linear(rgb[1] / 255.0)
    b_lin = _srgb_to_linear(rgb[2] / 255.0)
    lms = _mat3_mul(_M1, (r_lin, g_lin, b_lin))
    lms_ = (_cbrt_signed(lms[0]), _cbrt_signed(lms[1]), _cbrt_signed(lms[2]))
    L, a, b = _mat3_mul(_M2, lms_)
    C = math.hypot(a, b)
    # Below this threshold the hue angle is numerically meaningless
    # (the color is on the achromatic axis, and atan2 of float-noise
    # components rotates randomly). Pin to 0 for stability.
    if C < 1e-7:
        h = 0.0
    else:
        h = math.degrees(math.atan2(b, a))
        if h < 0:
            h += 360.0
    return Oklch(L, C, h)


def _oklch_to_linear_rgb(
    oklch: Oklch,
) -> tuple[float, float, float]:
    """OKLCH → linear sRGB. Channels may fall outside [0, 1]."""
    h_rad = math.radians(oklch.h)
    a = oklch.C * math.cos(h_rad)
    b = oklch.C * math.sin(h_rad)
    lms_ = _mat3_mul(_M2_INV, (oklch.L, a, b))
    lms = (lms_[0] ** 3, lms_[1] ** 3, lms_[2] ** 3)
    return _mat3_mul(_M1_INV, lms)


def oklch_to_rgb_float(oklch: Oklch) -> tuple[float, float, float]:
    """
    OKLCH → sRGB float (0–1 per channel, gamma-encoded, un-clamped).

    Channels outside [0, 1] indicate out-of-gamut. Use
    :func:`in_srgb_gamut` to test and :func:`clamp_to_srgb` to fix.
    """
    lin = _oklch_to_linear_rgb(oklch)
    return (
        _linear_to_srgb(lin[0]),
        _linear_to_srgb(lin[1]),
        _linear_to_srgb(lin[2]),
    )


def oklch_to_rgb(oklch: Oklch) -> tuple[int, int, int]:
    """
    OKLCH → sRGB (0–255, clamped). Lossy for out-of-gamut inputs: the
    hard channel clip can shift hue. Prefer :func:`clamp_to_srgb` first
    if preserving hue matters.
    """
    srgb = oklch_to_rgb_float(oklch)
    return (
        max(0, min(255, round(srgb[0] * 255))),
        max(0, min(255, round(srgb[1] * 255))),
        max(0, min(255, round(srgb[2] * 255))),
    )


# ─── Gamut ───────────────────────────────────────────────────────────

def in_srgb_gamut(oklch: Oklch) -> bool:
    """True iff the OKLCH color falls inside the sRGB gamut."""
    lin = _oklch_to_linear_rgb(oklch)
    return all(-_GAMUT_EPS <= c <= 1.0 + _GAMUT_EPS for c in lin)


def clamp_to_srgb(oklch: Oklch, max_iter: int = 24) -> Oklch:
    """
    If ``oklch`` is outside the sRGB gamut, reduce chroma via bisection
    until it fits, preserving L and h. Returns the original unchanged
    if it already fits.

    ``max_iter`` controls precision (24 iterations ≈ 2⁻²⁴ ≈ 6e-8 on C).
    """
    if in_srgb_gamut(oklch):
        return oklch
    lo, hi = 0.0, oklch.C
    best = Oklch(oklch.L, 0.0, oklch.h)
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        trial = Oklch(oklch.L, mid, oklch.h)
        if in_srgb_gamut(trial):
            best = trial
            lo = mid
        else:
            hi = mid
    return best


# ─── CSS oklch() parser ──────────────────────────────────────────────

# Tolerant grammar: whitespace-separated per CSS Color 4, or commas for
# legacy input. Alpha is accepted and ignored.
_OKLCH_RE = re.compile(
    r"""^\s*oklch\(\s*
        (?P<L>[-+]?(?:\d+\.?\d*|\.\d+)%?|none)
        \s*[,\s]\s*
        (?P<C>[-+]?(?:\d+\.?\d*|\.\d+)%?|none)
        \s*[,\s]\s*
        (?P<h>[-+]?(?:\d+\.?\d*|\.\d+)(?:deg|rad|grad|turn)?|none)
        (?:\s*/\s*[-+]?(?:\d+\.?\d*|\.\d+)%?)?
        \s*\)\s*$""",
    re.IGNORECASE | re.VERBOSE,
)


def _parse_L_token(s: str) -> float:
    s = s.strip().lower()
    if s == "none":
        return 0.0
    if s.endswith("%"):
        return float(s[:-1]) / 100.0
    # CSS spec: a bare number for L in oklch() is 0..1. Some authors
    # write 0..100 thinking in Lab conventions; if the number is > 1.5
    # we assume that mistake and scale.
    v = float(s)
    if v > 1.5:
        v = v / 100.0
    return v


def _parse_C_token(s: str) -> float:
    s = s.strip().lower()
    if s == "none":
        return 0.0
    if s.endswith("%"):
        # CSS Color 4: 100% chroma in oklch() maps to 0.4.
        return float(s[:-1]) / 100.0 * 0.4
    return float(s)


def _parse_h_token(s: str) -> float:
    s = s.strip().lower()
    if s == "none":
        return 0.0
    if s.endswith("deg"):
        return float(s[:-3])
    if s.endswith("rad"):
        return math.degrees(float(s[:-3]))
    if s.endswith("grad"):
        return float(s[:-4]) * 360.0 / 400.0
    if s.endswith("turn"):
        return float(s[:-4]) * 360.0
    return float(s)


def parse_oklch(value: str) -> Oklch:
    """
    Parse a CSS ``oklch()`` string. Accepts the full CSS Color 4
    grammar (whitespace-separated components, optional ``/ alpha``,
    percentages for L and C, angle units for h, the ``none`` keyword).
    Alpha is accepted but discarded.
    """
    m = _OKLCH_RE.match(value)
    if not m:
        raise ValueError(f"invalid oklch() syntax: {value!r}")
    L = _parse_L_token(m.group("L"))
    C = _parse_C_token(m.group("C"))
    h = _parse_h_token(m.group("h")) % 360.0
    return Oklch(L, C, h)


def format_oklch(
    oklch: Oklch,
    *,
    percent_L: bool = True,
    l_precision: int = 1,
    c_precision: int = 4,
    h_precision: int = 2,
) -> str:
    """
    Format an OKLCH value as a CSS ``oklch()`` string. Defaults match
    the shape most tools emit (``oklch(62.0% 0.1500 258.00)``).
    """
    if percent_L:
        L_str = f"{oklch.L * 100:.{l_precision}f}%"
    else:
        L_str = f"{oklch.L:.{l_precision + 3}f}"
    return f"oklch({L_str} {oklch.C:.{c_precision}f} {oklch.h:.{h_precision}f})"


# ─── CLI ─────────────────────────────────────────────────────────────

def _format_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _describe(color_str: str, clamp: bool) -> int:
    # Branch by input form. If the user typed oklch(...) we want to
    # inspect the parsed value *before* clamping, so gamut status and
    # ΔC are meaningful. For other forms (hex / rgb() / named) we route
    # through contrast.parse_color and derive OKLCH from the sRGB —
    # those are always in-gamut by construction.
    s = color_str.strip()
    is_oklch_input = s[:6].lower() == "oklch("

    if is_oklch_input:
        try:
            oklch = parse_oklch(s)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        in_gamut = in_srgb_gamut(oklch)
        display_rgb = oklch_to_rgb(clamp_to_srgb(oklch) if not in_gamut else oklch)
    else:
        from muriel.contrast import parse_color
        try:
            rgb = parse_color(s)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if rgb is None:
            print(
                f"error: {color_str!r} is transparent / unresolvable",
                file=sys.stderr,
            )
            return 2
        oklch = rgb_to_oklch(rgb)
        in_gamut = True  # sRGB input → always in gamut
        display_rgb = rgb

    print(f"input      : {color_str}")
    print(f"sRGB hex   : {_format_hex(display_rgb)}")
    print(f"sRGB rgb   : rgb({display_rgb[0]}, {display_rgb[1]}, {display_rgb[2]})")
    print(f"OKLCH      : {format_oklch(oklch)}")
    print(f"in sRGB?   : {'yes' if in_gamut else 'no'}")

    if is_oklch_input and not in_gamut and clamp:
        clamped = clamp_to_srgb(oklch)
        clamped_rgb = oklch_to_rgb(clamped)
        print(f"clamped    : {format_oklch(clamped)}")
        print(f"clamped hex: {_format_hex(clamped_rgb)}")
        print(f"ΔC         : {oklch.C - clamped.C:.4f}")
    return 0


def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m muriel.oklch",
        description=(
            "Convert a color between sRGB and OKLCH, report gamut, "
            "optionally clamp out-of-gamut OKLCH to sRGB."
        ),
    )
    parser.add_argument(
        "color", nargs="+",
        help="Color(s) to inspect. Hex, rgb(), named, or oklch().",
    )
    parser.add_argument(
        "--clamp", action="store_true",
        help="If an input is outside sRGB, print the chroma-clamped result.",
    )
    args = parser.parse_args(argv)

    exit_code = 0
    for i, color in enumerate(args.color):
        if i:
            print()
        rc = _describe(color, clamp=args.clamp)
        if rc:
            exit_code = rc
    return exit_code


if __name__ == "__main__":
    raise SystemExit(_main())
