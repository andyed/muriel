"""
muriel.control_map — where every control lives, in every state, as fact.

Reads a control map: a JSON census of an interactive UI's settled states,
each listing its visible controls with a bounding box. Reports, per
control, how many distinct screen homes it occupies across states; which
states put a control somewhere it has never been; and how much of the
protected subject (the canvas, the photo, the lamp) each state covers.

Created because a jury walked three rounds over a UI whose controls
appeared in a different place in nearly every state, and passed it. The
owner rejected it within the hour: "we keep spawning buttons in different
and random places." Each walked flow looked coherent on its own; the
wandering only shows when every state is laid side by side. A census
sees all of it, and unlike a reviewer it does not rate a move LOW
because the move is small.

The output is a finding of fact, stipulated before a panel sits
(``references/jury.md#jurisdiction``). The Walker rules on whether a
declared move carries meaning; it does not rule on whether a move
happened.

Control map format
------------------

.. code-block:: json

    {
      "viewport": [390, 844],
      "tolerance": 24,
      "protected": {"lamp": [100, 120, 190, 600]},
      "moves": {"heat-readout": "follows the finger while dragging"},
      "states": {
        "rest":       {"controls": {"menu": [16, 60, 44, 44]}},
        "tool-open":  {"controls": {"menu": [16, 60, 44, 44],
                                    "close": [300, 420, 44, 44]}}
      }
    }

Boxes are ``[x, y, width, height]`` in CSS px. ``tolerance`` (px, default
4% of the shorter viewport side, at least 12) is how far a control's
centre may drift and still count as the same home. ``protected`` names
regions controls should not cover; coverage is reported, never failed,
because covering the subject is sometimes the right call and the jury or
the owner decides whether it earned it. ``moves`` declares controls that
are meant to move, each with a one-line reason; a declared control is
reported but does not fail.

Harvesting a map
----------------

Drive each state with the host's own harness and record every element
that carries ``data-control``:

.. code-block:: js

    const controls = {};
    for (const el of document.querySelectorAll('[data-control]')) {
      const r = el.getBoundingClientRect(), s = getComputedStyle(el);
      if (r.width && r.height && s.visibility !== 'hidden' && +s.opacity > 0.05)
        controls[el.dataset.control] = [r.x, r.y, r.width, r.height].map(Math.round);
    }

One state per settled screen the person can reach: rest, controls awake,
each panel open, each tool active, each mode, a music beat mid-pulse.
The map is only as complete as the states it lists.

Usage
-----

.. code-block:: bash

    python -m muriel.control_map ui-map.json
    python -m muriel.control_map ui-map.json --json

Exit 0 when every undeclared control keeps one home; 1 when any wanders.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["ControlReport", "Home", "MapReport", "check", "main"]

Box = tuple[float, float, float, float]


@dataclass
class Home:
    """One screen position a control occupies, and the states that put it there."""
    centre: tuple[float, float]
    states: list[str] = field(default_factory=list)


@dataclass
class ControlReport:
    control: str
    homes: list[Home]
    declared: str | None  # reason from ``moves``, when the control is meant to move
    max_drift: float      # px between the two furthest-apart homes

    @property
    def wanders(self) -> bool:
        return len(self.homes) > 1 and self.declared is None


@dataclass
class MapReport:
    viewport: tuple[float, float]
    tolerance: float
    states: list[str]
    controls: list[ControlReport]
    new_homes: dict[str, list[str]]           # state -> controls in a never-used position
    coverage: dict[str, dict[str, float]]     # state -> protected region -> fraction covered

    @property
    def problems(self) -> list[ControlReport]:
        return [c for c in self.controls if c.wanders]

    @property
    def home_count(self) -> int:
        """Distinct positions used by any control: the size of the layout's vocabulary."""
        return len(_cluster([h.centre for c in self.controls for h in c.homes], self.tolerance))

    def to_dict(self) -> dict:
        return {
            "viewport": list(self.viewport),
            "tolerance_px": self.tolerance,
            "states": self.states,
            "home_count": self.home_count,
            "control_count": len(self.controls),
            "wandering": [c.control for c in self.problems],
            "controls": [
                {
                    "control": c.control,
                    "homes": [{"centre": [round(v) for v in h.centre], "states": h.states}
                              for h in c.homes],
                    "declared_move": c.declared,
                    "max_drift_px": round(c.max_drift),
                }
                for c in self.controls
            ],
            "new_homes_by_state": self.new_homes,
            "protected_coverage": {s: {k: round(v, 3) for k, v in r.items()}
                                   for s, r in self.coverage.items()},
        }


def _centre(b: Box) -> tuple[float, float]:
    return (b[0] + b[2] / 2, b[1] + b[3] / 2)


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _cluster(points: list[tuple[float, float]], tol: float) -> list[tuple[float, float]]:
    """Greedy single-pass clustering; a point within ``tol`` of a cluster joins it."""
    out: list[tuple[float, float]] = []
    for p in points:
        if not any(_dist(p, c) <= tol for c in out):
            out.append(p)
    return out


def _overlap(a: Box, b: Box) -> float:
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return max(0.0, w) * max(0.0, h)


def _box(v, where: str) -> Box:
    if not (isinstance(v, (list, tuple)) and len(v) == 4
            and all(isinstance(n, (int, float)) and math.isfinite(n) for n in v)):
        raise ValueError(f"{where}: expected [x, y, width, height], got {v!r}")
    if v[2] < 0 or v[3] < 0:
        raise ValueError(f"{where}: negative size {v!r}")
    return (float(v[0]), float(v[1]), float(v[2]), float(v[3]))


def check(source: str | Path | dict) -> MapReport:
    """Read a control map (path or parsed dict) and return its census."""
    data = source if isinstance(source, dict) else json.loads(Path(source).read_text())
    states_in = data.get("states")
    if not isinstance(states_in, dict) or not states_in:
        raise ValueError("control map has no states")
    vw, vh = data.get("viewport", [0, 0])
    tol = data.get("tolerance")
    if tol is None:
        # 4% of the shorter side: a thumb-width on a phone, without excusing a real move.
        tol = max(12.0, 0.04 * min(vw, vh)) if vw and vh else 24.0
    tol = float(tol)
    moves = data.get("moves", {}) or {}
    protected = {k: _box(v, f"protected.{k}") for k, v in (data.get("protected") or {}).items()}

    # control -> list of (state, centre), in state order
    seen: dict[str, list[tuple[str, tuple[float, float]]]] = {}
    boxes: dict[str, dict[str, Box]] = {}
    for state, body in states_in.items():
        ctrls = (body or {}).get("controls", {}) or {}
        boxes[state] = {}
        for cid, raw in ctrls.items():
            b = _box(raw, f"states.{state}.controls.{cid}")
            boxes[state][cid] = b
            seen.setdefault(cid, []).append((state, _centre(b)))

    reports: list[ControlReport] = []
    for cid, occ in seen.items():
        homes: list[Home] = []
        for state, c in occ:
            for h in homes:
                if _dist(c, h.centre) <= tol:
                    h.states.append(state)
                    break
            else:
                homes.append(Home(centre=c, states=[state]))
        drift = max((_dist(a.centre, b.centre) for a in homes for b in homes), default=0.0)
        reports.append(ControlReport(cid, homes, moves.get(cid), drift))
    reports.sort(key=lambda r: (-len(r.homes), r.control))

    # A state that puts any control where no control has been before grows the
    # layout's vocabulary; the person has a new place to look.
    used: list[tuple[float, float]] = []
    new_homes: dict[str, list[str]] = {}
    for state, ctrls in boxes.items():
        fresh = []
        for cid, b in ctrls.items():
            c = _centre(b)
            if not any(_dist(c, u) <= tol for u in used):
                fresh.append(cid)
        used.extend(_centre(b) for b in ctrls.values())
        if fresh and state != next(iter(boxes)):
            new_homes[state] = sorted(fresh)

    coverage: dict[str, dict[str, float]] = {}
    for state, ctrls in boxes.items():
        row = {}
        for name, p in protected.items():
            area = p[2] * p[3]
            # Sum of overlaps can double-count stacked controls; cap at 1.
            row[name] = min(1.0, sum(_overlap(b, p) for b in ctrls.values()) / area) if area else 0.0
        if row:
            coverage[state] = row

    return MapReport((float(vw), float(vh)), tol, list(states_in), reports, new_homes, coverage)


def _format(r: MapReport) -> str:
    lines = [
        (f"{len(r.states)} states, {len(r.controls)} controls, {r.home_count} distinct homes "
         f"(tolerance {r.tolerance:.0f} px)"),
    ]
    for c in r.controls:
        if len(c.homes) == 1:
            continue
        tag = f"declared: {c.declared}" if c.declared else "WANDERS"
        lines.append(f"  {c.control}: {len(c.homes)} homes, up to {c.max_drift:.0f} px apart — {tag}")
        for h in c.homes:
            lines.append(f"      ({h.centre[0]:.0f}, {h.centre[1]:.0f}) in {', '.join(h.states)}")
    for state, cids in r.new_homes.items():
        lines.append(f"  new position in '{state}': {', '.join(cids)}")
    for state, row in r.coverage.items():
        for name, f in row.items():
            if f > 0:
                lines.append(f"  '{state}' covers {f:.0%} of {name}")
    lines.append("PASS: every undeclared control keeps one home" if not r.problems
                 else f"FAIL: {len(r.problems)} control(s) wander without a declared reason")
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m muriel.control_map", description=__doc__.split("\n\n")[0])
    ap.add_argument("map", help="control map JSON")
    ap.add_argument("--json", action="store_true", help="emit the report as JSON")
    a = ap.parse_args(argv)
    try:
        r = check(a.map)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"control_map: {e}", file=sys.stderr)
        return 2
    print(json.dumps(r.to_dict(), indent=2) if a.json else _format(r))
    return 1 if r.problems else 0


if __name__ == "__main__":
    sys.exit(_main())


main = _main  # public alias for callers outside the muriel CLI
