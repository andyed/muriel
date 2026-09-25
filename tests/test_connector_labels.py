"""Connector labels sit beside the line, never on it.

muriel's rule (channels/diagrams.md, "Connector labels"): a label that
names a connector goes in clear channel space next to the line — no halo,
no opaque mask rect punched through the stroke. The read-back check
reconstructs every label box and every connector segment and fails on any
crossing. Planted fixtures prove it trips on the committed files
themselves, so a pass on the examples is not a blind pass.
"""

import re
from pathlib import Path

import pytest

from muriel.tools.diagrams._labels import connector_label_crossings

EXAMPLES = sorted(
    (Path(__file__).resolve().parents[1]
     / "plugins/muriel/skills/compose/examples/diagrams").glob("*.svg"))

NS = 'xmlns="http://www.w3.org/2000/svg"'


def _svg(body: str) -> str:
    return f'<svg {NS} viewBox="0 0 400 200">{body}</svg>'


def test_examples_exist():
    assert EXAMPLES


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_no_label_sits_on_a_connector(path):
    assert connector_label_crossings(path) == []


def _plant_on_first_connector(svg: str) -> str:
    """Drop a label at the midpoint of the first flow/handoff path."""
    m = re.search(r'<path d="M ([\d.]+) ([\d.]+) L ([\d.]+) ([\d.]+)'
                  r'[^"]*" fill="none"', svg)
    assert m, "no straight connector path in the example to plant on"
    x0, y0, x1, y1 = map(float, m.groups())
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    label = (f'<text x="{mx:.1f}" y="{my + 4:.1f}" font-size="12" '
             f'text-anchor="middle" fill="#e6e4d2">handoff</text>')
    return svg.replace("</svg>", label + "</svg>")


def test_planted_label_on_the_swimlane_example_trips():
    svg = next(p for p in EXAMPLES if p.name == "swimlane-release.svg"
               ).read_text("utf-8")
    hits = connector_label_crossings(_plant_on_first_connector(svg))
    assert {t for t, _ in hits} == {"handoff"}


def test_label_on_a_line_trips():
    svg = _svg('<line x1="0" y1="100" x2="400" y2="100" stroke="#888"/>'
               '<text x="200" y="104" font-size="12" text-anchor="middle">'
               'on it</text>')
    assert [t for t, _ in connector_label_crossings(svg)] == ["on it"]


def test_label_beside_the_line_passes():
    svg = _svg('<line x1="0" y1="100" x2="400" y2="100" stroke="#888"/>'
               '<text x="200" y="92" font-size="12" text-anchor="middle">'
               'beside</text>')
    assert connector_label_crossings(svg) == []


def test_mask_rect_does_not_excuse_the_crossing():
    """Upstream's opaque mask behind the label is exactly what the rule bans."""
    svg = _svg('<path d="M 0 100 L 400 100" fill="none" stroke="#888"/>'
               '<rect x="170" y="90" width="60" height="18" fill="#000"/>'
               '<text x="200" y="104" font-size="12" text-anchor="middle">'
               'masked</text>')
    assert [t for t, _ in connector_label_crossings(svg)] == ["masked"]


def test_filled_shapes_and_marker_geometry_are_not_connectors():
    svg = _svg('<defs><marker id="m"><path d="M0,0 L9,4.5 L0,9 z" '
               'stroke="#888" fill="none"/></marker></defs>'
               '<rect x="100" y="80" width="200" height="40" fill="#222" '
               'stroke="#888"/>'
               '<text x="200" y="104" font-size="12" text-anchor="middle">'
               'in a box</text>')
    assert connector_label_crossings(svg) == []


def test_curved_connector_is_checked_by_its_control_polygon():
    svg = _svg('<path d="M 0 150 Q 200 50 400 150" fill="none" '
               'stroke="#888"/>'
               '<text x="100" y="104" font-size="12" text-anchor="middle">'
               'arc</text>')
    assert [t for t, _ in connector_label_crossings(svg)] == ["arc"]
