"""muriel.tools.diagrams.check — one gate for a rendered diagram SVG.

``muriel diagram-check a.svg b.svg …`` runs the three read-back checks the
test suite runs on muriel's own generators, on any SVG:

1. **Accessible-figure contract** — :func:`._a11y.lint_a11y`: ``role="img"``,
   a valid viewBox, ``<title>`` first and short, ``<desc>`` present,
   slug-prefixed unique ids, ``aria-labelledby`` naming both.
2. **Label geometry** — :func:`._labels.verify_svg_labels`: no text off the
   canvas, spilling out of its box, or on top of another label.
3. **Contrast** — :func:`muriel.contrast.audit_svg` at muriel's 8:1 floor,
   including text colored by presentation attributes and scored against
   the shape actually behind it. Text sitting on a curved filled path
   (whose colour under the glyphs the audit cannot compute) is reported
   as unverified, not passed.

Fail-closed. A file in which no text is found fails, and so does a file
whose text the contrast audit could not score: either means the checks
were blind, and a blind check that passes is worse than none. Pass
``--allow-no-text`` only for a glyph-only mark (a logomark with no
lettering) — the a11y lint still runs on it.

Exit: 0 clean, 1 findings, 2 usage (missing file).
"""

from __future__ import annotations

import io
import sys
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from pathlib import Path
from typing import Optional, Sequence, Union

from muriel.contrast import RENDER_8, audit_svg
from muriel.tools.diagrams._a11y import lint_a11y
from muriel.tools.diagrams._labels import verify_svg_labels

__all__ = ["check_svg"]


def _text_runs(svg_text: str) -> int:
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return 0
    n = 0
    for el in root.iter():
        tag = el.tag.split("}", 1)[-1] if isinstance(el.tag, str) else ""
        if tag in ("text", "tspan") and "".join(el.itertext()).strip():
            n += 1
    return n


def check_svg(
    path: Union[str, Path],
    *,
    allow_no_text: bool = False,
) -> list[str]:
    """Every finding for one SVG file, each prefixed with its check name."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    findings = [f"[a11y] {f}" for f in lint_a11y(text)]

    runs = _text_runs(text)
    if runs == 0:
        if not allow_no_text:
            findings.append(
                "[blind] no <text> found — the label and contrast checks "
                "read nothing, so they cannot pass (use --allow-no-text "
                "for a glyph-only mark)"
            )
        return findings

    try:
        report = verify_svg_labels(text)
    except ET.ParseError as exc:
        findings.append(f"[labels] could not parse: {exc}")
    else:
        findings += [f"[labels] collision: {c.a_text!r} overlaps {c.b_text!r}"
                     for c in report.collisions]
        findings += [f"[labels] off canvas: {o!r}" for o in report.overruns]
        findings += [f"[labels] spills out of its shape: {o!r}"
                     for o in report.overhangs]

    with redirect_stdout(io.StringIO()):
        entries = audit_svg(path, required=RENDER_8, print_table=False)
    scored = [e for e in entries if e.ratio is not None]
    if not scored:
        findings.append(
            f"[blind] {runs} text run(s) found but the contrast audit "
            f"scored none — their colors could not be resolved"
        )
    for e in scored:
        if e.unverified and e.passes is not None:
            findings.append(
                f"[contrast-unverified] text over a curved filled <path>; the "
                f"colour behind it is not computed — {e.selector_display}"
                + (f" (×{e.count})" if e.count > 1 else "")
            )
        if e.passes is False:
            findings.append(
                f"[contrast] {e.ratio:.2f}:1 < {RENDER_8:.0f}:1 — "
                f"{e.selector_display}"
                + (f" (×{e.count})" if e.count > 1 else "")
            )
    return findings


def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="muriel diagram-check",
        description="Accessible-figure lint, label geometry and 8:1 contrast "
                    "on rendered SVGs. Fails closed on SVGs with no text.",
    )
    ap.add_argument("svg", nargs="+", type=Path)
    ap.add_argument("--allow-no-text", action="store_true",
                    help="accept a glyph-only mark with no <text> "
                         "(a11y lint still runs)")
    args = ap.parse_args(argv)

    failed = 0
    for p in args.svg:
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2
        findings = check_svg(p, allow_no_text=args.allow_no_text)
        if findings:
            failed += 1
            print(f"FAIL  {p}")
            for f in findings:
                print(f"      {f}")
        else:
            print(f"ok    {p}")
    if failed:
        print(f"\n{failed} of {len(args.svg)} file(s) failed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
