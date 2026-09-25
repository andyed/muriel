"""``muriel diagram-check``: one gate, fails closed."""

import io
from contextlib import redirect_stdout
from pathlib import Path

from muriel.__main__ import main as muriel_main
from muriel.tools.diagrams.check import check_svg

EXAMPLES = (Path(__file__).resolve().parents[1]
            / "plugins/muriel/skills/compose/examples/diagrams")

NS = 'xmlns="http://www.w3.org/2000/svg"'
HEAD = (f'<svg {NS} role="img" aria-labelledby="t-title t-desc" '
        'viewBox="0 0 400 200"><title id="t-title">T</title>'
        '<desc id="t-desc">D.</desc>'
        '<rect width="400" height="200" fill="#0a0a0f"/>')


def _run(*args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = muriel_main(["diagram-check", *map(str, args)])
    return rc, buf.getvalue()


def _write(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(HEAD + body + "</svg>", encoding="utf-8")
    return p


def test_committed_examples_pass():
    rc, out = _run(*sorted(EXAMPLES.glob("*.svg")))
    assert rc == 0, out


def test_clean_fixture_passes(tmp_path):
    p = _write(tmp_path, "ok.svg",
               '<text x="20" y="40" font-size="12" fill="#e6e4d2">hi</text>')
    assert check_svg(p) == []
    assert _run(p)[0] == 0


def test_no_text_fails_closed(tmp_path):
    p = _write(tmp_path, "blind.svg", '<circle cx="50" cy="50" r="10"/>')
    rc, out = _run(p)
    assert rc == 1 and "[blind]" in out
    # an explicit opt-in for a glyph-only mark still runs the a11y lint
    assert _run(p, "--allow-no-text")[0] == 0


def test_text_the_audit_cannot_color_fails_closed(tmp_path):
    p = _write(tmp_path, "unresolved.svg",
               '<text x="20" y="40" fill="var(--nope)">hi</text>')
    rc, out = _run(p)
    assert rc == 1 and "scored none" in out


def test_contrast_failure_exits_1(tmp_path):
    p = _write(tmp_path, "low.svg",
               '<text x="20" y="40" font-size="12" fill="#444455">dim</text>')
    rc, out = _run(p)
    assert rc == 1 and "[contrast]" in out


def test_a11y_failure_exits_1(tmp_path):
    p = tmp_path / "noa11y.svg"
    p.write_text(f'<svg {NS} viewBox="0 0 400 200">'
                 '<rect width="400" height="200" fill="#000"/>'
                 '<text x="20" y="40" fill="#fff">hi</text></svg>', "utf-8")
    rc, out = _run(p)
    assert rc == 1 and "[a11y]" in out


def test_label_off_canvas_exits_1(tmp_path):
    p = _write(tmp_path, "off.svg",
               '<text x="-200" y="40" font-size="12" fill="#e6e4d2">gone</text>')
    rc, out = _run(p)
    assert rc == 1 and "[labels]" in out


def test_unverified_background_exits_1(tmp_path):
    p = _write(tmp_path, "wedge.svg",
               '<path d="M 100 100 A 80 80 0 1 1 300 100 Z" fill="#335577"/>'
               '<text x="200" y="80" font-size="12" text-anchor="middle" '
               'fill="#ffffff">20°</text>')
    rc, out = _run(p)
    assert rc == 1 and "[contrast-unverified]" in out


def test_missing_file_is_a_usage_error(tmp_path):
    assert _run(tmp_path / "nope.svg")[0] == 2


def test_subcommand_is_listed_in_help():
    buf = io.StringIO()
    with redirect_stdout(buf):
        muriel_main([])
    assert "diagram-check" in buf.getvalue()
