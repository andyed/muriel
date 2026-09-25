"""heat_grid: the fill is the only quantity channel, and it has to be honest.

Every check reads the rendered SVG back — the cells' ``data-*`` bindings,
their rgba fills, the text colours — rather than trusting the generator's
arithmetic. The monotone-fill bound (±0.03) and the data-binding contract
are adapted from the MIT-licensed diagram-design skill (© 2025 Cathryn
Lavery), ``scripts/verify-heatmap.py``.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest

from muriel.contrast import _composite, contrast_ratio, parse_color
from muriel.tools.diagrams import heat_grid
from muriel.tools.diagrams._a11y import lint_a11y
from muriel.tools.diagrams.check import check_svg

NS = "{http://www.w3.org/2000/svg}"
TOL = 0.03

ROWS = ["Position 1", "Position 2", "Position 3", "Position 4"]
COLS = ["Navigational", "Informational", "Transactional"]
VALUES = [[412, 588, 471], [298, 521, None], [241, 463, 318], [0, 402, 265]]


def _render(tmp_path, name="hg.svg", rows=ROWS, cols=COLS, values=VALUES, **kw):
    kw.setdefault("unit", "mean fixation dwell (ms)")
    return Path(heat_grid(rows, cols, values, out_path=tmp_path / name, **kw))


def _cells(path):
    root = ET.parse(path).getroot()
    out = []
    for el in root.iter(f"{NS}rect"):
        if el.get("data-row") is None:
            continue
        m = re.match(r"rgba\(\s*\d+,\s*\d+,\s*\d+,\s*([\d.]+)\)", el.get("fill", ""))
        out.append({
            "row": el.get("data-row"), "col": el.get("data-col"),
            "value": el.get("data-value"),
            "alpha": float(m.group(1)) if m else None,
            "focal": el.get("data-focal") == "true",
            "missing": el.get("data-missing") == "true",
            "box": tuple(float(el.get(k)) for k in ("x", "y", "width", "height")),
            "fill": el.get("fill"),
        })
    return out


def _light_brand():
    return SimpleNamespace(
        colors=SimpleNamespace(background="#f5f5f5", foreground="#1a1a2e",
                               foreground_muted="#33334a", accent="#b3401a"),
        viz=SimpleNamespace(categorical=()),
        typography=SimpleNamespace(body_family=None, mono_family=None),
    )


# ─── Encoding ───────────────────────────────────────────────────────

def _monotone_findings(path):
    cells = [c for c in _cells(path) if not c["focal"] and not c["missing"]]
    cells.sort(key=lambda c: float(c["value"]))
    bad = [(a["value"], a["alpha"], b["value"], b["alpha"])
           for a, b in zip(cells, cells[1:]) if b["alpha"] < a["alpha"] - TOL]
    by_v = {}
    for c in cells:
        by_v.setdefault(c["value"], set()).add(c["alpha"])
    bad += [(v, s) for v, s in by_v.items() if max(s) - min(s) > TOL]
    return bad


@pytest.mark.parametrize("show_values", [True, False])
def test_fill_is_monotone_non_decreasing_in_value(tmp_path, show_values):
    assert _monotone_findings(_render(tmp_path, show_values=show_values)) == []


def test_monotone_check_trips_on_an_inverted_cell(tmp_path):
    """The check must find a real inversion, or its pass means nothing."""
    path = _render(tmp_path, show_values=False)
    svg = path.read_text("utf-8")
    top = max(c["alpha"] for c in _cells(path) if c["alpha"] is not None)
    # give the smallest value (0) the darkest fill
    svg = re.sub(r'(data-value="0" [^>]*fill="rgba\([^)]*, )[\d.]+\)',
                 lambda m: f"{m.group(1)}{top})", svg, count=1)
    path.write_text(svg, "utf-8")
    assert _monotone_findings(path)


def test_smallest_cell_is_still_visible_and_top_is_darker(tmp_path):
    cells = [c for c in _cells(_render(tmp_path)) if c["alpha"] is not None]
    alphas = [c["alpha"] for c in cells]
    assert min(alphas) >= 0.05          # a zero value still separates from paper
    assert max(alphas) > min(alphas)


def test_no_values_uses_the_full_ramp(tmp_path):
    shown = max(c["alpha"] for c in _cells(_render(tmp_path, "a.svg"))
                if c["alpha"] is not None)
    hidden = max(c["alpha"] for c in _cells(_render(tmp_path, "b.svg",
                                                    show_values=False))
                 if c["alpha"] is not None)
    assert hidden == pytest.approx(0.70)
    assert shown < hidden               # the ceiling was solved down for text


def test_legend_is_stepped_swatches_with_numeric_bounds(tmp_path):
    svg = _render(tmp_path).read_text("utf-8")
    assert "linearGradient" not in svg and "radialGradient" not in svg
    assert re.search(r">0–100</text>", svg)
    assert re.search(r">500–600</text>", svg)
    # Every cell alpha is one of the legend swatch alphas: the legend is the scale.
    root = ET.fromstring(svg)
    swatch = {el.get("fill") for el in root.iter(f"{NS}rect")
              if el.get("height") == "16" and el.get("fill", "").startswith("rgba")}
    for c in _cells(_render(tmp_path, "again.svg")):
        if c["alpha"] is not None:
            assert c["fill"] in swatch


# ─── Data bindings ──────────────────────────────────────────────────

def test_every_cell_carries_bindings_that_recompute_the_values(tmp_path):
    cells = _cells(_render(tmp_path))
    assert len(cells) == len(ROWS) * len(COLS)
    got = {(c["row"], c["col"]): c["value"] for c in cells}
    for r, row in enumerate(VALUES):
        for c, v in enumerate(row):
            want = "n/a" if v is None else f"{float(v):g}"
            assert got[(ROWS[r], COLS[c])] == want


def test_none_cell_is_drawn_with_text_never_blank(tmp_path):
    path = _render(tmp_path)
    missing = [c for c in _cells(path) if c["missing"]]
    assert len(missing) == 1 and missing[0]["value"] == "n/a"
    x, y, w, h = missing[0]["box"]
    root = ET.parse(path).getroot()
    inside = [t for t in root.iter(f"{NS}text")
              if x <= float(t.get("x")) <= x + w and y <= float(t.get("y")) <= y + h]
    assert [t.text for t in inside] == ["n/a"]
    assert "url(#" in missing[0]["fill"]


def test_none_cell_text_is_drawn_even_without_values(tmp_path):
    svg = _render(tmp_path, show_values=False).read_text("utf-8")
    assert ">n/a</text>" in svg


# ─── Focal ──────────────────────────────────────────────────────────

def test_focal_is_excluded_from_the_scale_max(tmp_path):
    base = [[10, 20, 30], [40, 50, 60], [70, 80, 90]]
    with_outlier = [row[:] for row in base]
    with_outlier[0][0] = 5000
    a = _cells(_render(tmp_path, "a.svg", rows=ROWS[:3], values=base,
                       focal=(0, 0), unit=None))
    b = _cells(_render(tmp_path, "b.svg", rows=ROWS[:3], values=with_outlier,
                       focal=(0, 0), unit=None))
    # The outlier moves nothing but its own cell.
    strip = lambda cs: [(c["row"], c["col"], c["alpha"]) for c in cs if not c["focal"]]  # noqa: E731
    assert strip(a) == strip(b)
    focal = [c for c in b if c["focal"]]
    assert len(focal) == 1 and focal[0]["value"] == "5000"


def test_focal_value_is_stated_in_the_legend_and_desc(tmp_path):
    svg = _render(tmp_path, focal=("Position 1", "Informational"),
                  focal_note="the top result holds").read_text("utf-8")
    desc = re.search(r"<desc [^>]*>(.*?)</desc>", svg, re.S).group(1)
    assert "Position 1 × Informational = 588 ms" in desc
    assert re.search(r">Position 1 × Informational = 588 ms — excluded from "
                     r"the scale; the top result holds</text>", svg)


def test_focal_on_a_missing_cell_raises(tmp_path):
    with pytest.raises(ValueError, match="focal"):
        _render(tmp_path, focal=(1, 2))


# ─── Refusals ───────────────────────────────────────────────────────

def test_negative_values_raise_and_point_to_diverging(tmp_path):
    bad = [row[:] for row in VALUES]
    bad[0][0] = -3
    with pytest.raises(ValueError, match="diverging"):
        _render(tmp_path, values=bad)


@pytest.mark.parametrize("rows,cols,hint", [
    (["a", "b"], COLS, "bar chart"),
    (ROWS, ["x", "y"], "bar chart"),
    ([f"r{i}" for i in range(8)], COLS, "at most 7"),
    (ROWS, [f"c{i}" for i in range(9)], "at most 8"),
])
def test_budget_limits_raise(tmp_path, rows, cols, hint):
    values = [[1] * len(cols) for _ in rows]
    with pytest.raises(ValueError, match=hint):
        _render(tmp_path, rows=rows, cols=cols, values=values)


def test_ragged_table_raises_rather_than_dropping(tmp_path):
    with pytest.raises(ValueError, match="row"):
        _render(tmp_path, values=VALUES[:3])
    ragged = [row[:] for row in VALUES]
    ragged[2] = ragged[2][:2]
    with pytest.raises(ValueError, match="None"):
        _render(tmp_path, values=ragged)


def test_non_numeric_and_nan_raise(tmp_path):
    for bad_v, exc in (("12", TypeError), (True, TypeError),
                       (float("nan"), ValueError)):
        bad = [row[:] for row in VALUES]
        bad[0][0] = bad_v
        with pytest.raises(exc):
            _render(tmp_path, values=bad)


# ─── Determinism, a11y, the gate ────────────────────────────────────

def test_rendering_is_deterministic(tmp_path):
    a = _render(tmp_path, "d.svg", focal=(0, 1)).read_bytes()
    b = _render(tmp_path / "again", "d.svg", focal=(0, 1)).read_bytes()
    assert a == b


def test_a11y_contract_is_clean(tmp_path):
    svg = _render(tmp_path, focal=(0, 1), row_title="SERP position",
                  col_title="Query intent", title="Dwell").read_text("utf-8")
    assert lint_a11y(svg) == []
    desc = re.search(r"<desc [^>]*>(.*?)</desc>", svg, re.S).group(1)
    for label in ROWS + COLS:
        assert label in desc
    assert not re.search(r"\b(causes?|significant|best|better|proves?)\b", desc)


def _value_text_ratios(path):
    """Each in-cell value label against its own composited cell fill."""
    root = ET.parse(path).getroot()
    bg = parse_color(root.find(f"{NS}rect").get("fill"))
    out = []
    cells = [c for c in _cells(path) if c["alpha"] is not None]
    for t in root.iter(f"{NS}text"):
        x, y = float(t.get("x")), float(t.get("y"))
        for c in cells:
            cx, cy, w, h = c["box"]
            if cx <= x <= cx + w and cy <= y <= cy + h:
                m = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)", c["fill"])
                rgb = tuple(int(m.group(i)) for i in (1, 2, 3))
                behind = _composite(rgb, float(m.group(4)), bg)
                out.append((t.text, contrast_ratio(parse_color(t.get("fill")), behind)))
    return out


@pytest.mark.parametrize("brand", [None, "light"])
def test_every_value_label_clears_8_to_1_on_its_composited_cell(tmp_path, brand):
    b = _light_brand() if brand == "light" else None
    path = _render(tmp_path, focal=(0, 1), row_title="SERP position",
                   col_title="Query intent", title="Dwell", brand=b)
    ratios = _value_text_ratios(path)
    assert len(ratios) == sum(v is not None for row in VALUES for v in row)
    for text, ratio in ratios:
        assert ratio >= 8.0, (text, ratio)
    assert check_svg(path) == []


def test_contrast_check_trips_on_a_sub_floor_value_label(tmp_path):
    path = _render(tmp_path)
    svg = path.read_text("utf-8").replace(
        'fill="#e6e4d2" font-family', 'fill="#3a3a44" font-family', 1)
    path.write_text(svg, "utf-8")
    assert any(r < 8.0 for _, r in _value_text_ratios(path))
    assert any("[contrast]" in f for f in check_svg(path))


def test_text_colour_is_chosen_by_computed_contrast(tmp_path):
    """The chooser is contrast-driven: on a dense fill it returns paper.

    In a rendered grid every value label comes out ink, and that is the
    solve working rather than a fixed colour: the ramp starts at the floor
    (ink's zone) and the ceiling stops at the first fill where no text
    colour clears 8:1, so paper's zone above the dead band is never
    reached. The chooser itself still has to pick paper when the fill
    calls for it.
    """
    from muriel.tools.diagrams._a11y import legible_on
    ink, paper = "#e6e4d2", "#0a0a0f"
    assert legible_on([ink, paper], "rgba(230, 228, 210, 0.9)", paper) == paper
    assert legible_on([ink, paper], "rgba(230, 228, 210, 0.1)", paper) == ink
    fills = {t.get("fill") for t in ET.parse(_render(tmp_path)).getroot()
             .iter(f"{NS}text") if t.text and t.text.isdigit()}
    assert fills == {ink}


def test_long_labels_grow_the_margin_and_cells(tmp_path):
    path = _render(
        tmp_path,
        rows=["Organic result, first position above the fold", "B", "C"],
        cols=["Navigational", "Informational/exploratory", "Tx"],
        values=[[1, 2, 3], [4, 5, 6], [7, 8, 9]], unit=None,
        value_format="{:,.2f} seconds")
    assert check_svg(path) == []
