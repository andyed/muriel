"""
render_assets — deprecated alias for the muriel package.

The project formerly known as render was renamed to muriel in April 2026
(in tribute to Muriel Cooper, 1925–1994). This module exists so that
existing notebooks with `from render_assets import ...` keep working for
one release cycle. Update imports to `from muriel import ...` when
convenient.

Re-exports every public name from `muriel` and raises a DeprecationWarning
on first import. Submodules are re-exported too, so `from
render_assets.contrast import audit_svg` continues to work.
"""

import sys as _sys
import warnings as _warnings

from muriel import *  # noqa: F401,F403
from muriel import __all__, __version__  # noqa: F401

# Re-export submodules so `from render_assets.X import Y` keeps working.
from muriel import (  # noqa: F401
    capture,
    contrast,
    dimensions,
    matplotlibrc_dark,
    matplotlibrc_light,
    stats,
    styleguide,
)

_sys.modules[__name__ + ".capture"] = capture
_sys.modules[__name__ + ".contrast"] = contrast
_sys.modules[__name__ + ".dimensions"] = dimensions
_sys.modules[__name__ + ".matplotlibrc_dark"] = matplotlibrc_dark
_sys.modules[__name__ + ".matplotlibrc_light"] = matplotlibrc_light
_sys.modules[__name__ + ".stats"] = stats
_sys.modules[__name__ + ".styleguide"] = styleguide

_warnings.warn(
    "render_assets is deprecated; the package was renamed to muriel. "
    "Update imports to `from muriel import ...`. This shim will be "
    "removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)
