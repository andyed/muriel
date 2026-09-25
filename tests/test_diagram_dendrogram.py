"""dendrogram: tidy-tree geometry, elbow-bus connectors, budgets, collapse.

Every geometric assertion reads the rendered SVG back (``data-node`` groups
and ``data-edge`` lines) rather than the generator's internal arrays, so a
layout that computes the right number but writes the wrong coordinate
still fails.
"""

import itertools
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from muriel.tools.diagrams import dendrogram
from muriel.tools.diagrams._a11y import lint_a11y
from muriel.tools.diagrams.check import check_svg

NS = "{http://www.w3.org/2000/svg}"

EYE = {"label": "Eye-movement events", "sublabel": "oculomotor record",
       "children": [
           {"label": "Fixation", "sublabel": "gaze held", "children": [
               {"label": "Microsaccade", "focal": True}, "Drift", "Tremor"]},
           {"label": "Saccade", "children": ["Reflexive", "Volitional"]},
           {"label": "Smooth pursuit", "children": ["Open-loop", "Closed-loop"]},
           {"label": "Blink", "children": ["Spontaneous", "Reflex", "Voluntary"]},
       ]}

# Uneven on purpose: a deep narrow branch, a wide branch, a shallow leaf,
# one very long label (forces the two-width scheme), one single-child chain.
UNEVEN = {"label": "Root with a long heading", "children": [
    {"label": "A deep branch", "children": [
        {"label": "Level two", "children": [
            "Leaf one", "Containerization/orchestration"]}]},
    {"label": "Wide", "children": ["x", "y", "z", "w", "v"]},
    "Shallow leaf"]}


def _parse(path):
    root = ET.parse(path).getroot()
    nodes = {}
    for g in root.iter(f"{NS}g"):
        nid = g.get("data-node")
        if nid is None:
            continue
        r = g.find(f"{NS}rect")
        x, y = float(r.get("x")), float(r.get("y"))
        w, h = float(r.get("width")), float(r.get("height"))
        nodes[nid] = {
            "depth": int(g.get("data-depth")),
            "parent": g.get("data-parent"),
            "collapsed": g.get("data-collapsed"),
            "box": (x, y, x + w, y + h),
            "text": [" ".join("".join(t.itertext()).split())
                     for t in g.iter(f"{NS}text")],
        }
    lines = []
    for ln in root.iter(f"{NS}line"):
        if ln.get("data-edge") is None:
            continue
        lines.append({
            "edge": ln.get("data-edge"), "from": ln.get("data-from"),
            "to": ln.get("data-to"),
            "p1": (float(ln.get("x1")), float(ln.get("y1"))),
            "p2": (float(ln.get("x2")), float(ln.get("y2"))),
        })
    return root, nodes, lines


def _children(nodes, pid):
    # Pre-order ids are n0, n1, …; sort numerically for drawing order.
    return sorted((k for k, v in nodes.items() if v["parent"] == pid),
                  key=lambda k: int(k[1:]))


def _centre(box, axis):
    return (box[0] + box[2]) / 2 if axis == "x" else (box[1] + box[3]) / 2


@pytest.fixture(params=[("eye", "down"), ("eye", "right"),
                        ("uneven", "down"), ("uneven", "right")])
def rendered(request, tmp_path):
    name, orient = request.param
    tree = EYE if name == "eye" else UNEVEN
    out = tmp_path / f"{name}-{orient}.svg"
    dendrogram(tree, orientation=orient, title=f"{name} {orient}", out_path=out)
    return out, orient


# ─── Layout ─────────────────────────────────────────────────────────

def test_parents_are_centred_on_their_first_and_last_child(rendered):
    path, orient = rendered
    _, nodes, _ = _parse(path)
    axis = "x" if orient == "down" else "y"
    checked = 0
    for pid, p in nodes.items():
        kids = _children(nodes, pid)
        if not kids:
            continue
        mid = (_centre(nodes[kids[0]]["box"], axis)
               + _centre(nodes[kids[-1]]["box"], axis)) / 2
        assert abs(_centre(p["box"], axis) - mid) <= 0.5, pid
        checked += 1
    assert checked >= 3


def test_no_two_boxes_overlap(rendered):
    path, _ = rendered
    _, nodes, _ = _parse(path)
    boxes = [n["box"] for n in nodes.values()]
    for a, b in itertools.combinations(boxes, 2):
        disjoint = a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]
        assert disjoint, (a, b)


def test_levels_are_never_skipped_and_ranks_are_evenly_spaced(rendered):
    path, orient = rendered
    _, nodes, _ = _parse(path)
    for n in nodes.values():
        if n["parent"] is not None:
            assert n["depth"] == nodes[n["parent"]]["depth"] + 1
    # Rank start (top edge / left edge) is shared by every node of a depth.
    idx = 1 if orient == "down" else 0
    starts = {}
    for n in nodes.values():
        starts.setdefault(n["depth"], set()).add(round(n["box"][idx], 1))
    assert all(len(s) == 1 for s in starts.values()), starts
    ordered = [next(iter(starts[d])) for d in sorted(starts)]
    if orient == "down":
        steps = {round(b - a, 1) for a, b in zip(ordered, ordered[1:])}
        assert len(steps) == 1, steps
    else:
        # Columns may differ in width (two-width scheme); the *gap* between
        # a column's right edge and the next column's left edge is constant.
        right = {}
        for n in nodes.values():
            right[n["depth"]] = max(right.get(n["depth"], 0), n["box"][2])
        gaps = {round(ordered[d + 1] - right[d], 1) for d in range(len(ordered) - 1)}
        assert len(gaps) == 1, gaps


def test_at_most_two_box_widths(rendered):
    path, _ = rendered
    _, nodes, _ = _parse(path)
    widths = {round(n["box"][2] - n["box"][0], 1) for n in nodes.values()}
    assert len(widths) <= 2, widths
    assert min(widths) >= 120
    heights = {round(n["box"][3] - n["box"][1], 1) for n in nodes.values()}
    assert len(heights) == 1 and 40 <= heights.pop() <= 52


def test_long_labels_pick_the_two_width_scheme(tmp_path):
    out = tmp_path / "u.svg"
    dendrogram(UNEVEN, out_path=out)
    _, nodes, _ = _parse(out)
    assert len({round(n["box"][2] - n["box"][0], 1) for n in nodes.values()}) == 2


# ─── Connectors ─────────────────────────────────────────────────────

def test_connectors_are_axis_aligned_elbow_buses(rendered):
    path, orient = rendered
    root, nodes, lines = _parse(path)
    assert not list(root.iter(f"{NS}path")), "connectors must be <line>, no curves"
    for ln in lines:
        (x1, y1), (x2, y2) = ln["p1"], ln["p2"]
        assert x1 == x2 or y1 == y2, f"diagonal connector {ln}"

    down = orient == "down"
    for pid, p in nodes.items():
        kids = _children(nodes, pid)
        if not kids:
            continue
        mine = [ln for ln in lines if ln["from"] == pid]
        stems = [ln for ln in mine if ln["edge"] == "stem"]
        buses = [ln for ln in mine if ln["edge"] == "bus"]
        drops = {ln["to"]: ln for ln in mine if ln["edge"] == "drop"}
        assert len(stems) == 1
        assert set(drops) == set(kids), "every child gets exactly one drop"
        stem = stems[0]
        px0, py0, px1, py1 = p["box"]
        if down:
            bus_level = stem["p2"][1]
            assert stem["p1"] == ((px0 + px1) / 2, py1) or \
                abs(stem["p1"][0] - (px0 + px1) / 2) <= 0.05
            assert abs(stem["p1"][1] - py1) <= 0.05
            assert py1 < bus_level
        else:
            bus_level = stem["p2"][0]
            assert abs(stem["p1"][0] - px1) <= 0.05
            assert abs(stem["p1"][1] - (py0 + py1) / 2) <= 0.05
            assert px1 < bus_level
        if len(kids) > 1:
            assert len(buses) == 1
            bus = buses[0]
            lvl = 1 if down else 0
            assert bus["p1"][lvl] == bus["p2"][lvl] == bus_level
        for c in kids:
            d = drops[c]
            cx0, cy0, cx1, cy1 = nodes[c]["box"]
            if down:
                assert d["p1"][1] == bus_level
                assert abs(d["p2"][1] - cy0) <= 0.05, "drop ends on child's top edge"
                assert abs(d["p1"][0] - (cx0 + cx1) / 2) <= 0.05
                assert cy0 > bus_level
            else:
                assert d["p1"][0] == bus_level
                assert abs(d["p2"][0] - cx0) <= 0.05, "drop ends on child's left edge"
                assert abs(d["p1"][1] - (cy0 + cy1) / 2) <= 0.05
                assert cx0 > bus_level


def test_connectors_are_drawn_before_nodes(tmp_path):
    out = tmp_path / "t.svg"
    dendrogram(EYE, out_path=out)
    order = [el.get("data-edge") and "edge" or el.get("data-node") and "node"
             for el in ET.parse(out).getroot().iter()
             if el.get("data-edge") or el.get("data-node")]
    assert order.index("node") > len(order) - 1 - order[::-1].index("edge")


def test_one_accent_and_data_depth(tmp_path):
    out = tmp_path / "t.svg"
    dendrogram(EYE, out_path=out)
    svg = out.read_text()
    assert svg.count('data-focal="true"') == 1
    assert svg.count('stroke="#7dd4e4"') == 1
    _, nodes, _ = _parse(out)
    assert {n["depth"] for n in nodes.values()} == {0, 1, 2}


# ─── Budgets and epistemic gates ────────────────────────────────────

def _chain(depth, breadth=2):
    node = {"label": f"L{depth - 1}"}
    for d in range(depth - 2, -1, -1):
        node = {"label": f"L{d}", "children": [node] + [f"s{d}-{k}" for k in range(breadth - 1)]}
    return node


def test_depth_budget(tmp_path):
    dendrogram(_chain(4), out_path=tmp_path / "ok.svg")
    with pytest.raises(ValueError, match=r"5 levels deep.*[Ss]plit"):
        dendrogram(_chain(5), out_path=tmp_path / "bad.svg")


def test_breadth_budget_points_at_collapse_over(tmp_path):
    tree = {"label": "R", "children": [f"c{i}" for i in range(6)]}
    with pytest.raises(ValueError, match="collapse_over"):
        dendrogram(tree, out_path=tmp_path / "bad.svg")


def test_leaf_extent_budget_is_computed(tmp_path):
    # 5 × 5 = 25 leaves at ≥144px pitch cannot fit 1920px downward.
    tree = {"label": "R", "children": [
        {"label": f"g{i}", "children": [f"g{i}-{k}" for k in range(5)]}
        for i in range(5)]}
    with pytest.raises(ValueError, match=r"25 leaves.*collapse_over.*orientation='right'"):
        dendrogram(tree, out_path=tmp_path / "bad.svg")
    # Folding each group to 3 visible leaves brings it under budget.
    dendrogram(tree, collapse_over=3, out_path=tmp_path / "ok.svg")


def test_single_path_is_a_process_not_a_tree(tmp_path):
    with pytest.raises(ValueError, match="process"):
        dendrogram({"label": "a", "children": [{"label": "b", "children": ["c"]}]},
                   out_path=tmp_path / "bad.svg")


def test_a_node_with_two_parents_routes_to_dag(tmp_path):
    shared = {"label": "Shared prerequisite"}
    tree = {"label": "R", "children": [
        {"label": "A", "children": [shared, "a2"]},
        {"label": "B", "children": [shared, "b2"]}]}
    with pytest.raises(ValueError, match="dag"):
        dendrogram(tree, out_path=tmp_path / "bad.svg")


def test_a_repeated_label_under_two_parents_warns(tmp_path):
    tree = {"label": "R", "children": [
        {"label": "A", "children": ["Other", "a2"]},
        {"label": "B", "children": ["Other", "b2"]}]}
    with pytest.warns(UserWarning, match="dag"):
        dendrogram(tree, out_path=tmp_path / "w.svg")


def test_focal_rules(tmp_path):
    two = {"label": "R", "children": [{"label": "a", "focal": True},
                                      {"label": "b", "focal": True}]}
    with pytest.raises(ValueError, match="one accent"):
        dendrogram(two, out_path=tmp_path / "x.svg")
    middle = {"label": "R", "children": [
        {"label": "a", "focal": True, "children": ["a1", "a2"]}, "b"]}
    with pytest.raises(ValueError, match="middle tier"):
        dendrogram(middle, out_path=tmp_path / "y.svg")
    root = {"label": "R", "focal": True, "children": ["a", "b"]}
    dendrogram(root, out_path=tmp_path / "z.svg")


# ─── collapse_over ──────────────────────────────────────────────────

def test_collapse_over_folds_the_tail_into_one_more_node(tmp_path):
    tree = {"label": "R", "children": [
        {"label": "k1", "children": ["deep1", "deep2"]}, "k2", "k3",
        {"label": "h1", "children": ["hidden-deep"]}, "h2", "h3", "h4"]}
    out = tmp_path / "c.svg"
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        dendrogram(tree, collapse_over=4, out_path=out)
    _, nodes, _ = _parse(out)
    kids = _children(nodes, "n0")
    assert len(kids) == 4
    assert [nodes[k]["text"][0] for k in kids] == ["k1", "k2", "k3", "+4 more"]
    more = nodes[kids[-1]]
    assert more["collapsed"] == "4" and not _children(nodes, kids[-1])
    labels = {t for n in nodes.values() for t in n["text"]}
    assert "hidden-deep" not in labels and "deep1" in labels
    svg = out.read_text()
    assert 'stroke-dasharray' in svg
    # The folded names survive in the accessible description.
    desc = ET.parse(out).getroot().find(f"{NS}desc").text
    assert "4 more not shown (h1, h2, h3, h4)" in desc


def test_collapse_over_leaves_small_families_alone(tmp_path):
    a, b = tmp_path / "a.svg", tmp_path / "b.svg"
    dendrogram(EYE, out_path=a)
    dendrogram(EYE, collapse_over=5, out_path=b)
    assert a.read_text().replace("b-title", "a-title").replace("b-desc", "a-desc") \
        == b.read_text().replace("b-title", "a-title").replace("b-desc", "a-desc")


def test_collapse_over_validation(tmp_path):
    for bad in (1, 6, 2.5, True):
        with pytest.raises(ValueError, match="collapse_over"):
            dendrogram(EYE, collapse_over=bad, out_path=tmp_path / "x.svg")
    tree = {"label": "R", "children": ["a", "b", "c", {"label": "d", "focal": True}]}
    with pytest.raises(ValueError, match="focal"):
        dendrogram(tree, collapse_over=3, out_path=tmp_path / "y.svg")


# ─── Determinism, a11y, the gate ────────────────────────────────────

def test_rendering_is_deterministic(tmp_path):
    a = Path(dendrogram(UNEVEN, title="T", out_path=tmp_path / "same.svg")).read_bytes()
    b = Path(dendrogram(UNEVEN, title="T", out_path=tmp_path / "same.svg")).read_bytes()
    assert a == b


def test_accessible_contract_and_diagram_check(rendered):
    path, _ = rendered
    assert lint_a11y(path.read_text(encoding="utf-8")) == []
    assert check_svg(path) == []


def test_diagram_check_with_a_brand(tmp_path):
    from muriel.styleguide import load_styleguide
    toml = (Path(__file__).resolve().parents[1]
            / "plugins/muriel/skills/compose/examples/muriel-brand.toml")
    out = tmp_path / "brand.svg"
    dendrogram(EYE, brand=load_styleguide(toml), title="Branded", out_path=out)
    assert check_svg(out) == []


def test_orientation_is_validated(tmp_path):
    with pytest.raises(ValueError, match="orientation"):
        dendrogram(EYE, orientation="up", out_path=tmp_path / "x.svg")


def test_committed_example_is_byte_identical(tmp_path):
    """The committed example is regenerated from its spec, not hand-edited."""
    import importlib.util
    repo = Path(__file__).resolve().parents[1]
    script = repo / "scripts/render_diagram_examples.py"
    spec = importlib.util.spec_from_file_location("_render_dendro_examples", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    name = "dendrogram-eye-movements.svg"
    rendered = Path(mod.render_examples(tmp_path)[name]).read_text(encoding="utf-8")
    committed = (repo / "plugins/muriel/skills/compose/examples/diagrams" / name
                 ).read_text(encoding="utf-8")
    assert rendered == committed, "run python3 scripts/render_diagram_examples.py"
