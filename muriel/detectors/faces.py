"""
muriel.detectors.faces — face bbox detection for smartcrop's hard-avoid list.

Backend: mediapipe FaceDetection (short-range + full-range).

Installed via ``pip install muriel[faces]``. Import is deferred until
``detect()`` is called, so importing this module is free.
"""

from __future__ import annotations

from typing import List, Tuple

from . import _require_extra

Bbox = Tuple[int, int, int, int]


def detect(image, *, min_confidence: float = 0.5, pad_frac: float = 0.08) -> List[Bbox]:
    """
    Return face bboxes as ``(left, top, right, bottom)`` in image pixels.

    Runs both the short-range (<2m) and full-range (>2m) MediaPipe models
    and unions the results. Boxes are padded by ``pad_frac`` of their
    size on each side so the smartcrop scorer keeps a margin around
    faces rather than cropping right at the hairline.
    """
    _require_extra("mediapipe", "faces", "Face detection")
    import mediapipe as mp
    import numpy as np

    from PIL import Image
    if not hasattr(image, "size"):
        image = Image.open(image)
    rgb = np.asarray(image.convert("RGB"))
    H, W = rgb.shape[:2]

    boxes: list[Bbox] = []
    for model_selection in (0, 1):  # 0 = short-range, 1 = full-range
        with mp.solutions.face_detection.FaceDetection(
            model_selection=model_selection,
            min_detection_confidence=min_confidence,
        ) as det:
            res = det.process(rgb)
            if not res.detections:
                continue
            for d in res.detections:
                rel = d.location_data.relative_bounding_box
                l = max(0, int((rel.xmin - rel.width * pad_frac) * W))
                t = max(0, int((rel.ymin - rel.height * pad_frac) * H))
                r = min(W, int((rel.xmin + rel.width * (1 + pad_frac)) * W))
                b = min(H, int((rel.ymin + rel.height * (1 + pad_frac)) * H))
                if r > l and b > t:
                    boxes.append((l, t, r, b))

    # De-duplicate near-identical boxes (the two models often agree).
    return _dedupe(boxes, iou_threshold=0.5)


def _dedupe(boxes: List[Bbox], iou_threshold: float) -> List[Bbox]:
    kept: list[Bbox] = []
    for box in sorted(boxes, key=lambda b: -(b[2] - b[0]) * (b[3] - b[1])):
        if all(_iou(box, k) < iou_threshold for k in kept):
            kept.append(box)
    return kept


def _iou(a: Bbox, b: Bbox) -> float:
    il = max(a[0], b[0]); it = max(a[1], b[1])
    ir = min(a[2], b[2]); ib = min(a[3], b[3])
    if ir <= il or ib <= it:
        return 0.0
    inter = (ir - il) * (ib - it)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)
