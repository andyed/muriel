"""
muriel.line_ends — fail any stroke that ends in mid-air.

Loads an SVG or HTML page in headless Chromium and checks every open end
of every checked stroke against the drawing the browser actually paints.
An end passes when it lands within ``tolerance`` viewBox px of another
stroke, a shape's outline, a dot, a text label (within ``text_gap``), or
the canvas edge; when a fill painted after it covers it; or when at least
``fence`` other ends arrive square-on to the same vertical or horizontal
line, the way gridlines stop at an unstroked plot edge. A near miss,
anything within ``near_miss`` px, is never excused that way: it is the
defect itself, and a generator that repeats it at every node would
otherwise excuse its own bug.
A short straight mark (a tick, up to 7 px) needs only one end rooted.

Created because a connector that stops 2 px short of its node, a
leader that misses its mark, or a gridline that overshoots the plot all
read as touching at 1×. The eye closes the gap. A rendered check does
not, and unlike a reviewer it checks every end. The Loupe jury seat
judges the same faults by eye on rasters; on SVG and HTML this check is
a finding of fact and is stipulated before the panel sits
(``references/jury.md#jurisdiction``).

Ported from anatomy's ``scripts/line-ends.mjs``
(github.com/wheresryan22/anatomy, MIT). The in-page half lives in
``line_ends.js`` beside this module, with a header that lists what
muriel changed and why. The license is in ``THIRD_PARTY_NOTICES.md``.

Marking an end that is meant to stop
------------------------------------

``data-free`` on the element: bare or ``"both"`` frees both ends,
``"start"`` or ``"end"`` one. Use it for a needle tip, a pointer, a rule
standing in for text. The same attribute anatomy uses, so its figures
check unchanged.

What is checked
---------------

By default, every stroked, unfilled ``path``, ``line`` and ``polyline``
outside ``defs``, markers, clip paths, masks, patterns and symbols, at
opacity 0.3 or more. ``lines=`` (``--lines``) replaces that with a CSS
selector, for example ``.iso-line`` on an anatomy figure. ``root=``
(``--root``) limits the check to one element of a page.

Usage
-----

.. code-block:: python

    from muriel.line_ends import check
    report = check("figure.svg")
    report.problems            # [] when every end lands

.. code-block:: bash

    python -m muriel.line_ends figure.svg
    python -m muriel.line_ends page.html --root '#fig-2' --out ends.png
    python -m muriel.line_ends figure.svg --json

Exit status:
    0 = every end lands
    1 = an end floats, or nothing was checked (``--allow-none`` for a
        figure with no lines; a check that read nothing did not pass)
    2 = usage error (file not found)
    4 = Playwright or its Chromium missing

Limitations
-----------

- Static. It checks the page as loaded; an animation frame, a hover
  state or a theme needs its own run (load that state, then call
  ``check`` on it, or point ``--root`` at a pre-posed copy).
- Text targets use the text element's bounding box, so a leader that
  lands in a label's line gap or past a short last line still passes.
- Implied edges are axis-aligned only. Ends that line up on a diagonal
  do not fence each other.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence, Union

__all__ = [
    "TOLERANCE",
    "TEXT_GAP",
    "FENCE",
    "NEAR_MISS",
    "LineEndProblem",
    "LineEndsReport",
    "check",
]

#: How close, in viewBox px, an end must come to something to land.
TOLERANCE: float = 1.0

#: Padding a leader may leave before its label's bounding box.
TEXT_GAP: float = 4.0

#: Ends from other lines that must share an axis-aligned line with an end
#: for it to count as stopping on an implied edge.
FENCE: int = 3

#: An end this close to something (but not within ``TOLERANCE``) is a
#: near miss and can never pass on an implied edge.
NEAR_MISS: float = 6.0

#: Viewport cap, so a runaway page cannot ask for a 40k px screenshot.
_MAX_VIEWPORT_PX: int = 4096

_SCRIPT = Path(__file__).with_name("line_ends.js")


@dataclass
class LineEndProblem:
    """One floating end. ``at`` is in the owning SVG's user units."""
    what: str
    end: str
    gap: Optional[float]   # viewBox px to the nearest target; None = nothing in reach
    at: tuple[float, float]
    client: tuple[float, float]
    mark: bool
    length: float
    opacity: float
    d: str = ""

    def to_dict(self) -> dict:
        return {
            "what": self.what,
            "end": self.end,
            "gap": self.gap,
            "at": list(self.at),
            "mark": self.mark,
            "length": self.length,
            "opacity": self.opacity,
            "d": self.d,
        }


@dataclass
class LineEndsReport:
    source: str
    ends: int
    lines: int
    implied: int
    problems: list[LineEndProblem] = field(default_factory=list)
    marks_path: Optional[Path] = None

    @property
    def blind(self) -> bool:
        """True when no end was checked, so the check saw nothing."""
        return self.ends == 0

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "ends": self.ends,
            "lines": self.lines,
            "implied": self.implied,
            "floating": len(self.problems),
            "problems": [p.to_dict() for p in self.problems],
            "marks": str(self.marks_path) if self.marks_path else None,
        }


def _require_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ImportError(
            "muriel.line_ends requires Playwright and its Chromium:\n"
            "    pip install playwright\n"
            "    playwright install chromium"
        ) from exc
    return sync_playwright


def _target_url(target: Union[str, Path]) -> str:
    text = str(target)
    if "://" in text:
        return text
    path = Path(text).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"no such file: {path}")
    return path.as_uri()


def _ring(screenshot: Path, problems: Sequence[LineEndProblem], scale: int) -> None:
    """Ring each floating end on the screenshot. Skipped without Pillow."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return
    with Image.open(str(screenshot)) as raw:
        img = raw.convert("RGB")
    draw = ImageDraw.Draw(img)
    radius = 6 * scale
    for problem in problems:
        x, y = problem.client[0] * scale, problem.client[1] * scale
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            outline=(255, 0, 80), width=max(2, scale),
        )
    img.save(str(screenshot))


def check(
    target: Union[str, Path],
    *,
    root: Optional[str] = None,
    lines: Optional[str] = None,
    tolerance: float = TOLERANCE,
    text_gap: float = TEXT_GAP,
    fence: int = FENCE,
    near_miss: float = NEAR_MISS,
    width: Optional[int] = None,
    height: Optional[int] = None,
    out: Optional[Union[str, Path]] = None,
    scale: int = 2,
) -> LineEndsReport:
    """
    Check every open stroke end in one SVG or HTML page.

    Parameters
    ----------
    target
        An ``.svg`` or ``.html`` path, or a URL.
    root
        CSS selector for the element to check (default: the whole page).
    lines
        CSS selector for the strokes to check, replacing the default of
        every stroked, unfilled path, line and polyline.
    tolerance, text_gap, fence, near_miss
        See the module constants.
    width, height
        Viewport size. Default: fit the page, capped at 4096 px.
    out
        Write a screenshot at ``scale``× with each floating end ringed.

    Raises
    ------
    ImportError
        Playwright missing.
    FileNotFoundError
        Target path missing.
    """
    sync_playwright = _require_playwright()
    url = _target_url(target)
    script = _SCRIPT.read_text(encoding="utf-8")
    options = {
        "root": root,
        "lines": lines,
        "tolerance": tolerance,
        "textGap": text_gap,
        "fence": fence,
        "nearMiss": near_miss,
    }

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as exc:  # Playwright raises its own Error type
            raise ImportError(
                f"Chromium for Playwright is not installed ({exc}). "
                "Run:  playwright install chromium"
            ) from exc
        try:
            page = browser.new_page(
                viewport={"width": width or 1280, "height": height or 1024},
                device_scale_factor=scale,
            )
            page.goto(url, wait_until="load")
            page.evaluate("document.fonts ? document.fonts.ready.then(() => true) : true")
            if width is None or height is None:
                # Fit the viewport to the drawing, so every end is on
                # screen: elementsFromPoint cannot see an off-screen fill.
                # A standalone SVG's scroll size is the viewport's, so
                # only its own box says how big the drawing is.
                size = page.evaluate(
                    """() => {
                        const el = document.documentElement;
                        const r = el.getBoundingClientRect();
                        if (el instanceof SVGSVGElement)
                            return [Math.ceil(r.width), Math.ceil(r.height)];
                        return [Math.ceil(Math.max(r.width, el.scrollWidth)),
                                Math.ceil(Math.max(r.height, el.scrollHeight))];
                    }"""
                )
                page.set_viewport_size({
                    "width": width or max(64, min(_MAX_VIEWPORT_PX, size[0])),
                    "height": height or max(64, min(_MAX_VIEWPORT_PX, size[1])),
                })
            raw = page.evaluate(script, options)
            report = LineEndsReport(
                source=url,
                ends=raw["ends"],
                lines=raw["lines"],
                implied=raw["implied"],
                problems=[
                    LineEndProblem(
                        what=p["what"],
                        end=p["end"],
                        gap=p["gap"],
                        at=tuple(p["at"]),
                        client=tuple(p["client"]),
                        mark=p["mark"],
                        length=p["length"],
                        opacity=p["opacity"],
                        d=p.get("d", ""),
                    )
                    for p in raw["problems"]
                ],
            )
            if out is not None:
                out_path = Path(out).expanduser().resolve()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                # The viewport already fits the page. full_page hangs on a
                # standalone SVG document in Chromium, and is not needed.
                page.screenshot(path=str(out_path), timeout=30000)
                _ring(out_path, report.problems, scale)
                report.marks_path = out_path
        finally:
            browser.close()
    return report


def _print_report(report: LineEndsReport) -> None:
    print(f"\nLine ends: {report.source}")
    print(f"  checked:  {report.ends} ends on {report.lines} lines"
          f"  ({report.implied} on implied edges)")
    if report.blind:
        print("  [blind] no open line ends found; the check read nothing")
    print(f"  floating: {len(report.problems)}")
    for p in report.problems:
        gap = f"{p.gap:.2f} px" if p.gap is not None else "nothing in reach"
        kind = "mark" if p.mark else "line"
        print(f"    {p.what}  {p.end} of {kind} ({p.length} px)  "
              f"at {p.at[0]},{p.at[1]}  gap {gap}"
              + (f"  d {p.d}…" if p.d else ""))
    if report.marks_path:
        print(f"  marks:    {report.marks_path}")
    print()


def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m muriel.line_ends",
        description=(
            "Fail any stroke whose end lands on nothing, checked against "
            "the drawing headless Chromium renders."
        ),
    )
    parser.add_argument("target", help="SVG or HTML file, or a URL.")
    parser.add_argument("--root", default=None, help="CSS selector of the element to check.")
    parser.add_argument("--lines", default=None,
                        help="CSS selector of the strokes to check (default: stroked, unfilled paths/lines/polylines).")
    parser.add_argument("--tolerance", type=float, default=TOLERANCE,
                        help=f"Landing distance in viewBox px (default {TOLERANCE}).")
    parser.add_argument("--text-gap", type=float, default=TEXT_GAP,
                        help=f"Padding a leader may leave before a label (default {TEXT_GAP}).")
    parser.add_argument("--fence", type=int, default=FENCE,
                        help=f"Aligned ends that form an implied edge; 0 disables (default {FENCE}).")
    parser.add_argument("--width", type=int, default=None, help="Viewport width (default: fit).")
    parser.add_argument("--height", type=int, default=None, help="Viewport height (default: fit).")
    parser.add_argument("--out", type=Path, default=None, help="Write a ringed screenshot here.")
    parser.add_argument("--allow-none", action="store_true",
                        help="Pass a figure that has no open line ends at all.")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    args = parser.parse_args(argv)

    try:
        report = check(
            args.target,
            root=args.root,
            lines=args.lines,
            tolerance=args.tolerance,
            text_gap=args.text_gap,
            fence=args.fence,
            width=args.width,
            height=args.height,
            out=args.out,
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        _print_report(report)
    if report.problems:
        return 1
    if report.blind and not args.allow_none:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
