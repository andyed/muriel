"""archetypes — five canonical style archetypes for muriel callers.

Each archetype names a coherent design vocabulary: typography, palette,
grid character, motion class, and editorial voice. Archetypes
**compose with channels** (the output medium): an ``"swiss"`` archetype
× ``"science"`` channel is a Swiss-styled science figure; a
``"luxury_editorial"`` archetype × ``"web"`` channel is an
editorial-styled web page. Not every combination makes sense — see
:attr:`Archetype.serves_channels` for fits each archetype was designed
to support, and :attr:`Archetype.avoid_channels` for combinations
that should be flagged.

The five-archetype taxonomy is inspired by Axium's design gallery
(axiumui.xyz). Names are conceptual — no third-party code, copy, or
prompts are embedded here.

Usage
-----
    from muriel.archetypes import get, ARCHETYPES
    a = get("swiss")
    a.typography       # 'neutral_sans'
    a.palette          # 'monochrome_one_accent'
    a.grid             # 'mathematical'
    a.motion           # 'utility' — bucket from muriel.motion
    a.voice            # 'objective'
    a.serves_channels  # ('science', 'web', 'svg', …)

CLI
---
    python -m muriel.archetypes              # print full catalog
    python -m muriel.archetypes swiss        # detail one archetype
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Literal

__all__ = [
    "Archetype",
    "ARCHETYPES",
    "ARCHETYPE_NAMES",
    "get",
]


Typography = Literal[
    "serif_editorial",          # generous serif, body + display
    "geometric_sans",           # Futura / Avenir / geometric grotesque
    "display_serif_body_sans",  # serif display + sans body, contrast pairing
    "monospace",                # JetBrains Mono / Fira Code / IBM Plex Mono
    "neutral_sans",             # Helvetica / Univers / Akzidenz-Grotesk
]

Palette = Literal[
    "monochrome",               # black on white, no chromatic color
    "bauhaus_primaries",        # red / yellow / blue + black + white
    "alabaster_warm",           # off-white, cream, muted gold accents
    "phosphor_dark",            # near-black bg + phosphor green or amber
    "monochrome_one_accent",    # greys + one chromatic accent (often red)
]

Grid = Literal[
    "asymmetric_whitespace",    # editorial, generous negative space
    "geometric_8px",            # strict 8px baseline, geometric forms
    "editorial_golden",         # golden-ratio columns, magazine pacing
    "fixed_width_cell",         # terminal character cells
    "mathematical",             # 12-col / fibonacci / explicit ratio system
]

# Motion class names map to muriel.motion buckets:
#   utility    → duration ≤ UTILITY_MS    (snappy, sub-perceptual)
#   cinematic  → duration ≥ CINEMATIC_MS  (slow, narrative)
#   minimal    → utility-only, plus a preference for static-by-default
MotionClass = Literal["utility", "cinematic", "minimal"]

Voice = Literal[
    "editorial",                # journalistic, restrained
    "functionalist",            # declarative, no decoration
    "aspirational",             # patrician, slow, elevated
    "technical_terse",          # clipped, dense, no preamble
    "objective",                # clinical, neutral, evidence-led
]


@dataclass(frozen=True)
class Archetype:
    """A named coherent design vocabulary for muriel artifacts."""

    name: str
    title: str
    summary: str
    typography: Typography
    palette: Palette
    grid: Grid
    motion: MotionClass
    voice: Voice
    serves_channels: tuple[str, ...]
    avoid_channels: tuple[str, ...] = ()


ARCHETYPES: dict[str, Archetype] = {
    "minimalist_monochrome": Archetype(
        name="minimalist_monochrome",
        title="Minimalist Monochrome",
        summary=(
            "Editorial serif, black on white, generous whitespace, no chromatic color. "
            "Reads as a long-form essay."
        ),
        typography="serif_editorial",
        palette="monochrome",
        grid="asymmetric_whitespace",
        motion="minimal",
        voice="editorial",
        serves_channels=("web", "svg", "science", "data-report", "infographic"),
        avoid_channels=("terminal",),
    ),
    "bauhaus": Archetype(
        name="bauhaus",
        title="Bauhaus",
        summary=(
            "Functionalist geometry, primary-color triad on white, strict 8px grid, "
            "geometric sans-serif. Form follows function — no decoration."
        ),
        typography="geometric_sans",
        palette="bauhaus_primaries",
        grid="geometric_8px",
        motion="utility",
        voice="functionalist",
        serves_channels=("web", "svg", "infographic", "diagrams", "gaze"),
        avoid_channels=("terminal",),
    ),
    "luxury_editorial": Archetype(
        name="luxury_editorial",
        title="Luxury Editorial",
        summary=(
            "Alabaster tones, display serif + body sans pairing, slow cinematic motion, "
            "editorial pacing. Patrician and unhurried."
        ),
        typography="display_serif_body_sans",
        palette="alabaster_warm",
        grid="editorial_golden",
        motion="cinematic",
        voice="aspirational",
        serves_channels=("web", "interactive", "video"),
        avoid_channels=("terminal", "science"),
    ),
    "terminal_cli": Archetype(
        name="terminal_cli",
        title="Terminal CLI",
        summary=(
            "Monospace on near-black, phosphor accent, fixed-width cell grid, "
            "instant utility motion. Developer-native, no images."
        ),
        typography="monospace",
        palette="phosphor_dark",
        grid="fixed_width_cell",
        motion="utility",
        voice="technical_terse",
        serves_channels=("terminal", "web", "svg"),
    ),
    "swiss": Archetype(
        name="swiss",
        title="Swiss Style",
        summary=(
            "Neutral sans on a mathematical grid, monochrome with a single chromatic "
            "accent (often red), objective tone. The reference vocabulary for science."
        ),
        typography="neutral_sans",
        palette="monochrome_one_accent",
        grid="mathematical",
        motion="utility",
        voice="objective",
        serves_channels=(
            "science", "web", "svg", "infographic", "data-report", "diagrams",
        ),
    ),
}

ARCHETYPE_NAMES: tuple[str, ...] = tuple(ARCHETYPES.keys())

# Friendly aliases for short-form lookups (Andy's example: ``archetype="swiss"``).
# Keys are normalised forms (lowercase, underscores).
_ALIASES: dict[str, str] = {
    "swiss_style": "swiss",
    "minimalist": "minimalist_monochrome",
    "monochrome": "minimalist_monochrome",
    "minimal_mono": "minimalist_monochrome",
    "luxury": "luxury_editorial",
    "editorial": "luxury_editorial",
    "terminal": "terminal_cli",
    "cli": "terminal_cli",
}


def get(name: str) -> Archetype:
    """Look up an archetype by canonical key or alias.

    Case-insensitive; hyphens and underscores interchangeable.
    Raises ``ValueError`` for unknown names with the catalogue listed.
    """
    key = name.strip().lower().replace("-", "_").replace(" ", "_")
    key = _ALIASES.get(key, key)
    if key not in ARCHETYPES:
        raise ValueError(
            f"unknown archetype {name!r}. Known: {', '.join(ARCHETYPE_NAMES)}. "
            f"Aliases: {', '.join(sorted(_ALIASES))}."
        )
    return ARCHETYPES[key]


def _format_one(a: Archetype, *, indent: str = "  ") -> str:
    lines = [
        f"{a.title}  ({a.name})",
        f"{indent}{a.summary}",
        f"{indent}typography : {a.typography}",
        f"{indent}palette    : {a.palette}",
        f"{indent}grid       : {a.grid}",
        f"{indent}motion     : {a.motion}",
        f"{indent}voice      : {a.voice}",
        f"{indent}serves     : {', '.join(a.serves_channels)}",
    ]
    if a.avoid_channels:
        lines.append(f"{indent}avoid      : {', '.join(a.avoid_channels)}")
    return "\n".join(lines)


def _selftest() -> int:
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append(f"{name}: {detail or 'failed'}")

    check("five archetypes registered", len(ARCHETYPES) == 5,
          f"got {len(ARCHETYPES)}")
    check("ARCHETYPE_NAMES matches dict", set(ARCHETYPE_NAMES) == set(ARCHETYPES))

    for key, a in ARCHETYPES.items():
        check(f"{key} name matches key", a.name == key)
        check(f"{key} has summary", len(a.summary) > 20)
        check(f"{key} has at least one serves channel",
              len(a.serves_channels) >= 1)
        check(f"{key} serves channels are tuples of str",
              all(isinstance(c, str) for c in a.serves_channels))

    # Lookup variants.
    check("get('swiss')", get("swiss").name == "swiss")
    check("get('Swiss')", get("Swiss").name == "swiss")
    check("get('swiss-style')", get("swiss-style").name == "swiss")
    check("get('Swiss Style')", get("Swiss Style").name == "swiss")
    check("get('terminal')", get("terminal").name == "terminal_cli")
    check("get('editorial')", get("editorial").name == "luxury_editorial")
    check("get('minimalist')", get("minimalist").name == "minimalist_monochrome")

    try:
        get("never-heard-of-it")
    except ValueError:
        pass
    else:
        check("unknown raises ValueError", False, "did not raise")

    # Motion class values are restricted to the muriel.motion buckets.
    valid_motion = {"utility", "cinematic", "minimal"}
    for key, a in ARCHETYPES.items():
        check(f"{key} motion is valid", a.motion in valid_motion, a.motion)

    if failures:
        for f in failures:
            print(f"FAIL  {f}", file=sys.stderr)
        return 1
    print(f"OK  {len(ARCHETYPES)} archetypes registered, lookups + invariants pass")
    return 0


def _main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if argv and argv[0] == "--selftest":
        return _selftest()
    if not argv:
        for key in ARCHETYPE_NAMES:
            print(_format_one(ARCHETYPES[key]))
            print()
        return 0
    try:
        a = get(argv[0])
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(_format_one(a))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
