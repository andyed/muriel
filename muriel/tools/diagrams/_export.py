"""muriel.tools.diagrams._export — strict SVG for SVG-1.1 importers.

muriel's tokens are authored as ``rgba(...)`` and render correctly
wherever colour is read as CSS (browsers, Figma, Illustrator). Strict
SVG-1.1 importers do not: PowerPoint's importer treats ``rgba(...)`` and
``transparent`` as unrecognised and paints them **opaque black**, so a
4%-alpha paper wash becomes a solid block that swallows the label in it.

:func:`strict_svg` rewrites every such colour into the SVG-1.1 form that
renders identically:

- ``rgba(r, g, b, a)`` / ``rgb(r g b / a)`` → ``#rrggbb`` plus the matching
  ``fill-opacity`` / ``stroke-opacity`` / ``stop-opacity``. An opacity
  already on the element is **multiplied**, not overwritten, so
  ``fill="rgba(…,0.5)" fill-opacity="0.8"`` becomes ``fill-opacity="0.4"``.
- ``#rrggbbaa`` / ``#rgba`` → ``#rrggbb`` plus opacity, the same way.
- ``transparent`` → ``none``.

It covers presentation attributes, inline ``style="…"`` declarations and
``<style>`` rule bodies, for ``fill``, ``stroke``, ``stop-color`` and
``flood-color`` (drop-shadow filters).
Anything else is left byte-for-byte alone, and the transform is
idempotent: a second pass finds nothing to rewrite.

The colour normalisation is adapted from the MIT-licensed diagram-design
skill (© 2025 Cathryn Lavery), ``references/export.md`` step 4, extended
to inline styles, ``<style>`` blocks, 8-digit hex and opacity
multiplication.

PNG export
----------
muriel ships no SVG rasteriser, so there is no ``--png`` here; rasterise
the strict SVG with whatever the destination uses (cairosvg, rsvg-convert,
a browser). Pick the scale with :func:`png_scale`: ``target_width /
viewBox_width`` clamped to 1–4. Below 1 soft-focuses the type (redraw at a
smaller size instead); above 4 upscales a layout designed for a smaller
canvas (redraw at a larger preset).

CLI::

    muriel diagram-export --strict in.svg -o out.svg
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional, Sequence

__all__ = ["strict_svg", "png_scale"]

_PAINT = {"fill": "fill-opacity", "stroke": "stroke-opacity",
          "stop-color": "stop-opacity", "flood-color": "flood-opacity"}

_NUM = r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"
_RGB_RE = re.compile(
    rf"^rgba?\(\s*({_NUM})(%?)\s*[,\s]\s*({_NUM})(%?)\s*[,\s]\s*({_NUM})(%?)"
    rf"\s*(?:[,/]\s*({_NUM})(%?)\s*)?\)$",
    re.IGNORECASE,
)
_HEX_ALPHA_RE = re.compile(r"^#([0-9a-fA-F]{8}|[0-9a-fA-F]{4})$")
_TAG_RE = re.compile(r"<(?![/!?])([A-Za-z_][\w:.-]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*)>")
_ATTR_RE = re.compile(r"(\s)([\w:.-]+)(\s*=\s*)(\"[^\"]*\"|'[^']*')")
_STYLE_BLOCK_RE = re.compile(r"(<style\b[^>]*>)(.*?)(</style>)",
                             re.DOTALL | re.IGNORECASE)
_RULE_BODY_RE = re.compile(r"\{([^{}]*)\}")


def _fmt(x: float) -> str:
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def _channel(v: str, pct: str) -> int:
    f = float(v) * (2.55 if pct else 1.0)
    return max(0, min(255, int(round(f))))


def _split_color(value: str):
    """``(hex, alpha)`` for a colour strict SVG can't read, else ``None``.

    ``transparent`` returns ``("none", 1.0)``. Plain ``#rrggbb``, named
    colours, ``none``, ``currentColor`` and ``url(...)`` return ``None``:
    they are already SVG 1.1.
    """
    v = value.strip()
    if v.lower() == "transparent":
        return "none", 1.0
    m = _RGB_RE.match(v)
    if m:
        r, g, b = (_channel(m.group(i), m.group(i + 1)) for i in (1, 3, 5))
        a = 1.0
        if m.group(7) is not None:
            a = float(m.group(7)) / (100.0 if m.group(8) else 1.0)
        return f"#{r:02x}{g:02x}{b:02x}", max(0.0, min(1.0, a))
    m = _HEX_ALPHA_RE.match(v)
    if m:
        h = m.group(1)
        if len(h) == 4:
            h = "".join(c * 2 for c in h)
        return f"#{h[:6].lower()}", int(h[6:8], 16) / 255.0
    return None


def _opacity(value: Optional[str]) -> float:
    if value is None:
        return 1.0
    v = value.strip()
    try:
        return float(v[:-1]) / 100.0 if v.endswith("%") else float(v)
    except ValueError:
        return 1.0


def _parse_decls(body: str) -> list[list[str]]:
    out = []
    for part in body.split(";"):
        if ":" not in part:
            if part.strip():
                out.append([part, None])
            continue
        k, v = part.split(":", 1)
        out.append([k.strip(), v.strip()])
    return out


def _decls_to_str(decls: list[list[str]]) -> str:
    return "; ".join(k if v is None else f"{k}: {v}" for k, v in decls)


def _fix_decls(body: str, attr_opacity: Optional[dict] = None):
    """Rewrite one declaration block. Returns ``(new_body, changed)``.

    ``attr_opacity`` holds the element's opacity *attributes*; a style
    colour with alpha multiplies into the style opacity when present (it
    wins over the attribute), else into the attribute value.
    """
    decls = _parse_decls(body)
    index = {k.lower(): i for i, (k, v) in enumerate(decls) if v is not None}
    changed = False
    for paint, op_name in _PAINT.items():
        if paint not in index:
            continue
        split = _split_color(decls[index[paint]][1])
        if split is None:
            continue
        hexv, alpha = split
        decls[index[paint]][1] = hexv
        changed = True
        if hexv == "none" or alpha >= 1.0:
            continue
        if op_name in index:
            base = _opacity(decls[index[op_name]][1])
            decls[index[op_name]][1] = _fmt(base * alpha)
        else:
            base = _opacity((attr_opacity or {}).get(op_name))
            decls.append([op_name, _fmt(base * alpha)])
            index[op_name] = len(decls) - 1
    if not changed:
        return body, False
    trail = ";" if body.rstrip().endswith(";") else ""
    return _decls_to_str(decls) + trail, True


def _fix_tag(m: re.Match) -> str:
    name, rest = m.group(1), m.group(2)
    attrs = {am.group(2): am for am in _ATTR_RE.finditer(rest)}
    if not any(k in attrs for k in (*_PAINT, "style")):
        return m.group(0)
    values = {k: am.group(4)[1:-1] for k, am in attrs.items()}
    new_values = dict(values)
    added: list[tuple[str, str]] = []

    style_ops = {}
    if "style" in values:
        style_ops = {k.lower(): v for k, v in _parse_decls(values["style"])
                     if v is not None}

    for paint, op_name in _PAINT.items():
        if paint not in values:
            continue
        split = _split_color(values[paint])
        if split is None:
            continue
        hexv, alpha = split
        new_values[paint] = hexv
        if hexv == "none" or alpha >= 1.0:
            continue
        if op_name in style_ops:
            # a style opacity beats the attribute, so fold alpha in there
            new_style = _parse_decls(new_values["style"])
            for d in new_style:
                if d[1] is not None and d[0].lower() == op_name:
                    d[1] = _fmt(_opacity(d[1]) * alpha)
            new_values["style"] = _decls_to_str(new_style)
        elif op_name in values:
            new_values[op_name] = _fmt(_opacity(values[op_name]) * alpha)
        else:
            added.append((op_name, _fmt(alpha)))

    if "style" in new_values:
        fixed, changed = _fix_decls(
            new_values["style"],
            {k: new_values.get(k) for k in _PAINT.values()})
        if changed:
            new_values["style"] = fixed

    if new_values == values and not added:
        return m.group(0)

    def repl(am: re.Match) -> str:
        k = am.group(2)
        if new_values.get(k) == values.get(k):
            return am.group(0)
        q = am.group(4)[0]
        return f"{am.group(1)}{k}{am.group(3)}{q}{new_values[k]}{q}"

    new_rest = _ATTR_RE.sub(repl, rest)
    closing = ""
    if new_rest.rstrip().endswith("/"):
        stripped = new_rest.rstrip()
        new_rest, closing = stripped[:-1].rstrip(), "/"
    extra = "".join(f' {k}="{v}"' for k, v in added)
    return f"<{name}{new_rest}{extra}{closing}>"


def strict_svg(text: str) -> str:
    """SVG text with every non-SVG-1.1 paint colour rewritten; see module doc."""

    def fix_block(m: re.Match) -> str:
        css = _RULE_BODY_RE.sub(
            lambda r: "{" + _fix_decls(r.group(1))[0] + "}", m.group(2))
        return m.group(1) + css + m.group(3)

    text = _STYLE_BLOCK_RE.sub(fix_block, text)
    # Tags inside <style> text are not tags; the CSS pass above owns them.
    out, pos = [], 0
    for sm in _STYLE_BLOCK_RE.finditer(text):
        out.append(_TAG_RE.sub(_fix_tag, text[pos:sm.start()]))
        out.append(_TAG_RE.sub(_fix_tag, sm.group(1)) + sm.group(2) + sm.group(3))
        pos = sm.end()
    out.append(_TAG_RE.sub(_fix_tag, text[pos:]))
    return "".join(out)


def png_scale(viewbox_width: float, target_width: float) -> float:
    """Raster scale for a target pixel width, clamped to 1–4.

    ``target_width / viewbox_width``, never below 1 (soft type: redraw
    smaller instead) and never above 4 (upscaling a small layout: redraw
    at a larger preset).
    """
    if not (viewbox_width > 0 and target_width > 0):
        raise ValueError("viewbox_width and target_width must be positive")
    return max(1.0, min(4.0, float(target_width) / float(viewbox_width)))


def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="muriel diagram-export",
        description="Rewrite rgba()/transparent/#rrggbbaa paint into "
                    "SVG-1.1 hex + opacity for PowerPoint and other strict "
                    "importers. Lossless in a browser; idempotent.",
    )
    ap.add_argument("svg", type=Path)
    ap.add_argument("--strict", action="store_true",
                    help="apply the strict SVG-1.1 colour pass (required)")
    ap.add_argument("-o", "--out", type=Path,
                    help="output path (default: stdout)")
    ap.add_argument("--check", action="store_true",
                    help="run diagram-check on the output and exit 1 on "
                         "findings (needs -o)")
    args = ap.parse_args(argv)

    if not args.strict:
        print("muriel diagram-export: nothing to do — pass --strict",
              file=sys.stderr)
        return 2
    if not args.svg.exists():
        print(f"error: file not found: {args.svg}", file=sys.stderr)
        return 2
    out = strict_svg(args.svg.read_text(encoding="utf-8"))
    if args.out is None:
        if args.check:
            print("error: --check needs -o", file=sys.stderr)
            return 2
        sys.stdout.write(out)
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out, encoding="utf-8")
    print(f"→ {args.out}")
    if args.check:
        from muriel.tools.diagrams.check import check_svg
        findings = check_svg(args.out)
        for f in findings:
            print(f"      {f}")
        return 1 if findings else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
