"""audit_svg reads presentation attributes, not just <style> CSS.

muriel's own diagram generators color text with ``fill="…"`` attributes.
Before this pass existed, ``audit_svg`` on any of them returned an empty
list — no text found, nothing failed — which reads exactly like a clean
audit. The fail-closed test at the bottom pins that down: every committed
example must yield scored text entries, and every one must clear 8:1.
"""

from pathlib import Path

import pytest

from muriel.contrast import RENDER_8, audit_svg, contrast_ratio

NS = 'xmlns="http://www.w3.org/2000/svg"'
EXAMPLES = sorted(
    (Path(__file__).resolve().parents[1]
     / "plugins/muriel/skills/compose/examples/diagrams").glob("*.svg"))


def _audit(tmp_path, body, **kw):
    p = tmp_path / "t.svg"
    p.write_text(f'<svg {NS} viewBox="0 0 400 200">{body}</svg>', "utf-8")
    return audit_svg(p, print_table=False, **kw)


def _attr(entries):
    return [e for e in entries if e.source == "svg-attr"]


def test_text_fill_attribute_is_audited(tmp_path):
    entries = _attr(_audit(tmp_path,
        '<rect width="400" height="200" fill="#0a0a0f"/>'
        '<text x="10" y="40" font-size="14" fill="#555566">low</text>'
        '<text x="10" y="80" font-size="14" fill="#e6e4d2">high</text>'))
    by_fill = {e.fill: e for e in entries}
    assert by_fill["#555566"].passes is False
    assert by_fill["#e6e4d2"].passes is True


def test_fill_inherited_from_group_and_tspan(tmp_path):
    entries = _attr(_audit(tmp_path,
        '<rect width="400" height="200" fill="#ffffff"/>'
        '<g fill="#999999"><text x="10" y="40" font-size="14">grey'
        '<tspan fill="#000000"> black</tspan></text></g>'))
    fills = {e.fill: e.passes for e in entries}
    assert fills == {"#999999": False, "#000000": True}


def test_rgba_text_is_composited_before_scoring(tmp_path):
    # Opaque #e6e4d2 clears 8:1 on near-black; at 40% alpha it does not.
    entries = _attr(_audit(tmp_path,
        '<rect width="400" height="200" fill="#0a0a0f"/>'
        '<text x="10" y="40" font-size="14" fill="rgba(230, 228, 210, 0.4)">'
        'faint</text>'))
    (e,) = entries
    assert contrast_ratio("#e6e4d2", "#0a0a0f") > RENDER_8
    assert e.passes is False


def test_fill_opacity_and_group_opacity_are_honoured(tmp_path):
    entries = _attr(_audit(tmp_path,
        '<rect width="400" height="200" fill="#0a0a0f"/>'
        '<g opacity="0.5"><text x="10" y="40" font-size="14" '
        'fill="#e6e4d2" fill-opacity="0.8">dim</text></g>'))
    (e,) = entries
    assert e.passes is False


def test_text_is_scored_against_the_tinted_box_behind_it(tmp_path):
    # Muted text clears 8:1 on the page but sits on a tinted focal band.
    body = ('<rect width="400" height="200" fill="#0a0a0f"/>'
            '<rect x="0" y="100" width="400" height="60" '
            'fill="rgba(125, 212, 228, 0.3)"/>'
            '<text x="20" y="40" font-size="12" fill="#b0b0c4">on page</text>'
            '<text x="20" y="135" font-size="12" fill="#b0b0c4">on band</text>')
    entries = _attr(_audit(tmp_path, body))
    assert len(entries) == 2
    page, band = sorted(entries, key=lambda e: -e.ratio)
    assert page.passes is True and page.bg_rgb == (10, 10, 15)
    assert band.passes is False and band.bg_rgb != (10, 10, 15)


def test_shapes_painted_after_the_text_do_not_count(tmp_path):
    entries = _attr(_audit(tmp_path,
        '<rect width="400" height="200" fill="#0a0a0f"/>'
        '<text x="20" y="40" font-size="12" fill="#e6e4d2">first</text>'
        '<rect x="0" y="0" width="400" height="200" fill="#e6e4d2"/>'))
    (e,) = entries
    assert e.passes is True


def test_explicit_background_overrides_compositing(tmp_path):
    entries = _attr(_audit(tmp_path,
        '<rect width="400" height="200" fill="#0a0a0f"/>'
        '<text x="20" y="40" font-size="12" fill="#e6e4d2">x</text>',
        background="#ffffff"))
    (e,) = entries
    assert e.bg_rgb == (255, 255, 255) and e.passes is False


def test_css_styled_text_is_left_to_the_css_pass(tmp_path):
    entries = _audit(tmp_path,
        '<defs><style>.bg{fill:#0a0a0f}.t{fill:#8a8aa0}</style></defs>'
        '<rect class="bg" width="400" height="200"/>'
        '<text class="t" x="10" y="40">css</text>')
    assert _attr(entries) == []
    assert any(e.selectors == [".t"] for e in entries)


def test_logotype_class_is_exempt(tmp_path):
    entries = _attr(_audit(tmp_path,
        '<rect width="400" height="200" fill="#0a0a0f"/>'
        '<text class="wordmark" x="10" y="40" font-size="30" '
        'fill="#333333">M</text>'))
    (e,) = entries
    assert e.role == "decorative" and e.passes is None


def test_text_over_a_curved_path_is_marked_unverified(tmp_path):
    entries = _attr(_audit(tmp_path,
        '<rect width="400" height="200" fill="#0a0a0f"/>'
        '<path d="M 100 100 A 80 80 0 1 1 300 100 Z" '
        'fill="rgba(100, 160, 200, 0.7)"/>'
        '<text x="200" y="80" font-size="12" text-anchor="middle" '
        'fill="#b0b0c4">20°</text>'))
    (e,) = entries
    assert e.unverified is True


def test_straight_edged_path_is_composited_like_a_polygon(tmp_path):
    entries = _attr(_audit(tmp_path,
        '<path d="M 0 0 L 400 0 L 400 200 L 0 200 Z" fill="#fafaf8"/>'
        '<text x="20" y="40" font-size="12" fill="#0f1117">ink</text>'))
    (e,) = entries
    assert e.bg_rgb == (250, 250, 248) and e.passes is True and not e.unverified


def test_overlapping_translucent_circles_composite_exactly(tmp_path):
    """Venn overlaps: two style-opacity circles stack source-over."""
    entries = _attr(_audit(tmp_path,
        '<rect width="400" height="200" fill="#ffffff"/>'
        '<circle cx="150" cy="100" r="80" style="fill: #ff0000; opacity: 0.5"/>'
        '<circle cx="250" cy="100" r="80" style="fill: #0000ff; opacity: 0.5"/>'
        '<text x="200" y="104" font-size="8" text-anchor="middle" '
        'fill="#000000">1</text>'))
    (e,) = entries
    # white → 50% red → 50% blue
    assert e.bg_rgb == (128, 64, 192) and not e.unverified


def test_circle_bbox_corner_is_not_inside_the_circle(tmp_path):
    """Inside the bounding box but outside the circle: page colour."""
    entries = _attr(_audit(tmp_path,
        '<rect width="400" height="200" fill="#ffffff"/>'
        '<circle cx="100" cy="100" r="90" fill="#000000"/>'
        '<text x="18" y="18" font-size="6" fill="#000000">c</text>'))
    (e,) = entries
    assert e.bg_rgb == (255, 255, 255)


def test_ellipse_is_composited(tmp_path):
    entries = _attr(_audit(tmp_path,
        '<rect width="400" height="200" fill="#ffffff"/>'
        '<ellipse cx="200" cy="100" rx="150" ry="40" fill="rgba(0,0,0,0.5)"/>'
        '<text x="200" y="104" font-size="8" text-anchor="middle" '
        'fill="#000000">e</text>'
        '<text x="200" y="190" font-size="8" text-anchor="middle" '
        'fill="#000000">out</text>'))
    bgs = sorted(e.bg_rgb for e in entries)
    assert bgs == [(128, 128, 128), (255, 255, 255)]


def test_venn_counts_get_a_real_ratio(tmp_path):
    """venn emits its sets as <circle>, so no count is unverified."""
    pytest.importorskip("matplotlib")
    pytest.importorskip("matplotlib_venn")
    from muriel.tools.diagrams.check import check_svg
    from muriel.tools.venn import venn_single
    out = Path(venn_single(
        {"a": 5, "b": 3, "c": 2, "a_b": 1, "a_c": 1, "b_c": 1, "all": 1},
        labels=["a", "b", "c"], title="Scope", out_path=tmp_path / "v.svg"))
    svg = out.read_text("utf-8")
    assert svg.count("<circle ") == 3 and "data-set=" in svg
    entries = _attr(audit_svg(out, print_table=False))
    counts = [e for e in entries if not e.unverified]
    assert counts and not any(e.unverified for e in entries)
    # the triple overlap is the darkest background a count sits on
    assert all(e.passes for e in entries)
    assert check_svg(out) == []


# ─── Fail-closed on the committed examples ──────────────────────────

def test_examples_exist():
    assert EXAMPLES, "no committed diagram examples found"


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_committed_example_is_audited_and_clears_8_to_1(path):
    entries = audit_svg(path, required=RENDER_8, print_table=False)
    scored = [e for e in entries if e.ratio is not None]
    assert scored, f"{path.name}: audit found no text — a blind audit, not a pass"
    failing = [f"{e.selector_display} {e.ratio:.2f}:1"
               for e in scored if e.passes is False]
    assert not failing, failing
    assert not [e for e in scored if e.unverified]
