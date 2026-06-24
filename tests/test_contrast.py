"""
Tests for muriel.contrast — covers the HTML audit path added in this
patch and pins down the SVG path so it stays unchanged. Standard
library only (uses unittest, no pytest dependency).
"""

from __future__ import annotations

import io
import textwrap
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muriel.contrast import (
    RENDER_8,
    WCAG_AA,
    SelectorEntry,
    audit_html,
    audit_svg,
    check_text_pair,
    contrast_ratio,
    parse_color,
)
from muriel import contrast as contrast_module


# ─── Helpers ────────────────────────────────────────────────────────────

def _write_tmp(suffix: str, content: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8",
    )
    f.write(content)
    f.close()
    return Path(f.name)


def _silently(callable_):
    """Run a function and swallow its stdout; return its return value."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        return callable_()


# ─── Color + ratio basics ───────────────────────────────────────────────

class ColorBasicsTests(unittest.TestCase):
    def test_hex_color_with_trailing_a_round_trips(self):
        # Regression: the old _parse_declarations called
        # str.rstrip("!important") which silently chewed the trailing 'a'
        # in colors like #8a847a. parse_color must still see all six chars.
        self.assertEqual(parse_color("#8a847a"), (138, 132, 122))

    def test_text_muted_8a847a_against_warm_cream_is_3_55(self):
        # The headline failure number from the index-ailab.html audit.
        ratio = contrast_ratio("#8a847a", "#fcfaf3")
        self.assertAlmostEqual(ratio, 3.55, delta=0.05)

    def test_accent_a04020_against_warm_cream_is_6_19(self):
        ratio = contrast_ratio("#a04020", "#fcfaf3")
        self.assertAlmostEqual(ratio, 6.19, delta=0.05)


# ─── _parse_declarations rstrip regression ──────────────────────────────

class DeclarationParserTests(unittest.TestCase):
    def test_value_ending_in_letter_from_important_set_is_preserved(self):
        decls, custom = contrast_module._parse_declarations(
            "color: #8a847a; font-size: 0.85em"
        )
        self.assertEqual(decls["color"], "#8a847a")
        self.assertEqual(decls["font-size"], "0.85em")

    def test_important_marker_is_stripped(self):
        decls, _ = contrast_module._parse_declarations(
            "color: #1a1612 !important"
        )
        self.assertEqual(decls["color"], "#1a1612")

    def test_custom_property_goes_into_separate_map(self):
        decls, custom = contrast_module._parse_declarations(
            "--text: #1a1612; color: var(--text)"
        )
        self.assertEqual(custom["--text"], "#1a1612")
        self.assertEqual(decls["color"], "var(--text)")
        self.assertNotIn("--text", decls)

    def test_paren_aware_split_keeps_rgba_intact(self):
        decls, _ = contrast_module._parse_declarations(
            "color: rgba(160, 64, 32, 0.25); font-weight: 500"
        )
        self.assertEqual(decls["color"], "rgba(160, 64, 32, 0.25)")
        self.assertEqual(decls["font-weight"], "500")


# ─── CSS variable resolution ────────────────────────────────────────────

class VarResolutionTests(unittest.TestCase):
    def test_one_level_var_resolves(self):
        rules = contrast_module._parse_rules(
            ":root { --text: #1a1612; } body { color: var(--text); }"
        )
        table = contrast_module._build_var_table(rules)
        self.assertEqual(
            contrast_module._resolve_var("var(--text)", table),
            "#1a1612",
        )

    def test_nested_var_resolves(self):
        rules = contrast_module._parse_rules(
            ":root { --base: #a04020; --soft: var(--base); }"
        )
        table = contrast_module._build_var_table(rules)
        self.assertEqual(
            contrast_module._resolve_var("var(--soft)", table),
            "#a04020",
        )

    def test_unknown_var_falls_back_to_fallback(self):
        rules = contrast_module._parse_rules(":root { --x: #ffffff; }")
        table = contrast_module._build_var_table(rules)
        self.assertEqual(
            contrast_module._resolve_var("var(--nope, #123456)", table),
            "#123456",
        )

    def test_unknown_var_with_no_fallback_left_unresolved(self):
        table: dict[str, str] = {}
        self.assertEqual(
            contrast_module._resolve_var("var(--nope)", table),
            "var(--nope)",
        )


# ─── At-rule stripping ──────────────────────────────────────────────────

class AtRuleStripTests(unittest.TestCase):
    def test_media_block_is_dropped(self):
        css = """
        .body { color: #111; }
        @media (max-width: 768px) {
          .body { color: #999; }
          .other { color: #888; }
        }
        .footer { color: #222; }
        """
        rules = contrast_module._parse_rules(css)
        selectors = {s for r in rules for s in r.selectors}
        # The .body / .footer outside @media survive.
        self.assertIn(".body", selectors)
        self.assertIn(".footer", selectors)
        # The .other inside @media is dropped.
        self.assertNotIn(".other", selectors)
        # .body only appears once (not the @media override).
        body_rules = [r for r in rules if ".body" in r.selectors]
        self.assertEqual(len(body_rules), 1)

    def test_keyframes_block_is_dropped(self):
        css = """
        @keyframes wiggle {
          0% { color: #f00; }
          100% { color: #0f0; }
        }
        .x { color: #123; }
        """
        rules = contrast_module._parse_rules(css)
        selectors = {s for r in rules for s in r.selectors}
        self.assertEqual(selectors, {".x"})


# ─── Background detection ───────────────────────────────────────────────

class BackgroundDetectionTests(unittest.TestCase):
    def test_body_background_shorthand_resolves_color_token(self):
        html = """
        <!doctype html><html><head><style>
        :root { --bg: #fcfaf3; }
        body { font-family: serif; background: var(--bg); color: #1a1612; }
        </style></head><body><p>hi</p></body></html>
        """
        path = _write_tmp(".html", html)
        try:
            entries, _ = _silently(lambda: audit_html(path, print_table=False))
            # body's color #1a1612 on the resolved #fcfaf3 background.
            body = next(e for e in entries if e.selectors == ["body"])
            self.assertEqual(body.fill_rgb, (26, 22, 18))
            self.assertGreater(body.ratio, 15.0)
        finally:
            path.unlink(missing_ok=True)

    def test_missing_background_falls_back_to_white_with_warning(self):
        html = """
        <html><head><style>
        body { color: #000000; }
        </style></head><body></body></html>
        """
        path = _write_tmp(".html", html)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                audit_html(path, print_table=True)
            self.assertIn("defaulting to #ffffff", buf.getvalue())
        finally:
            path.unlink(missing_ok=True)


# ─── End-to-end HTML reproducer ─────────────────────────────────────────

# Synthetic fixture mirroring the pre-fix state of
# index-ailab.html (text-muted #8a847a, .byline at 0.85em, TOC at 10px,
# data-level=3 row with opacity). The live exemplar has since been
# polished; this fixture freezes the original failure modes so the audit's
# detection of them is regression-tested.
PRE_FIX_HTML = textwrap.dedent("""\
<!doctype html>
<html lang="en">
<head>
  <style>
    :root {
      --bg: #fcfaf3;
      --text: #1a1612;
      --text-muted: #8a847a;
      --accent: #a04020;
    }
    body { background: var(--bg); color: var(--text); }
    .page-header .byline {
      font-size: 0.85em;
      color: var(--text-muted);
      font-weight: 400;
    }
    .outer-note { color: var(--accent); }
    mark.mg-mark { color: var(--text); border-bottom: 1.5px solid var(--accent); }
    #fisheye-toc a {
      font-size: 10px;
      color: var(--text-muted);
    }
    #fisheye-toc a[data-level="3"] {
      color: var(--text-muted);
      opacity: 0.85;
    }
    footer { font-size: 0.85em; color: var(--text-muted); }
  </style>
</head>
<body>
  <div class="page-header">
    <div class="byline">Andy Edmonds · April 2026</div>
  </div>
  <span class="outer-note">Cheap to sample.</span>
  <p style="color:#555;">Caption text</p>
  <footer>Footer line</footer>
</body>
</html>
""")


class PreFixReproducerTests(unittest.TestCase):
    """The four catches the task spec lists, on a synthetic frozen fixture."""

    def setUp(self):
        self.path = _write_tmp(".html", PRE_FIX_HTML)
        self.entries, self.legibility = _silently(
            lambda: audit_html(self.path, print_table=False)
        )

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def _find(self, selector: str) -> SelectorEntry:
        for e in self.entries:
            if selector in e.selectors:
                return e
        raise AssertionError(f"no entry for selector {selector!r}")

    def test_text_muted_3_55_fails_8_to_1(self):
        byline = self._find(".page-header .byline")
        self.assertAlmostEqual(byline.ratio, 3.55, delta=0.05)
        self.assertEqual(byline.status, "FAIL")
        self.assertEqual(byline.fill_rgb, (138, 132, 122))

    def test_accent_6_19_warns(self):
        # Below 8:1 but above WCAG AA → WARN.
        note = self._find(".outer-note")
        self.assertAlmostEqual(note.ratio, 6.19, delta=0.05)
        self.assertEqual(note.status, "WARN")
        self.assertGreater(note.ratio, WCAG_AA)
        self.assertLess(note.ratio, RENDER_8)

    def test_legibility_warnings_include_toc_byline_footer_opacity(self):
        issues = {w.issue for w in self.legibility}
        self.assertIn("sub-floor", issues)
        self.assertIn("caption-below-16", issues)
        self.assertIn("opacity-on-text", issues)

        # TOC sub-floor: 10px + default weight
        sub_floors = [w for w in self.legibility if w.issue == "sub-floor"]
        toc = [w for w in sub_floors if "#fisheye-toc a" in w.selectors[0]]
        self.assertTrue(toc, "expected sub-floor warning on #fisheye-toc a")

        # Caption floor warnings include byline AND footer
        captions = [w for w in self.legibility if w.issue == "caption-below-16"]
        cap_selectors = {s for w in captions for s in w.selectors}
        self.assertTrue(any("byline" in s for s in cap_selectors))
        self.assertTrue(any("footer" in s for s in cap_selectors))

        # Opacity-on-text on the data-level=3 row
        opac = [w for w in self.legibility if w.issue == "opacity-on-text"]
        self.assertTrue(opac)
        self.assertTrue(
            any('[data-level="3"]' in s for w in opac for s in w.selectors),
            "expected opacity-on-text on the [data-level=\"3\"] row",
        )

    def test_inline_style_color_is_audited(self):
        # The synthetic <p style="color:#555;"> is below 8:1 on cream.
        inline_555 = next(
            (e for e in self.entries if e.fill_rgb == (85, 85, 85)),
            None,
        )
        self.assertIsNotNone(inline_555)
        self.assertIn(inline_555.status, {"WARN", "FAIL"})
        self.assertEqual(inline_555.source, "inline")


# ─── Inline-style deduping ──────────────────────────────────────────────

class InlineStyleTests(unittest.TestCase):
    def test_repeated_inline_color_dedupes_with_count(self):
        html = """
        <html><head><style>body { background: #fff; }</style></head>
        <body>
          <p style="color:#888;">a</p>
          <p style="color:#888;">b</p>
          <p style="color:#888;">c</p>
          <p style="color:#222;">d</p>
        </body></html>
        """
        path = _write_tmp(".html", html)
        try:
            entries, _ = _silently(lambda: audit_html(path, print_table=False))
        finally:
            path.unlink(missing_ok=True)
        inline = [e for e in entries if e.source == "inline"]
        by_color = {e.fill_rgb: e for e in inline}
        self.assertEqual(by_color[(136, 136, 136)].count, 3)
        self.assertEqual(by_color[(34, 34, 34)].count, 1)

    def test_inline_styles_skipped_when_flag_off(self):
        html = (
            "<html><head><style>body{background:#fff}</style></head>"
            "<body><p style='color:#888;'>x</p></body></html>"
        )
        path = _write_tmp(".html", html)
        try:
            entries, _ = _silently(
                lambda: audit_html(path, print_table=False,
                                   audit_inline_styles=False)
            )
        finally:
            path.unlink(missing_ok=True)
        self.assertFalse(any(e.source == "inline" for e in entries))


# ─── SVG path unchanged ─────────────────────────────────────────────────

SVG_FIXTURE = textwrap.dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <style>
      .bg    { fill: #0a0a0f; }
      .title { fill: #e6e4d2; }
      .body  { fill: #8a8aa0; }
      .axis  { fill: #444444; }
    </style>
  </defs>
  <rect class="bg" width="100" height="100" />
  <text class="title" x="10" y="20">Title</text>
  <text class="body" x="10" y="40">Body</text>
</svg>
""")


class SvgAuditTests(unittest.TestCase):
    """Pin down the SVG path so the refactor doesn't change semantics."""

    def setUp(self):
        self.path = _write_tmp(".svg", SVG_FIXTURE)
        self.entries = _silently(lambda: audit_svg(self.path, print_table=False))

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_background_resolved_from_bg_class(self):
        # The .title entry: bg detected as #0a0a0f, fill #e6e4d2, ratio ~15.
        title = next(e for e in self.entries if e.selectors == [".title"])
        self.assertEqual(title.fill_rgb, (230, 228, 210))
        self.assertGreater(title.ratio, 14.0)
        self.assertEqual(title.status, "PASS")

    def test_text_role_below_threshold_fails(self):
        body = next(e for e in self.entries if e.selectors == [".body"])
        self.assertLess(body.ratio, RENDER_8)
        self.assertIn(body.status, {"WARN", "FAIL"})

    def test_decorative_axis_role_is_skipped(self):
        axis = next(e for e in self.entries if e.selectors == [".axis"])
        self.assertEqual(axis.role, "decorative")
        self.assertEqual(axis.status, "SKIP")
        self.assertIsNone(axis.passes)


# ─── Exit code semantics ────────────────────────────────────────────────

class ExitCodeTests(unittest.TestCase):
    def test_passing_html_exits_0(self):
        html = (
            "<html><head><style>"
            "body{background:#ffffff;color:#000000;font-size:20px;font-weight:500}"
            "</style></head><body><p>hi</p></body></html>"
        )
        path = _write_tmp(".html", html)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = contrast_module._main([str(path)])
            self.assertEqual(code, 0)
        finally:
            path.unlink(missing_ok=True)

    def test_failing_html_exits_1(self):
        html = (
            "<html><head><style>"
            "body{background:#ffffff;color:#888888;font-size:20px;font-weight:500}"
            "</style></head><body></body></html>"
        )
        path = _write_tmp(".html", html)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = contrast_module._main([str(path)])
            self.assertEqual(code, 1)
        finally:
            path.unlink(missing_ok=True)

    def test_legibility_only_exits_2(self):
        # Color contrast clears 8:1, but font-size 12px+default weight trips
        # the sub-floor rule.
        html = (
            "<html><head><style>"
            "body{background:#ffffff;color:#000000}"
            ".caption{font-size:12px;color:#000000}"
            "</style></head><body></body></html>"
        )
        path = _write_tmp(".html", html)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = contrast_module._main([str(path)])
            self.assertEqual(code, 2)
        finally:
            path.unlink(missing_ok=True)

    def test_missing_file_exits_3(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = contrast_module._main(["/nonexistent/path/nope.html"])
        self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main()
