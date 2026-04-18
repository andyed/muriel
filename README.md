<p align="center">
  <picture>
    <source srcset="assets/logo-animated-dark.gif" media="(prefers-color-scheme: dark)">
    <img src="assets/logo-animated.gif" alt="muriel — a multi-constraint solver" width="720">
  </picture>
</p>

# muriel

**A multi-constraint solver for visual production.** Mission: kick Photoshop's llama ass.

A single skill file (`muriel.md`) that teaches a Claude Code agent to generate every visual artifact a researcher-designer-engineer ships — from text source files that diff in git and regenerate from data. The rules (8:1 contrast, OLED palette, one font treatment, generated > drawn, reproducible > one-off) stay *live* at render time: brand tokens are parsed, contrast is audited, dimensions are enforced — not as lint after the fact, but as part of the act of making.

### Built on / integrates with

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776ab?logo=python&logoColor=white)
![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d97757)
![PyPI: muriel](https://img.shields.io/badge/PyPI-muriel-3775a9?logo=pypi&logoColor=white)

**Python channels**
![Pillow](https://img.shields.io/badge/Pillow-raster-informational)
![matplotlib](https://img.shields.io/badge/matplotlib-figures-11557c?logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-capture-45ba4b?logo=playwright&logoColor=white)
![svgwrite / cairosvg](https://img.shields.io/badge/svgwrite_%2F_cairosvg-SVG-orange)

**Editorial**
![marginalia](https://img.shields.io/badge/marginalia-editorial-e6e4d2?labelColor=0a0a0f)
![pandoc](https://img.shields.io/badge/pandoc-markdown-373737?logo=markdown&logoColor=white)
![WeasyPrint](https://img.shields.io/badge/WeasyPrint-HTML%E2%86%92PDF-000)

**Interactive / graphics**
![WebGL](https://img.shields.io/badge/WebGL-rendering-9b35d3)
![D3.js](https://img.shields.io/badge/D3.js-linked_displays-f68e56?logo=d3dotjs&logoColor=white)
![PixiJS v8](https://img.shields.io/badge/PixiJS-v8-e72264?logo=pixijs&logoColor=white)
![pretext](https://img.shields.io/badge/pretext-typography-666)

**Diagrams / video**
![Mermaid](https://img.shields.io/badge/Mermaid-diagrams-ff3670?logo=mermaid&logoColor=white)
![Excalidraw](https://img.shields.io/badge/Excalidraw-sketch_exports-6965db)
![FFmpeg](https://img.shields.io/badge/FFmpeg-video-007808?logo=ffmpeg&logoColor=white)

## Channels

- **Raster** (Pillow + `typeset.py`) — store assets, icons, banners, wordmarks
- **Vector** (SVG, `svgwrite`, `cairosvg`) — paper figures, data-driven diagrams, scalable icons
- **Editorial HTML** (marginalia) — blog posts, callouts, magazine layouts
- **Interactive** (WebGL / Canvas / D3) — live demos with parameter sliders
- **Web → static** (Playwright, weasyprint) — capture DOM to PNG/PDF
- **Video** (ffmpeg + `desktop-control`) — product demos, GIFs, talk recordings
- **Terminal** (Unicode charts) — sparklines, bar charts, tables
- **Density viz** (`typeset.render_heatmap()`) — Tobii-style fixation heatmaps
- **Gaze plots** — scanpath, bubble scanpath, AOI timeline, saccade rose

Photoshop does one of these (raster), badly for the others, and zero of them reproducibly.

## Install

Symlink `muriel.md` into `~/.claude/commands/` so Claude Code picks it up as `/muriel`:

```bash
git clone https://github.com/andyed/muriel ~/Documents/dev/muriel
ln -s ~/Documents/dev/muriel/muriel.md ~/.claude/commands/muriel.md
```

Invoke from any Claude Code session with `/muriel <what you need>`.

## Dependencies (by channel)

| Channel | Required | Optional |
|---|---|---|
| Raster | Python 3, Pillow | [`muriel/typeset.py`](muriel/typeset.py) for templates |
| SVG | none (hand-rolled) | `svgwrite`, `drawsvg`, `cairosvg`, `rsvg-convert`, Mermaid CLI |
| Editorial HTML | marginalia (CDN) | pandoc 3.x for markdown → HTML |
| Interactive | modern browser | D3, Three.js, p5.js (CDN) |
| Web → static | Playwright *or* weasyprint | headless Chrome |
| Video | ffmpeg (full build: `brew tap homebrew-ffmpeg/ffmpeg`) | — |
| Terminal | Python 3 | [`muriel/chart.py`](muriel/chart.py) |

## Universal rules

Encoded in `muriel.md` and enforced across every channel:

- **8:1 contrast minimum** on all text (compute WCAG ratio)
- **Decorative elements ≥55/255** on dark backgrounds
- **Measure before drawing** (bbox / viewBox / getBoundingClientRect)
- **OLED palette:** cream on near-black, not pure white
- **Generated > drawn.** If data can drive it, it should.
- **Reproducible > one-off.** Save the script alongside the output.

## License

MIT. See [LICENSE](LICENSE).
