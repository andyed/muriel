#!/usr/bin/env python3
"""build_diagram_icons.py — vendor and normalize Lucide glyphs for diagrams.

Reads the curated slot list in ``muriel/tools/diagrams/icons/_manifest.py``,
fetches each Lucide SVG from the pinned ``lucide-static`` release on the npm
CDN (only when it is not already cached), and writes
``muriel/tools/diagrams/icons/glyphs.py``: one ``GLYPHS`` dict of slot ->
inner SVG markup.

Normalization produces **inner markup only**, on Lucide's 24×24 grid:

- the outer ``<svg>`` and the license comment are dropped;
- presentation attributes (``fill``, ``stroke*``, ``class``) are dropped,
  so the generator's wrapping ``<g>`` supplies colour and weight from brand
  tokens;
- every primitive (``circle``, ``rect``, ``line``, ``polyline``,
  ``polygon``, ``ellipse``) is rewritten as an equivalent ``<path d>``.
  The label verifier and the contrast audit both treat bare ``rect`` /
  ``circle`` / ``polygon`` as containers or backgrounds at their raw
  coordinates; a glyph drawn under a ``transform`` would read as a shape
  in the canvas's top-left corner. A path is inert to both.

The raw SVGs and Lucide's LICENSE are cached under
``muriel/tools/diagrams/icons/vendor/lucide/`` and committed, so ``--check``
runs offline. Output is deterministic: same cache, same bytes.

Structure adapted from the MIT-licensed diagram-design skill
(© 2025 Cathryn Lavery), ``scripts/build-icons.py`` — fetch-with-cache,
normalize, emit a committed artifact.

Usage:
    python3 scripts/build_diagram_icons.py            # fetch missing + write
    python3 scripts/build_diagram_icons.py --check    # exit 1 if glyphs.py stale
    python3 scripts/build_diagram_icons.py --refresh  # refetch every SVG
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = REPO_ROOT / "muriel/tools/diagrams/icons"


def _load_manifest():
    # Loaded by file path, not through the package: the package __init__
    # imports glyphs.py, which is the file this script creates.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_muriel_icon_manifest", ICONS_DIR / "_manifest.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_manifest = _load_manifest()
LUCIDE_VERSION = _manifest.LUCIDE_VERSION
SLOTS = _manifest.SLOTS

VENDOR_DIR = ICONS_DIR / "vendor/lucide"
GLYPHS_OUT = ICONS_DIR / "glyphs.py"

CDN = "https://cdn.jsdelivr.net/npm/lucide-static@{v}/{path}"
SVG_NS = "http://www.w3.org/2000/svg"
_STRIP_ATTRS = {
    "fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
    "stroke-opacity", "fill-opacity", "class", "style",
}


# ─── Fetch ──────────────────────────────────────────────────────────

def _fetch(path: str) -> str:
    url = CDN.format(v=LUCIDE_VERSION, path=path)
    req = urllib.request.Request(
        url, headers={"User-Agent": "muriel-build-diagram-icons/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


def _cached(icon_id: str, refresh: bool, offline: bool) -> str:
    path = VENDOR_DIR / f"{icon_id}.svg"
    if path.exists() and not refresh:
        raw = path.read_text(encoding="utf-8")
        # The CDN stamps the version into a leading comment; a cache
        # left over from an older pin must not pass as the current one.
        m = re.search(r"lucide-static v([\d.]+)", raw)
        if m and m.group(1) == LUCIDE_VERSION:
            return raw
        if offline:
            raise SystemExit(
                f"cached {path.name} is lucide-static v{m.group(1) if m else '?'}, "
                f"pin is v{LUCIDE_VERSION}; rerun with --refresh")
    if offline:
        raise SystemExit(f"{path.name} not cached; run without --check first")
    raw = _fetch(f"icons/{icon_id}.svg")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw, encoding="utf-8")
    return raw


# ─── Normalize ──────────────────────────────────────────────────────

def _n(v) -> str:
    """Compact, stable number formatting: 3 decimals max, no trailing 0s."""
    s = f"{float(v):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _f(el: ET.Element, name: str, default: float = 0.0) -> float:
    raw = el.get(name)
    return float(raw) if raw not in (None, "") else default


def _points(raw: str) -> list[tuple[float, float]]:
    nums = [float(v) for v in raw.replace(",", " ").split()]
    return list(zip(nums[0::2], nums[1::2]))


def _to_path_d(el: ET.Element) -> str:
    tag = el.tag.split("}", 1)[-1]
    if tag == "path":
        return " ".join(el.get("d", "").split())
    if tag == "line":
        return (f"M{_n(_f(el, 'x1'))} {_n(_f(el, 'y1'))}"
                f"L{_n(_f(el, 'x2'))} {_n(_f(el, 'y2'))}")
    if tag in ("polyline", "polygon"):
        pts = _points(el.get("points", ""))
        d = "M" + "L".join(f"{_n(x)} {_n(y)}" for x, y in pts)
        return d + ("Z" if tag == "polygon" else "")
    if tag in ("circle", "ellipse"):
        cx, cy = _f(el, "cx"), _f(el, "cy")
        if tag == "circle":
            rx = ry = _f(el, "r")
        else:
            rx, ry = _f(el, "rx"), _f(el, "ry")
        # Two half-arcs: one full-ellipse arc is degenerate in SVG.
        return (f"M{_n(cx - rx)} {_n(cy)}"
                f"a{_n(rx)} {_n(ry)} 0 1 0 {_n(2 * rx)} 0"
                f"a{_n(rx)} {_n(ry)} 0 1 0 {_n(-2 * rx)} 0Z")
    if tag == "rect":
        x, y = _f(el, "x"), _f(el, "y")
        w, h = _f(el, "width"), _f(el, "height")
        rx = el.get("rx")
        ry = el.get("ry")
        rx = float(rx) if rx is not None else (float(ry) if ry is not None else 0.0)
        ry = float(ry) if ry is not None else rx
        rx, ry = min(rx, w / 2), min(ry, h / 2)
        if rx <= 0 or ry <= 0:
            return f"M{_n(x)} {_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}Z"
        return (f"M{_n(x + rx)} {_n(y)}h{_n(w - 2 * rx)}"
                f"a{_n(rx)} {_n(ry)} 0 0 1 {_n(rx)} {_n(ry)}v{_n(h - 2 * ry)}"
                f"a{_n(rx)} {_n(ry)} 0 0 1 {_n(-rx)} {_n(ry)}h{_n(-(w - 2 * rx))}"
                f"a{_n(rx)} {_n(ry)} 0 0 1 {_n(-rx)} {_n(-ry)}v{_n(-(h - 2 * ry))}"
                f"a{_n(rx)} {_n(ry)} 0 0 1 {_n(rx)} {_n(-ry)}Z")
    raise ValueError(f"unsupported Lucide element <{tag}>")


def normalize(raw: str, icon_id: str) -> str:
    """Lucide SVG -> inner markup: one ``<path d>`` per primitive."""
    body = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL).strip()
    root = ET.fromstring(body)
    if root.tag.split("}", 1)[-1] != "svg":
        raise ValueError(f"{icon_id}: root is not <svg>")
    if root.get("viewBox") != "0 0 24 24":
        raise ValueError(f"{icon_id}: viewBox {root.get('viewBox')!r}, want 0 0 24 24")
    out = []
    for el in root:
        if not isinstance(el.tag, str):
            continue
        # A child that fills (a dot drawn as a filled circle) would lose
        # its meaning once the wrapper says fill="none". None of the
        # curated set does; refuse rather than silently hollow one out.
        fill = (el.get("fill") or "").strip().lower()
        if fill and fill != "none":
            raise ValueError(f"{icon_id}: child <{el.tag}> sets fill={fill!r}")
        extra = set(el.attrib) - _STRIP_ATTRS - {
            "d", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r",
            "rx", "ry", "width", "height", "points"}
        if extra:
            raise ValueError(f"{icon_id}: unexpected attribute(s) {sorted(extra)}")
        out.append(f'<path d="{_to_path_d(el)}"/>')
    if not out:
        raise ValueError(f"{icon_id}: no geometry")
    return "".join(out)


# ─── Emit ───────────────────────────────────────────────────────────

_HEADER = '''"""Lucide glyphs for muriel's diagram generators — GENERATED, do not edit.

Regenerate with ``python3 scripts/build_diagram_icons.py``; the slot list
lives in ``_manifest.py``. Each value is inner SVG markup on a 24×24 grid:
``<path d>`` elements only, no colour or stroke attributes — the caller's
wrapping ``<g>`` supplies ``stroke``, ``stroke-width``, ``fill="none"`` and
round caps/joins.

Lucide is ISC-licensed (some glyphs derive from Feather, MIT); see
``vendor/lucide/LICENSE`` and ``THIRD_PARTY_NOTICES.md``.
"""

'''


def render_glyphs(*, refresh: bool = False, offline: bool = False) -> str:
    lines = [_HEADER, f'LUCIDE_VERSION = "{LUCIDE_VERSION}"', "", "GLYPHS: dict[str, str] = {"]
    for slot, (icon_id, _blurb) in SLOTS.items():
        inner = normalize(_cached(icon_id, refresh, offline), icon_id)
        lines.append(f"    # {slot} <- lucide:{icon_id}")
        lines.append(f"    {slot!r}: {inner!r},")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _ensure_license(refresh: bool, offline: bool) -> None:
    path = VENDOR_DIR / "LICENSE"
    if path.exists() and not refresh:
        return
    if offline:
        raise SystemExit("vendor/lucide/LICENSE missing; run without --check")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_fetch("LICENSE"), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="rebuild from the cache only; exit 1 if glyphs.py is stale")
    ap.add_argument("--refresh", action="store_true",
                    help="refetch every SVG and the LICENSE from the CDN")
    args = ap.parse_args(argv)
    if args.check and args.refresh:
        ap.error("--check and --refresh are exclusive")

    _ensure_license(args.refresh, args.check)
    text = render_glyphs(refresh=args.refresh, offline=args.check)
    current = GLYPHS_OUT.read_text(encoding="utf-8") if GLYPHS_OUT.exists() else ""
    if args.check:
        if current != text:
            print(f"stale: {GLYPHS_OUT.relative_to(REPO_ROOT)}")
            return 1
        print(f"diagram glyphs up to date ({len(SLOTS)} slots, lucide-static v{LUCIDE_VERSION})")
        return 0
    if current != text:
        GLYPHS_OUT.write_text(text, encoding="utf-8")
        print(f"wrote: {GLYPHS_OUT.relative_to(REPO_ROOT)} ({len(SLOTS)} slots)")
    else:
        print("diagram glyphs up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
