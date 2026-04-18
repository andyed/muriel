---
name: muriel
description: "Next-gen visual-production skill for LLMs — ten channels of tool-use recipes (raster, SVG, web, interactive, video, science, gaze, terminal, dimensions, style-guides), a two-tier brand-token schema with motion, anti-patterns per channel, a multi-constraint solver that enforces 8:1 contrast at render time, and a vision-model critique agent grounded in Tufte / Bertin / Gestalt. Use when the user needs any visual artifact for human eyes."
user-invocable: true
---

# muriel — next-gen visual-production skill for LLMs

muriel is a free, scriptable skill that teaches an LLM agent to produce every visual artifact a researcher-designer-engineer ships — from text source files that diff in git and regenerate from data. Ten named channels (raster, SVG, web, interactive, video, terminal, heatmaps, gaze, science, dimensions) each with rules and anti-patterns, four aesthetic vocabularies, a two-tier brand schema with motion tokens, a multi-constraint solver that keeps 8:1 contrast and OLED palette active at render time, and a vision-model critique agent grounded in Tufte / Bertin / Gestalt / Reichle / scanpath research that names what's wrong before ship.

## Channels

Each channel has a dedicated subfile with deep recipes, tooling, and lessons. This top-level index is the map; the subfiles are the territory.

| Channel | Format | Deep dive |
|---|---|---|
| **Raster** | PNG/JPG | [`channels/raster.md`](channels/raster.md) — Pillow, `typeset.py`, store dimensions, fonts, inline pattern |
| **Vector** | SVG | [`channels/svg.md`](channels/svg.md) — `svgwrite`, `cairosvg`, Mermaid, Excalidraw, `viewBox` theming |
| **Web** | HTML + CSS | [`channels/web.md`](channels/web.md) — marginalia, pandoc filter, Playwright/weasyprint capture, data-URI |
| **Interactive** | WebGL / Canvas / D3 | [`channels/interactive.md`](channels/interactive.md) — single-file scaffold, PermalinkManager, CodePen, Observable |
| **Video** | MP4 / GIF | [`channels/video.md`](channels/video.md) — ffmpeg + `desktop-control` + tooltip burn + editing recipes |
| **Terminal** | Unicode | [`channels/terminal.md`](channels/terminal.md) — `chart.py` bar charts, sparklines, tables |
| **Density viz** | PNG | [`channels/heatmaps.md`](channels/heatmaps.md) — Tobii-style Gaussian overlays |
| **Gaze plots** | PNG / SVG / JS | [`channels/gaze.md`](channels/gaze.md) — scanpath, bubble, AOI timeline, saccade rose |
| **Science** | matplotlib + LaTeX | [`channels/science.md`](channels/science.md) — rcparams, stats reporting, notebook editorial, paper figures |
| **Dimensions** | *cross-channel reference* | [`channels/dimensions.md`](channels/dimensions.md) — social cards, device footprints, viewport tiers, video, paper/print, favicons, scale factors |
| **Style guides** | *brand schema* | [`channels/style-guides.md`](channels/style-guides.md) — brand.toml schema, loader, rule enforcement, CSS/matplotlibrc derivation, example brand.toml files |


## Aesthetic vocabularies

Design grammars worth naming explicitly when a project's visual register calls for something specific. A menu of established traditions — borrow their conventions, don't reinvent them.

- [`vocabularies/fui.md`](vocabularies/fui.md) — **Fantasy / Fictional User Interface.** Sci-fi HUDs. Perception NYC, Territory Studio, Ash Thorp, GMUNK lineage. Thin strokes, mono numerics, staggered reveals, radial geometry, restrained palettes.
- [`vocabularies/visible-language.md`](vocabularies/visible-language.md) — **Visible Language Workshop.** The MIT Media Lab design tradition (Cooper, Small, Ishizaki, Maeda → Processing → pretext). Information landscapes, multi-scale typography, typography as data structure. Contemporary substrate: [`@chenglou/pretext`](https://chenglou.me/pretext/). See also `channels/interactive.md` for the pretext API and the `pretext-coachella` reference exemplar.

Additional vocabularies (Swiss grid, editorial, brutalist, newsprint) can be added here without restructuring the skill.

---

## Universal rules

Codified from per-project bug fixes — apply to **every** channel:

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

For data-driven channels (raster plots, SVG, interactive JS, science), apply Tufte/Bertin/CRAP via three high-leverage patterns:

- **Small multiples** — same chart, repeated, with one variable changing. Lets the eye compare without re-anchoring. Reach for this whenever you'd otherwise build a complex multi-series single chart.
- **Linked displays / brushing** — selecting in one view highlights the corresponding marks in every other view. D3's strength. Perfect for exploratory dashboards, phase-segmented timeline explorers, and any "facets that share a record set" interface.
- **Semantic zoom** — representation *changes* by zoom level, not just scale. Overview shows aggregate; mid zoom shows clusters; deep zoom shows individual records. Different from optical zoom. Pairs with linked displays for sector-explorer interfaces.

Reference: [`docs/PERMUTE.md`](docs/PERMUTE.md) — full Tufte/Bertin/Gestalt/CRAP framing.

## Interaction design grounding

When building interactive demos or UI affordances around the visuals, the design choices have empirical anchors:

- **Fitts's Law** — pointing time = `a + b·log₂(D/W + 1)`. Big targets close to the cursor are fast; small targets far away are slow. Implication: primary controls go large and near the user's current attention point. Fisheye expansion is Fitts's Law made visible.
- **Hick's Law** — choice time = `a + b·log₂(n + 1)`. Decision time grows logarithmically with options. Implication: collapse n>7 options into hierarchy or progressive disclosure.
- **Fisheye menus** — focus+context lens that expands the item under the cursor while compressing peripheral items (the user's own MS Human Factors thesis, Clemson). The trick: each item gets a *guaranteed minimum size* below the lens floor so distant items remain clickable, not just visible.
- **Marginalia callouts** — typographic affordances (pull quotes, asides, margin notes) are the editorial equivalent of fisheye: they create a visual hierarchy that lets the eye sample without losing the through-line.
- **Cortical magnification & foveation** — the retinal-side reason fisheye works at all. Cite primary sources (Curcio 1990, Freeman & Simoncelli 2011) when explaining *why* focus+context isn't a UI gimmick.
- **"It is impossible to separate the visual design from the design of the interface."** — David Small, [*Navigating Large Bodies of Text*](https://smg.media.mit.edu/library/small1996.html) (IBM Systems Journal, 1996). Visual grammar and interaction grammar are the same grammar. Every choice about how text renders is a choice about how people navigate it — and vice versa. See [`vocabularies/visible-language.md`](vocabularies/visible-language.md) for the full MIT Media Lab lineage this is drawn from.

Use these as design rationale in figure captions and blog posts — the vocabulary is precise, the laws are quantified, and the lineage runs from psychophysics through typography to interaction design.

---

## When to use

Whenever the user needs a visual artifact for human eyes — store assets, paper figures, blog post explainers, video demos, terminal output, scientific plots, infographics, screenshots, gaze visualizations. Invoke with `/muriel` followed by what's needed.

## Channel reference map

When the task lands in a specific channel, read the corresponding subfile *first* before executing:

| If the task is… | Read |
|---|---|
| App store assets, icons, banners, wordmarks, Pillow compositing | `channels/raster.md` |
| Paper figures, data-driven diagrams, SVG theming, Mermaid, Excalidraw | `channels/svg.md` |
| Blog posts, marginalia pages, pandoc → HTML/PDF, web capture, data-URI | `channels/web.md` |
| Interactive demos, WebGL/Canvas/D3, CodePen, Observable, permalink state | `channels/interactive.md` |
| Product demo videos, ffmpeg, tooltip burn, GIF generation | `channels/video.md` |
| Unicode bar charts, sparklines, terminal output, README tables | `channels/terminal.md` |
| Tobii-style density heatmaps from fixation data | `channels/heatmaps.md` |
| Scanpath plots, AOI timelines, bubble scanpaths, saccade roses | `channels/gaze.md` |
| matplotlib figures, stats reporting, notebook editorial, LaTeX hooks | `channels/science.md` |
| "What size should this be?" — social card / device / viewport / paper / video dimensions | `channels/dimensions.md` |
| Loading a brand's design tokens, enforcing brand ownership rules, deriving CSS / rcparams from a brand | `channels/style-guides.md` |
| Sci-fi HUD aesthetic, FUI grammar, Territory/Perception lineage | `vocabularies/fui.md` |
| Multi-scale typography, information landscapes, pretext, Cooper/Small lineage | `vocabularies/visible-language.md` |

For a multi-channel task (e.g., a blog post with an interactive demo captured as a paper figure), read the relevant subfiles in order of primary channel first.

---

## TODO

### Raster
- [x] **Drop shadow with blur** — Implemented via `ImageFilter.GaussianBlur` in `render_text()` shadow effect.
- [x] **Template system** — [`muriel/typeset.py`](muriel/typeset.py) ships `amazon-icon`, `amazon-small-icon`, `tvos-topshelf`, `play-feature` templates via `render_asset(template=...)`.
- [x] **Batch from JSON** — `generate_from_manifest("assets.json")` in `typeset.py`.
- [ ] **Multi-line text layout** — Auto-wrap long text with configurable max-width, line-height, and alignment.
- [ ] **Curved/arc text** — Text along a circular path for badges, seals, and circular icon borders.
- [ ] **Gradient text fill** — Linear/radial gradient fills inside letterforms.
- [ ] **Brand color extraction** — Auto-extract dominant colors from a background image.

### Hero-shot compositor (raster)

Device-framed product shots for app stores, blog heroes, social cards, case studies. The "classic marketing hero" channel that Photoshop and tools like Shottr / Xnapper own. muriel's version is brand-token-driven, reproducible, and composable.

- [ ] **`muriel/tools/heroshot.py`** — inputs: source screenshot(s), target dimension (via `muriel.dimensions`), brand.toml, title text. Output: ship-ready PNG that composites: isotropic scaling (no anamorphic distortion), optional 3D CSS-skew for product-at-angle effect, title typography from the brand, device bezel / browser chrome / generic frame, brand-consistent border.
- [ ] **Title placement rules** — above / below / overlaid, auto-chosen by aspect ratio; respects `brand.toml` typography and 8:1 contrast on the title vs. the hero's dominant luminance.
- [ ] **Border/frame library** — iPhone 15/16 silhouettes, browser chrome (Chrome / Safari), device-agnostic thin bezel, generous whitespace frame. Contributors add SVG-source bezels to `templates/bezels/`.
- [ ] **Skew presets** — `skew='none' | 'gentle' | 'aggressive' | 'product-3d'`. Gentle = ±3° rotation; aggressive = perspective transform with vanishing point; product-3d = Mercury-ad-style with drop shadow. All respect `motion_preference` if the hero is animated.
- [ ] **HTML variant** — generate live HTML with CSS 3D transforms so the hero can be embedded interactively in a blog post *or* captured via `muriel.capture` as a static PNG. Same tokens drive both paths.
- [ ] **Preset library** — `heroshot.app_store('iphone', screenshot, title, brand)`, `heroshot.blog_hero('browser', screenshot, title, brand)`, `heroshot.social_card('tight', screenshot, caption, brand)`.

### SVG
- [ ] **Gaze ribbon primitive** — `typeset.svg.gaze_ribbon(fixations)` reusable across gaze studies.
- [ ] **Phase overlay primitive** — Colored band generator from phase-segmented gaze data.
- [ ] **Phase-timeline diagram primitive** — Multi-band horizontal timeline.
- [ ] **Excalidraw → clean-export pipeline** — Batch re-export with `roughness:0`, Helvetica, solid fills.
- [ ] **Mermaid CLI wrapper** — Themed output matching marginalia `--mg-*` palette.

### Interactive JS
- [ ] **Extract shared `permalink.js`** — Standalone PermalinkManager implementation for demos (URL hash ↔ parameter state).
- [ ] **Demo loader snippet for marginalia** — `<mg-demo src="...">` custom element that lazy-loads an iframe.
- [ ] **Single-file demo bundler** — Inline CSS/JS/images as data URIs to produce a standalone `.html`.

### Web rendering & static capture
- [x] **Responsive viewport-sweep capture** — Shipped as `muriel/capture.py`. `capture_responsive(url, tiers=..., output_dir=...)` writes retina PNGs for every tier in one call. CLI: `python -m muriel.capture <url>`. Playwright optional dependency.
- [ ] **Small-multiples capture script** — Loop a demo across parameter values via URL hash, screenshot each, assemble into a grid. (Related to `capture.py` but captures *parameter* sweeps, not *viewport* sweeps.)
- [ ] **Marginalia + weasyprint paper template** — `@page` rules for A4 + letter, figure captions, bibliography.
- [ ] **Playwright device-frame compositor** — Replace manual Photoshop mockups with real HTML-rendered device frames.

### Pandoc + marginalia
- [x] **`marginalia/pandoc/marginalia.lua` filter** — Shipped as commit 4c66c16 on the marginalia repo.
- [x] **`marginalia/pandoc/template.html`** — Shipped alongside filter.
- [x] **US Constitution example** — Shipped at `marginalia/pandoc/examples/us-constitution.md`.
- [ ] **Markdown → PDF via marginalia + weasyprint** — End-to-end pipeline for paper drafts with marginalia styling preserved.

### Science
- [x] **`channels/science.md` subsection** — rcparams defaults, stats reporting, notebook editorial, LaTeX hooks, worked recipes.
- [x] **`muriel/matplotlibrc_dark.py` + `_light.py`** — Both rcparams blocks shipped as importable modules with graceful fallback when matplotlib is absent. Light variant matches the F explainer warm editorial palette.
- [x] **Statistical reporting helpers** — `muriel/stats.py` ships `format_comparison`, `format_null`, `format_correlation`, `format_auc`, `format_chi2`, `format_exploratory`, `cohens_d`, `cohens_d_paired`, `fisher_ci`, `apa_number`, `format_p`, `format_ci`. Standard library only. Enforces U+2212 minus signs, APA leading-zero stripping, detection-limit phrasing for nulls.
- [x] **`muriel/contrast.py` WCAG audit** — Standard-library-only module with `contrast_ratio`, `check_text_pair`, `audit_svg`, and a `python -m muriel.contrast file.svg` CLI (exit 0 / 1 / 2 for CI use). Classifies CSS selectors as text / decorative / ambiguous via substring hints. Used for the 8:1 compliance audit that caught three failing text roles in word-fingerprints and four failing tokens in marginalia's light theme.
- [x] **`muriel/dimensions.py` screen-size constants** — `Size` / `Device` / `PaperSize` NamedTuples with aspect labels and scale methods. 34 dotted-name registry entries (social cards, video, viewports), 17 device footprints with physical + CSS + scale factor, 5 paper sizes with DPI-aware pixel conversion, `figsize_for()` helper for 7 academic venues (CHI/ACM/IUI/IEEE/PNAS/Nature/LNCS), CLI self-test. Paired with `channels/dimensions.md`.
- [ ] **Figure caption template tool** — Generate caption skeletons from a figure spec dict.
- [ ] **Pre-registration boilerplate generator** — Common methods-section templates with fill-in slots.
- [ ] **`muriel/contrast.py` inline-fill pass** — Current audit only walks `<style>` CSS; add a second pass that walks `<text fill="…">` attributes for SVGs that set fills inline.
- [ ] **`muriel/contrast.py` marginalia-token audit** — Add a `audit_marginalia_tokens()` helper that reads `marginalia.css` and verifies every `--mg-*` custom property against both theme backgrounds.

### PERMUTE — elevate from docs/ to a cross-channel operator

PERMUTE currently lives as [`docs/PERMUTE.md`](docs/PERMUTE.md) (Tufte/Bertin/Gestalt/CRAP principles applied as transformation operators). That framing is channel-agnostic, not ASCII-specific — it should sit alongside FUI / Visible Language / PixiJS / Kinetic Typography as a first-class grammar.

- [ ] **Move to `vocabularies/permute.md`** — PERMUTE as a named design grammar: data artifacts iterate through principled transformations (chart-type remap, sort-order remap, small-multiples, linked displays, semantic zoom, categorical ↔ sequential ↔ diverging color, aspect-ratio remap, medium remap).
- [ ] **`muriel/permute.py`** — Python helper that takes a data spec + permutation axis and emits multiple variants. Channel-agnostic; each channel's renderer is a backend. `permute(data, axis="chart_type")` → one output per viable chart type; `permute(data, axis="medium")` → terminal / raster / SVG / interactive D3.
- [ ] **`## Permutations` section per channel** — enumerate which permutations each channel supports, as testable assertions.
- [ ] **`muriel-permute` agent (optional)** — given a data artifact, rank alternative presentations against the communicative intent. Complements `muriel-critique`: one names what's wrong, the other proposes what would be better.

### Style guides (brand schema)

- [ ] **OKLCH in `brand.toml`.** Today `colors.accent = "#50b4c8"` only parses hex. Add an OKLCH path so brands can write `colors.accent = "oklch(65% 0.15 220)"` — hex stays supported; OKLCH becomes recommended for palettes where lightness ramps matter (muted → vibrant at constant hue). Same `StyleGuide` object internally; emit via `to_css_vars(color_space='oklch'|'hex')`. Inspiration from [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (Apache-2.0), which recommends OKLCH for perceptual uniformity in brand-palette design.

### Web (editorial variant)
- [x] **Light editorial palette documented** — `channels/web.md` now has a section on the F-explainer pattern, with the `.outer-note` / `.stats-detail` / `.has-dropcap` / staged-h2 extensions catalogued.
- [ ] **Generalize `.outer-note` and `.stats-detail` back into marginalia** — Currently F-explainer-only; worth promoting to the main library if a second project adopts them.
- [ ] **Build-script variant of the pandoc bridge** — Node script using `marginalia-md.js` for projects that prefer browser-side conversion over pandoc.

### Image-production pipeline (LLM imagegen + enhancement + engines)

The canonical "raster without hand-compositing" path — not built yet; roadmap target. Pipeline shape:

```
prompt → [imagegen + brand.toml] → PNG → [enhance + target-tier] → [contrast.audit] → ship
```

- [ ] **`channels/imagegen.md`** — dedicated channel for LLM-generated raster: multi-provider wrapper (Gemini, DALL-E, Flux, Nano Banana, Ideogram), brand-constraint-aware prompting, contrast validation on output, reproducibility (prompt+seed stored alongside PNG).
- [ ] **`muriel/imagegen.py`** — provider abstraction behind one API. Injects the active `brand.toml` tokens (palette, typography, rules) into the system prompt as generation constraints. Returns a dataclass with `path`, `prompt`, `seed`, `provider`, `model`, `timestamp` so every output is fully reproducible.
- [ ] **Post-generation audit hook** — auto-run `muriel.contrast.audit_svg`-equivalent on raster outputs (LLM imagegen rarely clears 8:1 without prompting); surface a "regenerate or accept" decision to the caller.
- [ ] **`muriel/tools/enhance.py`** — upscaling + artifact removal wrapper (Real-ESRGAN or equivalent). Platform-aware via the dimensions registry: `enhance(img, target='twitter.instream')` both resizes *and* enhances in one call. Pairs with `muriel.dimensions` named tiers.
- [ ] **CLI:** `python -m muriel.imagegen "A foveated gaze heatmap over a SERP" --brand examples/muriel-brand.toml --dims twitter.instream --enhance`
- [ ] **Recipe in `channels/raster.md`** — full worked pipeline from prompt through ship-ready PNG, citing each step's helper.
#### Engine adapters

muriel is the constraint layer; the engine that produces pixels is swappable. Each adapter injects the active `brand.toml` into the engine's prompt/config, polls async jobs, and routes the output back through `muriel.contrast.audit` before ship.

**Default engines (free, already part of muriel):**
- `muriel.typeset` — Pillow compositing with brand tokens. Ships today; no TODO.
- `muriel.chart` — Unicode terminal charts. Ships today.

**Local / free engine adapters (TODO, high priority):**
- [ ] **`muriel/engines/flux_local.py`** — Flux via a local runtime (ComfyUI, diffusers, or ollama when supported). Zero cloud cost.
- [ ] **`muriel/engines/sdxl_local.py`** — Stable Diffusion XL via `diffusers` or ComfyUI. Zero cloud cost.
- [ ] **`muriel/engines/real_esrgan.py`** — local upscaling (2×/4×) via Real-ESRGAN PyTorch checkpoints. Free alternative to commercial upsamplers.
- [ ] **`muriel/engines/gemini.py`** — Google Gemini image gen via free tier + pay-as-you-go. Lowest activation energy for a cloud engine.

**Opt-in paid engine adapters (TODO, subscription required):**
- [ ] **`muriel/engines/firefly.py`** — [Adobe Firefly API](https://developer.adobe.com/firefly-services/docs/firefly-api/). Real capability (image5, creative upsampler, precise/adaptive composite, custom-brand models) but requires Adobe CC + Firefly credits per call. Ships as an optional engine; users without subs fall through to a free engine.
- [ ] **`muriel/engines/photoshop.py`** — local PS automation (UXP / ExtendScript / batch-actions). Free for users who already have Photoshop; still paid in aggregate (CC subscription).
- [ ] **`muriel/engines/dalle.py`** / **`muriel/engines/ideogram.py`** — optional commercial alternatives.

**Engine selection in `brand.toml`:**
- [ ] Add `[engine]` block: `preferred = "pillow"`, `fallback = ["flux_local", "gemini"]`, optional `paid_ok = false`. Let the brand declare its defaults; respect `paid_ok = false` to never call a metered endpoint.

**Positioning:** muriel stays free-first and engine-agnostic. The differentiator is not "we integrate with Firefly" (many will); it's that the brand-tokens + contrast-audit + critique-agent layer is **the same** whether the engine is Pillow locally, Flux in a GPU container, Gemini's free tier, or a paid Firefly custom model. The constraint discipline is the product.

#### Authoring engines (emit editable source files)

Different direction from render engines — these produce files the user can *refine further* in their preferred tool, with muriel's brand tokens already applied to layer names, groups, styles, type properties, and export settings.

- [ ] **`muriel/authoring/psd.py`** — emit a layered `.psd` from a brief + brand.toml. Uses `psd-tools` or a similar library. Standalone (does not require PS to be running). Brand colors become fill layers, type layers use the brand's typography stack, groups follow the brand's semantic taxonomy. Open the output in Photoshop for manual refinement.
- [ ] **`muriel/authoring/photoshop_live.py`** — script an already-running Photoshop instance via UXP or ExtendScript. Requires PS to be open; useful when the user is actively working and wants muriel to inject a brand-compliant composition into their current document.
- [ ] **`muriel/authoring/figma.py`** — Figma Files API to create / update designs. Brand tokens map to Figma variables; muriel writes a starter file the team can iterate on. Free tier has limits; works for individual users and small teams.
- [ ] **`muriel/authoring/canva.py`** — Canva Connect API. Produces a Canva design with brand palette applied. Useful for marketing collateral workflows where the team continues editing in Canva.
- [ ] **`muriel/authoring/affinity.py`** — Affinity scripting (.afdesign, .afphoto). Free-to-own alternative to PSD.

Authoring engines are complementary to render engines: render when you want a final PNG; author when you want a source file the user will continue to edit. Brand tokens apply identically across both paths.

Reference material (not direct swipes — shape inspiration):
- [sanjay3290/ai-skills/imagen](https://github.com/sanjay3290/ai-skills/tree/main/skills/imagen) (Apache-2.0) — minimal Gemini image-gen wrapper; informs the provider shape.
- [ComposioHQ/awesome-claude-skills/image-enhancer](https://github.com/ComposioHQ/awesome-claude-skills/tree/master/image-enhancer) — enhancement-plus-platform-tier pattern.
