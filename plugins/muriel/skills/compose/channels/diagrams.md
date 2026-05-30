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

## Prioritized catalog

Ordered by how often each structure carries a real argument in research, product, and editorial work. **Bold** is shipped today; the rest are queued in [`TODO.md`](../TODO.md).

| # | Structure | What it argues | Status |
|---|---|---|---|
| 1 | **2×2 matrix** | Two **independent** binary axes divide a population into four meaningful classes. | **Shipped** — `muriel.tools.diagrams.matrix` |
| 2 | **Cycle (3–8 step)** | Iterative process with no exit; each step feeds the next. | **Shipped** — `muriel.tools.diagrams.cycle` |
| 3 | Comparison pair | Same axes, one variable changed — the smallest Tufte small-multiple. | Queued |
| 4 | Phase / funnel | Sequential narrowing; later phases are subsets of earlier. | **Shipped** — `muriel.tools.diagrams.pyramid` (`orientation="down"`) |
| 5 | Layered stack | Higher layers depend on / abstract over lower; reading direction encodes hierarchy. | **Shipped** — `muriel.tools.diagrams.layer_stack` |
| 6 | Causal DAG | What causes what; arrow direction is load-bearing. | Queued |
| 7 | Venn / Euler | Categorical intersection; area-proportional. | **Shipped** — `muriel.tools.venn` |
| 8 | Spectrum | Position between two poles is the encoding. | Queued |
| 9 | Pyramid | Each level depends on the one below; apex is rare or important. | **Shipped** — `muriel.tools.diagrams.pyramid` (`orientation="up"`) |
| 10 | Comparison heat-grid | Dense `n × m` comparison; small multiples for categorical evals. | Queued |
| 11 | Swimlane | Cross-functional process; the handoffs between actors are the point. | **Shipped** — `muriel.tools.diagrams.swimlane` |

**Explicitly excluded.** Process arrows, list-with-chevrons, interconnected blocks, radial gear cosmetics, target-with-concentric-rings as decoration. If a SmartArt category exists only to ornament a list, this channel will never ship it.

## This channel is not the only path

Several diagram forms have an existing home elsewhere in muriel. The native generators here are the **static, brand-locked, print-ready** option — the right pick for a paper figure or editorial SVG that must clear the 8:1 floor with no JS runtime. They are deliberately *not* the exclusive provider. Before reaching for one, check whether an existing substrate already serves the form better:

| Form | Native generator | Existing alternative — and when to prefer it |
|---|---|---|
| 2×2, cycle, layer-stack, pyramid/funnel, swimlane, Venn | **this channel** | — (no cleaner substrate; these are the primitives) |
| Sequence / interaction | — | **Mermaid** `sequenceDiagram` via `mmdc` ([`svg.md`](svg.md)). Prefer Mermaid; only port to native SVG if a paper figure forbids the Mermaid aesthetic. |
| State machine | — | **Mermaid** `stateDiagram-v2`. Same call. |
| ER / data model | — | **Mermaid** `erDiagram`. Same call. |
| Flowchart / generic DAG | — | **Mermaid** `flowchart` today; native **causal DAG** is queued (catalog #6) for when arrow-direction is the load-bearing claim. |
| Timeline | — | **ECharts** time-axis + band overlays ([`echarts.md`](../vocabularies/echarts.md)), the `svg.md` OSEC phase diagram, or the infographics **Timeline** template ([`infographics.md`](infographics.md)). All predate this channel. |
| Single-actor process flow | swimlane (degenerate) | infographics **Process** template — lighter when there are no lanes. Use swimlane only when ownership/handoffs are the argument. |
| Tree / org-chart | — | **ECharts** `tree` series (interactive) or the infographics **Hierarchical** template. |
| Nested hierarchy (proportional) | — | Queued **hierarchy family** — sunburst / treemap / dendrogram (see [`TODO.md`](../TODO.md) #45), ECharts-backed. |
| Magnitude flow | — | Queued **Sankey** primitive ([`TODO.md`](../TODO.md) #44). |

Rule of thumb: **Mermaid** for node-link relational diagrams (sequence, state, ER, flowchart), **ECharts** when the diagram is data-driven or interactive (timeline, tree, treemap, sunburst), and **this channel** when the output is a static editorial SVG whose geometry encodes a specific rhetorical claim.

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

**Tiers** is 4–6 entries in reading order, top to bottom, each a string or a dict `{"label", "sublabel", "annotation", "value", "focal"}`. `orientation="up"` draws a pyramid (apex on top, narrow = rare/valuable); `"down"` draws a funnel (apex at bottom, narrow = converted). With `proportional=True` and a `value` on every tier, each tier becomes a centred bar whose width is proportional to its value — an **honest** funnel; otherwise tiers taper linearly, which says "narrowing" without faking a measurement. `focal` defaults to the apex (top tier for a pyramid, conversion tier for a funnel); pass `focal=-1` to highlight nothing.

**Anti-prescriptions:**

- Don't use a pyramid for non-hierarchical data — if tiers don't rest on each other, width encodes nothing and you've drawn a decorative triangle. Use a bar chart.
- Don't fake funnel widths. If they aren't proportional to the counts, the reader sees a drop-off that isn't there — pass real `value`s or say in the caption that the taper is ordinal.
- Don't highlight the base. Coral on the broad base dilutes the "apex = rare" signal.

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

## Design discipline

The generators bake in the editorial-diagram discipline that keeps SVG from reading as AI-generated SmartArt:

- **4px-increment alignment.** All band heights, margins, and offsets land on a 4px grid (`band_h = 64`, `tier_h = 64`, paddings of 48). Off-grid drift is the tell.
- **1px hairline dividers, no fills competing with content.** Non-focal bands use a near-invisible `paper` wash (`rgba(ink, 0.04)`); structure is carried by hairline strokes, not boxes.
- **No shadows, no gradients, no glow.** Nothing in `<defs>` but the arrow marker. Depth is implied by order, not by drop-shadows.
- **One accent, one focal element.** A single layer/tier gets the accent stroke + tint. Two highlights is no highlight.

This is a *philosophy* import, not a brand import: the tokens stay muriel's own (OLED palette, `StyleGuide` fonts) and text clears the **8:1** contrast rule — stricter than the source's WCAG AA. We did **not** adopt the source's typefaces or colour system.

> **Attribution.** The layout proportions for `layer_stack`, `pyramid`, and `swimlane` (band/tier/lane heights, taper rules, lane dividers + handoff emphasis, label placement, the focal-accent convention) are adapted from the MIT-licensed [`diagram-design`](https://github.com/cathrynlavery/diagram-design) skill, © 2025 Cathryn Lavery. muriel's contribution is the deterministic Python generators, the epistemic-precondition / anti-prescription gate on each, the 8:1 contrast floor, and brand-token integration. See [`THIRD_PARTY_NOTICES.md`](../../../../../THIRD_PARTY_NOTICES.md) for the full license.

## Worked examples

Both examples below render to `examples/diagrams/`:

- [`cycle-evolver.svg`](../examples/diagrams/cycle-evolver.svg) — a 5-step iteration loop with a centre label; honest re-rendering of the AI-generated reference image whose text was visibly mangled.
- [`matrix-sat-opt.svg`](../examples/diagrams/matrix-sat-opt.svg) — sat/opt × LF/HF, the orthogonality finding from ETTAC 2026. The matrix-shape claim is testable: if the axes were correlated, the diagonal cells would dominate; here the off-diagonal cells (`OPTIMIZER + LOAD`, `SATISFICER + LOAD`) carry distinct content, which is the data justification for a 2×2 over a 1D scatter.
- [`layers-tcpip.svg`](../examples/diagrams/layers-tcpip.svg) — a 4-layer dependency stack with the Transport layer as the focal band and an "abstraction ↑" axis; the stack shape is honest because each layer genuinely depends on the one below.
- [`funnel-q2.svg`](../examples/diagrams/funnel-q2.svg) — a proportional acquisition funnel; tier widths are driven by real counts (`proportional=True`), so the visual drop-off matches the `−%` annotations rather than faking a taper.
- [`swimlane-release.svg`](../examples/diagrams/swimlane-release.svg) — a 4-lane release pipeline; same-lane steps connect with a muted arrow, cross-lane handoffs are drawn in the accent because the handoffs are the claim.

## Auditing diagrams

Every diagram should pass `python -m muriel.contrast <file.svg>`. The included generators write fills inline (not via class selectors), so the audit currently reports zero text rules unless your selectors match marginalia conventions; rasterize via `cairosvg <file.svg> -o <file.png>` and inspect with the [muriel-critique](../../../agents/muriel-critique.md) agent for the visual-judgment pass.

For a rhetorical-fit pass: feed the diagram and the prose claim it accompanies to muriel-critique with the channel set to `diagrams`. The agent will check whether the structure earns its geometry.

## Anti-patterns

- **Reaching for a diagram before naming the claim.** If you can't say in one sentence what the diagram argues, the right diagram is no diagram.
- **Decorating a list with cell borders.** A 1×4 grid of bullet points with a header band is a list; don't market it as a "framework."
- **Cycling a sequence.** If the last step ends the work, draw a sequence with an end-cap; don't loop it back for the symmetry.
- **2×2 with marketing-jargon quadrants.** "Stars / Cash Cows / Dogs / Question Marks" is BCG-specific; lifting the names without the underlying market-share/growth measurement is cargo cult.
- **Mixing diagram types in one figure** without an organizing frame. A cycle next to a 2×2 next to a funnel reads as "I had three slides and combined them"; lay them out as small multiples instead.
