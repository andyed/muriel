"""CLI entry — ``python -m muriel.math``."""

from __future__ import annotations

import argparse
import sys

from . import MathError, _selftest, cache_clear, display, inline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="muriel.math",
        description="Render TeX to SVG via MathJax v3 (Node bridge).",
    )
    parser.add_argument(
        "tex",
        nargs="?",
        help="LaTeX source. Required unless --selftest or --cache-clear is passed.",
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Render as display math (centred, larger operators).",
    )
    parser.add_argument(
        "--font-size",
        type=float,
        default=13.0,
        metavar="PX",
        help="Target font size in CSS pixels (default: 13).",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the bridge smoke-test instead of rendering.",
    )
    parser.add_argument(
        "--cache-clear",
        action="store_true",
        help="Delete every cached render. Combine with a tex arg to re-render fresh.",
    )
    parser.add_argument(
        "--bbox",
        action="store_true",
        help="Print measured (width, height) to stderr after rendering.",
    )
    args = parser.parse_args(argv)

    if args.cache_clear:
        n = cache_clear()
        print(f"cleared {n} cached render(s)", file=sys.stderr)
        if not args.tex and not args.selftest:
            return 0

    if args.selftest:
        return _selftest()

    if not args.tex:
        parser.error("tex argument required (or pass --selftest)")

    fn = display if args.display else inline
    try:
        m = fn(args.tex, font_size_px=args.font_size)
    except MathError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    sys.stdout.write(m.svg + "\n")
    if args.bbox:
        print(f"width={m.width:.2f} height={m.height:.2f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
