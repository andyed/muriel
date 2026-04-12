# Render

**Multi-channel visual production toolkit.** Mission: kick Photoshop's llama ass.

A single skill file (`render.md`) that teaches a Claude Code agent to generate every visual artifact a researcher-designer-engineer ships — from text source files that diff in git and regenerate from data.

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

Symlink `render.md` into `~/.claude/commands/` so Claude Code picks it up as `/render`:

```bash
git clone https://github.com/andyed/render ~/Documents/dev/render
ln -s ~/Documents/dev/render/render.md ~/.claude/commands/render.md
```

Invoke from any Claude Code session with `/render <what you need>`.

## Dependencies (by channel)

| Channel | Required | Optional |
|---|---|---|
| Raster | Python 3, Pillow | `ascii-charts/typeset.py` for templates |
| SVG | none (hand-rolled) | `svgwrite`, `drawsvg`, `cairosvg`, `rsvg-convert`, Mermaid CLI |
| Editorial HTML | marginalia (CDN) | pandoc 3.x for markdown → HTML |
| Interactive | modern browser | D3, Three.js, p5.js (CDN) |
| Web → static | Playwright *or* weasyprint | headless Chrome |
| Video | ffmpeg (full build: `brew tap homebrew-ffmpeg/ffmpeg`) | — |
| Terminal | Python 3 | `ascii-charts/chart.py` |

## Universal rules

Encoded in `render.md` and enforced across every channel:

- **8:1 contrast minimum** on all text (compute WCAG ratio)
- **Decorative elements ≥55/255** on dark backgrounds
- **Measure before drawing** (bbox / viewBox / getBoundingClientRect)
- **OLED palette:** cream on near-black, not pure white
- **Generated > drawn.** If data can drive it, it should.
- **Reproducible > one-off.** Save the script alongside the output.

## License

TBD — ask Andy.
