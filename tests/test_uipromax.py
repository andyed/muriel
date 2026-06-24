"""
Tests for muriel.uipromax — the ui-ux-pro-max corpus loader + 8:1 re-gate,
and the palettes.py / critique.py accessors that surface it. Standard library
only (unittest). Row counts are pinned because the CSVs are a verbatim port.
"""

from __future__ import annotations

import unittest

from muriel import uipromax


EXPECTED_ROWS = {
    "colors": 161,
    "typography": 73,
    "ui_reasoning": 161,
    "ux_guidelines": 99,
    "styles": 84,
    "charts": 25,
    "icons": 105,
}


class Loading(unittest.TestCase):
    def test_all_tables_load_with_expected_counts(self):
        for name, n in EXPECTED_ROWS.items():
            rows = uipromax.table(name)
            self.assertEqual(len(rows), n, f"{name}: expected {n}, got {len(rows)}")
            self.assertIsInstance(rows[0], dict)

    def test_unknown_table_raises(self):
        with self.assertRaises(KeyError):
            uipromax.table("nope")

    def test_query_filters_and_survives_ragged_rows(self):
        # typography has ragged rows (overflow under the None key) — must not crash.
        hits = uipromax.font_pairings(query="luxury")
        self.assertTrue(hits)
        self.assertTrue(all("luxury" in " ".join(uipromax._cell_text(v) for v in r.values()).lower()
                            for r in hits))


class ContrastRegate(unittest.TestCase):
    def test_regate_splits_body_and_interactive(self):
        row = uipromax.colors()[0]  # SaaS (General)
        audit = uipromax.regate_palette(row)
        self.assertIn("Foreground/Background", audit.ratios)
        # Body text clears 8:1 for the first SaaS palette; its accent button
        # pair does not — so the set meets the gate but flags interactive pairs.
        self.assertTrue(audit.meets_floor)
        self.assertEqual(audit.body_failing, [])

    def test_most_sets_clear_body_floor_but_not_all_pairs(self):
        body_safe = uipromax.palettes(meeting_floor=True)
        every = uipromax.palettes()
        self.assertEqual(len(every), 161)
        # Most sets clear the body-text gate; a few don't.
        self.assertGreater(len(body_safe), 140)
        self.assertLess(len(body_safe), len(every))

    def test_interactive_pairs_mostly_below_floor(self):
        # On Accent/Accent almost never clears 8:1 — a real muriel finding.
        audits = uipromax.audit_palettes()
        on_accent_pass = sum(
            1 for a in audits if a.ratios.get("On Accent/Accent", 0) >= 8.0
        )
        self.assertLess(on_accent_pass, 30)


class CritiqueKnowledge(unittest.TestCase):
    def test_anti_patterns_nonempty_with_shape(self):
        rows = uipromax.anti_patterns()
        self.assertTrue(rows)
        sample = rows[0]
        self.assertEqual(set(sample), {"category", "anti_pattern", "severity", "source"})

    def test_anti_patterns_query(self):
        saas = uipromax.anti_patterns(query="saas")
        self.assertTrue(saas)
        self.assertLess(len(saas), len(uipromax.anti_patterns()))


class Wiring(unittest.TestCase):
    def test_palettes_accessor_delegates(self):
        from muriel.palettes import uipromax_brand_palettes
        got = uipromax_brand_palettes(meeting_floor=True)
        self.assertEqual(len(got), len(uipromax.palettes(meeting_floor=True)))

    def test_critique_accessor_delegates(self):
        from muriel.critique import uipromax_anti_patterns
        self.assertEqual(len(uipromax_anti_patterns()), len(uipromax.anti_patterns()))


if __name__ == "__main__":
    unittest.main()
