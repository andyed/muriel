#!/usr/bin/env python3
"""muriel.tools.corpus_audit — bulk-import a DESIGN.md corpus and report.

Why this exists
---------------
``muriel.design_md_import`` reads a single Google Stitch design.md and
emits a muriel brand.toml. That's enough for the one-brand workflow but
nowhere near enough to know whether the importer holds up across the
ecosystem. The DESIGN.md corpus is the natural fixture set: the
community-maintained `VoltAgent/awesome-design-md`_ repo ships ~73
hand-written DESIGN.md files for major brands (Stripe, Linear, Notion,
OpenAI, Anthropic, Cohere, Webflow, Vercel, Figma, …).

This module runs the entire corpus through ``parse_design_md`` and
emits a report that doubles as:

* A **regression harness** — any parser change that breaks a brand
  shows up immediately in the diff of two corpus reports.
* A **marketing artifact** — a public table of which brands satisfy
  muriel's universal 8:1 contrast floor on their imported
  ``background`` × ``foreground`` pair, and which don't. The 8:1 floor
  is muriel's defining rule; making it concrete against named brands
  is more persuasive than restating the policy.

Lineage
-------
Same idea as the "test against the whole npm ecosystem" harnesses used
by TypeScript / Babel / acorn. A corpus you don't own is a stronger
regression substrate than fixtures you wrote.

Usage
-----

::

    # one-time setup
    git clone https://github.com/VoltAgent/awesome-design-md /tmp/awesome-design-md

    # default: print a markdown table to stdout
    muriel import-corpus /tmp/awesome-design-md

    # full per-brand JSON (machine-readable for CI / diff)
    muriel import-corpus /tmp/awesome-design-md --format json -o report.json

    # just the headline numbers
    muriel import-corpus /tmp/awesome-design-md --format summary

The corpus path can point either at the repo root (containing
``design-md/<brand>/DESIGN.md``) or directly at the ``design-md/``
directory.

Cross-references: ``muriel.design_md_import`` (the importer being
exercised), ``muriel.contrast`` (the 8:1 ratio computation),
``CHANGELOG.md`` (release entry).

.. _VoltAgent/awesome-design-md: https://github.com/VoltAgent/awesome-design-md
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional, Sequence

from muriel.contrast import contrast_ratio
from muriel.design_md_import import parse_design_md

__all__ = [
    "BrandResult",
    "audit_corpus",
    "audit_file",
]


# Muriel's universal contrast floor — keep in sync with
# ``muriel.design_md_import.MURIEL_MIN_CONTRAST``.
MURIEL_MIN_CONTRAST = 8.0


@dataclass
class BrandResult:
    """Per-brand audit record."""

    brand: str
    source: str
    status: str  # "ok" | "no-frontmatter" | "parse-error" | "skipped"
    error: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    n_warnings: int = 0
    # Color extraction — populated when status == "ok".
    bg: Optional[str] = None
    fg: Optional[str] = None
    # When the importer can't find a usable bg/fg in the source it fills
    # in muriel's own defaults — those aren't the *brand's* contrast,
    # so the harness has to know to exclude them from the pass/fail
    # claim or the marketing artifact becomes dishonest.
    bg_defaulted: bool = False
    fg_defaulted: bool = False
    contrast: Optional[float] = None
    passes_8_1: Optional[bool] = None
    n_named_colors: int = 0
    n_aliases: int = 0
    # Typography extraction.
    n_scale_roles: int = 0
    has_body_family: bool = False
    has_display_family: bool = False
    # Misc structure.
    n_radii: int = 0
    n_motion_keys: int = 0
    n_elevation_keys: int = 0
    has_components_prose: bool = False
    has_dos_donts_prose: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─── Audit drivers ──────────────────────────────────────────────────


def audit_file(path: Path, brand: Optional[str] = None) -> BrandResult:
    """Audit a single DESIGN.md file."""
    name = brand or path.parent.name
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return BrandResult(
            brand=name, source=str(path), status="skipped",
            error=f"read failed: {exc}",
        )
    try:
        toml_dict, warnings = parse_design_md(text, source=path)
    except ValueError as exc:
        msg = str(exc)
        status = "no-frontmatter" if "frontmatter" in msg else "parse-error"
        return BrandResult(
            brand=name, source=str(path), status=status, error=msg,
        )

    result = BrandResult(
        brand=name, source=str(path), status="ok",
        warnings=list(warnings), n_warnings=len(warnings),
    )

    colors = toml_dict.get("colors") or {}
    result.bg = colors.get("background")
    result.fg = colors.get("foreground")
    named = colors.get("named") or {}
    aliases = colors.get("aliases") or {}
    result.n_named_colors = len(named) if isinstance(named, dict) else 0
    result.n_aliases = len(aliases) if isinstance(aliases, dict) else 0

    # Detect default-injection from the WARN trail. The importer logs
    # "(background) missing in source — defaulted to ..." when it can't
    # find a usable surface key; same for foreground.
    for w in warnings:
        if "(background) missing in source" in w:
            result.bg_defaulted = True
        if "(foreground) missing in source" in w:
            result.fg_defaulted = True

    if result.bg and result.fg:
        try:
            ratio = contrast_ratio(result.fg, result.bg)
            result.contrast = round(ratio, 2)
            # Only claim pass/fail when at least one of bg/fg came from
            # the source. If both are muriel defaults, the brand has no
            # stated bg/fg pair to evaluate — leave passes_8_1 = None.
            if result.bg_defaulted and result.fg_defaulted:
                result.passes_8_1 = None
            else:
                result.passes_8_1 = ratio >= MURIEL_MIN_CONTRAST
        except (ValueError, TypeError):
            result.contrast = None
            result.passes_8_1 = None

    typography = toml_dict.get("typography") or {}
    scale = typography.get("scale") or {}
    result.n_scale_roles = len(scale) if isinstance(scale, dict) else 0
    result.has_body_family = bool(typography.get("body_family"))
    result.has_display_family = bool(typography.get("display_family"))

    radii = toml_dict.get("radii") or {}
    result.n_radii = len(radii) if isinstance(radii, dict) else 0

    motion = toml_dict.get("motion") or {}
    result.n_motion_keys = len(motion) if isinstance(motion, dict) else 0

    elevation = toml_dict.get("elevation") or {}
    result.n_elevation_keys = len(elevation) if isinstance(elevation, dict) else 0

    rules = toml_dict.get("rules") or {}
    if isinstance(rules, dict):
        result.has_components_prose = "imported_components" in rules
        result.has_dos_donts_prose = "imported_dos_donts" in rules

    return result


def audit_corpus(corpus_root: Path) -> list[BrandResult]:
    """Walk a DESIGN.md corpus tree and audit every brand.

    Accepts either the awesome-design-md repo root (with a
    ``design-md/`` subdirectory) or the ``design-md/`` directory
    itself.
    """
    root = corpus_root
    candidate = root / "design-md"
    if candidate.is_dir():
        root = candidate
    if not root.is_dir():
        raise FileNotFoundError(
            f"{corpus_root} is not a directory or doesn't contain design-md/"
        )

    results: list[BrandResult] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        design_md = entry / "DESIGN.md"
        if not design_md.is_file():
            # Try lowercase fallback before declaring skipped.
            alt = entry / "design.md"
            if alt.is_file():
                design_md = alt
            else:
                results.append(BrandResult(
                    brand=entry.name, source=str(entry),
                    status="skipped",
                    error="no DESIGN.md or design.md in directory",
                ))
                continue
        results.append(audit_file(design_md, brand=entry.name))
    return results


# ─── Output formatters ──────────────────────────────────────────────


def _format_summary(results: list[BrandResult]) -> str:
    n = len(results)
    n_ok = sum(1 for r in results if r.status == "ok")
    n_parse_error = sum(1 for r in results if r.status == "parse-error")
    n_no_fm = sum(1 for r in results if r.status == "no-frontmatter")
    n_skipped = sum(1 for r in results if r.status == "skipped")
    n_pass_contrast = sum(1 for r in results if r.passes_8_1 is True)
    n_fail_contrast = sum(1 for r in results if r.passes_8_1 is False)
    n_both_defaulted = sum(
        1 for r in results
        if r.status == "ok" and r.bg_defaulted and r.fg_defaulted
    )
    n_partly_defaulted = sum(
        1 for r in results
        if r.status == "ok" and (r.bg_defaulted ^ r.fg_defaulted)
    )
    n_no_contrast = n_ok - n_pass_contrast - n_fail_contrast - n_both_defaulted
    total_warnings = sum(r.n_warnings for r in results)

    # Tally WARN messages by their first phrase (before the first colon
    # or "—") to group similar issues together.
    warn_counter: dict[str, int] = {}
    for r in results:
        for w in r.warnings:
            key = w.split("—")[0].split(":")[0].strip()
            # Truncate very long keys
            if len(key) > 80:
                key = key[:77] + "..."
            warn_counter[key] = warn_counter.get(key, 0) + 1
    top_warns = sorted(warn_counter.items(), key=lambda kv: -kv[1])[:8]

    lines: list[str] = [
        f"muriel DESIGN.md corpus audit — {n} brands",
        "",
        f"  Parsed cleanly:      {n_ok:>3}  ({n_ok * 100 // max(n, 1)}%)",
        f"  No frontmatter:      {n_no_fm:>3}",
        f"  Parse errors:        {n_parse_error:>3}",
        f"  Skipped:             {n_skipped:>3}",
        "",
        f"  Of parsed, brands with REAL bg/fg from source:",
        f"    Pass 8:1 contrast: {n_pass_contrast:>3}",
        f"    Fail 8:1 contrast: {n_fail_contrast:>3}",
        f"    Partly defaulted:  {n_partly_defaulted:>3}  (one of bg/fg defaulted by muriel)",
        f"    Both defaulted:    {n_both_defaulted:>3}  (importer found no usable surface keys)",
        f"    No bg/fg at all:   {n_no_contrast:>3}",
        "",
        f"  Total WARNs raised:  {total_warnings}",
    ]
    if top_warns:
        lines.append("")
        lines.append("  Top WARN categories:")
        for key, count in top_warns:
            lines.append(f"    {count:>3}× {key}")
    return "\n".join(lines) + "\n"


def _format_markdown(results: list[BrandResult]) -> str:
    """Markdown table — release-blog ready."""
    n = len(results)
    n_ok = sum(1 for r in results if r.status == "ok")
    n_pass = sum(1 for r in results if r.passes_8_1 is True)
    n_fail = sum(1 for r in results if r.passes_8_1 is False)

    lines: list[str] = [
        "# muriel DESIGN.md corpus audit",
        "",
        f"`muriel.design_md_import` ingested **{n_ok}/{n} DESIGN.md** files "
        f"from the [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) "
        f"corpus. Of the parsed brands, **{n_pass}** satisfy muriel's universal "
        f"8:1 contrast floor on their imported `background` × `foreground` pair, "
        f"**{n_fail}** fall short.",
        "",
        "| Brand | Status | bg | fg | Contrast | 8:1 | Scale roles | Body / Display | WARNs |",
        "|---|---|---|---|---:|:---:|---:|:---:|---:|",
    ]
    for r in sorted(results, key=lambda r: r.brand):
        if r.status != "ok":
            lines.append(
                f"| `{r.brand}` | {r.status} | — | — | — | — | — | — | — |"
            )
            continue
        contrast_txt = f"{r.contrast:.2f}" if r.contrast is not None else "—"
        if r.bg_defaulted and r.fg_defaulted:
            pass_mark = "n/a"  # muriel filled in both — not the brand's contrast
        else:
            pass_mark = "✓" if r.passes_8_1 else ("✗" if r.passes_8_1 is False else "—")
        bg_txt = f"`{r.bg}`{' *' if r.bg_defaulted else ''}" if r.bg else "—"
        fg_txt = f"`{r.fg}`{' *' if r.fg_defaulted else ''}" if r.fg else "—"
        bd = "B" if r.has_body_family else "·"
        dp = "D" if r.has_display_family else "·"
        lines.append(
            f"| `{r.brand}` | ok | {bg_txt} | {fg_txt} | "
            f"{contrast_txt} | {pass_mark} | "
            f"{r.n_scale_roles} | {bd}{dp} | {r.n_warnings} |"
        )
    lines.append("")
    lines.append(
        "*`*` next to a colour = muriel filled in a default because the "
        "importer didn't find a usable surface key in the source. When "
        "both bg and fg are defaulted the contrast claim is `n/a` (it's "
        "muriel's contrast, not the brand's). The 8:1 floor is muriel's "
        "universal a11y rule — stricter than WCAG AAA (7:1) — and applies "
        "regardless of any `contrast.minimum` in the source spec.*"
    )
    lines.append("")
    return "\n".join(lines) + "\n"


def _format_json(results: list[BrandResult]) -> str:
    return json.dumps(
        [r.as_dict() for r in results], indent=2, sort_keys=True,
    ) + "\n"


# ─── CLI ────────────────────────────────────────────────────────────


def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="muriel import-corpus",
        description=(
            "Audit a DESIGN.md corpus (e.g. awesome-design-md) against "
            "muriel's design_md_import + 8:1 contrast floor."
        ),
    )
    ap.add_argument(
        "corpus", type=Path, nargs="?",
        help="path to the corpus (repo root, or the design-md/ subdir)",
    )
    ap.add_argument(
        "--format", choices=("summary", "md", "json"), default="summary",
        help="output shape (default: summary)",
    )
    ap.add_argument(
        "-o", "--output", default="-",
        help="output file (default: stdout)",
    )
    ap.add_argument(
        "--fail-on", choices=("never", "any-error", "any-contrast-fail"),
        default="never",
        help=(
            "exit non-zero when this condition holds (CI gate). "
            "'any-error' = any non-ok status; "
            "'any-contrast-fail' = any parsed brand below 8:1."
        ),
    )
    args = ap.parse_args(argv)

    if args.corpus is None:
        ap.print_help()
        return 0
    if not args.corpus.exists():
        print(
            f"muriel import-corpus: {args.corpus} does not exist. "
            f"Try `git clone https://github.com/VoltAgent/awesome-design-md`.",
            file=sys.stderr,
        )
        return 2

    try:
        results = audit_corpus(args.corpus)
    except FileNotFoundError as exc:
        print(f"muriel import-corpus: {exc}", file=sys.stderr)
        return 2

    if args.format == "summary":
        text = _format_summary(results)
    elif args.format == "md":
        text = _format_markdown(results)
    else:
        text = _format_json(results)

    if args.output == "-":
        sys.stdout.write(text)
    else:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"wrote {args.output}", file=sys.stderr)

    if args.fail_on == "any-error":
        if any(r.status != "ok" for r in results):
            return 1
    elif args.fail_on == "any-contrast-fail":
        if any(r.passes_8_1 is False for r in results):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main())
