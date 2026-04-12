# Web — Marginalia, Pandoc, Static Capture, Data-URI

The editorial-HTML channel and its tooling. Covers:

- **Marginalia** — the typographic callout library for blog posts and paper-style pages
- **Pandoc bridge** — the Lua filter that emits marginalia classes from markdown
- **Web rendering & static capture** — Playwright / weasyprint / headless Chrome for DOM → PNG / PDF
- **Data-URI embedding** — single-file portability trick for artifacts that must travel self-contained

Part of the [Render](../render.md) skill — see the top-level index for mission, universal rules, and channel map.

## Marginalia — Editorial HTML

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

## Pandoc → Marginalia Bridge

Pandoc 3.2+ recognizes GitHub-style alerts (`> [!NOTE]`) via the `+alerts` extension. A Lua filter at `~/Documents/dev/marginalia/pandoc/marginalia.lua` rewrites pandoc's output to marginalia classes: GitHub alerts → `mg-callout[data-type]`, extended markers (ASIDE/MARGIN/QUOTE) → `mg-sidebar` / `mg-margin` / `mg-pull`, plain blockquotes → `mg-pull`, `==mark==` → `mg-mark`, `{Badge}` and multi-word `{Text: type}` → `mg-badge`, pandoc footnotes → `mg-fn` popover, fenced code → `mg-code`, inline code → `mg-inline-code`, `{dropcap}` line marker → `mg-dropcap` wrap.

### Usage

```bash
pandoc draft.md \
  --from markdown+mark+alerts \
  --lua-filter ~/Documents/dev/marginalia/pandoc/marginalia.lua \
  --template ~/Documents/dev/marginalia/pandoc/template.html \
  --standalone \
  -o draft.html
```

Same source fans out to PDF (via weasyprint), DOCX, or EPUB without losing marginalia's typographic voice:

```bash
# HTML → PDF
weasyprint draft.html draft.pdf

# Direct to DOCX (filter still applies)
pandoc draft.md --from markdown+mark+alerts \
  --lua-filter ~/Documents/dev/marginalia/pandoc/marginalia.lua \
  -o draft.docx
```

### Reference example
`~/Documents/dev/marginalia/pandoc/examples/us-constitution.md` — an annotated US Constitution reader's edition. Exercises every transformation: dropcap, all four callout colors, sidebars, margin notes in the desktop gutter via CSS Grid subgrid, pull quote, inline highlights, badges, footnote popover, fenced code, plus a cursive copperplate dropcap initial and closing signature paragraph. Good starting point for any new marginalia page.

## Light editorial variant — the F explainer pattern

The [Attentional Foraging F-pattern explainer](https://andyed.github.io/attentional-foraging/explainer/) uses marginalia with a set of light-theme editorial extensions that diverge from the default OLED palette. When a project wants a warm, reader-friendly light mode (explainer pages, blog posts, paper drafts), this is the reference exemplar.

Source: `~/Documents/dev/attentional-foraging/site/explainer/index.html` + `docs/drafts/osec-explainer.md` + `scripts/build-explainer.js`.

### Build path

The F explainer uses the browser-side **marginalia-md.js** converter via a Node build script, not pandoc. Markdown lives in `docs/drafts/osec-explainer.md`, build script runs `marginalia-md.js` at build time, output is pre-rendered static HTML at `site/explainer/index.html`. Different path from the pandoc bridge above, same underlying marginalia classes — the build script also post-processes `{dropcap}` into `<p class="has-dropcap">` as a workaround for a marginalia-md rendering quirk.

**When to use each path:**
- **Pandoc bridge** — for paper-draft round-trips (markdown → HTML → PDF → DOCX), when the same source needs to fan out to multiple output formats
- **marginalia-md.js + Node build** — for single-target static explainer pages with heavy custom extensions and inline raw HTML

### Extensions beyond core marginalia

The F explainer adds four non-canonical patterns. They're worth knowing by name because they solve gaps marginalia doesn't cover:

| Class / pattern | Purpose | Why it's not in core marginalia |
|---|---|---|
| **`.outer-note`** | Short punchy margin labels (0.75em, amber `#b08050`, ~150px wide, `position: absolute; right: -180px`). Hidden at `max-width: 1100px`. | `mg-margin` is for full-sentence annotations; these are one-phrase rubrications that work like Tufte sidenotes. |
| **`.stats-detail`** | Inline span for numerical details with a dashed amber underline (`ρ = 0.02, p = .30`). Warm cream background, smaller font. | No native inline-stats treatment in marginalia; inline `<code>` is wrong semantically. |
| **`.has-dropcap`** on `<p>` directly | `{dropcap}` line marker post-processed to `<p class="has-dropcap">`. CSS targets `p.has-dropcap::first-letter`. | Works around a marginalia-md.js rendering quirk; conceptually equivalent to our pandoc filter's `mg-dropcap` div wrap. |
| **Staged h2 colors via `:nth-of-type`** | `h2:nth-of-type(1..4)` get gold/red/blue/green for the OSEC stages (Orient, Survey, Evaluate, Commit). | Document-structure-driven color. Works because this page's h2s are the OSEC stages in order, so position *is* semantics. |

The F explainer also floats `.mg-margin` and `.mg-sidebar` to the right *inside* the content area (230px width, amber-tinted `#d4a574` border) rather than escaping to the outer gutter the way the US Constitution example does. Reader-friendly on narrower viewports.

### Warm editorial palette

| Token | Value | Role |
|---|---|---|
| Background | `#fafaf8` | Warm cream, not pure white |
| Body text | `#222222` | Near-black on Georgia serif |
| Accent amber | `#d4a574` | Margin-note borders, legend edges |
| Note blue | `#f5f8fd` bg + `#2266cc80` border | Info callouts |
| Tip green | `#f2faf4` bg + `#22883380` border | Positive notes |
| Warning amber | `#fdf9f0` bg + `#cc880080` border | Cautions |
| Important red | `#fdf5f5` bg + `#cc444480` border | Emphasis |
| Stats-detail bg | `#f8f4ee` + dashed `#d4a574` underline | Inline numerical callouts |

Matching matplotlibrc: [`render_assets/matplotlibrc_light.py`](../render_assets/matplotlibrc_light.py). Same Georgia stack, same `#fafaf8` figure facecolor — figures rendered with the light rcparams match the editorial palette 1:1.

### When to use which variant

- **Dark (OLED)** — default. Scrutinizer / Psychodeli assets, blog posts on dark-themed sites, paper figures destined for a dark slide deck, any page using the default `data-mg-theme="dark"`.
- **Light editorial** — long-form explainers, paper drafts in light review UI, blog posts on light-themed sites. Match to the F explainer when the voice is "reader's edition" not "research console".

**Pick one per document.** Don't mix dark and light callouts in the same paper or post.

### Key Claims / K-ID convention

Related: the attentional-foraging project uses a `[NB##:K##]` citation convention for quantitative findings. Every analysis notebook has a **Key Claims** block at the top with stable K-IDs. Prose cites findings via bracketed references (`[NB14:K3]` means notebook 14, key claim 3). Values must come from executed cell output, never hand-typed. Retired claims get `(retired YYYY-MM-DD: reason)` rather than renumbering.

When working on attentional-foraging or adopting the convention elsewhere: read `~/Documents/dev/attentional-foraging/CLAUDE.md` for the full spec, and if prose disagrees with a Key Claims row, the prose is wrong. Run `notebooks-v2/update_key_claims.py` after modifying a notebook's Key Claims block.

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

### Responsive sweep helper — `render_assets.capture`

For "what does this look like at mobile/tablet/laptop/desktop?" in one command, the paired module [`render_assets/capture.py`](../render_assets/capture.py) wraps Playwright around the tier data in [`render_assets/dimensions.py`](../render_assets/dimensions.py):

```python
from render_assets.capture import capture_responsive

paths = capture_responsive(
    url="https://andyed.github.io/marginalia/",
    output_dir="captures/",
    color_scheme="dark",
)
# Writes four retina PNGs (device_scale_factor=2):
#   captures/andyed-github-io-marginalia-mobile-390x844.png
#   captures/andyed-github-io-marginalia-tablet-820x1180.png
#   captures/andyed-github-io-marginalia-laptop-1280x800.png
#   captures/andyed-github-io-marginalia-desktop-1920x1080.png
```

Or from the command line:

```bash
python -m render_assets.capture https://andyed.github.io/marginalia/
python -m render_assets.capture https://example.com --dir captures/ --dark
python -m render_assets.capture https://example.com --selector main --slug hero
python -m render_assets.capture https://example.com --tiers mobile-large desktop-qhd ultrawide
python -m render_assets.capture https://example.com --full-page
```

Defaults: four-tier sweep (`mobile tablet laptop desktop`), `device_scale_factor=2`, wait for `document.fonts.ready`, wait for `networkidle`. Output filenames follow the naming convention in [`channels/dimensions.md`](dimensions.md#naming-convention-for-exported-files). Exit `0` on full success, `1` if any tier failed, `2` on missing Playwright / Chromium or usage error. Playwright is an optional install — the module is importable without it and raises a clean `ImportError` with install instructions on first call to `capture_responsive()`.

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
