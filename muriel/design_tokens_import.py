"""
muriel.design_tokens_import — import a design-tokens JSON into a muriel brand.toml.

Handles two input shapes, auto-detected:

  1. ATV / open-codesign ``tokens.json`` (``schemaVersion: 1``): a
     primitive / semantic / component tree of *bare* values, with
     ``{group.token}`` alias references
     (e.g. ``"{primitive.color.brass500}"``).
  2. W3C DTCG tokens — the format ``muriel export-dtcg`` emits: each token is
     a ``{"$value": ..., "$type": ...}`` object and aliases are ``{group.token}``.

Both normalise to a flat ``{dotted.path: resolved_value}`` map, then route by
path/leaf-name heuristics into muriel's brand.toml v2 schema. This closes the
round-trip with ``muriel export-dtcg`` (toml → DTCG → toml) and gives muriel a
front door for any design-token tool that speaks DTCG or the open-codesign
``tokens.json`` shape.

Lossy by design: DTCG and tokens.json can't natively express muriel's viz
palettes, ring gradients, semantic state *trios* (only the ``text`` colour
survives unless ``surface``/``border`` are present), or typed iconography.
The ``component`` layer of tokens.json is recorded as prose under
``[rules]`` rather than expanded — components don't map onto brand tokens.

muriel's universal 8:1 contrast floor overrides whatever the source ships:
the imported foreground/background pair and each semantic state's text colour
are re-gated against 8.0 via :func:`muriel.contrast.contrast_ratio`, and any
shortfall is surfaced as a WARN. The import still completes — the floor stays
the validation gate, not an import blocker (same policy as ``muriel import``).

Usage
-----

::

    muriel import-tokens tokens.json --out brands/foo/brand.toml
    muriel import-tokens tokens.json          # writes ./brand.toml

Zero deps: stdlib ``json`` + the shared TOML emitter and 8:1 floor constant
from :mod:`muriel.design_md_import`.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

# Reuse the zero-dep TOML emitter and the universal contrast floor rather than
# re-rolling them — design_md_import is the sibling importer and owns both.
from muriel.design_md_import import MURIEL_MIN_CONTRAST, _emit_toml

try:
    from muriel.contrast import contrast_ratio
except Exception:  # pragma: no cover - contrast is core, but stay defensive
    contrast_ratio = None  # type: ignore[assignment]


# ─── Flatten + alias resolution ───────────────────────────────────────────


_ALIAS_RE = re.compile(r"^\{([A-Za-z0-9_.\-]+)\}$")
_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")

# Top-level keys that are document metadata, not token groups.
_META_KEYS = {"name", "description", "schemaversion", "$schema", "$description"}


def _is_dtcg_token(node: Any) -> bool:
    """A DTCG token is a dict carrying a ``$value`` key."""
    return isinstance(node, dict) and "$value" in node


def _flatten_tokens(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Walk a tokens tree into ``{dotted.path: value}``.

    Recognises both shapes: a DTCG ``{"$value": ...}`` token contributes its
    ``$value`` at the node's path; a bare scalar (tokens.json) contributes
    itself. ``$``-prefixed bookkeeping keys (other than ``$value``) and the
    document-meta keys are skipped.
    """
    out: dict[str, Any] = {}
    if _is_dtcg_token(obj):
        out[prefix] = obj["$value"]
        return out
    if isinstance(obj, dict):
        for key, value in obj.items():
            k = str(key)
            if not prefix and k.lower() in _META_KEYS:
                continue
            if k.startswith("$"):
                continue
            child = f"{prefix}.{k}" if prefix else k
            out.update(_flatten_tokens(value, child))
        return out
    if isinstance(obj, (str, int, float, bool)) and prefix:
        out[prefix] = obj
    return out


def _resolve_aliases(flat: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Resolve ``{group.token}`` references against the flat map.

    Returns ``(resolved, warnings)``. Cycles and dangling references resolve
    to the literal alias string and emit a WARN so the brand author can see
    what dropped. A reference may target either the exact dotted path or its
    ``$value``-stripped equivalent (both spellings live in ``flat``).
    """
    warnings: list[str] = []
    resolved: dict[str, Any] = {}

    def resolve(value: Any, seen: tuple[str, ...]) -> Any:
        if not isinstance(value, str):
            return value
        m = _ALIAS_RE.match(value.strip())
        if not m:
            return value
        target = m.group(1)
        if target in seen:
            warnings.append(f"alias cycle at {{{target}}} — left unresolved")
            return value
        if target not in flat:
            warnings.append(f"alias {{{target}}} has no target — left unresolved")
            return value
        return resolve(flat[target], seen + (target,))

    for path, value in flat.items():
        resolved[path] = resolve(value, (path,))
    return resolved, warnings


# ─── Token → muriel mapping ───────────────────────────────────────────────


# Leaf-name token-set → muriel [colors] role. The *most specific* rule wins
# (the one whose required tokens are all present and most numerous), so
# `textPrimary` beats the generic `text→foreground` and `bgSurfaceMuted` beats
# `bgSurface`. Ties break by list order. Matching is case-insensitive on the
# leaf segment after camelCase/word splitting.
_COLOR_ROLE_RULES: list[tuple[tuple[str, ...], str]] = [
    # background — the base canvas
    (("bg", "app"),            "background"),
    (("background",),          "background"),
    (("canvas",),              "background"),
    (("bg",),                  "background"),
    # background_2 — raised surfaces (cards, sheets)
    (("bg", "surface"),        "background_2"),
    (("surface", "raised"),    "background_2"),
    (("surface", "card"),      "background_2"),
    (("card",),                "background_2"),
    (("surface",),             "background_2"),
    # background_3 — muted/sunken panels, dividers
    (("bg", "surface", "muted"), "background_3"),
    (("surface", "muted"),     "background_3"),
    (("surface", "sunken"),    "background_3"),
    # foreground — primary text
    (("text", "primary"),      "foreground"),
    (("foreground",),          "foreground"),
    (("body",),                "foreground"),
    (("ink",),                 "foreground"),
    (("text",),                "foreground"),
    # foreground_muted — secondary/tertiary text
    (("text", "secondary"),    "foreground_muted"),
    (("text", "muted"),        "foreground_muted"),
    (("text", "tertiary"),     "foreground_muted"),
    (("muted",),               "foreground_muted"),
    # accent_ink — higher-contrast accent (check before plain accent/ink)
    (("accent", "ink"),        "accent_ink"),
    (("ink", "accent"),        "accent_ink"),
    # accent
    (("accent", "value"),      "accent"),
    (("accent",),              "accent"),
    (("primary",),             "accent"),
    (("brand",),               "accent"),
]

# Leaf-name → semantic state. The text colour of each state must clear the
# 8:1 floor (re-gated below). open-codesign / ATV uses `stateSecure` etc.;
# DTCG (muriel export) nests under `semantic.<state>.text`.
_SEMANTIC_STATE_ALIASES: dict[str, str] = {
    "secure":   "success",
    "success":  "success",
    "positive": "success",
    "ok":       "success",
    "info":     "info",
    "scheduled": "info",
    "warning":  "warning",
    "caution":  "warning",
    "warn":     "warning",
    "danger":   "error",
    "error":    "error",
    "destructive": "error",
    "critical": "error",
}

_CAMEL_RE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")


def _leaf_tokens(path: str) -> list[str]:
    """Split the final path segment into lowercase word tokens.

    ``semantic.color.bgApp`` → ``["bg", "app"]``;
    ``color.semantic.success.text`` → ``["text"]`` (the leaf only).
    """
    leaf = path.split(".")[-1]
    return [t.lower() for t in _CAMEL_RE.findall(leaf)]


def _path_tokens(path: str) -> list[str]:
    """All path segments split into lowercase word tokens."""
    toks: list[str] = []
    for seg in path.split("."):
        toks.extend(t.lower() for t in _CAMEL_RE.findall(seg))
    return toks


def _is_color_path(path: str, value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if _HEX_RE.match(value.strip()):
        return True
    return "color" in _path_tokens(path) and value.strip().startswith("#")


def _semantic_state_for(path: str) -> Optional[str]:
    """If this colour path names a semantic state, return the muriel state."""
    toks = _path_tokens(path)
    if "semantic" in toks:
        # DTCG: semantic.<state>.<role>
        for seg in toks:
            if seg in _SEMANTIC_STATE_ALIASES:
                return _SEMANTIC_STATE_ALIASES[seg]
    # tokens.json: stateSecure / stateWarning …
    leaf = _leaf_tokens(path)
    if leaf and leaf[0] == "state" and len(leaf) > 1:
        return _SEMANTIC_STATE_ALIASES.get(leaf[1])
    # bare leaf that *is* a state word (success/warning/error/info)
    if len(leaf) == 1 and leaf[0] in _SEMANTIC_STATE_ALIASES:
        return _SEMANTIC_STATE_ALIASES[leaf[0]]
    return None


def _semantic_role_for(path: str) -> str:
    """text / surface / border within a semantic state (default: text)."""
    leaf = _leaf_tokens(path)
    for role in ("surface", "bg", "background"):
        if role in leaf:
            return "surface"
    if "border" in leaf:
        return "border"
    return "text"


def _color_role_for(path: str) -> Optional[str]:
    """Map a non-state colour path to a muriel [colors] role, or None.

    Most-specific rule wins: among rules whose required tokens are all present
    in the leaf, pick the one requiring the most tokens (ties → list order).
    """
    leaf = set(_leaf_tokens(path))
    best_role: Optional[str] = None
    best_len = 0
    for needed, role in _COLOR_ROLE_RULES:
        if len(needed) > best_len and all(tok in leaf for tok in needed):
            best_role, best_len = role, len(needed)
    return best_role


def _is_component_path(path: str) -> bool:
    """True for tokens.json ``component.*`` bindings — they reference other
    tokens rather than defining new ones, so they're not mined into brand
    tokens (the layer is preserved as prose instead)."""
    first = path.split(".", 1)[0].lower()
    return first in ("component", "components")


def _coerce_dimension(value: Any) -> Optional[int]:
    """``16`` / ``"16px"`` / ``"1rem"`` → an int pixel count where sensible."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        m = re.match(r"^(-?\d+(?:\.\d+)?)\s*(px|rem|em)?$", value.strip())
        if m:
            n = float(m.group(1))
            unit = m.group(2)
            if unit in ("rem", "em"):
                n *= 16.0
            return int(round(n))
    return None


def _coerce_ms(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        m = re.match(r"^(-?\d+(?:\.\d+)?)\s*(ms|s)?$", value.strip())
        if m:
            n = float(m.group(1))
            if m.group(2) == "s":
                n *= 1000.0
            return int(round(n))
    return None


def _cubic_from_list(value: Any) -> Optional[str]:
    """DTCG cubicBezier ``[x1,y1,x2,y2]`` → a CSS ``cubic-bezier(...)`` string."""
    if isinstance(value, list) and len(value) == 4 and all(
        isinstance(n, (int, float)) for n in value
    ):
        return "cubic-bezier(" + ", ".join(f"{float(n):g}" for n in value) + ")"
    if isinstance(value, str):
        return value
    return None


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", str(name).lower()).strip("-") or "imported"


def tokens_to_brand(
    raw: dict[str, Any],
    source: Optional[Path] = None,
) -> tuple[dict[str, Any], list[str]]:
    """Translate a parsed tokens JSON dict into a muriel brand.toml dict.

    Returns ``(toml_dict, warnings)``. The non-IO core of
    :func:`import_design_tokens` — usable directly for tests and batch ingest.
    """
    source = source or Path("<memory>")
    warnings: list[str] = []

    flat = _flatten_tokens(raw)
    resolved, alias_warnings = _resolve_aliases(flat)
    warnings.extend(alias_warnings)

    # component.* paths are bindings onto other tokens, not token definitions —
    # exclude them from mining (the layer is preserved as prose below).
    tokens = {p: v for p, v in resolved.items() if not _is_component_path(p)}

    out: dict[str, Any] = {}

    # ── meta ──────────────────────────────────────────────────────────────
    name = raw.get("name") or (source.stem if source.name != "<memory>" else "imported")
    out["meta"] = {
        "name":             str(name),
        "slug":             _slugify(str(name)),
        "version":          "1.0.0",
        "owner_repo":       "imported",
        "owner_path":       str(source),
        "canonical_source": str(source),
        "ownership_rule":   f"Imported from design tokens ({source.name}); "
                            f"hand-augment with muriel-specific fields as needed.",
    }
    description = raw.get("description")
    if isinstance(description, str) and description.strip():
        out["meta"]["description"] = description.strip()

    # ── colors + semantic states ──────────────────────────────────────────
    colors_out: dict[str, Any] = {}
    named: dict[str, str] = {}
    semantic_out: dict[str, dict[str, str]] = {}

    # Prefer semantic-layer role names over raw primitives: walk paths with a
    # `semantic` segment first so intent-named colours win the muriel role.
    color_paths = [p for p, v in tokens.items() if _is_color_path(p, v)]
    color_paths.sort(key=lambda p: (0 if "semantic" in _path_tokens(p) else 1, p))

    for path in color_paths:
        value = str(tokens[path]).strip()
        state = _semantic_state_for(path)
        if state:
            role = _semantic_role_for(path)
            semantic_out.setdefault(state, {})
            semantic_out[state].setdefault(role, value)
            continue
        role = _color_role_for(path)
        if role and role not in colors_out:
            colors_out[role] = value
        else:
            # Free-form accent — keep reachable by its leaf name.
            leaf = path.split(".")[-1]
            named.setdefault(leaf, value)

    # background + foreground are required by muriel.colors — default + WARN.
    if "background" not in colors_out:
        colors_out["background"] = "#0a0a0f"
        warnings.append("colors.background missing in source — defaulted to #0a0a0f")
    if "foreground" not in colors_out:
        colors_out["foreground"] = "#e6e4d2"
        warnings.append("colors.foreground missing in source — defaulted to #e6e4d2")
    if named:
        colors_out["named"] = named
    out["colors"] = colors_out
    if semantic_out:
        out["semantic"] = semantic_out

    # ── typography ────────────────────────────────────────────────────────
    typography_out: dict[str, Any] = {}
    for path, value in tokens.items():
        if not isinstance(value, str):
            continue
        toks = _path_tokens(path)
        leaf = _leaf_tokens(path)
        is_font = (
            "font" in toks or "fontfamily" in toks
            or "typography" in toks or "family" in leaf
        )
        if not is_font:
            continue
        # Only treat strings that look like font stacks (contain a letter and
        # are not hex) — skip resolved colours that live under `typography`.
        if value.strip().startswith("#"):
            continue
        if "display" in leaf or "heading" in leaf or "title" in leaf:
            typography_out.setdefault("display_family", value)
        elif "mono" in leaf or "data" in leaf or "code" in leaf:
            typography_out.setdefault("mono_family", value)
        elif "ui" in leaf or "body" in leaf or "text" in leaf or "sans" in leaf:
            typography_out.setdefault("body_family", value)
    if typography_out:
        out["typography"] = typography_out

    # ── spacing / radii ───────────────────────────────────────────────────
    spacing_out: dict[str, Any] = {}
    radii_out: dict[str, Any] = {}
    for path, value in tokens.items():
        toks = _path_tokens(path)
        leaf = path.split(".")[-1]
        if any(t in toks for t in ("radius", "radii")):
            px = _coerce_dimension(value)
            if px is not None:
                radii_out.setdefault(leaf, px)
        elif any(t in toks for t in ("space", "spacing")):
            px = _coerce_dimension(value)
            if px is not None:
                spacing_out.setdefault(leaf, px)
    if spacing_out:
        out["spacing"] = spacing_out
    if radii_out:
        out["radii"] = radii_out

    # ── motion ────────────────────────────────────────────────────────────
    motion_out: dict[str, Any] = {}
    for path, value in tokens.items():
        toks = _path_tokens(path)
        leaf = path.split(".")[-1]
        leaf_words = _leaf_tokens(path)
        in_motion = "motion" in toks
        is_duration = (
            "duration" in toks
            or (in_motion and (leaf_words and leaf_words[-1] == "ms"))
        )
        is_easing = (
            "easing" in toks or "cubicbezier" in toks
            or (in_motion and leaf_words and leaf_words[0] == "ease")
        )
        if is_duration:
            ms = _coerce_ms(value)
            if ms is not None:
                key = re.sub(r"(?:_?ms|Ms)$", "", leaf)
                key = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_") or "fast"
                motion_out.setdefault(f"duration_{key}", ms)
        elif is_easing:
            cb = _cubic_from_list(value)
            if cb is not None:
                key = re.sub(r"^ease[_-]?", "", leaf, flags=re.I)
                key = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_") or "default"
                motion_out.setdefault(f"easing_{key}", cb)
    if motion_out:
        out["motion"] = motion_out

    # ── a11y / contrast re-gate ───────────────────────────────────────────
    a11y: dict[str, Any] = {"min_contrast_ratio": MURIEL_MIN_CONTRAST}
    out["a11y"] = a11y

    if contrast_ratio is not None:
        bg = colors_out.get("background")
        fg = colors_out.get("foreground")
        try:
            if bg and fg:
                ratio = contrast_ratio(fg, bg)
                if ratio < MURIEL_MIN_CONTRAST:
                    warnings.append(
                        f"foreground/background contrast is {ratio:.2f}:1 — below "
                        f"muriel's {MURIEL_MIN_CONTRAST:g}:1 floor. Imported as-is; "
                        f"muriel will still gate against {MURIEL_MIN_CONTRAST:g}."
                    )
            # Each semantic state's text colour on the app background.
            for state, trio in semantic_out.items():
                txt = trio.get("text")
                if txt and bg:
                    ratio = contrast_ratio(txt, bg)
                    if ratio < MURIEL_MIN_CONTRAST:
                        warnings.append(
                            f"semantic.{state}.text contrast is {ratio:.2f}:1 on "
                            f"background — below the {MURIEL_MIN_CONTRAST:g}:1 floor."
                        )
        except Exception as exc:  # pragma: no cover - parse_color is robust
            warnings.append(f"contrast re-gate skipped: {exc}")

    # ── component layer (preserved as prose, not expanded) ────────────────
    component = raw.get("component")
    if isinstance(component, dict) and component:
        names = ", ".join(sorted(component.keys()))
        out["rules"] = {
            "imported_components":
                f"tokens.json carried a component layer ({names}). Components "
                f"don't map onto brand tokens; bind them per channel by hand.",
        }

    return out, warnings


# ─── Public API ───────────────────────────────────────────────────────────


def parse_design_tokens(
    text: str,
    source: Optional[Path] = None,
) -> tuple[dict[str, Any], list[str]]:
    """Parse a design-tokens JSON *string* into the brand.toml dict structure.

    Raises ``ValueError`` if the text is not a JSON object.
    """
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        suffix = f" in {source}" if source else ""
        raise ValueError(f"not valid JSON{suffix}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("design tokens must be a JSON object at the top level")
    return tokens_to_brand(raw, source=source)


def import_design_tokens(
    input_path: Path, output_path: Optional[Path] = None
) -> tuple[Path, list[str]]:
    """Read a tokens JSON file, translate to a muriel brand.toml, write it.

    Returns ``(output_path, warnings)``. Default output is ``./brand.toml``.
    """
    text = input_path.read_text(encoding="utf-8")
    toml_dict, warnings = parse_design_tokens(text, source=input_path)
    output = output_path or Path("brand.toml")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_emit_toml(toml_dict, header=_TOKENS_TOML_HEADER), encoding="utf-8")
    return output, warnings


_TOKENS_TOML_HEADER = (
    "# Generated by `muriel import-tokens` from a design-tokens JSON source.\n"
    "# Colours were re-gated against muriel's universal 8:1 contrast floor on\n"
    "# import (see WARNs). Hand-augment viz palette, logo, and voice as needed.\n"
)


# ─── CLI ────────────────────────────────────────────────────────────────────


def _print_help() -> None:
    print(
        "muriel import-tokens — convert a design-tokens JSON into a muriel brand.toml\n"
        "\n"
        "Usage:\n"
        "  muriel import-tokens <tokens.json> [--out <brand.toml>]\n"
        "\n"
        "Accepts:\n"
        "  - open-codesign / ATV tokens.json (schemaVersion 1, {alias} refs)\n"
        "  - W3C DTCG tokens ($value/$type) — round-trips `muriel export-dtcg`\n"
        "\n"
        "Options:\n"
        "  --out PATH   Output brand.toml path (default: ./brand.toml)\n"
        "  -h, --help   Show this message\n"
        "\n"
        "Lossy: viz palettes, ring gradients, and the component layer don't map\n"
        "onto brand tokens. WARNs print to stderr when an imported colour pair\n"
        "falls below muriel's universal 8:1 contrast floor.\n"
    )


def _main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        _print_help()
        return 0

    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--out", "-o"):
            if i + 1 >= len(args):
                print("muriel import-tokens: --out requires a path", file=sys.stderr)
                return 2
            output_path = Path(args[i + 1])
            i += 2
            continue
        if a.startswith("-"):
            print(f"muriel import-tokens: unknown flag {a!r}", file=sys.stderr)
            return 2
        if input_path is None:
            input_path = Path(a)
            i += 1
            continue
        print(f"muriel import-tokens: unexpected positional argument {a!r}", file=sys.stderr)
        return 2

    if input_path is None:
        print("muriel import-tokens: input path required", file=sys.stderr)
        _print_help()
        return 2
    if not input_path.exists():
        print(f"muriel import-tokens: {input_path} does not exist", file=sys.stderr)
        return 2

    try:
        out, warnings = import_design_tokens(input_path, output_path)
    except (ValueError, OSError) as exc:
        print(f"muriel import-tokens: {exc}", file=sys.stderr)
        return 1

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
