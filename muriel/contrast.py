"""
muriel.contrast — WCAG 2.1 contrast ratio helpers.

Standard-library-only module for computing WCAG 2.1 relative-luminance
contrast ratios between two sRGB colors, checking text/background pairs
against muriel's 8:1 rule (or any threshold), and auditing an SVG by
walking its ``<defs><style>`` block.

Created because the author shipped a set of SVGs claiming "8:1 on all
text" without actually running the numbers. Three text roles quietly
failed the rule and only got caught when a sharp collaborator asked
"is that really 8:1?" This module exists so that question has a
one-command answer.

Usage
-----

Programmatic:

.. code-block:: python

    from muriel.contrast import (
        contrast_ratio, check_text_pair, audit_svg, parse_color,
    )

    contrast_ratio("#e6e4d2", "#0a0a0f")         # → 15.42
    check_text_pair("#8a8aa0", "#0a0a0f")         # CheckResult(passes=False, …)
    audit_svg("examples/example-palette.svg")   # prints audit table

CLI:

.. code-block:: bash

    python -m muriel.contrast path/to/file.svg
    python -m muriel.contrast path/to/file.svg --required 4.5
    python -m muriel.contrast path/to/file.svg --background '#ffffff'

Exit status is 0 if every text rule clears the threshold, 1 if any fail,
2 on usage errors — so it slots into a pre-commit hook or CI check.

Thresholds
----------

- ``RENDER_8`` = 8.0 — muriel's universal rule (primary default)
- ``WCAG_AAA`` = 7.0 — WCAG 2.1 AAA normal text
- ``WCAG_AA``  = 4.5 — WCAG 2.1 AA  normal text
- ``WCAG_AA_LARGE`` = 3.0 — WCAG 2.1 AA large text (≥18pt or ≥14pt bold)

Limitations
-----------

- sRGB only; no P3 / Rec.2020 / Oklab
- Text pairs only; does not evaluate non-text UI / graphical contrast
- Parses CSS inside ``<style>`` blocks via a minimal regex — it will miss
  ``@media`` rules, nested rules, or anything exotic. It handles the
  common idioms used by ``muriel`` / ``marginalia`` SVGs.
- Inline ``fill`` attributes on individual ``<text>`` elements are not
  audited (v1). If your SVG sets fills via attributes rather than CSS
  classes, add a ``<style>`` block with equivalent classes first.
- Alpha channel ignored — we assume opaque text on opaque background.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
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
    "audit_svg",
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


# ─── SVG audit ──────────────────────────────────────────────────────────

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


def _selector_role(selector: str) -> str:
    """
    Classify a CSS selector as ``'text'``, ``'decorative'``, or
    ``'ambiguous'``. Text hints beat decorative hints. Ambiguous entries
    are checked (conservative default) but labeled so the user knows.
    """
    key = selector.strip().lstrip(".#").lower()
    # Text wins over decorative. Check longer hints first to avoid
    # "bg" matching "bg-text" falsely (no such case in practice but
    # the priority is explicit).
    if any(hint in key for hint in _TEXT_HINTS):
        return "text"
    if any(hint in key for hint in _DECORATIVE_HINTS):
        return "decorative"
    return "ambiguous"


@dataclass
class SelectorEntry:
    """One CSS rule with a resolvable ``fill`` value."""
    selectors: list[str]
    fill: Optional[str]
    fill_rgb: Optional[tuple[int, int, int]]
    role: str  # 'text' | 'decorative' | 'ambiguous'
    # Populated by audit_svg after background is resolved
    ratio: Optional[float] = None
    passes: Optional[bool] = None  # None means "exempt" (decorative)

    @property
    def fill_hex(self) -> Optional[str]:
        if self.fill_rgb is None:
            return None
        r, g, b = self.fill_rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    @property
    def selector_display(self) -> str:
        return ", ".join(self.selectors)


_CSS_RULE_RE = re.compile(
    r"(?P<sel>[^{}]+?)\s*\{\s*(?P<body>[^{}]*?)\s*\}",
    re.DOTALL,
)

_FILL_RE = re.compile(
    r"(?:^|[;\s])fill\s*:\s*([^;}]+?)(?=[;}]|$)",
    re.IGNORECASE,
)


def _strip_css_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def _extract_style_blocks(svg_source: str) -> list[str]:
    """
    Extract the text content of every ``<style>`` block in the SVG.
    Tries ElementTree first; falls back to regex on parse failure.
    """
    try:
        root = ET.fromstring(svg_source)
        blocks: list[str] = []
        for elem in root.iter():
            tag = elem.tag.split("}", 1)[-1]  # drop XML namespace
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


def _parse_css_rules(css: str) -> list[SelectorEntry]:
    """Walk a CSS string and return one SelectorEntry per rule with a fill."""
    css = _strip_css_comments(css)
    entries: list[SelectorEntry] = []
    for match in _CSS_RULE_RE.finditer(css):
        selector_group = match.group("sel").strip()
        if selector_group.startswith("@"):
            continue  # skip @media / @font-face / etc.
        body = match.group("body")
        fill_match = _FILL_RE.search(body)
        if not fill_match:
            continue
        fill_raw = fill_match.group(1).strip()
        try:
            fill_rgb = parse_color(fill_raw)
        except ValueError:
            fill_rgb = None
        if fill_rgb is None:
            continue
        selectors = [s.strip() for s in selector_group.split(",") if s.strip()]
        roles = {_selector_role(s) for s in selectors}
        # Text beats everything; decorative-only when unanimous
        if "text" in roles:
            role = "text"
        elif roles == {"decorative"}:
            role = "decorative"
        else:
            role = "ambiguous"
        entries.append(
            SelectorEntry(
                selectors=selectors,
                fill=fill_raw,
                fill_rgb=fill_rgb,
                role=role,
            )
        )
    return entries


def _resolve_background(
    entries: list[SelectorEntry],
    explicit_bg: Optional[str],
    svg_source: str,
) -> tuple[int, int, int]:
    """
    Pick a background color to compute contrast against.

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
        ``ratio`` and ``passes`` populated. Decorative entries have
        ``passes=None`` (exempt).
    """
    svg_path = Path(path)
    svg_source = svg_path.read_text(encoding="utf-8")

    blocks = _extract_style_blocks(svg_source)
    entries: list[SelectorEntry] = []
    for block in blocks:
        entries.extend(_parse_css_rules(block))

    bg_rgb = _resolve_background(entries, background, svg_source)

    for entry in entries:
        if entry.fill_rgb is None:
            continue
        entry.ratio = contrast_ratio(entry.fill_rgb, bg_rgb)
        if entry.role == "decorative":
            entry.passes = None  # exempt
        else:
            entry.passes = entry.ratio >= required

    if print_table:
        _print_audit_table(svg_path, bg_rgb, required, entries)

    return entries


def _print_audit_table(
    svg_path: Path,
    bg_rgb: tuple[int, int, int],
    required: float,
    entries: list[SelectorEntry],
) -> None:
    bg_hex = f"#{bg_rgb[0]:02x}{bg_rgb[1]:02x}{bg_rgb[2]:02x}"
    print(f"\nContrast audit: {svg_path}")
    print(f"  background:  {bg_hex}")
    print(f"  required:    {required:.1f}:1  (WCAG {_wcag_tier(required)})")
    print()
    headers = ("Status", "Ratio",  "Fill",   "Role",       "Selectors")
    widths  = (     6,       8,       10,       12,           48)
    header_line = "  " + "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("  " + "  ".join("─" * w for w in widths))

    fail_count = pass_count = skip_count = 0

    for entry in entries:
        if entry.fill_rgb is None:
            continue
        if entry.role == "decorative":
            status = "SKIP"
            skip_count += 1
        elif entry.passes:
            status = "PASS"
            pass_count += 1
        else:
            status = "FAIL"
            fail_count += 1
        ratio_str = f"{entry.ratio:.2f}:1" if entry.ratio is not None else "—"
        fill_str = entry.fill_hex or entry.fill or "?"
        sel_str = entry.selector_display
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
    print(
        f"  summary: {pass_count} pass · {fail_count} fail · "
        f"{skip_count} decorative (exempt)"
    )
    if fail_count:
        print(f"  result:  FAIL — {fail_count} text rule(s) below {required:.1f}:1")
    else:
        print(f"  result:  PASS — every text rule clears {required:.1f}:1")


# ─── CLI ────────────────────────────────────────────────────────────────

def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m muriel.contrast",
        description="Audit WCAG contrast ratios on every fill rule in an SVG.",
    )
    parser.add_argument("svg", type=Path, nargs="+",
                        help="SVG file(s) to audit.")
    parser.add_argument(
        "--required", type=float, default=RENDER_8,
        help="Minimum contrast ratio for text rules (default: 8.0, muriel's rule).",
    )
    parser.add_argument(
        "--background", type=str, default=None,
        help="Override the background color. Auto-detected from .bg class "
             "or first <rect fill=...> if not provided.",
    )
    args = parser.parse_args(argv)

    total_fail = 0
    for svg in args.svg:
        if not svg.exists():
            print(f"error: file not found: {svg}", file=sys.stderr)
            return 2
        entries = audit_svg(
            svg,
            required=args.required,
            background=args.background,
            print_table=True,
        )
        total_fail += sum(1 for e in entries if e.passes is False)
    return 1 if total_fail else 0


if __name__ == "__main__":
    raise SystemExit(_main())
