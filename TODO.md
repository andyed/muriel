# muriel — roadmap

Consolidated from `CHANGELOG.md`, `SKILL.md`, commit messages, and per-channel roadmap hints. Source of truth for what's next; `CHANGELOG.md` is source of truth for what's shipped.

## Canonical scenarios

Multi-channel narrative artifacts that compose several queued channels into one coherent demo. Each scenario forces the channel work it depends on; if the scenario ships, the channels worked. See `scenarios/`.

- [`scenarios/photons-to-recognition.md`](scenarios/photons-to-recognition.md) — Five-panel arc binding 3D (cone density on retina), brain (visual pathway through cortex), and diagrams (Sankey + sunburst) into one Scrutinizer talk-deck-as-explainer. Forces the build order: 3D → diagrams → brain. Reusable as deck slides, single composed infographic, blog post, or paper figure.
- [`scenarios/math-essay.md`](scenarios/math-essay.md) — Math-rich long-form essay binding marginalia (`channels/web.md`), KaTeX (`vocabularies/katex.md`), `typeset.py` figures, and Manim CE figure stills (when `channels/motion.md` ships) into one publishable HTML artifact. Reference exemplar: `inside_the_math` (psychodeli-webgl-port, shipped). Forces: math vocabulary completeness, Manim CE figure-embedding contract, marginalia ↔ KaTeX integration patterns.


## Active

- [ ] **`surfaces/` directory — implement the layer above channels.** [`vocabularies/surfaces.md`](plugins/muriel/skills/compose/vocabularies/surfaces.md) names the concept and cites html-anything as the canonical external catalog. Next step: ship muriel's first surface archetypes — start with the surfaces that compose channels muriel already has strong opinions on. Candidates ranked: (1) **deck-swiss-international** — fully spec'd by html-anything (22 layouts S01–S22, 4 locked themes), composes `channels/web.md` + `channels/charts.md` + `channels/polish.md`; (2) **frame-data-chart-nyt** — composes `channels/charts.md` for a hyperframes video frame, has clean editorial constraints; (3) **pm-spec** PRD — composes `channels/web.md` for a document register, ships as a marginalia template. Each surface lives at `surfaces/<name>/SKILL.md` + `surfaces/<name>/example.html` mirroring html-anything's shape; locked layout pool + locked palette + non-negotiable rules per surface. Defer until the first concrete brief actually wants one (the surface vocabulary should drive surface implementation, not speculation).
- [ ] **CJK-first font stack — i18n support.** html-anything routinely pairs Latin display fonts with `Noto Sans SC` for Chinese: `Inter Tight / Inter / Noto Sans SC / JetBrains Mono`. muriel's `brand.toml` schema and `channels/web.md` examples assume Latin-only font stacks today. When a brief needs CJK rendering: add a `i18n.cjk_fallback` field to `brand.toml`, default it to `Noto Sans SC`, ensure `muriel.contrast` audits the CJK glyphs (some CJK fonts render visibly heavier than their Latin pair at the same weight; verify the 8:1 floor on a representative CJK string, not just the Latin sample). Pairs with a queued `vocabularies/cjk-typography.md` covering vertical writing modes, ruby annotations, the Han-unification trap, and font-fallback-cascade order. No urgency until a brief lands.
- [ ] **Polish channel — promote rules into `muriel.critique` gates.** [`channels/polish.md`](plugins/muriel/skills/compose/channels/polish.md) ships 16 numbered rules + a validation checklist, but the critique agent doesn't auto-enforce them yet. Promote the top-tier (concentric radius math, hit-area minimum, `transition: all` ban, `will-change: all` ban, missing `tabular-nums` on dynamic numbers, `scale < 0.95` press) into the critique pre-scan as deterministic checks (regex / DOM walk) when the artifact targets the `app` register. Defer the optical-alignment + stagger-timing checks to the LLM critique pass — they need visual inspection. Pairs with the existing impeccable-bridge pre-scan.
- [ ] **Constraint-elicitation SKILL.md rule — pattern validated.** Pre-build constraint sheet (per [`project_muriel_constraint_elicitation`](~/.claude/projects/-Users-andyed-Documents-dev/memory/project_muriel_constraint_elicitation.md) memory) is already standard practice in [wrsmith108/visual-prompt-coach](https://github.com/wrsmith108/visual-prompt-coach) — it asks up to four questions before producing a prompt artifact (learning objective, what's shown, audience prior knowledge, constraints). Shape is the same as the queued muriel rule; reduces design risk. Next compose-mode session: lift the 4-question intake shape into the muriel rule + ship the drop-cap CONSTRAINTS.md exemplar.

- [ ] **Cross-harness packaging rollout — see [`HARNESSES.md`](HARNESSES.md).** Today muriel ships natively only for Claude Code (plugin + `install.sh`); ten other harnesses (Cursor, Codex CLI, Gemini CLI, GitHub Copilot, Kiro, OpenCode, Pi, Qoder, Rovo Dev, Trae) get a one-paragraph "mirror the SKILL.md into `.<harness>/skills/muriel/`" hint. Plan mirrors [pbakaus/impeccable](https://github.com/pbakaus/impeccable)'s eleven-harness matrix. P0: add `.agents/skills/muriel/` symlink to canonical (closes six harnesses with one change). P1: per-harness manifest generator + `./install.sh --harness <name>`. P2: frontmatter universalism, marketplace submissions, critique-agent portability.

- [ ] **muriel-critique auto-invoke gate — design the trigger conditions.** Retrospective evidence (`mona_laplacian`, `falloff_curves`, `notification_ghost`, all in the peripheral-color blog session 2026-04-25/26) shows a pattern: tier-collisions, terminology drift, and unverified numeric claims all reach the user before the critique agent sees them. The rules already exist in `agents/muriel-critique.md` (visual-inventory step 0, occlusion check, numeric-claim probe list). The miss is workflow — the agent gets invoked manually or never. *Do not* hard-wire "every figure runs through critique" — it would burn agent calls on every test render. Need to think hard about trigger conditions: maybe (a) only on artifacts produced by the `science` / `infographic` / `gaze` channels at non-draft DPI, (b) only when an artifact is about to be embedded in a published HTML/blog/paper file, (c) only when `--final` flag passed from a render script, (d) only when SKILL.md is loaded with an "audit" intent. Defer until the trigger surface is articulated.
- [ ] **Screenshot designer P0.** (from commit `533e32b`) Table-stakes compositor for marketing/doc screenshots: `drop_shadow()`, `fade_edge()`, `border_radius()`, `background()` (solid / gradient / mesh / blur / noise), `caption()` + dimension presets. Target channel: `channels/raster.md`, implementation under `muriel/tools/screenshot.py`.

## Queued

- [ ] **design.md export** — counterpart to the just-shipped `muriel import` (commit pending). Take a brand.toml, produce a Stitch-compatible design.md (frontmatter + Markdown prose) so brands round-trip through the open format. Lossy back-direction: muriel-specific fields (semantic state trios, ring gradients, viz palettes, voice, iconography) get lifted into prose sections rather than dropped, so they survive a future re-import. Add a round-trip test that confirms imported→exported→re-imported preserves the Stitch-native fields exactly.
- [ ] **Diagrams catalog — continuation.** MVP shipped (`matrix`, `cycle`); see [`channels/diagrams.md`](channels/diagrams.md) for the prioritized list. Remaining presets, in order: comparison pair, phase / funnel, layered stack, causal DAG, spectrum, pyramid, comparison heat-grid. Each ships with an epistemic precondition + anti-prescription in its docstring.
- [ ] **Diagrams icon-library decision.** The cycle generator has an `icon` slot per step that accepts raw SVG inner markup. Pick a substrate before adding icon helpers: lucide-static (MIT, ~1500 24×24 stroke icons), phosphor (MIT, multi-weight), or a hand-curated set of ~30 covering the diagram-relevant verbs. Settle this before extending past the matrix+cycle MVP.
- [ ] **`vocabularies/threejs.md` + `channels/3d.md`.** *Top-1 extension pick.* three.js is name-dropped in the README but undocumented; closes the most glaring vocab gap. MIT, zero license friction. Companion to `vocabularies/pixijs.md` — same shape (substrate decision, gotchas, version pin, exemplar). New `channels/3d.md` covers the channel surface (browser-side Three.js + Python-side PyVista / trimesh / Open3D). Consider naming it `channels/dimensional.md` if the "3d" tag reads narrow.
  - **Canonical PyVista exemplar to ship with the channel: cone-density-on-retinal-surface.** A 3D heatmap of receptor density painted on the back inner wall of the eye — fovea peak with radial falloff, exported as a rotated still. Solves a real explainer gap that 2D Gaussian curves can't carry (the falloff lives on a *curved* surface, and seeing it on the curve makes the cortical-magnification claim more visceral). When this lands, it becomes a second panel in the Scrutinizer foveation-explainer family ("the back of the eye, mapped") alongside the existing 2D side-view at `~/Documents/dev/scrutinizer-repo/scrutinizer-www/src/img/explainers/build_foveation.py`. Stretch goal: a sibling panel showing retina → V1 cortical magnification via the log-polar mapping (Blauch / Alvarez / Konkle 2026 reference).
- [ ] **`vocabularies/neuroimaging.md` + `channels/brain.md`.** Sibling to the 3D channel — brain viz is its own world with its own substrates and idioms, and folding it into a generic 3D channel would dilute the work. Primary substrate: **MNE-Python** (BSD-3, modern `mne.viz.Brain` built on PyVista; the 2026 successor to PySurfer). Companion stack: **nibabel** (MIT, file I/O foundation), **Nilearn** (BSD-3, statistical / glass-brain plotting + atlas fetchers), **fury** (BSD-3, VTK-based glyphs + streamtubes for connectivity arrows), **niivue** (BSD-3, browser-side WebGL widget for blog embeds). Atlases: Glasser HCP-MMP1.0 (CC-BY) for the modern parcellation including V1–V4 / V8 / MT / MST / FFC / PIT; Wang et al. (2015) probabilistic visual ROIs for stream-specific work (vocab-only ref since it ships through neuropythy AGPL-3, not bundled).
  - **Headline deliverable: `brain.visual_pathway()`** — takes a stream selection (`"ventral"` / `"dorsal"` / `"both"`) plus optional timing data, produces (a) a static publication figure with the hierarchy as a glass-brain projection + connecting arrows + region color, (b) an animated GIF/MP4 showing propagation, or (c) a niivue-embeddable HTML widget. Default timings from Schmolesky et al. (1998), Bullier (2001), Lamme & Roelfsema (2000): retina ~30ms, LGN ~50ms, V1 ~70ms, V2 ~100ms, V4 ~130ms, IT ~170ms; MT ~80ms, MST ~110ms, parietal ~140ms.
  - **Pairs with the queued PyVista cone-density-on-retina exemplar** as a two-panel "from photons to recognition" arc for the Scrutinizer foveation-explainer family: (1) cone density on the retinal surface = the *input*, (2) visual pathway through cortex = the *processing*. Same audience hit twice.
  - **License skip-list for this channel:** Connectome Workbench (GPL), Mayavi (LGPL via VTK — and MNE migrated off it for a reason), neuropythy (AGPL-3 — vocab-only reference, do not bundle).
- [ ] **`channels/motion.md`.** *Top-2 extension pick.* Operationalizes the schema's "motion as first-class field" with four MIT runtime adapters: Motion Canvas (TypeScript, programmatic keyframes — agent-authorable), Manim Community Edition (Python, expository / mathematical animation — pairs with `channels/science.md`), Lottie via `python-lottie` + `lottie-web` (declarative JSON, exports to web + After Effects), and **`@andyed/kinetic-type-engine`** (extracted from iblipper2025 — composable physics primitives for kinetic typography). Each gets a substrate-pick paragraph and at least one runnable example. Note GSAP separately under "may depend on, do not redistribute" — anti-competitive clause in the new free-for-commercial-use license precludes embedding.
  - **Kinetic-type-engine dependency:**
    - **Phase 1 done (2026-04-25):** `src/engine/` exists inside `iblipper2025` with primitives carved out — `chunking`, `fonts`, `layoutSafety`, `lineBreaking`, `nlp`, `orpCalculation`, `timingModel`, `trailModes`, `constants`, plus `__tests__/`. Fit tests followed the primitives. Spec at [`iblipper2025/docs/kinetic_type_engine_extraction_spec.md`](https://github.com/andyed/iblipper2025/blob/main/docs/kinetic_type_engine_extraction_spec.md).
    - **Phase 2 ahead:** publish to npm as `@andyed/kinetic-type-engine` under MIT in a standalone repo at `github.com/andyed/kinetic-type-engine`. Define the public `EngineConfig` / `PhysicsConfig` / `Frame` surface; ship `.d.ts`. Engine ships physics primitives (jitter, drift, fade, weight, scale, blur, glitch, trail, easing, timing); named recipes ('emphatic', 'hurry', …) stay in iBlipper as brand IP.
    - **Phase 3 ahead:** iblipper2025 swaps `src/engine/` for the npm dep.
    - **muriel-side adapter** lands when Phase 3 is complete. The other three adapters in this channel (Motion Canvas, Manim CE, Lottie) don't depend on the engine and can ship first.
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
- [ ] **Tests.** No `tests/` directory exists. Highest-risk untested modules: `oklch.py` (roundtrip correctness), `contrast.py`, `dimensions.py`.
- [ ] **Channel front-matter rollout.** Schema lives in [`channels/SCHEMA.md`](channels/SCHEMA.md). Shipped: `diagrams`, `science`, `gaze`, `heatmaps`, `infographics`, `web`, `svg`. Remaining: `dimensions`, `interactive`, `raster`, `style-guides`, `terminal`, `video`. The remaining six split into surface-flexible channels (audience optional — `interactive`, `raster`, `terminal`, `video`) and infrastructure channels with no artifact output (`dimensions`, `style-guides` — schema may grow a `kind: utility` flag before these land). Add front-matter as each channel is touched; do not bulk-rewrite. Critique runs without it — front-matter is opt-in.
- [ ] **5-dimension critique scoring** (mined from `nexu-io/open-design` `skills/critique`). Re-shape `muriel.critique` to score on 5 named dimensions with evidence-required: Direction consistency / Visual hierarchy / Detail execution / Functionality / **Veracity** (replacing open-design's "Innovation" — the wrong axis for science output; Veracity = chart supports the prose claim, nulls framed as detection limits, no extrapolated values labeled as measured). Today's automated checks become P0; the 5-dim scoring is a P1 layer with Keep/Fix/Quick-wins triple-list output. Optional SVG radar chart artifact mode.
- [ ] **`channels/decision-tree.md`.** "Which channel for which job" disambiguation page (mined from open-design's "When to pick X vs peer-skill Y" tables). Tree by *artifact destination* (paper / blog / social / app / talk) → channel → primitive. Today the choice is implicit; reader has to remember which channel exists.

## Someday

- [ ] **Screenshot designer P2.** `glass_panel()`, `numbered_callout()`, `reflection()`, `bento_grid()`, `glass_reflection_overlay()`, `auto_blur_regions()`, `magnifier()`, `annotation()`.
- [ ] **K-Dense ports** (from `SKILL.md:214-219`): market-research PDF channel, PPTX visual-QA pipeline, scientific-schematics shim, markitdown bridge.
- [ ] **Heading-style standardization pass** across `channels/*.md` — bare noun/verb convention, em-dashes only for structural disambiguation. ~12 files.
- [ ] **Scrutinizer release-video + promo prototypes** (demo-specific; two scripts).
- [ ] **PixiJS frame adapter for hyperframes** (video channel).

## Policy & process

Surfaced by the independent review of the v0.9.0 cut (2026-05-17). Meta-items about how to ship features, not features themselves. Acting on these *before* the next minor bump keeps the project coherent as channel + vocabulary count grows.

- [ ] **Write down the doc-convention contract.** Add `CONTRIBUTING.md` (or a section in `SKILL.md`) that specifies the boundaries between `channels/*.md` (output substrates with selftest + CLI), `vocabularies/*.md` (aesthetic grammars, no shipped code), `RELEASE_NOTES_v*.md` (public-prose voice), `CHANGELOG.md` (diff log), and per-module docstrings. The boundaries are felt right now, not specified — a new contributor would invent a fifth doc kind without realizing they were drifting. ~1 page.
- [ ] **Module API contract as test.** Every new module shipped in v0.8.0 + v0.9.0 follows the same shape (pure Python stdlib core, lazy optional-dep imports, `--selftest`, `--demo`, module docstring with anti-prescription). Codify as `tests/test_module_contract.py` that introspects `muriel/*.py` and `muriel/tools/*.py` and fails CI if a module is missing the contract. The pattern is real; institutionalizing it stops drift in module N+1.
- [ ] **Palette tier as a required field on every palette constant.** Add `tier ∈ {"text-safe", "decorative-only"}` to every named palette (the eleven currently in `muriel.palettes`). Then `muriel-critique` can FAIL any artifact that uses a `decorative-only` palette for text, automatically. The 8:1 floor stays absolute on text; the *scope* of where it applies gets named per-token. This is the right way to handle the Catppuccin Latte / Nord Aurora / Frost decorative-only exceptions without weakening the universal rule.
- [ ] **Corpus-audit-everything pattern.** `corpus_audit` in v0.8.0 caught three real importer bugs on its first run. The pattern generalizes: build analogous harnesses for (a) contrast — run `audit_svg` across every shipped example, (b) DTCG round-trip — already done in `corpus_audit`, formalize as CI gate, (c) palette generation — run `generate_for_floor` across the 11 palette × N standard-background matrix, (d) diagram rasterization — verify every diagram primitive renders cleanly via `rsvg-convert`. Each catches a different class of silent regression.
- [ ] **Spatial cross-substrate pattern — formalize before adding a second cross-substrate channel.** `channels/spatial.md` ships Python (`muriel.spatial`) + JS-runtime (`render_assets/`) sharing a coordinate system. The pattern is right (same coords in two substrates = the value); it's also where the queued `typeset_scene()` belongs — it's what *justifies* the dual-substrate framing by closing the loop. Ship `typeset_scene()` before the next channel goes cross-substrate, OR you'll have three channels that each invented their own bridge. Add "shared coordinate system" as a documented channel-frontmatter field so the convention propagates.

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
