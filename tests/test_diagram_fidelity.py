"""Proportional encodings must be proportional.

A funnel drawn with ``proportional=True`` claims its bar widths are the
counts. The check reads the rendered SVG back and compares each tier's
width ratio to the widest tier against its value ratio, as **relative**
error: a 2-pixel slip is noise on the widest bar and a large share of the
narrowest, so an absolute tolerance would pass exactly the bar most likely
to be wrong. The 8% bound and the relative-error framing are adapted from
the MIT-licensed diagram-design skill (© 2025 Cathryn Lavery),
``scripts/verify-treemap.py``.
"""

import re
from pathlib import Path

import pytest

from muriel.tools.diagrams._labels import verify_svg_labels
from muriel.tools.diagrams.pyramid import pyramid

REL_TOL = 0.08
EXAMPLE = (Path(__file__).resolve().parents[1]
           / "plugins/muriel/skills/compose/examples/diagrams/funnel-q2.svg")


def _tier_widths(svg: str) -> list[float]:
    widths = []
    for pts in re.findall(r'<polygon points="([^"]+)"', svg):
        xs = [float(v) for v in pts.replace(",", " ").split()[0::2]]
        widths.append(max(xs) - min(xs))
    return widths


def _assert_proportional(widths, values):
    assert len(widths) == len(values)
    w0, v0 = max(widths), max(values)
    for w, v in zip(widths, values):
        want = v / v0
        got = w / w0
        rel = abs(got - want) / want
        assert rel <= REL_TOL, (
            f"value ratio {want:.3f} drawn at width ratio {got:.3f} "
            f"({rel:.1%} relative error, bound {REL_TOL:.0%})"
        )


def _funnel(tmp_path, values, name="f.svg", **kw):
    tiers = [{"label": f"Tier {i}", "value": v} for i, v in enumerate(values)]
    return Path(pyramid(tiers, orientation="down", proportional=True,
                        out_path=tmp_path / name, **kw)).read_text("utf-8")


def test_committed_funnel_example_is_proportional():
    _assert_proportional(_tier_widths(EXAMPLE.read_text("utf-8")),
                         [100000, 24000, 9000, 2083])


@pytest.mark.parametrize("values", [
    [100000, 24000, 9000, 2100],      # the case that shipped at 1/.43/.32/.27
    [100, 90, 80, 70],
    [5000, 50, 5, 1],                  # a sliver: far narrower than its label
    [10, 10, 10, 10, 10, 10],
])
def test_proportional_widths_track_values(tmp_path, values):
    _assert_proportional(_tier_widths(_funnel(tmp_path, values)), values)


def test_narrow_tiers_move_their_label_outside_rather_than_widening(tmp_path):
    svg = _funnel(tmp_path, [5000, 50, 5, 1], title="Sliver",
                  axis_label="drop-off")
    # the label for a 1-in-5000 tier cannot fit inside a sub-pixel bar
    assert re.search(r'text-anchor="end">Tier 3</text>', svg)
    report = verify_svg_labels(svg)
    assert report.ok, report.summary()


def test_labels_that_fit_stay_centred(tmp_path):
    svg = _funnel(tmp_path, [100, 90, 80, 70])
    assert 'text-anchor="end"' not in svg


def test_ordinal_taper_is_unchanged(tmp_path):
    """Non-proportional mode still tapers linearly from 160 to 640 px."""
    svg = Path(pyramid(["A", "B", "C", "D"], out_path=tmp_path / "p.svg")
               ).read_text("utf-8")
    polys = re.findall(r'<polygon points="([^"]+)"', svg)
    tops, bots = [], []
    for pts in polys:
        xs = [float(v) for v in pts.replace(",", " ").split()[0::2]]
        tops.append(xs[1] - xs[0])
        bots.append(xs[2] - xs[3])
    assert tops == pytest.approx([160, 280, 400, 520])
    assert bots == pytest.approx([280, 400, 520, 640])
