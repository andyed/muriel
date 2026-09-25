"""Curated Lucide glyphs, and the cycle generator's icon slot and hub.

The glyph tests check the normalization contract the cycle wrapper relies
on: inner markup only, no colour of its own, geometry on the 24×24 grid.
The cycle tests read the rendered SVG back — labels, contrast, a11y —
rather than trusting the generator's arithmetic.
"""

import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from muriel.tools.diagrams._labels import verify_svg_labels
from muriel.tools.diagrams.check import check_svg
from muriel.tools.diagrams.cycle import cycle
from muriel.tools.diagrams.icons import (
    ALIASES,
    GLYPHS,
    LUCIDE_VERSION,
    SLOTS,
    resolve_icon,
)
from muriel.tools.diagrams.icons import _manifest

REPO = Path(__file__).resolve().parents[1]
SVG_NS = "http://www.w3.org/2000/svg"
_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _fragment(markup: str) -> ET.Element:
    return ET.fromstring(f'<g xmlns="{SVG_NS}">{markup}</g>')


# ─── Glyph contract ─────────────────────────────────────────────────

def test_manifest_and_glyphs_agree():
    assert list(GLYPHS) == list(SLOTS)
    assert LUCIDE_VERSION == _manifest.LUCIDE_VERSION
    assert 25 <= len(GLYPHS) <= 40
    # Aliases point at real slots and never shadow one.
    for alias, slot in ALIASES.items():
        assert slot in GLYPHS, alias
        assert alias not in GLYPHS, alias


@pytest.mark.parametrize("slot", sorted(GLYPHS))
def test_glyph_is_bare_inner_markup(slot):
    markup = GLYPHS[slot]
    root = _fragment(markup)          # parses as an XML fragment
    assert "<svg" not in markup
    for attr in ("fill=", "stroke=", "stroke-width=", "class=", "style="):
        assert attr not in markup, f"{slot} carries {attr}"
    children = list(root)
    assert children, slot
    assert all(el.tag == f"{{{SVG_NS}}}path" for el in children), (
        f"{slot}: only <path> survives normalization")


@pytest.mark.parametrize("slot", sorted(GLYPHS))
def test_glyph_geometry_on_the_24_grid(slot):
    # Rough bound: every number in every path — absolute coordinates and
    # relative deltas alike — lies within the 24-unit grid.
    for el in _fragment(GLYPHS[slot]):
        nums = [float(v) for v in _NUM.findall(el.get("d", ""))]
        assert nums, slot
        assert all(math.isfinite(v) and -24.0 <= v <= 24.0 for v in nums), slot
        # First moveto is absolute and must land on the canvas.
        m = re.match(r"\s*M\s*([-\d.]+)[ ,]+([-\d.]+)", el.get("d", ""))
        if m:
            x, y = float(m.group(1)), float(m.group(2))
            assert 0.0 <= x <= 24.0 and 0.0 <= y <= 24.0, (slot, x, y)


def test_build_script_check_is_clean():
    """glyphs.py is exactly what the vendored cache regenerates."""
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts/build_diagram_icons.py"), "--check"],
        capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stdout + r.stderr


def test_vendor_license_is_shipped():
    lic = (REPO / "muriel/tools/diagrams/icons/vendor/lucide/LICENSE").read_text()
    assert "ISC License" in lic and "Cole Bemis" in lic


# ─── Resolution ─────────────────────────────────────────────────────

def test_resolve_named_alias_and_raw():
    assert resolve_icon("refresh") == GLYPHS["refresh"]
    assert resolve_icon("Iterate") == GLYPHS["refresh"]
    assert resolve_icon("eye") == GLYPHS["observe"]
    raw = '<circle cx="12" cy="12" r="4"/>'
    assert resolve_icon(raw) == raw
    assert resolve_icon(None) is None


def test_unknown_icon_raises_with_suggestions():
    with pytest.raises(ValueError, match="refresh"):
        resolve_icon("refesh")
    with pytest.raises(ValueError, match="unknown icon"):
        cycle([{"label": "a", "icon": "nope-not-a-glyph"}, "b", "c"],
              out_path="/dev/null")


# ─── Cycle: icons ───────────────────────────────────────────────────

def test_cycle_draws_named_icon_inside_a_wrapper(tmp_path):
    path = cycle([{"label": "Observe", "icon": "observe"},
                  {"label": "Measure", "icon": "ruler"},
                  "Decide"], out_path=tmp_path / "icons.svg")
    body = Path(path).read_text(encoding="utf-8")
    assert GLYPHS["observe"] in body and GLYPHS["measure"] in body
    wrappers = re.findall(r'<g transform="[^"]*"[^>]*aria-hidden="true">', body)
    assert len(wrappers) == 2
    assert all('fill="none"' in w and "stroke=" in w for w in wrappers)
    assert check_svg(path) == []


def test_cycle_icon_scales_from_brand_iconography(tmp_path):
    from muriel.styleguide import load_styleguide
    brand = load_styleguide(
        REPO / "plugins/muriel/skills/compose/examples/example-brand.toml")
    path = cycle([{"label": "Plan", "icon": "idea"}, "Do", "Check"],
                 brand=brand, out_path=tmp_path / "brand.svg")
    body = Path(path).read_text(encoding="utf-8")
    size = brand.iconography.default_size
    assert f"scale({size / 24:.4g})" in body
    # Rendered stroke stays at the brand's stroke_px after scaling.
    sw = float(re.search(
        r'<g [^>]*stroke-width="([\d.]+)"[^>]*aria-hidden', body).group(1))
    assert sw * size / 24 == pytest.approx(brand.iconography.stroke_px, rel=1e-3)
    assert check_svg(path) == []


def test_raw_icon_markup_still_accepted(tmp_path):
    raw = '<circle cx="12" cy="12" r="6"/>'
    path = cycle([{"label": "a", "icon": raw}, "b", "c"],
                 out_path=tmp_path / "raw.svg")
    assert raw in Path(path).read_text(encoding="utf-8")


# ─── Cycle: hub ─────────────────────────────────────────────────────

def _spokes(body: str) -> list[str]:
    return re.findall(r'<path d="M [^"]+"[^>]*stroke-dasharray[^>]*/>', body)


def test_hub_draws_one_dashed_spoke_per_selected_step(tmp_path):
    steps = ["Capture", "Research", "Decide", "Act", "Measure", "Learn"]
    all_path = cycle(steps, hub={"label": "Shared memory"},
                     out_path=tmp_path / "all.svg")
    some_path = cycle(steps, hub={"label": "Shared memory",
                                  "steps": [0, "Measure"]},
                      out_path=tmp_path / "some.svg")
    all_body = Path(all_path).read_text(encoding="utf-8")
    some_body = Path(some_path).read_text(encoding="utf-8")
    assert len(_spokes(all_body)) == 6
    assert len(_spokes(some_body)) == 2
    # Spokes are neutral, not accent, and prefixed-id markers.
    accent = "#7dd4e4"
    assert all(accent not in s for s in _spokes(all_body))
    assert 'id="all-spoke-arrow"' in all_body
    # Spokes are drawn beneath the step nodes.
    assert all_body.index("stroke-dasharray") < all_body.index("<circle")
    assert "written back by Capture, Measure" in some_body


def test_hub_label_clears_8_to_1_and_labels_do_not_collide(tmp_path):
    path = cycle(["Plan", "Do", "Check", "Act"],
                 hub={"label": "Evidence log", "sublabel": "every run appends"},
                 title="PDCA with a log", out_path=tmp_path / "hub.svg")
    assert check_svg(path) == []


@pytest.mark.parametrize("n", [3, 5, 8])
def test_adversarial_hub_grows_the_ring_and_stays_clean(tmp_path, n):
    steps = [f"Stage number {i} of the pipeline" for i in range(n)]
    path = cycle(steps,
                 hub={"label": "Institutional knowledge base and "
                               "shared operating record",
                      "sublabel": "every stage reads it and writes back "
                                  "what it learned"},
                 title="Adversarial hub", out_path=tmp_path / f"adv{n}.svg")
    body = Path(path).read_text(encoding="utf-8")
    report = verify_svg_labels(path)
    assert report.ok, report.summary()
    assert check_svg(path) == []

    # Geometry: every spoke has visible length, and the hub box sits
    # inside the ring (no node circle overlaps it).
    rect = re.search(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" '
                     r'height="([\d.]+)" rx="10"', body)
    hx, hy, hw, hh = (float(v) for v in rect.groups())
    for cx, cy, r in re.findall(
            r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', body):
        cx, cy, r = float(cx), float(cy), float(r)
        nx = min(max(cx, hx), hx + hw)
        ny = min(max(cy, hy), hy + hh)
        assert math.hypot(cx - nx, cy - ny) > r + 12
    for s in _spokes(body):
        x0, y0, x1, y1 = (float(v) for v in re.search(
            r'M ([\d.]+) ([\d.]+) L ([\d.]+) ([\d.]+)', s).groups())
        assert math.hypot(x1 - x0, y1 - y0) >= 17.5


@pytest.mark.parametrize("n", [3, 4, 5, 6, 8])
def test_wrapped_step_labels_stay_off_the_node_circles(tmp_path, n):
    """A wrapped top label used to grow down onto its own node.

    The label verifier treats rects and polygons as containers, not
    circles, so this reads the circles back itself.
    """
    from muriel.tools.diagrams._labels import RATIO_SANS, label_bbox

    path = cycle([f"Stage number {i} of the pipeline" for i in range(n)],
                 hub="Shared record", out_path=tmp_path / f"wrap{n}.svg")
    root = ET.parse(path).getroot()
    circles = [(float(c.get("cx")), float(c.get("cy")), float(c.get("r")))
               for c in root.iter(f"{{{SVG_NS}}}circle")]
    for el in root.iter(f"{{{SVG_NS}}}text"):
        if el.get("font-size") != "15":
            continue
        box = label_bbox(el.text, 15, float(el.get("x")), float(el.get("y")),
                         text_anchor=el.get("text-anchor"),
                         char_width_ratio=RATIO_SANS)
        for cx, cy, r in circles:
            nx = min(max(cx, box.x0), box.x1)
            ny = min(max(cy, box.y0), box.y1)
            assert math.hypot(cx - nx, cy - ny) > r, (el.text, cx, cy)


def test_hub_validation():
    steps = ["a", "b", "c"]
    with pytest.raises(ValueError, match="center= and hub="):
        cycle(steps, center="x", hub="y", out_path="/dev/null")
    with pytest.raises(ValueError, match="label"):
        cycle(steps, hub={"label": "  "}, out_path="/dev/null")
    with pytest.raises(ValueError, match="out of range"):
        cycle(steps, hub={"label": "m", "steps": [3]}, out_path="/dev/null")
    with pytest.raises(ValueError, match="not a step label"):
        cycle(steps, hub={"label": "m", "steps": ["z"]}, out_path="/dev/null")


def test_no_hub_output_is_unchanged_by_the_hub_code(tmp_path):
    """A hub-less cycle carries no spoke marker and no hub rect."""
    body = Path(cycle(["a", "b", "c"], out_path=tmp_path / "plain.svg")
                ).read_text(encoding="utf-8")
    assert "spoke-arrow" not in body and 'rx="10"' not in body
