"""
Tests for muriel.typeset.pink_colormap.

The ramp was inline inside ``render_heatmap`` and got hand-extracted into
``attentional-foraging/scripts/render_max_lfhf_heatmap.py`` because there was
nothing importable. Two copies of a color ramp do not announce their drift —
the figures just quietly stop matching each other. It is now one function with
two callers, so it is pinned here.

Standard library + numpy only (unittest, no pytest dependency).
"""

from __future__ import annotations

import unittest

try:
    import numpy as np
except ImportError:  # pragma: no cover - numpy is optional for the package
    np = None

# muriel declares no required dependencies; raster work lives behind the
# `raster` extra (Pillow + numpy) and `muriel.typeset` imports PIL at module
# level. Skip rather than error when the extra is absent, so a bare
# `pip install -e .` still runs a green suite.
try:
    from muriel.typeset import pink_colormap
except ImportError:  # pragma: no cover - raster extra not installed
    pink_colormap = None


@unittest.skipIf(np is None or pink_colormap is None,
                 "requires the `raster` extra (Pillow + numpy)")
class TestPinkColormap(unittest.TestCase):
    def test_shape_and_dtype(self):
        out = pink_colormap(np.zeros((7, 11)))
        self.assertEqual(out.shape, (7, 11, 4))
        self.assertEqual(out.dtype, np.uint8)

    def test_below_threshold_is_fully_transparent(self):
        """Density at or below 0.01 must not paint — that is what keeps the
        background readable through a sparse heatmap."""
        out = pink_colormap(np.full((2, 2), 0.005))
        self.assertTrue((out == 0).all())

    def test_anchor_colors(self):
        """Low / mid / peak anchors of the ramp, pinned.

        d_gamma = d ** 0.7, so d_gamma == 0.5 at d = 0.5 ** (1/0.7); the two
        branches meet at the 'mid' color there.
        """
        d_mid = 0.5 ** (1 / 0.7)
        arr = np.array([[0.02, d_mid, 1.0]])
        rgb = pink_colormap(arr)[0, :, :3]

        # Low end sits near light pink (255, 210, 240) without reaching it,
        # because gamma lifts even small densities off the floor.
        self.assertTrue((rgb[0] > np.array([200, 100, 170])).all())
        # Midpoint is hot pink exactly.
        self.assertTrue(np.allclose(rgb[1], [230, 60, 140], atol=1))
        # Peak is deep magenta exactly.
        self.assertTrue(np.allclose(rgb[2], [180, 20, 80], atol=1))

    def test_alpha_saturates_at_240(self):
        out = pink_colormap(np.array([[1.0]]))
        self.assertEqual(int(out[0, 0, 3]), 240)

    def test_alpha_is_monotonic_in_density(self):
        d = np.linspace(0.02, 1.0, 25).reshape(1, -1)
        alpha = pink_colormap(d)[0, :, 3].astype(int)
        self.assertTrue((np.diff(alpha) >= 0).all(), "alpha must not decrease with density")

    def test_render_heatmap_still_uses_this_ramp(self):
        """Guards the extraction: render_heatmap must delegate, not re-implement."""
        from muriel import typeset  # noqa: F401 - guarded by skipIf above

        called = {}
        original = typeset.pink_colormap

        def spy(arr):
            called["yes"] = True
            return original(arr)

        typeset.pink_colormap = spy
        try:
            typeset.render_heatmap(
                [{"x": 10.0, "y": 10.0, "d": 200.0}],
                canvas_size=(32, 32),
            )
        finally:
            typeset.pink_colormap = original

        self.assertIn("yes", called, "render_heatmap no longer calls pink_colormap")


if __name__ == "__main__":
    unittest.main()
