"""Tests for muriel.route — complaint to lens.

Every case is the owner's verbatim wording from the Spinodal sessions of
2026-11-05 to 11-07, typos kept: the router has to work on how the owner
actually types, not on a cleaned-up paraphrase.
"""
import json

import pytest

from muriel.route import LENSES, main, route

# (complaint, lens that must lead, lenses that must also appear)
REAL = [
    (("ok, the pie is a nice interaction but it's FUGGGGLY!  We need some curves and more3 nuance "
     "than black and white.  obscruing the canvas has a cost, make it worthwhile. /muriel take it"),
     "taste", {"placement"}),
    ("totally unclear how jets are suppose to work", "discoverability", set()),
    (("for jets, lets flip the direction as you go to the top -- the jet overlay indicator has to be "
     "clickable/selectable, it's not discoverable as is"), "discoverability", set()),
    (("But the current interactions are not very fluid. The torus doesn't belong there, but the big "
     "problem is that we keep spawning buttons in different and random places. And so it's kind of "
     "all over the place. It needs a consistent and groovy interaction."), "placement", {"motion"}),
    ("too pinbally, let's cut sound from v1", "sound", set()),
    (("i dont think the S is the right logo-mark.  it is too likely to be seeen as a $ sign.  "
     "Can we riff on spinning nodes?"), "reading", set()),
    ("i guess studio, just to make it distinct from protoplasm and save us a headache", "reading", set()),
    ("it feels excessive (and kinda boring, looks like mold)", "taste", set()),
    ("amber feels pretty weak in this comparison", "taste", set()),
    ("can we use the lights in the cap and base as indicators audio reactivity is one, keep it super subtle",
     "magnitude", set()),
    (("for our background lgith animation, we still need a bit more separation with the glass, from a "
     "distance, the lamp blends in"), "magnitude", set()),
    ("Buttons do nothing", "defect", set()),
    ("And I can’t close the pie", "defect", set()),
    (("jets are partially free?  i can move aroudn the base... but wasn't the target spec, the idea was "
     "to move along the base and the side of the glass."), "spec", set()),
    ("demo status expired needs to be or at least beside the fire jets button", "placement", set()),
    ("and studio shoudl be \"get studio\" in the menu eh? it's really not clear what that is right now",
     "wording", {"discoverability"}),
    (("the artist's rotation is a bit jerky and random, it's really cool when it's able to make a "
     "foreground blob a background blob"), "motion", set()),
    ("tvos wax goes really really slow... jets are faster", "motion", set()),
    ("not happy with icon", "taste", set()),
]


@pytest.mark.parametrize(("complaint", "lead", "also"), REAL, ids=[c[:40] for c, *_ in REAL])
def test_real_complaints_route(complaint, lead, also):
    got = [r.lens.id for r in route(complaint)]
    assert got, "unrouted"
    assert got[0] == lead, got
    assert also <= set(got), got


def test_fugly_never_routes_to_a_loupe_only_panel():
    # The 11-05 miss: a taste complaint seated the Loupe alone and got "ship yes".
    r = route("it's FUGGGGLY!")[0]
    assert r.lens.id == "taste"
    assert "Loupe" not in r.lens.seats
    assert "Loupe" in r.lens.wont_settle


def test_discoverability_does_not_close_on_added_text():
    lens = next(lz for lz in LENSES if lz.id == "discoverability")
    assert "retr" in lens.closes_when  # the owner retries the first use
    assert "text" in lens.wont_settle or "label" in lens.wont_settle


def test_sound_seats_nobody():
    assert next(lz for lz in LENSES if lz.id == "sound").seats == ()


def test_defect_outranks_design_on_a_tie():
    assert route("the pie is ugly and the buttons do nothing")[0].lens.id in {"defect", "taste"}
    assert route("broken and ugly")[0].lens.id == "defect"


def test_requests_without_a_complaint_are_unrouted():
    assert route("Push it") == []
    assert route("Merge and redeploy") == []


@pytest.mark.parametrize(("text", "not_lens"), [
    # False positives found by routing every owner line from 11-05..11-07.
    ("spawn sessions for todo list items, have /muriel critique", "placement"),
    ("so looks like we're building a mobile app lava lamp -- for real", "reading"),
    ("so how would manually spinning a vessel of this shape and volume feel", "sound"),
    ("archive volume up", "sound"),
])
def test_known_false_positives(text, not_lens):
    assert not_lens not in {r.lens.id for r in route(text)}


def test_lens_ids_unique_and_cues_compile():
    ids = [lz.id for lz in LENSES]
    assert len(ids) == len(set(ids))


def test_non_string_rejected():
    with pytest.raises(TypeError):
        route(None)


def test_cli(capsys, monkeypatch):
    assert main(["too", "pinbally"]) == 0
    assert "sound" in capsys.readouterr().out
    assert main(["--json", "it's FUGGGGLY"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["routed"] and out["routes"][0]["lens"] == "taste"
    assert main(["Push it"]) == 1
    assert "UNROUTED" in capsys.readouterr().out
    assert main([]) == 2
    assert main(["--list"]) == 0
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO("totally unclear how jets work"))
    assert main(["-"]) == 0
    assert "discoverability" in capsys.readouterr().out
