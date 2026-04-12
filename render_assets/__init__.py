"""
render_assets — importable Python assets for the Render skill.

Four modules, pulled out of the render channel subfiles so notebooks and
CI checks can import them instead of copy-pasting.

  - matplotlibrc_dark  — OLED cream on near-black (default palette)
  - matplotlibrc_light — warm editorial palette (matches F explainer)
  - stats              — APA-style effect size / CI / phrasing helpers
  - contrast           — WCAG contrast audit (module + CLI)

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

Contrast auditing:

    from render_assets.contrast import (
        contrast_ratio, check_text_pair, audit_svg, RENDER_8,
    )
    contrast_ratio("#e6e4d2", "#0a0a0f")     # → 15.42
    audit_svg("examples/word-fingerprints.svg")  # prints an audit table

Or from the command line:

    python -m render_assets.contrast examples/*.svg
    python -m render_assets.contrast file.svg --required 4.5 --background '#fff'

See the module docstrings for the full APIs.
"""

__version__ = "0.1.0"
__all__ = [
    "matplotlibrc_dark",
    "matplotlibrc_light",
    "stats",
    "contrast",
]
