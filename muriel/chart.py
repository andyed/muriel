#!/usr/bin/env python3
"""ASCII Charts — Unicode bar charts for terminal, markdown, and chat.

Usage:
    python chart.py bar --data '{"A": 10, "B": 5}' --title "Scores"
    python chart.py bar --json data.json --title "Results"
    echo '{"A": 10}' | python chart.py bar --title "Piped"

Or as a library:
    from chart import bar_chart
    print(bar_chart({"A": 10, "B": 5}, title="Scores"))
"""

import json
import sys
import argparse
from typing import Optional

# Unicode block elements
FILL_SOLID = "█"
FILL_DENSE = "▓"
FILL_MEDIUM = "▒"
FILL_LIGHT = "░"
FILL_HALF = "▌"

# Sparkline blocks (bottom-to-top: 1/8 to 8/8)
SPARK_CHARS = " ▁▂▃▄▅▆▇█"

# Box drawing
BOX_H = "─"
BOX_V = "│"
BOX_TL = "┌"
BOX_TR = "┐"
BOX_BL = "└"
BOX_BR = "┘"


def bar_chart(
    data: dict[str, float],
    *,
    title: Optional[str] = None,
    width: int = 40,
    fill: str = FILL_SOLID,
    sort: bool = True,
    reverse: bool = True,
    marker: Optional[str] = None,
    marker_index: int = 0,
    show_values: bool = True,
    value_format: str = "g",
    suffix: str = "",
    compare: Optional[dict[str, float]] = None,
    compare_fill: str = FILL_MEDIUM,
    compare_label: Optional[str] = None,
    label: Optional[str] = None,
) -> str:
    """Generate a horizontal bar chart.

    Args:
        data: {label: value} dict
        title: Chart title (optional)
        width: Bar area width in characters
        fill: Unicode fill character for bars
        sort: Sort by value
        reverse: Descending order (largest first)
        marker: Character to mark specific items (e.g. "★")
        marker_index: Which item gets the marker (0 = top)
        show_values: Show numeric values after bars
        value_format: Format spec for values (e.g. ".1f", "g", "d")
        suffix: Unit suffix after values (e.g. "s", "ms", "%")
        compare: Second dataset for side-by-side comparison
        compare_fill: Fill character for comparison bars
        compare_label: Label for comparison dataset
        label: Label for primary dataset
    """
    if not data:
        return ""

    items = list(data.items())
    if sort:
        items.sort(key=lambda x: x[1], reverse=reverse)

    labels = [k for k, _ in items]
    values = [v for _, v in items]

    # Use absolute values for bar sizing, preserve originals for display
    abs_values = [abs(v) for v in values]

    # If comparing, merge keys and align
    if compare:
        comp_values = [compare.get(k, 0) for k in labels]
        abs_comp_values = [abs(v) for v in comp_values]
        max_val = max(max(abs_values), max(abs_comp_values))
    else:
        comp_values = None
        abs_comp_values = None
        max_val = max(abs_values) if abs_values else 1

    if max_val == 0:
        max_val = 1

    max_label = max(len(l) for l in labels)
    max_val_str = max(
        len(f"{v:{value_format}}{suffix}") for v in values
    )
    if comp_values:
        max_val_str = max(
            max_val_str,
            max(len(f"{v:{value_format}}{suffix}") for v in comp_values),
        )

    lines = []

    if title:
        lines.append(f"  {title}")
        lines.append("")

    # Legend for comparison mode
    if compare and (label or compare_label):
        legend_parts = []
        if label:
            legend_parts.append(f"  {fill}{fill} {label}")
        if compare_label:
            legend_parts.append(f"  {compare_fill}{compare_fill} {compare_label}")
        lines.append("  " + "    ".join(legend_parts))
        lines.append("")

    for i, (lbl, val) in enumerate(items):
        padded_label = lbl.rjust(max_label)

        if compare:
            # Side-by-side: primary bar on top line, comparison on bottom
            bar_len = int((abs_values[i] / max_val) * width)
            bar = fill * max(bar_len, 0)
            val_str = f"{val:{value_format}}{suffix}".rjust(max_val_str)

            comp_val = comp_values[i]
            comp_bar_len = int((abs_comp_values[i] / max_val) * width)
            comp_bar = compare_fill * max(comp_bar_len, 0)
            comp_val_str = f"{comp_val:{value_format}}{suffix}".rjust(max_val_str)

            marker_str = ""
            if marker and i == marker_index:
                marker_str = f"  {marker}"

            lines.append(f"  {padded_label}  {bar:<{width}}  {val_str}{marker_str}")
            lines.append(f"  {' ' * max_label}  {comp_bar:<{width}}  {comp_val_str}")
            if i < len(items) - 1:
                lines.append("")
        else:
            bar_len = int((abs_values[i] / max_val) * width)
            bar = fill * max(bar_len, 0)

            val_str = ""
            if show_values:
                val_str = f"  {val:{value_format}}{suffix}".rjust(max_val_str + 2)

            marker_str = ""
            if marker and i == marker_index:
                marker_str = f"  {marker}"

            lines.append(f"  {padded_label}  {bar:<{width}}{val_str}{marker_str}")

    return "\n".join(lines)


def sparkline(values: list[float], *, label: Optional[str] = None) -> str:
    """Generate a sparkline from a sequence of values.

    Args:
        values: List of numeric values
        label: Optional prefix label
    """
    if not values:
        return ""

    lo, hi = min(values), max(values)
    span = hi - lo if hi != lo else 1

    chars = []
    for v in values:
        idx = int((v - lo) / span * (len(SPARK_CHARS) - 1))
        chars.append(SPARK_CHARS[idx])

    line = "".join(chars)
    if label:
        line = f"{label}  {line}"
    return line


def table(
    rows: list[list[str]],
    *,
    headers: Optional[list[str]] = None,
    align: Optional[list[str]] = None,
) -> str:
    """Generate an aligned table.

    Args:
        rows: List of rows, each a list of cell strings
        headers: Optional header row
        align: Per-column alignment ("l", "r", "c"). Defaults to left.
    """
    all_rows = ([headers] if headers else []) + rows
    if not all_rows:
        return ""

    num_cols = max(len(r) for r in all_rows)
    col_widths = [0] * num_cols
    for row in all_rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    if align is None:
        align = ["l"] * num_cols

    def format_row(row):
        cells = []
        for i in range(num_cols):
            cell = str(row[i]) if i < len(row) else ""
            w = col_widths[i]
            a = align[i] if i < len(align) else "l"
            if a == "r":
                cells.append(cell.rjust(w))
            elif a == "c":
                cells.append(cell.center(w))
            else:
                cells.append(cell.ljust(w))
        return "  " + "  ".join(cells)

    lines = []
    if headers:
        lines.append(format_row(headers))
        sep = "  ".join(BOX_H * w for w in col_widths)
        lines.append("  " + sep)

    for row in rows:
        lines.append(format_row(row))

    return "\n".join(lines)


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="ASCII Charts")
    sub = parser.add_subparsers(dest="cmd")

    bar_p = sub.add_parser("bar", help="Horizontal bar chart")
    bar_p.add_argument("--data", help="JSON object: {label: value}")
    bar_p.add_argument("--json", help="Path to JSON file")
    bar_p.add_argument("--title", default=None)
    bar_p.add_argument("--width", type=int, default=40)
    bar_p.add_argument("--sort", action="store_true", default=True)
    bar_p.add_argument("--no-sort", dest="sort", action="store_false")
    bar_p.add_argument("--marker", default=None)
    bar_p.add_argument("--suffix", default="")
    bar_p.add_argument("--format", dest="value_format", default="g")
    bar_p.add_argument("--compare", help="JSON object for comparison dataset")
    bar_p.add_argument("--compare-fill", default=FILL_MEDIUM)
    bar_p.add_argument("--compare-label", default=None)
    bar_p.add_argument("--label", default=None)

    spark_p = sub.add_parser("spark", help="Sparkline")
    spark_p.add_argument("values", nargs="*", type=float)
    spark_p.add_argument("--label", default=None)

    args = parser.parse_args()

    if args.cmd == "bar":
        if args.json:
            with open(args.json) as f:
                data = json.load(f)
        elif args.data:
            data = json.loads(args.data)
        elif not sys.stdin.isatty():
            data = json.load(sys.stdin)
        else:
            parser.error("Provide --data, --json, or pipe JSON to stdin")

        compare = json.loads(args.compare) if args.compare else None

        print(bar_chart(
            data,
            title=args.title,
            width=args.width,
            sort=args.sort,
            marker=args.marker,
            suffix=args.suffix,
            value_format=args.value_format,
            compare=compare,
            compare_fill=args.compare_fill,
            compare_label=args.compare_label,
            label=args.label,
        ))

    elif args.cmd == "spark":
        if args.values:
            vals = args.values
        elif not sys.stdin.isatty():
            vals = [float(x) for x in sys.stdin.read().split()]
        else:
            parser.error("Provide values as args or via stdin")
        print(sparkline(vals, label=args.label))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
