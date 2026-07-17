---
channel: charts
status: active
requires:
  brand: optional
  audience: optional
  reads:
    - muriel.contrast
    - muriel.palettes
output:
  kinds: [svg, png, html]
  registers: [editorial, blog, app, social]
peer_channels:
  - science
  - web
  - interactive
  - infographics
---

# Charts — Data viz across web libraries

The JS/web charting channel: Recharts, ECharts, Chart.js, Plotly, D3/SVG. matplotlib lives in [`channels/science.md`](science.md) — read that for paper figures, stats reporting, and the OLED rcparams. This file is the agent-actionable counterpart for everything that renders in a browser.

Structurally ported from [Caylent's `tufte-data-viz`](https://github.com/caylent/tufte-data-viz) (MIT) — they did the cross-library rule-naming work. Muriel's universal rules (8:1 contrast, weight × size × opacity floors, OLED palette, brand tokens) override their color tokens. Read upstream for deeper per-library code; this file is the muriel-curated subset plus the strictness overrides.

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission, universal rules, and channel map.

## When to use

- A blog post, dashboard, or React app needs a chart and you're reaching for Recharts/ECharts/Chart.js/Plotly/D3
- Reviewing chart code (PR review, AI-generated chart cleanup)
- Replacing a `<Pie>` or dual-y-axis chart someone else wrote
- Sparklines or slopegraphs anywhere (web, app, marginalia page)

If the chart lands in a paper, lab notebook, or matplotlib pipeline — use [`channels/science.md`](science.md) instead.

## Workflow

1. **Identify the message.** Before writing chart code: what is the *finding* this chart must make visible? What is the *comparison context* — baseline, target, prior period, peer group? If no finding, no chart (see rule 22).
2. **Pick the right chart type** from the chart-type guide below.
3. **Apply the 22 universal rules.** They are defaults — deviate only on explicit user instruction.
4. **Apply library-specific config** from the quick-reference table.
5. **Run the validation checklist** before declaring done.
6. **Audit text colors with `muriel.contrast`** if the chart includes HTML/SVG text labels.

## Universal rules

Numbered for citation. Lifted from Tufte's classic principles + modern screen-first extensions; reworded for muriel's stricter floors.

### Layout & chrome

1. **No top or right borders.** Bottom + left axes are sufficient. Top/right lines are chartjunk.
2. **Direct labels, not legends.** Label each series at the endpoint, on the bar, or beside the cluster. Drop the `<Legend>` component. If there is only one series, the title carries the context.
3. **No gridlines by default.** For static charts where exact reads matter, horizontal-only at 0.08–0.12 opacity. For interactive charts, a contextual crosshair on hover replaces gridlines (rule 15). Never vertical gridlines.
4. **Range-frame axes.** Axis lines span only the data's range, not zero-to-arbitrary-max. Start at (or near) the min; end at the max. Exception: zero-baseline bar charts must include zero (rule 11 corollary).
5. **No 3D effects.** No perspective, no depth, no shadows on data elements. 2D data → 2D representation.
6. **No pie charts unless explicitly requested.** Default to a horizontal bar chart sorted by value. If pie is required: max 4 slices, 2D, start at 12 o'clock, direct percentage labels per slice.
7. **Aspect ratio ≈ 1.5:1.** Charts ~50% wider than tall. Standard sizes: 600×400, 750×500, 900×600. Exception: sparklines and small multiples may be more compact.
8. **No dual y-axes.** They imply correlations that may not exist. Use small multiples — two charts stacked, shared x-axis.

### Color & weight

9. **Background never pure white or pure black.** Light: `#fffff8` (muriel's web/editorial register) or `#e6e4d2` (OLED cream). Dark: `#151515` or `#0a0a0f` (OLED near-black).
10. **Gray-first, highlight selectively.** Default series is a muted dark gray; one accent color highlights the most important series or data point. Max 4 distinct colors. See *Color tokens* below — the muriel-strict palette differs from Tufte's published palette because Tufte's defaults fail 8:1.
11. **Bar baselines include zero.** Truncating a bar y-axis above zero exaggerates differences. Lines and scatters may use range-frame axes; bars may not.
12. **Annotate the notable.** If the data contains a peak, trough, inflection, or event boundary, add a text annotation pointing to it. Place in the nearest clear space with a short leader line if needed.
13. **Comparison context required.** Every chart must answer *"compared to what?"* — a baseline line, target band, prior period series, or peer group. A solitary line with no reference fails. (See also SKILL.md universal rule.)
14. **Minimal tooltips.** Plain text with value and label. No colored background, no border, no arrow pointer, no shadow.

### Screen extensions

15. **Progressive disclosure over static density.** Default to the clean overview; layer details through hover/tap/click. A contextual crosshair on hover replaces permanent gridlines.
16. **Accessible by default.** 8:1 minimum contrast on **all text** (muriel universal rule — Tufte settles for 4.5:1; we do not). Color is never the sole differentiator — pair with shape, dash pattern, or direct label. Every chart has a text alternative (`aria-label` summarizing the key finding, or a companion data table). Interactive charts are keyboard-navigable.
17. **Responsive, not just resized.** Use percentage width + `viewBox`, or adaptive breakpoint changes. At narrow viewports, change chart type or layout (horizontal bars, reduced tick density, abbreviated labels) — don't merely shrink.
18. **Animate to explain, not decorate.** Transitions for data changes (sort, filter, time-step) are good. Entrance bouncing, decorative motion, gratuitous "build-in" animations are chartjunk. Duration 200–500ms, ease-out. Always honor `prefers-reduced-motion`.
19. **Dark mode is a first-class palette, never an inversion.** Reduce saturation in dark mode (bright colors "vibrate" on dark backgrounds). Honor `prefers-color-scheme`. Use semantic tokens (`--chart-bg`, `--chart-text`, `--chart-series-default`) so swaps are automatic.

### Content & format

20. **Titles assert findings.** "Revenue Surged 23% in Q3" — not "Revenue by Quarter, 2024". The chart title states the insight. Subtitle adds context ("vs. prior year, USD millions"). If the data has no clear finding, the chart may not be needed (rule 22).
21. **Format numbers for humans.** Abbreviate large numbers (`$1.2M` not `$1,200,000`). Thousand separators for mid-range (`12,450`). Match decimal precision to significance. Right-align numbers in tables. State units once (axis label or title), not on every datum.
22. **Don't chart what a sentence can say.** 1–2 numbers → write a sentence with inline context ("Revenue was $4.2M, up 23% from Q2"). A simple ranking of 3–5 items → consider a table. Charts earn their space by revealing patterns, trends, or distributions that prose and tables cannot.

## Color tokens — muriel-strict overrides

Tufte's published palette uses `#666` series and `#e41a1c` accent. Both fail muriel's 8:1 floor on `#fffff8`. The muriel-strict palette below passes; verify with `python -m muriel.contrast <file.svg>` for any inline-styled output.

### Web/editorial register (Tufte light, muriel-strict)

| Token | Hex | Contrast vs `#fffff8` | Notes |
|---|---|---|---|
| Background | `#fffff8` | — | off-white, never pure |
| Text primary (titles, data labels) | `#1a1a1a` | 17.4:1 | ≥500 weight at body sizes |
| Text secondary (subtitles, annotations) | `#444` | 9.7:1 | passes 8:1 |
| Axis / rule | `#444` | 9.7:1 | match text-secondary |
| Default data series | `#444` | 9.7:1 | darker than Tufte's `#666` |
| Highlight / accent | `#8b0000` | 10.0:1 | deeper than Tufte's `#e41a1c` |
| Gridline (if used) | `#ddd` at 1.0 opacity | decorative | never `opacity:` on text |

### OLED register (muriel canonical)

| Token | Hex | Contrast vs `#0a0a0f` | Notes |
|---|---|---|---|
| Background | `#0a0a0f` | — | near-black, never pure |
| Text primary | `#e6e4d2` | 15.4:1 | cream, matches matplotlibrc_dark |
| Text secondary | `#bbb` | 9.5:1 | passes 8:1 |
| Axis / rule | `#bbb` | 9.5:1 | match text-secondary |
| Default data series | `#bbb` | 9.5:1 | darker than Tufte's `#999` |
| Highlight / accent | `#ffa07a` | 9.2:1 | salmon — passes 8:1 on near-black |
| Gridline (if used) | `#3a3a4a` | decorative | meets the ≥55/255 dark-bg floor |

### Categorical palettes (when categories must be distinguished by color)

Direct labels handle most cases (rule 2). When a true categorical encoding is unavoidable, use a colorblind-safe palette — never auto-generated rainbows. Muriel ships these as importable constants in `muriel.palettes` (`WONG`, `IBM`, `TOL_BRIGHT`, …). **Validate any palette you didn't get from that list** — a brand set, a hand-picked subset, or `generate_for_floor()` output — with `python -m muriel palettes --validate "#hex,#hex,…" --bg <surface>` (or `muriel cvd` for the separation report alone). This is the check `muriel.contrast` cannot make: contrast measures each color against the *background*, while `validate` measures the palette against *itself* under simulated protanopia/deuteranopia — two hues can each clear 8:1 on near-black and still be one color to a colorblind reader. Worst-pair ΔE ≥ 12 passes; 8–12 is legal only with a second encoding channel (direct label, dash, shape, texture); below 8 the slots collapse.

- **Wong 8** (Nature Methods 2011, optimized for protanopia/deuteranopia/tritanopia):
  `#000000 #E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7`
- **IBM 5** (IBM Design Language v2):
  `#648FFF #785EF0 #DC267F #FE6100 #FFB000`
- **Tol bright 7** (Paul Tol):
  `#4477AA #EE6677 #228833 #CCBB44 #66CCEE #AA3377 #BBBBBB`

Max 4 categories before pattern-pairing or small-multiplying. Always pair color with a second channel (shape, dash pattern, direct label).

### Sequential and diverging

- **Sequential** (ordered magnitude): use viridis, cividis, or any single-hue ramp. Never rainbow (perceptually non-uniform; colorblind-hostile).
- **Diverging** (deviation from a midpoint): two-hue blue↔red or teal↔orange, white-center. Use for effect sizes, profit/loss, change-from-baseline.

## Library quick reference

The 22 universal rules are sufficient for most charts. Per-library essentials below. For deep code examples, read the corresponding file in the upstream [`tufte-data-viz/rules/`](https://github.com/caylent/tufte-data-viz/tree/main/rules) — same rule names, same numbering.

| Library | Essential config (muriel-strict tokens applied) |
|---|---|
| **Recharts** | `<CartesianGrid stroke="none" />` · drop `<Legend />` · `<YAxis axisLine={false} tickLine={false} tick={{fill:'#444',fontSize:12}} />` · `<Line dot={false} strokeWidth={1.5} stroke="#444" />` · highlight series: `stroke="#8b0000"` · background: wrap in `<div style={{background:'#fffff8'}}>` |
| **ECharts** | `splitLine:{show:false}` · `legend:{show:false}` · `grid:{show:false}` · series: `endLabel:{show:true,formatter:'{a}'}` for direct labels · `backgroundColor:'#fffff8'` · axis text color: `#444`. **For dashboard / interactive / dark-theme work** (timeline overlays, playhead sync with HTML5 `<audio>`, `markArea` + `markLine` patterns, the training-data accuracy caveat) — see [`vocabularies/echarts.md`](../vocabularies/echarts.md). |
| **Chart.js** | `scales.x.grid.display:false` · `scales.x.border.display:false` (same for y) · `plugins.legend.display:false` · use `chartjs-plugin-datalabels` for direct labels · `backgroundColor:'rgba(68,68,68,0.8)'` (muriel `#444`) |
| **Plotly** | `showgrid=False` · `showlegend=False` · `plot_bgcolor='#fffff8'` · `paper_bgcolor='#fffff8'` · `zeroline=False` · `tickfont=dict(color='#444',size=12)` · use `fig.add_annotation(...)` for endpoint labels |
| **D3/SVG/HTML** | `.domain { display: none }` for axis lines (or set `stroke:#444; stroke-width:0.5`) · no `<rect>` backgrounds · gridlines at `stroke-opacity:0.1` if at all · use `<text>` for direct labels at `fill:#444` |
| **matplotlib** | see [`channels/science.md`](science.md) — already covered via `muriel.matplotlibrc_dark` / `_light` importable rcparams |

## Chart-type guidance

| Type | Key settings |
|---|---|
| **Line** | 1.5–2px stroke, no dots unless ≤7 points (then r=2), direct label at rightmost point, range-frame axes |
| **Bar** | Prefer horizontal for categorical labels (avoids rotated ticks). Sort by value descending. Direct value labels. Default fill `#444`. Zero baseline required (rule 11). |
| **Scatter** | Gray dots `#444` r=3. Highlight key cluster/outlier with `#8b0000`. Regression line if meaningful (dashed, thin). |
| **Time series** | Label events on chart ("Recession", "Launch"), range-frame x-axis. YoY: current solid, prior period 30% opacity. |
| **Small multiples** | Shared scale across ALL panels (most-common bug: per-panel auto-scale). X labels only on bottom row; y labels only on leftmost column. No panel borders. |
| **Sparklines** | ≈80×20px. No axes, labels, or gridlines. Min/max dots at r=1.5. Embed inline in text or table cells. |
| **Slopegraph** | Before/after categories. Label both endpoints (value + name). Gray default + highlight key slopes with `#8b0000`. |
| **Data table** | No zebra striping (moire). Whitespace + thin rules every 3–5 rows. Right-align numbers. `font-feature-settings: 'onum' 1` for old-style figures. |
| **Area** | Prefer lines. If area: fillOpacity 0.03–0.08, no gradient, direct labels at endpoints. |
| **Stacked bar** | Avoid — use small multiples. If forced: sort by total, direct labels per segment, max 4 segments. |
| **Heatmap** | See [`channels/heatmaps.md`](heatmaps.md) for density overlays. For categorical heatmaps: sequential or diverging palette only, value labels in cells, companion data table for accessibility. |

## Anti-patterns — detection and fix

When reviewing chart code, grep for these patterns. Each row is a PATTERN → FIX one-liner. Per-library detection blocks follow.

### Universal anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Pie chart | Humans poorly compare angles/areas. 28% vs 32% looks identical. | Horizontal bar, sorted by value. |
| 3D effects | Perspective distorts. Back bars appear smaller than equal front bars. | Flat 2D only. |
| Dual y-axes | Implies false correlation. Scale tricks make any two lines look correlated. | Two stacked charts, shared x. |
| Legend box | Eyes shuttle legend↔data. +40% cognitive load. | Direct labels at endpoints/on data. |
| Heavy gridlines | Cage that imprisons the data. Competes for attention. | Remove, or horizontal-only at 0.08–0.12 opacity. |
| Rainbow palette | No natural ordering. Inaccessible to 8% of males. | Gray + accent, or Wong/IBM/Tol palette. |
| Gauge / speedometer | Huge area for one number. No trend, no context. | Single large number + sparkline + comparison. |
| Zebra-striped table | Moire vibration. Stripes louder than data. | Whitespace + thin rules every 3–5 rows. |
| Gradient fills | No information. Distract from value reading. | Solid flat fill (muted gray or accent). |
| Rotated axis labels | 45°/90° text is hard to read. | Horizontal bar chart, or abbreviate ticks. |
| Truncated bar y-axis | A 2% change looks like 50% swing. | Include zero, or annotate the axis break explicitly. |
| Decorative borders | Box around chart is chartjunk. | Remove. Whitespace defines the chart boundary. |
| Markers on every point | 50+ circles = confetti, obscures trend. | `dot={false}` or markers only at min/max/endpoint. |
| Thick axis lines (2–3px) | 1+1=3 effect; phantom visual weight. | 0.5–1px, or remove if ticks orient. |
| Hover-only information | Touch and keyboard users get nothing. WCAG violation. | Tap/click/focus fallback. |
| Missing text alternative | Screen-readers announce nothing. | `aria-label` with key finding + data summary. |
| Color as sole differentiator | 8% of males have CVD. | Pair with shape, dash pattern, or direct label. |
| Gratuitous entrance animation | Delays comprehension. | Remove, or gate behind `prefers-reduced-motion`. |
| Fixed pixel width | Mobile overflow. | Percentage/`viewBox` width, or breakpoint-based layout. |
| Tufte `#666` series + `#e41a1c` accent | Fails muriel's 8:1 (5.7 / 4.7). | Use `#444` series + `#8b0000` accent (9.7 / 10.0). |
| `opacity:` on text labels | Composites effective contrast below the raw token. | Set color directly; never reach for opacity on text. |

### Per-library detection patterns

```
RECHARTS
  <Legend />                                 → remove; add direct labels
  <CartesianGrid />                          → <CartesianGrid stroke="none" />
  <Pie> / <PieChart>                         → <BarChart layout="vertical">
  fill="url(#gradient...)"                   → fill="#444"
  <YAxis yAxisId="right" />                  → two <LineChart> stacked
  stroke="#e41a1c" or other Tufte color      → stroke="#8b0000" (muriel-strict)
  <Area fillOpacity={0.3+} />                → <Line /> or fillOpacity={0.05}
  fill="#666" / stroke="#666"                → fill="#444" / stroke="#444"

ECHARTS
  type: 'pie'                                → type: 'bar', horizontal
  splitLine: { show: true }                  → splitLine: { show: false }
  legend: { show: true }                     → legend: { show: false } + endLabel
  series.areaStyle.opacity >= 0.3            → opacity: 0.05 or remove
  visualMap with rainbow                     → single-hue sequential
  textStyle.color: '#666'                    → '#444'

CHART.JS
  type: 'pie' / 'doughnut'                  → type: 'bar', indexAxis: 'y'
  grid.display: true                         → grid.display: false
  border.display: true                       → border.display: false
  plugins.legend.display: true               → display: false + datalabels plugin
  backgroundColor: 'rgba(R,G,B,0.5)'         → 'rgba(68,68,68,0.8)' (#444)

PLOTLY
  go.Pie(...)                                → go.Bar(orientation='h', ...)
  showlegend=True                            → showlegend=False + annotations
  showgrid=True                              → showgrid=False
  plot_bgcolor='white' / '#ffffff'           → plot_bgcolor='#fffff8'
  font.color='#666'                          → font.color='#444'

D3/SVG/HTML
  <rect class="background" fill="white" />   → remove or fill='#fffff8'
  .grid line { stroke-opacity: 0.5+; }       → 0.08–0.12, horizontal only
  rainbow scale (d3.interpolateRainbow)      → d3.interpolateViridis
  text { fill: #666; }                       → fill: #444
  text { opacity: 0.6; }                     → remove; set fill directly
```

## "Can I remove it?" test

For each non-data element, ask: *if I delete this, does the chart lose information?*

- Gridlines → usually no (data marks show position)
- Legend → no (if directly labeled)
- Axis title → sometimes no (if chart title already specifies the axis)
- Top/right borders → always no
- Background color other than off-white/near-black → always no
- Tick marks → maybe (keep if needed for read-precision, remove if axis line is sufficient)
- Tooltip border/background → always no

If "no," remove. If "maybe," try removing and verify the chart still communicates.

## Validation checklist

Before declaring a chart done:

- [ ] No top or right borders/spines
- [ ] No legend (or only when ≥3 series and direct labeling impossible)
- [ ] No vertical gridlines; horizontal gridlines only at ≤0.12 opacity if at all
- [ ] No pie chart (or explicit user request + max 4 slices)
- [ ] No dual y-axes
- [ ] No 3D, no gradient fills, no decorative borders
- [ ] Bar y-axis includes zero; line/scatter axes range-framed
- [ ] Title asserts the finding (rule 20)
- [ ] Comparison context present (baseline, target, prior period — rule 13)
- [ ] Each series directly labeled (rule 2)
- [ ] Notable points annotated (rule 12)
- [ ] All text passes 8:1 contrast — run `python -m muriel.contrast file.svg` for SVG output
- [ ] No `opacity:` on text labels
- [ ] Categorical palette passes CVD separation — run `python -m muriel palettes --validate "<hexes>" --bg <surface>` for any non-shipped palette (ΔE ≥ 12, or ≥ 8 with a second encoding channel)
- [ ] Categorical encoding paired with shape/dash/label, not color alone
- [ ] `aria-label` or companion data table present for screen-readers
- [ ] Responsive strategy chosen (not just shrunk)
- [ ] Animation gated behind `prefers-reduced-motion`
- [ ] Dark mode palette designed, not auto-inverted
- [ ] Numbers formatted for humans (abbreviated, thousand-separated, units stated once)
- [ ] The chart would lose information if you removed it (rule 22 — otherwise replace with a sentence)

## Prior art / upstream

- **[Caylent `tufte-data-viz`](https://github.com/caylent/tufte-data-viz)** (MIT). The structural model for this channel — 22 numbered rules, per-library cheat tables, anti-pattern PATTERN→FIX detection, can-I-remove test. Worth installing directly (`npx skills add caylent/tufte-data-viz`) when you want their full per-library rule files (each ~7–9KB). Muriel takes the structure and replaces the color tokens with our 8:1-passing palette; we keep their rule names so cross-references stay legible. Specific divergences:
  - Contrast bar: they target WCAG AA (3:1 element, 4.5:1 text); muriel mandates 8:1 text floor.
  - Default series: they use `#666` (5.7:1, fails); we use `#444` (9.7:1, passes).
  - Highlight: they use `#e41a1c` (4.7:1, fails); we use `#8b0000` (10.0:1, passes).
  - Dark-mode series: they use `#999` (6.4:1, fails); we use `#bbb` (9.5:1, passes).
  - Dark-mode highlight: they use `#fc8d62` (7.9:1, fails); we use `#ffa07a` (9.2:1, passes).
  - Weight × size × opacity floor: muriel adds the body-weight ≥500 / no-opacity-on-text rule on top of contrast (Tufte addresses contrast only).
- **[Tufte, *The Visual Display of Quantitative Information*](https://www.edwardtufte.com/book/the-visual-display-of-quantitative-information/)** (1983, 2nd ed. 2001). The book the upstream skill descends from. Coining sources for data-ink ratio, chartjunk, range-frame, small multiples, sparklines, slopegraph.
- **[Wong, *Points of view: Color blindness*](https://www.nature.com/articles/nmeth.1618)** (Nature Methods, 2011). Source for the Wong 8 palette.
- **[Paul Tol's notes on colour schemes](https://personal.sron.nl/~pault/)**. Source for Tol bright/light/muted palettes.
