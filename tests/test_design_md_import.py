"""
Tests for muriel.design_md_import — the Stitch design.md → brand.toml
importer. Standard library only (unittest, no pytest).

Covers: rem/em font sizes converting at a 16 px root, the WARN for a size
or radius that is present but unparseable, and the quiet skip of TypeUI's
string metadata keys (``sourceScale``, ``weights``) inside typography.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from muriel.design_md_import import _css_length_to_px, parse_design_md


FIXTURES = Path(__file__).parent / "fixtures" / "design_md"


def _import(name: str):
    path = FIXTURES / name
    return parse_design_md(path.read_text(encoding="utf-8"), source=path)


class CssLengthToPx(unittest.TestCase):
    def test_units_convert_at_16px_root(self):
        self.assertEqual(_css_length_to_px("2.5rem"), 40)
        self.assertEqual(_css_length_to_px("1em"), 16)
        self.assertEqual(_css_length_to_px("16px"), 16)
        self.assertEqual(_css_length_to_px("16"), 16)
        self.assertEqual(_css_length_to_px(".875REM"), 14)
        self.assertEqual(_css_length_to_px(14), 14)

    def test_whole_results_are_int(self):
        self.assertIsInstance(_css_length_to_px("2.5rem"), int)
        self.assertIsInstance(_css_length_to_px(16.0), int)
        self.assertEqual(_css_length_to_px("0.7rem"), 0.7 * 16)
        self.assertIsInstance(_css_length_to_px("0.7rem"), float)

    def test_non_lengths_return_none(self):
        for value in ("2.5vw", "50%", "clamp(1rem, 2vw, 3rem)", "-1rem", "", True,
                      None, [16], float("inf"), float("nan")):
            with self.subTest(value=value):
                self.assertIsNone(_css_length_to_px(value))


class RemSizesImport(unittest.TestCase):
    def setUp(self):
        self.data, self.warnings = _import("rem-sizes.DESIGN.md")
        self.scale = self.data["typography"]["scale"]

    def test_scale_roles_land_in_px(self):
        self.assertEqual(self.scale["h1"], {"size": 40})
        self.assertEqual(self.scale["body"], {"size": 16})
        self.assertEqual(self.scale["label-caps"], {"size": 14})
        self.assertEqual(self.scale["caption"]["size"], 0.7 * 16)

    def test_families_surface(self):
        typo = self.data["typography"]
        self.assertEqual(typo["display_family"], "Playfair Display")
        self.assertEqual(typo["body_family"], "Inter")

    def test_rem_radius_converts(self):
        self.assertEqual(self.data["radii"], {"sm": 4, "md": 8})

    def test_metadata_keys_skip_quietly(self):
        self.assertEqual(self.warnings, [])
        self.assertNotIn("sourceScale", self.scale)
        self.assertNotIn("weights", self.scale)


class UnparseableSizeImport(unittest.TestCase):
    def setUp(self):
        self.data, self.warnings = _import("unparseable-size.DESIGN.md")

    def test_unparseable_size_warns(self):
        self.assertIn(
            "typography.h1.fontSize '2.5vw' not parseable; skipping size",
            self.warnings,
        )
        # The family still imports; only the size is dropped.
        self.assertNotIn("h1", self.data["typography"]["scale"])
        self.assertEqual(self.data["typography"]["display_family"], "Playfair Display")
        self.assertEqual(self.data["typography"]["scale"]["body"], {"size": 16})

    def test_unparseable_radius_warns(self):
        self.assertIn("rounded.pill '50%' not parseable; skipping radius", self.warnings)
        self.assertEqual(self.data["radii"], {"sm": 4})


class NonNumericWeightAndLineHeight(unittest.TestCase):
    def test_string_weight_and_line_height_warn(self):
        text = (
            "---\n"
            "name: Quoted\n"
            "typography:\n"
            "  h1:\n"
            "    fontSize: 32px\n"
            '    fontWeight: "700"\n'
            "    lineHeight: 40px\n"
            "---\n"
        )
        data, warnings = parse_design_md(text)
        self.assertIn("typography.h1.fontWeight '700' not numeric; skipping weight", warnings)
        self.assertIn(
            "typography.h1.lineHeight '40px' not numeric; skipping line height", warnings
        )
        self.assertEqual(data["typography"]["scale"]["h1"], {"size": 32})

    def test_typography_metadata_key_that_is_a_map_still_imports(self):
        # Only the string form is skipped; a map under the same name is a role.
        text = (
            "---\n"
            "name: Weights Role\n"
            "colors:\n"
            '  surface: "#FFFFFF"\n'
            '  text: "#111827"\n'
            "typography:\n"
            "  weights:\n"
            "    fontSize: 1rem\n"
            "---\n"
        )
        data, warnings = parse_design_md(text)
        self.assertEqual(data["typography"]["scale"]["weights"], {"size": 16})
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
