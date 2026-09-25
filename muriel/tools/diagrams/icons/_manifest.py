"""Curated icon slots for muriel's diagram generators.

Each slot is a name a caller writes (``cycle(..., [{"icon": "measure"}])``)
mapped to the Lucide icon that draws it and a one-line note on what the
slot means. The set is small on purpose: diagram icons are verbs and
concepts that label a *step*, not a catalog of objects. Add a slot when a
real diagram needs it, then rerun ``scripts/build_diagram_icons.py``.

``ALIASES`` lets a caller use the Lucide-ish noun ("eye", "flask") for the
slot named by its verb ("observe", "test"). Aliases never appear in
``GLYPHS``; the resolver maps them first.

Source: Lucide (ISC; some glyphs derived from Feather, MIT). See
``vendor/lucide/LICENSE`` and ``THIRD_PARTY_NOTICES.md``.
"""

from __future__ import annotations

__all__ = ["LUCIDE_VERSION", "SLOTS", "ALIASES"]

# Pinned lucide-static release. Changing it means rerunning
# ``python3 scripts/build_diagram_icons.py --refresh``.
LUCIDE_VERSION = "1.48.0"

# slot -> (lucide icon id, blurb). Order is the catalog order.
SLOTS: dict[str, tuple[str, str]] = {
    # ── process verbs ─────────────────────────────────────────────
    "observe":   ("eye",              "Watch, sense, or collect signals."),
    "measure":   ("ruler",            "Quantify against a scale or metric."),
    "decide":    ("split",            "Choose between branches; a decision gate."),
    "refresh":   ("refresh-cw",       "Iterate; run the loop again."),
    "search":    ("search",           "Look something up; query."),
    "filter":    ("funnel",           "Narrow a set; keep what passes."),
    "compare":   ("scale",            "Weigh options against each other."),
    "test":      ("flask-conical",    "Run an experiment; test a hypothesis."),
    "learn":     ("book-open",        "Read, study, or update understanding."),
    "build":     ("hammer",           "Make or implement."),
    "ship":      ("rocket",           "Release or launch."),
    "review":    ("circle-check",     "Check, approve, or verify."),
    "alert":     ("triangle-alert",   "Warn; a signal needing attention."),
    "exchange":  ("arrow-right-left", "Hand off or trade in both directions."),
    "zoom-in":   ("zoom-in",          "Inspect closely; drill down."),
    # ── actors ────────────────────────────────────────────────────
    "user":      ("user",             "One person or actor."),
    "users":     ("users",            "A group, cohort, or team."),
    # ── artifacts and state ───────────────────────────────────────
    "document":  ("file-text",        "A written artifact: spec, report, note."),
    "database":  ("database",         "Stored records; durable state."),
    "chart":     ("chart-column",     "Results, metrics, or a report."),
    "message":   ("message-square",   "Feedback, a comment, or a conversation."),
    "link":      ("link",             "A connection or reference."),
    "layers":    ("layers",           "Stacked levels or abstraction layers."),
    # ── concepts ──────────────────────────────────────────────────
    "clock":     ("clock",            "Time, cadence, or waiting."),
    "target":    ("target",           "A goal or objective."),
    "idea":      ("lightbulb",        "An idea or hypothesis."),
    "lock":      ("lock",             "A constraint, freeze, or access control."),
    "gear":      ("settings",         "Configure or automate; machinery."),
    "flag":      ("flag",             "A milestone or marker."),
    "brain":     ("brain",            "Cognition, a model, or reasoning."),
}

# alias -> slot. Nouns and near-synonyms a caller is likely to reach for.
ALIASES: dict[str, str] = {
    "eye":              "observe",
    "ruler":            "measure",
    "split":            "decide",
    "iterate":          "refresh",
    "flask":            "test",
    "experiment":       "test",
    "book":             "learn",
    "hammer":           "build",
    "rocket":           "ship",
    "check":            "review",
    "warning":          "alert",
    "arrow-right-left": "exchange",
    "zoom":             "zoom-in",
    "person":           "user",
    "team":             "users",
    "doc":              "document",
    "file":             "document",
    "memory":           "database",
    "time":             "clock",
    "goal":             "target",
    "lightbulb":        "idea",
    "hypothesis":       "idea",
    "settings":         "gear",
    "milestone":        "flag",
}
