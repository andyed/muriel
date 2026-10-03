"""
Tests for muriel.contrast.repair_text_pair — same-hue lightness repair of
a failing text/background pair. Standard library only (unittest).

The four failing pairs below come from the bergside/awesome-design-skills
DESIGN.md registry (MIT): two dark themes that kept a near-black text
token, a grey-on-grey mono theme, and orange text on cream.
"""

from __future__ import annotations

import io
import random
import unittest
from contextlib import redirect_stdout

from muriel.contrast import (
    RENDER_8,
    WCAG_AA,
    _main,
    contrast_ratio,
    repair_text_pair,
)
from muriel.oklch import clamp_to_srgb, oklch_to_rgb, rgb_to_oklch


CORPUS_FAILURES = [
    # (slug, text, surface)
    ("bold", "#111827", "#111111"),
    ("pacman", "#111827", "#000000"),
    ("mono", "#78716B", "#E7E5E4"),
    ("pulse", "#EA580C", "#FFEDD5"),
]


class RepairFindsPassingColour(unittest.TestCase):

    def test_corpus_failures_all_repair_to_floor(self):
        for slug, fg, bg in CORPUS_FAILURES:
            with self.subTest(slug=slug):
                self.assertLess(contrast_ratio(fg, bg), RENDER_8)
                r = repair_text_pair(fg, bg)
                self.assertIn(r.direction, ("dark", "light"))
                self.assertIsNotNone(r.repaired)
                # Scored on the rounded 8-bit colour, so this is the
                # colour a caller would actually write.
                self.assertGreaterEqual(contrast_ratio(r.hex, bg), RENDER_8)
                self.assertAlmostEqual(r.ratio_after,
                                       contrast_ratio(r.hex, bg), places=9)

    def test_dark_surface_goes_lighter(self):
        r = repair_text_pair("#111827", "#111111")
        self.assertEqual(r.direction, "light")
        self.assertGreater(r.L_after, r.L_before)

    def test_light_surface_goes_darker(self):
        r = repair_text_pair("#EA580C", "#FFEDD5")
        self.assertEqual(r.direction, "dark")
        self.assertLess(r.L_after, r.L_before)

    def test_hue_held(self):
        r = repair_text_pair("#EA580C", "#FFEDD5")
        self.assertIsNotNone(r.hue_shift)
        self.assertLess(r.hue_shift, 1.0)

    def test_respects_required(self):
        r = repair_text_pair("#EA580C", "#FFEDD5", required=WCAG_AA)
        self.assertGreaterEqual(r.ratio_after, WCAG_AA)
        self.assertLess(r.ratio_after, RENDER_8)


class RepairIsMinimal(unittest.TestCase):
    """The repaired colour sits at the floor, not past it."""

    def test_one_step_back_toward_source_fails(self):
        for slug, fg, bg in CORPUS_FAILURES:
            with self.subTest(slug=slug):
                r = repair_text_pair(fg, bg)
                src = rgb_to_oklch(r.fg)
                back = 0.01 if r.direction == "dark" else -0.01
                nearer = oklch_to_rgb(clamp_to_srgb(src.replace(L=r.L_after + back)))
                self.assertLess(contrast_ratio(nearer, bg), RENDER_8)

    def test_no_large_overshoot(self):
        for slug, fg, bg in CORPUS_FAILURES:
            with self.subTest(slug=slug):
                self.assertLess(repair_text_pair(fg, bg).ratio_after, RENDER_8 + 0.25)


class RepairEdgeCases(unittest.TestCase):

    def test_passing_pair_returned_unchanged(self):
        r = repair_text_pair("#e6e4d2", "#0a0a0f")
        self.assertEqual(r.direction, "none")
        self.assertEqual(r.hex, "#e6e4d2")

    def test_mid_grey_background_is_unreachable(self):
        # Black and white both stop short of 8:1 on #777777, so no text
        # colour of any hue can pass; the background has to move.
        r = repair_text_pair("#ff0000", "#777777")
        self.assertEqual(r.direction, "unreachable")
        self.assertIsNone(r.repaired)
        self.assertIsNone(r.hex)
        self.assertLess(r.max_ratio, RENDER_8)
        self.assertIn("move the background", str(r))

    def test_forced_direction_can_be_unreachable(self):
        # Lightening orange on cream can never reach 8:1.
        r = repair_text_pair("#EA580C", "#FFEDD5", direction="light")
        self.assertEqual(r.direction, "unreachable")

    def test_exact_grey_stays_grey(self):
        # Bisection lands where 8-bit rounding flips; unguarded, the
        # channels rounded apart and #737373 came back #515051.
        for grey in ("#737373", "#7e7e7e", "#757575", "#959595", "#111111"):
            for bg in ("#ffffff", "#000000", "#f5f5f5"):
                with self.subTest(grey=grey, bg=bg):
                    r = repair_text_pair(grey, bg)
                    if r.repaired is not None:
                        self.assertEqual(len(set(r.repaired)), 1, r.hex)

    def test_grey_input_reports_no_hue_shift(self):
        r = repair_text_pair("#78716B", "#E7E5E4")
        self.assertIsNone(r.hue_shift)

    def test_bad_direction_raises(self):
        with self.assertRaises(ValueError):
            repair_text_pair("#000", "#fff", direction="up")

    def test_transparent_raises(self):
        with self.assertRaises(ValueError):
            repair_text_pair("transparent", "#fff")


class RepairSweep(unittest.TestCase):
    """Random pairs: every result either passes or is honestly unreachable."""

    def test_random_pairs(self):
        rng = random.Random(20261002)
        n_repaired = n_unreachable = 0
        for _ in range(300):
            fg = tuple(rng.randrange(256) for _ in range(3))
            bg = tuple(rng.randrange(256) for _ in range(3))
            r = repair_text_pair(fg, bg)
            if r.direction == "unreachable":
                n_unreachable += 1
                self.assertLess(contrast_ratio((0, 0, 0), bg), RENDER_8)
                self.assertLess(contrast_ratio((255, 255, 255), bg), RENDER_8)
            else:
                n_repaired += 1
                self.assertGreaterEqual(contrast_ratio(r.repaired, bg), RENDER_8)
        # Both branches must actually be exercised, or the sweep proves nothing.
        self.assertGreater(n_repaired, 0)
        self.assertGreater(n_unreachable, 0)


class RepairCli(unittest.TestCase):

    def _run(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = _main(argv)
        return code, buf.getvalue()

    def test_repair_exit_zero_and_prints_hex(self):
        code, out = self._run(["--repair", "#EA580C", "#FFEDD5"])
        self.assertEqual(code, 0)
        self.assertIn("→ #", out)

    def test_unreachable_exit_one(self):
        code, out = self._run(["--repair", "#ff0000", "#777777"])
        self.assertEqual(code, 1)
        self.assertIn("unreachable", out)

    def test_required_flag_threads_through(self):
        code, out = self._run(["--repair", "#EA580C", "#FFEDD5", "--required", "4.5"])
        self.assertEqual(code, 0)
        self.assertIn("4.50:1", out)


if __name__ == "__main__":
    unittest.main()
