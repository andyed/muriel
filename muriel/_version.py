"""Single source of truth for muriel's version.

Three copies of the version literal had drifted apart — ``pyproject.toml`` said
0.14.0, ``muriel/__init__.py`` said 0.7.1, and ``provenance.py`` said 0.6.0 —
and the last of those was the one being written into every stamped artifact.
Eight minor releases of drift were baked into research sidecars and PNG tEXt
chunks before anyone noticed, because a hardcoded constant is uniformly wrong
and therefore invisible.

Resolution order:

1. Installed package metadata. This is the normal case once muriel is installed
   (``pip install -e .``), and it is authoritative — it reflects the artifact
   actually on ``sys.path``, not whatever a checkout happens to say.
2. ``pyproject.toml`` next to the package, for a bare source checkout. Parsed
   with a regex rather than ``tomllib`` because the package supports Python 3.9
   and ``tomllib`` landed in 3.11.
3. ``"0+unknown"``. A sentinel that is obviously not a release, so a stamp
   carrying it reads as "provenance unavailable" rather than as a real version.

Nothing here hardcodes a release number. If you find yourself adding one, that
is the bug this module exists to prevent.
"""

from __future__ import annotations

import re
from pathlib import Path

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
_UNKNOWN = "0+unknown"

# `version = "1.2.3"` at the start of a line, tolerant of the aligned-equals
# style used in this repo's pyproject.
_VERSION_RE = re.compile(r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']')


def _from_metadata() -> str | None:
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - Python < 3.8
        return None
    try:
        return version("muriel")
    except PackageNotFoundError:
        return None
    except Exception:  # pragma: no cover - defensive; metadata must never raise here
        return None


def _from_pyproject() -> str | None:
    try:
        text = _PYPROJECT.read_text(encoding="utf-8")
    except OSError:
        return None
    m = _VERSION_RE.search(text)
    return m.group(1) if m else None


def get_version() -> str:
    """Return muriel's version, resolved at call time."""
    return _from_metadata() or _from_pyproject() or _UNKNOWN


__version__ = get_version()
