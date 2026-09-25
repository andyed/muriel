"""
Tests for muriel.motion — the duration binary plus the Emil-inspired
property / easing / scale axes, and the figure-motion contract (mode,
flash rate, sequence shape). Standard library only (unittest).

The module ships a thorough ``_selftest``; this wrapper folds it into the
``python -m unittest`` suite and pins the deliberate divergences from the
upstream source (duration binary over bands; 0.96 press scale over 0.97).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from muriel import motion
from muriel.styleguide import Motion, load_styleguide
from muriel.motion import (
    EXEMPTION_REASONS,
    REDUCE_POLICIES,
    REDUCE_POLICY_ALIASES,
    SEQUENCE_MAX_MS,
    STEP_HOLD_MS,
    STEP_TRANSITION_MS,
    normalize_reduce_policy,
    scan_duration_literals,
    untagged_uncanny_literals,
    validate_sequence_timing,
    validate_spring,
    CINEMATIC_MS,
    COMPOSITOR_SAFE_PROPERTIES,
    ENTRANCE_SCALE_FLOOR,
    LAYOUT_TRIGGERING_PROPERTIES,
    PRESS_SCALE,
    UTILITY_MS,
    LOOP_MIN_CYCLE_MS,
    MotionPolicyError,
    MotionPropertyError,
    easing_for,
    is_compositor_safe,
    validate_duration,
    validate_flash_rate,
    validate_mode,
    validate_properties,
    validate_scale,
    validate_sequence_shape,
)


class SelfTest(unittest.TestCase):
    def test_module_selftest_passes(self):
        self.assertEqual(motion._selftest(), 0)


class PropertyAxis(unittest.TestCase):
    def test_safe_and_layout_sets_disjoint(self):
        self.assertFalse(COMPOSITOR_SAFE_PROPERTIES & LAYOUT_TRIGGERING_PROPERTIES)

    def test_compositor_safe(self):
        self.assertTrue(is_compositor_safe("transform"))
        self.assertTrue(is_compositor_safe("-webkit-transform"))
        self.assertFalse(is_compositor_safe("height"))

    def test_layout_property_raises(self):
        with self.assertRaises(MotionPropertyError):
            validate_properties(["transform", "top"])

    def test_unknown_property_passes(self):
        validate_properties("color")  # not assumed unsafe


class EasingAxis(unittest.TestCase):
    def test_directions(self):
        self.assertEqual(easing_for("enter"), "ease-out")
        self.assertEqual(easing_for("exit"), "ease-in")
        self.assertEqual(easing_for("move"), "ease-in-out")

    def test_unknown_direction_raises(self):
        with self.assertRaises(ValueError):
            easing_for("diagonal")


class ScaleAxis(unittest.TestCase):
    def test_floor_and_identity_pass(self):
        validate_scale(ENTRANCE_SCALE_FLOOR)
        validate_scale(1.0)
        validate_scale(PRESS_SCALE, "press")

    def test_below_floor_and_overshoot_raise(self):
        for bad in (0.0, 0.9, 1.1):
            with self.assertRaises(ValueError):
                validate_scale(bad)


class DeliberateDivergences(unittest.TestCase):
    """muriel intentionally departs from the upstream source on two points."""

    def test_press_scale_is_muriels_096_not_097(self):
        self.assertEqual(PRESS_SCALE, 0.96)

    def test_emil_duration_bands_are_uncanny_to_muriel(self):
        # The source recommends 100–500ms bands; muriel's binary forbids them.
        for band_ms in (160, 250, 360, 500):
            with self.assertRaises(motion.MotionPolicyError):
                validate_duration(band_ms)
        # muriel's own buckets still pass.
        validate_duration(UTILITY_MS)
        validate_duration(CINEMATIC_MS)


class ModeContract(unittest.TestCase):
    """none / reveal / step / loop — adapted from diagram-design (MIT)."""

    def test_reveal_autoplays_once(self):
        validate_mode("reveal", autoplay=True, repeats=False, semantic=True)

    def test_reveal_must_not_repeat(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("reveal", autoplay=True, repeats=True, semantic=True)

    def test_step_must_not_autoplay(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("step", autoplay=True, repeats=False, semantic=True)

    def test_step_user_driven_passes(self):
        validate_mode("step", autoplay=False, repeats=False, semantic=True)

    def test_semantic_loop_rejected(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("loop", autoplay=True, repeats=True, semantic=True,
                          cycle_ms=3000)

    def test_loop_cycle_floor(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("loop", autoplay=True, repeats=True, semantic=False,
                          cycle_ms=LOOP_MIN_CYCLE_MS - 1)
        validate_mode("loop", autoplay=True, repeats=True, semantic=False,
                      cycle_ms=LOOP_MIN_CYCLE_MS)

    def test_loop_without_cycle_rejected(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("loop", autoplay=True, repeats=True, semantic=False)

    def test_none_is_inert(self):
        validate_mode("none", autoplay=False, repeats=False, semantic=True)
        with self.assertRaises(MotionPolicyError):
            validate_mode("none", autoplay=True, repeats=False, semantic=True)

    def test_unknown_mode_rejected(self):
        with self.assertRaises(MotionPolicyError):
            validate_mode("carousel", autoplay=False, repeats=False, semantic=False)


class FlashRate(unittest.TestCase):
    """WCAG 2.3.1: at most three flashes per second."""

    def test_three_per_second_passes(self):
        validate_flash_rate(3, 1000)

    def test_four_per_second_fails(self):
        with self.assertRaises(MotionPolicyError):
            validate_flash_rate(4, 1000)

    def test_rate_not_count(self):
        validate_flash_rate(6, 2000)  # 3/s over a 2s window
        with self.assertRaises(MotionPolicyError):
            validate_flash_rate(2, 500)  # 4/s

    def test_bad_window_raises_valueerror(self):
        with self.assertRaises(ValueError):
            validate_flash_rate(1, 0)


class SequenceShape(unittest.TestCase):
    """Structural budgets only: 1–8 steps, ≤2 per step, ≤12 total."""

    def test_within_budget_passes(self):
        validate_sequence_shape(5, [1, 2, 1, 1, 1])

    def test_three_in_one_step_fails(self):
        with self.assertRaises(MotionPolicyError):
            validate_sequence_shape(2, [3, 1])

    def test_thirteen_total_fails(self):
        with self.assertRaises(MotionPolicyError):
            validate_sequence_shape(7, [2, 2, 2, 2, 2, 2, 1])

    def test_twelve_total_passes(self):
        validate_sequence_shape(6, [2, 2, 2, 2, 2, 2])

    def test_step_count_bounds(self):
        for steps in (0, 9):
            with self.assertRaises(MotionPolicyError):
                validate_sequence_shape(steps, [1] * steps)
        validate_sequence_shape(8, [1] * 8)

    def test_mismatched_per_step_raises_valueerror(self):
        with self.assertRaises(ValueError):
            validate_sequence_shape(3, [1, 1])


# ─── Duration scope (owner decision 2026-09-24) ─────────────────────────────

_REPO = Path(__file__).resolve().parent.parent
_COMPOSE = _REPO / "plugins" / "muriel" / "skills" / "compose"
_BRAND_EXAMPLES = (
    _COMPOSE / "examples" / "muriel-brand.toml",
    _COMPOSE / "examples" / "example-brand.toml",
)
_OLD_DEFAULTS = (120, 240, 480, 800)
_DURATION_FIELDS = (
    "duration_instant", "duration_fast", "duration_normal",
    "duration_slow", "duration_reveal",
)

# Known uncanny literals in files this change may not edit. Each entry is
# (relative path, literal) with the reason; the scan still fails on any
# other hit in the same file, and fails if an entry goes stale.
_KNOWN_DEBT = {
    ("channels/diagrams.md", "0.15s"):
        "zoom-button hover transition; owned by the diagrams worktree — migrate to 0.1s",
}


class MotionTokenDefaults(unittest.TestCase):
    def test_old_defaults_gone_from_dataclass(self):
        m = Motion()
        values = {getattr(m, f) for f in _DURATION_FIELDS}
        for old in _OLD_DEFAULTS:
            self.assertNotIn(old, values)

    def test_every_default_passes_validate_duration(self):
        m = Motion()
        for f in _DURATION_FIELDS:
            validate_duration(getattr(m, f))  # kind="transition": the binary

    def test_mapping(self):
        m = Motion()
        self.assertEqual((m.duration_fast, m.duration_normal), (100, 100))
        self.assertEqual((m.duration_slow, m.duration_reveal), (1500, 1500))

    def test_brand_examples_migrated(self):
        for path in _BRAND_EXAMPLES:
            sg = load_styleguide(path)
            for f in _DURATION_FIELDS:
                ms = getattr(sg.motion, f)
                self.assertNotIn(ms, _OLD_DEFAULTS, f"{path.name} {f}")
                validate_duration(ms)

    def test_css_emits_sequence_tokens(self):
        css = load_styleguide(_BRAND_EXAMPLES[0]).to_css_vars(prefix="--mg-")
        self.assertIn("--mg-motion-transition: 100ms;", css)
        self.assertIn("--mg-motion-hold: 1500ms;", css)
        self.assertNotRegex(css, r"duration-\w+: (120|240|480|800)ms")


class DurationKinds(unittest.TestCase):
    def test_transition_is_default_and_binary(self):
        with self.assertRaises(MotionPolicyError):
            validate_duration(300)
        with self.assertRaises(MotionPolicyError):
            validate_duration(300, "transition")

    def test_exempt_kinds_pass_in_the_band(self):
        for kind in ("hold", "spring", "press"):
            validate_duration(300, kind)
            self.assertIn(kind, EXEMPTION_REASONS)

    def test_hold_must_cover_its_transition(self):
        validate_duration(1500, "hold", after_transition_ms=100)
        validate_duration(100, "hold", after_transition_ms=100)
        with self.assertRaises(MotionPolicyError):
            validate_duration(50, "hold", after_transition_ms=100)

    def test_unknown_kind_and_negative(self):
        with self.assertRaises(ValueError):
            validate_duration(100, "stagger")
        with self.assertRaises(ValueError):
            validate_duration(-1, "hold")

    def test_spring_validates_physics(self):
        validate_spring(bounce=0)
        validate_spring(bounce=0, stiffness=300)
        with self.assertRaises(MotionPolicyError):
            validate_spring(bounce=0.1)
        with self.assertRaises(ValueError):
            validate_spring(stiffness=0)


class SequenceTiming(unittest.TestCase):
    def test_constants(self):
        self.assertEqual((STEP_TRANSITION_MS, STEP_HOLD_MS, SEQUENCE_MAX_MS), (100, 1500, 8000))

    def test_five_step_reveal_passes(self):
        self.assertEqual(validate_sequence_timing(5, 100, 1500, "reveal"), 7500)

    def test_six_step_reveal_fails(self):
        with self.assertRaises(MotionPolicyError):
            validate_sequence_timing(6, 100, 1500, "reveal")

    def test_six_step_user_driven_passes(self):
        self.assertIsNone(validate_sequence_timing(6, 100, 1500, "step"))

    def test_uncanny_transition_fails(self):
        with self.assertRaises(MotionPolicyError):
            validate_sequence_timing(3, 480, 1500)

    def test_hold_shorter_than_transition_fails(self):
        with self.assertRaises(MotionPolicyError):
            validate_sequence_timing(3, 100, 50)

    def test_bad_mode_and_steps(self):
        with self.assertRaises(ValueError):
            validate_sequence_timing(3, 100, 1500, "loop")
        with self.assertRaises(ValueError):
            validate_sequence_timing(0, 100, 1500)


class ReducePolicyVocabulary(unittest.TestCase):
    def test_code_vocabulary(self):
        self.assertEqual(set(REDUCE_POLICIES), {"collapse-to-zero", "keep-fast", "keep-linear"})

    def test_reduce_alias(self):
        self.assertEqual(normalize_reduce_policy("reduce"), "keep-fast")
        self.assertEqual(normalize_reduce_policy("Keep-Linear"), "keep-linear")
        with self.assertRaises(ValueError):
            normalize_reduce_policy("freeze")

    def test_polish_rules_names_every_policy(self):
        text = (_COMPOSE / "references" / "polish-rules.md").read_text()
        for name in (*REDUCE_POLICIES, *REDUCE_POLICY_ALIASES):
            self.assertIn(f"`{name}`", text)


class UncannyDocScan(unittest.TestCase):
    """Fail-closed: every compose doc duration in 101–1499 ms is tagged exempt."""

    PLANTED = (
        "Stagger at 120ms between groups.\n"                       # untagged ms
        "transition: opacity 0.25s ease;\n"                        # untagged s
        "Use `{ duration: 0.4 }` here.\n"                          # bare seconds
        "duration_slow = 480\n"                                    # TOML ms
        "Gaps of 80–200ms.\n"                                      # range end
        "press lands in 150ms <!-- motion-exempt: press -->\n"     # tagged: ok
        "wrong tag 300ms <!-- motion-exempt: stagger -->\n"        # bad tag
        "<!-- motion-exempt: not-motion -->\n"
        "```\nRT fell from 842 ms to 671 ms\n```\n"                # block tag: ok
        "Utility 100ms, cinematic 1500ms.\n"                       # ends: ok
    )

    def _docs(self):
        files = sorted([*_COMPOSE.rglob("*.md"), *_COMPOSE.rglob("*.toml")])
        return [(p.relative_to(_COMPOSE).as_posix(), p.read_text()) for p in files]

    def test_planted_fixture_trips(self):
        hits = untagged_uncanny_literals(self.PLANTED)
        self.assertEqual(
            [lit for _, lit, _ in hits],
            ["120ms", "0.25s", "duration: 0.4", "duration_slow = 480", "200ms", "300ms"],
        )

    def test_scanner_is_not_blind(self):
        docs = self._docs()
        self.assertGreater(len(docs), 20, "compose doc glob found too few files")
        total = sum(len(scan_duration_literals(t)) for _, t in docs)
        self.assertGreater(total, 30, "scanner found almost no duration literals")

    def test_compose_docs_have_no_untagged_uncanny_durations(self):
        seen_debt = set()
        offenders = []
        for rel, text in self._docs():
            for line_no, lit, ms in untagged_uncanny_literals(text):
                if (rel, lit) in _KNOWN_DEBT:
                    seen_debt.add((rel, lit))
                    continue
                offenders.append(f"{rel}:{line_no}: {lit} ({ms:g} ms)")
        self.assertEqual(offenders, [], "untagged uncanny-band durations:\n" + "\n".join(offenders))
        stale = set(_KNOWN_DEBT) - seen_debt
        self.assertFalse(stale, f"_KNOWN_DEBT entries no longer present, remove them: {stale}")


if __name__ == "__main__":
    unittest.main()
