"""
muriel.uipromax — the ui-ux-pro-max design-knowledge corpus, re-gated to 8:1.

A verbatim MIT port of the CSV reference data from ``nextlevelbuilder/
ui-ux-pro-max-skill`` (via ``All-The-Vibes/ATV-Design``). Seven tables under
``data/*.csv`` (see ``LICENSE.txt``):

    colors          161 product-type → semantic colour sets (shadcn-shaped)
    typography       73 font pairings with mood keywords + Google Fonts URLs
    ui-reasoning    161 UI category → pattern / effects / anti-patterns rules
    ux-guidelines    99 do/don't rules with good + bad code examples
    styles           84 design styles (Swiss, neumorphism, …) with metadata
    charts           25 data-type → chart-type taxonomy with a11y fallbacks
    icons           105 Phosphor icon index

muriel's universal rules OVERRIDE the source's. The colour sets target WCAG
3:1/AA, so they are re-gated here against muriel's **8:1** floor via
:mod:`muriel.contrast`. The data ships unmodified — this module is the
muriel-native accessor layer plus the contrast gate; it contributes no
colours of its own.

The gate is the *body-text* pairs (Foreground/Background, Card text): most
sets clear 8:1 there, and :func:`palettes` with ``meeting_floor=True`` returns
those. Their *interactive* pairs (button labels on saturated brand colours,
muted-on-muted) mostly sit below 8:1 — that's a per-button decision the source
leaves at WCAG 3:1/AA — so they are reported by :func:`regate_palette` and
``muriel uipromax audit`` rather than failing the set.

The ``charts`` table is supplementary to ``channels/charts.md`` — that channel
stays canonical for muriel chart work; this is the compact decision matrix
with the source's accessibility-fallback column.

Usage
-----

::

    from muriel import uipromax
    uipromax.palettes(meeting_floor=True)        # sets that clear 8:1
    uipromax.regate_palette(uipromax.colors()[0])  # per-pair ratios
    uipromax.font_pairings(query="luxury")
    uipromax.anti_patterns(query="saas")

CLI::

    muriel uipromax                  # corpus summary + the 8:1 headline
    muriel uipromax audit            # per-palette 8:1 pass/fail
    muriel uipromax colors --meeting-floor
    muriel uipromax fonts --query editorial

Zero deps: stdlib ``csv`` + :func:`muriel.contrast.contrast_ratio`.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

try:
    from muriel.contrast import contrast_ratio
except Exception:  # pragma: no cover - contrast is core, stay defensive
    contrast_ratio = None  # type: ignore[assignment]


_DATA = Path(__file__).resolve().parent / "data"

# muriel's universal contrast floor. The source targets WCAG 3:1/AA; this is
# the gate every ported palette is measured against.
MURIEL_MIN_CONTRAST = 8.0

# Logical table name → CSV stem.
_TABLES = {
    "colors":        "colors",
    "typography":    "typography",
    "ui_reasoning":  "ui-reasoning",
    "ux_guidelines": "ux-guidelines",
    "styles":        "styles",
    "charts":        "charts",
    "icons":         "icons",
}

# Body-text pairs — the muriel 8:1 gate. These are the foreground/surface
# pairs muriel's "8:1 on all text" rule actually governs (running copy).
_BODY_TEXT_PAIRS = [
    ("Foreground", "Background"),
    ("Card Foreground", "Card"),
]

# Interactive / de-emphasized pairs — reported, not gated. Saturated brand
# colours rarely clear 8:1 with a legible label (On Accent/Accent ≈ 3:1 even
# in good palettes), and muted-on-muted is intentionally low-contrast. These
# are per-button decisions, so they inform rather than fail the set.
_UI_TEXT_PAIRS = [
    ("On Primary", "Primary"),
    ("On Secondary", "Secondary"),
    ("On Accent", "Accent"),
    ("On Destructive", "Destructive"),
    ("Muted Foreground", "Muted"),
]

_ALL_PAIRS = _BODY_TEXT_PAIRS + _UI_TEXT_PAIRS
_BODY_SET = set(_BODY_TEXT_PAIRS)


# ─── Raw table access ──────────────────────────────────────────────────────


def table(name: str) -> list[dict[str, str]]:
    """Load one corpus table as a list of row dicts (verbatim CSV)."""
    if name not in _TABLES:
        raise KeyError(f"unknown uipromax table {name!r}; expected one of {sorted(_TABLES)}")
    path = _DATA / f"{_TABLES[name]}.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _cell_text(v) -> str:
    """Searchable text for a DictReader cell. Ragged rows (a stray comma puts
    overflow fields in a list under the None key) are flattened, not crashed."""
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return " ".join(_cell_text(x) for x in v)
    return str(v)


def _query(rows: list[dict], q: Optional[str]) -> list[dict]:
    """Case-insensitive substring filter across all column values."""
    if not q:
        return rows
    ql = q.lower()
    return [r for r in rows if any(ql in _cell_text(v).lower() for v in r.values())]


def colors(query: Optional[str] = None) -> list[dict]:
    """Product-type → semantic colour sets."""
    return _query(table("colors"), query)


def font_pairings(query: Optional[str] = None) -> list[dict]:
    """Heading/body font pairings with mood keywords."""
    return _query(table("typography"), query)


def ui_reasoning(query: Optional[str] = None) -> list[dict]:
    """UI category → recommended pattern / effects / anti-patterns."""
    return _query(table("ui_reasoning"), query)


def ux_guidelines(query: Optional[str] = None) -> list[dict]:
    """Do/don't UX rules with good + bad code examples."""
    return _query(table("ux_guidelines"), query)


def styles(query: Optional[str] = None) -> list[dict]:
    """Design styles (Swiss, neumorphism, …) with metadata."""
    return _query(table("styles"), query)


def chart_types(query: Optional[str] = None) -> list[dict]:
    """Data-type → chart-type taxonomy with accessibility fallbacks."""
    return _query(table("charts"), query)


def icons(query: Optional[str] = None) -> list[dict]:
    """Phosphor icon index."""
    return _query(table("icons"), query)


def anti_patterns(query: Optional[str] = None) -> list[dict[str, str]]:
    """Flatten the ui-reasoning + ux-guidelines tables into a critique-shaped
    list of ``{category, anti_pattern, severity, source}`` rows.

    The muriel-native view consumed by :mod:`muriel.critique` — the negative
    rules ("don't") the corpus encodes, in one place.
    """
    out: list[dict[str, str]] = []
    for r in _query(ui_reasoning(), query):
        ap = (r.get("Anti_Patterns") or "").strip()
        if ap:
            out.append({
                "category": r.get("UI_Category", ""),
                "anti_pattern": ap,
                "severity": r.get("Severity", ""),
                "source": "ui-reasoning",
            })
    for r in _query(ux_guidelines(), query):
        dont = (r.get("Don't") or "").strip()
        if dont:
            out.append({
                "category": f"{r.get('Category', '')} / {r.get('Issue', '')}".strip(" /"),
                "anti_pattern": dont,
                "severity": r.get("Severity", ""),
                "source": "ux-guidelines",
            })
    return out


# ─── Contrast re-gate ──────────────────────────────────────────────────────


@dataclass
class PaletteAudit:
    """Per-pair 8:1 audit of one colour set.

    ``meets_floor`` reflects muriel's text gate — the *body-text* pairs only.
    Interactive pairs (button labels, muted text) are recorded in ``ratios``
    and ``ui_failing`` for transparency but do not fail the set.
    """

    product_type: str
    ratios: dict[str, float]   # "On Primary/Primary" → ratio (all pairs)
    body_failing: list[str]    # body-text pairs below the floor (the gate)
    ui_failing: list[str]      # interactive/muted pairs below the floor (info)

    @property
    def meets_floor(self) -> bool:
        return not self.body_failing


def regate_palette(row: dict, floor: float = MURIEL_MIN_CONTRAST) -> PaletteAudit:
    """Measure a colour-set row's text pairs against muriel's 8:1 floor.

    Body-text pairs gate the set; interactive/muted pairs are reported only.
    """
    if contrast_ratio is None:  # pragma: no cover
        raise RuntimeError("muriel.contrast unavailable — cannot re-gate palettes")
    ratios: dict[str, float] = {}
    body_failing: list[str] = []
    ui_failing: list[str] = []
    for fg_col, bg_col in _ALL_PAIRS:
        fg, bg = row.get(fg_col), row.get(bg_col)
        if not fg or not bg:
            continue
        try:
            r = contrast_ratio(fg, bg)
        except Exception:
            continue
        label = f"{fg_col}/{bg_col}"
        ratios[label] = round(r, 2)
        if r < floor:
            (body_failing if (fg_col, bg_col) in _BODY_SET else ui_failing).append(label)
    return PaletteAudit(row.get("Product Type", ""), ratios, body_failing, ui_failing)


def palettes(
    meeting_floor: bool = False, floor: float = MURIEL_MIN_CONTRAST
) -> list[dict]:
    """Colour sets, optionally filtered to those clearing muriel's 8:1 floor.

    With ``meeting_floor=False`` (default) returns every set verbatim; with
    ``True`` returns only sets whose text pairs all clear ``floor``.
    """
    rows = colors()
    if not meeting_floor:
        return rows
    return [r for r in rows if regate_palette(r, floor).meets_floor]


def audit_palettes(floor: float = MURIEL_MIN_CONTRAST) -> list[PaletteAudit]:
    """Re-gate every colour set; return the per-set audits."""
    return [regate_palette(r, floor) for r in colors()]


# ─── CLI ────────────────────────────────────────────────────────────────────


def _print_summary() -> None:
    counts = {name: len(table(name)) for name in _TABLES}
    audits = audit_palettes()
    body_ok = sum(1 for a in audits if a.meets_floor)
    print("muriel uipromax — ui-ux-pro-max corpus (MIT, re-gated to 8:1)\n")
    width = max(len(n) for n in counts)
    for name, n in counts.items():
        print(f"  {name:<{width}}  {n:>4} rows")
    print(
        f"\n  8:1 body text: {body_ok}/{len(audits)} colour sets clear muriel's "
        f"8:1 floor on\n  Foreground/Background + Card text. Their interactive "
        f"pairs (On Primary,\n  On Accent, …) target the source's WCAG 3:1/AA — "
        f"see `uipromax audit`.\n"
    )
    print("Subcommands: audit | colors | fonts | reasoning | guidelines | "
          "styles | charts | icons   [--query STR] [--meeting-floor]")


def _print_audit() -> None:
    audits = audit_palettes()
    body_ok = [a for a in audits if a.meets_floor]
    print(f"8:1 re-gate of {len(audits)} colour sets\n")
    print("sets clearing 8:1, per text pair:")
    for fg_col, bg_col in _ALL_PAIRS:
        label = f"{fg_col}/{bg_col}"
        present = [a for a in audits if label in a.ratios]
        passing = sum(1 for a in present if a.ratios[label] >= MURIEL_MIN_CONTRAST)
        tag = "  (muriel text gate)" if (fg_col, bg_col) in _BODY_SET else ""
        print(f"  {label:<28} {passing:>3}/{len(present)}{tag}")
    print(
        f"\nbody-text gate (Foreground/Background + Card Foreground/Card): "
        f"{len(body_ok)}/{len(audits)} sets clear 8:1."
    )
    print("  → usable as muriel starting points; re-gate each button/accent "
          "pair (`On *`) by hand —")
    print("    darken the label or enlarge the type until it clears 8:1.")


_LIST_TABLES = {
    "colors": colors, "fonts": font_pairings, "typography": font_pairings,
    "reasoning": ui_reasoning, "guidelines": ux_guidelines, "styles": styles,
    "charts": chart_types, "icons": icons,
}

# A short, legible column per table for the CLI list view.
_LIST_LABEL = {
    "colors": "Product Type", "fonts": "Font Pairing Name",
    "typography": "Font Pairing Name", "reasoning": "UI_Category",
    "guidelines": "Issue", "styles": "Style Category",
    "charts": "Data Type", "icons": "Icon Name",
}


def _main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    if args and args[0] in ("-h", "--help", "help"):
        _print_summary()
        return 0
    if not args:
        _print_summary()
        return 0

    sub = args[0]
    rest = args[1:]
    query: Optional[str] = None
    meeting_floor = False
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--query" and i + 1 < len(rest):
            query = rest[i + 1]
            i += 2
            continue
        if a == "--meeting-floor":
            meeting_floor = True
            i += 1
            continue
        print(f"muriel uipromax: unknown argument {a!r}", file=sys.stderr)
        return 2

    if sub == "audit":
        _print_audit()
        return 0
    if sub in ("colors",) and meeting_floor:
        rows = palettes(meeting_floor=True)
        rows = _query(rows, query)
    elif sub in _LIST_TABLES:
        rows = _LIST_TABLES[sub](query)
    else:
        print(f"muriel uipromax: unknown subcommand {sub!r}", file=sys.stderr)
        _print_summary()
        return 2

    label = _LIST_LABEL.get(sub, "")
    print(f"{sub}: {len(rows)} row(s)" + (f" matching {query!r}" if query else ""))
    for r in rows:
        name = r.get(label, "") or next(iter(r.values()), "")
        print(f"  • {name}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
