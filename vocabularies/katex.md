# KaTeX — math typesetting for the web

**When to reach for it.** When prose has math in it and the artifact lands on a web surface (marginalia essay, blog post, in-page explainer, infographic-with-equations). KaTeX renders LaTeX-syntax math to HTML+CSS — no canvas, no images, no MathJax-style runtime overhead — and works inside any of muriel's web channels.

Use it for:

- **Math-rich essays** rendered as long-form HTML (the [`inside_the_math`](https://github.com/andyed/psychodeli-webgl-port/blob/main/inside_the_math/index-marginalia.html) reference exemplar). Equations appear next to prose, themed from `brand.toml`, with no image-export step.
- **Single-equation callouts** inside any HTML output (marginalia callouts, infographic captions, deck slides).
- **In-page derivations.** A `display: block` equation per step, prose between, no Manim required for prose-side step-throughs.
- **Branded equation blocks** — equations as first-class designed elements, not raw math jammed into a paragraph.

Don't reach for it when:

- The artifact is a paper figure or print PDF. Use the [science channel](../channels/science.md) — matplotlib's mathtext (or true LaTeX via `usetex=True`) keeps everything in one rendering pass.
- The math is *moving* (equation morphs, glyph-level transitions, `TransformMatchingTex`-style rewrites). Use Manim CE — KaTeX renders one static frame at a time.
- The expression depends on a `\TeX` package KaTeX doesn't support ([function-support reference](https://katex.org/docs/supported.html)). Fall back to MathJax for that one document; KaTeX is faster but covers a smaller surface.

## Version and licensing

- Pin to **KaTeX `^0.16`** (latest at time of writing: `0.16.45`). The 0.16 line is the current stable; no 1.0 on the horizon.
- KaTeX is **MIT** — clean for muriel's outbound MIT license.
- Auto-render extension ships in the same package (`contrib/auto-render.min.js`).

## Quick start (CDN, lifted from `inside_the_math`)

The canonical setup is a `<link>` for CSS, a `<script>` for the engine, and a one-line auto-render call that walks the document for `$$…$$` (display) and `$…$` (inline) delimiters:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body, {
    delimiters: [
      { left: '$$', right: '$$', display: true },
      { left: '$',  right: '$',  display: false }
    ]
  });"></script>
```

`defer` matters — the engine and the contrib script must run after DOM parse, in order. The `onload` hook on the last script is what triggers the walk; everything's CDN-clean and no bundler is needed (matches muriel's no-bundler doctrine).

## Patterns worth knowing

### Equation blocks as designed objects (`.eq-block`)

Inline `$$…$$` is fine for casual math, but a math-essay surface usually wants equations rendered as named, themed blocks. The `inside_the_math` pattern wraps each display equation in a `.eq-block` container, themes it from CSS variables, and (optionally) lays a thematic background image at low opacity behind it for sectional accent:

```html
<div class="eq-block">
  $$\vec{F}_{total} = \sum_{i=1}^{N} \frac{w_i (\vec{K}_i - \vec{P})}{|\vec{K}_i - \vec{P}|^p}$$
</div>
```

```css
.eq-block {
  position: relative;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);   /* brand.accent stripe */
  border-radius: 0 4px 4px 0;
  padding: 1.2rem 1.5rem;
  margin: 1.5rem 0;
  overflow: hidden;
}
.eq-block::before {                        /* optional sectional background */
  content: ''; position: absolute; inset: 0;
  background-size: cover; background-position: center;
  opacity: .08; pointer-events: none;
  transition: opacity .3s;
}
.eq-block:hover::before { opacity: .14; }
.eq-block .katex-display { position: relative; z-index: 1; margin: 0; }
```

Brand integration is pure CSS — `--bg2`, `--border`, `--accent` are populated from `brand.toml` via the existing `:root` resolver. No KaTeX-specific theming hooks needed; KaTeX inherits color from its container.

### Inline math inside prose

KaTeX inline math respects `font-size` and `color`; it doesn't respect `font-family` (it always renders in KaTeX's bundled math fonts, derived from Computer Modern / STIX). That's fine — math typography is its own thing — but be aware the math glyphs won't pick up `brand.toml`'s `font.serif` / `font.sans`. Match the surrounding prose by setting line-height to leave room for KaTeX's slightly taller display:

```css
p { line-height: 1.65; }                /* leaves room for inline math */
.katex { font-size: 1.05em; }           /* nudge KaTeX to match prose weight */
```

### Equation numbering

KaTeX supports `\tag{n}` and `\tag*{n}` inside an equation for explicit numbering, plus the `aligned` / `align` environments for multi-line numbered systems:

```latex
$$ E = mc^2 \tag{1} $$

\begin{align}
  a &= b + c \tag{2a} \\
  d &= e + f \tag{2b}
\end{align}
```

For automatic numbering across an entire document, use the [`auto-render`](https://katex.org/docs/autorender.html) extension's `output: 'mathml'` with custom CSS counters, or render via the JS API and inject `\tag{}` from a counter. The `inside_the_math` essay does this manually per equation — fine for a one-off; tooling-worthy if it becomes routine.

### Color and emphasis inside math

KaTeX supports `\color{#hex}{…}` and `\textcolor{#hex}{…}` natively. Use this for emphasis-during-derivation (the static analog of Manim's `Indicate`):

```latex
$$ \int_0^1 x^2 \,dx = \left[\textcolor{#ffd166}{\tfrac{x^3}{3}}\right]_0^1 = \tfrac{1}{3} $$
```

Hex literals here are a soft conflict with `brand.toml` (KaTeX's color macros don't read CSS variables). Either accept the hardcoded hex inside `\textcolor{…}` and treat them as content, or pre-process the LaTeX source to substitute `brand.accent` etc. before rendering.

### Server-side rendering for static stills

If the artifact target is a PNG (paper figure, social card, OG image) rather than a live web page, KaTeX can render server-side via the `katex.renderToString()` JS API or via [`katex-cli`](https://github.com/KaTeX/KaTeX/tree/main/cli). Combine with Playwright (`muriel/capture.py`) to rasterize the resulting HTML at the channel's target resolution.

## Integration with muriel channels

- **[`channels/web.md`](../channels/web.md)** — the marginalia-channel landing spot. KaTeX is the math layer for any marginalia-themed essay. The `inside_the_math` exemplar is the reference implementation.
- **[`channels/science.md`](../channels/science.md)** — *don't use KaTeX for paper figures.* Use matplotlib's `usetex=True` instead so the math compiles in the same TeX pass as the rest of the figure. KaTeX is for web; LaTeX is for paper.
- **[`channels/interactive.md`](../channels/interactive.md)** — KaTeX coexists with `@chenglou/pretext` and WebGL on the same page. Render math statically via auto-render after pretext lays out prose; the two don't conflict because pretext draws to canvas and KaTeX renders to HTML siblings.
- **[`channels/infographics.md`](../channels/infographics.md)** — KaTeX inside SVG `<foreignObject>` works for HTML-rendered infographics; for raster export, render the page in Playwright and screenshot.

## Reference exemplar

- **`inside_the_math`** — `psychodeli-webgl-port/inside_the_math/index-marginalia.html`. 3,880 lines. Math-heavy essay built on marginalia + KaTeX + WebGL demos. The `.eq-block` pattern, the per-section background-image accents, the auto-render configuration, and the `\textcolor` usage in this vocab are all lifted from here. Reference, don't rewrite.

## Rules that always apply

Muriel's universal rules apply to KaTeX equations the same way they apply to any other text:

- **8:1 contrast minimum** between math glyphs and equation-block background. KaTeX inherits color from its container; setting `.eq-block` background and `.katex` color in the same CSS pass keeps this auditable.
- **Label every quantity.** Inline math without a verbal anchor in the surrounding prose is illegible to skim. Don't drop a bare `$\Delta E$` and walk away.
- **Measure before drawing.** KaTeX's display blocks have intrinsic width that can overflow narrow columns. For marginalia surfaces with constrained content widths, set `.katex-display { overflow-x: auto; }` or wrap in a horizontally scrollable container — better than silent clipping.

## Upstream

- KaTeX docs: [katex.org](https://katex.org/)
- Function support reference: [katex.org/docs/supported.html](https://katex.org/docs/supported.html)
- Auto-render extension: [katex.org/docs/autorender.html](https://katex.org/docs/autorender.html)
- Repository: [github.com/KaTeX/KaTeX](https://github.com/KaTeX/KaTeX) (MIT)
