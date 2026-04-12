# Terminal — ASCII / Unicode Data Viz

Unicode bar charts, sparklines, and tables for terminal/markdown/chat output. No images needed — the output diffs in git, pastes into README files, and renders in any monospace context.

Part of the [Render](../render.md) skill — see the top-level index for mission, universal rules, and channel map.

**Renderer:** `~/Documents/dev/ascii-charts/chart.py` — Python, zero dependencies.

## Available primitives

- `bar_chart()` — horizontal bars using block characters (`█▉▊▋▌▍▎▏`) for sub-cell resolution. Supports negative values, comparison bars, markers, custom fill characters.
- `sparkline()` — inline single-line trend via `▁▂▃▄▅▆▇█`. Drop into prose or table cells.
- `table()` — box-drawing-character tables with aligned columns, numeric formatting, optional separators.

## Design rules

- **Label every number.** Units and context required (the universal rule applies here too — a chart with unlabeled axes is worse than no chart).
- **Monospace is load-bearing.** Ensure the output context renders in a monospace font. Markdown code blocks work. Slack works. Most terminal viewers work. HTML `<pre>` works.
- **Width budgets matter.** Target 80 columns or less unless you know the host is wider. Sparklines fit in any column width.
- **Numeric formatting:** right-align, consistent decimals, thousand separators for readability.

## Shipped examples

- **ClickSense README** — bar charts for feature comparison
- **Cartographer README** — session activity sparklines and summary tables
- **Research logs** — polars DataFrames printed via `table()` in JSONL entries

## When to reach for terminal viz vs image

Use terminal viz when:
- The output goes into a README, commit message, or log
- The reader needs to copy-paste numbers
- Width is constrained (<120 columns)
- You want zero dependencies and instant iteration

Use image viz (raster / SVG) when:
- Aesthetic typography matters
- The data has >2 dimensions (color, shape, size encoding)
- The output is a paper figure or store asset
- Interactivity or animation matters
