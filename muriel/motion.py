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
    )

    validate_duration(80)     # OK — utility
    validate_duration(2000)   # OK — cinematic
    validate_duration(300)    # raises MotionPolicyError — uncanny zone

    validate_properties(["transform", "opacity"])  # OK
    validate_properties("top")                     # raises MotionPropertyError
    easing_for("enter")       # "ease-out"

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


def validate_duration(ms: float) -> None:
    """Raise ``MotionPolicyError`` if ``ms`` is in the uncanny zone.

    Negative durations raise ``ValueError`` (not a motion-policy
    violation — those are nonsense).
    """
    if ms < 0:
        raise ValueError(f"negative duration {ms}ms")
    if is_uncanny(ms):
        raise MotionPolicyError(
            f"{ms}ms is in the uncanny middle "
            f"({UTILITY_MS + 1}–{CINEMATIC_MS - 1}ms). "
            f"Pick utility (≤{UTILITY_MS}ms) or cinematic (≥{CINEMATIC_MS}ms)."
        )


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
        "\n"
        "quality axes (Emil-inspired, orthogonal to duration)\n"
        "----------------------------------------------------\n"
        f"property : animate {sorted(COMPOSITOR_SAFE_PROPERTIES)};\n"
        f"           never {sorted(LAYOUT_TRIGGERING_PROPERTIES)}\n"
        "easing   : enter → ease-out   exit → ease-in   move → ease-in-out\n"
        f"scale    : entrance floor {ENTRANCE_SCALE_FLOOR}, press {PRESS_SCALE} "
        "(not the source's 0.97)\n"
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
