"""
muriel.styleguide — brand style guide schema, loader, and token tools.

Style guides are a **schema** for brand design tokens — colors, typography,
assets, ownership rules — serialized as TOML and importable into any
muriel operation. Lets a muriel task pick up a brand's tokens without
reinventing them and without violating ownership rules like "this brand
is owned elsewhere, don't regenerate here."

The schema is a superset of what marginalia's ``--mg-*`` custom
properties cover, with room for brand-specific extras (ring gradients,
fractal fills, section accents, logo template paths, export commands).

Usage
-----

::

    from muriel.styleguide import load_styleguide

    sg = load_styleguide("examples/example-brand.toml")
    sg.meta.name                      # → 'Acme Research'
    sg.colors.background              # → '#0a0a0f'
    sg.colors.accent                  # → '#d2b06a'
    sg.colors.rings["r1"].color       # → '#91d7f8'
    sg.typography.display_family      # → 'Nunito'
    sg.assets.wordmark_template       # → 'templates/logo-wordmark.html'
    sg.rules.never_rebuild_image_generation_elsewhere  # → True

    # Contrast audit of the whole palette against the brand background
    for name, ratio, passes in sg.audit_contrast(required=8.0):
        mark = '✓' if passes else '✗'
        print(f'  {mark} {name:<20} {ratio:5.2f}:1')

    # Generate a matplotlib rcparams dict from the brand
    rc = sg.to_matplotlibrc()
    import matplotlib as mpl
    mpl.rcParams.update(rc)

    # Generate a CSS custom-property block
    print(sg.to_css_vars(prefix='--brand-'))

    # Respect ownership rules — raises if an operation is forbidden
    sg.rules.check('regenerate-wordmark')   # raises RuleViolation

CLI
---

::

    python -m muriel.styleguide examples/example-brand.toml
    python -m muriel.styleguide examples/example-brand.toml --css
    python -m muriel.styleguide examples/example-brand.toml --contrast

Schema
------

A brand.toml has six top-level tables. Only ``[meta]`` (name) and
``[colors]`` (background, foreground) are required; everything else is
optional.

- ``[meta]``: ``name``, ``slug``, ``version``, ``owner_repo``,
  ``owner_path``, ``canonical_source``, ``ownership_rule``
- ``[colors]``: ``background``, ``foreground``, plus any of
  ``background_2``, ``background_3``, ``foreground_muted``, ``accent``,
  ``accent_ink``, ``note``, ``tip``, ``warning``, ``important``
- ``[colors.rings]``: ring gradient as ``{r1 = { color, width_px }, …}``
- ``[colors.accents]``: named brand accents as ``{name = hex, …}``
- ``[typography]``: ``display_family``, ``display_weight``,
  ``display_line_height``, ``display_letter_spacing_em``,
  ``body_family``, ``mono_family``, ``paint_order``
- ``[assets]``: ``wordmark_template``, ``monogram_template``,
  ``fractal_fill_default``, ``fractal_fills = [...]``
- ``[dependencies]``: free-form, e.g. ``google_fonts = [...]``
- ``[export]``: free-form string commands, e.g. ``cmd_all = "npm run export"``
- ``[rules]``: boolean invariants. Reserved: ``never_modify_sources``,
  ``never_rebuild_image_generation_elsewhere``, ``brand_owner``. Extra
  keys are allowed and stored in ``rules.custom``.

See ``muriel/examples/example-brand.toml`` and
``muriel/examples/muriel-brand.toml`` for worked examples.

Dependencies
------------

Uses ``tomllib`` from the Python 3.11+ standard library. No external
dependencies.
"""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

__all__ = [
    # Types
    "Ring", "Colors", "Typography", "Motion", "Meta", "Assets", "Rules",
    "StyleGuide", "RuleViolation",
    # Loader
    "load_styleguide",
]


# ─── Types ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Ring:
    """One stop in a brand ring gradient (color + stroke width in pixels)."""
    color: str
    width_px: int


@dataclass(frozen=True)
class Colors:
    """
    Brand color tokens. Only ``background`` and ``foreground`` are
    required. Everything else is optional and may be None.

    The rings + accents dicts are brand-specific extras — any number of
    named entries for complex palettes.

    Two-tier schema
    ---------------
    Raw colors live at the top level (``background``, ``foreground``,
    ``accent``, etc.). The semantic layer lives in ``aliases`` — a dict
    mapping role names (``text``, ``decorative``, ``surface-primary``,
    ``semantic-note``) to either a raw-color name or a direct hex value.
    The alias layer is what contrast audits should consult for text
    roles; raw colors can be used directly but don't declare intent.
    """
    background: str
    foreground: str
    # Optional marginalia/matplotlib-compatible extras
    background_2: Optional[str] = None
    background_3: Optional[str] = None
    foreground_muted: Optional[str] = None
    accent: Optional[str] = None
    accent_ink: Optional[str] = None
    accent_decorative: Optional[str] = None  # decorative-only (exempt from 8:1 text rule)
    note: Optional[str] = None
    tip: Optional[str] = None
    warning: Optional[str] = None
    important: Optional[str] = None
    # Brand-specific
    rings: dict[str, Ring] = field(default_factory=dict)
    accents: dict[str, str] = field(default_factory=dict)
    # Semantic alias layer — {role: raw-name-or-hex}
    aliases: dict[str, str] = field(default_factory=dict)

    def resolve_alias(self, role: str) -> Optional[str]:
        """
        Resolve a semantic role (e.g. 'text', 'decorative') to a hex color.

        Looks up ``role`` in ``aliases``. If the value matches a raw-color
        field name on this dataclass, returns that field's value. If the
        value starts with ``#``, returns it as-is. Returns ``None`` if
        the role isn't defined.
        """
        target = self.aliases.get(role)
        if target is None:
            return None
        if target.startswith("#"):
            return target
        # Treat as a raw-color name
        if hasattr(self, target):
            return getattr(self, target)
        return None

    def text_roles(self) -> dict[str, str]:
        """Return a dict of {role_name: color} for roles meant as body text."""
        result: dict[str, str] = {"foreground": self.foreground}
        for name in (
            "foreground_muted", "accent", "accent_ink",
            "note", "tip", "warning", "important",
        ):
            value = getattr(self, name)
            if value is not None:
                result[name] = value
        return result


@dataclass(frozen=True)
class Typography:
    """Brand typography tokens."""
    display_family: Optional[str] = None
    display_weight: Optional[int] = None
    display_line_height: Optional[float] = None
    display_letter_spacing_em: Optional[float] = None
    body_family: Optional[str] = None
    mono_family: Optional[str] = None
    paint_order: Optional[str] = None


@dataclass(frozen=True)
class Meta:
    """Brand identity and provenance."""
    name: str
    slug: Optional[str] = None
    version: Optional[str] = None
    owner_repo: Optional[str] = None
    owner_path: Optional[str] = None
    canonical_source: Optional[str] = None
    ownership_rule: Optional[str] = None


@dataclass(frozen=True)
class Motion:
    """
    Brand motion tokens — durations (ms) and easing curves.

    Durations are integers in milliseconds; 0 means "no animation."
    Easings are either CSS cubic-bezier strings or keywords (``linear``,
    ``ease``, ``ease-in``, etc.). Consumed by the kinetic-typography,
    interactive, and video channels.

    ``motion_preference`` is a string flag. The canonical value
    ``"respect-prefers-reduced-motion"`` signals that consumers should
    collapse all durations to 0 when the OS-level reduced-motion
    preference is set.
    """
    duration_instant: int = 0
    duration_fast:    int = 120
    duration_normal:  int = 240
    duration_slow:    int = 480
    duration_reveal:  int = 800
    easing_default:   str = "cubic-bezier(0.2, 0.0, 0.2, 1.0)"
    easing_emphasis:  str = "cubic-bezier(0.4, 0.0, 0.2, 1.0)"
    easing_snappy:    str = "cubic-bezier(0.6, 0.0, 0.2, 1.0)"
    easing_linear:    str = "linear"
    motion_preference: str = "respect-prefers-reduced-motion"


@dataclass(frozen=True)
class Assets:
    """File paths (relative to the brand guide's owner_path) for brand assets."""
    wordmark_template: Optional[str] = None
    monogram_template: Optional[str] = None
    fractal_fill_default: Optional[str] = None
    fractal_fills: tuple[str, ...] = ()


class RuleViolation(RuntimeError):
    """Raised when an operation violates a brand rule."""


@dataclass(frozen=True)
class Rules:
    """
    Brand invariants. Reserved booleans are enforced by ``check()``;
    any extra keys are stored in ``custom`` without enforcement.
    """
    never_modify_sources: bool = False
    never_rebuild_image_generation_elsewhere: bool = False
    brand_owner: Optional[str] = None
    custom: dict[str, Any] = field(default_factory=dict)

    def check(self, operation: str) -> None:
        """
        Raise ``RuleViolation`` if ``operation`` is forbidden by a rule.

        Operations that trigger ``never_rebuild_image_generation_elsewhere``:
        anything containing ``'wordmark'``, ``'monogram'``, ``'logo'``,
        ``'favicon'``, or ``'brand-asset'`` in the name.

        Operations that trigger ``never_modify_sources``: anything containing
        ``'modify-source'``, ``'filter-source'``, or ``'blur-source'``.

        Parameters
        ----------
        operation : str
            A short identifier for the operation being attempted.
        """
        op = operation.lower()
        image_gen_ops = (
            "wordmark", "monogram", "logo", "favicon", "brand-asset",
            "app-icon", "regenerate-image",
        )
        source_ops = ("modify-source", "filter-source", "blur-source")

        if self.never_rebuild_image_generation_elsewhere:
            if any(k in op for k in image_gen_ops):
                owner = self.brand_owner or "the canonical brand guide"
                raise RuleViolation(
                    f"Operation {operation!r} is owned by {owner} and cannot "
                    f"be performed here. Use the owner's export pipeline instead."
                )
        if self.never_modify_sources:
            if any(k in op for k in source_ops):
                raise RuleViolation(
                    f"Operation {operation!r} would modify brand source files, "
                    f"which is forbidden by the brand rules."
                )


# ─── Main StyleGuide dataclass ───────────────────────────────────────────

@dataclass(frozen=True)
class StyleGuide:
    """
    A parsed brand style guide. Load via ``load_styleguide(path)``.

    Immutable so the same StyleGuide can be safely passed between
    functions without anyone mutating its tokens mid-operation.
    """
    meta: Meta
    colors: Colors
    typography: Typography
    motion: Motion
    assets: Assets
    rules: Rules
    dependencies: dict[str, Any]
    export: dict[str, str]
    source_path: Path

    # ─── Derived outputs ────────────────────────────────────────────────

    def to_matplotlibrc(self) -> dict[str, Any]:
        """
        Generate a matplotlib rcparams dict from brand colors.

        Mirrors the structure of ``muriel.matplotlibrc_dark.PARAMS``
        so the output can be passed directly to ``mpl.rcParams.update()``
        or ``plt.rc_context()``.

        Fonts default to the brand's ``body_family`` for ``font.family``
        if defined. Sizes follow the same conservative defaults as
        matplotlibrc_dark (14pt body, 16pt title, 10×6 figsize).
        """
        bg = self.colors.background
        fg = self.colors.foreground
        grid = self.colors.foreground_muted or self.colors.background_2 or "#3a3a4a"

        params: dict[str, Any] = {
            # Figure sizing
            "figure.figsize":       (10, 6),
            "figure.dpi":            120,
            "savefig.dpi":           300,
            "savefig.bbox":         "tight",
            "savefig.transparent":   False,
            # Typography
            "font.family":          "sans-serif",
            "font.size":             14,
            "axes.titlesize":        16,
            "axes.labelsize":        14,
            "xtick.labelsize":       12,
            "ytick.labelsize":       12,
            "legend.fontsize":       12,
            "figure.titlesize":      18,
            "font.weight":          "regular",
            # Palette
            "figure.facecolor":     bg,
            "axes.facecolor":       bg,
            "savefig.facecolor":    bg,
            "axes.edgecolor":       fg,
            "axes.labelcolor":      fg,
            "xtick.color":          fg,
            "ytick.color":          fg,
            "text.color":           fg,
            "grid.color":           grid,
            "grid.linewidth":        0.6,
            "grid.alpha":            1.0,
            # Axes
            "axes.linewidth":        1.2,
            "axes.grid":             True,
            "axes.grid.axis":       "y",
            "axes.axisbelow":        True,
            "axes.spines.top":       False,
            "axes.spines.right":     False,
            # Ticks
            "xtick.direction":      "out",
            "ytick.direction":      "out",
            "xtick.major.size":      5,
            "ytick.major.size":      5,
            "xtick.major.width":     1.2,
            "ytick.major.width":     1.2,
            # Lines
            "lines.linewidth":       2.0,
            "lines.markersize":      7,
            "patch.linewidth":       1.0,
            # Legend
            "legend.frameon":        True,
            "legend.framealpha":     0.9,
            "legend.edgecolor":     grid,
            "legend.facecolor":     self.colors.background_2 or bg,
        }
        if self.typography.body_family:
            params["font.family"] = self.typography.body_family.split(",")[0].strip("'\" ")
        if self.typography.mono_family:
            params["font.monospace"] = self.typography.mono_family
        return params

    def to_css_vars(self, prefix: str = "--brand-") -> str:
        """
        Generate a CSS ``:root`` block with custom properties for every
        defined brand color. Ring stops render as ``--brand-ring-{name}``
        and accents as ``--brand-accent-{name}``.

        Parameters
        ----------
        prefix : str
            The custom-property prefix. Defaults to ``'--brand-'``. Use
            ``'--mg-'`` to target marginalia overrides, though colors may
            not map 1:1.
        """
        lines = [":root {"]
        c = self.colors
        mapping = [
            ("bg",               c.background),
            ("bg2",              c.background_2),
            ("bg3",              c.background_3),
            ("fg",               c.foreground),
            ("fg-muted",         c.foreground_muted),
            ("accent",           c.accent),
            ("accent-ink",       c.accent_ink),
            ("note",             c.note),
            ("tip",              c.tip),
            ("warning",          c.warning),
            ("important",        c.important),
        ]
        for key, value in mapping:
            if value is not None:
                lines.append(f"  {prefix}{key}: {value};")
        for name, ring in c.rings.items():
            lines.append(f"  {prefix}ring-{name}: {ring.color};")
            lines.append(f"  {prefix}ring-{name}-width: {ring.width_px}px;")
        for name, value in c.accents.items():
            lines.append(f"  {prefix}accent-{name}: {value};")
        lines.append("}")
        return "\n".join(lines)

    def audit_contrast(
        self, required: float = 8.0,
    ) -> list[tuple[str, float, bool]]:
        """
        Check every text-role color against ``colors.background`` using
        WCAG 2.1 contrast ratio. Returns a list of ``(role, ratio, passes)``
        tuples.

        Parameters
        ----------
        required : float
            Minimum contrast ratio. Default 8.0 (muriel's universal rule).

        Returns
        -------
        list[tuple[str, float, bool]]
            One entry per text role that's defined on the brand. Use for
            both programmatic checks and human-readable audits.
        """
        from .contrast import contrast_ratio

        results: list[tuple[str, float, bool]] = []
        bg = self.colors.background
        for role, color in self.colors.text_roles().items():
            if role == "foreground":
                # The foreground color IS the text baseline; still worth
                # reporting its ratio
                pass
            try:
                ratio = contrast_ratio(color, bg)
            except Exception:
                continue
            results.append((role, ratio, ratio >= required))
        # Also audit named accents if present
        for name, color in self.colors.accents.items():
            try:
                ratio = contrast_ratio(color, bg)
            except Exception:
                continue
            results.append((f"accent.{name}", ratio, ratio >= required))
        return results

    def describe(self) -> str:
        """Return a short human-readable summary of the style guide."""
        lines = [
            f"Style Guide: {self.meta.name}"
            + (f" v{self.meta.version}" if self.meta.version else ""),
            f"  source:    {self.source_path}",
        ]
        if self.meta.owner_repo:
            lines.append(f"  owner:     {self.meta.owner_repo}")
        if self.meta.canonical_source:
            lines.append(f"  canonical: {self.meta.canonical_source}")

        lines.append("")
        lines.append("  Colors:")
        lines.append(f"    bg={self.colors.background}  fg={self.colors.foreground}")
        for field_name in ("accent", "accent_ink", "note", "tip", "warning", "important"):
            value = getattr(self.colors, field_name)
            if value:
                lines.append(f"    {field_name:<14} {value}")
        if self.colors.rings:
            lines.append(f"    rings: {len(self.colors.rings)} stops")
        if self.colors.accents:
            lines.append(f"    accents: {len(self.colors.accents)} named — "
                         f"{', '.join(sorted(self.colors.accents))}")

        if self.typography.display_family:
            lines.append("")
            lines.append("  Typography:")
            lines.append(
                f"    display: {self.typography.display_family} "
                f"{self.typography.display_weight or ''}"
            )
            if self.typography.body_family:
                lines.append(f"    body:    {self.typography.body_family}")

        if self.assets.wordmark_template or self.assets.monogram_template:
            lines.append("")
            lines.append("  Assets:")
            if self.assets.wordmark_template:
                lines.append(f"    wordmark: {self.assets.wordmark_template}")
            if self.assets.monogram_template:
                lines.append(f"    monogram: {self.assets.monogram_template}")
            if self.assets.fractal_fills:
                lines.append(f"    fills:    {len(self.assets.fractal_fills)} available")

        if self.rules.never_rebuild_image_generation_elsewhere:
            lines.append("")
            lines.append(f"  ⚠ Brand owner: {self.rules.brand_owner or '(unspecified)'}")
            lines.append(f"    Image generation locked to the owner's pipeline.")

        return "\n".join(lines)


# ─── Loader ──────────────────────────────────────────────────────────────

def load_styleguide(path: Union[str, Path]) -> StyleGuide:
    """
    Load a brand.toml style guide from disk into a frozen ``StyleGuide``.

    Parameters
    ----------
    path : str or Path
        Path to the TOML file.

    Returns
    -------
    StyleGuide
        A fully parsed, immutable style guide.

    Raises
    ------
    FileNotFoundError
        If the path doesn't exist.
    ValueError
        If required fields are missing (``meta.name``,
        ``colors.background``, ``colors.foreground``).
    tomllib.TOMLDecodeError
        If the file is not valid TOML.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"style guide not found: {p}")
    with p.open("rb") as f:
        data = tomllib.load(f)

    # ── meta ────────────────────────────────────────────────────────────
    meta_data = data.get("meta", {})
    if "name" not in meta_data:
        raise ValueError(f"{p}: [meta] is missing required field 'name'")
    meta = Meta(
        name=meta_data["name"],
        slug=meta_data.get("slug"),
        version=meta_data.get("version"),
        owner_repo=meta_data.get("owner_repo"),
        owner_path=meta_data.get("owner_path"),
        canonical_source=meta_data.get("canonical_source"),
        ownership_rule=meta_data.get("ownership_rule"),
    )

    # ── colors ──────────────────────────────────────────────────────────
    colors_data = data.get("colors", {})
    for required in ("background", "foreground"):
        if required not in colors_data:
            raise ValueError(
                f"{p}: [colors] is missing required field {required!r}"
            )
    rings_raw = colors_data.get("rings", {})
    rings: dict[str, Ring] = {}
    for key, value in rings_raw.items():
        if isinstance(value, dict) and "color" in value and "width_px" in value:
            rings[key] = Ring(color=value["color"], width_px=int(value["width_px"]))
    accents_raw = colors_data.get("accents", {})
    accents: dict[str, str] = {
        k: v for k, v in accents_raw.items() if isinstance(v, str)
    }
    aliases_raw = colors_data.get("aliases", {})
    aliases: dict[str, str] = {
        k: v for k, v in aliases_raw.items() if isinstance(v, str)
    }

    colors = Colors(
        background=colors_data["background"],
        foreground=colors_data["foreground"],
        background_2=colors_data.get("background_2"),
        background_3=colors_data.get("background_3"),
        foreground_muted=colors_data.get("foreground_muted"),
        accent=colors_data.get("accent"),
        accent_ink=colors_data.get("accent_ink"),
        accent_decorative=colors_data.get("accent_decorative"),
        note=colors_data.get("note"),
        tip=colors_data.get("tip"),
        warning=colors_data.get("warning"),
        important=colors_data.get("important"),
        rings=rings,
        accents=accents,
        aliases=aliases,
    )

    # ── typography ──────────────────────────────────────────────────────
    typo_data = data.get("typography", {})
    typography = Typography(
        display_family=typo_data.get("display_family"),
        display_weight=typo_data.get("display_weight"),
        display_line_height=typo_data.get("display_line_height"),
        display_letter_spacing_em=typo_data.get("display_letter_spacing_em"),
        body_family=typo_data.get("body_family"),
        mono_family=typo_data.get("mono_family"),
        paint_order=typo_data.get("paint_order"),
    )

    # ── motion ──────────────────────────────────────────────────────────
    motion_data = data.get("motion", {})
    motion = Motion(
        duration_instant=int(motion_data.get("duration_instant", 0)),
        duration_fast=int(motion_data.get("duration_fast", 120)),
        duration_normal=int(motion_data.get("duration_normal", 240)),
        duration_slow=int(motion_data.get("duration_slow", 480)),
        duration_reveal=int(motion_data.get("duration_reveal", 800)),
        easing_default=motion_data.get("easing_default", "cubic-bezier(0.2, 0.0, 0.2, 1.0)"),
        easing_emphasis=motion_data.get("easing_emphasis", "cubic-bezier(0.4, 0.0, 0.2, 1.0)"),
        easing_snappy=motion_data.get("easing_snappy", "cubic-bezier(0.6, 0.0, 0.2, 1.0)"),
        easing_linear=motion_data.get("easing_linear", "linear"),
        motion_preference=motion_data.get("motion_preference", "respect-prefers-reduced-motion"),
    )

    # ── assets ──────────────────────────────────────────────────────────
    assets_data = data.get("assets", {})
    assets = Assets(
        wordmark_template=assets_data.get("wordmark_template"),
        monogram_template=assets_data.get("monogram_template"),
        fractal_fill_default=assets_data.get("fractal_fill_default"),
        fractal_fills=tuple(assets_data.get("fractal_fills", [])),
    )

    # ── rules ───────────────────────────────────────────────────────────
    rules_data = data.get("rules", {})
    reserved = {
        "never_modify_sources",
        "never_rebuild_image_generation_elsewhere",
        "brand_owner",
    }
    custom = {k: v for k, v in rules_data.items() if k not in reserved}
    rules = Rules(
        never_modify_sources=bool(rules_data.get("never_modify_sources", False)),
        never_rebuild_image_generation_elsewhere=bool(
            rules_data.get("never_rebuild_image_generation_elsewhere", False)
        ),
        brand_owner=rules_data.get("brand_owner"),
        custom=custom,
    )

    dependencies = dict(data.get("dependencies", {}))
    export = {k: str(v) for k, v in data.get("export", {}).items()}

    return StyleGuide(
        meta=meta,
        colors=colors,
        typography=typography,
        motion=motion,
        assets=assets,
        rules=rules,
        dependencies=dependencies,
        export=export,
        source_path=p,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────

def _main(argv: Optional[list[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m muriel.styleguide",
        description=(
            "Load a brand.toml style guide and inspect its tokens, or "
            "generate derivative outputs (CSS, matplotlibrc) from it."
        ),
    )
    parser.add_argument("path", type=Path, help="Path to a brand.toml file")
    parser.add_argument(
        "--css", action="store_true",
        help="Print the brand as a CSS :root custom-property block.",
    )
    parser.add_argument(
        "--css-prefix", default="--brand-",
        help="Prefix for CSS custom properties. Default: --brand-",
    )
    parser.add_argument(
        "--contrast", action="store_true",
        help="Run a WCAG contrast audit of every color against the background.",
    )
    parser.add_argument(
        "--required", type=float, default=8.0,
        help="Contrast threshold for --contrast. Default: 8.0 (muriel's rule)",
    )
    args = parser.parse_args(argv)

    try:
        sg = load_styleguide(args.path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except tomllib.TOMLDecodeError as exc:
        print(f"error: invalid TOML in {args.path}: {exc}", file=sys.stderr)
        return 2

    print()
    print(sg.describe())

    if args.css:
        print()
        print(f"── CSS (prefix: {args.css_prefix}) ──")
        print(sg.to_css_vars(prefix=args.css_prefix))

    if args.contrast:
        print()
        print(f"── WCAG contrast audit (required: {args.required:.1f}:1) ──")
        results = sg.audit_contrast(required=args.required)
        fail_count = 0
        for role, ratio, passes in results:
            mark = "✓" if passes else "✗"
            status = "PASS" if passes else "FAIL"
            print(f"  {mark} {status}  {role:<22} {ratio:6.2f}:1")
            if not passes:
                fail_count += 1
        if fail_count:
            print()
            print(f"  {fail_count} role(s) failed the {args.required:.1f}:1 rule")
            return 1

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
