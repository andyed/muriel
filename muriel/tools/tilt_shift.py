"""
muriel.tools.tilt_shift — fake-lens tilt-shift blur for product shots.

Tilt-shift lenses produce a narrow depth-of-field band; applied to a
product screenshot, the effect sells the "photographed, not captured"
illusion that pairs with CSS 3D transforms in the marketing-hero
pipeline.

The algorithm:

1. Gaussian-blur the whole image with a strength-controlled radius.
2. Build a radial-falloff mask centered at the focus point (L-mode,
   255 at focus → 0 at the edges), with an ease-out falloff.
3. Composite original onto blurred through the mask — sharp at the
   focus, increasingly blurred toward the periphery.
4. Optionally add film-grain noise (0.5–1%) to prevent banding in
   large smooth regions.

Pillow-only. No numpy.

Usage
-----

::

    from muriel.tools.tilt_shift import tilt_shift
    tilt_shift(
        "raw-capture.png", "hero-tilt-shifted.png",
        focus=(0.5, 0.45),   # normalized (x, y) — 0..1
        radius=0.42,          # size of the in-focus region
        strength=0.6,         # blur amount — 0..1
        noise=0.008,          # film-grain, 0..0.03
    )

Or chain with :func:`muriel.capture.capture_with_transform` for the full
"URL → tilted capture → tilt-shift → ship" pipeline.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Tuple, Union

__all__ = ["tilt_shift"]


def _radial_mask(size: Tuple[int, int], focus: Tuple[float, float], radius: float):
    """
    Build an L-mode mask: 255 at focus, 0 at edges, smooth ease-out falloff.
    Radius is fractional — 0.42 means the sharp region covers ~42% of
    the smaller image dimension before the falloff starts.
    """
    from PIL import Image, ImageDraw, ImageFilter

    w, h = size
    cx = int(focus[0] * w)
    cy = int(focus[1] * h)

    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)

    # Outer radius: ellipse that fully encloses the image from the focus
    # plus a little extra so the gradient reaches the corners.
    outer = int(max(w, h) * (1.0 + radius))
    steps = 48

    for i in range(steps):
        # Ease-in-out: alpha grows slowly at first, steeply near center
        t = (steps - i) / steps  # 1.0 → 0.0
        # Shift origin so `radius` fraction is fully opaque
        if t > (1.0 - radius):
            alpha = 255
        else:
            # Remaining range (0 .. 1-radius) ease-out to 255
            norm = t / max(1e-6, 1.0 - radius)  # 0 → 1 as we approach center
            alpha = int(255 * (norm ** 2.2))   # slight ease-in
        r = int(outer * t)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha)

    # Smooth the stepped banding with a mild blur on the mask itself
    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(w, h) / 80))
    return mask


def _add_noise(img, amount: float):
    """Add Gaussian-ish noise without numpy. amount is 0..1, typical 0.005..0.02."""
    from PIL import Image, ImageChops

    if amount <= 0:
        return img

    # Build a noise layer per channel: L-mode random, shifted to zero-centered
    w, h = img.size
    span = int(255 * amount * 2)  # total spread in [-amount*255, +amount*255]
    noise_bytes = bytes(random.randint(0, span) for _ in range(w * h))
    noise_l = Image.frombytes("L", (w, h), noise_bytes)

    # Shift to zero-centered by subtracting span/2 via ImageChops
    offset = Image.new("L", (w, h), span // 2)
    # (noise_l - offset) clipped → signed-ish contribution
    noise_pos = ImageChops.subtract(noise_l, offset, scale=1.0, offset=0)
    noise_neg = ImageChops.subtract(offset, noise_l, scale=1.0, offset=0)

    # Convert L noise into RGB so it can be added to the image
    noise_pos_rgb = Image.merge("RGB", [noise_pos] * 3)
    noise_neg_rgb = Image.merge("RGB", [noise_neg] * 3)

    base = img.convert("RGB")
    result = ImageChops.add(base, noise_pos_rgb, scale=1.0, offset=0)
    result = ImageChops.subtract(result, noise_neg_rgb, scale=1.0, offset=0)
    return result


def tilt_shift(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    focus: Tuple[float, float] = (0.5, 0.45),
    radius: float = 0.42,
    strength: float = 0.6,
    noise: float = 0.008,
) -> str:
    """
    Apply a tilt-shift depth-of-field effect to a PNG/JPG.

    Parameters
    ----------
    input_path : str | Path
        Source image (typically a capture_with_transform output).
    output_path : str | Path
        Where to write the result.
    focus : (x, y)
        Focus point, normalized to 0..1. Default ``(0.5, 0.45)`` —
        slightly above vertical center, matching how photographers
        compose tilted product shots.
    radius : float
        Size of the in-focus region as a fraction of the smaller image
        dimension. Default 0.42. Larger → more of the image sharp.
    strength : float
        Blur amount, 0..1. Default 0.6. Applied as Gaussian radius =
        ``strength * min(w, h) / 10``.
    noise : float
        Optional film-grain, 0..0.03. Default 0.008. Set to 0 to skip.

    Returns
    -------
    str
        The written output path.
    """
    try:
        from PIL import Image, ImageFilter
    except ImportError as exc:
        raise ImportError(
            "muriel.tools.tilt_shift requires Pillow. Install with 'pip install Pillow'."
        ) from exc

    src = Image.open(str(input_path)).convert("RGB")

    # Blur radius
    blur_r = max(1.0, strength * min(src.size) / 10)
    blurred = src.filter(ImageFilter.GaussianBlur(radius=blur_r))

    # Radial mask
    mask = _radial_mask(src.size, focus, radius)

    # Composite: 255-region = original (sharp), 0-region = blurred
    composed = Image.composite(src, blurred, mask)

    # Optional noise
    if noise > 0:
        composed = _add_noise(composed, noise)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    composed.save(str(output_path), "PNG", optimize=True)
    return str(output_path)


# ─── CLI ─────────────────────────────────────────────────────────────

def _main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m muriel.tools.tilt_shift",
        description="Fake-lens tilt-shift blur for product-screenshot heroes.",
    )
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--focus-x", type=float, default=0.5, help="Focus X, 0..1 (default 0.5)")
    ap.add_argument("--focus-y", type=float, default=0.45, help="Focus Y, 0..1 (default 0.45)")
    ap.add_argument("--radius", type=float, default=0.42, help="In-focus region size (default 0.42)")
    ap.add_argument("--strength", type=float, default=0.6, help="Blur strength (default 0.6)")
    ap.add_argument("--noise", type=float, default=0.008, help="Film-grain (default 0.008, 0 to disable)")
    args = ap.parse_args(argv)

    out = tilt_shift(
        args.input, args.output,
        focus=(args.focus_x, args.focus_y),
        radius=args.radius,
        strength=args.strength,
        noise=args.noise,
    )
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
