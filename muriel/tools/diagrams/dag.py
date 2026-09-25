"""
muriel.tools.diagrams.dag — causal / dependency DAG as SVG.

When to use
-----------
A set of variables or components where **arrow direction is the claim**
and at least one node has **more than one parent**: query ambiguity and
SERP layout both drive dwell time; two packages both depend on one
shared library. Convergence is the thing a tree, a sequence, or a stack
cannot draw — ``swimlane`` chains steps one after another and
``layer_stack`` draws no edges at all, so neither can show a node with
two parents. That is this generator's admission ticket.

Epistemic precondition
----------------------
Every edge asserts that the source **causes, feeds, or is required by**
the destination, and the graph as a whole is acyclic except for at most
one feedback loop the author is prepared to defend. If you cannot say
what would change downstream when a source is intervened on, the arrow
is not earned.

Anti-prescription
-----------------
- **Single-parent hierarchy → dendrogram / hierarchy.** If every node has
  at most one parent and nothing loops back, the data is a tree. The
  generator raises rather than draw it (pass ``allow_tree=True`` only when
  arrow direction is itself the point), because a DAG layout implies
  convergence the data does not have.
- **Linear sequence → process or swimlane.** A chain ``a → b → c`` is a
  process; a DAG layout adds nothing but whitespace.
- **Association is not an arrow.** If edges mean "correlates with" or
  "is related to", don't draw arrowheads — use a matrix, a heat grid, or
  a plain list of pairs. An arrowhead claims direction.
- **One loop, not a hairball.** At most one back-edge, drawn dashed in the
  accent colour around the outside of the stack. Two feedback loops
  compete and neither reads; split the figure.

Layout
------
Nodes sit in rank rows by **longest-path depth** from the sources (rank 0
has no parents). Edges spanning more than one rank are routed through
virtual waypoints in the gaps between boxes. Within-rank order comes
from a barycenter heuristic over several sweeps plus adjacent-swap
refinement, tie-broken by input order, so the same spec always renders
the same file. Edges are orthogonal elbows with ``r=8`` rounded corners;
every horizontal jog runs on its own track in the channel between two
ranks, so a connector never passes behind a box it does not connect.
Multiple edges on one side of a box attach at distinct points ≥12px
apart. Nodes with two or more incoming edges carry an ``N in`` badge.

Budget: ≤9 nodes, ≤14 edges, ≤4 ranks, ≤1 back-edge. Over budget raises
with split guidance rather than drawing an illegible figure.

Geometry adapted from the MIT-licensed diagram-design skill
(``references/type-dependency.md`` and its connector rules; © 2025
Cathryn Lavery); the layout algorithm, tokens, contrast rule, and
epistemic gate are muriel's own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Optional, Union

from ._a11y import default_desc, figure_slug, legible_on, svg_open
from ._labels import (
    RATIO_MONO,
    RATIO_SANS,
    RATIO_SANS_BOLD,
    fit_text,
    grow_to_fit,
    text_width,
)

__all__ = ["dag", "MAX_NODES", "MAX_EDGES", "MAX_RANKS", "MAX_BACK_EDGES"]

_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

MAX_NODES = 9
MAX_EDGES = 14
MAX_RANKS = 4
MAX_BACK_EDGES = 1

# ─── Geometry (4px grid; floors, not limits) ────────────────────────
_BOX_W = 160          # node width floor (per rank: every box in a rank shares it)
_BOX_H = 56           # node height floor (global)
_BOX_PAD = 10         # horizontal breathing room inside a node
_LABEL_FS = 13
_LABEL_LH = 17
_SUB_FS = 11
_SUB_GAP = 16         # last label baseline → sublabel baseline
_BADGE_FS = 10
_BADGE_H = 14
_BADGE_INSET = 5
_EDGE_FS = 11
_CHANNEL_MIN = 64     # rank pitch = 56 + 64 = 120
_TRACK_GAP = 12       # parallel connectors stay ≥12px apart
_TRACK_MARGIN = 16    # first/last track to the channel's edge
_OUTER_CHANNEL = 32   # the margin channel a back-edge uses above/below the stack
_OUTER_LANE = 28      # back-edge lane distance from the widest rank
_PORT_MIN = 12        # attach points on one box side ≥12px apart
_RADIUS = 8
_PAD = 48
_ASC, _DESC = 0.80, 0.22   # muriel.layout.text_bbox's ascent/descent


# ─── Brand → tokens ─────────────────────────────────────────────────

def _resolve(brand) -> dict:
    if brand is None:
        return {
            "bg":         "#0a0a0f",
            "ink":        "#e6e4d2",
            "muted":      "#b0b0c4",
            "accent":     "#7dd4e4",
            "paper":      "rgba(230, 228, 210, 0.04)",
            "focal_fill": "rgba(125, 212, 228, 0.12)",
            "hairline":   "rgba(230, 228, 210, 0.14)",
            "stroke":     "rgba(230, 228, 210, 0.30)",
            "flow":       "rgba(176, 176, 196, 0.70)",
            "body_font":  "ui-sans-serif, -apple-system, system-ui, sans-serif",
        }
    c = brand.colors
    viz = brand.viz.categorical if brand.viz.categorical else []
    accent = viz[0] if viz else (c.foreground or "#7dd4e4")
    ink = c.foreground
    muted = c.foreground_muted or ink
    return {
        "bg":         c.background,
        "ink":        ink,
        "muted":      muted,
        "accent":     accent,
        "paper":      _rgba(ink, 0.04),
        "focal_fill": _rgba(accent, 0.12),
        "hairline":   _rgba(ink, 0.14),
        "stroke":     _rgba(ink, 0.30),
        "flow":       _rgba(muted, 0.70),
        "body_font":  brand.typography.body_family or "system-ui, sans-serif",
    }


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ─── Normalization + validation ─────────────────────────────────────

def _normalize(nodes, edges):
    if not nodes:
        raise ValueError("dag needs at least one node")
    norm_nodes: list[dict] = []
    index: dict[str, int] = {}
    for n in nodes:
        if isinstance(n, str):
            n = {"id": n}
        nid = n.get("id")
        if nid is None or str(nid) == "":
            raise ValueError(f"every node needs an 'id'; got {n!r}")
        nid = str(nid)
        if nid in index:
            raise ValueError(f"duplicate node id {nid!r}")
        index[nid] = len(norm_nodes)
        norm_nodes.append({
            "id": nid,
            "label": str(n.get("label", nid)),
            "sublabel": n.get("sublabel"),
            "focal": bool(n.get("focal", False)),
        })

    norm_edges: list[dict] = []
    seen: set[tuple[int, int]] = set()
    for e in edges:
        if isinstance(e, (tuple, list)):
            e = {"src": e[0], "dst": e[1]}
        src, dst = str(e.get("src")), str(e.get("dst"))
        for end in (src, dst):
            if end not in index:
                raise ValueError(
                    f"edge {src!r} → {dst!r} references unknown node id "
                    f"{end!r}; nodes are {list(index)}")
        if src == dst:
            raise ValueError(
                f"self-loop on {src!r}: a node cannot cause itself in a DAG; "
                f"if it is a feedback process, draw it as a cycle diagram")
        key = (index[src], index[dst])
        if key in seen:
            raise ValueError(f"duplicate edge {src!r} → {dst!r}")
        seen.add(key)
        label = e.get("label")
        norm_edges.append({
            "src": index[src], "dst": index[dst],
            "label": str(label) if label else None,
            "back": bool(e.get("back", False)),
        })
    return norm_nodes, norm_edges


def _find_cycle(n: int, fwd: list[dict]) -> Optional[list[int]]:
    """A cycle among forward edges as a node list, or ``None``.

    Iterative DFS in input order so the reported cycle is deterministic.
    """
    adj: list[list[int]] = [[] for _ in range(n)]
    for e in fwd:
        adj[e["src"]].append(e["dst"])
    color = [0] * n  # 0 unvisited, 1 on stack, 2 done
    for start in range(n):
        if color[start]:
            continue
        stack = [(start, 0)]
        path = [start]
        color[start] = 1
        while stack:
            v, i = stack[-1]
            if i < len(adj[v]):
                stack[-1] = (v, i + 1)
                w = adj[v][i]
                if color[w] == 1:
                    return path[path.index(w):] + [w]
                if color[w] == 0:
                    color[w] = 1
                    stack.append((w, 0))
                    path.append(w)
            else:
                color[v] = 2
                stack.pop()
                path.pop()
    return None


def _reaches(n: int, fwd: list[dict], a: int, b: int) -> bool:
    adj: list[list[int]] = [[] for _ in range(n)]
    for e in fwd:
        adj[e["src"]].append(e["dst"])
    todo, seen = [a], {a}
    while todo:
        v = todo.pop()
        if v == b:
            return True
        for w in adj[v]:
            if w not in seen:
                seen.add(w)
                todo.append(w)
    return False


def _validate(nodes, edges, allow_tree: bool) -> None:
    n, m = len(nodes), len(edges)
    ids = [nd["id"] for nd in nodes]
    if n > MAX_NODES:
        raise ValueError(
            f"dag holds at most {MAX_NODES} nodes (got {n}). Split it: an "
            f"overview DAG whose nodes are clusters, then one detail DAG per "
            f"cluster — or collapse a leaf cluster into one aggregate node "
            f"labelled with its count and say so in the caption.")
    if m > MAX_EDGES:
        raise ValueError(
            f"dag holds at most {MAX_EDGES} edges (got {m}). Past that the "
            f"figure is a hairball: split by sub-system, or keep only the "
            f"edges the argument needs and list the rest in the caption.")
    back = [e for e in edges if e["back"]]
    if len(back) > MAX_BACK_EDGES:
        raise ValueError(
            f"dag draws at most {MAX_BACK_EDGES} back-edge (got {len(back)}). "
            f"Two feedback loops compete and neither reads — pick the loop the "
            f"argument is about, and show the other in its own figure.")
    fwd = [e for e in edges if not e["back"]]
    cyc = _find_cycle(n, fwd)
    if cyc is not None:
        names = " → ".join(ids[i] for i in cyc)
        a, b = ids[cyc[-2]], ids[cyc[-1]]
        raise ValueError(
            f"forward edges form a cycle: {names}. A DAG may express a loop "
            f"only through one edge marked back=True (e.g. "
            f"{{'src': {a!r}, 'dst': {b!r}, 'back': True}}); if the loop is "
            f"the whole point, draw a cycle diagram instead.")
    for e in back:
        if not _reaches(n, fwd, e["dst"], e["src"]):
            raise ValueError(
                f"edge {ids[e['src']]!r} → {ids[e['dst']]!r} is marked "
                f"back=True but closes no cycle: {ids[e['dst']]!r} does not "
                f"reach {ids[e['src']]!r} through forward edges. Draw it as a "
                f"forward edge.")
    focal = [i for i, nd in enumerate(nodes) if nd["focal"]]
    if len(focal) > 1:
        raise ValueError(
            f"at most one focal node (got {', '.join(ids[i] for i in focal)}); "
            f"the accent is spent once per figure")
    if focal and back:
        raise ValueError(
            "the back-edge already carries the figure's one accent; drop "
            "focal= or draw the loop in its own figure")
    if not allow_tree and not back:
        parents = [0] * n
        for e in fwd:
            parents[e["dst"]] += 1
        if all(p <= 1 for p in parents):
            chain = (all(p == 1 for p in parents[1:]) and m == n - 1)
            hint = (" It is a single chain — a process or swimlane draws it "
                    "in less space." if chain else "")
            raise ValueError(
                "every node has at most one parent and nothing loops back, so "
                "this is a tree, not a DAG: a dendrogram / hierarchy draws it "
                "without implying a convergence the data does not have."
                + hint + " Pass allow_tree=True if arrow direction itself is "
                "the claim.")


# ─── Ranking + ordering ─────────────────────────────────────────────

def _ranks(n: int, fwd: list[dict]) -> list[int]:
    """Longest-path depth from the sources (Kahn order, input tie-break)."""
    parents: list[list[int]] = [[] for _ in range(n)]
    children: list[list[int]] = [[] for _ in range(n)]
    indeg = [0] * n
    for e in fwd:
        parents[e["dst"]].append(e["src"])
        children[e["src"]].append(e["dst"])
        indeg[e["dst"]] += 1
    rank = [0] * n
    ready = [v for v in range(n) if indeg[v] == 0]
    while ready:
        v = ready.pop(0)
        for w in children[v]:
            rank[w] = max(rank[w], rank[v] + 1)
            indeg[w] -= 1
            if indeg[w] == 0:
                ready.append(w)
        ready.sort()
    return rank


@dataclass
class _Elem:
    """A slot in a rank: a real node or a virtual waypoint of a long edge."""
    key: tuple                 # ("n", i) or ("d", edge_index, rank)
    tie: float                 # input-order tie-break
    size: float = 0.0          # extent along the cross axis
    center: float = 0.0
    up: list = field(default_factory=list)     # pieces into this elem
    down: list = field(default_factory=list)   # pieces out of this elem


@dataclass
class _Piece:
    """One rank-to-rank hop of a forward edge."""
    edge: int
    a: tuple                   # upper elem key
    b: tuple                   # lower elem key
    rank: int                  # rank of ``a``; the hop crosses channel rank+1


def _crossings(layers, pieces_between) -> int:
    total = 0
    for r in range(len(layers) - 1):
        pos_a = {k: i for i, k in enumerate(layers[r])}
        pos_b = {k: i for i, k in enumerate(layers[r + 1])}
        segs = [(pos_a[p.a], pos_b[p.b]) for p in pieces_between[r]]
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                (a1, b1), (a2, b2) = segs[i], segs[j]
                if (a1 - a2) * (b1 - b2) < 0:
                    total += 1
    return total


def _order(layers, elems, pieces_between):
    """Barycenter sweeps + adjacent swaps; deterministic, keeps the best."""
    def bary_sort(r: int, ref: int, attr: str) -> None:
        ref_pos = {k: i for i, k in enumerate(layers[ref])}
        cur = {k: i for i, k in enumerate(layers[r])}

        def key(k):
            ps = getattr(elems[k], attr)
            other = [ref_pos[p.a if attr == "up" else p.b] for p in ps]
            b = sum(other) / len(other) if other else cur[k]
            return (b, cur[k])
        layers[r].sort(key=key)

    # Initial: rank 0 in input order, later ranks by barycenter of parents.
    for r in range(len(layers)):
        layers[r].sort(key=lambda k: elems[k].tie)
    for r in range(1, len(layers)):
        bary_sort(r, r - 1, "up")

    best = [list(l) for l in layers]
    best_c = _crossings(layers, pieces_between)
    for _ in range(6):
        for r in range(len(layers) - 2, -1, -1):
            bary_sort(r, r + 1, "down")
        for r in range(1, len(layers)):
            bary_sort(r, r - 1, "up")
        c = _crossings(layers, pieces_between)
        if c < best_c:
            best, best_c = [list(l) for l in layers], c
    for r in range(len(layers)):
        layers[r][:] = best[r]

    # Adjacent-swap refinement: take any swap that strictly reduces crossings.
    improved = True
    while improved and best_c:
        improved = False
        for r in range(len(layers)):
            for i in range(len(layers[r]) - 1):
                layers[r][i], layers[r][i + 1] = layers[r][i + 1], layers[r][i]
                c = _crossings(layers, pieces_between)
                if c < best_c:
                    best_c, improved = c, True
                else:
                    layers[r][i], layers[r][i + 1] = layers[r][i + 1], layers[r][i]
    return best_c


def _pav(targets: list[float], offsets: list[float],
         weights: Optional[list[float]] = None) -> list[float]:
    """Least-squares centers in fixed order with minimum gaps.

    Minimise ``Σ w_i (x_i − t_i)²`` subject to ``x_{i+1} − x_i ≥ gap_i``.
    Substituting ``y_i = x_i − offset_i`` (cumulative gaps) turns the
    constraint into ``y`` non-decreasing — isotonic regression, solved
    exactly by pool-adjacent-violators.
    """
    ys = [t - o for t, o in zip(targets, offsets)]
    ws = weights or [1.0] * len(ys)
    blocks: list[list[float]] = []   # [mean, weight, count]
    for y, w0 in zip(ys, ws):
        blocks.append([y, w0, 1])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            m2, w2, c2 = blocks.pop()
            m1, w1, c1 = blocks.pop()
            w = w1 + w2
            blocks.append([(m1 * w1 + m2 * w2) / w, w, c1 + c2])
    out: list[float] = []
    for mean, _, count in blocks:
        out.extend([mean] * count)
    return [y + o for y, o in zip(out, offsets)]


# ─── Rounded orthogonal path ────────────────────────────────────────

def _rounded(points: list[tuple[float, float]], radius: float = _RADIUS) -> str:
    pts = [points[0]]
    for p in points[1:]:
        if abs(p[0] - pts[-1][0]) > 1e-6 or abs(p[1] - pts[-1][1]) > 1e-6:
            pts.append(p)
    d = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        l1 = abs(x1 - x0) + abs(y1 - y0)
        l2 = abs(x2 - x1) + abs(y2 - y1)
        r = min(radius, l1 / 2, l2 / 2)

        def toward(ax, ay, bx, by, dist, length):
            return (ax + (bx - ax) * dist / length, ay + (by - ay) * dist / length)
        ax, ay = toward(x1, y1, x0, y0, r, l1)
        bx, by = toward(x1, y1, x2, y2, r, l2)
        d.append(f"L {ax:.1f} {ay:.1f} Q {x1:.1f} {y1:.1f} {bx:.1f} {by:.1f}")
    d.append(f"L {pts[-1][0]:.1f} {pts[-1][1]:.1f}")
    return " ".join(d)


# ─── SVG ────────────────────────────────────────────────────────────

def dag(
    nodes,
    edges,
    *,
    direction: str = "down",
    title: Optional[str] = None,
    brand=None,
    out_path: Union[str, Path] = "dag.svg",
    desc: Optional[str] = None,
    allow_tree: bool = False,
) -> str:
    """Render a causal / dependency DAG (≤9 nodes, ≤14 edges, ≤4 ranks).

    Parameters
    ----------
    nodes
        Each a dict ``{"id": str, "label": str, "sublabel": str,
        "focal": bool}`` (or a bare id string). ``label`` defaults to the
        id; ``sublabel`` is a muted mono line under it (a unit, a
        measure, a version); ``focal`` highlights **one** node in the
        accent. Input order is the tie-break for layout, so reordering
        the list is how you nudge an otherwise-equal arrangement.
    edges
        Each a dict ``{"src": id, "dst": id, "label": str, "back": bool}``
        (or a ``(src, dst)`` pair). Forward edges must be acyclic. At most
        one edge may be marked ``back=True``; it must close a cycle, and
        is drawn dashed in the accent around the outside of the stack.
        ``label`` names the mechanism beside the edge's source end —
        label the few edges whose mechanism needs naming, not all of them.
    direction
        ``"down"`` (default; rank 0 on top) or ``"right"`` (rank 0 at
        left). Forward edges only ever point this way.
    title, desc
        Heading, and what the figure argues for the SVG ``<desc>``. The
        default desc lists nodes by rank and the edges; it asserts no
        claim.
    brand
        Optional ``muriel.styleguide.StyleGuide``.
    out_path
        Where to write the SVG. Its stem prefixes every id.
    allow_tree
        The generator refuses single-parent data (a tree) by default —
        see the module anti-prescription. Pass ``True`` when arrow
        direction itself is the point and a hierarchy would lose it.

    Raises
    ------
    ValueError
        Unknown ids, self-loops, duplicate edges, a forward cycle (named),
        a back-edge that closes no cycle, over budget, more than one focal
        element, a tree without ``allow_tree``, or an edge label with no
        free side of its connector.

    Returns
    -------
    str
        The path written.
    """
    if direction not in ("down", "right"):
        raise ValueError(f"direction must be 'down' or 'right'; got {direction!r}")
    down = direction == "down"
    nodes, edges = _normalize(nodes, edges)
    _validate(nodes, edges, allow_tree)
    n = len(nodes)
    t = _resolve(brand)
    slug = figure_slug(out_path, "dag")

    fwd_idx = [i for i, e in enumerate(edges) if not e["back"]]
    back_idx = [i for i, e in enumerate(edges) if e["back"]]
    rank = _ranks(n, [edges[i] for i in fwd_idx])
    n_ranks = max(rank) + 1
    if n_ranks > MAX_RANKS:
        deepest = max(range(n), key=lambda v: (rank[v], -v))
        raise ValueError(
            f"the longest dependency chain spans {n_ranks} ranks (max "
            f"{MAX_RANKS}), ending at {nodes[deepest]['id']!r}. Split the "
            f"figure at a hub node — upstream causes in one DAG, downstream "
            f"effects in another — or collapse a run of mediators into one "
            f"node.")

    in_count = [0] * n
    for e in edges:
        in_count[e["dst"]] += 1
    has_badge = [c >= 2 for c in in_count]

    # ── Measure nodes ───────────────────────────────────────────────
    def fits_for(width: float, v: int):
        return fit_text(nodes[v]["label"], _LABEL_FS, width - 2 * _BOX_PAD,
                        max_lines=2, char_width_ratio=RATIO_SANS_BOLD)

    rank_w = [float(_BOX_W)] * n_ranks
    for v in range(n):
        r = rank[v]
        fit = fits_for(rank_w[r], v)
        need = rank_w[r]
        if fit.reason == "unbreakable-word":
            need = max(need, fit.width + 2 * _BOX_PAD)
        sub = nodes[v]["sublabel"]
        if sub:
            need = max(need, text_width(sub, _SUB_FS,
                                        char_width_ratio=RATIO_MONO)
                       + 2 * _BOX_PAD)
        rank_w[r] = grow_to_fit(rank_w[r], need)
    fits = [fits_for(rank_w[rank[v]], v) for v in range(n)]

    def block_h(v: int) -> float:
        lines = max(1, len(fits[v].lines))
        h = _ASC * _LABEL_FS + (lines - 1) * _LABEL_LH
        if nodes[v]["sublabel"]:
            h += _SUB_GAP + _DESC * _SUB_FS
        else:
            h += _DESC * _LABEL_FS
        return h

    box_h = float(_BOX_H)
    for v in range(n):
        box_h = grow_to_fit(box_h, block_h(v) + 20)

    # ── Elements, pieces, layers ────────────────────────────────────
    elems: dict[tuple, _Elem] = {}
    layers: list[list[tuple]] = [[] for _ in range(n_ranks)]
    for v in range(n):
        k = ("n", v)
        elems[k] = _Elem(k, float(v))
        layers[rank[v]].append(k)
    pieces: list[_Piece] = []
    pieces_between: list[list[_Piece]] = [[] for _ in range(max(0, n_ranks - 1))]
    for ei in fwd_idx:
        e = edges[ei]
        chain = [("n", e["src"])]
        for r in range(rank[e["src"]] + 1, rank[e["dst"]]):
            k = ("d", ei, r)
            elems[k] = _Elem(k, n + ei + r / 10.0)
            layers[r].append(k)
            chain.append(k)
        chain.append(("n", e["dst"]))
        for a, b in zip(chain, chain[1:]):
            r = rank[e["src"]] + chain.index(a)
            p = _Piece(ei, a, b, r)
            pieces.append(p)
            pieces_between[r].append(p)
            elems[a].down.append(p)
            elems[b].up.append(p)

    _order(layers, elems, pieces_between)

    # ── Sizes along the cross axis, and port offsets ────────────────
    # "down": cross axis is x, a box spans its rank's width.
    # "right": cross axis is y, every box spans box_h.
    def node_cross(v: int) -> float:
        return rank_w[rank[v]] if down else box_h

    def rank_thick(r: int) -> float:
        return box_h if down else rank_w[r]

    back = edges[back_idx[0]] if back_idx else None
    # Ports need ≥12px spacing; grow boxes whose sides are crowded.
    side_count: dict[tuple, int] = {}
    for p in pieces:
        side_count[(p.a, "out")] = side_count.get((p.a, "out"), 0) + 1
        side_count[(p.b, "in")] = side_count.get((p.b, "in"), 0) + 1
    if back:
        ka, kb = ("n", back["src"]), ("n", back["dst"])
        side_count[(ka, "out")] = side_count.get((ka, "out"), 0) + 1
        side_count[(kb, "in")] = side_count.get((kb, "in"), 0) + 1
    for (k, _side), cnt in side_count.items():
        if k[0] != "n":
            continue
        need = _PORT_MIN * (cnt + 1)
        if down:
            r = rank[k[1]]
            rank_w[r] = grow_to_fit(rank_w[r], need)
        else:
            box_h = grow_to_fit(box_h, need)
    fits = [fits_for(rank_w[rank[v]], v) for v in range(n)]
    for v in range(n):
        box_h = grow_to_fit(box_h, block_h(v) + 20)

    # The fan-in badge sits in the top-right corner. Grow the (global)
    # height only if a badged node's centred text would actually reach
    # under it — a short label clears the badge at the floor height.
    def badge_w(v: int) -> float:
        return grow_to_fit(0, text_width(f"{in_count[v]} in", _BADGE_FS,
                                         char_width_ratio=RATIO_MONO) + 8)

    def text_hits_badge(v: int, h: float) -> bool:
        w = rank_w[rank[v]]
        # the width estimates are already conservative; 2px vertical air
        bx0 = w - _BADGE_INSET - badge_w(v)
        by1 = _BADGE_INSET + _BADGE_H + 2
        top = h / 2 - block_h(v) / 2
        base = top + _ASC * _LABEL_FS
        rows = [(ln, _LABEL_FS, base + i * _LABEL_LH, RATIO_SANS_BOLD)
                for i, ln in enumerate(fits[v].lines)]
        if nodes[v]["sublabel"]:
            rows.append((nodes[v]["sublabel"], _SUB_FS,
                         base + (len(fits[v].lines) - 1) * _LABEL_LH + _SUB_GAP,
                         RATIO_MONO))
        for text, fs, b, ratio in rows:
            tw = text_width(text, fs, char_width_ratio=ratio)
            if b - _ASC * fs < by1 and w / 2 + tw / 2 > bx0:
                return True
        return False

    for _ in range(40):
        if not any(has_badge[v] and text_hits_badge(v, box_h) for v in range(n)):
            break
        box_h += 4

    for k, el in elems.items():
        el.size = node_cross(k[1]) if k[0] == "n" else 0.0

    def gap(a: tuple, b: tuple) -> float:
        if a[0] == "n" and b[0] == "n":
            sep = 40.0 if down else 32.0
        elif a[0] == "n" or b[0] == "n":
            sep = 24.0
        else:
            sep = 16.0
        return elems[a].size / 2 + elems[b].size / 2 + sep

    # Port offset of a piece on an element side, relative to its centre.
    # Ports on a side are ordered by the other end's layer position so
    # connectors leaving one box do not cross each other; the back-edge
    # takes the outermost port, on the side of the lane it runs in.
    port_off: dict[tuple, float] = {}
    pos_in_layer = {k: i for l in layers for i, k in enumerate(l)}
    for k, el in elems.items():
        for side, ps, other in (("out", el.down, "b"), ("in", el.up, "a")):
            items = [(pos_in_layer[getattr(p, other)], p.edge, ("p", p.edge, p.rank))
                     for p in ps]
            if back and k[0] == "n":
                if side == "out" and k[1] == back["src"]:
                    items.append((10**6, back_idx[0], ("back", "out")))
                if side == "in" and k[1] == back["dst"]:
                    items.append((10**6, back_idx[0], ("back", "in")))
            items.sort()
            cnt = len(items)
            for j, (_, _, pid) in enumerate(items):
                off = el.size * (j + 1) / (cnt + 1) - el.size / 2 if k[0] == "n" else 0.0
                port_off[(k, side, pid)] = off

    def poff(k, side, pid):
        return port_off[(k, side, pid)]

    # ── Cross-axis placement: pull ports into line, keep order + gaps ─
    for l in layers:
        c = 0.0
        for i, k in enumerate(l):
            if i:
                c += gap(l[i - 1], k)
            elems[k].center = c
        mid = c / 2
        for k in l:
            elems[k].center -= mid

    def desired(k: tuple, use_up: bool, use_down: bool) -> float:
        el = elems[k]
        vals = []
        if use_up:
            for p in el.up:
                pid = ("p", p.edge, p.rank)
                vals.append(elems[p.a].center + poff(p.a, "out", pid)
                            - poff(k, "in", pid))
        if use_down:
            for p in el.down:
                pid = ("p", p.edge, p.rank)
                vals.append(elems[p.b].center + poff(p.b, "in", pid)
                            - poff(k, "out", pid))
        return sum(vals) / len(vals) if vals else el.center

    def place(r: int, use_up: bool, use_down: bool) -> None:
        l = layers[r]
        targets = [desired(k, use_up, use_down) for k in l]
        offsets = [0.0]
        for i in range(1, len(l)):
            offsets.append(offsets[-1] + gap(l[i - 1], l[i]))
        for k, x in zip(l, _pav(targets, offsets)):
            elems[k].center = x

    for _ in range(8):
        for r in range(1, n_ranks):
            place(r, True, False)
        for r in range(n_ranks - 2, -1, -1):
            place(r, False, True)
    for _ in range(4):
        for r in range(n_ranks):
            place(r, True, True)

    # Straighten long edges: each waypoint lines up under its upper
    # neighbour's port, so a multi-rank edge drops straight and jogs once
    # (at its destination) instead of once per rank. Real nodes are held
    # where they are by a much larger weight.
    for r in range(1, n_ranks):
        l = layers[r]
        targets, weights = [], []
        for k in l:
            el = elems[k]
            if k[0] == "d" and el.up:
                p = el.up[0]
                targets.append(elems[p.a].center
                               + poff(p.a, "out", ("p", p.edge, p.rank)))
                weights.append(1.0)
            else:
                targets.append(el.center)
                weights.append(1000.0)
        offsets = [0.0]
        for i in range(1, len(l)):
            offsets.append(offsets[-1] + gap(l[i - 1], l[i]))
        for k, x in zip(l, _pav(targets, offsets, weights)):
            elems[k].center = x

    # Round centres onto the half-pixel so straight edges stay straight.
    for el in elems.values():
        el.center = round(el.center * 2) / 2

    def port_u(k, side, pid) -> float:
        return elems[k].center + poff(k, side, pid)

    cross_lo = min(el.center - el.size / 2 for el in elems.values())
    cross_hi = max(el.center + el.size / 2 for el in elems.values())

    # ── Channels: label bands + one track per horizontal jog ────────
    # Channel c sits between rank c-1 and rank c; channel 0 is above the
    # stack and channel n_ranks below it (used only by a back-edge).
    jogs: list[list[dict]] = [[] for _ in range(n_ranks + 1)]
    straight: list[dict] = []
    # Pieces in chain order, so a waypoint snapped onto an upstream port
    # carries that exact coordinate into its next hop — sub-pixel
    # differences would otherwise draw a visible kink.
    for p in sorted(pieces, key=lambda p: (p.edge, p.rank)):
        pid = ("p", p.edge, p.rank)
        ua = port_u(p.a, "out", pid)
        ub = port_u(p.b, "in", pid)
        seg = {"piece": p, "ua": ua, "ub": ub, "edge": p.edge}
        if abs(ua - ub) < 0.75:
            seg["ub"] = ua
            if p.b[0] == "d":
                elems[p.b].center = ua
            straight.append(seg)
        else:
            jogs[p.rank + 1].append(seg)

    back_segs: list[dict] = []
    lane_u = cross_hi + _OUTER_LANE
    if back:
        ka, kb = ("n", back["src"]), ("n", back["dst"])
        b_out = {"back": "out", "ua": port_u(ka, "out", ("back", "out")),
                 "ub": lane_u, "edge": back_idx[0]}
        b_in = {"back": "in", "ua": lane_u,
                "ub": port_u(kb, "in", ("back", "in")), "edge": back_idx[0]}
        back_segs = [b_out, b_in]

    labelled_out = [False] * (n_ranks + 1)
    for p in pieces:
        if edges[p.edge]["label"] and p.a[0] == "n":
            labelled_out[p.rank + 1] = True

    label_w = {}
    for ei, e in enumerate(edges):
        if e["label"]:
            label_w[ei] = text_width(e["label"], _EDGE_FS,
                                     char_width_ratio=RATIO_SANS)
    band = [0.0] * (n_ranks + 1)
    for c in range(1, n_ranks):
        if labelled_out[c]:
            if down:
                band[c] = 20.0
            else:
                ws = [label_w[p.edge] for p in pieces
                      if p.rank + 1 == c and p.edge in label_w and p.a[0] == "n"]
                band[c] = grow_to_fit(0, max(ws) + 16)

    def order_tracks(segs: list[dict]) -> list[dict]:
        # Rightward jogs: the one starting furthest along gets the track
        # nearest the source; leftward jogs mirror that. It removes the
        # avoidable crossings between jogs that travel the same way.
        right = sorted([s for s in segs if s["ub"] > s["ua"]],
                       key=lambda s: (-s["ua"], s["edge"]))
        left = sorted([s for s in segs if s["ub"] <= s["ua"]],
                      key=lambda s: (s["ua"], s["edge"]))
        return right + left

    tracks: list[list[dict]] = []
    chan_size = []
    for c in range(n_ranks + 1):
        segs = order_tracks(jogs[c])
        if back and c == rank[back["src"]] + 1:
            segs = [back_segs[0]] + segs          # nearest the source
        if back and c == rank[back["dst"]]:
            segs = segs + [back_segs[1]]          # nearest the destination
        tracks.append(segs)
        if c in (0, n_ranks):
            size = (0.0 if not segs else
                    max(float(_OUTER_CHANNEL),
                        2 * _TRACK_MARGIN + _TRACK_GAP * (len(segs) - 1)))
        else:
            size = max(float(_CHANNEL_MIN),
                       band[c] + 2 * _TRACK_MARGIN
                       + _TRACK_GAP * max(0, len(segs) - 1))
            size = grow_to_fit(size, size)
        chan_size.append(size)

    # Rank-axis positions.
    rank_start = []
    v = chan_size[0]
    for r in range(n_ranks):
        rank_start.append(v)
        v += rank_thick(r) + chan_size[r + 1]
    rank_axis_end = v

    def chan_bounds(c: int) -> tuple[float, float]:
        if c == 0:
            return 0.0, chan_size[0]
        lo = rank_start[c - 1] + rank_thick(c - 1)
        return lo, lo + chan_size[c]

    for c, segs in enumerate(tracks):
        if not segs:
            continue
        lo, hi = chan_bounds(c)
        lo += band[c]
        span = _TRACK_GAP * (len(segs) - 1)
        first = lo + (hi - lo - span) / 2
        first = round(first * 2) / 2
        for i, s in enumerate(segs):
            s["track"] = first + i * _TRACK_GAP

    # ── Build paths in (u, v), map to (x, y) ────────────────────────
    def exit_v(k) -> float:
        r = rank[k[1]] if k[0] == "n" else k[2]
        return rank_start[r] + rank_thick(r)

    def entry_v(k) -> float:
        r = rank[k[1]] if k[0] == "n" else k[2]
        return rank_start[r]

    def xy(u: float, vv: float) -> tuple[float, float]:
        return (u, vv) if down else (vv, u)

    seg_of_piece = {}
    for s in straight:
        seg_of_piece[id(s["piece"])] = s
    for c in range(n_ranks + 1):
        for s in tracks[c]:
            if "piece" in s:
                seg_of_piece[id(s["piece"])] = s

    edge_paths: dict[int, list[tuple[float, float]]] = {}
    for ei in fwd_idx:
        e = edges[ei]
        ps = sorted([p for p in pieces if p.edge == ei], key=lambda p: p.rank)
        pts_uv: list[tuple[float, float]] = []
        for p in ps:
            s = seg_of_piece[id(p)]
            va, vb = exit_v(p.a), entry_v(p.b)
            if p.a[0] == "d":
                # the waypoint's vertical run through its rank
                pts_uv.append((s["ua"], entry_v(p.a)))
            pts_uv.append((s["ua"], va))
            if "track" in s:
                pts_uv.append((s["ua"], s["track"]))
                pts_uv.append((s["ub"], s["track"]))
            pts_uv.append((s["ub"], vb))
        # stop 1px short of the box edge so the arrow tip sits on the border
        u_end, v_end = pts_uv[-1]
        pts_uv[-1] = (u_end, v_end - 1)
        edge_paths[ei] = [xy(u, vv) for u, vv in pts_uv]

    if back:
        ka, kb = ("n", back["src"]), ("n", back["dst"])
        b_out, b_in = back_segs
        pts_uv = [
            (b_out["ua"], exit_v(ka)),
            (b_out["ua"], b_out["track"]),
            (lane_u, b_out["track"]),
            (lane_u, b_in["track"]),
            (b_in["ub"], b_in["track"]),
            (b_in["ub"], entry_v(kb) - 1),
        ]
        edge_paths[back_idx[0]] = [xy(u, vv) for u, vv in pts_uv]

    # Node boxes in (x, y).
    boxes: dict[int, tuple[float, float, float, float]] = {}
    for vtx in range(n):
        k = ("n", vtx)
        c0 = elems[k].center - elems[k].size / 2
        r = rank[vtx]
        if down:
            boxes[vtx] = (c0, rank_start[r], rank_w[r], box_h)
        else:
            boxes[vtx] = (rank_start[r], c0, rank_w[r], box_h)

    # ── Edge labels: beside the source end, on a side no connector uses ─
    def segs_xy(pts):
        return list(zip(pts, pts[1:]))

    all_segs = [(ei, a, b) for ei, pts in edge_paths.items()
                for a, b in segs_xy(pts)]

    def hits_segment(bb, ei_self) -> bool:
        x0, y0, x1, y1 = bb
        for ei, (ax, ay), (bx, by) in all_segs:
            if ei == ei_self:
                continue
            sx0, sx1 = sorted((ax, bx))
            sy0, sy1 = sorted((ay, by))
            if sx0 - 3 < x1 and sx1 + 3 > x0 and sy0 - 3 < y1 and sy1 + 3 > y0:
                return True
        return False

    def hits_box(bb) -> bool:
        x0, y0, x1, y1 = bb
        for bx, by, bw, bh in boxes.values():
            if bx < x1 and bx + bw > x0 and by < y1 and by + bh > y0:
                return True
        return False

    labels: list[dict] = []

    def overlaps_label(bb) -> bool:
        x0, y0, x1, y1 = bb
        for lab in labels:
            a0, b0, a1, b1 = lab["bbox"]
            if a0 - 4 < x1 and a1 + 4 > x0 and b0 - 2 < y1 and b1 + 2 > y0:
                return True
        return False

    asc, dsc = _ASC * _EDGE_FS, _DESC * _EDGE_FS
    for ei in fwd_idx:
        e = edges[ei]
        if not e["label"]:
            continue
        w = label_w[ei]
        (sx, sy) = edge_paths[ei][0]
        cands = []
        if down:
            base = sy + 4 + asc
            cands.append(("start", sx + 6, base, (sx + 6, base - asc, sx + 6 + w, base + dsc)))
            cands.append(("end", sx - 6, base, (sx - 6 - w, base - asc, sx - 6, base + dsc)))
        else:
            x = sx + 6
            above = sy - 5
            below = sy + 5 + asc
            cands.append(("start", x, above, (x, above - asc, x + w, above + dsc)))
            cands.append(("start", x, below, (x, below - asc, x + w, below + dsc)))
        for anchor, lx, ly, bb in cands:
            if not (hits_segment(bb, ei) or hits_box(bb) or overlaps_label(bb)):
                labels.append({"text": e["label"], "x": lx, "y": ly,
                               "anchor": anchor, "bbox": bb, "back": False})
                break
        else:
            raise ValueError(
                f"edge label {e['label']!r} on {nodes[e['src']]['id']!r} → "
                f"{nodes[e['dst']]['id']!r} has no free side: other connectors "
                f"leave the same box on both sides of it. Label fewer edges "
                f"from that node, or name the mechanism in desc=.")
    if back and back["label"]:
        w = text_width(back["label"], _EDGE_FS, char_width_ratio=RATIO_SANS)
        pts = edge_paths[back_idx[0]]
        (lx0, ly0), (lx1, ly1) = pts[2], pts[3]
        if down:
            x = lx0 + 8
            y = (ly0 + ly1) / 2 + (asc - dsc) / 2
            bb = (x, y - asc, x + w, y + dsc)
            labels.append({"text": back["label"], "x": x, "y": y,
                           "anchor": "start", "bbox": bb, "back": True})
        else:
            x = (lx0 + lx1) / 2
            y = ly0 + 8 + asc
            bb = (x - w / 2, y - asc, x + w / 2, y + dsc)
            labels.append({"text": back["label"], "x": x, "y": y,
                           "anchor": "middle", "bbox": bb, "back": True})

    # ── Canvas: translate everything to sit inside the padding ──────
    title_h = 72 if title else 0
    xs, ys = [], []
    for bx, by, bw, bh in boxes.values():
        xs += [bx, bx + bw]
        ys += [by, by + bh]
    for pts in edge_paths.values():
        xs += [p[0] for p in pts]
        ys += [p[1] for p in pts]
    for lab in labels:
        x0, y0, x1, y1 = lab["bbox"]
        xs += [x0, x1]
        ys += [y0, y1]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    if not down and chan_size[0] == 0:
        min_x = min(min_x, 0.0)
    if down and chan_size[0] == 0:
        min_y = min(min_y, 0.0)
    # Under a title the heading's own 72px band already separates it from
    # the figure; a full 48px pad on top of that reads as a gap.
    pad_top = 24 if title else _PAD
    dx = _PAD - min_x
    dy = title_h + pad_top - min_y
    width = grow_to_fit(0, (max_x - min_x) + 2 * _PAD)
    if title:
        width = max(width, grow_to_fit(0, _PAD * 2 + text_width(
            title, 20, char_width_ratio=RATIO_SANS_BOLD)))
    height = grow_to_fit(0, title_h + pad_top + (max_y - min_y) + _PAD)
    # centre the figure horizontally if the title widened the canvas
    dx += ((width - 2 * _PAD) - (max_x - min_x)) / 2

    def T(x, y):
        return x + dx, y + dy

    # ── Emit ─────────────────────────────────────────────────────────
    if desc is None:
        by_rank = []
        for r in range(n_ranks):
            members = [nodes[k[1]]["label"] for k in layers[r] if k[0] == "n"]
            by_rank.append(f"rank {r + 1}: " + ", ".join(members))
        parts_desc = [
            ("ranks, " + ("top to bottom" if down else "left to right") + " — "
             + "; ".join(by_rank)),
            "edges: " + ", ".join(
                f"{nodes[edges[i]['src']]['label']} → {nodes[edges[i]['dst']]['label']}"
                + (f" ({edges[i]['label']})" if edges[i]["label"] else "")
                for i in fwd_idx),
        ]
        if back:
            parts_desc.append(
                f"feedback edge: {nodes[back['src']]['label']} → "
                f"{nodes[back['dst']]['label']}"
                + (f" ({back['label']})" if back["label"] else ""))
        desc = default_desc(
            f"Directed acyclic graph with {n} nodes and {len(edges)} edges",
            title, parts_desc)

    out: list[str] = []
    out.append(svg_open(
        width=width, height=height, slug=slug, title=title or "DAG",
        desc=desc, attrs=f'font-family="{escape(t["body_font"])}"'))
    out.append(
        f'<defs>'
        f'<marker id="{slug}-arrow" markerWidth="8" markerHeight="8" '
        f'refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M0,0 L8,4 L0,8 z" fill="{t["flow"]}"/></marker>'
        f'<marker id="{slug}-arrow-back" markerWidth="8" markerHeight="8" '
        f'refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M0,0 L8,4 L0,8 z" fill="{t["accent"]}"/></marker>'
        f'</defs>')
    out.append(f'<rect width="{width}" height="{height}" fill="{t["bg"]}"/>')
    if title:
        out.append(
            f'<text x="{_PAD}" y="{title_h - 24}" fill="{t["ink"]}" '
            f'font-size="20" font-weight="600" text-anchor="start">'
            f'{escape(title)}</text>')

    # Edges first, so boxes paint over their ends.
    for ei in fwd_idx + back_idx:
        e = edges[ei]
        pts = [T(x, y) for x, y in edge_paths[ei]]
        src_id = escape(nodes[e["src"]]["id"], quote=True)
        dst_id = escape(nodes[e["dst"]]["id"], quote=True)
        if e["back"]:
            style = (f'stroke="{t["accent"]}" stroke-width="1.5" '
                     f'stroke-dasharray="5,4" marker-end="url(#{slug}-arrow-back)"')
            extra = ' data-back="true"'
        else:
            style = (f'stroke="{t["flow"]}" stroke-width="1.25" '
                     f'marker-end="url(#{slug}-arrow)"')
            extra = ""
        out.append(
            f'<path d="{_rounded(pts)}" fill="none" {style} '
            f'data-src="{src_id}" data-dst="{dst_id}"{extra}/>')

    edge_ink = legible_on([t["muted"], t["ink"]], t["bg"], t["bg"])
    back_ink = legible_on([t["accent"], t["ink"]], t["bg"], t["bg"])
    for lab in labels:
        x, y = T(lab["x"], lab["y"])
        fill = back_ink if lab["back"] else edge_ink
        out.append(
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{_EDGE_FS}" '
            f'text-anchor="{lab["anchor"]}">{escape(lab["text"])}</text>')

    for vtx in range(n):
        nd = nodes[vtx]
        bx, by, bw, bh = boxes[vtx]
        bx, by = T(bx, by)
        focal = nd["focal"]
        fill = t["focal_fill"] if focal else t["paper"]
        stroke = t["accent"] if focal else t["stroke"]
        sw = 1.5 if focal else 1
        ink = legible_on([t["ink"]], fill, t["bg"])
        sub_ink = legible_on([t["muted"], t["ink"]], fill, t["bg"])
        out.append(
            f'<g data-id="{escape(nd["id"], quote=True)}" data-rank="{rank[vtx]}">')
        # opaque underlay: the translucent node fill must not show edges through it
        out.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw}" height="{bh}" '
                   f'rx="6" fill="{t["bg"]}"/>')
        out.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw}" height="{bh}" '
                   f'rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        cx = bx + bw / 2
        cy = by + bh / 2
        top = cy - block_h(vtx) / 2
        base = top + _ASC * _LABEL_FS
        lines = fits[vtx].lines or ("",)
        for i, line in enumerate(lines):
            out.append(
                f'<text x="{cx:.1f}" y="{base + i * _LABEL_LH:.1f}" fill="{ink}" '
                f'font-size="{_LABEL_FS}" font-weight="600" text-anchor="middle">'
                f'{escape(line)}</text>')
        if nd["sublabel"]:
            sb = base + (len(lines) - 1) * _LABEL_LH + _SUB_GAP
            out.append(
                f'<text x="{cx:.1f}" y="{sb:.1f}" fill="{sub_ink}" '
                f'font-family="{_MONO}" font-size="{_SUB_FS}" text-anchor="middle">'
                f'{escape(nd["sublabel"])}</text>')
        if has_badge[vtx]:
            txt = f"{in_count[vtx]} in"
            tw = text_width(txt, _BADGE_FS, char_width_ratio=RATIO_MONO)
            bwid = grow_to_fit(0, tw + 8)
            rx0 = bx + bw - _BADGE_INSET - bwid
            ry0 = by + _BADGE_INSET
            badge_ink = legible_on([t["muted"], t["ink"]], t["bg"], t["bg"])
            out.append(
                f'<rect x="{rx0:.1f}" y="{ry0:.1f}" width="{bwid}" '
                f'height="{_BADGE_H}" rx="2" fill="{t["bg"]}" '
                f'stroke="{t["hairline"]}" stroke-width="1"/>')
            out.append(
                f'<text x="{rx0 + bwid / 2:.1f}" y="{ry0 + 10.5:.1f}" '
                f'fill="{badge_ink}" font-family="{_MONO}" '
                f'font-size="{_BADGE_FS}" text-anchor="middle">{txt}</text>')
        out.append('</g>')

    out.append('</svg>')
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")
    return str(path)


def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.dag spec.json out.svg``.

    Spec format::

        {
          "title": "What drives a click",
          "direction": "down",
          "nodes": [
            {"id": "amb",    "label": "Query ambiguity"},
            {"id": "layout", "label": "SERP layout"},
            {"id": "dwell",  "label": "Dwell time"},
            {"id": "click",  "label": "Click"}
          ],
          "edges": [
            {"src": "amb", "dst": "dwell"},
            {"src": "layout", "dst": "dwell"},
            {"src": "dwell", "dst": "click"}
          ],
          "brand": "examples/muriel-brand.toml"
        }
    """
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.dag")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    dag(
        spec["nodes"],
        spec["edges"],
        direction=spec.get("direction", "down"),
        title=spec.get("title"),
        brand=brand,
        out_path=args.output,
        desc=spec.get("desc"),
        allow_tree=bool(spec.get("allow_tree", False)),
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
