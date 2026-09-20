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


class TestStructuralRhetoric(unittest.TestCase):
    """Shape detectors added 2026-09-20: rule of three, antithesis density,
    and cross-sentence anaphora. Positive cases are generated prose caught in
    a live audit; negative cases are real sentences from the author's own
    documents, which must stay clean."""

    def test_repeated_contrast_marker_is_a_tricolon(self):
        text = ("Read frame by frame, a signal yields the drop but not the approach, "
                "the loud chord but not the far one, the repeat but not the return.")
        self.assertIn("structure-tricolon", _rules(text))

    def test_repeated_marker_is_warn_not_info(self):
        text = ("It gives the drop but not the approach, the chord but not the distance, "
                "the repeat but not the return.")
        sev = [f.severity for f in audit_text(text) if f.rule == "structure-tricolon"]
        self.assertEqual(sev, ["warn"])

    def test_participial_triad_flagged(self):
        text = ("The picture follows the music, leaning into a build, holding through "
                "a lull, treating a returning hook differently from a first hearing.")
        self.assertIn("structure-tricolon", _rules(text))

    def test_mixed_contrast_segments_flagged(self):
        text = ("Each number is the engine's own reading, not an independent annotation; "
                "each citation marks design lineage, never validation; and a detector "
                "that is wired to nothing is reported rather than omitted.")
        self.assertIn("structure-tricolon", _rules(text))

    def test_plain_list_of_three_is_not_a_tricolon(self):
        self.assertNotIn("structure-tricolon", _rules("The palette uses red, green, and blue."))

    def test_technical_three_item_list_is_clean(self):
        text = ("Ten times a second, one row records audio measurements, model outputs, "
                "and shader parameters.")
        self.assertNotIn("structure-tricolon", _rules(text))

    def test_single_earned_contrast_is_clean(self):
        text = ("A chord can therefore be smooth but far from home, or locally abrasive "
                "while remaining in the key.")
        self.assertNotIn("structure-tricolon", _rules(text))

    def test_antithesis_density_flags_a_stacked_paragraph(self):
        text = ("It is not a meter but an instrument. The point is the shape rather than "
                "the level. We built a mechanism, not a model. It reports the failure "
                "instead of hiding it.")
        self.assertIn("density-antithesis", _rules(text))

    def test_antithesis_density_allows_two(self):
        text = ("The engine reads shape rather than level. It reports the failure "
                "instead of hiding it.")
        self.assertNotIn("density-antithesis", _rules(text))

    def test_subordinator_anaphora_pair_flagged(self):
        text = ("Where the literature had a model, we run it. Where it had a finding, "
                "we built a mechanism that respects it.")
        self.assertIn("structure-anaphora", _rules(text))

    def test_terse_emphatic_repetition_is_not_anaphora(self):
        text = 'No false profundity. No "remarkably" or "fascinatingly."'
        self.assertNotIn("structure-anaphora", _rules(text))

    def test_common_opener_repetition_is_clean(self):
        text = ("The engine records the session. The file closes when the song changes. "
                "The next artifact begins.")
        self.assertNotIn("structure-anaphora", _rules(text))

    def test_authors_own_prose_stays_clean(self):
        text = ("A build matters before it peaks. A consonant chord can remain unstable "
                "because it sits far from tonic. The same motif carries different "
                "information when it returns.")
        new = {"structure-tricolon", "density-antithesis", "structure-anaphora"}
        self.assertEqual([r for r in _rules(text) if r in new], [])

    def test_contrast_across_list_items_is_not_a_stack(self):
        """Three bullets that each contain a contrast are three statements,
        not a rhetorical stack. Regression: this fired on the author's own
        CONSUMER_UX_PRINCIPLES before list lines were excluded."""
        text = (
            "- Progressive, not simultaneous. L1 and L2 stay visible.\n"
            "- The bloom uses the diagonal instead of a cramped sliver.\n"
            "- Battery uses the existing Power dive rather than a new surface.\n"
        )
        self.assertNotIn("density-antithesis", _rules(text))

    def test_wrapped_prose_is_still_scanned(self):
        """Regression: a line-based scan hid every sentence that spanned a
        wrap, which is most of them in hard-wrapped Markdown."""
        text = ("Read frame by frame, a signal yields the drop but not the\n"
                "approach, the loud chord but not the far one, the repeat but\n"
                "not the return.")
        self.assertIn("structure-tricolon", _rules(text))

    def test_bold_leading_list_items_is_a_definition_list(self):
        """A bullet opening with a bold term is the house idiom, not
        mid-sentence emphasis. Regression: fired 7x on the author's own
        LISTENING_PRINCIPLES before leading spans were excluded."""
        text = ("- **Anchor the root pie in a corner** when drilling.\n"
                "- **Progressive, not simultaneous.** L1 and L2 stay visible.\n"
                "- **Battery management** uses the existing Power dive.\n")
        self.assertNotIn("bold-overuse", _rules(text))

    def test_bold_table_cells_are_column_labels(self):
        text = ("| 1 | **Opt into AV** | one tap | mic |\n"
                "| 2 | **Listen only** | react to music | mic |\n"
                "| 3 | **Console** | power user | system |\n")
        self.assertNotIn("bold-overuse", _rules(text))

    def test_mid_paragraph_bold_still_flagged(self):
        text = ("This paragraph uses **bold** in the middle, then **more bold** "
                "here, and **still more** at the end.")
        self.assertIn("bold-overuse", _rules(text))
