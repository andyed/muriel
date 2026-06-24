"""
Tests for muriel.motion — the duration binary plus the Emil-inspired
property / easing / scale axes. Standard library only (unittest).

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
    MotionPropertyError,
    easing_for,
    is_compositor_safe,
    validate_duration,
    validate_properties,
    validate_scale,
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


if __name__ == "__main__":
    unittest.main()
