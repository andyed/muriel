#!/usr/bin/env python3
"""render_diagram_examples.py — regenerate the committed diagram examples.

The specs below are the single source of truth for the SVGs in
``plugins/muriel/skills/compose/examples/diagrams/``. The byte-identity test
in ``tests/test_diagram_labels.py`` renders from these same specs, so a
generator change that alters an example fails that test until this script is
run on purpose.

The rendered files are copied to the two published mirrors,
``docs/examples/diagrams/`` (committed, the built docs site) and
``site-build/examples/diagrams/`` (gitignored local build output, synced only
if present), so the three never drift.

Usage:
    python3 scripts/render_diagram_examples.py            # write + sync
    python3 scripts/render_diagram_examples.py --check    # exit 1 if stale
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from muriel.tools.diagrams.comparison_pair import comparison_pair  # noqa: E402
from muriel.tools.diagrams.cycle import cycle  # noqa: E402
from muriel.tools.diagrams.dendrogram import dendrogram  # noqa: E402
from muriel.tools.diagrams.dag import dag  # noqa: E402
from muriel.tools.diagrams.heat_grid import heat_grid  # noqa: E402
from muriel.tools.diagrams.layer_stack import layer_stack  # noqa: E402
from muriel.tools.diagrams.matrix import matrix  # noqa: E402
from muriel.tools.diagrams.pyramid import pyramid  # noqa: E402
from muriel.tools.diagrams.sankey import sankey  # noqa: E402
from muriel.tools.diagrams.swimlane import swimlane  # noqa: E402
from muriel.tools.diagrams.treemap import treemap  # noqa: E402

EXAMPLES = REPO_ROOT / "plugins/muriel/skills/compose/examples/diagrams"
MIRRORS = (
    REPO_ROOT / "docs/examples/diagrams",
    REPO_ROOT / "site-build/examples/diagrams",
)


def render_examples(out_dir: Path) -> dict[str, str]:
    """Render every committed example into ``out_dir``; name -> path."""
    out_dir = Path(out_dir)
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
            out_path=out_dir / "swimlane-release.svg"),
        "layers-tcpip.svg": layer_stack(
            [{"label": "Application", "tag": "L4", "note": "HTTP, DNS, TLS"},
             {"label": "Transport", "tag": "L3", "note": "TCP, UDP",
              "focal": True},
             {"label": "Internet", "tag": "L2", "note": "IP, ICMP"},
             {"label": "Link", "tag": "L1", "note": "Ethernet, Wi-Fi"}],
            title="The TCP/IP stack", axis_label="abstraction", axis_dir="up",
            out_path=out_dir / "layers-tcpip.svg"),
        "funnel-q2.svg": pyramid(
            [{"label": "Visitors", "sublabel": "all sessions",
              "value": 100000},
             {"label": "Signups", "value": 24000, "annotation": "−76%"},
             {"label": "Activated", "value": 9000, "annotation": "−62%"},
             {"label": "Paid", "value": 2083, "annotation": "−77%"}],
            orientation="down", proportional=True, axis_label="drop-off",
            title="Acquisition funnel — Q2",
            desc=("Funnel with bar widths proportional to count: of 100,000 "
                  "visitors, 24,000 signed up, 9,000 activated and 2,083 "
                  "paid, about 2% end to end. Each step loses between 62% "
                  "and 77% of the one before it."),
            out_path=out_dir / "funnel-q2.svg"),
        "cycle-evolver.svg": cycle(
            ["Learns", "Executes", "Evaluates", "Hypothesizes", "Tests"],
            center="Evolver's\nimprovement\ncycle",
            out_path=out_dir / "cycle-evolver.svg"),
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
            out_path=out_dir / "matrix-sat-opt.svg"),
        # Illustrative values, not measured data: the shape of a result
        # page where an answer box takes clicks from the top organic slot.
        "comparison-pair-serp.svg": comparison_pair(
            [{"label": "Position 1", "a": 38.0, "b": 31.5},
             {"label": "Position 2", "a": 16.5, "b": 17.0},
             {"label": "Position 3", "a": 10.2, "b": 11.8},
             {"label": "Position 4", "a": 7.1, "b": 8.0},
             {"label": "Position 5", "a": 5.4, "b": 5.6},
             {"label": "Position 6", "a": 4.3, "b": 4.1}],
            states=("Ten links", "With answer box"),
            focal="Position 1",
            scale={"min": 0, "max": 40, "unit": "% of clicks"},
            value_format="{:.1f}",
            title="Click share by result position (illustrative)",
            desc=("Illustrative slopegraph, not measured data. Adding an "
                  "answer box lowers position 1's click share from 38.0% "
                  "to 31.5%; positions 2 to 5 each gain between 0.2 and "
                  "1.6 points, and position 6 is roughly flat."),
            out_path=out_dir / "comparison-pair-serp.svg"),
        "comparison-pair-trace.svg": comparison_pair(
            [{"label": "Account in good standing", "a": "PASS", "b": "PASS"},
             {"label": "Within refund window", "a": "PASS", "b": "PASS"},
             {"label": "Amount under auto-limit", "a": "PASS", "b": "FAIL"},
             {"label": "Fraud score", "a": "PASS", "b": "NOT REACHED"},
             {"label": "Auto-approve", "a": "PASS", "b": "NOT REACHED"}],
            states=("Request A", "Request B"),
            title="Why two refund requests end differently",
            desc=("Two refund requests pass the same first two rules; "
                  "request B fails the auto-limit check, so the fraud score "
                  "and auto-approval are never reached for it."),
            out_path=out_dir / "comparison-pair-trace.svg"),
        "sankey-search-sessions.svg": sankey(
            ["Query", "First action", "Outcome"],
            [{"id": "sessions", "stage": "Query", "label": "Search sessions",
              "value": 10000},
             {"id": "organic", "stage": "First action",
              "label": "Organic click", "value": 5800},
             {"id": "ad", "stage": "First action", "label": "Ad click",
              "value": 1400},
             {"id": "noclick", "stage": "First action", "label": "No click",
              "value": 2800},
             {"id": "satisfied", "stage": "Outcome", "label": "Satisfied",
              "value": 6100},
             {"id": "reformulated", "stage": "Outcome",
              "label": "Reformulated", "value": 2700},
             {"id": "abandoned", "stage": "Outcome", "label": "Abandoned",
              "value": 1200}],
            [{"src": "sessions", "dst": "organic", "value": 5800},
             {"src": "sessions", "dst": "ad", "value": 1400},
             {"src": "sessions", "dst": "noclick", "value": 2800},
             {"src": "organic", "dst": "satisfied", "value": 4600},
             {"src": "organic", "dst": "reformulated", "value": 1200},
             {"src": "ad", "dst": "satisfied", "value": 700},
             {"src": "ad", "dst": "reformulated", "value": 700},
             {"src": "noclick", "dst": "satisfied", "value": 800},
             {"src": "noclick", "dst": "reformulated", "value": 800},
             {"src": "noclick", "dst": "abandoned", "value": 1200}],
            focal=["sessions", "ad", "reformulated"],
            unit="sessions",
            title="Search sessions: first action to outcome",
            desc=("Illustrative counts. Of 10,000 search sessions, 5,800 "
                  "start with an organic click, 1,400 with an ad click and "
                  "2,800 with no click. Half of the ad clicks (700 of 1,400) "
                  "end in a reformulated query, against about one in five "
                  "organic clicks (1,200 of 5,800). Of the no-click "
                  "sessions, 800 end satisfied on the results page itself."),
            out_path=out_dir / "sankey-search-sessions.svg"),
        "treemap-serp.svg": treemap(
            [{"label": "Organic results", "value": 7.42},
             {"label": "Ads", "value": 2.91, "focal": True,
              "sublabel": "top and bottom blocks"},
             {"label": "Knowledge panel", "value": 1.84},
             {"label": "Related searches", "value": 0.97},
             {"label": "Navigation", "value": 0.61},
             {"label": "Pagination", "value": 0.22}],
            title="Fixation time by SERP region (illustrative)", unit=" s",
            desc=("Illustrative treemap of mean fixation time per trial by "
                  "search-results-page region, area proportional to time: "
                  "organic results take about half of all fixation time "
                  "(7.42 of 13.97 s), ads about a fifth (2.91 s), and the "
                  "knowledge panel, related searches, navigation and "
                  "pagination share the remaining quarter."),
            out_path=out_dir / "treemap-serp.svg"),
        "dendrogram-eye-movements.svg": dendrogram(
            {"label": "Eye-movement events", "sublabel": "oculomotor record",
             "children": [
                 {"label": "Fixation", "sublabel": "gaze held", "children": [
                     {"label": "Microsaccade", "focal": True},
                     "Drift", "Tremor"]},
                 {"label": "Saccade", "sublabel": "ballistic shift",
                  "children": ["Reflexive", "Volitional"]},
                 {"label": "Smooth pursuit", "sublabel": "tracks a target",
                  "children": ["Open-loop", "Closed-loop"]},
                 {"label": "Blink", "sublabel": "lid closure",
                  "children": ["Spontaneous", "Reflex", "Voluntary"]}]},
            title="Eye-movement events",
            desc=("Taxonomy of eye-movement events in four classes: fixation, "
                  "saccade, smooth pursuit and blink, each split into its "
                  "subtypes. Fixation is not stillness: it contains three "
                  "movements of its own, microsaccades, drift and tremor, and "
                  "the microsaccade is the event under discussion."),
            out_path=out_dir / "dendrogram-eye-movements.svg"),
        "heat-grid-dwell.svg": heat_grid(
            ["Position 1", "Position 2", "Position 3", "Position 4",
             "Position 5", "Position 6–10"],
            ["Navigational", "Informational", "Transactional", "Local"],
            [[412, 588, 471, 436], [298, 521, 402, 365],
             [241, 463, 318, 290], [187, 402, 265, None],
             [164, 371, 228, 203], [118, 296, 176, 149]],
            focal=(0, 1),
            focal_note="informational queries hold the top result longest",
            unit="mean fixation dwell (ms)", row_title="SERP position",
            col_title="Query intent",
            title="Where searchers dwell, by position and intent",
            desc=("Illustrative values, not measured data. Heat grid of mean "
                  "fixation dwell in milliseconds by SERP position (rows 1 "
                  "to 6–10) and query intent (navigational, informational, "
                  "transactional, local). Dwell falls with position in every "
                  "intent column, and the informational column is highest at "
                  "every position; the focal cell, position 1 informational, "
                  "is 588 ms and is excluded from the scale. Position 4 "
                  "local has no measurement."),
            out_path=out_dir / "heat-grid-dwell.svg"),
        "cycle-experiment-icons.svg": cycle(
            [{"label": "Observe", "icon": "observe"},
             {"label": "Hypothesize", "icon": "idea"},
             {"label": "Test", "icon": "test"},
             {"label": "Measure", "icon": "measure"},
             {"label": "Learn", "icon": "learn"}],
            title="Experiment loop",
            desc=("Clockwise five-step experiment loop: observe, hypothesize, "
                  "test, measure, learn, then observe again. Each step has "
                  "an icon that repeats its label."),
            out_path=out_dir / "cycle-experiment-icons.svg"),
        "cycle-agent-hub.svg": cycle(
            [{"label": "Capture", "icon": "observe"},
             {"label": "Research", "icon": "search"},
             {"label": "Decide", "icon": "decide"},
             {"label": "Act", "icon": "ship"},
             {"label": "Measure", "icon": "chart"},
             {"label": "Learn", "icon": "learn"}],
            hub={"label": "Shared memory",
                 "sublabel": "one record, every pass",
                 "steps": ["Capture", "Decide", "Measure", "Learn"]},
            title="Agent operating loop",
            desc=("Clockwise six-step agent loop — capture, research, decide, "
                  "act, measure, learn — around a shared memory. Capture, "
                  "decide, measure and learn write back to the memory; "
                  "research and act only read from it, so they have no "
                  "write-back spoke."),
            out_path=out_dir / "cycle-agent-hub.svg"),
        "dag-serp-causal.svg": dag(
            [{"id": "amb", "label": "Query ambiguity",
              "sublabel": "intent entropy"},
             {"id": "layout", "label": "SERP layout", "sublabel": "module mix"},
             {"id": "ads", "label": "Ad density", "sublabel": "ads above fold"},
             {"id": "dwell", "label": "Dwell time", "sublabel": "per result"},
             {"id": "click", "label": "Click"},
             {"id": "sat", "label": "Satisfaction",
              "sublabel": "post-task survey"}],
            [{"src": "amb", "dst": "dwell"},
             {"src": "layout", "dst": "dwell"},
             {"src": "dwell", "dst": "click"},
             {"src": "ads", "dst": "click"},
             {"src": "click", "dst": "sat"},
             {"src": "sat", "dst": "amb", "back": True,
              "label": "reformulation"}],
            title="Causal model of SERP satisfaction",
            desc=("Illustrative causal model, not a fitted one. Query "
                  "ambiguity and SERP layout both drive dwell time; dwell "
                  "time and ad density both drive the click; the click "
                  "drives post-task satisfaction. One feedback edge: low "
                  "satisfaction leads to a reformulated, differently "
                  "ambiguous next query."),
            out_path=out_dir / "dag-serp-causal.svg"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="report stale examples and exit 1; write nothing")
    args = ap.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        rendered = render_examples(Path(tmp))
        stale = []
        for name, path in rendered.items():
            new = Path(path).read_bytes()
            targets = [EXAMPLES / name] + [
                m / name for m in MIRRORS if m.is_dir()
            ]
            for target in targets:
                if not target.exists() or target.read_bytes() != new:
                    stale.append(target)
                    if not args.check:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(path, target)
    for target in stale:
        verb = "stale" if args.check else "wrote"
        print(f"{verb}: {target.relative_to(REPO_ROOT)}")
    if not stale:
        print("diagram examples up to date")
    return 1 if (args.check and stale) else 0


if __name__ == "__main__":
    raise SystemExit(main())
