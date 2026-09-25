"""
muriel.tools.diagrams.sankey — conserved magnitude flow across 2–3 stages, as SVG.

When to use
-----------
A **quantity** that splits and merges as it moves through a small number
of stages, where the reader must compare how much went where: sessions
by first action and outcome, a compute budget by stage and result,
headcount by source and destination. This is the one diagram in the
family where **band thickness is the data**, so its precondition is
strict:

- every flow carries a measured magnitude in one shared unit;
- the quantity is **conserved** — each stage sums to the same total, and
  every middle node passes on exactly what it receives. Volume that
  leaves the story is drawn as a named node in the last stage
  ("Abandoned"), never allowed to evaporate between stages;
- something actually **splits or merges**. The branching is the claim.

Anti-prescription
-----------------
- **Equal weights → DAG, not Sankey.** If every flow is the same size, or
  the sizes aren't measured, thickness encodes nothing: you've drawn a
  directed graph with fat edges. Draw the graph.
- **No splits or merges → funnel.** A single narrowing quantity is a
  :func:`~muriel.tools.diagrams.pyramid` with ``orientation="down",
  proportional=True``.
- **A plain step sequence → process.** If nothing branches and nothing
  varies in thickness, it is a process diagram (``swimlane`` when owners
  matter, the infographics Process template otherwise).
- **Don't draw a fourth stage.** Past three columns the ribbons tangle and
  the eye can no longer follow one unit of volume end to end; split into
  two linked Sankeys that share the middle stage.
- **Don't colour per flow.** One muted treatment for ordinary ribbons, one
  accent for the single path the figure is about.

Geometry
--------
- Node bars are 12px wide; bar height is ``value × k`` with **one** global
  px-per-unit ``k``. Heights are data and are *not* rounded to the 4px
  grid (the upstream reference rounds; a bar that disagrees with the
  number printed beside it spends the chart's only credibility). Column
  positions, gaps and margins stay on the grid.
- Each flow gets its own slice of its source's and target's height.
  Outgoing slices stack in the order of their targets' vertical position,
  incoming slices in the order of their sources', which keeps every bar
  exactly saturated and removes the crossings a slice order can remove.
  Node order within a stage is the caller's.
- A ribbon is one closed, unstroked path: the top edge is the cubic
  ``M sx,y0 C mx,y0 mx,y1 tx,y1`` with **both** control points on the
  corridor midline, so it leaves and arrives horizontally and plugs into
  its bar square-on; the bottom edge is the same curve reversed. The
  curve is written **flattened to a polyline** (48 segments per edge,
  sub-pixel chord error). That is a contrast decision, not a shortcut:
  ``muriel.contrast`` scores text against straight-edged shapes exactly
  but can only bound a Bézier by its box, and every ribbon's box covers
  the middle stage's labels — so a curve-written Sankey could never pass
  ``muriel diagram-check``. The polyline makes the colour under every
  label computable.
- A ribbon thinner than 4px can't be seen. The plot first grows (up to
  640px of bar height) until the thinnest flow reaches 4px; past that the
  call **raises** and names the flow, rather than folding it into an
  invented "Other" band. Merging small flows is a claim about the data,
  so the caller makes it, in the spec, where it is visible.
- Labels: first stage end-anchored outside left, last stage
  start-anchored outside right, middle stage centred in the gutter above
  its bar (the gap the ribbons leave). The gap grows to hold the label,
  and the column spacing grows until no ribbon crosses a middle label.
  No arrowheads — direction is the column order.

Layout conventions (bar width, midline control points, one accent path,
column-specific label placement, the 8-node / 12-flow budget) are adapted
from the MIT-licensed diagram-design skill (© 2025 Cathryn Lavery),
``references/type-sankey.md``; the conservation and value-fidelity
invariants follow its ``scripts/verify-sankey.py``. The tokens, the 8:1
contrast rule, the raise-don't-fold policy and the epistemic gate are
muriel's own.
"""

from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import Optional, Sequence, Union

from ._a11y import default_desc, figure_slug, legible_on, svg_open
from ._labels import (
    RATIO_MONO,
    RATIO_SANS_BOLD,
    grow_to_fit,
    label_bbox,
    text_width,
)

__all__ = ["sankey"]

_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

MAX_STAGES = 3
MAX_NODES = 8
MAX_FLOWS = 12
MIN_RIBBON_PX = 4.0
BAR_W = 12
SEGMENTS = 48           # polyline segments per ribbon edge
REL_TOL = 1e-6          # conservation tolerance, relative to the stage total


# ─── Brand → tokens ─────────────────────────────────────────────────

def _resolve(brand) -> dict:
    if brand is None:
        return {
            "bg":           "#0a0a0f",
            "ink":          "#e6e4d2",
            "muted":        "#b0b0c4",
            "accent":       "#7dd4e4",
            "ribbon":       "rgba(176, 176, 196, 0.18)",
            "ribbon_focal": "rgba(125, 212, 228, 0.28)",
            "body_font":    "ui-sans-serif, -apple-system, system-ui, sans-serif",
        }
    c = brand.colors
    viz = brand.viz.categorical if brand.viz.categorical else []
    accent = viz[0] if viz else (c.foreground or "#7dd4e4")
    ink = c.foreground
    muted = c.foreground_muted or ink
    return {
        "bg":           c.background,
        "ink":          ink,
        "muted":        muted,
        "accent":       accent,
        "ribbon":       _rgba(muted, 0.18),
        "ribbon_focal": _rgba(accent, 0.28),
        "body_font":    brand.typography.body_family or "system-ui, sans-serif",
    }


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def _fmt(v: float) -> str:
    v = float(v)
    return f"{int(v):,}" if v.is_integer() else f"{v:,g}"


# ─── Validation ─────────────────────────────────────────────────────

def _normalize(stages, nodes, flows, focal):
    stage_labels = [s if isinstance(s, str) else s.get("label", "")
                    for s in stages]
    n_st = len(stage_labels)
    if n_st < 2:
        raise ValueError(f"sankey needs 2–3 stages; got {n_st}. One stage has "
                         f"nothing to flow into — use a bar chart.")
    if n_st > MAX_STAGES:
        raise ValueError(
            f"sankey supports 2–3 stages; got {n_st} ({', '.join(stage_labels)}). "
            f"Past three columns the ribbons tangle — split into two linked "
            f"Sankeys that share a stage, e.g. {stage_labels[:3]} and "
            f"{stage_labels[2:]}.")

    if len(nodes) > MAX_NODES or len(flows) > MAX_FLOWS:
        raise ValueError(
            f"sankey budget is ≤{MAX_NODES} nodes and ≤{MAX_FLOWS} flows; got "
            f"{len(nodes)} nodes and {len(flows)} flows. Fold the smallest "
            f"nodes of a stage into a named 'Other' node, or split into an "
            f"overview Sankey plus a detail one.")

    norm_nodes: dict[str, dict] = {}
    for i, n in enumerate(nodes):
        nid = str(n["id"])
        if nid in norm_nodes:
            raise ValueError(f"duplicate node id {nid!r}")
        st = n["stage"]
        if isinstance(st, str):
            if st not in stage_labels:
                raise ValueError(f"node {nid!r} names unknown stage {st!r}; "
                                 f"stages are {stage_labels}")
            st = stage_labels.index(st)
        if not 0 <= int(st) < n_st:
            raise ValueError(f"node {nid!r} stage index {st} out of range")
        value = float(n["value"])
        if not (math.isfinite(value) and value > 0):
            raise ValueError(f"node {nid!r} needs a finite positive value; "
                             f"got {n['value']!r}")
        norm_nodes[nid] = {"id": nid, "stage": int(st), "value": value,
                           "label": n.get("label", nid), "order": i}

    for s in range(n_st):
        if not any(n["stage"] == s for n in norm_nodes.values()):
            raise ValueError(f"stage {stage_labels[s]!r} has no nodes")

    norm_flows = []
    seen_fids: set[str] = set()
    for f in flows:
        src, dst = str(f["src"]), str(f["dst"])
        for end in (src, dst):
            if end not in norm_nodes:
                raise ValueError(f"flow {src!r} → {dst!r} names unknown node "
                                 f"{end!r}")
        a, b = norm_nodes[src], norm_nodes[dst]
        if b["stage"] != a["stage"] + 1:
            raise ValueError(
                f"flow {src!r} → {dst!r} runs from stage "
                f"{stage_labels[a['stage']]!r} to {stage_labels[b['stage']]!r}; "
                f"flows join adjacent stages, left to right")
        value = float(f["value"])
        if not (math.isfinite(value) and value > 0):
            raise ValueError(f"flow {src!r} → {dst!r} needs a finite positive "
                             f"value; got {f['value']!r}")
        fid = str(f.get("id") or f"{src}->{dst}")
        if fid in seen_fids:
            raise ValueError(f"duplicate flow {fid!r}; merge parallel flows "
                             f"into one")
        seen_fids.add(fid)
        norm_flows.append({"id": fid, "src": src, "dst": dst, "value": value,
                           "order": len(norm_flows)})

    # ── Conservation ────────────────────────────────────────────────
    totals = [sum(n["value"] for n in norm_nodes.values() if n["stage"] == s)
              for s in range(n_st)]
    tol = REL_TOL * max(totals)
    if max(totals) - min(totals) > tol:
        per = ", ".join(f"{stage_labels[s]} = {_fmt(totals[s])}"
                        for s in range(n_st))
        raise ValueError(
            f"stage totals differ ({per}). A Sankey claims volume is "
            f"conserved; draw what leaves as a named node in the last stage "
            f"rather than letting it vanish.")
    problems = []
    for n in norm_nodes.values():
        out_v = sum(f["value"] for f in norm_flows if f["src"] == n["id"])
        in_v = sum(f["value"] for f in norm_flows if f["dst"] == n["id"])
        if n["stage"] < n_st - 1 and abs(out_v - n["value"]) > tol:
            problems.append(f"{n['id']!r} is {_fmt(n['value'])} but sends "
                            f"{_fmt(out_v)}")
        if n["stage"] > 0 and abs(in_v - n["value"]) > tol:
            problems.append(f"{n['id']!r} is {_fmt(n['value'])} but receives "
                            f"{_fmt(in_v)}")
    if problems:
        raise ValueError("flows don't balance: " + "; ".join(problems))

    # ── Focal path ──────────────────────────────────────────────────
    focal_ids: list[str] = []
    if focal:
        focal = [str(x) for x in focal]
        by_pair = {(f["src"], f["dst"]): f["id"] for f in norm_flows}
        if len(focal) >= 2 and all(x in norm_nodes for x in focal):
            for a, b in zip(focal, focal[1:]):
                if (a, b) not in by_pair:
                    raise ValueError(f"focal path steps {a!r} → {b!r}, which "
                                     f"is not a flow")
                focal_ids.append(by_pair[(a, b)])
        elif all(x in seen_fids for x in focal):
            focal_ids = list(focal)
        else:
            raise ValueError(
                f"focal {focal!r} must be a path of ≥2 node ids joined by "
                f"flows, or a list of flow ids ('src->dst' or a flow's 'id')")
    return stage_labels, norm_nodes, norm_flows, set(focal_ids)


# ─── Geometry helpers ───────────────────────────────────────────────

def _bezier_edge(sx, y0, tx, y1, n=SEGMENTS):
    """Points on ``M sx,y0 C mx,y0 mx,y1 tx,y1``, both controls on the midline."""
    mx = (sx + tx) / 2
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u ** 3 * sx + 3 * u * u * t * mx + 3 * u * t * t * mx + t ** 3 * tx
        y = u ** 3 * y0 + 3 * u * u * t * y0 + 3 * u * t * t * y1 + t ** 3 * y1
        pts.append((x, y))
    return pts


def _span_at(edge, x):
    """Interpolated y of an x-monotone polyline at ``x`` (None if outside)."""
    if x < edge[0][0] or x > edge[-1][0]:
        return None
    for (xa, ya), (xb, yb) in zip(edge, edge[1:]):
        if xa <= x <= xb:
            return ya if xb == xa else ya + (yb - ya) * (x - xa) / (xb - xa)
    return edge[-1][1]


def _ribbon_hits(top, bot, box, pad=2.0) -> bool:
    """Does a ribbon (top/bottom edge polylines) cross a label box?"""
    x0, x1 = box.x0 - pad, box.x1 + pad
    xs = [x0, x1] + [p[0] for p in top if x0 < p[0] < x1]
    for x in xs:
        a, b = _span_at(top, x), _span_at(bot, x)
        if a is None or b is None:
            continue
        if a < box.y1 + pad and b > box.y0 - pad:
            return True
    return False


# ─── SVG ────────────────────────────────────────────────────────────

def sankey(
    stages: Sequence,
    nodes: Sequence[dict],
    flows: Sequence[dict],
    *,
    focal: Optional[Sequence[str]] = None,
    focal_label: Optional[str] = None,
    unit: Optional[str] = None,
    title: Optional[str] = None,
    brand=None,
    out_path: Union[str, Path] = "sankey.svg",
    width: int = 960,
    desc: Optional[str] = None,
) -> str:
    """Render a 2–3 stage Sankey whose ribbon widths are conserved volume.

    Parameters
    ----------
    stages
        2–3 stage names, left to right (strings or ``{"label": str}``).
        More than three raises: split into linked Sankeys.
    nodes
        ``[{"id": str, "stage": str|int, "label": str, "value": float}]``.
        ``stage`` is a stage name or index. Order within a stage is kept,
        top to bottom. Every stage must sum to the same total. Budget: ≤8.
    flows
        ``[{"src": id, "dst": id, "value": float, "id": str?}]`` between
        adjacent stages only. A first-stage node's outgoing flows must sum
        to its value, a last-stage node's incoming flows likewise, and a
        middle node must send exactly what it receives. Violations raise
        with the numbers. Budget: ≤12. A flow's id defaults to
        ``"src->dst"``.
    focal
        The one path the figure is about: node ids in stage order
        (``["sessions", "ad", "reformulated"]``) or flow ids. Its ribbons
        are drawn in the accent and painted last; everything else is muted.
    focal_label
        Legend text for the focal path. Defaults to the path's node labels
        joined by arrows. The legend is only drawn when ``focal`` is set,
        so the highlight is named in words, not colour alone.
    unit
        Appended to every printed value (``"4,600 sessions"``).
    title
        Optional heading above the figure.
    brand
        Optional ``muriel.styleguide.StyleGuide``.
    out_path
        Where to write the SVG. Its stem also prefixes the accessible
        ``<title>``/``<desc>`` ids.
    width
        Starting canvas width; it grows if labels or ribbons need room.
    desc
        What the figure argues, for the SVG ``<desc>``. Defaults to a
        conservative listing of stages, nodes and flows from the spec.

    Returns
    -------
    str
        The path written. Every node ``<rect>`` and ribbon ``<path>``
        carries ``data-value`` (and ribbons ``data-src``/``data-dst``) so
        conservation can be recomputed from the file alone.
    """
    stage_labels, nd, fl, focal_ids = _normalize(stages, nodes, flows, focal)
    n_st = len(stage_labels)
    t = _resolve(brand)
    unit_sfx = f" {unit}" if unit else ""

    cols = [sorted((n for n in nd.values() if n["stage"] == s),
                   key=lambda n: n["order"]) for s in range(n_st)]
    total = sum(n["value"] for n in cols[0])

    # ── Type metrics (4px grid) ─────────────────────────────────────
    name_fs, val_fs = 13, 10
    val_dy = 15                 # value baseline below the name baseline
    lab_gap = 10                # bar edge to an outside label
    pad_x = 24
    head_fs = 11
    head_ls = 1.5

    def _labels_of(n):
        return n["label"], f"{_fmt(n['value'])}{unit_sfx}"

    def _block(n, x, name_y, anchor):
        name, val = _labels_of(n)
        a = label_bbox(name, name_fs, x, name_y, text_anchor=anchor,
                       char_width_ratio=RATIO_SANS_BOLD)
        b = label_bbox(val, val_fs, x, name_y + val_dy, text_anchor=anchor,
                       char_width_ratio=RATIO_MONO)
        return type(a)(min(a.x0, b.x0), min(a.y0, b.y0),
                       max(a.x1, b.x1), max(a.y1, b.y1))

    probe = _block(cols[0][0], 0, 0, "start")
    asc = -probe.y0                         # name cap top above its baseline
    block_h = probe.y1 - probe.y0           # name + value, top to bottom

    def _block_w(n):
        name, val = _labels_of(n)
        return max(text_width(name, name_fs, char_width_ratio=RATIO_SANS_BOLD),
                   text_width(val, val_fs, char_width_ratio=RATIO_MONO))

    # ── Scale: one k for every bar and ribbon ───────────────────────
    plot_h = 320.0
    min_flow = min(f["value"] for f in fl)
    if min_flow * plot_h / total < MIN_RIBBON_PX:
        need = MIN_RIBBON_PX * total / min_flow
        if need > 640:
            thin = min(fl, key=lambda f: f["value"])
            raise ValueError(
                f"flow {thin['id']!r} ({_fmt(thin['value'])} of "
                f"{_fmt(total)}) would draw under {MIN_RIBBON_PX:.0f}px even "
                f"at the tallest plot; a ribbon nobody can see isn't "
                f"communicating. Merge it with its neighbours into a named "
                f"'Other' node in the spec.")
        plot_h = grow_to_fit(plot_h, need)
    k = plot_h / total

    # ── Vertical gaps between nodes ─────────────────────────────────
    #
    # One gap for the whole figure, so stages read as one system. Middle
    # labels sit in the gutter above their bar, so that gutter must hold
    # the two-line block; outer labels are centred on their bar, so the
    # gap must keep neighbouring blocks from touching.
    gap = 24.0
    if n_st == 3:
        gap = max(gap, block_h + 12)
    for s in (0, n_st - 1):
        for a, b in zip(cols[s], cols[s][1:]):
            ha, hb = a["value"] * k, b["value"] * k
            gap = max(gap, block_h + 6 - (ha + hb) / 2)
    gap = grow_to_fit(24.0, gap)

    # ── Horizontal layout ───────────────────────────────────────────
    left_w = max(_block_w(n) for n in cols[0])
    right_w = max(_block_w(n) for n in cols[-1])
    head_w = [text_width(s.upper(), head_fs, char_width_ratio=RATIO_MONO,
                         letter_spacing=head_ls) for s in stage_labels]
    x_first = grow_to_fit(0, max(pad_x + left_w + lab_gap,
                                 pad_x + head_w[0] / 2 - BAR_W / 2))
    right_need = max(lab_gap + right_w + pad_x,
                     head_w[-1] / 2 - BAR_W / 2 + pad_x)
    mid_w = max((_block_w(n) for n in cols[1]), default=0) if n_st == 3 else 0
    min_span = max(200.0, mid_w + 64)
    title_w = text_width(title, 20, char_width_ratio=RATIO_SANS_BOLD) if title else 0
    width = int(grow_to_fit(width, title_w + 2 * pad_x))

    title_h = 64 if title else 0
    head_y = title_h + 40               # stage-header baseline
    plot_top = head_y + 24.0

    def _layout(span):
        xs = [x_first + i * span for i in range(n_st)]
        # stack height per column; middle column also carries the label
        # gutter above its first bar
        stack = []
        for s in range(n_st):
            h = sum(n["value"] * k for n in cols[s]) + gap * (len(cols[s]) - 1)
            if 0 < s < n_st - 1:
                h += gap
            stack.append(h)
        tallest = max(stack)
        ys = {}
        for s in range(n_st):
            y = plot_top + (tallest - stack[s]) / 2
            if 0 < s < n_st - 1:
                y += gap
            # outer labels are centred on the bar; keep the first one clear
            # of the header row
            for n in cols[s]:
                ys[n["id"]] = y
                y += n["value"] * k + gap
        return xs, ys, tallest

    def _ribbons(xs, ys):
        out_off = {n: 0.0 for n in nd}
        in_off = {n: 0.0 for n in nd}
        # outgoing slices ordered by target position, incoming by source
        pos = lambda nid: (ys[nid], nd[nid]["order"])
        order_out = sorted(fl, key=lambda f: (pos(f["src"]), pos(f["dst"]),
                                              f["order"]))
        s_top = {}
        for f in order_out:
            s_top[f["id"]] = ys[f["src"]] + out_off[f["src"]]
            out_off[f["src"]] += f["value"] * k
        order_in = sorted(fl, key=lambda f: (pos(f["dst"]), pos(f["src"]),
                                             f["order"]))
        t_top = {}
        for f in order_in:
            t_top[f["id"]] = ys[f["dst"]] + in_off[f["dst"]]
            in_off[f["dst"]] += f["value"] * k
        rib = {}
        for f in fl:
            sx = xs[nd[f["src"]]["stage"]] + BAR_W
            tx = xs[nd[f["dst"]]["stage"]]
            th = f["value"] * k
            y0, y1 = s_top[f["id"]], t_top[f["id"]]
            top = _bezier_edge(sx, y0, tx, y1)
            bot = _bezier_edge(sx, y0 + th, tx, y1 + th)
            rib[f["id"]] = (top, bot)
        return rib

    def _mid_boxes(xs, ys):
        boxes = []
        if n_st != 3:
            return boxes
        for n in cols[1]:
            cx = xs[1] + BAR_W / 2
            name_y = ys[n["id"]] - gap / 2 - block_h / 2 + asc
            boxes.append((n, cx, name_y, _block(n, cx, name_y, "middle")))
        return boxes

    # Widen the corridors until no ribbon crosses a middle-stage label.
    # Ribbons flatten near their bars as the corridor lengthens, so this
    # converges; the contrast audit still scores anything left over.
    span = max(min_span, (width - x_first - right_need - BAR_W) / (n_st - 1))
    span = grow_to_fit(0, span)
    for _ in range(12):
        xs, ys, tallest = _layout(span)
        rib = _ribbons(xs, ys)
        mids = _mid_boxes(xs, ys)
        clash = any(_ribbon_hits(top, bot, box)
                    for (_n, _cx, _y, box) in mids
                    for top, bot in rib.values())
        if not clash:
            break
        span += 48

    # An outer label centred on a short top bar can rise above the stack;
    # push the plot down until every label clears the stage headers.
    label_tops = [ys[n["id"]] + n["value"] * k / 2 - block_h / 2
                  for s in (0, n_st - 1) for n in cols[s]]
    label_tops += [box.y0 for (_n, _cx, _y, box) in mids]
    shift = (head_y + 16) - min(label_tops)
    if shift > 0:
        plot_top = grow_to_fit(plot_top, plot_top + shift)
        xs, ys, tallest = _layout(span)
        rib = _ribbons(xs, ys)
    width = int(grow_to_fit(width, xs[-1] + BAR_W + right_need))

    # ── Legend + canvas height ──────────────────────────────────────
    plot_bot = plot_top + tallest
    outer_bot = max(
        ys[n["id"]] + n["value"] * k / 2 - asc + block_h
        for s in (0, n_st - 1) for n in cols[s])
    content_bot = max(plot_bot, outer_bot)
    legend_txt = None
    if focal_ids:
        if focal_label:
            legend_txt = focal_label
        else:
            path_nodes = []
            for f in sorted((f for f in fl if f["id"] in focal_ids),
                            key=lambda f: nd[f["src"]]["stage"]):
                for end in (f["src"], f["dst"]):
                    lab = nd[end]["label"]
                    if not path_nodes or path_nodes[-1] != lab:
                        path_nodes.append(lab)
            legend_txt = "Highlighted: " + " → ".join(path_nodes)
    legend_y = content_bot + 36
    height = (legend_y + 32) if legend_txt else (content_bot + 40)
    height = grow_to_fit(0, height)
    lw = text_width(legend_txt, 11, char_width_ratio=0.62) if legend_txt else 0
    width = int(grow_to_fit(width, x_first + 24 + lw + pad_x))

    # ── Description ─────────────────────────────────────────────────
    if desc is None:
        parts_d = [
            "stages, left to right: " + ", ".join(
                f"{stage_labels[s]} (" + ", ".join(
                    f"{n['label']} {_fmt(n['value'])}" for n in cols[s]) + ")"
                for s in range(n_st)),
            "flows: " + ", ".join(
                f"{nd[f['src']]['label']} to {nd[f['dst']]['label']} "
                f"{_fmt(f['value'])}" for f in fl),
            f"each stage totals {_fmt(total)}{unit_sfx}",
            (legend_txt or ""),
        ]
        desc = default_desc(
            f"Sankey with {n_st} stages, {len(nd)} nodes and {len(fl)} flows",
            title, parts_d)

    parts: list[str] = []
    parts.append(svg_open(
        width=width, height=height,
        slug=figure_slug(out_path, "sankey"),
        title=title or "Sankey", desc=desc,
        attrs=f'font-family="{escape(t["body_font"])}"',
    ))
    parts.append(f'<rect width="{width}" height="{height}" fill="{t["bg"]}"/>')

    if title:
        parts.append(
            f'<text x="{pad_x}" y="{title_h - 16:.1f}" fill="{t["ink"]}" '
            f'font-size="20" font-weight="600" text-anchor="start">'
            f'{escape(title)}</text>')

    for s, label in enumerate(stage_labels):
        parts.append(
            f'<text x="{xs[s] + BAR_W / 2:.1f}" y="{head_y:.1f}" '
            f'fill="{t["muted"]}" font-family="{_MONO}" font-size="{head_fs}" '
            f'letter-spacing="{head_ls}" text-anchor="middle">'
            f'{escape(label.upper())}</text>')

    # ── Ribbons: ordinary first, the focal path last ────────────────
    def _d(top, bot):
        pts = top + bot[::-1]
        head = f"M{pts[0][0]:.2f},{pts[0][1]:.2f}"
        body = " ".join(f"L{x:.2f},{y:.2f}" for x, y in pts[1:])
        return f"{head} {body} Z"

    for is_focal in (False, True):
        for f in fl:
            if (f["id"] in focal_ids) != is_focal:
                continue
            top, bot = rib[f["id"]]
            fill = t["ribbon_focal"] if is_focal else t["ribbon"]
            parts.append(
                f'<path d="{_d(top, bot)}" fill="{fill}" '
                f'data-flow="{escape(f["id"])}" data-src="{escape(f["src"])}" '
                f'data-dst="{escape(f["dst"])}" data-value="{f["value"]:g}"'
                + (' data-focal="true"' if is_focal else "") + '/>')

    # ── Node bars ───────────────────────────────────────────────────
    for s in range(n_st):
        for n in cols[s]:
            parts.append(
                f'<rect x="{xs[s]:.2f}" y="{ys[n["id"]]:.3f}" width="{BAR_W}" '
                f'height="{n["value"] * k:.3f}" fill="{t["ink"]}" '
                f'data-node="{escape(n["id"])}" data-stage="{s}" '
                f'data-value="{n["value"]:g}"/>')

    # ── Labels ──────────────────────────────────────────────────────
    val_fill = legible_on([t["muted"], t["ink"]], t["bg"], t["bg"])

    def _emit(n, x, name_y, anchor):
        name, val = _labels_of(n)
        parts.append(
            f'<text x="{x:.1f}" y="{name_y:.1f}" fill="{t["ink"]}" '
            f'font-size="{name_fs}" font-weight="600" text-anchor="{anchor}">'
            f'{escape(name)}</text>')
        parts.append(
            f'<text x="{x:.1f}" y="{name_y + val_dy:.1f}" fill="{val_fill}" '
            f'font-family="{_MONO}" font-size="{val_fs}" '
            f'text-anchor="{anchor}">{escape(val)}</text>')

    for s, anchor, dx in ((0, "end", -lab_gap),
                          (n_st - 1, "start", BAR_W + lab_gap)):
        for n in cols[s]:
            mid_y = ys[n["id"]] + n["value"] * k / 2
            name_y = mid_y - block_h / 2 + asc
            _emit(n, xs[s] + dx, name_y, anchor)
    for n, cx, name_y, _box in _mid_boxes(xs, ys):
        _emit(n, cx, name_y, "middle")

    # ── Legend: the highlight named in words ────────────────────────
    if legend_txt:
        parts.append(
            f'<rect x="{x_first:.1f}" y="{legend_y - 8:.1f}" width="16" '
            f'height="8" fill="{t["ribbon_focal"]}"/>')
        parts.append(
            f'<text x="{x_first + 24:.1f}" y="{legend_y:.1f}" '
            f'fill="{val_fill}" font-size="11" text-anchor="start">'
            f'{escape(legend_txt)}</text>')

    parts.append("</svg>")

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return str(out)


def _main(argv=None) -> int:
    """CLI: ``python -m muriel.tools.diagrams.sankey spec.json out.svg``.

    Spec format::

        {
          "title":  "Search sessions — first action to outcome",
          "unit":   "sessions",
          "stages": ["Query", "First action", "Outcome"],
          "nodes": [
            {"id": "q",   "stage": "Query",        "label": "Sessions",  "value": 1000},
            {"id": "clk", "stage": "First action", "label": "Click",     "value": 700},
            {"id": "no",  "stage": "First action", "label": "No click",  "value": 300},
            {"id": "sat", "stage": "Outcome",      "label": "Satisfied", "value": 600},
            {"id": "ref", "stage": "Outcome",      "label": "Reformulated", "value": 400}
          ],
          "flows": [
            {"src": "q",   "dst": "clk", "value": 700},
            {"src": "q",   "dst": "no",  "value": 300},
            {"src": "clk", "dst": "sat", "value": 500},
            {"src": "clk", "dst": "ref", "value": 200},
            {"src": "no",  "dst": "sat", "value": 100},
            {"src": "no",  "dst": "ref", "value": 200}
          ],
          "focal": ["q", "no", "ref"],
          "brand": "examples/muriel-brand.toml"
        }
    """
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="python -m muriel.tools.diagrams.sankey")
    ap.add_argument("spec")
    ap.add_argument("output")
    args = ap.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])
    sankey(
        spec["stages"],
        spec["nodes"],
        spec["flows"],
        focal=spec.get("focal"),
        focal_label=spec.get("focal_label"),
        unit=spec.get("unit"),
        title=spec.get("title"),
        brand=brand,
        out_path=args.output,
        desc=spec.get("desc"),
    )
    print(f"→ {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
