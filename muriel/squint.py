"""
muriel.squint — the blur ladder behind the Squinter jury seat.

Emits a progressive Gaussian-blur ladder plus the thumbnail companions
from a single input image, so a critic can judge what survives
degradation instead of judging a sharp render it already understands.

Created because "the hierarchy is clear" is unfalsifiable at full
resolution. A reader who knows the layout supplies the ranking the
pixels do not carry: they read the title first because they know it is
the title, not because it dominates. Blur removes that. At heavy blur
only the focal point should remain; at light blur, focal plus secondary
structure. If the reading order recovered under blur does not match the
intended one, the hierarchy failed — however clean the sharp render is.

Blur is scaled to the image, never fixed. A fixed 20 px radius erases a
400 px sprite entirely and leaves a 3000 px poster essentially sharp, so
the same command would answer a different question on every artifact.
Every level here is a fraction of the long edge, which makes the check
scale-invariant and the result comparable across artifacts.

The ladder
----------

Sigma as a fraction of the **larger** image dimension:

- ``light``  = 1.5%  — glyph detail gone; label groups and chart series
  still separate from each other.
- ``medium`` = 3.0%  — component-scale blocks begin merging into their
  neighbours.
- ``heavy``  = 5.0%  — only panel-scale masses survive. This is the
  level the Squinter seat grades focal dominance against.
- ``luma``   — the heavy level again with color discarded. Separates
  "reads as dominant" from "is merely saturated"; hue carries no
  luminance weight once it is gone.

Sigma is floored at 1.0 px so the filter is never a no-op on small
inputs.

Why those numbers
-----------------

The ladder thresholds **focal mass fraction** — the share of the frame a
mass occupies — because mass fraction is what the seat grades. Each
level is therefore specified by the mass size it half-erases, and the
sigma is derived from that, not the other way round.

Measured against Pillow's ``GaussianBlur`` (12.1.0), an isolated feature
of width ``d`` retains half its contrast at ``d = 2.14 * sigma``, a
quarter at ``1.40 * sigma``, a tenth at ``0.84 * sigma``. Across sigma
14, 28, 42 and 70 px the half-contrast ratio measured 2.11, 2.13, 2.18
and 2.16 — within 2% of its mean — so a single constant carries the
whole ladder: ``HALF_SURVIVAL_K``, rounded to 2.1. See
``survival_width``.

Half-survival width per level, as a fraction of the long edge:
3.15% / 6.3% / 10.5%. On a 1400 px frame that is 44 / 88 / 147 px — a
label group, a card block, a small panel. ``--json`` reports the same
three numbers per level as ``half_survival_px``, so a ballot can cite
the threshold it was actually judged under.

Body text is below all three by construction: 16 px on a 1400 px frame
is 1.1% of the long edge, which ``light`` takes to 0.09 retention. Text
legibility is not this seat's question and no level preserves it.

An earlier ladder ran 0.6 / 1.2 / 2.0%, putting heavy's half-survival
width at 59 px. Measured on that ladder, a 200 px card came through
``heavy`` at 1.00 retention — untouched. Block-composed artifacts, the
case this module exists to judge, then rendered as one picture at all
three levels: Pearson r between ``light`` and ``heavy`` was 0.87 on a
nine-tile grid and 0.98 on a single-focal-mass layout, a 0.11 spread.
The current ladder separates that pair 0.61 vs 0.96, a 0.34 spread.
``tests/test_squint.py`` pins the spread; a ladder that cannot tell a
grid from a hierarchy is not doing the seat's work.

Transparency has no luminance, so an alpha channel is composited onto an
explicit matte (default: muriel's OLED near-black) and the matte is
recorded. Do not leave it implied — figure/ground is exactly what this
tool is measuring. Palette images carry transparency in a ``tRNS`` chunk
rather than in a band, so modes ``P`` and ``PA`` are promoted to RGBA
before compositing; without that promotion a transparent pixel resolves
to whatever palette entry sits at its index, and figure/ground is
decided by an arbitrary color.

Determinism
-----------

No RNG. Fixed resampling filters (LANCZOS down, NEAREST for the
inspection zoom). Sigma rounded to 3 decimals before it reaches the
filter. Same input plus same matte gives byte-identical outputs.

Usage
-----

Programmatic:

.. code-block:: python

    from muriel.squint import squint, blur_sigma, ladder_sigmas

    blur_sigma(1400, "heavy")      # → 70.0
    ladder_sigmas(1400)            # → {'light': 21.0, 'medium': 42.0, …}
    survival_width(1400, "heavy")  # → 147.0  (masses narrower are halved)
    result = squint("render_assets/panel.png")
    result.paths["heavy"]          # → Path(…/squint/panel.squint-heavy.png)

CLI:

.. code-block:: bash

    python -m muriel.squint render_assets/panel.png
    python -m muriel.squint panel.png --out-dir /tmp/squint
    python -m muriel.squint panel.png --matte '#ffffff'
    python -m muriel.squint panel.png --json

Exit status:
    0 = ladder written
    3 = usage error (file not found, unreadable, bad matte)
    4 = Pillow missing — install the ``[raster]`` extra

Limitations
-----------

- Raster in, raster out. Rasterize SVG upstream (``cairosvg``) first.
- Judges luminance masses, not text. Contrast ratios belong to
  ``muriel.contrast``; this module deliberately reports none.
- Pillow's ``GaussianBlur`` is a three-pass box approximation, so the
  kernel is close to but not exactly Gaussian. Cost is independent of
  sigma, which is why the heavy level is cheap on large posters.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence, Union

__all__ = [
    "LADDER",
    "HALF_SURVIVAL_K",
    "MIN_SIGMA_PX",
    "THUMB_DIVISOR",
    "FAVICON_EDGE_PX",
    "FAVICON_ZOOM",
    "DEFAULT_MATTE",
    "LEVELS",
    "blur_sigma",
    "ladder_sigmas",
    "survival_width",
    "scaled_size",
    "thumb_size",
    "favicon_size",
    "output_paths",
    "SquintResult",
    "squint",
]

# ─── Ladder constants ────────────────────────────────────────────────────

#: Blur sigma as a fraction of the image's larger dimension. Derived in
#: the module docstring from the half-survival widths the seat grades
#: against: 3.15% / 6.3% / 10.5% of the long edge, divided by
#: ``HALF_SURVIVAL_K``. Change the widths, not these, and recompute.
LADDER: dict[str, float] = {
    "light":  0.015,
    "medium": 0.030,
    "heavy":  0.050,
}

#: Feature width, in units of sigma, at which Pillow's GaussianBlur
#: leaves half the original contrast. Measured on Pillow 12.1.0 at sigma
#: 14/28/42/70 px: 2.11, 2.13, 2.18, 2.16 — mean 2.14, within 2%. This
#: is the constant that turns a mass-fraction target into a sigma, so it
#: is the number to re-measure if the Pillow filter implementation
#: changes. ``tests/test_squint.py`` re-measures it on every run.
HALF_SURVIVAL_K: float = 2.1

#: Sigma floor. Below ~1 px a Gaussian is a no-op and the level lies.
MIN_SIGMA_PX: float = 1.0

#: The Thumbnail seat's first lens: 1/8 scale.
THUMB_DIVISOR: int = 8

#: The Thumbnail seat's second lens: favicon edge.
FAVICON_EDGE_PX: int = 16

#: Nearest-neighbour magnification applied to the 16 px render so a
#: reader can actually inspect it. The pixels are unchanged; only the
#: viewer's resampling is taken out of the loop.
FAVICON_ZOOM: int = 8

#: Matte for images with an alpha channel. muriel's OLED near-black.
DEFAULT_MATTE: str = "#0a0a0f"

#: Emitted levels, in the order the ladder is written and printed.
#: The Squinter reads these heaviest-first; the order here is
#: presentation order, not reading order.
LEVELS: tuple[str, ...] = (
    "light", "medium", "heavy", "luma", "eighth", "px16", "px16_zoom",
)

_FILE_SUFFIX: dict[str, str] = {
    "light":     "squint-light",
    "medium":    "squint-medium",
    "heavy":     "squint-heavy",
    "luma":      "squint-luma",
    "eighth":    "thumb-eighth",
    "px16":      "thumb-16px",
    "px16_zoom": "thumb-16px-zoom",
}

def _blur_label(level: str, tail: str) -> str:
    """Label a blur level by the mass fraction it half-erases, not by
    its sigma. The fraction is the seat's actual threshold."""
    pct = LADDER[level] * HALF_SURVIVAL_K * 100
    return f"gaussian, halves masses under {pct:.3g}% of frame — {tail}"


_LEVEL_LABEL: dict[str, str] = {
    "light":     _blur_label("light", "label groups still separate"),
    "medium":    _blur_label("medium", "component blocks merging"),
    "heavy":     _blur_label("heavy", "focal mass only"),
    "luma":      "heavy blur, color discarded",
    "eighth":    f"downscale 1/{THUMB_DIVISOR}",
    "px16":      f"downscale to {FAVICON_EDGE_PX} px long edge",
    "px16_zoom": f"{FAVICON_EDGE_PX} px render, {FAVICON_ZOOM}× nearest-neighbour",
}


# ─── Pure geometry / ladder math (no Pillow) ─────────────────────────────

def blur_sigma(long_edge: int, level: str) -> float:
    """
    Gaussian sigma in pixels for one ladder level on an image whose
    larger dimension is ``long_edge``.

    Scales with the image so the check asks the same question of a
    400 px sprite and a 3000 px poster. Floored at ``MIN_SIGMA_PX``.
    Rounded to 3 decimals so the value that reaches the filter is
    stable across platforms.

    Raises ``ValueError`` on an unknown level or a non-positive edge.
    """
    if level not in LADDER:
        raise ValueError(
            f"unknown blur level {level!r}; expected one of {sorted(LADDER)}"
        )
    if long_edge <= 0:
        raise ValueError(f"long_edge must be positive, got {long_edge!r}")
    return round(max(MIN_SIGMA_PX, LADDER[level] * long_edge), 3)


def ladder_sigmas(long_edge: int) -> dict[str, float]:
    """Every blur level's sigma for an image with this larger dimension."""
    return {level: blur_sigma(long_edge, level) for level in LADDER}


def survival_width(long_edge: int, level: str) -> float:
    """
    Feature width in pixels at which this level halves contrast.

    Anything narrower than the returned width is more than half gone at
    that level; anything much wider comes through intact. This is the
    number the seat is actually thresholding on, so report it rather
    than the sigma when explaining why a mass did or did not survive.
    """
    return round(HALF_SURVIVAL_K * blur_sigma(long_edge, level), 3)


def scaled_size(width: int, height: int, target_long_edge: int) -> tuple[int, int]:
    """
    Resize ``(width, height)`` so its larger dimension becomes
    ``target_long_edge``, preserving aspect ratio. Neither dimension is
    ever allowed to round to zero.
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"dimensions must be positive, got {width}×{height}")
    if target_long_edge <= 0:
        raise ValueError(f"target_long_edge must be positive, got {target_long_edge}")
    long_edge = max(width, height)
    scale = target_long_edge / long_edge
    # int(x + 0.5) rather than round() — half-up, no banker's rounding,
    # so the size is the same number on every implementation.
    return (
        max(1, int(width * scale + 0.5)),
        max(1, int(height * scale + 0.5)),
    )


def thumb_size(width: int, height: int, divisor: int = THUMB_DIVISOR) -> tuple[int, int]:
    """Size of the 1/``divisor``-scale thumbnail companion."""
    if divisor <= 0:
        raise ValueError(f"divisor must be positive, got {divisor}")
    target = max(1, int(max(width, height) / divisor + 0.5))
    return scaled_size(width, height, target)


def favicon_size(width: int, height: int, edge: int = FAVICON_EDGE_PX) -> tuple[int, int]:
    """Size of the favicon-scale companion — long edge pinned to ``edge``."""
    return scaled_size(width, height, edge)


def output_paths(
    image_path: Union[str, Path],
    out_dir: Optional[Union[str, Path]] = None,
) -> dict[str, Path]:
    """
    Absolute output path per level. Explicit export paths are a muriel
    reproducibility requirement, so this is a pure function you can call
    (and assert against) before anything is written.

    ``out_dir`` defaults to a ``squint/`` directory beside the input.
    """
    src = Path(image_path).expanduser().resolve()
    target = (
        Path(out_dir).expanduser().resolve()
        if out_dir is not None
        else src.parent / "squint"
    )
    return {
        level: target / f"{src.stem}.{_FILE_SUFFIX[level]}.png"
        for level in LEVELS
    }


# ─── Result ──────────────────────────────────────────────────────────────

@dataclass
class SquintResult:
    """What one squint run produced. ``paths`` is keyed by level."""
    source: Path
    width: int
    height: int
    matte: tuple[int, int, int]
    sigmas: dict[str, float]
    paths: dict[str, Path]
    sizes: dict[str, tuple[int, int]] = field(default_factory=dict)

    @property
    def long_edge(self) -> int:
        return max(self.width, self.height)

    @property
    def matte_hex(self) -> str:
        r, g, b = self.matte
        return f"#{r:02x}{g:02x}{b:02x}"

    def to_dict(self) -> dict:
        """JSON-serializable manifest — what the ``--json`` flag prints."""
        return {
            "source": str(self.source),
            "width": self.width,
            "height": self.height,
            "long_edge": self.long_edge,
            "matte": self.matte_hex,
            "levels": [
                {
                    "level": level,
                    "transform": _LEVEL_LABEL[level],
                    "sigma_px": self.sigmas.get(level),
                    # The threshold the seat grades against: masses
                    # narrower than this keep under half their contrast.
                    "half_survival_px": (
                        round(HALF_SURVIVAL_K * self.sigmas[level], 3)
                        if level in self.sigmas else None
                    ),
                    "width": self.sizes[level][0],
                    "height": self.sizes[level][1],
                    "path": str(self.paths[level]),
                }
                for level in LEVELS
            ],
        }


# ─── Lazy backends ───────────────────────────────────────────────────────

def _require_pillow():
    """
    Import Pillow on demand. Pillow ships in muriel's optional
    ``[raster]`` extra so a bare install stays dependency-free; the
    error names the extra rather than leaving the caller to guess.
    """
    try:
        from PIL import Image, ImageFilter
    except ImportError as exc:
        raise ImportError(
            "muriel.squint requires Pillow, which ships in muriel's optional "
            "raster extra. Install it with:  pip install 'muriel[raster]'  "
            "(or: pip install Pillow)"
        ) from exc
    return Image, ImageFilter


def _resolve_matte(value: Union[str, Sequence[int]]) -> tuple[int, int, int]:
    """Parse a matte color through muriel.contrast (lazy; stdlib-only module)."""
    from muriel.contrast import parse_color

    rgb = parse_color(value)
    if rgb is None:
        raise ValueError(f"matte must be an opaque color, got {value!r}")
    return rgb


# ─── The ladder ──────────────────────────────────────────────────────────

def squint(
    image_path: Union[str, Path],
    out_dir: Optional[Union[str, Path]] = None,
    *,
    matte: Union[str, Sequence[int]] = DEFAULT_MATTE,
) -> SquintResult:
    """
    Write the blur ladder and thumbnail companions for one image.

    Parameters
    ----------
    image_path
        Source raster (PNG / JPG / anything Pillow opens). Rasterize SVG
        upstream.
    out_dir
        Where the ladder lands. Defaults to ``squint/`` beside the input.
    matte
        Color composited under any alpha channel. Recorded in the result
        because it decides figure/ground.

    Returns
    -------
    SquintResult
        Source dimensions, per-level sigmas, per-level output paths.

    Raises
    ------
    ImportError
        Pillow not installed — the message names the ``[raster]`` extra.
    FileNotFoundError
        Source image missing.
    """
    Image, ImageFilter = _require_pillow()

    src_path = Path(image_path).expanduser().resolve()
    if not src_path.exists():
        raise FileNotFoundError(f"no such image: {src_path}")

    matte_rgb = _resolve_matte(matte)

    src = Image.open(str(src_path))
    # getbands() alone is not a transparency test. Palette images report
    # ('P',) and carry their transparency in a tRNS chunk under
    # info['transparency'], so an "A" check misses them entirely and
    # convert("RGB") then resolves every transparent pixel to whichever
    # palette entry sits at that index — figure/ground decided by an
    # arbitrary color while the result still records a matte. Small UI
    # exports are routinely mode P. Promote to RGBA first, then composite.
    if src.mode in ("P", "PA") or "transparency" in src.info:
        src = src.convert("RGBA")
    if "A" in src.getbands():
        rgba = src.convert("RGBA")
        flat = Image.new("RGB", rgba.size, matte_rgb)
        flat.paste(rgba, (0, 0), rgba)
        src = flat
    else:
        src = src.convert("RGB")

    width, height = src.size
    long_edge = max(width, height)
    sigmas = ladder_sigmas(long_edge)
    paths = output_paths(src_path, out_dir)
    paths[next(iter(paths))].parent.mkdir(parents=True, exist_ok=True)

    sizes: dict[str, tuple[int, int]] = {}

    blurred: dict[str, "Image.Image"] = {}
    for level in ("light", "medium", "heavy"):
        img = src.filter(ImageFilter.GaussianBlur(radius=sigmas[level]))
        blurred[level] = img
        img.save(str(paths[level]), "PNG", optimize=True)
        sizes[level] = img.size

    # Luminance-only pass on the heavy level: strips hue so a saturated
    # element cannot pose as a dominant one.
    luma = blurred["heavy"].convert("L")
    luma.save(str(paths["luma"]), "PNG", optimize=True)
    sizes["luma"] = luma.size

    eighth = src.resize(thumb_size(width, height), Image.Resampling.LANCZOS)
    eighth.save(str(paths["eighth"]), "PNG", optimize=True)
    sizes["eighth"] = eighth.size

    px16 = src.resize(favicon_size(width, height), Image.Resampling.LANCZOS)
    px16.save(str(paths["px16"]), "PNG", optimize=True)
    sizes["px16"] = px16.size

    # Nearest-neighbour so the zoom shows the 16 px pixels themselves and
    # not a viewer's guess at what sits between them.
    zoom = px16.resize(
        (px16.width * FAVICON_ZOOM, px16.height * FAVICON_ZOOM),
        Image.Resampling.NEAREST,
    )
    zoom.save(str(paths["px16_zoom"]), "PNG", optimize=True)
    sizes["px16_zoom"] = zoom.size

    return SquintResult(
        source=src_path,
        width=width,
        height=height,
        matte=matte_rgb,
        sigmas=sigmas,
        paths=paths,
        sizes=sizes,
    )


# ─── Pretty printer ──────────────────────────────────────────────────────

def _print_ladder(result: SquintResult) -> None:
    print(f"\nSquint ladder: {result.source}")
    print(f"  source:    {result.width} × {result.height} px "
          f"(long edge {result.long_edge})")
    print(f"  matte:     {result.matte_hex}")
    print(f"  out dir:   {result.paths[LEVELS[0]].parent}")
    halves = "  ".join(
        f"{level} {HALF_SURVIVAL_K * result.sigmas[level]:.0f}px"
        for level in LADDER
    )
    print(f"  halves at: {halves}   (mass width losing half its contrast)")
    print()
    headers = ("Level",  "Sigma",  "Size",     "Transform")
    widths  = (10,       10,       12,         46)
    print("  " + "  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  " + "  ".join("─" * w for w in widths))
    for level in LEVELS:
        sigma = result.sigmas.get(level)
        sigma_str = f"{sigma:.1f}px" if sigma is not None else "—"
        w, h = result.sizes[level]
        print(
            "  "
            + level.ljust(widths[0])
            + "  " + sigma_str.ljust(widths[1])
            + "  " + f"{w}×{h}".ljust(widths[2])
            + "  " + _LEVEL_LABEL[level]
        )
    print()
    print("  paths:")
    for level in LEVELS:
        print(f"    {level:<10} {result.paths[level]}")
    print()


# ─── CLI ─────────────────────────────────────────────────────────────────

def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m muriel.squint",
        description=(
            "Emit a dimension-scaled Gaussian blur ladder plus thumbnail "
            "companions, so hierarchy can be judged by what survives "
            "degradation."
        ),
    )
    parser.add_argument("image", type=Path, help="Source raster image.")
    parser.add_argument(
        "--out-dir", type=Path, default=None,
        help="Output directory (default: a squint/ directory beside the input).",
    )
    parser.add_argument(
        "--matte", type=str, default=DEFAULT_MATTE,
        help=f"Color composited under any alpha channel (default: {DEFAULT_MATTE}).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Print the manifest as JSON instead of a table.",
    )
    args = parser.parse_args(argv)

    if not args.image.exists():
        print(f"error: file not found: {args.image}", file=sys.stderr)
        return 3

    try:
        result = squint(args.image, args.out_dir, matte=args.matte)
    except ImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        _print_ladder(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
