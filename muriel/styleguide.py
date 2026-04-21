"""
muriel.styleguide — brand style guide schema v2, loader, and token tools.

Style guides are a **schema** for brand design tokens — colors, typography,
spacing, radii, elevation, motion, iconography, imagery, logo lockups,
voice, and accessibility floors — serialized as TOML and importable into
any muriel operation.

v2 scope
--------

Beyond v1's colors + typography families + motion + assets + rules:

- **Structural tokens** — `[spacing]`, `[radii]`, `[elevation]` scales.
- **Type scale** — `[typography.scale]` with named roles (display, h1–h6,
  body, body_small, caption, label, mono), each with size / weight /
  line-height / tracking.
- **Semantic states** — `[semantic]` replaces the ad-hoc note/tip/warning/
  important fields in colors with proper {text, surface, border} trios
  for success / error / warning / info / neutral.
- **Data-viz palette** — `[viz]` with categorical / sequential / diverging
  ordered color lists for the science and heatmaps channels.
- **Logo variants** — `[logo]` with wordmark / monogram / stacked /
  horizontal sub-tables, each a template + svg + png path trio, plus
  clear-space and minimum-size rules.
- **Iconography** — `[iconography]` with family, stroke width, default
  size, and available sizes list.
- **Imagery** — `[imagery]` with free-form style descriptor, treatments
  list, and a crop-policy hook that smartcrop consumes
  (`preserve-faces`, `preserve-text`, `energy-only`).
- **Voice** — `[voice]` with adjectives, say-yes / say-no examples for
  the editorial channels.
- **Accessibility floors** — `[a11y]` with min_contrast_ratio,
  min_hit_target_px, focus_ring_color, focus_ring_width_px,
  motion_reduce_policy. Overrides muriel's universal 8:1 default when
  a brand wants to tighten (or relax).

Usage
-----

::

    from muriel.styleguide import load_styleguide

    sg = load_styleguide("examples/muriel-brand.toml")
    sg.meta.name                              # → 'muriel'
    sg.colors.background                      # → '#0a0a0f'
    sg.semantic["success"].text               # → '#66bb6a'
    sg.viz.categorical                        # → ('#e6e4d2', '#50b4c8', ...)
    sg.typography.scale["h1"].size            # → 40
    sg.spacing["md"]                          # → 16
    sg.radii["lg"]                            # → 16
    sg.logo.wordmark.svg                      # → 'templates/logo-wordmark.svg'
    sg.voice.adjectives                       # → ('precise', 'unhurried', ...)
    sg.a11y.min_contrast_ratio                # → 8.0

Contrast audit honours the brand's own ``a11y.min_contrast_ratio`` when
unset by the caller::

    for name, ratio, passes in sg.audit_contrast():
        ...

CLI
---

::

    muriel styleguide examples/muriel-brand.toml
    muriel styleguide examples/muriel-brand.toml --css
    muriel styleguide examples/muriel-brand.toml --contrast

Dependencies
------------

``tomllib`` from the Python 3.11+ standard library. No external deps.
"""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

__all__ = [
    # Types
    "Ring", "Colors",
    "TextRole", "Typography",
    "Motion", "Meta",
    "LogoVariant", "Logo",
    "Iconography", "Imagery",
    "Voice", "A11y",
    "SemanticState",
    "Viz",
    "Assets", "Rules",
    "StyleGuide", "RuleViolation",
    # Loader
    "load_styleguide",
]


# ─── Colors ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Ring:
    """One stop in a brand ring gradient (color + stroke width in pixels)."""
    color: str
    width_px: int


@dataclass(frozen=True)
class Colors:
    """
    Raw color palette + aliases. Semantic states live in ``StyleGuide.semantic``
    (separate dataclass); this layer is for the raw neutrals + brand accents
    plus an aliases table mapping role names to raw-color names or hex values.
    """
    background: str
    foreground: str
    background_2: Optional[str] = None
    background_3: Optional[str] = None
    foreground_muted: Optional[str] = None
    accent: Optional[str] = None
    accent_ink: Optional[str] = None
    accent_decorative: Optional[str] = None
    rings: dict[str, Ring] = field(default_factory=dict)
    named: dict[str, str] = field(default_factory=dict)   # free-form brand accents
    aliases: dict[str, str] = field(default_factory=dict) # role → raw-name-or-hex

    def resolve_alias(self, role: str) -> Optional[str]:
        """Resolve a semantic role to a hex color. Returns None if unknown."""
        target = self.aliases.get(role)
        if target is None:
            return None
        if target.startswith("#"):
            return target
        if hasattr(self, target):
            v = getattr(self, target)
            if isinstance(v, str):
                return v
        if target in self.named:
            return self.named[target]
        return None

    def text_roles(self) -> dict[str, str]:
        """Raw-color roles that should clear the text contrast floor."""
        result: dict[str, str] = {"foreground": self.foreground}
        for name in ("foreground_muted", "accent", "accent_ink"):
            value = getattr(self, name)
            if value is not None:
                result[name] = value
        return result


# ─── Typography ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TextRole:
    """A named slot in the type scale (display, h1, body, caption, …)."""
    size: float
    weight: int = 400
    line_height: float = 1.4
    tracking_em: float = 0.0
    upper: bool = False


@dataclass(frozen=True)
class Typography:
    """Font stacks + a named type scale."""
    display_family: Optional[str] = None
    display_weight: Optional[int] = None
    display_line_height: Optional[float] = None
    display_letter_spacing_em: Optional[float] = None
    body_family: Optional[str] = None
    mono_family: Optional[str] = None
    paint_order: Optional[str] = None
    scale: dict[str, TextRole] = field(default_factory=dict)


# ─── Motion ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Motion:
    """Duration tokens (ms) + easing curves. Consumed by kinetic/interactive/video."""
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


# ─── Iconography + Imagery ───────────────────────────────────────────────

@dataclass(frozen=True)
class Iconography:
    """Icon family / style tokens."""
    family: Optional[str] = None            # 'custom', 'phosphor', 'heroicons', ...
    stroke_px: Optional[float] = None
    default_size: Optional[int] = None
    sizes: tuple[int, ...] = ()


@dataclass(frozen=True)
class Imagery:
    """
    Photography / illustration style tokens.

    ``crop_policy`` is consumed by smartcrop: 'preserve-faces',
    'preserve-text', 'preserve-both', or 'energy-only'.
    """
    style: Optional[str] = None             # free-form style descriptor
    treatments: tuple[str, ...] = ()        # e.g. 'muted-duotone', 'cream-wash'
    crop_policy: str = "energy-only"


# ─── Logo ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LogoVariant:
    """A single lockup (wordmark / monogram / stacked / horizontal)."""
    template: Optional[str] = None
    svg: Optional[str] = None
    png: Optional[str] = None


@dataclass(frozen=True)
class Logo:
    """Logo variants + clear-space and minimum-size rules."""
    clear_space_em: float = 1.0
    min_width_px: int = 64
    wordmark:   LogoVariant = field(default_factory=LogoVariant)
    monogram:   LogoVariant = field(default_factory=LogoVariant)
    stacked:    LogoVariant = field(default_factory=LogoVariant)
    horizontal: LogoVariant = field(default_factory=LogoVariant)


# ─── Voice ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Voice:
    """Editorial voice — adjectives + do/don't examples for marginalia + prose."""
    adjectives: tuple[str, ...] = ()
    say_yes: tuple[str, ...] = ()
    say_no:  tuple[str, ...] = ()


# ─── Semantic states ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class SemanticState:
    """A UI-feedback state expressed as a {text, surface, border} trio."""
    text: str
    surface: Optional[str] = None
    border: Optional[str] = None


# ─── Viz ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Viz:
    """Data-viz palettes for the science and heatmaps channels."""
    categorical: tuple[str, ...] = ()
    sequential:  tuple[str, ...] = ()
    diverging:   tuple[str, ...] = ()


# ─── A11y ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class A11y:
    """
    Per-brand accessibility floors.

    ``motion_reduce_policy`` values: ``'collapse-to-zero'``, ``'keep-fast'``,
    ``'keep-linear'``.

    ``focus_ring_color`` may be a hex value, a raw-color name from
    ``[colors]``, or a named accent from ``[colors.named]``.
    """
    min_contrast_ratio: float = 8.0
    min_hit_target_px: int = 44
    focus_ring_color: Optional[str] = None
    focus_ring_width_px: int = 3
    motion_reduce_policy: str = "collapse-to-zero"


# ─── Meta / Assets / Rules ───────────────────────────────────────────────

@dataclass(frozen=True)
class Meta:
    """Brand identity + provenance."""
    name: str
    slug: Optional[str] = None
    version: Optional[str] = None
    owner_repo: Optional[str] = None
    owner_path: Optional[str] = None
    canonical_source: Optional[str] = None
    ownership_rule: Optional[str] = None


@dataclass(frozen=True)
class Assets:
    """Non-logo asset paths (relative to owner_path)."""
    fractal_fill_default: Optional[str] = None
    fractal_fills: tuple[str, ...] = ()


class RuleViolation(RuntimeError):
    """Raised when an operation violates a brand rule."""


@dataclass(frozen=True)
class Rules:
    """
    Brand invariants. Reserved booleans are enforced by ``check()``;
    extras are stored in ``custom`` without enforcement.
    """
    never_modify_sources: bool = False
    never_rebuild_image_generation_elsewhere: bool = False
    brand_owner: Optional[str] = None
    custom: dict[str, Any] = field(default_factory=dict)

    def check(self, operation: str) -> None:
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
    """A parsed brand style guide. Load via ``load_styleguide(path)``."""

    meta: Meta
    colors: Colors
    semantic: dict[str, SemanticState]
    viz: Viz
    typography: Typography
    spacing: dict[str, int]
    radii: dict[str, int]
    elevation: dict[str, str]
    motion: Motion
    iconography: Iconography
    imagery: Imagery
    logo: Logo
    voice: Voice
    a11y: A11y
    assets: Assets
    rules: Rules
    dependencies: dict[str, Any]
    export: dict[str, str]
    source_path: Path

    # ─── Derived outputs ────────────────────────────────────────────────

    def to_matplotlibrc(self) -> dict[str, Any]:
        """Generate a matplotlib rcparams dict from brand tokens."""
        bg = self.colors.background
        fg = self.colors.foreground
        grid = self.colors.foreground_muted or self.colors.background_2 or "#3a3a4a"

        body_size = (self.typography.scale.get("body").size
                     if "body" in self.typography.scale else 14)
        title_size = (self.typography.scale.get("h2").size
                      if "h2" in self.typography.scale else 16)

        params: dict[str, Any] = {
            "figure.figsize":       (10, 6),
            "figure.dpi":            120,
            "savefig.dpi":           300,
            "savefig.bbox":         "tight",
            "savefig.transparent":   False,
            "font.family":          "sans-serif",
            "font.size":             body_size,
            "axes.titlesize":        title_size,
            "axes.labelsize":        body_size,
            "xtick.labelsize":       body_size - 2,
            "ytick.labelsize":       body_size - 2,
            "legend.fontsize":       body_size - 2,
            "figure.titlesize":      title_size + 2,
            "font.weight":          "regular",
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
            "axes.linewidth":        1.2,
            "axes.grid":             True,
            "axes.grid.axis":       "y",
            "axes.axisbelow":        True,
            "axes.spines.top":       False,
            "axes.spines.right":     False,
            "xtick.direction":      "out",
            "ytick.direction":      "out",
            "xtick.major.size":      5,
            "ytick.major.size":      5,
            "xtick.major.width":     1.2,
            "ytick.major.width":     1.2,
            "lines.linewidth":       2.0,
            "lines.markersize":      7,
            "patch.linewidth":       1.0,
            "legend.frameon":        True,
            "legend.framealpha":     0.9,
            "legend.edgecolor":     grid,
            "legend.facecolor":     self.colors.background_2 or bg,
        }
        if self.typography.body_family:
            params["font.family"] = self.typography.body_family.split(",")[0].strip("'\" ")
        if self.typography.mono_family:
            params["font.monospace"] = self.typography.mono_family
        # Brand-bound viz palette — matplotlib's default color cycle.
        # ``cycler`` ships with matplotlib; guard so the rest of the rc
        # dict is usable even when matplotlib isn't installed.
        if self.viz.categorical:
            try:
                from matplotlib import cycler
                params["axes.prop_cycle"] = cycler(color=list(self.viz.categorical))
            except ImportError:
                params["axes.prop_cycle_colors"] = list(self.viz.categorical)
        return params

    def to_css_vars(self, prefix: str = "--brand-") -> str:
        """Emit a CSS ``:root`` block covering every brand token."""
        lines = [":root {"]
        c = self.colors

        # Raw colors
        for key, value in (
            ("bg", c.background), ("bg2", c.background_2), ("bg3", c.background_3),
            ("fg", c.foreground), ("fg-muted", c.foreground_muted),
            ("accent", c.accent), ("accent-ink", c.accent_ink),
            ("accent-decorative", c.accent_decorative),
        ):
            if value is not None:
                lines.append(f"  {prefix}{key}: {value};")
        for name, value in c.named.items():
            lines.append(f"  {prefix}named-{name}: {value};")
        for name, ring in c.rings.items():
            lines.append(f"  {prefix}ring-{name}: {ring.color};")
            lines.append(f"  {prefix}ring-{name}-width: {ring.width_px}px;")

        # Semantic states
        for state_name, state in self.semantic.items():
            lines.append(f"  {prefix}{state_name}-text: {state.text};")
            if state.surface is not None:
                lines.append(f"  {prefix}{state_name}-surface: {state.surface};")
            if state.border is not None:
                lines.append(f"  {prefix}{state_name}-border: {state.border};")

        # Spacing / radii / elevation
        for k, v in self.spacing.items():
            lines.append(f"  {prefix}space-{k}: {v}px;")
        for k, v in self.radii.items():
            lines.append(f"  {prefix}radius-{k}: {v}px;")
        for k, v in self.elevation.items():
            lines.append(f"  {prefix}shadow-{k}: {v};")

        # Motion
        m = self.motion
        for k in ("instant", "fast", "normal", "slow", "reveal"):
            lines.append(f"  {prefix}duration-{k}: {getattr(m, f'duration_{k}')}ms;")
        for k in ("default", "emphasis", "snappy", "linear"):
            lines.append(f"  {prefix}ease-{k}: {getattr(m, f'easing_{k}')};")

        # Type scale
        for role_name, role in self.typography.scale.items():
            size = int(role.size) if role.size == int(role.size) else role.size
            lines.append(f"  {prefix}type-{role_name}-size: {size}px;")
            lines.append(f"  {prefix}type-{role_name}-weight: {role.weight};")
            lines.append(f"  {prefix}type-{role_name}-line-height: {role.line_height};")
            if role.tracking_em:
                lines.append(f"  {prefix}type-{role_name}-tracking: {role.tracking_em}em;")

        # A11y hooks
        a = self.a11y
        if a.focus_ring_color:
            lines.append(f"  {prefix}focus-ring: {a.focus_ring_color};")
        lines.append(f"  {prefix}focus-ring-width: {a.focus_ring_width_px}px;")
        lines.append(f"  {prefix}min-hit-target: {a.min_hit_target_px}px;")

        lines.append("}")
        return "\n".join(lines)

    def audit_contrast(
        self, required: Optional[float] = None,
    ) -> list[tuple[str, float, bool]]:
        """
        WCAG-2.1 contrast audit of every text-bearing role against
        ``colors.background``. If ``required`` is None, falls back to
        ``a11y.min_contrast_ratio`` (the per-brand floor).
        """
        from .contrast import contrast_ratio

        threshold = required if required is not None else self.a11y.min_contrast_ratio
        results: list[tuple[str, float, bool]] = []
        bg = self.colors.background

        for role, color in self.colors.text_roles().items():
            try:
                ratio = contrast_ratio(color, bg)
            except Exception:
                continue
            results.append((role, ratio, ratio >= threshold))

        # Named brand accents (often used as text)
        for name, color in self.colors.named.items():
            try:
                ratio = contrast_ratio(color, bg)
            except Exception:
                continue
            results.append((f"named.{name}", ratio, ratio >= threshold))

        # Semantic state text colors — the canonical "will users read this?" check.
        for state_name, state in self.semantic.items():
            try:
                ratio = contrast_ratio(state.text, bg)
            except Exception:
                continue
            results.append((f"semantic.{state_name}", ratio, ratio >= threshold))

        return results

    def describe(self) -> str:
        """Human-readable summary of the style guide."""
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
        for name in ("accent", "accent_ink", "accent_decorative"):
            v = getattr(self.colors, name)
            if v:
                lines.append(f"    {name:<18} {v}")
        if self.colors.rings:
            lines.append(f"    rings: {len(self.colors.rings)} stops")
        if self.colors.named:
            lines.append(f"    named: {len(self.colors.named)} — "
                         f"{', '.join(sorted(self.colors.named))}")

        if self.semantic:
            lines.append("")
            lines.append("  Semantic states:")
            for name, state in self.semantic.items():
                lines.append(f"    {name:<10} text={state.text}")

        if self.viz.categorical or self.viz.sequential or self.viz.diverging:
            lines.append("")
            lines.append("  Data viz:")
            if self.viz.categorical:
                lines.append(f"    categorical: {len(self.viz.categorical)} colors")
            if self.viz.sequential:
                lines.append(f"    sequential:  {len(self.viz.sequential)} stops")
            if self.viz.diverging:
                lines.append(f"    diverging:   {len(self.viz.diverging)} stops")

        if self.typography.display_family or self.typography.scale:
            lines.append("")
            lines.append("  Typography:")
            if self.typography.display_family:
                lines.append(
                    f"    display: {self.typography.display_family} "
                    f"{self.typography.display_weight or ''}"
                )
            if self.typography.body_family:
                lines.append(f"    body:    {self.typography.body_family}")
            if self.typography.scale:
                lines.append(f"    scale:   {len(self.typography.scale)} roles — "
                             f"{', '.join(self.typography.scale)}")

        if self.spacing or self.radii or self.elevation:
            lines.append("")
            lines.append("  Structural tokens:")
            if self.spacing:
                lines.append(f"    spacing:   {len(self.spacing)} steps")
            if self.radii:
                lines.append(f"    radii:     {len(self.radii)} steps")
            if self.elevation:
                lines.append(f"    elevation: {len(self.elevation)} levels")

        if any((self.logo.wordmark.template, self.logo.monogram.template,
                self.logo.stacked.template, self.logo.horizontal.template)):
            lines.append("")
            lines.append("  Logo:")
            for vname in ("wordmark", "monogram", "stacked", "horizontal"):
                v: LogoVariant = getattr(self.logo, vname)
                if v.template or v.svg or v.png:
                    lines.append(
                        f"    {vname:<11} template={v.template or '—'}  "
                        f"svg={v.svg or '—'}"
                    )
            lines.append(f"    clear_space_em={self.logo.clear_space_em}  "
                         f"min_width_px={self.logo.min_width_px}")

        if self.voice.adjectives:
            lines.append("")
            lines.append(f"  Voice: {', '.join(self.voice.adjectives)}")

        lines.append("")
        lines.append("  A11y:")
        lines.append(f"    min_contrast_ratio: {self.a11y.min_contrast_ratio}:1")
        lines.append(f"    min_hit_target_px:  {self.a11y.min_hit_target_px}")
        if self.a11y.focus_ring_color:
            lines.append(f"    focus_ring:         {self.a11y.focus_ring_color}")

        if self.rules.never_rebuild_image_generation_elsewhere:
            lines.append("")
            lines.append(f"  ⚠ Brand owner: {self.rules.brand_owner or '(unspecified)'}")
            lines.append(f"    Image generation locked to the owner's pipeline.")

        return "\n".join(lines)


# ─── Loader ──────────────────────────────────────────────────────────────

def _text_role(d: dict[str, Any]) -> TextRole:
    return TextRole(
        size=float(d["size"]),
        weight=int(d.get("weight", 400)),
        line_height=float(d.get("line_height", 1.4)),
        tracking_em=float(d.get("tracking_em", 0.0)),
        upper=bool(d.get("upper", False)),
    )


def _logo_variant(d: dict[str, Any]) -> LogoVariant:
    return LogoVariant(
        template=d.get("template"),
        svg=d.get("svg"),
        png=d.get("png"),
    )


def load_styleguide(path: Union[str, Path]) -> StyleGuide:
    """
    Load a brand.toml style guide from disk into a frozen ``StyleGuide``.

    Raises
    ------
    FileNotFoundError          — path missing
    ValueError                 — required fields missing
    tomllib.TOMLDecodeError    — invalid TOML
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"style guide not found: {p}")
    with p.open("rb") as f:
        data = tomllib.load(f)

    # ── meta ────────────────────────────────────────────────────────────
    m = data.get("meta", {})
    if "name" not in m:
        raise ValueError(f"{p}: [meta] is missing required field 'name'")
    meta = Meta(
        name=m["name"],
        slug=m.get("slug"),
        version=m.get("version"),
        owner_repo=m.get("owner_repo"),
        owner_path=m.get("owner_path"),
        canonical_source=m.get("canonical_source"),
        ownership_rule=m.get("ownership_rule"),
    )

    # ── colors ──────────────────────────────────────────────────────────
    cd = data.get("colors", {})
    for req in ("background", "foreground"):
        if req not in cd:
            raise ValueError(f"{p}: [colors] is missing required field {req!r}")
    rings = {
        k: Ring(color=v["color"], width_px=int(v["width_px"]))
        for k, v in cd.get("rings", {}).items()
        if isinstance(v, dict) and "color" in v and "width_px" in v
    }
    named   = {k: v for k, v in cd.get("named",   {}).items() if isinstance(v, str)}
    aliases = {k: v for k, v in cd.get("aliases", {}).items() if isinstance(v, str)}
    colors = Colors(
        background=cd["background"],
        foreground=cd["foreground"],
        background_2=cd.get("background_2"),
        background_3=cd.get("background_3"),
        foreground_muted=cd.get("foreground_muted"),
        accent=cd.get("accent"),
        accent_ink=cd.get("accent_ink"),
        accent_decorative=cd.get("accent_decorative"),
        rings=rings, named=named, aliases=aliases,
    )

    # ── semantic ────────────────────────────────────────────────────────
    sem_raw = data.get("semantic", {})
    semantic: dict[str, SemanticState] = {}
    for name, v in sem_raw.items():
        if isinstance(v, dict) and "text" in v:
            semantic[name] = SemanticState(
                text=v["text"],
                surface=v.get("surface"),
                border=v.get("border"),
            )

    # ── viz ─────────────────────────────────────────────────────────────
    vd = data.get("viz", {})
    viz = Viz(
        categorical=tuple(vd.get("categorical", ())),
        sequential=tuple(vd.get("sequential", ())),
        diverging=tuple(vd.get("diverging", ())),
    )

    # ── typography ──────────────────────────────────────────────────────
    td = data.get("typography", {})
    scale_raw = td.get("scale", {})
    scale = {
        k: _text_role(v) for k, v in scale_raw.items()
        if isinstance(v, dict) and "size" in v
    }
    typography = Typography(
        display_family=td.get("display_family"),
        display_weight=td.get("display_weight"),
        display_line_height=td.get("display_line_height"),
        display_letter_spacing_em=td.get("display_letter_spacing_em"),
        body_family=td.get("body_family"),
        mono_family=td.get("mono_family"),
        paint_order=td.get("paint_order"),
        scale=scale,
    )

    # ── spacing / radii / elevation ─────────────────────────────────────
    spacing   = {k: int(v) for k, v in data.get("spacing",   {}).items()}
    radii     = {k: int(v) for k, v in data.get("radii",     {}).items()}
    elevation = {k: str(v) for k, v in data.get("elevation", {}).items()}

    # ── motion ──────────────────────────────────────────────────────────
    md = data.get("motion", {})
    motion = Motion(
        duration_instant=int(md.get("duration_instant", 0)),
        duration_fast=int(md.get("duration_fast", 120)),
        duration_normal=int(md.get("duration_normal", 240)),
        duration_slow=int(md.get("duration_slow", 480)),
        duration_reveal=int(md.get("duration_reveal", 800)),
        easing_default=md.get("easing_default", "cubic-bezier(0.2, 0.0, 0.2, 1.0)"),
        easing_emphasis=md.get("easing_emphasis", "cubic-bezier(0.4, 0.0, 0.2, 1.0)"),
        easing_snappy=md.get("easing_snappy", "cubic-bezier(0.6, 0.0, 0.2, 1.0)"),
        easing_linear=md.get("easing_linear", "linear"),
        motion_preference=md.get("motion_preference", "respect-prefers-reduced-motion"),
    )

    # ── iconography / imagery ───────────────────────────────────────────
    id_ = data.get("iconography", {})
    iconography = Iconography(
        family=id_.get("family"),
        stroke_px=id_.get("stroke_px"),
        default_size=id_.get("default_size"),
        sizes=tuple(id_.get("sizes", ())),
    )
    im = data.get("imagery", {})
    imagery = Imagery(
        style=im.get("style"),
        treatments=tuple(im.get("treatments", ())),
        crop_policy=im.get("crop_policy", "energy-only"),
    )

    # ── logo ────────────────────────────────────────────────────────────
    ld = data.get("logo", {})
    logo = Logo(
        clear_space_em=float(ld.get("clear_space_em", 1.0)),
        min_width_px=int(ld.get("min_width_px", 64)),
        wordmark=_logo_variant(ld.get("wordmark", {})),
        monogram=_logo_variant(ld.get("monogram", {})),
        stacked=_logo_variant(ld.get("stacked", {})),
        horizontal=_logo_variant(ld.get("horizontal", {})),
    )

    # ── voice ───────────────────────────────────────────────────────────
    vd_ = data.get("voice", {})
    voice = Voice(
        adjectives=tuple(vd_.get("adjectives", ())),
        say_yes=tuple(vd_.get("say_yes", ())),
        say_no=tuple(vd_.get("say_no", ())),
    )

    # ── a11y ────────────────────────────────────────────────────────────
    ad = data.get("a11y", {})
    a11y = A11y(
        min_contrast_ratio=float(ad.get("min_contrast_ratio", 8.0)),
        min_hit_target_px=int(ad.get("min_hit_target_px", 44)),
        focus_ring_color=ad.get("focus_ring_color"),
        focus_ring_width_px=int(ad.get("focus_ring_width_px", 3)),
        motion_reduce_policy=ad.get("motion_reduce_policy", "collapse-to-zero"),
    )

    # ── assets ──────────────────────────────────────────────────────────
    ad2 = data.get("assets", {})
    assets = Assets(
        fractal_fill_default=ad2.get("fractal_fill_default"),
        fractal_fills=tuple(ad2.get("fractal_fills", ())),
    )

    # ── rules ───────────────────────────────────────────────────────────
    rd = data.get("rules", {})
    reserved = {"never_modify_sources",
                "never_rebuild_image_generation_elsewhere",
                "brand_owner"}
    rules = Rules(
        never_modify_sources=bool(rd.get("never_modify_sources", False)),
        never_rebuild_image_generation_elsewhere=bool(
            rd.get("never_rebuild_image_generation_elsewhere", False)),
        brand_owner=rd.get("brand_owner"),
        custom={k: v for k, v in rd.items() if k not in reserved},
    )

    return StyleGuide(
        meta=meta, colors=colors, semantic=semantic, viz=viz,
        typography=typography,
        spacing=spacing, radii=radii, elevation=elevation,
        motion=motion, iconography=iconography, imagery=imagery,
        logo=logo, voice=voice, a11y=a11y,
        assets=assets, rules=rules,
        dependencies=dict(data.get("dependencies", {})),
        export={k: str(v) for k, v in data.get("export", {}).items()},
        source_path=p,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────

def _main(argv: Optional[list[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m muriel.styleguide",
        description="Load a brand.toml; describe / emit CSS / audit contrast.",
    )
    parser.add_argument("path", type=Path, help="Path to a brand.toml file")
    parser.add_argument("--css", action="store_true",
                        help="Emit a CSS :root custom-property block.")
    parser.add_argument("--css-prefix", default="--brand-",
                        help="Prefix for CSS variables. Default: --brand-")
    parser.add_argument("--contrast", action="store_true",
                        help="Audit every color role against the background.")
    parser.add_argument("--required", type=float, default=None,
                        help="Override the brand's own a11y.min_contrast_ratio.")
    args = parser.parse_args(argv)

    try:
        sg = load_styleguide(args.path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr); return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr); return 2
    except tomllib.TOMLDecodeError as exc:
        print(f"error: invalid TOML in {args.path}: {exc}", file=sys.stderr); return 2

    print()
    print(sg.describe())

    if args.css:
        print()
        print(f"── CSS (prefix: {args.css_prefix}) ──")
        print(sg.to_css_vars(prefix=args.css_prefix))

    if args.contrast:
        threshold = args.required if args.required is not None else sg.a11y.min_contrast_ratio
        print()
        print(f"── WCAG contrast audit (required: {threshold:.1f}:1) ──")
        results = sg.audit_contrast(required=args.required)
        fail_count = 0
        for role, ratio, passes in results:
            mark = "✓" if passes else "✗"
            status = "PASS" if passes else "FAIL"
            print(f"  {mark} {status}  {role:<24} {ratio:6.2f}:1")
            if not passes:
                fail_count += 1
        if fail_count:
            print()
            print(f"  {fail_count} role(s) failed the {threshold:.1f}:1 rule")
            return 1

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
