# ECharts — option-tree charting substrate

> **Candor up front:** Anthropic's training data has deep coverage of D3 and matplotlib and good coverage of Plotly/Chart.js, but ECharts is *under-represented*. When generating ECharts code, we get it ~right structurally but routinely hallucinate field names, miss the `markArea` two-element pair shape, mis-nest `axisLine.lineStyle.color`, or invent option keys that don't exist. **Verify against the upstream docs every time:** [echarts.apache.org/en/option.html](https://echarts.apache.org/en/option.html). Don't ship ECharts code untested.

**When to reach for it.** ECharts shines when you need a declarative time-series / scatter / radar chart on a dark-theme dashboard, with multiple overlaid series, brushable selection, and built-in tooltip + legend + zoom out of the box. It's the lightest substrate when:

- The piece is interactive (live data, hover, brush, drilldown) — D3 lets you do everything but you re-implement the chrome each time
- The chart already has more than one series and a tooltip on every datapoint would be useful — Chart.js handles single-series-with-tooltip well but multi-series tooltips are clumsy
- The chart is part of a larger UI (dashboard, report, studio surface) that already loads a JS framework — ECharts ships as a single `~1MB` minified file
- You want time-segmented overlays (`markArea`) and live cursor sync (`markLine`) without writing your own SVG primitives — D3 makes you build them; ECharts has them as first-class

**Don't reach for it when:**

- The output is a static SVG paper figure → use matplotlib via [`channels/science.md`](../channels/science.md), or D3+SVG via [`channels/svg.md`](../channels/svg.md). ECharts' SVG renderer exists but the DX is canvas-first.
- The chart is a one-off table-replacement (e.g. a single sparkline) → [`channels/terminal.md`](../channels/terminal.md) or plain SVG.
- The piece needs strict Tufte / 8:1 chrome enforcement → start from [`channels/charts.md`](../channels/charts.md), which has the per-library anti-pattern table. ECharts defaults violate most of that table; the configs below override them.
- You're going to ship the chart as a sharable PNG → render via headless screenshot or use matplotlib directly. ECharts is interactive-first.

## Version and licensing

- Pin to **`echarts@^5.4`** (current stable line). CDN: `https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js` — gzipped ≈ 350 KB.
- Apache-2.0 license — safe to vendor.
- For offline use (studio surfaces, file:// pages), download the dist file and reference it locally. Don't rely on the CDN when the artifact has to survive a network outage.

## Dark-mode baseline (the studio pattern)

ECharts' defaults are tuned for light pages: white background, dark `#666` axis text, white tooltip with subtle border, light gray gridlines. On a dark surface they read as blown-out chrome. The fix is to override five blocks in `setOption`:

```js
chart.setOption({
  // 1. Inherit page background — don't paint a white box behind the chart.
  backgroundColor: 'transparent',

  // 2. Set base text color so legend, axis labels, tooltip inherit it.
  //    Use the brand's primary foreground; ECharts cascades textStyle through children.
  textStyle: {
    color: '#e8e4f0',
    fontFamily: 'system-ui, sans-serif',
  },

  // 3. Axes — line color must be visible on dark, splitLine should be subtle.
  //    (Repeat for yAxis.)
  xAxis: {
    axisLine: { lineStyle: { color: '#5a5470' } },   // visible but quiet
    splitLine: { lineStyle: { color: '#2a2638' } },  // even quieter — guides the eye, doesn't compete
  },

  // 4. Tooltip — the white default is the worst offender on dark themes.
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(20, 18, 26, 0.95)',
    borderColor: '#3a3450',
    textStyle: { color: '#e8e4f0' },
  },

  // 5. Legend — explicit text color (ECharts ignores parent textStyle here in some versions).
  legend: { textStyle: { color: '#b8b3c8' } },

  series: [/* … */],
});
```

This is enough for any single-chart dashboard panel. For multi-chart pages, wrap the above in a theme object and `echarts.registerTheme('studio-dark', theme)`; then `echarts.init(el, 'studio-dark')`. But registering a custom theme is more ceremony than most studio pieces need — inline overrides are fine for ≤3 chart instances.

## Time-segmented overlays (`markArea`)

The most powerful ECharts feature for asserted-arc-style timelines: rectangular bands behind a time series, each spanning a labeled time range. Used in psychodeli-audio-lab/studio to overlay state-target phases (relaxed / focused / open-monitoring / hypnagogic) on a 48-second analyzer-feature timeline.

**The shape (commonly mis-written):** `markArea.data` is a list of **pairs**. Each pair is `[startObj, endObj]`, where the first object specifies the leading edge + visual style and the second specifies the trailing edge. Both objects use `xAxis` (or `yAxis`) for the coordinate.

```js
series: [{
  type: 'line',
  data: tSec.map((t, i) => [t, values[i]]),
  markArea: {
    silent: true,                          // don't intercept hover on data points
    label: { position: 'top' },            // label sits above the chart, not inside the band
    data: [
      [
        { name: 'drone_solo', xAxis: 0,
          itemStyle: { color: 'rgba(155,110,200,0.18)',
                       borderColor: '#9b6ec8', borderWidth: 1 } },
        { xAxis: 10 }
      ],
      [
        { name: 'chant_call', xAxis: 10,
          itemStyle: { color: 'rgba(155,110,200,0.18)' } },
        { xAxis: 20 }
      ],
    ]
  }
}]
```

Three traps I hit:

- **The hallucinated single-object form.** Plenty of generated code writes `data: [{ name, xAxis: [t0, t1], itemStyle }]`. Wrong shape — ECharts silently renders nothing. Always the **pair**.
- **Missing `silent: true`.** Without it, the band's invisible bounding box intercepts mouse events meant for the data series — tooltips stop firing on hover over the band region.
- **Label position default is `'inside'`** which paints the segment name *over* your data. `position: 'top'` floats it above the chart frame and usually reads cleaner.

## The series color contract — the bug I burned a round-trip on

**Setting `lineStyle.color` is not enough.** ECharts treats `color` at the series root as the "series base color" — it drives the legend marker, the tooltip dot, and the default symbol fill. `lineStyle.color` only paints the line itself. If you set only `lineStyle.color`, the line draws in your color but the legend marker (and tooltip dot) keeps using ECharts' default 9-color palette:

```
default_palette: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']
```

Caught the live in psychodeli-audio-lab/studio: I'd set five `lineStyle.color: BRAND.X` overrides and the lines drew correctly, but the legend showed `#5470c6 #91cc75 #fac858 #ee6666 #73c0de` — every legend marker pulled the default palette in index order. Looked correct in isolation, was 100% lying about which line was which.

**The reliable pattern: set BOTH top-level `color: []` AND series-root `color`** for every series with brand colors:

```js
chart.setOption({
  // Series-cycle palette — drives any series without an explicit `color`.
  color: [BRAND.accent, BRAND.stateRelaxed, BRAND.stateFocused, BRAND.stateHypnagogic, BRAND.fail],

  series: [
    {
      name: 'centroid (Hz)',
      type: 'line',
      color: BRAND.accent,                        // legend marker + tooltip dot
      lineStyle: { width: 1.8, color: BRAND.accent },  // line stroke
      data: /* … */,
    },
    // … same shape per series
  ],
});
```

Why both? The top-level `color: []` array is the categorical palette ECharts cycles through. Per-series `color` is an explicit override. Setting both makes the contract explicit (no positional dependency on series order) and survives series-list reordering during refactor.

Other `color`-family fields that have their own narrow purpose:

- `itemStyle.color` — fill color for symbols, bars, pie slices. For line charts with `showSymbol: false`, irrelevant.
- `areaStyle.color` — for stacked area charts; fill below the line.
- `emphasis.itemStyle.color` — hover state. Defaults to the series base color brightened ~30%; explicit override only if the default doesn't read on your background.

If you see the legend in default-palette colors while the lines render correctly, that's this bug. Fix: set `color` at series root.

## Playhead sync gotchas

Pattern from studio: bind a `markLine` to the audio element's `currentTime`. **Don't drive it from `timeupdate` alone — programmatic `audio.currentTime = X` while paused does NOT fire `timeupdate`.** That event is playback-locked (fires ~4Hz only while the audio is playing). For seek-to-segment UX or any non-playback playhead movement, subscribe to `seeked` AND `loadedmetadata` as well:

```js
const player = document.getElementById('player');
const drawPlayhead = () => {
  chart.setOption({
    series: [{
      markLine: {
        symbol: 'none', silent: true, animation: false,
        lineStyle: { color: BRAND.fg, width: 1.5, opacity: 0.85 },
        label: { show: false },
        data: [{ xAxis: player.currentTime }],
      }
    }]
  });
};
player.addEventListener('timeupdate',     drawPlayhead);  // playback tick
player.addEventListener('seeked',         drawPlayhead);  // programmatic + scrubbed seek
player.addEventListener('loadedmetadata', drawPlayhead);  // initial position after load
```

Caught live: a segment-card click handler did `player.currentTime = t0` without calling `play()`, expecting the playhead to follow. It didn't, because timeupdate is playback-locked. The user wanted seek-without-play (preview the segment context, then optionally hit space to play) — adding `seeked` to the event list fixes the UX without forcing playback.

**`preload="metadata"` is unreliable for showing duration at page load.** Chromium defers metadata fetch — even after `audio.load()` + 8 second wait, `readyState` may still be 0 (HAVE_NOTHING) and `duration` is NaN. If the player chrome MUST show duration immediately, use `preload="auto"`. Cost: full audio fetch on page load. For studio surfaces serving local-net WAVs this is invisible; for public web pages with multi-megabyte audio it's not.

(Note: Chrome extension contexts sometimes block media auto-fetch even with `preload="auto"` — verify against a regular browser tab before declaring it broken in production.)

## ECharts diffs the option tree (don't fight it)

Pattern from studio: bind a `markLine` to the audio element's `currentTime`, update on `timeupdate` event. ECharts diffs the option tree, so we only pay for the line move, not a full redraw.

```js
const player = document.getElementById('player');
player.addEventListener('timeupdate', () => {
  chart.setOption({
    series: [{
      markLine: {
        symbol: 'none',
        silent: true,
        lineStyle: { color: '#fff', width: 1, opacity: 0.8 },
        data: [{ xAxis: player.currentTime }]
      }
    }]
  });
});
```

- `timeupdate` fires ~4Hz on Chromium, ~250ms throttle. Not animation-smooth, but the eye reads it as "playing." For animation-smooth, use `requestAnimationFrame` and read `player.currentTime` each tick.
- **Don't use `notMerge: true`** here — you want ECharts to diff the partial option, not blow away the series config and re-render from scratch every frame.
- For seek-by-click on segment labels, the reverse direction works the same: `player.currentTime = segment.t[0]` and the next `timeupdate` triggers the playhead move. No need to manually drive both.

## Multi-axis discipline (don't lie with scaling)

The scaling temptation: you have spectralCentroid (0–12000 Hz), energy bands (0–2), and onsetStrength (0–1) on the same chart, so you multiply the small ones (×200, ×1000) to make them visible against the centroid scale. **Don't.** The legend then reports "onsetStrength × 1000" and the viewer has to do mental math.

Use **multiple yAxis** with `yAxisIndex` per series:

```js
yAxis: [
  { type: 'value', name: 'Hz', position: 'left' },
  { type: 'value', name: 'energy', position: 'right' },
],
series: [
  { name: 'centroid (Hz)', yAxisIndex: 0, type: 'line', data: /* … */ },
  { name: 'energy',        yAxisIndex: 1, type: 'line', data: /* … */ },
],
```

Two y-axes for two unit families is honest. Four series sharing one axis with three of them rescaled is not.

(This is the *one* legitimate use of dual y-axes — different unit dimensions. The Tufte/charts.md anti-pattern about dual y-axes is specifically about *same unit, different scale* dual axes that fake correlation. Different units, properly labeled, is fine.)

## Data-shape contract

ECharts time-series wants `[[x, y], [x, y], …]` arrays. Not `{x, y}` objects. Build the array explicitly; avoid `dataset` + `encode` for simple cases — they add indirection without much benefit until you're sharing one dataset across multiple series.

```js
// ✓ Correct
data: tSec.map((t, i) => [t, values[i]])

// ✗ Hallucinated — ECharts won't parse this for line type without dataset config
data: tSec.map((t, i) => ({ x: t, y: values[i] }))
```

## Renderer: canvas vs SVG

Default canvas. Faster for >500 points, no DOM bloat, transparent backgrounds work. Switch to SVG (`echarts.init(el, theme, { renderer: 'svg' })`) only when:

- You need DOM-level a11y on individual marks (screen reader landmarks)
- You're exporting the chart as a static SVG asset (rare — usually better to export PNG from canvas)
- The chart is part of a larger SVG composition you want to inspect with devtools

For audio-reactive / playhead-driven charts, canvas is the right choice — SVG redraws cost more on every `setOption`.

## Worked exemplar

`psychodeli-audio-lab/studio/meditate-001.html` (generated by `tools/studio-build.py`). The single-page studio surface:

- Dark-theme baseline (overrides above)
- 5 series on shared y-axis (acceptable here only because energy bands and onset are dimensionless ratios on the same 0–1 logical scale; centroid is plotted in Hz on the same axis as a deliberate visual-density tradeoff — see the "Multi-axis discipline" caveat above; this file currently violates that rule and is a candidate for refactor to dual yAxis)
- `markArea` segments per asserted-arc phase, colored by state-target taxonomy
- `markLine` playhead synced to the `<audio>` element
- Click-on-segment → seek the audio → ECharts updates on next `timeupdate`

When in doubt, copy that file's `setOption` block as a starting point rather than generating from memory.

## What I don't trust myself to write without checking the docs

When generating ECharts options from a prompt, my failure modes (the ECharts-specific ones, beyond the dark-theme defaults above):

- **The series color contract** — confirmed live, see section above. `lineStyle.color` ≠ legend marker color. Always also set series-root `color` (and/or top-level `color: []` palette).
- **`markArea.data` shape** — pairs of `[startObj, endObj]`, not single objects with `xAxis: [t0, t1]`. Confirmed live; muriel example uses the pair shape.
- **`timeupdate` vs `seeked`** — confirmed live; `timeupdate` is playback-locked, `seeked` is the companion event for programmatic seeks.
- **`visualMap`** — the piecewise/continuous distinction, the `inRange.color` array length matching the data range. I usually get the structure right but the field names drift.
- **`dataZoom`** — `inside` vs `slider` types, the `start` and `end` percentage semantics, `xAxisIndex` linkage.
- **`graphic`** — custom overlay shapes (text, rect, line annotations not tied to a series). I tend to mis-nest `elements[].style` vs `elements[].shape`.
- **`brush`** — the cross-series selection mode. Most generated code under-specifies `toolbox.feature.brush` and the brush UI never appears.
- **`series.large` performance flag** for >5k points — the threshold and the trade-off (loses some interactive precision) is easy to mis-state.
- **`animation` defaults** vary by chart type and ECharts version; disable explicitly for headless rendering (`animation: false`) rather than trusting a global config.

When you hit any of these, open [the option reference](https://echarts.apache.org/en/option.html), `Cmd-F` the field name, and verify against the v5 schema. Don't ship from memory.

## Heatmap + visualMap (the "3D projected grid" pattern)

When you have a third data dimension that doesn't fit on a 2D line chart, the cheapest projection is a **heatmap with visualMap**: two categorical axes (e.g. time × band) and color encoding the third dimension's magnitude. It's the 2D shadow of a 3D landscape — the canonical spectrogram move — and ECharts ships it natively without `echarts-gl`.

Worked exemplar from psychodeli-audio-lab/studio: a (time × frequency-band × energy) heatmap rendered below the 1D timeline, sharing the time axis so the eye can correlate "where the centroid line spikes" with "which band is hot at that moment."

```js
chart.setOption({
  // … brand theme tokens …

  xAxis: {
    type: 'category',                  // category, not value — heatmap cells align to indices
    data: timeLabels,                  // ['0.0', '0.2', '0.4', …]
    name: 'sec', nameLocation: 'middle',
    // Heuristic: 10–12 visible labels max. interval is a SKIP count
    // (n-1), not a "1 in n" ratio. interval: 24 → labels at index 0, 25, 50…
    axisLabel: { interval: Math.floor(timeLabels.length / 10) },
  },

  yAxis: {
    type: 'category',
    data: ['low', 'mid', 'high'],      // first item renders at BOTTOM of axis
                                        // (ECharts inverts y-category by convention —
                                        //  matches spectrogram intuition: low @ floor)
  },

  visualMap: {
    min: 0, max: bandMax,
    orient: 'vertical', right: 16, top: 'center',   // vertical on the right
                                                     // reads cleaner than horizontal bottom
                                                     // for a wide heatmap
    itemWidth: 14, itemHeight: 140,
    calculable: true,                  // adds drag handles for range filter
    inRange:    { color: [BG, COOL, MID, WARM, HOT] },   // 4–5 color stops, low→high
    outOfRange: { color: [BG] },       // pair with calculable so dragging dims outside

    // GOTCHA: text is [upperLabel, lowerLabel] — FIRST string labels MAX value.
    // Mnemonic: reads top-down on a vertical visualMap.
    text: ['3.8', '0'],
  },

  series: [{
    type: 'heatmap',
    // Each cell is a [xIdx, yIdx, value] TRIPLE — not a structured object.
    // xIdx/yIdx are integer indices into the category arrays.
    data: [[0, 0, 1.2], [0, 1, 0.4], [0, 2, 0.1], [1, 0, 1.5], …],
    progressive: 1000,                 // chunked render for >1000 cells
    emphasis: {                        // hover state
      itemStyle: { borderColor: BRAND.fg, borderWidth: 1 },
    },
  }],
});
```

**The non-obvious bits:**

- **`visualMap.text` is `[upperLabel, lowerLabel]`** — first element labels the TOP of the vertical slider (the max value), second labels the BOTTOM (min). Mnemonic: it reads top-down. Counterintuitive enough that everyone gets it wrong the first time. Bare `text: ['max', 'min']` is the default-ish form; for numeric labels you typically want the actual numbers as strings.

- **`visualMap.inRange.color` is a list of color stops** ECharts interpolates between — order goes low → high. 4–5 stops covers most thermal maps without banding. For a brand-themed thermal: `[bg, cool-accent, brand-primary, warm-amber, hot-salmon]`.

- **`visualMap.calculable: true`** adds drag handles. Pair with `outOfRange.color: [bg]` so dragging the handles visually filters the heatmap to the active range — incredibly useful for "show me only cells above 2.0" exploration.

- **`xAxis.axisLabel.interval` is a SKIP count, not a ratio.** `interval: 24` produces labels at indices `0, 25, 50, …` — show one, skip 24. Easy to misread as "1 in 24" (it's 1 in 25). Common heuristic: `Math.floor(arr.length / 10)` gives roughly 10 visible labels.

- **Category y-axis renders first-item-at-bottom by default** (ECharts inverts y-categories). So `data: ['low', 'mid', 'high']` puts `low` at the floor — perfect spectrogram convention. If you want top-down rendering (taxonomic lists, ranking), set `yAxis.inverse: true`.

- **Heatmap data is `[xIdx, yIdx, value]` triples**, not objects. The tuple positions are coordinates → color-mapped value. Tooltip formatter receives `p.data` as the same triple — index into it: `formatter: p => \`${p.data[2].toFixed(2)}\``.

- **For sparse data** (cells you don't want rendered), just omit them from the data array. ECharts doesn't render a cell for an absent (x, y) coordinate. No need for null fills.

- **`progressive: N`** chunks the render — useful when you have >1000 cells. For a 249 × 3 = 747 cell grid it's overkill but harmless. Above ~10k cells, drop the chunk size to 500 to avoid first-paint stutter.

- **For TRUE 3D** (perspective, rotatable, depth) — that's `echarts-gl`, a separate package (`echarts-gl@^2.0`, ~600 KB minified). Series types: `bar3D`, `scatter3D`, `surface`, `line3D`. Reach for it when the magnitude axis needs to be VIEWED in 3D (rotation, parallax) rather than projected to color. For dashboard / report surfaces, the 2D heatmap projection is almost always the right call — color is read faster than depth, and you don't need to manage a camera.

## Live-verification protocol

When wiring up an ECharts surface, before declaring it done:

1. **Open in a real Chrome tab.** Not just a screenshot, not just devtools — a live tab where you can probe the chart instance.
2. **Probe the resolved option tree** via `echarts.getInstanceByDom(el).getOption()`. ECharts merges your input with defaults — what you see in `getOption()` is what's actually painting. Check:
   - `opt.color` — is the palette you intended? (If you didn't set it, it's the default 9 colors — caught the legend-marker bug this way.)
   - `opt.series[i].color` vs `opt.series[i].lineStyle.color` — series-root color drives legend.
   - `opt.yAxis[i].min/max` — did your `min: 0, max: N` survive merge, or did auto-scaling override?
   - `opt.series[i].markArea.data` — is the two-pair shape preserved after merge?
3. **Trigger the interactions you wired** (audio seek, hover, legend click) and re-probe. State changes that should affect the option tree are easy to assert; state changes that don't are easy to miss.
4. **Test programmatic state changes**, not just user-driven ones. `player.currentTime = X` from a JS console probes whether your `seeked` handler is wired (the `timeupdate`-only bug doesn't show under "play and watch").

This caught two real bugs in 15 minutes on the studio page that wouldn't have shown in static screenshots: the legend color mismatch and the timeupdate-only playhead.

## See also

- [`channels/charts.md`](../channels/charts.md) — the strict-mode Tufte enforcement layer with per-library anti-pattern tables. ECharts defaults violate ~half of that table; the cheat row there is the minimum override set, the section above is the dark-theme dashboard set.
- [`channels/interactive.md`](../channels/interactive.md) — single-file interactive demo scaffolds. ECharts loaded from CDN is a common substrate for marginalia demos with one chart.
- [`vocabularies/pixijs.md`](pixijs.md) — when you need per-pixel control or particle counts beyond ECharts' batching (10k+ marks).
