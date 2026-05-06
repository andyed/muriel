"""
Generate the muriel scope Venn diagram and a two-panel channel overlap
demo — reproducing the AF "LAB vs WILD" visual pattern with muriel's
own content, applied through `muriel.tools.venn`.

Run:
    python -m muriel.tools.venn       # (future CLI)
    # or for now:
    python examples/gallery/venn-scope-demo.py
"""

from pathlib import Path

from muriel.tools.venn import venn_single, venn_panels
from muriel.styleguide import load_styleguide


ROOT = Path(__file__).resolve().parent.parent.parent
BRAND = load_styleguide(str(ROOT / "examples" / "muriel-brand.toml"))
OUT = ROOT / "docs"


# ─── Diagram 1: three-circle scope (muriel / marginalia / iblipper) ──

venn_single(
    sets={
        "muriel": 14,         # muriel-only: WCAG audit, dimensions, gaze-viz, stats, contrast CLI,
                              #              heroshot, matplotlibrc, capture, critique agent,
                              #              engine adapters, brand-schema w/ motion, imagegen TODO,
                              #              PERMUTE grammar, terminal charts
        "marginalia": 8,      # marginalia-only: mg-callout taxonomy, pandoc Lua filter,
                              #                  3D perspective pull-quote, mg-spread magazine
                              #                  layout, badge grammar, footnote popovers,
                              #                  marginalia-md.js, light theme
        "iblipper": 6,        # iblipper-only: emotional vocabulary, SDF text pipeline,
                              #                 protest-sign mode, shareable URL state,
                              #                 12-pose animation, web haptics
        "muriel_marginalia": 3,   # shared: typography scale, 8:1 contrast floor, OLED palette
        "muriel_iblipper":   3,   # shared: motion tokens, kinetic typography grammar, brand.toml
        "marginalia_iblipper": 1, # shared: typography-first design
        "all":               2,   # shared by all three: brand-token-driven + reproducible
    },
    labels=["muriel", "marginalia", "iblipper"],
    brand=BRAND,
    title="Overlapping scope — muriel, marginalia, iblipper",
    out_path=str(OUT / "venn-scope.png"),
)
print("wrote docs/venn-scope.png")


# ─── Diagram 2: two-panel channel overlap (AF LAB/WILD pattern) ──────

venn_panels(
    panels=[
        {
            "labels": ["raster", "web", "interactive"],
            "title": "muriel — today",
            "sets": {
                "raster":      7,   # Pillow icons, wordmarks, heroshot, thumbnails, app-store assets, OG cards, charts
                "web":         5,   # marginalia pages, pandoc bridge, weasyprint PDF, data-URI, SVG-in-HTML
                "interactive": 4,   # WebGL demos, D3, PermalinkManager, pretext-coachella
                "raster_web":      2,  # screenshot-as-hero, device-frame capture
                "raster_interactive": 2,  # canvas-captured-as-PNG, single-frame demo pose
                "web_interactive":    3,  # CodePen/Observable embeds, iframe demos, live pretext
                "all":             2,  # exportable viz components, brand-token-driven
            },
        },
        {
            "labels": ["raster", "web", "interactive"],
            "title": "muriel — after imagegen + authoring TODOs land",
            "sets": {
                "raster":      9,   # + LLM imagegen output, enhance/upscale pipeline
                "web":         6,   # + authoring engines emit .fig / Canva designs
                "interactive": 5,   # + authoring engines emit editable canvas state
                "raster_web":      3,   # + exported .psd for web-to-print
                "raster_interactive": 3,   # + interactive preview of imagegen variants
                "web_interactive":    4,   # + shared authoring session ⇄ live demo
                "all":             4,   # + imagegen pipeline emits all three channels from one spec
            },
        },
    ],
    brand=BRAND,
    title="muriel channel overlap — current scope vs. roadmap",
    out_path=str(OUT / "venn-channels-roadmap.png"),
)
print("wrote docs/venn-channels-roadmap.png")
