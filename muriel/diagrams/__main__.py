"""CLI entry — ``python -m muriel.diagrams``."""

from __future__ import annotations

import argparse
import sys

from . import (
    DiagramError,
    THEMES,
    _selftest,
    cache_clear,
    render,
    render_ascii,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="muriel.diagrams",
        description="Render Mermaid to SVG/ASCII via beautiful-mermaid (Node bridge).",
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Mermaid source. Required unless --selftest or --cache-clear is passed.",
    )
    parser.add_argument(
        "--ascii",
        action="store_true",
        help="Render as Unicode terminal output instead of SVG.",
    )
    parser.add_argument(
        "--theme",
        default=None,
        choices=THEMES,
        metavar="NAME",
        help=f"Built-in theme name. One of: {', '.join(THEMES)}.",
    )
    parser.add_argument("--bg", help="Override background color (hex or var()).")
    parser.add_argument("--fg", help="Override foreground / primary text color.")
    parser.add_argument("--accent", help="Override accent color (arrowheads, highlights).")
    parser.add_argument(
        "--flatten",
        action="store_true",
        help=(
            "Bake CSS custom properties into concrete hex values so the "
            "SVG renders in librsvg / cairo / LaTeX (default emits var()-"
            "driven SVG for browser theming)."
        ),
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the bridge smoke-test instead of rendering.",
    )
    parser.add_argument(
        "--cache-clear",
        action="store_true",
        help="Delete every cached render. Combine with a source arg to re-render fresh.",
    )
    parser.add_argument(
        "--bbox",
        action="store_true",
        help="(SVG only) print measured (width, height) to stderr after rendering.",
    )
    args = parser.parse_args(argv)

    if args.cache_clear:
        n = cache_clear()
        print(f"cleared {n} cached render(s)", file=sys.stderr)
        if not args.source and not args.selftest:
            return 0

    if args.selftest:
        return _selftest()

    if not args.source:
        parser.error("source argument required (or pass --selftest)")

    color_kwargs = {
        k: v for k, v in (("bg", args.bg), ("fg", args.fg), ("accent", args.accent))
        if v
    }

    try:
        if args.ascii:
            text = render_ascii(args.source, theme=args.theme, **color_kwargs)
            sys.stdout.write(text)
            if not text.endswith("\n"):
                sys.stdout.write("\n")
        else:
            d = render(
                args.source,
                theme=args.theme,
                flatten=args.flatten,
                **color_kwargs,
            )
            sys.stdout.write(d.svg + "\n")
            if args.bbox:
                print(f"width={d.width:.2f} height={d.height:.2f}", file=sys.stderr)
    except DiagramError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
