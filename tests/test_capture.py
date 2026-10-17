"""
Tests for muriel.capture filenames.

The filename is the only record of an image's size that survives into
everything downstream: muriel.squint keeps the stem for its companions,
and a jury seat reasons about scale from it. Two claims are tested:

  * A viewport capture keeps the tier convention, ``{slug}-{tier}-{W}x{H}``
    with W×H the tier's CSS viewport.
  * An element (``--selector``) or full-page capture reports the written
    PNG's real pixel size. Before this, a 1200×630 card captured at scale 2
    on the desktop tier was written as ``…-desktop-1920x1080.png`` while the
    file held 2400×1260 pixels.

The naming logic is pure and tested without a browser. The end-to-end
tests skip cleanly when Playwright or its Chromium build is absent, which
is the case in CI. Standard library only (unittest, no pytest dependency).
"""

from __future__ import annotations

import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

from muriel.capture import (
    CaptureError,
    _main,
    capture_filename,
    capture_responsive,
    png_dimensions,
)
from muriel.dimensions import Size


def _png_header(width: int, height: int) -> bytes:
    """Signature plus IHDR length/type/size: the 24 bytes png_dimensions reads."""
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I4sII", 13, b"IHDR", width, height)


class PngDimensionsTests(unittest.TestCase):
    def test_reads_ihdr(self):
        self.assertEqual(png_dimensions(_png_header(2400, 1260)), (2400, 1260))

    def test_reads_ihdr_with_trailing_chunks(self):
        data = _png_header(16, 9) + b"\x08\x06\x00\x00\x00" + b"\x00" * 64
        self.assertEqual(png_dimensions(data), (16, 9))

    def test_rejects_non_png(self):
        with self.assertRaises(ValueError):
            png_dimensions(b"GIF89a" + b"\x00" * 32)

    def test_rejects_truncated_header(self):
        with self.assertRaises(ValueError):
            png_dimensions(_png_header(2400, 1260)[:20])


class CaptureFilenameTests(unittest.TestCase):
    def test_viewport_capture_names_the_tier_viewport(self):
        self.assertEqual(
            capture_filename("hero", "desktop", Size(1920, 1080)),
            "hero-desktop-1920x1080.png",
        )

    def test_element_capture_names_the_image_not_the_viewport(self):
        name = capture_filename("A", "desktop", Size(1920, 1080), (2400, 1260))
        self.assertEqual(name, "A-desktop-2400x1260.png")
        self.assertNotIn("1920x1080", name)

    def test_tier_survives_so_tiers_do_not_collide(self):
        # A fixed-size element is the same size at every tier; the tier
        # segment is what keeps the second capture from overwriting the first.
        a = capture_filename("card", "laptop", Size(1280, 800), (2400, 1260))
        b = capture_filename("card", "desktop", Size(1920, 1080), (2400, 1260))
        self.assertNotEqual(a, b)


# A 1200×630 card on a page wider and taller than it, so a viewport-named
# file and an element-named file can never coincide.
_CARD_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><style>
  html, body { margin: 0; background: #ffffff; }
  #card { width: 1200px; height: 630px; margin: 40px; background: #101010; }
</style></head><body><div id="card"></div></body></html>
"""


def _skip_unless_browser(test: unittest.TestCase, exc: Exception) -> None:
    """Skip when Chromium is missing; re-raise anything else."""
    if "not installed" in str(exc).lower():
        test.skipTest(f"Chromium for Playwright not installed: {exc}")
    raise exc


@unittest.skipUnless(
    importlib.util.find_spec("playwright") is not None,
    "playwright not installed (optional dependency)",
)
class CaptureEndToEndTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.page = self.tmp / "card.html"
        self.page.write_text(_CARD_PAGE, encoding="utf-8")
        self.url = self.page.as_uri()
        self.out = self.tmp / "out"

    def tearDown(self):
        self._tmp.cleanup()

    def test_cli_selector_names_file_by_real_pixel_size(self):
        try:
            status = _main([
                self.url, "--tiers", "desktop", "--scale", "2",
                "--selector", "#card", "--slug", "card",
                "--dir", str(self.out), "--no-idle", "--quiet",
            ])
        except CaptureError as exc:  # pragma: no cover - environment
            _skip_unless_browser(self, exc)
        if status == 2:
            self.skipTest("Chromium for Playwright not installed")
        self.assertEqual(status, 0)

        written = sorted(p.name for p in self.out.iterdir())
        self.assertEqual(written, ["card-desktop-2400x1260.png"])
        data = (self.out / written[0]).read_bytes()
        self.assertEqual(png_dimensions(data), (2400, 1260))

    def test_viewport_capture_keeps_tier_name(self):
        try:
            paths = capture_responsive(
                self.url, tiers=["desktop"], output_dir=self.out,
                slug="page", device_scale_factor=1,
                network_idle=False, verbose=False,
            )
        except CaptureError as exc:  # pragma: no cover - environment
            _skip_unless_browser(self, exc)
        self.assertEqual([p.name for p in paths], ["page-desktop-1920x1080.png"])
        self.assertEqual(png_dimensions(paths[0].read_bytes()), (1920, 1080))


if __name__ == "__main__":
    unittest.main()
