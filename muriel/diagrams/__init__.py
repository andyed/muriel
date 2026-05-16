"""diagrams — Mermaid → SVG / ASCII via beautiful-mermaid (Node bridge).

Renders Mermaid source to self-contained SVG strings (or terminal-ready
ASCII) without a headless browser. Built on the upstream
beautiful-mermaid package (synchronous, zero DOM, ELK layout engine).

Supported diagram types
-----------------------
- flowchart       (``graph TD``, ``flowchart LR``)
- state           (``stateDiagram-v2``)
- sequence        (``sequenceDiagram``)
- class           (``classDiagram``)
- ER              (``erDiagram``)
- XY chart        (``xychart-beta``)

Two uses
--------
1. **Drop SVG into figures.** Use ``Diagram.svg`` or ``Diagram.svg_at``.
2. **Participate in layout.** Each fragment exposes a measured
   :class:`muriel.layout.BBox`. Pass ``Diagram.at(x, y)`` into
   ``place_label(obstacles=...)`` so neighbouring labels avoid it.

Theming
-------
Built-in themes (``zinc-dark``, ``tokyo-night``, ``catppuccin-mocha``,
…) accepted by name. Override individual colors via keyword
arguments — ``bg``, ``fg``, ``line``, ``accent``, ``muted``,
``surface``, ``border``. With just ``bg``/``fg`` you get a coherent
two-color palette; everything else is derived via ``color-mix()``.

Setup
-----
    cd muriel/diagrams && npm install

The Node binary is located via ``$PATH``. Set ``MURIEL_DIAGRAMS_NODE``
to override.

Cache lives at ``~/.cache/muriel/diagrams/`` (override with
``MURIEL_DIAGRAMS_CACHE``).

Usage
-----
    from muriel.diagrams import render, render_ascii
    d = render("graph TD\\nA[Start] --> B[End]", theme="tokyo-night")
    d.svg          # <svg>...</svg>
    d.bbox         # BBox(0, 0, w, h)
    d.svg_at(120, 80)

    text = render_ascii("graph LR; A --> B --> C")
    print(text)

CLI
---
    python -m muriel.diagrams --selftest
    python -m muriel.diagrams 'graph TD; A --> B' --theme zinc-dark
    python -m muriel.diagrams 'graph LR; A --> B' --ascii
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from ..layout import BBox

__all__ = [
    "Diagram",
    "DiagramError",
    "render",
    "render_ascii",
    "cache_clear",
    "flatten_css_vars",
    "THEMES",
]


class DiagramError(RuntimeError):
    """Raised when a Mermaid render fails (missing Node, install gap, bad source)."""


_PKG_DIR = Path(__file__).parent
_BRIDGE_JS = _PKG_DIR / "render.mjs"
_NODE_MODULES = _PKG_DIR / "node_modules"

_CACHE_DIR = Path(
    os.environ.get(
        "MURIEL_DIAGRAMS_CACHE",
        str(Path.home() / ".cache" / "muriel" / "diagrams"),
    )
)

# Theme names recognised by beautiful-mermaid out of the box. Kept in
# sync with src/theme.ts in the upstream package. Source of truth is
# still the upstream THEMES export — this list is for autocomplete
# and validation hints only.
THEMES: tuple[str, ...] = (
    "zinc-light",
    "zinc-dark",
    "tokyo-night",
    "tokyo-night-storm",
    "tokyo-night-light",
    "catppuccin-mocha",
    "catppuccin-latte",
    "nord",
    "nord-light",
    "dracula",
    "github-light",
    "github-dark",
    "solarized-light",
    "solarized-dark",
    "one-dark",
)

# Color enrichment keys accepted on top of (or instead of) a named theme.
_COLOR_KEYS = ("bg", "fg", "line", "accent", "muted", "surface", "border")

# Layout / typography options accepted by beautiful-mermaid's RenderOptions.
_OPTION_KEYS = (
    "font",
    "padding",
    "nodeSpacing",
    "layerSpacing",
    "componentSpacing",
    "transparent",
)


@dataclass(frozen=True)
class Diagram:
    """A rendered Mermaid diagram: SVG string + measured bbox."""

    source: str
    svg: str
    width: float
    height: float
    theme: Optional[str]

    @property
    def bbox(self) -> BBox:
        """BBox anchored at (0, 0). Use ``at()`` to position it."""
        return BBox(0.0, 0.0, self.width, self.height)

    def at(self, x: float, y: float) -> BBox:
        """BBox translated to ``(x, y)`` — drop into place_label obstacles."""
        return BBox(x, y, x + self.width, y + self.height)

    def svg_at(self, x: float, y: float) -> str:
        """SVG fragment wrapped in ``<g transform="translate(x, y)">``."""
        return f'<g transform="translate({x:.2f},{y:.2f})">{self.svg}</g>'


def _canonical_payload(
    source: str,
    mode: str,
    theme: Optional[str],
    colors: dict,
    options: dict,
) -> dict:
    """Build the JSON payload sent to the bridge. Pure, no side effects."""
    return {
        "source": source,
        "mode": mode,
        "theme": theme,
        "colors": dict(sorted(colors.items())) if colors else {},
        "options": dict(sorted(options.items())) if options else {},
    }


def _cache_key(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(blob).hexdigest()[:32]


def _cache_path(key: str) -> Path:
    return _CACHE_DIR / f"{key}.json"


def _cache_load(key: str) -> Optional[dict]:
    p = _cache_path(key)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _cache_store(key: str, payload: dict) -> None:
    # Best-effort: never let a cache write fail an otherwise-good render.
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path(key).write_text(json.dumps(payload))
    except OSError:
        pass


def cache_clear() -> int:
    """Remove every cached render. Returns the count deleted."""
    if not _CACHE_DIR.exists():
        return 0
    n = 0
    for p in _CACHE_DIR.glob("*.json"):
        try:
            p.unlink()
            n += 1
        except OSError:
            pass
    return n


def _find_node() -> str:
    candidates = [
        os.environ.get("MURIEL_DIAGRAMS_NODE"),
        os.environ.get("MURIEL_MATH_NODE"),  # reuse if user already set it
        shutil.which("node"),
        "/opt/homebrew/bin/node",
        "/usr/local/bin/node",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise DiagramError(
        "node binary not found. Install Node.js (brew install node) or set "
        "MURIEL_DIAGRAMS_NODE to its absolute path."
    )


def _ensure_bridge_installed() -> None:
    if not _BRIDGE_JS.exists():
        raise DiagramError(f"bridge script missing: {_BRIDGE_JS}. Reinstall muriel.")
    if not _NODE_MODULES.exists():
        raise DiagramError(
            "beautiful-mermaid is not installed. Run:\n"
            f"    cd {_PKG_DIR} && npm install"
        )


def _invoke_bridge(payload: dict) -> dict:
    _ensure_bridge_installed()
    node = _find_node()
    try:
        proc = subprocess.run(
            [node, str(_BRIDGE_JS)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(_PKG_DIR),
        )
    except subprocess.TimeoutExpired as e:
        raise DiagramError(f"render bridge timed out after {e.timeout}s") from e

    if proc.returncode != 0:
        raise DiagramError(
            f"render bridge exited {proc.returncode}: {proc.stderr.strip()}"
        )
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise DiagramError(
            f"render bridge returned invalid JSON: {proc.stdout[:200]!r}"
        ) from e
    if "error" in result:
        raise DiagramError(f"Mermaid render failed: {result['error']}")
    return result


# ─── CSS variable flattening for rasterizer compatibility ──────────
#
# beautiful-mermaid emits CSS custom properties + color-mix() so themes
# can be swapped live in a browser. That breaks every static rasterizer
# (librsvg, cairo, ImageMagick, LaTeX) — they don't resolve var() /
# color-mix. For paper figures we need concrete hex values baked in.

def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c + c for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(
        f"{max(0, min(255, int(round(c)))):02x}" for c in rgb
    )


def _mix_srgb(a_hex: str, b_hex: str, pct: float) -> str:
    """color-mix(in srgb, A pct%, B) — sRGB-space linear blend."""
    a = _hex_to_rgb(a_hex)
    b = _hex_to_rgb(b_hex)
    p = pct / 100.0
    return _rgb_to_hex(tuple(p * a[i] + (1 - p) * b[i] for i in range(3)))


# Mirrors beautiful-mermaid's MIX table in src/theme.ts. Keep in sync.
def _resolved_palette(bg: str, fg: str) -> dict[str, str]:
    return {
        "--bg": bg,
        "--fg": fg,
        "--line": _mix_srgb(fg, bg, 50),
        "--accent": _mix_srgb(fg, bg, 85),
        "--muted": _mix_srgb(fg, bg, 40),
        "--surface": _mix_srgb(fg, bg, 3),
        "--border": _mix_srgb(fg, bg, 20),
        "--_text": fg,
        "--_text-sec": _mix_srgb(fg, bg, 60),
        "--_text-muted": _mix_srgb(fg, bg, 40),
        "--_text-faint": _mix_srgb(fg, bg, 25),
        "--_line": _mix_srgb(fg, bg, 50),
        "--_arrow": _mix_srgb(fg, bg, 85),
        "--_node-fill": _mix_srgb(fg, bg, 3),
        "--_node-stroke": _mix_srgb(fg, bg, 20),
        "--_group-fill": bg,
        "--_group-hdr": _mix_srgb(fg, bg, 5),
        "--_inner-stroke": _mix_srgb(fg, bg, 12),
        "--_key-badge": _mix_srgb(fg, bg, 10),
    }


_VAR_RE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+(?:\s*,[^)]*)?)\s*\)")
_STYLE_BLOCK_RE = re.compile(r"<style>.*?</style>", flags=re.DOTALL)
_INLINE_VARS_RE = re.compile(r'\sstyle="[^"]*--[^"]*"')


def flatten_css_vars(
    svg: str, *, bg: str = "#FFFFFF", fg: str = "#27272A"
) -> str:
    """Replace every ``var(--X)`` reference in ``svg`` with a concrete hex.

    beautiful-mermaid's output uses CSS custom properties so themes can
    swap live in a browser. Static rasterizers (librsvg, cairo, LaTeX)
    cannot resolve those references and render every fill as black.
    This helper bakes the resolved palette into the SVG using the same
    MIX weights beautiful-mermaid ships with — the flattened output is
    byte-equivalent to a browser render with the given ``bg``/``fg``.

    Also strips the embedded ``<style>`` block (now redundant) and the
    inline ``style="--bg:…;--fg:…"`` attribute on the root ``<svg>``.
    """
    resolved = _resolved_palette(bg, fg)

    def replace(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        name = body.split(",", 1)[0].strip()
        return resolved.get(name, match.group(0))

    svg = _VAR_RE.sub(replace, svg)
    svg = _STYLE_BLOCK_RE.sub("", svg)
    svg = _INLINE_VARS_RE.sub("", svg)
    return svg


def _split_kwargs(kwargs: dict) -> tuple[dict, dict]:
    """Partition kwargs into (colors, options). Reject unknown keys."""
    colors: dict = {}
    options: dict = {}
    for k, v in kwargs.items():
        if v is None:
            continue
        if k in _COLOR_KEYS:
            colors[k] = v
        elif k in _OPTION_KEYS:
            options[k] = v
        else:
            raise TypeError(
                f"unknown render option {k!r}. "
                f"Colors: {_COLOR_KEYS}. Options: {_OPTION_KEYS}."
            )
    return colors, options


def render(
    source: str,
    *,
    theme: Optional[str] = None,
    flatten: bool = False,
    **kwargs: Any,
) -> Diagram:
    """Render Mermaid ``source`` to a self-contained SVG.

    ``theme`` is a built-in theme name (see :data:`THEMES`). Override
    or supply individual colors via keyword args (``bg``, ``fg``,
    ``line``, ``accent``, ``muted``, ``surface``, ``border``). Layout
    options: ``font``, ``padding``, ``nodeSpacing``, ``layerSpacing``,
    ``componentSpacing``, ``transparent``.

    Pass ``flatten=True`` to bake the CSS custom properties into
    concrete hex values. The default (``False``) emits the upstream
    var()-driven SVG, which renders correctly in browsers and supports
    live theme switching but renders as solid-black rectangles in
    librsvg, cairo, ImageMagick, and LaTeX. Use ``flatten=True`` for
    paper figures, README assets, and any downstream rasterization.
    """
    if not source or not source.strip():
        raise ValueError("source must be a non-empty Mermaid string")
    if theme is not None and theme not in THEMES:
        # Allow custom themes via colors-only path; named themes must
        # match the upstream catalogue.
        raise ValueError(
            f"unknown theme {theme!r}. Known: {', '.join(THEMES)}."
        )

    colors, options = _split_kwargs(kwargs)
    payload = _canonical_payload(source, "svg", theme, colors, options)

    key = _cache_key(payload)
    cached = _cache_load(key)
    if cached is not None and "bg" in cached:
        svg = cached["svg"]
        if flatten:
            svg = flatten_css_vars(svg, bg=cached["bg"], fg=cached["fg"])
        return Diagram(
            source=source,
            svg=svg,
            width=float(cached["width"]),
            height=float(cached["height"]),
            theme=theme,
        )

    result = _invoke_bridge(payload)
    _cache_store(
        key,
        {
            "svg": result["svg"],
            "width": result["width"],
            "height": result["height"],
            "bg": result.get("bg", "#FFFFFF"),
            "fg": result.get("fg", "#27272A"),
        },
    )
    svg = result["svg"]
    if flatten:
        svg = flatten_css_vars(
            svg,
            bg=result.get("bg", "#FFFFFF"),
            fg=result.get("fg", "#27272A"),
        )
    return Diagram(
        source=source,
        svg=svg,
        width=float(result["width"]),
        height=float(result["height"]),
        theme=theme,
    )


def render_ascii(
    source: str, *, theme: Optional[str] = None, **kwargs: Any
) -> str:
    """Render Mermaid ``source`` to a Unicode terminal diagram.

    Returns the rendered string. No bbox is computed — terminal output
    doesn't participate in the layout system. Supported diagram types
    match the upstream beautiful-mermaid ASCII engine; XY charts are
    not yet supported in ASCII mode.
    """
    if not source or not source.strip():
        raise ValueError("source must be a non-empty Mermaid string")
    if theme is not None and theme not in THEMES:
        raise ValueError(
            f"unknown theme {theme!r}. Known: {', '.join(THEMES)}."
        )

    colors, options = _split_kwargs(kwargs)
    payload = _canonical_payload(source, "ascii", theme, colors, options)

    key = _cache_key(payload)
    cached = _cache_load(key)
    if cached is not None:
        return str(cached["ascii"])

    result = _invoke_bridge(payload)
    _cache_store(key, {"ascii": result["ascii"]})
    return str(result["ascii"])


def _selftest() -> int:
    """Smoke-test the bridge end-to-end. Returns process exit code."""
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append(f"{name}: {detail or 'failed'}")

    try:
        d = render("graph TD\nA[Start] --> B[End]", theme="zinc-dark")
    except DiagramError as e:
        print(f"SKIP — bridge not available: {e}", file=sys.stderr)
        return 0

    check("render returns Diagram", isinstance(d, Diagram))
    check("svg non-empty", len(d.svg) > 0)
    check("svg starts with <svg", d.svg.lstrip().startswith("<svg"))
    check("width > 0", d.width > 0, f"got {d.width}")
    check("height > 0", d.height > 0, f"got {d.height}")
    check("bbox matches dims", d.bbox == BBox(0, 0, d.width, d.height))
    check("theme preserved", d.theme == "zinc-dark")

    # Cache hit: second render is byte-identical.
    d2 = render("graph TD\nA[Start] --> B[End]", theme="zinc-dark")
    check("cache returns identical svg", d.svg == d2.svg)

    # at() translates the bbox without resizing.
    box = d.at(100, 50)
    check("at() x0 set", box.x0 == 100)
    check("at() y0 set", box.y0 == 50)
    check("at() width preserved", abs(box.width - d.width) < 1e-9)

    # Custom colors path.
    d3 = render("graph LR\nA --> B", bg="#101010", fg="#fafafa")
    check("custom colors svg non-empty", len(d3.svg) > 0)

    # ASCII mode.
    try:
        ascii_out = render_ascii("graph LR\nA --> B --> C")
        check("ascii non-empty", len(ascii_out) > 0)
        check("ascii has box chars", any(ch in ascii_out for ch in "┌─└│"))
    except DiagramError as e:
        check("ascii render", False, str(e))

    # Sequence diagram (different parser path).
    try:
        seq = render(
            "sequenceDiagram\nAlice->>Bob: Hello\nBob-->>Alice: Hi",
            theme="zinc-dark",
        )
        check("sequence svg non-empty", len(seq.svg) > 0)
    except DiagramError as e:
        check("sequence render", False, str(e))

    # flatten=True must produce an SVG free of var() and color-mix(),
    # so it renders correctly in static rasterizers (librsvg, cairo).
    flat = render(
        "graph TD\nA[Start] --> B[End]", theme="zinc-light", flatten=True
    )
    check("flattened svg non-empty", len(flat.svg) > 0)
    check("flattened svg has no var()", "var(--" not in flat.svg)
    check("flattened svg has no color-mix", "color-mix" not in flat.svg)
    check("flattened svg has hex colors", "#" in flat.svg)

    # Empty input raises.
    try:
        render("")
    except ValueError:
        pass
    else:
        check("empty source raises ValueError", False, "did not raise")

    # Unknown theme raises.
    try:
        render("graph TD\nA --> B", theme="nonexistent-theme")
    except ValueError:
        pass
    else:
        check("bad theme raises ValueError", False, "did not raise")

    # Bad source raises DiagramError.
    try:
        render("not a real mermaid diagram syntax ::: !!!")
    except (DiagramError, ValueError):
        pass
    else:
        check("bad source raises", False, "did not raise")

    # Unknown kwarg rejected.
    try:
        render("graph TD\nA --> B", nonexistent_kwarg="x")  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        check("unknown kwarg raises TypeError", False, "did not raise")

    if failures:
        for f in failures:
            print(f"FAIL  {f}", file=sys.stderr)
        return 1
    print(f"OK  basic checks passed (cache at {_CACHE_DIR})")
    return 0
