"""
muriel.detectors — optional hard-avoid and saliency backends.

Each submodule wraps one optional extra. Imports are lazy (inside the
function body), so touching ``from muriel.detectors import faces`` does
not drag mediapipe / easyocr / onnxruntime into memory until you actually
call ``faces.detect(...)``.

Extras
------

::

    pip install muriel[faces]      # mediapipe
    pip install muriel[text]       # easyocr
    pip install muriel[saliency]   # onnxruntime + model fetch

Missing extras raise ``ExtraNotInstalled`` with a one-line install hint
— no ImportError stack traces leaking to end users.
"""

from __future__ import annotations

from importlib import util as _ilu


class ExtraNotInstalled(RuntimeError):
    """Raised when a detector is invoked but its optional extra is absent."""


def _require_extra(module_name: str, extra_name: str, purpose: str) -> None:
    """
    Probe for ``module_name`` without importing it. Raise a friendly
    message if absent. The caller does the actual ``import`` afterwards.
    """
    if _ilu.find_spec(module_name) is None:
        raise ExtraNotInstalled(
            f"{purpose} requires the '{module_name}' package. "
            f"Install: pip install 'muriel[{extra_name}]'"
        )


# Extras manifest — kept here (not per-submodule) so ``muriel doctor``
# can introspect without importing the detector modules.
EXTRAS: dict[str, dict[str, str]] = {
    "faces":    {"module": "mediapipe",   "purpose": "Face detection"},
    "text":     {"module": "easyocr",     "purpose": "Text / OCR detection"},
    "saliency": {"module": "onnxruntime", "purpose": "Saliency model (DeepGaze IIE)"},
}


__all__ = ["ExtraNotInstalled", "_require_extra", "EXTRAS"]
