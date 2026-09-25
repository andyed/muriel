"""
muriel.tools.diagrams — rhetorical-primitive diagrams as deterministic SVG.

Each generator embodies a specific argument structure. The docstring on
each function names its **epistemic precondition** — the shape of data /
claim it can honestly carry — and an **anti-prescription** — when reaching
for that structure misleads.

Catalog (MVP):

    matrix(quadrants, *, axes, ...)            → 2×2 categorical decomposition.
    cycle(steps, *, center, ...)               → N-step iterative process (3–8).
    layer_stack(layers, *, focal, ...)         → 4–6 layer dependency stack.
    pyramid(tiers, *, orientation, ...)        → 4–6 tier pyramid / funnel.
    swimlane(lanes, steps, ...)                → cross-functional process
                                                  with per-actor lanes + handoffs.
    comparison_pair(items, *, states, ...)     → one item set under two states:
                                                  slopegraph (numbers) or trace
                                                  pair (status words).
    treemap(cells, *, max_cells, ...)          → 4–8 part squarified
                                                  part-of-whole; area = share.
    dendrogram(tree, *, orientation, ...)      → tidy tree (≤4 levels, ≤5
                                                  children) with elbow-bus
                                                  connectors.
    heat_grid(rows, cols, values, ...)         → rows × columns comparison of an
                                                  unsigned quantity (opacity ramp).
    foveal_overlay(*, verbosity, ...)          → Scrutinizer's UI overlay
                                                  (svg-overlay.js port: fovea
                                                  + parafovea + uniform grid).
    engine_sectors_overlay(*, verbosity, ...)  → Blauch et al. 2026 isotropic
                                                  cortical sectors cobweb
                                                  (the engine's sampling layout).
    sankey(stages, nodes, flows, *, focal, ...) → 2–3 stage conserved
                                                  magnitude flow.

All write self-contained SVG, accept an optional ``StyleGuide``, and
fall back to muriel's OLED palette. Every one writes the accessible-figure
contract (``role="img"``, slug-prefixed ``<title>``/``<desc>`` named by
``aria-labelledby``; see ``_a11y``) and takes ``desc=`` for what the figure
argues. ``muriel diagram-check`` (``check.py``) is the read-back gate:
a11y lint, label geometry, 8:1 contrast. Output is hand-rolled SVG (no
``svgwrite`` dependency) for transparency: the file you ship is the
file the agent wrote.
"""

from muriel.tools.diagrams.matrix import matrix
from muriel.tools.diagrams.cycle import cycle
from muriel.tools.diagrams.layer_stack import layer_stack
from muriel.tools.diagrams.pyramid import pyramid
from muriel.tools.diagrams.swimlane import swimlane
from muriel.tools.diagrams.comparison_pair import comparison_pair
from muriel.tools.diagrams.treemap import treemap
from muriel.tools.diagrams.dendrogram import dendrogram
from muriel.tools.diagrams.heat_grid import heat_grid
from muriel.tools.diagrams.foveal_overlay import foveal_overlay
from muriel.tools.diagrams.engine_sectors_overlay import engine_sectors_overlay
from muriel.tools.diagrams.sankey import sankey

__all__ = [
    "matrix", "cycle", "layer_stack", "pyramid", "swimlane",
    "foveal_overlay", "engine_sectors_overlay",
    "comparison_pair",
    "treemap",
    "dendrogram",
    "heat_grid",
]
__all__ += ["sankey"]
