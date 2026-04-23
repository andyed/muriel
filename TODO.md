# muriel — roadmap

Consolidated from `CHANGELOG.md`, `SKILL.md`, commit messages, and per-channel roadmap hints. Source of truth for what's next; `CHANGELOG.md` is source of truth for what's shipped.

## Active

- [ ] **Cut 0.6.0.** `[Unreleased]` block in `CHANGELOG.md` is ready: OKLCH module + brand.toml schema v2. Commit the uncommitted OKLCH changes, move the block, tag.
- [ ] **Screenshot designer P0.** (from commit `533e32b`) Table-stakes compositor for marketing/doc screenshots: `drop_shadow()`, `fade_edge()`, `border_radius()`, `background()` (solid / gradient / mesh / blur / noise), `caption()` + dimension presets. Target channel: `channels/raster.md`, implementation under `muriel/tools/screenshot.py`.
- [ ] **FUI productionization.** `vocabularies/fui.md` is a 56-line reference card; peer vocabularies have substrate decision trees, SDF rules, "common failures" lists, and working exemplars. Expand to parity, then add a `channels/interactive.md` "Sci-fi UI patterns" subsection with four scaffold demos (ticker, compass, scan-line overlay, staggered reveal) and a CodePen Prefill.

## Queued

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

## Release gate

- `render_assets` deprecation shim is committed to removal in **0.7.0** (see `CHANGELOG.md [0.5.0] Deprecated`). Do not remove before then.
