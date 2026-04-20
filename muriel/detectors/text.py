"""
muriel.detectors.text — text bbox detection for smartcrop's hard-avoid list.

Backend: EasyOCR (CRAFT detector + CRNN recogniser — we use detection only).

Installed via ``pip install muriel[text]``. Import is deferred until
``detect()`` is called.
"""

from __future__ import annotations

from typing import List, Tuple

from . import _require_extra

Bbox = Tuple[int, int, int, int]

_READER = None  # cached — EasyOCR's Reader is expensive to construct.


def detect(image, *, languages=("en",), pad_px: int = 4) -> List[Bbox]:
    """
    Return text bboxes as ``(left, top, right, bottom)`` in image pixels.

    EasyOCR returns polygon boxes; we collapse each to its axis-aligned
    bbox with a small ``pad_px`` margin so tight-cropping a letter still
    counts as a clip.
    """
    _require_extra("easyocr", "text", "Text detection")
    import easyocr
    import numpy as np
    from PIL import Image

    global _READER
    if _READER is None:
        _READER = easyocr.Reader(list(languages), gpu=False, verbose=False)

    if not hasattr(image, "size"):
        image = Image.open(image)
    arr = np.asarray(image.convert("RGB"))
    H, W = arr.shape[:2]

    # EasyOCR returns (horizontal_rects, free_polys), each wrapped in a
    # batch list. Horizontal rects are [xmin, xmax, ymin, ymax]; free polys
    # are lists of 4 (x, y) points (rotated / non-axis-aligned text).
    horizontal_batches, free_batches = _READER.detect(arr, text_threshold=0.7)
    horizontal = horizontal_batches[0] if horizontal_batches else []
    free = free_batches[0] if free_batches else []

    boxes: list[Bbox] = []

    for rect in horizontal:
        xmin, xmax, ymin, ymax = (int(v) for v in rect)
        l = max(0, xmin - pad_px)
        t = max(0, ymin - pad_px)
        r = min(W, xmax + pad_px)
        b = min(H, ymax + pad_px)
        if r > l and b > t:
            boxes.append((l, t, r, b))

    for poly in free:
        xs = [int(p[0]) for p in poly]
        ys = [int(p[1]) for p in poly]
        l = max(0, min(xs) - pad_px)
        t = max(0, min(ys) - pad_px)
        r = min(W, max(xs) + pad_px)
        b = min(H, max(ys) + pad_px)
        if r > l and b > t:
            boxes.append((l, t, r, b))

    return boxes
