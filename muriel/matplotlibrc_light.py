"""
muriel.matplotlibrc_light — warm editorial light palette for matplotlib.

Light-mode matplotlib configuration for blog explainers, paper drafts,
and reading-edition pages that want a warm editorial voice — not a
clinical journal-white look.

Key palette values:
    background   #fafaf8   (warm cream, not pure white)
    body         #222222   (near-black, not true black)
    accent       #d4a574   (amber — margin note borders, legend edge)
    legend bg    #fdf8f2   (warm cream callout)
    grid         #dddddd   (muted gray, neutral)

Font stack is Georgia serif by default — reading-edition voice. Override
to sans-serif if the target is a blog with a sans body:

    from muriel.matplotlibrc_light import PARAMS, apply
    PARAMS["font.family"] = "sans-serif"
    apply()

For journal submissions requiring pure-white backgrounds, override the
cream values:

    PARAMS.update({
        "figure.facecolor":  "white",
        "axes.facecolor":    "white",
        "savefig.facecolor": "white",
        "grid.color":        "#cccccc",
    })
    apply()

Usage
-----
Auto-apply on import:

    from muriel import matplotlibrc_light   # noqa: F401

Scoped:

    import matplotlib.pyplot as plt
    from muriel.matplotlibrc_light import PARAMS
    with plt.rc_context(PARAMS):
        fig, ax = plt.subplots()
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
    "font.family":         "serif",
    "font.serif":          ["Georgia", "Times New Roman", "DejaVu Serif"],
    "font.size":            14,
    "axes.titlesize":       16,
    "axes.labelsize":       14,
    "xtick.labelsize":      12,
    "ytick.labelsize":      12,
    "legend.fontsize":      12,
    "figure.titlesize":     18,
    "font.weight":         "regular",

    # ── palette (warm editorial; matches F explainer) ─────────────────
    "figure.facecolor":    "#fafaf8",
    "axes.facecolor":      "#fafaf8",
    "savefig.facecolor":   "#fafaf8",
    "axes.edgecolor":      "#222222",
    "axes.labelcolor":     "#222222",
    "xtick.color":         "#222222",
    "ytick.color":         "#222222",
    "text.color":          "#222222",
    "grid.color":          "#dddddd",
    "grid.linewidth":       0.6,
    "grid.alpha":           1.0,

    # ── axes ───────────────────────────────────────────────────────────
    "axes.linewidth":       1.2,
    "axes.grid":            True,
    "axes.grid.axis":      "y",
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

    # ── legend (amber accent matching F explainer margin notes) ───────
    "legend.frameon":       True,
    "legend.framealpha":    0.9,
    "legend.edgecolor":    "#d4a574",
    "legend.facecolor":    "#fdf8f2",
}


def apply() -> None:
    """Update matplotlib's global rcParams with the warm editorial PARAMS."""
    import matplotlib as mpl
    mpl.rcParams.update(PARAMS)


# Auto-apply; degrade gracefully if matplotlib is not installed.
try:
    apply()
except ImportError:
    pass
