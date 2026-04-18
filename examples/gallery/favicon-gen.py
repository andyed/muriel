"""
Generate muriel favicons from the colophon still.

Crops tight to the seven bars (no type), pads to square, downsizes to
standard favicon sizes (16, 32, 180 apple-touch, 512 maskable). Writes
both to docs/ (for the github pages site) and assets/ (canonical).

Runs against both light and dark variants so the favicon has light/dark
SVG twins if a `<link media="(prefers-color-scheme)">` path is desired.
"""

from pathlib import Path
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"

# ── Tight crop coordinates (hand-tuned for the 1200×630 colophon) ──
# The seven bars sit at roughly x=346..846, y=88..378 on both variants.
# We center the crop on that region and expand to square with a bit of
# breathing room.
BAR_LEFT, BAR_TOP, BAR_RIGHT, BAR_BOT = 346, 88, 846, 378
BAR_W = BAR_RIGHT - BAR_LEFT           # 500
BAR_H = BAR_BOT - BAR_TOP              # 290
SIDE = max(BAR_W, BAR_H) + 60          # 560 = bars + symmetric padding on all sides


def tight_crop_on_bg(img: Image.Image, bg_color: tuple) -> Image.Image:
    """
    Crop tight to the bars (no wordmark), then paste onto a square
    canvas of the source's own background color so the favicon has
    symmetric breathing room without pulling adjacent image content.
    """
    bars = img.crop((BAR_LEFT, BAR_TOP, BAR_RIGHT, BAR_BOT))
    canvas = Image.new("RGBA", (SIDE, SIDE), bg_color + (255,))
    # Center the bar crop on the square canvas
    paste_x = (SIDE - BAR_W) // 2
    paste_y = (SIDE - BAR_H) // 2
    canvas.paste(bars, (paste_x, paste_y))
    return canvas


def generate_sizes(src_path: Path, out_stem: Path, bg_color: tuple) -> None:
    """Resize the square-cropped bar region to favicon sizes."""
    img = Image.open(src_path).convert("RGBA")
    cropped = tight_crop_on_bg(img, bg_color)

    sizes = {
        "16":  cropped.resize((16, 16),   Image.Resampling.LANCZOS),
        "32":  cropped.resize((32, 32),   Image.Resampling.LANCZOS),
        "180": cropped.resize((180, 180), Image.Resampling.LANCZOS),
        "512": cropped.resize((512, 512), Image.Resampling.LANCZOS),
    }
    for name, im in sizes.items():
        out = out_stem.parent / f"{out_stem.stem}-{name}.png"
        im.save(out, "PNG", optimize=True)
        print(f"  → {out.relative_to(ROOT)}")


# ── Light (dark bars on cream) — default favicon for most browsers ──
print("Light favicon:")
generate_sizes(ASSETS / "logo-light.png", DOCS / "favicon", bg_color=(230, 228, 210))

# ── Dark (cream bars on near-black) — for prefers-color-scheme: dark ──
print("Dark favicon:")
generate_sizes(ASSETS / "logo-dark.png", DOCS / "favicon-dark", bg_color=(26, 22, 20))

# Canonical sizes also landed in assets/ for anyone importing the repo
# assets directly (GitHub repo icon, social previews, etc.).
for size in ("32", "180", "512"):
    for variant in ("light", "dark"):
        src = DOCS / f"favicon{'-dark' if variant == 'dark' else ''}-{size}.png"
        dst = ASSETS / f"favicon-{variant}-{size}.png"
        dst.write_bytes(src.read_bytes())

print("\nalso mirrored to assets/favicon-{light,dark}-{32,180,512}.png")
