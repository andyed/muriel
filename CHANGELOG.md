# Changelog

All notable changes to muriel are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
version numbers follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **`muriel.palettes.generate_for_floor()` — contrast-floor-driven
  palette generation.** The named palettes above (Wong / IBM / Tol)
  are *audited* against the 8:1 floor after the fact. This function
  inverts the relationship: pick a background and a target contrast
  ratio, and the palette is generated *at* the floor by construction.
  Every output color is guaranteed by the algorithm — not by audit —
  to hit the floor against the chosen background.

  Lineage: [`adobe/leonardo`](https://github.com/adobe/leonardo)
  (Apache-2.0). Leonardo's core insight ported to muriel's stack:
  Python, zero external deps, routes through `muriel.oklch` (binary
  search on perceptual L for the target relative luminance, then on
  chroma for max sRGB-gamut saturation) and verifies with
  `muriel.contrast.contrast_ratio`. Direction auto-resolves to light
  on dark backgrounds and dark on light backgrounds; explicit
  `direction="light"|"dark"` available. Raises `ValueError` cleanly
  when the floor can't be reached (mid-tone bg with floor=10, etc.).
  CLI: `python -m muriel.palettes --generate --bg "#0a0a0f" --floor
  8 --n 6` prints the palette with verified contrast per color.
  Ships with `--selftest`.

  Verified output (dark bg, floor 8, n=6): all six hit 8.05–8.48:1.
  Verified output (light bg `#fafafa`, floor 8, n=6): all six hit
  8.05–9.16:1.

- **`channels/terminal.md` — animated-effects section.** Cross-pollinates
  the terminal channel with the kinetic-typography vocabulary by
  documenting [`TerminalTextEffects`](https://github.com/ChrisBuilds/terminaltexteffects)
  (TTE, MIT, ~100 named effects). Expands the channel from static
  primitives (`bar_chart`, `sparkline`, `table`) to terminal-as-
  artifact for installer ceremonies, deploy banners, README hero
  GIFs. Anti-prescription notes when motion in static-replay contexts
  becomes decoration. Paired with a new row in
  `vocabularies/kinetic-typography.md` substrate-choices table —
  same kinetic-type rules (max contrast, strategic motion, no
  ambient noise), new runtime (ANSI cells instead of canvas).

### Changed
- **`muriel.contrast` + `muriel.oklch` module docstrings now cite
  [`color-js/color.js`](https://github.com/color-js/color.js)** (MIT,
  maintained by the CSS Color Module spec editors) as the
  spec-authoritative reference for the wider color-science ecosystem
  (APCA, non-sRGB gamuts, deltaE, every CSS Color 4 space).
  muriel's stdlib-only subset stays the path for the 8:1 enforcement
  floor; color.js is the recommended drop-down when more is needed.

## [0.8.0] — 2026-05-17

**The rigorous round-trip.** Closes loops: the design.md → brand.toml → tokens.json round-trip got honest (corpus audit + three importer fixes), got fully two-way (new DTCG exporter), and grew a new visual surface that wires into both ends (spatial perspective grids + Three.js exemplars). First release where a brand can come in from `awesome-design-md`, ship outward to any DTCG-aware downstream, and render type into felt space without leaving the toolkit. Long-form notes: [`RELEASE_NOTES_v0.8.0.md`](RELEASE_NOTES_v0.8.0.md).

### Added
- **`muriel.spatial` + `render_assets/` exemplars + `channels/spatial.md`
  — depth scaffolding for layered typography.** Closes a long-standing
  gap: muriel rendered figures and brand chrome well, but had no
  primitive for type-in-space — the Cooper VLW / Perspective Wall /
  Data Mountain lineage. Two coupled surfaces:
  - **Static side: `muriel.spatial`** — pure-Python SVG perspective
    grids. `grid("1pt"|"2pt"|"3pt"|"iso", BBox(...))` returns a
    `PerspectiveGrid` (frozen dataclass with `vanishing_points` and
    canvas-clipped `GridLine` tuples) with `.svg()` emit. Tron-style
    cyan-on-near-black defaults; Liang-Barsky line clipping;
    fade-to-horizon depth weighting on transversals;
    isometric branch for parallel axonometric. CLI: `python -m
    muriel.spatial --demo` (2×2 panel of all four modes), `--mode
    {1pt,2pt,3pt,iso}` for single mode at full canvas, `--selftest`.
  - **Interactive side: `render_assets/`** — Three.js + CSS3DRenderer
    exemplars sharing one helper lib (`_lib/spatial.js`,
    `_lib/spatial.css`). The two-renderer stack keeps WebGL grid /
    horizon / atmosphere on the GPU while DOM cards composite on top
    via CSS3D, so text stays selectable, copyable, and screen-reader
    addressable. Helpers: `createScene`, `Mountain`,
    `addFloorGrid`, `addHorizon`, `makePlane`, `FocusController`
    (click-to-focus animation), `startRenderLoop` (parallax +
    auto-orbit). Five exemplars across two brand families:
    `spatial-typography/` (Cooper VLW homage),
    `mindbendingpixels-mountain/` + `sciprogfi-agentchan-mountain/`
    (Data Mountain — Dumais et al. 2001), `perspective-wall/` +
    `sciprogfi-lux-mesh-wall/` (Mackinlay-Robertson-Card 1991). Single
    gallery page at `render_assets/index.html`.
  - **`channels/spatial.md`** — channel doc with the full lineage
    (Alberti 1435 → Dürer 1525 → Cooper VLW 1980s → Mackinlay 1991
    → Robertson 1993 → Dumais 2001 → Tron), the four-mode anti-
    prescription (when *not* to reach for perspective), palette-token
    table showing the demo defaults pass 8:1 on `#e6e4d2` × `#07070d`
    (15.42:1), and a worked example wiring the JS lib into an exemplar.
  Coordinate system is shared between the static and interactive sides
  by design — the queued `muriel.spatial.typeset_scene()` (in TODO)
  will close the loop: take a `PerspectiveGrid` plus a list of DOM
  blocks with anchor names (`("vp", "left", 3)` /
  `("grid", row, col, depth)`) and emit a runnable
  `<scene>/index.html` so a paper figure and a fly-through share their
  geometry by construction, not by hand-port.

- **`muriel.dtcg_export` + `muriel export-dtcg` — emit a brand.toml as
  W3C Design Tokens Community Group JSON.** Third leg of the muriel
  round-trip: `design.md → brand.toml → tokens.json`. With both
  halves a brand.toml pivots into the entire
  [style-dictionary](https://amzn.github.io/style-dictionary/)
  ecosystem (style-dictionary, theo, Figma tokens-studio, token-css,
  iOS / Android / Tailwind / CSS-vars pipelines downstream) without
  writing any downstream transformer.

  Maps every brand.toml v2 block onto its DTCG-canonical type group:
  `[colors]` → `color`, `[colors.aliases]` → DTCG alias tokens with
  `{color.foreground}` reference syntax, `[semantic.{state}]` →
  nested `color.semantic.{state}.{text|surface|border}`,
  `[viz.{categorical,sequential,diverging}]` → indexed
  `color.viz.{series}.{1,2,…}` (DTCG has no native array type),
  `[typography.scale.{role}]` → composite `typography` tokens with
  `fontFamily` / `fontWeight` / `fontSize` / `lineHeight` /
  `letterSpacing` fields, `[spacing]` + `[radii]` → `dimension`,
  `[motion.duration_*]` → `duration`, `[motion.easing_*]` →
  `cubicBezier` (parses both `cubic-bezier(a,b,c,d)` and CSS keywords
  `linear` / `ease` / `ease-in` / `ease-out` / `ease-in-out`),
  `[elevation]` → best-effort `shadow` parse with the raw CSS string
  preserved under `$extensions.muriel.elevation_raw`.

  Muriel-specific fields that DTCG doesn't model natively
  (`iconography`, `imagery`, `logo`, `voice`, `rules`,
  `provenance`, `a11y`, `motion.motion_preference`, typography
  `upper: true`) are preserved under `$extensions.muriel.*` so a
  future brand.toml round-trip importer can recover them.

  Pure Python — no jsonschema or DTCG validator dependency. Lazy
  `tomllib` import so the in-memory `to_dtcg(dict) → dict` mapper
  works on Python 3.10 too (file-based `export_dtcg(path)` requires
  3.11+ for stdlib `tomllib`). Ships with `DTCGError`, public
  `to_dtcg` + `export_dtcg`, comprehensive `--selftest`, and CLI
  via `muriel export-dtcg brand.toml [-o tokens.json]`. **End-to-end
  verified**: all 61 parseable awesome-design-md brands round-trip
  cleanly through `import → export` with zero failures.

### Fixed
- **`muriel.design_md_import` — three bugs surfaced by the new corpus
  audit, each lifting clean-parse rate against the 71-brand
  awesome-design-md corpus.** Before/after on the harness:
  parsed cleanly 48/71 → **61/71** (85%), parse errors 13 → **0**,
  brands with REAL bg/fg from source 6/48 → **61/61**, pass 8:1 on
  stated colours 0 → **48**, total WARNs 90 → **0**.
  - **Color-key mapping rewritten as a priority list
    (`STITCH_COLOR_PRIORITY`).** Old flat `STITCH_COLOR_TO_MURIEL`
    dict made the winner iteration-order-dependent and missed the
    most common keys in the actual corpus (`canvas` / `ink` / `body` /
    `primary`). New list is ordered — first stitch key found in
    priority order wins for each muriel role. Adds Anthropic-style
    canonical keys (`canvas`, `body`, `ink`), variants (`canvas-light`,
    `canvas-cream`, `canvas-night`, `surface-canvas-light`,
    `surface-canvas-dark`), and obvious synonyms (`bg`, `paper`,
    `text`, `text-primary`, `brand`). Fixes 42 brands that previously
    had BOTH bg and fg silently defaulted to muriel's `#0a0a0f` /
    `#e6e4d2`. Legacy flat-dict mirror retained for any external
    consumer.
  - **YAML anchor / ref detection scoped to value-start
    (`_ANCHOR_REF_RE`).** Old whole-line substring check matched
    `" *"` and `"& "` inside prose strings (Ferrari's
    `**near-black** (...)`, several others), false-positiving as
    unsupported YAML. Check moved into `_coerce_scalar` against an
    actual `^[&*]\\w[\\w-]*\\b` pattern at value-start, after quote
    stripping. Fixes ~4 parse errors.
  - **YAML block scalars (`|` / `>`) now supported via
    `_expand_block_scalars` preprocessing.** ~1/6 of corpus brands
    (Nike, NVIDIA, Ollama, opencode.ai, Renault, Replicate, Resend,
    Revolut, …) carry their brand summary as
    `description: |` followed by an indented continuation. Old parser
    bailed with "unexpected indent" on the continuation. New
    preprocessor inlines the block into a single synthetic
    `key: "..."` row with newlines round-tripped through a Private
    Use Area sentinel (U+E000 — chosen because `str.splitlines()` does
    not split on PUA codepoints, whereas U+2028 / U+2029 would).
    Handles literal (`|`) and folded (`>`) styles. Fixes ~9 parse
    errors.

### Added
- **`muriel.tools.corpus_audit` + `muriel import-corpus` — bulk-import
  a DESIGN.md corpus and report.** Runs the entire
  [awesome-design-md](https://github.com/VoltAgent/awesome-design-md)
  corpus (71 brands incl. Stripe, Linear, Notion, Anthropic, OpenAI,
  Cohere, Webflow, Vercel, Figma, …) through
  `muriel.design_md_import.parse_design_md` and emits a per-brand
  report. Three output shapes: `--format summary` (terminal headline
  numbers + top WARN categories), `--format md` (release-blog
  markdown table — brand × bg × fg × contrast × 8:1 pass/fail), and
  `--format json` (machine-readable per-brand record for CI diff).
  Honest accounting: when the importer fills in muriel's defaults
  because the source spec lacks usable surface keys, the brand's
  bg/fg are marked `*` and contrast is reported `n/a` rather than
  pretending muriel's defaults are the brand's contrast. A
  `--fail-on {never,any-error,any-contrast-fail}` gate turns the
  harness into a CI check.
- **`muriel.design_md_import.parse_design_md(text, source=None)`.**
  Non-IO counterpart of `import_design_md` — parses a design.md
  string into the brand.toml dict shape without writing anything.
  Lets `corpus_audit` iterate 71 brands without spraying 71
  brand.toml files into the filesystem, and lets tests assert on
  parser output without temp-file scaffolding.
- **`muriel.patterns` — generative pattern primitives for backgrounds
  and texture.** Three deterministic primitives that cover the
  workhorse background surface (and unblock the queued
  `channels/raster.md` screenshot-designer `background()` arg):
  - **`dots`** — Bridson (2007) fast Poisson-disk sampling. Even visual
    density, no obvious tiling. For dot-grid meshes, scatter texture,
    particle carriers.
  - **`flow`** — value-noise vector field traced as short polyline
    streamlines, LIC-style (Cabral & Leedom 1993). For directional
    backgrounds and contour-suggestion texture.
  - **`grain`** — value-noise raster sampled at cell granularity into a
    small SVG `<pattern>` tile that repeats across the canvas. File
    size stays O(tile_cells²) regardless of canvas dimensions. For
    film-grain, paper-texture, subtle non-flat fill.

  Pure Python — no numpy, scipy, or Pillow. All randomness routes
  through `hashlib.blake2b` so same seed → byte-identical SVG across
  platforms and Python versions. Each primitive ships `bg` + `fg`
  parameters; overlay text validates against `bg` (the contrast
  anchor) through `muriel.contrast`. Ships with `DotField` /
  `FlowField` / `Grain` frozen dataclasses, `_value_noise2` /
  `_bridson` / `_trace_streamline` internals, `python -m
  muriel.patterns --demo` (1×3 panel of all three primitives),
  `--kind {dots,flow,grain}` for single-primitive render, and
  `--selftest`. Lineage: `css-doodle`, `glisp`, `curv`, `nannou`,
  `noc-book-2`.

## [0.7.1] — 2026-05-14

### Added
- **`muriel.layout` — bbox-aware annotation placement.** `place_label()`
  closes a catalogued 100%-fail-rate pattern: hand-coded inline label
  placement produced an overlap on *every* iteration of *every*
  figure-with-annotations task, and the cover-up — white-stroke halos
  behind text — was worse than the original sin (occlusion-as-priority,
  data falsified to make the label fit). The helper takes the text, its
  font size, an ordered list of candidate in-plot anchors, and an
  obstacle point-cloud (or bbox list), and returns the first
  collision-free placement. When every in-plot candidate collides it
  falls back, in order, to **safe-by-construction zones**: the nearer
  left/right margin (a label outside `plot_bbox` cannot overlap data by
  construction), then the caption. Every rejected candidate is recorded
  on the result with the reason. It never shrinks text and never emits a
  halo. Ships with `BBox` / `Anchor` / `Rejection` / `Placement`
  dataclasses, a `text_bbox()` metric estimator, `sample_polyline()` for
  densifying curves into obstacle clouds, a `Placement.svg_text()`
  emitter (stroke-free by contract), `python -m muriel.layout --demo`
  (renders the bbox-vs-geometry check as a worked SVG) and `--selftest`.
- **`vocabularies/declassified.md`.** The visual register of the
  document-not-meant-for-the-reader — FBI Vault / FOIA reading-room /
  Wikileaks / Stasi-files lineage. Six provenance values, two redaction
  grammars (gov-at-creation vs view-time censorship), exemption-code
  system, classification banners, decl stamps, case-file paratext,
  aging-as-era-distance, and a four-handed marginalia vocabulary. For
  fiction documents framed as released, worldbuilding bibles, or
  editorial pieces *about* secrecy.
- **`muriel.provenance` module + `[provenance]` brand.toml schema.**
  Records where a brand's tokens came from so a derived artifact can
  cite its source.
- **`muriel.aiism` — anti-AI-tell prose audit module.** Flags AI-tell
  vocabulary and constructions in prose; `regime` added to the loaded-
  vocabulary list.
- **`muriel.palettes` — colorblind-safe categorical palettes.** Wong /
  IBM / Tol ramps as an importable module.
- **Audience profiles for style guides.** Vocabulary becomes a brand
  parameter, so a guide can target a reader profile.
- **Typed front-matter schema across channels** (heatmaps,
  infographics, web, svg, diagrams, science, gaze) with worked
  exemplars; **`muriel-critique` channel-aware gates + P0 honesty
  probe**, codified as a CLI gate with a tools index; **diagrams**
  `engine_sectors_overlay` (Blauch isotropic-sectors cobweb) and
  `foveal_overlay` (Scrutinizer brand mark) primitives; social-card
  validation pass in the skill.
- **`vocabularies/muriel-brand.md`.** Canonical brand-identity spec for
  muriel itself — closes the irony gap of theming every other project
  from a documented brand while running on vibes for our own. Defines
  the six-bar mark with exact rect coordinates for full (with bar-6
  ascender) and inline (capped, no ascender) variants; lineage to
  Müller-Brockmann + Cooper VLW; color tokens matching
  `examples/muriel-brand.toml`; subpixel rendering floor at ~28-30px
  display width; wordmark conventions (`muriel` always lowercase,
  `built with muriel` as canonical attribution, Inter regular + semibold,
  no italic); drop-in HTML/SVG snippets for inline credit, block credit,
  and wordmark-only fallback. First production deployment of the inline
  form is the `inside_the_math` footer credit (psychodeli-webgl-port).

### Changed
- **Repackage as a Claude Code plugin.** `/plugin marketplace add andyed/muriel`
  + `/plugin install muriel@andyed-muriel` is now the canonical end-user
  install — no clone, no symlinks, `/plugin uninstall` reverses cleanly.
  `SKILL.md`, `channels/`, `vocabularies/`, `examples/` moved under
  `plugins/muriel/skills/compose/`; `agents/muriel-critique.md` moved under
  `plugins/muriel/agents/`. `.claude-plugin/marketplace.json` at repo root
  catalogs the single plugin. Cross-references inside the skill tree that
  pointed at the Python package or top-level `docs/` were rewritten to
  GitHub URLs (the plugin cache only copies the plugin root subtree, so
  `../muriel/...` no longer resolves at runtime). `install.sh` retained as
  the developer-checkout install path; symlinks now target the new
  `plugins/muriel/skills/compose/` location and the script refuses if the
  plugin install is already present, to avoid double-loading. Plugin
  invocation is namespaced `/muriel:compose`; the standalone install via
  `install.sh` continues to give the bare `/muriel`. Spec at
  [`docs/spec-plugin-packaging.md`](docs/spec-plugin-packaging.md).

## [0.7.0] — 2026-04-25

### Added
- **`vocabularies/katex.md`.** Names KaTeX as muriel's web math engine
  — MIT, CDN-clean, no bundler, pin `^0.16`. Documents the `.eq-block`
  pattern, `auto-render` configuration, color/emphasis with
  `\textcolor`, server-side rendering for stills, and integration with
  the marginalia channel and `channels/science.md` (KaTeX is for web,
  matplotlib + LaTeX is for paper). Reference exemplar: `inside_the_math`
  (psychodeli-webgl-port, shipped). Cross-referenced from `SKILL.md`'s
  vocabulary index and a new "Math — KaTeX" subsection in
  `channels/web.md`.
- **iblipper substrate role broadened.** `vocabularies/kinetic-typography.md`
  iblipper entry now covers both animated kinetic-type artifacts *and*
  single-frame social-media graphic stills where slogan-scale
  rhetorical typography is the work. Edit Message → export PNG covers
  the still path without IAP. SKILL.md vocab index updated to match.
- **`muriel import <design.md>`.** New subcommand ingests a Google
  Stitch [design.md](https://stitch.withgoogle.com/docs/design-md/)
  and produces a muriel `brand.toml`. Zero-dep: hand-rolled YAML
  frontmatter parser + TOML emitter for the subset muriel's
  brand.toml uses. Stitch colors → `[colors]` (accent /
  accent_decorative / background / foreground) plus unmapped roles
  into `[colors.named]` + `[colors.aliases]`; Stitch typography →
  `[typography.scale]` + family at body/mono/display level; Stitch
  rounded → `[radii]`; elevation/motion preserved; Stitch
  `contrast.minimum < 8.0` warns to stderr and is recorded under
  `[a11y.imported_min_contrast_ratio]` while muriel's 8.0 floor
  stays the gate; prose Components / Do's-and-Don'ts preserved as
  `[rules.imported_*]` strings. Export direction (toml → design.md)
  queued.
- **`channels/diagrams.md` + `muriel.tools.diagrams`.** Eleventh channel.
  Rhetorical-primitive diagrams as deterministic SVG. MVP ships
  `matrix(quadrants, axes, …)` (2×2 categorical decomposition) and
  `cycle(steps, …)` (3–8 step iterative process). Each generator
  writes hand-rolled SVG with brand-aware fallback to the OLED
  palette and carries an explicit *epistemic precondition* +
  *anti-prescription* in its docstring. JSON-spec CLIs at
  `python -m muriel.tools.diagrams.{matrix,cycle}`. Worked examples
  in `examples/diagrams/`. Catalog table in the channel doc names
  the queued primitives (comparison pair, funnel, stack, DAG,
  spectrum, pyramid, heat-grid).
- **FUI vocabulary expanded to peer parity.** `vocabularies/fui.md`
  now carries a substrate decision table, common-failures list,
  cross-vocabulary SDF alpha rule, and integration points across
  channels. New runnable single-file scaffold at
  `examples/fui-scaffold.html` demonstrates four primitives (data
  ticker, radial compass, Canvas waveform, staggered reveal),
  corner brackets, scan-line overlay, and `prefers-reduced-motion`
  fallback — all on the known-safe 8:1 palette and driven by
  `--mg-duration-reveal` / `--mg-ease-emphasis`. New "Sci-fi UI
  patterns" subsection in `channels/interactive.md` names the
  canonical stack and points at the scaffold.
- **`muriel-critique` agent: vision-model sharpening.** Adds a
  Visual Inventory step 0 (3–5 sentence structural describe-before-
  judge pass), a per-artifact-type workflow table (PNG/JPG → look;
  SVG → grep + rasterize; PDF → pages; HTML/animated → decline),
  honest-hedging rule on contrast (verbal floors over fake decimals
  unless computed), and two new cross-channel checks: text-rendering
  integrity (mangled glyphs, duplicated letters, Cyrillic-in-Latin)
  as `CRITICAL`, and occlusion/overlap as a layout-bug tell.
- **`muriel-critique` agent: scoped Bash for compute calls.** Agent
  now has `Bash` in its `tools` list, scoped via project
  `.claude/settings.json` (committed; `.gitignore` negated) to
  read-only invocations of `muriel.contrast`, `muriel.oklch`, and
  `cairosvg` across `python` / `python3` / `.venv/bin/python` /
  `uv run` prefixes. Lets the agent cite exact WCAG ratios on SVG
  artifacts and rasterize SVG → PNG for real visual audits instead
  of eyeballing XML.
- **`critique` extra in pyproject.toml.** New optional dependency
  group declaring `cairosvg>=2.7` for the rasterizer path. Rolled
  into the `all` convenience extra.
- **Top-level `TODO.md`** consolidating the previously-scattered
  roadmap (CHANGELOG, SKILL.md, commit messages, per-channel
  hints) into Active / Queued / Someday / Won't-do sections.

### Changed
- **Tone pass across `README.md`, `channels/interactive.md`,
  `channels/style-guides.md`, `channels/infographics.md`, and
  `vocabularies/fui.md`.** Removed "next-gen" / "highest-leverage" /
  "unlocks" softening; tightened explainer-mode openings on
  style-guides and infographics; replaced the territory-marking
  framing in infographics with direct positioning. Channel-doc
  headings remain mixed pending a later standardization pass.
- **`muriel/__init__.py` docstring** updated for the OKLCH module
  and lists eight modules (was seven).
- **Unused imports removed** from `muriel/contrast.py`,
  `muriel/typeset.py`, and `muriel/oklch.py` (`field`, `math`,
  `sys`, `Union` respectively).

## [0.6.0] — 2026-04-23

### Added
- **`muriel.oklch` module.** Stdlib-only OKLCH / OKLab conversion
  (Ottosson 2020 / CSS Color Module Level 4), CSS `oklch()` parser
  covering the full CSS 4 grammar (percentages, angle units, `none`,
  legacy commas, alpha tolerated-and-discarded), sRGB gamut check, and
  chroma-bisection clamp that preserves L and h. Roundtrip is
  bit-exact on sRGB integer channels; primaries match Ottosson's
  reference values to four decimals.
- **`contrast.parse_color` accepts `oklch(...)`.** Every existing
  contrast helper — `contrast_ratio`, `check_text_pair`, `audit_svg`
  — now accepts OKLCH inputs transparently via a lazy import.
  Out-of-gamut OKLCH is auto-clamped so hue and lightness are
  preserved instead of hard-clipping the channel.
- **CLI.** `python -m muriel.oklch <color>` inspects any color
  (hex / `rgb()` / named / `oklch()`) and reports hex, sRGB, OKLCH,
  and gamut status; `--clamp` additionally reports the chroma-clamped
  OKLCH and ΔC for out-of-gamut OKLCH inputs.
- **`brand.toml` schema v2** covering the full design-token surface:
  `[spacing]`, `[radii]`, `[elevation]` structural ramps;
  `[typography.scale]` named type scale (display, h1–h4, body, body_small,
  caption, label, mono); `[semantic.*]` `{text, surface, border}` trios
  replacing the ad-hoc `note/tip/warning/important` fields;
  `[viz]` categorical / sequential / diverging palettes;
  `[iconography]` + `[imagery]` (with `crop_policy` hook into smartcrop);
  `[logo]` variants (wordmark / monogram / stacked / horizontal) with
  clear-space and min-width rules; `[voice]` adjectives + say-yes /
  say-no; `[a11y]` floors (`min_contrast_ratio`, `min_hit_target_px`,
  `focus_ring_*`, `motion_reduce_policy`).
- **Brand-driven contrast floor.** `StyleGuide.audit_contrast()` now
  defaults to the brand's own `a11y.min_contrast_ratio` (falls back to
  muriel's universal 8.0) instead of requiring an explicit argument.
- **CSS vars emitter expansion.** `to_css_vars()` now emits the full
  token surface: semantic-state trios, spacing / radii / elevation
  ramps, motion durations + easings, the full type scale (size / weight
  / line-height / tracking per role), and a11y hooks.

### Changed
- `examples/muriel-brand.toml` and `examples/example-brand.toml`
  rewritten against v2, each populating every optional block.
- `examples/example-brand.toml` `named` and `viz.categorical` entries
  bumped to clear muriel's 8:1 floor (`wildflowers`, `tiedye`,
  `violet`); `accent_decorative` now actually fails 8:1 to match its
  role.
- `muriel/tools/venn.py` `_region_colors` ported off the v1
  `colors.{tip,warning,important}` fields to the v2
  `viz.categorical` palette with `semantic.*` fallback.

## [0.5.0] — 2026-04-18

First public release. The project was previously named `render`; this
release formalizes the rename in honor of Muriel Cooper (1925–1994) and
consolidates the codebase.

### Added
- **Cooper tribute** in the README, placed after the opening paragraph
  before Channels. Cites Reinfurt & Wiesenberger (MIT Press, 2017) and
  David Small's *Rethinking the book* (MIT PhD, 1999).
- **Four named vocabularies** under `vocabularies/`: FUI, Visible
  Language, PixiJS, Kinetic Typography — design grammars to borrow from
  rather than reinvent.
- **PixiJS vocabulary** is a curated subset of [pixijs/pixijs-skills](https://github.com/pixijs/pixijs-skills) (MIT). Upstream is the source of truth.
- **Anti-patterns sections** in every channel doc — negative rules that
  complement the positive universal rules. Lifted in spirit from
  pbakaus/impeccable.
- **Two-tier brand schema.** `[colors.aliases]` block in `brand.toml`
  routes semantic roles (text, text-muted, decorative, surface-*,
  semantic-*) to raw colors. Unblocks text-accent vs decorative-accent
  distinction that was needed for light palettes.
- **Motion token block.** New `[motion]` section in `brand.toml` with
  duration (instant/fast/normal/slow/reveal) and easing tokens. Consumed
  by kinetic-typography, interactive, and video channels.
- **`muriel/examples/gallery/`** — 7 worked examples mapping shipped
  figures to muriel channels, each with a thumbnail and a live-post link.
- **`muriel/examples/logos/`** — colophon hero mark (still + animated)
  reinterpreting Cooper's mitp colophon for "muriel."
- **ascii-charts fold.** `chart.py`, `typeset.py`, `gen_og_batch.py`,
  `docs/PERMUTE.md`, and `templates/` moved into muriel. Former
  ascii-charts repo now redundant.
- **`muriel.dimensions`** — 34 named size presets, 17 device footprints,
  5 paper sizes, `figsize_for()` helper for 7 academic venues.
- **`muriel.capture`** — Playwright responsive viewport-sweep capture.
- **`muriel.styleguide`** — `brand.toml` loader with contrast audit, CSS
  variable derivation, matplotlib rcparams derivation, ownership rules.
- **`muriel.stats`** — APA-style reporting helpers enforcing
  detection-limit framing for nulls, proper minus-sign typography, and
  leading-zero stripping.
- **`muriel.contrast`** — WCAG contrast audit module + CLI with exit
  codes for CI use. Enforces muriel's 8:1 text rule.

### Changed
- Python package renamed `render_assets` → `muriel`. A deprecation
  shim at `render_assets/__init__.py` re-exports from muriel with a
  `DeprecationWarning`; existing notebooks continue to work for one
  release cycle.
- Skill directory renamed `~/.claude/skills/render/` → `~/.claude/skills/muriel/`.
- `SKILL.md` frontmatter `name: render` → `name: muriel`.
- All `~/Documents/dev/render/` paths in docs and CLI help text updated
  to `~/Documents/dev/muriel/`.

### Removed
- Personal research artifacts from the public repo. `psychodeli-brand.toml`
  and word-fingerprints SVG fixtures moved to a private sidecar skill
  (`muriel-personal`) and replaced with synthetic `example-brand.toml` /
  `example-palette.svg` fixtures that exercise the same code paths.

### Deprecated
- `render_assets` Python import path. Will be removed in 0.7.0. Update
  imports to `from muriel import ...` when convenient.
