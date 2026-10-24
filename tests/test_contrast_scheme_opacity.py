"""The CSS audit sees dark mode and translucent text.

Two colophon failures got past ``muriel.contrast`` on 2026-10-24 because
the CSS pass read only the light ``:root`` and scored every colour as
opaque:

- ``.sub2 { fill: #5C5852 }`` stayed #5C5852 in dark mode, where the
  paper is #1F1A14: 2.44:1. Rules inside
  ``@media (prefers-color-scheme: dark)`` were dropped with every other
  ``@media`` block, so the dark cascade was never scored.
- ``.credit { fill: var(--accent); fill-opacity: 0.88 }`` was scored at
  the raw #3A3530's 9.37:1. Composited over #E8E2D0 it paints #4F4A43,
  6.78:1.

The fixtures in ``tests/fixtures/contrast`` are frozen copies of
``plugins/muriel/skills/compose/examples/logos/output/colophon/
interactive-colophon.html``: ``pre-fix`` from commit 9a14b9e, ``fixed``
from branch ``fix/logo-contrast`` (per-mode ``--ink-soft``, credit at full
opacity). The rendered values these tests expect were read back from a
headless Chromium page in both colour schemes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from muriel import contrast as contrast_module
from muriel.contrast import RENDER_8, audit_html, audit_svg, contrast_ratio

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "contrast"
PRE_FIX = FIXTURES / "interactive-colophon.pre-fix.html"
FIXED = FIXTURES / "interactive-colophon.fixed.html"


def _html(tmp_path, css, body="<p>x</p>"):
    p = tmp_path / "t.html"
    p.write_text(
        f"<!doctype html><html><head><style>{css}</style></head>"
        f"<body>{body}</body></html>",
        "utf-8",
    )
    return p


def _row(entries, selector, scheme=None):
    rows = [e for e in entries
            if selector in e.selectors
            and getattr(e, "scheme", None) == scheme]
    assert len(rows) == 1, (selector, scheme, rows)
    return rows[0]


def _hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


# ─── The colophon, before and after ─────────────────────────────────────

@pytest.fixture(scope="module")
def pre_fix():
    entries, _ = audit_html(PRE_FIX, print_table=False)
    return entries


@pytest.fixture(scope="module")
def fixed():
    entries, _ = audit_html(FIXED, print_table=False)
    return entries


def test_pre_fix_sub2_fails_in_dark_mode(pre_fix):
    sub2 = _row(pre_fix, ".sub2", "dark")
    assert sub2.fill_hex == "#5c5852"
    assert sub2.ratio == pytest.approx(2.44, abs=0.01)
    assert sub2.status == "FAIL"
    assert sub2.passes is False


def test_pre_fix_credit_is_scored_after_fill_opacity(pre_fix):
    credit = _row(pre_fix, ".credit")
    # #3A3530 at 0.88 over #E8E2D0. The raw colour would score 9.37:1.
    assert credit.fill_hex == "#4f4a43"
    assert credit.opacity == pytest.approx(0.88)
    assert credit.ratio == pytest.approx(6.78, abs=0.01)
    assert credit.passes is False
    # Above WCAG AA, so the tier is WARN; it still fails the 8:1 rule.
    assert credit.status == "WARN"


def test_pre_fix_dark_rows_resolve_the_dark_custom_properties(pre_fix):
    # var(--ink) is #E8E2D0 in the dark block; the paper is #1F1A14.
    sub1 = _row(pre_fix, ".sub1", "dark")
    assert sub1.fill_hex == "#e8e2d0"
    assert sub1.ratio == pytest.approx(contrast_ratio("#E8E2D0", "#1F1A14"))


def test_fixed_colophon_passes_both_rows_in_both_schemes(fixed):
    for selector in (".sub2", ".credit"):
        for scheme in (None, "dark"):
            row = _row(fixed, selector, scheme)
            assert row.status == "PASS", (selector, scheme, row.ratio)
            assert row.ratio >= RENDER_8
    assert _row(fixed, ".sub2").fill_hex == "#433f3a"
    assert _row(fixed, ".sub2", "dark").fill_hex == "#bab099"


def test_colophon_cli_labels_the_dark_rows(capsys):
    code = contrast_module._main([str(PRE_FIX)])
    out = capsys.readouterr().out
    assert code == 1
    assert "#1f1a14" in out
    dark_sub2 = [ln for ln in out.splitlines()
                 if "[dark]" in ln and ".sub2" in ln]
    assert len(dark_sub2) == 1
    assert dark_sub2[0].split()[:2] == ["FAIL", "2.44:1"]


# ─── prefers-color-scheme: dark ─────────────────────────────────────────

DARK_ONLY_FAIL = """
:root { --bg: #ffffff; --fg: #111111; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #121212; --fg: #eeeeee; }
}
body { background: var(--bg); color: var(--fg); }
.note { color: #333333; }
"""


def test_text_that_fails_only_in_dark_mode_is_reported(tmp_path):
    entries, _ = audit_html(_html(tmp_path, DARK_ONLY_FAIL), print_table=False)
    assert _row(entries, ".note").status == "PASS"
    dark = _row(entries, ".note", "dark")
    assert dark.status == "FAIL"
    assert dark.ratio == pytest.approx(contrast_ratio("#333333", "#121212"))
    # body's var(--fg) follows the dark block too.
    assert _row(entries, "body", "dark").fill_hex == "#eeeeee"


def test_page_without_a_dark_block_gets_no_dark_rows(tmp_path):
    css = "body { background: #fff; color: #111; } .note { color: #222; }"
    entries, _ = audit_html(_html(tmp_path, css), print_table=False)
    assert entries
    assert all(getattr(e, "scheme", None) is None for e in entries)


def test_dark_override_of_a_selector_replaces_its_colour(tmp_path):
    css = """
    body { background: #ffffff; }
    .note { color: #333333; font-weight: 500; }
    @media (prefers-color-scheme: dark) {
      body { background: #121212; }
      .note { color: #dddddd; }
    }
    """
    entries, _ = audit_html(_html(tmp_path, css), print_table=False)
    note = _row(entries, ".note", "dark")  # one row, not a stale #333 too
    assert note.fill_hex == "#dddddd"
    assert note.status == "PASS"


def test_dark_body_background_wins_over_html_body_shorthand(tmp_path):
    css = """
    html, body { background: #ffffff; }
    body { color: #222222; }
    @media (prefers-color-scheme: dark) {
      body { background: #101010; color: #e0e0e0; }
    }
    """
    entries, _ = audit_html(_html(tmp_path, css), print_table=False)
    body = _row(entries, "body", "dark")
    assert body.ratio == pytest.approx(contrast_ratio("#e0e0e0", "#101010"))


def test_compound_dark_media_query_counts_other_media_still_dropped(tmp_path):
    css = """
    body { background: #ffffff; color: #111111; }
    @media screen and (prefers-color-scheme: dark) {
      body { background: #000000; }
    }
    @media (max-width: 600px) { .narrow { color: #999999; } }
    @media (prefers-color-scheme: light) { .lite { color: #999999; } }
    """
    entries, _ = audit_html(_html(tmp_path, css), print_table=False)
    body = _row(entries, "body", "dark")
    assert body.status == "FAIL"  # #111 on #000
    selectors = {s for e in entries for s in e.selectors}
    assert ".narrow" not in selectors
    assert ".lite" not in selectors


def test_media_rules_outside_the_dark_scheme_stay_out_of_the_base_pass():
    rules = contrast_module._parse_rules(DARK_ONLY_FAIL)
    assert all(r.scheme is None for r in rules)
    roots = [r for r in rules if r.selectors == [":root"]]
    assert len(roots) == 1 and roots[0].custom_props["--bg"] == "#ffffff"


def test_dark_inline_styles_resolve_dark_vars(tmp_path):
    p = _html(tmp_path, DARK_ONLY_FAIL,
              body='<p style="color: var(--fg)">x</p>')
    entries, _ = audit_html(p, print_table=False)
    light = [e for e in entries
             if e.source == "inline" and getattr(e, "scheme", None) is None]
    dark = [e for e in entries
            if e.source == "inline" and getattr(e, "scheme", None) == "dark"]
    assert [e.fill_hex for e in light] == ["#111111"]
    assert [e.fill_hex for e in dark] == ["#eeeeee"]
    assert dark[0].status == "PASS"


def test_svg_dark_block_is_audited(tmp_path):
    p = tmp_path / "t.svg"
    p.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40">'
        "<style>"
        ".bg { fill: #ffffff; } .label { fill: #333333; }"
        "@media (prefers-color-scheme: dark) { .bg { fill: #111111; } }"
        "</style>"
        '<rect class="bg" width="100" height="40"/>'
        '<text class="label" x="4" y="20">hi</text></svg>',
        "utf-8",
    )
    entries = audit_svg(p, print_table=False)
    assert _row(entries, ".label").status == "PASS"
    assert _row(entries, ".label", "dark").status == "FAIL"


# ─── fill-opacity / opacity composited ──────────────────────────────────

def test_fill_opacity_in_a_css_rule_is_composited(tmp_path):
    css = """
    body { background: #E8E2D0; }
    .credit { font-size: 16px; fill: #3A3530; fill-opacity: 0.88; }
    """
    entries, _ = audit_html(_html(tmp_path, css), print_table=False)
    credit = _row(entries, ".credit")
    assert credit.fill == "#3A3530"  # the colour as written
    assert credit.fill_hex == "#4f4a43"  # what it paints
    assert credit.ratio == pytest.approx(6.78, abs=0.01)


def test_opacity_on_svg_text_is_composited(tmp_path):
    css = """
    body { background: #ffffff; }
    .label { font-size: 18px; fill: #000000; opacity: 0.5; }
    """
    entries, _ = audit_html(_html(tmp_path, css), print_table=False)
    label = _row(entries, ".label")
    assert label.fill_hex == "#808080"
    assert label.ratio == pytest.approx(contrast_ratio("#808080", "#ffffff"))


def test_opacity_and_fill_opacity_multiply(tmp_path):
    css = """
    body { background: #ffffff; }
    .label { fill: #000000; fill-opacity: 50%; opacity: 0.5; }
    """
    entries, _ = audit_html(_html(tmp_path, css), print_table=False)
    label = _row(entries, ".label")
    assert label.opacity == pytest.approx(0.25)
    assert label.fill_hex == "#bfbfbf"


def test_fill_opacity_does_not_touch_an_html_color(tmp_path):
    css = "body { background: #fff; } .note { color: #000; fill-opacity: .5; }"
    entries, _ = audit_html(_html(tmp_path, css), print_table=False)
    assert _row(entries, ".note").fill_hex == "#000000"


def test_opacity_zero_is_a_hidden_state_not_a_colour(tmp_path):
    # Fade-in starting states: scored as written, never as 1:1.
    css = "body { background: #fff; } .reveal { color: #111; opacity: 0; }"
    entries, _ = audit_html(_html(tmp_path, css), print_table=False)
    assert _row(entries, ".reveal").status == "PASS"


def test_fill_opacity_composited_over_the_dark_background(tmp_path):
    css = """
    :root { --paper: #ffffff; }
    @media (prefers-color-scheme: dark) { :root { --paper: #000000; } }
    body { background: var(--paper); }
    .credit { fill: #808080; fill-opacity: 0.5; }
    """
    entries, _ = audit_html(_html(tmp_path, css), print_table=False)
    assert _row(entries, ".credit").fill_hex == "#c0c0c0"
    assert _row(entries, ".credit", "dark").fill_hex == "#404040"


def test_svg_css_fill_opacity_is_composited(tmp_path):
    p = tmp_path / "t.svg"
    p.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40">'
        "<style>.bg { fill: #E8E2D0; }"
        ".credit { fill: #3A3530; fill-opacity: 0.88; }</style>"
        '<rect class="bg" width="100" height="40"/>'
        '<text class="credit" x="4" y="20">hi</text></svg>',
        "utf-8",
    )
    credit = _row(audit_svg(p, print_table=False), ".credit")
    assert credit.ratio == pytest.approx(6.78, abs=0.01)


def test_opacity_warning_is_kept_and_covers_fill_opacity():
    rules = contrast_module._parse_rules(
        ".a { color: #000; opacity: 0.8; }"
        ".b { fill: #000; fill-opacity: 0.88; }"
        ".c { fill: #000; }"
    )
    warned = {w.selectors[0] for w in contrast_module._legibility_check(rules)
              if w.issue == "opacity-on-text"}
    assert warned == {".a", ".b"}


def test_cli_shows_the_colour_as_written_beside_the_composite(tmp_path, capsys):
    css = "body { background: #E8E2D0; } .credit { fill: #3A3530; fill-opacity: 0.88; }"
    contrast_module._main([str(_html(tmp_path, css))])
    line = next(ln for ln in capsys.readouterr().out.splitlines()
                if ".credit" in ln and ":1" in ln)
    assert "#4f4a43" in line and "#3A3530 at 0.88" in line

