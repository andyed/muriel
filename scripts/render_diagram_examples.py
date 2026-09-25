#!/usr/bin/env python3
"""render_diagram_examples.py — regenerate the committed diagram examples.

The specs below are the single source of truth for the five SVGs in
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

from muriel.tools.diagrams.cycle import cycle  # noqa: E402
from muriel.tools.diagrams.dendrogram import dendrogram  # noqa: E402
from muriel.tools.diagrams.layer_stack import layer_stack  # noqa: E402
from muriel.tools.diagrams.matrix import matrix  # noqa: E402
from muriel.tools.diagrams.pyramid import pyramid  # noqa: E402
from muriel.tools.diagrams.swimlane import swimlane  # noqa: E402

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
