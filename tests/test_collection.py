"""muriel.collection against Wunderkammer's collection validator.

Four layers:

1. Ports of every case in Wunderkammer's ``tests/collection.test.mjs``,
   the suite behind ``wall/collection.mjs``'s ``validateCollection()``.
2. One test per rule: plant a single violation in a valid document and
   expect exactly that problem, so a rule that stops firing, or starts
   firing on its neighbours, fails here.
3. The builder and CLI: build output validates, and exit codes hold.
4. Differential checks against the reference itself, run with Node when a
   Wunderkammer checkout is present (``WUNDERKAMMER_DIR``, default
   ``~/Documents/dev/wunderkammer-readme``) and skipped cleanly otherwise:
   the same documents through both validators, the same URLs through both
   URL parsers.

   The validators are compared at pinned commits, not at whatever the
   checkout has checked out. ``REFERENCE`` names one Wunderkammer commit
   for each release in ``muriel.collection.RELEASES``, and each run reads
   that commit's validator from the checkout's object store with
   ``git show``. Every run checks every release, and the result does not
   change when the checkout moves. A separate test fails when the
   checkout's validator files match no pinned commit: that is the signal
   to port Wunderkammer's change and pin the new commit.

   A commit between releases that changes the validator files but no rule
   goes in ``EQUIVALENT``, mapped to the release it validates as. The
   checkout test accepts it, and the differential test runs it against
   that release on every run, so the claim stays checked.
"""

import copy
import json
import os
import random
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

from muriel import collection as col
from muriel import _whatwg_url
from muriel.collection import LIMITS, RELEASES, build, format_problems, validate

BASE = "https://host.example/c/collection.json"
ROOT = Path(__file__).resolve().parent.parent
WK = Path(os.environ.get("WUNDERKAMMER_DIR", Path.home() / "Documents/dev/wunderkammer-readme"))
PSYCHODELI = WK / "examples/psychodeli/collection.json"
#: The Wunderkammer commit each release is compared against (layer 4).
REFERENCE = {
    "0.1.0": "caadd2e558e94eb7df109e9c389cbfccfef23781",   # tag v0.1.0
    "0.2.0": "dc16ee877a5c165f0fdec8beec0cd33847a6ce40",   # tag v0.2.0, with ui.nouns
    "0.3.0": "04c13dede6aa0a8e0dc133eaf62889582af31f21",   # tag v0.3.0, the same collection fields as 0.2.0
}
#: Unreleased Wunderkammer commits whose validator files differ from every
#: pin's but validate as the mapped release does (layer 4).
EQUIVALENT = {
    "1dbda0c5009a2b24e5d8a8b554ee2bd01874cfac": "0.2.0",   # adds the collectionImages() export
}
#: Every (release, commit) the differential tests run.
PINS = [*REFERENCE.items(), *((release, commit) for commit, release in EQUIVALENT.items())]
#: wall/collection.mjs and every module it imports.
VALIDATOR_FILES = ("wall/collection.mjs", "wall/facet-counts.mjs")
UI_FIELDS = {"0.1.0": "title, defaultGroup, facetOrder, facetLabels, hiddenFacets",
             "0.2.0": "title, defaultGroup, facetOrder, facetLabels, hiddenFacets, nouns",
             "0.3.0": "title, defaultGroup, facetOrder, facetLabels, hiddenFacets, nouns"}


def doc(**over):
    d = {
        "format": "wunderkammer.collection", "version": 1, "corpus": {"id": "example:covers"},
        "ui": {"title": "Covers", "defaultGroup": "decade", "facetOrder": ["decade", "genre"],
               "facetLabels": {"decade": "release decade"}},
        "clips": [
            {"id": "a", "title": "A", "cover": "https://img.example/a.webp",
             "props": {"decade": "1980s", "genre": ["pop", "electronic"]}, "sourceUrl": "https://example.org/a"},
            {"id": "b", "title": "B", "cover": "covers/b.webp", "props": {"decade": "1990s", "genre": "pop"},
             "captured": "1994-05"},
        ],
    }
    d.update(over)
    return d


def sprite_doc(**over):
    d = doc(
        sheets=[{"src": "sheets/p64.webp", "edge": 64, "width": 140, "height": 40},
                {"src": "sheets/p480.webp", "edge": 480, "width": 968, "height": 274}],
        clips=[
            {"id": "a", "title": "A", "props": {"decade": "1980s"}, "sheetSlots": [[0, 2, 2, 64, 36], [1, 2, 2, 480, 270]]},
            {"id": "b", "title": "B", "props": {"decade": "1990s"}, "sheetSlots": [[0, 70, 2, 64, 36], [1, 486, 2, 480, 270]]},
        ],
    )
    d.update(over)
    return d


def problems_of(d, base_url=BASE, release=col.WUNDERKAMMER):
    problems = validate(d, base_url=base_url, release=release)
    assert problems, "expected problems, got a valid document"
    return list(problems)


def has(problems, start, fragment):
    assert any(p.startswith(start) and fragment in p for p in problems), \
        f"{start} … {fragment}\n" + "\n".join(problems)


# ─── 1. ports of tests/collection.test.mjs ───────────────────────────────

DERIVED = {"tags": {}, "source": {}, "kind": {}, "captured": {"1994-05": 1},
           "decade": {"1980s": 1, "1990s": 1}, "genre": {"pop": 2, "electronic": 1}}


def test_a_minimal_collection_validates_and_derives_facet_counts():
    problems = validate(doc())
    assert problems == [] and problems.warnings == []
    # The JS test reads the derived counts back; here, supplying exactly
    # those counts must draw no warning, and any other counts must.
    assert validate(doc(facets=DERIVED)).warnings == []
    assert col._facets(doc()["clips"]) == DERIVED


def test_every_problem_is_reported_with_its_path_in_one_list():
    bad = doc(format="wunderkammer", vault="/private/vault", extra=1)
    del bad["corpus"]
    bad["clips"][0]["sourceUrl"] = "javascript:alert(1)"
    bad["clips"][1]["cover"] = "data:text/html,<script>alert(1)</script>"
    bad["clips"][1]["captured"] = "May 1994"
    bad["clips"].append({"id": "a", "image": "x.png"})
    problems = problems_of(bad)
    has(problems, "format", "wunderkammer.collection")
    has(problems, "collection.vault", "server response")
    has(problems, "collection.extra", "supported: format")
    has(problems, "corpus", "must be an object")
    has(problems, "clips[0].sourceUrl", "http(s)")
    has(problems, "clips[1].cover", "data:image/")
    has(problems, "clips[1].captured", "ISO date")
    has(problems, "clips[2]", "repeats the identity of clips[0]")
    has(problems, "clips[2].image", "put other attributes in props")


@pytest.mark.parametrize("source_url", [
    "javascript:alert(1)", "JAVASCRIPT:alert(1)", "data:text/html,x", "file:///etc/passwd", "obsidian://open?vault=x",
])
def test_link_schemes_are_http_only(source_url):
    assert any(p.startswith("clips[0].sourceUrl") for p in problems_of(doc(clips=[{"id": "a", "sourceUrl": source_url}])))


def test_url_is_http_or_an_opaque_urn_identity():
    assert any(p.startswith("clips[0].url") for p in problems_of(doc(clips=[{"id": "a", "url": "javascript:alert(1)"}])))
    assert validate(doc(clips=[{"id": "a", "url": "urn:clipwall:image:abc"}])) == []


def test_relative_media_and_links_resolve_against_the_document_url():
    clip = {"id": "a", "cover": "covers/a.webp", "coverVariants": [{"src": "../small/a.webp", "width": 128}],
            "media": [{"src": "/full/a.png"}], "sourceUrl": "about.html"}
    assert validate(doc(clips=[clip]), base_url=BASE) == []
    # Resolution is real: a relative url and its absolute spelling are one identity.
    twins = [{"id": "a", "url": "about.html"}, {"id": "b", "url": "https://host.example/c/about.html"}]
    assert validate(doc(clips=twins), base_url=BASE) == [
        'clips[1] repeats the identity of clips[0] (url "https://host.example/c/about.html")']
    # Without a base, a relative image stays page-relative and a relative link is refused.
    assert validate(doc()) == []
    assert validate(doc(clips=[{"id": "a", "sourceUrl": "about.html"}])) == [
        "clips[0].sourceUrl must be an absolute http(s) URL"]


def test_props_are_scalars_or_arrays_of_scalars_and_cannot_be_hidden_by_clip_fields():
    problems = problems_of(doc(clips=[{"id": "a", "props": {
        "title": "x", "score": float("inf"), "nested": {"a": 1}, "ok": [1, "two", True]}}]))
    assert any(p.startswith("clips[0].props.title") and "hidden" in p for p in problems)
    assert any(p.startswith("clips[0].props.score") for p in problems)
    assert any(p.startswith("clips[0].props.nested") for p in problems)
    assert not any(p.startswith("clips[0].props.ok") for p in problems)


def test_supplied_facet_counts_are_replaced_with_a_warning_only_when_they_disagree():
    assert validate(doc(facets=DERIVED)).warnings == []
    assert validate(doc(facets={"decade": {"1980s": 99}})).warnings == [
        "facets differ from the counts derived from clips; the derived counts are used"]


def test_problem_lists_are_capped_and_say_how_many_were_left_out():
    clips = [{"id": f"c{i}", "sourceUrl": "ftp://x"} for i in range(40)]
    problems = validate(doc(clips=clips))
    assert len(problems) == LIMITS["problems"] == 25
    assert problems.overflow == 15 and problems.total == 40
    message = format_problems(problems)
    assert "(40 problems)" in message
    assert message.endswith("- …and 15 more")


def test_ui_nouns_names_an_item_and_its_plural_both_are_required_words():
    # Added after 0.1.0. The JS test's second half, a server payload's
    # ui.nouns surviving toCollection(), is not ported (see below).
    nouns = {"item": "frame", "items": "frames"}
    assert validate(doc(ui={"title": "Frames", "nouns": nouns}), release="0.2.0") == []
    problems = problems_of(doc(ui={"nouns": {"item": "frame", "plural": "frames"}}), release="0.2.0")
    has(problems, "ui.nouns.plural", "supported: item, items")
    has(problems, "ui.nouns.items", "non-empty string")
    has(problems_of(doc(ui={"nouns": "frames"}), release="0.2.0"), "ui.nouns", "must be an object")
    has(problems_of(doc(ui={"nouns": {"item": "x" * 41, "items": "xs"}}), release="0.2.0"), "ui.nouns.item ", "")


def test_a_server_payload_is_refused_until_converted():
    # toCollection() is the reference's converter and is not ported; what is
    # ported is the boundary it exists for. A raw /api/clips payload is
    # refused by name, and its converted form validates.
    payload = {"clips": [{"id": "a", "title": "A", "url": "urn:clipwall:image:a", "tags": [], "props": {"year": "2026"},
                          "cover": "media/a.webp", "editUri": "obsidian://x", "palette": ["#112233"]}],
               "corpus": {"id": "demo", "revision": "r1"}, "facets": {}, "vault": "/srv/private/vault",
               "adapters": ["images"], "generated": "now", "ui": {"title": "Demo"}}
    problems = problems_of(payload)
    for key in ("vault", "adapters", "generated"):
        assert f"collection.{key} belongs to a wunderkammer server response; a collection document does not carry it" in problems
    has(problems, "clips[0].editUri", "put other attributes in props")
    converted = {"format": "wunderkammer.collection", "version": 1, "corpus": {"id": "demo", "revision": "r1"},
                 "ui": {"title": "Demo"},
                 "clips": [{k: v for k, v in payload["clips"][0].items() if k != "editUri"}],
                 "viewState": {"version": 1, "mode": "mountain", "groupKey": "year", "piles": []}}
    assert validate(converted) == []


def test_the_shared_facet_counter_matches_the_server_shape_and_tolerates_clips_without_tags():
    clips = [{"tags": ["x", "y"], "source": "s", "kind": "page", "captured": "2026-01-02",
              "props": {"color": ["red", "blue"], "empty": ""}}, {"props": {"color": "red"}}]
    assert col._facets(clips) == {"tags": {"x": 1, "y": 1}, "source": {"s": 1}, "kind": {"page": 1},
                                  "captured": {"2026-01": 1}, "color": {"red": 2, "blue": 1}}


def test_a_collection_may_ship_its_covers_as_sprite_sheet_cells():
    problems = validate(sprite_doc(), base_url=BASE)
    assert problems == [] and problems.warnings == []


@pytest.mark.parametrize("src", ["javascript:alert(1)", "data:text/html,x", "file:///etc/passwd", "obsidian://open?vault=x"])
def test_sheet_sources_follow_the_image_scheme_rule(src):
    bad = sprite_doc()
    bad["sheets"][1]["src"] = src
    assert any(p.startswith("sheets[1].src") and "data:image/" in p for p in problems_of(bad))


def test_a_data_image_sheet_source_is_accepted():
    ok = sprite_doc()
    ok["sheets"][0]["src"] = "data:image/png;base64,iVBORw0KGgo="
    assert validate(ok) == []


def test_every_sheet_cell_is_checked_against_the_sheet_it_points_into():
    bad = sprite_doc()
    bad["sheets"].append({"src": "sheets/x.webp", "edge": 0, "width": 10.5, "height": 99999})
    bad["clips"][0]["sheetSlots"] = [[0, 2, 2, 64, 36], [0, 70, 2, 64, 36]]   # two cells in one level
    bad["clips"][1]["sheetSlots"] = [[0, 100, 2, 64, 36], [5, 0, 0, 1, 1], [1, 2, 2, 480, "270"], [2, 0, 0, 1, 1]]
    bad["clips"] += [{"id": "c", "sheetSlots": [[1, 0, 0, 481, 100]]}, {"id": "d", "sheetSlots": "all"}]
    problems = problems_of(bad)
    has(problems, "sheets[2].edge", "integer from 1")
    has(problems, "sheets[2].width", "integer from 1")
    has(problems, "sheets[2].height", "integer from 1")
    has(problems, "clips[0].sheetSlots[1]", "repeats the 64 px level")
    has(problems, "clips[1].sheetSlots[0]", "inside sheets[0] (140×40)")
    has(problems, "clips[1].sheetSlots[1]", "sheets[5], which does not exist")
    has(problems, "clips[1].sheetSlots[2]", "five integers")
    has(problems, "clips[1].sheetSlots[3]", "sheets[2], which is not valid")
    has(problems, "clips[2].sheetSlots[0]", "larger than its sheet's edge (480)")
    has(problems, "clips[3].sheetSlots", "[sheet, x, y, w, h]")


def test_cells_need_a_sheets_list_and_a_sheet_no_cell_uses_is_a_warning():
    orphan = sprite_doc()
    del orphan["sheets"]
    assert any(p.startswith("clips[0].sheetSlots") and "top-level sheets" in p for p in problems_of(orphan))
    unused = sprite_doc()
    unused["sheets"].append({"src": "sheets/extra.webp", "edge": 160, "width": 10, "height": 10})
    warnings = validate(unused).warnings
    assert any("sheets [2]" in w and "nothing loads them" in w for w in warnings), warnings
    assert any(p.startswith("sheets") and "1 to" in p for p in problems_of(sprite_doc(sheets=[])))


def test_images_sheets_says_what_cells_are_when_a_clip_also_has_a_file():
    assert validate(sprite_doc(images={"cors": True, "sheets": "covers"})) == []
    assert validate(sprite_doc(images={"sheets": "overview"})) == []
    assert any(p.startswith("images.sheets") and "overview, covers" in p
               for p in problems_of(sprite_doc(images={"sheets": "full"})))


# ─── the shipped example ─────────────────────────────────────────────────

def test_the_psychodeli_example_validates():
    if not PSYCHODELI.is_file():
        pytest.skip(f"no Wunderkammer checkout at {WK} (set WUNDERKAMMER_DIR)")
    d = json.loads(PSYCHODELI.read_text(encoding="utf-8"))
    problems = validate(d)
    assert problems == [], format_problems(problems)
    assert problems.warnings == []
    assert len(d["clips"]) > 0 and "sheets" in d   # it exercises sprite sheets, not just covers


# ─── 2. one planted violation, exactly one problem ───────────────────────

CLIP_FIELDS = ("id, url, title, cover, coverVariants, detailCover, media, sheetSlots, sourceUrl, sourceLabel, "
               "note, tags, props, source, kind, captured, palette, projection")


def planted(mutate, base=doc, base_url=None, release=col.WUNDERKAMMER):
    d = base()
    mutate(d)
    return list(validate(d, base_url=base_url, release=release))


@pytest.mark.parametrize("mutate, expected", [
    (lambda d: d.update(format="wunderkammer"), 'format must be "wunderkammer.collection"'),
    (lambda d: d.pop("format"), 'format must be "wunderkammer.collection"'),
    (lambda d: d.update(version=2), "version must be 1"),
    (lambda d: d.update(version="1"), "version must be 1"),
    (lambda d: d.update(version=True), "version must be 1"),   # True == 1 in Python, not in JS
    (lambda d: d.pop("corpus"), "corpus must be an object"),
    (lambda d: d["corpus"].pop("id"), "corpus.id must be a non-empty string of at most 200 characters"),
    (lambda d: d["corpus"].update(id="   "), "corpus.id must be a non-empty string of at most 200 characters"),
    (lambda d: d.update(clips=[]), "clips must be an array of 1 to 50000 items"),
    (lambda d: d.pop("clips"), "clips must be an array of 1 to 50000 items"),
])
def test_required_fields(mutate, expected):
    assert planted(mutate) == [expected]


def test_clips_above_the_limit_are_refused():
    clips = [{"id": str(i)} for i in range(LIMITS["clips"] + 1)]
    assert planted(lambda d: d.update(clips=clips)) == ["clips must be an array of 1 to 50000 items"]
    assert planted(lambda d: d.update(clips=clips[:-1])) == []


@pytest.mark.parametrize("mutate, expected", [
    (lambda d: d.update(extra=1),
     "collection.extra is not supported (supported: format, version, corpus, ui, facetTypes, images, viewState, sheets, facets, clips)"),
    (lambda d: d["corpus"].update(name="x"), "corpus.name is not supported (supported: id, revision)"),
    (lambda d: d["ui"].update(corpusName="x"), f"ui.corpusName is not supported (supported: {UI_FIELDS[col.WUNDERKAMMER]})"),
    (lambda d: d.update(images={"lazy": True}), "images.lazy is not supported (supported: cors, sheets)"),
    (lambda d: d["clips"][0].update(image="x.png"),
     f"clips[0].image is not supported (supported: {CLIP_FIELDS}; put other attributes in props)"),
    (lambda d: d["clips"][0].update(__proto__={}), "clips[0].__proto__ is not allowed"),
])
def test_unknown_keys_are_refused_with_the_supported_list(mutate, expected):
    assert planted(mutate) == [expected]


@pytest.mark.parametrize("release", RELEASES)
def test_the_supported_ui_list_is_the_releases_own(release):
    assert planted(lambda d: d["ui"].update(corpusName="x"), release=release) == \
        [f"ui.corpusName is not supported (supported: {UI_FIELDS[release]})"]


@pytest.mark.parametrize("release, nouns, expected", [
    ("0.1.0", {"item": "cat", "items": "cats"}, [f"ui.nouns is not supported (supported: {UI_FIELDS['0.1.0']})"]),
    ("0.1.0", "not checked further", [f"ui.nouns is not supported (supported: {UI_FIELDS['0.1.0']})"]),
    ("0.2.0", {"item": "cat", "items": "cats"}, []),
    ("0.2.0", {"item": "😀" * 20, "items": "cats"}, []),   # 40 UTF-16 code units
    ("0.2.0", {"item": "😀" * 20 + "s", "items": "cats"}, ["ui.nouns.item must be a non-empty string of at most 40 characters"]),
    ("0.2.0", {"item": "cat"}, ["ui.nouns.items must be a non-empty string of at most 40 characters"]),
    ("0.2.0", {"item": " ", "items": 2}, ["ui.nouns.item must be a non-empty string of at most 40 characters",
                                           "ui.nouns.items must be a non-empty string of at most 40 characters"]),
    ("0.2.0", {"item": "cat", "items": "cats", "plural": "cats"}, ["ui.nouns.plural is not supported (supported: item, items)"]),
    ("0.2.0", {"item": "cat", "items": "cats", "__proto__": {}}, ["ui.nouns.__proto__ is not allowed"]),
    ("0.2.0", ["cat", "cats"], ["ui.nouns must be an object"]),
    ("0.2.0", None, ["ui.nouns must be an object"]),
])
def test_ui_nouns_by_release(release, nouns, expected):
    assert planted(lambda d: d["ui"].update(nouns=nouns), release=release) == expected


def test_an_unknown_release_is_an_error():
    with pytest.raises(ValueError, match=r"known: 0\.1\.0, 0\.2\.0, 0\.3\.0"):
        validate(doc(), release="0.4.0")


def test_every_added_field_names_a_known_release():
    assert col.WUNDERKAMMER in RELEASES and set(col.SINCE.values()) <= set(RELEASES)
    assert RELEASES[0] not in col.SINCE.values()   # a field the oldest release accepts was not added


def test_the_default_release_is_the_one_the_collections_reference_pins():
    text = (ROOT / "plugins/muriel/skills/compose/references/collections.md").read_text(encoding="utf-8")
    pins = re.findall(r"wunderkammer@v?(\d+\.\d+\.\d+)|wunderkammer/(?:tree|blob)/v(\d+\.\d+\.\d+)", text)
    assert pins and {a or b for a, b in pins} == {col.WUNDERKAMMER}


def test_only_the_first_unknown_clip_key_lists_the_supported_ones():
    def mutate(d):
        d["clips"][0]["image"] = "x.png"
        d["clips"][1]["image"] = "y.png"
    assert planted(mutate) == [
        f"clips[0].image is not supported (supported: {CLIP_FIELDS}; put other attributes in props)",
        "clips[1].image is not supported",
    ]


@pytest.mark.parametrize("key", ["vault", "adapters", "generated"])
def test_server_only_keys_are_refused_by_name(key):
    assert planted(lambda d: d.update({key: "x"})) == [
        f"collection.{key} belongs to a wunderkammer server response; a collection document does not carry it"]


def test_sheets_is_part_of_the_format_not_a_server_key():
    # wall/collection.mjs at 5ba188a accepts sheets as sprite-sheet support.
    assert validate(sprite_doc()) == []


@pytest.mark.parametrize("clips, expected", [
    ([{"id": "a"}, {"id": "a"}], 'clips[1] repeats the identity of clips[0] (id "a")'),
    ([{"id": "a", "url": "https://x.example/p"}, {"id": "b", "url": "https://x.example/p"}],
     'clips[1] repeats the identity of clips[0] (url "https://x.example/p")'),
    # Identity is the URL Standard's href, so two spellings of one URL collide.
    ([{"id": "a", "url": "HTTPS://X.Example:443/a/../p"}, {"id": "b", "url": "https://x.example/p"}],
     'clips[1] repeats the identity of clips[0] (url "https://x.example/p")'),
    ([{"id": "a", "url": "urn:clipwall:image:1"}, {"id": "b", "url": "urn:clipwall:image:1"}],
     'clips[1] repeats the identity of clips[0] (url "urn:clipwall:image:1")'),
    # url wins over id: the same id under two urls is two clips.
    ([{"id": "a", "url": "https://x.example/1"}, {"id": "a", "url": "https://x.example/2"}], None),
])
def test_identity_is_url_then_id(clips, expected):
    assert planted(lambda d: d.update(clips=clips)) == ([expected] if expected else [])


@pytest.mark.parametrize("value, expected", [
    ("https://example.org/a", None),
    ("http://example.org/a", None),
    ("javascript:alert(1)", "must be an http(s) URL"),
    ("mailto:a@example.org", "must be an http(s) URL"),
    ("about.html", "must be an absolute http(s) URL"),
    ("http://exa mple.org/", "must be an absolute http(s) URL"),   # urllib would accept this
    ("http://example.org:99999/", "must be an absolute http(s) URL"),
])
def test_source_url_must_be_http(value, expected):
    result = planted(lambda d: d["clips"][0].update(sourceUrl=value))
    assert result == ([f"clips[0].sourceUrl {expected}"] if expected else [])


@pytest.mark.parametrize("value, base_url, expected", [
    ("https://img.example/a.webp", None, None),
    ("data:image/png;base64,iVBORw0KGgo=", None, None),
    ("DATA:IMAGE/svg+xml,<svg/>", None, None),
    ("blob:https://host.example/2b6f", None, None),
    ("covers/a.webp", None, None),
    ("covers/a.webp", BASE, None),
    ("data:text/html,<b>x</b>", None, "must be an http(s), data:image/ or blob: URL"),
    ("file:///etc/passwd", None, "must be an http(s), data:image/ or blob: URL"),
    ("c:/covers/a.webp", None, "must be an http(s), data:image/ or blob: URL"),   # c: is a scheme
    ("covers/a.webp", "file:///tmp/c/collection.json", "must be an http(s), data:image/ or blob: URL"),
    ("//cdn.example/a.webp", None, "must be a valid URL"),   # protocol-relative needs a base
    ("http:", None, "must be a valid URL"),
    ("covers/a.webp", "not a url", "must be a valid URL"),
])
def test_image_schemes(value, base_url, expected):
    # One clip, so the base cannot also reach the fixture's other URLs.
    result = planted(lambda d: d.update(clips=[{"id": "a", "cover": value}]), base_url=base_url)
    assert result == ([f"clips[0].cover {expected}"] if expected else [])


@pytest.mark.parametrize("props, expected", [
    ({"n": 3, "flag": False, "none": None, "list": ["a", 2, True]}, []),
    ({"nested": {"a": 1}}, ["clips[0].props.nested must be a string, finite number or boolean"]),
    ({"score": float("nan")}, ["clips[0].props.score must be a string, finite number or boolean"]),
    ({"big": 10 ** 400}, ["clips[0].props.big must be a string, finite number or boolean"]),   # Infinity in JS
    ({"list": ["a", {"b": 1}, {"c": 2}]}, ["clips[0].props.list[1] must be a string, finite number or boolean"]),
    ({"list": ["x"] * 201}, ["clips[0].props.list supports at most 200 values"]),
    # A string that is too long is reported twice, as the reference reports it.
    ({"long": "x" * 501}, ["clips[0].props.long must be a string of at most 500 characters",
                           "clips[0].props.long must be a string, finite number or boolean"]),
    ({"note": "x"}, ["clips[0].props.note is hidden by the clip's own note field; rename the attribute"]),
    ({"constructor": "x"}, ["clips[0].props.constructor is not allowed",
                            'clips[0].props key "constructor" is not a supported attribute name']),
])
def test_props(props, expected):
    assert planted(lambda d: d["clips"][0].update(props=props)) == expected


def test_props_hold_at_most_128_attributes():
    props = {f"p{i}": i for i in range(129)}
    assert planted(lambda d: d["clips"][0].update(props=props)) == ["clips[0].props supports at most 128 attributes"]


@pytest.mark.parametrize("value, ok", [
    ("1994", True), ("1994-05", True), ("1994-05-07", True), ("1994-05-07T10:11", True),
    ("1994-05-07 10:11:12.250Z", True), ("1994-05-07T10:11:12+0200", True), ("1994-05-07T10:11:12-07:00", True),
    ("May 1994", False), ("94-05", False), ("1994-5", False), ("1994-05-07T10", False),
    ("1994-05\n", False),              # JS $ does not match before a trailing newline
    ("\u0661\u0669\u0669\u0664", False),   # Arabic-Indic digits: Python's \d would take them
    (1994, False),
])
def test_captured_is_an_iso_date(value, ok):
    result = planted(lambda d: d["clips"][0].update(captured=value))
    assert result == ([] if ok else ["clips[0].captured must be an ISO date: YYYY, YYYY-MM, YYYY-MM-DD or a date-time"])


def test_text_limits_count_utf16_code_units():
    # 250 emoji are 500 UTF-16 units: at the limit. 251 are over it,
    # though Python's len() says 251.
    assert planted(lambda d: d["clips"][0].update(title="😀" * 250)) == []
    assert planted(lambda d: d["clips"][0].update(title="😀" * 251)) == [
        "clips[0].title must be a string of at most 500 characters"]


@pytest.mark.parametrize("value, ok", [
    ("\u00a0", False), ("\ufeff", False), ("\u3000", False),   # JS trim() strips these
    ("\u0085", True),    # NEL: Python's strip() removes it, JS trim() does not
    ("a\u0001", False),  # control character
    ("a\tb", True),
])
def test_ids_follow_javascript_whitespace_and_control_rules(value, ok):
    result = planted(lambda d: d["clips"][0].update(id=value))
    assert result == ([] if ok else ["clips[0].id must be a non-empty string of at most 300 characters"])


def test_problems_follow_javascript_key_order():
    # Object.keys() lists integer-like keys first, ascending.
    result = planted(lambda d: d["clips"][0].update(props={"b": {}, "2": {}, "1": {}}))
    assert result == [f"clips[0].props.{k} must be a string, finite number or boolean" for k in ("1", "2", "b")]


@pytest.mark.parametrize("mutate, expected", [
    (lambda d: d["ui"].update(defaultGroup="__proto__"), "ui.defaultGroup is not a supported attribute name"),
    (lambda d: d["ui"].update(facetOrder="decade"), "ui.facetOrder must be an array of at most 64 attribute names"),
    (lambda d: d["ui"].update(facetLabels={"decade": "x" * 121}),
     "ui.facetLabels.decade must be a non-empty string of at most 120 characters"),
    (lambda d: d.update(facetTypes={"decade": {"type": "bins"}}),
     "facetTypes.decade.type must be one of categorical, ordinal, numeric, date"),
    (lambda d: d.update(facetTypes={"decade": {"type": "numeric", "order": [1]}}),
     "facetTypes.decade.order is only meaningful for an ordinal facet"),
    (lambda d: d.update(images={"cors": "yes"}), "images.cors must be true or false"),
    (lambda d: d.update(viewState={"version": 2}), "viewState.version must be 1"),
    (lambda d: d.update(viewState={"version": 1, "piles": [1]}),
     "viewState.piles must be an array of at most 1000 pile objects"),
    (lambda d: d["clips"][0].update(palette=["#11223"]), "clips[0].palette must be an array of at most 16 #rrggbb colors"),
    (lambda d: d["clips"][0].update(projection={"x": 2, "y": 0}), "clips[0].projection needs x and y numbers from -1 to 1"),
    (lambda d: d["clips"][0].update(projection={"x": 0, "y": 0, "col": -1}),
     "clips[0].projection.col must be a non-negative integer"),
    (lambda d: d["clips"][0].update(coverVariants=[{"src": "a.webp", "width": 0}]),
     "clips[0].coverVariants[0].width must be an integer from 1 to 8192"),
    (lambda d: d["clips"][0].update(tags="pop"), "clips[0].tags must be an array of at most 200 strings"),
])
def test_other_fields(mutate, expected):
    assert planted(mutate) == [expected]


@pytest.mark.parametrize("cell, expected", [
    ([0.0, 2, 2, 64, 36], None),                       # 0.0 is the integer 0 in JS
    ([-1, 0, 0, 1, 1], "points at sheets[-1], which does not exist"),   # not Python's sheets[-1]
    ([1e21, 0, 0, 1, 1], "points at sheets[1e+21], which does not exist"),
    ([0, 2, 2, 64, True], "must be [sheet, x, y, w, h], five integers"),
])
def test_sheet_cells_use_javascript_numbers(cell, expected):
    def mutate(d):
        d["clips"][0]["sheetSlots"] = [cell, [1, 2, 2, 480, 270]]
    result = planted(mutate, base=sprite_doc)
    assert result == ([f"clips[0].sheetSlots[0] {expected}"] if expected else [])


def test_a_non_object_document_has_one_problem():
    for d in (None, [], "collection.json", 1):
        assert list(validate(d)) == ["collection must be an object"]


# ─── 3. build and CLI ────────────────────────────────────────────────────

def _images(folder: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    (folder / "sub").mkdir(parents=True)
    (folder / ".hidden").mkdir()
    Image.new("RGB", (40, 30), "red").save(folder / "a b#1.png")
    Image.new("RGB", (16, 16), "blue").save(folder / "sub" / "c.gif")
    Image.new("RGB", (24, 12), "green").save(folder / "sub" / "d.webp")
    photo = Image.new("RGB", (60, 40), "white")
    exif = Image.Exif()
    exif[0x0112] = 6   # rotated a quarter turn on display
    exif.get_ifd(0x8769)[0x9003] = "2019:07:04 12:30:00"
    exif.get_ifd(0x8769)[0x9011] = "+02:00"
    photo.save(folder / "photo.jpg", exif=exif)
    Image.new("RGB", (8, 8)).save(folder / ".hidden" / "skip.png")
    Image.new("RGB", (8, 8)).save(folder / ".dot.png")
    (folder / "notes.txt").write_text("not an image")
    (folder / "icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"/>')


def test_folder_build_validates(tmp_path):
    folder = tmp_path / "photos"
    _images(folder)
    os.utime(folder / "a b#1.png", (1700000000, 1700000000))
    d = build(folder, title="Trip", group="captured")
    problems = validate(d)
    assert problems == [], format_problems(problems)
    assert d["ui"] == {"title": "Trip", "defaultGroup": "captured"}
    assert d["corpus"]["id"] == "photos" and len(d["corpus"]["revision"]) == 16
    clips = {c["id"]: c for c in d["clips"]}
    assert sorted(clips) == ["a b#1.png", "icon.svg", "photo.jpg", "sub/c.gif", "sub/d.webp"]
    a = clips["a b#1.png"]
    assert a["title"] == "a b#1"
    assert a["cover"] == "a%20b%231.png"   # '#' would otherwise start a fragment
    assert a["props"] == {"width": 40, "height": 30}
    assert a["captured"] == datetime.fromtimestamp(1700000000).astimezone().isoformat(timespec="seconds")
    photo = clips["photo.jpg"]
    assert photo["captured"] == "2019-07-04T12:30:00+02:00"
    assert photo["props"] == {"width": 40, "height": 60}   # orientation 6 swaps the edges
    assert clips["sub/c.gif"]["cover"] == "sub/c.gif"
    assert "props" not in clips["icon.svg"]


def test_folder_covers_are_relative_to_where_the_document_lives(tmp_path):
    folder = tmp_path / "photos"
    _images(folder)
    d = build(folder, relative_to=tmp_path / "site")
    assert {c["cover"] for c in d["clips"]} >= {"../photos/a%20b%231.png", "../photos/sub/c.gif"}
    assert validate(d) == []


def test_folder_build_without_pillow_reads_sizes_from_headers(tmp_path, monkeypatch):
    folder = tmp_path / "photos"
    _images(folder)
    Image = pytest.importorskip("PIL.Image")
    Image.new("RGB", (33, 21)).save(folder / "e.bmp")
    Image.new("RGBA", (31, 17)).save(folder / "f.webp", lossless=True)
    monkeypatch.setattr(col, "_pillow_info", lambda path: None)
    clips = {c["id"]: c for c in build(folder)["clips"]}
    assert clips["a b#1.png"]["props"] == {"width": 40, "height": 30}
    assert clips["sub/c.gif"]["props"] == {"width": 16, "height": 16}
    assert clips["sub/d.webp"]["props"] == {"width": 24, "height": 12}
    assert clips["f.webp"]["props"] == {"width": 31, "height": 17}
    assert clips["e.bmp"]["props"] == {"width": 33, "height": 21}
    assert clips["photo.jpg"]["props"] == {"width": 60, "height": 40}   # stored size: no EXIF without Pillow
    assert clips["photo.jpg"]["captured"] != "2019-07-04T12:30:00+02:00"


def test_an_empty_folder_is_an_error(tmp_path):
    (tmp_path / "notes.txt").write_text("x")
    with pytest.raises(ValueError, match="no images"):
        build(tmp_path)


def _csv(tmp_path, text, name="albums.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_csv_build_validates(tmp_path):
    path = _csv(tmp_path, "\ufeffid,title,cover,sourceUrl,captured,decade,genre[],label\n"
                          'x1,One,covers/x1.webp,https://example.org/1,1994-05,1990s,"pop, electronic,",Warp\n'
                          "x2,Two,,,,1980s,pop,\n"
                          ",,,,,,,\n")
    d = build(path, group="genre")
    assert validate(d) == []
    assert d["corpus"]["id"] == "albums" and d["ui"] == {"title": "albums", "defaultGroup": "genre"}
    assert d["clips"] == [
        {"id": "x1", "title": "One", "cover": "covers/x1.webp", "sourceUrl": "https://example.org/1", "captured": "1994-05",
         "props": {"decade": "1990s", "genre": ["pop", "electronic"], "label": "Warp"}},
        {"id": "x2", "title": "Two", "props": {"decade": "1980s", "genre": ["pop"]}},
    ]


def test_csv_commas_split_only_under_a_list_header(tmp_path):
    d = build(_csv(tmp_path, 'id,genre,genre2[]\nx,"pop, rock","pop, rock"\n'))
    assert d["clips"][0]["props"] == {"genre": "pop, rock", "genre2": ["pop", "rock"]}


@pytest.mark.parametrize("text, message", [
    ("title,decade\nOne,1990s\n", "no id column"),
    ("id,note\nx,hello\n", "a prop may not shadow a clip field"),
    ("id,title[]\nx,a\n", "holds one value"),
    ("id,decade,decade\nx,a,b\n", "appears twice"),
    ("id,,decade\nx,,a\n", "has no name"),
    ("id,decade\nx,a,extra\n", "3 cells under a 2-column header"),
    ("id,decade\n,1990s\n", "the id cell is empty"),
    ("id,decade\n", "no rows"),
    ("", "no header row"),
])
def test_csv_mapping_errors(tmp_path, text, message):
    with pytest.raises(ValueError, match=message):
        build(_csv(tmp_path, text))


def test_a_group_must_name_an_attribute(tmp_path):
    with pytest.raises(ValueError, match=r"group 'decad' is not an attribute of any clip \(available: decade\)"):
        build(_csv(tmp_path, "id,decade\nx,1990s\n"), group="decad")


def test_a_csv_build_with_a_bad_link_has_problems(tmp_path):
    d = build(_csv(tmp_path, "id,sourceUrl\nx,javascript:alert(1)\n"))
    assert list(validate(d)) == ["clips[0].sourceUrl must be an http(s) URL"]


def run_cli(*args, stdin=None):
    return subprocess.run([sys.executable, "-m", "muriel.collection", *map(str, args)],
                          input=stdin, capture_output=True, text=True)


def test_cli_build_writes_a_valid_document(tmp_path):
    folder = tmp_path / "photos"
    _images(folder)
    out = tmp_path / "site" / "collection.json"
    r = run_cli("build", folder, "--out", out, "--title", "Trip", "--group", "captured")
    assert r.returncode == 0, r.stderr
    assert "wrote" in r.stdout and "5 clips" in r.stdout
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["ui"]["title"] == "Trip"
    assert all(c["cover"].startswith("../photos/") for c in written["clips"])
    assert validate(written) == []


def test_cli_build_refuses_to_write_an_invalid_document(tmp_path):
    out = tmp_path / "collection.json"
    r = run_cli("build", _csv(tmp_path, "id,sourceUrl\nx,ftp://x\n"), "--out", out)
    assert r.returncode == 1
    assert "clips[0].sourceUrl must be an http(s) URL" in r.stdout
    assert not out.exists()


@pytest.mark.parametrize("args", [("build", "missing-folder", "--out", "x.json"), ("build",), ("bogus",)])
def test_cli_build_usage_errors_exit_2(tmp_path, args):
    assert run_cli(*args).returncode == 2


def test_cli_validate_exit_codes(tmp_path):
    good = tmp_path / "good.json"
    good.write_text(json.dumps(doc()), encoding="utf-8")
    r = run_cli("validate", good)
    assert (r.returncode, r.stdout.strip()) == (0, f"{good}: valid (2 clips)")

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(doc(format="x", extra=1)), encoding="utf-8")
    r = run_cli("validate", bad)
    assert r.returncode == 1
    assert r.stdout.splitlines()[:3] == [
        "Collection is not valid (2 problems):",
        "- collection.extra is not supported (supported: format, version, corpus, ui, facetTypes, images, "
        "viewState, sheets, facets, clips)",
        '- format must be "wunderkammer.collection"',
    ]

    (tmp_path / "empty.json").write_text("  \n")
    (tmp_path / "broken.json").write_text("{nope")
    (tmp_path / "nan.json").write_text('{"x": NaN}')
    for name in ("missing.json", "empty.json", "broken.json", "nan.json"):
        assert run_cli("validate", tmp_path / name).returncode == 2, name
    assert run_cli("validate", "-", stdin="").returncode == 2
    assert run_cli("validate", "-", stdin=json.dumps(doc())).returncode == 0
    assert run_cli("validate", "-", stdin="[]").returncode == 1


def test_cli_validate_resolves_against_a_base_url(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps(doc(clips=[{"id": "a", "sourceUrl": "about.html"}])), encoding="utf-8")
    assert run_cli("validate", path).returncode == 1
    assert run_cli("validate", path, "--base-url", BASE).returncode == 0


def test_cli_validate_prints_warnings_and_still_passes(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps(doc(facets={"decade": {"1980s": 99}})), encoding="utf-8")
    r = run_cli("validate", path)
    assert r.returncode == 0
    assert "warning: facets differ" in r.stderr


def test_cli_validate_checks_for_a_release(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps(doc(ui={"title": "Cats", "nouns": {"item": "cat", "items": "cats"}})), encoding="utf-8")
    assert run_cli("validate", path).returncode == 0   # the default, 0.3.0, accepts ui.nouns
    r = run_cli("validate", path, "--release", "0.1.0")
    assert r.returncode == 1
    assert f"- ui.nouns is not supported (supported: {UI_FIELDS['0.1.0']})" in r.stdout.splitlines()
    assert r.stderr.strip() == ("note: ui.nouns is newer than Wunderkammer 0.1.0; "
                                "for a wall from release 0.2.0, validate with --release 0.2.0")
    assert run_cli("validate", path, "--release", "0.4.0").returncode == 2
    # A problem the release does not explain draws no note.
    path.write_text(json.dumps(doc(ui={"corpusName": "x"})), encoding="utf-8")
    r = run_cli("validate", path, "--release", "0.1.0")
    assert (r.returncode, r.stderr) == (1, "")


def test_the_muriel_dispatcher_lists_collection():
    r = subprocess.run([sys.executable, "-m", "muriel"], capture_output=True, text=True)
    assert "collection" in r.stdout
    r = subprocess.run([sys.executable, "-m", "muriel", "collection", "validate", "-"], input=json.dumps(doc()),
                       capture_output=True, text=True)
    assert r.returncode == 0


# ─── 4. differential: the reference itself ───────────────────────────────

def _reference():
    node = shutil.which("node")
    if not node or not (WK / "wall/collection.mjs").is_file():
        pytest.skip(f"needs node and a Wunderkammer checkout at {WK} (set WUNDERKAMMER_DIR)")
    return node


def _git(*args):
    return subprocess.run(["git", "-C", str(WK), *args], capture_output=True)


def _require_git_checkout():
    if not shutil.which("git") or _git("rev-parse", "--git-dir").returncode != 0:
        pytest.skip(f"needs a Wunderkammer git checkout at {WK} (set WUNDERKAMMER_DIR)")


@pytest.fixture(scope="session")
def pinned(tmp_path_factory):
    """``pinned(release, commit)``: node, and that commit's validator and example in a scratch folder."""
    node = _reference()
    _require_git_checkout()
    made = {}

    def get(release, commit):
        if commit not in made:
            if _git("cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
                pytest.skip(f"{WK} lacks Wunderkammer {commit[:7]} ({release}); run git -C {WK} fetch origin --tags")
            out = tmp_path_factory.mktemp(f"wunderkammer-{release}-{commit[:7]}")
            for path in (*VALIDATOR_FILES, "examples/psychodeli/collection.json"):
                blob = _git("show", f"{commit}:{path}")
                assert blob.returncode == 0, blob.stderr.decode()
                (out / path).parent.mkdir(parents=True, exist_ok=True)
                (out / path).write_bytes(blob.stdout)
            made[commit] = out
        return node, made[commit]
    return get


def test_every_release_has_a_pinned_reference():
    assert set(REFERENCE) == set(RELEASES)
    assert set(EQUIVALENT.values()) <= set(RELEASES) and not set(EQUIVALENT) & set(REFERENCE.values())


def test_the_checkout_validator_matches_a_pinned_commit():
    """The checkout moving past every pin fails here, not silently.

    The differential tests read pinned commits, so they keep passing when
    Wunderkammer changes its validator. This test compares the checkout's
    validator files with each pin's: when none matches, port the change to
    muriel/collection.py and pin the new commit in REFERENCE. A change that
    alters no rule goes in EQUIVALENT instead, and test_both_validators_agree
    then has to pass against it.
    """
    if not (WK / VALIDATOR_FILES[0]).is_file():
        pytest.skip(f"no Wunderkammer checkout at {WK} (set WUNDERKAMMER_DIR)")
    _require_git_checkout()
    # Every module the validator imports must be one compared here.
    for path in VALIDATOR_FILES:
        for name in re.findall(r"""from\s+['"]\./([^'"]+)['"]""", (WK / path).read_text(encoding="utf-8")):
            assert f"wall/{name}" in VALIDATOR_FILES, f"{path} imports wall/{name}; add it to VALIDATOR_FILES"
    blobs = lambda ref: [_git("rev-parse", f"{ref}:{p}").stdout.strip() for p in VALIDATOR_FILES]
    here = [_git("hash-object", "--", p).stdout.strip() for p in VALIDATOR_FILES]
    matches = [release for release, commit in PINS if blobs(commit) == here]
    newest = REFERENCE[RELEASES[-1]]
    assert matches, (f"the validator at {WK} matches no pinned commit; see git -C {WK} diff {newest[:7]} -- "
                     f"{' '.join(VALIDATOR_FILES)}, port it, and pin the new commit in REFERENCE "
                     f"(or, if no rule changed, map it to its release in EQUIVALENT)")


_JS_VALIDATE = r"""
import { validateCollection } from %s;
import { readFileSync } from "node:fs";
const cases = JSON.parse(readFileSync(0, "utf8"));
console.log(JSON.stringify(cases.map(([doc, baseUrl]) => {
  try { return { problems: [], overflow: 0, warnings: validateCollection(doc, { baseUrl }).warnings }; }
  catch (e) {
    if (!e.problems) return { crash: String(e) };
    const total = Number(/\((\d+) problems?\)/.exec(e.message)[1]);
    return { problems: e.problems, overflow: total - e.problems.length, warnings: [] };
  }
})));
"""

_VALUES = [None, True, False, 0, 1, -1, 1.0, 1.5, 2 ** 53 + 1, 10 ** 400, -0.0, "", " ", "\u00a0", "\u0085", "a",
           "x" * 81, "😀" * 121, "\u0001", "a\nb", "__proto__", "title", "1994-05-07 10:11:12.5+0200", "May 1994",
           "https://x.example/a", "HTTPS://X.EXAMPLE/b/../a", "http:x", "javascript:alert(1)",
           "data:image/png;base64,AAAA", " data:image/png,x", "blob:https://x/1", "covers/a.webp", "//cdn.x/a.png",
           "c:/x.png", "urn:clipwall:image:abc", "urn:x:abc\n", "#112233", [], [1], ["a", {"x": 1}],
           [[0, 2, 2, 64, 36]], [[5, 0, 0, 1, 1]], [[1e21, 0, 0, 1, 1]], {}, {"2": 1, "b": 2, "1": 3},
           {"src": "x.png", "edge": 64, "width": 64, "height": 64}, {"type": "ordinal", "order": ["a"]},
           {"x": 0.5, "y": -1}, ["x"] * 201, "covers", "full", {"item": "cat", "items": "cats"}]
_KEYS = ["format", "version", "corpus", "ui", "facetTypes", "images", "viewState", "sheets", "facets", "clips", "vault",
         "extra", "id", "title", "defaultGroup", "facetOrder", "facetLabels", "url", "cover", "coverVariants",
         "media", "sheetSlots", "sourceUrl", "note", "tags", "props", "source", "captured", "palette", "projection",
         "image", "decade", "src", "edge", "width", "type", "order", "x", "col", "0", "nouns", "item", "items"]
_NOUNS = [{"item": "cat", "items": "cats"}, {"item": "frame", "plural": "frames"}, "frames", None, [], {},
          {"item": "x" * 41, "items": "xs"}, {"item": "😀" * 20, "items": "😀" * 21}, {"item": " ", "items": " "},
          {"item": "a\u0001", "items": "b"}, {"item": 1, "items": True}, {"item": "cat", "items": "cats", "__proto__": {}}]


def _mutants(n, seed):
    """Valid documents with one to four random edits each: a cheap fuzz."""
    rnd = random.Random(seed)

    def containers(node, out):
        out.append(node)
        for v in (node.values() if isinstance(node, dict) else node):
            if isinstance(v, (dict, list)):
                containers(v, out)
        return out

    for _ in range(n):
        d = rnd.choice([doc, sprite_doc])()
        for _ in range(rnd.randint(1, 4)):
            c = rnd.choice(containers(d, []))
            v = copy.deepcopy(rnd.choice(_VALUES))
            if isinstance(c, dict):
                if c and rnd.random() < 0.2:
                    del c[rnd.choice(list(c))]
                else:
                    c[rnd.choice(list(c)) if c and rnd.random() < 0.5 else rnd.choice(_KEYS)] = v
            elif c:
                c[rnd.randrange(len(c))] = v
        yield d


@pytest.mark.parametrize("release, commit", PINS, ids=[f"{r}@{c[:7]}" for r, c in PINS])
def test_both_validators_agree(tmp_path, pinned, release, commit):
    node, reference = pinned(release, commit)
    folder = tmp_path / "photos"
    _images(folder)
    cases = [(doc(), None), (sprite_doc(), BASE), (doc(facets=DERIVED), None), (doc(facets={"x": 1}), None),
             (build(folder, group="captured"), None),
             (build(_csv(tmp_path, 'id,cover,sourceUrl,genre[]\nx,a.png,https://e.org/x,"a,b"\ny,b.png,about.html,a\n')), None)]
    cases += [(doc(ui={"title": "Cats", "nouns": n}), None) for n in _NOUNS]
    cases += [(d, base) for d, base in zip(_mutants(400, seed=5), [None, BASE, "file:///c/c.json", "not a url"] * 100)]
    cases.append((json.loads((reference / "examples/psychodeli/collection.json").read_text(encoding="utf-8")), None))
    # Both sides read the same JSON text, as the CLI and the wall would.
    payload = json.dumps(cases)
    script = _JS_VALIDATE % json.dumps((reference / "wall/collection.mjs").as_uri())
    r = subprocess.run([node, "--input-type=module", "-e", script], input=payload, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    mismatches, outcomes = [], []
    for (d, base), want in zip(json.loads(payload), json.loads(r.stdout)):
        got = validate(d, base_url=base, release=release)
        outcomes.append(list(got))
        if {"problems": list(got), "overflow": got.overflow, "warnings": got.warnings} != want:
            mismatches.append((json.dumps(d)[:300], base, want, list(got)))
    assert not mismatches, mismatches[:3]
    # The cases reach the release's ui.nouns rule, accepted or refused.
    noun_cases = outcomes[6:6 + len(_NOUNS)]
    if release == "0.1.0":
        assert all(any(p.startswith("ui.nouns is not supported") for p in o) for o in noun_cases)
    else:
        assert noun_cases[0] == [] and any(p.startswith("ui.nouns.item ") for o in noun_cases for p in o)


_URLS = [
    "http://x/a^b{c}`d|e", "http://x/?q=a^b'c", "http://x/#f^ `<>", "HTTP://EXAMPLE.com:80/a/./b/../c", "http://xn--a/",
    "http://0x7f.1/", "http://1.2.3.4.5/", "http://[::ffff:1.2.3.4]/", "http://[1:0:0:2:0:0:0:3]/", "http://4294967296/",
    "http://x/%2e%2E/y", "http://a b/", "https:x", "http:\\\\x\\y", "\thttp://x/\n", "ht\ntp://x/", "http://a@b@c/",
    "http://x:99999/", "https://x:443/", "file:///C|/x", "file://localhost/x", "foo://bad host/x", "foo:/", "blob:",
    "data:", "?q", "#f", "", "../a", "//cdn.example/a", "http://ß.de/", "http://例え.テスト/", "http://♥.com/",
    "http://\u00ad/", "http://\u05d0a.com/", "http://x%41.com/", "http://%zz/", "http://example.com/\ufeff/foo",
]


def test_url_parser_matches_node():
    node = _reference()
    cases = [[u, b] for u in _URLS for b in (None, BASE, "file:///tmp/c.json", "sc://h/a/b")]
    script = ('const c = JSON.parse(require("fs").readFileSync(0, "utf8"));'
              'console.log(JSON.stringify(c.map(([u, b]) => { try { return (b === null ? new URL(u) : new URL(u, b)).href }'
              ' catch { return null } })))')
    r = subprocess.run([node, "-e", script], input=json.dumps(cases), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    got = [getattr(_whatwg_url.parse(u, b), "href", None) for u, b in cases]
    mismatches = [(u, b, w, g) for (u, b), w, g in zip(cases, json.loads(r.stdout), got) if w != g]
    assert not mismatches, mismatches[:5]
