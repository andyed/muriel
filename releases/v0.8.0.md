# muriel v0.8.0 — the rigorous round-trip

*Released 2026-05-17.*

This is the release that closes loops. The design.md → brand.toml → tokens.json round-trip got honest (corpus audit + three importer fixes), got fully two-way (new DTCG exporter), and grew a new visual surface that wires into both ends (spatial perspective grids + Three.js exemplars). It's the first release where you can take a brand from `awesome-design-md`, pull it into muriel, ship outward to any DTCG-aware downstream, *and* render type into felt space without leaving the toolkit.

The unifying claim — first articulated in the corpus harness, now operational — is that **muriel is the rigorous offline cousin of DESIGN.md**: it consumes the corpus, exports out to the W3C standard, and refuses to lower the 8:1 floor through any of it. Not the warm one. Not the friendly one. The one that names PostHog at 7.20 and ElevenLabs at 7.63 in writing.

---

## Spatial — depth scaffolding for typography

The Cooper VLW / Mackinlay-Robertson-Card / Dumais Data Mountain lineage finally has a primitive. Two coupled surfaces:

- **`muriel.spatial`** — pure-Python SVG perspective grids. `grid("1pt"|"2pt"|"3pt"|"iso", BBox(...))` returns a frozen `PerspectiveGrid` with `.svg()` emit. Tron-style cyan-on-near-black defaults, Liang-Barsky line clipping, fade-to-horizon depth weighting.
- **`render_assets/`** — Three.js + CSS3DRenderer exemplars sharing one helper lib. Two-renderer stack (WebGL grid underneath, CSS3D DOM on top) so text stays selectable, copyable, and screen-reader addressable. Five exemplars across two brand families (psychodeli + sciprogfi): spatial-typography, two Data Mountains, two Perspective Walls.
- **`channels/spatial.md`** — the lineage doc (Alberti 1435 → Dürer 1525 → Cooper VLW 1980s → Mackinlay 1991 → Dumais 2001 → Tron) with the anti-prescription baked in: *"if you can't name which lineage the composition belongs to, you're decorating, not arguing."*

Static and interactive sides share a coordinate system by design. The queued `typeset_scene()` will close that loop — take a `PerspectiveGrid` plus DOM blocks with anchor names, emit a runnable scene/index.html so a paper figure and a fly-through share their geometry by construction, not by hand-port.

## DTCG export — round-trip to the W3C ecosystem

`muriel export-dtcg brand.toml` emits W3C Design Tokens Community Group JSON. Every brand.toml v2 block maps to a canonical DTCG type group (`color`, `dimension`, `fontFamily`, `typography`, `duration`, `cubicBezier`, `shadow`). Muriel-specific carry-overs (iconography, logo, voice, motion preference, typography `upper:true`) land under `$extensions.muriel.*` so a future round-trip importer can recover them.

**End-to-end verified**: all 61 import-parseable `awesome-design-md` brands round-trip cleanly through `parse_design_md → to_dtcg`. The exported JSON drops straight into `style-dictionary`, `theo`, Figma tokens-studio, or token-css, and from there into iOS / Android / Tailwind / CSS-vars pipelines.

## Corpus audit + three design_md_import fixes

`muriel import-corpus <path>` runs an entire DESIGN.md corpus through the importer and reports per-brand. Three output formats (`summary` / `md` / `json`), a CI gate (`--fail-on {any-error,any-contrast-fail}`), and honest 8:1 accounting (brands whose bg/fg muriel defaulted are flagged, so the marketing artifact never claims a pass on muriel's own defaults).

Run against the 71-brand `awesome-design-md` corpus, the harness immediately surfaced three real bugs in `design_md_import`. Before / after on the same harness:

| metric | initial | shipped |
|---|---:|---:|
| Parsed cleanly | 48 (67%) | **61 (85%)** |
| Parse errors | 13 | **0** |
| Pass 8:1 on real source colors | 0 | **48** |
| Brands with bg AND fg defaulted | 42 | **0** |
| Total WARNs raised | 90 | **0** |

The three fixes:

1. **`STITCH_COLOR_PRIORITY`** — priority-ordered color-key list replaces the old flat dict. Adds the canonical awesome-design-md / Anthropic keys (`canvas`, `ink`, `body`, `primary`) plus 16 variants. Recovers 42 brands.
2. **Anchor / ref detection scoped to value-start** via `^[&*]\w[\w-]*\b`. No more false positives on Ferrari's `**near-black** (...)` prose.
3. **YAML block scalars (`|`, `>`) preprocessed** via `_expand_block_scalars`. Nike / NVIDIA / Ollama / Renault / Replicate / Resend / Revolut / opencode.ai all now ingest. Sentinel lesson learned: `str.splitlines()` silently splits on U+2028 / U+2029 — use a Private Use Area codepoint instead.

### Hall of shame — brands shipping below muriel's 8:1 floor

Sorted by ascending contrast on their stated `body × canvas` pair:

| brand | contrast | bg | fg | note |
|---|---:|---|---|---|
| binance | 1.18 | #ffffff | #eaecef | spec ambiguity (body intended for dark canvas) |
| together.ai | 3.03 | #ffffff | #959494 | |
| vodafone | 4.06 | #ffffff | #7e7e7e | |
| wired | 4.61 | #ffffff | #757575 | |
| ollama | 4.74 | #ffffff | #737373 | |
| expo | 5.94 | #ffffff | #60646c | |
| ferrari | 6.00 | #181818 | #969696 | |
| coinbase | 6.21 | #ffffff | #5b616e | |
| uber | 6.48 | #ffffff | #5e5e5e | |
| zapier | 6.54 | #fffefb | #605d52 | |
| cursor | 6.63 | #f7f7f4 | #5a5852 | |
| posthog | 7.20 | #eeefe9 | #4d4f46 | **passes WCAG AAA (7:1), fails muriel 8:1** |
| elevenlabs | 7.63 | #f5f5f5 | #4e4e4e | **passes WCAG AAA (7:1), fails muriel 8:1** |

The PostHog / ElevenLabs pair is the cleanest argument *for* the 8:1 floor — well-resourced design teams shipping at 7.2 thinking they're safe, when AAA isn't enough for the reading conditions most people actually have.

## Generative pattern primitives — `muriel.patterns`

Three deterministic background primitives, pure Python, zero deps:

- **`dots`** — Bridson Poisson-disk sampling for even visual density without obvious tiling.
- **`flow`** — value-noise vector field traced as short polyline streamlines (LIC-style after Cabral & Leedom 1993).
- **`grain`** — value-noise raster as a small SVG `<pattern>` tile that repeats; file size stays O(tile_cells²) regardless of canvas.

All routes through `hashlib.blake2b` so the same `seed` produces byte-identical output across platforms. Unblocks the screenshot-designer P0 `background()` arg.

## Small additions

- **`parse_design_md(text, source=None)`** — public, non-IO counterpart of `import_design_md`. Lets batch ingest and tests work in memory without temp files. The corpus harness depends on it.

## Try it

```bash
# Run the entire awesome-design-md corpus through muriel
git clone https://github.com/VoltAgent/awesome-design-md /tmp/awesome-design-md
muriel import-corpus /tmp/awesome-design-md
muriel import-corpus /tmp/awesome-design-md --format md -o corpus_report.md

# Single-brand round-trip
muriel import /tmp/awesome-design-md/design-md/stripe/DESIGN.md --out stripe-brand.toml
muriel export-dtcg stripe-brand.toml -o stripe-tokens.json

# Try the visual surfaces
python -m muriel.spatial --demo > spatial.svg
python -m muriel.patterns --demo > patterns.svg
open render_assets/index.html
```

## Upgrade notes

- **No breaking changes.** `STITCH_COLOR_TO_MURIEL` is kept as a legacy flat-dict mirror of `STITCH_COLOR_PRIORITY` for any external consumer; new code should consult the priority list directly.
- Python 3.10 still supported for the in-memory paths (`to_dtcg(dict) → dict`, every selftest). Python 3.11+ required for the file-based `export_dtcg(path)` (stdlib `tomllib`); the module raises a clear `DTCGError` with the upgrade hint on 3.10.

## Verified

```
python -m muriel.spatial --selftest        # passes
python -m muriel.patterns --selftest       # passes
python -m muriel.dtcg_export --selftest    # passes
python -m muriel import-corpus /tmp/awesome-design-md
  # 71 brands · 61 parsed · 48 pass 8:1 · 13 fail · 0 errors · 0 WARNs
```

## Credits — sources of inspiration

This release builds on, references, or is informed by the following projects. Crediting the MIT-licensed ones first because Andy said to.

### MIT

- [`VoltAgent/awesome-design-md`](https://github.com/VoltAgent/awesome-design-md) — the 71-brand DESIGN.md corpus this release audits, exports, and credits in the hall of shame. Most of the importer fixes in this cut exist because the corpus surfaced them in under three seconds.
- [`mrdoob/three.js`](https://github.com/mrdoob/three.js) — every `render_assets/` exemplar runs on three.js + the bundled CSS3DRenderer addon. The two-renderer stack (WebGL underneath, CSS3D on top) is verbatim three.js idiom.
- [`css-doodle/css-doodle`](https://github.com/css-doodle/css-doodle) — pattern-language lineage referenced in `muriel.patterns`. The "rule-based generative grid" framing came from here.
- [`baku89/glisp`](https://github.com/baku89/glisp) — pattern-language lineage. Lisp-as-design-DSL reference for the patterns docstring.
- [`nannou-org/nannou`](https://github.com/nannou-org/nannou) (MIT / Apache-2.0 dual) — pattern-language lineage. The Rust-creative-coding peer to the kind of work `muriel.patterns` does in Python.
- [`shiffman/The-Nature-of-Code-Examples`](https://github.com/shiffman/The-Nature-of-Code-Examples) — Shiffman's *Nature of Code* algorithm catalog. Referenced in `muriel.patterns` for physics primitives; the canonical pond for the queued `channels/motion.md`.

### Permissive (non-MIT) — the DTCG downstream we feed

- [`amzn/style-dictionary`](https://github.com/amzn/style-dictionary) (Apache-2.0) — the canonical DTCG consumer. `muriel.dtcg_export` is shaped to feed this directly: hand its output to style-dictionary's build system to produce CSS vars / iOS / Android / Tailwind.
- [`salesforce-ux/theo`](https://github.com/salesforce-ux/theo) (BSD-3-Clause) — older sibling of style-dictionary; same DTCG-consumer slot.

### Spec

- [Design Tokens Community Group format](https://design-tokens.github.io/community-group/format/) — the W3C draft this release maps brand.toml v2 onto. The `$value` / `$type` / `$extensions` shape, the `{group.token}` alias syntax, the composite-typography schema, the cubic-bezier and shadow types — all consumed verbatim. Community-driven under the W3C Community Group process.

### Historical / academic — already cited inline in `channels/spatial.md`

The spatial channel's lineage table runs Alberti 1435 → Dürer 1525 → Cooper VLW 1980s → Mackinlay-Robertson-Card 1991 → Robertson Information Visualizer 1993 → Dumais Data Mountain 2001. The patterns algorithm references are Bridson 2007 (Poisson-disk) and Cabral & Leedom 1993 (LIC). Both credited at the point of use; not duplicated here.

## What's next (TODO highlights)

- **`muriel.spatial.typeset_scene()`** — Python emitter closing the static-↔-interactive coordinate-sharing loop.
- **Wire `muriel.patterns` into `muriel.tools.screenshot.background()`** — the screenshot-designer P0 backbone.
- **DTCG aliases for typography composites** — currently each composite is fully expanded; aliasing common shapes would shrink output.
- **A v0.7-equivalent of the parser for the 10 no-frontmatter brands** is **explicitly out of scope** — those entries are corpus-curation choices (pure markdown design notes), not parser bugs.
