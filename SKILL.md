---
name: muriel
description: "A multi-constraint solver for visual production — raster, SVG, web, interactive, video, terminal, density viz, gaze, science, infographics across ten output channels plus dimensions + style-guides cross-channel references. Brand tokens, 8:1 contrast rule, and dimension constants stay active at render time. Use when the user needs any visual artifact for human eyes."
user-invocable: true
---

# muriel — Multi-channel visual production


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
| **Infographics** | SVG → PNG | [`channels/infographics.md`](channels/infographics.md) — 10 types × layout patterns × colorblind-safe palettes, deterministic SVG (not AI), 60-30-10 color / 60-40 viz:text rule, 5-point quality rubric at 8:1 |
| **Diagrams** | SVG | [`channels/diagrams.md`](channels/diagrams.md) — rhetorical primitives (2×2 matrix, N-step cycle, Venn shipped; comparison pair, funnel, stack, DAG, spectrum, pyramid, heat-grid queued). Each preset carries an epistemic precondition and an anti-prescription. |


## Aesthetic vocabularies

Design grammars worth naming explicitly when a project's visual register calls for something specific. A menu of established traditions — borrow their conventions, don't reinvent them.

- [`vocabularies/fui.md`](vocabularies/fui.md) — **Fantasy / Fictional User Interface.** Sci-fi HUDs. Perception NYC, Territory Studio, Ash Thorp, GMUNK lineage. Thin strokes, mono numerics, staggered reveals, radial geometry, restrained palettes.
- [`vocabularies/visible-language.md`](vocabularies/visible-language.md) — **Visible Language Workshop.** The MIT Media Lab design tradition (Cooper, Small, Ishizaki, Maeda → Processing → pretext). Information landscapes, multi-scale typography, typography as data structure. Contemporary substrate: [`@chenglou/pretext`](https://chenglou.me/pretext/). See also `channels/interactive.md` for the pretext API and the `pretext-coachella` reference exemplar.
- [`vocabularies/pixijs.md`](vocabularies/pixijs.md) — **PixiJS 2D WebGL/WebGPU substrate.** When Canvas/D3 runs out of headroom and Three.js is overkill. Particle-dense gaze overlays, shader-driven foveation demos, audio-reactive visuals. Pin to `^8.18`. **Lifted from [pixijs/pixijs-skills](https://github.com/pixijs/pixijs-skills) (MIT)** — they did the documentation work; we curated the relevant subset. Read upstream for depth.
- [`vocabularies/kinetic-typography.md`](vocabularies/kinetic-typography.md) — **Letters that move with intent.** Saul Bass → Kyle Cooper → Territory Studio lineage. Max contrast, strategic motion, rehearsed emotional vocabulary, SDF alpha rule. Substrate options: pretext for typographic Canvas2D animation, iblipper for a full animation-as-language pipeline, Troika SDF for 3D scenes. Invoke `/iblipper` when the output itself is the animated artifact.

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
- **Linked displays / brushing** — selecting in one view highlights the corresponding marks in every other view. D3's strength. Perfect for exploratory dashboards, OSEC phase explorers, and any "facets that share a record set" interface.
- **Semantic zoom** — representation *changes* by zoom level, not just scale. Overview shows aggregate; mid zoom shows clusters; deep zoom shows individual records. Different from optical zoom. Pairs with linked displays for the OSEC sector explorer pattern.

Reference: `~/Documents/dev/ascii-charts/docs/PERMUTE.md` — full Tufte/Bertin/Gestalt/CRAP framing.

## Interaction design grounding

When building interactive demos or UI affordances around the visuals, the design choices have empirical anchors:

- **Fitts's Law** — pointing time = `a + b·log₂(D/W + 1)`. Big targets close to the cursor are fast; small targets far away are slow. Implication: primary controls go large and near the user's current attention point. Fisheye expansion is Fitts's Law made visible.
- **Hick's Law** — choice time = `a + b·log₂(n + 1)`. Decision time grows logarithmically with options. Implication: collapse n>7 options into hierarchy or progressive disclosure.
- **Fisheye menus** — focus+context lens that expands the item under the cursor while compressing peripheral items (the user's own MS Human Factors thesis, Clemson). The trick: each item gets a *guaranteed minimum size* below the lens floor so distant items remain clickable, not just visible.
- **Marginalia callouts** — typographic affordances (pull quotes, asides, margin notes) are the editorial equivalent of fisheye: they create a visual hierarchy that lets the eye sample without losing the through-line.
- **Cortical magnification & foveation** — the retinal-side reason fisheye works at all. Inside the Math is the canonical explainer; reference it when explaining *why* focus+context isn't a UI gimmick.
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
| Social-shareable explainers, LinkedIn/X cards, README hero images, single-image infographics | `channels/infographics.md` |
| Sci-fi HUD aesthetic, FUI grammar, Territory/Perception lineage | `vocabularies/fui.md` |
| Multi-scale typography, information landscapes, pretext, Cooper/Small lineage | `vocabularies/visible-language.md` |
| Particle-dense gaze overlays, shader filters, PixiJS v8 patterns | `vocabularies/pixijs.md` |
| Animated typography, emotional motion vocabulary, Bass/Cooper/Territory lineage | `vocabularies/kinetic-typography.md` |

For a multi-channel task (e.g., a blog post with an interactive demo captured as a paper figure), read the relevant subfiles in order of primary channel first.

---

## TODO

### Raster
- [x] **Drop shadow with blur** — Implemented via `ImageFilter.GaussianBlur` in `render_text()` shadow effect.
- [x] **Template system** — `ascii-charts/typeset.py` ships `amazon-icon`, `amazon-small-icon`, `tvos-topshelf`, `play-feature` templates via `render_asset(template=...)`.
- [x] **Batch from JSON** — `generate_from_manifest("assets.json")` in `typeset.py`.
- [ ] **Multi-line text layout** — Auto-wrap long text with configurable max-width, line-height, and alignment.
- [ ] **Curved/arc text** — Text along a circular path for badges, seals, and circular icon borders.
- [ ] **Gradient text fill** — Linear/radial gradient fills inside letterforms.
- [ ] **Screenshot compositing** — Place device-framed app screenshots into promotional images. See expanded roadmap below.
- [ ] **Brand color extraction** — Auto-extract dominant colors from a background image.

#### Screenshot designer features — roadmap

> The screenshot-beautifier category (Pika, Shots.so, CleanShot X, Screely, BrandBird, Canva screenshot editor, Screen Studio, Rotato, Previewed, Mockdrop, Screenshot.rocks, BrowserFrame, Figma mockup plugins) has converged on a fairly standard feature set. Port the useful ones into muriel's raster channel as opinionated presets. We're stealing the feature menu, not the products.

**P0 — table stakes (ship first):**
- [ ] **`drop_shadow(offset, blur, color, spread)`** — multi-layer ambient + key shadows, Material-3 style. Existing `render_text()` shadow handles text only; this is for composited screenshots/images.
- [ ] **`fade_edge(side, ramp_px, curve="linear"|"ease")`** — progressive alpha ramp on any side (top/right/bottom/left) or radial. Andy's seed feature; rare as a preset outside Pika + Screen Studio.
- [ ] **`border_radius(r)`** — rounded corners on the screenshot/image before compositing.
- [ ] **`background(kind, …)`** — unified API with kinds: `solid`, `linear_gradient`, `radial_gradient`, `mesh_gradient` (3–5 color blobs), `image_blur`, `noise_overlay`, `transparent`.
- [ ] **`caption(text, position, style_token)`** — bound to brand tokens; enforces 8:1 contrast at render time, not as lint pass.
- [ ] **App Store + social dimension presets** — named constants already in [`channels/dimensions.md`](channels/dimensions.md); confirm coverage: `IPHONE_69_PORTRAIT` 1290×2796, `IPAD_13_PORTRAIT` 2064×2752, `OG_IMAGE` 1200×630, `X_CARD` 1200×675, `IG_SQUARE` 1080×1080, `IG_STORY` 1080×1920, `PRODUCT_HUNT` 1270×760.

**P1 — distinctive, low effort:**
- [ ] **`tilt(angle_deg, axis)`** — 2D affine shear (cheap fake-3D). Real perspective later.
- [ ] **`device_frame(kind)`** — PNG overlay library. Minimum kit: `iphone_15_pro_dynamic_island`, `macbook_pro`, `browser_chrome_light`, `browser_chrome_dark`, `browser_safari_mac`, `ipad`.
- [ ] **`browser_url_bar(url, title)`** — editable text rendered into the chrome asset (the URL is half the joke).
- [ ] **`spotlight(x, y, radius, falloff)`** — radial bright spot for "look here" emphasis.
- [ ] **`vignette(strength, shape="oval"|"rect")`** — classic framing effect.
- [ ] **`noise(amount)`** — post-filter; fights banding on gradients.
- [ ] **`glow(color, blur, intensity)`** — outer glow (Psychodeli audio-reactive aesthetic).

**P2 — differentiators:**
- [ ] **`glass_panel(rect, blur, tint)`** — frosted backdrop card behind device (2023–2026 aesthetic).
- [ ] **`numbered_callout(x, y, n, leader_to=(x,y))`** — step markers 1…n with leader line (BrandBird / CleanShot).
- [ ] **`reflection(height_frac, opacity)`** — iPod-style mirror under device.
- [ ] **`bento_grid(cells)`** — template compositor for N screenshots + brand palette (Pika).
- [ ] **`glass_reflection_overlay(asset)`** — pre-baked highlight PNG multiplied over screen for fake HDRI (Rotato lite).
- [ ] **`auto_blur_regions(detector)`** — heuristic blur for emails/tokens in debug captures. Scrutinizer-relevant when publishing validation screenshots.
- [ ] **`magnifier(x, y, radius, zoom)`** — BrandBird's "Highlight Product Feature" tool. Circular zoom-in lens on a specific UI region.
- [ ] **`annotation(arrow|rect|circle|emoji, x, y, …)`** — BrandBird/CleanShot annotation primitives.

**P3 — out of channel (skip or defer elsewhere):**
- Animated MP4 / GIF export → [`channels/video.md`](channels/video.md).
- Ray-traced 3D device renders → pre-render pipeline; muriel just ships the baked PNGs.
- Scene compositing (flat-lay, in-hand) → defer; not on brand for Scrutinizer/Psychodeli.
- AI screenshot editing (Magic Edit / Magic Grab / Magic Eraser from Canva; Uizard Screenshot Scanner reverse-engineering to mockups) → different skill; muriel is deterministic.

### SVG
- [ ] **Gaze ribbon primitive** — `typeset.svg.gaze_ribbon(fixations)` reusable across AdSERP / RecGaze work.
- [ ] **F-pattern overlay primitive** — Colored band generator from phase-segmented gaze data.
- [ ] **OSEC phase diagram primitive** — Multi-band horizontal timeline.
- [ ] **Excalidraw → clean-export pipeline** — Batch re-export with `roughness:0`, Helvetica, solid fills.
- [ ] **Mermaid CLI wrapper** — Themed output matching marginalia `--mg-*` palette.

### Interactive JS
- [ ] **Extract shared `permalink.js`** — Pull the PermalinkManager pattern out of Scrutinizer/Psychodeli for demos outside those repos.
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

### Web (editorial variant)
- [x] **Light editorial palette documented** — `channels/web.md` now has a section on the F-explainer pattern, with the `.outer-note` / `.stats-detail` / `.has-dropcap` / staged-h2 extensions catalogued.
- [ ] **Generalize `.outer-note` and `.stats-detail` back into marginalia** — Currently F-explainer-only; worth promoting to the main library if a second project adopts them.
- [ ] **Build-script variant of the pandoc bridge** — Node script using `marginalia-md.js` for projects that prefer browser-side conversion over pandoc.

### Video
- [x] **`channels/video.md`** — Recordly + desktop-control + ffmpeg + `burn-tooltips.sh` recipes shipped.
- [x] **hyperframes integration** — HeyGen's Apache-2.0 HTML → MP4 tool wired into the video channel. Installed via `npx skills add heygen-com/hyperframes -y -g` — registers `/hyperframes`, `/hyperframes-cli`, `/hyperframes-registry`, `/website-to-hyperframes`, `/gsap` as slash commands. Documented in [`channels/video.md`](channels/video.md) with pick-the-substrate-by-source-of-truth decision table.
- [ ] **Scrutinizer release-video prototype** — port `scrutinizer-www/src/blog/drafts/video-script-v2.6.md` and `video-script-minecraft-fast-demo.md` into hyperframes compositions. First proof that the HTML → MP4 path works for Scrutinizer release announcements. Bonus: the scripts already have precise timecodes + tooltip text.
- [ ] **`scrutinizer.app` → promo video** — invoke `/website-to-hyperframes` against scrutinizer.app and produce a 30–60s promo. Benchmark auto-generated quality vs hand-authored compositions.
- [ ] **PixiJS Frame Adapter** — bring muriel's PixiJS vocabulary (shader-driven gaze overlays, audio-reactive visuals) into hyperframes as a custom renderer. Unlocks Scrutinizer/Psychodeli WebGL demos as composable video blocks.

### Upstream ports — K-Dense scientific-agent-skills

> [K-Dense AI's `scientific-agent-skills`](https://github.com/K-Dense-AI/scientific-agent-skills) is an MIT-licensed family of research skills. Several overlap muriel's territory enough to borrow structure, templates, or tooling from. These are ports / adaptations, not wholesale adoption — muriel has its own brand rules and palette commitments.

- [x] **Infographics type × style matrix** — Shipped as [`channels/infographics.md`](channels/infographics.md). 10 types × layout patterns × 8:1-strict rubric, Wong/IBM/Tol colorblind-safe palettes named. Deterministic SVG (not AI image generation) — muriel's lane. K-Dense's AI pipeline explicitly not adopted. First exemplar: Scrutinizer foveation explainer at `scrutinizer-www/src/img/explainers/foveation.{svg,png,py}` — portrait 1080×1920, Anatomical + Statistical + Comparison hybrid, passes `muriel/contrast.py` at 8:1 across all 9 text roles.
- [ ] **Market-research long-form PDF channel** — New `channels/market-research.md`. 50+ page templated report: Front matter (5pp) → Core analysis (35pp: market definition, TAM/SAM/SOM sizing, PESTLE, Porter's Five Forces, segmentation, technology trends, regulatory, risk) → Strategic section (10pp: recommendations, roadmap, financials) → Back matter (5pp). LaTeX + `market_research.sty` or weasyprint+marginalia. 5–6 core visuals minimum at 300 DPI. Directly relevant to PM work (Quora/Poe, future roles). Source: [K-Dense market-research-reports](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/market-research-reports/SKILL.md).
- [ ] **PPTX visual-QA pipeline** — New `channels/pptx.md`. Swipe the infrastructure (not the rigid templates): `pptxgenjs` (JS, muriel-native) for generation → LibreOffice `soffice` for PDF conversion → `pdftoppm` for per-slide PNG → Pillow thumbnail grid for visual inspection. This is the real gold: the generate → render → inspect → fix loop. Include K-Dense's 10 palettes + font pairings + the "no accent lines under titles" AI-tell heuristic as brand defaults. Skip K-Dense's fixed templates — they converge to sameness, which fights muriel's multi-constraint-solver ethos. Source: [K-Dense pptx](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/pptx/SKILL.md).
- [ ] **Colorblind-safe palette commitment** — Wong, IBM, Tol as named palettes in `channels/style-guides.md` alongside the OLED/editorial palettes. Ship as importable constants in `muriel/palettes.py` (or extend `muriel/matplotlibrc_*.py` with `CATEGORICAL_WONG`, `CATEGORICAL_IBM`, `CATEGORICAL_TOL`). Cross-reference from [`channels/science.md`](channels/science.md) color section.
- [ ] **scientific-schematics compatibility shim** — K-Dense's [literature-review](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/literature-review/SKILL.md) and hypothesis-generation skills require a [`scientific-schematics`](https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/scientific-skills/scientific-schematics) skill as a mandatory dependency for figures (PRISMA diagrams, flowcharts, synthesis maps). If muriel wants to interoperate with the K-Dense workflow, expose a compatible interface (Python entry point that matches their expected call signature) that delegates to muriel's SVG + raster channels. Low-priority until a project actually needs it.
- [ ] **Markitdown → marginalia post-processor** — Separate tool (not a muriel channel). Microsoft's [`markitdown`](https://github.com/microsoft/markitdown) converts 15+ formats to markdown. K-Dense [wraps it](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/markitdown/SKILL.md) with AI image descriptions. Build a thin pipe: `markitdown file.pdf | marginalia-inject > out.md` that adds marginalia callout syntax (`.outer-note`, pull-quotes, sidenotes) to markdown output. If it proves useful, propose upstream as a markitdown plugin rather than forking.
