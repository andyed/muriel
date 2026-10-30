"""
muriel.loupe — the magnified-crop lens behind the Loupe jury seat.

Cuts a deterministic grid of overlapping cells out of one image and
writes each at 4× magnification, so a critic can judge local finish
(whether lines land, joints meet, edges resolve) without the whole
composition there to fill the gaps in for them.

Created because "it looked fine at 1×" is how local defects ship. At
viewing scale the visual system completes contours: a rule that stops
2 px short of an outline reads as touching it, a seam that misses its
corner reads as meeting it, two fills with a hairline of background
between them read as one shape. A reviewer who knows what the joint is
supposed to look like supplies the rest. Magnification takes that
completion away. The practice comes from the anatomy isometric-figure
skill (github.com/wheresryan22/anatomy, MIT), whose rejected figures
were mostly faults its owner found by zooming in on joints that had
passed at 1×.

Scale is fixed, not proportional
--------------------------------

``muriel.squint`` scales its blur to the long edge because hierarchy is
relative: a mass matters as a share of the frame. Local finish is not
relative. A 1 px gap is a 1 px gap on a 400 px sprite and on a 4000 px
poster, so the cell here is a fixed ``CELL_PX`` of *ship* pixels: the
pixels the artifact is seen at. Scaling the cell with the frame would
make a poster's loupe a 1× view, which is the failure the module
exists to prevent.

Why these numbers
-----------------

- ``ZOOM`` = 4. A 1 px feature becomes 4 px, enough to resolve a gap
  that is invisible at 1×, while a cell still holds the joint and its
  neighbours. That matches the 4× close-ups in anatomy's verification
  loop.
- ``CELL_PX`` = 256 ship px, so each tile is 1024 px on its long edge.
  Vision models downsample inputs past roughly 1.5k px on the long
  edge. A tile that a model shrinks back loses the magnification it was
  cut for, and 1024 stays under that limit with margin. Change ``ZOOM``
  and ``CELL_PX`` together, keeping ``TILE_EDGE_PX`` near 1024.
- ``OVERLAP_PX`` = 32. Neighbouring cells share a 32 px band, so any
  feature up to 32 px across that straddles a cell boundary falls
  wholly inside at least one cell. Without the overlap a defect on a
  seam is split across two tiles and is whole in neither.
- ``BUDGET`` = 16 tiles. Reading is the seat's cost, and it is paid per
  option. Cells are ranked by structure (below) and only the top
  ``BUDGET`` are written; the manifest still lists every cell, so the
  ballot can state its coverage instead of implying it was total.

Ranking: structure, not emptiness
---------------------------------

Each cell is scored by edge density: the share of its ship pixels whose
luminance edge response (Pillow ``FIND_EDGES``) is at least
``EDGE_LEVEL``. Joints, junctions, text and ticks score high; a field
of flat colour scores zero. Cells with fewer than ``EMPTY_EDGE_PX`` edge
pixels are marked ``empty`` and never written.

An empty cell is not a finding. anatomy treats a bare face as
unfinished work because its figures are dense by design. muriel does
not: whitespace is a decision, and the Loupe seat may not fire on it.
The ranking exists to spend the budget where there is something to
inspect, not to reward density.

Edge density is a proxy. It ranks dense text blocks high and a lone
short tick low. That is acceptable for a lens, because the lens finds
nothing itself. It decides where the seat looks, and the manifest
says where it did not.

Vector, raster, and source scale
--------------------------------

The magnified tile is only as honest as its resampling:

- **SVG input** is rasterized at ``ZOOM``× with ``cairosvg`` (muriel's
  ``[critique]`` extra). That is a true re-render, which is what a
  browser does when it zooms vector content. ``render: rerender``.
- **A raster already rendered at N×** (``muriel capture --scale 4``,
  or any ``@4x`` export) is passed with ``--source-scale N``. Cells are
  still laid out in ship pixels; at N = ``ZOOM`` the tile is a straight
  crop with no resampling. ``render: rerender``.
- **A 1× raster** is magnified nearest-neighbour, so the tile shows the
  pixels themselves and not an interpolator's guess between them, the
  same reason ``muriel.squint``'s ``px16_zoom`` is nearest-neighbour.
  Every diagonal then shows a stair-step. That is the lens, not a
  defect, and the manifest records ``render: nearest`` so the seat
  knows it. Prefer a re-render whenever the source exists.

What the seat is denied
-----------------------

No overview image is written: no contact sheet, grid map or
thumbnail. The Loupe seat is defined by never seeing the whole
composition, so a lens that shipped one would undo its own denial. Cell
coordinates are in the manifest because a ballot has to cite where a
defect is.

Transparency is composited onto an explicit matte (default muriel's
OLED near-black) and the matte is recorded, as in ``muriel.squint``. A
dark hairline on a transparent ground disappears on a dark matte, so
pass ``--matte`` with the background the artifact actually ships on.

Determinism
-----------

No RNG. Fixed filters (NEAREST up, LANCZOS down, BOX to score a
multi-scale source). Fixed cell geometry. Ties in rank break by row,
then column. Same input, matte and source scale give byte-identical
tiles and an identical manifest.

Usage
-----

.. code-block:: python

    from muriel.loupe import loupe, cell_origins
    cell_origins(1200, 256, 32)    # → [0, 224, 448, 672, 896, 944]
    result = loupe("render_assets/panel.png")
    result.read_cells()[0].path    # densest cell, at 4×

.. code-block:: bash

    python -m muriel.loupe panel.png
    python -m muriel.loupe panel@4x.png --source-scale 4
    python -m muriel.loupe figure.svg --matte '#ffffff' --json
    python -m muriel.loupe poster.png --budget 24 --out-dir /tmp/loupe

Exit status:
    0 = tiles written
    3 = usage error (file not found, unreadable, bad matte or scale)
    4 = Pillow missing (``[raster]``), or cairosvg missing for an SVG
        (``[critique]``)

Limitations
-----------

- A lens, not a detector. It finds nothing on its own. On SVG and HTML,
  ``muriel.line_ends`` measures stroke ends in the rendered page and its
  output is a finding of fact; the lens is for what that check cannot
  reach.
- Judges pixels, not markup. A defect that only exists in some state
  the raster did not capture (hover, an animation frame, a theme) is
  invisible here; capture that state and run the lens on it.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence, Union

__all__ = [
    "ZOOM",
    "CELL_PX",
    "TILE_EDGE_PX",
    "OVERLAP_PX",
    "BUDGET",
    "EDGE_LEVEL",
    "EMPTY_EDGE_PX",
    "DEFAULT_MATTE",
    "cell_origins",
    "cell_grid",
    "ship_size",
    "LoupeCell",
    "LoupeResult",
    "loupe",
]

# ─── Lens constants ──────────────────────────────────────────────────────

#: Magnification of every tile, in ship pixels.
ZOOM: int = 4

#: Cell edge in ship pixels. Fixed, never a fraction of the frame. See
#: "Scale is fixed, not proportional" in the module docstring.
CELL_PX: int = 256

#: Tile edge the seat actually reads. Kept under the size at which a
#: vision model downsamples its input, so the zoom survives the model.
TILE_EDGE_PX: int = CELL_PX * ZOOM

#: Band shared by neighbouring cells. A feature up to this wide that
#: straddles a boundary lands whole in at least one cell.
OVERLAP_PX: int = 32

#: Tiles written per run. The seat's reading cost, paid per option.
BUDGET: int = 16

#: Luminance edge response (0-255, Pillow FIND_EDGES) a pixel must reach
#: to count as structure.
EDGE_LEVEL: int = 32

#: Below this many edge pixels a cell has nothing to inspect.
EMPTY_EDGE_PX: int = 24

#: Matte for images with an alpha channel. muriel's OLED near-black,
#: shared with muriel.squint.
DEFAULT_MATTE: str = "#0a0a0f"


# ─── Pure geometry (no Pillow) ───────────────────────────────────────────

def cell_origins(length: int, cell: int = CELL_PX, overlap: int = OVERLAP_PX) -> list[int]:
    """
    Start offsets of the cells along one axis of ``length`` pixels.

    Cells step by ``cell - overlap``. The last cell is pulled back flush
    with the far edge instead of hanging past it, so no tile is partial
    and the far margin gets the same magnification as the rest. An axis
    no longer than one cell gets a single cell at 0.

    Raises ``ValueError`` on a non-positive length or cell, or an overlap
    that leaves no forward step.
    """
    if length <= 0:
        raise ValueError(f"length must be positive, got {length!r}")
    if cell <= 0:
        raise ValueError(f"cell must be positive, got {cell!r}")
    if not 0 <= overlap < cell:
        raise ValueError(f"overlap must be in [0, cell), got {overlap!r} for cell {cell}")
    if length <= cell:
        return [0]
    stride = cell - overlap
    origins = list(range(0, length - cell, stride))
    # The flush cell can land within one stride of the previous origin;
    # it is kept anyway, because dropping it leaves the far edge uncut.
    if origins[-1] != length - cell:
        origins.append(length - cell)
    return origins


def cell_grid(
    width: int,
    height: int,
    cell: int = CELL_PX,
    overlap: int = OVERLAP_PX,
) -> list[tuple[int, int, int, int, int, int]]:
    """
    Every cell as ``(row, col, x, y, w, h)`` in ship pixels, row-major.

    ``w`` and ``h`` are ``min(cell, dimension)``, so an image smaller
    than a cell is one cell covering all of it.
    """
    xs = cell_origins(width, cell, overlap)
    ys = cell_origins(height, cell, overlap)
    w = min(cell, width)
    h = min(cell, height)
    return [
        (row, col, x, y, w, h)
        for row, y in enumerate(ys)
        for col, x in enumerate(xs)
    ]


def ship_size(width: int, height: int, source_scale: int) -> tuple[int, int]:
    """
    Ship-pixel size of a raster rendered at ``source_scale``×.

    Half-up rounding (``int(x + 0.5)``), the same on every platform.
    """
    if source_scale <= 0:
        raise ValueError(f"source_scale must be positive, got {source_scale!r}")
    if width <= 0 or height <= 0:
        raise ValueError(f"dimensions must be positive, got {width}×{height}")
    return (
        max(1, int(width / source_scale + 0.5)),
        max(1, int(height / source_scale + 0.5)),
    )


def _cell_id(row: int, col: int) -> str:
    """1-based, so a ballot reads ``r1c1`` for the top-left cell."""
    return f"r{row + 1}c{col + 1}"


def _render_label(source_scale: int, zoom: int) -> str:
    if source_scale >= zoom:
        return "rerender"
    return "nearest"


# ─── Result ──────────────────────────────────────────────────────────────

@dataclass
class LoupeCell:
    """One cell of the grid. Geometry is in ship pixels."""
    row: int
    col: int
    x: int
    y: int
    w: int
    h: int
    edge_px: int
    score: float
    status: str  # "read" | "unread" | "empty"
    rank: Optional[int] = None
    path: Optional[Path] = None

    @property
    def id(self) -> str:
        return _cell_id(self.row, self.col)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "row": self.row + 1,
            "col": self.col + 1,
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "edge_px": self.edge_px,
            "score": self.score,
            "status": self.status,
            "rank": self.rank,
            "path": str(self.path) if self.path else None,
        }


@dataclass
class LoupeResult:
    """What one loupe run produced."""
    source: Path
    width: int          # ship pixels
    height: int         # ship pixels
    source_scale: int
    zoom: int
    render: str         # "rerender" | "nearest"
    matte: tuple[int, int, int]
    budget: int
    out_dir: Path
    cells: list[LoupeCell] = field(default_factory=list)

    @property
    def matte_hex(self) -> str:
        r, g, b = self.matte
        return f"#{r:02x}{g:02x}{b:02x}"

    def read_cells(self) -> list[LoupeCell]:
        """Written tiles, in reading order (rank 1 first)."""
        return sorted(
            (c for c in self.cells if c.status == "read"),
            key=lambda c: c.rank,
        )

    def coverage(self) -> dict:
        """Counts a ballot cites instead of implying full coverage."""
        counts = {"read": 0, "unread": 0, "empty": 0}
        for c in self.cells:
            counts[c.status] += 1
        return {"cells": len(self.cells), **counts}

    def to_dict(self) -> dict:
        """JSON-serializable manifest, what ``--json`` prints."""
        return {
            "source": str(self.source),
            "width": self.width,
            "height": self.height,
            "source_scale": self.source_scale,
            "zoom": self.zoom,
            "render": self.render,
            "matte": self.matte_hex,
            "cell_px": CELL_PX,
            "overlap_px": OVERLAP_PX,
            "tile_edge_px": CELL_PX * self.zoom,
            "budget": self.budget,
            "out_dir": str(self.out_dir),
            "coverage": self.coverage(),
            # Reading order first, then the cells that were not written,
            # so the manifest reads top-down the way the seat should.
            "cells": [c.to_dict() for c in self.read_cells()]
            + [c.to_dict() for c in self.cells if c.status != "read"],
        }


# ─── Lazy backends ───────────────────────────────────────────────────────

def _require_pillow():
    """
    Import Pillow on demand. Pillow ships in muriel's optional
    ``[raster]`` extra so a bare install stays dependency-free.
    """
    try:
        from PIL import Image, ImageFilter
    except ImportError as exc:
        raise ImportError(
            "muriel.loupe requires Pillow, which ships in muriel's optional "
            "raster extra. Install it with:  pip install 'muriel[raster]'  "
            "(or: pip install Pillow)"
        ) from exc
    return Image, ImageFilter


def _rasterize_svg(svg_path: Path, scale: int) -> bytes:
    """SVG → PNG bytes at ``scale``× via cairosvg (``[critique]`` extra)."""
    try:
        import cairosvg
    except ImportError as exc:
        raise ImportError(
            "muriel.loupe needs cairosvg to re-render an SVG at "
            f"{scale}×. It ships in muriel's optional critique extra: "
            "pip install 'muriel[critique]'. Or rasterize at "
            f"{scale}× yourself and pass --source-scale {scale}."
        ) from exc
    return cairosvg.svg2png(url=str(svg_path), scale=scale)


def _resolve_matte(value: Union[str, Sequence[int]]) -> tuple[int, int, int]:
    from muriel.contrast import parse_color

    rgb = parse_color(value)
    if rgb is None:
        raise ValueError(f"matte must be an opaque color, got {value!r}")
    return rgb


def _flatten(src, matte_rgb, Image):
    """
    Composite any transparency onto the matte. Palette images carry
    transparency in a tRNS chunk, not a band, so they are promoted to
    RGBA first. muriel.squint documents why that matters.
    """
    if src.mode in ("P", "PA") or "transparency" in src.info:
        src = src.convert("RGBA")
    if "A" in src.getbands():
        rgba = src.convert("RGBA")
        flat = Image.new("RGB", rgba.size, matte_rgb)
        flat.paste(rgba, (0, 0), rgba)
        return flat
    return src.convert("RGB")


# ─── The lens ────────────────────────────────────────────────────────────

def loupe(
    image_path: Union[str, Path],
    out_dir: Optional[Union[str, Path]] = None,
    *,
    source_scale: int = 1,
    matte: Union[str, Sequence[int]] = DEFAULT_MATTE,
    budget: int = BUDGET,
    zoom: int = ZOOM,
) -> LoupeResult:
    """
    Write the top ``budget`` magnified cells of one image.

    Parameters
    ----------
    image_path
        A raster Pillow opens, or an ``.svg`` (re-rendered at ``zoom``×
        through cairosvg; ``source_scale`` is then ignored).
    out_dir
        Where tiles land. Defaults to ``loupe/`` beside the input.
    source_scale
        The scale the raster was rendered at relative to ship size: 1
        for a normal export, 2 for a default ``muriel capture``, 4 for
        ``--scale 4``. Cells are laid out in ship pixels either way.
    matte
        Color composited under any alpha channel. Recorded.
    budget
        Tiles written, densest first. Every cell is still listed.
    zoom
        Magnification. Leave at ``ZOOM`` unless re-deriving the lens.

    Raises
    ------
    ImportError
        Pillow missing, or cairosvg missing for an SVG.
    FileNotFoundError
        Source missing.
    ValueError
        Bad matte, scale, budget or zoom.
    """
    Image, ImageFilter = _require_pillow()

    if budget < 0:
        raise ValueError(f"budget must be non-negative, got {budget!r}")
    if zoom <= 0:
        raise ValueError(f"zoom must be positive, got {zoom!r}")

    src_path = Path(image_path).expanduser().resolve()
    if not src_path.exists():
        raise FileNotFoundError(f"no such image: {src_path}")
    matte_rgb = _resolve_matte(matte)

    if src_path.suffix.lower() == ".svg":
        import io

        src = Image.open(io.BytesIO(_rasterize_svg(src_path, zoom)))
        source_scale = zoom
    else:
        src = Image.open(str(src_path))
    src = _flatten(src, matte_rgb, Image)

    width, height = ship_size(src.width, src.height, source_scale)
    render = _render_label(source_scale, zoom)

    # Score on a ship-scale copy so EMPTY_EDGE_PX means the same thing at
    # every source scale. BOX is the plain area average: no ringing to
    # invent edges the artifact does not have.
    luma = src.convert("L")
    if luma.size != (width, height):
        luma = luma.resize((width, height), Image.Resampling.BOX)
    edges = luma.filter(ImageFilter.FIND_EDGES).point(
        lambda v: 255 if v >= EDGE_LEVEL else 0
    )
    # Pillow's 3×3 filters copy the outermost ring of pixels through
    # unfiltered, so on a white or mid-grey ground the frame itself scores
    # as an edge and every border cell looks occupied. Zero that ring; a
    # one-pixel loss of true edges at the very border is the price.
    from PIL import ImageDraw

    ImageDraw.Draw(edges).rectangle(
        [0, 0, edges.width - 1, edges.height - 1], outline=0
    )

    target = (
        Path(out_dir).expanduser().resolve()
        if out_dir is not None
        else src_path.parent / "loupe"
    )

    cells: list[LoupeCell] = []
    for row, col, x, y, w, h in cell_grid(width, height):
        edge_px = edges.crop((x, y, x + w, y + h)).histogram()[255]
        cells.append(LoupeCell(
            row=row, col=col, x=x, y=y, w=w, h=h,
            edge_px=edge_px,
            score=round(edge_px / (w * h), 4),
            status="empty" if edge_px < EMPTY_EDGE_PX else "unread",
        ))

    ranked = sorted(
        (c for c in cells if c.status != "empty"),
        key=lambda c: (-c.edge_px, c.row, c.col),
    )
    if ranked and budget:
        target.mkdir(parents=True, exist_ok=True)
    for rank, cell in enumerate(ranked[:budget], start=1):
        box = (
            cell.x * source_scale,
            cell.y * source_scale,
            min(src.width, (cell.x + cell.w) * source_scale),
            min(src.height, (cell.y + cell.h) * source_scale),
        )
        tile = src.crop(box)
        size = (cell.w * zoom, cell.h * zoom)
        if tile.size != size:
            # Up: nearest, so the tile shows real pixels. Down (a source
            # rendered past the zoom): LANCZOS, the only honest reduction.
            method = (
                Image.Resampling.NEAREST
                if size[0] > tile.width
                else Image.Resampling.LANCZOS
            )
            tile = tile.resize(size, method)
        path = target / f"{src_path.stem}.loupe-{cell.id}.png"
        tile.save(str(path), "PNG", optimize=True)
        cell.status = "read"
        cell.rank = rank
        cell.path = path

    return LoupeResult(
        source=src_path,
        width=width,
        height=height,
        source_scale=source_scale,
        zoom=zoom,
        render=render,
        matte=matte_rgb,
        budget=budget,
        out_dir=target,
        cells=cells,
    )


# ─── Pretty printer ──────────────────────────────────────────────────────

def _print_result(result: LoupeResult) -> None:
    cov = result.coverage()
    print(f"\nLoupe: {result.source}")
    print(f"  ship size: {result.width} × {result.height} px "
          f"(source at {result.source_scale}×)")
    print(f"  lens:      {CELL_PX} px cells, {OVERLAP_PX} px overlap, "
          f"{result.zoom}× ({result.render}), tiles {CELL_PX * result.zoom} px")
    print(f"  matte:     {result.matte_hex}")
    print(f"  coverage:  {cov['read']} read · {cov['unread']} unread · "
          f"{cov['empty']} empty of {cov['cells']} cells")
    print()
    print(f"  {'Rank':<5} {'Cell':<8} {'At (ship px)':<16} {'Edge':<7} Path")
    print(f"  {'─' * 5} {'─' * 8} {'─' * 16} {'─' * 7} {'─' * 30}")
    for c in result.read_cells():
        print(f"  {c.rank:<5} {c.id:<8} {f'{c.x},{c.y}':<16} {c.score:<7.4f} {c.path}")
    print()


# ─── CLI ─────────────────────────────────────────────────────────────────

def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m muriel.loupe",
        description=(
            "Cut fixed-size overlapping cells from an image and write the "
            "densest at 4×, so local finish can be judged without the "
            "composition filling the gaps."
        ),
    )
    parser.add_argument("image", type=Path, help="Raster image, or an SVG to re-render.")
    parser.add_argument(
        "--out-dir", type=Path, default=None,
        help="Output directory (default: a loupe/ directory beside the input).",
    )
    parser.add_argument(
        "--source-scale", type=int, default=1,
        help="Scale the raster was rendered at (2 for a default muriel capture, "
             "4 for --scale 4). Default 1.",
    )
    parser.add_argument(
        "--matte", type=str, default=DEFAULT_MATTE,
        help=f"Color composited under any alpha channel (default: {DEFAULT_MATTE}).",
    )
    parser.add_argument(
        "--budget", type=int, default=BUDGET,
        help=f"Tiles to write, densest first (default: {BUDGET}).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Print the manifest as JSON instead of a table.",
    )
    args = parser.parse_args(argv)

    if not args.image.exists():
        print(f"error: file not found: {args.image}", file=sys.stderr)
        return 3

    try:
        result = loupe(
            args.image,
            args.out_dir,
            source_scale=args.source_scale,
            matte=args.matte,
            budget=args.budget,
        )
    except ImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        _print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
