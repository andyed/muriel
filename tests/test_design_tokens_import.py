"""
Tests for muriel.design_tokens_import — the DTCG / open-codesign tokens.json
→ brand.toml importer. Standard library only (unittest, no pytest).

Covers: alias resolution, ATV-shape colour tiering, semantic-state mapping,
component-layer exclusion, the 8:1 contrast re-gate WARNs, motion/spacing/
typography mining, required-field defaults, and a DTCG round-trip.
"""

from __future__ import annotations

import json
import unittest

from muriel.design_tokens_import import (
    parse_design_tokens,
    tokens_to_brand,
    _color_role_for,
    _resolve_aliases,
)


# ─── Fixtures ───────────────────────────────────────────────────────────

# Minimal open-codesign / ATV tokens.json: primitive → semantic → component,
# with {alias} references. Mirrors the vaultline example's shape.
ATV_TOKENS = {
    "name": "test-brand",
    "description": "A fixture brand.",
    "schemaVersion": 1,
    "primitive": {
        "color": {
            "ink900": "#0b0b0f",      # near-black — good fg on light
            "paper0": "#ffffff",
            "stone100": "#f0ece2",
            "stone200": "#ded6c4",
            "slate500": "#5b6166",
            "brass500": "#7a5a1e",    # dark brass — clears 8:1 on white
            "mint400": "#9fe6bd",     # light mint — fails 8:1 on white
        },
        "space": {"1": 4, "2": 8, "4": 16},
        "radius": {"card": 28, "round": 999},
        "motion": {
            "fastMs": 160,
            "panelMs": 360,
            "easeStandard": "cubic-bezier(.2,.8,.2,1)",
        },
        "font": {
            "display": "Fraunces, serif",
            "ui": "Inter, sans-serif",
            "data": "IBM Plex Mono, monospace",
        },
    },
    "semantic": {
        "color": {
            "bgApp": "{primitive.color.stone100}",
            "bgSurface": "{primitive.color.paper0}",
            "bgSurfaceMuted": "{primitive.color.stone200}",
            "textPrimary": "{primitive.color.ink900}",
            "textSecondary": "{primitive.color.slate500}",
            "accentValue": "{primitive.color.brass500}",
            "stateSecure": "{primitive.color.mint400}",
            "stateDanger": "{primitive.color.brass500}",
        },
        "typography": {
            "heading": "{primitive.font.display}",
            "body": "{primitive.font.ui}",
        },
    },
    "component": {
        "card": {
            "background": "{semantic.color.bgSurface}",
            "radius": "{primitive.radius.card}",
        },
    },
}


class AliasResolution(unittest.TestCase):
    def test_resolves_chained_refs(self):
        flat = {
            "a.x": "#123456",
            "b.y": "{a.x}",
            "c.z": "{b.y}",
        }
        resolved, warns = _resolve_aliases(flat)
        self.assertEqual(resolved["c.z"], "#123456")
        self.assertEqual(warns, [])

    def test_dangling_ref_warns_and_keeps_literal(self):
        resolved, warns = _resolve_aliases({"a": "{nope.gone}"})
        self.assertEqual(resolved["a"], "{nope.gone}")
        self.assertTrue(any("no target" in w for w in warns))

    def test_cycle_does_not_hang(self):
        resolved, warns = _resolve_aliases({"a": "{b}", "b": "{a}"})
        self.assertTrue(any("cycle" in w for w in warns))


class ColorRoleMapping(unittest.TestCase):
    def test_most_specific_wins(self):
        # textPrimary must beat the generic text→foreground rule.
        self.assertEqual(_color_role_for("semantic.color.textPrimary"), "foreground")
        self.assertEqual(_color_role_for("semantic.color.textSecondary"), "foreground_muted")
        self.assertEqual(_color_role_for("semantic.color.textMuted"), "foreground_muted")

    def test_surface_tiers(self):
        self.assertEqual(_color_role_for("semantic.color.bgApp"), "background")
        self.assertEqual(_color_role_for("semantic.color.bgSurface"), "background_2")
        self.assertEqual(_color_role_for("semantic.color.bgSurfaceMuted"), "background_3")

    def test_accent_variants(self):
        self.assertEqual(_color_role_for("semantic.color.accentValue"), "accent")
        self.assertEqual(_color_role_for("color.accentInk"), "accent_ink")


class ATVImport(unittest.TestCase):
    def setUp(self):
        self.brand, self.warns = tokens_to_brand(ATV_TOKENS)

    def test_color_tiers(self):
        c = self.brand["colors"]
        self.assertEqual(c["background"], "#f0ece2")
        self.assertEqual(c["background_2"], "#ffffff")
        self.assertEqual(c["background_3"], "#ded6c4")
        self.assertEqual(c["foreground"], "#0b0b0f")        # textPrimary, not muted
        self.assertEqual(c["foreground_muted"], "#5b6166")
        self.assertEqual(c["accent"], "#7a5a1e")

    def test_semantic_states_mapped(self):
        sem = self.brand["semantic"]
        self.assertEqual(sem["success"]["text"], "#9fe6bd")  # stateSecure
        self.assertEqual(sem["error"]["text"], "#7a5a1e")    # stateDanger

    def test_component_layer_not_mined(self):
        # The component card.radius must NOT leak into [radii]; only the two
        # primitive radii should be present.
        self.assertEqual(set(self.brand["radii"]), {"card", "round"})
        # And no component colour leaks as a named colour.
        named = self.brand["colors"].get("named", {})
        self.assertNotIn("background", named)
        # The component layer is preserved as prose instead.
        self.assertIn("imported_components", self.brand.get("rules", {}))

    def test_motion_and_spacing(self):
        m = self.brand["motion"]
        self.assertEqual(m["duration_fast"], 160)
        self.assertEqual(m["duration_panel"], 360)
        self.assertEqual(m["easing_standard"], "cubic-bezier(.2,.8,.2,1)")
        self.assertEqual(self.brand["spacing"]["4"], 16)

    def test_typography_families(self):
        t = self.brand["typography"]
        self.assertEqual(t["display_family"], "Fraunces, serif")
        self.assertEqual(t["body_family"], "Inter, sans-serif")
        self.assertEqual(t["mono_family"], "IBM Plex Mono, monospace")

    def test_contrast_regate_warns_below_floor(self):
        # mint400 (#9fe6bd) as success.text on stone100 background fails 8:1.
        self.assertTrue(
            any("success" in w and "8:1" in w for w in self.warns),
            f"expected a sub-8:1 WARN for success.text; got {self.warns}",
        )

    def test_a11y_floor_recorded(self):
        self.assertEqual(self.brand["a11y"]["min_contrast_ratio"], 8.0)


class MissingRequiredFields(unittest.TestCase):
    def test_defaults_background_and_foreground(self):
        brand, warns = tokens_to_brand({"name": "bare", "primitive": {"space": {"1": 4}}})
        self.assertEqual(brand["colors"]["background"], "#0a0a0f")
        self.assertEqual(brand["colors"]["foreground"], "#e6e4d2")
        self.assertTrue(any("background missing" in w for w in warns))
        self.assertTrue(any("foreground missing" in w for w in warns))


class DTCGRoundTrip(unittest.TestCase):
    def test_dtcg_value_type_tokens(self):
        # A minimal W3C DTCG document (the shape muriel export-dtcg emits).
        dtcg = {
            "color": {
                "background": {"$value": "#0a0a0f", "$type": "color"},
                "foreground": {"$value": "#e6e4d2", "$type": "color"},
                "accent": {"$value": "#50b4c8", "$type": "color"},
                "semantic": {
                    "success": {"text": {"$value": "#66bb6a", "$type": "color"}},
                    "error": {"text": {"$value": "#ff8282", "$type": "color"}},
                },
                "aliases": {
                    "text": {"$value": "{color.foreground}", "$type": "color"},
                },
            },
            "spacing": {"md": {"$value": "16px", "$type": "dimension"}},
            "radius": {"lg": {"$value": "16px", "$type": "dimension"}},
            "duration": {"fast": {"$value": "120ms", "$type": "duration"}},
        }
        brand, warns = parse_design_tokens(json.dumps(dtcg))
        c = brand["colors"]
        self.assertEqual(c["background"], "#0a0a0f")
        self.assertEqual(c["foreground"], "#e6e4d2")
        self.assertEqual(c["accent"], "#50b4c8")
        self.assertEqual(brand["semantic"]["success"]["text"], "#66bb6a")
        self.assertEqual(brand["spacing"]["md"], 16)
        self.assertEqual(brand["radii"]["lg"], 16)
        self.assertEqual(brand["motion"]["duration_fast"], 120)
        # muriel's own palette clears 8:1 — no contrast WARN expected.
        self.assertFalse([w for w in warns if "contrast" in w])


if __name__ == "__main__":
    unittest.main()
