"""Causal / dependency DAG generator: layout invariants read back from the SVG.

Every geometric claim here is checked on the rendered file, not on the
generator's internal arithmetic: node boxes come from ``<g data-id
data-rank>`` groups, connectors from ``<path data-src data-dst>``, with the
rounded corners sampled along their curves.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from muriel.tools.diagrams import dag
from muriel.tools.diagrams._a11y import lint_a11y
from muriel.tools.diagrams.check import check_svg
from muriel.tools.diagrams.dag import MAX_EDGES, MAX_NODES

NS = "{http://www.w3.org/2000/svg}"
# A causal model with two convergent nodes, a long edge, and a feedback loop.
SERP_NODES = [
    {"id": "amb", "label": "Query ambiguity", "sublabel": "intent entropy"},
    {"id": "layout", "label": "SERP layout", "sublabel": "module mix"},
    {"id": "ads", "label": "Ad density", "sublabel": "ads above fold"},
    {"id": "dwell", "label": "Dwell time", "sublabel": "per result"},
    {"id": "click", "label": "Click"},
    {"id": "sat", "label": "Satisfaction", "sublabel": "post-task survey"},
]
SERP_EDGES = [
    {"src": "amb", "dst": "dwell"},
    {"src": "layout", "dst": "dwell"},
    {"src": "dwell", "dst": "click"},
    {"src": "ads", "dst": "click"},
    {"src": "click", "dst": "sat"},
    {"src": "sat", "dst": "amb", "back": True, "label": "reformulation"},
]

# Denser: 9 nodes, 12 edges, long edges, an edge label, crossings to reduce.
STRESS_NODES = [{"id": c, "label": f"Node {c.upper()}"} for c in "abcdefghi"]
STRESS_EDGES = [("a", "d"), ("b", "d"), ("b", "e"), ("c", "e"), ("a", "g"),
                ("d", "f"), ("e", "f"), ("e", "h"), ("c", "i"), ("f", "i"),
                ("g", "h"), {"src": "d", "dst": "g", "label": "gates"}]

CASES = {
    "serp_down": (SERP_NODES, SERP_EDGES, "down"),
    "serp_right": (SERP_NODES, SERP_EDGES, "right"),
    "stress_down": (STRESS_NODES, STRESS_EDGES, "down"),
    "stress_right": (STRESS_NODES, STRESS_EDGES, "right"),
}


# ─── Read-back helpers ──────────────────────────────────────────────

def _parse(path):
    root = ET.fromstring(Path(path).read_text(encoding="utf-8"))
    nodes = {}
    for g in root.iter(f"{NS}g"):
        if g.get("data-id") is None:
            continue
        rect = g.find(f"{NS}rect")
        x, y = float(rect.get("x")), float(rect.get("y"))
        w, h = float(rect.get("width")), float(rect.get("height"))
        nodes[g.get("data-id")] = {"rank": int(g.get("data-rank")),
                                   "box": (x, y, x + w, y + h)}
    edges = []
    for p in root.iter(f"{NS}path"):
        if p.get("data-src") is None:
            continue
        edges.append({"src": p.get("data-src"), "dst": p.get("data-dst"),
                      "back": p.get("data-back") == "true",
                      "pts": _polyline(p.get("d"))})
    return root, nodes, edges


def _polyline(d):
    """Path ``d`` (M / L / Q only) as points, sampling each quadratic."""
    toks = re.findall(r"[MLQ]|-?\d+(?:\.\d+)?", d)
    pts, i, cmd = [], 0, None
    while i < len(toks):
        if toks[i] in "MLQ":
            cmd = toks[i]
            i += 1
        if cmd in "ML":
            pts.append((float(toks[i]), float(toks[i + 1])))
            i += 2
        else:  # Q cx cy x y
            (x0, y0) = pts[-1]
            cx, cy, x1, y1 = map(float, toks[i:i + 4])
            i += 4
            for k in range(1, 9):
                t = k / 8
                pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
                            (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1))
    return pts


def _seg_hits_box(a, b, box, inset=0.5):
    """Does segment a→b enter the interior of ``box``? (Liang–Barsky.)"""
    x0, y0, x1, y1 = box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if p == 0:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return False
    return True


@pytest.fixture(params=sorted(CASES))
def rendered(request, tmp_path):
    nodes, edges, direction = CASES[request.param]
    out = dag(nodes, edges, direction=direction,
              out_path=tmp_path / f"{request.param}.svg")
    return request.param, direction, out


# ─── Layout invariants ──────────────────────────────────────────────

def _longest_path_ranks(nodes, edges):
    ids = [n["id"] for n in nodes]
    fwd = []
    for e in edges:
        if isinstance(e, tuple):
            fwd.append(e)
        elif not e.get("back"):
            fwd.append((e["src"], e["dst"]))
    rank = {i: 0 for i in ids}
    for _ in ids:                       # Bellman-style relaxation, ≤ n passes
        for s, d in fwd:
            rank[d] = max(rank[d], rank[s] + 1)
    return rank


def test_ranks_equal_longest_path_depth(rendered):
    name, _, out = rendered
    nodes, edges, _ = CASES[name]
    _, drawn, _ = _parse(out)
    want = _longest_path_ranks(nodes, edges)
    assert {k: v["rank"] for k, v in drawn.items()} == want


def test_forward_edges_only_advance(rendered):
    """Down: y never decreases along a forward edge. Right: x never does."""
    _, direction, out = rendered
    _, nodes, edges = _parse(out)
    axis = 1 if direction == "down" else 0
    for e in edges:
        if e["back"]:
            continue
        vals = [p[axis] for p in e["pts"]]
        assert all(b >= a - 1e-6 for a, b in zip(vals, vals[1:])), e
        # and it lands on the destination's entry side
        box = nodes[e["dst"]]["box"]
        assert abs(e["pts"][-1][axis] - box[axis]) <= 1.5


def test_segments_are_orthogonal_between_corners(rendered):
    _, _, out = rendered
    root = ET.fromstring(Path(out).read_text(encoding="utf-8"))
    for p in root.iter(f"{NS}path"):
        if p.get("data-src") is None:
            continue
        toks = re.findall(r"[MLQ]|-?\d+(?:\.\d+)?", p.get("d"))
        # every L lands axis-aligned with the point before it
        pts, i, cmd = [], 0, None
        while i < len(toks):
            if toks[i] in "MLQ":
                cmd = toks[i]
                i += 1
            n = 4 if cmd == "Q" else 2
            vals = list(map(float, toks[i:i + n]))
            i += n
            if cmd == "L":
                x0, y0 = pts[-1]
                assert abs(vals[0] - x0) < 0.05 or abs(vals[1] - y0) < 0.05, p.get("d")
            pts.append((vals[-2], vals[-1]))


def test_no_edge_passes_through_a_non_endpoint_box(rendered):
    _, _, out = rendered
    _, nodes, edges = _parse(out)
    for e in edges:
        for nid, nd in nodes.items():
            if nid in (e["src"], e["dst"]):
                continue
            for a, b in zip(e["pts"], e["pts"][1:]):
                assert not _seg_hits_box(a, b, nd["box"]), (e["src"], e["dst"], nid)


def test_attach_points_on_one_side_are_at_least_12px_apart(rendered):
    _, direction, out = rendered
    _, nodes, edges = _parse(out)
    cross = 0 if direction == "down" else 1
    sides: dict = {}
    for e in edges:
        sides.setdefault((e["src"], "out"), []).append(e["pts"][0][cross])
        sides.setdefault((e["dst"], "in"), []).append(e["pts"][-1][cross])
    for key, us in sides.items():
        us = sorted(us)
        for a, b in zip(us, us[1:]):
            assert b - a >= 12 - 1e-6, (key, us)


def test_back_edge_routes_outside_every_box(tmp_path):
    out = dag(SERP_NODES, SERP_EDGES, out_path=tmp_path / "b.svg")
    _, nodes, edges = _parse(out)
    back = [e for e in edges if e["back"]]
    assert len(back) == 1
    right_of_all = max(nd["box"][2] for nd in nodes.values())
    assert max(p[0] for p in back[0]["pts"]) > right_of_all
    svg = Path(out).read_text(encoding="utf-8")
    assert 'stroke-dasharray="5,4"' in svg
    assert svg.count('stroke-dasharray') == 1


def test_fan_in_badge_marks_every_convergent_node(tmp_path):
    out = dag(SERP_NODES, SERP_EDGES, out_path=tmp_path / "f.svg")
    root, _, _ = _parse(out)
    badged = {g.get("data-id"): "".join(t.text for t in g.iter(f"{NS}text"))
              for g in root.iter(f"{NS}g") if g.get("data-id")}
    assert "2 in" in badged["dwell"]
    assert "2 in" in badged["click"]
    # a single input (here, only the feedback edge) is not convergence
    assert " in" not in badged["amb"]
    assert " in" not in badged["layout"]


def test_edges_carry_endpoints_and_draw_before_nodes(tmp_path):
    svg = Path(dag(SERP_NODES, SERP_EDGES, out_path=tmp_path / "o.svg")
               ).read_text(encoding="utf-8")
    assert 'data-src="amb" data-dst="dwell"' in svg
    assert svg.rfind("data-src=") < svg.find("data-id=")
    assert 'id="o-arrow"' in svg and 'url(#o-arrow)' in svg


def test_layout_is_deterministic(tmp_path):
    a = Path(dag(STRESS_NODES, STRESS_EDGES, out_path=tmp_path / "x" / "d.svg")
             ).read_bytes()
    b = Path(dag(STRESS_NODES, STRESS_EDGES, out_path=tmp_path / "y" / "d.svg")
             ).read_bytes()
    assert a == b


def test_barycenter_removes_an_avoidable_crossing(tmp_path):
    # Input order invites a crossing (a→y, b→x with x listed first); the
    # ordering pass must untangle it.
    nodes = ["a", "b", "x", "y", "z"]
    edges = [("a", "y"), ("b", "x"), ("a", "z"), ("b", "z")]
    _, drawn, _ = _parse(dag(nodes, edges, out_path=tmp_path / "c.svg"))
    ax, bx = drawn["a"]["box"][0], drawn["b"]["box"][0]
    xx, yx = drawn["x"]["box"][0], drawn["y"]["box"][0]
    assert (ax < bx) == (yx < xx)


def test_labels_grow_boxes_and_never_escape(tmp_path):
    nodes = [{"id": "a", "label": "Supercalifragilisticexpialidocious"},
             {"id": "b", "label": "a rather long label that has to wrap twice"},
             {"id": "c", "label": "C", "sublabel": "v3.23 · npm registry mirror"}]
    out = dag(nodes, [("a", "c"), ("b", "c")], out_path=tmp_path / "g.svg")
    assert check_svg(out) == []


# ─── Gates: every generated figure passes the same checks as the rest ─

def test_a11y_and_diagram_check_clean(rendered):
    _, _, out = rendered
    assert lint_a11y(Path(out).read_text(encoding="utf-8")) == []
    assert check_svg(out) == []


# ─── Validation ─────────────────────────────────────────────────────

def test_forward_cycle_raises_and_names_it(tmp_path):
    with pytest.raises(ValueError, match=r"cycle: a → b → c → a"):
        dag(["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")],
            out_path=tmp_path / "x.svg")


def test_one_back_edge_expresses_the_cycle(tmp_path):
    out = dag(["a", "b", "c"],
              [("a", "b"), ("b", "c"), {"src": "c", "dst": "a", "back": True}],
              out_path=tmp_path / "x.svg")
    assert check_svg(out) == []


def test_back_edge_that_closes_no_cycle_raises(tmp_path):
    with pytest.raises(ValueError, match="closes no cycle"):
        dag(["a", "b", "c"],
            [("a", "c"), ("b", "c"), {"src": "a", "dst": "b", "back": True}],
            out_path=tmp_path / "x.svg")


def test_unknown_id_and_self_loop_raise(tmp_path):
    with pytest.raises(ValueError, match="unknown node id 'q'"):
        dag(["a", "b"], [("a", "q")], out_path=tmp_path / "x.svg")
    with pytest.raises(ValueError, match="self-loop"):
        dag(["a", "b"], [("a", "a")], out_path=tmp_path / "x.svg")


def test_tree_precondition_raises_with_an_escape(tmp_path):
    tree = [("r", "a"), ("r", "b"), ("a", "c")]
    with pytest.raises(ValueError, match="dendrogram"):
        dag(["r", "a", "b", "c"], tree, out_path=tmp_path / "t.svg")
    with pytest.raises(ValueError, match="swimlane"):
        dag(["a", "b", "c"], [("a", "b"), ("b", "c")], out_path=tmp_path / "t.svg")
    out = dag(["r", "a", "b", "c"], tree, allow_tree=True,
              out_path=tmp_path / "t.svg")
    assert check_svg(out) == []


@pytest.mark.parametrize("kind", ["nodes", "edges", "ranks", "back"])
def test_budget_errors_carry_split_guidance(tmp_path, kind):
    if kind == "nodes":
        nodes = [str(i) for i in range(MAX_NODES + 1)]
        edges = [("0", "2"), ("1", "2")]
        msg = "at most 9 nodes.*[Ss]plit"
    elif kind == "edges":
        nodes = [str(i) for i in range(8)]
        edges = [(str(a), str(b)) for a in range(4) for b in range(4, 8)]
        assert len(edges) > MAX_EDGES
        msg = "at most 14 edges"
    elif kind == "ranks":
        nodes = ["a", "b", "c", "d", "e", "x"]
        edges = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("x", "e")]
        msg = "spans 5 ranks.*[Ss]plit"
    else:
        nodes = ["a", "b", "c"]
        edges = [("a", "b"), ("b", "c"),
                 {"src": "c", "dst": "a", "back": True},
                 {"src": "b", "dst": "a", "back": True}]
        msg = "at most 1 back-edge"
    with pytest.raises(ValueError, match=msg):
        dag(nodes, edges, out_path=tmp_path / "x.svg")


def test_one_accent_only(tmp_path):
    with pytest.raises(ValueError, match="one focal"):
        dag([{"id": "a", "focal": True}, {"id": "b", "focal": True}, "c"],
            [("a", "c"), ("b", "c")], out_path=tmp_path / "x.svg")
    with pytest.raises(ValueError, match="accent"):
        dag([{"id": "a", "focal": True}, "b", "c"],
            [("a", "b"), ("b", "c"), {"src": "c", "dst": "a", "back": True}],
            out_path=tmp_path / "x.svg")


def test_direction_is_validated(tmp_path):
    with pytest.raises(ValueError, match="direction"):
        dag(["a", "b", "c"], [("a", "c"), ("b", "c")], direction="up",
            out_path=tmp_path / "x.svg")
