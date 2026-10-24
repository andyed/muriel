"""
Tests for muriel.loupe — the magnified-crop lens behind the Loupe seat.

Five claims carry the module and all five are tested here:

  * The grid covers the frame with no partial tile. Every ship pixel
    lies in some cell, and the last cell on each axis is flush with the
    far edge instead of hanging past it.
  * The overlap does its job. Any feature no wider than OVERLAP_PX that
    straddles a cell boundary lands whole inside at least one cell;
    otherwise a defect on a seam is split across two tiles and is whole
    in neither.
  * Scale is fixed. The cell is CELL_PX ship pixels on a sprite and on a
    poster alike, unlike muriel.squint, whose blur scales with the
    frame. A proportional cell would turn a poster's loupe into a 1×
    view.
  * The lens magnifies what is there. A 1 px rule comes out ZOOM px
    wide, a pre-rendered @4x source gives the same ship-pixel geometry
    as its 1× export, and empty cells are never written: whitespace is
    not something the seat may fire on.
  * The run is deterministic. Same input, same tiles, byte for byte.

The geometry is pure and tested without Pillow. The render tests skip
cleanly when Pillow (muriel's optional [raster] extra) is absent.
Standard library only (unittest, no pytest dependency).
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muriel.loupe import (
    BUDGET,
    CELL_PX,
    EMPTY_EDGE_PX,
    OVERLAP_PX,
    TILE_EDGE_PX,
    ZOOM,
    cell_grid,
    cell_origins,
    loupe,
    ship_size,
)
from muriel import loupe as loupe_module


try:  # optional [raster] extra
    from PIL import Image, ImageDraw
    HAS_PILLOW = True
except ImportError:  # pragma: no cover — exercised on a bare install
    HAS_PILLOW = False


# ─── Grid geometry (no Pillow) ───────────────────────────────────────────

class GridGeometryTests(unittest.TestCase):
    def test_tile_stays_under_a_vision_model_resize(self):
        # A tile the reading model shrinks back loses the zoom it was cut
        # for. 1024 px is the ceiling the module docstring commits to.
        self.assertEqual(TILE_EDGE_PX, CELL_PX * ZOOM)
        self.assertLessEqual(TILE_EDGE_PX, 1024)
        self.assertEqual(ZOOM, 4)

    def test_docstring_example(self):
        self.assertEqual(cell_origins(1200, 256, 32), [0, 224, 448, 672, 896, 944])

    def test_every_pixel_is_covered_and_no_cell_overhangs(self):
        for length in (1, 17, 255, 256, 257, 480, 900, 1200, 1201, 3000):
            origins = cell_origins(length)
            cell = min(CELL_PX, length)
            covered = set()
            for x in origins:
                self.assertGreaterEqual(x, 0)
                self.assertLessEqual(x + cell, length, f"overhang at {length}")
                covered.update(range(x, x + cell))
            self.assertEqual(covered, set(range(length)), f"gap at {length}")

    def test_last_cell_is_flush(self):
        for length in (257, 900, 1201, 3000):
            self.assertEqual(cell_origins(length)[-1], length - CELL_PX)

    def test_small_axis_is_one_cell(self):
        self.assertEqual(cell_origins(200), [0])
        grid = cell_grid(200, 120)
        self.assertEqual(grid, [(0, 0, 0, 0, 200, 120)])

    def test_overlap_keeps_a_straddling_feature_whole(self):
        # Slide a feature exactly OVERLAP_PX wide across every position
        # on a frame several cells long; each placement must sit wholly
        # inside some cell.
        length = 1200
        origins = cell_origins(length)
        for start in range(0, length - OVERLAP_PX + 1):
            end = start + OVERLAP_PX
            self.assertTrue(
                any(x <= start and end <= x + CELL_PX for x in origins),
                f"feature at {start}-{end} split across cells",
            )

    def test_cell_size_is_fixed_not_proportional(self):
        # The squint ladder scales with the long edge; the loupe must not.
        for width, height in ((400, 300), (1400, 900), (4000, 3000)):
            sizes = {(w, h) for _, _, _, _, w, h in cell_grid(width, height)}
            self.assertEqual(sizes, {(CELL_PX, CELL_PX)})

    def test_bad_geometry_raises(self):
        with self.assertRaises(ValueError):
            cell_origins(0)
        with self.assertRaises(ValueError):
            cell_origins(100, cell=0)
        with self.assertRaises(ValueError):
            cell_origins(1000, cell=256, overlap=256)

    def test_ship_size_rounds_half_up(self):
        self.assertEqual(ship_size(3600, 2520, 4), (900, 630))
        self.assertEqual(ship_size(1801, 1261, 2), (901, 631))
        with self.assertRaises(ValueError):
            ship_size(100, 100, 0)


# ─── Rendering (Pillow) ──────────────────────────────────────────────────

def _blank(width, height, color=(255, 255, 255)):
    return Image.new("RGB", (width, height), color)


def _save(img, directory, name):
    path = Path(directory) / name
    img.save(str(path))
    return path


@unittest.skipUnless(HAS_PILLOW, "Pillow not installed — muriel[raster]")
class LensRenderTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_blank_frame_writes_nothing(self):
        # Whitespace is a decision, not unfinished work. An empty cell is
        # never a tile, so the seat can never be handed one to fire on.
        src = _save(_blank(900, 600), self.tmp, "blank.png")
        result = loupe(src, self.tmp / "out")
        self.assertEqual(result.coverage()["read"], 0)
        self.assertEqual(result.coverage()["empty"], len(result.cells))
        self.assertFalse((self.tmp / "out").exists())

    def test_structure_ranks_first(self):
        # One busy region in an otherwise empty frame: its cell is rank 1.
        img = _blank(1200, 800)
        draw = ImageDraw.Draw(img)
        for i in range(0, 120, 6):
            draw.line([(700 + i, 500), (700 + i, 620)], fill=(20, 20, 20), width=1)
        src = _save(img, self.tmp, "busy.png")
        result = loupe(src, self.tmp / "out")
        top = result.read_cells()[0]
        self.assertTrue(top.x <= 700 and 820 <= top.x + top.w, top.to_dict())
        self.assertTrue(top.y <= 500 and 620 <= top.y + top.h, top.to_dict())

    def test_a_one_pixel_rule_comes_out_zoom_wide(self):
        img = _blank(256, 256)
        ImageDraw.Draw(img).line([(128, 20), (128, 230)], fill=(0, 0, 0), width=1)
        src = _save(img, self.tmp, "rule.png")
        result = loupe(src, self.tmp / "out")
        with Image.open(str(result.read_cells()[0].path)) as raw:
            tile = raw.convert("L")
        self.assertEqual(tile.size, (256 * ZOOM, 256 * ZOOM))
        row = [tile.getpixel((x, 500)) for x in range(tile.width)]
        dark = [x for x, v in enumerate(row) if v < 128]
        self.assertEqual(len(dark), ZOOM)
        self.assertEqual(result.render, "nearest")

    def test_source_scale_keeps_ship_geometry(self):
        # A @4x render and its 1× export lay out the same cells in ship
        # pixels; the @4x tile is a straight crop, not a resample.
        def draw(scale):
            img = _blank(600 * scale, 400 * scale)
            d = ImageDraw.Draw(img)
            d.rectangle([100 * scale, 100 * scale, 300 * scale, 250 * scale],
                        outline=(0, 0, 0), width=scale)
            return img

        one = loupe(_save(draw(1), self.tmp, "one.png"), self.tmp / "a")
        four = loupe(_save(draw(4), self.tmp, "four.png"), self.tmp / "b",
                     source_scale=4)
        self.assertEqual((one.width, one.height), (four.width, four.height))
        self.assertEqual(
            [(c.x, c.y, c.w, c.h) for c in one.cells],
            [(c.x, c.y, c.w, c.h) for c in four.cells],
        )
        self.assertEqual(four.render, "rerender")
        with Image.open(str(four.read_cells()[0].path)) as tile:
            size = tile.size
        self.assertEqual(size, (four.read_cells()[0].w * ZOOM,
                                four.read_cells()[0].h * ZOOM))

    def test_budget_caps_tiles_and_manifest_lists_the_rest(self):
        img = _blank(1600, 1200)
        draw = ImageDraw.Draw(img)
        for x in range(0, 1600, 40):
            draw.line([(x, 0), (x, 1199)], fill=(0, 0, 0), width=1)
        src = _save(img, self.tmp, "grid.png")
        result = loupe(src, self.tmp / "out", budget=5)
        cov = result.coverage()
        self.assertEqual(cov["read"], 5)
        self.assertEqual(cov["read"] + cov["unread"] + cov["empty"], cov["cells"])
        self.assertEqual(len(list((self.tmp / "out").glob("*.png"))), 5)
        self.assertEqual([c.rank for c in result.read_cells()], [1, 2, 3, 4, 5])
        manifest = result.to_dict()
        self.assertEqual(len(manifest["cells"]), cov["cells"])
        self.assertEqual(manifest["cells"][0]["rank"], 1)

    def test_a_cell_under_the_empty_floor_is_not_written(self):
        # A few stray pixels are noise, not structure.
        img = _blank(512, 256)
        for i in range(3):
            img.putpixel((40 + i, 40), (0, 0, 0))
        result = loupe(_save(img, self.tmp, "specks.png"), self.tmp / "out")
        self.assertTrue(all(c.edge_px < EMPTY_EDGE_PX for c in result.cells))
        self.assertEqual(result.coverage()["read"], 0)

    def test_matte_is_recorded_and_palette_alpha_is_honoured(self):
        # A transparent palette image must composite onto the matte, not
        # resolve to whatever entry sits at the transparent index.
        # Index 0 is magenta and transparent: a pixel that came out magenta
        # was resolved by palette index instead of composited.
        pal = Image.new("P", (256, 256), 0)
        pal.putpalette([255, 0, 255, 0, 0, 0] + [0] * (256 * 3 - 6))
        ImageDraw.Draw(pal).rectangle([60, 60, 190, 190], outline=1, width=2)
        src = self.tmp / "pal.png"
        pal.save(str(src), transparency=0)
        result = loupe(src, self.tmp / "out", matte="#ffffff")
        self.assertEqual(result.matte_hex, "#ffffff")
        with Image.open(str(result.read_cells()[0].path)) as raw:
            tile = raw.convert("RGB")
        self.assertEqual(tile.getpixel((4, 4)), (255, 255, 255))

    def test_deterministic(self):
        img = _blank(900, 700)
        draw = ImageDraw.Draw(img)
        draw.ellipse([120, 90, 640, 520], outline=(30, 30, 30), width=1)
        draw.line([(0, 650), (899, 40)], fill=(60, 60, 60), width=1)
        src = _save(img, self.tmp, "det.png")
        a = loupe(src, self.tmp / "a")
        b = loupe(src, self.tmp / "b")
        self.assertEqual(
            [c.to_dict() | {"path": None} for c in a.cells],
            [c.to_dict() | {"path": None} for c in b.cells],
        )
        for ca, cb in zip(a.read_cells(), b.read_cells()):
            self.assertEqual(ca.path.read_bytes(), cb.path.read_bytes())

    def test_no_overview_image_is_written(self):
        # The seat is denied the composition; a contact sheet or grid map
        # in the output directory would undo that denial.
        img = _blank(1200, 800)
        ImageDraw.Draw(img).rectangle([100, 100, 1100, 700], outline=(0, 0, 0), width=1)
        result = loupe(_save(img, self.tmp, "frame.png"), self.tmp / "out", budget=BUDGET)
        written = {p.name for p in (self.tmp / "out").iterdir()}
        expected = {c.path.name for c in result.read_cells()}
        self.assertEqual(written, expected)

    def test_cli_json_and_exit_codes(self):
        img = _blank(512, 512)
        ImageDraw.Draw(img).rectangle([50, 50, 400, 400], outline=(0, 0, 0), width=1)
        src = _save(img, self.tmp, "cli.png")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = loupe_module._main([str(src), "--out-dir", str(self.tmp / "o"), "--json"])
        self.assertEqual(code, 0)
        manifest = json.loads(buf.getvalue())
        self.assertEqual(manifest["zoom"], ZOOM)
        self.assertEqual(manifest["cell_px"], CELL_PX)
        self.assertIn("coverage", manifest)
        self.assertEqual(loupe_module._main([str(self.tmp / "missing.png")]), 3)
        self.assertEqual(loupe_module._main([str(src), "--matte", "not-a-color"]), 3)
        self.assertEqual(loupe_module._main([str(src), "--source-scale", "0"]), 3)


if __name__ == "__main__":
    unittest.main()
