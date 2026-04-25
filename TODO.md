# muriel — roadmap

Consolidated from `CHANGELOG.md`, `SKILL.md`, commit messages, and per-channel roadmap hints. Source of truth for what's next; `CHANGELOG.md` is source of truth for what's shipped.

## Active

- [ ] **Cut 0.6.0.** `[Unreleased]` block in `CHANGELOG.md` is ready: OKLCH module + brand.toml schema v2. Commit the uncommitted OKLCH changes, move the block, tag.
- [ ] **Screenshot designer P0.** (from commit `533e32b`) Table-stakes compositor for marketing/doc screenshots: `drop_shadow()`, `fade_edge()`, `border_radius()`, `background()` (solid / gradient / mesh / blur / noise), `caption()` + dimension presets. Target channel: `channels/raster.md`, implementation under `muriel/tools/screenshot.py`.
- [ ] **FUI productionization.** `vocabularies/fui.md` is a 56-line reference card; peer vocabularies have substrate decision trees, SDF rules, "common failures" lists, and working exemplars. Expand to parity, then add a `channels/interactive.md` "Sci-fi UI patterns" subsection with four scaffold demos (ticker, compass, scan-line overlay, staggered reveal) and a CodePen Prefill.

## Queued

- [ ] **design.md export** — counterpart to the just-shipped `muriel import` (commit pending). Take a brand.toml, produce a Stitch-compatible design.md (frontmatter + Markdown prose) so brands round-trip through the open format. Lossy back-direction: muriel-specific fields (semantic state trios, ring gradients, viz palettes, voice, iconography) get lifted into prose sections rather than dropped, so they survive a future re-import. Add a round-trip test that confirms imported→exported→re-imported preserves the Stitch-native fields exactly.
- [ ] **Diagrams catalog — continuation.** MVP shipped (`matrix`, `cycle`); see [`channels/diagrams.md`](channels/diagrams.md) for the prioritized list. Remaining presets, in order: comparison pair, phase / funnel, layered stack, causal DAG, spectrum, pyramid, comparison heat-grid. Each ships with an epistemic precondition + anti-prescription in its docstring.
- [ ] **Diagrams icon-library decision.** The cycle generator has an `icon` slot per step that accepts raw SVG inner markup. Pick a substrate before adding icon helpers: lucide-static (MIT, ~1500 24×24 stroke icons), phosphor (MIT, multi-weight), or a hand-curated set of ~30 covering the diagram-relevant verbs. Settle this before extending past the matrix+cycle MVP.
- [ ] **`vocabularies/threejs.md` + `channels/3d.md`.** *Top-1 extension pick.* three.js is name-dropped in the README but undocumented; closes the most glaring vocab gap. MIT, zero license friction. Companion to `vocabularies/pixijs.md` — same shape (substrate decision, gotchas, version pin, exemplar). New `channels/3d.md` covers the channel surface (browser-side Three.js + Python-side PyVista / trimesh / Open3D). Consider naming it `channels/dimensional.md` if the "3d" tag reads narrow.
  - **Canonical PyVista exemplar to ship with the channel: cone-density-on-retinal-surface.** A 3D heatmap of receptor density painted on the back inner wall of the eye — fovea peak with radial falloff, exported as a rotated still. Solves a real explainer gap that 2D Gaussian curves can't carry (the falloff lives on a *curved* surface, and seeing it on the curve makes the cortical-magnification claim more visceral). When this lands, it becomes a second panel in the Scrutinizer foveation-explainer family ("the back of the eye, mapped") alongside the existing 2D side-view at `~/Documents/dev/scrutinizer-repo/scrutinizer-www/src/img/explainers/build_foveation.py`. Stretch goal: a sibling panel showing retina → V1 cortical magnification via the log-polar mapping (Blauch / Alvarez / Konkle 2026 reference).
- [ ] **`channels/motion.md`.** *Top-2 extension pick.* Operationalizes the schema's "motion as first-class field" with three MIT runtime adapters: Motion Canvas (TypeScript, programmatic keyframes — agent-authorable), Manim Community Edition (Python, expository / mathematical animation — pairs with `channels/science.md`), Lottie via `python-lottie` + `lottie-web` (declarative JSON, exports to web + After Effects). Each gets a substrate-pick paragraph and at least one runnable example. Note GSAP separately under "may depend on, do not redistribute" — anti-competitive clause in the new free-for-commercial-use license precludes embedding.
- [ ] **`channels/charts-declarative.md`.** *Top-3 extension pick.* Declarative-JSON charting alongside matplotlib. Two adapters: Vega-Lite + Altair (BSD-3, grammar-of-graphics — extremely LLM-friendly because the spec *is* the chart) and Observable Plot (ISC, modern concise D3). Rationale: matplotlib is for paper figures; LLMs reliably author Vega-Lite specs but stumble through matplotlib's imperative API.
- [ ] **`channels/charts-interactive.md`.** Different lane from charts-declarative — *rich interactive widget library*, not grammar of graphics. Primary adapter: Apache ECharts (Apache-2.0). Alternates: Plotly.js (MIT), Bokeh (BSD-3). ECharts wins for dashboards, geographic widgets at country/province granularity, parallel coordinates with brushing, calendar heatmaps, sankey + theme-river flow viz, smooth animated transitions between chart types, 3D scatter/surface. Theme system maps cleanly onto brand tokens. Use when the artifact lives on a web surface and reader interaction is part of the contract; use charts-declarative when the artifact is a static figure and the spec is the auditable source.
- [ ] **Sankey diagram primitive** (new entry in `channels/diagrams.md` catalog). Argues *"this magnitude flowed from here to there"* — directly relevant to OSEC phase flow, attentional foraging migration, conversion funnels with branching. Three viable paths: (A) wrap `d3-sankey` (BSD-3, official Bostock plugin) via Node, (B) wrap `pysankey2` or `floweaver` (both MIT, matplotlib-rendered), (C) port the d3-sankey iterative-relaxation algorithm to Python (~250 lines) for a deterministic SVG output that matches the matrix + cycle pattern. Path C is the cleanest fit for muriel's ethos but the most work; path A ships fastest if a Node hop is acceptable. Decide before implementing. Anti-prescription: don't use a Sankey if your "flow" doesn't carry magnitudes — a flow with all-equal weights is a DAG, not a Sankey.
- [ ] **Hierarchy family in `channels/diagrams.md` — currently underspecified.** The catalog names *pyramid* (1D ordered hierarchy) but skips the rest of the family. Add at minimum: **sunburst** (multi-level radial hierarchy with area-proportional slices), **treemap** (rectangular sibling of sunburst), **dendrogram** (branching tree display). Each carries a distinct epistemic shape and shouldn't be conflated. Sunburst is the highest-priority entry — it argues *"this category contains these subcategories, with proportional weights, recursively"*, which lands cleanly on research taxonomies, eye-tracking AOI nesting (page → region → element), F-pattern phase × sub-phase decomposition, and click/conversion category drill-downs. Same three-path decision as Sankey: (A) wrap `d3-hierarchy` + `d3-shape` via Node, (B) no good Python wrapper exists, (C) port the partition-layout algorithm (~100 lines, recursive arc-angle assignment) for deterministic SVG. ECharts has the nicest interactive reference implementation (click-to-reroot at 60fps with breadcrumb-persistent parent) — that's the canonical pattern for the `channels/charts-interactive.md` lane when drill-down is part of the contract. Anti-prescription: don't use sunburst if the leaf weights are roughly equal — uniform area carries no signal; use a dendrogram or tree instead.
- [ ] **Screenshot designer P1.** Distinctive moves: `tilt()` (2D affine), `device_frame()`, `browser_url_bar()`, `spotlight()`, `vignette()`, `noise()`, `glow()`.
- [ ] **Saliency detector wiring.** `muriel/detectors/saliency.py:53` is a v0.2 placeholder; fetch logic is stubbed at `muriel/warmup.py:87`. Ship the ONNX backend.
- [ ] **SVG primitives reused across research repos.**
  - Gaze ribbon primitive (currently hand-rolled in AdSERP / RecGaze).
  - F-pattern overlay (phase-segmented gaze framing).
  - OSEC phase diagram (multi-band timeline).
- [ ] **Shared `permalink.js`.** Extract from Scrutinizer + Psychodeli; single source in `channels/interactive.md`.
- [ ] **Science helpers** (from `SKILL.md:193-196`):
  - Figure caption template tool.
  - Pre-registration boilerplate generator.
  - `contrast.py` inline-fill pass — walk `<text fill="…">` in SVG.
  - `contrast.py` marginalia-token audit.
- [ ] **Multi-line raster text layout.** Configurable max-width, line-height, alignment in `muriel.typeset`. Blocks some infographics.
- [ ] **Constraint-elicitation SKILL.md rule.** Queued per memory: ask 4–5 sharp constraint questions before first composite build (trial pending).
- [ ] **Tests.** No `tests/` directory exists. Highest-risk untested modules: `oklch.py` (roundtrip correctness), `contrast.py`, `dimensions.py`.

## Someday

- [ ] **Screenshot designer P2.** `glass_panel()`, `numbered_callout()`, `reflection()`, `bento_grid()`, `glass_reflection_overlay()`, `auto_blur_regions()`, `magnifier()`, `annotation()`.
- [ ] **K-Dense ports** (from `SKILL.md:214-219`): market-research PDF channel, PPTX visual-QA pipeline, scientific-schematics shim, markitdown bridge.
- [ ] **Heading-style standardization pass** across `channels/*.md` — bare noun/verb convention, em-dashes only for structural disambiguation. ~12 files.
- [ ] **Scrutinizer release-video + promo prototypes** (demo-specific; two scripts).
- [ ] **PixiJS frame adapter for hyperframes** (video channel).

## Won't-do

- Ray-traced 3D device renders — pre-render pipeline; muriel ships PNGs.
- AI screenshot editing (Magic Edit / Magic Grab) — different skill.
- Perspective-transform screenshots — P1 `tilt()` is 2D affine only; real 3D deferred indefinitely.
- Venn beyond 3 sets — four interlocking circles are cosmetic, not informative (see `muriel/tools/venn.py`).
- **Bundling copyleft / source-available libraries.** Any of the following may be referenced from a vocabulary doc but never vendored, wrapped as a bundled adapter, or imported as a hard dependency without adopting their copyleft (or paying):
  - **GPL family:** ComfyUI (GPL-3), Blender bpy (GPL), PlantUML (GPL).
  - **AGPL:** Hydra-synth (AGPL-3.0). Vocab-only reference at most.
  - **LGPL:** p5.js (LGPL).
  - **Source-available / paid:** tldraw SDK (production use requires paid license as of SDK 4.0; only starter kits are MIT).
  - **MPL / file-scoped copyleft:** Satori (MPL-2.0) — fine to depend on, not to vendor-modify.
  - **Anti-competitive clause:** GSAP (now free for commercial use under Webflow's Standard License, but contains a clause forbidding use in competing visual-animation builders; not OSI-approved). OK to depend on, not to redistribute.

## Vocabularies & engine adapters — full candidate inventory

Curated by gap area. Each candidate's license noted; only MIT / Apache-2.0 / BSD / ISC / MPL-2.0 are viable as bundled adapters under muriel's outbound MIT license.

**3D and generative graphics** (gap: three.js is name-dropped only):
- three.js (MIT) — primary 3D substrate.
- Babylon.js (Apache-2.0) — heavier; physics + WebXR.
- regl (MIT) — functional WebGL; generative / procedural.
- PyVista (MIT) and trimesh (MIT) — Python-side mesh / scientific viz.
- Open3D (MIT) — point clouds, meshes, reconstruction.

**Animation and motion** (gap: motion is in the schema but has no runtime adapter):
- Motion Canvas (MIT) — TypeScript, programmatic keyframes; agent-authorable.
- Manim Community Edition (MIT) — mathematical / expository.
- Lottie via lottie-web + python-lottie (MIT) — declarative JSON, web + AE export.
- Rive runtimes (MIT, confirmed April 2026) — state-machine interactive animation, multi-platform.
- GSAP — see Won't-bundle block above.

**Charting beyond matplotlib** (gap: matplotlib is the only path):
- Vega-Lite + Vega + Altair (BSD-3) — grammar of graphics, JSON-spec, LLM-friendly.
- Observable Plot (ISC) — modern concise D3 API.
- Plotly.js (MIT) — interactive HTML.
- Apache ECharts (Apache-2.0) — rich statistical + geographic.
- Bokeh (BSD-3) — Python-native interactive.

**Image processing / CV / generative AI** (gap: Flux adapter mentioned but unpopulated):
- OpenCV (Apache-2.0) — classical CV.
- scikit-image (BSD-3) — scientific image processing on the NumPy stack.
- rembg (MIT) — background removal.
- HuggingFace diffusers (Apache-2.0) — wrapper for diffusion models. **Caveat:** weights (SD / Flux) carry their own non-MIT licenses; vocabulary yes, bundled weights no.

**Typography** (gap: typeset.py is custom, no font tooling):
- fontTools (MIT) — parse / subset / manipulate OpenType; essential for variable fonts.
- HarfBuzz (Old MIT / "MIT-Harfbuzz") — shaping engine.
- opentype.js (MIT) — browser-side font parsing.
- Satori (MPL-2.0) — JSX-to-SVG text layout. See Won't-bundle for redistribution caveat.

**Diagramming** (currently Mermaid + Excalidraw only):
- Graphviz (CPL / EPL-style, MIT-compatible in practice) — canonical graph layout. Pairs with the queued causal DAG diagram primitive.
- Excalidraw libraries (MIT) — already referenced; promote to first-class.
- draw.io / mxGraph core (Apache-2.0).
- *Skip:* tldraw SDK (source-available), PlantUML (GPL).

**Creative coding / shader toolkits**:
- openFrameworks (MIT) — C++; heavier to embed but MIT-clean.
- *Skip:* Hydra (AGPL-3.0); Shadertoy snippets (author-dependent — curate carefully).

**Geospatial** (absent):
- Leaflet (BSD-2).
- deck.gl (MIT), kepler.gl (MIT).
- MapLibre GL (BSD-3).

**Audio / waveform** (absent):
- WaveSurfer.js (BSD-3).
- Tone.js (MIT), Howler.js (MIT).

**Sources** (for the contested licenses): rive-runtime LICENSE (Rive MIT confirmed); CSS-Tricks "GSAP Now Completely Free" + Webflow Standard License (GSAP anti-compete clause); tldraw SDK License + tldraw blog "License updates for the SDK" (paid for production); hydra-synth/hydra LICENSE (AGPL-3.0).

## Release gate

- `render_assets` deprecation shim is committed to removal in **0.7.0** (see `CHANGELOG.md [0.5.0] Deprecated`). Do not remove before then.
