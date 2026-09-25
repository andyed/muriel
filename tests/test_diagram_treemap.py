"""Treemap: area is the only encoding, so area is what gets checked.

Every check reads the rendered SVG back — cell rects and their declared
``data-share`` — rather than trusting the layout arithmetic, so a layout
that computes the right rectangle and writes the wrong one still fails.

Area fidelity is **relative** error, ``(drawn − true) / true``, per cell:
a 0.1-point slip is nothing on a 50% cell and a quarter of a 0.4% one, and
the sliver is the cell gutters and rounding distort most. The framing is
adapted from diagram-design's ``scripts/verify-treemap.py`` (MIT,
© 2025 Cathryn Lavery); the 4% bound is tighter than its 8%.
"""

import re
import warnings
from itertools import combinations
from pathlib import Path

import pytest

from muriel.tools.diagrams import treemap
from muriel.tools.diagrams._a11y import lint_a11y
from muriel.tools.diagrams._labels import verify_svg_labels
from muriel.tools.diagrams.check import check_svg

REL_TOL = 0.04
GUTTER = 4.0
EXAMPLE = (Path(__file__).resolve().parents[1]
           / "plugins/muriel/skills/compose/examples/diagrams/treemap-serp.svg")

_CELL_RE = re.compile(r"<rect [^>]*data-share=[^>]*/>")
_NUM = lambda tag, name: float(re.search(rf'\b{name}="([^"]+)"', tag).group(1))  # noqa: E731


def _cells(svg: str) -> list[dict]:
    out = []
    for tag in _CELL_RE.findall(svg):
        out.append({
            "x": _NUM(tag, "x"), "y": _NUM(tag, "y"),
            "w": _NUM(tag, "width"), "h": _NUM(tag, "height"),
            "share": _NUM(tag, "data-share"), "value": _NUM(tag, "data-value"),
            "label": re.search(r'data-label="([^"]*)"', tag).group(1),
            "tier": re.search(r'data-tier="([^"]*)"', tag).group(1),
        })
    return out


def _render(tmp_path, values, name="t.svg", **kw):
    cells = [{"label": f"Part {i}", "value": v} for i, v in enumerate(values)]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        path = treemap(cells, out_path=tmp_path / name, **kw)
    return Path(path).read_text("utf-8")


def _canvas(svg: str) -> tuple[float, float]:
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    return float(vb.group(1)), float(vb.group(2))


def _assert_area_fidelity(svg: str) -> None:
    cells = _cells(svg)
    total = sum(c["w"] * c["h"] for c in cells)
    share_total = sum(c["share"] for c in cells)
    assert share_total == pytest.approx(100, abs=0.01)
    for c in cells:
        drawn = c["w"] * c["h"] / total * 100
        rel = (drawn - c["share"]) / c["share"]
        assert abs(rel) <= REL_TOL, (
            f"{c['label']}: declares {c['share']:.3f}%, draws {drawn:.3f}% "
            f"({rel:+.1%} relative, bound {REL_TOL:.0%})")


VALUE_SETS = [
    [7.42, 2.91, 1.84, 0.97, 0.61, 0.22],       # the SERP example
    [5000, 900, 40, 30, 12, 9],                  # heavy tail, several slivers
    [60, 20, 10, 10],                            # ties
    [100, 80, 55, 40, 30, 22, 14, 3],            # full 8
    [1, 2, 3, 5, 8, 13, 21, 34],                 # fibonacci, given ascending
]


# ─── Area ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("values", VALUE_SETS)
def test_area_fidelity_within_four_percent_relative(tmp_path, values):
    _assert_area_fidelity(_render(tmp_path, values))


def test_committed_example_area_fidelity():
    _assert_area_fidelity(EXAMPLE.read_text("utf-8"))


@pytest.mark.parametrize("values", VALUE_SETS)
def test_declared_share_and_value_match_the_input(tmp_path, values):
    cells = _cells(_render(tmp_path, values))
    total = sum(values)
    assert len(cells) == len(values)  # nothing dropped
    assert sorted(c["value"] for c in cells) == pytest.approx(sorted(values))
    for c in cells:
        assert c["share"] == pytest.approx(c["value"] / total * 100, abs=1e-3)


def test_cells_are_drawn_largest_first(tmp_path):
    cells = _cells(_render(tmp_path, [1, 5, 3, 2]))
    assert [c["value"] for c in cells] == [5, 3, 2, 1]


# ─── Geometry ───────────────────────────────────────────────────────

@pytest.mark.parametrize("values", VALUE_SETS)
def test_cells_inside_canvas_and_non_overlapping_with_gutter(tmp_path, values):
    svg = _render(tmp_path, values, title="T")
    cw, ch = _canvas(svg)
    cells = _cells(svg)
    for c in cells:
        assert c["x"] >= 0 and c["y"] >= 0
        assert c["x"] + c["w"] <= cw and c["y"] + c["h"] <= ch
    for a, b in combinations(cells, 2):
        gap_x = max(b["x"] - (a["x"] + a["w"]), a["x"] - (b["x"] + b["w"]))
        gap_y = max(b["y"] - (a["y"] + a["h"]), a["y"] - (b["y"] + b["h"]))
        # separated along at least one axis by a full gutter (0.02 = the
        # two-decimal rounding of written coordinates)
        assert max(gap_x, gap_y) >= GUTTER - 0.02, (a["label"], b["label"])


def test_cells_tile_the_plot_less_gutters(tmp_path):
    """Outer edges sit on the plot rect; the gutter is the only gap."""
    cells = _cells(_render(tmp_path, [7.42, 2.91, 1.84, 0.97, 0.61, 0.22]))
    x0 = min(c["x"] for c in cells)
    y0 = min(c["y"] for c in cells)
    x1 = max(c["x"] + c["w"] for c in cells)
    y1 = max(c["y"] + c["h"] for c in cells)
    assert (x1 - x0, y1 - y0) == pytest.approx((896, 480), abs=0.02)


def test_layout_is_squarified_not_striped(tmp_path):
    cells = _cells(_render(tmp_path, [30, 25, 20, 15, 10]))
    worst = max(max(c["w"] / c["h"], c["h"] / c["w"]) for c in cells)
    assert worst < 3.0


def test_render_is_deterministic(tmp_path):
    a = _render(tmp_path, VALUE_SETS[1], name="a.svg")
    b = _render(tmp_path, VALUE_SETS[1], name="a.svg")
    assert a == b


# ─── Label tiers ────────────────────────────────────────────────────

def _texts_in(svg: str, c: dict) -> list[str]:
    out = []
    for x, y, body in re.findall(
            r'<text x="([\d.]+)" y="([\d.]+)"[^>]*>([^<]*)</text>', svg):
        x, y = float(x), float(y)
        if c["x"] <= x <= c["x"] + c["w"] and c["y"] <= y <= c["y"] + c["h"]:
            out.append(body)
    return out


def test_label_tiers_follow_cell_size(tmp_path):
    svg = _render(tmp_path, [5000, 900, 40, 30, 12, 9])
    cells = _cells(svg)
    by_label = {c["label"]: c for c in cells}
    big = by_label["Part 0"]
    assert big["tier"] == "large"
    texts = _texts_in(svg, big)
    assert texts[0] == "Part 0"
    assert "5,000" in texts[1] and "83%" in texts[1]
    # tiers only ever get poorer as cells get smaller
    rank = {"large": 3, "medium": 2, "small": 1, "sliver": 0}
    assert [rank[c["tier"]] for c in cells] == sorted(
        (rank[c["tier"]] for c in cells), reverse=True)


def test_medium_tier_drops_share_but_keeps_value(tmp_path):
    # name + value fits a narrow cell, name + value + share does not
    svg = _render(tmp_path, [200, 140, 100, 60], width=360,
                  plot_height=160, unit=" ms")
    mediums = [c for c in _cells(svg) if c["tier"] == "medium"]
    assert mediums, [c["tier"] for c in _cells(svg)]
    for c in mediums:
        texts = _texts_in(svg, c)
        assert any(" ms" in t for t in texts)
        assert not any("%" in t for t in texts)


def test_small_tier_uses_short_name_and_explains_it_in_the_legend(tmp_path):
    cells = [{"label": "Organic results", "value": 70},
             {"label": "Ads", "value": 20},
             {"label": "Knowledge panel", "value": 8},
             {"label": "Related searches", "value": 3, "short": "Rel"}]
    svg = Path(treemap(cells, out_path=tmp_path / "s.svg")).read_text("utf-8")
    rel = next(c for c in _cells(svg) if c["label"] == "Related searches")
    assert rel["tier"] == "small"
    assert _texts_in(svg, rel) == ["Rel"]
    assert re.search(r">Rel = Related searches · 3 · 3\.0%</text>", svg)


def test_sliver_has_no_text_in_cell_and_is_named_in_the_legend(tmp_path):
    svg = _render(tmp_path, [5000, 900, 40, 30, 12, 9])
    slivers = [c for c in _cells(svg) if c["tier"] == "sliver"]
    assert slivers
    for c in slivers:
        assert _texts_in(svg, c) == []
        legend = re.search(rf'>({re.escape(c["label"])} · [^<]+)</text>', svg)
        assert legend, c["label"]
        assert "%" in legend.group(1) and "bottom" in legend.group(1)
        # the locator disc, when drawn, sits wholly inside its cell
    for cx, cy, r in re.findall(
            r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"[^>]*'
            r'data-marker="sliver"', svg):
        cx, cy, r = float(cx), float(cy), float(r)
        host = next(c for c in slivers
                    if c["x"] <= cx <= c["x"] + c["w"]
                    and c["y"] <= cy <= c["y"] + c["h"])
        assert host["x"] <= cx - r and cx + r <= host["x"] + host["w"]
        assert host["y"] <= cy - r and cy + r <= host["y"] + host["h"]


def test_labels_are_never_rotated(tmp_path):
    svg = _render(tmp_path, [5000, 900, 40, 30, 12, 9])
    assert "rotate(" not in svg and "transform" not in svg


def test_cells_are_not_resized_for_labels(tmp_path):
    """Long names change tiers, never geometry."""
    short = _render(tmp_path, [50, 30, 15, 5], name="a.svg")
    cells = [{"label": f"An extremely long category name number {i}",
              "value": v} for i, v in enumerate([50, 30, 15, 5])]
    long_ = Path(treemap(cells, out_path=tmp_path / "b.svg")).read_text("utf-8")
    geom = lambda s: [(c["x"], c["y"], c["w"], c["h"]) for c in _cells(s)]  # noqa: E731
    assert geom(short) == geom(long_)


# ─── Gates ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("values", VALUE_SETS)
def test_rendered_treemaps_pass_diagram_check(tmp_path, values):
    svg_path = tmp_path / "c.svg"
    _render(tmp_path, values, name="c.svg", title="Check")
    assert check_svg(svg_path) == []
    report = verify_svg_labels(svg_path.read_text("utf-8"))
    assert report.ok, report.summary()


def test_brand_with_light_paper_still_clears_the_floor(tmp_path):
    from types import SimpleNamespace as NS
    brand = NS(
        colors=NS(background="#f7f5ee", foreground="#16161d",
                  foreground_muted="#3a3a48"),
        viz=NS(categorical=["#b3261e"]),
        typography=NS(body_family=None, mono_family=None),
    )
    cells = [{"label": "Organic", "value": 60, "focal": True},
             {"label": "Ads", "value": 25}, {"label": "Panel", "value": 10},
             {"label": "Nav", "value": 5}]
    out = treemap(cells, brand=brand, title="Light", out_path=tmp_path / "l.svg")
    assert check_svg(out) == []


def test_a11y_contract_and_default_desc(tmp_path):
    svg = _render(tmp_path, [7.42, 2.91, 1.84, 0.97], title="Fixation")
    assert lint_a11y(svg) == []
    desc = re.search(r"<desc [^>]*>(.*?)</desc>", svg).group(1)
    for i in range(4):
        assert f"Part {i}" in desc
    assert not re.search(r"\b(causes?|significant|best|better|proves?)\b", desc)


def test_focal_cell_takes_the_accent_stroke(tmp_path):
    cells = [{"label": "A", "value": 50}, {"label": "B", "value": 30, "focal": True},
             {"label": "C", "value": 15}, {"label": "D", "value": 5}]
    svg = Path(treemap(cells, out_path=tmp_path / "f.svg")).read_text("utf-8")
    b = re.search(r'<rect [^>]*data-label="B"[^>]*/>', svg).group(0)
    assert 'stroke="#7dd4e4"' in b and 'stroke-width="1.5"' in b
    assert svg.count('stroke-width="1.5"') == 1


# ─── Input discipline ───────────────────────────────────────────────

def test_too_many_cells_raises_with_guidance(tmp_path):
    with pytest.raises(ValueError, match="max_cells"):
        _render(tmp_path, list(range(1, 11)))


def test_max_cells_collapses_the_tail_into_a_named_other(tmp_path):
    values = [40, 25, 12, 8, 5, 4, 3, 2, 1]
    svg = _render(tmp_path, values, max_cells=6)
    cells = _cells(svg)
    assert len(cells) == 6
    other = next(c for c in cells if c["label"] == "Other")
    assert other["value"] == pytest.approx(4 + 3 + 2 + 1)
    assert 'data-members="Part 5; Part 6; Part 7; Part 8"' in svg
    desc = re.search(r"<desc [^>]*>(.*?)</desc>", svg).group(1)
    assert "combines Part 5, Part 6, Part 7, Part 8" in desc
    _assert_area_fidelity(svg)


def test_collapsing_the_focal_cell_raises(tmp_path):
    cells = [{"label": str(i), "value": 10 - i, "focal": i == 8}
             for i in range(9)]
    with pytest.raises(ValueError, match="focal"):
        treemap(cells, max_cells=6, out_path=tmp_path / "x.svg")


@pytest.mark.parametrize("bad", [0, -3, float("nan"), float("inf")])
def test_non_positive_values_raise_rather_than_drop(tmp_path, bad):
    with pytest.raises(ValueError, match="finite and > 0"):
        _render(tmp_path, [10, 5, 3, bad])


def test_too_few_cells_raises(tmp_path):
    with pytest.raises(ValueError, match="4–8"):
        _render(tmp_path, [3, 2, 1])


def test_two_focal_cells_raise(tmp_path):
    cells = [{"label": c, "value": v, "focal": True}
             for c, v in zip("ABCD", [4, 3, 2, 1])]
    with pytest.raises(ValueError, match="at most one"):
        treemap(cells, out_path=tmp_path / "x.svg")


def test_near_uniform_values_warn(tmp_path):
    cells = [{"label": c, "value": v} for c, v in zip("ABCD", [10, 9.5, 9, 8.5])]
    with pytest.warns(UserWarning, match="uniform area"):
        treemap(cells, out_path=tmp_path / "u.svg")


def test_many_slivers_warn(tmp_path):
    cells = [{"label": f"Region {i}", "value": v}
             for i, v in enumerate([5000, 900, 40, 30, 12, 9])]
    with pytest.warns(UserWarning, match="bar chart"):
        treemap(cells, out_path=tmp_path / "s.svg")


def test_area_check_trips_on_an_oversized_sliver(tmp_path):
    """The gate must fail on the defect it exists for: a small cell drawn
    too big (the upstream bug — a sliver 50% oversized, every check green)."""
    svg = _render(tmp_path, [7.42, 2.91, 1.84, 0.97, 0.61, 0.22])
    smallest = _cells(svg)[-1]
    tag = re.search(r'<rect [^>]*data-label="Part 5"[^>]*/>', svg).group(0)
    bad = tag.replace(f'width="{smallest["w"]:.2f}"',
                      f'width="{smallest["w"] * 1.5:.2f}"')
    assert bad != tag
    with pytest.raises(AssertionError, match="relative"):
        _assert_area_fidelity(svg.replace(tag, bad))
