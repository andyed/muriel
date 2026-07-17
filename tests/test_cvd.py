"""
Tests for muriel.cvd and muriel.palettes.validate — the CVD-separation
checks contrast.py structurally cannot make. Standard library only
(unittest, no pytest dependency).

The load-bearing claims under test:

  * Machado-2009 simulation + CIE76 ΔE reproduce the sibling dataviz
    validator's numbers (independent cross-check of the color math).
  * kind=None means NORMAL vision in both delta_e and min_separation
    (the overload bug that once made the CLI print deutan's number).
  * validate() gates on separation + a role-aware contrast floor, and
    runs NEITHER the lightness band NOR the chroma gate the siblings do —
    because ported to muriel's surfaces they reject muriel's own output.
"""

from __future__ import annotations

import unittest

from muriel.cvd import (
    CVD_FLOOR,
    CVD_TARGET,
    CVD_KINDS,
    Separation,
    delta_e,
    min_separation,
    separation_matrix,
    simulate,
    worst_separation,
)
from muriel.contrast import contrast_ratio
from muriel.palettes import WONG, TOL_BRIGHT, generate_for_floor, validate


class TestSimulation(unittest.TestCase):
    def test_achromatic_anchors_unmoved(self):
        for kind in CVD_KINDS:
            self.assertEqual(simulate("#000000", kind), (0, 0, 0))
            r, g, b = simulate("#ffffff", kind)
            self.assertTrue(all(c >= 253 for c in (r, g, b)))

    def test_simulate_rejects_bad_kind(self):
        with self.assertRaises(ValueError):
            simulate("#ff0000", "monochrome")

    def test_accepts_hex_and_rgb_triple(self):
        self.assertEqual(simulate((0, 0, 0), "deutan"), simulate("#000000", "deutan"))


class TestDeltaE(unittest.TestCase):
    def test_identity_is_zero(self):
        for kind in (None,) + CVD_KINDS:
            self.assertLess(delta_e("#D55E00", "#D55E00", kind), 1e-9)

    def test_symmetry(self):
        self.assertAlmostEqual(
            delta_e("#000000", "#ffffff"), delta_e("#ffffff", "#000000"), places=9
        )

    def test_black_white_is_lstar_range(self):
        # CIE76 black↔white ΔE is the L* range, 100.
        self.assertAlmostEqual(delta_e("#000000", "#ffffff"), 100.0, delta=0.5)

    def test_parse_equivalence(self):
        self.assertAlmostEqual(
            delta_e("#4477AA", (238, 102, 119)),
            delta_e((68, 119, 170), "#EE6677"),
            places=9,
        )


class TestCrossValidation(unittest.TestCase):
    """The sibling dataviz validator reports Wong's worst ADJACENT pair as
    deutan ΔE 48.9, tritan 16.1, normal 59.5. Muriel must land on the same
    numbers (small rounding differences from exact-vs-approx CIE constants)."""

    def test_wong_adjacent_matches_reference(self):
        normal = min_separation(WONG, None, pairs="adjacent")
        deutan = min_separation(WONG, "deutan", pairs="adjacent")
        tritan = min_separation(WONG, "tritan", pairs="adjacent")
        self.assertAlmostEqual(normal.delta, 59.5, delta=0.3)
        self.assertAlmostEqual(deutan.delta, 48.9, delta=0.3)
        self.assertAlmostEqual(tritan.delta, 16.1, delta=0.3)


class TestKindNoneMeansNormal(unittest.TestCase):
    """Regression: kind=None must mean normal vision in min_separation, the
    same as in delta_e — not 'search protan+deutan'. The overload once made
    the CLI's 'normal' row silently print deutan's number."""

    def test_min_separation_none_is_normal_vision(self):
        pair = ["#56B4E9", "#009E73"]
        normal = min_separation(pair)
        self.assertIsNone(normal.kind)
        self.assertAlmostEqual(normal.delta, delta_e(*pair), places=9)
        # Normal separation exceeds the CVD-simulated separation for this pair.
        self.assertGreater(normal.delta, min_separation(pair, "deutan").delta)

    def test_worst_separation_searches_cvd_kinds(self):
        w = worst_separation(WONG)
        self.assertIn(w.kind, ("protan", "deutan"))
        # Never optimistic: no better than any kind it searched.
        for k in ("protan", "deutan"):
            self.assertLessEqual(w.delta, min_separation(WONG, k).delta + 1e-9)


class TestSeparationBookkeeping(unittest.TestCase):
    def test_degenerate_palettes(self):
        self.assertIsNone(min_separation(["#ffffff"]))
        self.assertIsNone(min_separation([]))
        self.assertIsNone(worst_separation(["#ffffff"]))

    def test_adjacent_is_subset_of_all(self):
        p = ["#4477AA", "#EE6677", "#228833", "#CCBB44"]
        self.assertGreaterEqual(
            min_separation(p, "deutan", pairs="adjacent").delta,
            min_separation(p, "deutan", pairs="all").delta - 1e-9,
        )

    def test_matrix_sorted_ascending(self):
        p = ["#4477AA", "#EE6677", "#228833", "#CCBB44"]
        deltas = [d for _, _, d in separation_matrix(p, "deutan")]
        self.assertEqual(deltas, sorted(deltas))

    def test_separation_status_bands(self):
        self.assertEqual(Separation(20, "deutan", "#a", "#b", 0, 1).status, "pass")
        self.assertEqual(Separation(10, "deutan", "#a", "#b", 0, 1).status, "floor")
        self.assertEqual(Separation(3, "deutan", "#a", "#b", 0, 1).status, "fail")


class TestValidate(unittest.TestCase):
    def test_wong_passes_on_its_own_paper(self):
        # Wong is THE colorblind-safe reference; it must pass on white paper,
        # black slot and all. A validator that fails Wong here is broken.
        self.assertTrue(validate(WONG, bg="#fffff8").ok)

    def test_wong_black_slot_warns_on_oled(self):
        # #000000 is invisible on near-black (1.06:1) — warns as a mark, does
        # not silently pass, and is NOT hard-failed for lacking a hue.
        report = validate(WONG, bg="#0a0a0f")
        contrast = [c for c in report.checks if c.name == "Contrast vs surface"][0]
        self.assertEqual(contrast.status, "warn")
        self.assertIn("#000000", contrast.detail)

    def test_mode_follows_surface(self):
        self.assertEqual(validate(WONG, bg="#0a0a0f").mode, "dark")
        self.assertEqual(validate(WONG, bg="#fffff8").mode, "light")

    def test_cvd_collapse_caught_when_contrast_passes(self):
        # The reason the module exists: two hues clearing the 8:1 TEXT floor on
        # near-black, collapsing for a deuteranope. contrast.py sees two PASSes.
        pink, teal = "#ff78af", "#00bfa8"
        for c in (pink, teal):
            self.assertGreaterEqual(contrast_ratio(c, "#0a0a0f"), 8.0)
        report = validate([pink, teal], bg="#0a0a0f")
        cvd = [c for c in report.checks if c.name == "CVD separation"][0]
        self.assertEqual(cvd.status, "fail")
        self.assertFalse(report.ok)

    def test_text_floor_is_hard_mark_floor_has_relief(self):
        # A color below 3:1 as a MARK warns (relief available); the SAME color
        # as TEXT hard-fails at muriel's 8:1 floor, which has no relief valve.
        near = ["#0a0a10", "#EE6677"]
        mark = [c for c in validate(near, bg="#0a0a0f").checks
                if c.name == "Contrast vs surface"][0]
        self.assertEqual(mark.status, "warn")
        text = [c for c in validate(near, bg="#0a0a0f", as_text=True).checks
                if c.name == "Contrast vs surface"][0]
        self.assertEqual(text.status, "fail")

    def test_no_chroma_gate_gray_judged_by_separation(self):
        # A well-separated gray-first pair passes; a gray only fails when it
        # actually collapses into a neighbour (protan darkens #EE6677 → #888).
        self.assertTrue(validate(["#bbbbbb", "#ffa07a"], bg="#0a0a0f").ok)
        self.assertFalse(validate(["#888888", "#EE6677"], bg="#0a0a0f").ok)

    def test_no_lightness_band_generator_output_clears_contrast(self):
        # generate_for_floor emits AT the 8:1 floor; validate's contrast check
        # must find it clean. A foreign lightness band would reject it wholesale.
        gen = generate_for_floor("#0a0a0f", floor=8.0, n=6)
        contrast = [c for c in validate(gen, bg="#0a0a0f", as_text=True).checks
                    if c.name == "Contrast vs surface"][0]
        self.assertEqual(contrast.status, "pass")

    def test_generator_and_validator_are_complementary(self):
        # The generator does NOT check CVD — its evenly-spaced hues can collapse.
        # validate() is exactly the complement that catches it.
        gen = generate_for_floor("#0a0a0f", floor=8.0, n=6)
        cvd = [c for c in validate(gen, bg="#0a0a0f").checks
               if c.name == "CVD separation"][0]
        self.assertIn(cvd.status, ("warn", "fail"))

    def test_empty_palette_raises(self):
        with self.assertRaises(ValueError):
            validate([], bg="#0a0a0f")

    def test_report_truthiness_tracks_ok(self):
        good = validate(WONG, bg="#fffff8")
        self.assertEqual(bool(good), good.ok)
        self.assertTrue(all(c.status != "fail" for c in good.checks) == good.ok)

    def test_tol_bright_grey_slot_not_rejected_for_being_gray(self):
        # Tol Bright ships #BBBBBB; on the paper it targets it must not be
        # rejected simply for low chroma.
        self.assertIn("#BBBBBB", TOL_BRIGHT)
        report = validate(TOL_BRIGHT, bg="#fffff8")
        # It may warn/fail on separation or contrast, but never on a chroma gate
        # (there is no such check).
        self.assertFalse(any(c.name == "Chroma floor" for c in report.checks))


class TestSelftests(unittest.TestCase):
    def test_cvd_selftest(self):
        from muriel.cvd import _selftest
        self.assertEqual(_selftest(), 0)

    def test_palettes_selftest(self):
        from muriel.palettes import _selftest
        self.assertEqual(_selftest(), 0)


if __name__ == "__main__":
    unittest.main()
