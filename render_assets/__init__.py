"""
render_assets — importable Python assets for the Render skill.

Two matplotlibrc blocks (dark OLED and warm editorial light) and a
statistical reporting helper module, pulled out of
`~/Documents/dev/render/channels/science.md` so notebooks can import
them instead of copy-pasting.

Usage
-----

Apply a matplotlib palette on import (side-effect):

    from render_assets import matplotlibrc_dark   # OLED cream on near-black
    # or
    from render_assets import matplotlibrc_light  # warm editorial (F explainer)

Or scope a palette to a single figure:

    import matplotlib.pyplot as plt
    from render_assets.matplotlibrc_dark import PARAMS
    with plt.rc_context(PARAMS):
        fig, ax = plt.subplots()
        ax.plot(...)
        fig.savefig('scoped.pdf')

Statistical reporting helpers:

    from render_assets.stats import (
        format_comparison, format_null, format_correlation,
        format_auc, format_chi2, format_exploratory,
        cohens_d, cohens_d_paired, fisher_ci,
        apa_number, format_p, format_ci,
    )

See the module docstrings in `stats.py` for the full API.
"""

__version__ = "0.1.0"
__all__ = [
    "matplotlibrc_dark",
    "matplotlibrc_light",
    "stats",
]
