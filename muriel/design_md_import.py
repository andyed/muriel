"""
muriel.design_md_import — import a Google Stitch design.md into a muriel brand.toml.

design.md (https://stitch.withgoogle.com/docs/design-md/) is a YAML-frontmatter
+ Markdown-prose format for design systems. muriel's brand.toml v2 is a strict
superset, so importing flattens back to muriel's schema with WARN on quality
gaps (e.g., imported contrast < muriel's universal 8:1 floor).

Lossy by design: design.md's flat frontmatter can't express muriel's ring
gradients, semantic state trios, viz palettes, or typed iconography. Those
fields stay absent after import and can be hand-augmented. Prose sections
("Components", "Do's and Don'ts") are preserved as free-form rules strings.

Round-trip note: this module is the IMPORT half. Export (toml → design.md)
is in TODO.md as a follow-up; round-trip preservation of Stitch-native fields
should be tested when both halves exist.

Usage
-----

::

    muriel import design.md --out brands/my-brand/brand.toml
    muriel import design.md                 # writes to ./brand.toml

Zero deps: hand-rolled YAML frontmatter parser (handles the Stitch schema
shape — strings, numbers, nested dicts, lists; rejects anchors/refs/tags) and
hand-rolled TOML emitter for the subset muriel's brand.toml uses.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Optional, Sequence


# ─── Frontmatter parsing ──────────────────────────────────────────────────


def _split_frontmatter(text: str) -> tuple[str, str]:
    """
    Split a design.md into (frontmatter_yaml, body_markdown).
    Frontmatter is the block between leading ``---`` lines. If no frontmatter
    is present, returns ("", text).
    """
    if not text.startswith("---"):
        return "", text
    # Find the closing fence
    m = re.search(r"^---\s*$\n(.*?)\n^---\s*$\n?", text, flags=re.MULTILINE | re.DOTALL)
    if not m:
        # Malformed: opening --- without closing. Treat whole file as body.
        return "", text
    return m.group(1), text[m.end():]


_NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def _coerce_scalar(s: str) -> Any:
    """Cast a YAML-ish scalar string to int / float / bool / None / str."""
    s = s.strip()
    if not s:
        return ""
    # Strip matching quotes
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if s in ("null", "Null", "NULL", "~"):
        return None
    if _NUM_RE.match(s):
        return float(s) if "." in s else int(s)
    return s


def _parse_yaml_frontmatter(text: str) -> dict[str, Any]:
    """
    Minimal YAML parser for the Stitch frontmatter shape.

    Supports:
      - Top-level scalars: ``key: value``
      - Nested dicts via 2-space indentation
      - Inline string values (quoted or unquoted)
      - Numbers (int / float)
      - Booleans, null
      - List values via ``- item`` lines

    Rejects (raises ValueError):
      - Tabs in indentation (mix-detection is fragile)
      - YAML anchors/refs (``&``/``*``)
      - Tags (``!str`` etc.)
      - Multi-doc separators after the first
    """
    if not text.strip():
        return {}

    lines = text.splitlines()
    # Strip blank + comment lines for the iteration; preserve indentation.
    # Comment stripping must be quote-aware so we don't munch `#FF9632` hex
    # color values. Walk the line; ignore `#` inside a single- or double-quoted
    # string. Strip from the first unquoted `#` to end-of-line.
    cleaned: list[tuple[int, str]] = []
    for raw in lines:
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ValueError(f"design.md frontmatter uses tab indentation; expected spaces: {raw!r}")
        in_dq = False
        in_sq = False
        cut = len(raw)
        for idx, ch in enumerate(raw):
            if ch == '"' and not in_sq:
                in_dq = not in_dq
            elif ch == "'" and not in_dq:
                in_sq = not in_sq
            elif ch == "#" and not in_dq and not in_sq:
                cut = idx
                break
        stripped = raw[:cut].rstrip()
        if not stripped.strip():
            continue
        # Anchor / ref / tag detection runs on the still-quoted content
        if stripped.lstrip().startswith("!"):
            raise ValueError(f"unsupported YAML feature (tag) in: {raw!r}")
        # Anchors and refs use & and * but only at the value position; reject
        # unconditionally to keep the parser scope tight.
        for marker in ("& ", "&\n", "&  ", " *"):
            if marker in stripped:
                raise ValueError(f"unsupported YAML feature (anchor/ref) in: {raw!r}")
        indent = len(stripped) - len(stripped.lstrip(" "))
        cleaned.append((indent, stripped.lstrip(" ")))

    # Recursive-descent style: pop lines from the front, build a dict tree
    pos = [0]

    def parse_block(base_indent: int) -> Any:
        """Parse a block starting at the next line; stops when indent drops below base_indent."""
        # Determine if this is a list block or a map block
        if pos[0] >= len(cleaned):
            return None
        first_indent, first_text = cleaned[pos[0]]
        if first_indent < base_indent:
            return None
        if first_text.startswith("- "):
            return parse_list(base_indent)
        return parse_map(base_indent)

    def parse_map(base_indent: int) -> dict[str, Any]:
        result: dict[str, Any] = {}
        while pos[0] < len(cleaned):
            indent, text_line = cleaned[pos[0]]
            if indent < base_indent:
                break
            if indent > base_indent:
                # Should have been consumed by the previous line's value parser
                raise ValueError(f"unexpected indent at line: {text_line!r}")
            if text_line.startswith("- "):
                # A list-style entry where a map was expected — bail
                break
            if ":" not in text_line:
                raise ValueError(f"expected 'key: value' or 'key:' at line: {text_line!r}")
            key, _, after = text_line.partition(":")
            key = key.strip()
            after = after.strip()
            pos[0] += 1
            if after:
                # Inline value
                result[key] = _coerce_scalar(after)
            else:
                # Nested block — peek next line's indent
                if pos[0] >= len(cleaned):
                    result[key] = None
                    continue
                next_indent, _ = cleaned[pos[0]]
                if next_indent <= base_indent:
                    # Empty value
                    result[key] = None
                else:
                    result[key] = parse_block(next_indent)
        return result

    def parse_list(base_indent: int) -> list[Any]:
        items: list[Any] = []
        while pos[0] < len(cleaned):
            indent, text_line = cleaned[pos[0]]
            if indent < base_indent or not text_line.startswith("- "):
                break
            if indent > base_indent:
                raise ValueError(f"unexpected indent in list at line: {text_line!r}")
            content = text_line[2:].strip()
            pos[0] += 1
            if not content:
                # Sub-block list item (rare in Stitch frontmatter; bail)
                raise ValueError("list-of-blocks not supported in design.md frontmatter import")
            items.append(_coerce_scalar(content))
        return items

    return parse_map(0)


# ─── Prose section parsing ────────────────────────────────────────────────


_HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$", flags=re.MULTILINE)


def _parse_prose_sections(body: str) -> dict[str, str]:
    """
    Extract Markdown sections by their ``##`` headings into a {title: content}
    map. Subsections (``###``) are flattened back into their parent's content
    so we don't lose nesting context.
    """
    matches = list(_HEADING_RE.finditer(body))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        if m.group(1) != "##":
            continue
        title = m.group(2).strip()
        start = m.end()
        # Find next H2 (skip H3s)
        end = len(body)
        for j in range(i + 1, len(matches)):
            if matches[j].group(1) == "##":
                end = matches[j].start()
                break
        content = body[start:end].strip()
        sections[title] = content
    return sections


# ─── Stitch → muriel mapping ──────────────────────────────────────────────


# Map Stitch frontmatter color role names to muriel brand.toml [colors] keys.
# Stitch keys on the left, muriel keys on the right. Unmapped Stitch keys
# fall through into [colors.named] as free-form brand accents.
STITCH_COLOR_TO_MURIEL: dict[str, str] = {
    "primary":      "accent",
    "accent":       "accent",
    "secondary":    "accent_decorative",
    "surface":      "background",
    "background":   "background",
    "on-surface":   "foreground",
    "onSurface":    "foreground",
    "on_surface":   "foreground",
}


# Stitch typography role → muriel typography.scale role
STITCH_TYPE_TO_MURIEL: dict[str, str] = {
    "body":      "body",
    "body-md":   "body",
    "body_md":   "body",
    "headline":  "h1",
    "title":     "h1",
    "subtitle":  "h2",
    "caption":   "caption",
    "label":     "label",
    "mono":      "mono",
}


# Muriel's universal contrast floor — overrides anything an imported spec
# carries. Surfaced as a WARN, not an error: the imported spec's preference
# is recorded; muriel's floor remains the validation gate.
MURIEL_MIN_CONTRAST = 8.0


def _stitch_to_muriel_dict(
    frontmatter: dict[str, Any],
    prose: dict[str, str],
    source_path: Path,
) -> tuple[dict[str, Any], list[str]]:
    """
    Translate parsed Stitch design.md content into a muriel brand.toml dict
    suitable for emission via ``_emit_toml``. Returns (toml_dict, warnings).
    """
    warnings: list[str] = []
    out: dict[str, Any] = {}

    # ─── meta ────────────────────────────────────────────────────────────
    name = frontmatter.get("name") or source_path.stem
    slug = re.sub(r"[^a-z0-9_-]+", "-", str(name).lower()).strip("-") or "imported"
    out["meta"] = {
        "name":             str(name),
        "slug":             slug,
        "version":          "1.0.0",
        "owner_repo":       "imported",
        "owner_path":       str(source_path),
        "canonical_source": str(source_path),
        "ownership_rule":   f"Imported from design.md ({source_path.name}); "
                            f"hand-augment with muriel-specific fields as needed.",
    }

    # ─── colors ──────────────────────────────────────────────────────────
    colors_in = frontmatter.get("colors") or {}
    if not isinstance(colors_in, dict):
        warnings.append(f"colors block is not a map; got {type(colors_in).__name__}; skipping")
        colors_in = {}

    colors_out: dict[str, Any] = {}
    aliases: dict[str, str] = {}
    named: dict[str, str] = {}

    for stitch_key, value in colors_in.items():
        if not isinstance(value, str):
            warnings.append(f"colors.{stitch_key} is not a string ({value!r}); skipping")
            continue
        muriel_key = STITCH_COLOR_TO_MURIEL.get(stitch_key)
        if muriel_key:
            colors_out[muriel_key] = value
        else:
            named[stitch_key] = value
            # Also expose as an alias by the original Stitch role name
            aliases[stitch_key] = value

    # muriel.colors REQUIRES background + foreground; default if missing.
    if "background" not in colors_out:
        colors_out["background"] = "#0a0a0f"
        warnings.append("colors.surface (background) missing in source — defaulted to #0a0a0f")
    if "foreground" not in colors_out:
        colors_out["foreground"] = "#e6e4d2"
        warnings.append("colors.on-surface (foreground) missing in source — defaulted to #e6e4d2")

    if named:
        colors_out["named"] = named
    if aliases:
        colors_out["aliases"] = aliases

    out["colors"] = colors_out

    # ─── typography ──────────────────────────────────────────────────────
    type_in = frontmatter.get("typography") or {}
    if not isinstance(type_in, dict):
        warnings.append(f"typography block is not a map; got {type(type_in).__name__}; skipping")
        type_in = {}

    typography_out: dict[str, Any] = {}
    scale_out: dict[str, dict[str, Any]] = {}

    for stitch_role, role_def in type_in.items():
        if not isinstance(role_def, dict):
            warnings.append(f"typography.{stitch_role} is not a map; skipping")
            continue
        muriel_role = STITCH_TYPE_TO_MURIEL.get(stitch_role, stitch_role)
        scale_entry: dict[str, Any] = {}
        size = role_def.get("fontSize") or role_def.get("size")
        if isinstance(size, str):
            # "16px" → 16
            m = re.match(r"^(\d+(?:\.\d+)?)\s*(px)?$", size.strip())
            if m:
                size = float(m.group(1))
                if size.is_integer():
                    size = int(size)
        if isinstance(size, (int, float)):
            scale_entry["size"] = size
        weight = role_def.get("fontWeight") or role_def.get("weight")
        if isinstance(weight, (int, float)):
            scale_entry["weight"] = int(weight)
        line_height = role_def.get("lineHeight") or role_def.get("line_height")
        if isinstance(line_height, (int, float)):
            scale_entry["line_height"] = float(line_height)
        if scale_entry:
            scale_out[muriel_role] = scale_entry

        # Surface body / mono / display family at the typography top level
        family = role_def.get("fontFamily") or role_def.get("family")
        if isinstance(family, str):
            if muriel_role == "body":
                typography_out["body_family"] = family
            elif muriel_role == "mono":
                typography_out["mono_family"] = family
            elif muriel_role in ("h1", "display"):
                typography_out["display_family"] = family
                if isinstance(weight, (int, float)):
                    typography_out["display_weight"] = int(weight)
                if isinstance(line_height, (int, float)):
                    typography_out["display_line_height"] = float(line_height)

    if scale_out:
        typography_out["scale"] = scale_out
    if typography_out:
        out["typography"] = typography_out

    # ─── radii ───────────────────────────────────────────────────────────
    rounded_in = frontmatter.get("rounded") or frontmatter.get("radii") or {}
    if isinstance(rounded_in, dict):
        radii_out: dict[str, Any] = {}
        for key, value in rounded_in.items():
            if isinstance(value, str):
                m = re.match(r"^(\d+(?:\.\d+)?)\s*(px)?$", value.strip())
                if m:
                    radii_out[key] = int(float(m.group(1)))
                    continue
            if isinstance(value, (int, float)):
                radii_out[key] = int(value)
        if radii_out:
            out["radii"] = radii_out

    # ─── elevation ───────────────────────────────────────────────────────
    elevation_in = frontmatter.get("elevation") or {}
    if isinstance(elevation_in, dict) and elevation_in:
        # Stitch's elevation isn't formalized — preserve as-is for muriel to
        # interpret per channel.
        out["elevation"] = {
            k: v for k, v in elevation_in.items()
            if isinstance(v, (str, int, float, dict))
        }

    # ─── motion ──────────────────────────────────────────────────────────
    motion_in = frontmatter.get("motion") or {}
    if isinstance(motion_in, dict) and motion_in:
        # Pass through string durations/easing curves; muriel.Motion has its
        # own defaults — these become an override block in the brand.toml.
        out["motion"] = {k: str(v) for k, v in motion_in.items() if v is not None}

    # ─── a11y / contrast policy ──────────────────────────────────────────
    contrast_in = frontmatter.get("contrast") or {}
    imported_min = None
    if isinstance(contrast_in, dict):
        imported_min = contrast_in.get("minimum") or contrast_in.get("min_contrast")
    if isinstance(imported_min, (int, float)) and imported_min < MURIEL_MIN_CONTRAST:
        warnings.append(
            f"imported contrast.minimum is {imported_min} — below muriel's 8.0 floor. "
            f"Imported preference recorded; muriel will still validate against 8.0."
        )

    a11y: dict[str, Any] = {
        "min_contrast_ratio": MURIEL_MIN_CONTRAST,
    }
    if imported_min is not None and isinstance(imported_min, (int, float)):
        a11y["imported_min_contrast_ratio"] = float(imported_min)
    out["a11y"] = a11y

    # ─── rules (Do's and Don'ts) ─────────────────────────────────────────
    rules_text = None
    for title, content in prose.items():
        norm = title.lower().replace("'", "").replace("'", "")
        if "do" in norm and "dont" in norm:
            rules_text = content
            break
        if norm in ("rules", "guidelines"):
            rules_text = content
            break
    if rules_text:
        out["rules"] = {
            "imported_dos_donts": rules_text,
        }

    # ─── components (preserved as prose) ──────────────────────────────────
    components_text = prose.get("Components") or prose.get("components")
    if components_text:
        out.setdefault("rules", {})["imported_components"] = components_text

    return out, warnings


# ─── TOML emission (zero-dep) ─────────────────────────────────────────────


def _toml_escape_string(s: str) -> str:
    """Escape a string for TOML basic string output (single-line, double-quoted)."""
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return f'"{s}"'


def _toml_emit_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if v is None:
        # TOML has no null — skip at the caller. Defensive return.
        return '""'
    if isinstance(v, str):
        if "\n" in v:
            # Use a triple-quoted basic string (multi-line) for prose blocks
            escaped = v.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
            return f'"""\n{escaped}\n"""'
        return _toml_escape_string(v)
    if isinstance(v, list):
        parts = [_toml_emit_value(x) for x in v]
        return "[" + ", ".join(parts) + "]"
    raise TypeError(f"unsupported TOML value type: {type(v).__name__}")


def _is_inline_table(d: dict) -> bool:
    """Decide whether a dict should emit as an inline { } table or its own [section]."""
    if not d:
        return True
    # If any value is itself a dict, it has to be a section (TOML rules)
    for v in d.values():
        if isinstance(v, dict):
            return False
    # Short flat dicts → inline; long ones → section
    return len(d) <= 4 and all(isinstance(v, (str, int, float, bool)) for v in d.values())


def _emit_toml(data: dict[str, Any]) -> str:
    """Emit a brand.toml string from a nested dict. Subset of TOML — strings,
    numbers, booleans, lists of those, nested tables. No arrays-of-tables."""
    lines: list[str] = []
    lines.append(
        "# Generated by `muriel import` from a design.md source.\n"
        "# Hand-augment with muriel-specific fields (semantic states, viz palette,\n"
        "# logo lockups, ring gradients, voice) as needed for richer composites.\n"
    )

    def emit_section(prefix: str, body: dict[str, Any]) -> None:
        # Emit non-dict scalars first
        scalars = {k: v for k, v in body.items() if not isinstance(v, dict)}
        sub_dicts = {k: v for k, v in body.items() if isinstance(v, dict)}
        if prefix:
            lines.append(f"\n[{prefix}]")
        for k, v in scalars.items():
            if v is None:
                continue
            lines.append(f"{k} = {_toml_emit_value(v)}")
        for k, sub in sub_dicts.items():
            sub_prefix = f"{prefix}.{k}" if prefix else k
            emit_section(sub_prefix, sub)

    # Top-level scalars
    top_scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    for k, v in top_scalars.items():
        if v is not None:
            lines.append(f"{k} = {_toml_emit_value(v)}")
    # Top-level sections
    for k, v in data.items():
        if isinstance(v, dict):
            emit_section(k, v)

    return "\n".join(lines).rstrip() + "\n"


# ─── Public API ───────────────────────────────────────────────────────────


def import_design_md(input_path: Path, output_path: Optional[Path] = None) -> tuple[Path, list[str]]:
    """
    Read a design.md file, translate to a muriel brand.toml, write to
    ``output_path`` (default: ./brand.toml). Returns (output_path, warnings).
    """
    text = input_path.read_text()
    fm_text, body = _split_frontmatter(text)
    if not fm_text:
        raise ValueError(
            f"{input_path}: no YAML frontmatter found between --- markers; "
            "design.md import requires the Stitch frontmatter shape."
        )
    frontmatter = _parse_yaml_frontmatter(fm_text)
    prose = _parse_prose_sections(body)
    toml_dict, warnings = _stitch_to_muriel_dict(frontmatter, prose, input_path)

    output = output_path or Path("brand.toml")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_emit_toml(toml_dict))
    return output, warnings


# ─── CLI ──────────────────────────────────────────────────────────────────


def _print_help() -> None:
    print(
        "muriel import — convert a Google Stitch design.md into a muriel brand.toml\n"
        "\n"
        "Usage:\n"
        "  muriel import <design.md> [--out <brand.toml>]\n"
        "\n"
        "Options:\n"
        "  --out PATH   Output brand.toml path (default: ./brand.toml)\n"
        "  -h, --help   Show this message\n"
        "\n"
        "Lossy: design.md's flat schema can't express muriel's semantic states,\n"
        "ring gradients, viz palettes, or typed iconography. Those stay absent\n"
        "after import; hand-augment as needed. WARNs print to stderr when the\n"
        "imported spec specifies below muriel's universal 8:1 contrast floor.\n"
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
                print("muriel import: --out requires a path", file=sys.stderr)
                return 2
            output_path = Path(args[i + 1])
            i += 2
            continue
        if a.startswith("-"):
            print(f"muriel import: unknown flag {a!r}", file=sys.stderr)
            return 2
        if input_path is None:
            input_path = Path(a)
            i += 1
            continue
        print(f"muriel import: unexpected positional argument {a!r}", file=sys.stderr)
        return 2

    if input_path is None:
        print("muriel import: input path required", file=sys.stderr)
        _print_help()
        return 2
    if not input_path.exists():
        print(f"muriel import: {input_path} does not exist", file=sys.stderr)
        return 2

    try:
        out, warnings = import_design_md(input_path, output_path)
    except (ValueError, OSError) as exc:
        print(f"muriel import: {exc}", file=sys.stderr)
        return 1

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
