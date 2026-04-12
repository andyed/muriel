# Raster — Pillow + typeset.py

PNG/JPG compositing via Python/Pillow for store assets, icons, banners, wordmarks, screenshots, and any bitmap output. Primary tool: `~/Documents/dev/ascii-charts/typeset.py`. Falls back to inline Pillow code for custom layouts.

Part of the [Render](../render.md) skill — see the top-level index for mission, universal rules, and channel map.

## Capabilities

- Render text onto background images or solid colors
- Multiple text layers with independent sizing, positioning, color
- Glow/shadow effects for readability on busy backgrounds
- Center darkening vignette for text contrast
- Output at exact pixel dimensions required by stores
- Batch generation for multiple sizes from one design
- Contrast verification (WCAG AA minimum, 8:1 preferred)

## Available Fonts (macOS)

Check these paths in order, use first available:
```python
FONT_PATHS = [
    '/System/Library/Fonts/Helvetica.ttc',
    '/System/Library/Fonts/SFCompact.ttf',
    '/Library/Fonts/Arial Bold.ttf',
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    '/System/Library/Fonts/Supplemental/Futura.ttc',
    '/System/Library/Fonts/Supplemental/Impact.ttf',
]
```

For font index in .ttc files (multiple fonts in one file), use `ImageFont.truetype(path, size, index=N)`:
- Helvetica.ttc: 0=Regular, 1=Bold, 2=Light, 3=Oblique, 4=BoldOblique
- Futura.ttc: 0=Medium, 1=Bold, 2=CondensedMedium, 3=CondensedExtraBold

**Always use full file paths.** Named fonts (e.g., `"Arial"`) don't resolve on macOS. Same applies to ImageMagick — use `magick` not `convert`, always with full TTF paths.

## Common Store Dimensions

### Amazon Appstore (Fire TV)
| Asset | Size | Format |
|-------|------|--------|
| App icon | 1280x720 | PNG, no transparency |
| Screenshots | 1920x1080 | JPG/PNG, landscape |
| Background | 1920x1080 | JPG/PNG, no transparency |
| Featured logo | 640x260 | PNG, transparency OK |
| Featured bg | 1920x720 | JPG/PNG, no transparency |
| Small icon | 114x114 | PNG |
| Large icon | 512x512 | PNG |

### Apple tvOS App Store
| Asset | Size | Format |
|-------|------|--------|
| App icon | 1280x768 | PNG, layered |
| Top shelf | 2320x720 or 1920x720 | PNG |
| Screenshots | 1920x1080 or 3840x2160 | PNG/JPG |

### Google Play Store
| Asset | Size | Format |
|-------|------|--------|
| Feature graphic | 1024x500 | PNG/JPG |
| App icon | 512x512 | PNG |
| Screenshots | 1920x1080 | PNG/JPG |

## Reusable Module

**`~/Documents/dev/ascii-charts/typeset.py`** extracts the boilerplate below into importable functions. Prefer using it over inline scripts:

```python
from typeset import find_font, render_asset, generate_from_manifest

# Single asset
render_asset("My App", template="amazon-icon", background="bg.png", output="icon.png", tagline="Subtitle")

# Batch from manifest
generate_from_manifest("assets.json")
```

CLI: `python3 typeset.py --manifest assets.json` or `python3 typeset.py --template amazon-icon --text "App Name" --out icon.png`

Available templates: `amazon-icon` (1280x720), `amazon-small-icon` (512x512), `tvos-topshelf` (2320x720), `play-feature` (1024x500). List with `--list-templates`.

For custom layouts that don't fit a template, fall back to the inline pattern below.

## Implementation Pattern (inline fallback)

Use this Python/Pillow pattern when templates don't fit:

```python
from PIL import Image, ImageDraw, ImageFont
import os, math

# 1. Load or create background
bg = Image.open('background.png').convert('RGB')  # RGB for no-transparency requirements

# 2. Crop/resize to target dimensions
w, h = bg.size
sq = min(w, h)
left, top = (w - sq) // 2, (h - sq) // 2
square = bg.crop((left, top, left + sq, top + sq)).resize((512, 512), Image.LANCZOS)

# 3. Optional: darken center for text readability (radial vignette)
overlay = Image.new('RGB', (size, size), (0, 0, 0))
mask = Image.new('L', (size, size), 0)
mask_draw = ImageDraw.Draw(mask)
for r in range(size // 2, 0, -1):
    alpha = int(140 * (1 - r / (size // 2)))
    mask_draw.ellipse([size//2-r, size//2-r, size//2+r, size//2+r], fill=alpha)
result = Image.composite(overlay, square, mask)

# 4. Find font
font_path = next((f for f in FONT_PATHS if os.path.exists(f)), None)
font = ImageFont.truetype(font_path, size=120, index=1) if font_path else ImageFont.load_default()

# 5. MEASURE FIRST — check text fits before drawing
draw = ImageDraw.Draw(result)
bbox = draw.textbbox((0, 0), "TEXT", font=font)
text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

# Auto-shrink if text overflows canvas (leave 10% margin)
max_w = int(canvas_w * 0.9)
if text_w > max_w:
    font = ImageFont.truetype(font_path, size=int(120 * max_w / text_w), index=1)
    bbox = draw.textbbox((0, 0), "TEXT", font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

# Center
x = (canvas_w - text_w) // 2
y = (canvas_h - text_h) // 2

# 6. Draw text with glow
# Glow pass (multiple offsets in a darker tint)
for dx in range(-2, 3):
    for dy in range(-2, 3):
        if dx == 0 and dy == 0: continue
        draw.text((x+dx, y+dy), "TEXT", fill=(80, 60, 120), font=font)
# Main text
draw.text((x, y), "TEXT", fill=(255, 255, 255), font=font)

# 7. Verify contrast
def luminance(rgb):
    r, g, b = [c/255.0 for c in rgb]
    r = r/12.92 if r <= 0.03928 else ((r+0.055)/1.055)**2.4
    g = g/12.92 if g <= 0.03928 else ((g+0.055)/1.055)**2.4
    b = b/12.92 if b <= 0.03928 else ((b+0.055)/1.055)**2.4
    return 0.2126*r + 0.7152*g + 0.0722*b

def contrast_ratio(fg, bg):
    l1, l2 = luminance(fg), luminance(bg)
    if l1 < l2: l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)

ratio = contrast_ratio((255, 255, 255), (10, 10, 15))
print(f"Contrast ratio: {ratio:.1f}:1 {'PASS' if ratio >= 4.5 else 'FAIL — needs brighter text or darker bg'}")
```

## Lessons from Past Projects

These patterns come from real bugs and fixes across projects.

### Text sizing
- **Measure before drawing.** Use `textbbox()` to check dimensions BEFORE rendering. Text that overflows the canvas is the most common bug (iblipper `b737a07` — font cropping on "Hurry" emotion).
- **Short words can be bigger.** 4-7 character words can fill 50%+ more space than the default size (iblipper `5f35f69` — Billboard optimization).
- **Long text needs auto-shrink.** Scale font size proportionally: `new_size = base_size * max_width / text_width`.

### Line height and spacing
- **Don't crush line height.** Line height factor of 1.0 is standard — going below causes text overlap on large sizes (iblipper `3f50f62`).
- **Multi-line: use Golden Ratio.** For text >8 characters that wraps, Golden Ratio (1.618) proportions for text-area-to-whitespace look right (iblipper `7625fc6`).
- **Letter-spacing uses explicit pixel offsets**, not CSS-style `letter-spacing`. Draw each character individually with `x += char_width + spacing`.

### Contrast and readability
- **Check contrast ratio.** WCAG AA minimum is 4.5:1 for normal text, 3:1 for large text (>18pt bold). The wordmark fix (`bfbcbfd`) bumped to 10.8:1.
- **Subtle background elements disappear on mobile.** Grid lines, contour marks, and fine detail at contrast <30 units (on 0-255 scale) are invisible on small screens in ambient light. Minimum ~55 units for decorative elements that should be visible.
- **Dark theme: cream/olive text on near-black.** `(230, 228, 210)` on `(10, 10, 15)` is the proven palette. Pure white `(255, 255, 255)` is too harsh for OLED.

### Brand consistency
- **psychodeli-brand-guide owns all Psychodeli image generation.** Never rebuild that pipeline elsewhere. Nunito 900, 10-ring blue gradient border, fractal fill.
- **One font treatment per app.** Vary background, not typography. Same weight + size across all platform sizes for one product.
- **Optical alignment > mathematical alignment.** Nudge text 2-4px visually when adjacent to UI elements (Psychodeli `d84f2f3` — wordmark nudged 4px for optical alignment with audio button).

## Naming Convention

Output files should be prefixed with the platform target:
- `firetv-icon-512x512.png`
- `tvos-topshelf-2320x720.png`
- `play-feature-1024x500.png`

This allows multiple platform assets to coexist in the same `assets/` directory.

## Design Principles

- **OLED-first**: Dark backgrounds, luminous text, true black where possible
- **Readable at small sizes**: Test that text is legible at the smallest output size before generating the full set
- **No false profundity**: App name + one line descriptor max. No taglines, no adjectives.
- **Consistent branding**: Same font treatment across all sizes for one app. Vary background, not typography.
- **Show the product**: Use actual app screenshots as backgrounds, not stock imagery.
- **Verify contrast**: Always print the contrast ratio. Below 4.5:1 is a fail.

## Workflow

1. User describes what they need (app name, sizes, background image)
2. Generate all sizes in one Python script
3. **Measure all text bboxes before drawing** — auto-shrink if overflow detected
4. **Print contrast ratios** for all text layers
5. Show the results inline for approval
6. Iterate on font size, positioning, effects as needed
7. Save with platform-prefixed filenames to project's `assets/` directory
