"""
Tests for muriel.squint — the blur ladder behind the Squinter jury seat.

Four claims carry the module and all four are tested here:

  * The ladder scales with the image. A fixed pixel radius would ask a
    different question of a 400px sprite than of a 3000px poster, which
    is the failure the module exists to prevent.
  * The ladder discriminates. Three levels that produce the same picture
    are one level with three filenames. LadderDiscriminationTests holds
    a one-dominant-mass fixture against a nine-equal-tile fixture and
    fails if heavy cannot tell them apart. Monotone variance down the
    ladder is true of any blur on any input and proves nothing on its
    own, so it is not relied on for this.
  * HALF_SURVIVAL_K is a measurement, not a folk constant. It is
    re-measured against the installed Pillow on every run, because it is
    the number that converts the seat's mass-fraction threshold into a
    sigma.
  * The run is deterministic. Same input, same matte, byte-identical
    outputs — otherwise the lens does not replay and the seat's ballot
    cannot be audited.

The math is pure and tested without Pillow. The render tests skip
cleanly when Pillow (muriel's optional [raster] extra) is absent.
Standard library only (unittest, no pytest dependency).
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muriel.squint import (
    DEFAULT_MATTE,
    FAVICON_EDGE_PX,
    HALF_SURVIVAL_K,
    LADDER,
    LEVELS,
    MIN_SIGMA_PX,
    THUMB_DIVISOR,
    SquintResult,
    blur_sigma,
    favicon_size,
    ladder_sigmas,
    output_paths,
    scaled_size,
    squint,
    survival_width,
    thumb_size,
)
from muriel import squint as squint_module


try:  # optional [raster] extra
    from PIL import Image  # noqa: F401
    HAS_PILLOW = True
except ImportError:  # pragma: no cover — exercised on a bare install
    HAS_PILLOW = False


# ─── Ladder math (no Pillow) ─────────────────────────────────────────────

class LadderMathTests(unittest.TestCase):
    def test_heavy_is_five_percent_of_the_long_edge(self):
        # The ladder is specified by the mass fraction each level
        # half-erases: 3.15% / 6.3% / 10.5% of the long edge. Divided by
        # HALF_SURVIVAL_K that gives 1.5% / 3.0% / 5.0% sigma. Move
        # either number without the other and the tool stops thresholding
        # what the Squinter seat claims to grade.
        self.assertAlmostEqual(blur_sigma(1400, "heavy"), 70.0, places=3)
        self.assertAlmostEqual(LADDER["heavy"], 0.050, places=6)
        self.assertAlmostEqual(LADDER["medium"], 0.030, places=6)
        self.assertAlmostEqual(LADDER["light"], 0.015, places=6)

    def test_survival_width_is_the_stated_mass_fraction(self):
        # 1400px frame: 44 / 88 / 147 px — label group, card block,
        # small panel. These are the numbers a ballot should cite.
        self.assertAlmostEqual(survival_width(1400, "light"), 44.1, places=1)
        self.assertAlmostEqual(survival_width(1400, "medium"), 88.2, places=1)
        self.assertAlmostEqual(survival_width(1400, "heavy"), 147.0, places=1)
        for level in LADDER:
            fraction = survival_width(2000, level) / 2000
            self.assertAlmostEqual(
                fraction, LADDER[level] * HALF_SURVIVAL_K, places=4, msg=level
            )

    def test_sigma_is_proportional_to_the_long_edge(self):
        # The whole point: doubling the image doubles the blur, so the
        # check asks one question across artifact sizes.
        for level in LADDER:
            small = blur_sigma(1000, level)
            large = blur_sigma(2000, level)
            self.assertAlmostEqual(large / small, 2.0, places=3, msg=level)

    def test_ladder_is_strictly_increasing(self):
        s = ladder_sigmas(3000)
        self.assertLess(s["light"], s["medium"])
        self.assertLess(s["medium"], s["heavy"])

    def test_sigma_floor_keeps_tiny_images_from_a_no_op_blur(self):
        # 1.5% of 64px is 0.96px — a Gaussian that small does nothing and
        # the level would lie about having degraded anything.
        self.assertEqual(blur_sigma(64, "light"), MIN_SIGMA_PX)
        self.assertGreater(blur_sigma(64, "heavy"), MIN_SIGMA_PX)

    def test_sigma_is_deterministic(self):
        for level in LADDER:
            self.assertEqual(blur_sigma(1337, level), blur_sigma(1337, level))

    def test_sigma_is_rounded_for_cross_platform_stability(self):
        # 0.006 * 777 = 4.662 exactly at 3dp; no long float tail reaches
        # the filter.
        value = blur_sigma(777, "light")
        self.assertEqual(value, round(value, 3))

    def test_unknown_level_raises(self):
        with self.assertRaises(ValueError):
            blur_sigma(1000, "squint-really-hard")

    def test_non_positive_edge_raises(self):
        with self.assertRaises(ValueError):
            blur_sigma(0, "heavy")

    def test_ladder_sigmas_covers_every_blur_level(self):
        self.assertEqual(set(ladder_sigmas(800)), set(LADDER))


# ─── Thumbnail geometry (no Pillow) ──────────────────────────────────────

class ThumbnailMathTests(unittest.TestCase):
    def test_eighth_scale_preserves_aspect_ratio(self):
        w, h = thumb_size(1600, 900)
        self.assertEqual(w, 1600 // THUMB_DIVISOR)
        self.assertAlmostEqual(w / h, 1600 / 900, delta=0.02)

    def test_favicon_long_edge_is_pinned(self):
        self.assertEqual(max(favicon_size(1600, 900)), FAVICON_EDGE_PX)
        self.assertEqual(max(favicon_size(900, 1600)), FAVICON_EDGE_PX)

    def test_extreme_aspect_never_rounds_a_dimension_to_zero(self):
        # A 2000×9 rule strip at favicon scale would be 16×0.07 px.
        w, h = favicon_size(2000, 9)
        self.assertEqual(w, FAVICON_EDGE_PX)
        self.assertGreaterEqual(h, 1)

    def test_scaled_size_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            scaled_size(0, 100, 16)
        with self.assertRaises(ValueError):
            scaled_size(100, 100, 0)

    def test_thumb_size_rejects_bad_divisor(self):
        with self.assertRaises(ValueError):
            thumb_size(100, 100, divisor=0)


# ─── Export paths (no Pillow) ────────────────────────────────────────────

class OutputPathTests(unittest.TestCase):
    def test_every_level_gets_a_distinct_absolute_path(self):
        paths = output_paths("/tmp/example/panel.png")
        self.assertEqual(set(paths), set(LEVELS))
        self.assertEqual(len({str(p) for p in paths.values()}), len(LEVELS))
        for p in paths.values():
            self.assertTrue(p.is_absolute())
            self.assertEqual(p.suffix, ".png")

    def test_default_out_dir_is_a_squint_directory_beside_the_input(self):
        paths = output_paths("/tmp/example/panel.png")
        self.assertEqual(paths["heavy"].parent.name, "squint")
        self.assertEqual(paths["heavy"].parent.parent.name, "example")

    def test_out_dir_override_is_honored(self):
        paths = output_paths("/tmp/example/panel.png", "/tmp/elsewhere")
        for p in paths.values():
            self.assertEqual(p.parent, Path("/tmp/elsewhere").resolve())

    def test_stem_is_carried_into_the_filename(self):
        paths = output_paths("/tmp/example/dwell-b.png")
        self.assertTrue(paths["heavy"].name.startswith("dwell-b."))


# ─── Missing-Pillow path ─────────────────────────────────────────────────

class PillowGateTests(unittest.TestCase):
    def test_error_names_the_raster_extra(self):
        # Poison the import so the gate fires whether or not Pillow is
        # installed: a None entry in sys.modules makes `from PIL import …`
        # raise ImportError.
        saved = sys.modules.get("PIL", "absent")
        sys.modules["PIL"] = None  # type: ignore[assignment]
        try:
            with self.assertRaises(ImportError) as ctx:
                squint_module._require_pillow()
        finally:
            if saved == "absent":
                sys.modules.pop("PIL", None)
            else:
                sys.modules["PIL"] = saved
        message = str(ctx.exception)
        self.assertIn("Pillow", message)
        self.assertIn("muriel[raster]", message)


# ─── Render (needs Pillow) ───────────────────────────────────────────────

def _make_test_image(path: Path, size=(320, 200)) -> Path:
    """A deterministic two-mass composition: one bright block, one dim."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", size, (10, 10, 15))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 140, 90], fill=(230, 228, 210))
    draw.rectangle([180, 120, 300, 180], fill=(60, 60, 70))
    img.save(str(path), "PNG")
    return path


@unittest.skipUnless(HAS_PILLOW, "Pillow not installed (muriel[raster] extra)")
class RenderTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.src = _make_test_image(self.tmp / "panel.png")

    def tearDown(self):
        self._tmp.cleanup()

    def test_every_level_is_written(self):
        result = squint(self.src, self.tmp / "out")
        self.assertIsInstance(result, SquintResult)
        for level in LEVELS:
            self.assertTrue(
                result.paths[level].exists(), msg=f"{level} not written"
            )

    def test_run_is_byte_identical_across_runs(self):
        first = squint(self.src, self.tmp / "a")
        second = squint(self.src, self.tmp / "b")
        for level in LEVELS:
            self.assertEqual(
                first.paths[level].read_bytes(),
                second.paths[level].read_bytes(),
                msg=f"{level} is not deterministic",
            )

    def test_recorded_dimensions_match_the_written_files(self):
        from PIL import Image

        result = squint(self.src, self.tmp / "out")
        self.assertEqual((result.width, result.height), (320, 200))
        for level in LEVELS:
            with Image.open(str(result.paths[level])) as img:
                self.assertEqual(img.size, result.sizes[level], msg=level)

    def test_blur_levels_keep_the_source_dimensions(self):
        result = squint(self.src, self.tmp / "out")
        for level in ("light", "medium", "heavy", "luma"):
            self.assertEqual(result.sizes[level], (320, 200), msg=level)

    def test_thumbnail_companions_are_downscaled(self):
        result = squint(self.src, self.tmp / "out")
        self.assertEqual(result.sizes["eighth"], (40, 25))
        self.assertEqual(max(result.sizes["px16"]), FAVICON_EDGE_PX)
        self.assertEqual(
            result.sizes["px16_zoom"][0],
            result.sizes["px16"][0] * squint_module.FAVICON_ZOOM,
        )

    def test_luma_level_is_single_channel(self):
        from PIL import Image

        result = squint(self.src, self.tmp / "out")
        with Image.open(str(result.paths["luma"])) as img:
            self.assertEqual(img.mode, "L")

    def test_heavier_levels_carry_less_luminance_variance(self):
        # Necessary, nowhere near sufficient. A Gaussian preserves the
        # mean and reduces the variance, so this holds for any blur
        # ladder on any input — including one whose three levels are the
        # same picture. It catches mislabeled levels and nothing else.
        # LadderDiscriminationTests is what tests the ladder.
        from PIL import Image, ImageStat

        def sd(path: Path) -> float:
            with Image.open(str(path)) as img:
                return ImageStat.Stat(img.convert("L")).stddev[0]

        result = squint(self.src, self.tmp / "out")
        light, medium, heavy = (
            sd(result.paths[level]) for level in ("light", "medium", "heavy")
        )
        self.assertLess(medium, light)
        self.assertLess(heavy, medium)

    def test_matte_is_recorded_and_applied_to_alpha(self):
        from PIL import Image

        rgba = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        alpha_src = self.tmp / "transparent.png"
        rgba.save(str(alpha_src), "PNG")

        result = squint(alpha_src, self.tmp / "matte", matte="#ffffff")
        self.assertEqual(result.matte, (255, 255, 255))
        self.assertEqual(result.matte_hex, "#ffffff")
        with Image.open(str(result.paths["heavy"])) as img:
            self.assertEqual(img.convert("RGB").getpixel((32, 32)), (255, 255, 255))

    def test_palette_transparency_is_matted_not_resolved_to_a_palette_entry(self):
        # Mode P carries transparency in a tRNS chunk, not in a band, so
        # getbands() returns ('P',) and an "A" check misses it. Without
        # an RGBA promotion, convert("RGB") resolves every transparent
        # pixel to whatever palette entry sits at its index — here a
        # saturated red — while the result still records a near-black
        # matte. Figure/ground would be decided by a palette index, which
        # is the one thing this tool must not get wrong. Small UI exports
        # are routinely mode P.
        from PIL import Image, ImageDraw

        pal_src = self.tmp / "palette.png"
        img = Image.new("P", (240, 240), 0)
        img.putpalette([255, 0, 0] + [0, 0, 0] * 255)  # index 0: red
        ImageDraw.Draw(img).rectangle([90, 90, 150, 150], fill=1)
        img.save(str(pal_src), "PNG", transparency=0)

        with Image.open(str(pal_src)) as probe:
            # Guard the premise: if Pillow ever starts reporting an alpha
            # band here, this test is no longer covering the bug.
            self.assertNotIn("A", probe.getbands())
            self.assertIn("transparency", probe.info)

        result = squint(pal_src, self.tmp / "palette-out", matte="#ffffff")
        self.assertEqual(result.matte, (255, 255, 255))
        with Image.open(str(result.paths["heavy"])) as out:
            corner = out.convert("RGB").getpixel((6, 6))
        # Far enough from the opaque square that no blur reaches it, so
        # the matte value must survive exactly.
        self.assertEqual(corner, (255, 255, 255), msg=f"got {corner}")

    def test_default_matte_is_muriel_near_black(self):
        result = squint(self.src, self.tmp / "out")
        self.assertEqual(result.matte_hex, DEFAULT_MATTE)

    def test_missing_source_raises(self):
        with self.assertRaises(FileNotFoundError):
            squint(self.tmp / "nope.png", self.tmp / "out")


# ─── Ladder discrimination (needs Pillow) ────────────────────────────────

FRAME = (1400, 900)
_BG = (10, 10, 15)


def _one_dominant_mass(path: Path) -> Path:
    """A real hierarchy: one hero mass plus four small secondaries.

    The hero spans roughly half the frame, so it is far above every
    level's half-survival width and must come through the whole ladder.
    """
    from PIL import Image, ImageDraw

    img = Image.new("RGB", FRAME, _BG)
    d = ImageDraw.Draw(img)
    d.rectangle([70, 60, 760, 520], fill=(232, 230, 214))
    for i, x in enumerate((70, 420, 770, 1120)):
        d.rectangle([x, 620, x + 200, 800], fill=(70 + i * 6, 70, 82))
    img.save(str(path), "PNG")
    return path


def _nine_equal_tiles(path: Path) -> Path:
    """No hierarchy: a 3x3 comparison grid of equal-weight tiles, each
    carrying interior detail at body-text scale."""
    from PIL import Image, ImageDraw

    w, h = FRAME
    img = Image.new("RGB", FRAME, _BG)
    d = ImageDraw.Draw(img)
    cw, ch = w // 3, h // 3
    for r in range(3):
        for c in range(3):
            x0, y0 = c * cw + 28, r * ch + 28
            x1, y1 = (c + 1) * cw - 28, (r + 1) * ch - 28
            d.rectangle([x0, y0, x1, y1], fill=(198, 196, 186))
            for k in range(4):
                yy = y0 + 40 + k * 26
                d.rectangle([x0 + 30, yy, x1 - 30, yy + 14], fill=(40, 40, 52))
    img.save(str(path), "PNG")
    return path


def _coarse_luma(path: Path) -> bytes:
    """Luminance of a blurred level on a 140x90 grid.

    A blurred image carries no high-frequency content, so a BOX
    downsample is close to lossless here and correlating on 12,600
    samples instead of 1.26M keeps the test in pure Python. Checked
    against a full-resolution numpy correlation: agreement to 0.003.
    """
    from PIL import Image

    with Image.open(str(path)) as img:
        return img.convert("L").resize((140, 90), Image.Resampling.BOX).tobytes()


def _pearson(a: bytes, b: bytes) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    sab = sxx = syy = 0.0
    for x, y in zip(a, b):
        dx, dy = x - ma, y - mb
        sab += dx * dy
        sxx += dx * dx
        syy += dy * dy
    return sab / ((sxx * syy) ** 0.5) if sxx and syy else 1.0


@unittest.skipUnless(HAS_PILLOW, "Pillow not installed (muriel[raster] extra)")
class LadderDiscriminationTests(unittest.TestCase):
    """The ladder must produce different pictures at different levels,
    and must react differently to a hierarchy than to a grid.

    This is the test the monotone-variance check cannot be: variance
    falls down any blur ladder on any input, including one whose three
    levels are visually identical. The Squinter reads the four levels
    heaviest-first and writes a separate record for each. If heavy and
    light are the same picture, that protocol yields four descriptions
    of one image and the seat's ballot is theatre.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _light_to_heavy_correlation(self, fixture, name: str) -> float:
        src = fixture(self.tmp / f"{name}.png")
        result = squint(src, self.tmp / f"{name}-out")
        return _pearson(
            _coarse_luma(result.paths["light"]),
            _coarse_luma(result.paths["heavy"]),
        )

    def test_heavy_dissolves_a_grid_but_keeps_a_real_focal_mass(self):
        # Measured on this pair, 1400x900:
        #   ladder 0.6/1.2/2.0%  dominant 0.984  tiles 0.871  spread 0.11
        #   ladder 1.5/3.0/5.0%  dominant 0.956  tiles 0.614  spread 0.34
        # The old ladder's heavy left a 200px card at 1.00 contrast
        # retention, so it only ever erased text and every level showed
        # the same composition. Thresholds sit between the two.
        dominant = self._light_to_heavy_correlation(
            _one_dominant_mass, "dominant")
        tiles = self._light_to_heavy_correlation(
            _nine_equal_tiles, "tiles")

        # A genuine focal mass is far wider than heavy's half-survival
        # width, so it survives and the composition barely moves.
        self.assertGreater(dominant, 0.90, msg=f"dominant={dominant:.3f}")
        # Equal-weight tiles have no focal mass to survive, so heavy must
        # dissolve the grid rather than redraw it.
        self.assertLess(tiles, 0.75, msg=f"tiles={tiles:.3f}")
        # The spread is the discrimination itself. Under a ladder that
        # only erases text, both fixtures sit near 1.0 and this collapses.
        self.assertGreater(
            dominant - tiles, 0.25,
            msg=(f"ladder does not discriminate: dominant={dominant:.3f} "
                 f"tiles={tiles:.3f} spread={dominant - tiles:.3f}"),
        )

    def test_half_survival_constant_matches_the_installed_pillow(self):
        # HALF_SURVIVAL_K converts the seat's mass-fraction threshold
        # into a sigma. If Pillow's box-approximated Gaussian changes,
        # every stated survival width silently becomes wrong. Re-measure
        # it rather than trusting the comment.
        from PIL import Image, ImageDraw, ImageFilter

        bg, fg = 10, 240
        for sigma in (14.0, 28.0, 70.0):
            edge = 1400
            d = max(1, int(round(HALF_SURVIVAL_K * sigma)))
            img = Image.new("L", (edge, edge), bg)
            c = edge // 2
            ImageDraw.Draw(img).rectangle(
                [c - d // 2, c - d // 2, c + d // 2, c + d // 2], fill=fg)
            blurred = img.filter(ImageFilter.GaussianBlur(radius=sigma))
            retained = (max(blurred.tobytes()) - bg) / (fg - bg)
            self.assertAlmostEqual(
                retained, 0.5, delta=0.08,
                msg=f"sigma={sigma}: width {d}px retained {retained:.3f}",
            )


@unittest.skipUnless(HAS_PILLOW, "Pillow not installed (muriel[raster] extra)")
class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.src = _make_test_image(self.tmp / "panel.png")

    def tearDown(self):
        self._tmp.cleanup()

    def test_cli_prints_every_output_path(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = squint_module._main(
                [str(self.src), "--out-dir", str(self.tmp / "out")]
            )
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        # The agent Reads these back — if a path is not printed, that
        # level is invisible to the seat.
        for level in LEVELS:
            self.assertIn(level, out)
        self.assertIn(str(self.tmp / "out"), out)

    def test_json_manifest_is_parseable_and_complete(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = squint_module._main(
                [str(self.src), "--out-dir", str(self.tmp / "out"), "--json"]
            )
        self.assertEqual(rc, 0)
        manifest = json.loads(buf.getvalue())
        self.assertEqual(manifest["long_edge"], 320)
        self.assertEqual(
            [entry["level"] for entry in manifest["levels"]], list(LEVELS)
        )
        for entry in manifest["levels"]:
            self.assertTrue(Path(entry["path"]).exists())

    def test_missing_file_is_a_usage_error(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = squint_module._main([str(self.tmp / "absent.png")])
        self.assertEqual(rc, 3)

    def test_bad_matte_is_a_usage_error(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = squint_module._main([str(self.src), "--matte", "not-a-color"])
        self.assertEqual(rc, 3)


class RegistryTests(unittest.TestCase):
    def test_squint_is_registered_in_the_top_level_cli(self):
        from muriel.__main__ import SUBCOMMANDS

        self.assertIn("squint", SUBCOMMANDS)
        module_name, helpline = SUBCOMMANDS["squint"]
        self.assertEqual(module_name, "muriel.squint")
        self.assertTrue(helpline)


if __name__ == "__main__":
    unittest.main()
