"""
muriel.tools.diagrams — rhetorical-primitive diagrams as deterministic SVG.

Each generator embodies a specific argument structure. The docstring on
each function names its **epistemic precondition** — the shape of data /
claim it can honestly carry — and an **anti-prescription** — when reaching
for that structure misleads.

Catalog (MVP):

    matrix(quadrants, *, axes, ...) → 2×2 categorical decomposition.
    cycle(steps, *, center, ...)    → N-step iterative process (3–8).

Both write self-contained SVG, accept an optional ``StyleGuide``, and
fall back to muriel's OLED palette. Output is hand-rolled SVG (no
``svgwrite`` dependency) for transparency: the file you ship is the
file the agent wrote.
"""

from muriel.tools.diagrams.matrix import matrix
from muriel.tools.diagrams.cycle import cycle

__all__ = ["matrix", "cycle"]
