"""Focused tests for Muriel's deterministic SVG pattern primitives."""

import math

import pytest

from muriel.layout import BBox
from muriel.patterns import PatternError, WaveField, wavefield


CANVAS = BBox(0, 0, 640, 360)


def test_wavefield_generated_mode_is_seeded_and_inspectable():
    first = wavefield(CANVAS, layers=4, samples=15, seed=23)
    again = wavefield(CANVAS, layers=4, samples=15, seed=23)
    other = wavefield(CANVAS, layers=4, samples=15, seed=24)

    assert isinstance(first, WaveField)
    assert first == again
    assert first != other
    assert first.source == "generated"
    assert len(first.layers) == 4
    assert all(len(layer.points) == 15 for layer in first.layers)
    assert all(layer.curve_d.startswith("M ") for layer in first.layers)
    assert all(layer.area_d.endswith(" Z") for layer in first.layers)


def test_wavefield_series_mode_preserves_normalized_values_and_scale():
    field = wavefield(
        CANVAS,
        series=((-1.0, -0.5, 0.0, 0.5, 1.0),),
        amplitude=60,
        smoothness=0.5,
    )
    layer = field.layers[0]

    assert field.source == "series"
    assert layer.values == (-1.0, -0.5, 0.0, 0.5, 1.0)
    assert math.isclose(layer.points[0][1], layer.baseline_y + 60)
    assert math.isclose(layer.points[2][1], layer.baseline_y)
    assert math.isclose(layer.points[-1][1], layer.baseline_y - 60)
    assert layer.points[0][0] == CANVAS.x0
    assert layer.points[-1][0] == CANVAS.x1


def test_wavefield_svg_is_accessible_viewbox_first_and_themeable():
    svg = wavefield(CANVAS, layers=2, seed=3).svg(
        title="Signal & uncertainty",
        desc="Two normalized bands.",
    )

    assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg" role="img"')
    assert 'viewBox="0 0 640 360"' in svg
    assert "<title>Signal &amp; uncertainty</title>" in svg
    assert "<desc>Two normalized bands.</desc>" in svg
    assert "var(--mg-bg, #0a0a14)" in svg
    assert "var(--mg-accent, #7fdfff)" in svg
    assert svg.count('data-source="generated"') == 2


def test_wavefield_line_art_uses_open_paths_without_fill():
    field = wavefield(CANVAS, layers=3, seed=8)
    svg = field.svg(bg=None, fill_colors=(), stroke_width=2)

    assert "<rect" not in svg
    assert svg.count('fill="none"') == 3
    for layer in field.layers:
        assert f'd="{layer.curve_d}"' in svg
        assert layer.area_d not in svg


@pytest.mark.parametrize(
    "build",
    [
        lambda: wavefield(CANVAS, layers=0),
        lambda: wavefield(CANVAS, samples=3),
        lambda: wavefield(CANVAS, cycles=0),
        lambda: wavefield(CANVAS, roughness=-0.01),
        lambda: wavefield(CANVAS, smoothness=1.01),
        lambda: wavefield(CANVAS, margin=0.45),
        lambda: wavefield(CANVAS, amplitude=500),
        lambda: wavefield(CANVAS, series=()),
        lambda: wavefield(CANVAS, series=((0.0,),)),
        lambda: wavefield(CANVAS, series=((0.0, float("nan")),)),
        lambda: wavefield(CANVAS, series=((-1.1, 0.0),)),
        lambda: wavefield(CANVAS, layers=2, series=((0.0, 1.0),)),
    ],
)
def test_wavefield_rejects_ambiguous_or_invalid_geometry(build):
    with pytest.raises(PatternError):
        build()


def test_wavefield_svg_rejects_invalid_render_parameters():
    field = wavefield(CANVAS, layers=2)

    with pytest.raises(PatternError):
        field.svg(fill_opacity=1.1)
    with pytest.raises(PatternError):
        field.svg(stroke_width=-1)
