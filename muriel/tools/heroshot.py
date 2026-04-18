"""
muriel.tools.heroshot — tilted, bordered, shadowed hero-shot compositor.

Takes a screenshot (or any PNG/JPG), applies a brand-aware hero treatment:
perspective tilt, brand-colored border, drop shadow, composed onto a
brand-background canvas sized to any ``muriel.dimensions`` named tier.

The canonical "marketing hero" operation muriel's raster channel needed
— Pillow-only, no numpy, no external dependencies beyond Pillow itself
(which is already raster-channel optional).

Usage (programmatic)
--------------------

::

    from muriel.tools.heroshot import tilt_and_frame
    from muriel.styleguide import load_styleguide

    brand = load_styleguide("examples/muriel-brand.toml")
    tilt_and_frame(
        "screenshot.png", "hero.png",
        tilt_deg=8,          # +right / -left perspective
        border_width=10,     # px, brand-colored
        brand=brand,         # pulls background + decorative color
        target="twitter.instream",   # muriel.dimensions named tier
    )

Usage (CLI)
-----------

::

    python -m muriel.tools.heroshot input.png output.png
    python -m muriel.tools.heroshot input.png hero.png --tilt 12 --border 8 \\
        --brand examples/muriel-brand.toml --target og.card

Dependencies
------------

Pillow only. The perspective solve is implemented in pure Python via
Gaussian elimination, so no numpy / scipy / OpenCV required.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Union

__all__ = ["tilt_and_frame"]


# ─── Color helpers ───────────────────────────────────────────────────

def _hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    s = hex_str.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


# ─── Geometry: perspective coefficients via pure-Python Gaussian elimination ──

def _solve_perspective(
    target: list[Tuple[float, float]],
    source: list[Tuple[float, float]],
) -> Tuple[float, ...]:
    """
    Solve for the 8 coefficients of a perspective transform mapping
    ``target`` quadrilateral to ``source`` quadrilateral.

    PIL's ``Image.transform`` with ``Image.PERSPECTIVE`` is backwards:
    it expects the coefficients that map *output* pixels to *input*
    pixels. So we pass the output quad as ``target`` and input as
    ``source``; the returned coefficients go straight into PIL.

    Each pair ``(tx, ty) -> (sx, sy)`` yields two equations:
        sx = (a*tx + b*ty + c) / (g*tx + h*ty + 1)
        sy = (d*tx + e*ty + f) / (g*tx + h*ty + 1)
    Rearranged to linear form:
        a*tx + b*ty + c - g*sx*tx - h*sx*ty = sx
        d*tx + e*ty + f - g*sy*tx - h*sy*ty = sy
    Four pairs → 8 equations → unique solution for (a..h).
    """
    matrix = []
    for (tx, ty), (sx, sy) in zip(target, source):
        matrix.append([tx, ty, 1, 0, 0, 0, -sx * tx, -sx * ty, sx])
        matrix.append([0, 0, 0, tx, ty, 1, -sy * tx, -sy * ty, sy])

    # Gaussian elimination with partial pivoting
    n = 8
    for i in range(n):
        # Pivot
        pivot = max(range(i, n), key=lambda k: abs(matrix[k][i]))
        matrix[i], matrix[pivot] = matrix[pivot], matrix[i]
        piv_val = matrix[i][i]
        if piv_val == 0:
            raise ValueError("Perspective solve failed — degenerate geometry")
        # Normalize
        matrix[i] = [x / piv_val for x in matrix[i]]
        # Eliminate
        for j in range(n):
            if j == i:
                continue
            factor = matrix[j][i]
            matrix[j] = [matrix[j][k] - factor * matrix[i][k] for k in range(n + 1)]

    return tuple(row[-1] for row in matrix)


def _perspective_tilt(img, deg: float):
    """
    Apply a perspective tilt around the vertical axis.

    Positive ``deg`` recedes the right side (tilt left-to-right).
    Negative ``deg`` recedes the left side.
    """
    from PIL import Image  # lazy import — Pillow is optional at module level

    if abs(deg) < 0.1:
        return img

    w, h = img.size
    shrink = abs(deg) / 90.0 * 0.35  # 0..0.35 fractional shrink on the far edge
    dy = int(h * shrink / 2)

    if deg > 0:
        # Right side recedes inward
        source = [(0, 0), (w, 0), (w, h), (0, h)]
        target = [(0, 0), (w, dy), (w, h - dy), (0, h)]
    else:
        source = [(0, 0), (w, 0), (w, h), (0, h)]
        target = [(0, dy), (w, 0), (w, h), (0, h - dy)]

    coeffs = _solve_perspective(target, source)
    return img.transform(
        img.size,
        Image.PERSPECTIVE,
        coeffs,
        resample=Image.Resampling.BICUBIC,
    )


# ─── Layer builders ──────────────────────────────────────────────────

def _add_border(img, width: int, color: Tuple[int, int, int]):
    """Inset the image inside a solid color border."""
    from PIL import Image

    if width <= 0:
        return img
    w, h = img.size
    new = Image.new("RGBA", (w + 2 * width, h + 2 * width), color + (255,))
    new.paste(img, (width, width), img if img.mode == "RGBA" else None)
    return new


def _make_shadow(img, blur: int, alpha: int):
    """Blurred dark shadow matched to the image's alpha channel."""
    from PIL import Image, ImageFilter

    if img.mode != "RGBA":
        mask = Image.new("L", img.size, 255)
    else:
        mask = img.split()[3]

    shadow_rgba = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dark = Image.new("RGBA", img.size, (0, 0, 0, alpha))
    shadow_rgba.paste(dark, (0, 0), mask)
    return shadow_rgba.filter(ImageFilter.GaussianBlur(blur))


# ─── Main entry point ────────────────────────────────────────────────

def tilt_and_frame(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    tilt_deg: float = 8.0,
    border_width: int = 10,
    border_color: Optional[Tuple[int, int, int]] = None,
    shadow: bool = True,
    shadow_blur: int = 28,
    shadow_alpha: int = 150,
    shadow_offset: Tuple[int, int] = (0, 18),
    background_color: Optional[Tuple[int, int, int]] = None,
    brand=None,
    target: Optional[str] = None,
    padding_frac: float = 0.18,
) -> str:
    """
    Tilt + border + shadow, composed onto a brand-background canvas.

    Parameters
    ----------
    input_path : str | Path
        Source image. Any format Pillow can open.
    output_path : str | Path
        Where to write the finished PNG.
    tilt_deg : float
        Perspective tilt in degrees. Positive recedes the right side;
        negative recedes the left. Typical range: ``-15 .. +15``.
    border_width : int
        Inset border thickness in pixels.
    border_color : (R, G, B), optional
        Override the brand-derived border color.
    shadow : bool
        Draw a drop shadow under the tilted image.
    shadow_blur : int
        Gaussian blur radius for the shadow, pixels.
    shadow_alpha : int
        Shadow opacity, 0..255.
    shadow_offset : (x, y)
        Offset applied to the shadow relative to the image.
    background_color : (R, G, B), optional
        Canvas background. Defaults to the brand's background or
        muriel OLED near-black.
    brand : muriel.styleguide.StyleGuide, optional
        If provided, brand colors fill in: decorative/accent for the
        border, background for the canvas.
    target : str, optional
        A dotted-name tier from ``muriel.dimensions.REGISTRY``
        (e.g., ``"twitter.instream"``, ``"og.card"``). Sets canvas size.
        If omitted, canvas is sized to the tilted image plus padding.
    padding_frac : float
        If ``target`` is omitted, pad this fraction of the tilted image
        around it when sizing the canvas.

    Returns
    -------
    str
        The written ``output_path`` (for chaining).
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            "muriel.tools.heroshot requires Pillow. Install with 'pip install Pillow'."
        ) from exc

    # ── Resolve brand-driven defaults ─────────────────────────────────
    if brand is not None:
        if border_color is None:
            candidate = (
                brand.colors.resolve_alias("decorative")
                or brand.colors.accent_decorative
                or brand.colors.accent
                or brand.colors.foreground
            )
            border_color = _hex_to_rgb(candidate)
        if background_color is None:
            background_color = _hex_to_rgb(brand.colors.background)

    if border_color is None:
        border_color = (230, 228, 210)  # muriel cream default
    if background_color is None:
        background_color = (10, 10, 15)  # muriel OLED near-black

    # ── Load + transform ─────────────────────────────────────────────
    src = Image.open(str(input_path)).convert("RGBA")
    bordered = _add_border(src, border_width, border_color)
    tilted = _perspective_tilt(bordered, tilt_deg)

    # ── Canvas sizing ────────────────────────────────────────────────
    if target is not None:
        from muriel.dimensions import lookup

        size = lookup(target)
        cw, ch = size.width, size.height
    else:
        cw = int(tilted.width * (1 + 2 * padding_frac))
        ch = int(tilted.height * (1 + 2 * padding_frac))

    canvas = Image.new("RGB", (cw, ch), background_color)

    # ── Fit tilted image into canvas (scale down if it overflows) ────
    fit = min(cw / tilted.width, ch / tilted.height, 1.0) * (1 - padding_frac)
    if fit < 1.0:
        tw, th = int(tilted.width * fit), int(tilted.height * fit)
        tilted = tilted.resize((tw, th), Image.Resampling.LANCZOS)

    x = (cw - tilted.width) // 2
    y = (ch - tilted.height) // 2

    # ── Shadow + image ───────────────────────────────────────────────
    if shadow:
        sh = _make_shadow(tilted, blur=shadow_blur, alpha=shadow_alpha)
        canvas.paste(sh, (x + shadow_offset[0], y + shadow_offset[1]), sh)

    canvas.paste(tilted, (x, y), tilted)

    # ── Save ─────────────────────────────────────────────────────────
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(output_path), "PNG", optimize=True)
    return str(output_path)


# ─── CLI ────────────────────────────────────────────────────────────

def _main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m muriel.tools.heroshot",
        description="Tilted, bordered, shadowed hero-shot compositor.",
    )
    ap.add_argument("input", help="Source image path")
    ap.add_argument("output", help="Output PNG path")
    ap.add_argument("--tilt", type=float, default=8.0, help="Perspective tilt in degrees (default 8)")
    ap.add_argument("--border", type=int, default=10, help="Border width in pixels (default 10)")
    ap.add_argument("--border-color", help="Override border color (hex, e.g. #50b4c8)")
    ap.add_argument("--no-shadow", action="store_true", help="Disable drop shadow")
    ap.add_argument("--brand", help="Path to a brand.toml (muriel.styleguide format)")
    ap.add_argument("--target", help="muriel.dimensions named tier (e.g. twitter.instream, og.card)")
    ap.add_argument("--bg", help="Override background color (hex)")
    args = ap.parse_args(argv)

    brand = None
    if args.brand:
        from muriel.styleguide import load_styleguide

        brand = load_styleguide(args.brand)

    border_color = _hex_to_rgb(args.border_color) if args.border_color else None
    background_color = _hex_to_rgb(args.bg) if args.bg else None

    out = tilt_and_frame(
        args.input,
        args.output,
        tilt_deg=args.tilt,
        border_width=args.border,
        border_color=border_color,
        shadow=not args.no_shadow,
        background_color=background_color,
        brand=brand,
        target=args.target,
    )
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
