#!/usr/bin/env python3
"""Regenerate Muriel's three wavefield proof artifacts."""

from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))

from muriel.layout import BBox  # noqa: E402
from muriel.patterns import wavefield  # noqa: E402


def write(name: str, svg: str) -> None:
    (HERE / name).write_text(svg, encoding="utf-8")


def main() -> None:
    divider = wavefield(
        BBox(0, 0, 1200, 240),
        layers=3,
        samples=18,
        amplitude=24,
        cycles=1.35,
        roughness=0.18,
        seed=23,
    )
    write(
        "decorative-divider.svg",
        divider.svg(
            fill_colors=("#12323b", "#1d6878", "#7fdfff"),
            stroke="#e6e4d2",
            stroke_width=1,
            title="Generated wave divider",
            desc=(
                "Three seeded harmonic contours used only as an editorial "
                "section boundary; seed 23."
            ),
        ),
    )

    signal = wavefield(
        BBox(0, 0, 1200, 420),
        series=((
            -0.72, -0.40, 0.04, 0.36, 0.68, 0.91, 0.62, 0.18,
            -0.16, -0.44, -0.20, 0.21, 0.55, 0.38, 0.06, -0.31,
        ),),
        amplitude=110,
        smoothness=0.72,
    )
    write(
        "semantic-signal.svg",
        signal.svg(
            fill_colors=("#1d6878",),
            stroke="#7fdfff",
            stroke_width=3,
            title="Illustrative normalized signal band",
            desc=(
                "One caller-supplied normalized series. Positive values rise "
                "above the baseline; illustrative data, not a measurement."
            ),
        ),
    )

    uncertainty = wavefield(
        BBox(0, 0, 1200, 620),
        series=(
            (-0.68, -0.42, -0.08, 0.24, 0.48, 0.72, 0.60, 0.34, 0.08, -0.18),
            (-0.45, -0.18, 0.16, 0.50, 0.70, 0.52, 0.28, 0.04, -0.20, -0.38),
            (-0.20, 0.08, 0.42, 0.74, 0.54, 0.24, -0.02, -0.28, -0.46, -0.26),
            (0.04, 0.34, 0.68, 0.50, 0.18, -0.10, -0.34, -0.54, -0.28, 0.02),
            (0.28, 0.60, 0.42, 0.12, -0.18, -0.42, -0.60, -0.32, 0.00, 0.30),
        ),
        amplitude=38,
        smoothness=0.82,
    )
    write(
        "uncertainty-slices.svg",
        uncertainty.svg(
            fill_colors=("#102a32", "#123943", "#164b58", "#1b6170", "#287f8f"),
            stroke="#7fdfff",
            stroke_width=1.5,
            title="Illustrative uncertainty slices",
            desc=(
                "Five caller-supplied normalized scenario slices sharing one "
                "scale; illustrative data, not a statistical confidence interval."
            ),
        ),
    )


if __name__ == "__main__":
    main()
