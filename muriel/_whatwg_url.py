"""
muriel._whatwg_url — the WHATWG URL Standard's basic URL parser, in Python.

Exists so ``muriel.collection`` can decide what ``new URL(value, base)``
decides in a browser or Node: whether a string parses at all, what its
scheme is, and what ``href`` it serializes to (a clip's ``url`` is its
identity, so two spellings of one URL must collide here as they do in
the reference validator). ``urllib.parse`` follows RFC 3986, which
accepts strings the URL Standard refuses (``http://a b/``) and refuses
none of the hosts it does, so it cannot stand in.

Ported state by state from https://url.spec.whatwg.org/#concept-basic-url-parser,
without state overrides (no setters are needed). Calibrated against
Node's parser (ada), which, like the reference validator's test run,
lowercases ASCII hosts without validating ``xn--`` labels.

Where it cannot match: non-ASCII hosts. The standard runs UTS #46, whose
mapping table is not in the standard library. ``_uts46_label`` stands in
with NFKC + lowercase, the default-ignorable removals, the
combining-mark, joiner and bidi rules, and ``unicodedata``'s idea of
which code points are assigned, which follows the Python version.
ASCII hosts, which is nearly every URL a collection carries, take the
standard's own ASCII path and match exactly.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Optional, Union

SPECIAL = {"ftp": 21, "file": None, "http": 80, "https": 443, "ws": 80, "wss": 443}

_C0_SPACE = "".join(chr(i) for i in range(0x21))
_TAB_NEWLINE = re.compile("[\t\n\r]")

# Percent-encode sets (URL Standard §1.3). Every set encodes C0 controls
# and everything above U+007E; the strings are each set's ASCII additions.
# Compiled to one character class each, so a run of text encodes in one
# pass: a 1 MB data: URL must not cost a million function calls.
def _set(extra: str) -> "re.Pattern[str]":
    return re.compile("[\x00-\x1f\x7f-\U0010ffff" + "".join(re.escape(c) for c in extra) + "]")


_C0 = _set("")
_FRAGMENT = _set(' "<>`')
_QUERY = _set(' "#<>')
_SPECIAL_QUERY = _set(' "#<>\'')
_PATH = _set(' "#<>?^`{}')
_USERINFO = _set(' "#<>?^`{}/:;=@[\\]|')

_FORBIDDEN_HOST = frozenset("\x00\t\n\r #/:<>?@[\\]^|")
_FORBIDDEN_DOMAIN = _FORBIDDEN_HOST | frozenset(chr(i) for i in range(0x20)) | {"%", "\x7f"}

_ASCII_ALPHA = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
_ASCII_DIGIT = frozenset("0123456789")
_ASCII_HEX = _ASCII_DIGIT | frozenset("abcdefABCDEF")
_SCHEME_CHAR = _ASCII_ALPHA | _ASCII_DIGIT | frozenset("+-.")

_EOF = None


class URL:
    """A parsed URL record: just enough to read ``scheme`` and ``href``."""

    __slots__ = ("scheme", "username", "password", "host", "port", "path", "query", "fragment")

    def __init__(self) -> None:
        self.scheme = ""
        self.username = ""
        self.password = ""
        self.host: Optional[str] = None   # serialized; "" is the empty host
        self.port: Optional[int] = None
        self.path: Union[List[str], str] = []   # a str is an opaque path
        self.query: Optional[str] = None
        self.fragment: Optional[str] = None

    @property
    def special(self) -> bool:
        return self.scheme in SPECIAL

    @property
    def opaque(self) -> bool:
        return isinstance(self.path, str)

    @property
    def protocol(self) -> str:
        return self.scheme + ":"

    @property
    def href(self) -> str:
        out = self.scheme + ":"
        if self.host is not None:
            out += "//"
            if self.username or self.password:
                out += self.username
                if self.password:
                    out += ":" + self.password
                out += "@"
            out += self.host
            if self.port is not None:
                out += ":" + str(self.port)
        if self.opaque:
            out += self.path
        else:
            if self.host is None and len(self.path) > 1 and self.path[0] == "":
                out += "/."
            out += "".join("/" + seg for seg in self.path)
        if self.query is not None:
            out += "?" + self.query
        if self.fragment is not None:
            out += "#" + self.fragment
        return out


# ─── helpers ─────────────────────────────────────────────────────────────

def _usv(s: str) -> str:
    """Pair surrogates and replace lone ones with U+FFFD, as a USVString does."""
    return s.encode("utf-16-le", "surrogatepass").decode("utf-16-le", "replace")


def _encode(s: str, encode_set: "re.Pattern[str]") -> str:
    return encode_set.sub(lambda m: "".join(f"%{b:02X}" for b in m.group().encode("utf-8")), s)


def _until(s: str, start: int, stops: "re.Pattern[str]") -> int:
    """Index of the first stop character at or after ``start``, else len(s)."""
    m = stops.search(s, start)
    return m.start() if m else len(s)


_STOP_OPAQUE = re.compile("[?#]")
_STOP_PATH = re.compile("[/?#]")
_STOP_SPECIAL_PATH = re.compile("[/\\\\?#]")


def _percent_decode(s: str) -> bytes:
    data = s.encode("utf-8")
    out = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if (b == 0x25 and i + 2 < len(data)
                and chr(data[i + 1]) in _ASCII_HEX and chr(data[i + 2]) in _ASCII_HEX):
            out.append(int(data[i + 1:i + 3], 16))
            i += 3
        else:
            out.append(b)
            i += 1
    return bytes(out)


def _ascii_lower(s: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in s)


def _is_drive(s: str) -> bool:
    return len(s) == 2 and s[0] in _ASCII_ALPHA and s[1] in ":|"


def _is_normalized_drive(s: str) -> bool:
    return len(s) == 2 and s[0] in _ASCII_ALPHA and s[1] == ":"


def _starts_with_drive(s: str) -> bool:
    return len(s) >= 2 and _is_drive(s[:2]) and (len(s) == 2 or s[2] in "/\\?#")


def _single_dot(s: str) -> bool:
    return s == "." or s.lower() == "%2e"


def _double_dot(s: str) -> bool:
    return s.lower() in ("..", ".%2e", "%2e.", "%2e%2e")


def _shorten(url: URL) -> None:
    path = url.path
    if url.scheme == "file" and len(path) == 1 and _is_normalized_drive(path[0]):
        return
    if path:
        path.pop()


# ─── hosts ───────────────────────────────────────────────────────────────

def _ipv4_number(s: str):
    if not s:
        return None
    radix = 10
    if len(s) >= 2 and s[:2] in ("0x", "0X"):
        s, radix = s[2:], 16
    elif len(s) >= 2 and s[0] == "0":
        s, radix = s[1:], 8
    if not s:
        return 0
    digits = {10: _ASCII_DIGIT, 16: _ASCII_HEX, 8: frozenset("01234567")}[radix]
    if any(c not in digits for c in s):
        return None
    return int(s, radix)


def _ends_in_number(s: str) -> bool:
    parts = s.split(".")
    if parts[-1] == "":
        if len(parts) == 1:
            return False
        parts.pop()
    last = parts[-1]
    if last and all(c in _ASCII_DIGIT for c in last):
        return True
    return _ipv4_number(last) is not None


def _ipv4(s: str) -> Optional[str]:
    parts = s.split(".")
    if parts[-1] == "" and len(parts) > 1:
        parts.pop()
    if len(parts) > 4:
        return None
    numbers = []
    for part in parts:
        n = _ipv4_number(part)
        if n is None:
            return None
        numbers.append(n)
    if any(n > 255 for n in numbers[:-1]):
        return None
    if numbers[-1] >= 256 ** (5 - len(numbers)):
        return None
    ipv4 = numbers[-1]
    for i, n in enumerate(numbers[:-1]):
        ipv4 += n * 256 ** (3 - i)
    return ".".join(str((ipv4 >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def _ipv6(s: str) -> Optional[str]:
    address = [0] * 8
    piece = 0
    compress = None
    p = 0
    n = len(s)

    def at(i):
        return s[i] if i < n else _EOF

    if at(p) == ":":
        if at(p + 1) != ":":
            return None
        p += 2
        piece += 1
        compress = piece
    while at(p) is not _EOF:
        if piece == 8:
            return None
        if at(p) == ":":
            if compress is not None:
                return None
            p += 1
            piece += 1
            compress = piece
            continue
        value = length = 0
        while length < 4 and at(p) is not _EOF and at(p) in _ASCII_HEX:
            value = value * 16 + int(at(p), 16)
            p += 1
            length += 1
        if at(p) == ".":
            if length == 0:
                return None
            p -= length
            if piece > 6:
                return None
            seen = 0
            while at(p) is not _EOF:
                v4 = None
                if seen > 0:
                    if at(p) == "." and seen < 4:
                        p += 1
                    else:
                        return None
                if at(p) is _EOF or at(p) not in _ASCII_DIGIT:
                    return None
                while at(p) is not _EOF and at(p) in _ASCII_DIGIT:
                    d = int(at(p))
                    if v4 is None:
                        v4 = d
                    elif v4 == 0:
                        return None
                    else:
                        v4 = v4 * 10 + d
                    if v4 > 255:
                        return None
                    p += 1
                address[piece] = address[piece] * 0x100 + v4
                seen += 1
                if seen in (2, 4):
                    piece += 1
            if seen != 4:
                return None
            break
        elif at(p) == ":":
            p += 1
            if at(p) is _EOF:
                return None
        elif at(p) is not _EOF:
            return None
        address[piece] = value
        piece += 1
    if compress is not None:
        swaps = piece - compress
        piece = 7
        while piece != 0 and swaps > 0:
            j = compress + swaps - 1
            address[piece], address[j] = address[j], address[piece]
            piece -= 1
            swaps -= 1
    elif piece != 8:
        return None
    # Serialize: compress the first longest run of two or more zero pieces.
    best_start, best_len, i = None, 1, 0
    while i < 8:
        if address[i] == 0:
            j = i
            while j < 8 and address[j] == 0:
                j += 1
            if j - i > best_len:
                best_start, best_len = i, j - i
            i = j
        else:
            i += 1
    out, ignore0 = "", False
    for i in range(8):
        if ignore0 and address[i] == 0:
            continue
        ignore0 = False
        if best_start == i:
            out += "::" if i == 0 else ":"
            ignore0 = True
            continue
        out += format(address[i], "x")
        if i != 7:
            out += ":"
    return "[" + out + "]"


# Code points UTS #46 drops ("ignored"), which NFKC keeps.
_IGNORED = frozenset(
    [0x00AD, 0x034F, 0x180B, 0x180C, 0x180D, 0x180F, 0x200B, 0xFEFF]
    + list(range(0x2060, 0x2065)) + list(range(0x206A, 0x2070))
    + list(range(0xFE00, 0xFE10)) + list(range(0x1BCA0, 0x1BCA4)) + list(range(0xE0100, 0xE01F0))
)
_JOINERS = frozenset("\u200c\u200d")
# Kept as themselves by nontransitional processing, where casefolding changes them.
_DEVIATIONS = frozenset("\u00df\u03c2")
_SEPARATORS = frozenset(".\u3002\uff0e\uff61")
_BAD_CATEGORIES = ("Cc", "Cf", "Cn", "Co", "Cs", "Zs", "Zl", "Zp")
_RTL = ("R", "AL", "AN")


def _uts46_map(domain: str) -> Optional[str]:
    """NFKC_Casefold with UTS #46's exceptions, or None for a disallowed code point."""
    out = []
    for ch in domain:
        if ord(ch) in _IGNORED:
            continue
        if ch == "\ufffd":
            return None
        if ch in _SEPARATORS:
            out.append(".")
        elif ch in _DEVIATIONS or ch in _JOINERS:
            out.append(ch)
        else:
            mapped = unicodedata.normalize("NFKC", ch)
            if any(c in _SEPARATORS for c in mapped):
                return None   # U+2024 ONE DOT LEADER and kin: disallowed, not a label break
            out.append(unicodedata.normalize("NFKC", mapped.casefold()))
    return unicodedata.normalize("NFC", "".join(out))


def _uts46_label(label: str) -> Optional[str]:
    """Approximate UTS #46 validity for one mapped, non-ASCII label."""
    if not label:
        return label
    if unicodedata.category(label[0]).startswith("M"):
        return None
    for i, ch in enumerate(label):
        if ch in _JOINERS:
            # CheckJoiners: a joiner is valid only after a virama.
            if i == 0 or unicodedata.combining(label[i - 1]) != 9:
                return None
            continue
        if unicodedata.category(ch) in _BAD_CATEGORIES:
            return None
    return label


def _bidi_ok(label: str) -> bool:
    """RFC 5893's rule for one label of a domain that contains RTL text."""
    if not label:
        return True
    classes = [unicodedata.bidirectional(c) for c in label]
    trimmed = classes[:]
    while trimmed and trimmed[-1] == "NSM":
        trimmed.pop()
    if not trimmed:
        return False
    first, last = classes[0], trimmed[-1]
    if first in ("R", "AL"):
        allowed = {"R", "AL", "AN", "EN", "ES", "CS", "ET", "ON", "BN", "NSM"}
        if any(c not in allowed for c in classes) or last not in ("R", "AL", "EN", "AN"):
            return False
        return not ("EN" in classes and "AN" in classes)
    if first == "L":
        allowed = {"L", "EN", "ES", "CS", "ET", "ON", "BN", "NSM"}
        return all(c in allowed for c in classes) and last in ("L", "EN")
    return False


def _decode_xn(label: str) -> Optional[str]:
    """An ``xn--`` label, decoded and checked as UTS #46 does, else None."""
    if not label.isascii():
        return None
    try:
        decoded = label[4:].encode("ascii").decode("punycode")
    except (UnicodeError, ValueError):
        return None
    if not decoded or decoded.isascii():
        return None
    if _uts46_map(decoded) != decoded:
        return None   # not already in mapped form
    return _uts46_label(decoded)


def _domain_to_ascii(domain: str) -> Optional[str]:
    if domain.isascii():
        # Node's parser lowercases any ASCII domain, xn-- labels included.
        result = _ascii_lower(domain)
    else:
        mapped = _uts46_map(domain)
        if mapped is None:
            return None
        labels = mapped.split(".")
        out = []
        for label in labels:
            if label.startswith("xn--"):
                # Once a host is not ASCII, every xn-- label is decoded and
                # checked, where the ASCII path above passes them through.
                label = _decode_xn(label)
                if label is None:
                    return None
            elif not label.isascii() and _uts46_label(label) is None:
                return None
            # Node applies the bidi rule only to labels that hold RTL text.
            if any(unicodedata.bidirectional(c) in _RTL for c in label) and not _bidi_ok(label):
                return None
            out.append(label if label.isascii() else "xn--" + label.encode("punycode").decode("ascii"))
        result = ".".join(out)
    if not result or any(c in _FORBIDDEN_DOMAIN for c in result):
        return None
    return result


def _host(s: str, opaque: bool) -> Optional[str]:
    if s.startswith("["):
        if not s.endswith("]"):
            return None
        return _ipv6(s[1:-1])
    if opaque:
        if any(c in _FORBIDDEN_HOST for c in s):
            return None
        return _encode(s, _C0)
    domain = _percent_decode(s).decode("utf-8", "replace")
    ascii_domain = _domain_to_ascii(domain)
    if ascii_domain is None:
        return None
    if _ends_in_number(ascii_domain):
        return _ipv4(ascii_domain)
    return ascii_domain


# ─── the parser ──────────────────────────────────────────────────────────

def parse(value: str, base: Optional[Union[str, URL]] = None) -> Optional[URL]:
    """``new URL(value, base)``: the URL record, or None where JS throws."""
    if isinstance(base, str):
        base = parse(base)
        if base is None:
            return None
    s = _usv(_TAB_NEWLINE.sub("", value.strip(_C0_SPACE)))
    return _basic_parse(s, base)


def _basic_parse(s: str, base: Optional[URL]) -> Optional[URL]:  # noqa: C901 — one state machine
    url = URL()
    state = "scheme start"
    buf = ""
    at_seen = in_brackets = password_seen = False
    n = len(s)
    p = 0

    while True:
        c = s[p] if p < n else _EOF
        special = url.special

        if state == "scheme start":
            if c is not _EOF and c in _ASCII_ALPHA:
                buf += c.lower()
                state = "scheme"
            else:
                state = "no scheme"
                p -= 1

        elif state == "scheme":
            if c is not _EOF and c in _SCHEME_CHAR:
                buf += c.lower()
            elif c == ":":
                url.scheme, buf = buf, ""
                if url.scheme == "file":
                    state = "file"
                elif url.special and base is not None and base.scheme == url.scheme:
                    state = "special relative or authority"
                elif url.special:
                    state = "special authority slashes"
                elif s.startswith("/", p + 1):
                    state = "path or authority"
                    p += 1
                else:
                    url.path = ""
                    state = "opaque path"
            else:
                buf = ""
                state = "no scheme"
                p = -1

        elif state == "no scheme":
            if base is None or (base.opaque and c != "#"):
                return None
            if base.opaque and c == "#":
                url.scheme, url.path, url.query = base.scheme, base.path, base.query
                url.fragment = ""
                state = "fragment"
            elif base.scheme != "file":
                state = "relative"
                p -= 1
            else:
                state = "file"
                p -= 1

        elif state == "special relative or authority":
            if c == "/" and s.startswith("/", p + 1):
                state = "special authority ignore slashes"
                p += 1
            else:
                state = "relative"
                p -= 1

        elif state == "path or authority":
            if c == "/":
                state = "authority"
            else:
                state = "path"
                p -= 1

        elif state == "relative":
            url.scheme = base.scheme
            special = url.special
            if c == "/":
                state = "relative slash"
            elif special and c == "\\":
                state = "relative slash"
            else:
                url.username, url.password = base.username, base.password
                url.host, url.port = base.host, base.port
                url.path, url.query = list(base.path), base.query
                if c == "?":
                    url.query = ""
                    state = "query"
                elif c == "#":
                    url.fragment = ""
                    state = "fragment"
                elif c is not _EOF:
                    url.query = None
                    _shorten(url)
                    state = "path"
                    p -= 1

        elif state == "relative slash":
            if special and c in ("/", "\\"):
                state = "special authority ignore slashes"
            elif c == "/":
                state = "authority"
            else:
                url.username, url.password = base.username, base.password
                url.host, url.port = base.host, base.port
                state = "path"
                p -= 1

        elif state == "special authority slashes":
            if c == "/" and s.startswith("/", p + 1):
                state = "special authority ignore slashes"
                p += 1
            else:
                state = "special authority ignore slashes"
                p -= 1

        elif state == "special authority ignore slashes":
            if c not in ("/", "\\"):
                state = "authority"
                p -= 1

        elif state == "authority":
            if c == "@":
                if at_seen:
                    buf = "%40" + buf
                at_seen = True
                for ch in buf:
                    if ch == ":" and not password_seen:
                        password_seen = True
                        continue
                    enc = _encode(ch, _USERINFO)
                    if password_seen:
                        url.password += enc
                    else:
                        url.username += enc
                buf = ""
            elif c in (_EOF, "/", "?", "#") or (special and c == "\\"):
                if at_seen and buf == "":
                    return None
                p -= len(buf) + 1
                buf = ""
                state = "host"
            else:
                buf += c

        elif state == "host":
            if c == ":" and not in_brackets:
                if buf == "":
                    return None
                host = _host(buf, not special)
                if host is None:
                    return None
                url.host, buf = host, ""
                state = "port"
            elif c in (_EOF, "/", "?", "#") or (special and c == "\\"):
                p -= 1
                if special and buf == "":
                    return None
                host = _host(buf, not special)
                if host is None:
                    return None
                url.host, buf = host, ""
                state = "path start"
            else:
                if c == "[":
                    in_brackets = True
                elif c == "]":
                    in_brackets = False
                buf += c

        elif state == "port":
            if c is not _EOF and c in _ASCII_DIGIT:
                buf += c
            elif c in (_EOF, "/", "?", "#") or (special and c == "\\"):
                if buf:
                    port = int(buf)
                    if port > 65535:
                        return None
                    url.port = None if SPECIAL.get(url.scheme, -1) == port else port
                    buf = ""
                state = "path start"
                p -= 1
            else:
                return None

        elif state == "file":
            url.scheme = "file"
            url.host = ""
            special = True
            if c in ("/", "\\"):
                state = "file slash"
            elif base is not None and base.scheme == "file":
                url.host, url.path, url.query = base.host, list(base.path), base.query
                if c == "?":
                    url.query = ""
                    state = "query"
                elif c == "#":
                    url.fragment = ""
                    state = "fragment"
                elif c is not _EOF:
                    url.query = None
                    if not _starts_with_drive(s[p:]):
                        _shorten(url)
                    else:
                        url.path = []
                    state = "path"
                    p -= 1
            else:
                state = "path"
                p -= 1

        elif state == "file slash":
            if c in ("/", "\\"):
                state = "file host"
            else:
                if base is not None and base.scheme == "file":
                    url.host = base.host
                    if (not _starts_with_drive(s[p:]) and base.path
                            and _is_normalized_drive(base.path[0])):
                        url.path.append(base.path[0])
                state = "path"
                p -= 1

        elif state == "file host":
            if c in (_EOF, "/", "\\", "?", "#"):
                p -= 1
                if _is_drive(buf):
                    state = "path"   # buf carries into the path state
                elif buf == "":
                    url.host = ""
                    state = "path start"
                else:
                    host = _host(buf, False)
                    if host is None:
                        return None
                    url.host = "" if host == "localhost" else host
                    buf = ""
                    state = "path start"
            else:
                buf += c

        elif state == "path start":
            if special:
                state = "path"
                if c not in ("/", "\\"):
                    p -= 1
            elif c == "?":
                url.query = ""
                state = "query"
            elif c == "#":
                url.fragment = ""
                state = "fragment"
            elif c is not _EOF:
                state = "path"
                if c != "/":
                    p -= 1

        elif state == "path":
            slash = c == "/" or (special and c == "\\")
            if c is _EOF or slash or c in ("?", "#"):
                if _double_dot(buf):
                    _shorten(url)
                    if not slash:
                        url.path.append("")
                elif _single_dot(buf) and not slash:
                    url.path.append("")
                elif not _single_dot(buf):
                    if url.scheme == "file" and not url.path and _is_drive(buf):
                        buf = buf[0] + ":"
                    url.path.append(buf)
                buf = ""
                if c == "?":
                    url.query = ""
                    state = "query"
                elif c == "#":
                    url.fragment = ""
                    state = "fragment"
            else:
                j = _until(s, p, _STOP_SPECIAL_PATH if special else _STOP_PATH)
                buf += _encode(s[p:j], _PATH)
                p = j - 1

        elif state == "opaque path":
            if c == "?":
                url.query = ""
                state = "query"
            elif c == "#":
                url.fragment = ""
                state = "fragment"
            elif c is not _EOF:
                j = _until(s, p, _STOP_OPAQUE)
                url.path += _encode(s[p:j], _C0)
                p = j - 1

        elif state == "query":
            if c == "#" or c is _EOF:
                url.query += _encode(buf, _SPECIAL_QUERY if special else _QUERY)
                buf = ""
                if c == "#":
                    url.fragment = ""
                    state = "fragment"
            else:
                j = s.find("#", p)
                j = n if j < 0 else j
                buf += s[p:j]
                p = j - 1

        elif state == "fragment":
            if c is not _EOF:
                url.fragment += _encode(s[p:], _FRAGMENT)
                p = n - 1

        # "If after a run pointer points to the EOF code point, go to the
        # next step": a state that stepped back off EOF runs again.
        if p >= n:
            return url
        p += 1
