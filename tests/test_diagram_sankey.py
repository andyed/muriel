"""The Sankey's claim is that ribbon width is volume and volume is conserved.

Every way of breaking that claim renders perfectly, so these tests read the
written SVG back (``data-value`` on every bar and ribbon, geometry from the
coordinates) and recompute the invariants rather than trusting the
generator's arithmetic. The invariant list follows the MIT-licensed
diagram-design skill (© 2025 Cathryn Lavery), ``scripts/verify-sankey.py``:
conservation, column totals, ribbon width constancy, value fidelity as
relative error, and ribbons meeting their bars square-on.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from muriel.tools.diagrams import sankey
from muriel.tools.diagrams._a11y import lint_a11y
from muriel.tools.diagrams.check import check_svg

NS = "{http://www.w3.org/2000/svg}"
EXAMPLE = (Path(__file__).resolve().parents[1]
           / "plugins/muriel/skills/compose/examples/diagrams"
           / "sankey-search-sessions.svg")

STAGES = ["Query", "Action", "Outcome"]
NODES = [
    {"id": "q", "stage": "Query", "label": "Sessions", "value": 1000},
    {"id": "clk", "stage": "Action", "label": "Click", "value": 600},
    {"id": "ad", "stage": "Action", "label": "Ad click", "value": 150},
    {"id": "no", "stage": "Action", "label": "No click", "value": 250},
    {"id": "sat", "stage": "Outcome", "label": "Satisfied", "value": 620},
    {"id": "ref", "stage": "Outcome", "label": "Reformulated", "value": 280},
    {"id": "gone", "stage": "Outcome", "label": "Abandoned", "value": 100},
]
FLOWS = [
    {"src": "q", "dst": "clk", "value": 600},
    {"src": "q", "dst": "ad", "value": 150},
    {"src": "q", "dst": "no", "value": 250},
    {"src": "clk", "dst": "sat", "value": 480},
    {"src": "clk", "dst": "ref", "value": 120},
    {"src": "ad", "dst": "sat", "value": 70},
    {"src": "ad", "dst": "ref", "value": 80},
    {"src": "no", "dst": "sat", "value": 70},
    {"src": "no", "dst": "ref", "value": 80},
    {"src": "no", "dst": "gone", "value": 100},
]


def _render(tmp_path, stages=STAGES, nodes=NODES, flows=FLOWS, name="s.svg",
            **kw):
    return Path(sankey(stages, nodes, flows, out_path=tmp_path / name, **kw))


def _parse(svg_text):
    root = ET.fromstring(svg_text)
    bars = {}
    for r in root.iter(f"{NS}rect"):
        if r.get("data-node"):
            bars[r.get("data-node")] = {
                "x": float(r.get("x")), "y": float(r.get("y")),
                "w": float(r.get("width")), "h": float(r.get("height")),
                "stage": int(r.get("data-stage")),
                "value": float(r.get("data-value")),
            }
    ribbons = []
    for p in root.iter(f"{NS}path"):
        if not p.get("data-flow"):
            continue
        pts = [tuple(map(float, m)) for m in
               re.findall(r"[ML]([-\d.]+),([-\d.]+)", p.get("d"))]
        assert p.get("d").rstrip().endswith("Z"), "ribbon must be closed"
        half = len(pts) // 2
        top, bot = pts[:half], pts[half:][::-1]
        ribbons.append({"src": p.get("data-src"), "dst": p.get("data-dst"),
                        "value": float(p.get("data-value")),
                        "focal": p.get("data-focal") == "true",
                        "top": top, "bot": bot, "fill": p.get("fill"),
                        "stroke": p.get("stroke")})
    return bars, ribbons


def _assert_conserved(svg_text):
    bars, ribbons = _parse(svg_text)
    assert bars and ribbons, "read nothing — a blind check must not pass"

    # value fidelity: one k, relative error ≤ 4 % on every bar
    k = max(b["h"] for b in bars.values()) / max(b["value"] for b in bars.values())
    for nid, b in bars.items():
        want = b["value"] * k
        assert abs(b["h"] - want) / want <= 0.04, (nid, b["h"], want)

    # column totals within 1 px
    stages = sorted({b["stage"] for b in bars.values()})
    col_h = [sum(b["h"] for b in bars.values() if b["stage"] == s)
             for s in stages]
    assert max(col_h) - min(col_h) <= 1.0, col_h

    for r in ribbons:
        src, dst = bars[r["src"]], bars[r["dst"]]
        w_src = r["bot"][0][1] - r["top"][0][1]
        w_dst = r["bot"][-1][1] - r["top"][-1][1]
        # ribbon width constancy + width is volume on the same k
        assert w_src == pytest.approx(w_dst, abs=0.05)
        assert abs(w_src - r["value"] * k) / (r["value"] * k) <= 0.04
        # endpoints land on the bar edges, inside the bar's extent
        assert r["top"][0][0] == pytest.approx(src["x"] + src["w"], abs=0.01)
        assert r["top"][-1][0] == pytest.approx(dst["x"], abs=0.01)
        assert r["bot"][0][0] == pytest.approx(src["x"] + src["w"], abs=0.01)
        assert src["y"] - 0.01 <= r["top"][0][1] <= r["bot"][0][1] \
            <= src["y"] + src["h"] + 0.01
        assert dst["y"] - 0.01 <= r["top"][-1][1] <= r["bot"][-1][1] \
            <= dst["y"] + dst["h"] + 0.01
        # square-on at both bars: the first and last segments are flat
        for edge in (r["top"], r["bot"]):
            for (xa, ya), (xb, yb) in ((edge[0], edge[1]), (edge[-2], edge[-1])):
                assert abs(yb - ya) / (xb - xa) < 0.05, "ribbon slants at its bar"

    # in == out per middle node, and every bar saturated, within 0.75 px
    for nid, b in bars.items():
        ins = [r for r in ribbons if r["dst"] == nid]
        outs = [r for r in ribbons if r["src"] == nid]
        w_in = sum(r["bot"][-1][1] - r["top"][-1][1] for r in ins)
        w_out = sum(r["bot"][0][1] - r["top"][0][1] for r in outs)
        if ins:
            assert abs(w_in - b["h"]) <= 0.75, (nid, w_in, b["h"])
        if outs:
            assert abs(w_out - b["h"]) <= 0.75, (nid, w_out, b["h"])
        if ins and outs:
            assert abs(w_in - w_out) <= 0.75, (nid, w_in, w_out)
        # slices never overlap at a bar
        for group, end in ((ins, -1), (outs, 0)):
            spans = sorted((r["top"][end][1], r["bot"][end][1]) for r in group)
            for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
                assert b0 >= a1 - 0.01, (nid, spans)
    return bars, ribbons


# ─── Conservation, geometry, drawing order ──────────────────────────

def test_committed_example_is_conserved():
    bars, ribbons = _assert_conserved(EXAMPLE.read_text("utf-8"))
    assert len(bars) == 7 and len(ribbons) == 10


def test_fixture_is_conserved(tmp_path):
    _assert_conserved(_render(tmp_path).read_text("utf-8"))


def test_two_stage_sankey_is_conserved(tmp_path):
    out = _render(
        tmp_path, ["Source", "Destination"],
        [{"id": "a", "stage": 0, "label": "Team A", "value": 30},
         {"id": "b", "stage": 0, "label": "Team B", "value": 70},
         {"id": "x", "stage": 1, "label": "Product", "value": 60},
         {"id": "y", "stage": 1, "label": "Platform", "value": 40}],
        [{"src": "a", "dst": "x", "value": 20},
         {"src": "a", "dst": "y", "value": 10},
         {"src": "b", "dst": "x", "value": 40},
         {"src": "b", "dst": "y", "value": 30}],
        name="two.svg", title="Headcount")
    _assert_conserved(out.read_text("utf-8"))
    assert check_svg(out) == []


def test_focal_ribbons_are_accent_painted_last_and_named(tmp_path):
    svg = _render(tmp_path, focal=["q", "ad", "ref"]).read_text("utf-8")
    _, ribbons = _parse(svg)
    flags = [r["focal"] for r in ribbons]
    assert flags.count(True) == 2
    assert flags == sorted(flags), "focal ribbons must be painted last"
    assert all(r["stroke"] is None for r in ribbons), "ribbons carry no stroke"
    assert len({r["fill"] for r in ribbons}) == 2   # muted + one accent
    assert "Highlighted: Sessions → Ad click → Reformulated" in svg
    assert "marker" not in svg, "no arrowheads on a Sankey"


def test_focal_accepts_flow_ids(tmp_path):
    svg = _render(tmp_path, focal=["no->gone"]).read_text("utf-8")
    assert sum(r["focal"] for r in _parse(svg)[1]) == 1


def test_thin_flow_grows_the_plot_to_four_pixels(tmp_path):
    nodes = [{"id": "a", "stage": 0, "value": 1000},
             {"id": "x", "stage": 1, "value": 990},
             {"id": "y", "stage": 1, "value": 10}]
    flows = [{"src": "a", "dst": "x", "value": 990},
             {"src": "a", "dst": "y", "value": 10}]
    svg = _render(tmp_path, ["S", "T"], nodes, flows).read_text("utf-8")
    _, ribbons = _assert_conserved(svg)
    assert min(r["bot"][0][1] - r["top"][0][1] for r in ribbons) >= 4 - 1e-6


def test_middle_labels_sit_clear_of_every_ribbon(tmp_path):
    from muriel.tools.diagrams._labels import verify_svg_labels
    for svg in (EXAMPLE.read_text("utf-8"),
                _render(tmp_path).read_text("utf-8")):
        assert verify_svg_labels(svg).ok


# ─── Validation errors carry the numbers ────────────────────────────

def test_four_stages_raise_with_a_split_suggestion(tmp_path):
    with pytest.raises(ValueError, match="split into two linked"):
        _render(tmp_path, ["a", "b", "c", "d"])


def test_one_stage_raises(tmp_path):
    with pytest.raises(ValueError, match="2–3 stages"):
        _render(tmp_path, ["only"])


def test_over_node_budget_raises(tmp_path):
    nodes = [{"id": "src", "stage": 0, "value": 9}] + [
        {"id": f"n{i}", "stage": 1, "value": 1} for i in range(9)]
    flows = [{"src": "src", "dst": f"n{i}", "value": 1} for i in range(9)]
    with pytest.raises(ValueError, match="≤8 nodes"):
        _render(tmp_path, ["a", "b"], nodes, flows)


def test_over_flow_budget_raises(tmp_path):
    nodes = ([{"id": f"a{i}", "stage": 0, "value": 4} for i in range(4)]
             + [{"id": f"b{j}", "stage": 1, "value": 4} for j in range(4)])
    flows = [{"src": f"a{i}", "dst": f"b{j}", "value": 1}
             for i in range(4) for j in range(4)]
    with pytest.raises(ValueError, match="≤12 flows"):
        _render(tmp_path, ["a", "b"], nodes, flows)


def test_unequal_stage_totals_raise_with_numbers(tmp_path):
    nodes = [dict(n) for n in NODES]
    nodes[-1]["value"] = 90
    with pytest.raises(ValueError, match=r"Query = 1,000.*Outcome = 990"):
        _render(tmp_path, nodes=nodes)


def test_leaky_middle_node_raises_with_numbers(tmp_path):
    # Stage totals still agree; only the middle nodes leak. Ad click sends
    # 10 fewer than it receives and No click 10 more.
    flows = [dict(f) for f in FLOWS]
    flows[5]["value"] = 60      # ad -> sat
    flows[7]["value"] = 80      # no -> sat
    with pytest.raises(ValueError, match=r"'ad' is 150 but sends 140"):
        _render(tmp_path, flows=flows)


def test_non_adjacent_flow_raises(tmp_path):
    nodes = [{"id": "a", "stage": 0, "value": 1}, {"id": "b", "stage": 1, "value": 1},
             {"id": "c", "stage": 2, "value": 1}]
    flows = [{"src": "a", "dst": "c", "value": 1}, {"src": "b", "dst": "c", "value": 1}]
    with pytest.raises(ValueError, match="adjacent stages"):
        _render(tmp_path, ["x", "y", "z"], nodes, flows)


def test_invisible_ribbon_raises_instead_of_folding(tmp_path):
    nodes = [{"id": "a", "stage": 0, "value": 100000},
             {"id": "x", "stage": 1, "value": 99999},
             {"id": "y", "stage": 1, "value": 1}]
    flows = [{"src": "a", "dst": "x", "value": 99999},
             {"src": "a", "dst": "y", "value": 1}]
    with pytest.raises(ValueError, match=r"'a->y'.*'Other'"):
        _render(tmp_path, ["S", "T"], nodes, flows)


def test_focal_that_is_not_a_path_raises(tmp_path):
    with pytest.raises(ValueError, match="not a flow"):
        _render(tmp_path, focal=["q", "gone"])
    with pytest.raises(ValueError, match="path of"):
        _render(tmp_path, focal=["nope"])


# ─── Determinism, a11y, the gate ────────────────────────────────────

def test_rendering_is_byte_identical_twice(tmp_path):
    a = _render(tmp_path, name="a.svg", focal=["q", "no", "gone"]).read_bytes()
    b = _render(tmp_path, name="a.svg", focal=["q", "no", "gone"]).read_bytes()
    assert a == b


def test_a11y_lint_is_clean(tmp_path):
    svg = _render(tmp_path, title="Sessions").read_text("utf-8")
    assert lint_a11y(svg) == []
    assert lint_a11y(EXAMPLE.read_text("utf-8")) == []


def test_default_desc_lists_the_spec_and_claims_nothing(tmp_path):
    svg = _render(tmp_path).read_text("utf-8")
    desc = re.search(r"<desc [^>]*>(.*?)</desc>", svg).group(1)
    for word in ("Sessions", "Reformulated", "1,000"):
        assert word in desc
    assert not re.search(r"\b(causes?|significant|best|better|proves?)\b", desc)


def test_diagram_check_is_clean(tmp_path):
    assert check_svg(EXAMPLE) == []
    assert check_svg(_render(tmp_path, focal=["q", "ad", "ref"],
                             unit="sessions", title="Fixture")) == []


@pytest.mark.parametrize("toml", ["muriel-brand.toml", "example-brand.toml",
                                  "scrutinizer-brand.toml"])
def test_brand_tokens_drive_colour(tmp_path, toml):
    from muriel.styleguide import load_styleguide
    brand = load_styleguide(Path(__file__).resolve().parents[1]
                            / "plugins/muriel/skills/compose/examples" / toml)
    out = _render(tmp_path, brand=brand, focal=["q", "ad", "ref"],
                  unit="sessions")
    svg = out.read_text("utf-8")
    assert brand.colors.background.lower() in svg.lower()
    assert "#0a0a0f" not in svg or brand.colors.background.lower() == "#0a0a0f"
    assert check_svg(out) == []


def test_cli_parity(tmp_path):
    import json

    from muriel.tools.diagrams.sankey import _main
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"stages": STAGES, "nodes": NODES,
                                "flows": FLOWS, "focal": ["q", "ad", "ref"],
                                "unit": "sessions", "title": "CLI"}))
    cli_out = tmp_path / "cli.svg"
    assert _main([str(spec), str(cli_out)]) == 0
    (tmp_path / "py").mkdir()
    py_out = _render(tmp_path / "py", name="cli.svg", focal=["q", "ad", "ref"],
                     unit="sessions", title="CLI")
    assert cli_out.read_bytes() == py_out.read_bytes()


def test_committed_example_is_byte_identical(tmp_path):
    """The example regenerates from its spec in render_diagram_examples.py."""
    import importlib.util
    script = (Path(__file__).resolve().parents[1]
              / "scripts/render_diagram_examples.py")
    spec = importlib.util.spec_from_file_location("_rde_sankey", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rendered = mod.render_examples(tmp_path)["sankey-search-sessions.svg"]
    assert Path(rendered).read_bytes() == EXAMPLE.read_bytes(), (
        "regenerate on purpose: python3 scripts/render_diagram_examples.py")
