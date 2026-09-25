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


# ─── data-* read-back: recompute the encoding from the file alone ───

EXAMPLES_DIR = EXAMPLE.parent


def _elements(svg: str, tag: str, attr: str):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(svg)
    return [el for el in root.iter()
            if el.tag.split("}", 1)[-1] == tag and el.get(attr) is not None]


def _poly_width(el) -> float:
    xs = [float(v) for v in el.get("points").replace(",", " ").split()[0::2]]
    return max(xs) - min(xs)


def test_funnel_width_ratio_recomputes_from_data_value():
    """No hard-coded counts: the file carries its own values."""
    tiers = _elements(EXAMPLE.read_text("utf-8"), "polygon", "data-value")
    assert len(tiers) == 4
    _assert_proportional([_poly_width(t) for t in tiers],
                         [float(t.get("data-value")) for t in tiers])


def test_ordinal_pyramid_carries_index_but_no_value(tmp_path):
    svg = Path(pyramid(["A", "B", "C", "D"], out_path=tmp_path / "p.svg")
               ).read_text("utf-8")
    assert "data-value" not in svg
    assert [int(e.get("data-index"))
            for e in _elements(svg, "polygon", "data-index")] == [0, 1, 2, 3]


def test_matrix_cells_carry_row_and_col():
    svg = (EXAMPLES_DIR / "matrix-sat-opt.svg").read_text("utf-8")
    cells = _elements(svg, "rect", "data-row")
    assert {(c.get("data-row"), c.get("data-col")) for c in cells} == {
        ("0", "0"), ("0", "1"), ("1", "0"), ("1", "1")}
    # row/col agree with the drawn geometry: higher index → further right/down
    for c in cells:
        for d in cells:
            same_row = c.get("data-row") == d.get("data-row")
            same_col = c.get("data-col") == d.get("data-col")
            if same_row and int(c.get("data-col")) < int(d.get("data-col")):
                assert float(c.get("x")) < float(d.get("x"))
            if same_col and int(c.get("data-row")) < int(d.get("data-row")):
                assert float(c.get("y")) < float(d.get("y"))


def test_layer_stack_bands_carry_index_in_draw_order():
    svg = (EXAMPLES_DIR / "layers-tcpip.svg").read_text("utf-8")
    bands = _elements(svg, "rect", "data-index")
    assert [int(b.get("data-index")) for b in bands] == [0, 1, 2, 3]
    ys = [float(b.get("y")) for b in bands]
    assert ys == sorted(ys)


def test_swimlane_steps_sit_in_their_lane_in_flow_order():
    svg = (EXAMPLES_DIR / "swimlane-release.svg").read_text("utf-8")
    steps = _elements(svg, "rect", "data-step")
    assert [int(s.get("data-step")) for s in steps] == list(range(6))
    # the spec: PM, Engineering, Engineering, QA, PM, Release
    assert [int(s.get("data-lane")) for s in steps] == [0, 1, 1, 2, 0, 3]
    centre_y: dict[str, set] = {}
    for s in steps:
        cy = float(s.get("y")) + float(s.get("height")) / 2
        centre_y.setdefault(s.get("data-lane"), set()).add(round(cy, 1))
    assert all(len(v) == 1 for v in centre_y.values()), centre_y
    lanes_by_y = sorted(centre_y, key=lambda k: next(iter(centre_y[k])))
    assert lanes_by_y == sorted(lanes_by_y, key=int)
    xs = [float(s.get("x")) for s in steps]
    assert xs == sorted(xs)


def test_venn_region_labels_carry_their_count(tmp_path):
    pytest.importorskip("matplotlib")
    pytest.importorskip("matplotlib_venn")
    from muriel.tools.venn import venn_single
    spec = {"a": 5, "b": 3, "c": 2, "a_b": 1, "a_c": 4, "b_c": 1, "all": 7}
    out = venn_single(spec, labels=["a", "b", "c"], title="Scope",
                      out_path=tmp_path / "v.svg")
    svg = Path(out).read_text("utf-8")
    regions = {e.get("data-region"): e for e in
               _elements(svg, "text", "data-region")}
    want = {"100": 5, "010": 3, "001": 2, "110": 1, "101": 4, "011": 1,
            "111": 7}
    assert {k: float(e.get("data-count")) for k, e in regions.items()} == want
    for k, e in regions.items():
        assert "".join(e.itertext()).strip() == str(want[k])
