"""
muriel.tools.diagrams.dendrogram — branching tree / hierarchy as SVG.

When to use
-----------
A structure where **every node has exactly one parent** and the claim is
decomposition: *X consists of these parts, and each part of these*. Research
taxonomies (eye-movement events → fixation / saccade / pursuit / blink →
subtypes), a module tree, a skill tree, a decision breakdown. The geometry
carries two things and only two: **containment** (which parent a node hangs
from) and **depth** (how many decompositions separate it from the root).
Rank position along the depth axis means "same number of splits from the
root" — nothing else.

Leaf weights are absent, or roughly equal, or beside the point. That is the
case where a tree beats a sunburst or treemap: when every leaf would get the
same area anyway, area carries no signal and the node-link form reads faster.

Not a clustering dendrogram
---------------------------
The name is the botanical one (a branching tree), not the statistical one.
Rank spacing here is uniform and encodes depth, **not merge distance**. If
the heights are data — the output of hierarchical clustering, where the
linkage distance at which two clusters merge is the finding — draw it with
``scipy.cluster.hierarchy.dendrogram`` on a real axis instead.

Not the exclusive provider
--------------------------
This is the static, brand-locked, print-ready option. For an interactive,
collapsible tree on a web surface, ECharts' ``tree`` series is lighter
(``vocabularies/echarts.md``); for a quick hierarchy in a design doc, the
infographics **Hierarchical** template. Reach for this generator when the
deliverable is a paper figure or editorial SVG that must match brand tokens
and clear the 8:1 contrast floor.

Anti-prescription
-----------------
- **Any node with two parents is not a tree.** A shared prerequisite, a
  concept filed under two headings, a cause with two effects that reconverge
  — that is a DAG; use the ``dag`` generator. This one refuses a node object
  that appears under two parents, and warns when one label does.
- **If the leaf proportions matter, the tree hides them.** Budget share per
  category, AOI dwell per region, traffic per page: use ``treemap`` (or a
  sunburst) so area carries the magnitude.
- **One path only is a process, not a hierarchy.** A chain where every node
  has one child is a sequence; draw it as a ``swimlane`` or the infographics
  Process template. The generator refuses a tree with no branching.
- **Don't go past four levels or five children.** Past root + 3 tiers the
  reader stops holding the structure; past five siblings the bus reads as a
  list. Split into an overview plus one figure per subtree, add grouping
  nodes, or fold the tail with ``collapse_over=``.
- **One accent, on the root or on one critical leaf.** An accent on a middle
  tier claims that tier is the point, which a tree's geometry can't support;
  two accents is no accent.

Geometry follows the editorial-diagram discipline: 4px-increment alignment,
1px orthogonal (elbow-bus) connectors drawn before the nodes, no diagonals,
no shadows, at most two box widths. Layout conventions (node proportions,
the elbow bus, depth/breadth budget, single accent) are adapted from the
MIT-licensed diagram-design skill (© 2025 Cathryn Lavery), ``type-tree.md``;
the tidy-tree placement, tokens, contrast rule, and epistemic gate are
muriel's own.
"""

from __future__ import annotations

import warnings
from html import escape
from pathlib import Path
from typing import Optional, Union

from ._a11y import default_desc, figure_slug, legible_on, svg_open
from ._labels import (
    RATIO_MONO,
    RATIO_SANS_BOLD,
    fit_text,
    grow_to_fit,
    text_width,
)

__all__ = ["dendrogram", "MAX_DEPTH", "MAX_BREADTH", "MAX_EXTENT"]

_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

MAX_DEPTH = 4      # levels, root included (root + 3 tiers)
MAX_BREADTH = 5    # children per node
# How far the leaf axis may run before the figure stops being one figure:
# a 1920px-wide slide/figure for a downward tree, a 1440px-tall page for a
# rightward one. The leaf budget is *computed* against this after the
# labels are measured, so it tracks the real box sizes rather than a count.
MAX_EXTENT = {"down": 1920.0, "right": 1440.0}


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
            "branch":     "rgba(230, 228, 210, 0.32)",
            "flow":       "rgba(176, 176, 196, 0.55)",
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
        "branch":     _rgba(ink, 0.32),
        "flow":       _rgba(muted, 0.55),
        "body_font":  brand.typography.body_family or "system-ui, sans-serif",
    }


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ─── Normalization ──────────────────────────────────────────────────

def _as_node(n) -> dict:
    if isinstance(n, str):
        return {"label": n}
    if not isinstance(n, dict):
        raise TypeError(
            f"tree nodes are dicts {{'label', 'sublabel', 'focal', "
            f"'children'}} or bare strings; got {type(n).__name__}")
    return n


def _has_focal(n) -> bool:
    n = _as_node(n)
    return bool(n.get("focal")) or any(
        _has_focal(c) for c in (n.get("children") or []))


def _normalize(tree, collapse_over: Optional[int]) -> list[dict]:
    """Flatten the nested spec into a pre-order node list.

    Each entry: ``label``, ``sublabel``, ``focal``, ``depth``, ``parent``
    (index or None), ``children`` (indices), ``collapsed`` (how many
    siblings a ``+N more`` node stands for; 0 otherwise), ``hidden``
    (their labels).
    """
    nodes: list[dict] = []
    seen: set[int] = set()

    def walk(raw, depth: int, parent: Optional[int]) -> int:
        n = _as_node(raw)
        if isinstance(raw, dict):
            if id(raw) in seen:
                label = str(raw.get("label", "")).strip()
                raise ValueError(
                    f"node {label!r} appears under two parents — that is a "
                    f"DAG, not a tree. Use the `dag` generator "
                    f"(muriel.tools.diagrams.dag).")
            seen.add(id(raw))
        label = " ".join(str(n.get("label", "")).split())
        if not label:
            raise ValueError("every tree node needs a non-empty 'label'")
        sub = n.get("sublabel")
        sub = " ".join(str(sub).split()) if sub else ""
        idx = len(nodes)
        nodes.append({
            "label": label, "sublabel": sub, "focal": bool(n.get("focal")),
            "depth": depth, "parent": parent, "children": [],
            "collapsed": 0, "hidden": (),
        })
        kids = list(n.get("children") or [])
        if collapse_over is not None and len(kids) > collapse_over:
            keep, hidden = kids[:collapse_over - 1], kids[collapse_over - 1:]
            for h in hidden:
                if _has_focal(h):
                    raise ValueError(
                        f"collapse_over={collapse_over} would fold the focal "
                        f"node away under {label!r}; move its branch earlier "
                        f"in the sibling list so it stays visible")
            for k in keep:
                nodes[idx]["children"].append(walk(k, depth + 1, idx))
            more = len(nodes)
            nodes.append({
                "label": f"+{len(hidden)} more", "sublabel": "",
                "focal": False, "depth": depth + 1, "parent": idx,
                "children": [], "collapsed": len(hidden),
                "hidden": tuple(" ".join(str(_as_node(h).get("label", ""))
                                         .split()) for h in hidden),
            })
            nodes[idx]["children"].append(more)
        else:
            for k in kids:
                nodes[idx]["children"].append(walk(k, depth + 1, idx))
        return idx

    walk(tree, 0, None)
    return nodes


def _validate(nodes: list[dict], collapse_over: Optional[int]) -> None:
    levels = max(n["depth"] for n in nodes) + 1
    if levels > MAX_DEPTH:
        raise ValueError(
            f"tree is {levels} levels deep; the budget is {MAX_DEPTH} "
            f"(root + {MAX_DEPTH - 1} tiers). Split it: draw an overview to "
            f"depth {MAX_DEPTH - 1}, then one detail figure per subtree.")
    for n in nodes:
        k = len(n["children"])
        if k > MAX_BREADTH:
            raise ValueError(
                f"{n['label']!r} has {k} children; the budget is "
                f"{MAX_BREADTH} per node. Introduce grouping nodes, or pass "
                f"collapse_over={MAX_BREADTH} to fold the overflow siblings "
                f"into one '+N more' node.")
    if not any(len(n["children"]) >= 2 for n in nodes):
        raise ValueError(
            "no node has two or more children — a single path is a process, "
            "not a hierarchy. Draw it as a sequence (swimlane, or the "
            "infographics Process template).")
    focal = [n for n in nodes if n["focal"]]
    if len(focal) > 1:
        raise ValueError(
            f"{len(focal)} focal nodes ({', '.join(repr(n['label']) for n in focal)}); "
            f"a tree takes one accent — the root or one critical leaf")
    if focal and focal[0]["parent"] is not None and focal[0]["children"]:
        raise ValueError(
            f"focal node {focal[0]['label']!r} is a middle tier; the accent "
            f"goes on the root or on one critical leaf")
    # Same label under two different parents: probably one entity filed
    # twice, which is the DAG smell. Not an error — "Other" legitimately
    # recurs — but worth saying.
    parents_by_label: dict[str, set] = {}
    for n in nodes:
        if n["parent"] is not None and not n["collapsed"]:
            parents_by_label.setdefault(n["label"], set()).add(n["parent"])
    for label, ps in sorted(parents_by_label.items()):
        if len(ps) > 1:
            warnings.warn(
                f"label {label!r} appears under {len(ps)} parents; if it is "
                f"one thing, the structure is a DAG — use the `dag` generator",
                stacklevel=3)


# ─── Box widths: measured, at most two ──────────────────────────────

def _choose_widths(needs_by_depth: dict[int, float], counts: dict[int, int],
                   floor: float, spread: float) -> dict[int, float]:
    """One width per rank, quantized to at most two distinct values.

    Widths are per *rank*, not per node, so every row (or column) is
    regular. When the ranks' needs sit within ``spread`` of each other,
    everything takes the widest; otherwise the ranks split into a narrow
    and a wide group at whichever threshold minimises total box width.
    """
    needs = {d: max(floor, w) for d, w in needs_by_depth.items()}
    wide = max(needs.values())
    if wide - min(needs.values()) < spread:
        return {d: wide for d in needs}
    best_cost = sum(wide * counts[d] for d in needs)
    best = {d: wide for d in needs}
    for narrow in sorted(set(needs.values())):
        if narrow >= wide or wide - narrow < spread:
            continue
        assign = {d: (narrow if w <= narrow else wide) for d, w in needs.items()}
        cost = sum(assign[d] * counts[d] for d in needs)
        if cost < best_cost:
            best_cost, best = cost, assign
    return best


# ─── Tidy-tree placement ────────────────────────────────────────────

def _tidy(nodes: list[dict], size: list[float], gap: float) -> list[float]:
    """Leaf-axis centre of every node (root at 0).

    Post-order, contour-based (Reingold–Tilford without threads — these
    trees are small). Each child subtree is pushed along the leaf axis
    until, at every depth both share, it clears what is already placed by
    ``gap``; the parent is then centred exactly on the midpoint of its
    first and last child. Subtrees never overlap by construction, and the
    result depends only on the input order.
    """

    def place(i: int):
        n = nodes[i]
        half = size[i] / 2
        if not n["children"]:
            return {i: 0.0}, {n["depth"]: [-half, half]}
        rel: dict[int, float] = {}
        contour: dict[int, list[float]] = {}
        centres: list[float] = []
        for c in n["children"]:
            crel, ccont = place(c)
            shift = 0.0
            if contour:
                shift = max(contour[d][1] + gap - ccont[d][0]
                            for d in ccont if d in contour)
            for k, v in crel.items():
                rel[k] = v + shift
            for d, (lo, hi) in ccont.items():
                if d in contour:
                    contour[d][0] = min(contour[d][0], lo + shift)
                    contour[d][1] = max(contour[d][1], hi + shift)
                else:
                    contour[d] = [lo + shift, hi + shift]
            centres.append(rel[c])
        mid = (centres[0] + centres[-1]) / 2
        rel = {k: v - mid for k, v in rel.items()}
        contour = {d: [lo - mid, hi - mid] for d, (lo, hi) in contour.items()}
        rel[i] = 0.0
        contour[n["depth"]] = [-half, half]
        return rel, contour

    rel, contour = place(0)
    lo = min(v[0] for v in contour.values())
    return [rel[i] - lo for i in range(len(nodes))]


# ─── SVG ────────────────────────────────────────────────────────────

def dendrogram(
    tree,
    *,
    orientation: str = "down",
    collapse_over: Optional[int] = None,
    title: Optional[str] = None,
    brand=None,
    out_path: Union[str, Path] = "dendrogram.svg",
    desc: Optional[str] = None,
) -> str:
    """Render a tidy tree with elbow-bus connectors.

    Parameters
    ----------
    tree
        The root node, nested: ``{"label": str, "sublabel": str,
        "focal": bool, "children": [node, ...]}``. ``sublabel`` and
        ``focal`` are optional; a bare string is a leaf. Child order is
        drawing order. Budget: at most 4 levels (root included) and 5
        children per node; the tree must branch somewhere.
    orientation
        ``"down"`` (root at top, default) or ``"right"`` (root at left).
        ``"right"`` stacks leaves vertically and fits more of them.
    collapse_over
        Optional int, 2–5. Any node with more children than this keeps its
        first ``collapse_over - 1`` children and folds the rest into one
        dashed ``+N more`` leaf, which stands for the folded siblings *and
        their subtrees*. The node's visible breadth is then exactly
        ``collapse_over``. Order the children by importance before relying
        on it; a fold that would hide the focal node raises instead.
        The folded labels are named in the default ``<desc>``.
    title
        Optional heading.
    brand
        Optional ``muriel.styleguide.StyleGuide``.
    out_path
        Where to write the SVG. Its stem also prefixes the accessible
        ``<title>``/``<desc>`` ids.
    desc
        What the figure argues, for the SVG ``<desc>``. Defaults to a
        conservative description that lists the containment and states no
        claim of its own.

    Every node is emitted as ``<g data-node data-depth data-parent>``;
    connectors are ``<line data-edge="stem|bus|drop">`` drawn before the
    nodes. The leaf-axis extent is checked against :data:`MAX_EXTENT`
    after the labels are measured, and an over-budget tree raises with
    the options (``collapse_over``, ``orientation="right"``, split).

    Returns
    -------
    str
        The path written.
    """
    if orientation not in ("down", "right"):
        raise ValueError(f"orientation must be 'down' or 'right', got {orientation!r}")
    if collapse_over is not None:
        if (isinstance(collapse_over, bool) or not isinstance(collapse_over, int)
                or not 2 <= collapse_over <= MAX_BREADTH):
            raise ValueError(
                f"collapse_over must be an int from 2 to {MAX_BREADTH} "
                f"(visible children per node, the '+N more' node included); "
                f"got {collapse_over!r}")
    nodes = _normalize(tree, collapse_over)
    _validate(nodes, collapse_over)
    t = _resolve(brand)
    down = orientation == "down"

    # ── Geometry (4px grid) ─────────────────────────────────────────
    #
    # Floors, not limits: boxes grow if the measured labels need it.
    box_w_min  = 120           # upstream range 120–180
    box_w_soft = 180           # past this the name wraps before growing
    box_h      = 40            # 40 one line; 52 with a sublabel
    pad_x      = 12            # label inset from the box edge
    pad_y      = 10
    line_h     = 16            # name leading at font-size 13
    sub_h      = 15            # sublabel row at font-size 11
    rank_gap   = 64            # box edge to box edge across ranks; bus at half
    leaf_gap   = 24 if down else 12
    pad        = 48
    title_h    = 72 if title else 0
    name_fs, sub_fs = 13, 11

    def name_w(s: str) -> float:
        return text_width(s, name_fs, char_width_ratio=RATIO_SANS_BOLD)

    def sub_w(s: str) -> float:
        return text_width(s, sub_fs, char_width_ratio=RATIO_MONO)

    # Per-node width need: one line if it fits under the soft cap, else
    # wrap the name to two lines at the cap; an unbreakable word wider
    # than the cap grows past it (text never escapes its box).
    inner_soft = box_w_soft - 2 * pad_x
    needs: list[float] = []
    for n in nodes:
        one = max(name_w(n["label"]), sub_w(n["sublabel"]))
        if one <= inner_soft:
            needs.append(one + 2 * pad_x)
            continue
        f = fit_text(n["label"], name_fs, inner_soft, max_lines=2,
                     char_width_ratio=RATIO_SANS_BOLD)
        needs.append(max(f.width, inner_soft, sub_w(n["sublabel"])) + 2 * pad_x)

    by_depth: dict[int, float] = {}
    counts: dict[int, int] = {}
    for n, w in zip(nodes, needs):
        by_depth[n["depth"]] = max(by_depth.get(n["depth"], 0.0), w)
        counts[n["depth"]] = counts.get(n["depth"], 0) + 1
    by_depth = {d: grow_to_fit(box_w_min, w) for d, w in by_depth.items()}
    rank_w = _choose_widths(by_depth, counts, box_w_min, spread=32)
    widths = [rank_w[n["depth"]] for n in nodes]

    # Now that widths are settled, wrap every name at its own box.
    fits = [fit_text(n["label"], name_fs, w - 2 * pad_x, max_lines=2,
                     char_width_ratio=RATIO_SANS_BOLD)
            for n, w in zip(nodes, widths)]
    n_lines = max(len(f.lines) for f in fits)
    has_sub = any(n["sublabel"] for n in nodes)
    content_h = n_lines * line_h + (sub_h if has_sub else 0)
    box_h = grow_to_fit(box_h, content_h + 2 * pad_y)

    # ── Place ───────────────────────────────────────────────────────
    along = widths if down else [box_h] * len(nodes)
    leaf_pos = _tidy(nodes, along, leaf_gap)
    extent = max(p + s / 2 for p, s in zip(leaf_pos, along))
    n_leaves = sum(1 for n in nodes if not n["children"])
    if extent > MAX_EXTENT[orientation]:
        other = "right" if down else "down"
        raise ValueError(
            f"{n_leaves} leaves need {extent:.0f}px along the leaf axis; the "
            f"{orientation!r} budget is {MAX_EXTENT[orientation]:.0f}px. "
            f"Pass collapse_over= (2–{MAX_BREADTH}) to fold overflow siblings "
            f"into '+N more' nodes"
            + (f", try orientation={other!r} (stacks leaves vertically)"
               if down else "")
            + ", or split into an overview plus one figure per subtree.")

    n_ranks = max(n["depth"] for n in nodes) + 1
    if down:
        rank_pos = [d * (box_h + rank_gap) for d in range(n_ranks)]
    else:
        rank_pos, x = [], 0.0
        for d in range(n_ranks):
            rank_pos.append(x)
            x += rank_w[d] + rank_gap

    # Canvas. The tree sits at (ox, oy); the title may widen the canvas.
    title_w = text_width(title, 20, char_width_ratio=RATIO_SANS_BOLD) if title else 0.0
    if down:
        tree_w, tree_h = extent, rank_pos[-1] + box_h
    else:
        tree_w, tree_h = rank_pos[-1] + rank_w[n_ranks - 1], extent
    ox, oy = pad, title_h + pad
    width = int(grow_to_fit(0, max(tree_w, title_w) + 2 * pad))
    height = int(grow_to_fit(0, oy + tree_h + pad))
    if down:  # centre the tree when the title made the canvas wider
        ox = (width - tree_w) / 2

    # Box geometry per node: (x, y, w, h) and the leaf-axis centre.
    boxes: list[tuple[float, float, float, float]] = []
    for i, n in enumerate(nodes):
        w = widths[i]
        if down:
            cx = ox + leaf_pos[i]
            boxes.append((cx - w / 2, oy + rank_pos[n["depth"]], w, box_h))
        else:
            cy = oy + leaf_pos[i]
            boxes.append((ox + rank_pos[n["depth"]], cy - box_h / 2, w, box_h))

    # ── Emit ────────────────────────────────────────────────────────
    parts: list[str] = []
    if desc is None:
        clauses = [f"root: {nodes[0]['label']}"]
        for n in nodes:
            if not n["children"]:
                continue
            kids = []
            for c in n["children"]:
                cn = nodes[c]
                if cn["collapsed"]:
                    kids.append(f"{cn['collapsed']} more not shown "
                                f"({', '.join(cn['hidden'])})")
                else:
                    kids.append(cn["label"])
            clauses.append(f"{n['label']} contains {', '.join(kids)}")
        focal = [n for n in nodes if n["focal"]]
        if focal:
            clauses.append(f"highlighted: {focal[0]['label']}")
        desc = default_desc(
            f"Tree with {len(nodes)} nodes over {n_ranks} levels", title, clauses)
    parts.append(svg_open(
        width=width, height=height,
        slug=figure_slug(out_path, "dendrogram"),
        title=title or "Tree", desc=desc,
        attrs=f'font-family="{escape(t["body_font"])}"',
    ))
    parts.append(f'<rect width="{width}" height="{height}" fill="{t["bg"]}"/>')
    if title:
        parts.append(
            f'<text x="{pad}" y="{title_h - 24:.1f}" fill="{t["ink"]}" '
            f'font-size="20" font-weight="600" text-anchor="start">'
            f'{escape(title)}</text>')

    # Connectors first, so node fills sit on top of line ends.
    def line(kind: str, frm: int, x1, y1, x2, y2, to: Optional[int] = None) -> str:
        to_attr = f' data-to="n{to}"' if to is not None else ""
        return (f'<line data-edge="{kind}" data-from="n{frm}"{to_attr} '
                f'x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{t["flow"]}" stroke-width="1"/>')

    parts.append('<g data-layer="connectors" fill="none">')
    for i, n in enumerate(nodes):
        if not n["children"]:
            continue
        px, py, pw, ph = boxes[i]
        kids = n["children"]
        if down:
            pcx = px + pw / 2
            bus = py + ph + rank_gap / 2
            parts.append(line("stem", i, pcx, py + ph, pcx, bus))
            first = boxes[kids[0]][0] + boxes[kids[0]][2] / 2
            last = boxes[kids[-1]][0] + boxes[kids[-1]][2] / 2
            if len(kids) > 1:
                parts.append(line("bus", i, first, bus, last, bus))
            for c in kids:
                cx_, cy_, cw_, _ = boxes[c]
                ccx = cx_ + cw_ / 2
                parts.append(line("drop", i, ccx, bus, ccx, cy_, to=c))
        else:
            pcy = py + ph / 2
            bus = rank_pos[n["depth"]] + ox + rank_w[n["depth"]] + rank_gap / 2
            parts.append(line("stem", i, px + pw, pcy, bus, pcy))
            first = boxes[kids[0]][1] + boxes[kids[0]][3] / 2
            last = boxes[kids[-1]][1] + boxes[kids[-1]][3] / 2
            if len(kids) > 1:
                parts.append(line("bus", i, bus, first, bus, last))
            for c in kids:
                cx_, cy_, _, ch_ = boxes[c]
                ccy = cy_ + ch_ / 2
                parts.append(line("drop", i, bus, ccy, cx_, ccy, to=c))
    parts.append('</g>')

    # Nodes.
    for i, (n, fit) in enumerate(zip(nodes, fits)):
        x, y, w, h = boxes[i]
        if n["focal"]:
            fill, stroke, sw = t["focal_fill"], t["accent"], 1.5
        elif n["children"]:
            fill, stroke, sw = t["paper"], t["branch"], 1
        else:
            fill, stroke, sw = t["paper"], t["hairline"], 1
        dash = ' stroke-dasharray="4 3"' if n["collapsed"] else ""
        parent = f' data-parent="n{n["parent"]}"' if n["parent"] is not None else ""
        collapsed = f' data-collapsed="{n["collapsed"]}"' if n["collapsed"] else ""
        focal = ' data-focal="true"' if n["focal"] else ""
        parts.append(f'<g data-node="n{i}" data-depth="{n["depth"]}"'
                     f'{parent}{collapsed}{focal}>')
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="4" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')
        cx, cy = x + w / 2, y + h / 2
        block = len(fit.lines) * line_h + (sub_h if n["sublabel"] else 0)
        top = cy - block / 2
        name_fill = (legible_on([t["muted"], t["ink"]], fill, t["bg"])
                     if n["collapsed"] else t["ink"])
        weight = "500" if n["collapsed"] else "600"
        for li, ln in enumerate(fit.lines):
            parts.append(
                f'<text x="{cx:.1f}" y="{top + 12 + li * line_h:.1f}" '
                f'fill="{name_fill}" font-size="{name_fs}" '
                f'font-weight="{weight}" text-anchor="middle">{escape(ln)}</text>')
        if n["sublabel"]:
            sub_fill = legible_on([t["muted"], t["ink"]], fill, t["bg"])
            parts.append(
                f'<text x="{cx:.1f}" y="{top + len(fit.lines) * line_h + 12:.1f}" '
                f'fill="{sub_fill}" font-family="{_MONO}" font-size="{sub_fs}" '
                f'text-anchor="middle">{escape(n["sublabel"])}</text>')
        parts.append('</g>')

    parts.append('</svg>')

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return str(out)


def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.dendrogram spec.json out.svg``.

    Spec format::

        {
          "title": "Eye-movement events",
          "orientation": "down",
          "collapse_over": 5,
          "tree": {
            "label": "Eye-movement events",
            "children": [
              {"label": "Fixation", "children": [
                {"label": "Microsaccade", "focal": true}, "Drift", "Tremor"]},
              {"label": "Saccade", "children": ["Reflexive", "Voluntary"]}
            ]
          },
          "brand": "examples/muriel-brand.toml"
        }
    """
    import argparse, json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.dendrogram")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    dendrogram(
        spec["tree"],
        orientation=spec.get("orientation", "down"),
        collapse_over=spec.get("collapse_over"),
        title=spec.get("title"),
        brand=brand,
        out_path=args.output,
        desc=spec.get("desc"),
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
