"""
muriel.warmup — explicit model prefetch for installed extras.

Smartcrop's detectors lazy-download their weights on first call, which
is the worst time to discover your coffee-shop wifi is flaky. Run this
once after ``pip install muriel[...]`` to get every model in place up
front, with a progress indicator and a final summary of cache sizes.

Usage
-----

::

    muriel warmup                  # warm every installed extra
    muriel warmup --faces --text   # only these
    muriel warmup --saliency       # (v0.2 — placeholder for now)

Design
------

Each backend's warmup is a one-line touch that forces the underlying
library to fetch and cache its weights, using each library's native
mechanism:

  * mediapipe — models are bundled in the wheel; constructing the
    detector once is the "warmup". Nothing to download.
  * easyocr — ``easyocr.Reader([...])`` downloads detector + recognizer
    weights to ``~/.EasyOCR/`` on first call.
  * saliency — fetches the DeepGaze ONNX file into
    ``~/.cache/muriel/saliency/``. (v0.2)

Missing extras are skipped silently with a one-line note — this command
is meant to be idempotent and safe to run anytime.
"""

from __future__ import annotations

import sys
import time
from importlib import util as _ilu
from typing import Optional, Sequence

from muriel.detectors import EXTRAS


def _installed(module_name: str) -> bool:
    return _ilu.find_spec(module_name) is not None


def warmup_faces() -> tuple[bool, str]:
    """Construct a MediaPipe detector once so any model-side init runs."""
    if not _installed("mediapipe"):
        return False, "mediapipe not installed"
    import mediapipe as mp  # noqa: F401
    t0 = time.time()
    with mp.solutions.face_detection.FaceDetection(
        model_selection=0, min_detection_confidence=0.5,
    ):
        pass
    with mp.solutions.face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.5,
    ):
        pass
    return True, f"initialised (both models) in {time.time() - t0:.2f}s"


def warmup_text(languages=("en",)) -> tuple[bool, str]:
    """Force EasyOCR to download + cache detector/recognizer weights."""
    if not _installed("easyocr"):
        return False, "easyocr not installed"
    import easyocr
    t0 = time.time()
    # Constructing the Reader pulls weights into ~/.EasyOCR on first call.
    easyocr.Reader(list(languages), gpu=False, verbose=False)
    return True, f"downloaded / verified weights in {time.time() - t0:.2f}s"


def warmup_saliency() -> tuple[bool, str]:
    """Fetch the DeepGaze ONNX into the muriel cache. (v0.2)"""
    if not _installed("onnxruntime"):
        return False, "onnxruntime not installed"
    from muriel.detectors import saliency as _sal
    if _sal.is_warmed():
        return True, f"already cached at {_sal.cached_model_path()}"
    # v0.2 — real fetch here with a pinned URL + sha256.
    return False, (
        "saliency model fetch not yet implemented (v0.2). "
        "Detector stub will error until wired."
    )


_WARMERS = {
    "faces":    warmup_faces,
    "text":     warmup_text,
    "saliency": warmup_saliency,
}


def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="muriel warmup",
        description="Prefetch detector model weights for installed extras.",
    )
    for name in EXTRAS:
        ap.add_argument(f"--{name}", action="store_true",
                        help=f"Warm the {name} extra.")
    args = ap.parse_args(argv)

    # If no flags, warm everything that's installed.
    requested = [n for n in EXTRAS if getattr(args, n)]
    if not requested:
        requested = [n for n, info in EXTRAS.items() if _installed(info["module"])]
        if not requested:
            print("No extras installed. Nothing to warm up.")
            print("Install extras first, e.g.: pip install 'muriel[faces,text]'")
            return 0

    print(f"Warming up: {', '.join(requested)}")
    print()

    any_failed = False
    for name in requested:
        warmer = _WARMERS[name]
        print(f"  • {name} ... ", end="", flush=True)
        try:
            ok, msg = warmer()
        except Exception as exc:                    # noqa: BLE001
            ok, msg = False, f"error — {exc}"
        sys.stdout.write(f"{'ok' if ok else 'skipped'}: {msg}\n")
        if not ok:
            any_failed = True

    return 0 if not any_failed else 1


if __name__ == "__main__":
    raise SystemExit(_main())
