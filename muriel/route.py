"""
muriel.route — send an owner's complaint to the lens that can answer it.

Reads a complaint in the owner's own words ("the pie is FUGGGGLY",
"totally unclear how jets are suppose to work", "too pinbally") and names
the first move, the seats and tools that can settle it, and the ones that
cannot. Run it before convening anything in response to a complaint.

Created because muriel's worst misses on Spinodal (2026-11-05 to 11-07)
were routing errors, not bad judgement inside a seat:

- "the pie is … FUGGGGLY! … /muriel take it" seated the Loupe alone. The
  Loupe judges finish at 4×; it returned no findings and "ship yes". Ugly
  is a taste call, and taste goes to the owner as a side-by-side page.
- The Walker found "five gestures have no visible route" on 11-05. The
  finding was marked fixed when a line of text was added. The owner was
  still writing "totally unclear how jets are suppose to work" on 11-06
  and "not discoverable as is" on 11-07. A discoverability complaint
  closes when the owner retries the first use, not when copy lands.
- A sound sitting fixed 36 spec and safety findings; the owner then cut
  sound as "too pinbally". No seat listens.
- "Too likely to be seen as a $ sign" and "distinct from Protoplasm" are
  readings a brief-anchored seat cannot make; the Stranger can, and
  sibling closeness is the owner's portfolio call.

The table below is cue words → lens. It matches loosely on purpose: the
owner types fast ("shoudl", "FUGGGGLY", "obscruing"). A complaint can hit
several lenses; all are reported, strongest first. A complaint that hits
none is reported as unrouted, and the right move then is to ask the owner
which lens it is, not to seat the default panel.

Usage
-----

.. code-block:: bash

    python -m muriel route "ok, the pie is a nice interaction but it's FUGGGGLY!"
    echo "too pinbally, let's cut sound" | python -m muriel route -
    python -m muriel route --list          # print the routing table
    python -m muriel route --json "..."

Exit 0 when the complaint routes, 1 when it matches no lens, 2 on usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

__all__ = ["LENSES", "Lens", "Route", "main", "route"]


@dataclass(frozen=True)
class Lens:
    id: str
    question: str           # what the owner is actually asking
    cues: tuple[str, ...]   # case-insensitive regexes over the complaint
    first: str              # the first move, before any panel
    seats: tuple[str, ...]  # jury seats that can rule on it, if any
    tools: tuple[str, ...]  # muriel tools / measurements that answer it
    closes_when: str        # what counts as fixed
    wont_settle: str        # the routes that look like answers and are not


# Order is the tie-break: a defect outranks a design question, and a spec
# conflict outranks taste, because both make the design discussion moot.
LENSES: tuple[Lens, ...] = (
    Lens(
        id="defect",
        question="Something does not work.",
        cues=(r"\bdo(es)?\s*n[o']t\s+(do|work|respond)", r"\bdo(es)? nothing\b",
              r"\bcan'?t (close|open|dismiss|exit|get out)", r"\bcannot (close|open|dismiss)",
              r"\bbroken\b", r"\bwon'?t (open|close|load|start|respond)", r"\bno gpu\b",
              r"\bcrash", r"\bfrozen\b", r"\bblank (screen|page)\b"),
        first="Reproduce it in the harness and fix it. Not a jury question.",
        seats=(),
        tools=("a failing test or harness repro",),
        closes_when="The repro passes on the build the owner opens.",
        wont_settle="Any panel. A jury finding on a broken control rates the design of something that does not run.",
    ),
    Lens(
        id="spec",
        question="The build disagrees with what was decided.",
        cues=(r"\bwas(n'?t| not) the (target )?spec", r"\bwe said\b", r"\bthe idea was\b",
              r"\bsupposed? to be\b", r"\bi thought we\b", r"\bwhat happened\b", r"\bmy bad\b",
              r"\bwe (agreed|decided)\b", r"\bnot what (i|we) (asked|meant|wanted)"),
        first="Check the single versioned product spec. If the owner's statement and the spec differ, "
              "ask which wins and update the spec before the UI.",
        seats=(),
        tools=("the product spec, diffed against the build",),
        closes_when="The spec states the rule once and every platform's build matches it.",
        wont_settle="Any panel. Seats judge the artifact against the brief they are given; a stale brief makes them agree with the bug.",
    ),
    Lens(
        id="taste",
        question="Is it beautiful enough to be here?",
        cues=(r"\bugly\b", r"\bf+u+g+l+y\b", r"\bfu+g+g*l+y", r"\bboring\b", r"\bweak\b", r"\bcheap\b",
              r"\bnot (very )?elegant\b", r"\bnot happy with\b", r"\bclunky\b", r"\bprettier\b",
              r"\blooks like (mold|mould|garbage|a mess|crap|clip ?art)", r"\bgross\b", r"\bmeh\b",
              r"\bblah\b", r"\bdated\b", r"\bfeels? excessive\b", r"\bcurves\b", r"\bnuance\b",
              r"\bnot (very )?(nice|pretty|groovy)\b"),
        first="Put one page in front of the owner: two or more options side by side at shipping "
              "size, each with a working link to a live build. Ask which, not whether.",
        seats=("Forger", "Squinter"),
        tools=("side-by-side page", "muriel squint"),
        closes_when="The owner picks an option on the page.",
        wont_settle="The Loupe alone, the Pedant, or a panel that returns no findings. Finish and labels are not taste; "
                    "'no findings, ship yes' on a taste complaint is a routing error.",
    ),
    Lens(
        id="reading",
        question="What does it look like to someone who was not told?",
        cues=(r"\blooks like (a|an)\b", r"\bseen as\b", r"\breads as\b", r"\bmistaken for\b", r"\breminds? me of\b",
              r"\btoo (much )?like\b", r"\bdistinct from\b", r"\bsame as\b", r"\$ ?sign\b",
              r"\btoo (protoplasm|psychodeli)\b", r"\bmore (protoplasm|psychodeli)\b", r"\bknock-?off\b"),
        first="Cold read: seat the Stranger with the brief withheld, at full size and at 1/8. "
              "If the worry is a sibling product, show the owner both products side by side.",
        seats=("Stranger", "Thumbnail"),
        tools=("muriel squint (1/8 companions)", "sibling side-by-side page"),
        closes_when="A cold reader names the intended thing first, and the owner accepts the sibling distance.",
        wont_settle="Seats that read the brief. Once told it is an S, nobody sees the $.",
    ),
    Lens(
        id="discoverability",
        question="Can a first-time person find it and tell what it does?",
        cues=(r"\bunclear\b", r"\bnot (very )?clear\b", r"\bnot discoverable\b", r"\bundiscoverable\b",
              r"\bcan'?t (find|tell|figure)", r"\bnot (very )?(apparent|obvious)\b", r"\bwhat is this\b",
              r"\bhow (do|does|are|is) .{0,40}(work|suppose|supposed)", r"\bwhere('?s| is) the\b",
              r"\bdidn'?t (know|notice|see)\b", r"\bconfus", r"\bhidden\b", r"\blost\b",
              r"\bwhat .{0,20} (is|does) (that|it) (do|mean)"),
        first="Seat the Walker on a first-use task with the rationale withheld, then have the owner "
              "retry that first use on the new build.",
        seats=("Walker", "Stranger"),
        tools=("muriel control-map", "first-use walkthrough filmstrip"),
        closes_when="The owner retries the first use and finds it. Added explanatory text alone does not close it.",
        wont_settle="Marking the finding fixed because a hint or label was added. Single-frame seats, which never "
                    "attempt the task.",
    ),
    Lens(
        id="placement",
        question="Does every control live in one place, and does it earn the space it covers?",
        cues=(r"\brandom places?\b", r"\ball over the place\b", r"\bdifferent( and random)? places\b",
              r"\bconsistent\b", r"\bspawn\w* (buttons?|controls?|panels?|menus?)", r"\bmoves? around\b", r"\bjumps?\b", r"\bbeside\b",
              r"\bnext to\b", r"\bobsc\w*", r"\bcover(s|ing)? the\b", r"\bin the way\b",
              r"\bblocks? the\b", r"\bcorners?\b", r"\bwhere .{0,30}(live|go|belong)\b"),
        first="Harvest a control map and run it; stipulate the wandering and coverage lines before anyone judges.",
        seats=("Walker",),
        tools=("muriel control-map",),
        closes_when="The census passes with every move declared, and the owner accepts the coverage.",
        wont_settle="Panels that walk one journey or judge one frame. Each journey looks coherent; the wandering "
                    "is between journeys.",
    ),
    Lens(
        id="motion",
        question="Does it move well?",
        cues=(r"\bjerky\b", r"\bjanky\b", r"\bjank\b", r"\bnot (very )?fluid\b", r"\bstutter",
              r"\btoo (slow|fast)\b", r"\b(really )+slow\b", r"\bmoving slow\b", r"\blaggy\b", r"\blag\b",
              r"\bframe ?rate\b", r"\bfps\b", r"\bease\b", r"\babrupt\b", r"\bsnappy\b", r"\bsluggish\b",
              r"\bchoppy\b", r"\bfunky\b"),
        first="Capture it moving: a filmstrip at fixed timesteps or a short clip, before and after, "
              "with frame time and simulated speed measured separately.",
        seats=("Walker",),
        tools=("muriel motion (duration policy)", "frame-time trace", "side-by-side clip"),
        closes_when="The owner watches the after clip next to the before and prefers it.",
        wont_settle="Any seat shown stills. A still cannot be jerky.",
    ),
    # Not "audio": the owner says "audio reactivity" for the visuals answering sound.
    Lens(
        id="sound",
        question="Does it sound right?",
        cues=(r"\bpinbal", r"\bsounds?\b", r"\bloud\b", r"\bharsh\b", r"\bclicky\b",
              r"\btinny\b", r"\bchimes?\b", r"\bbeeps?\b", r"\bvolume (is|too|level)", r"\bsfx\b", r"\bmuddy\b"),
        first="Put matched-level clips in front of the owner, A/B. Measure what can be measured "
              "(onset rate and regularity, peak and loudness) and say what the numbers cannot hear.",
        seats=(),
        tools=("A/B clip page", "onset and loudness measurement"),
        closes_when="The owner listens and keeps it.",
        wont_settle="Any seat. Seats read specs and waveforms; none listens. A sound sitting can clear safety "
                    "and spec findings and still ship something the owner cuts.",
    ),
    Lens(
        id="magnitude",
        question="Is the effect the right size?",
        cues=(r"\bsubtle\b", r"\bbrighter\b", r"\bdimmer\b", r"\btoo (bright|dark|dim|big|small|much|little|strong|faint)\b",
              r"\bbarely\b", r"\bcan'?t see\b", r"\bwashed out\b", r"\bcontrast\b", r"\bblends? in\b",
              r"\bseparation\b", r"\bfrom a distance\b", r"\bpops?\b", r"\bmore (of|separation|color|colour)\b",
              r"\bstand out\b"),
        first="Measure it: the squint ladder, the 1/8 thumbnail, contrast numbers, and before/after at "
              "stated parameter values, on one sheet with a link.",
        seats=("Squinter", "Thumbnail"),
        tools=("muriel squint", "muriel contrast", "measurement sheet"),
        closes_when="The owner picks a value from the sheet.",
        wont_settle="Argument without numbers, and a jury on a question a tool answers.",
    ),
    Lens(
        id="wording",
        question="Does the label say what it does?",
        cues=(r"\bsh\w{2,5} be\s*[\"'“‘]", r"\bcall it\b", r"\bwording\b", r"\blabel", r"\bcopy\b",
              r"\btell (the )?users?\b", r"\bin the menu\b", r"\brename\b", r"\bsays\b"),
        first="Seat the Pedant on the text alone and the Stranger on whether each label predicts its action.",
        seats=("Pedant", "Stranger"),
        tools=("muriel aiism",),
        closes_when="A cold reader predicts each labelled action correctly.",
        wont_settle="Seats that see the layout first; a handsome panel hides a vague label.",
    ),
)


@dataclass
class Route:
    lens: Lens
    hits: list[str]   # the text that matched, in complaint order

    def to_dict(self) -> dict:
        lz = self.lens
        return {"lens": lz.id, "question": lz.question, "matched": self.hits, "first": lz.first,
                "seats": list(lz.seats), "tools": list(lz.tools), "closes_when": lz.closes_when,
                "wont_settle": lz.wont_settle}


_COMPILED = [(lens, [re.compile(c, re.IGNORECASE) for c in lens.cues]) for lens in LENSES]


def route(complaint: str) -> list[Route]:
    """Lenses the complaint hits, strongest first (most distinct cue matches; table order breaks ties)."""
    if not isinstance(complaint, str):
        raise TypeError("complaint must be a string")
    # Phones and some editors type curly apostrophes; the cues are written with straight ones.
    complaint = complaint.replace("\u2019", "'").replace("\u2018", "'")
    found = []
    for order, (lens, pats) in enumerate(_COMPILED):
        spans = []
        for p in pats:
            spans.extend((m.start(), m.group(0)) for m in p.finditer(complaint))
        if spans:
            hits = list(dict.fromkeys(text.strip() for _, text in sorted(spans)))
            found.append((-len(hits), order, Route(lens, hits)))
    return [r for *_, r in sorted(found, key=lambda t: (t[0], t[1]))]


def _format(complaint: str, routes: list[Route]) -> str:
    quoted = complaint.strip().replace("\n", " ")
    lines = [f"“{quoted[:160]}{'…' if len(quoted) > 160 else ''}”"]
    if not routes:
        lines.append("UNROUTED: no lens matched. Ask the owner which question this is "
                     "(" + ", ".join(lz.id for lz in LENSES) + ") before seating anyone.")
        return "\n".join(lines)
    for i, r in enumerate(routes):
        lz = r.lens
        lines.append(f"{'→' if i == 0 else '+'} {lz.id}: {lz.question}  [matched: {', '.join(r.hits)}]")
        lines.append(f"    first:  {lz.first}")
        if lz.seats:
            lines.append(f"    seats:  {', '.join(lz.seats)}")
        lines.append(f"    tools:  {', '.join(lz.tools)}")
        lines.append(f"    closes: {lz.closes_when}")
        lines.append(f"    won't settle it: {lz.wont_settle}")
    return "\n".join(lines)


def _table() -> str:
    out = []
    for lz in LENSES:
        out.append(f"{lz.id}: {lz.question}")
        out.append(f"    seats: {', '.join(lz.seats) or '(none: not a jury question)'}")
        out.append(f"    first: {lz.first}")
    return "\n".join(out)


def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m muriel route", description=__doc__.strip().split("\n\n")[1])
    ap.add_argument("complaint", nargs="*", help="the owner's words; '-' reads stdin")
    ap.add_argument("--json", action="store_true", help="emit the routes as JSON")
    ap.add_argument("--list", action="store_true", help="print the routing table and exit")
    a = ap.parse_args(argv)
    if a.list:
        print(json.dumps([Route(lz, []).to_dict() for lz in LENSES], indent=2, ensure_ascii=False)
              if a.json else _table())
        return 0
    text = sys.stdin.read() if a.complaint == ["-"] else " ".join(a.complaint)
    if not text.strip():
        print("route: give the complaint as arguments or '-' for stdin", file=sys.stderr)
        return 2
    routes = route(text)
    if a.json:
        print(json.dumps({"complaint": text.strip(), "routed": bool(routes),
                          "routes": [r.to_dict() for r in routes]}, indent=2, ensure_ascii=False))
    else:
        print(_format(text, routes))
    return 0 if routes else 1


if __name__ == "__main__":
    sys.exit(_main())


main = _main  # public alias for callers outside the muriel CLI
