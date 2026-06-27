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
- Alpha channel ignored — we assume opaque text on opaque background.
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
        entry.ratio = contrast_ratio(entry.fill_rgb, bg_rgb)
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


# ─── Public audit functions ─────────────────────────────────────────────

def audit_svg(
    path: Union[str, Path],
    required: float = RENDER_8,
    background: Optional[str] = None,
    print_table: bool = True,
) -> list[SelectorEntry]:
    """
    Audit every CSS fill rule in an SVG file against a contrast threshold.

    Parameters
    ----------
    path
        Path to an SVG file with a ``<defs><style>`` block.
    required
        Minimum contrast ratio for text rules. Default: muriel's 8.0.
    background
        Override the background color. If ``None``, auto-detects ``.bg``
        class fill or the first ``<rect fill=...>`` attribute, falling
        back to ``#000000``.
    print_table
        If ``True``, prints a formatted audit table to stdout.

    Returns
    -------
    list[SelectorEntry]
        One per CSS rule with a resolvable fill. Each entry has
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
        if entry.source == "inline" and entry.count > 1:
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
