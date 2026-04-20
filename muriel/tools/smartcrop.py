"""
muriel.tools.smartcrop — saliency-aware crop window solver.

Given an input image and a target aspect ratio, find the crop window that
maximises visual energy (edges + saturation) without clipping hard-avoid
regions (faces, text — optional, via extras).

This is muriel's saliency-aware placement primitive. First consumer: the
raster channel (OG cards, store banners, hero crops). Downstream: the
compositor, where the score map tells the layout engine "put this badge
in the lowest-energy quadrant that doesn't overlap a face."

v0.1 — edges-only
-----------------

No extras required. Sobel-edge magnitude × HSV saturation on an integral
image, candidate grid search, edge-bleed penalty. Pillow + numpy (numpy
imported lazily inside the function body, per muriel convention).

The ``faces``, ``text``, and ``saliency`` backends hook in via
``hard_avoid_bboxes`` and ``saliency_map`` parameters. v0.1 leaves them
empty; ``muriel.detectors`` populates them in v0.2 if the relevant extras
are installed.

Prior art
---------

- smartcrop.js (Jonas Wagner) — the energy scorer and integral-image
  candidate search trace back to this. https://github.com/jwagner/smartcrop.js
- smartcrop.py — older Python port; this implementation is independent.

Usage (programmatic)
--------------------

::

    from muriel.tools.smartcrop import crop_for

    result = crop_for(
        "input.jpg",
        ratio="16:9",          # or "og.card", or 1.91, or (16, 9)
        scales=(1.0, 0.9, 0.8, 0.7),
        debug_dir=None,
    )
    result.bbox               # → (left, top, right, bottom)
    result.score              # → float
    result.crop("out.jpg")    # writes the crop

Usage (CLI)
-----------

::

    muriel smartcrop in.jpg out.jpg --ratio 16:9
    muriel smartcrop in.jpg out.jpg --ratio 1:1 --ratio 16:9 --debug debug/
    muriel smartcrop in.jpg out.jpg --ratio og.card --faces on  # v0.2

Output
------

For a single ratio, ``out.jpg`` is the cropped image. For multiple
``--ratio`` flags, ``out.jpg`` becomes a template — each ratio writes
``out__<ratio-label>.jpg`` alongside a JSON sidecar with the chosen
bbox and score breakdown.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union

__all__ = ["crop_for", "parse_ratio", "CropResult"]


# ─── Types ───────────────────────────────────────────────────────────

Bbox = Tuple[int, int, int, int]   # (left, top, right, bottom)
RatioLike = Union[str, float, Tuple[int, int]]


@dataclass
class CropResult:
    """Outcome of a single-ratio crop solve."""

    bbox: Bbox
    score: float
    target_ratio: float
    score_components: dict = field(default_factory=dict)
    hard_avoid_boxes: List[Bbox] = field(default_factory=list)
    image_size: Tuple[int, int] = (0, 0)  # (W, H) of the source

    def crop(self, output_path: Union[str, Path], *, source=None) -> str:
        """Apply the bbox to ``source`` (or the path it came from) and save."""
        from PIL import Image

        if source is None:
            raise ValueError("CropResult.crop() needs source= image or path")
        img = source if hasattr(source, "crop") else Image.open(source)
        crop = img.crop(self.bbox)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        crop.save(str(out), optimize=True)
        return str(out)


# ─── Ratio parsing ───────────────────────────────────────────────────

def parse_ratio(ratio: RatioLike) -> Tuple[float, str]:
    """
    Resolve a user-facing ratio into (aspect, label).

    Accepts:
      * ``"16:9"`` — colon-separated int pair
      * ``"og.card"`` — ``muriel.dimensions`` registry lookup
      * ``1.91`` — direct width/height ratio
      * ``(1200, 630)`` / ``Size(1200, 630)`` — pair

    Returns the aspect as ``width / height`` plus a short slug
    (``"16x9"``, ``"og-card"``, ``"1.91"``) suitable for filenames.
    """
    if isinstance(ratio, (tuple, list)) and len(ratio) == 2:
        w, h = ratio
        return float(w) / float(h), f"{int(w)}x{int(h)}"

    if isinstance(ratio, (int, float)):
        return float(ratio), f"{float(ratio):.2f}".rstrip("0").rstrip(".")

    if isinstance(ratio, str):
        s = ratio.strip()
        if ":" in s:
            a, b = s.split(":", 1)
            return float(a) / float(b), f"{a}x{b}"
        if "." in s and all(c.isdigit() or c == "." for c in s):
            return float(s), s
        # treat as registry lookup
        try:
            from muriel.dimensions import lookup
            size = lookup(s)
            return size.aspect_ratio, s.replace(".", "-")
        except Exception as exc:
            raise ValueError(
                f"Cannot parse ratio {ratio!r}. Use '16:9', 'og.card', "
                f"1.91, or (w, h). (lookup error: {exc})"
            ) from exc

    raise TypeError(f"Unsupported ratio type: {type(ratio)!r}")


# ─── Scoring ─────────────────────────────────────────────────────────

_WEIGHTS = {
    "edges":       1.00,  # gradient magnitude
    "saturation":  0.70,  # HSV S channel
    "lightness":   0.25,  # |L - 0.5|  (favour mid-tones — text, skin, fabric)
    "bleed":      -0.60,  # subtract: energy clinging to the crop border
}


def _compute_energy(rgb):
    """Return a (H, W) float32 array of per-pixel energy."""
    import numpy as np

    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # Sobel magnitude via separable diff-of-neighbours (cheap, no scipy).
    gray = (0.299 * r + 0.587 * g + 0.114 * b).astype(np.float32)
    gx = np.abs(np.gradient(gray, axis=1))
    gy = np.abs(np.gradient(gray, axis=0))
    edges = gx + gy
    edges /= max(float(edges.max()), 1.0)

    # HSV saturation & lightness from RGB without PIL.Image.convert("HSV")
    # so we keep float precision.
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    lightness = (maxc + minc) * 0.5
    # Saturation: HSL formula, avoids div-by-zero on achromatic pixels.
    denom = 1.0 - np.abs(2 * lightness - 1.0)
    sat = np.where(denom > 1e-4, (maxc - minc) / np.maximum(denom, 1e-4), 0.0)
    mid_tone = 1.0 - np.abs(lightness - 0.5) * 2.0  # 1 at L=0.5, 0 at extremes

    energy = (
        _WEIGHTS["edges"] * edges
        + _WEIGHTS["saturation"] * sat
        + _WEIGHTS["lightness"] * mid_tone
    )
    # Clip negatives so integral image sums stay well-behaved.
    return np.clip(energy, 0.0, None).astype(np.float32)


def _integral(arr):
    import numpy as np
    # Pad with a zero row/col so bbox sums are one lookup per corner.
    ii = np.zeros((arr.shape[0] + 1, arr.shape[1] + 1), dtype=np.float64)
    ii[1:, 1:] = arr.cumsum(axis=0).cumsum(axis=1)
    return ii


def _box_sum(ii, left, top, right, bottom):
    # inclusive-exclusive: (left, top) inclusive, (right, bottom) exclusive
    return ii[bottom, right] - ii[top, right] - ii[bottom, left] + ii[top, left]


# ─── Candidate generation ───────────────────────────────────────────

def _candidates(
    W: int,
    H: int,
    target_aspect: float,
    scales: Sequence[float],
    step_frac: float = 1.0 / 32.0,
) -> Iterable[Bbox]:
    """Yield axis-aligned crop bboxes at the requested aspect ratio."""
    # Largest box of the target aspect that fits.
    if W / H >= target_aspect:
        base_h = H
        base_w = int(round(H * target_aspect))
    else:
        base_w = W
        base_h = int(round(W / target_aspect))

    step = max(4, int(min(W, H) * step_frac))

    for scale in scales:
        cw = int(round(base_w * scale))
        ch = int(round(base_h * scale))
        if cw < 16 or ch < 16:
            continue
        if cw > W or ch > H:
            continue
        for top in range(0, H - ch + 1, step):
            for left in range(0, W - cw + 1, step):
                yield (left, top, left + cw, top + ch)


# ─── Hard-avoid penalty ─────────────────────────────────────────────

def _clips_box(crop: Bbox, avoid: Bbox) -> bool:
    """True if ``crop`` partially clips ``avoid`` (overlaps but doesn't contain)."""
    cl, ct, cr, cb = crop
    al, at, ar, ab = avoid
    # No overlap → no clip (fine, avoid region just isn't in the crop).
    if ar <= cl or al >= cr or ab <= ct or at >= cb:
        return False
    # Fully inside → no clip.
    if cl <= al and ct <= at and cr >= ar and cb >= ab:
        return False
    return True


# ─── Main solver ────────────────────────────────────────────────────

def crop_for(
    image,
    ratio: RatioLike,
    *,
    scales: Sequence[float] = (1.0, 0.9, 0.82, 0.72),
    hard_avoid_bboxes: Sequence[Bbox] = (),
    saliency_map=None,       # v0.2 hook — not used in v0.1
    scale_penalty: float = 0.7,
    debug_dir: Optional[Union[str, Path]] = None,
) -> CropResult:
    """
    Find the best crop of ``image`` at the requested aspect ratio.

    Parameters
    ----------
    image : path, Path, or PIL.Image.Image
        The source.
    ratio : RatioLike
        See ``parse_ratio``.
    scales : sequence of float
        Crop sizes to try, as a fraction of the largest-fitting box.
        Smaller scales are penalised via ``scale_penalty`` so bigger
        crops win ties.
    hard_avoid_bboxes : sequence of Bbox
        Regions that must not be partially clipped. Any crop that slices
        one of these receives a prohibitive penalty (effectively
        excluded). v0.1 leaves this empty; detectors populate it in v0.2.
    saliency_map : optional array
        (v0.2) If provided, replaces the edge-energy map.
    scale_penalty : float
        Penalty exponent on scale — final score = raw_score × scale^penalty.
    debug_dir : path or None
        If set, write ``energy_heatmap.png`` and ``candidates.json`` for
        inspection.
    """
    from PIL import Image
    import numpy as np

    if hasattr(image, "convert"):
        img = image.convert("RGB")
        source_path = None
    else:
        source_path = Path(image)
        img = Image.open(source_path).convert("RGB")

    W, H = img.size
    target_aspect, _label = parse_ratio(ratio)

    # Downsample for the energy map — the scorer is a judgment call, not a
    # precise measurement. 320px on the short edge is enough.
    SCORE_SHORT_EDGE = 320
    if min(W, H) > SCORE_SHORT_EDGE:
        s = SCORE_SHORT_EDGE / min(W, H)
        sw, sh = int(round(W * s)), int(round(H * s))
        small = img.resize((sw, sh), Image.LANCZOS)
    else:
        s = 1.0
        sw, sh = W, H
        small = img

    rgb = np.asarray(small, dtype=np.float32) / 255.0
    energy = _compute_energy(rgb) if saliency_map is None else saliency_map
    ii = _integral(energy)

    # Edge-bleed: a thin shell along the crop's interior perimeter.
    BLEED_FRAC = 0.04

    # Scale hard-avoid bboxes into score-space.
    avoid_small = [
        (int(l * s), int(t * s), int(r * s), int(b * s))
        for (l, t, r, b) in hard_avoid_bboxes
    ]

    best = None
    best_components = None
    candidate_log: list[dict] = []

    for (cl, ct, cr, cb) in _candidates(W, H, target_aspect, scales):
        # Project candidate into score-space.
        sl = max(0, int(round(cl * s)))
        st = max(0, int(round(ct * s)))
        sr = min(sw, int(round(cr * s)))
        sb = min(sh, int(round(cb * s)))
        if sr - sl < 2 or sb - st < 2:
            continue

        full = _box_sum(ii, sl, st, sr, sb)
        area = (sr - sl) * (sb - st)
        if area <= 0:
            continue
        raw_energy = full / area

        # Edge-bleed: inner shell
        mw = max(1, int(round((sr - sl) * BLEED_FRAC)))
        mh = max(1, int(round((sb - st) * BLEED_FRAC)))
        inner_l = min(sr, sl + mw)
        inner_t = min(sb, st + mh)
        inner_r = max(sl, sr - mw)
        inner_b = max(st, sb - mh)
        if inner_r > inner_l and inner_b > inner_t:
            inner_sum = _box_sum(ii, inner_l, inner_t, inner_r, inner_b)
            shell_sum = full - inner_sum
            shell_area = area - (inner_r - inner_l) * (inner_b - inner_t)
            bleed = shell_sum / max(shell_area, 1)
        else:
            bleed = raw_energy

        # Scale bias: prefer bigger crops.
        cw_frac = (cr - cl) / max(W, H)
        ch_frac = (cb - ct) / max(W, H)
        scale_frac = max(cw_frac, ch_frac)

        score = (raw_energy + _WEIGHTS["bleed"] * bleed) * (scale_frac ** scale_penalty)

        # Hard-avoid: any partial clip vetoes the candidate outright.
        vetoed = any(_clips_box((cl, ct, cr, cb), a) for a in hard_avoid_bboxes)
        if vetoed:
            score = -1e9

        if debug_dir is not None:
            candidate_log.append({
                "bbox": [cl, ct, cr, cb],
                "score": float(score),
                "energy": float(raw_energy),
                "bleed": float(bleed),
                "scale_frac": float(scale_frac),
                "vetoed": bool(vetoed),
            })

        if best is None or score > best[1]:
            best = ((cl, ct, cr, cb), score)
            best_components = {
                "energy": float(raw_energy),
                "bleed": float(bleed),
                "scale_frac": float(scale_frac),
            }

    if best is None:
        # Degenerate: image is smaller than any candidate of this aspect.
        raise ValueError(
            f"No candidate crop of aspect {target_aspect:.3f} fits in "
            f"image of size {W}x{H}. Try --allow-upscale (not implemented)."
        )

    bbox, score = best

    if debug_dir is not None:
        _write_debug(debug_dir, small, energy, bbox, s, candidate_log, hard_avoid_bboxes)

    return CropResult(
        bbox=bbox,
        score=float(score),
        target_ratio=target_aspect,
        score_components=best_components or {},
        hard_avoid_boxes=list(hard_avoid_bboxes),
        image_size=(W, H),
    )


# ─── Debug output ───────────────────────────────────────────────────

def _write_debug(debug_dir, small_img, energy, chosen_bbox, scale, candidate_log, avoid_boxes):
    import numpy as np
    from PIL import Image, ImageDraw

    d = Path(debug_dir)
    d.mkdir(parents=True, exist_ok=True)

    # Heatmap: energy normalised to 0-255, magma-ish (pure-numpy — no matplotlib dep)
    e = energy / max(float(energy.max()), 1e-6)
    r = np.clip(1.5 * e - 0.3, 0, 1)
    g = np.clip(1.2 * e - 0.1, 0, 1)
    b = np.clip(0.8 - 0.5 * e, 0, 1)
    heat = np.dstack([r, g, b])
    heat_img = Image.fromarray((heat * 255).astype("uint8"), "RGB")
    # Overlay chosen crop on small-space coords.
    overlay = Image.blend(
        small_img.convert("RGB"),
        heat_img.resize(small_img.size, Image.LANCZOS),
        0.55,
    )
    draw = ImageDraw.Draw(overlay)
    sl, st, sr, sb = [int(round(v * scale)) for v in chosen_bbox]
    draw.rectangle([sl, st, sr - 1, sb - 1], outline=(255, 149, 149), width=3)
    for (al, at, ar, ab) in avoid_boxes:
        draw.rectangle(
            [int(al * scale), int(at * scale), int(ar * scale), int(ab * scale)],
            outline=(255, 255, 0), width=2,
        )
    overlay.save(d / "energy_heatmap.png", optimize=True)

    (d / "candidates.json").write_text(
        json.dumps({"chosen": list(chosen_bbox), "candidates": candidate_log[:1000]},
                   indent=2)
    )


# ─── CLI ────────────────────────────────────────────────────────────

def _slug_for_ratio(label: str) -> str:
    return label.replace(":", "x").replace(".", "-").replace("/", "-")


def _main(argv=None) -> int:
    import argparse
    from PIL import Image

    ap = argparse.ArgumentParser(
        prog="muriel smartcrop",
        description="Saliency-aware crop solver (v0.1: edges-only).",
    )
    ap.add_argument("input")
    ap.add_argument("output",
                    help="Output path. With multiple --ratio flags this becomes a template "
                         "(suffix __<ratio> inserted before extension).")
    ap.add_argument("--ratio", action="append", default=None,
                    help="Target aspect: '16:9', 'og.card', 1.91, or WxH. Repeatable.")
    ap.add_argument("--scales", default="1.0,0.9,0.82,0.72",
                    help="Comma-separated scale fractions to try.")
    ap.add_argument("--faces", choices=["on", "off"], default="off",
                    help="Avoid clipping detected faces. Requires muriel[faces].")
    ap.add_argument("--text", choices=["on", "off"], default="off",
                    help="Avoid clipping detected text. Requires muriel[text].")
    ap.add_argument("--saliency", choices=["edges", "deepgaze"], default="edges",
                    help="Saliency backend. 'deepgaze' requires muriel[saliency].")
    ap.add_argument("--debug", default=None,
                    help="Write energy heatmap + candidates.json to this directory.")
    ap.add_argument("--json-sidecar", action="store_true",
                    help="Write <output>.smartcrop.json alongside each crop.")
    args = ap.parse_args(argv)

    if not args.ratio:
        args.ratio = ["1:1"]

    scales = tuple(float(x) for x in args.scales.split(",") if x.strip())

    # Dispatch detectors lazily — surface friendly missing-extra errors here.
    hard_avoid: list[Bbox] = []
    saliency_map = None

    src_img = Image.open(args.input).convert("RGB")

    from muriel.detectors import ExtraNotInstalled
    try:
        if args.faces == "on":
            from muriel.detectors import faces as _faces
            hard_avoid.extend(_faces.detect(src_img))
        if args.text == "on":
            from muriel.detectors import text as _text
            hard_avoid.extend(_text.detect(src_img))
        if args.saliency == "deepgaze":
            from muriel.detectors import saliency as _sal
            saliency_map = _sal.compute(src_img)
    except ExtraNotInstalled as exc:
        import sys
        print(f"muriel smartcrop: {exc}", file=sys.stderr)
        return 2

    out_path = Path(args.output)
    multi = len(args.ratio) > 1

    exit_code = 0
    for r in args.ratio:
        target_aspect, label = parse_ratio(r)
        result = crop_for(
            src_img, r,
            scales=scales,
            hard_avoid_bboxes=hard_avoid,
            saliency_map=saliency_map,
            debug_dir=args.debug,
        )

        if multi:
            slug = _slug_for_ratio(label)
            this_out = out_path.with_name(
                f"{out_path.stem}__{slug}{out_path.suffix}"
            )
        else:
            this_out = out_path

        result.crop(this_out, source=src_img)
        print(
            f"→ {this_out}  "
            f"bbox={result.bbox}  score={result.score:.3f}  "
            f"aspect={result.target_ratio:.3f}"
        )

        if args.json_sidecar:
            sidecar = this_out.with_suffix(this_out.suffix + ".smartcrop.json")
            sidecar.write_text(json.dumps({
                "source": str(args.input),
                "output": str(this_out),
                "bbox": list(result.bbox),
                "score": result.score,
                "target_ratio": result.target_ratio,
                "components": result.score_components,
                "image_size": list(result.image_size),
                "hard_avoid": [list(b) for b in result.hard_avoid_boxes],
            }, indent=2))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(_main())
