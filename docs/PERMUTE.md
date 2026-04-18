# Permute — Divergent Data Visualization

Show the same data multiple ways. Pick the one that earns its ink.

## The journey

```
typographer → magazine layout → scientific communicator → infographic master
  (store       (marginalia,      (research-findings.json,  (permute,
   assets)      pull quotes,      citation verification,    linked displays,
                 editorial)        chart generation)         semantic zoom)
```

Each stage is useful on its own. The path meanders — we built store icons before bar charts, charts before infographics. That's fine. The connecting thread is: typography is the medium, data is the content, and the agent's job is to compose them into something a human can read at a glance.

## The idea

One dataset, N representations. The typographer shouldn't converge on a chart type before seeing alternatives. Permute generates a spread of visual encodings for the same values and lets you choose — or shows you something you didn't think to ask for.

This is Tufte's "small multiples" applied to the design process itself: instead of showing readers multiple views of the data, show the *designer* multiple views of the *chart* before committing.

## Why

The bar chart is the default because it's safe. But "safe" often means "least informative." Tufte's core argument: maximize the data-ink ratio — every mark should encode information. A horizontal bar chart of four values that are all within 10% of each other wastes 90% of its ink on sameness. A slope chart or dot plot would surface the differences.

The ClickSense deceleration data is a good example. We rendered it as a bar chart:

```
  ballistic  ████                            -0.0012
     normal  ████████████                    -0.0032
deliberative █████████████████               -0.0044
    extended ██████████████████████████████  -0.0076
```

That works. But is it the best encoding? Permute would also show:

**Slope/gradient** — emphasizes the monotonic progression:
```
  ballistic    ·
     normal        · · ·
  deliberative          · · · · ·
    extended                      · · · · · · · ·
  ──────────────────────────────────────────────────
  -0.001                                      -0.008
```

**Ratio annotation** — Tufte's "data behind the data":
```
  ballistic   -0.0012  ──┐
     normal   -0.0032    │ 2.7×
  deliberative-0.0044    │ 3.7×
    extended  -0.0076  ──┘ 6.3× from baseline
```

**Sparkline inline** — for embedding in prose:
```
  Deceleration across hold buckets: ▁▃▅█ (monotonic, 6.3× range)
```

Same data. Four encodings. Each reveals a different aspect: magnitude (bars), trend (slope), relative change (ratios), compactness (sparkline).

## Influences

**Tufte** — Data-ink ratio. Chartjunk elimination. Small multiples. The central question: "Compared to what?" Every chart answers a comparison question; permute forces you to name which one.

**Bertin** — *Semiology of Graphics*. The retinal variables: position, size, value, texture, color, orientation, shape. A bar chart uses position + size. A dot plot uses only position. Different variables foreground different patterns.

**Cleveland & McGill** — Perceptual accuracy hierarchy. Position along a common scale > length > angle > area > volume > color. Permute should rank its outputs by this hierarchy, not alphabetically.

**Wilkinson** — *Grammar of Graphics*. Data → aesthetics → geometry → statistics → coordinates → facets. Permute is a sweep across the geometry dimension while holding everything else constant.

**Few** — *Show Me the Numbers*. The "right chart" depends on the relationship: comparison, composition, distribution, or relationship. Permute categorizes the data's structure first, then generates chart types appropriate for that category.

**Gestalt principles** — Proximity, similarity, continuity, closure, common fate. These aren't about what chart to draw — they're about why the chart works once drawn. Bars in a group read as related (proximity). Identical fill patterns read as the same category (similarity). A monotonic slope reads as a trend (continuity). A sparkline `▁▃▅█` reads as one object, not four characters (closure). Permute uses these as evaluation criteria: does this encoding let Gestalt do the cognitive work, or does it fight the viewer's perceptual system?

**CRAP** (Williams) — Contrast, Repetition, Alignment, Proximity. The layout principles that make an infographic cohere rather than scatter. Contrast: the biggest number should look biggest — if all bars are similar length, the encoding is wrong. Repetition: small multiples work because the visual structure repeats, so only the data varies. Alignment: labels right-justified, bars left-justified, values right-justified — three alignment edges, not zero. Proximity: the legend sits next to the chart it explains, not in a separate box. These four rules govern the linked-display composer — every composed layout should pass a CRAP audit.

## How it works

```python
from chart import permute

# Input: labeled values + optional metadata
results = permute(
    data={"ballistic": -0.0012, "normal": -0.0032,
          "deliberative": -0.0044, "extended": -0.0076},
    ordered=True,          # natural ordering matters
    relationship="trend",  # trend | comparison | composition | distribution
)

# Output: list of (encoding_name, rendered_text, rationale)
for name, chart, why in results:
    print(f"── {name} ──")
    print(f"   {why}")
    print(chart)
    print()
```

### Relationship → encoding map

| Relationship | Primary encodings | When to use |
|---|---|---|
| **trend** | slope, sparkline, indexed bar | Ordered categories, monotonic or cyclic patterns |
| **comparison** | bar, dot plot, ratio annotation | Unordered categories, "which is bigger" |
| **composition** | stacked bar, proportion, waffle | Parts of a whole |
| **distribution** | histogram, box markers, percentile | Spread and shape of continuous values |

### Encoding catalog

| Encoding | When it wins | Tufte principle |
|---|---|---|
| Horizontal bar | Large magnitude differences (>3×) | Clear, but low data-ink for similar values |
| Dot plot | Many items, similar values | Maximum data-ink ratio |
| Sparkline | Inline in prose, space-constrained | Data-word integration |
| Slope/gradient | Trend across ordered categories | Reveals monotonicity |
| Ratio annotation | Relative change matters more than absolute | "Compared to what?" made explicit |
| Ranked table | >8 items, multiple metrics per item | When structure matters more than shape |
| Lollipop | Bar chart with less ink | Same info, less chartjunk |

## What permute does NOT do

- Pick for you. It generates alternatives; you choose.
- Add decoration. Every encoding is minimal — no borders, no gridlines, no legends unless the data demands them.
- Generate images. This is the text path only (Unicode/monospace). The image path (`typeset.py`) is a separate concern.

## Advanced techniques

Three patterns from visualization research that elevate permute from "chart picker" to infographic generation:

### Semantic zoom

Same data at different levels of detail, triggered by context — not by pinching a screen, but by where the chart appears. A sparkline in a README becomes a full bar chart in a deep-dive doc becomes an annotated slope chart in a blog post. The data doesn't change; the ink budget does.

```
Level 0 (inline):    ▁▃▅█ (-0.001→-0.008)
Level 1 (summary):   4 bars with labels and values
Level 2 (analysis):  Slope chart + ratio annotations + trend line + n= callout
```

Permute generates all levels from one data spec. The caller picks the zoom level for their context. This is Shneiderman's mantra — "overview first, zoom and filter, details on demand" — applied to static text output.

### Small multiples

Tufte's most powerful idea: the same visual structure repeated across a faceting variable. Not one chart of all data, but N charts of sliced data, aligned so your eye does the comparison.

```
  Mouse (n=3,725)                    Touch (n=1,476)

  ballistic   ███  8.5%             ballistic   █████████  26.3%
     normal   ███████████████ 41.9%    normal   ████████████████ 46.1%
  deliberative████████████████ 37.8% deliberative██████  17.0%
    extended  █████  11.9%            extended  ████  10.6%
```

Two charts. Same structure. The difference *leaps out* without annotation because the visual encoding is consistent. Permute should offer small-multiple layouts whenever the data has a natural facet (device type, age group, condition).

### Linked displays

Multiple chart types showing different aspects of the same dataset, arranged as a unit. Not alternatives (pick one) but complements (read together). This is the infographic aspiration — a composed visual narrative from structured data.

```
┌─ Distribution ──────────────┐  ┌─ Trend ──────────────────────┐
│  normal    ████████████ 1230 │  │  Deceleration:  ▁▃▅█         │
│  deliber.  ██████████  1061  │  │  Pause:         ████ ████ █████│
│  extended  ███          288  │  │  Corrections:   █████ ██ █    │
│  ballistic ██           216  │  │                               │
└──────────────────────────────┘  └───────────────────────────────┘
         n=2,795 clicks                  4 hold-duration buckets
```

Distribution on the left (what the data looks like). Trends on the right (how the metrics move across buckets). Linked because they share the same axis of hold-duration buckets. Together they say more than either alone.

## Aspiration: infographics

The end state isn't "a chart." It's a **composed visual narrative** — what a good editorial infographic does. Data enters as structured JSON (like `research-findings.json`). Permute selects encodings. Linked displays arrange them into a coherent layout. Semantic zoom adapts the output to the publication context.

The typographer already has two rendering paths: Pillow images and Unicode text. Infographics can live in either. A terminal-native infographic is a linked display of ASCII charts. A store asset infographic is a Pillow composition of rendered chart images with text overlays.

The research-findings.json in ClickSense is the first test corpus. 26 findings across 8 domains — enough to compose a real infographic showing the landscape of motor behavior research as it relates to click confidence.

## Status

Not yet built. `chart.py` has `bar_chart()`, `sparkline()`, and `table()`. Permute would add:
- Relationship classifier (trend/comparison/composition/distribution)
- New encodings: dot plot, slope chart, ratio annotation, lollipop
- Small-multiple layout engine (faceted repetition)
- Linked-display composer (multiple chart types, shared axes)
- Semantic zoom levels (inline → summary → analysis)
- `permute()` function that generates all applicable views from one data spec
