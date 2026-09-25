"""The accessible-figure contract, on every generator and against its lint.

Positive half: every SVG muriel's diagram generators write passes
``lint_a11y`` with zero findings. Negative half: a fixture per rule that
the lint must trip — a lint that finds nothing on a broken file is the
failure mode this test exists to catch.
"""

import re
from pathlib import Path

import pytest

from muriel.tools.diagrams import (
    cycle,
    engine_sectors_overlay,
    foveal_overlay,
    layer_stack,
    matrix,
    pyramid,
    swimlane,
)
from muriel.tools.diagrams._a11y import TITLE_MAX, fit_title, lint_a11y, slugify


def _read(path_or_markup):
    s = str(path_or_markup)
    if s.lstrip().startswith("<"):
        return s
    return Path(s).read_text(encoding="utf-8")


def _venn_single(out):
    pytest.importorskip("matplotlib")
    pytest.importorskip("matplotlib_venn")
    from muriel.tools.venn import venn_single
    return venn_single({"a": 5, "b": 3, "c": 2, "a_b": 1, "a_c": 1,
                        "b_c": 1, "all": 1},
                       labels=["a", "b", "c"], title="Scope", out_path=out)


def _venn_panels(out):
    pytest.importorskip("matplotlib")
    pytest.importorskip("matplotlib_venn")
    from muriel.tools.venn import venn_panels
    return venn_panels(
        [{"sets": {"10": 5, "01": 3, "11": 2}, "labels": ["A", "B"],
          "title": "LAB"},
         {"sets": {"10": 4, "01": 3, "11": 1}, "labels": ["A", "B"],
          "title": "WILD"}],
        title="LAB vs WILD", out_path=out)


def _wavefield(out):
    from muriel.layout import BBox
    from muriel.patterns import wavefield
    svg = wavefield(BBox(0, 0, 320, 180), layers=3, seed=4).svg(
        title="Wave field", desc="Three seeded contour layers.")
    Path(out).write_text(svg, encoding="utf-8")
    return str(out)


GENERATORS = {
    "matrix": lambda out: matrix(
        ["A", "B", "C", "D"], axes=(("lo", "hi"), ("lo", "hi")),
        title="Matrix", out_path=out),
    "cycle": lambda out: cycle(["Plan", "Do", "Check", "Act"],
                               center="PDCA", out_path=out),
    "layer_stack": lambda out: layer_stack(
        ["One", "Two", "Three", "Four"], title="Stack", out_path=out),
    "pyramid": lambda out: pyramid(["A", "B", "C", "D"], out_path=out),
    "funnel_proportional": lambda out: pyramid(
        [{"label": "Top", "value": 100}, {"label": "Mid", "value": 40},
         {"label": "Low", "value": 10}, {"label": "End", "value": 2}],
        orientation="down", proportional=True, title="Funnel", out_path=out),
    "swimlane": lambda out: swimlane(
        ["A", "B"], [{"label": "go", "lane": "A"}, {"label": "stop", "lane": "B"}],
        out_path=out),
    "foveal_overlay_l1": lambda out: foveal_overlay(verbosity=1, out_path=out),
    "foveal_overlay_l3": lambda out: foveal_overlay(verbosity=3, out_path=out),
    "engine_sectors_l1": lambda out: engine_sectors_overlay(verbosity=1, out_path=out),
    "engine_sectors_l3": lambda out: engine_sectors_overlay(verbosity=3, out_path=out),
    "venn_single": _venn_single,
    "venn_panels": _venn_panels,
    "wavefield": _wavefield,
}


@pytest.mark.parametrize("name", sorted(GENERATORS))
def test_every_generator_meets_the_contract(tmp_path, name):
    out = tmp_path / f"{name}.svg"
    GENERATORS[name](out)
    svg = out.read_text(encoding="utf-8")
    assert lint_a11y(svg) == []


def test_committed_examples_meet_the_contract():
    examples = sorted(
        (Path(__file__).resolve().parents[1]
         / "plugins/muriel/skills/compose/examples/diagrams").glob("*.svg"))
    assert examples, "no committed diagram examples found"
    for p in examples:
        assert lint_a11y(p.read_text(encoding="utf-8")) == [], p.name


def test_title_is_first_child_and_ids_come_from_out_path(tmp_path):
    svg = _read(pyramid(["A", "B", "C", "D"], title="Skills",
                        out_path=tmp_path / "Q3 skills.svg"))
    assert re.search(
        r'<svg [^>]*role="img" aria-labelledby="q3-skills-title q3-skills-desc"',
        svg)
    body = svg.split(">", 1)[1].lstrip()
    assert body.startswith('<title id="q3-skills-title">Skills</title>')


def test_title_defaults_to_the_diagram_kind(tmp_path):
    svg = _read(cycle(["a", "b", "c"], out_path=tmp_path / "c.svg"))
    assert '<title id="c-title">Cycle</title>' in svg
    svg = _read(pyramid(["a", "b", "c", "d"], orientation="down",
                        out_path=tmp_path / "f.svg"))
    assert '<title id="f-title">Funnel</title>' in svg


def test_default_desc_lists_labels_and_invents_nothing(tmp_path):
    svg = _read(layer_stack(
        [{"label": "App", "tag": "L2"}, "Net", "Link", "Wire"],
        title="Stack", out_path=tmp_path / "s.svg"))
    desc = re.search(r"<desc [^>]*>(.*?)</desc>", svg).group(1)
    for word in ("App", "Net", "Link", "Wire", "Stack"):
        assert word in desc
    # A default must not claim causation, significance, or ranking.
    assert not re.search(r"\b(causes?|significant|best|better|proves?)\b", desc)


def test_explicit_desc_is_used_and_escaped(tmp_path):
    svg = _read(swimlane(["A", "B"], [{"label": "x", "lane": "A"}],
                         desc="Handoffs <5% & falling",
                         out_path=tmp_path / "s.svg"))
    assert '<desc id="s-desc">Handoffs &lt;5% &amp; falling</desc>' in svg


def test_long_title_is_shortened_and_kept_whole_in_desc(tmp_path):
    long_title = ("Quarterly acquisition funnel for the enterprise segment "
                  "across all regions")
    svg = _read(pyramid(["A", "B", "C", "D"], title=long_title,
                        out_path=tmp_path / "long.svg"))
    assert lint_a11y(svg) == []
    title = re.search(r"<title [^>]*>(.*?)</title>", svg).group(1)
    desc = re.search(r"<desc [^>]*>(.*?)</desc>", svg).group(1)
    assert len(title) <= TITLE_MAX and title.endswith("…")
    assert desc.startswith(long_title)
    # The drawn heading is not truncated — only the accessible name.
    assert f">{long_title}</text>" in svg


def test_fit_title_leaves_short_titles_alone():
    assert fit_title("Short", "d") == ("Short", "d")


def test_slugify_yields_valid_xml_id_prefixes():
    assert slugify("Funnel Q2!") == "funnel-q2"
    assert slugify("2024 plan") == "fig-2024-plan"
    assert slugify("???") == "figure"


def test_two_figures_inlined_together_do_not_share_ids(tmp_path):
    a = _read(cycle(["a", "b", "c"], out_path=tmp_path / "first.svg"))
    b = _read(cycle(["a", "b", "c"], out_path=tmp_path / "second.svg"))
    ids = lambda s: set(re.findall(r'<(?:title|desc) id="([^"]+)"', s))  # noqa: E731
    assert not ids(a) & ids(b)


# ─── Negative fixtures: each must trip its rule ─────────────────────

GOOD = (
    '<svg xmlns="http://www.w3.org/2000/svg" role="img" '
    'aria-labelledby="f-title f-desc" viewBox="0 0 100 50">'
    '<title id="f-title">Fixture</title>'
    '<desc id="f-desc">A fixture.</desc>'
    '<rect width="100" height="50" fill="#000"/></svg>'
)


def test_good_fixture_is_clean():
    assert lint_a11y(GOOD) == []


def _trips(svg: str, needle: str) -> None:
    findings = lint_a11y(svg)
    assert findings, "lint found nothing on a broken fixture"
    assert any(needle in f for f in findings), findings


def test_missing_role_trips():
    _trips(GOOD.replace(' role="img"', ""), 'role="img"')


def test_bare_id_trips():
    svg = (GOOD.replace('id="f-title"', 'id="title"')
               .replace("f-title f-desc", "title f-desc"))
    _trips(svg, 'bare id="title"')


def test_title_not_first_child_trips():
    svg = GOOD.replace(
        '<title id="f-title">Fixture</title>',
        '<defs/><title id="f-title">Fixture</title>')
    _trips(svg, "first child")


def test_title_over_sixty_chars_trips():
    svg = GOOD.replace(">Fixture<", ">" + "x" * (TITLE_MAX + 1) + "<")
    _trips(svg, "characters")


def test_dangling_labelledby_trips():
    _trips(GOOD.replace("f-title f-desc", "f-title nope-desc"), "missing id")


def test_labelledby_out_of_order_trips():
    _trips(GOOD.replace("f-title f-desc", "f-desc f-title"), "title first")


def test_missing_labelledby_trips():
    _trips(GOOD.replace(' aria-labelledby="f-title f-desc"', ""), "aria-labelledby")


def test_missing_or_empty_desc_trips():
    _trips(GOOD.replace('<desc id="f-desc">A fixture.</desc>', ""), "<desc>")
    _trips(GOOD.replace(">A fixture.<", "> <"), "<desc> is empty")


def test_empty_title_trips():
    _trips(GOOD.replace(">Fixture<", "><"), "<title> is empty")


def test_duplicate_id_trips():
    _trips(GOOD.replace('<rect ', '<rect id="f-desc" '), "duplicate id")


@pytest.mark.parametrize("vb", ["0 0 100", "0 0 0 50", "0 0 -1 50",
                                "0 0 inf 50", "a b c d"])
def test_bad_viewbox_trips(vb):
    _trips(GOOD.replace('viewBox="0 0 100 50"', f'viewBox="{vb}"'), "viewBox")


def test_aria_hidden_svg_is_exempt():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
           '<rect width="1" height="1"/></svg>')
    assert lint_a11y(svg) == []


def test_malformed_xml_is_a_finding_not_a_pass():
    assert lint_a11y("<svg><title>") != []
