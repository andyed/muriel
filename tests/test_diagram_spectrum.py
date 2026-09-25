"""spectrum: position is the encoding, so position is what gets checked.

Every geometric assertion reads the rendered SVG back — the circles' ``cx``
against the ``data-*`` values bound to their row and the plot's own
``data-min`` / ``data-max`` / ``data-x0`` / ``data-x1`` — rather than
trusting the generator's arithmetic.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from muriel.tools.diagrams._a11y import lint_a11y
from muriel.tools.diagrams._labels import verify_svg_labels
from muriel.tools.diagrams.check import check_svg
from muriel.tools.diagrams.spectrum import MAX_ROWS, spectrum

NS = "{http://www.w3.org/2000/svg}"
TOL_PX = 0.5
EXAMPLE = (Path(__file__).resolve().parents[1]
           / "plugins/muriel/skills/compose/examples/diagrams"
           / "spectrum-palette-tritan.svg")

SCALE = {"min": -10, "max": 30, "left_pole": "cold", "right_pole": "hot"}


def _root(path):
    return ET.fromstring(Path(path).read_text("utf-8"))


def _plot(root):
    g = next(e for e in root.iter(f"{NS}g")
             if e.get("class") == "spectrum-plot")
    return (float(g.get("data-min")), float(g.get("data-max")),
            float(g.get("data-x0")), float(g.get("data-x1")))


def _rows(root):
    return [e for e in root.iter(f"{NS}g") if e.get("class") == "spectrum-row"]


def _circle(row, role):
    return next(c for c in row.iter(f"{NS}circle") if c.get("data-role") == role)


def _x(v, lo, hi, x0, x1):
    return x0 + (v - lo) / (hi - lo) * (x1 - x0)


# ─── Position fidelity ──────────────────────────────────────────────

@pytest.mark.parametrize("values", [
    [-10, 0, 7.5, 30],
    [0.1, 29.9, 12.345, -9.99],
    [30, 30, -10],
])
def test_points_sit_at_their_value(tmp_path, values):
    items = [{"label": f"item {i}", "value": v} for i, v in enumerate(values)]
    root = _root(spectrum(items, scale=SCALE, out_path=tmp_path / "p.svg"))
    lo, hi, x0, x1 = _plot(root)
    assert (lo, hi) == (-10, 30)
    rows = _rows(root)
    assert len(rows) == len(values)
    for row in rows:
        v = float(row.get("data-value"))
        cx = float(_circle(row, "point").get("cx"))
        assert abs(cx - _x(v, lo, hi, x0, x1)) <= TOL_PX


def test_dumbbell_ends_sit_at_their_values(tmp_path):
    items = [{"label": "up", "start": -4, "end": 22},
             {"label": "down", "start": 28.5, "end": 3},
             {"label": "flat", "start": 5, "end": 5}]
    root = _root(spectrum(items, scale=SCALE, out_path=tmp_path / "d.svg"))
    lo, hi, x0, x1 = _plot(root)
    for row in _rows(root):
        for role, attr in (("start", "data-start"), ("end", "data-end")):
            v = float(row.get(attr))
            cx = float(_circle(row, role).get("cx"))
            assert abs(cx - _x(v, lo, hi, x0, x1)) <= TOL_PX


def test_axis_spans_exactly_the_given_domain_and_ticks_both_ends(tmp_path):
    root = _root(spectrum([{"label": "a", "value": 3}],
                          scale={**SCALE, "ticks": [0, 10, 20]},
                          out_path=tmp_path / "t.svg"))
    ticks = [t.text for t in root.iter(f"{NS}text")
             if t.get("text-anchor") == "middle" and t.get("font-size") == "10"]
    assert ticks[0] == "−10" and ticks[-1] == "30"
    assert {"0", "10", "20"} <= set(ticks)


def test_poles_are_labeled_at_both_ends(tmp_path):
    root = _root(spectrum([{"label": "a", "value": 3}], scale=SCALE,
                          out_path=tmp_path / "poles.svg"))
    lo, hi, x0, x1 = _plot(root)
    poles = {t.get("data-pole"): t for t in root.iter(f"{NS}text")
             if t.get("data-pole")}
    assert poles["left"].text == "cold" and poles["right"].text == "hot"
    assert float(poles["left"].get("x")) == pytest.approx(x0, abs=0.1)
    assert poles["left"].get("text-anchor") == "start"
    assert float(poles["right"].get("x")) == pytest.approx(x1, abs=0.1)
    assert poles["right"].get("text-anchor") == "end"


# ─── Direction markers ──────────────────────────────────────────────

def test_change_direction_reads_without_colour(tmp_path):
    items = [{"label": "up", "start": 0, "end": 20},
             {"label": "down", "start": 20, "end": 0},
             {"label": "flat", "start": 5, "end": 5}]
    root = _root(spectrum(items, scale=SCALE, out_path=tmp_path / "dir.svg"))
    rows = {r.get("data-label"): r for r in _rows(root)}
    assert rows["up"].get("data-direction") == "increase"
    assert rows["down"].get("data-direction") == "decrease"
    assert rows["flat"].get("data-direction") == "none"
    bg = next(root.iter(f"{NS}rect")).get("fill")
    for name in ("up", "down"):
        row = rows[name]
        start, end = _circle(row, "start"), _circle(row, "end")
        # Hollow start (background fill, stroked), solid end — shape, not hue.
        assert start.get("fill") == bg and start.get("stroke")
        assert end.get("fill") != bg and not end.get("stroke")
        # The connector's arrowhead points at the end dot.
        line = next(row.iter(f"{NS}line"))
        assert "marker-end" in line.attrib
        x1, x2 = float(line.get("x1")), float(line.get("x2"))
        ex = float(end.get("cx"))
        assert abs(x2 - ex) < abs(x1 - ex)


def test_extent_ranges_have_no_direction(tmp_path):
    items = [{"label": "a", "start": 0, "end": 20},
             {"label": "b", "start": 25, "end": 5}]
    svg = spectrum(items, scale=SCALE, range_kind="extent",
                   out_path=tmp_path / "ext.svg")
    root = _root(svg)
    for row in _rows(root):
        assert row.get("data-direction") == "none"
        assert _circle(row, "start").get("fill") == _circle(row, "end").get("fill")
        assert not any("marker-end" in ln.attrib for ln in row.iter(f"{NS}line"))


def test_short_gap_keeps_true_positions_and_drops_the_arrow(tmp_path):
    items = [{"label": "close", "start": 10, "end": 10.3}]
    root = _root(spectrum(items, scale=SCALE, out_path=tmp_path / "c.svg"))
    lo, hi, x0, x1 = _plot(root)
    row = _rows(root)[0]
    assert float(_circle(row, "end").get("cx")) == pytest.approx(
        _x(10.3, lo, hi, x0, x1), abs=TOL_PX)
    assert not any("marker-end" in ln.attrib for ln in row.iter(f"{NS}line"))


# ─── Sort modes ─────────────────────────────────────────────────────

RANGES = [{"label": "A", "start": 0, "end": 5},     # +5, end 5
          {"label": "B", "start": 20, "end": 10},   # −10, end 10
          {"label": "C", "start": 1, "end": 25}]    # +24, end 25


@pytest.mark.parametrize("sort,order", [
    ("input", ["A", "B", "C"]),
    ("value", ["C", "B", "A"]),
    ("delta", ["C", "A", "B"]),
])
def test_sort_modes(tmp_path, sort, order):
    root = _root(spectrum(RANGES, scale=SCALE, sort=sort,
                          out_path=tmp_path / f"{sort}.svg"))
    assert [r.get("data-label") for r in _rows(root)] == order
    ys = [float(_circle(r, "end").get("cy")) for r in _rows(root)]
    assert ys == sorted(ys)
    footer = [t.text for t in root.iter(f"{NS}text")
              if t.text and t.text.startswith("Rows ")]
    assert footer, "the row order must be stated"


def test_value_sort_on_points(tmp_path):
    pts = [{"label": "lo", "value": 1}, {"label": "hi", "value": 9},
           {"label": "mid", "value": 5}]
    root = _root(spectrum(pts, scale=SCALE, sort="value",
                          out_path=tmp_path / "v.svg"))
    assert [r.get("data-label") for r in _rows(root)] == ["hi", "mid", "lo"]


def test_focal_follows_its_item_through_a_sort(tmp_path):
    root = _root(spectrum(RANGES, scale=SCALE, sort="delta", focal=1,
                          out_path=tmp_path / "f.svg"))
    focal = [r.get("data-label") for r in _rows(root) if r.get("data-focal")]
    assert focal == ["B"]


# ─── Validation ─────────────────────────────────────────────────────

@pytest.mark.parametrize("items,kw,needle", [
    ([], {}, "at least one"),
    ([{"label": f"i{k}", "value": 1} for k in range(MAX_ROWS + 1)], {},
     "at most"),
    ([{"label": "a", "start": -11, "end": 5}], {}, "outside the scale"),
    ([{"label": "a", "start": 0, "end": 31}], {}, "outside the scale"),
    ([{"label": "a", "value": 40}], {}, "outside the scale"),
    ([{"label": "a", "start": 1}], {}, "both 'start' and 'end'"),
    ([{"label": "a", "value": 1, "start": 1, "end": 2}], {}, "either"),
    ([{"label": "a", "value": 1}, {"label": "b", "start": 1, "end": 2}], {},
     "mix"),
    ([{"label": "a", "value": 1}], {"sort": "delta"}, "points have no change"),
    ([{"label": "a", "value": 1}], {"sort": "rank"}, "sort must be"),
    ([{"label": "a", "value": 1}], {"focal": 3}, "out of range"),
    ([{"label": "a", "value": 1, "focal": True},
      {"label": "b", "value": 2, "focal": True}], {}, "at most one focal"),
    ([{"label": "", "value": 1}], {}, "label"),
    ([{"label": "a", "value": float("nan")}], {}, "finite"),
    ([{"label": "a", "value": 1}], {"range_kind": "trend"}, "range_kind"),
])
def test_invalid_specs_raise(tmp_path, items, kw, needle):
    with pytest.raises(ValueError, match=re.escape(needle)):
        spectrum(items, scale=SCALE, out_path=tmp_path / "x.svg", **kw)


@pytest.mark.parametrize("scale,needle", [
    ({"min": 5, "max": 5, "left_pole": "a", "right_pole": "b"}, "greater"),
    ({"min": 0, "max": 5, "left_pole": "", "right_pole": "b"}, "pole"),
    ({"min": 0, "max": 5, "right_pole": "b"}, "left_pole"),
    ({"min": 0, "max": 5, "left_pole": "a", "right_pole": "b",
      "ticks": [7]}, "outside the scale"),
])
def test_invalid_scales_raise(tmp_path, scale, needle):
    with pytest.raises(ValueError, match=re.escape(needle)):
        spectrum([{"label": "a", "value": 1}], scale=scale,
                 out_path=tmp_path / "x.svg")


def test_truncated_ratio_scale_needs_an_explicit_choice(tmp_path):
    scale = {"min": 40, "max": 80, "left_pole": "low", "right_pole": "high"}
    items = [{"label": "a", "start": 45, "end": 72}]
    with pytest.raises(ValueError, match="does not include zero"):
        spectrum(items, scale=scale, out_path=tmp_path / "z.svg")

    # zero=False: interval scale, drawn as given and disclosed in the footer.
    root = _root(spectrum(items, scale=scale, zero=False,
                          out_path=tmp_path / "z1.svg"))
    assert _plot(root)[:2] == (40, 80)
    assert any("does not start at zero" in (t.text or "")
               for t in root.iter(f"{NS}text"))

    # zero=True: the axis is extended to include zero.
    root = _root(spectrum(items, scale=scale, zero=True,
                          out_path=tmp_path / "z2.svg"))
    assert _plot(root)[:2] == (0, 80)

    # The choice can also travel in the scale dict (JSON specs).
    spectrum(items, scale={**scale, "zero": False}, out_path=tmp_path / "z3.svg")


# ─── Output contract ────────────────────────────────────────────────

def test_rendering_is_deterministic(tmp_path):
    a = spectrum(RANGES, scale=SCALE, focal=2, show_delta=True,
                 out_path=tmp_path / "same.svg")
    first = Path(a).read_text("utf-8")
    b = spectrum(RANGES, scale=SCALE, focal=2, show_delta=True,
                 out_path=tmp_path / "same.svg")
    assert Path(b).read_text("utf-8") == first


def test_delta_column_prints_signed_change_in_points_for_percent(tmp_path):
    svg = Path(spectrum(
        [{"label": "a", "start": 30, "end": 42.5},
         {"label": "b", "start": 60, "end": 51}],
        scale={"min": 0, "max": 100, "left_pole": "none", "right_pole": "all",
               "unit": "%"},
        show_delta=True, out_path=tmp_path / "pct.svg")).read_text("utf-8")
    assert ">+12.5 pts<" in svg and ">−9.0 pts<" in svg
    assert ">42.5%<" in svg


def test_default_desc_lists_items_and_claims_nothing(tmp_path):
    svg = Path(spectrum(RANGES, scale=SCALE, sort="delta",
                        out_path=tmp_path / "desc.svg")).read_text("utf-8")
    desc = re.search(r"<desc [^>]*>(.*?)</desc>", svg, re.S).group(1)
    for word in ("cold", "hot", "A", "B", "C", "sorted by change"):
        assert word in desc
    assert not re.search(r"\b(causes?|significant|best|better|proves?)\b", desc)


ADVERSARIAL = {
    "long-labels": dict(
        items=[{"label": "A deliberately long row label that has to wrap",
                "start": -10, "end": 30, "focal": True},
               {"label": "Supercalifragilisticexpialidocious", "start": 30,
                "end": -10},
               {"label": "x", "start": -10, "end": -10}],
        scale={**SCALE, "left_pole": "an unusually verbose left pole",
               "right_pole": "and an equally verbose right pole"},
        show_delta=True, title="Adversarial spectrum"),
    "points-at-edges": dict(
        items=[{"label": f"row {i}", "value": v} for i, v in
               enumerate([-10, 30, -10, 30, 10, -10, 30, 0, 29.99, -9.99])],
        scale=SCALE, sort="value"),
    "extent-percent": dict(
        items=[{"label": "a", "start": 0, "end": 100},
               {"label": "b", "start": 49.5, "end": 50.5}],
        scale={"min": 0, "max": 100, "left_pole": "none", "right_pole": "all",
               "unit": "%", "label": "share of sessions"},
        range_kind="extent", show_delta=True, series=("min", "max")),
}


@pytest.mark.parametrize("name", sorted(ADVERSARIAL))
def test_adversarial_specs_pass_every_gate(tmp_path, name):
    path = spectrum(out_path=tmp_path / f"{name}.svg", **ADVERSARIAL[name])
    report = verify_svg_labels(path)
    assert report.ok, report.summary()
    assert lint_a11y(Path(path).read_text("utf-8")) == []
    assert check_svg(path) == []


def test_brand_tokens_are_used(tmp_path):
    pytest.importorskip("tomllib")  # brand.toml loading is 3.11+
    from muriel.styleguide import load_styleguide
    brand = load_styleguide(Path(__file__).resolve().parents[1]
                            / "docs/examples/example-brand.toml")
    path = spectrum(RANGES, scale=SCALE, focal=0, brand=brand,
                    out_path=tmp_path / "brand.svg")
    svg = Path(path).read_text("utf-8")
    assert f'fill="{brand.colors.background}"' in svg
    assert check_svg(path) == []


# ─── The committed example ──────────────────────────────────────────

def test_committed_example_is_clean_and_matches_its_desc():
    assert check_svg(EXAMPLE) == []
    root = _root(EXAMPLE)
    rows = {r.get("data-label"): r for r in _rows(root)}
    # The <desc> quotes these numbers; if the palettes or the CVD model
    # change, the example's claim has to be rewritten, not silently kept.
    for label, start, end in (("Wong", 17.4, 5.3),
                              ("Nord Aurora", 16.8, 8.8),
                              ("Nord Frost", -16.2, -7.5)):
        assert float(rows[label].get("data-start")) == start
        assert float(rows[label].get("data-end")) == end
    for label in ("IBM", "Catppuccin Mocha", "Tol high-contrast"):
        r = rows[label]
        assert abs(float(r.get("data-end")) - float(r.get("data-start"))) <= 4
