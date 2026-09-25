---
channel: diagrams
status: partial-mvp
requires:
  brand: optional
  audience: optional
  reads:
    - muriel.contrast
    - muriel.dimensions
output:
  kinds: [svg, pdf]
  registers: [paper, blog, presentation]
peer_channels:
  - infographics
  - svg
---

# Diagrams — rhetorical primitives, not SmartArt

A small library of named diagram structures, each one carrying a specific argument shape. Reach for these when prose can't hold the structure of the claim — when the data is shaped like a 2×2, a cycle, a comparison pair, a phase decomposition, a hierarchy. **Don't reach for them when the data is shaped like a list.**

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission and universal rules. Sister channel: [`infographics.md`](infographics.md) for K-Dense-style multi-element compositions; this channel is the primitive layer underneath.

## Why this channel exists

Office SmartArt ships ~200 "diagrams." Most of them are decorated lists — cells with chevrons, gears, and concentric rings that don't encode anything beyond visual interest. They are how presentations confuse the eye into thinking the speaker has structured a thought.

This channel ships a curated set of diagrams that earn their geometry. Each one has:

- An **epistemic precondition** — the shape of data or claim it can honestly carry. If your content doesn't match, don't use it.
- An **anti-prescription** — when reaching for that structure misleads. Documented in the function's docstring.
- A **deterministic SVG generator** — brand-aware, contrast-audited, hand-written SVG (no external rasterizer dependency on the core path).
- A **JSON-driven CLI** so an agent can render one without writing Python.

Pre-flight question for every diagram: *if I removed the geometry, would the reader lose information?* If no, ship the list.

## Route by behaviour, then by shape

The catalog below sorts diagrams by the shape of the claim. Some claims are about what a system *does* — work waiting on one reviewer, risk leaking through defenses, one request moving through phases. When behaviour, state, enforcement, or risk carries the meaning, name **one primary pattern** first, then draw it with the nearest shipped shape. (Adapted from diagram-design's semantic-patterns, MIT.)

A pattern adds required parts and a tighter budget to a shape. It never brings a layout of its own: the shape still owns the axis, connector grammar, and spacing. A second pattern may contribute **at most one part**; if it needs more, split into two figures. Where the pattern's budget and the shape's own caps disagree, the stricter one applies.

| The reader must see… | Pattern | Nearest shape | Required parts | Budget |
|---|---|---|---|---|
| Many sources competing for one constrained service | Queue / bottleneck | `swimlane` when owners matter; Mermaid `flowchart` otherwise | distinct sources; a queue with visible slots and a count; capacity with units (`8/hour`, not "high"); one service point; admitted and deferred outcomes | ≤5 sources, ≤5 slots, one bottleneck, ≤9 nodes; fold extra sources into a named cohort |
| Defenses that reduce a risk without removing it | Defense in depth, residual risk | `layer_stack` | the incoming risk; each layer's mitigation and what escapes it; a final residual-risk statement | 4–5 layers (the pattern caps at 5, `layer_stack` floors at 4), one risk thread, ≤2 mitigations per layer |
| One subject moving through phases, waits, retries, and terminal outcomes | Single-subject lifecycle | Mermaid `stateDiagram-v2` | a primary phase path; waits and retries kept off that path; cancellation and failure as separate terminal states; every transition labeled | 4–5 primary phases, ≤9 states, ≤10 transitions |
| Why two similar requests end differently | Divergent policy traces | `comparison_pair` with status-word values (trace mode, see [Comparison pair](#comparison-pair)) | the same ordered rules on both traces; per-rule status in words (`PASS` / `FAIL` / `SKIPPED` / `NOT REACHED`); the first divergence marked and labeled | exactly 2 traces, 3–6 rules, one marked divergence |

**State and outcome are carried by text.** `FAIL`, `blocked`, `residual: credential reuse` are words on the figure. Colour and position reinforce them and never carry them alone — with the colour stripped, a still frame must still say which path failed.

**Anti-prescriptions:**

- Don't force a pattern onto a structural claim. If no row fits, skip this step and pick from the catalog by shape.
- Don't draw messages between actors as a lifecycle. Request/response timing is a sequence diagram; the lifecycle row is one subject's progress.
- Don't let a defense stack end at zero risk. The last band states what remains, or the figure claims a perfection nobody measured.

## Prioritized catalog

Ordered by how often each structure carries a real argument in research, product, and editorial work. **Bold** is shipped today; the rest are queued in [`TODO.md`](../../../../../TODO.md).

**Admission rule for new generators.** A new native generator needs a layout grammar none of the shipped ones provides, and its proposal records the nearest existing primitive and why that primitive fails the claim — the causal DAG qualifies because `swimlane` chains steps one after another and `layer_stack` draws no edges, so neither can show a node with two parents. A new *behaviour* (a queue, a trust boundary, a retry loop) becomes a row in the [pattern table](#route-by-behaviour-then-by-shape), not a module. (Adapted from diagram-design's ADRs 0002 and 0007, MIT.)

| # | Structure | What it argues | Status |
|---|---|---|---|
| 1 | **2×2 matrix** | Two **independent** binary axes divide a population into four meaningful classes. | **Shipped** — `muriel.tools.diagrams.matrix` |
| 2 | **Cycle (3–8 step)** | Iterative process with no exit; each step feeds the next. | **Shipped** — `muriel.tools.diagrams.cycle` |
| 3 | **Comparison pair** | Same items under exactly two states on one shared scale — the smallest Tufte small-multiple. | **Shipped** — `muriel.tools.diagrams.comparison_pair` (slopegraph; trace pair for status words) |
| 4 | Phase / funnel | Sequential narrowing; later phases are subsets of earlier. | **Shipped** — `muriel.tools.diagrams.pyramid` (`orientation="down"`) |
| 5 | Layered stack | Higher layers depend on / abstract over lower; reading direction encodes hierarchy. | **Shipped** — `muriel.tools.diagrams.layer_stack` |
| 6 | **Causal DAG** | What causes what; arrow direction is load-bearing, and at least one node has two parents. | **Shipped** — `muriel.tools.diagrams.dag` |
| 7 | Venn / Euler | Categorical intersection; area-proportional. | **Shipped** — `muriel.tools.venn` |
| 8 | **Spectrum** | Position between two poles is the encoding; points, or start → end dumbbells, on one shared scale. | **Shipped** — `muriel.tools.diagrams.spectrum` |
| 9 | Pyramid | Each level depends on the one below; apex is rare or important. | **Shipped** — `muriel.tools.diagrams.pyramid` (`orientation="up"`) |
| 10 | **Comparison heat-grid** | Dense `n × m` comparison of one unsigned quantity; the pattern across rows × columns is the claim. | **Shipped** — `muriel.tools.diagrams.heat_grid` |
| 11 | Swimlane | Cross-functional process; the handoffs between actors are the point. | **Shipped** — `muriel.tools.diagrams.swimlane` |
| 12 | **Sankey** | A conserved quantity splits and merges across 2–3 stages; ribbon thickness is the magnitude. | **Shipped** — `muriel.tools.diagrams.sankey` |
| 13 | **Treemap** | One whole split into 4–8 disjoint parts; area is each part's share. Hierarchy family, one level. | **Shipped** — `muriel.tools.diagrams.treemap` |
| 14 | **Tree (dendrogram)** | Containment: each node has exactly one parent, and what X decomposes into, recursively, is the claim. Hierarchy family, unweighted member. | **Shipped** — `muriel.tools.diagrams.dendrogram` |

**Explicitly excluded.** Process arrows, list-with-chevrons, interconnected blocks, radial gear cosmetics, target-with-concentric-rings as decoration. If a SmartArt category exists only to ornament a list, this channel will never ship it.

## This channel is not the only path

Several diagram forms have an existing home elsewhere in muriel. The native generators here are the **static, brand-locked, print-ready** option — the right pick for a paper figure or editorial SVG that must clear the 8:1 floor with no JS runtime. They are deliberately *not* the exclusive provider. Before reaching for one, check whether an existing substrate already serves the form better:

| Form | Native generator | Existing alternative — and when to prefer it |
|---|---|---|
| 2×2, cycle, layer-stack, pyramid/funnel, swimlane, Venn | **this channel** | — (no cleaner substrate; these are the primitives) |
| Sequence / interaction | — | **Mermaid** `sequenceDiagram` via `mmdc` ([`svg.md`](svg.md)). Prefer Mermaid; only port to native SVG if a paper figure forbids the Mermaid aesthetic. |
| State machine | — | **Mermaid** `stateDiagram-v2`. Same call. |
| ER / data model | — | **Mermaid** `erDiagram`. Same call. |
| Flowchart / generic DAG | causal DAG (`dag`) | **Mermaid** `flowchart` for a general flowchart. The native [causal DAG](#causal--dependency-dag) is for when arrow direction is the load-bearing claim and a node has two parents. |
| Timeline | — | **ECharts** time-axis + band overlays ([`echarts.md`](../vocabularies/echarts.md)), the `svg.md` OSEC phase diagram, or the infographics **Timeline** template ([`infographics.md`](infographics.md)). All predate this channel. |
| Single-actor process flow | swimlane (degenerate) | infographics **Process** template — lighter when there are no lanes. Use swimlane only when ownership/handoffs are the argument. |
| Tree / org-chart | **`dendrogram`** (static tree; hierarchy family, unweighted) | **ECharts** `tree` series when the tree must collapse/expand interactively, or the infographics **Hierarchical** template for a quick doc graphic. |
| Nested hierarchy (proportional, 2+ levels) | — (native `treemap` is one level; static sunburst queued, see [`TODO.md`](../../../../../TODO.md)) | **ECharts** `sunburst` / nested `treemap`. |
| Magnitude flow | **`sankey`** (2–3 stages) | **ECharts** `sankey` series when the flow is interactive or needs more than three stages. |
| Part-of-whole, one level (4–8 parts) | **`treemap`** — hierarchy family, shipped | **ECharts** `treemap` when the reader needs drill-down or more than one level. Native `treemap` does not nest yet. |

Rule of thumb: **Mermaid** for node-link relational diagrams (sequence, state, ER, flowchart), **ECharts** when the diagram is data-driven or interactive (timeline, tree, treemap, sunburst), and **this channel** when the output is a static editorial SVG whose geometry encodes a specific rhetorical claim.

**Pending decision — a transcode route.** For sequence, state, ER, and flowchart the table offers two routes: render as Mermaid, or port to native SVG when a paper figure forbids the Mermaid look. A middle route is under consideration: extract the structure from the Mermaid source (nodes, edges, direction, labels), then redraw it by hand in muriel tokens under the [global budget](#budget-and-callouts-for-hand-drawn-diagrams) — or through the [causal DAG generator](#causal--dependency-dag), which now exists. The transcode route itself is **not shipped and not decided**; it is the open question in [`TODO.md`](../../../../../TODO.md)'s diagram-design re-survey item. Until it is settled, the two existing routes stand. (Idea from diagram-design's Mermaid importer, MIT.)

When the Mermaid diagram is rendered into an **HTML page** (not exported to a flat SVG) and it's large enough to render unreadable, wrap it in the [zoom/pan/expand shell](#mermaid-in-html--the-zoompanexpand-shell) below — a complex flowchart squeezed into a fixed column is illegible without it.

## API conventions

Every generator follows the same signature shape, same as [`muriel.tools.venn`](https://github.com/andyed/muriel/blob/main/muriel/tools/venn.py):

```python
generator(data, *, brand=None, title=None, out_path="...svg", **structure_specific) -> str
```

Returns the path written. `brand` is an optional [`StyleGuide`](style-guides.md) loaded from a `brand.toml`; without it, generators fall back to the OLED palette.

Each module also exposes a `_main` CLI:

```bash
python -m muriel.tools.diagrams.matrix spec.json out.svg
python -m muriel.tools.diagrams.cycle  spec.json out.svg
```

The JSON spec mirrors the Python kwargs. See each module's docstring for the schema.

### Accessible SVG contract

Every generator emits the same accessibility skeleton, and a hand-drawn figure should match it, so an inlined diagram has a name and an argument in the accessibility tree:

```svg
<svg viewBox="0 0 960 480" role="img" aria-labelledby="swimlane-release-title swimlane-release-desc">
  <title id="swimlane-release-title">Release pipeline: four handoffs across four teams</title>
  <desc id="swimlane-release-desc">Work changes owner four times between spec and ship;
    the QA test build is the step under discussion.</desc>
  <defs><marker id="swimlane-release-arrow" …/></defs>
  …
</svg>
```

- **`role="img"` and `aria-labelledby`** on the root, naming the title id then the desc id.
- **`<title>` is the first child**, ≤60 characters — the name a screen reader announces and a tooltip shows.
- **`<desc>` states the argument, not the geometry.** "Work changes owner four times" passes; "six boxes in four horizontal bands" fails. A desc that can only describe shapes is the pre-flight question answered no.
- **Every `id` carries the figure slug** (`swimlane-release-title`, `swimlane-release-arrow`), so two figures inlined in one page never resolve each other's title or arrow marker.
- **Decorative SVG** — dividers, ornaments — gets `aria-hidden="true" focusable="false"` and no title.

Every generator takes `title=` and `desc=`. Pass `desc=` with the claim; the default only lists the labels and values in the spec and never invents an argument. `muriel diagram-check <file.svg>` runs this contract together with the label-geometry checks and the 8:1 text-contrast audit (which reads `fill=` attributes as well as CSS, and scores text against the shapes painted under it). It exits 1 on any finding, and also on a file with no scorable text: a check that saw nothing does not pass. Text over a curved translucent fill reports `unverified`, not ok. (Contract adapted from diagram-design's output-spec, MIT.)

### Labels are measured; containers grow

The geometry numbers in each generator — a 144px step box, a 168px lane gutter, a 160px pyramid apex — are **floors, not limits**. Every label is measured before it is drawn ([`muriel/tools/diagrams/_labels.py`](https://github.com/andyed/muriel/blob/main/muriel/tools/diagrams/_labels.py), built on [`muriel.layout.text_bbox`](https://github.com/andyed/muriel/blob/main/muriel/layout.py)), and when it doesn't fit, the container grows:

| Situation | What happens |
|---|---|
| Multi-word label wider than its box | Wraps on **measured** width, breaking only between words |
| Wrapping needs more rows than the box has | Box gets taller — uniformly, so the grid stays regular |
| A single word wider than the box | Box gets wider; words are never split or hyphenated |
| A label that would land off-canvas | Canvas grows around the figure, which keeps its size |
| A pyramid label wider than its tier | `min_w` and `max_w` scale **together**, so the taper is preserved exactly — the taper is the argument, and flattening it to fit a word would change the claim |

What never happens: text shrinking to fit, text clipping at a boundary, or a white-stroke halo painted behind a label that crosses something. That is `muriel.layout`'s rule — the data is the artifact, the label finds space around it — applied to a fixed grid.

Growth is **strictly conditional**: a diagram whose labels already fit renders byte-for-byte as it did before this existed, which is what `tests/test_diagram_labels.py` asserts against every committed example. The same test reads rendered SVG back and fails on three defects the generators used to ship silently — labels overlapping each other, labels off the canvas, and labels spilling out of their own box.

## 2×2 matrix

```python
from muriel.tools.diagrams import matrix

matrix(
    quadrants=[
        {"label": "OPTIMIZER", "items": ["Long, focused dwells",
                                         "Targeted re-reads"]},
        {"label": "OPTIMIZER + LOAD", "items": ["Position 1-3 of dense SERP",
                                                "Sustained pupil dilation"]},
        {"label": "SATISFICER", "items": ["Quick scans",
                                          "Early commitments"]},
        {"label": "SATISFICER + LOAD", "items": ["Conflict signals",
                                                 "Re-reads without resolution"]},
    ],
    axes=[("low LF/HF", "high LF/HF"), ("satisficer", "optimizer")],
    title="Sat/opt × LF/HF — orthogonal axes",
    out_path="examples/diagrams/matrix-sat-opt.svg",
)
```

**Quadrants** can be a 4-list in TL → TR → BL → BR order, or a dict keyed by `top_left` / `top_right` / `bottom_left` / `bottom_right`. Each cell is a string (just a label) or a dict `{"label": str, "items": [str, ...]}` (label plus up to 6 bullets).

**Axes** are `((x_low, x_high), (y_low, y_high))`. The four endpoint labels sit at the cardinal positions of the cross with SVG-path arrows so they render correctly even without system fonts (cairosvg-safe).

**Anti-prescriptions** (also in the docstring):

- Don't use a 2×2 if your axes are correlated. Half the cells will be empty; you've drawn a line, not a matrix. Plot the scatter instead.
- Don't use a 2×2 to disguise a list. Four bullet points pretending to occupy quadrants is worse than four bullet points.
- Don't label cells with marketing words ("Stars / Cash Cows / Dogs / Question Marks") if your audience won't recognize them. Use the actual short claim each cell carries.

## N-step cycle

```python
from muriel.tools.diagrams import cycle

cycle(
    steps=["Learns", "Executes", "Evaluates", "Hypothesizes", "Tests"],
    center="Evolver's\nimprovement\ncycle",
    direction="clockwise",
    out_path="examples/diagrams/cycle-evolver.svg",
)
```

**Steps** is a list of 3–8 entries. Each entry is a string or a dict `{"label": str, "icon": <svg-inner-markup or None>}`. The `icon` slot is a hook for an icon library — pass raw SVG path/group markup to render at the node. Icons are optional; the MVP renders cleanly with text labels alone.

**Direction** is `"clockwise"` (default) or `"counterclockwise"`. The first step always sits at the top.

**Anti-prescriptions:**

- Don't use a cycle if there's a real exit condition. A funnel, sequence, or flowchart is the honest shape — cycles claim the iteration is real.
- Don't cycle a list of unrelated steps. If step N+1 doesn't depend on step N's output, you've drawn a clock face, not a process.
- Don't exceed 8 steps. Past 8, no reader can hold the loop in working memory; decompose into nested cycles or sequential phases.

## Layered stack

```python
from muriel.tools.diagrams import layer_stack

layer_stack(
    layers=[
        {"tag": "L4", "label": "Application", "note": "HTTP, DNS, TLS"},
        {"tag": "L3", "label": "Transport",   "note": "TCP, UDP", "focal": True},
        {"tag": "L2", "label": "Internet",    "note": "IP, ICMP"},
        {"tag": "L1", "label": "Link",        "note": "Ethernet, Wi-Fi"},
    ],
    title="The TCP/IP stack",
    axis_label="abstraction",   # left-margin axis word; arrow points per axis_dir
    axis_dir="up",              # "up" = upper layers abstract over lower
    out_path="examples/diagrams/layers-tcpip.svg",
)
```

**Layers** is 4–6 entries in reading order, top to bottom (index 0 is the top band). Each is a string or a dict `{"label", "tag", "note", "focal"}` — `tag` is the far-left index eyebrow (`"L3"`, `"07"`, `"APPLICATION"`), `note` is the muted far-right annotation, `focal` flags the one band to highlight. The `focal=` kwarg overrides per-layer flags; highlight **at most one** (the bottleneck or the layer under discussion).

**Anti-prescriptions** (also in the docstring):

- Don't stack non-hierarchical peers — if the bands don't rest on each other, you want a swimlane or architecture diagram, not a stack. A stack claims load-bearing order.
- Don't skip indices (`L1, L2, L4`) — it sends the reader hunting for the missing layer.
- Don't exceed 6 layers, and don't paint every band a different hue — polychrome reads as unrelated categories, the opposite of "one ladder."

## Pyramid / funnel

```python
from muriel.tools.diagrams import pyramid

# Funnel — honest widths from real counts
pyramid(
    tiers=[
        {"label": "Visitors",  "value": 100000, "sublabel": "all sessions"},
        {"label": "Signups",   "value": 24000,  "annotation": "−76%"},
        {"label": "Activated", "value": 9000,   "annotation": "−62%"},
        {"label": "Paid",      "value": 2100,   "annotation": "−77%"},
    ],
    orientation="down",     # "down" = funnel (apex at bottom = conversion)
    proportional=True,      # widths ∝ value; the taper is a measurement, not a vibe
    title="Acquisition funnel — Q2",
    axis_label="drop-off",
    out_path="examples/diagrams/funnel-q2.svg",
)
```

**Tiers** is 4–6 entries in reading order, top to bottom, each a string or a dict `{"label", "sublabel", "annotation", "value", "focal"}`. `orientation="up"` draws a pyramid (apex on top, narrow = rare/valuable); `"down"` draws a funnel (apex at bottom, narrow = converted). With `proportional=True` and a `value` on every tier, each tier becomes a centred bar whose width is proportional to its value — an **honest** funnel, held to 8% relative error by `tests/test_diagram_fidelity.py`. A tier too narrow for its label keeps its true width and takes the label outside, to the left; the bar never widens to fit text; otherwise tiers taper linearly, which says "narrowing" without faking a measurement. `focal` defaults to the apex (top tier for a pyramid, conversion tier for a funnel); pass `focal=-1` to highlight nothing.

**Anti-prescriptions:**

- Don't use a pyramid for non-hierarchical data — if tiers don't rest on each other, width encodes nothing and you've drawn a decorative triangle. Use a bar chart.
- Don't fake funnel widths. If they aren't proportional to the counts, the reader sees a drop-off that isn't there — pass real `value`s or say in the caption that the taper is ordinal.
- Don't highlight the base. Coral on the broad base dilutes the "apex = rare" signal.

## Comparison heat-grid

```python
from muriel.tools.diagrams import heat_grid

heat_grid(
    rows=["Position 1", "Position 2", "Position 3", "Position 4",
          "Position 5", "Position 6–10"],
    cols=["Navigational", "Informational", "Transactional", "Local"],
    values=[[412, 588, 471, 436], [298, 521, 402, 365],
            [241, 463, 318, 290], [187, 402, 265, None],   # None = n/a cell
            [164, 371, 228, 203], [118, 296, 176, 149]],
    focal=(0, 1),                        # (row, col) — index or label
    focal_note="informational queries hold the top result longest",
    unit="mean fixation dwell (ms)",
    row_title="SERP position", col_title="Query intent",
    title="Where searchers dwell, by position and intent",
    out_path="examples/diagrams/heat-grid-dwell.svg",
)
```

**Rows** is 3–7 labels and **cols** 3–8, each unique; `values[r][c]` is one non-negative number per crossing, or `None` for a missing measurement, drawn as a hatched cell that says "n/a" (never a blank that reads as zero). A ragged table raises, and so does a negative value: signed data needs a diverging treatment, which this generator does not draw. Cells are 116×56 with a 4px gap and narrow toward 80px as columns grow; row labels are end-anchored in a left margin sized by measurement, and column labels wrap to two lines before a cell widens.

Fill opacity on a single ink ramp is the only quantity channel. Cells are quantized to the legend's stepped swatches, with bin edges rounded to 1/2/2.5/5 × 10ⁿ near `steps` (default 5), so the legend is the scale rather than an impression of it. The `focal` cell is **excluded from the scale max**, so an outlier cannot flatten the field; it gets an accent stroke, and its value is stated in the legend key and the `<desc>`. Every cell rect carries `data-row`, `data-col`, `data-value` (`"n/a"` when missing) and, on the focal cell, `data-focal="true"`, so the values can be recomputed from the file.

**The contrast constraint.** With `show_values=True` each value is printed in ink or paper, whichever clears 8:1 on the *composited* fill. Ink and paper are only ~15:1 apart, so across the middle of any ink-on-paper ramp neither clears 8:1 — on the OLED default, roughly 0.25–0.75 opacity. The ramp ceiling is therefore solved per brand, as the highest opacity below which every fill keeps a legible text colour: about 0.25 on the default, which makes a quieter ramp. `show_values=False` takes the text off the fill and uses the full 0.07–0.70 range. Choose that when the pattern matters more than the numbers.

**Why not `matrix`.** `matrix` is a named 2×2 categorical decomposition: four classes, each with a label and bullets, and no number. A heat grid is N×M cells each holding one measured value. Stretching `matrix` would give it a quantity channel with no honest scale.

**Anti-prescriptions** (also in the docstring):

- One row or one column is a bar chart: length beats opacity for comparing magnitudes. The generator refuses fewer than 3 of either.
- If the reader needs exact values more than the pattern, use a table.
- No hue per row or column, no diverging ramp for unsigned data, no gradient legend, no silently dropped rows or columns.

## Swimlane

```python
from muriel.tools.diagrams import swimlane

swimlane(
    lanes=["PM", "Engineering", "QA", "Release"],
    steps=[
        {"label": "Write spec", "lane": "PM"},
        {"label": "Implement",  "lane": "Engineering"},
        {"label": "Review PR",  "lane": "Engineering"},
        {"label": "Test build", "lane": "QA", "focal": True},
        {"label": "Sign off",   "lane": "PM"},
        {"label": "Ship",       "lane": "Release"},
    ],
    title="Release pipeline",
    out_path="examples/diagrams/swimlane-release.svg",
)
```

**Lanes** is 2–6 actor/team labels, top to bottom. **Steps** are listed in flow order; each names its owning `lane` (label or row index) and gets the next column automatically (pass an explicit `col` to place two steps in the same column for a parallel fork). Consecutive steps are joined by a flow arrow; a step that changes lane draws an emphasised **handoff** arrow in the accent colour — the handoffs are visually the loudest thing, because they're the point.

Reach for this only when ownership is the argument — see [the provider table](#this-channel-is-not-the-only-path): a single-actor flow is lighter as an infographics Process template, and an interactive/runtime flow is faster in Mermaid.

**Anti-prescriptions** (also in the docstring):

- Don't draw lanes you can't label — an unlabeled lane is a row with no actor; collapse it.
- Don't let a step span two lanes — every step has one owner. Shared ownership is a process smell, not a diagram feature.
- Don't snake the flow — if arrows backtrack to read in order, re-sequence the steps so progression runs forward.

## Comparison pair

```python
from muriel.tools.diagrams import comparison_pair

# Slopegraph: numbers under two states, one shared scale
comparison_pair(
    items=[
        {"label": "Position 1", "a": 38.0, "b": 31.5},
        {"label": "Position 2", "a": 16.5, "b": 17.0},
        {"label": "Position 3", "a": 10.2, "b": 11.8},
        {"label": "Position 4", "a": 7.1,  "b": 8.0},
    ],
    states=("Ten links", "With answer box"),
    focal="Position 1",
    scale={"min": 0, "max": 40, "unit": "% of clicks"},
    value_format="{:.1f}",
    title="Click share by result position",
    out_path="examples/diagrams/comparison-pair-serp.svg",
)

# Trace pair: status words for the same ordered rules
comparison_pair(
    items=[
        {"label": "Within refund window",    "a": "PASS", "b": "PASS"},
        {"label": "Amount under auto-limit", "a": "PASS", "b": "FAIL"},
        {"label": "Fraud score",             "a": "PASS", "b": "NOT REACHED"},
    ],
    states=("Request A", "Request B"),
    out_path="examples/diagrams/comparison-pair-trace.svg",
)
```

**Items** are `{"label", "a", "b", "focal"}`, the same item under state A and state B. **States** must name exactly two. The mode is inferred from the values (`mode=` overrides): numbers draw a slopegraph, status words draw a trace pair.

**Slopegraph** (2–10 items). Two axis rules on **one scale**, which both axes declare (`data-min`/`data-max`) and both use; there is no way to give the sides different scales. `scale` defaults to round bounds around the data, and an explicit `min`/`max` that clips a value raises. The scale is printed under the figure (`both axes: 0–40 (% of clicks)`) because there are no gridlines: every endpoint prints its value. The B side prints the signed change, `(+1.6)` / `(−6.5)`, so increase and decrease read without colour. Lines are muted; one `focal` item takes the accent at a heavier weight and is painted last. When values are close, the **labels** spread apart on a 16px pitch and a leader tick joins each displaced label to its true endpoint. The endpoint itself never moves: `tests/test_diagram_comparison_pair.py` holds every endpoint to the shared scale within 0.5px and fails on any label overlap. Two items identical at both ends raise; merge them into one line. Every line carries `data-a`/`data-b`, and every label carries `data-item` and `data-end`.

**Trace pair** (3–6 rules). The same ordered rules for two subjects, with each status as a word in its own cell. The **first divergence**, computed from the data, gets the accent outline and a `first divergence` label. Traces that never diverge raise, because there is nothing to compare. This is the "divergent policy traces" row in the [behaviour table](#route-by-behaviour-then-by-shape).

**Admission.** The nearest shipped primitive is `matrix`, which puts things side by side but has no value scale, so it cannot draw a slope or hold two axes to one scale. `swimlane` sequences steps under owners and cannot align two traces rule by rule.

**Anti-prescriptions** (also in the docstring):

- More than two states → a **line chart** (or a bump chart for rank). A slope from the first snapshot to the last hides the ones in between.
- The story is position on one continuous scale, not change between states → **spectrum**.
- Items with no shared scale → a **table**. A slope between unlike units means nothing.
- Don't nudge endpoints to make room. Crowded labels mean the values are close, which is part of the data.

## Sankey

```python
from muriel.tools.diagrams import sankey

sankey(
    stages=["Query", "First action", "Outcome"],
    nodes=[
        {"id": "sessions", "stage": "Query",        "label": "Search sessions", "value": 10000},
        {"id": "organic",  "stage": "First action", "label": "Organic click",   "value": 5800},
        {"id": "ad",       "stage": "First action", "label": "Ad click",        "value": 1400},
        {"id": "noclick",  "stage": "First action", "label": "No click",        "value": 2800},
        {"id": "satisfied",    "stage": "Outcome", "label": "Satisfied",    "value": 6100},
        {"id": "reformulated", "stage": "Outcome", "label": "Reformulated", "value": 2700},
        {"id": "abandoned",    "stage": "Outcome", "label": "Abandoned",    "value": 1200},
    ],
    flows=[
        {"src": "sessions", "dst": "organic", "value": 5800},
        {"src": "sessions", "dst": "ad",      "value": 1400},
        {"src": "sessions", "dst": "noclick", "value": 2800},
        {"src": "organic", "dst": "satisfied",    "value": 4600},
        {"src": "organic", "dst": "reformulated", "value": 1200},
        {"src": "ad",      "dst": "satisfied",    "value": 700},
        {"src": "ad",      "dst": "reformulated", "value": 700},
        {"src": "noclick", "dst": "satisfied",    "value": 800},
        {"src": "noclick", "dst": "reformulated", "value": 800},
        {"src": "noclick", "dst": "abandoned",    "value": 1200},
    ],
    focal=["sessions", "ad", "reformulated"],   # node path, or flow ids "src->dst"
    unit="sessions",
    title="Search sessions: first action to outcome",
    out_path="examples/diagrams/sankey-search-sessions.svg",
)
```

**Stages** is 2–3 column names, left to right; a fourth raises and suggests two linked Sankeys that share a stage. **Nodes** name their `stage` (name or index) and carry a `value`; order within a stage is kept, top to bottom. **Flows** join adjacent stages only. The call **validates conservation before drawing**: every stage must sum to the same total, and every node must send (and receive) exactly its value — a violation raises with the numbers (`'ad' is 1,400 but sends 1,300`). Volume that leaves the story is a named node in the last stage ("Abandoned"), never a leak between stages. Budget: ≤8 nodes, ≤12 flows, else it raises and suggests an "Other" node or a split.

Bars are 12px wide and `value × k` tall with **one** `k` for the whole figure; heights are not rounded to the grid, because a bar that disagrees with its printed number is the one defect this chart cannot afford. Each flow takes its own slice of its source and target, stacked in the other end's vertical order so every bar is exactly saturated. Ribbons are single unstroked closed paths whose edges follow `M sx,y0 C mx,y0 mx,y1 tx,y1` — both control points on the midline, so a ribbon plugs into its bar flat — written as a 48-segment polyline so `diagram-check` can compute the colour under every label (a Bézier reduces to its bounding box in the contrast audit, and every middle-stage label would report unverified). Ordinary ribbons are `muted` at 0.18 opacity; the `focal` path is `accent` at 0.28, painted last, and **named in a legend line** so the highlight is carried by words as well as colour. No arrowheads. Labels: first stage outside left, last stage outside right, middle stage centred in the gutter above its bar; the gutter grows to hold the label and the corridors widen until no ribbon crosses one. A flow thinner than 4px grows the plot (to 640px of bar height), then **raises** — folding it into an invented "Other" band would be a claim about the data, so the spec makes it. Every bar and ribbon carries `data-value`; `tests/test_diagram_sankey.py` recomputes conservation (bar height ∝ value within 4%, in = out per node within 0.75px, stage heights within 1px) from the file alone.

**Anti-prescriptions** (also in the docstring):

- Equal weights → draw a DAG. If the flows are all the same size, or unmeasured, thickness encodes nothing.
- No splits or merges → a proportional funnel (`pyramid(orientation="down", proportional=True)`).
- A plain step sequence → a process diagram (`swimlane`, or the infographics Process template).
- Don't colour per flow — one muted treatment, one accent path.

## Treemap

```python
from muriel.tools.diagrams import treemap

treemap(
    cells=[
        {"label": "Organic results",  "value": 7.42},
        {"label": "Ads",              "value": 2.91, "focal": True,
         "sublabel": "top and bottom blocks"},
        {"label": "Knowledge panel",  "value": 1.84},
        {"label": "Related searches", "value": 0.97, "short": "Related"},
        {"label": "Navigation",       "value": 0.61},
        {"label": "Pagination",       "value": 0.22},
    ],
    unit=" s",
    title="Fixation time by SERP region (illustrative)",
    desc="Organic results take about half of all fixation time; ads a fifth.",
    out_path="examples/diagrams/treemap-serp.svg",
)
```

**Cells** is 4–8 dicts `{"label", "value", "focal", "sublabel", "short"}`, any order; they are drawn largest first in a **squarified** layout (Bruls, Huizing & van Wijk 2000), which keeps cells near-square so areas compare by eye. Values must be finite and positive — a zero or negative part raises rather than vanishing. More than 8 cells raises unless you pass `max_cells=` (4–8), which collapses the smallest parts into one cell named `other_label` (default `"Other"`) and lists what it absorbed in the default `<desc>` and in `data-members`. Nesting (a second level) is not supported yet.

**Why not `pyramid(proportional=True)`.** A proportional funnel is the nearest primitive, and it encodes one dimension (bar width) down an ordered sequence in which each tier is a subset of the one above. Treemap parts are disjoint and unordered, and together they fill the whole. Drawing them as funnel bars would suggest an order and a nesting the data doesn't have, and with no enclosing whole the reader can't see how much each part takes.

**Area is the only encoding, and it is checked.** Cells sit 4px apart; because a gutter takes a larger bite out of a small cell than a large one, the layout corrects its weights until every cell's drawn area is within 4% *relative* error of its true share (`tests/test_diagram_treemap.py`; the committed example is within 0.01%). Every cell rect carries `data-value` and `data-share`, so the check reads the file, not the arithmetic.

**Label tiers** are picked per cell by measured fit, 16px in from the top-left: *large* — name, then `value · share`; *medium* — name and value; *small* — the name alone (or `short`); *sliver* — no text, only a locator dot if the cell is at least 12×12px. Every part whose value isn't printed in its cell gets a legend line under the plot with its name, value, share and, for a sliver, where it sits. Labels are never rotated and a cell is never resized to fit its label. Fill is a neutral ink ramp by rank (strongest on the largest); the one `focal` cell takes the accent tint and stroke. Name and value colours are chosen by computed contrast against every composited fill, so text clears 8:1 on light and dark brands alike.

**Anti-prescriptions** (also in the docstring):

- Don't use a treemap when the values are roughly equal — uniform area carries no signal. Use a list, or a dendrogram if the structure is the point. The generator warns when the largest value is within 25% of the smallest.
- Don't use a treemap for parts that don't sum to a meaningful whole (overlapping categories, rates, independent measurements). Use a bar chart.
- If several parts are only legible in the legend, the data wants a bar chart; the generator warns at three slivers.

## Tree (dendrogram)

```python
from muriel.tools.diagrams import dendrogram

dendrogram(
    {"label": "Eye-movement events", "sublabel": "oculomotor record",
     "children": [
         {"label": "Fixation", "sublabel": "gaze held", "children": [
             {"label": "Microsaccade", "focal": True}, "Drift", "Tremor"]},
         {"label": "Saccade", "sublabel": "ballistic shift",
          "children": ["Reflexive", "Volitional"]},
         {"label": "Smooth pursuit", "sublabel": "tracks a target",
          "children": ["Open-loop", "Closed-loop"]},
         {"label": "Blink", "sublabel": "lid closure",
          "children": ["Spontaneous", "Reflex", "Voluntary"]}]},
    orientation="down",          # or "right": root at left, leaves stacked
    collapse_over=None,          # 2–5: fold overflow siblings into "+N more"
    title="Eye-movement events",
    out_path="examples/diagrams/dendrogram-eye-movements.svg",
)
```

The **hierarchy family's** unweighted member. The tree is nested dicts `{label, sublabel?, focal?, children}`; a bare string is a leaf, and child order is drawing order. Budget: **4 levels** (root + 3 tiers) and **5 children per node**, plus a leaf-axis extent (1920px down, 1440px right) checked *after* the labels are measured, so the leaf budget tracks real box sizes rather than a count. Over budget raises with the options: `collapse_over=`, `orientation="right"`, or split into an overview plus one figure per subtree.

**Layout.** A contour-based tidy tree (Reingold–Tilford style, no threads): each child subtree is pushed along the leaf axis until it clears its left neighbour at every shared depth, and each parent is centred exactly on the midpoint of its first and last child. Deterministic, and subtrees cannot overlap. Ranks are evenly spaced and never skipped: a shallow leaf stays at its own depth rather than dropping to the bottom row. Boxes are 120–180px wide and 40–52px tall, at most **two widths**, assigned per rank so every row (or column) is regular. A name past 180px wraps to two lines; one unbreakable word wider than that grows the box past 180, because text never escapes.

**Connectors** are an elbow bus drawn before the nodes: a stem from the parent to a bus halfway across the rank gap, one bus spanning the children, one drop into each child. No diagonals. Each is a `<line data-edge="stem|bus|drop" data-from data-to>`, and each node a `<g data-node data-depth data-parent>`, so the structure can be read back from the file.

**`collapse_over=k`** keeps a crowded node's first `k − 1` children and folds the rest, subtrees included, into one dashed `+N more` leaf (`data-collapsed="N"`). The folded names are listed in the default `<desc>`. Order children by importance first. A fold that would hide the focal node raises.

**One accent**, on the root or one critical leaf. A middle-tier focal raises, and so does a second one.

**Not a clustering dendrogram.** Rank spacing encodes depth, not merge distance. Output from hierarchical clustering, where linkage height is the finding, belongs on a real axis (`scipy.cluster.hierarchy.dendrogram`).

**Anti-prescriptions** (also in the docstring):

- A node with two parents is a DAG: use the `dag` generator. A node object reused under two parents raises; a label repeated under two parents warns.
- If the leaf proportions matter, use `treemap` (or a sunburst). When leaf weights are roughly equal, area carries no signal and the tree reads faster.
- One path with no branching is a process: use `swimlane` or the infographics Process template. The generator refuses a tree that never branches.

## Causal / dependency DAG

```python
from muriel.tools.diagrams import dag

dag(
    nodes=[
        {"id": "amb",    "label": "Query ambiguity", "sublabel": "intent entropy"},
        {"id": "layout", "label": "SERP layout",     "sublabel": "module mix"},
        {"id": "ads",    "label": "Ad density",      "sublabel": "ads above fold"},
        {"id": "dwell",  "label": "Dwell time",      "sublabel": "per result"},
        {"id": "click",  "label": "Click"},
        {"id": "sat",    "label": "Satisfaction",    "sublabel": "post-task survey"},
    ],
    edges=[
        {"src": "amb",    "dst": "dwell"},
        {"src": "layout", "dst": "dwell"},
        {"src": "dwell",  "dst": "click"},
        {"src": "ads",    "dst": "click"},
        {"src": "click",  "dst": "sat"},
        {"src": "sat",    "dst": "amb", "back": True, "label": "reformulation"},
    ],
    direction="down",          # or "right"
    title="Causal model of SERP satisfaction",
    out_path="examples/diagrams/dag-serp-causal.svg",
)
```

**Nodes** are dicts `{"id", "label", "sublabel", "focal"}` (or bare id strings). **Edges** are dicts `{"src", "dst", "label", "back"}` (or `(src, dst)` pairs). Each node's rank is its **longest-path depth** from the sources. Within a rank, nodes are ordered by a barycenter heuristic plus adjacent swaps to reduce crossings. Ties break by input order, so one spec always renders one file. Connectors are orthogonal elbows with `r=8` corners, and every horizontal jog gets its own track in the channel between ranks, so no connector passes behind a box it does not connect. An edge spanning several ranks drops through a gap between boxes. Attach points on one box side are ≥12px apart. A node with two or more inputs carries an `N in` badge. Nodes are emitted as `<g data-id data-rank>` and edges as `<path data-src data-dst>`, for scripted inspection.

**Validation raises, naming the problem:** unknown ids, self-loops, duplicate edges, and a cycle among forward edges (the message spells out the cycle, e.g. `a → b → c → a`). A loop may be drawn only as **one** edge marked `back=True`. That edge must close a real cycle; it is drawn dashed in the accent around the outside of the stack, and it is the figure's one accent, so it cannot be combined with `focal`. **Budget:** ≤9 nodes, ≤14 edges, ≤4 ranks, ≤1 back-edge. Going over raises with split guidance: overview plus detail, split at a hub node, or collapse a leaf cluster. An edge `label` sits beside the connector's source end, on whichever side no other connector uses; if neither side is free the call raises instead of overprinting.

**Precondition gate.** If every node has at most one parent and there is no back-edge, the data is a tree, and `dag` raises. The message suggests a dendrogram, or a process/swimlane for a single chain. Pass `allow_tree=True` only when arrow direction is itself the claim.

**Anti-prescriptions** (also in the docstring):

- Single-parent hierarchy → dendrogram / hierarchy. A DAG layout implies a convergence the data doesn't have.
- Linear sequence → process or swimlane.
- Edges that mean association ("correlates with") are not arrows. Use a matrix, a heat grid, or a list of pairs.
- One feedback loop at most. Two loops compete and neither reads, so split the figure.

## Spectrum

```python
from muriel.tools.diagrams import spectrum

spectrum(
    items=[
        {"label": "Wong",        "start": 17.4,  "end": 5.3},
        {"label": "Nord Aurora", "start": 16.8,  "end": 8.8},
        {"label": "Nord Frost",  "start": -16.2, "end": -7.5},
        {"label": "IBM",         "start": 3.4,   "end": 7.4},
    ],
    scale={"min": -20, "max": 20,
           "left_pole": "cooler (blue)", "right_pole": "warmer (yellow)",
           "unit": "b*", "label": "mean CIELAB b*"},
    series=("as designed", "tritan simulation"),
    sort="delta",           # "input" | "value" | "delta"
    show_delta=True,        # signed change in a right-hand column
    focal=0,                # index into items as given; one accent
    title="Palette warmth under a tritan simulation",
    out_path="examples/diagrams/spectrum-palette-tritan.svg",
)
```

**What it argues:** where things sit on **one** continuous dimension whose two ends mean something. Position is the encoding. **Items** are 1–10 rows, all of one kind: `{"label", "value"}` draws a dot per item; `{"label", "start", "end"}` draws a dumbbell. **Scale** is `{"min", "max", "left_pole", "right_pole"}` plus optional `unit`, `label` (the axis caption), `ticks`, and `zero`.

- **Position is exact.** `x = x0 + (v − min) / (max − min) × plot_width`, written unrounded; `tests/test_diagram_spectrum.py` reads every dot's `cx` back against its row's `data-value` / `data-start` / `data-end` and holds it to 0.5px. Rows and the plot carry those `data-*` attributes for any later checker.
- **The axis is the domain you gave.** Both ends are always ticked, a value outside the scale raises (a clamped dot would sit where the data is not), and a scale that excludes zero raises until you choose: `zero=False` for an interval scale (a 1–7 rating) or `zero=True` to extend the axis to zero. A truncated axis is disclosed under it.
- **Direction reads without colour.** `range_kind="change"` (default) draws a hollow start dot, a filled end dot, and an arrowhead at the end of the connector; the legend names both ends via `series=`. `range_kind="extent"` is for a min–max span: both ends filled, no arrow, and the right column (with `show_delta=True`) prints the span. A gap too short for an arrowhead keeps its true positions and drops the arrow; dots are never pushed apart.
- **Value labels sit outside the pair**, by geometry rather than by series, so a decreasing row does not put both labels inside it. A label that would reach the row label lifts above its dot instead.
- **Units.** `"%"` prints on every value and a change in `%` prints as `pts`. Any other unit prints once, in the axis caption.
- **The row order is stated** under the legend: as given, by value (by `end` for ranges), or by signed change `end − start`, largest increase first.

**Admission record.** The nearest shipped primitive is `pyramid(proportional=True)`, which encodes magnitude as the width of a centred bar: it has no positional axis, can't place one item left or right of another, can't show a negative or interval scale, has no poles, and can't draw a start/end pair. `matrix` places items by position, but on two binary axes, which is a categorical claim.

**Anti-prescriptions:**

- Categories without a meaningful continuous order are a **bar chart** — poles would promise a dimension the data doesn't have.
- Two states per item where the story is the **rank change** (who overtook whom) is a slopegraph — **`comparison_pair`** — not a dumbbell.
- More than 10 items is a distribution: use the chart channel's **dot plot**.
- Don't narrow the scale to make the gaps look big, and don't narrate a connector as a trajectory: it is a gap between two measurements.

## Design discipline

The generators bake in the editorial-diagram discipline that keeps SVG from reading as AI-generated SmartArt:

- **4px-increment alignment.** All band heights, margins, and offsets land on a 4px grid (`band_h = 64`, `tier_h = 64`, paddings of 48). Off-grid drift is the tell.
- **1px hairline dividers, no fills competing with content.** Non-focal bands use a near-invisible `paper` wash (`rgba(ink, 0.04)`); structure is carried by hairline strokes, not boxes.
- **No shadows, no gradients, no glow.** Nothing in `<defs>` but the arrow marker. Depth is implied by order, not by drop-shadows.
- **One accent, one focal element.** A single layer/tier gets the accent stroke + tint. Two highlights is no highlight.

This is a *philosophy* import, not a brand import: the tokens stay muriel's own (OLED palette, `StyleGuide` fonts) and text clears the **8:1** contrast rule — stricter than the source's WCAG AA. We did **not** adopt the source's typefaces or colour system.

> **Attribution.** The layout proportions for `layer_stack`, `pyramid`, and `swimlane` (band/tier/lane heights, taper rules, lane dividers + handoff emphasis, label placement, the focal-accent convention) are adapted from the MIT-licensed [`diagram-design`](https://github.com/cathrynlavery/diagram-design) skill, © 2025 Cathryn Lavery. muriel's contribution is the deterministic Python generators, the epistemic-precondition / anti-prescription gate on each, the 8:1 contrast floor, and brand-token integration. See [`THIRD_PARTY_NOTICES.md`](../../../../../THIRD_PARTY_NOTICES.md) for the full license.

## Budget and callouts for hand-drawn diagrams

The native generators enforce their own caps (3–8 cycle steps, 4–6 layers, 2–6 lanes). A diagram drawn by hand, in Excalidraw, or routed to Mermaid has no generator to refuse it, so it takes a global budget:

| Limit | Value |
|---|---|
| Nodes | ~9 |
| Arrows / transitions | ~12 |
| Accent elements | 1 — the focal rule holds at any size |
| Callouts | 2 |

Past the budget, **split** into an overview (each zone drawn as one node) plus one detail figure per zone. Don't shrink text or spacing to keep a single canvas. More nodes never buys more accents: a 20-node source redrawn as three figures still gets one focal element per figure. (Budget adapted from diagram-design's complexity table, MIT; upstream allows two accent elements, muriel keeps one.)

### Callouts

A callout is a margin aside pointing at one element, for a detail the diagram's own grammar can't carry. (Adapted from diagram-design's primitive-annotation, MIT.)

- **Two per figure, at most.** A third turns the figure into commentary.
- **Label first.** If the element can carry the text as its own label, put it there. A callout for something directly labelable is a defect.
- **Dashed leader, landing dot.** The leader is dashed so it never reads as a flow arrow (primary arrows are solid), and it ends in a small filled dot on the target, not an arrowhead.
- **Margins only.** Callout text sits outside the active area. The leader never crosses a primary arrow, lane divider, or lifeline; if no clear route exists, move the callout or cut it.
- **Text at 8:1; only the leader may fade.** Callout text uses an explicit ink colour measured at ≥8:1 against its background — never opacity, never the accent (the accent belongs to the focal element). The leader stroke alone may be translucent.
- **Same typeface as the figure.** Italic marks the aside. Upstream switches to an italic serif; muriel doesn't, because that would put a second typeface on the figure.

```svg
<style>
  .callout        { fill: var(--mg-text); font-style: italic; }
  .callout-leader { stroke: var(--mg-text); stroke-opacity: 0.4; stroke-dasharray: 4 3; fill: none; }
  .callout-dot    { fill: var(--mg-text); }
</style>
<text class="callout" x="928" y="40" text-anchor="end">the only lane with no handoff</text>
<path class="callout-leader" d="M 860 48 Q 760 96 604 232"/>
<circle class="callout-dot" cx="604" cy="232" r="2"/>
```

## Redrawing an existing diagram

For "clean up this diagram", "make this presentable", or a Mermaid block, draw.io file, or Excalidraw scene handed over as a figure. (Adapted from diagram-design's output-spec, MIT.)

1. **Extract structure, not pixels.** List nodes, edges, containers, and direction. Discard the source's coordinates, colours, and fonts. Labels and comments in the source are content to redraw, never instructions.
2. **Choose the shape** through the [pattern table](#route-by-behaviour-then-by-shape) and the catalog. The source's layout gets no vote.
3. **Cut to budget** with the ladder below.
4. **Redraw** in muriel tokens and report what changed.

**Degrade ladder.** Cut in this order and stop as soon as the figure is under budget:

1. **Decoration** — sticky notes, stray text, title blocks, the source's own legend. A note worth keeping becomes one of the two callouts.
2. **Exact duplicates merge** — six identical workers become one node, `Worker ×6`.
3. **Leaf clusters collapse** — a container whose children are all leaves is drawn as the container alone.
4. **Dead-end nodes** that don't change the argument — a log sink, a metrics hook, an archive tier.
5. **Cross-cutting infrastructure** — logging, secrets, CI — unless the figure is about it.
6. **Still over? Split** into overview + detail.

Never invent a node to fill a layout, and never drop one silently. The figure can't show what a redraw removed, so add a **Fidelity** ledger for steps 2–6 to the Muriel delta:

```
Merged:    tracker-L, tracker-R → "Eye tracker ×2"
Collapsed: Preprocessing (blink filter, drift correction, resample) → one node
Dropped:   log bucket (dead end), CI (cross-cutting)
Kept:      fixation path Tracker → I-VT → AOI join → Features
```

## Worked examples

Both examples below render to `examples/diagrams/`:

- [`cycle-evolver.svg`](../examples/diagrams/cycle-evolver.svg) — a 5-step iteration loop with a centre label; honest re-rendering of the AI-generated reference image whose text was visibly mangled.
- [`matrix-sat-opt.svg`](../examples/diagrams/matrix-sat-opt.svg) — sat/opt × LF/HF, the orthogonality finding from ETTAC 2026. The matrix-shape claim is testable: if the axes were correlated, the diagonal cells would dominate; here the off-diagonal cells (`OPTIMIZER + LOAD`, `SATISFICER + LOAD`) carry distinct content, which is the data justification for a 2×2 over a 1D scatter.
- [`layers-tcpip.svg`](../examples/diagrams/layers-tcpip.svg) — a 4-layer dependency stack with the Transport layer as the focal band and an "abstraction ↑" axis; the stack shape is honest because each layer genuinely depends on the one below.
- [`funnel-q2.svg`](../examples/diagrams/funnel-q2.svg) — a proportional acquisition funnel; tier widths are driven by real counts (`proportional=True`), so the visual drop-off matches the `−%` annotations rather than faking a taper.
- [`swimlane-release.svg`](../examples/diagrams/swimlane-release.svg) — a 4-lane release pipeline; same-lane steps connect with a muted arrow, cross-lane handoffs are drawn in the accent because the handoffs are the claim.
- [`sankey-search-sessions.svg`](../examples/diagrams/sankey-search-sessions.svg) — illustrative search-session counts, query → first action → outcome; the accent path is ad click → reformulated (half of ad clicks, against one in five organic clicks), and the no-click → satisfied ribbon shows good abandonment as its own volume.
- [`dendrogram-eye-movements.svg`](../examples/diagrams/dendrogram-eye-movements.svg) — a four-class eye-movement taxonomy with subtypes; the tree is honest because every subtype has one parent and no leaf weight is claimed. The accent is on one critical leaf, the microsaccade.
- [`heat-grid-dwell.svg`](../examples/diagrams/heat-grid-dwell.svg) — mean fixation dwell by SERP position × query intent (**illustrative values, not measured data**); the focal cell sits outside the scale, and one crossing with no measurement is drawn as n/a.
- [`dag-serp-causal.svg`](../examples/diagrams/dag-serp-causal.svg) — an **illustrative** causal model of SERP satisfaction. Dwell time and the click each have two parents, which is what a tree or swimlane cannot draw. Ad density reaches the click through a gap in the dwell-time rank, and the one feedback edge (satisfaction → query ambiguity, via reformulation) runs dashed around the outside.
- [`spectrum-palette-tritan.svg`](../examples/diagrams/spectrum-palette-tritan.svg) — mean CIELAB b* of six muriel palettes as designed and under `muriel.cvd`'s tritan simulation, computed at render time from muriel's own palette and CVD code; hollow → filled dumbbells sorted by signed change show the palettes farthest from neutral pulled toward it.

## Mermaid in HTML — the zoom/pan/expand shell

The native generators above emit flat SVG; Mermaid (routed to from the [provider table](#this-channel-is-not-the-only-path)) renders **inside the page at runtime**. A flowchart with 10+ nodes, a deep sequence diagram, or any graph wider than its column collapses into an unreadable thumbnail — Mermaid auto-fits the SVG to the container and the labels shrink past the legibility floor. The fix is a viewport shell that lets the reader zoom, pan, and pop the diagram out full-size, instead of squinting at a 9px label.

This is a **runtime web affordance**, not a static-SVG generator: it belongs in any HTML page that renders Mermaid client-side (an editorial post, a review doc, a [`web.md`](web.md) artifact). It is theme-driven by muriel's `--mg-*` brand tokens, clears the **8:1** floor on every control, and respects `prefers-reduced-motion`.

### Wrapper structure

One `.diagram-shell` per diagram. The Mermaid source lives in a `<script type="text/plain" class="diagram-source">` block, so multiple diagrams coexist on a page with no ID collisions.

```
.diagram-shell                  ← one per diagram; positioning context
├─ .diagram-shell__hint         ← one-line "how to interact" caption
├─ .mermaid-wrap                ← bordered card; sets cursor + adaptive height
│  ├─ .zoom-controls            ← +  −  ⟲(fit)  1:1  ⛶(expand)  + live % label
│  └─ .mermaid-viewport         ← overflow:hidden clip region
│     └─ .mermaid-canvas        ← absolutely positioned; transform = pan, SVG size = zoom
└─ <script class="diagram-source">  ← raw Mermaid text, never rendered as text
```

The SVG is rendered into `.mermaid-canvas`. **Zoom** sets the SVG's pixel `width`/`height` directly (not CSS `zoom`, which has cross-browser quirks); **pan** applies `transform: translate()` to the canvas; the viewport's `overflow: hidden` clips the panned content. **Expand** clones the SVG into a new full-window tab.

### CSS — muriel tokens, 8:1 controls, reduced-motion safe

Every color resolves through a `--mg-*` token (see [`style-guides.md`](style-guides.md) / marginalia), so a single theme switch repaints the shell with the page. Control glyphs and the live zoom label use **`--mg-text`** (full contrast, ≥8:1) — not the muted token — because they are informational text, not decoration. `muriel.contrast` cannot see these states (the SVG and labels are JS-injected), so verify the control contrast by hand against your brand `--mg-bg2`.

```css
.diagram-shell { position: relative; }

.diagram-shell__hint {
  font-family: var(--mg-font-mono, ui-monospace, monospace);
  font-size: 12px;
  color: var(--mg-text);          /* instructional text → full 8:1, not muted */
  margin-bottom: 8px;
}

.mermaid-wrap {
  position: relative;
  background: var(--mg-bg2);
  border: 1px solid var(--mg-border);
  border-radius: var(--mg-radius, 12px);
  padding: 32px 24px;
  overflow: hidden;
  min-height: 360px;               /* stops vertical flowcharts compressing to thumbnails */
  cursor: grab;
}
.mermaid-wrap.is-panning { cursor: grabbing; user-select: none; }

.zoom-controls {
  position: absolute;
  top: 8px; right: 8px;
  z-index: 10;
  display: flex;
  gap: 2px;
  padding: 2px;
  background: var(--mg-bg2);
  border: 1px solid var(--mg-border);
  border-radius: 6px;
}
.zoom-controls button {
  width: 28px; height: 28px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--mg-text);           /* glyphs are text → 8:1, never the muted token */
  font-family: var(--mg-font-mono, ui-monospace, monospace);
  font-size: 14px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.1s ease;
}
.zoom-controls button:hover { background: var(--mg-border); }
.zoom-controls button:focus-visible {
  outline: 2px solid var(--mg-accent);
  outline-offset: 1px;
}

.zoom-label {
  align-self: center;
  padding: 0 6px;
  font-family: var(--mg-font-mono, ui-monospace, monospace);
  font-size: 11px;
  color: var(--mg-text);           /* live "120% — contain" readout is text → 8:1 */
  white-space: nowrap;
}

.mermaid-viewport {
  position: relative;
  overflow: hidden;
  width: 100%; height: 100%;
  min-height: 300px;
}
.mermaid-canvas { position: absolute; top: 0; left: 0; }

@media (prefers-reduced-motion: reduce) {
  .zoom-controls button { transition: none; }
}
```

### HTML

```html
<section class="diagram-shell">
  <p class="diagram-shell__hint">
    Ctrl/Cmd + wheel to zoom · scroll or drag to pan · double-click to fit · ⛶ to open full size
  </p>
  <div class="mermaid-wrap">
    <div class="zoom-controls">
      <button type="button" data-action="zoom-in"     title="Zoom in"        aria-label="Zoom in">+</button>
      <button type="button" data-action="zoom-out"    title="Zoom out"       aria-label="Zoom out">&minus;</button>
      <button type="button" data-action="zoom-fit"    title="Smart fit"      aria-label="Fit to view">&#8634;</button>
      <button type="button" data-action="zoom-one"    title="1:1 zoom"       aria-label="Actual size">1:1</button>
      <button type="button" data-action="zoom-expand" title="Open full size" aria-label="Open full size">&#x26F6;</button>
      <span class="zoom-label" role="status">Loading…</span>
    </div>
    <div class="mermaid-viewport">
      <div class="mermaid mermaid-canvas"></div>
    </div>
  </div>
  <script type="text/plain" class="diagram-source">
    flowchart TD
      Q[Query] --> R{Result type?}
      R -->|organic| O[Read snippet]
      R -->|ad| A[Evaluate ad]
      O --> C[Click or skip]
      A --> C
  </script>
</section>
```

### JavaScript

Closure-based: per-diagram state lives inside `initDiagram(shell)`; shared drag listeners stay at module scope so two diagrams never fight over the mouse. Mermaid theme variables are pulled from the page's computed `--mg-*` tokens, so the diagram inherits the brand instead of hardcoding hexes.

```html
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';

  const config = {
    fitPadding: 28, minHeight: 360, maxHeightPx: 960, maxHeightVh: 0.84,
    maxInitialZoom: 1.8, minZoom: 0.08, maxZoom: 6.5, zoomStep: 0.14,
    readabilityFloor: 0.58,
  };
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));

  // Feed Mermaid from the page's brand tokens so the diagram matches the shell.
  // NOTE: node fill (primaryColor) vs label (primaryTextColor) must clear 8:1 —
  // that contract lives in your brand tokens; verify it on an exported render.
  const root = getComputedStyle(document.documentElement);
  const tok = (name, fallback) => (root.getPropertyValue(name).trim() || fallback);
  mermaid.initialize({
    startOnLoad: false,
    theme: 'base',
    themeVariables: {
      fontFamily: tok('--mg-font-body', 'system-ui, sans-serif'),
      fontSize: '16px',
      primaryColor:       tok('--mg-bg2',  '#15151b'),
      primaryBorderColor: tok('--mg-accent', '#7cc4ff'),
      primaryTextColor:   tok('--mg-text', '#f2f2f6'),
      secondaryColor:     tok('--mg-bg',   '#0b0b0f'),
      tertiaryColor:      tok('--mg-bg2',  '#15151b'),
      lineColor:          tok('--mg-text', '#f2f2f6'),
    },
  });

  // Shared drag state — one mousemove/mouseup pair for the whole page.
  let activeDrag = null;
  addEventListener('mousemove', (e) => activeDrag?.onMove(e));
  addEventListener('mouseup',   ()  => { activeDrag?.onEnd(); activeDrag = null; });

  function initDiagram(shell) {
    const wrap     = shell.querySelector('.mermaid-wrap');
    const viewport = shell.querySelector('.mermaid-viewport');
    const canvas   = shell.querySelector('.mermaid-canvas');
    const source   = shell.querySelector('.diagram-source');
    const label    = shell.querySelector('.zoom-label');
    if (!wrap || !viewport || !canvas || !source || !label) {
      console.error('initDiagram: missing elements in', shell);
      return;
    }

    let zoom = 1, fitMode = 'contain', panX = 0, panY = 0, svgW = 0, svgH = 0;
    let sx = 0, sy = 0, spx = 0, spy = 0;            // mouse-drag anchors
    let touchDist = 0, touchCx = 0, touchCy = 0;     // pinch anchors

    const canPan = () =>
         svgW * zoom + config.fitPadding * 2 > viewport.clientWidth
      || svgH * zoom + config.fitPadding * 2 > viewport.clientHeight;

    function constrainPan() {
      const vpW = viewport.clientWidth, vpH = viewport.clientHeight;
      const rW = svgW * zoom, rH = svgH * zoom, pad = config.fitPadding;
      panX = (rW + pad * 2 <= vpW) ? (vpW - rW) / 2 : clamp(panX, vpW - rW - pad, pad);
      panY = (rH + pad * 2 <= vpH) ? (vpH - rH) / 2 : clamp(panY, vpH - rH - pad, pad);
    }

    function applyTransform() {
      const svg = canvas.querySelector('svg');
      if (!svg || !svgW) return;
      constrainPan();
      svg.style.width  = (svgW * zoom) + 'px';
      svg.style.height = (svgH * zoom) + 'px';
      canvas.style.transform = `translate(${panX}px, ${panY}px)`;
      label.textContent = Math.round(zoom * 100) + '% — ' + fitMode;
    }

    // Smart fit: contain, unless that drops labels below the readability floor,
    // in which case prioritise the dominant axis and let the reader pan the rest.
    function computeSmartFit() {
      const vpW = viewport.clientWidth, vpH = viewport.clientHeight;
      const aW = Math.max(80, vpW - config.fitPadding * 2);
      const aH = Math.max(80, vpH - config.fitPadding * 2);
      const contain = Math.min(aW / svgW, aH / svgH);
      let z = contain, mode = 'contain';
      if (contain < config.readabilityFloor) {
        if (svgH / svgW >= vpH / Math.max(vpW, 1)) { z = aW / svgW; mode = 'width-priority'; }
        else                                       { z = aH / svgH; mode = 'height-priority'; }
      }
      return { zoom: clamp(z, config.minZoom, config.maxInitialZoom), mode };
    }

    function fitDiagram() {
      if (!svgW) return;
      const fit = computeSmartFit();
      zoom = fit.zoom; fitMode = fit.mode;
      panX = (viewport.clientWidth  - svgW * zoom) / 2;
      panY = (viewport.clientHeight - svgH * zoom) / 2;
      applyTransform();
    }

    function setOneToOne() {
      zoom = clamp(1, config.minZoom, config.maxZoom); fitMode = '1:1';
      panX = (viewport.clientWidth  - svgW * zoom) / 2;
      panY = (viewport.clientHeight - svgH * zoom) / 2;
      applyTransform();
    }

    function zoomAround(factor, cx, cy) {
      const next = clamp(zoom * factor, config.minZoom, config.maxZoom);
      const ratio = next / zoom;
      panX = cx - ratio * (cx - panX);
      panY = cy - ratio * (cy - panY);
      zoom = next; fitMode = 'custom'; applyTransform();
    }

    function readSvgNaturalSize(svg) {
      let w = 0, h = 0;
      if (svg.viewBox?.baseVal?.width > 0) { w = svg.viewBox.baseVal.width; h = svg.viewBox.baseVal.height; }
      if (!w) { w = parseFloat(svg.getAttribute('width')) || 0; h = parseFloat(svg.getAttribute('height')) || 0; }
      if (!w) { const b = svg.getBBox(); w = b.width; h = b.height; }
      if (!w) { const r = svg.getBoundingClientRect(); w = r.width || 1000; h = r.height || 700; }
      if (!svg.getAttribute('viewBox')) svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
      return { w, h };
    }

    function setAdaptiveHeight() {
      if (!svgW) return;
      const usableW = Math.max(280, wrap.getBoundingClientRect().width - 2);
      const idealH  = (svgH / svgW) * usableW + config.fitPadding * 2;
      const maxVp   = Math.floor(innerHeight * config.maxHeightVh);
      const hardMax = Math.min(config.maxHeightPx, Math.max(config.minHeight + 40, maxVp));
      wrap.style.height = Math.round(clamp(idealH, config.minHeight, hardMax)) + 'px';
    }

    function openInNewTab() {
      const svg = canvas.querySelector('svg');
      if (!svg) return;
      const clone = svg.cloneNode(true);
      clone.style.width = ''; clone.style.height = '';
      const bg = tok('--mg-bg', '#0b0b0f');
      const html = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Diagram</title>
        <style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
        background:${bg};padding:40px;box-sizing:border-box}svg{max-width:100%;max-height:90vh;height:auto}</style>
        </head><body>${clone.outerHTML}</body></html>`;
      open(URL.createObjectURL(new Blob([html], { type: 'text/html' })), '_blank');
    }

    async function render() {
      try {
        const code = source.textContent.trim();
        if (!code) { label.textContent = 'Error: empty source'; return; }
        const id = 'diagram-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8);
        const { svg } = await mermaid.render(id, code);
        // Parse as text/html, NOT image/svg+xml: the strict XML parser silently
        // truncates Mermaid's <foreignObject> labels (unclosed <br> etc.).
        const parsed = new DOMParser().parseFromString(svg, 'text/html');
        const parsedSvg = parsed.body.querySelector('svg');
        if (!parsedSvg) { label.textContent = 'Error: no SVG'; return; }
        canvas.replaceChildren(document.adoptNode(parsedSvg));

        const size = readSvgNaturalSize(parsedSvg);
        svgW = size.w; svgH = size.h;
        parsedSvg.removeAttribute('width');
        parsedSvg.removeAttribute('height');
        parsedSvg.style.maxWidth = 'none';
        parsedSvg.style.display = 'block';

        setAdaptiveHeight();
        fitDiagram();
      } catch (err) {
        console.error('Mermaid render failed:', err);
        label.textContent = 'Error: ' + (err.message || 'render failed');
      }
    }

    const actions = {
      'zoom-in':     () => zoomAround(1 + config.zoomStep,       viewport.clientWidth / 2, viewport.clientHeight / 2),
      'zoom-out':    () => zoomAround(1 / (1 + config.zoomStep), viewport.clientWidth / 2, viewport.clientHeight / 2),
      'zoom-fit':    fitDiagram,
      'zoom-one':    setOneToOne,
      'zoom-expand': openInNewTab,
    };
    Object.entries(actions).forEach(([action, handler]) =>
      wrap.querySelector(`[data-action="${action}"]`)?.addEventListener('click', handler));

    viewport.addEventListener('dblclick', fitDiagram);

    viewport.addEventListener('wheel', (e) => {
      if (e.ctrlKey || e.metaKey) {                 // Ctrl/Cmd + wheel → zoom at cursor
        e.preventDefault();
        const rect = viewport.getBoundingClientRect();
        const factor = e.deltaY < 0 ? 1 + config.zoomStep : 1 / (1 + config.zoomStep);
        zoomAround(factor, e.clientX - rect.left, e.clientY - rect.top);
      } else if (canPan()) {                          // bare wheel → pan
        e.preventDefault();
        panX -= e.deltaX; panY -= e.deltaY; applyTransform();
      }
    }, { passive: false });

    viewport.addEventListener('mousedown', (e) => {
      if (e.target.closest('.zoom-controls') || !canPan()) return;
      wrap.classList.add('is-panning');
      sx = e.clientX; sy = e.clientY; spx = panX; spy = panY;
      e.preventDefault();
      activeDrag = {
        onMove: (ev) => { panX = spx + (ev.clientX - sx); panY = spy + (ev.clientY - sy); applyTransform(); },
        onEnd:  ()   => wrap.classList.remove('is-panning'),
      };
    });

    viewport.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) { sx = e.touches[0].clientX; sy = e.touches[0].clientY; spx = panX; spy = panY; }
      else if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        touchDist = Math.hypot(dx, dy);
        const r = viewport.getBoundingClientRect();
        touchCx = (e.touches[0].clientX + e.touches[1].clientX) / 2 - r.left;
        touchCy = (e.touches[0].clientY + e.touches[1].clientY) / 2 - r.top;
      }
    }, { passive: true });

    viewport.addEventListener('touchmove', (e) => {
      if (e.touches.length === 1 && canPan()) {
        if (touchDist > 0) { sx = e.touches[0].clientX; sy = e.touches[0].clientY; spx = panX; spy = panY; touchDist = 0; }
        e.preventDefault();
        panX = spx + (e.touches[0].clientX - sx);
        panY = spy + (e.touches[0].clientY - sy);
        applyTransform();
      } else if (e.touches.length === 2 && touchDist > 0) {
        e.preventDefault();
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const d = Math.hypot(dx, dy);
        zoomAround(d / touchDist, touchCx, touchCy);
        touchDist = d;
      }
    }, { passive: false });

    new ResizeObserver(() => { if (svgW) { setAdaptiveHeight(); fitDiagram(); } }).observe(wrap);
    render();
  }

  document.querySelectorAll('.diagram-shell').forEach(initDiagram);
</script>
```

### Notes and gotchas

- **Parse Mermaid output as `text/html`, never `image/svg+xml`.** Mermaid 10+ emits HTML (`<br>`, unclosed tags) inside `<foreignObject>` labels; the strict XML parser silently truncates labels and edges. `canvas.innerHTML = svg` works but trips security scanners as an HTML sink — adopt the parsed node instead.
- **One `.diagram-shell` per diagram.** The source lives in `<script type="text/plain">`, so IDs never collide and you can drop a dozen on one page.
- **Reserve Mermaid for graphs that need it.** A simple linear flow (A → B → C) renders tiny in a tall container — use CSS step-cards or a native [layer-stack / swimlane](#prioritized-catalog) instead. The shell earns its weight only when automatic edge routing does.
- **8:1 is on you for the diagram body.** The shell's chrome (controls, labels) is wired to clear 8:1, but Mermaid node fills vs. label text come from your brand tokens — `muriel.contrast` can't audit the runtime-injected SVG, so export one render (`mmdc -i diagram.mmd -o diagram.svg`, see [`svg.md`](svg.md)) and audit that flat file to prove the floor.
- **Reduced motion.** The pan/zoom transforms are direct user manipulation (no easing), so they're motion-safe by construction; the only animated property is the button hover, which the `prefers-reduced-motion` block disables.

## Auditing diagrams

Every diagram should pass `muriel diagram-check <file.svg>` (the [accessible SVG contract](#accessible-svg-contract), label geometry, 8:1 contrast) once that subcommand lands; until then, `python -m muriel.contrast <file.svg>`. The included generators write fills inline (not via class selectors), so the audit currently reports zero text rules unless your selectors match marginalia conventions; rasterize via `cairosvg <file.svg> -o <file.png>` and inspect with the [muriel-critique](../../../agents/muriel-critique.md) agent for the visual-judgment pass.

For a rhetorical-fit pass: feed the diagram and the prose claim it accompanies to muriel-critique with the channel set to `diagrams`. The agent will check whether the structure earns its geometry.

## Anti-patterns

- **Reaching for a diagram before naming the claim.** If you can't say in one sentence what the diagram argues, the right diagram is no diagram.
- **Decorating a list with cell borders.** A 1×4 grid of bullet points with a header band is a list; don't market it as a "framework."
- **Cycling a sequence.** If the last step ends the work, draw a sequence with an end-cap; don't loop it back for the symmetry.
- **2×2 with marketing-jargon quadrants.** "Stars / Cash Cows / Dogs / Question Marks" is BCG-specific; lifting the names without the underlying market-share/growth measurement is cargo cult.
- **Mixing diagram types in one figure** without an organizing frame. A cycle next to a 2×2 next to a funnel reads as "I had three slides and combined them"; lay them out as small multiples instead.
