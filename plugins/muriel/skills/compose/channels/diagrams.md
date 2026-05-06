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
| 4 | Phase / funnel | Sequential narrowing; later phases are subsets of earlier. | Queued |
| 5 | Layered stack | Higher layers depend on / abstract over lower; reading direction encodes hierarchy. | Queued |
| 6 | Causal DAG | What causes what; arrow direction is load-bearing. | Queued |
| 7 | Venn / Euler | Categorical intersection; area-proportional. | **Shipped** — `muriel.tools.venn` |
| 8 | Spectrum | Position between two poles is the encoding. | Queued |
| 9 | Pyramid | Each level depends on the one below; apex is rare or important. | Queued |
| 10 | Comparison heat-grid | Dense `n × m` comparison; small multiples for categorical evals. | Queued |

**Explicitly excluded.** Process arrows, list-with-chevrons, interconnected blocks, radial gear cosmetics, target-with-concentric-rings as decoration. If a SmartArt category exists only to ornament a list, this channel will never ship it.

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

## Worked examples

Both examples below render to `examples/diagrams/`:

- [`cycle-evolver.svg`](../examples/diagrams/cycle-evolver.svg) — a 5-step iteration loop with a centre label; honest re-rendering of the AI-generated reference image whose text was visibly mangled.
- [`matrix-sat-opt.svg`](../examples/diagrams/matrix-sat-opt.svg) — sat/opt × LF/HF, the orthogonality finding from ETTAC 2026. The matrix-shape claim is testable: if the axes were correlated, the diagonal cells would dominate; here the off-diagonal cells (`OPTIMIZER + LOAD`, `SATISFICER + LOAD`) carry distinct content, which is the data justification for a 2×2 over a 1D scatter.

## Auditing diagrams

Every diagram should pass `python -m muriel.contrast <file.svg>`. The included generators write fills inline (not via class selectors), so the audit currently reports zero text rules unless your selectors match marginalia conventions; rasterize via `cairosvg <file.svg> -o <file.png>` and inspect with the [muriel-critique](../../../agents/muriel-critique.md) agent for the visual-judgment pass.

For a rhetorical-fit pass: feed the diagram and the prose claim it accompanies to muriel-critique with the channel set to `diagrams`. The agent will check whether the structure earns its geometry.

## Anti-patterns

- **Reaching for a diagram before naming the claim.** If you can't say in one sentence what the diagram argues, the right diagram is no diagram.
- **Decorating a list with cell borders.** A 1×4 grid of bullet points with a header band is a list; don't market it as a "framework."
- **Cycling a sequence.** If the last step ends the work, draw a sequence with an end-cap; don't loop it back for the symmetry.
- **2×2 with marketing-jargon quadrants.** "Stars / Cash Cows / Dogs / Question Marks" is BCG-specific; lifting the names without the underlying market-share/growth measurement is cargo cult.
- **Mixing diagram types in one figure** without an organizing frame. A cycle next to a 2×2 next to a funnel reads as "I had three slides and combined them"; lay them out as small multiples instead.
