"""
muriel.detectors.saliency — saliency map for smartcrop's energy scorer.

Backend: DeepGaze IIE (or equivalent) via onnxruntime. The model file is
fetched explicitly by ``muriel warmup --saliency`` — no silent downloads
at render time.

v0.1 status
-----------

This module is a stub: it raises ``ExtraNotInstalled`` unless both
``onnxruntime`` and a cached model file are present. The model wiring
is left for v0.2.

Installed via ``pip install muriel[saliency]``.
"""

from __future__ import annotations

from pathlib import Path

from . import _require_extra


CACHE_DIR = Path.home() / ".cache" / "muriel" / "saliency"
MODEL_FILENAME = "deepgaze_iie.onnx"  # placeholder — v0.2 will pin a real URL


def cached_model_path() -> Path:
    return CACHE_DIR / MODEL_FILENAME


def is_warmed() -> bool:
    return cached_model_path().exists()


def compute(image):
    """
    Return a (H, W) float32 saliency map aligned to ``image`` pixels.

    Raises ``ExtraNotInstalled`` if onnxruntime is not installed or if
    the model weights have not been fetched via ``muriel warmup``.
    """
    _require_extra("onnxruntime", "saliency", "Saliency model")
    if not is_warmed():
        from . import ExtraNotInstalled
        raise ExtraNotInstalled(
            f"Saliency model not cached at {cached_model_path()}. "
            f"Fetch: muriel warmup --saliency"
        )
    # v0.2 — wire DeepGaze IIE ONNX inference here.
    raise NotImplementedError(
        "Saliency backend not yet wired. "
        "Edges-only scorer is the v0.1 default; use --saliency edges."
    )
