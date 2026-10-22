"""
muriel.collection — build and check Wunderkammer collection documents.

A collection document (format ``wunderkammer.collection``, version 1) is
how an agent shows a person a visual collection in Wunderkammer without a
server: one JSON file of clips, each with an id, a title, a cover and
attributes to facet by. This module writes one from a folder of images or
a CSV, and checks one before it is handed over, so neither the agent nor
the person learns about a bad document from a blank wall.

The checks are a port of ``validateCollection()`` in Wunderkammer's
``wall/collection.mjs``, the validator the wall itself runs, so a document
this module passes is one the wall loads. ``docs/CONTRACT.md`` in
Wunderkammer describes the format. In short:

- ``format`` is ``"wunderkammer.collection"`` and ``version`` is 1;
  ``corpus.id`` is required, and ``clips`` holds 1 to 50,000 items.
- Unknown keys are refused with the list of supported ones. Keys only a
  Wunderkammer server sends (``vault``, ``adapters``, ``generated``) are
  refused by name.
- A clip's identity is its ``url``, falling back to its ``id``; a repeated
  identity is an error.
- ``sourceUrl`` must be http(s). Images (``cover``, ``detailCover``,
  ``coverVariants[].src``, ``media[].src``, ``sheets[].src``) may be
  http(s), ``data:image/`` or ``blob:``; a clip's ``video`` may be http(s)
  or ``blob:``, never ``data:``. Relative URLs resolve against the
  document's URL when ``base_url`` is given; without one, a relative image
  or video stays relative to the page and a relative link is refused.
- ``props`` values are strings, finite numbers, booleans, null, or arrays
  of those. A props key may not name a clip field, because the wall reads
  the clip's own field first.
- ``captured`` is an ISO date: ``YYYY``, ``YYYY-MM``, ``YYYY-MM-DD`` or a
  date-time.
- Sprite sheets (``sheets`` and per-clip ``sheetSlots``) are checked
  against the pages they point into.
- Every problem is reported with its path, up to 25, with a count of the
  rest.

The checks follow one Wunderkammer release at a time, because each wall
refuses the fields added after it. ``validate()`` checks for
``WUNDERKAMMER`` (0.3.0, the release muriel's collections reference pins)
unless ``release`` names another one in ``RELEASES``. 0.2.0 adds
``ui.nouns``, which 0.1.0 refuses, and 0.3.0 adds no fields. ``"next"`` is
Wunderkammer's work after 0.3.0, which adds a clip's ``video``. ``SINCE``
lists each added field with the first release that accepts it.

Where Python and JavaScript differ, the port follows JavaScript: string
limits count UTF-16 code units, numbers compare as doubles, ``trim()`` and
``\\s`` use JavaScript's whitespace set, object keys are visited in
JavaScript's order (integer-like keys first), and URLs are parsed by the
URL Standard (``muriel._whatwg_url``), not RFC 3986. The one known gap is
hostnames outside ASCII; see that module.

Usage
-----

::

    from muriel.collection import build, validate, format_problems

    doc = build("photos/", title="Trip", group="captured")
    problems = validate(doc)
    if problems:
        print(format_problems(problems))

Or from the command line::

    python -m muriel.collection build photos/ --out photos/collection.json
    python -m muriel.collection build albums.csv --out collection.json --group decade
    python -m muriel.collection validate collection.json
    python -m muriel.collection validate collection.json --release 0.1.0
    python -m muriel.collection validate collection.json --release next

``validate`` exits 0 when the document is valid, 1 when it has problems
(each printed with its path), and 2 when it read nothing or the input is
not JSON.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union
from urllib.parse import quote

from . import _whatwg_url

__all__ = ["build", "validate", "format_problems", "Problems", "FORMAT", "VERSION", "LIMITS",
           "WUNDERKAMMER", "RELEASES", "SINCE"]

FORMAT = "wunderkammer.collection"
VERSION = 1
#: The release validate() checks for by default: the one muriel's
#: references/collections.md pins. Move both together.
WUNDERKAMMER = "0.3.0"
#: The releases validate() can check for, oldest first. Each one has a
#: pinned commit in tests/test_collection.py's REFERENCE. "next" is
#: Wunderkammer after 0.3.0; rename it to the release that ships it.
RELEASES = ("0.1.0", "0.2.0", "0.3.0", "next")
#: Each field added after 0.1.0, with the first release that accepts it.
#: An older release refuses it as unsupported, as that release's wall does.
#: A clip field is named ``clips.<field>``.
SINCE = MappingProxyType({"ui.nouns": "0.2.0", "clips.video": "next"})
LIMITS = MappingProxyType({
    "clips": 50000, "problems": 25, "sheets": 4096, "sheetSlots": 8, "sheetEdge": 4096, "sheetPx": 16384,
})

TOP = ("format", "version", "corpus", "ui", "facetTypes", "images", "viewState", "sheets", "facets", "clips")
#: Keys a Wunderkammer server payload carries that a portable document must not.
SERVER_ONLY = ("vault", "adapters", "generated")
CLIP = ("id", "url", "title", "cover", "coverVariants", "detailCover", "media", "video", "sheetSlots", "sourceUrl",
        "sourceLabel", "note", "tags", "props", "source", "kind", "captured", "palette", "projection")
UI = ("title", "defaultGroup", "facetOrder", "facetLabels", "hiddenFacets", "nouns")
FACET_TYPES = ("categorical", "ordinal", "numeric", "date")
SHEET_ROLES = ("overview", "covers")
FORBIDDEN = ("__proto__", "prototype", "constructor")

_CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")
# Every pattern spells out [0-9] and [a-zA-Z]: in Python, \d matches any
# Unicode digit and [a-z] with IGNORECASE matches U+212A KELVIN SIGN.
_CAPTURED = re.compile(
    r"[0-9]{4}(-[0-9]{2}(-[0-9]{2}([T ][0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]+)?)?(Z|[+-][0-9]{2}:?[0-9]{2})?)?)?)?"
)
# JavaScript's WhiteSpace and LineTerminator: what trim() strips and \s matches.
_JS_SPACE = "\t\n\v\f\r              " \
            "    　﻿"
_URN = re.compile("[uU][rR][nN]:[a-zA-Z0-9][a-zA-Z0-9-]{0,31}:[^" + re.escape(_JS_SPACE) + "]+")
_SCHEME_PREFIX = re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*:")
_DATA_IMAGE = re.compile("[dD][aA][tT][aA]:[iI][mM][aA][gG][eE]/")
_HEX_COLOR = re.compile("#[0-9a-fA-F]{6}")
_ARRAY_INDEX = re.compile("0|[1-9][0-9]*")

_MISSING = object()   # JavaScript's undefined: a key that is absent, as opposed to null


class Problems(list):
    """What :func:`validate` found: ``"<path> <message>"`` strings.

    At most ``LIMITS["problems"]`` are kept; ``overflow`` counts the rest
    and ``total`` is both together. An empty list means the document is
    valid, and only then does ``warnings`` hold anything: notes the wall
    also logs without refusing the document.
    """

    def __init__(self, items: Iterable[str] = (), overflow: int = 0, warnings: Iterable[str] = ()):
        super().__init__(items)
        self.overflow = overflow
        self.warnings = list(warnings)

    @property
    def total(self) -> int:
        return len(self) + self.overflow


def format_problems(problems: Problems) -> str:
    """The message the wall's ``CollectionError`` carries, line for line."""
    total = len(problems) + getattr(problems, "overflow", 0)
    more = f"\n- …and {problems.overflow} more" if getattr(problems, "overflow", 0) else ""
    return (f"Collection is not valid ({total} problem{'' if total == 1 else 's'}):\n- "
            + "\n- ".join(problems) + more)


# ─── JavaScript semantics ────────────────────────────────────────────────

def _js_len(s: str) -> int:
    """``s.length``: UTF-16 code units, so an emoji counts twice."""
    if s.isascii():
        return len(s)
    return len(s) + sum(1 for ch in s if ord(ch) > 0xFFFF)


def _js_slice(s: str, n: int) -> str:
    """``s.slice(0, n)`` in UTF-16 code units."""
    if _js_len(s) == len(s):
        return s[:n]
    return s.encode("utf-16-le", "surrogatepass")[:2 * n].decode("utf-16-le", "surrogatepass")


def _utf16(s: str) -> bytes:
    """Sort key for JavaScript's default string order (UTF-16 code units)."""
    return s.encode("utf-16-be", "surrogatepass")


def _number(x: Any) -> Optional[float]:
    """The double JavaScript holds for a JSON number, else None."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    try:
        return float(x)
    except OverflowError:   # an integer literal past 1e308 is Infinity in JS
        return math.inf if x > 0 else -math.inf


def _is_integer(x: Any) -> bool:
    """``Number.isInteger(x)``."""
    f = _number(x)
    return f is not None and math.isfinite(f) and f.is_integer()


def _js_num(x: Any) -> str:
    """``String(n)`` for a number: shortest digits, exponent past 1e21."""
    f = _number(x)
    if f is None:
        return str(x)
    if math.isnan(f):
        return "NaN"
    if math.isinf(f):
        return "Infinity" if f > 0 else "-Infinity"
    if f == 0:
        return "0"
    sign = "-" if f < 0 else ""
    d = Decimal(repr(abs(f))).normalize().as_tuple()
    digits = "".join(map(str, d.digits))
    k = len(digits)
    n = d.exponent + k
    if k <= n <= 21:
        s = digits + "0" * (n - k)
    elif 0 < n <= 21:
        s = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        s = "0." + "0" * -n + digits
    else:
        e = n - 1
        s = digits[0] + ("." + digits[1:] if k > 1 else "") + "e" + ("+" if e >= 0 else "-") + str(abs(e))
    return sign + s


def _js_string(x: Any) -> str:
    """``String(x)`` for a JSON value."""
    if x is None:
        return "null"
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, (int, float)):
        return _js_num(x)
    if isinstance(x, str):
        return x
    if isinstance(x, (list, tuple)):
        return ",".join("" if v is None else _js_string(v) for v in x)
    return "[object Object]"


def _js_keys(d: dict) -> list:
    """``Object.keys(d)``: array-index keys first, ascending, then insertion order."""
    index = [k for k in d if isinstance(k, str) and _ARRAY_INDEX.fullmatch(k) and int(k) < 4294967295]
    if not index:
        return list(d)
    index.sort(key=int)
    chosen = set(index)
    return index + [k for k in d if k not in chosen]


def _is_array(x: Any) -> bool:
    return isinstance(x, (list, tuple))


def _plain(x: Any) -> bool:
    return isinstance(x, dict)


def _get(d: Any, key: str) -> Any:
    return d.get(key, _MISSING) if isinstance(d, dict) else _MISSING


def _supported(section: str, keys: Sequence[str], release: str) -> Tuple[str, ...]:
    """``keys`` of ``section`` that ``release`` accepts, in the reference's order."""
    have = RELEASES.index(release)
    return tuple(k for k in keys if RELEASES.index(SINCE.get(f"{section}.{k}", RELEASES[0])) <= have)


def _too_new(problems: Sequence[str], release: str) -> List[Tuple[str, str]]:
    """(field, release) for each field ``problems`` refuse only because ``release`` predates it."""
    have = RELEASES.index(release)
    found = []
    for f, since in SINCE.items():
        section, _, key = f.partition(".")
        # A clip field is refused at its clip's path: clips[3].video.
        index = r"\[[0-9]+\]" if section == "clips" else ""
        at = re.compile(re.escape(section) + index + re.escape(f".{key} is not supported"))
        if RELEASES.index(since) > have and any(at.match(p) for p in problems):
            found.append((f, since))
    return found


# ─── the checker ─────────────────────────────────────────────────────────

class _Checker:
    """The closures inside ``validateCollection()``, with their shared state."""

    def __init__(self, base_url: Optional[str]):
        self.problems: List[str] = []
        self.overflow = 0
        self.has_base = bool(base_url)
        # An unparseable base makes every new URL(value, base) throw.
        self.base = _whatwg_url.parse(base_url) if base_url else None

    def problem(self, path: str, message: str) -> None:
        if len(self.problems) < LIMITS["problems"]:
            self.problems.append(f"{path} {message}")
        else:
            self.overflow += 1

    def text(self, value: Any, path: str, max: int = 240, empty: bool = False) -> Optional[str]:
        if (not isinstance(value, str) or _js_len(value) > max
                or (not empty and not value.strip(_JS_SPACE)) or _CONTROL.search(value)):
            self.problem(path, f"must be {'a' if empty else 'a non-empty'} string of at most {max} characters")
            return None
        return value

    def field(self, value: Any, path: str) -> Optional[str]:
        v = self.text(value, path, max=80)
        if v is not None and v in FORBIDDEN:
            self.problem(path, "is not a supported attribute name")
            return None
        return v

    def keys(self, value: Any, path: str, allowed: Optional[Sequence[str]] = None) -> bool:
        if not _plain(value):
            self.problem(path, "must be an object")
            return False
        for key in _js_keys(value):
            if key in FORBIDDEN:
                self.problem(f"{path}.{key}", "is not allowed")
            elif allowed is not None and key not in allowed:
                self.problem(f"{path}.{key}", f"is not supported (supported: {', '.join(allowed)})")
        return True

    def fields(self, value: Any, path: str, max: int) -> List[str]:
        if not _is_array(value) or len(value) > max:
            self.problem(path, f"must be an array of at most {max} attribute names")
            return []
        return [v for v in (self.field(x, f"{path}[{i}]") for i, x in enumerate(value)) if v is not None]

    def _url(self, value: str):
        if self.has_base:
            return None if self.base is None else _whatwg_url.parse(value, self.base)
        return _whatwg_url.parse(value)

    def image(self, value: Any, path: str) -> bool:
        """An image source: http(s), data:image/ or blob:, after resolving relative paths."""
        if self.text(value, path, max=1 << 20) is None:
            return False
        url = self._url(value)
        if url is None:
            # Without a base, a relative path stays relative to the page.
            if not self.has_base and not _SCHEME_PREFIX.match(value) and not value.startswith("//"):
                return True
            self.problem(path, "must be a valid URL")
            return False
        if (not _DATA_IMAGE.match(value)) if url.scheme == "data" else url.scheme not in ("http", "https", "blob"):
            self.problem(path, "must be an http(s), data:image/ or blob: URL")
            return False
        return True

    def video(self, value: Any, path: str) -> bool:
        """A video source: http(s) or blob:, after resolving relative paths. Never data:."""
        if self.text(value, path, max=4096) is None:
            return False
        url = self._url(value)
        if url is None:
            # Without a base, a relative path stays relative to the page.
            if not self.has_base and not _SCHEME_PREFIX.match(value) and not value.startswith("//"):
                return True
            self.problem(path, "must be a valid URL")
            return False
        if url.scheme not in ("http", "https", "blob"):
            self.problem(path, "must be an http(s) or blob: URL")
            return False
        return True

    def link(self, value: Any, path: str) -> Optional[str]:
        """A link a person can follow: http(s) only. Returns its href."""
        if self.text(value, path, max=4096) is None:
            return None
        url = self._url(value)
        if url is None:
            self.problem(path, "must be an absolute http(s) URL")
            return None
        if url.scheme not in ("http", "https"):
            self.problem(path, "must be an http(s) URL")
            return None
        return url.href

    def scalar(self, x: Any, path: str) -> bool:
        # A string that fails text() is reported twice, as the reference does.
        if isinstance(x, str):
            ok = self.text(x, path, max=500, empty=True) is not None
        else:
            f = _number(x)
            ok = isinstance(x, bool) or (f is not None and math.isfinite(f))
        if not ok:
            self.problem(path, "must be a string, finite number or boolean")
        return ok


def validate(doc: Any, *, base_url: Optional[str] = None, release: str = WUNDERKAMMER) -> Problems:
    """List what is wrong with a collection document; empty means valid.

    ``base_url`` is the URL the document will be served from. Relative
    images and links resolve against it, as the wall resolves them. Leave
    it out to check a document that will sit beside its covers: relative
    images are then accepted as page-relative and relative links refused.

    ``release`` is the Wunderkammer release whose wall will load the
    document, one of ``RELEASES``. Fields added after it are refused, with
    its own supported list, as its wall refuses them.
    """
    if release not in RELEASES:
        raise ValueError(f"unknown Wunderkammer release {release!r} (known: {', '.join(RELEASES)})")
    ui_keys, clip_keys = _supported("ui", UI, release), _supported("clips", CLIP, release)
    ck = _Checker(base_url)
    problem = ck.problem

    if not ck.keys(doc, "collection"):
        return Problems(ck.problems)
    for key in _js_keys(doc):
        if key in SERVER_ONLY:
            problem(f"collection.{key}", "belongs to a wunderkammer server response; a collection document does not carry it")
        elif key not in TOP and key not in FORBIDDEN:
            problem(f"collection.{key}", f"is not supported (supported: {', '.join(TOP)})")
    fmt = _get(doc, "format")
    if not (isinstance(fmt, str) and fmt == FORMAT):
        problem("format", f'must be "{FORMAT}"')
    if _number(_get(doc, "version")) != 1.0:
        problem("version", "must be 1")

    corpus = _get(doc, "corpus")
    if ck.keys(corpus, "corpus", ("id", "revision")):
        ck.text(_get(corpus, "id"), "corpus.id", max=200)
        if "revision" in corpus:
            ck.text(corpus["revision"], "corpus.revision", max=200)

    ui = _get(doc, "ui")
    if ui is not _MISSING and ck.keys(ui, "ui", ui_keys):
        if "title" in ui:
            ck.text(ui["title"], "ui.title", max=200)
        if "defaultGroup" in ui:
            ck.field(ui["defaultGroup"], "ui.defaultGroup")
        if "facetOrder" in ui:
            ck.fields(ui["facetOrder"], "ui.facetOrder", 64)
        if "hiddenFacets" in ui:
            ck.fields(ui["hiddenFacets"], "ui.hiddenFacets", 64)
        if "facetLabels" in ui and ck.keys(ui["facetLabels"], "ui.facetLabels"):
            labels = ui["facetLabels"]
            for k in _js_keys(labels):
                if ck.field(k, f'ui.facetLabels key "{k}"') is not None:
                    ck.text(labels[k], f"ui.facetLabels.{k}", max=120)
        # What the comparison page calls one item and several; both, since a
        # plural cannot be guessed. Both words are checked, as in the reference.
        if "nouns" in ui_keys and "nouns" in ui and ck.keys(ui["nouns"], "ui.nouns", ("item", "items")):
            ck.text(_get(ui["nouns"], "item"), "ui.nouns.item", max=40)
            ck.text(_get(ui["nouns"], "items"), "ui.nouns.items", max=40)

    # Validated and carried; the wall does not yet order or bin by them.
    facet_types = _get(doc, "facetTypes")
    if facet_types is not _MISSING and ck.keys(facet_types, "facetTypes"):
        names = _js_keys(facet_types)
        if len(names) > 64:
            problem("facetTypes", "supports at most 64 attributes")
        for k in names[:64]:
            v, path = facet_types[k], f"facetTypes.{k}"
            if ck.field(k, f'facetTypes key "{k}"') is None or not ck.keys(v, path, ("type", "order")):
                continue
            kind = _get(v, "type")
            if not (isinstance(kind, str) and kind in FACET_TYPES):
                problem(f"{path}.type", f"must be one of {', '.join(FACET_TYPES)}")
                continue
            if "order" in v:
                order = v["order"]
                if kind != "ordinal":
                    problem(f"{path}.order", "is only meaningful for an ordinal facet")
                elif not _is_array(order) or len(order) > 500:
                    problem(f"{path}.order", "must be an array of at most 500 values")
                else:
                    for i, o in enumerate(order):
                        ck.text(o, f"{path}.order[{i}]", max=200)

    images = _get(doc, "images")
    if images is not _MISSING and ck.keys(images, "images", ("cors", "sheets")):
        if "cors" in images and not isinstance(images["cors"], bool):
            problem("images.cors", "must be true or false")
        if "sheets" in images and not (isinstance(images["sheets"], str) and images["sheets"] in SHEET_ROLES):
            problem("images.sheets", f"must be one of {', '.join(SHEET_ROLES)}")

    view_state = _get(doc, "viewState")
    if view_state is not _MISSING and ck.keys(view_state, "viewState", ("version", "mode", "groupKey", "piles")):
        if _number(_get(view_state, "version")) != 1.0:
            problem("viewState.version", "must be 1")
        if "mode" in view_state:
            ck.text(view_state["mode"], "viewState.mode", max=40)
        if "groupKey" in view_state:
            ck.field(view_state["groupKey"], "viewState.groupKey")
        if "piles" in view_state:
            piles = view_state["piles"]
            if not _is_array(piles) or len(piles) > 1000 or not all(_plain(p) for p in piles):
                problem("viewState.piles", "must be an array of at most 1000 pile objects")

    # Sprite sheets: pages that hold every cover; clips point into them
    # with sheetSlots, checked against these bounds below.
    sheets: Optional[List[Optional[Dict[str, float]]]] = None
    if "sheets" in doc:
        raw = doc["sheets"]
        if not _is_array(raw) or not raw or len(raw) > LIMITS["sheets"]:
            problem("sheets", f"must be an array of 1 to {LIMITS['sheets']} {{ src, edge, width, height }} objects")
        else:
            sheets = [_check_sheet(ck, sheet, f"sheets[{i}]") for i, sheet in enumerate(raw)]
    used_sheets = set()

    clips = _get(doc, "clips")
    out_clips: List[Dict[str, Any]] = []
    if not _is_array(clips) or not clips or len(clips) > LIMITS["clips"]:
        problem("clips", f"must be an array of 1 to {LIMITS['clips']} items")
    else:
        seen: Dict[str, int] = {}
        unknown_reported = False
        for i, clip in enumerate(clips):
            path = f"clips[{i}]"
            if not _plain(clip):
                problem(path, "must be an object")
                continue
            for key in _js_keys(clip):
                if key in clip_keys:
                    continue
                if key in FORBIDDEN:
                    problem(f"{path}.{key}", "is not allowed")
                elif not unknown_reported:
                    unknown_reported = True
                    problem(f"{path}.{key}", f"is not supported (supported: {', '.join(clip_keys)}; put other attributes in props)")
                else:
                    problem(f"{path}.{key}", "is not supported")
            out_clips.append(_check_clip(ck, clip, path, i, seen, sheets, used_sheets, clip_keys))

    if ck.problems or ck.overflow:
        return Problems(ck.problems, ck.overflow)

    warnings = []
    if sheets is not None:
        unused = [i for i in range(len(sheets)) if i not in used_sheets]
        if unused:
            listed = ", ".join(f"[{i}]" for i in unused[:10])
            warnings.append(f"sheets {listed}{' …' if len(unused) > 10 else ''} hold no clip's cell; nothing loads them")
    # Counts are derived so they cannot disagree with the clips.
    if "facets" in doc and not _same_counts(doc["facets"], _facets(out_clips)):
        warnings.append("facets differ from the counts derived from clips; the derived counts are used")
    return Problems(warnings=warnings)


def _check_sheet(ck: _Checker, sheet: Any, path: str) -> Optional[Dict[str, float]]:
    if not ck.keys(sheet, path, ("src", "edge", "width", "height")):
        return None
    ok = ck.image(_get(sheet, "src"), f"{path}.src")
    edge = _get(sheet, "edge")
    if not _is_integer(edge) or not 1 <= _number(edge) <= LIMITS["sheetEdge"]:
        ck.problem(f"{path}.edge", f"must be an integer from 1 to {LIMITS['sheetEdge']}")
        ok = False
    for k in ("width", "height"):
        v = _get(sheet, k)
        if not _is_integer(v) or not 1 <= _number(v) <= LIMITS["sheetPx"]:
            ck.problem(f"{path}.{k}", f"must be an integer from 1 to {LIMITS['sheetPx']}")
            ok = False
    if not ok:
        return None
    return {"edge": _number(edge), "width": _number(sheet["width"]), "height": _number(sheet["height"])}


def _check_clip(ck: _Checker, clip: dict, path: str, i: int, seen: Dict[str, int],
                sheets: Optional[list], used_sheets: set, clip_keys: Sequence[str]) -> Dict[str, Any]:
    """One clip's checks, in the reference's order. Returns what facets need.

    ``clip_keys`` are the clip fields the release accepts; one it does not
    was refused as unsupported and is not checked further.
    """
    problem = ck.problem
    c: Dict[str, Any] = {"id": ck.text(_get(clip, "id"), f"{path}.id", max=300)}
    url = None
    if "url" in clip:
        # url is identity first; it is followed only when no sourceUrl is given.
        raw = clip["url"]
        if isinstance(raw, str) and _URN.fullmatch(raw) and _js_len(raw) <= 4096:
            url = raw
        else:
            url = ck.link(raw, f"{path}.url")
    key = url or c["id"]
    key = "null" if key is None else key   # String(null), as the reference keys two bad ids
    if key in seen:
        problem(path, f'repeats the identity of clips[{seen[key]}] ({"url" if url else "id"} "{_js_slice(key, 80)}")')
    else:
        seen[key] = i
    if "title" in clip:
        ck.text(clip["title"], f"{path}.title", max=500, empty=True)
    for name in ("cover", "detailCover"):
        if name in clip:
            ck.image(clip[name], f"{path}.{name}")
    if "coverVariants" in clip:
        variants = clip["coverVariants"]
        if not _is_array(variants) or len(variants) > 8:
            problem(f"{path}.coverVariants", "must be an array of at most 8 { src, width } objects")
        else:
            for j, v in enumerate(variants):
                p = f"{path}.coverVariants[{j}]"
                if not ck.keys(v, p, ("src", "width")):
                    continue
                width = _get(v, "width")
                if not _is_integer(width) or not 1 <= _number(width) <= 8192:
                    problem(f"{p}.width", "must be an integer from 1 to 8192")
                ck.image(_get(v, "src"), f"{p}.src")
    if "media" in clip:
        media = clip["media"]
        if not _is_array(media) or len(media) > 32:
            problem(f"{path}.media", "must be an array of at most 32 { src } objects")
        else:
            for j, m in enumerate(media):
                if ck.keys(m, f"{path}.media[{j}]", ("src",)):
                    ck.image(_get(m, "src"), f"{path}.media[{j}].src")
    if "video" in clip and "video" in clip_keys:
        ck.video(clip["video"], f"{path}.video")
    if "sheetSlots" in clip:
        _check_slots(ck, clip["sheetSlots"], f"{path}.sheetSlots", sheets, used_sheets)
    if "sourceUrl" in clip:
        ck.link(clip["sourceUrl"], f"{path}.sourceUrl")
    if "sourceLabel" in clip:
        ck.text(clip["sourceLabel"], f"{path}.sourceLabel", max=100)
    if "note" in clip:
        ck.text(clip["note"], f"{path}.note", max=20000, empty=True)
    c["tags"] = []
    if "tags" in clip:
        tags = clip["tags"]
        if not _is_array(tags) or len(tags) > 200:
            problem(f"{path}.tags", "must be an array of at most 200 strings")
        else:
            c["tags"] = [ck.text(t, f"{path}.tags[{j}]", max=200) for j, t in enumerate(tags)]
    for name in ("source", "kind"):
        if name in clip:
            c[name] = ck.text(clip[name], f"{path}.{name}", max=200)
    if "captured" in clip:
        captured = clip["captured"]
        if not isinstance(captured, str) or not _CAPTURED.fullmatch(captured):
            problem(f"{path}.captured", "must be an ISO date: YYYY, YYYY-MM, YYYY-MM-DD or a date-time")
        else:
            c["captured"] = captured
    if "props" in clip and ck.keys(clip["props"], f"{path}.props"):
        props = clip["props"]
        names = _js_keys(props)
        if len(names) > 128:
            problem(f"{path}.props", "supports at most 128 attributes")
        c["props"] = {}
        for k in names[:128]:
            v, p = props[k], f"{path}.props.{k}"
            if ck.field(k, f'{path}.props key "{k}"') is None:
                continue
            # The wall reads a clip's own field before props, so these would be invisible.
            if k in clip_keys:
                problem(p, f"is hidden by the clip's own {k} field; rename the attribute")
                continue
            if v is None:
                c["props"][k] = None
            elif _is_array(v):
                if len(v) > 200:
                    problem(p, "supports at most 200 values")
                elif all(ck.scalar(x, f"{p}[{j}]") for j, x in enumerate(v)):   # stops at the first bad value
                    c["props"][k] = list(v)
            elif ck.scalar(v, p):
                c["props"][k] = v
    if "palette" in clip:
        palette = clip["palette"]
        if (not _is_array(palette) or len(palette) > 16
                or not all(isinstance(h, str) and _HEX_COLOR.fullmatch(h) for h in palette)):
            problem(f"{path}.palette", "must be an array of at most 16 #rrggbb colors")
    if "projection" in clip and ck.keys(clip["projection"], f"{path}.projection", ("x", "y", "col", "row")):
        pr = clip["projection"]

        def unit(n: Any) -> bool:
            f = _number(n)
            return f is not None and -1 <= f <= 1

        if not unit(_get(pr, "x")) or not unit(_get(pr, "y")):
            problem(f"{path}.projection", "needs x and y numbers from -1 to 1")
        for k in ("col", "row"):
            if k in pr and not (_is_integer(pr[k]) and _number(pr[k]) >= 0):
                problem(f"{path}.projection.{k}", "must be a non-negative integer")
    return c


def _check_slots(ck: _Checker, slots: Any, path: str, sheets: Optional[list], used_sheets: set) -> None:
    limit = LIMITS["sheetSlots"]
    if sheets is None:
        ck.problem(path, "needs a top-level sheets list to point into")
        return
    if not _is_array(slots) or not slots or len(slots) > limit:
        ck.problem(path, f"must be an array of 1 to {limit} [sheet, x, y, w, h] cells")
        return
    levels = set()
    for j, cell in enumerate(slots):
        q = f"{path}[{j}]"
        if not _is_array(cell) or len(cell) != 5 or not all(_is_integer(v) for v in cell):
            ck.problem(q, "must be [sheet, x, y, w, h], five integers")
            continue
        index, x, y, w, h = (_number(v) for v in cell)
        in_range = 0 <= index < len(sheets)
        sheet = sheets[int(index)] if in_range else None
        if sheet is None:
            ck.problem(q, f"points at sheets[{_js_num(index)}], {'which is not valid' if in_range else 'which does not exist'}")
            continue
        if x < 0 or y < 0 or w < 1 or h < 1 or x + w > sheet["width"] or y + h > sheet["height"]:
            ck.problem(q, f"must lie inside sheets[{_js_num(index)}] ({_js_num(sheet['width'])}×{_js_num(sheet['height'])})")
            continue
        # Tiers pick a cell by its level's edge, so a cell may not exceed it.
        if max(w, h) > sheet["edge"]:
            ck.problem(q, f"is larger than its sheet's edge ({_js_num(sheet['edge'])})")
            continue
        if sheet["edge"] in levels:
            ck.problem(q, f"repeats the {_js_num(sheet['edge'])} px level; give one cell per level")
            continue
        levels.add(sheet["edge"])
        used_sheets.add(int(index))


# ─── facet counts (wall/facet-counts.mjs) ────────────────────────────────

def _facets(clips: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """``buildFacets()``: value counts per facet, derived from the clips."""
    facets: Dict[str, Dict[str, int]] = {"tags": {}, "source": {}, "kind": {}, "captured": {}}
    by_prop: Dict[str, Dict[str, int]] = {}

    def bump(bucket: Dict[str, int], value: str) -> None:
        bucket[value] = bucket.get(value, 0) + 1

    for c in clips:
        for t in c.get("tags") or []:
            bump(facets["tags"], _js_string(t))
        for name in ("source", "kind"):
            if c.get(name):
                bump(facets[name], c[name])
        month = _js_slice(c.get("captured") or "", 7)
        if month:
            bump(facets["captured"], month)
        props = c.get("props") or {}
        for k in _js_keys(props):
            v = props[k]
            if v is None or (isinstance(v, str) and v == ""):
                continue
            bucket = by_prop.setdefault(k, {})
            for item in (v if _is_array(v) else [v]):
                bump(bucket, _js_string(item))
    facets.update(by_prop)
    return facets


def _entries(v: Any) -> List[list]:
    """``Object.entries(v || {})``."""
    if isinstance(v, dict):
        return [[k, v[k]] for k in _js_keys(v)]
    if _is_array(v):
        return [[str(i), x] for i, x in enumerate(v)]
    if isinstance(v, str) and v:
        units = v.encode("utf-16-le", "surrogatepass")
        return [[str(i), units[2 * i:2 * i + 2].decode("utf-16-le", "surrogatepass")] for i in range(len(units) // 2)]
    return []


def _js_json(v: Any) -> str:
    """``JSON.stringify(v)``, enough to compare two values the way the reference does."""
    if v is None or isinstance(v, bool):
        return json.dumps(v)
    if isinstance(v, (int, float)):
        f = _number(v)
        return _js_num(f) if math.isfinite(f) else "null"
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if _is_array(v):
        return "[" + ",".join(_js_json(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ",".join(json.dumps(str(k), ensure_ascii=False) + ":" + _js_json(v[k]) for k in _js_keys(v)) + "}"
    return "null"


def _same_counts(a: Any, b: Dict[str, Dict[str, int]]) -> bool:
    if not _plain(a):
        return False

    def norm(f: dict) -> str:
        return _js_json([[k, sorted(_entries(f[k]), key=lambda e: _utf16(_js_string(e)))]
                         for k in sorted(_js_keys(f), key=lambda k: _utf16(str(k)))])

    return norm(a) == norm(b)


# ─── build ───────────────────────────────────────────────────────────────

#: Image types a browser shows as a cover.
IMAGE_SUFFIXES = (".apng", ".avif", ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp")
#: CSV columns read as clip fields; every other column becomes a prop.
CSV_COLUMNS = ("id", "title", "cover", "sourceUrl", "captured")


def build(source: Union[str, Path], *, title: Optional[str] = None, group: Optional[str] = None,
          relative_to: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Build a collection document from a folder of images or a CSV.

    A folder gives one clip per image (``IMAGE_SUFFIXES``, hidden files
    skipped, subfolders included): ``id`` is the file's path relative to
    the folder, ``title`` its name without the extension, ``cover`` its
    path relative to ``relative_to`` (the folder itself by default; pass
    the directory the document will be saved in), ``captured`` the EXIF
    capture time when Pillow can read one and the file's modification time
    otherwise, and ``props.width`` / ``props.height`` its pixel size.

    A CSV gives one clip per row. The columns ``id``, ``title``, ``cover``,
    ``sourceUrl`` and ``captured`` fill those fields, written as given;
    every other column becomes a prop, as a string. A cell becomes an
    array only when its column header ends in ``[]`` (``genre[]``), split on
    commas. Empty cells are left out.

    ``title`` sets ``ui.title`` (default: the folder or file name) and
    ``group`` sets ``ui.defaultGroup``, which must name an attribute some
    clip has. Raises ``ValueError`` for a source that yields no clips or a
    CSV it cannot map; the result may still have problems
    :func:`validate` reports (a bad ``sourceUrl`` in a CSV, say).
    """
    src = Path(source)
    if src.is_dir():
        clips = _clips_from_folder(src, Path(relative_to) if relative_to is not None else src)
        name = src.resolve().name
    elif src.is_file() and src.suffix.lower() == ".csv":
        clips = _clips_from_csv(src)
        name = src.stem
    elif not src.exists():
        raise FileNotFoundError(f"no such folder or file: {src}")
    else:
        raise ValueError(f"{src} is neither a folder of images nor a .csv file")
    name = name or "collection"

    digest = hashlib.sha256(json.dumps(clips, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    doc: Dict[str, Any] = {
        "format": FORMAT,
        "version": VERSION,
        # The revision changes whenever the clips do, so a comparison recipe
        # written against this document can tell it has gone stale.
        "corpus": {"id": name, "revision": digest[:16]},
        "ui": {"title": title if title is not None else name},
        "clips": clips,
    }
    if group is not None:
        available = sorted({"captured"} & {k for c in clips for k in c}
                           | {k for c in clips for k in c.get("props", {})})
        if group not in available:
            raise ValueError(f"group {group!r} is not an attribute of any clip "
                             f"(available: {', '.join(available) or 'none'})")
        doc["ui"]["defaultGroup"] = group
    return doc


def _clips_from_folder(folder: Path, relative_to: Path) -> List[Dict[str, Any]]:
    folder = folder.resolve()
    base = relative_to.resolve()
    found: List[Tuple[str, Path]] = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for f in filenames:
            if not f.startswith(".") and os.path.splitext(f)[1].lower() in IMAGE_SUFFIXES:
                path = Path(dirpath) / f
                found.append((path.relative_to(folder).as_posix(), path))
    if not found:
        raise ValueError(f"no images in {folder} (looked for {', '.join(IMAGE_SUFFIXES)})")
    clips = []
    for rel, path in sorted(found):
        info = _image_info(path)
        clip: Dict[str, Any] = {"id": rel, "title": path.stem, "cover": _url_path(os.path.relpath(path, base))}
        clip["captured"] = info.get("captured") or _mtime(path)
        props = {k: info[k] for k in ("width", "height") if k in info}
        if props:
            clip["props"] = props
        clips.append(clip)
    return clips


def _url_path(rel: str) -> str:
    """A relative file path as a relative URL: each segment percent-encoded.

    ``#``, ``?`` and ``%`` would otherwise end or garble the path, and a
    colon in the first segment would read as a scheme (``c:x.png``).
    """
    return "/".join(quote(seg, safe="!$&'()*+,;=@") for seg in Path(rel).as_posix().split("/"))


def _mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")


_EXIF_DATE = re.compile(r"([0-9]{4}):([0-9]{2}):([0-9]{2})[ T]([0-9]{2}):([0-9]{2}):([0-9]{2})")
_EXIF_OFFSET = re.compile(r"[+-][0-9]{2}:[0-9]{2}")


def _image_info(path: Path) -> Dict[str, Any]:
    """Pixel size, and EXIF capture time when Pillow is installed."""
    info = _pillow_info(path)
    if info is None:
        size = _sniff_size(path)
        info = {"width": size[0], "height": size[1]} if size else {}
    return info


def _pillow_info(path: Path) -> Optional[Dict[str, Any]]:
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as im:
            width, height = im.size
            exif = im.getexif()
    except Exception:   # Pillow raises a dozen types for files it cannot read (SVG, AVIF without a plugin)
        return None
    info: Dict[str, Any] = {"width": width, "height": height}
    if exif.get(0x0112) in (5, 6, 7, 8):   # Orientation: displayed rotated a quarter turn
        info["width"], info["height"] = height, width
    try:
        sub = exif.get_ifd(0x8769)   # the Exif IFD
    except Exception:
        sub = {}
    for tag, offset_tag in ((0x9003, 0x9011), (0x9004, 0x9012)):   # DateTimeOriginal, DateTimeDigitized
        m = _EXIF_DATE.match(str(sub.get(tag) or "").strip("\x00 "))
        if m and m.group(1) != "0000":
            captured = "{}-{}-{}T{}:{}:{}".format(*m.groups())
            offset = str(sub.get(offset_tag) or "").strip("\x00 ")
            info["captured"] = captured + (offset if _EXIF_OFFSET.fullmatch(offset) else "")
            break
    return info


def _sniff_size(path: Path) -> Optional[Tuple[int, int]]:
    """Width and height from the file header, for when Pillow is absent.

    PNG, GIF, BMP, WebP and JPEG. EXIF orientation is not applied here.
    """
    try:
        with open(path, "rb") as fh:
            head = fh.read(32)
            if head.startswith(b"\x89PNG\r\n\x1a\n") and head[12:16] == b"IHDR":
                return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
            if head[:6] in (b"GIF87a", b"GIF89a"):
                return int.from_bytes(head[6:8], "little"), int.from_bytes(head[8:10], "little")
            if head[:2] == b"BM" and len(head) >= 26:
                return (int.from_bytes(head[18:22], "little", signed=True),
                        abs(int.from_bytes(head[22:26], "little", signed=True)))
            if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
                return _webp_size(head + fh.read(32))
            if head[:2] == b"\xff\xd8":
                fh.seek(2)
                return _jpeg_size(fh)
    except OSError:
        return None
    return None


def _webp_size(b: bytes) -> Optional[Tuple[int, int]]:
    chunk = b[12:16]
    if chunk == b"VP8 " and len(b) >= 30:
        return int.from_bytes(b[26:28], "little") & 0x3FFF, int.from_bytes(b[28:30], "little") & 0x3FFF
    if chunk == b"VP8L" and len(b) >= 25:
        b0, b1, b2, b3 = b[21:25]
        return 1 + (((b1 & 0x3F) << 8) | b0), 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
    if chunk == b"VP8X" and len(b) >= 30:
        return 1 + int.from_bytes(b[24:27], "little"), 1 + int.from_bytes(b[27:30], "little")
    return None


def _jpeg_size(fh) -> Optional[Tuple[int, int]]:
    while True:
        byte = fh.read(1)
        while byte and byte != b"\xff":
            byte = fh.read(1)
        while byte == b"\xff":
            byte = fh.read(1)
        if not byte:
            return None
        marker = byte[0]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            continue   # markers without a length
        if marker in (0xD9, 0xDA):
            return None   # end of image, or start of scan before any frame header
        length = int.from_bytes(fh.read(2), "big")
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):   # a start-of-frame
            data = fh.read(5)
            if len(data) < 5:
                return None
            return int.from_bytes(data[3:5], "big"), int.from_bytes(data[1:3], "big")
        if length < 2:
            return None
        fh.seek(length - 2, os.SEEK_CUR)


def _clips_from_csv(path: Path) -> List[Dict[str, Any]]:
    # utf-8-sig: spreadsheet exports often begin with a byte-order mark.
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if not header or not any(h.strip() for h in header):
            raise ValueError(f"{path} has no header row")
        columns = _csv_columns(header, path)
        clips = []
        for row in reader:
            if not any(cell.strip() for cell in row):
                continue
            line = reader.line_num
            if len(row) > len(columns):
                raise ValueError(f"{path}, line {line}: {len(row)} cells under a {len(columns)}-column header")
            clip: Dict[str, Any] = {}
            props: Dict[str, Any] = {}
            for (name, is_list), cell in zip(columns, row):
                value = cell.strip()
                if not value:
                    continue
                if name in CSV_COLUMNS:
                    clip[name] = value
                elif is_list:
                    items = [v.strip() for v in value.split(",") if v.strip()]
                    if items:
                        props[name] = items
                else:
                    props[name] = value
            if "id" not in clip:
                raise ValueError(f"{path}, line {line}: the id cell is empty")
            ordered = {k: clip[k] for k in CSV_COLUMNS if k in clip}
            if props:
                ordered["props"] = props
            clips.append(ordered)
    if not clips:
        raise ValueError(f"{path} has a header but no rows")
    return clips


def _csv_columns(header: List[str], path: Path) -> List[Tuple[str, bool]]:
    columns: List[Tuple[str, bool]] = []
    for n, raw in enumerate(header, start=1):
        h = raw.strip()
        is_list = h.endswith("[]")
        name = h[:-2].strip() if is_list else h
        where = f"{path}, column {n} ({raw!r})"
        if not name:
            raise ValueError(f"{where}: the column has no name")
        if name in CSV_COLUMNS and is_list:
            raise ValueError(f"{where}: {name} holds one value; drop the []")
        if name in CLIP and name not in CSV_COLUMNS:
            raise ValueError(f"{where}: {name} is a clip field the CSV builder does not fill, "
                             f"and a prop may not shadow a clip field; rename the column")
        if name in FORBIDDEN:
            raise ValueError(f"{where}: {name} is not a supported attribute name")
        if any(name == c for c, _ in columns):
            raise ValueError(f"{where}: {name} appears twice")
        columns.append((name, is_list))
    if not any(name == "id" for name, _ in columns):
        raise ValueError(f"{path} has no id column; every clip needs an id "
                         f"(columns: {', '.join(c for c, _ in columns)})")
    return columns


# ─── CLI ─────────────────────────────────────────────────────────────────

def _say(text: str, stream=None) -> None:
    """Print without dying on a terminal that cannot encode the text."""
    stream = stream or sys.stdout
    encoding = getattr(stream, "encoding", None) or "utf-8"
    print(text.encode(encoding, "backslashreplace").decode(encoding), file=stream)


def _not_json(constant: str) -> Any:
    # Python's json accepts NaN and Infinity; JSON.parse does not.
    raise ValueError(f"{constant} is not a JSON value")


def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m muriel.collection",
        description="Build and validate Wunderkammer collection documents (format wunderkammer.collection, version 1).",
    )
    sub = parser.add_subparsers(dest="command", metavar="{build,validate}")
    sub.required = True

    b = sub.add_parser("build", help="Write a collection document from a folder of images or a CSV.",
                       description="Write a collection document from a folder of images or a CSV, "
                                   "and check it before writing. Nothing is written when it has problems.")
    b.add_argument("source", type=Path, help="A folder of images or a .csv file.")
    b.add_argument("--out", type=Path, required=True, help="Where to write the document. Folder covers are written relative to it.")
    b.add_argument("--title", default=None, help="ui.title (default: the folder or file name).")
    b.add_argument("--group", metavar="FIELD", default=None, help="ui.defaultGroup: the attribute the wall groups by first.")

    v = sub.add_parser("validate", help="Check a collection document and list its problems.",
                       description="Check a collection document. Exit 0 when valid, 1 with problems "
                                   "(each printed with its path), 2 when nothing was read or it is not JSON.")
    v.add_argument("document", help="A collection.json, or - for standard input.")
    v.add_argument("--base-url", default=None,
                   help="The URL the document will be served from. Relative covers and links resolve "
                        "against it, as the wall resolves them.")
    v.add_argument("--release", choices=RELEASES, default=WUNDERKAMMER,
                   help=f"The Wunderkammer release whose wall will load it (default {WUNDERKAMMER}, the release "
                        "muriel's collections reference pins; 0.1.0 refuses ui.nouns).")
    args = parser.parse_args(argv)

    if args.command == "build":
        return _build_command(args)
    return _validate_command(args)


def _build_command(args) -> int:
    try:
        doc = build(args.source, title=args.title, group=args.group,
                    relative_to=args.out.parent if args.source.is_dir() else None)
    except (OSError, ValueError, UnicodeDecodeError, csv.Error) as exc:
        _say(f"error: {exc}", sys.stderr)
        return 2
    problems = validate(doc)
    if problems:
        _say(format_problems(problems))
        _say(f"nothing written to {args.out}", sys.stderr)
        return 1
    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as exc:
        _say(f"error: {exc}", sys.stderr)
        return 2
    _say(f"wrote {args.out}: {len(doc['clips'])} clips")
    for w in problems.warnings:
        _say(f"warning: {w}", sys.stderr)
    return 0


def _validate_command(args) -> int:
    name = "standard input" if args.document == "-" else args.document
    try:
        if args.document == "-":
            raw = sys.stdin.read()
        else:
            # utf-8-sig: a browser's response.json() strips a byte-order mark too.
            raw = Path(args.document).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        _say(f"error: cannot read {name}: {exc}", sys.stderr)
        return 2
    if not raw.strip():
        _say(f"error: {name} is empty", sys.stderr)
        return 2
    try:
        doc = json.loads(raw.lstrip("﻿"), parse_constant=_not_json)
    except ValueError as exc:
        _say(f"error: {name} is not JSON: {exc}", sys.stderr)
        return 2
    problems = validate(doc, base_url=args.base_url, release=args.release)
    if problems:
        _say(format_problems(problems))
        for field, since in _too_new(problems, args.release):
            _say(f"note: {field} is newer than Wunderkammer {args.release}; "
                 f"for a wall from release {since}, validate with --release {since}", sys.stderr)
        return 1
    _say(f"{name}: valid ({len(doc['clips'])} clips)")
    for w in problems.warnings:
        _say(f"warning: {w}", sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
