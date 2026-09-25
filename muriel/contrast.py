"""
muriel.contrast — WCAG 2.1 contrast ratio helpers.

Standard-library-only module for computing WCAG 2.1 relative-luminance
contrast ratios between two sRGB colors, checking text/background pairs
against muriel's 8:1 rule (or any threshold), and auditing SVG or HTML
files by walking their ``<style>`` blocks (and, for HTML, inline
``style="…"`` attributes and CSS custom properties).

Created because the author shipped a set of SVGs claiming "8:1 on all
text" without actually running the numbers. Three text roles quietly
failed the rule and only got caught when a sharp collaborator asked
"is that really 8:1?" This module exists so that question has a
one-command answer.

For the broader contrast / WCAG / APCA ecosystem and a spec-authoritative
implementation, see ``color-js/color.js``
(https://github.com/color-js/color.js, MIT) — by the CSS Color Module
editors; ships WCAG 2.x and APCA (WCAG 3 draft) ratios in one API.
This module covers muriel's enforcement floor (WCAG 2.1 8:1 on text);
drop down to color.js when you need APCA, non-sRGB gamuts, or fancy
delta-E.

Usage
-----

Programmatic:

.. code-block:: python

    from muriel.contrast import (
        contrast_ratio, check_text_pair, audit_svg, audit_html, parse_color,
    )

    contrast_ratio("#e6e4d2", "#0a0a0f")         # → 15.42
    check_text_pair("#8a8aa0", "#0a0a0f")         # CheckResult(passes=False, …)
    audit_svg("examples/example-palette.svg")    # prints audit table
    audit_html("docs/article.html")              # prints audit + legibility table

CLI:

.. code-block:: bash

    python -m muriel.contrast path/to/file.svg
    python -m muriel.contrast path/to/file.html
    python -m muriel.contrast path/to/file.html --required 4.5
    python -m muriel.contrast path/to/file.html --background '#ffffff'

Exit status:
    0 = every text rule clears the threshold and no legibility warnings
    1 = one or more text rules fail the contrast threshold
    2 = contrast passes but legibility floor warnings were emitted
    3 = usage error (file not found, etc.)

Thresholds
----------

- ``RENDER_8`` = 8.0 — muriel's universal rule (primary default)
- ``WCAG_AAA`` = 7.0 — WCAG 2.1 AAA normal text
- ``WCAG_AA``  = 4.5 — WCAG 2.1 AA  normal text
- ``WCAG_AA_LARGE`` = 3.0 — WCAG 2.1 AA large text (≥18pt or ≥14pt bold)

Status tiers in the audit table
-------------------------------

- ``PASS`` — ratio ≥ required (the muriel-8 floor by default)
- ``WARN`` — ratio below required but at or above WCAG-AA (4.5)
- ``FAIL`` — ratio below WCAG-AA
- ``SKIP`` — selector classified as decorative; exempted from the text rule

Limitations
-----------

- sRGB only; no P3 / Rec.2020 / Oklab
- Text pairs only; does not evaluate non-text UI / graphical contrast
- Parses CSS inside ``<style>`` blocks via minimal regex + brace
  matching. ``@media`` / ``@keyframes`` / ``@supports`` blocks are
  skipped (their bodies don't enter the audit). Nested selectors and
  CSS-nesting syntax beyond one level are not interpreted.
- CSS rules: alpha channel ignored — opaque text on an opaque background
  is assumed. SVG presentation attributes (``<text fill="…">``) are
  alpha-composited: see below.

SVG presentation attributes
---------------------------

``audit_svg`` also reads ``fill`` off ``<text>`` / ``<tspan>`` elements
(and inherited from an ancestor ``<g fill>``, or an inline
``style="fill:…"``), because muriel's own diagram generators write colour
that way and a CSS-only audit reads such a file as having no text at all.
Each text run is scored against the background actually behind it: the
page background, with every earlier ``rect`` / ``polygon`` / ``circle`` /
``ellipse`` / straight-edged ``path`` that contains the run composited over it (``rgba()``,
``fill-opacity`` and ``opacity`` honoured), and the text colour's own
alpha composited over that. The run is sampled at its start, middle and
end and scored at the worst of the three. Shapes under a ``transform``
are skipped. Elements whose fill comes from a CSS class are left to the
CSS pass. Text over a filled *curved* path (arcs, Béziers — a wedge, a
circle drawn as a path) cannot be scored exactly; those runs are marked
``unverified`` on their entry rather than silently passed.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence, Union
import xml.etree.ElementTree as ET

__all__ = [
    "RENDER_8",
    "WCAG_AAA",
    "WCAG_AA",
    "WCAG_AA_LARGE",
    "parse_color",
    "hex_to_rgb",
    "relative_luminance",
    "contrast_ratio",
    "CheckResult",
    "check_text_pair",
    "SelectorEntry",
    "LegibilityWarning",
    "audit_svg",
    "audit_html",
]

# ─── Threshold constants ─────────────────────────────────────────────────

RENDER_8:       float = 8.0
WCAG_AAA:       float = 7.0
WCAG_AA:        float = 4.5
WCAG_AA_LARGE:  float = 3.0

ColorInput = Union[str, Sequence[int], tuple]


# ─── Color parsing ───────────────────────────────────────────────────────

# Minimal CSS named-color map. The full CSS4 spec has ~150 names; this
# covers the ones that actually appear in hand-written SVG palettes.
_CSS_NAMED_COLORS: dict[str, Optional[tuple[int, int, int]]] = {
    "black":        (0, 0, 0),
    "white":        (255, 255, 255),
    "red":          (255, 0, 0),
    "green":        (0, 128, 0),
    "blue":         (0, 0, 255),
    "gray":         (128, 128, 128),
    "grey":         (128, 128, 128),
    "lightgray":    (211, 211, 211),
    "darkgray":     (169, 169, 169),
    "silver":       (192, 192, 192),
    "yellow":       (255, 255, 0),
    "cyan":         (0, 255, 255),
    "magenta":      (255, 0, 255),
    "orange":       (255, 165, 0),
    "purple":       (128, 0, 128),
    "pink":         (255, 192, 203),
    "brown":        (165, 42, 42),
    "navy":         (0, 0, 128),
    "teal":         (0, 128, 128),
    "lime":         (0, 255, 0),
    "aqua":         (0, 255, 255),
    "fuchsia":      (255, 0, 255),
    "maroon":       (128, 0, 0),
    "olive":        (128, 128, 0),
    # sentinels for unresolvable values
    "transparent":  None,
    "none":         None,
    "currentcolor": None,
    "inherit":      None,
    "initial":      None,
    "unset":        None,
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """
    Parse ``#RRGGBB``, ``#RGB``, ``#RRGGBBAA``, or ``#RGBA`` to ``(R, G, B)``.
    Alpha channel is ignored (assumes opaque compositing).
    """
    s = value.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    elif len(s) == 4:
        s = "".join(c * 2 for c in s[:3])
    elif len(s) == 8:
        s = s[:6]
    if len(s) != 6 or not all(c in "0123456789abcdefABCDEF" for c in s):
        raise ValueError(f"invalid hex color: {value!r}")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


_RGB_FN_RE = re.compile(
    r"^rgba?\(\s*([\d.]+)%?\s*[,\s]\s*([\d.]+)%?\s*[,\s]\s*([\d.]+)%?"
    r"(?:\s*[,/]\s*[\d.]+%?)?\s*\)$",
    re.IGNORECASE,
)


def parse_color(value: ColorInput) -> Optional[tuple[int, int, int]]:
    """
    Parse a color value as hex (``#abc``, ``#abcdef``), ``rgb()``/``rgba()``,
    ``oklch(...)``, named color, or ``(R, G, B)`` tuple. Returns
    ``(R, G, B)`` in 0–255, or ``None`` if the value is transparent /
    ``currentColor`` / ``none``.

    OKLCH inputs are routed through ``muriel.oklch`` (lazy import).
    Out-of-gamut OKLCH colors are clamped via chroma reduction so the
    returned sRGB triple is faithful to the intended hue/lightness
    rather than hard-clipped.

    Raises ``ValueError`` on genuinely unparseable input.
    """
    if isinstance(value, (tuple, list)):
        if len(value) < 3:
            raise ValueError(f"RGB tuple must have ≥3 elements: {value!r}")
        return (int(value[0]), int(value[1]), int(value[2]))

    s = str(value).strip()
    if not s:
        return None
    if s.startswith("#"):
        return hex_to_rgb(s)
    if s[:6].lower() == "oklch(":
        from muriel.oklch import clamp_to_srgb, oklch_to_rgb, parse_oklch
        return oklch_to_rgb(clamp_to_srgb(parse_oklch(s)))
    m = _RGB_FN_RE.match(s)
    if m:
        return (
            int(float(m.group(1))),
            int(float(m.group(2))),
            int(float(m.group(3))),
        )
    key = s.lower()
    if key in _CSS_NAMED_COLORS:
        return _CSS_NAMED_COLORS[key]
    raise ValueError(f"unrecognized color: {value!r}")


# ─── Luminance + contrast ───────────────────────────────────────────────

def _srgb_to_linear(channel: int) -> float:
    """sRGB channel 0..255 → linear 0..1 per WCAG 2.1 §2.3."""
    c = channel / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """
    WCAG 2.1 relative luminance for an sRGB color in 0..255.

    https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
    """
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: ColorInput, bg: ColorInput) -> float:
    """
    WCAG 2.1 contrast ratio between two colors. Accepts hex strings,
    named colors, ``rgb()`` function syntax, or ``(R, G, B)`` tuples.
    Order doesn't matter — the brighter luminance is always numerator.

    Returns a float in [1.0, 21.0]. 21.0 is black-on-white.
    """
    fg_rgb = parse_color(fg) if not isinstance(fg, tuple) or len(fg) != 3 else fg
    bg_rgb = parse_color(bg) if not isinstance(bg, tuple) or len(bg) != 3 else bg
    if fg_rgb is None or bg_rgb is None:
        raise ValueError(
            "cannot compute contrast against transparent / unresolvable color"
        )
    l1 = relative_luminance(fg_rgb)
    l2 = relative_luminance(bg_rgb)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


# ─── Text-pair check ────────────────────────────────────────────────────

@dataclass
class CheckResult:
    """Outcome of a single foreground/background pair check."""
    fg: tuple[int, int, int]
    bg: tuple[int, int, int]
    ratio: float
    required: float
    passes: bool
    wcag_tier: str  # 'render-8' | 'AAA' | 'AA' | 'AA-large' | 'fail'

    def __str__(self) -> str:
        status = "PASS" if self.passes else "FAIL"
        return (
            f"{status}: {self.ratio:.2f}:1 "
            f"(required {self.required:.1f}:1, WCAG {self.wcag_tier})"
        )


def _wcag_tier(ratio: float) -> str:
    """Classify a ratio against the four common thresholds."""
    if ratio >= RENDER_8:
        return "render-8"
    if ratio >= WCAG_AAA:
        return "AAA"
    if ratio >= WCAG_AA:
        return "AA"
    if ratio >= WCAG_AA_LARGE:
        return "AA-large"
    return "fail"


def check_text_pair(
    fg: ColorInput, bg: ColorInput, required: float = RENDER_8,
) -> CheckResult:
    """
    Check a foreground/background text pair against a contrast threshold.
    Default threshold is muriel's 8:1 rule.
    """
    fg_rgb = parse_color(fg) if isinstance(fg, str) else tuple(fg)  # type: ignore[arg-type]
    bg_rgb = parse_color(bg) if isinstance(bg, str) else tuple(bg)  # type: ignore[arg-type]
    if fg_rgb is None or bg_rgb is None:
        raise ValueError("cannot check transparent / unresolvable color")
    ratio = contrast_ratio(fg_rgb, bg_rgb)
    return CheckResult(
        fg=fg_rgb,
        bg=bg_rgb,
        ratio=ratio,
        required=required,
        passes=(ratio >= required),
        wcag_tier=_wcag_tier(ratio),
    )


# ─── Selector role classification ───────────────────────────────────────

# Substrings that strongly suggest decorative (non-text) CSS selectors.
# Class names containing these are flagged SKIP in the audit table
# instead of failing the text rule. Case-insensitive substring match.
_DECORATIVE_HINTS = (
    "bg", "background",
    "rule", "divider", "border", "frame", "separator",
    "axis", "grid", "tick",
    "shadow", "glow", "aura", "vignette",
    "path", "shape", "line",
    "icon", "arrow", "marker", "pointer",
)

# Logotype selectors are exempt from the text rule per WCAG 1.4.3 — a
# wordmark/logo glyph is a recognizable brand SHAPE, not running text the
# reader parses for meaning. Checked BEFORE text hints so it wins over the
# generic "mark" text hint (which "wordmark"/"lettermark"/"brandmark" contain).
# Keep tokens specific enough not to false-positive on body copy.
_LOGOTYPE_HINTS = (
    "logo", "logotype", "wordmark", "lettermark", "brandmark", "monogram",
)

# Substrings that strongly suggest text roles. Text wins over decorative
# when both match — be conservative and check if uncertain.
_TEXT_HINTS = (
    "text", "title", "subtitle", "heading", "head", "caption", "label",
    "body", "prose", "para", "paragraph",
    "kicker", "tagline", "byline", "footer", "header",
    "model", "response", "prompt", "closer", "lede", "lead",
    "col-head", "col_head", "colhead",
    "callout", "quote", "pull", "note", "aside", "margin",
    "badge", "fn", "footnote", "mark", "highlight",
    "code", "mono", "stat",
    "dropcap",
    # muriel / marginalia project classes that are known text roles
    "out-m", "out-r", "apple-m", "apple-r",
)

# HTML element names that always render text. If a selector's leaf token
# is one of these, classify as text without consulting hint substrings.
_TEXT_TAGS = frozenset({
    "p", "span", "a", "li", "ul", "ol", "dl", "dt", "dd",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "q", "em", "strong", "i", "b", "u", "s",
    "small", "sub", "sup", "mark", "cite", "var", "samp",
    "code", "pre", "kbd", "abbr", "time", "ins", "del",
    "td", "th", "caption", "label", "legend", "figcaption",
    "summary", "details", "dfn",
    "body", "article", "section", "main", "aside", "header", "footer",
    "nav", "div", "fieldset",
})


def _selector_role(selector: str) -> str:
    """
    Classify a CSS selector as ``'text'``, ``'decorative'``, or
    ``'ambiguous'``. Text-tag leaves and text hints beat decorative
    hints. Ambiguous entries are checked (conservative default) but
    labeled so the user knows.
    """
    raw = selector.strip()
    key = raw.lstrip(".#").lower()
    # Strip pseudo-classes/elements and attribute selectors so the leaf
    # token comparison works for things like "footer a" or "h2:nth-of-type(2)".
    # Take the last simple selector after combinators.
    last = re.split(r"\s+|[>+~]", raw.strip())[-1] if raw else ""
    last = re.sub(r"::?[A-Za-z-]+(\([^)]*\))?", "", last)
    last = re.sub(r"\[[^\]]*\]", "", last)
    last = last.strip().lstrip(".#")
    # Logotype exemption (WCAG 1.4.3) wins over everything, including the
    # generic "mark" text hint that wordmark/lettermark/brandmark contain.
    if any(hint in key for hint in _LOGOTYPE_HINTS):
        return "decorative"
    leaf_tag = re.match(r"[A-Za-z][A-Za-z0-9-]*", last)
    if leaf_tag and leaf_tag.group(0).lower() in _TEXT_TAGS:
        return "text"
    if any(hint in key for hint in _TEXT_HINTS):
        return "text"
    if any(hint in key for hint in _DECORATIVE_HINTS):
        return "decorative"
    return "ambiguous"


# ─── Data classes for entries + warnings ────────────────────────────────

@dataclass
class SelectorEntry:
    """One CSS (or inline-style) rule with a resolvable foreground color."""
    selectors: list[str]
    fill: Optional[str]
    fill_rgb: Optional[tuple[int, int, int]]
    role: str  # 'text' | 'decorative' | 'ambiguous'
    # Populated by the audit functions after the background is resolved.
    ratio: Optional[float] = None
    passes: Optional[bool] = None   # True/False vs required; None means exempt
    status: Optional[str] = None    # 'PASS' | 'WARN' | 'FAIL' | 'SKIP'
    source: str = "css"             # 'css' | 'inline' | 'svg-attr'
    count: int = 1                  # for deduped inline entries
    # Set for 'svg-attr' entries: the background actually behind that text
    # (page bg with every enclosing shape composited over it). None means
    # "score against the audit-wide background".
    bg_rgb: Optional[tuple[int, int, int]] = None
    # Set for 'svg-attr' entries whose text sits on a curved filled <path>
    # (a wedge, a circle drawn as a path): the colour under it is not
    # known, so the ratio shown is against what *is* known and may be
    # optimistic. muriel diagram-check fails such runs as unverified.
    unverified: bool = False

    @property
    def fill_hex(self) -> Optional[str]:
        if self.fill_rgb is None:
            return None
        r, g, b = self.fill_rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    @property
    def selector_display(self) -> str:
        return ", ".join(self.selectors)


@dataclass
class LegibilityWarning:
    """One legibility-floor concern that did not necessarily fail contrast."""
    selectors: list[str]
    issue: str          # short tag: 'sub-floor' | 'opacity-on-text' | 'caption-below-16'
    detail: str         # human-readable explanation


# ─── CSS tokenizing helpers ─────────────────────────────────────────────

def _strip_css_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def _strip_at_rule_blocks(css: str) -> str:
    """
    Remove ``@media``, ``@keyframes``, ``@supports`` (etc.) blocks along
    with their bodies. Single-line at-rules without a brace block (e.g.
    ``@import``, ``@charset``) are stripped up to the terminating ``;``.

    This is a brace-matching pass so the remaining text only contains
    top-level rules ``selector { decl; … }``. The existing regex parser
    can then walk those without picking up rules nested inside ``@media``
    (the spec says to skip them for now).
    """
    out: list[str] = []
    i = 0
    n = len(css)
    while i < n:
        ch = css[i]
        if ch == "@":
            j = i
            while j < n and css[j] not in "{;":
                j += 1
            if j >= n:
                break
            if css[j] == ";":
                i = j + 1
                continue
            # css[j] == '{' — find matching closer
            depth = 1
            k = j + 1
            while k < n and depth > 0:
                if css[k] == "{":
                    depth += 1
                elif css[k] == "}":
                    depth -= 1
                k += 1
            i = k
        else:
            out.append(ch)
            i += 1
    return "".join(out)


@dataclass
class _CssRule:
    selectors: list[str]
    declarations: dict[str, str]
    selector_text: str
    # Last-declaration-wins map of custom properties (--name → value).
    custom_props: dict[str, str] = field(default_factory=dict)


# A rule body: matches "{ ... }" with no nested braces. We pre-strip
# at-rule blocks so nested rules shouldn't appear at this stage.
_CSS_RULE_RE = re.compile(
    r"(?P<sel>[^{}]+?)\s*\{\s*(?P<body>[^{}]*?)\s*\}",
    re.DOTALL,
)


def _parse_declarations(body: str) -> tuple[dict[str, str], dict[str, str]]:
    """
    Split a CSS rule body into ``{property: value}``. Returns two maps:
    one for "normal" declarations and one for ``--custom-property``
    declarations. Last value wins on duplicates. Comments must be
    stripped beforehand.
    """
    decls: dict[str, str] = {}
    custom: dict[str, str] = {}
    # Use a manual splitter so values that contain semicolons inside
    # function call parens (e.g. rgba(160, 64, 32, 0.25)) survive.
    depth = 0
    buf: list[str] = []
    pieces: list[str] = []
    for ch in body:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == ";" and depth == 0:
            pieces.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        pieces.append("".join(buf))
    for piece in pieces:
        if ":" not in piece:
            continue
        name, _, value = piece.partition(":")
        name = name.strip()
        value = value.strip()
        # Strip a trailing "!important" (whitespace-tolerant, case-insensitive).
        # Do NOT use str.rstrip("!important") — that treats the argument as a
        # character set and silently chews real value characters (e.g. the
        # trailing 'a' in #8a847a).
        m = re.match(r"^(.*?)\s*!important\s*$", value, re.IGNORECASE)
        if m:
            value = m.group(1).strip()
        if not name or not value:
            continue
        if name.startswith("--"):
            custom[name] = value
        else:
            decls[name.lower()] = value
    return decls, custom


def _parse_rules(css: str) -> list[_CssRule]:
    """Walk a CSS string and return one _CssRule per top-level rule."""
    css = _strip_at_rule_blocks(_strip_css_comments(css))
    rules: list[_CssRule] = []
    for match in _CSS_RULE_RE.finditer(css):
        selector_text = match.group("sel").strip()
        if not selector_text or selector_text.startswith("@"):
            continue
        body = match.group("body")
        decls, custom = _parse_declarations(body)
        if not decls and not custom:
            continue
        selectors = [s.strip() for s in selector_text.split(",") if s.strip()]
        if not selectors:
            continue
        rules.append(
            _CssRule(
                selectors=selectors,
                declarations=decls,
                selector_text=selector_text,
                custom_props=custom,
            )
        )
    return rules


# ─── CSS custom-property resolution ─────────────────────────────────────

_VAR_FN_RE = re.compile(
    r"var\(\s*(--[A-Za-z0-9_-]+)\s*(?:,\s*([^)]*))?\)",
)


def _build_var_table(rules: list[_CssRule]) -> dict[str, str]:
    """
    Flatten all ``--name: value`` declarations across the rules into a
    single map. Later definitions override earlier ones (a crude
    approximation of CSS cascade; works for the common case where
    custom properties live in ``:root``).
    """
    table: dict[str, str] = {}
    for rule in rules:
        for name, value in rule.custom_props.items():
            table[name] = value
    return table


def _resolve_var(value: str, table: dict[str, str], depth: int = 0) -> str:
    """
    Recursively substitute ``var(--name)`` references with their resolved
    value from the var table. Depth-limited to break cycles.
    """
    if depth > 16:
        return value
    if "var(" not in value:
        return value

    def repl(m: re.Match) -> str:
        name = m.group(1)
        fallback = (m.group(2) or "").strip()
        if name in table:
            return _resolve_var(table[name], table, depth + 1)
        if fallback:
            return _resolve_var(fallback, table, depth + 1)
        return m.group(0)  # leave unresolvable as-is

    return _VAR_FN_RE.sub(repl, value)


# ─── Entry construction from rules ──────────────────────────────────────

def _classify_role(selectors: list[str]) -> str:
    """Aggregate role across a multi-selector rule: text wins, then ambiguous."""
    roles = {_selector_role(s) for s in selectors}
    if "text" in roles:
        return "text"
    if roles == {"decorative"}:
        return "decorative"
    return "ambiguous"


def _entries_from_rules(
    rules: list[_CssRule],
    var_table: dict[str, str],
    properties: Sequence[str],
    *,
    source: str = "css",
) -> tuple[list[SelectorEntry], list[str]]:
    """
    Build SelectorEntries for every rule that sets at least one of the
    given foreground properties (typically ``color`` for HTML, ``fill``
    for SVG, or both). Returns ``(entries, warnings)`` where warnings
    lists var-resolution failures.
    """
    entries: list[SelectorEntry] = []
    warnings: list[str] = []
    for rule in rules:
        raw_value: Optional[str] = None
        for prop in properties:
            if prop in rule.declarations:
                raw_value = rule.declarations[prop]
                break
        if raw_value is None:
            continue
        resolved = _resolve_var(raw_value, var_table)
        try:
            rgb = parse_color(resolved)
        except ValueError:
            if "var(" in resolved:
                warnings.append(
                    f"unresolved var() in {rule.selector_text!r}: {raw_value!r}"
                )
            continue
        if rgb is None:
            continue
        role = _classify_role(rule.selectors)
        entries.append(
            SelectorEntry(
                selectors=list(rule.selectors),
                fill=resolved,
                fill_rgb=rgb,
                role=role,
                source=source,
            )
        )
    return entries, warnings


# ─── Inline style parsing (HTML) ────────────────────────────────────────

_INLINE_STYLE_RE = re.compile(
    r"<([A-Za-z][A-Za-z0-9-]*)\b[^>]*?\bstyle\s*=\s*(['\"])(.*?)\2",
    re.DOTALL | re.IGNORECASE,
)


def _entries_from_inline_styles(
    html_source: str,
    var_table: dict[str, str],
) -> tuple[list[SelectorEntry], list[str]]:
    """
    Walk ``style="…"`` attributes in the HTML body. Audit each declared
    ``color`` (and, for inline SVG, ``fill``) value. Dedupe by
    (tag, color) so a hundred ``<span style="color:#555">`` collapse to
    one entry with ``count=N``.
    """
    # Slice off everything before <body> to avoid auditing <link>/<meta>.
    body_split = re.split(r"<body\b[^>]*>", html_source, maxsplit=1, flags=re.IGNORECASE)
    body_source = body_split[1] if len(body_split) > 1 else html_source

    grouped: dict[tuple[str, str], SelectorEntry] = {}
    warnings: list[str] = []
    for match in _INLINE_STYLE_RE.finditer(body_source):
        tag = match.group(1).lower()
        style_text = match.group(3)
        decls, _ = _parse_declarations(_strip_css_comments(style_text))
        for prop in ("color", "fill"):
            if prop not in decls:
                continue
            raw_value = decls[prop]
            resolved = _resolve_var(raw_value, var_table)
            try:
                rgb = parse_color(resolved)
            except ValueError:
                if "var(" in resolved:
                    warnings.append(
                        f"unresolved var() in inline <{tag} style=…>: {raw_value!r}"
                    )
                continue
            if rgb is None:
                continue
            key = (tag, resolved.lower())
            if key in grouped:
                grouped[key].count += 1
            else:
                role = "text" if tag in _TEXT_TAGS else "ambiguous"
                grouped[key] = SelectorEntry(
                    selectors=[f"<{tag} style {prop}:{resolved}>"],
                    fill=resolved,
                    fill_rgb=rgb,
                    role=role,
                    source="inline",
                )
    return list(grouped.values()), warnings


# ─── Background detection ───────────────────────────────────────────────

def _resolve_background_svg(
    entries: list[SelectorEntry],
    explicit_bg: Optional[str],
    svg_source: str,
) -> tuple[int, int, int]:
    """
    Pick a background color for the SVG audit.

    Priority: explicit argument → ``.bg`` class fill → first ``<rect
    fill=...>`` attribute in the SVG → ``#000000`` default.
    """
    if explicit_bg:
        rgb = parse_color(explicit_bg)
        if rgb is not None:
            return rgb
    for entry in entries:
        for s in entry.selectors:
            if s.lstrip(".#").lower() in ("bg", "background"):
                if entry.fill_rgb is not None:
                    return entry.fill_rgb
    match = re.search(
        r"<rect[^>]*\bfill\s*=\s*['\"]([^'\"]+)['\"][^>]*/?>",
        svg_source,
        flags=re.IGNORECASE,
    )
    if match:
        try:
            rgb = parse_color(match.group(1))
            if rgb is not None:
                return rgb
        except ValueError:
            pass
    return (0, 0, 0)


def _resolve_background_html(
    rules: list[_CssRule],
    var_table: dict[str, str],
    explicit_bg: Optional[str],
) -> tuple[tuple[int, int, int], Optional[str]]:
    """
    Pick a background color for the HTML audit. Returns ``(rgb, warning)``
    where the warning is non-None if we had to fall back to white.

    Priority: explicit argument → ``body { background[-color] }`` →
    ``html { background[-color] }`` → ``#ffffff`` (with warning).
    """
    if explicit_bg:
        rgb = parse_color(explicit_bg)
        if rgb is not None:
            return rgb, None
    for selector_key in ("body", "html"):
        for rule in rules:
            if any(s.strip().lower() == selector_key for s in rule.selectors):
                for prop in ("background-color", "background"):
                    if prop in rule.declarations:
                        raw = rule.declarations[prop]
                        # background shorthand may be "color image position …"
                        # — take the first whitespace-separated token that
                        # parses as a color.
                        for token in _split_background_tokens(raw):
                            resolved = _resolve_var(token, var_table)
                            try:
                                rgb = parse_color(resolved)
                            except ValueError:
                                continue
                            if rgb is not None:
                                return rgb, None
    return (255, 255, 255), (
        "no body { background } declaration found — defaulting to #ffffff"
    )


def _split_background_tokens(value: str) -> list[str]:
    """Split a CSS background shorthand into top-level tokens (paren-aware)."""
    tokens: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in value:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch.isspace() and depth == 0:
            if buf:
                tokens.append("".join(buf))
                buf = []
        else:
            buf.append(ch)
    if buf:
        tokens.append("".join(buf))
    return tokens


# ─── Style-block extraction ─────────────────────────────────────────────

def _extract_style_blocks_xml(svg_source: str) -> list[str]:
    """
    Extract ``<style>`` text via ElementTree, falling back to regex on
    parse failure. Used for SVG and as a fast path for valid XHTML.
    """
    try:
        root = ET.fromstring(svg_source)
        blocks: list[str] = []
        for elem in root.iter():
            tag = elem.tag.split("}", 1)[-1]
            if tag == "style" and elem.text:
                blocks.append(elem.text)
        if blocks:
            return blocks
    except ET.ParseError:
        pass
    return re.findall(
        r"<style[^>]*>(.*?)</style>",
        svg_source,
        flags=re.DOTALL | re.IGNORECASE,
    )


def _extract_style_blocks_html(html_source: str) -> list[str]:
    """
    Extract every ``<style>`` block from an HTML source via regex. Most
    HTML in the wild isn't well-formed XML (unclosed ``<meta>`` and the
    like), so we skip the ElementTree fast path here.
    """
    return re.findall(
        r"<style[^>]*>(.*?)</style>",
        html_source,
        flags=re.DOTALL | re.IGNORECASE,
    )


# ─── Status / scoring helpers ───────────────────────────────────────────

def _status_for(ratio: float, required: float) -> str:
    """PASS / WARN / FAIL classification for the audit table."""
    if ratio >= required:
        return "PASS"
    if ratio >= WCAG_AA:
        return "WARN"
    return "FAIL"


def _score_entries(entries: list[SelectorEntry], bg_rgb: tuple[int, int, int],
                   required: float) -> None:
    """Populate ratio, passes, status on every entry with a resolved fill."""
    for entry in entries:
        if entry.fill_rgb is None:
            continue
        entry.ratio = contrast_ratio(entry.fill_rgb, entry.bg_rgb or bg_rgb)
        if entry.role == "decorative":
            entry.passes = None
            entry.status = "SKIP"
        else:
            entry.status = _status_for(entry.ratio, required)
            entry.passes = (entry.status == "PASS")


# ─── Legibility-floor pass ──────────────────────────────────────────────

_FONT_SIZE_RE = re.compile(r"^([\d.]+)\s*(px|pt|em|rem|%)?$", re.IGNORECASE)
_FONT_WEIGHT_NAMES = {
    "normal": 400, "regular": 400, "book": 400,
    "medium": 500, "semibold": 600, "demibold": 600,
    "bold": 700, "extrabold": 800, "black": 900,
    "light": 300, "extralight": 200, "thin": 100,
    "bolder": 700, "lighter": 300,
}


def _parse_font_size_px(value: str, base_px: float = 16.0) -> Optional[float]:
    """Return font-size in pixels, or None if unparseable."""
    if not value:
        return None
    m = _FONT_SIZE_RE.match(value.strip())
    if not m:
        return None
    num = float(m.group(1))
    unit = (m.group(2) or "px").lower()
    if unit == "px":
        return num
    if unit == "pt":
        return num * (96.0 / 72.0)
    if unit in ("em", "rem"):
        return num * base_px
    if unit == "%":
        return num / 100.0 * base_px
    return None


def _parse_font_weight(value: str) -> Optional[int]:
    """Return a numeric weight, or None if unparseable."""
    if not value:
        return None
    v = value.strip().lower()
    if v in _FONT_WEIGHT_NAMES:
        return _FONT_WEIGHT_NAMES[v]
    try:
        return int(float(v))
    except ValueError:
        return None


_CAPTION_SELECTOR_RE = re.compile(
    r"(?:^|[\s>+~,])(footer|figcaption)(?:[\s:>+~,\[]|$)"
    r"|(?:^|[\s.])(byline|caption)(?:[\s.:>+~,\[]|$)",
    re.IGNORECASE,
)


def _legibility_check(rules: list[_CssRule]) -> list[LegibilityWarning]:
    """
    Apply muriel's legibility-floor rules to parsed CSS:

    - font-size ≤ 14px AND (no font-weight or font-weight < 500) → WARN.
    - opacity present AND color present → WARN ("opacity erodes contrast").
    - selector matches footer / .byline / .caption / figcaption AND
      font-size ≤ 16px → WARN ("caption text below 16px floor").

    Selectors are evaluated independently; a rule with multiple selectors
    is considered to match if any single selector matches.
    """
    warnings: list[LegibilityWarning] = []
    for rule in rules:
        decls = rule.declarations
        size_raw = decls.get("font-size")
        weight_raw = decls.get("font-weight")
        opacity_raw = decls.get("opacity")
        color_raw = decls.get("color")

        size_px = _parse_font_size_px(size_raw) if size_raw else None
        weight = _parse_font_weight(weight_raw) if weight_raw else None

        if size_px is not None and size_px <= 14.0:
            if weight is None or weight < 500:
                warnings.append(LegibilityWarning(
                    selectors=list(rule.selectors),
                    issue="sub-floor",
                    detail=(
                        f"font-size {size_px:.1f}px with weight "
                        f"{weight if weight is not None else 'default(400)'}"
                        " — sub-floor and not medium+"
                    ),
                ))

        if opacity_raw and color_raw:
            try:
                op = float(opacity_raw)
            except ValueError:
                op = 1.0
            if op < 1.0:
                warnings.append(LegibilityWarning(
                    selectors=list(rule.selectors),
                    issue="opacity-on-text",
                    detail=(
                        f"opacity {op:.2f} on a rule that also sets color — "
                        "composites effective contrast below the raw ratio"
                    ),
                ))

        if size_px is not None and size_px <= 16.0:
            for sel in rule.selectors:
                if _CAPTION_SELECTOR_RE.search(sel):
                    warnings.append(LegibilityWarning(
                        selectors=list(rule.selectors),
                        issue="caption-below-16",
                        detail=(
                            f"footer/byline/caption selector {sel!r} at "
                            f"{size_px:.1f}px — below the 16px caption floor"
                        ),
                    ))
                    break
    return warnings


# ─── SVG presentation-attribute pass ────────────────────────────────────

_RGBA_ALPHA_RE = re.compile(
    r"^rgba?\(\s*[\d.]+%?\s*[,\s]\s*[\d.]+%?\s*[,\s]\s*[\d.]+%?"
    r"\s*[,/]\s*([\d.]+)(%?)\s*\)$",
    re.IGNORECASE,
)
_SHAPE_TAGS = ("rect", "polygon", "circle", "ellipse")
_TEXT_ELEMS = ("text", "tspan")


def _color_alpha(value: str) -> float:
    """Alpha carried inside a color value itself (rgba(), #RRGGBBAA, #RGBA)."""
    v = value.strip()
    m = _RGBA_ALPHA_RE.match(v)
    if m:
        a = float(m.group(1))
        return max(0.0, min(1.0, a / 100.0 if m.group(2) else a))
    if v.startswith("#"):
        h = v[1:]
        if len(h) == 8:
            return int(h[6:8], 16) / 255.0
        if len(h) == 4:
            return int(h[3] * 2, 16) / 255.0
    return 1.0


def _composite(fg: tuple[int, int, int], alpha: float,
               bg: tuple[int, int, int]) -> tuple[int, int, int]:
    """Source-over: what an alpha-``alpha`` ``fg`` looks like on ``bg``."""
    a = max(0.0, min(1.0, alpha))
    return tuple(int(round(a * f + (1 - a) * b)) for f, b in zip(fg, bg))


def _local_tag(tag) -> str:
    return tag.split("}", 1)[-1] if isinstance(tag, str) else ""


def _num(el: ET.Element, name: str, default: float = 0.0) -> float:
    raw = el.get(name)
    if raw is None:
        return default
    try:
        return float(raw.strip().rstrip("px"))
    except ValueError:
        return default


def _paint_props(el: ET.Element) -> dict[str, str]:
    """fill / fill-opacity / opacity from attributes, inline style winning."""
    props = {k: el.get(k) for k in ("fill", "fill-opacity", "opacity")
             if el.get(k) is not None}
    style = el.get("style")
    if style:
        decls, _ = _parse_declarations(_strip_css_comments(style))
        for k in ("fill", "fill-opacity", "opacity"):
            if k in decls:
                props[k] = decls[k]
    return props


def _style_decl(el: ET.Element, name: str) -> Optional[str]:
    style = el.get("style")
    if not style:
        return None
    decls, _ = _parse_declarations(_strip_css_comments(style))
    return decls.get(name)


def _style_num(el: ET.Element, name: str) -> float:
    raw = _style_decl(el, name)
    if not raw:
        return 0.0
    try:
        return float(raw.strip().rstrip("px"))
    except ValueError:
        return 0.0


def _float_or(value: Optional[str], default: float = 1.0) -> float:
    if value is None:
        return default
    v = value.strip()
    try:
        return float(v[:-1]) / 100.0 if v.endswith("%") else float(v)
    except ValueError:
        return default


def _shape_contains(el: ET.Element, tag: str, x: float, y: float) -> bool:
    if tag == "rect":
        rx, ry = _num(el, "x"), _num(el, "y")
        w, h = _num(el, "width"), _num(el, "height")
        return w > 0 and h > 0 and rx <= x <= rx + w and ry <= y <= ry + h
    if tag == "circle":
        cx, cy, r = _num(el, "cx"), _num(el, "cy"), _num(el, "r")
        return r > 0 and (x - cx) ** 2 + (y - cy) ** 2 <= r * r
    if tag == "ellipse":
        cx, cy = _num(el, "cx"), _num(el, "cy")
        rx, ry = _num(el, "rx"), _num(el, "ry")
        return (rx > 0 and ry > 0
                and ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0)
    if tag == "polygon":
        raw = (el.get("points") or "").replace(",", " ").split()
        try:
            nums = [float(v) for v in raw]
        except ValueError:
            return False
        if len(nums) < 6 or len(nums) % 2:
            return False
        return _point_in_poly(x, y, list(zip(nums[0::2], nums[1::2])))
    if tag == "path":
        geom = _path_geometry(el.get("d") or "")
        if geom is None or geom[0] != "poly":
            return False
        return _point_in_poly(x, y, geom[1])
    return False


_PATH_TOKEN_RE = re.compile(
    r"[MmLlHhVvCcSsQqTtAaZz]|[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"
)
_PATH_ARITY = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4,
               "T": 2, "A": 7, "Z": 0}


def _path_geometry(d: str):
    """``("poly", vertices)`` for a straight-edged path, else ``("bbox", box)``.

    A path made only of move/line segments is a polygon and can be tested
    exactly (matplotlib draws its figure and axes backgrounds that way). A
    path with curves or arcs is reduced to a conservative bounding box —
    every endpoint and control point, arcs padded by their radii — which is
    enough to know text *might* sit on it, not what colour is under it.
    Returns ``None`` for an unparseable path.
    """
    tokens = _PATH_TOKEN_RE.findall(d or "")
    pts: list[tuple[float, float]] = []
    pad = 0.0
    curved = False
    cx = cy = sx = sy = 0.0
    cmd = None
    i = 0
    try:
        while i < len(tokens):
            tok = tokens[i]
            if tok.isalpha():
                cmd = tok
                i += 1
                if cmd in "Zz":
                    cx, cy = sx, sy
                    continue
            if cmd is None:
                return None
            up = cmd.upper()
            n = _PATH_ARITY[up]
            args = [float(v) for v in tokens[i:i + n]]
            if len(args) < n:
                break
            i += n
            rel = cmd.islower()
            if up == "H":
                cx = cx + args[0] if rel else args[0]
            elif up == "V":
                cy = cy + args[0] if rel else args[0]
            elif up == "A":
                curved = True
                pad = max(pad, abs(args[0]), abs(args[1]))
                cx, cy = (cx + args[5], cy + args[6]) if rel else (args[5], args[6])
            else:
                if up in "CSQ":
                    curved = True
                    for k in range(0, n - 2, 2):
                        pts.append((cx + args[k], cy + args[k + 1]) if rel
                                   else (args[k], args[k + 1]))
                cx, cy = (cx + args[-2], cy + args[-1]) if rel else (args[-2], args[-1])
            if up == "M":
                sx, sy = cx, cy
                if cmd == "M":
                    cmd = "L"  # implicit lineto after a moveto
                elif cmd == "m":
                    cmd = "l"
            pts.append((cx, cy))
    except (ValueError, KeyError):
        return None
    if not curved:
        return ("poly", pts) if len(pts) >= 3 else None
    if not pts:
        return None
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    return ("bbox", (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad))


def _point_in_poly(x: float, y: float, poly) -> bool:
    hit = False
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        if (y0 > y) != (y1 > y):
            if x < x0 + (y - y0) / (y1 - y0) * (x1 - x0):
                hit = not hit
    return hit


def _css_fill_classes(rules: list[_CssRule]) -> set[str]:
    """Class names some CSS rule assigns a fill to (CSS beats attributes)."""
    out: set[str] = set()
    for rule in rules:
        if "fill" not in rule.declarations:
            continue
        for sel in rule.selectors:
            out.update(re.findall(r"\.([A-Za-z0-9_-]+)", sel))
    return out


def _entries_from_svg_attributes(
    svg_source: str,
    rules: list[_CssRule],
    var_table: dict[str, str],
    page_bg: tuple[int, int, int],
    *,
    composite_shapes: bool = True,
) -> tuple[list[SelectorEntry], int]:
    """
    Walk ``<text>`` / ``<tspan>`` runs and build one entry per distinct
    (fill, background) pair, deduplicated with a count. Returns
    ``(entries, text_runs_seen)``; the second number is every text run
    found, scored or not, so a caller can tell "no text" from "no
    attribute-colored text".
    """
    try:
        root = ET.fromstring(svg_source)
    except ET.ParseError:
        return [], 0

    css_classes = _css_fill_classes(rules)
    grouped: dict[tuple, SelectorEntry] = {}
    painted: list[tuple[ET.Element, str, tuple[int, int, int], float]] = []
    runs = 0
    curved_boxes: list[tuple[float, float, float, float]] = []

    def resolve(raw: str) -> Optional[tuple[tuple[int, int, int], float]]:
        val = _resolve_var(raw, var_table)
        if val.strip().lower().startswith("url("):
            return None
        try:
            rgb = parse_color(val)
        except ValueError:
            return None
        if rgb is None:
            return None
        return rgb, _color_alpha(val)

    def bg_at(x: float, y: float) -> tuple[int, int, int]:
        bg = page_bg
        if not composite_shapes:
            return bg
        for el, tag, rgb, alpha in painted:
            if _shape_contains(el, tag, x, y):
                bg = _composite(rgb, alpha, bg)
        return bg

    def walk(el: ET.Element, fill: Optional[str], fill_op: float,
             op: float, transformed: bool, classes: tuple[str, ...]) -> None:
        nonlocal runs
        tag = _local_tag(el.tag)
        if tag in ("defs", "clipPath", "mask", "pattern", "marker",
                   "symbol", "title", "desc", "metadata", "style"):
            return
        props = _paint_props(el)
        own_classes = tuple((el.get("class") or "").split())
        classes = classes + own_classes
        if "fill" in props:
            fill = props["fill"]
        fill_op = fill_op * _float_or(props.get("fill-opacity"))
        op = op * _float_or(props.get("opacity"))
        transformed = transformed or bool(el.get("transform"))

        if tag == "path" and not transformed:
            geom = _path_geometry(el.get("d") or "")
            got = resolve(fill) if fill is not None else ((0, 0, 0), 1.0)
            if geom is not None and got is not None and fill_op * op > 0:
                if geom[0] == "poly":
                    painted.append((el, "path", got[0], got[1] * fill_op * op))
                else:
                    curved_boxes.append(geom[1])
        if tag in _SHAPE_TAGS and not transformed:
            if fill is not None:
                got = resolve(fill)
                if got is not None:
                    rgb, a = got
                    painted.append((el, tag, rgb, a * fill_op * op))
            elif not any(c in css_classes for c in classes):
                painted.append((el, tag, (0, 0, 0), fill_op * op))

        if tag in _TEXT_ELEMS:
            direct = (el.text or "").strip()
            if tag == "text":
                direct = direct or "".join(
                    (c.tail or "") for c in el).strip()
            if direct:
                runs += 1
                styled_by_css = any(c in css_classes for c in classes)
                if not (styled_by_css and "fill" not in props):
                    raw = fill if fill is not None else "#000000"
                    got = resolve(raw)
                    if got is not None:
                        _score_text_run(el, direct, raw, got, fill_op * op,
                                        classes)
        for child in el:
            if isinstance(child.tag, str):
                walk(child, fill, fill_op, op, transformed, classes)

    def _score_text_run(el, text, raw, got, alpha_mult, classes):
        rgb, a = got
        # Anchor point comes from the nearest <text> with coordinates.
        x = _num(el, "x", float("nan"))
        y = _num(el, "y", float("nan"))
        if x != x or y != y:  # NaN → a tspan without its own position
            parent = text_positions.get(el)
            x, y = parent if parent else (0.0, 0.0)
        fs = (_num(el, "font-size", 0.0) or _style_num(el, "font-size")
              or text_sizes.get(el, 16.0))
        w = 0.55 * fs * len(text)
        anchor = (el.get("text-anchor") or _style_decl(el, "text-anchor")
                  or text_anchors.get(el, "start"))
        x0 = {"middle": x - w / 2, "end": x - w}.get(anchor, x)
        cy = y - 0.35 * fs
        worst: Optional[tuple[float, tuple, tuple]] = None
        samples = (x0 + 1, x0 + w / 2, x0 + w - 1)
        unverified = any(
            bx0 <= sx <= bx1 and by0 <= cy <= by1
            for sx in samples
            for bx0, by0, bx1, by1 in curved_boxes
        )
        for sx in samples:
            bg = bg_at(sx, cy)
            fg = _composite(rgb, a * alpha_mult, bg)
            ratio = contrast_ratio(fg, bg)
            if worst is None or ratio < worst[0]:
                worst = (ratio, fg, bg)
        _, fg, bg = worst
        role = "text"
        if classes and all(_selector_role("." + c) == "decorative"
                           for c in classes):
            role = "decorative"
        key = (fg, bg, role, unverified)
        if key in grouped:
            grouped[key].count += 1
            return
        bg_hex = "#{:02x}{:02x}{:02x}".format(*bg)
        snippet = text if len(text) <= 24 else text[:23] + "…"
        grouped[key] = SelectorEntry(
            selectors=[f"<text fill={raw.strip()}> on {bg_hex}"
                       + (" (over a curved <path>: unverified)" if unverified else "")
                       + f" “{snippet}”"],
            fill=raw.strip(),
            fill_rgb=fg,
            role=role,
            source="svg-attr",
            bg_rgb=bg,
            unverified=unverified,
        )

    # tspans inherit position / size / anchor from their <text>
    text_positions: dict[ET.Element, tuple[float, float]] = {}
    text_sizes: dict[ET.Element, float] = {}
    text_anchors: dict[ET.Element, str] = {}
    for t_el in root.iter():
        if _local_tag(t_el.tag) != "text":
            continue
        pos = (_num(t_el, "x"), _num(t_el, "y"))
        size = _num(t_el, "font-size", 0.0) or _style_num(t_el, "font-size") or 16.0
        anch = t_el.get("text-anchor") or _style_decl(t_el, "text-anchor") or "start"
        for sub in t_el.iter():
            if sub is t_el:
                continue
            text_positions[sub] = (_num(sub, "x", pos[0]), _num(sub, "y", pos[1]))
            text_sizes[sub] = _num(sub, "font-size", size)
            text_anchors[sub] = sub.get("text-anchor", anch)

    root_props = _paint_props(root)
    walk(root, root_props.get("fill"), 1.0, 1.0, False, ())
    return list(grouped.values()), runs


# ─── Public audit functions ─────────────────────────────────────────────

def audit_svg(
    path: Union[str, Path],
    required: float = RENDER_8,
    background: Optional[str] = None,
    print_table: bool = True,
) -> list[SelectorEntry]:
    """
    Audit every CSS fill rule, and every ``<text>``/``<tspan>`` colored by
    a presentation attribute, in an SVG file against a contrast threshold.

    Parameters
    ----------
    path
        Path to an SVG file with a ``<defs><style>`` block.
    required
        Minimum contrast ratio for text rules. Default: muriel's 8.0.
    background
        Override the background color. If ``None``, auto-detects ``.bg``
        class fill or the first ``<rect fill=...>`` attribute, falling
        back to ``#000000``. An explicit background also switches off
        per-text shape compositing: every attribute-colored text run is
        scored against it as given.
    print_table
        If ``True``, prints a formatted audit table to stdout.

    Returns
    -------
    list[SelectorEntry]
        One per CSS rule with a resolvable fill, then one per distinct
        (text color, background) pair among attribute-colored text runs
        (``source="svg-attr"``, ``bg_rgb`` set, ``count`` = runs). Each entry has
        ``ratio``, ``status`` and ``passes`` populated. Decorative
        entries have ``passes=None`` (exempt).
    """
    svg_path = Path(path)
    svg_source = svg_path.read_text(encoding="utf-8")

    blocks = _extract_style_blocks_xml(svg_source)
    rules: list[_CssRule] = []
    for block in blocks:
        rules.extend(_parse_rules(block))

    var_table = _build_var_table(rules)
    entries, var_warnings = _entries_from_rules(
        rules, var_table, properties=("fill",), source="css"
    )
    bg_rgb = _resolve_background_svg(entries, background, svg_source)
    attr_entries, _runs = _entries_from_svg_attributes(
        svg_source, rules, var_table, bg_rgb,
        composite_shapes=background is None,
    )
    entries.extend(attr_entries)
    _score_entries(entries, bg_rgb, required)

    legibility = _legibility_check(rules)

    if print_table:
        _print_audit_table(
            svg_path, bg_rgb, required, entries,
            legibility=legibility,
            extra_warnings=var_warnings,
        )

    return entries


def audit_html(
    path: Union[str, Path],
    required: float = RENDER_8,
    background: Optional[str] = None,
    print_table: bool = True,
    audit_inline_styles: bool = True,
) -> tuple[list[SelectorEntry], list[LegibilityWarning]]:
    """
    Audit every CSS color rule (and inline ``style="…"`` color) in an
    HTML file against a contrast threshold.

    Parameters
    ----------
    path
        Path to an HTML file. ``<style>`` blocks in ``<head>`` and inline
        ``style="…"`` attributes on body elements are walked.
    required
        Minimum contrast ratio for text rules. Default: muriel's 8.0.
    background
        Override the background color. If ``None``, auto-detects
        ``body { background[-color] }``, then ``html { background[-color] }``,
        falling back to ``#ffffff`` with a warning.
    print_table
        If ``True``, prints a formatted audit table to stdout.
    audit_inline_styles
        If ``True`` (default), also walks ``style="…"`` attributes on
        body elements and audits any ``color`` / ``fill`` declarations.

    Returns
    -------
    tuple[list[SelectorEntry], list[LegibilityWarning]]
        (contrast entries, legibility warnings).
    """
    html_path = Path(path)
    html_source = html_path.read_text(encoding="utf-8")

    blocks = _extract_style_blocks_html(html_source)
    rules: list[_CssRule] = []
    for block in blocks:
        rules.extend(_parse_rules(block))

    var_table = _build_var_table(rules)

    # HTML rules may also use `fill` (inline SVG); accept either property.
    css_entries, var_warnings = _entries_from_rules(
        rules, var_table, properties=("color", "fill"), source="css",
    )

    inline_entries: list[SelectorEntry] = []
    if audit_inline_styles:
        inline_entries, inline_warnings = _entries_from_inline_styles(
            html_source, var_table,
        )
        var_warnings.extend(inline_warnings)

    bg_rgb, bg_warning = _resolve_background_html(
        rules, var_table, background,
    )

    entries = css_entries + inline_entries
    _score_entries(entries, bg_rgb, required)

    legibility = _legibility_check(rules)

    extra: list[str] = list(var_warnings)
    if bg_warning:
        extra.insert(0, bg_warning)

    if print_table:
        _print_audit_table(
            html_path, bg_rgb, required, entries,
            legibility=legibility,
            extra_warnings=extra,
        )

    return entries, legibility


# ─── Pretty printer ─────────────────────────────────────────────────────

def _print_audit_table(
    src_path: Path,
    bg_rgb: tuple[int, int, int],
    required: float,
    entries: list[SelectorEntry],
    *,
    legibility: Optional[list[LegibilityWarning]] = None,
    extra_warnings: Optional[list[str]] = None,
) -> None:
    bg_hex = f"#{bg_rgb[0]:02x}{bg_rgb[1]:02x}{bg_rgb[2]:02x}"
    print(f"\nContrast audit: {src_path}")
    print(f"  background:  {bg_hex}")
    print(f"  required:    {required:.1f}:1  (WCAG {_wcag_tier(required)})")
    if extra_warnings:
        for w in extra_warnings:
            print(f"  note:        {w}")
    print()
    headers = ("Status", "Ratio",  "Fill",   "Role",       "Selectors")
    widths  = (     6,       8,       10,       12,           48)
    header_line = "  " + "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("  " + "  ".join("─" * w for w in widths))

    fail_count = warn_count = pass_count = skip_count = 0

    for entry in entries:
        if entry.fill_rgb is None:
            continue
        status = entry.status or "?"
        if status == "FAIL":
            fail_count += 1
        elif status == "WARN":
            warn_count += 1
        elif status == "PASS":
            pass_count += 1
        elif status == "SKIP":
            skip_count += 1
        ratio_str = f"{entry.ratio:.2f}:1" if entry.ratio is not None else "—"
        fill_str = entry.fill_hex or entry.fill or "?"
        sel_str = entry.selector_display
        if entry.source in ("inline", "svg-attr") and entry.count > 1:
            sel_str = f"{sel_str}  (×{entry.count})"
        if len(sel_str) > widths[4]:
            sel_str = sel_str[: widths[4] - 1] + "…"
        print(
            "  "
            + status.ljust(widths[0])
            + "  " + ratio_str.ljust(widths[1])
            + "  " + fill_str.ljust(widths[2])
            + "  " + entry.role.ljust(widths[3])
            + "  " + sel_str
        )

    print()
    summary_parts = [
        f"{pass_count} pass",
        f"{warn_count} warn",
        f"{fail_count} fail",
        f"{skip_count} decorative (exempt)",
    ]
    print(f"  contrast:  {' · '.join(summary_parts)}")

    if legibility:
        print()
        print(f"  legibility-floor warnings ({len(legibility)}):")
        for w in legibility:
            sel = ", ".join(w.selectors)
            if len(sel) > 60:
                sel = sel[:59] + "…"
            print(f"    [{w.issue}] {sel}")
            print(f"        {w.detail}")

    print()
    below = fail_count + warn_count
    if below:
        print(
            f"  result:    FAIL — {below} text rule(s) below {required:.1f}:1"
        )
    elif legibility:
        print(
            f"  result:    WARN — contrast clears {required:.1f}:1 but "
            f"{len(legibility)} legibility-floor issue(s)"
        )
    else:
        print(f"  result:    PASS — every text rule clears {required:.1f}:1")


# ─── CLI ────────────────────────────────────────────────────────────────

def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m muriel.contrast",
        description=(
            "Audit WCAG contrast ratios in an SVG or HTML file. "
            "HTML mode also runs the legibility-floor pass."
        ),
    )
    parser.add_argument("path", type=Path, nargs="+",
                        help="SVG or HTML file(s) to audit.")
    parser.add_argument(
        "--required", type=float, default=RENDER_8,
        help="Minimum contrast ratio for text rules (default: 8.0, muriel's rule).",
    )
    parser.add_argument(
        "--background", type=str, default=None,
        help="Override the background color. Auto-detected from .bg class "
             "or body { background } if not provided.",
    )
    parser.add_argument(
        "--no-inline", action="store_true",
        help="HTML only: skip inline style=\"…\" attributes.",
    )
    args = parser.parse_args(argv)

    total_fail = 0
    total_legibility = 0
    for p in args.path:
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 3
        ext = p.suffix.lower()
        if ext in (".html", ".htm"):
            entries, legibility = audit_html(
                p,
                required=args.required,
                background=args.background,
                print_table=True,
                audit_inline_styles=not args.no_inline,
            )
            total_legibility += len(legibility)
        else:
            entries = audit_svg(
                p,
                required=args.required,
                background=args.background,
                print_table=True,
            )
        total_fail += sum(
            1 for e in entries
            if e.status in ("FAIL", "WARN")
        )

    if total_fail:
        return 1
    if total_legibility:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
