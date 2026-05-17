#!/usr/bin/env python3
"""muriel.dtcg_export — emit a brand.toml as W3C Design Tokens (DTCG) JSON.

Why this exists
---------------
``muriel.design_md_import`` reads a Google Stitch design.md and produces
a muriel brand.toml. This module is the third leg of the round-trip:
brand.toml → DTCG JSON. With both halves, muriel becomes the rigorous
hub between two ecosystems:

* **Stitch design.md** — community-driven, markdown-first, LLM-readable
  brand specs (awesome-design-md corpus etc.).
* **W3C Design Tokens Community Group format** — the platform-neutral
  schema that ``style-dictionary``, ``theo``, Figma tokens-studio,
  ``token-css``, and downstream iOS / Android / Tailwind / CSS-vars
  pipelines all consume.

With this exporter a brand.toml can pivot into the entire
style-dictionary ecosystem without writing any downstream transformer.
Combined with ``muriel import``, the workflow is:

::

    design.md ──import──▶ brand.toml ──export──▶ tokens.json
                              │                       │
                              ▼                       ▼
                       muriel renderers       style-dictionary,
                       (matplotlib, SVG,      theo, Figma plugins,
                       CSS, Playwright)       iOS/Android pipelines

Specification
-------------
DTCG draft (Editor's Draft, 2024+):
https://design-tokens.github.io/community-group/format/

Implementer notes:

* Each leaf token is ``{"$value": <V>, "$type": <T>, "$description": ...}``.
* Groups are nested dicts; group-level ``$description`` / ``$extensions``
  optional.
* Aliases use ``{group.token}`` string syntax in ``$value``.
* This module emits these DTCG types: ``color``, ``dimension``,
  ``fontFamily``, ``fontWeight``, ``duration``, ``cubicBezier``,
  ``typography`` (composite), ``shadow`` (composite, best-effort),
  ``string`` (escape hatch).
* muriel-specific fields that don't fit DTCG cleanly (e.g.
  ``elevation`` CSS box-shadow originals, ``motion.motion_preference``)
  are preserved under ``$extensions.muriel.*`` so a round-trip back to
  brand.toml can recover them.

Lineage
-------
Schema by Design Tokens Community Group (w3c); reference implementations
``style-dictionary`` (Amazon), ``theo`` (Salesforce), ``token-css``
(community). Sibling: ``muriel.design_md_import`` (the other half of
the round-trip).

Usage
-----

::

    from muriel.dtcg_export import to_dtcg, export_dtcg

    # In-memory (e.g. corpus audit pipelines)
    tokens = to_dtcg(brand_toml_dict)

    # File-based
    export_dtcg(Path("brand.toml"), Path("tokens.json"))

CLI
---

::

    muriel export-dtcg brand.toml                      # writes ./tokens.json
    muriel export-dtcg brand.toml -o my-tokens.json
    muriel export-dtcg brand.toml --selftest           # assertion suite

Cross-references: ``muriel.design_md_import`` (round-trip partner),
``muriel.styleguide`` (the in-process dataclass loader for brand.toml),
``muriel.tools.corpus_audit`` (the harness this exporter slots into).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

# ``tomllib`` is Python 3.11+ stdlib. Imported lazily inside the file
# reader so this module loads cleanly on 3.10 (the pure-dict
# ``to_dtcg`` + selftest path is the common case and doesn't need it).

__all__ = [
    "DTCGError",
    "to_dtcg",
    "export_dtcg",
]


class DTCGError(ValueError):
    """Raised when brand-data shape can't be mapped to DTCG."""


# ─── Helpers ────────────────────────────────────────────────────────


def _as_px(v: Any) -> Optional[str]:
    """Coerce a numeric or trailing-``px`` string into a DTCG dimension
    value (always ``"<N>px"``). Returns None if not coercible."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return f"{int(v) if v == int(v) else v}px"
    if isinstance(v, str):
        m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*(px)?\s*$", v)
        if m:
            n = float(m.group(1))
            return f"{int(n) if n == int(n) else n}px"
    return None


def _as_ms(v: Any) -> Optional[str]:
    """Coerce numeric or ``Nms`` string into DTCG duration value."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return f"{int(v) if v == int(v) else v}ms"
    if isinstance(v, str):
        m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*(ms|s)?\s*$", v)
        if m:
            n = float(m.group(1))
            if m.group(2) == "s":
                n *= 1000.0
            return f"{int(n) if n == int(n) else n}ms"
    return None


_CUBIC_RE = re.compile(
    r"cubic-bezier\(\s*(-?\d+(?:\.\d+)?)\s*,"
    r"\s*(-?\d+(?:\.\d+)?)\s*,"
    r"\s*(-?\d+(?:\.\d+)?)\s*,"
    r"\s*(-?\d+(?:\.\d+)?)\s*\)"
)

# Standard keyword → cubic-bezier mappings. DTCG cubicBezier requires
# four numbers; the keyword aliases map to the same control points the
# CSS spec defines for the keywords.
_EASING_KEYWORDS: dict[str, list[float]] = {
    "linear":      [0.0, 0.0, 1.0, 1.0],
    "ease":        [0.25, 0.1, 0.25, 1.0],
    "ease-in":     [0.42, 0.0, 1.0, 1.0],
    "ease-out":    [0.0, 0.0, 0.58, 1.0],
    "ease-in-out": [0.42, 0.0, 0.58, 1.0],
}


def _as_cubic_bezier(v: Any) -> Optional[list[float]]:
    """Parse a CSS easing into DTCG cubic-bezier control points."""
    if not isinstance(v, str):
        return None
    s = v.strip().lower()
    if s in _EASING_KEYWORDS:
        return list(_EASING_KEYWORDS[s])
    m = _CUBIC_RE.search(s)
    if m:
        return [float(m.group(i)) for i in range(1, 5)]
    return None


def _as_em(v: Any) -> Optional[str]:
    """Coerce a number → ``Nem`` string, for letter-spacing fields."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return f"{v}em"
    if isinstance(v, str):
        if v.endswith("em") or v.endswith("rem"):
            return v
    return None


# Permissive shadow parser — handles `0 4px 12px rgba(0,0,0,0.4)` and
# simple variants. Returns the structured DTCG shadow value, or None.
_SHADOW_RE = re.compile(
    r"^\s*"
    r"(-?\d+(?:\.\d+)?)(?:px)?\s+"     # offsetX
    r"(-?\d+(?:\.\d+)?)(?:px)?\s+"     # offsetY
    r"(\d+(?:\.\d+)?)(?:px)?\s+"        # blur
    r"(?:(\d+(?:\.\d+)?)(?:px)?\s+)?"   # spread (optional)
    r"(\S.*\S|\S)\s*$"                  # color (rest of string)
)


def _as_shadow(v: Any) -> Optional[dict[str, Any]]:
    """Best-effort parse of a CSS box-shadow into DTCG shadow value."""
    if not isinstance(v, str):
        return None
    m = _SHADOW_RE.match(v)
    if not m:
        return None
    offset_x = m.group(1)
    offset_y = m.group(2)
    blur = m.group(3)
    spread = m.group(4)
    color = m.group(5)
    out: dict[str, Any] = {
        "color":   color,
        "offsetX": f"{offset_x}px",
        "offsetY": f"{offset_y}px",
        "blur":    f"{blur}px",
    }
    if spread:
        out["spread"] = f"{spread}px"
    return out


# ─── Group mappers ──────────────────────────────────────────────────


def _map_colors(brand: dict[str, Any]) -> dict[str, Any]:
    """[colors] + [colors.aliases] → DTCG color tokens."""
    out: dict[str, Any] = {}
    colors = brand.get("colors") or {}
    aliases = colors.get("aliases") if isinstance(colors, dict) else None

    for key, value in colors.items():
        if key in ("aliases", "named"):
            continue
        if isinstance(value, str):
            out[key] = {"$value": value, "$type": "color"}
        # ``named`` could be a sub-dict — flatten below.
    named = colors.get("named") if isinstance(colors, dict) else None
    if isinstance(named, dict) and named:
        named_out: dict[str, Any] = {}
        for k, v in named.items():
            if isinstance(v, str):
                named_out[k] = {"$value": v, "$type": "color"}
        if named_out:
            out["named"] = named_out

    if isinstance(aliases, dict) and aliases:
        aliases_out: dict[str, Any] = {}
        for alias_name, target in aliases.items():
            if not isinstance(target, str):
                continue
            # If `target` looks like a hex literal, emit as a direct
            # color; otherwise emit as a DTCG alias pointing at
            # `color.{target}`.
            if target.startswith("#"):
                aliases_out[alias_name] = {"$value": target, "$type": "color"}
            else:
                aliases_out[alias_name] = {
                    "$value": "{color." + target + "}",
                    "$type": "color",
                }
        if aliases_out:
            out["aliases"] = aliases_out

    return out


def _map_semantic(brand: dict[str, Any]) -> dict[str, Any]:
    """[semantic.{success,warning,error,info}] → nested DTCG colors."""
    semantic = brand.get("semantic") or {}
    if not isinstance(semantic, dict):
        return {}
    out: dict[str, Any] = {}
    for state, trio in semantic.items():
        if not isinstance(trio, dict):
            continue
        state_out: dict[str, Any] = {}
        for role in ("text", "surface", "border"):
            v = trio.get(role)
            if isinstance(v, str):
                state_out[role] = {"$value": v, "$type": "color"}
        if state_out:
            out[state] = state_out
    return out


def _map_viz(brand: dict[str, Any]) -> dict[str, Any]:
    """[viz.categorical] / [viz.sequential] / [viz.diverging] →
    per-index color tokens (DTCG has no native array type)."""
    viz = brand.get("viz") or {}
    if not isinstance(viz, dict):
        return {}
    out: dict[str, Any] = {}
    for series in ("categorical", "sequential", "diverging"):
        arr = viz.get(series)
        if not isinstance(arr, list):
            continue
        series_out: dict[str, Any] = {}
        for i, color in enumerate(arr):
            if isinstance(color, str):
                # 1-based index so `viz.categorical.1` reads naturally.
                series_out[str(i + 1)] = {"$value": color, "$type": "color"}
        if series_out:
            out[series] = series_out
    return out


def _map_typography(brand: dict[str, Any]) -> tuple[dict, dict, dict]:
    """[typography] → (font_family_tokens, font_weight_tokens, typography_tokens).

    Returns three independent group dicts so the caller can place them
    under DTCG's preferred top-level type groupings.
    """
    typo = brand.get("typography") or {}
    if not isinstance(typo, dict):
        return {}, {}, {}

    ff: dict[str, Any] = {}
    fw: dict[str, Any] = {}
    composite: dict[str, Any] = {}

    # Family scalars at the typography top level.
    for src, dst in (
        ("display_family", "display"),
        ("body_family",    "body"),
        ("mono_family",    "mono"),
    ):
        v = typo.get(src)
        if isinstance(v, str):
            ff[dst] = {"$value": v, "$type": "fontFamily"}

    # Display weight as a fontWeight token.
    if isinstance(typo.get("display_weight"), (int, float)):
        fw["display"] = {
            "$value": int(typo["display_weight"]), "$type": "fontWeight",
        }

    # The scale → composite typography tokens.
    scale = typo.get("scale")
    if isinstance(scale, dict):
        for role, role_def in scale.items():
            if not isinstance(role_def, dict):
                continue
            comp: dict[str, Any] = {}
            size = role_def.get("size")
            weight = role_def.get("weight")
            line_height = role_def.get("line_height") or role_def.get("lineHeight")
            tracking = role_def.get("tracking_em")
            # Pull family from typography top level by role intent —
            # `mono` uses mono_family; `display`/`h1`/`h2` use display;
            # everything else uses body.
            if role == "mono":
                family = typo.get("mono_family")
            elif role in ("display", "h1", "h2", "h3", "h4"):
                family = typo.get("display_family") or typo.get("body_family")
            else:
                family = typo.get("body_family")
            if isinstance(family, str):
                comp["fontFamily"] = family
            if isinstance(weight, (int, float)):
                comp["fontWeight"] = int(weight)
            px = _as_px(size)
            if px is not None:
                comp["fontSize"] = px
            if isinstance(line_height, (int, float)):
                comp["lineHeight"] = float(line_height)
            em = _as_em(tracking)
            if em is not None:
                comp["letterSpacing"] = em
            # `upper: true` isn't part of DTCG typography — preserve via
            # $extensions so a round-trip can recover it.
            extensions = {}
            if role_def.get("upper") is True:
                extensions["muriel"] = {"upper": True}
            if comp:
                token: dict[str, Any] = {
                    "$value": comp, "$type": "typography",
                }
                if extensions:
                    token["$extensions"] = extensions
                composite[role] = token

    return ff, fw, composite


def _map_spacing_and_radii(brand: dict[str, Any]) -> dict[str, Any]:
    """[spacing] + [radii] → DTCG dimension tokens."""
    out: dict[str, Any] = {}
    for src, dst in (("spacing", "spacing"), ("radii", "radius")):
        block = brand.get(src)
        if not isinstance(block, dict):
            continue
        bucket: dict[str, Any] = {}
        for k, v in block.items():
            px = _as_px(v)
            if px is not None:
                bucket[str(k)] = {"$value": px, "$type": "dimension"}
        if bucket:
            out[dst] = bucket
    return out


def _map_motion(brand: dict[str, Any]) -> tuple[dict, dict, dict]:
    """[motion] → (duration_tokens, easing_tokens, raw_strings_for_extensions)."""
    motion = brand.get("motion") or {}
    if not isinstance(motion, dict):
        return {}, {}, {}
    durations: dict[str, Any] = {}
    easings: dict[str, Any] = {}
    other: dict[str, Any] = {}
    for k, v in motion.items():
        if k.startswith("duration"):
            name = k[len("duration_"):] if k.startswith("duration_") else k
            ms = _as_ms(v)
            if ms is not None:
                durations[name] = {"$value": ms, "$type": "duration"}
                continue
        if k.startswith("easing"):
            name = k[len("easing_"):] if k.startswith("easing_") else k
            cb = _as_cubic_bezier(v)
            if cb is not None:
                easings[name] = {"$value": cb, "$type": "cubicBezier"}
                continue
        # Anything else (e.g. motion_preference) goes to $extensions
        # as a literal so a round-trip can recover it.
        other[k] = v
    return durations, easings, other


def _map_shadow(brand: dict[str, Any]) -> tuple[dict, dict]:
    """[elevation] → (shadow_tokens, raw_strings_for_extensions)."""
    elev = brand.get("elevation") or {}
    if not isinstance(elev, dict):
        return {}, {}
    out: dict[str, Any] = {}
    raw: dict[str, Any] = {}
    for k, v in elev.items():
        if not isinstance(v, str):
            continue
        parsed = _as_shadow(v)
        if parsed:
            out[k] = {"$value": parsed, "$type": "shadow"}
        # Always retain the raw CSS string for round-trip.
        raw[k] = v
    return out, raw


def _meta_extensions(brand: dict[str, Any]) -> dict[str, Any]:
    """Build the top-level $extensions blob — muriel-specific bits that
    DTCG doesn't model natively."""
    ext: dict[str, Any] = {}
    meta = brand.get("meta")
    if isinstance(meta, dict):
        ext["meta"] = meta
    # Anything else lives in the per-group $extensions, not here.
    return {"muriel": ext} if ext else {}


# ─── Public API ─────────────────────────────────────────────────────


def to_dtcg(brand: dict[str, Any]) -> dict[str, Any]:
    """Translate a brand.toml dict into DTCG token tree.

    The output is JSON-serialisable and follows the W3C Design Tokens
    Community Group format. Top-level groups are organised by DTCG token
    type for downstream-tool compatibility: ``color``, ``dimension``,
    ``fontFamily``, ``fontWeight``, ``typography``, ``duration``,
    ``cubicBezier``, ``shadow``. Muriel-specific fields land under
    ``$extensions.muriel.*``.
    """
    if not isinstance(brand, dict):
        raise DTCGError(f"brand data must be a dict, got {type(brand).__name__}")

    out: dict[str, Any] = {}

    # color (with nested sub-groups)
    color: dict[str, Any] = {}
    cmap = _map_colors(brand)
    if cmap:
        color.update(cmap)
    semantic = _map_semantic(brand)
    if semantic:
        color["semantic"] = semantic
    viz = _map_viz(brand)
    if viz:
        color["viz"] = viz
    if color:
        out["color"] = color

    # typography family + weight + composite
    ff, fw, composite = _map_typography(brand)
    if ff:
        out["fontFamily"] = ff
    if fw:
        out["fontWeight"] = fw
    if composite:
        out["typography"] = composite

    # spacing + radius → dimension group
    dims = _map_spacing_and_radii(brand)
    if dims:
        out["dimension"] = dims

    # motion → duration + cubicBezier (+ extension carry-overs)
    durations, easings, motion_other = _map_motion(brand)
    if durations:
        out["duration"] = durations
    if easings:
        out["cubicBezier"] = easings

    # elevation → shadow (+ raw CSS extension)
    shadows, raw_shadows = _map_shadow(brand)
    if shadows:
        out["shadow"] = shadows

    # Top-level $extensions for muriel-specific carry-overs.
    extensions: dict[str, Any] = {}
    if motion_other:
        extensions.setdefault("muriel", {})["motion"] = motion_other
    if raw_shadows:
        extensions.setdefault("muriel", {})["elevation_raw"] = raw_shadows
    if isinstance(brand.get("meta"), dict):
        extensions.setdefault("muriel", {})["meta"] = brand["meta"]
    # iconography / imagery / logo / voice — preserve verbatim so a
    # future brand.toml round-trip importer can recover them.
    for carry in ("iconography", "imagery", "logo", "voice", "rules",
                  "provenance", "a11y"):
        v = brand.get(carry)
        if v is not None:
            extensions.setdefault("muriel", {})[carry] = v
    if extensions:
        out["$extensions"] = extensions

    return out


def export_dtcg(
    brand_toml_path: Path,
    output_path: Optional[Path] = None,
) -> Path:
    """Read a brand.toml, emit DTCG JSON to ``output_path`` (default:
    ``./tokens.json``). Returns the output path."""
    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError as exc:
        raise DTCGError(
            "tomllib (Python 3.11+ stdlib) required to read brand.toml. "
            "Either upgrade to Python 3.11+ or hand-load the brand dict "
            "and call to_dtcg() directly."
        ) from exc
    with open(brand_toml_path, "rb") as f:
        brand = tomllib.load(f)
    tokens = to_dtcg(brand)
    out = output_path or Path("tokens.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(tokens, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out


# ─── Selftest / CLI ─────────────────────────────────────────────────


def _selftest() -> int:
    # Numeric coercers.
    assert _as_px(4) == "4px"
    assert _as_px(1.5) == "1.5px"
    assert _as_px("16") == "16px"
    assert _as_px("16px") == "16px"
    assert _as_px("auto") is None
    assert _as_px(True) is None

    assert _as_ms(120) == "120ms"
    assert _as_ms("240") == "240ms"
    assert _as_ms("0.4s") == "400ms"
    assert _as_ms(False) is None

    assert _as_cubic_bezier("linear") == [0.0, 0.0, 1.0, 1.0]
    assert _as_cubic_bezier("cubic-bezier(0.2, 0.0, 0.2, 1.0)") == [0.2, 0.0, 0.2, 1.0]
    assert _as_cubic_bezier("ease-in-out")[0] == 0.42
    assert _as_cubic_bezier(123) is None

    shadow = _as_shadow("0 4px 12px rgba(0,0,0,0.40)")
    assert shadow == {
        "color": "rgba(0,0,0,0.40)",
        "offsetX": "0px",
        "offsetY": "4px",
        "blur": "12px",
    }

    # Synthetic minimal brand → expected DTCG shape.
    brand = {
        "meta": {"name": "Test", "slug": "test"},
        "colors": {
            "background": "#0a0a0f",
            "foreground": "#e6e4d2",
            "accent":     "#50b4c8",
            "aliases":    {"text": "foreground", "surface": "background"},
            "named":      {"highlight": "#ff8282"},
        },
        "semantic": {
            "success": {"text": "#66bb6a", "surface": "#0f1a10", "border": "#66bb6a"},
        },
        "viz": {
            "categorical": ["#e6e4d2", "#50b4c8", "#66bb6a"],
        },
        "typography": {
            "body_family":    "Helvetica, sans-serif",
            "display_family": "Inter, sans-serif",
            "display_weight": 700,
            "scale": {
                "body": {"size": 16, "weight": 400, "line_height": 1.5},
                "h1":   {"size": 40, "weight": 700, "line_height": 1.05, "tracking_em": -0.02},
                "label": {"size": 12, "weight": 600, "line_height": 1.2, "upper": True},
            },
        },
        "spacing": {"sm": 8, "md": 16},
        "radii":   {"sm": 4, "pill": 9999},
        "elevation": {"low": "0 1px 2px rgba(0,0,0,0.30)"},
        "motion": {
            "duration_fast":   120,
            "easing_default":  "cubic-bezier(0.2, 0.0, 0.2, 1.0)",
            "easing_linear":   "linear",
            "motion_preference": "respect-prefers-reduced-motion",
        },
        "iconography": {"family": "custom", "stroke_px": 1.5},
    }
    tokens = to_dtcg(brand)

    # color group structure.
    assert tokens["color"]["background"] == {"$value": "#0a0a0f", "$type": "color"}
    assert tokens["color"]["accent"]["$value"] == "#50b4c8"
    assert tokens["color"]["aliases"]["text"]["$value"] == "{color.foreground}"
    assert tokens["color"]["named"]["highlight"]["$value"] == "#ff8282"
    assert tokens["color"]["semantic"]["success"]["text"]["$value"] == "#66bb6a"
    assert tokens["color"]["viz"]["categorical"]["1"]["$value"] == "#e6e4d2"
    assert tokens["color"]["viz"]["categorical"]["3"]["$value"] == "#66bb6a"

    # fontFamily + typography composite.
    assert tokens["fontFamily"]["body"]["$value"] == "Helvetica, sans-serif"
    assert tokens["fontFamily"]["display"]["$value"] == "Inter, sans-serif"
    assert tokens["fontWeight"]["display"]["$value"] == 700
    body = tokens["typography"]["body"]
    assert body["$type"] == "typography"
    assert body["$value"]["fontSize"] == "16px"
    assert body["$value"]["fontWeight"] == 400
    assert body["$value"]["lineHeight"] == 1.5
    assert body["$value"]["fontFamily"] == "Helvetica, sans-serif"
    h1 = tokens["typography"]["h1"]
    assert h1["$value"]["letterSpacing"] == "-0.02em"
    assert h1["$value"]["fontFamily"] == "Inter, sans-serif"
    label = tokens["typography"]["label"]
    assert label["$extensions"]["muriel"]["upper"] is True

    # dimension.
    assert tokens["dimension"]["spacing"]["sm"]["$value"] == "8px"
    assert tokens["dimension"]["radius"]["pill"]["$value"] == "9999px"

    # duration + cubicBezier.
    assert tokens["duration"]["fast"]["$value"] == "120ms"
    assert tokens["cubicBezier"]["default"]["$value"] == [0.2, 0.0, 0.2, 1.0]
    assert tokens["cubicBezier"]["linear"]["$value"] == [0.0, 0.0, 1.0, 1.0]

    # shadow — derived from the synthetic brand's `elevation.low =
    # "0 1px 2px rgba(0,0,0,0.30)"`, so blur should be 2px.
    assert tokens["shadow"]["low"]["$value"]["blur"] == "2px"
    assert tokens["shadow"]["low"]["$value"]["offsetY"] == "1px"
    assert tokens["shadow"]["low"]["$value"]["color"] == "rgba(0,0,0,0.30)"

    # Extensions: motion_preference + raw elevation + iconography preserved.
    ext = tokens["$extensions"]["muriel"]
    assert ext["motion"]["motion_preference"] == "respect-prefers-reduced-motion"
    assert ext["elevation_raw"]["low"] == "0 1px 2px rgba(0,0,0,0.30)"
    assert ext["iconography"]["family"] == "custom"
    assert ext["meta"]["name"] == "Test"

    # JSON-serialisable end-to-end.
    json.dumps(tokens)

    # Empty / minimal input is non-fatal.
    empty = to_dtcg({})
    assert empty == {} or empty == {"$extensions": {"muriel": {}}}

    # Non-dict input raises.
    try:
        to_dtcg("not a dict")  # type: ignore[arg-type]
    except DTCGError:
        pass
    else:
        raise AssertionError("expected DTCGError")

    return 0


def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="muriel export-dtcg",
        description=(
            "Export a brand.toml as W3C Design Tokens Community Group JSON. "
            "Round-trip partner to `muriel import` (design.md → brand.toml). "
            "Downstream-compatible with style-dictionary, theo, Figma "
            "tokens-studio, token-css, and any DTCG-aware pipeline."
        ),
    )
    ap.add_argument("input", nargs="?", type=Path,
                    help="path to brand.toml")
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="output JSON path (default: ./tokens.json)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the assertion suite and exit")
    args = ap.parse_args(argv)

    if args.selftest:
        _selftest()
        print("muriel.dtcg_export: selftest passed", file=sys.stderr)
        return 0

    if args.input is None:
        ap.print_help()
        return 0
    if not args.input.exists():
        print(f"muriel export-dtcg: {args.input} does not exist", file=sys.stderr)
        return 2

    try:
        out = export_dtcg(args.input, args.output)
    except (OSError, DTCGError, ValueError) as exc:
        # tomllib.TOMLDecodeError is a ValueError subclass — covered above.
        print(f"muriel export-dtcg: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
