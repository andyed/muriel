"""comparison_pair: a slopegraph must be one scale, and its labels must not lie.

The slopegraph makes one claim, that both axes carry the same scale, so a
line's angle is a rate of change. These tests read the rendered SVG back
(never the generator's arithmetic) and hold it to that claim:

- every endpoint sits where the shared scale puts its value, to 0.5px;
- the two axes declare, and draw, the identical scale;
- close values push their *labels* apart (with a leader tick) while the
  endpoints stay exact, and no two labels overlap;
- the printed delta carries the sign of the change, so increase and
  decrease read without colour.

The shared-scale and no-jitter invariants follow diagram-design's
``scripts/verify-slopegraph.py`` (MIT, © 2025 Cathryn Lavery).
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from muriel.tools.diagrams import comparison_pair
from muriel.tools.diagrams._a11y import lint_a11y
from muriel.tools.diagrams._labels import verify_svg_labels
from muriel.tools.diagrams.check import check_svg

NS = "{http://www.w3.org/2000/svg}"
TOL = 0.5
EXAMPLES = (Path(__file__).resolve().parents[1]
            / "plugins/muriel/skills/compose/examples/diagrams")

CROWDED = [
    {"label": "Alpha", "a": 10.0, "b": 12.0},
    {"label": "Beta", "a": 10.4, "b": 11.8},
    {"label": "Gamma", "a": 10.8, "b": 30.0},
    {"label": "Delta", "a": 11.0, "b": 11.9},
    {"label": "Epsilon", "a": 40.0, "b": 25.0},
]


def _render(tmp_path, items=CROWDED, name="cp.svg", **kw):
    kw.setdefault("states", ("Before", "After"))
    path = comparison_pair(items, out_path=tmp_path / name, **kw)
    return Path(path).read_text(encoding="utf-8")


def _axes(root):
    out = {}
    for el in root.iter(f"{NS}line"):
        if el.get("data-axis"):
            out[el.get("data-axis")] = el
    return out


def _series(root):
    return [el for el in root.iter(f"{NS}line")
            if el.get("data-a") is not None]


def _expected_y(axis, v):
    lo, hi = float(axis.get("data-min")), float(axis.get("data-max"))
    top, bot = float(axis.get("data-top")), float(axis.get("data-bottom"))
    return top + (bot - top) * (hi - v) / (hi - lo)


# ─── Position fidelity and the shared scale ─────────────────────────

@pytest.mark.parametrize("items", [
    CROWDED,
    [{"label": "x", "a": 0.0, "b": 100.0}, {"label": "y", "a": 100.0, "b": 0.0}],
    [{"label": f"s{i}", "a": 1000 + i * 37.0, "b": 1500 - i * 51.0}
     for i in range(10)],
    [{"label": "neg", "a": -5.0, "b": 3.0}, {"label": "pos", "a": 2.0, "b": -1.0}],
])
def test_endpoints_sit_on_the_shared_scale(tmp_path, items):
    root = ET.fromstring(_render(tmp_path, items))
    axes = _axes(root)
    lines = _series(root)
    assert len(lines) == len(items)
    for ln in lines:
        a, b = float(ln.get("data-a")), float(ln.get("data-b"))
        assert abs(float(ln.get("y1")) - _expected_y(axes["a"], a)) <= TOL
        assert abs(float(ln.get("y2")) - _expected_y(axes["b"], b)) <= TOL
        # the drawn x is the axis x on each side
        assert float(ln.get("x1")) == float(axes["a"].get("x1"))
        assert float(ln.get("x2")) == float(axes["b"].get("x1"))


def test_both_axes_declare_and_draw_one_scale(tmp_path):
    root = ET.fromstring(_render(tmp_path))
    a, b = _axes(root)["a"], _axes(root)["b"]
    for attr in ("data-min", "data-max", "data-top", "data-bottom",
                 "y1", "y2"):
        assert a.get(attr) == b.get(attr), attr
    # A value common to both sides lands at the same y on both axes: fit
    # y = m*v + c per side from the drawn lines and compare slope + origin.
    lines = _series(root)

    def fit(pts):
        n = len(pts)
        mx = sum(p[0] for p in pts) / n
        my = sum(p[1] for p in pts) / n
        m = (sum((x - mx) * (y - my) for x, y in pts)
             / sum((x - mx) ** 2 for x, _ in pts))
        return m, my - m * mx

    ma, ca = fit([(float(l.get("data-a")), float(l.get("y1"))) for l in lines])
    mb, cb = fit([(float(l.get("data-b")), float(l.get("y2"))) for l in lines])
    assert ma == pytest.approx(mb, abs=1e-3)
    assert ca == pytest.approx(cb, abs=TOL)


def test_explicit_scale_is_used_and_must_contain_the_data(tmp_path):
    root = ET.fromstring(_render(tmp_path, scale={"min": 0, "max": 50,
                                                  "unit": "ms"}))
    ax = _axes(root)["a"]
    assert float(ax.get("data-min")) == 0 and float(ax.get("data-max")) == 50
    svg = ET.tostring(root, encoding="unicode")
    assert "both axes: 0–50 (ms)" in svg
    with pytest.raises(ValueError, match="does not contain"):
        _render(tmp_path, scale={"min": 0, "max": 20})
    with pytest.raises(ValueError, match="min < max"):
        _render(tmp_path, scale={"min": 50, "max": 0})


# ─── Label nudging ──────────────────────────────────────────────────

def _labels_by(root, end):
    rows = {}
    for el in root.iter(f"{NS}text"):
        if el.get("data-end") == end and el.get("data-role") == "name":
            rows[el.get("data-item")] = float(el.get("y"))
    return rows


def test_close_values_nudge_labels_but_never_endpoints(tmp_path):
    svg = _render(tmp_path)
    root = ET.fromstring(svg)
    axes = _axes(root)
    # Endpoints are exact even though Alpha/Beta/Gamma/Delta crowd.
    for ln in _series(root):
        assert abs(float(ln.get("y1"))
                   - _expected_y(axes["a"], float(ln.get("data-a")))) <= TOL
    rows = sorted(_labels_by(root, "a").values())
    gaps = [b - a for a, b in zip(rows, rows[1:])]
    assert min(gaps) >= 16 - 1e-6, gaps
    # At least one label was displaced, and each displaced one has a leader.
    leaders = [el for el in root.iter(f"{NS}line")
               if el.get("data-role") == "leader"]
    assert leaders
    for ld in leaders:
        item, end = ld.get("data-item"), ld.get("data-end")
        series = next(l for l in _series(root) if l.get("data-item") == item)
        true_y = float(series.get("y1" if end == "a" else "y2"))
        assert float(ld.get("y1")) == pytest.approx(true_y, abs=1e-3)
    report = verify_svg_labels(svg)
    assert report.ok, report.summary()


def test_label_order_follows_value_order(tmp_path):
    root = ET.fromstring(_render(tmp_path))
    for end in ("a", "b"):
        rows = _labels_by(root, end)
        vals = {l.get("data-item"): float(l.get(f"data-{end}"))
                for l in _series(root)}
        by_value = sorted(rows, key=lambda k: -vals[k])
        by_row = sorted(rows, key=lambda k: rows[k])
        assert by_value == by_row


def test_uncrowded_labels_stay_on_their_endpoint(tmp_path):
    items = [{"label": "hi", "a": 90.0, "b": 80.0},
             {"label": "lo", "a": 10.0, "b": 20.0}]
    svg = _render(tmp_path, items)
    assert 'data-role="leader"' not in svg


def test_no_label_overlaps_at_the_budget_with_identical_starts(tmp_path):
    items = [{"label": f"Series number {i}", "a": 50.0, "b": 40.0 + i}
             for i in range(10)]
    svg = _render(tmp_path, items)
    rows = sorted(_labels_by(ET.fromstring(svg), "a").values())
    assert all(b - a >= 16 - 1e-6 for a, b in zip(rows, rows[1:]))
    report = verify_svg_labels(svg)
    assert report.ok, report.summary()


# ─── Delta text ─────────────────────────────────────────────────────

def test_delta_text_sign_matches_the_change(tmp_path):
    items = [{"label": "up", "a": 10.0, "b": 22.0},
             {"label": "down", "a": 30.0, "b": 22.5},
             {"label": "flat", "a": 15.0, "b": 15.0}]
    root = ET.fromstring(_render(tmp_path, items, value_format="{:.0f}"))
    got = {el.get("data-item"): "".join(el.itertext())
           for el in root.iter(f"{NS}text") if el.get("data-role") == "delta"}
    assert got["up"] == "(+12)"
    assert got["down"] == "(−8)"   # typographic minus, magnitude 7.5 → 8
    assert got["flat"] == "(0)"
    for el in root.iter(f"{NS}text"):
        if el.get("data-role") == "delta":
            d = float(el.get("data-delta"))
            text = "".join(el.itertext())
            if d > 0:
                assert text.startswith("(+")
            elif d < 0:
                assert text.startswith("(−")


def test_printed_values_match_declared_values(tmp_path):
    root = ET.fromstring(_render(tmp_path, value_format="{:.1f}"))
    vals = {l.get("data-item"): l for l in _series(root)}
    for el in root.iter(f"{NS}text"):
        if el.get("data-role") == "value":
            line = vals[el.get("data-item")]
            want = float(line.get(f"data-{el.get('data-end')}"))
            assert float("".join(el.itertext())) == pytest.approx(want, abs=0.05)


# ─── Focal ──────────────────────────────────────────────────────────

def test_focal_is_painted_last_and_is_the_only_accent(tmp_path):
    svg = _render(tmp_path, focal="Beta")
    root = ET.fromstring(svg)
    lines = _series(root)
    assert lines[-1].get("data-item") == "Beta"
    strokes = {l.get("stroke") for l in lines[:-1]}
    assert lines[-1].get("stroke") not in strokes


def test_two_focal_items_raise(tmp_path):
    items = [dict(it) for it in CROWDED]
    items[0]["focal"] = True
    with pytest.raises(ValueError, match="at most one focal"):
        _render(tmp_path, items, focal="Beta")
    with pytest.raises(ValueError, match="at most one focal"):
        _render(tmp_path, focal=["Alpha", "Beta"])


# ─── Budget and input errors ────────────────────────────────────────

def test_budget_errors(tmp_path):
    many = [{"label": f"s{i}", "a": float(i), "b": float(i + 1)}
            for i in range(11)]
    with pytest.raises(ValueError, match="2–10 items"):
        _render(tmp_path, many)
    with pytest.raises(ValueError, match="2–10 items"):
        _render(tmp_path, [{"label": "one", "a": 1.0, "b": 2.0}])
    with pytest.raises(ValueError, match="exactly two states"):
        _render(tmp_path, states=("a", "b", "c"))


@pytest.mark.parametrize("bad, match", [
    ([{"label": "x", "a": 1.0, "b": None}, {"label": "y", "a": 1, "b": 2}],
     "missing an endpoint"),
    ([{"label": "x", "a": float("nan"), "b": 1.0},
      {"label": "y", "a": 1.0, "b": 2.0}], "finite"),
    ([{"label": "x", "a": 1.0, "b": 2.0}, {"label": "y", "a": 1.0, "b": 2.0}],
     "coincide"),
    ([{"label": "x", "a": 1.0, "b": 2.0}, {"label": "x", "a": 3.0, "b": 2.0}],
     "duplicate"),
    ([{"label": "x", "a": 1.0, "b": "PASS"}, {"label": "y", "a": 1, "b": 2}],
     "cannot infer mode"),
])
def test_bad_inputs_raise(tmp_path, bad, match):
    with pytest.raises(ValueError, match=match):
        _render(tmp_path, bad)


# ─── Determinism, a11y, diagram-check ───────────────────────────────

def test_output_is_deterministic(tmp_path):
    a = _render(tmp_path, name="one.svg", focal="Gamma")
    b = _render(tmp_path, name="one.svg", focal="Gamma")
    assert a == b


@pytest.mark.parametrize("kw", [
    {},
    {"focal": "Epsilon", "title": "Latency before and after", "scale":
     {"unit": "ms"}},
])
def test_slope_passes_a11y_and_diagram_check(tmp_path, kw):
    path = comparison_pair(CROWDED, states=("Before", "After"),
                           out_path=tmp_path / "chk.svg", **kw)
    assert lint_a11y(Path(path).read_text(encoding="utf-8")) == []
    assert check_svg(path) == []


# ─── Trace mode ─────────────────────────────────────────────────────

TRACE = [
    {"label": "Signed in", "a": "PASS", "b": "PASS"},
    {"label": "Quota", "a": "PASS", "b": "FAIL"},
    {"label": "Geo policy", "a": "PASS", "b": "NOT REACHED"},
    {"label": "Deliver", "a": "PASS", "b": "NOT REACHED"},
]


def test_trace_marks_the_first_divergence_only(tmp_path):
    svg = _render(tmp_path, TRACE, states=("Request A", "Request B"))
    root = ET.fromstring(svg)
    marks = [el for el in root.iter(f"{NS}text")
             if el.get("data-role") == "divergence"]
    assert len(marks) == 1 and marks[0].get("data-item") == "Quota"
    statuses = {(el.get("data-item"), el.get("data-end")): "".join(el.itertext())
                for el in root.iter(f"{NS}text")
                if el.get("data-role") == "status"}
    assert statuses[("Quota", "b")] == "FAIL"
    assert statuses[("Deliver", "b")] == "NOT REACHED"
    assert check_svg(tmp_path / "cp.svg") == []


def test_trace_errors(tmp_path):
    same = [{"label": f"r{i}", "a": "PASS", "b": "PASS"} for i in range(4)]
    with pytest.raises(ValueError, match="never diverge"):
        _render(tmp_path, same)
    with pytest.raises(ValueError, match="3–6 rules"):
        _render(tmp_path, TRACE[:2])
    with pytest.raises(ValueError, match="3–6 rules"):
        _render(tmp_path, TRACE + [{"label": f"extra {i}", "a": "PASS",
                                    "b": "SKIPPED"} for i in range(3)])
    with pytest.raises(ValueError, match="focal"):
        _render(tmp_path, TRACE, focal="Quota")


# ─── Committed examples ─────────────────────────────────────────────

@pytest.mark.parametrize("name", ["comparison-pair-serp.svg",
                                  "comparison-pair-trace.svg"])
def test_committed_example_is_byte_identical_and_clean(tmp_path, name):
    import importlib.util

    script = Path(__file__).resolve().parents[1] / "scripts/render_diagram_examples.py"
    spec = importlib.util.spec_from_file_location("_rde_cp", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rendered = Path(mod.render_examples(tmp_path)[name]).read_text("utf-8")
    assert rendered == (EXAMPLES / name).read_text("utf-8"), (
        f"{name} is stale; run python3 scripts/render_diagram_examples.py")
    assert check_svg(EXAMPLES / name) == []
