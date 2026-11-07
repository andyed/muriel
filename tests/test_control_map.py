"""Tests for muriel.control_map — the control-home census."""
import json

import pytest

from muriel.control_map import check, main

# Shaped like the Spinodal v1 UI that passed three jury rounds: the close
# button and the heat readout each appear somewhere new as the state changes.
WANDERING = {
    "viewport": [390, 844],
    "protected": {"lamp": [100, 120, 190, 600]},
    "states": {
        "rest":      {"controls": {"room": [16, 60, 44, 44], "lamp": [330, 60, 44, 44]}},
        "pie-open":  {"controls": {"room": [16, 60, 44, 44], "lamp": [330, 60, 44, 44],
                                   "close": [170, 400, 44, 44], "heat": [120, 700, 80, 30]}},
        "tool-held": {"controls": {"room": [16, 60, 44, 44], "lamp": [330, 60, 44, 44],
                                   "close": [300, 620, 44, 44], "heat": [240, 300, 80, 30]}},
    },
}


def test_stable_controls_pass():
    r = check({"viewport": [390, 844], "states": {
        "a": {"controls": {"m": [10, 10, 44, 44]}},
        "b": {"controls": {"m": [14, 12, 44, 44]}},   # 4.5 px drift, inside tolerance
    }})
    assert r.problems == []
    assert r.home_count == 1


def test_wandering_controls_fail():
    r = check(WANDERING)
    assert {c.control for c in r.problems} == {"close", "heat"}
    close = next(c for c in r.controls if c.control == "close")
    assert len(close.homes) == 2 and close.max_drift > 200


def test_declared_move_is_reported_not_failed():
    m = dict(WANDERING, moves={"heat": "follows the finger while dragging"})
    r = check(m)
    assert [c.control for c in r.problems] == ["close"]
    heat = next(c for c in r.controls if c.control == "heat")
    assert heat.declared and len(heat.homes) == 2


def test_new_homes_name_the_state():
    r = check(WANDERING)
    assert r.new_homes["pie-open"] == ["close", "heat"]
    assert r.new_homes["tool-held"] == ["close", "heat"]


def test_protected_coverage_is_measured():
    r = check(WANDERING)
    assert r.coverage["rest"]["lamp"] == 0
    assert 0 < r.coverage["pie-open"]["lamp"] < 0.05


def test_default_tolerance_scales_with_viewport():
    assert check({"viewport": [390, 844], "states": {"a": {"controls": {}}}}).tolerance == pytest.approx(15.6)
    assert check({"viewport": [200, 200], "states": {"a": {"controls": {}}}}).tolerance == 12


@pytest.mark.parametrize("bad", [[1, 2, 3], [0, 0, -1, 4], [0, 0, float("nan"), 4], "box"])
def test_bad_boxes_are_rejected(bad):
    with pytest.raises(ValueError):
        check({"states": {"a": {"controls": {"x": bad}}}})


def test_cli_exit_codes(tmp_path, capsys):
    p = tmp_path / "map.json"
    p.write_text(json.dumps(WANDERING))
    assert main([str(p)]) == 1
    assert "WANDERS" in capsys.readouterr().out
    p.write_text(json.dumps(dict(WANDERING, moves={"close": "x", "heat": "y"})))
    assert main([str(p), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["wandering"] == []
    assert main([str(tmp_path / "missing.json")]) == 2
