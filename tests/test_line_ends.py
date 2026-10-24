"""
Tests for muriel.line_ends — the rendered line-end check.

One fixture holds every case side by side, so one browser launch checks
them all, and the assertion is the exact set of ends that float. A test
that only counted failures could pass with the wrong ends failing.

Cases that must land:
  * a connector touching a flat-filled node with no outline (muriel's
    diagrams draw nodes this way; anatomy's original check did not count
    a fill edge as a target);
  * an end under a fill painted after it;
  * a tick rooted at one end on an axis;
  * a leader stopping within TEXT_GAP of its label;
  * an arrow whose marker tip reaches the node the path stops short of;
  * gridlines stopping together at an unstroked plot edge (an implied
    edge, the fence rule);
  * ends marked data-free;
  * a rule running off the canvas edge.

Cases that must float:
  * a connector stopping 5 px short of an outlined node (a near miss, so
    it can never be excused by an implied edge);
  * a connector overshooting into a filled node drawn before it;
  * a tick with neither end rooted;
  * a leader 15 px short of its label;
  * an arrow whose marker tip stops 6.5 px short.

Skips when Playwright or its Chromium is absent.
Standard library only (unittest, no pytest dependency).
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muriel import line_ends as line_ends_module
from muriel.line_ends import FENCE, NEAR_MISS, TEXT_GAP, TOLERANCE, check


def _chromium_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as pw:
            pw.chromium.launch().close()
    except Exception:
        return False
    return True


HAS_CHROMIUM = _chromium_available()

# viewBox 600×400 drawn at 1200×800, so client px are 2× user units and
# the test proves gaps and positions come back in viewBox units.
FIXTURE = """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 600 400">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L10,5 L0,10 z" fill="#000"/>
    </marker>
  </defs>
  <rect width="600" height="400" fill="#fff"/>
  <g stroke="#000" stroke-width="1.5" fill="none">
    <!-- lands: flat-filled node to filled dot -->
    <rect x="20" y="20" width="60" height="40" fill="#333" stroke="none"/>
    <circle cx="170" cy="40" r="10" fill="#333" stroke="none"/>
    <line id="ok-flat" x1="80" y1="40" x2="160" y2="40"/>

    <!-- floats: 5 px short of an outlined node -->
    <rect x="20" y="100" width="60" height="40"/>
    <circle cx="170" cy="120" r="10" fill="#333" stroke="none"/>
    <path id="short" d="M 85 120 L 160 120"/>

    <!-- floats: overshoots into a filled node drawn first -->
    <rect x="200" y="20" width="60" height="40" fill="#333" stroke="none"/>
    <circle cx="310" cy="40" r="10" fill="#333" stroke="none"/>
    <line id="poke" x1="300" y1="40" x2="240" y2="40"/>

    <!-- lands: end tucked under a fill painted after it -->
    <circle cx="330" cy="120" r="10" fill="#333" stroke="none"/>
    <line id="tucked" x1="340" y1="120" x2="400" y2="120"/>
    <rect x="390" y="100" width="40" height="40" fill="#333" stroke="none"/>

    <!-- axis runs canvas edge to canvas edge; one rooted tick, one not -->
    <line id="axis" x1="0" y1="250" x2="600" y2="250"/>
    <line id="tick-ok" x1="100" y1="250" x2="100" y2="256"/>
    <line id="tick-float" x1="150" y1="270" x2="150" y2="276"/>

    <!-- leaders: one within the text gap, one far short -->
    <circle cx="360" cy="300" r="6" fill="#333" stroke="none"/>
    <line id="leader-ok" x1="366" y1="300" x2="418" y2="300"/>
    <circle cx="360" cy="340" r="6" fill="#333" stroke="none"/>
    <line id="leader-far" x1="366" y1="340" x2="405" y2="340"/>

    <!-- arrows: tip reaches the node, and tip stops short -->
    <rect x="540" y="20" width="40" height="40"/>
    <circle cx="480" cy="40" r="6" fill="#333" stroke="none"/>
    <path id="arrow-ok" d="M 486 40 L 538 40" marker-end="url(#arrow)"/>
    <rect x="540" y="100" width="40" height="40"/>
    <circle cx="480" cy="120" r="6" fill="#333" stroke="none"/>
    <path id="arrow-short" d="M 486 120 L 532 120" marker-end="url(#arrow)"/>

    <!-- gridlines from the canvas edge, stopping at an unstroked plot edge -->
    <line id="g1" x1="0" y1="300" x2="180" y2="300"/>
    <line id="g2" x1="0" y1="320" x2="180" y2="320"/>
    <line id="g3" x1="0" y1="340" x2="180" y2="340"/>
    <line id="g4" x1="0" y1="360" x2="180" y2="360"/>

    <!-- meant to stop -->
    <path id="free" d="M 450 200 L 520 200" data-free=""/>
    <circle cx="450" cy="170" r="6" fill="#333" stroke="none"/>
    <line id="free-end" x1="456" y1="170" x2="520" y2="170" data-free="end"/>
  </g>
  <g fill="#000" font-family="sans-serif" font-size="16">
    <text x="420" y="305">Label</text>
    <text x="420" y="345">Label</text>
  </g>
</svg>
"""

EXPECTED = {
    ("short", "start"),
    ("poke", "end"),
    ("tick-float", "start"),
    ("tick-float", "end"),
    ("leader-far", "end"),
    ("arrow-short", "end"),
}


def _id_of(what: str) -> str:
    # describe() writes "<tag>#<id>[ in <owner>]".
    return what.split("#", 1)[1].split(" ", 1)[0] if "#" in what else what


class ConstantsTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(TOLERANCE, 1.0)
        self.assertGreater(TEXT_GAP, TOLERANCE)
        self.assertGreater(NEAR_MISS, TOLERANCE)
        self.assertGreaterEqual(FENCE, 3)

    def test_missing_file_is_a_usage_error(self):
        self.assertEqual(line_ends_module._main(["/nonexistent/figure.svg"]), 2)


@unittest.skipUnless(HAS_CHROMIUM, "Playwright Chromium not installed")
class LineEndsRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.fixture = cls.tmp / "fixture.svg"
        cls.fixture.write_text(FIXTURE, encoding="utf-8")
        cls.report = check(cls.fixture)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_exactly_the_expected_ends_float(self):
        got = {(_id_of(p.what), p.end) for p in self.report.problems}
        self.assertEqual(got, EXPECTED)

    def test_gridlines_pass_on_an_implied_edge(self):
        self.assertGreaterEqual(self.report.implied, 4)

    def test_positions_and_gaps_are_in_viewbox_units(self):
        short = next(p for p in self.report.problems if _id_of(p.what) == "short")
        self.assertAlmostEqual(short.at[0], 85, delta=0.2)
        self.assertAlmostEqual(short.at[1], 120, delta=0.2)
        # The outline's centreline is at x=80: 5 viewBox px, not 10 client px.
        self.assertAlmostEqual(short.gap, 5, delta=0.3)

    def test_free_ends_are_not_counted(self):
        # 17 open strokes in the fixture, 3 free ends among them; closed
        # shapes and filled shapes contribute none.
        self.assertEqual(self.report.lines, 17)
        self.assertEqual(self.report.ends, 17 * 2 - 3)

    def test_blind_check_fails_closed(self):
        blank = self.tmp / "blank.svg"
        blank.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">'
            '<rect x="10" y="10" width="80" height="40" fill="#333"/></svg>',
            encoding="utf-8",
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(line_ends_module._main([str(blank)]), 1)
            self.assertEqual(line_ends_module._main([str(blank), "--allow-none"]), 0)
        self.assertIn("[blind]", buf.getvalue())

    def test_lines_selector_and_json(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = line_ends_module._main([str(self.fixture), "--lines", "#short", "--json"])
        self.assertEqual(code, 1)
        report = json.loads(buf.getvalue())
        self.assertEqual(report["lines"], 1)
        self.assertEqual(report["floating"], 1)
        self.assertEqual(report["problems"][0]["end"], "start")


if __name__ == "__main__":
    unittest.main()
