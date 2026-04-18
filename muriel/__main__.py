"""
muriel — top-level CLI dispatcher.

Unifies per-module CLIs (``python -m muriel.capture``, ``.contrast``,
``.tools.heroshot``, etc.) behind a single ``muriel <subcommand>``
entry point. Each subcommand forwards its remaining arguments to the
module's ``_main(argv)`` function.

Usage
-----

::

    muriel                                 # list subcommands
    muriel --help                          # same
    muriel capture https://example.com     # responsive viewport-sweep screenshot
    muriel contrast audit page.svg         # WCAG 8:1 audit
    muriel dimensions                      # print the dimensions registry
    muriel heroshot in.png out.png --tilt 12
    muriel tilt-shift raw.png hero.png
    muriel venn spec.json out.png
    muriel styleguide examples/muriel-brand.toml --css

Invoked via:

- ``muriel …``         after ``pip install -e .`` (the console script)
- ``python -m muriel …``  without installation

Pattern lifted from [geraldnguyen/social-media-posters][sm-posters]
(MIT): one top-level CLI that dispatches to platform submodules. Same
shape, different domain — there it's one-CLI-to-many-social-platforms;
here it's one-CLI-to-many-visual-production-tools.

[sm-posters]: https://github.com/geraldnguyen/social-media-posters
"""

from __future__ import annotations

import sys
from importlib import import_module
from typing import Optional, Sequence


SUBCOMMANDS: dict[str, tuple[str, str]] = {
    # name            (module,                              one-line help)
    "capture":        ("muriel.capture",                    "Responsive viewport-sweep screenshot via Playwright"),
    "contrast":       ("muriel.contrast",                   "WCAG 8:1 contrast audit on SVG / CSS / color pairs"),
    "dimensions":     ("muriel.dimensions",                 "Print the dimensions registry (sizes, devices, paper)"),
    "heroshot":       ("muriel.tools.heroshot",             "Tilted + bordered + shadowed hero-shot from a PNG"),
    "tilt-shift":     ("muriel.tools.tilt_shift",           "Fake-lens depth-of-field blur on a PNG"),
    "venn":           ("muriel.tools.venn",                 "Area-proportional Venn / Euler diagram from a JSON spec"),
    "styleguide":     ("muriel.styleguide",                 "Load a brand.toml; print / derive CSS / matplotlibrc / contrast audit"),
}


def _print_help() -> None:
    print("muriel — next-gen visual-production skill for LLMs\n")
    print("Usage:  muriel <subcommand> [args...]\n")
    print("Subcommands:")
    width = max(len(name) for name in SUBCOMMANDS)
    for name, (module, helpline) in SUBCOMMANDS.items():
        print(f"  {name:<{width}}   {helpline}")
    print("\nFor subcommand usage:")
    print("  muriel <subcommand> --help\n")
    print("This dispatcher is a thin wrapper; each subcommand is also")
    print("available directly via 'python -m <module>'.")


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]

    if not argv or argv[0] in ("-h", "--help", "help"):
        _print_help()
        return 0

    sub = argv[0]
    rest = argv[1:]

    if sub not in SUBCOMMANDS:
        print(f"muriel: unknown subcommand {sub!r}\n", file=sys.stderr)
        _print_help()
        return 2

    module_name, _ = SUBCOMMANDS[sub]
    try:
        module = import_module(module_name)
    except ImportError as exc:
        print(f"muriel: failed to import {module_name} — {exc}", file=sys.stderr)
        return 2

    if not hasattr(module, "_main"):
        print(
            f"muriel: internal error — {module_name} has no _main() dispatcher",
            file=sys.stderr,
        )
        return 2

    rc = module._main(rest)
    return int(rc) if rc is not None else 0


if __name__ == "__main__":
    sys.exit(main())
