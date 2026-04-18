# Contributing to muriel

Thanks for looking. muriel is a multi-constraint solver for visual
production — a set of design rules, channel recipes, and Python helpers
that produce every visual artifact a researcher-designer-engineer ships.
Contributions are welcome; below is how to make yours land cleanly.

## Before you start

1. **Read the top-level [`README.md`](README.md) and [`muriel.md`](muriel.md).** The universal rules
   (8:1 contrast, decorative ≥55/255, OLED palette, one font treatment,
   generated > drawn, reproducible > one-off) apply to every
   contribution. Anti-patterns sections in each channel doc spell out
   what to avoid.
2. **Skim the channel and vocabulary you're touching.** Every channel
   subfile under [`channels/`](channels/) and every vocabulary under
   [`vocabularies/`](vocabularies/) has a distinct voice and scope.
   Match it; don't homogenize.
3. **Run the contrast audit.** If your change touches any text color or
   SVG, run `python -m muriel.contrast <file>` before pushing. Exit 0
   means you cleared 8:1.

## What belongs where

| You're adding… | Land it at… |
|---|---|
| A new output channel (e.g. print, imagegen) | `channels/<name>.md` — one file, same structure as existing channels (When to use / Tooling / Patterns / Anti-patterns) |
| A new design grammar or aesthetic tradition | `vocabularies/<name>.md` — cite lineage, list exemplars, integrate with existing channels |
| A Python helper used across channels | `muriel/<module>.py` — add to `muriel/__init__.py`'s `__all__` and docstring table |
| A brand style guide example | `examples/<slug>-brand.toml` — fictional brand preferred; real brands should live in their own repo |
| A thumbnail-linked gallery example | `examples/gallery/` — thumbnail ≤ 500 KB, live URL required |
| A small reusable data file | `templates/<name>.json` or similar |

## Rules of the road

- **Prose files keep their voice.** Terse, opinionated, slightly dry,
  no false profundity, no "remarkably," no "surprisingly."
- **Every claim with a number gets a unit and context.** No bare
  ratios, no unlabeled axes.
- **If the data could drive it, generate it.** Don't hand-draw what a
  script can regenerate.
- **Save the script next to the output.** Reproducibility > one-off.
- **Respect brand ownership rules.** If a `brand.toml` sets
  `never_rebuild_image_generation_elsewhere = true`, don't regenerate
  that brand's wordmarks or monograms in muriel.

## Adding a channel

A new channel doc should follow this shape:

```markdown
# <Channel> — <one-line summary>

<One paragraph on what the channel is and why it exists.>

Part of the [muriel](../muriel.md) skill.

## When to use
- …

## Tooling
| Tool | Strength | Recipe |

## Patterns
- …

## Anti-patterns
- Don't …
```

Also add an entry to [`muriel.md`](muriel.md)'s Channel table and the
Channel reference map.

## Adding a vocabulary

Vocabularies are named design grammars — FUI, Visible Language,
PixiJS, Kinetic Typography. A new one should:

- Cite the lineage (who invented it, where it's canonical).
- List public exemplars (shipping projects, well-known work).
- Explain how it integrates with existing muriel channels.
- Name the substrate choices (library / library family) for execution.

Also add an entry to [`muriel.md`](muriel.md)'s Aesthetic vocabularies
list and the Channel reference map.

## Python contributions

- **Standard library preferred.** muriel ships with zero required
  dependencies. Matplotlib, Pillow, Playwright are allowed but
  optional — guard imports and raise a clean `ImportError` with
  install instructions on first use.
- **Dataclasses for schemas**, not arbitrary dicts.
- **Type hints on public APIs.** Use `Optional[str]`, not `str | None`
  (we support Python 3.9+).
- **CLIs use exit codes.** 0 = success, 1 = soft failure (contrast
  rule violated, etc.), 2 = usage error / missing dep.
- **Tests are welcome.** `pytest` planned; patterns to follow will
  land once the first test suite is in.

## Commit style

Conventional Commits: `type(scope): message`. Examples:

```
feat(channels): add imagegen channel
fix(contrast): handle inline fill attributes on <text>
docs(vocabularies): lift PixiJS v9 patterns from upstream
refactor(styleguide): split colors.aliases resolution to its own helper
```

## License

All contributions are released under MIT (same as the rest of the
project — see [`LICENSE`](LICENSE)). By submitting, you agree to this.
