# Scenario — Math-rich Long-form Essay

A canonical multi-channel demo binding marginalia (long-form HTML), KaTeX (web math typesetting), `typeset.py` figures (static raster), and Manim CE figure stills (when `channels/motion.md` ships) into one publishable, math-heavy essay. The scenario forces muriel's math story to be coherent end-to-end.

The arc exists for two reasons:

1. **As a publishable artifact pattern.** Math-rich long-form is one of the most asked-for output shapes for technical writing — explainers, derivations, model documentation, paper companions. muriel should be able to scaffold a new one in minutes from `brand.toml` plus prose + math source, and a returning writer should be able to extend it without re-deriving the integration patterns.
2. **As a forcing function for the math channel work.** Each piece of the essay exercises a specific muriel surface that today is either undocumented, hand-rolled, or out-of-band. Building the arc proves the surfaces carry the load.

## Reference exemplar

`inside_the_math` (shipped, in `psychodeli-webgl-port/inside_the_math/`):

- 3,856-line `index.html` plus a 3,880-line `index-marginalia.html` variant.
- Math: KaTeX `0.16.9` via CDN, `auto-render` walking `$$…$$` (display) and `$…$` (inline) delimiters.
- Document: marginalia patterns, themed via CSS custom properties.
- Equations: rendered inside themed `.eq-block` containers with sectional background images and brand-accented border-left.
- Figures: hand-rolled WebGL demos and SVG diagrams inline in the prose.

The reference is shipped — *don't rewrite it*. The scenario lifts patterns from it and documents them as muriel-reusable.

## Audience

- Primary: technical writers producing math-heavy explainers (model papers, derivation walk-throughs, algorithm tutorials, research-companion essays for Scrutinizer / AdSERP / Psychodeli work).
- Secondary: any author who needs to mix prose, math, code, and figures in a single web artifact and wants the artifact to look intentional rather than templated.

## Format outputs (all from one source pipeline)

| Output | Where it lands | Substrate |
|---|---|---|
| **Web essay** (the canonical form) | Project blog, GitHub Pages, marginalia-themed standalone HTML | marginalia + KaTeX + inline figures |
| **Static-figure variant** | Paper companion, arxiv preprint, print PDF | Same prose body via `weasyprint`/Playwright capture; equations rasterize; figures already raster |
| **Single-image hero** | Social-card / OG share for the essay | `typeset.py` headline + brand-themed background; pulls one signature equation as still |
| **Excerpt social-graphic** | Twitter / LinkedIn share of one striking equation | iBlipper single-frame mode (post-`@andyed/kinetic-type-engine` extraction) themed from `brand.toml` |

The point: marginalia + KaTeX is the source of truth; everything else falls out by rendering or extracting from it.

## The five panels (composition contract)

Each "panel" here is a distinct piece of the essay-as-artifact, not a slide. A real essay weaves them; the scenario names each one as a forcing function for a muriel surface.

### Panel 1 — Prose body with inline math

**Claim:** *Inline math reads like prose, not like a code block.* `KaTeX` inline expressions (`$…$`) inherit color and line-height from the surrounding paragraph; the marginalia `mg-` palette propagates into KaTeX glyph color via CSS custom properties.

**Surface:** `vocabularies/katex.md` (shipped) + `channels/web.md` "Math — KaTeX" subsection (shipped).

**Pattern:** load KaTeX + `auto-render` via CDN; configure `delimiters` for `$…$` and `$$…$$`; set `p { line-height: 1.65 }` so inline math doesn't crowd surrounding lines.

### Panel 2 — Display equations as designed objects (`.eq-block`)

**Claim:** *Block-level math in long-form prose is a designed element, not a bare TeX dump.* Wrap each display equation in a themed `.eq-block` container with brand-accented border-left, optional sectional background-image at low opacity, and inherited contrast from the marginalia palette. The pattern is lifted directly from `inside_the_math`.

**Surface:** `vocabularies/katex.md` `.eq-block` pattern (shipped).

**Forces:** the marginalia ↔ KaTeX integration to actually work — `--mg-bg`, `--mg-border`, `--mg-accent` need to flow into `.eq-block`'s computed styles. If a future marginalia palette change breaks the equation containers, the scenario catches it.

### Panel 3 — A worked derivation as a 4–8 frame contact sheet

**Claim:** *Derivations should display step-by-step in long-form prose without forcing the reader into video.* A multi-step derivation (apply rule → simplify → substitute → evaluate) renders as a numbered frame sequence — typically 4–8 stills — composed into a single contact-sheet PNG and embedded as `<figure>` between two paragraphs of prose.

**Surface:** `channels/motion.md` (queued — Manim CE adapter) + `typeset.contact_sheet(frames, cols)` (queued helper).

**Forces:** Manim CE figure-embedding contract — *what does a Manim output that's intended for a marginalia essay actually look like?* The scenario answers: a numbered PNG sequence at the channel's web target dimensions, themed from `brand.toml`, composed into a contact sheet by `typeset.py`, captioned in marginalia. No video required for inline pedagogy.

### Panel 4 — A signature equation as a static hero

**Claim:** *Every math-rich essay has one signature equation worth lifting as the OG card / social hero.* Pull one display equation, render it server-side via `katex.renderToString()`, rasterize the resulting HTML through `muriel/capture.py` at OG-card dimensions, composed against a `typeset.py`-rendered branded background.

**Surface:** `vocabularies/katex.md` server-side rendering (shipped) + `muriel/capture.py` (shipped) + `typeset.py` (shipped).

**Forces:** the social-card path for math content — proves an essay can ship its own share assets without hand-roll in Figma.

### Panel 5 — One excerpt as a kinetic-typography social graphic

**Claim:** *A short, striking equation — or the verbal claim attached to it — can ship as a social-media graphic in iBlipper's rhetorical-typography idiom, themed from the same `brand.toml` as the essay.* Slogan-scale typography for the verbal claim, optionally followed by the equation as a held final frame.

**Surface:** iBlipper single-frame mode (existing) + `vocabularies/kinetic-typography.md` (shipped) + `@andyed/kinetic-type-engine` (per [iblipper2025 extraction spec](https://github.com/andyed/iblipper2025/blob/main/docs/kinetic_type_engine_extraction_spec.md), pending).

**Forces:** the muriel ↔ kinetic-type-engine integration. Until the engine is extracted, this panel ships in degraded form — a hand-themed iBlipper URL or a `typeset.py` headline still. Post-extraction, it's a programmatic call themed from `brand.toml`.

## Channel build order (forces the sequencing)

The scenario depends on shipped + queued surfaces. To make it shippable end-to-end:

**Already shipped (Panels 1, 2, 4 work today):**
1. **marginalia channel** (`channels/web.md`) — the document substrate.
2. **KaTeX vocabulary** (`vocabularies/katex.md`, v0.7.0) — math engine + `.eq-block` pattern.
3. **`typeset.py`** — branded headline / background composition.
4. **`muriel/capture.py`** — Playwright HTML → PNG.

**Queued (unlocks Panel 3):**
5. **`channels/motion.md` Manim CE adapter** — TODO top-2 extension. Needed for the worked-derivation contact sheet. Other motion adapters (Motion Canvas, Lottie) aren't required for this scenario.
6. **`typeset.contact_sheet(frames, cols)`** helper — composes numbered frames into a single PNG. Cheap; can ship alongside the Manim adapter.

**Queued + dependency on extraction (unlocks Panel 5 in full form):**
7. **`@andyed/kinetic-type-engine`** — extracted from iblipper2025 per the [extraction spec](https://github.com/andyed/iblipper2025/blob/main/docs/kinetic_type_engine_extraction_spec.md). Until phase 3 lands, Panel 5 ships in degraded form (hand-themed URL or `typeset.py` headline).

If the Manim adapter slips, Panel 3 falls back to a hand-rolled SVG-step diagram. If the engine extraction slips, Panel 5 falls back to `typeset.py`. The essay-as-arc still ships with placeholders; the channels just don't get their full forcing-function exercise.

## Reusability — each panel is also a standalone

Every panel is designed to ship independently:

- Panel 1 alone: any prose page with inline math (technical doc, blog post, README).
- Panel 2 alone: a single equation as a designed callout in any marginalia document.
- Panel 3 alone: a contact-sheet figure in a paper or report — Manim is doing the math; muriel is doing the layout.
- Panel 4 alone: an OG card / social hero for any math-related artifact.
- Panel 5 alone: a kinetic social graphic for any rhetorical claim, math or not.

The atoms compose into the essay; they also compose into anything else.

## Brand and contrast contract

Everything passes muriel's universal rules:

- 8:1 contrast on every text element including KaTeX glyphs against `.eq-block` background.
- Decorative strokes ≥55/255 on dark background; sectional background images at ≤14% opacity (per the `inside_the_math` `.eq-block::before` pattern).
- Single font family per surface (`brand.typography.serif` for body, `brand.typography.sans` for headings; KaTeX's bundled math fonts are used for math glyphs and don't honor `brand.toml`'s typography keys — that's a documented exception, not a bug).
- OLED palette baseline; brand-token import from project `brand.toml` overrides.
- All sectional background images optional and lazy-loaded; the essay must remain legible without them.

This is also a stress-test of the math-display brand discipline: five surfaces, one palette, one type system. If the essay looks coherent end-to-end, the math story is integrated.

## Critique pass

Every panel runs through `muriel-critique` before it ships:

- **Visual inventory step 0** describes structure before judging content.
- **Contrast** (8:1 floor) on every text element, computed not estimated.
- **Text-rendering integrity** — no mangled glyphs, no Cyrillic-in-Latin (KaTeX has known edge cases with certain font fallbacks).
- **Brand-fit (ΔE-OK)** on rendered colors against `brand.toml` tokens.
- **Sequence consistency** for Panel 3 contact sheets — no font fallback mid-sequence, no unexpected scale jumps between frames.
- **Caption presence** — every figure inside the essay has non-empty `alt` and visible `<figcaption>`.

A scenario render that fails any of these is the diagnostic, not the deliverable.

## Acceptance

The scenario is "done" when an author can:

1. Drop a prose-plus-math source (markdown with KaTeX delimiters and embedded figure references) into a muriel-scaffolded marginalia essay.
2. Theme it with one project's `brand.toml`.
3. Render to HTML in under five minutes, with all five panels producing or degrading gracefully based on which queued channels are shipped.
4. Re-theme the same essay with a different `brand.toml` and rebuild without per-panel hand-tuning.
5. Pass `muriel-critique` on first or second iteration.

When a contributor can do all five for a new essay in the time it takes to write the prose, the math story is coherent.
