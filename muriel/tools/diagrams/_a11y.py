"""muriel.tools.diagrams._a11y — the accessible-SVG contract for generated figures.

Every standalone figure muriel writes is an image a screen reader has to
name. SVG gives it two slots for that, ``<title>`` (the short accessible
name) and ``<desc>`` (the longer description), and ARIA gives the root a
way to point at them. The contract, written once here and used by every
generator:

- the root carries ``role="img"`` and ``aria-labelledby="{slug}-title
  {slug}-desc"``;
- ``<title id="{slug}-title">`` is the **first child element** — before
  ``<defs>`` and the background rect — because some assistive tech only
  reads a title in that position;
- ``<desc id="{slug}-desc">`` follows it;
- ids are prefixed with a per-figure slug. A bare ``id="title"`` collides
  the moment two figures are inlined into one HTML page, and the second
  figure silently announces the first one's name.

:func:`svg_open` writes that header. :func:`lint_a11y` reads a rendered
SVG back and reports every way it breaks the contract; it is the gate the
tests and ``muriel diagram-check`` run, so a generator that forgets the
header fails instead of shipping a figure that reads as "image".

The rule set is adapted from the MIT-licensed diagram-design skill
(© 2025 Cathryn Lavery), ``scripts/lint-skin.py::lint_accessible_svgs``.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Sequence, Union
from xml.sax.saxutils import escape as _xml_escape_text

__all__ = [
    "TITLE_MAX",
    "slugify",
    "figure_slug",
    "fit_title",
    "svg_open",
    "default_desc",
    "inject_a11y",
    "legible_on",
    "lint_a11y",
]

TITLE_MAX = 60  # an accessible name is announced whole; keep it a name


def _esc(text: str) -> str:
    """Escape text for XML element content *and* double-quoted attributes."""
    return _xml_escape_text(str(text), {'"': "&quot;"})


def slugify(text: str, fallback: str = "figure") -> str:
    """Lowercase ASCII slug usable as an XML id prefix.

    XML ids may not start with a digit, so a slug that would is prefixed
    with ``fig-``.
    """
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    if not s:
        s = fallback
    if not s[0].isalpha():
        s = f"fig-{s}"
    return s


def figure_slug(out_path: Optional[Union[str, Path]], kind: str) -> str:
    """Slug from the output file's stem, else from the diagram kind."""
    if out_path is not None:
        stem = Path(out_path).stem
        if stem:
            return slugify(stem, fallback=slugify(kind))
    return slugify(kind)


def fit_title(title: str, desc: str) -> tuple[str, str]:
    """Hold the accessible name to :data:`TITLE_MAX` characters.

    A longer title is cut at a word boundary with an ellipsis, and the
    full text moves to the front of the description so nothing is lost.
    """
    title = " ".join(str(title).split())
    if len(title) <= TITLE_MAX:
        return title, desc
    cut = title[: TITLE_MAX - 1]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    short = cut.rstrip(" ,;:—-") + "…"
    full = title if title.endswith((".", "!", "?")) else title + "."
    return short, (full + " " + desc).strip()


def svg_open(
    *,
    width: float,
    height: float,
    slug: str,
    title: str,
    desc: str,
    attrs: str = "",
) -> str:
    """Root ``<svg>`` tag plus its ``<title>``/``<desc>`` children.

    ``attrs`` is appended verbatim to the root tag (``font-family`` and the
    like). Returns a single string; emit ``</svg>`` yourself at the end.
    """
    title, desc = fit_title(title, desc)
    desc = " ".join(str(desc).split()) or title
    tid, did = f"{slug}-title", f"{slug}-desc"
    extra = f" {attrs.strip()}" if attrs.strip() else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-labelledby="{tid} {did}" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}"{extra}>\n'
        f'<title id="{tid}">{_esc(title)}</title>\n'
        f'<desc id="{did}">{_esc(desc)}</desc>'
    )


def default_desc(kind: str, title: Optional[str], parts: Sequence[str]) -> str:
    """Conservative description built only from what the spec says.

    ``kind`` is a noun phrase ("Funnel with 4 tiers"), ``parts`` are
    already-formatted clauses ("top to bottom: Visitors, Signups").
    Nothing is inferred: the default names the figure and lists its
    labels. The argument the figure makes belongs in ``desc=``.
    """
    head = kind
    if title:
        head = f"{kind} titled “{' '.join(title.split())}”"
    body = "; ".join(p for p in parts if p)
    if body:
        body = body[0].upper() + body[1:]
    return f"{head}. {body}." if body else f"{head}."


def legible_on(
    candidates: Sequence[str],
    surface: str,
    page_bg: str,
    required: float = 8.0,
) -> str:
    """First colour in ``candidates`` that clears ``required`` on ``surface``.

    ``surface`` may be translucent (``rgba(...)``); it is composited over
    ``page_bg`` first, which is what the reader actually sees behind the
    text. Generators pass their preferred token first (``muted``) and a
    stronger one after (``ink``), so a brand whose muted tone clears 8:1
    on the page but not on a tinted focal band gets ink there instead of
    shipping sub-floor text. If none clears, the highest-contrast
    candidate is returned and the contrast audit reports it.
    """
    from muriel.contrast import (
        _color_alpha, _composite, contrast_ratio, parse_color,
    )
    base = parse_color(page_bg) or (0, 0, 0)
    srf = parse_color(surface)
    behind = _composite(srf, _color_alpha(surface), base) if srf else base
    best, best_ratio = candidates[0], -1.0
    for c in candidates:
        ratio = contrast_ratio(parse_color(c), behind)
        if ratio >= required:
            return c
        if ratio > best_ratio:
            best, best_ratio = c, ratio
    return best


_ROOT_RE = re.compile(r"<svg\b[^>]*>", re.DOTALL)
_STRIP_RE = re.compile(r'\s(?:role|aria-labelledby)\s*=\s*("[^"]*"|\'[^\']*\')')


def _prefix_foreign_ids(svg_text: str, slug: str) -> str:
    """Prefix every id another renderer wrote (matplotlib's ``figure_1``,
    ``patch_2``, clip paths) and every reference to it, so two inlined
    figures never resolve each other's ``url(#…)`` targets."""
    prefix = f"{slug}-"
    ids = {i for i in re.findall(r'\bid="([^"]+)"', svg_text)
           if not i.startswith(prefix)}
    if not ids:
        return svg_text

    def ren(i: str) -> str:
        return prefix + i if i in ids else i

    svg_text = re.sub(r'\bid="([^"]+)"',
                      lambda m: f'id="{ren(m.group(1))}"', svg_text)
    svg_text = re.sub(r'url\(#([^)\s]+)\)',
                      lambda m: f"url(#{ren(m.group(1))})", svg_text)
    return re.sub(r'((?:xlink:)?href)="#([^"]+)"',
                  lambda m: f'{m.group(1)}="#{ren(m.group(2))}"', svg_text)


def inject_a11y(svg_text: str, *, slug: str, title: str, desc: str) -> str:
    """Retrofit the contract onto SVG another renderer wrote (matplotlib).

    Adds ``role``/``aria-labelledby`` to the root tag, replacing any
    existing values, and inserts ``<title>``/``<desc>`` as its first
    children — ahead of matplotlib's ``<metadata>`` and ``<defs>``.
    """
    svg_text = _prefix_foreign_ids(svg_text, slug)
    m = _ROOT_RE.search(svg_text)
    if m is None:
        raise ValueError("no <svg> root tag found")
    title, desc = fit_title(title, desc)
    desc = " ".join(str(desc).split()) or title
    tid, did = f"{slug}-title", f"{slug}-desc"
    tag = _STRIP_RE.sub("", m.group(0))
    close = "/>" if tag.endswith("/>") else ">"
    tag = tag[: -len(close)].rstrip()
    tag = f'{tag} role="img" aria-labelledby="{tid} {did}">'
    head = f'\n<title id="{tid}">{_esc(title)}</title>\n<desc id="{did}">{_esc(desc)}</desc>'
    tail = "</svg>" if close == "/>" else ""
    return svg_text[: m.start()] + tag + head + tail + svg_text[m.end():]


# ─── Lint ───────────────────────────────────────────────────────────

_SVG_NS = "http://www.w3.org/2000/svg"
_NUM_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def _local(tag) -> str:
    return tag.split("}", 1)[-1] if isinstance(tag, str) else ""


def lint_a11y(svg_text: str) -> list[str]:
    """Every way a rendered SVG misses the accessible-figure contract.

    Returns a list of human-readable findings; an empty list is a pass.
    An ``<svg aria-hidden="true">`` is decorative by declaration and is
    not checked.
    """
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        return [f"not well-formed XML: {exc}"]
    if _local(root.tag) != "svg":
        return [f"root element is <{_local(root.tag)}>, not <svg>"]
    if (root.get("aria-hidden") or "").strip().lower() == "true":
        return []

    findings: list[str] = []

    if (root.get("role") or "").strip().lower() != "img":
        findings.append('root <svg> must carry role="img"')

    vb = root.get("viewBox")
    if not vb:
        findings.append("root <svg> must have a viewBox")
    else:
        parts = re.split(r"[\s,]+", vb.strip())
        ok = False
        if len(parts) == 4 and all(_NUM_RE.match(p) for p in parts):
            nums = [float(p) for p in parts]
            ok = all(math.isfinite(n) for n in nums) and nums[2] > 0 and nums[3] > 0
        if not ok:
            findings.append(
                f'viewBox "{vb}" is not four finite numbers with positive '
                f"width and height"
            )

    children = [c for c in root if isinstance(c.tag, str)]
    titles = [c for c in children if _local(c.tag) == "title"]
    descs = [c for c in children if _local(c.tag) == "desc"]

    title_el = titles[0] if titles else None
    if title_el is None:
        findings.append("missing <title> child of the root <svg>")
    else:
        if children[0] is not title_el:
            findings.append(
                f"<title> must be the first child element; found "
                f"<{_local(children[0].tag)}> first"
            )
        text = " ".join("".join(title_el.itertext()).split())
        if not text:
            findings.append("<title> is empty")
        elif len(text) > TITLE_MAX:
            findings.append(
                f"<title> is {len(text)} characters (max {TITLE_MAX}); "
                f"move the detail into <desc>"
            )

    desc_el = descs[0] if descs else None
    if desc_el is None:
        findings.append("missing <desc> child of the root <svg>")
    elif not " ".join("".join(desc_el.itertext()).split()):
        findings.append("<desc> is empty")

    # ids: prefixed, unique
    seen: dict[str, int] = {}
    for el in root.iter():
        eid = el.get("id")
        if eid is None:
            continue
        seen[eid] = seen.get(eid, 0) + 1
    for eid, count in seen.items():
        if eid in ("title", "desc"):
            findings.append(
                f'bare id="{eid}" collides when figures are inlined together; '
                f'prefix it with a figure slug'
            )
        if count > 1:
            findings.append(f'duplicate id="{eid}" ({count} elements)')
    # Every id shares the title's slug, so a marker or filter from one inlined
    # figure can never resolve into another's (the second url(#arrow) wins).
    title_id = title_el.get("id") if title_el is not None else None
    if title_id and title_id.endswith("-title"):
        prefix = title_id[: -len("title")]
        for eid in seen:
            if eid not in ("title", "desc") and not eid.startswith(prefix):
                findings.append(
                    f'id="{eid}" lacks the figure slug "{prefix}"; two inlined '
                    f'figures would share it'
                )
    for label, el in (("title", title_el), ("desc", desc_el)):
        if el is not None and not el.get("id"):
            findings.append(f"<{label}> has no id for aria-labelledby to name")

    refs = (root.get("aria-labelledby") or "").split()
    if not refs:
        findings.append("aria-labelledby must name the <title> id then the <desc> id")
    else:
        dangling = [r for r in refs if r not in seen]
        if dangling:
            findings.append(
                "aria-labelledby references missing id(s): " + ", ".join(dangling)
            )
        want = [
            el.get("id") for el in (title_el, desc_el)
            if el is not None and el.get("id")
        ]
        if len(want) == 2 and refs[:2] != want:
            findings.append(
                f'aria-labelledby is "{" ".join(refs)}"; expected '
                f'"{want[0]} {want[1]}" (title first, then desc)'
            )
    return findings
