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

Usage
-----
    from muriel.motion import (
        UTILITY_MS, CINEMATIC_MS,
        is_utility, is_cinematic, is_uncanny,
        validate_duration, MotionPolicyError,
    )

    validate_duration(80)     # OK — utility
    validate_duration(2000)   # OK — cinematic
    validate_duration(300)    # raises MotionPolicyError — uncanny zone

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
