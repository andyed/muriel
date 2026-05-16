"""math — TeX → SVG via MathJax v3 (Node bridge).

Pre-renders LaTeX equations to self-contained SVG fragments with
measured bounding boxes. Each fragment embeds every glyph as an
inline SVG path (``fontCache: "none"``), so it drops into any
artifact without an external font dependency.

Two uses
--------
1. **Embed in figures.** Use ``Math.svg`` or ``Math.svg_at(x, y)``.
2. **Participate in layout.** Each fragment exposes a measured
   :class:`muriel.layout.BBox`. Pass ``Math.at(x, y)`` into
   ``place_label(obstacles=...)`` so neighbouring labels avoid it.
   *Placing the math itself* is the caller's job for now — a
   ``place_math()`` helper will follow once real cases land.

Why a Node bridge?
------------------
MathJax v3 is the canonical TeX renderer with the deepest LaTeX
surface (``align``, ``cases``, ``mathbb``, custom macros). There is
no pure-Python equivalent with the same coverage. The bridge is a
~70-line ``tex2svg.js`` invoked as a subprocess; output is cached
per ``(tex, display, font_size_px)`` so repeat renders are O(stat).

Setup
-----
    cd muriel/math && npm install

The Node binary is located via ``$PATH``. ``/opt/homebrew/bin/node``
(Homebrew on Apple Silicon) works out of the box; set
``MURIEL_MATH_NODE`` to an absolute path to override.

Cache lives at ``~/.cache/muriel/math/`` (override with
``MURIEL_MATH_CACHE``). Clear with ``cache_clear()`` or
``python -m muriel.math --cache-clear``.

Usage
-----
    from muriel.math import inline, display
    m = inline(r"d_{\\min}", font_size_px=13)
    m.svg                  # <svg>...</svg>
    m.bbox                 # BBox(0, 0, w, h) in CSS px
    m.at(x=120, y=80)      # BBox translated — obstacle for place_label
    m.svg_at(x=120, y=80)  # <g transform="translate(…)">…</g>

CLI
---
    python -m muriel.math --selftest
    python -m muriel.math 'E = mc^2' --display
    python -m muriel.math 'd_{\\min}' --font-size 13 --bbox
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..layout import BBox

__all__ = ["Math", "MathError", "inline", "display", "cache_clear"]


class MathError(RuntimeError):
    """Raised when TeX cannot be rendered (missing Node, install gap, bad LaTeX)."""


_PKG_DIR = Path(__file__).parent
_BRIDGE_JS = _PKG_DIR / "tex2svg.js"
_NODE_MODULES = _PKG_DIR / "node_modules"

_CACHE_DIR = Path(
    os.environ.get(
        "MURIEL_MATH_CACHE",
        str(Path.home() / ".cache" / "muriel" / "math"),
    )
)

# Matches matplotlib "small" body text — comfortable inline default.
_DEFAULT_FONT_SIZE_PX = 13.0


@dataclass(frozen=True)
class Math:
    """A rendered TeX expression: SVG fragment plus measured bbox."""

    tex: str
    svg: str          # standalone <svg>, glyphs inlined as <path> data
    width: float      # CSS pixels at the rendered font-size
    height: float
    display: bool
    font_size_px: float

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


def _cache_key(tex: str, display: bool, font_size_px: float) -> str:
    h = hashlib.sha256()
    h.update(tex.encode("utf-8"))
    h.update(b"|D" if display else b"|I")
    h.update(b"|")
    h.update(f"{font_size_px:.3f}".encode("ascii"))
    return h.hexdigest()[:32]


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
    """Locate the Node binary, raising MathError with install hints if missing."""
    candidates = [
        os.environ.get("MURIEL_MATH_NODE"),
        shutil.which("node"),
        "/opt/homebrew/bin/node",
        "/usr/local/bin/node",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise MathError(
        "node binary not found. Install Node.js (brew install node) or set "
        "MURIEL_MATH_NODE to its absolute path."
    )


def _ensure_bridge_installed() -> None:
    if not _BRIDGE_JS.exists():
        raise MathError(f"bridge script missing: {_BRIDGE_JS}. Reinstall muriel.")
    if not _NODE_MODULES.exists():
        raise MathError(
            "mathjax-full is not installed. Run:\n"
            f"    cd {_PKG_DIR} && npm install"
        )


def _invoke_bridge(tex: str, display: bool, font_size_px: float) -> dict:
    _ensure_bridge_installed()
    node = _find_node()
    payload = json.dumps(
        {
            "tex": tex,
            "display": display,
            # 1 ex ≈ font_size * 0.5 for most fonts; MathJax expects ex.
            "ex": font_size_px / 2.0,
        }
    )
    try:
        proc = subprocess.run(
            [node, str(_BRIDGE_JS)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(_PKG_DIR),
        )
    except subprocess.TimeoutExpired as e:
        raise MathError(f"tex2svg bridge timed out after {e.timeout}s") from e

    if proc.returncode != 0:
        raise MathError(
            f"tex2svg bridge exited {proc.returncode}: {proc.stderr.strip()}"
        )
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise MathError(
            f"tex2svg bridge returned invalid JSON: {proc.stdout[:200]!r}"
        ) from e
    if "error" in result:
        raise MathError(f"TeX render failed: {result['error']}")
    return result


def _render(tex: str, display: bool, font_size_px: float) -> Math:
    if not tex or not tex.strip():
        raise ValueError("tex must be a non-empty string")
    if font_size_px <= 0:
        raise ValueError(f"font_size_px must be > 0, got {font_size_px}")

    key = _cache_key(tex, display, font_size_px)
    cached = _cache_load(key)
    if cached is not None:
        return Math(
            tex=tex,
            svg=cached["svg"],
            width=float(cached["width"]),
            height=float(cached["height"]),
            display=display,
            font_size_px=font_size_px,
        )

    result = _invoke_bridge(tex, display, font_size_px)
    _cache_store(
        key,
        {
            "svg": result["svg"],
            "width": result["width"],
            "height": result["height"],
        },
    )
    return Math(
        tex=tex,
        svg=result["svg"],
        width=float(result["width"]),
        height=float(result["height"]),
        display=display,
        font_size_px=font_size_px,
    )


def inline(tex: str, *, font_size_px: float = _DEFAULT_FONT_SIZE_PX) -> Math:
    """Render ``tex`` as inline math (``\\(…\\)`` style).

    Use for math interleaved with surrounding prose — axis labels,
    in-figure annotations, table cells. Baseline aligns with text.
    """
    return _render(tex, display=False, font_size_px=font_size_px)


def display(tex: str, *, font_size_px: float = _DEFAULT_FONT_SIZE_PX) -> Math:
    """Render ``tex`` as display math (``\\[…\\]`` style).

    Use for centred standalone equations — typically larger, with
    summation operators rendered at full size.
    """
    return _render(tex, display=True, font_size_px=font_size_px)


def _selftest() -> int:
    """Smoke-test the bridge end-to-end. Returns process exit code."""
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append(f"{name}: {detail or 'failed'}")

    # Bridge availability is environmental — skip rather than fail.
    try:
        m1 = inline(r"d_{\min}", font_size_px=13)
    except MathError as e:
        print(f"SKIP — bridge not available: {e}", file=sys.stderr)
        return 0

    check("inline returns Math", isinstance(m1, Math))
    check("inline svg non-empty", len(m1.svg) > 0)
    check("inline svg is <svg>", m1.svg.lstrip().startswith("<svg"))
    check("inline width > 0", m1.width > 0, f"got {m1.width}")
    check("inline height > 0", m1.height > 0, f"got {m1.height}")
    check(
        "bbox matches dims",
        m1.bbox == BBox(0, 0, m1.width, m1.height),
    )

    # Cache hit: second render is byte-identical.
    m2 = inline(r"d_{\min}", font_size_px=13)
    check("cache returns identical svg", m1.svg == m2.svg)
    check("cache returns identical width", m1.width == m2.width)

    # Display mode propagates and renders.
    m3 = display(r"\sum_{i=0}^{n} x_i", font_size_px=13)
    check("display svg non-empty", len(m3.svg) > 0)
    check("display flag set", m3.display is True)

    # at() translates the bbox without resizing.
    box = m1.at(100, 50)
    check("at() x0 set", box.x0 == 100)
    check("at() y0 set", box.y0 == 50)
    check("at() width preserved", abs(box.width - m1.width) < 1e-9)

    # Empty input raises.
    try:
        inline("")
    except ValueError:
        pass
    else:
        check("empty tex raises ValueError", False, "did not raise")

    # Bogus TeX raises MathError, doesn't crash.
    try:
        inline(r"\nonexistentmacroXYZ")
    except (MathError, ValueError):
        pass
    else:
        check("bad tex raises", False, "did not raise")

    if failures:
        for f in failures:
            print(f"FAIL  {f}", file=sys.stderr)
        return 1
    print(f"OK  basic checks passed (cache at {_CACHE_DIR})")
    return 0
