"""muriel.tools.diagrams._labels — measured text fitting for the SVG generators.

Why this exists
---------------
The diagram generators lay out on a fixed 4px grid and emit ``<text>`` at
coordinates derived from that grid: a step label centred in a 144px box, a
lane name right-anchored in a 168px gutter, a layer name and its note at
opposite ends of one 680px band. None of it measured the text. A label
wider than its container ran past the edge — off the canvas for the gutter
case, into the neighbouring column for the step case, straight through the
note for the band case. ``cycle`` wrapped at a hardcoded 14 characters,
which is a proxy for width, not width: "Illuminate" (10) and "WWWWWWWWWW"
(10) are the same length and nowhere near the same size.

``muriel.layout`` already owns the arithmetic — :func:`~muriel.layout.text_bbox`
estimates a rendered box, and ``place_label`` resolves collisions by moving
the label. The generators need the measurement but not that policy: their
geometry *is* the design, so a label centred in its box has nowhere else to
go. What they need is to wrap on measured width and then **grow the
container**.

That is this module's whole contract, and it is ``layout.py``'s ethos
restated for a grid:

- Never shrink the text. Never clip it. Never halo it.
- Wrap on measured width, breaking only between words.
- If it still doesn't fit, the container grows — uniformly, so the grid
  stays regular.
- Growth is strictly conditional. A diagram whose labels already fit
  renders exactly as it did before this module existed.

:func:`verify_svg_labels` closes the loop: it reads a rendered SVG back,
reconstructs every text bbox, and reports overlaps. The generators do not
call it — it is the gate the test suite runs, so a geometry regression
fails CI instead of shipping.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence, Union

from muriel.layout import BBox, text_bbox

__all__ = [
    "RATIO_SANS",
    "RATIO_SANS_BOLD",
    "RATIO_MONO",
    "RATIO_UPPER",
    "Fit",
    "Collision",
    "LabelReport",
    "text_width",
    "wrap_measured",
    "fit_text",
    "label_bbox",
    "grow_to_fit",
    "connector_label_crossings",
    "verify_svg_labels",
]


# ─── Advance-width ratios ───────────────────────────────────────────
#
# Per-character advance as a fraction of font-size. These are averages
# over a mixed-case Latin run; over-estimating is the safe direction,
# because it grows a container that might not have needed it rather than
# clipping text that did. Same conservatism as layout.text_bbox.

RATIO_SANS = 0.60       # body sans, regular/medium
RATIO_SANS_BOLD = 0.62  # weight 600+ runs slightly wider
RATIO_MONO = 0.60       # ui-monospace advance is ~0.6em
RATIO_UPPER = 0.66      # an all-caps run has no narrow x-height glyphs


@dataclass(frozen=True)
class Fit:
    """The result of fitting text into a fixed width.

    ``lines`` is the text as it should be rendered, one entry per rendered
    ``<text>`` row. ``width`` is the measured width of the widest line.
    ``needs_growth`` is true when ``width`` still exceeds the container
    that was asked for, and ``reason`` says which kind of growth resolves
    it:

    ``"unbreakable-word"``
        A single word is wider than the container. No amount of wrapping
        helps; the container has to get wider.
    ``"line-count"``
        The text wrapped, but into more lines than the caller allowed.
        The container has to get taller.
    ``""``
        It fits.
    """

    lines: tuple[str, ...]
    width: float
    max_width: float
    needs_growth: bool
    reason: str = ""

    @property
    def overflow(self) -> float:
        """How much wider than the container the widest line is (>= 0)."""
        return max(0.0, self.width - self.max_width)


@dataclass(frozen=True)
class Collision:
    """Two rendered labels whose boxes overlap."""

    a_text: str
    b_text: str
    a_bbox: BBox
    b_bbox: BBox

    def __str__(self) -> str:  # pragma: no cover - diagnostic sugar
        return (
            f"{self.a_text!r} @ ({self.a_bbox.x0:.1f},{self.a_bbox.y0:.1f}) "
            f"overlaps {self.b_text!r} @ "
            f"({self.b_bbox.x0:.1f},{self.b_bbox.y0:.1f})"
        )


@dataclass(frozen=True)
class LabelReport:
    """What a read-back check found. Falsy when the diagram is clean."""

    collisions: list = field(default_factory=list)
    """Pairs of labels whose boxes overlap — two labels, both illegible."""

    overruns: list = field(default_factory=list)
    """Labels whose box escapes the canvas — text rendered off the edge."""

    overhangs: list = field(default_factory=list)
    """Labels straddling a container's edge — text spilling out of its box."""

    @property
    def ok(self) -> bool:
        return not (self.collisions or self.overruns or self.overhangs)

    def __bool__(self) -> bool:
        return not self.ok

    def summary(self) -> str:
        """One-line count, for test failure messages."""
        return (
            f"{len(self.collisions)} collision(s), "
            f"{len(self.overruns)} overrun(s), "
            f"{len(self.overhangs)} overhang(s)"
        )


def text_width(
    text: str,
    font_size: float,
    *,
    char_width_ratio: float = RATIO_SANS,
    letter_spacing: float = 0.0,
) -> float:
    """Measured width of ``text`` in SVG user units.

    ``letter_spacing`` is the SVG attribute of the same name, in user
    units. It is counted once per character rather than once per gap —
    renderers disagree about the trailing gap, and the extra character's
    worth keeps the estimate on the conservative side.
    """
    if not text:
        return 0.0
    base = text_bbox(text, font_size, 0.0, 0.0, "start", "alphabetic",
                     char_width_ratio).width
    return base + len(text) * letter_spacing


def wrap_measured(
    text: str,
    font_size: float,
    max_width: float,
    *,
    char_width_ratio: float = RATIO_SANS,
    letter_spacing: float = 0.0,
) -> list[str]:
    """Greedy word-wrap on *measured* width.

    Breaks only at existing whitespace — a word wider than ``max_width``
    is returned on a line of its own rather than split mid-word, because
    hyphenating a label silently changes what it says. The caller sees
    that case as :attr:`Fit.reason` ``"unbreakable-word"`` and grows the
    container.
    """
    words = text.split()
    if not words:
        return []

    def w(s: str) -> float:
        return text_width(s, font_size,
                          char_width_ratio=char_width_ratio,
                          letter_spacing=letter_spacing)

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if w(candidate) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def fit_text(
    text: str,
    font_size: float,
    max_width: float,
    *,
    max_lines: int = 2,
    char_width_ratio: float = RATIO_SANS,
    letter_spacing: float = 0.0,
) -> Fit:
    """Wrap ``text`` into ``max_width``, reporting what growth it needs.

    Wraps greedily on measured width. If the result exceeds ``max_lines``,
    the lines are re-joined into exactly ``max_lines`` rows (so the caller
    can choose to grow height instead) and ``reason`` is ``"line-count"``.
    A single over-wide word reports ``"unbreakable-word"`` and is never
    split.
    """
    if max_lines < 1:
        raise ValueError(f"max_lines must be >= 1, got {max_lines}")

    def w(s: str) -> float:
        return text_width(s, font_size,
                          char_width_ratio=char_width_ratio,
                          letter_spacing=letter_spacing)

    lines = wrap_measured(text, font_size, max_width,
                          char_width_ratio=char_width_ratio,
                          letter_spacing=letter_spacing)
    if not lines:
        return Fit((), 0.0, max_width, False, "")

    widest = max(w(ln) for ln in lines)

    # An over-wide single word survives wrapping intact; that is the one
    # case wrapping cannot fix, so it outranks a line-count overflow.
    if widest > max_width:
        return Fit(tuple(lines), widest, max_width, True, "unbreakable-word")

    if len(lines) > max_lines:
        return Fit(tuple(lines), widest, max_width, True, "line-count")

    return Fit(tuple(lines), widest, max_width, False, "")


def label_bbox(
    text: str,
    font_size: float,
    x: float,
    y: float,
    *,
    text_anchor: str = "start",
    baseline: str = "alphabetic",
    char_width_ratio: float = RATIO_SANS,
    letter_spacing: float = 0.0,
) -> BBox:
    """Bounding box of a label as the generators emit it.

    Thin wrapper over :func:`muriel.layout.text_bbox` that also accounts
    for ``letter-spacing``, which the base helper does not model. The
    extra width is added on the side the anchor grows toward, so a
    right-anchored label still ends at ``x``.
    """
    box = text_bbox(text, font_size, x, y, text_anchor, baseline,
                    char_width_ratio)
    if not letter_spacing or not text:
        return box
    extra = len(text) * letter_spacing
    if text_anchor == "start":
        return BBox(box.x0, box.y0, box.x1 + extra, box.y1)
    if text_anchor == "end":
        return BBox(box.x0 - extra, box.y0, box.x1, box.y1)
    return BBox(box.x0 - extra / 2, box.y0, box.x1 + extra / 2, box.y1)


# ─── SVG read-back verifier ─────────────────────────────────────────

_SVG_NS = "http://www.w3.org/2000/svg"
_MONO_HINT = re.compile(r"mono|consolas|menlo|courier", re.I)


@dataclass
class _ParsedLabel:
    text: str
    bbox: BBox
    rotated: bool = False
    outside: bool = False
    _raw: dict = field(default_factory=dict)


def _float_attr(el: ET.Element, name: str, default: float = 0.0) -> float:
    raw = el.get(name)
    if raw is None:
        return default
    try:
        return float(raw.strip().rstrip("px"))
    except ValueError:
        return default


def _parse_labels(root: ET.Element, canvas: Optional[BBox]) -> list[_ParsedLabel]:
    out: list[_ParsedLabel] = []
    for el in root.iter(f"{{{_SVG_NS}}}text"):
        text = "".join(el.itertext()).strip()
        if not text:
            continue
        font_size = _float_attr(el, "font-size", 12.0)
        x = _float_attr(el, "x")
        y = _float_attr(el, "y")
        anchor = el.get("text-anchor", "start")
        baseline = el.get("dominant-baseline", "alphabetic")
        if baseline not in ("alphabetic", "auto", "baseline", "middle",
                            "central", "hanging", "text-before-edge"):
            baseline = "alphabetic"
        family = el.get("font-family", "")
        ratio = RATIO_MONO if _MONO_HINT.search(family) else RATIO_SANS
        spacing = _float_attr(el, "letter-spacing")

        box = label_bbox(text, font_size, x, y, text_anchor=anchor,
                         baseline=baseline, char_width_ratio=ratio,
                         letter_spacing=spacing)
        outside = False
        if canvas is not None:
            outside = (box.x0 < canvas.x0 or box.x1 > canvas.x1
                       or box.y0 < canvas.y0 or box.y1 > canvas.y1)
        out.append(_ParsedLabel(text, box, rotated=bool(el.get("transform")),
                                outside=outside))
    return out


def _containers(root: ET.Element) -> list[list[tuple[float, float]]]:
    """Every shape a label could sit in, as a corner list.

    Rects become their four corners; polygons keep their own vertices, so
    a tapered pyramid tier is tested against its actual sloped edges
    rather than a bounding box that would forgive a label poking out of
    the narrow end.
    """
    out: list[list[tuple[float, float]]] = []
    for el in root.iter(f"{{{_SVG_NS}}}rect"):
        x, y = _float_attr(el, "x"), _float_attr(el, "y")
        w, h = _float_attr(el, "width"), _float_attr(el, "height")
        if w > 0 and h > 0:
            out.append([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
    for el in root.iter(f"{{{_SVG_NS}}}polygon"):
        raw = (el.get("points") or "").replace(",", " ").split()
        try:
            nums = [float(v) for v in raw]
        except ValueError:
            continue
        if len(nums) >= 6 and len(nums) % 2 == 0:
            out.append(list(zip(nums[0::2], nums[1::2])))
    return out


def _inside(x: float, y: float, poly: Sequence[tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon. Boundary counts as inside."""
    hit = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            t = (y - y0) / (y1 - y0)
            if x < x0 + t * (x1 - x0):
                hit = not hit
    return hit


def _straddles(text: BBox, poly: Sequence[tuple[float, float]]) -> bool:
    """True if ``text`` spills out of a shape it is sitting in.

    Corner containment alone is not enough. A label only slightly too
    wide has two corners in and two out, but a label *much* too wide
    clears the shape on both sides and has no corner inside at all — the
    worst case would read as clean. So the test is:

    - the label is at this shape's height (its vertical midpoint falls
      inside the shape's vertical extent), and
    - the two boxes overlap horizontally, and
    - the label is not fully contained.

    The height condition is what keeps a title above a box, or a lane
    eyebrow beside one, from being read as spilling out of it.
    """
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    shape = BBox(min(xs), min(ys), max(xs), max(ys))

    mid_y = (text.y0 + text.y1) / 2
    if not (shape.y0 <= mid_y <= shape.y1):
        return False
    if text.x1 <= shape.x0 or text.x0 >= shape.x1:
        return False

    corners = [
        (text.x0, text.y0), (text.x1, text.y0),
        (text.x1, text.y1), (text.x0, text.y1),
    ]
    return not all(_inside(cx, cy, poly) for cx, cy in corners)


def verify_svg_labels(
    svg: Union[str, Path],
    *,
    padding: float = 0.0,
    ignore: Sequence[str] = (),
) -> "LabelReport":
    """Read a rendered SVG back and report every way a label misses.

    Reconstructs each ``<text>`` element's bounding box from its own
    attributes — position, anchor, baseline, size, family, letter-spacing
    — and tests every pair. This is a *read-back* check on purpose: it
    verifies what the file actually says rather than trusting the
    generator's own arithmetic, so a growth rule that computes the right
    number but writes the wrong coordinate still fails.

    Rotated labels (the ``transform``-bearing axis captions) are measured
    for the canvas check but excluded from pairwise collision, because
    their axis-aligned box is not where the glyphs land.

    Parameters
    ----------
    svg
        SVG markup, or a path to a ``.svg`` file.
    padding
        Extra margin applied to every box before testing. Use a small
        positive value to require visible separation rather than mere
        non-overlap.
    ignore
        Substrings; a label containing any of them is skipped entirely.

    Returns
    -------
    LabelReport
        Three independent failure modes — see :class:`LabelReport`. They
        are worth separating because they fail differently: an overrun is
        invisible text, an overhang is visible text in the wrong place,
        and a collision is two labels illegible at once.
    """
    markup = svg
    if isinstance(svg, Path) or (
        isinstance(svg, str) and not svg.lstrip().startswith("<")
    ):
        markup = Path(svg).read_text(encoding="utf-8")

    root = ET.fromstring(markup)
    canvas: Optional[BBox] = None
    view = root.get("viewBox")
    if view:
        try:
            vx, vy, vw, vh = (float(v) for v in view.replace(",", " ").split())
            canvas = BBox(vx, vy, vx + vw, vy + vh)
        except ValueError:
            canvas = None

    labels = [
        lab for lab in _parse_labels(root, canvas)
        if not any(tok in lab.text for tok in ignore)
    ]

    overruns = [lab.text for lab in labels if lab.outside]

    collisions: list[Collision] = []
    testable = [lab for lab in labels if not lab.rotated]
    for i, a in enumerate(testable):
        for b in testable[i + 1:]:
            if a.bbox.expand(padding).intersects(b.bbox.expand(padding)):
                collisions.append(Collision(a.text, b.text, a.bbox, b.bbox))

    containers = _containers(root)
    overhangs = [
        lab.text for lab in testable
        if any(_straddles(lab.bbox, shape) for shape in containers)
    ]
    return LabelReport(collisions, overruns, overhangs)


def grow_to_fit(
    current: float,
    required: float,
    *,
    grid: float = 4.0,
) -> float:
    """Round ``required`` up onto the ``grid``, never below ``current``.

    The generators align everything to a 4px grid; growth that ignored it
    would leave the rest of the layout half a pixel off. Returns
    ``current`` unchanged when it is already big enough, which is what
    keeps existing diagrams byte-identical.
    """
    if required <= current:
        return current
    return float(grid * -(-required // grid))  # ceil-div onto the grid


# ─── Connector-label clearance ──────────────────────────────────────
#
# muriel's rule: a connector label sits in clear space beside its line,
# never on it with a halo or mask rect behind it. This reads a rendered
# SVG back and reports every text box a connector segment passes through.

_SKIP_SUBTREES = ("defs", "marker", "clipPath", "mask", "pattern", "symbol")
_PATH_CMD_RE = re.compile(
    r"[MmLlHhVvCcSsQqTtAaZz]|[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_ARITY = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2,
          "A": 7, "Z": 0}


def _path_polyline(d: str) -> list[list[tuple[float, float]]]:
    """Subpaths of ``d`` as point lists (curves by their control polygon).

    A Bézier lies inside its control polygon's hull, so walking the control
    points over-reports a crossing rather than missing one.
    """
    toks = _PATH_CMD_RE.findall(d or "")
    subs: list[list[tuple[float, float]]] = []
    cur: list[tuple[float, float]] = []
    x = y = sx = sy = 0.0
    cmd = None
    i = 0
    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if cur:
                    cur.append((sx, sy))
                x, y = sx, sy
                continue
        if cmd is None:
            break
        up, rel = cmd.upper(), cmd.islower()
        n = _ARITY[up]
        try:
            a = [float(v) for v in toks[i:i + n]]
        except ValueError:
            break
        if len(a) < n:
            break
        i += n
        if up == "M":
            if len(cur) > 1:
                subs.append(cur)
            x, y = (x + a[0], y + a[1]) if rel else (a[0], a[1])
            sx, sy = x, y
            cur = [(x, y)]
            cmd = "l" if rel else "L"
            continue
        if up == "H":
            x = x + a[0] if rel else a[0]
        elif up == "V":
            y = y + a[0] if rel else a[0]
        else:
            if up in "CSQ":
                for k in range(0, n - 2, 2):
                    cur.append((x + a[k], y + a[k + 1]) if rel
                               else (a[k], a[k + 1]))
            x, y = (x + a[-2], y + a[-1]) if rel else (a[-2], a[-1])
        cur.append((x, y))
    if len(cur) > 1:
        subs.append(cur)
    return subs


def _segment_hits_box(p, q, box: BBox) -> bool:
    """Liang–Barsky: does segment p→q pass through the (open) box?"""
    (x0, y0), (x1, y1) = p, q
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for pk, qk in ((-dx, x0 - box.x0), (dx, box.x1 - x0),
                   (-dy, y0 - box.y0), (dy, box.y1 - y0)):
        if pk == 0:
            if qk <= 0:
                return False
            continue
        t = qk / pk
        if pk < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 >= t1:
            return False
    return True


def _is_connector(el: ET.Element, tag: str) -> bool:
    stroke = (el.get("stroke") or "").strip().lower()
    style = (el.get("style") or "").replace(" ", "").lower()
    if not stroke:
        m = re.search(r"stroke:([^;]+)", style)
        stroke = m.group(1) if m else ""
    if stroke in ("", "none", "transparent"):
        return False
    if tag in ("line", "polyline"):
        return True
    fill = (el.get("fill") or "").strip().lower()
    if not fill:
        m = re.search(r"fill:([^;]+)", style)
        fill = m.group(1) if m else ""
    return fill in ("none", "transparent")  # an open stroked path


def connector_label_crossings(
    svg: Union[str, Path], *, inset: float = 0.5,
) -> list[tuple[str, tuple[float, float, float, float]]]:
    """Every (label, segment) where a connector passes through a label box.

    A connector is a stroked ``<line>``, ``<polyline>``, or unfilled
    ``<path>`` outside ``<defs>``/``<marker>``. Label boxes come from the
    same read-back as :func:`verify_svg_labels`, shrunk by ``inset`` so a
    line that only grazes a box edge does not count. Rotated labels and
    anything under a transformed group are skipped: their boxes are not
    where the glyphs land.
    """
    if isinstance(svg, Path) or (isinstance(svg, str)
                                 and not svg.lstrip().startswith("<")):
        svg = Path(svg).read_text(encoding="utf-8")
    root = ET.fromstring(svg)
    labels = [lbl for lbl in _parse_labels(root, None) if not lbl.rotated]

    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []

    def walk(el: ET.Element, transformed: bool) -> None:
        tag = el.tag.split("}", 1)[-1] if isinstance(el.tag, str) else ""
        if tag in _SKIP_SUBTREES:
            return
        transformed = transformed or bool(el.get("transform"))
        if not transformed and tag in ("line", "polyline", "path") \
                and _is_connector(el, tag):
            if tag == "line":
                pts = [[(_float_attr(el, "x1"), _float_attr(el, "y1")),
                        (_float_attr(el, "x2"), _float_attr(el, "y2"))]]
            elif tag == "polyline":
                nums = [float(v) for v in
                        (el.get("points") or "").replace(",", " ").split()]
                pts = [list(zip(nums[0::2], nums[1::2]))]
            else:
                pts = _path_polyline(el.get("d") or "")
            for poly in pts:
                segments.extend(zip(poly, poly[1:]))
        for child in el:
            walk(child, transformed)

    walk(root, False)
    hits = []
    for lbl in labels:
        b = lbl.bbox
        box = BBox(b.x0 + inset, b.y0 + inset, b.x1 - inset, b.y1 - inset)
        if box.x1 <= box.x0 or box.y1 <= box.y0:
            continue
        for p, q in segments:
            if _segment_hits_box(p, q, box):
                hits.append((lbl.text, (p[0], p[1], q[0], q[1])))
    return hits
