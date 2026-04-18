"""
muriel — multi-channel visual production toolkit, Python side.

Seven modules, pulled out of the channel subfiles so notebooks and CI
checks can import them instead of copy-pasting.

  - matplotlibrc_dark  — OLED cream on near-black (default palette)
  - matplotlibrc_light — warm editorial palette (matches F explainer)
  - stats              — APA-style effect size / CI / phrasing helpers
  - contrast           — WCAG contrast audit (module + CLI)
  - dimensions         — common screen-size footprints (Size / Device /
                         PaperSize, social cards, video, viewports,
                         academic figsize helper, dotted-name registry)
  - capture            — Playwright viewport-sweep screenshot helper
                         (module + CLI, optional Playwright dependency)
  - styleguide         — brand style guide schema and TOML loader with
                         rule enforcement, contrast auditing, CSS +
                         matplotlibrc derivation (module + CLI)

Usage
-----

Apply a matplotlib palette on import (side-effect):

    from muriel import matplotlibrc_dark   # OLED cream on near-black
    # or
    from muriel import matplotlibrc_light  # warm editorial (F explainer)

Or scope a palette to a single figure:

    import matplotlib.pyplot as plt
    from muriel.matplotlibrc_dark import PARAMS
    with plt.rc_context(PARAMS):
        fig, ax = plt.subplots()
        ax.plot(...)
        fig.savefig('scoped.pdf')

Statistical reporting helpers:

    from muriel.stats import (
        format_comparison, format_null, format_correlation,
        format_auc, format_chi2, format_exploratory,
        cohens_d, cohens_d_paired, fisher_ci,
        apa_number, format_p, format_ci,
    )

Contrast auditing:

    from muriel.contrast import (
        contrast_ratio, check_text_pair, audit_svg, RENDER_8,
    )
    contrast_ratio("#e6e4d2", "#0a0a0f")     # → 15.42
    audit_svg("examples/example-palette.svg")  # prints an audit table

Or from the command line:

    python -m muriel.contrast examples/*.svg
    python -m muriel.contrast file.svg --required 4.5 --background '#fff'

Dimension lookups and academic figsize helpers:

    from muriel.dimensions import (
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

    python -m muriel.dimensions

Responsive viewport-sweep screenshot capture:

    from muriel.capture import capture_responsive
    paths = capture_responsive(
        url="https://example.com/",
        output_dir="captures/",
    )
    # → four PNGs named by slug + tier + dimensions

Or from the command line:

    python -m muriel.capture https://example.com
    python -m muriel.capture https://example.com --tiers mobile tablet laptop desktop
    python -m muriel.capture https://example.com --dir captures/ --dark --selector main

Requires Playwright (optional install). Module imports cleanly without
it; capture_responsive() raises ImportError with install instructions
on first call.

Brand style guides:

    from muriel.styleguide import load_styleguide, RuleViolation

    sg = load_styleguide("examples/example-brand.toml")
    sg.colors.accent                  # → '#d2b06a'
    sg.audit_contrast(required=8.0)   # → per-role WCAG audit
    sg.to_matplotlibrc()              # → dict for mpl.rcParams.update()
    sg.to_css_vars(prefix="--brand-") # → :root custom-property block
    sg.rules.check("regenerate-wordmark")  # → raises RuleViolation

Or from the command line:

    python -m muriel.styleguide examples/example-brand.toml
    python -m muriel.styleguide brand.toml --css --css-prefix '--mg-'
    python -m muriel.styleguide brand.toml --contrast --required 8.0

See the module docstrings for the full APIs.
"""

__version__ = "0.5.0"
__all__ = [
    "matplotlibrc_dark",
    "matplotlibrc_light",
    "stats",
    "contrast",
    "dimensions",
    "capture",
    "styleguide",
]
