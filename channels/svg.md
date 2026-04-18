# SVG — Vector Channel

Photoshop can't generate vectors from data. SVG can — and the output diffs in git, scales infinitely, embeds in HTML and LaTeX, and inherits CSS theming from marginalia (`--mg-*` carries through to `<svg>` children).

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission, universal rules, and channel map.

## When to use
- Paper figures (round-trip with LaTeX)
- Diagrams generated from data (gaze ribbons, F-pattern overlays, OSEC phase bands)
- Icons and wordmarks that need exact scaling
- Anything embedded in a marginalia HTML page that should re-theme on light/dark switch
- Statistical plots when matplotlib's SVG export is ugly

## Tooling
- **Hand-rolled `<svg>` strings** — zero deps. Fine under 200 lines.
- **`svgwrite`** or **`drawsvg`** (Python) — fluent API for procedural generation.
- **`mermaid-cli`** (`mmdc`) — flowcharts from text → SVG.
- **Excalidraw export** — manual diagrams. Always `roughness: 0`, `fontFamily: 2` (Helvetica), `fillStyle: "solid"` (per past feedback — the hand-drawn aesthetic reads as fake). For Claude-driven editing of Excalidraw diagrams (create/move/align/distribute shapes in a live canvas), pair with [yctimlin/mcp_excalidraw](https://github.com/yctimlin/mcp_excalidraw) (MIT MCP server, 26 tools over a localhost canvas). muriel generates the `.excalidraw` file deterministically; mcp_excalidraw is the refinement loop.
- **`cairosvg`** or **`rsvg-convert`** (homebrew) — SVG → PNG/PDF when stores reject vectors. Use full TTF font paths, same rule as Pillow.

## Patterns
- **Use `viewBox`, not fixed `width`/`height`.** Scales without re-export.
- **CSS custom properties for theming** — share the `--mg-*` prefix with marginalia so SVGs inherit the host page palette:
  ```svg
  <svg viewBox="0 0 400 200" role="img">
    <title>Phase decomposition</title>
    <desc>Survey phase (0-2s) followed by evaluate phase (2-8s).</desc>
    <style>
      .axis { stroke: var(--mg-fg, #e6e4d2); stroke-width: 2; }
      .data { fill: var(--mg-accent, #ff7); }
    </style>
    <line class="axis" x1="20" y1="180" x2="380" y2="180"/>
    <rect class="data" x="20" y="100" width="80" height="80"/>
  </svg>
  ```
- **`<title>` and `<desc>`** are accessibility-required for paper figures.
- **`<text>` elements respect 8:1 contrast** — same WCAG check applies.
- **Embed fonts via `<defs>` + `@font-face`** if the SVG must render outside its host page.

## Recipes
- **Gaze ribbons** — line through fixation points, stroke-width = duration in ms / 10
- **F-pattern overlay** — colored bands over a SERP screenshot showing survey + evaluate phases (per the F-pattern decomposition work)
- **OSEC phase diagram** — multi-band horizontal timeline from a gaze sequence
- **Wordmark generation** — a branded wordmark border at any size from one source (but defer to acme-brand-guide for actual asset generation)

## Conversion
- **SVG → PNG:** `cairosvg input.svg -o out.png -W 1280 -H 720` or `rsvg-convert -w 1280 input.svg > out.png`
- **SVG → PDF:** `cairosvg input.svg -o out.pdf` (for paper inclusion)
- **HTML → SVG snapshot:** Playwright `page.locator('svg').screenshot()` for live-rendered figures — see [channels/web.md](web.md) for the static capture pipeline.

## Anti-patterns

- **Don't hardcode `fill="#hex"` on text.** Use CSS classes + `<style>` so a theme switch re-paints the whole diagram.
- **Don't ship SMIL animations without a CSS fallback.** Browser support has diverged since Firefox 2015.
- **Don't rely on `<tspan>` alone for multi-line text.** Measure bbox, fall back to multiple `<text>` elements if layout matters.
- **Don't nest `<g>` beyond two levels without a reason you can state in one sentence.**
