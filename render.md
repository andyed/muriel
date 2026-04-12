# Render — Multi-channel visual production

**Mission: kick Photoshop's llama ass.** Photoshop is a $30/mo static raster editor with menu-driven workflow and zero path to data-driven generation. Render is a free, scriptable, multi-channel toolkit that produces every visual artifact a researcher-designer-engineer ships — from text source files that diff in git and regenerate from data.

## Channels

| Channel | Format | Tool | Section |
|---|---|---|---|
| Raster | PNG/JPG | Pillow + `typeset.py` | [Implementation Pattern](#implementation-pattern-inline-fallback) |
| Vector | SVG | hand-rolled / `svgwrite` / `cairosvg` | [SVG](#svg--vector-channel) |
| Editorial HTML | DOM + CSS | marginalia | [Marginalia](#marginalia--editorial-html-channel) |
| Interactive | WebGL / Canvas / D3 | single-file HTML | [Interactive JS](#interactive-js--live-demo-channel) |
| Web → static | Playwright / headless Chrome | screenshot, PDF, DOM capture | [Web Rendering & Static Capture](#web-rendering--static-capture) |
| Video | MP4 / GIF | ffmpeg + `desktop-control` | [Video Production](#video-production-product-demos) |
| Terminal | Unicode | `chart.py` | [ASCII Charts](#ascii-charts-text-based-data-viz) |
| Density viz | PNG | `typeset.render_heatmap()` | [Heatmaps](#heatmaps--smooth-gaussian-density-overlays) |
| Gaze viz | PNG/SVG/JS | scanpath, fixation, AOI | [Gaze Plots](#gaze-plots--scanpath--fixation-visualization) |

Photoshop does one of these (raster), badly for the others, and zero of them reproducibly.

## Universal rules

Codified from per-project bug fixes — apply to every channel:

- **8:1 contrast minimum** on all text. Compute the WCAG ratio. No exceptions.
- **Decorative elements ≥55/255** on a dark background, or they vanish on small screens.
- **Measure before drawing.** Bbox / `viewBox` / `getBoundingClientRect` first; auto-shrink on overflow.
- **Label every number.** Units and context required.
- **OLED palette:** `(230,228,210)` cream on `(10,10,15)` near-black. Pure white is too harsh.
- **One font treatment per app/paper.** Vary background, not typography.
- **Optical alignment > mathematical alignment.** Nudge 2-4px when adjacent to UI elements.
- **Generated > drawn.** If the data could drive it, it should.
- **Reproducible > one-off.** Save the script alongside the output.
- **No false profundity.** Substance over hype.

## Visualization principles

For data-driven channels (raster plots, SVG, interactive JS), apply Tufte/Bertin/CRAP via three high-leverage patterns:

- **Small multiples** — same chart, repeated, with one variable changing. Lets the eye compare without re-anchoring. Reach for this whenever you'd otherwise build a complex multi-series single chart. (Tufte's coining; appears throughout AdSERP / Scrutinizer figures.)
- **Linked displays / brushing** — selecting in one view highlights the corresponding marks in every other view. D3's strength. Perfect for exploratory dashboards, OSEC phase explorers, and any "facets that share a record set" interface.
- **Semantic zoom** — representation *changes* by zoom level, not just scale. Overview shows aggregate; mid zoom shows clusters; deep zoom shows individual records. Different from optical zoom. Pairs with linked displays for the OSEC sector explorer pattern.

Reference: `~/Documents/dev/ascii-charts/docs/PERMUTE.md` — full Tufte/Bertin/Gestalt/CRAP framing.

## Interaction design grounding

When building interactive demos or UI affordances around the visuals, the design choices have empirical anchors:

- **Fitts's Law** — pointing time = `a + b·log₂(D/W + 1)`. Big targets close to the cursor are fast; small targets far away are slow. Implication: primary controls go large and near the user's current attention point. Fisheye expansion is Fitts's Law made visible.
- **Hick's Law** — choice time = `a + b·log₂(n + 1)`. Decision time grows logarithmically with options. Implication: collapse n>7 options into hierarchy or progressive disclosure.
- **Fisheye menus** — focus+context lens that expands the item under the cursor while compressing peripheral items. Andy's MS Human Factors thesis (Clemson). The trick: each item gets a *guaranteed minimum size* below the lens floor so distant items remain clickable, not just visible. Apply to long lists where the user needs to keep peripheral context.
- **Marginalia callouts** — typographic affordances (pull quotes, asides, margin notes) are the editorial equivalent of fisheye: they create a visual hierarchy that lets the eye sample without losing the through-line.
- **Cortical magnification & foveation** — the retinal-side reason fisheye works at all. Inside the Math is the canonical explainer; reference it when explaining *why* focus+context isn't a UI gimmick.

Use these as design rationale in figure captions and blog posts — the vocabulary is precise, the laws are quantified, and the lineage runs from psychophysics to interaction design.

## Aesthetic vocabularies

Design grammars worth naming explicitly when a project's visual register calls for something specific. Like the Visualization Principles section above, these are a menu of established traditions — borrow their conventions, don't reinvent them. Start with FUI; add more as projects demand.

### FUI — Fantasy / Fictional User Interface

The industry term for sci-fi UI: the HUDs, consoles, and data overlays you see in Iron Man, Blade Runner 2049, The Martian, Westworld, The Expanse. Not "cyberpunk" (too broad, that's the umbrella aesthetic). Not "HUD" (that's a UI mode, heads-up). **FUI** is the keyword that unlocks the right references.

**Canonical lineage — where to look for inspiration:**

| Studio / Designer | Work | Notable for |
|---|---|---|
| **Perception NYC** (John LePore) | Iron Man's Stark HUDs, Black Panther's Shuri lab, Avengers | Radial geometry, translucent data layers |
| **Territory Studio** | Blade Runner 2049, The Martian, Ex Machina, Ghost in the Shell (2017) | Analytical overlays, thin-stroke grids, restraint |
| **Ash Thorp** | Prometheus, Ender's Game, Call of Duty Ghosts | Motion-forward reveals, procedural data |
| **GMUNK** (Bradley G. Munkowitz) | TRON: Legacy, Oblivion, Prometheus | Radial/polar compositions, shader-driven textures |
| **Jayse Hansen** | Iron Man 3, Big Hero 6, Star Trek Beyond | Typographic/numeric precision in flight HUDs |

**Visual grammar — the recognizable elements:**

- **Thin strokes** (0.5–1px) arranged in grids, polar coordinates, concentric rings, or parallel rules
- **Monospace numerics with leading zeros** — `00042`, `0.0384`, `N 40°42'46"`, `T-00:14:22`
- **Radial / polar elements** — dials, compass overlays, scan arcs, rose diagrams. Psychodeli's 10-ring wordmark border is a well-tempered instance of this grammar.
- **Grid overlays** — faint CSS Grid lines in accent color, sometimes animated or parallax-scrolling
- **Leader lines** — thin diagonal strokes from a data point to a typographic callout, like an engineering drawing
- **Scan lines** — subtle horizontal-line texture across the frame (~3% opacity, 2px period). Optional chromatic aberration for CRT nostalgia.
- **Data tickers** — live-updating numbers, `requestAnimationFrame`-driven counters that roll or flicker between values
- **Animated reveals** — elements fade / translate / scale in with staggered 80–200ms delays, not instantly. `cubic-bezier(0.4, 0, 0.2, 1)` for the "precise machinery" feel.
- **Restrained palette** — one dominant accent hue (cyan, amber, red) on near-black. Matches the universal OLED rule.
- **Glitch / noise accents** — used as *punctuation*, never as ambient texture

**Technical substrates — what to build it with:**

- **SVG** for thin-stroke geometry (rings, grids, crosshairs, rose diagrams). Animate via `requestAnimationFrame`, `<animate>` elements, or CSS transitions on stroke properties.
- **CSS Grid** for the underlying layout. HUD blocks are rectangular arrays; let the cascade do the arithmetic.
- **Canvas2D** for tickers and anything where SVG reflow would be expensive. 60fps number counters, rolling waveforms, heatmap scrubs.
- **WebGL shaders** for fullscreen post-process — scan lines, chromatic aberration, noise. One fragment shader layered on top of everything else.
- **Monospace display fonts:**
  - *Working mono:* IBM Plex Mono, JetBrains Mono, Berkeley Mono (paid, exquisite), Space Mono, Fira Code
  - *Display FUI mono:* Orbitron, Rajdhani, Exo, Share Tech Mono, Audiowide — drawn specifically for sci-fi interfaces
- **Animation timing:** 80–200ms stagger between elements on reveal; `ease-out` for entrance, `ease-in` for exit. Use the Web Animations API (`element.animate(...)`) for programmatic sequencing.

**Restraint rules — FUI is shockingly easy to do badly:**

- **One loud element per screen.** Everything else is quiet. A single radial scanner, a single rolling data block, a single reveal animation — surrounded by calm typography.
- **Information actually present.** Fake data (`Lorem 0923.88.Ipsum`) reads as fake. Either show real data or stylize the placeholder so clearly nobody mistakes it for real (block rectangles, `████`, `XX.XX`).
- **Motion earns attention.** Don't animate everything simultaneously. Stagger reveals. Let the eye land and re-land.
- **Accessibility still applies.** 8:1 contrast works here too — thin strokes at low opacity fail the rule. Key information must meet WCAG even in the darkest HUD.
- **Type is load-bearing.** Most amateur FUI dies from mushy typography. Pick one monospace face, commit to it, track it tight, and let the numbers do the work.

**Reference archives — where to browse when stuck:**

- [fuidesign.com](https://fuidesign.com/) — Ash Thorp's curated showcase
- [hudsandguis.com](https://www.hudsandguis.com/) — dormant but canonical Tumblr archive; still the best single-site reference
- [perception.nyc](https://perception.nyc/) / [territorystudio.com](https://territorystudio.com/) — studio portfolios
- CodePen search for `#fui`, `#hud`, `#sci-fi-ui` — community implementations worth forking
- Film stills from the lineage above — particularly Blade Runner 2049 (analytical spread), The Martian (orbital mechanics), Ghost in the Shell 2017 (full-screen data overlays)

**Where FUI fits the current project set:**

- **Scrutinizer** — the vision-science overlays (eccentricity rings, PPD calibration, sector explorers) are already proto-FUI. Codifying the vocabulary sharpens future work.
- **Cartographer Explorer v2** — session timelines, faceted overviews, approach-retreat dashboards are natural HUD territory.
- **Paper figures** (AdSERP, RecGaze, OSEC) — static gaze-path visualizations can borrow FUI grammar without gimmickry: leader lines, mono numerics, faint grids behind the gaze ribbon.
- **No Kings / iBlipper** — kinetic typography intersects FUI through Territory Studio's work on motion-forward interfaces.
- **OSEC phase explorer** — semantic zoom + FUI grammar is the right pairing.

## When to use

Whenever the user needs a visual artifact for human eyes — store assets, paper figures, blog post explainers, video demos, terminal output, scientific plots, infographics, screenshots, gaze visualizations. Invoke with `/render` followed by what's needed.

## Raster capabilities

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

These patterns come from real bugs and fixes across Andy's projects:

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

## Marginalia — Editorial HTML Channel

The editorial layer for blog posts, paper-style web pages, and any prose that needs typographic callouts. 15 components, zero dependencies, dark theme by default. CSS-only — JS is optional.

**Library:** `~/Documents/dev/marginalia/` (CDN: `marginalia@latest`)
**Reference:** `~/Documents/dev/marginalia/SKILL.md` (full pattern catalog) and `~/Documents/dev/marginalia/llm.md` (LLM cheat sheet)

### Quick setup
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/marginalia@latest/marginalia.css">
<script src="https://cdn.jsdelivr.net/npm/marginalia@latest/marginalia.js" defer></script>
<script src="https://cdn.jsdelivr.net/npm/marginalia@latest/marginalia-md.js" defer></script>
```

### Markdown patterns (subset)
```
> [!NOTE]    > [!TIP]    > [!WARNING]    > [!IMPORTANT]
> [!QUOTE]   > [!ASIDE]  > [!MARGIN]
==highlighted==    {Badge}    {Badge: tip}    [^1](footnote)
{dropcap}
```

Plain `>` blockquotes become 3D perspective pull quotes — the signature component. Wrap content in `<div class="mg-spread">` for two-column magazine layout.

### Rules (from past feedback)
- **Core narrative inline always.** Sidebars are for "go deeper" references only — one per section, at the heading.
- **Decorative elements ≥3:1 contrast.** Don't fade below — compute the ratio.
- **All text 8:1 minimum.**
- All marginalia classes use `mg-` prefix. Theme via `--mg-*` CSS custom properties — these inherit into child SVGs, so a single theme switch repaints the whole page including embedded vector graphics.

### Pandoc bridge (proposed)
Pandoc 3.9+ recognizes GitHub-style alerts (`> [!NOTE]`) natively. A Lua filter at `marginalia/pandoc/marginalia.lua` would rewrite pandoc's default classes (`alert alert-note`) to marginalia's (`mg-callout` + `data-type="note"`), plus handle plain blockquotes → pull quotes, `Mark` inline → `mg-highlight`, footnotes → popovers, and `{dropcap}` markers. Pair with a custom template `marginalia/pandoc/template.html` that includes the CDN tags. Then any markdown source flows: `pandoc input.md --filter marginalia.lua --template template.html -o out.html` — and the same source can target HTML, PDF (via weasyprint or LaTeX), DOCX, EPUB.

## SVG — Vector Channel

Photoshop can't generate vectors from data. SVG can — and the output diffs in git, scales infinitely, embeds in HTML and LaTeX, and inherits CSS theming from marginalia (`--mg-*` carries through to `<svg>` children).

### When to use
- Paper figures (round-trip with LaTeX)
- Diagrams generated from data (gaze ribbons, F-pattern overlays, OSEC phase bands)
- Icons and wordmarks that need exact scaling
- Anything embedded in a marginalia HTML page that should re-theme on light/dark switch
- Statistical plots when matplotlib's SVG export is ugly

### Tooling
- **Hand-rolled `<svg>` strings** — zero deps. Fine under 200 lines.
- **`svgwrite`** or **`drawsvg`** (Python) — fluent API for procedural generation.
- **`mermaid-cli`** (`mmdc`) — flowcharts from text → SVG.
- **Excalidraw export** — manual diagrams. Always `roughness: 0`, `fontFamily: 2` (Helvetica), `fillStyle: "solid"` (per past feedback — the hand-drawn aesthetic reads as fake).
- **`cairosvg`** or **`rsvg-convert`** (homebrew) — SVG → PNG/PDF when stores reject vectors. Use full TTF font paths, same rule as Pillow.

### Patterns
- **Use `viewBox`, not fixed `width`/`height`.** Scales without re-export.
- **CSS custom properties for theming** — share the `--mg-*` prefix with marginalia so SVGs inherit the host page palette:
  ```svg
  <svg viewBox="0 0 400 200" role="img">
    <title>Phase decomposition</title>
    <desc>Survey phase (0-2s) followed by evaluate phase (2-8s).</desc>
    <style>
      .axis { stroke: var(--mg-fg, #e6e4d2); stroke-width: 2; }
      .data { fill: var(--mg-accent, #ff7); }
    </style>
    <line class="axis" x1="20" y1="180" x2="380" y2="180"/>
    <rect class="data" x="20" y="100" width="80" height="80"/>
  </svg>
  ```
- **`<title>` and `<desc>`** are accessibility-required for paper figures.
- **`<text>` elements respect 8:1 contrast** — same WCAG check applies.
- **Embed fonts via `<defs>` + `@font-face`** if the SVG must render outside its host page.

### Recipes
- **Gaze ribbons** — line through fixation points, stroke-width = duration in ms / 10
- **F-pattern overlay** — colored bands over a SERP screenshot showing survey + evaluate phases (per the F-pattern decomposition work)
- **OSEC phase diagram** — multi-band horizontal timeline from a gaze sequence
- **Wordmark generation** — Psychodeli's 10-ring blue gradient border at any size from one source (but defer to psychodeli-brand-guide for actual asset generation)

### Conversion
- **SVG → PNG:** `cairosvg input.svg -o out.png -W 1280 -H 720` or `rsvg-convert -w 1280 input.svg > out.png`
- **SVG → PDF:** `cairosvg input.svg -o out.pdf` (for paper inclusion)
- **HTML → SVG snapshot:** Playwright `page.locator('svg').screenshot()` for live-rendered figures (see Web Rendering & Static Capture)

## Interactive JS — Live Demo Channel

The biggest win over Photoshop: **parameters the reader can move**. Static images can't be explored; interactive demos let the reader develop intuition by playing with the underlying model.

### When to use
- Blog post explainers (Adventures in AI Coding, Inside the Math style)
- Paper figures with sliders (CHI / ETTAC / CIKM submissions can include live demo URLs)
- Worked examples and teaching artifacts
- Audio-reactive visualizers (Psychodeli lineage)
- Eye-tracking replays with timeline scrubber
- Anything where "watching it move" matters more than "seeing one frame"

### Constraints (from `~/CLAUDE.md`)
- **ES6 modules direct.** No bundlers, no build step.
- **WebGL is the primary graphics stack.** Canvas2D for non-shader 2D, D3 for data binding to DOM/SVG, Three.js when 3D scene management beats raw WebGL.
- **Defensive numerics:** `isFinite()` guards, NaN traps, clamp before passing to GLSL.
- **Small focused functions** over mega-files.
- **Inline comments explain "why."**

### Default scaffold — single-file HTML

```html
<!DOCTYPE html>
<html data-mg-theme="dark">
<head>
  <meta charset="utf-8">
  <title>Demo</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/marginalia@latest/marginalia.css">
  <style>
    :root { color-scheme: dark; }
    body { max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
    canvas { width: 100%; aspect-ratio: 16/9; display: block; background: #0a0a0f; }
    .controls { display: flex; gap: 1rem; padding: 1rem 0; }
  </style>
</head>
<body>
  <main>
    <h1>Title</h1>
    <p>One-paragraph context.</p>
    <canvas id="stage" width="1280" height="720"></canvas>
    <div class="controls">
      <label>Param <input type="range" id="p1" min="0" max="1" step="0.01" value="0.5"></label>
    </div>
  </main>
  <script type="module">
    'use strict';
    const cvs = document.getElementById('stage');
    const ctx = cvs.getContext('2d'); // or 'webgl2'
    const p1 = document.getElementById('p1');
    function frame() {
      const v = parseFloat(p1.value);
      if (!isFinite(v)) return requestAnimationFrame(frame);
      // ... draw using v ...
      requestAnimationFrame(frame);
    }
    frame();
  </script>
</body>
</html>
```

One file. No build. Marginalia handles editorial chrome. Demo lives at `<project>/demos/<name>.html` and can be linked from a blog post or paper.

### Library choices

| Need | Library | Why |
|---|---|---|
| Shaders / 3D / perf | WebGL2 raw + Three.js for scenes | Andy's primary stack |
| Data binding to DOM/SVG | D3 v7 | Reactive scales, no virtual DOM |
| 2D sketches / teaching | p5.js | Lowest activation energy |
| Audio-reactive | Web Audio API + AnalyserNode | Native, zero deps |
| Eye-tracking replay | Custom Canvas2D + rAF | Fixation timing matters; no abstraction |
| Reactive UI controls | Vanilla `<input type="range">` | No framework needed for sliders |

### Permalink convention
Demos with shareable state should follow the **PermalinkManager** pattern from Scrutinizer/Psychodeli: URL hash encodes parameters, parsed on load, rewritten on change. Read the existing manager class first — don't reinvent it.

### Marginalia integration
Wrap demos in marginalia callouts for editorial context:
```html
<aside class="mg-callout" data-type="tip">
  <h3>Try it</h3>
  <iframe src="demos/foveation.html" loading="lazy" style="width:100%;border:0;aspect-ratio:16/9"></iframe>
  <p>Drag the slider to see how cortical magnification compresses peripheral vision.</p>
</aside>
```

### Reference exemplars (don't rewrite)
- **Inside the Math** — shipped WebGL explainer for foveation/cortical magnification. Reference it; don't rebuild it.
- **Scrutinizer demos** — PermalinkManager pattern for shareable WebGL state.
- **Psychodeli** — audio-reactive shader pipeline (owned by psychodeli-brand-guide for assets).

### Distribution & hosting

Once a demo exists as a single-file HTML, the next decision is where it lives. Different hosts have sharply different strengths — choose based on audience (private vs public), forkability, and build friction.

| Host | Best for | Trade |
|---|---|---|
| **GitHub Pages** | Repo-hosted demos (Scrutinizer, Psychodeli, marginalia, Inside the Math) — canonical, diffable, co-located with source. | Build/push latency; doesn't surface demos for browsing discovery. |
| **CodePen** | Single-file shareable demos; sci-fi / FUI experiments; "paste this into a Pen" teaching artifacts; fork-to-iterate. | Free Pens are public — don't paste unreleased client or research code. |
| **Observable** | D3 data-viz figures with reactive cells — the right host for CHI / ETTAC / CIKM paper figures where the reader can move parameters. | Cell-based, not a normal HTML file — different mental model. |
| **gist** | Minimum-friction single-file distribution; linkable from notes and papers. | No live preview without a third-party renderer (bl.ocks.org went read-only). |
| **CodeSandbox / StackBlitz** | Full-project demos with npm dependencies; SDK examples. | Overkill for single-file work; heavier iteration loop. |
| **Local `file://`** | Private iteration, screenshot capture, ffmpeg recording of interactive demos. | Doesn't share without promoting to a host. |

#### CodePen — the Prefill API

CodePen's highest-leverage feature: `POST` a JSON payload of HTML/CSS/JS to `codepen.io/pen/define` and open a new Pen with the code pre-populated, ready for the reader to run or fork. Perfect for "Try this in a Pen" buttons inside blog posts — one click and the reader is in a live editor with your code.

```html
<form action="https://codepen.io/pen/define" method="POST" target="_blank">
  <input type="hidden" name="data" value='{
    "title": "FUI scan overlay",
    "html": "<canvas id=c></canvas>",
    "css":  "body{background:#000}",
    "js":   "/* demo code here */",
    "tags": ["fui","canvas","webgl"]
  }'>
  <button type="submit">Open in CodePen</button>
</form>
```

Full docs: [blog.codepen.io/documentation/prefill](https://blog.codepen.io/documentation/prefill/). Tags, titles, descriptions, and external resources (including marginalia CDN) can all be set in the payload. For educational content this is the highest-leverage single feature in the whole skill — don't reach for screenshots when you can reach for a live fork.

#### CodePen — embeds

Two modes, both work inside marginalia pages:

```html
<!-- Result only -->
<p class="codepen" data-height="400" data-default-tab="result"
   data-slug-hash="abcDEF" data-user="andyed">
  See the Pen on CodePen.
</p>
<script src="https://cpwebassets.codepen.io/assets/embed/ei.js" async></script>

<!-- Full editor (html + css + js tabs) -->
<p class="codepen" data-height="600" data-default-tab="html,result"
   data-slug-hash="abcDEF" data-user="andyed">...</p>
```

Wrap the embed in a marginalia callout for editorial framing inside a blog post:

```html
<aside class="mg-callout" data-type="tip">
  <h3>Try it</h3>
  <p class="codepen" data-height="500" data-slug-hash="..." data-user="andyed"></p>
</aside>
```

#### Observable — for paper figures

Observable notebooks (`observablehq.com`) are the right host for reactive D3 figures embedded in research papers. Cells are reactive — change one slider and every downstream cell recomputes. The embed runtime (`@observablehq/runtime`) lets you pull specific cells into a marginalia page, so the notebook becomes the source of truth and the blog post is a curated view into it. Ideal for CHI / ETTAC / CIKM figure supplements where the reader should be able to explore parameters.

#### Tag conventions

On CodePen specifically: tag each experiment with both a **technical** tag (`webgl`, `canvas`, `svg`, `d3`) and a **genre** tag (`fui`, `hud`, `generative`, `typography`, `scrollytelling`) so your work surfaces to the right community and theirs surfaces to yours.

#### Privacy caveat

Free CodePen Pens are public. Free Observable notebooks are public. Free gists can be "secret" but are still URL-accessible. Don't paste unreleased Scrutinizer shaders, unpublished research data, or client work into any free tier — use GitHub Pages (private repo + gh-pages) or local files for anything sensitive. When in doubt, ask before pasting.

### Lessons from past projects
- **No bare `console.log` in Psychodeli.** Use `window.debugManager`.
- **Don't dim/fade SERP cards on hover or brush.**
- **WebGL variable names: read the source, don't guess.**
- **Shader changes need verification.** Run tests or capture a screenshot before claiming a fix is working.

## Web Rendering & Static Capture

The "DOM is the rendering engine" trick: build the artifact as HTML/CSS/SVG/JS, then capture it with headless Chrome or Playwright. Combines marginalia's editorial chrome, SVG's vector precision, and interactive JS's parameter sliders — then freezes one state into PNG or PDF for distribution.

### When to use
- Capture an SVG that's CSS-themed at runtime (avoids redoing colors per export)
- Snapshot an interactive demo at a specific parameter state
- Render a marginalia paper-style HTML page as PDF for paper submission
- Build infographics in HTML (CSS Grid, marginalia callouts, embedded SVG) and rasterize for store/social
- Capture a Three.js scene at exact framing for blog hero images
- Generate device-frame screenshots from real page renders rather than mocking in Photoshop

### Tooling

| Tool | Strength | Recipe |
|---|---|---|
| **Playwright** (Python or Node) | Full automation, waits for fonts/network/JS, supports clip regions | `page.goto(url); page.locator('svg').screenshot()` |
| **Puppeteer** | Same idea, Chrome-only, lighter | `await page.screenshot({ path, clip })` |
| **`chrome --headless --screenshot`** | Zero-script one-off | `chrome --headless --screenshot=out.png --window-size=1280,720 file://...` |
| **`weasyprint`** | HTML+CSS → PDF without a browser; respects `@page` rules | `weasyprint input.html out.pdf` |

### Patterns

- **Wait for fonts.** `page.evaluate(() => document.fonts.ready)` before screenshot, or webfonts render mid-capture.
- **Set `device_scale_factor=2`** for retina-quality output.
- **Use `clip` regions** to capture a single SVG/canvas instead of the whole viewport.
- **Inject parameters via URL hash** so the same demo HTML can be captured at multiple states (pairs with PermalinkManager pattern).
- **Use `--virtual-time-budget`** in headless Chrome to fast-forward animations to a stable frame.
- **`prefers-color-scheme: dark` matters.** Force it via `page.emulate_media(color_scheme='dark')` so OLED palette renders correctly.
- **Capture small multiples in one run.** Loop over parameter values, set URL hash, screenshot. Output a grid of frames that compose into a small-multiples figure.

### Example: SVG → PNG via Playwright
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(device_scale_factor=2)
    page.set_content(open('chart.html').read())
    page.evaluate('document.fonts.ready')
    page.locator('svg#chart').screenshot(path='chart.png')
    browser.close()
```

### Example: marginalia HTML → PDF via weasyprint
```bash
weasyprint paper-draft.html paper-draft.pdf
```
Add `@page { size: A4; margin: 2cm }` to the marginalia stylesheet override for paper formatting.

### Static capture as the unifier
This channel is what makes the whole toolkit composable. SVG rendered with CSS theming → captured as PNG → embedded in a video. Interactive demo at three parameter states → captured as small multiples → assembled into one image. Marginalia page → captured as PDF for submission. **The DOM is the most flexible compositor; static capture is the export step.**

## Data-URI Embedding

The portability trick: embed images directly inside HTML/SVG/CSS as `data:image/png;base64,...` URIs. Single-file artifacts with zero asset management — they email, paste into Slack, copy onto USB sticks, embed in iframes from sandboxes that block external loads.

### When to use
- Single-file HTML demos (one file = the whole thing)
- SVG with embedded raster textures (one file = the whole figure)
- Marginalia blog post fragments that need to be paste-able
- Email-friendly artifacts (Outlook/Gmail strip external `<img>` until clicked)
- Paper figures where the journal wants a self-contained submission
- CSS backgrounds without HTTP round-trips
- Inlining icons inside SVG so a single file renders correctly when downloaded

### Recipes

**Bash → data URI:**
```bash
# PNG → data URI string
echo "data:image/png;base64,$(base64 -i input.png | tr -d '\n')"

# SVG → data URI (URL-encoded, smaller than base64 for SVG)
python3 -c "import urllib.parse; print('data:image/svg+xml,' + urllib.parse.quote(open('input.svg').read()))"
```

**Python → data URI:**
```python
import base64
def data_uri(path, mime='image/png'):
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'data:{mime};base64,{b64}'

img_uri = data_uri('icon.png')
html = f'<img src="{img_uri}">'
```

**Pillow → data URI without writing a file:**
```python
import io, base64
from PIL import Image
buf = io.BytesIO()
img.save(buf, format='PNG')
uri = f'data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}'
```

**SVG `<image>` element with embedded raster:**
```xml
<svg viewBox="0 0 400 200">
  <image href="data:image/png;base64,iVBORw0KG..." width="400" height="200"/>
</svg>
```

### Size budget
Base64 inflates by ~33%. Stay under ~200 KB per image inside HTML; above that, prefer external assets unless portability is non-negotiable. SVGs URL-encode smaller than base64 — use `urllib.parse.quote` instead.

### Caveats
- Data URIs **bypass browser cache**. Don't use for images that repeat across many pages.
- Some XML parsers reject very long attribute values.
- Email clients are inconsistent: Gmail strips data URIs in some contexts, Outlook handles them in HTML body but not signatures.

## Gaze Plots — Scanpath / Fixation Visualization

The vision-science specialty channel. Photoshop has nothing here; matplotlib has primitives but no eye-tracking idioms. Render keeps the canonical recipes alongside the heatmap pipeline.

### Plot types

| Plot | What it shows | Best for |
|---|---|---|
| **Scanpath** | Numbered fixations connected by saccade lines | Single trial, qualitative inspection |
| **Bubble scanpath** | Same, but circle radius = fixation duration | Single trial, duration emphasis |
| **Heatmap** | Gaussian density over all fixations | Aggregate across trials/users |
| **AOI timeline** | Horizontal bands showing which AOI is fixated when | Sequential analysis, OSEC phases |
| **Saccade rose** | Polar histogram of saccade directions | Reading vs. scanning detection |
| **Fixation duration histogram** | Distribution of fixation durations | Cognitive load comparison |
| **Approach-retreat plot** | Cursor distance to gaze over time | Mouse-gaze coupling (per `project_recgaze_analysis.md`) |

### Tooling
- **`typeset.render_heatmap()`** — already shipped (Tobii-style topographic). See [Heatmaps](#heatmaps--smooth-gaussian-density-overlays) below.
- **Matplotlib + `Circle` patches** — scanpath/bubble scanpath. Set `figsize` large per the readability rule; never default.
- **D3 + SVG** — interactive scanpath with hover-to-inspect, brush-to-filter. Pairs with linked-displays principle.
- **Custom Canvas2D + `requestAnimationFrame`** — playback with timeline scrubber.

### Patterns
- **Numbered fixations** use circles with the index inside; size scales with duration. 8:1 contrast on the number.
- **Saccade lines** at low alpha (~0.4) so overlapping paths don't black out the underlying stimulus.
- **Background stimulus** desaturated to 0.6–0.7 (`feedback_plot_readability.md`) so gaze marks pop without losing context.
- **Color encodes time, not user.** Sequential colormap from start (cool) to end (warm). Categorical color is for AOIs.
- **Always overlay on the actual stimulus**, not a blank canvas. The whole point is showing *where on the page* attention went.
- **AOI rectangles in `<rect class="aoi">`** with marginalia-themed stroke so they re-theme on light/dark switch.

### Recipes Andy actually needs
- **AdSERP scanpaths** — fixation sequence over a SERP screenshot, colored by phase (survey/evaluate per F-pattern decomposition)
- **RecGaze approach-retreat** — cursor x/y vs gaze x/y over time, distance line below (for IUI 2027 / CIKM 2026 papers)
- **Pupil LF/HF trajectory** — cognitive load index over trial position, with sat/opt overlay (ETTAC 2026)
- **Mind2Web replay** — peripheral rendering predictions vs actual gaze fixations, frame by frame

### Data formats
- **Tobii-native:** TSV with `Timestamp, GazePointX, GazePointY, FixationIndex, FixationDuration`
- **Polars idiom** (per Andy's preferences):
  ```python
  import polars as pl
  fix = pl.read_csv('trial.tsv', separator='\t').filter(pl.col('FixationIndex').is_not_null())
  ```
- **Mind2Web format:** action sequence with bounding boxes; scanpath = saccade through bbox centers

## ASCII Charts (text-based data viz)

Another rendering path: Unicode bar charts, sparklines, and tables for terminal/markdown/chat output. No images needed.

**Renderer:** `~/Documents/dev/ascii-charts/chart.py` — Python, zero dependencies.

Available: `bar_chart()`, `sparkline()`, `table()`. Supports negative values, comparison bars, markers, custom fill characters. See the ClickSense README and cartographer README for shipped examples.

## Video Production (product demos)

Another rendering path: scripted screen recordings with tooltip overlays for YouTube/social demos.

### Tools available

| Tool | What it does | How to invoke |
|------|-------------|---------------|
| `desktop-control` MCP | Move mouse, click, key combos, screenshots | `mcp__desktop-control__move_mouse`, `__click`, `__key_combo` |
| `/scrutinizer` skill | Switch modes, toggle features via AppleScript menus | `/scrutinizer mode minecraft-eyeball` |
| AppleScript (direct) | Any macOS UI automation — menu clicks, window focus, keystrokes | `osascript -e '...'` |
| macOS screen recording | Capture video | User starts with `Cmd+Shift+5`, agent controls the app |
| ffmpeg (homebrew-ffmpeg tap) | Trim, burn captions, add music, encode | Hard-burn via `subtitles` filter (libass) |

### Workflow

1. **Write a tooltip manifest** — JSON array of `{start, end, text}` objects
2. **Script the choreography** — `desktop-control` moves the mouse on timed coordinates; AppleScript switches modes
3. **User records** with `Cmd+Shift+5` while agent drives the app
4. **Post-process**: `burn-tooltips.sh manifest.json raw.mov output.mp4`
   - Generates SRT from manifest
   - Burns captions via ffmpeg `subtitles` filter (Helvetica 24px, white, black outline)
   - Trims with `-ss` / `-t` flags
   - Drops audio with `-an` when needed
   - H.264 CRF 22, faststart for YouTube

### ffmpeg setup

The default `brew install ffmpeg` lacks `drawtext`/`subtitles` filters. Install the full version:
```bash
brew uninstall ffmpeg
brew tap homebrew-ffmpeg/ffmpeg
brew install homebrew-ffmpeg/ffmpeg/ffmpeg
```
This includes freetype, libass, fontconfig — enables `drawtext`, `subtitles`, and `ass` filters.

### Tooltip burn script

`scrutinizer2025/scripts/burn-tooltips.sh` — two modes:
```bash
# SRT only (no ffmpeg needed)
burn-tooltips.sh tooltips.json output.srt

# Full pipeline: trim + burn + optional music
burn-tooltips.sh tooltips.json raw.mov output.mp4 [music.mp3]
```

Uses `subtitles` filter (libass) for hard-burn. Falls back to soft-sub mux if drawtext unavailable. Music mixed at 15% volume.

### Lessons learned

- **Trim first, caption second** — tooltip timecodes are relative to the trimmed video, not the raw recording. Use `-ss` to skip dead intro before the filter chain.
- **Drop audio with `-an`** — screen recordings capture system audio, dogs barking, etc.
- **macOS filenames have Unicode spaces** — `PM` in screen recording filenames uses a narrow no-break space (U+202F). Use glob matching, not exact strings.
- **Excalidraw: skip hand-drawn** — use `roughness: 0`, `fontFamily: 2` (Helvetica), `fillStyle: "solid"`. The hand-drawn aesthetic reads as fake, not charming.
- **SRT for YouTube** — even with hard-burned captions, upload the SRT too. YouTube auto-translates it.

### ffmpeg editing recipes

Standalone operations for cutting, joining, and splitting video outside the tooltip pipeline.

```bash
# Cut segment (fast, keyframe-aligned)
ffmpeg -ss 00:00:10 -to 00:00:30 -i input.mp4 -c copy output.mp4

# Cut segment (precise, re-encodes)
ffmpeg -ss 00:00:10 -i input.mp4 -t 20 -c:v libx264 -c:a aac output.mp4

# Last N seconds
ffmpeg -sseof -30 -i input.mp4 -c copy output.mp4

# Concatenate via file list (recommended — works across codecs)
# list.txt contains: file 'clip1.mp4'\nfile 'clip2.mp4'\nfile 'clip3.mp4'
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4

# Concatenate with re-encode (when codecs differ)
ffmpeg -f concat -safe 0 -i list.txt -c:v libx264 -c:a aac output.mp4

# Split into fixed-length segments
ffmpeg -i input.mp4 -c copy -f segment -segment_time 60 -reset_timestamps 1 output_%03d.mp4
```

**`-c copy` vs re-encode:** `-c copy` is instant but cuts on keyframes (may be off by a few frames). Add `-c:v libx264 -c:a aac` for frame-accurate cuts at the cost of speed. `-ss` before `-i` is faster; after `-i` is more precise.

### Design doc

See `~/Documents/dev/ascii-charts/docs/PERMUTE.md` for the infographic aspiration: Tufte, Bertin, Gestalt, CRAP, semantic zoom, small multiples, linked displays.

## Heatmaps — Smooth Gaussian Density Overlays

`typeset.render_heatmap()` generates Tobii-style topographic heatmaps from fixation data. Used for the attentional-foraging explainer images.

```python
from typeset import render_heatmap

heatmap = render_heatmap(
    fixations,              # list of {'x', 'y', 'd'} dicts
    canvas_size=(400, 800), # output dimensions
    radius=18,              # blob radius (controls bin coarseness)
    blur=8,                 # gaussian blur after binning
    colormap="pink",        # "pink" (Tobii-style), "heat", or (r,g,b) tuple
    background="serp.png",  # optional background image path
    desaturate=0.7,         # background desaturation (0=color, 1=gray)
    bg_opacity=0.35,        # background layer opacity
    output="heatmap.png",   # save path (None to just return Image)
)
```

**How it works:** Fixations are binned into a coarse grid, then large gaussian blobs are stamped at each bin center (weighted by fixation count/duration). Density is quantized into 8 bands to create visible topographic contour plateaus, then softened with a light blur so band edges aren't pixelated. Result: discrete rounded peaks that merge where they overlap, like contour islands on a topo map.

**Key parameters:**
- `radius` controls blob size and bin coarseness. Smaller = more granular topology. 12–20 is the sweet spot for aggregate data.
- `blur` controls post-stamp smoothing. Keep low (6–10) to preserve topo feel. Too high washes out the contour structure.
- For sparse data (<500 fixations), increase radius to 30+ so individual blobs are visible.
- For dense data (>10K fixations), the contour banding is what creates the topo feel — without it, density saturates everywhere.

**Colormaps:**
- `"pink"` — monochrome magenta with gamma-corrected two-stop ramp: light pink → hot pink → deep magenta. Alpha ramps fast and saturates early.
- `"heat"` — yellow → red → dark red.
- `(r, g, b)` tuple — monochrome with custom tint.

**Generation script:** `attentional-foraging/scripts/generate_explainer_heatmaps.py` — loads all 2,776 AdSERP trials, filters by phase/behavior, generates `f-decomposition.png` and `f-dissection.png` for the explainer page.

## TODO

### Raster
- [x] **Drop shadow with blur** — Implemented via `ImageFilter.GaussianBlur` in `render_text()` shadow effect.
- [x] **Template system** — `ascii-charts/typeset.py` ships `amazon-icon`, `amazon-small-icon`, `tvos-topshelf`, `play-feature` templates via `render_asset(template=...)`.
- [x] **Batch from JSON** — `generate_from_manifest("assets.json")` in `typeset.py`; CLI `python3 typeset.py --manifest assets.json`.
- [ ] **Multi-line text layout** — Auto-wrap long text with configurable max-width, line-height, and alignment. Currently single-line only.
- [ ] **Curved/arc text** — Text along a circular path for badges, seals, and circular app icon borders. Pillow lacks native support; needs per-character rotation + placement.
- [ ] **Gradient text fill** — Linear/radial gradient fills inside letterforms. Approach: render text as mask, composite with gradient image.
- [ ] **Screenshot compositing** — Place device-framed app screenshots into promotional images (phone/TV mockup frames).
- [ ] **Brand color extraction** — Auto-extract dominant colors from a background image to choose complementary text colors.

### SVG
- [ ] **Gaze ribbon primitive** — `typeset.svg.gaze_ribbon(fixations)` reusable across AdSERP / RecGaze work.
- [ ] **F-pattern overlay primitive** — Colored band generator from phase-segmented gaze data.
- [ ] **OSEC phase diagram primitive** — Multi-band horizontal timeline from a gaze sequence.
- [ ] **Excalidraw → clean-export pipeline** — Batch re-export with `roughness:0`, Helvetica, solid fills.
- [ ] **Mermaid CLI wrapper** — Themed output matching marginalia `--mg-*` palette.

### Interactive JS
- [ ] **Extract shared `permalink.js`** — Pull the PermalinkManager pattern out of Scrutinizer/Psychodeli so demos outside those repos can reuse URL-hash state.
- [ ] **Demo loader snippet for marginalia** — `<mg-demo src="...">` custom element that lazy-loads an iframe and shows a poster frame while loading.
- [ ] **Single-file demo bundler** — Tiny script that inlines CSS/JS/images as data URIs to produce a standalone `.html` for email/paper submission.

### Web rendering & static capture
- [ ] **Small-multiples capture script** — Loop a demo across parameter values via URL hash, screenshot each, assemble into a grid.
- [ ] **Marginalia + weasyprint paper template** — `@page` rules for A4 + letter, figure captions, bibliography.
- [ ] **Playwright device-frame compositor** — Replace manual Photoshop mockups with real HTML-rendered device frames.

### Pandoc + marginalia
- [ ] **`marginalia/pandoc/marginalia.lua` filter** — GitHub alerts → `mg-callout`, blockquotes → pull quotes, Mark → highlight, notes → popovers.
- [ ] **`marginalia/pandoc/template.html`** — Standalone HTML template with CDN tags and `data-mg-theme="dark"`.
- [ ] **Markdown → PDF via marginalia + weasyprint** — End-to-end path for paper drafts.

### Scientific comms (not yet sectioned)
- [ ] **`render/science.md`** subsection — matplotlib rcparams defaults, effect size + CI formatters, notebook editorial pass rules.
- [ ] **Statistical reporting helpers** — format effect sizes, CIs, χ², AUC with the phrasing rules from `feedback_empirical_not_truth.md`.
- [ ] **Figure caption template** — caption-first writing with auto numbering.
