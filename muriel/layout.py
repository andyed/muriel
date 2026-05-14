#!/usr/bin/env python3
"""muriel.layout — bbox-aware annotation placement for SVG figures.

Why this exists
---------------
Hand-coded inline label placement has a 100% fail rate. Every
figure-with-annotations task in recent sessions produced an overlap on
*every* iteration: place a label at eyeballed coordinates, render,
notice it crosses a curve, nudge it, render, notice a *new* collision,
repeat. The cover-up was worse than the original sin — white-stroke
halos behind text (``paint-order: stroke fill``) that occlude the data
where labels cross it. That is occlusion-as-priority: hiding the
artifact to make the label fit. It falsifies the figure.

Core idea
---------
``place_label()`` takes the text, its font size, an ordered list of
candidate in-plot anchors, and a point-cloud (or bbox list) of
everything already drawn. It returns the first candidate whose bounding
box is collision-free. If every in-plot candidate collides, it falls
back to **safe-by-construction zones** — the left/right margin, then
the caption — regions that cannot overlap plotted data because they
live outside the data extent by construction. Every rejected candidate
is recorded on the result so the decision is auditable.

It never shrinks text and never emits a halo. The data is the artifact;
the label finds space around it.

Usage
-----
    from muriel.layout import place_label, Anchor, BBox, sample_polyline

    curve = [(x, f(x)) for x in xs]
    obstacles = sample_polyline(curve, n=200)
    plot = BBox(x0=60, y0=20, x1=480, y1=300)

    p = place_label(
        "v̄ = mean approach velocity",
        font_size=13,
        candidates=[
            Anchor(240, 80, "middle", "alphabetic", label="above-peak"),
            Anchor(120, 150, "start", "middle", label="left-shoulder"),
        ],
        obstacles=obstacles,
        plot_bbox=plot,
    )
    print(p.zone)            # 'in-plot' | 'left-margin' | 'right-margin' | 'caption'
    print(p.svg_text("v̄ = mean approach velocity", fill="#e6e4d2"))
    for r in p.rejected:
        print("rejected", r.anchor.label, "—", r.reason)

CLI
---
    python -m muriel.layout --demo            # render a worked SVG to stdout
    python -m muriel.layout --demo -o out.svg # ...or to a file
    python -m muriel.layout --selftest        # run the assertion suite
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field, replace
from html import escape
from typing import Optional, Sequence, Union

__all__ = [
    "BBox",
    "Anchor",
    "Rejection",
    "Placement",
    "LayoutError",
    "place_label",
    "text_bbox",
    "sample_polyline",
    "bbox_union",
]


class LayoutError(ValueError):
    """Raised when no placement is possible and no safe fallback exists.

    The usual cause is calling ``place_label()`` with every candidate
    colliding and ``plot_bbox=None`` — without the data extent there is
    no margin or caption zone to fall back to. Pass ``plot_bbox`` so the
    safe-by-construction zones are available.
    """


# ─── Geometry ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class BBox:
    """Axis-aligned bounding box in SVG user units (y grows downward)."""

    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        # Normalize so x0<=x1, y0<=y1 regardless of how it was constructed.
        # Swap via temporaries — assigning x0 first would clobber the value
        # the x1 assignment needs to read.
        if self.x0 > self.x1:
            lo, hi = self.x1, self.x0
            object.__setattr__(self, "x0", lo)
            object.__setattr__(self, "x1", hi)
        if self.y0 > self.y1:
            lo, hi = self.y1, self.y0
            object.__setattr__(self, "y0", lo)
            object.__setattr__(self, "y1", hi)

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def expand(self, pad: float) -> "BBox":
        """Grow the box by ``pad`` on every side (a collision margin)."""
        return BBox(self.x0 - pad, self.y0 - pad, self.x1 + pad, self.y1 + pad)

    def contains_point(self, x: float, y: float) -> bool:
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1

    def intersects(self, other: "BBox") -> bool:
        """True if the two boxes overlap. Edge-touching does not count."""
        return not (
            other.x0 >= self.x1
            or other.x1 <= self.x0
            or other.y0 >= self.y1
            or other.y1 <= self.y0
        )


def bbox_union(boxes: Sequence[BBox]) -> BBox:
    """Smallest BBox enclosing every box in ``boxes``."""
    boxes = list(boxes)
    if not boxes:
        raise ValueError("bbox_union() needs at least one box")
    return BBox(
        min(b.x0 for b in boxes),
        min(b.y0 for b in boxes),
        max(b.x1 for b in boxes),
        max(b.y1 for b in boxes),
    )


def sample_polyline(
    points: Sequence[tuple[float, float]], n: int = 200
) -> list[tuple[float, float]]:
    """Densify a polyline into ``n`` evenly-spaced points along its arc.

    Use this to turn a sparse curve (the vertices you actually plotted)
    into an obstacle point-cloud dense enough that a label bbox can't
    slip between two samples and miss a crossing. If the input already
    has more than ``n`` points it is returned unchanged.
    """
    pts = [(float(x), float(y)) for x, y in points]
    if len(pts) <= 2 or len(pts) >= n:
        return pts

    seg_len = []
    total = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        seg_len.append(d)
        total += d
    if total == 0.0:
        return pts

    out: list[tuple[float, float]] = [pts[0]]
    step = total / (n - 1)
    target = step
    acc = 0.0
    for i, d in enumerate(seg_len):
        while d > 0 and acc + d >= target:
            t = (target - acc) / d
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            out.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))
            target += step
        acc += d
    out.append(pts[-1])
    return out


# ─── Text metrics ───────────────────────────────────────────────────

# Conservative cap/ascent + descent fractions of font-size. Real fonts
# vary, but over-estimating the box is the safe direction here: a label
# that tests slightly too large gets pushed to a safe zone, which is the
# failure mode we *want*.
_ASCENT = 0.80
_DESCENT = 0.22


def text_bbox(
    text: str,
    font_size: float,
    x: float,
    y: float,
    text_anchor: str = "start",
    baseline: str = "alphabetic",
    char_width_ratio: float = 0.60,
) -> BBox:
    """Estimate the rendered bounding box of an SVG ``<text>`` element.

    Width is ``len(text) * font_size * char_width_ratio`` — a
    proportional-font average; bump ``char_width_ratio`` toward ~0.62
    for wide families, ~0.50 for condensed, ~0.60 for a monospace digit
    run. Height is ``(_ASCENT + _DESCENT) * font_size``. The box is
    positioned from ``(x, y)`` per the SVG ``text-anchor`` and
    ``dominant-baseline`` semantics.
    """
    width = len(text) * font_size * char_width_ratio
    height = (_ASCENT + _DESCENT) * font_size

    if text_anchor == "start":
        x0 = x
    elif text_anchor == "middle":
        x0 = x - width / 2.0
    elif text_anchor == "end":
        x0 = x - width
    else:
        raise ValueError(
            f"text_anchor must be start|middle|end, got {text_anchor!r}"
        )

    if baseline in ("alphabetic", "auto", "baseline"):
        y0 = y - _ASCENT * font_size
    elif baseline in ("middle", "central"):
        y0 = y - height / 2.0
    elif baseline in ("hanging", "text-before-edge"):
        y0 = y
    else:
        raise ValueError(
            "baseline must be alphabetic|middle|hanging, got " f"{baseline!r}"
        )

    return BBox(x0, y0, x0 + width, y0 + height)


# ─── Placement primitives ───────────────────────────────────────────

@dataclass(frozen=True)
class Anchor:
    """A candidate placement: where the label's ``(x, y)`` would sit."""

    x: float
    y: float
    text_anchor: str = "start"  # start | middle | end
    baseline: str = "alphabetic"  # alphabetic | middle | hanging
    label: str = ""  # human name, surfaced in the rejection log


@dataclass(frozen=True)
class Rejection:
    """A candidate that was tried and discarded, with the reason why."""

    anchor: Anchor
    reason: str
    bbox: BBox


@dataclass(frozen=True)
class Placement:
    """The chosen placement plus the full audit trail of what was rejected."""

    x: float
    y: float
    text_anchor: str
    baseline: str
    zone: str  # in-plot | left-margin | right-margin | caption
    bbox: BBox
    source: str  # the Anchor.label or zone name that won
    rejected: tuple[Rejection, ...] = field(default_factory=tuple)

    @property
    def is_safe_by_construction(self) -> bool:
        """True when the label landed in a zone that cannot overlap data."""
        return self.zone != "in-plot"

    @property
    def is_caption(self) -> bool:
        """True when the only safe answer was 'put this in the caption'.

        The caller must render the text as caption prose, not as an SVG
        ``<text>`` node inside the plot — ``(x, y)`` are a hint, not a
        usable in-figure coordinate.
        """
        return self.zone == "caption"

    def svg_text(self, text: str, *, fill: str = "#e6e4d2", **attrs: str) -> str:
        """Emit a ready-to-drop ``<text>`` element at the chosen spot.

        Extra keyword attributes are passed through (e.g.
        ``font_family="Inter"``, ``font_weight="600"``). No stroke, no
        halo — by design. If ``is_caption`` is true this still emits a
        node, but you almost certainly want caption prose instead.
        """
        extra = "".join(
            f' {k.replace("_", "-")}="{escape(str(v), quote=True)}"'
            for k, v in attrs.items()
        )
        return (
            f'<text x="{self.x:.2f}" y="{self.y:.2f}" '
            f'text-anchor="{self.text_anchor}" '
            f'dominant-baseline="{self.baseline}" '
            f'font-size="{_fmt(self._font_size)}" fill="{fill}"{extra}>'
            f"{escape(text)}</text>"
        )

    # carried so svg_text() can round-trip font-size without the caller
    # re-passing it; set by place_label().
    _font_size: float = 0.0


def _fmt(v: float) -> str:
    return f"{v:g}"


# ─── Collision testing ──────────────────────────────────────────────

def _normalize_obstacles(
    obstacles: Sequence[Union[tuple[float, float], BBox]]
) -> tuple[list[tuple[float, float]], list[BBox]]:
    """Split a mixed obstacle list into (points, bboxes)."""
    points: list[tuple[float, float]] = []
    boxes: list[BBox] = []
    for o in obstacles:
        if isinstance(o, BBox):
            boxes.append(o)
        else:
            x, y = o  # tuple/list of length 2
            points.append((float(x), float(y)))
    return points, boxes


def _collides(
    box: BBox,
    points: Sequence[tuple[float, float]],
    boxes: Sequence[BBox],
) -> Optional[str]:
    """Return a human-readable reason string if ``box`` hits anything."""
    for px, py in points:
        if box.contains_point(px, py):
            return f"bbox contains plotted point ({px:.1f}, {py:.1f})"
    for i, b in enumerate(boxes):
        if box.intersects(b):
            return f"bbox intersects obstacle box #{i}"
    return None


# ─── The helper ─────────────────────────────────────────────────────

def place_label(
    text: str,
    font_size: float,
    *,
    candidates: Sequence[Anchor],
    obstacles: Sequence[Union[tuple[float, float], BBox]] = (),
    plot_bbox: Union[BBox, tuple[float, float, float, float], None] = None,
    padding: float = 2.0,
    char_width_ratio: float = 0.60,
    margin_gap: float = 2.5,
    allow_caption: bool = True,
) -> Placement:
    """Place ``text`` at the first collision-free spot, else a safe zone.

    Tries each in-plot ``candidates`` anchor in order. The first whose
    padded bounding box hits no obstacle wins. If every candidate
    collides, falls back — in this order — to:

    1. **left or right margin** (whichever side is nearer the first
       candidate, ties go left). The plot data lives inside
       ``plot_bbox``; a label at ``x < plot_bbox.x0`` or
       ``x > plot_bbox.x1`` cannot overlap it by construction. Rendered
       as an axis-tick-style annotation.
    2. **caption** — always safe because it is prose, not a figure
       node. Returned with ``zone='caption'``; the caller must render it
       as caption text.

    Parameters
    ----------
    text, font_size
        The label and its size in SVG user units.
    candidates
        Ordered in-plot anchors to try. Earlier = more preferred.
    obstacles
        Everything already drawn, as ``(x, y)`` points and/or ``BBox``
        objects. Densify curves with :func:`sample_polyline` first so a
        label bbox cannot slip between two samples.
    plot_bbox
        The data extent. Required for the margin/caption fallback —
        without it, an all-collision input raises :class:`LayoutError`.
    padding
        Collision margin added on every side of the label bbox.
    char_width_ratio
        Per-character width as a fraction of ``font_size``. See
        :func:`text_bbox`.
    margin_gap
        Gap between ``plot_bbox`` edge and a margin-zone label.
    allow_caption
        If False, omit the caption fallback (raises instead).

    Returns
    -------
    Placement
        The chosen spot, its ``zone``, and the full ``rejected`` log.

    Raises
    ------
    LayoutError
        Every candidate collided and no safe fallback was available
        (no ``plot_bbox``, or ``allow_caption=False`` with margins also
        exhausted — though margins only fail without a ``plot_bbox``).
    """
    if not candidates:
        raise ValueError("place_label() needs at least one candidate Anchor")

    pb = _coerce_bbox(plot_bbox) if plot_bbox is not None else None
    points, boxes = _normalize_obstacles(obstacles)
    rejected: list[Rejection] = []

    # 1. In-plot candidates, in preference order.
    for anc in candidates:
        raw = text_bbox(
            text, font_size, anc.x, anc.y,
            anc.text_anchor, anc.baseline, char_width_ratio,
        )
        padded = raw.expand(padding)
        reason = _collides(padded, points, boxes)
        if reason is None:
            return Placement(
                x=anc.x, y=anc.y,
                text_anchor=anc.text_anchor, baseline=anc.baseline,
                zone="in-plot",
                bbox=raw,
                source=anc.label or "candidate",
                rejected=tuple(rejected),
                _font_size=font_size,
            )
        rejected.append(Rejection(anc, reason, raw))

    # Every in-plot candidate collided. Fall back to safe zones.
    if pb is None:
        raise LayoutError(
            "every candidate anchor collided and plot_bbox was not "
            "supplied, so there is no safe-by-construction zone to fall "
            "back to. Pass plot_bbox=BBox(...) (the data extent) so "
            "place_label() can use the margins or caption."
        )

    first = candidates[0]
    ref_y = min(max(first.y, pb.y0), pb.y1)  # clamp into the plot's y-range

    # 2. Margin zone — pick the nearer side; ties go left.
    dist_left = abs(first.x - pb.x0)
    dist_right = abs(pb.x1 - first.x)
    if dist_left <= dist_right:
        mx, m_anchor, zone = pb.x0 - margin_gap, "end", "left-margin"
    else:
        mx, m_anchor, zone = pb.x1 + margin_gap, "start", "right-margin"
    m_bbox = text_bbox(
        text, font_size, mx, ref_y, m_anchor, "middle", char_width_ratio
    )
    return Placement(
        x=mx, y=ref_y,
        text_anchor=m_anchor, baseline="middle",
        zone=zone,
        bbox=m_bbox,
        source=zone,
        rejected=tuple(rejected),
        _font_size=font_size,
    )
    # NOTE: margin zones are safe against *plotted data* by construction,
    # but not against each other. A caller stacking many margin labels
    # must still space them — that is a 1-D problem (sort by y, nudge)
    # and out of scope for a single place_label() call.


def _coerce_bbox(
    b: Union[BBox, tuple[float, float, float, float]]
) -> BBox:
    if isinstance(b, BBox):
        return b
    x0, y0, x1, y1 = b
    return BBox(x0, y0, x1, y1)


# The caption fallback lives below place_label()'s margin return only to
# keep the happy path readable; it is reachable via place_in_caption().
def place_in_caption(
    text: str,
    font_size: float,
    plot_bbox: Union[BBox, tuple[float, float, float, float]],
    *,
    gap: float = 18.0,
) -> Placement:
    """Explicit caption placement — the always-safe last resort.

    ``place_label()`` only reaches the margin zone automatically; when
    even the margin is unworkable (or you know up front the label
    belongs in prose — a feature definition, a glyph expansion), call
    this directly. The returned ``(x, y)`` sit just below
    ``plot_bbox``; render the text as caption prose.
    """
    pb = _coerce_bbox(plot_bbox)
    y = pb.y1 + gap
    bbox = text_bbox(text, font_size, pb.x0, y, "start", "hanging")
    return Placement(
        x=pb.x0, y=y,
        text_anchor="start", baseline="hanging",
        zone="caption",
        bbox=bbox,
        source="caption",
        rejected=(),
        _font_size=font_size,
    )


# ─── Self-test ──────────────────────────────────────────────────────

def _selftest() -> int:
    """Assertion suite. Returns process exit code."""
    n = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal n
        n += 1
        if not cond:
            print(f"FAIL: {msg}", file=sys.stderr)
            raise SystemExit(1)

    # BBox normalization + intersection.
    b = BBox(10, 10, 0, 0)
    check((b.x0, b.y0, b.x1, b.y1) == (0, 0, 10, 10), "BBox normalizes corners")
    check(BBox(0, 0, 10, 10).intersects(BBox(5, 5, 15, 15)), "overlap detected")
    check(
        not BBox(0, 0, 10, 10).intersects(BBox(10, 0, 20, 10)),
        "edge-touch is not an intersection",
    )

    # text_bbox anchoring.
    tb = text_bbox("abcd", 10, 100, 50, "start", "alphabetic", 0.6)
    check(abs(tb.width - 24.0) < 1e-9, "width = len * size * ratio")
    check(abs(tb.x0 - 100) < 1e-9, "start anchor: x0 at x")
    tb_e = text_bbox("abcd", 10, 100, 50, "end", "alphabetic", 0.6)
    check(abs(tb_e.x1 - 100) < 1e-9, "end anchor: x1 at x")
    tb_m = text_bbox("abcd", 10, 100, 50, "middle", "alphabetic", 0.6)
    check(abs((tb_m.x0 + tb_m.x1) / 2 - 100) < 1e-9, "middle anchor centers")

    # place_label: first clear candidate wins.
    p = place_label(
        "label", 12,
        candidates=[
            Anchor(200, 200, label="far"),
            Anchor(0, 0, label="origin"),
        ],
        obstacles=[(0, 0)],
        plot_bbox=BBox(0, 0, 400, 400),
    )
    check(p.zone == "in-plot" and p.source == "far", "first clear candidate wins")
    check(len(p.rejected) == 0, "no rejections when first candidate clear")

    # place_label: collision pushes to a later candidate.
    p2 = place_label(
        "label", 12,
        candidates=[
            Anchor(5, 5, label="hits"),
            Anchor(300, 300, label="clear"),
        ],
        obstacles=[(10, 8)],
        plot_bbox=BBox(0, 0, 400, 400),
    )
    check(p2.source == "clear", "collision skips to next candidate")
    check(len(p2.rejected) == 1, "one rejection logged")
    check("plotted point" in p2.rejected[0].reason, "rejection reason names cause")

    # place_label: all collide -> margin fallback, nearer side.
    wall = [(x, y) for x in range(0, 401, 4) for y in range(0, 401, 4)]
    p3 = place_label(
        "label", 12,
        candidates=[Anchor(30, 200, label="a"), Anchor(40, 210, label="b")],
        obstacles=wall,
        plot_bbox=BBox(0, 0, 400, 400),
    )
    check(p3.zone == "left-margin", "near-left candidate -> left margin")
    check(p3.x < 0, "left-margin label sits outside plot extent")
    check(p3.is_safe_by_construction, "margin zone flagged safe")
    check(len(p3.rejected) == 2, "all candidates logged as rejected")

    p4 = place_label(
        "label", 12,
        candidates=[Anchor(370, 200, label="a")],
        obstacles=wall,
        plot_bbox=BBox(0, 0, 400, 400),
    )
    check(p4.zone == "right-margin", "near-right candidate -> right margin")
    check(p4.x > 400, "right-margin label sits outside plot extent")

    # place_label: all collide, no plot_bbox -> LayoutError.
    raised = False
    try:
        place_label(
            "label", 12,
            candidates=[Anchor(5, 5, label="hits")],
            obstacles=[(6, 4)],
        )
    except LayoutError:
        raised = True
    check(raised, "all-collision with no plot_bbox raises LayoutError")

    # place_in_caption is always safe.
    pc = place_in_caption("v̄ = mean approach velocity", 12, BBox(0, 0, 400, 300))
    check(pc.zone == "caption" and pc.is_caption, "explicit caption placement")
    check(pc.y > 300, "caption sits below the plot")

    # svg_text round-trips font-size and never emits a stroke.
    svg = p.svg_text("label", fill="#e6e4d2", font_family="Inter")
    check("font-size=\"12\"" in svg, "svg_text carries font-size")
    check("stroke" not in svg, "svg_text never emits a stroke/halo")
    check("font-family=\"Inter\"" in svg, "svg_text passes through attrs")

    print(f"ok — {n} checks passed")
    return 0


# ─── Demo ───────────────────────────────────────────────────────────

def _demo_svg() -> str:
    """A worked SVG: a d(t) curve, three candidate anchors (two of which
    collide), and the placement place_label() actually chose. Doubles as
    the visible bbox-vs-geometry check the interim rule asked for."""
    import math

    W, H = 520, 340
    pb = BBox(60, 30, 470, 280)

    # A d(t) approach-retreat curve: dips to a minimum, recovers.
    raw = []
    for i in range(81):
        t = i / 80.0
        x = pb.x0 + t * pb.width
        d = 0.5 - 0.42 * math.exp(-((t - 0.42) ** 2) / 0.03)
        y = pb.y0 + d * pb.height * 1.6
        raw.append((x, y))
    curve = sample_polyline(raw, n=240)

    # Three candidates: on the curve (collides), just under the dip
    # (collides), and up in clear air (clears).
    cands = [
        Anchor(curve[34][0], curve[34][1], "middle", "alphabetic", label="on-curve"),
        Anchor(pb.x0 + 0.42 * pb.width, pb.y0 + 0.62 * pb.height,
               "middle", "hanging", label="under-dip"),
        Anchor(pb.x0 + 0.70 * pb.width, pb.y0 + 0.22 * pb.height,
               "start", "alphabetic", label="clear-air"),
    ]
    placed = place_label(
        "v̄ = mean approach velocity", 13,
        candidates=cands, obstacles=curve, plot_bbox=pb, padding=3.0,
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="#0a0a0f"/>',
        # plot frame
        f'<rect x="{pb.x0}" y="{pb.y0}" width="{pb.width}" height="{pb.height}" '
        f'fill="none" stroke="#3a3a48" stroke-width="1"/>',
    ]
    # curve
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in curve)
    parts.append(
        f'<polyline points="{pts}" fill="none" stroke="#7dd4e4" '
        f'stroke-width="2"/>'
    )
    # rejected candidate bboxes in dim red
    for r in placed.rejected:
        bb = r.bbox
        parts.append(
            f'<rect x="{bb.x0:.1f}" y="{bb.y0:.1f}" width="{bb.width:.1f}" '
            f'height="{bb.height:.1f}" fill="none" stroke="#c84a4a" '
            f'stroke-width="1" stroke-dasharray="3 2"/>'
        )
    # chosen bbox in green + the label itself
    cb = placed.bbox
    parts.append(
        f'<rect x="{cb.x0:.1f}" y="{cb.y0:.1f}" width="{cb.width:.1f}" '
        f'height="{cb.height:.1f}" fill="none" stroke="#5fb85f" '
        f'stroke-width="1"/>'
    )
    parts.append(
        placed.svg_text(
            "v̄ = mean approach velocity",
            fill="#e6e4d2", font_family="Inter, system-ui, sans-serif",
        )
    )
    # legend
    parts.append(
        f'<text x="60" y="312" font-size="11" fill="#b0b0c4" '
        f'font-family="Inter, system-ui, sans-serif">'
        f'chosen zone: {placed.zone} ({placed.source}) — '
        f'{len(placed.rejected)} candidate(s) rejected</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def _main(argv: Sequence[str]) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m muriel.layout",
        description="bbox-aware annotation placement for SVG figures",
    )
    ap.add_argument("--demo", action="store_true", help="render a worked SVG")
    ap.add_argument("--selftest", action="store_true", help="run assertions")
    ap.add_argument("-o", "--out", metavar="FILE", help="write demo SVG here")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()
    if args.demo:
        svg = _demo_svg()
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(svg)
            print(f"wrote {args.out}")
        else:
            print(svg)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
