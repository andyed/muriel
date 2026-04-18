#!/usr/bin/env python3
"""Typeset — Reusable text-on-image compositing for store assets.

Extracts the boilerplate from the typographer skill into importable functions.
Use standalone or via manifest-driven batch generation.

Usage:
    python typeset.py --manifest assets.json
    python typeset.py --template amazon-icon --text "My App" --bg screenshot.png --out icon.png

Or as a library:
    from typeset import find_font, render_asset
    render_asset("My App", template="amazon-icon", background="bg.png", output="icon.png")
"""

import json
import math
import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TEMPLATES_DIR = Path(__file__).parent / "templates"

# macOS font paths — checked in order, first match wins
FONT_PATHS = {
    "helvetica": {
        "regular": ("/System/Library/Fonts/Helvetica.ttc", 0),
        "bold": ("/System/Library/Fonts/Helvetica.ttc", 1),
        "light": ("/System/Library/Fonts/Helvetica.ttc", 2),
    },
    "futura": {
        "medium": ("/System/Library/Fonts/Supplemental/Futura.ttc", 0),
        "bold": ("/System/Library/Fonts/Supplemental/Futura.ttc", 1),
        "condensed": ("/System/Library/Fonts/Supplemental/Futura.ttc", 2),
    },
    "impact": {
        "regular": ("/System/Library/Fonts/Supplemental/Impact.ttf", None),
    },
    "arial": {
        "bold": ("/Library/Fonts/Arial Bold.ttf", None),
        "regular": ("/System/Library/Fonts/Supplemental/Arial.ttf", None),
    },
    "sf-compact": {
        "regular": ("/System/Library/Fonts/SFCompact.ttf", None),
    },
}


def find_font(family="helvetica", weight="bold", size=72):
    """Find a system font by family and weight, return a PIL ImageFont.

    Args:
        family: Font family name (helvetica, futura, impact, arial, sf-compact)
        weight: Weight variant (regular, bold, light, medium, condensed)
        size: Font size in pixels

    Returns:
        PIL ImageFont object

    Raises:
        FileNotFoundError if no matching font found
    """
    family = family.lower()
    weight = weight.lower()

    if family in FONT_PATHS and weight in FONT_PATHS[family]:
        path, index = FONT_PATHS[family][weight]
        if os.path.exists(path):
            if index is not None:
                return ImageFont.truetype(path, size, index=index)
            return ImageFont.truetype(path, size)

    # Fallback: try any weight in the requested family
    if family in FONT_PATHS:
        for w, (path, index) in FONT_PATHS[family].items():
            if os.path.exists(path):
                if index is not None:
                    return ImageFont.truetype(path, size, index=index)
                return ImageFont.truetype(path, size)

    # Last resort: try all families
    for fam in FONT_PATHS.values():
        for w, (path, index) in fam.items():
            if os.path.exists(path):
                if index is not None:
                    return ImageFont.truetype(path, size, index=index)
                return ImageFont.truetype(path, size)

    raise FileNotFoundError(f"No font found for {family}/{weight}")


def measure_text(text, font, max_width=None):
    """Measure text and optionally auto-shrink to fit max_width.

    Returns:
        (font, bbox) where font may be resized and bbox is (width, height)
    """
    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if max_width and text_w > max_width:
        scale = max_width / text_w
        new_size = max(12, int(font.size * scale))
        font = font.font_variant(size=new_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    return font, (text_w, text_h)


def luminance(rgb):
    """Calculate relative luminance per WCAG 2.1."""
    r, g, b = [c / 255.0 for c in rgb[:3]]
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def check_contrast(fg, bg):
    """Check WCAG contrast ratio between foreground and background colors.

    Args:
        fg: (r, g, b) foreground color
        bg: (r, g, b) background color

    Returns:
        (ratio, pass_aa, pass_aaa) — ratio as float, booleans for AA (4.5:1) and AAA (7:1)
    """
    l1, l2 = luminance(fg), luminance(bg)
    if l1 < l2:
        l1, l2 = l2, l1
    ratio = (l1 + 0.05) / (l2 + 0.05)
    return ratio, ratio >= 4.5, ratio >= 7.0


def render_text(draw, text, position, font, color=(255, 255, 255), effects=None):
    """Render text with optional glow and shadow effects.

    Args:
        draw: PIL ImageDraw object
        text: Text string to render
        position: (x, y) tuple
        font: PIL ImageFont object
        color: (r, g, b) text color
        effects: dict with optional keys:
            "glow": {"radius": int, "color": (r, g, b)}
            "shadow": {"offset": (dx, dy), "blur": int, "color": (r, g, b, a)}
    """
    x, y = position

    if effects:
        # Shadow with Gaussian blur
        if "shadow" in effects:
            s = effects["shadow"]
            dx, dy = s.get("offset", (3, 3))
            blur_radius = s.get("blur", 4)
            shadow_color = s.get("color", (0, 0, 0))

            # Render shadow on a separate layer for blur
            img = draw.im
            shadow_layer = Image.new("RGBA", (img.size[0], img.size[1]), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            shadow_draw.text((x + dx, y + dy), text, fill=shadow_color, font=font)
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
            # Composite shadow back — caller needs to handle this separately
            # For now, fall back to multi-offset approach
            for odx in range(-blur_radius, blur_radius + 1):
                for ody in range(-blur_radius, blur_radius + 1):
                    if odx == 0 and ody == 0:
                        continue
                    draw.text((x + dx + odx, y + dy + ody), text, fill=shadow_color, font=font)

        # Glow (multi-offset in a tint color)
        if "glow" in effects:
            g = effects["glow"]
            radius = g.get("radius", 2)
            glow_color = g.get("color", (80, 60, 120))
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x + dx, y + dy), text, fill=glow_color, font=font)

    # Main text
    draw.text((x, y), text, fill=color, font=font)


def apply_vignette(image, intensity=140):
    """Apply a radial darkening vignette for text readability.

    Args:
        image: PIL Image (RGB)
        intensity: Max darkness at center (0-255)

    Returns:
        New composited image
    """
    w, h = image.size
    overlay = Image.new("RGB", (w, h), (0, 0, 0))
    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = min(w, h) // 2
    for r in range(radius, 0, -1):
        alpha = int(intensity * (1 - r / radius))
        cx, cy = w // 2, h // 2
        mask_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha)
    return Image.composite(overlay, image, mask)


def load_template(name):
    """Load a template JSON file by name.

    Args:
        name: Template name (without .json extension)

    Returns:
        dict with template configuration
    """
    path = TEMPLATES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    with open(path) as f:
        return json.load(f)


def render_asset(text, *, template=None, template_data=None, background=None,
                 output="output.png", tagline=None, text_color=(230, 228, 210),
                 effects=None):
    """Render a complete store asset from a template.

    Args:
        text: Primary text (app name)
        template: Template name to load, or None if template_data provided
        template_data: Dict with template configuration (alternative to template name)
        background: Path to background image, or None for solid black
        output: Output file path
        tagline: Optional subtitle text
        text_color: (r, g, b) text color
        effects: Override effects dict, or None to use template defaults
    """
    tmpl = template_data or load_template(template)
    w, h = tmpl["width"], tmpl["height"]

    # Background
    if background and os.path.exists(background):
        bg = Image.open(background).convert("RGB")
        # Crop to aspect ratio, then resize
        bw, bh = bg.size
        target_ratio = w / h
        bg_ratio = bw / bh
        if bg_ratio > target_ratio:
            new_bw = int(bh * target_ratio)
            left = (bw - new_bw) // 2
            bg = bg.crop((left, 0, left + new_bw, bh))
        else:
            new_bh = int(bw / target_ratio)
            top = (bh - new_bh) // 2
            bg = bg.crop((0, top, bw, top + new_bh))
        bg = bg.resize((w, h), Image.LANCZOS)
    else:
        bg = Image.new("RGB", (w, h), (10, 10, 15))

    # Vignette
    if tmpl.get("bg_style") == "vignette":
        bg = apply_vignette(bg)

    # Text area
    ta = tmpl.get("text_area", {"x": 0.1, "y": 0.3, "w": 0.8, "h": 0.4})
    text_x = int(ta["x"] * w)
    text_max_w = int(ta["w"] * w)
    text_y = int(ta["y"] * h)

    # Font
    fd = tmpl.get("default_font", {"family": "helvetica", "weight": "bold", "size_ratio": 0.15})
    base_size = int(fd.get("size_ratio", 0.15) * h)
    font = find_font(fd.get("family", "helvetica"), fd.get("weight", "bold"), base_size)

    # Measure and auto-shrink
    font, (text_w, text_h) = measure_text(text, font, text_max_w)

    # Center in text area
    x = text_x + (text_max_w - text_w) // 2
    y = text_y

    # Effects
    if effects is None:
        tmpl_effects = tmpl.get("effects", [])
        effects = {}
        if "glow" in tmpl_effects:
            effects["glow"] = {"radius": 2, "color": (80, 60, 120)}
        if "shadow" in tmpl_effects:
            effects["shadow"] = {"offset": (3, 3), "blur": 4, "color": (0, 0, 0)}

    # Draw
    draw = ImageDraw.Draw(bg)
    render_text(draw, text, (x, y), font, text_color, effects)

    # Tagline
    if tagline:
        tag_size = max(16, base_size // 3)
        tag_font = find_font(fd.get("family", "helvetica"), "regular", tag_size)
        tag_font, (tw, th) = measure_text(tagline, tag_font, text_max_w)
        tx = text_x + (text_max_w - tw) // 2
        ty = y + text_h + int(tag_size * 0.5)
        render_text(draw, tagline, (tx, ty), tag_font, text_color, None)

    # Contrast check
    bg_sample = (10, 10, 15)
    ratio, aa, aaa = check_contrast(text_color, bg_sample)
    print(f"  {output}: {w}x{h}, contrast {ratio:.1f}:1 {'AA' if aa else 'FAIL'}")

    # Save
    fmt = tmpl.get("format", "PNG")
    if not tmpl.get("transparency", False) and bg.mode == "RGBA":
        bg = bg.convert("RGB")
    bg.save(output, fmt)
    return output


def generate_from_manifest(manifest_path):
    """Generate all assets defined in a manifest file.

    Args:
        manifest_path: Path to assets.json manifest

    Returns:
        List of output file paths
    """
    with open(manifest_path) as f:
        manifest = json.load(f)

    app_name = manifest["app_name"]
    tagline = manifest.get("tagline")
    background = manifest.get("background")
    brand = manifest.get("brand_colors", {})
    text_color = hex_to_rgb(brand.get("primary", "#e6e4d2"))

    outputs = []
    for target in manifest["targets"]:
        tmpl = load_template(target["template"])
        out = target["output"]
        out_dir = os.path.dirname(out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        result = render_asset(
            app_name,
            template_data=tmpl,
            background=background,
            output=out,
            tagline=tagline,
            text_color=text_color,
        )
        outputs.append(result)

    return outputs


def render_heatmap(fixations, *, background=None, canvas_size=(1280, 1024),
                   radius=40, blur=30, colormap="pink", desaturate=0.7,
                   output=None, bg_opacity=0.35):
    """Render a smooth gaussian density heatmap from fixation data.

    Args:
        fixations: list of dicts with 'x', 'y', and optionally 'd' (duration ms).
            Duration weights the density contribution of each fixation.
        background: path to background image, or PIL Image, or None for white.
        canvas_size: (width, height) of the output canvas.
        radius: base radius of each fixation blob in pixels.
        blur: gaussian blur radius applied to the density layer.
        colormap: color ramp name — "pink" (monochrome magenta like Tobii),
            "heat" (white→yellow→red→black), or (r,g,b) tuple for monochrome.
        desaturate: how much to desaturate the background (0=full color, 1=grayscale).
        output: path to save the image, or None to return without saving.
        bg_opacity: opacity of the background layer (0=invisible, 1=full).

    Returns:
        PIL Image (RGBA)
    """
    import numpy as np

    w, h = canvas_size

    # Build density with binned gaussian blobs for topographic feel.
    # Bin fixations into a coarse grid, then stamp large gaussians at each
    # bin center — produces discrete rounded peaks that merge where they
    # overlap, like contour islands on a topo map.
    bin_size = max(8, radius // 2)
    bins_y = (h + bin_size - 1) // bin_size
    bins_x = (w + bin_size - 1) // bin_size
    grid = np.zeros((bins_y, bins_x), dtype=np.float64)
    for f in fixations:
        bx = min(int(f['x']) // bin_size, bins_x - 1)
        by = min(int(f['y']) // bin_size, bins_y - 1)
        if 0 <= bx < bins_x and 0 <= by < bins_y:
            grid[by, bx] += f.get('d', 200) / 200.0

    density = np.zeros((h, w), dtype=np.float64)
    sigma = radius * 0.55
    for by in range(bins_y):
        for bx in range(bins_x):
            if grid[by, bx] == 0:
                continue
            cx = bx * bin_size + bin_size // 2
            cy = by * bin_size + bin_size // 2
            weight = grid[by, bx]
            r = int(radius * 1.8)
            y0, y1 = max(0, cy - r), min(h, cy + r)
            x0, x1 = max(0, cx - r), min(w, cx + r)
            if y0 >= y1 or x0 >= x1:
                continue
            yy, xx = np.mgrid[y0:y1, x0:x1]
            dist_sq = (xx - cx) ** 2 + (yy - cy) ** 2
            falloff = np.exp(-0.5 * dist_sq / (sigma * sigma))
            density[y0:y1, x0:x1] += weight * falloff

    if density.max() > 0:
        density /= density.max()

    # Single gentle blur to smooth bin edges without flattening peaks
    density_img = Image.fromarray((density * 255).astype(np.uint8), mode='L')
    density_img = density_img.filter(ImageFilter.GaussianBlur(blur))

    # Normalize after blur
    density_arr = np.array(density_img, dtype=np.float64) / 255.0
    dmax = density_arr.max()
    if dmax > 0:
        density_arr /= dmax

    # Contour banding: quantize density into discrete levels to create
    # visible topographic bands. Each band is a plateau — the transitions
    # between bands create the contour-line feel.
    n_bands = 8
    density_arr = np.floor(density_arr * n_bands) / n_bands
    # Re-smooth the staircase slightly so band edges are soft, not pixelated
    band_img = Image.fromarray((density_arr * 255).astype(np.uint8), mode='L')
    band_img = band_img.filter(ImageFilter.GaussianBlur(3))
    density_arr = np.array(band_img, dtype=np.float64) / 255.0
    dmax = density_arr.max()
    if dmax > 0:
        density_arr /= dmax

    # Apply colormap
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    if colormap == "pink":
        # Monochrome pink/magenta: transparent → light pink → hot pink → deep magenta
        # Apply gamma to increase contrast at peaks
        d_gamma = density_arr ** 0.7  # push midtones toward peaks
        for c in range(3):
            low = [255, 210, 240][c]   # very light pink at low density
            mid = [230, 60, 140][c]    # hot pink at medium density
            high = [180, 20, 80][c]    # deep magenta at peak
            rgba[:, :, c] = np.where(
                density_arr > 0.01,
                np.where(
                    d_gamma < 0.5,
                    (low + (mid - low) * d_gamma * 2).astype(np.uint8),
                    (mid + (high - mid) * (d_gamma - 0.5) * 2).astype(np.uint8),
                ),
                0
            )
        # Alpha: ramp up faster, saturate earlier
        rgba[:, :, 3] = np.where(
            density_arr > 0.01,
            np.minimum(240, (d_gamma * 300).astype(np.uint16)).astype(np.uint8),
            0
        )
    elif colormap == "heat":
        # Classic: transparent → yellow → red → dark red
        for c in range(3):
            if c == 0:  # R
                rgba[:, :, c] = np.minimum(255, (density_arr * 400)).astype(np.uint8)
            elif c == 1:  # G
                rgba[:, :, c] = np.where(
                    density_arr < 0.5,
                    (density_arr * 2 * 200).astype(np.uint8),
                    (200 * (1 - (density_arr - 0.5) * 2)).astype(np.uint8)
                )
            else:  # B
                rgba[:, :, c] = 0
        rgba[:, :, 3] = np.where(density_arr > 0.01, (density_arr * 200 + 30).clip(0, 220).astype(np.uint8), 0)
    elif isinstance(colormap, (tuple, list)) and len(colormap) == 3:
        # Monochrome with custom tint
        cr, cg, cb = colormap
        rgba[:, :, 0] = (density_arr * cr).astype(np.uint8)
        rgba[:, :, 1] = (density_arr * cg).astype(np.uint8)
        rgba[:, :, 2] = (density_arr * cb).astype(np.uint8)
        rgba[:, :, 3] = (density_arr * 220).astype(np.uint8)
    else:
        raise ValueError(f"Unknown colormap: {colormap}")

    heatmap_layer = Image.fromarray(rgba, mode='RGBA')

    # Background
    if background is None:
        bg = Image.new('RGBA', (w, h), (255, 255, 255, 255))
    elif isinstance(background, (str, Path)):
        bg = Image.open(str(background)).convert('RGBA')
        bg = bg.resize((w, h), Image.LANCZOS)
    elif isinstance(background, Image.Image):
        bg = background.convert('RGBA').resize((w, h), Image.LANCZOS)
    else:
        bg = Image.new('RGBA', (w, h), (255, 255, 255, 255))

    # Desaturate background
    if desaturate > 0:
        bg_rgb = bg.convert('RGB')
        gray = bg_rgb.convert('L').convert('RGB')
        bg_rgb = Image.blend(bg_rgb, gray, desaturate)
        bg = bg_rgb.convert('RGBA')
        # Apply bg_opacity
        bg_arr = np.array(bg)
        bg_arr[:, :, 3] = int(bg_opacity * 255)
        bg = Image.fromarray(bg_arr)

    # Composite: white base → desaturated bg → heatmap
    result = Image.new('RGBA', (w, h), (255, 255, 255, 255))
    result = Image.alpha_composite(result, bg)
    result = Image.alpha_composite(result, heatmap_layer)

    if output:
        result.convert('RGB').save(output)
        print(f"  heatmap: {output} ({w}x{h}, {len(fixations)} fixations, blur={blur})")

    return result


def hex_to_rgb(hex_color):
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="Typeset — store asset generator")
    parser.add_argument("--manifest", help="Path to assets.json manifest for batch generation")
    parser.add_argument("--template", help="Template name for single asset")
    parser.add_argument("--text", help="Primary text")
    parser.add_argument("--tagline", help="Subtitle text")
    parser.add_argument("--bg", help="Background image path")
    parser.add_argument("--out", default="output.png", help="Output file path")
    parser.add_argument("--color", default="#e6e4d2", help="Text color as hex")
    parser.add_argument("--list-templates", action="store_true", help="List available templates")

    args = parser.parse_args()

    if args.list_templates:
        if TEMPLATES_DIR.exists():
            for f in sorted(TEMPLATES_DIR.glob("*.json")):
                tmpl = json.load(open(f))
                print(f"  {f.stem:20s}  {tmpl['width']}x{tmpl['height']}  {tmpl.get('name', '')}")
        else:
            print("No templates directory found.")
        return

    if args.manifest:
        outputs = generate_from_manifest(args.manifest)
        print(f"\nGenerated {len(outputs)} assets.")
    elif args.template and args.text:
        render_asset(
            args.text,
            template=args.template,
            background=args.bg,
            output=args.out,
            tagline=args.tagline,
            text_color=hex_to_rgb(args.color),
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
