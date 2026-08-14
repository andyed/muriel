"""Geometry gate for the diagram generators.

Three things are checked here, and they are different claims.

**Measurement** — the arithmetic in ``_labels`` is right: widths scale with
the string, wrapping breaks on measured width rather than character count,
and the two kinds of overflow are told apart.

**Non-regression** — every committed example renders byte-identical. This
is the load-bearing test for the growth rules: they are supposed to be
strictly conditional, so a diagram whose labels already fit must come out
exactly as it did before any of this existed. A diff here means growth
fired when it shouldn't have.

**The gate** — adversarial specs, whose labels genuinely don't fit, render
clean. Each is a spec that produced a real defect before the fix: text off
the canvas, text spilling out of its own box, two labels on top of each
other, or an item silently dropped. The check reads the rendered SVG back
rather than trusting the generator's arithmetic, so a growth rule that
computes the right number and writes the wrong coordinate still fails.
"""

from pathlib import Path

import pytest

from muriel.tools.diagrams._labels import (
    RATIO_MONO,
    RATIO_SANS,
    fit_text,
    grow_to_fit,
    text_width,
    verify_svg_labels,
    wrap_measured,
)
from muriel.tools.diagrams.cycle import cycle
from muriel.tools.diagrams.layer_stack import layer_stack
from muriel.tools.diagrams.matrix import matrix
from muriel.tools.diagrams.pyramid import pyramid
from muriel.tools.diagrams.swimlane import swimlane

EXAMPLES = (
    Path(__file__).resolve().parents[1]
    / "plugins/muriel/skills/compose/examples/diagrams"
)


# ─── Measurement ────────────────────────────────────────────────────

def test_text_width_scales_with_content_not_just_length():
    # The bug the old char-count wrap had: same length, same verdict.
    assert text_width("abcd", 10, char_width_ratio=0.6) == pytest.approx(24.0)
    assert text_width("", 10) == 0.0
    # Letter-spacing is real width and must be counted.
    plain = text_width("ABCD", 10, char_width_ratio=RATIO_MONO)
    spaced = text_width("ABCD", 10, char_width_ratio=RATIO_MONO,
                        letter_spacing=1.5)
    assert spaced > plain
    assert spaced - plain == pytest.approx(6.0)


def test_wrap_measured_breaks_on_width_and_never_splits_a_word():
    lines = wrap_measured("alpha beta gamma delta", 10, 60,
                          char_width_ratio=RATIO_SANS)
    assert all(text_width(ln, 10, char_width_ratio=RATIO_SANS) <= 60
               for ln in lines)
    assert " ".join(lines) == "alpha beta gamma delta"

    # A word wider than the budget survives intact on its own line —
    # hyphenating a label would silently change what it says.
    long_word = "Containerization/orchestration"
    assert wrap_measured(long_word, 13, 100) == [long_word]


def test_fit_text_distinguishes_the_two_kinds_of_overflow():
    fits = fit_text("Write spec", 13, 128)
    assert not fits.needs_growth and fits.reason == ""

    # Wrappable, but into more rows than allowed -> grow height.
    tall = fit_text("alpha beta gamma delta epsilon zeta", 13, 90, max_lines=2)
    assert tall.needs_growth and tall.reason == "line-count"

    # Not wrappable at all -> grow width.
    wide = fit_text("Containerization/orchestration", 13, 128)
    assert wide.needs_growth and wide.reason == "unbreakable-word"
    assert wide.overflow > 0


def test_grow_to_fit_is_a_floor_on_the_4px_grid():
    assert grow_to_fit(144, 100) == 144      # already big enough
    assert grow_to_fit(144, 187.2) == 188    # rounds up onto the grid
    assert grow_to_fit(144, 144) == 144      # exact fit does not grow


def test_verifier_catches_each_failure_mode():
    ns = 'xmlns="http://www.w3.org/2000/svg"'

    overlapping = (
        f'<svg {ns} viewBox="0 0 400 200">'
        '<text x="10" y="20" font-size="13">hello world</text>'
        '<text x="12" y="22" font-size="13">on top of it</text></svg>'
    )
    assert len(verify_svg_labels(overlapping).collisions) == 1

    off_canvas = (
        f'<svg {ns} viewBox="0 0 400 200">'
        '<text x="-80" y="60" font-size="13">gone</text></svg>'
    )
    assert verify_svg_labels(off_canvas).overruns == ["gone"]

    # Straddling a rect edge, and clearing it on *both* sides — the
    # second is the case corner-containment alone would miss.
    spilling = (
        f'<svg {ns} viewBox="0 0 400 200">'
        '<rect x="150" y="40" width="60" height="30"/>'
        '<text x="120" y="60" font-size="13">far too wide for that box</text>'
        '</svg>'
    )
    assert verify_svg_labels(spilling).overhangs

    clean = (
        f'<svg {ns} viewBox="0 0 400 200">'
        '<rect x="20" y="40" width="300" height="40"/>'
        '<text x="30" y="65" font-size="13">fits fine</text></svg>'
    )
    assert verify_svg_labels(clean).ok


def test_verifier_does_not_flag_a_label_beside_or_above_a_shape():
    # A lane eyebrow sits at a box's height but left of it; a title sits
    # above. Neither is spilling out of the box.
    ns = 'xmlns="http://www.w3.org/2000/svg"'
    svg = (
        f'<svg {ns} viewBox="0 0 400 200">'
        '<rect x="200" y="80" width="150" height="40"/>'
        '<text x="150" y="105" font-size="11" text-anchor="end">LANE</text>'
        '<text x="200" y="30" font-size="20">Title</text></svg>'
    )
    assert verify_svg_labels(svg).ok


# ─── Non-regression: committed examples are untouched ───────────────

def _render_examples(tmp_path):
    """Every committed example, re-rendered from its own spec."""
    return {
        "swimlane-release.svg": swimlane(
            ["PM", "Engineering", "QA", "Release"],
            [{"label": "Write spec", "lane": "PM"},
             {"label": "Implement", "lane": "Engineering"},
             {"label": "Review PR", "lane": "Engineering"},
             {"label": "Test build", "lane": "QA", "focal": True},
             {"label": "Sign off", "lane": "PM"},
             {"label": "Ship", "lane": "Release"}],
            title="Release pipeline",
            out_path=tmp_path / "swimlane-release.svg"),
        "layers-tcpip.svg": layer_stack(
            [{"label": "Application", "tag": "L4", "note": "HTTP, DNS, TLS"},
             {"label": "Transport", "tag": "L3", "note": "TCP, UDP",
              "focal": True},
             {"label": "Internet", "tag": "L2", "note": "IP, ICMP"},
             {"label": "Link", "tag": "L1", "note": "Ethernet, Wi-Fi"}],
            title="The TCP/IP stack", axis_label="abstraction", axis_dir="up",
            out_path=tmp_path / "layers-tcpip.svg"),
        "funnel-q2.svg": pyramid(
            [{"label": "Visitors", "sublabel": "all sessions",
              "value": 100000},
             {"label": "Signups", "value": 24000, "annotation": "−76%"},
             {"label": "Activated", "value": 9000, "annotation": "−62%"},
             {"label": "Paid", "value": 2083, "annotation": "−77%"}],
            orientation="down", proportional=True, axis_label="drop-off",
            title="Acquisition funnel — Q2",
            out_path=tmp_path / "funnel-q2.svg"),
        "cycle-evolver.svg": cycle(
            ["Learns", "Executes", "Evaluates", "Hypothesizes", "Tests"],
            center="Evolver's\nimprovement\ncycle",
            out_path=tmp_path / "cycle-evolver.svg"),
        "matrix-sat-opt.svg": matrix(
            [{"label": "OPTIMIZER",
              "items": ["Long, focused dwells", "Targeted re-reads",
                        "Cognitive load rises with rank"]},
             {"label": "OPTIMIZER + LOAD",
              "items": ["Position 1-3 of dense SERP",
                        "Sustained pupil dilation", "Slow click latency"]},
             {"label": "SATISFICER",
              "items": ["Quick scans", "Early commitments",
                        "Low pupil reactivity"]},
             {"label": "SATISFICER + LOAD",
              "items": ["Conflict signals", "Re-reads without resolution",
                        "Premature exit"]}],
            axes=(("low LF/HF", "high LF/HF"), ("satisficer", "optimizer")),
            title="Sat/opt × LF/HF — orthogonal axes",
            out_path=tmp_path / "matrix-sat-opt.svg"),
    }


@pytest.mark.parametrize("name", [
    "swimlane-release.svg", "layers-tcpip.svg", "funnel-q2.svg",
    "cycle-evolver.svg", "matrix-sat-opt.svg",
])
def test_committed_example_is_byte_identical(tmp_path, name):
    """Growth is conditional: a diagram that fits is rendered unchanged."""
    rendered = Path(_render_examples(tmp_path)[name]).read_text(encoding="utf-8")
    committed = (EXAMPLES / name).read_text(encoding="utf-8")
    assert rendered == committed, (
        f"{name} changed. Either a growth rule fired on a diagram that "
        f"already fit, or the example needs regenerating on purpose."
    )


# ─── The gate: labels that don't fit still render clean ─────────────

def _swimlane_adversarial(out):
    return swimlane(
        ["Product management", "Platform infrastructure",
         "Quality assurance & release engineering"],
        [{"label": "Draft the requirements document",
          "lane": "Product management"},
         {"label": "Containerization/orchestration",
          "lane": "Platform infrastructure"},
         {"label": "Regression suite",
          "lane": "Quality assurance & release engineering", "focal": True},
         {"label": "Ship", "lane": "Product management"}],
        title="Adversarial labels", out_path=out)


def _layer_stack_adversarial(out):
    return layer_stack(
        [{"label": "Presentation, interaction and accessibility surface",
          "tag": "APPLICATION EDGE",
          "note": "React, design tokens, telemetry, feature flags"},
         {"label": "Domain orchestration", "tag": "SERVICES",
          "note": "gRPC, workflow engine", "focal": True},
         {"label": "Persistence", "tag": "DATA", "note": "Postgres, Redis"},
         {"label": "Infrastructure", "tag": "PLATFORM", "note": "Kubernetes"}],
        title="Adversarial stack", out_path=out)


def _pyramid_adversarial(out):
    return pyramid(
        [{"label": "Domain specialists publishing original work",
          "sublabel": "peer-reviewed venues"},
         {"label": "Practising engineers"},
         {"label": "Adjacent contributors"},
         {"label": "General audience"}],
        orientation="up", title="Adversarial pyramid", axis_label="rarer",
        out_path=out)


def _cycle_adversarial(out):
    return cycle(
        ["Instrument", "Containerization/orchestration",
         "Attribute regressions", "Interoperability/standardization"],
        center="Incident\nloop", title="Adversarial cycle", out_path=out)


def _matrix_adversarial(out):
    return matrix(
        [{"label": "OPTIMIZER", "items": [
            "Long, focused dwells on the primary result block",
            "Targeted re-reads of the snippet body",
            "Deliberation before the first click",
            "Cross-referencing between adjacent organic results",
            "Late commitment after full-page survey",
            "Return visits to previously skipped results",
            "Query reformulation rather than settling"]},
         {"label": "OPTIMIZER + LOAD",
          "items": ["Cognitive load rises with rank"]},
         {"label": "SATISFICER", "items": ["Quick scans"]},
         {"label": "SATISFICER + LOAD", "items": ["Premature exit"]}],
        axes=(("low LF/HF", "high LF/HF"), ("satisficer", "optimizer")),
        title="Adversarial matrix", out_path=out)


ADVERSARIAL = {
    "swimlane": _swimlane_adversarial,
    "layer_stack": _layer_stack_adversarial,
    "pyramid": _pyramid_adversarial,
    "cycle": _cycle_adversarial,
    "matrix": _matrix_adversarial,
}


@pytest.mark.parametrize("name", sorted(ADVERSARIAL))
def test_adversarial_labels_render_without_defects(tmp_path, name):
    path = ADVERSARIAL[name](tmp_path / f"{name}-adversarial.svg")
    report = verify_svg_labels(path)
    assert report.ok, f"{name}: {report.summary()}\n" + "\n".join(
        [f"  collision: {c}" for c in report.collisions]
        + [f"  overrun:   {o!r}" for o in report.overruns]
        + [f"  overhang:  {o!r}" for o in report.overhangs]
    )


def test_matrix_renders_every_item_rather_than_silently_capping(tmp_path):
    """The old code kept the first six bullets and dropped the rest."""
    path = _matrix_adversarial(tmp_path / "matrix-cap.svg")
    body = Path(path).read_text(encoding="utf-8")
    # The seventh bullet is the one the old cap ate. It wraps across two
    # rows here, so match a word from it rather than the whole string.
    assert "reformulation" in body
    assert "settling" in body


def test_widened_pyramid_still_clears_its_axis(tmp_path):
    """Scaling the taper must not push the base under the axis arrow.

    The axis is drawn in the left margin at a fixed x; growth is
    symmetric about the centre, so a base that outgrows the margin slides
    underneath it. No text is involved, so the label verifier cannot see
    this one — it needs its own check.
    """
    import re

    path = _pyramid_adversarial(tmp_path / "axis.svg")
    body = Path(path).read_text(encoding="utf-8")
    axis_x = float(re.search(r'<line x1="([\d.]+)"', body).group(1))
    left_edges = [
        min(float(v) for v in pts.replace(",", " ").split()[0::2])
        for pts in re.findall(r'<polygon points="([^"]+)"', body)
    ]
    assert min(left_edges) > axis_x + 8, (
        f"widest tier reaches x={min(left_edges):.1f}, axis sits at "
        f"x={axis_x:.1f}"
    )


def test_growth_is_proportional_not_arbitrary(tmp_path):
    """A pyramid grows by scaling the taper, preserving its shape."""
    import re

    small = pyramid(["Alpha", "Beta", "Gamma", "Delta"],
                    out_path=tmp_path / "small.svg")
    big = _pyramid_adversarial(tmp_path / "big.svg")

    def apex_and_base(path):
        pts = re.findall(r'<polygon points="([^"]+)"',
                         Path(path).read_text(encoding="utf-8"))
        first = [float(v) for v in pts[0].replace(",", " ").split()]
        last = [float(v) for v in pts[-1].replace(",", " ").split()]
        return first[2] - first[0], last[4] - last[6]

    small_ratio = (lambda a, b: a / b)(*apex_and_base(small))
    big_ratio = (lambda a, b: a / b)(*apex_and_base(big))
    assert big_ratio == pytest.approx(small_ratio, rel=0.02)
