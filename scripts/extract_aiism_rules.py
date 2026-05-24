#!/usr/bin/env python3
"""
extract_aiism_rules.py — One-shot extractor that emits muriel's rule tables
as JSON entries compatible with the science-agent aiism-rules.json schema.

Loads the inline `*_RULES` tables from muriel.aiism, maps each entry to the
target JSON shape (with per-rule source attribution), and writes back into
science-agent/src/aiism-rules.json — preserving any existing entries
(e.g. the ARS-derived rules already there).

Usage:
    python3 scripts/extract_aiism_rules.py [--dry-run] [--target=<path>]

Defaults:
    --target=$HOME/Documents/dev/science-agent/src/aiism-rules.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Make the muriel package importable when run from the repo root.
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
sys.path.insert(0, str(REPO_ROOT))

from muriel import aiism  # noqa: E402


# ---------------------------------------------------------------------------
# Per-rule attribution. Maps rule_id → source label written to the JSON.
# Rules not in this dict default to "muriel → Wikipedia/Vale (CC-BY-SA-4.0)"
# because the muriel docstring marks phrase tables as Vale/Wiki-derivative.
# Project-specific rules (referencing muriel-internal naming or local critique)
# are listed explicitly here as unencumbered.
# ---------------------------------------------------------------------------

PROJECT_SPECIFIC = {
    # Hard-artifact rules — LLM tooling residue identified in local sessions.
    "artifact-oaicite",
    "artifact-turn-token",
    "artifact-sandbox-path",
    "artifact-chatgpt-url",
    "artifact-utm-chatgpt",
    "artifact-knowledge-cutoff",
    "artifact-realtime-disclaimer",
    "artifact-refusal-preamble",
    # Single-phrase rules that reference muriel project-internal naming.
    "phrase-earn-their-keep",
    "phrase-locus-of",
    "phrase-unit-at-which",
    "phrase-substrate-licenses",
    "phrase-doing-its-share",
    "phrase-observational-register",
    "phrase-names-the-same-observation",
    "phrase-the-hope-is-that",
    "phrase-looking-into-the-corners",
    "phrase-leaky-cursor-aside",
    "phrase-not-just-but",
    "phrase-regime",
    # Repeated-phrase intensifier rules — local critique of paper-v4 prose.
    "repeat-load-bearing",
    "repeat-structurally",
    "repeat-materially",
    "repeat-meaningfully",
    "repeat-already-compound",
    # Proximity / pattern rules — project-specific cleft tic.
    "doubled-cleft",
}

SRC_PROJECT = "muriel (project-specific; parent-project license)"
SRC_VALE = "muriel → Wikipedia/Vale (CC-BY-SA-4.0)"


def source_for(rule_id: str) -> str:
    return SRC_PROJECT if rule_id in PROJECT_SPECIFIC else SRC_VALE


# ---------------------------------------------------------------------------
# Rule-table → JSON-entry converters
# ---------------------------------------------------------------------------

def from_hard_artifact(entry) -> dict:
    rid, pattern, message = entry
    return {
        "id": rid,
        "kind": "hard-artifact",
        "severity": "error",
        "pattern": pattern,
        "message": message,
        "source": source_for(rid),
    }


def from_single_phrase(entry) -> dict:
    rid, pattern, severity, message = entry
    return {
        "id": rid,
        "kind": "single-phrase",
        "severity": severity,
        "pattern": pattern,
        "message": message,
        "source": source_for(rid),
    }


def from_repeated_phrase(entry) -> dict:
    rid, pattern, max_count, severity, message = entry
    out = {
        "id": rid,
        "kind": "repeated-phrase",
        "severity": severity,
        "pattern": pattern,
        "max_count": max_count,
        "message": message,
        "source": source_for(rid),
    }
    # Some repeated rules also need multiline matching (rule_id-driven in muriel).
    if rid.startswith("repeat-what"):
        out["flags"] = "im"
    return out


def from_cluster(entry) -> dict:
    rid, pattern, threshold, scope, severity, message = entry
    return {
        "id": rid,
        "kind": "cluster",
        "severity": severity,
        "pattern": pattern,
        "threshold": threshold,
        "scope": scope,
        "message": message,
        "source": source_for(rid),
    }


def from_proximity(entry) -> dict:
    rid, pattern, severity, message, max_dist = entry
    return {
        "id": rid,
        "kind": "proximity",
        "severity": severity,
        "pattern": pattern,
        "max_distance_chars": max_dist,
        "message": message,
        "source": source_for(rid),
    }


# Engine-specific rules — declared in JSON for discoverability but the
# detector lives in code (muriel/aiism.py and prose-audit.js separately).
ENGINE_RULES = [
    {
        "id": "sentence-too-long",
        "kind": "engine",
        "severity": "warn",
        "config": {"warn_at_words": 45, "error_at_words": 65},
        "description": "Long-sentence detector. Sentence ≥ warn_at_words → info; ≥ error_at_words → warn. Detector requires per-line splitter; implemented in each engine.",
        "source": SRC_PROJECT,
    },
    {
        "id": "bold-overuse",
        "kind": "engine",
        "severity": "info",
        "config": {"max_per_paragraph": 2},
        "description": "Flags paragraphs with ≥3 bold spans. Requires markdown-aware paragraph segmentation; implemented in each engine.",
        "source": SRC_PROJECT,
    },
    {
        "id": "density-em-dash-line",
        "kind": "engine",
        "severity": "info",
        "config": {"max_per_line": 2},
        "description": "Flags lines with ≥3 em/en dashes. Per-line scan; implemented in each engine.",
        "source": SRC_PROJECT,
    },
]


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def extract_all() -> list[dict]:
    rules: list[dict] = []
    rules.extend(from_hard_artifact(e) for e in aiism.HARD_ARTIFACT_RULES)
    rules.extend(from_single_phrase(e) for e in aiism.SINGLE_PHRASE_RULES)
    rules.extend(from_repeated_phrase(e) for e in aiism.REPEATED_PHRASE_RULES)
    rules.extend(from_cluster(e) for e in aiism.CLUSTER_RULES)
    rules.extend(from_proximity(e) for e in aiism.PROXIMITY_RULES)
    rules.extend(ENGINE_RULES)
    return rules


def merge(existing: dict, new_rules: list[dict]) -> tuple[dict, dict]:
    """Merge new rules into existing JSON object. Returns (merged, stats)."""
    existing_ids = {r["id"] for r in existing.get("rules", [])}
    added = 0
    skipped: list[str] = []
    for rule in new_rules:
        if rule["id"] in existing_ids:
            skipped.append(rule["id"])
            continue
        existing.setdefault("rules", []).append(rule)
        existing_ids.add(rule["id"])
        added += 1
    stats = {"added": added, "skipped": skipped,
             "total_after": len(existing.get("rules", []))}
    return existing, stats


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--target",
                   default=os.path.expanduser(
                       "~/Documents/dev/science-agent/src/aiism-rules.json"))
    p.add_argument("--dry-run", action="store_true",
                   help="Print stats; don't write the file.")
    args = p.parse_args(argv)

    target = Path(args.target)
    if not target.exists():
        print(f"target not found: {target}", file=sys.stderr)
        return 2

    existing = json.loads(target.read_text())
    new_rules = extract_all()
    merged, stats = merge(existing, new_rules)

    print(f"Source tables in muriel.aiism:")
    print(f"  HARD_ARTIFACT_RULES:   {len(aiism.HARD_ARTIFACT_RULES):>3}")
    print(f"  SINGLE_PHRASE_RULES:   {len(aiism.SINGLE_PHRASE_RULES):>3}")
    print(f"  REPEATED_PHRASE_RULES: {len(aiism.REPEATED_PHRASE_RULES):>3}")
    print(f"  CLUSTER_RULES:         {len(aiism.CLUSTER_RULES):>3}")
    print(f"  PROXIMITY_RULES:       {len(aiism.PROXIMITY_RULES):>3}")
    print(f"  ENGINE (declared):     {len(ENGINE_RULES):>3}")
    print()
    print(f"Merge into {target}:")
    print(f"  added:   {stats['added']}")
    print(f"  skipped: {len(stats['skipped'])} (id collision)")
    if stats["skipped"]:
        for sid in stats["skipped"]:
            print(f"    - {sid}")
    print(f"  total after merge: {stats['total_after']}")

    if args.dry_run:
        print("\n(dry run — no file written)")
        return 0

    target.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n")
    print(f"\nWrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
