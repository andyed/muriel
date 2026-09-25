"""
Tests for muriel.motion — the duration binary plus the Emil-inspired
property / easing / scale axes, and the figure-motion contract (mode,
flash rate, sequence shape). Standard library only (unittest).

The module ships a thorough ``_selftest``; this wrapper folds it into the
``python -m unittest`` suite and pins the deliberate divergences from the
upstream source (duration binary over bands; 0.96 press scale over 0.97).
"""

from __future__ import annotations

import unittest

from muriel import motion
from muriel.motion import (
    CINEMATIC_MS,
    COMPOSITOR_SAFE_PROPERTIES,
    ENTRANCE_SCALE_FLOOR,
    LAYOUT_TRIGGERING_PROPERTIES,
    PRESS_SCALE,
    UTILITY_MS,
    LOOP_MIN_CYCLE_MS,
    MotionPolicyError,
    MotionPropertyError,
    easing_for,
    is_compositor_safe,
    validate_duration,
    validate_flash_rate,
    validate_mode,
    validate_properties,
    validate_scale,
    validate_sequence_shape,
)


class SelfTest(unittest.TestCase):
    def test_module_selftest_passes(self):
        self.assertEqual(motion._selftest(), 0)


class PropertyAxis(unittest.TestCase):
    def test_safe_and_layout_sets_disjoint(self):
        self.assertFalse(COMPOSITOR_SAFE_PROPERTIES & LAYOUT_TRIGGERING_PROPERTIES)

    def test_compositor_safe(self):
        self.assertTrue(is_compositor_safe("transform"))
        self.assertTrue(is_compositor_safe("-webkit-transform"))
        self.assertFalse(is_compositor_safe("height"))

    def test_layout_property_raises(self):
        with self.assertRaises(MotionPropertyError):
            validate_properties(["transform", "top"])

    def test_unknown_property_passes(self):
        validate_properties("color")  # not assumed unsafe


class EasingAxis(unittest.TestCase):
    def test_directions(self):
        self.assertEqual(easing_for("enter"), "ease-out")
        self.assertEqual(easing_for("exit"), "ease-in")
        self.assertEqual(easing_for("move"), "ease-in-out")

    def test_unknown_direction_raises(self):
        with self.assertRaises(ValueError):
            easing_for("diagonal")


class ScaleAxis(unittest.TestCase):
    def test_floor_and_identity_pass(self):
        validate_scale(ENTRANCE_SCALE_FLOOR)
        validate_scale(1.0)
        validate_scale(PRESS_SCALE, "press")

    def test_below_floor_and_overshoot_raise(self):
        for bad in (0.0, 0.9, 1.1):
            with self.assertRaises(ValueError):
                validate_scale(bad)


class DeliberateDivergences(unittest.TestCase):
    """muriel intentionally departs from the upstream source on two points."""

    def test_press_scale_is_muriels_096_not_097(self):
        self.assertEqual(PRESS_SCALE, 0.96)

    def test_emil_duration_bands_are_uncanny_to_muriel(self):
        # The source recommends 100–500ms bands; muriel's binary forbids them.
        for band_ms in (160, 250, 360, 500):
            with self.assertRaises(motion.MotionPolicyError):
                validate_duration(band_ms)
        # muriel's own buckets still pass.
        validate_duration(UTILITY_MS)
        validate_duration(CINEMATIC_MS)


class ModeContract(unittest.TestCase):
    """none / reveal / step / loop — adapted from diagram-design (MIT)."""

    def test_reveal_autoplays_once(self):
        validate_mode("reveal", autoplay=True, repeats=False, semantic=True)

    def test_reveal_must_not_repeat(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("reveal", autoplay=True, repeats=True, semantic=True)

    def test_step_must_not_autoplay(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("step", autoplay=True, repeats=False, semantic=True)

    def test_step_user_driven_passes(self):
        validate_mode("step", autoplay=False, repeats=False, semantic=True)

    def test_semantic_loop_rejected(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("loop", autoplay=True, repeats=True, semantic=True,
                          cycle_ms=3000)

    def test_loop_cycle_floor(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("loop", autoplay=True, repeats=True, semantic=False,
                          cycle_ms=LOOP_MIN_CYCLE_MS - 1)
        validate_mode("loop", autoplay=True, repeats=True, semantic=False,
                      cycle_ms=LOOP_MIN_CYCLE_MS)

    def test_loop_without_cycle_rejected(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("loop", autoplay=True, repeats=True, semantic=False)

    def test_none_is_inert(self):
        validate_mode("none", autoplay=False, repeats=False, semantic=True)
        with self.assertRaises(MotionPolicyError):
            validate_mode("none", autoplay=True, repeats=False, semantic=True)

    def test_unknown_mode_rejected(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("carousel", autoplay=False, repeats=False, semantic=False)


class FlashRate(unittest.TestCase):
    """WCAG 2.3.1: at most three flashes per second."""

    def test_three_per_second_passes(self):
        validate_flash_rate(3, 1000)

    def test_four_per_second_fails(self):
        with self.assertRaises(MotionPolicyError):
            validate_flash_rate(4, 1000)

    def test_rate_not_count(self):
        validate_flash_rate(6, 2000)  # 3/s over a 2s window
        with self.assertRaises(MotionPolicyError):
            validate_flash_rate(2, 500)  # 4/s

    def test_bad_window_raises_valueerror(self):
        with self.assertRaises(ValueError):
            validate_flash_rate(1, 0)


class SequenceShape(unittest.TestCase):
    """Structural budgets only: 1–8 steps, ≤2 per step, ≤12 total."""

    def test_within_budget_passes(self):
        validate_sequence_shape(5, [1, 2, 1, 1, 1])

    def test_three_in_one_step_fails(self):
        with self.assertRaises(MotionPolicyError):
            validate_sequence_shape(2, [3, 1])

    def test_thirteen_total_fails(self):
        with self.assertRaises(MotionPolicyError):
            validate_sequence_shape(7, [2, 2, 2, 2, 2, 2, 1])

    def test_twelve_total_passes(self):
        validate_sequence_shape(6, [2, 2, 2, 2, 2, 2])

    def test_step_count_bounds(self):
        for steps in (0, 9):
            with self.assertRaises(MotionPolicyError):
                validate_sequence_shape(steps, [1] * steps)
        validate_sequence_shape(8, [1] * 8)

    def test_mismatched_per_step_raises_valueerror(self):
        with self.assertRaises(ValueError):
            validate_sequence_shape(3, [1, 1])


if __name__ == "__main__":
    unittest.main()
