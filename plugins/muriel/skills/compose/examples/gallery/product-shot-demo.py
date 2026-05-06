"""
Full product-shot pipeline demo:

  URL → capture_with_transform (CSS 3D tilt in the live DOM, retina)
      → tilt_shift (fake-lens depth of field)
      → PNG hero

Runs against the muriel landing page itself. Eats the dogfood.
"""

from pathlib import Path

from muriel.capture import capture_with_transform
from muriel.tools.tilt_shift import tilt_shift


ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "docs"

URL = "http://muriel.mindbendingpixels.com/"

# ── 1. Capture with the photo-3d preset (the Medium article's signature) ──

raw = capture_with_transform(
    URL,
    selector="#tuner",                  # the motion tuner — a UI-shaped block with sliders
    transform="preset:book",            # gentle rotateY(-15°); reads cleaner than iso-left for dark UI
    output=str(OUT / "product-shot-raw.png"),
    viewport=(1680, 1050),              # taller viewport so the tuner isn't cramped
    device_scale_factor=2,
    color_scheme="dark",
    settle_ms=600,
    crop_to_element=True,               # drop adjacent un-tilted sections
    crop_padding=120,
    verbose=True,
)

# ── 2. Tilt-shift for lens-like depth ─────────────────────────────────────

final = tilt_shift(
    raw,
    str(OUT / "product-shot-hero.png"),
    focus=(0.5, 0.55),         # focus slightly below center (where the bars are)
    radius=0.55,               # wide in-focus region so the whole tuner stays sharp
    strength=0.28,             # gentle blur — depth cue, not heavy bokeh
    noise=0.005,
)

print(f"\n  hero → {final}")
