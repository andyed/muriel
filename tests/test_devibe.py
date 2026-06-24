"""
Tests for muriel.devibe — the design-tell scanner. Covers rule firing,
the cream+serif+sage combo synthesis, the 8:1 contrast cross-check, the
unslop-ignore escape hatch, suppress patterns, and the CLI exit codes.
Standard library only (unittest, no pytest dependency).
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muriel.devibe import (
    Finding,
    audit_source,
    audit_path,
    vibe_score,
    verdict,
    main,
)


def _write_tmp(suffix: str, content: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8",
    )
    f.write(content)
    f.close()
    return Path(f.name)


def _rules(findings: list[Finding]) -> set[str]:
    return {f.rule for f in findings}


class TestRuleFiring(unittest.TestCase):
    def test_ai_purple_tailwind_class(self):
        findings = audit_source('<button className="bg-indigo-600">x</button>')
        self.assertIn("ai-purple", _rules(findings))
        self.assertTrue(all(f.severity == "error" for f in findings if f.rule == "ai-purple"))

    def test_ai_purple_hex_gets_contrast_note(self):
        findings = audit_source('p { color: #6366f1; }')
        purple = [f for f in findings if f.rule == "ai-purple"]
        self.assertTrue(purple)
        # The 8:1 cross-check should annotate the indigo default (4.47:1 on white).
        self.assertIn("fails muriel 8:1", purple[0].message)

    def test_contrast_note_absent_when_disabled(self):
        findings = audit_source('p { color: #6366f1; }', contrast=False)
        purple = [f for f in findings if f.rule == "ai-purple"]
        self.assertTrue(purple)
        self.assertNotIn("fails muriel 8:1", purple[0].message)

    def test_gradient_text(self):
        findings = audit_source('<h1 class="bg-clip-text text-transparent">hi</h1>')
        self.assertIn("gradient-text", _rules(findings))

    def test_hero_three_cards(self):
        findings = audit_source('<div class="grid grid-cols-1 md:grid-cols-3">x</div>')
        self.assertIn("hero-three-cards", _rules(findings))

    def test_generic_sans_font(self):
        findings = audit_source('body { font-family: Inter, sans-serif; }')
        self.assertIn("generic-sans-font", _rules(findings))

    def test_clean_source_no_findings(self):
        clean = (
            "body { font-family: 'Sentinel', Georgia, serif; "
            "color: #e6e4d2; background: #0a0a0f; }\n"
            "h1 { color: #d4a017; }\n"
        )
        self.assertEqual(audit_source(clean), [])


class TestTastefulDefaultCombo(unittest.TestCase):
    def test_cream_plus_serif_triggers_combo_error(self):
        src = (
            '<body style="background:#faf8f5">\n'
            '  <h1 style="font-family:Fraunces">Title</h1>\n'
            "</body>\n"
        )
        findings = audit_source(src)
        self.assertIn("tasteful-default-combo", _rules(findings))
        combo = [f for f in findings if f.rule == "tasteful-default-combo"][0]
        self.assertEqual(combo.severity, "error")

    def test_cream_alone_no_combo(self):
        findings = audit_source('<body style="background:#faf8f5">x</body>')
        self.assertIn("cream-page-bg", _rules(findings))
        self.assertNotIn("tasteful-default-combo", _rules(findings))

    def test_combo_message_names_the_present_axes(self):
        src = 'a{color:#15573a} b{font-family:Playfair Display} c{background:#faf8f5}'
        findings = audit_source(src)
        combo = [f for f in findings if f.rule == "tasteful-default-combo"]
        self.assertTrue(combo)
        # All three axes present → all three named.
        for axis in ("cream", "serif", "sage"):
            self.assertIn(axis, combo[0].message)


class TestEscapeHatchAndSuppress(unittest.TestCase):
    def test_unslop_ignore_skips_line(self):
        src = '<div class="bg-indigo-600">brand color unslop-ignore</div>'
        self.assertEqual(audit_source(src), [])

    def test_muriel_ignore_skips_line(self):
        src = '<div class="bg-indigo-600">brand color muriel-ignore</div>'
        self.assertEqual(audit_source(src), [])

    def test_rounded_full_suppressed_on_small_box(self):
        # Avatar / status dot — h-10 w-10 rounded-full is not a pill button.
        src = '<span class="h-10 w-10 rounded-full">av</span>'
        self.assertNotIn("rounded-everything", _rules(audit_source(src)))

    def test_rounded_full_fires_on_button(self):
        src = '<button class="px-4 rounded-full">Get started</button>'
        self.assertIn("rounded-everything", _rules(audit_source(src)))


class TestDisplayedCodeMasking(unittest.TestCase):
    """A page that *quotes* a tell — a docs sample, a code block, a comment —
    must not be read as committing one. muriel's own tells-teaching docs, which
    necessarily show AI-purple hexes and the gradient-text CSS, are the case
    this protects."""

    def test_hex_inside_inline_code_not_flagged(self):
        src = '<p>Avoid <code>#6366f1</code>, the Tailwind indigo default.</p>'
        self.assertEqual(audit_source(src), [])

    def test_gradient_css_inside_code_not_flagged(self):
        # The docs entry that *explains* the gradient-text tell (web.md:312).
        src = '<p><code>background-clip: text</code> with a gradient fill.</p>'
        self.assertNotIn("gradient-text", _rules(audit_source(src)))

    def test_pre_block_indigo_not_flagged(self):
        # A pygments-style highlight block quoting a palette constant
        # (infographics.md scrutinizer recipe).
        src = (
            '<div class="highlight"><pre><span></span><code>\n'
            '<span class="n">INDIGO_400</span> = <span class="s2">"#818cf8"</span>\n'
            '</code></pre></div>\n'
        )
        self.assertEqual(audit_source(src), [])

    def test_html_comment_tell_not_flagged(self):
        src = '<!-- example to avoid: bg-indigo-600 with gradient-text -->'
        self.assertEqual(audit_source(src), [])

    def test_tell_on_code_element_class_still_flagged(self):
        # Content is blanked, not the tag — a tell on the element's own class
        # is real chrome and must still fire.
        src = '<code class="bg-indigo-600">x</code>'
        self.assertIn("ai-purple", _rules(audit_source(src)))

    def test_tell_in_prose_beside_code_still_flagged(self):
        # The hex in <code> is masked; the violet class on the <p> is chrome.
        src = '<p class="text-violet-500">see <code>#6366f1</code></p>'
        self.assertIn("ai-purple", _rules(audit_source(src)))

    def test_line_numbers_survive_masking(self):
        # Blanking preserves newlines, so a real tell after a masked block
        # still reports its true line number.
        src = (
            '<pre><code>\n'                                       # line 1
            'bg-indigo-600 example\n'                             # line 2 (masked)
            '</code></pre>\n'                                     # line 3
            '<h1 class="bg-clip-text text-transparent">x</h1>\n'  # line 4 (real)
        )
        grad = [f for f in audit_source(src) if f.rule == "gradient-text"]
        self.assertTrue(grad)
        self.assertEqual(grad[0].line, 4)


class TestScoringAndPath(unittest.TestCase):
    def test_vibe_score_weights(self):
        findings = [
            Finding("f", 1, 1, "error", "r1", "m", "e"),
            Finding("f", 2, 1, "warn", "r2", "m", "e"),
            Finding("f", 3, 1, "info", "r3", "m", "e"),
        ]
        self.assertEqual(vibe_score(findings), 3 + 2 + 1)

    def test_verdict_tiers(self):
        self.assertEqual(verdict([]), "Clean — no design tells detected")
        strong = [Finding("f", i, 1, "error", f"r{i}", "m", "e") for i in range(3)]
        self.assertEqual(verdict(strong), "STRONG AI-default look")

    def test_findings_sort_worst_first(self):
        src = (
            "div{border-radius:9999px}\n"       # info
            'h1{color:#6366f1}\n'               # error (ai-purple)
        )
        findings = audit_source(src)
        self.assertTrue(findings)
        self.assertEqual(findings[0].severity, "error")  # sorted worst-first

    def test_audit_path_walks_directory(self):
        d = Path(tempfile.mkdtemp())
        (d / "page.tsx").write_text('<div className="bg-violet-500">x</div>')
        (d / "skip.min.js").write_text('a' * 6000)  # minified, skipped
        (d / "notes.txt").write_text('bg-violet-500')  # non-web ext, skipped
        findings = audit_path(d)
        files = {Path(f.file).name for f in findings}
        self.assertEqual(files, {"page.tsx"})


class TestCli(unittest.TestCase):
    def test_exit_1_on_error_tier(self):
        p = _write_tmp(".tsx", '<h1 class="bg-clip-text text-transparent">x</h1>')
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main([str(p), "--no-color"])
        self.assertEqual(rc, 1)
        self.assertIn("gradient-text", buf.getvalue())

    def test_exit_0_when_below_threshold(self):
        # An info-only source with --severity error should exit 0.
        p = _write_tmp(".tsx", '<button class="px-4 rounded-full">go</button>')
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main([str(p), "--severity", "error", "--no-color"])
        self.assertEqual(rc, 0)

    def test_exit_2_on_missing_path(self):
        rc = main(["/nonexistent/path/xyz.tsx"])
        self.assertEqual(rc, 2)

    def test_json_output_is_valid(self):
        p = _write_tmp(".tsx", '<h1 class="bg-indigo-600">x</h1>')
        buf = io.StringIO()
        with redirect_stdout(buf):
            main([str(p), "--json"])
        payload = json.loads(buf.getvalue())
        self.assertIn("findings", payload)
        self.assertIn("vibe_score", payload)
        self.assertEqual(payload["summary"]["total"], len(payload["findings"]))


if __name__ == "__main__":
    unittest.main()
