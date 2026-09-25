"""motion — duration policy for muriel-driven animations.

Forced-binary rule: an animation is either **utility** (≤ 100 ms,
snappy and sub-perceptual) or **cinematic** (≥ 1500 ms, slow and
intentional). The middle ground — 101–1499 ms — is the *uncanny zone*
where motion reads as lag rather than purpose: too slow to feel
responsive, too fast to feel narrative.

This module enforces the rule programmatically. Callers pick one of
the two buckets and use the canonical constants
:data:`UTILITY_MS` / :data:`CINEMATIC_MS`, or pass a candidate
duration through :func:`validate_duration` to catch uncanny-zone
values before they ship.

Why the binary
--------------
Either the animation is invisible — the user processes it as instant
— or it is clearly intentional — the user processes it as narrative.
Everything else reads as lag and dilutes both modes. Axium ships this
as a stated policy; muriel adopts it as a check.

What the binary governs (owner decision, 2026-09-24)
----------------------------------------------------
The binary governs **transitions**: an interpolated change of position,
opacity, size, or color. ``validate_duration(ms)`` defaults to
``kind="transition"`` and enforces it. Three kinds are exempt, each for a
stated reason:

* ``"hold"`` — a pause between steps is not motion; nothing interpolates,
  so there is no lag to perceive. It must still be ≥ the transition it
  follows (pass ``after_transition_ms``), or the next step starts before
  the last one has landed.
* ``"spring"`` — the duration emerges from physics parameters, so the
  number is an output, not a choice. Validate the parameters instead
  (:func:`validate_spring`: bounce stays ``0``, polish rule 13).
* ``"press"`` — direct-manipulation feedback is coupled to the input; it
  is a response, not a scheduled animation (polish rule 14's
  ``scale(0.96)`` press, rule 20's touch opacity dip).

Sequences (step-through and timed reveals) use
:data:`STEP_TRANSITION_MS` (100) between states and :data:`STEP_HOLD_MS`
(1500) on each state. :func:`validate_sequence_timing` checks both and caps
a timed reveal at :data:`SEQUENCE_MAX_MS` (8000 ms total hold), so a reveal
at 1500 ms holds runs at most 5 steps. A ``"step"`` sequence is
user-driven and has no total.

Token mapping
-------------
``muriel.styleguide.Motion`` defaults sit on the two ends:
``duration_instant`` 0, ``duration_fast`` / ``duration_normal`` → 100
(utility transitions), ``duration_slow`` / ``duration_reveal`` → 1500
(cinematic). ``StyleGuide.to_css()`` also emits
``--<prefix>motion-transition`` / ``--<prefix>motion-hold`` from the
step constants (:data:`MOTION_CSS_TOKENS`).

Beyond duration — property, easing, scale
-----------------------------------------
Duration is one axis. These three orthogonal axes are paraphrased from the
Emil-Kowalski-inspired motion principles in All-The-Vibes/ATV-Design
(``skills/emil-design-eng-inspired``, MIT). muriel adopts the axes that do
*not* collide with the binary above:

* **Property** — animate only compositor-safe properties (``transform``,
  ``opacity``, ``filter``, ``clip-path``); never layout-triggering ones
  (``width`` / ``height`` / ``top`` / ``left`` / ``margin`` / ``padding``).
  Layout animation forces a reflow every frame and janks.
  :func:`validate_properties` enforces this.
* **Easing direction** — ``ease-out`` for entrances (and any user-triggered
  motion), ``ease-in`` for exits, ``ease-in-out`` for things moving while
  staying on screen. :func:`easing_for` returns the curve.
* **Scale** — entrance transforms floor at ``0.95`` (a card stepping forward,
  not a black hole opening from ``0``); press feedback uses ``0.96``.

Modes, flashing, sequence shape
-------------------------------
Structural checks for motion that explains a figure, adapted from
diagram-design's animation contract (MIT, © 2025 Cathryn Lavery); see
``references/polish-rules.md`` rules 28–29. None of them look at timing
except the decorative-loop cycle floor (≥ 3000 ms, cinematic under the
binary above):

* **Mode** — ``none`` / ``reveal`` / ``step`` / ``loop``. Only ``reveal``
  autoplays, and once; ``step`` is user-driven; ``loop`` is decorative and
  never carries meaning. :func:`validate_mode`.
* **Flash rate** — at most three flashes per second (WCAG 2.3.1).
  :func:`validate_flash_rate`.
* **Sequence shape** — 1–8 steps, ≤ 2 items entering per step, ≤ 12 items
  total. :func:`validate_sequence_shape`.

What muriel deliberately does NOT take from the source: its duration *bands*
(100–500 ms). Those sit squarely in muriel's uncanny zone — the binary above
overrides them. muriel also keeps press scale at ``0.96`` (its own tuned
value, see ``channels/polish.md`` rule 14), not the source's ``0.97``.

Usage
-----
    from muriel.motion import (
        UTILITY_MS, CINEMATIC_MS,
        is_utility, is_cinematic, is_uncanny,
        validate_duration, MotionPolicyError,
        validate_properties, easing_for, validate_scale,
        ENTRANCE_SCALE_FLOOR, PRESS_SCALE,
        validate_mode, validate_flash_rate, validate_sequence_shape,
    )

    validate_duration(80)     # OK — utility
    validate_duration(2000)   # OK — cinematic
    validate_duration(300)    # raises MotionPolicyError — uncanny zone
    validate_duration(300, kind="press")                          # OK — exempt
    validate_duration(1500, kind="hold", after_transition_ms=100)  # OK
    validate_sequence_timing(5, 100, 1500, mode="reveal")         # OK — 7500 ms

    validate_properties(["transform", "opacity"])  # OK
    validate_properties("top")                     # raises MotionPropertyError
    easing_for("enter")       # "ease-out"

    validate_mode("reveal", autoplay=True, repeats=False, semantic=True)  # OK
    validate_mode("step", autoplay=True, repeats=False, semantic=True)    # raises
    validate_flash_rate(4, 1000)          # raises — over 3 flashes/s
    validate_sequence_shape(5, [1, 2, 1, 1, 1])  # OK

CLI
---
    python -m muriel.motion             # print policy
    python -m muriel.motion 250         # classify / validate a candidate
    python -m muriel.motion --selftest  # run invariant checks
"""

from __future__ import annotations

import sys

__all__ = [
    "UTILITY_MS",
    "CINEMATIC_MS",
    "MotionPolicyError",
    "is_utility",
    "is_cinematic",
    "is_uncanny",
    "classify",
    "validate_duration",
    # Scope of the binary: transition vs exempt kinds; sequence timing.
    "DURATION_KINDS",
    "EXEMPT_KINDS",
    "EXEMPTION_REASONS",
    "STEP_TRANSITION_MS",
    "STEP_HOLD_MS",
    "SEQUENCE_MAX_MS",
    "SEQUENCE_MODES",
    "MOTION_CSS_TOKENS",
    "validate_spring",
    "validate_sequence_timing",
    # prefers-reduced-motion response vocabulary.
    "REDUCE_POLICIES",
    "REDUCE_POLICY_ALIASES",
    "normalize_reduce_policy",
    # Emil-inspired axes (orthogonal to the duration binary).
    "MotionPropertyError",
    "COMPOSITOR_SAFE_PROPERTIES",
    "LAYOUT_TRIGGERING_PROPERTIES",
    "EASING_BY_DIRECTION",
    "ENTRANCE_SCALE_FLOOR",
    "PRESS_SCALE",
    "is_compositor_safe",
    "validate_properties",
    "easing_for",
    "validate_scale",
    # Mode / flash / sequence-shape contract (diagram-design, MIT).
    "MOTION_MODES",
    "LOOP_MIN_CYCLE_MS",
    "MAX_FLASHES_PER_SECOND",
    "MAX_SEQUENCE_STEPS",
    "MAX_ITEMS_PER_STEP",
    "MAX_SEQUENCE_ITEMS",
    "validate_mode",
    "validate_flash_rate",
    "validate_sequence_shape",
]


UTILITY_MS: int = 100
"""Maximum duration (ms) for a utility-class animation."""

CINEMATIC_MS: int = 1500
"""Minimum duration (ms) for a cinematic-class animation."""


class MotionPolicyError(ValueError):
    """Raised when a duration falls in the uncanny middle (101–1499 ms)."""


def is_utility(ms: float) -> bool:
    """True iff ``ms`` is a snappy, sub-perceptual utility duration."""
    return 0 <= ms <= UTILITY_MS


def is_cinematic(ms: float) -> bool:
    """True iff ``ms`` is a slow, intentional cinematic duration."""
    return ms >= CINEMATIC_MS


def is_uncanny(ms: float) -> bool:
    """True iff ``ms`` falls in the forbidden middle zone."""
    return UTILITY_MS < ms < CINEMATIC_MS


def classify(ms: float) -> str:
    """Return ``"utility"`` / ``"cinematic"`` / ``"uncanny"`` for ``ms``."""
    if ms < 0:
        raise ValueError(f"negative duration {ms}ms")
    if is_utility(ms):
        return "utility"
    if is_cinematic(ms):
        return "cinematic"
    return "uncanny"


# ─── Scope: which durations the binary governs ─────────────────────────────

DURATION_KINDS: tuple[str, ...] = ("transition", "hold", "spring", "press")
"""Every kind :func:`validate_duration` accepts. Only ``transition`` is binary."""

EXEMPTION_REASONS: dict[str, str] = {
    "hold": "a pause between steps is not motion; it must be >= the transition it follows",
    "spring": "duration emerges from physics params; validate stiffness/bounce, not duration",
    "press": "direct-manipulation feedback is coupled to input, not a scheduled animation",
}
"""One-line reason per exempt kind. Mirrored in polish-rules.md (motion scope)."""

EXEMPT_KINDS = frozenset(EXEMPTION_REASONS)

STEP_TRANSITION_MS: int = UTILITY_MS
"""Transition between two states of a sequence (utility end of the binary)."""

STEP_HOLD_MS: int = CINEMATIC_MS
"""Hold on each state of a timed sequence (cinematic end of the binary)."""

SEQUENCE_MAX_MS: int = 8000
"""Cap on total hold time for a timed ``reveal``: 5 steps at 1500 ms."""

SEQUENCE_MODES: tuple[str, ...] = ("step", "reveal")

MOTION_CSS_TOKENS: dict[str, str] = {
    "motion-transition": f"{STEP_TRANSITION_MS}ms",
    "motion-hold": f"{STEP_HOLD_MS}ms",
}
"""CSS custom properties (unprefixed names) emitted by ``StyleGuide.to_css``."""


def validate_duration(
    ms: float,
    kind: str = "transition",
    *,
    after_transition_ms: float | None = None,
) -> None:
    """Raise ``MotionPolicyError`` if a ``transition`` is in the uncanny zone.

    ``kind`` scopes the rule (see module docstring): ``"transition"`` is
    held to the binary; ``"hold"``, ``"spring"``, ``"press"`` are exempt
    (:data:`EXEMPTION_REASONS`). A ``"hold"`` given ``after_transition_ms``
    must be ≥ that transition. Negative durations raise ``ValueError``
    (not a motion-policy violation — those are nonsense), as does an
    unknown ``kind``.
    """
    if kind not in DURATION_KINDS:
        raise ValueError(f"unknown duration kind {kind!r}; expected one of {DURATION_KINDS}")
    if ms < 0:
        raise ValueError(f"negative duration {ms}ms")
    if kind == "hold":
        if after_transition_ms is not None and ms < after_transition_ms:
            raise MotionPolicyError(
                f"hold {ms}ms is shorter than the {after_transition_ms}ms transition "
                "it follows; the next step would start before this one lands."
            )
        return
    if kind in EXEMPT_KINDS:
        return
    if is_uncanny(ms):
        raise MotionPolicyError(
            f"{ms}ms is in the uncanny middle "
            f"({UTILITY_MS + 1}–{CINEMATIC_MS - 1}ms). "
            f"Pick utility (≤{UTILITY_MS}ms) or cinematic (≥{CINEMATIC_MS}ms)."
        )


def validate_spring(bounce: float = 0.0, stiffness: float | None = None) -> None:
    """Validate a spring by its physics, not its emergent duration.

    ``bounce`` must be ``0`` (polish rule 13: bounce > 0 reads as
    gimmicky). ``stiffness``, when given, must be finite and positive.
    """
    if bounce != 0:
        raise MotionPolicyError(f"spring bounce {bounce} must be 0 (polish rule 13)")
    if stiffness is not None and not (0 < stiffness < float("inf")):
        raise ValueError(f"spring stiffness {stiffness} must be finite and > 0")


def validate_sequence_timing(
    steps: int,
    transition_ms: float = STEP_TRANSITION_MS,
    hold_ms: float = STEP_HOLD_MS,
    mode: str = "step",
) -> int | None:
    """Validate a stepped sequence; return total hold ms for a reveal.

    * ``transition_ms`` is a transition — held to the binary.
    * ``hold_ms`` is exempt from the binary but must be ≥ ``transition_ms``.
    * ``mode="reveal"`` (timed, auto-advancing): ``steps * hold_ms`` must be
      ≤ :data:`SEQUENCE_MAX_MS`. ``mode="step"`` is user-driven — no total,
      returns ``None``.
    """
    if mode not in SEQUENCE_MODES:
        raise ValueError(f"unknown sequence mode {mode!r}; expected one of {SEQUENCE_MODES}")
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError(f"steps must be a positive int, got {steps!r}")
    validate_duration(transition_ms, "transition")
    validate_duration(hold_ms, "hold", after_transition_ms=transition_ms)
    if mode == "step":
        return None
    total = int(steps * hold_ms)
    if total > SEQUENCE_MAX_MS:
        max_steps = int(SEQUENCE_MAX_MS // hold_ms) if hold_ms else steps
        raise MotionPolicyError(
            f"timed reveal holds {steps} x {hold_ms:g}ms = {total}ms, over the "
            f"{SEQUENCE_MAX_MS}ms cap; at {hold_ms:g}ms holds a reveal caps at "
            f"{max_steps} steps. Split it, or make it user-stepped (mode='step')."
        )
    return total


# ─── prefers-reduced-motion response vocabulary ────────────────────────────
#
# One vocabulary for ``[a11y].motion_reduce_policy`` (styleguide.A11y) and
# polish-rules.md rule 20. The code names are canonical; ``reduce`` is the
# name polish-rules used before 2026-09-24 and stays accepted as an alias.

REDUCE_POLICIES: dict[str, str] = {
    "collapse-to-zero": "every duration to 0; state changes are instant (default)",
    "keep-fast": "keep utility (<=100ms) opacity fades, transforms to identity, "
                 "drop cinematic and decorative motion",
    "keep-linear": "keep opacity fades at their durations with linear easing, "
                   "transforms to identity, drop decorative motion",
}

REDUCE_POLICY_ALIASES: dict[str, str] = {"reduce": "keep-fast"}


def normalize_reduce_policy(value: str) -> str:
    """Return the canonical ``motion_reduce_policy`` for ``value``.

    Resolves aliases (``reduce`` → ``keep-fast``). Raises ``ValueError`` on
    an unknown policy.
    """
    key = str(value).strip().lower()
    key = REDUCE_POLICY_ALIASES.get(key, key)
    if key not in REDUCE_POLICIES:
        raise ValueError(
            f"unknown motion_reduce_policy {value!r}; expected one of "
            f"{sorted(REDUCE_POLICIES)} (aliases: {REDUCE_POLICY_ALIASES})"
        )
    return key


# ─── Motion quality axes (Emil-inspired; see module docstring) ─────────────
#
# Orthogonal to the duration binary above. Paraphrased from the
# emil-design-eng-inspired skill in All-The-Vibes/ATV-Design (MIT). muriel
# adopts the property / easing / scale axes but NOT the source's duration
# bands (100–500 ms), which fall in the uncanny zone the binary forbids.


class MotionPropertyError(ValueError):
    """Raised when an animation targets a layout-triggering CSS property."""


# GPU-compositable properties — animating these stays off the main thread.
# Mirrors channels/polish.md rule 16's will-change table.
COMPOSITOR_SAFE_PROPERTIES = frozenset({
    "transform", "translate", "scale", "rotate",
    "opacity", "filter", "clip-path",
})

# Properties whose animation forces a layout pass (reflow) every frame.
LAYOUT_TRIGGERING_PROPERTIES = frozenset({
    "width", "height", "top", "left", "right", "bottom",
    "margin", "padding", "border-width", "inset",
})

# Easing curve by motion direction. Entrances decelerate to rest (ease-out);
# exits accelerate away (ease-in); on-screen repositions do both (ease-in-out).
EASING_BY_DIRECTION = {
    "enter": "ease-out",
    "exit":  "ease-in",
    "move":  "ease-in-out",
}

# Entrance transforms scale up FROM this floor, never from 0 — opacity carries
# "wasn't here, now is"; scale carries depth.
ENTRANCE_SCALE_FLOOR: float = 0.95

# Press feedback scale — muriel's tuned value (polish.md rule 14), not the
# source's 0.97. Below 0.95 reads as collapsing, not depressing.
PRESS_SCALE: float = 0.96


def _normalize_property(prop: str) -> str:
    """Lowercase + strip a CSS property, reducing a vendor prefix to its base.

    ``-webkit-transform`` → ``transform``; ``clip-path`` stays ``clip-path``.
    """
    p = prop.strip().lower()
    if p.startswith("-"):
        parts = p.split("-")  # ['', 'webkit', 'transform'] / ['', 'webkit', 'clip', 'path']
        if len(parts) >= 3:
            p = "-".join(parts[2:])
    return p


def is_compositor_safe(prop: str) -> bool:
    """True iff ``prop`` can be animated on the GPU compositor."""
    return _normalize_property(prop) in COMPOSITOR_SAFE_PROPERTIES


def validate_properties(props) -> None:
    """Raise ``MotionPropertyError`` if any property triggers layout.

    Accepts a single property name or an iterable of them. A property that is
    neither known-safe nor known-layout-triggering passes silently — unknown
    custom properties are not assumed unsafe.
    """
    if isinstance(props, str):
        props = [props]
    offenders = sorted({
        np for np in (_normalize_property(p) for p in props)
        if np in LAYOUT_TRIGGERING_PROPERTIES
    })
    if offenders:
        noun = "property" if len(offenders) == 1 else "properties"
        raise MotionPropertyError(
            f"animating layout-triggering {noun} {offenders}: forces a reflow "
            "every frame. Use transform/opacity instead (translate() not "
            "top/left, scale() not width/height)."
        )


def easing_for(direction: str) -> str:
    """Return the easing curve for a motion ``direction``.

    ``"enter"`` → ``ease-out``, ``"exit"`` → ``ease-in``, ``"move"`` →
    ``ease-in-out`` (on-screen reposition). Raises ``ValueError`` on an
    unknown direction.
    """
    key = direction.strip().lower()
    if key not in EASING_BY_DIRECTION:
        raise ValueError(
            f"unknown motion direction {direction!r}; "
            f"expected one of {sorted(EASING_BY_DIRECTION)}"
        )
    return EASING_BY_DIRECTION[key]


def validate_scale(value: float, kind: str = "entrance") -> None:
    """Raise ``ValueError`` if a scale transform is outside the legible band.

    Entrances and presses both floor at :data:`ENTRANCE_SCALE_FLOOR` (0.95):
    below it reads as a collapse / black-hole, above ``1.0`` overshoots into
    the bounce territory the polish channel bans. (``kind`` is accepted for
    call-site clarity; both kinds share the band.)
    """
    if kind not in ("entrance", "press"):
        raise ValueError(f"unknown scale kind {kind!r}; expected 'entrance' or 'press'")
    if not (ENTRANCE_SCALE_FLOOR <= value <= 1.0):
        raise ValueError(
            f"{kind} scale {value} is outside the legible band "
            f"[{ENTRANCE_SCALE_FLOOR}, 1.0]: below floor reads as a collapse, "
            "above 1.0 overshoots into bounce."
        )


# ─── Mode / flash / sequence-shape contract ────────────────────────────────
#
# Adapted from diagram-design's animation contract (MIT, © 2025 Cathryn
# Lavery): references/animation.md and ADRs 0001 / 0003. Structural only —
# the source's --motion-* clock tokens are NOT imported; how long a step or
# hold lasts is unresolved against the duration binary above.

MOTION_MODES = frozenset({"none", "reveal", "step", "loop"})

# A decorative loop cycles no faster than this. Slower loops stay ambient;
# faster ones start to pull the eye like an alert.
LOOP_MIN_CYCLE_MS: int = 3000

# WCAG 2.3.1 (Three Flashes or Below Threshold).
MAX_FLASHES_PER_SECOND: int = 3

MAX_SEQUENCE_STEPS: int = 8
MAX_ITEMS_PER_STEP: int = 2
MAX_SEQUENCE_ITEMS: int = 12


def validate_mode(
    mode: str,
    *,
    autoplay: bool,
    repeats: bool,
    semantic: bool,
    cycle_ms: float | None = None,
) -> None:
    """Raise ``MotionPolicyError`` if a figure's motion mode breaks the contract.

    ``autoplay``: motion starts without user action. ``repeats``: it plays
    more than once without an explicit Replay. ``semantic``: the moving
    elements carry meaning (state, values, order, outcomes). ``cycle_ms``:
    one loop cycle, required for ``loop``.

    * ``none``   — no motion at all: no autoplay, no repeat.
    * ``reveal`` — the only autoplay mode; plays once.
    * ``step``   — user-driven; never autoplays or repeats.
    * ``loop``   — decorative only (``semantic=False``), cycle ≥ 3000 ms.
    """
    key = mode.strip().lower() if isinstance(mode, str) else mode
    if key not in MOTION_MODES:
        raise MotionPolicyError(
            f"unknown motion mode {mode!r}; expected one of {sorted(MOTION_MODES)}"
        )
    if key == "none":
        if autoplay or repeats:
            raise MotionPolicyError(
                "mode 'none' is a static figure; it cannot autoplay or repeat."
            )
    elif key == "reveal":
        if repeats:
            raise MotionPolicyError(
                "mode 'reveal' plays once and ends on the complete frame; it "
                "never repeats without an explicit Replay."
            )
    elif key == "step":
        if autoplay:
            raise MotionPolicyError(
                "mode 'step' is user-driven; only 'reveal' may autoplay."
            )
        if repeats:
            raise MotionPolicyError("mode 'step' does not repeat on its own.")
    else:  # loop
        if semantic:
            raise MotionPolicyError(
                "mode 'loop' is decorative only; a repeating motion must not "
                "carry meaning. Use 'reveal' or 'step' for semantic motion."
            )
        if cycle_ms is None:
            raise MotionPolicyError(
                f"mode 'loop' needs cycle_ms (≥ {LOOP_MIN_CYCLE_MS}ms)."
            )
        if not (isinstance(cycle_ms, (int, float)) and cycle_ms == cycle_ms):
            raise ValueError(f"cycle_ms must be a finite number, got {cycle_ms!r}")
        if cycle_ms < LOOP_MIN_CYCLE_MS:
            raise MotionPolicyError(
                f"loop cycle {cycle_ms}ms is under the {LOOP_MIN_CYCLE_MS}ms "
                "floor; faster loops pull the eye like an alert."
            )


def validate_flash_rate(transitions: int, window_ms: float) -> None:
    """Raise ``MotionPolicyError`` if flashes exceed 3 per second (WCAG 2.3.1).

    ``transitions`` counts flashes (general or red) observed within a window
    of ``window_ms``. The check is on the rate: ``transitions / seconds``
    must not exceed :data:`MAX_FLASHES_PER_SECOND`.
    """
    if transitions < 0:
        raise ValueError(f"negative flash count {transitions}")
    if not (window_ms > 0 and window_ms != float("inf")):
        raise ValueError(f"window_ms must be a positive finite number, got {window_ms!r}")
    rate = transitions / (window_ms / 1000.0)
    if rate > MAX_FLASHES_PER_SECOND:
        raise MotionPolicyError(
            f"{transitions} flashes in {window_ms:g}ms is {rate:.2f}/s; "
            f"WCAG 2.3.1 allows at most {MAX_FLASHES_PER_SECOND}/s."
        )


def validate_sequence_shape(steps: int, per_step) -> None:
    """Raise ``MotionPolicyError`` if a reveal/step sequence is over budget.

    Structural budgets only (no timing): ``1 ≤ steps ≤ 8``, at most 2 items
    entering in any one step, at most 12 items in total. ``per_step`` lists
    the item count entering at each step and must have ``steps`` entries.
    """
    counts = list(per_step)
    if any(c < 0 for c in counts):
        raise ValueError(f"negative item count in per_step {counts}")
    if not (1 <= steps <= MAX_SEQUENCE_STEPS):
        raise MotionPolicyError(
            f"{steps} steps; a sequence has 1–{MAX_SEQUENCE_STEPS}. "
            "Over budget means the static figure is too dense, not that motion should rescue it."
        )
    if len(counts) != steps:
        raise ValueError(f"per_step has {len(counts)} entries for {steps} steps")
    if max(counts) > MAX_ITEMS_PER_STEP:
        raise MotionPolicyError(
            f"{max(counts)} items enter in one step; at most {MAX_ITEMS_PER_STEP}."
        )
    total = sum(counts)
    if total > MAX_SEQUENCE_ITEMS:
        raise MotionPolicyError(
            f"{total} items across the sequence; at most {MAX_SEQUENCE_ITEMS}."
        )


def _selftest() -> int:
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append(f"{name}: {detail or 'failed'}")

    # Boundary behaviour at 100 / 101 / 1499 / 1500.
    check("0 is utility", is_utility(0))
    check("100 is utility", is_utility(UTILITY_MS))
    check("101 is uncanny", is_uncanny(UTILITY_MS + 1))
    check("1499 is uncanny", is_uncanny(CINEMATIC_MS - 1))
    check("1500 is cinematic", is_cinematic(CINEMATIC_MS))
    check("2000 is cinematic", is_cinematic(2000))

    # Exactly one class per non-negative input.
    for ms in (0, 50, 100, 101, 500, 1499, 1500, 5000):
        n = int(is_utility(ms)) + int(is_uncanny(ms)) + int(is_cinematic(ms))
        check(f"{ms}ms has exactly one class", n == 1, f"got {n}")

    # classify() agrees with the predicates.
    check("classify(80) == utility", classify(80) == "utility")
    check("classify(300) == uncanny", classify(300) == "uncanny")
    check("classify(2000) == cinematic", classify(2000) == "cinematic")

    # validate_duration: pass utility / cinematic.
    validate_duration(80)
    validate_duration(100)
    validate_duration(1500)
    validate_duration(5000)

    # validate_duration: raise on uncanny.
    try:
        validate_duration(300)
    except MotionPolicyError:
        pass
    else:
        check("300ms raises MotionPolicyError", False, "did not raise")

    # validate_duration: raise on negative.
    try:
        validate_duration(-1)
    except ValueError:
        pass
    else:
        check("negative raises ValueError", False, "did not raise")

    # ── Scope: exempt kinds + sequence timing ──
    validate_duration(300, "press")
    validate_duration(300, "spring")
    validate_duration(1500, "hold", after_transition_ms=100)
    try:
        validate_duration(50, "hold", after_transition_ms=100)
    except MotionPolicyError:
        pass
    else:
        check("hold shorter than its transition raises", False, "did not raise")
    check("reveal of 5 at 1500 ok",
          validate_sequence_timing(5, 100, 1500, "reveal") == 7500)
    try:
        validate_sequence_timing(6, 100, 1500, "reveal")
    except MotionPolicyError:
        pass
    else:
        check("reveal of 6 at 1500 raises", False, "did not raise")
    check("reduce aliases keep-fast", normalize_reduce_policy("reduce") == "keep-fast")

    # ── Emil-inspired axes ──
    # Property selection.
    check("transform is compositor-safe", is_compositor_safe("transform"))
    check("opacity is compositor-safe", is_compositor_safe("opacity"))
    check("-webkit-transform normalizes", is_compositor_safe("-webkit-transform"))
    check("top is not compositor-safe", not is_compositor_safe("top"))
    check("safe/layout sets are disjoint",
          not (COMPOSITOR_SAFE_PROPERTIES & LAYOUT_TRIGGERING_PROPERTIES))
    validate_properties(["transform", "opacity", "filter"])  # all safe — passes
    validate_properties("color")  # unknown property → passes silently
    try:
        validate_properties(["transform", "width"])
    except MotionPropertyError:
        pass
    else:
        check("layout property raises MotionPropertyError", False, "did not raise")

    # Easing direction.
    check("enter → ease-out", easing_for("enter") == "ease-out")
    check("exit → ease-in", easing_for("exit") == "ease-in")
    check("move → ease-in-out", easing_for("move") == "ease-in-out")
    try:
        easing_for("sideways")
    except ValueError:
        pass
    else:
        check("unknown direction raises ValueError", False, "did not raise")

    # Scale band — press stays muriel's 0.96, not the source's 0.97.
    check("press scale is 0.96", PRESS_SCALE == 0.96)
    validate_scale(ENTRANCE_SCALE_FLOOR)   # floor passes
    validate_scale(0.96, "press")          # press passes
    validate_scale(1.0)                    # identity passes
    for bad in (0.0, 0.9, 1.1):
        try:
            validate_scale(bad)
        except ValueError:
            pass
        else:
            check(f"scale {bad} rejected", False, "did not raise")

    # ── Mode / flash / sequence shape ──
    validate_mode("none", autoplay=False, repeats=False, semantic=True)
    validate_mode("reveal", autoplay=True, repeats=False, semantic=True)
    validate_mode("step", autoplay=False, repeats=False, semantic=True)
    validate_mode("loop", autoplay=True, repeats=True, semantic=False,
                  cycle_ms=LOOP_MIN_CYCLE_MS)
    for args, kw in (
        (("step",), dict(autoplay=True, repeats=False, semantic=True)),
        (("reveal",), dict(autoplay=True, repeats=True, semantic=True)),
        (("loop",), dict(autoplay=True, repeats=True, semantic=True, cycle_ms=3000)),
        (("loop",), dict(autoplay=True, repeats=True, semantic=False, cycle_ms=2999)),
        (("carousel",), dict(autoplay=False, repeats=False, semantic=False)),
    ):
        try:
            validate_mode(*args, **kw)
        except MotionPolicyError:
            pass
        else:
            check(f"validate_mode{args}{kw} rejected", False, "did not raise")
    validate_flash_rate(3, 1000)
    try:
        validate_flash_rate(4, 1000)
    except MotionPolicyError:
        pass
    else:
        check("4 flashes/s rejected", False, "did not raise")
    validate_sequence_shape(5, [1, 2, 1, 1, 1])
    for steps, per in ((2, [3, 1]), (7, [2, 2, 2, 2, 2, 2, 1]), (0, []), (9, [1] * 9)):
        try:
            validate_sequence_shape(steps, per)
        except MotionPolicyError:
            pass
        else:
            check(f"sequence {steps}/{per} rejected", False, "did not raise")

    if failures:
        for f in failures:
            print(f"FAIL  {f}", file=sys.stderr)
        return 1
    print("OK  motion policy invariants pass")
    return 0


def _format_policy() -> str:
    return (
        "muriel motion policy\n"
        "--------------------\n"
        f"utility   : 0 – {UTILITY_MS} ms     (snappy, sub-perceptual)\n"
        f"cinematic : {CINEMATIC_MS} ms +   (slow, intentional, narrative)\n"
        f"uncanny   : {UTILITY_MS + 1} – {CINEMATIC_MS - 1} ms  (forbidden — reads as lag)\n"
        "scope     : transitions only; exempt kinds —\n"
        + "".join(f"            {k:<6} {r}\n" for k, r in EXEMPTION_REASONS.items())
        + f"sequence  : transition {STEP_TRANSITION_MS} ms, hold {STEP_HOLD_MS} ms, "
        f"timed reveal <= {SEQUENCE_MAX_MS} ms total hold\n"
        "\n"
        "quality axes (Emil-inspired, orthogonal to duration)\n"
        "----------------------------------------------------\n"
        f"property : animate {sorted(COMPOSITOR_SAFE_PROPERTIES)};\n"
        f"           never {sorted(LAYOUT_TRIGGERING_PROPERTIES)}\n"
        "easing   : enter → ease-out   exit → ease-in   move → ease-in-out\n"
        f"scale    : entrance floor {ENTRANCE_SCALE_FLOOR}, press {PRESS_SCALE} "
        "(not the source's 0.97)\n"
        "\n"
        "figure motion contract (diagram-design, structural only)\n"
        "--------------------------------------------------------\n"
        f"modes    : {sorted(MOTION_MODES)}; only reveal autoplays (once)\n"
        f"loop     : decorative only, cycle ≥ {LOOP_MIN_CYCLE_MS} ms\n"
        f"flash    : ≤ {MAX_FLASHES_PER_SECOND}/s (WCAG 2.3.1)\n"
        f"sequence : 1–{MAX_SEQUENCE_STEPS} steps, ≤ {MAX_ITEMS_PER_STEP}/step, "
        f"≤ {MAX_SEQUENCE_ITEMS} items\n"
    )


def _main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if argv and argv[0] == "--selftest":
        return _selftest()
    if not argv:
        print(_format_policy(), end="")
        return 0
    try:
        ms = float(argv[0])
    except ValueError:
        print(f"error: expected a numeric duration in ms, got {argv[0]!r}", file=sys.stderr)
        return 2
    try:
        cls = classify(ms)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(f"{ms:g}ms → {cls}")
    if cls == "uncanny":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main())
