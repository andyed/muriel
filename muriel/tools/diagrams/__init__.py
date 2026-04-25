"""
muriel.tools.diagrams — rhetorical-primitive diagrams as deterministic SVG.

Each generator embodies a specific argument structure. The docstring on
each function names its **epistemic precondition** — the shape of data /
claim it can honestly carry — and an **anti-prescription** — when reaching
for that structure misleads.

Catalog (MVP):

    matrix(quadrants, *, axes, ...)            → 2×2 categorical decomposition.
    cycle(steps, *, center, ...)               → N-step iterative process (3–8).
    foveal_overlay(*, verbosity, ...)          → Scrutinizer's UI overlay
                                                  (svg-overlay.js port: fovea
                                                  + parafovea + uniform grid).
    engine_sectors_overlay(*, verbosity, ...)  → Blauch et al. 2026 isotropic
                                                  cortical sectors cobweb
                                                  (the engine's sampling layout).

All write self-contained SVG, accept an optional ``StyleGuide``, and
fall back to muriel's OLED palette. Output is hand-rolled SVG (no
``svgwrite`` dependency) for transparency: the file you ship is the
file the agent wrote.
"""

from muriel.tools.diagrams.matrix import matrix
from muriel.tools.diagrams.cycle import cycle
from muriel.tools.diagrams.foveal_overlay import foveal_overlay
from muriel.tools.diagrams.engine_sectors_overlay import engine_sectors_overlay

__all__ = ["matrix", "cycle", "foveal_overlay", "engine_sectors_overlay"]
