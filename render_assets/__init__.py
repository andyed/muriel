"""
render_assets — importable Python assets for the Render skill.

Five modules, pulled out of the render channel subfiles so notebooks and
CI checks can import them instead of copy-pasting.

  - matplotlibrc_dark  — OLED cream on near-black (default palette)
  - matplotlibrc_light — warm editorial palette (matches F explainer)
  - stats              — APA-style effect size / CI / phrasing helpers
  - contrast           — WCAG contrast audit (module + CLI)
  - dimensions         — common screen-size footprints (Size / Device /
                         PaperSize, social cards, video, viewports,
                         academic figsize helper, dotted-name registry)

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

Dimension lookups and academic figsize helpers:

    from render_assets.dimensions import (
        TWITTER_INSTREAM, OG_CARD, VIDEO_1080P, A4,
        figsize_for, lookup, device, Size,
    )
    TWITTER_INSTREAM               # → Size(1600, 900)
    OG_CARD.aspect_label           # → '1.91:1'
    OG_CARD.scale(2)               # → Size(2400, 1260)  (retina upload)
    A4.px_300dpi                   # → Size(2481, 3507)
    figsize_for('chi', columns=1)  # → (3.33, 2.0)
    device('iphone-15-pro').css    # → Size(393, 852)
    lookup('twitter.instream')     # → Size(1600, 900)

Or from the command line (prints the full registry + devices + paper):

    python -m render_assets.dimensions

See the module docstrings for the full APIs.
"""

__version__ = "0.2.0"
__all__ = [
    "matplotlibrc_dark",
    "matplotlibrc_light",
    "stats",
    "contrast",
    "dimensions",
]
