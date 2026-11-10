"""
Tests for muriel.rasterize — SVG to PNG with an ImageMagick fallback.

The module makes three claims, each tested here:

  * The backend order holds. cairosvg wins where it imports; an install
    that raises OSError at import (no Cairo library, the Windows case) is
    unavailable rather than fatal; ImageMagick is next; nothing usable is
    a clear error, not a traceback.
  * Font stacks resolve the way a browser resolves them. librsvg takes
    only the first family, so the pinned SVG must name the first
    installed one, with the CSS-only keywords muriel's generators lead
    with expanded to real faces.
  * Intermediate weights survive. With named faces on, 600 on Segoe UI
    becomes the Semibold face at weight 400, every declaring element is
    explicit so descendants inherit the right face, and pinning stands
    down where its cascade cannot see (a <style> sheet, a one-face
    family).

Pinning is pure and tested against a fixture font list, so it runs on
any OS. The render tests need ImageMagick 7 and skip cleanly without it.
Standard library only (unittest, no pytest dependency).
"""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from muriel import rasterize as rz
from muriel.rasterize import (
    Face,
    RasterizeUnavailable,
    face_family,
    match_weight,
    parse_font_list,
    pin_fonts,
    rasterize,
    resolve_stack,
    split_stack,
)


def _block(name: str, family: str, weight: int, style: str = "Normal") -> str:
    return (f"  Font: {name}\n    family: {family}\n    style: {style}\n"
            f"    stretch: Normal\n    weight: {weight}\n    metrics: not defined\n"
            f"    glyphs: c:\\windows\\fonts\\{name.lower()}.ttf\n    index: 0\n")


FONT_LIST = "Path: Windows Fonts\n" + "".join([
    _block("Arial", "Arial", 400),
    _block("Arial-Bold", "Arial", 700),
    _block("Arial-Black", "Arial", 900),
    _block("Consolas", "Consolas", 400),
    _block("Consolas-Bold", "Consolas", 700),
    _block("Consolas-Italic", "Consolas", 400, "Italic"),
    _block("Segoe-UI", "Segoe UI", 400),
    _block("Segoe-UI-Light", "Segoe UI", 300),
    _block("Segoe-UI-Semibold", "Segoe UI", 600),
    _block("Segoe-UI-Bold", "Segoe UI", 700),
    _block("Segoe-UI-Black", "Segoe UI", 900),
    _block("Segoe-UI-Italic", "Segoe UI", 400, "Italic"),
    _block("Segoe-UI-Semibold-Italic", "Segoe UI", 600, "Italic"),
    _block("Segoe-UI-Bold-Italic", "Segoe UI", 700, "Italic"),
    _block("Segoe-UI-Variable", "Segoe UI Variable", 400),
])
CATALOG = parse_font_list(FONT_LIST)

SVG_NS = "http://www.w3.org/2000/svg"
MURIEL_STACK = "ui-sans-serif, -apple-system, system-ui, sans-serif"
MONO_STACK = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def _svg(body: str, root_attrs: str = f'font-family="{MURIEL_STACK}"') -> str:
    return (f'<svg xmlns="{SVG_NS}" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="200" height="100" viewBox="0 0 200 100" {root_attrs}>{body}</svg>')


def _style(el: ET.Element) -> dict[str, str]:
    return rz._style_decls(el.get("style"))


def _texts(svg_text: str) -> list[ET.Element]:
    return ET.fromstring(svg_text).findall(f".//{{{SVG_NS}}}text")


class ParseFontListTests(unittest.TestCase):
    def test_faces_group_by_family(self):
        self.assertEqual(sorted(CATALOG), ["arial", "consolas", "segoe ui",
                                           "segoe ui variable"])
        weights = sorted(f.weight for f in CATALOG["segoe ui"] if not f.italic)
        self.assertEqual(weights, [300, 400, 600, 700, 900])

    def test_italic_and_name_are_read(self):
        face = next(f for f in CATALOG["segoe ui"] if f.italic and f.weight == 600)
        self.assertEqual(face.name, "Segoe-UI-Semibold-Italic")

    def test_glyph_path_colon_does_not_split_a_block(self):
        self.assertEqual(len(CATALOG["arial"]), 3)

    def test_empty_listing(self):
        self.assertEqual(parse_font_list(""), {})


class ResolveStackTests(unittest.TestCase):
    def test_split_strips_quotes(self):
        self.assertEqual(split_stack("'Inter', \"Segoe UI\" , sans-serif"),
                         ["Inter", "Segoe UI", "sans-serif"])

    def test_muriel_stack_lands_on_the_system_ui_face(self):
        self.assertEqual(resolve_stack(MURIEL_STACK, CATALOG), "Segoe UI")

    def test_monospace_stack_skips_missing_families(self):
        self.assertEqual(resolve_stack(MONO_STACK, CATALOG), "Consolas")

    def test_walks_past_a_missing_first_family(self):
        self.assertEqual(resolve_stack("'Inter', Arial, sans-serif", CATALOG), "Arial")

    def test_case_insensitive(self):
        self.assertEqual(resolve_stack("segoe ui", CATALOG), "Segoe UI")

    def test_nothing_installed_and_no_generic_is_none(self):
        self.assertIsNone(resolve_stack("Inter, Roboto", CATALOG))

    def test_generic_with_no_candidate_falls_to_fontconfig_generic(self):
        only_variable = {"segoe ui variable": CATALOG["segoe ui variable"]}
        self.assertEqual(resolve_stack("Inter, system-ui", only_variable), "sans-serif")


class MatchWeightTests(unittest.TestCase):
    """CSS Fonts 4 §5.2: the weight-matching branches."""

    def test_exact(self):
        self.assertEqual(match_weight(600, [400, 600, 700]), 600)

    def test_above_500_prefers_heavier(self):
        self.assertEqual(match_weight(600, [400, 700, 900]), 700)
        self.assertEqual(match_weight(650, [400, 600]), 600)

    def test_below_400_prefers_lighter_then_heavier(self):
        self.assertEqual(match_weight(300, [200, 400]), 200)
        self.assertEqual(match_weight(300, [400, 700]), 400)

    def test_400_to_500_tries_up_to_500_then_lighter(self):
        self.assertEqual(match_weight(450, [400, 500]), 500)
        self.assertEqual(match_weight(500, [300, 400, 600, 700]), 400)
        self.assertEqual(match_weight(450, [600, 700]), 600)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            match_weight(400, [])


class FaceFamilyTests(unittest.TestCase):
    def test_named_faces(self):
        self.assertEqual(face_family(Face("Segoe-UI-Semibold", "Segoe UI", 600, False)),
                         "Segoe UI Semibold")
        self.assertEqual(face_family(Face("Segoe-UI-Semibold-Italic", "Segoe UI", 600, True)),
                         "Segoe UI Semibold")
        self.assertEqual(face_family(Face("Arial-Black", "Arial", 900, False)), "Arial Black")

    def test_ribbi_faces_answer_to_the_family(self):
        self.assertIsNone(face_family(Face("Segoe-UI", "Segoe UI", 400, False)))
        self.assertIsNone(face_family(Face("Segoe-UI-Bold-Italic", "Segoe UI", 700, True)))

    def test_name_that_does_not_extend_the_family(self):
        self.assertIsNone(face_family(Face("SegoeUI-Semibold", "Segoe UI", 600, False)))


class PinFontsTests(unittest.TestCase):
    def pin(self, svg_text: str, named_faces: bool = True):
        return pin_fonts(svg_text, CATALOG, named_faces=named_faces)

    def test_muriel_label_weights_get_their_faces(self):
        out, report = self.pin(_svg(
            '<text font-weight="600">Title</text>'
            '<text font-weight="700">Focal</text>'
            f'<text font-family="{MONO_STACK}" font-size="11">38.0</text>'))
        title, focal, mono = _texts(out)
        self.assertEqual(_style(title), {"font-family": "'Segoe UI Semibold'",
                                         "font-weight": "400"})
        self.assertEqual(_style(focal), {"font-family": "'Segoe UI'", "font-weight": "700"})
        self.assertEqual(_style(mono)["font-family"], "'Consolas'")
        self.assertIsNone(title.get("font-weight"))
        rows = {(r["from"], r["to"]) for r in report.to_list()}
        self.assertIn((MURIEL_STACK, "Segoe UI"), rows)
        self.assertIn(("Segoe UI @600", "Segoe UI Semibold"), rows)

    def test_without_named_faces_only_stacks_change(self):
        out, report = self.pin(_svg('<text font-weight="600">Title</text>'),
                               named_faces=False)
        root = ET.fromstring(out)
        self.assertEqual(root.get("font-family"), "Segoe UI")
        self.assertEqual(_texts(out)[0].get("font-weight"), "600")
        self.assertFalse(report.faces)

    def test_descendant_does_not_inherit_a_pinned_face_it_did_not_ask_for(self):
        out, _ = self.pin(_svg(
            '<g font-weight="600"><text font-weight="400">Body</text>'
            '<text>Inherits</text></g>'))
        root = ET.fromstring(out)
        group = root.find(f"{{{SVG_NS}}}g")
        body, inherits = _texts(out)
        self.assertEqual(_style(group)["font-family"], "'Segoe UI Semibold'")
        self.assertEqual(_style(body), {"font-family": "'Segoe UI'", "font-weight": "400"})
        self.assertEqual(_style(inherits), {})

    def test_italic_picks_from_italic_faces(self):
        out, _ = self.pin(_svg('<text font-style="italic" font-weight="600">Aside</text>'))
        text = _texts(out)[0]
        self.assertEqual(_style(text)["font-family"], "'Segoe UI Semibold'")
        self.assertEqual(text.get("font-style"), "italic")

    def test_weight_with_no_matching_face_rounds_like_css(self):
        out, report = self.pin(_svg('<text font-family="Arial" font-weight="600">A</text>'))
        self.assertEqual(_style(_texts(out)[0]),
                         {"font-family": "'Arial'", "font-weight": "700"})
        self.assertFalse(report.faces)

    def test_single_face_family_keeps_its_authored_weight(self):
        out, report = self.pin(_svg(
            '<text font-family="Segoe UI Variable" font-weight="600">A</text>'))
        self.assertEqual(_style(_texts(out)[0]),
                         {"font-family": "'Segoe UI Variable'", "font-weight": "600"})
        self.assertFalse(report.faces)

    def test_already_installed_family_is_returned_untouched(self):
        src = _svg('<text font-weight="600">A</text>', root_attrs='font-family="Arial"')
        out, report = self.pin(src)
        self.assertEqual(out, src)
        self.assertFalse(report.changed)

    def test_style_sheet_resolves_stacks_but_skips_weights(self):
        out, report = self.pin(_svg(
            f"<style>.t {{ font-family: {MURIEL_STACK}; font-weight: 600 }}</style>"
            '<text class="t" font-weight="600">A</text>', root_attrs=""))
        style = ET.fromstring(out).find(f"{{{SVG_NS}}}style")
        self.assertIn("font-family: 'Segoe UI';", style.text)
        self.assertEqual(_texts(out)[0].get("font-weight"), "600")
        self.assertTrue(any("<style> sheet" in n for n in report.notes))

    def test_inline_style_stack_is_resolved_in_place(self):
        out, _ = self.pin(_svg(f'<text style="font-family: {MURIEL_STACK}; fill: red">A</text>',
                               root_attrs=""), named_faces=False)
        self.assertEqual(_style(_texts(out)[0]),
                         {"font-family": "'Segoe UI'", "fill": "red"})

    def test_unresolvable_stack_is_left_as_authored(self):
        out, _ = self.pin(_svg('<text font-weight="600">A</text>',
                               root_attrs='font-family="Inter, Roboto"'))
        self.assertEqual(ET.fromstring(out).get("font-family"), "Inter, Roboto")

    def test_namespaces_survive(self):
        out, _ = self.pin(_svg('<use xlink:href="#a"/><text>A</text>'))
        self.assertIn("xlink:href", out)
        self.assertNotIn("ns0", out)

    def test_no_fonts_declared_returns_input_unchanged(self):
        src = _svg("<rect width='5' height='5'/>", root_attrs="")
        out, report = self.pin(src)
        self.assertEqual(out, src)
        self.assertFalse(report.changed)

    def test_empty_catalog_and_bad_svg_are_noted_not_raised(self):
        src = _svg("<text>A</text>")
        out, report = pin_fonts(src, {}, named_faces=True)
        self.assertEqual(out, src)
        self.assertTrue(report.notes)
        out, report = self.pin("<svg><text>unclosed</svg>")
        self.assertEqual(out, "<svg><text>unclosed</svg>")
        self.assertTrue(any("did not parse" in n for n in report.notes))


class BackendOrderTests(unittest.TestCase):
    def test_no_backend_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            svg = Path(tmp) / "a.svg"
            svg.write_text(_svg("<text>A</text>"), encoding="utf-8")
            with mock.patch.object(rz, "_load_cairosvg", return_value=(None, "no cairo")), \
                 mock.patch.object(rz.shutil, "which", return_value=None):
                with self.assertRaises(RasterizeUnavailable) as ctx:
                    rasterize(svg, Path(tmp) / "a.png")
                self.assertIn("cairosvg: no cairo", str(ctx.exception))
                self.assertIn("magick", str(ctx.exception))
                with redirect_stderr(io.StringIO()):
                    rc = rz._main([str(svg), "-o", str(Path(tmp) / "a.png")])
                self.assertEqual(rc, 4)

    def test_cairo_import_oserror_counts_as_unavailable(self):
        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "cairosvg":
                raise OSError('no library called "cairo-2" was found\nmore detail')
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=fake_import):
            module, reason = rz._load_cairosvg()
        self.assertIsNone(module)
        self.assertIn("Cairo library is missing", reason)
        self.assertNotIn("more detail", reason)

    def test_missing_file_exits_3(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(rz._main(["does-not-exist.svg", "-o", "x.png"]), 3)

    def test_registered_with_the_dispatcher(self):
        from muriel.__main__ import SUBCOMMANDS
        self.assertEqual(SUBCOMMANDS["rasterize"][0], "muriel.rasterize")


@unittest.skipUnless(shutil.which("magick"), "ImageMagick 7 (magick) not on PATH")
class MagickRenderTests(unittest.TestCase):
    def render(self, body: str, scale: float = 2.0, **kwargs):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        src = Path(tmp.name) / "fig.svg"
        src.write_text(_svg(body), encoding="utf-8")
        return src, rasterize(src, Path(tmp.name) / "out" / "fig.png", scale=scale,
                              backend="magick", **kwargs)

    def test_scale_sets_pixel_size(self):
        _, result = self.render("<text x='4' y='40'>A</text>", scale=2)
        self.assertEqual(result.backend, "magick")
        self.assertEqual(result.size, (400, 200))

    def test_pinned_render_leaves_no_temp_file(self):
        src, result = self.render("<text x='4' y='40' font-weight='600'>A</text>")
        self.assertTrue(result.fonts)
        self.assertEqual([p.name for p in src.parent.iterdir() if p.name.startswith(".")], [])

    def test_image_elements_are_flagged_and_the_side_copy_is_cleaned_up(self):
        # A relative href puts the pinned copy beside the source; it must
        # not outlive the render, and the image limitation must be named.
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder = Path(tmp.name)
        (folder / "dot.svg").write_text(
            f'<svg xmlns="{SVG_NS}" width="10" height="10"><rect width="10" height="10"/></svg>',
            encoding="utf-8")
        src = folder / "fig.svg"
        src.write_text(_svg('<image href="dot.svg" width="200" height="100"/>'
                            "<text x='4' y='40'>A</text>"), encoding="utf-8")
        result = rasterize(src, folder / "fig.png", scale=1, backend="magick")
        self.assertTrue(result.fonts)
        self.assertEqual(sorted(p.name for p in folder.iterdir()),
                         ["dot.svg", "fig.png", "fig.svg"])
        self.assertTrue(any("<image>" in n and "muriel capture" in n for n in result.notes))

    def test_empty_canvas_stays_transparent_like_cairosvg(self):
        _, result = self.render("<rect width='10' height='10' fill='#123456'/>", scale=1)
        alpha = subprocess.run(
            [shutil.which("magick"), str(result.output), "-format", "%[fx:p{150,80}.a]", "info:"],
            capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(alpha, "0")


if __name__ == "__main__":
    unittest.main()
