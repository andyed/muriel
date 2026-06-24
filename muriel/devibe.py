"""
muriel.devibe — anti-AI-tell design audit for web/UI source.

The visual analogue of :mod:`muriel.aiism`. Where aiism flags the prose tics
that mark a passage as AI-drafted, devibe flags the *design* defaults that mark
a site as vibe-coded (AI-built): the untouched shadcn/Tailwind look, AI-purple
as the primary colour, gradient-filled headings, unprompted neon glow,
emoji-as-icons, the centred hero + three-feature-card skeleton — and the 2026
"tasteful default" (cream background + serif display + sage accent) that the
previous wave of anti-slop advice converged on, which now reads as AI just as
fast as the purple gradient did.

Two things make this muriel's tool rather than a straight port:

1. **Re-ranked for muriel's own risk.** The cream + serif + sage combination
   leads the catalogue as an ``error`` — not because it is the loudest complaint
   in the source data (the old purple default still is) but because it is the
   look muriel, and Claude's house style generally, is most likely to emit on
   autopilot. A tool should flag the default *you* reach for.

2. **8:1 cross-check.** devibe knows about :mod:`muriel.contrast`. When a colour
   tell captures a concrete hex (AI-purple as primary, neon-on-dark), devibe
   also reports whether that colour clears muriel's 8:1 floor on muriel's two
   canonical backgrounds (paper ``#ffffff``, OLED ``#0a0a0f``). Tailwind's
   default indigo (``#6366f1``), for instance, is both a "nobody chose this"
   tell *and* a 4.47:1 fail on white against muriel's 8:1 floor — two reasons to
   replace it, not one. This is the thing the source scanner cannot do; muriel
   can.

Rule data is derived from ``JCarterJohnson/vibecoded-design-tells`` (MIT) — a
Reddit-mined ranking of the visual tells of AI-built sites (3.2M posts / 3,033
on-topic comments across 47 subreddits). Because that repo is MIT, its rules are
safe to derive from here, unlike the CC-BY-SA prose lists removed from aiism in
0.10.0. Severities are remapped to muriel's ``info``/``warn``/``error`` triple.

What it cannot see: layout coherence, spacing rhythm, alignment, text overflow.
Those are a large part of why a page reads as AI and a regex cannot catch them —
check them by eye (source repo's ``tells.md`` §10).

Usage
-----

Programmatic::

    from muriel.devibe import audit_path, audit_source
    for f in audit_path("src/"):
        print(f.file, f.line, f.severity, f.rule, f.message)

CLI::

    python -m muriel.devibe src/                  # scan a dir or file
    python -m muriel.devibe src/ --severity error # exit 1 only on error-tier
    python -m muriel.devibe page.html --json      # machine-readable, for CI
    python -m muriel.devibe src/ --no-contrast    # skip the 8:1 cross-check

Exit status: 0 = clean (or only findings below ``--severity``), 1 = findings at
or above the configured severity, 2 = usage error.

A tell is an *unspecified default*, not a banned colour. Mark a line with
``unslop-ignore`` or ``muriel-ignore`` when a flagged value is a deliberate
decision and devibe will skip it — so the audit stays trustworthy and does not
nag about a chosen brand colour.

devibe also distinguishes *committing* a tell from *quoting* one: the displayed
content of ``<pre>``/``<code>`` samples and HTML comments is blanked before the
scan, so a page that shows an AI-purple hex or the gradient-text CSS to teach it
(this toolkit's own docs are the motivating case) is not flagged for it. Tag
attributes are still read — a tell on a ``<code>`` element's own class is real
chrome and still fires.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

SEVERITIES = ("info", "warn", "error")
_SEV_ORDER = {s: i for i, s in enumerate(SEVERITIES)}
_SEV_WEIGHT = {"info": 1, "warn": 2, "error": 3}

# File types worth scanning, and trees/products to skip. Mirrors the source
# scanner: generated/vendored output and minified bundles carry no design
# intent, so auditing them only produces noise.
EXTS = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx",
        ".ts", ".tsx", ".vue", ".svelte", ".astro", ".mdx"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "vendor",
             "coverage", ".svelte-kit", ".astro", ".turbo", ".cache",
             "__pycache__", "site-build"}

# Lines carrying either marker are an explicit human decision; skip them.
_IGNORE_MARKERS = ("unslop-ignore", "muriel-ignore")

# muriel's two canonical backgrounds, used by the 8:1 cross-check: paper white
# for light figures/sites, OLED near-black for the universal dark default.
_CANONICAL_BACKGROUNDS = (("#fff", "#ffffff"), ("#0a0a0f", "#0a0a0f"))


# ---------------------------------------------------------------------------
# Rule table
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Rule:
    id: str
    label: str
    severity: str               # info | warn | error
    fix: str
    patterns: tuple[str, ...]
    suppress: str | None = None     # if this matches the line, the rule is skipped
    contrast_hex: bool = False      # try to extract a hex and run the 8:1 check
    combo_key: str | None = None    # tag for the cream+serif+sage combo synthesis


# Ordered worst-first for readability; the report re-sorts by severity anyway.
# Severity is muriel's re-rank: the cream/serif/sage combo is elevated to error
# (it is muriel's own house-style risk); otherwise the data ranking holds —
# shadcn defaults, AI-purple, and gradient text are the top concrete tells.
RULES: tuple[Rule, ...] = (
    # ── error: the strongest signals + muriel's own default ──────────────
    Rule("shadcn-default-card",
         "Untouched shadcn default Card / theme tokens", "error",
         "Theme the tokens (primary, radius, neutrals, spacing) before building. "
         "The stock defaults are the giveaway, not shadcn itself.",
         (r"rounded-lg\s+border\s+bg-card\s+text-card-foreground\s+shadow-sm",
          r"\"baseColor\"\s*:\s*\"(slate|zinc|gray|neutral|stone)\"",
          r"--radius\s*:\s*0\.5rem")),
    Rule("ai-purple",
         "AI purple / indigo / violet as the primary colour", "error",
         "Pick a brand colour outside the violet/indigo/purple band. It is "
         "Tailwind's default, so it reads as 'nobody chose this'.",
         (r"\b(bg|text|from|via|to|border|ring|fill|stroke|decoration|outline)-(indigo|violet|purple|fuchsia)-(400|500|600|700|800)\b",
          r"#(6366f1|4f46e5|818cf8|7c3aed|6d28d9|8b5cf6|a855f7|9333ea|7e22ce|c026d3|d946ef)\b"),
         contrast_hex=True),
    Rule("gradient-text",
         "Gradient-filled text (heading / hero)", "error",
         "Solid colour on headings and copy. Gradient body text is one of the "
         "strongest single AI tells — almost no deliberate brand does it.",
         (r"bg-clip-text\s+[^\"'`]*text-transparent",
          r"text-transparent\s+[^\"'`]*bg-clip-text",
          r"-webkit-background-clip\s*:\s*text",
          r"\bbackground-clip\s*:\s*text")),

    # ── warn: real defaults, weaker or noisier than the top three ────────
    Rule("cream-page-bg",
         "Cream / beige 'tasteful default' page background", "warn",
         "The 2026 tell, not the fix. Anchor the page colour to the real brand "
         "or a reference. If cream is a genuine decision, mark it unslop-ignore.",
         (r"#(faf8f5|f5f1e8|f3eee3|fdfbf7|f7f3ec|faf6ef|f6f1e7|fbf7f0|f4efe4)\b",
          r"\bbg-(stone|amber|orange)-(50|100)\b"),
         combo_key="cream"),
    Rule("serif-display-default",
         "Overexposed 'tasteful' serif display face", "warn",
         "Instrument Serif / Fraunces / Playfair are the new autopilot 'I tried "
         "to pick a tasteful font' default. Choose type for a reason, ideally "
         "not these for the headline that sets the whole tone.",
         (r"\b(Instrument\s*Serif|Fraunces|Playfair\s*Display|Cormorant|Spectral|DM\s*Serif)\b",),
         combo_key="serif"),
    Rule("purple-blue-gradient",
         "Purple-to-blue / pink gradient", "warn",
         "Default to solid fills. If you must gradient, keep stops analogous and "
         "low-contrast, never the rainbow purple-to-blue.",
         (r"from-(purple|violet|indigo|fuchsia)-\d+\s+(via-[a-z]+-\d+\s+)?to-(blue|indigo|pink|cyan|sky)-\d+",
          r"linear-gradient\([^)]*#(6366f1|7c3aed|8b5cf6|a855f7)[^)]*\)")),
    Rule("hero-three-cards",
         "Centred hero + three-feature-card grid skeleton", "warn",
         "Break the grid: asymmetric hero with a real product screenshot; vary "
         "sections instead of stacking identical 3-up icon cards.",
         (r"grid-cols-1\s+(sm:grid-cols-2\s+)?md:grid-cols-3",)),
    Rule("generic-sans-font",
         "Generic default sans (Inter / Geist / Roboto)", "warn",
         "The 'I didn't pick a font' default. Choose a typeface with character "
         "and pair a display + body face for a reason.",
         (r"font-family\s*:\s*['\"]?(Inter|Geist|Roboto)\b",
          r"\b(Inter|Geist|Geist_Mono|Roboto)\s*\(",
          r"fontFamily\s*:\s*\{[^}]*['\"](Inter|Geist|Roboto)")),
    Rule("neon-glow",
         "Unprompted neon glow shadow", "warn",
         "Remove glow you did not deliberately design. Dark mode should rely on "
         "contrast and spacing, not glow.",
         (r"shadow-\[0_0_",
          r"drop-shadow-\[0_0_",
          r"text-shadow\s*:[^;]*\d+px[^;]*(rgba|#|hsl)",
          r"box-shadow\s*:[^;]*\b0\s+0\s+\d{2,}px"),
         contrast_hex=True),

    # ── info: minor / noisier signals — fix if cheap, do not over-rotate ─
    Rule("sage-accent",
         "Sage / forest-green 'tasteful default' accent", "info",
         "Part of the cream+serif+sage house look. Fine as a stated brand "
         "decision; a tell when it is the colour the model reached for.",
         (r"#(15573a|1a4d3a)\b",
          r"\b(bg|text|border|ring|from|to)-(emerald|green)-(700|800|900)\b"),
         combo_key="sage"),
    Rule("rounded-everything",
         "Large rounded corners / pill buttons everywhere", "info",
         "Use a small, intentional radius scale by role. Not everything "
         "maximally rounded; pills only occasionally.",
         (r"\brounded-(2xl|3xl|full)\b",
          r"border-radius\s*:\s*(999\d*px|9999px)"),
         # rounded-full on a small box is a status dot / avatar / icon, not a
         # pill button — skip those sizes.
         suppress=r"\b[hw]-(\d|10|11|12|14|16)(\.5)?\b"),
    Rule("fade-in-animations",
         "Boilerplate fade-in / hover-grow / scroll animation", "info",
         "Motion only when it communicates state; gate behind "
         "prefers-reduced-motion. If every section animates the same way, cut it.",
         (r"initial=\{\{\s*opacity:\s*0",
          r"whileInView",
          r"whileHover=\{\{\s*scale",
          r"data-aos\s*=",
          r"\bhover:scale-1\d{2}\b")),
    Rule("emoji-as-icons",
         "Emoji used as icons / section bullets", "info",
         "Use a real SVG icon set (Lucide / Phosphor / Heroicons) or none. "
         "Emoji standing in for UI icons signals low effort.",
         (r"[\U0001F680✨⚡\U0001F525\U0001F4A1\U0001F512✅\U0001F3AF\U0001F31F\U0001F6E1\U0001F4C8\U0001F511\U0001F389]",)),
    Rule("hype-copy",
         "Generated marketing-copy cliche", "info",
         "Say what the product literally does, with specifics. Cut the template "
         "hype words.",
         (r"\bTransform your\b", r"\bSupercharge\b", r"\bUnleash\b",
          r"\bEffortlessly\b", r"\breimagined\b",
          r"take your [^.]{0,30}to the next level", r"\bGame-?changer\b")),
    Rule("stock-illustration",
         "Generic blob / stock illustration source", "info",
         "Use real screenshots or commissioned art instead of undraw-style blobs.",
         (r"\bundraw\b", r"\bstoryset\b", r"\bdrawkit\b")),
)

# Compile once.
_COMPILED: list[tuple[Rule, list[re.Pattern], re.Pattern | None]] = [
    (r,
     [re.compile(p, re.IGNORECASE) for p in r.patterns],
     re.compile(r.suppress, re.IGNORECASE) if r.suppress else None)
    for r in RULES
]


@dataclass
class Finding:
    file: str
    line: int
    column: int
    severity: str
    rule: str
    message: str
    excerpt: str

    def __lt__(self, other: "Finding") -> bool:
        # Worst-first, then by location, so the report leads with the strongest
        # tell (the cream/serif/sage combo and the error tier) rather than
        # whatever happens to appear on line 1.
        return (
            (-_SEV_ORDER[self.severity], self.file, self.line, self.column, self.rule)
            < (-_SEV_ORDER[other.severity], other.file, other.line, other.column, other.rule)
        )


# ---------------------------------------------------------------------------
# 8:1 cross-check (muriel's differentiator)
# ---------------------------------------------------------------------------

_HEX6_RE = re.compile(r"#?\b([0-9a-fA-F]{6})\b")


def _contrast_note(matched: str) -> str:
    """If ``matched`` contains a concrete 6-digit hex, report whether it clears
    muriel's 8:1 floor on the two canonical backgrounds. Returns a note to
    append to the finding message, or ``""`` if no hex / contrast unavailable.

    This is the join between devibe and :mod:`muriel.contrast`: a default colour
    that also fails 8:1 is two problems, and the second is muriel's mandate."""
    m = _HEX6_RE.search(matched)
    if not m:
        return ""
    hex_str = "#" + m.group(1).lower()
    try:
        from muriel.contrast import contrast_ratio
    except Exception:
        return ""
    fails = []
    for label, bg in _CANONICAL_BACKGROUNDS:
        try:
            ratio = contrast_ratio(hex_str, bg)
        except ValueError:
            continue
        if ratio < 8.0:
            fails.append(f"{ratio:.2f}:1 on {label}")
    if not fails:
        return ""
    return " · also fails muriel 8:1 as text (" + ", ".join(fails) + ")"


# ---------------------------------------------------------------------------
# Displayed-code masking
# ---------------------------------------------------------------------------
# A design tell is something a page *commits* in its own chrome, not something
# it *quotes*. Documentation that teaches the tells — muriel's own docs are the
# motivating case — necessarily shows AI-purple hexes, the gradient-text CSS,
# and the fonts-to-avoid by name inside <pre>/<code> samples and HTML comments.
# Reading those as chrome makes a tells-teaching site fail its own scanner. So
# before the per-line scan, blank the *content* of <pre>/<code> spans and HTML
# comments while keeping their tags and attributes intact (a tell on a <code>
# element's own class is still real chrome), along with the file's line and
# column geometry so findings still point at the right place.

_CODE_REGION_RE = re.compile(
    r"(<pre\b[^>]*>)(.*?)(</pre>)|(<code\b[^>]*>)(.*?)(</code>)",
    re.IGNORECASE | re.DOTALL,
)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _blank(s: str) -> str:
    """Replace every character with a space, preserving newlines so downstream
    line numbers and column offsets are unchanged."""
    return "".join("\n" if c == "\n" else " " for c in s)


def _mask_displayed_code(text: str) -> str:
    """Blank the displayed *content* of <pre>/<code> spans and HTML comments,
    leaving their tags/attributes and the file's line/column geometry intact.
    Quoted code documents a tell; it does not commit one."""
    def repl(m: "re.Match[str]") -> str:
        if m.group(1) is not None:                            # <pre> … </pre>
            return m.group(1) + _blank(m.group(2)) + m.group(3)
        return m.group(4) + _blank(m.group(5)) + m.group(6)   # <code> … </code>
    masked = _CODE_REGION_RE.sub(repl, text)
    return _HTML_COMMENT_RE.sub(lambda m: _blank(m.group(0)), masked)


# ---------------------------------------------------------------------------
# Core audit
# ---------------------------------------------------------------------------

def audit_source(text: str, filename: str = "<string>", *, contrast: bool = True) -> list[Finding]:
    """Scan one source string for design tells. Per-line regex rules plus a
    file-level synthesis for the cream + serif + sage combination (the source
    repo's rule: any two of the three is the strong signal)."""
    lines = text.split("\n")
    # Minified bundle: one enormous line. No design intent to read here.
    if len(lines) == 1 and len(lines[0]) > 5000:
        return []

    # Scan against a copy with displayed code/comments blanked, so a page that
    # *quotes* a tell (a docs sample, a code block) is not read as committing
    # one. Excerpts and the unslop-ignore check still use the original line.
    scan_lines = _mask_displayed_code(text).split("\n")

    findings: list[Finding] = []
    combo_hits: dict[str, Finding] = {}     # combo_key -> first finding seen

    for i, (raw, scan) in enumerate(zip(lines, scan_lines), start=1):
        if any(marker in raw.lower() for marker in _IGNORE_MARKERS):
            continue
        for rule, regexes, suppress in _COMPILED:
            if suppress is not None and suppress.search(scan):
                continue
            for rx in regexes:
                m = rx.search(scan)
                if not m:
                    continue
                col = m.start() + 1
                message = rule.fix
                if contrast and rule.contrast_hex:
                    message += _contrast_note(m.group(0))
                f = Finding(filename, i, col, rule.severity, rule.id,
                            message, raw.strip()[:160])
                findings.append(f)
                if rule.combo_key and rule.combo_key not in combo_hits:
                    combo_hits[rule.combo_key] = f
                break  # one finding per rule per line

    # Cream + serif + sage: two of the three co-occurring in a file is the
    # 2026 "tasteful default" — muriel's own house-style risk. Elevate to a
    # single error that leads the report.
    if len(combo_hits) >= 2:
        present = sorted(combo_hits)
        anchor = min(combo_hits.values(), key=lambda f: (f.line, f.column))
        findings.append(Finding(
            filename, anchor.line, anchor.column, "error", "tasteful-default-combo",
            f"Tasteful-default look: {' + '.join(present)} co-occur in this file. "
            "This is the cream/serif/sage house style Reddit now clocks as AI on "
            "sight. Anchor colour and type to the real brand or a reference; if it "
            "is a genuine warm-editorial decision, mark the lines unslop-ignore.",
            anchor.excerpt))

    findings.sort()  # worst-first, so the combo / error tier leads
    return findings


def audit_path(path: str | Path, *, contrast: bool = True) -> list[Finding]:
    """Scan a file or directory tree. Returns findings sorted worst-first."""
    findings: list[Finding] = []
    for fp in _iter_files(Path(path)):
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        findings += audit_source(text, str(fp), contrast=contrast)
    findings.sort()
    return findings


def _iter_files(path: Path):
    if path.is_file():
        yield path
        return
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith((".min.js", ".min.css")):
                continue
            if Path(f).suffix.lower() in EXTS:
                yield Path(root) / f


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def vibe_score(findings: list[Finding]) -> int:
    """Weighted total (error=3, warn=2, info=1), as in the source scanner."""
    return sum(_SEV_WEIGHT[f.severity] for f in findings)


def verdict(findings: list[Finding]) -> str:
    by_sev = {s: sum(1 for f in findings if f.severity == s) for s in SEVERITIES}
    score = vibe_score(findings)
    if by_sev["error"] >= 3 or score >= 15:
        return "STRONG AI-default look"
    if by_sev["error"] >= 1 or score >= 6:
        return "Some AI defaults present"
    if score > 0:
        return "Mostly clean, minor tells"
    return "Clean — no design tells detected"


_SEV_GLYPH = {"info": "·", "warn": "!", "error": "X"}
_SEV_ANSI = {"info": "\033[90m", "warn": "\033[33m", "error": "\033[31m"}
_RESET = "\033[0m"


def format_findings(findings: list[Finding], *, color: bool = True) -> str:
    if not findings:
        return "clean — no design tells detected."
    by_sev = {s: 0 for s in SEVERITIES}
    by_rule: dict[str, int] = {}
    lines = []
    for f in findings:
        by_sev[f.severity] += 1
        by_rule[f.rule] = by_rule.get(f.rule, 0) + 1
        glyph = _SEV_GLYPH[f.severity]
        sev = (f"{_SEV_ANSI[f.severity]}{glyph} {f.severity}{_RESET}"
               if color else f"{glyph} {f.severity}")
        loc = f"{f.file}:{f.line}:{f.column}"
        lines.append(f"  {loc}")
        lines.append(f"      {sev:<14} {f.rule:<24} {f.message}")
        lines.append(f"      > {f.excerpt[:110]}")
    summary = (f"\n{by_sev['error']} error · {by_sev['warn']} warn · "
               f"{by_sev['info']} info  "
               f"({len(findings)} total, {len(by_rule)} rules, "
               f"vibe score {vibe_score(findings)})")
    by_rule_lines = "\n".join(
        f"  {n:>3}  {rule}" for rule, n in sorted(by_rule.items(), key=lambda kv: -kv[1])
    )
    tail = ("\n\nLayout, spacing, and overflow tells need eyes — a regex cannot "
            "see them. Eyeball the hero layout and section rhythm too.")
    return (f"verdict: {verdict(findings)}\n\n"
            + "\n".join(lines) + summary
            + "\n\nrule counts:\n" + by_rule_lines + tail)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="muriel.devibe",
                                description=__doc__.split("\n\n")[0])
    p.add_argument("path", help="file or directory to scan")
    p.add_argument("--severity", choices=SEVERITIES, default="warn",
                   help="exit nonzero if any finding is at or above this severity "
                        "(default: warn)")
    p.add_argument("--no-contrast", action="store_true",
                   help="skip the muriel 8:1 cross-check on colour tells")
    p.add_argument("--no-color", action="store_true", help="disable ANSI colour")
    p.add_argument("--rule", action="append",
                   help="filter to specific rule id (repeatable)")
    p.add_argument("--json", action="store_true",
                   help="emit findings as JSON for tool integration")
    args = p.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"path not found: {target}", file=sys.stderr)
        return 2

    findings = audit_path(target, contrast=not args.no_contrast)
    if args.rule:
        wanted = set(args.rule)
        findings = [f for f in findings if f.rule in wanted]

    if args.json:
        payload = {
            "path": str(target),
            "verdict": verdict(findings),
            "vibe_score": vibe_score(findings),
            "summary": {s: sum(1 for f in findings if f.severity == s)
                        for s in SEVERITIES} | {"total": len(findings)},
            "findings": [
                {"file": f.file, "line": f.line, "column": f.column,
                 "severity": f.severity, "rule": f.rule,
                 "message": f.message, "excerpt": f.excerpt}
                for f in findings
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_findings(findings, color=not args.no_color))

    if not findings:
        return 0
    threshold = _SEV_ORDER[args.severity]
    worst = max(_SEV_ORDER[f.severity] for f in findings)
    return 1 if worst >= threshold else 0


# Alias for the ``muriel <subcommand>`` dispatcher, which calls ``_main``.
_main = main


if __name__ == "__main__":
    sys.exit(main())
