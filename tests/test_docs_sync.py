"""Every exported diagram generator is documented in the diagrams channel.

``muriel.tools.diagrams.__all__`` is read at test time, so a generator
added to the package fails here until ``channels/diagrams.md`` mentions
it. Fail-closed: an empty ``__all__`` or an unreadable doc is a failure,
and a planted fixture proves the check can trip.
"""

import re
from pathlib import Path

import muriel.tools.diagrams as diagrams

DOC = (Path(__file__).resolve().parents[1]
       / "plugins/muriel/skills/compose/channels/diagrams.md")


def undocumented(names, doc_text: str) -> list[str]:
    """Names with no whole-word mention in ``doc_text``.

    Whole-word, so ``cycle`` is not satisfied by ``recycled``; the word
    boundary is ``[A-Za-z0-9_]``, matching Python identifiers.
    """
    missing = []
    for name in names:
        if not re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])",
                         doc_text):
            missing.append(name)
    return missing


def test_all_is_nonempty():
    assert list(diagrams.__all__), "diagrams.__all__ is empty — nothing checked"


def test_every_exported_generator_is_in_the_diagrams_channel():
    text = DOC.read_text(encoding="utf-8")
    assert text.strip(), f"{DOC} is empty"
    missing = undocumented(diagrams.__all__, text)
    assert not missing, (
        f"exported from muriel.tools.diagrams but not mentioned in "
        f"{DOC.name}: {missing}"
    )


def test_check_trips_on_a_planted_undocumented_name():
    text = DOC.read_text(encoding="utf-8")
    planted = list(diagrams.__all__) + ["zz_planted_generator"]
    assert undocumented(planted, text) == ["zz_planted_generator"]


def test_word_boundary_is_enforced():
    assert undocumented(["cycle"], "use recycled cycles") == ["cycle"]
    assert undocumented(["cycle"], "call `cycle(steps)`") == []
    assert undocumented(["heat_grid"], "heat_grid_v2 only") == ["heat_grid"]
