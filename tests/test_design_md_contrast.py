"""
Tests for the text-pair contrast check in muriel.design_md_import and the
same-hue fix it carries into muriel.tools.corpus_audit. Standard library
only (unittest).
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from muriel.contrast import contrast_ratio
from muriel.design_md_import import parse_design_md
from muriel.tools.corpus_audit import _format_markdown, _format_summary, audit_file


def _design_md(surface: str, text: str) -> str:
    return textwrap.dedent(f"""\
        ---
        name: Fixture
        colors:
          primary: "#2A3FE5"
          surface: "{surface}"
          text: "{text}"
        ---

        ## Overview

        Fixture.
        """)


def _pair_warns(warnings):
    return [w for w in warnings if w.startswith("text pair")]


class ImporterWarnsOnTextPair(unittest.TestCase):

    def test_failing_pair_warns_with_fix(self):
        # bergside/awesome-design-skills `pulse`: orange text on cream.
        _, warnings = parse_design_md(_design_md("#FFEDD5", "#EA580C"))
        warns = _pair_warns(warnings)
        self.assertEqual(len(warns), 1)
        self.assertIn("3.11:1", warns[0])
        self.assertIn("#812b00", warns[0])
        self.assertIn("Source value kept", warns[0])
        self.assertGreaterEqual(contrast_ratio("#812b00", "#FFEDD5"), 8.0)

    def test_source_colour_is_not_rewritten(self):
        toml_dict, _ = parse_design_md(_design_md("#FFEDD5", "#EA580C"))
        self.assertEqual(toml_dict["colors"]["foreground"], "#EA580C")

    def test_passing_pair_is_silent(self):
        _, warnings = parse_design_md(_design_md("#FFFFFF", "#111827"))
        self.assertEqual(_pair_warns(warnings), [])

    def test_unreachable_pair_says_move_background(self):
        _, warnings = parse_design_md(_design_md("#777777", "#FF0000"))
        warns = _pair_warns(warnings)
        self.assertEqual(len(warns), 1)
        self.assertIn("background has to move", warns[0])

    def test_both_defaulted_pair_is_not_judged(self):
        # No surface or text keys: muriel fills both, and its own default
        # pair is not the brand's contrast.
        text = textwrap.dedent("""\
            ---
            name: Fixture
            colors:
              primary: "#2A3FE5"
            ---
            """)
        _, warnings = parse_design_md(text)
        self.assertEqual(_pair_warns(warnings), [])

    def test_warn_prefix_groups_in_corpus_tally(self):
        # corpus_audit keys WARNs on the text before the first "—" or ":".
        _, warnings = parse_design_md(_design_md("#FFEDD5", "#EA580C"))
        key = _pair_warns(warnings)[0].split("—")[0].split(":")[0].strip()
        self.assertEqual(key, "text pair below muriel's contrast floor")


class CorpusAuditCarriesFix(unittest.TestCase):

    def _audit(self, surface, text, brand="fixture"):
        d = Path(tempfile.mkdtemp()) / brand
        d.mkdir()
        p = d / "DESIGN.md"
        p.write_text(_design_md(surface, text), encoding="utf-8")
        return audit_file(p)

    def test_failing_brand_gets_repair_fields(self):
        r = self._audit("#111111", "#111827", brand="bold")
        self.assertIs(r.passes_8_1, False)
        self.assertEqual(r.repair_direction, "light")
        self.assertIsNotNone(r.repair)
        self.assertGreaterEqual(r.repair_contrast, 8.0)

    def test_passing_brand_has_no_repair(self):
        r = self._audit("#FFFFFF", "#111827")
        self.assertIs(r.passes_8_1, True)
        self.assertIsNone(r.repair)
        self.assertIsNone(r.repair_direction)

    def test_unreachable_brand(self):
        r = self._audit("#777777", "#FF0000")
        self.assertEqual(r.repair_direction, "unreachable")
        self.assertIsNone(r.repair)
        self.assertIn("move bg", _format_markdown([r]))
        self.assertIn("background has to move", _format_summary([r]))

    def test_reports_list_the_fix(self):
        r = self._audit("#FFEDD5", "#EA580C", brand="pulse")
        self.assertIn("#812b00", _format_summary([r]))
        self.assertIn("`#812b00`", _format_markdown([r]))


if __name__ == "__main__":
    unittest.main()
