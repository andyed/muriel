"""
muriel.tools.venn — area-proportional Venn / Euler diagrams, brand-aware.

Thin wrapper over `matplotlib_venn` that applies a muriel ``StyleGuide``
to the circle fills, labels, and annotations. Supports 2-set and 3-set
area-proportional diagrams (the library's native strength); for 4+ sets,
fall back to a different encoding — a Venn with four interlocking
circles is cosmetic, not informative.

Two shipped patterns:

- ``venn_single(sets, counts, *, brand, title, out_path)`` — one diagram.
- ``venn_panels(panels, *, brand, title, out_path)`` — two or more
  diagrams side by side, the AF "LAB vs WILD" layout, for condition
  comparisons.

Usage
-----

::

    from muriel.tools.venn import venn_single, venn_panels
    from muriel.styleguide import load_styleguide

    brand = load_styleguide("examples/muriel-brand.toml")

    # 3-set scope diagram: muriel / marginalia / iblipper
    venn_single(
        sets={"muriel": 38, "marginalia": 22, "iblipper": 14,
              "muriel_marginalia": 6, "muriel_iblipper": 5,
              "marginalia_iblipper": 2, "all": 3},
        brand=brand,
        title="Overlapping scope — muriel, marginalia, iblipper",
        out_path="docs/venn-scope.png",
    )

Subset keys follow the matplotlib_venn3 convention: three-letter binary
strings ``'100' .. '111'``. The helper accepts both the binary keys and
friendlier aliases (``'muriel'`` == ``'100'``, ``'all'`` == ``'111'``,
etc.) and normalizes internally.

Dependencies
------------

Requires ``matplotlib`` and ``matplotlib-venn``. Both are optional at
muriel's core level; install with ``pip install matplotlib matplotlib-venn``
before calling these helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

__all__ = ["venn_single", "venn_panels"]


# ─── Accessible SVG ──────────────────────────────────────────────────

def _fmt_count(v: float) -> str:
    v = float(v)
    return f"{int(v):,}" if v.is_integer() else f"{v:,g}"


def _regions_desc(subsets: Dict[str, float], labels: Sequence[str]) -> str:
    """"A only 38, A and B only 6, all three 3" — straight from the spec."""
    out = []
    for key in sorted(subsets, key=lambda k: (-k.count("1"), k), reverse=True):
        members = [labels[i] for i, b in enumerate(key) if b == "1"]
        if not members:
            continue
        if len(members) == len(labels):
            name = "all three" if len(labels) == 3 else "both"
        else:
            name = " and ".join(members) + " only"
        out.append(f"{name} {_fmt_count(subsets[key])}")
    return ", ".join(out)


def _savefig(fig, out_path, *, dpi: int, facecolor: str) -> None:
    """Save; SVG keeps its text as <text> rather than outlined paths.

    matplotlib outlines glyphs by default, which leaves a screen reader
    nothing to read and the contrast audit nothing to measure — the
    diagram-check gate reports such a file as blind.
    """
    import matplotlib.pyplot as plt

    rc = {"svg.fonttype": "none"} if Path(out_path).suffix.lower() == ".svg" else {}
    with plt.rc_context(rc):
        fig.savefig(str(out_path), dpi=dpi, bbox_inches="tight",
                    facecolor=facecolor)


def _data_num(v: float) -> str:
    f = float(v)
    return str(int(f)) if f.is_integer() and abs(f) < 1e15 else repr(f)


def _gid_prefix(out_path, kind: str) -> str:
    from muriel.tools.diagrams._a11y import figure_slug
    return figure_slug(out_path, kind)


_GID_TEXT_RE = __import__("re").compile(
    r'(<g id="(?P<gid>[^"]+)">\s*<text\b)')


def _annotate_svg(text: str, annotations: Dict[str, Dict[str, str]]) -> str:
    """Add ``data-*`` attributes to the elements matplotlib wrapped in ``gid``s.

    matplotlib writes an artist's ``gid`` as the id of a ``<g>`` around the
    element; the data belongs on the element itself (the ``<text>`` a test
    or a reader recomputes from), so it is attached there.
    """
    from xml.sax.saxutils import quoteattr

    def text_attrs(m):
        attrs = annotations.get(m.group("gid"), {})
        extra = "".join(f" {k}={quoteattr(v)}" for k, v in attrs.items()
                        if k.startswith("data-"))
        return m.group(1) + extra

    return _GID_TEXT_RE.sub(text_attrs, text)


def _write_accessible(out_path, *, kind: str, title: Optional[str],
                      desc: str,
                      annotations: Optional[Dict[str, Dict[str, str]]] = None,
                      ) -> None:
    """matplotlib writes no <title>/<desc>; add the contract to SVG output."""
    path = Path(out_path)
    if path.suffix.lower() != ".svg":
        return  # raster output has no accessible-name slot
    from muriel.tools.diagrams._a11y import figure_slug, inject_a11y
    text = path.read_text(encoding="utf-8")
    if annotations:
        text = _annotate_svg(text, annotations)
    path.write_text(
        inject_a11y(text, slug=figure_slug(path, kind),
                    title=title or "Venn diagram", desc=desc),
        encoding="utf-8",
    )


# ─── Key normalization ───────────────────────────────────────────────

def _normalize_venn3(sets: Dict[str, int], labels: Sequence[str]) -> Dict[str, float]:
    """
    Accept mixed key conventions and produce the matplotlib_venn3 dict
    (keys are '100', '010', '001', '110', '101', '011', '111').

    Accepted alias keys (case-insensitive):
      labels[0]                               → '100'
      labels[1]                               → '010'
      labels[2]                               → '001'
      labels[0] + '_' + labels[1] / 'ab'      → '110'
      labels[0] + '_' + labels[2] / 'ac'      → '101'
      labels[1] + '_' + labels[2] / 'bc'      → '011'
      'all' / 'abc'                           → '111'
    """
    a, b, c = [s.lower() for s in labels]
    alias_map = {
        a: "100", "a": "100",
        b: "010", "b": "010",
        c: "001", "c": "001",
        f"{a}_{b}": "110", "ab": "110", f"{b}_{a}": "110",
        f"{a}_{c}": "101", "ac": "101", f"{c}_{a}": "101",
        f"{b}_{c}": "011", "bc": "011", f"{c}_{b}": "011",
        "all": "111", "abc": "111",
    }
    out: Dict[str, float] = {k: 0.0 for k in ("100", "010", "001", "110", "101", "011", "111")}
    for raw_key, value in sets.items():
        canonical = alias_map.get(raw_key.lower(), raw_key)
        if canonical not in out:
            raise ValueError(f"unrecognized subset key {raw_key!r}; expected one of {list(alias_map)}")
        out[canonical] = float(value)
    return out


def _normalize_venn2(sets: Dict[str, int], labels: Sequence[str]) -> Dict[str, float]:
    """Same idea, 2-set — keys '10', '01', '11'."""
    a, b = [s.lower() for s in labels]
    alias_map = {
        a: "10", "a": "10",
        b: "01", "b": "01",
        f"{a}_{b}": "11", "ab": "11", f"{b}_{a}": "11",
        "both": "11", "all": "11",
    }
    out: Dict[str, float] = {k: 0.0 for k in ("10", "01", "11")}
    for raw_key, value in sets.items():
        canonical = alias_map.get(raw_key.lower(), raw_key)
        if canonical not in out:
            raise ValueError(f"unrecognized subset key {raw_key!r}")
        out[canonical] = float(value)
    return out


# ─── Brand-driven styling ────────────────────────────────────────────

def _region_colors(brand) -> List[str]:
    """Pick three distinct brand-aware fill colors."""
    fallback = ["#66bb6a", "#e6a817", "#ff8282"]
    if brand is None:
        return fallback
    viz = brand.viz.categorical
    if len(viz) >= 3:
        return [viz[2], viz[3], viz[4]] if len(viz) >= 5 else list(viz[:3])
    sem = brand.semantic
    return [
        (sem["success"].text if "success" in sem else fallback[0]),
        (sem["warning"].text if "warning" in sem else fallback[1]),
        (sem["error"].text if "error" in sem else fallback[2]),
    ]


def _text_color(brand) -> str:
    if brand is None:
        return "#0a0a0f"
    return brand.colors.background  # dark background means dark text on light regions


def _bg_color(brand) -> str:
    if brand is None:
        return "#fafaf8"
    # Venns read better on a light panel, so use muted cream if available
    return "#fafaf8"


# ─── Plotting ────────────────────────────────────────────────────────

def _plot_venn_on_axis(
    ax,
    sets: Dict[str, float],
    labels: Sequence[str],
    *,
    brand,
    subset_labels: Optional[Dict[str, str]] = None,
    title: Optional[str] = None,
    gid_prefix: Optional[str] = None,
) -> Dict[str, Dict[str, str]]:
    """Render a 2- or 3-set Venn on the given matplotlib axis.

    Returns ``{gid: {attr: value}}`` for the SVG post-pass: each region's
    count label carries ``data-region`` (the binary subset key) and
    ``data-count`` (the value from the spec, not the drawn string), so a
    test can recompute the regions from the file.
    """
    import matplotlib.pyplot as plt  # noqa: F401 (asserts matplotlib installed)
    from matplotlib_venn import venn2, venn3

    colors = _region_colors(brand)
    text_color = "#0f1117"

    if len(labels) == 3:
        v = venn3(subsets=sets, set_labels=tuple(labels), ax=ax,
                  set_colors=colors, alpha=0.55)
    elif len(labels) == 2:
        v = venn2(subsets=sets, set_labels=tuple(labels), ax=ax,
                  set_colors=colors[:2], alpha=0.55)
    else:
        raise ValueError(f"venn supports 2 or 3 sets; got {len(labels)}")

    # Style the set labels
    for key in (v.set_labels or []):
        if key is not None:
            key.set_fontsize(12)
            key.set_fontweight("bold")
            key.set_color(text_color)

    # Style the subset (count) labels; strip trailing ".0" for integer counts
    if subset_labels is not None:
        for region_key, text in subset_labels.items():
            region = v.get_label_by_id(region_key)
            if region is not None:
                region.set_text(text)
    for lbl in filter(None, v.subset_labels):
        lbl.set_fontsize(10)
        lbl.set_color(text_color)
        txt = lbl.get_text()
        if txt.endswith(".0"):
            lbl.set_text(txt[:-2])

    if title:
        ax.set_title(title, fontsize=13, color=text_color, pad=10, loc="left")

    annotations: Dict[str, Dict[str, str]] = {}
    if gid_prefix:
        for region_id in sets:
            lbl = v.get_label_by_id(region_id)
            if lbl is None:
                continue
            gid = f"{gid_prefix}-region-{region_id}"
            lbl.set_gid(gid)
            annotations[gid] = {"data-region": region_id,
                                "data-count": _data_num(sets[region_id])}
    return annotations


def venn_single(
    sets: Dict[str, int],
    *,
    labels: Optional[Sequence[str]] = None,
    brand=None,
    title: Optional[str] = None,
    out_path: Union[str, Path] = "venn.png",
    figsize=(8, 6),
    dpi: int = 200,
    subset_labels: Optional[Dict[str, str]] = None,
    desc: Optional[str] = None,
) -> str:
    """
    Render a single area-proportional Venn and save to ``out_path``.

    ``sets`` is a dict of {subset-key: count}; ``labels`` names the 2 or 3
    sets. If ``labels`` is omitted, the three longest prefix keys become
    the set labels (convenient for ``{"muriel": N, "marginalia": N, ...}``
    inputs).

    For ``.svg`` output the file carries the accessible-figure contract
    (``role="img"``, ``<title>``, ``<desc>``). ``desc`` should say what
    the overlap argues; the default only names the sets and region counts.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "muriel.tools.venn requires matplotlib. Install with 'pip install matplotlib matplotlib-venn'."
        ) from exc
    try:
        import matplotlib_venn  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "muriel.tools.venn requires matplotlib-venn. Install with 'pip install matplotlib-venn'."
        ) from exc

    if labels is None:
        candidates = [k for k in sets if "_" not in k and k.lower() not in ("all", "both", "abc")]
        labels = candidates[:3] if len(candidates) >= 3 else candidates[:2]
        if len(labels) not in (2, 3):
            raise ValueError("provide `labels` explicitly for this input")

    normalizer = _normalize_venn3 if len(labels) == 3 else _normalize_venn2
    subsets = normalizer(sets, labels)

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi, facecolor=_bg_color(brand))
    ax.set_facecolor(_bg_color(brand))
    ann = _plot_venn_on_axis(ax, subsets, labels, brand=brand,
                             subset_labels=subset_labels, title=title,
                             gid_prefix=_gid_prefix(out_path, "venn"))
    fig.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    _savefig(fig, out_path, dpi=dpi, facecolor=_bg_color(brand))
    plt.close(fig)
    if desc is None:
        from muriel.tools.diagrams._a11y import default_desc
        desc = default_desc(
            f"Area-proportional Venn diagram of {len(labels)} sets", title,
            ["sets: " + ", ".join(labels),
             "region sizes: " + _regions_desc(subsets, labels)])
    _write_accessible(out_path, kind="venn", title=title, desc=desc,
                      annotations=ann)
    return str(out_path)


def _main(argv=None) -> int:
    """Minimal CLI — render a 2- or 3-set Venn from a JSON spec file.

    The JSON spec looks like::

        {
          "labels": ["muriel", "marginalia", "iblipper"],
          "sets":   {"muriel": 14, "marginalia": 8, "iblipper": 6,
                     "muriel_marginalia": 3, "all": 2},
          "title":  "Overlapping scope",
          "brand":  "examples/muriel-brand.toml"
        }

    Usage: python -m muriel.tools.venn spec.json output.png
    """
    import argparse, json

    ap = argparse.ArgumentParser(
        prog="python -m muriel.tools.venn",
        description="Area-proportional Venn / Euler diagram from a JSON spec.",
    )
    ap.add_argument("spec", help="Path to a JSON spec file (see module docstring)")
    ap.add_argument("output", help="Output PNG path")
    args = ap.parse_args(argv)

    with open(args.spec) as f:
        spec = json.load(f)

    brand = None
    if "brand" in spec:
        from muriel.styleguide import load_styleguide
        brand = load_styleguide(spec["brand"])

    venn_single(
        sets=spec["sets"],
        labels=spec.get("labels"),
        brand=brand,
        title=spec.get("title"),
        out_path=args.output,
        desc=spec.get("desc"),
    )
    print(f"→ {args.output}")
    return 0


def venn_panels(
    panels: List[Dict],
    *,
    brand=None,
    title: Optional[str] = None,
    out_path: Union[str, Path] = "venn-panels.png",
    figsize=None,
    dpi: int = 200,
    desc: Optional[str] = None,
) -> str:
    """
    Render two or more Venn diagrams side by side — the AF
    "LAB vs WILD" pattern. ``.svg`` output carries ``role="img"`` plus
    ``<title>``/``<desc>``; pass ``desc`` to say what the comparison shows.

    Each entry in ``panels`` is a dict:
      {"sets": {...}, "labels": [a, b, (c)], "title": "...",
       "subset_labels": {...}  # optional}

    Returns the written path.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "muriel.tools.venn requires matplotlib. Install with 'pip install matplotlib matplotlib-venn'."
        ) from exc

    n = len(panels)
    if figsize is None:
        figsize = (7.5 * n, 6)

    fig, axes = plt.subplots(1, n, figsize=figsize, dpi=dpi,
                             facecolor=_bg_color(brand))
    if n == 1:
        axes = [axes]
    for ax in axes:
        ax.set_facecolor(_bg_color(brand))

    ann: Dict[str, Dict[str, str]] = {}
    prefix = _gid_prefix(out_path, "venn-panels")
    for i, spec in enumerate(panels):
        labels = spec["labels"]
        normalizer = _normalize_venn3 if len(labels) == 3 else _normalize_venn2
        subsets = normalizer(spec["sets"], labels)
        ann.update(_plot_venn_on_axis(
            axes[i], subsets, labels, brand=brand,
            subset_labels=spec.get("subset_labels"),
            title=spec.get("title"),
            gid_prefix=f"{prefix}-p{i}",
        ))

    if title:
        fig.suptitle(title, fontsize=14, color="#0f1117", y=1.01)

    fig.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    _savefig(fig, out_path, dpi=dpi, facecolor=_bg_color(brand))
    plt.close(fig)
    if desc is None:
        from muriel.tools.diagrams._a11y import default_desc
        panel_txt = []
        for spec in panels:
            labels = spec["labels"]
            normalizer = _normalize_venn3 if len(labels) == 3 else _normalize_venn2
            subsets = normalizer(spec["sets"], labels)
            head = spec.get("title") or " / ".join(labels)
            panel_txt.append(f"{head}: {_regions_desc(subsets, labels)}")
        desc = default_desc(f"{n} area-proportional Venn panels", title,
                            panel_txt)
    _write_accessible(out_path, kind="venn-panels", title=title, desc=desc,
                      annotations=ann)
    return str(out_path)
