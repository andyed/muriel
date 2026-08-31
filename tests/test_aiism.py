"""
Tests for muriel.aiism — focused on the per-rule suppression mechanism (the
'regime' technical-collocation suppressor) and the cleared-candidates "do not
chase" list backported from muriel.devibe. Standard library only (unittest).
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from muriel.aiism import (
    audit_text,
    format_cleared,
    CLEARED_CANDIDATES,
    main,
)


def _rules(text: str) -> list[str]:
    return [f.rule for f in audit_text(text)]


class TestRegimeSuppression(unittest.TestCase):
    def test_political_regime_flagged(self):
        self.assertIn("phrase-regime", _rules("The regime's crackdown intensified."))

    def test_regime_change_flagged(self):
        self.assertIn("phrase-regime", _rules("They debated regime change for years."))

    def test_asymptotic_regime_suppressed(self):
        self.assertNotIn("phrase-regime", _rules("In the asymptotic regime the error vanishes."))

    def test_linear_regime_suppressed(self):
        self.assertNotIn("phrase-regime",
                         _rules("the linear regime of the psychometric function"))

    def test_scotopic_regime_suppressed(self):
        self.assertNotIn("phrase-regime",
                         _rules("contrast sensitivity in the scotopic regime"))

    def test_low_light_regime_suppressed(self):
        # Hyphenated compound qualifier — the boundary before "light" still fires.
        self.assertNotIn("phrase-regime",
                         _rules("performance in the low-light regime degrades"))

    def test_saturation_regime_suppressed(self):
        self.assertNotIn("phrase-regime", _rules("the response enters a saturation regime"))

    def test_mixed_only_political_flagged(self):
        # One technical (suppressed) + one political (flagged), and the political
        # one sits within the look-back window of the technical one — exactly the
        # case a two-sided window would get wrong. Expect exactly one hit.
        text = "The linear regime held until the regime seized the broadcast tower."
        hits = [f for f in audit_text(text) if f.rule == "phrase-regime"]
        self.assertEqual(len(hits), 1)
        # And it should point at the second (political) occurrence.
        self.assertIn("seized", text[text.index("regime", text.index("regime") + 1):])


class TestAnalystVoiceTells(unittest.TestCase):
    """Two analyst-voice tells observed in decision memos."""

    def test_priced_cost_flagged(self):
        self.assertIn("phrase-priced-cost",
                      _rules("The regression is a priced cost of the ship."))

    def test_priced_cost_case_insensitive(self):
        self.assertIn("phrase-priced-cost",
                      _rules("Priced cost: the engagement regression."))

    def test_plain_cost_not_flagged(self):
        self.assertNotIn("phrase-priced-cost",
                         _rules("The cost was pre-identified in the proposal."))

    def test_declared_risk_names_flagged(self):
        self.assertIn("phrase-document-part-as-actor",
                      _rules("This is the cost the declared risk names."))

    def test_pre_registration_named_flagged(self):
        self.assertIn("phrase-document-part-as-actor",
                      _rules("We accept the skip cost the pre-registration named."))

    def test_risk_statement_names_flagged(self):
        self.assertIn("phrase-document-part-as-actor",
                      _rules("exactly the tradeoff the risk statement names"))

    def test_qualified_comms_named_flagged(self):
        self.assertIn("phrase-document-part-as-actor",
                      _rules("the regression the kickoff memo named"))

    def test_bare_comms_named_flagged(self):
        self.assertIn("phrase-document-part-as-actor",
                      _rules("the tradeoff the announcement names"))

    def test_writeup_hyphen_variant_flagged(self):
        self.assertIn("phrase-document-part-as-actor",
                      _rules("the caveat the write-up named"))

    def test_plain_actor_phrasing_not_flagged(self):
        self.assertNotIn("phrase-document-part-as-actor",
                         _rules("This was pre-identified as a risk when the work was proposed."))

    def test_comms_without_inversion_not_flagged(self):
        self.assertNotIn("phrase-document-part-as-actor",
                         _rules("We sent the memo and named the owner."))


class TestClearedCandidates(unittest.TestCase):
    def test_list_nonempty_and_well_formed(self):
        self.assertTrue(CLEARED_CANDIDATES)
        for candidate, why in CLEARED_CANDIDATES:
            self.assertTrue(candidate and why)

    def test_format_cleared_mentions_em_dash(self):
        out = format_cleared()
        self.assertIn("em-dash", out)
        self.assertIn("do not chase", out.lower())

    def test_cli_list_cleared_exits_zero_without_file(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["--list-cleared"])
        self.assertEqual(rc, 0)
        self.assertIn("do not chase", buf.getvalue().lower())

    def test_cli_no_file_errors(self):
        # argparse .error() raises SystemExit(2)
        with self.assertRaises(SystemExit) as cm:
            main([])
        self.assertEqual(cm.exception.code, 2)


class TestPipelineIntact(unittest.TestCase):
    """Wiring suppression in must not break ordinary rule firing."""

    def test_load_bearing_repeat_still_errors(self):
        text = "It is load-bearing. The load-bearing claim. Another load-bearing point."
        self.assertIn("repeat-load-bearing", _rules(text))

    def test_locus_of_still_flagged(self):
        self.assertIn("phrase-locus-of", _rules("This is the locus of control here."))


if __name__ == "__main__":
    unittest.main()
