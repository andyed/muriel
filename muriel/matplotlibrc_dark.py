"""
muriel.matplotlibrc_dark — OLED dark palette for matplotlib.

Drop-in matplotlib configuration matching muriel's universal rules:
- 8:1 contrast text (cream `#e6e4d2` on near-black `#0a0a0f`)
- Large default figsize (10×6) — paper-figure-ready
- Helvetica/sans-serif stack with Regular weight minimum (no Light at
  small sizes — that rule exists because of an actual bug)
- Horizontal grid only, top/right spines off
- Thick lines (2.0) so PDF re-renders survive downstream re-scaling

Usage
-----
Auto-apply on import (side-effect — affects global rcParams):

    from muriel import matplotlibrc_dark   # noqa: F401

Manual control:

    from muriel.matplotlibrc_dark import apply, PARAMS
    apply()                                 # update rcParams globally

Scoped to a single figure:

    import matplotlib.pyplot as plt
    from muriel.matplotlibrc_dark import PARAMS
    with plt.rc_context(PARAMS):
        fig, ax = plt.subplots()
        # ...

See `channels/science.md` in the muriel repo for the rationale behind
each setting.
"""

from __future__ import annotations

PARAMS: dict = {
    # ── figure sizing ──────────────────────────────────────────────────
    "figure.figsize":      (10, 6),
    "figure.dpi":           120,
    "savefig.dpi":          300,
    "savefig.bbox":        "tight",
    "savefig.transparent":  False,

    # ── typography ─────────────────────────────────────────────────────
    "font.family":         "sans-serif",
    "font.sans-serif":     ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size":            14,
    "axes.titlesize":       16,
    "axes.labelsize":       14,
    "xtick.labelsize":      12,
    "ytick.labelsize":      12,
    "legend.fontsize":      12,
    "figure.titlesize":     18,
    "font.weight":         "regular",  # Light at small sizes fails legibility

    # ── palette (cream on near-black; matches muriel universal OLED) ──
    "figure.facecolor":    "#0a0a0f",
    "axes.facecolor":      "#0a0a0f",
    "savefig.facecolor":   "#0a0a0f",
    "axes.edgecolor":      "#e6e4d2",
    "axes.labelcolor":     "#e6e4d2",
    "xtick.color":         "#e6e4d2",
    "ytick.color":         "#e6e4d2",
    "text.color":          "#e6e4d2",
    "grid.color":          "#3a3a4a",  # decorative ≥55/255 on dark bg
    "grid.linewidth":       0.6,
    "grid.alpha":           1.0,       # set color directly; alpha fails on PDF

    # ── axes ───────────────────────────────────────────────────────────
    "axes.linewidth":       1.2,
    "axes.grid":            True,
    "axes.grid.axis":      "y",        # horizontal grid only
    "axes.axisbelow":       True,
    "axes.spines.top":      False,
    "axes.spines.right":    False,

    # ── ticks ──────────────────────────────────────────────────────────
    "xtick.direction":     "out",
    "ytick.direction":     "out",
    "xtick.major.size":     5,
    "ytick.major.size":     5,
    "xtick.major.width":    1.2,
    "ytick.major.width":    1.2,

    # ── lines and markers ──────────────────────────────────────────────
    "lines.linewidth":      2.0,
    "lines.markersize":     7,
    "patch.linewidth":      1.0,

    # ── legend ─────────────────────────────────────────────────────────
    "legend.frameon":       True,
    "legend.framealpha":    0.9,
    "legend.edgecolor":    "#3a3a4a",
    "legend.facecolor":    "#0f1117",
}


def apply() -> None:
    """Update matplotlib's global rcParams with the dark OLED PARAMS."""
    import matplotlib as mpl
    mpl.rcParams.update(PARAMS)


# Auto-apply on bare `import muriel.matplotlibrc_dark`.
# Degrade gracefully if matplotlib is not installed — PARAMS is still
# importable as a plain dict, and apply() will raise informatively on
# explicit call.
try:
    apply()
except ImportError:
    pass
