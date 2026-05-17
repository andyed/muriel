# Terminal — ASCII / Unicode Data Viz

Unicode bar charts, sparklines, and tables for terminal/markdown/chat output. No images needed — the output diffs in git, pastes into README files, and renders in any monospace context.

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission, universal rules, and channel map.

**Renderer:** [`muriel/chart.py`](https://github.com/andyed/muriel/blob/main/muriel/chart.py) — Python, zero dependencies.

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

## Animated effects — when the terminal IS the artifact

Static primitives above cover the common case (numbers in prose, README badges, log summaries). When the terminal output *is* the artifact — installer ceremonies, demo openings, deploy banners, README captures shown as GIFs — animation is what carries the message, and the substrate is **[TerminalTextEffects](https://github.com/ChrisBuilds/terminaltexteffects) (TTE)** (MIT, Python, `pip install terminaltexteffects`). A library of ~100 named effects (matrix, decrypt, scattered, rain, sweep, vhsTape, …) that take a string and play it into the terminal as a single composed animation. ANSI-escape backend; no curses, no ncurses dependency.

```python
from terminaltexteffects.effects.effect_decrypt import Decrypt
effect = Decrypt("muriel v0.8.0 — the rigorous round-trip")
with effect.terminal_output() as out:
    for frame in effect:
        out.print(frame)
```

This is the natural cross-pollination point with [`vocabularies/kinetic-typography.md`](../vocabularies/kinetic-typography.md): the kinetic-typography rules apply (max contrast, strategic motion, no ambient noise, rehearsed emotional vocabulary) but now the runtime is a terminal cell grid instead of pretext / iblipper. Same rules, new substrate.

**Capture** as MP4 / GIF (for README hero or video channel hand-off) via [`asciinema`](https://github.com/asciinema/asciinema) record → `agg` render, or by piping into [`muriel.capture`](../../../../../muriel/capture.py)'s terminal-emulator shot when that ships.

**Anti-prescription specific to this substrate.** Don't animate text that the reader will need to re-read — animation in a static-replay context is decoration. Reserve TTE for moments where the *first* reveal carries the entire weight (install completion, deploy success, scene-opener captions). Once captured as a GIF for a README, the GIF replays on every page load; if it's still saying something on the third replay, you over-animated.

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

## Anti-patterns

- **Don't use ASCII when Unicode has better glyphs.** `━` not `-`, `│` not `|`, `▁▂▃▄▅▆▇█` for bars.
- **Don't show more than ~15 bars horizontally** without a visual break or a scroll region.
- **Don't use color in terminals whose truecolor support you haven't verified** — fall back to ANSI 8 or named tokens.
