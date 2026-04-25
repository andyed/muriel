# Changelog

All notable changes to muriel are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
version numbers follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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
