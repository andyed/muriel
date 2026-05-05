"""
muriel.critique — render critique gate.

Codifies the recurring ``/muriel critique`` pattern as a checklist + report
generator. Runs the automated checks muriel can do (delegating to
``muriel.contrast`` for SVG WCAG audits, ``muriel.dimensions`` for size-
target verification) and produces a structured Markdown critique report
following the format used in informal critiques across this skill:

    ### Verdict: PASS / NEEDS REVISION / FAIL
    ### FAIL items — framework violations
    ### NEEDS REVISION — weak execution
    ### What works — keep list
    ### Recommended path forward

The point is not that this CLI replaces human judgment. It is that the
critique pass becomes a *required gate* before any artifact is shipped —
not an optional polish step. Most checks here scaffold the human
checklist; a few (contrast, dimension targeting) run fully automatically.

Why this exists
---------------

Across one weekend (2026-05-03), ``/muriel critique`` was invoked five
times across three projects. Each invocation surfaced fixable issues that
the rendered artifact would have shipped with otherwise. The pattern
revealed: critique is the unit of progress, not the unit of polish.

Usage
-----

Programmatic:

.. code-block:: python

    from muriel.critique import critique_artifact, CritiqueReport

    report = critique_artifact("docs/figs/task_overview.png")
    print(report.as_markdown())

CLI:

.. code-block:: bash

    python -m muriel.critique path/to/figure.{png,svg,pdf}
    python -m muriel.critique path/to/figure.svg --threshold 8.0
    python -m muriel.critique path/to/figure.png --target paper-2col --audience science-paper
    python -m muriel.critique path/to/figure.png --output critique.md

Exit codes:
  0  = PASS — all automated checks cleared, manual checklist present
  1  = NEEDS REVISION — automated checks flagged issues
  2  = FAIL — usage / file errors

Designed to slot into a pre-commit hook for the ``scripts/output/figures/``
or ``docs/figs/`` directories.
"""
from __future__ import annotations

import argparse
import dataclasses
import re
import sys
from pathlib import Path
from typing import Optional

# Module imports — keep stdlib-first; muriel sub-modules optional.
try:
    from muriel.contrast import audit_svg, parse_color, contrast_ratio
    _HAS_CONTRAST = True
except Exception:
    _HAS_CONTRAST = False

try:
    from muriel.dimensions import figsize_for, REGISTRY
    _HAS_DIMENSIONS = True
except Exception:
    _HAS_DIMENSIONS = False


VERDICT_PASS = "PASS"
VERDICT_NEEDS_REVISION = "NEEDS REVISION"
VERDICT_FAIL = "FAIL"


@dataclasses.dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    framework: str = ""  # citation for muriel rule violated, if any


@dataclasses.dataclass
class CritiqueReport:
    artifact_path: str
    verdict: str
    automated_checks: list[CheckResult] = dataclasses.field(default_factory=list)
    manual_checklist: list[str] = dataclasses.field(default_factory=list)
    keep_list: list[str] = dataclasses.field(default_factory=list)
    recommendations: list[str] = dataclasses.field(default_factory=list)

    def add_auto(self, name: str, passed: bool, detail: str = "", framework: str = "") -> None:
        self.automated_checks.append(CheckResult(name, passed, detail, framework))

    @property
    def n_failed_auto(self) -> int:
        return sum(1 for c in self.automated_checks if not c.passed)

    def as_markdown(self) -> str:
        lines = []
        lines.append(f"# muriel critique — `{Path(self.artifact_path).name}`\n")
        lines.append(f"## Verdict: **{self.verdict}**\n")

        # Automated checks
        lines.append("## Automated checks\n")
        if not self.automated_checks:
            lines.append("_No automated checks ran. (File type may not have a checker yet.)_\n")
        else:
            for c in self.automated_checks:
                icon = "✓" if c.passed else "✗"
                line = f"- {icon} **{c.name}** — {c.detail}"
                if c.framework:
                    line += f" *(framework: {c.framework})*"
                lines.append(line)
        lines.append("")

        # Manual checklist (the heart of the critique discipline)
        lines.append("## Manual checklist\n")
        lines.append("These checks require human judgment. Walk each one and update verdict.\n")
        for item in self.manual_checklist:
            lines.append(f"- [ ] {item}")
        lines.append("")

        # Keep list
        if self.keep_list:
            lines.append("## What works (keep)\n")
            for item in self.keep_list:
                lines.append(f"- {item}")
            lines.append("")

        # Recommendations
        if self.recommendations:
            lines.append("## Recommended path forward\n")
            for r in self.recommendations:
                lines.append(f"- {r}")
            lines.append("")

        return "\n".join(lines)

    def exit_code(self) -> int:
        if self.verdict == VERDICT_FAIL:
            return 2
        if self.verdict == VERDICT_NEEDS_REVISION:
            return 1
        return 0


# ── Manual-checklist templates ──

CHECKLIST_UNIVERSAL = [
    "**Element-count discipline**: ≤ 3 load-bearing visual concepts per panel. "
    "Each element passes the Tufte test ('removing it would reduce information').",
    "**Hero hierarchy**: each panel has exactly one largest element, one second-largest, "
    "rest supporting. Re-layer if four elements compete for attention.",
    "**8:1 contrast on all text** (computed; auto-checked for SVG, manual for raster).",
    "**Decorative elements ≥ 55/255** on dark BG, or visible ≥ 1.5px at target DPI.",
    "**Caption ↔ chart split**: any element < 1.5 px or < 9 pt at target DPI moves to caption.",
    "**One font treatment** per app/paper. Vary background, not typography.",
    "**Audience vocabulary check**: no internal project jargon in chart text. "
    "Use field-standard terms the audience already knows.",
    "**Generated > drawn**: this artifact came from a reproducible script saved alongside.",
    "**Reproducible**: the script regenerates the artifact bit-for-bit; "
    "iteration deltas are in the docstring.",
    "**No false profundity**: substance over hype. Each label earns its place.",
]

CHECKLIST_BY_CHANNEL = {
    "science": [
        "**rcparams**: figure uses `muriel.matplotlibrc_light` or `_dark`, "
        "not raw matplotlib defaults.",
        "**APA stats**: every reported number has units; "
        "*p*-values use `muriel.stats.format_p`; minus signs are U+2212.",
        "**Caption**: caption carries the methodology/sample size, "
        "not buried in chart annotations.",
    ],
    "infographic": [
        "**60-30-10 color rule**: dominant / secondary / accent colors balance.",
        "**60-40 viz:text rule**: roughly 60% visual / 40% text by area.",
        "**Single-image scope**: communicates one claim, not a sequence.",
    ],
    "paper-figure": [
        "**Single-column ≤ 8.5 cm wide** unless explicitly two-column",
        "**LaTeX-friendly**: no rasterized text in the PDF; vectors throughout.",
        "**Figure caption ≤ 80 words**, leads with the take-away.",
    ],
    "social-card": [
        "**Safe area**: critical content within central 80% of the frame.",
        "**Single hero**: one headline at >= 36pt; subtitle ≤ 16pt.",
    ],
}


# ── Channel front-matter parser ──
#
# Handles the bounded YAML subset documented in ``channels/SCHEMA.md``:
# top-level ``key: value``, one level of nested ``key: value`` pairs, and
# inline list values (``[a, b]``). No PyYAML dependency — keeps muriel's
# zero-required-deps invariant.

def _parse_frontmatter(text: str) -> dict:
    """Parse the leading ``---``-delimited YAML block; return ``{}`` if absent.

    Handles the bounded subset documented in ``channels/SCHEMA.md``:
    top-level scalar / inline-list / dict / list, and one level of nested
    scalar / inline-list / list. List bullets target whichever key most
    recently opened with an empty value.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out: dict = {}
    current_top: Optional[str] = None
    current_list: Optional[list] = None
    for raw in text[3:end].splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if stripped.startswith("- "):
            item = stripped[2:].strip().strip("'\"")
            if current_list is None and current_top is not None:
                if isinstance(out.get(current_top), dict) and not out[current_top]:
                    out[current_top] = []
                    current_list = out[current_top]
            if isinstance(current_list, list):
                current_list.append(item)
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if indent == 0:
            current_top = key
            current_list = None
            if not value:
                out[key] = {}
            elif value.startswith("[") and value.endswith("]"):
                out[key] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
            else:
                out[key] = value.strip("'\"")
        else:
            if current_top is None:
                continue
            if not isinstance(out.get(current_top), dict):
                out[current_top] = {}
            if not value:
                out[current_top][key] = []
                current_list = out[current_top][key]
            elif value.startswith("[") and value.endswith("]"):
                out[current_top][key] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
                current_list = None
            else:
                out[current_top][key] = value.strip("'\"")
                current_list = None
    return out


def _load_channel_meta(channel: str) -> dict:
    """Load front-matter for ``channels/<channel>.md`` if present.

    Returns an empty dict when the file is missing or has no front-matter.
    Critique then proceeds without channel-specific gates.
    """
    here = Path(__file__).resolve().parent.parent
    chan_path = here / "channels" / f"{channel}.md"
    if not chan_path.exists():
        return {}
    try:
        return _parse_frontmatter(chan_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── P0 honesty probe ──
#
# Two-tier scan, mined from open-design's ``replit-deck`` P0 honesty gate:
#
#   * AI-slop emoji in artifact text → hard FAIL (always inappropriate for
#     scientific / editorial output).
#   * Narrative numeric claims (``10x faster``, ``$50M``, ``3 billion``,
#     ``+45%``) → NEEDS REVISION, with each claim listed for human audit.
#     Tick labels and bare numbers in axis context are deliberately *not*
#     flagged — they are data, not claims.
#
# Operates on SVG text content (raster artifacts skip the probe).

# Stock SaaS / pitch-deck emoji that should never appear in muriel output.
SLOP_EMOJI = ("🚀", "✨", "📊", "🔥", "💯", "⚡", "🎯", "💪", "🙌")

# Patterns that signal a *narrative* numeric claim, not a tick label.
# Order matters — more specific patterns first.
NARRATIVE_CLAIM_PATTERNS = (
    re.compile(r"\b\d+(?:\.\d+)?\s*[x×]\s+(?:faster|slower|more|less|better|larger|smaller|higher|lower)\b", re.I),
    re.compile(r"\b\d+(?:\.\d+)?\s*%\s+(?:faster|slower|more|less|better|improvement|increase|decrease|gain|loss)\b", re.I),
    re.compile(r"\$\s*\d+(?:\.\d+)?\s*[KMB]\b"),
    re.compile(r"\b\d+(?:\.\d+)?\s+(?:billion|million|trillion)\b", re.I),
    re.compile(r"[+\-]\d+(?:\.\d+)?\s*%\s+(?:vs|over|than)\b", re.I),
)

_TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_CITED_RE = re.compile(r'data-(?:source|cite|citation)\s*=', re.I)


def _extract_svg_text(svg_text: str) -> list[str]:
    """Pull plain text content out of every ``<text>`` element."""
    out = []
    for m in _TEXT_RE.finditer(svg_text):
        inner = _TAG_RE.sub("", m.group(1)).strip()
        if inner:
            out.append(inner)
    return out


def _honesty_probe_svg(svg_text: str) -> tuple[list[str], list[str]]:
    """Run the P0 honesty probe on an SVG.

    Returns (slop_emoji_found, narrative_claims_found). Either non-empty
    triggers the corresponding finding; both empty means the probe passed.
    """
    text_blocks = _extract_svg_text(svg_text)
    haystack = "\n".join(text_blocks)
    slop = [e for e in SLOP_EMOJI if e in haystack]
    claims: list[str] = []
    for pat in NARRATIVE_CLAIM_PATTERNS:
        for m in pat.finditer(haystack):
            claim = m.group(0).strip()
            if claim not in claims:
                claims.append(claim)
    # If the SVG cites sources via data-* attributes, claims may be
    # legitimate — surface them anyway but mark as cited so the report
    # downgrades from P0 fail to P1 audit.
    return slop, claims


def _is_svg(path: Path) -> bool:
    return path.suffix.lower() == ".svg"


def _is_raster(path: Path) -> bool:
    return path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")


def _is_pdf(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


def critique_artifact(
    artifact_path: str | Path,
    *,
    threshold: float = 8.0,
    target: Optional[str] = None,
    audience: Optional[str] = None,
    channel: str = "science",
) -> CritiqueReport:
    """Run automated checks on an artifact and assemble a critique report.

    Parameters
    ----------
    artifact_path : str or Path
        Path to the rendered artifact.
    threshold : float
        WCAG contrast threshold (default 8.0 — muriel's 8:1 rule).
    target : str, optional
        Named dimension target from ``muriel.dimensions.REGISTRY``
        (e.g., ``'og-image'``, ``'paper-2col'``). When set, dimension
        check verifies the artifact size matches.
    audience : str, optional
        Named audience profile (see ``style-guides.md`` audiences section).
        When set, vocabulary lint runs against the audience's denylist.
    channel : str
        Channel context — picks the per-channel checklist additions.
        Default ``'science'``.
    """
    p = Path(artifact_path)
    report = CritiqueReport(artifact_path=str(p), verdict=VERDICT_NEEDS_REVISION)

    # ── Automated check 1: file exists & readable ──
    if not p.exists():
        report.verdict = VERDICT_FAIL
        report.add_auto("file exists", False, f"{p} does not exist")
        return report
    report.add_auto("file exists & readable", True, f"{p.stat().st_size:,} bytes")

    # ── Channel front-matter — opt-in gates per channel ──
    chan_meta = _load_channel_meta(channel)
    requires = chan_meta.get("requires", {}) if isinstance(chan_meta.get("requires"), dict) else {}
    if requires.get("audience") == "required" and not audience:
        report.add_auto(
            "channel requires audience profile",
            False,
            f"channel `{channel}` declares `requires.audience: required` but "
            "no `--audience` was passed; vocabulary denylist cannot run",
            framework="channels/SCHEMA.md",
        )
    if requires.get("brand") == "required":
        # Brand presence is conventionally signaled by the artifact carrying
        # brand-token references; a hard check would need to cross-reference
        # the rendering script. Surface as a manual checklist item.
        pass

    # ── Automated check 2: contrast (SVG only) ──
    if _is_svg(p) and _HAS_CONTRAST:
        try:
            entries = audit_svg(str(p), required=threshold, print_table=False)
            failed = [e for e in entries if getattr(e, "passed", True) is False]
            ok = not failed
            report.add_auto(
                f"WCAG ≥ {threshold:.1f} on text roles",
                ok,
                f"{len(entries)} text role(s) audited; "
                + ("all cleared" if ok else f"{len(failed)} failed at threshold {threshold:.1f}"),
                framework="muriel universal rule: 8:1 minimum on text",
            )
        except Exception as e:
            report.add_auto("WCAG contrast audit", False,
                            f"audit error: {e}")
    elif _is_raster(p) or _is_pdf(p):
        report.add_auto(
            "WCAG contrast audit",
            True,  # not applicable, not failed
            f"{p.suffix} — manual check required (no raster auditor in muriel yet)",
        )

    # ── Automated check 3: P0 honesty probe (SVG only) ──
    #
    # Mined from open-design's replit-deck checklist — "no invented
    # metrics, no stock SaaS emoji". Two findings:
    #   * slop emoji → hard FAIL.
    #   * narrative numeric claims → NEEDS REVISION + per-claim audit list.
    if _is_svg(p):
        try:
            svg_text = p.read_text(encoding="utf-8", errors="replace")
            cited = bool(_CITED_RE.search(svg_text))
            slop, claims = _honesty_probe_svg(svg_text)
            if slop:
                report.add_auto(
                    "P0 honesty: no AI-slop emoji",
                    False,
                    f"found {len(slop)} stock emoji in <text>: {' '.join(slop)}",
                    framework="open-design replit-deck P0 honesty gate",
                )
                report.verdict = VERDICT_FAIL
            else:
                report.add_auto(
                    "P0 honesty: no AI-slop emoji",
                    True,
                    "no stock SaaS emoji found in artifact text",
                )
            if claims:
                detail = (
                    f"found {len(claims)} narrative numeric claim(s): "
                    + "; ".join(f"`{c}`" for c in claims[:5])
                    + (" …" if len(claims) > 5 else "")
                    + (
                        " — artifact has data-source/data-cite attributes; audit each claim."
                        if cited
                        else " — no data-source attributes found; each claim must be sourced or labeled illustrative."
                    )
                )
                report.add_auto(
                    "P0 honesty: numeric claims sourced",
                    False,
                    detail,
                    framework="open-design replit-deck P0 honesty gate",
                )
            else:
                report.add_auto(
                    "P0 honesty: numeric claims sourced",
                    True,
                    "no narrative numeric-claim patterns detected in artifact text",
                )
        except Exception as e:
            report.add_auto("P0 honesty probe", False, f"probe error: {e}")

    # ── Automated check 4: dimension target match ──
    if target and _HAS_DIMENSIONS:
        if target in REGISTRY:
            tgt = REGISTRY[target]
            report.add_auto(
                f"dimension target = {target}",
                True,  # placeholder — actual size check would need image lib
                f"target {tgt.width}x{tgt.height} ({tgt.aspect_label}); "
                "manual check required for raster pixel sizes",
            )
        else:
            report.add_auto(
                f"dimension target = {target}",
                False,
                f"target '{target}' not in muriel.dimensions.REGISTRY",
            )

    # ── Manual checklist ──
    report.manual_checklist.extend(CHECKLIST_UNIVERSAL)
    if channel in CHECKLIST_BY_CHANNEL:
        report.manual_checklist.extend(CHECKLIST_BY_CHANNEL[channel])

    if audience:
        report.manual_checklist.insert(
            0,
            f"**Audience: `{audience}`** — verify chart text uses this audience's "
            "field-standard vocabulary; project-internal jargon is filtered out. "
            "(See `channels/style-guides.md` audience profiles.)"
        )

    # ── Verdict ──
    # Automated checks set FAIL only on critical failures (file missing, audit error).
    # Otherwise the verdict starts at NEEDS REVISION (default) and the human
    # walks the manual checklist to either confirm PASS or identify issues.
    if report.n_failed_auto == 0:
        # All automated checks cleared. Verdict is "NEEDS REVISION pending manual"
        # — escalates to PASS only when a reviewer has walked the checklist.
        # We don't auto-PASS without that walk.
        report.verdict = VERDICT_NEEDS_REVISION
        report.recommendations.append(
            "Walk the manual checklist. If every item passes, mark verdict as "
            "PASS in the report. Issues found → revise and re-run critique."
        )
    else:
        report.verdict = VERDICT_NEEDS_REVISION

    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("artifact", help="path to the artifact (SVG/PNG/PDF)")
    ap.add_argument("--threshold", type=float, default=8.0,
                    help="WCAG contrast threshold (default: 8.0)")
    ap.add_argument("--target", default=None,
                    help="named dimension target (e.g., 'og-image', 'paper-2col')")
    ap.add_argument("--audience", default=None,
                    help="audience profile tag (see style-guides.md)")
    ap.add_argument("--channel", default="science",
                    help="channel slug; matches a `channels/<slug>.md` front-matter "
                         "block when present (see channels/SCHEMA.md). Unknown "
                         "channels skip the front-matter gate and run universal checks only.")
    ap.add_argument("--output", "-o", default=None,
                    help="write Markdown report to this path "
                         "(default: stdout)")
    args = ap.parse_args()

    report = critique_artifact(
        args.artifact,
        threshold=args.threshold,
        target=args.target,
        audience=args.audience,
        channel=args.channel,
    )
    md = report.as_markdown()
    if args.output:
        Path(args.output).write_text(md)
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        print(md)
    sys.exit(report.exit_code())


if __name__ == "__main__":
    main()
