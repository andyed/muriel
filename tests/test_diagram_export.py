"""Strict SVG-1.1 export: no rgba()/transparent left, same colours rendered."""

import io
import re
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from muriel.__main__ import main as muriel_main
from muriel.contrast import _color_alpha, _composite, audit_svg, parse_color
from muriel.tools.diagrams import engine_sectors_overlay, foveal_overlay
from muriel.tools.diagrams._a11y import lint_a11y
from muriel.tools.diagrams._export import png_scale, strict_svg
from muriel.tools.diagrams.check import check_svg

EXAMPLES = sorted(
    (Path(__file__).resolve().parents[1]
     / "plugins/muriel/skills/compose/examples/diagrams").glob("*.svg"))

# A paint value strict importers can't read, anywhere in an attribute,
# a style declaration, or a <style> rule.
_BAD_PAINT = re.compile(
    r"""(?:fill|stroke|stop-color|flood-color)\s*[=:]\s*["']?\s*"""
    r"""(?:rgba?\(|transparent|#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{4}\b)""",
    re.IGNORECASE)


def _svgs(tmp_path):
    """Committed examples plus the overlays, which lean hardest on rgba."""
    out = list(EXAMPLES)
    for name, gen in (("fov.svg", foveal_overlay),
                      ("eng.svg", engine_sectors_overlay)):
        path = tmp_path / name
        gen(verbosity=3, out_path=path)  # returns markup; the file is written
        out.append(path)
    return out


def test_examples_exist():
    assert EXAMPLES


def test_committed_examples_actually_use_rgba():
    """Otherwise the round-trip below proves nothing."""
    assert any(_BAD_PAINT.search(p.read_text("utf-8")) for p in EXAMPLES)


# ─── Unit cases ─────────────────────────────────────────────────────

@pytest.mark.parametrize("src, want", [
    ('<rect fill="rgba(230, 228, 210, 0.04)"/>',
     '<rect fill="#e6e4d2" fill-opacity="0.04"/>'),
    ('<rect fill="rgba(230,228,210,.04)" stroke="rgba(1,2,3,0.5)"/>',
     '<rect fill="#e6e4d2" stroke="#010203" fill-opacity="0.04" '
     'stroke-opacity="0.5"/>'),
    # an opacity already on the element is multiplied, not overwritten
    ('<rect fill="rgba(10,20,30,0.5)" fill-opacity="0.8"/>',
     '<rect fill="#0a141e" fill-opacity="0.4"/>'),
    ('<g fill="transparent"></g>', '<g fill="none"></g>'),
    ('<rect fill="#ff000080"/>', '<rect fill="#ff0000" fill-opacity="0.502"/>'),
    ('<rect fill="#f008"/>', '<rect fill="#ff0000" fill-opacity="0.5333"/>'),
    ('<rect fill="rgb(255 0 0 / 50%)"/>',
     '<rect fill="#ff0000" fill-opacity="0.5"/>'),
    ('<stop stop-color="rgba(0,0,0,0.25)"/>',
     '<stop stop-color="#000000" stop-opacity="0.25"/>'),
    ('<rect style="fill: rgba(255,0,0,0.5); fill-opacity: 0.5"/>',
     '<rect style="fill: #ff0000; fill-opacity: 0.25"/>'),
    ('<style>.a{fill:rgba(0,0,0,.2)}</style>',
     '<style>.a{fill: #000000; fill-opacity: 0.2}</style>'),
])
def test_unit_rewrites(src, want):
    assert strict_svg(src) == want


@pytest.mark.parametrize("src", [
    '<rect fill="#e6e4d2" fill-opacity="0.3"/>',
    '<rect fill="none" stroke="currentColor"/>',
    '<rect fill="url(#g)"/>',
    '<text fill="#fff">fill="rgba(1,2,3,0.4)" is text, not paint</text>',
    '<rect fill="rgba(1,2,3,1)"/>'.replace("rgba(1,2,3,1)", "#010203"),
])
def test_already_strict_is_untouched(src):
    assert strict_svg(src) == src


def test_opaque_rgba_gets_no_opacity_attribute():
    assert strict_svg('<rect fill="rgba(1,2,3,1)"/>') == '<rect fill="#010203"/>'


# ─── Round trip on real output ──────────────────────────────────────

def test_round_trip_leaves_no_rgba_and_is_idempotent(tmp_path):
    for p in _svgs(tmp_path):
        src = p.read_text("utf-8")
        out = strict_svg(src)
        assert not _BAD_PAINT.search(out), (p.name, _BAD_PAINT.search(out))
        assert strict_svg(out) == out, p.name
        ET.fromstring(out)  # still well-formed
        assert lint_a11y(out) == [], p.name


def _painted(svg: str):
    """(tag, fill as (rgb, alpha)) for every element with a fill, in order."""
    out = []
    for el in ET.fromstring(svg).iter():
        fill = el.get("fill")
        if fill is None or fill in ("none",) or fill.startswith("url("):
            continue
        rgb = parse_color(fill)
        if rgb is None:
            continue
        alpha = _color_alpha(fill) * float(el.get("fill-opacity", "1"))
        out.append((el.tag, rgb, alpha))
    return out


@pytest.mark.parametrize("bg", [(10, 10, 15), (250, 250, 248)])
def test_every_fill_composites_to_the_same_colour(tmp_path, bg):
    for p in _svgs(tmp_path):
        src = p.read_text("utf-8")
        before, after = _painted(src), _painted(strict_svg(src))
        assert len(before) == len(after), p.name
        for (t0, rgb0, a0), (t1, rgb1, a1) in zip(before, after):
            assert t0 == t1
            c0 = _composite(rgb0, a0, bg)
            c1 = _composite(rgb1, a1, bg)
            assert max(abs(x - y) for x, y in zip(c0, c1)) <= 1, (
                p.name, rgb0, a0, rgb1, a1)


def test_contrast_audit_is_unchanged(tmp_path):
    """Every text run scores against the same background before and after."""
    for p in _svgs(tmp_path):
        out = tmp_path / f"strict-{p.name}"
        out.write_text(strict_svg(p.read_text("utf-8")), "utf-8")
        key = lambda e: (e.fill_rgb, e.bg_rgb, e.count)  # noqa: E731
        with redirect_stdout(io.StringIO()):
            a = sorted(map(key, audit_svg(p, print_table=False)))
            b = sorted(map(key, audit_svg(out, print_table=False)))
        assert len(a) == len(b), p.name
        for (f0, b0, n0), (f1, b1, n1) in zip(a, b):
            assert n0 == n1
            assert max(abs(x - y) for x, y in zip(f0 + b0, f1 + b1)) <= 1


def test_diagram_check_passes_on_strict_examples(tmp_path):
    for p in EXAMPLES:
        out = tmp_path / p.name
        out.write_text(strict_svg(p.read_text("utf-8")), "utf-8")
        assert check_svg(out) == [], p.name


# ─── CLI ────────────────────────────────────────────────────────────

def _run(*args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = muriel_main(["diagram-export", *map(str, args)])
    return rc, buf.getvalue()


def test_cli_writes_strict_output(tmp_path):
    src = next(p for p in EXAMPLES if p.name == "swimlane-release.svg")
    out = tmp_path / "out.svg"
    rc, _ = _run("--strict", src, "-o", out, "--check")
    assert rc == 0
    assert "rgba(" not in out.read_text("utf-8")


def test_cli_without_strict_is_a_usage_error(tmp_path):
    assert _run(EXAMPLES[0])[0] == 2


def test_cli_missing_file_is_a_usage_error(tmp_path):
    assert _run("--strict", tmp_path / "nope.svg")[0] == 2


# ─── Raster scale rule ──────────────────────────────────────────────

@pytest.mark.parametrize("vb, target, want", [
    (960, 1200, 1.25),
    (1280, 2560, 2.0),
    (1280, 640, 1.0),    # never below 1
    (320, 4000, 4.0),    # never above 4
])
def test_png_scale_is_clamped(vb, target, want):
    assert png_scale(vb, target) == pytest.approx(want)


def test_png_scale_rejects_nonpositive():
    with pytest.raises(ValueError):
        png_scale(0, 100)
