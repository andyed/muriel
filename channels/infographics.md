---
channel: infographics
status: active
requires:
  brand: optional
  audience: required
  reads:
    - muriel.contrast
    - muriel.dimensions
    - muriel.palettes
output:
  kinds: [svg, png]
  registers: [social, blog, editorial]
peer_channels:
  - diagrams
  - raster
  - svg
---

# Infographics — Scannable Visual Storytelling

The social-shareable, blog-embed, single-image explainer channel. Designed to survive thumbnail rendering, LinkedIn timelines, X cards, and README READMEs — where the viewer gets ~2 seconds to decide whether to engage.

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission, universal rules, and channel map. Closely related: [`channels/raster.md`](raster.md) (final export), [`channels/svg.md`](svg.md) (vector primitives), [`channels/science.md`](science.md) (stats reporting that often feeds the data), [`channels/style-guides.md`](style-guides.md) (brand tokens).

## When to use

- Single-image explainers for social (LinkedIn, X, Pinterest, Instagram)
- Blog hero images that communicate the post's thesis in one frame
- README top-of-file shareables
- Conference poster summaries
- Internal one-pagers for decks (when a whole slide reduces to one visual)

If the target is a paper figure with a caption, use [`channels/science.md`](science.md) instead — different constraints, different substrate.

## Deterministic, editable, auditable

This channel ships reproducible SVG (with optional raster export). The K-Dense `infographics` skill (which this channel borrows structure from) generates raster via Nano Banana Pro and scores via Gemini 3 Pro — a different path, kept separate.

- **Editable.** One wrong number or font swap — edit the source, re-render. AI regeneration produces a different artifact every time.
- **Auditable.** Every color and text element runs through `muriel/contrast.py` for 8:1 WCAG compliance. Raster AI output is opaque to that check.
- **Reproducible.** The generator script ships alongside the artifact. Re-render at a new size or with updated numbers months later.
- **On-brand.** Brand tokens apply at render time, not as a post-hoc prompt-engineering problem.

AI image generation lives in other skills (iblipper for animated typography, muriel's raster channel for static AI-as-tool workflows).

## The ten types

Taxonomy borrowed from [K-Dense infographics](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/infographics/SKILL.md) (MIT). Each type suggests a structure; pick the one that matches the message, don't force data into the wrong shape.

| # | Type | Purpose | Layout patterns | Muriel examples |
|---|------|---------|----------------|-----------------|
| 1 | **Statistical** | Present quantitative findings, comparisons, survey results | Single-stat hero / multi-stat grid / chart-centric / comparison bars | Scrutinizer validation numbers, AdSERP dwell-time results |
| 2 | **Timeline** | Chronological events, milestones, project phases | Horizontal / vertical / winding / circular | Vision-science lineage, project milestones, release history |
| 3 | **Process** | Step-by-step workflows, instructions | Vertical cascade / horizontal flow / circular / branching | Scrutinizer rendering pipeline (LGN → V1 → V4 → DoG) |
| 4 | **Comparison** | Side-by-side options, pros/cons, competitive analysis | Two-column split / table / Venn / feature matrix | Fovea vs. periphery, Scrutinizer vs. existing simulators |
| 5 | **List** | Tips, facts, key takeaways | Vertical list / two-column / icon grid / cards | "Ten things your peripheral vision misses" |
| 6 | **Geographic** | Location-based data, regional statistics | Full map / map-with-sidebar / regional / multi-map | Participant geography for multi-site studies |
| 7 | **Hierarchical** | Levels, priority, organizational structure | Pyramid / inverted / org chart / stacked blocks | Visual cortex hierarchy (V1 → V4 → IT), research priorities |
| 8 | **Anatomical** | Complex systems via familiar visual metaphor | Central-image-with-callouts / exploded / cross-section / before-after | Eye anatomy, retinotopic cortex map, device diagrams |
| 9 | **Resume** | Professional achievements, skills, experience | Single column / two column / header-focus / modular | Speaker bios, about pages, portfolio summaries |
| 10 | **Social Media** | Platform-optimized shareable content | Square / vertical / carousel / quote card | Kevin-Weil-style LinkedIn shares, X cards |

Hybrid is fine and often better. The Scrutinizer foveation explainer (see Recipes) is **Anatomical + Statistical + Comparison** stacked vertically in a social-media portrait format.

## Layout patterns

| Pattern | Best for | Reading path |
|---------|----------|--------------|
| **F-pattern** | Text-heavy, lists, articles | Across top → across subhead → down-left spine. Matches Western reading. |
| **Z-pattern** | Minimal, landing-page, single message | Top-left → top-right → diagonal → bottom-right. Works for 4 key zones. |
| **Single column** | Mobile-first, scrolling, process | Top → bottom. Portrait social-first. Use for the Scrutinizer explainer pattern. |
| **Multi-column** | Comparisons, pros/cons, dual category | Side-by-side. Share header and footer. |
| **Grid** | Equal-weight items, icon collections, stat arrays | Scannable, equal importance. 2×2, 3×3, 2×3. |
| **Modular / cards** | Mixed content weights, dashboard, magazine | Varied cell sizes. Modern, flexible. |

**Muriel default for LinkedIn/X/Pinterest:** single-column portrait (1080×1920 or 1080×1350). The vertical stack matches mobile scroll behavior; every block can be understood without seeing its neighbors.

## Color

Three-layer discipline, in order of authority:

### 1. Universal rule (non-negotiable): WCAG 8:1 on all text

Muriel's universal rule is stricter than K-Dense's 4.5:1. Every text element must hit 8:1 against its immediate background. Run `python -m muriel.contrast artifact.svg` before shipping. Decorative elements (grid lines, axis ticks, borders) drop to the ≥55/255-on-dark-background rule.

### 2. Named colorblind-safe palettes

Ship as muriel constants. Use when the infographic has ≥3 categorical colors. Derived from K-Dense's references:

| Palette | Colors | Origin | When |
|---------|--------|--------|------|
| **Wong** (Okabe-Ito) | `#000000` `#E69F00` `#56B4E9` `#009E73` `#F0E442` `#0072B2` `#D55E00` `#CC79A7` | Bang Wong, scientific viz standard | Default for science-adjacent categorical data |
| **IBM** | `#648FFF` `#785EF0` `#DC267F` `#FE6100` `#FFB000` | IBM Carbon colorblind-safe | Corporate / tech contexts |
| **Tol** | `#332288` `#88CCEE` `#44AA99` `#117733` `#999933` `#DDCC77` `#CC6677` `#882255` `#AA4499` | Paul Tol, 12-color qualitative | When you need more than 8 categories |

Test every palette in a colorblindness simulator before shipping. Never convey meaning through color alone — pair with shape, pattern, or text label.

### 3. Brand tokens (when available)

If the target project has a `brand.toml` (see [`channels/style-guides.md`](style-guides.md)), load it and derive from there. For scrutinizer-www specifically the brand is slate-900 background (`#0f172a`), Inter, indigo-500 accent (`#6366f1`), indigo-400 links (`#818cf8`). See the Scrutinizer recipe below.

### 60-30-10 distribution

Within any palette:

- **60% dominant** — backgrounds, large surfaces. Usually neutral.
- **30% secondary** — supporting elements, most text, most fills.
- **10% accent** — the brightest / most saturated color. Reserved for the single most important element.

Break this rule and the image reads as chaos. Honor it and the eye knows where to land first.

## Typography

One font family per artifact. Vary weight and size, not family. K-Dense recommends 2-3 fonts; muriel's universal rule is stricter — **one** family, and only bring in a second if you have a specific reason (a mono family for numerics, a display family for a hero number).

Size tiers, for a 1080×1920 portrait infographic:

| Role | Size | Weight |
|------|------|--------|
| Hero stat (the one big number) | 180-240px | Extrabold / Black |
| Main title | 72-96px | Bold |
| Section headers | 48-56px | Semibold |
| Body / callout text | 28-36px | Regular |
| Axis / small labels | 20-28px | Regular |
| Attribution / URL footer | 18-22px | Regular / Light |

Left-align body. Center-align hero numbers and main titles. Never center-align body text blocks — eye-tracking fails at the left edge.

Recommended families (in order of muriel preference):

1. **Inter** — neutral sans, superb at small sizes, weights 100-900, free. Default for most muriel artifacts. Matches scrutinizer-www.
2. **IBM Plex Sans** — slightly warmer, matches IBM palette, ships with mono variant.
3. **Atkinson Hyperlegible** — Braille Institute's open font, engineered for low-vision readers. Use when accessibility is the headline virtue.

Avoid: Light weights below 14pt. Condensed faces for body text. Any font where the lowercase-l and uppercase-I are identical (Helvetica's classic failure). All-caps paragraphs.

## The story arc

Every infographic — even a single-screen shareable — follows introduction / body / conclusion:

- **Intro (10-15% of surface)** — hook headline, hero stat or hero image, enough context to tell the viewer why to care.
- **Body (70-80%)** — the substance. Data, diagrams, mechanisms. Sections visually separated by rules, spacing, or cards.
- **Conclusion (10-15%)** — the takeaway, call-to-action, attribution, URL.

Missing the conclusion is the most common failure mode. An infographic without a "what you do with this" leaves the viewer unanchored.

## Quality rubric

Adapted from K-Dense's 5-point rubric. Muriel ships at **≥8.0 / 10** before the image leaves the filesystem. Below that, iterate or discard — don't ship marginal work.

| Dimension | Weight | What passes |
|-----------|--------|-------------|
| **Visual hierarchy & layout** | 2 | Single clear first-read focal point. Reading path obvious without instruction. 60-40 visual/text ratio. White space matches element groupings. |
| **Typography & readability** | 2 | One family (or one + mono). Hero element obviously dominant. No text below 18px. Left-aligned body. 8:1 contrast everywhere. |
| **Data-viz prominence & honesty** | 2 | Data is a first-class citizen, not decoration. Y-axis starts at zero for bars. ≤7 pie slices. No 3D. Direct labels over legends. Numbers sized readable. |
| **Color accessibility** | 2 | Colorblind-safe palette. 60-30-10 distribution. Never color-alone for meaning. WCAG 8:1 text audit passes. |
| **Overall professional impact** | 2 | The artifact reads as an intentional design artifact, not a template fill. Would survive sharing by someone not paid to share it. |

Scoring: assign 0-2 per dimension (0 = fails, 1 = passes but mid, 2 = strong). Sum to 10. If any single dimension is 0, the infographic does not ship regardless of total score.

## Rendering pipeline

### 1. Specify in Python, emit SVG

Write a build script that emits SVG from structured input. Standard library only where possible. Save the script alongside the output — per muriel's Reproducible rule.

```python
# build_<subject>.py
WIDTH, HEIGHT = 1080, 1920  # Portrait social-first
SLATE_900 = "#0f172a"
CREAM     = "#e6e4d2"
INDIGO_400 = "#818cf8"
# ... palette ...

def emit_svg(data: dict) -> str:
    # Return a complete SVG string
    ...

if __name__ == "__main__":
    import json, pathlib
    data = json.loads(pathlib.Path("data.json").read_text())
    out = pathlib.Path(__file__).parent / "explainer.svg"
    out.write_text(emit_svg(data))
```

### 2. Audit with `muriel/contrast.py`

```bash
python -m muriel.contrast explainer.svg
```

Exit 0 = 8:1 passes for all text. Exit 1 = violations reported. Exit 2 = malformed SVG.

### 3. Raster export (for platforms that don't accept SVG)

```bash
# cairosvg (preferred, pip-installable)
python -c "import cairosvg; cairosvg.svg2png(url='explainer.svg', write_to='explainer.png', output_width=1080)"

# or rsvg-convert (Homebrew: librsvg)
rsvg-convert -w 1080 explainer.svg -o explainer.png

# or Inkscape CLI (cross-platform but heavy)
inkscape explainer.svg --export-type=png --export-filename=explainer.png -w 1080
```

For LinkedIn specifically: export at 1080×1920 PNG (or 1080×1350 if the platform crops). Keep the SVG as the source of truth.

### 4. Save data separately

If the infographic is data-driven (a set of stats, a timeline of events), keep `data.json` separate from the build script. Updating numbers becomes a data edit, not a code edit.

## Recipes

### LinkedIn portrait social-share (1080×1920)

The canonical muriel infographic. Single-column layout, hero at top, 2-3 body panels, conclusion + URL at bottom.

**Grid discipline:** 60px margin on left and right. Section spacing 48px. Horizontal rules at `cream-900 alpha 0.15` thickness 1.

**Hero zone:** 0-400px (y-axis). Title left-aligned, hero stat (if any) right-aligned or centered underneath.

**Body zone:** 400-1680px. Three panels, each ~420px tall. Panel title left-aligned at 48px, panel content below at 400px effective height.

**Footer zone:** 1680-1920px. Tagline + URL + attribution. Right-aligned or centered. Never hero-sized.

### Scrutinizer foveation explainer

See `assets/explainers/foveation.svg` in scrutinizer-www. Source script in the same directory. Subject: foveation + cortical magnification. Type: Anatomical + Statistical + Comparison hybrid.

Key claims (drawn from canonical scrutinizer-www copy — safe to reuse):

- "Only ~2° of your visual field is sharp. The rest is peripheral — blurred, desaturated, crowded."
- "Half the visual cortex processes the central 2° of vision."
- "Color narrows in the periphery. S-cones are sparse outside the fovea; parvocellular resolution drops with eccentricity."
- "Crowding: in the periphery, objects aren't invisible — they're unidentifiable."

Palette: scrutinizer-www canonical — slate-900 `#0f172a` background, white primary text, indigo-500 `#6366f1` accent, indigo-400 `#818cf8` for links, cyan-400 `#22d3ee` for secondary data series. Font: Inter.

## Anti-patterns

- **AI-generated background textures that are "kind of noise."** If you can't describe the texture in one sentence (what does it represent?), delete it. Decoration without information is chart junk.
- **Every number the same size.** Hero numbers should dominate. If all numbers are the same size, nothing is the hero.
- **Centered body paragraphs.** Readable only in short headlines. Body text gets left-aligned, always.
- **Text over photography without a mask.** If you're going to place text on imagery, compute the local contrast or add a mask. Universal rule: 8:1 everywhere, including over photos.
- **Rainbow colormap for a categorical variable.** Categorical wants discrete, distinguishable hues — Wong or Tol. Rainbow implies order.
- **Title + subtitle + intro paragraph + body** — the intro should be the title. Subtitle + body is enough. An extra layer of text before the data just delays the first-read.
- **Legend when direct labels would work.** If you can label the lines on the chart directly, do it. Legends force the eye to ping-pong.
- **No attribution / no URL.** Without a footer, the infographic dies on re-share. Always sign the work and include the canonical URL.
- **Accent lines under titles.** K-Dense flagged this as an AI-generated-deck tell. Muriel rejects it. Use whitespace for separation; reserve rules for genuine content boundaries.
- **Decorative emojis in the hero.** Muriel's universal rules prohibit emoji except on explicit user request. Ship without.

## Prior art / upstream

- [K-Dense scientific-agent-skills — infographics](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/infographics/SKILL.md) (MIT). Source for the 10-type taxonomy, 8-style-preset concept, 5-point quality rubric, 60-40 visual/text rule, 60-30-10 color rule, and colorblind-safe palettes (Wong/IBM/Tol). K-Dense's pipeline (Nano Banana Pro + Gemini scoring) is explicitly **not** adopted — muriel's lane is deterministic SVG.
- [K-Dense — design_principles.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/infographics/references/design_principles.md). Long-form principles reference. Useful when debating a specific layout choice in an artifact review.
- [K-Dense — color_palettes.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/infographics/references/color_palettes.md). Industry-style palettes (Corporate / Healthcare / Tech / Nature / Education / Marketing / Finance / Nonprofit). Reference when adapting muriel output to a brand that doesn't have its own tokens.
- [Bang Wong — "Points of view: Color blindness"](https://www.nature.com/articles/nmeth.1618) (Nature Methods, 2011). Primary source for the Okabe-Ito palette.
- [Paul Tol — Colour Schemes](https://personal.sron.nl/~pault/). Primary source for the Tol qualitative / sequential / diverging palettes.
