"""
muriel.rasterize — SVG to PNG for a visual audit, on whatever renderer the box has.

The critique agent judges a PNG, not SVG source, so every SVG audit starts
with a rasterize step. cairosvg (the ``[critique]`` extra) was the only
path, and on Windows it installs cleanly and then fails at import: it binds
the system Cairo library through cffi, and Windows ships no
``libcairo-2.dll``. ImageMagick's Windows build carries librsvg and Cairo
inside it, so ``magick`` renders SVG with nothing else installed.

Backends, first that works wins:

1. ``cairosvg`` — unchanged wherever it already works. An import that
   raises OSError (installed, no Cairo library) counts as unavailable.
2. ``magick`` — ImageMagick 7's librsvg delegate, with fonts pinned first.

Font pinning
------------

The librsvg that ImageMagick bundles (2.40) hands a whole ``font-family``
value to Pango as one name. It does not walk a CSS stack: ``Inter, Arial,
sans-serif`` with Inter absent falls back to Pango's generic "Sans" with an
"expect ugly output" warning and never reaches Arial, and the CSS-only
keywords muriel's generators lead with (``ui-sans-serif``, ``system-ui``,
``ui-monospace``) match nothing. So before the render every
``font-family`` — attribute, inline style, ``<style>`` sheet — is resolved
to the first family ImageMagick lists as installed, with the keywords
standing for the faces a browser picks (``system-ui`` is Segoe UI on
Windows, ``monospace`` is Consolas).

On Windows a second gap remains: only a family's regular, bold and their
italics answer to the family name, so ``font-weight: 600`` renders Bold and
300 renders Regular. muriel's generators put 500 and 600 on most labels,
so the unpinned render overstates hierarchy. Windows also names those
faces as families of their own ("Segoe UI Semibold"), so every element
that declares a font is rewritten to name the face directly at weight 400,
the face chosen by the CSS weight-matching rule. A family with one listed
face (a variable font) is left to the renderer. Weight pinning is skipped
when a ``<style>`` sheet sets fonts: the cascade here reads attributes and
inline styles only, and an inline pin would override the sheet.

cairosvg also reads only the first family of a stack. Pinning is not
applied on that rung, so output on boxes where cairosvg works is unchanged.

Embedded images do not survive the ImageMagick rung: its librsvg drops
nested-SVG and data-URI ``<image>`` elements and discolors PNG ones. The
result carries a note when the source has any, pointing at ``muriel
capture``, which renders through Chromium.

Usage
-----

::

    python -m muriel.rasterize fig.svg -o fig.png             # 2x by default
    python -m muriel.rasterize fig.svg -o fig.png --scale 1   # CSS pixels
    python -m muriel.rasterize fig.svg -o fig.png --backend magick --json
"""

from __future__ import annotations

import functools
import io
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence


BACKENDS = ("cairosvg", "magick")
DEFAULT_SCALE = 2.0
CSS_PX_PER_INCH = 96

# CSS keyword → the family group a browser resolves it to.
GENERIC_KEYWORDS: dict[str, str] = {
    "system-ui":          "system-ui",
    "-apple-system":      "system-ui",
    "blinkmacsystemfont": "system-ui",
    "ui-sans-serif":      "system-ui",
    "ui-rounded":         "system-ui",
    "sans-serif":         "sans-serif",
    "ui-serif":           "serif",
    "serif":              "serif",
    "ui-monospace":       "monospace",
    "monospace":          "monospace",
}

# Installed-family candidates per group, in the order a browser on each
# platform would land on them. First one ImageMagick lists wins.
GENERIC_CANDIDATES: dict[str, tuple[str, ...]] = {
    "system-ui":  ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Cantarell",
                   "Ubuntu", "Noto Sans", "DejaVu Sans"),
    "sans-serif": ("Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"),
    "serif":      ("Times New Roman", "Times", "Liberation Serif", "DejaVu Serif"),
    "monospace":  ("Consolas", "Cascadia Mono", "Menlo", "SF Mono",
                   "Liberation Mono", "DejaVu Sans Mono", "Courier New"),
}

# When no candidate is installed, the plain generic fontconfig understands.
_FONTCONFIG_GENERIC = {
    "system-ui": "sans-serif", "sans-serif": "sans-serif",
    "serif": "serif", "monospace": "monospace",
}

_CSS_GENERICS = set(GENERIC_KEYWORDS) | {"cursive", "fantasy", "emoji", "math", "fangsong"}
_FONT_PROPS = ("font-family", "font-weight", "font-style")
_SHEET_FAMILY = re.compile(r"(font-family\s*:\s*)([^;{}!]*[^;{}!\s])")
_SHEET_SETS_FONTS = re.compile(r"font(?:-family|-weight)?\s*:")
_RELATIVE_REF = re.compile(
    r"""(?:href\s*=\s*["']|url\(\s*["']?)(?!#|data:|[a-zA-Z][a-zA-Z0-9+.-]*:)""")
_IMAGE_ELEMENT = re.compile(r"<(?:[\w.-]+:)?image\b")


class RasterizeUnavailable(RuntimeError):
    """No rasterizer backend works on this box."""


# --------------------------------------------------------------------------
# Font catalog — what ImageMagick can render
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Face:
    name: str      # ImageMagick font name, e.g. "Segoe-UI-Semibold"
    family: str    # "Segoe UI"
    weight: int    # 100-900
    italic: bool


FontCatalog = dict[str, list[Face]]   # keyed by lower-case family


def parse_font_list(text: str) -> FontCatalog:
    """Parse ``magick -list font`` output into faces grouped by family."""
    catalog: FontCatalog = {}
    current: dict[str, object] = {}

    def flush() -> None:
        family = current.get("family")
        if current.get("name") and family:
            face = Face(str(current["name"]), str(family),
                        int(current.get("weight", 400)),
                        bool(current.get("italic", False)))
            catalog.setdefault(face.family.lower(), []).append(face)

    for line in text.splitlines():
        key, sep, value = line.strip().partition(":")
        if not sep:
            continue
        key, value = key.strip().lower(), value.strip()
        if key == "font":
            flush()
            current = {"name": value}
        elif key == "family":
            current["family"] = value
        elif key == "style":
            current["italic"] = value.lower() in ("italic", "oblique")
        elif key == "weight":
            try:
                current["weight"] = int(value)
            except ValueError:
                pass
    flush()
    return catalog


@functools.lru_cache(maxsize=4)
def installed_faces(magick: str) -> FontCatalog:
    """The fonts ``magick`` can see; empty when the listing fails."""
    try:
        proc = subprocess.run([magick, "-list", "font"], capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return {}
    return parse_font_list(proc.stdout)


# --------------------------------------------------------------------------
# Resolution — stacks to families, weights to faces
# --------------------------------------------------------------------------

def split_stack(value: str) -> list[str]:
    """``"'Inter', system-ui"`` → ``["Inter", "system-ui"]``."""
    return [part.strip().strip("'\"").strip()
            for part in value.split(",") if part.strip().strip("'\"").strip()]


def resolve_stack(value: str, catalog: FontCatalog) -> Optional[str]:
    """First installed family in a CSS stack, keywords expanded.

    None when nothing in the stack resolves and it names no generic; the
    value is then left as authored.
    """
    fallback = None
    for item in split_stack(value):
        group = GENERIC_KEYWORDS.get(item.lower())
        if group is None:
            faces = catalog.get(item.lower())
            if faces:
                return faces[0].family
            continue
        for candidate in GENERIC_CANDIDATES[group]:
            faces = catalog.get(candidate.lower())
            if faces:
                return faces[0].family
        fallback = fallback or _FONTCONFIG_GENERIC[group]
    return fallback


def match_weight(desired: int, available: Sequence[int]) -> int:
    """The weight CSS font matching picks from ``available`` (CSS Fonts 4 §5.2)."""
    weights = sorted(set(available))
    if not weights:
        raise ValueError("no weights to match against")
    if desired in weights:
        return desired
    below = [w for w in reversed(weights) if w < desired]
    above = [w for w in weights if w > desired]
    if 400 <= desired <= 500:
        order = ([w for w in above if w <= 500] + below
                 + [w for w in above if w > 500])
    elif desired < 400:
        order = below + above
    else:
        order = above + below
    return order[0]


def face_family(face: Face) -> Optional[str]:
    """The family name Windows gives a non-RIBBI face ("Segoe UI Semibold").

    Derived from ImageMagick's hyphenated font name; None for regular and
    bold faces, which answer to the family name, and for names that do not
    extend the family.
    """
    prefix = face.family.replace(" ", "-") + "-"
    if not face.name.startswith(prefix):
        return None
    words = [w for w in face.name[len(prefix):].split("-")
             if w and w.lower() not in ("italic", "oblique")]
    if not words or [w.lower() for w in words] in (["regular"], ["bold"]):
        return None
    return f"{face.family} {' '.join(words)}"


def _parse_weight(raw: Optional[str], parent: int) -> Optional[int]:
    if raw is None:
        return None
    value = raw.strip().lower()
    if value == "normal":
        return 400
    if value == "bold":
        return 700
    if value == "bolder":
        return 400 if parent < 350 else 700 if parent < 550 else 900
    if value == "lighter":
        return 100 if parent < 550 else 400 if parent < 750 else 700
    try:
        return max(1, min(1000, int(float(value))))
    except ValueError:
        return None


def _quote(family: str) -> str:
    """CSS-quote one family name; generics and stacks pass through."""
    if "," in family or family[:1] in "'\"" or family.lower() in _CSS_GENERICS:
        return family
    return f"'{family}'"


# --------------------------------------------------------------------------
# Pinning — rewrite the SVG so librsvg gets one installed face per element
# --------------------------------------------------------------------------

@dataclass
class PinReport:
    families: dict[tuple[str, str], int] = field(default_factory=dict)
    faces: dict[tuple[str, str], int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def _count(self, table: dict, key: tuple[str, str]) -> None:
        table[key] = table.get(key, 0) + 1

    @property
    def changed(self) -> bool:
        return bool(self.families or self.faces)

    def to_list(self) -> list[dict]:
        rows = [{"kind": "family", "from": a, "to": b, "count": n}
                for (a, b), n in self.families.items()]
        rows += [{"kind": "face", "from": a, "to": b, "count": n}
                 for (a, b), n in self.faces.items()]
        return rows


def _style_decls(raw: Optional[str]) -> dict[str, str]:
    decls: dict[str, str] = {}
    for part in (raw or "").split(";"):
        name, sep, value = part.partition(":")
        if sep and name.strip():
            decls[name.strip().lower()] = value.strip()
    return decls


def _style_text(decls: dict[str, str]) -> str:
    return ";".join(f"{k}:{v}" for k, v in decls.items())


def _register_namespaces(svg_text: str) -> None:
    """Keep the source's prefixes so ET writes ``xlink:href``, not ``ns0:href``."""
    try:
        for _event, (prefix, uri) in ET.iterparse(io.StringIO(svg_text),
                                                  events=("start-ns",)):
            try:
                ET.register_namespace(prefix, uri)
            except ValueError:
                pass
    except ET.ParseError:
        pass


def pin_fonts(svg_text: str, catalog: FontCatalog, *,
              named_faces: Optional[bool] = None) -> tuple[str, PinReport]:
    """Resolve every font stack, and on Windows every intermediate weight.

    Returns the rewritten SVG text and a report of what changed. The text
    comes back untouched when the catalog is empty, the SVG does not parse,
    or nothing needed pinning.
    """
    report = PinReport()
    if not catalog:
        report.notes.append("font pinning skipped: ImageMagick listed no fonts")
        return svg_text, report
    if named_faces is None:
        named_faces = sys.platform == "win32"

    _register_namespaces(svg_text)
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        report.notes.append(f"font pinning skipped: SVG did not parse ({exc})")
        return svg_text, report

    def resolve(stack: str) -> str:
        resolved = resolve_stack(stack, catalog)
        if resolved is None or split_stack(stack) == [resolved]:
            return stack
        report._count(report.families, (stack.strip(), resolved))
        return resolved

    sheet_sets_fonts = False
    for el in root.iter():
        if isinstance(el.tag, str) and el.tag.rsplit("}", 1)[-1] == "style" and el.text:
            sheet_sets_fonts = sheet_sets_fonts or bool(_SHEET_SETS_FONTS.search(el.text))
            el.text = _SHEET_FAMILY.sub(
                lambda m: m.group(1) + _quote(resolve(m.group(2))), el.text)
    pin_weights = named_faces and not sheet_sets_fonts
    if named_faces and sheet_sets_fonts:
        report.notes.append(
            "weight pinning skipped: a <style> sheet sets fonts, so the cascade "
            "here cannot see every element's weight")

    def walk(el: ET.Element, family: Optional[str], weight: int, italic: bool) -> None:
        decls = _style_decls(el.get("style"))
        raw = {p: decls.get(p, el.get(p)) for p in _FONT_PROPS}
        raw = {p: v for p, v in raw.items()
               if v is not None and v.strip().lower() != "inherit"}

        if "font-family" in raw:
            family = resolve(raw["font-family"])
            if "font-family" in decls:
                decls["font-family"] = _quote(family)
            else:
                el.set("font-family", family)
        parsed = _parse_weight(raw.get("font-weight"), weight)
        if parsed is not None:
            weight = parsed
        if "font-style" in raw:
            italic = raw["font-style"].strip().lower() in ("italic", "oblique")

        if pin_weights and raw and family is not None:
            target, target_weight = family, weight
            faces = [f for f in catalog.get(family.lower(), []) if f.italic == italic]
            if len(faces) >= 2:
                chosen = match_weight(weight, [f.weight for f in faces])
                if chosen in (400, 700):
                    target_weight = chosen
                else:
                    named = face_family(next(f for f in faces if f.weight == chosen))
                    if named:
                        target, target_weight = named, 400
                        report._count(report.faces, (f"{family} @{weight}", named))
            # Explicit on every declaring element, even when unchanged, so a
            # descendant never inherits an ancestor's pinned face in place of
            # the one its own cascade asks for.
            for prop in ("font-family", "font-weight"):
                el.attrib.pop(prop, None)
            decls["font-family"] = _quote(target)
            decls["font-weight"] = str(target_weight)

        if decls and decls != _style_decls(el.get("style")):
            el.set("style", _style_text(decls))
        for child in el:
            walk(child, family, weight, italic)

    walk(root, None, 400, False)
    if not report.changed:
        return svg_text, report
    return ET.tostring(root, encoding="unicode"), report


# --------------------------------------------------------------------------
# Backends
# --------------------------------------------------------------------------

def _load_cairosvg():
    """(module, None) when cairosvg imports, else (None, reason)."""
    try:
        import cairosvg  # type: ignore
    except ImportError:
        return None, "not installed (pip install 'muriel[critique]')"
    except OSError as exc:
        first = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
        return None, f"installed, but the Cairo library is missing: {first}"
    return cairosvg, None


def available_backends() -> dict[str, Optional[str]]:
    """Backend → None when usable, else why not."""
    _, cairo_reason = _load_cairosvg()
    return {
        "cairosvg": cairo_reason,
        "magick": None if shutil.which("magick") else "ImageMagick 7 (magick) not on PATH",
    }


def _png_size(path: Path) -> Optional[tuple[int, int]]:
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
    except OSError:
        return None
    if head[:8] != b"\x89PNG\r\n\x1a\n" or len(head) < 24:
        return None
    return struct.unpack(">II", head[16:24])


@dataclass
class RasterResult:
    source: Path
    output: Path
    backend: str
    scale: float
    size: Optional[tuple[int, int]]
    fonts: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source": str(self.source),
            "output": str(self.output),
            "backend": self.backend,
            "scale": self.scale,
            "width": self.size[0] if self.size else None,
            "height": self.size[1] if self.size else None,
            "fonts": self.fonts,
            "notes": self.notes,
        }


def _render_magick(magick: str, svg: Path, out: Path, scale: float) -> list[str]:
    cmd = [magick, "-background", "none", "-density", f"{CSS_PX_PER_INCH * scale:g}",
           str(svg), str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=300)
    if proc.returncode != 0 or not out.exists() or out.stat().st_size == 0:
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        raise RuntimeError("magick failed: " + (detail[-1] if detail else f"exit {proc.returncode}"))
    misses = [line for line in proc.stderr.splitlines() if "couldn't load font" in line]
    if not misses:
        return []
    first = misses[0].split("couldn't load font", 1)[1].strip()
    return [f"{len(misses)} font fallback(s) in the render, e.g. {first}"]


def rasterize(svg: Path, out: Path, *, scale: float = DEFAULT_SCALE,
              backend: str = "auto", pin: bool = True,
              named_faces: Optional[bool] = None) -> RasterResult:
    """Render ``svg`` to ``out`` with the first backend that works.

    Raises RasterizeUnavailable when the requested backend (or, for
    ``auto``, every backend) is unusable, and RuntimeError when a backend
    runs but fails.
    """
    svg, out = Path(svg), Path(out)
    if scale <= 0:
        raise ValueError(f"scale must be positive, got {scale}")
    if backend not in ("auto",) + BACKENDS:
        raise ValueError(f"unknown backend {backend!r}")
    if not svg.exists():
        raise FileNotFoundError(svg)
    out.parent.mkdir(parents=True, exist_ok=True)

    status = available_backends()
    order = BACKENDS if backend == "auto" else (backend,)
    usable = [b for b in order if status[b] is None]
    if not usable:
        why = "; ".join(f"{b}: {status[b]}" for b in order)
        raise RasterizeUnavailable(f"no SVG rasterizer available ({why})")
    chosen = usable[0]
    notes = [f"{b} skipped: {status[b]}" for b in order[:order.index(chosen)]]

    if chosen == "cairosvg":
        cairosvg, _ = _load_cairosvg()
        cairosvg.svg2png(url=str(svg), write_to=str(out), scale=scale)
        return RasterResult(svg, out, chosen, scale, _png_size(out), notes=notes)

    magick = shutil.which("magick")
    text = svg.read_text(encoding="utf-8", errors="replace")
    images = len(_IMAGE_ELEMENT.findall(text))
    if images:
        notes.append(f"{images} <image> element(s): ImageMagick's librsvg drops or "
                     "discolors embedded images; use muriel capture (Chromium) "
                     "when they matter")
    if not pin:
        notes += _render_magick(magick, svg, out, scale)
        return RasterResult(svg, out, chosen, scale, _png_size(out), notes=notes)

    pinned, report = pin_fonts(text, installed_faces(magick), named_faces=named_faces)
    fonts, notes = report.to_list(), notes + report.notes
    if not report.changed:
        notes += _render_magick(magick, svg, out, scale)
        return RasterResult(svg, out, chosen, scale, _png_size(out), fonts, notes)

    # Relative hrefs resolve against the SVG's own directory, so the pinned
    # copy goes beside the source when it has any; otherwise system temp.
    temp_dir = svg.parent if _RELATIVE_REF.search(text) else None
    try:
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".svg",
                                             prefix=".muriel-raster-", dir=temp_dir,
                                             delete=False)
    except OSError:
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".svg",
                                             prefix=".muriel-raster-", delete=False)
        notes.append("source directory not writable; relative hrefs may not resolve")
    try:
        with handle:
            handle.write(pinned)
        notes += _render_magick(magick, Path(handle.name), out, scale)
    finally:
        Path(handle.name).unlink(missing_ok=True)
    return RasterResult(svg, out, chosen, scale, _png_size(out), fonts, notes)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _print_result(result: RasterResult) -> None:
    print(f"rasterize  {result.source}")
    print(f"  backend  {result.backend}")
    size = f"  {result.size[0]}x{result.size[1]}" if result.size else ""
    print(f"  output   {result.output}{size}  at {result.scale:g}x")
    for i, row in enumerate(result.fonts):
        label = "  fonts    " if i == 0 else "           "
        print(f"{label}{row['from']} -> {row['to']}  (x{row['count']})")
    for note in result.notes:
        print(f"  note     {note}")


def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m muriel.rasterize",
        description=(
            "Rasterize an SVG to PNG for a visual audit: cairosvg where it "
            "works, else ImageMagick with font stacks and weights pinned to "
            "installed faces."
        ),
    )
    parser.add_argument("svg", type=Path, help="Source SVG.")
    parser.add_argument("-o", "--output", type=Path, required=True,
                        help="Output PNG path.")
    parser.add_argument("--scale", type=float, default=DEFAULT_SCALE,
                        help=f"Device scale; 1 = CSS pixels at 96 dpi (default: {DEFAULT_SCALE:g}).")
    parser.add_argument("--backend", choices=("auto",) + BACKENDS, default="auto",
                        help="Force one backend (default: first that works).")
    parser.add_argument("--no-pin-fonts", action="store_true",
                        help="Hand ImageMagick the SVG as authored.")
    parser.add_argument("--json", action="store_true",
                        help="Print the result as JSON instead of a table.")
    args = parser.parse_args(argv)

    if not args.svg.exists():
        print(f"error: file not found: {args.svg}", file=sys.stderr)
        return 3
    try:
        result = rasterize(args.svg, args.output, scale=args.scale,
                           backend=args.backend, pin=not args.no_pin_fonts)
    except RasterizeUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        _print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
